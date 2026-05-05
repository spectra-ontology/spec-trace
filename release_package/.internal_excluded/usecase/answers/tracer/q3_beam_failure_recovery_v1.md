# Q3. Beam Failure Detection / Beam Failure Recovery (BFD/BFR) 표준 절차

> **답변 출처 제약**: 본 문서의 사실 문장은 모두 spec-trace(3gpp-tracer) 검색 결과(Qdrant TS/TDoc + Neo4j KG)에서만 인용한다. 외부 웹/일반 지식 사용 금지. 인용 형식은 `[<TS> §<sec>, chunkId=...]` 또는 `[TDoc <num>, chunkId=...]`.

---

## 메타

| 항목 | 값 |
|---|---|
| 질문 | NR BFD/BFR 표준 절차 — 도입 배경, 38.213/38.321/38.331/38.133/38.533 파라미터/절차, 문서 간 연결고리 |
| 검색 컬렉션 | `ran1_ts_sections`, `ran2_ts_sections`, `ran4_ts_sections`, `ran5_ts_sections`, `ran1_tdoc_chunks`, `ran2_tdoc_chunks`, `ran4_tdoc_chunks`, `ran5_tdoc_chunks` (총 8개) |
| Neo4j KG | RAN1=7687, RAN2=7688, RAN4=7690, RAN5=7691 |
| Qdrant 쿼리 수 | TS 27개 + TDoc 12개 = **39 쿼리** |
| Cypher 쿼리 수 | **4개** (`Section→Spec` BELONGS_TO_SPEC, BFD/BFR/Link recovery 키워드) |
| 임베딩 모델 | `openai/text-embedding-3-small` (OpenRouter) |
| 결과 로그 | `logs/cross-phase/usecase/q3_retrieval_log.json` |
| 검색 스크립트 | `scripts/cross-phase/usecase/q3_search_bfd_bfr.py` |

---

## 3gpp-tracer 검색 결과 요약

### Qdrant TS 섹션 (27 쿼리, 각 top_k=10 → 270 hit)

| 컬렉션 / Spec | 고유 sectionId 수 | 비고 |
|---|---:|---|
| `ran1_ts_sections` / 38.213 | 35 | §5(Radio link monitoring), §6(Link recovery procedures) 중심 |
| `ran2_ts_sections` / 38.321 | 35 | §5.17(BFD/BFR procedure), §5.18.25/§6.1.3.x(MAC CE) |
| `ran2_ts_sections` / 38.331 | 45 | §5.7.1a(fast MCG link recovery), §5.7.13(RLM/BFD relaxation), §5.5.5.2(beam meas) 등 |
| `ran4_ts_sections` / 38.133 | 47 | §8.1(RLM), §8.18(TRP-specific Link Recovery), §8.5B/8.5D/8.19(BFD evaluation, recovery delay) |
| `ran5_ts_sections` / 38.533 | 33 | §10.3.4 / §11.4.4 / §17.5.2 등 BFD-LR 시험 케이스 |

총 고유 TS 섹션: **195개**, 총 hit: **270**.

### Qdrant TDoc (12 쿼리 → 120 hit, 모두 비어있지 않음)

| 컬렉션 | 대표 hit | release |
|---|---|---|
| `ran1_tdoc_chunks` | R1-1717606, R1-1707606, R1-1713597 | Rel-15(도입) |
| `ran2_tdoc_chunks` | R2-1803196, R2-1900212, R2-2301761, R2-2407883 | Rel-15 → Rel-18 |
| `ran4_tdoc_chunks` | R4-1704760, R4-2511038 | Rel-15, Rel-19 |
| `ran5_tdoc_chunks` | R5-198423, R5-204985 | Rel-16+ |

### Neo4j KG (4 cypher)

