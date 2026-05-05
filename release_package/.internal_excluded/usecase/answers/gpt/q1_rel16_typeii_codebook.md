# Rel.16 enhanced Type-II codebook 표준 아이템 정리

> 본 문서는 Rel.16 enhanced Type-II codebook을 WID 도입 배경, 38.211, 38.212, 38.214, 38.306, 38.331, 38.521-4 관점에서 문서 간 연결고리 중심으로 정리한 1차 분석안이다.  
> 참고: 질문의 `38.512-4`는 NR UE performance 문맥상 `TS 38.521-4: NR UE conformance specification; Radio transmission and reception; Part 4: Performance`로 해석했다.

---

## 1. 도입 배경: 왜 Rel.16 enhanced Type-II가 필요했나

Rel.15 Type-II CSI codebook은 고해상도 PMI 피드백을 통해 MU-MIMO 성능을 높이기 위한 구조였지만, CSI feedback overhead가 크고, 특히 wideband/subband coefficient를 많이 보고해야 하는 상황에서 uplink control overhead가 문제가 된다.

Rel.16 MIMO enhancement의 핵심 방향은 다음이다.

```text
Rel.15 Type-II
  고해상도 CSI 가능
  하지만 coefficient 보고량이 큼
  rank 확장과 overhead 문제가 있음

Rel.16 enhanced Type-II
  spatial-domain basis + frequency-domain basis + coefficient sparsity
  필요한 coefficient만 선택/보고
  MU-MIMO scheduler가 더 정교한 precoder를 구성 가능
  overhead는 Rel.15 Type-II 대비 제어
```

즉, Rel.16 enhanced Type-II codebook은 단순히 더 복잡한 codebook이 아니라, **MU-MIMO에서 scheduler가 더 정교한 channel direction 정보를 얻으면서도 CSI feedback overhead를 제어하기 위한 구조**라고 볼 수 있다.

---

## 2. 문서 간 연결 흐름

```text
38.331
  CSI-ReportConfig / CodebookConfig-r16에서 typeII-r16 또는 관련 Type-II 설정
  NZP-CSI-RS-ResourceSet / CSI-RS-ResourceMapping으로 CSI 측정 자원 구성
      ↓
38.211
  CSI-RS resource가 실제 RE/port/CDM/frequency/time 위치에 어떻게 매핑되는지 정의
      ↓
38.214
  UE가 CSI-RS를 측정하고, enhanced Type-II codebook 기반으로 PMI/RI/CQI 계산
      ↓
38.212
  계산된 RI/CQI/PMI/non-zero coefficient 정보를 UCI Part 1/Part 2 bit field로 인코딩
      ↓
38.306
  UE가 enhanced Type-II codebook, port-selection, rank/port 조합을 지원하는지 capability 보고
      ↓
38.521-4
  해당 CSI reporting 기능이 실제 무선 조건에서 요구 성능을 만족하는지 conformance test
```

핵심은 **38.331이 설정을 깔고, 38.211이 CSI-RS의 실제 물리 자원을 정의하고, 38.214가 codebook 수학/절차를 정의하고, 38.212가 UCI bit field를 정의하고, 38.306/38.521-4가 각각 capability와 성능 검증을 담당**한다는 점이다.

---

## 3. 38.331: RRC parameter

RRC에서는 크게 두 가지를 구성한다.

첫째, **무엇을 측정할지**이다. `NZP-CSI-RS-ResourceSet`, `NZP-CSI-RS-Resource`, `CSI-RS-ResourceMapping` 등을 통해 CSI-RS 자원을 구성한다. `CSI-RS-ResourceMapping`에는 `frequencyDomainAllocation`, `nrofPorts`, `firstOFDMSymbolInTimeDomain`, `cdm-Type`, `density`, `freqBand` 같은 필드가 포함된다.

둘째, **어떤 codebook으로 CSI를 보고할지**이다. `CSI-ReportConfig` 안의 `CodebookConfig` 계열에서 Type-II codebook을 설정하며, Rel.16에서는 `CodebookConfig-r16`에 `typeII-r16` 계열 설정이 들어간다.

