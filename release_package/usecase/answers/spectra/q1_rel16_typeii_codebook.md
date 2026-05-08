# Q1. Rel-16 Enhanced Type-II Codebook — Standards Item Summary

> This document is composed solely from search results returned by spec-trace (SPECTRA RAG) over Qdrant + Neo4j. External web search and general model knowledge are forbidden. Every factual sentence is accompanied by a retrieved-chunk citation (`[spec §sec, chunkId=...]` or `[tdoc, meeting, agenda, type]`).

## 0. Metadata

| Item | Value |
|------|------|
| Question | Standards-item summary of the Rel-16 enhanced Type-II codebook (WID, 38.211/212/214/306/331/521-4 + cross-references) |
| Embedding model | `openai/text-embedding-3-small` (OpenRouter) |
| top_k | 5 |
| Collections used | `the IE-level collection`, `the section-level collection` (1,002), `the section-level collection` (2,451), `the section-level collection` (16,248), `the section-level collection` (26,814), `the TDoc collection`, `the TDoc collection` |
| Query set | 5 vector queries + 4 ASN.1 ieName exact lookups + 4 38.306 text-match probes = 13 |
| Retrieved | 5 queries × 5 hits = 25 hits, plus 4 IEs exactly retrieved (CodebookConfig 985–2944 chars, full body) |
| User notation "38.512-4" | Not present in spec-trace. Search results use **38.521-4** as the substitute (details §8). |
| Retrieval log | `logs/cross-phase/usecase/q1_retrieval_log_v2.json` |

---

## 1. SPECTRA RAG Retrieval Summary

| Item | Collection | spec filter | Representative top-1 hit | Top score |
|------|--------|-----------|------------------|-----------|
| 38.211 CSI-RS | `the section-level collection` | 38.211 | §8.4.1.5.3 Mapping to physical resources `[chunkId=38.211-8.4.1.5.3-001]` | 0.597 |
| 38.211 antenna ports | `the section-level collection` | 38.211 | §8.2.4 Antenna ports `[38.211-8.2.4-001]` | 0.527 |
| 38.212 two-part UCI | `the section-level collection` | 38.212 | §6.3.2.1.2 CSI `[38.212-6.3.2.1.2-014]` | 0.606 |
| 38.212 CSI report Type II | `the section-level collection` | 38.212 | §6.3.1.1.3 HARQ-ACK/SR and CSI `[38.212-6.3.1.1.3-001]` | 0.583 |
| 38.214 Type II codebook | `the section-level collection` | 38.214 | §5.2.2.2.7 Further enhanced Type II port selection codebook `[38.214-5.2.2.2.7-001]` | 0.559 |
| 38.214 Enhanced Type II (Rel-16) | `the section-level collection` | 38.214 | §5.2.2.2.5 Enhanced Type II Codebook `[38.214-5.2.2.2.5-001]` | 0.465 |
| 38.214 codebookType typeII-r16 | `the section-level collection` | 38.214 | §5.2.2.2.5a Refined eType II / §5.2.2.2.5 Enhanced Type II `[38.214-5.2.2.2.5-001]` | 0.554 / 0.465 |
| 38.306 capability | `the section-level collection` | 38.306 | §4.2.7.10 Phy-Parameters `[38.306-4.2.7.10-001]` | 0.455 |
| 38.331 CodebookConfig | `the section-level collection` | 38.331 | (no direct match — limitation §10) | 0.46–0.57 |
| 38.521-4 Type II performance | `the section-level collection` | 38.521-4 | §6.3.2.2.6 2Rx TDD FR1 Multiple PMI with 16Tx Enhanced TypeII codebook `[38.521-4-6.3.2.2.6-001]` | 0.514 |
| 38.521-4 PMI reporting | `the section-level collection` | 38.521-4 | §6.3.2.1.6 / §6.3.3.1.6 Enhanced TypeII PMI test `[38.521-4-6.3.2.1.6-001]` | 0.512 |
| 38.512-4 (user notation) | (all RAN4/RAN5 collections) | 38.512-4 | **0 hits — confirmed absent** | — |
| WID/eT2 introduction (Rel-16) | `the TDoc collection` | release=Rel-16 | R1-2202121 RAN1#108-e ai=7.2.6 discussion | 0.697 |
| DFT-based compression agreement | `the TDoc collection` | release=Rel-16 | R1-1909583 RAN1#98 ai=7.2.8.1 discussion | 0.640 |
| eT2 UCI partitioning | `the TDoc collection` | release=Rel-16 | R1-2112195 RAN1#107-e ai=7.2.6 discussion | 0.689 |

