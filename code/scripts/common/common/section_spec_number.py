#!/usr/bin/env python3
"""section_spec_number.py — Section.specNumber의 정의와 일치 여부 검사.

정의
----
`Section.specNumber`는 소속 Spec의 규격 번호를 조회에 사용하도록 속성에도 저장한 값이다.

    (sec:Section)-[:BELONGS_TO_SPEC]->(sp:Spec)  가 정확히 하나이고
    sp 가 release-키 Spec(specRelease 보유)이며 sp.specNumber 가 있으면
    sec.specNumber = sp.specNumber

속성에도 저장하면 Section을 규격 번호로 거르는 질의(분류 라벨·답변 질의·Qdrant payload
대조)가 소속 관계를 추가로 조회하지 않아도 된다. 적재기·누락값 보완 도구·게이트는
같은 정의를 사용해 이 속성과 소속 Spec의 규격 번호가 일치하는지 확인한다.
온톨로지에서는 `tdoc:specNumber` 의 Section 값과 SHACL `SectionBelongsToReleaseKeyedShape`
(`belongsToSpec/specNumber` 와 같아야 한다)가 같은 정의를 선언한다.

판정
----
Section 마다 하나의 상태를 준다.

  agree       값이 있고 소속 Spec 의 값과 같다.
  missing     정의로 값을 정할 수 있는데 속성이 없다. 누락값 보완 도구의 대상이다.
  disagree    속성이 있는데 소속 Spec의 값과 다르다. 속성과 소속 관계 중 어느 쪽을
              고쳐야 하는지는 이 검사만으로 정할 수 없으므로 기존 값을 덮어쓰지 않는다.
  noOwner     BELONGS_TO_SPEC 이 없다. 정의로 값을 정할 수 없다.
  multiOwner  BELONGS_TO_SPEC 이 둘 이상이다. 정의로 값을 정할 수 없다.
  badOwner    소속 노드가 Spec 이 아니거나, 허브(specRelease 없음)이거나, specNumber 가 없다.

상태와 별도로 `ownerIdMismatch`를 센다. sectionId의 문법은
`{specNumber}-{specRelease}-{sectionNumber}`이며 규격 번호와 release가 포함된다.
이 접두 부분이 소속 Spec의 값과 다르면 신원과 소속의 불일치로 집계한다. 속성과 관계의
규격 번호만 비교하면 놓칠 수 있으므로 별도로 검사하며, 원인 판단에는 입력 근거가 필요하다.

Spec:     docs/tsg/RAN/formal/RAN1/phase-3/design-spec/tdoc_ontology_specs(TS).md Step 5 §3.1 · Step 6 §3
Ontology: ontology/schema/tdoc-ontology.ttl (tdoc:specNumber) · tdoc-ontology-shapes.ttl
          (SectionBelongsToReleaseKeyedShape)
사용처:   적재기 `scripts/tsg/RAN/formal/RAN{1..5}/phase-3/neo4j/01_load_ts_structure.py` 의 SET,
          채움 도구 `scripts/tsg/RAN/formal/common/backfill_section_spec_number.py`,
          게이트 `scripts/common/data-integrity/check_section_spec_number.py`.
Cycle:    Section 신원 속성의 정의를 적재와 감사에서 함께 사용한다.
LLM 호출: 없음
"""
from __future__ import annotations

STATUSES = ("agree", "missing", "disagree", "noOwner", "multiOwner", "badOwner")

#: 게이트를 막는 상태. agree 만 통과다.
BLOCKING = tuple(s for s in STATUSES if s != "agree") + ("ownerIdMismatch",)

#: 소속 관계를 적재한 직후 같은 SET 절로 규격 번호 속성을 저장한다.
LOADER_SET = "SET sec.specNumber = sp.specNumber"

_CLASSIFY = """
MATCH (sec:Section)
WITH sec, [(sec)-[:BELONGS_TO_SPEC]->(x) | x] AS owners
WITH sec, owners, size(owners) AS n
WITH sec, owners, n, CASE WHEN n = 1 THEN owners[0] END AS sp
WITH sec, owners, n, sp,
     coalesce(n = 1 AND sp:Spec AND sp.specRelease IS NOT NULL
              AND sp.specNumber IS NOT NULL, false) AS derivable
WITH sec, owners, sp, derivable,
     CASE
       WHEN n = 0 THEN 'noOwner'
       WHEN n > 1 THEN 'multiOwner'
       WHEN NOT derivable THEN 'badOwner'
       WHEN sec.specNumber IS NULL THEN 'missing'
       WHEN sec.specNumber = sp.specNumber THEN 'agree'
       ELSE 'disagree'
     END AS status,
     derivable AND NOT coalesce(
       sec.sectionId STARTS WITH (sp.specNumber + '-' + sp.specRelease + '-'), false
     ) AS idMismatch
"""

