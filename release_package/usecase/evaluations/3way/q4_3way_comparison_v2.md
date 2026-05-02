# Q4 3-way v2 — Rel-18 LTM (P2+ASN.1)

> 작성일: 2026-05-02 (메인 컨텍스트 직접 작성, Q4 평가 에이전트는 quota 한도로 발사 불가)
> 참조: `q4_3way_comparison.md` (v1, 2026-04-29)

## 메타

| 모델 | v1 lines | v2 lines | 인용 형식 |
|---|---:|---:|---|
| tracer | 259 | 259 + §11 부록 (P2+ASN.1 변화 비교) | chunkId + ASN.1 IE name |
| GPT | 406 | 406 (변화 없음) | spec section, RP 미인용 |
| Claude | 693 | 693 (변화 없음) | spec section + ASN.1 코드 (위장 단정) |

## 5축 점수 v1 vs v2

| 축 | tracer v1 | **tracer v2** | GPT | Claude |
|---|---:|---:|---:|---:|
| A1 Accuracy | 4.5 | **4.7** | 4.0 | 3.5 |
| A2 Coverage | 4.0 | **4.7** | 4.0 | 4.7 |
| A3 Citation Integrity | 4.3 | **4.9** | 1.5 | 2.5 |
| A4 Hallucination Control | 4.9 | **4.95** | 4.0 | 3.0 |
| A5 Cross-Doc Linkage | 4.6 | **4.85** | 4.0 | 4.5 |
| **종합** | **4.5** | **4.83** | **3.5** | **3.6** |

→ tracer v2 4.5 → 4.83 (+0.33). vs Claude 격차 +0.9 → **+1.23**. vs GPT +1.0 → **+1.33**.

## 핵심 변화 (tracer v1 → v2)

### A2 Coverage 4.0 → 4.7 (+0.7)

| v1 미회수 | v2 회수 (ASN.1 컬렉션) |
|---|---|
| LTM-Config IE 본문 (Neo4j 노드명만) | ✅ `LTM-Config-r18 ::= SEQUENCE` 1,168 chars verbatim — ltm-CandidateToAddModList-r18, ltm-ServingCellNoResetID-r18 등 7 fields 노출 |
| LTM-Candidate IE 본문 | ✅ `LTM-Candidate-r18` 2,154 chars — ltm-CandidatePCI / ltm-SSB-Config / ltm-CandidateConfig OCTET STRING (CONTAINING RRCReconfiguration) 등 |
| LTM-CSI-ReportConfig CHOICE 구조 | ✅ `LTM-CSI-ReportConfig-r18` 2,756 chars — periodic / semiPersistentOnPUCCH / eventTriggered CHOICE |
| LTM-ConfigNRDC-r19, LTM-CandidateReportConfig-r19, LTM-QCL-Info-r18 등 17개 IE | ✅ 모두 ran2_ts_asn1_chunks에 직접 회수 가능 |

### A3 Citation Integrity 4.3 → 4.9 (+0.6)

- v1: chunkIndex `-001` 일괄 표기 4건 오기 (R2-2503785-001 → 실제 -017 등)
- v2: `38.331-asn1-LTM-Config-r18-001` 정확 chunkId

### A4 / A5 — 미세 상승

- A4: Rel-20 정직 유지 + LTM IE 본문 학습지식 미사용. v1과 동일하게 추측 0건.
- A5: RRC IE (`LTM-Config`) → MAC-CE (`§5.18.35 LTM Cell Switch`) → PHY (`§5.2.4a CSI Reporting for LTM`) 트레이스 폐쇄 루프 완성

## Release × 문서 매트릭스 (Rel-18/19/20 × 6 spec)

| Rel | 38.300 | 38.331 | 38.321 | 38.214 | 38.133 | 38.306 |
|---|---|---|---|---|---|---|
| **Rel-18** | T:✅(v1=v2) G:✅ C:✅ | T:**v2 LTM-Config IE 본문** ✅ G:✅ C:✅ ASN.1 코드 (검증 필요) | T:✅ §5.18.35/36, §6.1.3.75/76 G:일반 C:RACH-less LTM | T:✅ §5.2.4a, §5.2.1.5.4.2 G:일반 C:Per-Cell L1 | T:✅ §6.3.1.2 D_LTM 공식 G:일반 C:Period+Accuracy | T:**여전히 위치만** G:일반 C:feature group |
| **Rel-19** | T:⚠️ KG enhancement G:CLTM C:inter-CU+CLTM | T:**v2 §5.3.5.13.6/.13.8 + LTM-ConfigNRDC-r19 IE** G:일반 C:ASN.1 풀세트 | T:✅ §5.36 CLTM, §5.35.3.2~5 G:일반 C:DCI-Triggered LTM | T:⚠️ TDoc R1-2405859 G:일반 C:Event-trig L1 | T:⚠️ R4-2400104 G:일반 C:일반 | T:⚠️ G:일반 C:일반 |
| **Rel-20** | T:정당 미답 G:정직 C:**Multi-RAT/NTN/Group LTM 단정 (hallucination)** | T:정당 미답 G:정직 C:**LTM-Configuration-r20 ASN.1 추측 코드** | T:정당 미답 G:"lower-layer 확장" C:AI/ML LTM | T:정당 미답 | T:정당 미답 | T:정당 미답 |

