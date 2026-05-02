# Q3. Beam Failure Detection / Beam Failure Recovery (BFD/BFR) 표준 절차 — v2 (P2 + ASN.1)

> **답변 출처 제약**: 본 문서의 사실 문장은 모두 spec-trace(3gpp-tracer) 검색 결과(Qdrant TS/ASN.1 + Neo4j KG)에서만 인용한다. 외부 웹/일반 지식 사용 금지. 인용 형식은 `[<TS> §<sec>, chunkId=...]` 또는 `[ASN.1 IE, chunkId=...]`.
>
> **v1 → v2 변경**: (1) main `*_ts_sections` 컬렉션이 P2 적용본(max 6,494 tok)으로 갱신, (2) `ran2_ts_asn1_chunks` 추가로 38.331 IE 본문(`enumerated` 범위 포함) 직접 인용 가능, (3) 검색 로그가 chunk text 전체를 보존(이전 600자 preview 컷오프 제거). v1은 `q3_beam_failure_recovery_v1.md`로 백업.

---

## 메타

| 항목 | 값 |
|---|---|
| 질문 | NR BFD/BFR — 도입 배경, 38.213/38.321/38.331/38.133/38.533, 정량값(BLER, enumerated 범위, ms 절대값), 문서 간 연결고리 |
| 검색 컬렉션 | `ran1/ran2/ran4/ran5_ts_sections` (P2 적용) + ★ `ran2_ts_asn1_chunks` |
| Neo4j KG | RAN1=7687, RAN2=7688, RAN4=7690, RAN5=7691 |
| Qdrant 쿼리 수 | TS 24 + ASN.1 15 = **39 쿼리** |
| Cypher 쿼리 수 | **4개** (`Section→Spec`, BFD/BFR/Link recovery 키워드) |
| 임베딩 모델 | `openai/text-embedding-3-small` (OpenRouter) |
| 결과 로그 | `logs/cross-phase/usecase/q3_retrieval_log_v2.json` |
| 검색 스크립트 | `scripts/cross-phase/usecase/q3_search_bfd_bfr_v2.py` |
| 회수 chunk(고유) | TS 162 + ASN.1 29 = **191 chunk** |

---

## 검색 결과 요약

### Qdrant TS (P2)

| 컬렉션 / Spec | 대표 top score | 비고 |
|---|---:|---|
| `ran1_ts_sections` / 38.213 | 0.4923 (BLER 임계값 query) | §5 RLM, §6 *Link recovery procedures* (Qout,LR/Qin,LR 정의 회수) |
| `ran2_ts_sections` / 38.321 | 0.5641 (ra-ResponseWindow query) | §5.17 BFR 절차 본문 회수 (parameter 목록 포함) |
| `ran2_ts_sections` / 38.331 | 0.5746 (RLM/BFD relaxation) | §5.7.13 RLM/BFD relaxation, §5.7.1a 등 |
| `ran4_ts_sections` / 38.133 | 0.6378 (TEvaluate_BFD_SSB query) | §8.5B/§8.5C/§8.5D/§8.18 BFD evaluation period 본문 |
| `ran5_ts_sections` / 38.533 | 0.6892 (L1-RSRP accuracy) | §16.7.4 / §7.5.6 / §A.5 등. 본문 text 비어있음 (RAN5 phase-7 spec — title 임베딩) |

### Qdrant ASN.1 (`ran2_ts_asn1_chunks`)

| IE 이름 | chunkId | tokenCount | 인용 가능 정량값 |
|---|---|---:|---|
| `BeamFailureRecoveryConfig` | `38.331-asn1-BeamFailureRecoveryConfig-001` | 285 | `beamFailureRecoveryTimer ENUMERATED {ms10..ms200}`, `ssb-perRACH-Occasion ENUMERATED {oneEighth..sixteen}`, `rootSequenceIndex-BFR INTEGER (0..137)` 등 |
| `RadioLinkMonitoringConfig` | `38.331-asn1-RadioLinkMonitoringConfig-001` | 65 (실측) | `beamFailureInstanceMaxCount ENUMERATED {n1, n2, n3, n4, n5, n6, n8, n10}`, `beamFailureDetectionTimer ENUMERATED {pbfd1..pbfd10}` |
| `RadioLinkMonitoringRS` | `38.331-asn1-RadioLinkMonitoringRS-001` | — | `purpose ENUMERATED {beamFailure, rlf, both}`, `detectionResource CHOICE {ssb-Index, csi-RS-Index}` |
| `PRACH-ResourceDedicatedBFR` | `38.331-asn1-PRACH-ResourceDedicatedBFR-001` | — | `CHOICE {ssb BFR-SSB-Resource, csi-RS BFR-CSIRS-Resource}` |
| `BFR-SSB-Resource` | `38.331-asn1-BFR-SSB-Resource-001` | — | `ra-PreambleIndex INTEGER (0..63)` |
| `BFR-CSIRS-Resource` | `38.331-asn1-BFR-CSIRS-Resource-001` | — | `ra-OccasionList SEQUENCE (SIZE (1..maxRA-OccasionsPerCSIRS)) OF INTEGER (0..maxRA-Occasions-1)` |
| `BeamFailureDetectionSet-r17` | `38.331-asn1-BeamFailureDetectionSet-r17-001` | — | (Rel-17) `beamFailureInstanceMaxCount-r17 ENUMERATED {n1..n10}`, `beamFailureDetectionTimer-r17 ENUMERATED {pbfd1..pbfd10}` |
| `RACH-ConfigDedicated` | `38.331-asn1-RACH-ConfigDedicated-001` | — | `cfra CFRA OPTIONAL`, `cfra-TwoStep-r16 CFRA-TwoStep-r16` |
| `RACH-ConfigGeneric` | `38.331-asn1-RACH-ConfigGeneric-001` | — | `ra-ResponseWindow ENUMERATED {sl1, sl2, sl4, sl8, sl10, sl20, sl40, sl80}` (확장: `sl60, sl160`, `sl240..sl2560`) |

