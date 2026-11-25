#!/usr/bin/env python3
"""
Extract RAN3 Change Request ZIP files
- `source/<Release>/TSG/` 의 zip 을 전부 푼다(CR 목록 `metadata/cr_list.csv` 로 거르지 않는다)
- 안쪽 zip 까지 끝까지 푼다(zip 옆 제 이름 폴더, zip 은 남긴다)
- Parallel extraction with 8 workers
- Resume capability (skip already extracted, nested zips re-checked)
"""

import argparse
import logging
import shutil
import subprocess
import sys
import zipfile
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

# Paths
WORKSPACE_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts" / "common" / "common"))
import os_residue  # noqa: E402
import zip_names  # noqa: E402 — 플래그 없이 담긴 UTF-8 이름을 되찾아 푼다
import rar_archive  # noqa: E402 — 7z 가 풀지 못하는 RAR 를 libarchive 로 푼다
SOURCE_DIR = WORKSPACE_ROOT / "data" / "corpus" / "tsg" / "RAN" / "formal" / "change-requests" / "RAN3" / "source"
EXTRACT_DIR = WORKSPACE_ROOT / "data" / "corpus" / "tsg" / "RAN" / "formal" / "change-requests" / "RAN3" / "derived"
LOG_DIR = WORKSPACE_ROOT / "logs" / "tsg" / "RAN" / "formal" / "RAN3" / "phase-0" / "extract" / "change-requests"


