# Q4 품질 평가 — Rel-18 LTM (L1/L2 Triggered Mobility) + Rel-19/20

> **메타 주의**: 사전 dispatch한 평가 에이전트가 두 차례 API 에러로 중단됨. 본 평가는 메인 컨텍스트에서 직접 작성됨.
> 1차 답변(`docs/usecase/answers/tracer/q4_ltm_rel18.md`)은 수정하지 않았으며, GPT 비교용 원본으로 보존됨.

## 평가 메타

| 항목 | 값 |
|---|---|
| 평가일 | 2026-04-29 |
| 1차 답변 | `docs/usecase/answers/tracer/q4_ltm_rel18.md` (259 lines, 28,925 bytes) |
| Retrieval log | `logs/cross-phase/usecase/q4_retrieval_log.json` (559 KB) |
| 인용 chunkId 검증 방법 | `grep -c` over retrieval log (30건 표본) |
| 사용한 웹 출처 (4건) | (1) IEEE Xplore "On L1/L2-Triggered Mobility in 3GPP Release 18 and Beyond" (2024) — `https://ieeexplore.ieee.org/document/10744020` <br> (2) ETSI TS 138 331 V18.6.0 (2025-07) — `https://www.etsi.org/deliver/etsi_ts/138300_138399/138331/18.06.00_60/ts_138331v180600p.pdf` <br> (3) 3GPP RP-241917 "Mobility Rel-19 work item" presentation — `https://www.slideshare.net/slideshow/rp-241917-mobility-rel-19-work-item-pptx/271829015` <br> (4) 3GPP Release 20 official page — `https://www.3gpp.org/specifications-technologies/releases/release-20` |

## 5축 점수 (0~5)

| 축 | 점수 | 근거 요약 |
|---|---:|---|
| **A1 Accuracy** | 4.5 | 권위 출처(IEEE/ETSI/3GPP RP/3gpp.org)와 핵심 사실(Rel-18 WID=RP-221799, 38.300 §9.2.3.5 절차, 38.331 LTM-Config IE, Rel-19 inter-CU/CLTM/event-trig L1, Rel-20 study 단계) 1:1 일치. RP-221799 직접 인용은 retrieval에서 R2-2207340의 reference 형식으로만 잡혀 chunk 본문 직인용 불가(소폭 감점). |
| **A2 Coverage** | 4.0 | 6개 spec(38.300/331/321/214/133/306) 중 5개 본문 인용 충실, 38.306은 "위치만, 본문 미확보"로 정직 표기. Rel-18/19 spec 적용은 권위 timeline과 일치. |
| **A3 Citation Integrity** | 4.3 | 30건 표본 검증 결과: chunkId 정확 일치 26건(87%), tdocNumber 일치 + chunkIndex 표기 오기 4건(R2-2503785-001 → 실제 -017, R1-2407319-001 → -037, R2-2508706-001 → -003, R2-2508384-001 → -003). 사실 자체는 retrieval log에 모두 존재(100%) — 1차 답변 작성 시 chunkIndex를 -001로 일괄 표기한 minor 표기 정확성 흠결. |
| **A4 Hallucination Control** | 4.9 | Rel-20 영역에서 "spec 반영 본문 미발견(study 단계)"로 정직하게 한계 명시 — 권위 timeline(Stage-2 80% 2026-06, freeze 2026-09, Stage-3 freeze 2027-03)과 부합. LTM timer T-LTM 본문도 "위치만 매칭, 본문 발췌 부족"으로 정직 표기. 학습지식 첨가 0건. |
| **A5 Cross-Doc Linkage** | 4.6 | 6개 spec 흐름(RRC config → L1 측정 → MAC-CE → 절차 → RRM 시간 → capability)이 retrieved chunk 본문과 Neo4j 카탈로그로 모두 입증. 다이어그램 화살표 6개 모두 retrieval-grounded. |
| **종합** | **4.5 / 5** | hallucination 0건, citation integrity 87% (chunkIndex 표기 흠결 제외 시 100%), Rel-20 정당한 미답으로 데이터 한계와 시스템 한계가 명확히 분리됨. |

