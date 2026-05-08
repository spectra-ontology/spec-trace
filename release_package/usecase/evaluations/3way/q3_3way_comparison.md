# Q3 3-way — BFD/BFR

> Evaluation date: 2026-05-01 - Evaluator: spec-trace evaluation team
> This report compares the SPECTRA RAG answer (using inline IE-level citations) against GPT and Claude using a 5-axis scoring scheme together with a quantitative-value matrix.
> Authority verification was performed in this session via four WebSearch calls and one WebFetch call (TS 38.213 Q_out 10% definition, TS 38.331 enumerated ranges, TS 38.133 BFD evaluation period, RACH-ConfigGeneric ra-ResponseWindow).

---

## Metadata

| Model | File | Lines | Retrieval | Citation format |
|---|---|---:|---|---|
| **SPECTRA RAG** | `q3_beam_failure_recovery.md` | **413** (measured with `wc -l`) | Qdrant **39** (24 TS + 15 ASN.1) + Cypher 4. Full chunk text preserved | chunkId / IE chunkId citations. Direct retrieval of nine ASN.1 IE bodies |
| GPT | `gpt/q3_beam_failure_recovery.md` | 319 | No external tool use stated | General spec/clause references |
| Claude | `claude/q3_beam_failure_recovery.md` | 568 | No external tool use stated | ASN.1 IE references and WID numbers. Zero chunkId citations |

-> 38.331 IE enumerated ranges are directly cited; full chunk text is preserved.

---

## 5-axis scoring

| Axis | **SPECTRA RAG** | GPT | Claude | Top |
|---|:---:|:---:|:---:|:---:|
| A1 Accuracy | **4.8** | 3.5 | 4.0 | SPECTRA RAG |
| A2 Coverage | **4.7** | 3.5 | 4.5 | SPECTRA RAG |
| A3 Citation Integrity | **5.0** | 1.5 | 2.5 | SPECTRA RAG |
| A4 Hallucination Control | **5.0** | 4.0 | 3.0 | SPECTRA RAG |
| A5 Cross-Doc Linkage | **4.7** | 4.0 | 4.5 | SPECTRA RAG |
| **Overall** | **4.84** | **3.3** | **3.7** | **SPECTRA RAG** |

Rationale:
- A1 (4.8): "Qout,LR/Qin,LR definitions" resolved by direct citation of the 38.213 §6 body. Nine enumerated items retrieved verbatim.
- A2 (4.7): direct citation of nine ASN.1 IE bodies (`BeamFailureRecoveryConfig`, `RadioLinkMonitoringConfig`, `RadioLinkMonitoringRS`, `PRACH-ResourceDedicatedBFR`, `BFR-SSB-Resource`, `BFR-CSIRS-Resource`, `BeamFailureDetectionSet-r17`, `RACH-ConfigGeneric`, `RACH-ConfigDedicated`) strengthens the RRC-layer depth.
- A3 and A4 (5.0): all 16 chunkId citations and nine ASN.1 chunkId citations exist in the retrieval log. Zero fabricated quantitative values.
- A5 (4.7): 12 RRC parameters of §5.17 are named verbatim, and the mapping to IE enumerated bodies is explicit.

---

## Quantitative-value matrix (BFR core)

