# SPECTRA Answer — Basis for Deriving the PCell (E-UTRA) Type1 PH When Transmitting Real PHR in EN-DC

> Retrieval approach: semantic embedding search over the 3GPP TS spec body (vector similarity) + cross-verification against the standards structure. Because this is EN-DC, the PCell (E-UTRA) is cross-spec to LTE, so the NR (38.321) corpus body is supplemented by authoritative public LTE references. The core is cross-confirmed with public materials.

## Conclusion

**Yes (conditionally).** When `phr-ModeOtherCG = real` and the **other (LTE) MAC entity has UL resources allocated on the relevant Serving Cell (PCell) and an actual transmission occurs**, the NR MAC **obtains** that PCell's `PCMAX,f,c` **from the physical layer**, and the PCell Type1 PH becomes the **real PH based on LTE's actual PUSCH transmission**. Since the PCell is E-UTRA, the formula for the PH value itself follows LTE (TS 36.213). Conversely, if that condition is not met (no UL grant on the relevant cell, or the real condition does not hold), it is a **virtual PH (based on the reference format)**.

In other words, the questioner's understanding ("use real PH based on LTE's most recently transmitted PUSCH") is **correct when the real condition holds.**

## Basis

- **[TS 38.321 §5.4.6 (PHR procedure)]** verbatim: *"if this MAC entity has UL resources allocated for transmission on this Serving Cell; or if the other MAC entity, if configured, has UL resources allocated for transmission on this Serving Cell and phr-ModeOtherCG is set to real by upper layers: obtain the value for the corresponding PCMAX,f,c field from the physical layer."* → **Obtaining PCMAX from the PHY = based on actual transmission (real)**. Otherwise (else), it is computed with the reference/assumed format = virtual.
- **[TS 38.321 §6.1.3.9 Multiple Entry PHR MAC CE]**: contains the bitmap + (the other MAC entity's SpCell) Type 2 PH + each Serving Cell's **Type 1 PH field and the associated PCMAX,f,c octet** (including PCell). That is, the PCell Type1 PH is reported carried in this NR Multiple Entry PHR.
- **PCell = E-UTRA → the Type1 PH formula is LTE**: `[web: TS 36.213 §5.1.1.2]` *"PHtype1,c(i) = PCMAX,c(i) − P̂calc_PUSCH,c(i)"* (the value of PCMAX minus the computed PUSCH transmission power). If real, the `PCMAX,c(i)` of the actual transmission subframe and the actual PUSCH power are used.

## Refinement Regarding "Most Recently Transmitted PUSCH"

The real PH is derived based on the actual transmission when an **actual UL transmission (PUSCH) exists** on the relevant Serving Cell at the time of reporting. Since the two MAC entities (LTE/NR) are asynchronous in EN-DC, the exact value and timing reference of the LTE PCell PH carried in the NR PHR are governed by the **LTE procedures (36.213/36.321)**. Therefore, the interpretation "real PH based on LTE's most recently transmitted PUSCH" is valid as long as the real condition (other MAC entity UL resource allocation + phr-ModeOtherCG=real) is met.

## Standards Structure Cross-Verification

- NR side: `phr-ModeOtherCG` (real/virtual) configuration → the real/virtual branching in 38.321 §5.4.6 → the PCell Type1 PH + PCMAX,f,c octet of the §6.1.3.9 Multiple Entry PHR MAC CE. (Variant MAC CEs such as FR2/twoPHRMode follow the same structure.)
- LTE side: PCell (E-UTRA) Type1 PH formula = 36.213; real/virtual is distinguished as actual vs reference in the reporting format.

## Cross-Confirmation (External Public Materials)

- Consistent with public materials: Type1 PH (36.213) = PCMAX,c − Pcalc_PUSCH,c; in EN-DC, MN = LTE (PCell) / SN = NR; PHR distinguishes actual (real) vs reference (virtual) (V field). This is consistent with the present determination, with 0 conflicts. The primary basis = the corpus 38.321 §5.4.6/§6.1.3.9 verbatim; the LTE formula is supplemented by the authoritative public reference (36.213).

## Honest Gap

- **The governing specs for the PCell PH formula and the exact timing reference are LTE TS 36.213/36.321**, which are outside the ingestion scope of this NR corpus (38.xxx), so they were supplemented with authoritative public references (`[web:]`). The NR-side procedures (real/virtual condition, MAC CE format) are grounded with corpus verbatim.
- The details of the `P̂calc_PUSCH` calculation (MPR/A-MPR, etc.) depend on 36.213/36.101 — confirm against the LTE spec of the applicable release.