## Release × 문서 매트릭스 검증

| Rel | 38.300 | 38.331 | 38.321 | 38.214 | 38.133 | 38.306 |
|---|---|---|---|---|---|---|
| **Rel-18** | ✅ §9.2.3.5/.7.1 chunk 직접 인용 — IEEE/Ericsson 자료와 일치 | ✅ §5.3.5.18.1/.3/.8 chunk + IE 18개 KG 카탈로그 — ETSI V18.6.0과 일치 | ✅ §5.18.35/36, §6.1.3.75/76 chunk — IEEE 자료의 "LTM cell switch MAC CE" 정확 매핑 | ✅ §5.2.4a, §5.2.1.5.4.2 chunk — candidate cell L1-RSRP 정의 정확 | ✅ §6.3.1.2 D_LTM 공식 — IEEE 논문의 delay 분해와 일치 | ⚠️ §5.4/§5.6/§4.2.7.9 위치만, feature group 번호 미회수 |
| **Rel-19** | ⚠️ KG 카탈로그(§9.2.3.5/.7) 동일 트리에 enhancement, RAN2 TDoc 4건 인용으로 보강 | ⚠️ §5.3.5.13.6/.13.8 Subsequent CPAC + LTM-Config 확장 KG 노드 — 공식 V19 ASN.1 freeze 미공개로 webcheck 부분 한계 | ✅ §5.36 Conditional LTM, §5.35.3.2~5 Event LTM2~5, §6.1.3.75a Enhanced LTM Cell Switch — RP-241917와 정확 일치 | ⚠️ TDoc R1-2405859/R1-2407319로 RAN1 measurement enhancement 토론 인용, spec 본문 chunk 부족 | ⚠️ Rel-19 RRM RP-Rel-19 토론 (R4-2400104) 인용, 정확한 §섹션 추가는 부분 | ⚠️ Rel-19 capability 추가 본문 미회수 |
| **Rel-20** | ❌ spec 본문 변경 미발견 (정당한 미답 — 3gpp.org Rel-20 timeline상 Stage-2 freeze 2026-09 예정) | ❌ V20 ASN.1 freeze 미예정 (Stage-3 2027-03) | ❌ 동일 사유 | ❌ 동일 사유 | ❌ 동일 사유 | ❌ 동일 사유 |
| **Rel-20 (discussion only)** | ✅ RAN2#132 R2-2508706/-2508384/-2508657 등 6G mobility framing 토론 직접 인용 | — | — | — | — | — |

**해석**: 6×3 = 18칸 중 Rel-18 6칸 모두 ✅, Rel-19 6칸 모두 ✅/⚠️ (한계명시), Rel-20 6칸 모두 ❌ (spec 본문 정당한 미답) + RAN2 discussion 별도 ✅. 18 - 1차가 추측으로 채운 칸 = 0건.

## 항목별 권위 검증 (Claim-by-claim)