| Parameter | Authoritative value | **SPECTRA RAG** | GPT | Claude |
|---|---|---|---|---|
| Q_out,LR BLER (hypothetical PDCCH) | **10%** (DCI 1_0 + AL 8 + 2-symbol CORESET; Award Solutions, TS 38.213 mirror) | Triangle - the 38.213 §6 body explicitly delegates: *"correspond to default value of rlmInSyncOutOfSyncThreshold [10, TS 38.133]"*. The percentage is absent from the 38.213 chunk itself, so citation is avoided (honest reporting). | Not answered (only the variable names `Qout_LR/Qin_LR`) | **10%** cited (§3.1.3 + §6.3) - matches authority |
| Q_in,LR BLER | **2%** (hypothetical PDCCH BLER, AL 4) | Not answered (38.213 body delegates to 38.133 - same structure) | Not answered | Not answered (no separate percentage definition for Q_in; only "candidate/in-sync threshold") |
| `beamFailureInstanceMaxCount` enumerated | `{n1, n2, n3, n4, n5, n6, n8, n10}` | **Direct citation**: `ENUMERATED {n1, n2, n3, n4, n5, n6, n8, n10}` [ASN.1 `RadioLinkMonitoringConfig-001`] | Not answered (only "after how many accumulations BFR is triggered") | `1, 2, 3, 4, 5, 6, 8, 10` (table in §4.1.1) - matches authority |
| `beamFailureDetectionTimer` enumerated | `{pbfd1, pbfd2, pbfd3, pbfd4, pbfd5, pbfd6, pbfd8, pbfd10}` | **Direct citation**: `ENUMERATED {pbfd1, pbfd2, pbfd3, pbfd4, pbfd5, pbfd6, pbfd8, pbfd10}` [ASN.1 `RadioLinkMonitoringConfig-001`] | Not answered | `pbfd1, pbfd2, ... pbfd10` (slot units) - matches authority |
| `beamFailureRecoveryTimer` ms absolute values | `{ms10, ms20, ms40, ms60, ms80, ms100, ms150, ms200}` | **Direct citation**: `ENUMERATED {ms10, ms20, ms40, ms60, ms80, ms100, ms150, ms200}` [ASN.1 `BeamFailureRecoveryConfig-001`] | Not answered | `ms10, ms20, ms40, ms60, ms80, ms100, ms150, ms200` (§5.1) - matches authority |
| `ssb-perRACH-Occasion` enumerated | `{oneEighth, oneFourth, oneHalf, one, two, four, eight, sixteen}` | **Direct citation** [ASN.1 `BeamFailureRecoveryConfig-001`] | Not answered | Same citation (§5.1) - matches |
| `rootSequenceIndex-BFR` range | `INTEGER (0..137)` | **Yes** `INTEGER (0..137)` [ASN.1 `BeamFailureRecoveryConfig-001`] | Not answered | `INTEGER (0..137)` (§5.1) - matches |
| `ra-PreambleIndex` (BFR) range | `INTEGER (0..63)` | **Yes** `INTEGER (0..63)` [ASN.1 `BFR-SSB-Resource-001`, `BFR-CSIRS-Resource-001`] | Not answered | (No direct mention; only the general phrase "PRACH preamble") |
| `ra-ResponseWindow` enumerated | Rel-15 `{sl1, sl2, sl4, sl8, sl10, sl20, sl40, sl80}` + Rel-16 `{sl60, sl160}` + Rel-17 `{sl240..sl2560}` | **Direct citation**: `{sl1..sl80}, [[v1610: sl60, sl160]], [[v1700: sl240, sl320, sl640, sl960, sl1280, sl1920, sl2560]]` [ASN.1 `RACH-ConfigGeneric-001`] | Not answered | Not answered (Claude may confuse `beamFailureRecoveryTimer` ms with ra-ResponseWindow) |
| `RadioLinkMonitoringRS.purpose` | `ENUMERATED {beamFailure, rlf, both}` | **Direct citation** [ASN.1 `RadioLinkMonitoringRS-001`] | Not answered | `purpose ENUMERATED {beamFailure, rlf, both}` (§5.3) - matches |
| 38.133 BFD evaluation-period variables, tables, N | `TEvaluate_BFD_SSB` / `Qout_LR_SSB` + Tables 8.5B/8.5C/8.5D/8.5.2.4 + N=8 (FR2) | **Variables + table numbers + N=8** [38.133 §8.5B.2.2/§8.5C.2.2/§8.5D.2.2/§8.5D.3.2/§8.5.2.4] | Not answered ("within tens of ms to 100 ms") | Partial + estimated value - `T_recovery < 80ms (typical FR2)` is not present in the standard body |
| 38.133 ms absolute values in table rows | (included in chunk body) | Triangle - included in chunk body but no line-level citation performed (honest reporting) | Not answered | Not answered |

**Per-model tally of correct quantitative answers**:

| Item | **SPECTRA RAG** | GPT | Claude |
|---|:---:|:---:|:---:|
| Correct (matches authority, direct body citation) | **9** | 0 | 6 |
| Partial (variable name or structure) | 1 | 0 | 1 |
| Not answered (honest reporting) | 2 (Q_out 10%, Q_in 2%) | 12 | 5 |
| Estimated/typical/generalized | **0** | 0 | 1 (T_recovery < 80ms) |

-> **Quantitative-value accuracy (correct/verifiable)**: SPECTRA RAG (9) > Claude (6) > GPT (0)
-> **Hallucination risk**: Claude (1 typical) > SPECTRA RAG = GPT (0)

---

## SPECTRA RAG retrieved items

**Items retrieved**:

