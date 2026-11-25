#!/usr/bin/env python3
"""
Phase-6 Figure 이미지 추출 Enhancement
파싱(03)이 쓴 그림 색인(figures/index.json)에 그림 파일과 개수를 채운다

그림 색인의 항목(그림 개체마다 하나 · 캡션 짝 · 그림 파일 경로)은 03 과 같은 규칙(`docx_figures.figures`)으로
원본에서 다시 얻는다. 다시 얻은 항목이 03 이 쓴 항목과 다르면 03 산출이 원본 · 규칙과 어긋난 것이라 그 문서는
오류로 남기고 손대지 않는다. 그림 파일은 색인 항목이 가리키는 부품만 figures/media/ 에 쓴다 — 색인 항목이
가리키지 않는 그림 부품은 쓰지 않고, 앞선 실행이 남긴 그런 파일은 지운다.
03 은 그림 개체가 있는 문서에만 그림 색인을 쓰므로, 색인이 없는 문서는 보강 대상이 아니다.

구현 계획: docs/tsg/RAN/formal/RAN4/phase-6/step1_parsing.md

사용법:
    python 04_enhance_figures.py --workers 4 --resume
    python 04_enhance_figures.py --meeting RAN4#118 --limit 10
"""

import json
import logging
import os
import sys
import argparse
import tempfile
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent))
from parse_tdoc_lib import meeting_id_to_folder, DEFAULT_WG, tdoc_dir_for, tdoc_documents, document_figures
import pool_run  # noqa: E402  워커가 죽어도 문서를 잃지 않는 RAN 공용 풀. 경로는 parse_tdoc_lib 가 건다
import tdoc_copy_owner  # noqa: E402  03 이 제 문서를 되찾아 읽은 번호의 기록. 경로는 parse_tdoc_lib 가 건다
import docx_figures  # noqa: E402  그림 개체 · 캡션 짝 · 그림 파일 경로의 정본(03 과 같은 규칙). 경로는 parse_tdoc_lib 가 건다


# =============================================================================
# 설정
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(PROJECT_ROOT / "scripts/common"))
from common.atomic_io import write_json_atomic
import tdoc_selection  # noqa: E402
LOG_DIR = PROJECT_ROOT / "logs" / "tsg" / "RAN" / "formal"

# 풀 하나가 맡는 문서 수. 묶음 끝에서는 가장 느린 문서를 기다리므로 너무 작으면 그 기다림이 잦고,
# 너무 크면 풀이 깨졌을 때 줄어든 워커로 도는 몫이 커진다. Phase-4 CR 파서의 묶음 크기와 같게 둔다.
POOL_SLICE = 2000
log = logging.getLogger(__name__)

def get_data_base(wg: str) -> Path:
    return PROJECT_ROOT / "data" / "corpus" / "tsg" / "RAN" / "formal" / "meetings" / wg / "derived"

def get_parsed_base(wg: str) -> Path:
    return PROJECT_ROOT / "vectordb" / "parsed" / "tdocs" / wg


# =============================================================================
# Meeting ID 매핑 — parse_tdoc_lib.meeting_id_to_folder() 사용
# =============================================================================

def get_source_docs(meeting_id: str, tdoc_number: str, data_base: Path = None, wg: str = DEFAULT_WG,
                    parsed_dir: Path = None) -> list[Path]:
    """원본 문서 묶음(`tdoc_documents`) — 바탕 문서 다음에 함께 읽는 표지. TDoc 폴더가 없으면 빈 목록."""
    if data_base is None:
        data_base = get_data_base(wg)
    folder_name = meeting_id_to_folder(meeting_id, wg, base_dir=data_base)  # -e/bis suffix glob
    # 번호→폴더와 폴더→문서 둘 다 파싱(03)과 같은 규칙이어야 같은 문서를 보강한다.
    tdoc_dir = tdoc_dir_for(data_base / folder_name / "Docs", tdoc_number)
    if not tdoc_dir:
        return []
    # > 주의: 03 이 남의 문서 사본 대신 같은 폴더의 제 문서를 읽은 번호는 산출 폴더에 그 문서를 적어 둔다.
    # 폴더 규칙으로 다시 고르면 03 이 버린 남의 문서를 보강하게 되므로, 기록이 있으면 기록을 따른다.
    if parsed_dir is not None:
        recorded = tdoc_copy_owner.recorded_documents(parsed_dir, tdoc_dir)
        if recorded is not None:
            return recorded
    return tdoc_documents(tdoc_dir)