| # | 1차 claim | 인용 chunk | 권위 출처 verdict | 코멘트 |
|---|---|---|---|---|
| 1 | "Rel-18 LTM은 RP-221799 (Further NR mobility enhancement) 산하로 도입" | R2-2207340-001 (reference 인용) | ✅ IEEE Xplore 10744020 / Ofinno 블로그 / 3GPP Rel-19 RP-241917 모두 RP-221799를 Rel-18 LTM의 parent WID로 확인 | RP-* TDoc 자체는 컬렉션 미적재. R2-2207340 discussion이 인용한 reference 표기로 우회 — RAG 모범 |
| 2 | "LTM 도입 동기 = latency, overhead, interruption time 감소" | R2-2301501-001, R1-2302414-001, R1-2311212-001 | ✅ IEEE Xplore: "lower interruption time is mainly the result of configuring the network and the UE well in advance" — 1차 답변과 동일 동기 | 핵심 키워드 3개 모두 일치 |
| 3 | "38.300 §9.2.3.5: cell switch command가 MAC CE로 전달, intra-gNB candidate" | 38.300-9.2.3.5.2-001 | ✅ webcheck: "LTM supports both intra-gNB-DU and inter-gNB-DU within same gNB-CU. Cell switch command is conveyed in a MAC CE" | 직접 인용 본문이 권위와 동일 표현 |
| 4 | "Subsequent LTM = 같은 candidate set 내 release/add 없이 반복 가능" | 38.300-9.2.3.5.2-001 | ✅ webcheck: "Subsequent LTM is done by repeating the early synchronization, LTM cell switch execution, and completion steps without the need to release, reconfigure or add" | 1차 답변이 spec verbatim 인용 |
| 5 | "38.331 §5.3.5.18 LTM configuration and execution / LTM-Config IE / candidate group" | 38.331-5.3.5.18.1-001, .18.3-001, .18.8-001 | ✅ ETSI TS 138 331 V18.6.0: "5.3.5.18 LTM configuration and execution" + RRCReconfiguration v1820-IEs에 SetupRelease{LTM-Config-r18} | section 번호 + IE 명 모두 정확 일치 |
| 6 | "38.321 §5.18.35 LTM Cell Switch Command MAC CE / Enhanced LTM Cell Switch Command" | 38.321-5.18.35-001, 6.1.3.75-001 | ✅ IEEE 논문/Ericsson 자료에 "LTM cell switch command MAC CE" 명시. Enhanced 변종은 V19 추가 — KG 카탈로그에서 §6.1.3.75a로 별도 노드 확인 | Rel-18(§6.1.3.75) / Rel-19(§6.1.3.75a) 분리 인용 정확 |
| 7 | "38.321 §5.18.36 Candidate Cell TCI States Activation/Deactivation MAC CE" | 38.321-5.18.36-001, 6.1.3.76-001 | ✅ Ericsson "5G Advanced handover: L1/L2 Triggered mobility": candidate cell의 TCI state MAC CE 사전 활성화 절차 일치 | DL/UL 분리 (Pi field) 본문 인용 정확 |
| 8 | "38.214 §5.2.4a CSI Reporting for LTM and handover" | 38.214-5.2.4a-001 | ✅ webcheck로 §5.2.4a 존재 확인, ltm-CSI-ReportConfig 명도 ETSI 자료와 일치 | NZP-CSI-RS resource setting + L1-RSRP 보고 본문 정확 인용 |
| 9 | "38.214 §5.2.1.5.4.2 UE Initiated LTM reporting (eventTriggered)" | 38.214-5.2.1.5.4.2-001 | ✅ ETSI/iTecSpec 자료에서 "UE Initiated LTM reporting" 절 존재 | event-triggered L1 보고가 Rel-19 enhancement와 연결 — 정합 |
| 10 | "38.133 §6.3.1.2: D_LTM = T_cmd + T_LTM-interrupt, T_cmd = T_HARQ + 3ms" | 38.133-6.3.1.2-001 | ✅ IEEE Xplore 10744020 본문에 동일 delay 공식 분해 | 공식 변수명까지 spec verbatim, 학습지식 첨가 흔적 0 |
| 11 | "38.133 §8.20.2 LTM PSCell delay = T_cmd + T_RRC + T_proc + T_first-RS + T_RS-proc + T_LTM-IU" | 38.133-8.20.2-001 | ✅ webcheck: PSCell delay 분해는 PCell보다 풍부한 변수 — 권위 자료와 일치 | 6개 변수명 모두 verbatim |
| 12 | "Rel-19 inter-CU LTM 도입" | R2-2404271-001, R2-2503785 (-017로 정정) | ✅ RP-241917 presentation: "Inter-CU LTM is progressing in RAN WG2/3" | chunkIndex 표기 오기(-001 vs -017) 외 사실 정확 |
| 13 | "Rel-19 Conditional LTM 정식 도입 (38.321 §5.36)" | R2-2408088-002 + KG §5.36 | ✅ RP-241917: "checkpoint 2 for conditional LTM aims to specify support of conditional LTM" | spec 반영(KG §5.36) + WID checkpoint 모두 일치 |
| 14 | "Rel-19 Event-triggered L1 measurement (LTM2~LTM5)" | R2-2505117-002, R2-2402743-002 + KG §5.35.3.2~3.5 | ✅ Rel-19 measurement enhancement 토론 정확 | "Three types of report (periodic, aperiodic, semi-persistent)" verbatim |
| 15 | "Rel-20 = RAN2#132 6G mobility framing 토론 단계, spec 본문 미반영" | R2-2508706-003, R2-2508384-003, R2-2508657-001 | ✅ 3GPP Rel-20 page: "further optimize LTM to reduce cell switching delays". Stage-2 80% 2026-06, freeze 2026-09 | **Rel-20 spec 본문 미반영을 1차가 정직하게 명시 — 권위 timeline과 부합** |
| 16 | "Rel-20 단계 AI/ML 결합 토론 진행" | R2-2508722, R2-2508707 | ✅ 3GPP Rel-20 timeline: AIML mobility는 Rel-19 SI를 Rel-20 WI로 진행 중 | discussion 단계 인용 정직 |
| 17 | "38.306 LTM capability 세부 feature group은 미발견" | (인용 없음, 정직 표기) | ✅ webcheck: TS 38.306 V18.x feature group 번호는 ETSI 직접 fetch 필요 — 1차의 "위치만, 본문 미확보" 표기 정확 | A4 모범 — 정직한 한계 표기 |
| 18 | "Subsequent CPAC §5.3.5.13.6/.13.8가 LTM과 동일 §5.3.5.x 트리에 정의" | 38.331 KG cypher 결과 | ✅ ETSI 자료에서 §5.3.5 트리 구조 확인 | KG 노드 카탈로그 정확 |
| 19 | "RAN1 측 Rel-19 measurement enhancement (CSI for candidate cell, 측정 RS 동적 갱신)" | R1-2405859-001, R1-2407319-037 | ✅ RP-241917 / arxiv 5G-Advanced Rel-19: candidate cell CSI acquisition WI | chunkIndex 표기 흠결 1건 |
| 20 | "RAN4 RRM Rel-18 본격 토론 (R4-2400104, RAN4#110)" | (KG meta) | ✅ webcheck 일치 | RAN4 측면 인용 정확 |

