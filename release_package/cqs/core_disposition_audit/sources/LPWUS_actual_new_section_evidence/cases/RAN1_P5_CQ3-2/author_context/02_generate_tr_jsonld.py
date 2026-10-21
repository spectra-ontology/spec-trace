#!/usr/bin/env python3
"""
Phase-5 Step-1: JSON-LD 인스턴스 생성
- TechnicalReport 인스턴스 생성
- TRImpact 인스턴스 생성
- 동적 Spec 인스턴스 생성 (Phase-1에 없는 경우). Section 은 만들지 않는다(create_dynamic_instances 참조)

Spec 참조: docs/tsg/RAN/formal/RAN1/phase-5/design-spec/tdoc_ontology_specs(TR).md Step 7
"""

from __future__ import annotations

import json
import csv
import sys
from pathlib import Path
from datetime import datetime

# 경로 설정
PROJECT_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
_FORMAL_COMMON = PROJECT_ROOT / "scripts" / "tsg" / "RAN" / "formal" / "common"
if str(_FORMAL_COMMON) not in sys.path:
    sys.path.append(str(_FORMAL_COMMON))
from section_index_guard import require_complete_section_index  # noqa: E402
PARSED_DIR = PROJECT_ROOT / "ontology" / "output" / "tsg" / "RAN" / "formal" / "parsed_tr" / "RAN1"
IMPACT_CSV = PROJECT_ROOT / "ontology" / "input" / "tsg" / "RAN" / "formal" / "TR" / "RAN1" / "tr_impact_mapping.csv"
OUTPUT_DIR = PROJECT_ROOT / "ontology" / "output" / "tsg" / "RAN" / "formal" / "instances" / "phase-5" / "RAN1"

# Phase-1/3 인스턴스 경로 (동적 생성 확인용)
PHASE1_DIR = PROJECT_ROOT / "ontology" / "output" / "tsg" / "RAN" / "formal" / "instances" / "phase-1" / "RAN1"
PHASE3_DIR = PROJECT_ROOT / "ontology" / "output" / "tsg" / "RAN" / "formal" / "instances" / "phase-3" / "RAN1"

# specTitle 매핑 파일 (Phase-1/4/5 공통 사용)
SPEC_TITLES_FILE = PROJECT_ROOT / "ontology" / "input" / "spec_titles.json"

# JSON-LD Context
CONTEXT = {
    "@vocab": "http://3gpp.org/ontology/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "trNumber": {"@type": "xsd:string"},
    "trVersion": {"@type": "xsd:string"},
    "trTitle": {"@type": "xsd:string"},
    "trStatus": {"@type": "xsd:string"},
    "scope": {"@type": "xsd:string"},
    "conclusions": {"@type": "xsd:string"},
    "studyItemRpNumber": {"@type": "xsd:string"},
    "workItemRpNumber": {"@type": "xsd:string"},
    "targetRelease": {"@type": "@id"},
    "trImpactId": {"@type": "xsd:string"},
    "impactType": {"@type": "xsd:string"},
    "affectedSection": {"@type": "xsd:string"},
    "impactDescription": {"@type": "xsd:string"},
    "hasTRImpact": {"@type": "@id"},
    "impactOfTR": {"@type": "@id"},
    "impactsSpec": {"@type": "@id"},
    "impactsSection": {"@type": "@id"},
    "specNumber": {"@type": "xsd:string"},
    "sectionNumber": {"@type": "xsd:string"},
    "referencesTR": {"@type": "@id"}
}


