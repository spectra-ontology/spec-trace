#!/usr/bin/env python3
"""
RAN3 Phase-4 Step 2-1: Neo4j 적재
- 입력: ontology/output/RAN/formal/instances/phase-4/RAN3/ (4개 JSON-LD)
- 적재 순서 (Spec §10):
  1. 인덱스 생성
  2. CRPack 노드
  3. 동적 Spec 노드
  4. CR 레이블 보장
  5. CR 속성 확장
  6. belongsToCRPack/hasCR 양방향
  7. affectsCore/Test/OMSpec
  8. modifiesSection/modifiedByCR 양방향

Spec: tdoc_ontology_specs(CR).md
Neo4j 관계명: UPPER_SNAKE_CASE
RAN3 Neo4j: port 7689 (RAN1과 별도 컨테이너)
"""

import json
import os
import sys
from pathlib import Path
from neo4j import GraphDatabase

# === 경로 설정 ===
PROJECT_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
INSTANCES_DIR = PROJECT_ROOT / "ontology" / "output" / "RAN" / "formal" / "instances" / "phase-4" / "RAN3"

# Spec §7.11: RAN3 Neo4j (별도 컨테이너, port 7689)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7689")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

BATCH_SIZE = 500


def load_jsonld(filename: str) -> list[dict]:
    path = INSTANCES_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("@graph", [])


def uri_to_id(uri: str) -> str:
    """URI에서 ID 추출: tdoc:crpack/RP-250233 → RP-250233"""
    if "/" in uri:
        return uri.rsplit("/", 1)[-1]
    return uri.replace("tdoc:", "")


def to_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


# Step 0: CR 레이블 보장
def ensure_cr_labels(session, cr_exts: list[dict]) -> int:
    """Phase-1에서 :CR 미분류된 Tdoc에 :CR 레이블 추가."""
    tdoc_numbers = [uri_to_id(cr["@id"]) for cr in cr_exts]

    result = session.run(
        """
        UNWIND $tdocs AS num
        MATCH (t:Tdoc {tdocNumber: num})
        WHERE NOT t:CR
        SET t:CR
        RETURN count(t) AS cnt
        """,
        tdocs=tdoc_numbers,
    )
    fixed = result.single()["cnt"]
    if fixed > 0:
        print(f"  [ensure_cr_labels] {fixed}개 Tdoc에 :CR 레이블 추가")
    return fixed


# Step 1: Indexes
def create_indexes(session):
    indexes = [
        "CREATE INDEX IF NOT EXISTS FOR (cp:CRPack) ON (cp.crPackId)",
    ]
    for idx in indexes:
        session.run(idx)
    print(f"  Created {len(indexes)} indexes")


# Step 2: CRPack 노드
def load_crpack_nodes(session, crpacks: list[dict]) -> int:
    count = 0
    for i in range(0, len(crpacks), BATCH_SIZE):
        batch = crpacks[i : i + BATCH_SIZE]
        params = []
        for cp in batch:
            params.append({
                "crPackId": cp.get("tdoc:crPackId", ""),
                "tsgMeeting": cp.get("tdoc:tsgMeeting", ""),
            })
        result = session.run(
            """
            UNWIND $batch AS cp
            MERGE (pack:CRPack {crPackId: cp.crPackId})
            SET pack.tsgMeeting = CASE WHEN cp.tsgMeeting <> '' THEN cp.tsgMeeting ELSE null END
            RETURN count(pack) AS cnt
            """,
            batch=params,
        )
        count += result.single()["cnt"]
    return count


# Step 3: 동적 Spec 노드
def load_dynamic_specs(session, specs: list[dict]) -> int:
    if not specs:
        return 0
    params = [{"specNumber": s.get("tdoc:specNumber", "")} for s in specs]
    result = session.run(
        """
        UNWIND $batch AS s
        MERGE (sp:Spec {specNumber: s.specNumber})
        RETURN count(sp) AS cnt
        """,
        batch=params,
    )
    return result.single()["cnt"]


# Step 4: CR 속성 확장
def load_cr_extensions(session, cr_exts: list[dict]) -> int:
    count = 0
    for i in range(0, len(cr_exts), BATCH_SIZE):
        batch = cr_exts[i : i + BATCH_SIZE]
        params = []
        for cr in batch:
            tdoc_number = uri_to_id(cr["@id"])
            params.append({
                "tdocNumber": tdoc_number,
                "reasonForChange": cr.get("tdoc:reasonForChange"),
                "summaryOfChange": cr.get("tdoc:summaryOfChange"),
                "consequencesIfNotApproved": cr.get("tdoc:consequencesIfNotApproved"),
            })
        # Q4 정정: MATCH → MERGE로 변경.
        # Phase-1 Tdoc List 커버리지 밖 CR (RAN3 K-4 errors=0 16건 등)은 Phase-1에서 노드 미생성.
        # Phase-4 cr_extensions 기준으로 Neo4j에 누락된 CR 노드를 생성하여 KG 완전성 확보.
        result = session.run(
            """
            UNWIND $batch AS cr
            MERGE (c:CR {tdocNumber: cr.tdocNumber})
            ON CREATE SET c._createdBy = 'phase-4-backfill'
            SET c.reasonForChange = cr.reasonForChange,
                c.summaryOfChange = cr.summaryOfChange,
                c.consequencesIfNotApproved = cr.consequencesIfNotApproved
            RETURN count(c) AS cnt
            """,
            batch=params,
        )
        count += result.single()["cnt"]
    return count


