# SPECTRA Answer — The neighbor-cell PBCH decoding assumption and RRM measurement / handover (semantic search over the spec body + cross-validation against the standard structure + external public references)

> Search approach: TS body text of 3GPP is searched by semantic embedding (vector similarity), the standard structure (section / IE definition location, cross-spec references, editions) is cross-validated against the structured representation of the standard, and then **the core verdict of the generated answer is independently cross-checked against public references**. The axes along which the clause structure of the measurement-requirement spec (38.133 §9) divides (intra/inter-frequency · SSB/CSI-RS · FR1/FR2) are adopted directly as decomposition axes. The spec body is the primary authority; external references are auxiliary and confirmatory.

## Conclusion (first)

**In Rel-15 mobility (RRM measurement + handover), the cases where decoding the "content (payload/MIB)" of the neighbor cell's PBCH becomes mandatory are narrow and specific — in most cases it is unnecessary.**

- **The measurement quantities themselves (SS-RSRP/RSRQ/SINR, CSI-RSRP, etc.)** — **unnecessary** on all axes. Measurement is based on SSS (or CSI-RS) power; PBCH DM-RS is merely an optional reference signal.
- **The Rel-15 points where PBCH content decoding actually becomes necessary** (reducible to two physical reasons):
  - **(a) When the UE must determine the SSB index of an FR2 cell on its own** — the upper bits of the index are in the PBCH payload. → When SSB-based · **inter-freq · FR2 · index (beam) reporting** is configured.
  - **(b) When the SFN of an asynchronous neighbor must be acquired** — the SFN is only in the PBCH payload/MIB (FR-independent). → CSI-RS-based · **inter-freq (FR1·FR2)**, and **asynchronous intra (FR1 FDD)**.
- **Handover execution** — a step to acquire the MIB of the target SpCell is procedurally included (omitted when timing is already held / RA is not needed).
- **CGI reporting during measurement *reporting* (reportCGI)** — the neighbor's MIB is read directly.
- The rest (all SSB intra-freq, FR1 SSB index, inter-freq without index reporting, synchronous CSI-RS intra) — **unnecessary**.

→ In one line: **"Decoding is unnecessary for the same frequency / FR1 SSB index / simple power measurement / synchronous CSI-RS. The cells where it becomes mandatory are (i) inter-freq FR2 SSB-index reporting, (ii) SFN acquisition for CSI-RS inter-freq (FR1·FR2) / asynchronous intra, (iii) handover target MIB acquire, (iv) CGI reporting — i.e., only where 'FR2 SSB index self-determination' or 'asynchronous neighbor SFN/MIB acquisition' occurs."**

## Term decomposition — the meaning of "neighbor PBCH decoding"

- **(i) *Power measurement* of the reference signals in the PBCH region** — SSS (primary) + optional PBCH DM-RS power. Not decoding.
- **(ii) SS/PBCH block index determination** — for FR1, the PBCH **DM-RS sequence** (correlation detection); for FR2, additionally the PBCH **payload bits** (channel decoding).
- **(iii) Decoding the PBCH payload/MIB content · SFN** — recovery of the transport-block content such as the SFN. SFN acquisition of an asynchronous neighbor and handover MIB acquire fall here.

Basis — the measurement quantity is SSS power, and PBCH DM-RS is optional (38.215 §5.1.1):

> *"SS reference signal received power (SS-RSRP) is defined as the linear average over the power contributions (in [W]) of the resource elements that carry secondary synchronization signals. ... For SS-RSRP determination demodulation reference signals for physical broadcast channel (PBCH) and, if indicated by higher layers, CSI reference signals in addition to secondary synchronization signals may be used."* [38.215 §5.1.1]

The bit source of the SSB index (38.213 §4.1):

> *"a UE determines the 2 LSB bits of a candidate SS/PBCH block index per half frame from a one-to-one mapping with an index of the DM-RS sequence transmitted in the PBCH ... the UE determines the ... MSB bit[s] of the candidate SS/PBCH block index from PBCH payload bit ... as described in [5, TS 38.212]."* [38.213 §4.1]

The SFN is carried in the PBCH payload (38.213 §4.4):

> *"a same PBCH payload, other than the SFN index and the half frame index, for a first SS/PBCH block ..."* [38.213 §4.4]

→ For FR1, the SSB index is always the DM-RS sequence → payload decoding not needed. Only for FR2 are the upper bits of the index in the payload. The SFN is in the payload/MIB only, regardless of FR.

