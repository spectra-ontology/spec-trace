"""TSG RAN 총회 문서의 원문 글을 뽑아 SQLite FTS5 색인 하나를 만든다 (모델 호출 없음).

왜 만드는가
  원문만 보는 식별자 경로(`measure_raw_source_route.py`)는 CR 묶음(RP-)이 어떤 CR 을 담았고 어느 총회에
  올라갔는지를 기록에서 읽지 않고 총회 문서의 글에서 찾는다. 작업반 청크 컬렉션에는 총회 문서가 없으므로
  원본 zip 에서 글을 직접 뽑는다.

무엇을 읽는가
  `data/corpus/tsg/RAN/formal/meetings/TSG_RAN/source/TSGR_*/{Docs,Report}` 와
  `data/corpus/tsg/RAN/formal/change-requests/TSG_RAN/source/Rel-*/` 아래 파일 전부. 두 트리는 같은 파일을
  하드 링크로 나눠 가지므로 inode 하나를 한 번만 읽는다. 바이트가 같은 파일(sha256)은 글을 한 번만 남기고
  경로와 번호를 모두 붙인다. `meetings/TSG_RAN/derived/` 에 같은 줄기 이름의 폴더가 있으면 그 폴더의 파일을
  읽는다(Phase-0 이 이미 풀어 둔 결과).

문서 번호
  문서의 번호는 파일 이름이다. zip 줄기 이름을 대문자로 바꾸고 줄표 변형(U+2010~U+2015, U+2212)을 `-` 로
  맞춘다. zip 안 항목은 담은 zip 의 번호에 더해 항목 경로(폴더·파일 이름)에 적힌 `R[1-5]-`·`RP-` 번호를
  자기 번호로 갖는다. 회의 폴더 이름(`TSGR_85` 따위)과 기록에서 온 값은 쓰지 않는다.

글 뽑기
  zip 은 안의 zip 까지 따라 푼다. 파이썬 zipfile 이 열지 못하는 파일(RAR · 7z · 중앙 디렉터리가 없는 zip)은
  7z 로 푼다. 항목 형식마다 `raw_source_text.file_text`(워드는 저장소 표준 `docx_text`)로 읽는다. Word 97-2003
  이진 문서(.doc · .dot)는 먼저 `word97_text.doc_text` 로 바로 읽고, 그 판독기가 읽지 못한 문서(Word 6/95 형식 ·
  OLE 가 아닌 파일 따위)만 그 까닭을 남긴 뒤 LibreOffice 로 넘긴다. 다른 옛 이진 형식(.xls · .ppt · .rtf …)은
  LibreOffice 로 OOXML 로 바꾼 뒤 읽는다. 항목마다 읽은 판독기(`reader`)와, 바로 읽은 .doc 에서 글로 싣지 않은
  수식 개체 · 그림 · 도형 · 글상자 글자 수(`omissions`)를 남긴다. 판독기가 UTF-16 대리 쌍을 반쪽씩 낸 글
  (PDF 의 글자 대응표 따위)은 짝이 맞는 두 반쪽을 한 글자로 합치고, 짝 없는 반쪽은 U+FFFD 로 바꿔 그 수를
  `omissions.loneSurrogates` 로 남긴다(짝 없는 반쪽은 UTF-8 로 저장할 수 없다).
  변환·읽기 시간 한도는 멈춘 프로세스를 끊기 위한 것이다. 한 zip 의 옛 형식을 한꺼번에 바꾸다 한도에 걸리면
  그 묶음의 결과를 버리고(끊긴 순간 쓰던 파일이 잘렸을 수 있다) 하나씩 다시 바꾼다. 하나씩 바꾸다 한도에 걸린
  항목은 까닭 "변환 시간 초과", 읽기 한도에 걸린 항목은 "읽기 시간 초과" 로 세고, 성공한 항목의 가장 긴
  시간을 함께 남겨 한도가 결과를 바꿨는지 보인다. 읽지 못한 항목은 모두 까닭별로 세고
  `plenary_failures.jsonl` 에 하나씩 남긴다.

청크
  Phase-6 기고문 재청킹(`scripts/tsg/RAN/formal/RAN1/phase-6/tdoc-parser/07_rechunk_all.py` 의
  `MAX_TOKENS = 2000`, `count_tokens` 의 1 토큰 = 4 글자)과 같은 상한 8000 글자로 줄 경계에서 자른다.
  한 줄이 상한보다 길면 상한 앞의 마지막 공백에서 나누고, 공백이 없으면 상한에서 자른다.

산출 (Git 추적 밖 런타임 산출물)
  logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/raw_source_route/index/plenary.sqlite3
  logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/raw_source_route/plenary_census.json
  logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/raw_source_route/plenary_failures.jsonl
  작업 중에는 `plenary.sqlite3.partial` 에 쌓고, 다시 실행하면 이미 담은 inode 를 건너뛴다.

자원
  사용 가능한 메모리가 8 GiB 아래로 내려가면 새 파일을 넘기지 않고 멈춘다(다시 실행하면 이어 간다).
  풀어 둔 항목은 파일마다 만든 임시 폴더에 두고 파일을 다 읽으면 지운다.

사용 (저장소 루트에서):
  PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark \\
    python3 scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/build_plenary_index.py \\
    [--workers 16] [--scratch <임시 폴더>] [--limit N]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import shutil
import signal
import sqlite3
import statistics
import subprocess
import tempfile
import time
import zipfile
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from concurrent.futures.process import BrokenProcessPool
from pathlib import Path

import raw_source_text as rst
import word97_text

ROOT = next(path for path in Path(__file__).resolve().parents if (path / ".git").exists())
TRACK = ROOT / "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
OUT_DIR = TRACK / "final/raw_source_route"
INDEX = OUT_DIR / "index/plenary.sqlite3"
CENSUS = OUT_DIR / "plenary_census.json"
FAILURES = OUT_DIR / "plenary_failures.jsonl"
MEETINGS = Path("data/corpus/tsg/RAN/formal/meetings/TSG_RAN/source")
DERIVED = Path("data/corpus/tsg/RAN/formal/meetings/TSG_RAN/derived")
CR_TREE = Path("data/corpus/tsg/RAN/formal/change-requests/TSG_RAN/source")
# 07_rechunk_all.py 의 MAX_TOKENS(2000) × count_tokens 의 4 글자.
CHUNK_CHARS = 2000 * 4
CONVERT_SECONDS = 300
READ_SECONDS = 900
SEVENZ_SECONDS = 600
MIN_AVAILABLE_GIB = 8.0
NATIVE_WORD = (".doc", ".dot")
DASHES = dict.fromkeys(map(ord, "‐‑‒–—―−"), "-")
# 파일 이름에서는 번호 앞에 밑줄이 붙으므로(`38213_CR0058_(Rel-15)_R1-1909887.docx`) 낱말 경계(`\\b`) 대신
# 앞 글자가 영문·숫자가 아닌 자리에서 찾는다. 뒤 경계는 측정 스크립트의 `DOC_RE`·`PACK_RE` 와 같다.
DOC_RE = re.compile(r"(?<![A-Za-z0-9])R[1-5]-\d{5,7}(?!\d)", re.I)
PACK_RE = re.compile(r"(?<![A-Za-z0-9])RP-\d{6}(?!\d)", re.I)
SCHEMA = """
CREATE TABLE inodes(inode TEXT PRIMARY KEY, file_id INTEGER NOT NULL, paths TEXT NOT NULL);
CREATE TABLE files(id INTEGER PRIMARY KEY, sha256 TEXT UNIQUE, bytes INTEGER, paths TEXT NOT NULL, names TEXT NOT NULL,
                   opener TEXT, outcome TEXT NOT NULL, reason TEXT, detail TEXT, seconds REAL);
