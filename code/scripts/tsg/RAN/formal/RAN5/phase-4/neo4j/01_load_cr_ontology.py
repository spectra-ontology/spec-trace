#!/usr/bin/env python3
"""
RAN5 Phase-4: Load CR ontology into Neo4j (port 7691).

Input: ontology/output/tsg/RAN/formal/parsed_cr/RAN5/ (cr_documents.json, crpacks.json)
Output: neo4j-tdoc-ran5 (bolt://localhost:7691)

이 적재기가 만드는 것(CRPack 노드 · BELONGS_TO_CR_PACK/HAS_CR · AFFECTS_*_SPEC ·
CR 발 MODIFIES_SECTION/MODIFIED_BY_CR · `_createdBy='phase-4-backfill'` CR 노드 · CR 의
CR-Form 속성 reasonForChange/summaryOfChange/consequencesIfNotApproved)은 이 적재기
말고 만드는 자리가 없다. 그래서 적재 뒤 KG 의 그 부분을 입력 JSON 과 같게 맞춘다(reconcile) —
MERGE 만 하면 옛 파싱이 남긴 간선이 영영 남아 KG 가 현재 생성 코드 산출의 함수가 아니게 된다.
`--dry-run` 은 쓰지 않고 흡수·삭제할 것만 센다.

backfill CR 노드에는 Phase-1 의 신원(`:Tdoc` 라벨 · `id`)이 없어, 뒤에 Phase-1 이 같은 tdocNumber 의
Tdoc 을 적재하면 `MERGE (t:Tdoc {id})` 가 이 노드를 못 찾고 둘째 노드를 만든다. 그러면
`MERGE (cr:CR {tdocNumber})` 가 둘을 함께 잡아 간선·속성이 두 벌이 된다. 적재 전에 그런 backfill
노드를 Tdoc 쪽으로 흡수한다 — 다른 생성 코드의 간선(Email 층 ANCHORS 등)은 짝으로 옮기고(대상
tdocNumber 가 같으므로 뜻이 그대로다) 소유 간선·속성은 이번 적재가 짝 위에 다시 쓴다.

AFFECTS_*_SPEC 은 release-blind 인 허브 Spec(`specRelease IS NULL`)에만 단다. `specNumber` 로만
MATCH 하면 같은 번호의 release-키 Spec 변형에도 모두 붙어, CR 이 적지 않은 release 를 고쳤다는
거짓 간선이 된다. 정합화는 허브가 아닌 Spec 으로 간 이 간선을 입력과 무관하게 지운다.

Phase-1 입력에 없는 CR 은 backfill 노드로 서서, Phase-1 이 Tdoc List 에서 채우는 제목과
MODIFIES(→ Spec) · RELATED_TO(→ WorkItem) 간선이 없다. 그 CR 에는 `cr_documents.json` 의 CR 서식 값
(title · spec_number · work_item)으로 셋을 채운다(`cr_backfill_form`). Phase-1 노드의 값은 덮어쓰지
않고, 채운 제목에는 `titleSource='cr-form'`, 단 간선에는 `_createdBy='phase-4-backfill'` 를 적는다.
대상 Spec · WorkItem 노드가 없으면 만들지 않고 센다.
"""

import argparse

import json
import os
import re
import sys
import time
from pathlib import Path
from neo4j import GraphDatabase

PROJECT_ROOT = Path(__file__).resolve().parents[7]

# 자격증명의 정본은 저장소 루트의 `.env` 한 벌이고, 그것을 읽는 자리도 한 곳이다.
# 자리마다 평문 대신값을 두면 그 대신값이 곧 두 번째 정본이 되어 정본이 갈린다.
_SCRIPTS_COMMON = PROJECT_ROOT / "scripts" / "common"
if str(_SCRIPTS_COMMON) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_COMMON))
from common import credentials, axis  # noqa: E402

# 「Clauses affected」 칸을 읽는 규칙은 5 WG 가 한 벌을 쓴다 — WG 마다 정리기가 따로 있으면
# 같은 칸이 WG 마다 다른 절로 해소된다.
_FORMAL_COMMON = PROJECT_ROOT / "scripts" / "tsg" / "RAN" / "formal" / "common"
if str(_FORMAL_COMMON) not in sys.path:
    sys.path.append(str(_FORMAL_COMMON))
from cr_clause import clause_candidates  # noqa: E402
from cr_backfill_form import fill_backfill_form, reconcile_backfill_form  # noqa: E402
from cr_number_sheet import REPORT_NAME, reconcile_cr_numbers  # noqa: E402
from section_index_guard import require_complete_section_index  # noqa: E402
sys.path.insert(0, str(_FORMAL_COMMON / "phase-4"))
from cr_section_index import SectionIndex, _REL_NUM_RE, rel_num  # noqa: E402

PARSED_DIR = PROJECT_ROOT / "ontology" / "output" / "tsg" / "RAN" / "formal" / "parsed_cr" / "RAN5"

from common.operation_targets import child_neo4j_uri  # noqa: E402

