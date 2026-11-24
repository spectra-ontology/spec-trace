"""글 검색 경로마다 독해 모델이 받는 문맥에 정답이 얼마나 들어오는지 센다 (모델 호출 없음).

왜 재는가
  텍스트 비교 방법은 밀집 검색 한 번으로 청크 8개를 골라 청크마다 앞 1500자만 준다(`run_chain_eval.py`의
  `retrieve`·`solve_text`). 점수가 낮은 이유가 "사실이 서로 다른 문서에 흩어져 있어서"인지,
  아니면 정답이 한 청크에 있는데 그 청크를 못 찾아서인지는 이 실행만으로 가를 수 없다.
  그래서 더 강한 글 경로들이 문맥에 정답을 얼마나 넣을 수 있는지를 같은 기준으로 잰다.

무엇을 세는가
  `measure_dense_context_ceiling.py` 와 같은 상한이다. 문맥은 청크마다 `retrieve` 가 붙이는 메타데이터 JSON 과
  본문(경로마다 정한 길이로 자름)을 이어 붙인 글이다. 정답 행의 모든 칸이 그 글에 문자열로 들어 있으면 그 행을
  "담김"으로 센다. 견주기 전에 채점(`score_chain_eval.cell_key`)과 같이 대소문자를 무시하고 bis 회의 표기를
  한 가지 철자로 맞춘다. 칸이 서로 다른 청크에 흩어져 있어도 담긴 것으로 세므로 상한은 느슨한 쪽이다.
  - allRows: 정답 행이 모두 담긴 문항 수(어떤 독해 모델이든 이 문맥만으로 낼 수 있는 정확 일치의 상한).
  - anyRow: 정답 행이 하나라도 담긴 문항 수.
  - allRows 문항을 다시 셋으로 나눈다. 모든 행이 청크 하나 안에 담기면 singleChunk, 행마다 한 문서
    (CR·기고문은 `tdocNumber`, 결정 기록은 `resolutionId`)의 청크들 안에 담기면 singleDocument,
    어떤 행이든 두 문서 이상을 합쳐야 담기면 multiDocument 다. "사실이 서로 다른 문서에 있다"는 설명은
    multiDocument 의 크기로 확인한다.
  - 칸 이름(`fields`)마다 담긴 칸의 비율도 함께 남긴다.
  빈 정답 문항은 상한을 정의할 수 없으므로 emptyGold 로 문항 수만 센다.

경로
  dense_8x1500    `retrieve(item, 8)`, 본문 앞 1500자. 지금의 텍스트 비교 실행과 같은 문맥이다(RAN5 포함).
  dense_12x4000   `retrieve(item, 12)`, 본문 앞 4000자. KDD 리버털에서 쓴 예산이다.
  bm25_*          질문 단어(불용어 제외, 64개까지)를 OR 로 묶은 FTS5 BM25. 질의식은 KDD 리버털
                  `matched_retrieval.py` 의 `query_expression` 과 같다. 모델이 다음 질의를 쓰는 2회차는 모델 호출이라 뺀다.
  rrf_*           BM25 상위 100개와 `retrieve(item, 100)` 을 상수 60 의 역순위 합(RRF)으로 합친다.
  tdoc_*          질문에 적힌 문서·묶음 번호와 payload `tdocNumber` 가 같은 청크 전부. 식별자 찾기를 글자 그대로 옮긴 경로다.
  idkey_*         질문에 적힌 식별자를 payload 키로 찾은 청크 전부. 작업반 문서 번호는 `tdocNumber` 일치와
                  그 번호를 담은 결정 기록(`resolutionId` 가 `DOC-{회의}-{문서 번호}-…` 꼴; 결정 기록 컬렉션에는
                  `tdocNumber` 가 없다), CR 묶음 번호(RP-)는 `crPackId` 또는 `tdocNumber` 일치, 절 이력 문항은
                  질문의 (규격, 절)이 `specNumber` 와 `clausesAffected` 에 있는 CR 청크다(릴리스는 거르지 않아 상위 집합).
                  tdoc 경로를 payload 키 전체로 넓힌, 식별자를 키로 쓰는 검색기의 상한이다.
  idany_*         idkey 에 더해 메타데이터나 본문에 그 문서·묶음 번호가 적힌 청크 전부(FTS5 로 숫자 토큰을 찾은 뒤
                  원래 표기 `R1-2403693` 이 들어 있는지 다시 확인). 개정 관계("revised in R1-…")처럼 다른 문서의
                  기록 안에만 적힌 연결을 잡는다.
  hopkey_*·hopany_*  위 두 경로의 문맥에 보이는 문서·묶음 번호(`R[1-5]-` 다섯~일곱 자리, `RP-` 여섯 자리)를
                  하나도 빼지 않고 같은 찾기로 한 번 더 따라간다. 잘린 문맥에서는 잘린 글에 보이는 번호만,
                  자르지 않은 문맥에서는 본문 전체에 보이는 번호를 따른다. 경계는 "단계 하나"이고 개수는 자르지 않는다.
                  개수 상한(예: 앞의 N개)은 어느 번호를 버릴지를 근거 없이 정하게 되지만, 단계 하나는 "첫 문맥이
                  돌려준 식별자를 빠짐없이 따라간 검색기"라는 뜻이 분명하다. 단계를 더 늘리면 묶음 → 묶음의 모든 CR →
                  그 CR 들이 적은 모든 문서처럼 말뭉치 전체로 번져 상한이 뜻을 잃는다. 문항마다 따라간 번호 수와
                  더해진 청크 수, 문맥 글자 수를 남겨 이 경로가 실제로 얼마나 큰 문맥을 요구하는지 보인다.
  `*_1500` 은 청크마다 본문 앞 1500자, `*_full` 은 본문 전체다.

색인
  `build` 단계가 다섯 WG 의 `resolution_chunks`·`cr_chunks`·`tdoc_chunks` 를 Qdrant 에서 읽기만 해 WG 마다
  SQLite 파일 하나(`text_route_ceiling/index/{wg}.sqlite3`)를 만든다. 본문은 `retrieve` 와 같은 키 순서
  (`text`, `content`)로 고르고 메타데이터도 `retrieve` 와 같은 키만 담는다. 시작과 끝의 점 개수가 같고
  저장한 수와도 같을 때만 파일을 완성한다. `measure` 단계는 색인의 점 개수가 지금 컬렉션과 다르면 멈추고,
  밀집 검색이 돌려준 청크마다 색인의 같은 청크와 메타데이터·본문이 같은지 대조해 결과에 남긴다.
  색인은 이 스크립트가 다시 만들 수 있는 런타임 산출물이라 `logs/` 아래(Git 추적 밖)에 둔다.

자원
  사용 가능한 메모리가 8 GiB 아래로 내려가면 멈춘다. 임베딩은 로컬 bge-m3(`retrieve`)만 쓰고 한 번에 하나씩 한다.
  Qdrant 컬렉션과 Neo4j 는 바꾸지 않는다.

사용 (저장소 루트에서):
  PYTHONPATH=scripts/common python3 scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/measure_text_route_ceiling.py build --wg RAN1
  PYTHONPATH=scripts/common python3 scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/measure_text_route_ceiling.py measure \
    [--items <chain_items_admitted.jsonl> ...] [--out-dir <폴더>]
  `measure` 는 문항별 결과(`<폴더>/items.jsonl`)를 쌓으며, 질문 해시와 정답 해시가 모두 같은 문항은 다시 세지 않는다.
  끝나면 `<폴더>/ceiling.json` 을 쓴다.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import sqlite3
import statistics
import time
from pathlib import Path

from run_chain_eval import DENSE_COLLECTIONS, QDRANT, TEXT_KEYS, post, retrieve
from score_chain_eval import cell_key, meeting_spelling

ROOT = next(path for path in Path(__file__).resolve().parents if (path / ".git").exists())
TRACK = ROOT / "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
ITEM_FILES = (TRACK / "chain_items_rebuilt/chain_items_admitted.jsonl",
              TRACK / "chain_items_ran5/chain_items_admitted.jsonl")
OUT_DIR = TRACK / "text_route_ceiling"
INDEX_DIR = OUT_DIR / "index"
WGS = ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")
# `retrieve` 가 문맥에 붙이는 메타데이터 키와 같은 순서. `measure` 가 밀집 검색 결과와 대조해 같은지 확인한다.
META_KEYS = ("tdocNumber", "meeting", "meetingId", "crPackId", "tsgMeeting", "specNumber", "crNumber",
             "clausesAffected", "resolutionId")
MIN_AVAILABLE_GIB = 8.0
RRF_K = 60
# 두 목록 모두에서 100위 밖인 청크의 점수는 2/(60+101) 이하라, BM25 상위 12개가 이미 가진 1/(60+12) 를 넘지 못한다.
# 그래서 이 깊이로 자른 목록에 없는 청크는 합친 상위 12개에 들어올 수 없다(한쪽 목록에서만 100위 밖인 청크는
# 그 목록의 몫을 잃는다).
FUSION_DEPTH = 100
DOC_RE = re.compile(r"\bR[1-5]-\d{5,7}(?!\d)", re.I)
PACK_RE = re.compile(r"\bRP-\d{6}(?!\d)", re.I)
# 절 번호에는 RAN5 처럼 밑줄이 들어갈 수 있다(예: 7.3B.2.3_1.1).
CLAUSE_RE = re.compile(r"clause ([0-9A-Z][0-9A-Za-z._]*?) of TS ([0-9][0-9.]*(?:-\d+)?)\b")
CLAUSE_TOKEN = re.compile(r"[A-Z]?\d+(?:[._][0-9A-Za-z]+)*|[A-Z](?:[._]\d[0-9A-Za-z]*)+")
STOPWORDS = set("a an and are as at be by for from has have how in is it of on or that the their this to was "
                "were what when where which who with".split())
SCHEMA = """
CREATE TABLE docs(id INTEGER PRIMARY KEY, collection TEXT NOT NULL, point_id TEXT NOT NULL, chunk_id TEXT,
                  tdoc TEXT, pack TEXT, spec TEXT, meta TEXT NOT NULL, text TEXT NOT NULL);
