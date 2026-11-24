"""추적 사슬 문항의 정답에서 기록 요소 하나를 다른 출처의 값으로 바꾸면 정답 행이 바뀌는지 센다 (모델 호출 없음).

정답 행은 여섯 요소를 잇는다. E1 처분(회의 보고서), E2 결정 회의, E3 개정 연결, E4 CR 의 묶음 소속(묶음 표지),
E5 묶음의 TSG 회의, E6 CR 이 고치는 절이다. 요소를 비우는 대조는 그 요소를 쓰는지만 보인다. 여기서는 요소마다
같은 사실을 적은 가장 가까운 다른 출처, 곧 사무국 TDoc 목록의 칸으로 그 요소만 바꾸고
`measure_relational_equivalence.py` 의 `cr_side` 참조 SQL 을 그대로 다시 실행한다.
- E1   처분 코드 ← 목록 상태(`document.list_status`). 표기는 `measure_cross_source_agreement.py` 와 같이 맞춘다
       (`approved` = `agreed`, `endorsed (bl)` = `endorsed`, 밑줄 = 공백). 처분 기록의 회의는 그대로 둔다.
- E2   결정 회의 ← 목록의 발표 회의(`document.presented_at`). 처분 코드는 그대로 둔다.
- E1E2 처분 기록 전체 ← 목록 한 줄(상태와 발표 회의)로 처분 행을 새로 만든다.
- E3   개정 연결 ← 앞 문서의 `revisedTo` 칸. 기록은 뒤 문서의 `isRevisionOf` 칸이라 두 칸 모두 목록에서 온다.
- E4   묶음 소속 ← 목록의 묶음 번호(`document.pack_field`). 묶음 기록에 없는 묶음은 TSG 회의(E5)를 모르므로 NULL 이다.
- E6   고친 절 ← 목록의 `tdoc:clausesAffected` 를 생성기와 같은 절 해소 규칙으로 목록 자신의 규격·release 에 잇는다.
E5 는 내보낸 기록 가운데 묶음 기록 밖에 같은 사실을 적은 칸이 없어 바꾸지 않는다.

다른 출처가 어떤 대상에 대해 값을 말하지 않으면(목록에 없는 문서, 빈 상태, `available`·`reserved`, 닫힌 코드
집합 밖의 상태, 그 회의의 목록에 칸 자체가 없는 경우 등) 그 대상을 정의되지 않은 대상으로 둔다. 문항마다 두 번
실행한다. A 는 바꾼 테이블만 쓴 결과, F 는 정의되지 않은 대상에 기록 값을 채운 결과다. 질의가 모두 내부 조인이라
A ⊆ F 다.
- changed    A 에 정답 밖 행이 있거나(추가) F 에서 정답 행이 빠진다(손실). 정의되지 않은 대상을 어떻게 채워도 남는다
- undefined  추가·손실은 없지만 F 와 A 가 다르거나, 읽은 문서 가운데 정의되지 않은 대상이 있다
- unchanged  A = F = 정답이고 읽은 문서가 모두 정의되어 있다
단위는 문항이다. 바꾸기 전 재계산이 정답과 다른 문항은 셈에서 빼고 따로 적는다. E6 는 표지의 절 칸을 지금의
해소 규칙으로 다시 이었을 때 정답이 달라지는 문항(해소 규칙 변화)도 뺀다.

DB 는 읽기 전용으로 열고, 바꾼 테이블은 같은 이름의 TEMP 테이블로 가린다. RAN1~4 DB 는 다시 지은 처분 기록을
이미 담고 있어 그대로 쓴다. `--pre-integration-wg` 작업반의 문항 가운데 처분 테이블을 읽는 문항은 그래프 통합
전 기록에 기댄 결과로 표시한다. RAN4·RAN5 의 절 색인은 생성기처럼 Neo4j 에서 읽되 읽기 전용 세션만 쓴다.

사용: python3 measure_substitution_ablation.py --db-dir <dir> --items <jsonl> [<jsonl> ...] --out <json>
          [--neo4j-section-wg RAN4 RAN5] [--pre-integration-wg RAN1]      (저장소 루트에서 실행)
"""
from __future__ import annotations

import argparse
import collections
import gc
import hashlib
import importlib.util
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Callable, NamedTuple

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path[:0] = [str(HERE), str(ROOT / "scripts" / "common"), str(ROOT / "scripts" / "tsg" / "RAN" / "formal" / "common")]

from decision_disposition import CODES  # noqa: E402
from export_chain_records_sqlite import INDEXES, SECTION, as_list, available_gib  # noqa: E402
from measure_cross_source_agreement import LIST_WITHOUT_DISPOSITION, SAME, canonical  # noqa: E402
from measure_cross_source_agreement import measure as instance_cross_source  # noqa: E402
from measure_pack_source_agreement import PACK_NUMBER  # noqa: E402
from measure_relational_equivalence import SQL, VARIANTS, shape  # noqa: E402
from verify_chain_items import CLOSED_WITHOUT_PACK  # noqa: E402

LOGS = Path("logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark")
INSTANCES = Path("ontology/output/tsg/RAN/formal/instances")
PARSED = Path("ontology/output/tsg/RAN/formal/parsed_cr")
GENERATOR = {**{wg: Path(f"scripts/tsg/RAN/formal/{wg}/phase-4/cr-parser/03_generate_cr_jsonld.py")
                for wg in ("RAN1", "RAN2", "RAN3", "RAN4")},
             "RAN5": Path("scripts/tsg/RAN/formal/RAN5/phase-4/neo4j/01_load_cr_ontology.py")}
# 그래프 통합이 진행 중인 포트. 이 포트의 그래프는 읽지 않는다.
BUSY_BOLT_PORT = ":7687"
QUERIES = {family: sql.format(**VARIANTS["cr_side"]) for family, sql in SQL.items()}
TABLES = {family: set(shape(sql)["tableNames"]) for family, sql in QUERIES.items()}
TABLE_NAMES = ("document", "revision", "meeting", "resolution", "disposition", "cr_pack", "cr_in_pack",
               "pack_member", "section", "cr_modifies_section", "section_modified_by")
# TEMP 테이블에는 기본 키가 없어 내보내기의 색인에 더해 id 칸 색인을 둔다.
ID_INDEXES = (("disposition", "id"), ("resolution", "id"), ("cr_pack", "id"), ("section", "id"))
# 예시에 적는 행·문서 수의 상한. 예시는 읽는 사람이 바뀐 자리를 보게 하려는 것이라 전부 싣지 않는다.
ROW_CAP, DOCUMENT_CAP, EXAMPLES = 40, 15, 3
# 처분 표를 읽지 않는 문항 종류. 통합 전 표시에서 뺀다.
NO_DISPOSITION_FAMILIES = {family for family, tables in TABLES.items() if "disposition" not in tables}
GLOB_PACK = re.compile(r"RP-[0-9]")


class Doc(NamedTuple):
    id: str
    number: str
    doc_type: str | None
    cr_number: str | None
    spec: str | None
    target_release: str | None
    list_status: str | None
    presented_at: str | None
    pack_field: str | None


def code_key(value: str) -> str:
    return canonical(value).replace(" ", "_")


def list_code(status: str | None) -> tuple[str, str | None]:
    """목록 상태를 닫힌 처분 코드로 옮긴다. (종류, 코드) 를 돌려준다."""
    if status is None or not status.strip():
        return "noListStatus", None
    value = canonical(status)
    if value in LIST_WITHOUT_DISPOSITION:
        return "listWithoutDisposition", None
    code = value.replace(" ", "_")
    return ("mapped", code) if code in CODES else ("outsideCodeSet", None)


def is_verified(row: tuple) -> bool:
    return row[4] == "source_verified" and row[5] == "whole_target"


def row_key(row) -> tuple[str, ...]:
    return tuple("" if value is None else str(value) for value in row)


def rows_out(rows) -> list:
    return [list(row) for row in sorted(rows, key=row_key)[:ROW_CAP]]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 24), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_memory(floor: float, label: str, log: list) -> None:
    gib = round(available_gib(), 1)
    log.append({"step": label, "availableGib": gib})
    if gib < floor:
        raise SystemExit(f"가용 메모리 {gib} GiB < {floor} GiB: {label} 앞에서 멈춘다")


def walk(start: str, following: dict[str, set[str]]) -> set[str]:
    """재귀 공통 테이블식 `later` 와 같은 집합(시작 문서는 순환으로 돌아올 때만 든다)."""
    seen: set[str] = set()
    frontier = list(following.get(start, ()))
    while frontier:
        node = frontier.pop()
        if node not in seen:
            seen.add(node)
            frontier.extend(following.get(node, ()))
    return seen