NEO4J_URI = child_neo4j_uri("RAN5", axis.bolt_uri("RAN5"))
CRNUMBER_REPORT = axis.tree_path("logs", wg="RAN5", phase=4) / REPORT_NAME
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = credentials.neo4j_password()

BATCH_SIZE = 500


def normalize_spec_number(raw: str) -> str:
    """38521-1 → 38.521-1, 38533 → 38.533"""
    if not raw:
        return raw
    raw = raw.strip().replace(" ", "")
    if "." in raw:
        return raw
    # 5+ digits without dot: insert dot after position 2
    m = re.match(r'^(\d{2})(\d{3})(.*)', raw)
    if m:
        return f"{m.group(1)}.{m.group(2)}{m.group(3)}"
    return raw


def _input_graph(data, label):
    """빈 목록과 잘못된 JSON-LD 구조를 구분한다."""
    if not isinstance(data, dict) or not isinstance(data.get("@graph"), list):
        raise ValueError(f"{label}: @graph 목록이 필요합니다")
    graph = data["@graph"]
    if any(not isinstance(row, dict) for row in graph):
        raise ValueError(f"{label}: 각 항목은 객체여야 합니다")
    return graph


def _input_rows(rows, label):
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"{label}: 객체 목록이 필요합니다")
    return rows


def _input_text(value, label, allow_none=False):
    if allow_none and value is None:
        return
    if not isinstance(value, str):
        raise ValueError(f"{label}: 문자열이 필요합니다")


def _input_key(value, label):
    """노드를 가르는 키. 빠졌거나 빈 문자열이면 정합화가 그 키로 입력 밖을 가를 수 없다."""
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label}: 빈 문자열이 아닌 키가 필요합니다")


def _input_refs(value, label, allow_none=False):
    if allow_none and value is None:
        return
    values = [value] if isinstance(value, str) else value
    if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
        raise ValueError(f"{label}: 문자열 또는 문자열 목록이 필요합니다")


def _input_property(value, label):
    """기존 nullable/scalar 속성을 보존하고 JSON 객체·중첩 목록을 거부한다."""
    scalar = (str, int, float, bool)
    if value is None or isinstance(value, scalar):
        return
    if isinstance(value, list) and all(isinstance(v, scalar) for v in value):
        return
    raise ValueError(f"{label}: 스칼라 속성 또는 스칼라 목록이 필요합니다")


def _input_records(data, key):
    if not isinstance(data, dict) or not isinstance(data.get(key), list):
        raise ValueError(f"{key}: 목록이 필요합니다")
    rows = data[key]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"{key}: 각 항목은 객체여야 합니다")
    return rows


def _accept_cr_inputs(packs, docs):
    _input_rows(packs, "packs")
    _input_rows(docs, "documents")
    # 정합화는 이 두 목록 밖의 팩 · 소속 간선 · CR-Form 속성 · backfill CR · 동적 Spec 을 지운다. 빈 목록을
    # 정상 입력으로 받으면 이 적재기가 소유한 것이 모두 지워진다. Spec 은 CRPack 마다 hasCR 1..* 이고 CR 확장
    # 수가 0 이 아니라(Appendix P4-V02 · P4-V03) 빈 목록은 입력이 망가진 것이다.
    for rows, label in ((packs, "packs"), (docs, "documents")):
        if not rows:
            raise ValueError(f"{label}: 빈 목록이라 정합화가 소유 노드를 모두 지웁니다")
    for pack in packs:
        _input_key(pack.get("crPackId"), "crPackId")
        _input_refs(pack.get("tdocNumbers", []), "tdocNumbers")
        _input_property(pack.get("tsgMeeting"), "tsgMeeting")
    for doc in docs:
        _input_key(doc.get("tdoc_number"), "tdoc_number")
        for field, _ in CROSS_SPEC_FIELDS:
            values = doc.get(field)
            if not values:
                continue
            if not isinstance(values, list):
                raise ValueError(f"{field}: 목록이 필요합니다")
            for value in values:
                if value:
                    _input_text(value, field)
        clauses = doc.get("clauses_affected", "")
        if clauses:
            _input_text(clauses, "clauses_affected")
            if clauses.strip():
                if doc.get("spec_number"):
                    _input_text(doc["spec_number"], "spec_number")
                    if doc.get("release"):
                        _input_text(doc["release"], "release")
        for field in ("reason_for_change", "summary_of_change", "consequences_if_not_approved"):
            _input_property(doc.get(field), field)


def load_json(filename: str) -> dict:
    path = PARSED_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_indexes(session):
    for q in [
        "CREATE INDEX IF NOT EXISTS FOR (p:CRPack) ON (p.crPackId)",
    ]:
        session.run(q)
    print("  Indexes created")


def load_crpacks(session, packs: list[dict]) -> int:
    count = 0
    for i in range(0, len(packs), BATCH_SIZE):
        batch = [
            {"crPackId": p["crPackId"], "tsgMeeting": p.get("tsgMeeting")}
            for p in packs[i:i + BATCH_SIZE]
        ]
        r = session.run("""
            UNWIND $batch AS p
            MERGE (pack:CRPack {crPackId: p.crPackId})
            SET pack.tsgMeeting = p.tsgMeeting
            RETURN count(pack) AS cnt
        """, batch=batch)
        count += r.single()["cnt"]
    return count


