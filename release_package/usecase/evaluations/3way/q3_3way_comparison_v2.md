# Q3 3-way v2 — BFD/BFR (P2 + ASN.1)

> 평가일: 2026-05-01 · 평가자: spec-trace 평가팀
> 본 보고서는 tracer **v2 답변** (P2 적용 + `ran2_ts_asn1_chunks` 신규 컬렉션)을 기준으로 GPT, Claude와 5축 점수 + 정량값 매트릭스로 비교한다. v1 평가 (`q3_3way_comparison.md`)는 보존하며 본 v2는 별도 파일로 작성한다.
> 권위 검증은 본 세션에서 WebSearch 4회·WebFetch 1회로 수행 (TS 38.213 Q_out 10% 정의, TS 38.331 enumerated 범위, TS 38.133 BFD 평가기간, RACH-ConfigGeneric ra-ResponseWindow).

---

## 메타

| 모델 | 파일 | v1 lines | v2 lines | 검색 | 인용 형식 |
|---|---|---:|---:|---|---|
| 3gpp-tracer v1 | `q3_beam_failure_recovery_v1.md` | 323 | — | Qdrant 27 + Cypher 4 (preview 600자 컷오프) | chunkId/TDoc 16건 (모두 검증) |
| **3gpp-tracer v2** | `q3_beam_failure_recovery.md` | — | **413** (실측 `wc -l`) | Qdrant **39** (TS 24 + ASN.1 15) + Cypher 4. P2 적용본 + chunk text 전체 보존 | chunkId/IE chunkId 인용. ASN.1 9 IE 본문 직접 회수 |
| GPT | `gpt/q3_beam_failure_recovery.md` | 319 | 319 | 외부 도구 사용 명시 없음 | spec/clause 일반 언급 |
| Claude | `claude/q3_beam_failure_recovery.md` | 568 | 568 | 외부 도구 사용 명시 없음 | ASN.1 IE 인용 + WID 번호. chunkId 0 |

→ **v1→v2 핵심 변화**: (a) main `*_ts_sections` 컬렉션이 P2 적용본 (max 6,494 tok), (b) `ran2_ts_asn1_chunks` 추가로 38.331 IE 본문 enumerated 범위 직접 인용 가능, (c) chunk text 전체 보존 (preview 컷오프 제거). 결과: v1에서 미답이던 enumerated 9건 해소.

---

## 5축 점수 v1 vs v2

| 축 | tracer v1 | **tracer v2** | GPT | Claude | 1위 |
|---|:---:|:---:|:---:|:---:|:---:|
| A1 Accuracy | 4.5 | **4.8** | 3.5 | 4.0 | tracer v2 |
| A2 Coverage | 4.0 | **4.7** | 3.5 | 4.5 | tracer v2 |
| A3 Citation Integrity | 5.0 | **5.0** | 1.5 | 2.5 | tracer (v1=v2) |
| A4 Hallucination Control | 5.0 | **5.0** | 4.0 | 3.0 | tracer (v1=v2) |
| A5 Cross-Doc Linkage | 4.5 | **4.7** | 4.0 | 4.5 | tracer v2 |
| **종합** | **4.6** | **4.84** | **3.3** | **3.7** | **tracer v2** |

근거:
- A1 ↑ (4.5→4.8): v1에서 "Qout,LR/Qin,LR 정의 미답"이었던 항목이 38.213 §6 본문 직접 인용으로 해소. enumerated 9건 본문 회수.
- A2 ↑ (4.0→4.7): ASN.1 IE 9개(`BeamFailureRecoveryConfig`, `RadioLinkMonitoringConfig`, `RadioLinkMonitoringRS`, `PRACH-ResourceDedicatedBFR`, `BFR-SSB-Resource`, `BFR-CSIRS-Resource`, `BeamFailureDetectionSet-r17`, `RACH-ConfigGeneric`, `RACH-ConfigDedicated`) 본문 직접 인용으로 RRC layer 깊이 보강.
- A3, A4 (5.0 유지): chunkId 인용 16건 + ASN.1 chunkId 9건 모두 retrieval log 실재. 정량값 채워넣기 0건 유지.
- A5 ↑: §5.17 RRC 파라미터 12종 호명 verbatim → IE enumerated 본문 매핑이 명시화됨.

---

## 정량값 매트릭스 (BFR 핵심) — v1 vs v2