class Records:
    """DB 의 기록을 파이썬 구조로 읽어 둔다. 대체 테이블과 읽은 문서 집합을 만들 때 쓴다."""

    def __init__(self, db: sqlite3.Connection) -> None:
        self.rows = {name: db.execute(f"SELECT * FROM main.{name}").fetchall() for name in TABLE_NAMES}
        self.documents = {row[0]: Doc(*row) for row in self.rows["document"]}
        self.meetings = {row[0] for row in self.rows["meeting"]}
        self.meeting_of = dict(self.rows["resolution"])
        self.codes: dict[str, set[str]] = collections.defaultdict(set)
        self.record_meetings: dict[str, set] = collections.defaultdict(set)
        self.verified_rows: dict[str, list[tuple]] = collections.defaultdict(list)
        self.all_codes: dict[str, set[str]] = collections.defaultdict(set)
        for row in self.rows["disposition"]:
            self.all_codes[row[2]].add(row[3])
            if is_verified(row):
                self.codes[row[2]].add(code_key(row[3]))
                self.record_meetings[row[2]].add(self.meeting_of.get(row[1]))
                self.verified_rows[row[2]].append(row)
        self.following: dict[str, set[str]] = collections.defaultdict(set)
        for earlier, later in self.rows["revision"]:
            self.following[earlier].add(later)
        self.pack_ids = {row[0] for row in self.rows["cr_pack"]}
        self.pack_crs: dict[str, set[str]] = collections.defaultdict(set)
        self.member_packs: dict[str, set[str]] = collections.defaultdict(set)
        for cr, pack in self.rows["pack_member"]:
            self.pack_crs[pack].add(cr)
            self.member_packs[cr].add(pack)
        self.in_packs: dict[str, set[str]] = collections.defaultdict(set)
        for cr, pack in self.rows["cr_in_pack"]:
            self.in_packs[cr].add(pack)
        self.changes: dict[str, set[str]] = collections.defaultdict(set)
        self.section_crs: dict[str, set[str]] = collections.defaultdict(set)
        for cr, section in self.rows["cr_modifies_section"]:
            self.changes[cr].add(section)
            self.section_crs[section].add(cr)
        self.modified_by: dict[str, set[str]] = collections.defaultdict(set)
        for cr, section in self.rows["section_modified_by"]:
            self.modified_by[section].add(cr)
        self.sections = {row[0]: row for row in self.rows["section"]}
        self.by_pack_field: dict[str, set[str]] = collections.defaultdict(set)
        for doc in self.documents.values():
            if doc.pack_field is not None:
                self.by_pack_field[doc.pack_field].add(doc.id)

    def release_matched(self, section: str, crs) -> set[str]:
        """`doc.target_release = s.release` 를 통과하는 CR(문서가 목록에 있고 두 release 가 NULL 이 아니고 같다)."""
        release = self.sections.get(section, (None, None, None, None))[2]
        return {cr for cr in crs if cr in self.documents and release is not None
                and self.documents[cr].target_release == release}

    def base_read(self, item: dict) -> set[str]:
        """질의가 처분·회의·묶음 값을 읽는 문서."""
        family, anchor = item["family"], item["anchor"]
        if family == "revision_chain":
            return walk(anchor, self.following)
        if family == "clause_history":
            return self.release_matched(anchor, self.section_crs.get(anchor, ()))
        if family == "pack_origin":
            return set(self.pack_crs.get(anchor, ()))
        return {anchor}


class Shadow:
    """같은 이름의 TEMP 테이블로 main 테이블을 가린다. 나갈 때 TEMP 테이블을 지운다."""

    def __init__(self, db: sqlite3.Connection, tables: dict[str, list[tuple]]) -> None:
        self.db, self.tables = db, tables

    def __enter__(self) -> "Shadow":
        for name, rows in self.tables.items():
            self.db.execute(f"CREATE TEMP TABLE {name} AS SELECT * FROM main.{name} WHERE 0")
            self.insert(name, rows)
            for table, column in INDEXES + ID_INDEXES:
                if table == name:
                    self.db.execute(f"CREATE INDEX temp.shadow_{table}_{column} ON {table}({column})")
        return self

    def insert(self, name: str, rows: list[tuple]) -> None:
        if rows:
            self.db.executemany(f"INSERT INTO temp.{name} VALUES ({', '.join('?' * len(rows[0]))})", rows)

    def __exit__(self, *exc) -> None:
        for name in self.tables:
            self.db.execute(f"DROP TABLE IF EXISTS temp.{name}")
        self.db.commit()


def run(db: sqlite3.Connection, item: dict) -> set[tuple]:
    return {tuple(row) for row in db.execute(QUERIES[item["family"]], {"anchor": item["anchor"]})}


class Substitution(NamedTuple):
    name: str
    tables: dict[str, list[tuple]]          # 대체 테이블(가릴 테이블 이름 → 행)
    fill: dict[str, list[tuple]]            # 정의되지 않은 대상의 기록 행
    state: Callable[[str], str]             # 문서(대상)별 상태
    defined: frozenset[str]                 # 정의된 상태
    read: Callable[[dict], set[str]]        # 문항이 이 요소 값을 읽는 문서
    describe: Callable[[str], dict]         # 예시용 문서별 기록 값과 대체 값
    open_candidates: Callable[[dict, set[str]], int] | None = None


def evaluate(db: sqlite3.Connection, sub: Substitution, items: list[dict], wg: str, pre: bool) -> list[dict]:
    with Shadow(db, sub.tables) as shadow:
        alternative = {item["id"]: run(db, item) for item in items}
        for name, rows in sub.fill.items():
            shadow.insert(name, rows)
        filled = {item["id"]: run(db, item) for item in items}
    results = []
    for item in items:
        gold = {tuple(row) for row in item["gold"]}
        a, f = alternative[item["id"]], filled[item["id"]]
        read = sub.read(item)
        undefined_docs = sorted(d for d in read if sub.state(d) not in sub.defined)
        added, lost = a - gold, gold - f
        unexpressed, uncertain = (gold & f) - a, f - a - gold
        if added or lost:
            outcome, detail = "changed", "both" if added and lost else "addedOnly" if added else "lostOnly"
        elif f != a:
            outcome, detail = "undefined", "rowsNeedRecord"
        elif undefined_docs:
            outcome, detail = "undefined", "readDocumentOnly"
        else:
            outcome, detail = "unchanged", None
        result = {"id": item["id"], "wg": wg, "family": item["family"], "outcome": outcome, "detail": detail,
                  "alsoUndefined": outcome == "changed" and bool(unexpressed or uncertain or undefined_docs),
                  "preIntegration": pre and item["family"] not in NO_DISPOSITION_FAMILIES,
                  "rows": {"gold": len(gold), "alternative": len(a), "filled": len(f), "added": len(added),
                           "lost": len(lost), "unexpressed": len(unexpressed), "uncertain": len(uncertain),
                           "addedWithNull": sum(any(v is None for v in row) for row in added)},
                  "readDocuments": len(read), "undefinedDocuments": len(undefined_docs),
                  "undefinedStates": dict(collections.Counter(sub.state(d) for d in undefined_docs)),
                  "subsetViolation": not a <= f}
        if sub.open_candidates is not None:
            result["openCandidates"] = sub.open_candidates(item, read)
        if outcome != "unchanged":
            described = [{"document": d, **sub.describe(d)} for d in sorted(read)]
            described.sort(key=lambda entry: (entry["record"] == entry["alternative"], entry["document"]))
            result["_example"] = {
                "anchor": item["anchor"], "question": item["question"],
                "goldRows": rows_out(gold), "alternativeRows": rows_out(a), "addedRows": rows_out(added),
                "lostRows": rows_out(lost), "unexpressedRows": rows_out(unexpressed),
                "uncertainRows": rows_out(uncertain), "documents": described[:DOCUMENT_CAP],
                "documentsShown": min(len(described), DOCUMENT_CAP), "documentsRead": len(described)}
        results.append(result)
    return results


# --- 대체 ---------------------------------------------------------------------------------------------

E1_DEFINED = frozenset({"noVerifiedDisposition", "sameCode", "listCodeAmongRecordCodes", "differentCode"})


