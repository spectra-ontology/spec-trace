#!/usr/bin/env python3
"""cr_cq_gold.py: Phase-8 CR 검색 CQ(RAN1~5)의 기준 정의 정답과 통과 판정.

CQ 마다 질의 글과 설명만 보고 정한 결정적 기준(스펙 · 작업 항목 · 조항 · 카테고리 · Release · 낱말 묶음)을
둔다. 그 기준을 Neo4j phase-4 CR 메타데이터와 Qdrant 헤더 청크 payload 에 대 보아 정답 집합을 만든다.
벡터 유사도는 어디에도 쓰지 않는다.

옛 정답(`cq_test_dataset.json` 의 `expected_tdocs`)을 쓰지 않는 까닭:

> 주의: RAN4 · RAN5 의 옛 정답은 의미 검색 top-K 후보에서 골랐다(데이터셋 `selection_method` 기록). 검증기도
> 같은 임베딩으로 찾으므로, 그 정답과의 일치는 검색 품질이 아니라 「같은 임베딩이 같은 답을 낸다」는 순환이다.
> RAN3 의 옛 정답은 `reasonForChange` 한 칸의 CONTAINS 결과 몇 건이고, RAN1 의 옛 정답은 KG 제목 CONTAINS
> 결과다(데이터셋 `metadata.warning`). RAN1 · RAN2 는 여러 CQ 에 정답이 비어 있다.
>
> 주의: 관련 문서가 수백 건인 질의에 정답 몇 건만 적으면 recall@10 은 정답 크기에 묶인다. 정답이 10 건을
> 넘으면 상한이 10/|정답| 이고, 정답 밖의 관련 문서를 돌려준 검색은 틀린 것으로 셈된다. 그래서 여기서는
> 기준을 만족하는 집합 전체를 정답으로 두고 상위 10 개의 정밀도(P@10)로 잰다.

정답 두 등급:

* strict: 제목이 기준을 만족한다. 제목은 KG `c.title`, 비었거나 `(reserved)` 이면 헤더 payload `title`.
* lenient: 제목 또는 표지의 Reason for change · Summary of change 가 기준을 만족한다. 통과 판정은 lenient 로
  하고 strict 는 함께 보고한다.

모집단 F 는 검색이 돌려줄 수 있는 문서, 곧 Qdrant 헤더 청크가 있는 TDoc 이다. CQ 의 `filters` 가 있으면
헤더 payload 에 그대로 건다(문자열은 같음, 배열은 원소 포함; `chunkType` 은 청크 범위라 TDoc 거르기에
쓰지 않는다). 한 TDoc 에 헤더 청크가 여럿이면 처음 읽은 것을 쓴다. 스펙 · 작업 항목 · 조항은 KG 와 헤더
payload 의 합집합이고, Release 는 KG `_targetRelease`, 카테고리는 KG 가 비면 헤더 payload 다.

통과 문턱:

> 주의: 상위 10 개를 F 에서 아무렇게나 뽑아도 기준 문서는 기저율 p0 = |C∩F|/|F| 만큼 맞는다. 그래서 문턱은
> 「F 에서 서로 다른 TDoc n = min(10, |F|) 개를 무작위로 뽑았을 때 k 개 이상 맞힐 확률이 alpha 이하인 가장
> 작은 k」(k_min)로 둔다. 순위는 서로 다른 TDoc 이므로(`cr_tdoc_ranking`) 이 확률은 비복원 추출, 곧
> 초기하 분포 P[Hypergeom(|F|, |C∩F|, n) >= k] 이고 유리수로 정확히 셈한다. 이항 P[Binomial(10, p0) >= k] 를
> 쓰면 F 가 작을 때 틀린다: |F| < 10 이면 검색이 F 전체를 돌려주는 것만으로 정답을 모두 맞히는데도 이항은
> 그것을 우연보다 나은 결과로 친다. alpha = 0.05 는 관례이며 데이터에서 끌어낸 값이 아니다.
>
> 주의: p0 = 1 이면 필터를 통과한 문서가 모두 정답이라 어떤 검색도 정밀도로 통과한다. 이런 CQ 는
> `match_mode = filter_conformance` 로 두고, 돌려준 TDoc 이 모두 필터를 만족하는지만 본다. 검색 품질은
> 이 CQ 로 재지 못한다. p0 < 1 인데 맞힐 수 있는 가장 큰 k = min(n, |C∩F|) 에서도 꼬리 확률이 alpha 를
> 넘으면 무작위 검색과 가를 길이 없으므로 `not_testable` 이다.
> p0 = 0 이면(F 안에 기준 문서가 없으면) 꼬리 확률은 k = 1 에서 이미 0 이지만 어떤 검색도 맞힐 문서가 없으므로
> 이것도 `not_testable` 이다.

기준 사후 수정:

> 주의: 기준은 결과를 보기 전에 정했다. 결과 표본을 본 뒤 고친 기준은 `amended_post_hoc` 에 까닭을 남긴다.
> 사후 수정은 기준이 결과에 맞춰졌을 수 있다는 뜻이므로 보고할 때 따로 밝힌다.

낱말 경계:

> 주의: 파이썬 `\\b` 는 `_` 를 낱말 글자로 본다. 그래서 `\\bNTN\\b` 는 작업 항목 코드 꼴 `NR_NTN_solutions` 안의
> NTN 을 놓친다(`_N` 사이는 경계가 아니다). 여기의 정규식은 `\\b` 를 「`_` 를 뺀 낱말 글자」의 경계로 바꿔
> 컴파일한다(`_wb`). 모든 낱말 묶음이 이 규칙을 함께 쓴다.

사용:
    python3 -E scripts/tsg/RAN/formal/common/cr_cq_gold.py --wg RAN4 --out <파일>
    python3 -E scripts/tsg/RAN/formal/common/cr_cq_gold.py --wg all --out <디렉토리>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from fractions import Fraction
from math import comb
from pathlib import Path
from typing import Callable, Iterable, Mapping

_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
for _p in (_ROOT / "scripts" / "common", _ROOT / "scripts" / "common" / "common"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
from common import axis, credentials  # noqa: E402

WGS = ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")
K = 10
ALPHA = Fraction(1, 20)
QDRANT_HOST, QDRANT_PORT = "localhost", 6333
#: 헤더 청크 payload 에서 읽는 칸.
HEADER_FIELDS = ["tdocNumber", "specNumber", "crNumber", "category", "workItem", "meeting", "title",
                 "clausesAffected", "crPackId", "source"]
#: 모집단을 거를 때 쓰지 않는 필터 칸. 청크 범위라 TDoc 의 성질이 아니다.
NON_TDOC_FILTERS = ("chunkType",)

# ── 낱말 묶음 ─────────────────────────────────────────────────────────────

#: `_` 를 뺀 낱말 글자 사이의 경계. `\b` 와 같되 `_` 를 낱말 밖 글자로 본다.
_WB = r"(?:(?<![^\W_])(?=[^\W_])|(?<=[^\W_])(?![^\W_]))"


def _wb(pattern: str) -> str:
    return pattern.replace(r"\b", _WB)


def rx(pattern: str, flags: int = re.I) -> Callable[[str], bool]:
    c = re.compile(_wb(pattern), flags)
    return lambda s: bool(c.search(s or ""))


def cl(r, *prefixes) -> bool:
    """조항 번호가 접두어 중 하나로 시작한다."""
    return any(str(c) == p or str(c).startswith(p + ".") for c in r["clauses"] for p in prefixes)


def sp(r, *specs) -> bool:
    return bool(set(specs) & r["specs"])


def wi(r, pattern: str) -> bool:
    """작업 항목 코드 하나가 패턴에 맞는다(대소문자 무관)."""
    c = re.compile(pattern, re.I)
    return any(c.search(w or "") for w in r["wis"])


def nr_conf(r) -> bool:
    """NR 적합성 시험 스펙(38.5xx)을 고친다."""
    return any(s.startswith("38.5") for s in r["specs"])


# 약어는 대소문자를 가리고(flags=0) 낱말은 가리지 않는다.
CA = rx(r"\bCA\b|\bCA_|carrier aggregation|band combination|bandwidth combination|\bBCS\b")
INTRO = rx(r"introduc|\bnew\b|\badd")
FR2 = rx(r"FR2|FR1\s*\+\s*FR2", 0)
REDCAP = rx(r"red\s*cap|reduced capabilit")
_NTN_ACR = rx(r"\bNTN\b|non[- ]terrestrial|satellite|\bSAN\b", 0)
_NTN_WORD = rx(r"non[- ]terrestrial|satellite")
NTN = lambda s: _NTN_ACR(s) or _NTN_WORD(s)  # noqa: E731
_TIMING_WORD = rx(r"timing|Rx-Tx|time difference|timing advance|K_?offset")
_TA = rx(r"\bTA\b", 0)
TIMING = lambda s: _TIMING_WORD(s) or _TA(s)  # noqa: E731
SPUR = rx(r"spurious")
HPUE = rx(r"HPUE|\bPC\s?2\b|power class 2|high power")
ENDC = rx(r"EN-?DC|LTE.?NR|dual connectivity|DC_")
_CHO_WORD = rx(r"conditional handover|conditional reconfiguration|condReconfig|condExecution")
_CHO_ACR = rx(r"\bCHO\b", 0)
CHO = lambda s: _CHO_WORD(s) or _CHO_ACR(s)  # noqa: E731
_SL_WORD = rx(r"sidelink|side link|V2X")
_SL_ACR = rx(r"\bSL\b|PC5", 0)
SL = lambda s: _SL_WORD(s) or _SL_ACR(s)  # noqa: E731
RESALLOC = rx(r"resource allocation|resource pool|resource selection|resource reselection|"
              r"resource (re)?evaluation|mode ?[12]\b|configured grant|dynamic grant|SL grant|"
              r"pre-emption|preemption|sensing")
NRDC = rx(r"NR-?DC\b|NR DC\b")
POS = rx(r"positioning|\bLPP\b|location")
MEASREP = rx(r"measurement|report")
CAPENQ = rx(r"capability enquiry|UECapabilityEnquiry|UECapabilityInformation|capability transfer")
RRCRECONF = rx(r"RRC ?Reconfiguration|RRC (connection )?reconfiguration")
HARQ = rx(r"HARQ")
ACCURACY = rx(r"accura|integrity")
SPLIT = rx(r"split")
_SDT_ACR = rx(r"\bSDT\b", 0)
_SDT_WORD = rx(r"small data")
SDT = lambda s: _SDT_ACR(s) or _SDT_WORD(s)  # noqa: E731
SDT_LDV = rx(r"large|data volume|threshold|terminat|subsequent")
MIGR = rx(r"migrat|handover|mobile|mobility|\bHO\b")
#: 이동 IAB(mobile IAB): 'mobile IAB' · 'mobile-IAB' · 'mIAB' · 'mobile integrated access and backhaul'.
MOBILE_IAB = rx(r"mobile[\s-]*IAB|\bmIAB\b|mobile integrated access")
#: > 주의: 이동 IAB 작업 항목 코드(`NR_mobile_IAB` · `NR_mobile_IAB-Core`)는 근거로 쓰지 않는다. 같은 작업
#: >   항목 아래에 'mobile TRP location' 측위 CR 이 함께 올라가 있어서, 작업 항목만으로 받으면 질의가 묻지
#: >   않은 측위 CR 이 들어온다. 그래서 해당 등급의 본문(제목 또는 표지)에 이동 IAB 어휘가 있어야 한다.
NGU = rx(r"NG-U|NGU|\bN3\b|user plane|tunnel|GTP|bearer")
LOCREP = rx(r"location report")
ICS = rx(r"initial context setup")
MOP = rx(r"maximum output power|max(\.|imum)? output power|\bMOP\b")
DEFAULT = rx(r"default|pre-?test|generic procedure|reference configuration")
GAP = rx(r"measurement gap|meas\.? ?gap|MeasGap|gap pattern|gap config|\bgaps?\b.*meas|meas.*\bgaps?\b|"
         r"\bMG\b|NCSG|pre-?configured gap|concurrent gap")
BEAM = rx(r"beam peak|beam search|beam management|RSRPB|RSRP_?B\b|beam lock|beamlock|beam sweep")
_OTA = rx(r"\bOTA\b|-O\b", 0)
_RRC_MSG = rx(r"RRC|message|IE")
_BEAM_FR2 = rx(r"beam peak|RSRPB|RSRP_?B\b")
_RRCRECONF_IE = rx(r"RRCReconfiguration", 0)
_MBS_ACR = rx(r"\bMBS\b|multicast", 0)
_MULTICAST = rx(r"multicast")
MBS_MULTICAST = lambda s: _MBS_ACR(s) or _MULTICAST(s)  # noqa: E731
_MBS_WORD = rx(r"multicast|broadcast")
_MBS_ACR_ALL = rx(r"\bMBS\b|MBMS", 0)
MBS = lambda s: _MBS_WORD(s) or _MBS_ACR_ALL(s)  # noqa: E731
HO_TIME = rx(r"handover|\bHO\b|timing|time window|\bwindow\b|time[- ]based")
# RAN1(물리 계층) 낱말 묶음.
_SBFD_ACR = rx(r"\bSBFD\b", 0)
_SBFD_WORD = rx(r"sub-?band (non-overlapping )?full[- ]duplex|full[- ]duplex")
SBFD = lambda s: _SBFD_ACR(s) or _SBFD_WORD(s)  # noqa: E731
RA_PHY = rx(r"resource allocation|frequency[- ]domain resource|time[- ]domain resource|resource block|\bPRBs?\b|"
            r"\bRB set|\bRBs?\b")
_WUS_ACR = rx(r"\bLP-?WUS\b|\bWUS\b|\bLP-?SS\b|\bLR\b", 0)
_WUS_WORD = rx(r"wake[- ]?up signal|wake[- ]?up radio|low[- ]power wake")
WUS = lambda s: _WUS_ACR(s) or _WUS_WORD(s)  # noqa: E731
_DRX_ACR = rx(r"\bDRX\b", 0)
_DRX_WORD = rx(r"discontinuous reception|configur")
DRX_CONF = lambda s: _DRX_ACR(s) or _DRX_WORD(s)  # noqa: E731
_AIML_ACR = rx(r"\bAI\b|\bML\b|\bAI/ML\b|\bAIML\b", 0)
_AIML_WORD = rx(r"artificial intelligence|machine learning")
AIML = lambda s: _AIML_ACR(s) or _AIML_WORD(s)  # noqa: E731
BEAM_WORD = rx(r"beam")
_MC_WORD = rx(r"multi[- ]?carrier|multi[- ]?cell|multiple (serving )?cells|multi-PDSCH|multi-PUSCH|"
              r"multiple PDSCHs|multiple PUSCHs|cross[- ]carrier|DCI formats? [01]_3")
MC_SCHED = lambda s: _MC_WORD(s)  # noqa: E731
SCHED = rx(r"schedul")
PDCCH_REP = rx(r"PDCCH repetition|repetitions? of PDCCH|PDCCH.{0,40}repet|repet.{0,40}PDCCH")
HARQ_EXT = rx(r"\b32\b|extend|extension|increas|larger number|more HARQ")
_CSI_ACR = rx(r"\bCSI\b|\bCSI-RS\b|\bPMI\b|\bCQI\b|\bCRI\b|\bRI\b", 0)
_CSI_WORD = rx(r"channel state information|codebook")
CSI = lambda s: _CSI_ACR(s) or _CSI_WORD(s)  # noqa: E731
CSI_REPORT = rx(r"CSI[- ]report|CSI-ReportConfig|report(ing)? (of |the )?(CSI|channel state)|CSI (computation|feedback)")
_SRS_ACR = rx(r"\bSRS\b", 0)
_SRS_WORD = rx(r"sounding reference")
SRS = lambda s: _SRS_ACR(s) or _SRS_WORD(s)  # noqa: E731
_ES_ACR = rx(r"\bNES\b|\bNW ES\b|cell DTX|cell DRX|SSB-less|\bUE ES\b", 0)
_ES_WORD = rx(r"energy sav|power sav|network energy|energy efficien|cell (DTX|DRX)|on-demand SSB|on-demand SIB")
ENERGY = lambda s: _ES_ACR(s) or _ES_WORD(s)  # noqa: E731
_UE_ACR = rx(r"\bUEs?\b", 0)
PDCCH_MON = rx(r"PDCCH monitoring|monitoring occasion|monitor(ing)? (of )?PDCCH|search space|PDCCH candidate|"
               r"blind decod|\bCCEs?\b|\bCORESETs?\b")
_CAS_ACR = rx(r"\bCAS\b", 0)
MUTING = rx(r"mut(e|ing)\b|muted")
_BEAM_ACR = rx(r"\bTCI\b|\bBFR\b|\bBFD\b|\bBM\b", 0)
BEAM_MGMT = lambda s: BEAM_WORD(s) or _BEAM_ACR(s)  # noqa: E731
_MOB_ACR = rx(r"\bHO\b|\bLTM\b|\bCHO\b", 0)
_MOB_WORD = rx(r"mobility|handover|L1/L2[- ]triggered|cell switch")
MOBILITY = lambda s: _MOB_ACR(s) or _MOB_WORD(s)  # noqa: E731
BWP = rx(r"bandwidth part|\bBWPs?\b")
HARQ_ACK_MC = rx(r"DCI formats? 1_3|multi-PDSCH|multiple PDSCHs|multi-cell|sub-?codebook")
MIMO_PH5 = rx(r"MIMO (Phase|Ph\.?) ?5|MIMO_Ph5|Rel-?19 MIMO|MIMO enhancement.{0,20}Rel-?19")


def _rel17_redcap(r) -> bool:
    return r["rel"] == "Rel_17" or (r["rel"] == "" and wi(r, r"^NR_redcap-(Core|Perf)$"))


def _sl_wi(r) -> bool:
    return wi(r, r"V2X|NRSL")


# ── CQ 기준 ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CQ:
    """CQ 하나의 기준. pred(r, X) 의 X 는 'T'(제목, strict) 또는 'C'(제목+표지, lenient)."""
    query: str
    filters: dict
    criteria: str
    pred: Callable[[dict, str], bool]
    #: 결과를 본 뒤 고쳤으면 그 까닭, 아니면 None.
    amended_post_hoc: str | None = None


def _rel(r, *rels) -> bool:
    return r["rel"] in rels


def _ntn_r1(r, X) -> bool:
    return wi(r, r"NTN") or NTN(r[X])


def _aiml_beam(r, X) -> bool:
    return (AIML(r[X]) or wi(r, r"AIML|AI_ML")) and BEAM_WORD(r[X])


def _mimo_ph5(r, X) -> bool:
    return wi(r, r"^NR_MIMO_Ph5") or MIMO_PH5(r[X])


_AMEND_REDCAP = ("KG _targetRelease 가 제목이 (reserved) 인 CR 노드에서 비어 있어 Rel-17 RedCap CR 이 빠졌다; "
                 "Release 가 비면 Rel-17 RedCap 작업 항목(NR_redcap-Core/Perf)을 Rel-17 로 본다")
_AMEND_MBS = ("맨 'broadcast' 와 작업 항목 소속만으로 posSIB broadcast · 여러 작업 항목을 단 UE capability CR 이 "
              "들어왔다; 글에 MBS 또는 multicast 를 요구한다")
_AMEND_NTN = "맨 'time' 이 'Timer' 에 맞았다; handover · timing · time window · window · time-based 로 좁힌다"
_AMEND_MIAB = ("blind re-derivation found the general-IAB scope too broad: 일반 IAB · inter-CU 이동 CR 과 "
               "'mobile TRP location'(측위) 같은 오탐이 들어왔다; 질의가 묻는 이동 IAB(mobile IAB) 어휘가 "
               "본문에 있는 CR 로 좁히고, 측위 CR 이 함께 실린 이동 IAB 작업 항목 코드만으로는 받지 않는다")

CRITERIA: dict[str, dict[str, CQ]] = {
    "RAN1": {
        "S1-01": CQ("SBFD resource allocation", {},
                    "SBFD (keyword or WI NR_duplex_evo*) and resource allocation keyword",
                    lambda r, X: (SBFD(r[X]) or wi(r, r"^NR_duplex_evo")) and RA_PHY(r[X])),
        "S1-02": CQ("wake-up signal DRX configuration", {"workItem": "NR_LPWUS-Core"},
                    "wake-up signal keyword and (DRX or configuration keyword) [filter workItem=NR_LPWUS-Core]",
                    lambda r, X: WUS(r[X]) and DRX_CONF(r[X])),
        "S1-03": CQ("beam prediction AI/ML", {}, "AI/ML (keyword or WI *AIML*) and beam keyword",
                    _aiml_beam),
        "S1-04": CQ("multi-carrier scheduling", {"workItem": "NR_MC_enh2-Core"},
                    "multi-carrier/multi-cell keyword or scheduling keyword [filter workItem=NR_MC_enh2-Core]",
                    lambda r, X: MC_SCHED(r[X]) or SCHED(r[X])),
        "S1-05": CQ("NTN intra-slot PDCCH repetition enhancement",
                    {"specNumber": "38.213", "workItem": "NR_NTN_Ph3-Core"},
                    "PDCCH repetition keyword [filter specNumber=38.213, workItem=NR_NTN_Ph3-Core]",
                    lambda r, X: PDCCH_REP(r[X])),
        "S1-06": CQ("HARQ process extension 32", {}, "HARQ and (32 / extend / extension / increase)",
                    lambda r, X: HARQ(r[X]) and HARQ_EXT(r[X])),
        "S2-01": CQ("CSI related changes", {"workItem": "NR_MIMO_Ph5-Core"},
                    "CSI keyword [filter workItem=NR_MIMO_Ph5-Core]", lambda r, X: CSI(r[X])),
        "S2-03": CQ("SRS related changes", {"workItem": "TEI19"},
                    "SRS keyword [filter workItem=TEI19]", lambda r, X: SRS(r[X])),
        "S2-04": CQ("energy saving related changes", {"workItem": "Netw_Energy_NR_enh-Core"},
                    "any CR with WI Netw_Energy_NR_enh-Core [filter defines topic: network energy saving]",
                    lambda r, X: wi(r, r"^Netw_Energy_NR_enh-Core$")),
        "S3-01": CQ("PDCCH monitoring", {"specNumber": "38.213"},
                    "38.213 PDCCH monitoring: clause 10.1* or PDCCH monitoring/search space keyword",
                    lambda r, X: sp(r, "38.213") and (cl(r, "10.1") or PDCCH_MON(r[X]))),
        "S3-02": CQ("resource allocation changes", {"specNumber": "38.214"},
                    "38.214 resource allocation: clause 5.1.2* / 6.1.2* or resource allocation keyword",
                    lambda r, X: sp(r, "38.214") and (cl(r, "5.1.2", "6.1.2") or RA_PHY(r[X]))),
        "S3-03": CQ("HARQ process", {"specNumber": "38.212"}, "38.212 HARQ keyword",
                    lambda r, X: sp(r, "38.212") and HARQ(r[X])),
        "S3-04": CQ("CAS muting", {"specNumber": "38.211"}, "38.211 CAS (acronym) and muting keyword",
                    lambda r, X: sp(r, "38.211") and _CAS_ACR(r[X]) and MUTING(r[X])),
        "S4-01": CQ("beam management new feature", {"category": "B"},
                    "category B and beam management (beam / TCI / BFR / BFD / BM)",
                    lambda r, X: r["cat"] == "B" and BEAM_MGMT(r[X])),
        "S4-02": CQ("mobility correction", {"category": "F"},
                    "category F and mobility (mobility / handover / HO / LTM / CHO / L1/L2-triggered / cell switch)",
                    lambda r, X: r["cat"] == "F" and MOBILITY(r[X])),
        "S4-03": CQ("MIMO Phase 5 feature introduction", {"category": "B", "workItem": "NR_MIMO_Ph5-Core"},
                    "category B with WI NR_MIMO_Ph5-Core [filter defines topic]",
                    lambda r, X: r["cat"] == "B" and wi(r, r"^NR_MIMO_Ph5-Core$")),
        "S5-01": CQ("changes to section 5.2.1.1", {"clausesAffected": "5.2.1.1", "specNumber": "38.214"},
                    "38.214 clause 5.2.1.1* [filter defines topic]",
                    lambda r, X: sp(r, "38.214") and cl(r, "5.2.1.1")),
        "S5-02": CQ("HARQ-ACK sub-codebook DCI format 1_3 multi-PDSCH unicast",
                    {"clausesAffected": "9.1.2.1", "specNumber": "38.213"},
                    "38.213 clause 9.1.2.1* and (DCI format 1_3 / multi-PDSCH / multi-cell / sub-codebook keyword)",
                    lambda r, X: sp(r, "38.213") and cl(r, "9.1.2.1") and HARQ_ACK_MC(r[X])),
        "S5-03": CQ("why was this section modified", {"clausesAffected": "5.1.2.1", "specNumber": "38.214"},
                    "38.214 clause 5.1.2.1* [filter defines topic; query text names no topic]",
                    lambda r, X: sp(r, "38.214") and cl(r, "5.1.2.1")),
        "S7-01": CQ("HARQ process 수를 32개로 확장한 이유", {"chunkType": "header"},
                    "HARQ and (32 / extend / extension / increase)",
                    lambda r, X: HARQ(r[X]) and HARQ_EXT(r[X])),
        "S7-02": CQ("NTN에서 PDCCH repetition이 도입된 배경", {"chunkType": "header"},
                    "NTN (keyword or WI *NTN*) and PDCCH repetition keyword",
                    lambda r, X: _ntn_r1(r, X) and PDCCH_REP(r[X])),
        "S7-03": CQ("에너지 절감을 위한 UE 동작 변경 목적", {"chunkType": "header"},
                    "energy saving (keyword or WI Netw_Energy*) and UE keyword",
                    lambda r, X: (ENERGY(r[X]) or wi(r, r"^Netw_Energy")) and _UE_ACR(r[X])),
        "S7-04": CQ("reason for introducing AI/ML beam management", {"chunkType": "header"},
                    "AI/ML (keyword or WI *AIML*) and beam keyword", _aiml_beam),
        "E-04": CQ("multi-carrier scheduling bandwidth part", {"workItem": "NR_MC_enh2-Core"},
                   "bandwidth part keyword [filter workItem=NR_MC_enh2-Core]",
                   lambda r, X: BWP(r[X])),
        "E-05": CQ("빔 예측 AI/ML 변경", {}, "AI/ML (keyword or WI *AIML*) and beam keyword", _aiml_beam),
        "E-06": CQ("In Rel-19, which CRs modified the CSI reporting procedure?", {},
                   "Rel-19 (KG _targetRelease) and (CSI reporting keyword or 38.214 clause 5.2*)",
                   lambda r, X: _rel(r, "Rel_19") and (CSI_REPORT(r[X]) or (sp(r, "38.214") and cl(r, "5.2")))),
        "H-03": CQ("MIMO Phase 5 변경 이유", {"chunkType": "header"},
                   "MIMO Phase 5 (WI NR_MIMO_Ph5* or keyword)", _mimo_ph5),
        "H-04": CQ("MIMO Phase 5 CSI reporting change details", {"chunkType": "body"},
                   "MIMO Phase 5 (WI NR_MIMO_Ph5* or keyword) and CSI keyword",
                   lambda r, X: _mimo_ph5(r, X) and CSI(r[X])),
    },
    "RAN4": {
        "RAN4-CR-CQ-001": CQ(
            "FR2 CA bandwidth combination introduction", {"specNumber": ["38.101-2", "38.101-3"]},
            "FR2 CA band/bandwidth combination introduction: UE RF spec 38.101-2 (FR2) or 38.101-3 with FR2 in "
            "title; CA/combination keyword; introduction keyword",
            lambda r, X: sp(r, "38.101-2", "38.101-3") and CA(r[X]) and INTRO(r[X])
            and (sp(r, "38.101-2") or FR2(r[X]))),
        "RAN4-CR-CQ-002": CQ(
            "RedCap UE Rel-17 introduction RF requirements",
            {"specNumber": ["38.101-1", "38.101-2", "38.101-3", "38.101-4"]},
            "RedCap (WI NR_redcap* or keyword) Rel-17 UE RF requirements (38.101-1/-2/-3/-4); missing release -> "
            "Rel-17 if WI NR_redcap-Core/Perf",
            lambda r, X: (wi(r, r"redcap") or REDCAP(r[X])) and _rel17_redcap(r)
            and sp(r, "38.101-1", "38.101-2", "38.101-3", "38.101-4"),
            _AMEND_REDCAP),
        "RAN4-CR-CQ-003": CQ(
            "NTN UE timing measurement requirements", {"specNumber": "38.133"},
            "NTN (WI *NTN* or keyword) in 38.133 touching UE timing: clause 7.1C*/7.3C* or timing keyword",
            lambda r, X: (wi(r, r"NTN") or NTN(r[X])) and sp(r, "38.133")
            and (cl(r, "7.1C", "7.3C") or TIMING(r[X]))),
        "RAN4-CR-CQ-004": CQ(
            "OTA AAS BS spurious emissions limit", {"specNumber": ["37.105", "37.145-2", "38.104", "38.141-2"]},
            "AAS BS spurious emissions: spec 37.105/37.145-2 (AAS BS), or NR BS 38.104/38.141-2 with OTA in text; "
            "spurious keyword",
            lambda r, X: SPUR(r[X]) and (sp(r, "37.105", "37.145-2")
                                         or (sp(r, "38.104", "38.141-2") and _OTA(r[X])))),
        "RAN4-CR-CQ-005": CQ(
            "HPUE PC2 EN-DC band combination", {"specNumber": "38.101-3"},
            "HPUE/PC2 EN-DC combinations: spec 38.101-3; HPUE keyword or WI HPUE*; EN-DC keyword or WI *DC* or "
            "clause 5.5B/6.2B/7.3B",
            lambda r, X: sp(r, "38.101-3") and (HPUE(r[X]) or wi(r, r"HPUE"))
            and (ENDC(r[X]) or wi(r, r"DC") or cl(r, "5.5B", "6.2B", "7.3B"))),
    },
    "RAN5": {
        "RAN5-CR-CQ-001": CQ(
            "NR CA maximum output power test case", {},
            "NR CA maximum output power test: 38.521-1/-2/-3; clause 6.2A.1* or (MOP keyword and CA keyword)",
            lambda r, X: sp(r, "38.521-1", "38.521-2", "38.521-3")
            and (cl(r, "6.2A.1") or (MOP(r[X]) and CA(r[X])))),
        "RAN5-CR-CQ-002": CQ(
            "RRC default pre-test configuration conformance", {},
            "RRC default (pre-test) message contents: 38.508-1; clause 4.6* (Default NG-RAN RRC message and IE "
            "contents) or (RRC and default/pre-test keyword)",
            lambda r, X: sp(r, "38.508-1") and (cl(r, "4.6") or (_RRC_MSG(r[X]) and DEFAULT(r[X])))),
        "RAN5-CR-CQ-003": CQ(
            "measurement gap configuration reporting test", {},
            "measurement gap configuration/reporting in NR conformance specs (38.5xx): gap keyword",
            lambda r, X: nr_conf(r) and GAP(r[X])),
        "RAN5-CR-CQ-004": CQ(
            "FR2 beam management RSRP search procedure", {},
            "FR2 beam management / beam peak (RSRPB) search: beam keyword and (FR2 keyword or spec "
            "38.521-2/38.521-3/38.903 or beam-peak/RSRPB which are FR2 OTA notions)",
            lambda r, X: BEAM(r[X]) and (FR2(r[X]) or sp(r, "38.521-2", "38.521-3", "38.903")
                                         or _BEAM_FR2(r[X]))),
        "RAN5-CR-CQ-005": CQ(
            "RedCap UE conformance test requirements", {},
            "RedCap conformance tests: RedCap keyword or WI *redcap*; NR conformance spec 38.5xx",
            lambda r, X: (wi(r, r"redcap") or REDCAP(r[X])) and nr_conf(r)),
        "RAN5-CR-CQ-006": CQ(
            "NR sidelink V2X default configuration", {},
            "NR sidelink/V2X default configuration: sidelink keyword or WI *V2X*/*SL*; 38.508-1 or (38.5xx and "
            "default keyword)",
            lambda r, X: (SL(r[X]) or wi(r, r"V2X|_SL|NRSL|sidelink"))
            and (sp(r, "38.508-1") or (nr_conf(r) and DEFAULT(r[X])))),
    },
    "RAN2": {
        "S1-01": CQ("conditional handover reconfiguration", {"specNumber": "38.331"}, "conditional handover in 38.331",
                    lambda r, X: sp(r, "38.331") and CHO(r[X])),
        "S1-02": CQ("NR sidelink V2X resource allocation", {"specNumber": ["38.331", "38.321"]},
                    "NR sidelink resource allocation in 38.331/38.321",
                    lambda r, X: sp(r, "38.331", "38.321") and (SL(r[X]) or _sl_wi(r)) and RESALLOC(r[X])),
        "S1-03": CQ("MBS multicast session management", {"specNumber": "38.331"}, "MBS/multicast keyword in 38.331",
                    lambda r, X: sp(r, "38.331") and MBS_MULTICAST(r[X]), _AMEND_MBS),
        "S1-04": CQ("NR-DC bearer configuration", {"specNumber": "37.340"}, "NR-DC in 37.340",
                    lambda r, X: sp(r, "37.340") and NRDC(r[X])),
        "S1-05": CQ("positioning measurement reporting", {"specNumber": ["38.305", "37.355"]},
                    "positioning measurement/reporting in 38.305/37.355",
                    lambda r, X: sp(r, "38.305", "37.355") and MEASREP(r[X])),
        "S1-06": CQ("UE capability enquiry procedure", {"specNumber": ["38.306", "38.331"]},
                    "UE capability: any 38.306 CR, or 38.331 CR on clause 5.6.1* / capability enquiry keyword",
                    lambda r, X: sp(r, "38.306") or (sp(r, "38.331") and (cl(r, "5.6.1") or CAPENQ(r[X])))),
        "S2-01": CQ("RRC 변경", {"workItem": "NR_newRAT-Core"},
                    "RRC (38.331) CR with WI NR_newRAT-Core [filter workItem=NR_newRAT-Core]",
                    lambda r, X: sp(r, "38.331") and wi(r, r"^NR_newRAT-Core$")),
        "S2-02": CQ("sidelink 전체 변경 요약", {"workItem": "5G_V2X_NRSL-Core"},
                    "any CR with WI 5G_V2X_NRSL-Core [filter defines topic]",
                    lambda r, X: wi(r, r"^5G_V2X_NRSL-Core$")),
        "S2-03": CQ("positioning 관련 변경", {"workItem": "NR_pos-Core"},
                    "any CR with WI NR_pos-Core [filter defines topic]",
                    lambda r, X: wi(r, r"^NR_pos-Core$")),
        "S3-01": CQ("RRC connection reconfiguration", {"specNumber": "38.331"},
                    "38.331 RRC reconfiguration: clause 5.3.5* or RRCReconfiguration keyword",
                    lambda r, X: sp(r, "38.331") and (cl(r, "5.3.5") or RRCRECONF(r[X]))),
        "S3-02": CQ("UE capability", {"specNumber": "38.306"},
                    "any 38.306 CR [filter defines topic: 38.306 = UE capabilities]",
                    lambda r, X: sp(r, "38.306")),
        "S3-03": CQ("MAC HARQ process", {"specNumber": "38.321"}, "38.321 HARQ",
                    lambda r, X: sp(r, "38.321") and HARQ(r[X])),
        "S4-01": CQ("conditional handover 새 기능", {"category": "B"}, "category B conditional handover",
                    lambda r, X: r["cat"] == "B" and CHO(r[X])),
        "S4-02": CQ("RRC 오류 수정", {"category": "F"}, "category F RRC (38.331/36.331)",
                    lambda r, X: r["cat"] == "F" and sp(r, "38.331", "36.331")),
        "S4-03": CQ("V2X 기능 도입", {"category": "B", "workItem": "5G_V2X_NRSL-Core"},
                    "category B with WI 5G_V2X_NRSL-Core [filter defines topic]",
                    lambda r, X: r["cat"] == "B" and wi(r, r"^5G_V2X_NRSL-Core$")),
        "S5-01": CQ("changes to section 5.3.5", {"clausesAffected": "5.3.5", "specNumber": "38.331"},
                    "38.331 clause 5.3.5* [filter defines topic]",
                    lambda r, X: sp(r, "38.331") and cl(r, "5.3.5")),
        "S5-02": CQ("changes to section 4.2.7.2", {"clausesAffected": "4.2.7.2", "specNumber": "38.306"},
                    "38.306 clause 4.2.7.2*",
                    lambda r, X: sp(r, "38.306") and cl(r, "4.2.7.2")),
        "S7-01": CQ("conditional handover를 도입한 이유", {"chunkType": "header"},
                    "conditional handover (any spec)", lambda r, X: CHO(r[X])),
        "S7-02": CQ("NR sidelink resource allocation이 변경된 배경", {"chunkType": "header"},
                    "sidelink resource allocation (any spec)",
                    lambda r, X: (SL(r[X]) or _sl_wi(r)) and RESALLOC(r[X])),
        "S7-03": CQ("positioning measurement 정확도를 높이기 위한 변경 목적", {"chunkType": "header"},
                    "positioning accuracy (positioning spec or keyword, and accuracy/integrity keyword)",
                    lambda r, X: (sp(r, "38.305", "37.355") or POS(r[X]) or wi(r, r"pos")) and ACCURACY(r[X])),
        "E-03": CQ("RRCReconfiguration SEQUENCE", {"specNumber": "38.331"}, "38.331 RRCReconfiguration",
                   lambda r, X: sp(r, "38.331") and _RRCRECONF_IE(r[X])),
        "E-04": CQ("NR-DC bearer split configuration", {}, "NR-DC split bearer (any spec)",
                   lambda r, X: NRDC(r[X]) and SPLIT(r[X])),
        "E-05": CQ("conditional handover 관련 변경", {}, "conditional handover (any spec)",
                   lambda r, X: CHO(r[X])),
        "H-03": CQ("V2X 변경 이유", {"chunkType": "header"}, "V2X/sidelink (any spec)",
                   lambda r, X: SL(r[X]) or _sl_wi(r)),
        "H-04": CQ("V2X sidelink 변경 내용", {"chunkType": "body"}, "V2X/sidelink (any spec)",
                   lambda r, X: SL(r[X]) or _sl_wi(r)),
    },
    "RAN3": {
        "RAN3-CR-CQ-001": CQ(
            "SDT large data volume termination threshold", {},
            "SDT and (large data volume / threshold / termination)",
            lambda r, X: (SDT(r[X]) or wi(r, r"SDT")) and SDT_LDV(r[X])),
        "RAN3-CR-CQ-002": CQ(
            "mobile IAB migration handover support", {},
            "mobile IAB keyword (mobile IAB / mIAB / mobile integrated access) in the graded text and "
            "(migration / handover / mobile); the WI code alone does not qualify",
            lambda r, X: MOBILE_IAB(r[X]) and MIGR(r[X]),
            _AMEND_MIAB),
        "RAN3-CR-CQ-003": CQ(
            "NTN handover timing window satellite", {},
            "NTN/satellite and (handover / timing / time window / time-based)",
            lambda r, X: (NTN(r[X]) or wi(r, r"NTN")) and HO_TIME(r[X]),
            _AMEND_NTN),
        "RAN3-CR-CQ-004": CQ(
            "MBS multicast NG-U interface bearer", {},
            "MBS and (NG-U spec 38.414/38.415 or NG-U/N3/user plane/tunnel/bearer keyword)",
            lambda r, X: (MBS(r[X]) or wi(r, r"MBS")) and (sp(r, "38.414", "38.415") or NGU(r[X]))),
        "RAN3-CR-CQ-005": CQ(
            "location reporting event Initial Context Setup", {},
            "location reporting and Initial Context Setup",
            lambda r, X: LOCREP(r[X]) and ICS(r[X])),
    },
}

# ── 레코드 ────────────────────────────────────────────────────────────────

_Q_KG = """
MATCH (c:CR)-[:BELONGS_TO_CR_PACK]->(:CRPack)
WITH DISTINCT c
OPTIONAL MATCH (c)-[:MODIFIES]->(s:Spec)
WITH c, collect(DISTINCT s.specNumber) AS specs
OPTIONAL MATCH (c)-[:RELATED_TO]->(w:WorkItem)
WITH c, specs, collect(DISTINCT w.workItemCode) AS wis
OPTIONAL MATCH (c)-[:MODIFIES_SECTION]->(x)
RETURN c.tdocNumber AS tdoc, c.title AS title, specs AS specs, wis AS wis,
       collect(DISTINCT x.sectionNumber) AS secs, c._targetRelease AS rel, c.crCategory AS cat,
       c.reasonForChange AS reason, c.summaryOfChange AS summary