Q_AUDIT = _CLASSIFY + """
RETURN count(*) AS sections,
       sum(CASE status WHEN 'agree' THEN 1 ELSE 0 END) AS agree,
       sum(CASE status WHEN 'missing' THEN 1 ELSE 0 END) AS missing,
       sum(CASE status WHEN 'disagree' THEN 1 ELSE 0 END) AS disagree,
       sum(CASE status WHEN 'noOwner' THEN 1 ELSE 0 END) AS noOwner,
       sum(CASE status WHEN 'multiOwner' THEN 1 ELSE 0 END) AS multiOwner,
       sum(CASE status WHEN 'badOwner' THEN 1 ELSE 0 END) AS badOwner,
       sum(CASE WHEN idMismatch THEN 1 ELSE 0 END) AS ownerIdMismatch,
       collect(CASE WHEN status = 'missing' THEN
         {sectionId: sec.sectionId, ownerSpecNumber: sp.specNumber,
          ownerSpecRelease: sp.specRelease} END)[..$k] AS missingExamples,
       collect(CASE WHEN status = 'disagree' THEN
         {sectionId: sec.sectionId, value: sec.specNumber, ownerSpecNumber: sp.specNumber,
          ownerSpecRelease: sp.specRelease} END)[..$k] AS disagreeExamples,
       collect(CASE WHEN status = 'noOwner' THEN
         {sectionId: sec.sectionId, value: sec.specNumber} END)[..$k] AS noOwnerExamples,
       collect(CASE WHEN status = 'multiOwner' THEN
         {sectionId: sec.sectionId, value: sec.specNumber,
          owners: [o IN owners | {labels: labels(o), specNumber: o.specNumber,
                                  specRelease: o.specRelease}]} END)[..$k] AS multiOwnerExamples,
       collect(CASE WHEN status = 'badOwner' THEN
         {sectionId: sec.sectionId, value: sec.specNumber, ownerLabels: labels(owners[0]),
          ownerSpecNumber: owners[0].specNumber, ownerSpecRelease: owners[0].specRelease}
         END)[..$k] AS badOwnerExamples,
       collect(CASE WHEN idMismatch THEN
         {sectionId: sec.sectionId, ownerSpecNumber: sp.specNumber,
          ownerSpecRelease: sp.specRelease} END)[..$k] AS ownerIdMismatchExamples
"""

#: missing 상태이며 sectionId의 규격 번호·release가 소속 Spec과 일치하는 절만 묶는다.
#: 신원과 소속이 불일치하면 기존 근거를 검토할 수 있도록 값을 보완하지 않는다.
Q_FILL_PLAN = _CLASSIFY + """
WITH sec, sp, status, idMismatch
WHERE status = 'missing' AND NOT idMismatch
WITH sp, collect({element: elementId(sec), sectionId: sec.sectionId}) AS sections
RETURN elementId(sp) AS spec, sp.specNumber AS specNumber, sp.specRelease AS specRelease,
       sections
ORDER BY specNumber, specRelease
"""

#: 기록해 둔 사전 상태(값 없음)의 절만, 그 상태가 그대로일 때만 채운다.
Q_FILL = """
MATCH (sp:Spec) WHERE elementId(sp) = $spec
UNWIND $elements AS element
MATCH (sec:Section) WHERE elementId(sec) = element
MATCH (sec)-[:BELONGS_TO_SPEC]->(sp)
WHERE sec.specNumber IS NULL
  AND size([(sec)-[:BELONGS_TO_SPEC]->(x) | x]) = 1
SET sec.specNumber = sp.specNumber
RETURN count(sec) AS written
"""

Q_HAS_SECTION_LABEL = "CALL db.labels() YIELD label WHERE label = 'Section' RETURN count(*) AS n"


def audit(session, examples: int = 5) -> dict:
    """한 그래프의 Section 을 정의대로 판정해 상태별 수와 예시를 돌려준다. 읽기만 한다.

    Section 라벨이 아예 없는 그래프(예: plenary 파티션)는 질의를 보내지 않고 `sections=0` 을
    돌려준다. 없는 라벨을 질의하면 서버가 경고만 쏟고 같은 0 을 돌려주기 때문이다.
    """
    def work(tx):
        if not tx.run(Q_HAS_SECTION_LABEL).single()["n"]:
            return {"sections": 0, **{s: 0 for s in STATUSES}, "ownerIdMismatch": 0}
        return dict(tx.run(Q_AUDIT, k=examples).single())
    return session.execute_read(work)


def fill_plan(session) -> list[dict]:
    """채울 절을 소속 Spec 별로 묶어 돌려준다. 읽기만 한다."""
    def work(tx):
        if not tx.run(Q_HAS_SECTION_LABEL).single()["n"]:
            return []
        return [dict(r) for r in tx.run(Q_FILL_PLAN)]
    return session.execute_read(work)


def fill_group(session, group: dict) -> int:
    """한 Spec 묶음을 한 트랜잭션으로 채운다. 기록과 다른 수가 쓰이면 되돌린다."""
    elements = [s["element"] for s in group["sections"]]

    def work(tx):
        written = tx.run(Q_FILL, spec=group["spec"], elements=elements).single()["written"]
        if written != len(elements):
            raise RuntimeError(
                f"{group['specNumber']} {group['specRelease']}: 기록한 {len(elements)}개 중 "
                f"{written}개만 사전 상태 그대로다 — 기록 뒤 그래프가 바뀌었으므로 쓰지 않는다")
        return written
    return session.execute_write(work)


def blocking_count(result: dict) -> int:
    return sum(result.get(key, 0) for key in BLOCKING)