def substitute_e1(rec: Records) -> tuple[Substitution, dict]:
    def state(d: str) -> str:
        if not rec.codes.get(d):
            return "noVerifiedDisposition"
        doc = rec.documents.get(d)
        if doc is None:
            return "notInDocumentList"
        kind, code = list_code(doc.list_status)
        if kind != "mapped":
            return kind
        if rec.codes[d] == {code}:
            return "sameCode"
        return "listCodeAmongRecordCodes" if code in rec.codes[d] else "differentCode"

    table, fill = [], []
    for row in rec.rows["disposition"]:
        if not is_verified(row):
            table.append(row)
        elif state(row[2]) in E1_DEFINED:
            table.append(row[:3] + (list_code(rec.documents[row[2]].list_status)[1],) + row[4:])
        else:
            fill.append(row)

    def describe(d: str) -> dict:
        doc = rec.documents.get(d)
        s = state(d)
        alternative = ([list_code(doc.list_status)[1]] if s in E1_DEFINED - {"noVerifiedDisposition"}
                       else [] if s == "noVerifiedDisposition" else None)
        return {"state": s, "record": sorted(rec.codes.get(d, ())), "alternative": alternative,
                "listStatus": doc.list_status if doc else None}

    targets = collections.Counter(state(t) for t in rec.codes)
    mapping: collections.Counter[tuple] = collections.Counter()
    on_targets: collections.Counter[tuple] = collections.Counter()
    for doc in rec.documents.values():
        kind, code = list_code(doc.list_status)
        entry = (doc.list_status, canonical(doc.list_status) if doc.list_status else None, kind, code)
        mapping[entry] += 1
        on_targets[entry] += doc.id in rec.codes
    diagnostics = {
        "verifiedTargetStates": dict(sorted(targets.items())),
        "valueMapping": [{"listStatus": raw, "normalized": norm, "kind": kind, "code": code,
                          "documents": n, "verifiedTargets": on_targets[(raw, norm, kind, code)]}
                         for (raw, norm, kind, code), n in sorted(mapping.items(), key=lambda kv: -kv[1])],
        "recordCodesOutsideCodeSet": sorted({c for codes in rec.all_codes.values() for c in codes
                                             if code_key(c) not in CODES}),
        "dispositionRowsReplaced": len(rec.rows["disposition"]) - len(fill),
        "verifiedRowsLeftToFill": len(fill)}
    return Substitution("E1", {"disposition": table}, {"disposition": fill}, state, E1_DEFINED,
                        rec.base_read, describe), diagnostics


def presented_reason(rec: Records, d: str) -> str | None:
    doc = rec.documents.get(d)
    if doc is None:
        return "notInDocumentList"
    if doc.presented_at is None:
        return "noPresentedAt"
    return None if doc.presented_at in rec.meetings else "presentedAtNotMeeting"


E2_DEFINED = frozenset({"noVerifiedDisposition", "sameMeeting", "presentedAmongRecord", "recordWithoutMeeting",
                        "differentMeeting"})


def substitute_e2(rec: Records) -> tuple[Substitution, dict]:
    def state(d: str) -> str:
        if not rec.codes.get(d):
            return "noVerifiedDisposition"
        reason = presented_reason(rec, d)
        if reason:
            return reason
        presented = rec.documents[d].presented_at
        known = rec.record_meetings[d] & rec.meetings
        if known == {presented}:
            return "sameMeeting"
        if presented in known:
            return "presentedAmongRecord"
        return "recordWithoutMeeting" if not known else "differentMeeting"

    table, fill, resolutions = [], [], list(rec.rows["resolution"])
    for row in rec.rows["disposition"]:
        if not is_verified(row):
            table.append(row)
        elif state(row[2]) in E2_DEFINED:
            table.append((row[0], "alt:" + row[2]) + row[2:])
        else:
            fill.append(row)
    resolutions += [("alt:" + t, rec.documents[t].presented_at) for t in rec.codes if state(t) in E2_DEFINED]

    def describe(d: str) -> dict:
        doc = rec.documents.get(d)
        s = state(d)
        record = sorted({m for m in rec.record_meetings.get(d, ())} - {None}) if d in rec.codes else []
        alternative = [doc.presented_at] if s in E2_DEFINED - {"noVerifiedDisposition"} else (
            [] if s == "noVerifiedDisposition" else None)
        return {"state": s, "record": record, "alternative": alternative,
                "presentedAt": doc.presented_at if doc else None}

    diagnostics = {"verifiedTargetStates": dict(sorted(collections.Counter(state(t) for t in rec.codes).items())),
                   "valueMapping": "발표 회의 식별자를 그대로 결정 회의로 쓴다(회의 표의 식별자와 같은 꼴)",
                   "presentedAtReasons": dict(collections.Counter(
                       presented_reason(rec, d) or "meetingKnown" for d in rec.documents)),
                   "verifiedRowsLeftToFill": len(fill)}
    return Substitution("E2", {"disposition": table, "resolution": resolutions}, {"disposition": fill}, state,
                        E2_DEFINED, rec.base_read, describe), diagnostics


E12_DEFINED = frozenset({"listRow", "silentBoth", "notInDocumentList-noRecord"})


def substitute_e1e2(rec: Records) -> tuple[Substitution, dict]:
    def state(d: str) -> str:
        doc, has = rec.documents.get(d), bool(rec.codes.get(d))
        if doc is None:
            return "notInDocumentList" if has else "notInDocumentList-noRecord"
        kind, _ = list_code(doc.list_status)
        if kind == "mapped":
            reason = presented_reason(rec, d)
            return "listRow" if reason is None else f"mapped-{reason}"
        if kind == "outsideCodeSet":
            return "outsideCodeSet"
        return f"{kind}-withRecord" if has else "silentBoth"

    table = [row for row in rec.rows["disposition"] if not is_verified(row)]
    resolutions = list(rec.rows["resolution"])
    crosstab: collections.Counter[tuple] = collections.Counter()
    for d, doc in rec.documents.items():
        s = state(d)
        if s == "listRow":
            code = list_code(doc.list_status)[1]
            table.append(("list:" + d, "list:" + d, d, code, "source_verified", "whole_target", None, None))
            resolutions.append(("list:" + d, doc.presented_at))
            has = bool(rec.codes.get(d))
            crosstab[(s, has, has and code in rec.codes[d], has and doc.presented_at in rec.record_meetings[d])] += 1
        else:
            crosstab[(s, bool(rec.codes.get(d)), None, None)] += 1
    for t in rec.codes:
        if t not in rec.documents:
            crosstab[(state(t), True, None, None)] += 1
    fill = [row for t, rows in rec.verified_rows.items() if state(t) not in E12_DEFINED for row in rows]

    def describe(d: str) -> dict:
        doc = rec.documents.get(d)
        s = state(d)
        record = sorted([code_key(r[3]), rec.meeting_of.get(r[1]) or ""] for r in rec.verified_rows.get(d, ()))
        record = [list(x) for x in dict.fromkeys(tuple(x) for x in record)]
        alternative = ([[list_code(doc.list_status)[1], doc.presented_at]] if s == "listRow"
                       else [] if s in E12_DEFINED else None)
        return {"state": s, "record": record, "alternative": alternative,
                "listStatus": doc.list_status if doc else None, "presentedAt": doc.presented_at if doc else None}

    diagnostics = {"crosstab": [{"state": s, "hasVerifiedRecord": has, "codeAmongRecord": code,
                                 "meetingAmongRecord": meeting, "documents": n}
                                for (s, has, code, meeting), n in sorted(crosstab.items(), key=row_key)],
                   "listRows": sum(n for (s, *_), n in crosstab.items() if s == "listRow"),
                   "verifiedRowsLeftToFill": len(fill)}
    return Substitution("E1E2", {"disposition": table, "resolution": resolutions}, {"disposition": fill}, state,
                        E12_DEFINED, rec.base_read, describe), diagnostics


E3_DEFINED = frozenset({"link", "linkTargetsOutsideDocumentList", "none"})
# 빈 칸 민감도에서 정의되지 않은 쪽으로 옮기는 상태(칸이 있는 회의의 빈 칸).
BLANK_STATES = {"E3": "none", "E4": "none-emptyCell", "E6": "noListText-emptyCell"}


def link_ids(value) -> list[str]:
    ids = []
    for entry in as_list(value):
        if isinstance(entry, dict):
            entry = entry.get("@id")
        if isinstance(entry, str) and entry:
            ids.append(entry)
    return list(dict.fromkeys(ids))


