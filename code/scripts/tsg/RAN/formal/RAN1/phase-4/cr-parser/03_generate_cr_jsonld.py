#!/usr/bin/env python3
"""
Phase-4 Step 1-3: JSON-LD 인스턴스 생성
- 입력: parsed JSON (cover_sheets.json, cr_documents.json) + Phase-1/3 인스턴스
- 출력: ontology/output/tsg/RAN/formal/instances/phase-4/RAN1/ (4개 파일)

Spec: tdoc_ontology_specs(CR).md §5, §7

URI 패턴 (Phase-1 기존 준수):
- CR: tdoc:{tdocNumber}  (예: tdoc:R1-2001224)
- CRPack: tdoc:crpack/{crPackId}  (예: tdoc:crpack/RP-180200)
- Spec: tdoc:spec/{spec.replace('.','_')}  (예: tdoc:spec/38_214)
- Section: tdoc:section/{sectionId}  (예: tdoc:section/38.214-Rel-16-5.1.3.2)
"""

import json
import re
import sys
import logging
from pathlib import Path

# === 경로 설정 ===
PROJECT_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "common"))
from ontology.jsonld_context import canonical_document  # noqa: E402
from common.atomic_io import publish_text_set  # noqa: E402

# 「Clauses affected」 칸을 읽는 규칙은 5 WG 가 한 벌을 쓴다 — WG 마다 정리기가 따로 있으면
# 같은 칸이 WG 마다 다른 절로 해소된다.
_FORMAL_COMMON = PROJECT_ROOT / "scripts" / "tsg" / "RAN" / "formal" / "common"
if str(_FORMAL_COMMON) not in sys.path:
    sys.path.append(str(_FORMAL_COMMON))
from cr_clause import clause_candidates  # noqa: E402
import tsg_cr_decision  # noqa: E402 — TSG 회의가 팩 안 CR 마다 내린 판정
from section_index_guard import require_complete_section_index  # noqa: E402
sys.path.insert(0, str(_FORMAL_COMMON / "phase-4"))
from cr_section_index import SectionIndex, _REL_NUM_RE, rel_num  # noqa: E402

PARSED_DIR = PROJECT_ROOT / "ontology" / "output" / "tsg" / "RAN" / "formal" / "parsed_cr" / "RAN1"
INSTANCES_DIR = PROJECT_ROOT / "ontology" / "output" / "tsg" / "RAN" / "formal" / "instances"
OUTPUT_DIR = INSTANCES_DIR / "phase-4" / "RAN1"
LOG_DIR = PROJECT_ROOT / "logs" / "tsg" / "RAN" / "formal" / "RAN1" / "phase-4"

# specTitle 매핑 파일 (Phase-1/4/5 공통 사용)
SPEC_TITLES_FILE = PROJECT_ROOT / "ontology" / "input" / "spec_titles.json"


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
            logging.FileHandler(LOG_DIR / "03_generate_cr_jsonld.log", mode="w"),
        ],
    )


log = logging.getLogger(__name__)


# === JSON-LD Context ===
# Phase-1 패턴 준수: Object Property는 @type: @id로 선언

CRPACK_CONTEXT = {
    "@vocab": "https://w3id.org/spectra#",
    "tdoc": "https://w3id.org/spectra#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "hasCR": {"@id": "tdoc:hasCR", "@type": "@id"},
}

CR_EXTENSION_CONTEXT = {
    "@vocab": "https://w3id.org/spectra#",
    "tdoc": "https://w3id.org/spectra#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "belongsToCRPack": {"@id": "tdoc:belongsToCRPack", "@type": "@id"},
    "affectsCoreSpec": {"@id": "tdoc:affectsCoreSpec", "@type": "@id"},
    "affectsTestSpec": {"@id": "tdoc:affectsTestSpec", "@type": "@id"},
    "affectsOMSpec": {"@id": "tdoc:affectsOMSpec", "@type": "@id"},
    "modifiesSection": {"@id": "tdoc:modifiesSection", "@type": "@id"},
}

SECTION_EXT_CONTEXT = {
    "@vocab": "https://w3id.org/spectra#",
    "tdoc": "https://w3id.org/spectra#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "modifiedByCR": {"@id": "tdoc:modifiedByCR", "@type": "@id"},
}

