#!/usr/bin/env python3
"""
Phase-6 전체 범위 Tdoc 파싱

구현 문서: docs/tsg/RAN/formal/RAN2/phase-6/step1_parsing.md

사용법:
    # 워커 8 은 python-docx 의 문서당 메모리가 쌓여 OOM 으로 죽은 값이다. 기본 4 를 올리지 않는다.
    # 전체 실행
    python 03_parse_full_scope.py --workers 4 --resume

    # 특정 회의만 실행
    python 03_parse_full_scope.py --meetings TSGR2_121,TSGR2_122 --resume

    # 테스트 (3개 회의)
    python 03_parse_full_scope.py --test --resume
"""

import json
import os
import re
import argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool
from collections import Counter
import gc
import time
import sys

# 상위 모듈 import를 위한 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from parse_tdoc_lib import (
    find_docx_file, tdoc_documents, parse_documents,
    tdoc_number_of,
    ChunkEngine, OutputGenerator,
    convert_meeting_id, WG_FOLDER_PREFIX, WG_TDOC_PREFIX,
    MetadataResolver,
    kg_titles_in_meeting,
)

# RAN2 전용 스크립트
WG = "RAN2"
DEFAULT_WG = WG  # parse_tdoc_lib.DEFAULT_WG를 덮어씀 (아래 함수 서명 호환용)


# =============================================================================
# 설정
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[7]

# 자격증명은 공통 credentials 모듈에서 읽는다.
# 이 스크립트에 별도의 비밀번호 기본값을 두지 않는다.
_SCRIPTS_COMMON = PROJECT_ROOT / "scripts" / "common"
if str(_SCRIPTS_COMMON) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_COMMON))
from common import credentials, service_endpoints as endpoints  # noqa: E402

# docx_text에서 수행한 필드 보정은 doc_fields.STATS에 누적된다.
# 같은 문서의 본문 부품을 여러 경로에서 읽을 수 있으므로, 문서별로 보정 호출 횟수 대신
# 적용된 보정 종류를 기록한다.
sys.path.insert(0, str(_SCRIPTS_COMMON.parent / "tsg" / "RAN" / "formal" / "common"))
import doc_fields  # noqa: E402
# 동일 문서 사본들에서 각 TDoc 번호에 맞는 본문을 선택하는 공통 규칙.
import tdoc_copy_owner  # noqa: E402
import tdoc_selection  # noqa: E402

# Neo4j 접속 대상은 WG 레지스트리와 환경 설정을 대조한다.

def get_neo4j_uri(wg: str = WG) -> str:
    return endpoints.neo4j_uri(wg)


# =============================================================================
# 워커별 MetadataResolver (ProcessPoolExecutor initializer)
# =============================================================================

# 워커 프로세스 단위로 1회 생성. parse_single_tdoc()가 참조.
_WORKER_RESOLVER: MetadataResolver | None = None


def _init_worker(neo4j_uri: str, neo4j_auth: tuple, wg: str) -> None:
    """ProcessPoolExecutor 워커 초기화. 각 워커당 Neo4j 연결 1회 생성."""
    global _WORKER_RESOLVER
    _WORKER_RESOLVER = MetadataResolver(
        neo4j_uri=neo4j_uri, neo4j_auth=neo4j_auth, wg=wg
    )
    _WORKER_RESOLVER.connect()
    if not _WORKER_RESOLVER._connected:
        raise RuntimeError(
            f"[Worker init] Neo4j 연결 실패: {neo4j_uri} (wg={wg}). "
            f"Phase-1 KG가 올라와 있는지 + NEO4J_PASSWORD가 맞는지 확인."
        )

def get_data_base(wg: str) -> Path:
    return PROJECT_ROOT / "data" / "corpus" / "tsg" / "RAN" / "formal" / "meetings" / wg / "derived"

def get_output_base(wg: str) -> Path:
    return PROJECT_ROOT / "vectordb" / "parsed" / "tdocs" / wg

LOG_DIR = PROJECT_ROOT / "logs" / "tsg" / "RAN" / "formal"


# =============================================================================
# Meeting ID 매핑
# =============================================================================

def folder_to_meeting_id(folder_name: str, wg: str = DEFAULT_WG) -> str:
    """폴더명 → Meeting ID 변환 (WG-agnostic)"""
    return convert_meeting_id(folder_name, wg)


