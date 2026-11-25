#!/usr/bin/env python3
"""
Phase-6 청킹 개선 스크립트 (P1 개선)
- chunkId 필드 추가: {tdocNumber}-{chunkIndex:03d}
- 작은 청크 병합: 추정 100 토큰 미만
- 큰 청크 분할: 추정 2000 토큰 초과인 청크를 문장 단위로 분할
  개별 문장이 상한보다 길면 그대로 남기고 결과 통계에 집계합니다.

사용법:
    python 07_rechunk_all.py --workers 8
    python 07_rechunk_all.py --meeting RAN3#123-bis --limit 10  # 테스트
"""

import json
import logging
import os
import sys
import argparse
import re
from pathlib import Path
from datetime import datetime
import time


# =============================================================================
# 설정
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[7]
LOG_DIR = PROJECT_ROOT / "logs" / "tsg" / "RAN" / "formal"
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "tsg" / "RAN" / "formal" / "common"))
import pool_run  # noqa: E402  워커 실패 시 작업을 재시도하는 RAN 공용 풀
import tdoc_selection  # noqa: E402

# 풀 하나가 맡는 문서 수. 묶음 끝에서는 가장 느린 문서를 기다리므로 너무 작으면 그 기다림이 잦고,
# 너무 크면 풀이 깨졌을 때 줄어든 워커로 도는 몫이 커진다. Phase-4 CR 파서의 묶음 크기와 같게 둔다.
POOL_SLICE = 2000
log = logging.getLogger(__name__)
DEFAULT_WG = "RAN3"


def get_parsed_base(wg: str) -> Path:
    return PROJECT_ROOT / "vectordb" / "parsed" / "tdocs" / wg

MIN_TOKENS = 100
MAX_TOKENS = 2000


# =============================================================================
# 토큰 및 청킹 유틸리티
# =============================================================================

def count_tokens(text: str) -> int:
    """토큰 수 추정 (1 토큰 = 4 글자)"""
    return len(text) // 4 if text else 0


def split_into_sentences(text: str) -> list[str]:
    """텍스트를 문장으로 분할"""
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in sentences if s.strip()]


def merge_small_chunks(chunks: list[dict]) -> list[dict]:
    """작은 청크를 병합하며 원문 순서대로 절 제목을 보존한다."""
    if not chunks:
        return chunks

    merged = []

    for chunk in chunks:
        # 현재 청크가 작으면 이전 청크와 병합 시도
        if merged and chunk['tokenCount'] < MIN_TOKENS:
            prev = merged[-1]
            merged_content = prev['content'] + '\n' + chunk['content']
            merged_tokens = count_tokens(merged_content)

            # 병합해도 MAX_TOKENS 이하면 병합
            if merged_tokens <= MAX_TOKENS:
                merged[-1] = {
                    **prev,
                    'content': merged_content,
                    'sectionTitle': ' / '.join(dict.fromkeys(title for title in (prev.get('sectionTitle', ''), chunk.get('sectionTitle', '')) if title)),
                    'tokenCount': merged_tokens
                }
                continue

        # 이전 청크가 작으면 현재와 병합 시도
        if merged and merged[-1]['tokenCount'] < MIN_TOKENS:
            prev = merged[-1]
            merged_content = prev['content'] + '\n' + chunk['content']
            merged_tokens = count_tokens(merged_content)

            if merged_tokens <= MAX_TOKENS:
                merged[-1] = {
                    **prev,
                    'content': merged_content,
                    'sectionTitle': ' / '.join(dict.fromkeys(title for title in (prev.get('sectionTitle', ''), chunk.get('sectionTitle', '')) if title)),
                    'tokenCount': merged_tokens
                }
                continue

        merged.append(chunk.copy())

    return merged


