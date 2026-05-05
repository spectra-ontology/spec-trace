# Rel.15부터 Rel.20까지 TCI-state 관련 표준 아이템 정리

> 본 문서는 Rel.15부터 Rel.20까지 TCI-state 관련 기능을 WID 도입 배경, 38.214의 QCL assumption, 38.321의 MAC CE 절차, 38.331의 RRC parameter, 38.306의 UE capability 관점에서 문서 간 연결고리 중심으로 정리한 1차 분석안이다.  
> Rel.20은 아직 진행 중인 영역이므로, frozen normative behavior처럼 단정하지 않고 공개된 scope와 draft CR 기반의 확장 방향으로 정리한다.

---

## 1. TCI-state의 본질

TCI-state는 간단히 말하면 **“이 PDSCH/PDCCH/CSI-RS/UL 전송을 어떤 reference signal과 같은 beam/QCL 관계로 해석할 것인가”**를 알려주는 상태이다.

QCL, 즉 quasi co-location은 두 antenna port 사이에서 한 port의 channel property를 다른 port의 channel property 추정에 사용할 수 있다는 의미이다.

QCL type은 대략 다음과 같이 이해할 수 있다.

| QCL type | 포함되는 channel property |
|---|---|
| Type A | Doppler shift, Doppler spread, average delay, delay spread |
| Type B | Doppler shift, Doppler spread |
| Type C | Doppler shift, average delay |
| Type D | spatial Rx parameter |

특히 beam management 관점에서는 **QCL Type D**가 중요하다. Type D는 UE가 어떤 receive beam 또는 spatial filter를 사용해야 하는지와 연결되기 때문이다.

---

## 2. 문서 간 연결 구조

```text
38.331
  TCI-State / dl-OrJointTCI-StateList / ul-TCI-StateList 구성
      ↓
38.321
  MAC CE로 TCI state activation/deactivation 또는 DCI codepoint mapping
      ↓
38.214
  UE가 DCI의 TCI field 또는 default rule에 따라 QCL assumption 적용
      ↓
38.306
  UE가 지원 가능한 TCI state 수, active TCI 수, unified TCI 기능을 capability로 보고
```

핵심은 다음이다.

```text
RRC는 후보를 깔아준다.
MAC CE는 그 후보 중 실제 활성화할 것을 고른다.
DCI는 활성화된 후보 중 어느 것을 이번 전송에 적용할지 지시한다.
PHY는 해당 TCI-state의 QCL assumption을 적용한다.
UE capability는 이 전체 설정의 상한선을 정한다.
```

---

## 3. Release별 큰 흐름

| Release | 표준 아이템 관점 | 38.214 QCL/TCI | 38.321 MAC CE | 38.331 RRC parameter | 38.306 UE capability |
|---|---|---|---|---|---|
| Rel.15 | NR initial access/beam management baseline | PDSCH/PDCCH/CSI-RS에 대한 TCI-state와 QCL assumption 도입 | PDSCH TCI activation/deactivation, PDCCH TCI indication | `TCI-State`, `PDSCH-Config.tci-StatesToAddModList`, CORESET/search space 관련 TCI | configured TCI state 수, active TCI per BWP/CC |
| Rel.16 | MIMO/multi-TRP enhancement | single-DCI multi-TRP 등에서 복수 TCI state 적용 기반 확장 | enhanced PDSCH TCI activation, multi-TRP 관련 TCI mapping | simultaneous TCI update list, serving-cell 공통/그룹 activation | multi-TRP/복수 TCI 관련 capability |
| Rel.17 | Unified TCI | DL TCI와 UL spatial relation을 unified framework로 통합 | unified TCI states activation/deactivation MAC CE | `dl-OrJointTCI-StateList`, `ul-TCI-StateList`, `unifiedTCI-StateType` | joint/separate unified TCI 지원 |
| Rel.18 | Enhanced unified TCI, LTM 연계, multi-TRP 고도화 | DCI 1_1/1_2/1_3, joint/separate TCI, candidate-cell TCI와 연계 | enhanced unified TCI, LTM cell switch, candidate cell TCI, BFD-RS indication | LTM candidate TCI, Rel.18 unified TCI capability 확장 | multi-active TCI, CJT, per-CORESETPoolIndex 등 |
| Rel.19 | LTM/CLTM 및 inter-cell beam management 확장 | candidate TCI, CLTM, serving/candidate cell beam assumption 확장 | Enhanced LTM, candidate cell TCI, CLTM 관련 절차 | CLTM/LTM 후보 cell 및 조건부 설정 | CLTM, enhanced mobility, eType-II/CJT 등 capability 확장 |
| Rel.20 | 진행 중. Mobility enhancement phase 4, LTM/CLTM 추가 확장 | 아직 frozen spec으로 단정하면 안 됨 | conditional LTM, SCell activation, DC/inter-CU 관련 확장 논의 | 조건부 mobility/LTM 후보 설정 확장 방향 | Rel.20 capability는 최종 spec freeze 전까지 유동적 |

---

## 4. Rel.15 baseline TCI

