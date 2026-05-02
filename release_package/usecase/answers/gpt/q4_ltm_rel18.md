# Rel.18 LTM, L1/L2 Triggered Mobility 표준 아이템 정리

> 본 문서는 Rel.18에서 도입된 LTM, L1/L2 Triggered Mobility를 38.300, 38.331, 38.321, 38.214, 38.133, 38.306 관점에서 정리하고, Rel.19/Rel.20 확장 방향까지 문서 간 연결고리 중심으로 설명한 1차 분석안이다.  
> Rel.20은 진행 중인 영역이므로 최종 frozen normative behavior가 아니라 공개 scope와 draft CR 기반의 방향성으로 정리한다.

---

## 1. 도입 배경

기존 handover는 RRC 기반이다.

```text
측정 보고
  ↓
네트워크 handover 결정
  ↓
RRCReconfiguration
  ↓
UE가 target cell 동기화
  ↓
RACH
  ↓
RRCReconfigurationComplete
```

이 구조는 안정적이지만 interruption time이 크다. 특히 고속 이동, FR2, small cell, dense deployment에서는 handover latency가 성능 병목이 된다.

Rel.18 LTM의 목적은 **target/candidate cell configuration을 미리 준비해두고**, 실제 전환 시점에는 **MAC CE 같은 lower-layer signaling으로 빠르게 cell switch를 실행**하는 것이다.

---

## 2. LTM의 핵심 개념

```text
RRC phase
  candidate cell configuration을 미리 UE에 제공

Preparation phase
  candidate TCI state, CSI-RS/SSB resource, early DL sync, optional early UL TA 준비

Execution phase
  MAC CE로 target configuration ID / TCI / TA / NCC 등을 지시

Completion phase
  RACH 또는 RACH-less 방식으로 target cell 접속 완료
```

LTM은 기존 handover를 완전히 대체하는 것이 아니라, **handover 실행부를 lower layer로 내리는 구조**에 가깝다.

즉:

```text
기존 HO:
  RRC가 전환 시점에 큰 절차를 수행

LTM:
  RRC는 후보 설정을 미리 준비
  MAC CE가 빠르게 전환 실행
```

---

## 3. 문서 간 연결 구조

```text
38.300
  LTM 개념과 전체 절차 설명
      ↓
38.331
  LTM candidate cell configuration, candidate TCI, CSI resource, early sync 관련 RRC 설정
      ↓
38.214
  candidate cell L1 measurement/reporting, TCI/QCL assumption 적용
      ↓
38.321
  LTM Cell Switch Command MAC CE, Enhanced LTM MAC CE, Candidate Cell TCI MAC CE
      ↓
38.133
  mobility interruption time, RRM requirement
      ↓
38.306
  UE가 LTM, early sync, candidate cell/beam/reporting을 지원하는지 capability 보고
```

핵심은 다음이다.

```text
38.331은 “갈 수 있는 target 후보들”을 미리 UE에 설치한다.
38.321 MAC CE는 그중 “지금 이 후보로 바꿔라”를 지시한다.
38.214는 그 순간 어떤 TCI/QCL/measurement assumption을 적용할지 정의한다.
38.133은 얼마나 빠르고 안정적으로 전환해야 하는지 requirement를 준다.
38.306은 UE가 어디까지 지원 가능한지 상한선을 정한다.
```

---

## 4. 38.300: LTM 개념과 procedure

38.300의 intra-gNB LTM 절차를 요약하면 다음이다.

```text
1. UE가 L3 measurement report 전송
2. serving gNB가 candidate target cell을 결정
3. RRCReconfiguration으로 candidate cell configuration 제공
4. UE가 candidate configuration 저장
5. UE가 candidate cell에 대해 early DL sync 수행
6. 필요 시 early UL sync / TA 획득
7. UE가 L1 measurement report 수행
8. gNB가 MAC CE cell switch command 전송
9. UE가 target configuration ID, TCI, TA 등을 적용
10. valid TA가 있으면 RACH-less, 없으면 RACH-based access
11. UE가 RRCReconfigurationComplete 또는 UL data로 완료
```

38.300에서 중요한 개념은 다음이다.