def substitute_e3(rec: Records, revised_to: dict[str, object], blank_defined: bool = True) -> tuple[Substitution, dict]:
    defined = E3_DEFINED if blank_defined else E3_DEFINED - {BLANK_STATES["E3"]}
    column = {rec.documents[d].presented_at for d, value in revised_to.items() if link_ids(value)}
    alt_following: dict[str, set[str]] = {}
    dropped = 0
    for d, value in revised_to.items():
        ids = link_ids(value)
        kept = [x for x in ids if x in rec.documents]
        dropped += len(ids) - len(kept)
        if kept:
            alt_following[d] = set(kept)

    def state(d: str) -> str:
        doc = rec.documents.get(d)
        if doc is None:
            return "notInDocumentList"
        if link_ids(revised_to.get(d)):
            return "link" if d in alt_following else "linkTargetsOutsideDocumentList"
        if doc.presented_at is None:
            return "noPresentedAt"
        return "none" if doc.presented_at in column else "meetingWithoutColumn"

    table = [(d, x) for d, targets in alt_following.items() for x in sorted(targets)]
    fill = [row for row in rec.rows["revision"] if state(row[0]) not in defined]
    filled_following: dict[str, set[str]] = collections.defaultdict(set)
    for earlier, later in table + fill:
        filled_following[earlier].add(later)

    def read(item: dict) -> set[str]:
        return {item["anchor"]} | walk(item["anchor"], filled_following)

    def describe(d: str) -> dict:
        s = state(d)
        alternative = sorted(alt_following.get(d, ())) if s in defined else None
        doc = rec.documents.get(d)
        return {"state": s, "record": sorted(rec.following.get(d, ())), "alternative": alternative,
                "presentedAt": doc.presented_at if doc else None,
                "laterPresentedAt": sorted({rec.documents[x].presented_at for x in
                                            rec.following.get(d, set()) | alt_following.get(d, set())
                                            if x in rec.documents})}

    record_pairs, alt_pairs = set(rec.rows["revision"]), set(table)

    def by_meeting(pairs) -> dict:
        """연결의 두 문서가 같은 회의에 발표되었는지."""
        meeting = lambda d: rec.documents[d].presented_at if d in rec.documents else None
        return dict(collections.Counter("sameMeeting" if meeting(e) == meeting(x) else "crossMeeting"
                                        for e, x in pairs))

    diagnostics = {
        "documentStates": dict(collections.Counter(state(d) for d in rec.documents)),
        "valueMapping": "revisedTo 의 문서 식별자를 그대로 (앞 문서, 뒤 문서) 연결로 쓴다",
        "linkTargetsDropped": dropped, "meetingsWithColumn": len(column),
        "pairs": {"both": len(record_pairs & alt_pairs), "alternativeOnly": len(alt_pairs - record_pairs),
                  "recordOnlyByEarlierState": dict(collections.Counter(
                      state(e) for e, _ in record_pairs - alt_pairs))},
        "pairsByMeeting": {"both": by_meeting(record_pairs & alt_pairs),
                           "alternativeOnly": by_meeting(alt_pairs - record_pairs),
                           "recordOnlyEarlierNone": by_meeting(
                               (e, x) for e, x in record_pairs - alt_pairs if state(e) == "none")},
        "recordRowsLeftToFill": len(fill)}
    return Substitution("E3", {"revision": table}, {"revision": fill}, state, defined, read, describe), diagnostics


E4_DEFINED = frozenset({"link", "none-dash", "none-emptyCell"})


def pack_category(rec: Records, doc: Doc) -> str:
    """`measure_pack_source_agreement.py` 와 같은 분류."""
    value = doc.pack_field or ""
    recorded = {pack.rsplit("/", 1)[-1] for pack in rec.member_packs.get(doc.id, ())}
    if not PACK_NUMBER.fullmatch(value):
        return "packRecordOnly" if recorded else "neither"
    if value in recorded:
        return "same"
    return "differentPack" if recorded else "documentListOnly"


def substitute_e4(rec: Records, blank_defined: bool = True) -> tuple[Substitution, dict]:
    defined = E4_DEFINED if blank_defined else E4_DEFINED - {BLANK_STATES["E4"]}
    column = {doc.presented_at for doc in rec.documents.values() if doc.pack_field is not None}

    def state(d: str) -> str:
        doc = rec.documents.get(d)
        if doc is None:
            return "notInDocumentList"
        if doc.pack_field is not None:
            if PACK_NUMBER.fullmatch(doc.pack_field):
                return "link"
            return "none-dash" if doc.pack_field == "-" else "nonPackText"
        if doc.presented_at is None:
            return "noPresentedAt"
        return "none-emptyCell" if doc.presented_at in column else "meetingWithoutColumn"

    links = [(d, "tdoc:crpack/" + doc.pack_field) for d, doc in rec.documents.items() if state(d) == "link"]
    new_packs = sorted({pack for _, pack in links} - rec.pack_ids)
    packs = list(rec.rows["cr_pack"]) + [(pack, pack.rsplit("/", 1)[-1], None, None) for pack in new_packs]
    fill_in = [row for row in rec.rows["cr_in_pack"] if state(row[0]) not in defined]
    fill_member = [row for row in rec.rows["pack_member"] if state(row[0]) not in defined]

    def read(item: dict) -> set[str]:
        if item["family"] == "pack_origin":
            return set(rec.pack_crs.get(item["anchor"], ())) | rec.by_pack_field.get(
                item["anchor"].rsplit("/", 1)[-1], set())
        return rec.base_read(item)

    def open_candidates(item: dict, read_docs: set[str]) -> int:
        """묶음 출발 문항에서 묶음 칸이 값을 말하지 않는 같은 회의의 CR(닫힌 세계 가정의 민감도)."""
        if item["family"] != "pack_origin":
            return 0
        meetings = {rec.documents[d].presented_at for d in read_docs if d in rec.documents}
        return sum(1 for d, doc in rec.documents.items() if d not in read_docs and doc.doc_type == "tdoc:CR"
                   and doc.presented_at in meetings and state(d) in ("nonPackText", "meetingWithoutColumn"))

    def describe(d: str) -> dict:
        doc = rec.documents.get(d)
        s = state(d)
        local = lambda packs_: sorted(p.rsplit("/", 1)[-1] for p in packs_)
        record = sorted(set(local(rec.in_packs.get(d, ()))) | set(local(rec.member_packs.get(d, ()))))
        alternative = [doc.pack_field] if s == "link" else [] if s in defined else None
        return {"state": s, "record": record, "alternative": alternative,
                "recordCrInPack": local(rec.in_packs.get(d, ())), "recordPackMember": local(rec.member_packs.get(d, ())),
                "packField": doc.pack_field if doc else None, "presentedAt": doc.presented_at if doc else None}

    categories = collections.Counter((pack_category(rec, doc), state(d)) for d, doc in rec.documents.items())
    diagnostics = {
        "documentStates": dict(collections.Counter(state(d) for d in rec.documents)),
        "valueMapping": "RP-<숫자> 칸은 묶음 tdoc:crpack/<번호>, '-' 와 회의에 칸이 있는 빈 칸은 묶음 없음, 그 밖의 글은 정의되지 않음",
        "packCategoryByState": [{"category": c, "state": s, "documents": n}
                                for (c, s), n in sorted(categories.items())],
        "packsAbsentFromPackRecords": len(new_packs), "meetingsWithColumn": len(column),
        "recordRowsLeftToFill": {"cr_in_pack": len(fill_in), "pack_member": len(fill_member)}}
    sub = Substitution("E4", {"cr_in_pack": links, "pack_member": list(links), "cr_pack": packs},
                       {"cr_in_pack": fill_in, "pack_member": fill_member}, state, defined, read, describe,
                       open_candidates)
    return sub, diagnostics


class ClauseResolver:
    """생성기 모듈의 절 해소 규칙을 그대로 부른다(RAN1~4 `parse_clauses_to_sections`, RAN5 `load_modifies_section`)."""

    def __init__(self, wg: str, module, index) -> None:
        self.wg, self.module, self.index = wg, module, index

    def resolve(self, tdoc_number: str, spec: str | None, clauses: str | None, release: str | None) -> set[str]:
        if self.wg == "RAN5":
            want: set[tuple[str, str]] = set()
            self.module.load_modifies_section(None, [{"tdoc_number": tdoc_number, "clauses_affected": clauses or "",
                                                      "spec_number": spec or "", "release": release}],
                                              self.index, want=want, write=False)
            return {"tdoc:section/" + sid for _, sid in want}
        return set(self.module.parse_clauses_to_sections(spec, clauses, self.index, release))