# =============================================================================
# 그림 색인 보강
# =============================================================================

def index_entries(figs: list) -> list[dict]:
    """그림 색인의 figures 배열 — 03 의 OutputGenerator 와 같은 함수(`docx_figures.index_entry`)로 만든다."""
    return [docx_figures.index_entry(f) for f in figs]


def write_media(media_dir: Path, files: dict) -> int:
    """그림 파일 경로('media/…') → 부품 을 media_dir 에 쓰고, 색인이 가리키지 않는 파일은 지운다. 쓴 파일 수.

    파일마다 다 쓴 뒤에 제자리로 옮긴다 — 쓰는 도중 워커가 죽어도 반쯤 쓴 그림 파일이 남지 않는다.
    """
    media_dir.mkdir(parents=True, exist_ok=True)
    keep = set()
    for rel, part in files.items():
        out = media_dir.parent / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = None
        try:
            with tempfile.NamedTemporaryFile(dir=out.parent, prefix=f".{out.name}.", suffix=".tmp", delete=False) as stream:
                tmp = Path(stream.name)
                stream.write(part.blob)
            os.replace(tmp, out)
        finally:
            if tmp is not None:
                tmp.unlink(missing_ok=True)
        keep.add(out)
    for f in media_dir.rglob('*'):
        if f.is_file() and f not in keep:
            f.unlink()
    return len(keep)


def enhance_single_tdoc(args: tuple) -> dict:
    """문서 하나 — 03 이 쓴 그림 색인을 같은 규칙으로 다시 얻어 대조하고, 그림 파일과 개수를 채운다."""
    parsed_dir, meeting_id, tdoc_number, data_base, wg = args
    figures_index = parsed_dir / 'figures' / 'index.json'

    try:
        with open(figures_index, encoding='utf-8') as f:
            written = json.load(f).get('figures')

        # 03 이 그림 색인을 쓴 문서인데 원본을 못 찾으면 그림 파일을 채울 수 없다 — 건너뜀이 아니라 오류다.
        docx_paths = get_source_docs(meeting_id, tdoc_number, data_base, wg, parsed_dir)
        if not docx_paths:
            return {'status': 'error', 'tdocNumber': tdoc_number, 'error': 'no_source_docx'}

        # 묶음 문서마다 03 과 같은 규칙으로 그림을 얻고(`document_figures`), 03 과 같은 함수(`docx_figures.bundle`)로
        # 번호를 잇고 표지의 그림 파일 경로를 `media/cover…/` 로 옮긴다.
        docs, groups = zip(*(document_figures(p, tdoc_number) for p in docx_paths))
        groups = docx_figures.bundle(groups, tdoc_number)
        entries = index_entries([f for g in groups for f in g])
        if entries != written:
            return {'status': 'error', 'tdocNumber': tdoc_number,
                    'error': f"stale_03_index: 03 색인 {len(written or [])}항목 · 다시 얻은 색인 {len(entries)}항목"}

        media = {}
        for doc, figs in zip(docs, groups):
            for path, part in (docx_figures.media_parts(doc, figs) if figs else {}).items():
                if media.setdefault(path, part) is not part:
                    raise ValueError(f"그림 파일 경로 {path} 에 묶음 문서 둘의 부품")
        media_files = write_media(parsed_dir / 'figures' / 'media', media)

        # 개수 키(Spec §3.6): image_count = 그림 항목 수 · caption_count = 캡션이 있는 항목 수 ·
        # matched_count = 그림 파일과 짝지은 항목 수(filePath 가 있는 항목).
        counts = {
            'image_count': len(entries),
            'caption_count': sum(1 for e in entries if e['caption']),
            'matched_count': sum(1 for e in entries if e['filePath'])
        }

        # 다 쓴 뒤에 제자리로 옮긴다 — 쓰는 도중 워커가 죽어도 반쯤 쓴 파일이 남지 않는다.
        write_json_atomic(figures_index, {
                'tdocNumber': tdoc_number,
                'meetingId': meeting_id,
                'figures': entries,
                **counts
            })

        return {
            'status': 'success',
            'tdocNumber': tdoc_number,
            'meetingId': meeting_id,
            'media_files': media_files,
            **counts
        }

    except Exception as e:
        return {
            'status': 'error',
            'tdocNumber': tdoc_number,
            'error': f"{type(e).__name__}: {e}"
        }


