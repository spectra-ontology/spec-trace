# Q2 3-way 비교 — TCI-state Rel-15~Rel-20

> 평가일: 2026-04-29 / 평가 대상: spec-trace 3gpp-tracer / GPT / Claude의 Q2 답변
> 권위 출처: ETSI TS 138.214/321/331/306 (V15~V18.x), 3GPP RAN1/RAN2/RAN-Rel18~19 페이지, Ofinno Unified Beam Management whitepaper, sharetechnote QCL/TCI, Itecspec 38.321 §5.18 / 38.331 §6.3.2 (`docs/usecase/evaluations/tracer/q2_quality_eval.md` 인용 셋)

## 메타

| 모델 | 파일 | 라인 | 인용 형식 | 외부 도구 |
|---|---|---:|---|---|
| 3gpp-tracer | `docs/usecase/answers/tracer/q2_tci_state_rel15_to_rel20.md` | 247 | `[spec §sec, chunkId=...]` / `[tdoc, mtg, type, ai=..., release]` / `[Neo4j RAN2, sectionNumber=...]` | 없음 (Qdrant `ran{1,2}_ts_sections`/`ran{1,2}_tdoc_chunks` + Neo4j RAN1/RAN2 only) |
| GPT | `docs/usecase/answers/gpt/q2_tci_state_rel15_to_rel20.md` | 323 | spec 명 (`38.214`, `38.321`) + IE 명 + section/IE 명만 (URL/§번호/chunkId 없음) | LLM 사전지식 + 일반 통용 자료 (5G Americas, Qualcomm 등 끝 참고문헌만) |
| Claude | `docs/usecase/answers/claude/q2_tci_state_rel15_to_rel20.md` | 497 | spec §번호 + ASN.1 코드블럭 + WID 번호 (`RP-170739` 등) — 단 chunkId/URL 없음, ASN.1 본문은 모델 생성 | LLM 사전지식 (38.133 RRM Test 언급, 38.300 인용) |

---

## 5축 점수 비교

| 축 | tracer | GPT | Claude | 1위 | 코멘트 |
|---|---:|---:|---:|---|---|
| A1 Accuracy | 4.6 | 3.6 | 3.4 | tracer | tracer는 §5.18.23 / §6.1.3.47 / §6.1.3.70/71 / `dl-OrJointTCI-StateList-r17` 등 권위 ETSI 본문과 1:1 직인용 일치. GPT는 spec 명만 등장하고 §번호 없이 IE만 나열 — 일반 흐름은 정확하나 검증 불가 사실 다수. Claude는 ASN.1 본문(IE 정의)을 직접 작성했는데 `LCID 53`/`LCID 49`/`LCID 56` 등 LCID 번호와 `64-bit bitmap`, `T_BAT`, `beamAppTime-r17` 등 sharetechnote 수준 디테일이 권위 본문과 불일치 또는 미검증 (할루시네이션 후보). |
| A2 Coverage | 4.0 | 3.6 | 4.4 | Claude | 24칸 중 tracer 13✅/11⚠️/0❌ (Rel-19/20 한계 명시), GPT 24칸 모두 셀 채움 (단 Rel-20은 "frozen 아님" 가드), Claude 24칸 모두 채움 + Rel-20에 ASN.1 draft까지 포함. 단 Claude의 "Rel-19 = AI/ML 기반 BM"은 권위 출처(NR MIMO Phase 5 / RP-242394)와 다름. |
| A3 Citation Integrity | 5.0 | 1.5 | 2.0 | tracer | tracer는 chunkId 12/12 + TDoc 31/31 retrieval log에 존재 검증됨 (`q2_quality_eval.md` §A3=5.0). GPT는 §번호 없이 IE 명만 — 검증 가능성 매우 낮음. Claude는 §번호+WID 번호 (RP-170739/RP-181433/RP-193133/RP-211583/RP-234037/RP-234039)를 제시했지만 retrieval 근거 없음, 모델 사전지식 — 외부 권위로 일부 검증 가능하나 chunkId 수준 검증 불가. |
| A4 Hallucination Control | 4.8 | 3.5 | 2.8 | tracer | tracer Rel-19/20 영역 모두 "데이터셋 한계로 미식별" 명시, hallucination 1건만 (§6.1.3.14 Rel-15 attribution). GPT는 Rel-20을 "frozen 아님" 가드로 처리하지만 Rel-19 CLTM/inter-cell BM Rel-19 도입 단정은 근거 부족 (RP-WID 미명시). Claude는 Rel-19를 "AI/ML for Beam Management"로 단정 + Rel-20 "Cross-Carrier TCI / Sub-band TCI / NTN TCI" + ASN.1 `TCI-State-r20` 코드블록 작성 — Rel-20 spec 미확정 영역 추측 채움 명백. |
| A5 Cross-Doc Linkage | 4.7 | 4.0 | 4.5 | tracer | tracer는 38.214 §5.1.5 본문이 38.321 §6.1.3.70 직인용하는 cross-reference 등 5개 연결고리 retrieved-grounded (권위 검증 ✅). GPT는 RRC→MAC→DCI→PHY→Cap 흐름 단순 다이어그램만. Claude는 release별 mermaid-style flow + §8.2 Rel-17 Unified TCI cross-document flow + §8.3 ID 공간/활성 TCI 개수/QCL Type D rule 정합성 checkpoint까지 — 매핑은 풍부하나 일부 항목(beamAppTime ↔ T_BAT) 권위 검증 부족. |
| **종합** | **4.6** | **3.2** | **3.4** | tracer | tracer가 5축 중 4축에서 1위 (A2만 Claude). citation integrity 차이가 결정적. |