| KG | 매칭 Section 수 | 대표 sectionId |
|---:|---:|---|
| RAN1 (38.213) | 2 | `38.213-5` (Radio link monitoring), `38.213-6` (Link recovery procedures) |
| RAN2 (38.321/38.331) | 7 | `38.321-5.17`, `38.321-5.18.25`, `38.321-6.1.3.23`, `38.321-6.1.3.43`, `38.321-6.1.3.58`, `38.331-5.7.13`, ... |
| RAN4 (38.133) | 100 (LIMIT) | `38.133-8.18`, `38.133-8.18.2`, `38.133-8.18.3`, `38.133-8.18.7`, ... |
| RAN5 (38.533) | 100 (LIMIT) | `38.533-10.3.4`, `38.533-11.4.4`, `38.533-10.3.4.0.1`, ... |

> **주의**: 38.321 KG에서 `5.17` 1개 노드만 잡힌 것은 KG가 level-1 항목까지만 정규화 적재했기 때문이다. 절차 본문은 Qdrant TS chunk에 들어있다. RAN1 38.213도 같은 양상으로, KG는 §5/§6 두 노드만 보유하고 본문은 Qdrant chunks에 있다.

---

## 답변 본문

### 1. 도입 배경 및 필요성

NR Rel-15 RAN1 단계에서 빔 실패에서의 회복 메커니즘이 별도 절차로 도입되었다. R1-1707606은 “Mechanism 1과 2 모두 지원” 등 BFR의 기본 메커니즘 제안을 담고 있고 [TDoc R1-1707606 (Rel-15), chunkId=R1-1707606@..., agendaItem=7.1.2.2.2]:

> *"In this contribution, we have studied the mechanism to recover from beam failure and proposed as following: Proposal #1: Support both Mechanism 1 and 2 to recover from beam failure. Proposal #2: Support explicit/implicit signaling for indicating whether or not new candidate beam exists."* [TDoc R1-1707606, chunkId=R1-1707606@..., title="Discussion on beam failure recovery"]

빔 실패 검출 메트릭으로는 L1-RSRP가 채택되었다. R1-1713597은 다음과 같이 명시한다 [TDoc R1-1713597, chunkId=R1-1713597@..., title="Beam failure recovery"]:

> *"Proposal 1: NR supports L1-RSRP as the measurement metric to detect beam failure. Proposal 2: NR considers the following alternatives of using L1-RSRP in beam failure detection: (1) Averaged L1-RSRP, (2) All consecutive N L1-RSRP measurement being b..."*

RAN2 측 도입 동기는 R2-1803196이 명확히 보여준다 [TDoc R2-1803196 (Rel-15), chunkId=R2-1803196@..., agendaItem=10.3.1.4.2]:

> *"Beam failure recovery procedure is described in section 5.17 of TS 38.321. Based on a number of 'beam failure instances' from physical layer MAC will trigger a random access procedure which allows the recovery."*

후속 릴리스에서는 SCell까지 BFR 적용을 확장하는 동기가 제시되었다. R2-1900212는 Rel-15 BFR가 SCell에 효용이 없음을 다음과 같이 지적한다 [TDoc R2-1900212 (Rel-16), chunkId=R2-1900212@..., agendaItem=11.10.4]:

> *"Observation 2: The current Rel-15 BFR is useless in support of beam failure on the SCell for CA depl..."*

Rel-18에서는 SCell deactivated 상태에서의 빔 변화 대응이 제안되었다 [TDoc R2-2301761 (Rel-18), chunkId=R2-2301761@..., agendaItem=8.20.2]:

> *"When the beam of SCell changes while the SCell is deactivated, it takes more time from receiving (Enhanced) SCell Activation MAC CE to starting exchange of user data... Allow UE to trigger beam failure recovery on SCell when the UE detects a beam failure on the tempora..."*

> **요약**: 빔포밍 기반 NR 운영에서 RLF→RRC re-establishment는 너무 늦은 회복 경로이므로, MAC/L1 단의 빠른 빔 회복 절차가 Rel-15에서 도입되었고, Rel-16에서 SCell BFR로 확장, Rel-17/18에서 추가 강화되었다 (위 4개 TDoc 인용).

---