def ensure_cr_labels(session, docs: list[dict]) -> int:
    """Phase-1 이 :CR 로 분류하지 않은 입력 CR 의 Tdoc 에 :CR 레이블을 붙인다.

    Phase-1 @type 분류에서 일부 CR 이 'tdoc:Tdoc' 으로만 분류되면 :CR 레이블이 없어,
    `MERGE (cr:CR {tdocNumber})` 가 그 Tdoc 을 못 찾고 같은 문서의 backfill 노드를 따로 만든다.
    그래서 흡수·속성 확장 전에 입력 기준으로 레이블을 붙인다.
    """
    result = session.run(
        """
        UNWIND $tdocs AS num
        MATCH (t:Tdoc {tdocNumber: num})
        WHERE NOT t:CR
        SET t:CR
        RETURN count(t) AS cnt
        """,
        tdocs=[d["tdoc_number"] for d in docs],
    )
    fixed = result.single()["cnt"]
    if fixed > 0:
        print(f"  [ensure_cr_labels] {fixed}개 Tdoc에 :CR 레이블 추가")
    return fixed


def load_cr_extensions(session, docs: list[dict]) -> int:
    count = 0
    for i in range(0, len(docs), BATCH_SIZE):
        batch = [
            {
                "tdoc": d["tdoc_number"],
                "reason": d.get("reason_for_change"),
                "summary": d.get("summary_of_change"),
                "consequences": d.get("consequences_if_not_approved"),
            }
            for d in docs[i:i + BATCH_SIZE]
        ]
        # MATCH 가 아니라 MERGE 다. Phase-1 Tdoc List 가 다루지 않는 CR 은 Phase-1 노드가 없어,
        # MATCH 면 그 CR 의 속성·간선이 말없이 빠진다. 없는 CR 은 backfill 노드로 만든다.
        r = session.run("""
            UNWIND $batch AS d
            MERGE (cr:CR {tdocNumber: d.tdoc})
            ON CREATE SET cr._createdBy = 'phase-4-backfill'
            SET cr.reasonForChange = d.reason,
                cr.summaryOfChange = d.summary,
                cr.consequencesIfNotApproved = d.consequences
            RETURN count(cr) AS cnt
        """, batch=batch)
        count += r.single()["cnt"]
    return count


def load_crpack_relationships(session, packs: list[dict]) -> int:
    count = 0
    for pack in packs:
        if not pack.get("tdocNumbers"):
            continue
        for i in range(0, len(pack["tdocNumbers"]), BATCH_SIZE):
            batch = pack["tdocNumbers"][i:i + BATCH_SIZE]
            r = session.run("""
                MATCH (pack:CRPack {crPackId: $packId})
                UNWIND $tdocs AS tdoc
                MATCH (cr:CR {tdocNumber: tdoc})
                MERGE (cr)-[:BELONGS_TO_CR_PACK]->(pack)
                MERGE (pack)-[:HAS_CR]->(cr)
                RETURN count(*) AS cnt
            """, packId=pack["crPackId"], tdocs=batch)
            count += r.single()["cnt"]
    return count


CROSS_SPEC_FIELDS = [
    ("affects_core_spec", "AFFECTS_CORE_SPEC"),
    ("affects_test_spec", "AFFECTS_TEST_SPEC"),
    ("affects_om_spec", "AFFECTS_OM_SPEC"),
]


def desired_cross_spec(docs: list[dict]) -> set[tuple[str, str, str]]:
    """(tdocNumber, 관계 타입, specNumber) — 입력이 요구하는 교차 spec 간선 전부."""
    want = set()
    for d in docs:
        for field, rel_type in CROSS_SPEC_FIELDS:
            for s in d.get(field) or []:
                if s:
                    want.add((d["tdoc_number"], rel_type, normalize_spec_number(s)))
    return want