---

## Release × 문서 24칸 매트릭스 비교

표기: T=tracer / G=GPT / C=Claude. ✅=정확 채움, ⚠️=부분/한계 명시, ❌=미답 또는 부정확.

| Rel | 38.214 | 38.321 | 38.331 | 38.306 |
|---|---|---|---|---|
| Rel-15 | T:✅ §5.1.5 TCI-State list, M=`maxNumberConfiguredTCIstatesPerCC` 직인용 (chunkId=`38.214-5.1.5-001`)<br>G:✅ "PDSCH/PDCCH/CSI-RS QCL assumption 도입" (§번호 없음)<br>C:✅ §5.1.5 PDSCH/PDCCH default rule + CORESET 0 SS/PBCH QCL — 권위 일치 | T:✅ §6.1.3.14 PDSCH TCI activation MAC CE 본문 직인용<br>G:✅ "PDSCH TCI act/deact, PDCCH TCI indication" (§ 없음)<br>C:⚠️ LCID 53/52/47 + 64-bit bitmap 형식 작성 — LCID 번호 권위 출처 미검증 (sharetechnote 수준 추정값) | T:⚠️ `TCI-State`/`TCI-StateId` IE 등록 (Neo4j Section 노드만, ASN.1 본문 없음 — 한계 명시)<br>G:✅ `TCI-State`, `PDSCH-Config.tci-StatesToAddModList`, CORESET TCI<br>C:✅ ASN.1 `TCI-State`/`QCL-Info` 정의 작성 — 구조는 권위 일치, 다만 모델 생성 본문 | T:⚠️ §4.2.15.7.1 BandNR 테이블 헤더 회수 (한계 명시)<br>G:✅ "configured TCI 수, active TCI per BWP/CC"<br>C:✅ `maxNumberConfiguredTCIStatesPerCC: {n4..n128}`, `maxNumberActiveTCI-PerBWP: {n1,n2,n4,n8}` — 권위 일치 |
| Rel-16 | T:✅ §5.1.5에서 38.321 §6.1.3.70 cross-ref ("8 sets to DCI codepoint")<br>G:✅ "single-DCI mTRP 복수 TCI" (§ 없음)<br>C:✅ §5.1.5 5가지 mTRP scheme (1a/2a/2b/3/4) — 권위 일치 (sharetechnote/Ofinno) | T:✅ §6.1.3.24 Enhanced PDSCH TCI activation (eLCID)<br>G:✅ "enhanced PDSCH TCI activation, mTRP TCI mapping"<br>C:⚠️ "Enhanced PDSCH TCI MAC CE LCID 49" — LCID 번호 검증 불가 | T:⚠️ `tci-PresentInDCI`/`tci-PresentDCI-1-2` 명시 (38.214 §5.1.5에 인용됨)<br>G:✅ "simultaneous TCI update list, serving-cell 그룹 activation" (Rel-18 기능을 Rel-16으로 잘못 표기)<br>C:✅ `RepetitionSchemeConfig-r16` ASN.1 — 일치 | T:⚠️ cap 테이블 군집만 회수 (정확 행 미식별)<br>G:✅ "mTRP/복수 TCI cap"<br>C:✅ `mTRP-PDSCH-r16`, `maxNumberSimultaneousTCI-States-NCJT-r16` — 권위 일치 |
| Rel-17 | T:✅ `dl-OrJointTCI-StateList-r17` chunk 직인용<br>G:✅ "DL/UL unified" (§ 없음)<br>C:✅ Joint vs Separate TCI + DCI Format 1_1/1_2 + PDCCH-Order TCI Indication — 권위 일치 (Ofinno) | T:✅ §5.18.23/§6.1.3.47 Unified TCI MAC CE, `simultaneousU-TCI-UpdateList1..4`<br>G:✅ "unified TCI activation MAC CE"<br>C:⚠️ "Unified TCI MAC CE LCID 56" — LCID 번호 검증 필요 | T:✅ `TCI-UL-State`/`TCI-UL-StateId` IE Neo4j 등록<br>G:✅ `dl-OrJointTCI-StateList`, `ul-TCI-StateList`, `unifiedTCI-StateType`<br>C:✅ ASN.1 `TCI-UL-State-r17` + `pathlossReferenceRS-Id` — 권위 일치 | T:⚠️ cap 행 정확 미식별 (한계)<br>G:✅ "joint/separate unified TCI 지원"<br>C:✅ `unifiedTCI-StateMode-r17: {joint, separate, both}`, `beamAppTime-r17` — 권위 일치 (단 `T_BAT` 약어는 Claude 자체) |
| Rel-18 | T:✅ joint/separate 분기 + `tci-SeparateTCI-UpdateMultiActiveTCI-Per…`<br>G:⚠️ "DCI 1_1/1_2/1_3, joint/separate" (DCI 1_3는 권위 미확인)<br>C:✅ Multi-cell TCI + STxMP + LTM 통합 — 권위 일치 | T:✅ §5.18.33 Enhanced Unified TCI + §6.1.3.70/71 (Joint/Separate)<br>G:✅ "enhanced unified TCI, LTM cell switch, candidate cell TCI"<br>C:⚠️ "Multi-cell TCI MAC CE / LTM cell switch MAC CE" (구체 §번호/LCID 없음) | T:✅ `TCI-ActivatedConfig`, `LTM-TCI-Info` IE 등록<br>G:✅ "LTM candidate TCI, Rel.18 unified TCI cap 확장"<br>C:✅ ASN.1 `simultaneousU-TCI-UpdateList1..4-r18` — 권위 일치 | T:⚠️ r18 cap 흔적 (`additionalTime-CB-8TxPUSCH-r18`)만<br>G:✅ "multi-active TCI, CJT, per-CORESETPoolIndex"<br>C:✅ `multiCellPdcch-PdschTciStateUpdate-r18`, `unifiedTCI-MultiCellSet-r18` |
| Rel-19 | T:⚠️ "별도 § 추가 미식별" 한계 명시<br>G:⚠️ "candidate TCI, CLTM 확장" (NR MIMO Phase 5 미언급)<br>C:❌ "AI/ML beam prediction" — 권위 출처(NR MIMO Phase 5, RP-242394, asymmetric DL sTRP/UL mTRP)와 다름 | T:✅ §5.18.36 Candidate Cell TCI / §6.1.3.76 / §6.1.3.77 Cross-RRH TCI MAC CE (Neo4j)<br>G:⚠️ "Enhanced LTM, candidate cell TCI, CLTM 절차"<br>C:❌ "AI/ML 모델 activation MAC CE (working assumption)" — 권위 미확인 | T:✅ `CandidateTCI-State`/`CandidateTCI-UL-State` IE 등록<br>G:⚠️ "CLTM/LTM candidate cell, 조건부 설정"<br>C:❌ ASN.1 `AI-ML-Configuration-r19` 작성 — Rel-19 RP-WID는 RP-234039(AI/ML for Air Interface)와 RP-242394(NR MIMO Ph5) 별개. Claude는 두 WI를 혼동 + AI/ML을 TCI 본류로 단정 | T:⚠️ r19 cap 직접 미식별<br>G:✅ "CLTM, eType-II/CJT cap 확장"<br>C:❌ `ai-ml-BeamPrediction-r19` — 권위 미확인 (모델 추정) |
| Rel-20 | T:⚠️ "spec 본문 변경 미식별, 6G overview discussion만" — 정직<br>G:⚠️ "frozen 아님, draft CR 방향" — 정직 가드<br>C:❌ "Cross-Carrier TCI / Sub-band TCI / NTN TCI" + ASN.1 `TCI-State-r20` draft — Rel-20 spec 진입 전 추측 채움 | T:⚠️ 동일<br>G:⚠️ "conditional LTM, SCell activation, DC/inter-CU 논의"<br>C:❌ "TBD" (정직) | T:⚠️ 동일<br>G:⚠️ "조건부 mobility/LTM 후보 확장"<br>C:❌ ASN.1 draft (`crossCarrierRefRS-r20`, `subbandTCI-Application-r20`, `ntn-DopplerComp-r20`) — 추측 채움 | T:⚠️ 동일<br>G:⚠️ "Rel.20 capability 유동적"<br>C:❌ "TBD" |

