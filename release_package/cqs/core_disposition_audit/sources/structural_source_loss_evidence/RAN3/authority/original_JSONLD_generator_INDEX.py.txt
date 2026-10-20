#!/usr/bin/env python3
"""
RAN3 Phase-4 Step 1-3: JSON-LD 인스턴스 생성
- 입력: parsed JSON (cover_sheets.json, cr_documents.json) + Phase-1/3 인스턴스
- 출력: ontology/output/RAN/formal/instances/phase-4/RAN3/ (4개 파일)

Spec §6~7, §9~§11 (CRPack, CR 확장, Section 역관계, 동적 Spec)

URI 패턴 (Phase-1 기존 준수):
- CR: tdoc:{tdocNumber}  (예: tdoc:R3-2500001)
- CRPack: tdoc:crpack/{crPackId}  (예: tdoc:crpack/RP-250233)
- Spec: tdoc:spec/{spec.replace('.','_')}  (예: tdoc:spec/38_331)
- Section: tdoc:section/{sectionId}  (예: tdoc:section/38.331-5.3.5)
"""

import json
import re
import sys
import logging
from pathlib import Path

# === 경로 설정 ===
PROJECT_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
PARSED_DIR = PROJECT_ROOT / "ontology" / "output" / "RAN" / "formal" / "parsed_cr" / "RAN3"
INSTANCES_DIR = PROJECT_ROOT / "ontology" / "output" / "RAN" / "formal" / "instances"
OUTPUT_DIR = INSTANCES_DIR / "phase-4" / "RAN3"
LOG_DIR = PROJECT_ROOT / "logs" / "RAN" / "formal" / "RAN3" / "phase-4"

SPEC_TITLES_FILE = PROJECT_ROOT / "ontology" / "input" / "spec_titles.json"

LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "03_generate_cr_jsonld.log", mode="w"),
    ],
)
log = logging.getLogger(__name__)


# === JSON-LD Context ===
CRPACK_CONTEXT = {
    "@vocab": "http://3gpp.org/ontology/tdoc#",
    "tdoc": "http://3gpp.org/ontology/tdoc#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "hasCR": {"@id": "tdoc:hasCR", "@type": "@id"},
}

CR_EXTENSION_CONTEXT = {
    "@vocab": "http://3gpp.org/ontology/tdoc#",
    "tdoc": "http://3gpp.org/ontology/tdoc#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "belongsToCRPack": {"@id": "tdoc:belongsToCRPack", "@type": "@id"},
    "affectsCoreSpec": {"@id": "tdoc:affectsCoreSpec", "@type": "@id"},
    "affectsTestSpec": {"@id": "tdoc:affectsTestSpec", "@type": "@id"},
    "affectsOMSpec": {"@id": "tdoc:affectsOMSpec", "@type": "@id"},
    "modifiesSection": {"@id": "tdoc:modifiesSection", "@type": "@id"},
}

SECTION_EXT_CONTEXT = {
    "@vocab": "http://3gpp.org/ontology/tdoc#",
    "tdoc": "http://3gpp.org/ontology/tdoc#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "modifiedByCR": {"@id": "tdoc:modifiedByCR", "@type": "@id"},
}