def load_cross_spec(session, docs: list[dict]) -> tuple[int, int, int, int]:
    counts = {rel_type: 0 for _, rel_type in CROSS_SPEC_FIELDS}
    dyn_cnt = 0

    all_cross_specs = {sn for _, _, sn in desired_cross_spec(docs)}

    # 동적 Spec 생성 (Neo4j에 없는 것만). 이번 실행에 새로 만든 수만 센다 — `_dynamic` 은
    # 앞선 실행이 만든 노드에도 남아 있어 그 값을 세면 누적 수가 된다.
    # 허브는 Phase-1 loader(`MERGE (s:Spec {id: item['@id']})`)와 같은 `id` 를 갖고 태어난다.
    # id 가 없으면 뒤에 그 번호가 Phase-1 목록에 들어올 때 Phase-1 이 이 허브를 못 찾고 둘째
    # 허브를 만들어 간선이 두 노드로 갈린다. 앞선 실행이 id 없이 만든 허브에는 먼저 id 를 붙인다.
    if all_cross_specs:
        hub_ids = [{"specNumber": sn, "specId": f"tdoc:spec/{sn.replace('.', '_')}"}
                   for sn in sorted(all_cross_specs)]
        session.run("""
            UNWIND $batch AS s
            MATCH (h:Spec {specNumber: s.specNumber})
              WHERE h.specRelease IS NULL AND h.id IS NULL
                AND NOT EXISTS { MATCH (:Spec {id: s.specId}) }
            WITH s, head(collect(h)) AS h
            SET h.id = s.specId
        """, batch=hub_ids)
        existing = {
            r["sn"] for r in session.run(
                "MATCH (sp:Spec) WHERE sp.specNumber IN $sns AND sp.specRelease IS NULL "
                "RETURN sp.specNumber AS sn",
                sns=sorted(all_cross_specs),
            )
        }
        for spec in sorted(all_cross_specs - existing):
            session.run("CREATE (sp:Spec {id: $id, specNumber: $sn, _dynamic: true})",
                        id=f"tdoc:spec/{spec.replace('.', '_')}", sn=spec)
            dyn_cnt += 1

    # Cross-Spec 관계 생성
    for d in docs:
        tdoc = d["tdoc_number"]
        for field, rel_type in CROSS_SPEC_FIELDS:
            specs = d.get(field, [])
            if not specs:
                continue
            normalized = [normalize_spec_number(s) for s in specs if s]
            if not normalized:
                continue
            r = session.run(f"""
                MATCH (cr:CR {{tdocNumber: $tdoc}})
                UNWIND $specs AS sn
                MATCH (sp:Spec {{specNumber: sn}}) WHERE sp.specRelease IS NULL
                MERGE (cr)-[:{rel_type}]->(sp)
                RETURN count(*) AS cnt
            """, tdoc=tdoc, specs=normalized)
            counts[rel_type] += r.single()["cnt"]

    return (counts["AFFECTS_CORE_SPEC"], counts["AFFECTS_TEST_SPEC"],
            counts["AFFECTS_OM_SPEC"], dyn_cnt)








def load_section_index(session) -> SectionIndex:
    """Neo4j Section(release-키)에서 SectionIndex 구성."""
    result = session.run(
        # Phase-3 가 적재한 절만 과녁이다(BELONGS_TO_SPEC 은 그 적재기만 긋는다). 입력에서 빠졌는데
        # 남의 간선 때문에 보존된 노드까지 읽으면 CR 이 그 노드를 다시 과녁으로 삼아 스스로를 살린다.
        "MATCH (s:Section)-[:BELONGS_TO_SPEC]->(:Spec) RETURN s.sectionId AS sid, s.sectionNumber AS num"
    )
    entries = [
        (record["sid"], record["num"])
        for record in result
        if record["sid"] and record["num"] is not None
    ]
    # 비었거나 일부만 적재된 그래프면 CR 의 절 간선이 오류 없이 빠진다. Phase-3 파서의 절 수보다 적으면 멈춘다.
    require_complete_section_index("RAN5", (sid for sid, _ in entries),
                                   "Neo4j (:Section)-[:BELONGS_TO_SPEC]->(:Spec)")
    return SectionIndex(entries)


def load_modifies_section(session, docs: list[dict], section_index: SectionIndex,
                          want: set[tuple[str, str]] | None = None, write: bool = True) -> int:
    """clauses_affected → Section 간선. `want` 에 (tdocNumber, sectionId) 를 모은다."""
    count = 0
    for d in docs:
        clauses = d.get("clauses_affected", "")
        if not clauses or not clauses.strip():
            continue
        tdoc = d["tdoc_number"]
        spec_raw = d.get("spec_number", "")
        spec = normalize_spec_number(spec_raw)
        if not spec:
            continue

        release = d.get("release")
        section_ids = []
        for candidates in clause_candidates(clauses):
            for c in candidates:
                sid = section_index.resolve(spec, c, release)
                if sid:
                    section_ids.append(sid)
                    break

        # 서로 다른 clause 가 같은 Section 으로 해소될 수 있다(fallback). 중복을 두면 MERGE 는
        # 간선을 하나만 두지만 count(*) 는 행을 세어 적재 수가 KG 보다 커진다.
        section_ids = list(dict.fromkeys(section_ids))
        if not section_ids:
            continue
        if want is not None:
            want.update((tdoc, sid) for sid in section_ids)
        if not write:
            continue

        r = session.run("""
            MATCH (cr:CR {tdocNumber: $tdoc})
            UNWIND $sids AS sid
            MATCH (sec:Section {sectionId: sid})
            MERGE (cr)-[:MODIFIES_SECTION]->(sec)
            MERGE (sec)-[:MODIFIED_BY_CR]->(cr)
            RETURN count(*) AS cnt
        """, tdoc=tdoc, sids=section_ids)
        count += r.single()["cnt"]
    return count


OWNED_CR_PROPS = ["reasonForChange", "summaryOfChange", "consequencesIfNotApproved"]
#: Phase-1 이 :CR 로 분류하는 Tdoc 목록 Type(`phase-1/jsonld/03_tdoc_instances.py` 의 `CR_TYPES`).
PHASE1_CR_TYPES = ("CR", "draftCR", "pCR")
OWNED_REL_TYPES = ["BELONGS_TO_CR_PACK", "HAS_CR", "AFFECTS_CORE_SPEC", "AFFECTS_TEST_SPEC",
                   "AFFECTS_OM_SPEC", "MODIFIES_SECTION", "MODIFIED_BY_CR"]


