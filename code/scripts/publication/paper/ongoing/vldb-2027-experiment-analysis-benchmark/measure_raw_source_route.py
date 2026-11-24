"""원문 글만으로 식별자를 따라갈 때 정답이 문맥에 얼마나 들어오는지 센다 (모델 호출 없음).

왜 재는가
  `measure_text_route_ceiling.py` 의 hop 경로는 기록 필드(payload 메타데이터 · `crPackId` · `clausesAffected` ·
  결정 기록의 `resolutionId`)로 청크를 찾고 문맥에도 메타데이터 JSON 을 붙인다. 그 담김에는 기록에서 만든 정보가
  들어 있다. 이 스크립트는 같은 식별자 따라가기를 원문 글만으로 다시 한다. 청크의 정체는 그 청크가 나온 원문
  파일의 문서 번호 하나이고, 문맥에는 원문 글과 그 파일 이름만 들어간다.

원문 글
  - 작업반 청크: `text_route_ceiling/index/ran{N}.sqlite3` 의 결정 기록 · CR · 기고문 청크 본문.
    `audit_source_text.py` 가 세 컬렉션을 원문 글로 판정했고(`final/raw_source_route/source_text_audit.json`),
    CR 청크는 `raw_source_text.raw_chunk_text` 로 기록 필드에서 만든 표지 줄을 걷어 낸 나머지만 쓴다.
    기고문 · CR 청크의 정체는 `tdoc` 칸(원문 zip 파일 이름의 문서 번호)이고, 문맥의 머리에도 이 번호만 붙인다.
    결정 기록 청크는 회의록에서 잘라 낸 글이라 자기 문서 번호가 없으므로, 본문에 번호가 적혀 있을 때(언급)만 들어온다.
  - TSG 총회 문서: `build_plenary_index.py` 가 만든 `final/raw_source_route/index/plenary.sqlite3`.
    청크의 정체는 바깥 파일 이름의 RP 번호(`owners`)와 zip 안 경로에 적힌 문서 번호(`member_owner`)다.
    문맥의 머리는 바깥 파일 이름들과 zip 안 경로다.

경로 (문항마다)
  시작  질문에 적힌 작업반 문서 번호(R[1-5]-…)와 RP 번호를 질문에 나온 차례로 찾는다. 번호마다
        ① 작업반 자기 번호 청크(`tdoc` = 번호, id 순) ② 작업반 언급 청크(본문에 번호 표기, id 순)
        ③ 총회 자기 번호 청크(바깥 파일의 청크 다음 zip 안 경로의 청크, 문서 · 순번 순) ④ 총회 언급 청크(id 순).
        언급은 FTS5 로 숫자 앞머리 토큰을 찾고 원문 글에서 `(?<![A-Za-z0-9])번호(?!\\d)` 로 다시 거른다(대시 변형은 `-` 로 본다).
        절 이력 문항은 이어서 (규격, 절) 청크를 넣는다(작업반 다음 총회, 각각 id 순). 그 절이 본문의
        `Clauses affected` 줄(값이 다음 줄에 있으면 다음 줄)에 있거나 줄 머리 제목으로 나오고, 같은 문서
        (작업반은 같은 `tdoc`, 결정 기록은 그 청크 하나, 총회는 zip 안 같은 문서)의 본문이나 파일 이름에 그 규격 번호가
        있는 청크다. 릴리스는 거르지 않는다(기존 측정과 같다).
  한 번 따라가기  시작 청크마다 보이는 글(머리 + 변형별 길이의 본문)에 나오는 문서 · RP 번호를 처음 나온 차례로
        모아, 이미 찾은 번호를 빼고 ①~④ 를 한 번씩 더 한다.
  변형  raw_wg_*     작업반 청크만(①② · 작업반 절 청크, 따라가기도 작업반만)
        raw_wgtsg_*  작업반 청크 + 총회 청크
        _1500 = 청크마다 본문 앞 1500자, _full = 본문 전체. 머리는 언제나 붙는다.
  문맥에서 같은 청크는 처음 들어온 자리에만 둔다. 변형끼리는 포함 관계다(raw_wg ⊆ raw_wgtsg, _1500 ⊆ _full).

무엇을 세는가
  `measure_text_route_ceiling.judge` 와 같은 담김이다. 정답 행의 모든 칸(`score_chain_eval.cell_key`)이 문맥 글에
  들어 있으면 담김이고, allRows · anyRow 와 singleChunk · singleDocument · multiDocument, 칸 이름별 담긴 비율,
  문항별 문맥 크기(청크 수 · 글자 수)를 남긴다. 문서 단위 분류에서는 작업반 청크를 기존 측정과 같이
  `measure_text_route_ceiling.doc_key` 로 묶고(분류에만 쓰고 찾기에는 쓰지 않는다), 총회 청크는 zip 안 문서 하나를
  한 문서로 본다. 문맥 글을 다 이어 붙이지 않고 청크 하나씩 견준다. 정답 칸에는 줄바꿈이 없으므로(실행 때 확인한다)
  줄바꿈으로 이어 붙인 글에서 견준 것과 결과가 같다. 회의 표기는 채점과 같이 bis 철자만 맞추고 그 밖의 표기 차이
  (`3GPP TSG RAN WG1 Meeting #99` 와 `RAN1#99` 같은)는 맞추지 않는다.

독해 모델에 넘기는 차례
  `orders.jsonl` 에 `ORDER_VARIANTS` 의 경로 차례(시작 청크 다음 따라간 청크)를 문항마다 남긴다. 청크 열쇠는
  작업반 `w:{WG}:{id}`, 총회 `t:{id}` 이고, 보이는 글 길이를 앞에서부터 더해 `ORDER_CHARS` 를 넘는 데까지 적는다.

자원
  사용 가능한 메모리가 8 GiB 아래로 내려가면 멈춘다. 색인은 읽기만 한다(Qdrant 는 색인 점 수 확인에만 읽는다).

사용 (저장소 루트에서):
  PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark python3 \\
    scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/measure_raw_source_route.py \\
    [--items <chain_items_admitted.jsonl> ...] [--out-dir <폴더>] [--wg RAN1 ...] [--limit N] [--fresh]
  문항별 결과(`items.jsonl` · `orders.jsonl`)를 쌓으며, 질문 · 정답 · 색인 해시가 모두 같은 문항은 다시 세지 않는다.
  끝나면 `<폴더>/ceiling.json` 을 쓴다.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sqlite3
import statistics
import time
from pathlib import Path

from build_plenary_index import DASHES, numbers_in
from measure_text_route_ceiling import (ROOT, WGS, Index, available_gib, doc_key, gold_sha, guard_memory, index_path,
                                         named_identifiers, shown)
from raw_source_text import raw_chunk_text
from score_chain_eval import cell_key, meeting_spelling

TRACK = ROOT / "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
ITEM_FILES = (TRACK / "integration/items_final/gate/core/chain_items_admitted.jsonl",
              TRACK / "integration/items_final/gate/ran5/chain_items_admitted.jsonl")
OUT_DIR = TRACK / "final/raw_source_route"
PLENARY = OUT_DIR / "index/plenary.sqlite3"
VARIANTS = ("raw_wg_1500", "raw_wg_full", "raw_wgtsg_1500", "raw_wgtsg_full")
ORDER_VARIANTS = ("raw_wg_1500", "raw_wgtsg_1500")
PASSAGE_CHARS = 1500
ORDER_CHARS = 200_000
FETCH = 900
RESOLUTION = "_resolution_chunks"
AFFECTED = re.compile(r"clauses?\s+affected\s*:?", re.I)
EMPTY_REST = re.compile(r"[\s|:;,.\-]*")


def mention_pattern(ident: str) -> re.Pattern:
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(ident) + r"(?!\d)", re.I)


def number_query(ident: str) -> str:
    """번호의 숫자 부분을 앞머리 토큰으로 찾는 FTS5 식(`R1-1909887r1` 같은 표기도 후보로 잡는다)."""
    return '"' + ident.split("-", 1)[1] + '"*'


def spec_query(spec: str) -> str:
    """규격 번호 후보를 찾는 FTS5 식. `38.213`·`TS38.213`·`38.213v16` 같은 표기를 모두 후보로 잡는다."""
    parts = re.findall(r"[0-9A-Za-z]+", spec)
    tail = "" if "-" in spec else "*"
    plain = " ".join(parts)
    return f'("{plain}"{tail} OR "ts{plain}"{tail})'


def spec_pattern(spec: str) -> re.Pattern:
    after = r"(?!\d|\.\d)" if "-" in spec else r"(?!\d|-\d|\.\d)"
    return re.compile(r"(?<![\d.])" + re.escape(spec) + after)


def spec_name_pattern(spec: str) -> re.Pattern:
    """파일 이름에 붙는 규격 표기(`38213_CR0058…`·`38213-CR…`·`38.213 CR…`)."""
    compact = re.escape(spec.replace(".", ""))
    return re.compile(r"(?<![\d.])(?:" + compact + r"|" + re.escape(spec) + r")(?=[ _-]?CR)", re.I)


def clause_query(clause: str) -> str:
    return '"' + " ".join(re.findall(r"[0-9A-Za-z]+", clause)) + '"'


def clause_pattern(clause: str) -> re.Pattern:
    return re.compile(r"(?<![\w.])" + re.escape(clause) + r"(?![\w]|\.\d)", re.I)


def clause_in_text(text: str, clause: re.Pattern, heading: re.Pattern) -> bool:
    """절 번호가 `Clauses affected` 줄의 값이나 줄 머리 제목으로 나오는가."""
    if heading.search(text):
        return True
    lines = text.split("\n")
    for position, line in enumerate(lines):
        match = AFFECTED.search(line)
        if not match:
            continue
        rest = line[match.end():]
        if EMPTY_REST.fullmatch(rest):
            following = next((later for later in lines[position + 1:] if later.strip()), "")
            rest = following
        if clause.search(rest):
            return True
    return False


def heading_pattern(clause: str) -> re.Pattern:
    return re.compile(r"^[ \t]*(?:[-–][ \t]*)?" + re.escape(clause) + r"(?:[ \t]|$)", re.I | re.M)


class Source:
    """원문 청크 저장소 하나(작업반 하나 또는 총회). 번호 찾기 결과는 실행 동안 기억한다."""

    prefix = ""

    def __init__(self):
        self.own_cache: dict[str, list[int]] = {}
        self.mention_cache: dict[str, list[int]] = {}
        self.spec_cache: dict[str, dict[str, list[int]]] = {}
        self.spec_doc_cache: dict[tuple[str, str], bool] = {}
        self.clause_cache: dict[tuple[str, str], list[int]] = {}

    def own(self, ident: str) -> list[int]:
        if ident not in self.own_cache:
            self.own_cache[ident] = self.own_ids(ident)
        return self.own_cache[ident]

    def mention(self, ident: str) -> list[int]:
        if ident not in self.mention_cache:
            pattern = mention_pattern(ident)
            candidates = self.match_ids(number_query(ident))
            found = [row_id for row_id, chunk in sorted(self.fetch(candidates).items())
                     if pattern.search(chunk["text"].translate(DASHES))]
            self.mention_cache[ident] = found
        return self.mention_cache[ident]

    def clause(self, spec: str, clause: str) -> list[int]:
        key = (spec, clause)
        if key not in self.clause_cache:
            spec_docs = self.spec_documents(spec)
            candidates = [row_id for row_id, doc in self.doc_of(self.match_ids(clause_query(clause))).items()
                          if doc in spec_docs]
            pattern, heading, found = clause_pattern(clause), heading_pattern(clause), []
            for row_id, chunk in sorted(self.fetch(candidates).items()):
                if clause_in_text(chunk["text"], pattern, heading) and self.doc_has_spec(spec, chunk["doc"]):
                    found.append(row_id)
            self.clause_cache[key] = found
        return self.clause_cache[key]

    def spec_documents(self, spec: str) -> dict[str, list[int]]:
        """규격 번호 후보 청크를 문서별로 모은다(FTS5 후보, 본문 확인은 `doc_has_spec` 에서 필요할 때만)."""
        if spec not in self.spec_cache:
            by_doc: dict[str, list[int]] = collections.defaultdict(list)
            for row_id, doc in self.doc_of(self.match_ids(spec_query(spec))).items():
                by_doc[doc].append(row_id)
            for doc in self.named_spec_documents(spec):
                by_doc.setdefault(doc, [])
            self.spec_cache[spec] = dict(by_doc)
        return self.spec_cache[spec]

    def doc_has_spec(self, spec: str, doc: str) -> bool:
        key = (spec, doc)
        if key not in self.spec_doc_cache:
            pattern = spec_pattern(spec)
            held = doc in self.named_spec_documents(spec)
            if not held:
                held = any(pattern.search(chunk["text"]) for chunk in
                           self.fetch(self.spec_documents(spec).get(doc, [])).values())
            self.spec_doc_cache[key] = held
        return self.spec_doc_cache[key]

    def named_spec_documents(self, spec: str) -> set[str]:
        return set()

    def key(self, row_id: int) -> str:
        return f"{self.prefix}{row_id}"


class WgSource(Source):
    def __init__(self, wg: str):
        super().__init__()
        self.wg = wg
        self.prefix = f"w:{wg}:"
        self.index = Index(wg)
        self.con = self.index.con

    def own_ids(self, ident: str) -> list[int]:
        return [row[0] for row in self.con.execute(
            "SELECT id FROM docs WHERE tdoc = ? AND collection NOT LIKE ? ESCAPE '\\' ORDER BY id",
            (ident, "%" + RESOLUTION.replace("_", "\\_")))]

    def match_ids(self, expression: str) -> list[int]:
        return [row[0] for row in self.con.execute("SELECT rowid FROM search WHERE search MATCH ?",
                                                    (f"text : {expression}",))]

    def doc_of(self, ids) -> dict[int, str]:
        """찾기용 같은 문서: 기고문 · CR 청크는 `tdoc`, 결정 기록 청크는 그 청크 하나."""
        ids, found = list(ids), {}
        for start in range(0, len(ids), FETCH):
            part = ids[start:start + FETCH]
            for row_id, collection, tdoc in self.con.execute(
                    f"SELECT id, collection, tdoc FROM docs WHERE id IN ({','.join('?' * len(part))})", part):
                found[row_id] = f"r:{row_id}" if collection.endswith(RESOLUTION) or not tdoc else tdoc
        return found

    def fetch(self, ids) -> dict[int, dict]:
        ids, found = list(ids), {}
        for start in range(0, len(ids), FETCH):
            part = ids[start:start + FETCH]
            for row_id, collection, chunk_id, tdoc, meta, text in self.con.execute(
                    f"SELECT id, collection, chunk_id, tdoc, meta, text FROM docs WHERE id IN "
                    f"({','.join('?' * len(part))})", part):
                raw, _ = raw_chunk_text(collection, chunk_id or "", text)
                resolution = collection.endswith(RESOLUTION) or not tdoc
                found[row_id] = {"text": raw, "header": "" if resolution else tdoc,
                                 "doc": f"r:{row_id}" if resolution else tdoc,
                                 "group": f"{self.wg}:" + doc_key(collection, json.loads(meta), chunk_id)}
        return found


class PlenarySource(Source):
    prefix = "t:"

    def __init__(self, path: Path):
        super().__init__()
        self.path = path
        self.con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        self.names = {file_id: "; ".join(dict.fromkeys(json.loads(names)))
                      for file_id, names in self.con.execute("SELECT id, names FROM files")}
        self.chains = {member_id: chain for member_id, chain in self.con.execute("SELECT id, chain FROM members")}
        self.named_spec_cache: dict[str, set[str]] = {}

    def own_ids(self, ident: str) -> list[int]:
        ids = [row[0] for row in self.con.execute(
            "SELECT c.id FROM owners o JOIN chunks c ON c.file_id = o.file_id WHERE o.own = ? "
            "ORDER BY c.file_id, c.member_id, c.seq", (ident,))]
        ids += [row[0] for row in self.con.execute(
            "SELECT c.id FROM member_owner m JOIN chunks c ON c.member_id = m.member_id WHERE m.own = ? "
            "ORDER BY c.member_id, c.seq", (ident,))]
        return list(dict.fromkeys(ids))

    def match_ids(self, expression: str) -> list[int]:
        return [row[0] for row in self.con.execute("SELECT rowid FROM search WHERE search MATCH ?", (expression,))]

    def doc_of(self, ids) -> dict[int, str]:
        ids, found = list(ids), {}
        for start in range(0, len(ids), FETCH):
            part = ids[start:start + FETCH]
            for row_id, member_id in self.con.execute(
                    f"SELECT id, member_id FROM chunks WHERE id IN ({','.join('?' * len(part))})", part):
                found[row_id] = f"m:{member_id}"
        return found

    def header(self, file_id: int, member_id: int) -> str:
        return f"{self.names[file_id]} / {self.chains[member_id]}"

    def fetch(self, ids) -> dict[int, dict]:
        ids, found = list(ids), {}
        for start in range(0, len(ids), FETCH):
            part = ids[start:start + FETCH]
            for row_id, member_id, file_id, text in self.con.execute(
                    f"SELECT id, member_id, file_id, text FROM chunks WHERE id IN ({','.join('?' * len(part))})",
                    part):
                found[row_id] = {"text": text, "header": self.header(file_id, member_id), "doc": f"m:{member_id}",
                                 "group": f"tsg:{member_id}"}
        return found

    def named_spec_documents(self, spec: str) -> set[str]:
        if spec not in self.named_spec_cache:
            pattern = spec_name_pattern(spec)
            docs = {f"m:{member_id}" for member_id, chain in self.chains.items() if pattern.search(chain)}
            for member_id, file_id in self.con.execute("SELECT id, file_id FROM members"):
                if pattern.search(self.names[file_id]):
                    docs.add(f"m:{member_id}")
            self.named_spec_cache[spec] = docs
        return self.named_spec_cache[spec]

    def build_info(self) -> dict:
        return dict(self.con.execute("SELECT name, value FROM build_info"))


def visible(chunk: dict, limit: int | None) -> str:
    text = chunk["text"] if limit is None else chunk["text"][:limit]
    return f"{chunk['header']}\n{text}" if chunk["header"] else text


def lookups(sources: list[Source], ident: str) -> list[str]:
    keys: list[str] = []
    for source in sources:
        keys += [source.key(row_id) for row_id in source.own(ident)]
        keys += [source.key(row_id) for row_id in source.mention(ident)]
    return keys


def route(named: dict, sources: list[Source], limit: int | None, fetched: dict[str, dict]) -> dict:
    """시작 청크와 한 번 따라간 청크를 경로 차례로 돌려준다."""
    seeds: list[str] = []
    for ident in named["docs"] + named["packs"]:
        seeds += lookups(sources, ident)
    if named["clause"]:
        for source in sources:
            seeds += [source.key(row_id) for row_id in source.clause(*named["clause"])]
    seeds = list(dict.fromkeys(seeds))
    load(seeds, sources, fetched)
    looked_up = set(named["docs"] + named["packs"])
    found: list[str] = []
    for key in seeds:
        found += numbers_in(visible(fetched[key], limit))
    follow = [ident for ident in dict.fromkeys(found) if ident not in looked_up]
    hops: list[str] = []
    for ident in follow:
        hops += lookups(sources, ident)
    ordered = list(dict.fromkeys(seeds + hops))
    return {"keys": ordered, "seedChunks": len(seeds), "identifiersFollowed": len(follow),
            "chunksAdded": len(ordered) - len(seeds)}


def load(keys, sources: list[Source], fetched: dict[str, dict]) -> None:
    by_prefix = {source.prefix: source for source in sources}
    wanted: dict[str, list[int]] = collections.defaultdict(list)
    for key in keys:
        if key not in fetched:
            prefix, row_id = key.rsplit(":", 1)
            wanted[prefix + ":"].append(int(row_id))
    for prefix, ids in wanted.items():
        source = by_prefix[prefix]
        for row_id, chunk in source.fetch(ids).items():
            fetched[source.key(row_id)] = chunk


class Judge:
    """`measure_text_route_ceiling.judge` 를 청크 하나씩 견주는 꼴로 옮긴 것."""

    def __init__(self, item: dict):
        self.cells = [[cell_key(cell) for cell in row] for row in item["gold"]]
        if any("\n" in cell for row in self.cells for cell in row):
            raise SystemExit(f"{item['id']}: 정답 칸에 줄바꿈이 있어 청크별 견주기가 이어 붙인 글과 달라진다")
        self.full = [(1 << len(row)) - 1 for row in self.cells]
        self.context = [0] * len(self.cells)
        self.single = [False] * len(self.cells)
        self.by_doc: dict[str, list[int]] = {}
        self.documents: set[str] = set()
        self.chunks = 0
        self.chars = 0

    def add(self, piece: str, group: str) -> None:
        self.chars += len(piece) + (1 if self.chunks else 0)
        self.chunks += 1
        self.documents.add(group)
        for position, cells in enumerate(self.cells):
            held = 0
            for bit, cell in enumerate(cells):
                if cell in piece:
                    held |= 1 << bit
            if not held:
                continue
            self.context[position] |= held
            if held == self.full[position]:
                self.single[position] = True
            doc = self.by_doc.setdefault(group, [0] * len(self.cells))
            doc[position] |= held

    def result(self, fields: list[str]) -> dict:
        rows, fields_held = [], [0] * len(fields)
        for position, full in enumerate(self.full):
            for bit in range(len(fields)):
                fields_held[bit] += bool(self.context[position] >> bit & 1)
            if self.context[position] != full:
                rows.append("missing")
            elif self.single[position]:
                rows.append("chunk")
            elif any(doc[position] == full for doc in self.by_doc.values()):
                rows.append("document")
            else:
                rows.append("documents")
        return {"chunks": self.chunks, "documents": len(self.documents), "chars": self.chars, "rows": rows,
                "fieldsHeld": fields_held}


def measure_item(item: dict, wg_source: WgSource, plenary: PlenarySource | None) -> tuple[dict, dict]:
    named = named_identifiers(item["question"])
    fetched: dict[str, dict] = {}
    plans = {}
    for variant in VARIANTS:
        sources = [wg_source] + ([plenary] if "wgtsg" in variant and plenary else [])
        if "wgtsg" in variant and plenary is None:
            continue
        plans[variant] = route(named, sources, PASSAGE_CHARS if variant.endswith("_1500") else None, fetched)
    members = {variant: set(plan["keys"]) for variant, plan in plans.items()}
    union = list(dict.fromkeys(key for plan in plans.values() for key in plan["keys"]))
    judges = {variant: Judge(item) for variant in plans}
    lengths: dict[str, int] = {}
    sources = [wg_source] + ([plenary] if plenary else [])
    for start in range(0, len(union), 4 * FETCH):
        part = union[start:start + 4 * FETCH]
        load(part, sources, fetched)
        for key in part:
            chunk = fetched.pop(key)
            short, whole = visible(chunk, PASSAGE_CHARS), visible(chunk, None)
            lengths[key] = len(short)
            pieces = {PASSAGE_CHARS: meeting_spelling(short.lower()), None: None}
            for variant, judge in judges.items():
                if key not in members[variant]:
                    continue
                if variant.endswith("_1500"):
                    judge.add(pieces[PASSAGE_CHARS], chunk["group"])
                else:
                    if pieces[None] is None:
                        pieces[None] = meeting_spelling(whole.lower())
                    judge.add(pieces[None], chunk["group"])
    record = {"id": item["id"], "questionSha256": hashlib.sha256(item["question"].encode()).hexdigest(),
              "goldSha256": gold_sha(item), "wg": item["wg"], "family": item["family"], "fields": item["fields"],
              "goldRows": len(item["gold"]), "named": named,
              "routes": {variant: judge.result(item["fields"]) for variant, judge in judges.items()},
              "hops": {variant: {key: plan[key] for key in ("seedChunks", "identifiersFollowed", "chunksAdded")}
                       for variant, plan in plans.items()}}
    orders = {"id": item["id"], "questionSha256": record["questionSha256"], "orders": {}}
    for variant in ORDER_VARIANTS:
        if variant not in plans:
            continue
        keys, total = [], 0
        for key in plans[variant]["keys"]:
            if total >= ORDER_CHARS:
                break
            keys.append(key)
            total += lengths[key] + 2
        orders["orders"][variant] = {"total": len(plans[variant]["keys"]), "stored": len(keys),
                                     "storedChars": total, "keys": keys}
    return record, orders


def summarize(records: list[dict], variants: tuple[str, ...]) -> dict:
    def group(selected: list[dict]) -> dict:
        scored = [record for record in selected if record["goldRows"]]
        out = {"n": len(scored), "emptyGold": len(selected) - len(scored), "routes": {}}
        for variant in variants:
            stats = collections.Counter()
            chunks, chars = [], []
            for record in scored:
                result = record["routes"][variant]
                rows = result["rows"]
                chunks.append(result["chunks"])
                chars.append(result["chars"])
                if "missing" not in rows:
                    stats["allRows"] += 1
                    worst = "documents" if "documents" in rows else "document" if "document" in rows else "chunk"
                    stats[{"chunk": "singleChunk", "document": "singleDocument", "documents": "multiDocument"}[worst]] += 1
                stats["anyRow"] += any(row != "missing" for row in rows)
            out["routes"][variant] = {key: stats[key] for key in ("allRows", "anyRow", "singleChunk", "singleDocument",
                                                                  "multiDocument")}
            if scored:
                out["routes"][variant].update(chunksMedian=statistics.median(chunks), chunksMax=max(chunks),
                                              charsMedian=statistics.median(chars), charsMax=max(chars),
                                              emptyContext=sum(1 for value in chunks if value == 0))
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
        fields[family] = {variant: {name: f"{sum(record['routes'][variant]['fieldsHeld'][position] for record in selected)}/{total}"
                                    for position, name in enumerate(names)} for variant in variants}
    hop_stats = {}
    for variant in variants:
        hop_stats[variant] = {}
        for key in ("seedChunks", "identifiersFollowed", "chunksAdded"):
            values = [record["hops"][variant][key] for record in records]
            hop_stats[variant][f"{key}Median"] = statistics.median(values)
            hop_stats[variant][f"{key}Max"] = max(values)
        hop_stats[variant]["noSeedItems"] = sum(1 for record in records if record["hops"][variant]["seedChunks"] == 0)
    return {"groups": groups, "fieldsHeld": fields, "hops": hop_stats}


def index_stamp(wgs: list[str], plenary: PlenarySource | None) -> str:
    parts = [{"wg": wg, "bytes": index_path(wg).stat().st_size} for wg in wgs]
    if plenary:
        parts.append({"plenary": plenary.build_info(), "bytes": plenary.path.stat().st_size})
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def measure(args) -> None:
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    per_item, per_order = out_dir / "items.jsonl", out_dir / "orders.jsonl"
    if args.fresh:
        per_item.unlink(missing_ok=True)
        per_order.unlink(missing_ok=True)
    plenary = None if args.no_tsg else PlenarySource(PLENARY)
    variants = VARIANTS if plenary else tuple(variant for variant in VARIANTS if "wgtsg" not in variant)
    items = [json.loads(line) for path in args.items for line in path.read_text().splitlines() if line.strip()]
    stamp = index_stamp(list(WGS), plenary)
    current = {item["id"]: (hashlib.sha256(item["question"].encode()).hexdigest(), gold_sha(item)) for item in items}
    stored = read_jsonl(per_item)
    kept = [record for record in stored if current.get(record["id"]) == (record["questionSha256"], record["goldSha256"])
            and record.get("indexStamp") == stamp]
    kept_ids = {record["id"] for record in kept}
    kept_orders = [order for order in read_jsonl(per_order) if order["id"] in kept_ids]
    if len(kept) != len(stored):
        per_item.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in kept))
        per_order.write_text("".join(json.dumps(order, ensure_ascii=False) + "\n" for order in kept_orders))
    taken: collections.Counter = collections.Counter()
    counts = {}
    with per_item.open("a") as out, per_order.open("a") as out_orders:
        for wg in WGS:
            if args.wg and wg not in args.wg:
                continue
            todo = [item for item in items if item["wg"] == wg and item["id"] not in kept_ids]
            if args.limit:
                limited = []
                for item in todo:
                    taken[item["family"], wg] += 1
                    if taken[item["family"], wg] <= args.limit:
                        limited.append(item)
                todo = limited
            if not todo:
                continue
            source = WgSource(wg)
            counts[wg] = source.index.check_counts()
            for position, item in enumerate(todo, 1):
                guard_memory()
                started = time.time()
                record, orders = measure_item(item, source, plenary)
                record["seconds"] = round(time.time() - started, 2)
                record["indexStamp"] = stamp
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                out_orders.write(json.dumps(orders, ensure_ascii=False) + "\n")
                out.flush()
                out_orders.flush()
                if position % 10 == 0 or position == len(todo):
                    print(json.dumps({"wg": wg, "done": position, "of": len(todo), "lastSeconds": record["seconds"],
                                      "availableGiB": round(available_gib(), 1)}), flush=True)
    records = read_jsonl(per_item)
    seconds = collections.Counter()
    for record in records:
        seconds[record["wg"]] += record["seconds"]
    report = {
        "items": {"files": [shown(path) for path in args.items], "total": len(items), "measured": len(records)},
        "metric": "정답 행의 모든 칸(cell_key)이 문맥(청크마다 머리 + 변형별 길이의 원문 본문)에 들어 있으면 담김. "
                  "대소문자 무시, bis 회의 표기만 한 가지 철자로 맞춤. allRows=모든 행 담김, anyRow=한 행 이상 담김. "
                  "빈 정답 문항은 emptyGold 로만 센다.",
        "identity": "작업반 기고문 · CR 청크는 tdoc 칸(원문 파일 이름의 문서 번호), 결정 기록 청크는 정체 없음(언급으로만 들어옴), "
                    "총회 청크는 바깥 파일 이름의 RP 번호와 zip 안 경로의 문서 번호",
        "variants": {"raw_wg": "작업반 원문 청크만", "raw_wgtsg": "작업반 원문 청크 + TSG 총회 문서 청크",
                     "suffix": "_1500 = 청크마다 본문 앞 1500자, _full = 본문 전체. 머리(문서 번호 · 파일 이름)는 언제나 붙는다"},
        "sources": {"wgIndexes": {wg: shown(index_path(wg)) for wg in WGS},
                    "wgLiveCounts": counts,
                    "plenaryIndex": shown(PLENARY) if plenary else None,
                    "plenaryBuildInfo": plenary.build_info() if plenary else None,
                    "sourceTextAudit": shown(OUT_DIR / "source_text_audit.json"),
                    "indexStamp": stamp},
        "runtime": {"measureSecondsByWg": {wg: round(value, 1) for wg, value in sorted(seconds.items())},
                    "measureSecondsTotal": round(sum(seconds.values()), 1)},
        **summarize(records, variants),
    }
    (out_dir / "ceiling.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    total = report["groups"][0]
    print(json.dumps({"n": total["n"], "emptyGold": total["emptyGold"],
                      "allRows": {variant: total["routes"][variant]["allRows"] for variant in variants}},
                     ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", default=list(ITEM_FILES), help="문항 파일(chain_items_admitted.jsonl)")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR, help="ceiling.json · items.jsonl · orders.jsonl 을 쓸 폴더")
    parser.add_argument("--wg", nargs="*", choices=WGS, help="이 WG 들만 센다")
    parser.add_argument("--limit", type=int, help="시험용: WG · 종류마다 앞에서부터 이 수만 센다")
    parser.add_argument("--no-tsg", action="store_true", help="시험용: 총회 색인 없이 raw_wg 변형만 센다")
    parser.add_argument("--fresh", action="store_true", help="쌓아 둔 문항별 결과를 지우고 처음부터 센다")
    measure(parser.parse_args())


if __name__ == "__main__":
    main()
