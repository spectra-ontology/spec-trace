# NR Beam Failure Detection (BFD) 및 Beam Failure Recovery (BFR) 표준 분석 보고서

## 목차
1. [도입 배경 및 필요성](#1-도입-배경-및-필요성)
2. [핵심 개념 및 동작 개요](#2-핵심-개념-및-동작-개요)
3. [38.213 — Physical Layer 동작](#3-38213--physical-layer-동작)
4. [38.321 — MAC Layer 절차](#4-38321--mac-layer-절차)
5. [38.331 — RRC Parameter](#5-38331--rrc-parameter)
6. [38.133 / 38.533 — UE 성능 요구사항](#6-38133--38533--ue-성능-요구사항)
7. [Release별 진화](#7-release별-진화)
8. [문서 간 연결 구조](#8-문서-간-연결-구조)

---

## 1. 도입 배경 및 필요성

### 1.1 NR FR2 환경에서의 Beam Blockage 문제

NR은 mm-wave 대역(FR2: 24.25 ~ 52.6 GHz, FR2-2: ~71 GHz)을 본격 활용하는 첫 cellular 표준이다. 이 대역의 특성:

- **High path loss**: 자유공간 손실이 sub-6GHz 대비 20dB 이상 높음 → narrow beam 송신 필수
- **Blockage 민감성**: 사람 몸, 손, 차량, 건물 등에 의해 수십 dB 순간 attenuation 발생
- **Dynamic 환경**: UE 회전, 이동, blocker 통과 등에 의해 best beam이 빠르게 변경

이러한 환경에서 **현재 사용 중인 beam이 갑자기 무효화**되면, RLF(Radio Link Failure) → RRC re-establishment → connection drop이라는 무거운 절차로 이어진다. 이는 latency, throughput 측면에서 매우 비효율적이다.

### 1.2 도입 필요성

다음 두 요구사항이 핵심이었다:

1. **Fast detection**: ms 단위로 beam 무효화 감지
2. **Fast recovery without RLF**: RRC 재구성 없이 새 beam으로 빠르게 복구

이를 위해 **Beam Failure Recovery (BFR)** 절차가 NR Rel.15부터 도입되었다. 핵심 아이디어:

- UE가 **PDCCH가 전달되는 beam의 품질을 지속 monitor**
- 일정 횟수 연속 실패 시 **gNB에 SCell-specific BFR request 전송**
- gNB는 새 beam으로 응답 → 동일 RRC 상태 유지

### 1.3 진화 단계 (간략)

| Release | 주요 진화 |
|---|---|
| Rel.15 | PCell BFR 도입 (CFRA 기반) |
| Rel.16 | SCell BFR 도입 (MAC-CE 기반), L1-RSRP 기반 candidate 평가 |
| Rel.17 | Unified BFR framework, multi-TRP 환경 BFR 확장, multi-panel BFR |

상세 진화는 본 보고서 §7에서 다룸.

---

## 2. 핵심 개념 및 동작 개요

### 2.1 BFD-RS와 candidate beam RS

BFR 절차는 두 가지 종류의 RS 집합을 사용한다:

#### (1) Beam Failure Detection RS (BFD-RS)
- 현재 PDCCH의 spatial QCL source RS (Type D)를 monitor
- 이 RS의 품질(L1 측정값)을 기준으로 beam failure 판단
- RRC `failureDetectionResources` 또는 implicit derivation

#### (2) Candidate Beam RS (CB-RS, q_1 set)
- Beam 실패 시 새 beam의 후보가 되는 RS 집합
- RRC `candidateBeamRSList`로 설정
- L1-RSRP 기반으로 평가, threshold 이상인 beam을 선택해 보고

### 2.2 BFR 절차의 4단계

```
   ┌──────────────────────────────┐
   │  Step 1: Beam Failure        │
   │  Instance Detection          │
   │  (PHY: 38.213)               │
   └──────────────┬───────────────┘
                  │ BFI indication
                  ▼
   ┌──────────────────────────────┐
   │  Step 2: Beam Failure        │
   │  Declaration                 │
   │  (MAC: 38.321)               │
   │  - 카운터 누적, timer 관리   │
   └──────────────┬───────────────┘
                  │ Failure declared
                  ▼
   ┌──────────────────────────────┐
   │  Step 3: Candidate Beam      │
   │  Identification              │
   │  (PHY+MAC)                   │
   └──────────────┬───────────────┘
                  │ Candidate selected
                  ▼
   ┌──────────────────────────────┐
   │  Step 4: BFRQ Transmission   │
   │  & gNB Response              │
   │  (CFRA / MAC-CE / DCI)       │
   └──────────────────────────────┘
```

---

## 3. 38.213 — Physical Layer 동작

### 3.1 Beam Failure Instance (BFI) 검출 — Clause 6

#### 3.1.1 측정 대상

UE는 다음 RS의 L1 품질을 측정:
- RRC `failureDetectionResources` (NZP-CSI-RS 또는 SSB)에 명시된 RS, **OR**
- Explicit list가 없으면, 모든 active CORESET의 TCI-state에서 derive된 RS (QCL Type D source)

NR Rel.15: 최대 2 RS, Rel.16+: 최대 64 RS (BFD-RS list)

#### 3.1.2 평가 기준: 가상 BLER (hypothetical BLER)

UE는 측정된 RS의 채널/노이즈 추정으로부터 **가상의 PDCCH BLER**을 계산:

$$\text{BLER}_{\text{hypothetical}} = f(\text{SINR}_{\text{est}}, \text{PDCCH config})$$

여기서 PDCCH config은 가장 worst-case parameter (e.g., Aggregation Level 8, Rel.15에서는 specific 가정)를 가정.

#### 3.1.3 Beam Failure Instance 판정

- **BLER_hypothetical > Q_out_LR (e.g., 10%)** 이면 BFI 발생, MAC layer로 indication
- 평가 주기 T_evaluate_BFD는 BFD-RS의 periodicity와 같음 (typical: 5~40 ms)

### 3.2 Candidate Beam Identification — Clause 6

#### 3.2.1 평가 대상

`candidateBeamRSList`(q_1 set)에 정의된 RS의 L1-RSRP 측정.

#### 3.2.2 Threshold

RRC parameter `rsrp-ThresholdSSB` 또는 `rsrp-ThresholdBFR` (typical: -110 dBm)

#### 3.2.3 후보 선택

L1-RSRP > threshold인 RS 중 **가장 좋은 RS의 RS index**를 MAC layer에 indication.

### 3.3 BFRQ 전송 (Beam Failure Recovery Request)

#### Rel.15: PRACH-based BFRQ
- 전용 CFRA(Contention-Free Random Access) preamble 사용
- BeamFailureRecoveryConfig의 `recoverySearchSpaceId`에 대응하는 PDCCH로 응답 monitor

#### Rel.16: MAC-CE-based BFRQ (SCell)
- SCell이 실패 시 PCell의 PUSCH로 MAC-CE 전송
- MAC-CE: `BFR MAC CE` (LCID 47 또는 fixed)

### 3.4 Recovery Response Window (38.213 Clause 9)

UE는 BFRQ 전송 후 다음 window 동안 PDCCH (DCI 1_0 with RA-RNTI 또는 C-RNTI) monitor:

$$\text{Window} = \text{BeamFailureRecoveryTimer} \text{ slots}$$

이 window 안에 응답 수신하면 recovery 성공. 미수신 시 BFRQ 재시도 또는 RLF 선언.

---

## 4. 38.321 — MAC Layer 절차

### 4.1 PCell BFR (Rel.15) — Clause 5.17

#### 4.1.1 변수 및 카운터

| 변수 | 의미 | RRC 설정 | 기본 동작 |
|---|---|---|---|
| BFI_COUNTER | 누적 BFI 횟수 | (없음, 카운터) | BFI마다 +1 |
| beamFailureInstanceMaxCount | 실패 선언 임계값 | RRC | 1, 2, 3, 4, 5, 6, 8, 10 |
| beamFailureDetectionTimer | BFI 카운터 reset 타이머 | RRC | pbfd1, pbfd2, ... pbfd10 (slot 단위) |

#### 4.1.2 절차

```
Lower layers로부터 BFI indication 수신 시:
1. BFI_COUNTER += 1
2. beamFailureDetectionTimer 시작/재시작
3. IF BFI_COUNTER >= beamFailureInstanceMaxCount:
       Beam failure 선언
       BFR 절차 시작 (random access for SpCell)

beamFailureDetectionTimer expiry 시:
1. BFI_COUNTER = 0
```

#### 4.1.3 BFR Initiation (PCell)

- RA procedure trigger (Random Access)
- `beamFailureRecoveryConfig` 내의 `candidateBeamRSList`로 candidate 평가
- Suitable beam의 PRACH preamble로 BFRQ 전송
- `beamFailureRecoveryTimer` 동안 PDCCH monitor
- Timer expiry → 일반 RA fallback

### 4.2 SCell BFR (Rel.16) — Clause 5.17.2

PCell BFR과 달리 **PRACH가 SCell에 없을 수 있으므로** MAC-CE 기반 절차 사용.

#### 4.2.1 BFR MAC CE 포맷 (Truncated/Full BFR MAC CE)

```
| C7 | C6 | C5 | C4 | C3 | C2 | C1 | C0 |   ← octet 1: failed cell bitmap (PCell 제외 0~7)
| AC | R  | Candidate RS ID (6 bits)    |   ← octet 2: per-cell candidate
...
```

- `C_i = 1`: SCell i에서 beam failure 발생
- `AC = 1`: candidate beam ID 유효
- `Candidate RS ID`: 6 bits → 64개 candidate RS 식별

#### 4.2.2 SCell BFR Procedure

```
1. SCell i에서 BFI_COUNTER_i 누적
2. BFI_COUNTER_i >= beamFailureInstanceMaxCount → SCell i 실패 선언
3. trigger BFR for SCell i (UL grant 요청)
4. BFR MAC CE 작성:
   - C_i bit set
   - candidate beam 평가하여 RS ID 포함
5. PUSCH로 BFR MAC CE 전송 (PCell 또는 anchor SCell 통해)
6. gNB 응답 수신 (PDCCH로 BFR 적용 확인)
```

#### 4.2.3 Truncated vs Full

- **Truncated BFR MAC CE** (LCID 47): UL grant 작아서 모든 SCell 정보 못 담을 때
- **Full BFR MAC CE** (LCID 48): 8 SCell 모두 가능

### 4.3 SR for BFR

UL grant가 없는 상태에서 BFR 시작 시 **dedicated SR (Scheduling Request) for BFR** 사용:
- `schedulingRequestId-BFR-r16` (RRC)
- BFR 발생 시 즉시 SR 전송 → gNB가 UL grant 제공

### 4.4 Recovery 성공 조건 (38.321)

다음 조건 만족 시 BFR 절차 종료:
- **PCell**: `recoverySearchSpaceId`에 해당하는 search space에서 C-RNTI scrambled DCI 수신
- **SCell**: 해당 SCell에 대한 PDCCH 수신 또는 명시적 BFR confirm

---

## 5. 38.331 — RRC Parameter

### 5.1 BeamFailureRecoveryConfig (PCell용)

```asn1
BeamFailureRecoveryConfig ::= SEQUENCE {
    rootSequenceIndex-BFR           INTEGER (0..137)  OPTIONAL,
    rach-ConfigBFR                  RACH-ConfigGeneric  OPTIONAL,
    rsrp-ThresholdSSB               RSRP-Range  OPTIONAL,
    candidateBeamRSList             SEQUENCE (SIZE(1..maxNrofCandidateBeams)) OF PRACH-ResourceDedicatedBFR  OPTIONAL,
    ssb-perRACH-Occasion            ENUMERATED {oneEighth, oneFourth, oneHalf, one, two, four, eight, sixteen}  OPTIONAL,
    ra-ssb-OccasionMaskIndex        INTEGER (0..15)  OPTIONAL,
    recoverySearchSpaceId           SearchSpaceId  OPTIONAL,
    ra-Prioritization               RA-Prioritization  OPTIONAL,
    beamFailureRecoveryTimer        ENUMERATED {ms10, ms20, ms40, ms60, ms80, ms100, ms150, ms200}  OPTIONAL,
    msg1-SubcarrierSpacing          SubcarrierSpacing  OPTIONAL,
    ...
}
```

핵심 파라미터 의미:
- **`candidateBeamRSList`**: q_1 set, recovery 시 후보 beam 측정 대상
- **`rsrp-ThresholdSSB`**: candidate 선택 임계값
- **`recoverySearchSpaceId`**: BFR 응답 PDCCH monitoring search space
- **`beamFailureRecoveryTimer`**: BFR 응답 wait timer

### 5.2 BeamFailureRecoverySCellConfig (Rel.16, SCell용)

```asn1
BeamFailureRecoverySCellConfig-r16 ::= SEQUENCE {
    rsrp-ThresholdBFR-r16                    RSRP-Range  OPTIONAL,
    candidateBeamRSSCellList-r16             SEQUENCE (SIZE(1..maxNrofCandidateBeams-r16)) OF CandidateBeamRS-r16  OPTIONAL,
    beamFailureRecoveryTimer-r16             ENUMERATED {ms10, ms20, ms40, ms60, ms80, ms100, ms150, ms200}  OPTIONAL,
    ...
}

CandidateBeamRS-r16 ::= SEQUENCE {
    candidateBeamConfig-r16   CHOICE {
        ssb-r16        SSB-Index,
        csi-RS-r16     NZP-CSI-RS-ResourceId
    },
    servCellId                ServCellIndex  OPTIONAL  -- 다른 cell의 RS 가능
}
```

### 5.3 RadioLinkMonitoringConfig (BFD-RS 설정)

```asn1
RadioLinkMonitoringConfig ::= SEQUENCE {
    failureDetectionResourcesToAddModList   SEQUENCE OF RadioLinkMonitoringRS  OPTIONAL,
    failureDetectionResourcesToReleaseList  SEQUENCE OF RadioLinkMonitoringRS-Id  OPTIONAL,
    beamFailureInstanceMaxCount             ENUMERATED {n1, n2, n3, n4, n5, n6, n8, n10}  OPTIONAL,
    beamFailureDetectionTimer               ENUMERATED {pbfd1, pbfd2, pbfd3, pbfd4, pbfd5, pbfd6, pbfd8, pbfd10}  OPTIONAL
}

RadioLinkMonitoringRS ::= SEQUENCE {
    radioLinkMonitoringRS-Id    RadioLinkMonitoringRS-Id,
    purpose                     ENUMERATED {beamFailure, rlf, both},
    detectionResource           CHOICE {
        ssb-Index   SSB-Index,
        csi-RS-Index NZP-CSI-RS-ResourceId
    }
}
```

핵심 사항:
- **`purpose`**: 동일 RS를 BFD와 RLF detection 양쪽에 사용 가능
- 최대 RS 개수: Rel.15 = 2, Rel.16+ = up to 8 또는 그 이상

### 5.4 SchedulingRequestResourceConfig with BFR

```asn1
SchedulingRequestResourceConfig ::= SEQUENCE {
    ...,
    schedulingRequestId         SchedulingRequestId,
    ...
}

-- BFR-dedicated SR
SchedulingRequestConfig ::= SEQUENCE {
    schedulingRequestToAddModList SEQUENCE OF SchedulingRequestToAddMod  OPTIONAL,
    ...
}
```

`schedulingRequestId-BFR-SCell-r16`이 SCell BFR을 위해 별도 정의됨.

---

## 6. 38.133 / 38.533 — UE 성능 요구사항

### 6.1 38.133 — RRM 요구사항

#### 6.1.1 BFD 성능 (Clause 8.5)

UE는 다음 시간 내에 BFI를 검출해야 한다:

$$T_{\text{Evaluate\_BFD\_SSB}} = \max(T_{\text{DRX}}, M \cdot T_{\text{SSB}})$$

여기서:
- T_SSB: SSB periodicity (typical 20 ms)
- M: implementation factor (1 또는 5, condition에 따라)

#### 6.1.2 Candidate Beam 평가 시간 (Clause 8.5.4)

L1-RSRP 측정 + suitable beam 식별까지의 시간:

$$T_{\text{search}} = \max(T_{\text{DRX}}, M_2 \cdot T_{\text{measurement period}})$$

#### 6.1.3 SCell BFR Recovery Time

총 BFR 절차 완료 시간 (Clause 8.5.x):
- BFI detection ~ candidate identification: 위 시간
- BFRQ 전송 ~ gNB 응답 수신: scheduling 영향
- 전체 typical: **수십 ms ~ 100 ms 이내**

#### 6.1.4 Test Configuration 예

| Parameter | Value |
|---|---|
| Cell A SS-RSRP | -100 dBm (BFD-RS source) |
| Cell A degrades to | -130 dBm (failure) |
| Candidate beam B SS-RSRP | -100 dBm |
| Threshold | -110 dBm |
| Required: T_recovery | < 80 ms (typical FR2) |

### 6.2 38.533 — Conformance Test

38.133의 RRM requirement는 38.533에서 **conformance test case**로 구체화된다.

#### 6.2.1 BFD Test Case (38.533 Clause 7.6 부근)

Test purpose: UE가 정의된 시간 내 BFI 누적 → beam failure 선언 가능 검증.

```
Test setup:
- gNB가 PCell 주 beam (CSI-RS 1)을 -130 dBm으로 attenuate
- Candidate beam (SSB B)를 -100 dBm으로 송신
- 시간 측정: attenuation 시점 ~ UE의 PRACH/MAC-CE BFRQ 전송 시점
- Pass criterion: T < specified bound
```

#### 6.2.2 SCell BFR Test Case

- SCell에서 BFI 발생 → PCell 통해 BFR MAC CE 전송
- 측정: SCell 실패 발생 시점 ~ MAC CE 전송 시점 ~ gNB confirmation

#### 6.2.3 False Alarm Test

UE가 false alarm으로 정상 beam에서 BFR 선언하지 않아야 한다:
- BFD-RS 품질이 -100 dBm으로 양호한 상황에서 90% 이상 시간 동안 BFR 미발생

### 6.3 핵심 RRM Parameter (정량 기준)

38.133 기준 typical 값:

| Parameter | Value | 적용 |
|---|---|---|
| Q_out_LR (BLER threshold) | 10% | BFI 판정 |
| L1-RSRP threshold | -110 dBm (default) | Candidate 선정 |
| beamFailureInstanceMaxCount | 1~10 (RRC), 통상 3 | Failure 선언 |
| beamFailureDetectionTimer | 1~10 × evaluation period | Counter reset |
| beamFailureRecoveryTimer | 10~200 ms | Response 대기 |

---

## 7. Release별 진화

### 7.1 Rel.15 — PCell BFR (Initial)

- **Scope**: PCell only
- **Mechanism**: PRACH-based CFRA
- **Limitation**: SCell에서 실패 시 즉시 RLF로 이어질 위험

### 7.2 Rel.16 — SCell BFR

WID: RP-201305 (NR_eMIMO_2 / Mobility enhancements)

- **Scope**: PCell + SCell
- **New mechanism**: MAC-CE based BFR for SCell
- **신규**: 
  - BFR MAC CE (LCID 47, 48)
  - `BeamFailureRecoverySCellConfig`
  - SR-BFR resource

### 7.3 Rel.17 — Multi-TRP BFR + Unified BFR

WID: RP-211583 (FeMIMO)

- **Multi-TRP BFR**: 두 TRP 중 하나의 beam만 실패 시 부분 BFR
  - `failureDetectionSet1-r17`, `failureDetectionSet2-r17`
  - Per-TRP BFR MAC-CE
- **Unified BFR**: Unified TCI framework와의 통합
  - Joint TCI 환경에서 BFR이 DL+UL beam 동시 갱신

### 7.4 Rel.18 — Multi-Panel BFR

WID: RP-234037

- **Multi-panel UE**: 한 panel 실패 시 다른 panel로 전환
- **per-panel BFD-RS, candidate beam**
- LTM과의 연계: BFR이 LTM cell switch trigger로 사용 가능

---

## 8. 문서 간 연결 구조

### 8.1 절차 흐름과 문서 매핑

```
[Phase 1: Detection]
   ┌─────────────────────────────────┐
   │ 38.213 §6:                       │
   │ - BFD-RS 측정                    │
   │ - Hypothetical BLER 계산         │
   │ - BFI 발생 시 MAC indication     │
   └────────────────┬────────────────┘
                    │
   ┌────────────────▼────────────────┐
   │ 38.321 §5.17:                    │
   │ - BFI_COUNTER 관리               │
   │ - beamFailureDetectionTimer      │
   │ - 임계값 도달 시 failure 선언   │
   └────────────────┬────────────────┘
                    │
[Phase 2: Recovery]│
                    ▼
   ┌─────────────────────────────────┐
   │ 38.213 §9:                       │
   │ - candidateBeamRS L1-RSRP 측정   │
   │ - Threshold > 인 RS 식별        │
   └────────────────┬────────────────┘
                    │
   ┌────────────────▼────────────────┐
   │ 38.321 §5.17 / §5.4:             │
   │ - PCell: RA 절차                 │
   │ - SCell: BFR MAC CE + SR-BFR     │
   └────────────────┬────────────────┘
                    │
   ┌────────────────▼────────────────┐
   │ 38.213 §10:                      │
   │ - BFR response window            │
   │ - recoverySearchSpaceId monitor  │
   └────────────────┬────────────────┘
                    │
[Phase 3: Validation]
                    ▼
   ┌─────────────────────────────────┐
   │ 38.133 §8.5 / 38.533 §7.6:       │
   │ - Time/Latency 요구사항          │
   │ - Conformance test               │
   └─────────────────────────────────┘
```

### 8.2 RRC ↔ MAC ↔ PHY ↔ RRM 정합성

| 항목 | 38.331 (RRC) | 38.321 (MAC) | 38.213 (PHY) | 38.133 (RRM) |
|---|---|---|---|---|
| BFD-RS 설정 | `failureDetectionResourcesToAddModList` | (사용) | 측정 대상 | 측정 시간 요구 |
| 실패 임계값 | `beamFailureInstanceMaxCount` | BFI_COUNTER 비교 | (BFI 트리거) | — |
| 카운터 리셋 | `beamFailureDetectionTimer` | Timer 관리 | — | Timer 정확도 |
| Candidate RS | `candidateBeamRSList` | 후보 선택 | L1-RSRP 측정 | 평가 시간 |
| RSRP threshold | `rsrp-ThresholdSSB` | 비교 | Threshold 비교 | 측정 정확도 |
| Recovery search space | `recoverySearchSpaceId` | (사용) | PDCCH monitor | — |
| Response timer | `beamFailureRecoveryTimer` | Timer 관리 | Window 결정 | Total recovery time |
| SCell BFR MAC-CE | LCID 47/48 (간접) | 포맷 정의 | (UL 전송) | Total time |
| SR-BFR | `schedulingRequestId-BFR` | SR 트리거 | PUCCH SR 자원 | SR latency |

### 8.3 핵심 정합성 Checkpoint

#### Checkpoint 1: BFD-RS 일관성
- 38.331 `failureDetectionResources`에 명시 (또는 implicit derivation rule 적용)
- 38.213이 동일 RS의 BLER 측정
- 38.133 시간 요구사항이 동일 RS periodicity 기반

#### Checkpoint 2: 카운터/타이머 매칭
- 38.331 RRC에서 `beamFailureInstanceMaxCount` (예: n3)
- 38.321 MAC가 정확히 n3번 BFI 누적 시 failure 선언
- 38.213 PHY가 매 BFI 검출 주기마다 indication

#### Checkpoint 3: Recovery 응답 검증
- 38.331 `recoverySearchSpaceId`로 응답 PDCCH 위치 정의
- 38.213이 해당 SearchSpace에서 PDCCH monitoring
- 38.321이 응답 수신 시 절차 종료

#### Checkpoint 4: Latency Budget
- 38.213의 evaluation period (e.g., M × T_SSB)
- + 38.321의 카운터 누적 시간
- + 38.213의 BFRQ 전송 + response window
- = 38.133의 Total recovery time requirement

이 모든 합이 38.133에서 정한 한계 (예: 80 ms FR2) 이내여야 함.

### 8.4 구체 실행 시나리오 (예: FR2 PCell BFR)

```
T = 0 ms:    PCell BFD-RS (CSI-RS) 신호 -130 dBm으로 저하
T = 5 ms:    UE 첫 BFI 검출 (38.213 §6, BLER > 10%)
T = 5 ms:    BFI_COUNTER = 1, beamFailureDetectionTimer 시작 (38.321)
T = 25 ms:   2번째 BFI, COUNTER = 2
T = 45 ms:   3번째 BFI, COUNTER = 3 = beamFailureInstanceMaxCount
             → Beam failure 선언 (38.321 §5.17)
T = 45 ms:   Candidate beam 평가 시작 (38.213 §9)
T = 50 ms:   Candidate SSB B (-100 dBm > threshold) 선정
T = 50 ms:   PRACH preamble 송신 (RA 절차)
T = 60 ms:   PDCCH on recoverySearchSpaceId 수신 (gNB 응답)
T = 60 ms:   BFR 절차 완료 (38.321)
=> Total: 60 ms < 80 ms (38.133 spec) ✓
```

---

## 9. 결론

NR Beam Failure Detection/Recovery 절차는 다음 의의를 갖는다:

1. **RLF 회피**: RRC re-establishment의 무거운 절차 없이 ms 단위로 beam 복구
2. **계층 통합 설계**: PHY measurement → MAC procedure → RRC config가 정교하게 결합
3. **Release별 진화**: PCell only → SCell → Multi-TRP → Multi-panel로 적용 범위 지속 확장
4. **FR2 운용성 확보**: mm-wave 대역의 가장 큰 약점인 blockage 문제를 cellular spec 차원에서 해결

특히 BFR은 LTM(L1/L2 Triggered Mobility)과 같은 후속 mobility 기술의 토대가 되며, AI/ML 기반 beam prediction(Rel.19+)에서는 proactive BFR로 진화하고 있다.

---

*문서 참조: TS 38.213, TS 38.321, TS 38.331, TS 38.133, TS 38.533 (Rel.15 ~ Rel.18), RP-170739, RP-201305, RP-211583, RP-234037*