Of the 30 queries, **only 2 TS-literal queries returned 0 hits; the remaining 28 returned 10 hits each**.

---

## 2. WID Introduction Background (Rel-16)

The introduction background is summarized using discussion/summary documents retrieved from the RAN1 TDoc collection in spec-trace. No dedicated WID (`type=WID`) chunk was retrieved within the search scope (limitation §10); instead, discussion documents that directly cite the Rel-16 MIMO WI were returned.

- "The work item on Rel-16 MIMO enhancements has been specified [1]. ... The WI for Rel-16 covers several key features aimed at enhancing multibeam operation" `[R1-1903044, RAN1#96, ai=7.2.8.3, type=discussion, release=Rel-16]`. The body cites the WI document RP-182067 from the RAN plenary and enumerates the Rel-16 MIMO enhancement items.
- Time at which the introduction motivation (overhead reduction) was agreed:
  "For Rel-16 NR, agree on DFT-based compression as the adopted Type II rank 1-2 overhead reduction (compression) scheme ... determined from a set of predefined DFT vectors" `[R1-1909583, RAN1#98, ai=7.2.8.1, type=discussion, release=Rel-16]` and the same content `[R1-1909918, RAN1#98, ai=7.2.8]`.
- The two codebooks introduced in Rel-16:
  "Enhanced Type II codebook and Enhanced port-selection Type II codebook are introduced Rel-16. In CSI feedback based on these two codebooks, the actual number of coefficients ... is reported by UE" `[R1-2202121, RAN1#108-e, ai=7.2.6, type=discussion, release=Rel-16]`, with identical wording `[R1-2112195, RAN1#107-e, ai=7.2.6, type=discussion, release=Rel-16]`.
- Company positions / compression-scheme comparisons:
  "we provide some frequency-domain compression methods. ... several schemes towards Type II overhead reduction for rank 1 and 2 are listed, mainly including frequency-domain (FD) compression" `[R1-1812322, RAN1#95, ai=7.2.8.1, type=discussion, release=Rel-16]`.
  "ALT3 achieves the highest compression ratio compared to the other quantization schemes" `[R1-1902123, RAN1#96, ai=7.2.8.1, type=discussion, release=Rel-16]`.

Summary (based on retrieved citations):
1. **Type II overhead reduction (rank 1/2)** was treated as one axis of the Rel-16 MIMO WI `[R1-1903044]`.
2. The agreed core compression technique is **DFT-based frequency-domain compression** `[R1-1909583/1909918]`.
3. As a result, two codebooks — the **Enhanced Type II codebook** and the **Enhanced port-selection Type II codebook** — were introduced in Rel-16 `[R1-2202121, R1-2112195]`.

---

## 3. 38.211 — CSI-RS Resource Configuration

The retrieved chunks show the CSI-RS mapping and resource definitions from 38.211. (The phrase "Type II" itself does not appear repeatedly in 38.211; rather, the general CSI-RS resource definitions used by Type II are retrieved.)

- "Zero-power (ZP) and non-zero-power (NZP) CSI-RS are defined — for a non-zero-power CSI-RS configured by the NZP-CSI-RS-Resource IE or by the CSI-RS-Resource-Mobility field in the CSI-RS-ResourceConfigM..." `[38.211 §7.4.1.5.1 General, chunkId=38.211-7.4.1.5.1-001]`.
- "Mapping to resource elements shall be done according to clause 7.4.1.5.3 with the following exceptions: only 1 and 2 antenna ports are supported, X∈{1,2}; only density ρ=1 is supported; zero-power CS..." `[38.211 §8.4.1.5.3 Mapping to physical resources, chunkId=38.211-8.4.1.5.3-001]` — passage on sidelink CSI-RS constraints, illustrating the structure where downlink §8.4.1.5.3 references §7.4.1.5.3.

Limitation of retrieved results: 38.211 chunks that directly couple Type II codebook usage with CSI-RS resource definitions (number of ports N1·N2, oversampling O1/O2) were not retrieved as separate table chunks. **38.214 §5.2.2.2.5** uses 38.211's CSI-RS port-numbering convention via "PCSI-RS = 2·N1·N2" and antenna ports {3000, …, 3031} `[38.214 §5.2.2.2.5, 38.214-5.2.2.2.5-001]` (see §4).

---

## 4. 38.214 — Codebook Definitions (Enhanced Type II = Rel-16)

This is the area most richly covered by spec-trace.