def load_generator(wg: str):
    spec = importlib.util.spec_from_file_location(f"generator_{wg}", GENERATOR[wg])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_section_index(wg: str, module, neo4j_wgs: set[str]):
    """생성기와 같은 절 색인. RAN1~3 은 phase-3 파일, RAN4·RAN5 는 Neo4j 읽기 전용 세션."""
    if wg in ("RAN1", "RAN2", "RAN3"):
        path = INSTANCES / f"phase-3/{wg}/release-aware/sections.jsonld"
        return module.load_phase3_sections(), {"source": str(path), "sha256": sha256_file(path)}
    if wg not in neo4j_wgs:
        return None, {"source": None, "skipped": f"--neo4j-section-wg 에 {wg} 가 없어 절 색인을 읽지 않았다"}
    uri = module.NEO4J_URI
    if uri.endswith(BUSY_BOLT_PORT):
        raise SystemExit(f"{wg} 절 색인 주소 {uri} 는 통합 중인 그래프라 읽지 않는다")
    from neo4j import READ_ACCESS, GraphDatabase
    query = "MATCH (s:Section)-[:BELONGS_TO_SPEC]->(:Spec) RETURN s.sectionId AS sid, s.sectionNumber AS num"
    driver = GraphDatabase.driver(uri, auth=(module.NEO4J_USER, module.NEO4J_PASSWORD))
    try:
        with driver.session(default_access_mode=READ_ACCESS) as session:
            if wg == "RAN5":
                index = module.load_section_index(session)
            else:
                entries = [(r["sid"], r["num"]) for r in session.run(query) if r["sid"] and r["num"] is not None]
                module.require_complete_section_index(wg, (sid for sid, _ in entries), f"{uri} {query}")
                index = module.SectionIndex(entries)
    finally:
        driver.close()
    return index, {"source": f"{uri} (읽기 전용 세션)", "query": query}


def index_digest(index) -> dict:
    keys = sorted(index.sid_by.items())
    return {"entries": len(keys), "sha256": hashlib.sha256(json.dumps(keys).encode()).hexdigest()}


def with_sections(rec: Records, section_ids) -> list[tuple]:
    extra = []
    for sid in sorted(set(section_ids) - set(rec.sections)):
        match = SECTION.match(sid)
        extra.append((sid, *(match.group("spec", "release", "clause") if match else (None, None, None))))
    return list(rec.rows["section"]) + extra


def clause_text(value) -> tuple[str | None, bool]:
    """목록의 절 칸을 글로 읽는다. 목록이면 쉼표로 잇는다. (글, 글이 아닌 값이 있었는지)."""
    parts, odd = [], False
    for entry in as_list(value):
        if isinstance(entry, str):
            parts.append(entry)
        else:
            odd = True
    text = ", ".join(parts)
    return (text if text.strip() else None), odd


E6_DEFINED = frozenset({"link", "noSection", "noListText-emptyCell"})


def substitute_e6(rec: Records, clauses: dict[str, object], resolver: ClauseResolver,
                  blank_defined: bool = True) -> tuple[Substitution, dict]:
    defined = E6_DEFINED if blank_defined else E6_DEFINED - {BLANK_STATES["E6"]}
    column = {rec.documents[d].presented_at for d in clauses}
    alt_changes: dict[str, set[str]] = {}
    texts: dict[str, str] = {}
    odd_values = 0
    for d, value in clauses.items():
        text, odd = clause_text(value)
        odd_values += odd
        if text is None:
            continue
        texts[d] = text
        doc = rec.documents[d]
        if doc.spec is not None:
            alt_changes[d] = resolver.resolve(doc.number, doc.spec, text, doc.target_release)

    def state(d: str) -> str:
        doc = rec.documents.get(d)
        if doc is None:
            return "notInDocumentList"
        if d in texts:
            if doc.spec is None:
                return "noSpec"
            return "link" if alt_changes[d] else "noSection"
        if d in clauses:
            return "noListText-emptyCell"
        if doc.presented_at is None:
            return "noListText-noPresentedAt"
        return "noListText-emptyCell" if doc.presented_at in column else "noListText-meetingWithoutColumn"

    table = [(d, sid) for d, sids in alt_changes.items() for sid in sorted(sids)]
    fill = [row for row in rec.rows["cr_modifies_section"] if state(row[0]) not in defined]
    alt_section_crs: dict[str, set[str]] = collections.defaultdict(set)
    for d, sid in table:
        alt_section_crs[sid].add(d)

    def read(item: dict) -> set[str]:
        if item["family"] == "clause_history":
            anchor = item["anchor"]
            return rec.release_matched(anchor, rec.section_crs.get(anchor, set()) | alt_section_crs.get(anchor, set()))
        return rec.base_read(item)

    def open_candidates(item: dict, read_docs: set[str]) -> int:
        """절 출발 문항에서 절 칸이 값을 말하지 않는 같은 규격·release 의 문서(닫힌 세계 가정의 민감도)."""
        if item["family"] != "clause_history":
            return 0
        section = rec.sections.get(item["anchor"])
        if section is None:
            return 0
        return sum(1 for d, doc in rec.documents.items() if d not in read_docs and doc.spec == section[1]
                   and doc.target_release == section[2] and state(d) not in defined)

    def describe(d: str) -> dict:
        s = state(d)
        short = lambda sids: sorted(x.rsplit("/", 1)[-1] for x in sids)
        alternative = short(alt_changes.get(d, ())) if s in defined else None
        doc = rec.documents.get(d)
        return {"state": s, "record": short(rec.changes.get(d, ())), "alternative": alternative,
                "listClauses": texts.get(d), "listSpec": doc.spec if doc else None,
                "listRelease": doc.target_release if doc else None, "presentedAt": doc.presented_at if doc else None}

    link_types = collections.Counter(rec.documents[d].doc_type for d, sids in alt_changes.items() if sids)
    diagnostics = {
        "documentStates": dict(collections.Counter(state(d) for d in rec.documents)),
        "valueMapping": "절 칸을 생성기의 해소 규칙으로 목록 자신의 규격·release 판 절에 잇는다",
        "linkDocumentsByType": dict(link_types), "nonTextClauseValues": odd_values,
        "meetingsWithColumn": len(column), "recordRowsLeftToFill": len(fill)}
    sections = with_sections(rec, (sid for _, sid in table))
    sub = Substitution("E6", {"cr_modifies_section": table, "section": sections}, {"cr_modifies_section": fill},
                       state, defined, read, describe, open_candidates)
    return sub, diagnostics


# --- 대조·재계산 ------------------------------------------------------------------------------------------

def shadow_controls(db: sqlite3.Connection, rec: Records, items: list[dict], baseline: dict[str, set]) -> dict:
    """가리기가 동작하는지: 같은 행으로 가리면 그대로, 빈 표로 가리면 행이 있던 결과가 모두 빈다."""
    report = {}
    for table in ("disposition", "resolution", "revision", "cr_in_pack", "pack_member", "cr_pack", "section",
                  "cr_modifies_section"):
        scope = [item for item in items if table in TABLES[item["family"]]]
        with Shadow(db, {table: list(rec.rows[table])}):
            same = sum(run(db, item) == baseline[item["id"]] for item in scope)
        with Shadow(db, {table: []}):
            emptied = sum(not run(db, item) for item in scope if baseline[item["id"]])
        report[table] = {"items": len(scope), "fullCopySameAsBaseline": same,
                         "nonEmptyBaseline": sum(bool(baseline[item["id"]]) for item in scope),
                         "emptyTableEmptiesResult": emptied}
    return report


def gate5_recheck(rec: Records, items: list[dict]) -> dict:
    """`verify_chain_items.py` 의 묶음 출처 일치 검사를 같은 DB 에서 다시 센다."""
    hits = []
    for item in items:
        family, anchor = item["family"], item["anchor"]
        if family == "revision_chain":
            considered = walk(anchor, rec.following)
        elif family == "clause_history":
            considered = rec.release_matched(anchor, rec.modified_by.get(anchor, ()))
        elif family == "pack_origin":
            considered = set(rec.pack_crs.get(anchor, ())) | rec.by_pack_field.get(anchor.rsplit("/", 1)[-1], set())
        else:
            considered = {anchor}
        bad = sorted(d for d in considered if d in rec.documents and GLOB_PACK.match(rec.documents[d].pack_field or "")
                     and "tdoc:crpack/" + rec.documents[d].pack_field not in rec.member_packs.get(d, ()))
        if bad:
            hits.append({"id": item["id"], "documents": bad[:DOCUMENT_CAP]})
    return {"items": len(items), "itemsWithDifferingPackSources": len(hits), "hits": hits}


