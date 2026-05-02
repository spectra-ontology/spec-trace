# Beam Failure Detection과 Beam Failure Recovery 표준 절차 정리

> 본 문서는 Beam Failure Detection, Beam Failure Recovery 절차를 도입 배경, 관련 파라미터, 38.213/38.321/38.331 동작, 38.133/38.533 성능 요구사항 관점에서 문서 간 연결고리 중심으로 정리한 1차 분석안이다.

---

## 1. 도입 배경과 필요성

NR, 특히 FR2/mmWave에서는 beam 기반 송수신이 필수이다. 그런데 UE 회전, 손가림, 이동, blockage, TRP switching 등으로 serving beam 품질이 급격히 나빠질 수 있다.

이때 매번 RLF까지 기다렸다가 RRC re-establishment나 handover를 수행하면 interruption이 커진다.

따라서 BFD/BFR은 다음 목적을 가진다.

```text
Beam 품질 저하를 L1/MAC에서 빠르게 감지
  ↓
RLF까지 가기 전에 candidate beam 탐색
  ↓
PRACH 또는 MAC CE/SR 기반으로 recovery 요청
  ↓
새 beam으로 PDCCH/PDSCH/PUCCH/PUSCH 동작 복구
```

즉, BFD/BFR은 **beam-level failure를 cell-level failure로 확대시키지 않기 위한 절차**이다.

---

## 2. 문서 간 연결 구조

```text
38.331
  BFD resource, candidate beam, threshold, timer, recovery search space configure
      ↓
38.213
  UE가 어떤 RS를 BFD RS q0, candidate RS q1로 보고 L1 link quality 평가할지 정의
      ↓
38.321
  lower layer BFI indication을 MAC이 count하고 timer/maxCount 기준으로 BFR trigger
      ↓
38.213
  SpCell이면 PRACH 기반 link recovery, recoverySearchSpaceId monitoring
      ↓
38.321
  SCell이면 BFR MAC CE / truncated BFR MAC CE 또는 SR
      ↓
38.133 / 38.533
  BFD/CBD evaluation time, scheduling restriction, conformance test
```

핵심은 다음이다.

```text
38.331은 파라미터를 준다.
38.213은 L1에서 beam failure와 candidate beam을 어떻게 판단하는지 정한다.
38.321은 MAC에서 BFI counter와 recovery trigger를 관리한다.
38.133은 UE가 얼마나 빨리 판단해야 하는지 requirement를 준다.
38.533은 그 requirement를 시험으로 검증한다.
```

---

## 3. 38.331: 주요 RRC parameter

BFD/BFR 관련 RRC parameter는 크게 **failure detection용**과 **recovery용**으로 나뉜다.

---

### 3.1 Beam failure detection 쪽

| Parameter | 의미 |
|---|---|
| `failureDetectionResourcesToAddModList` | BFD에 사용할 RS list. CSI-RS 또는 SSB 기반 |
| `failureDetectionResourcesToReleaseList` | BFD resource release |
| `failureDetectionSet1`, `failureDetectionSet2` | BFD resource set 구분 |
| `beamFailureInstanceMaxCount` | lower layer에서 올라온 beam failure instance가 몇 번 누적되면 BFR을 trigger할지 |
| `beamFailureDetectionTimer` | BFI counter를 reset하기 위한 timer |
| `rlmInSyncOutOfSyncThreshold` | Qout/Qin 판단에 사용되는 threshold 계열 |

의미를 풀면 다음과 같다.

```text
failureDetectionResources
  → 현재 beam이 죽었는지 감시할 reference signal

beamFailureInstanceMaxCount
  → 몇 번 연속/누적으로 나쁘다고 판단되면 beam failure로 볼지

beamFailureDetectionTimer
  → 일정 시간 안에 BFI가 충분히 누적되지 않으면 counter reset
```

---

### 3.2 Beam failure recovery 쪽

| Parameter | 의미 |
|---|---|
| `candidateBeamRSList` | recovery 후보 beam RS list |
| `rsrp-ThresholdSSB` | SSB 후보 beam 판단 threshold |
| `rsrp-ThresholdBFR` | BFR candidate beam 판단 threshold |
| `recoverySearchSpaceId` | recovery 이후 UE가 PDCCH를 모니터링할 search space |
| `beamFailureRecoveryTimer` | BFR 절차 유효 timer |
| `rach-ConfigBFR` | BFR용 RACH configuration |
| `ssb-perRACH-Occasion` | SSB와 RACH occasion mapping |
| `ra-ssb-OccasionMaskIndex` | RACH occasion mask |
| `schedulingRequestID-BFR` | SCell BFR에서 SR 사용 시 연결되는 SR ID |