## RRM measurement — decomposed by the clause structure of the measurement-requirement spec (38.133 §9)

Since 38.133 divides measurement into §9.2 (intra) / §9.3 (inter) / §9.10 (CSI-RS based), these are adopted directly as MECE axes.

### 0. The measurement quantities (RSRP/RSRQ/SINR) themselves → unnecessary on all axes

The power/quality measurement quantities are SSS or CSI-RS power. CSI-RSRP is PBCH-independent (38.215 §5.1.2):

> *"For CSI-RSRP determination CSI reference signals transmitted on antenna port 3000 according to TS 38.211 [3] shall be used."* [38.215 §5.1.2]

### A. SSB-based · intra-frequency → unnecessary for FR1·FR2

For a same-frequency cell, under the synchronization assumption the SSB index is derived from the cell (38.133 §9.2.5.1):

> *"The UE shall be able to identify a new detectable intra-frequency cell within Tidentify_intra_without_index if the UE is not indicated to report SSB based RRM measurement result with the associated SSB index ..., or the UE is indicated that the neighbour cell is synchronous with the serving cell (deriveSSB-IndexFromCell is enabled). ... It is assumed that deriveSSB-IndexFromCell is always enabled for FR1 TDD and FR2 with SCS smaller or equal to 480 kHz."* [38.133 §9.2.5.1]

The meaning of deriveSSB-IndexFromCell (38.133 §7.7.1):

> *"When deriveSSB-IndexFromCell is enabled, the UE assumes frame boundary alignment ... across cells on the same frequency carrier ... and the SFNs of all cells on the same frequency carrier are the same."* [38.133 §7.7.1]

→ **Unnecessary for both FR1 and FR2**: for FR2, deriveSSB is always enabled → SSB index/timing is derived from cell sync. For FR1, the index is the DM-RS sequence anyway. (However, in an out-of-assumption configuration of asynchronous FR2 without deriveSSB set + index reporting, payload decoding is entailed because of the upper bits of the FR2 SSB index — an exception outside the §9.2.5.1 synchronization assumption.)

### B. SSB-based · inter-frequency → unnecessary for FR1 / payload decoding for FR2 when index reporting is set

The cell-derivation option for inter-freq is a later-release feature (38.133 §9.3.4):

> *"the UE shall be able to identify a new detectable inter-frequency cell within Tidentify_inter_without_index if UE is not indicated to report SSB based RRM measurement result with the associated SSB index ... or deriveSSB-IndexFromCellInter-r17 is configured ... Otherwise UE shall be able to identify a new detectable inter-frequency cell within Tidentify_inter_with_index."* [38.133 §9.3.4]

→ Since the Rel-15 baseline does not have `deriveSSB-IndexFromCellInter`(-r17), **when index reporting is configured** the UE must actually determine the index via `with_index`:
- **FR1** — the index is the DM-RS sequence → **unnecessary**.
- **FR2** — the upper bits of the index are in the PBCH payload → **neighbor PBCH payload decoding required**.
- No index reporting (FR1·FR2) — only PSS/SSS identification → **unnecessary**.

### C. CSI-RS-based · intra-frequency → unnecessary if synchronous / SFN decoding if asynchronous (FR1 FDD)

CSI-RS measurement requires an associated SSB + time to **acquire the neighbor's SFN**, but is split by whether synchronous or not (38.133 §9.10.2.5):

> *"... the CSI-RS based measurement shall include PSS/SSS detection time of associatedSSB, the time period used to acquire the SFN information and CSI-RS based measurement period without gap. ... The time period used to acquire the SFN information is equal to 0 if the UE is indicated that the neighbour cell is synchronous with the serving cell (deriveSSB-IndexFromCell is enabled). Otherwise, the time period used to acquire the SFN information is TCSI-RS_SFN_intra ... for FR1. It is assumed that deriveSSB-IndexFromCell is always enabled for FR1 TDD and FR2."* [38.133 §9.10.2.5]

→ **FR1 TDD · FR2 (synchronous)** — SFN acquisition = 0 → **unnecessary**. **Asynchronous FR1 FDD** — SFN acquisition = TCSI-RS_SFN_intra > 0 → neighbor SFN (= PBCH payload) acquisition → **PBCH decoding required**.

### D. CSI-RS-based · inter-frequency → SFN decoding required for both FR1·FR2

Because they are different carriers, there is no same-carrier synchronization assumption, so the SFN acquisition term is always included (38.133 §9.10.3.5):