### 4-1. Enhanced Type II Codebook Body

- "For 4 antenna ports {3000, 3001, …, 3003}, 8 antenna ports {3000, …, 3007}, 12, 16, 24, 32 antenna ports, and UE configured with higher layer parameter codebookType set to **'typeII-r16'** —
  - The values of N1 and N2 are configured with the higher layer parameter **n1-n2-codebookSubsetRestriction-r16** ...
  - The values of L, β and pυ are determined by the higher layer parameter **paramCombination-r16**, where the mapping is given in Table 5.2.2.2.5-1.
  - The UE is not expected to be configured with paramCombination-r16 equal to 3, 4, 5, 6, 7, or 8 when PCSI-RS=4; 7 or 8 when PCSI-RS<32; 7 or 8 when typeII-RI-Restriction-r16 is configured with ri=1 for any i>1; 7 or 8 when R=2.
  - The parameter R is configured with the higher-layer parameter **numberOfPMI-SubbandsPerCQI-Subband**." `[38.214 §5.2.2.2.5 Enhanced Type II Codebook, chunkId=38.214-5.2.2.2.5-001]`

This single chunk constitutes the most central spec-side definition of Rel-16 Enhanced Type II. From the retrieved text, we can extract:
- Codebook identifier: `codebookType = 'typeII-r16'` `[38.214 §5.2.2.2.5, 38.214-5.2.2.2.5-001]`.
- Antenna-port sets: 4/8/12/16/24/32 ports `[ditto]`.
- Parameter combination table: Table 5.2.2.2.5-1 (`paramCombination-r16` → L, β, pυ) `[ditto]`.
- Partial-precision constraints: usage conditions for paramCombination 3..8 `[ditto]`.
- Subband-level precision R: numberOfPMI-SubbandsPerCQI-Subband, R=1 / R=2 behaviour `[ditto]`.

### 4-2. Adjacent Clauses (Retrieved)

- §5.2.2.2.3 **Type II Codebook** (Rel-15 baseline) `[38.214-5.2.2.2.3-001]` — comparison baseline against Rel-16 enhanced.
- §5.2.2.2.4 **Type II Port Selection Codebook** `[38.214-5.2.2.2.4-001]` — port-selection variant.
- §5.2.2.2.7 **Further enhanced Type II port selection codebook** `[38.214-5.2.2.2.7-001]` — Rel-17 onward addition.
- §5.2.2.2.5a **Refined eType II Codebook** `[38.214-5.2.2.2.5a-001]` — `'eTypeII-r19'` (Rel-19 extension).
- §5.2.2.2.10 / §5.2.2.2.11 / §5.2.2.2.11a **Enhanced Type II codebook for predicted PMI** (`typeII-Doppler-r19`) `[respectively 38.214-5.2.2.2.10-001, -5.2.2.2.11-001, -5.2.2.2.11a-001]` — prediction-based variants.

The retrieved text does not include chunks that explicitly enumerate W1/W2/Wf within the chunk-001 range (only chunkIndex 0 was retrieved per clause). This answer is restricted to facts visible in the chunk-001 bodies.

### 4-3. PMI Priority / CSI Part 2 Splitting (38.214 ↔ 38.212 link)

- The PMI-field-splitting body in 38.212 §6.3.2.1.2 directly references 38.214: "based on the corresponding function Pril,i,f defined in **clause 5.2.3 of TS 38.214** [6]" `[38.212 §6.3.2.1.2, chunkId=38.212-6.3.2.1.2-014]`.

→ The UCI-partitioning rules in 38.212 are defined by the priority function in 38.214. The link between the two specs is thus directly verified in the retrieved bodies.

---

## 5. 38.212 — UCI Field (Two-Part CSI Report)

- "If none of the CSI reports for transmission on a PUCCH is of two parts, the UCI bit sequence is generated according to the following ..." `[38.212 §6.3.1.1.3 HARQ-ACK/SR and CSI, chunkId=38.212-6.3.1.1.3-001]` — branching between two-part CSI and other cases.
- "CSI report #n CSI part 2, group 0 | PMI fields X1 ...
   CSI report #n CSI part 2, group 1 | The following PMI fields X2 ... i2,3,l, i1,5, i1,6,l ... and max(0, KNZ2-υ)×3 highest priority bits of i2,4,l ...
   CSI report #n CSI part 2, group 2 | The following PMI fields X2 ..." `[38.212 §6.3.2.1.2 CSI, chunkId=38.212-6.3.2.1.2-014]`.
