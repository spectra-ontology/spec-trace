# SPECTRA Answer — DCI format 0_1 bit size calculation for the Rel-18 DCI-based waveform switch

> Retrieval method: 3GPP TS spec body text searched via semantic embeddings (vector similarity) and cross-verified against the standards structure in the knowledge graph. Since this question concerns both field composition and the rationale for its introduction, **the related Change Request (CR) / contribution (TDoc) partitions were also searched**. The key verdict was cross-checked against publicly available material.

## Conclusion (Q1)

If `dynamicTransformPrecoderFieldPresenceDCI-0-1-r18 = enabled`, the bit size calculation of DCI format 0_1 reflects the following:

1. **A 1-bit `Transform precoder indicator` field is added to DCI 0_1** (for DCI 0_1 monitored with C-RNTI / CS-RNTI / MCS-C-RNTI).
2. At the same time, **the fields whose widths differ between transform precoder enabled vs disabled** (Precoding information and number of layers, Antenna ports, PTRS-DMRS association, Second precoding information, etc.) are **aligned to a fixed width that covers both cases**, so that **the overall size of DCI 0_1 does not change** regardless of which waveform is actually indicated dynamically.
3. To the DCI 0_1 size computed this way, the standard **DCI 0_0/0_1 size alignment** (38.212 §7.3.1.0 / §7.3.1.1) is applied (padding/truncation to match the sizes of 0_0 and 0_1).

In other words, it is not "enabled, so just add 1 bit" — the calculation proceeds as **1 bit added (transform precoder indicator) + fixed-width alignment of the variable-width fields → then 0_0/0_1 alignment**.

## Detailed grounding (corpus verbatim, TS 38.212 §7.3.1.1.2)

- **Field size**: *"Transform precoder indicator – 0 or 1 bit"*, and *"– 1 bit if the higher layer parameter dynamicTransformPrecoderFieldPresenceDCI-0-1 is configured to 'enabled' and if the UE is configured to monitor DCI format 0_1 with CRC scrambled by C-RNTI or CS-RNTI or MCS-C-RNTI"* → under the enabled condition this field = **1 bit** (otherwise 0 bits).
- **Alignment trigger for variable-width fields**: *"Transform precoder indicator field is present, if the bit width of the Precoding information and number of layers field for the case with transform precoder enabled is not equal to that for the case with transform precoder disabled"* — the same wording also applies to the **Antenna ports**, **PTRS-DMRS association**, and **Second precoding information** fields. That is, when any field differs in width between the two waveforms, the indicator is present, and those fields are determined to a single size independent of the dynamic indication.
- Related fields (e.g., DMRS sequence initialization) are likewise tied to the presence of the indicator, in the form *"1 bit if transform precoder is disabled by higher layers or if the Transform precoder indicator field is present"*.

## Background of introduction (supporting — CR/TDoc)

- [CR CR0165 for 38.212] *"Reason for change: Capture the endorsed text proposals on DCI format 0_1 and DCI format 0_2 ... Summary of change: Update the Transform precoder indicator field in DCI format 0_1 and DCI format 0_2 per the text proposal in R1-2310499"* (RAN1#114bis). → This field was introduced by the **dynamic waveform switching (DFT-s-OFDM ↔ CP-OFDM)** WI within Rel-18 coverage enhancement.

## Standards-structure cross-verification

- RRC: the Rel-18 field `dynamicTransformPrecoderFieldPresenceDCI-0-1-r18` (enabled) in `PUSCH-Config` → determines the presence of the `Transform precoder indicator` field in PHY DCI 0_1. The PHY field size/alignment rules are 38.212 §7.3.1.1.2 + §7.3.1.0.

## Cross-check (external public material)

- The introduction of explicit DCI signaling for Rel-18 dynamic waveform switching (DWS) is consistent with the RAN1 coverage enhancement WI contributions/agreements (multiple company contributions proposed "a 1-bit DCI indication or reuse of a legacy field"). The primary grounding is the 38.212 §7.3.1.1.2 body text in the corpus + CR0165; the public search serves only as supporting context (non-authoritative contributions are not used as grounds for the verdict).

## Honest gap

- The **exact bit counts** of the variable-width fields (Precoding information / Antenna ports / PTRS-DMRS association) depend on the codebook type, maxRank, number of antenna ports, and the RRC config, so they must be finalized with the applicable config. This answer grounds the *calculation procedure* (indicator 1 bit + fixed-width alignment of variable-width fields + 0_0/0_1 alignment) and the 1-bit condition of the indicator field in the 38.212 body text.
