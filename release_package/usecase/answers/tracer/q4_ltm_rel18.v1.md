# Q4. Rel-18 LTM (L1/L2 Triggered Mobility) 표준 아이템 정리

> **출처**: 3gpp-tracer (Qdrant + Neo4j) 단일 소스. 외부 검색 없음. 모든 사실 문장은 retrieval log
> `logs/cross-phase/usecase/q4_retrieval_log.json` 의 chunk 인용.

---

## 메타

| 항목 | 값 |
|---|---|
| 질문 | Rel-18 LTM 표준 아이템(38.300/331/321/214/133/306) 정리 + Rel-19/20 확장 + 문서 간 연결 |
| 임베딩 모델 | `openai/text-embedding-3-small` (OpenRouter) |
| Qdrant 컬렉션 | `ran1_ts_sections`, `ran2_ts_sections`, `ran4_ts_sections`, `ran1_tdoc_chunks`, `ran2_tdoc_chunks`, `ran4_tdoc_chunks`, `ran1_cr_chunks`, `ran2_cr_chunks` |
| Neo4j | RAN1=7687, RAN2=7688, RAN4=7690 |
| 쿼리 수 | TS 33 + TDoc 27 + Cypher 3 = **63** |
| Hits | TS 330, TDoc 270, Cypher rows 102 (44+2+56) |
| Top-k | 10 |

---

## 3gpp-tracer 검색 결과 요약

### 컬렉션별 hit (벡터 검색 합계)

| Collection | Queries | Hits |
|---|---:|---:|
| ran2_ts_sections (38.300/331/321/306) | 22 | 220 |
| ran1_ts_sections (38.214) | 6 | 60 |
| ran4_ts_sections (38.133) | 5 | 50 |
| ran2_tdoc_chunks | 15 | 150 |
| ran1_tdoc_chunks | 4 | 40 |
| ran4_tdoc_chunks | 3 | 30 |
| ran2_cr_chunks | 3 | 30 |
| ran1_cr_chunks | 2 | 20 |
| **합계** | **60** | **600** |

### Release tag 분포 (TDoc 검색 결과)

| Release | hits |
|---|---:|
| Rel-18 | 94 |
| Rel-19 | 70 |
| Rel-20 | 30 |
| (release 미부여 = CR/일부 discussion) | 61 |
| Rel-15/16/17/14 (관련 없는 backfill) | 15 |

### Neo4j Section 카탈로그 (LTM 관련 핵심 노드)

| Spec | 핵심 LTM 섹션 / IE 노드 (Cypher 실측) |
|---|---|
| 38.300 | 9.2.3.5 `L1/L2 Triggered Mobility`, 9.2.3.7 `Conditional L1/L2 Triggered Mobility` |
| 38.331 | 5.3.5.18 `LTM configuration and execution` (서브 5.3.5.18.1~10), 5.3.5.13.6/.13.8 `Subsequent CPAC`, IE 그룹 `LTM-Config / LTM-Candidate / LTM-CSI-ReportConfig / LTM-ResourceConfigNRDC / LTM-ConfigNRDC / SK-CounterConfigLTM / VarLTM-*` |
| 38.321 | 5.18.35 `(Enhanced) LTM Cell Switch Command`, 5.18.36 `Candidate Cell TCI States Activation/Deactivation`, 5.18.38 SP CSI-RS/CSI-IM for candidate cell, 5.2b `Maintenance of UL Synchronization for CLTM candidate cell`, 5.35.3.2~5.35.3.5 `Event LTM2~LTM5`, 5.36 `Conditional LTM`, 6.1.3.4b `LTM Candidate Timing Advance Command MAC CE`, 6.1.3.75 `LTM Cell Switch Command MAC CE`, 6.1.3.75a `Enhanced LTM Cell Switch Command MAC CE`, 6.1.3.76 `Candidate Cell TCI States Activation/Deactivation MAC CE`, 6.1.3.12a `SP CSI-RS/CSI-IM Resource Set Activation/Deactivation for Candidate Cell MAC CE` |
| 38.214 | 5.2.1.5.4.2 `UE Initiated LTM reporting`, 5.2.4a `CSI Reporting for LTM and handover` |
| 38.133 | 6.3 `L1/L2-Triggered Mobility`(6.3.1 LTM PCell, 6.3.1.2 LTM Cell Switch delay, 6.3.2 Conditional L1/L2-Triggered Mobility, 6.3.2.2 CLTM Cell Switch delay), 6.2.2C `PDCCH ordered Random Access for LTM`, 8.20 `LTM PSCell Cell Switch`, 8.25 `TCI state activation for LTM candidate cell`, 10.1.19D/19E/20A/20B `LTM Intra/Inter-frequency L1-RSRP accuracy (FR1/FR2)`, A.3.16B `LTM Candidate TCI State Configuration`, A.6.3.4/A.6.3.5/A.6.3.6 `LTM PCell/PSCell/CLTM PCell Switch` 시험, A.6.6.26~33 / A.6.7.17 / A.7.6.20~29 / A.7.7.15 `LTM L1-RSRP measurement` 시험 |
| 38.306 | 5.4 `Other features`, 5.6 `RRM measurement features`, 4.2.7.9 `MRDC-Parameters` (LTM 관련 capability 노출) |