def get_all_meeting_folders(data_base: Path, wg: str = DEFAULT_WG) -> list[Path]:
    """모든 회의 폴더 반환 (WG별 접두사 자동 판별)"""
    prefix = WG_FOLDER_PREFIX.get(wg, "")
    folders = sorted([f for f in data_base.iterdir()
                      if f.is_dir() and f.name.startswith(prefix)])
    return folders


# =============================================================================
# 파싱 함수
# =============================================================================


def parse_single_tdoc(args: tuple) -> dict:
    """단일 Tdoc 파싱 (병렬 처리용)"""
    docx_paths, tdoc_number, output_base, meeting_folder, meeting_id = args
    fixes_before = Counter(doc_fields.STATS)

    try:
        # 1. 파싱(docx/docm, Spec §1.3). 본문과 함께 선택된 표지를 하나의 파싱 결과로 합친다.
        #    (`tdoc_documents` · `parse_documents`).
        content = parse_documents(docx_paths, tdoc_number)

        # 2. 청킹 (chunkId 생성 포함)
        chunker = ChunkEngine()
        chunks = chunker.chunk_sections(content.sections, tdoc_number=tdoc_number)

        # 3. 메타데이터 (Neo4j 쿼리 — 필수, fail-fast)
        if _WORKER_RESOLVER is None or not _WORKER_RESOLVER._connected:
            raise RuntimeError(
                "Worker에 연결된 MetadataResolver 없음. "
                "ProcessPoolExecutor(initializer=_init_worker, initargs=...) 로 실행하세요."
            )
        metadata = _WORKER_RESOLVER.resolve_metadata(tdoc_number, meeting_id)
        # fail-fast: Neo4j에 TDoc 노드가 없거나 속성이 전부 누락된 경우
        # KG 가 phase-6-backfill 로 등록한 문서(Phase-1 목록에 없는 회의 문서)는 빈 메타데이터로 남긴다.
        if (not metadata.get('title') and not metadata.get('source')
                and not _WORKER_RESOLVER.is_kg_placeholder(tdoc_number)):
            raise RuntimeError(
                "Neo4j metadata 조회 실패: Phase-1 KG에 TDoc 노드가 없거나 "
                "속성(title/source) 전부 누락. Phase-1 적재 상태 확인 필요."
            )

        # 4. 출력 생성
        generator = OutputGenerator(output_base)
        generator.generate(content, chunks, metadata, meeting_id)

        return {
            'status': 'success',
            'tdocNumber': tdoc_number,
            'meetingId': meeting_id,
            'type': content.doc_type,
            'paragraphCount': content.paragraph_count,
            'sectionCount': len(content.sections),
            'chunkCount': len(chunks),
            'tableCount': len(content.tables),
            'figureCount': len(content.figures),
            'equationCount': len(content.equations),
            'fieldFixes': sorted(Counter(doc_fields.STATS) - fixes_before),
        }

    except Exception as e:
        return {
            'status': 'error',
            'tdocNumber': tdoc_number,
            'meetingId': meeting_id,
            'error': str(e)
        }
    finally:
        # python-docx의 순환 참조는 lxml 트리의 C 메모리도 유지할 수 있다.
        # 문서마다 명시적으로 GC를 실행해 워커 메모리 누적을 줄인다.
        gc.collect()


# TDoc 번호의 발급 WG 접두사(`R2`·`RP`·`S2`). 현재 WG의 접두사는 WG_TDOC_PREFIX에서 얻는다.
_TDOC_ISSUER = re.compile(r"([A-Za-z]+\d*)-\d")
_OWN_ISSUER = WG_TDOC_PREFIX[DEFAULT_WG].rstrip("-").upper()