SPEC_DYNAMIC_CONTEXT = {
    "@vocab": "http://3gpp.org/ontology/tdoc#",
    "tdoc": "http://3gpp.org/ontology/tdoc#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}


# === URI 생성 ===

def cr_uri(tdoc_number: str) -> str:
    return f"tdoc:{tdoc_number}"

def crpack_uri(cr_pack_id: str) -> str:
    return f"tdoc:crpack/{cr_pack_id}"

def spec_uri(spec_number: str) -> str:
    return f"tdoc:spec/{spec_number.replace('.', '_')}"

def section_uri(section_id: str) -> str:
    return f"tdoc:section/{section_id}"


# === Phase-1/3 데이터 로드 ===

def load_phase1_crs() -> set[str]:
    """Phase-1 tdocs.jsonld에서 CR의 tdocNumber 집합 로드."""
    path = INSTANCES_DIR / "phase-1" / "RAN3" / "tdocs.jsonld"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    cr_tdocs = set()
    for item in data.get("@graph", []):
        tdoc_type = item.get("@type", "")
        if tdoc_type in ("tdoc:CR", "tdoc:Tdoc"):
            tdoc_num = item.get("tdoc:tdocNumber", "")
            if tdoc_num:
                cr_tdocs.add(tdoc_num)
    return cr_tdocs


def load_phase1_specs() -> set[str]:
    """Phase-1 specs.jsonld에서 Spec 번호 집합 로드."""
    path = INSTANCES_DIR / "phase-1" / "RAN3" / "specs.jsonld"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    specs = set()
    for item in data.get("@graph", []):
        spec_num = item.get("tdoc:specNumber", "")
        if spec_num:
            specs.add(spec_num)
    return specs


_REL_NUM_RE = re.compile(r"Rel-(\d+)")


def rel_num(rel: str | None) -> int:
    m = _REL_NUM_RE.search(rel or "")
    return int(m.group(1)) if m else -1


class SectionIndex:
    """release-키 Section 조회: (spec, release, sectionNumber) → sectionId.

    Section은 release-키(`{spec}-Rel-{N}-{secnum}`)로만 존재하므로 CR의
    clausesAffected를 CR target release 기준으로 해소한다. resolve 규칙은
    phase-3 migrate_to_release_aware.py와 동일: exact → fallback-le(≤target
    최신) → fallback-fwd → drop; release 미상이면 latest.
    """

    def __init__(self, entries) -> None:
        # entries: iterable of (sectionId, sectionNumber)
        self.sid_by: dict[tuple[str, str, str], str] = {}
        rels: dict[str, set[str]] = {}
        for sid, secnum in entries:
            secnum = str(secnum)
            if not sid or not sid.endswith("-" + secnum):
                continue
            stem = sid[: -(len(secnum) + 1)]
            if "-Rel-" not in stem:
                continue
            spec, rel_tail = stem.rsplit("-Rel-", 1)
            rel = f"Rel-{rel_tail}"
            self.sid_by[(spec, rel, secnum)] = sid
            rels.setdefault(spec, set()).add(rel)
        self.releases_by_spec: dict[str, list[str]] = {
            spec: sorted(rs, key=rel_num, reverse=True) for spec, rs in rels.items()
        }
        self.stats: dict[str, int] = {}

    def resolve(self, spec: str, secnum: str, target_rel: str | None) -> str | None:
        secnum = str(secnum)
        rels = self.releases_by_spec.get(spec)
        if not rels:
            self.stats["drop-nospec"] = self.stats.get("drop-nospec", 0) + 1
            return None
        if target_rel is None or rel_num(target_rel) < 0:
            target_rel = rels[0]
            base_method = "latest"
        else:
            base_method = "exact"
        sid = self.sid_by.get((spec, target_rel, secnum))
        if sid:
            self.stats[base_method] = self.stats.get(base_method, 0) + 1
            return sid
        tnum = rel_num(target_rel)
        for r in rels:  # descending
            if rel_num(r) <= tnum and (spec, r, secnum) in self.sid_by:
                self.stats["fallback-le"] = self.stats.get("fallback-le", 0) + 1
                return self.sid_by[(spec, r, secnum)]
        for r in rels:
            if (spec, r, secnum) in self.sid_by:
                self.stats["fallback-fwd"] = self.stats.get("fallback-fwd", 0) + 1
                return self.sid_by[(spec, r, secnum)]
        self.stats["drop-nosec"] = self.stats.get("drop-nosec", 0) + 1
        return None


def load_phase3_sections() -> SectionIndex:
    """Phase-3 release-aware sections.jsonld에서 SectionIndex 로드."""
    path = INSTANCES_DIR / "phase-3" / "RAN3" / "release-aware" / "sections.jsonld"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    entries = []
    for item in data.get("@graph", []):
        sid = item.get("sectionId", "") or item.get("tdoc:sectionId", "")
        secnum = item.get("sectionNumber", "") or item.get("tdoc:sectionNumber", "")
        if sid and secnum != "":
            entries.append((sid, secnum))
    return SectionIndex(entries)


# === clausesAffected → Section 매칭 ===

def parse_clauses_to_sections(spec_number: str | None, clauses_text: str | None,
                               section_index: SectionIndex,
                               release: str | None) -> list[str]:
    """clausesAffected 문자열을 CR release 기준 release-키 Section URI로 해소."""
    if not spec_number or not clauses_text:
        return []

    clause_parts = re.split(r"[,;]\s*", clauses_text.strip())

    matched_sections = []
    for clause in clause_parts:
        clause = clause.strip()
        if not clause:
            continue

        clause_clean = re.sub(r"[^0-9A-Za-z.]", "", clause)
        if not clause_clean:
            continue

        sid = section_index.resolve(spec_number, clause_clean, release)
        if sid:
            matched_sections.append(section_uri(sid))

    return list(dict.fromkeys(matched_sections))


# === JSON-LD 생성 ===

def generate_crpacks(cover_data: dict, phase1_crs: set[str]) -> list[dict]:
    """CRPack 인스턴스 생성.

    Spec §13.1: hasCR 최소 1개. Phase-1에 매칭되는 CR이 0개인 Pack은 생성하지 않음.
    """
    instances = []
    skipped_empty = 0

    for pack in cover_data.get("crpacks", []):
        cr_pack_id = pack["cr_pack_id"]

        cr_refs = []
        for entry in pack.get("cr_entries", []):
            tdoc = entry.get("tdoc_number", "")
            if tdoc and tdoc in phase1_crs:
                cr_refs.append(cr_uri(tdoc))

        # Spec §13.1: hasCR 최소 1개 — Phase-1에 매칭되는 CR이 없으면 생성 안 함
        if not cr_refs:
            skipped_empty += 1
            continue

        instance = {
            "@id": crpack_uri(cr_pack_id),
            "@type": "CRPack",
            "tdoc:crPackId": cr_pack_id,
        }

        if pack.get("tsg_meeting"):
            instance["tdoc:tsgMeeting"] = pack["tsg_meeting"]

        instance["hasCR"] = cr_refs if len(cr_refs) > 1 else cr_refs[0]

        instances.append(instance)

    if skipped_empty:
        log.info(f"  CRPack 생성 스킵 (Phase-1 매칭 CR 0건): {skipped_empty}개")

    return instances


def generate_cr_extensions(cr_docs: dict, phase1_crs: set[str],
                           phase1_specs: set[str], section_ids: SectionIndex) -> tuple[list[dict], list[str]]:
    """CR 확장 속성 인스턴스 생성."""
    instances = []
    new_specs_needed = set()
    matched_phase1 = 0
    unmatched = 0

    for cr in cr_docs.get("documents", []):
        tdoc_number = cr.get("tdoc_number", "")
        if not tdoc_number:
            continue

        is_phase1 = tdoc_number in phase1_crs
        if is_phase1:
            matched_phase1 += 1
        else:
            unmatched += 1

        instance = {
            "@id": cr_uri(tdoc_number),
            "@type": "tdoc:CR",
        }

        has_data = False
        if cr.get("reason_for_change"):
            instance["tdoc:reasonForChange"] = cr["reason_for_change"]
            has_data = True
        if cr.get("summary_of_change"):
            instance["tdoc:summaryOfChange"] = cr["summary_of_change"]
            has_data = True
        if cr.get("consequences_if_not_approved"):
            instance["tdoc:consequencesIfNotApproved"] = cr["consequences_if_not_approved"]
            has_data = True

        if cr.get("cr_pack_id"):
            instance["belongsToCRPack"] = crpack_uri(cr["cr_pack_id"])
            has_data = True

        for spec_list, prop in [
            (cr.get("affects_core_spec", []), "affectsCoreSpec"),
            (cr.get("affects_test_spec", []), "affectsTestSpec"),
            (cr.get("affects_om_spec", []), "affectsOMSpec"),
        ]:
            if spec_list:
                refs = []
                for spec_num in spec_list:
                    refs.append(spec_uri(spec_num))
                    if spec_num not in phase1_specs:
                        new_specs_needed.add(spec_num)
                instance[prop] = refs if len(refs) > 1 else refs[0]
                has_data = True

        spec_number = cr.get("spec_number")
        clauses = cr.get("clauses_affected")
        section_refs = parse_clauses_to_sections(spec_number, clauses, section_ids, cr.get("release"))
        if section_refs:
            instance["modifiesSection"] = section_refs if len(section_refs) > 1 else section_refs[0]
            has_data = True

        if has_data:
            instances.append(instance)

    log.info(f"  Phase-1 매칭: {matched_phase1}, 미매칭: {unmatched}")
    log.info(f"  신규 Spec 필요: {len(new_specs_needed)}개 ({sorted(new_specs_needed)})")

    return instances, sorted(new_specs_needed)


def generate_section_extensions(cr_extensions: list[dict]) -> list[dict]:
    """Section modifiedByCR 역관계 인스턴스 생성."""
    section_to_crs: dict[str, list[str]] = {}

    for cr_ext in cr_extensions:
        cr_id = cr_ext["@id"]
        mod_sections = cr_ext.get("modifiesSection", [])
        if isinstance(mod_sections, str):
            mod_sections = [mod_sections]

        for sec_uri_val in mod_sections:
            section_to_crs.setdefault(sec_uri_val, []).append(cr_id)

    instances = []
    for sec_uri_str, cr_uris in sorted(section_to_crs.items()):
        instance = {
            "@id": sec_uri_str,
            "@type": "Section",
            "modifiedByCR": cr_uris if len(cr_uris) > 1 else cr_uris[0],
        }
        instances.append(instance)

    return instances


def load_spec_titles() -> dict[str, str]:
    if not SPEC_TITLES_FILE.exists():
        return {}
    try:
        with open(SPEC_TITLES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('specs', {})
    except Exception:
        return {}


def generate_dynamic_specs(new_spec_numbers: list[str]) -> list[dict]:
    """Phase-1에 없는 Spec의 동적 생성 인스턴스."""
    spec_titles = load_spec_titles()
    title_found = 0

    instances = []
    for spec_num in new_spec_numbers:
        instance = {
            "@id": spec_uri(spec_num),
            "@type": "tdoc:Spec",
            "tdoc:specNumber": spec_num,
        }

        if spec_num in spec_titles:
            instance["tdoc:specTitle"] = spec_titles[spec_num]
            title_found += 1

        instances.append(instance)

    log.info(f"    specTitle 매핑: {title_found}/{len(new_spec_numbers)}개 적용")
    return instances


# === 메인 ===

def main():
    log.info("=" * 60)
    log.info("RAN3 Phase-4 Step 1-3: JSON-LD 인스턴스 생성 시작")
    log.info("=" * 60)

    log.info("입력 데이터 로드...")

    with open(PARSED_DIR / "cover_sheets.json", encoding="utf-8") as f:
        cover_data = json.load(f)
    log.info(f"  Cover Sheets: {cover_data['metadata']['unique_crpacks']} CRPacks")

    with open(PARSED_DIR / "cr_documents.json", encoding="utf-8") as f:
        cr_docs = json.load(f)
    log.info(f"  CR Documents: {cr_docs['metadata']['unique_crs']} CRs")

    log.info("Phase-1/3 참조 데이터 로드...")
    phase1_crs = load_phase1_crs()
    log.info(f"  Phase-1 CR: {len(phase1_crs)}개")

    # Q4 정정: Phase-4 Neo4j 로더가 MATCH→MERGE로 변경되어 누락 CR backfill 지원.
    # Phase-4 cr_docs의 tdoc_number도 phase1_crs에 보강 → CRPack 생성 스킵 조건 완화.
    # 결과: RAN3 K-4 errors=0 16건 CRPack 복구 + K-1 100% (이미 반영).
    cr_doc_tdocs = {cr.get("tdoc_number", "") for cr in cr_docs.get("documents", []) if cr.get("tdoc_number")}
    phase4_additional = cr_doc_tdocs - phase1_crs
    phase1_crs = phase1_crs | cr_doc_tdocs
    log.info(f"  Phase-4 backfill CR: {len(phase4_additional)}개 (Phase-1 미커버)")
    log.info(f"  확장 후 CR set: {len(phase1_crs)}개")

    phase1_specs = load_phase1_specs()
    log.info(f"  Phase-1 Spec: {len(phase1_specs)}개")

    section_ids = load_phase3_sections()
    log.info(f"  Phase-3 Section(release-키): {len(section_ids.sid_by)}개")

    # 1. CRPack
    log.info("\n1. CRPack 인스턴스 생성...")
    crpack_instances = generate_crpacks(cover_data, phase1_crs)
    log.info(f"  CRPack: {len(crpack_instances)}개")

    # 2. CR 확장
    log.info("\n2. CR 확장 인스턴스 생성...")
    cr_ext_instances, new_specs = generate_cr_extensions(
        cr_docs, phase1_crs, phase1_specs, section_ids
    )
    log.info(f"  CR extensions: {len(cr_ext_instances)}개")
    log.info(f"  Section resolve 통계: {dict(sorted(section_ids.stats.items()))}")

    # 3. Section 역관계
    log.info("\n3. Section modifiedByCR 역관계 생성...")
    section_ext_instances = generate_section_extensions(cr_ext_instances)
    log.info(f"  Section extensions: {len(section_ext_instances)}개")

    # 4. 동적 Spec
    log.info("\n4. 동적 Spec 인스턴스 생성...")
    spec_dynamic_instances = generate_dynamic_specs(new_specs)
    log.info(f"  Dynamic Spec: {len(spec_dynamic_instances)}개")

    # JSON-LD 출력
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    outputs = [
        ("crpacks.jsonld", CRPACK_CONTEXT, crpack_instances),
        ("cr_extensions.jsonld", CR_EXTENSION_CONTEXT, cr_ext_instances),
        ("section_extensions.jsonld", SECTION_EXT_CONTEXT, section_ext_instances),
        ("spec_dynamic.jsonld", SPEC_DYNAMIC_CONTEXT, spec_dynamic_instances),
    ]

    for filename, context, instances in outputs:
        output_path = OUTPUT_DIR / filename
        jsonld = {
            "@context": context,
            "@graph": instances,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(jsonld, f, ensure_ascii=False, indent=2)

        size_kb = output_path.stat().st_size / 1024
        log.info(f"  {filename}: {len(instances)}개 ({size_kb:.1f} KB)")

    log.info("\n" + "=" * 60)
    log.info("생성 결과 요약")
    log.info("=" * 60)
    log.info(f"  CRPack: {len(crpack_instances)}개")
    log.info(f"  CR extensions: {len(cr_ext_instances)}개")
    log.info(f"  Section extensions: {len(section_ext_instances)}개")
    log.info(f"  Dynamic Spec: {len(spec_dynamic_instances)}개")
    total = len(crpack_instances) + len(cr_ext_instances) + len(section_ext_instances) + len(spec_dynamic_instances)
    log.info(f"  총 인스턴스: {total}개")

    return 0


if __name__ == "__main__":
    sys.exit(main())
