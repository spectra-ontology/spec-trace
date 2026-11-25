#!/usr/bin/env python3
"""
Phase-6 청크 업데이트 스크립트
Figure/Equation Enhancement 결과를 chunks.json에 통합

사용법:
    python 06_update_chunks.py --workers 4 --resume
    python 06_update_chunks.py --meeting RAN4#118 --limit 10
"""

import json
import logging
import os
import sys
import argparse
import hashlib
from pathlib import Path
import time


# =============================================================================
# 설정
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(PROJECT_ROOT / "scripts/common"))
from common.atomic_io import write_json_atomic
LOG_DIR = PROJECT_ROOT / "logs" / "tsg" / "RAN" / "formal"
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "tsg" / "RAN" / "formal" / "common"))
import pool_run  # noqa: E402  워커가 죽어도 문서를 잃지 않는 RAN 공용 풀
import tdoc_selection  # noqa: E402

# 풀 하나가 맡는 문서 수. 묶음 끝에서는 가장 느린 문서를 기다리므로 너무 작으면 그 기다림이 잦고,
# 너무 크면 풀이 깨졌을 때 줄어든 워커로 도는 몫이 커진다. Phase-4 CR 파서의 묶음 크기와 같게 둔다.
POOL_SLICE = 2000
log = logging.getLogger(__name__)
DEFAULT_WG = "RAN4"


def get_parsed_base(wg: str) -> Path:
    return PROJECT_ROOT / "vectordb" / "parsed" / "tdocs" / wg


# =============================================================================
# 청크 업데이트 로직
# =============================================================================

#: 요약을 만드는 보강 입력. 둘 다 선택 파일이다. 그림 · 수식이 없는 문서에는 없을 수 있다.
INPUT_FILES = {'figures': ('figures', 'index.json'), 'equations': ('equations.json',)}


def input_digests(tdoc_dir: Path) -> dict:
    """보강 입력 파일마다 바이트 sha256. 없는 파일은 None.

    완료 판정(`enhanced_version`)만 보면 04 · 05 를 다시 돌려 입력이 바뀌어도 요약이 첫 값으로 남는다.
    요약을 만든 입력의 지문을 함께 남기고, 지문이 같을 때만 다 된 것으로 본다.
    """
    out = {}
    for key, parts in INPUT_FILES.items():
        path = tdoc_dir.joinpath(*parts)
        out[key] = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    return out