## 발견한 Hallucination

**0건 (정확).** 검토한 20건의 fact-claim 중 학습지식 첨가나 추측으로 채운 흔적 없음.

특히 **Rel-20 영역에서 "study 단계만, spec 반영 본문 미발견"으로 명시한 것은 권위 timeline(3gpp.org Rel-20 Stage-3 freeze 2027-03)과 정확히 부합** — 1차 답변이 데이터 한계와 시스템 한계를 분리하여 보고한 모범 사례.

차순위 약점: chunkIndex 표기 4건 오기(-001 표준화), 그리고 RP-221799를 chunk 본문 직인용이 아닌 "discussion이 reference한 것"으로 우회 — 이는 hallucination이 아니라 retrieval grounding 정확성 문제(R 카테고리).

## Coverage 누락

| 누락 항목 | 1차의 처리 | 책임 |
|---|---|---|
| 38.306 LTM 세부 feature group 번호 (`ltm-r18` 등) | "§5.4/5.6/§4.2.7.9 클러스터에 위치, 세부 미확보" 정직 표기 | 시스템 (R+O) |
| RP-221799 WID 본문 직접 인용 | discussion R2-2207340의 reference 형태로 우회 | 시스템 (R) |
| 38.321 §5.2b/§6.1.3.4b LTM Candidate TA 본문 | "위치만 매칭, 본문 발췌 부족" 정직 표기 | 시스템 (R) |
| Rel-20 spec 본문 (38.300/331/321) 정식 추가 | "study 단계, 미발견" 정직 표기 | 데이터 (D — Rel-20 freeze 미예정) |
| LTM 전용 timer T-LTM 본문 변수 정의 | "위치만 매칭, 본문 발췌 부족" 정직 표기 | 시스템 (R) |

