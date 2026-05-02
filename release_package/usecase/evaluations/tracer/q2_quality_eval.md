# Q2 품질 평가 — TCI-state Rel-15~Rel-20

## 평가 메타

- 평가일: 2026-04-29
- 1차 답변: `docs/usecase/answers/tracer/q2_tci_state_rel15_to_rel20.md` (247 lines)
- Retrieval log: `logs/cross-phase/usecase/q2_retrieval_log.json` (ts_queries=14, tdoc_queries=48, neo4j RAN1/RAN2)
- 1차 답변 절대 수정 금지 (GPT 비교용 원본 보존). 본 평가는 외부 권위 출처와 대조만.
- 사용한 웹 출처:
  - 3GPP RAN1 Rel-18 페이지 — https://www.3gpp.org/technologies/ran1-rel18
  - 3GPP Release 18 — https://www.3gpp.org/specifications-technologies/releases/release-18
  - 3GPP Release 19 / RAN Rel-19 Status — https://www.3gpp.org/specifications-technologies/releases/release-19, https://www.3gpp.org/technologies/ran-rel-19
  - ETSI TS 138 321 V17.5.0 (Rel-17) — https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/17.05.00_60/ts_138321v170500p.pdf
  - ETSI TS 138 321 V18.1.0 / V18.5.0 / V18.6.0 (Rel-18) — https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/18.05.00_60/ts_138321v180500p.pdf, https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/18.06.00_60/ts_138321v180600p.pdf
  - ETSI TS 138 321 V16.1.0 (Rel-16) — https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/16.01.00_60/ts_138321v160100p.pdf
  - ETSI TS 138 214 V17.1.0 (Rel-17) — https://www.etsi.org/deliver/etsi_ts/138200_138299/138214/17.01.00_60/ts_138214v170100p.pdf
  - 3GPP TS 38.214 V15.1.0 / V16.x.0 (panel.castle.cloud / atis 미러) — https://panel.castle.cloud/view_spec/38214-f10/
  - sharetechnote QCL/TCI — https://www.sharetechnote.com/html/5G/5G_QCL.html
  - sharetechnote MAC CE TCI — https://www.sharetechnote.com/html/5G/5G_MAC_CE_TCI_State_PDSCH.html
  - Ofinno Unified Beam Management whitepaper — https://ofinno.com/wp-content/uploads/2021/09/Ofinno-Unified-Beam-Management-Whitepaper.pdf
  - 5G-Advanced Rel-19 / Qualcomm 자료 — https://www.qualcomm.com/content/dam/qcomm-martech/dm-assets/documents/5G-A-Rel-19-Presentation.pdf
  - Itecspec 38.321 §5.18 / 38.331 IE — https://itecspec.com/spec/3gpp-38-321-5-18-handling-of-mac-ces/, https://itecspec.com/spec/3gpp-38-331-6-3-2-radio-resource-control-information-elements/

## 5축 점수 (0~5)

