#!/usr/bin/env python3
"""
RAN3 Phase-0 Step-6: DOC→DOCX 변환

처리 산출물 슬롯(`derived`)의 .doc 파일을 LibreOffice headless로 .docx 로 제자리 변환한다.
추출과 변환이 같은 슬롯에 쓰므로 입력면과 출력면이 같다 — .docx 복사 분기는
목적지가 곧 원본이라 늘 건너뛴다.

대상: meetings + change-requests

Usage:
    python3 scripts/tsg/RAN/formal/RAN3/phase-0/transform/01_transform_doc_to_docx.py
    python3 scripts/tsg/RAN/formal/RAN3/phase-0/transform/01_transform_doc_to_docx.py --target meetings
    python3 scripts/tsg/RAN/formal/RAN3/phase-0/transform/01_transform_doc_to_docx.py --target change-requests
    python3 scripts/tsg/RAN/formal/RAN3/phase-0/transform/01_transform_doc_to_docx.py --workers 4
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
import io
import zipfile
import zlib
from functools import lru_cache
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(PROJECT_ROOT / "scripts/tsg/RAN/formal/common"))
from native_word_conversion import publish_validated_conversion, validate_docx  # noqa: E402
sys.path.insert(0, str(PROJECT_ROOT / "scripts/common/common"))
from atomic_io import copy_file_atomic, write_json_atomic  # noqa: E402
sys.path.insert(0, str(PROJECT_ROOT / "scripts/common/bootstrap"))
from process_stream import stop_process_group  # noqa: E402
WG = "RAN3"

# 대상 하나에 슬롯 하나. 변환은 그 슬롯 안에서 제자리로 일어난다.
TARGETS = {
    "meetings": PROJECT_ROOT / "data" / "corpus" / "tsg" / "RAN" / "formal" / "meetings" / WG / "derived",
    "change-requests": PROJECT_ROOT / "data" / "corpus" / "tsg" / "RAN" / "formal" / "change-requests" / WG / "derived",
}

# 변환 제한 시간은 문서 구조와 실행 환경에 맞춰 배치별 환경변수로 조정한다.
CONVERT_TIMEOUT_SEC = int(os.environ.get("SPECTRA_DOC_CONVERT_TIMEOUT", "600"))

LOG_DIR = PROJECT_ROOT / "logs" / "tsg" / "RAN" / "formal" / WG / "phase-0" / "transform"


def link_or_copy(src: Path, dest: Path) -> None:
    """하드링크 또는 공용 원자적 복사로 완성된 파일을 게시한다."""
    if dest.is_symlink():
        raise ValueError(f"변환 출력은 심볼릭 링크를 사용할 수 없습니다: {dest}")
    if dest.exists() and dest.samefile(src):
        return
    with tempfile.TemporaryDirectory(prefix=".docx-link-", dir=dest.parent) as directory:
        prepared = Path(directory) / dest.name
        try:
            prepared.hardlink_to(src)
        except OSError:
            copy_file_atomic(src, dest)
        else:
            os.replace(prepared, dest)


def check_libreoffice():
    result = subprocess.run(["which", "soffice"], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"LibreOffice: {result.stdout.strip()}")
        return True
    print("[ERROR] LibreOffice not found. Install: sudo apt-get install libreoffice")
    return False


def is_libreoffice_output(docx_path: Path) -> bool:
    """이 .docx 를 우리가 만들었는가.

    LibreOffice 변환물은 docProps/app.xml 의 <Application> 에 자기 이름을 남기고,
    3GPP 배포본은 "Microsoft Office Word" 를 남기거나 app.xml 자체가 없다.
    파생물과 원본은 이름만으로 구분되지 않으므로 이 서명으로 가른다.
    """
    try:
        with zipfile.ZipFile(docx_path) as zf:
            return b"LibreOffice" in zf.read("docProps/app.xml")
    except (KeyError, OSError, zipfile.BadZipFile):
        return False


def seven_zip_member_names(archive: Path) -> frozenset | None:
    """`7z` 이 읽는 압축본의 구성원 파일 이름(폴더 없이, 소문자). 못 읽으면 None."""
    exe = shutil.which("7z") or shutil.which("7za")
    if exe is None:
        return None
    try:
        res = subprocess.run([exe, "l", "-slt", "-ba", str(archive)],
                             capture_output=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if res.returncode != 0:
        return None
    out = res.stdout.decode("utf-8", "replace")
    names = {line[7:].replace("\\", "/").rsplit("/", 1)[-1].lower()
             for line in out.splitlines() if line.startswith("Path = ")}
    return frozenset(names) if names else None


@lru_cache(maxsize=64)
def zip_files_in(directory: Path) -> dict:
    """폴더 안 `.zip` 파일을 확장자 대소문자를 접은 이름으로 찾는 표. 폴더가 없으면 빈 표."""
    try:
        return {p.name.lower(): p for p in directory.iterdir()
                if p.suffix.lower() == ".zip" and p.is_file()}
    except OSError:
        return {}


@lru_cache(maxsize=256)
def archive_member_names(zip_path: Path) -> frozenset | None:
    """배포 ZIP 구성원의 파일 이름(폴더 없이, 소문자). 열리지 않으면 None.

    이름만 `.zip` 이고 내용이 7-Zip 인 배포본이 있다(해제기도 `7z` 로 연다). ZIP 으로
    열리지 않으면 `seven_zip_member_names` 로 넘긴다.

    UTF-8 표시가 없는 구성원 이름은 zipfile 이 cp437 로 읽는다. 해제기가 다른 부호계로
    풀었을 수 있으므로 원래 바이트를 UTF-8 · CP949 · CP932 로도 읽어 함께 넣는다.
    """
    try:
        with zipfile.ZipFile(zip_path) as zf:
            infos = zf.infolist()
    except zipfile.BadZipFile:
        return seven_zip_member_names(zip_path)
    except OSError:
        return None
    return infos_member_names(infos)


def infos_member_names(infos) -> frozenset:
    """ZIP 구성원 목록의 파일 이름(폴더 없이, 소문자). 부호계 처리는 `archive_member_names` 와 같다."""
    names = set()
    for info in infos:
        base = info.filename.rsplit("/", 1)[-1]
        names.add(base.lower())
        if info.flag_bits & 0x800:
            continue
        try:
            raw = base.encode("cp437")
        except UnicodeEncodeError:
            continue
        for enc in ("utf-8", "cp949", "cp932"):
            try:
                names.add(raw.decode(enc).lower())
            except UnicodeDecodeError:
                pass
    return frozenset(names)


@lru_cache(maxsize=256)
def nested_member_names(zip_path: Path, folders: tuple) -> frozenset | None:
    """`zip_path` 를 푼 자리에서 `folders` 를 따라 내려간 곳에 풀린 안쪽 ZIP 의 구성원 이름.

    해제기는 ZIP 안의 `Y.zip` 을 그 옆 `Y/` 로 푼다. 풀린 `Y.zip` 이 derived 에 남지 않은 자리에서는
    위로 올라가며 처음 만나는 짝 ZIP 이 바깥 ZIP 이고, 그 구성원 목록에는 안쪽 ZIP 의 구성원이 없다.
    바깥 목록만 보면 안쪽 배포본이 이 단계의 산출물로 읽혀 같은 이름 `.doc` 의 변환물이 배포본을
    덮는다(RAN5 R5-252974 의 `38.533 12.4.1.1 TT/38.533 12.4.1.1 TT.docx`). 그래서 폴더 이름과
    짝인 `<폴더>.zip` 구성원을 따라 안쪽 ZIP 으로 내려간다. 짝이 없는 폴더는 ZIP 안의 보통 폴더다.

    내려갈 안쪽 ZIP 이 없으면 빈 집합, 내려가야 하는데 열지 못하면 None 이다.
    """
    want = [f.lower() + ".zip" for f in folders]
    outer = archive_member_names(zip_path)
    if not outer or not any(w in outer for w in want):
        return frozenset()
    try:
        zf = zipfile.ZipFile(zip_path)
    except (zipfile.BadZipFile, OSError):
        return None
    opened = [zf]
    try:
        cur = zf
        for w in want:
            hit = next((i for i in cur.infolist()
                        if not i.is_dir() and w in infos_member_names([i])), None)
            if hit is not None:
                cur = zipfile.ZipFile(io.BytesIO(cur.read(hit)))
                opened.append(cur)
        return frozenset() if cur is zf else infos_member_names(cur.infolist())
    except (zipfile.BadZipFile, NotImplementedError, OSError, EOFError, zlib.error):
        return None
    finally:
        for archive in reversed(opened):
            archive.close()


def shipped_in_archive(path: Path) -> bool | None:
    """이 파일이 압축 해제기가 그 폴더에 푼 배포 ZIP 의 구성원인가.

    해제기는 `X.zip` 을 같은 자리의 `X/` 폴더로 푼다. 수집 원본 슬롯(`source`)의 ZIP 은
    처리 산출물 슬롯(`derived`)의 같은 상대 위치로, derived 안에서 다시 나온 ZIP 은 그
    옆 폴더로 풀린다. 짝 ZIP 의 확장자는 대소문자를 접어 찾는다(`.ZIP` 배포본이 있다).
    파일이 든 폴더에서 위로 올라가며 짝 ZIP 을 찾고, 처음 찾은 ZIP 의
    구성원 이름에 이 파일 이름이 있는지를 돌려준다. 경로에 `derived` 가 없거나, 짝 ZIP 이
    없거나, 짝 ZIP 이 열리지 않으면 None 이다.
    """
    parts = path.parts
    if "derived" not in parts:
        return None
    i = len(parts) - 1 - parts[::-1].index("derived")
    derived_root = Path(*parts[:i + 1])
    source_root = Path(*parts[:i]) / "source"
    d = path.parent
    while d != derived_root and derived_root in d.parents:
        rel = d.relative_to(derived_root)
        for archive in (zip_files_in(d.parent).get(d.name.lower() + ".zip"),
                        zip_files_in(source_root / rel.parent).get(rel.name.lower() + ".zip")):
            if archive is not None:
                names = archive_member_names(archive)
                if names is None:
                    return None
                if path.name.lower() in names:
                    return True
                inner = nested_member_names(archive, path.parent.relative_to(d).parts)
                if inner is None:
                    return None
                return path.name.lower() in inner
        d = d.parent
    return None


def is_own_derivative(docx_path: Path) -> bool:
    """이 .docx 가 변환 단계의 산출물인가 — 배포 ZIP 에 없던 파일인가.

    판별자는 배포 ZIP 구성원 여부다(`shipped_in_archive`). 생성기 서명
    (`is_libreoffice_output`)은 양쪽으로 틀린다. 다른 도구로 만든 옛 변환물은 서명이 없어
    배포본으로 읽히고, 그러면 같은 `.doc` 이 `X.doc.docx` 로 한 번 더 변환된다. 기고자가
    LibreOffice 로 만든 배포본은 우리 산출물로 읽히고, 그러면 파생물이 배포본의 이름을
    차지한다. 서명은 짝 ZIP 을 찾지 못하거나 열지 못할 때만 쓴다.
    """
    shipped = shipped_in_archive(docx_path)
    if shipped is None:
        return is_libreoffice_output(docx_path)
    return not shipped


def is_ooxml(path: Path) -> bool:
    """이름은 .doc 인데 내용이 OOXML(docx) 인가.

    기고자가 docx 를 `.doc` 이름으로 올리는 일이 있다. LibreOffice 는 이름이 아니라
    내용을 보므로 이것도 변환은 해낸다 — 다만 이미 목적 형식인 문서를 우리 손으로 다시
    인코딩해 배포본 바이트를 파생물로 갈아 끼우고, 필요 없던 그 단계가 끝나지 않으면
    산출이 아예 없어 그 TDoc 이 하류에서 통째로 빠진다. 여기에는 변환할 것이 없다 —
    하류가 찾을 이름이 없을 뿐이다.

    `is_libreoffice_output` 과 같은 원리로 이름이 아니라 내용으로 가른다. 두 바이트를
    먼저 보므로 진짜 OLE `.doc` 에는 사실상 비용이 없다.
    """
    try:
        with path.open("rb") as fh:
            if fh.read(2) != b"PK":
                return False
        with zipfile.ZipFile(path) as zf:
            return "word/document.xml" in zf.namelist()
    except (OSError, zipfile.BadZipFile):
        return False


def is_drm_wrapped(path: Path) -> bool:
    """기고자가 사내 DRM 으로 감싸 올린 파일인가.

    LibreOffice 는 이런 컨테이너 앞에서 멈추지 않는다. 열지 못한 바이트를 텍스트로
    읽어 그대로 옮겨 적고 종료코드 0 으로 끝내므로 이름도 크기도 정상인 `.docx` 가
    남는다. 그 안에는 DRM 헤더를 UTF-16 으로 읽은 글자가 수만 자 들어 있다 —
    실패가 성공한 산출물의 모습으로 남는 자리라 계수만 보는 눈에는 잡히지 않고,
    하류 파서는 그것을 문서 본문으로 읽는다.

    현재 변환 경로에서 지원하는 DRM 서명을 확인한다.
    해당 파일은 변환 대상에서 제외하고 미변환 사유로 기록한다.
    """
    try:
        with path.open("rb") as fh:
            head = fh.read(16)
    except OSError:
        return False
    return b"NASCA" in head or head.startswith(b"%TSD-")


def stale_drm_derivatives(path: Path) -> list[Path]:
    """DRM 래퍼 `path` 곁에 앞선 실행이 남긴 변환물.

    주의: 래퍼를 변환기에 보내지 않는 판정(`is_drm_wrapped`)이 생기기 전 실행은 래퍼를 LibreOffice 로
    변환해 깨진 바이트를 본문으로 담은 `.docx` 를 남겼다(R2-1708441). 래퍼는 이제 일감이 아니므로 그 산출
    이름을 claim 하는 항목이 없고, 남은 변환물은 배포본처럼 `.docx` 일감에 섞여 하류 파서가 본문으로
    읽는다. 판정을 고쳐도 재실행이 이 자리를 지우지 않으면 고친 효과가 코퍼스에 닿지 않는다.
    지우기는 되돌릴 수 없으므로 서로 다른 두 근거가 모두 우리 것이라고 할 때만 고른다 — 배포 ZIP 에
    없던 파일이고(`is_own_derivative`) LibreOffice 서명을 지녔을 때.
    """
    found = []
    for cand in (path.with_suffix(".docx"), Path(str(path) + ".docx")):
        if (cand != path and cand.is_file() and not cand.samefile(path)
                and is_own_derivative(cand) and is_libreoffice_output(cand)):
            found.append(cand)
    return found


OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


def ole_named_docx(path: Path) -> str | None:
    """이름은 .docx 인데 내용이 OLE 복합문서인가. 그렇다면 무엇을 담았는지, 아니면 None.

    기고자가 Word 97-2003 문서를 `.docx` 이름으로 올리는 일이 있다. 확장자로 가르면 이
    파일은 이미 목적 형식으로 셈되어 변환기에 가지 않고, 하류 파서는 ZIP 이 아니라서 열지
    못한다 — 그 TDoc 은 본문 없는 문서로 남는다. LibreOffice 는 이름이 아니라 내용을 보므로
    이 파일도 변환해 낸다. `is_ooxml`(이름은 .doc 인 OOXML)의 거울 자리다.

    같은 OLE 그릇에 암호화(IRM)된 OOXML 이 든 경우가 있다(`EncryptedPackage` 스트림).
    암호화된 본문은 현재 변환 경로의 지원 범위에 따라 변환 대상에서 제외한다.

    돌려주는 값: "word97" 변환 대상 · "irm" 열 수 없음 · None OLE 가 아님.
    """
    try:
        with path.open("rb") as fh:
            if fh.read(8) != OLE_MAGIC:
                return None
            marker = "EncryptedPackage".encode("utf-16-le")
            tail = b""
            while block := fh.read(io.DEFAULT_BUFFER_SIZE):
                window = tail + block
                if marker in window:
                    return "irm"
                tail = window[-(len(marker) - 1):]
    except OSError:
        return None
    return "word97"


def needs_conversion(path: Path) -> bool:
    """변환을 거쳐야 읽히는 파일인가 — `.doc` 전부와, 내용이 OLE · DRM 인 `.docx`.

    `.docx` 가운데 IRM · DRM 은 변환기에도 보내지 않지만 여기서는 참이다. 산출이 없는 채로
    `unconverted_docs` 에 남아야 원장이 그 TDoc 이 빠진 이유를 적는다.
    """
    suffix = path.suffix.lower()
    if suffix == ".doc":
        return True
    return suffix == ".docx" and (is_drm_wrapped(path) or ole_named_docx(path) is not None)


def conversion_target(doc_path: Path) -> Path:
    """산출물이 쓸 이름. 처리는 제자리이므로 늘 .doc 과 같은 디렉토리다.

    같은 이름의 .docx 가 이미 있는데 그것이 우리 산출물이 아니면(`is_own_derivative`),
    그 .docx 는 배포 ZIP 에 .doc 과 함께 들어온 별개의 원본이다. 파생물이 원본의 이름을
    차지하면 원본이 트리에서 사라지므로, 그 자리에서만 확장자를 겹쳐 쓴다
    (`X.doc` -> `X.doc.docx`).

    이름만 .docx 인 옛 문서(`ole_named_docx`)는 그 이름을 원본 자신이 차지하고 있다.
    원본은 우리 산출물이 아니므로 같은 갈래를 타 확장자를 겹쳐 적는다
    (`X.docx` -> `X.docx.docx`).

    내용이 이미 OOXML 인 `.doc` 은 변환이 아니라 이름만 붙이는 일이다(`is_ooxml`).
    그 자리에 우리 재인코딩본이 있으면 원본 바이트가 이름을 되찾는다 — 원본을 그대로
    둘 수 있는데 재인코딩본을 남길 이유가 없다. 배포본이 차지하고 있으면 별개의
    문서이므로 비켜 적는다.

    재실행 안전: 판정 근거가 파일 내용이라 이미 처리한 자리는 언제나 같은 이름으로
    돌아온다. 이름만 붙인 자리는 대상과 같은 파일이 되므로(`samefile`) 그 자체가
    고정점이다 — 이 갈래가 없으면 산출 이름이 재실행마다 한 칸씩 밀린다.

    주의: 앞선 규칙이 코퍼스에 남긴 두 자리는 이 함수가 알아보지 못한다.
    (1) 배포본 `X.docx` 를 옛 실행이 `X.doc` 의 변환물로 덮어쓴 자리. 이름은 여전히 ZIP
    구성원이라 `shipped_in_archive` 는 배포본으로 읽는다. 이름이 아니라 ZIP 구성원의 바이트와
    견주어야 드러나고, 찾으면 ZIP 에서 배포본을 되살린다. 되살리면 폴더에 `X.docx` 와
    `X.doc.docx` 가 함께 남으므로 파서가 어느 판을 고르는지 다시 본다(`docx_pick.drop_shipped_twins`).
    (2) 배포되지 않은 옛 변환물 `X.docx` 곁의 `X.doc.docx`. 지금 규칙의 대상은 `X.docx` 이므로
    `X.doc.docx` 는 옛 규칙(생성기 서명 판별)이 비켜 적은 산출이다. 코퍼스에서 지운다.
    """
    stem_target = doc_path.parent / (doc_path.stem + ".docx")
    if is_ooxml(doc_path):
        if not stem_target.exists():
            return stem_target
        if stem_target.samefile(doc_path):
            return stem_target
        if is_own_derivative(stem_target):
            return stem_target
        return doc_path.parent / (doc_path.name + ".docx")
    if stem_target.exists() and not is_own_derivative(stem_target):
        return doc_path.parent / (doc_path.name + ".docx")
    return stem_target

def unconverted_docs(derived_dir: Path) -> list[Path]:
    """변환물 없는 옛 형식 문서(`needs_conversion`). 결정량이므로 지름길에서도 반드시 잰다.

    일감이 없다는 것과 미변환이 없다는 것은 다른 말이다. 앞의 것을 뒤의 것으로
    적으면 변환기에 보낼 수 없는 파일만 남은 슬롯이 "이상 없음"으로 보이고,
    슬롯이 통째로 빠진 자리도 조용해진다 — 이 트랙에서 반복해 나온 공허 통과다.
    """
    return [f for f in derived_dir.rglob("*")
            if f.is_file() and needs_conversion(f)
            and not conversion_target(f).exists()]


def convert_doc_to_docx(doc_path: Path, output_file: Path) -> dict:
    """문서 하나를 변환하고 자식 프로세스와 임시 디렉터리를 정리한다."""
    profile_dir = out_dir = None
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        if output_file.exists() and output_file.stat().st_size > 0:
            validate_docx(output_file)
            return {'success': True, 'file': str(doc_path), 'skipped': True}
        profile_dir = Path(tempfile.mkdtemp(prefix="lo_RAN3_"))
        out_dir = Path(tempfile.mkdtemp(prefix="loout_RAN3_"))
        cmd = ['soffice', '--headless', f'-env:UserInstallation=file://{profile_dir}',
               '--convert-to', 'docx', '--outdir', str(out_dir), str(doc_path)]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, start_new_session=(os.name == 'posix'))
        try:
            _, stderr = process.communicate(timeout=CONVERT_TIMEOUT_SEC)
        except subprocess.TimeoutExpired:
            stop_process_group(process)
            return {'success': False, 'file': str(doc_path),
                    'error': f"Timeout ({CONVERT_TIMEOUT_SEC}s)", 'timeout': True}
        except BaseException:
            stop_process_group(process)
            raise
        produced = out_dir / (doc_path.stem + '.docx')
        if process.returncode != 0:
            return {'success': False, 'file': str(doc_path),
                    'error': stderr.strip() if stderr else 'Unknown error'}
        if not produced.exists() or produced.stat().st_size == 0:
            return {'success': False, 'file': str(doc_path), 'error': 'Output file not created'}
        publish_validated_conversion(produced, output_file, doc_path,
                                     soffice="soffice", timeout=CONVERT_TIMEOUT_SEC)
        return {'success': True, 'file': str(doc_path)}
    except Exception as exc:
        return {'success': False, 'file': str(doc_path), 'error': f"Exception: {exc}"}
    finally:
        for owned_dir in (out_dir, profile_dir):
            if owned_dir is not None:
                shutil.rmtree(owned_dir, ignore_errors=True)


def copy_docx(docx_path: Path, output_file: Path) -> dict:
    """이미 목적 형식인 파일을 산출 이름에 건다.

    자리가 이미 차 있을 때 그냥 건너뛰면, 앞선 실행이 남긴 우리 재인코딩본이 원본을
    영영 가린다. 자리에 있는 것이 대상 자신이면 고정점이라 할 일이 없고, 우리
    산출물이면 원본 바이트가 그 이름을 되찾고, 배포본이면 건드리지 않는다.
    """
    try:
        validate_docx(docx_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        if output_file.exists():
            # 배포 ZIP 구성원 여부와 생성기 서명이 모두 우리 파생물로 가리킬 때 교체한다.
            if output_file.samefile(docx_path) or not (is_own_derivative(output_file)
                                                      and is_libreoffice_output(output_file)):
                validate_docx(output_file)
                return {"success": True, "file": str(docx_path), "skipped": True}
        link_or_copy(docx_path, output_file)
        return {"success": True, "file": str(docx_path), "copied": True}
    except Exception as e:
        return {"success": False, "file": str(docx_path), "error": str(e)}

def process_file(file_info: tuple) -> dict:
    file_path, output_file, file_type = file_info
    if file_type == "docx":
        return copy_docx(file_path, output_file)
    elif file_type == "doc":
        return convert_doc_to_docx(file_path, output_file)
    return {"success": False, "file": str(file_path), "error": f"Unknown: {file_type}"}


def transform_target(target_name, derived_dir, max_workers):
    print(f"\n{'='*70}")
    print(f"[{WG}] {target_name} DOC→DOCX 변환")
    print(f"{'='*70}")
    print(f"  슬롯: {derived_dir} (제자리 변환)")

    if not derived_dir.exists():
        print("  [WARN] 디렉토리 없음")
        return {"target": target_name, "total": 0,
                "unconverted_doc": 0, "slot_missing": True}

    doc_items = []
    docx_paths = []
    drm_wrapped = []
    irm_encrypted = []
    for file_path in sorted(derived_dir.rglob("*")):
        if not file_path.is_file():
            continue
        suffix = file_path.suffix.lower()
        if suffix not in [".doc", ".docx"]:
            continue
        if suffix == ".doc":
            if is_drm_wrapped(file_path):
                drm_wrapped.append(file_path)
                continue
            output_file = conversion_target(file_path)
            kind = "docx" if is_ooxml(file_path) else "doc"
            doc_items.append((file_path, output_file, kind))
        elif is_drm_wrapped(file_path):
            drm_wrapped.append(file_path)
        elif (ole := ole_named_docx(file_path)) == "irm":
            irm_encrypted.append(file_path)
        elif ole == "word97":
            # 이름은 .docx 이나 내용은 옛 .doc 이다. 산출 이름의 자리를 원본 자신이 차지하고
            # 있으므로 `conversion_target` 이 확장자를 겹쳐 적는다(`X.docx` -> `X.docx.docx`).
            doc_items.append((file_path, conversion_target(file_path), "doc"))
        else:
            docx_paths.append(file_path)

    # DRM 래퍼의 옛 변환물은 배포본처럼 보여 `.docx` 일감에 섞인다(`stale_drm_derivatives`).
    # 일감에서 빼고 코퍼스에서 지운다.
    drm_stale = sorted({s for p in drm_wrapped for s in stale_drm_derivatives(p)})
    docx_paths = [p for p in docx_paths if p not in set(drm_stale)]
    for stale in drm_stale:
        stale.unlink()

    # 제자리 처리라 한 항목의 산출 자리가 다른 항목의 입력 자리다. `X.doc` 이 산출
    # 이름으로 `X.docx` 를 claim 하면 그 `.docx` 는 독립한 일감이 아니다 — 둘을 따로
    # 보내면 한 워커가 비우는 자리를 다른 워커가 읽어, 파일은 옳게 끝나는데 기록만
    # 실패로 남는다. 결과가 맞으니 아무도 들여다보지 않는 실패다. claim 된 자리는
    # 일감에서 뺀다.
    claimed = {out for _, out, _ in doc_items}
    files_to_process = doc_items + [
        (p, p, "docx") for p in docx_paths if p not in claimed
    ]

    if drm_wrapped:
        print(f"  DRM 래퍼 — 변환 대상에서 제외: {len(drm_wrapped)}건")
    if drm_stale:
        print(f"  DRM 래퍼의 옛 변환물 — 코퍼스에서 지움: {len(drm_stale)}건")
    if irm_encrypted:
        print(f"  암호화(IRM) OOXML — 변환 대상에서 제외: {len(irm_encrypted)}건")

    doc_count = sum(1 for _, _, t in files_to_process if t == "doc")
    docx_count = sum(1 for _, _, t in files_to_process if t == "docx")
    print(f"  .doc 변환: {doc_count}, .docx 복사: {docx_count}, 총: {len(files_to_process)}")

    stats = {
        "target": target_name, "total": len(files_to_process),
        "doc_converted": 0, "docx_copied": 0, "skipped": 0,
        "errors": [], "timeouts": [],
        "drm_wrapped": [str(p) for p in drm_wrapped],
        "drm_stale_removed": [str(p) for p in drm_stale],
        "irm_encrypted": [str(p) for p in irm_encrypted],
    }

    start = time.time()
    completed = 0

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_file, fi): fi for fi in files_to_process}
        for future in as_completed(futures):
            result = future.result()
            completed += 1
            if result["success"]:
                if result.get("skipped"):
                    stats["skipped"] += 1
                elif result.get("copied"):
                    stats["docx_copied"] += 1
                else:
                    stats["doc_converted"] += 1
            else:
                if result.get("timeout"):
                    stats["timeouts"].append(result["file"])
                else:
                    stats["errors"].append({"file": result["file"], "error": result.get("error", "")})

            if completed % 500 == 0:
                elapsed = time.time() - start
                rate = completed / elapsed if elapsed > 0 else 0
                eta = (len(files_to_process) - completed) / rate if rate > 0 else 0
                print(f"    {completed}/{len(files_to_process)} "
                      f"({completed*100//len(files_to_process)}%) | "
                      f"{rate:.1f} f/s | ETA {eta/60:.1f}min")

    elapsed = time.time() - start
    stats["elapsed_min"] = round(elapsed / 60, 1)

    print(f"\n  결과: 변환 {stats['doc_converted']}, 복사 {stats['docx_copied']}, "
          f"스킵 {stats['skipped']}, 에러 {len(stats['errors'])}, "
          f"타임아웃 {len(stats['timeouts'])}")
    print(f"  소요: {elapsed/60:.1f}분")

    if stats["errors"]:
        print("  에러 상위 5건:")
        for e in stats["errors"][:5]:
            print(f"    {Path(e['file']).name}: {e['error'][:60]}")

    # 결정량: 자기 변환물이 없는 .doc 수.
    #
    # 추출과 변환이 같은 슬롯에 쓰므로 .doc 은 변환 뒤에도 제자리에 남는다.
    # "남은 .doc 수"로는 변환 여부를 알 수 없고, 두 트리(extracted/transformed)를
    # 세어 대조하던 옛 표현도 슬롯이 하나가 되면서 성립하지 않는다. 결정량 자체는
    # 그대로다 — 변환물 없는 .doc 이 0이어야 한다. 누락되면 하류 Phase 에서 그
    # 문서의 인스턴스가 통째로 빠진다.
    unconverted = unconverted_docs(derived_dir)
    stats["unconverted_doc"] = len(unconverted)
    if unconverted:
        print(f"  [WARN] 변환물 없는 옛 형식 문서: {len(unconverted)}건")
        for f in unconverted[:10]:
            print(f"    - {f.relative_to(derived_dir)}")
        if len(unconverted) > 10:
            print(f"    ... 외 {len(unconverted) - 10}건")
    else:
        print("  변환물 없는 옛 형식 문서: 0건")

    return stats


def main():
    parser = argparse.ArgumentParser(description=f"{WG} Phase-0 Step-6: DOC→DOCX")
    parser.add_argument("--target", choices=["meetings", "change-requests", "all"], default="all")
    parser.add_argument("--workers", type=int, default=4, help="병렬 워커 수 (기본: 4)")
    args = parser.parse_args()
    if args.workers <= 0:
        parser.error("--workers는 양의 정수여야 합니다")

    print("=" * 70)
    print(f"{WG} Phase-0 Step-6: DOC→DOCX Transform")
    print(f"시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Workers: {args.workers}")
    print("=" * 70)

    targets = list(TARGETS.keys()) if args.target == "all" else [args.target]
    invalid = [TARGETS[name] for name in targets
               if not TARGETS[name].is_dir()
               or not any(path.is_file() and path.suffix.lower() in {".doc", ".docx"}
                          for path in TARGETS[name].rglob("*"))]
    if invalid:
        for path in invalid:
            print(f"[ERROR] 선택한 입력 디렉토리에 DOC/DOCX 문서가 필요합니다: {path}")
        return 1
    if not check_libreoffice():
        return 1

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    all_stats = []
    for target_name in targets:
        stats = transform_target(target_name, TARGETS[target_name], args.workers)
        all_stats.append(stats)

    stats_file = LOG_DIR / f"transform_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    write_json_atomic(stats_file, all_stats)
    print(f"\n통계: {stats_file}")
    return 1 if any(stat.get("slot_missing") or stat.get("errors")
                    or stat.get("timeouts") or stat.get("unconverted_doc")
                    for stat in all_stats) else 0


if __name__ == "__main__":
    raise SystemExit(main())