def cross_source(rec: Records) -> dict:
    """처분 기록과 목록 상태의 일치(`measure_cross_source_agreement.py` 의 allDocuments 셈)를 DB 에서 다시 센다."""
    compared = agree = silent = absent = 0
    for target, codes in rec.codes.items():
        doc = rec.documents.get(target)
        if doc is None or doc.list_status is None:
            absent += 1
            continue
        status = canonical(doc.list_status)
        if status in LIST_WITHOUT_DISPOSITION:
            silent += 1
            continue
        compared += 1
        agree += status in {canonical(c) for c in codes}
    return {"listWithoutDisposition": silent, "compared": compared, "agree": agree,
            "differences": compared - agree, "targetsAbsentFromTdocList": absent}


def empty_gold_supplement(rec: Records, items: list[dict]) -> dict:
    """빈 정답 문항의 근거(처분이 묶음 없는 닫힘 코드)를 목록 상태로 바꾸어도 서는지 본다."""
    rows = []
    for item in items:
        if item["family"] != "pack_lookup_empty":
            continue
        doc = rec.documents.get(item["anchor"])
        kind, code = list_code(doc.list_status if doc else None)
        rows.append({"id": item["id"], "listStatus": doc.list_status if doc else None, "kind": kind, "code": code,
                     "listCodeClosedWithoutPack": code in CLOSED_WITHOUT_PACK,
                     "recordCodes": sorted(rec.all_codes.get(item["anchor"], ())),
                     "verifiedRecordCodes": sorted(rec.codes.get(item["anchor"], ()))})
    summary = collections.Counter("closedWithoutPack" if r["listCodeClosedWithoutPack"] else
                                  f"{r['kind']}:{r['code']}" if r["code"] else r["kind"] for r in rows)
    return {"items": len(rows), "byListCode": dict(sorted(summary.items())), "rows": rows}


# --- 모으기 --------------------------------------------------------------------------------------------

def empty_cell() -> dict:
    return {"evaluated": 0, "unchanged": 0, "changed": 0, "undefined": 0, "excluded": 0,
            "changedKinds": collections.Counter(), "undefinedReasons": collections.Counter(),
            "changedAlsoUndefined": 0, "preIntegrationItems": 0, "subsetViolations": 0}


def aggregate(results: list[dict]) -> dict:
    cells = {"all": collections.defaultdict(empty_cell), "byWg": collections.defaultdict(empty_cell),
             "byFamily": collections.defaultdict(empty_cell), "byWgFamily": collections.defaultdict(empty_cell)}
    for r in results:
        for by, key in (("all", "all"), ("byWg", r["wg"]), ("byFamily", r["family"]),
                        ("byWgFamily", f"{r['wg']}/{r['family']}")):
            cell = cells[by][key]
            if r["outcome"] == "excluded":
                cell["excluded"] += 1
                continue
            cell["evaluated"] += 1
            cell[r["outcome"]] += 1
            cell["preIntegrationItems"] += r["preIntegration"]
            cell["subsetViolations"] += r["subsetViolation"]
            if r["outcome"] == "changed":
                cell["changedKinds"][r["detail"]] += 1
                cell["changedAlsoUndefined"] += r["alsoUndefined"]
            elif r["outcome"] == "undefined":
                cell["undefinedReasons"][r["detail"]] += 1
    out = {}
    for by, group in cells.items():
        out[by] = {key: {name: dict(sorted(value.items())) if isinstance(value, collections.Counter) else value
                         for name, value in cell.items()} for key, cell in sorted(group.items())}
    out["all"] = out["all"].get("all", empty_cell() | {"changedKinds": {}, "undefinedReasons": {}})
    return out


def pick_examples(results: list[dict]) -> list[dict]:
    """바뀐 문항을 먼저, 그다음 정의되지 않은 문항을 고른다. 작업반·종류가 겹치지 않게 고르고 통합 전 표시가 없는 것을 앞세운다."""
    pool = [r for r in results if r["outcome"] in ("changed", "undefined") and "_example" in r]
    chosen: list[dict] = []
    while pool and len(chosen) < EXAMPLES:
        wgs, families = {r["wg"] for r in chosen}, {r["family"] for r in chosen}
        best = min(pool, key=lambda r: (r["outcome"] != "changed", -((r["wg"] not in wgs) + (r["family"] not in families)),
                                        r["preIntegration"], r["id"]))
        pool.remove(best)
        chosen.append(best)
    return [{key: value for key, value in r.items() if key != "_example"} | r["_example"] for r in chosen]


# --- 작업반 하나 ----------------------------------------------------------------------------------------

def read_list_columns(wg: str, manifest_inputs: list[dict]) -> tuple[dict, dict, dict]:
    """목록 파일에서 `revisedTo`·`isRevisionOf`·`tdoc:clausesAffected` 칸을 읽는다. 읽은 바이트가 내보낼 때의
    파일과 같은지 본다. `isRevisionOf` 는 개정 기록과 같은 칸인지 대조하는 데만 쓴다."""
    entry = next(e for e in manifest_inputs if e["path"].endswith(f"phase-1/{wg}/tdocs.jsonld"))
    data = Path(entry["path"]).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    graph = json.loads(data)["@graph"]
    del data
    revised, clauses, ids, inverse = {}, {}, set(), set()
    for record in graph:
        if "tdoc:tdocNumber" not in record:
            continue
        ids.add(record["@id"])
        if "revisedTo" in record:
            revised[record["@id"]] = record["revisedTo"]
        inverse.update((earlier, record["@id"]) for earlier in link_ids(record.get("isRevisionOf")))
        if "tdoc:clausesAffected" in record:
            clauses[record["@id"]] = record["tdoc:clausesAffected"]
    del graph
    gc.collect()
    check = {"path": entry["path"], "sha256": digest, "sameAsExport": digest == entry["sha256"]}
    return revised, clauses, {**check, "documentIds": ids, "inverseIsRevisionOf": inverse}