def split_oversized_chunks(chunks: list[dict]) -> list[dict]:
    """큰 청크 분할 (> MAX_TOKENS)"""
    result = []

    for chunk in chunks:
        if chunk['tokenCount'] <= MAX_TOKENS:
            result.append(chunk)
            continue

        # 문장 단위로 분할
        text = chunk['content']
        sentences = split_into_sentences(text)

        if not sentences:
            # 분할 불가능하면 그대로 유지
            result.append(chunk)
            continue

        current_text = []
        current_tokens = 0

        for sentence in sentences:
            sent_tokens = count_tokens(sentence)

            if current_tokens + sent_tokens > MAX_TOKENS and current_text:
                # 현재까지 저장
                result.append({
                    **chunk,
                    'content': ' '.join(current_text),
                    'tokenCount': current_tokens
                })
                current_text = [sentence]
                current_tokens = sent_tokens
            else:
                current_text.append(sentence)
                current_tokens += sent_tokens

        # 마지막 부분
        if current_text:
            result.append({
                **chunk,
                'content': ' '.join(current_text),
                'tokenCount': current_tokens
            })

    return result


def add_chunk_ids(chunks: list[dict], tdoc_number: str) -> list[dict]:
    """chunkId 필드 추가"""
    for i, chunk in enumerate(chunks):
        chunk['chunkId'] = f"{tdoc_number}-{i+1:03d}"
        chunk['chunkIndex'] = i + 1
    return chunks


# =============================================================================
# 메인 처리 로직
# =============================================================================

