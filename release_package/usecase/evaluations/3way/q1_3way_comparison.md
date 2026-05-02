# Q1 3-way 비교 — Rel-16 enhanced Type-II codebook

> 평가일: 2026-04-29
> 평가자: Claude (Opus 4.7, 1M context)
> 권위 검증 베이스: `docs/usecase/evaluations/tracer/q1_quality_eval.md` (web 외부 출처 18 fact-claim 1:1 대조 완료)
> 추가 검증: GPT/Claude 답변의 학습지식 기반 claim에 대해 권위 출처(sharetechnote, ATIS V16.2.0, 3GPP 38.521-4 cover, IEEE/ResearchGate Rel-16 Type II 논문) 대조

---

## 메타

| 모델 | 파일 | 라인 | 인용 형식 | 외부 도구 |
|---|---|---:|---|---|
| 3gpp-tracer | `answers/tracer/q1_rel16_typeii_codebook.md` | 279 | `[spec §sec, chunkId=...]` + `[Rxxx, RAN1#N, ai=..., type=..., release=...]` (chunkId 검증 가능, retrieval log 280 hits 100% 정합) | RAG only (Qdrant + Neo4j, 외부 web 미사용) |
| GPT | `answers/gpt/q1_rel16_typeii_codebook.md` | 249 | spec section 번호 없음, "참고 출처"로 spec 번호와 5G Americas 보고서 1건만 나열 | 학습지식 + 일반 reference (검증 불가) |
| Claude | `answers/claude/q1_rel16_typeii_codebook.md` | 404 | spec clause 번호 (예: 38.214 §5.2.2.2.5), RP-191085/RP-182863 WID 번호 명기, ASN.1 syntax 직접 인용 | 학습지식 (web 미접속, "참조: ... v16.x" 메타로 release만 명시) |

---

## 5축 점수 비교 (각 0~5)

| 축 | tracer | GPT | Claude | 1위 | 코멘트 |
|---|---:|---:|---:|---|---|
| A1 Accuracy | **4.6** | 3.5 | 4.2 | tracer | tracer는 권위 cross-check 17/18 ✅. Claude는 spec 절 번호·ASN.1·paramCombination 표 정확하나 RP-182863 WID 번호 학습지식 (RP-181453이 정설, RP-182863은 RAN1 WID 별도 추적 번호) + "throughput 30%+" 같은 정량 수치는 검증 불가. GPT는 절 번호조차 없어 정확성 측정 자체가 어려우나 high-level 서술은 큰 오류 없음. |
| A2 Coverage | **3.8** | 4.0 | **4.7** | Claude | Claude가 7개 항목 모두 풍부 (특히 38.331 ASN.1 IE 본문, 38.306 capability 행, 38.214 W₁·W̃₂·Wf 수식, paramCombination-r16 8행 표 직접 기술). tracer는 38.331/38.306 미회수로 한계 명시. GPT는 모든 항목 다루나 깊이가 high-level 추상에 머무름. |
| A3 Citation Integrity | **5.0** | 1.0 | 2.5 | tracer | tracer는 27 chunkId + 10 TDoc 100% retrieval log 존재 검증 완료 (Python set diff 0건). Claude는 spec section 번호 정확하나 검증 가능한 chunk-level 출처 없음, 학습지식과 spec 본문이 섞여 분리 불가. GPT는 spec section 번호조차 없어 검증 자체 불가. |
| A4 Hallucination Control | **4.8** | 3.0 | 3.5 | tracer | tracer는 38.331/38.306 본문 미발견을 §10에 정직 명시, RP-182067도 retrieved chunk 본문 안에 등장하는 것만 인용. Claude는 RP-191085(RAN1 MIMO Enhancement WID revision)·"throughput 30% 이상" 같은 수치를 학습지식으로 단언 — 사실 가능성은 있으나 검증 trace가 없음. GPT는 "Rel.15 → Rel.16" 흐름 서술이 일반론으로 hallucination이라 보긴 어렵지만 fact-grounding이 0. |
| A5 Cross-Doc Linkage | **4.5** | 3.8 | **4.6** | Claude (근소) | Claude는 §8.2 Cross-Reference 매트릭스에서 5개 spec × 6개 컨셉 매트릭스를 명시 + §8.3 Configuration→Behavior 6단계 구체 예시. tracer는 retrieved 본문 인용으로 4개 실선 + 2개 점선 (38.331/38.306 미커버 정직 표기). GPT는 흐름도 1개 (8단계)로 high-level. tracer의 38.212↔38.214 §5.2.3 priority function 직접 인용은 retrieval 우위. |
| **종합** | **4.5** | 3.1 | 3.9 | — | tracer = 사실 정확성+citation 모범, Claude = coverage+depth, GPT = 흐름 가독성. |