| 개념 | 의미 |
|---|---|
| candidate cell configuration | target 후보 cell에 대한 RRC configuration |
| early DL sync | 전환 전에 candidate cell의 DL timing/sync를 미리 확보 |
| early UL sync | 전환 전에 target UL timing 또는 TA를 미리 확보 |
| RACH-less LTM | valid TA가 있는 경우 random access 없이 cell switch |
| RACH-based LTM | valid TA가 없거나 필요한 경우 random access 수행 |
| L1 measurement report | candidate cell 품질을 lower-layer decision에 활용 |
| Cell Switch Command | 실제 전환을 지시하는 MAC CE |

LTM의 본질은 **candidate를 미리 준비하고, 실행은 MAC CE로 빠르게 수행하는 것**이다.

---

## 5. 38.331: RRC parameter

38.331에서 LTM 관련 RRC parameter는 candidate configuration을 미리 UE에 저장시키는 역할을 한다.

| RRC IE/parameter | 역할 |
|---|---|
| `LTM-Config` | LTM 전체 configuration container |
| `LTM-CandidateConfig` | candidate cell별 RRCReconfiguration 후보 |
| candidate cell PCI | candidate target cell 식별 |
| early UL sync config | target cell로 빠르게 UL timing 맞추기 위한 설정 |
| no-reset / TA 관련 ID | MAC reset, TA 유지/재사용 관련 제어 |
| LTM CSI resource config | candidate cell L1 measurement/reporting용 CSI-RS/SSB resource |
| `LTM-TCI-Info` | LTM activation/cell switch 시 적용할 TCI 정보 |
| candidate TCI state | target/candidate cell에서 사용할 beam/QCL assumption |

RRC configuration을 절차로 보면 다음과 같다.

```text
RRCReconfiguration
  ↓
LTM-Config 제공
  ↓
candidate cell별 configuration 저장
  ↓
candidate cell 측정용 CSI-RS/SSB resource 구성
  ↓
candidate TCI state 구성
  ↓
early DL/UL sync 가능하도록 관련 설정 제공
```

즉, 38.331은 LTM에서 **preparation phase**를 담당한다.

---

## 6. 38.321: MAC CE 동작

38.321에는 LTM Cell Switch Command MAC CE와 Enhanced LTM Cell Switch Command MAC CE가 있다.

MAC CE는 다음 정보를 전달하는 실행 trigger이다.

| MAC CE 정보 | 의미 |
|---|---|
| target configuration ID | RRC가 미리 준 후보 중 어느 target으로 갈지 |
| candidate TCI state | target/candidate cell에서 사용할 beam/QCL assumption |
| TA 또는 TA 관련 정보 | RACH-less 가능 여부와 UL timing |
| NCC/security 관련 정보 | target 전환 시 security context |
| RACH/RACH-less 관련 indicator | random access 필요 여부 |
| SR configuration | 전환 직후 UL 제어 절차 |
| lower-layer TCI information | 전환 직후 적용할 beam/TCI 정보 |

MAC CE 기반 실행 흐름은 다음이다.

```text
1. UE는 RRC로 LTM candidate config를 이미 저장하고 있음
2. gNB가 MAC CE Cell Switch Command 전송
3. UE는 target configuration ID를 확인
4. 해당 candidate config를 적용
5. 지시된 TCI/TA/NCC 정보를 적용
6. valid TA가 있으면 RACH-less 전환
7. valid TA가 없으면 RACH-based 전환
8. 전환 후 UL data 또는 RRCReconfigurationComplete 등으로 완료
```

38.321의 역할은 **LTM execution phase**를 담당하는 것이다.

---

## 7. 38.214: L1 measurement와 reporting

LTM에서는 UE가 target/candidate cell에 대해 L1 measurement를 수행해야 한다. 측정 대상은 보통 candidate cell의 SSB 또는 CSI-RS이고, L1-RSRP reporting이 cell switch decision에 사용된다.

38.214 관점에서는 다음이 중요하다.

```text
candidate cell CSI-RS/SSB 측정
  ↓
L1-RSRP report
  ↓
gNB가 MAC CE cell switch command 결정
  ↓
UE는 CandidateTCI-State 또는 indicated TCI를 기준으로 QCL assumption 적용
```

38.214에서 중요한 역할은 다음이다.