| RRC 영역 | 역할 |
|---|---|
| `CSI-ReportConfig` | CSI 보고 방식, 보고 주기, codebook type, report quantity 설정 |
| `CodebookConfig-r16` | Rel.16 enhanced Type-II codebook 관련 설정 |
| `CSI-ResourceConfig` | CSI 측정 대상 resource set 연결 |
| `NZP-CSI-RS-ResourceSet` | 하나 이상의 NZP CSI-RS resource 묶음 |
| `NZP-CSI-RS-Resource` | 개별 CSI-RS resource |
| `CSI-RS-ResourceMapping` | CSI-RS port 수, RE 위치, CDM, density, RB 범위 |

RRC 관점에서 보면 enhanced Type-II codebook은 독립적으로 존재하는 것이 아니라, **CSI-RS resource configuration과 CSI report configuration이 결합된 기능**이다.

---

## 4. 38.211: CSI-RS resource configuration

38.211은 CSI-RS가 실제 물리 자원에 어떻게 매핑되는지를 정의한다. CSI-RS resource mapping에는 다음과 같은 요소가 관여한다.

| 항목 | 의미 |
|---|---|
| `nrofPorts` | CSI-RS antenna port 수 |
| `frequencyDomainAllocation` | 주파수 영역 RE 배치 |
| `firstOFDMSymbolInTimeDomain` | 시간 영역 시작 OFDM symbol |
| `cdm-Type` | CDM 방식 |
| `density` | CSI-RS density |
| `freqBand` | CSI-RS가 배치되는 RB 범위 |

enhanced Type-II codebook 관점에서 중요한 점은, **CSI-RS port 수와 resource 구성이 codebook dimension을 결정**한다는 것이다.

```text
RRC의 nrofPorts / CSI-RS resource set
  ↓
38.211의 CSI-RS port 및 RE mapping
  ↓
UE가 해당 CSI-RS를 측정
  ↓
38.214 codebook의 spatial/frequency basis와 coefficient 산출
```

특히 고차 MIMO나 다수 antenna port에서 Type-II codebook의 이점이 커지므로, CSI-RS port configuration은 enhanced Type-II codebook의 전제 조건이다.

---

## 5. 38.214: codebook 정의

38.214는 UE가 측정한 CSI-RS로부터 어떤 codebook 구조를 사용해 PMI를 만들지 정의한다. Rel.16 enhanced Type-II의 핵심은 단순히 “beam index 하나를 고르는 것”이 아니라, **여러 basis vector와 coefficient를 사용해 precoding matrix를 구성**하는 것이다.

동작을 간단히 쓰면 다음과 같다.

```text
1. UE가 CSI-RS를 측정
2. spatial-domain basis 후보를 선택
3. frequency-domain basis 후보를 선택
4. 각 layer별 coefficient를 계산
5. 의미 있는 non-zero coefficient만 선택
6. RI/CQI/PMI/LI/non-zero coefficient 정보를 CSI report로 구성
```

여기서 중요한 개념은 다음이다.

| 개념 | 의미 |
|---|---|
| spatial-domain basis | 안테나/beam 방향 영역의 basis |
| frequency-domain basis | 주파수 선택적 채널 변화를 표현하기 위한 basis |
| coefficient | 선택된 basis를 조합하는 가중치 |
| non-zero coefficient | 실제 보고할 의미 있는 coefficient |
| bitmap | 어떤 basis/coefficient가 선택되었는지 표시 |
| RI/CQI/PMI/LI | rank, channel quality, precoder matrix, layer indicator 관련 CSI 정보 |

즉, enhanced Type-II는 **채널을 sparse한 basis 조합으로 표현해서 feedback overhead를 줄이는 구조**라고 이해할 수 있다.

---

## 6. 38.212: UCI field 정보

38.212는 CSI report가 UCI bitstream으로 어떻게 인코딩되는지를 정의한다. Type-II 계열 CSI report는 보통 **Part 1**과 **Part 2**로 나뉜다.

| UCI part | 주요 내용 |
|---|---|
| CSI Part 1 | RI, CQI, total non-zero coefficient 수 등 Part 2 decoding에 필요한 정보 |
| CSI Part 2 | PMI, LI, coefficient 관련 상세 정보 |

38.214가 “무슨 정보를 계산해야 하는가”를 정의한다면, 38.212는 “그 정보를 UCI로 몇 bit에 어떻게 실어 보내는가”를 정의한다.

문서 연결은 다음과 같다.