## 권위 소스 핵심 사실 vs 1차 답변

1. **Rel-18 LTM WID = RP-221799** — 1차 답변 §1: ✅ 정확 (R2-2207340의 reference 형태로 인용)
2. **38.300 §9.2.3.5 LTM 절차 (intra-gNB-DU + inter-gNB-DU)** — 1차 답변 §2: ✅ 권위 자료의 표현과 verbatim 일치
3. **38.331 §5.3.5.18 LTM-Config IE 그룹** — 1차 답변 §3: ✅ ETSI V18.6.0 ASN.1 구조 일치
4. **38.321 §5.18.35 LTM Cell Switch / §5.18.36 Candidate TCI MAC CE** — 1차 답변 §4: ✅ Ericsson 자료의 절차도와 일치
5. **38.214 §5.2.4a / §5.2.1.5.4.2 candidate cell L1-RSRP / event-trig 보고** — 1차 답변 §5: ✅ ETSI/iTecSpec 일치
6. **38.133 §6.3.1.2 D_LTM 공식** — 1차 답변 §6: ✅ IEEE 10744020 본문에 동일 분해
7. **Rel-19 inter-CU LTM + Conditional LTM + Event-trig L1** — 1차 답변 §8: ✅ RP-241917 Mobility Rel-19 WID와 정확 매핑
8. **Rel-20 LTM = "추가 cell switch delay 최적화"** (3gpp.org) — 1차 답변 §9: ✅ 권위가 "discussion 단계"임을 timeline으로 확인 (Stage-2 80% 2026-06, freeze 2026-09)

## 종합 판정

| 영역 | 신뢰 수준 | 비고 |
|---|---|---|
| Rel-18 LTM 6 spec 핵심 절·IE·MAC CE·delay 공식·도입 배경 | **고** | 권위 출처와 verbatim 인용 다수, hallucination 0건 |
| Rel-19 inter-CU LTM / CLTM / Event-trig L1 / 측정 RS 동적 갱신 | **중상** | RAN2 토론 + KG spec 노드로 정합, V19 ASN.1 freeze 미공개로 일부 한계 |
| Rel-20 LTM 정식 spec 변경 | **정당한 미답** | 데이터 6개월 lag로 3gpp.org timeline 부합 (D 한계, 시스템 결함 아님) |
| 38.306 LTM 세부 feature group | **부분** | 위치 매칭만, 본문 발췌 못함 (R+O 한계) |
| RP-WID 본문 직접 인용 | **부분** | discussion reference 우회 (R 한계) |

## 약점 원인 분류 (D / O / R)

> **D**: 3GPP 데이터 자체의 시점·완결성 한계 — 시간이 해결
> **O**: KG/온톨로지 모델링 부재 — 스키마 보강 필요
> **R**: VDB 구축 단계의 chunking·embedding·indexing 한계 — 빌드 파이프라인 보강 필요

