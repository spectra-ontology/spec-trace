"""Portable CR lexical cache for a common search engine.

Spec: retain exact source metadata, whole compound identities and same-chunk
filter conjunctions. Cache construction is explicit and streaming; opening a
missing or stale cache never starts a build. This module has no model, vector
database, evaluation, relevance-label or CQ dependency. Ranking policy selection
belongs to the caller. A lexical score is never a dense cosine.

The index includes canonical title, header intent, body and metadata separately.
Body/metadata evidence therefore survives a zero title/header BM25F score.
Document-wide title/header context and filter-local body/metadata are explicitly
distinguished in the returned features. Cache generations are source-SHA bound.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import stat
import time
import unicodedata
import uuid
from typing import Iterator, Mapping

SCHEMA = "spectra.cr_search.lexical_cache.v1"
LEXICAL_POLICY = "nfc_casefold_exact_ascii_compounds_v1"
DEFAULT_CACHE_ROOT = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "spectra" / "cr_search"
SEPARATORS = frozenset("-_./")
CONSISTENT_FIELDS = ("specNumber", "crNumber", "category", "workItem", "meeting",
                     "strategy", "clausesAffected", "sectionIds")
FILTER_FIELDS = frozenset(("chunkId", "chunkType", "tdocNumber", *CONSISTENT_FIELDS,
                           "chunkSectionId", "chunkIndex", "totalChunks", "tokenCount"))
MAX_CHUNK_CHARACTERS = 8 << 20
MAX_WITNESS_CHUNKS = 3
LOCAL_SMALL_MAX_SOURCE_BYTES = 32 << 20
LOCAL_SMALL_MAX_CHUNKS = 10_000
_HEADER_END = re.compile(r"(?im)^(?:Consequences if not approved|Clauses affected|Change text)\s*:")


class CacheError(RuntimeError):
    """Missing, incomplete, incompatible or stale cache generation."""


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for part in iter(lambda: stream.read(1 << 20), b""):
            digest.update(part)
    return digest.hexdigest()


def _identity(path: Path) -> tuple[int, ...]:
    value = path.stat()
    if not stat.S_ISREG(value.st_mode):
        raise CacheError("A regular file is required: " + str(path))
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def _sha(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("An exact lowercase SHA256 is required")
    return value


@dataclass(frozen=True)
class CacheSpec:
    collection_name: str
    source_path: Path
    source_sha256: str
    cache_root: Path | None = None
    manifest_path: Path | None = None
    manifest_sha256: str | None = None

    def __post_init__(self):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", self.collection_name):
            raise ValueError("A plain collection name is required")
        _sha(self.source_sha256)
        object.__setattr__(self, "source_path", Path(self.source_path).expanduser().absolute())
        root = self.cache_root if self.cache_root is not None else os.environ.get("SPECTRA_CR_SEARCH_CACHE", DEFAULT_CACHE_ROOT)
        object.__setattr__(self, "cache_root", Path(root).expanduser().absolute())
        if self.manifest_path is not None:
            object.__setattr__(self, "manifest_path", Path(self.manifest_path).expanduser().absolute())
            _sha(self.manifest_sha256)
        elif self.manifest_sha256 is not None:
            raise ValueError("A manifest SHA requires its exact manifest path")

    @property
    def code_sha256(self) -> str:
        return sha256(Path(__file__))

    @property
    def path(self) -> Path:
        # A code change cannot reuse a cache produced by a different tokenizer,
        # metadata projection, streaming parser, filter contract or schema.
        token = hashlib.sha256(_json([SCHEMA, LEXICAL_POLICY, self.source_sha256,
                                      self.code_sha256]).encode()).hexdigest()
        return self.cache_root / self.collection_name / (token + ".sqlite")


def load_cache_spec(manifest_path: Path, manifest_sha256: str, *, collection_name: str,
                    source_path: Path, cache_root: Path | None = None) -> CacheSpec:
    """Load an explicitly pinned source registry; never infer a new source SHA.

    The manifest maps collection names to sourceSha256, without host paths.
    Source location comes from the same native loader configuration as before.
    Its schema is {schema: 'spectra.cr_search.source_manifest.v1',
    collections: {collection_name: {sourceSha256: '<64 lowercase hex>'}}}.
    """
    path = Path(manifest_path).expanduser().resolve(strict=True)
    before = _identity(path)
    if before[2] > 1 << 20 or sha256(path) != _sha(manifest_sha256):
        raise CacheError("Source registry is oversized or differs from its pinned SHA")
    manifest = json.loads(path.read_bytes())
    if _identity(path) != before or sha256(path) != manifest_sha256:
        raise CacheError("Source registry changed while being read")
    if manifest.get("schema") != "spectra.cr_search.source_manifest.v1":
        raise CacheError("Unsupported source registry schema")
    entry = manifest.get("collections", {}).get(collection_name)
    if not isinstance(entry, dict) or set(entry) != {"sourceSha256"}:
        raise CacheError("Collection requires one explicit source SHA in the source registry")
    return CacheSpec(collection_name, source_path, _sha(entry["sourceSha256"]), cache_root, path, manifest_sha256)


def resolve_cache_spec(*, collection_name: str, source_path: Path, cache_root: Path | None = None,
                       manifest_path: Path | None = None, manifest_sha256: str | None = None) -> CacheSpec:
    """Resolve the explicitly configured registry or cache-root source_manifest.json.

    The local registry is configuration supplied by the operator, never a SHA
    guessed from current corpus bytes. Its bytes are frozen before parsing.
    A separate deployment pin can optionally be supplied as manifest_sha256.
    """
    root = Path(cache_root if cache_root is not None else os.environ.get("SPECTRA_CR_SEARCH_CACHE", DEFAULT_CACHE_ROOT)).expanduser().absolute()
    path = Path(manifest_path).expanduser().absolute() if manifest_path is not None else root / "source_manifest.json"
    before = _identity(path)
    if before[2] > 1 << 20:
        raise CacheError("Source registry exceeds its size bound")
    pinned = manifest_sha256 if manifest_sha256 is not None else sha256(path)
    if _identity(path) != before:
        raise CacheError("Source registry changed during resolution")
    return load_cache_spec(path, pinned, collection_name=collection_name, source_path=source_path, cache_root=root)


def _atom(char: str) -> bool:
    return unicodedata.category(char)[0] in ("L", "N", "M")


def _start(char: str) -> bool:
    return unicodedata.category(char)[0] in ("L", "N")


def _key(value: str) -> str:
    return unicodedata.normalize("NFC", value).casefold()


def lexemes(text: str) -> Iterator[dict]:
    """Exact existing whole-lexeme grammar; separator identities never fold."""
    if not isinstance(text, str):
        raise ValueError("Lexical source must be a string")
    position = 0
    while position < len(text):
        if not (_atom(text[position]) or text[position] in SEPARATORS):
            position += 1
            continue
        left = position
        while position < len(text) and (_atom(text[position]) or text[position] in SEPARATORS):
            position += 1
        end = position
        while end > left and text[end - 1] == ".":
            end -= 1
        value = text[left:end]
        if not value or not _start(value[0]):
            continue
        atoms, offset, valid = [], 0, True
        while offset < len(value):
            begin = offset
            if not _start(value[offset]):
                valid = False
                break
            while offset < len(value) and _atom(value[offset]):
                offset += 1
            atoms.append(value[begin:offset])
            if offset < len(value):
                offset += 1
                if offset == len(value):
                    valid = False
                    break
        if valid:
            yield {"text": value, "key": _key(value), "start": left, "end": end,
                   "compound": len(atoms) > 1, "atoms": [_key(atom) for atom in atoms]}


def query_terms(query: str) -> dict:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("The complete original query is required")
    ordinary, compound = {}, {}
    for item in lexemes(query):
        target = compound if item["compound"] else ordinary
        target.setdefault(item["key"], item["text"])
    return {"compound": [{"key": key, "surface": value} for key, value in compound.items()],
            "ordinary": [{"key": key, "surface": value} for key, value in ordinary.items()]}


def _frequencies(text: str) -> tuple[Counter, int]:
    frequencies, length = Counter(), 0
    for item in lexemes(text):
        length += len(item["atoms"])
        if item["compound"]:
            frequencies[("compound", item["key"])] += 1
        frequencies.update(("ordinary", atom) for atom in item["atoms"])
    return frequencies, length


def _scalar(value) -> str:
    if type(value) not in (str, int, bool):
        raise ValueError("Filter values must be strings, integers or booleans")
    return _json(value)


def _validated_filters(filters: Mapping | None) -> dict:
    if filters is not None and not isinstance(filters, Mapping):
        raise ValueError("Filters must be a mapping")
    result = dict(filters or {})
    for field, wanted in result.items():
        if field not in FILTER_FIELDS:
            raise ValueError("Unsupported filter field: " + str(field))
        for value in (wanted if isinstance(wanted, (list, tuple)) else [wanted]):
            _scalar(value)
    return result


def _filter_sql(filters: Mapping | None, alias: str = "c") -> tuple[str, list]:
    filters = _validated_filters(filters)
    clauses, parameters = [], []
    for field, wanted in filters.items():
        values = list(wanted) if isinstance(wanted, (list, tuple)) else [wanted]
        if not values:
            clauses.append("0")
            continue
        encoded = list(dict.fromkeys(_scalar(value) for value in values))
        clauses.append("EXISTS(SELECT 1 FROM filter_values v WHERE v.chunk_id=" + alias +
                       ".id AND v.field=? AND v.value_json IN(" + ",".join("?" for _ in encoded) + "))")
        parameters.extend([field, *encoded])
    return " AND ".join(clauses) if clauses else "1", parameters


def satisfies_filters(payload: Mapping, filters: Mapping | None) -> bool:
    for field, wanted in _validated_filters(filters).items():
        values = list(wanted) if isinstance(wanted, (list, tuple)) else [wanted]
        actual = payload.get(field)
        actual = actual if isinstance(actual, list) else [actual]
        if not any(type(value) is type(target) and value == target for value in actual for target in values):
            return False
    return True


def iter_chunks(source: Path) -> Iterator[dict]:
    """Stream chunks from the native top-level JSON object with bounded items.

    Prefix fields are parsed as JSON values so a literal '"chunks":[' inside
    another string cannot be mistaken for the array. No whole-source loads.
    """
    decoder = json.JSONDecoder()
    with Path(source).open(encoding="utf-8") as stream:
        buffer, eof = "", False

        def fill():
            nonlocal buffer, eof
            part = stream.read(1 << 16)
            buffer += part
            eof = not part
            if len(buffer) > MAX_CHUNK_CHARACTERS:
                raise ValueError("A JSON item exceeds the bounded parser limit")

        def space():
            nonlocal buffer
            while True:
                buffer = buffer.lstrip()
                if buffer or eof:
                    return
                fill()

        def expect(char):
            nonlocal buffer
            space()
            if not buffer.startswith(char):
                raise ValueError("Malformed JSON object/array boundary")
            buffer = buffer[len(char):]

        def decode():
            nonlocal buffer
            while True:
                space()
                try:
                    value, end = decoder.raw_decode(buffer)
                except json.JSONDecodeError:
                    if eof:
                        raise ValueError("Incomplete JSON value")
                    fill()
                    continue
                # A number may otherwise be accepted at a read-block boundary
                # before its remaining digits arrive.
                if end == len(buffer) and not eof:
                    fill()
                    continue
                buffer = buffer[end:]
                return value

        expect("{")
        seen_chunks, first = False, True
        while True:
            space()
            if buffer.startswith("}"):
                buffer = buffer[1:]
                break
            if not first:
                expect(",")
            key = decode()
            if not isinstance(key, str):
                raise ValueError("JSON object field must be a string")
            expect(":")
            if key != "chunks":
                decode()
            else:
                if seen_chunks:
                    raise ValueError("Duplicate top-level chunks field")
                seen_chunks = True
                expect("[")
                space()
                if buffer.startswith("]"):
                    buffer = buffer[1:]
                else:
                    while True:
                        chunk = decode()
                        if not isinstance(chunk, dict):
                            raise ValueError("Chunk must be a JSON object")
                        yield chunk
                        space()
                        if buffer.startswith("]"):
                            buffer = buffer[1:]
                            break
                        expect(",")
            first = False
        space()
        if buffer or not seen_chunks:
            raise ValueError("Trailing source bytes or missing chunks array")


def _effective_text(chunk: Mapping) -> str:
    text = chunk.get("text") or chunk.get("content") or ""
    if not isinstance(text, str):
        raise ValueError("Chunk text/content must be a string")
    return text


def _metadata_text(payload: Mapping) -> str:
    values = []
    def visit(value, depth=0):
        if depth > 64:
            raise ValueError("Metadata nesting exceeds its bounded depth")
        if value is None:
            return
        if isinstance(value, dict):
            for key in sorted(value):
                visit(value[key], depth + 1)
        elif isinstance(value, list):
            for item in value:
                visit(item, depth + 1)
        elif type(value) in (str, int, bool):
            values.append(str(value))
        elif isinstance(value, float) and math.isfinite(value):
            values.append(str(value))
        else:
            raise ValueError("Unsupported source metadata value")
    visit(payload)
    return "\n".join(values)


def _build_guard():
    """Explicit builds require the authorized bounded systemd execution plan."""
    import subprocess
    unit = os.environ.get("SPECTRA_CR_SEARCH_BUILD_UNIT", "")
    if not re.fullmatch(r"[A-Za-z0-9_.@:-]+\.service", unit):
        raise CacheError("Set the exact owning systemd build unit")
    result = subprocess.run(["systemctl", "--user", "show", unit,
                             "-p", "MemoryMax", "-p", "Nice", "-p", "ControlGroup"],
                            capture_output=True, text=True, check=True, timeout=10)
    properties = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    if not properties.get("MemoryMax", "").isdigit() or not 0 < int(properties["MemoryMax"]) <= 12 << 30:
        raise CacheError("Build MemoryMax must be positive and at most 12 GiB")
    if int(properties.get("Nice", "-1")) != 19 or os.getpriority(os.PRIO_PROCESS, 0) != 19:
        raise CacheError("Build nice must be 19")
    cgroup = properties.get("ControlGroup")
    lines = Path("/proc/self/cgroup").read_text().splitlines()
    if not cgroup or not any(line.split(":", 2)[-1] == cgroup for line in lines):
        raise CacheError("Build process is not in its declared owning unit")
    available = next(int(line.split()[1]) * 1024 for line in Path("/proc/meminfo").read_text().splitlines()
                     if line.startswith("MemAvailable:"))
    if available < 20 << 30:
        raise CacheError("Build requires at least 20 GiB available RAM")


_DDL = """
CREATE TABLE generation(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE docs(tdoc TEXT PRIMARY KEY,common_json TEXT NOT NULL,title TEXT NOT NULL DEFAULT '',
 header_text TEXT NOT NULL DEFAULT '',title_length INTEGER NOT NULL DEFAULT 0,header_length INTEGER NOT NULL DEFAULT 0);
CREATE TABLE chunks(id INTEGER PRIMARY KEY,chunk_id TEXT UNIQUE NOT NULL,tdoc TEXT NOT NULL,
 chunk_type TEXT,payload_json TEXT NOT NULL,text_value TEXT NOT NULL,text_sha256 TEXT NOT NULL,
 source_text_length INTEGER NOT NULL,metadata_length INTEGER NOT NULL);
CREATE INDEX chunks_tdoc ON chunks(tdoc);
CREATE TABLE filter_values(chunk_id INTEGER NOT NULL,field TEXT NOT NULL,value_json TEXT NOT NULL,
 PRIMARY KEY(chunk_id,field,value_json));
CREATE TABLE document_terms(tdoc TEXT NOT NULL,field TEXT NOT NULL,kind TEXT NOT NULL,term TEXT NOT NULL,
 tf INTEGER NOT NULL,PRIMARY KEY(tdoc,field,kind,term));
CREATE TABLE chunk_terms(chunk_id INTEGER NOT NULL,field TEXT NOT NULL,kind TEXT NOT NULL,term TEXT NOT NULL,
 tf INTEGER NOT NULL,PRIMARY KEY(chunk_id,field,kind,term));
"""
_SECONDARY_INDEXES = (
    "CREATE INDEX filter_lookup ON filter_values(field,value_json,chunk_id)",
    "CREATE INDEX document_term_lookup ON document_terms(kind,term,tdoc,field)",
    "CREATE INDEX chunk_term_lookup ON chunk_terms(kind,term,chunk_id,field)",
)


def _emit_new(path: Path, value):
    with path.open("x", encoding="utf-8") as stream:
        stream.write(_json(value) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _fsync_directory(path: Path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def build_cache(spec: CacheSpec, *, build_mode: str = "bounded-unit") -> dict:
    """Build explicitly in an owning unit or a size-limited local-small mode.

    Per-generation flock serializes builders. A ready file is published only
    after commit, integrity check, close, fsync and a second complete source SHA.
    Existing ready caches are validated and reused; they are never overwritten.
    No implicit retry, stale-file deletion, seed import or old-generation cleanup.
    """
    if build_mode not in {"bounded-unit", "local-small"}:
        raise ValueError("Unknown cache build mode")

    def guard():
        if build_mode == "bounded-unit":
            _build_guard()
        elif _identity(spec.source_path)[2] > LOCAL_SMALL_MAX_SOURCE_BYTES:
            raise CacheError("local-small source exceeds 32 MiB; use a smaller source or bounded-unit")

    guard()
    code_before = spec.code_sha256
    source = spec.source_path.resolve(strict=True)
    source_before = _identity(source)
    if sha256(source) != spec.source_sha256 or _identity(source) != source_before:
        raise CacheError("Source generation differs from the supplied SHA")
    target = spec.path
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if target.parent.resolve() != target.parent:
        raise CacheError("Cache directories must not be symlinks")
    lock = os.open(target.with_suffix(".lock"), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if target.exists() or target.is_symlink():
            with SearchCache(spec) as reader:
                if build_mode == "local-small" and reader.generation["chunks"] > LOCAL_SMALL_MAX_CHUNKS:
                    raise CacheError("local-small source exceeds 10000 chunks; ready generation requires bounded-unit")
                return dict(reader.generation, reused=True)
        attempt = target.with_name(target.stem + ".attempt_" + uuid.uuid4().hex + ".sqlite")
        reserved = os.open(attempt, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        os.close(reserved)
        connection = None
        count, started = 0, time.monotonic()
        try:
            connection = sqlite3.connect(attempt)
            connection.execute("PRAGMA journal_mode=DELETE")
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute("PRAGMA temp_store=FILE")
            connection.execute("PRAGMA cache_size=" + ("-16384" if build_mode == "local-small" else "-262144"))
            connection.executescript(_DDL)
            connection.execute("BEGIN")
            for chunk in iter_chunks(source):
                if build_mode == "local-small" and count >= LOCAL_SMALL_MAX_CHUNKS:
                    raise CacheError("local-small source exceeds 10000 chunks; no partial cache is published")
                cid, tdoc = chunk.get("chunkId"), chunk.get("tdocNumber")
                if not isinstance(cid, str) or not cid or not isinstance(tdoc, str) or not tdoc:
                    raise ValueError("Every chunk requires a nonempty chunkId and tdocNumber")
                text = _effective_text(chunk)
                common = _json({field: chunk.get(field) for field in CONSISTENT_FIELDS})
                prior = connection.execute("SELECT common_json,title FROM docs WHERE tdoc=?", (tdoc,)).fetchone()
                if prior is None:
                    connection.execute("INSERT INTO docs(tdoc,common_json) VALUES(?,?)", (tdoc, common))
                elif prior[0] != common:
                    raise ValueError("Conflicting TDoc metadata: " + tdoc)
                if chunk.get("chunkType") == "header":
                    title = chunk.get("title") or ""
                    if not isinstance(title, str) or (prior and prior[1] and title and prior[1] != title):
                        raise ValueError("Conflicting or non-string canonical title: " + tdoc)
                    connection.execute("UPDATE docs SET title=CASE WHEN title='' THEN ? ELSE title END,"
                                       "header_text=header_text || CASE WHEN header_text='' THEN '' ELSE char(10) END || ? WHERE tdoc=?",
                                       (title, text, tdoc))
                payload = {key: value for key, value in chunk.items() if key not in ("text", "content")}
                metadata = _metadata_text(payload)
                text_tf, text_length = _frequencies(text)
                source_field = "source_header" if chunk.get("chunkType") == "header" else "body"
                metadata_tf, metadata_length = _frequencies(metadata)
                rowid = connection.execute("INSERT INTO chunks(chunk_id,tdoc,chunk_type,payload_json,text_value,text_sha256,source_text_length,metadata_length) VALUES(?,?,?,?,?,?,?,?)",
                    (cid, tdoc, chunk.get("chunkType"), _json(payload), text,
                     hashlib.sha256(text.encode()).hexdigest(), text_length, metadata_length)).lastrowid
                filter_rows = []
                for field in FILTER_FIELDS:
                    value = payload.get(field)
                    values = value if isinstance(value, list) else [value]
                    # A source null represents absent MatchValue evidence; a
                    # query asking for null is rejected by _validated_filters.
                    for encoded in {_scalar(value) for value in values if value is not None}:
                        filter_rows.append((rowid, field, encoded))
                connection.executemany("INSERT INTO filter_values VALUES(?,?,?)", filter_rows)
                for field, frequencies in ((source_field, text_tf), ("metadata", metadata_tf)):
                    connection.executemany("INSERT INTO chunk_terms VALUES(?,?,?,?,?)",
                                           ((rowid, field, kind, term, tf) for (kind, term), tf in frequencies.items()))
                count += 1
                if count % 1000 == 0:
                    guard()
            for tdoc, title, header in connection.execute("SELECT tdoc,title,header_text FROM docs"):
                intent = _HEADER_END.split(header, maxsplit=1)[0]
                lengths = []
                for field, text in (("title", title), ("header", intent)):
                    frequencies, length = _frequencies(text)
                    lengths.append(length)
                    connection.executemany("INSERT INTO document_terms VALUES(?,?,?,?,?)",
                                           ((tdoc, field, kind, term, tf) for (kind, term), tf in frequencies.items()))
                connection.execute("UPDATE docs SET title_length=?,header_length=? WHERE tdoc=?", (*lengths, tdoc))
            for statement in _SECONDARY_INDEXES:
                connection.execute(statement)
            if source_before != _identity(source) or sha256(source) != spec.source_sha256 or source_before != _identity(source):
                raise CacheError("Source generation changed during construction")
            if spec.code_sha256 != code_before:
                raise CacheError("Cache implementation changed during construction")
            receipt = {"status": "ready", "schema": SCHEMA, "lexicalPolicy": LEXICAL_POLICY,
                       "collection": spec.collection_name, "source": str(source), "sourceSha256": spec.source_sha256,
                       "sourceIdentityAtBuild": list(source_before), "codeSha256": code_before,
                       "chunks": count, "tdocs": connection.execute("SELECT count(*) FROM docs").fetchone()[0],
                       "emptyTitleDocuments": connection.execute("SELECT count(*) FROM docs WHERE title='' ").fetchone()[0],
                       "emptyHeaderDocuments": connection.execute("SELECT count(*) FROM docs WHERE header_text='' ").fetchone()[0],
                       "completeCorpus": True, "includesBody": True, "includesMetadata": True,
                       "includesGold": False, "seconds": time.monotonic() - started,
                       "sqliteVersion": sqlite3.sqlite_version, "buildMode": build_mode}
            connection.executemany("INSERT INTO generation VALUES(?,?)", ((key, _json(value)) for key, value in receipt.items()))
            connection.commit()
            if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise CacheError("Cache SQLite integrity check failed")
            connection.close()
            connection = None
            descriptor = os.open(attempt, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            guard()
            if source_before != _identity(source) or spec.code_sha256 != code_before:
                raise CacheError("Source or implementation changed before cache publication")
            if target.exists() or target.is_symlink():
                raise CacheError("Ready target appeared despite the per-cache build lock")
            # Link publishes a completely written inode atomically and refuses
            # any existing target, unlike replace(); unlink removes only our
            # private attempt name after successful publication.
            os.link(attempt, target, follow_symlinks=False)
            attempt.unlink()
            _fsync_directory(target.parent)
            return receipt
        except BaseException as error:
            if connection is not None:
                connection.rollback()
                connection.close()
            _emit_new(attempt.with_suffix(".failed.json"), {"status": "failed_preserved", "attempt": str(attempt),
                      "chunksProcessed": count, "errorType": type(error).__name__, "error": str(error),
                      "sourceSha256": spec.source_sha256, "codeSha256": code_before})
            raise
    finally:
        os.close(lock)


class SearchCache:
    """Readonly completed generation. No query can initiate source rebuilding."""
    def __init__(self, spec: CacheSpec):
        self.spec, self.path = spec, spec.path
        self._source = spec.source_path.resolve(strict=True)
        self._source_identity = _identity(self._source)
        if sha256(self._source) != spec.source_sha256 or _identity(self._source) != self._source_identity:
            raise CacheError("Current source SHA differs from the requested generation")
        self._manifest_identity = None
        if spec.manifest_path is not None:
            self._manifest_identity = _identity(spec.manifest_path)
            if sha256(spec.manifest_path) != spec.manifest_sha256 or _identity(spec.manifest_path) != self._manifest_identity:
                raise CacheError("Source registry changed after CacheSpec resolution")
        if self.path.is_symlink():
            raise CacheError("Cache symlinks are not accepted")
        self._index_identity = _identity(self.path)
        self.connection = sqlite3.connect(self.path.as_uri() + "?mode=ro&immutable=1", uri=True)
        self.connection.execute("PRAGMA query_only=ON")
        self.connection.execute("PRAGMA temp_store=FILE")
        self.connection.execute("PRAGMA cache_size=-8192")
        try:
            self.generation = {key: json.loads(value) for key, value in self.connection.execute("SELECT key,value FROM generation")}
            required = {"status": "ready", "schema": SCHEMA, "lexicalPolicy": LEXICAL_POLICY,
                        "sourceSha256": spec.source_sha256, "codeSha256": spec.code_sha256,
                        "collection": spec.collection_name, "completeCorpus": True,
                        "includesBody": True, "includesMetadata": True, "includesGold": False}
            if any(self.generation.get(key) != value for key, value in required.items()):
                raise CacheError("Cache generation is incomplete or incompatible")
            self.check_current()
        except BaseException:
            self.connection.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def check_current(self):
        if _identity(self.path) != self._index_identity or _identity(self._source) != self._source_identity:
            raise CacheError("Cache/source identity changed after activation")
        if self.spec.source_path.resolve(strict=True) != self._source:
            raise CacheError("Source path now resolves to a different file")
        if self.spec.manifest_path is not None and _identity(self.spec.manifest_path) != self._manifest_identity:
            raise CacheError("Source registry changed after cache activation")

    def close(self):
        try:
            self.check_current()
        finally:
            self.connection.close()

    def eligible_documents(self, filters: Mapping | None = None) -> Iterator[dict]:
        """Eligibility requires ONE actual chunk satisfying ALL field filters."""
        self.check_current()
        where, parameters = _filter_sql(filters)
        for tdoc, title, header, common, title_length, header_length in self.connection.execute(
                "SELECT d.tdoc,d.title,d.header_text,d.common_json,d.title_length,d.header_length FROM docs d "
                "WHERE EXISTS(SELECT 1 FROM chunks c WHERE c.tdoc=d.tdoc AND " + where + ") ORDER BY d.tdoc", parameters):
            yield {"tdocNumber": tdoc, "title": title, "header_text": header, "common": json.loads(common),
                   "titleLength": title_length, "headerLength": header_length}
        self.check_current()

    def canonical_chunk(self, chunk_id: str) -> dict:
        self.check_current()
        row = self.connection.execute("SELECT payload_json,text_value FROM chunks WHERE chunk_id=?", (chunk_id,)).fetchone()
        if row is None:
            raise CacheError("Retrieved chunk is absent from the source generation")
        return dict(json.loads(row[0]), text=row[1])

    def check_dense_payload(self, payload: Mapping, filters: Mapping | None = None) -> dict:
        canonical = self.canonical_chunk(payload.get("chunkId"))
        expected = {key: value for key, value in canonical.items() if key not in ("text", "content")}
        actual = {key: value for key, value in payload.items() if key not in ("text", "content")}
        if _json(actual) != _json(expected) or _effective_text(payload) != canonical["text"]:
            raise CacheError("Vector hit payload differs from the canonical source generation")
        if not satisfies_filters(canonical, filters):
            raise CacheError("Vector hit violates the original same-chunk filters")
        return canonical

    def lexical_features(self, query: str, filters: Mapping | None = None, *, include_body: bool = True) -> dict:
        """Full eligible population statistics, not statistics of dense500.

        bm25fDocumentFrequency concerns title/header only. evidenceDocumentFrequency
        additionally covers actual filter-local metadata and, when requested,
        body. Query weights and ranking choices are not inferred from labels.
        """
        terms = query_terms(query)
        wanted = [(kind, term["key"]) for kind in ("ordinary", "compound") for term in terms[kind]]
        entries = {row["tdocNumber"]: {"tdocNumber": row["tdocNumber"], "titleTf": {}, "headerTf": {},
                   "titleLength": row["titleLength"], "headerLength": row["headerLength"],
                   "bodyTerms": [], "sourceHeaderTerms": [], "metadataTerms": [],
                   "matchedBodyChunkIds": [], "matchedSourceHeaderChunkIds": [], "matchedMetadataChunkIds": [],
                   "bodyTermChunkPairs": 0, "sourceHeaderTermChunkPairs": 0, "metadataTermChunkPairs": 0}
                   for row in self.eligible_documents(filters)}
        document_frequency, evidence_frequency = Counter(), Counter()
        where, parameters = _filter_sql(filters)
        for kind, key in wanted:
            for tdoc, field, frequency in self.connection.execute(
                    "SELECT tdoc,field,tf FROM document_terms WHERE kind=? AND term=? ORDER BY tdoc,field", (kind, key)):
                if tdoc in entries:
                    entries[tdoc]["titleTf" if field == "title" else "headerTf"][key] = frequency
            fields = ("body", "source_header", "metadata") if include_body else ("source_header", "metadata")
            placeholders = ",".join("?" for _ in fields)
            for tdoc, cid, field in self.connection.execute(
                    "SELECT c.tdoc,c.chunk_id,t.field FROM chunk_terms t JOIN chunks c ON c.id=t.chunk_id "
                    "WHERE t.kind=? AND t.term=? AND t.field IN(" + placeholders + ") AND " + where +
                    " ORDER BY c.tdoc,c.id,t.field", [kind, key, *fields, *parameters]):
                if tdoc not in entries:
                    raise CacheError("Same-chunk term query escaped its document population")
                entry = entries[tdoc]
                names = {"body": ("bodyTerms", "matchedBodyChunkIds", "bodyTermChunkPairs"),
                         "source_header": ("sourceHeaderTerms", "matchedSourceHeaderChunkIds", "sourceHeaderTermChunkPairs"),
                         "metadata": ("metadataTerms", "matchedMetadataChunkIds", "metadataTermChunkPairs")}
                term_field, witness_field, count_field = names[field]
                entry[count_field] += 1
                if key not in entry[term_field]:
                    entry[term_field].append(key)
                if cid not in entry[witness_field] and len(entry[witness_field]) < MAX_WITNESS_CHUNKS:
                    entry[witness_field].append(cid)
        total = len(entries)
        title_total = sum(row["titleLength"] for row in entries.values())
        header_total = sum(row["headerLength"] for row in entries.values())
        for entry in entries.values():
            matched = set(entry["titleTf"]) | set(entry["headerTf"])
            document_frequency.update(matched)
            evidence_frequency.update(matched | set(entry["bodyTerms"]) | set(entry["sourceHeaderTerms"]) | set(entry["metadataTerms"]))
            entry["lexicalEvidencePositive"] = bool(matched or entry["bodyTerms"] or entry["sourceHeaderTerms"] or entry["metadataTerms"])
            entry["headerLexicalPositive"] = bool(matched)
        keys = sorted(key for _, key in wanted)
        self.check_current()
        return {"query": query, "filters": dict(filters or {}), "queryTerms": terms,
                "eligibleDocuments": total, "entries": list(entries.values()),
                "fieldLengthTotals": [title_total, header_total],
                "averageFieldLengths": [title_total / total if total else 0.0, header_total / total if total else 0.0],
                "bm25fDocumentFrequency": {key: document_frequency[key] for key in keys},
                "evidenceDocumentFrequency": {key: evidence_frequency[key] for key in keys},
                "idf": {key: math.log1p((total - document_frequency[key] + .5) / (document_frequency[key] + .5)) for key in keys},
                "positiveEvidenceDocuments": sum(row["lexicalEvidencePositive"] for row in entries.values()),
                "headerPositiveDocuments": sum(row["headerLexicalPositive"] for row in entries.values()),
                "includesCompleteEligibleBody": include_body, "includesMetadata": True,
                "includesCompleteEligibleSourceHeader": True,
                "witnessChunksPerFieldMaximum": MAX_WITNESS_CHUNKS,
                "sourceSha256": self.spec.source_sha256, "collection": self.spec.collection_name,
                "scoreKind": "unranked_lexical_features", "includesGold": False,
                "titleHeaderContext": "whole_document", "bodyMetadataContext": "same_filtered_chunk"}


def rank_bm25f(features: Mapping, *, title_boost: float, header_boost: float = 1.0,
               k1: float = 1.2, b: float = .75, dense_scores: Mapping | None = None) -> list[dict]:
    """Explicit general policy; no automatic adoption or mode-specific selection.

    Empty fields contribute zero. Missing dense scores sort after finite cosine
    ties, using a sentinel solely as a deterministic tie key, never as output.
    Body-only evidence remains represented even though two-field BM25F is zero;
    callers must not equate that zero with absent whole-document evidence.
    """
    for name, value in (("title_boost", title_boost), ("header_boost", header_boost), ("k1", k1)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(name + " must be finite and positive")
    if isinstance(b, bool) or not isinstance(b, (int, float)) or not math.isfinite(b) or not 0 <= b <= 1:
        raise ValueError("b must be finite in [0,1]")
    dense_scores = dict(dense_scores or {})
    if set(dense_scores) - {entry["tdocNumber"] for entry in features["entries"]}:
        raise CacheError("Dense documents escaped the full eligible source population")
    for value in dense_scores.values():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not -1.00001 <= value <= 1.00001:
            raise ValueError("Dense tie scores must be original finite cosines")
    averages = features["averageFieldLengths"]
    ranked = []
    for entry in features["entries"]:
        contributions = {}
        for key, idf in features["idf"].items():
            weighted = 0.0
            for field, average, boost in (("title", averages[0], title_boost), ("header", averages[1], header_boost)):
                frequency = entry[field + "Tf"].get(key, 0)
                if frequency:
                    if average <= 0:
                        raise CacheError("Nonzero frequency in a zero-length corpus field")
                    weighted += boost * frequency / (1 - b + b * entry[field + "Length"] / average)
            contributions[key] = idf * (k1 + 1) * weighted / (k1 + weighted) if weighted else 0.0
        value = dict(entry, bm25f=math.fsum(contributions.values()), termScores=contributions,
                     raw_dense_cosine=dense_scores.get(entry["tdocNumber"]), rank_score_kind="bm25f")
        value["rank_score"] = value["bm25f"]
        ranked.append(value)
    ranked.sort(key=lambda row: (-row["rank_score"], -(row["raw_dense_cosine"] if row["raw_dense_cosine"] is not None else -2.0), row["tdocNumber"]))
    return ranked


def _publish_source_manifest(path: Path, spec: CacheSpec):
    """Publish a complete new registry without replacing an operator's file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(_json({"schema": "spectra.cr_search.source_manifest.v1",
                         "collections": {spec.collection_name: {"sourceSha256": spec.source_sha256}}}) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path, follow_symlinks=False)
        _fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    """Explicit one-collection build CLI; source registries remain operator-owned."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--expected-code-sha256", required=True)
    parser.add_argument("--cache-root", type=Path)
    parser.add_argument("--build-mode", choices=("bounded-unit", "local-small"), default="bounded-unit",
                        help="Default: existing bounded systemd unit; local-small: at most 32 MiB/10000 chunks")
    parser.add_argument("--unit", help="Exact owning user systemd service; required for bounded-unit")
    parser.add_argument("--write-source-manifest", type=Path, metavar="NEW_PATH",
                        help="Publish a new one-collection source registry after a successful build; never overwrite")
    parser.add_argument("--receipt", type=Path, required=True, help="New receipt path; never overwritten")
    arguments = parser.parse_args()
    if arguments.build_mode == "bounded-unit" and not arguments.unit:
        parser.error("--unit is required for --build-mode bounded-unit")
    if arguments.build_mode == "local-small" and arguments.unit:
        parser.error("--unit applies only to --build-mode bounded-unit")
    if sha256(Path(__file__)) != _sha(arguments.expected_code_sha256):
        raise CacheError("Builder code differs from its execution pin")
    if arguments.receipt.exists() or arguments.receipt.is_symlink():
        raise FileExistsError(arguments.receipt)
    if arguments.write_source_manifest is not None:
        manifest = arguments.write_source_manifest.expanduser().absolute()
        if manifest.exists() or manifest.is_symlink():
            raise FileExistsError(manifest)
        if manifest == arguments.receipt.expanduser().absolute():
            parser.error("Receipt and source manifest require distinct paths")
    if arguments.unit:
        os.environ["SPECTRA_CR_SEARCH_BUILD_UNIT"] = arguments.unit
    spec = CacheSpec(arguments.collection, arguments.source, arguments.source_sha256, arguments.cache_root)
    arguments.receipt.parent.mkdir(parents=True, exist_ok=True)
    try:
        receipt = build_cache(spec, build_mode=arguments.build_mode)
        if arguments.write_source_manifest is not None:
            _publish_source_manifest(manifest, spec)
            receipt = dict(receipt, sourceManifest=str(manifest), sourceManifestSha256=sha256(manifest))
    except BaseException as error:
        _emit_new(arguments.receipt, {"status": "build_failed", "errorType": type(error).__name__,
                  "error": str(error), "collection": spec.collection_name,
                  "sourceSha256": spec.source_sha256, "codeSha256": arguments.expected_code_sha256})
        raise
    _emit_new(arguments.receipt, dict(receipt, cachePath=str(spec.path), cacheSha256=sha256(spec.path)))
    print(_json({"status": receipt["status"], "collection": spec.collection_name,
                 "chunks": receipt["chunks"], "tdocs": receipt["tdocs"], "cachePath": str(spec.path)}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