**채움 비율 (24칸 기준)**:
- tracer: ✅13 / ⚠️11 / ❌0 → 채움 13칸 (54%) + 한계명시 11칸 (46%) = 24/24 정직 처리
- GPT: ✅16 / ⚠️8 / ❌0 → 채움 16칸 (67%) + 가드 표기 8칸 (33%)
- Claude: ✅14 / ⚠️0 / ❌10 → 채움 14칸 (58%) + 추측 채움 또는 단정 부정확 10칸 (42%)

→ **GPT가 채움 칸 수 1위지만 §번호 없이 IE 나열 수준. Claude는 채움 풍부하나 Rel-19/20 추측 채움 비율 높음. tracer는 채움 칸은 적지만 모두 retrieved-grounded.**

---

## 항목별 차분

| 항목 | tracer | GPT | Claude | 비고 |
|---|---|---|---|---|
| **Rel-17 unified TCI framework** | ✅ §5.18.23/§6.1.3.47 + `dl-OrJointTCI-StateList-r17` 본문 chunk + RAN2 inter-cell BM TDoc(R2-2110534/22)으로 도입 흐름 입증. 3spec 가로지르는 매핑이 retrieval 본문에서 직접 확인됨. | ✅ "DL beam과 UL spatial relation을 unified로 통합" + `dl-OrJointTCI-StateList`, `ul-TCI-StateList`, `unifiedTCI-StateType` IE 명 + joint/separate 모드 정의 — 흐름은 정확하나 §번호/근거 없음. | ✅ Joint vs Separate TCI + Beam Application Time T_BAT + DCI without DL grant + ASN.1 `TCI-UL-State-r17` 본문 + `pathlossReferenceRS-Id` 통합. WID(RP-202147/RP-211583) 인용. **3개 모델 모두 Rel-17 핵심은 정확**. | tracer: retrieved-grounded. GPT: 흐름만. Claude: 디테일 풍부 + WID 인용 + ASN.1 본문 — 다만 chunkId 검증 불가. |
| **Rel-18 inter-cell BM** | ✅ §5.18.33 Enhanced Unified TCI + §6.1.3.70/71 joint/separate + LTM-TCI-Info IE + R1-2309110/2309111 FL summary + R2-2207753 LTM discussion + R1-2300932 unified TCI multi-TRP 확장. | ⚠️ "enhanced unified TCI, LTM, candidate-cell TCI" — 흐름 정확하나 inter-cell BM이 Rel-17/Rel-18에 걸쳐 있다는 권위 사실(Rel-17 ICBM 도입, Rel-18 LTM/multi-TRP 확장)을 흐릿하게 표현. | ✅ Multi-cell TCI (`simultaneousU-TCI-UpdateList1..4-r18`) + STxMP multi-panel + LTM 통합. WID(RP-234037 NR_MIMO_evolution_Ph4) 인용. **inter-cell BM을 multi-cell 확장으로 정리**, LTM은 별도. | tracer가 RAN1/RAN2 TDoc 양면에서 Rel-17 ICBM → Rel-18 multi-TRP 확장의 흐름을 직접 입증. Claude는 multi-cell/multi-panel 시점 정리. GPT는 흐름만. |
| **Rel-19 mTRP/TCI 확장** | ✅ §5.18.36 Candidate Cell TCI + §6.1.3.76/77 Cross-RRH TCI + CandidateTCI-State IE + R1-2402686/2404815/2408118 asymmetric DL sTRP/UL mTRP + R2-2508663 RP-242394 인용 — **권위(NR MIMO Phase 5)와 정확 일치**. | ⚠️ "CLTM/inter-cell BM 확장, eType-II/CJT cap" — Rel-19 도입 항목명 모호. RP-WID 미인용. CLTM/LTM은 권위 출처에서 Rel-18이 LTM, Rel-19에서 LTM 추가 enhancement이지 "CLTM이 Rel-19 신규"라는 단정은 근거 부족. | ❌ "AI/ML for Beam Management" 단정, RP-234039 인용. **권위 출처(NR MIMO Phase 5 / RP-242394)와 다름**. AI/ML은 Rel-19 별개 WI(RP-234039)이지 TCI framework 본류 확장이 아님. ASN.1 `AI-ML-Configuration-r19` 작성 = 추측 채움. | tracer 1위 (NR MIMO Phase 5 정확). Claude는 카테고리 자체를 잘못 분류 (AI/ML vs mTRP/TCI). GPT는 흐릿하지만 mTRP/CLTM은 부분 정확. |
| **Rel-20 spec 본문** | ⚠️ "spec 본문 변경 미식별, 6G overview discussion만 회수" — 정직한 미답. R1-2505125/2506063/2506358 (Nokia/Samsung 6G overview) + R2-2508085/2508849 6G mobility로 retrieval 자체는 풍부하나 spec 본문 변경 단언 안 함. | ⚠️ "frozen 아님, draft CR 방향. Mobility enhancement Phase 4, conditional LTM, SCell activation, DC/inter-CU LTM, RACH-based conditional LTM 후처리" — 정직 가드 + LTM 계열 확장 방향 나열. 단 Rel-20은 6G IMT-2030 단계로 LTM이 본류인지 단언 어려움. | ❌ "Cross-Carrier TCI / Sub-band TCI / AI/ML mature / NTN TCI" + ASN.1 `TCI-State-r20` (`crossCarrierRefRS-r20`, `subbandTCI-Application-r20`, `ntn-DopplerComp-r20`) draft 코드블럭 작성. **Rel-20 spec 미확정 영역에 ASN.1 본문 추측 작성** — Hallucination 명백. (단 §7 끝에 "Spec 미확정 영역" 가드 1줄 있음.) | tracer 정직, GPT 가드, Claude 추측 채움. Rel-20에서 가장 차이가 두드러짐. |
| **문서 간 연결고리** | ✅ 5개 연결: ① RRC→PHY (38.214 §5.1.5가 RRC IE 직인용) ② MAC→PHY (§6.1.3.70 cross-ref) ③ 3-spec 가로지름 (Rel-17 unified) ④ UE cap 호출 ⑤ TDoc→spec — **모두 retrieved 본문에서 직접 입증**. | ✅ 단순 다이어그램 1개 (`RRC → MAC CE → DCI → PHY → Capability`) + Rel별 mermaid-style flow 6개 — 흐름은 정확하나 cross-reference 본문 없음. | ✅ 매우 풍부: §8.1 Release×문서 진화 매트릭스 + §8.2 Rel-17 cross-document flow (WID → 3spec → cap → 38.133 RRM Test) + §8.3 정합성 checkpoint 4개 (TCI ID 공간, 활성 TCI 개수, DCI codepoint, QCL Type D rule) + §8.4 Beam switching latency 진화 — **3개 중 가장 풍부**. 다만 38.133 RRM Test 인용은 권위 출처에서 "Rel-17 T_BAT test" 항목 직접 검증 불가. | tracer는 retrieved-grounded, GPT는 단순, Claude는 풍부하지만 일부 미검증. |