def measure_wg(wg: str, items: list[dict], db_path: Path, manifest: dict, args, memory: list) -> tuple[dict, dict]:
    require_memory(args.min_available_gib, f"{wg} DB 기록 읽기", memory)
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    db.execute("PRAGMA temp_store=MEMORY")
    rec = Records(db)
    pre = wg in set(args.pre_integration_wg or ())
    report: dict = {"preIntegration": pre}

    baseline = {item["id"]: run(db, item) for item in items}
    mismatches = [{"id": item["id"], "family": item["family"],
                   "onlyInGold": rows_out({tuple(r) for r in item["gold"]} - baseline[item["id"]]),
                   "onlyInRecomputation": rows_out(baseline[item["id"]] - {tuple(r) for r in item["gold"]})}
                  for item in items if baseline[item["id"]] != {tuple(r) for r in item["gold"]}]
    report["baseline"] = {"items": len(items), "reproduced": len(items) - len(mismatches), "mismatches": mismatches}
    kept = [item for item in items if item["id"] not in {m["id"] for m in mismatches}]
    excluded = {m["id"]: "baselineDiffersFromGold" for m in mismatches}

    report["shadowControls"] = shadow_controls(db, rec, items, baseline)
    report["gate5PackSources"] = gate5_recheck(rec, items)
    report["crossSourceFromDb"] = cross_source(rec)
    report["packCategoriesFromDb"] = dict(sorted(collections.Counter(
        pack_category(rec, doc) for doc in rec.documents.values()).items()))
    report["emptyGoldSupplement"] = empty_gold_supplement(rec, items)

    results: dict[str, list[dict]] = {}
    diagnostics: dict[str, dict] = {}

    def apply(sub: Substitution, families: set[str], skip: dict[str, str], label: str | None = None) -> None:
        scope = [item for item in items if item["family"] in families]
        todo = [item for item in scope if item["id"] not in excluded and item["id"] not in skip]
        out = evaluate(db, sub, todo, wg, pre)
        for item in scope:
            reason = excluded.get(item["id"]) or skip.get(item["id"])
            if reason:
                out.append({"id": item["id"], "wg": wg, "family": item["family"], "outcome": "excluded",
                            "detail": reason, "preIntegration": pre and item["family"] not in NO_DISPOSITION_FAMILIES})
        results[label or sub.name] = out

    for build, families in ((substitute_e1, FAMILIES["E1"]), (substitute_e2, FAMILIES["E2"]),
                            (substitute_e1e2, FAMILIES["E1E2"]), (substitute_e4, FAMILIES["E4"])):
        sub, diag = build(rec)
        diagnostics[sub.name] = diag
        apply(sub, families, {})
        if sub.name == "E1":
            states, cs = diag["verifiedTargetStates"], report["crossSourceFromDb"]
            identity = {
                "compared": sum(states.get(k, 0) for k in ("sameCode", "listCodeAmongRecordCodes", "differentCode",
                                                           "outsideCodeSet")) == cs["compared"],
                "agree": states.get("sameCode", 0) + states.get("listCodeAmongRecordCodes", 0) == cs["agree"],
                "listWithoutDisposition": states.get("listWithoutDisposition", 0) == cs["listWithoutDisposition"],
                "absent": states.get("notInDocumentList", 0) + states.get("noListStatus", 0)
                == cs["targetsAbsentFromTdocList"]}
            if not all(identity.values()):
                raise SystemExit(f"{wg} E1 상태 수가 처분·목록 일치 셈과 맞지 않는다: {identity}")
            diag["identityWithCrossSource"] = identity
        if sub.name == "E4":
            del sub
            sub, _ = substitute_e4(rec, blank_defined=False)
            apply(sub, families, {}, "E4:blankCellUndefined")
        del sub
        gc.collect()

    require_memory(args.min_available_gib, f"{wg} 목록 칸 읽기", memory)
    revised, clauses, list_check = read_list_columns(wg, manifest["inputs"])
    ids = list_check.pop("documentIds")
    inverse = list_check.pop("inverseIsRevisionOf")
    record_pairs = set(rec.rows["revision"])
    list_check["revisionRecordAgainstIsRevisionOf"] = {
        "recordPairs": len(record_pairs), "inverseIsRevisionOfPairs": len(inverse),
        "same": record_pairs == inverse, "recordOnly": len(record_pairs - inverse),
        "isRevisionOfOnly": len(inverse - record_pairs)}
    del inverse, record_pairs
    list_check["sameDocumentsAsDb"] = ids == set(rec.documents)
    report["listColumns"] = list_check
    if list_check["sameAsExport"] and list_check["sameDocumentsAsDb"]:
        sub, diag = substitute_e3(rec, revised)
        diagnostics["E3"] = diag
        apply(sub, FAMILIES["E3"], {})
        sub, _ = substitute_e3(rec, revised, blank_defined=False)
        apply(sub, FAMILIES["E3"], {}, "E3:blankCellUndefined")
    else:
        diagnostics["E3"] = {"skipped": "목록 파일이 내보낼 때와 달라 칸을 바꿔 끼울 수 없다"}
    del revised

    require_memory(args.min_available_gib, f"{wg} 표지·절 색인 읽기", memory)
    cover_path = PARSED / wg / "cr_documents.json"
    cover_data = json.loads(cover_path.read_text())
    cover = cover_data.get("cr_documents", cover_data.get("documents"))
    del cover_data
    module = load_generator(wg)
    index, index_source = load_section_index(wg, module, set(args.neo4j_section_wg or ()))
    report["sectionIndex"] = index_source | ({**index_digest(index)} if index is not None else {})
    report["cover"] = {"path": str(cover_path), "sha256": sha256_file(cover_path), "entries": len(cover),
                       "entriesWithoutClauses": sum(1 for c in cover if not c.get("clauses_affected"))}
    if index is None or not list_check["sameAsExport"] or not list_check["sameDocumentsAsDb"]:
        diagnostics["E6"] = {"skipped": index_source.get("skipped") or "목록 파일이 내보낼 때와 다르다"}
    else:
        resolver = ClauseResolver(wg, module, index)
        control: dict[str, set[str]] = collections.defaultdict(set)
        cover_context: dict[str, set[tuple]] = collections.defaultdict(set)
        for entry in cover:
            if not entry.get("tdoc_number"):
                continue
            cr = "tdoc:" + entry["tdoc_number"]
            control[cr] |= resolver.resolve(entry["tdoc_number"], entry.get("spec_number"),
                                            entry.get("clauses_affected"), entry.get("release"))
            spec = entry.get("spec_number")
            if wg == "RAN5" and spec:
                spec = module.normalize_spec_number(spec)
            cover_context[cr].add((spec, entry.get("release")))
        control_rows = [(cr, sid) for cr, sids in control.items() for sid in sorted(sids)]
        control_rows += [row for row in rec.rows["cr_modifies_section"] if row[0] not in control]
        drift = sorted(cr for cr in control if control[cr] != rec.changes.get(cr, set()))
        scope = [item for item in kept if item["family"] in FAMILIES["E6"]]
        with Shadow(db, {"cr_modifies_section": control_rows,
                         "section": with_sections(rec, (sid for _, sid in control_rows))}):
            drift_items = {item["id"]: run(db, item) for item in scope}
        skip = {item["id"]: "resolverDrift" for item in scope
                if drift_items[item["id"]] != {tuple(r) for r in item["gold"]}}
        sub, diag = substitute_e6(rec, clauses, resolver)
        context_differs = [cr for cr, contexts in cover_context.items() if cr in rec.documents
                           and (rec.documents[cr].spec, rec.documents[cr].target_release) not in contexts]
        diag["resolverControl"] = {
            "coveredCrs": len(control), "coveredCrsWhoseReresolvedSectionsDifferFromRecord": len(drift),
            "examples": drift[:DOCUMENT_CAP], "itemsExcludedForResolverDrift": sorted(skip)}
        diag["coveredCrsWhoseListSpecOrReleaseDiffersFromCover"] = len(context_differs)
        diagnostics["E6"] = diag
        apply(sub, FAMILIES["E6"], skip)
        sub, _ = substitute_e6(rec, clauses, resolver, blank_defined=False)
        apply(sub, FAMILIES["E6"], skip, "E6:blankCellUndefined")
    del clauses, cover, module, index
    db.close()
    del rec
    gc.collect()
    report["substitutionDiagnostics"] = diagnostics
    return report, results