def meeting_slots(docs_folder: Path, meeting_id: str, driver,
                  claimed: dict[tuple[str, str], str] | None = None,
                  own: dict[str, Path] | None = None):
    """회의 Docs 폴더에서 선택한 (TDoc 폴더, 문서, 번호) 목록과 제외 사유를 반환한다.

    반환값은 (선택 목록, 사유별 제외 항목, 다른 TDoc의 사본으로 판정한 번호별 근거)다.
    제외 사유는 다음 다섯 종류다.

      no_docx       선택 가능한 DOCX/DOCM이 없는 폴더(pptx·pdf·xlsx 전용 문서 등)
      not_a_folder  Docs/ 바로 아래 놓인 일반 파일
      dup_slot      정규화한 TDoc 번호가 먼저 선택한 폴더와 겹치는 폴더
      foreign_copy  문서 내용과 제목 대조로 다른 TDoc의 사본이라고 판정한 번호
      foreign_wg    다른 WG가 발급한 TDoc 번호의 폴더

    `claimed`는 여러 입력 폴더가 같은 회의 ID로 정규화될 때 먼저 선택한 번호를 공유한다.
    `own`이 주어지면, 처음 선택한 사본 대신 같은 폴더에서 찾은 해당 TDoc의 문서를 기록한다.
    이 문서는 폴더 기본 선택 규칙(tdoc_documents) 대신 단독으로 파싱한다.
    Phase-10 사후 검증(post_validate._explain_kg_only)도 이 함수를 재사용해
    KG에만 있는 TDoc이 파싱 대상에서 제외된 사유를 설명한다.
    """
    claimed = {} if claimed is None else claimed
    left: dict[str, list[str]] = {"no_docx": [], "not_a_folder": [], "dup_slot": [], "foreign_copy": [],
                                  "foreign_wg": []}
    slots: list[tuple[Path, Path, str]] = []
    for tdoc_folder in sorted(docs_folder.iterdir()):
        if not tdoc_folder.is_dir():
            left["not_a_folder"].append(f"{meeting_id}/{tdoc_folder.name}")
            continue

        docx_file = find_docx_file(tdoc_folder)
        if not docx_file:
            left["no_docx"].append(f"{meeting_id}/{tdoc_folder.name}")
            continue

        # 출력 폴더는 tdoc_number_of로 정규화한 번호를 사용한다.
        # resume도 같은 번호로 기존 산출물의 존재를 확인한다.
        tdoc_number = tdoc_number_of(tdoc_folder.name)

        # 다른 WG 접두사의 TDoc은 현재 WG의 산출물·VDB·KG에 등록하지 않는다.
        # TDoc 번호 형식이 아닌 이름이나 현재 WG 번호 뒤에 접미사가 붙은 이름은
        # 이 발급 WG 검사만으로 제외하지 않는다.
        issuer = _TDOC_ISSUER.match(tdoc_number)
        if issuer and issuer.group(1).upper() != _OWN_ISSUER:
            left["foreign_wg"].append(f"{meeting_id}/{tdoc_folder.name}")
            continue

        # 공백·%20·끝 마침표·서식 문자가 다른 폴더도 같은 TDoc 번호로 정규화될 수 있다.
        # 먼저 선택한 번호의 출력을 덮어쓰지 않도록 이후 폴더는 제외 사유에 기록한다.
        # 정렬된 입력에서 먼저 나온 폴더를 유지한다.
        slot = (meeting_id, tdoc_number)
        if slot in claimed:
            left["dup_slot"].append(f"{meeting_id}/{tdoc_folder.name!r}"
                                    f" (이미 {claimed[slot]!r} 가 같은 번호를 씀)")
            continue
        claimed[slot] = tdoc_folder.name
        slots.append((tdoc_folder, docx_file, tdoc_number))

    # 같은 본문을 서로 다른 TDoc 번호로 파싱하지 않도록 문서 제목과 회의 KG 제목을 대조한다.
    # tdoc_copy_owner가 어느 번호의 본문인지 판정하지 못한 경우에는 모두 유지한다.
    foreign = tdoc_copy_owner.foreign_copies(
        {n: dx for _, dx, n in slots},
        lambda nums: kg_titles_in_meeting(driver, nums, meeting_id),
        tdoc_number_of)
    # 처음 선택한 파일이 다른 TDoc의 사본이어도 같은 폴더에 해당 TDoc의 본문이 있을 수 있다.
    # 현재 번호의 KG 제목에만 일치하는 파일이 하나면 그 파일로 선택을 바꾼다.
    # 기본 폴더 선택 규칙과 달라진 선택은 collect_tasks에서 출력 폴더에 기록한다.
    found: dict[str, Path] = {}
    if foreign:
        folder_of = {n: f for f, _, n in slots}
        picks = [dx for _, dx, _ in slots]
        titles = kg_titles_in_meeting(driver, sorted({m for n, (_, o) in foreign.items() for m in (n, *o)}),
                                      meeting_id)
        for n, (_, others) in sorted(foreign.items()):
            doc = tdoc_copy_owner.own_document(folder_of[n], picks, titles.get(n, ""),
                                               [titles.get(m, "") for m in others])
            if doc is not None:
                found[n] = doc
        foreign = {n: v for n, v in foreign.items() if n not in found}
    if own is not None:
        own.update(found)
    for n, (how, others) in sorted(foreign.items()):
        by = "제목" if how == "title" else "파일 이름"
        left["foreign_copy"].append(f"{meeting_id}/{n} ({by}으로 {', '.join(others)} 의 문서로 가림)")
    slots = [(f, found.get(n, dx), n) for f, dx, n in slots if n not in foreign]
    return slots, left, foreign


