# Rel.18 LTM (L1/L2 Triggered Mobility) 표준 분석 및 Rel.19/20 진화 보고서

## 목차
1. [LTM 도입 배경](#1-ltm-도입-배경)
2. [38.300 — LTM 개념 및 Architecture](#2-38300--ltm-개념-및-architecture)
3. [38.331 — RRC Parameter](#3-38331--rrc-parameter)
4. [38.321 — MAC-CE 동작](#4-38321--mac-ce-동작)
5. [38.214 — L1 Measurement 및 Reporting](#5-38214--l1-measurement-및-reporting)
6. [38.133 — RRM 요구사항](#6-38133--rrm-요구사항)
7. [38.306 — UE Capability](#7-38306--ue-capability)
8. [Rel.19 — LTM 확장](#8-rel19--ltm-확장)
9. [Rel.20 — LTM 진화 방향](#9-rel20--ltm-진화-방향)
10. [문서 간 연결 구조](#10-문서-간-연결-구조)

---

## 1. LTM 도입 배경

### 1.1 기존 Handover 한계

NR Rel.15부터 사용된 mobility 기법:

| 기법 | Release | Latency | 문제점 |
|---|---|---|---|
| L3 Handover (RRC reconfig.) | Rel.15 | 50~100 ms | RRC signaling 무거움, interruption 큼 |
| Conditional Handover (CHO) | Rel.16 | 20~50 ms | 여전히 RRC level |
| DAPS Handover | Rel.16 | ~수십 ms | UL data lossless, but 복잡 |

특히 **FR2 환경의 빠른 beam 변동**과 **dense small cell 환경의 잦은 cell change**에서는 위 latency가 user experience를 저하시킨다.

### 1.2 WID: RP-234037 (NR_Mob_enh_Ph4)

Rel.18 mobility enhancement WID는 다음을 핵심 objective로 명시:

> *"Specify L1/L2-based inter-cell mobility (LTM) procedure to reduce mobility latency and interruption time, leveraging the existing beam management framework."*

### 1.3 핵심 컨셉

LTM의 핵심 idea는 **cell change를 RRC 재구성 없이 MAC-CE 또는 DCI로 trigger**하는 것이다.

```
[Conventional HO]                  [LTM (Rel.18)]
                                   
RRC Reconfig (Source)              RRC Reconfig with candidate config (Source) [pre-configured]
   ↓                                   ↓ (사전에 미리)
RRC Reconfig (Target)              MAC-CE 또는 DCI로 cell switch
   ↓                                   ↓
~50 ms interruption                <20 ms interruption
```

### 1.4 LTM의 차별점

- **Pre-configuration**: 후보 cell들을 미리 RRC로 설정
- **Dynamic activation**: MAC-CE 또는 DCI로 즉시 cell switch
- **Beam-cell unified management**: TCI framework 위에서 beam과 cell을 통합 관리
- **Lower layer measurement 활용**: L3 measurement 대신 L1 measurement 활용

---

## 2. 38.300 — LTM 개념 및 Architecture

### 2.1 LTM의 위치 (Clause 9.2.x)

38.300에서 LTM은 다음과 같이 정의:

> *"L1/L2 triggered mobility (LTM) is a mechanism for fast inter-cell mobility within a single Master Node (MN) where candidate target cells are pre-configured via RRC and the cell switch is triggered by L1/L2 signaling (MAC CE or DCI)."*

### 2.2 Architecture 가정

#### 2.2.1 적용 범위
- **Intra-DU LTM**: 동일 gNB-DU 내 cell change (latency 가장 작음)
- **Intra-CU/Inter-DU LTM**: 동일 gNB-CU, 다른 DU 간 (Rel.18 working assumption)
- **Inter-gNB**: Rel.18에서는 미지원 (Rel.19+ candidate)

#### 2.2.2 Source ↔ Target Cell 관계
- 동일 frequency 또는 다른 frequency 가능
- 동일 또는 다른 PCI(Physical Cell Identifier)
- 동일 gNB-CU에서 관리됨이 가정

### 2.3 LTM 절차 개요 (38.300 Clause 9.2.x)

```
[Step 1: Pre-configuration phase]
   Source cell ─── RRC Reconfiguration with candidate cell list ───> UE
                   (CandidateCellInfoListLTM)

[Step 2: Measurement phase]
   UE ─── L1 measurement on candidate cell SSB/CSI-RS ───> Source cell
        (per-cell L1-RSRP / L1-SINR reporting)

[Step 3: Cell switch trigger]
   Source cell ─── MAC-CE (LTM Cell Switch Command) ───> UE
        OR ─── DCI Format X (LTM trigger) ───> UE

[Step 4: Cell switch execution]
   UE: Apply target cell configuration (TCI, BWP, RACH, ...) without RRC reconfig

[Step 5: Optional RACH-less / RACH-based access]
   - RACH-less: TA reuse from pre-config
   - RACH-based: Random access on target cell

[Step 6: Confirmation]
   UE ─── PDCCH 수신 on target cell ───> 절차 완료
```

### 2.4 Cell Group과의 관계

LTM은 **MCG (Master Cell Group)** 내에서 동작. SCG (Secondary Cell Group)는 Rel.18 LTM 범위 외이며, 향후 release 검토 대상.

---

## 3. 38.331 — RRC Parameter

### 3.1 CandidateCellInfoListLTM-r18

LTM의 핵심 RRC IE. Source cell이 UE에 후보 cell들을 미리 설정.

```asn1
CandidateCellInfoListCPC-LTM-r18 ::= SEQUENCE (SIZE (1..maxNrofCandidateCells-r18)) 
    OF CandidateCellInfo-LTM-r18

CandidateCellInfo-LTM-r18 ::= SEQUENCE {
    physCellId-r18              PhysCellId,
    ssbFrequency-r18            ARFCN-ValueNR  OPTIONAL,
    candidateConfigId-r18       CandidateCellConfigId-r18,
    rrcReconfiguration-r18      OCTET STRING (CONTAINING RRCReconfiguration),
    -- 위는 기존 CHO와 유사
    
    -- LTM 신규 부분
    ltm-CellId-r18              LTM-CellId-r18,
    ltm-CandidateConfig-r18     LTM-CandidateConfig-r18,
    ...
}

LTM-CandidateConfig-r18 ::= SEQUENCE {
    rach-ConfigGenericLTM-r18       RACH-ConfigGenericLTM-r18  OPTIONAL,
    timingAdjustmentLTM-r18         INTEGER (-127..128)  OPTIONAL,  -- TA pre-config
    ssbToTrack-r18                  SEQUENCE OF SSB-Index  OPTIONAL,
    csiRS-ResourceList-r18          SEQUENCE OF NZP-CSI-RS-ResourceId  OPTIONAL,
    tciStateList-r18                SEQUENCE OF TCI-StateId  OPTIONAL,
    ...
}
```

### 3.2 LTM 활성화 관련 IE

```asn1
PDCCH-Config ::= SEQUENCE {
    ...,
    [[
    -- Rel.18
    candidateCellSwitchTriggerConfig-r18    SetupRelease { CandidateCellSwitchTriggerConfig-r18 } OPTIONAL
    ]]
}

CandidateCellSwitchTriggerConfig-r18 ::= SEQUENCE {
    triggerMethod-r18           ENUMERATED { mac-CE, dci, both },
    targetCellList-r18          SEQUENCE OF LTM-CellId-r18,
    cellSwitchTimer-r18         ENUMERATED {ms10, ms20, ...} OPTIONAL,
    ...
}
```

### 3.3 L1 Measurement 설정 확장

```asn1
CSI-MeasConfig ::= SEQUENCE {
    ...,
    [[
    candidateCellMeasConfigLTM-r18  SEQUENCE OF CandidateCellMeasLTM-r18  OPTIONAL
    ]]
}

CandidateCellMeasLTM-r18 ::= SEQUENCE {
    candidateCellId-r18         LTM-CellId-r18,
    measResource-r18            CHOICE {
        ssb         SSB-Index,
        csi-rs      NZP-CSI-RS-ResourceId
    },
    reportConfig-r18            CSI-ReportConfigId
}
```

### 3.4 핵심 IE 의미 정리

| IE | 의미 |
|---|---|
| `CandidateCellInfoListCPC-LTM-r18` | 후보 cell 사전 설정 list (최대 8 또는 16) |
| `LTM-CandidateConfig-r18` | 각 후보의 RACH, TA, TCI, BWP 설정 |
| `candidateCellSwitchTriggerConfig-r18` | trigger 방법 (MAC-CE / DCI) 선택 |
| `cellSwitchTimer-r18` | switch 절차 timeout |
| `candidateCellMeasConfigLTM-r18` | 후보 cell의 SSB/CSI-RS L1 측정 설정 |
| `timingAdjustmentLTM-r18` | TA pre-config (RACH-less switch용) |
| `ssbToTrack-r18` | 후보 cell에서 monitor할 SSB index |

---

## 4. 38.321 — MAC-CE 동작

### 4.1 신규 MAC-CE: LTM Cell Switch Command MAC CE

38.321 Clause 5.x.y에 다음 MAC-CE가 정의된다 (LCID 별도 할당, R18에서 신규):

```
| R | R | T  | Candidate Cell Configuration ID (5 bits) |   ← octet 1
| TCI State ID  (7 bits)               | R                |   ← octet 2
| BWP ID (2)| R | R | R | R | R | R              |        ← octet 3 (선택적)
...
```

#### Field 의미:
- **T (Type)**: switch type (RACH-less / RACH-based)
- **Candidate Cell Configuration ID**: pre-configured candidate 중 어느 것 사용
- **TCI State ID**: 활성화할 beam (target cell의 TCI list 참조)
- **BWP ID**: target cell에서 활성화할 BWP

### 4.2 LTM 절차 (MAC 관점) — Clause 5.x

```
[T = 0]: MAC-CE for LTM cell switch 수신
[T = T1]: MAC-CE 처리 시작 (HARQ ACK 후)
[T = T1 + T_apply]: LTM cell switch 적용
   - Source cell의 RRC connection 유지 (PHY는 target으로 변경)
   - Target cell의 PHY/MAC config 적용
   - TCI activation (target 내 indicated TCI)
   - BWP switch (target의 indicated BWP)
   
[T = T1 + T_apply + T_RACH (선택)]: RACH 절차 (necessary 시)
   - timingAdjustmentLTM 사용 시 RACH-less
   - 그 외 4-step RA
   
[T = T1 + T_total]: Target cell PDCCH monitoring 시작
```

T_apply는 38.133에서 정의 (typical: 수 ms ~ 수십 ms).

### 4.3 RACH-less LTM

UE가 source cell에 있을 때 candidate cell들의 TA를 미리 알려받고:
- `timingAdjustmentLTM-r18`: 기존 source TA로부터 derive 또는 explicit
- Target cell의 SSB/CSI-RS 측정으로 TA 보정 가능 시 RACH 생략

### 4.4 LTM과 BFR/Beam Management의 관계

LTM cell switch 후:
- **TCI re-activation** 필요 (38.321 unified TCI activation MAC CE)
- BFR procedure는 새 cell context로 reset
- beamFailureInstanceMaxCount 카운터 reset

### 4.5 DCI-Triggered LTM

MAC-CE 외에 **DCI-based trigger** 도입 (Rel.18 working assumption 일부 → final spec 확인 필요):
- 새 DCI Format 또는 기존 DCI의 reserved field 활용
- MAC-CE 대비 더 빠른 trigger latency
- 단, payload 작아 simple trigger만 가능 (full config는 RRC pre-config에 의존)

---

## 5. 38.214 — L1 Measurement 및 Reporting

### 5.1 Candidate Cell L1 Measurement (Clause 5.1.6 확장)

UE가 LTM 후보 cell들에 대해 수행할 L1 측정:

#### 5.1.1 측정 대상
- Candidate cell의 SSB (SS-RSRP, SS-SINR)
- Candidate cell의 CSI-RS (CSI-RSRP, CSI-SINR)
- 단, 후보 cell의 RS는 source cell이 사전 알려준 시간/주파수 자원에 위치

#### 5.1.2 측정 주기
- SSB: 후보 cell의 SSB periodicity (typical 20 ms)
- CSI-RS: RRC `periodicityAndOffset` 따름
- 측정 윈도우: source cell이 정의 가능 (UE의 measurement gap 활용)

### 5.2 L1 Reporting for LTM (Clause 5.2.1.4 확장)

#### 5.2.1 Report Quantity 확장

기존 CSI-ReportConfig의 `reportQuantity`에 LTM 관련 quantity 추가:

```
reportQuantity ENUMERATED {
    none, cri-RI-PMI-CQI, ...,
    cri-RSRP-r17,
    -- Rel.18 신규
    cri-RSRP-Index-r18,                  -- per-cell
    ssb-Index-RSRP-LTM-r18,
    cell-Quality-LTM-r18                 -- aggregated cell-level
}
```

#### 5.2.2 Per-Cell L1 Report

UE가 candidate cell별로 다음 정보 보고:
- Cell ID (또는 candidate config ID)
- 가장 좋은 SSB index 또는 CSI-RS resource index
- Corresponding L1-RSRP (또는 L1-SINR)

#### 5.2.3 Reporting Trigger
- **Periodic**: PUCCH로 주기 보고
- **Aperiodic**: DCI 또는 MAC-CE trigger 시
- **Event-triggered**: 후보 cell의 L1-RSRP가 source 대비 일정 dB 우위 시 (Rel.18 enhancement)

### 5.3 L3 Filtering 우회

LTM은 fast switching이 목적이므로 **L3 filtering (smoothing)을 우회**:
- 기존 L3 measurement: SS-RSRP에 layer 3 filter 적용 (수백 ms ~ 초 단위 smoothing)
- LTM L1 measurement: filter 없이 즉시 보고 (수 ms ~ 수십 ms)

### 5.4 Resource Mapping 가정

UE는 candidate cell의 SSB/CSI-RS 위치를 source cell의 frame structure 기준으로 알아야 한다:
- `ssbFrequency-r18`: 후보 cell의 SSB frequency
- 후보 cell의 SCS, slot offset 등이 RRC로 미리 제공됨

---

## 6. 38.133 — RRM 요구사항

### 6.1 Candidate Cell Measurement Requirement (Clause 9.x)

#### 6.1.1 Measurement Period

UE는 다음 시간 내에 candidate cell의 RSRP를 측정 가능:

$$T_{\text{LTM\_meas}} = N \cdot T_{\text{SSB}} + T_{\text{processing}}$$

여기서 N은 SSB sample 수 (typical 1~5), T_SSB는 SSB periodicity.

Typical 값: **20~100 ms** (FR1), **40~200 ms** (FR2)

#### 6.1.2 Measurement Accuracy

Candidate cell의 L1-RSRP 측정 정확도:
- ±6 dB (FR1, normal condition)
- ±9 dB (FR2)

### 6.2 LTM Cell Switch Latency Requirement

#### 6.2.1 Total Switch Time

```
T_total = T_signaling + T_apply + T_RACH (if applicable) + T_PDCCH_acquisition
```

각 component의 typical 요구:
- T_signaling: MAC-CE 수신 + ACK = ~5 ms
- T_apply: target cell config 적용 = ~10 ms (FR1), ~15 ms (FR2)
- T_RACH (RACH-based): ~10 ms additional
- T_RACH (RACH-less): 0 ms
- T_PDCCH_acquisition: ~수 ms

**Target total**: 20~30 ms (RACH-less), 40~50 ms (RACH-based)

이는 기존 L3 HO (50~100 ms) 대비 50%+ 단축.

#### 6.2.2 Interruption Time

User plane (PDCCH/PDSCH) 끊김 시간:
- LTM RACH-less: ≤ 15 ms (FR1)
- LTM RACH-based: ≤ 30 ms (FR1)
- 이는 38.133에서 정량화

### 6.3 측정 Capability 요구

UE는 source cell 측정과 candidate cell 측정을 동시에 수행 가능해야 한다:
- Same frequency: 추가 부담 없음
- Different frequency (intra-band): minor impact
- Different frequency (inter-band): measurement gap 사용 가능

### 6.4 Candidate Cell 수

UE가 동시에 monitor 가능한 candidate cell 수:
- 최소 4 cells
- UE capability `maxNumberCandidateCellsLTM-r18`에 따라 8 또는 16

### 6.5 Test Configuration 예 (38.133)

| Parameter | Value |
|---|---|
| Source cell SS-RSRP | -90 dBm |
| Candidate cell A SS-RSRP | -85 dBm (5 dB stronger) |
| Cell switch trigger | MAC-CE at T = T0 |
| Required: T_total | < 30 ms (RACH-less) |
| Pass criterion | UE acquires PDCCH on target by T0 + 30 ms |

---

## 7. 38.306 — UE Capability

### 7.1 LTM Capability Field

```
ltm-r18: ENUMERATED { supported }
ltm-IntraDU-r18: ENUMERATED { supported }
ltm-InterDU-r18: ENUMERATED { supported }  -- optional, separate
ltm-RACHless-r18: ENUMERATED { supported }
ltm-MAC-CE-r18: ENUMERATED { supported }
ltm-DCI-r18: ENUMERATED { supported }
maxNumberCandidateCellsLTM-r18: ENUMERATED { n4, n8, n16 }
maxNumberCandidateConfigsLTM-r18: ENUMERATED { n8, n16, n32 }
```

### 7.2 Per-Band Capability

UE는 band별로 다음 신고:
- `ltm-Supported-FR1` / `ltm-Supported-FR2`
- `ltm-MeasurementCapability`: 동시 측정 가능 candidate 수
- `ltm-CellSwitchInterruptionTime`: switching time 분류

### 7.3 Cross-Capability 조건

LTM 사용은 다음 capability 동반 필요:
- `unifiedTCI-StateMode-r17` (Rel.17 unified TCI 의존)
- `tciState-r17` (DL/UL unified TCI)
- `bwp-Operation` (BWP switching capability)

---

## 8. Rel.19 — LTM 확장

### 8.1 도입 배경 (WID: NR_Mob_enh_Ph5, RP-234041 / RP-242630 등)

Rel.18 LTM은 intra-CU에 한정된 첫 단계였다. Rel.19에서는 다음을 확장:

1. **Inter-CU LTM**: 다른 gNB-CU 간 fast cell switch
2. **SCG LTM**: Secondary Cell Group의 LTM 적용
3. **Conditional LTM (CLTM)**: CHO와 LTM의 hybrid — UE가 자율 trigger
4. **AI/ML 기반 LTM trigger**: 측정 예측 기반 proactive LTM

### 8.2 38.331 확장

```asn1
-- Rel.19 working draft
LTM-Configuration-r19 ::= SEQUENCE {
    interCU-Support-r19         BOOLEAN,
    candidateCellInfoSCG-r19    SEQUENCE OF CandidateCellInfo-LTM-SCG-r19  OPTIONAL,
    conditionalLTM-r19          ConditionalLTM-Config-r19  OPTIONAL,
    ...
}

ConditionalLTM-Config-r19 ::= SEQUENCE {
    triggerCondition-r19    SEQUENCE {
        l1RsrpThreshold-r19     RSRP-Range,
        timeToTrigger-r19       INTEGER (0..1024)  -- ms 단위
    },
    autoExecute-r19         BOOLEAN
}
```

### 8.3 38.321 확장

- **Inter-CU LTM MAC-CE**: source CU와 target CU 간 context transfer 절차 동반
- **Conditional LTM MAC-CE**: 조건 충족 시 UE 자율 cell switch (CHO와 유사하나 L1/L2 단)

### 8.4 38.214 확장

L1 measurement 확장:
- **AI/ML-aided measurement prediction**: 부분 측정으로 candidate cell 품질 예측
- **Reduced measurement overhead**: subset measurement

### 8.5 38.133 확장

- Inter-CU LTM의 latency requirement (typical 30~50 ms)
- SCG LTM의 latency
- Conditional LTM의 trigger 평가 시간

### 8.6 38.306 확장

```
ltm-InterCU-r19
ltm-SCG-r19
ltm-Conditional-r19
ltm-AIAssisted-r19
```

---

## 9. Rel.20 — LTM 진화 방향

### 9.1 Rel.20 SI/WI 진행 (현재 시점 기준)

Rel.20에서 진행 중이거나 candidate인 LTM 관련 작업:

1. **Multi-RAT LTM**: NR-DC, NR-LTE inter-RAT LTM
2. **NTN LTM**: 위성 환경에서의 LTM (큰 propagation delay 고려)
3. **Group-based LTM**: 여러 UE가 함께 cell switch (V2X, IIoT 시나리오)
4. **LTM with full AI/ML**: 완전 자율 prediction-based LTM

### 9.2 잠재적 RRC 확장 (TBD)

```asn1
-- Rel.20 candidate (확정 아님)
LTM-Configuration-r20 ::= SEQUENCE {
    interRAT-LTM-r20            ENUMERATED { supported, notSupported }  OPTIONAL,
    ntn-LTM-r20                 NTN-LTM-Config-r20  OPTIONAL,
    groupLTM-r20                Group-LTM-Config-r20  OPTIONAL,
    aiml-LTM-r20                AI-ML-LTM-Config-r20  OPTIONAL,
    ...
}
```

### 9.3 NTN 환경 특이사항

NTN(Non-Terrestrial Network)에서의 LTM은 특별 고려 필요:
- 위성 이동 속도가 빨라 source cell 자체가 빠르게 변동
- TA 변화율 큼 → RACH-less LTM이 더 매력적
- Doppler shift 보정이 LTM 절차에 통합 필요

---

## 10. 문서 간 연결 구조

### 10.1 LTM의 End-to-End 흐름과 문서 매핑

```
[Phase 0: Setup]
   ┌────────────────────────────────────────┐
   │ 38.300 §9.2:                            │
   │ Architecture, intra/inter-DU 정의       │
   │ Source ↔ Target 관계 정의               │
   └─────────────────────┬──────────────────┘
                         │
   ┌─────────────────────▼──────────────────┐
   │ 38.331:                                 │
   │ - CandidateCellInfoListCPC-LTM-r18      │
   │ - LTM-CandidateConfig (RACH, TA, TCI)   │
   │ - candidateCellMeasConfigLTM-r18        │
   │ - candidateCellSwitchTriggerConfig-r18  │
   └─────────────────────┬──────────────────┘
                         │ Pre-configuration 완료
                         │
[Phase 1: Measurement]   │
                         ▼
   ┌────────────────────────────────────────┐
   │ 38.214 §5.1.6, §5.2:                    │
   │ - candidate cell SSB/CSI-RS L1 측정     │
   │ - cri-RSRP-Index-r18 등 보고            │
   │ - Per-cell, per-beam L1-RSRP            │
   └─────────────────────┬──────────────────┘
                         │
   ┌─────────────────────▼──────────────────┐
   │ 38.133 §9.x:                            │
   │ - Measurement period (T_LTM_meas)       │
   │ - Accuracy ±6/±9 dB                     │
   └─────────────────────┬──────────────────┘
                         │
[Phase 2: Trigger]       │
                         ▼
   ┌────────────────────────────────────────┐
   │ 38.321:                                 │
   │ - LTM Cell Switch MAC-CE                │
   │ - Candidate config ID, TCI ID, BWP ID   │
   │ - Trigger 처리 → cell switch 시작       │
   └─────────────────────┬──────────────────┘
                         │
[Phase 3: Execution]     │
                         ▼
   ┌────────────────────────────────────────┐
   │ 38.321 + 38.214 + 38.211:               │
   │ - Target cell PHY config 적용           │
   │ - TCI activation (Unified TCI)          │
   │ - BWP switch                            │
   │ - RACH (선택) 또는 RACH-less            │
   └─────────────────────┬──────────────────┘
                         │
   ┌─────────────────────▼──────────────────┐
   │ 38.133:                                 │
   │ - T_apply, T_total 요구사항 검증        │
   │ - Interruption time bound               │
   └─────────────────────┬──────────────────┘
                         │
[Phase 4: Capability     │
         Validation]     │
                         ▼
   ┌────────────────────────────────────────┐
   │ 38.306:                                 │
   │ - UE의 LTM 지원 신고                   │
   │ - candidate 수, switching time class    │
   └────────────────────────────────────────┘
```

### 10.2 핵심 정합성 매트릭스

| 항목 | 38.300 | 38.331 | 38.321 | 38.214 | 38.133 | 38.306 |
|---|---|---|---|---|---|---|
| 후보 cell 정의 | concept | CandidateCellInfo IE | (사용) | meas config | meas requirement | maxNumberCandidate |
| Cell switch trigger | concept | triggerMethod (mac-CE/dci) | MAC-CE 포맷 | — | latency req | trigger 지원 |
| Pre-config TA | concept | timingAdjustmentLTM | (사용) | — | TA accuracy | RACH-less 지원 |
| TCI 적용 | TCI framework | tciStateList | Unified TCI activation | TCI-state | TCI activation latency | unifiedTCI-StateMode |
| L1 measurement | concept | measResource | (보고 처리) | report quantity | meas period | L1 measurement |
| Interruption time | concept | cellSwitchTimer | timer 처리 | — | bound 정의 | interruption class |

### 10.3 의존성 트리

```
LTM (Rel.18)
  │
  ├─[depends on]─ Unified TCI Framework (Rel.17)
  │                  └─ TCI-State, MAC-CE activation
  │
  ├─[depends on]─ BWP Operation (Rel.15)
  │                  └─ BWP switching mechanism
  │
  ├─[depends on]─ Beam Management (Rel.15+)
  │                  └─ L1-RSRP measurement, reporting
  │
  ├─[extends]──── Conditional Handover (Rel.16)
  │                  └─ pre-configuration concept
  │
  └─[interacts with]─ BFR (Rel.15+)
                       └─ Beam failure → potential LTM trigger
```

### 10.4 Rel.18 → Rel.19 → Rel.20 진화 매트릭스

| 측면 | Rel.18 (Initial LTM) | Rel.19 (Extended) | Rel.20 (Future) |
|---|---|---|---|
| **Scope (38.300)** | Intra-CU (intra/inter-DU) | + Inter-CU, SCG | + Inter-RAT, NTN, Group |
| **RRC (38.331)** | CandidateCellInfoListCPC-LTM | + ConditionalLTM-Config, SCG candidate | + NTN-LTM, Group-LTM |
| **MAC-CE (38.321)** | LTM Cell Switch MAC CE | + Inter-CU MAC CE, Conditional LTM | + AI-driven MAC CE |
| **L1 Meas (38.214)** | Per-cell L1-RSRP | + AI/ML-aided prediction | + Full AI inference |
| **RRM (38.133)** | Intra-DU latency 요구 | + Inter-CU, SCG latency | + NTN, group latency |
| **Capability (38.306)** | ltm-IntraDU, ltm-RACHless | + ltm-InterCU, ltm-Conditional | + ltm-AIML, ltm-NTN |

### 10.5 구체 실행 시나리오 (예: FR2 RACH-less LTM)

```
T = -1000 ms: Source cell이 UE에게 RRC Reconfiguration 송신
              - Candidate Cell A, B, C 정보 (PCI, frequency, SSB, ...)
              - LTM-CandidateConfig (TA pre-config, TCI, BWP)
              - candidateCellMeasConfigLTM 활성

T = -500 ms ~ T = 0 ms: UE가 candidate cells L1-RSRP 측정
              - Cell A: -100 dBm
              - Cell B: -85 dBm (가장 좋음)
              - Cell C: -110 dBm
              - PUCCH/PUSCH로 cri-RSRP-Index-r18 보고

T = 0 ms: gNB가 LTM Cell Switch MAC CE 송신
          - Candidate Config ID = 2 (Cell B)
          - TCI State ID = 5
          - BWP ID = 1
          - Type = RACH-less

T = 1 ms: UE가 MAC-CE HARQ ACK 송신

T = 5 ms: UE가 LTM 절차 적용 시작
          - Source cell PHY 중단
          - Target cell B의 PHY config 적용 (TCI 5, BWP 1)
          - timingAdjustmentLTM 적용 (TA = -25 sample 등)

T = 12 ms: UE가 target cell B의 PDCCH monitoring 시작

T = 18 ms: 첫 PDCCH 수신 (DCI on target cell)
=> Total = 18 ms < 30 ms (38.133 spec for RACH-less LTM) ✓
=> Interruption time = 12 ms < 15 ms ✓
```

---

## 11. 결론

### 11.1 LTM의 표준적 의의

LTM은 NR mobility의 architectural transformation이다:

1. **L3 → L1/L2 Mobility**: cell change의 latency를 50%+ 단축
2. **Pre-configuration paradigm**: dynamic decision의 부담을 RRC 단에서 사전 처리로 이전
3. **Beam-Cell unified management**: TCI framework 위에서 beam과 cell 관리 통합
4. **Foundation for future enhancements**: AI/ML mobility, NTN mobility의 base가 됨

### 11.2 Cross-Document 설계 철학

LTM은 단일 문서에서 정의되지 않고, 다음과 같은 **cross-layer 설계**의 모범 사례이다:

- Concept (38.300) → RRC config (38.331) → MAC procedure (38.321) → PHY measurement (38.214) → RRM bound (38.133) → Capability (38.306)
- 각 layer가 명확한 책임 분담과 interface 가지고, layer 간 정합성이 spec 단에서 보장됨

### 11.3 향후 진화

Rel.19/20로 갈수록:
- **Spatial scope 확장**: intra-CU → inter-CU → inter-RAT → NTN
- **Intelligence 강화**: rule-based → AI/ML predicted
- **Group operation**: per-UE → per-group (V2X, IIoT)

이러한 진화는 모두 Rel.18 LTM이 정립한 **"pre-configure + L1/L2 trigger"** paradigm을 확장하는 형태로 진행된다.

---

*문서 참조: TS 38.300 v18.x, TS 38.331 v18.x, TS 38.321 v18.x, TS 38.214 v18.x, TS 38.133 v18.x, TS 38.306 v18.x, RP-234037, RP-234041*

*※ 본 보고서는 작성 시점(2026년 4월)에서 Rel.18은 frozen, Rel.19는 frozen 또는 finalization 단계, Rel.20은 SI/WI 진행 중인 상황을 반영. Rel.19/20 spec 세부사항은 최종 publication 시점에 변동 가능.*