---

## 강점 / 약점 (모델별)

### 3gpp-tracer

**강점**:
- Citation Integrity 5.0/5.0 — chunkId 12/12 + TDoc 31/31 모두 retrieval log에서 검증 가능 (`logs/cross-phase/usecase/q2_retrieval_log.json`).
- Rel-17/18 핵심 본문(`dl-OrJointTCI-StateList-r17`, §5.18.23, §5.18.33, §6.1.3.70/71)을 spec 직인용 + RAN1/RAN2 TDoc 도입 배경(R1-2300932, R1-2309110/11, R2-2110534/22, R2-2207753)을 양면에서 입증.
- Rel-19 mTRP/TCI 확장을 권위(NR MIMO Phase 5, RP-242394)와 정확히 일치시킴 (Candidate Cell TCI + Cross-RRH TCI MAC CE).
- Rel-19/20 영역 추측 채움 거의 없음 — "데이터셋 한계로 미식별"로 정직 표기.
- Cross-doc linkage 5개 모두 retrieved 본문의 직접 cross-reference로 입증.

**약점**:
- 38.331 ASN.1 IE 본문(`TCI-State`, `tci-StatesToAddModList`, `qcl-Type1/2` 필드)이 `ran2_ts_sections` 청크에 없음 — Neo4j Section 노드 등록 정보로만 입증.
- 38.306 capability 테이블이 행 단위 청킹 안 됨 — 정확 cap 항목 행을 못 짚음 (`maxNumberConfiguredTCIstatesPerCC`/`maxNumberActiveTCI-PerBWP` 행).
- Hallucination 1건 (§6.1.3.14 "Rel-15부터 운영" — chunk 본문에 release 표기 없음).
- chunk payload에 `specVersion` 메타데이터 부재 → release attribution 직인용 근거 약함.
- RP-WID(RP-211583/RP-234037 등)가 별도 컬렉션으로 적재 안 됨 — TDoc discussion이 RP 번호를 인용하는 우회 입증.