"""


def fetch_kg(wg: str) -> dict[str, dict]:
    """CR 팩에 든 phase-4 CR 노드의 메타데이터. 읽기 전용 세션."""
    from neo4j import GraphDatabase
    drv = GraphDatabase.driver(axis.bolt_uri(wg), auth=credentials.neo4j_auth())
    try:
        with drv.session(default_access_mode="READ") as s:
            return {r["tdoc"]: r.data() for r in s.run(_Q_KG)}
    finally:
        drv.close()


def fetch_headers(wg: str, collection: str | None = None) -> dict[str, dict]:
    """Qdrant CR 컬렉션의 헤더 청크 payload(벡터 없이). 한 TDoc 에 여럿이면 처음 읽은 것.

    > 주의: collection 을 주면 그 컬렉션을 읽는다. 검증기가 `--collection` 으로 다른 컬렉션을 검색하면
    > 모집단도 같은 컬렉션에서 와야 p0 · k_min 이 그 검색에 맞는다. None 이면 WG 의 기본 CR 컬렉션이다.
    """
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import FieldCondition, Filter, MatchValue, PayloadSelectorInclude
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=300)
    flt = Filter(must=[FieldCondition(key="chunkType", match=MatchValue(value="header"))])
    coll = collection or axis.qdrant_collection(wg, "cr_chunks")
    out: dict[str, dict] = {}
    offset = None
    while True:
        points, offset = client.scroll(coll, scroll_filter=flt, limit=1000,
                                       offset=offset, with_payload=PayloadSelectorInclude(include=HEADER_FIELDS),
                                       with_vectors=False)
        for p in points:
            out.setdefault(p.payload["tdocNumber"], p.payload)
        if offset is None:
            return out


def build_records(kg: Mapping[str, dict], headers: Mapping[str, dict]) -> dict[str, dict]:
    """헤더 청크가 있는 TDoc 마다 기준이 읽는 레코드 하나."""
    recs = {}
    for t, h in headers.items():
        k = kg.get(t, {})
        title = k.get("title")
        if not title or title.strip().lower() in ("(reserved)", "reserved"):
            title = h.get("title") or ""
        hc = h.get("clausesAffected") or []
        if not isinstance(hc, list):
            hc = [hc]
        specs = {x for x in (k.get("specs") or []) if x}
        if h.get("specNumber"):
            specs.add(h["specNumber"])
        wis = {x for x in (k.get("wis") or []) if x}
        if h.get("workItem"):
            wis |= {w.strip() for w in re.split(r"[,;]", h["workItem"]) if w.strip()}
        recs[t] = dict(T=title, C=" ".join([title, k.get("reason") or "", k.get("summary") or ""]),
                       specs=specs, wis=wis, clauses=set(map(str, k.get("secs") or [])) | set(map(str, hc)),
                       rel=(k.get("rel") or "").split("/")[-1], cat=k.get("cat") or h.get("category") or "", h=h)
    return recs


def satisfies_filters(payload: Mapping, filters: Mapping, skip: Iterable[str] = ()) -> bool:
    """payload 가 필터를 만족한다. 필터 값이 하나면 문자열은 같음, 배열은 원소 포함.

    필터 값이 목록이면 「이 중 하나」다(검색 쪽 `cr_tdoc_ranking.build_filter` 의 `MatchAny` 와 같은 뜻):
    문자열 칸은 목록 안에 있어야 하고, 배열 칸은 목록과 겹치는 원소가 하나 이상 있어야 한다.
    """
    skip = set(skip)
    for key, want in filters.items():
        if key in skip:
            continue
        got = payload.get(key)
        if isinstance(want, (list, tuple)):
            if isinstance(got, list):
                if not set(got) & set(want):
                    return False
            elif got not in want:
                return False
        elif isinstance(got, list):
            if want not in got:
                return False
        elif got != want:
            return False
    return True


# ── 문턱 ─────────────────────────────────────────────────────────────────

def hypergeom_tail(population: int, successes: int, draws: int, k: int) -> Fraction:
    """P[Hypergeom(population, successes, draws) >= k], 유리수로 정확히."""
    total = comb(population, draws)
    return sum((Fraction(comb(successes, j) * comb(population - successes, draws - j), total)
                for j in range(k, min(successes, draws) + 1)), Fraction(0))


def k_min(population: int, successes: int, k: int = K, alpha: Fraction = ALPHA) -> int | None:
    """F 에서 서로 다른 n = min(k, |F|) 개를 무작위로 뽑아 k_min 개 이상 맞힐 확률이 alpha 이하인 가장 작은 k_min.

    그 k_min 이 맞힐 수 있는 가장 큰 수 min(n, successes) 를 넘거나 정답이 F 전체면 None.
    """
    draws = min(k, population)
    if population <= 0 or successes >= population:
        return None
    for j in range(1, min(successes, draws) + 1):
        if hypergeom_tail(population, successes, draws, j) <= alpha:
            return j
    return None


# ── 정답 ─────────────────────────────────────────────────────────────────

def gold_for(wg: str, recs: Mapping[str, dict]) -> dict[str, dict]:
    out = {}
    for cid, cq in CRITERIA[wg].items():
        F = [t for t, r in recs.items() if satisfies_filters(r["h"], cq.filters, NON_TDOC_FILTERS)]
        strict = sorted(t for t in F if cq.pred(recs[t], "T"))
        lenient = sorted(t for t in F if cq.pred(recs[t], "C"))
        p0 = Fraction(len(lenient), len(F)) if F else None
        km = k_min(len(F), len(lenient)) if p0 is not None else None
        if p0 is None:
            mode = "not_testable"
        elif p0 == 0:
            mode = "not_testable"
        elif p0 == 1:
            mode = "filter_conformance"
        elif km is None:
            mode = "not_testable"
        else:
            mode = "criteria_precision_at_k"
        out[cid] = {
            "query": cq.query, "filters": cq.filters, "criteria": cq.criteria,
            "amended_post_hoc": cq.amended_post_hoc,
            "universe_size": len(F), "n_strict": len(strict), "n_lenient": len(lenient),
            "strict_tdocs": strict, "lenient_tdocs": lenient,
            "p0": float(p0) if p0 is not None else None,
            "p0_fraction": [len(lenient), len(F)],
            "k": K, "draws": min(K, len(F)), "alpha": float(ALPHA), "k_min": km,
            "match_mode": mode,
        }
    return out


def build(wg: str, collection: str | None = None) -> dict[str, dict]:
    return gold_for(wg, build_records(fetch_kg(wg), fetch_headers(wg, collection)))


# ── 판정 ─────────────────────────────────────────────────────────────────

def _distinct(tdocs: Iterable[str]) -> list[str]:
    seen, out = set(), []
    for t in tdocs:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def evaluate(gold_entry: Mapping, ranked_tdocs: Iterable[str],
             returned_payloads: Mapping[str, Mapping | list] | None = None) -> dict:
    """검색이 돌려준 TDoc 순위(중복은 첫 자리만 센다)를 정답 하나에 대해 판정한다.

    criteria_precision_at_k: 상위 10 개 중 lenient 정답 수가 k_min 이상이면 PASS.
    filter_conformance: 돌려준 TDoc 이 하나 이상이고 모두 CQ 필터를 만족하면 PASS. 만족 여부는
    returned_payloads(TDoc → payload 또는 payload 목록; 목록이면 모두 만족해야 한다)로 본다. payload 가
    없는 TDoc 은 확인할 수 없으므로 위반으로 센다.
    not_testable: 판정하지 않는다.
    """
    ranked = _distinct(ranked_tdocs)
    top = ranked[:K]
    lenient, strict = set(gold_entry["lenient_tdocs"]), set(gold_entry["strict_tdocs"])
    hits_l = sum(t in lenient for t in top)
    hits_s = sum(t in strict for t in top)
    mode = gold_entry["match_mode"]
    res = {"match_mode": mode, "n_returned": len(ranked), "hits_lenient": hits_l, "hits_strict": hits_s,
           "p_at_10_lenient": hits_l / K, "p_at_10_strict": hits_s / K, "k_min": gold_entry["k_min"]}
    if mode == "filter_conformance":
        if returned_payloads is None:
            raise ValueError("filter_conformance 판정에는 returned_payloads 가 있어야 한다")
        bad = []
        for t in ranked:
            pls = returned_payloads.get(t)
            if pls is None:
                bad.append(t)
                continue
            if not isinstance(pls, list):
                pls = [pls]
            if not pls or not all(satisfies_filters(p, gold_entry["filters"]) for p in pls):
                bad.append(t)
        res["filter_violations"] = bad
        res["status"] = "PASS" if ranked and not bad else "FAIL"
    elif mode == "not_testable":
        res["status"] = "NOT_TESTABLE"
    else:
        res["status"] = "PASS" if hits_l >= gold_entry["k_min"] else "FAIL"
    return res


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wg", required=True, choices=[*WGS, "all"])
    ap.add_argument("--out", required=True, type=Path,
                    help="한 WG 면 JSON 파일, all 이면 gold_{WG}.json 을 쓸 디렉토리")
    ap.add_argument("--collection", help="헤더를 읽을 Qdrant CR 컬렉션(한 WG 일 때만). 없으면 WG 기본값")
    args = ap.parse_args(argv[1:])
    if args.collection and args.wg == "all":
        ap.error("--collection 은 --wg 하나와만 쓴다")
    targets = list(WGS) if args.wg == "all" else [args.wg]
    for wg in targets:
        gold = build(wg, args.collection)
        path = args.out / f"gold_{wg}.json" if args.wg == "all" else args.out
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(gold, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        for cid, e in gold.items():
            p0_text = "NOT_TESTABLE" if e["p0"] is None else f"{e['p0']:.5f}"
            print(f"{wg} {cid} F={e['universe_size']} strict={e['n_strict']} lenient={e['n_lenient']} "
                  f"p0={p0_text} k_min={e['k_min']} {e['match_mode']}"
                  + (" [amended_post_hoc]" if e["amended_post_hoc"] else ""))
        print(f"{wg} → {path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