def _enhanced(figures_index: Path) -> bool:
    """이미 보강한 그림 색인인가 — 개수 키는 04 만 쓴다(03 이 쓴 색인에는 없다).

    읽지 못하는 색인은 보강 대상으로 남겨 그 문서의 오류로 드러나게 한다.
    """
    try:
        return 'image_count' in json.loads(figures_index.read_text(encoding='utf-8'))
    except ValueError:
        return False


# =============================================================================
# 메인 로직
# =============================================================================

def collect_tasks(parsed_base: Path, data_base: Path, wg: str = DEFAULT_WG,
                   meeting_filter: str = None, resume: bool = False, tdoc_filter: str | None = None) -> list[tuple]:
    """Enhancement 대상 수집 — 03 이 그림 색인을 쓴 문서. (대상, 이어 받기로 건너뛴 수, 그림 색인 없는 문서 수)."""
    selected = tdoc_selection.parsed_target(parsed_base, wg, meeting_filter, tdoc_filter)
    tasks = []
    skipped = 0
    no_index = 0

    for meeting_dir in sorted(parsed_base.iterdir()):
        if not meeting_dir.is_dir() or not meeting_dir.name.startswith(f"{wg}#"):
            continue

        meeting_id = meeting_dir.name

        # 회의 필터
        if meeting_filter and meeting_id != meeting_filter:
            continue

        for tdoc_dir in sorted(meeting_dir.iterdir()):
            if not tdoc_dir.is_dir():
                continue

            tdoc_number = tdoc_dir.name
            if selected is not None and tdoc_number != selected:
                continue

            # 03 은 그림 개체가 있는 문서에만 그림 색인을 쓴다 — 색인이 없으면 보강할 것이 없다.
            figures_index = tdoc_dir / 'figures' / 'index.json'
            if not figures_index.exists():
                no_index += 1
                continue

            # Resume 모드: 이미 보강한 색인만 건너뛴다(03 이 쓴 그대로인 색인은 보강 대상).
            if resume and _enhanced(figures_index):
                skipped += 1
                continue

            tasks.append((tdoc_dir, meeting_id, tdoc_number, data_base, wg))

    return tasks, skipped, no_index