의미를 풀면 다음과 같다.

```text
candidateBeamRSList
  → 복구에 사용할 수 있는 후보 beam 목록

rsrp-ThresholdBFR
  → 후보 beam으로 인정할 최소 품질

recoverySearchSpaceId
  → recovery 요청 후 gNB 응답을 찾을 PDCCH search space

rach-ConfigBFR
  → SpCell BFR에서 사용할 PRACH 설정

schedulingRequestID-BFR
  → SCell BFR에서 BFR MAC CE 전송 기회를 얻기 위한 SR 설정
```

---

## 4. 38.213: L1 동작

38.213에서는 BFD/BFR의 PHY layer 판단 기준을 정의한다.

UE는 BFD용 RS set `q0`를 구성한다. RRC가 명시적으로 BFD RS를 configure하면 그것을 사용하고, 없으면 active TCI-State의 QCL Type-D RS 등을 기반으로 default BFD RS를 유도할 수 있다.

candidate beam RS set `q1`은 recovery 후보 beam을 찾기 위한 RS set이다.

```text
q0: 현재 serving beam/link가 실패했는지 보는 RS set
q1: recovery candidate beam을 찾는 RS set
Qout_LR: link recovery 관점의 out-of-sync threshold
Qin_LR: link recovery 관점의 in-sync/candidate threshold
```

L1 동작을 절차로 쓰면 다음과 같다.

```text
1. UE는 q0 RS를 측정한다.
2. q0의 link quality가 Qout_LR보다 나쁘면 lower layer가 BFI를 MAC에 indication한다.
3. UE는 q1 RS를 측정해 candidate beam을 찾는다.
4. candidate beam 품질이 threshold 이상이면 recovery 후보로 선택한다.
5. SpCell이면 PRACH 기반 link recovery를 수행한다.
6. recovery 이후 recoverySearchSpaceId로 지정된 search space에서 PDCCH를 모니터링한다.
```

---

## 5. 38.321: MAC 절차

38.321에서는 lower layer에서 beam failure instance indication, 즉 BFI가 올라왔을 때 MAC이 어떻게 처리하는지 정의한다.

MAC은 다음 파라미터를 사용한다.

| MAC 변수/파라미터 | 의미 |
|---|---|
| `BFI_COUNTER` | beam failure instance 누적 counter |
| `beamFailureInstanceMaxCount` | counter가 이 값에 도달하면 BFR trigger |
| `beamFailureDetectionTimer` | BFI counter reset timer |
| `beamFailureRecoveryTimer` | recovery 절차 timer |
| candidate beam 정보 | recovery 요청 시 어떤 beam을 사용할지 |

MAC 절차는 다음과 같이 이해할 수 있다.

```text
1. lower layer가 BFI를 MAC에 전달
2. MAC이 BFI_COUNTER 증가
3. beamFailureDetectionTimer start/restart
4. BFI_COUNTER >= beamFailureInstanceMaxCount이면 BFR trigger
5. candidate beam이 있으면 recovery 절차 수행
6. SpCell과 SCell에 따라 다른 recovery path 사용
```

---

## 6. SpCell BFR과 SCell BFR 차이

SpCell과 SCell은 recovery 방식이 다르다.

| 대상 | Recovery 방식 |
|---|---|
| SpCell, 즉 PCell/PSCell | PRACH 기반 BFR. recoverySearchSpaceId 모니터링 |
| SCell | BFR MAC CE, truncated BFR MAC CE, 또는 SR 기반 알림 |

### 6.1 SpCell BFR

SpCell은 PCell 또는 PSCell이므로, failure가 생기면 제어 연결 자체가 위험해진다. 따라서 PRACH 기반으로 recovery를 수행한다.

```text
SpCell beam failure
  ↓
candidate beam 선택
  ↓
BFR용 PRACH preamble/resource 전송
  ↓
recoverySearchSpaceId에서 PDCCH 모니터링
  ↓
gNB 응답 수신 후 beam 복구
```

### 6.2 SCell BFR

SCell은 secondary cell이므로, PCell 제어 연결이 살아있는 상태에서 MAC CE로 BFR 정보를 보낼 수 있다.

```text
SCell beam failure
  ↓
candidate beam 선택
  ↓
BFR MAC CE 또는 truncated BFR MAC CE trigger
  ↓
필요 시 SR trigger
  ↓
PCell/PUCCH/PUSCH 경로로 gNB에 BFR 정보 전달
```

즉, SpCell BFR은 **접속 복구 성격**이 강하고, SCell BFR은 **보조 cell의 beam 상태 보고/복구 요청 성격**이 강하다.

---