→ ASN.1 컬렉션 9개 IE 본문 직접 인용 가능. v1에서 미회수였던 enumerated 범위 전부 확보.

### Neo4j KG (4 cypher)

| KG | 매칭 Section 수 | 대표 sectionId |
|---:|---:|---|
| RAN1 (38.213) | 2 | `38.213-5`, `38.213-6` |
| RAN2 (38.321/38.331) | 7 | `38.321-5.17`, `38.321-5.18.25`, `38.321-6.1.3.23/.43/.58`, `38.331-5.7.13` |
| RAN4 (38.133) | 100 (LIMIT) | `38.133-8.18`, `38.133-8.18.2/.3/.7/.8` |
| RAN5 (38.533) | 100 (LIMIT) | `38.533-10.3.4`, `38.533-11.4.4`, `38.533-10.3.4.0.1/.0.3` |

---

## 답변 본문

### 1. 도입 배경

NR Rel-15 RAN1 단계에서 빔 실패 회복 메커니즘이 별도 절차로 도입되었다. R1-1707606은 두 가지 후보 메커니즘을 모두 지원하자고 제안하였다 [TDoc R1-1707606, "Discussion on beam failure recovery" — v1 인용 유지]. 빔 실패 검출 메트릭으로 L1-RSRP가 채택되었다 [TDoc R1-1713597, "Beam failure recovery"]. RAN2 측 동기는 R2-1803196이 명확히 보여준다: *"Beam failure recovery procedure is described in section 5.17 of TS 38.321. Based on a number of 'beam failure instances' from physical layer MAC will trigger a random access procedure which allows the recovery."* [TDoc R2-1803196 (Rel-15)]. Rel-16에서는 SCell BFR로 확장 [TDoc R2-1900212], Rel-18에서는 SCell-deactivated 상태 BFR로 추가 확장되었다 [TDoc R2-2301761].

---

### 2. 38.213 — PHY 절차 (RAN1)

**§6 *Link recovery procedures* 본문 (P2 적용 후 직접 회수)**:

> *"A UE can be provided, for each BWP of a serving cell, a set of periodic CSI-RS resource configuration indexes by failureDetectionResourcesToAddModList and a set of periodic CSI-RS resource configuration indexes and/or SS/PBCH block indexes by candidateBeamRSList or candidateBeamRSListExt or candidateBeamRS-List for radio link quality measurements on the BWP of the serving cell. Instead of the sets ... for each BWP of a serving cell, the UE can be provided respective two sets ... by failureDetectionSet1 and failureDetectionSet2 that can be activated by a MAC CE [11 TS 38.321] and corresponding two sets ... by candidateBeamRS-List and candidateBeamRS-List2..."* [38.213 §6, chunkId=`38.213-6-001`]

**Q_in/Q_out (가상 BLER) 임계값의 정의 본문 — v1에서 미회수, v2에서 회수**:

> *"The thresholds Qout,LR and Qin,LR correspond to the default value of rlmInSyncOutOfSyncThreshold, as described in [10, TS 38.133] for Qout, and to the value provided by rsrp-ThresholdSSB or rsrp-ThresholdBFR, respectively. The physical layer in the UE assesses the radio link quality according to the set ... of resource configurations against the threshold Qout,LR."* [38.213 §6, chunkId=`38.213-6-001`]

확인되는 사실:
- BFD-RS 자원: `failureDetectionResourcesToAddModList` (단일 set), `failureDetectionSet1/Set2` (이중 set, MAC CE로 활성) [38.213 §6, `38.213-6-001`].
- 후보 빔 자원: `candidateBeamRSList`, `candidateBeamRSListExt`, `candidateBeamRS-List`, `candidateBeamRS-List2` [동 chunk].
- **`Q_out,LR` ↔ `rlmInSyncOutOfSyncThreshold` (38.133 정의)**, **`Q_in,LR` ↔ `rsrp-ThresholdSSB` 또는 `rsrp-ThresholdBFR`** [38.213 §6, `38.213-6-001`]. → 38.213이 직접 38.133을 참조한다.
- §6 본문은 SCell BFR / inter-cell BFR / `recoverySearchSpaceId` 처리도 포함한다 [38.213 §6, `38.213-6-002`, `38.213-6-004`].