def main():
    parser = argparse.ArgumentParser(description="Phase-6 Figure 이미지 추출")
    parser.add_argument("--workers", type=int, default=4, help="병렬 워커 수")
    parser.add_argument("--resume", action="store_true", help="이미 보강한 그림 색인 건너뛰기")
    parser.add_argument("--meeting", type=str, help="특정 회의만 처리 (예: RAN4#118)")
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

    DATA_BASE = get_data_base(args.wg)
    PARSED_BASE = get_parsed_base(args.wg)

    print("=" * 70)
    print(f"Phase-6 Figure 이미지 추출 Enhancement (WG: {args.wg})")
    print("=" * 70)
    print(f"워커: {args.workers}")
    print(f"Resume: {args.resume}")
    if args.meeting:
        print(f"회의 필터: {args.meeting}")
    print("=" * 70)

    # 작업 수집
    print("\n[작업 수집]")
    tasks, skipped, no_index = tdoc_selection.collect_or_error(parser, collect_tasks, PARSED_BASE, DATA_BASE, wg=args.wg, meeting_filter=args.meeting, resume=args.resume, tdoc_filter=args.tdoc)

    print(f"처리 대상: {len(tasks)}")
    if skipped > 0:
        print(f"건너뛴 문서: {skipped}")
    print(f"그림 색인 없는 문서(보강 대상 아님): {no_index}")

    if args.limit > 0:
        tasks = tasks[:args.limit]
        print(f"제한 적용: {len(tasks)} 문서만 처리")

    if not tasks:
        print("처리할 문서가 없습니다.")
        return

    # 병렬 처리
    print("\n[Figure 추출 시작]")
    start_time = time.time()

    results = []
    errors = []

    completed = 0
    total_images = 0

    # 묶음마다 새 풀을 띄워 RAN 공용 풀(pool_run)로 돈다 — 워커가 죽어도(메모리 상한 등) 끝나지 못한
    # 문서를 워커를 줄여 다시 돌리고, 문서마다 순환 GC 를 돌려 python-docx · lxml 트리가 워커에 쌓이지 않게 한다.
    for i in range(0, len(tasks), POOL_SLICE):
        for result in pool_run.run_all(enhance_single_tdoc, [(t,) for t in tasks[i:i + POOL_SLICE]],
                                       args.workers, log):
            completed += 1

            if result['status'] == 'success':
                results.append(result)
                total_images += result.get('image_count', 0)
            elif result['status'] == 'error':
                errors.append(result)

            if completed % 100 == 0 or completed == len(tasks):
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                print(f"  진행: {completed}/{len(tasks)} ({completed*100/len(tasks):.1f}%) "
                      f"| 속도: {rate:.1f} docs/s | 이미지: {total_images}")

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
        print("\n[Figure 통계]")
        print(f"  이미지 포함 문서: {sum(1 for r in results if r.get('image_count', 0) > 0)}")
        print(f"  총 그림 항목: {sum(r.get('image_count', 0) for r in results)}")
        print(f"  캡션 있는 항목: {sum(r.get('caption_count', 0) for r in results)}")
        print(f"  그림 파일 있는 항목: {sum(r.get('matched_count', 0) for r in results)}")
        print(f"  쓴 그림 파일: {sum(r.get('media_files', 0) for r in results)}")

    if errors:
        print("\n[오류 목록 (처음 5개)]")
        for err in errors[:5]:
            print(f"  {err['tdocNumber']}: {err.get('error', 'unknown')[:60]}")

    # 리포트 저장
    log_dir = LOG_DIR / args.wg / "phase-6"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_path = log_dir / f"enhance_figures_{timestamp}.json"

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
                'total_images': sum(r.get('image_count', 0) for r in results),
                'total_captions': sum(r.get('caption_count', 0) for r in results),
                'total_matched': sum(r.get('matched_count', 0) for r in results),
                'total_media_files': sum(r.get('media_files', 0) for r in results),
                'docs_with_images': sum(1 for r in results if r.get('image_count', 0) > 0),
                'docs_without_index': no_index,
                'skipped_resume': skipped
            },
            'errors': errors  # 실패자 목록은 자르지 않는다. 수만 남고 이름이 사라지면 어느 문서가 빠졌는지 되짚을 길이 없다.
        }, f, indent=2, ensure_ascii=False)

    print(f"\n리포트 저장: {report_path}")

    # 오류가 하나라도 있으면 종료 코드 1 — 파이프라인(set -e · pipefail)이 이 단계를 실패로 받는다.
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