### GPT

**강점**:
- 24칸 매트릭스 전체 채움 (가장 깔끔한 single-table 요약).
- TCI 본질 설명 (§1, QCL Type A~D 표) + RRC/MAC/DCI/PHY 흐름 다이어그램이 직관적.
- Rel-20을 "frozen 아님, draft CR 방향"으로 가드 — 추측 단정 회피.
- Release별 흐름이 일관된 pattern으로 정리 ("Rel.X RRC: ... ↓ MAC CE: ... ↓ PHY: ... ↓ cap: ...").
- 5G Americas / Qualcomm 끝 참고문헌 명시 — 외부 출처 인정.

**약점**:
- §번호/chunkId/URL 전혀 없음 — 검증 가능성 최저 (citation integrity 1.5/5).
- IE 명 (`tci-StatesToAddModList`)만 등장하고 정의 본문 없음 — 사실 검증을 독자가 spec을 별도로 열어야 함.
- Rel-19 = "CLTM/inter-cell BM 확장"으로 단정 — 권위 출처(NR MIMO Phase 5/RP-242394)와 일부 어긋남. CLTM(Conditional LTM)은 Rel-19 enhancement지만 본류는 mTRP/asymmetric DL sTRP/UL mTRP.
- Rel-16에 "simultaneous TCI update list" 언급 — 이는 Rel-18 multi-cell TCI 항목으로 권위 본문에 있음. Release 매핑 오류.
- RP-WID 번호 없음.
- ASN.1 본문/MAC CE 포맷/LCID 번호 등 디테일 없음.