| 항목 | 의미 |
|---|---|
| L1-RSRP measurement | candidate cell/beam 품질 측정 |
| CSI-RS/SSB 기반 measurement | target/candidate cell의 beam 품질 평가 |
| TCI/QCL assumption | 전환 시 어떤 beam/spatial assumption을 적용할지 |
| CandidateTCI-State | LTM cell switch 시 target/candidate cell에서 사용할 TCI |
| DCI/MAC CE TCI indication과의 관계 | 전환 직후 PDCCH/PDSCH 수신 assumption 결정 |

즉, 38.214는 LTM에서 **측정과 beam assumption의 PHY 동작**을 담당한다.

---

## 8. 38.133: RRM 요구사항

LTM의 성능상 핵심은 **mobility interruption time을 줄이는 것**이다.

성능 requirement는 다음 항목들과 연결된다.

| 항목 | 의미 |
|---|---|
| mobility interruption time | cell switch 중 DL/UL 데이터가 끊기는 시간 |
| early DL sync availability | target cell DL timing을 미리 맞출 수 있는지 |
| early UL sync / TA validity | RACH-less 전환 가능 여부 |
| L1 measurement/reporting latency | MAC CE trigger 이전 target quality 판단 속도 |
| RACH-based vs RACH-less | access 방식에 따른 interruption 차이 |
| processing time | MAC CE 수신 후 target config 적용까지의 UE 처리 시간 |

기존 handover와 LTM의 차이는 다음이다.

```text
기존 RRC handover:
  RRC signaling + synchronization + RACH + completion으로 interruption 발생

LTM:
  RRC preparation을 미리 수행
  execution은 MAC CE와 lower-layer sync로 빠르게 수행
  valid TA가 있으면 RACH-less로 interruption을 더 줄임
```

따라서 38.133에서 LTM 관련 RRM requirement는 **전환 시간, 측정 시간, sync 준비 상태, RACH-less 가능 조건**과 연결된다.

---

## 9. 38.306: UE capability

LTM은 UE 구현 부담이 크다. UE는 serving cell을 유지하면서 candidate cell 측정, candidate TCI, early sync, TA, possible RACH-less switch 등을 처리해야 한다.

따라서 capability에는 다음 류의 항목이 들어간다.

| Capability 범주 | 의미 |
|---|---|
| 지원 가능한 LTM candidate cell 수 | 몇 개 후보 cell configuration을 저장/관리 가능한지 |
| 지원 가능한 candidate beam/TCI 수 | candidate cell별 beam 후보 수 |
| L1 measurement/reporting capability | LTM용 L1-RSRP reporting 지원 수준 |
| early DL sync capability | target cell sync를 미리 수행할 수 있는지 |
| early UL sync capability | target cell UL timing/TA를 미리 준비할 수 있는지 |
| RACH-less LTM capability | valid TA 기반 RACH-less switch 지원 여부 |
| CLTM capability | Rel.19 conditional LTM 지원 여부 |

Capability 연결은 다음이다.

```text
UE가 LTM capability 미지원
  → gNB는 LTM candidate config를 주면 안 됨

UE가 candidate cell 수 제한
  → RRC의 LTM-CandidateConfig 수는 capability 이내여야 함

UE가 RACH-less 미지원
  → gNB는 RACH-based LTM 중심으로 설정해야 함

UE가 early UL sync 미지원
  → TA 기반 fast switch 절차를 제한해야 함
```

즉, 38.306은 LTM에서 **network가 구성할 수 있는 기능 범위의 상한선**을 정한다.

---

## 10. Rel.19 확장: CLTM

Rel.19의 핵심 확장 중 하나는 **CLTM, Conditional LTM**이다.

기존 Rel.18 LTM은 gNB가 MAC CE로 “지금 target으로 바꿔라”를 지시하는 구조에 가깝다. CLTM은 UE가 RRC로 받은 조건을 평가하다가, 조건이 만족되면 lower-layer 절차로 cell switch를 실행하는 방향이다.

```text
Rel.18 LTM:
  RRC로 candidate config 준비
  gNB MAC CE로 cell switch command
  UE가 target cell로 switch

Rel.19 CLTM:
  RRC로 candidate config + execution condition 준비
  UE가 L1/L3 condition 평가
  조건 만족 시 UE가 target cell로 switch
```

CLTM 절차를 요약하면 다음이다.