def collect_tasks(meeting_folders: list[Path], output_base: Path, driver,
                  wg: str = DEFAULT_WG, resume: bool = False,
                  tdoc_filter: str | None = None) -> list[tuple]:
    """meeting_slots로 파싱 작업을 선택한다. driver는 회의 KG 제목을 조회하는 Neo4j 연결이다."""
    selected = tdoc_selection.validate_scope(
        wg, tdoc_filter, meeting_folders[0].name if len(meeting_folders) == 1 else None,
        meeting_prefix=WG_FOLDER_PREFIX.get(wg, ""))
    found = False
    tasks = []
    skipped = 0
    # 파싱 대상에서 제외한 문서의 이름과 사유를 기록한다.
    # 이후 KG와 VDB의 문서 차이를 진단할 때 입력 부재와 선택 제외를 구분할 수 있다.
    left: dict[str, list[str]] = {"no_docx": [], "not_a_folder": [], "dup_slot": [], "foreign_copy": [],
                                  "foreign_wg": []}
    no_docs_folder = []
    stale = []         # 다른 TDoc의 사본으로 제외한 번호에 남은 이전 산출물
    regained = []      # 같은 폴더에서 해당 TDoc의 문서를 찾아 선택을 바꾼 번호
    claimed: dict[tuple[str, str], str] = {}

    for meeting_folder in meeting_folders:
        meeting_id = folder_to_meeting_id(meeting_folder.name, wg)
        docs_folder = meeting_folder / "Docs"

        if not docs_folder.exists():
            print(f"  ⚠️ Docs 폴더 없음: {meeting_folder.name}")
            no_docs_folder.append(meeting_folder.name)
            continue

        own: dict[str, Path] = {}
        slots, out, foreign = meeting_slots(docs_folder, meeting_id, driver, claimed, own)
        regained.extend(f"{meeting_id}/{n} → {own[n].name}" for n in sorted(own))
        for k, v in out.items():
            left[k].extend(v)
        # 사본 제외 판정은 resume 검사 전에 수행한다.
        # 이전 실행이 다른 TDoc의 본문으로 만든 산출물은 여기서 삭제하지 않고 이름을 보고한다.
        stale.extend(f"{meeting_id}/{n}" for n in sorted(foreign)
                     if (output_base / meeting_id / n / "chunks.json").exists())

        for tdoc_folder, docx_file, tdoc_number in slots:
            if selected is not None and tdoc_number != selected:
                continue
            found = True
            parsed_dir = output_base / meeting_id / tdoc_number
            documents = [own[tdoc_number]] if tdoc_number in own else None
            # Resume은 기존 chunks.json이 있고 이전과 현재의 문서 선택 기록이 같을 때만 건너뛴다.
            # 이전에 다른 TDoc 사본을 읽었던 경우는 tdoc_copy_owner.RECORD로 구분한다.
            if resume:
                output_chunks = parsed_dir / "chunks.json"
                if (output_chunks.exists()
                        and tdoc_copy_owner.recorded_documents(parsed_dir, tdoc_folder) == documents):
                    skipped += 1
                    continue

            # 기본 입력은 tdoc_documents가 선택한 본문과 표지다.
            # 문서가 하위 폴더에 있어도 TDoc 번호는 상위 TDoc 폴더에서 정규화한 값을 전달한다.
            # 사본 대신 찾은 문서는 단독으로 읽고, 04·05 후처리도 같은 파일을 읽도록 기록한다.
            # 기본 폴더 선택으로 돌아간 경우에는 이전의 별도 문서 선택 기록을 지운다.
            tdoc_copy_owner.sync_record(parsed_dir, tdoc_folder, documents)
            tasks.append((tuple(documents or tdoc_documents(tdoc_folder)), tdoc_number, output_base,
                          meeting_folder.name, meeting_id))

    if any(left.values()) or no_docs_folder:
        print(f"  파싱 대상에서 제외: .docx 없는 Tdoc 폴더 {len(left['no_docx'])}건"
              f" · 폴더가 아닌 항목 {len(left['not_a_folder'])}건"
              f" · Docs 폴더 없는 회의 {len(no_docs_folder)}건"
              f" · 번호가 겹친 폴더 {len(left['dup_slot'])}건"
              f" · 남의 문서 사본 {len(left['foreign_copy'])}건"
              f" · 다른 WG 번호 폴더 {len(left['foreign_wg'])}건")
        if left["no_docx"]:
            print(f"    .docx 없음 예: {left['no_docx'][:5]}")
        if left["dup_slot"]:
            print(f"    번호 겹침: {left['dup_slot']}")
        if left["foreign_copy"]:
            print(f"    남의 문서 사본: {left['foreign_copy']}")
        if left["foreign_wg"]:
            print(f"    다른 WG 번호 폴더: {left['foreign_wg']}")
    if stale:
        print(f"  ⚠️ 남의 문서 사본으로 뺀 번호에 앞 실행의 산출이 남아 있음 {len(stale)}건: {stale}")
    if regained:
        print(f"  남의 문서 사본으로 가렸다가 같은 폴더의 제 문서로 되돌린 번호 {len(regained)}건: {regained}")

    tdoc_selection.require_found(selected, found, meeting_folders[0].name if meeting_folders else "")
    return tasks, skipped