CREATE VIRTUAL TABLE search USING fts5(meta, text, content='docs', content_rowid='id',
                                       tokenize='unicode61 remove_diacritics 2');
CREATE TABLE cr_clause(spec TEXT NOT NULL, clause TEXT NOT NULL, id INTEGER NOT NULL);
CREATE TABLE manifest(collection TEXT PRIMARY KEY, count_start INTEGER, count_end INTEGER, stored INTEGER,
                      non_string_text INTEGER, seconds REAL);
CREATE TABLE build_info(name TEXT PRIMARY KEY, value REAL);
"""
POST_INDEXES = ("CREATE INDEX docs_tdoc ON docs(tdoc)", "CREATE INDEX docs_pack ON docs(pack)",
                "CREATE INDEX docs_chunk ON docs(collection, chunk_id)",
                "CREATE INDEX cr_clause_key ON cr_clause(spec, clause)")
ROUTES = ("dense_8x1500", "dense_12x4000", "bm25_8x1500", "bm25_12x4000", "rrf_8x1500", "rrf_12x4000",
          "tdoc_1500", "tdoc_full", "idkey_1500", "idkey_full", "idany_1500", "idany_full",
          "hopkey_1500", "hopkey_full", "hopany_1500", "hopany_full")


def available_gib() -> float:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 1024 ** 2
    raise RuntimeError("MemAvailable 를 읽지 못했다")


def guard_memory() -> None:
    if available_gib() < MIN_AVAILABLE_GIB:
        raise SystemExit(f"사용 가능한 메모리가 {available_gib():.1f} GiB 로 {MIN_AVAILABLE_GIB} GiB 아래라 멈춘다")


def index_path(wg: str) -> Path:
    return INDEX_DIR / f"{wg.lower()}.sqlite3"


def connect_index(wg: str) -> sqlite3.Connection:
    path = index_path(wg)
    if not path.exists():
        raise SystemExit(f"색인이 없다: {path.relative_to(ROOT)} (먼저 build --wg {wg})")
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.execute("PRAGMA cache_size=-65536")
    return con


def point_count(collection: str) -> int:
    return post(f"{QDRANT}/collections/{collection}/points/count", {"exact": True}, timeout=300)["result"]["count"]


def clause_tokens(value) -> set[str]:
    parts = value if isinstance(value, list) else [value]
    return {token for part in parts if isinstance(part, str) for token in CLAUSE_TOKEN.findall(part)}


def query_expression(query: str) -> str:
    """KDD 리버털 `matched_retrieval.py` 의 질의식과 같다: 불용어를 뺀 낱말을 64개까지 OR 로 묶는다."""
    terms: list[str] = []
    for term in re.findall(r"[^\W_]+", query.casefold(), flags=re.UNICODE):
        if len(term) > 1 and term not in STOPWORDS and term not in terms:
            terms.append(term)
    return " OR ".join('"' + term.replace('"', '""') + '"' for term in terms[:64])


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def build(wg: str, page: int) -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    final = index_path(wg)
    if final.exists():
        raise SystemExit(f"이미 있다: {final.relative_to(ROOT)} (다시 만들려면 지우고 실행한다)")
    partial = final.with_suffix(".partial")
    partial.unlink(missing_ok=True)
    os.environ["SQLITE_TMPDIR"] = str(INDEX_DIR)
    con = sqlite3.connect(partial)
    con.execute("PRAGMA journal_mode=OFF")
    con.execute("PRAGMA synchronous=OFF")
    con.execute("PRAGMA cache_size=-131072")
    con.executescript(SCHEMA)
    include = list(TEXT_KEYS) + ["chunkId"] + list(META_KEYS)
    next_id = 1
    for suffix in DENSE_COLLECTIONS:
        collection = f"{wg.lower()}_{suffix}"
        started, count_start = time.time(), point_count(collection)
        stored = non_string = pages = 0
        offset = None
        while True:
            body = {"limit": page, "with_payload": {"include": include}, "with_vector": False}
            if offset is not None:
                body["offset"] = offset
            result = post(f"{QDRANT}/collections/{collection}/points/scroll", body, timeout=300)["result"]
            docs, fts, clauses = [], [], []
            for point in result["points"]:
                payload = point.get("payload") or {}
                text = next((payload[key] for key in TEXT_KEYS if payload.get(key)), "")
                if not isinstance(text, str):
                    non_string += 1
                    text = json.dumps(text, ensure_ascii=False)
                meta = json.dumps({key: payload[key] for key in META_KEYS if payload.get(key)}, ensure_ascii=False)
                tdoc, pack, spec = (payload.get(key) if isinstance(payload.get(key), str) and payload.get(key) else None
                                    for key in ("tdocNumber", "crPackId", "specNumber"))
                docs.append((next_id, collection, str(point["id"]), payload.get("chunkId"), tdoc, pack, spec,
                             meta, text))
                fts.append((next_id, meta, text))
                if suffix == "cr_chunks" and spec:
                    clauses += [(spec, clause, next_id) for clause in clause_tokens(payload.get("clausesAffected"))]
                next_id += 1
            con.executemany("INSERT INTO docs VALUES (?,?,?,?,?,?,?,?,?)", docs)
            con.executemany("INSERT INTO search(rowid, meta, text) VALUES (?,?,?)", fts)
            con.executemany("INSERT INTO cr_clause VALUES (?,?,?)", clauses)
            stored += len(docs)
            pages += 1
            if pages % 20 == 0:
                con.commit()
                guard_memory()
                print(json.dumps({"collection": collection, "stored": stored, "of": count_start,
                                  "seconds": round(time.time() - started), "availableGiB": round(available_gib(), 1)}),
                      flush=True)
            offset = result.get("next_page_offset")
            if offset is None:
                break
        con.commit()
        count_end = point_count(collection)
        if not count_start == stored == count_end:
            con.close()
            raise SystemExit(f"{collection}: 시작 {count_start} · 저장 {stored} · 끝 {count_end} 가 달라 멈춘다"
                             f" (미완성 파일 {partial.relative_to(ROOT)})")
        con.execute("INSERT INTO manifest VALUES (?,?,?,?,?,?)",
                    (collection, count_start, count_end, stored, non_string, round(time.time() - started, 1)))
        con.commit()
        print(json.dumps({"completed": collection, "stored": stored, "seconds": round(time.time() - started)}),
              flush=True)
    started = time.time()
    for statement in POST_INDEXES:
        con.execute(statement)
    con.execute("INSERT INTO search(search) VALUES ('optimize')")
    con.execute("INSERT INTO build_info VALUES ('finishSeconds', ?)", (round(time.time() - started, 1),))
    con.commit()
    con.close()
    partial.rename(final)
    print(json.dumps({"index": str(final.relative_to(ROOT)), "bytes": final.stat().st_size,
                      "finishSeconds": round(time.time() - started)}), flush=True)


# ---------------------------------------------------------------------------
# measure
# ---------------------------------------------------------------------------

def doc_key(collection: str, meta: dict, chunk_id) -> str:
    return meta.get("tdocNumber") or meta.get("resolutionId") or f"{collection}:{chunk_id}"


class Index:
    """WG 하나의 색인. 식별자 찾기 결과는 실행 동안 기억해 같은 번호를 다시 찾지 않는다."""

    def __init__(self, wg: str):
        self.con = connect_index(wg)
        self.key_cache: dict[str, set[int]] = {}
        self.mention_cache: dict[str, set[int]] = {}
        self.resolution_doc: dict[str, set[int]] | None = None

    def check_counts(self) -> list[dict]:
        rows = self.con.execute("SELECT collection, stored FROM manifest ORDER BY collection").fetchall()
        report = []
        for collection, stored in rows:
            live = point_count(collection)
            report.append({"collection": collection, "indexed": stored, "live": live})
            if live != stored:
                raise SystemExit(f"{collection}: 색인 {stored} 점, 지금 {live} 점 — 색인을 다시 만든다")
        return report

    def tdoc_ids(self, ident: str) -> set[int]:
        return {row[0] for row in self.con.execute("SELECT id FROM docs WHERE tdoc = ?", (ident,))}

    def resolution_documents(self) -> dict[str, set[int]]:
        """문서 하나에 대한 결정 기록은 `resolutionId` 에 그 문서 번호를 담는다(`DOC-{회의}-{문서 번호}-b…`).

        결정 기록 컬렉션에는 `tdocNumber` 가 없으므로, 이 키를 읽어야 식별자 찾기가 결정 기록에 닿는다.
        """
        if self.resolution_doc is None:
            self.resolution_doc = collections.defaultdict(set)
            for row_id, meta in self.con.execute(
                    "SELECT id, meta FROM docs WHERE collection LIKE '%\\_resolution\\_chunks' ESCAPE '\\'"):
                resolution = json.loads(meta).get("resolutionId", "")
                if resolution.startswith("DOC-"):
                    for ident in set(match.upper() for match in DOC_RE.findall(resolution)):
                        self.resolution_doc[ident].add(row_id)
        return self.resolution_doc

    def key_ids(self, ident: str) -> set[int]:
        if ident not in self.key_cache:
            if ident.startswith("RP-"):
                sql, args = "SELECT id FROM docs WHERE pack = ? UNION SELECT id FROM docs WHERE tdoc = ?", (ident, ident)
            else:
                sql, args = "SELECT id FROM docs WHERE tdoc = ?", (ident,)
            found = {row[0] for row in self.con.execute(sql, args)}
            self.key_cache[ident] = found | self.resolution_documents().get(ident, set())
        return self.key_cache[ident]

    def mention_ids(self, ident: str) -> set[int]:
        """메타데이터나 본문에 번호 표기가 그대로 들어 있는 청크. 숫자 토큰으로 후보를 찾고 원래 표기로 다시 거른다."""
        if ident not in self.mention_cache:
            number = ident.split("-", 1)[1]
            needle = ident.lower()
            found = set()
            for row_id, meta, text in self.con.execute(
                    "SELECT d.id, d.meta, d.text FROM search JOIN docs d ON d.id = search.rowid WHERE search MATCH ?",
                    (f'"{number}"',)):
                if needle in meta.lower() or needle in text.lower():
                    found.add(row_id)
            self.mention_cache[ident] = found
        return self.mention_cache[ident]

    def clause_ids(self, spec: str, clause: str) -> set[int]:
        return {row[0] for row in self.con.execute(
            "SELECT id FROM cr_clause WHERE spec = ? AND clause = ?", (spec, clause))}

    def fetch(self, ids) -> dict[int, dict]:
        ids = list(ids)
        found: dict[int, dict] = {}
        for start in range(0, len(ids), 900):
            part = ids[start:start + 900]
            for row_id, collection, chunk_id, meta, text in self.con.execute(
                    f"SELECT id, collection, chunk_id, meta, text FROM docs WHERE id IN ({','.join('?' * len(part))})",
                    part):
                found[row_id] = {"collection": collection, "chunkId": chunk_id, "metaJson": meta, "text": text,
                                 "doc": doc_key(collection, json.loads(meta), chunk_id)}
        return found

    def rows(self, ids) -> list[dict]:
        found = self.fetch(ids)
        return [found[row_id] for row_id in sorted(found)]

    def by_chunk(self, collection: str, chunk_id) -> dict | None:
        row = self.con.execute("SELECT meta, text FROM docs WHERE collection = ? AND chunk_id = ? LIMIT 2",
                               (collection, chunk_id)).fetchall()
        return None if len(row) != 1 else {"metaJson": row[0][0], "text": row[0][1]}

    def bm25(self, question: str, limit: int) -> list[dict]:
        expression = query_expression(question)
        if not expression:
            return []
        # 순위는 FTS5 표 안에서만 매기고 본문은 고른 줄만 읽는다(일치한 모든 줄의 본문을 읽지 않게).
        ranked = [row[0] for row in self.con.execute(
            "SELECT rowid FROM search WHERE search MATCH ? ORDER BY rank, rowid LIMIT ?", (expression, limit))]
        found = self.fetch(ranked)
        return [found[row_id] for row_id in ranked]

    def manifest(self) -> list[dict]:
        names = ("collection", "countStart", "countEnd", "stored", "nonStringText", "seconds")
        return [dict(zip(names, row)) for row in self.con.execute("SELECT * FROM manifest ORDER BY collection")]

    def chunk_id_checks(self) -> list[dict]:
        """`(collection, chunkId)` 가 청크 하나를 가리키는지 확인한다. RRF 와 대조가 이 키를 쓴다."""
        return [{"collection": collection, "rows": rows, "nullChunkId": nulls, "duplicateChunkId": rows - nulls - distinct}
                for collection, rows, nulls, distinct in self.con.execute(
                    "SELECT collection, COUNT(*), SUM(chunk_id IS NULL), COUNT(DISTINCT chunk_id) FROM docs "
                    "GROUP BY collection ORDER BY collection")]


def dense_chunks(item: dict, top: int) -> list[dict]:
    # 본문이 문자열이 아니면 색인과 같은 방식(JSON)으로 글로 바꾼다. `build` 가 그런 점의 수를 manifest 에 남긴다.
    return [{"collection": chunk["collection"], "chunkId": chunk["chunkId"],
             "metaJson": json.dumps(chunk["meta"], ensure_ascii=False),
             "text": chunk["text"] if isinstance(chunk["text"], str) else json.dumps(chunk["text"], ensure_ascii=False),
             "doc": doc_key(chunk["collection"], chunk["meta"], chunk["chunkId"])}
            for chunk in retrieve(item, top)]


def fuse(*rankings: list[dict]) -> list[dict]:
    scores: dict[tuple, float] = collections.defaultdict(float)
    best: dict[tuple, int] = {}
    chunk_of: dict[tuple, dict] = {}
    for ranking in rankings:
        for rank, chunk in enumerate(ranking, 1):
            key = (chunk["collection"], chunk["chunkId"])
            scores[key] += 1.0 / (RRF_K + rank)
            best[key] = min(best.get(key, rank), rank)
            chunk_of.setdefault(key, chunk)
    return [chunk_of[key] for key in sorted(scores, key=lambda key: (-scores[key], best[key], key))]


def named_identifiers(question: str) -> dict:
    docs = list(dict.fromkeys(match.upper() for match in DOC_RE.findall(question)))
    packs = list(dict.fromkeys(match.upper() for match in PACK_RE.findall(question)))
    clause = CLAUSE_RE.search(question)
    return {"docs": docs, "packs": packs, "clause": [clause.group(2), clause.group(1)] if clause else None}


def visible(chunk: dict, limit: int | None) -> str:
    return chunk["metaJson"] + "\n" + (chunk["text"] if limit is None else chunk["text"][:limit])


def seed_ids(index: Index, named: dict, mention: bool) -> set[int]:
    ids: set[int] = set()
    for ident in named["docs"] + named["packs"]:
        ids |= index.key_ids(ident)
        if mention:
            ids |= index.mention_ids(ident)
    if named["clause"]:
        ids |= index.clause_ids(*named["clause"])
    return ids


def hop_ids(index: Index, seeds: set[int], looked_up: set[str], limit: int | None, mention: bool) -> tuple[set[int], int]:
    """시작 문맥에 보이는 문서·묶음 번호를 모두 한 번 더 찾는다. 따라간 번호 수도 돌려준다."""
    found: set[str] = set()
    for chunk in index.rows(seeds):
        text = visible(chunk, limit)
        found.update(match.upper() for match in DOC_RE.findall(text))
        found.update(match.upper() for match in PACK_RE.findall(text))
    follow = sorted(found - looked_up)
    ids = set(seeds)
    for ident in follow:
        ids |= index.key_ids(ident)
        if mention:
            ids |= index.mention_ids(ident)
    return ids, len(follow)


def judge(chunks: list[dict], limit: int | None, item: dict) -> dict:
    """정답 행마다 담김 여부와 어디까지 합쳐야 담기는지(청크 하나·문서 하나·여러 문서)를 판정한다."""
    pieces = [meeting_spelling(visible(chunk, limit).lower()) for chunk in chunks]
    context = "\n".join(pieces)
    by_doc: dict[str, list[str]] = collections.defaultdict(list)
    for chunk, piece in zip(chunks, pieces):
        by_doc[chunk["doc"]].append(piece)
    documents = ["\n".join(parts) for parts in by_doc.values()]
    rows, fields_held = [], [0] * len(item["fields"])
    for row in item["gold"]:
        cells = [cell_key(cell) for cell in row]
        present = [cell in context for cell in cells]
        for position, held in enumerate(present):
            fields_held[position] += held
        if not all(present):
            rows.append("missing")
        elif any(all(cell in piece for cell in cells) for piece in pieces):
            rows.append("chunk")
        elif any(all(cell in document for cell in cells) for document in documents):
            rows.append("document")
        else:
            rows.append("documents")
    return {"chunks": len(chunks), "documents": len(by_doc), "chars": len(context), "rows": rows,
            "fieldsHeld": fields_held}


def measure_item(item: dict, index: Index) -> dict:
    named = named_identifiers(item["question"])
    looked_up = set(named["docs"] + named["packs"])
    dense8, dense12 = dense_chunks(item, 8), dense_chunks(item, 12)
    dense_deep = dense_chunks(item, FUSION_DEPTH)
    integrity = collections.Counter()
    for chunk in dense8 + dense12 + dense_deep:
        stored = index.by_chunk(chunk["collection"], chunk["chunkId"])
        if stored is None:
            integrity["missingOrAmbiguous"] += 1
        else:
            integrity["compared"] += 1
            integrity["metaMismatch"] += stored["metaJson"] != chunk["metaJson"]
            integrity["textMismatch"] += stored["text"] != chunk["text"]
    lexical = index.bm25(item["question"], FUSION_DEPTH)
    fused = fuse(lexical, dense_deep)
    contexts = {"dense_8x1500": (dense8, 1500), "dense_12x4000": (dense12, 4000),
                "bm25_8x1500": (lexical[:8], 1500), "bm25_12x4000": (lexical[:12], 4000),
                "rrf_8x1500": (fused[:8], 1500), "rrf_12x4000": (fused[:12], 4000)}
    literal = set().union(*(index.tdoc_ids(ident) for ident in looked_up))
    contexts["tdoc_1500"], contexts["tdoc_full"] = (index.rows(literal), 1500), (index.rows(literal), None)
    hops = {}
    for mention, name in ((False, "key"), (True, "any")):
        seeds = seed_ids(index, named, mention)
        for limit, suffix in ((1500, "1500"), (None, "full")):
            contexts[f"id{name}_{suffix}"] = (index.rows(seeds), limit)
            ids, followed = hop_ids(index, seeds, looked_up, limit, mention)
            contexts[f"hop{name}_{suffix}"] = (index.rows(ids), limit)
            hops[f"hop{name}_{suffix}"] = {"identifiersFollowed": followed, "chunksAdded": len(ids) - len(seeds)}
    return {"id": item["id"], "questionSha256": hashlib.sha256(item["question"].encode()).hexdigest(),
            "goldSha256": gold_sha(item), "wg": item["wg"], "family": item["family"], "fields": item["fields"], "goldRows": len(item["gold"]),
            "named": named, "anchor": item["anchor"],
            "routes": {route: judge(chunks, limit, item) for route, (chunks, limit) in contexts.items()},
            "hops": hops, "integrity": dict(integrity)}


def summarize(records: list[dict]) -> dict:
    def group(selected: list[dict]) -> dict:
        scored = [record for record in selected if record["goldRows"]]
        out = {"n": len(scored), "emptyGold": len(selected) - len(scored), "routes": {}}
        for route in ROUTES:
            stats = collections.Counter()
            chunks, chars = [], []
            for record in scored:
                result = record["routes"][route]
                rows = result["rows"]
                chunks.append(result["chunks"])
                chars.append(result["chars"])
                if "missing" not in rows:
                    stats["allRows"] += 1
                    worst = "documents" if "documents" in rows else "document" if "document" in rows else "chunk"
                    stats[{"chunk": "singleChunk", "document": "singleDocument", "documents": "multiDocument"}[worst]] += 1
                stats["anyRow"] += any(row != "missing" for row in rows)
            out["routes"][route] = {key: stats[key] for key in ("allRows", "anyRow", "singleChunk", "singleDocument",
                                                               "multiDocument")}
            if scored:
                out["routes"][route].update(chunksMedian=statistics.median(chunks), chunksMax=max(chunks),
                                            charsMedian=statistics.median(chars), charsMax=max(chars))
        return out

    groups = [{"by": "total", "value": "all", **group(records)}]
    for key in ("wg", "family"):
        for value in sorted({record[key] for record in records}):
            groups.append({"by": key, "value": value, **group([r for r in records if r[key] == value])})
    for wg, family in sorted({(record["wg"], record["family"]) for record in records}):
        groups.append({"by": "wg×family", "value": f"{wg}|{family}",
                       **group([r for r in records if r["wg"] == wg and r["family"] == family])})
    fields: dict = {}
    for family in sorted({record["family"] for record in records}):
        selected = [record for record in records if record["family"] == family and record["goldRows"]]
        if not selected:
            continue
        names = selected[0]["fields"]
        total = sum(record["goldRows"] for record in selected)
        fields[family] = {route: {name: round(sum(record["routes"][route]["fieldsHeld"][position]
                                                  for record in selected) / total, 4)
                                  for position, name in enumerate(names)} for route in ROUTES}
    hop_stats = {}
    for route in ("hopkey_1500", "hopkey_full", "hopany_1500", "hopany_full"):
        followed = [record["hops"][route]["identifiersFollowed"] for record in records]
        added = [record["hops"][route]["chunksAdded"] for record in records]
        hop_stats[route] = {"identifiersFollowedMedian": statistics.median(followed),
                            "identifiersFollowedMax": max(followed),
                            "chunksAddedMedian": statistics.median(added), "chunksAddedMax": max(added)}
    return {"groups": groups, "fieldHeldRate": fields, "hops": hop_stats}


def gold_sha(item: dict) -> str:
    """판정은 정답 행에 달려 있으므로, 질문이 같아도 정답이 바뀐 문항은 다시 센다."""
    rows = sorted(json.dumps(row, ensure_ascii=False) for row in item["gold"])
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


def shown(path: Path) -> str:
    path = path.resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def measure(fresh: bool, only: list[str] | None, limit: int | None, item_files: list[Path], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    per_item = out_dir / "items.jsonl"
    if fresh:
        per_item.unlink(missing_ok=True)
    items = [json.loads(line) for path in item_files for line in path.read_text().splitlines() if line.strip()]
    current = {item["id"]: (hashlib.sha256(item["question"].encode()).hexdigest(), gold_sha(item)) for item in items}
    stored = [json.loads(line) for line in per_item.read_text().splitlines()] if per_item.exists() else []
    kept = [record for record in stored
            if current.get(record["id"]) == (record["questionSha256"], record.get("goldSha256"))]
    if len(kept) != len(stored):
        per_item.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in kept))
    done = {record["id"] for record in kept}
    taken: collections.Counter = collections.Counter()
    with per_item.open("a") as out:
        for wg in WGS:
            if only and wg not in only:
                continue
            todo = [item for item in items if item["wg"] == wg and item["id"] not in done]
            if limit:
                kept_todo = []
                for item in todo:
                    taken[item["family"], wg] += 1
                    if taken[item["family"], wg] <= limit:
                        kept_todo.append(item)
                todo = kept_todo
            if not todo:
                continue
            index = Index(wg)
            index.check_counts()
            for position, item in enumerate(todo, 1):
                guard_memory()
                started = time.time()
                record = measure_item(item, index)
                record["seconds"] = round(time.time() - started, 2)
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                out.flush()
                if position % 10 == 0 or position == len(todo):
                    print(json.dumps({"wg": wg, "done": position, "of": len(todo), "lastSeconds": record["seconds"],
                                      "availableGiB": round(available_gib(), 1)}), flush=True)
    records = [json.loads(line) for line in per_item.read_text().splitlines()]
    dense_check: collections.Counter = collections.Counter()
    seconds: collections.Counter = collections.Counter()
    for record in records:
        dense_check.update(record["integrity"])
        seconds[record["wg"]] += record["seconds"]
    indexes = {}
    for wg in sorted({record["wg"] for record in records}):
        index = Index(wg)
        indexes[wg] = {"file": str(index_path(wg).relative_to(ROOT)), "bytes": index_path(wg).stat().st_size,
                       "liveCounts": index.check_counts(), "manifest": index.manifest(),
                       "finishSeconds": index.con.execute(
                           "SELECT value FROM build_info WHERE name = 'finishSeconds'").fetchone()[0],
                       "chunkIds": index.chunk_id_checks()}
    report = {
        "items": {"files": [shown(path) for path in item_files], "total": len(items),
                  "measured": len(records)},
        "metric": "정답 행의 모든 칸이 문맥(청크마다 메타데이터 JSON + 경로별 길이로 자른 본문)에 들어 있으면 담김, "
                  "대소문자 무시, bis 회의 표기는 한 가지 철자로 맞춤. allRows=모든 행 담김, anyRow=한 행 이상 담김. 빈 정답 문항은 emptyGold 로만 센다.",
        "routes": {"dense": "run_chain_eval.retrieve(item, top): WG 의 결정·CR·기고문 컬렉션마다 top 개를 찾아 점수순 top 개",
                   "bm25": "WG 색인 전체(세 컬렉션)에 질문 낱말 OR 질의, FTS5 bm25 순위(메타데이터·본문 두 칸, 같은 가중치)",
                   "tdoc": "질문에 적힌 문서·묶음 번호와 tdocNumber 가 같은 청크 전부(작업 지시의 글자 그대로의 식별자 찾기)",
                   "rrf": f"BM25 상위 {FUSION_DEPTH} 와 retrieve(item, {FUSION_DEPTH}) 의 역순위 합, 상수 {RRF_K}",
                   "idkey": "질문의 작업반 문서 번호 = tdocNumber 또는 결정 기록 resolutionId(DOC-…)에 담긴 문서 번호, "
                            "RP 묶음 번호 = crPackId 또는 tdocNumber, "
                            "절 이력 문항의 (규격, 절) = CR 청크의 specNumber·clausesAffected(릴리스 거르지 않음)",
                   "idany": "idkey 에 더해 메타데이터나 본문에 문서·묶음 번호 표기가 들어 있는 청크",
                   "hop": "id 경로의 문맥에 보이는 R[1-5]- 문서 번호와 RP- 묶음 번호를 모두 같은 찾기로 한 번 더 따라감",
                   "suffix": "_1500·_8x1500 = 청크마다 본문 앞 1500자, _12x4000 = 4000자, _full = 본문 전체"},
        "integrity": {"denseChunksAgainstIndex": dict(dense_check), "indexes": indexes},
        "runtime": {"measureSecondsByWg": {wg: round(value, 1) for wg, value in sorted(seconds.items())},
                    "measureSecondsTotal": round(sum(seconds.values()), 1),
                    "buildSecondsTotal": round(sum(entry["seconds"] for info in indexes.values()
                                                   for entry in info["manifest"])
                                               + sum(info["finishSeconds"] for info in indexes.values()), 1)},
        **summarize(records),
    }
    (out_dir / "ceiling.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    total = report["groups"][0]
    print(json.dumps({"n": total["n"], "emptyGold": total["emptyGold"],
                      "allRows": {route: total["routes"][route]["allRows"] for route in ROUTES}}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build", help="WG 하나의 FTS5 색인을 Qdrant 에서 읽어 만든다")
    build_parser.add_argument("--wg", required=True, choices=WGS)
    build_parser.add_argument("--page", type=int, default=512, help="scroll 한 번에 읽는 점 수")
    measure_parser = sub.add_parser("measure", help="모든 문항의 경로별 상한을 센다")
    measure_parser.add_argument("--fresh", action="store_true", help="쌓아 둔 문항별 결과를 지우고 처음부터 센다")
    measure_parser.add_argument("--wg", nargs="*", choices=WGS, help="이 WG 들만 센다")
    measure_parser.add_argument("--limit", type=int, help="시험용: WG·종류마다 앞에서부터 이 수만 센다")
    measure_parser.add_argument("--items", type=Path, nargs="+", default=list(ITEM_FILES),
                                help="문항 파일(chain_items_admitted.jsonl). 주지 않으면 ITEM_FILES")
    measure_parser.add_argument("--out-dir", type=Path, default=OUT_DIR,
                                help="ceiling.json·items.jsonl 을 쓸 폴더. 색인은 언제나 INDEX_DIR 에서 읽는다")
    args = parser.parse_args()
    if args.command == "build":
        guard_memory()
        build(args.wg, args.page)
    else:
        measure(args.fresh, args.wg, args.limit, args.items, args.out_dir)


if __name__ == "__main__":
    main()