Rel.15에서 TCI-state는 NR beam-based operation의 핵심이었다. RRC가 여러 TCI-state를 configure하고, MAC CE가 그중 일부를 activate하며, DCI의 TCI field가 실제 PDSCH 수신 시 어떤 QCL assumption을 적용할지 지정하는 구조이다.

연결은 다음과 같다.

```text
RRC: TCI-State 후보 n개 구성
  ↓
MAC CE: 그중 active set을 DCI codepoint에 mapping
  ↓
DCI: codepoint 하나 지시
  ↓
PHY: 해당 TCI-State의 QCL Type A/B/C/D 적용
```

Rel.15의 기본 구조는 다음과 같다.

| 문서 | 역할 |
|---|---|
| 38.331 | `TCI-State`, `PDSCH-Config.tci-StatesToAddModList`, CORESET 관련 TCI 설정 |
| 38.321 | PDSCH TCI states activation/deactivation MAC CE |
| 38.214 | PDSCH 수신 시 DCI TCI field 또는 default TCI state 기반 QCL assumption 적용 |
| 38.306 | configured/active TCI state 수, QCL Type-D 관련 capability 보고 |

Rel.15 TCI의 핵심 목적은 **PDSCH/PDCCH 수신 beam을 명확히 지시하여 beamformed NR operation을 안정적으로 지원하는 것**이다.

---

## 5. Rel.16: multi-TRP와 enhanced TCI activation

Rel.16에서는 multi-TRP operation이 중요해졌다. 특히 single-DCI multi-TRP에서는 하나의 DCI로 여러 TRP에서 오는 PDSCH를 제어해야 하므로, TCI-state도 단순히 하나만 지시하는 구조로는 부족하다.

정리하면 다음과 같다.

```text
Rel.15
  DCI codepoint → TCI-state 1개

Rel.16 multi-TRP
  DCI codepoint → TCI-state pair 또는 복수 TCI state
  → single-DCI multi-TRP PDSCH 수신 가능
```

Rel.16 TCI 확장의 의미는 다음이다.

| 항목 | 의미 |
|---|---|
| multi-TRP | 여러 TRP가 동일 UE에게 전송 |
| single-DCI multi-TRP | 하나의 DCI로 복수 TRP 전송 제어 |
| 복수 TCI-state | TRP별 beam/QCL assumption을 구분하기 위함 |
| enhanced TCI activation | DCI codepoint와 복수 TCI-state mapping을 지원하기 위한 MAC CE 확장 |

문서 간 연결은 다음이다.

```text
38.331
  multi-TRP에 필요한 TCI 후보 구성
      ↓
38.321
  enhanced TCI activation MAC CE로 codepoint와 TCI pair mapping
      ↓
38.214
  PDSCH 수신 시 복수 TCI-state/QCL assumption 적용
      ↓
38.306
  UE가 multi-TRP/복수 TCI 처리를 지원하는지 capability 보고
```

---

## 6. Rel.17: Unified TCI

Rel.17의 중요한 변화는 **DL beam indication과 UL spatial relation을 unified TCI framework로 묶은 것**이다.

기존에는 대략 다음 구조였다.

```text
기존:
  DL: TCI-State
  UL: spatial relation / SRS resource indicator 등 별도 구조
```

Rel.17 unified TCI에서는 다음 구조가 가능해졌다.

```text
Rel.17:
  joint TCI: DL beam과 UL spatial filter를 함께 지시
  separate TCI: DL TCI와 UL TCI를 분리 지시
```

즉, unified TCI는 beam indication을 DL 중심에서 DL/UL 공통 또는 분리 구조로 확장한 것이다.

| 문서 | Rel.17 unified TCI 역할 |
|---|---|
| 38.331 | `dl-OrJointTCI-StateList`, `ul-TCI-StateList`, `unifiedTCI-StateType` 등 설정 |
| 38.321 | unified TCI states activation/deactivation MAC CE |
| 38.214 | joint/separate TCI 적용 방식, DL QCL 및 UL spatial filter 해석 |
| 38.306 | joint/separate unified TCI 지원 capability 보고 |

이 구조의 장점은 다음이다.

```text
DL beam 관리와 UL spatial filter 관리가 분리되어 있으면
  → 설정/activation/signaling이 복잡해짐

Unified TCI 도입
  → DL/UL beam 관련 지시를 일관된 TCI framework로 통합
  → multi-TRP, FR2, mobility 환경에서 beam update 효율 증가
```

---

## 7. Rel.18: enhanced unified TCI, LTM, candidate-cell TCI

Rel.18에서는 unified TCI가 더 복잡한 mobility/multi-TRP 상황과 연결된다.

특히 LTM, 즉 L1/L2 Triggered Mobility가 도입되면서, TCI-state는 단순한 serving cell beam indication을 넘어 **candidate target cell로 이동할 때 어떤 beam/QCL assumption을 적용할 것인가**까지 포함하게 된다.

Rel.18의 특징은 다음과 같다.

