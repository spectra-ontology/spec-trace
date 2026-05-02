# Q3 품질 평가 — Beam Failure Detection/Recovery

## 평가 메타

- 평가일: 2026-04-29
- 1차 답변: `docs/usecase/answers/tracer/q3_beam_failure_recovery.md` (323 lines)
- Retrieval log: `logs/cross-phase/usecase/q3_retrieval_log.json` (TS 27쿼리·270 hit, TDoc 12쿼리·120 hit, Cypher 4건)
- 평가 방식: 1차 답변의 모든 fact-claim을 (a) retrieval log 실재성 (b) 권위 출처와 일치성 (c) 1차가 명시한 "preview 컷오프 미회수"를 학습지식으로 채워넣었는지 — 3가지 차원으로 검증
- 사용한 권위 웹 출처:
  - [3GPP TS 38.213 V16.0.0 (castle.cloud mirror)](https://panel.castle.cloud/view_spec/38213-g00/pdf/)
  - [Award Solutions — Is Beam Failure a Connection Drop in 5G Part 1](https://www.awardsolutions.com/portal/resources/beam-failure-part-1)
  - [ShareTechnote — 5G/NR Beam Failure Recovery](https://www.sharetechnote.com/html/5G/5G_BeamFailureRecovery.html)
  - [TechSpec — 38.321 §5.17 Beam Failure Detection and Recovery](https://itecspec.com/spec/3gpp-38-321-5-17-beam-failure-detection-and-recovery-procedure/)
  - [TechSpec — 38.300 §9.2.8 Beam failure detection and recovery](https://itecspec.com/spec/3gpp-38-300-9-2-8-beam-failure-detection-and-recovery/)
  - [WirelessBrew — BFD/BFR procedure 5G NR](https://wirelessbrew.com/5g-nr/5g-mac-layer/beam-failure-detection-and-recovery-procedure-in-5g-nr/)
  - [Justia Patent — SCell BFR Patent #11,909,488](https://patents.justia.com/patent/11909488)
  - [Award Solutions — RLM/BFD thresholds](https://www.awardsolutions.com/portal/resources/beam-failure-part-1)

---

## 5축 점수 (0~5)

| 축 | 점수 | 근거 요약 |
|---|---:|---|
| A1 Accuracy | 4.5 | 절차/이름/IE/변수명 모두 권위 출처와 일치. 정량값(BLER %, ms, enumerated 범위)은 1차가 의도적으로 인용 회피 → 가짜 수치 0건. 단점: Q_out_LR / Q_in_LR 정의(가상 PDCCH BLER 10%/2%)는 38.133 영역으로 retrieve 됨에도 본문에서 "직접 chunk 매칭 약함"이라고만 표기 — 실제 chunk 본문에 들어있을 가능성을 더 깊이 파지 않음 |
| A2 Coverage | 4.0 | 6개 항목(도입배경/38.213/38.321/38.331/38.133/38.533/연결고리) 모두 다룸. 시퀀스 다이어그램 + 연결고리 도식 우수. 한계: enumerated 범위(`n1~n10`, `pbfd1~pbfd10`)와 ms 단위 평가 기간 표 row를 retrieval에는 있는지 표시했으나 실제 인용 0건 → 사용자 질문의 "정량값" 축은 ~40% 만족 |
| A3 Citation Integrity | 5.0 | 1차가 인용한 16개 chunk/TDoc 중 **16/16 모두 retrieval log에 실재**. 본문 인용 quote가 retrieval log의 `text_preview`/`content_preview`와 verbatim 일치. R1-1707606, R1-1713597, R2-1803196, R2-1900212, R2-2301761, R2-2407883, R5-204985, 38.213-6-001, 38.321-5.17-001, 38.321-5.1.4-001, 38.133-8.18.2.2-001, 38.133-8.5B.2.2-001, 38.133-8.5D.3.2-001, 38.533-17.5.2.1-001, 38.533-7.5.6.1.2-001, 38.321-6.1.3.30-001 전부 검증 |
| A4 Hallucination Control | 5.0 | **핵심 평가축에서 만점**. 1차 보고서가 "정량값 미회수"라고 자가 진단한 5개 항목(BLER 10%/2%, beamFailureInstanceMaxCount 범위, beamFailureDetectionTimer 범위, 표 8.18.2.2-1 ms row, 38.533 test tolerance) 모두 본문에 채워넣지 않음. 자가 검증 표 §자가 검증에서 "**NO** — 정량 정의 변수명만 chunk에서 직접 인용. row의 ms 단위 수치는 preview 미노출이므로 본문에 인용하지 않음" 명시. 학습지식 누출 0건 |
| A5 Cross-Doc Linkage | 4.5 | BFR 시퀀스 (RRC config → L1 q0 측정 → MAC instance counting → contention-free PRACH → ra-ResponseWindow → RAN4 평가 기간 → RAN5 conformance) 8단계 다이어그램 + 5개 명시적 연결 인용. 38.331↔38.321 연결은 R2-2407883 본문의 "See also TS 38.321 [3], clause 5.17" 직접 인용으로 강함. 약점: 38.213→38.321의 L1 indication 메커니즘을 R2-1803196(RAN2 분석문서)으로만 연결, 38.213 본문에서 직접 "MAC reports beam failure instance" 같은 chunk는 인용 없음 (RAN1 spec은 PHY indication 정의가 약하게 retrieve됨) |
| **종합** | **4.6 / 5** | citation integrity와 hallucination control 만점, accuracy/coverage/linkage는 정량값 비인용 정책 때문에 0.5씩 차감. 1차 답변은 "검색기에서 실제로 회수한 사실만 인용"이라는 spec-trace 원칙을 모범적으로 지킴 |

---

## 정량값 검증 (BFR 핵심)

| 파라미터 | 권위 소스 값 | 1차 답변 처리 | 평가 |
|---|---|---|---|
| Q_out,LR BLER 임계값 | 10% (가상 PDCCH, DCI format 1_0, CCE aggregation level 8, 2-symbol CORESET) [Award Solutions, ShareTechnote, TS 38.213 mirror] | 본문에 수치 미인용 + "커버리지 한계: top score 0.33로 직접 chunk 매칭 약함" 명시 | ⚠️ 미답이지만 정확 (가짜 값 안 채움) |
| Q_in,LR BLER 임계값 | 2% (가상 PDCCH, DCI 1_0, CCE aggregation 4) [Award Solutions, ShareTechnote] | 본문에 수치 미인용 | ⚠️ 미답이지만 정확 |
| beamFailureInstanceMaxCount 범위 | `{n1, n2, n3, n4, n5, n6, n8, n10}` [ShareTechnote, WirelessBrew] | 변수명만 인용("counter ≥ beamFailureInstanceMaxCount 도달 시 BFR 트리거" — 단, 이는 R2-1803196 인용으로 처리), enumerated 범위 미공개 | ⚠️ 미답이지만 정확 |
| beamFailureDetectionTimer 범위 | `{pbfd1, pbfd2, pbfd3, pbfd4, pbfd5, pbfd6, pbfd8, pbfd10}` [ShareTechnote] | 본문에서 변수명·범위 모두 미인용 (chunk score 낮아 미검색이라 §자가 검증·"3gpp-tracer 미발견" 목록에 명시) | ⚠️ 미답 (정확) |
| ra-ResponseWindow 범위 | `{sl1, sl2, sl4, sl8, sl10, sl20, sl40, sl80}` [ShareTechnote] | 변수명·연결만 인용 (`BeamFailureRecoveryConfig` 내), 범위 미인용 | ⚠️ 미답 (정확) |
| BFD 평가 기간 (38.133 §8.18.2.2-1) | TEvaluate_BFD_SSB FR1 표 본체. FR2-1 N=2/4/6, FR2 N=8 [TS 38.133 mirror, retrieval log preview] | 변수명·N 값(2,4,6) chunk verbatim 인용. 표 row의 ms 절대값은 preview 컷오프로 미인용 — §커버리지/한계 표에 명시 | ✅ 부분 답변 정확 |
| Qout_LR_SSB 임계값 (38.133) | RAN4가 정의한 DL link quality 임계값 (38.213 Q_out,LR과 정합). 38.133 §8.18.2.2 본문 변수 [retrieval log 8.18.2.2-001] | 변수명 정확 인용, 절대값 미인용 | ✅ 변수명 인용 정확 |
| BFR test tolerance (38.533) | 38.533 §17.5.2.1 PC3 / f ≤ 40.8 GHz. §7.5.6.1.2는 *Editor's note: incomplete, FFS, Test tolerance analysis is missing* [retrieval log] | "FFS 마커 그대로 포함, 단정 인용 불가" 명시 | ✅ 한계 정확 표기 |
| BFR PRACH 형식 | contention-free Random Access Preamble, ra-ResponseWindow는 BeamFailureRecoveryConfig 내 [TS 38.321 §5.1.4] | "BFR PRACH는 contention-free 형태로 전송되고, 응답 모니터링은 BeamFailureRecoveryConfig 내 ra-ResponseWindow로 제어" — 38.321 §5.1.4 chunk verbatim | ✅ 정확 |
| L1-RSRP 측정 메트릭 | NR BFD 측정 메트릭은 L1-RSRP [R1-1713597] | R1-1713597 Proposal 1 verbatim 인용 | ✅ 정확 |
| SCell BFR 도입 release | Rel-16 [Intel patent, RAN1/RAN2 agreement, Justia patent #11,909,488] | R2-1900212 Rel-16 인용 — "Current Rel-15 BFR is useless in support of beam failure on the SCell" verbatim | ✅ 정확 |

---

## 항목별 권위 검증 (Claim-by-claim)

| # | 1차 claim | 인용 chunk | 권위 출처 verdict | 코멘트 |
|---:|---|---|---|---|
| 1 | "NR Rel-15 RAN1 단계에서 빔 실패에서의 회복 메커니즘이 별도 절차로 도입" | R1-1707606 (Rel-15) | ✅ 일치 | retrieval log에서 release="Rel-15", agendaItem=7.1.2.2.2 확인 |
| 2 | "Mechanism 1과 2 모두 지원" Proposal #1 본문 | R1-1707606 | ✅ 일치 | content_preview verbatim 일치 |
| 3 | "L1-RSRP as the measurement metric to detect beam failure" Proposal 1 | R1-1713597 | ✅ 일치 | content_preview에 정확히 존재. 권위 소스(ShareTechnote·Award Solutions)도 L1-RSRP 메트릭 확인 |
| 4 | "Beam failure recovery procedure is described in section 5.17 of TS 38.321 ... a number of beam failure instances ... will trigger a random access procedure" | R2-1803196 | ✅ 일치 | content_preview verbatim |
| 5 | "Current Rel-15 BFR is useless in support of beam failure on the SCell" | R2-1900212 (Rel-16) | ✅ 일치 | Rel-16 SCell BFR 도입 동기. patent #11,909,488와 정합 |
| 6 | "When the beam of SCell changes while the SCell is deactivated... Allow UE to trigger beam failure recovery on SCell..." | R2-2301761 (Rel-18) | ✅ 일치 | Rel-18 추가 강화 정확 |
| 7 | 38.213 §6 q0/q1 자원 정의 (`failureDetectionResourcesToAddModList`, `candidateBeamRSList`) | 38.213-6-001 | ✅ 일치 | text_preview에 verbatim. TS 38.213 권위 소스와 정합 |
| 8 | 38.321 §5.17 "MAC entity may be configured by RRC per Serving Cell or per BFD-RS set with a beam failure recovery procedure" | 38.321-5.17-001 | ✅ 일치 | TechSpec 권위 소스와 절차 일치 |
| 9 | 38.321 §5.1.4 "contention-free Random Access Preamble for beam failure recovery request ... start the ra-ResponseWindow configured in BeamFailureRecoveryConfig" | 38.321-5.1.4-001 | ✅ 일치 | text_preview verbatim |
| 10 | 38.331 IE `BeamFailureRecoveryRSConfig` "See also TS 38.321 [3], clause 5.17" + `rsrp-ThresholdBFR-r16  RSRP-Range` | R2-2407883 | ✅ 일치 | content_preview에 ASN.1 fragment 그대로. RSRP-Range 타입 정확 |
| 11 | 38.133 §8.18.2.2 "TEvaluate_BFD_SSB ... Qout_LR_SSB ... FR2 with scaling factor N, where N=2,4,6 in FR2-1" | 38.133-8.18.2.2-001 | ✅ 일치 | text_preview verbatim. FR2-1 N 값까지 정확 |
| 12 | 38.133 §8.5B.2.2 "TEvaluate_BFD_SSB_Redcap" RedCap 변형 | 38.133-8.5B.2.2-001 | ✅ 일치 | text_preview verbatim |
| 13 | 38.133 §8.5D.3.2 "TEvaluate_BFD_CSI-RS ... Qout_LR_CSI-RS" | 38.133-8.5D.3.2-001 | ✅ 일치 | text_preview verbatim |
| 14 | 38.533 §17.5.2.1 "verify ... UE properly detects SSB-based beam failure in the set q0 ... PC3, f ≤ 40.8 GHz" | 38.533-17.5.2.1-001 | ✅ 일치 | text_preview verbatim. Editor's Note도 chunk에 존재 |
| 15 | 38.533 §7.5.6.1.2 "Editor's note: incomplete ... FFS ... Test tolerance analysis is missing" | 38.533-7.5.6.1.2-001 | ✅ 일치 | text_preview verbatim. 1차가 정량 인용 회피한 근거로 사용 — 적절 |
| 16 | "The normative reference for this requirement is TS 38.133 [6] clause A.4.5.5.1" | R5-204985 (Rel-16) | ✅ 일치 | content_preview verbatim |

---

## 발견한 Hallucination

**0건**.

핵심 분석:
- 1차 답변은 사용자 질문의 핵심 정량값(BLER %, beamFailureInstanceMaxCount 범위, beamFailureDetectionTimer 범위, 38.133 표 ms row, 38.533 tolerance)을 **전부 미인용 처리**.
- §자가 검증 표 4번 항목 "임의의 타이머/카운터/임계값 수치를 학습지식으로 채워넣었는가? **NO**"가 권위 검증 결과 사실로 확인됨.
- §"3gpp-tracer에서 미발견(또는 retrieval 신뢰도 부족)으로 답변 제외" 5개 bullet이 정직한 한계 보고로 작동.
- LLM이 학습지식으로 알고 있을 법한 매우 유명한 값(`Q_out=10%`, `Q_in=2%`, `n1~n10`, `pbfd1~pbfd10`)도 전혀 누출되지 않음 — spec-trace 원칙 준수가 모범적.

**잠재적 위험 영역(검증 결과 hallucination 아님)**:
- 본문 §1 "RAN2 측 도입 동기 ... 빔포밍 기반 NR 운영에서 RLF→RRC re-establishment는 너무 늦은 회복 경로이므로" — 이 인과 추론은 chunk 본문 직접 인용은 아님. 그러나 R2-1803196의 "based on a number of beam failure instances ... will trigger a random access procedure which allows the recovery"에서 합리적으로 도출되며 권위 출처([TechSpec 38.300 §9.2.8](https://itecspec.com/spec/3gpp-38-300-9-2-8-beam-failure-detection-and-recovery/))와도 일치 → hallucination 아님, 적절한 요약.
- §5 "BFD-RS 종류(SSB / CSI-RS) × UE 종류(일반 / RedCap) × 주파수(FR1 / FR2/FR2-1)별로 별도 평가 기간 변수와 표를 정의" — 3개 chunk(38.133-8.18.2.2-001 / 8.5B.2.2-001 / 8.5D.3.2-001)에서 직접 도출되는 사실. 정확.

---

## Coverage 누락

사용자 질문 6개 항목별:

| 항목 | 충족도 | 비고 |
|---|:---:|---|
| 도입 배경/필요성 | ✅ Full | R1-1707606/R1-1713597/R2-1803196 + Rel-15→16→18 진화 명시 |
| 38.213 PHY 절차 | ⚠️ Partial | q0/q1 자원 정의는 정확 인용. 그러나 핵심 정의 — *Q_out,LR이 가상 PDCCH BLER 10%로 정의됨* — 미답 (chunk score 0.33로 회수 부족 명시) |
| 38.321 MAC 절차 | ✅ Mostly Full | §5.17 BFR procedure + §5.1.4 BFR PRACH + ra-ResponseWindow 모두 인용. 누락: BFI_COUNTER 만기 reset 메커니즘 — chunk score 낮아 미답 |
| 38.331 RRC parameter | ⚠️ Partial | `BeamFailureRecoveryRSConfig` IE는 R2-2407883 통해 부분 인용. 핵심 누락: §6.3 `BeamFailureRecoveryConfig` IE의 ASN.1 enumerated 범위 (`n1~n10`, `pbfd1~pbfd10`, `sl1~sl80`). 1차가 §"커버리지 한계"에서 RAN1 Phase-7 IE-vs-절차 임베딩 한계와 동일 양상이라 명시 — 시스템적 한계 |
| 38.133 RRM 요구사항 | ⚠️ Partial | 변수명·구조·FR1/FR2 분기 정확. 표 row의 ms 절대값은 preview 컷오프로 미인용 |
| 38.533 시험 | ✅ Mostly Full | EN-DC/NR SA, FR1/FR2, PCell/PSCell, DRX 분기 + 시험 케이스 KG 노드 모두 인용. 누락: 시험 tolerance 정량값 (FFS 마커로 spec 자체가 미완성) — 책임 회피 아님 |
| 문서간 연결고리 | ✅ Full | 5개 명시적 연결 + 시퀀스 다이어그램 + 워크플로우 도식. 우수 |

**핵심 누락 1건**: Q_out,LR / Q_in,LR의 BLER 10% / 2% 정의 — 권위 출처에서 매우 명확하고 38.213 §5/§6에 본문이 존재. 1차 답변은 retrieve된 chunk text (38.213-5-001) 내부에 들어있을 가능성에도 깊이 파고들지 않음. spec-trace 검색 엔진의 임베딩 의미공간이 "Q_out / Q_in 정의"에 약하게 매칭됨이 시스템 개선 대상.

---

## 권위 소스 핵심 사실 vs 1차 답변

1. **BFR 도입 (Rel-15)** — 권위 소스(Justia patent, RAN1 agreement)는 NR Rel-15 RAN1 #88bis/#89/AdHoc#2에서 채택. **1차 답변**: R1-1707606 (Rel-15), R1-1713597, R1-1717606 (RAN1 #90b)으로 구체 인용. 일치 ✅.

2. **38.213 §6 BFD/BFR PHY** — 권위 소스: Q_out,LR (BLER 10%, DCI 1_0 + CCE aggregation 8, 2-symbol CORESET), Q_in,LR (BLER 2%, DCI 1_0 + CCE aggregation 4). q0 (BFD-RS), q1 (candidate beam RS). **1차 답변**: q0/q1 자원 정의는 chunk verbatim 인용 ✅. BLER 정량값 미인용 ⚠️ (의도적 — chunk 매칭 약함을 정직 보고).

3. **38.321 §5.17 BFR MAC** — 권위 소스(TechSpec): "Beam failure is detected by counting beam failure instance indication from lower layers... if BFI_COUNTER >= beamFailureInstanceMaxCount, RA is triggered". **1차 답변**: chunk verbatim 인용 ✅. BFI_COUNTER 만기 분기는 §6.1.3.30 chunk score 낮아 미답.

4. **SCell BFR (Rel-16)** — 권위 소스(Justia patent #11,909,488, RAN1/RAN2 agreement): SCell BFR은 BFR MAC CE 전송으로 동작 (PCell/PSCell의 PRACH 방식과 다름). **1차 답변**: R2-1900212 Rel-16 도입 동기 인용 + §3 KG 노드에 `38.321-6.1.3.23 BFR MAC CEs`, `38.321-6.1.3.43 Enhanced BFR MAC CEs` 명시 ✅. SCell BFR이 PRACH 대신 MAC CE를 쓴다는 차이점은 본문에서 명시적 설명 없음 ⚠️ (KG 노드명에서 추론 가능).

5. **38.133 RRM 측정 시간** — 권위 소스: TS 38.133 §8.18.2.2 표 8.18.2.2-1/-2가 ms 단위 row 보유. FR1/FR2/FR2-1 차이. **1차 답변**: 변수명·N 값(2,4,6)·구조 정확 ✅. ms row 절대값 미인용 ⚠️ (preview 컷오프).

---

## 종합 판정

- **신뢰 가능 영역 (그대로 사용 가능)**:
  - 절차/이름/IE/관계
  - BFR 시퀀스 다이어그램
  - 문서간 연결고리 (특히 38.331↔38.321 IE-procedure linkage)
  - Release 진화 (Rel-15 PCell/PSCell BFR → Rel-16 SCell BFR → Rel-17/18 강화)
  - q0/q1 자원, contention-free PRACH, ra-ResponseWindow
  - 38.133 평가 기간 변수 체계 (SSB/CSI-RS × 일반/RedCap × FR1/FR2/FR2-1)
  - 38.533 시험 케이스 분기 구조

- **부분 신뢰 영역 (재검색 후 보강 필요)**:
  - 38.331 IE ASN.1 enumerated 범위 (`n1~n10`, `pbfd1~pbfd10`, `sl1~sl80`) — 권위 소스에는 명확
  - SCell BFR이 PRACH 대신 MAC CE 사용한다는 동작 차이 — 1차 답변은 KG 노드명만 표기

- **미흡 영역 (정량값)**:
  - Q_out,LR / Q_in,LR BLER 임계값 (10% / 2%) — 사용자 질문이 명시적으로 요구
  - 38.133 표 8.18.2.2-1 / 8.5B.2.2-1 / 8.5D.3.2-1 ms 절대값
  - 38.533 시험 tolerance (spec 자체가 FFS — 책임 분리 가능)

**1차 답변 평가**: spec-trace의 "검색기에서 실제 회수한 사실만 인용" 원칙을 모범적으로 준수. citation integrity 16/16, hallucination 0건이 결정적 강점. 단점은 시스템적 — 정량값을 다루는 chunk가 검색기에서 정확히 retrieve되지 않은 것이지, LLM이 이를 채워넣지 않은 것은 정직성 측면에서 만점.

---

## 시스템 개선 권고 (RAG 측면)

1. **Chunk preview 컷오프 확장**: 현재 600자(`text_preview` / `content_preview`) → 2000자. 38.133 표 8.18.2.2-1 같은 ms row가 chunk 본문에 들어있으나 preview에서 잘림 → 답변 가능한 사실을 "미답"으로 처리하는 false negative. log 파일이 커지더라도 정확성 우선.

2. **38.533 FFS 마커 청크 필터링 또는 메타데이터 플래그**: §7.5.6.1.2 같은 chunk가 *Editor's note: incomplete, FFS* 마커를 포함. retrieval에서 우선순위 낮추거나 별도 `is_ffs_placeholder=true` 메타데이터로 마킹. 현재는 top-1 hit이 FFS chunk라서 답변에 정량 인용 불가.

3. **38.331 ASN.1 IE 별도 청킹**: §6.3 IE 정의는 본문(§5 절차)과 임베딩 의미공간이 다름 (RAN1 Phase-7 한계와 동일). IE chunk를 `chunk_type=asn1_ie`로 표기 + IE-name 키워드를 임베딩 텍스트 앞단에 명시적 prefix 처리 (예: "IE BeamFailureRecoveryConfig: ..."). enumerated 범위 (`n1, n2, ...`) 매칭 가능.

4. **38.213 §6 BLER 정의 chunk 임베딩 보강**: 권위 소스 일치 사실이 spec-trace에서 top score 0.33으로 회수된 점은 임베딩 품질 문제. "hypothetical PDCCH BLER" 같은 키워드를 chunk 메타데이터로 추가하거나, sub-section level로 더 잘게 청킹.

5. **TDoc citation 누락 풀텍스트 호출 옵션**: chunk_id가 retrieve되었으나 600자에 핵심 본문이 없는 경우, 답변 단계에서 해당 chunk의 full text를 별도 API 콜로 가져오는 fallback. 1차 답변이 §6.1.3.30 chunk를 "in this excerpt" 표기로 회피한 사례를 자동 보강.

6. **Cross-spec 연결 cypher 강화**: 현재 KG에 38.331 IE → 38.321 §5.17 같은 명시적 `REFERENCES_CLAUSE` 관계가 약함 (1차 답변이 "KG는 절(clause) 단위, IE 단위 노드 없음" 명시). IE→Procedure 직접 edge를 phase-3/4에서 추출.

---

## 약점 원인 분류 (D / O / R)

> **D**: 3GPP 데이터 자체의 시점·완결성 한계 — 시간이 해결
> **O**: KG/온톨로지 모델링 부재 — 스키마 보강 필요
> **R**: VDB 구축 단계의 chunking·embedding·indexing 한계 — 빌드 파이프라인 보강 필요

| # | 약점 | D / O / R | 근거 | 개선 가능성 |
|---|---|:---:|---|---|
| 1 | 38.213 Q_out,LR / Q_in,LR BLER 정량값 (10% / 2%) 미회수 | **R** | 38.213 §6 BFD 정의 chunk가 600자 preview 컷오프로 BLER 임계값 본문이 잘림. dense retrieval로 chunk가 회수되더라도 본문에 "10%"/"2%" 노출 안 됨. 임베딩 품질 문제도 부분 (top score 0.33). | 高 — preview 컷오프 600 → 2000자 확장 |
| 2 | 38.331 `beamFailureInstanceMaxCount` (n1~n10) / `beamFailureDetectionTimer` (pbfd1~pbfd10) enumerated 범위 본문 미회수 | **R + O** | (R) 38.331 IE block이 sectionTitle과 분리되지 않아 IE 본문 dense retrieval 약함. (O) `RRCParameter` 라벨이 IE를 분리 모델링하지 않아 graph 우회도 불가. | 高 — IE 단위 chunking + KG IE 노드 |
| 3 | 38.321 `BFI_COUNTER` 만기 분기 / SCell BFR이 PRACH 대신 MAC CE 사용 | **R + O** | (R) 38.321 §5.17 SCell BFR은 절(clause) 단위 chunk이지만 본문 발췌 부족. (O) MAC CE 6.1.3.x를 BFR procedure 노드와 연결하는 cross-clause edge 미모델링. | 中 — IE→Procedure REFERENCES_CLAUSE edge 추가 |
| 4 | 38.133 표(8.18.x / 8.5B.x / 8.5D.x) ms 정량값 행 단위 미회수 | **R** | (R) 38.133 RRM 표가 표 행 단위 chunking 안 됨. preview 컷오프로 ms 절대값 본문이 잘림. | 高 — table-row chunking + preview 확장 |
| 5 | 38.533 BFR test tolerance 정량값 미회수 (FFS 마커 포함) | **D + R** | (D) 38.533 V18.x 일부 절이 *FFS / Editor's note: incomplete* 표기로 3GPP 원본 자체가 미완. (R) FFS 마커 chunk 필터링 없음. | (D 부분 시간 해결) + (R 필터링 보강) |
| 6 | BFR 도입 RP-WID 본문 직접 인용 불가 | **R** | RP-* TDoc 별도 컬렉션 미적재. discussion이 RP-* reference 형태로 우회. | 中 — `ranX_rp_tdocs` 컬렉션 신설 |
| 7 | KG에 IE → procedure clause 직접 edge 부재 | **O** | KG는 절(clause) 단위 노드만, IE 단위 노드 부분 존재. `BeamFailureRecoveryConfig` IE → 38.321 §5.17 같은 명시적 `REFERENCES_CLAUSE` 관계 약함. | 中 — phase-3/4에서 IE→Procedure edge 추출 |
| 8 | BFR 절차 흐름 / 파라미터 변수명 / cross-doc 연결고리 | **(없음)** | 데이터 한계 없음 — 절차/이름은 retrieved-grounded로 인용 정확. | (D 책임 0) |

**합계**: D 1건 부분(#5 38.533 FFS), R 3건, R+O 2건, O 1건, D+R 1건. **시스템(R/O) 책임이 다수**, 38.533 FFS 마커는 3GPP 원본 자체 미완(D)이지만 그것 외에 정량값 모두 시스템 한계.

**개선 우선순위**:
1. (P1, R) chunk preview 600자 → 2000자 확장 — Q3 정량값 + Q4 LTM timer 공통 해소
2. (P1, R+O) 38.331 IE 단위 chunking + KG IE 노드 — Q1/Q2/Q3/Q4 공통
3. (P1, R) 38.133 RRM 표 행(row) 단위 chunking — ms 절대값 인용 가능
4. (P2, R) FFS 마커 chunk 필터링 — 38.533 spec quality gate
5. (P2, O) IE→Procedure `REFERENCES_CLAUSE` edge 추출 — graph-RAG 강화
6. (P2, R) RP-WID 별도 컬렉션 신설
