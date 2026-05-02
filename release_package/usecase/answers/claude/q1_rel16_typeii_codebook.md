# Rel.16 Enhanced Type-II Codebook 표준 분석 보고서

## 목차
1. [도입 배경 (WID 관점)](#1-도입-배경-wid-관점)
2. [38.211 — CSI-RS Resource Configuration](#2-38211--csi-rs-resource-configuration)
3. [38.212 — UCI Field 정의](#3-38212--uci-field-정의)
4. [38.214 — Enhanced Type-II Codebook 정의](#4-38214--enhanced-type-ii-codebook-정의)
5. [38.306 — UE Capability](#5-38306--ue-capability)
6. [38.331 — RRC Parameter](#6-38331--rrc-parameter)
7. [38.512-4 — 성능 Requirement](#7-38512-4--성능-requirement)
8. [문서 간 연결 구조](#8-문서-간-연결-구조)

---

## 1. 도입 배경 (WID 관점)

### 1.1 Rel.15 Type-II Codebook의 한계

Rel.15에서 도입된 Type-II codebook은 MU-MIMO를 위한 high-resolution PMI를 제공하기 위해 설계되었다. 그러나 다음과 같은 명확한 한계가 있었다:

- **과도한 UCI overhead**: Type-II PMI는 SD(Spatial Domain) basis별로 모든 subband에 대해 amplitude와 phase coefficient를 직접 quantize하여 보고하기 때문에, rank-2, 32 ports, 19 subbands 환경에서 수백~1000+ bit에 달하는 payload가 발생.
- **UCI segmentation 문제**: PUCCH format 3/4의 capacity를 초과하면 CSI part가 omission되거나 multi-part로 split되어 정확도가 떨어짐.
- **MU-MIMO 성능 vs overhead trade-off의 비효율성**: 실제 channel은 frequency domain에서 강한 correlation을 가지므로 subband별 독립 quantization은 redundant.

### 1.2 RP-182863 / RP-191085 (NR MIMO Enhancement WID)

Rel.16의 NR MIMO Enhancement WI(RP-182863로 시작, RP-191085로 revise)는 다음을 핵심 objective로 명시했다:

> *"Specify enhancement on CSI reporting for MU-MIMO with focus on overhead reduction, including DFT-based compression in frequency domain."*

핵심 motivation은 다음 두 가지로 요약된다:

1. **Frequency domain compression**: Subband별 독립 PMI 대신, FD basis(DFT vectors)를 사용해 압축된 형태로 보고.
2. **Overhead 절감**: 동일 또는 유사한 MU-MIMO 성능을 유지하면서 PMI payload를 50% 이상 감소.

### 1.3 핵심 기술 컨셉

Enhanced Type-II는 Rel.15 Type-II의 SD basis 선택 구조는 유지하되, **FD basis를 추가로 도입한 3-stage compression** 구조이다:

```
W = W₁ · W̃₂ · W_f^H
```

- **W₁**: SD basis selection (Rel.15와 유사, 2L beams 선택)
- **W̃₂**: SD-FD coefficient matrix (linear combination coefficient들의 압축된 형태)
- **W_f**: FD basis selection (Mv개의 DFT vector 선택)

추가로 도입된 핵심 기법은 **bitmap-based non-zero coefficient indication**이다. 전체 2L×Mv coefficient 중 K0 = ⌈β·2LMv⌉ 개의 non-zero coefficient만 보고한다.

---

## 2. 38.211 — CSI-RS Resource Configuration

### 2.1 NZP-CSI-RS Resource for Enhanced Type-II

38.211 Clause 7.4.1.5에 정의된 NZP-CSI-RS의 resource element 매핑은 Rel.15와 동일하나, Enhanced Type-II는 다음 configuration이 강제된다:

| 파라미터 | 값 | 비고 |
|---|---|---|
| Number of CSI-RS ports (P) | {4, 8, 12, 16, 24, 32} | Rel.15 Type-II와 동일 set |
| CDM type | `cdm8-FD2-TD4` 또는 `fd-CDM2`, `cdm4-FD2-TD2` | port 수에 따라 |
| Density (ρ) | 1 RE/RB/port | High-resolution PMI를 위해 1로 고정 |
| Frequency domain location | k̄ | TS 38.211 Table 7.4.1.5.3-1 참조 |

### 2.2 CSI-RS Sequence Generation

PN sequence 초기화는 다음과 같다:

$$c_{\text{init}} = \left( 2^{10}(N_{\text{symb}}^{\text{slot}} \cdot n_{s,f}^\mu + l + 1)(2 n_{ID} + 1) + n_{ID} \right) \bmod 2^{31}$$

여기서 `n_ID`는 `NZP-CSI-RS-Resource`의 `scramblingID`로부터 전달된다. Enhanced Type-II에서도 sequence generation은 변경되지 않는다.

### 2.3 Resource Mapping의 핵심 제약

Enhanced Type-II codebook은 **rank ≤ 4** 만 지원하므로 (38.214에서 정의), CSI-RS port 수와 rank의 조합은 제한적이다. CSI-RS는 반드시 **NZP-CSI-RS-ResourceSet** 내에서 단일 resource로 구성되어야 하며, port aggregation은 불가하다.

---

## 3. 38.212 — UCI Field 정의

38.212 Clause 6.3.1.1.2와 6.3.2.1.2에 Enhanced Type-II의 UCI field 구조가 정의되어 있다.

### 3.1 Two-Part UCI 구조

Enhanced Type-II는 **Type-II와 동일하게 two-part UCI**로 보고된다:

#### CSI Part 1 (고정 길이)
- RI (Rank Indicator): ⌈log₂(R_max)⌉ bits, R_max ∈ {1,2,3,4}
- Wideband CQI (4 bits)
- **Number of non-zero coefficients indication per layer**: ⌈log₂(K0+1)⌉ bits × R
  - 이 field가 Rel.15 대비 **새로 추가된 핵심 요소**이다. Part 2의 길이를 Part 1으로부터 결정하기 위함.

#### CSI Part 2 (가변 길이, Part 1로부터 결정)
- SD basis indication (W₁): ⌈log₂(C(N₁N₂, L))⌉ bits
- FD basis indication (W_f): per-layer indication (Mv 개의 DFT vector index)
- Bitmap of non-zero coefficients: 2LMv bits per layer
- Strongest coefficient indicator (SCI): ⌈log₂(2L)⌉ bits per layer
- Amplitude(reference) + amplitude(differential) + phase: 각 non-zero coefficient에 대해
- Subband CQI (per-CW): 2 bits per subband per CW

### 3.2 Priority 기반 Omission 규칙

Part 2가 PUCCH/PUSCH capacity를 초과하면 **priority 기반 omission**이 적용된다 (38.212 Clause 6.3.2.1.2). Priority는 다음 식으로 계산된다:

$$\text{Pri}(l, m) = 2 L \cdot R \cdot \pi(m) + R \cdot l + r$$

여기서:
- l: SD index, m: FD index, r: layer index
- π(m): permutation function — 0번째 FD index가 가장 높은 priority를 갖도록 reordering

낮은 priority group부터 순차적으로 drop되며, 이는 "graceful degradation"을 보장한다.

### 3.3 Bit Sequence 구성

UCI bit sequence 생성, polar coding, rate matching은 일반 UCI와 동일하다 (Clause 6.3.1, 6.3.2). 단, Part 1과 Part 2는 별도 polar code로 인코딩된다.

---

## 4. 38.214 — Enhanced Type-II Codebook 정의

### 4.1 Codebook 식별자

38.214 Clause 5.2.2.2.5에 **Type II Port Selection Codebook**과 함께 Clause 5.2.2.2.5에 새 codebook이 정의되어 있다. RRC parameter `codebookType`의 값으로 다음이 추가되었다:

- `typeII-r16` (Enhanced Type-II)
- `typeII-PortSelection-r16` (Enhanced Type-II Port Selection)

### 4.2 Precoder 수식 정의

Layer l에 대한 precoder는 다음과 같이 표현된다:

$$W^{(l)} = \frac{1}{\sqrt{N_1 N_2 \gamma^{(l)}}} \sum_{i=0}^{2L-1} \sum_{f=0}^{M_v - 1} v_{m_1^{(i)}, m_2^{(i)}} \cdot \tilde{w}_{i,f}^{(l)} \cdot y_f^{H}$$

- $v_{m_1, m_2}$: SD oversampled DFT vector (Rel.15 Type-II와 동일)
- $\tilde{w}_{i,f}^{(l)}$: SD-FD coefficient (compressed)
- $y_f$: FD DFT vector, length N₃ (number of precoding sub-bands × R)
- γ^(l): power normalization factor

### 4.3 핵심 파라미터: L, p_v, β

다음 세 파라미터가 codebook configuration의 trade-off를 결정한다:

| Parameter | 의미 | 가능한 값 |
|---|---|---|
| L | SD basis 개수 | {2, 4, 6} |
| p_v | FD basis 비율 (rank별로 다름) | {1/4, 1/2} for rank 1-2; {1/4} for rank 3-4 |
| β | Non-zero coefficient 비율 | {1/4, 1/2, 3/4} |

이 세 파라미터의 조합으로 8가지 `paramCombination-r16` 값이 정의되어 있다 (38.214 Table 5.2.2.2.5-1).

### 4.4 Mv 결정

FD basis 개수 Mv는 다음과 같이 결정된다:

$$M_v = \lceil p_v \cdot N_3 \rceil \quad \text{for rank 1, 2}$$
$$M_v = \lceil p_v \cdot N_3 / 2 \rceil \quad \text{for rank 3, 4}$$

N3는 다음과 같이 결정된다:
- `subbandAmplitude=true`인 경우: N₃ = NSB × R (R은 PMI subband 당 PRG 수)
- 기본: N₃ = NSB

### 4.5 Coefficient Quantization

Non-zero coefficient는 다음과 같이 양자화된다:

$$\tilde{w}_{i,f}^{(l)} = p_{i,f}^{(l)} \cdot \phi_{i,f}^{(l)}$$

- **Reference amplitude**: 4 bits (per polarization)
- **Differential amplitude**: 3 bits (each non-zero coefficient)
- **Phase**: 16-PSK (4 bits) for high-amplitude, 8-PSK (3 bits) for low-amplitude

### 4.6 Strongest Coefficient Indicator (SCI)

Layer l의 가장 강한 coefficient의 SD-FD index는 별도로 보고되며 (⌈log₂(2L·Mv)⌉ 또는 ⌈log₂(K0)⌉ bits), 해당 coefficient는 amplitude=1, phase=0으로 normalize된다.

### 4.7 Port Selection Variant

`typeII-PortSelection-r16`은 SD basis selection 대신, beamformed CSI-RS 환경에서 **L개의 port를 선택**한다. Operator가 BS에서 미리 beamforming을 적용한 CSI-RS를 송신할 때 사용된다.

---

## 5. 38.306 — UE Capability

### 5.1 관련 Capability Field

38.306 Clause 4.2.7.5 (CSI Reporting capability)에 다음 capability들이 정의되어 있다:

| Capability | 위치 | 의미 |
|---|---|---|
| `typeII-r16` | `csi-ReportFramework-r16` | Enhanced Type-II 지원 여부 |
| `typeII-PortSelection-r16` | 동일 | Port selection variant 지원 |
| `paramCombination-r16` | per-band | 지원하는 (L, p_v, β) 조합 |
| `maxNumberRxTxBeamSwitchDL` | per-band | beam switching capability와의 연관 |

### 5.2 Port 수와 Layer 제한

- 지원하는 max number of ports: {4, 8, 12, 16, 24, 32} 중 UE가 신고
- Max rank for Enhanced Type-II: **최대 4** (38.214 정의에 따른 제한)
- `simultaneousCSI-ReportsPerCC-r16` field로 동시 처리 가능한 CSI report 수 제한

### 5.3 Computational Complexity 관련

CSI computation은 38.214 Table 5.2.1.5-2에 정의된 **CSI processing units (CPUs)** 점유 수를 갖는다. Enhanced Type-II는 Rel.15 Type-II와 동일하게 N_CPU = 무제한(∞)으로 간주되어, 다른 CSI computation을 모두 block한다 (즉, 동시 1개만 처리 가능). 이는 implementation 부담을 반영한 것이다.

### 5.4 Frequency Granularity

`csi-ReportFrequencyGranularity-r16`로 PMI subband size R = 1 또는 R = 2를 indication. R = 2는 더 fine한 frequency resolution을 제공.

---

## 6. 38.331 — RRC Parameter

### 6.1 CodebookConfig IE의 확장

38.331에서 `CodebookConfig` IE는 다음과 같이 확장되었다:

```asn1
CodebookConfig ::= SEQUENCE {
    codebookType  CHOICE {
        type1    SEQUENCE { ... },
        type2    SEQUENCE { ... },
        ...,
        type2-r16  SEQUENCE {
            subType    CHOICE {
                typeII-r16                  TypeII-r16,
                typeII-PortSelection-r16    TypeII-PortSelection-r16
            },
            paramCombination-r16    INTEGER (1..8)
        }
    }
}
```

### 6.2 TypeII-r16 IE 상세

```asn1
TypeII-r16 ::= SEQUENCE {
    n1-n2-codebookSubsetRestriction-r16  CHOICE {
        two-one          BIT STRING (SIZE (16)),
        two-two          BIT STRING (SIZE (43)),
        ... (각 (N1, N2) 조합별)
    },
    typeII-RI-Restriction-r16    BIT STRING (SIZE (4)),
    numberOfPMI-SubbandsPerCQI-Subband-r16  INTEGER (1..2)
}
```

#### 핵심 sub-IE 의미:

- **`n1-n2-codebookSubsetRestriction-r16`**: SD beam restriction. 특정 (N1, N2) 조합에 대해 사용 가능한 oversampled DFT vector의 subset을 bitmap으로 제한.
- **`typeII-RI-Restriction-r16`**: 4 bits bitmap. UE가 보고할 수 있는 rank를 1~4 중 제한.
- **`numberOfPMI-SubbandsPerCQI-Subband-r16`**: R 값. 1 또는 2.

### 6.3 paramCombination-r16 표

`paramCombination-r16` (1~8)이 (L, p_v, β) 조합을 선택한다 (38.214 Table 5.2.2.2.5-1):

| Index | L | p_v (rank 1-2) | p_v (rank 3-4) | β |
|---|---|---|---|---|
| 1 | 2 | 1/4 | — | 1/4 |
| 2 | 2 | 1/4 | — | 1/2 |
| 3 | 4 | 1/4 | — | 1/4 |
| 4 | 4 | 1/4 | — | 1/2 |
| 5 | 4 | 1/4 | 1/4 | 3/4 |
| 6 | 4 | 1/2 | 1/4 | 1/2 |
| 7 | 6 | 1/4 | — | 1/2 |
| 8 | 6 | 1/4 | — | 3/4 |

### 6.4 CSI-ReportConfig 연동

```asn1
CSI-ReportConfig ::= SEQUENCE {
    ...,
    codebookConfig    CodebookConfig    OPTIONAL,
    reportFreqConfiguration    SEQUENCE {
        cqi-FormatIndicator    ENUMERATED { widebandCQI, subbandCQI },
        pmi-FormatIndicator    ENUMERATED { widebandPMI, subbandPMI },  -- 반드시 subbandPMI여야 함
        csi-ReportingBand    CHOICE { ... }
    }
}
```

Enhanced Type-II는 **반드시 `pmi-FormatIndicator = subbandPMI`** 이어야 하며, `reportQuantity = cri-RI-PMI-CQI` (또는 그에 상응)로 설정되어야 한다.

---

## 7. 38.512-4 — 성능 Requirement

> 주의: TS 38.512는 NR conformance test의 RRM 부분이다. CSI 관련 demodulation requirement는 주로 **TS 38.101-4** (UE demodulation)에 정의된다. Enhanced Type-II에 대한 specific test case는 **TS 38.101-4 Clause 5.2A** 부근에서 다루어진다. 본 보고서에서는 38.512 시리즈와 연관된 RRM 측면 + 38.101-4 demod 측면을 함께 정리한다.

### 7.1 Test Case 구조

CSI feedback 정확도 평가는 직접적인 PMI 비교가 아니라 **closed-loop throughput-based test**로 이루어진다:

- **PMI random vs PMI follow** 비교
- 동일 SNR 조건에서 PMI follow의 throughput이 reference random 대비 일정 % 이상 향상되어야 함

### 7.2 주요 Test Conditions (TS 38.101-4 기준)

| Parameter | Typical Value |
|---|---|
| Channel model | TDLA, TDLB, CDL-A, CDL-C |
| Number of CSI-RS ports | 16, 32 |
| Codebook | typeII-r16, paramCombination ∈ {6, 7} |
| MCS | Fixed (예: MCS index 13) |
| Transmission scheme | Closed-loop with PMI follow |
| Reference performance | Random PMI baseline |

### 7.3 성능 Metric

대표적으로:
- **Throughput gain**: Enhanced Type-II PMI 사용 시 random PMI 대비 throughput이 **30% 이상 향상**되어야 함 (typical CDL channel)
- **MU-MIMO scenario**: 2-UE MU-MIMO setup에서 sum throughput이 SU-MIMO + Type-I 대비 일정 비율 이상

### 7.4 RRM Side (38.133)

CSI reporting periodicity, latency 관점의 RRM 요구사항은 38.133 Clause 9.5에 정의되어 있다:

- **CSI reporting delay**: aperiodic CSI trigger부터 보고까지 Z₁/Z₁' symbol 이내
- Enhanced Type-II는 latency class 2 (relaxed timeline) 적용 가능
- Z₁ 값은 BWP의 SCS와 X (CSI processing capability)에 따라 결정

---

## 8. 문서 간 연결 구조

### 8.1 데이터 흐름 관점의 cross-reference

```
                    [WID: RP-191085]
                          │
                          ▼
                     설계 결정
        ┌─────────────┬──┴──┬──────────────┐
        ▼             ▼     ▼              ▼
   [38.211]      [38.214]   [38.331]    [38.306]
  CSI-RS 송신   Codebook    RRC 설정     Capability
   (P, CDM)     수식 (W)    (paramComb)  (지원여부)
        │             │     │              │
        └──────┬──────┘     │              │
               ▼            │              │
         UE: PMI 계산 ◄──────┘              │
               │                            │
               ▼                            │
          [38.212]                          │
        UCI 인코딩                          │
        (Part1/Part2)                       │
               │                            │
               ▼                            │
         BS: 디코딩                         │
               │                            │
               ▼                            │
       [38.101-4 / 38.512-4]                │
       성능 검증 ◄───────────────────────────┘
```

### 8.2 핵심 Cross-Reference 매트릭스

| Concept | 38.211 | 38.212 | 38.214 | 38.306 | 38.331 |
|---|---|---|---|---|---|
| CSI-RS 자원 | 7.4.1.5 (RE 매핑) | — | 5.2.2 (선택 규칙) | 4.2.7.5 | NZP-CSI-RS-Resource |
| Codebook 정의 | — | 6.3.1.1.2 (UCI 구성) | 5.2.2.2.5 (W 수식) | typeII-r16 capability | CodebookConfig.type2-r16 |
| paramCombination | — | UCI 길이 결정 입력 | Table 5.2.2.2.5-1 | 지원 조합 신고 | paramCombination-r16 |
| Non-zero coeff | — | bitmap field | K0 = ⌈β·2LMv⌉ | — | (간접) β로 결정 |
| Two-part UCI | — | 6.3.1.1.2 / 6.3.2.1.2 | 5.2.3 (general) | maxNumber CSI | reportConfigType |
| Priority omission | — | 6.3.2.1.2 | 5.2.3 (general) | — | — |

### 8.3 Configuration → Behavior 흐름 (구체 예시)

**예: gNB가 16-port Enhanced Type-II를 설정하려 할 때**

1. **38.306 확인**: UE가 `typeII-r16`을 지원하고 `paramCombination-r16 = 6` 가능한지 확인
2. **38.331 RRC 설정**:
   - `NZP-CSI-RS-ResourceSet` 내 16-port resource 설정
   - `CodebookConfig.type2-r16.typeII-r16` 으로 codebook 지정
   - `paramCombination-r16 = 6` (L=4, p_v=1/2, β=1/2) 설정
   - `numberOfPMI-SubbandsPerCQI-Subband-r16 = 1`
   - `typeII-RI-Restriction-r16` bitmap으로 rank 1~4 허용
3. **38.211 송신**: CSI-RS는 16 ports, fd-CDM2, density=1로 송신
4. **38.214 수식 적용**: UE가 W^(l) 계산, 비제로 계수 K0 = ⌈0.5 × 2×4 × Mv⌉ 산출
5. **38.212 인코딩**: Part 1에 RI/wideband CQI/non-zero coefficient 수, Part 2에 W₁/W_f/bitmap/계수 인코딩
6. **38.512-4 / 38.101-4 검증**: PMI follow throughput이 baseline 대비 요구 gain 충족 확인

### 8.4 핵심 정합성 포인트

- **paramCombination-r16의 8개 값**은 RRC(38.331) → Codebook(38.214) → UCI 길이(38.212) → Capability(38.306) 의 4개 spec에서 일관되게 참조되며, 한 곳이라도 mismatch 발생 시 entire CSI report 무효화
- **K0 (non-zero coefficient 수)**: 38.214에서 정의 → 38.212에서 Part 1 field 길이 결정 → Part 2 디코딩 길이 결정의 critical chain
- **Rank ≤ 4 제약**: 38.214에 정의 → 38.331 typeII-RI-Restriction이 4-bit bitmap인 이유 → 38.306 capability에서도 max 4 layer 신고

---

## 9. 결론 및 의의

Rel.16 Enhanced Type-II Codebook은 다음 세 축에서 NR MIMO를 진화시켰다:

1. **Frequency Domain Compression**: DFT-based FD basis 도입으로 PMI overhead 50%+ 절감
2. **Adaptive Resolution**: paramCombination 8가지 조합으로 link condition별 trade-off 선택 가능
3. **Two-Part UCI with Priority Omission**: limited UL resource 환경에서 graceful degradation 보장

이 codebook은 Rel.17의 추가 enhancement(eType-II for FDD reciprocity, port selection 확장)와 Rel.18의 추가 압축 기법(CJT 등)의 출발점이 되었다.

---

*문서 참조: TS 38.211 v16.x, TS 38.212 v16.x, TS 38.214 v16.x, TS 38.306 v16.x, TS 38.331 v16.x, TS 38.101-4 v16.x, RP-191085*