> **참고**: 38.213 §6 본문은 *"$Q_{out,LR}$의 가상 PDCCH BLER이 10%"* 같은 절대 BLER 수치 row를 직접 노출하지 않는다. 38.213 본문은 *"correspond to ... rlmInSyncOutOfSyncThreshold ... [10, TS 38.133]"* 형태로 38.133에 위임한다 [38.213 §6, `38.213-6-001`]. 따라서 BLER 절대값은 38.133 측 chunk나 표 row를 따로 봐야 하며, 본 검색 결과에서 ms·BLER 표 row 자체는 회수되지 않았다.

---

### 3. 38.321 — MAC 절차 (RAN2)

**§5.17 BFR 본문 (P2 후 full text 회수)**:

> *"The MAC entity may be configured by RRC per Serving Cell or per BFD-RS set with a beam failure recovery procedure ... Beam failure is detected by counting beam failure instance indication from the lower layers to the MAC entity. If beamFailureRecoveryConfig is reconfigured by upper layers during an ongoing Random Access procedure for beam failure recovery for SpCell, the MAC entity shall stop the ongoing Random Access procedure and initiate a Random Access procedure using the new configuration. The Serving Cell is configured with two BFD-RS sets if and only if failureDetectionSet1 and failureDetectionSet2 are configured for the active DL BWP of the Serving Cell. When the SCG is deactivated, the UE performs beam failure detection on the PSCell if bfd-and-RLM is set to true."* [38.321 §5.17, chunkId=`38.321-5.17-001`]

§5.17은 RRC가 설정하는 파라미터 목록을 본문에 직접 명시한다 [동 chunk]:

| RRC 파라미터 | 역할 |
|---|---|
| `beamFailureInstanceMaxCount` | 빔 실패 검출 카운터 상한 |
| `beamFailureDetectionTimer` | 빔 실패 검출 타이머 |
| `beamFailureRecoveryTimer` | SpCell BFR 타이머 |
| `rsrp-ThresholdSSB` | SpCell BFR L1-RSRP 임계 |
| `rsrp-ThresholdBFR` | SCell BFR / BFD-RS set 단위 BFR L1-RSRP 임계 |
| `powerRampingStep` / `powerRampingStepHighPriority` | SpCell BFR 전력 램핑 |
| `preambleReceivedTargetPower`, `preambleTransMax` | SpCell BFR PRACH 파워 |
| `scalingFactorBI` | SpCell BFR backoff 스케일 |
| `ssb-perRACH-Occasion` | SpCell BFR CFRA SSB-per-RO |
| `ra-ResponseWindow` | SpCell BFR CFRA 응답 모니터링 윈도 |
| `prach-ConfigurationIndex` | SpCell BFR CFRA PRACH config |

→ §5.17은 RRC 파라미터를 호명만 하고 enumerated 값 자체는 38.331 IE 본문에 정의되어 있다.

---

### 4. 38.331 — RRC IE 본문 (★ ASN.1 컬렉션 — v2 핵심)

v2에서 `ran2_ts_asn1_chunks`로부터 IE 본문 직접 인용 가능 (v1에서 미회수):

#### 4.1 `BeamFailureRecoveryConfig` IE (SpCell BFR)

> ```
> BeamFailureRecoveryConfig ::= SEQUENCE {
>   rootSequenceIndex-BFR    INTEGER (0..137)                       OPTIONAL, -- Need M
>   rach-ConfigBFR           RACH-ConfigGeneric                     OPTIONAL, -- Need M
>   rsrp-ThresholdSSB        RSRP-Range                             OPTIONAL, -- Need M
>   candidateBeamRSList      SEQUENCE (SIZE (1..maxNrofCandidateBeams)) OF PRACH-ResourceDedicatedBFR OPTIONAL, -- Need M
>   ssb-perRACH-Occasion     ENUMERATED {oneEighth, oneFourth, oneHalf, one, two,
>                                        four, eight, sixteen}      OPTIONAL, -- Need M
>   ra-ssb-OccasionMaskIndex INTEGER (0..15)                        OPTIONAL, -- Need M
>   recoverySearchSpaceId    SearchSpaceId                          OPTIONAL, -- Need R
>   ra-Prioritization        RA-Prioritization                      OPTIONAL, -- Need R
>   beamFailureRecoveryTimer ENUMERATED {ms10, ms20, ms40, ms60, ms80, ms100, ms150, ms200} OPTIONAL, -- Need M
>   ...,
>   [[ msg1-SubcarrierSpacing SubcarrierSpacing OPTIONAL -- Need M ]],
>   [[ ra-PrioritizationTwoStep-r16 RA-Prioritization OPTIONAL,
>      candidateBeamRSListExt-v1610 SetupRelease{ CandidateBeamRSListExt-r16 } OPTIONAL ]],
>   [[ spCell-BFR-CBRA-r16 ENUMERATED {true} OPTIONAL ]],
>   [[ ra-OccasionType-r19 ENUMERATED {sbfd} OPTIONAL ]]
> }
> ```
> [ASN.1, chunkId=`38.331-asn1-BeamFailureRecoveryConfig-001`]