def absorb_backfill_twins(session, dry_run: bool) -> dict[str, int]:
    """같은 tdocNumber 의 Tdoc 짝이 생긴 backfill CR 노드를 그 짝으로 흡수한다.

    짝에 :CR 라벨이 없어도 흡수한다. 입력에 있는 CR 이면 앞선 CR 레이블 보장이 이미 라벨을
    붙였고, 입력에 없는 문서면 Phase-1 이 CR 로 보지 않은 그 Tdoc 이 정본이다. `Tdoc:CR` 로만
    찾으면 둘째 경우의 backfill 노드가 같은 문서의 둘째 노드로 남는다 — 정합화는 다른 생성 코드의
    간선이 붙은 backfill 노드를 지우지 않는다.

    다른 생성 코드의 간선은 짝으로 옮긴다(짝에 같은 타입·같은 상대·같은 속성의 간선이 이미 있으면
    옮기지 않고 버린다). 소유 간선과 CR-Form 속성은 버린다 — 이어지는 적재가 짝 위에 다시 쓴다.
    짝이 둘 이상이면 어느 쪽이 정본인지 이 적재기가 정할 수 없으므로 건드리지 않고 센다.
    """
    pairs, ambiguous = [], 0
    for r in session.run("""
            MATCH (bf:CR {_createdBy: 'phase-4-backfill'}) WHERE NOT bf:Tdoc
            MATCH (tw:Tdoc {tdocNumber: bf.tdocNumber})
            RETURN elementId(bf) AS bf, collect(elementId(tw)) AS tws
        """):
        if len(r["tws"]) == 1:
            pairs.append({"bf": r["bf"], "tw": r["tws"][0]})
        else:
            ambiguous += 1
    moved = dropped = 0
    if pairs:
        cnt = lambda q: sum(
            session.run(q, pairs=pairs[i:i + BATCH_SIZE], owned=OWNED_REL_TYPES).single()["n"]
            for i in range(0, len(pairs), BATCH_SIZE)
        )
        # CR 서식 간선(`_createdBy='phase-4-backfill'` 인 MODIFIES · RELATED_TO)은 옮기지 않고 bf 와 함께
        # 지운다. 짝인 Phase-1 노드에는 Tdoc List 가 단 같은 뜻의 간선이 있다.
        match = ("UNWIND $pairs AS p MATCH (bf) WHERE elementId(bf) = p.bf "
                 "MATCH (tw) WHERE elementId(tw) = p.tw ")
        same_in = ("EXISTS { MATCH (x)-[r2]->(tw) WHERE type(r2) = type(r) "
                   "AND properties(r2) = properties(r) }")
        same_out = ("EXISTS { MATCH (tw)-[r2]->(x) WHERE type(r2) = type(r) "
                    "AND properties(r2) = properties(r) }")
        if dry_run:
            dropped = cnt(match + "MATCH (x)-[r]->(bf) WHERE NOT type(r) IN $owned AND coalesce(r._createdBy, '') <> 'phase-4-backfill' AND x <> bf "
                          f"AND {same_in} RETURN count(r) AS n")
            dropped += cnt(match + "MATCH (bf)-[r]->(x) WHERE NOT type(r) IN $owned AND coalesce(r._createdBy, '') <> 'phase-4-backfill' AND x <> bf "
                           f"AND {same_out} RETURN count(r) AS n")
            moved = cnt(match + "MATCH (bf)-[r]-(x) WHERE NOT type(r) IN $owned AND coalesce(r._createdBy, '') <> 'phase-4-backfill' AND x <> bf "
                        "RETURN count(r) AS n") - dropped
        else:
            dropped = cnt(match + "MATCH (x)-[r]->(bf) WHERE NOT type(r) IN $owned AND coalesce(r._createdBy, '') <> 'phase-4-backfill' AND x <> bf "
                          f"AND {same_in} DELETE r RETURN count(*) AS n")
            dropped += cnt(match + "MATCH (bf)-[r]->(x) WHERE NOT type(r) IN $owned AND coalesce(r._createdBy, '') <> 'phase-4-backfill' AND x <> bf "
                           f"AND {same_out} DELETE r RETURN count(*) AS n")
            moved = cnt(match + "MATCH (x)-[r]->(bf) WHERE NOT type(r) IN $owned AND coalesce(r._createdBy, '') <> 'phase-4-backfill' AND x <> bf "
                        "CALL apoc.refactor.to(r, tw) YIELD output RETURN count(output) AS n")
            moved += cnt(match + "MATCH (bf)-[r]->(x) WHERE NOT type(r) IN $owned AND coalesce(r._createdBy, '') <> 'phase-4-backfill' AND x <> bf "
                         "CALL apoc.refactor.from(r, tw) YIELD output RETURN count(output) AS n")
            cnt(match + "DETACH DELETE bf RETURN count(*) AS n")
    return {"backfill twin absorbed": len(pairs), "foreign edges moved to twin": moved,
            "foreign edges already on twin (dropped)": dropped, "backfill twin ambiguous (left)": ambiguous}


