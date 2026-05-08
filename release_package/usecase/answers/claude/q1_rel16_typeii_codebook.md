# Rel.16 Enhanced Type-II Codebook Standard Analysis Report

## Table of Contents
1. [Motivation (WID Perspective)](#1-motivation-wid-perspective)
2. [38.211 — CSI-RS Resource Configuration](#2-38211--csi-rs-resource-configuration)
3. [38.212 — UCI Field Definitions](#3-38212--uci-field-definitions)
4. [38.214 — Enhanced Type-II Codebook Definition](#4-38214--enhanced-type-ii-codebook-definition)
5. [38.306 — UE Capability](#5-38306--ue-capability)
6. [38.331 — RRC Parameters](#6-38331--rrc-parameters)
7. [38.512-4 — Performance Requirements](#7-38512-4--performance-requirements)
8. [Cross-Document Linkages](#8-cross-document-linkages)

---

## 1. Motivation (WID Perspective)

### 1.1 Limitations of the Rel.15 Type-II Codebook

The Type-II codebook introduced in Rel.15 was designed to provide a high-resolution PMI for MU-MIMO. However, it had the following clear limitations:

- **Excessive UCI overhead**: The Type-II PMI directly quantizes amplitude and phase coefficients per SD (Spatial Domain) basis for every subband, which can result in payloads ranging from hundreds to over 1000 bits in a rank-2, 32-port, 19-subband configuration.
- **UCI segmentation problems**: When the payload exceeds the capacity of PUCCH format 3/4, CSI parts are omitted or split into multi-part, degrading accuracy.
- **Inefficient MU-MIMO performance vs. overhead trade-off**: Real channels exhibit strong correlation in the frequency domain, so independent quantization per subband is redundant.

### 1.2 RP-182863 / RP-191085 (NR MIMO Enhancement WID)

The Rel.16 NR MIMO Enhancement WI (which began as RP-182863 and was revised to RP-191085) explicitly stated the following as the core objective:

> *"Specify enhancement on CSI reporting for MU-MIMO with focus on overhead reduction, including DFT-based compression in frequency domain."*

The core motivation can be summarized in two points:

1. **Frequency domain compression**: Instead of independent PMI per subband, report in compressed form using FD basis (DFT vectors).
2. **Overhead reduction**: Reduce PMI payload by 50% or more while maintaining the same or similar MU-MIMO performance.

### 1.3 Core Technical Concept

Enhanced Type-II preserves the SD basis selection structure of Rel.15 Type-II while adding **a 3-stage compression structure that newly introduces an FD basis**:

```
W = W₁ · W̃₂ · W_f^H
```

- **W₁**: SD basis selection (similar to Rel.15, choosing 2L beams)
- **W̃₂**: SD-FD coefficient matrix (compressed form of the linear combination coefficients)
- **W_f**: FD basis selection (choosing Mv DFT vectors)

An additional core technique introduced is **bitmap-based non-zero coefficient indication**. Out of the total 2L×Mv coefficients, only K0 = ⌈β·2LMv⌉ non-zero coefficients are reported.

---

## 2. 38.211 — CSI-RS Resource Configuration

### 2.1 NZP-CSI-RS Resource for Enhanced Type-II

The resource element mapping of NZP-CSI-RS, defined in 38.211 Clause 7.4.1.5, is identical to Rel.15, but Enhanced Type-II enforces the following configuration:

| Parameter | Value | Notes |
|---|---|---|
| Number of CSI-RS ports (P) | {4, 8, 12, 16, 24, 32} | Same set as Rel.15 Type-II |
| CDM type | `cdm8-FD2-TD4` or `fd-CDM2`, `cdm4-FD2-TD2` | Depends on the number of ports |
| Density (ρ) | 1 RE/RB/port | Fixed at 1 to support high-resolution PMI |
| Frequency domain location | k̄ | See TS 38.211 Table 7.4.1.5.3-1 |

### 2.2 CSI-RS Sequence Generation

The PN sequence is initialized as follows:

$$c_{\text{init}} = \left( 2^{10}(N_{\text{symb}}^{\text{slot}} \cdot n_{s,f}^\mu + l + 1)(2 n_{ID} + 1) + n_{ID} \right) \bmod 2^{31}$$

Here, `n_ID` is conveyed by the `scramblingID` of `NZP-CSI-RS-Resource`. Sequence generation does not change for Enhanced Type-II.

### 2.3 Key Constraints in Resource Mapping

Since the Enhanced Type-II codebook supports **rank ≤ 4 only** (as defined in 38.214), the combinations of CSI-RS ports and rank are limited. The CSI-RS must be configured as a single resource within an **NZP-CSI-RS-ResourceSet**; port aggregation is not allowed.

---

## 3. 38.212 — UCI Field Definitions

The UCI field structure of Enhanced Type-II is defined in 38.212 Clause 6.3.1.1.2 and 6.3.2.1.2.

### 3.1 Two-Part UCI Structure

Enhanced Type-II is reported with **two-part UCI in the same way as Type-II**:

#### CSI Part 1 (Fixed Length)
- RI (Rank Indicator): ⌈log₂(R_max)⌉ bits, R_max ∈ {1,2,3,4}
- Wideband CQI (4 bits)
- **Number of non-zero coefficients indication per layer**: ⌈log₂(K0+1)⌉ bits × R
  - This field is **the key element newly added compared with Rel.15**, and is used to determine the length of Part 2 from Part 1.

#### CSI Part 2 (Variable Length, Determined from Part 1)
- SD basis indication (W₁): ⌈log₂(C(N₁N₂, L))⌉ bits
- FD basis indication (W_f): per-layer indication (Mv DFT vector indices)
- Bitmap of non-zero coefficients: 2LMv bits per layer
- Strongest coefficient indicator (SCI): ⌈log₂(2L)⌉ bits per layer
- Amplitude(reference) + amplitude(differential) + phase: for each non-zero coefficient
- Subband CQI (per-CW): 2 bits per subband per CW

### 3.2 Priority-Based Omission Rule

When Part 2 exceeds the PUCCH/PUSCH capacity, **priority-based omission** is applied (38.212 Clause 6.3.2.1.2). The priority is computed as:

$$\text{Pri}(l, m) = 2 L \cdot R \cdot \pi(m) + R \cdot l + r$$

where:
- l: SD index, m: FD index, r: layer index
- π(m): a permutation function — reorders so that the 0-th FD index has the highest priority

Lower-priority groups are dropped first, ensuring "graceful degradation".

### 3.3 Bit Sequence Construction

UCI bit sequence generation, polar coding, and rate matching are the same as ordinary UCI (Clause 6.3.1, 6.3.2). However, Part 1 and Part 2 are encoded with separate polar codes.

---

## 4. 38.214 — Enhanced Type-II Codebook Definition

### 4.1 Codebook Identifiers

In 38.214 Clause 5.2.2.2.5, alongside the **Type II Port Selection Codebook**, a new codebook is defined in Clause 5.2.2.2.5. The following values are added to the RRC parameter `codebookType`:

- `typeII-r16` (Enhanced Type-II)
- `typeII-PortSelection-r16` (Enhanced Type-II Port Selection)

### 4.2 Precoder Equation Definition

The precoder for layer l is expressed as:

$$W^{(l)} = \frac{1}{\sqrt{N_1 N_2 \gamma^{(l)}}} \sum_{i=0}^{2L-1} \sum_{f=0}^{M_v - 1} v_{m_1^{(i)}, m_2^{(i)}} \cdot \tilde{w}_{i,f}^{(l)} \cdot y_f^{H}$$

- $v_{m_1, m_2}$: SD oversampled DFT vector (same as Rel.15 Type-II)
- $\tilde{w}_{i,f}^{(l)}$: SD-FD coefficient (compressed)
- $y_f$: FD DFT vector, length N₃ (number of precoding sub-bands × R)
- γ^(l): power normalization factor

### 4.3 Key Parameters: L, p_v, β

The following three parameters determine the trade-offs in the codebook configuration:

| Parameter | Meaning | Possible Values |
|---|---|---|
| L | Number of SD bases | {2, 4, 6} |
| p_v | FD basis ratio (varies by rank) | {1/4, 1/2} for rank 1-2; {1/4} for rank 3-4 |
| β | Non-zero coefficient ratio | {1/4, 1/2, 3/4} |

Eight `paramCombination-r16` values are defined as combinations of these three parameters (38.214 Table 5.2.2.2.5-1).

### 4.4 Determining Mv

The number of FD bases Mv is determined as follows:

$$M_v = \lceil p_v \cdot N_3 \rceil \quad \text{for rank 1, 2}$$
$$M_v = \lceil p_v \cdot N_3 / 2 \rceil \quad \text{for rank 3, 4}$$

N3 is determined as:
- If `subbandAmplitude=true`: N₃ = NSB × R (where R is the number of PRGs per PMI subband)
- Default: N₃ = NSB

### 4.5 Coefficient Quantization

Non-zero coefficients are quantized as:

$$\tilde{w}_{i,f}^{(l)} = p_{i,f}^{(l)} \cdot \phi_{i,f}^{(l)}$$

- **Reference amplitude**: 4 bits (per polarization)
- **Differential amplitude**: 3 bits (per non-zero coefficient)
- **Phase**: 16-PSK (4 bits) for high-amplitude, 8-PSK (3 bits) for low-amplitude

### 4.6 Strongest Coefficient Indicator (SCI)

The SD-FD index of the strongest coefficient of layer l is reported separately (⌈log₂(2L·Mv)⌉ or ⌈log₂(K0)⌉ bits), and that coefficient is normalized to amplitude=1, phase=0.

### 4.7 Port Selection Variant

`typeII-PortSelection-r16`, instead of selecting an SD basis, **selects L ports** in a beamformed CSI-RS environment. It is used when the operator transmits beamformed CSI-RS that has been pre-beamformed at the BS.

---

## 5. 38.306 — UE Capability

### 5.1 Relevant Capability Fields

The following capabilities are defined under 38.306 Clause 4.2.7.5 (CSI Reporting capability):

| Capability | Location | Meaning |
|---|---|---|
| `typeII-r16` | `csi-ReportFramework-r16` | Whether Enhanced Type-II is supported |
| `typeII-PortSelection-r16` | Same | Whether the Port selection variant is supported |
| `paramCombination-r16` | per-band | Supported (L, p_v, β) combinations |
| `maxNumberRxTxBeamSwitchDL` | per-band | Linkage with beam-switching capability |

### 5.2 Port Count and Layer Limits

- Maximum supported number of ports: declared by the UE among {4, 8, 12, 16, 24, 32}
- Max rank for Enhanced Type-II: **at most 4** (as restricted by the 38.214 definition)
- The `simultaneousCSI-ReportsPerCC-r16` field limits the number of CSI reports that can be processed simultaneously

### 5.3 Computational Complexity Aspects

CSI computation occupies the **CSI processing units (CPUs)** count defined in 38.214 Table 5.2.1.5-2. As with Rel.15 Type-II, Enhanced Type-II is treated as N_CPU = unlimited (∞), blocking all other CSI computations (i.e., only one can be processed at a time). This reflects the implementation burden.

### 5.4 Frequency Granularity

The PMI subband size R = 1 or R = 2 is indicated via `csi-ReportFrequencyGranularity-r16`. R = 2 provides finer frequency resolution.

---

## 6. 38.331 — RRC Parameters

### 6.1 Extension of the CodebookConfig IE

In 38.331, the `CodebookConfig` IE has been extended as follows:

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

### 6.2 TypeII-r16 IE Details

```asn1
TypeII-r16 ::= SEQUENCE {
    n1-n2-codebookSubsetRestriction-r16  CHOICE {
        two-one          BIT STRING (SIZE (16)),
        two-two          BIT STRING (SIZE (43)),
        ... (per (N1, N2) combination)
    },
    typeII-RI-Restriction-r16    BIT STRING (SIZE (4)),
    numberOfPMI-SubbandsPerCQI-Subband-r16  INTEGER (1..2)
}
```

#### Meaning of key sub-IEs:

- **`n1-n2-codebookSubsetRestriction-r16`**: SD beam restriction. For each (N1, N2) combination, restricts the subset of usable oversampled DFT vectors via a bitmap.
- **`typeII-RI-Restriction-r16`**: A 4-bit bitmap. Restricts the rank values 1–4 the UE can report.
- **`numberOfPMI-SubbandsPerCQI-Subband-r16`**: The R value. 1 or 2.

### 6.3 paramCombination-r16 Table

`paramCombination-r16` (1–8) selects the (L, p_v, β) combination (38.214 Table 5.2.2.2.5-1):

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

### 6.4 CSI-ReportConfig Coupling

```asn1
CSI-ReportConfig ::= SEQUENCE {
    ...,
    codebookConfig    CodebookConfig    OPTIONAL,
    reportFreqConfiguration    SEQUENCE {
        cqi-FormatIndicator    ENUMERATED { widebandCQI, subbandCQI },
        pmi-FormatIndicator    ENUMERATED { widebandPMI, subbandPMI },  -- must be subbandPMI
        csi-ReportingBand    CHOICE { ... }
    }
}
```

For Enhanced Type-II, **`pmi-FormatIndicator = subbandPMI` is mandatory**, and `reportQuantity = cri-RI-PMI-CQI` (or its equivalent) must be configured.

---

## 7. 38.512-4 — Performance Requirements

> Note: TS 38.512 is the RRM portion of NR conformance test. CSI-related demodulation requirements are mainly defined in **TS 38.101-4** (UE demodulation). Specific test cases for Enhanced Type-II are addressed around **TS 38.101-4 Clause 5.2A**. This report covers both the RRM aspects associated with the 38.512 series and the demod aspects in 38.101-4.

### 7.1 Test Case Structure

CSI feedback accuracy is evaluated via a **closed-loop throughput-based test**, not by directly comparing PMIs:

- Comparison of **PMI random vs PMI follow**
- Under the same SNR, the throughput with PMI follow must improve by a certain percentage or more compared with the random reference.

### 7.2 Main Test Conditions (TS 38.101-4 basis)

| Parameter | Typical Value |
|---|---|
| Channel model | TDLA, TDLB, CDL-A, CDL-C |
| Number of CSI-RS ports | 16, 32 |
| Codebook | typeII-r16, paramCombination ∈ {6, 7} |
| MCS | Fixed (e.g., MCS index 13) |
| Transmission scheme | Closed-loop with PMI follow |
| Reference performance | Random PMI baseline |

### 7.3 Performance Metrics

Representative metrics:
- **Throughput gain**: When using Enhanced Type-II PMI, throughput must improve **by 30% or more** compared with random PMI (typical CDL channel)
- **MU-MIMO scenario**: In a 2-UE MU-MIMO setup, the sum throughput must exceed SU-MIMO + Type-I by a certain ratio

### 7.4 RRM Side (38.133)

RRM requirements concerning CSI reporting periodicity and latency are defined in 38.133 Clause 9.5:

- **CSI reporting delay**: From an aperiodic CSI trigger to the report, within Z₁/Z₁' symbols
- Enhanced Type-II may apply latency class 2 (relaxed timeline)
- The Z₁ value depends on the BWP's SCS and X (CSI processing capability)

---

## 8. Cross-Document Linkages

### 8.1 Cross-Reference from a Data-Flow Perspective

```
                    [WID: RP-191085]
                          │
                          ▼
                     Design decisions
        ┌─────────────┬──┴──┬──────────────┐
        ▼             ▼     ▼              ▼
   [38.211]      [38.214]   [38.331]    [38.306]
   CSI-RS Tx    Codebook    RRC config   Capability
   (P, CDM)     equation(W) (paramComb)  (support)
        │             │     │              │
        └──────┬──────┘     │              │
               ▼            │              │
         UE: PMI calc ◄─────┘              │
               │                            │
               ▼                            │
          [38.212]                          │
        UCI encoding                        │
        (Part1/Part2)                       │
               │                            │
               ▼                            │
         BS: decoding                       │
               │                            │
               ▼                            │
       [38.101-4 / 38.512-4]                │
       Performance verify ◄──────────────────┘
```

### 8.2 Key Cross-Reference Matrix

| Concept | 38.211 | 38.212 | 38.214 | 38.306 | 38.331 |
|---|---|---|---|---|---|
| CSI-RS resource | 7.4.1.5 (RE mapping) | — | 5.2.2 (selection rule) | 4.2.7.5 | NZP-CSI-RS-Resource |
| Codebook definition | — | 6.3.1.1.2 (UCI structure) | 5.2.2.2.5 (W equation) | typeII-r16 capability | CodebookConfig.type2-r16 |
| paramCombination | — | UCI length input | Table 5.2.2.2.5-1 | Reports supported combos | paramCombination-r16 |
| Non-zero coeff | — | bitmap field | K0 = ⌈β·2LMv⌉ | — | (indirect) determined by β |
| Two-part UCI | — | 6.3.1.1.2 / 6.3.2.1.2 | 5.2.3 (general) | maxNumber CSI | reportConfigType |
| Priority omission | — | 6.3.2.1.2 | 5.2.3 (general) | — | — |

### 8.3 Configuration → Behavior Flow (Concrete Example)

**Example: gNB tries to configure 16-port Enhanced Type-II**

1. **Check 38.306**: Verify that the UE supports `typeII-r16` and that `paramCombination-r16 = 6` is possible
2. **38.331 RRC configuration**:
   - Configure a 16-port resource within `NZP-CSI-RS-ResourceSet`
   - Specify the codebook via `CodebookConfig.type2-r16.typeII-r16`
   - Configure `paramCombination-r16 = 6` (L=4, p_v=1/2, β=1/2)
   - `numberOfPMI-SubbandsPerCQI-Subband-r16 = 1`
   - Allow ranks 1–4 via the `typeII-RI-Restriction-r16` bitmap
3. **38.211 transmission**: Transmit CSI-RS with 16 ports, fd-CDM2, density=1
4. **Apply 38.214 equations**: UE computes W^(l) and derives the non-zero coefficient count K0 = ⌈0.5 × 2×4 × Mv⌉
5. **38.212 encoding**: Encode RI/wideband CQI/non-zero coefficient count in Part 1, and W₁/W_f/bitmap/coefficients in Part 2
6. **38.512-4 / 38.101-4 verification**: Confirm that the PMI follow throughput meets the required gain over the baseline

### 8.4 Key Consistency Points

- The **8 values of paramCombination-r16** are referenced consistently across the four specs RRC(38.331) → Codebook(38.214) → UCI length(38.212) → Capability(38.306); a mismatch in any one invalidates the entire CSI report.
- **K0 (number of non-zero coefficients)**: defined in 38.214 → determines the Part 1 field length in 38.212 → critical chain that determines the Part 2 decoding length
- **Rank ≤ 4 constraint**: defined in 38.214 → reason why typeII-RI-Restriction in 38.331 is a 4-bit bitmap → maximum of 4 layers also reported in 38.306 capability

---

## 9. Conclusion and Significance

The Rel.16 Enhanced Type-II Codebook advances NR MIMO along three axes:

1. **Frequency Domain Compression**: Introduces a DFT-based FD basis to reduce PMI overhead by 50% or more
2. **Adaptive Resolution**: Eight paramCombination choices allow trade-off selection per link condition
3. **Two-Part UCI with Priority Omission**: Guarantees graceful degradation under limited UL resources

This codebook became the starting point for Rel.17 additional enhancements (eType-II for FDD reciprocity, port selection extensions) and for Rel.18 additional compression techniques (CJT, etc.).

---

*Document references: TS 38.211 v16.x, TS 38.212 v16.x, TS 38.214 v16.x, TS 38.306 v16.x, TS 38.331 v16.x, TS 38.101-4 v16.x, RP-191085*