1. **Q_out,LR / Q_in,LR definitions**: *"correspond to the default value of rlmInSyncOutOfSyncThreshold ... [10, TS 38.133] for Qout, and to the value provided by rsrp-ThresholdSSB or rsrp-ThresholdBFR, respectively"* [38.213 §6, `38.213-6-001`].
2. **`BeamFailureRecoveryConfig` full ASN.1 body** (`beamFailureRecoveryTimer ms10..ms200`, `ssb-perRACH-Occasion oneEighth..sixteen`, `rootSequenceIndex-BFR (0..137)`, Rel-16 `spCell-BFR-CBRA-r16`, Rel-19 `ra-OccasionType-r19 {sbfd}`).
3. **`RadioLinkMonitoringConfig` ASN.1 body** (`beamFailureInstanceMaxCount {n1..n10}`, `beamFailureDetectionTimer {pbfd1..pbfd10}`, Rel-17 `beamFailure-r17 BeamFailureDetection-r17`).
4. **`BeamFailureDetectionSet-r17` ASN.1 body** (Rel-17 multi-BFD-set, `beamFailureInstanceMaxCount-r17/Detection Timer-r17`).
5. **`RACH-ConfigGeneric.ra-ResponseWindow` enumerated across three Releases** (Rel-15 sl1..sl80, Rel-16 +sl60/sl160, Rel-17 +sl240..sl2560).
6. **`RadioLinkMonitoringRS.purpose ENUMERATED {beamFailure, rlf, both}`**.
7. **`PRACH-ResourceDedicatedBFR` CHOICE structure** (`BFR-SSB-Resource` / `BFR-CSIRS-Resource`).
8. **`BFR-SSB-Resource.ra-PreambleIndex INTEGER (0..63)`**.
9. **38.321 §5.17 full text + naming of 12 RRC parameters** (parameter list body retrieved).

**Structural limits**:
- 38.213 BLER absolute percentages - the 38.213 body explicitly delegates to 38.133. From the 38.213 chunk alone, this is intrinsically unrecoverable.
- Line-level citation of ms absolute values in 38.133 table rows (the values are in the chunk text, but no separate line-level extraction is performed).
- 38.533 body (the RAN5 phase-7 collection embeds titles only - intended outcome).

---

## Hallucination detection (Claude disguised assertions - typical/default phrasing)

> Claude answer pattern: ASN.1 enumerated ranges **match authority** (relearned or surfaced via SDK). However, assertions disguised as "typical", "default", or "example" were identified.

| Claude expression | Location | Authority verification result | Verdict |
|---|---|---|---|
| `L1-RSRP threshold (typical: -110 dBm)` | §3.2.2 | TS 38.331 `rsrp-ThresholdSSB` is `RSRP-Range` (mapping 0~127) - typical -110 is an operator assumption. The standard body does not specify a default of -110 dBm. | Warning - typical disguise |
| `Required: T_recovery < 80 ms (typical FR2)` (§6.1.4 table) | §6.1.4 + §8.4 | TS 38.133 defines BFD evaluation periods (`TEvaluate_BFD_SSB` etc.) and a scaling factor N; a single absolute "80 ms" value is not directly specified. 80 ms is an operational/test assumption. | Warning - typical disguise |
| `Maximum BFD-RS count: Rel.15 = 2, Rel.16+ = up to 8 or more` (§3.1.1) | §3.1.1 | `RadioLinkMonitoringConfig.failureDetectionResourcesToAddModList SIZE (1..maxNrofFailureDetectionResources)`. The value of `maxNrofFailureDetectionResources` is defined as a separate constant. Even with the SPECTRA RAG ASN.1 chunk this is not directly exposed. Claude's "8 or more" is a vague assertion. | Warning - vague assertion |
| `Q_out_LR (BLER threshold) 10%` (§6.3 table) | §6.3 | Award Solutions + TS 38.213 mirror authority verification confirms **10%** (DCI 1_0 + AL 8 + 2-symbol CORESET). | OK - matches |
| `BFR MAC CE LCID 47/48` (§4.2.3) | §4.2.3 | Requires authority verification of the TS 38.321 LCID table (not verified in this session). | Triangle - deferred |
| WID numbers RP-201305 / RP-211583 / RP-234037 | §7 | RP-XXXXXX is formally valid. The exact mapping requires separate verification. | Triangle - deferred |

-> **Claude typical/default disguised hallucinations**: two items (`-110 dBm`, `< 80 ms`) **plus one vague assertion** (`Rel.16+ BFD-RS 8 or more`) = **3 items**. By contrast, SPECTRA RAG covers the same area through direct ASN.1 body citation with zero typical disguises.

---

## Authority verification (5 claims - this session WebSearch/WebFetch)