def _delete_rels(session, rel_ids: list[str], dry_run: bool) -> int:
    if not dry_run:
        for i in range(0, len(rel_ids), BATCH_SIZE):
            session.run(
                "UNWIND $ids AS rid MATCH ()-[r]->() WHERE elementId(r) = rid DELETE r",
                ids=rel_ids[i:i + BATCH_SIZE],
            )
    return len(rel_ids)


def reconcile(session, packs: list[dict], docs: list[dict],
              want_sections: set[tuple[str, str]], dry_run: bool) -> dict[str, int]:
    """이 적재기가 소유한 KG 부분을 입력과 같게 맞춘다. 지운(또는 지울) 수를 돌려준다."""
    _accept_cr_inputs(packs, docs)
    out: dict[str, int] = {}
    pack_ids = {p["crPackId"] for p in packs}
    want_member = {(t, p["crPackId"]) for p in packs for t in p.get("tdocNumbers") or []}
    doc_tdocs = {d["tdoc_number"] for d in docs}
    want_cross = desired_cross_spec(docs)

    # CRPack 노드: 입력에 없는 팩은 간선째 지운다.
    stale_packs = [
        r["id"] for r in session.run("MATCH (p:CRPack) RETURN p.crPackId AS id")
        if r["id"] not in pack_ids
    ]
    if stale_packs and not dry_run:
        session.run("MATCH (p:CRPack) WHERE p.crPackId IN $ids DETACH DELETE p", ids=stale_packs)
    out["CRPack"] = len(stale_packs)

    # 팩 소속 간선: 양방향 모두.
    for rel_type, pattern in [
        ("BELONGS_TO_CR_PACK", "(cr:CR)-[r:BELONGS_TO_CR_PACK]->(p:CRPack)"),
        ("HAS_CR", "(p:CRPack)-[r:HAS_CR]->(cr:CR)"),
    ]:
        ids = [
            r["rid"] for r in session.run(
                f"MATCH {pattern} RETURN elementId(r) AS rid, cr.tdocNumber AS t, p.crPackId AS p"
            )
            if (r["t"], r["p"]) not in want_member
        ]
        out[rel_type] = _delete_rels(session, ids, dry_run)

    # 교차 spec 간선 — 허브가 아닌 Spec 으로 간 것은 입력에 있어도 틀린 간선이다.
    for _, rel_type in CROSS_SPEC_FIELDS:
        ids = [
            r["rid"] for r in session.run(
                f"MATCH (cr:CR)-[r:{rel_type}]->(sp:Spec) "
                "RETURN elementId(r) AS rid, cr.tdocNumber AS t, sp.specNumber AS sn, "
                "sp.specRelease IS NULL AS hub"
            )
            if not r["hub"] or (r["t"], rel_type, r["sn"]) not in want_cross
        ]
        out[rel_type] = _delete_rels(session, ids, dry_run)

    # CR 발 Section 간선: 이번 실행의 해소 결과가 기준이다.
    for rel_type, pattern in [
        ("MODIFIES_SECTION", "(cr:CR)-[r:MODIFIES_SECTION]->(s:Section)"),
        ("MODIFIED_BY_CR", "(s:Section)-[r:MODIFIED_BY_CR]->(cr:CR)"),
    ]:
        ids = [
            r["rid"] for r in session.run(
                f"MATCH {pattern} RETURN elementId(r) AS rid, cr.tdocNumber AS t, s.sectionId AS sid"
            )
            if (r["t"], r["sid"]) not in want_sections
        ]
        out[rel_type] = _delete_rels(session, ids, dry_run)

    # CR-Form 속성: 입력에 없는 CR 에 남은 값은 옛 파싱이 다른 문서에서 읽어 붙인 것이라
    # 간선만 걷고 두면 보고서·답변이 그 값을 이 CR 의 변경 이유로 읽는다.
    stale_prop = [
        r["id"] for r in session.run(
            "MATCH (cr:CR) WHERE " + " OR ".join(f"cr.{p} IS NOT NULL" for p in OWNED_CR_PROPS)
            + " RETURN elementId(cr) AS id, cr.tdocNumber AS t"
        )
        if r["t"] not in doc_tdocs
    ]
    if stale_prop and not dry_run:
        session.run(
            "UNWIND $ids AS nid MATCH (cr) WHERE elementId(cr) = nid REMOVE "
            + ", ".join(f"cr.{p}" for p in OWNED_CR_PROPS),
            ids=stale_prop,
        )
    out["CR-Form 속성 (입력 밖 CR)"] = len(stale_prop)

    # CR 서식 값(backfill CR 의 제목 · MODIFIES · RELATED_TO) 가운데 입력이 요구하지 않는 것. 아래에서
    # 다른 생성 코드의 간선 때문에 남는 backfill 노드에 옛 입력의 값이 붙어 있지 않게 먼저 걷는다.
    out.update(reconcile_backfill_form(session, docs, doc_tdocs, dry_run, normalize_spec=normalize_spec_number))

    # backfill CR 노드: 입력에 없거나, 같은 tdocNumber 의 Tdoc 노드가 뒤에 생겨 둘이 된 것.
    # 다른 생성 코드의 간선(예: Email 층 ANCHORS)이 붙은 노드는 그 생성 코드의 것이기도 하므로 남기고
    # (소유 간선은 위에서 이미 걷혔다) 따로 센다.
    stale_cr, kept = [], []
    for r in session.run("""
            MATCH (cr:CR {_createdBy: 'phase-4-backfill'}) WHERE NOT cr:Tdoc
            OPTIONAL MATCH (twin:Tdoc {tdocNumber: cr.tdocNumber})
            OPTIONAL MATCH (cr)-[x]-() WHERE NOT type(x) IN $owned
                AND coalesce(x._createdBy, '') <> 'phase-4-backfill'
            RETURN elementId(cr) AS id, cr.tdocNumber AS t, twin IS NOT NULL AS twinned,
                   count(x) AS foreign
        """, owned=OWNED_REL_TYPES):
        if r["twinned"] or r["t"] not in doc_tdocs:
            (kept if r["foreign"] else stale_cr).append(r["id"])
    if stale_cr and not dry_run:
        session.run("UNWIND $ids AS nid MATCH (n) WHERE elementId(n) = nid DETACH DELETE n", ids=stale_cr)
    out["backfill CR node"] = len(stale_cr)
    out["backfill CR node kept (foreign edges)"] = len(kept)

    # 동적 Spec 노드(`_dynamic`). 입력의 읽기가 바뀌어 그 번호가 사라지면 간선만 걷히고 노드가
    # 남는다. 이번 입력에 없고 간선이 하나도 없는 것만 지운다 — 간선이 있으면 다른 생성 코드가 쓰는
    # 노드다. dry-run 은 위 간선을 걷지 않으므로 지금 고아인 것만 센다.
    want_specs = {sn for _, _, sn in want_cross}
    stale_spec = [
        r["id"] for r in session.run(
            "MATCH (sp:Spec {_dynamic: true}) WHERE NOT (sp)--() "
            "RETURN elementId(sp) AS id, sp.specNumber AS sn"
        )
        if r["sn"] not in want_specs
    ]
    if stale_spec and not dry_run:
        session.run("UNWIND $ids AS nid MATCH (n) WHERE elementId(n) = nid DELETE n", ids=stale_spec)
    out["동적 Spec node (입력 밖 · 간선 0)"] = len(stale_spec)

    # :CR 레이블. 주의: `ensure_cr_labels` 가 붙인 :CR 은 입력이 바뀌어도 남는다. Tdoc 목록 Type 이 `PHASE1_CR_TYPES`
    # 밖인 Tdoc 은 이 적재기의 입력이 CR 로 받을 때만 :CR 이므로, 입력 CR 문서에도 입력 팩 소속에도 없으면 걷는다.
    # 예: CR 서식이 없어 Phase-4 기록에서 빠진 문서(`cr_attachments.split_no_form`), 옛 입력이 CR 로 잘못 받은
    # `LS in` · `other` · `discussion` 문서. 입력 안의 문서는 Type 이 `other` 여도 CR 로 둔다(Tdoc 목록의 Type 이 틀린
    # CR 이 있다). 소속 간선 · CR-Form 속성은 위에서 `(cr:CR)` 로 걷었으므로 레이블은 맨 끝에 걷는다.
    keep_cr = doc_tdocs | {t for t, _ in want_member}
    stale_label = [
        r["id"] for r in session.run(
            "MATCH (t:Tdoc:CR) WHERE t.type IS NULL OR NOT t.type IN $types "
            "RETURN elementId(t) AS id, t.tdocNumber AS t",
            types=list(PHASE1_CR_TYPES),
        )
        if r["t"] not in keep_cr
    ]
    if stale_label and not dry_run:
        session.run("UNWIND $ids AS nid MATCH (t) WHERE elementId(t) = nid REMOVE t:CR", ids=stale_label)
    out[":CR 레이블 (입력 밖 · Phase-1 비 CR Type)"] = len(stale_label)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="쓰지 않고 reconcile 로 지울 수만 센다")
    args = ap.parse_args()

    print("=" * 60)
    print("RAN5 Phase-4: Load CR Ontology into Neo4j")
    print(f"  URI: {NEO4J_URI}")
    print("=" * 60)

    print("\n[1/7] Loading parsed data...")
    packs_data = load_json("crpacks.json")
    packs = _input_records(packs_data, "packs")
    docs_data = load_json("cr_documents.json")
    docs = _input_records(docs_data, "documents")
    _accept_cr_inputs(packs, docs)
    print(f"  CRPacks: {len(packs)}, CR docs: {len(docs)}")

    print("\n[2/7] Connecting to Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        print("  Connected")

        t0 = time.time()
        # 절 색인의 하한은 쓰기 전에 본다. [7/7] 에서 처음 보면 앞 단계의 자동 커밋 쓰기(색인 · CR 레이블)가
        # 이미 남은 뒤에 멈춘다. 이 적재기의 앞 단계는 Section 을 만들지 않으므로 여기서 읽은 수가 [7/7] 과 같다.
        with driver.session() as session:
            load_section_index(session)

        if args.dry_run:
            with driver.session() as session:
                want_sections: set[tuple[str, str]] = set()
                load_modifies_section(session, docs, load_section_index(session), want_sections, write=False)
                print("\n[dry-run] 흡수·reconcile 가 바꿀 것:")
                for k, v in absorb_backfill_twins(session, dry_run=True).items():
                    print(f"  {k}: {v}")
                for k, v in reconcile(session, packs, docs, want_sections, dry_run=True).items():
                    print(f"  {k}: {v}")
                print("\n[dry-run] backfill CR 에 채울 CR 서식 값:")
                for k, v in fill_backfill_form(session, docs, {d["tdoc_number"] for d in docs}, dry_run=True,
                                               normalize_spec=normalize_spec_number).items():
                    print(f"  {k}: {v}")
                print("\n[dry-run] crNumber 를 CR 시트가 확인한 번호로:")
                for k, v in reconcile_cr_numbers(session, docs, dry_run=True).items():
                    print(f"  {k}: {v}")
            return

        with driver.session() as session:
            print("\n[3/7] Creating indexes...")
            create_indexes(session)

            print("  CR 레이블 보장...")
            db = session.begin_transaction()
            ensure_cr_labels(db, docs)

            print("  backfill 쌍둥이 흡수...")
            for k, v in absorb_backfill_twins(db, dry_run=False).items():
                print(f"    {k}: {v}")

            print("\n[4/7] Loading CRPack nodes...")
            pack_cnt = load_crpacks(db, packs)
            if pack_cnt != len(packs):
                raise RuntimeError("CRPack count differs from input")
            print(f"  CRPack: {pack_cnt}")

            print("\n[5/7] Loading CR extensions...")
            cr_cnt = load_cr_extensions(db, docs)
            if cr_cnt != len(docs):
                raise RuntimeError("CR count differs from input")
            print(f"  CR extended: {cr_cnt}")
            print("  backfill CR 에 CR 서식 값(제목 · MODIFIES · RELATED_TO)...")
            for k, v in fill_backfill_form(db, docs, {d["tdoc_number"] for d in docs}, dry_run=False,
                                           normalize_spec=normalize_spec_number).items():
                print(f"    {k}: {v}")
            print("  crNumber 를 CR 시트가 확인한 번호로(바꾼 노드 · 충돌은 {})...".format(CRNUMBER_REPORT.name))
            for k, v in reconcile_cr_numbers(db, docs, dry_run=False, report_path=CRNUMBER_REPORT).items():
                print(f"    {k}: {v}")

            print("\n[6/7] Loading relationships...")
            rel_cnt = load_crpack_relationships(db, packs)
            expected_members = {(t, p["crPackId"]) for p in packs for t in p.get("tdocNumbers") or []}
            if rel_cnt != len(expected_members):
                raise RuntimeError("CRPack membership differs from input")
            print(f"  BELONGS_TO_CR_PACK + HAS_CR: {rel_cnt}")

            core, test, om, dyn = load_cross_spec(db, docs)
            desired_cross = desired_cross_spec(docs)
            for count, (_, relation) in zip((core, test, om), CROSS_SPEC_FIELDS):
                if count != sum(kind == relation for _, kind, _ in desired_cross):
                    raise RuntimeError(f"{relation} differs from input")
            print(f"  AFFECTS_CORE_SPEC: {core}")
            print(f"  AFFECTS_TEST_SPEC: {test}")
            print(f"  AFFECTS_OM_SPEC: {om}")
            print(f"  Dynamic Spec created: {dyn}")

            print("\n[7/7] Loading MODIFIES_SECTION...")
            section_index = load_section_index(db)
            print(f"  Section(release-키): {len(section_index.sid_by)}")
            want_sections = set()
            mod_cnt = load_modifies_section(db, docs, section_index, want_sections)
            if mod_cnt != len(want_sections):
                raise RuntimeError("CR Section relationships differ from input")
            print(f"  MODIFIES_SECTION + MODIFIED_BY_CR: {mod_cnt}")
            print(f"  Section resolve 통계: {dict(sorted(section_index.stats.items()))}")

            print("\n[reconcile] 입력에 없는 소유 노드·간선 제거...")
            # 적재와 정합화를 함께 커밋해 실패 시 기존 그래프를 보존한다.
            removed = reconcile(db, packs, docs, want_sections, dry_run=False)
            db.commit()
            for k, v in removed.items():
                print(f"  {k}: {v}")

    finally:
        driver.close()
    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print("Summary")
    print(f"{'=' * 60}")
    print(f"  CRPack: {pack_cnt}")
    print(f"  CR extended: {cr_cnt}")
    print(f"  Pack relationships: {rel_cnt}")
    print(f"  Cross-Spec: core={core}, test={test}, om={om}")
    print(f"  Dynamic Spec: {dyn}")
    print(f"  MODIFIES_SECTION: {mod_cnt}")
    print(f"  Reconcile removed: {removed}")
    print(f"  Elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