SPEC_DYNAMIC_CONTEXT = {
    "@vocab": "https://w3id.org/spectra#",
    "tdoc": "https://w3id.org/spectra#",
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

def load_graph(path: Path) -> list:
    """JSON-LD 파일의 `@graph` 목록을 돌려준다.

    이 단계의 Phase-1/3 입력은 모두 필수다. `@graph` 가 없거나 목록이 아닌데 빈 목록으로 넘어가면
    모든 Spec 이 동적 Spec 으로, 모든 CR 이 backfill 로 잡히고 절 매칭이 모두 빠지는데도 오류가
    나지 않는다. 그래서 여기서 멈춘다.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    graph = data.get("@graph") if isinstance(data, dict) else None
    if not isinstance(graph, list):
        raise SystemExit(f"JSON-LD 의 @graph 목록을 읽지 못함: {path}")
    return graph


def load_phase1_crs() -> set[str]:
    """Phase-1 tdocs.jsonld에서 CR의 tdocNumber 집합 로드."""
    path = INSTANCES_DIR / "phase-1" / "RAN1" / "tdocs.jsonld"
    cr_tdocs = set()
    for item in load_graph(path):
        tdoc_type = item.get("@type", "")
        if tdoc_type in ("tdoc:CR", "tdoc:Tdoc"):
            tdoc_num = item.get("tdoc:tdocNumber", "")
            if tdoc_num:
                cr_tdocs.add(tdoc_num)
    return cr_tdocs


def load_phase1_specs() -> set[str]:
    """Phase-1 specs.jsonld에서 Spec 번호 집합 로드."""
    path = INSTANCES_DIR / "phase-1" / "RAN1" / "specs.jsonld"
    specs = set()
    for item in load_graph(path):
        spec_num = item.get("tdoc:specNumber", "")
        if spec_num:
            specs.add(spec_num)
    return specs








def load_phase3_sections() -> SectionIndex:
    """Phase-3 release-aware sections.jsonld에서 SectionIndex 로드.

    Note: Phase-3는 @vocab context를 사용하므로 키가 'sectionId' (prefix 없음).
    """
    path = INSTANCES_DIR / "phase-3" / "RAN1" / "release-aware" / "sections.jsonld"
    entries = []
    for item in load_graph(path):
        # Phase-3는 @vocab 사용 → prefix 없는 키
        sid = item.get("sectionId", "") or item.get("tdoc:sectionId", "")
        secnum = item.get("sectionNumber", "") or item.get("tdoc:sectionNumber", "")
        if sid and secnum != "":
            entries.append((sid, secnum))
    # 덮이거나 일부만 남은 색인이면 CR 의 절 간선이 오류 없이 빠진다. Phase-3 파서의 절 수보다 적으면 멈춘다.
    require_complete_section_index("RAN1", (sid for sid, _ in entries), str(path))
    return SectionIndex(entries)


# === clausesAffected → Section 매칭 ===

def parse_clauses_to_sections(spec_number: str | None, clauses_text: str | None,
                               section_index: SectionIndex,
                               release: str | None) -> list[str]:
    """clausesAffected 문자열을 CR release 기준 release-키 Section URI로 해소.

    칸에서 절 번호를 읽는 규칙은 `cr_clause.clause_candidates` 가 정한다. 절마다 후보를 차례로
    찾아 처음 걸린 Section 하나만 잇는다.
    """
    if not spec_number or not clauses_text:
        return []

    matched_sections = []
    for candidates in clause_candidates(clauses_text):
        for secnum in candidates:
            sid = section_index.resolve(spec_number, secnum, release)
            if sid:
                matched_sections.append(section_uri(sid))
                break

    return list(dict.fromkeys(matched_sections))


# === JSON-LD 생성 ===

def spec_key(spec: str) -> str:
    """Cover 셀(`38.211`)과 파일명(`38211`)의 spec 표기를 한 형태로 맞춘다."""
    return spec.replace(".", "").replace(" ", "").lower()


def generate_crpacks(cover_data: dict, cr_docs: dict, phase1_crs: set[str]) -> list[dict]:
    """CRPack 인스턴스 생성.

    팩 소속의 출처는 둘이다 — Cover 표의 CR 행과, CR 문서가 놓인 팩 디렉토리(`cr_pack_id`,
    CR 확장의 belongsToCRPack 이 된다). 팩과 hasCR 을 Cover 만으로 만들면 Cover 셀이 어긋난
    팩의 CR 이 belongsToCRPack 으로 없는 팩(또는 hasCR 이 빈 팩)을 가리킨다. 그래서 두 출처의
    합집합으로 만든다.

    같은 CR 이 두 팩에 실리는 일이 있다(한 팩의 Cover 에 실렸는데 CR 문서는 다른 팩 디렉토리에
    있는 경우). Spec Step 6 §4 는 belongsToCRPack 을 Functional(0..1)로 두므로 소속 팩은 CR 마다 하나다 —
    CR 문서의 `cr_pack_id` 가 있으면 그것, 없으면 그 CR 을 싣는 첫 팩이다. hasCR 은 이 소속의
    역관계만 싣는다. Cover 행 가운데 같은 팩 디렉토리의 CR 파일과 (spec, CR 번호)가 같은데 Tdoc
    번호가 다르고 그 Tdoc 이 팩 안의 파일도 아닌 행은 Cover 의 오타이므로 소속 근거로 쓰지 않는다.

    Spec §11.1 무결성 검증: hasCR 최소 1개 · hasCR 대상 CR 의 Phase-1 존재는 오류 로그로 다룬다.
    hasCR 의 cardinality 가 1..* 이므로 소속 CR 이 0건인 Pack 은 만들지 않고 오류 로그에만 남긴다
    (Cover 도 WG CR 파일도 없이 RP 문서 자체가 CR 인 디렉토리가 여기에 해당한다).
    """
    instances = []
    empty_packs = []
    not_in_phase1 = 0

    dir_members: dict[str, list[str]] = {}
    dir_keys: dict[str, set[tuple[str, str]]] = {}
    for cr in cr_docs.get("cr_documents", []):
        if cr.get("cr_pack_id") and cr.get("tdoc_number"):
            dir_members.setdefault(cr["cr_pack_id"], []).append(cr["tdoc_number"])
            m = re.search(r"_CR(\d+)", Path(cr.get("source_path") or "").name, re.I)
            if m and cr.get("spec_number"):
                dir_keys.setdefault(cr["cr_pack_id"], set()).add(
                    (spec_key(cr["spec_number"]), m.group(1).zfill(4)))
    packs = list(cover_data.get("crpacks", []))
    covered = {p["cr_pack_id"] for p in packs}
    packs += [{"cr_pack_id": pid, "cr_entries": []} for pid in sorted(dir_members) if pid not in covered]

    def cover_tdocs(pack: dict) -> list[str]:
        pid = pack["cr_pack_id"]
        keys, files = dir_keys.get(pid, set()), set(dir_members.get(pid, []))
        return [e["tdoc_number"] for e in pack.get("cr_entries", [])
                if e.get("tdoc_number")
                and (e["tdoc_number"] in files
                     or (spec_key(e.get("spec") or ""), str(e.get("cr_number") or "").zfill(4)) not in keys)]

    owner: dict[str, str] = {t: pid for pid, ts in dir_members.items() for t in ts}
    # CR 문서가 없어 Cover 에만 실린 CR 은 TSG 회의 판정이 앞서는 팩에 둔다(같으면 Cover 차례).
    # 주의: Cover 는 CR 시트가 그 팩에 두지 않은 CR 도 적는다. RAN1 RAN#108 RP-251576 의 Cover 는
    # `R1-2505066`(36.211 CR0577)을 적지만 CR 시트의 RP-251576 행에는 그 CR 이 없다. 가장 앞선 판정이
    # `not listed` 인 CR 은 어느 팩에도 두지 않는다. 두면 회의가 다루지 않은 CR 이 팩에 붙는다.
    cover_only: dict[str, list[str]] = {}
    for pack in packs:
        for t in cover_tdocs(pack):
            if t not in owner:
                cover_only.setdefault(t, []).append(pack["cr_pack_id"])
    unlisted: list[tuple[str, str]] = []
    for t, pids in cover_only.items():
        ranks = {p: tsg_cr_decision.rank(t, p) for p in pids}
        pid = next(p for p in pids if ranks[p] == min(ranks.values()))
        if tsg_cr_decision.decision(t, pid)[0] in (tsg_cr_decision.NOT_LISTED, tsg_cr_decision.NOT_A_PACK):
            unlisted.append((pid, t))
            continue
        owner[t] = pid
    if unlisted:
        log.warning(f"  Cover 에만 실리고 CR 시트의 그 팩에 없는 CR: {len(unlisted)}개 (예: {unlisted[:5]})")

    for pack in packs:
        cr_pack_id = pack["cr_pack_id"]

        tdocs = cover_tdocs(pack) + dir_members.get(cr_pack_id, [])
        tdocs = [t for t in dict.fromkeys(tdocs) if owner.get(t) == cr_pack_id]
        not_in_phase1 += sum(1 for t in tdocs if t not in phase1_crs)
        cr_refs = [cr_uri(t) for t in tdocs]
        if not cr_refs:
            empty_packs.append(cr_pack_id)
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

    if empty_packs:
        log.error(f"  hasCR 최소 1개 위반으로 생성하지 않은 CRPack: {len(empty_packs)}개 (예: {empty_packs[:5]})")
    if not_in_phase1:
        log.error(f"  hasCR 대상 CR 중 Phase-1 부재: {not_in_phase1}개")
    return instances


def generate_cr_extensions(cr_docs: dict, phase1_crs: set[str],
                           phase1_specs: set[str],
                           section_ids: SectionIndex) -> tuple[list[dict], list[str]]:
    """CR 확장 속성 인스턴스 생성.

    반환: (cr_extension_instances, new_spec_numbers)
    """
    instances = []
    new_specs_needed = set()
    matched_phase1 = 0
    unmatched = 0

    for cr in cr_docs.get("cr_documents", []):
        tdoc_number = cr.get("tdoc_number", "")
        if not tdoc_number:
            continue

        # Phase-1 매칭 확인
        is_phase1 = tdoc_number in phase1_crs
        if is_phase1:
            matched_phase1 += 1
        else:
            unmatched += 1

        instance = {
            "@id": cr_uri(tdoc_number),
            "@type": "tdoc:CR",
        }

        # Data Properties
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

        # belongsToCRPack
        if cr.get("cr_pack_id"):
            instance["belongsToCRPack"] = crpack_uri(cr["cr_pack_id"])
            has_data = True

        # affectsSpec (Cross-Spec)
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

        # modifiesSection
        spec_number = cr.get("spec_number")
        clauses = cr.get("clauses_affected")
        section_refs = parse_clauses_to_sections(spec_number, clauses, section_ids,
                                                 cr.get("release"))
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
    # section_uri → [cr_uris]
    section_to_crs: dict[str, list[str]] = {}

    for cr_ext in cr_extensions:
        cr_id = cr_ext["@id"]
        mod_sections = cr_ext.get("modifiesSection", [])
        if isinstance(mod_sections, str):
            mod_sections = [mod_sections]

        for sec_uri in mod_sections:
            section_to_crs.setdefault(sec_uri, []).append(cr_id)

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
    """specTitle 매핑 파일 로드 (specNumber → specTitle)

    빈 사전으로 넘어가면 Spec 노드가 모두 제목 없이 나가므로, 파일이 없거나 깨졌으면 멈춘다.
    """
    try:
        with open(SPEC_TITLES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)['specs']
    except (OSError, ValueError, KeyError) as e:
        raise SystemExit(f"specTitle 매핑 파일을 읽지 못함: {SPEC_TITLES_FILE}: {e}") from e


def generate_dynamic_specs(new_spec_numbers: list[str]) -> list[dict]:
    """Phase-1에 없는 Spec의 동적 생성 인스턴스.

    specTitle 매핑 파일에서 제목을 조회하여 추가합니다.
    """
    # specTitle 매핑 로드
    spec_titles = load_spec_titles()
    title_found = 0

    instances = []
    for spec_num in new_spec_numbers:
        instance = {
            "@id": spec_uri(spec_num),
            "@type": "tdoc:Spec",
            "tdoc:specNumber": spec_num,
        }

        # specTitle 추가 (매핑에 있는 경우)
        if spec_num in spec_titles:
            instance["tdoc:specTitle"] = spec_titles[spec_num]
            title_found += 1

        instances.append(instance)

    log.info(f"    specTitle 매핑: {title_found}/{len(new_spec_numbers)}개 적용")
    return instances


# === 메인 ===

def main():
    configure_logging()
    log.info("=" * 60)
    log.info("Phase-4 Step 1-3: JSON-LD 인스턴스 생성 시작")
    log.info("=" * 60)

    # 입력 데이터 로드
    log.info("입력 데이터 로드...")

    with open(PARSED_DIR / "cover_sheets.json", encoding="utf-8") as f:
        cover_data = json.load(f)
    log.info(f"  Cover Sheets: {cover_data['metadata']['unique_crpacks']} CRPacks")

    with open(PARSED_DIR / "cr_documents.json", encoding="utf-8") as f:
        cr_docs = json.load(f)
    # CR 문서 목록은 필수 입력이다. 키가 없거나 목록이 아닌데 빈 목록으로 넘어가면 CR 확장이 0건이고
    # 팩은 Cover 만으로 만들어진 채 정상 종료한다. 그래서 여기서 멈춘다.
    if not isinstance(cr_docs, dict) or not isinstance(cr_docs.get("cr_documents"), list):
        raise SystemExit(f"cr_documents.json 의 cr_documents 목록을 읽지 못함: {PARSED_DIR / 'cr_documents.json'}")
    log.info(f"  CR Documents: {cr_docs['metadata']['unique_crs']} CRs")

    # Phase-1/3 참조 데이터 로드
    log.info("Phase-1/3 참조 데이터 로드...")
    phase1_crs = load_phase1_crs()
    log.info(f"  Phase-1 Tdoc(CR·Tdoc 타입): {len(phase1_crs)}개")

    # Phase-1 이 덮지 못한 CR 도 로더가 MERGE 로 backfill 한다 — 여기서는 그 규모만 센다.
    cr_doc_tdocs = {cr["tdoc_number"] for cr in cr_docs.get("cr_documents", []) if cr.get("tdoc_number")}
    log.info(f"  Phase-4 backfill CR: {len(cr_doc_tdocs - phase1_crs)}개 (Phase-1 미커버)")

    phase1_specs = load_phase1_specs()
    log.info(f"  Phase-1 Spec: {len(phase1_specs)}개")

    section_ids = load_phase3_sections()
    log.info(f"  Phase-3 Section(release-키): {len(section_ids.sid_by)}개")

    # === 1. CRPack 인스턴스 ===
    log.info("\n1. CRPack 인스턴스 생성...")
    crpack_instances = generate_crpacks(cover_data, cr_docs, phase1_crs)
    log.info(f"  CRPack: {len(crpack_instances)}개")

    # === 2. CR 확장 인스턴스 ===
    log.info("\n2. CR 확장 인스턴스 생성...")
    cr_ext_instances, new_specs = generate_cr_extensions(
        cr_docs, phase1_crs, phase1_specs, section_ids
    )
    log.info(f"  CR extensions: {len(cr_ext_instances)}개")
    log.info(f"  Section resolve 통계: {dict(sorted(section_ids.stats.items()))}")

    # === 3. Section 역관계 인스턴스 ===
    log.info("\n3. Section modifiedByCR 역관계 생성...")
    section_ext_instances = generate_section_extensions(cr_ext_instances)
    log.info(f"  Section extensions: {len(section_ext_instances)}개")

    # === 4. 동적 Spec 인스턴스 ===
    log.info("\n4. 동적 Spec 인스턴스 생성...")
    spec_dynamic_instances = generate_dynamic_specs(new_specs)
    log.info(f"  Dynamic Spec: {len(spec_dynamic_instances)}개")

    # === JSON-LD 출력 ===
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    outputs = [
        ("crpacks.jsonld", CRPACK_CONTEXT, crpack_instances),
        ("cr_extensions.jsonld", CR_EXTENSION_CONTEXT, cr_ext_instances),
        ("section_extensions.jsonld", SECTION_EXT_CONTEXT, section_ext_instances),
        ("spec_dynamic.jsonld", SPEC_DYNAMIC_CONTEXT, spec_dynamic_instances),
    ]

    # Validate every document before replacing any member of the output batch.
    prepared = [(filename, instances, json.dumps(canonical_document(
        {"@context": context, "@graph": instances}, wg='RAN1'),
        ensure_ascii=False, indent=2)) for filename, context, instances in outputs]
    publish_text_set([(OUTPUT_DIR / filename, text) for filename, _, text in prepared])
    for filename, instances, _ in prepared:
        output_path = OUTPUT_DIR / filename

        size_kb = output_path.stat().st_size / 1024
        log.info(f"  {filename}: {len(instances)}개 ({size_kb:.1f} KB)")

    # === 요약 ===
    log.info("\n" + "=" * 60)
    log.info("생성 결과 요약")
    log.info("=" * 60)
    log.info(f"  CRPack: {len(crpack_instances)}개")
    log.info(f"  CR extensions: {len(cr_ext_instances)}개")
    log.info(f"  Section extensions: {len(section_ext_instances)}개")
    log.info(f"  Dynamic Spec: {len(spec_dynamic_instances)}개")
    log.info(f"  총 인스턴스: {len(crpack_instances) + len(cr_ext_instances) + len(section_ext_instances) + len(spec_dynamic_instances)}개")

    return 0


if __name__ == "__main__":
    sys.exit(main())