### Claude

**강점**:
- 24칸 매트릭스 + Rel-17 cross-document flow + §8.3 정합성 checkpoint 4개 + §8.4 latency 진화 — 3개 중 가장 풍부한 cross-doc 매핑.
- ASN.1 본문 (TCI-State, QCL-Info, TCI-UL-State-r17, RepetitionSchemeConfig-r16, PDSCH-Config simultaneousU-TCI-UpdateList1..4-r18) 직접 작성 — Rel-15~18 본문 구조는 권위 출처와 일치.
- WID 번호 (RP-170739, RP-181433, RP-193133, RP-211583, RP-234037, RP-234039) 인용 — Rel-15/16/17/18/19의 WID 참조.
- TCI 개념(§1) + Beam Application Time T_BAT + Joint/Separate vs DL-only/UL-only TCI 분류표 — 디테일 풍부.
- 38.133 RRM Test 인용 — RAN4 영역까지 cross-doc 매핑 시도.

**약점**:
- Rel-19를 "AI/ML for Beam Management"로 단정 — 권위 출처(NR MIMO Phase 5/RP-242394)와 본류 다름. AI/ML(RP-234039)은 별개 WI.
- Rel-20 "Cross-Carrier TCI / Sub-band TCI / NTN TCI" + ASN.1 `TCI-State-r20` draft — Rel-20 spec 미확정 영역 추측 채움 (§7 끝 1줄 가드는 있음).
- LCID 번호(53/52/47/49/56) — sharetechnote 수준 추정값, 권위 ETSI 본문 직인용 부재.
- chunkId/URL 없음 — citation integrity tracer보다 낮음.
- "Rel.16 enhanced TCI activation MAC CE LCID 49" 같은 LCID 번호와 "T_BAT 1, 3, 7 slots" 같은 구체 수치가 권위 본문 직인용 없이 등장 — 미검증 디테일.
- AI/ML beam prediction을 Rel-19 TCI framework 본류로 끌어올린 점이 가장 심각한 카테고리 오분류.

---

## Hallucination 검출 (외부 LLM, 특히 Rel-19/20)

| 모델 | 의심 사실 | 권위 검증 | verdict |
|---|---|---|---|
| tracer | "§6.1.3.14는 Rel-15 시점부터 운영된 PDSCH TCI activation MAC CE" | §6.1.3.14가 Rel-15 NR 본문에 포함된 사실은 권위 ETSI V15.x.0 확인됨 (sharetechnote/Itecspec). 다만 chunk 본문에 "Rel-15" 표기 직인용은 없음. | 약한 hallucination 1건 (release attribution 추론) — 사실 자체는 정확. |
| GPT | "Rel.16 simultaneous TCI update list, serving-cell 공통/그룹 activation" | Rel-16에서는 단일 PDCCH mTRP의 enhanced PDSCH TCI activation이 도입되었고, simultaneous TCI update list (`simultaneousU-TCI-UpdateList1..4`)는 권위 출처에서 Rel-18 multi-cell TCI 항목. | 중간 hallucination 1건 (Rel 매핑 오류) — Rel-16 ↔ Rel-18 혼동. |
| GPT | "Rel.18 DCI 1_1/1_2/1_3" | DCI Format 1_3는 Rel-18 본문에 등장하지 않음. unified TCI는 1_1/1_2 + DCI without DL grant. | 약한 hallucination — DCI 1_3 미검증. |
| GPT | "Rel.19 = CLTM/inter-cell beam management 확장" 단정 | Rel-19 NR MIMO Phase 5(RP-242394)는 asymmetric DL sTRP/UL mTRP가 본류, Candidate Cell TCI + Cross-RRH TCI 도입. CLTM은 Rel-19 enhancement지만 본류 분류는 부정확. | 약한 hallucination — 카테고리 오분류 부분. |
| Claude | "Rel.19 = AI/ML for Beam Management" 단정 + ASN.1 `AI-ML-Configuration-r19` | RP-234039 (AI/ML for NR Air Interface)는 Rel-19 별개 SI/WI로 존재 (권위 확인). 단 TCI framework 본류 확장은 NR MIMO Phase 5(RP-242394)이지 AI/ML이 아님. ASN.1 본문은 모델 추정. | **명확한 hallucination** — Rel-19 TCI framework 카테고리 오분류 + ASN.1 본문 추측. |
| Claude | "Rel.19 ai-ml-BeamPrediction-r19, ai-ml-Spatial-r19, ai-ml-Temporal-r19, maxNumber-ai-ml-Models-r19" capability | 권위 38.306 V19.x.0에서 직접 확인 불가 (Rel-19 freeze 단계 미완료). | 명확한 hallucination — capability 항목명 추측. |
| Claude | "Rel.20 Cross-Carrier TCI, Sub-band Specific TCI, NTN 환경 TCI + ASN.1 `TCI-State-r20`(`crossCarrierRefRS-r20`, `subbandTCI-Application-r20`, `ntn-DopplerComp-r20`)" | 3GPP Rel-20은 6G IMT-2030 단계 진입, Stage-2 freeze 2026-09 / Stage-3 freeze 2027-03 (권위 timeline). spec 본문 추가 단계 진입 전. | **명확한 hallucination** — Rel-20 spec 미확정 영역 ASN.1 추측 채움 (§7 끝 1줄 가드 있음). |
| Claude | "LCID 53/52/47/49/56" (Rel-15/16/17 MAC CE LCID 번호) | 권위 ETSI V18.x.0 §Table 6.2.1-1에서 직접 검증 필요 — sharetechnote 수준 추정값과 일치하나 직인용 부재. | 약한 hallucination — LCID 번호 권위 직인용 없이 단정. |
| Claude | "T_BAT 1, 3, 7 slots" + "Beam switching latency Rel-15 ~10 ms → Rel-17 ~3 ms → Rel-18 <100 ms (cell change)" | Beam Application Time(`beamAppTime-r17`)은 권위 38.306 일치, 다만 1/3/7 slots와 latency 수치는 일반 통용 자료(Qualcomm 자료 등) 수준. ETSI 본문 직인용 부재. | 약한 hallucination — 수치 직인용 없음. |