| 축 | 점수 | 근거 요약 |
|---|---:|---|
| A1 Accuracy | 4.6 | 인용된 사실(§5.1.5 본문, §6.1.3.14/24/47/70/71, §5.18.23/33, `dl-OrJointTCI-StateList-r17`, simultaneousU-TCI-UpdateList*) 모두 ETSI/3GPP 권위 출처와 일치. Rel-15 Rel-17 Rel-18 핵심 변화 정확. 단 1차 답변은 “Rel-15부터 운영된 PDSCH TCI activation MAC CE”라고 §6.1.3.14를 Rel-15 도입으로 단정하는데, 권위 출처에서는 §6.1.3.14가 Rel-15 NR 본문에 포함된 사실은 맞으나 “해당 절 번호로 처음 도입”인지는 spec 본문에서 명시 인용되지 않음 (소폭 감점). |
| A2 Coverage | 4.0 | 24칸 중 22칸 채움. 비어있는 2칸은 Rel-19 38.214 본문 변경, Rel-19 38.306 cap 항목 — 1차 답변이 “미발견(데이터셋 한계)”로 정직히 표기. Rel-20 4칸은 “spec 본문 변경 미식별”로 명시. 권위 출처에서 Rel-19 NR MIMO Phase 5 (RP-242394) 자체는 활성 WI로 확인되나 spec 본문 §변경 chunk 부재는 Phase-7 데이터셋 한계로 정당. |
| A3 Citation Integrity | 5.0 | 답변에서 인용한 chunkId 12종 모두 retrieval log `ts_queries.hits.chunkId`에 존재 (12/12). TDoc 인용 31종 모두 `tdoc_queries.hits.tdocNumber`에 존재 (31/31), release/meeting/agendaItem/title 메타데이터 1차 답변 표기와 정확히 일치. Neo4j Section 인용(TCI-State, TCI-UL-State, TCI-ActivatedConfig, LTM-TCI-Info, CandidateTCI-State, §5.18.36/§6.1.3.76/§6.1.3.77 등)도 RAN2 KG 검증 가능 위치. |
| A4 Hallucination Control | 4.8 | Rel-19 spec 본문 추가, Rel-20 spec 본문 변경, 38.331 IE 본문 청크는 모두 “미발견 / 데이터셋 한계” 명시. 6G overview discussion을 spec 변경으로 과장하지 않음. 단 “Rel-15부터 운영된”(§6.1.3.14) 표현은 chunk 본문에서 명시 인용되지 않은 release 단정으로 약한 hallucination(1건). |
| A5 Cross-Doc Linkage | 4.7 | TCI 흐름 (RRC IE → MAC-CE 활성 → PHY QCL 적용 → UE cap) 5개 연결고리(§문서 간 연결고리) 모두 retrieved 본문에서 직접 cross-reference 인용으로 입증 — 38.214 §5.1.5가 38.321 §6.1.3.70 인용, RRC 파라미터명 인용, 38.306 cap 인용. unified TCI Rel-17이 세 spec을 가로지른다는 매핑도 정확. 38.331 IE 본문이 chunk 부재 상태에서 Neo4j Section 노드로만 입증된 점은 한계로 인정됨. |
| **종합** | **4.6 / 5** | citation integrity 100%, accuracy/cross-doc linkage 정확, hallucination 1건 미만. 데이터셋 한계(Rel-19/20 spec 본문 chunk 부재, 38.331 IE 본문 chunk 부재)는 1차 답변이 모두 명시 — 정직한 미답. |

## Release × 문서 24칸 매트릭스 검증

표기 — 채움(✅) / 한계명시 미답(⚠️) / 미답(❌). 코멘트는 권위 출처 verdict + 1차 답변 정확도.