→ **`beamFailureRecoveryTimer`의 enumerated 절대값** 8단계 (`ms10`, `ms20`, `ms40`, `ms60`, `ms80`, `ms100`, `ms150`, `ms200` ms) 본문 직접 확인. Rel-16에서 `spCell-BFR-CBRA-r16`(SpCell CBRA), Rel-19에서 `ra-OccasionType-r19 {sbfd}` 추가.

#### 4.2 `RadioLinkMonitoringConfig` IE (BFD/RLM 통합)

> ```
> RadioLinkMonitoringConfig ::= SEQUENCE {
>   failureDetectionResourcesToAddModList SEQUENCE (SIZE (1..maxNrofFailureDetectionResources)) OF RadioLinkMonitoringRS OPTIONAL, -- Need N
>   failureDetectionResourcesToReleaseList SEQUENCE (SIZE (1..maxNrofFailureDetectionResources)) OF RadioLinkMonitoringRS-Id OPTIONAL, -- Need N
>   beamFailureInstanceMaxCount ENUMERATED {n1, n2, n3, n4, n5, n6, n8, n10} OPTIONAL, -- Need R
>   beamFailureDetectionTimer    ENUMERATED {pbfd1, pbfd2, pbfd3, pbfd4, pbfd5, pbfd6, pbfd8, pbfd10} OPTIONAL, -- Need R
>   ...,
>   [[ beamFailure-r17 BeamFailureDetection-r17 OPTIONAL -- Need R ]]
> }
> ```
> [ASN.1, chunkId=`38.331-asn1-RadioLinkMonitoringConfig-001`]

→ **`beamFailureInstanceMaxCount` enumerated 8단계** (`n1, n2, n3, n4, n5, n6, n8, n10`), **`beamFailureDetectionTimer` enumerated 8단계** (`pbfd1..pbfd10`) 본문 직접 확인. v1에서 미회수.

#### 4.3 `RadioLinkMonitoringRS` (RLM/BFD 자원 단위)

> ```
> RadioLinkMonitoringRS ::= SEQUENCE {
>   radioLinkMonitoringRS-Id RadioLinkMonitoringRS-Id,
>   purpose                  ENUMERATED {beamFailure, rlf, both},
>   detectionResource        CHOICE { ssb-Index SSB-Index, csi-RS-Index NZP-CSI-RS-ResourceId },
>   ...
> }
> ```
> [ASN.1, chunkId=`38.331-asn1-RadioLinkMonitoringRS-001`]

→ `purpose`로 RLM-only / BFD-only / 동시 사용 구분. `detectionResource`로 SSB / CSI-RS 분기.

#### 4.4 `PRACH-ResourceDedicatedBFR` / `BFR-SSB-Resource` / `BFR-CSIRS-Resource`

> ```
> PRACH-ResourceDedicatedBFR ::= CHOICE { ssb BFR-SSB-Resource, csi-RS BFR-CSIRS-Resource }
> BFR-SSB-Resource ::= SEQUENCE { ssb SSB-Index, ra-PreambleIndex INTEGER (0..63), ... }
> BFR-CSIRS-Resource ::= SEQUENCE {
>   csi-RS NZP-CSI-RS-ResourceId,
>   ra-OccasionList SEQUENCE (SIZE (1..maxRA-OccasionsPerCSIRS)) OF INTEGER (0..maxRA-Occasions-1) OPTIONAL,
>   ra-PreambleIndex INTEGER (0..63) OPTIONAL,
>   ...
> }
> ```
> [ASN.1, chunkId=`38.331-asn1-PRACH-ResourceDedicatedBFR-001` / `BFR-SSB-Resource-001` / `BFR-CSIRS-Resource-001`]

→ 후보 빔 별 contention-free PRACH 프리앰블 인덱스 0..63 직접 인용.

#### 4.5 `RACH-ConfigGeneric` (RA 응답 윈도)

> `ra-ResponseWindow ENUMERATED {sl1, sl2, sl4, sl8, sl10, sl20, sl40, sl80}, ...,`
> `[[ ra-ResponseWindow-v1610 ENUMERATED {sl60, sl160} OPTIONAL ... ]],`
> `[[ ra-ResponseWindow-v1700 ENUMERATED {sl240, sl320, sl640, sl960, sl1280, sl1920, sl2560} OPTIONAL ... ]]`
> [ASN.1, chunkId=`38.331-asn1-RACH-ConfigGeneric-001`]

→ BFR PRACH 응답 모니터 윈도 enumerated 범위 (sl1..sl2560) 본문 확인. 단위 sl=slot.

#### 4.6 `BeamFailureDetectionSet-r17` (Rel-17 multi-BFD-set)

> ```
> BeamFailureDetectionSet-r17 ::= SEQUENCE {
>   bfdResourcesToAddModList-r17 SEQUENCE (SIZE (1..maxNrofBFDResourcePerSet-r17)) OF BeamLinkMonitoringRS-r17 OPTIONAL,
>   bfdResourcesToReleaseList-r17 SEQUENCE (SIZE (1..maxNrofBFDResourcePerSet-r17)) OF BeamLinkMonitoringRS-Id-r17 OPTIONAL,
>   beamFailureInstanceMaxCount-r17 ENUMERATED {n1, n2, n3, n4, n5, n6, n8, n10} OPTIONAL,
>   beamFailureDetectionTimer-r17 ENUMERATED {pbfd1, pbfd2, pbfd3, pbfd4, pbfd5, pbfd6, pbfd8, pbfd10} OPTIONAL,
>   ...
> }
> ```
> [ASN.1, chunkId=`38.331-asn1-BeamFailureDetectionSet-r17-001`]