def rechunk_single_tdoc(args: tuple) -> dict:
    """단일 TDoc의 청크를 분할·병합하고 청크 식별자를 갱신한다."""
    tdoc_dir, meeting_id, tdoc_number, force = args

    chunks_file = tdoc_dir / 'chunks.json'

    if not chunks_file.exists():
        return {'status': 'skipped', 'reason': 'no_chunks', 'tdocNumber': tdoc_number}

    try:
        with open(chunks_file) as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return {'status': 'error', 'reason': 'invalid_json', 'tdocNumber': tdoc_number}

    # 이미 v3.0으로 업데이트된 경우 건너뛰기 — --force 면 다시 처리한다
    if data.get('chunk_version') == '3.0' and not force:
        return {'status': 'skipped', 'reason': 'already_v3', 'tdocNumber': tdoc_number}

    chunks = data.get('chunks', [])
    original_count = len(chunks)

    if not chunks:
        return {'status': 'skipped', 'reason': 'empty_chunks', 'tdocNumber': tdoc_number}

    # 1단계: 큰 청크 분할
    chunks = split_oversized_chunks(chunks)

    # 2단계: 작은 청크 병합
    chunks = merge_small_chunks(chunks)

    # 3단계: chunkId 추가
    chunks = add_chunk_ids(chunks, tdoc_number)

    # 통계 계산
    tokens = [c['tokenCount'] for c in chunks]
    undersized = sum(1 for t in tokens if t < MIN_TOKENS)
    oversized = sum(1 for t in tokens if t > MAX_TOKENS)

    # 업데이트
    data['chunks'] = chunks
    data['chunk_version'] = '3.0'
    data['chunk_timestamp'] = datetime.utcnow().isoformat() + 'Z'

    # 저장
    # 전체 JSON을 임시 파일에 쓴 후 대상 파일을 교체한다. 교체 전까지 기존 대상 파일을 유지한다.
    tmp = chunks_file.with_name(chunks_file.name + '.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, chunks_file)

    return {
        'status': 'success',
        'tdocNumber': tdoc_number,
        'original_chunks': original_count,
        'new_chunks': len(chunks),
        'undersized': undersized,
        'oversized': oversized
    }


def collect_tasks(parsed_base: Path, wg: str = DEFAULT_WG,
                   meeting_filter: str = None, force: bool = False, tdoc_filter: str | None = None) -> list:
    """처리 대상 수집"""
    selected = tdoc_selection.parsed_target(parsed_base, wg, meeting_filter, tdoc_filter)
    tasks = []

    for meeting_dir in sorted(parsed_base.iterdir()):
        if not meeting_dir.is_dir() or not meeting_dir.name.startswith(f"{wg}#"):
            continue

        meeting_id = meeting_dir.name

        if meeting_filter and meeting_id != meeting_filter:
            continue

        for tdoc_dir in sorted(meeting_dir.iterdir()):
            if not tdoc_dir.is_dir():
                continue

            tdoc_number = tdoc_dir.name
            if selected is not None and tdoc_number != selected:
                continue

            # force가 아니면 이미 v3.0인 것 건너뛰기
            if not force:
                chunks_file = tdoc_dir / 'chunks.json'
                if chunks_file.exists():
                    try:
                        with open(chunks_file) as f:
                            data = json.load(f)
                        if data.get('chunk_version') == '3.0':
                            continue
                    except (OSError, ValueError, AttributeError):
                        pass

            tasks.append((tdoc_dir, meeting_id, tdoc_number, force))

    return tasks


def main():
    parser = argparse.ArgumentParser(description="Phase-6 청킹 개선 (P1)")
    parser.add_argument("--workers", type=int, default=8, help="병렬 워커 수")
    parser.add_argument("--meeting", type=str, help="특정 회의만 처리")
    parser.add_argument("--limit", type=int, default=0, help="처리할 최대 문서 수")
    parser.add_argument("--force", action="store_true", help="이미 처리된 문서도 재처리")
    parser.add_argument(
        "--wg",
        type=str,
        default=DEFAULT_WG,
        choices=[DEFAULT_WG],
        help=f"Working Group (기본: {DEFAULT_WG})"
    )

    tdoc_selection.add_argument(parser)
    args = parser.parse_args()
    tdoc_selection.validate_arguments(parser, args, wg=DEFAULT_WG)
    if args.workers < 1:
        parser.error("--workers는 1 이상의 정수여야 합니다")
    if args.limit < 0:
        parser.error("--limit는 0 이상의 정수여야 합니다")

    PARSED_BASE = get_parsed_base(args.wg)

    print("=" * 70)
    print(f"Phase-6 청킹 개선 (P1) (WG: {args.wg})")
    print("=" * 70)
    print(f"MIN_TOKENS: {MIN_TOKENS}, MAX_TOKENS: {MAX_TOKENS}")
    print(f"워커: {args.workers}")
    if args.meeting:
        print(f"회의 필터: {args.meeting}")
    print("=" * 70)

    # 작업 수집
    print("\n[작업 수집]")
    tasks = tdoc_selection.collect_or_error(parser, collect_tasks, PARSED_BASE, wg=args.wg, meeting_filter=args.meeting, force=args.force, tdoc_filter=args.tdoc)
    print(f"처리 대상: {len(tasks)}")

    if args.limit > 0:
        tasks = tasks[:args.limit]
        print(f"제한 적용: {len(tasks)} 문서만 처리")

    if not tasks:
        print("처리할 문서가 없습니다.")
        return

    # 병렬 처리
    print("\n[청킹 개선 시작]")
    start_time = time.time()

    results = {'success': 0, 'skipped': 0, 'error': 0}
    total_undersized = 0
    total_oversized = 0
    errors = []

    completed = 0

    # 작업을 묶음별 공용 풀에서 실행한다. 풀이 종료되면 완료되지 않은 작업을
    # 줄어든 워커 수로 재시도한다.
    for i in range(0, len(tasks), POOL_SLICE):
        for result in pool_run.run_all(rechunk_single_tdoc, [(t,) for t in tasks[i:i + POOL_SLICE]],
                                       args.workers, log):
            completed += 1

            status = result['status']
            results[status] = results.get(status, 0) + 1

            if status == 'success':
                total_undersized += result.get('undersized', 0)
                total_oversized += result.get('oversized', 0)
            elif status == 'error':
                errors.append(result)

            if completed % 1000 == 0 or completed == len(tasks):
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                print(f"  진행: {completed}/{len(tasks)} ({rate:.0f}/초)")

    elapsed = time.time() - start_time

    # 결과 출력
    print("\n" + "=" * 70)
    print("결과")
    print("=" * 70)
    print(f"처리 완료: {results['success']}")
    print(f"건너뜀: {results['skipped']}")
    print(f"에러: {results['error']}")
    print(f"소요 시간: {elapsed:.1f}초")
    print("\n남은 문제 청크:")
    print(f"  Undersized (<100 토큰): {total_undersized}")
    print(f"  Oversized (>2000 토큰): {total_oversized}")

    # 로그 저장
    log_dir = LOG_DIR / args.wg / "phase-6"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"rechunk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(log_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': len(tasks),
                **results,
                'elapsed_seconds': elapsed
            },
            'stats': {
                'remaining_undersized': total_undersized,
                'remaining_oversized': total_oversized
            },
            'errors': errors  # 재처리할 문서를 식별할 수 있도록 오류 목록 전체를 저장한다.
        }, f, indent=2)

    print(f"\n로그 저장: {log_file}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
