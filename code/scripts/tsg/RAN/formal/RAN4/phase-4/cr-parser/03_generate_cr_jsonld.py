#!/usr/bin/env python3
"""
RAN4 Phase-4 Step 1-3: JSON-LD 인스턴스 생성
- 입력: parsed JSON (cover_sheets.json, cr_documents.json) + Phase-1 인스턴스 + Neo4j Section
- 출력: ontology/output/tsg/RAN/formal/instances/phase-4/RAN4/ (4개 파일)

Spec Step 7 §5 · §6 · §11 · §7 (CRPack, CR 확장, Section 역관계, 동적 Spec)

RAN4 고유:
- Phase-3 인스턴스 파일 없음 → Neo4j(port 7690)에서 Section ID 조회
- R4-\\d{7} 패턴 (7자리)
- Spec 번호 접미사: -1, -2, -3 등 (38.101-1, 38.101-3)

URI 패턴 (Phase-1 기존 준수):
- CR: tdoc:{tdocNumber}  (예: tdoc:R4-2502652)
- CRPack: tdoc:crpack/{crPackId}  (예: tdoc:crpack/RP-250233)
- Spec: tdoc:spec/{spec.replace('.','_')}  (예: tdoc:spec/38_133)
- Section: tdoc:section/{sectionId}  (예: tdoc:section/38.133-Rel-18-8.3.12)
"""

import json
import os
import re
import sys
import logging
from pathlib import Path

from neo4j import GraphDatabase

# === 경로 설정 ===
PROJECT_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "common"))
from ontology.jsonld_context import canonical_document  # noqa: E402
from common.atomic_io import publish_text_set  # noqa: E402

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
import tsg_cr_decision  # noqa: E402 — TSG 회의가 팩 안 CR 마다 내린 판정
from section_index_guard import require_complete_section_index  # noqa: E402
sys.path.insert(0, str(_FORMAL_COMMON / "phase-4"))
from cr_section_index import SectionIndex, _REL_NUM_RE, rel_num  # noqa: E402
PARSED_DIR = PROJECT_ROOT / "ontology" / "output" / "tsg" / "RAN" / "formal" / "parsed_cr" / "RAN4"
INSTANCES_DIR = PROJECT_ROOT / "ontology" / "output" / "tsg" / "RAN" / "formal" / "instances"
OUTPUT_DIR = INSTANCES_DIR / "phase-4" / "RAN4"
LOG_DIR = PROJECT_ROOT / "logs" / "tsg" / "RAN" / "formal" / "RAN4" / "phase-4"

SPEC_TITLES_FILE = PROJECT_ROOT / "ontology" / "input" / "spec_titles.json"

# RAN4 Neo4j: port 7690
NEO4J_URI = axis.bolt_uri("RAN4")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = credentials.neo4j_password()


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


# === Phase-1 데이터 로드 ===