# 풀 하나에서 워커 한 개가 처리하는 문서 수. Python 3.10의 ProcessPoolExecutor는 워커를 교체하지 않아,
# 큰 문서를 지날 때마다 늘어난 힙이 워커에 그대로 남는다(워커 셋 · 6G 상한에서 워커당 약 1,500건째에 OOM).
# 이만큼마다 풀을 새로 띄워 힙을 운영체제에 돌려준다. 풀을 다시 띄우는 비용(fork · Neo4j 연결)은
# 문서 수백 건을 파싱하는 시간에 비해 작다.
DOCS_PER_WORKER_POOL = 100


def _parse_in_pool(tasks: list[tuple], workers: int, initargs: tuple) -> tuple[list, list]:
    """한 풀에서 tasks 를 파싱한다. 워커가 죽어 풀이 깨지면 끝내지 못한 task 를 돌려준다."""
    finished, unfinished = [], []
    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=_init_worker,
        initargs=initargs,
    ) as executor:
        futures = {executor.submit(parse_single_tdoc, task): task for task in tasks}
        for future in as_completed(futures):
            try:
                finished.append(future.result())
            except BrokenProcessPool:
                unfinished.append(futures[future])
    return finished, unfinished


def run_parallel_parsing(
    tasks: list[tuple],
    workers: int,
    neo4j_uri: str,
    neo4j_auth: tuple,
    wg: str,
) -> tuple[list, list, float]:
    """병렬 파싱 실행. 각 워커는 _init_worker로 Neo4j 연결을 1회 생성.

    풀은 워커당 DOCS_PER_WORKER_POOL 건마다 새로 띄운다. 워커가 죽어 풀이 깨지면(메모리 상한
    초과 등) 끝내지 못한 문서를 한 건씩 따로 다시 파싱하고, 그래도 워커를 죽이는 문서만 실패로 남긴다.
    """
    results = []
    errors = []
    initargs = (neo4j_uri, neo4j_auth, wg)
    slice_size = workers * DOCS_PER_WORKER_POOL
    completed = 0

    start_time = time.time()

    def record(result: dict):
        nonlocal completed
        completed += 1

        if result['status'] == 'success':
            results.append(result)
        else:
            errors.append(result)

        # 진행 상황 출력 (100개마다)
        if completed % 100 == 0 or completed == len(tasks):
            elapsed = time.time() - start_time
            rate = completed / elapsed if elapsed > 0 else 0
            print(f"  진행: {completed}/{len(tasks)} ({completed*100/len(tasks):.1f}%) "
                  f"| 속도: {rate:.1f} docs/s | 성공: {len(results)} | 실패: {len(errors)}")

    for i in range(0, len(tasks), slice_size):
        finished, unfinished = _parse_in_pool(tasks[i:i + slice_size], workers, initargs)
        for result in finished:
            record(result)
        for task in unfinished:
            retried, lost = _parse_in_pool([task], 1, initargs)
            for result in retried:
                record(result)
            for _docx_paths, tdoc_number, _output_base, _meeting_folder, meeting_id in lost:
                record({
                    'status': 'error',
                    'tdocNumber': tdoc_number,
                    'meetingId': meeting_id,
                    'error': 'worker process died (memory limit exceeded?)',
                })

    elapsed = time.time() - start_time
    return results, errors, elapsed