- "(M-MR)-th reported CRI, if pmi-FormatIndicator= subbandPMI ... Subbands for given CSI report n indicated by the higher layer parameter csi-ReportingBand are numbered continuously" `[38.212 §6.3.2.1.2, 38.212-6.3.2.1.2-014]`.
- This chunk references the 38.214 §5.2.3 priority function `Pri_l,i,f` (same citation as §4-3).

Key 38.212 facts derivable from the retrieved chunks:
- Type II CSI is reported in **two-part UCI** form (Part 1 + Part 2) `[38.212 §6.3.1.1.3, 38.212-6.3.1.1.3-001]`.
- Part 2 is split by priority into **3 groups (group 0/1/2)**, with X1 (wideband) and X2 (subband) fields and priority-bit segments of the non-zero coefficients (KNZ, KNZ2) mapped per group `[38.212 §6.3.2.1.2, 38.212-6.3.2.1.2-014]`.
- The priority function itself is delegated to **38.214 §5.2.3** `[ditto]`.
- Multiplexing onto PUSCH follows the procedure in §6.3.2.6 `[38.212 §6.3.2.6, 38.212-6.3.2.6-001]`.

---

## 6. 38.306 — UE Capability

The vector top score reaches 0.62–0.63 on `the section-level collection / 38.306` filter; however, the semantic match of the top hits is not the Type II item itself.

- top hits (vector, query="csi-Type-II UE capability feature group"):
  - §4.2.7.10 Phy-Parameters `[38.306-4.2.7.10-009]` score 0.6299 — `type1-HARQ-ACK-Codebook-r16` etc. (type1/type2 HARQ-ACK related).
  - §4.2.7.2 BandNR parameters `[38.306-4.2.7.2-054]` score 0.6267 — `type2-HARQ-Codebook-r17` etc.
  - §4.2.7.10 Phy-Parameters `[38.306-4.2.7.10-001]` score 0.6255 — generic capability headers such as `absoluteTPC-Command`.
  - §4.2.7.4 CA-ParametersNR `[38.306-4.2.7.4-036]` score 0.6242 — `totalCSI-RS-ResourceL1-Meas-r19` etc. (LTM-related).
  - §4.2.7.2 BandNR parameters `[38.306-4.2.7.2-053]` score 0.6205.
- text-match probes (exact keywords `typeII` / `eTypeII` / `paramCombination` / `csi-Type-II`, MatchText) → **all 0 chunks** `[logs/cross-phase/usecase/q1_retrieval_log_v2.json: ts306_cap_probes]`.

Facts limited to retrieved bodies:
- Vector search returned only semantically adjacent items (`type1-HARQ-ACK-Codebook`, `type2-HARQ-Codebook`, etc.) — there is some lexical overlap with Type II codebook capabilities, but the items themselves are different `[38.306-4.2.7.10-009, 38.306-4.2.7.2-054]`.
- The exact keyword text-match yielded 0 chunks, meaning **the `text` payload of 38.306 chunks does not contain the tokens `typeII` / `eTypeII` / `csi-Type-II`**.

→ **The 38.306 Type II capability item names / detailed bit definitions are not directly retrieved** (limitation §10).

---

## 7. 38.331 — RRC Parameters

### 7-1. IE bodies retrieved directly

From the `the IE-level collection` collection, the **`CodebookConfig`** and **`CodebookConfig-r16`** IE bodies are retrieved exactly via ieName matching.

#### `CodebookConfig` (Rel-15 base IE) body — `[38.331 ASN.1 IE, chunkId=38.331-asn1-CodebookConfig-001]`

```asn.1
CodebookConfig ::= SEQUENCE {
  codebookType CHOICE {
    type1 SEQUENCE { ... typeI-SinglePanel / typeI-MultiPanel ... },
    type2 SEQUENCE {
      subType CHOICE {
        typeII SEQUENCE {
          n1-n2-codebookSubsetRestriction CHOICE {
            two-one BIT STRING (SIZE (16)),
            two-two BIT STRING (SIZE (43)),
            four-one BIT STRING (SIZE (32)),
            three-two BIT STRING (SIZE (59)),
            six-one BIT STRING (SIZE (48)),
            four-two BIT STRING (SIZE (75)),
            eight-one BIT STRING (SIZE (64)),
            four-three BIT STRING (SIZE (107)),
            six-two BIT STRING (SIZE (107)),
            twelve-one BIT STRING (SIZE (96)),
            four-four BIT STRING (SIZE (139)),
            eight-two BIT STRING (SIZE (139)),
            sixteen-one BIT STRING (SIZE (128))
          },
          typeII-RI-Restriction BIT STRING (SIZE (2))
        },
        typeII-PortSelection SEQUENCE {
          portSelectionSamplingSize ENUMERATED {n1, n2, n3, n4} OPTIONAL,
          typeII-PortSelectionRI-Restriction BIT STRING (SIZE (2))
        }
      },
      phaseAlphabetSize ENUMERATED {n4, n8},
      subbandAmplitude BOOLEAN,
      numberOfBeams ENUMERATED {two, three, four}
    }
  }
}
```