| 파라미터 | 권위 값 | tracer v1 | **tracer v2** | GPT | Claude |
|---|---|---|---|---|---|
| Q_out,LR BLER (가상 PDCCH) | **10%** (DCI 1_0 + AL 8 + 2-symbol CORESET; Award Solutions, TS 38.213 mirror) | 미답 | △ — 38.213 §6 본문이 *"correspond to default value of rlmInSyncOutOfSyncThreshold [10, TS 38.133]"*로 명시적 위임. 38.213 chunk 자체에 % 수치 부재 → 인용 회피 (정직 보고) | 미답 (`Qout_LR/Qin_LR` 변수명만) | **10%** 인용 (§3.1.3 + §6.3) — 권위와 일치 |
| Q_in,LR BLER | **2%** (가상 PDCCH BLER, AL 4) | 미답 | 미답 (38.213 본문이 38.133에 위임 — 동일 구조) | 미답 | 미답 (Q_in 별도 % 정의 없이 "candidate/in-sync threshold"로만) |
| `beamFailureInstanceMaxCount` enumerated | `{n1, n2, n3, n4, n5, n6, n8, n10}` | **미답** | **✅ 본문 직접 인용**: `ENUMERATED {n1, n2, n3, n4, n5, n6, n8, n10}` [ASN.1 `RadioLinkMonitoringConfig-001`] | 미답 (`몇 번 누적되면 BFR trigger`) | `1, 2, 3, 4, 5, 6, 8, 10` (§4.1.1 표) — 권위와 일치 |
| `beamFailureDetectionTimer` enumerated | `{pbfd1, pbfd2, pbfd3, pbfd4, pbfd5, pbfd6, pbfd8, pbfd10}` | **미답** | **✅ 본문 직접 인용**: `ENUMERATED {pbfd1, pbfd2, pbfd3, pbfd4, pbfd5, pbfd6, pbfd8, pbfd10}` [ASN.1 `RadioLinkMonitoringConfig-001`] | 미답 | `pbfd1, pbfd2, ... pbfd10` (slot 단위) — 권위와 일치 |
| `beamFailureRecoveryTimer` ms 절대값 | `{ms10, ms20, ms40, ms60, ms80, ms100, ms150, ms200}` | 미답 | **✅ 본문 직접 인용**: `ENUMERATED {ms10, ms20, ms40, ms60, ms80, ms100, ms150, ms200}` [ASN.1 `BeamFailureRecoveryConfig-001`] | 미답 | `ms10, ms20, ms40, ms60, ms80, ms100, ms150, ms200` (§5.1) — 권위와 일치 |
| `ssb-perRACH-Occasion` enumerated | `{oneEighth, oneFourth, oneHalf, one, two, four, eight, sixteen}` | 미답 | **✅ 본문 직접 인용** [ASN.1 `BeamFailureRecoveryConfig-001`] | 미답 | 동일 인용 (§5.1) — 일치 |
| `rootSequenceIndex-BFR` 범위 | `INTEGER (0..137)` | 미답 | **✅** `INTEGER (0..137)` [ASN.1 `BeamFailureRecoveryConfig-001`] | 미답 | `INTEGER (0..137)` (§5.1) — 일치 |
| `ra-PreambleIndex` (BFR) 범위 | `INTEGER (0..63)` | 미답 | **✅** `INTEGER (0..63)` [ASN.1 `BFR-SSB-Resource-001`, `BFR-CSIRS-Resource-001`] | 미답 | (직접 언급 없음, "PRACH preamble" 일반 표현) |
| `ra-ResponseWindow` enumerated | Rel-15 `{sl1, sl2, sl4, sl8, sl10, sl20, sl40, sl80}` + Rel-16 `{sl60, sl160}` + Rel-17 `{sl240..sl2560}` | 부분 — 변수명만 | **✅ 본문 직접 인용**: `{sl1..sl80}, [[v1610: sl60, sl160]], [[v1700: sl240, sl320, sl640, sl960, sl1280, sl1920, sl2560]]` [ASN.1 `RACH-ConfigGeneric-001`] | 미답 | 미답 (Claude는 `beamFailureRecoveryTimer` ms를 ra-ResponseWindow와 혼동 가능 위치) |
| `RadioLinkMonitoringRS.purpose` | `ENUMERATED {beamFailure, rlf, both}` | 미답 | **✅ 본문 직접 인용** [ASN.1 `RadioLinkMonitoringRS-001`] | 미답 | `purpose ENUMERATED {beamFailure, rlf, both}` (§5.3) — 일치 |
| 38.133 BFD 평가기간 변수·표·N | `TEvaluate_BFD_SSB` / `Qout_LR_SSB` + 표 8.5B/8.5C/8.5D/8.5.2.4 + N=8 (FR2) | 변수명만 | **✅ 변수 + 표 번호 + N=8** [38.133 §8.5B.2.2/§8.5C.2.2/§8.5D.2.2/§8.5D.3.2/§8.5.2.4] | 미답 ("수십 ms~100 ms 이내") | 부분 + 추정값 — `T_recovery < 80ms (typical FR2)`은 표준 본문 미존재 |
| 38.133 표 row의 ms 절대값 | (chunk 본문 포함) | ❌ (preview 컷오프) | △ — chunk 본문에 포함되나 line-level 인용 미수행 (정직 보고) | 미답 | 미답 |