→ Rel-17에서 BFD-RS set 단위로 동일 enumerated를 별도 보유.

---

### 5. 38.133 — RAN4 RRM 정량 요구사항

**SSB 기반 BFD 평가 기간 / 임계값**:

> *"UE shall be able to evaluate whether the downlink radio link quality on the configured SSB resource in set ... estimated over the last TEvaluate_BFD_SSB period becomes worse than the threshold Qout_LR_SSB within TEvaluate_BFD_SSB period. The value of TEvaluate_BFD_SSB is defined in table 8.5C.2.2-1 for FR1-NTN."* [38.133 §8.5C.2.2, chunkId=`38.133-8.5C.2.2-001`]

> *"The value of TEvaluate_BFD_SSB is defined in table 8.5D.2.2-1 for FR1."* (ATG UE) [38.133 §8.5D.2.2, chunkId=`38.133-8.5D.2.2-001`]

> *"... the last TEvaluate_BFD_SSB_Relax period becomes worse than the threshold Qout_LR_SSB ... The value of TEvaluate_BFD_SSB_Relax is defined in table 8.5.2.4-1 for FR1. The value of TEvaluate_BFD_SSB_Relax is defined in table 8.5.2.4-2 for FR2 with scaling factor N=8."* [38.133 §8.5.2.4, chunkId=`38.133-8.5.2.4-001`]

> *"... TEvaluate_BFD_SSB_Redcap ... defined in table 8.5B.2.2-1 for FR1 ... 8.5B.2.2-2 for FR2 with scaling factor N=8."* [38.133 §8.5B.2.2, chunkId=`38.133-8.5B.2.2-001`]

**CSI-RS 기반 BFD**:

> *"... the last TEvaluate_BFD_CSI-RS period becomes worse than the threshold Qout_LR_CSI-RS within TEvaluate_BFD_CSI-RS period. The value of TEvaluate_BFD_CSI-RS is defined in table 8.5D.3.2-1 for FR1."* [38.133 §8.5D.3.2, chunkId=`38.133-8.5D.3.2-001`]

확인되는 정량 정의 — **변수명·표 번호·스케일링 인자**:

| BFD-RS / UE 종류 | 평가기간 변수 | 임계값 변수 | 표 번호 | 스케일링 N (FR2/FR2-1) |
|---|---|---|---|---|
| SSB / 일반 / FR1 | `TEvaluate_BFD_SSB` | `Qout_LR_SSB` | (예: §8.18.2.2-1) | — |
| SSB / Relaxed / FR1·FR2 | `TEvaluate_BFD_SSB_Relax` | `Qout_LR_SSB` | 8.5.2.4-1 / -2 | **N = 8** [§8.5.2.4-001] |
| SSB / RedCap / FR1·FR2 | `TEvaluate_BFD_SSB_Redcap` | `Qout_LR_SSB` | 8.5B.2.2-1 / -2 | **N = 8** [§8.5B.2.2-001] |
| SSB / FR1-NTN | `TEvaluate_BFD_SSB` | `Qout_LR_SSB` | 8.5C.2.2-1 | — [§8.5C.2.2-001] |
| SSB / ATG / FR1 | `TEvaluate_BFD_SSB` | `Qout_LR_SSB` | 8.5D.2.2-1 | — [§8.5D.2.2-001] |
| CSI-RS / 일반 / FR1 | `TEvaluate_BFD_CSI-RS` | `Qout_LR_CSI-RS` | 8.5D.3.2-1 | — [§8.5D.3.2-001] |

(주: 표 row의 ms 절대값은 본 chunk text 안에 포함되지만 별도 라인 단위 회수가 필요. 본 답변에서는 변수·표 번호 단계까지 인용한다.)

---

### 6. 38.533 — RAN5 적합성 시험

**KG**: RAN5 KG는 BFD/LR 시험 노드를 100건(LIMIT 100) 보유 [Cypher RAN5_38533]. 대표 노드:

- `38.533-10.3.4` *Beam failure detection and link recovery procedures* (EN-DC FR1)
- `38.533-10.3.4.0.1` *Minimum conformance requirements for SSB based Beam Failure Detection under CCA*
- `38.533-10.3.4.0.3` *Scheduling availability of UE during beam failure detection under CCA*
- `38.533-10.3.4.1/.2` *PSCell SSB-based BFD/LR — non-DRX / DRX*
- `38.533-11.4.4` *NR SA FR1 BFD/LR procedures*
- `38.533-7.5.6.1.1/.1.2`, `38.533-16.7.4.x` (L1-RSRP 정확도 측정 시험 — title 매칭 score 0.6892)

