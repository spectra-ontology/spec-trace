# NR TCI-State 표준 진화 분석 보고서 (Rel.15 ~ Rel.20)

## 목차
1. [TCI-State 개념 개요](#1-tci-state-개념-개요)
2. [Rel.15 — TCI-State의 도입](#2-rel15--tci-state의-도입)
3. [Rel.16 — Multi-TRP 및 URLLC 확장](#3-rel16--multi-trp-및-urllc-확장)
4. [Rel.17 — Unified TCI Framework](#4-rel17--unified-tci-framework)
5. [Rel.18 — UL Tx Switching, MIMO Evolution과 LTM 연계](#5-rel18--ul-tx-switching-mimo-evolution과-ltm-연계)
6. [Rel.19 — AI/ML 기반 Beam Management 연계](#6-rel19--aiml-기반-beam-management-연계)
7. [Rel.20 — 진화 방향](#7-rel20--진화-방향)
8. [문서 간 연결 구조 (전체 release 통합)](#8-문서-간-연결-구조)

---

## 1. TCI-State 개념 개요

**TCI (Transmission Configuration Indicator) State**는 NR에서 **DL/UL 신호 간의 spatial 및 large-scale parameter 관계**를 추상화하는 핵심 framework이다. 다음 두 정보를 캡슐화한다:

- **QCL (Quasi Co-Location) 관계**: 하나의 RS와 다른 RS 간의 channel property 공유 관계
- **Beam 식별자**: UE가 어떤 spatial filter(=beam)를 사용해야 하는지 indication

QCL Type은 4가지로 정의된다:
- **Type A**: Doppler shift, Doppler spread, average delay, delay spread
- **Type B**: Doppler shift, Doppler spread
- **Type C**: Doppler shift, average delay
- **Type D**: Spatial Rx parameter (=beam)

**Type D**가 사실상 "beam" 정보이며, FR2(mm-wave) 대역에서 핵심적 역할을 한다.

---

## 2. Rel.15 — TCI-State의 도입

### 2.1 도입 배경 (WID: RP-170739, RP-181433)

NR Rel.15 SI/WI는 mm-wave 대역(FR2) 운영을 처음부터 고려했고, 다음 요구사항을 제시했다:

> *"Specify mechanism to support analog beamforming-based transmission and reception, including beam indication for both downlink and uplink."*

LTE는 cell-specific reference signal에 기반한 omni-directional 송신을 가정했지만, NR은 **beamforming이 default**가 되어야 한다. 이를 위해 도입된 framework가 TCI-state이다.

### 2.2 38.214 — QCL Assumption (Rel.15)

#### 2.2.1 PDSCH의 QCL Source (Clause 5.1.5)

UE는 PDSCH의 DM-RS port가 다음 RS와 QCL 관계라고 가정:
- DCI에 의해 indicated된 TCI-state (M개의 후보 중 하나)
- TCI field가 DCI에 없으면, default rule 적용 (가장 최근 activated CORESET의 TCI)

**Rel.15에서는 PDSCH TCI field가 DCI Format 1_1에만 존재**했다.

#### 2.2.2 PDCCH의 QCL Source (Clause 5.1.5)

각 CORESET에 대해 TCI-state가 RRC로 list 설정 후 MAC-CE로 1개 active:
- CORESET 0 (PBCH-config): SS/PBCH block과 QCL'd (default)
- CORESET >0: TCI-StatesPDCCH-ToAddList로 후보 설정 → MAC-CE로 1개 활성화

#### 2.2.3 CSI-RS의 QCL

각 NZP-CSI-RS-Resource는 `qcl-InfoPeriodicCSI-RS` 또는 dynamic 활성화로 TCI-state와 연결.

### 2.3 38.321 — MAC-CE 절차 (Rel.15)

| MAC-CE | LCID | 기능 |
|---|---|---|
| TCI States Activation/Deactivation for UE-specific PDSCH MAC CE | 53 | RRC로 설정된 64개 candidate 중 8개를 activate (3-bit indication 가능) |
| TCI State Indication for UE-specific PDCCH MAC CE | 52 | CORESET별 1개 TCI 활성화 |
| Aperiodic CSI Trigger State Subselection MAC CE | 47 | CSI trigger state 선택 |

#### MAC-CE 포맷 예 (PDSCH TCI Activation):

```
| Serving Cell ID (5 bits) | BWP ID (2 bits) | R |
| T0 (1) | T1 (1) | T2 (1) | T3 (1) | T4 (1) | T5 (1) | T6 (1) | T7 (1) |  ← 64-bit bitmap
| TCI state IDs ...                                                       |
```

TCI 활성화 명령 수신 후 **3 ms (HARQ-ACK + processing delay)** 이내에 적용되어야 함.

### 2.4 38.331 — RRC Parameter (Rel.15)

```asn1
TCI-State ::= SEQUENCE {
    tci-StateId         TCI-StateId,
    qcl-Type1           QCL-Info,
    qcl-Type2           QCL-Info  OPTIONAL,
    ...
}

QCL-Info ::= SEQUENCE {
    cell                ServCellIndex  OPTIONAL,
    bwp-Id              BWP-Id  OPTIONAL,
    referenceSignal     CHOICE {
        csi-rs              NZP-CSI-RS-ResourceId,
        ssb                 SSB-Index
    },
    qcl-Type            ENUMERATED {typeA, typeB, typeC, typeD},
    ...
}
```

핵심 rule:
- 한 TCI-state는 최대 2개 QCL relation 보유 (qcl-Type1 필수, qcl-Type2 옵션)
- FR2 운영 시 qcl-Type2는 typeD여야 함
- `tci-StatesToAddModList`: 최대 64개 후보
- `tci-StatesToReleaseList`: 삭제 list

### 2.5 38.306 — UE Capability (Rel.15)

```
maxNumberConfiguredTCIStatesPerCC: { n4, n8, n16, n32, n64, n128 }
maxNumberActiveTCI-PerBWP: { n1, n2, n4, n8 }
```

- 64개 RRC 후보 중 MAC-CE로 동시 활성화 가능한 TCI 수 (UE band별 신고)
- FR1: 통상 n1 또는 n2, FR2: n4 또는 n8

---

## 3. Rel.16 — Multi-TRP 및 URLLC 확장

### 3.1 도입 배경 (WID: RP-193133, NR MIMO Enhancement)

Rel.16은 두 가지 main motivation으로 TCI framework를 확장:

1. **Multi-TRP 지원**: 동일 PDSCH를 두 TRP에서 송신하기 위해 두 TCI-state 동시 적용
2. **URLLC URLLC**: PDSCH repetition을 통한 reliability 향상

### 3.2 38.214 — QCL Assumption 확장

#### 3.2.1 Multi-TRP를 위한 두 TCI-state 동시 적용 (Clause 5.1.5)

DCI Format 1_1의 TCI field 코드포인트가 **2 TCI-states에 매핑**될 수 있게 됨:

- 각 TCI state는 PDSCH의 절반의 layer에 적용 (NCJT, scheme 1a)
- 또는 각 TRP가 다른 시간/주파수 자원을 사용 (FDM scheme 2a/2b, TDM scheme 3, 4)

5가지 Multi-TRP scheme 정의:
- **Scheme 1a (SDM)**: 2 TRP가 다른 layer 송신 (NCJT)
- **Scheme 2a/2b (FDM)**: 다른 frequency resource
- **Scheme 3 (TDM intra-slot)**: 동일 slot 내 다른 mini-slot
- **Scheme 4 (TDM inter-slot)**: 다른 slot

#### 3.2.2 PDCCH Repetition

CORESET 두 개에 다른 TCI 적용, MO(monitoring occasion) linking으로 동일 DCI 두 번 수신 → soft combining.

### 3.3 38.321 — MAC-CE 확장

새 MAC-CE: **Enhanced TCI States Activation/Deactivation for UE-specific PDSCH MAC CE** (LCID 49):
- 단일 코드포인트에 **두 TCI state**를 mapping 가능
- 8 codepoints × 2 TCI = 최대 16 TCI 동시 활성

### 3.4 38.331 — RRC 확장

```asn1
PDCCH-Config ::= SEQUENCE {
    ...,
    [[
    monitoringCapabilityConfig-r16   ENUMERATED {r15monitoringcapability, r16monitoringcapability}
    ]]
}

PDSCH-Config ::= SEQUENCE {
    ...,
    [[
    repetitionSchemeConfig-r16       SetupRelease { RepetitionSchemeConfig-r16 } OPTIONAL,
    enableTwoQCLTypeDForBFD-RS-r17   ENUMERATED {enabled} OPTIONAL  -- (이는 Rel.17)
    ]]
}

RepetitionSchemeConfig-r16 ::= CHOICE {
    fdm-TDM-r16    SetupRelease { FDM-TDM-r16 },
    slotBased-r16  SetupRelease { SlotBased-r16 }
}
```

### 3.5 38.306 — Capability 확장

```
maxNumberSimultaneousTCI-States-NCJT-r16
maxNumberConfiguredTCI-StatePoolsPerBWP-NCJT-r16
mTRP-PDSCH-r16
mTRP-PDCCH-r16
```

---

## 4. Rel.17 — Unified TCI Framework

### 4.1 도입 배경 (WID: RP-202147 / RP-211583, FeMIMO)

Rel.15/16의 가장 큰 한계는 **DL과 UL의 beam indication이 분리**되어 있다는 점이었다:
- DL: TCI-state (PDCCH/PDSCH/CSI-RS)
- UL: Spatial Relation Info (PUCCH/SRS) 또는 SRI (PUSCH)

이는 다음 문제를 야기:
- 동일한 beam을 DL과 UL에 적용하려 해도 별도 RRC + MAC-CE 시그널링 필요
- Multi-panel UE 운영 시 panel-by-panel 관리 어려움
- Beam switching latency 가중

**Unified TCI Framework**는 단일 framework로 DL과 UL 모두 indicate하는 통합 구조를 제공한다.

### 4.2 38.214 — Unified TCI

#### 4.2.1 Joint TCI vs Separate TCI

두 모드 정의:
- **Joint TCI**: 하나의 TCI가 DL+UL 모두 적용
- **Separate TCI**: DL TCI와 UL TCI 별도

#### 4.2.2 새 TCI-state 종류 (Clause 5.1.5의 확장)

| 종류 | 적용 대상 |
|---|---|
| Joint TCI | PDCCH, PDSCH, CSI-RS, PUCCH, PUSCH, SRS (모두) |
| DL-only TCI | PDCCH, PDSCH, CSI-RS |
| UL-only TCI | PUCCH, PUSCH, SRS |

DCI Format 1_1, 1_2에 더해 **DCI Format 1_1/1_2의 새 codepoint** 또는 **DCI Format 1_1 with a non-scheduling DL grant**로 TCI indication.

#### 4.2.3 PDCCH Order TCI Indication

특별히, "DCI without DL assignment" (purely beam indication DCI) 도입 → MAC-CE 보다 빠른 beam switching.

### 4.3 38.321 — MAC-CE 확장

**Unified TCI States Activation/Deactivation MAC CE** (LCID 56):
- Joint TCI list와 separate TCI list 별도 관리
- 최대 64개 → 8개 active

### 4.4 38.331 — RRC 확장

```asn1
PDSCH-Config ::= SEQUENCE {
    ...,
    [[
    unifiedTCI-StateType-r17        ENUMERATED { joint, separate } OPTIONAL,
    dl-OrJointTCI-StateList-r17     SEQUENCE (SIZE (1..maxNrofTCIs-r17)) OF TCI-State OPTIONAL,
    ul-TCI-StateList-r17            SEQUENCE (SIZE (1..maxNrofTCIs-r17)) OF TCI-UL-State-r17 OPTIONAL
    ]]
}

TCI-UL-State-r17 ::= SEQUENCE {
    tci-UL-StateId          TCI-UL-StateId-r17,
    bwp-Id                  BWP-Id  OPTIONAL,
    referenceSignal         CHOICE {
        ssb         SSB-Index,
        csi-rs      NZP-CSI-RS-ResourceId,
        srs         SRS-ResourceId-r17     -- UL의 경우 SRS도 reference 가능
    },
    ul-PowerControl-r17     PowerControl-r17  OPTIONAL,
    pathlossReferenceRS-Id  PathlossReferenceRS-Id-r17  OPTIONAL
}
```

핵심 차이점:
- UL TCI는 **SRS resource를 reference로 사용 가능** (UL beamforming의 자연스러운 source)
- Pathloss RS와 power control parameter가 TCI에 통합됨

### 4.5 38.306 — Capability

```
unifiedTCI-StateMode-r17: { joint, separate, both }
maxNumActiveTCI-StatesPerCC-r17
beamSwitchTiming-r17
ul-TCI-r17
```

UE는 joint와 separate 중 어느 모드를 지원하는지, 동시 active TCI 개수를 신고.

### 4.6 Beam Application Time

Rel.17의 핵심 신규 개념: **beam application time T_BAT**
- DCI 수신 → ACK → T_BAT 후 indicated TCI 적용
- T_BAT는 UE capability `beamAppTime-r17`로 신고 (1, 3, 7 slots 등)

---

## 5. Rel.18 — UL Tx Switching, MIMO Evolution과 LTM 연계

### 5.1 도입 배경 (WID: RP-234037, NR_MIMO_evolution_Ph4)

Rel.18은 unified TCI를 다음 영역으로 확장:

1. **Multi-cell beam management**: 여러 serving cell에 단일 TCI 적용 (CA scenario)
2. **L1/L2 Triggered Mobility (LTM)**: cell change를 RRC reconfig 없이 MAC-CE/DCI로 (별도 보고서 참조)
3. **Multi-panel UE**: 동시 multi-panel 송신을 위한 TCI 확장

### 5.2 38.214 — 확장 사항

#### 5.2.1 Multi-cell TCI

단일 TCI activation MAC-CE로 여러 CC에 동일 TCI 적용:
- 같은 frequency band 내 여러 CC가 동일 beam 사용 시 효율적
- `simultaneousTCI-UpdateList` (RRC)에 같이 update될 cell list 정의

#### 5.2.2 Multi-panel Simultaneous Transmission (STxMP)

UE가 두 panel로 동시 PUSCH 송신:
- 두 SRS resource set, 두 TCI 활성
- DCI에 panel selection field 추가

#### 5.2.3 LTM과의 통합

LTM에서 candidate cell의 TCI는 RRC로 미리 설정 → MAC-CE/DCI로 활성화. LTM 자체는 별도 보고서를 참조.

### 5.3 38.321 — MAC-CE 확장

- **Unified TCI States Activation/Deactivation MAC CE for multiple cells** (LCID 추가)
- **LTM cell switch command MAC CE** (LCID 추가) — 별도 보고서

### 5.4 38.331 — RRC 확장

```asn1
PDSCH-Config ::= SEQUENCE {
    ...,
    [[
    -- Rel.18 multi-cell TCI
    simultaneousU-TCI-UpdateList1-r18       SEQUENCE OF ServCellIndex OPTIONAL,
    simultaneousU-TCI-UpdateList2-r18       SEQUENCE OF ServCellIndex OPTIONAL,
    simultaneousU-TCI-UpdateList3-r18       SEQUENCE OF ServCellIndex OPTIONAL,
    simultaneousU-TCI-UpdateList4-r18       SEQUENCE OF ServCellIndex OPTIONAL
    ]]
}
```

각 list는 동시에 update될 CC group을 정의. 최대 4개 group 운영 가능.

### 5.5 38.306 — Capability

```
multiCellPdcch-PdschTciStateUpdate-r18
multiPanelMTRP-PUSCH-r18
unifiedTCI-MultiCellSet-r18
```

---

## 6. Rel.19 — AI/ML 기반 Beam Management 연계

### 6.1 도입 배경 (WID: RP-234039, AI/ML for NR Air Interface)

Rel.19에서는 AI/ML for beam management가 본격 SI/WI로 진행되며, TCI framework는 다음 방향으로 확장된다 (작성 시점 기준의 진행 상황):

1. **AI/ML 기반 beam prediction**: 부분 측정만으로 best beam 예측 → TCI 후보 압축
2. **Spatial domain prediction**: Set A (full) 중 Set B (subset)만 측정 → AI가 Set A의 TCI 추천
3. **Temporal domain prediction**: 과거 측정으로 미래 beam 예측 → 빠른 TCI 변경

### 6.2 38.214 — 변경 사항

#### 6.2.1 AI/ML CSI/Beam reporting

새 reporting quantity 정의:
- `cri-ssb-AI-prediction`: AI 모델 input/output 보고
- TCI 추천을 UE가 능동 제안 가능

### 6.3 38.321 — MAC-CE

AI/ML 모델 activation/deactivation MAC-CE (working assumption):
- 모델 ID 활성/비활성
- TCI activation MAC-CE는 기존 framework 유지하되, AI 추천 결과 포함

### 6.4 38.331 — RRC

```asn1
-- (Rel.19 working draft 수준)
AI-ML-Configuration-r19 ::= SEQUENCE {
    modelId                 AI-ML-ModelId-r19,
    functionalityType       ENUMERATED { beamPrediction, csiCompression, ... },
    inputConfiguration      ...,
    outputConfiguration     ...
}
```

(Rel.19는 본 보고서 작성 시점에 완료 단계이므로 일부 detail은 확정 시 변경 가능.)

### 6.5 38.306 — Capability

```
ai-ml-BeamPrediction-r19
ai-ml-Spatial-r19
ai-ml-Temporal-r19
maxNumber-ai-ml-Models-r19
```

---

## 7. Rel.20 — 진화 방향

### 7.1 진행 중 작업 (TSG-RAN 작업 계획 기준)

Rel.20은 본 보고서 작성 시점 기준으로 SI 단계가 진행 중이며, TCI 관련 주요 candidate는 다음과 같다:

1. **Cross-Carrier TCI**: CA 운영 시 다른 carrier에서 측정한 RS를 TCI reference로 사용
2. **Sub-band Specific TCI**: BWP 내 sub-band 별 다른 TCI 적용 (frequency-selective beamforming)
3. **AI/ML Mature**: Rel.19의 AI/ML beam management를 normative 기능으로 확장
4. **NTN 환경 TCI**: Non-terrestrial network 환경에서 위성/UE 이동을 반영한 dynamic TCI

### 7.2 잠재적 RRC 확장

```asn1
TCI-State-r20 ::= SEQUENCE {
    ...,
    crossCarrierRefRS-r20       OPTIONAL,
    subbandTCI-Application-r20  OPTIONAL,
    ntn-DopplerComp-r20         OPTIONAL
}
```

(Spec 미확정 영역)

---

## 8. 문서 간 연결 구조 (전체 release 통합)

### 8.1 Release별 진화 매트릭스

| 요소 | Rel.15 | Rel.16 | Rel.17 | Rel.18 | Rel.19 | Rel.20 |
|---|---|---|---|---|---|---|
| **TCI 적용 대상** | DL-only (CSI-RS, PDCCH, PDSCH) | + Multi-TRP | + Unified DL/UL | + Multi-cell, Multi-panel | + AI/ML 추천 | + Cross-carrier, Sub-band |
| **활성화 방법** | RRC + MAC-CE (PDCCH), DCI (PDSCH) | + 2-TCI codepoint | + DCI w/o DL grant, T_BAT | + LTM 연계 | + AI 모델 기반 | + 다양 |
| **38.214 핵심 Clause** | 5.1.5 (QCL) | 5.1.5 + Multi-TRP | 5.1.5 + Unified | + Multi-cell | + AI/ML | TBD |
| **38.321 신규 MAC-CE** | TCI Activation (PDSCH/PDCCH) | Enhanced PDSCH TCI (2-TCI) | Unified TCI Activation | Multi-cell TCI, LTM | AI/ML 모델 | TBD |
| **38.331 핵심 IE** | TCI-State, QCL-Info | RepetitionSchemeConfig | unifiedTCI-StateType, TCI-UL-State | simultaneousU-TCI-UpdateList | AI-ML-Config | TBD |
| **38.306 핵심 Capability** | maxNumberActiveTCI-PerBWP | mTRP-PDSCH/PDCCH | unifiedTCI-StateMode, beamAppTime | multiCellPdcch-PdschTciStateUpdate | ai-ml-BeamPrediction | TBD |

### 8.2 Cross-Document Flow (Rel.17 Unified TCI 예시)

```
                [WID: RP-211583, FeMIMO]
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
   [38.214 §5.1.5]   [38.321 MAC-CE]  [38.331 RRC]
   - Joint/Separate  - Unified TCI    - unifiedTCI-StateType
     TCI 정의          Activation       - TCI-UL-State 신규
   - T_BAT 정의        MAC-CE         - dl-OrJointTCI-StateList
                                       - ul-TCI-StateList
          │               │               │
          └───────┬───────┴───────────────┘
                  ▼
          [38.306 Capability]
          - unifiedTCI-StateMode (joint/separate)
          - beamAppTime
          - ul-TCI
                  │
                  ▼
          [38.133 RRM Test]
          - TCI activation latency requirement
          - Beam application time test
```

### 8.3 핵심 정합성 Checkpoint

각 release에서 cross-document 정합성을 위해 반드시 일치해야 하는 점:

1. **TCI ID 공간**:
   - 38.331의 `tci-StateId` (0~127) ↔ 38.321 MAC-CE의 TCI ID field 폭 ↔ 38.214의 indication 규칙
   - Rel.17에서 joint/UL은 별도 ID 공간 사용

2. **활성 TCI 개수**:
   - 38.306 capability `maxNumberActiveTCI-PerBWP` ≤ 38.331 RRC 설정 가능 max ≤ 38.321 MAC-CE bitmap 길이

3. **DCI codepoint와 active TCI**:
   - DCI TCI field = 3 bits → 8 codepoints → MAC-CE로 활성화된 TCI 중 8개 mapping
   - Rel.16+ 에서는 codepoint당 1 또는 2 TCI

4. **QCL Type D rule**:
   - 38.214 §5.1.5에서 정의된 "qcl-Type2 = typeD only when FR2"가 38.331 RRC 검증에 반영

### 8.4 Beam Switching Timeline의 진화

| Release | Beam switching 방법 | Latency (typical) |
|---|---|---|
| Rel.15 | RRC reconfig + MAC-CE activation + DCI indication | ~10 ms |
| Rel.16 | + 2-TCI MAC-CE (multi-TRP) | ~10 ms (similar) |
| Rel.17 | Unified TCI + DCI w/o DL grant + T_BAT | ~3 ms (T_BAT 단축) |
| Rel.18 | LTM (MAC-CE/DCI based cell switch) | <100 ms (cell change) |
| Rel.19 | AI/ML predicted TCI | proactive (predictable) |

---

## 9. 결론

NR TCI-state framework는 다음 진화 축으로 발전했다:

1. **Coverage Expansion**: DL-only → DL+UL Unified → Multi-cell, Multi-panel
2. **Latency Reduction**: RRC → MAC-CE → DCI → AI/ML 예측
3. **Granularity**: Per-BWP → Per-cell-group → Per-subband (Rel.20)
4. **Intelligence**: 측정 기반 → AI/ML 추론 기반

특히 Rel.17의 Unified TCI Framework는 NR beam management 의 architectural turning point로, Rel.18 LTM, Rel.19 AI/ML, Rel.20의 미래 확장이 모두 이 framework 위에 구축된다.

---

*문서 참조: TS 38.214, 38.321, 38.331, 38.306, 38.133 (Rel.15 ~ Rel.19), RP-170739, RP-181433, RP-193133, RP-211583, RP-234037, RP-234039*