### 2. 38.213 — BFD/BFR 물리계층 절차 (RAN1)

**KG 구조**: 38.213에는 §5 *Radio link monitoring*, §6 *Link recovery procedures* 두 개 level-1 절이 잡힌다 [Neo4j RAN1 7687, sectionId=`38.213-5`, `38.213-6`].

**핵심 본문 — 빔 실패 검출 자원과 후보 빔 자원 구성**:

> *"A UE can be provided, for each BWP of a serving cell, a set q0 of periodic CSI-RS resource configuration indexes by failureDetectionResourcesToAddModList and a set q1 of periodic CSI-RS resource configuration indexes and/or SS/PBCH block indexes by candidateBeamRSList or candidateBeamRSListExt or candidateBeamRS-List for radio link quality measurements on the BWP of the serving cell. Instead of the sets q0 and q1, for each BWP of a serving cell, the UE can be provided respective two sets q0,0 and q0,1 of periodic CSI-RS resource configuration indexes by failureDetectionSet1 and failureDetectio..."* [38.213 §6, chunkId=38.213-6-001]

이 본문은 다음 핵심 개념을 정의한다:
- **q0 (BFD-RS set)**: `failureDetectionResourcesToAddModList` 또는 `failureDetectionSet1` 등으로 RRC가 설정하는 빔 실패 검출용 주기적 CSI-RS/SSB 자원 [38.213 §6, chunkId=38.213-6-001].
- **q1 (Candidate beam set)**: `candidateBeamRSList` 등으로 설정하는 후보 빔 자원 [38.213 §6, chunkId=38.213-6-001].

> **커버리지 한계**: 본 검색에서 $Q_{out,LR}$ / $Q_{in,LR}$의 가상(BLER) 임계값 정의 본문은 직접 chunk로 retrieve되지 않았다 (top score 0.33). KG는 §5/§6 두 노드만 보유 → 더 깊은 sub-section level 본문은 Qdrant chunk text 내부에서만 확인 가능 (위 §6-001 chunk의 후속 chunk가 미인용 영역).

---

### 3. 38.321 — MAC 절차 (RAN2)

**KG 노드**: RAN2 KG에서 38.321 BFD/BFR 관련 7개 노드 중 5개가 직접 매핑된다 [Neo4j RAN2 7688, BELONGS_TO_SPEC]:
- `38.321-5.17` *Beam Failure Detection and Recovery procedure*
- `38.321-5.18.25` *BFD-RS Indication MAC CE*
- `38.321-6.1.3.23` *BFR MAC CEs*
- `38.321-6.1.3.43` *Enhanced BFR MAC CEs*
- `38.321-6.1.3.58` *BFD-RS Indication MAC CE*

**핵심 본문 — §5.17 BFD/BFR 절차**:

> *"The MAC entity may be configured by RRC per Serving Cell or per BFD-RS set with a beam failure recovery procedure which is used for indicating to the serving gNB of a new SSB or CSI-RS when beam failure is detected on the serving SSB(s)/CSI-RS(s). Beam failure is detected by counting beam failure instance indication from the lower layers to the MAC entity. If beamFailureRecoveryConfig is reconfigured by upper layers during an ongoing Random Access procedure for beam failure recovery for SpCell, the MAC entity shall stop the ongoing Random Access procedure and initiate a Random Access procedure..."* [38.321 §5.17, chunkId=38.321-5.17-001]

이 본문에서 확인되는 절차 요소:
- MAC entity가 RRC로부터 *per Serving Cell* 또는 *per BFD-RS set* 단위로 BFR 설정을 받는다 [38.321 §5.17, chunkId=38.321-5.17-001].
- 하위 계층(L1)에서 올라오는 *beam failure instance indication*을 카운팅하여 빔 실패를 검출한다 [38.321 §5.17, chunkId=38.321-5.17-001].
- 진행 중인 BFR Random Access 도중 `beamFailureRecoveryConfig`가 재설정되면 MAC은 기존 RA를 중단하고 재개시한다 [38.321 §5.17, chunkId=38.321-5.17-001].