# Step 5: belongsToCRPack / hasCR
def load_crpack_relationships(session, cr_exts: list[dict], crpacks: list[dict]) -> int:
    """CR ↔ CRPack 양방향 관계 생성.

    소스 2개:
    1. cr_extensions.jsonld의 belongsToCRPack (CR → CRPack)
    2. crpacks.jsonld의 hasCR (CRPack → CR) — 같은 CR이 여러 Cover Sheet에 나열된 경우 보완
    """
    # 1) cr_extensions 기반
    pairs = set()
    for cr in cr_exts:
        pack_ref = cr.get("belongsToCRPack")
        if pack_ref:
            pairs.add((uri_to_id(cr["@id"]), uri_to_id(pack_ref)))

    # 2) crpacks.jsonld hasCR 기반 보완
    # Spec §6 §3: belongsToCRPack Functional — CR은 최대 1개 Pack에만 속함
    # 이미 다른 Pack에 속한 CR은 skip
    cr_already_assigned = {t for t, p in pairs}
    hasCR_added = 0
    for cp in crpacks:
        pack_id = cp.get("tdoc:crPackId", "")
        has_cr = cp.get("hasCR", [])
        if isinstance(has_cr, str):
            has_cr = [has_cr]
        for ref in has_cr:
            tdoc = ref.replace("tdoc:", "")
            if tdoc not in cr_already_assigned:
                pairs.add((tdoc, pack_id))
                cr_already_assigned.add(tdoc)
                hasCR_added += 1
    if hasCR_added:
        print(f"  [hasCR 보완] {hasCR_added}개 CR 추가 연결")

    pairs_list = [{"tdocNumber": t, "crPackId": p} for t, p in pairs]

    count = 0
    for i in range(0, len(pairs_list), BATCH_SIZE):
        batch = pairs_list[i : i + BATCH_SIZE]
        result = session.run(
            """
            UNWIND $batch AS p
            MATCH (c:CR {tdocNumber: p.tdocNumber})
            MATCH (pack:CRPack {crPackId: p.crPackId})
            MERGE (c)-[:BELONGS_TO_CR_PACK]->(pack)
            MERGE (pack)-[:HAS_CR]->(c)
            RETURN count(*) AS cnt
            """,
            batch=batch,
        )
        count += result.single()["cnt"]
    return count


# Step 6: affectsCore/Test/OMSpec
def load_affects_spec(session, cr_exts: list[dict]) -> dict:
    counts = {"core": 0, "test": 0, "om": 0}

    for rel_type, prop, label in [
        ("AFFECTS_CORE_SPEC", "affectsCoreSpec", "core"),
        ("AFFECTS_TEST_SPEC", "affectsTestSpec", "test"),
        ("AFFECTS_OM_SPEC", "affectsOMSpec", "om"),
    ]:
        pairs = []
        for cr in cr_exts:
            refs = to_list(cr.get(prop))
            for ref in refs:
                spec_num = uri_to_id(ref).replace("_", ".")
                pairs.append({
                    "tdocNumber": uri_to_id(cr["@id"]),
                    "specNumber": spec_num,
                })

        if not pairs:
            continue

        for i in range(0, len(pairs), BATCH_SIZE):
            batch = pairs[i : i + BATCH_SIZE]
            result = session.run(
                f"""
                UNWIND $batch AS p
                MATCH (c:CR {{tdocNumber: p.tdocNumber}})
                MATCH (sp:Spec {{specNumber: p.specNumber}})
                MERGE (c)-[:{rel_type}]->(sp)
                RETURN count(*) AS cnt
                """,
                batch=batch,
            )
            counts[label] += result.single()["cnt"]

    return counts


# Step 7: modifiesSection / modifiedByCR
def load_modifies_section(session, cr_exts: list[dict]) -> int:
    pairs = []
    for cr in cr_exts:
        refs = to_list(cr.get("modifiesSection"))
        for ref in refs:
            pairs.append({
                "tdocNumber": uri_to_id(cr["@id"]),
                "sectionId": uri_to_id(ref),
            })

    count = 0
    for i in range(0, len(pairs), BATCH_SIZE):
        batch = pairs[i : i + BATCH_SIZE]
        result = session.run(
            """
            UNWIND $batch AS p
            MATCH (c:CR {tdocNumber: p.tdocNumber})
            MATCH (sec:Section {sectionId: p.sectionId})
            MERGE (c)-[:MODIFIES_SECTION]->(sec)
            MERGE (sec)-[:MODIFIED_BY_CR]->(c)
            RETURN count(*) AS cnt
            """,
            batch=batch,
        )
        count += result.single()["cnt"]
    return count