```text
38.214
  UE가 RI/CQI/PMI/LI/coefficient 정보 계산
      ↓
38.212
  CSI Part 1 / Part 2 field로 bit encoding
      ↓
PUCCH 또는 PUSCH를 통해 CSI report 전송
```

enhanced Type-II에서 Part 1이 중요한 이유는, Part 2의 payload 크기가 RI나 non-zero coefficient 수에 따라 달라질 수 있기 때문이다. 즉, Part 1은 단순한 CSI 정보가 아니라 **Part 2를 해석하기 위한 meta-information** 역할도 한다.

---

## 7. 38.306: UE capability

38.306에서는 UE가 어떤 Type-II/eType-II codebook 조합을 지원하는지 capability로 보고한다. Capability는 gNB가 RRC 설정을 줄 때 지켜야 하는 상한선이다.

중요한 capability 범주는 다음과 같다.

| Capability 범주 | 의미 |
|---|---|
| enhanced Type-II rank 지원 | rank 1/2 또는 그 이상 지원 여부 |
| CSI-RS port 수 지원 | 몇 port CSI-RS 기반 codebook을 처리 가능한지 |
| port-selection Type-II 지원 | port-selection 기반 Type-II codebook 지원 여부 |
| frequency-domain compression 지원 | FD basis 기반 compression 지원 여부 |
| coefficient 보고 조합 | non-zero coefficient 수, amplitude/phase reporting 조합 지원 |

연결고리는 다음이다.

```text
UE capability가 enhanced Type-II 미지원
  → gNB는 해당 CodebookConfig를 주면 안 됨

UE capability가 특정 rank/port 조합만 지원
  → RRC의 CSI-RS port 수, CodebookConfig, report setting은 그 범위 내에서 구성되어야 함

UE capability가 port-selection Type-II 지원
  → gNB는 port-selection 기반 CSI reporting을 구성 가능
```

따라서 38.306은 scheduler/RRC configuration의 **가능 범위**를 정한다.

---

## 8. 38.521-4: 성능 requirement

질문에 적힌 38.512-4는 38.521-4로 해석했다. 38.521-4는 NR UE radio transmission/reception performance conformance 문서이며, CSI reporting conducted requirement를 포함한다.

38.521-4의 CSI reporting requirement는 “UE가 특정 CSI-RS/채널 조건에서 올바른 CSI를 보고할 수 있는가”를 검증한다.

연결 구조는 다음과 같다.

```text
38.331/38.211
  CSI-RS와 codebook 설정
38.214
  UE가 PMI/CQI/RI 계산
38.212
  UCI encoding
38.521-4
  이 CSI reporting이 시험 조건에서 요구 성능을 만족하는지 검증
```

성능 requirement 관점에서는 다음이 중요하다.

| 항목 | 의미 |
|---|---|
| CSI reporting accuracy | UE가 요구되는 PMI/CQI/RI를 적절히 보고하는지 |
| multiple PMI/reporting scenario | 복수 PMI 또는 복잡한 CSI report 상황에서의 정확성 |
| Type-II/eType-II optional feature test | capability가 있는 UE에 대해 해당 기능 성능 검증 |
| FR1/FR2 조건 | band와 RF 조건에 따른 시험 구성 |
| 2Rx/4Rx, Tx port 조합 | UE RF chain 및 CSI-RS port 조합별 검증 |

---

## 9. 최종 요약

```text
Rel.16 MIMO WID
  → MU-MIMO 성능 향상과 CSI overhead 절감
  → 38.331이 CSI-RS/codebook report 설정
  → 38.211이 CSI-RS resource mapping
  → 38.214가 enhanced Type-II codebook 계산
  → 38.212가 UCI Part 1/2 bit field 정의
  → 38.306이 UE 지원 capability 제한
  → 38.521-4가 CSI reporting performance 검증
```

enhanced Type-II codebook은 **CSI-RS 측정 자원, codebook 계산, UCI encoding, UE capability, conformance requirement가 강하게 연결된 기능**이다. 따라서 단일 clause만 보는 것보다, 위 문서 흐름대로 추적해야 표준 동작을 제대로 이해할 수 있다.

---

## 참고 출처

- 3GPP TS 38-series list: https://www.3gpp.org/dynareport/38-series.htm
- 3GPP TS 38.211, 38.212, 38.214, 38.306, 38.331
- 3GPP TS 38.521-4
- 5G Americas, 5G Evolution: 3GPP Releases 16 and 17 overview