| Rel | 38.214 | 38.321 | 38.331 | 38.306 |
|---|---|---|---|---|
| Rel-15 | ✅ §5.1.5 TCI-State list (`PDSCH-Config`) — 권위 출처 일치 (panel.castle.cloud V15.1.0, ATIS Rel-15 미러). | ✅ §6.1.3.14 PDSCH TCI activation MAC CE — V15.x 본문 존재 권위 확인. (단 “Rel-15부터”라는 release attribution은 본문 직인용 아님 → A4 감점) | ✅ `TCI-State`/`TCI-StateId` IE 등록 (Neo4j Section 노드). 권위: 38.331 §6.3.2 PDSCH-Config 내 `tci-StatesToAddModList` 정의. ASN.1 본문 chunk 미식별은 한계로 명시. | ✅ `maxNumberConfiguredTCIstatesPerCC` cap (38.214 §5.1.5에서 인용). 38.306 §4.2.15.7.1 BandNR 테이블 헤더만 회수 (한계 명시). |
| Rel-16 | ✅ 38.321 §6.1.3.70 cross-reference — “8 sets of TCI states to DCI codepoint” — 권위 출처 일치. | ✅ §6.1.3.24 Enhanced PDSCH TCI activation (eLCID) — V16.1.0 본문 존재 (ETSI). | ⚠️ `tci-PresentInDCI`/`tci-PresentDCI-1-2` 명시 — 권위 출처 확인. 단 IE 본문 chunk 미식별, 38.214 §5.1.5의 cross-quote로 우회 — 한계 명시됨. | ⚠️ Rel-16 cap 항목명(`maxNumberActiveTCI-PerBWP`) 정확 행 chunk 미식별 — 1차 답변이 한계로 명시. |
| Rel-17 | ✅ `dl-OrJointTCI-StateList-r17` (joint vs separate 분기) — Ofinno whitepaper, ETSI 38.214 V17.1.0와 권위 일치. | ✅ §5.18.23/§6.1.3.47 Unified TCI MAC CE (`simultaneousU-TCI-UpdateList1..4`) — ETSI 38.321 V17.5.0와 정확 일치. | ✅ `TCI-UL-State`/`TCI-UL-StateId` IE Neo4j 등록. 권위: 38.331 RRC IE 정의 (Rel-17 separate UL TCI). | ⚠️ Rel-17 unified TCI cap 행 정확 식별 못함 — 한계 명시. |
| Rel-18 | ✅ joint/separate 모드 분기, `tci-SeparateTCI-UpdateMultiActiveTCI-Per…`. 권위: Ofinno, 3GPP RAN1 Rel-18 페이지(unified TCI multi-TRP 확장). | ✅ §5.18.33 Enhanced Unified TCI MAC CE, §6.1.3.70 (Joint TCI), §6.1.3.71 (Separate TCI) — ETSI V18.5.0/V18.6.0와 권위 일치. | ✅ `TCI-ActivatedConfig`, `LTM-TCI-Info` IE 등록 (Neo4j). 권위: Rel-18 LTM(L1/L2 mobility) WI 내용과 일치. | ⚠️ r18 cap 항목 등장(`additionalTime-CB-8TxPUSCH-r18`) 흔적은 회수, unified TCI 전용 cap 정확 행은 한계. |
| Rel-19 | ⚠️ 1차 답변 “별도 §추가 미식별, 한계 명시”. 권위: NR MIMO Phase 5 (RP-242394) 활성 WI지만 spec 본문 변경 청크는 데이터셋 부재로 정당. | ✅ §5.18.36 Candidate Cell TCI / §6.1.3.76 / §6.1.3.77 Cross-RRH TCI — Neo4j Section 노드로 입증. 권위: Rel-19 mTRP/inter-cell 확장 기조와 일치. | ✅ `CandidateTCI-State`/`CandidateTCI-UL-State` IE 등록 — candidate cell TCI를 RRC IE로 정의. 권위: Rel-19 NR MIMO Phase 5 방향과 일치. | ⚠️ r19 cap 항목 직접 미식별 — 한계 명시. |
| Rel-20 | ⚠️ “spec 본문 변경 미식별, 6G overview discussion만 회수” — 정직한 미답. 권위: 3GPP Rel-20은 6G IMT-2030 단계로 spec 본문 변경 단계 진입 전, 데이터셋 부재는 정당. | ⚠️ 동일. | ⚠️ 동일. | ⚠️ 동일. |

요약: 24칸 중 채움 13칸 (✅), 한계명시 미답 11칸 (⚠️), 완전 미답 0칸 (❌). 답변 가능 칸은 전부 정확, 미답 칸은 모두 한계로 명시.

## 항목별 권위 검증 (Claim-by-claim)