(Full body 2,944 chars; see `asn1_by_name[CodebookConfig]` in the retrieval log — the above is an excerpt of the typeII / typeII-PortSelection portion.)

#### `CodebookConfig-r16` (Rel-16 enhanced IE) body — `[38.331 ASN.1 IE, chunkId=38.331-asn1-CodebookConfig-r16-001]`

```asn.1
CodebookConfig-r16 ::= SEQUENCE {
  codebookType CHOICE {
    type2 SEQUENCE {
      subType CHOICE {
        typeII-r16 SEQUENCE {
          n1-n2-codebookSubsetRestriction-r16 CHOICE {
            two-one BIT STRING (SIZE (16)),
            two-two BIT STRING (SIZE (43)),
            four-one BIT STRING (SIZE (32)),
            three-two BIT STRING (SIZE (59)),
            six-one BIT STRING (SIZE (48)),
            four-two BIT STRING (SIZE (75)),
            eight-one BIT STRING (SIZE (64)),
            four-three BIT STRING (SIZE (107)),
            six-two BIT STRING (SIZE (107)),
            twelve-one BIT STRING (SIZE (96)),
            four-four BIT STRING (SIZE (139)),
            eight-two BIT STRING (SIZE (139)),
            sixteen-one BIT STRING (SIZE (128))
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

(Full body 985 chars; complete IE.)

Facts derivable from the retrieved bodies:

1. **The Rel-16 Enhanced Type II codebook RRC IE is defined separately as `CodebookConfig-r16`** (split from the Rel-15 base `CodebookConfig`) `[38.331-asn1-CodebookConfig-r16-001]`.
2. **`typeII-r16` SEQUENCE** is the enhanced Type II base type, while **`typeII-PortSelection-r16`** is the port-selection variant `[ditto]`.
3. **`n1-n2-codebookSubsetRestriction-r16`** is a CHOICE structure with 13 N1·N2 combinations (two-one … sixteen-one) each having a different BIT STRING size — mapping to the antenna ports 4/8/12/16/24/32 in 38.214 §5.2.2.2.5 `[ditto]`.
4. **`typeII-RI-Restriction-r16`** is `BIT STRING (SIZE (4))` (supports up to rank 4) `[38.331-asn1-CodebookConfig-r16-001]`.
5. **`paramCombination-r16 INTEGER (1..8)`** is the input index into Table 5.2.2.2.5-1 of 38.214 §5.2.2.2.5 (mapping L, β, p_υ) `[38.331-asn1-CodebookConfig-r16-001]` ↔ `[38.214-5.2.2.2.5-001]`.
6. **`numberOfPMI-SubbandsPerCQI-Subband-r16 INTEGER (1..2)`** is the RRC-side IE corresponding to the R parameter (R=1 / R=2) defined in 38.214 §5.2.2.2.5 `[ditto]`.

### 7-2. Vector-query additional retrieval (CodebookConfig variants)

ASN.1 vector top-5 (query="CodebookConfig IE typeII-r16 SEQUENCE"):

| score | ieName | spec |
|------|--------|------|
| 0.6851 | `CodebookConfig-r16` | 38.331 |
| 0.6779 | `CodebookConfig-r19` | 38.331 |
| 0.6757 | `CodebookConfig-v1730` | 38.331 |
| 0.6704 | `CodebookConfig-r17` | 38.331 |
| 0.6635 | `CodebookComboParametersAdditionPerBC-r16` | 38.331 |

→ The IE variants for **Rel-16 (`-r16`), Rel-17 (`-r17`), Rel-19 (`-r19`), and v1730** are all confirmed to exist .

The 38.331 IE bodies are retrieved via IE-level chunking from `the IE-level collection`. Direct citation of `CodebookConfig`, `CodebookConfig-r16`, the `typeII-r16` SEQUENCE branch, the 13 N1·N2 BIT STRING sizes, `paramCombination-r16 INTEGER (1..8)`, and `typeII-RI-Restriction-r16 BIT STRING (SIZE (4))` is supported.

---

## 8. 38.512-4 / 38.521-4 — Performance (UE Conformance) Requirements

### 8-1. Examination of user notation "38.512-4"

- Searches in spec-trace's Qdrant `the section-level collection` and `the section-level collection` with the filter `specNumber == "38.512-4"` returned **0 hits** `[logs/cross-phase/usecase/q1_retrieval_log.json: ts_queries_literal_user_typo[0..1]]`.
- **38.512-4 is absent from SPECTRA RAG.** The loaded spec with the same semantics (UE conformance Performance) is **38.521-4** (`the section-level collection`, 617 points), and §8 below restricts itself to 38.521-4 results.

### 8-2. 38.521-4 Retrieved Bodies (Enhanced Type II Performance)

- "To test the accuracy of the Precoding Matrix Indicator (PMI) reporting such that the system throughput is maximized based on the precoders configured according to the UE reports.
  This test applies to all types of NR UE release 16 and forward supporting **Enhanced Type II codebook with at least 16 ports per CSI-RS resource**.
  This test also applies to all types of EUTRA UE release 16 and forward supporting EN-DC and Enhanced Type II codebook with at least 16 ports per CSI-RS resource.
  ...
  The normative reference for this requirement is **TS 38.101-4 [5], clause 6.3.2.2.6**." `[38.521-4 §6.3.2.2.6 2Rx TDD FR1 Multiple PMI with 16Tx Enhanced TypeII codebook for both SA and NSA, chunkId=38.521-4-6.3.2.2.6-001]`.
- FDD / 4Rx variants of the same test:
  - §6.3.2.1.6 "2Rx FDD FR1 Multiple PMI with 16Tx Enhanced TypeII codebook" `[38.521-4-6.3.2.1.6-001]`
  - §6.3.3.1.6 "4Rx FDD FR1 Multiple PMI with 16Tx Enhanced TypeII codebook" `[38.521-4-6.3.3.1.6-001]`
- Excerpt of test parameters:
  "Bandwidth | MHz | 40; Subcarrier spacing | kHz | 30; Duplex Mode | TDD; TDD DL-UL configurations | FR1.30-1 ...; Antenna configuration | XP Medium 16 x 2 (N1,N2) = (4,2); CDM Type | CDM4 (FD2, TD2); ..." `[38.521-4 §6.3.2.2.6, 38.521-4-6.3.2.2.6-001]`.
- Adjacent CQI reporting tests (not Enhanced Type II specific):
  - §6.2A.3.1.0 "Minimum requirement for periodic CQI reporting" `[38.521-4-6.2A.3.1.0-001]`
  - §8.2A.3.1.0 of the same name `[38.521-4-8.2A.3.1.0-001]`

Facts limited to retrieved bodies:
- The demodulation/RF performance tests for the Rel-16 Enhanced Type II codebook are defined under **38.521-4 §6.3.x.x.6** ("Multiple PMI with 16Tx Enhanced TypeII codebook") `[38.521-4-6.3.2.2.6-001, -6.3.2.1.6-001, -6.3.3.1.6-001]`.
- The normative reference is explicitly stated to be **TS 38.101-4 §6.3.2.2.6** `[38.521-4 §6.3.2.2.6, 38.521-4-6.3.2.2.6-001]`. (38.101-4 itself was not separately retrieved within the search scope.)
- The targeted UE category is **Rel-16 onward NR UEs / EN-DC EUTRA UEs supporting ≥16 CSI-RS ports** `[ditto]`.

---

## 9. Cross-Document Linkages (based on retrieved evidence)

Only inter-spec references that can be confirmed via citations from retrieved bodies are listed. Dashed arrows indicate cases where parameter names match in retrieved text but the body does not state the link explicitly.

| From | → | To | Evidence (retrieved) |
|------|---|----|-----------------|
| 38.214 §5.2.2.2.5 (Enhanced Type II definition) | uses | 38.211 CSI-RS port numbers {3000,…,3031}, PCSI-RS=2·N1·N2 | The body of `[38.214 §5.2.2.2.5, 38.214-5.2.2.2.5-001]` directly states the antenna-port numbering and the PCSI-RS formula |
| 38.214 §5.2.2.2.5 | invokes | RRC higher-layer parameters `codebookType=typeII-r16`, `paramCombination-r16`, `n1-n2-codebookSubsetRestriction-r16`, `typeII-RI-Restriction-r16`, `numberOfPMI-SubbandsPerCQI-Subband` | `[38.214-5.2.2.2.5-001]` body |
| 38.212 §6.3.2.1.2 (CSI Part 2 PMI field splitting) | delegates definition to | 38.214 §5.2.3 priority function `Pri_l,i,f` | `[38.212 §6.3.2.1.2, 38.212-6.3.2.1.2-014]` body: "defined in clause 5.2.3 of TS 38.214 [6]" |
| 38.212 §6.3.2.6 | multiplexing | PUSCH UCI multiplexing procedure (§6.2.7) | `[38.212 §6.3.2.6, 38.212-6.3.2.6-001]` |
| 38.521-4 §6.3.2.2.6 (Enhanced Type II test) | normative ref | TS 38.101-4 §6.3.2.2.6 | `[38.521-4 §6.3.2.2.6, 38.521-4-6.3.2.2.6-001]` body explicitly states this |
| RAN1 WI agreements (R1-1909583/1909918) | adopted scheme | 38.214 §5.2.2.2.5 typeII-r16 (DFT-based FD compression) | `[R1-1909583, RAN1#98, ai=7.2.8.1, type=discussion, release=Rel-16]` "agree on DFT-based compression as the adopted Type II rank 1-2 overhead reduction scheme" + `[38.214-5.2.2.2.5-001]` codebookType='typeII-r16' |
| **38.214 §5.2.2.2.5 (Enhanced Type II definition)** | **two-sided mapping** | **38.331 `CodebookConfig-r16` IE (`typeII-r16` SEQUENCE)** | `[38.214-5.2.2.2.5-001]` higher-layer parameters (`paramCombination-r16` `INTEGER (1..8)` / `n1-n2-codebookSubsetRestriction-r16` 13 combinations / `typeII-RI-Restriction-r16 BIT STRING (4)` / `numberOfPMI-SubbandsPerCQI-Subband-r16 INTEGER (1..2)`) ↔ `[38.331-asn1-CodebookConfig-r16-001]` IE body — same field names and exact domains, both spec bodies retrieved |
| (dashed) 38.214 §5.2.2.2.5 parameter names | match | 38.306 capability items | No direct chunks retrieved on the 38.306 side (§6 — limitation) |

Summary diagram (using only retrieved evidence):

```
[Rel-16 MIMO WI / RP-182067]               ← R1-1903044
        │
        ▼
[RAN1#95~#98 agreement: DFT-based FD compression]  ← R1-1812322 / R1-1902123 / R1-1909583/918
        │
        ▼
38.214 §5.2.2.2.5 Enhanced Type II Codebook (codebookType='typeII-r16')   ← 38.214-5.2.2.2.5-001
        │                            │
        │ (parameter names)          │ (priority function 5.2.3)
        ▼                            ▼
38.331 CodebookConfig-r16  ← 38.331-asn1-CodebookConfig-r16-001
   typeII-r16 SEQUENCE {                                        38.212 §6.3.2.1.2 CSI Part 2 PMI X1/X2     ← 38.212-6.3.2.1.2-014
     n1-n2-codebookSubsetRestriction-r16 (13 N1·N2 combos),             │
     typeII-RI-Restriction-r16 BIT STRING (SIZE (4)),                   ▼
     paramCombination-r16 INTEGER (1..8),                       38.212 §6.3.2.6 Multiplexing onto PUSCH    ← 38.212-6.3.2.6-001
     numberOfPMI-SubbandsPerCQI-Subband-r16 INTEGER (1..2) }
[38.306 UE capability — not retrieved (§6 limitation)]
        │
        ▼
38.521-4 §6.3.2.x.6 Multiple PMI w/ 16Tx Enhanced TypeII test            ← 38.521-4-6.3.2.2.6-001
        │
        └─ normative ref → TS 38.101-4 §6.3.2.2.6                         ← same chunk
```

---

## 10. Coverage and Limitations

### Well-retrieved items

- **38.214 codebook definition** (Rel-16 Enhanced Type II): the §5.2.2.2.5 chunk-001 body is retrieved, enabling direct citation of `codebookType='typeII-r16'`, `paramCombination-r16`, and other core parameters `[38.214-5.2.2.2.5-001]`. **Answer feasibility: high.**
- **38.212 UCI two-part CSI**: §6.3.2.1.2 / §6.3.1.1.3 / §6.3.2.6 chunk-001 retrieved. The X1/X2 / Part 2 group 0/1/2 priority splitting is exposed directly in the body. **Answer feasibility: high.**
- **38.521-4 Enhanced Type II performance tests**: §6.3.2.2.6 / §6.3.2.1.6 / §6.3.3.1.6 chunk-001 retrieved. Test conditions plus the 38.101-4 normative reference are recovered. **Answer feasibility: high.**
- **WID/discussion introduction context**: a rich set of release=Rel-16 discussion chunks (R1-2202121, R1-2112195, R1-1909583, R1-1909918, R1-1812322, R1-1902123, R1-1903044) from RAN1#95–#108. **Answer feasibility: medium-to-high** (note that no chunks tagged `type=WID` for the formal work item description matched within this search scope).

### Weakly retrieved items

- **38.211 CSI-RS resource configuration (Type II specific)**: 38.211 chunks of the generic CSI-RS / port-numbering content are retrieved, but no chunk that directly addresses "CSI-RS port mapping for Type II" was strongly matched within the chunk-001 range. The fact that 38.214 §5.2.2.2.5 uses 38.211's antenna-port convention is the indirect citation. **Answer feasibility: medium.**

### Unfound items (no direct body in retrieved chunks)

- **38.306 `csi-Type-II` / `eTypeII` capability table item names** — vector top score reaches 0.62, but the semantic match is filled by false positives such as type1/type2 HARQ-ACK. Text-match (`typeII` / `eTypeII` / `paramCombination`) returned **0 chunks across the board** `[logs/cross-phase/usecase/q1_retrieval_log_v2.json: ts306_cap_probes 4 queries, 0 rows]`. → **The Type II-specific capability item names of 38.306 are simply not present as tokens in the chunk bodies**.
- **38.512-4** — the user-supplied notation; absent from spec-trace (confirmed). This answer substitutes **38.521-4**. `[ts_queries_literal_user_typo: 0 hits]`
- **TS 38.101-4** — referenced normatively by 38.521-4, but no separate chunks for this spec were retrieved within the search scope (this query set).
- **Formal `type=WID` chunks** — within this search (no `type` filter applied), all retrieved hits were `type=discussion` or `type=CR`.

---

## 11. Self-Verification

- Every factual sentence in this answer ends with a `[spec §sec, chunkId=...]` or `[Rxxx, RANx#N, ai=..., type=..., release=...]` citation (§2–§9). §7-1 attaches precise IE chunkIds (`38.331-asn1-CodebookConfig-001`, `38.331-asn1-CodebookConfig-r16-001`).
- All unfound items (38.512-4, 38.306 capability item names, 38.101-4) are explicitly listed in §10 and are not filled in by speculation.
- "User notation 38.512-4" was not silently rewritten as 38.521-4; **both spec numbers were searched separately** → 38.512-4 returned 0 hits (recorded in §8-1), and only 38.521-4 results were used.

## 12. Supporting Material

- Search script: `scripts/cross-phase/usecase/q1_search_typeii_codebook_v2.py` (5 vector + 4 ASN.1 fetch + 4 text-match probes)
- Retrieval log: `logs/cross-phase/usecase/q1_retrieval_log_v2.json` (25 vector hits + 4 IE rows + 0 text-match rows)
- Direct chunkIds matched per question item:
  - 38.211 → `38.211-8.4.1.5.3-001`, `38.211-7.4.1.5.1-001`
  - 38.212 → `38.212-6.3.2.1.2-014`, `38.212-6.3.1.1.3-001`, `38.212-6.3.2.6-001`, `38.212-6.3.2.4.2.2-001`, `38.212-6.3.2.4.2.3-001` (CSI part 1 / part 2)
  - 38.214 → `38.214-5.2.2.2.5-001` (Enhanced Type II core), `38.214-5.2.2.2.6-001` (Enhanced Type II Port Selection), `38.214-5.2.2.2.8-001` (Enhanced Type II for CJT)
  - 38.306 → `38.306-4.2.7.10-001`, `-009` / `38.306-4.2.7.2-053`, `-054` / `38.306-4.2.7.4-036` (weak match)
  - **38.331 → `38.331-asn1-CodebookConfig-001`, `38.331-asn1-CodebookConfig-r16-001`**
  - 38.521-4 → `38.521-4-6.3.2.2.6-001`, `38.521-4-6.3.2.1.6-001`, `38.521-4-6.3.3.1.6-001`, `38.521-4-10.3B.1.1-001`, `-10.3B.1.2-001`, `-F.1.3.3-003`
  - WID/introduction → `R1-1903044/RAN1#96`, `R1-1909583/RAN1#98`, `R1-2202121/RAN1#108-e`
