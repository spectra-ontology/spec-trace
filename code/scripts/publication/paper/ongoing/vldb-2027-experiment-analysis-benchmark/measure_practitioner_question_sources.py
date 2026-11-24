"""실무자가 쓴 질문 사례를 전수 판정한 목록을 사례 폴더와 대조하고, 과정 추적형 비율과 추적 사슬 문항 종류와의 겹침을 센다 (모델 호출 없음).

판정은 에이전트 한 명이 질문 파일(`00_original_question.md`, `00_question_structured.md`, `00_question_only.md`)을 직접 읽고
`JUDGMENTS`에 적었다. 답변 파일(`01_*`)은 읽지 않는다. 이 스크립트는 판정을 만들지 않고 다음을 검사·집계한다.

- 사례 폴더에서 질문 파일을 가진 디렉터리 전부와 `JUDGMENTS`의 키가 1:1로 일치하는지 검사한다(빠진 사례·남는 판정이 있으면 종료 코드 1).
- 판정 근거로 적은 인용 구절이 그 사례의 질문 파일에 글자 그대로 있는지 검사한다(없으면 종료 코드 1).
- 유형별·대응 종류별 사례 수와, 사례가 요구하는 기록 요소가 문항 종류가 의존하는 요소와 겹치는 정도를 센다.
  문항 종류가 의존하는 요소는 `chain_schema_ablation.json`의 실측(그 요소를 비우면 성립하지 않는 문항이 1개 이상)에서 읽는다.

유형 정의(질문 단위마다 하나).

- `process_trace`: 주 질문이 특정 규격 문구·문서·CR이 표준화 과정에서 어떻게 처리됐는지(어느 변경·회의·결정)를 묻는다.
- `mixed`: 주 질문은 규격 해석·구현이고, 질문 원문이 표준화 과정 기록(CR의 배경·논의, 합의, 회의 논의)을 명시적으로 함께 요청한다.
- `interpretation`: 규격 내용의 해석·구현을 묻고 과정 기록을 명시적으로 요청하지 않는다.
  설계 의도·근거를 묻되 기록을 지목하지 않는 질문은 이 유형에 두고 `asksDesignRationale`로 표시한다.

대응 정의(`process_trace`와 `mixed`에만 판정).

- `direct`: 질문이 요구하는 답 전부가 한 문항 종류의 요청 필드로 채워진다.
- `partial`: 한 문항 종류의 출발점과 요청 필드 일부가 질문이 요구하는 기록과 겹치고, 질문이 요구하는 나머지 내용은 그 종류의 필드에 없다.
- `none`: 질문이 요구하는 기록이 어느 문항 종류의 요청 필드와도 겹치지 않는다.

질문 원문에 있는 작성자 이름·소속·게시물 식별자·URL은 결과에 옮기지 않는다.

사용: python3 measure_practitioner_question_sources.py --out <json> [--ablation <chain_schema_ablation.json>]
저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

CASES = Path("docs/capability/answer/cases")
QUESTION_FILES = ("00_original_question.md", "00_question_structured.md", "00_question_only.md")
DEFAULT_ABLATION = Path("logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/chain_schema_ablation.json")

# 추적 사슬이 쓰는 기록 요소(chain_schema_ablation.json의 element 이름과 같다).
BENCHMARK_ELEMENTS = ("document_disposition", "wg_meeting_of_disposition", "revision_link",
                      "pack_membership", "tsg_meeting_of_pack", "clause_modified_by_cr")
# 실무 질문이 요구하지만 추적 사슬의 요청 필드에 없는 기록.
OUTSIDE_ELEMENTS = ("change_rationale", "discussion_content", "agreement_record", "cross_spec_correspondence")

SW, MODEM = "CP_SW_team/CP_SW_case_", "CP_modem_team/CP_modem_case_"
B1, B2 = "sr_standards_board/RAN1_case/case_", "sr_standards_board/RAN2_case/case_"


def interpretation(asks: str, quote: str, rationale: bool = False) -> dict:
    return {"asks": asks, "type": "interpretation", "asksDesignRationale": rationale, "quotes": [quote],
            "familyMapping": None, "nearestFamily": None, "elements": [], "mappingNote": None}


JUDGMENTS: dict[str, dict] = {
    SW + "001_pdu_release_reject_cause43": interpretation(
        "PDU session release가 cause #43으로 거절된 뒤 단말이 Registration request를 보내야 하는지",
        "PDU session을 inactive로 포함하여 Registration request를 전송함"),
    SW + "002_lte_neighcells_crs_assumptions": interpretation(
        "lte-NeighCellsCRS-Assumptions를 리스트의 각 CRS 패턴에 어떻게 적용하는지",
        "추가 기술 된 lte-NeighCellscRS-Assumptions 내용에 대해서 문의 드립니다"),
    SW + "003_emergency_dereg_test_11_4_1": {
        "asks": "TS 38.523-1 시험 11.4.1에 CR로 추가된 단계의 타이머·RRC release 동작 해석과, 그 CR의 도입 배경·논의 내용",
        "type": "mixed", "asksDesignRationale": False,
        "quotes": ["R5-253194 도입 배경 및 논의 내용이 필요 함",
                   "RAN5 CR 에 대해서 3GPP 24.501, 23.501 에 해당 내용이 있는지 확인이 필요 함"],
        "familyMapping": "none", "nearestFamily": None,
        "elements": ["change_rationale", "discussion_content", "cross_spec_correspondence"],
        "mappingNote": "출발점이 번호로 지목된 CR 한 건이라는 점은 CR에서 출발하는 문항 종류와 같다. "
                       "요청한 것은 그 CR의 배경·논의 내용과 다른 규격의 대응 문구이고 처분·회의·묶음·절이 아니다."},
    SW + "004_pc1_5_max_output_power_clause_removed_v17": {
        "asks": "TS 38.101의 PC1.5 관련 문구가 v16에는 있고 v17에서 빠진 이유와, 그 변경을 다룬 회의가 있었는지",
        "type": "process_trace", "asksDesignRationale": False,
        "quotes": ["이 문구가 38.101 v16에선 있었는데 v17에선 사라짐",
                   "회의가 있었던건지 아니면 특정 이유가 있는지"],
        "familyMapping": "partial", "nearestFamily": "clause_history",
        "elements": ["clause_modified_by_cr", "wg_meeting_of_disposition", "change_rationale"],
        "mappingNote": "규격 절에서 출발해 그 절을 고친 CR과 그 CR을 처리한 작업반 회의를 찾는 부분이 clause_history와 겹친다. "
                       "빠진 이유는 어느 문항 종류의 요청 필드에도 없다."},
    SW + "005_rel18_dci_waveform_switch_dci_0_1_bit_size": interpretation(
        "Rel-18 동적 waveform 전환 설정에서 DCI 0_1의 bit size를 어떻게 계산하는지",
        "DCI 0_1 의 bit size 를 어떻게 계산해야 하는지"),
    SW + "006_ntn_t430_epochtime_sfn_wraparound": interpretation(
        "NTN epochTime의 SFN 해석과 wrap-around 판정 구현이 규격 의도와 맞는지",
        "해석 및 구현이 spec 의도와 일치하는가"),
    SW + "007_single_port_vs_single_antenna_port_terminology_38101": interpretation(
        "TS 38.101의 single-port transmission과 single antenna-port를 같은 뜻으로 읽어도 되는지",
        "해석해도 되는가"),
    SW + "008_hplmn_search_full_vs_stored_frequency_scan": interpretation(
        "HPLMN 주기 탐색을 저장된 주파수만으로 수행하면 규격 위반인지",
        "3GPP spec violation"),
    SW + "009_ntn_referencelocation_degreeslongitude_asn1_vs_2scomplement": interpretation(
        "ReferenceLocation의 degreesLongitude를 ASN.1 PER과 2의 보수 중 어느 기준으로 디코딩하는지",
        "`degreesLongitude`를 디코딩할 때"),
    SW + "010_rel18_ltm_early_dlul_sync_interruption_tfirstrs": interpretation(
        "Rel-18 LTM에서 TCI activation과 cell switch command 사이 160 ms 제한이 무엇을 제한하며 candidate cell이 여럿일 때 동기 절차가 어떻게 되는지",
        "160ms 값이 명시된 근거에 대해 추가 확인이 필요해 보입니다", rationale=True),
    SW + "010_rel18_ltm_early_dlul_sync_interruption_tfirstrs/followup_01_worstcase_feasibility": interpretation(
        "candidate cell 8개가 동시에 전달되는 최악 조건에서 cell별 TO/FO 순차 추정이 시간 제한 안에 가능한지",
        "각 cell 별 TO/FO 를 순차 추정"),
    SW + "011_rel18_ltm_t304_expiry_attemptltmswitch_pdcp_srb_rollback": interpretation(
        "LTM에서 T304 만료 뒤 source PCell 설정으로 되돌릴 때 PDCP state variable이 포함되는지와 attemptLTM-Switch 분기의 근거",
        "rollback 여부가 갈리는", rationale=True),
    SW + "012_pdcch_reg_interleaving_first_ofdm_symbol_mapping": interpretation(
        "첫 번째 OFDM 심볼에 PDCCH가 전혀 매핑되지 않는 경우가 있는지",
        "첫 번째 OFDM 심볼에 PDCCH가 전혀 매핑되지 않는 case"),
    SW + "012_pdcch_reg_interleaving_first_ofdm_symbol_mapping/followup_01_pdcch_first_symbol_bandwidth_ge_3mhz": interpretation(
        "대역폭 3 MHz 이상으로 좁혀도 첫 OFDM 심볼이 PDCCH 없이 비는 경우가 있는지",
        "case 가 존재하는가"),
    SW + "013_ntn_rachless_handover_rel18_fallback_conditions": {
        "asks": "NR-NTN Rel-18 RACH-less handover의 계층별 구현 고려사항과 RACH 기반 절차로 돌아가는 조건, 표준화에서 가장 논쟁이 많았던 부분",
        "type": "mixed", "asksDesignRationale": False,
        "quotes": ["Protocol SW 구현 시 참고 및 고려해야 할 변경 사항을 리스트로 생성 부탁 드립니다",
                   "가장 논쟁이 많았던 부분에 대해서도 정리 부탁 드려요"],
        "familyMapping": "none", "nearestFamily": None, "elements": ["discussion_content"],
        "mappingNote": "논쟁이 된 논의 내용을 요청하며 특정 문서의 처분·회의·묶음·절 기록을 묻지 않는다."},
    SW + "014_rel15_pucch_repetition_sr_csi_overlap_srcounter": interpretation(
        "PUCCH 반복 전송에서 SR과 CSI가 겹칠 때의 동작과 SR counter 증가 시점",
        "SR count 를 1 증가"),
    SW + "014_rel15_pucch_repetition_sr_csi_overlap_srcounter/followup_01_sr_occasion_csi_overlap_gnb_reception": interpretation(
        "SR occasion과 CSI 전송 slot이 겹칠 때 기지국이 두 가설로 복호해야 하는지",
        "NW에서는 csi로 decoding해보고 SR로도 decoding을 시도 해봐야하는걸까요"),
    MODEM + "001_bfd_two_sets": interpretation(
        "BFD set이 둘일 때 한 set의 실패만으로 BFR 절차를 시작하는지",
        "set1 failure만으로 BFR RA를 시작해야 하는가"),
    MODEM + "002_ntn_location_cho": interpretation(
        "NTN에서 위치·시간 기반 trigger만으로 CHO를 실행하는지",
        "location/time-based trigger만 만족하면 CHO execution을 수행해야 하는가"),
    MODEM + "003_csi_with_cdrx": interpretation(
        "C-DRX inactive time에 걸린 CSI report를 전송하는지 버리는지",
        "report occasion이 inactive time이므로 drop해야 하는가"),
    MODEM + "004_powercontroloffset_cdm2_epre": {
        "asks": "powerControlOffset과 CDM2 설정에서 port별 CSI-RS 전력을 1과 1/2 중 무엇으로 해석하는지(회의 논의를 근거로 요청)",
        "type": "mixed", "asksDesignRationale": False,
        "quotes": ["per-port CSI-RS power를 1로 해석하는 것이 맞아? 아니면 1/2로 해석하는 것이 맞아?",
                   "표준 문서들과 표준 회의 논의 내용들을 근거로 답변을 해줘"],
        "familyMapping": "none", "nearestFamily": None, "elements": ["discussion_content"],
        "mappingNote": "회의 논의를 해석의 근거로 요청하며 특정 문서의 처리 기록을 묻지 않는다."},
    B1 + "001_srs_pusch_pucch_priority": interpretation(
        "SRS와 PUSCH/PUCCH 전송이 겹칠 때 어느 쪽이 우선하는지",
        "어떤경우에 SRS송신이 PUSCH/PUCCH 송신보다 우선될 수 있는 것인가요"),
    B1 + "002_uci_pusch_etype2_csi_part2_omission": {
        "asks": "Enhanced Type 2 codebook에서 CSI part2가 모두 omission되는 경우가 있는지와, 그 모호성에 대한 논의·합의가 있었는지",
        "type": "mixed", "asksDesignRationale": False,
        "quotes": ["CSI part2가 모두 omission되는 경우가 발생하는지",
                   "모호성에 대한 논의가 또는 합의 내용이 있는지요"],
        "familyMapping": "none", "nearestFamily": None, "elements": ["agreement_record", "discussion_content"],
        "mappingNote": "특정 주제에 대한 합의·논의의 존재를 묻는다. 일곱 문항 종류는 문서·CR·묶음·절에서 출발하며 주제에서 합의를 찾는 종류가 없다."},
    B1 + "003_dci_duplicate_ul_scheduling_cancel": interpretation(
        "뒤에 온 DCI의 상향링크 자원 할당이 겹치면 앞 DCI의 스케줄링이 무효가 되는지",
        "제1 DCI에 따른 스케줄링은 무효화(취소)되는 것으로 이해한 것이 맞는 것일까요"),
    B1 + "004_subband_pmi_layer_indicator_uci_bit": interpretation(
        "subband PMI와 layer indicator가 함께 설정될 때 CSI part2의 UCI bit 구성",
        "UCI bit 구성이 어떻게 되는지 문의 드립니다"),
    B2 + "001_neighbor_cell_pbch_decoding_rrm_handover": interpretation(
        "Rel-15 mobility 동작에서 이웃 셀 PBCH decoding이 필요한지",
        "neighbor cell 의 PBCH decoding 이 필요한지 확인해줘"),
    B2 + "002_rrm_pbch_decode_intra_inter_ssb_csirs": interpretation(
        "Rel-15 RRM 측정에서 이웃 셀 PBCH decoding이 필수인지(주파수 내·간, SSB·CSI-RS, FR1·FR2별)",
        "neighbor cell 의 PBCH decoding 이 필수적인지 알고 싶어"),
    B2 + "003_2step_cfra_msga_crnti_mac_ce_handover": interpretation(
        "2-step CFRA handover에서 MSGA PUSCH에 C-RNTI MAC CE를 싣는지와 어느 셀의 C-RNTI인지",
        "target cell의 C-RNTI를 설정해서 보내는 것이 맞는지 확인 부탁드립니다"),
    B2 + "004_rach_config_ssb_perrach_absent_default_handover": interpretation(
        "ssb-perRACH-OccasionAndCB-PreamblesPerSSB가 없을 때 단말이 어떤 값으로 동작하는지",
        "논리적으로 당연한 동작으로 보면 될까"),
    B2 + "005_phr_p_field_mpe_reporting_pcmax": interpretation(
        "PHR P field 정의의 두 조건이 OR 관계인지",
        "아래 두 조건이 OR 조건인건가요"),
    B2 + "006_endc_phr_real_virtual_pcell_type1_ph": interpretation(
        "EN-DC multiple PHR에서 PCell Type 1 PH 값을 어떤 전송 기준으로 산출하는지",
        "real PH값을 이용하는 것이 맞는지 확인 부탁드립니다"),
    B2 + "007_mbs_multicast_ptp_rlc_architecture": interpretation(
        "MBS multicast PTP 전송의 RLC entity 구성 의미와 그 option이 채택된 의도",
        "어떤 의도로 이러한 option 이 채택되었는지 궁금합니다", rationale=True),
    B2 + "008_bwp_switching_random_access_pseudocode_spcell_scell": interpretation(
        "Random Access 개시 때 BWP 전환 pseudo-code의 SpCell·SCell 동작 해석과 그 이유",
        "왜 이런 동작을 하는지 궁금합니다", rationale=True),
}

# 결과에 옮기면 안 되는 식별 정보의 표지(URL, 메일 주소, 게시물 식별자).
IDENTIFYING = re.compile(r"https?://|@[A-Za-z]|post_id", re.IGNORECASE)


def question_units() -> dict[str, list[Path]]:
    units: dict[str, list[Path]] = {}
    for path in sorted(CASES.rglob("00_*.md")):
        if path.name in QUESTION_FILES:
            units.setdefault(path.parent.relative_to(CASES).as_posix(), []).append(path)
    return units


def origin_evidence(units: dict[str, list[Path]]) -> dict:
    readme = CASES / "README.md"
    phrases = ("실제로 받은 질문 한 건", "누군가 실제로 물어본 질문 하나", "게시판 원문 그대로")
    lines = readme.read_text().splitlines()
    found = [{"phrase": phrase, "line": next((n for n, text in enumerate(lines, 1) if phrase in text), None)}
             for phrase in phrases]
    # 각 질문 파일의 Source 줄은 출처 종류(현업 질문·사내 게시판)를 적는다. 줄 본문에는 조직 이름이 있어 종류만 센다.
    source_kind = collections.Counter()
    for unit, paths in units.items():
        source = " ".join(line for path in paths for line in path.read_text().splitlines()
                          if line.startswith("> Source"))
        kind = ("field_team_question" if "현업" in source else
                "internal_standards_board" if "게시판" in source else "no_source_line")
        source_kind[kind] += 1
    return {"readme": readme.as_posix(), "readmePhrases": found,
            "unitsBySourceLineKind": dict(source_kind),
            "sourceLineKinds": {"field_team_question": "Source 줄에 '현업' 표기",
                                "internal_standards_board": "Source 줄에 '게시판' 표기",
                                "no_source_line": "질문 파일에 Source 줄 없음"}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--ablation", type=Path, default=DEFAULT_ABLATION)
    args = parser.parse_args()

    units = question_units()
    missing, extra = sorted(set(units) - set(JUDGMENTS)), sorted(set(JUDGMENTS) - set(units))
    problems = [f"판정이 없는 사례: {u}" for u in missing] + [f"사례 폴더에 없는 판정: {u}" for u in extra]
    for unit, judgment in JUDGMENTS.items():
        text = "\n".join(path.read_text() for path in units.get(unit, ()))
        for quote in judgment["quotes"]:
            if quote not in text:
                problems.append(f"인용 구절이 질문 파일에 없음: {unit}: {quote}")
            if IDENTIFYING.search(quote):
                problems.append(f"인용 구절에 식별 정보 표지: {unit}")
        unknown = set(judgment["elements"]) - set(BENCHMARK_ELEMENTS) - set(OUTSIDE_ELEMENTS)
        if unknown:
            problems.append(f"정의되지 않은 기록 요소: {unit}: {sorted(unknown)}")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        raise SystemExit(1)

    ablation = json.loads(args.ablation.read_text())
    family_elements = {family: [a["element"] for a in ablation["ablations"] if a["brokenByFamily"][family] > 0]
                       for family in ablation["itemsByFamily"]}
    if {a["element"] for a in ablation["ablations"]} != set(BENCHMARK_ELEMENTS):
        raise SystemExit("chain_schema_ablation.json의 요소 이름이 BENCHMARK_ELEMENTS와 다르다")

    rows = []
    for unit in sorted(JUDGMENTS):
        judgment = JUDGMENTS[unit]
        inside = [e for e in judgment["elements"] if e in BENCHMARK_ELEMENTS]
        outside = [e for e in judgment["elements"] if e in OUTSIDE_ELEMENTS]
        row = {"unit": unit, "isFollowup": "/followup_" in unit,
               "questionFiles": [path.name for path in units[unit]], **judgment,
               "benchmarkElementsRequired": inside, "outsideElementsRequired": outside}
        if judgment["type"] != "interpretation":
            row["familyOverlap"] = {family: {"shared": [e for e in inside if e in elements],
                                             "familyElements": len(elements)}
                                    for family, elements in family_elements.items()}
        rows.append(row)

    def count(key, subset=rows) -> dict:
        return dict(collections.Counter(str(row[key]) for row in subset))

    cases = [row for row in rows if not row["isFollowup"]]
    process = [row for row in rows if row["type"] != "interpretation"]
    element_units = {e: [row["unit"] for row in rows if e in row["elements"]]
                     for e in BENCHMARK_ELEMENTS + OUTSIDE_ELEMENTS}
    report = {
        "casesRoot": CASES.as_posix(),
        "units": len(rows), "cases": len(cases), "followups": len(rows) - len(cases),
        "unitsBySource": dict(collections.Counter(row["unit"].split("/")[0] for row in rows)),
        "unitsByType": count("type"), "casesByType": count("type", cases),
        "interpretationUnitsAskingDesignRationale": sum(row["asksDesignRationale"] for row in rows),
        "processOrMixedUnits": len(process),
        "familyMappingOfProcessOrMixedUnits": count("familyMapping", process),
        "nearestFamilyOfProcessOrMixedUnits": count("nearestFamily", process),
        "familyElementsFromAblation": family_elements,
        "unitsRequiringElement": {e: len(u) for e, u in element_units.items()},
        "unitsRequiringAnyBenchmarkElement": sum(bool(row["benchmarkElementsRequired"]) for row in rows),
        "unitsRequiringOnlyOutsideElements": sum(bool(row["outsideElementsRequired"])
                                                 and not row["benchmarkElementsRequired"] for row in rows),
        "benchmarkElementsRequiredByAnyUnit": sum(bool(element_units[e]) for e in BENCHMARK_ELEMENTS),
        "benchmarkElements": len(BENCHMARK_ELEMENTS),
        "originEvidence": origin_evidence(units),
        "judgments": rows,
    }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "judgments"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