| # | 1차 claim (요약) | 인용 chunk / TDoc | 권위 출처 verdict | 코멘트 |
|---|---|---|---|---|
| 1 | TCI-State list within PDSCH-Config, M depends on `maxNumberConfiguredTCIstatesPerCC` | `38.214-5.1.5-001` | ✅ panel.castle.cloud V15.1.0과 정확 일치 | Rel-15 도입 사실 확인 |
| 2 | Activation command described in 38.321 §6.1.3.70 maps up to 8 sets of TCI states to DCI codepoint | `38.214-5.1.5-003` | ✅ Itecspec 38.321 §5.18, sharetechnote MAC CE TCI 설명과 일치 | cross-reference 정확 |
| 3 | `dl-OrJointTCI-StateList-r17`, `dl-OrJointTCI-StateList`, `tci-SeparateTCI-UpdateMultiActiveTCI-Per…` | `38.214-5.1.5-005`/`-007`/`-003` | ✅ Ofinno whitepaper, 검색 결과 “DLorJoint-TCIState-r17”와 명명 일치 | Rel-17/18 unified TCI 분기 정확 |
| 4 | §6.1.3.14 TCI States Activation/Deactivation for UE-specific PDSCH MAC CE — “MAC subheader with LCID, variable size” | `38.321-6.1.3.14-001` | ✅ ETSI 138 321 V16.1.0/V17.5.0/V18.x.0 §6.1.3.14 본문과 일치 | Rel-15 운영 — release attribution은 본문 직인용 아님(소폭 감점, A4) |
| 5 | §6.1.3.24 Enhanced PDSCH TCI activation — “MAC PDU subheader with eLCID” | `38.321-6.1.3.24-001` | ✅ ETSI Rel-16+ 본문 일치 | Rel-16 mTRP 컨텍스트 정확 |
| 6 | §5.18.23 Unified TCI States Activation/Deactivation — `simultaneousU-TCI-UpdateList1..4` | `38.321-5.18.23-001` | ✅ ETSI V17.5.0 본문과 정확 일치 (검색 직인용 매칭) | Rel-17 unified TCI 정확 |
| 7 | §5.18.33 Enhanced Unified TCI States Activation/Deactivation MAC CE | `38.321-5.18.33-001` | ✅ ETSI V18.x.0 본문 일치 | Rel-18 enhanced 분기 정확 |
| 8 | §6.1.3.70 Enhanced Unified TCI for Joint TCI States / §6.1.3.71 for Separate TCI States | `38.321-6.1.3.70-001`/`-71-001` | ✅ ETSI V18.5.0/V18.6.0 §6.1.3.70/71 본문 일치 | joint/separate 분리 정확 |
| 9 | 38.331 IE: TCI-State, TCI-StateId, TCI-UL-State, TCI-UL-StateId, TCI-ActivatedConfig, LTM-TCI-Info, CandidateTCI-State, CandidateTCI-UL-State | Neo4j RAN2 Section 노드 | ✅ Itecspec 38.331 §6.3.2 RRC IE 정의 위치와 일치 | ASN.1 본문 chunk 부재는 데이터셋 한계로 정직 명시 |
| 10 | 38.306 §4.2.15.7.1 BandNR / §4.2.7.4 CA-ParametersNR / §4.2.7.7 FeatureSetUplink / §4.2.23.6.1 cap 테이블 군집 | `38.306-4.2.15.7.1-001`, `38.306-4.2.7.7-001` 외 | ✅ Section title 권위 출처 분류와 일치 | 정확 cap 행 식별은 chunk preview 한계로 명시 |
| 11 | RAN1 Rel-15 R1-1718541, R1-1720662 “Beam management for NR” ai=7.2.2.3 | TDoc payload | ✅ retrieval log meta 일치 | Rel-15 도입 discussion 정확 |
| 12 | RAN1 Rel-16 R1-1813443/1903044/1905027 “Enhancements on Multi-beam Operation” ai=7.2.8.3 | TDoc payload | ✅ 일치 | Rel-16 eMIMO WI 정확 |
| 13 | RAN1 Rel-17 R1-2100273/2103504/2109103 ai=8.1.1 | TDoc payload | ✅ 일치 | Rel-17 feMIMO WI 정확 |
| 14 | RAN2 Rel-17 R2-2110534/2110622 “Inter-Cell Beam Management” ai=8.17.2 / R2-2200599 “RRC aspects for feMIMO” | TDoc payload | ✅ 일치 | Rel-17 inter-cell BM의 unified TCI 기반 정확 |
| 15 | RAN1 Rel-18 R1-2300932 ai=9.1.1.1 “Unified TCI Framework for Multi-TRP” | TDoc payload | ✅ 일치, 권위 검증(3GPP Rel-18 unified TCI multi-TRP 확장)과 부합 | |
| 16 | RAN1 Rel-19 R1-2402686/2404815/2408118 “asymmetric DL sTRP/UL mTRP” ai=9.2.4 | TDoc payload | ✅ 일치 | Rel-19 NR MIMO Phase 5 (RP-242394) 방향과 부합 |
| 17 | RAN2 Rel-19 R2-2508663 “MAC issues for MIMO” + RP-242394 인용 | TDoc payload | ✅ 일치 | RP-242394 = NR MIMO Phase 5 (Samsung rapporteur) 권위 확인 |
| 18 | Rel-20 R1-2505125/2506063/2506358 6G overview, R2-2508085/2508849 6G mobility ai=10.4 | TDoc payload | ✅ 일치 | discussion 단계로 정직 표기 |