def load_tr_metadata() -> list:
    """파싱된 TR 메타데이터 로드"""
    metadata_file = PARSED_DIR / "tr_metadata.json"
    with open(metadata_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['technicalReports']


def _check_columns(row: dict, path) -> None:
    """열 수가 머리줄보다 많은 행을 멈춘다. 따옴표 없는 쉼표가 낀 행은 csv 가 남는 칸을
    None 키로 떼어 두므로, 그대로 읽으면 마지막 열(impactDescription)이 잘린 채 나간다."""
    if None in row:
        raise SystemExit(f"{path}: 머리줄보다 열이 많은 행(따옴표 없는 쉼표?) — {row}")


def load_impact_mapping() -> list:
    """TR-TS 영향 관계 CSV 로드"""
    impacts = []
    with open(IMPACT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            _check_columns(row, IMPACT_CSV)
            impacts.append(row)
    return impacts


def generate_tr_id(tr_number: str) -> str:
    """
    TechnicalReport ID 생성
    Spec Step 7 §4.3: tr:{trNumber} (예: tr:38.769)
    """
    return f"tr:{tr_number}"


def generate_tr_impact_id(tr_number: str, spec_number: str, section_number: str = None) -> str:
    """
    TRImpact ID 생성
    Spec Step 7 §7.2: trimpact:{trNumber}-{specNumber}[-S{sectionNumber}]
    접두어 trimpact: 는 Spec Step 7 §4.3 의 impact: 와 다르다.
    """
    base_id = f"trimpact:{tr_number}-{spec_number}"
    if section_number:
        base_id += f"-S{section_number}"
    return base_id


def generate_release_id(release: str) -> str:
    """Release ID 생성 (Phase-1 패턴 재사용)"""
    if not release:
        return None
    # Rel-18 -> release:Rel-18
    return f"release:{release}"


def generate_spec_id(spec_number: str) -> str:
    """Spec ID 생성 (Phase-1 패턴 재사용)"""
    return f"spec:{spec_number}"


def _rel_num(release: str) -> int:
    """"Rel-19" → 19. 파싱 불가 시 -1."""
    try:
        return int(release.split("Rel-")[-1])
    except (ValueError, IndexError):
        return -1


class SectionIndex:
    """(spec, sectionNumber) → 최신 release sectionId 매핑.

    release-aware Section 코퍼스(Phase-3 release-aware/sections.jsonld)에서
    로드한다. TRImpact → Section(IMPACTS_SECTION) 관계는
    migrate_to_release_aware.py 규약(release_source="latest")을 따라
    impacted Section을 해당 spec의 최신 release variant로 해석한다.
    """

    def __init__(self, entries: list[tuple]):
        # entries: (spec, secnum, release, section_id)
        self._by_key: dict[tuple, list[tuple]] = {}
        for spec, secnum, release, sid in entries:
            self._by_key.setdefault((spec, str(secnum)), []).append((_rel_num(release), sid))
        for key in self._by_key:
            self._by_key[key].sort(key=lambda t: t[0], reverse=True)
        self.stats = {"resolved": 0, "unresolved": 0}

    def resolve_latest(self, spec: str, secnum: str) -> str | None:
        """(spec, secnum)의 최신 release sectionId(release-키) 반환. 없으면 None."""
        variants = self._by_key.get((spec, str(secnum)))
        if not variants:
            self.stats["unresolved"] += 1
            return None
        self.stats["resolved"] += 1
        return variants[0][1]


def load_release_section_index() -> SectionIndex:
    """Phase-3 release-aware sections.jsonld에서 SectionIndex 로드."""
    path = PHASE3_DIR / "release-aware" / "sections.jsonld"
    entries: list[tuple] = []
    # 파일 부재도 아래 하한 검사에서 0 절로 멈춘다. 빈 인덱스로 진행하면 impactsSection 이 모두
    # unresolved 로 빠지는데도 정상 종료한다.
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        # 파일이 있는데 `@graph` 가 목록이 아니면 빈 인덱스로 두지 않고 멈춘다.
        graph = data.get("@graph") if isinstance(data, dict) else None
        if not isinstance(graph, list):
            raise SystemExit(f"JSON-LD 의 @graph 목록을 읽지 못함: {path}")
        for item in graph:
            if item.get("@type") not in ("Section", "tdoc:Section"):
                continue
            sid = item.get("sectionId") or item.get("tdoc:sectionId")
            secnum = item.get("sectionNumber", item.get("tdoc:sectionNumber", ""))
            belongs = item.get("belongsToSpec", item.get("tdoc:belongsToSpec", ""))
            # belongsToSpec: "tdoc:spec/38_211/Rel-19" → spec="38.211", release="Rel-19"
            parts = belongs.replace("tdoc:spec/", "").split("/")
            if not sid or secnum == "" or len(parts) < 2:
                continue
            entries.append((parts[0].replace("_", "."), str(secnum), parts[1], sid))
    # 덮이거나 일부만 남은 색인이면 impactsSection 이 오류 없이 빠진다. Phase-3 파서의 절 수보다 적으면 멈춘다.
    require_complete_section_index("RAN1", (e[3] for e in entries), str(path))
    return SectionIndex(entries)


# main()에서 1회 초기화. release-aware 해석 실패분은 ghost 생성 없이 건너뛴다.
SECTION_INDEX: SectionIndex | None = None


def generate_section_id(spec_number: str, section_number: str) -> str | None:
    """impacted Section을 release-키 sectionId(`section:{spec}-Rel-NN-{num}`)로 해석.

    SECTION_INDEX(최신 release 매핑)로 해석. 해석 불가 시 None을 반환하여
    legacy(비-release-키) ghost Section/dangling 참조 생성을 방지한다.
    """
    if SECTION_INDEX is None:
        return None
    sid = SECTION_INDEX.resolve_latest(spec_number, section_number)
    return f"section:{sid}" if sid else None


def create_technical_report_instance(tr: dict, impact_ids: list) -> dict:
    """
    TechnicalReport JSON-LD 인스턴스 생성

    Spec §6.1 TechnicalReport 인스턴스 생성:
    - 필수: trNumber, trVersion, trTitle, trStatus
    - 선택: scope, conclusions, targetRelease
    """
    instance = {
        "@id": generate_tr_id(tr['trNumber']),
        "@type": "TechnicalReport",
        "trNumber": tr['trNumber'],
        "trVersion": tr['trVersion'],
        "trTitle": tr['trTitle'],
        "trStatus": tr['trStatus']
    }

    # 선택 속성
    if tr.get('scope'):
        instance['scope'] = tr['scope']

    if tr.get('conclusions'):
        instance['conclusions'] = tr['conclusions']

    if tr.get('targetRelease'):
        instance['targetRelease'] = generate_release_id(tr['targetRelease'])

    # Spec §3.1 #7~#8: RP 번호
    if tr.get('studyItemRpNumber'):
        instance['studyItemRpNumber'] = tr['studyItemRpNumber']
    if tr.get('workItemRpNumber'):
        instance['workItemRpNumber'] = tr['workItemRpNumber']

    # hasTRImpact 관계 (NoChange가 아닌 경우만)
    if impact_ids:
        instance['hasTRImpact'] = impact_ids

    # referencesTR 관계 (TTL: referencesTR / referencedByTR)
    refs = tr.get('referencesTR', [])
    if refs:
        instance['referencesTR'] = [generate_tr_id(ref) for ref in refs]

    return instance


def create_tr_impact_instance(impact: dict) -> dict:
    """
    TRImpact JSON-LD 인스턴스 생성

    Spec §7.2 TRImpact 인스턴스 생성:
    - NoChange인 경우 TRImpact 생성 안 함
    - 필수: trImpactId, impactType, impactOfTR, impactsSpec
    - 선택: impactsSection, affectedSection, impactDescription
    """
    tr_number = impact['trNumber']
    impact_type = impact['impactType']
    spec_number = impact.get('impactsSpec', '')
    section_number = impact.get('impactsSection', '')

    # NoChange는 TRImpact 생성 안 함
    if impact_type == 'NoChange':
        return None
    # impactsSpec 은 필수다. 비어 있으면 "spec:" 처럼 대상 없는 참조가 나가므로 멈춘다
    if not spec_number:
        raise SystemExit(f"impactsSpec 이 빈 {impact_type} 행: {impact}")

    # ID 생성
    impact_id = generate_tr_impact_id(tr_number, spec_number, section_number)

    instance = {
        "@id": impact_id,
        "@type": "TRImpact",
        "trImpactId": impact_id.replace("trimpact:", ""),
        "impactType": impact_type,
        "impactOfTR": generate_tr_id(tr_number),
        "impactsSpec": generate_spec_id(spec_number)
    }

    # 선택 속성: impactsSection은 release-aware Section으로 해석될 때만 설정한다
    # (해석 불가 시 legacy 비-release-키 dangling 참조 방지). 원시 절 번호인
    # affectedSection은 trace용으로 항상 보존한다.
    if section_number:
        resolved_section = generate_section_id(spec_number, section_number)
        if resolved_section:
            instance['impactsSection'] = resolved_section
        instance['affectedSection'] = section_number

    if impact.get('impactDescription'):
        instance['impactDescription'] = impact['impactDescription']

    return instance


def check_existing_specs() -> set:
    """Phase-1에 존재하는 Spec 번호 집합 로드"""
    existing = set()

    specs_file = PHASE1_DIR / "specs.jsonld"
    if specs_file.exists():
        try:
            with open(specs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            graph = data.get('@graph', [data])
            for item in graph:
                # Check both with and without prefix
                spec_num = item.get('specNumber') or item.get('tdoc:specNumber', '')
                if spec_num:
                    existing.add(spec_num)
        except Exception as e:
            print(f"   Warning: Error loading specs: {e}")

    return existing


def load_spec_titles() -> dict[str, str]:
    """specTitle 매핑 파일 로드 (specNumber → specTitle)

    빈 사전으로 넘어가면 Spec 노드가 모두 제목 없이 나가므로, 파일이 없거나 깨졌으면 멈춘다.
    """
    try:
        with open(SPEC_TITLES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)['specs']
    except (OSError, ValueError, KeyError) as e:
        raise SystemExit(f"specTitle 매핑 파일을 읽지 못함: {SPEC_TITLES_FILE}: {e}") from e


def create_dynamic_instances(impacts: list, existing_specs: set) -> list:
    """
    동적 Spec 인스턴스 생성

    Spec §5.1: Phase-1에 없는 Spec 최소 인스턴스 생성. specTitle 매핑 파일에 제목이
    있으면 붙인다. Spec §5.2 의 동적 Section 은 만들지 않는다(아래 주석).
    """
    # specTitle 매핑 로드
    spec_titles = load_spec_titles()
    title_found = 0

    dynamic = []
    created_specs = set()

    for impact in impacts:
        if impact['impactType'] == 'NoChange':
            continue

        spec_number = impact.get('impactsSpec', '')

        # 동적 Spec 생성
        if spec_number and spec_number not in existing_specs and spec_number not in created_specs:
            spec_instance = {
                "@id": generate_spec_id(spec_number),
                "@type": "Spec",
                "specNumber": spec_number,
                "_dynamicCreated": True,
                "_createdBy": "Phase-5"
            }

            # specTitle 추가 (매핑에 있는 경우)
            if spec_number in spec_titles:
                spec_instance["specTitle"] = spec_titles[spec_number]
                title_found += 1

            dynamic.append(spec_instance)
            created_specs.add(spec_number)

        # 동적 Section은 생성하지 않는다: release-aware 코퍼스에서 Section은
        # release-키 variant로만 존재하며(추상 Section 허브 없음), 해석 불가한
        # impacted Section에 legacy(비-release-키) ghost를 만들면 hub-pollution-free
        # 불변식을 깬다. IMPACTS_SECTION은 SECTION_INDEX로 최신 release variant에
        # 해석되는 기존 Section에만 연결된다(create_tr_impact_instance 참조).

    if created_specs:
        print(f"   specTitle 매핑: {title_found}/{len(created_specs)}개 적용")

    return dynamic


def main():
    print("=" * 60)
    print("Phase-5 Step-1: JSON-LD Instance Generation")
    print("=" * 60)

    # 출력 디렉토리 생성
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 데이터 로드
    print("\n📂 Loading data...")
    tr_metadata = load_tr_metadata()
    impacts = load_impact_mapping()
    print(f"   TR metadata: {len(tr_metadata)} TRs")
    print(f"   Impact mapping: {len(impacts)} relations")

    # 기존 인스턴스 확인 + release-aware Section 인덱스 로드
    print("\n🔍 Checking existing instances...")
    global SECTION_INDEX
    SECTION_INDEX = load_release_section_index()
    existing_specs = check_existing_specs()
    print(f"   Existing Specs: {len(existing_specs)}")
    print(f"   Release-aware Sections indexed: {len(SECTION_INDEX._by_key)} (spec, section) keys")

    # TR별 Impact ID 매핑
    tr_impact_map = {}
    for impact in impacts:
        tr_num = impact['trNumber']
        if impact['impactType'] != 'NoChange':
            impact_id = generate_tr_impact_id(
                tr_num,
                impact.get('impactsSpec', ''),
                impact.get('impactsSection', '')
            )
            if tr_num not in tr_impact_map:
                tr_impact_map[tr_num] = []
            tr_impact_map[tr_num].append(impact_id)

    # TechnicalReport 인스턴스 생성
    print("\n📝 Generating TechnicalReport instances...")
    tr_instances = []
    for tr in tr_metadata:
        impact_ids = tr_impact_map.get(tr['trNumber'], [])
        instance = create_technical_report_instance(tr, impact_ids)
        tr_instances.append(instance)

    # TRImpact 인스턴스 생성
    print("📝 Generating TRImpact instances...")
    impact_instances = []
    seen_ids = set()
    for impact in impacts:
        instance = create_tr_impact_instance(impact)
        if instance:
            # 적재기는 trImpactId 로 MERGE 하므로 겹치는 행은 소리 없이 하나로 합쳐진다
            if instance['@id'] in seen_ids:
                raise SystemExit(f"trImpactId 가 겹치는 행: {instance['@id']} ({impact})")
            seen_ids.add(instance['@id'])
            impact_instances.append(instance)

    # 동적 Spec 인스턴스 생성
    print("📝 Generating dynamic Spec instances...")
    dynamic_instances = create_dynamic_instances(impacts, existing_specs)

    # 통계
    print("\n" + "=" * 60)
    print("📊 Generation Statistics")
    print("=" * 60)
    print(f"   TechnicalReport: {len(tr_instances)}")
    print(f"   TRImpact: {len(impact_instances)}")
    print(f"   Dynamic Spec: {len(dynamic_instances)}")
    print(f"   Total: {len(tr_instances) + len(impact_instances) + len(dynamic_instances)}")
    # 해석하지 못한 절은 impactsSection 없이 나가므로 여기서 수를 드러낸다.
    print(f"   impactsSection resolved: {SECTION_INDEX.stats['resolved']}, "
          f"unresolved (dropped): {SECTION_INDEX.stats['unresolved']}")

    # JSON-LD 파일 저장
    print("\n💾 Saving JSON-LD files...")

    # technical_reports.jsonld
    tr_output = {
        "@context": CONTEXT,
        "@graph": tr_instances
    }
    tr_file = OUTPUT_DIR / "technical_reports.jsonld"
    with open(tr_file, 'w', encoding='utf-8') as f:
        json.dump(tr_output, f, ensure_ascii=False, indent=2)
    print(f"   ✅ {tr_file.name}: {len(tr_instances)} instances")

    # tr_impacts.jsonld
    impact_output = {
        "@context": CONTEXT,
        "@graph": impact_instances
    }
    impact_file = OUTPUT_DIR / "tr_impacts.jsonld"
    with open(impact_file, 'w', encoding='utf-8') as f:
        json.dump(impact_output, f, ensure_ascii=False, indent=2)
    print(f"   ✅ {impact_file.name}: {len(impact_instances)} instances")

    # spec_section_dynamic.jsonld (동적 생성된 것만).
    # 동적 인스턴스가 없으면 이전 실행에서 남은 stale 파일을 제거한다 — 잔존 파일이
    # 있으면 loader가 옛 legacy(비-release-키) ghost Section을 다시 MERGE해 hub-pollution
    # 불변식을 깬다.
    dynamic_file = OUTPUT_DIR / "spec_section_dynamic.jsonld"
    if dynamic_instances:
        dynamic_output = {
            "@context": CONTEXT,
            "@graph": dynamic_instances
        }
        with open(dynamic_file, 'w', encoding='utf-8') as f:
            json.dump(dynamic_output, f, ensure_ascii=False, indent=2)
        print(f"   ✅ {dynamic_file.name}: {len(dynamic_instances)} instances")
    elif dynamic_file.exists():
        dynamic_file.unlink()
        print(f"   🧹 Removed stale {dynamic_file.name} (no dynamic instances)")

    # 메타데이터 저장
    metadata = {
        "generatedAt": datetime.now().isoformat(),
        "statistics": {
            "technicalReports": len(tr_instances),
            "trImpacts": len(impact_instances),
            "dynamicInstances": len(dynamic_instances),
            "total": len(tr_instances) + len(impact_instances) + len(dynamic_instances),
            "impactsSectionResolved": SECTION_INDEX.stats["resolved"],
            "impactsSectionUnresolved": SECTION_INDEX.stats["unresolved"]
        },
        "files": ["technical_reports.jsonld", "tr_impacts.jsonld"]
                 + (["spec_section_dynamic.jsonld"] if dynamic_instances else [])
    }
    metadata_file = OUTPUT_DIR / "generation_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\n✅ JSON-LD generation complete!")
    print(f"   Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
