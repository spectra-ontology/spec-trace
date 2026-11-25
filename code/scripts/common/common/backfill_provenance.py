"""phase-6-backfill Tdoc 노드의 원본 목록·파싱 산출이 남아 있는지 판정한다.

`_createdBy='phase-6-backfill'` 인 Tdoc 은 Phase-1 목록에 없지만 VectorDB 에 있던 문서를 KG 에
노드로 세운 것이다(`docs/tsg/build/process/orphan_detection_guide.md` 패턴 A). 그 노드를 만든
스크립트는 저장소에 없고, 노드가 기댄 근거는 그때의 파싱 산출 이름 하나다.

파서가 번호 규칙(`tdoc_number.tdoc_number_of`)과 번호 자리 규칙(`meeting_slots` 의 dup_slot ·
foreign_copy)을 갖춘 뒤로는 같은 문서가 정규 번호 한 자리로만 산출된다. 그래서 정규화 전 이름
(끝의 U+200E · U+2011 하이픈 · 끝 마침표 · 밑줄 구분자)이나 사본 폴더 이름(같은 바이트를 든
꼬리 이름, 다른 번호의 문서를 담은 폴더)으로 세워진 노드는 근거를 잃은 채 남는다. 남은 노드는
정규 번호 노드와 같은 회의에 PRESENTED_AT 을 한 번 더 걸어 회의별 Tdoc 계수에 한 번 더 잡히고,
이메일 앵커가 그 이름으로 걸려 있으면 같은 문서의 앵커가 두 노드로 갈린다.

근거는 둘 중 하나다.
  (1) 그 이름 그대로의 파싱 산출 `vectordb/parsed/tdocs/<WG>/<회의>/<이름>/chunks.json`
  (2) Phase-1 목록 `tdocs.jsonld` 의 같은 이름 행
둘 다 없으면 근거를 잃은 노드다.

같은 증상(회의별 Tdoc 계수에 한 번 더 잡힘)의 형제가 하나 더 있다. 한 Tdoc 에서 같은 회의로
PRESENTED_AT 이 두 갈래 걸린 경우다. 옛 복구가 Tdoc 노드와 CR 노드에 따로 PRESENTED_AT 을 걸었고
(패턴 A 의 `phase-6-backfill-recovery`, 패턴 F 의 `cr-orphan-recovery`), 두 노드가 뒤에 한 노드로
합쳐지면서 두 관계가 같은 두 끝 사이에 나란히 남았다. 판정은 `parallel_presented_at` 이다.

판정은 게이트 `scripts/common/data-integrity/check_kg_tdoc_identity.py` 와 정리 도구
`scripts/tsg/RAN/formal/common/prune_stale_backfill.py` 가 이 모듈 한 벌을 쓴다. 두 자리에
따로 적으면 판정이 갈린다.
"""
from __future__ import annotations

import json
import re
from collections import Counter

from . import axis
from .tdoc_number import parent_tdoc_number, tdoc_number_of

MARKER = "phase-6-backfill"

#: 정리 도구가 옮기거나 지울 줄 아는 관계. 이 밖의 관계가 걸린 노드는 판정만 하고 손대지 않는다 —
#: 모르는 관계를 DETACH DELETE 로 함께 지우면 그 관계를 만든 쪽의 정보가 소리 없이 사라진다.
RESOLVABLE = {("PRESENTED_AT", "out"), ("ANCHORS", "in")}

# 산출 JSON-LD 는 통째로 싣기엔 크다. 줄 단위로 번호만 읽는다.
_LISTED = re.compile(r'"tdoc:tdocNumber":\s*"((?:[^"\\]|\\.)*)"')


def parsed_names(wg: str) -> set[str]:
    """파싱 산출이 있는 TDoc 폴더 이름 (회의를 가리지 않는다)."""
    base = axis.tree_path("vectordb_parsed", doc_type="tdocs", wg=wg)
    return {p.parent.name for p in base.glob("*/*/chunks.json")}


def listed_names(wg: str, wanted: set[str]) -> set[str]:
    """`wanted` 가운데 Phase-1 목록에 행이 있는 이름."""
    path = axis.tree_path("ontology_instances", wg=wg, phase=1) / "tdocs.jsonld"
    found: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            for m in _LISTED.finditer(line):
                name = json.loads(f'"{m.group(1)}"')
                if name in wanted:
                    found.add(name)
    return found


def _marked(created_by) -> bool:
    # 이중 레이블 노드는 `_createdBy` 를 리스트로 든다(['phase-4-backfill', 'phase-6-backfill']).
    if isinstance(created_by, list):
        return MARKER in created_by
    return created_by == MARKER