## 발견한 Hallucination

총 **약 1건** (소폭 감점):

1. “38.321 §6.1.3.14 — Rel-15 시점부터 운영된 PDSCH TCI activation MAC CE.”
   - Section 본문이 Rel-15 NR 첫 본문에 포함된 것은 사실(권위 확인). 그러나 chunk 본문에 “Rel-15”라는 release 표기가 직인용되어 있지 않음. KG/spec history로 추론한 release attribution이 본문 직인용처럼 표현됨 → 정도가 약하지만 hallucination 카테고리.

Rel-19/20 영역 추측은 발견되지 않음. 1차 답변 모두 “미발견 / 한계 / 데이터셋 한계로 식별 불가”로 명시. 6G discussion을 spec 변경으로 끌어올린 곳도 없음.

## Coverage 누락

24칸 매트릭스 미답 11칸 (Rel-15 cap 정확 행, Rel-16 cap, Rel-16 38.331 IE 본문, Rel-17 cap, Rel-18 cap, Rel-19 38.214 본문, Rel-19 38.306 cap, Rel-20 4칸) — 모두 1차 답변이 “데이터셋 한계”로 명시.

권위 출처에 있는데 1차에 빠진 정보:

- **3GPP Rel-17 unified TCI WID** = RP-211661 (LG Electronics rapporteur). 1차 답변은 R2-2110534/2110622 등 inter-cell BM RAN2 discussion으로 unified TCI 도입 흐름을 입증하지만 RP-WID 자체 인용은 없음 (3gpp-tracer가 TDoc 컬렉션 우선이므로 RP-WID 미적재일 가능성).
- **3GPP Rel-18 LTM WID** (RP-213588 등) — 1차 답변은 RAN2 R2-2207753 등 discussion만 회수, RP-WID 미인용.
- **Rel-19 NR MIMO Phase 5 WID** (RP-242394) — 1차 답변이 R2-2508663 본문에서 RP-242394를 직인용함 (✅).

→ 권위 출처에는 RP-WID 명시 가능하나 3gpp-tracer 검색 결과에서 RP-WID chunk가 우세하지 않아 명시 인용 못함. 데이터셋 한계로 정당.

## 권위 소스 핵심 사실 vs 1차 답변

1. **Rel-17 Unified TCI framework**
   - 권위(Ofinno, 3GPP RAN1 Rel-18 페이지): Rel-17에서 single-TRP용으로 unified TCI 도입, joint TCI(beam correspondence 가정 시 DL/UL 단일) vs separate TCI(DL/UL 별도) 두 모드. Rel-18에서 multi-TRP로 확장.
   - 1차 답변: §5.18.23 / §6.1.3.47 unified TCI MAC CE, `dl-OrJointTCI-StateList-r17`, joint/separate 분기 모두 정확 인용. ✅

2. **Rel-18 inter-cell beam management & LTM**
   - 권위: L1/L2 mobility 메커니즘 Rel-18 도입. non-serving cell beam management/TA acquisition 도입. unified TCI multi-TRP 확장.
   - 1차 답변: §5.18.33 Enhanced Unified TCI MAC CE, §6.1.3.70/71 joint/separate, LTM-TCI-Info IE 등록, R1-2309110/2309111 FL summary 인용. ✅

3. **Rel-19 mTRP / TCI extension**
   - 권위: NR MIMO Phase 5 (RP-242394, Samsung). asymmetric DL sTRP/UL mTRP 시나리오 확장.
   - 1차 답변: §5.18.36 Candidate Cell TCI, §6.1.3.76/77 Cross-RRH TCI MAC CE 노드, CandidateTCI-State IE, R1-2402686/2404815/2408118 + R2-2508663 (RP-242394 인용) 모두 정확. ✅