**Rel-19/20 hallucination 비교**:
- tracer: 0건 (모두 "데이터셋 한계로 미식별")
- GPT: 약한 1건 (Rel-19 카테고리 오분류 부분)
- Claude: 명확한 3건 + 약한 2건 — 가장 많음.

---

## 3gpp-tracer 개선 시사점

`docs/usecase/evaluations/tracer/q2_quality_eval.md`의 D/O/R 분류와 연계:

### P1 (즉시 개선 — R+O 영역)

1. **38.331 ASN.1 IE 본문 청킹** (R+O)
   - 현재 RAN2 KG에 IE Section 노드(`TCI-State`, `TCI-UL-State`, `LTM-TCI-Info`, `CandidateTCI-State` 등)는 등록되어 있으나, ASN.1 본문이 `ran2_ts_sections` Qdrant chunk로 회수되지 않음.
   - **개선**: Phase-7 RAN2 청킹 정책에 ASN.1 의미 단위 분리(예: `tci-StatesToAddModList`, `qcl-Type1`, `qcl-Type2`, `referenceSignal` 필드별 chunk) 추가.
   - **임팩트**: Q2의 24칸 매트릭스 38.331 셀이 모두 `⚠️` → `✅`로 격상. Rel-15 baseline ASN.1 본문 직인용 가능 → Claude의 ASN.1 강점을 retrieved-grounded로 흡수.

2. **38.306 capability 테이블 행 단위 청킹** (R+O)
   - 현재 회수된 청크는 테이블 헤더(`Definitions for parameters | Per | M | …`)만. `maxNumberConfiguredTCIstatesPerCC`/`maxNumberActiveTCI-PerBWP`/`unifiedTCI-StateMode-r17` 등 정확 cap 항목 행 chunk 없음.
   - **개선**: Phase-7 38.306 테이블 파싱에 "테이블 행 단위 chunk split" 정책 추가, KG에 `Capability`/`FeatureGroup` 라벨 추가.
   - **임팩트**: Rel-15~Rel-18 cap 4칸이 `⚠️` → `✅`로 격상.

3. **chunk payload `specVersion` 메타 추가** (R+O)
   - Qdrant payload에 `specVersion` 필드 부재 → "Rel-15부터 운영" 같은 release attribution이 chunk 본문 직인용 근거 없음 (현재 1건 hallucination 원인).
   - **개선**: Phase-7 청킹 시 spec 파일명에서 version 추출(`38.214-f10` → `V15.1.0` → `Rel-15`), payload 필드 보강. KG에 `Spec ↔ SpecVersion ↔ Release` edge 모델링.
   - **임팩트**: tracer의 1건 hallucination 해소 + release-by-release 답변 정밀도 향상.

### P2 (RP-WID 컬렉션 신설 — R 영역)