def twin_number(name: str) -> str | None:
    """근거를 잃은 이름이 가리키던 정규 번호. 없으면 None."""
    canon = tdoc_number_of(name)
    return canon if canon != name else parent_tdoc_number(name)


def _edges(session, eid: str) -> Counter:
    rows = session.run(
        "MATCH (t) WHERE elementId(t) = $e MATCH (t)-[r]-(x) "
        "RETURN type(r) AS ty, CASE WHEN startNode(r) = t THEN 'out' ELSE 'in' END AS d, count(*) AS c",
        e=eid)
    return Counter({(r["ty"], r["d"]): r["c"] for r in rows})


def _keyless_anchors(session, eid: str) -> int:
    # 앵커는 (context_chunk_id, entity_URI) 를 키로 MERGE 된다. 키가 빈 앵커는 옮길 때 그 키로
    # 짝을 찾을 수 없다.
    return session.run(
        "MATCH (x)-[a:ANCHORS]->(t) WHERE elementId(t) = $e AND a.context_chunk_id IS NULL "
        "RETURN count(a) AS c", e=eid).single()["c"]


def _meetings(session, eid: str) -> dict[str, str]:
    rows = session.run(
        "MATCH (t)-[:PRESENTED_AT]->(m) WHERE elementId(t) = $e "
        "RETURN elementId(m) AS m, coalesce(m.canonicalMeetingNumber, m.meetingNumber, '') AS name",
        e=eid)
    return {r["m"]: r["name"] for r in rows}


def stale_nodes(session, wg: str) -> list[dict]:
    """근거를 잃은 phase-6-backfill Tdoc 과 각각의 처리 판정.

    판정(`verdict`)은 둘이다.
      prune    정리 도구가 처리한다. ANCHORS 는 정규 번호 노드로 옮기고 노드는 지운다.
      blocked  손대지 않는다. `reason` 에 막힌 까닭을 적는다.
    """
    rows = session.run(
        "MATCH (t:Tdoc) WHERE t._createdBy IS NOT NULL AND t.tdocNumber IS NOT NULL "
        "RETURN elementId(t) AS e, t.tdocNumber AS n, t._createdBy AS cb").data()
    marked = [r for r in rows if _marked(r["cb"])]
    parsed = parsed_names(wg)
    lacking = {r["n"] for r in marked if r["n"] not in parsed}
    if not lacking:
        return []
    listed = listed_names(wg, lacking | {t for t in map(twin_number, lacking) if t})

    out = []
    for r in marked:
        name = r["n"]
        if name in parsed or name in listed:
            continue
        edges = _edges(session, r["e"])
        meetings = _meetings(session, r["e"])
        twin = twin_number(name)
        twin_rows = session.run("MATCH (k:Tdoc {tdocNumber: $n}) RETURN elementId(k) AS e",
                                n=twin).data() if twin else []
        item = {"element_id": r["e"], "name": name, "twin": twin,
                "twin_element_id": twin_rows[0]["e"] if len(twin_rows) == 1 else None,
                "meetings": sorted(meetings.values()),
                "edges": {f"{t}:{d}": c for (t, d), c in sorted(edges.items())}}
        reason = None
        unknown = sorted(f"{t}:{d}" for (t, d) in edges if (t, d) not in RESOLVABLE)
        if unknown:
            reason = f"정리 도구가 다루지 않는 관계 {unknown}"
        elif edges.get(("ANCHORS", "in")) and _keyless_anchors(session, r["e"]):
            reason = "context_chunk_id 가 빈 앵커"
        elif twin_rows and len(twin_rows) != 1:
            reason = f"정규 번호 {twin!r} 노드가 {len(twin_rows)}개"
        elif twin_rows:
            twin_basis = twin in parsed or twin in listed
            twin_meetings = _meetings(session, twin_rows[0]["e"])
            if not twin_basis:
                reason = f"정규 번호 {twin!r} 노드도 근거가 없음"
            elif not set(meetings) <= set(twin_meetings):
                reason = (f"정규 번호 {twin!r} 노드가 걸리지 않은 회의 "
                          f"{sorted(meetings[m] for m in set(meetings) - set(twin_meetings))}")
        elif edges.get(("ANCHORS", "in")):
            reason = "앵커를 옮겨 받을 정규 번호 노드가 없음"
        item["verdict"] = "blocked" if reason else "prune"
        item["reason"] = reason
        out.append(item)
    return out


