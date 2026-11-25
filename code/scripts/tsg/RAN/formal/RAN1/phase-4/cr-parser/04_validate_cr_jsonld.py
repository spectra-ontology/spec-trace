#!/usr/bin/env python3
"""
Phase-4 Step 1-4: JSON-LD 검증
- 입력: ontology/output/tsg/RAN/formal/instances/phase-4/RAN1/ (4개 파일)
- 검증: 무결성, 통계, 관계 일관성

Spec: tdoc_ontology_specs(CR).md §7 (인스턴스 예시 기반 검증)
"""

import json
import sys
import logging
from pathlib import Path

# === 경로 설정 ===
PROJECT_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "common"))
from ontology.jsonld_context import require_core_rdf_targets  # noqa: E402
_FORMAL_COMMON = PROJECT_ROOT / "scripts" / "tsg" / "RAN" / "formal" / "common"
if str(_FORMAL_COMMON) not in sys.path:
    sys.path.append(str(_FORMAL_COMMON))
from section_index_guard import require_complete_section_index  # noqa: E402
PHASE4_DIR = PROJECT_ROOT / "ontology" / "output" / "tsg" / "RAN" / "formal" / "instances" / "phase-4" / "RAN1"
PHASE1_DIR = PROJECT_ROOT / "ontology" / "output" / "tsg" / "RAN" / "formal" / "instances" / "phase-1" / "RAN1"
PHASE3_DIR = PROJECT_ROOT / "ontology" / "output" / "tsg" / "RAN" / "formal" / "instances" / "phase-3" / "RAN1"
PARSED_DIR = PROJECT_ROOT / "ontology" / "output" / "tsg" / "RAN" / "formal" / "parsed_cr" / "RAN1"
LOG_DIR = PROJECT_ROOT / "logs" / "tsg" / "RAN" / "formal" / "RAN1" / "phase-4"


