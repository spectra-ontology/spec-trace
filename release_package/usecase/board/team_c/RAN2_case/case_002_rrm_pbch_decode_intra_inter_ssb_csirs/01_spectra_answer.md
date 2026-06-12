# Whether neighbor cell PBCH (payload/MIB) decode is needed for RRM measurement (Rel-15)

> Basis: verbatim 3GPP TS quotations + standards-structure cross-checking. Every verdict is grounded only on TS clauses retrieved from the corpus or on the `-rNN` introduction tags of ASN.1 fields. Cells with no evidence found are left blank.

## 0. Question scope lock (release lock)

- **Release: Rel-15 baseline.**
- **Version caveat (honest)**: For Rel-15, judgments are made by combining (1) the body mechanisms and (2) the **`-rNN` introduction tags of ASN.1 fields** (which directly record in which release a field was added). The `-rNN` tag is not prior knowledge but a real piece of evidence embedded in the corpus.
- Additions beyond Rel-15 (FR2-1/FR2-2, `-r16`/`-r17` fields, 38.133 §9.10, etc.) are separated out in §5.

## 1. Question decomposition (case matrix)

- frequency: **intra-frequency / inter-frequency**
- reference signal: **SSB-based / CSI-RS-based**
- band: **FR1 / FR2**
- (distinction) **measurement-quantity computation** (SS-RSRP/RSRQ/SINR) vs **reading PBCH information** (SSB index / SFN)

## 2. Per-case verdict + corpus basis

verdict ∈ {needed / not needed / conditional}. Each cell is grounded only on a corpus clause or a `-rNN` tag.

| # | case | verdict | basis |
|---|---|---|---|
| A | SSB-based · **intra** · FR1/FR2 | **not needed** | TS 38.215 §5.1.1 — SS-RSRP = SSS RE power (+ optional PBCH **DM-RS**), independent of payload. SSB index from 38.213 §4.1 DM-RS sequence + `deriveSSB-IndexFromCell` (suffix-less base field = exists in Rel-15) |
| B | CSI-RS-based · **intra** · FR1/FR2 | **not needed** | TS 38.214 §5.1.6.1.3 — the timing assumption is bounded by **"with same refFreqCSI-RS"** (applies to intra). No separate acquisition of neighbor SFN required |
| C | SSB-based · **inter** · FR1 | **not needed** | TS 38.213 §4.1 — FR1 Lmax≤8 → SSB index derived from the PBCH **DM-RS sequence** (LSB), payload not required |
| D | SSB-based · **inter** · **FR2** + SSB-index (beam) reporting | **conditionally needed** | TS 38.213 §4.1 — FR2 Lmax=64 → the 3 MSB of the SSB index = **PBCH payload bits** a_{A+5..A+7}. ※ Not full MIB decode, but **acquisition of payload bits** |
| E | CSI-RS-based · **inter** · FR1/FR2 | **conditionally needed** | (a) The §5.1.6.1.3 timing assumption is for same-refFreq (intra) only → does not apply to inter. (b) **`deriveSSB-IndexFromCellInter` has the `-r17` tag** = in Rel-15 there is no inter-frequency sync bypass → the neighbor **SFN must actually be acquired**. SFN ∈ MIB (PBCH payload). (§9.10.3.5's `TCSI-RS_SFN_inter` corroborates this, but §9.10 may be post-Rel-15 → see §5 caveat) |
| — | reportCGI | (out of scope) | Not RRM measurement-quantity computation but a separate `reportCGI` procedure → MIB/SIB1 decode is outside the question scope |

### Key corpus verbatim (positive & negative)

- **(negative, measurement quantity)** TS 38.215 §5.1.1 SS-RSRP: *"... linear average over the power contributions ... of the resource elements that carry secondary synchronization signals. For SS-RSRP determination demodulation reference signals for physical broadcast channel (PBCH) and, if indicated by higher layers, CSI reference signals ... may be used."* → The measurement quantity is independent of PBCH **payload** decode (DM-RS is an optional enhancement).
- **(negative, CSI-RS intra bounding)** TS 38.214 §5.1.6.1.3: *"... the UE may assume the absolute value of the time difference between radio frame i between any two cells, listed in the configuration with the higher layer parameter CSI-RS-CellMobility and **with same refFreqCSI-RS**, is less than 153600 Ts."* → The "same refFreqCSI-RS" conditional clause **bounds this assumption to intra** → it does not apply to inter (basis for case E).
- **(positive, SSB inter FR2)** TS 38.213 §4.1: Lmax=64 → the 3 MSB of the SSB index are obtained from the PBCH **payload bits** (case D).
- **(release tag, key for case E)** corpus 38.331 ASN.1: `deriveSSB-IndexFromCellInter-r17` exists = the inter-frequency sync bypass is **new in Rel-17** → it is absent in Rel-15 → inter-frequency CSI-RS must actually acquire the SFN.

## 3. Bottom line

**In Rel-15, intra-frequency RRM measurement (both SSB and CSI-RS) is designed to be performed without decoding the neighbor PBCH.** The computation of the measurement quantity (SS-RSRP/RSRQ/SINR) itself **never** requires a full neighbor PBCH payload/MIB decode (measurement = based on SSS power). The cases that require acquiring PBCH-related information are the two inter-frequency conditions only:
- **D**: SSB-based · inter · FR2 + SSB-index reporting → the SSB index MSB are in the PBCH **payload bits** (not full MIB decode).
- **E**: CSI-RS-based · inter → acquisition of the neighbor **SFN (= MIB)** (because in Rel-15 the sync bypass `-r17` does not exist).

## 4. Evidence sources (corpus-verified)

- TS 38.215 §5.1.1 / §5.1.2 — SS-RSRP / CSI-RSRP definitions (reference signals used for measurement)
- TS 38.214 §5.1.6.1.3 — CSI-RS for mobility, timing assumption (bounded by "same refFreqCSI-RS")
- TS 38.213 §4.1 — SS/PBCH block index acquisition (FR1 Lmax≤8 DM-RS / FR2 Lmax=64 payload bits)
- TS 38.331 — `deriveSSB-IndexFromCell` (base, Rel-15) / `deriveSSB-IndexFromCellInter-r17` (Rel-17) / `CSI-RS-CellMobility{associatedSSB}` / `MIB.systemFrameNumber`

## 5. Release scope note (outside Rel-15 — do not mix in)

- `deriveSSB-IndexFromCellInter` is **`-r17`** → inter-frequency sync-derivation is a Rel-17 matter. Applying "if synchronous, SFN is not needed" to inter-frequency in a Rel-15 answer would be **release contamination (incorrect)**.
- 38.133 **§9.10** (CSI-RS L3 mobility measurement requirements) may be absent from the Rel-15 ToC → the primary basis for Case E is not §9.10.3.5 but the `-r17` tag + the §5.1.6.1.3 bounding clause. §9.10 is cited only as corroboration.
- The FR2-1/FR2-2 distinction (→ which introduces the FR2 asynchronous case) is a later release → in Rel-15, FR2 is assumed synchronous, so cases A/B are also "not needed" in FR2.
