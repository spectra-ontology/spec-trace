# SPECTRA Answer — UCI bit mapping order when subband PMI + Layer Indicator are configured in CSI part 2

> Question source: internal engineering board (anonymized).

---

## Conclusion (summary)

1. **The Layer Indicator (LI) is mapped in the CSI part 2 "wideband" segment (Table 6.3.2.1.2-4) even in the subband PMI configuration.** The LI row and the PMI wideband information (i1) row of Table 6.3.2.1.2-4 do not carry a pmi-FormatIndicator condition, and only the **wideband PMI (i2) row** carries the "if pmi-FormatIndicator = widebandPMI" condition. That is, even when configured as subbandPMI, Table -4 still applies, and within it the mapping proceeds in the order **Wideband CQI (2nd TB) → LI → PMI wideband information (i1)**, skipping only the wideband i2 row.
2. **The absence of an LI row in Table 6.3.2.1.2-5 is not an omission.** Since LI is a wideband quantity (one per reporting unit), its mapping is already completed in the part 2 wideband segment, and Table -5 (part 2 subband) only contains quantities that repeat per subband (subband differential CQI, PMI subband i2), in the order even subbands → odd subbands.
3. **The full part 2 order of a single report** is therefore: `[part 2 wideband: WB CQI (2nd TB) → LI → i1]` → `[part 2 subband: SB CQI of even subbands → i2 of even subbands → SB CQI of odd subbands → i2 of odd subbands]`. When multiple CSI reports are multiplexed, **the part 2 wideband of all reports comes first** (in report-number order), followed by **the part 2 subband of all reports** (in report-number order) (Table 6.3.2.1.2-7).

## 1. Table 6.3.2.1.2-4 is not a wideband-PMI-only table

In the question this was understood as "Table 6.3.2.1.2-4 is the order in the wideband PMI [case]", but looking at the per-row conditional statements of the table, this table is **the table of the part 2 "wideband segment"**, not a "wideband-PMI-configuration-only" table. The base rows of Table 6.3.2.1.2-4 of the current TS 38.212 §6.3.2.1.2 (subscript fields are supplemented with [ ] where the font was lost during body extraction):

> "CSI report #n CSI part 2 wideband |
> Wideband CQI for the second TB as in Tables 6.3.1.1.2-3/3C/4/5, **if present and reported**
> Layer Indicator as in Tables 6.3.1.1.2-3/3C/4/5, **if reported**
> PMI wideband information fields [i1], from left to right as in Tables 6.3.1.1.2-1/1A/1B/2/2A or 6.3.2.1.2-1/2, **if reported**
> PMI wideband information fields [i2], from left to right as in Tables 6.3.1.1.2-1/1A/1B/2/2A or 6.3.2.1.2-1/2, or codebook index for 2 antenna ports according to Clause 5.2.2.2.1 in [6, TS38.214], **if pmi-FormatIndicator = widebandPMI and if reported**"

The key point is that the conditional statement differs per row:

| Table -4 row | Applicable condition | When subbandPMI is configured |
|---|---|---|
| Wideband CQI (2nd TB) | if present and reported | Applies |
| **Layer Indicator** | **if reported** (independent of PMI format) | **Applies** |
| PMI wideband information [i1] | if reported (independent of PMI format) | Applies — i1 is a wideband quantity even in subbandPMI |
| PMI wideband information [i2] | if pmi-FormatIndicator = **widebandPMI** | Skipped (i2 goes to Table -5) |

That is, in the subband PMI configuration, the "LI → PMI order" you asked about **is kept as the LI → i1 order within the part 2 wideband segment**, and only the per-subband component of the PMI (i2) moves to the part 2 subband segment.

## 2. Why there is no LI in Table 6.3.2.1.2-5 — LI is a wideband quantity

The base rows of Table 6.3.2.1.2-5 of the same clause:

> "CSI report #n Part 2 subband |
> Subband differential CQI for the second TB of **all even subbands** with increasing order of subband number, as in Tables 6.3.1.1.2-3/3C/4/5, if cqi-FormatIndicator=subbandCQI and if reported
> PMI subband information fields [i2] of **all even subbands** with increasing order of subband number, from left to right ..., **if pmi-FormatIndicator = subbandPMI** and if reported
> Subband differential CQI for the second TB of **all odd subbands** ..., if cqi-FormatIndicator=subbandCQI and if reported
> PMI subband information fields [i2] of **all odd subbands** ..., if pmi-FormatIndicator = subbandPMI and if reported"