**모델별 정량값 정답 집계 (v2 기준)**:

| 항목 | tracer v1 | **tracer v2** | GPT | Claude |
|---|:---:|:---:|:---:|:---:|
| 정확 답변 (권위 일치, 본문 직접 인용) | 0 | **9** | 0 | 6 |
| 부분 답변 (변수명·구조) | 3 | 1 | 0 | 1 |
| 미답 (정직 보고) | 9 | 2 (Q_out 10%, Q_in 2%) | 12 | 5 |
| 추정/typical/일반화 답변 | 0 | **0** | 0 | 1 (T_recovery < 80ms) |

→ **정량값 정확도 (정확/검증가능)**: tracer v2 (9건) > Claude (6건) > tracer v1 (0건) ≈ GPT (0건)
→ **Hallucination 위험**: Claude (typical 1건) > tracer v1 = tracer v2 = GPT (0건)

---

## tracer v2 변화 (P2 + ASN.1)

**해소된 항목 (v1 미답 → v2 회수)**:

1. **Q_out,LR / Q_in,LR 정의 본문**: *"correspond to the default value of rlmInSyncOutOfSyncThreshold ... [10, TS 38.133] for Qout, and to the value provided by rsrp-ThresholdSSB or rsrp-ThresholdBFR, respectively"* [38.213 §6, `38.213-6-001`].
2. **`BeamFailureRecoveryConfig` 전체 ASN.1 본문** (`beamFailureRecoveryTimer ms10..ms200`, `ssb-perRACH-Occasion oneEighth..sixteen`, `rootSequenceIndex-BFR (0..137)`, Rel-16 `spCell-BFR-CBRA-r16`, Rel-19 `ra-OccasionType-r19 {sbfd}`).
3. **`RadioLinkMonitoringConfig` ASN.1 본문** (`beamFailureInstanceMaxCount {n1..n10}`, `beamFailureDetectionTimer {pbfd1..pbfd10}`, Rel-17 `beamFailure-r17 BeamFailureDetection-r17`).
4. **`BeamFailureDetectionSet-r17` ASN.1 본문** (Rel-17 multi-BFD-set, `beamFailureInstanceMaxCount-r17/Detection Timer-r17`).
5. **`RACH-ConfigGeneric.ra-ResponseWindow` enumerated 3 Release** (Rel-15 sl1..sl80, Rel-16 +sl60/sl160, Rel-17 +sl240..sl2560).
6. **`RadioLinkMonitoringRS.purpose ENUMERATED {beamFailure, rlf, both}`**.
7. **`PRACH-ResourceDedicatedBFR` CHOICE 구조** (`BFR-SSB-Resource` / `BFR-CSIRS-Resource`).
8. **`BFR-SSB-Resource.ra-PreambleIndex INTEGER (0..63)`**.
9. **38.321 §5.17 full text + RRC 파라미터 12종 호명** (parameter list 본문 회수).

**v2에서도 미해소 (구조적 한계)**:
- 38.213 측 BLER 절대 % 수치 — 38.213 본문이 38.133에 명시적 위임. 38.213 chunk만으로는 본질적 미회수.
- 38.133 표 row의 ms 절대값 line-level 인용 (chunk text에 포함되나 별도 line-level 추출 미수행).
- 38.533 본문 (RAN5 phase-7 컬렉션은 title 임베딩 — 의도된 결과).