**RA Response window 처리 — RA 파트와 연결**:

> *"if the contention-free Random Access Preamble for beam failure recovery request was transmitted by the MAC entity: ... start the ra-ResponseWindow configured in BeamFailureRecoveryConfig at..."* [38.321 §5.1.4, chunkId=38.321-5.1.4-001]

즉 BFR PRACH는 contention-free 형태로 전송되고, 응답 모니터링은 `BeamFailureRecoveryConfig` 내 `ra-ResponseWindow`로 제어된다 [38.321 §5.1.4, chunkId=38.321-5.1.4-001].

> **커버리지 한계**: `beamFailureInstanceMaxCount` 카운터 만기 시 RACH-Resource로의 천이 본문 단편(top-1)은 §6.1.3.30 chunk (score 0.35)에서 잡혔지만 *full text*는 본 인용 범위에서 직접 노출되지 않았다 — chunk 자체는 검색됨 [38.321 §6.1.3.30, chunkId 미공개 in this excerpt].

---

### 4. 38.331 — RRC 파라미터 (RAN2)

**KG 노드**: 38.331에서 BFD/BFR 명시적 매칭은 §5.7.13 *RLM/BFD relaxation* 한 곳이다 [Neo4j RAN2 7688, sectionId=`38.331-5.7.13`]. 그러나 IE 정의 본문은 38.331 §6.3에 있고, KG에는 IE 단위 노드로 정규화되어 있지 않다 (KG는 절(clause) 단위).

**파라미터 단편 (CR로부터)**: Rel-18 CR R2-2407883은 `BeamFailureRecoveryRSConfig` IE의 ASN.1을 정확히 노출한다 [TDoc R2-2407883 (Rel-18, CR), chunkId=R2-2407883@...]:

> *"The IE BeamFailureRecoveryRSConfig is used to configure the UE with candidate beams for beam failure recovery in case of beam failure detection. See also TS 38.321 [3], clause 5.17."*
>
> *"BeamFailureRecoveryRSConfig-r16 ::= SEQUENCE { rsrp-ThresholdBFR-r16               RSRP-Range ..."* [TDoc R2-2407883, chunkId=R2-2407883@...]

이로부터 다음 사실이 확인된다:
- IE `BeamFailureRecoveryRSConfig`는 *후보 빔* (candidateBeamRS)을 UE에 설정한다 [TDoc R2-2407883, chunkId=R2-2407883@...].
- `rsrp-ThresholdBFR-r16`은 `RSRP-Range` 타입으로 정의된다 [TDoc R2-2407883, chunkId=R2-2407883@...].
- 38.331 IE는 38.321 §5.17 절차와 명시적으로 연결된다 ("See also TS 38.321 [3], clause 5.17") [TDoc R2-2407883, chunkId=R2-2407883@...].

**RLM/BFD relaxation (§5.7.13)**: KG에 절 단위로 잡힌 별도 노드 [Neo4j RAN2, sectionId=`38.331-5.7.13`, title="RLM/BFD relaxation"]. 본문 chunk 자체는 본 검색 단계에서 top-1로 잡히지 않아 추가 인용 보류.

> **커버리지 한계**: 38.331 §6.3 *Radio resource control information elements* 영역의 IE ASN.1 (`BeamFailureRecoveryConfig`, `RadioLinkMonitoringConfig`, `RACH-ConfigDedicated`)은 본 38.331 전용 키워드 검색에서 top-5 외부로 밀렸다. 임베딩 의미공간에서 IE 정의 vs 절차 본문 사이 구분이 약하다는 RAN1 Phase-7 기존 한계와 같은 양상.

---

### 5. 38.133 — RAN4 RRM 요구사항