def drifted_anchor_keys(session) -> list[dict]:
    """Tdoc 을 가리키는 ANCHORS 가운데 키 `entity_URI` 가 대상의 `tdocNumber` 와 다른 것.

    이메일 앵커 적재기는 VectorDB 페이로드의 `tdocNumber` 를 그대로 `entity_URI` 에 적는다.
    페이로드가 정규화 전 이름(뒤 공백 등)이던 때 걸린 앵커는 정규 번호 노드에 걸려 있으면서도 키만
    옛 이름을 든다. 그 키로는 지금의 적재기가 같은 앵커를 MERGE 로 찾지 못해 두 벌이 생긴다.

    `fixable` 은 옛 키를 번호 규칙에 넣으면 대상 번호가 되고, 정규 키의 짝이 아직 없는 경우다.
    """
    rows = session.run(
        "MATCH (x)-[a:ANCHORS]->(t:Tdoc) WHERE t.tdocNumber IS NOT NULL "
        "AND (a.entity_URI IS NULL OR a.entity_URI <> t.tdocNumber) "
        "OPTIONAL MATCH (x)-[b:ANCHORS {context_chunk_id: a.context_chunk_id, "
        "entity_URI: t.tdocNumber}]->(t) "
        "RETURN elementId(a) AS e, a.entity_URI AS key, t.tdocNumber AS n, "
        "a.context_chunk_id IS NOT NULL AS has_chunk, count(b) AS twins").data()
    out = []
    for r in rows:
        fixable = (r["key"] is not None and r["has_chunk"] and r["twins"] == 0
                   and tdoc_number_of(r["key"]) == r["n"])
        out.append({"element_id": r["e"], "key": r["key"], "number": r["n"], "fixable": fixable})
    return out


#: 개최 형식 꼬리표. 회의 식별자 정규화 규칙(`docs/tsg/build/standards/meeting_id_normalization.md`
#: §3)은 e-meeting 표시를 이름이 아니라 속성으로 보고 지운다. 게이트
#: `check_meeting_consistency.canonical_meeting_id` 의 첫 줄과 같은 꼬리 규칙이다.
_MEETING_FORMAT_TAIL = re.compile(r"[-_](?:e|E|Electronic)$")


def meeting_key_of(key: str) -> str:
    """옛 Meeting 앵커 키에서 개최 형식 꼬리 하나만 걷어 낸 것.

    bis 표기 접기 등 다른 정규화는 하지 않는다. 그 게이트의 머리말대로 잘못 만들어진 식별자를
    흡수하면 생성 코드의 결함이 다시 보이지 않으므로, 꼬리 하나만 걷어 정확히 대상 id 가 되는 키만
    같은 회의로 본다.
    """
    return _MEETING_FORMAT_TAIL.sub("", key.strip())


def drifted_meeting_anchor_keys(session) -> list[dict]:
    """Meeting 을 가리키는 ANCHORS 가운데 키 `entity_URI` 가 대상의 `id` 와 다른 것.

    이메일 결정적 앵커 생성기는 회의 앵커의 `entity_URI` 에 그때의 Meeting.id 를 적는다. 회의
    폴더 이름의 `_EOM` 을 개최 형식 표시로 잘못 읽던 때 만든 id 에는 `-e` 꼬리가 붙었고, 그 뒤
    Meeting.id 가 꼬리 없이 다시 서면서 앵커는 정규 노드에 걸린 채 키만 옛 id 를 든다. 그 키로는
    지금의 적재기가 같은 앵커를 MERGE 로 찾지 못해 두 벌이 생긴다.

    `fixable` 은 다음을 모두 만족할 때다.
      - 키와 청크가 있고, 정규 키(`m.id`)의 짝이 아직 없다.
      - 옛 키가 지금 어느 Meeting 의 id 도 아니다(다른 회의를 가리키는 키를 옮기지 않는다).
      - 옛 키에서 개최 형식 꼬리 하나를 걷으면 정확히 `m.id` 다(`meeting_key_of`).
      - 앵커의 `match_key` 가 대상의 `canonicalMeetingNumber` 와 같다(본문에서 찾은 회의 번호가
        이 회의다).
    """
    rows = session.run(
        "MATCH (x)-[a:ANCHORS]->(m:Meeting) WHERE m.id IS NOT NULL "
        "AND (a.entity_URI IS NULL OR a.entity_URI <> m.id) "
        "OPTIONAL MATCH (x)-[b:ANCHORS {context_chunk_id: a.context_chunk_id, "
        "entity_URI: m.id}]->(m) "
        "WITH a, m, count(b) AS twins "
        "OPTIONAL MATCH (o:Meeting {id: a.entity_URI}) "
        "RETURN elementId(a) AS e, a.entity_URI AS key, m.id AS id, "
        "a.context_chunk_id IS NOT NULL AS has_chunk, twins, count(o) AS taken, "
        "a.match_key IS NOT NULL AND a.match_key = m.canonicalMeetingNumber AS same_number").data()
    out = []
    for r in rows:
        fixable = (r["key"] is not None and r["has_chunk"] and r["twins"] == 0
                   and r["taken"] == 0 and r["same_number"]
                   and meeting_key_of(r["key"]) == r["id"])
        out.append({"element_id": r["e"], "key": r["key"], "number": r["id"], "fixable": fixable})
    return out