```text
1. RRC가 CLTM candidate configuration과 execution condition 제공
2. UE가 configuration을 저장하고 조건 평가 시작
3. early DL sync 수행 가능
4. L1/L3 condition이 만족되면 UE가 target cell로 switch
5. valid TA가 있으면 RACH-less 가능
6. valid TA가 없으면 CFRA/CBRA 등 RACH-based access
7. CLTM에서는 LTM MAC CE 없이 UE가 조건 만족 시 실행
8. 실행 시 MAC reset 수행
```

Rel.18 LTM과 Rel.19 CLTM의 차이는 다음이다.

| 구분 | Rel.18 LTM | Rel.19 CLTM |
|---|---|---|
| 실행 trigger | gNB MAC CE cell switch command | UE가 조건 만족 시 실행 |
| 후보 설정 | RRC preconfiguration | RRC conditional configuration |
| measurement | L1/L3 measurement 기반 | L1/L3 condition 평가 |
| RACH-less | valid TA 있으면 가능 | valid TA 있으면 가능 |
| MAC CE | 핵심 실행 trigger | CLTM 실행에는 LTM MAC CE 불필요 |
| 목적 | fast network-controlled mobility | faster conditional lower-layer mobility |

Rel.19에서 절차가 확장된 필요성은 다음이다.

```text
gNB가 매번 MAC CE로 switch 타이밍을 지시하면
  → signaling delay와 scheduling dependency가 있음

UE가 조건을 직접 평가하고 실행하면
  → 빠른 mobility 가능
  → 고속 이동/FR2/small cell 환경에서 interruption 감소 가능
```

---

## 11. Rel.20 확장 방향

Rel.20은 진행 중인 영역이므로 확정적인 normative description처럼 쓰면 안 된다. 다만 공개 scope와 draft CR을 기준으로 하면 다음 방향이 보인다.

| 확장 방향 | 필요성 |
|---|---|
| lower-layer triggered mobility 추가 개선 | LTM/CLTM의 interruption time과 robustness 개선 |
| SCell activation과 LTM 연계 | CA/DC 환경에서 serving cell뿐 아니라 secondary cell activation 지연 감소 |
| DC/inter-CU LTM | multi-node, inter-gNB, inter-CU mobility에서 LTM 적용 범위 확대 |
| conditional LTM RRM requirement 정교화 | UE가 조건 만족 판단과 switch delay를 얼마나 빠르고 안정적으로 수행해야 하는지 명확화 |
| RACH-based conditional LTM 상태 정리 | switch 후 activated TCI state, candidate state, MAC/RRC state cleanup 문제 해결 |
| mobility enhancement phase 4 | Rel.18/19 mobility 기능의 coverage와 안정성 개선 |

Rel.20 방향을 한 줄로 쓰면 다음이다.

```text
Rel.18 LTM:
  network-controlled lower-layer cell switch

Rel.19 CLTM:
  condition-based UE-triggered lower-layer cell switch

Rel.20:
  CA/DC/inter-CU/SCell activation 등 더 복잡한 deployment로 lower-layer mobility 확장
```

---

## 12. 최종 요약

```text
기존 RRC handover latency 문제
  → Rel.18 LTM: RRC preconfiguration + MAC CE cell switch
  → 38.300이 개념/절차
  → 38.331이 candidate config/TCI/CSI resource 구성
  → 38.321이 LTM MAC CE 실행
  → 38.214가 L1 measurement/reporting 및 QCL/TCI assumption
  → 38.133이 interruption/RRM requirement
  → 38.306이 UE capability
  → Rel.19 CLTM: 조건 만족 시 UE-triggered lower-layer mobility
  → Rel.20: SCell/DC/inter-CU/conditional LTM 성능 확장
```

LTM의 핵심은 **handover 준비는 RRC로 미리 해두고, 실행은 L1/L2에서 빠르게 하는 것**이다. Rel.19/20으로 갈수록 이 구조는 network-controlled LTM에서 conditional/UE-triggered mobility, 그리고 CA/DC/inter-CU 환경으로 확장된다.

---

## 참고 출처

- 3GPP TS 38.300: NR overall description
- 3GPP TS 38.331: Radio Resource Control protocol specification
- 3GPP TS 38.321: Medium Access Control protocol specification
- 3GPP TS 38.214: Physical layer procedures for data
- 3GPP TS 38.133: Requirements for support of radio resource management
- 3GPP TS 38.306: UE radio access capabilities
- Qualcomm, 3GPP Release 19/20 overview 자료