def _read_input(path: Path) -> tuple[dict | None, str | None]:
    """보강 입력 하나와 그 바이트 sha256. 없으면 (None, None). 있는데 JSON 객체로 읽히지 않으면 예외를 올린다.

    손상된 입력을 없는 입력처럼 넘기면 요약 없이 완료 표시가 붙고, 그 표시 때문에 고친 입력도 건너뛴다.
    지문은 읽은 바이트에서 낸다. 따로 다시 읽으면 그 사이에 바뀐 파일의 지문이 남는다.
    """
    if not path.exists():
        return None, None
    raw = path.read_bytes()
    data = json.loads(raw.decode('utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: JSON 객체가 아니다")
    return data, hashlib.sha256(raw).hexdigest()


def load_inputs(tdoc_dir: Path) -> tuple[dict | None, dict | None, dict]:
    """그림 색인 · 수식 목록 · 둘의 지문. 수식은 보강(05)을 거친 것만 쓴다. 없거나 보강 전이면 None."""
    figures, fig_digest = _read_input(tdoc_dir.joinpath(*INPUT_FILES['figures']))
    equations, eq_digest = _read_input(tdoc_dir.joinpath(*INPUT_FILES['equations']))
    if equations is not None and not equations.get('enhanced'):
        equations = None
    return figures, equations, {'figures': fig_digest, 'equations': eq_digest}


def is_current(chunks_data: dict, digests: dict) -> bool:
    """chunks.json 의 요약이 지금 보강 입력으로 만든 것인가."""
    return chunks_data.get('enhanced_version') == '2.0' and chunks_data.get('enhancement_inputs') == digests


def update_chunks(tdoc_dir: Path, figures: dict | None, equations: dict | None, digests: dict) -> dict:
    """chunks.json 업데이트"""
    chunks_file = tdoc_dir / 'chunks.json'

    if not chunks_file.exists():
        return {'status': 'skipped', 'reason': 'no_chunks'}

    try:
        with open(chunks_file) as f:
            chunks_data = json.load(f)
    except json.JSONDecodeError:
        return {'status': 'error', 'reason': 'invalid_json'}

    # 이미 지금 입력으로 업데이트되었는지 확인
    if is_current(chunks_data, digests):
        return {'status': 'skipped', 'reason': 'already_updated'}

    # Enhancement 정보 추가. 입력이 없어진 요약은 지운다. 남겨 두면 옛 입력의 값이 지금 값으로 읽힌다.
    chunks_data['enhanced_version'] = '2.0'
    chunks_data['enhancement_timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    chunks_data['enhancement_inputs'] = digests
    chunks_data.pop('figure_summary', None)
    chunks_data.pop('equation_summary', None)

    # Figure 통계 추가
    if figures:
        chunks_data['figure_summary'] = {
            'count': figures.get('image_count', 0),
            'with_caption': figures.get('caption_count', 0)
        }

    # Equation 통계 추가
    if equations:
        # count 는 OMML 수식과 수식 개체(`w:object`)를 함께 센 수다. 종류(source)가 없는 항목은 OMML 수식이다.
        eqs = equations.get('equations', [])
        chunks_data['equation_summary'] = {
            'count': equations.get('total_count', 0),
            'omml_count': sum(1 for eq in eqs if eq.get('source', 'omml') == 'omml'),
            'ole_count': sum(1 for eq in eqs if eq.get('source') == 'ole'),
            'with_latex': equations.get('with_latex', 0)
        }

    # 수식 글은 이미 청크 본문에 있다 — 파서(03)가 `docx_text.chunk_text` 로 수식 자리에 선형 표기를 넣는다.
    # 여기서는 문서 단위 수식 통계만 붙인다.

    # 저장
    # 다 쓴 뒤에 제자리로 옮긴다 — 쓰는 도중 워커가 죽어도 반쯤 쓴 파일이 남지 않는다.
    write_json_atomic(chunks_file, chunks_data)

    return {
        'status': 'success',
        'figures': figures.get('image_count', 0) if figures else 0,
        'equations': equations.get('total_count', 0) if equations else 0
    }


def process_single_tdoc(args: tuple) -> dict:
    """단일 Tdoc 처리"""
    tdoc_dir, meeting_id, tdoc_number = args

    try:
        # Enhancement 데이터 로드. 읽지 못하는 입력은 예외로 올라와 아래 except 가 오류로 돌려주고 chunks.json 은 그대로 둔다.
        figures, equations, digests = load_inputs(tdoc_dir)

        # 청크 업데이트
        result = update_chunks(tdoc_dir, figures, equations, digests)
        result['tdocNumber'] = tdoc_number
        result['meetingId'] = meeting_id

        return result

    except Exception as e:
        return {
            'status': 'error',
            'tdocNumber': tdoc_number,
            'error': str(e)
        }


# =============================================================================
# 메인 로직
# =============================================================================

def collect_tasks(parsed_base: Path, wg: str = DEFAULT_WG,
                   meeting_filter: str = None, resume: bool = False, tdoc_filter: str | None = None) -> tuple[list, int]:
    """처리 대상 수집"""
    selected = tdoc_selection.parsed_target(parsed_base, wg, meeting_filter, tdoc_filter)
    tasks = []
    skipped = 0

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

            # Resume 모드: 지금 입력으로 이미 업데이트된 것 건너뛰기(워커와 같은 `is_current` 판정)
            if resume:
                chunks_file = tdoc_dir / 'chunks.json'
                if chunks_file.exists():
                    try:
                        with open(chunks_file) as f:
                            data = json.load(f)
                        if is_current(data, input_digests(tdoc_dir)):
                            skipped += 1
                            continue
                    except json.JSONDecodeError:
                        pass

            tasks.append((tdoc_dir, meeting_id, tdoc_number))

    return tasks, skipped


def main():
    parser = argparse.ArgumentParser(description="Phase-6 청크 업데이트")
    parser.add_argument("--workers", type=int, default=4, help="병렬 워커 수")
    parser.add_argument("--resume", action="store_true", help="이미 처리된 문서 건너뛰기")
    parser.add_argument("--meeting", type=str, help="특정 회의만 처리")
    parser.add_argument("--limit", type=int, default=0, help="처리할 최대 문서 수")
    parser.add_argument(
        "--wg",
        type=str,
        default=DEFAULT_WG,
        help=f"Working Group (기본: {DEFAULT_WG})"
    )

    tdoc_selection.add_argument(parser)
    args = parser.parse_args()
    tdoc_selection.validate_arguments(parser, args, wg=DEFAULT_WG)
    if args.workers <= 0:
        parser.error("--workers는 양의 정수여야 합니다")
    if args.limit < 0:
        parser.error("--limit은 0 이상의 정수여야 합니다")

    PARSED_BASE = get_parsed_base(args.wg)

    print("=" * 70)
    print(f"Phase-6 청크 업데이트 (Enhancement 통합) (WG: {args.wg})")
    print("=" * 70)
    print(f"워커: {args.workers}")
    print(f"Resume: {args.resume}")
    if args.meeting:
        print(f"회의 필터: {args.meeting}")
    print("=" * 70)

    # 작업 수집
    print("\n[작업 수집]")
    tasks, skipped = tdoc_selection.collect_or_error(parser, collect_tasks, PARSED_BASE, wg=args.wg, meeting_filter=args.meeting, resume=args.resume, tdoc_filter=args.tdoc)

    print(f"처리 대상: {len(tasks)}")
    if skipped > 0:
        print(f"건너뛴 문서: {skipped}")

    if args.limit > 0:
        tasks = tasks[:args.limit]
        print(f"제한 적용: {len(tasks)} 문서만 처리")

    if not tasks:
        print("처리할 문서가 없습니다.")
        return

    # 병렬 처리
    print("\n[청크 업데이트 시작]")
    start_time = time.time()

    results = []
    errors = []

    completed = 0
    total_figures = 0
    total_equations = 0

    # 묶음마다 새 풀을 띄워 RAN 공용 풀(pool_run)로 돈다 — 워커가 죽어도 끝나지 못한 문서를 워커를 줄여
    # 다시 돌린다. 풀 하나가 통째로 깨져 단계가 멈추지 않는다.
    for i in range(0, len(tasks), POOL_SLICE):
        for result in pool_run.run_all(process_single_tdoc, [(t,) for t in tasks[i:i + POOL_SLICE]],
                                       args.workers, log):
            completed += 1

            if result['status'] == 'success':
                results.append(result)
                total_figures += result.get('figures', 0)
                total_equations += result.get('equations', 0)
            elif result['status'] == 'error':
                errors.append(result)

            if completed % 500 == 0 or completed == len(tasks):
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                print(f"  진행: {completed}/{len(tasks)} ({completed*100/len(tasks):.1f}%) "
                      f"| 속도: {rate:.1f} docs/s")

    elapsed = time.time() - start_time

    # 결과 요약
    print("\n" + "=" * 70)
    print("결과 요약")
    print("=" * 70)
    print(f"총 처리: {len(tasks)}")
    print(f"성공: {len(results)}")
    print(f"오류: {len(errors)}")
    print(f"소요 시간: {elapsed:.1f}초")

    if results:
        docs_with_figures = sum(1 for r in results if r.get('figures', 0) > 0)
        docs_with_equations = sum(1 for r in results if r.get('equations', 0) > 0)

        print("\n[통계]")
        print(f"  Figure 포함 문서: {docs_with_figures}")
        print(f"  Equation 포함 문서: {docs_with_equations}")
        print(f"  총 Figure: {total_figures}")
        print(f"  총 Equation: {total_equations}")

    if errors:
        print("\n[오류 목록 (처음 5개)]")
        for err in errors[:5]:
            print(f"  {err.get('tdocNumber', '?')}: {err.get('error', 'unknown')[:60]}")

    # 리포트 저장
    log_dir = LOG_DIR / args.wg / "phase-6"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_path = log_dir / f"update_chunks_{timestamp}.json"

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'summary': {
                'total': len(tasks),
                'success': len(results),
                'errors': len(errors),
                'elapsed_seconds': elapsed
            },
            'stats': {
                'total_figures': total_figures,
                'total_equations': total_equations,
                'docs_with_figures': sum(1 for r in results if r.get('figures', 0) > 0),
                'docs_with_equations': sum(1 for r in results if r.get('equations', 0) > 0)
            },
            'errors': errors  # 실패자 목록은 자르지 않는다. 수만 남고 이름이 사라지면 어느 문서가 빠졌는지 되짚을 길이 없다.
        }, f, indent=2, ensure_ascii=False)

    print(f"\n리포트 저장: {report_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