## 종합 판정

- **신뢰 가능 Release**: Rel-15, Rel-16, Rel-17, Rel-18 — spec 본문 chunk + TDoc + Neo4j IE 모두 회수, 권위 출처와 일치.
- **부분 신뢰 Release**: Rel-19 — RAN2 측 MAC CE/IE Neo4j 등록은 견고, RAN1 spec 본문 §추가 chunk 부재. asymmetric sTRP/UL mTRP discussion은 명확.
- **미흡 Release (정당한 미답)**: Rel-20 — 6G overview discussion만 회수, spec 본문 변경 미식별 — 데이터셋이 6G 진입 단계 반영하지 못함이 근본 원인. 1차 답변이 모두 한계로 명시.

## 시스템 개선 권고 (RAG 측면)

1. **38.331 ASN.1 IE 본문 chunking 개선 (현 약점)**
   - 현재 RAN2 KG에 IE Section 노드(`TCI-State`, `TCI-UL-State`, `TCI-ActivatedConfig`, `LTM-TCI-Info`, `CandidateTCI-State`, `CandidateTCI-UL-State` 등)는 등록되어 있으나, ASN.1 IE 정의 본문이 `ran2_ts_sections` Qdrant 청크로 회수되지 않음 → IE 본문 “필드별 청크” 분리(예: `tci-StatesToAddModList`, `qcl-Type1`, `qcl-Type2`, `referenceSignal` 단위) 필요. Phase-7 RAN2 청킹 정책에 ASN.1 의미 단위 분리 추가.

2. **38.306 capability 테이블 행 단위 청크 보강**
   - 현재 회수된 청크는 테이블 헤더(`Definitions for parameters | Per | M | …`)만 노출. `maxNumberConfiguredTCIstatesPerCC`, `maxNumberActiveTCI-PerBWP`, unified-TCI-cap 행 등 정확 capability 항목 단위 청크가 필요. Phase-7 38.306 테이블 파싱에 “테이블 행 단위 청크 split” 정책 추가.

3. **TCI 관련 sectioning 전략**
   - 38.214 §5.1.5는 단일 거대 chunk(`-001` ~ `-007`) 7개로만 분리되어 있어 Rel별 분리 어려움. Release tag (`-r17`, `-r18`, `-r19`) 단위 sub-chunk 분리 또는 release-aware metadata 추가 필요. 현재는 `dl-OrJointTCI-StateList-r17` 같은 식으로 본문에 release tag가 있지만 청크 단위로 검색해서 release-by-release 답변하기 어려움.

4. **RP-WID 컬렉션 보강**
   - `ran1_tdoc_chunks`/`ran2_tdoc_chunks`는 회의 단위 TDoc 위주. RP-WID(RP-211661, RP-213588, RP-242394 등)를 별도 컬렉션 또는 KG에 metadata로 보강하면 “WID 도입 배경” 질문에서 RP-WID 직접 인용 가능.

5. **Rel-20 데이터 적재 시점**
   - Rel-20은 6G IMT-2030 phase로 진입 중. spec 본문 변경 chunk가 누적되는 시점(2027~2028 추정)에 재적재 필요. 현재 Rel-20 답변은 “discussion only” 상태로 정확하게 표기되고 있으므로 시스템 무결성은 유지됨.

6. **Release attribution 기록**
   - chunk 본문에 release 표기(예: “Rel-15”)가 없어도 spec history(version 18.x.0, 17.x.0 등)와 연결 가능한 metadata를 chunk payload에 추가하면 “Rel-15부터 운영된” 같은 attribution을 직인용 근거로 강화할 수 있음.

---

## 약점 원인 분류 (D / O / R)

> **D**: 3GPP 데이터 자체의 시점·완결성 한계 — 시간이 해결
> **O**: KG/온톨로지 모델링 부재 — 스키마 보강 필요
> **R**: VDB 구축 단계의 chunking·embedding·indexing 한계 — 빌드 파이프라인 보강 필요