| 항목 | 의미 |
|---|---|
| enhanced unified TCI | joint/separate TCI 구조를 더 다양한 DCI/MAC CE 구조와 연결 |
| multiple active TCI | 복수 active beam/TCI를 동시에 다루는 방향 |
| LTM candidate TCI | candidate target cell에서 사용할 TCI-state를 미리 준비 |
| candidate cell TCI indication | MAC CE로 target/candidate cell의 TCI를 지시 |
| BFD-RS indication | beam failure detection resource와 TCI 관계 정교화 |

문서 연결은 다음이다.

```text
38.331
  LTM candidate cell configuration과 candidate TCI-state 구성
      ↓
38.321
  LTM Cell Switch Command / Candidate Cell TCI State Indication MAC CE
      ↓
38.214
  LTM 전환 시 CandidateTCI-State 또는 indicated TCI 기반 QCL assumption 적용
      ↓
38.306
  LTM, unified TCI, multiple active TCI 관련 capability 보고
```

Rel.18의 핵심은 **TCI-state가 mobility execution과 직접 연결되기 시작했다**는 점이다.

---

## 8. Rel.19: LTM/CLTM 및 inter-cell beam management 확장

Rel.19에서는 Rel.18 LTM의 구조가 더 확장된다. 특히 CLTM, 즉 Conditional LTM이 중요하다.

Rel.18 LTM은 대체로 다음 구조이다.

```text
RRC로 candidate config 준비
  ↓
gNB가 MAC CE로 cell switch 명령
  ↓
UE가 target cell로 빠르게 전환
```

Rel.19 CLTM은 다음 구조에 가깝다.

```text
RRC로 candidate config와 execution condition 준비
  ↓
UE가 조건을 평가
  ↓
조건 만족 시 UE가 lower-layer mobility 실행
```

TCI-state 관점에서는 다음이 중요하다.

| 항목 | 의미 |
|---|---|
| candidate cell TCI | target 후보 cell에서 사용할 beam/QCL assumption |
| CLTM condition | 특정 measurement 조건 만족 시 switch 실행 |
| serving/candidate beam 관리 | serving cell과 candidate cell의 beam을 동시에 관리 |
| inter-cell beam management | cell 간 beam 전환을 더 낮은 layer에서 빠르게 처리 |
| CJT/multi-TRP 연계 | coordinated joint transmission과 TCI 확장 |

문서 연결은 다음이다.

```text
38.331
  CLTM candidate config, condition, candidate TCI 구성
      ↓
38.214
  candidate cell measurement 및 QCL/TCI assumption
      ↓
38.321
  LTM/Enhanced LTM/Candidate Cell TCI 관련 MAC CE
      ↓
38.306
  CLTM, enhanced mobility, candidate beam/TCI capability 보고
```

---

## 9. Rel.20: 진행 중인 확장 방향

Rel.20은 아직 진행 중인 영역이므로 확정된 최종 표준처럼 쓰면 안 된다. 다만 공개된 scope와 draft CR 방향을 기준으로 보면 다음과 같은 확장이 예상된다.

| 확장 방향 | 필요성 |
|---|---|
| Mobility enhancement phase 4 | Rel.18/19 LTM/CLTM의 coverage와 robustness 개선 |
| lower-layer triggered mobility 추가 개선 | RRC handover latency를 더 줄이기 위함 |
| SCell activation 연계 | CA 환경에서 SCell activation delay 감소 |
| DC/inter-CU LTM | dual connectivity 또는 inter-CU 환경까지 LTM 확장 |
| conditional LTM RRM requirement | UE-triggered mobility의 delay와 reliability requirement 명확화 |
| RACH-based conditional LTM 후처리 | switch 후 TCI state, MAC state, RRC state 정리 문제 해결 |

Rel.20에서는 TCI-state가 더 이상 단순 beam indication이 아니라, **mobility, candidate cell, SCell activation, DC architecture와 결합된 lower-layer control state**로 확장될 가능성이 크다.

---

## 10. 최종 요약

```text
Rel.15 beam/QCL baseline
  → Rel.16 multi-TRP
  → Rel.17 unified TCI
  → Rel.18 enhanced unified TCI + LTM candidate TCI
  → Rel.19 CLTM/inter-cell beam management
  → Rel.20 mobility enhancement phase 4

38.331 TCI 후보 구성
  → 38.321 MAC CE activation/mapping
  → 38.214 QCL assumption 적용
  → 38.306 capability 보고
```

TCI-state는 release가 올라가면서 다음처럼 진화했다.

```text
Rel.15: DL beam/QCL indication
Rel.16: multi-TRP 복수 TCI
Rel.17: DL/UL unified TCI
Rel.18: LTM candidate cell TCI와 mobility 연계
Rel.19: CLTM/inter-cell beam management 확장
Rel.20: lower-layer mobility, SCell/DC/inter-CU까지 확장 중
```

---

## 참고 출처

- 3GPP TS 38.214: Physical layer procedures for data
- 3GPP TS 38.321: Medium Access Control protocol specification
- 3GPP TS 38.331: Radio Resource Control protocol specification
- 3GPP TS 38.306: UE radio access capabilities
- 3GPP TS 38.300: NR overall description
- 5G Americas, 5G Advanced / 3GPP release overview 자료
- Qualcomm, 3GPP Release 19/20 overview 자료