#: 나란한 PRESENTED_AT 가운데 하나를 지워도 잃는 것이 없는 속성. 복구 표지뿐이고, 지우는 관계의
#: 표지는 정리 도구의 되돌림 기록에 남는다. 이 밖의 속성이 든 관계가 섞이면 손대지 않는다.
RECOVERY_PROPS = {"recoveredBy", "recoveredAt"}


def parallel_presented_at(session) -> list[dict]:
    """한 Tdoc 에서 같은 회의로 나란히 걸린 PRESENTED_AT 묶음과 각각의 처리 판정.

    남길 관계는 복구 표지가 없는 것(적재기가 건 것)을 먼저, 그다음 `recoveredAt` 이 이른 것을 고른다.
    `verdict` 는 `prune`(남길 하나 밖의 관계를 지운다) 또는 `blocked`(복구 표지 밖의 속성이 있다)다.
    """
    rows = session.run(
        "MATCH (t:Tdoc)-[r:PRESENTED_AT]->(m) WITH t, m, collect(r) AS rs WHERE size(rs) > 1 "
        "RETURN elementId(t) AS t, t.tdocNumber AS n, elementId(m) AS m, "
        "coalesce(m.canonicalMeetingNumber, m.meetingNumber, '') AS meeting, "
        "[r IN rs | {element_id: elementId(r), props: properties(r)}] AS edges").data()
    out = []
    for r in rows:
        edges = sorted(r["edges"], key=lambda e: (e["props"].get("recoveredBy") is not None,
                                                  str(e["props"].get("recoveredAt") or ""),
                                                  e["element_id"]))
        extra = sorted({k for e in edges for k in e["props"]} - RECOVERY_PROPS)
        out.append({"tdoc_element_id": r["t"], "name": r["n"], "meeting_element_id": r["m"],
                    "meeting": r["meeting"], "keep": edges[0], "drop": edges[1:],
                    "verdict": "blocked" if extra else "prune",
                    "reason": f"복구 표지 밖의 관계 속성 {extra}" if extra else None})
    return out


#: 속성 이름을 Cypher 에 이름으로 넣기 전에 거르는 규칙. 동적 키 제거는 APOC 없이 쓸 수 없어서
#: 정리 도구가 이름을 백틱으로 감싸 넣는다. 이 규칙 밖의 이름은 판정만 하고 손대지 않는다.
SAFE_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def empty_string_properties(session) -> list[dict]:
    """값이 빈 문자열인 Tdoc 속성. 노드마다 그런 속성 이름 목록과 처리 판정을 돌려준다.

    값이 없는 속성은 속성이 없는 것으로 둔다. 빈 문자열은 읽는 쪽이 값으로 받는다. 예를 들어
    `release = ''` 가 `_targetRelease` 옆에 있으면, 질의를 쓰는 쪽은 release 를 거르는 조건을 빈
    속성에 걸고 결과 0 행을 받는다. 같은 문서의 릴리스는 `_targetRelease` 와 `TARGET_RELEASE` 가 든다.
    모든 Tdoc을 조회하고 레이블과 `_createdBy`를 결과에 포함한다. 호출자는 이 정보와
    속성별 판정을 확인한 뒤 정리 대상을 선택한다.

    `verdict` 는 `drop`(빈 속성을 지운다) 또는 `blocked`(속성 이름이 `SAFE_KEY` 밖이다)다.
    """
    rows = session.run(
        "MATCH (t:Tdoc) WITH t, [k IN keys(t) WHERE t[k] = ''] AS ks WHERE size(ks) > 0 "
        "RETURN elementId(t) AS e, t.tdocNumber AS n, labels(t) AS labels, "
        "t._createdBy AS created_by, ks ORDER BY n").data()
    out = []
    for r in rows:
        unsafe = sorted(k for k in r["ks"] if not SAFE_KEY.fullmatch(k))
        out.append({"element_id": r["e"], "name": r["n"], "labels": sorted(r["labels"]),
                    "created_by": r["created_by"], "keys": sorted(r["ks"]),
                    "verdict": "blocked" if unsafe else "drop",
                    "reason": f"Cypher 이름으로 넣을 수 없는 속성 이름 {unsafe}" if unsafe else None})
    return out


def noncanonical_numbers(session) -> list[str]:
    """번호 규칙의 고정점이 아닌 `tdocNumber` (backfill 여부와 상관없이)."""
    rows = session.run("MATCH (t:Tdoc) WHERE t.tdocNumber IS NOT NULL RETURN t.tdocNumber AS n")
    return sorted(r["n"] for r in rows if tdoc_number_of(r["n"]) != r["n"])