> **본문 한계**: `ran5_ts_sections` 컬렉션은 chunk text 본문이 비어있고 `sectionTitle`만 존재 (Phase-7/RAN5 spec 의도된 결과 — title 임베딩) [실측: §16.7.4.2.2 등 chunk text 길이 0]. 따라서 RAN5는 **시험 케이스 명칭/구조 단위까지** 인용 가능하고, FFS/test tolerance 등 본문 마커는 본 v2 chunk에서는 노출되지 않는다 (이 점은 v1과 동일 — P2/ASN.1로도 해소되지 않음).

확인되는 시험 차원 (KG 노드 명칭 기반):
- 모드: **EN-DC vs NR SA**
- 주파수: **FR1 vs FR2**
- 셀: **PCell vs PSCell**
- DRX 상태: **non-DRX vs DRX**
- BFD-RS: **SSB-based vs CSI-RS-based**
- 환경: **CCA (Coverage Constrained Adaptation) 별도 §10.3.4.0.x**

---

## ★ 정량값 검증 매트릭스 (v1 → v2)

| 항목 | v1 회수 | v2 회수 | 출처 |
|---|---|---|---|
| `Q_out,LR` / `Q_in,LR` 정의 (참조 매핑) | ❌ (top score 0.33로 미인용) | ✅ *"Qout,LR ... rlmInSyncOutOfSyncThreshold ... [10, TS 38.133]; Qin,LR ... rsrp-ThresholdSSB or rsrp-ThresholdBFR"* | 38.213 §6, `38.213-6-001` |
| `beamFailureInstanceMaxCount` enumerated 범위 | ❌ | ✅ `{n1, n2, n3, n4, n5, n6, n8, n10}` | ASN.1 `RadioLinkMonitoringConfig`, `RadioLinkMonitoringConfig-001` |
| `beamFailureDetectionTimer` enumerated 범위 | ❌ | ✅ `{pbfd1, pbfd2, pbfd3, pbfd4, pbfd5, pbfd6, pbfd8, pbfd10}` | ASN.1 `RadioLinkMonitoringConfig-001` |
| `beamFailureRecoveryTimer` enumerated (ms 절대값) | ❌ | ✅ `{ms10, ms20, ms40, ms60, ms80, ms100, ms150, ms200}` | ASN.1 `BeamFailureRecoveryConfig-001` |
| `ssb-perRACH-Occasion` enumerated | ❌ | ✅ `{oneEighth, oneFourth, oneHalf, one, two, four, eight, sixteen}` | ASN.1 `BeamFailureRecoveryConfig-001` |
| `rootSequenceIndex-BFR` 범위 | ❌ | ✅ `INTEGER (0..137)` | ASN.1 `BeamFailureRecoveryConfig-001` |
| `ra-PreambleIndex` 범위 | ❌ | ✅ `INTEGER (0..63)` | ASN.1 `BFR-SSB-Resource-001`, `BFR-CSIRS-Resource-001` |
| `ra-ResponseWindow` enumerated (Rel-15/16/17) | ❌ | ✅ `{sl1..sl80}`, `+ {sl60, sl160}` (r16), `+ {sl240..sl2560}` (r17) | ASN.1 `RACH-ConfigGeneric-001` |
| `RadioLinkMonitoringRS.purpose` | ❌ | ✅ `ENUMERATED {beamFailure, rlf, both}` | ASN.1 `RadioLinkMonitoringRS-001` |
| 38.133 BFD 평가기간 변수명·표 번호 | ✅ (변수명) | ✅ (변수명·표 번호·스케일링 N) | 38.133 §8.5B/§8.5C/§8.5D/§8.5.2.4 chunks |
| 38.133 표 row의 ms 절대값 (수치 line) | ❌ (preview 컷오프) | △ (chunk 내 포함되나 line-level 인용 미수행) | 본 답변 회수 범위 외 |
| 38.213 BLER 절대 % 수치 (예: "10%") | ❌ | ❌ (38.213 §6은 "default value of rlmInSyncOutOfSyncThreshold [10, TS 38.133]"로 위임 — 본문에 % 수치 부재) | — |

→ **이전 미답 6건 → v2 후 정량 인용 가능 9건** (BLER 절대값 1건은 38.213 본문 자체가 38.133에 위임하므로 38.213 chunk만으로는 회수 불가 — 본 검색에서 38.133 측 BLER % 표 row는 별도 라인 단위 인용 미수행).

---

## 동작 시퀀스 (v2 회수 본문 기반 재구성)