# === 메인 ===

def main():
    print("=" * 60)
    print("RAN3 Phase-4 Step 2-1: Neo4j 적재 시작")
    print("=" * 60)

    # JSON-LD 로드
    crpacks = load_jsonld("crpacks.jsonld")
    cr_exts = load_jsonld("cr_extensions.jsonld")
    specs_dyn = load_jsonld("spec_dynamic.jsonld")

    print(f"  CRPack: {len(crpacks)}개")
    print(f"  CR extensions: {len(cr_exts)}개")
    print(f"  Dynamic Spec: {len(specs_dyn)}개")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        with driver.session() as session:
            print("\n[1/7] 인덱스 생성...")
            create_indexes(session)

            print("[2/7] CRPack 노드 생성...")
            cnt = load_crpack_nodes(session, crpacks)
            print(f"  Created/updated: {cnt} CRPack nodes")

            print("[3/7] 동적 Spec 노드 생성...")
            cnt = load_dynamic_specs(session, specs_dyn)
            print(f"  Created/updated: {cnt} dynamic Spec nodes")

            print("[0/7] CR 레이블 보장...")
            ensure_cr_labels(session, cr_exts)

            print("[4/7] CR 속성 확장...")
            cnt = load_cr_extensions(session, cr_exts)
            print(f"  Updated: {cnt} CR nodes")

            print("[5/7] CRPack 관계 생성...")
            cnt = load_crpack_relationships(session, cr_exts, crpacks)
            print(f"  Created: {cnt} BELONGS_TO_CR_PACK + HAS_CR pairs")

            print("[6/7] Cross-Spec 관계 생성...")
            counts = load_affects_spec(session, cr_exts)
            print(f"  AFFECTS_CORE_SPEC: {counts['core']}")
            print(f"  AFFECTS_TEST_SPEC: {counts['test']}")
            print(f"  AFFECTS_OM_SPEC: {counts['om']}")

            print("[7/7] modifiesSection 관계 생성...")
            cnt = load_modifies_section(session, cr_exts)
            print(f"  Created: {cnt} MODIFIES_SECTION + MODIFIED_BY_CR pairs")

            # Step 8: Spec §13.1 hasCR 최소 1개 — 빈 CRPack 삭제
            print("[8/8] 빈 CRPack 삭제 (Spec §13.1)...")
            result = session.run("""
                MATCH (cp:CRPack)
                WHERE NOT EXISTS { MATCH (cp)-[:HAS_CR]->() }
                DETACH DELETE cp
                RETURN count(cp) AS cnt
            """)
            deleted = result.single()["cnt"]
            if deleted:
                print(f"  Deleted: {deleted} empty CRPack nodes")

            # 검증 쿼리
            print("\n" + "=" * 60)
            print("적재 검증")
            print("=" * 60)

            verify_queries = [
                ("CRPack 노드 수", "MATCH (cp:CRPack) RETURN count(cp) AS cnt"),
                ("CR with reasonForChange", "MATCH (c:CR) WHERE c.reasonForChange IS NOT NULL RETURN count(c) AS cnt"),
                ("BELONGS_TO_CR_PACK 관계", "MATCH ()-[r:BELONGS_TO_CR_PACK]->() RETURN count(r) AS cnt"),
                ("HAS_CR 관계", "MATCH ()-[r:HAS_CR]->() RETURN count(r) AS cnt"),
                ("AFFECTS_CORE_SPEC 관계", "MATCH ()-[r:AFFECTS_CORE_SPEC]->() RETURN count(r) AS cnt"),
                ("AFFECTS_TEST_SPEC 관계", "MATCH ()-[r:AFFECTS_TEST_SPEC]->() RETURN count(r) AS cnt"),
                ("AFFECTS_OM_SPEC 관계", "MATCH ()-[r:AFFECTS_OM_SPEC]->() RETURN count(r) AS cnt"),
                ("MODIFIES_SECTION 관계", "MATCH ()-[r:MODIFIES_SECTION]->() RETURN count(r) AS cnt"),
                ("MODIFIED_BY_CR 관계", "MATCH ()-[r:MODIFIED_BY_CR]->() RETURN count(r) AS cnt"),
            ]

            for label, query in verify_queries:
                result = session.run(query)
                cnt = result.single()["cnt"]
                print(f"  {label}: {cnt}")

    finally:
        driver.close()

    print("\n✅ RAN3 Phase-4 Neo4j 적재 완료!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