def load_graph(path: Path) -> list:
    """JSON-LD 파일의 `@graph` 목록을 돌려준다.

    이 단계의 Phase-1 입력은 모두 필수다. `@graph` 가 없거나 목록이 아닌데 빈 목록으로 넘어가면
    모든 Spec 이 동적 Spec 으로, 모든 CR 이 backfill 로 잡히는데도 오류가 나지 않는다.
    그래서 여기서 멈춘다.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    graph = data.get("@graph") if isinstance(data, dict) else None
    if not isinstance(graph, list):
        raise SystemExit(f"JSON-LD 의 @graph 목록을 읽지 못함: {path}")
    return graph


def load_phase1_crs() -> set[str]:
    """Phase-1 tdocs.jsonld에서 CR의 tdocNumber 집합 로드."""
    path = INSTANCES_DIR / "phase-1" / "RAN4" / "tdocs.jsonld"
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
    path = INSTANCES_DIR / "phase-1" / "RAN4" / "specs.jsonld"
    specs = set()
    for item in load_graph(path):
        spec_num = item.get("tdoc:specNumber", "")
        if spec_num:
            specs.add(spec_num)
    return specs








def load_neo4j_sections() -> SectionIndex:
    """Neo4j(port 7690)에서 release-키 SectionIndex 로드.
    RAN4 Phase-3 인스턴스 파일이 없으므로 Neo4j 직접 조회.
    """
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    entries = []
    try:
        with driver.session() as session:
            result = session.run(
                # Phase-3 가 적재한 절만 과녁이다(BELONGS_TO_SPEC 은 그 적재기만 긋는다). 입력에서 빠졌는데
                # 남의 간선 때문에 보존된 노드까지 읽으면 CR 이 그 노드를 다시 과녁으로 삼아 스스로를 살린다.
                "MATCH (s:Section)-[:BELONGS_TO_SPEC]->(:Spec) RETURN s.sectionId AS sid, s.sectionNumber AS num"
            )
            for record in result:
                sid, num = record["sid"], record["num"]
                if sid and num is not None:
                    entries.append((sid, num))
    finally:
        driver.close()
    # 비었거나 일부만 적재된 그래프면 CR 의 절 간선이 오류 없이 빠진다. Phase-3 파서의 절 수보다 적으면 멈춘다.
    require_complete_section_index("RAN4", (sid for sid, _ in entries),
                                   f"{NEO4J_URI} (:Section)-[:BELONGS_TO_SPEC]->(:Spec)")
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
    """Cover 셀(`38.101-1`)과 파일명(`38101-1`)의 spec 표기를 한 형태로 맞춘다."""
    return spec.replace(".", "").replace(" ", "").lower()


def generate_crpacks(cover_data: dict, cr_docs: dict, phase1_crs: set[str]) -> list[dict]:
    """CRPack 인스턴스 생성.
    Spec §13.1: hasCR 최소 1개. 소속 CR 이 0개인 Pack은 생성하지 않음.

    팩 소속의 출처는 둘이다 — Cover 표의 CR 행과, CR 문서가 놓인 팩 디렉토리(`cr_pack_id`,
    CR 확장의 belongsToCRPack 이 된다). 팩을 만들지 말지를 Cover 만으로 정하면 Cover 셀이
    어긋난 팩이 빠지는데 그 팩의 CR 은 여전히 belongsToCRPack 으로 그 팩을 가리켜, 없는 팩을
    가리키는 참조가 된다. 그래서 두 출처의 합집합으로 팩과 hasCR 을 만든다.

    같은 CR 이 두 팩에 놓이는 일이 있다(묶음 팩의 Cover 에도 실리고 제 단독 팩 디렉토리에도
    있는 경우). Spec Step 6 §3 은 belongsToCRPack 을 Functional(0..1)로 두므로 소속 팩은 CR 마다
    하나로 정한다 — CR 문서의 `cr_pack_id` 가 있으면 그것, 없으면 그 CR 을 싣는 첫 팩이다.
    hasCR 은 이 소속의 역관계만 싣는다. 그래야 hasCR 과 belongsToCRPack 이 서로의 역이 되고,
    다른 팩에 소속이 정해진 CR 만 가진 팩은 소속 CR 0건이 되어 만들지 않는다.

    Cover 행의 Tdoc 번호는 같은 팩 디렉토리의 CR 파일과 (spec, CR 번호)가 같은데 Tdoc 번호가
    다른 경우가 있다 — Cover 의 오타나 revision 이전 번호다. 팩에 실제로 들어 있는 것은 파일이고
    파일명이 spec · CR 번호 · Tdoc 번호를 함께 적으므로, 그런 Cover 행은 소속 근거로 쓰지 않는다.
    쓰면 번호가 가리키는 엉뚱한 Tdoc(논의 문서 · 다른 CR 의 draft)이 팩에 붙는다.
    """
    instances = []
    skipped_empty = 0
    absent: list[str] = []

    dir_members: dict[str, list[str]] = {}
    dir_keys: dict[str, set[tuple[str, str]]] = {}
    for cr in cr_docs.get("documents", []):
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
        keys = dir_keys.get(pack["cr_pack_id"], set())
        return [e["tdoc_number"] for e in pack.get("cr_entries", [])
                if e.get("tdoc_number")
                and (spec_key(e.get("spec") or ""), str(e.get("cr_number") or "").zfill(4)) not in keys]

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
        members = [t for t in dict.fromkeys(tdocs) if owner.get(t) == cr_pack_id]
        absent += [t for t in members if t not in phase1_crs]
        cr_refs = [cr_uri(t) for t in members if t in phase1_crs]

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

    # Spec §13.1 무결성 검증: 두 위반 모두 오류 로그로 남긴다
    if skipped_empty:
        log.error(f"  hasCR 최소 1개 위반으로 생성하지 않은 CRPack: {skipped_empty}개")
    if absent:
        log.error(f"  hasCR 에서 뺀 CR(Phase-1 에도 CR 문서에도 없음): {len(absent)}개 (예: {absent[:5]})")

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
    log.info(f"  신규 Spec 필요: {len(new_specs_needed)}개 ({sorted(new_specs_needed)[:20]}...)")

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
    """specTitle 매핑 파일 로드 (specNumber → specTitle)

    빈 사전으로 넘어가면 Spec 노드가 모두 제목 없이 나가므로, 파일이 없거나 깨졌으면 멈춘다.
    """
    try:
        with open(SPEC_TITLES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)['specs']
    except (OSError, ValueError, KeyError) as e:
        raise SystemExit(f"specTitle 매핑 파일을 읽지 못함: {SPEC_TITLES_FILE}: {e}") from e


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
    configure_logging()
    log.info("=" * 60)
    log.info("RAN4 Phase-4 Step 1-3: JSON-LD 인스턴스 생성 시작")
    log.info("=" * 60)

    log.info("입력 데이터 로드...")

    with open(PARSED_DIR / "cover_sheets.json", encoding="utf-8") as f:
        cover_data = json.load(f)
    log.info(f"  Cover Sheets: {cover_data['metadata']['unique_crpacks']} CRPacks")

    with open(PARSED_DIR / "cr_documents.json", encoding="utf-8") as f:
        cr_docs = json.load(f)
    # CR 문서 목록은 필수 입력이다. 키가 없거나 목록이 아닌데 빈 목록으로 넘어가면 CR 확장이 0건이고
    # 팩은 Cover 만으로 만들어진 채 정상 종료한다. 그래서 여기서 멈춘다.
    if not isinstance(cr_docs, dict) or not isinstance(cr_docs.get("documents"), list):
        raise SystemExit(f"cr_documents.json 의 documents 목록을 읽지 못함: {PARSED_DIR / 'cr_documents.json'}")
    log.info(f"  CR Documents: {cr_docs['metadata']['unique_crs']} CRs")

    log.info("Phase-1 참조 데이터 로드...")
    phase1_crs = load_phase1_crs()
    log.info(f"  Phase-1 Tdoc(CR·Tdoc 타입): {len(phase1_crs)}개")
    # 매칭 통계는 보강 전 집합으로 센다 — 보강한 집합으로 세면 미매칭이 정의상 0 이 된다.
    phase1_only = set(phase1_crs)

    # 로더는 CR 확장을 MERGE 하므로 Phase-1 이 덮지 못한 CR 도 노드가 된다. 그래서 CR 문서의
    # tdoc_number 를 hasCR 대상 집합에 더한다 — 이 집합 밖의 Cover 행 번호만 hasCR 에서 빠진다.
    cr_doc_tdocs = {cr.get("tdoc_number", "") for cr in cr_docs.get("documents", []) if cr.get("tdoc_number")}
    phase4_additional = cr_doc_tdocs - phase1_crs
    phase1_crs = phase1_crs | cr_doc_tdocs
    log.info(f"  Phase-4 backfill CR: {len(phase4_additional)}개 (Phase-1 미커버)")
    log.info(f"  확장 후 CR set: {len(phase1_crs)}개")

    phase1_specs = load_phase1_specs()
    log.info(f"  Phase-1 Spec: {len(phase1_specs)}개")

    log.info("Neo4j Section 데이터 로드 (port 7690)...")
    section_ids = load_neo4j_sections()
    log.info(f"  Neo4j Section(release-키): {len(section_ids.sid_by)}개")

    # 1. CRPack
    log.info("\n1. CRPack 인스턴스 생성...")
    crpack_instances = generate_crpacks(cover_data, cr_docs, phase1_crs)
    log.info(f"  CRPack: {len(crpack_instances)}개")

    # 2. CR 확장
    log.info("\n2. CR 확장 인스턴스 생성...")
    cr_ext_instances, new_specs = generate_cr_extensions(
        cr_docs, phase1_only, phase1_specs, section_ids
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

    # Validate every document before replacing any member of the output batch.
    prepared = [(filename, instances, json.dumps(canonical_document(
        {"@context": context, "@graph": instances}, wg='RAN4'),
        ensure_ascii=False, indent=2)) for filename, context, instances in outputs]
    publish_text_set([(OUTPUT_DIR / filename, text) for filename, _, text in prepared])
    for filename, instances, _ in prepared:
        output_path = OUTPUT_DIR / filename

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