FAMILIES = {
    "E1": {f for f, t in TABLES.items() if "disposition" in t},
    "E2": {f for f, t in TABLES.items() if "meeting" in t},
    "E1E2": {f for f, t in TABLES.items() if "disposition" in t},
    "E3": {f for f, t in TABLES.items() if "revision" in t},
    "E4": {f for f, t in TABLES.items() if t & {"cr_in_pack", "pack_member"}},
    "E6": {f for f, t in TABLES.items() if "cr_modifies_section" in t},
}
ELEMENTS = {
    "E1": {"element": "WG 처분 코드", "recordSource": "회의 보고서 처분 기록(disposition.code)",
           "alternativeSource": "TDoc 목록 상태(document.list_status)", "tablesReplaced": ["disposition"]},
    "E2": {"element": "결정 회의", "recordSource": "처분 기록의 결의가 내려진 회의(resolution.meeting_id)",
           "alternativeSource": "TDoc 목록의 발표 회의(document.presented_at)",
           "tablesReplaced": ["disposition", "resolution"]},
    "E1E2": {"element": "처분 기록 전체(코드와 회의)", "recordSource": "회의 보고서 처분 기록",
             "alternativeSource": "TDoc 목록 한 줄(list_status, presented_at)",
             "tablesReplaced": ["disposition", "resolution"]},
    "E3": {"element": "개정 연결", "recordSource": "TDoc 목록의 isRevisionOf(뒤 문서 칸, revision 표)",
           "alternativeSource": "TDoc 목록의 revisedTo(앞 문서 칸)", "tablesReplaced": ["revision"]},
    "E4": {"element": "CR 의 TSG 묶음 소속", "recordSource": "묶음 표지 기록(cr_in_pack, pack_member)",
           "alternativeSource": "TDoc 목록의 묶음 번호(document.pack_field)",
           "tablesReplaced": ["cr_in_pack", "pack_member", "cr_pack"]},
    "E6": {"element": "CR 이 고친 절", "recordSource": "CR 표지의 Clauses affected 를 해소한 기록(cr_modifies_section)",
           "alternativeSource": "TDoc 목록의 tdoc:clausesAffected 를 같은 규칙으로 해소",
           "tablesReplaced": ["cr_modifies_section", "section"]},
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--db-dir", type=Path, required=True)
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=LOGS / "relational_equivalence/export_manifest.json")
    parser.add_argument("--pack-agreement", type=Path, nargs="+",
                        default=[LOGS / "pack_source_agreement.json", LOGS / "pack_source_agreement_RAN5.json"])
    parser.add_argument("--cross-source", type=Path, default=LOGS / "cross_source_agreement.json")
    # 작업 지시의 하한: 가용 메모리가 8 GiB 아래면 무거운 단계를 시작하지 않는다.
    parser.add_argument("--min-available-gib", type=float, default=8.0)
    parser.add_argument("--neo4j-section-wg", nargs="*", default=[])
    parser.add_argument("--pre-integration-wg", nargs="*", default=[])
    parser.add_argument("--wg", nargs="*", help="이 작업반만 잰다(시험용)")
    args = parser.parse_args()

    memory: list[dict] = []
    items_by_wg: dict[str, list[dict]] = collections.defaultdict(list)
    item_files = []
    for path in args.items:
        loaded = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        item_files.append({"path": str(path), "items": len(loaded), "sha256": sha256_file(path),
                           "byWg": dict(sorted(collections.Counter(i["wg"] for i in loaded).items()))})
        for item in loaded:
            items_by_wg[item["wg"]].append(item)
    wgs = sorted(w for w in items_by_wg if not args.wg or w in args.wg)
    manifest = json.loads(args.manifest.read_text())
    source_changed = {}
    for wg in wgs:
        changed = [entry["path"] for entry in manifest["exports"][wg]["inputs"]
                   if not Path(entry["path"]).exists() or sha256_file(Path(entry["path"])) != entry["sha256"]]
        source_changed[wg] = changed

    per_wg, results = {}, collections.defaultdict(list)
    databases = {}
    for wg in wgs:
        db_path = args.db_dir / f"{wg}.sqlite"
        databases[wg] = {"path": str(db_path), "bytes": db_path.stat().st_size, "sha256": sha256_file(db_path),
                         "manifestTableRows": manifest["exports"][wg]["tableRows"]}
        report, wg_results = measure_wg(wg, items_by_wg[wg], db_path, manifest["exports"][wg], args, memory)
        per_wg[wg] = report
        for name, rows in wg_results.items():
            results[name].extend(rows)
        print(wg, "baseline", report["baseline"]["reproduced"], "/", report["baseline"]["items"],
              {name: collections.Counter(r["outcome"] for r in rows) for name, rows in wg_results.items()}, flush=True)

    # 지금의 인스턴스 파일로 다시 잰 처분·목록 일치. 설치가 진행 중이라 읽기 앞뒤의 해시를 함께 적는다.
    instance_now = {}
    for wg in wgs:
        require_memory(args.min_available_gib, f"{wg} 지금 인스턴스 처분·목록 일치", memory)
        paths = [INSTANCES / f"phase-1/{wg}/tdocs.jsonld", INSTANCES / f"phase-2/{wg}/decision_dispositions.jsonld"]
        before = {str(p): sha256_file(p) for p in paths}
        value = instance_cross_source(wg)["allDocuments"]
        after = {str(p): sha256_file(p) for p in paths}
        # 내보낸 처분 파일은 disposition_rebuild 아래 경로라 파일 이름으로 짝을 짓는다.
        exported = {Path(e["path"]).name: e for e in manifest["exports"][wg]["inputs"]}
        instance_now[wg] = {key: value[key] for key in ("listWithoutDisposition", "compared", "agree",
                                                         "targetsAbsentFromTdocList")} | {
            "differences": value["compared"] - value["agree"], "unchangedDuringRead": before == after,
            "inputs": [{"path": p, "sha256": h, "exportedPath": exported.get(Path(p).name, {}).get("path"),
                        "sameAsExport": exported.get(Path(p).name, {}).get("sha256") == h} for p, h in after.items()]}
        gc.collect()

    stored_cross = json.loads(args.cross_source.read_text())
    stored_pack = {row["wg"]: row for path in args.pack_agreement for row in json.loads(path.read_text())["byWg"]}
    reconciliation = {
        "storedCrossSource": {"path": str(args.cross_source), "byWg": {
            wg: {key: stored_cross[wg]["allDocuments"][key] for key in
                 ("listWithoutDisposition", "compared", "agree", "targetsAbsentFromTdocList")} for wg in stored_cross}},
        "storedPackAgreement": {"paths": [str(p) for p in args.pack_agreement], "byWg": {
            wg: {key: row[key] for key in ("same", "differentPack", "documentListOnly", "packRecordOnly", "neither")}
            for wg, row in sorted(stored_pack.items())}},
        "dbCrossSource": {wg: per_wg[wg]["crossSourceFromDb"] for wg in wgs},
        "dbPackCategories": {wg: per_wg[wg]["packCategoriesFromDb"] for wg in wgs},
        "instanceCrossSourceNow": instance_now}
    for label, table in (("storedCrossSource", reconciliation["storedCrossSource"]["byWg"]),
                         ("dbCrossSource", reconciliation["dbCrossSource"]),
                         ("instanceCrossSourceNow", instance_now)):
        compared = sum(row["compared"] for row in table.values())
        agree = sum(row["agree"] for row in table.values())
        reconciliation[label + "Total"] = {"compared": compared, "agree": agree, "differences": compared - agree}
    for label, table in (("storedPackAgreement", reconciliation["storedPackAgreement"]["byWg"]),
                         ("dbPackCategories", reconciliation["dbPackCategories"])):
        reconciliation[label + "RAN1to4"] = {key: sum(table.get(wg, {}).get(key, 0) for wg in
                                                      ("RAN1", "RAN2", "RAN3", "RAN4"))
                                             for key in ("documentListOnly", "differentPack", "packRecordOnly")}

    substitutions = {}
    for name in ("E1", "E2", "E1E2", "E3", "E4", "E6"):
        rows = results.get(name, [])
        substitutions[name] = {
            **ELEMENTS[name], "families": sorted(FAMILIES[name]), "counts": aggregate(rows),
            "diagnosticsByWg": {wg: per_wg[wg]["substitutionDiagnostics"].get(name) for wg in wgs},
            "examples": pick_examples(rows),
            "items": [{key: value for key, value in r.items() if key != "_example"} for r in rows]}
        variant = name + ":blankCellUndefined"
        if variant in results:
            substitutions[name]["blankCellUndefined"] = {
                "meaning": f"칸이 있는 회의에서 빈 칸({BLANK_STATES[name]})을 '없음'으로 읽지 않고 정의되지 않은 "
                           "것으로 볼 때의 같은 셈",
                "counts": aggregate(results[variant]), "examples": pick_examples(results[variant])}
    report = {
        "description": __doc__.split("\n")[0],
        "unit": "문항. 한 문항은 대체 하나에서 unchanged·changed·undefined 가운데 하나이고, "
                "대체가 읽는 테이블을 쓰지 않는 종류의 문항은 그 대체에서 세지 않는다",
        "excluded": "바꾸기 전 재계산이 정답과 다른 문항(baselineDiffersFromGold), E6 에서 표지 절 칸을 지금의 해소 "
                    "규칙으로 다시 이은 결과가 정답과 다른 문항(resolverDrift). E5(묶음의 TSG 회의)는 묶음 기록 밖에 "
                    "같은 사실을 적은 출처가 없어 바꾸지 않는다",
        "records": "DB 는 export_chain_records_sqlite.py 가 내보낸 파일을 읽기 전용으로 그대로 쓴다. RAN1~4 DB 는 "
                   "다시 지은 처분 기록(disposition_rebuild)을 이미 담고 있다",
        "preIntegration": {"wgs": sorted(args.pre_integration_wg or ()),
                           "meaning": "이 작업반 문항 가운데 처분 테이블을 읽는 문항의 결과는 그래프 통합 전 처분 기록에 "
                                      "기댄다. 통합이 끝나면 다시 잰다"},
        "codeMapping": {"same": SAME, "listWithoutDisposition": sorted(LIST_WITHOUT_DISPOSITION),
                        "closedCodes": sorted(CODES), "closedWithoutPack": list(CLOSED_WITHOUT_PACK),
                        "rule": "목록 상태를 소문자로 바꾸고 밑줄을 공백으로 맞춘 뒤 same 표로 옮기고, 공백을 밑줄로 "
                                "바꾼 값이 닫힌 코드에 있으면 그 코드, 없으면 outsideCodeSet 이다"},
        "queries": {family: {"sql": " ".join(sql.split()), "tables": sorted(TABLES[family])}
                    for family, sql in QUERIES.items()},
        "inputs": {"itemFiles": item_files, "databases": databases,
                   "manifest": {"path": str(args.manifest), "sha256": sha256_file(args.manifest)},
                   "exportInputsChangedSince": source_changed},
        "memoryChecks": memory,
        "byWg": {wg: {key: value for key, value in per_wg[wg].items() if key != "substitutionDiagnostics"}
                 for wg in wgs},
        "reconciliation": reconciliation,
        "substitutions": substitutions}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1, default=sorted) + "\n")
    for name, sub in substitutions.items():
        for label, counts in ((name, sub["counts"]),
                              (name + ":blankCellUndefined", sub.get("blankCellUndefined", {}).get("counts"))):
            if counts is None:
                continue
            cell = counts["all"]
            print(label, {key: cell[key] for key in ("evaluated", "unchanged", "changed", "undefined", "excluded")},
                  cell["changedKinds"], cell["undefinedReasons"])


if __name__ == "__main__":
    main()