def print_summary(results: list, errors: list, elapsed: float, total_tasks: int):
    """결과 요약 출력"""
    print("\n" + "=" * 70)
    print("결과 요약")
    print("=" * 70)
    print(f"총 처리: {total_tasks}")
    print(f"성공: {len(results)}")
    print(f"실패: {len(errors)}")
    print(f"성공률: {len(results) / total_tasks * 100:.1f}%" if total_tasks > 0 else "N/A")
    print(f"소요 시간: {elapsed:.1f}초 ({elapsed/60:.1f}분)")
    print(f"처리 속도: {total_tasks / elapsed:.1f} docs/s" if elapsed > 0 else "N/A")

    if results:
        print("\n[회의별 분포]")
        meeting_counter = Counter(r['meetingId'] for r in results)
        for meeting_id, count in sorted(meeting_counter.items()):
            print(f"  {meeting_id}: {count}")

        print("\n[유형별 분포]")
        type_counter = Counter(r['type'] for r in results)
        for doc_type, count in type_counter.most_common():
            pct = count / len(results) * 100
            print(f"  {doc_type}: {count} ({pct:.1f}%)")

        print("\n[청크 통계]")
        total_chunks = sum(r['chunkCount'] for r in results)
        total_paras = sum(r['paragraphCount'] for r in results)
        print(f"  총 청크: {total_chunks}")
        print(f"  총 문단: {total_paras}")
        print(f"  평균 청크/문서: {total_chunks / len(results):.1f}")

    fixes = Counter(k for r in results for k in r.get('fieldFixes', ()))
    if fixes:
        print("\n[필드 보정 — 종류별 문서 수]")
        for kind, count in sorted(fixes.items()):
            print(f"  {kind}: {count}")

    if errors:
        print("\n[오류 목록 (처음 10개)]")
        for err in errors[:10]:
            print(f"  {err['meetingId']}/{err['tdocNumber']}: {err['error'][:60]}...")


def save_report(results: list, errors: list, elapsed: float, mode: str, wg: str = WG):
    """리포트 저장"""
    log_dir = LOG_DIR / wg / "phase-6"
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_path = log_dir / f"parse_full_scope_{mode}_{timestamp}.json"

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'mode': mode,
            'timestamp': timestamp,
            'summary': {
                'total': len(results) + len(errors),
                'success': len(results),
                'failed': len(errors),
                'success_rate': len(results) / (len(results) + len(errors)) * 100 if results or errors else 0,
                'elapsed_seconds': elapsed,
                'docs_per_second': (len(results) + len(errors)) / elapsed if elapsed > 0 else 0
            },
            'meeting_distribution': dict(Counter(r['meetingId'] for r in results)),
            'type_distribution': dict(Counter(r['type'] for r in results)),
            # doc_fields.STATS의 보정 종류별로 해당 보정이 적용된 문서 수를 기록한다.
            'field_fix_documents': dict(sorted(Counter(
                k for r in results for k in r.get('fieldFixes', ())).items())),
            'errors': errors  # 실패한 문서 목록은 자르지 않는다. 수만 남고 이름이 사라지면 어느 문서가 빠졌는지 되짚을 길이 없다.
        }, f, indent=2, ensure_ascii=False)

    print(f"\n리포트 저장: {report_path}")
    return report_path