4. **`ran{1,2}_rp_tdocs` 컬렉션 신설** (R)
   - 현재 `ran{1,2}_tdoc_chunks`는 회의 단위 TDoc 위주. RP-WID(RP-170739, RP-181433, RP-193133, RP-211583, RP-234037, RP-234039, RP-242394)가 별도 컬렉션으로 적재 안 됨.
   - 1차 답변에서 R2-2508663이 RP-242394를 직인용한 것은 우회 입증.
   - **개선**: RAN Plenary RP-* TDoc을 별도 컬렉션 또는 KG `WorkItem` 노드로 적재. payload에 WID title, rapporteur, target release 메타데이터.
   - **임팩트**: "Rel-X WID 도입 배경" 질문에서 RP-WID 직접 인용 → Claude의 WID 인용 강점을 retrieved-grounded로 흡수.

### P3 (38.214 §5.1.5 sub-chunking — R 영역)

5. **§5.1.5 release tag 단위 sub-chunk 분리** (R)
   - 38.214 §5.1.5는 단일 거대 chunk(`-001` ~ `-007`) 7개로만 분리 — release별 분리 어려움.
   - **개선**: chunk 본문 내 `-r17`/`-r18`/`-r19` tag 단위 또는 paragraph 단위 sub-chunking + release-aware metadata 추가.
   - **임팩트**: Rel-17/18/19 38.214 셀이 retrieve 단계에서 "어느 release의 본문 chunk인지" 명시적 분류 가능.

### P4 (Rel-20 데이터 — D 영역, 시간 해결)

6. **Rel-20 spec 본문 적재 시점**
   - Rel-20은 6G IMT-2030 단계 진입 (Stage-2 freeze 2026-09, Stage-3 freeze 2027-03 — 3gpp.org 권위 timeline).
   - **개선**: 자동 적재 파이프라인이 spec freeze 시점(2026-09 ~ 2027-03 ~)에 Rel-20 본문 chunk 자동 추가.
   - **임팩트**: 현재는 정직한 미답으로 시스템 무결성 유지 — 시간 경과로 자연 해결.

### Rel-19/20 ASN.1 chunking 우선순위

Q2의 핵심 차이가 Rel-19/20에서 발생하므로, P1-1 (38.331 IE chunking) + P3 (38.214 sub-chunking)가 Q2 직접 개선에 가장 임팩트 큼. P2 (RP-WID 컬렉션)는 "WID 도입 배경" 차원에서 Q2뿐 아니라 모든 release-comparative 질문에 효과.

---

## 실무 활용 결론

| 사용 목적 | 권장 모델 | 이유 |
|---|---|---|
| **Spec 직인용이 필요한 작업** (논문/특허/기고) | tracer | chunkId + retrieval log로 모든 사실 검증 가능. citation integrity 5.0. Rel-15~18 핵심 본문 (§5.18.23, §6.1.3.70/71, `dl-OrJointTCI-StateList-r17`) 권위 일치. |
| **빠른 흐름 파악 / 초보 학습용** | GPT | 24칸 매트릭스 single-table + RRC→MAC→DCI→PHY→Cap 흐름 다이어그램이 가장 직관적. Rel-20 "frozen 아님" 가드도 안전. 단 §번호 검증은 별도 필요. |
| **풍부한 cross-doc 매핑 / 정합성 checkpoint** | Claude | §8.3 정합성 checkpoint (TCI ID 공간, 활성 TCI 개수, DCI codepoint, QCL Type D rule) + §8.4 latency 진화 + ASN.1 본문 + WID 인용 — 가장 풍부. **단 Rel-19 (AI/ML 단정), Rel-20 (ASN.1 추측), LCID 번호 등은 권위 검증 필수**. |
| **Rel-19/20 작업** (NR MIMO Phase 5, 6G IMT-2030) | tracer (정직한 미답) > GPT (가드) >> Claude (추측 채움) | Claude의 Rel-19 AI/ML 단정 + Rel-20 ASN.1 draft는 spec 진입 전 hallucination. tracer의 "데이터셋 한계로 미식별" 표기가 가장 안전. |
| **종합 1차 답변 (혼합)** | tracer 본문 + Claude의 cross-doc checkpoint 표 + GPT의 single-table 매트릭스 | tracer를 fact base로, Claude/GPT는 organize-only로 활용. Claude의 Rel-19/20 항목과 LCID 번호는 모두 권위 검증 후 사용. |

**핵심 결론**: Q2에서 tracer는 citation integrity (1위) + Rel-17/18 권위 일치 (1위) + Rel-19 NR MIMO Phase 5 정확 매핑 (1위) + Rel-20 정직한 미답 (1위)으로 4축에서 1위. 24칸 채움 비율은 GPT/Claude가 더 많지만 Claude의 Rel-19/20 hallucination 5건이 평가 분모를 깎음. tracer의 P1 개선(38.331 IE chunking + 38.306 cap 행 chunking + specVersion payload)이 적용되면 24칸 모두 retrieved-grounded ✅ 가능.