> *"TCSI-RS_identify_inter = (TPSS/SSS_sync + TCSI-RS_measurement_period_inter + TCSI-RS_SFN_inter) ms ... TCSI-RS_SFN_inter is the time period used to acquire the SFN information of the cell being measured, which is shown in table 9.10.3.5-3 for FR1 and equals inter-frequency TSSB_time_index_inter in clause 9.3.4 for FR2 ..."* [38.133 §9.10.3.5]

→ **FR1** — neighbor SFN acquisition → **PBCH (SFN) decoding required**. **FR2** — SSB time-index (= upper bits of PBCH payload) acquisition → **PBCH payload decoding required**.

## Handover

### E. Handover execution → target SpCell MIB acquire (conditionally omitted)

The configuration is sent down by the source cell via reconfigurationWithSync, but the execution procedure directly specifies, after DL synchronization to the target SpCell, **applying the BCCH configuration + target SpCell MIB acquire** (38.331 §5.3.5.5.2):

> *"start synchronising to the DL of the target SpCell; apply the specified BCCH configuration defined in 9.1.1.1 for the target SpCell; acquire the MIB of the target SpCell, which is scheduled as specified in TS 38.213 [13];"* [38.331 §5.3.5.5.2]

Omission condition (38.331 §5.3.5.5.2):

> *"NOTE 2: The UE may omit reading the MIB if the UE already has the required timing information, or the timing information is not needed for random access ..."* [38.331 §5.3.5.5.2]

→ HO execution includes target MIB acquire in principle (acquiring timing/SFN from the target PBCH/MIB), omitted if the target is known. (reconfigurationWithSync = the procedure introduced in Rel-15.)

## Boundary (measurement reporting / camping)

### F. CGI reporting (reportCGI) → reading the neighbor MIB directly

The `ReportConfigNR.reportType` CHOICE has `reportCGI`, and if that cell's MIB indicates SIB1 is not broadcast, the parameters are obtained directly from that MIB (38.331 §5.5.5.1):

> *"else if MIB indicates the SIB1 is not broadcast: include the noSIB1 including the ssb-SubcarrierOffset and pdcch-ConfigSIB1 obtained from MIB of the concerned cell;"* [38.331 §5.5.5.1]

### G. Cell (re)selection / camping → MIB decoding

At actual camping time, the MIB of the candidate serving cell is decoded to judge access (38.331 §5.2.2.4.1):

> *"Upon receiving the MIB the UE shall: store the acquired MIB; ... if the cellBarred in the acquired MIB is set to barred: ... consider the cell as barred ...; else: apply the received systemFrameNumber, pdcch-ConfigSIB1, subCarrierSpacingCommon, ssb-SubcarrierOffset and dmrs-TypeA-Position."* [38.331 §5.2.2.4.1]

## Comparison table (case → verdict → basis)

| Measurement/operation | freq | FR | PBCH content decoding? | Basis |
|---|---|---|---|---|
| Measurement quantity (RSRP/RSRQ/SINR) | intra·inter | FR1·FR2 | No | 38.215 §5.1.1/§5.1.2 |
| SSB-based | intra | FR1·FR2 | No (deriveSSB / DM-RS) | 38.133 §9.2.5.1·§7.7.1, 38.213 §4.1 |
| SSB-based (index reporting) | inter | FR1 | No (index=DM-RS) | 38.133 §9.3.4, 38.213 §4.1 |
| SSB-based (index reporting) | inter | **FR2** | **Yes — PBCH payload (index MSB)** | 38.133 §9.3.4, 38.213 §4.1 |
| SSB-based (no index reporting) | inter | FR1·FR2 | No (PSS/SSS) | 38.133 §9.3.4 |
| CSI-RS-based (synchronous) | intra | FR1 TDD·FR2 | No (SFN acquisition=0) | 38.133 §9.10.2.5 |
| CSI-RS-based (asynchronous) | intra | **FR1 FDD** | **Yes — PBCH (SFN) acquisition** | 38.133 §9.10.2.5, 38.213 §4.4 |
| CSI-RS-based | inter | **FR1** | **Yes — PBCH (SFN) acquisition** | 38.133 §9.10.3.5 |
| CSI-RS-based | inter | **FR2** | **Yes — PBCH payload (time-index)** | 38.133 §9.10.3.5 → §9.3.4 |
| Handover execution | — | — | **Yes (in principle) — target MIB acquire, conditionally omitted** | 38.331 §5.3.5.5.2 |
| reportCGI reporting | — | — | **Yes — concerned cell MIB** | 38.331 §5.5.5.1 |
| (boundary) camping | — | — | Yes (serving transition) | 38.331 §5.2.2.4.1 |