# =============================================================================
# 메인 함수
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Phase-6 전체 범위 Tdoc 파싱")
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="병렬 처리 워커 수 (기본: 4 — 8 은 OOM 으로 죽은 값이다)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="이미 파싱된 문서 건너뛰기"
    )
    parser.add_argument(
        "--meetings",
        type=str,
        help="특정 회의만 실행 (쉼표 구분, 예: TSGR2_131,TSGR2_132)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="테스트 모드 (3개 회의만 실행)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="처리할 최대 문서 수 (0=전체)"
    )

    tdoc_selection.add_argument(parser)
    args = parser.parse_args()
    tdoc_selection.validate_arguments(parser, args, wg=DEFAULT_WG, meeting_prefix=WG_FOLDER_PREFIX.get(getattr(args, "wg", DEFAULT_WG), ""))

    # RAN2 전용 경로
    DATA_BASE = get_data_base(WG)
    OUTPUT_BASE = get_output_base(WG)

    print("=" * 70)
    print(f"Phase-6 전체 범위 Tdoc 파싱 (WG: {WG})")
    print("=" * 70)

    # 회의 폴더 선택
    if args.test:
        # 테스트 모드: 마지막 3개 회의
        all_folders = get_all_meeting_folders(DATA_BASE, WG)
        meeting_folders = all_folders[-3:] if len(all_folders) >= 3 else all_folders
        mode = "test"
        print(f"모드: 테스트 ({len(meeting_folders)}개 회의)")
    elif args.meetings:
        # 특정 회의
        folder_names = [n.strip() for n in args.meetings.split(",")]
        missing = [name for name in folder_names if not (DATA_BASE / name).is_dir()]
        if missing:
            # 없는 이름을 빼고 나머지만 돌리면 그 회의는 파싱되지 않은 채 성공으로 끝난다.
            sys.exit(f"회의 폴더 없음: {', '.join(missing)} ({DATA_BASE})")
        meeting_folders = [DATA_BASE / name for name in folder_names]
        mode = "custom"
        print(f"모드: 커스텀 ({len(meeting_folders)}개 회의)")
    else:
        # 전체 실행
        meeting_folders = get_all_meeting_folders(DATA_BASE, WG)
        mode = "full"
        print(f"모드: 전체 ({len(meeting_folders)}개 회의)")

    print(f"워커: {args.workers}")
    print(f"Resume: {args.resume}")
    print(f"출력: {OUTPUT_BASE}")
    print("=" * 70)

    # 회의 목록 출력
    print(f"\n[대상 회의 ({len(meeting_folders)}개)]")
    for folder in meeting_folders:
        meeting_id = folder_to_meeting_id(folder.name, WG)
        print(f"  {folder.name} → {meeting_id}")

    # 출력 디렉토리 생성
    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

    # meeting_slots는 회의 KG 제목으로 동일 문서 사본의 TDoc 번호를 구분한다.
    # 작업을 선택하기 전에 제목 조회에 필요한 Neo4j 연결부터 확인한다.
    neo4j_uri = get_neo4j_uri(WG)
    neo4j_auth = credentials.neo4j_auth()
    kg = MetadataResolver(neo4j_uri=neo4j_uri, neo4j_auth=neo4j_auth, wg=WG)
    try:
        kg.connect()
        if not kg._connected:
            sys.exit(f"Neo4j 연결 실패: {neo4j_uri} — 남의 문서 사본을 가릴 KG 제목을 읽을 수 없습니다")

        # 작업 수집
        print("\n[작업 수집]")
        tasks, skipped = tdoc_selection.collect_or_error(parser, collect_tasks, meeting_folders, OUTPUT_BASE, kg._driver, wg=WG, resume=args.resume, tdoc_filter=args.tdoc)
    finally:
        kg.close()

    print(f"파싱 대상: {len(tasks)}")
    if skipped > 0:
        print(f"건너뛴 문서 (이미 파싱됨): {skipped}")

    if args.limit > 0:
        tasks = tasks[:args.limit]
        print(f"제한 적용: {len(tasks)} 문서만 처리")

    if not tasks:
        print("파싱할 문서가 없습니다.")
        return

    print(f"Neo4j: {neo4j_uri}")

    # 병렬 파싱 실행
    print("\n[파싱 시작]")
    results, errors, elapsed = run_parallel_parsing(
        tasks,
        workers=args.workers,
        neo4j_uri=neo4j_uri,
        neo4j_auth=neo4j_auth,
        wg=WG,
    )

    # 결과 요약
    print_summary(results, errors, elapsed, len(tasks))

    # 리포트 저장
    save_report(results, errors, elapsed, mode, wg=WG)

    # 성공률 검증
    success_rate = len(results) / len(tasks) * 100 if tasks else 0
    if success_rate >= 95:
        print(f"\n✅ 품질 검증 통과: {success_rate:.1f}% ≥ 95%")
    else:
        print(f"\n⚠️ 품질 검증 실패: {success_rate:.1f}% < 95%")
        # 기준 미달은 단계 실패다. 문서 단위 오류가 기준 안이면 0 으로 끝나 전체 일괄 실행이 깨진 원본 몇 개로 멈추지 않는다.
        sys.exit(1)


if __name__ == "__main__":
    main()