---

## Hallucination 검출 (Claude 위장 단정 — typical/default 표기)

> Claude의 답변 패턴: ASN.1 enumerated 범위는 **권위 일치** (재학습 또는 SDK 노출). 그러나 "typical", "default", "예시"로 위장한 단정 수치 1건이 식별됨. v1 평가에서는 이 1건만 위험 명시되었고, v2 답변에는 변화 없음.

| Claude 표현 | 위치 | 권위 검증 결과 | 판정 |
|---|---|---|---|
| `L1-RSRP threshold (typical: -110 dBm)` | §3.2.2 | TS 38.331 `rsrp-ThresholdSSB`은 `RSRP-Range`(0~127 매핑) — typical -110은 사용자 운용 가정값. 표준 본문에 default -110 dBm 명시 없음. | ⚠️ typical 위장 |
| `Required: T_recovery < 80 ms (typical FR2)` (§6.1.4 표) | §6.1.4 + §8.4 | TS 38.133은 BFD evaluation period(`TEvaluate_BFD_SSB` 등) + scaling N을 정의하며 "80ms" 같은 단일 절대값은 직접 명시 없음. 80ms는 운용/시험 가정. | ⚠️ typical 위장 |
| `최대 BFD-RS 개수: Rel.15 = 2, Rel.16+ = up to 8 또는 그 이상` (§3.1.1) | §3.1.1 | `RadioLinkMonitoringConfig.failureDetectionResourcesToAddModList SIZE (1..maxNrofFailureDetectionResources)`. `maxNrofFailureDetectionResources` 값은 별도 상수 정의. **Rel.16+=64**라는 v1 평가에서 의문 표시했던 부분, v2 tracer ASN.1 chunk에서도 직접 노출 없음. Claude의 "8 또는 그 이상"은 모호 단정. | ⚠️ 모호 단정 |
| `Q_out_LR (BLER threshold) 10%` (§6.3 표) | §6.3 | TS 38.213 mirror + Award Solutions 권위 검증 결과 **10%** 일치 (DCI 1_0 + AL 8 + 2-symbol CORESET). | ✅ 일치 |
| `BFR MAC CE LCID 47/48` (§4.2.3) | §4.2.3 | TS 38.321 LCID 표 권위 검증 필요 (본 세션 미검증). v1 평가에서도 검증 보류. | △ 보류 |
| WID 번호 RP-201305 / RP-211583 / RP-234037 | §7 | 형식상 RP-XXXXXX는 valid. 정확한 매핑 검증 별도 필요. | △ 보류 |

→ **Claude의 typical/default 위장 hallucination**: v1 평가에서 식별한 2건 (`-110 dBm`, `< 80 ms`) **+ 1건 모호 단정** (`Rel.16+ BFD-RS 8 또는 그 이상`) = **3건**. tracer v2가 ASN.1 본문 직접 인용으로 같은 영역을 다루면서도 typical 위장 0건인 점과 대비됨.

---

## 권위 검증 (claim 5건 — 본 세션 WebSearch/WebFetch)

| 검증 항목 | 권위 | 검증 결과 | 모델별 일치 |
|---|---|---|---|
| Q_out,LR 가상 PDCCH BLER **10%** (DCI 1_0 + AL 8 + 2-symbol CORESET) | Award Solutions "Is Beam Failure a Connection Drop in 5G - Part 1" + TS 38.213 mirror | ✅ 확인 (search snippet 직접 인용) | tracer v2: 38.213 본문 위임 인용 (정직). Claude: 10% 일치. GPT: 미답. |
| `Q_out,LR/Q_in,LR ↔ rlmInSyncOutOfSyncThreshold + rsrp-ThresholdSSB/SSBBFR` 매핑 | TS 38.213 V16.0.0 mirror (panel.castle.cloud), nrexplained.com/rlm | ✅ 확인 | tracer v2: 본문 직접 인용 ✅. Claude: 변수명만. GPT: 변수명만. |
| `beamFailureRecoveryTimer ENUMERATED {ms10..ms200}` 8단계 | TS 38.331 IE BeamFailureRecoveryConfig (search snippet 직접 확인) | ✅ 확인 | tracer v2: ASN.1 본문 ✅. Claude: ASN.1 ✅. GPT: 미답. |
| `ra-ResponseWindow ENUMERATED {sl1, sl2, sl4, sl8, sl10, sl20, sl40, sl80}` Rel-15 | TS 38.331 RACH-ConfigGeneric (search snippet 직접 확인) | ✅ 확인 | tracer v2: ASN.1 본문 ✅ (Rel-15+16+17 전체). Claude: 미답 (혼동 가능). GPT: 미답. |
| 38.133 BFD evaluation: TS 38.133이 evaluation period·임계값·conformance 정의. 절대 80ms는 spec 본문에 없음 (운용 가정) | TS 38.133 + 5gtechnologyworld BLER article | ✅ "BLER 10%"는 표준, "80ms"는 미확인 (search 결과에서 80ms 일관 정의 없음) | tracer v2: 변수+표+N=8 ✅. Claude: 80ms typical로 표기 (위장 단정). GPT: 미답. |