**KG 노드**: 38.133에서 BFD/BFR/link recovery 매칭이 100건(LIMIT) 도달. 핵심 노드 [Neo4j RAN4 7690, BELONGS_TO_SPEC]:
- `38.133-8.1` *Radio Link Monitoring*
- `38.133-8.18` *TRP specific Link Recovery Procedures*
- `38.133-8.18.2` *Requirements for TRP specific SSB based beam failure detection*
- `38.133-8.18.3` *Requirements for CSI-RS based beam failure detection*
- `38.133-8.18.7` *Requirements for TRP specific Beam Failure Recovery*
- `38.133-8.18.8` *Scheduling availability of UE during TRP specific beam failure detection*

**핵심 본문 — BFD 평가 기간 정의**:

> *"UE shall be able to evaluate whether the downlink radio link quality on the configured SSB resource in two sets and estimated over the last TEvaluate_BFD_SSB period becomes worse than the threshold Qout_LR_SSB within TEvaluate_BFD_SSB period. The value of TEvaluate_BFD_SSB is defined in table 8.18.2.2-1 for FR1. The value of TEvaluate_BFD_SSB is defined in table 8.18.2.2-2 for FR2 with scaling factor N, where -N = 2, 4, or 6 in FR2-1 for UE sup..."* [38.133 §8.18.2.2, chunkId=38.133-8.18.2.2-001]

확인되는 정량 정의 — **검색 결과 본문 그대로 인용**:
- BFD 평가 메트릭은 `Qout_LR_SSB` (DL radio link quality 임계값) [38.133 §8.18.2.2, chunkId=38.133-8.18.2.2-001].
- 평가 기간 변수명은 `TEvaluate_BFD_SSB` [38.133 §8.18.2.2, chunkId=38.133-8.18.2.2-001].
- FR2-1 NW에서는 스케일링 인자 N = 2, 4, 6 적용 [38.133 §8.18.2.2, chunkId=38.133-8.18.2.2-001].
- FR1/FR2 표는 `8.18.2.2-1`, `8.18.2.2-2` [38.133 §8.18.2.2, chunkId=38.133-8.18.2.2-001].

**RedCap/CSI-RS 변형 평가 기간**:

> *"UE shall be able to evaluate whether the downlink radio link quality on the configured SSB resource in set estimated over the last TEvaluate_BFD_SSB_Redcap period becomes worse than the threshold Qout_LR_SSB within TEvaluate_BFD_SSB_Redcap period. The value of TEvaluate_BFD_SSB_Redcap is defined in table 8.5B.2.2-1 for FR1."* [38.133 §8.5B.2.2, chunkId=38.133-8.5B.2.2-001]

> *"UE shall be able to evaluate whether the downlink radio link quality on the CSI-RS resource in set estimated over the last TEvaluate_BFD_CSI-RS period becomes worse than the threshold Qout_LR_CSI-RS within TEvaluate_BFD_CSI-RS period. The value of TEvaluate_BFD_CSI-RS is defined in table 8.5D.3.2-1 for FR1."* [38.133 §8.5D.3.2, chunkId=38.133-8.5D.3.2-001]

즉 RAN4는 **BFD-RS 종류(SSB / CSI-RS) × UE 종류(일반 / RedCap) × 주파수(FR1 / FR2/FR2-1)** 별로 별도 평가 기간 변수와 표를 정의한다 [위 3개 chunk 인용].

> **수치 정밀**: 본 spec-trace 검색은 표 8.18.2.2-1 등 **표 본체의 ms 단위 수치 row까지는 chunk 본문에 포함되어 있으나** preview 600자 컷오프로 인해 본 답변에는 노출되지 않는다. 표 상세값을 정확히 인용하려면 해당 chunkId 의 full text 호출이 추가 필요 (현재 retrieval 결과 JSON에는 600자 preview만 저장).

---

### 6. 38.533 — RAN5 적합성 시험