def configure_logging() -> None:
    """실행 진입점에서만 로그를 준비한다.

    로그 파일은 mode="w" 로 열리므로 이 설정이 모듈 최상위에 있으면 import 만으로
    운영 로그가 비워진다. 이 모듈을 싣기만 하는 쪽(측정 도구, Phase-11 작업)이
    남의 기록을 지우지 않도록 main() 이 부를 때만 연다.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_DIR / "04_validate_cr_jsonld.log", mode="w"),
        ],
    )


log = logging.getLogger(__name__)


# === 유틸 ===

def load_jsonld(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
        require_core_rdf_targets(data)
    return data.get("@graph", [])


def to_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


# === 검증 함수 ===

class ValidationResult:
    """독립적인 검사 결과를 누적해 한 번의 실행에서 여러 결함을 보고한다.

    JSON 읽기 실패처럼 후속 검사를 수행할 수 없는 오류는 호출부에서 예외로 전파한다.
    """

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.details = []

    def check(self, name: str, condition: bool, detail: str = ""):
        if condition:
            self.passed += 1
            self.details.append(f"  ✅ {name}")
        else:
            self.failed += 1
            msg = f"  ❌ {name}"
            if detail:
                msg += f" — {detail}"
            self.details.append(msg)

    def warn(self, name: str, detail: str = ""):
        self.warnings += 1
        msg = f"  ⚠️  {name}"
        if detail:
            msg += f" — {detail}"
        self.details.append(msg)

    def summary(self) -> str:
        total = self.passed + self.failed
        return f"PASS {self.passed}/{total} (warnings: {self.warnings})"


def validate_integrity(result: ValidationResult):
    """1단계: 무결성 검증."""
    log.info("\n--- 1. 무결성 검증 ---")

    # CRPack
    crpacks = load_jsonld(PHASE4_DIR / "crpacks.jsonld")
    crpack_ids = set()
    for pack in crpacks:
        cid = pack.get("@id", "")
        result.check("CRPack @id pattern", cid.startswith("tdoc:crpack/"),
                      f"Bad id: {cid}")
        crpack_ids.add(cid)
        result.check("CRPack has crPackId", bool(pack.get("tdoc:crPackId")))
        result.check("CRPack @type", pack.get("@type") == "CRPack",
                      f"Got: {pack.get('@type')}")

    result.check("CRPack ID uniqueness",
                  len(crpack_ids) == len(crpacks),
                  f"Unique: {len(crpack_ids)}, Total: {len(crpacks)}")

    # CR extensions
    cr_exts = load_jsonld(PHASE4_DIR / "cr_extensions.jsonld")
    cr_ext_ids = set()
    for cr in cr_exts:
        cid = cr.get("@id", "")
        result.check("CR @id pattern", cid.startswith("tdoc:R1-"),
                      f"Bad id: {cid}")
        cr_ext_ids.add(cid)

    result.check("CR extension ID uniqueness",
                  len(cr_ext_ids) == len(cr_exts),
                  f"Unique: {len(cr_ext_ids)}, Total: {len(cr_exts)}")

    # Section extensions
    sec_exts = load_jsonld(PHASE4_DIR / "section_extensions.jsonld")
    sec_ext_ids = set()
    for sec in sec_exts:
        sid = sec.get("@id", "")
        result.check("Section @id pattern", sid.startswith("tdoc:section/"),
                      f"Bad id: {sid}")
        sec_ext_ids.add(sid)

    result.check("Section extension ID uniqueness",
                  len(sec_ext_ids) == len(sec_exts),
                  f"Unique: {len(sec_ext_ids)}, Total: {len(sec_exts)}")

    # Dynamic Specs
    specs = load_jsonld(PHASE4_DIR / "spec_dynamic.jsonld")
    for sp in specs:
        sid = sp.get("@id", "")
        result.check("Dynamic Spec @id pattern", sid.startswith("tdoc:spec/"),
                      f"Bad id: {sid}")
    result.check("Dynamic Spec ID uniqueness", len({sp.get('@id') for sp in specs}) == len(specs))

    return crpacks, cr_exts, sec_exts, specs


def validate_statistics(result: ValidationResult,
                        crpacks: list, cr_exts: list, sec_exts: list, specs: list):
    """2단계: 통계 검증."""
    log.info("\n--- 2. 통계 검증 ---")

    # Cover sheet 원본 데이터
    with open(PARSED_DIR / "cover_sheets.json", encoding="utf-8") as f:
        cover = json.load(f)

    with open(PARSED_DIR / "cr_documents.json", encoding="utf-8") as f:
        cr_docs = json.load(f)
        cr_meta = cr_docs["metadata"]

    # hasCR 는 1..* 라 소속 CR 이 0 개인 팩 후보는 CRPack 으로 만들지 않는다(Spec §6).
    # 그래서 팩 수는 Cover unique 와 같지 않고, 팩 후보 = 생성된 팩 ∪ 소속 CR 0 개인 팩이어야 한다.
    candidates = {p["cr_pack_id"] for p in cover["crpacks"]}
    candidates.update(c["cr_pack_id"] for c in cr_docs.get("cr_documents", [])
                      if c.get("cr_pack_id") and c.get("tdoc_number"))
    created = {p["tdoc:crPackId"] for p in crpacks}
    owners = {ref.removeprefix("tdoc:crpack/")
              for c in cr_exts for ref in to_list(c.get("belongsToCRPack"))}
    not_created = candidates - created
    result.check("CRPack ⊆ Cover·CR 디렉토리 팩 후보",
                  created <= candidates,
                  f"후보 밖 팩: {sorted(created - candidates)[:5]}")
    result.check("만들지 않은 팩 후보 = 소속 CR 0개",
                  not (not_created & owners),
                  f"후보 {len(candidates)} = 생성 {len(created)} + 소속 0 {len(not_created)}; "
                  f"소속 CR 이 있는데 빠진 팩: {sorted(not_created & owners)[:5]}")
    result.check("생성된 CRPack 은 hasCR ≥ 1",
                  all(to_list(p.get("hasCR")) for p in crpacks),
                  f"빈 팩: {sum(1 for p in crpacks if not to_list(p.get('hasCR')))}")

    # 선택 범위의 실제 파싱 기록을 기준으로 검증한다. 과거 전체 코퍼스의 절대 수나
    # 필드 비율을 요구하면 회의·기간을 좁혀 구축한 정상 결과가 실패한다.
    source_rows = cr_docs["cr_documents"]
    source_by_id = {f'tdoc:{row["tdoc_number"]}': row for row in source_rows
                    if isinstance(row.get("tdoc_number"), str) and row["tdoc_number"].strip()}
    generated_by_id = {row["@id"]: row for row in cr_exts}
    result.check("선택한 CR 입력 존재", bool(source_rows))
    result.check("파싱 CR 식별자 유일성·완전성",
                  len(source_by_id) == len(source_rows) == cr_meta["unique_crs"])
    result.check("CR extension 식별자 유일성", len(generated_by_id) == len(cr_exts))
    result.check("선택한 CR 식별자 전체 보존", set(source_by_id) == set(generated_by_id),
                  f"Missing: {sorted(set(source_by_id) - set(generated_by_id))[:5]}; "
                  f"Unexpected: {sorted(set(generated_by_id) - set(source_by_id))[:5]}")
    for source_field, property_name in [("reason_for_change", "tdoc:reasonForChange"),
                                        ("summary_of_change", "tdoc:summaryOfChange"),
                                        ("consequences_if_not_approved", "tdoc:consequencesIfNotApproved")]:
        expected = {identity: row[source_field] for identity, row in source_by_id.items()
                    if row.get(source_field)}
        actual = {identity: row[property_name] for identity, row in generated_by_id.items()
                  if row.get(property_name)}
        result.check(f"{property_name} 원문 필드 보존", actual == expected,
                      f"Source: {len(expected)}, Generated: {len(actual)}")

    log.info(f"  Dynamic Spec: {len(specs)}개")
    log.info(f"  Section extensions: {len(sec_exts)}개")


def validate_relationships(result: ValidationResult,
                           crpacks: list, cr_exts: list, sec_exts: list):
    """3단계: 관계 일관성 검증."""
    log.info("\n--- 3. 관계 일관성 검증 ---")

    # === hasCR ↔ belongsToCRPack 대칭 검증 ===

    # CRPack → CR (hasCR)
    pack_to_crs = {}
    for pack in crpacks:
        pack_id = pack["@id"]
        crs = to_list(pack.get("hasCR"))
        pack_to_crs[pack_id] = set(crs)

    # CR → CRPack (belongsToCRPack)
    cr_to_pack = {}
    for cr in cr_exts:
        cr_id = cr["@id"]
        cr_to_pack[cr_id] = set(to_list(cr.get("belongsToCRPack")))

    result.check("belongsToCRPack Functional", all(len(packs) <= 1 for packs in cr_to_pack.values()))
    pack_edges = {(pack_id, cr_id) for pack_id, crs in pack_to_crs.items() for cr_id in crs}
    owners = {}
    for pack_id, cr_id in pack_edges:
        owners.setdefault(cr_id, set()).add(pack_id)
    result.check("hasCR InverseFunctional", all(len(packs) <= 1 for packs in owners.values()))
    # 표지에만 있는 CR은 확장이 없을 수 있다. 확장이 있는 CR의 소속은 양방향이 일치해야 한다.
    expected_edges = {(pack_id, cr_id) for pack_id, cr_id in pack_edges if cr_id in cr_to_pack}
    actual_edges = {(pack_id, cr_id) for cr_id, packs in cr_to_pack.items() for pack_id in packs}
    result.check("hasCR ↔ belongsToCRPack 대칭",
                  expected_edges == actual_edges,
                  f"Missing: {len(expected_edges - actual_edges)}, Unexpected: {len(actual_edges - expected_edges)}")

    # === modifiesSection ↔ modifiedByCR 대칭 검증 ===

    # CR → Section (modifiesSection)
    cr_to_sections = {}
    for cr in cr_exts:
        cr_id = cr["@id"]
        sections = to_list(cr.get("modifiesSection"))
        if sections:
            cr_to_sections[cr_id] = set(sections)

    # Section → CR (modifiedByCR)
    section_to_crs = {}
    for sec in sec_exts:
        sec_id = sec["@id"]
        crs = to_list(sec.get("modifiedByCR"))
        section_to_crs[sec_id] = set(crs)

    forward = {(sec_id, cr_id) for cr_id, sections in cr_to_sections.items() for sec_id in sections}
    reverse = {(sec_id, cr_id) for sec_id, crs in section_to_crs.items() for cr_id in crs}
    result.check("modifiesSection ↔ modifiedByCR 대칭",
                  forward == reverse,
                  f"Missing: {len(forward - reverse)}, Unexpected: {len(reverse - forward)}")

    # === FK 존재 검증: belongsToCRPack → CRPack ===
    crpack_id_set = {p["@id"] for p in crpacks}
    missing_packs = 0
    for cr in cr_exts:
        for pack_ref in to_list(cr.get("belongsToCRPack")):
            if pack_ref not in crpack_id_set:
                missing_packs += 1

    result.check("belongsToCRPack FK 존재",
                  missing_packs == 0,
                  f"Missing CRPack refs: {missing_packs}")

    # === FK 존재 검증: modifiesSection → Section (Phase-3) ===
    phase3_sections = set()
    phase3_section_ids = []
    phase3_path = PHASE3_DIR / "release-aware" / "sections.jsonld"
    for item in load_jsonld(phase3_path):
        phase3_sections.add(item.get("@id", ""))
        phase3_section_ids.append(item.get("sectionId", "") or item.get("tdoc:sectionId", ""))
    # 덮인 색인으로 만든 산출물은 modifiesSection 이 비어 이 FK 검사를 공허하게 통과한다.
    # 같은 색인을 대조 기준으로 쓰므로 Phase-3 파서의 절 수보다 적으면 검증하지 않고 멈춘다.
    require_complete_section_index("RAN1", phase3_section_ids, str(phase3_path))

    missing_sections = 0
    for cr in cr_exts:
        for sec_ref in to_list(cr.get("modifiesSection")):
            if sec_ref not in phase3_sections:
                missing_sections += 1

    result.check("modifiesSection FK → Phase-3 Section",
                  missing_sections == 0,
                  f"Missing Section refs: {missing_sections}")

    # === affectsSpec FK → Spec ===
    phase1_specs = set()
    for item in load_jsonld(PHASE1_DIR / "specs.jsonld"):
        phase1_specs.add(item.get("@id", ""))
    dynamic_specs = {s["@id"] for s in load_jsonld(PHASE4_DIR / "spec_dynamic.jsonld")}
    all_specs = phase1_specs | dynamic_specs

    missing_spec_refs = 0
    for cr in cr_exts:
        for prop in ("affectsCoreSpec", "affectsTestSpec", "affectsOMSpec"):
            for ref in to_list(cr.get(prop)):
                if ref not in all_specs:
                    missing_spec_refs += 1

    result.check("affectsSpec FK → Spec (Phase-1 + Dynamic)",
                  missing_spec_refs == 0,
                  f"Missing Spec refs: {missing_spec_refs}")


# === 메인 ===

def main():
    configure_logging()
    log.info("=" * 60)
    log.info("Phase-4 Step 1-4: JSON-LD 검증 시작")
    log.info("=" * 60)

    result = ValidationResult()

    # 1. 무결성
    crpacks, cr_exts, sec_exts, specs = validate_integrity(result)

    # 2. 통계
    validate_statistics(result, crpacks, cr_exts, sec_exts, specs)

    # 3. 관계 일관성
    validate_relationships(result, crpacks, cr_exts, sec_exts)

    # === 결과 출력 ===
    log.info("\n" + "=" * 60)
    log.info(f"검증 결과: {result.summary()}")
    log.info("=" * 60)

    for detail in result.details:
        log.info(detail)

    if result.failed > 0:
        log.error(f"\n❌ {result.failed}개 검증 실패!")
        return 1

    log.info("\n✅ 모든 검증 통과!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
