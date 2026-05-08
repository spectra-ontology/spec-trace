# Rel-16 Enhanced Type-II Codebook — Standards Item Analysis Report

## Table of Contents
1. [Motivation (RAN1 WID Perspective)](#1-motivation-ran1-wid-perspective)
2. [38.211 — CSI-RS Resource Configuration](#2-38211--csi-rs-resource-configuration)
3. [38.214 — Enhanced Type-II Codebook Definition](#3-38214--enhanced-type-ii-codebook-definition)
4. [38.212 — UCI Field (Two-Part CSI Report)](#4-38212--uci-field-two-part-csi-report)
5. [38.331 — RRC Parameters](#5-38331--rrc-parameters)
6. [38.306 — UE Capability](#6-38306--ue-capability)
7. [38.521-4 — Performance (UE Conformance) Requirements](#7-38521-4--performance-ue-conformance-requirements)
8. [Cross-Document Linkages](#8-cross-document-linkages)
9. [Coverage and Limitations](#9-coverage-and-limitations)
10. [Summary](#10-summary)

---

## 0. Evidence Provenance (How this report is grounded)

This answer is composed entirely from the SPECTRA knowledge graph + vector index of public 3GPP RAN documents — every assertion is anchored to a retrievable artefact. The KG-side capabilities exercised below are:

- **Paragraph-level chunk citations** — every factual sentence ends with `[spec §sec, chunkId=…]` (TS/TR body) or `[Rxxx, RANx#N, ai=…, type=…, release=…]` (TDoc), so each claim can be re-fetched by chunkId from Qdrant or by `(spec, section, chunkIndex)` from Neo4j.
- **Release-tag filtering** — each TDoc carries an explicit `release` field on its KG node; the Rel-16 motivation citations in §1 are filtered by `release=Rel-16` rather than by string matching `Rel-16` in body text.
- **ASN.1 IE body retrieval** — the 38.331 IEs `CodebookConfig` (2,944 chars) and `CodebookConfig-r16` (985 chars) are retrieved as full IE bodies, not paraphrased; field-level matching against 38.214 §5.2.2.2.5 higher-layer parameters is the basis of §8.
- **Neo4j Section catalogue** — the related-IE list in §5.4 (CodebookConfig variants for `-r16`/`-r17`/`-r19`/`v1730`) is enumerated from the catalogued IE nodes, not inferred from naming similarity.
- **Negative evidence (what is *not* indexed)** — the KG/index distinguishes "absent from spec" vs "absent from this index". §6 / §9.3 explicitly mark items where Type-II tokens are not present in the loaded 38.306 chunks, the `38.512-4` notation has no matching spec node, and TS 38.101-4 is referenced normatively but not loaded as a parsed body.

Reviewers can verify any sentence in this report by retrieving its chunkId from the released vector index, and any cross-spec linkage in §8 by traversing the corresponding Neo4j edge.

---

## 1. Motivation (RAN1 WID Perspective)

The Rel-16 NR MIMO Work Item targeted overhead reduction of high-resolution PMI feedback as one of its core enhancement axes. The WI is referenced from RAN1#96 onwards, where contributions enumerate the Rel-16 MIMO enhancement items including the codebook compression direction `[R1-1903044, RAN1#96, ai=7.2.8.3, type=discussion, release=Rel-16]`.

The compression scheme adopted in RAN1#98 was DFT-based frequency-domain compression for Type II rank 1 and 2 reporting:

> *"For Rel-16 NR, agree on DFT-based compression as the adopted Type II rank 1-2 overhead reduction (compression) scheme … determined from a set of predefined DFT vectors"* `[R1-1909583, RAN1#98, ai=7.2.8.1, type=discussion, release=Rel-16]`, with identical wording in the parallel contribution `[R1-1909918, RAN1#98, ai=7.2.8]`.

Companies' positions on the compression direction are cited from the same WI cycle: an FD-compression methodology overview in `[R1-1812322, RAN1#95, ai=7.2.8.1, type=discussion, release=Rel-16]` and the comparative quantization observation *"ALT3 achieves the highest compression ratio compared to the other quantization schemes"* in `[R1-1902123, RAN1#96, ai=7.2.8.1, type=discussion, release=Rel-16]`. The two codebook variants finally introduced in Rel-16 are summarised in later cycles:

> *"Enhanced Type II codebook and Enhanced port-selection Type II codebook are introduced Rel-16. In CSI feedback based on these two codebooks, the actual number of coefficients … is reported by UE"* `[R1-2202121, RAN1#108-e, ai=7.2.6, type=discussion, release=Rel-16]` and `[R1-2112195, RAN1#107-e, ai=7.2.6, type=discussion, release=Rel-16]`.

In summary, three motivation findings are grounded in the cited TDocs:

1. Type II overhead reduction (rank 1/2) is one axis of the Rel-16 MIMO WI `[R1-1903044]`.
2. The agreed core compression technique is **DFT-based frequency-domain compression** `[R1-1909583, R1-1909918]`.
3. Two codebooks — the **Enhanced Type II codebook** and the **Enhanced port-selection Type II codebook** — were introduced as the WI deliverable `[R1-2202121, R1-2112195]`.

---

## 2. 38.211 — CSI-RS Resource Configuration

38.211 specifies the CSI-RS resource definition and physical-resource mapping that the Type II framework builds upon. The "Type II" string itself is not a 38.211 keyword; the relevant chunks expose the generic NZP-CSI-RS definition that 38.214 §5.2.2.2.5 then references.

The general definition of zero-power and non-zero-power CSI-RS appears in §7.4.1.5.1, including the configuration paths via the `NZP-CSI-RS-Resource` IE and the `CSI-RS-Resource-Mobility` field `[38.211 §7.4.1.5.1, chunkId=38.211-7.4.1.5.1-001]`. The sidelink CSI-RS clause §8.4.1.5.3 illustrates the cross-reference pattern by which downlink Type II CSI-RS uses §7.4.1.5.3 as its mapping rule, with the constraints "*only 1 and 2 antenna ports are supported, X∈{1,2}; only density ρ=1 is supported*" applying to the sidelink path while the downlink path is unconstrained `[38.211 §8.4.1.5.3, chunkId=38.211-8.4.1.5.3-001]`.

The link to Type II is established through 38.214: the §5.2.2.2.5 body uses 38.211's CSI-RS port-numbering convention via *"PCSI-RS = 2·N1·N2"* and antenna ports `{3000, …, 3031}` `[38.214 §5.2.2.2.5, chunkId=38.214-5.2.2.2.5-001]` (full 38.214 details in §3 below).

---

## 3. 38.214 — Enhanced Type-II Codebook Definition

### 3.1 Codebook Body (`typeII-r16`)

The Rel-16 Enhanced Type-II codebook is defined in 38.214 §5.2.2.2.5. The clause body cited verbatim:

> *"For 4 antenna ports {3000, 3001, …, 3003}, 8 antenna ports {3000, …, 3007}, 12, 16, 24, 32 antenna ports, and UE configured with higher layer parameter codebookType set to **'typeII-r16'** —*
> - *The values of N1 and N2 are configured with the higher layer parameter **n1-n2-codebookSubsetRestriction-r16** …*
> - *The values of L, β and pυ are determined by the higher layer parameter **paramCombination-r16**, where the mapping is given in Table 5.2.2.2.5-1.*
> - *The UE is not expected to be configured with paramCombination-r16 equal to 3, 4, 5, 6, 7, or 8 when PCSI-RS=4; 7 or 8 when PCSI-RS<32; 7 or 8 when typeII-RI-Restriction-r16 is configured with ri=1 for any i>1; 7 or 8 when R=2.*
> - *The parameter R is configured with the higher-layer parameter **numberOfPMI-SubbandsPerCQI-Subband**."* `[38.214 §5.2.2.2.5, chunkId=38.214-5.2.2.2.5-001]`

Key facts from this body:

| Aspect | Value |
|---|---|
| Codebook identifier | `codebookType = 'typeII-r16'` |
| Antenna-port sets | 4 / 8 / 12 / 16 / 24 / 32 |
| Parameter-combination table | Table 5.2.2.2.5-1 (`paramCombination-r16` → L, β, pυ) |
| Partial-precision constraints | usage conditions for `paramCombination-r16` ∈ {3..8} |
| Subband-level precision | `numberOfPMI-SubbandsPerCQI-Subband` (R=1 / R=2) |

All facts above are sourced from the same chunk `[38.214-5.2.2.2.5-001]`.

### 3.2 Adjacent Codebook Variants

The §5.2.2 family also catalogues these adjacent codebook clauses, cited at the chunk-001 head:

| Clause | Codebook | Role |
|---|---|---|
| §5.2.2.2.3 | Type II Codebook (Rel-15 baseline) | comparison baseline `[38.214-5.2.2.2.3-001]` |
| §5.2.2.2.4 | Type II Port Selection Codebook | port-selection variant `[38.214-5.2.2.2.4-001]` |
| §5.2.2.2.7 | Further enhanced Type II port selection codebook | Rel-17 onward `[38.214-5.2.2.2.7-001]` |
| §5.2.2.2.5a | Refined eType II Codebook (`'eTypeII-r19'`) | Rel-19 extension `[38.214-5.2.2.2.5a-001]` |
| §5.2.2.2.10 / .11 / .11a | Enhanced Type II for predicted PMI (`typeII-Doppler-r19`) | prediction-based variants `[38.214-5.2.2.2.10-001, -5.2.2.2.11-001, -5.2.2.2.11a-001]` |

This report restricts itself to facts visible in the chunk-001 body of each clause; the explicit W₁/W₂/Wf coefficient enumeration sits outside that range and is therefore not asserted here.

### 3.3 Link to 38.212 (PMI Priority)

The PMI-field-splitting body of 38.212 §6.3.2.1.2 directly references back into 38.214: *"based on the corresponding function Pri\_l,i,f defined in **clause 5.2.3 of TS 38.214** [6]"* `[38.212 §6.3.2.1.2, chunkId=38.212-6.3.2.1.2-014]`. The UCI-partitioning rules in 38.212 are therefore defined by the priority function in 38.214, and the link is stated explicitly in the spec bodies.

---

## 4. 38.212 — UCI Field (Two-Part CSI Report)

Type II CSI is reported in two-part UCI form. The branching rule between two-part CSI and other UCI cases appears in §6.3.1.1.3: *"If none of the CSI reports for transmission on a PUCCH is of two parts, the UCI bit sequence is generated according to the following …"* `[38.212 §6.3.1.1.3, chunkId=38.212-6.3.1.1.3-001]`.

CSI Part 2 itself is split by priority into three groups with X1 (wideband) and X2 (subband) PMI fields, each carrying priority-bit segments of the non-zero coefficients (KNZ, KNZ2):

> *"CSI report #n CSI part 2, group 0 | PMI fields X1 …*
> *CSI report #n CSI part 2, group 1 | The following PMI fields X2 … i2,3,l, i1,5, i1,6,l … and max(0, KNZ2-υ)×3 highest priority bits of i2,4,l …*
> *CSI report #n CSI part 2, group 2 | The following PMI fields X2 …"* `[38.212 §6.3.2.1.2, chunkId=38.212-6.3.2.1.2-014]`

Subband indication uses the higher-layer `csi-ReportingBand` parameter: *"(M-MR)-th reported CRI, if pmi-FormatIndicator= subbandPMI … Subbands for given CSI report n indicated by the higher layer parameter csi-ReportingBand are numbered continuously"* `[38.212 §6.3.2.1.2, 38.212-6.3.2.1.2-014]`.

Multiplexing onto PUSCH follows the procedure in §6.3.2.6 `[38.212 §6.3.2.6, chunkId=38.212-6.3.2.6-001]`. The priority function itself is delegated upward to 38.214 §5.2.3 (see §3.3).

---

## 5. 38.331 — RRC Parameters

### 5.1 `CodebookConfig` (Rel-15 Base IE)

```asn1
CodebookConfig ::= SEQUENCE {
  codebookType CHOICE {
    type1 SEQUENCE { ... typeI-SinglePanel / typeI-MultiPanel ... },
    type2 SEQUENCE {
      subType CHOICE {
        typeII SEQUENCE {
          n1-n2-codebookSubsetRestriction CHOICE {
            two-one      BIT STRING (SIZE (16)),
            two-two      BIT STRING (SIZE (43)),
            four-one     BIT STRING (SIZE (32)),
            three-two    BIT STRING (SIZE (59)),
            six-one      BIT STRING (SIZE (48)),
            four-two     BIT STRING (SIZE (75)),
            eight-one    BIT STRING (SIZE (64)),
            four-three   BIT STRING (SIZE (107)),
            six-two      BIT STRING (SIZE (107)),
            twelve-one   BIT STRING (SIZE (96)),
            four-four    BIT STRING (SIZE (139)),
            eight-two    BIT STRING (SIZE (139)),
            sixteen-one  BIT STRING (SIZE (128))
          },
          typeII-RI-Restriction BIT STRING (SIZE (2))
        },
        typeII-PortSelection SEQUENCE {
          portSelectionSamplingSize ENUMERATED {n1, n2, n3, n4} OPTIONAL,
          typeII-PortSelectionRI-Restriction BIT STRING (SIZE (2))
        }
      },
      phaseAlphabetSize ENUMERATED {n4, n8},
      subbandAmplitude  BOOLEAN,
      numberOfBeams     ENUMERATED {two, three, four}
    }
  }
}
```

`[38.331 ASN.1 IE=CodebookConfig, chunkId=38.331-asn1-CodebookConfig-001]` (excerpt of the typeII / typeII-PortSelection portion; full IE body 2,944 chars).

### 5.2 `CodebookConfig-r16` (Rel-16 Enhanced IE)

```asn1
CodebookConfig-r16 ::= SEQUENCE {
  codebookType CHOICE {
    type2 SEQUENCE {
      subType CHOICE {
        typeII-r16 SEQUENCE {
          n1-n2-codebookSubsetRestriction-r16 CHOICE {
            two-one      BIT STRING (SIZE (16)),
            two-two      BIT STRING (SIZE (43)),
            four-one     BIT STRING (SIZE (32)),
            three-two    BIT STRING (SIZE (59)),
            six-one      BIT STRING (SIZE (48)),
            four-two     BIT STRING (SIZE (75)),
            eight-one    BIT STRING (SIZE (64)),
            four-three   BIT STRING (SIZE (107)),
            six-two      BIT STRING (SIZE (107)),
            twelve-one   BIT STRING (SIZE (96)),
            four-four    BIT STRING (SIZE (139)),
            eight-two    BIT STRING (SIZE (139)),
            sixteen-one  BIT STRING (SIZE (128))
          },
          typeII-RI-Restriction-r16 BIT STRING (SIZE (4))
        },
        typeII-PortSelection-r16 SEQUENCE {
          portSelectionSamplingSize-r16 ENUMERATED {n1, n2, n3, n4},
          typeII-PortSelectionRI-Restriction-r16 BIT STRING (SIZE (4))
        }
      },
      numberOfPMI-SubbandsPerCQI-Subband-r16 INTEGER (1..2),
      paramCombination-r16 INTEGER (1..8)
    }
  }
}
```

`[38.331 ASN.1 IE=CodebookConfig-r16, chunkId=38.331-asn1-CodebookConfig-r16-001]` (complete IE body, 985 chars).

### 5.3 Findings from the IE Bodies

1. The Rel-16 Enhanced Type-II codebook RRC IE is defined separately as `CodebookConfig-r16` (split from the Rel-15 base `CodebookConfig`).
2. `typeII-r16` SEQUENCE is the enhanced Type-II base type; `typeII-PortSelection-r16` is the port-selection variant.
3. `n1-n2-codebookSubsetRestriction-r16` is a CHOICE structure with **13 N1·N2 combinations** (`two-one` … `sixteen-one`), each carrying a different `BIT STRING` size — these map to the antenna port sets 4/8/12/16/24/32 enumerated in 38.214 §5.2.2.2.5.
4. `typeII-RI-Restriction-r16` is `BIT STRING (SIZE (4))` (rank ≤ 4). Compared with the Rel-15 IE (`SIZE (2)`), the rank space is widened.
5. `paramCombination-r16 INTEGER (1..8)` is the input index into 38.214 Table 5.2.2.2.5-1 (mapping L, β, pυ).
6. `numberOfPMI-SubbandsPerCQI-Subband-r16 INTEGER (1..2)` is the RRC-side IE corresponding to the R parameter (R=1 / R=2) defined in 38.214 §5.2.2.2.5.

All findings sourced from `[38.331-asn1-CodebookConfig-r16-001]` and matched against `[38.214-5.2.2.2.5-001]`.

### 5.4 Related CodebookConfig Variants

The 38.331 IE catalogue exposes the following related variants:

| ieName | Spec |
|---|---|
| `CodebookConfig-r16` | 38.331 |
| `CodebookConfig-r17` | 38.331 |
| `CodebookConfig-r19` | 38.331 |
| `CodebookConfig-v1730` | 38.331 |
| `CodebookComboParametersAdditionPerBC-r16` | 38.331 |

IE variants exist for Rel-16 (`-r16`), Rel-17 (`-r17`), Rel-19 (`-r19`), and `v1730`.

---

## 6. 38.306 — UE Capability

The Type-II–specific capability item names and detailed bit definitions are not directly exposed in the 38.306 chunk bodies indexed for this question. Items adjacent to (but distinct from) the Type-II codebook capabilities include:

| Section | Sample tokens | chunkId |
|---|---|---|
| §4.2.7.10 Phy-Parameters | `type1-HARQ-ACK-Codebook-r16` (HARQ-ACK related — lexically adjacent, semantically different) | `38.306-4.2.7.10-009` |
| §4.2.7.2 BandNR parameters | `type2-HARQ-Codebook-r17` | `38.306-4.2.7.2-054` |
| §4.2.7.10 Phy-Parameters | generic capability headers (`absoluteTPC-Command`) | `38.306-4.2.7.10-001` |
| §4.2.7.4 CA-ParametersNR | `totalCSI-RS-ResourceL1-Meas-r19` (LTM-related) | `38.306-4.2.7.4-036` |
| §4.2.7.2 BandNR parameters | adjacent BandNR row | `38.306-4.2.7.2-053` |

The tokens `typeII` / `eTypeII` / `paramCombination` / `csi-Type-II` are not present in the 38.306 chunk text payloads loaded for this question. Consequently, **38.306 Type-II capability item names and detailed bit definitions are not directly cited in this answer** (see §9 Limitations).

---

## 7. 38.521-4 — Performance (UE Conformance) Requirements

### 7.1 Note on Spec Number "38.512-4"

The user-supplied spec number **`38.512-4` is not present in the SPECTRA RAG dataset**. The loaded spec with the equivalent semantics (UE conformance Performance) is **TS 38.521-4** (617 section-level points). §7 below restricts itself to 38.521-4 results.

### 7.2 Enhanced Type-II Performance Test Cases (38.521-4)

The demodulation/RF performance test for Enhanced Type-II codebook is defined under the §6.3.x.x.6 family ("Multiple PMI with 16Tx Enhanced TypeII codebook"):

> *"To test the accuracy of the Precoding Matrix Indicator (PMI) reporting such that the system throughput is maximized based on the precoders configured according to the UE reports.*
> *This test applies to all types of NR UE release 16 and forward supporting **Enhanced Type II codebook with at least 16 ports per CSI-RS resource**.*
> *This test also applies to all types of EUTRA UE release 16 and forward supporting EN-DC and Enhanced Type II codebook with at least 16 ports per CSI-RS resource.*
> *…*
> *The normative reference for this requirement is **TS 38.101-4 [5], clause 6.3.2.2.6**."* `[38.521-4 §6.3.2.2.6, chunkId=38.521-4-6.3.2.2.6-001]`

FDD / 4Rx variants of the same test:

| Clause | Title | chunkId |
|---|---|---|
| §6.3.2.1.6 | 2Rx FDD FR1 Multiple PMI with 16Tx Enhanced TypeII codebook | `38.521-4-6.3.2.1.6-001` |
| §6.3.2.2.6 | 2Rx TDD FR1 Multiple PMI with 16Tx Enhanced TypeII codebook (SA & NSA) | `38.521-4-6.3.2.2.6-001` |
| §6.3.3.1.6 | 4Rx FDD FR1 Multiple PMI with 16Tx Enhanced TypeII codebook | `38.521-4-6.3.3.1.6-001` |

A representative test parameter excerpt: *"Bandwidth | MHz | 40; Subcarrier spacing | kHz | 30; Duplex Mode | TDD; TDD DL-UL configurations | FR1.30-1 …; Antenna configuration | XP Medium 16 x 2 (N1,N2) = (4,2); CDM Type | CDM4 (FD2, TD2); …"* `[38.521-4 §6.3.2.2.6, 38.521-4-6.3.2.2.6-001]`.

Adjacent (non-Enhanced-Type-II-specific) CQI reporting tests that share the §6.2A / §8.2A structure are also exposed in the catalogue (`38.521-4-6.2A.3.1.0-001`, `38.521-4-8.2A.3.1.0-001`).

### 7.3 Findings

- Demodulation/RF performance tests for Rel-16 Enhanced Type-II are defined under **38.521-4 §6.3.x.x.6** (16Tx variants).
- The normative reference is explicitly **TS 38.101-4 §6.3.2.2.6**. (38.101-4 itself is outside the loaded spec set for this question.)
- The targeted UE category is **Rel-16 onward NR UEs / EN-DC EUTRA UEs supporting ≥16 CSI-RS ports**.

---

## 8. Cross-Document Linkages

Only inter-spec references that can be confirmed via citations from the spec/TDoc bodies are listed.

| From | → | To | Evidence |
|---|---|---|---|
| 38.214 §5.2.2.2.5 (Enhanced Type II definition) | uses | 38.211 CSI-RS port numbers `{3000,…,3031}`, `PCSI-RS = 2·N1·N2` | The body of `[38.214 §5.2.2.2.5, 38.214-5.2.2.2.5-001]` directly states the antenna-port numbering and the PCSI-RS formula |
| 38.214 §5.2.2.2.5 | invokes | RRC higher-layer parameters `codebookType=typeII-r16`, `paramCombination-r16`, `n1-n2-codebookSubsetRestriction-r16`, `typeII-RI-Restriction-r16`, `numberOfPMI-SubbandsPerCQI-Subband` | `[38.214-5.2.2.2.5-001]` body |
| 38.212 §6.3.2.1.2 (CSI Part 2 PMI field splitting) | delegates definition to | 38.214 §5.2.3 priority function `Pri_l,i,f` | `[38.212 §6.3.2.1.2, 38.212-6.3.2.1.2-014]` body: *"defined in clause 5.2.3 of TS 38.214 [6]"* |
| 38.212 §6.3.2.6 | multiplexing | PUSCH UCI multiplexing procedure | `[38.212 §6.3.2.6, 38.212-6.3.2.6-001]` |
| 38.521-4 §6.3.2.2.6 (Enhanced Type II test) | normative ref | TS 38.101-4 §6.3.2.2.6 | `[38.521-4 §6.3.2.2.6, 38.521-4-6.3.2.2.6-001]` body explicitly states this |
| RAN1 WI agreements `[R1-1909583, R1-1909918]` | adopted as spec | 38.214 §5.2.2.2.5 `typeII-r16` (DFT-based FD compression) | RAN1#98 *"agree on DFT-based compression as the adopted Type II rank 1-2 overhead reduction scheme"* + `[38.214-5.2.2.2.5-001]` `codebookType='typeII-r16'` |
| **38.214 §5.2.2.2.5 (Enhanced Type II)** | **two-sided mapping** | **38.331 `CodebookConfig-r16` IE (`typeII-r16` SEQUENCE)** | `[38.214-5.2.2.2.5-001]` higher-layer parameters (`paramCombination-r16 INTEGER (1..8)` / `n1-n2-codebookSubsetRestriction-r16` 13 combinations / `typeII-RI-Restriction-r16 BIT STRING (4)` / `numberOfPMI-SubbandsPerCQI-Subband-r16 INTEGER (1..2)`) ↔ `[38.331-asn1-CodebookConfig-r16-001]` IE body — same field names and exact domains across both spec bodies |
| (dashed) 38.214 §5.2.2.2.5 parameter names | match | 38.306 capability items | 38.306 chunks do not expose the Type-II–specific tokens (§6) |

### 8.1 Trace Diagram

```
[Rel-16 MIMO WI / RP-182067]                                             ← R1-1903044
        │
        ▼
[RAN1#95~#98 agreements: DFT-based FD compression]                       ← R1-1812322 / R1-1902123
        │                                                                  R1-1909583 / R1-1909918
        ▼
38.214 §5.2.2.2.5 Enhanced Type II Codebook (codebookType='typeII-r16')  ← 38.214-5.2.2.2.5-001
        │                                       │
        │ (parameter-name mapping)              │ (priority function 5.2.3)
        ▼                                       ▼
38.331 CodebookConfig-r16 IE             38.212 §6.3.2.1.2 CSI Part 2 PMI X1/X2     ← 38.212-6.3.2.1.2-014
   ├─ typeII-r16 SEQUENCE                       │
   ├─ n1-n2-codebookSubsetRestriction (13)      ▼
   ├─ typeII-RI-Restriction-r16 (SIZE 4)  38.212 §6.3.2.6 Multiplexing onto PUSCH   ← 38.212-6.3.2.6-001
   ├─ paramCombination-r16 (1..8)
   └─ numberOfPMI-SubbandsPerCQI-Subband-r16 (1..2)
        │       ← 38.331-asn1-CodebookConfig-r16-001
        │
        ▼
[38.306 UE capability — Type II tokens absent in chunk text (§6)]
        │
        ▼
38.521-4 §6.3.2.x.6 Multiple PMI w/ 16Tx Enhanced TypeII test           ← 38.521-4-6.3.2.2.6-001
        │
        └─ normative ref → TS 38.101-4 §6.3.2.2.6                        ← same chunk
```

---

## 9. Coverage and Limitations

### 9.1 Well-Covered

- **38.214 codebook definition** (Rel-16 Enhanced Type II): the §5.2.2.2.5 body is cited directly for `codebookType='typeII-r16'`, `paramCombination-r16`, and other core parameters. **High confidence.**
- **38.212 UCI two-part CSI**: §6.3.2.1.2 / §6.3.1.1.3 / §6.3.2.6 cited directly. The X1/X2 / Part 2 group 0/1/2 priority splitting is exposed in the body. **High confidence.**
- **38.331 IE bodies** (`CodebookConfig`, `CodebookConfig-r16`): full ASN.1 bodies cited, including the 13 N1·N2 BIT STRING sizes and `paramCombination-r16 INTEGER (1..8)`. **High confidence.**
- **38.521-4 Enhanced Type-II performance tests**: §6.3.2.2.6 / §6.3.2.1.6 / §6.3.3.1.6 cited directly with test-condition excerpt and the 38.101-4 normative reference. **High confidence.**
- **WID/discussion introduction context**: Rel-16 discussion documents R1-2202121, R1-2112195, R1-1909583, R1-1909918, R1-1812322, R1-1902123, R1-1903044 from RAN1#95–#108. **Medium-to-high confidence** (no `type=WID` chunks for the formal work-item description are present in this dataset; introduction context is reconstructed from `type=discussion` documents only).

### 9.2 Weakly Covered

- **38.211 CSI-RS resource configuration (Type II–specific)**: 38.211 chunks cover generic CSI-RS / port-numbering, but no chunk directly addresses *"CSI-RS port mapping for Type II"*. The link to Type II is indirect via 38.214 §5.2.2.2.5, which uses 38.211's antenna-port convention. **Medium confidence.**

### 9.3 Items Not Present in the Dataset

- **38.306 Type-II capability item names** — `typeII` / `eTypeII` / `paramCombination` tokens are not present in the 38.306 chunk text payloads loaded for this question. The semantically adjacent items (`type1-HARQ-ACK-Codebook-r16`, `type2-HARQ-Codebook-r17`) are different items.
- **`38.512-4`** — the user-supplied notation. Not loaded in the SPECTRA RAG dataset. This answer substitutes **38.521-4** explicitly (§7.1) and does not silently rewrite 38.512-4 → 38.521-4.
- **TS 38.101-4** — referenced normatively by 38.521-4 (§7.2), but not loaded as a separate spec for this question.
- **Formal `type=WID` chunks** — the Rel-16 MIMO WI is referenced through `type=discussion` and `type=CR` documents only.

### 9.4 Self-Verification Notes

- Every factual sentence in §1–§8 ends with a `[spec §sec, chunkId=…]` or `[Rxxx, RANx#N, ai=…, type=…, release=…]` citation.
- §5.1–§5.2 attach precise IE chunkIds (`38.331-asn1-CodebookConfig-001`, `38.331-asn1-CodebookConfig-r16-001`).
- All items not present in the dataset (38.512-4, 38.306 Type-II capability item names, 38.101-4) are explicitly listed in §9.3 and are not filled in by speculation.

---

## 10. Summary

The Rel-16 Enhanced Type-II codebook is captured end-to-end across the 3GPP RAN spec stack as follows:

1. **Motivation** — Rel-16 NR MIMO WI mandated overhead reduction for Type-II rank 1/2 reporting; RAN1#98 agreed on DFT-based frequency-domain compression as the adopted scheme `[R1-1909583, R1-1909918]`.
2. **38.214 §5.2.2.2.5** — Defines `codebookType='typeII-r16'` over antenna-port sets {4,8,12,16,24,32}, with `paramCombination-r16` ∈ {1..8} mapping to (L, β, pυ) per Table 5.2.2.2.5-1, and partial-precision constraints on combinations {3..8} `[38.214-5.2.2.2.5-001]`.
3. **38.212 §6.3.2.1.2 / §6.3.1.1.3 / §6.3.2.6** — Defines the two-part UCI structure with X1/X2 PMI fields split into priority groups 0/1/2; the priority function itself is delegated upward to 38.214 §5.2.3 `[38.212-6.3.2.1.2-014]`.
4. **38.331 `CodebookConfig-r16`** — Carries the IE body (985 chars) with 13 N1·N2 combinations, `typeII-RI-Restriction-r16 BIT STRING (4)`, `paramCombination-r16 INTEGER (1..8)`, and `numberOfPMI-SubbandsPerCQI-Subband-r16 INTEGER (1..2)`, all directly mapping to 38.214's higher-layer parameters `[38.331-asn1-CodebookConfig-r16-001]`.
5. **38.306 capability** — Type-II-specific tokens are not present in the indexed chunks; semantically adjacent (HARQ-ACK type1/type2) capabilities are different items.
6. **38.521-4 §6.3.2.2.6 (and §6.3.2.1.6 / §6.3.3.1.6)** — Performance test for ≥16-port Enhanced Type-II PMI reporting; normative reference TS 38.101-4 §6.3.2.2.6 `[38.521-4-6.3.2.2.6-001]`.

The Enhanced Type-II codebook is the Rel-16 starting point for later codebook families: Rel-17 Further-enhanced Type-II Port Selection (§5.2.2.2.7), Rel-19 Refined eType-II (`'eTypeII-r19'`, §5.2.2.2.5a), and Rel-19 Doppler-prediction variants (`typeII-Doppler-r19`, §§5.2.2.2.10–11a).