All the rows of this table are "of all even/odd subbands with increasing order of subband number" — that is, they contain only **quantities that repeat along the subband index**. Since LI is a wideband quantity that is reported only once per report (this is expressed by the fact that the LI row of Table -4 always applies without a PMI format condition), it has no place in this table, and this is **not a mapping-order undefined case but rather mapping already completed in the part 2 wideband segment**.

## 3. Segment combination order — Table 6.3.2.1.2-7

The body of §6.3.2.1.2 specifies the generation of the part 2 bit sequence as follows:

> "The CSI fields of all CSI reports, in the order from upper part to lower part in Table 6.3.2.1.2-7, are mapped to the UCI bit sequence..."

And the body of Table 6.3.2.1.2-7:

> "CSI report #1, CSI part 2 wideband, as in Table 6.3.2.1.2-4/4A/4B/4C, ... if CSI part 2 exists for CSI report #1
> CSI report #2, CSI part 2 wideband, ...
> …
> CSI report #n, CSI part 2 wideband, ...
> CSI report #1, CSI part 2 subband, as in Table 6.3.2.1.2-5/5C/5D/5H/5I, ... if CSI part 2 exists for CSI report #1
> CSI report #2, CSI part 2 subband, ...
> …
> CSI report #n, CSI part 2 subband, ..."

That is, **the part 2 wideband segments (Table -4 family) of all reports come first in report-number order**, followed by **the part 2 subband segments (Table -5 family) of all reports in report-number order**. The PUCCH side (§6.3.1.1.2, Table 6.3.1.1.2-14) has the same wideband-first structure.

## 4. Overall — bit order of the question scenario (subband PMI + LI)

Assuming a single CSI report, cqi-FormatIndicator=subbandCQI, pmi-FormatIndicator=subbandPMI, with LI included in reportQuantity:

```
CSI part 2 bit sequence
├─ [part 2 wideband, Table 6.3.2.1.2-4]
│   1. Wideband CQI for 2nd TB   (when present, e.g. rank>4)
│   2. Layer Indicator           ← the LI position you asked about
│   3. PMI wideband information [i1]
│   (the wideband i2 row is skipped since it is conditioned on widebandPMI)
└─ [part 2 subband, Table 6.3.2.1.2-5]
    4. even subbands: SB differential CQI (2nd TB) → PMI subband [i2]  (increasing subband number)
    5. odd subbands:  SB differential CQI (2nd TB) → PMI subband [i2]  (increasing subband number)
```

When multiple reports are multiplexed, the ├ segments above come first for all reports, and the └ segments follow afterwards (§3).

## Verification scope and limitations

- Scope of cross-checking: the full text of TS 38.212 §6.3.2.1.2 (mapping of CSI part 1/2 for UCI on PUSCH) — the base-form rows and conditional statements of Table 6.3.2.1.2-4, the base-form rows and conditional statements of Table 6.3.2.1.2-5, the body for the combination order of Table 6.3.2.1.2-7, and the parallel table of §6.3.1.1.2 (UCI on PUCCH) (Table 6.3.1.1.2-14) were verified row by row. The absence of an LI row in the Table -5 family (base form + variants) was confirmed across the entire scope of the clause body. In cross-checking against external public material (CSI ordering descriptions in patent literature, public transcripts), the structure "part 2 wideband of all reports first → part 2 subband" and the inclusion of LI within part 2 wideband were consistent.
- The citations are based on the body of the **currently loaded version**. The subscript fields inside the tables (the detailed indices of i1/i2, e.g. x1,1, x1,2 …) were supplemented with [ ] notation because the font was lost during body extraction, and for the per-field left→right order within i1/i2 (e.g. i1,1 → i1,2 → …) only the specification that it follows the column order of the reference tables (the Tables 6.3.1.1.2-1 family) was confirmed; those tables themselves are not developed in this answer.
- The variant tables of Table -4/-5 (4A/4B/4C, 5A~5J — for special codebooks such as CJT, NCJT, TDCP) were checked only for the purpose of confirming the combination order, and were not developed row by row. The question scenario (general Type I/II single-panel reporting) is covered by the base-form tables.
- The priority rules for the case where part 2 is omitted (omission) due to PUSCH resource constraints (TS 38.214 §5.2.3, in units of Priority) are outside the scope of the question and are not developed here — even in the case of omission, the mapping order itself is the same as in this answer.