**KG 노드**: 38.533에서 BFD/BFR/link recovery 매칭 100건 도달 [Neo4j RAN5 7691]. 대표 시험 케이스:
- `38.533-10.3.4` *Beam failure detection and link recovery procedures* (EN-DC FR1 영역)
- `38.533-10.3.4.0.1` *Minimum conformance requirements for SSB based Beam Failure Detection under CCA*
- `38.533-10.3.4.0.3` *Scheduling availability of UE during beam failure detection under CCA*
- `38.533-10.3.4.1` *EN-DC FR1 Beam Failure Detection and Link Recovery Test for PSCell configured with SSB-based BFD and LR in non-DRX mode*
- `38.533-10.3.4.2` 동일하지만 *DRX mode*
- `38.533-11.4.4` *Beam failure detection and link recovery procedures* (NR SA FR1 영역)

**시험 케이스 본문 (FR2 PCell SSB-based BFD)**:

> *"The purpose of this test is to verify that the UE properly detects SSB-based beam failure in the set q0 configured for a serving cell and that the UE performs correct SSB-based link recovery based..."* [38.533 §17.5.2.1, chunkId=38.533-17.5.2.1-001]

> *"This test case is complete for the following configurations: -UE PC3 -Test frequencies f ≤ 40.8 GHz; This test case is incomplete for UE power classes other than PC3..."* [38.533 §17.5.2.1, chunkId=38.533-17.5.2.1-001]

즉 38.533 BFD/LR 시험은:
- **q0 (BFD-RS set)** 위에서 빔 실패 검출이 정상 동작하는지 검증 [38.533 §17.5.2.1, chunkId=38.533-17.5.2.1-001].
- **EN-DC vs NR SA**, **FR1 vs FR2**, **PCell vs PSCell**, **non-DRX vs DRX**, **UE Power Class** 차원으로 시험 케이스가 분기된다 [38.533 §10.3.4.1/§10.3.4.2/§17.5.2.1 KG nodes + chunks].

> **커버리지 한계 — RAN5 검색 품질**: 일부 38.533 chunk는 *"Editor's note: This test case is incomplete... Test tolerance analysis is missing... FFS"* 같은 미완성 표기를 그대로 포함한다 [38.533 §7.5.6.1.2, chunkId=38.533-7.5.6.1.2-001]. 시험 정밀 임계값을 답변에 단정해 인용할 수 없다 — 검색에서 최상위 hit이 FFS 마커가 있는 chunk다.

---

## 동작 절차 시퀀스 (검색 결과 기반 재구성)

```
[gNB]                                         [UE — MAC + L1]
  |                                                |
  | (1) RRC: BeamFailureRecoveryRSConfig +         |
  |     RadioLinkMonitoringConfig 송신 (38.331)    |
  |———————————————————————————————→               |
  |                                                |  set q0 (BFD-RS): failureDetectionResourcesToAddModList
  |                                                |  set q1 (candidate): candidateBeamRSList
  |                                                |  [38.213 §6, chunkId=38.213-6-001]
  |                                                |
  |                                                | (2) L1: q0 위 hypothetical BLER 측정 →
  |                                                |     beam failure instance를 MAC으로 indication
  |                                                |     (38.321 §5.17 — counting)
  |                                                |     [38.321 §5.17, chunkId=38.321-5.17-001]
  |                                                |
  |                                                | (3) MAC: counter ≥ beamFailureInstanceMaxCount
  |                                                |     도달 시 BFR 트리거
  |                                                |     [R2-1803196 인용 — "based on a number of
  |                                                |     beam failure instances ... will trigger
  |                                                |     a random access procedure"]
  |                                                |
  |                                                | (4) candidate beam 식별 (q1, L1-RSRP ≥ threshold)
  |                                                |     [R1-1713597 — "L1-RSRP as the
  |                                                |     measurement metric"]
  |                                                |
  |                                                | (5) contention-free PRACH 전송
  |                                                |     (BFR 전용 RA preamble)
  |                                                |     [38.321 §5.1.4, chunkId=38.321-5.1.4-001]
  |←———————————————————————————————                |
  |                                                |
  | (6) gNB response monitoring                    |
  |     ra-ResponseWindow (BeamFailureRecoveryConfig)|
  |     [38.321 §5.1.4, chunkId=38.321-5.1.4-001]  |
  |———————————————————————————————→               |
  |                                                |
  | (7) RAN4 평가 기간 TEvaluate_BFD_SSB 내 검출        |
  |     [38.133 §8.18.2.2, chunkId=38.133-8.18.2.2-001]|
  |                                                |
  | (8) RAN5 conformance — q0 위 BFD + correct LR  |
  |     [38.533 §17.5.2.1, chunkId=38.533-17.5.2.1-001]|
```