---

## 항목별 차분 (질문 7개 항목 + 연결고리)

| 항목 | tracer | GPT | Claude | 비고 |
|---|---|---|---|---|
| **WID 도입배경** | RAN1 discussion chunk 7건 (R1-1903044/1909583/1909918/2202121/2112195/1812322/1902123) retrieved-grounded 인용. 정식 WID(RP-182067)는 chunk 본문에서만 등장. **release=Rel-16 + DFT-FD compression 합의 흐름** 추적. | "Rel.15 한계 → Rel.16 enhancement" high-level 서술. WID 번호 없음. "5G Americas Rel-16 overview" reference. | RP-182863 / RP-191085 WID 번호 명기 + 핵심 objective 직접 quote. **W = W₁·W̃₂·Wf^H 3-stage 압축 수식 + bitmap-based non-zero coefficient indication** 직접 기술. | Claude가 가장 풍부하나 RP 번호·"50%+ overhead reduction"은 학습지식. tracer는 retrieved-grounded만 인용해 깊이는 부족하지만 검증 가능. |
| **38.211 CSI-RS** | §7.4.1.5.1 / §8.4.1.5.3 chunk 회수. Type II 전용 매핑은 38.214 §5.2.2.2.5 본문에서 우회 인용 (PCSI-RS=2·N1·N2). **한계 명시**. | nrofPorts/cdm-Type/density/freqBand 6개 IE field 표로 정리 (high-level). RE 매핑 수식 없음. | §7.4.1.5 RE 매핑 + c_init PN sequence 수식 직접 + CDM type {cdm8-FD2-TD4, fd-CDM2, cdm4-FD2-TD2}. **rank ≤ 4 제약** 명기. | Claude가 c_init 수식·CDM type 구체값까지 (학습지식). tracer 우회 인용은 정확하나 38.211 측 근거는 약함. GPT는 IE field 나열만. |
| **38.212 UCI** | §6.3.2.1.2 chunk-014 + §6.3.1.1.3 chunk-001 + §6.3.2.6 chunk-001. **Part 2 group 0/1/2 + X1/X2 매핑** 본문 직접. 우선순위 함수는 38.214 §5.2.3에 위임됨을 retrieved 인용. | Part 1 = "RI/CQI/non-zero coefficient 수", Part 2 = "PMI/LI/coefficient" 표 (high-level). priority omission 언급 없음. | Part 1 field 길이 공식 (⌈log₂(K0+1)⌉ bits × R), Part 2 layout 7항목 (W₁/Wf/bitmap/SCI/amplitude/phase/CQI), priority 공식 Pri(l,m) = 2L·R·π(m) + R·l + r. | Claude가 가장 깊이 있으나 priority 공식은 spec 검증 필요 (38.212 §6.3.2.1.2의 정확한 formulation). tracer가 "group 0/1/2 + X1/X2"로 retrieval 본문에 충실. |
| **38.214 codebook** | §5.2.2.2.5 chunk-001 본문 직접. typeII-r16, paramCombination-r16, n1-n2-codebookSubsetRestriction-r16, antenna ports {3000..3031}, 4/8/12/16/24/32 ports, 사용 제약(3..8) 모두 retrieved-grounded. 인접 절 6개 (§5.2.2.2.3/.4/.5a/.7/.10/.11/.11a) 정리. | 동작 6단계 + 6개 컨셉 표. paramCombination 표 없음. 수식 없음. | W^(l) = (1/√(N₁N₂γ^(l)))·ΣΣ v·w̃·y_f^H 수식 + L/p_v/β 표 + paramCombination-r16 1~8 8행 표 (L, p_v, β 값) + Mv = ⌈p_v·N3⌉ + amplitude/phase quantization (4-bit ref / 3-bit diff / 16-PSK / 8-PSK) + SCI 정의. | tracer는 retrieved-grounded 5/5, Claude는 수식·표·quantization까지. paramCombination 8행 표는 **권위소스(ATIS V16.2.0 Table 5.2.2.2.5-1)와 1:1 대조 시 일치**. Claude가 본 항목에서 가장 풍부. |
| **38.306 capability** | §4.2.7.10 Phy-Parameters chunk 회수, **csi-Type-II 항목명 chunk-001 본문에 미발견** (한계 §6 명시). | enhanced Type-II rank/port-selection/FD compression 등 5개 capability 범주 high-level 표. 정확한 IE 이름 없음. | csi-ReportFramework-r16 / typeII-r16 / typeII-PortSelection-r16 / paramCombination-r16(per-band) / simultaneousCSI-ReportsPerCC-r16 / csi-ReportFrequencyGranularity-r16 IE 직접 명기. CPU 점유 = ∞ (단독 처리) 명기. | Claude가 IE 이름·CPU 정책까지 (학습지식). tracer 미회수 → Claude로 보강 필요 영역. GPT는 high-level 만. |
| **38.331 RRC** | CodebookConfig IE 본문 미회수 (한계 §7 명시). 38.214 본문에서 RRC 파라미터명 우회 인용만. | CSI-ReportConfig / CodebookConfig-r16 / CSI-ResourceConfig / NZP-CSI-RS-Resource 6개 IE 표. ASN.1 본문 없음. | **CodebookConfig ASN.1 SEQUENCE 본문 직접** (type2-r16, subType, paramCombination-r16) + TypeII-r16 SEQUENCE (n1-n2-codebookSubsetRestriction-r16 BIT STRING per (N1,N2), typeII-RI-Restriction-r16 BIT STRING(SIZE(4)), numberOfPMI-SubbandsPerCQI-Subband-r16). pmi-FormatIndicator=subbandPMI 강제. | **Claude 압도적 우위**. tracer 시스템 한계가 가장 두드러진 항목. ASN.1 syntax 정확성은 38.331 v16.x와 cross-check 필요하나 sharetechnote 정리와 일치. |
| **38.521-4 성능** | §6.3.2.2.6 (TDD FR1 16Tx) + §6.3.2.1.6 (FDD FR1 16Tx) + §6.3.3.1.6 (4Rx FDD FR1 16Tx) chunk 직접. 시험 파라미터 (BW=40MHz, SCS=30kHz, (N1,N2)=(4,2), CDM4) retrieved. **TS 38.101-4 §6.3.2.2.6 normative ref 본문 인용**. | "CSI reporting accuracy / multiple PMI / FR1-FR2 / 2Rx-4Rx" 5개 카테고리 high-level. 절 번호 없음. | 38.512-4 vs 38.521-4 구분 명기 (38.512 = RRM, 38.101-4 = demod). closed-loop throughput-based test, PMI random vs PMI follow, **throughput 30%+ gain** 단언. test condition 표 (TDLA/TDLB/CDL-A/CDL-C, MCS index 13 등). 38.133 §9.5 RRM (Z₁/Z₁' delay) 추가. | tracer가 정확한 절 번호 + 시험 파라미터, Claude가 test 메커니즘과 metric을 학습지식으로 보강. **"30%+ gain" 같은 정량 수치는 권위소스 미확인** (Claude의 hallucination 위험 영역). |
| **연결고리** | retrieved 본문 인용 5건 + 점선 2건 (38.331/38.306). **38.212→38.214 §5.2.3 priority function**, **38.521-4→38.101-4 normative ref**, **RAN1 WI agreement→typeII-r16** 모두 본문 직접. | 8단계 흐름도 (RP→38.331→38.211→38.214→38.212→38.306→38.521-4). 컨셉 정확. | §8.2 5×6 cross-reference 매트릭스 + §8.3 Configuration→Behavior 6단계 구체 예시 (16-port paramCombination=6 설정 시 chain) + §8.4 정합성 포인트 3건. | Claude의 매트릭스+예시가 가장 구조적. tracer는 retrieved 검증 가능성 우위. GPT는 high-level. |

---

## 강점 / 약점 (모델별)

### 3gpp-tracer

**강점**:
- **Citation 100% 검증 가능**: 27 chunkId + 10 TDoc → retrieval log 280 hits 1:1 매칭 (Python set diff 0건). 답변의 모든 사실 문장에 chunk-level 인용 부착.
- **Hallucination 0**: 학습지식으로 사실 채워넣지 않음. 38.331/38.306/38.101-4/정식 WID chunk 미회수를 §10에 정직 명시.
- **사용자 오타 자체 치환 안 함**: "38.512-4"를 38.521-4로 자동 치환하지 않고 양쪽 검색 → 0 hits 사실 보고 후 38.521-4 사용. RAG 모범 패턴.
- **권위 cross-check 17/18 ✅**: sharetechnote, ATIS V16.2.0, IEEE/ResearchGate, 3GPP 38.521-4 cover와 1:1 일치.
- **WID 도입 배경 retrieved 흐름**: RAN1#95~#108 discussion chunk를 시간순으로 추적 가능 (R1-1812322 → R1-1909583 → R1-2202121).

**약점**:
- **38.331 ASN.1 IE 본문 미회수**: CodebookConfig / TypeII-r16 IE 정의가 chunk-001 외부에 위치하거나 ASN.1 syntax 매칭 약함.
- **38.306 capability 행 미회수**: 표 형식 chunk가 절 단위로 잘려 있어 csi-Type-II 항목명 직접 인용 불가.
- **38.211 Type II 전용 매핑 약함**: 일반 CSI-RS chunk만 회수, Type II 전용 PCSI-RS=2·N1·N2 식은 38.214에서 우회.
- **38.101-4 미적재**: 38.521-4 normative ref이지만 별도 chunk 없음.
- **정식 type=WID chunk 미적재**: discussion으로 우회.

### GPT

**강점**:
- **흐름 가독성**: 8단계 ASCII 흐름도 + 4단계 RRC 영역 표가 high-level 그림 제공. 학습 자료로 적합.
- **사용자 오타 처리**: 38.512-4 → 38.521-4 명기 (단 자체 판단 치환).
- **균형 잡힌 항목 분배**: 7개 항목 모두 비슷한 길이 (편향 없음).

**약점**:
- **Citation 0**: spec section 번호도 없음. "참고 출처"는 spec 번호 5건과 5G Americas 보고서 1건만. 검증 자체 불가.
- **Depth 부족**: 모든 항목이 high-level IE 표 + 흐름도로 끝남. paramCombination 표 없음, 수식 없음, ASN.1 없음.
- **Fact-grounding 0**: 학습지식과 일반 컨텍스트가 섞여 어느 사실이 spec 본문 출처인지 추적 불가.
- **WID 번호 없음**: RP-* 번호 미명기 (반대로 hallucination 위험은 낮으나 정보 가치도 낮음).

### Claude

**강점**:
- **Coverage 최강**: 7개 항목 모두 깊이 있게 (특히 38.214 수식 W^(l), paramCombination 1~8 8행 표, 38.331 CodebookConfig ASN.1 SEQUENCE, 38.212 priority 공식, 38.306 IE 이름·CPU 정책).
- **Cross-doc 매트릭스**: §8.2 5×6 cross-reference + §8.3 Configuration→Behavior 6단계 예시. 구조적 깊이.
- **수식·ASN.1·표 직접 기술**: c_init PN seq, W^(l) precoder, Mv = ⌈p_v·N3⌉, amplitude quantization (4-bit ref, 16-PSK), bit string size 등. **권위 cross-check 시 paramCombination 표는 ATIS V16.2.0 Table 5.2.2.2.5-1과 일치**.
- **38.512 vs 38.521 vs 38.101-4 구분 명기**: "38.512는 RRM, 38.521-4는 conformance, 38.101-4는 demod requirement"라고 표준 구조 명시.

**약점**:
- **Citation 검증 불가**: spec section 번호는 있으나 chunk-level 출처 없음. "TS 38.211 v16.x 참조" 메타만.
- **학습지식과 spec 본문 분리 불가**: ASN.1 본문이 실제 38.331 v16.x와 정확히 일치하는지, 아니면 학습지식의 합리적 재구성인지 답변 자체로는 판별 불가.
- **검증 안 된 정량 수치**: "throughput 30% 이상", "PMI payload 50%+ 절감", "MCS index 13" 등 학습지식 추정. 일부는 권위소스에서 확인되나 (50% reduction은 IEEE 논문에 등장), spec 본문 자체에는 없음.
- **WID 번호 RP-182863 / RP-191085**: RAN1 trail 번호 가능성. 정설 WID는 RP-181453 (NR_MIMO_enh) — Claude가 reviser 번호를 인용한 것은 부분 정확이나 출처 불명.

---

## Hallucination 검출 (외부 LLM = GPT, Claude)

| 모델 | 의심 사실 | 권위 검증 | verdict |
|---|---|---|---|
| Claude | "RP-182863 → RP-191085 (Rel-16 NR MIMO Enhancement WID)" | 3GPP Rel-16 portal에 NR_MIMO_enh WID 존재. RP-182863은 RAN1 trail (specifically RAN1 contribution이 아니라 RAN plenary 문서). RP-191085는 revision일 수 있으나 web 직접 검색 시 매칭 안 됨. | △ 부분 검증. RP-181453(정설 WID 번호) 미언급 — 출처 학습지식. |
| Claude | "Specify enhancement on CSI reporting for MU-MIMO with focus on overhead reduction, including DFT-based compression in frequency domain." (직접 quote) | tracer 답변에서 retrieved chunk(R1-1909583/1909918) 본문에 동일 표현 존재. WID 본문 quote인지 discussion paraphrase인지 출처 불명. | △ 가능성 있음 — DFT-based FD compression objective는 권위소스 일치. quote의 WID 본문 정확성은 검증 어려움. |
| Claude | "PMI payload 50% 이상 감소 / throughput 30% 이상 향상" | IEEE/ResearchGate "Overhead Reduction of NR Type II CSI for Rel-16" 논문에서 50% overhead reduction 언급 확인. throughput 30% 정량 수치는 spec 본문에 없음 (spec은 단지 conformance test 시험 조건만 정의). | △ 50%는 ✅ 일치, 30% throughput은 학습지식 추정 (논문 시뮬결과 가능성). spec 자체에 30% 수치 없음. |
| Claude | "rank ≤ 4 제약" | sharetechnote / ATIS V16.2.0: Rel-16 typeII-r16은 R_max=4(rank 1~4) — typeII-RI-Restriction-r16 BIT STRING(SIZE(4))로 확인. | ✅ 일치. |
| Claude | "Reference amplitude 4 bits, Differential 3 bits, 16-PSK / 8-PSK phase" | sharetechnote에 4-bit ref / 3-bit diff / 16-PSK/8-PSK quantization 정확히 명시. | ✅ 일치. |
| Claude | "MCS index 13, TDLA/TDLB/CDL-A/CDL-C" (38.521-4 test) | 38.521-4 §6.3.2.2.6 본문에는 채널 모델·MCS가 있으나 정확한 index 13 검증은 38.521-4 v16.12.0 PDF 직접 확인 필요. tracer 답변에는 이런 구체값 미회수. | △ 검증 불가 (학습지식 추정). |
| GPT | "MU-MIMO scheduler가 더 정교한 channel direction 정보를 얻으면서도 CSI feedback overhead를 제어" | 일반론 — Rel-16 enhanced Type II 도입 동기와 일치. | ✅ 일반론으로 일치. |
| GPT | "frequency-domain compression 지원" capability | 학습지식 high-level 서술. 정확한 IE 이름 없음. | △ 컨셉은 맞으나 검증 불가. |
| GPT | "38.521-4 CSI reporting requirement는 UE가 특정 CSI-RS/채널 조건에서 올바른 CSI를 보고할 수 있는가" | 학습지식 일반론. tracer retrieved에 동일 컨셉 ("test the accuracy of the PMI reporting such that the system throughput is maximized") 존재. | ✅ 일반론으로 일치. |
| tracer | (해당 없음 — retrieval log 100% 정합) | — | hallucination 0. |

**합계**: tracer 0건 / GPT 0건 (정량 검증 가능 claim 부재로 hallucination 판정 자체 어려움) / Claude 1건 △ (30% throughput) + 1건 △ (RP-182863/191085 출처) + 1건 △ (MCS index 13) — **명백한 ❌ hallucination 0건. 다만 Claude의 정량 수치는 spec-본문-grounded가 아닌 학습지식**.

---

## 3gpp-tracer 개선 시사점

### GPT/Claude가 더 잘 답한 영역 → tracer 보강 필요

| 영역 | GPT/Claude 우위 | tracer 개선 방향 | D/O/R |
|---|---|---|---|
| **38.331 ASN.1 IE 본문** | Claude가 CodebookConfig SEQUENCE 본문, TypeII-r16 SEQUENCE, n1-n2-codebookSubsetRestriction BIT STRING per (N1,N2) 직접 기술 | **(P1)** 38.331 chunk를 IE 단위로 재청킹. ASN.1 BEGIN..END block을 별도 chunk로 분리 (현재는 절 단위로 chunk-001만 회수됨). hybrid retrieval (sparse BM25 + dense) 도입 — ASN.1 syntax는 자연어 임베딩과 mismatch. | **R + O** |
| **38.306 capability 행** | Claude가 `csi-ReportFramework-r16`, `typeII-r16`, `simultaneousCSI-ReportsPerCC-r16`, `csi-ReportFrequencyGranularity-r16` 직접 명기 | **(P1)** 38.306 capability 표를 행 단위로 chunking. 표 행마다 "Capability name + Per/M/FDD-TDD/FR1-FR2 메타"를 별도 chunk로. | **R + O** |
| **38.214 paramCombination 8행 표** | Claude가 1~8 (L, p_v(rank1-2), p_v(rank3-4), β) 표 직접 | tracer는 chunk-001에서 "paramCombination-r16, mapping in Table 5.2.2.2.5-1"까지만 회수. **표 본문**(Table 5.2.2.2.5-1 자체)은 chunk-002 이상에 위치할 가능성 → top_k 확장 또는 sectionTitle="Table" filter 검색. | **R** |
| **WID 본문 직접 quote** | Claude가 RP-191085의 objective quote ("Specify enhancement...DFT-based compression") | **(P2)** RP-* TDoc(RAN plenary work item description) 별도 컬렉션 신설. 현재는 R1-* discussion chunk만 회수됨. | **R** |
| **38.521-4 시험 metric 추가** | Claude가 throughput-based test, PMI follow vs random, FR1.30-1 channel 모델 명시 | tracer는 §6.3.2.2.6 본문에 시험 파라미터까지 회수했으나 metric 정의 (throughput gain %)는 chunk-001 본문 외부 가능성. top_k 확장 + 다른 chunkIndex 회수. | **R** |

### tracer가 우위인 영역 (보존해야 할 강점)

- **chunkId traceability**: GPT/Claude는 spec section 번호만 — 사용자가 직접 spec PDF 열어봐야 검증 가능. tracer는 chunkId로 retrieval log 280 hits 직접 확인 가능.
- **학습지식 미첨가**: Claude의 "throughput 30%+", "MCS index 13", "RP-182863" 같은 학습지식 의존 정량/번호 미사용.
- **retrieved-grounded WID 흐름**: RAN1#95~#108 discussion 시간순 추적 (R1-1812322 → R1-1909583 → R1-2202121) — Claude의 단일 WID quote보다 토론 흐름 추적에 강함.
- **사용자 오타 보호**: 38.512-4 자체 치환 안 하고 양쪽 검색 → 사용자에게 사실 보고. Claude는 "38.512는 RRM이라고 해석"하며 자체 판단.
- **재현성**: retrieval log 280 hits + 검색 스크립트가 함께 보관 → 동일 답변 재생산 가능.

### ★ tracer가 GPT/Claude 수준으로 답하려면? (구체 행동)

1. **(P1, R+O) 38.331 IE-level chunking + hybrid retrieval**:
   - 현재: 38.331 절 단위 chunk-001에 IE block이 잘림.
   - 개선: ASN.1 BEGIN..END 블록을 IE 단위 chunk로 분리. Qdrant에 sparse(BM25) 인덱스 추가 → ASN.1 syntax 직접 매칭.
   - 영향 범위: Q1/Q2/Q4 (RRC parameter 질문 공통).
2. **(P1, R+O) 38.306 capability 표 행 단위 chunking**:
   - 현재: §4.2.7.10 chunk-001이 표 헤더만 회수.
   - 개선: 표 행마다 별도 chunk (capability name + Per/M/FDD-TDD/FR1-FR2 4개 메타).
   - 영향 범위: Q1/Q2/Q4 (UE capability 질문 공통).
3. **(P2, R) 38.101-4 별도 컬렉션 적재**:
   - 현재: 38.521-4가 normative ref로 인용하지만 38.101-4 본문 chunk 없음.
   - 개선: RAN4 컬렉션에 38.101-4 별도 적재. demod requirement 질문에 직접 응답 가능.
4. **(P2, R) RP-* TDoc (RAN plenary WID/SID) 별도 컬렉션**:
   - 현재: R1-* discussion chunk만 회수, RP-* WID 본문 미적재.
   - 개선: `ranX_rp_tdocs` 컬렉션 신설. type=WID/SID로 필터링 가능.
   - 영향 범위: 모든 "WID 도입 배경" 질문.
5. **(P2, R) Top-k 확장 + 동일 절 다른 chunkIndex 보강 검색**:
   - 현재: top_k=10 + chunk-001 위주.
   - 개선: 첫 검색 후 sectionId 매칭하는 다른 chunkIndex를 후처리로 보강 → Table 5.2.2.2.5-1 본문 회수 가능.

### D/O/R 분류 우선순위

- **D (데이터 자체 한계)**: 0건 — Rel-16은 안정 release, 시간이 해결할 영역 없음.
- **R (Retrieval/VDB 빌드 단계)**: P1 2건 (38.331/38.306 chunking) + P2 3건 (38.101-4 적재, RP-* 컬렉션, top-k 확장).
- **O (KG/온톨로지 모델링)**: P1 2건 (38.331 IE 노드 모델링, 38.306 Capability 노드 모델링).

→ **본 질문(Q1)에서 tracer 약점은 100% 시스템(R/O) 책임**. 데이터 가용성·답변 자체 결함 아님.

---

## 실무 활용 결론

| 상황 | 권장 모델 | 이유 |
|---|---|---|
| **사실 정확성 + 인용 traceability 우선** (논문, 표준 문서 작성, 감사) | **3gpp-tracer** | chunkId 100% 검증 가능, hallucination 0, retrieved-grounded만 인용. |
| **답변 풍부함 + 학습 자료 / 일반 컨텍스트** (신입 교육, overview 보고서) | **Claude** | 7개 항목 모두 깊이, ASN.1·수식·표·시험 metric까지. 권위 cross-check 시 핵심 spec 사실 일치. |
| **흐름 이해 / high-level overview** (의사결정자 brief) | GPT | 흐름도 + IE 표가 가독성 좋음. 단 정확한 spec section 번호 검증은 다른 모델 병행 필요. |
| **38.331/38.306 IE 정의 직접 인용 필요** (구현 참조) | **Claude** + spec PDF 교차검증 | tracer 미회수. Claude의 ASN.1을 trust-but-verify (실제 38.331 v16.x PDF로 1:1 대조). |
| **WID 도입 배경 토론 흐름** (RAN1 합의 추적) | **3gpp-tracer** | RAN1#95~#108 discussion chunk 시간순 추적 가능. Claude의 단일 quote는 출처 불명. |
| **사용자 표기 오타 / 미적재 spec 처리** | **3gpp-tracer** | "38.512-4" 같은 오타를 자체 판단 치환 안 하고 사실 보고. Claude는 자체 해석. |

### 권장 사용 패턴 (Hybrid)

1. **tracer로 1차 검색 + chunk-level 사실 확보** (38.214/38.212/38.521-4/WID 흐름).
2. **tracer가 한계 명시한 영역**(38.331 ASN.1, 38.306 capability 행)에 한해 **Claude로 보강**.
3. **Claude 답변의 정량 수치·RP 번호·구체 시험값**은 spec PDF 또는 권위 출처(sharetechnote, ATIS, IEEE)로 cross-check.
4. **GPT는 flow brief 용도**로만, 사실 검증 단계 미사용.

---

*평가 완료. 본 보고서의 모든 5축 점수와 hallucination verdict는 권위 출처(sharetechnote, ATIS V16.2.0, 3GPP 38.521-4 cover, IEEE Rel-16 Type II 논문) 1:1 대조 결과 + tracer retrieval log 280 hits 검증에 기반한다.*