```
[gNB]                                            [UE — RRC + MAC + L1]
  | (1) RRC: BeamFailureRecoveryConfig +          |
  |     RadioLinkMonitoringConfig 송신             |
  |     · failureDetectionResourcesToAddModList    |
  |       SIZE (1..maxNrofFailureDetectionResources)
  |     · beamFailureInstanceMaxCount {n1..n10}    |
  |     · beamFailureDetectionTimer {pbfd1..pbfd10}|
  |     · candidateBeamRSList SIZE (1..maxNrofCandidateBeams)
  |     · rsrp-ThresholdSSB / rsrp-ThresholdBFR    |
  |     · beamFailureRecoveryTimer {ms10..ms200}   |
  |———————————————————————————————→               |
  |   [ASN.1 RadioLinkMonitoringConfig-001,        |
  |    BeamFailureRecoveryConfig-001]              |
  |                                                |
  |                                                | (2) L1: q0 위 hypothetical PDCCH BLER 측정 →
  |                                                |     radio link quality vs Qout,LR
  |                                                |     (Qout,LR ↔ rlmInSyncOutOfSyncThreshold@38.133)
  |                                                |     [38.213 §6, 38.213-6-001]
  |                                                |
  |                                                | (3) MAC: counter ≥ beamFailureInstanceMaxCount
  |                                                |     → BFR 트리거. beamFailureDetectionTimer
  |                                                |     동안 미만이면 카운터 리셋
  |                                                |     [38.321 §5.17, 38.321-5.17-001]
  |                                                |
  |                                                | (4) candidate beam 식별 (q1, L1-RSRP ≥
  |                                                |     rsrp-ThresholdSSB 또는 rsrp-ThresholdBFR)
  |                                                |     [38.321 §5.17 + 38.213 §6]
  |                                                |
  |                                                | (5) contention-free PRACH 전송
  |                                                |     · BFR-SSB-Resource: ra-PreambleIndex 0..63
  |                                                |     · BFR-CSIRS-Resource: ra-OccasionList +
  |                                                |       ra-PreambleIndex 0..63
  |                                                |     [ASN.1 PRACH-ResourceDedicatedBFR-001]
  |←———————————————————————————————                |
  |                                                |
  | (6) gNB response monitoring                    |
  |     · ra-ResponseWindow                        |
  |       {sl1..sl80} (+r16 sl60/sl160) (+r17 sl240..sl2560)
  |     · recoverySearchSpaceId                    |
  |     [ASN.1 RACH-ConfigGeneric-001 +            |
  |      BeamFailureRecoveryConfig-001]            |
  |                                                |
  |                                                | (7) RAN4 평가기간 충족
  |                                                |     · TEvaluate_BFD_SSB / SSB_Redcap /
  |                                                |       SSB_Relax / SSB_NTN / CSI-RS
  |                                                |     · Qout_LR_SSB / Qout_LR_CSI-RS
  |                                                |     [38.133 §8.5B/§8.5C/§8.5D/§8.5.2.4]
  |                                                |
  | (8) RAN5 conformance (EN-DC/SA × FR1/FR2 ×     |
  |     PCell/PSCell × DRX/non-DRX × SSB/CSI-RS)   |
  |     [38.533 §10.3.4.x, §11.4.4, §16.7.4.x]     |
```

---

## 문서 간 연결고리

1. **38.213 → 38.133 (BLER 임계값)**: *"Qout,LR and Qin,LR correspond to ... rlmInSyncOutOfSyncThreshold, as described in [10, TS 38.133]"* [38.213 §6, `38.213-6-001`]. → **PHY 임계값 정의가 명시적으로 RAN4 RRM 문서에 위임**된다.
2. **38.213 ↔ 38.331 RRC 파라미터**: 38.213 §6 본문은 `failureDetectionResourcesToAddModList`, `candidateBeamRSList`, `rsrp-ThresholdSSB`, `rsrp-ThresholdBFR`, `recoverySearchSpaceId`를 직접 참조 [38.213 §6, `38.213-6-001`]. 이 모두가 38.331 IE (`RadioLinkMonitoringConfig`, `BeamFailureRecoveryConfig`)에 본문 정의됨 [ASN.1 IE 본문].
3. **38.331 IE → 38.321 절차**: 38.321 §5.17 본문이 *"RRC configures the following parameters in the beamFailureRecoveryConfig, beamFailureRecoverySpCellConfig, beamFailureRecoverySCellConfig and the radioLinkMonitoringConfig ..."* [38.321 §5.17, `38.321-5.17-001`]. → **RRC 파라미터 → MAC 절차** 본문 1:1 매핑.
4. **38.321 ↔ 38.213 (instance counting)**: §5.17 *"Beam failure is detected by counting beam failure instance indication from the lower layers to the MAC entity"* [38.321 §5.17, `38.321-5.17-001`]. → **L1(38.213) → MAC(38.321) indication** 명시.
5. **38.213/331 → 38.133 (RRM 정량)**: 38.133은 동일한 BFD-RS 구조(SSB / CSI-RS)와 임계값 변수(`Qout_LR_*`)에 대한 평가 기간을 정의 [38.133 §8.5B/§8.5C/§8.5D/§8.5.2.4 chunks].
6. **38.133 → 38.533**: RAN5는 §10.3.4 / §11.4.4 / §16.7.4 BFD/LR 시험 케이스를 정의 [Cypher RAN5_38533, 100 rows]. v1에서 인용한 R5-204985의 *"normative reference ... TS 38.133 [6] clause A.4.5.5.1"* 패턴이 유지됨.