CREATE TABLE owners(own TEXT NOT NULL, file_id INTEGER NOT NULL, UNIQUE(own, file_id));
CREATE TABLE members(id INTEGER PRIMARY KEY, file_id INTEGER NOT NULL, chain TEXT NOT NULL, ext TEXT NOT NULL,
                     bytes INTEGER, outcome TEXT NOT NULL, reason TEXT, detail TEXT, chars INTEGER,
                     convert_seconds REAL, read_seconds REAL, depth INTEGER NOT NULL, reader TEXT,
                     native_fallback TEXT, native_detail TEXT, omissions TEXT);
CREATE TABLE member_owner(own TEXT NOT NULL, member_id INTEGER NOT NULL);
CREATE TABLE chunks(id INTEGER PRIMARY KEY, member_id INTEGER NOT NULL, file_id INTEGER NOT NULL, seq INTEGER NOT NULL,
                    text TEXT NOT NULL);
CREATE TABLE build_info(name TEXT PRIMARY KEY, value TEXT);
"""
POST = ("CREATE VIRTUAL TABLE search USING fts5(text, content='chunks', content_rowid='id', "
        "tokenize='unicode61 remove_diacritics 2')",
        "INSERT INTO search(search) VALUES ('rebuild')",
        "INSERT INTO search(search) VALUES ('optimize')",
        "CREATE INDEX owners_own ON owners(own)", "CREATE INDEX member_owner_own ON member_owner(own)",
        "CREATE INDEX chunks_member ON chunks(member_id, seq)", "CREATE INDEX chunks_file ON chunks(file_id)",
        "CREATE INDEX members_file ON members(file_id)")


def available_gib() -> float:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 1024 ** 2
    raise RuntimeError("MemAvailable 를 읽지 못했다")


SURROGATE = re.compile("[\ud800-\udfff]")


def paired(text: str) -> tuple[str, int]:
    """반쪽으로 나온 UTF-16 대리 쌍을 합친 글과 짝이 없어 U+FFFD 로 바꾼 반쪽 수."""
    if not SURROGATE.search(text):
        return text, 0
    fixed = text.encode("utf-16-le", "surrogatepass").decode("utf-16-le", "replace")
    return fixed, fixed.count("\ufffd") - text.count("\ufffd")


def own_number(name: str) -> str:
    """파일 이름에서 확장자를 뗀 줄기를 문서 번호로 쓴다."""
    return Path(name).stem.translate(DASHES).upper()


def numbers_in(text: str) -> list[str]:
    plain = text.translate(DASHES)
    found = [match.upper() for match in DOC_RE.findall(plain)] + [match.upper() for match in PACK_RE.findall(plain)]
    return list(dict.fromkeys(found))


def macos_extra(name: str) -> bool:
    """macOS 가 zip 에 덧붙이는 부속 파일(`__MACOSX/` 아래, `._` 로 시작, `.DS_Store`)."""
    parts = name.replace("\\", "/").split("/")
    return "__MACOSX" in parts or parts[-1].startswith("._") or parts[-1] == ".DS_Store"


def census_paths() -> tuple[list[dict], dict]:
    """두 트리의 파일을 inode 로 묶는다. 묶음 순서는 첫 경로의 사전순이다."""
    groups: dict[str, list[str]] = collections.defaultdict(list)
    per_tree = {}
    for tree, pattern in ((MEETINGS, "TSGR_*/*/*"), (CR_TREE, "Rel-*/**/*")):
        files = [path for path in sorted((ROOT / tree).glob(pattern)) if path.is_file()]
        inodes = set()
        for path in files:
            stat = path.stat()
            key = f"{stat.st_dev}:{stat.st_ino}"
            inodes.add(key)
            groups[key].append(str(path.relative_to(ROOT)))
        folders = collections.Counter(Path(path).parent.name for path in files)
        per_tree[str(tree)] = {"files": len(files), "distinctInodes": len(inodes), "byParentFolder": dict(folders)}
    meeting_inodes = set()
    for key, paths in groups.items():
        if any(path.startswith(str(MEETINGS)) for path in paths):
            meeting_inodes.add(key)
    cr_only = [key for key in groups if key not in meeting_inodes]
    ordered = [{"inode": key, "paths": sorted(paths)} for key, paths in sorted(groups.items(), key=lambda kv: min(kv[1]))]
    summary = {"trees": per_tree, "distinctInodes": len(groups), "crTreeInodesNotInMeetings": len(cr_only),
               "crTreeOnlyExamples": [groups[key] for key in cr_only[:5]]}
    return ordered, summary


class _Alarm(Exception):
    pass


def _on_alarm(signum, frame):
    raise _Alarm()


def timed(function, *args):
    signal.signal(signal.SIGALRM, _on_alarm)
    signal.alarm(READ_SECONDS)
    try:
        return function(*args)
    finally:
        signal.alarm(0)


def sevenz(archive: Path, out: Path) -> tuple[bool, str]:
    out.mkdir(parents=True, exist_ok=True)
    try:
        done = subprocess.run(["7z", "x", "-y", "-bd", "-bso0", "-bsp0", f"-o{out}", str(archive)],
                              stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=SEVENZ_SECONDS, check=False)
        return done.returncode == 0, done.stderr.decode("utf-8", "replace").strip()[:300]
    except subprocess.TimeoutExpired:
        return False, "7z 시간 초과"


class Extractor:
    """inode 하나(파일 하나)를 풀어 항목마다 글 또는 못 읽은 까닭을 낸다."""

    def __init__(self, work: Path, profile: Path):
        self.work = work
        self.profile = profile
        self.counter = 0
        self.members: list[dict] = []
        self.pending: list[tuple[dict, Path]] = []

    def slot(self, ext: str) -> Path:
        self.counter += 1
        return self.work / f"m{self.counter:06d}{ext}"

    def add(self, chain: list[str], ext: str, size, outcome: str, reason: str = "", detail: str = "") -> dict:
        record = {"chain": chain, "ext": ext, "bytes": size, "outcome": outcome, "reason": reason, "detail": detail,
                  "chars": 0, "text": "", "convertSeconds": None, "readSeconds": None, "depth": len(chain) - 1,
                  "reader": None, "nativeFallback": "", "nativeDetail": "", "omissions": None}
        self.members.append(record)
        return record

    def visit_file(self, path: Path, chain: list[str]) -> None:
        name = chain[-1]
        ext = rst.suffix(name) or "(확장자 없음)"
        size = path.stat().st_size
        if macos_extra(name):
            self.add(chain, ext, size, "skipped", "macOS 부속 파일")
        elif ext in rst.NESTED:
            self.visit_archive(path, chain, size)
        else:
            self.pending.append((self.add(chain, ext, size, "pending"), path))

    def visit_archive(self, path: Path, chain: list[str], size) -> str:
        """zip 하나를 푼다. 쓴 방법(zipfile·7z)을 돌려준다. 둘 다 못 하면 항목 하나로 실패를 남긴다."""
        try:
            archive = zipfile.ZipFile(path)
        except (zipfile.BadZipFile, OSError, ValueError) as error:
            first = f"{type(error).__name__}: {error}"[:200]
            out = self.slot("")
            ok, message = sevenz(path, out)
            found = sorted(p for p in out.rglob("*") if p.is_file())
            if not found:
                self.add(chain, ".zip", size, "failed", "압축 풀기 실패", f"zipfile {first}; 7z {message}")
                return "failed"
            for inner in found:
                self.visit_file(inner, chain + [str(inner.relative_to(out))])
            if not ok:
                self.add(chain, ".zip", size, "partial", "7z 일부 복구", message)
            return "7z"
        with archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                inner_chain = chain + [info.filename]
                ext = rst.suffix(info.filename) or "(확장자 없음)"
                if macos_extra(info.filename):
                    self.add(inner_chain, ext, info.file_size, "skipped", "macOS 부속 파일")
                    continue
                target = self.slot(ext if ext != "(확장자 없음)" else "")
                try:
                    with archive.open(info) as source, open(target, "wb") as sink:
                        shutil.copyfileobj(source, sink, 1 << 20)
                except RuntimeError as error:
                    reason = "암호 걸린 zip 항목" if "encrypt" in str(error).lower() else "zip 항목 풀기 실패"
                    self.add(inner_chain, ext, info.file_size, "failed", reason, str(error)[:200])
                    continue
                except (zipfile.BadZipFile, OSError, EOFError, NotImplementedError, ValueError) as error:
                    self.add(inner_chain, ext, info.file_size, "failed", "zip 항목 풀기 실패",
                             f"{type(error).__name__}: {error}"[:200])
                    continue
                self.visit_file(target, inner_chain)
        return "zipfile"

    def native(self) -> None:
        """.doc · .dot 를 `word97_text` 로 바로 읽는다. 읽지 못하면 까닭을 남기고 LibreOffice 차례로 둔다."""
        for record, path in self.pending:
            if record["outcome"] != "pending" or record["ext"] not in NATIVE_WORD:
                continue
            stats: dict = {}
            started = time.time()
            try:
                text = timed(word97_text.doc_text, path.read_bytes(), stats)
            except rst.ExtractError as error:
                record.update(nativeFallback=error.reason, nativeDetail=error.detail or "")
                continue
            except _Alarm:
                record.update(nativeFallback="읽기 시간 초과", nativeDetail=f"{READ_SECONDS}s")
                continue
            except Exception as error:  # noqa: BLE001 — 판독기의 모든 예외를 넘김 까닭으로 센다
                record.update(nativeFallback="읽기 예외", nativeDetail=f"{type(error).__name__}: {error}"[:200])
                continue
            finally:
                record["readSeconds"] = round(time.time() - started, 4)
            record.update(reader="word97_text", nativeText=text, omissions=stats)

    def convert(self) -> None:
        """옛 이진 형식을 한꺼번에 바꾸고, 바뀌지 않은 파일만 하나씩 다시 바꿔 까닭을 가른다."""
        legacy = []
        for record, path in self.pending:
            if record["ext"] in rst.LEGACY and "nativeText" not in record:
                if path.parent != self.work:
                    # 7z · derived 에서 온 파일은 줄기 이름이 겹칠 수 있어 변환 결과가 서로 덮지 않게 옮겨 둔다.
                    staged = self.slot(record["ext"])
                    shutil.copyfile(path, staged)
                    path = staged
                legacy.append((record, path))
        if not legacy:
            return
        profile = self.profile
        out = self.work / "converted"
        out.mkdir(exist_ok=True)
        started = time.time()
        done = rst.convert_legacy([path for _, path in legacy], out, profile, CONVERT_SECONDS)
        batch_seconds = time.time() - started
        if batch_seconds >= CONVERT_SECONDS:
            done = {}  # 끊긴 묶음: 끊긴 순간 쓰던 파일이 잘렸을 수 있어 모두 하나씩 다시 바꾼다
        for record, path in legacy:
            record["reader"] = "libreoffice"
            if path not in done:
                started = time.time()
                single = rst.convert_legacy([path], out, profile, CONVERT_SECONDS)
                seconds = time.time() - started
                if path in single and seconds < CONVERT_SECONDS:
                    done[path] = single[path]
                    record["convertSeconds"] = round(seconds, 2)
                else:
                    reason = "변환 시간 초과" if seconds >= CONVERT_SECONDS else "변환 실패"
                    record.update(outcome="failed", reason=reason, detail=f"LibreOffice {seconds:.0f}s")
                    continue
            else:
                record["convertSeconds"] = round(batch_seconds / len(legacy), 2)
            record["converted"] = done[path]

    def read(self) -> None:
        for record, path in self.pending:
            if record["outcome"] != "pending":
                continue
            if "nativeText" in record:
                text = self.settle(record, record.pop("nativeText").strip())
                if not text:
                    record.update(outcome="empty", reason="빈 글")
                else:
                    record.update(outcome="extracted", text=text, chars=len(text))
                continue
            source = record.pop("converted", path)
            if record["reader"] is None:
                record["reader"] = "file_text"
            started = time.time()
            try:
                text = timed(rst.file_text, source)
            except rst.ExtractError as error:
                record.update(outcome="failed", reason=error.reason, detail=error.detail or record["ext"])
                continue
            except _Alarm:
                record.update(outcome="failed", reason="읽기 시간 초과", detail=f"{READ_SECONDS}s")
                continue
            except Exception as error:  # noqa: BLE001 — 읽기 도구의 모든 예외를 까닭으로 센다
                record.update(outcome="failed", reason="읽기 예외", detail=f"{type(error).__name__}: {error}"[:200])
                continue
            finally:
                record["readSeconds"] = round(time.time() - started, 2)
            text = self.settle(record, text.strip())
            if not text:
                record.update(outcome="empty", reason="빈 글")
            else:
                record.update(outcome="extracted", text=text, chars=len(text))

    @staticmethod
    def settle(record: dict, text: str) -> str:
        text, lone = paired(text)
        if lone:
            record["omissions"] = {**(record["omissions"] or {}), "loneSurrogates": lone}
        return text


def extract(group: dict, run_dir: str) -> dict:
    """워커: inode 하나를 읽는다. LibreOffice 사용자 설정은 워커 프로세스마다 하나를 이어 쓴다."""
    started = time.time()
    first = ROOT / group["paths"][0]
    digest = hashlib.sha256()
    with open(first, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    work = Path(tempfile.mkdtemp(prefix="file-", dir=run_dir))
    extractor = Extractor(work, Path(run_dir) / f"lo-profile-{os.getpid()}")
    try:
        names = sorted({Path(path).name for path in group["paths"]})
        derived = [ROOT / DERIVED / Path(path).relative_to(MEETINGS).parent / Path(path).stem
                   for path in group["paths"] if path.startswith(str(MEETINGS))]
        derived = [folder for folder in derived if folder.is_dir()]
        if derived:
            opener = "derived"
            for inner in sorted(p for p in derived[0].rglob("*") if p.is_file()):
                extractor.visit_file(inner, [names[0], str(inner.relative_to(derived[0]))])
        else:
            opener = extractor.visit_archive(first, [names[0]], first.stat().st_size)
        extractor.native()
        extractor.convert()
        extractor.read()
    finally:
        shutil.rmtree(work, ignore_errors=True)
    for record in extractor.members:
        record["chain"] = record["chain"][1:]
    return {"inode": group["inode"], "paths": group["paths"], "names": names, "sha256": digest.hexdigest(),
            "bytes": first.stat().st_size, "opener": opener, "members": extractor.members,
            "seconds": round(time.time() - started, 2)}


def split_line(line: str) -> list[str]:
    parts = []
    while len(line) > CHUNK_CHARS:
        cut = line.rfind(" ", 0, CHUNK_CHARS + 1)
        cut = cut if cut > 0 else CHUNK_CHARS
        parts.append(line[:cut])
        line = line[cut:].lstrip(" ")
    parts.append(line)
    return parts


def chunk_text(text: str) -> list[str]:
    pieces, current, size = [], [], 0
    for line in text.split("\n"):
        for part in split_line(line):
            grow = len(part) + (1 if current else 0)
            if current and size + grow > CHUNK_CHARS:
                pieces.append("\n".join(current))
                current, size, grow = [], 0, len(part)
            current.append(part)
            size += grow
    if current:
        pieces.append("\n".join(current))
    return [piece.strip() for piece in pieces if piece.strip()]


def connect(path: Path) -> sqlite3.Connection:
    fresh = not path.exists()
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    if fresh:
        con.executescript(SCHEMA)
    return con


def store(con: sqlite3.Connection, result: dict, failures) -> None:
    existing = con.execute("SELECT id, paths, names FROM files WHERE sha256 = ?", (result["sha256"],)).fetchone()
    owns = sorted({own_number(name) for name in result["names"]})
    if existing:
        file_id = existing[0]
        paths = sorted(set(json.loads(existing[1])) | set(result["paths"]))
        names = sorted(set(json.loads(existing[2])) | set(result["names"]))
        con.execute("UPDATE files SET paths = ?, names = ? WHERE id = ?",
                    (json.dumps(paths, ensure_ascii=False), json.dumps(names, ensure_ascii=False), file_id))
    else:
        members = result["members"]
        outcome = "extracted" if any(m["outcome"] == "extracted" for m in members) else "nothing"
        cursor = con.execute(
            "INSERT INTO files(sha256, bytes, paths, names, opener, outcome, seconds) VALUES (?,?,?,?,?,?,?)",
            (result["sha256"], result["bytes"], json.dumps(result["paths"], ensure_ascii=False),
             json.dumps(result["names"], ensure_ascii=False), result["opener"], outcome, result["seconds"]))
        file_id = cursor.lastrowid
        for member in members:
            chain = " / ".join(member["chain"])
            cursor = con.execute(
                "INSERT INTO members(file_id, chain, ext, bytes, outcome, reason, detail, chars, convert_seconds, "
                "read_seconds, depth, reader, native_fallback, native_detail, omissions) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (file_id, chain, member["ext"], member["bytes"], member["outcome"], member["reason"], member["detail"],
                 member["chars"], member["convertSeconds"], member["readSeconds"], member["depth"], member["reader"],
                 member["nativeFallback"], member["nativeDetail"],
                 json.dumps(member["omissions"]) if member["omissions"] is not None else None))
            member_id = cursor.lastrowid
            for own in numbers_in(chain):
                con.execute("INSERT INTO member_owner VALUES (?, ?)", (own, member_id))
            if member["outcome"] == "extracted":
                con.executemany("INSERT INTO chunks(member_id, file_id, seq, text) VALUES (?,?,?,?)",
                                [(member_id, file_id, seq, piece) for seq, piece in enumerate(chunk_text(member["text"]))])
            if member["outcome"] in ("failed", "partial", "empty"):
                failures.write(json.dumps({"paths": result["paths"], "chain": chain, "ext": member["ext"],
                                           "outcome": member["outcome"], "reason": member["reason"],
                                           "detail": member["detail"], "reader": member["reader"],
                                           "nativeFallback": member["nativeFallback"]}, ensure_ascii=False) + "\n")
    for own in owns:
        con.execute("INSERT OR IGNORE INTO owners VALUES (?, ?)", (own, file_id))
    con.execute("INSERT INTO inodes VALUES (?, ?, ?)",
                (result["inode"], file_id, json.dumps(result["paths"], ensure_ascii=False)))


def failed_file(group: dict, reason: str, detail: str) -> dict:
    """항목을 알 수 없게 실패한 파일(워커가 죽음 · 예외)을 실패 항목 하나로 남긴다."""
    first = ROOT / group["paths"][0]
    digest = hashlib.sha256(first.read_bytes()).hexdigest()
    names = sorted({Path(path).name for path in group["paths"]})
    return {"inode": group["inode"], "paths": group["paths"], "names": names, "sha256": digest,
            "bytes": first.stat().st_size, "opener": "failed", "seconds": 0.0,
            "members": [{"chain": [], "ext": rst.suffix(names[0]), "bytes": first.stat().st_size, "outcome": "failed",
                         "reason": reason, "detail": detail, "chars": 0, "text": "", "convertSeconds": None,
                         "readSeconds": None, "depth": 0, "reader": None, "nativeFallback": "", "nativeDetail": "",
                         "omissions": None}]}


def run(groups: list[dict], workers: int, run_dir: str, con: sqlite3.Connection, failures) -> int:
    """창 크기(워커 수의 두 배)만큼만 넘겨 풀이 깨져도 의심 항목을 좁힌다. 의심 항목은 끝에서 하나씩 돈다."""
    queue = collections.deque(groups)
    suspects: list[dict] = []
    stored = 0
    started = time.time()
    try:
        while queue:
            stored += _window(queue, suspects, workers, run_dir, con, failures, stored, started)
        for group in suspects:
            with ProcessPoolExecutor(max_workers=1) as single:
                try:
                    result = single.submit(extract, group, run_dir).result()
                except BrokenProcessPool:
                    result = failed_file(group, "워커 비정상 종료", "워커 하나로 돌려도 프로세스가 죽음")
                except Exception as error:  # noqa: BLE001
                    result = failed_file(group, "추출 예외", f"{type(error).__name__}: {error}"[:200])
            store(con, result, failures)
            stored += 1
    except BaseException:
        # 파일 하나를 저장하다 멈췄으면 그 파일의 줄이 반쯤 들어가 있다. 마지막 확정 뒤의 것을 모두 되돌리고
        # 다시 실행할 때 그 파일들부터 읽게 한다.
        con.rollback()
        failures.discard()
        raise
    con.commit()
    failures.flush()
    return stored


class FailureLog:
    """못 읽은 항목의 줄을 색인 확정과 함께 쓴다. 되돌린 파일의 줄이 남아 다시 읽을 때 두 번 적히지 않게 한다."""

    def __init__(self, handle):
        self.handle = handle
        self.lines: list[str] = []

    def write(self, line: str) -> None:
        self.lines.append(line)

    def flush(self) -> None:
        """색인을 확정한 뒤에만 부른다."""
        self.handle.writelines(self.lines)
        self.lines.clear()
        self.handle.flush()

    def discard(self) -> None:
        self.lines.clear()


def _window(queue, suspects, workers, run_dir, con, failures, stored_before, started) -> int:
    """풀 하나로 대기열을 돈다. 풀이 깨지면 떠 있던 항목을 의심 목록에 넣고 돌아간다."""
    stored = 0
    executor = ProcessPoolExecutor(max_workers=workers, max_tasks_per_child=200)
    inflight = {}
    try:
        while queue or inflight:
            while queue and len(inflight) < 2 * workers:
                if available_gib() < MIN_AVAILABLE_GIB:
                    raise SystemExit(f"사용 가능한 메모리 {available_gib():.1f} GiB — 멈춘다(다시 실행하면 이어 간다)")
                future = executor.submit(extract, queue[0], run_dir)
                inflight[future] = queue.popleft()
            done, _ = wait(inflight, return_when=FIRST_COMPLETED)
            for future in done:
                group = inflight.pop(future)
                try:
                    result = future.result()
                except BrokenProcessPool:
                    suspects.append(group)
                    continue
                except Exception as error:  # noqa: BLE001 — 파일 하나의 예외는 그 파일의 실패로 센다
                    result = failed_file(group, "추출 예외", f"{type(error).__name__}: {error}"[:200])
                store(con, result, failures)
                stored += 1
                total = stored_before + stored
                if total % 200 == 0:
                    con.commit()
                    failures.flush()
                    rate = total / (time.time() - started)
                    print(json.dumps({"stored": total, "queued": len(queue), "suspects": len(suspects),
                                      "perSecond": round(rate, 2), "availableGiB": round(available_gib(), 1),
                                      "etaMinutes": round(len(queue) / rate / 60, 1) if rate else None}), flush=True)
    except BrokenProcessPool:
        suspects.extend(inflight.values())
    finally:
        executor.shutdown(wait=True, cancel_futures=True)
    return stored


def census(con: sqlite3.Connection, path_summary: dict) -> dict:
    def rows(sql):
        return con.execute(sql).fetchall()

    # 'partial' 줄은 7z 가 일부만 푼 zip 의 표지다(그 zip 에서 나온 항목은 따로 센다). 항목 수에서 뺀다.
    documents = rows("SELECT outcome, COUNT(*) FROM members WHERE outcome != 'partial' GROUP BY outcome")
    by_reason = rows("SELECT outcome, reason, ext, COUNT(*) FROM members WHERE outcome NOT IN ('extracted', 'partial') "
                     "GROUP BY outcome, reason, ext ORDER BY outcome, COUNT(*) DESC")
    by_ext = rows("SELECT ext, outcome, COUNT(*) FROM members WHERE outcome != 'partial' "
                  "GROUP BY ext, outcome ORDER BY ext")
    readers = rows("SELECT ext, reader, outcome, COUNT(*) FROM members WHERE reader IS NOT NULL "
                   "GROUP BY ext, reader, outcome ORDER BY ext, reader, outcome")
    fallback = rows("SELECT native_fallback, outcome, COUNT(*) FROM members WHERE native_fallback != '' "
                    "GROUP BY native_fallback, outcome ORDER BY COUNT(*) DESC")
    omitted: dict[str, int] = collections.Counter()
    omitted_members: dict[str, int] = collections.Counter()
    for (value,) in rows("SELECT omissions FROM members WHERE omissions IS NOT NULL AND outcome = 'extracted'"):
        for key, count in json.loads(value).items():
            omitted[key] += count
            omitted_members[key] += count > 0
    formats: dict[str, dict] = collections.defaultdict(dict)
    for ext, outcome, count in by_ext:
        formats[ext][outcome] = count
    convert = [row[0] for row in rows("SELECT convert_seconds FROM members WHERE outcome = 'extracted' "
                                      "AND convert_seconds IS NOT NULL")]
    read = [row[0] for row in rows("SELECT read_seconds FROM members WHERE outcome = 'extracted'")]
    stems = [row[0] for row in rows("SELECT DISTINCT own FROM owners")]
    unpatterned = [stem for stem in stems if not PACK_RE.fullmatch(stem)]
    return {
        "rule": "inode 하나를 한 번 읽고, 바이트가 같은 파일은 글을 한 번만 남긴다. 항목은 zip 안의 파일 하나다"
                "(안의 zip 은 담는 그릇이라 항목으로 세지 않고 그 안을 센다). 'partial' 은 7z 가 일부만 풀어 낸 zip,"
                " 'nothing' 파일은 글이 나온 항목이 하나도 없는 파일이다.",
        "paths": path_summary,
        "inodesStored": rows("SELECT COUNT(*) FROM inodes")[0][0],
        "distinctContents": rows("SELECT COUNT(*) FROM files")[0][0],
        "filesByOpener": dict(rows("SELECT opener, COUNT(*) FROM files GROUP BY opener")),
        "filesByOutcome": dict(rows("SELECT outcome, COUNT(*) FROM files GROUP BY outcome")),
        "filesWithoutText": [{"names": json.loads(names), "opener": opener} for names, opener in
                             rows("SELECT names, opener FROM files WHERE outcome = 'nothing' ORDER BY id")],
        "members": {"found": sum(count for _, count in documents), "byOutcome": dict(documents),
                    "archiveNotesPartial": rows("SELECT COUNT(*) FROM members WHERE outcome = 'partial'")[0][0],
                    "byReader": [{"ext": e, "reader": r, "outcome": o, "count": c} for e, r, o, c in readers],
                    "nativeFallbackByReason": [{"reason": r, "finalOutcome": o, "count": c} for r, o, c in fallback],
                    "nativeOmissions": {"rule": "word97_text 로 읽은 .doc · .dot 항목에서 글로 싣지 않은 것의 합과 "
                                                "그것이 하나라도 있는 항목 수. loneSurrogates 는 판독기와 상관없이 "
                                                "짝 없는 UTF-16 반쪽을 U+FFFD 로 바꾼 수",
                                        "totals": dict(omitted), "membersWithAny": dict(omitted_members)},
                    "notExtractedByReason": [{"outcome": o, "reason": r, "ext": e, "count": c} for o, r, e, c in by_reason],
                    "formats": formats,
                    "maxDepth": rows("SELECT MAX(depth) FROM members")[0][0]},
        "seconds": {"convertMaxExtracted": max(convert) if convert else None,
                    "convertMedianExtracted": statistics.median(convert) if convert else None,
                    "readMaxExtracted": max(read) if read else None,
                    "convertLimit": CONVERT_SECONDS, "readLimit": READ_SECONDS, "sevenzLimit": SEVENZ_SECONDS},
        "chunks": {"count": rows("SELECT COUNT(*) FROM chunks")[0][0],
                   "chars": rows("SELECT SUM(LENGTH(text)) FROM chunks")[0][0], "maxChars": CHUNK_CHARS},
        "ownNumbers": {"distinct": len(stems), "notRpPattern": unpatterned},
        "memberOwnNumbers": rows("SELECT COUNT(DISTINCT own) FROM member_owner")[0][0],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--scratch", default=tempfile.gettempdir(), help="항목을 풀어 둘 임시 폴더의 부모")
    parser.add_argument("--limit", type=int, help="시험용: 앞에서부터 이 수의 inode 만 읽고 색인은 완성하지 않는다")
    args = parser.parse_args()
    os.chdir(ROOT)
    groups, path_summary = census_paths()
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    partial = INDEX.with_name(INDEX.name + ".partial")
    con = connect(partial)
    done = {row[0] for row in con.execute("SELECT inode FROM inodes")}
    todo = [group for group in groups if group["inode"] not in done]
    if args.limit is not None:
        todo = todo[:args.limit]
    print(json.dumps({"inodes": len(groups), "alreadyStored": len(done), "toRead": len(todo)}), flush=True)
    run_dir = tempfile.mkdtemp(prefix="plenary-run-", dir=args.scratch)
    try:
        with open(FAILURES, "a", encoding="utf-8") as handle:
            run(todo, args.workers, run_dir, con, FailureLog(handle))
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
    stored = con.execute("SELECT COUNT(*) FROM inodes").fetchone()[0]
    if args.limit is not None or stored != len(groups):
        print(json.dumps({"stored": stored, "inodes": len(groups), "complete": False}), flush=True)
        con.close()
        return
    started = time.time()
    for statement in POST:
        con.execute(statement)
    con.execute("INSERT OR REPLACE INTO build_info VALUES ('postSeconds', ?)", (str(round(time.time() - started, 1)),))
    con.commit()
    report = census(con, path_summary)
    con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    con.execute("PRAGMA journal_mode=DELETE")
    con.close()
    partial.rename(INDEX)
    report["index"] = str(INDEX.relative_to(ROOT))
    report["indexBytes"] = INDEX.stat().st_size
    report["failuresFile"] = str(FAILURES.relative_to(ROOT))
    CENSUS.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"census": str(CENSUS.relative_to(ROOT)), "chunks": report["chunks"]}, ensure_ascii=False),
          flush=True)


if __name__ == "__main__":
    main()