## 7. 주요 파라미터 의미 정리

| 파라미터 | 문서 | 의미 |
|---|---|---|
| `failureDetectionResourcesToAddModList` | 38.331 | BFD에 사용할 RS 목록 |
| `beamFailureInstanceMaxCount` | 38.331/38.321 | BFI counter가 이 값에 도달하면 BFR trigger |
| `beamFailureDetectionTimer` | 38.331/38.321 | BFI counter reset timer |
| `candidateBeamRSList` | 38.331 | recovery 후보 beam 측정용 RS 목록 |
| `rsrp-ThresholdBFR` | 38.331/38.213 | 후보 beam으로 인정할 threshold |
| `recoverySearchSpaceId` | 38.331/38.213 | BFR 이후 응답 PDCCH monitoring search space |
| `beamFailureRecoveryTimer` | 38.331/38.321 | BFR 절차 유효 timer |
| `rach-ConfigBFR` | 38.331 | SpCell BFR용 RACH 설정 |
| `schedulingRequestID-BFR` | 38.331/38.321 | SCell BFR에서 SR trigger에 사용 |
| `q0` | 38.213 | beam failure detection RS set |
| `q1` | 38.213 | candidate beam RS set |
| `Qout_LR` | 38.213/38.133 | link recovery out-of-sync threshold |
| `Qin_LR` | 38.213/38.133 | candidate/in-sync threshold |

---

## 8. 38.133: RRM 요구사항

38.133은 RRM requirement 문서로, BFD와 candidate beam detection의 시간 요구사항을 정의한다.

성능 요구사항은 대략 다음 범주로 나뉜다.

| Requirement 범주 | 의미 |
|---|---|
| BFD evaluation time | UE가 serving beam failure를 판단하는 데 허용되는 시간 |
| candidate beam detection time | UE가 recovery 후보 beam을 찾는 데 허용되는 시간 |
| FR1/FR2 구분 | frequency range에 따른 requirement 차이 |
| SSB/CSI-RS 기반 구분 | BFD RS가 SSB인지 CSI-RS인지에 따른 차이 |
| DRX/non-DRX 구분 | DRX 동작 여부에 따른 평가 주기 차이 |
| measurement restriction | 측정 가능 occasion 제한이 있을 때의 requirement |
| scheduling restriction | PDSCH/PDCCH scheduling 조건이 있는 경우의 restriction |

즉, 38.133은 “BFD/BFR 절차가 있어야 한다”가 아니라, **UE가 정해진 조건에서 얼마나 빨리 beam failure와 candidate beam을 판단해야 하는지**를 정의한다.

---

## 9. 38.533: Conformance test

38.533은 38.133의 RRM requirement를 실제 시험으로 검증하는 문서이다.

BFD/BFR 관련 시험은 대략 다음을 검증한다.

| Test 범주 | 검증 내용 |
|---|---|
| SSB-based BFD | SSB 기반 BFD/link recovery 성능 |
| CSI-RS-based BFD | CSI-RS 기반 BFD/link recovery 성능 |
| FR1/FR2 | band별 BFD/BFR 성능 |
| DRX/non-DRX | DRX 조건에서의 BFD/BFR 성능 |
| SpCell BFR | PCell/PSCell recovery 절차 |
| SCell BFR | SCell BFR MAC CE/SR 기반 절차 |
| candidate beam detection | candidate beam 탐색 및 threshold 만족 여부 |

연결은 다음과 같다.

```text
38.133
  UE가 몇 ms 안에 beam failure와 candidate beam을 판단해야 하는가

38.533
  그 requirement를 시험 장비 환경에서 어떻게 검증하는가
```

---

## 10. 최종 요약

```text
Beam blockage / beam degradation
  → 38.331이 BFD RS, candidate RS, threshold, timer 구성
  → 38.213이 q0/q1와 Qout/Qin 기반 L1 판단 정의
  → 38.321이 BFI counter와 BFR trigger 수행
  → SpCell은 PRACH recovery, SCell은 BFR MAC CE/SR
  → 38.133/38.533이 detection/recovery 성능 검증
```

BFD/BFR은 NR beam operation에서 **beam-level 장애를 빠르게 감지하고, cell-level RLF로 확대되기 전에 복구하기 위한 L1/MAC/RRC 결합 절차**이다.

---

## 참고 출처

- 3GPP TS 38.213: Physical layer procedures for control
- 3GPP TS 38.321: Medium Access Control protocol specification
- 3GPP TS 38.331: Radio Resource Control protocol specification
- 3GPP TS 38.133: Requirements for support of radio resource management
- 3GPP TS 38.533: NR User Equipment conformance specification; RRM