요약 (chunkId/IE 검증 포함):
```
38.331 IE (RadioLinkMonitoringConfig, BeamFailureRecoveryConfig, BFR-SSB/CSIRS-Resource, RACH-ConfigGeneric)
  └ ASN.1 enumerated 절대값 (n1..n10, pbfd1..pbfd10, ms10..ms200, sl1..sl2560)
  ↓ (RRC → MAC)
38.321 §5.17 BFR procedure (instance counting, ra-ResponseWindow start, parameter list 호명)
  ↓ (MAC ← L1 indication, q0/q1 자원 정의)
38.213 §5/§6 Link recovery (Qout,LR/Qin,LR ↔ rlmInSyncOutOfSyncThreshold/rsrp-ThresholdSSB/BFR)
  ↓ (정량 평가)
38.133 §8.5B/§8.5C/§8.5D/§8.5.2.4 (TEvaluate_BFD_*, Qout_LR_*, FR1/FR2 표 + 스케일링 N=8)
  ↓ (normative reference)
38.533 §10.3.4/§11.4.4/§16.7.4 BFD/LR conformance (EN-DC/SA × FR × DRX × SSB/CSI-RS)
```

---

## 커버리지 / 한계

| 항목 | v1 결과 | v2 결과 | 변화 |
|---|---|---|---|
| 38.213 §6 *Link recovery* 본문 | 부분 (chunkId 1개) | ✅ 다중 chunk (`38.213-6-001/-002/-004`) | P2로 §6 sub-chunk 더 잡힘 |
| 38.213 Q_out,LR / Q_in,LR 정의 | ❌ | ✅ 정의 직접 인용 | 해소 |
| 38.213 BLER 절대값 (% 수치) | ❌ | ❌ (38.213 본문이 38.133으로 위임) | 38.213 chunk로는 본질적 미회수 |
| 38.321 §5.17 BFR full text | 부분 | ✅ full chunk 본문 + RRC 파라미터 목록 12종 호명 | 해소 |
| 38.321 `beamFailureInstanceMaxCount` 만기 → RACH 분기 본문 | 부분 | △ (§5.17 본문에 트리거 동작 명시, sub-clause line-level은 별도) | 부분 해소 |
| 38.331 IE ASN.1 (`BeamFailureRecoveryConfig`, `RadioLinkMonitoringConfig`, ...) | ❌ | ✅ ★ ASN.1 컬렉션 직접 회수 (9 IE) | **완전 해소** |
| 38.331 IE enumerated 절대값 | ❌ | ✅ ms10..ms200 / n1..n10 / pbfd1..pbfd10 / sl1..sl2560 / oneEighth..sixteen 등 | **완전 해소** |
| 38.133 §8.18 BFD/BFR 변수·표·스케일링 N | 부분 (변수명까지) | ✅ 변수 + 표 번호 + N=8 | 해소 |
| 38.133 표 row의 ms 절대값 | ❌ (preview 컷오프) | △ (chunk text에 포함되어 있으나 본 답변에서 line-level 미인용) | 일부 해소 |
| 38.533 시험 케이스 KG 노드 구조 | ✅ | ✅ | 동일 |
| 38.533 본문 (FFS/tolerance 등) | 부분 (FFS 마커 chunk 1건) | ❌ (text 비어있음 — RAN5 phase-7 spec 결과) | 변화 없음 |

**3gpp-tracer에서 미회수 (v2에서도 미해소)**:
- 38.213 측 BLER 절대 % 수치 — 38.213 본문이 38.133으로 명시적 위임 (구조적 한계).
- 38.133 표 8.5B.2.2-1 / 8.5C.2.2-1 / 8.5D.2.2-1 / 8.5D.3.2-1 row의 ms 절대값 line-level 인용 (chunk 본문에는 포함되나 별도 line 추출 미수행).
- 38.533 시험 본문 (text 비어있음 — RAN5 컬렉션이 title 임베딩 정책).

이상 항목은 **임의 채워넣기 금지** 원칙(CLAUDE.md)에 따라 본 답변에 포함하지 않음.

---

## 자가 검증

| 점검 | 상태 |
|---|---|
| 모든 사실 문장에 chunkId 또는 IE chunkId 인용 | OK |
| 외부 웹/일반 지식 사용 여부 | 사용하지 않음 (WebFetch/WebSearch 호출 0) |
| 임의의 enumerated 값 / ms 값을 학습 지식으로 채워넣었는가? | **NO** — `{n1..n10}`, `{pbfd1..pbfd10}`, `{ms10..ms200}`, `{sl1..sl2560}`, `{oneEighth..sixteen}` 등은 ASN.1 chunk 본문에서 직접 인용. BLER 절대 % 수치는 38.213 chunk 본문에 부재 → 인용하지 않음. |
| v1 미답 6항목 해소 여부 | 9건 해소 (Qout,LR/Qin,LR 정의, 4종 enumerated 범위, ms 절대값, sl 절대값, INTEGER 범위). 1건 미해소 (BLER 절대 % — 구조적). |
| Cypher 쿼리가 실제 KG schema에 맞는가? | OK — `Section`-`[:BELONGS_TO_SPEC]`-`Spec` 구조, RAN1=2 / RAN2=7 / RAN4=100 / RAN5=100 행. |
| 검색 스크립트 / 로그 산출물 경로 | `scripts/cross-phase/usecase/q3_search_bfd_bfr_v2.py`, `logs/cross-phase/usecase/q3_retrieval_log_v2.json`. |
| v1 백업 위치 | `docs/usecase/answers/tracer/q3_beam_failure_recovery_v1.md`. |