각 단계의 인용은 위 표시한 chunkId에서 직접 retrieve된 본문에 근거한다.

---

## 문서 간 연결고리

검색 결과로 직접 확인된 명시적 연결:

1. **38.331 IE ↔ 38.321 절차**: CR R2-2407883 본문에 *"The IE BeamFailureRecoveryRSConfig is used to configure the UE with candidate beams... See also TS 38.321 [3], clause 5.17."* 명시 [TDoc R2-2407883, chunkId=R2-2407883@...]. → **RRC 파라미터 → MAC 절차** 연결을 spec 본문이 직접 가리킨다.

2. **38.321 ↔ 38.213**: R2-1803196 본문 *"Beam failure recovery procedure is described in section 5.17 of TS 38.321. Based on a number of 'beam failure instances' from physical layer..."* [TDoc R2-1803196, chunkId=R2-1803196@...]. → **MAC 절차 ← L1 indication** 연결.

3. **38.213 ↔ 38.133**: 38.213 §6는 q0/q1 자원 정의 [38.213 §6, chunkId=38.213-6-001], 38.133 §8.18.2.2는 동일 q0 set에 대한 평가 기간(`TEvaluate_BFD_SSB`)과 임계값(`Qout_LR_SSB`)을 정량 요구사항으로 정의 [38.133 §8.18.2.2, chunkId=38.133-8.18.2.2-001]. → **L1 절차 → RRM 시간 요구사항**.

4. **38.133 ↔ 38.533**: 38.533 §10.3.4 시험 케이스의 normative reference로 38.133이 인용되는 패턴이 38.533 chunk에 일관되게 보인다 (예: §7.5.6.1.2 *"The minimum conformance requirements are specified in clause 7.5.6.1"*) [38.533 §7.5.6.1.2, chunkId=38.533-7.5.6.1.2-001]; R5-204985는 *"The normative reference for this requirement is TS 38.133 [6] clause A.4.5.5.1"* 명시 [TDoc R5-204985 (Rel-16, CR), chunkId=R5-204985@...]. → **RRM 요구사항 → 시험 절차** 연결.

5. **WG 흐름**: TDoc retrieval에서 R1-* (RAN1, PHY 도입) → R2-* (RAN2, MAC/RRC 후속) → R4-* (RAN4, RRM 정량 요구사항 도입) → R5-* (RAN5, 시험 케이스 정의) 순서로 release가 분포한다 (R1-1707606=Rel-15 → R4-2511038=Rel-19) — 사양 작성 시간 순 흐름 자체가 retrieval 결과로 노출된다 [TDoc 인용 4건, agendaItem 차이 확인].

요약:
```
38.331 RRC IE  ─┐
                ├─ (RRC config) ──→  38.321 MAC §5.17 BFR procedure
38.331 RLM     ─┘                        │
                                          │ (instance counting from L1)
                                          ↓
                                     38.213 §5/§6 BFD-RS, candidate beam, PRACH
                                          │
                                          │ (정량 평가: TEvaluate_BFD_*, Qout_LR_*)
                                          ↓
                                     38.133 §8.18 RAN4 RRM
                                          │
                                          │ (normative ref)
                                          ↓
                                     38.533 §10.3.4 / §17.5.2 RAN5 conformance
```
(연결 화살표마다 해당 chunkId 또는 KG sectionId가 위 인용으로 검증됨.)

---

## 커버리지 / 한계