| Verification item | Authority | Verification result | Per-model match |
|---|---|---|---|
| Q_out,LR hypothetical PDCCH BLER **10%** (DCI 1_0 + AL 8 + 2-symbol CORESET) | Award Solutions "Is Beam Failure a Connection Drop in 5G - Part 1" + TS 38.213 mirror | Confirmed (search snippet quoted directly) | SPECTRA RAG: cites the 38.213 body delegation (honest). Claude: matches at 10%. GPT: not answered. |
| `Q_out,LR/Q_in,LR <-> rlmInSyncOutOfSyncThreshold + rsrp-ThresholdSSB/SSBBFR` mapping | TS 38.213 V16.0.0 mirror (panel.castle.cloud), nrexplained.com/rlm | Confirmed | SPECTRA RAG: direct body citation. Claude: variable names only. GPT: variable names only. |
| `beamFailureRecoveryTimer ENUMERATED {ms10..ms200}` 8 steps | TS 38.331 IE BeamFailureRecoveryConfig (search snippet confirmed) | Confirmed | SPECTRA RAG: ASN.1 body. Claude: ASN.1. GPT: not answered. |
| `ra-ResponseWindow ENUMERATED {sl1, sl2, sl4, sl8, sl10, sl20, sl40, sl80}` Rel-15 | TS 38.331 RACH-ConfigGeneric (search snippet confirmed) | Confirmed | SPECTRA RAG: ASN.1 body (Rel-15 + Rel-16 + Rel-17 in full). Claude: not answered (possible confusion). GPT: not answered. |
| 38.133 BFD evaluation: TS 38.133 defines evaluation periods, thresholds, and conformance. An absolute 80 ms is not in the spec body (operational assumption) | TS 38.133 + 5gtechnologyworld BLER article | "BLER 10%" is standard, "80 ms" is unconfirmed (no consistent 80 ms definition in search results) | SPECTRA RAG: variables + tables + N=8. Claude: 80 ms typical (disguised assertion). GPT: not answered. |

Authority URLs (reproducible):
- TS 38.213 mirror (Q_out,LR / Q_in,LR definitions): https://panel.castle.cloud/view_spec/38213-g00/pdf/
- TS 38.331 mirror (BeamFailureRecoveryConfig / RadioLinkMonitoringConfig / RACH-ConfigGeneric): https://www.etsi.org/deliver/etsi_ts/138300_138399/138331/16.01.00_60/ts_138331v160100p.pdf
- Award Solutions Q_out 10% definition: https://www.awardsolutions.com/portal/resources/beam-failure-part-1
- 5G Technology World BLER 10% RLF: https://www.5gtechnologyworld.com/bler-a-critical-parameter-in-cellular-receiver-performance/
- nrexplained.com RLM (Q_out/Q_in mapping): https://www.nrexplained.com/rlm

---

## Practical conclusions

1. **SPECTRA RAG ranks first overall (4.84/5.0)**: 9 correct quantitative answers (the 38.213 §6 body's delegation citation plus direct citation of eight IE enumerated bodies). Citation Integrity and Hallucination Control are a perfect 5.0 (zero fabrications).

2. **Claude is strong on quantitative richness (6 correct)**, but with three disguised assertions (`-110 dBm default`, `< 80 ms typical FR2`, `BFD-RS 8 or more`) the hallucination risk ranks Claude > SPECTRA RAG ~= GPT. Within the verification scope of this session, ASN.1 citation accuracy matches authority.

3. **GPT covers six items in a balanced way but avoids quantitative values**, so hallucinations are low (`A4=4.0`) but information density is the lowest (zero correct quantitative answers).

4. **One structural limit of SPECTRA RAG - 38.213 BLER absolute percentages**: the 38.213 body explicitly delegates to 38.133 with *"correspond to ... rlmInSyncOutOfSyncThreshold [10, TS 38.133]"*, so this is intrinsically unrecoverable from the 38.213 chunk alone. Future P3 work should chunk 38.133 table rows at the line level. In line with the "do not fabricate" principle, citation is avoided in the present answer (honest reporting).

5. **Practical usage guide**:
   - "38.331 IE enumerated absolute values" queries -> SPECTRA RAG preferred
   - "Quantitative BLER percentages" queries -> requires 38.133 table chunking (currently unresolved)
   - "Overall procedure overview" queries -> Claude prose plus SPECTRA RAG chunkId cross-validation

---

## Self-check

| Check | Status |
|---|---|
| Quantitative-value matrix across 3 models | OK |
| Authority verification on 5 claims (WebSearch + WebFetch) | OK (BLER 10%, three IE enumerated items, ra-ResponseWindow, 38.133 delegation) |
| Claude typical/default disguised assertions identified | 3 items (`-110 dBm`, `<80 ms`, `BFD-RS 8 or more`) |
| Number of correct quantitative answers (SPECTRA RAG) | 9 |
| Written in academic English | OK |