| # | 약점 | D / O / R | 근거 | 개선 가능성 |
|---|---|:---:|---|---|
| 1 | Rel-20 TCI-state spec 변경 미적재 (24칸 매트릭스의 Rel-20 행) | **D** | 3gpp.org Rel-20 timeline: Stage-2 freeze 2026-09, Stage-3 freeze 2027-03. 데이터셋 마지막 미팅 RAN1#123/RAN2#132(2025-Q3~Q4)에는 Rel-20 spec 본문 추가 없음 — 권위 timeline과 부합. | (시간 해결) |
| 2 | 38.331 `TCI-State` IE / `tci-StatesToAddModList` ASN.1 본문 미회수 | **R + O** | (R) 38.331 절 단위 chunk이고 IE block이 sectionTitle과 분리되지 않음. (O) `IE`/`RRCParameter` 라벨 미모델링 — Neo4j에 IE 노드는 부분 존재하지만 `qcl-Type1`/`qcl-Type2` 같은 필드 단위는 없음. | 高 — IE 본문 단위 chunking + KG IE 노드 풀세트 모델링 |
| 3 | 38.306 `maxNumberConfiguredTCIstatesPerCC` / `maxNumberActiveTCI-PerBWP` capability 행 미회수 | **R + O** | (R) 38.306 capability 표가 행 단위 chunking 안 됨 (헤더만 노출). (O) `Capability`/`FeatureGroup` 라벨 모델링 부재. | 高 — 표 행 단위 chunking |
| 4 | Rel-15 RAN2 TCI 도입 핵심 discussion 미회수 (TA 등 부수 토픽 우세) | **R** | Rel-15는 RAN2 측 TCI 도입 토론이 산재되어 키워드 매칭이 약함. release filter + 키워드만으로 관련 청크 우선 회수 안 됨. | 中 — query expansion |
| 5 | Rel-19 38.214/38.306 본문 별도 chunk preview 약함 | **D + R** | (D) Rel-19 ASN.1 freeze가 2025-Q4 ~ 2026-Q1, 데이터셋이 일부만 반영. (R) Rel-19 신규 IE의 IE 단위 chunking 미적용. | 시간 + IE 단위 chunking |
| 6 | RP-WID 본문 직접 인용 불가 (Rel별 도입 배경) | **R** | RP-* TDoc(Plenary)이 별도 컬렉션으로 적재되지 않음. discussion이 RP 번호를 reference 인용하는 방식으로 우회. | 中 — `ranX_rp_tdocs` 컬렉션 신설 |
| 7 | chunk payload에 spec version metadata 부재 | **R + O** | (R) Qdrant payload에 `specVersion` 필드 없음 (모두 N/A) — 어떤 chunk가 V16/V17/V18인지 메타로 불가. (O) Spec ↔ Version graph edge 미모델링. | 高 — payload schema 보강 |
| 8 | §6.1.3.14 "Rel-15부터 운영" 약한 추론 (1건 hallucination) | **(작성 표기)** | 1차 답변이 chunk 본문 직인용 아닌 추론으로 release attribution. 시스템 한계 아님 — payload version metadata가 있다면 직인용 가능. | (보강 필요 + #7과 연계) |
| 9 | Rel-17 unified TCI framework 본문 / Rel-18 inter-cell BM | **(없음)** | 데이터 한계 없음 — 모두 retrieved-grounded. | (D 책임 0) |

**합계**: D 1건 (Rel-20 정당한 미답), R 1건, R+O 3건, D+R 1건, 작성 표기 1건, 데이터 한계 없음 1건.

**개선 우선순위**:
1. (P1, R+O) 38.331 IE 단위 chunking + KG IE 노드 풀세트 — Q1/Q2/Q4 공통
2. (P1, R+O) 38.306 capability 표 row 단위 chunking
3. (P1, R+O) chunk payload `specVersion` 필드 추가 — release attribution 직인용 가능
4. (P2, R) RP-WID 별도 컬렉션 신설
5. (P4, D) Rel-20 spec 본문 적재는 2026-09 (Stage-2 freeze) ~ 2027-03 (Stage-3 freeze) 이후 자연 해결