def setup_logging():
    """실행할 때만 로그 파일을 연다 — 모듈을 읽기만 하는 시험·점검이 빈 로그를 남기지 않게."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def pack_zips():
    """`source/<Release>/TSG/` 아래 모든 ZIP 파일을 선택한다.

    포털 CR 목록(`metadata/cr_list.csv`)은 수집 이후 회의의 묶음이나 RP 번호로 배포된
    총회 CR을 포함하지 않을 수 있으므로 `tsg_tdoc` 열로 ZIP을 필터링하지 않는다.
    Phase-4 표지 파서와 Phase-8 CR 청크 생성기가 derived의 묶음 폴더를 읽으므로,
    이 단계에서 제외한 CR은 후속 KG·VectorDB 구축에도 포함되지 않는다.
    모든 Release 폴더를 확인하며, `.ZIP`·`.Zip`도 선택하도록 확장자의 대소문자를 구분하지 않는다.
    """
    return sorted(p for p in SOURCE_DIR.glob("Rel-*/TSG/*")
                  if p.is_file() and p.suffix.lower() == ".zip")


def drop_failed_output(directory):
    """실패한 추출의 출력 디렉터리와 부분 파일을 삭제한다.

    비어 있지 않은 디렉터리는 재실행 시 건너뛰므로 실패한 부분 파일을 남기지 않는다.
    기존 내용이 있는 디렉터리는 호출부의 skipped 분기에서 처리한다.
    """
    shutil.rmtree(directory, ignore_errors=True)


def extract_with_7z(archive, dest):
    """zipfile 이 열지 못한 아카이브를 7z 로 연다. 7z 이 없으면 실패로 돌린다."""
    exe = shutil.which("7z") or shutil.which("7za")
    if exe is None:
        return False
    try:
        result = subprocess.run([exe, "x", "-y", "-p-", f"-o{dest}", "--", str(archive)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                timeout=600)
    except (OSError, subprocess.SubprocessError):
        return False
    # 종료코드 0 만 성공으로 본다. 7z 은 지원하지 않는 압축 방식을 만나면 0바이트 자리표를
    # 만들어 두고 오류로 끝낸다 — 산출물의 존재를 성공의 증거로 삼지 않는다.
    return result.returncode == 0 and dest.is_dir() and any(dest.iterdir())


def extract_nested_archives(extract_dir, max_depth, current_depth):
    """해제된 트리 안의 zip 을 이어서 연다. 실패한 안쪽 zip 의 결과 목록을 돌려준다.

    TSG 묶음 zip 은 CR 마다 WG 회의 TDoc zip 을 담고, 그 안에 다시 시험 허용치 분석 zip 을
    담기도 한다. 확장자는 접어서 찾고, 추출 잔재(`__MACOSX/` 아래 · `._*`)는 zip 이름을
    달고 있어도 열지 않는다.
    """
    if current_depth >= max_depth:
        return []
    failed = []
    nested_zips = sorted(
        p for p in extract_dir.rglob("*")
        if p.is_file() and p.suffix.lower() == ".zip"
        and os_residue.classify_path(p.relative_to(extract_dir)) is None
    )
    for nested_zip in nested_zips:
        failed.extend(r for r in extract_zip_recursive(nested_zip, max_depth, current_depth + 1)
                      if r[0] in ('bad_zip', 'error'))
    return failed


def extract_zip_recursive(zip_path, max_depth=10, current_depth=0, dest=None):
    """zip 하나를 풀고 안쪽 zip 을 끝까지 푼다. [(상태, 경로)] — 이 zip 과 실패한 안쪽 zip.

    바깥 zip 은 `EXTRACT_DIR` 의 같은 상대 자리에 제 이름 폴더로 푼다. 안쪽 zip 은 zip 옆에
    제 이름 폴더로 풀고 zip 은 남긴다 — 회의 추출기(`extract_meetings.py`)와 같은 배치다.
    zip 을 지우고 안쪽 항목을 바깥 폴더에 평평하게 쏟으면, 변환 단계가 문서가 원본 zip 에
    담겨 온 것인지 제 변환본인지를 가리지 못해, 담겨 온 `.docx` 를 옆 `.doc` 의 변환본으로
    덮어쓴다. 같은 이름의 항목을 담은 두 안쪽 zip 도 한 자리에서 서로 덮는다.
    """
    if current_depth == 0:
        extract_dir = dest if dest is not None else EXTRACT_DIR / zip_path.relative_to(SOURCE_DIR).parent / zip_path.stem
    else:
        extract_dir = zip_path.parent / zip_path.stem

    if extract_dir.exists() and not extract_dir.is_dir():
        logging.error(f"✗ 목적지가 파일이라 풀 수 없음: {extract_dir}")
        return [('error', zip_path)]

    # 기존 디렉터리는 바깥 ZIP을 다시 해제하지 않고, 안쪽 ZIP의 누락된 추출 결과를 확인한다.
    if extract_dir.exists() and any(extract_dir.iterdir()):
        return [('skipped', zip_path)] + extract_nested_archives(extract_dir, max_depth, current_depth)

    extracted = False
    try:
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_names.extractall(zip_ref, extract_dir)
        os_residue.purge(extract_dir)
        extracted = True
        return [('success', zip_path)] + extract_nested_archives(extract_dir, max_depth, current_depth)

    except (zipfile.BadZipFile, NotImplementedError, zlib.error, EOFError):
        # zip 이어도 zipfile 이 못 푸는 것이 깨졌다는 뜻은 아니다 — Deflate64(압축 방식 9)는
        # NotImplementedError 로 멈추고, 온전한 zip 한 벌 뒤에 다른 판의 꼬리가 남은 zip 은
        # CRC 오류로 멈추지만 7z 은 둘 다 온전히 푼다. 7z 로 풀기 전에 zipfile 이 쓴 항목을
        # 지운다 — 두 도구가 이름 인코딩을 다르게 읽으면 같은 항목이 두 이름으로 겹쳐 남는다.
        # 7z 해제가 실패하면 RAR 형식인지 확인하고 libarchive 해제를 시도한다.
        drop_failed_output(extract_dir)
        if extract_with_7z(zip_path, extract_dir) or rar_archive.extract(zip_path, extract_dir):
            os_residue.purge(extract_dir)
            extracted = True
            return [('success', zip_path)] + extract_nested_archives(extract_dir, max_depth, current_depth)
        drop_failed_output(extract_dir)
        logging.error(f"✗ Bad ZIP file: {zip_path}")
        return [('bad_zip', zip_path)]
    except Exception as e:
        drop_failed_output(extract_dir)
        logging.error(f"✗ Error extracting {zip_path}: {e}")
        return [('error', zip_path)]
    finally:
        if not extracted:
            drop_failed_output(extract_dir)


def main():
    parser = argparse.ArgumentParser(description='Extract RAN3 Change Request ZIP files')
    parser.add_argument('--workers', type=int, default=8, help='Number of parallel workers (default: 8)')
    parser.add_argument('--dest', type=Path, default=None,
                        help='derived 대신 이 폴더 아래에 같은 배치로 푼다(빈 폴더에서 다시 만들어 견줄 때)')
    args = parser.parse_args()
    global EXTRACT_DIR
    if args.dest is not None:
        EXTRACT_DIR = args.dest.resolve()
    setup_logging()

    logging.info("="*60)
    logging.info("RAN3 Change Requests Extraction")
    logging.info(f"Source: {SOURCE_DIR}")
    logging.info(f"Extract to: {EXTRACT_DIR}")
    logging.info(f"Workers: {args.workers}")
    logging.info("="*60)

    if not SOURCE_DIR.exists():
        logging.error(f"Source directory not found: {SOURCE_DIR}")
        return 1

    zip_files = pack_zips()
    if not zip_files:
        logging.warning("No ZIP files found")
        return 1

    logging.info(f"TSG zip: {len(zip_files)}")

    counts = {'success': 0, 'skipped': 0, 'bad_zip': 0, 'error': 0}
    nested_failed = {}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(extract_zip_recursive, zip_file): zip_file for zip_file in zip_files}
        with tqdm(total=len(zip_files), desc="Extracting CRs") as pbar:
            for future in as_completed(futures):
                results = future.result()
                counts[results[0][0]] += 1
                nested_failed.update((r[1], r[0]) for r in results[1:] if r[0] in ('bad_zip', 'error'))
                pbar.update(1)

    logging.info("="*60)
    logging.info("Extraction Summary")
    logging.info(f"Total: {len(zip_files)}")
    logging.info(f"Success: {counts['success']}")
    logging.info(f"Skipped (already extracted): {counts['skipped']}")
    logging.info(f"Failed: {counts['bad_zip'] + counts['error']}")
    logging.info(f"안쪽 zip 실패: {len(nested_failed)}")
    for path, status in sorted(nested_failed.items(), key=lambda r: str(r[0])):
        logging.info(f"  {status}: {path}")
    logging.info("="*60)
    return 1 if counts['bad_zip'] + counts['error'] or nested_failed else 0


if __name__ == "__main__":
    sys.exit(main())