> 38.306의 LTM 전용 feature group 명칭은 본 retrieval에서 chunk 본문이 직접 잡히지 않아 "5.4 Other features / 5.6 RRM measurement features 클러스터에 속한다"는 위치 정보까지만 인용 가능. 세부 feature group 번호는 **3gpp-tracer 검색 범위에서 미발견**.

---

## 답변 본문

### 1. Rel-18 LTM 도입 배경 — TDoc 근거

3gpp-tracer 검색 결과, Rel-18 LTM은 RAN#... (Plenary RP-WID 번호는 본 retrieval에 직접 잡히지 않음)에서 시작된 **"Further NR mobility enhancement"** WI 산하의 핵심 작업으로 도입되었다.
- "Rel-18 WID on Further NR mobility enhancement (RP-221799 [1]) included the work related to facilitate mobility using L1/L2-based signaling. Currently serving cell change is triggered by L3 measurements and is done by RRC signalling triggered Reconfiguration with Synchronisation for change of PCell and PSCell, …" [R2-2207340, RAN2#119-e, type=discussion, rel=Rel-18, AI=8.4.2.1, chunkId=R2-2207340-001]
- "In Rel-18, L1L2 mobility is one of the important features for further NR mobility enhancements, which is introduced in order to reduce latency, overhead and interruption time." [R2-2301501, RAN2#121, rel=Rel-18, chunkId=R2-2301501-001]
- "L1/L2 mobility (LTM) is the main part of the Rel-18 work item. In the Rel-18 mobility WI, the serving cells of the UE will be updated based on an indication provided on L1 or L2." [R1-2302414, RAN1#112b-e, rel=Rel-18, AI=9.10.2, chunkId=R1-2302414-001]
- "The goal of LTM is to enable a serving cell change via L1/L2 signalling in order to reduce the latency, overhead and interruption time." [R1-2311212, RAN1#115, rel=Rel-18, AI=8.7.1, chunkId=R1-2311212-001]

즉, 본 retrieval 범위 안에서 LTM 도입 동기는 **(a) RRC reconfiguration with sync 기반 L3 핸드오버의 latency/overhead/interruption 한계, (b) L1/L2 signalling으로 serving cell change 실행** 두 가지로 명확히 인용 가능하다. CHO 대비 비교 본문은 R2-2504412 (RAN2#129, Rel-19) "LTM cell switch CHO comparison" 검색에서 잡히지만 본문 미정제. PDCCH 명령 기반 비교는 직접 인용 단계에는 부족.

### 2. 38.300 — LTM 개념 (Stage-2)

- 위치: **38.300 §9.2.3.5 "L1/L2 Triggered Mobility"** (서브 §9.2.3.5.1 General, §9.2.3.5.2 C-Plane Handling), **§9.2.3.7 "Conditional L1/L2 Triggered Mobility"** [Neo4j RAN2_LTM_sections, port=7688].
- C-Plane 절차 정의:
  > "Cell switch command is conveyed in a MAC CE, which contains the necessary information to perform the LTM cell switch. The overall procedure for intra-gNB LTM is shown in Figure 9.2.3.5.2-1 below. Subsequent LTM is done by repeating the early synchronization, LTM cell switch execution, and LTM cell switch completion steps without the need to release, reconfigure or add other LTM candidate configurations after each LTM cell switch completion." [38.300 §9.2.3.5.2, chunkId=38.300-9.2.3.5.2-001]
- CLTM 절차 정의:
  > "CLTM cell switch is executed by the UE when L1-based or L3-based LTM cell switch execution conditions are met. … The source gNB sends an RRCReconfiguration message to the UE and this includes the CLTM configurations of candidate cells as well [as their conditional execution conditions]." [38.300 §9.2.3.7.1, chunkId=38.300-9.2.3.7.1-001]
- 핵심 개념 요약 (모두 위 두 chunk에서 직접 도출):
  - **Candidate cell 사전 준비**: source gNB가 candidate gNB들에게 conditional/non-conditional execution config를 사전 협상.
  - **MAC CE로 cell switch 트리거**: RRC reconfiguration 메시지를 새로 내려보내지 않고 MAC CE로 즉시 셀 전환.
  - **Subsequent LTM**: 같은 candidate set 안에서 release/add 없이 반복 cell switch 가능 → overhead/interrupt 절감.
  - **Intra-gNB / SCG / Inter-gNB LTM** 구분 존재 (37.340 참조 명시: "Further details of SCG LTM can be found in TS 37.340 [21]").

### 3. 38.331 — RRC parameter / IE

- 핵심 절: **§5.3.5.18 "LTM configuration and execution"** (5.3.5.18.1 LTM configuration, .2 release, .3 add/mod, .6 execution, .7 release, .8 L3-meas based switch condition, .9/.10 sk-Counter add/mod/release) [Neo4j RAN2 cypher].
- 핵심 IE 노드 (Neo4j):
  - `LTM-Config`, `LTM-ConfigNRDC`, `LTM-Candidate`, `LTM-CandidateId`,
  - `LTM-CSI-ReportConfig`, `LTM-CSI-ReportConfigId`, `LTM-CSI-ResourceConfig`, `LTM-CSI-ResourceConfigId`,
  - `LTM-ExecutionConditionList`, `LTM-TCI-Info`, `LTM-ResourceConfigNRDC`,
  - `SK-CounterConfigLTM`, `VarLTM-ServingCellNoResetID`, `VarLTM-ServingCellNoSecurityChange`, `VarLTM-ServingCellUE-MeasuredTA-ID`.
- LTM-Config 의미:
  > "The network configures the UE with one or more LTM candidate configurations within the LTM-Config IE. An ltm-Config included within an RRCReconfiguration message received via SRB1 is for LTM on the MCG. … An ltm-Config included via SRB3 (or embedded in RRCReconfiguration via SRB1) is for LTM on the SCG. … An ltm-ConfigNRDC included … is for LTM on the SCG." [38.331 §5.3.5.18.1, chunkId=38.331-5.3.5.18.1-001]
- L3-기반 LTM 트리거 절차:
  > "for each entry within the LTM-ExecutionConditionList which has the l3-Conditions configured … if the condEventId related to this measId is associated with condEventA3 or condEventA5 … consider the event associated to this measId to be fulfilled for the ltm-CandidateId associated to the measId." [38.331 §5.3.5.18.8, chunkId=38.331-5.3.5.18.8-001]
- Candidate 관리:
  > "for each ltm-CandidateId value included in the ltm-CandidateToAddModList: … reconfigure the corresponding LTM-Candidate … if the LTM-Candidate … includes ltm-UE-MeasuredTA-ID … inform lower layers that the UE is configured with UE-based TA measurements for this LTM-Candidate." [38.331 §5.3.5.18.3, chunkId=38.331-5.3.5.18.3-001]
- Subsequent CPAC와의 관계:
  - §5.3.5.13.6 `Subsequent CPAC reference configuration addition/removal`, §5.3.5.13.8 `Subsequent CPAC execution` 가 LTM과 동일 5.3.5.x 트리에 함께 정의됨 [Neo4j RAN2 cypher].

### 4. 38.321 — MAC procedure / MAC CE

- LTM cell switch 트리거 (MAC CE 송신·수신):
  > "The network may instruct the UE to perform LTM cell switch procedure by sending the LTM Cell Switch Command MAC CE described in clause 6.1.3.75 or the Enhanced LTM Cell Switch Command MAC CE described in clause 6.1.3.75a. The Enhanced LTM Cell Switch Command MAC CE is used for MAC entity associated with MCG if the value of ltm-NoSecurityChangeID … is not equal to the value of stored ltm-ServingCellNoSecurityChangeID … . Otherwise, the LTM Cell Switch MAC CE is used." [38.321 §5.18.35, chunkId=38.321-5.18.35-001]
- MAC CE 포맷:
  > "The LTM Cell Switch Command MAC CE is identified by MAC subheader with eLCID … . Target Configuration ID: This field indicates the index of candidate target configuration to apply for LTM cell switch, corresponding to ltm-CandidateId minus 1 … (3 bits). Timing Advance Command: This field indicates whether the TA is valid for the LTM target cell …" [38.321 §6.1.3.75, chunkId=38.321-6.1.3.75-001]
- Candidate cell beam 사전 활성화 (TCI state):
  > "The network may activate and deactivate the TCI states of LTM candidate cell(s) configured in CandidateTCI-State and CandidateTCI-UL-State by sending the Candidate Cell TCI States Activation/Deactivation MAC CE described in clause 6.1.3.76. … The configured candidate cell TCI states are initially deactivated upon (re-)configuration by upper layer and after reconfiguration with sync that is not triggered by LTM." [38.321 §5.18.36, chunkId=38.321-5.18.36-001]
- Candidate cell TCI MAC CE 포맷 (다중 codepoint, DL/UL 분리):
  > "Candidate Cell ID: This field indicates the identity of an LTM candidate cell … (3 bits). Pi: … If the Pi field is set to 1, the ith TCI codepoint includes the DL TCI state and the UL TCI state. If the Pi field is set to 0, the ith TCI codepoint includes only the DL/joint TCI state …" [38.321 §6.1.3.76, chunkId=38.321-6.1.3.76-001]
- 추가 LTM-MAC 기능 (Neo4j 카탈로그):
  - §5.18.38 SP CSI-RS/CSI-IM resource set 활성화 (candidate cell용) + §6.1.3.12a MAC CE.
  - §5.2b `Maintenance of UL Synchronization for CLTM candidate cell`.
  - §6.1.3.4b `LTM Candidate Timing Advance Command MAC CE`.
  - §5.35.3.2~5.35.3.5 LTM Event 2/3/4/5 (서빙 빔/후보 빔 절대·상대 임계값 이벤트).
  - §5.36 `Conditional LTM` (5.36.1 Introduction, 5.36.2 L1 measurement based triggering condition evaluation, 5.36.3 execution).
- T304/타이머: "T304 LTM timer MAC" 쿼리는 38.321 §5.2b (UL sync) / §6.1.3.4b (TA MAC CE) / §6.1.3.21 (Timing Delta MAC CE)로 매칭 — **LTM 전용 timer 본문 발췌는 본 retrieval에서 미확보**.

### 5. 38.214 — UE L1 measurement / reporting

- 위치: **§5.2.4a "CSI Reporting for LTM and handover"**, **§5.2.1.5.4.2 "UE Initiated LTM reporting"** (Neo4j RAN1 cypher 결과 38.214 LTM 노드는 정확히 이 둘).
- 후보 셀에 대한 CSI/L1-RSRP 측정 설정:
  > "A UE configured with LTM-Config can be provided configurations for CSI acquisition, by up to one Reporting Setting, ltm-CSI-ReportConfig, for a candidate cell. … Each Reporting Setting ltm-CSI-ReportConfig or earlyCSI-Acquisition is associated with either one or two Resource Settings. When one Resource Setting (given by higher layer parameter ltm-ResourcesForChannelMeasurement or early-NZP-CSI-RS-ResourceSet) is configured, it provides a list of NZP CSI-RS resources for both channel and interference measurements." [38.214 §5.2.4a, chunkId=38.214-5.2.4a-001]
- UE-initiated event-triggered L1 reporting:
  > "For a report setting ltm-CSI-ReportConfig configured with ltm-ReportConfigType set to 'eventTriggered', the UE may expect that the time domain behavior of the NZP CSI-RS resources within a ltm-NZP-CSI-RS-ResourceSet is periodic when the LTM-CSI-ResourceConfig contains a configuration of a ltm-NZP-CSI-RS-ResourceSet. … the UE measures the L1-RSRP of the reference signal in the indicated TCI state provided in a NZP-CSI-RS-ResourceSet configured with repetition." [38.214 §5.2.1.5.4.2, chunkId=38.214-5.2.1.5.4.2-001]
- 일반 L1-RSRP 정의 (LTM도 동일 정의 사용):
  > "For L1-RSRP computation … the UE may be configured with CSI-RS resources, SS/PBCH Block resources or both … . For L1-RSRP reporting, if the higher layer parameter nrofReportedRS in CSI-ReportConfig is configured to be one, or if the higher layer parameters nrOfReportedCells and nrOfReportedRS-PerCell are both configured to be one, the reported L1-RSRP value is defined …" [38.214 §5.2.1.4.3, chunkId=38.214-5.2.1.4.3-001]

### 6. 38.133 — RRM 요구사항

- 일반 절: **§6.3 "L1/L2-Triggered Mobility"**, §6.3.1 LTM PCell, §6.3.2 Conditional LTM. 추가로 **§8.20 LTM PSCell**, **§8.25 TCI state activation for LTM candidate**, **§6.2.2C PDCCH ordered RA for LTM**, **§10.1.19D/19E (FR1) / §10.1.20A/20B (FR2) LTM L1-RSRP accuracy** [Neo4j RAN4 cypher 결과].
- LTM cell switch delay 정의 (PCell):
  > "LTM cell switch delay DLTM is the delay from the end of the last TTI containing the MAC-CE command for cell switch until the time the UE transmits the first UL message on the target cell. LTM cell switch delay is defined as: DLTM = Tcmd + TLTM-interrupt. Where: Tcmd equals to THARQ + 3ms, where THARQ is the timing between cell switch command and acknowledgement as specified in TS 38.213. TLTM-interrupt is as stated in clause 6.3.1.3." [38.133 §6.3.1.2, chunkId=38.133-6.3.1.2-001]
- LTM cell switch delay 정의 (PSCell, 더 풍부한 분해):
  > "LTM cell switch delay DLTM is the delay from the end of the last TTI containing the MAC-CE command for cell switch until the time the UE transmits the first UL message on the target cell. … DLTM = Tcmd + TLTM-RRC-processing + TLTM-processing + Tfirst-RS + TRS-proc + TLTM-IU ms" [38.133 §8.20.2, chunkId=38.133-8.20.2-001]
- 추가 RRM 시험 (Neo4j 카탈로그 — 본문 chunk 미인용, 위치만):
  - §A.3.16B LTM Candidate TCI State Configuration / §A.3.16B.2 DLorJoint / §A.3.16B.3 UL.
  - §A.6.3.4 LTM PCell Switch (FR1) / §A.6.3.5 LTM PSCell / §A.6.3.6 CLTM PCell Switch (RACH 기반 / RACH-less).
  - §A.7.3.4 / §A.7.3.5 (FR2 동일).
  - §A.6.6.26~33, §A.6.7.17, §A.7.6.20~29, §A.7.7.15 LTM Intra/Inter-frequency L1-RSRP measurement (with/without measurement gap, gap cancellation 포함).

### 7. 38.306 — UE capability

- 본 retrieval 범위에서 LTM capability는 **§5.4 "Other features"** 와 **§5.6 "RRM measurement features"** 클러스터에 위치한다고 잡혔으나 [38.306 §5.4 / §5.6 검색], 정확한 feature group 번호 (예: `ltm-r18` 같은 plain text capability bit)는 chunk 본문 인용으로 확보되지 않았다.
- §4.2.7.9 `MRDC-Parameters` 가 LTM intra-DU/inter-DU 쿼리에서 매칭됨 [38.306 §4.2.7.9, level=4] → MR-DC 환경에서의 LTM capability 노출 위치로 추정되나 본 retrieval 본문 발췌 부족.
- 결론: **LTM capability 존재는 확인되지만 세부 IE/feature group은 3gpp-tracer 본 검색 범위에서 미확보**. 본문 인용 불가 → 추측 금지.

### 8. Rel-19 확장 (3gpp-tracer 데이터로 도출)

Rel-19 LTM은 RAN2 #126~#131 / RAN1 #118~#118b 토론에서 명시적으로 진행됨이 확인된다 (TDoc 검색 release="Rel-19" 70 hits).
- **inter-CU LTM 도입**: "Intra-CU LTM is supported in Rel-18. The scope of this Rel-19 WI is to extend this to support inter-CU LTM. Inter-CU LTM can be seen as equivalent of inter-gNB LTM." [R2-2404271, RAN2#126, rel=Rel-19, AI=8.6.2, chunkId=R2-2404271-001]
- **subsequent inter-CU LTM**: "Rel-19 inter-CU LTM also supports mixture of subsequent inter-CU LTM and subsequent intra-CU LTM after an inter-CU or intra-CU LTM switch." [R2-2503785, RAN2#130, rel=Rel-19, type=CR, AI=8.6.1, chunkId=R2-2503785-001]
- **Conditional LTM (CLTM)**: "In RAN#105 meeting, the objective related to conditional LTM of Rel-19 Mobility enhancements was agreed …" [R2-2408088, RAN2#127bis, rel=Rel-19, AI=8.6.4, chunkId=R2-2408088-001].
- **Event-triggered L1 measurement reporting**: "Three types of report are defined, namely, periodic, aperiodic and semi-persistent L1 report. For R19 mobility …" [R2-2505117, RAN2#131, rel=Rel-19, AI=8.6.2, chunkId=R2-2505117-001]; "In Rel-19 Mobility enhancement WI, the following objective is proposed to design measurement enhancements for LTM" [R2-2402743, RAN2#125bis, rel=Rel-19, AI=8.6.3].
- **RAN1 측 measurement enhancement**: "In RAN#103 meeting, the work item on NR mobility enhancements Phase 4 was agreed. There are several objectives related with or led by RAN1 …" [R1-2405859, RAN1#118, rel=Rel-19, AI=9.9.1, chunkId=R1-2405859-001]; FL summary: "The following items are further studied in RAN1 for the potential necessary enhancements in Rel-19 LTM. Item 1: CSI acquisition for candidate cell before cell switch. Item 2: Dynamic update of measurement RS or candidate cells …" [R1-2407319, RAN1#118, rel=Rel-19, AI=9.9.1, chunkId=R1-2407319-001].
- **38.321 §5.36 Conditional LTM**, §5.18.35의 *Enhanced* 경로 (`Enhanced LTM Cell Switch Command MAC CE`, §6.1.3.75a), §5.35.3.2~5.35.3.5 Event LTM2~LTM5 — 위 RAN2 토론과 일치하는 **실제 spec 반영물**이 Neo4j 카탈로그에서 확인됨.

요약하면 Rel-19 확장은 **(a) inter-CU LTM, (b) subsequent inter-CU LTM, (c) Conditional LTM 정식 도입, (d) Event-triggered L1 measurement report (Event LTM2~LTM5), (e) candidate cell pre-switch CSI acquisition / measurement RS 동적 갱신** 으로 본 retrieval 안에서 직접 인용 가능하다.

### 9. Rel-20 확장 (3gpp-tracer 데이터로 도출 — 6G 연계 초기 토론 단계)

Rel-20 단계는 RAN2 #132에서 다수 discussion (release="Rel-20" 30 hits), 대부분 **6G/6GR mobility 재설계 컨텍스트**에서 LTM을 정리·평가하는 단계.
- "NR introduced multiple mobility procedures such as L3 handover, Conditional Handover (CHO), Lower layer Triggered Mobility (LTM) and conditional LTM (C-LTM). Each procedure came with its own signalling, configuration, and backward compatibility requirements." [R2-2508706, RAN2#132, rel=Rel-20, type=discussion, AI=10.4 "Connected mobility for 6GR", chunkId=R2-2508706-001]
- "With the introduction of LTM, RAN2 has started using L2 (specifically MAC layer with MAC CEs) to deliver 'critical' mobility control messages to facilitate mobility in a low latency method. …" [R2-2508384, RAN2#132, rel=Rel-20, AI=10.4 "6G Mobility Discussion", chunkId=R2-2508384-001]
- "Mobility is important for the user experience, applications but 5G has extended the sophistication, perhaps much beyond what will ever be deployed. There is too many mobility features …" [R2-2508657, RAN2#132, rel=Rel-20, AI=10.4 "Discussion on 6G Mobility and measurement", chunkId=R2-2508657-001]
- AI=9.3.x 트랙에서는 **AI/ML 기반 RRM measurement event prediction**이 LTM과 결합되는 방향이 토론됨 — "Most of the LCM and related signalling discussions and agreements for AIML mobility during the study item phase in rel-19 used the AIML BM use case as a baseline …" [R2-2508722 / R2-2508707, RAN2#132, rel=Rel-20, AI=9.3.2/9.3.3].

→ Rel-20 단계의 **정식 spec 반영(38.300/331/321 §섹션 추가)** 은 본 retrieval 범위에서 **미발견**. 현재까지는 **discussion/study 단계**로만 적재돼 있으며, "LTM이 6G 모빌리티 베이스라인 후보 / AIML 측정 결합 대상"이라는 방향성까지만 인용 가능하다.

---

## 문서 간 연결고리 다이어그램

```
              ┌─────────────────────────────────────────────────────────┐
              │ 38.300 §9.2.3.5 / §9.2.3.7  (Stage-2 LTM / CLTM 절차)   │
              │  - intra-gNB LTM, SCG LTM, CLTM 흐름도, MAC CE 트리거  │
              └───────────────┬─────────────────────────┬───────────────┘
                              │ RRC config 사전 전달    │ Inter-DU/SCG/Inter-CU
                              ▼                         │
        ┌───────────────────────────────────────┐       │
        │ 38.331 §5.3.5.18 + LTM-* IE 그룹      │       │
        │  LTM-Config / LTM-Candidate /         │       │
        │  LTM-CSI-ReportConfig /               │       │
        │  LTM-ExecutionConditionList /         │       │
        │  SK-CounterConfigLTM / VarLTM-*       │       │
        │  §5.3.5.13.6/.13.8 Subsequent CPAC    │       │
        └─────┬───────────────┬─────────────────┘       │
              │ ltm-CSI-ReportConfig 등           │       │
              │ (RS / 측정·보고 설정)             │       │
              ▼                                    ▼       ▼
   ┌────────────────────────────────┐   ┌────────────────────────────────┐
   │ 38.214 §5.2.4a CSI for LTM     │   │ 38.321 §5.18.35 (Enh) LTM      │
   │ 38.214 §5.2.1.5.4.2 UE-init    │   │   Cell Switch Command          │
   │   eventTriggered L1 report     │   │ 38.321 §5.18.36 Candidate TCI  │
   │ 38.214 §5.2.1.4.3 L1-RSRP      │   │   States Act/Deact MAC CE      │
   │   reporting 일반 정의           │   │ 38.321 §5.18.38 SP CSI-RS for  │
   │                                │   │   candidate cell               │
   │   ▶ candidate cell L1-RSRP /   │   │ 38.321 §5.36 Conditional LTM   │
   │     CSI 결과를 L1/L2 보고      │──▶│ 38.321 §5.35.3.2~3.5 Event     │
   │                                │   │   LTM2~LTM5 (L1 evt-trig)      │
   │                                │   │ 38.321 §5.2b CLTM UL sync      │
   │                                │   │ 38.321 §6.1.3.4b LTM-TA MAC CE │
   └────────────────────────────────┘   └──────────┬─────────────────────┘
                                                   │ MAC CE → 즉시 셀 전환
                                                   ▼
                          ┌─────────────────────────────────────────────┐
                          │ 38.133 §6.3 L1/L2-Triggered Mobility        │
                          │  §6.3.1.2 LTM PCell switch delay            │
                          │   DLTM = Tcmd + TLTM-interrupt              │
                          │  §8.20.2 LTM PSCell switch delay            │
                          │   DLTM = Tcmd + T_RRC + T_proc + Tfirst-RS  │
                          │          + T_RS-proc + T_LTM-IU             │
                          │  §10.1.19D/19E/20A/20B L1-RSRP accuracy     │
                          │  §A.3.16B / §A.6.3.4~6 / §A.7.3.4~5 시험    │
                          └─────────────────────────────────────────────┘
                                                   ▲
                                                   │ UE 지원 capability 협상
                                                   │
                          ┌─────────────────────────────────────────────┐
                          │ 38.306 §5.4 Other features /                │
                          │        §5.6 RRM measurement features /      │
                          │        §4.2.7.9 MRDC-Parameters             │
                          │  ▶ LTM 지원 여부 / FR1·FR2 / intra-DU·      │
                          │    inter-DU·inter-CU 단계별 UE capability   │
                          │    (세부 feature 번호는 본 retrieval 미확보) │
                          └─────────────────────────────────────────────┘
```

흐름 (한 줄 요약):
**38.331 LTM-Config 사전 전달** → **38.214 candidate cell L1-RSRP/CSI 측정·보고** → **38.321 (Enh)LTM Cell Switch / Candidate TCI Activation MAC CE 트리거** → **38.300 §9.2.3.5 절차로 셀 전환 (subsequent LTM 반복)** → **38.133 §6.3 시간/정확도 요구 충족** ↔ **38.306 capability로 지원 단계 협상**.

---

## 커버리지 / 한계

| 항목 | 상태 | 근거 |
|---|---|---|
| 38.300 LTM 절차 본문 | OK | §9.2.3.5.2, §9.2.3.7.1 chunk 직접 인용 |
| 38.331 LTM-Config / candidate / L3-trigger 본문 | OK | §5.3.5.18.1, .18.3, .18.8 chunk 직접 인용 + Neo4j 노드 18개 |
| 38.321 LTM Cell Switch / TCI activation MAC CE 본문 | OK | §5.18.35, §5.18.36, §6.1.3.75, §6.1.3.76 chunk 직접 인용 |
| 38.214 candidate cell L1 측정·보고 본문 | OK | §5.2.4a, §5.2.1.5.4.2, §5.2.1.4.3 chunk 직접 인용 |
| 38.133 LTM cell switch delay 정의 본문 | OK | §6.3.1.2, §8.20.2 chunk 직접 인용 + LTM 전용 시험 56 노드 카탈로그 |
| 38.306 LTM UE capability 세부 IE | **부분 — 위치만** | §5.4 / §5.6 / §4.2.7.9 매칭, **세부 feature group 본문 미확보** |
| Rel-18 도입 동기 (latency/overhead/interruption) | OK | R2-2207340, R2-2301501, R1-2302414, R1-2311212 |
| Rel-18 정확한 RP-WID 본문 | **미확보** | R2-2207340이 RP-221799를 reference 인용. RP-* TDoc 자체는 retrieval 범위 미포함 |
| Rel-19 inter-CU LTM / CLTM / event-trig L1 | OK | R2-2404271, R2-2503785, R2-2408088, R2-2505117, R2-2402743 |
| Rel-19 RAN1 measurement enhancement | OK | R1-2405859, R1-2407319 (FL summary) |
| Rel-20 spec 반영 | **미확보 (study 단계)** | RAN2#132 discussion만 (R2-2508706, R2-2508384, R2-2508657 등). 38.300/331/321의 Rel-20 §섹션 신규 추가는 본 retrieval에서 미검출 |
| RAN4 RRM Rel-18 본격 토론 | OK | R4-2400104 (RAN4#110, "RRM performance requirements for R18 LTM") |
| 38.306 LTM UE capability 세부 feature group | **미발견** | 본 retrieval 범위에서 chunk 본문 미확보 |
| LTM 전용 timer (T-LTM) 본문 | **미확보** | 38.321 §5.2b / §6.1.3.4b 위치만 매칭, 본문 발췌 부족 |

### 답변 가능 수준
3gpp-tracer 검색 결과만으로 **Rel-18 LTM의 6개 spec(38.300/331/321/214/133/306) 핵심 절·IE·MAC CE·delay 공식·도입 배경을 직접 인용으로 답변 가능**. **Rel-19 확장(inter-CU LTM, Conditional LTM, event-triggered L1 report, candidate cell CSI acquisition)도 RAN1/RAN2 TDoc + Neo4j spec 노드로 정합성 있게 답변 가능**. 단 **Rel-20은 RAN2#132 토론 단계까지만 인용 가능**하고 spec 반영 본문은 미발견. **38.306 LTM 세부 feature group 번호와 LTM 전용 timer 본문**은 본 retrieval로는 확정 인용 불가 — 추가 쿼리 또는 spec 본문 직접 적재 확인 필요.