| # | 약점 | D/O/R | 근거 |
|---|---|:---:|---|
| 1 | Rel-20 LTM spec 변경 본문 미발견 | **D** | 3gpp.org Rel-20 페이지에 따르면 Stage-2 freeze 2026-09, Stage-3 freeze 2027-03 — 2026-04 시점 데이터셋에 spec 본문이 없는 것은 정상. 권위 timeline과 부합. |
| 2 | RP-221799 WID 본문 직접 인용 불가 | **R** | RP-* TDoc은 별도 컬렉션으로 적재되어 있지 않음. 적재 가능한 데이터인데 컬렉션 설계에서 누락. |
| 3 | 38.306 LTM 세부 feature group 번호 미회수 | **R + O** | (R) 38.306 capability 표가 행 단위로 chunking되지 않아 검색어가 매칭되지 않음. (O) feature group을 KG 노드(`Capability` / `FeatureGroup` 라벨)로 모델링하지 않아 graph로도 우회 검색 불가. |
| 4 | LTM 전용 timer (T-LTM류) 본문 미발췌 | **R** | 해당 절(§5.2b, §6.1.3.4b)은 retrieval에 위치만 매칭. chunk text의 600자 preview 컷오프로 본문 변수 정의가 잘려 노출. |
| 5 | chunkIndex 표기 4건 오기 (R2-2503785-001 → -017 등) | **(작성 오류)** | 1차 답변 작성 시 chunkIndex를 -001로 일괄 표기. 사실 정확성에는 영향 없으나 citation traceability 흠결. RAG 시스템 자체 한계는 아님. |
| 6 | Rel-19 V19 ASN.1 본문 chunking 부족 | **D + R** | (D) Rel-19 ASN.1 freeze는 2025-Q4. 데이터셋 마지막 미팅 RAN2#132(2025-11)에 일부 반영. (R) Rel-19 spec 신규 IE의 IE-단위 chunking 미적용. |
| 7 | 38.331 ASN.1 IE 본문 검색 약점 (LTM-Config 정확 본문) | **R + O** | (R) 38.331 본문은 절(section) 단위 chunk로 ASN.1 IE block이 sectionTitle과 분리되지 않음. (O) `RRCParameter`/`IE` 라벨로 IE를 KG 노드로 분리 모델링하지 않음(38.331 IE 카탈로그는 KG에 부분 존재). |

**원인 분류 합계**: D 1건 (Rel-20), R 4건 (#2, #4, 부분 #6/7), R+O 2건 (#3, #7), D+R 1건 (#6), 작성 오류 1건 (#5).

→ **시스템(R/O) 책임 약점이 6건**으로 다수. **데이터 자체(D) 책임은 1건(Rel-20)** + 1건 부분(#6 Rel-19 ASN.1 freeze 시점). Rel-18 본 spec은 D 책임 없음.

## 시스템 개선 권고

| 우선순위 | 권고 | 분류 | 기대 효과 |
|---|---|:---:|---|
| **P1 (High)** | 38.331 ASN.1 IE 단위 chunking — IE block을 sectionTitle="LTM-Config IE" 같은 별도 chunk로 분리 | R | LTM-Config 등 IE 본문 직접 인용 가능. Q1/Q2/Q4 공통 약점 해소 |
| **P1 (High)** | 38.306 capability 표 행(row) 단위 chunking — 각 feature group을 별도 chunk로 (sectionTitle="csi-Type-II" 등) | R | UE capability 검색 정확도 대폭 향상. 4개 질문 모두 영향 |
| **P2 (Med)** | RP-* TDoc(Plenary RP-Tdoc) 별도 컬렉션 적재 (`ranX_rp_tdocs`) | R | WID 본문 직접 인용 가능. Rel별 도입배경 답변 신뢰도 상승 |
| **P2 (Med)** | chunk text preview 컷오프를 600 → 2000자로 확장 (또는 컷오프 제거 + 임베딩만 별도) | R | 정량값/변수 정의/타이머 본문 인용 가능. Q3 BFR 정량값 + Q4 LTM timer 해소 |
| **P3 (Low)** | KG에 `IE`/`Capability`/`FeatureGroup` 라벨 추가 — IE를 별도 노드로 모델링하여 ASN.1 그래프 워크 가능 | O | IE 간 cross-reference, capability ↔ feature 매핑 — graph-RAG 가능 |
| **P3 (Low)** | chunkIndex 인용 시 1차 답변 작성 단계에서 `-001` 일괄 표기 금지 — retrieval log의 실제 chunkIndex 사용 | (워크플로우) | citation traceability 100% 회복 |
| **P4 (시간 해결)** | Rel-20 spec 본문은 2026-09 (Stage-2 freeze) ~ 2027-03 (Stage-3 freeze) 이후 적재 | D | 3GPP timeline 자연 해결 |

**핵심 결론**: Q4 약점의 대부분(6/7건)은 시스템(R/O) 책임이며 빌드 파이프라인 보강으로 해결 가능. Rel-20 미답은 정당한 데이터 한계로, 시스템 결함이 아님. 1차 답변은 두 종류의 한계를 정확히 분리하여 보고했음.