**One-line conclusion:** Unnecessary for simple measurement / all SSB intra / FR1 SSB index / synchronous CSI-RS. The cells where it becomes mandatory are in bold — all share the same reason of **'FR2 SSB index self-determination' or 'asynchronous neighbor SFN/MIB acquisition'** + handover/CGI.

## Cross-validation against the standard structure

- **Measurement-requirement clause structure = decomposition axes:** 38.133 §9.2 (intra)/§9.3 (inter)/§9.10 (CSI-RS) divide the axes, and each clause's `without_index`/`with_index` + `deriveSSB-IndexFromCell(Inter)` + SFN acquisition conditions determine the detailed verdict.
- **IE definition locations (38.331):** `MeasObjectNR`→`ReferenceSignalConfig` (SSB-based `ssb-ConfigMobility` vs CSI-RS-based `csi-rs-ResourceConfigMobility`), `SSB-ConfigMobility.deriveSSB-IndexFromCell` (Rel-15 base) / `deriveSSB-IndexFromCellInter-r17` (`[[ ]]` extension = Rel-17), `ReportConfigNR.reportType` (including reportCGI), MIB IE. The ASN.1 `-r17` suffix and `[[ ]]` block directly support "inter-freq derivation is Rel-17."
- **cross-WG · layer:** measurement quantity = RAN1 38.215 / SSB index · SFN encoding = RAN1 38.213 · 38.212 / measurement control = RAN2 38.331 / measurement requirement = RAN4 38.133 / handover procedure = RAN2 38.331. The answer is determined by the combination of PHY + RRC + RAN4.

## External cross-validation (independent cross-check)

After generation, the core verdict was independently cross-validated against public references — **result: no conflict (confirmed), no verdict correction needed.**

- **deriveSSB-IndexFromCell ↔ avoiding PBCH decoding** — public references directly confirm the mechanism: *"deriveSSB-IndexFromCell ... allows the UE to use the timing belonging to one NR cell to derive the SSB Indices belonging to other NR cells ... avoids the requirement to decode the PBCH belonging to each individual NR cell."* → consistent with this answer's axis of "intra (deriveSSB enabled) = decoding avoided / inter (Rel-15, deriveSSB-IndexFromCellInter absent) = decoding required."
- **CSI-RS ↔ SSB timing/SFN dependence** — *"UE detects SSB to acquire timing synchronization of a cell, then applies the acquired timing to measure the CSI-RS"*, and when serving/target are asynchronous, SFN/SFTD acquisition is needed → consistent with the SFN (= PBCH payload) dependence of CSI-RS (cases C/D).
- **handover target MIB acquire** — public references and patents confirm target SpCell MIB acquire during reconfigurationWithSync execution (consistent with case E).
- **Source-access limitation**: direct fetch of the authoritative original text, ETSI TS 138 133 V15.x full-text, was blocked by the host (403) → supplemented via web-search snippets + an ATIS S3 mirror (403-free). **The edition markers within the corpus (the `-r17` suffix on IE names, the ASN.1 `[[ ]]` extension) are the primary authority**, and the verdict stands on those markers. External references are for consistency confirmation only.

## Honest gap

- **Release:** the verdict is for Rel-15. `deriveSSB-IndexFromCellInter` (Rel-17) is excluded from the conclusion (this is the basis for the decoding need when inter-freq FR2 index reporting is set). The FR2-2 (480/960 kHz) clause and the "SCS≤480kHz" qualifier in §9.2.5.1 are later editions — for Rel-15 FR2 (120/240 kHz), "always enabled for FR2" applies across the board.
- **Corpus edition limitation:** the index is a single latest edition (38.133 v16.7.0 / 38.331 v18.7.0). The Rel-15 separation is based on the edition markers within the corpus (the `-r17` suffix, the ASN.1 `[[ ]]`) — the primary authority. A full external comparison against the public Rel-15 edition is partial due to ETSI host blocking (independent cross-checking is recommended).
- **Not cited:** the body of 38.212 §7.1.1 (PBCH payload encoding) and detailed numerical values of measurement gap/period are omitted as non-determinative for the decoding-need verdict. The UE capability (38.306) · conformance test (38.521, etc.) layers do not overturn this verdict and so are not cited directly.