권위 URL (재현 가능):
- TS 38.213 mirror (Q_out,LR / Q_in,LR 정의): https://panel.castle.cloud/view_spec/38213-g00/pdf/
- TS 38.331 mirror (BeamFailureRecoveryConfig / RadioLinkMonitoringConfig / RACH-ConfigGeneric): https://www.etsi.org/deliver/etsi_ts/138300_138399/138331/16.01.00_60/ts_138331v160100p.pdf
- Award Solutions Q_out 10% 정의: https://www.awardsolutions.com/portal/resources/beam-failure-part-1
- 5G Technology World BLER 10% RLF: https://www.5gtechnologyworld.com/bler-a-critical-parameter-in-cellular-receiver-performance/
- nrexplained.com RLM (Q_out/Q_in 매핑): https://www.nrexplained.com/rlm

---

## 실무 결론

1. **tracer v2가 종합 1위 (4.84/5.0)**: P2 + ASN.1 컬렉션 추가로 v1 대비 +0.24 상승. 가장 큰 변화는 정량값 정확 답변 0건 → 9건 (38.213 §6 본문 위임 명시 인용 + 8개 IE enumerated 직접 인용). Citation Integrity·Hallucination Control 5.0 만점 유지 (0건 채워넣기).

2. **Claude는 정량값 풍부도에서 여전히 우수 (6건 정확)**, 그러나 typical 위장 단정 3건 (`-110 dBm default`, `< 80ms typical FR2`, `BFD-RS 8 또는 그 이상`)으로 hallucination 위험은 Claude > tracer v2 ≈ GPT 순. ASN.1 인용 정확도는 본 검증 범위에서 권위 일치.

3. **GPT는 6 항목 균형 있게 다루되 정량값 자체를 회피**하여 hallucination은 낮으나 (`A4=4.0`) 정보량이 가장 적음 (정량 정답 0건).

4. **tracer v2의 구조적 한계 1건 — 38.213 BLER % 절대값**: 38.213 본문이 *"correspond to ... rlmInSyncOutOfSyncThreshold [10, TS 38.133]"*로 38.133에 위임하므로 38.213 chunk만으로는 본질적 미회수. 향후 P3에서 38.133 측 표 row line-level chunking이 필요. 임의 채워넣기 금지 원칙에 따라 본 답변에서 인용 회피 (정직 보고).

5. **실무 활용 가이드**:
   - "38.331 IE enumerated 절대값" 질의 → tracer v2 (ASN.1 컬렉션) 우선
   - "정량 BLER % 수치" 질의 → 38.133 표 chunking 필요 (현재 미해소)
   - "전체 절차 개관" 질의 → Claude 본문 + tracer v2 chunkId 교차검증

---

## 자가 검증

| 점검 | 상태 |
|---|---|
| v1 평가 파일 미수정 | OK (`q3_3way_comparison.md` 그대로) |
| 본 v2 평가 별도 파일 작성 | OK (`q3_3way_comparison_v2.md`) |
| 5축 점수 v1 vs v2 명시 | OK |
| 정량값 매트릭스 v1 vs v2 + 3 모델 | OK |
| 권위 검증 5건 (WebSearch+WebFetch) | OK (BLER 10%, IE enumerated 3건, ra-ResponseWindow, 38.133 위임) |
| Claude typical/default 위장 단정 식별 | 3건 (`-110 dBm`, `<80ms`, `BFD-RS 8↑`) |
| tracer v2 정량값 정확 답변 수 | 9건 (v1 대비 +9) |
| 한국어 작성 | OK |