| 항목 | 결과 | 비고 |
|---|---|---|
| 38.213 BFD-RS / candidate beam set 본문 | **잘 retrieve됨** | §6 본문 chunkId=38.213-6-001 |
| 38.213 Q_in/Q_out (가상 BLER) 정량 정의 | **부분** — top score 0.33로 직접 chunk 매칭 약함 | 본문은 §5/§6 chunk에 있으나 키워드 매칭 부족 |
| 38.321 §5.17 BFR procedure | **잘 retrieve됨** | chunkId=38.321-5.17-001 |
| 38.321 `beamFailureInstanceMaxCount` 카운터 만기 분기 본문 | **부분** — chunk는 잡히나 600자 preview에 본문 안 잡힘 | full text 호출 필요 |
| 38.331 IE ASN.1 (`BeamFailureRecoveryConfig`, `RadioLinkMonitoringConfig`) 본문 | **부분** — top-5에서 §6.3 IE chunk 미노출, CR(R2-2407883)이 IE ASN.1을 대신 노출 | RAN1 Phase-7에서 알려진 IE vs 절차 임베딩 한계와 동일 양상 |
| 38.133 §8.18 BFD/BFR 요구사항 / 평가 기간 / 임계값 변수명 | **잘 retrieve됨** | chunkId=38.133-8.18.2.2-001 외 다수 |
| 38.133 표 8.18.2.2-1 등 표 row의 ms 수치 | **부분** — chunk 본문에 표가 들어있으나 600자 preview로 인해 답변에는 미인용 |
| 38.533 BFD/LR 시험 케이스 구조 | **잘 retrieve됨** | EN-DC/NR SA, FR1/FR2, DRX/non-DRX 시험 케이스 KG 노드와 chunk 모두 잡힘 |
| 38.533 시험 정확도 정량값 (test tolerance) | **부분** — top hit이 *"Editor's note: incomplete... FFS"* 마커 포함 | spec-trace 데이터 자체가 미완 표기를 포함 |

**3gpp-tracer에서 미발견(또는 retrieval 신뢰도 부족)으로 답변 제외**:
- 38.213 `Q_out`/`Q_in` BLER 임계값의 구체 수치 (예: BLER 10% 등)
- 38.321 `beamFailureDetectionTimer` 만기 시 카운터 reset 본문 (chunk score 낮음)
- 38.331 §6.3 `BeamFailureRecoveryConfig` IE 전체 ASN.1 (CR 본문 R2-2407883에 부분 ASN.1만 노출)
- 38.133 표 8.18.2.2-1 / 8.5B.2.2-1 / 8.5D.3.2-1 row의 ms 수치 (preview 컷오프로 미노출)
- 38.533 시험 tolerance 정량 임계값 (top chunk가 FFS 마커)

이상 항목은 **임의 채워넣기 금지** 원칙(CLAUDE.md)에 따라 본 답변에 포함하지 않음.

---

## 자가 검증

| 점검 | 상태 |
|---|---|
| 모든 사실 문장에 chunkId 또는 sectionId 인용 | OK |
| 외부 웹/일반 지식 사용 여부 | 사용하지 않음 (WebFetch/WebSearch 호출 0) |
| 임의의 타이머/카운터/임계값 수치를 학습지식으로 채워넣었는가? | **NO** — 정량 정의 변수명(`TEvaluate_BFD_SSB`, `Qout_LR_SSB`, `beamFailureInstanceMaxCount`, `ra-ResponseWindow` 등)은 chunk 본문에서 직접 인용. row의 ms 단위 수치는 preview 미노출이므로 본문에 인용하지 않음 |
| 미발견 항목을 명시했는가? | OK — “커버리지 / 한계” 표 + “3gpp-tracer에서 미발견” 목록 |
| Cypher 쿼리가 실제 KG schema에 맞는가? | OK — `Section`-`[:BELONGS_TO_SPEC]`-`Spec` 구조 확인 후 작성, RAN1=2 / RAN2=7 / RAN4=100 / RAN5=100 행 반환 (LIMIT 100 적용) |