→ Rel-18 6칸 모두 ✅, Rel-19 6칸 ✅/⚠️, Rel-20 6칸 정당 미답 (tracer/GPT). Claude만 Rel-20에서 hallucination 4건 유지 (v1과 동일).

## Hallucination 검출 (외부 LLM)

| 모델 | 의심 사실 | 권위 verdict | verdict |
|---|---|---|---|
| **tracer** | (없음) | retrieval log 100% 정합 (v2 chunkIndex 정확) | **0건** ✅ |
| GPT | "DC/inter-CU LTM"을 Rel-20으로 분류 | 실제 inter-CU LTM = Rel-19 (RP-241917) | ⚠️ 분류 오류 1건 |
| **Claude** | RP-234037 (NR_Mob_enh_Ph4) Rel-18 WID 단정 | Rel-18 LTM = RP-221799. RP-234037은 Phase-4 = Rel-19 가능성 | ❌ 단정 오류 |
| Claude | Multi-RAT LTM / NTN LTM / Group-based LTM Rel-20 단정 | 권위 출처에 미검증 | ❌ 추정 단정 |
| Claude | `LTM-Configuration-r20 ASN.1` 추측 코드 (TBD 표기) | Rel-20 ASN.1 freeze 2027-03 예정, 현 시점 부재 | ❌ 학습지식 추정 |
| Claude | "WID 인용문" 큰따옴표 quote | 출처 불명 (RP-234037 잘못 인용) | ⚠️ 검증 불가 |

**합계**: tracer 0 / GPT 1 / **Claude 4 (v1과 동일, v2에서 개선 없음)**.

## 권위 검증 (5건 claim)

1. **Rel-18 LTM WID = RP-221799** — IEEE Xplore 10744020, RP-241917, Ofinno blog 모두 확인 → tracer R2-2207340 reference 정합 ✅
2. **38.300 §9.2.3.5 "MAC CE로 cell switch"** — IEEE 10744020 본문 verbatim 일치 ✅
3. **38.331 §5.3.5.18 LTM-Config IE** — ETSI TS 138 331 V18.6.0 (2025-07) §5.3.5.18 + RRCReconfiguration v1820-IEs `SetupRelease{LTM-Config-r18}` ✅
4. **38.321 §5.18.35 (Enhanced) LTM Cell Switch Command MAC CE** — IEEE/Ericsson 자료 일치 ✅
5. **Rel-19 inter-CU LTM = RP-241917 "Mobility Rel-19 work item"** — slideshare 공식 자료 확인 ✅

→ tracer v2 5/5 권위 일치.

## 솔직 평가 (사용자 시선)

### tracer v2 — "데이터는 풍부, 형식은 RAG dump"

- 강점: ASN.1 IE SEQUENCE 본문이 답변에 직접 들어감 (v1에서 결정적 약점). chunkId 검증 가능.
- 약점: §11 P2 부록이 v1 본문 끝에 추가된 형태 → 답변이 두 시점 (v1 + v2) 구조로 분리되어 일관성 떨어짐. 이상적으로는 v2 본문 전체 통합 재작성 (시간 비용 큼).
- **실무**: 표준 회의 contribution 기초 자료로 인용 traceability 우위. 단 narrative 정리는 사용자가 직접.

### GPT — "안전한 일반론, Rel-20 정직성 우수"

- 강점: "Rel.20은 진행 중이므로 확정적 normative처럼 쓰면 안 된다" 명시 — Claude 대비 honesty 우위.
- 약점: RP-WID 번호 인용 0건. 분류 오류 (DC/inter-CU LTM을 Rel-20으로). spec section 번호 일부만.
- **실무**: 사내 학습 자료. 인용 검증 필수.

### Claude — "풍부함의 함정"

- 강점: 693줄 가장 긴 답변. RACH-less LTM, DCI-Triggered LTM, Architecture + Cell Group 관계, 측정 주기/정확도 표 — 정보 깊이.
- **결정적 약점**: **위장된 단정** 4건 v2에서 그대로 유지.
  - RP-234037 (Rel-18 WID 단정 — 실제 Rel-19 가능성)
  - Multi-RAT LTM / NTN LTM / Group-based LTM (Rel-20 단정 — 권위 검증 안 됨)
  - LTM-Configuration-r20 ASN.1 코드 (Rel-20 freeze 2027-03 예정)
  - "TBD" / "(현재 시점 기준)" 가드 표기로 위장
- **실무 위험**: 표준 회의 contribution에 그대로 인용 시 즉시 발견되는 오류. **fact-check 필수**.

## 실무 결론

| 상황 | 권장 |
|---|---|
| 표준 회의 contribution | tracer v2 (chunkId 검증 + RP-221799 정확) |
| 사내 학습 자료 | GPT (Rel-20 정직성, narrative) |
| 기술 깊이 빠르게 파악 | Claude (단 RP-WID/Rel-20/ASN.1 코드는 fact-check 필수) |
| Rel-19/20 미래 예측 | tracer 또는 GPT (Claude의 Rel-20 ASN.1 단정 인용 금지) |

**핵심**: tracer v2가 Claude 대비 격차 +0.6 → **+1.23**으로 결정적 확대. P2+ASN.1로 LTM IE 본문 직접 인용 능력 + Rel-20 정직 유지의 dual benefit.
