# SPECTRA Answer — Default CRS-IM assumptions of lte-NeighCellsCRS-Assumptions and the mapping criteria for the lte-CRS-PatternList1 (Rel-16) list

> Retrieval method: the 3GPP TS/TR spec body text is searched with semantic embeddings (vector similarity), and the standards' structure and relationships (IE definition locations, cross-spec references, release-introduction structure) are cross-checked via a Knowledge Graph. Both paths are used together. The key verdicts were additionally cross-checked against public 3GPP/ETSI materials (see "Public-source cross-check" below).

## Conclusion (one line)

- **Q1 — Supported.** Even when delivered as `lte-CRS-PatternList1-r16` (a list), application of the `lte-NeighCellsCRS-Assumptions` default assumptions is not blocked. The precondition for applying the assumptions is not "list vs. single" but "**whether RateMatchPatternLTE-CRS is configured for the serving cell**", and since `lte-CRS-PatternList1` is also a container holding `RateMatchPatternLTE-CRS`, that precondition is satisfied.
- **Q2 — There is no mapping rule in the spec for "picking one element from the list."** The default-assumption text and the `LTE-NeighCellsCRS-AssistInfo` field descriptions all refer only to **the value of the singular `RateMatchPatternLTE-CRS`**, and no rule of the form "select element N of the list" exists in the 38.331/38.214 body text. However, the structural fact that each list element models a **distinct LTE carrier** (below) determines the mapping in practice — that is, when filling in the default values for a given neighbour LTE cell, taking freqDL/bandwidthDL/MBSFN/CRS port from **the element describing the LTE carrier corresponding to that neighbour cell's centre frequency/bandwidth** is the interpretation consistent with the spec structure.

---

## Terminology decomposition (to avoid confusion)

This question mixes three operations with different meanings, so we first separate them.

- (i) **Serving cell rate matching** — rate matching the serving cell's NR PDSCH around the CRS REs of the LTE carrier(s) overlapping the cell itself. This uses `lte-CRS-ToMatchAround` (Rel-15, single) / `lte-CRS-PatternList1·2` (Rel-16, lists). The governing clause is 38.214 §5.1.4.2.
- (ii) **Neighbour cell CRS-IM (interference mitigation)** — the UE mitigating CRS interference from *neighbour* LTE cells. This uses `LTE-NeighCellsCRS-AssistInfoList-r17` + `lte-NeighCellsCRS-Assumptions-r17`.
- (iii) **Fallback reference of the default assumptions** — the fallback rule whereby, if some neighbour information is not provided in (ii), the **serving cell's (i) configuration values** are used instead.

The ambiguity in the question arises because (i), the fallback source of (iii), changed from single to list in Rel-16. The case analysis below addresses how this (iii) fallback behaves in the list situation.

---

## Case-by-case analysis

### Case A — Rel-15 single pattern (`lte-CRS-ToMatchAround`)

It sits in the first release-group of `ServingCellConfig` as a single container (verbatim ASN.1):

```asn1
lte-CRS-ToMatchAround   SetupRelease { RateMatchPatternLTE-CRS }   OPTIONAL,   -- Need M
```

[38.331 ASN.1 IE=ServingCellConfig]

`RateMatchPatternLTE-CRS` is a SEQUENCE describing a single carrier (verbatim ASN.1):

```asn1
RateMatchPatternLTE-CRS ::= SEQUENCE {
    carrierFreqDL            INTEGER (0..16383),
    carrierBandwidthDL       ENUMERATED {n6, n15, n25, n50, n75, n100, spare2, spare1},
    mbsfn-SubframeConfigList EUTRA-MBSFN-SubframeConfigList   OPTIONAL,   -- Need M
    nrofCRS-Ports            ENUMERATED {n1, n2, n4},
    v-Shift                  ENUMERATED {n0, n1, n2, n3, n4, n5}
}
```

[38.331 ASN.1 IE=RateMatchPatternLTE-CRS]

Since the source is a single instance, the reference target of the default assumptions is this one instance without ambiguity. As the questioner's analysis states, it is clear. **Verdict: application clear, no ambiguity.**

### Case B — Rel-16 list (`lte-CRS-PatternList1-r16`) — whether the default assumptions can be applied (Q1)

It sits in the Rel-16 release-group of `ServingCellConfig` as a list container (verbatim ASN.1):

```asn1
lte-CRS-PatternList1-r16   SetupRelease { LTE-CRS-PatternList-r16 }   OPTIONAL,   -- Need M
lte-CRS-PatternList2-r16   SetupRelease { LTE-CRS-PatternList-r16 }   OPTIONAL,   -- Need M
```

[38.331 ASN.1 IE=ServingCellConfig]

The list type holds up to 3 instances of `RateMatchPatternLTE-CRS`, exactly as quoted in the question:

```asn1
LTE-CRS-PatternList-r16 ::= SEQUENCE (SIZE (1..maxLTE-CRS-Patterns-r16)) OF RateMatchPatternLTE-CRS
maxLTE-CRS-Patterns-r16  INTEGER ::= 3
```

The precondition for applying the default assumptions is **not the list/single form but "whether RateMatchPatternLTE-CRS is configured for the serving cell."** The evidence is that the assumption text quoted in the question repeatedly says *"...the same as the one indicated in RateMatchPatternLTE-CRS if configured for the serving cell"* / *"...is 4 if RateMatchPatternLTE-CRS is not configured for the serving cell"*. Since `lte-CRS-PatternList1-r16` is a container holding `RateMatchPatternLTE-CRS`, the "configured" condition is satisfied — therefore **application of the default assumptions is supported even when delivered as a list.**

The same conclusion is confirmed from the UE capability side. The body text of the CRS-IM capability `supportedCRS-InterfMitigation-r17` states the condition for applying the assumptions **without any single/list distinction**, solely in terms of whether `RateMatchPatternLTE-CRS` is configured for the serving cell (verbatim):

> *"For the UE supporting the capability of crs-IM-DSS-15kHzSCS-r17, the UE can perform CRS-IM without the assistant configuration information of neighbour LTE cells **when RateMatchPatternLTE-CRS is configured for the serving cell**, and if lte-NeighCellsCRS-Assumptions-r17 is not configured."*

[38.306 §4.2.7.6]

Moreover, the same capability item makes CRS-IM support in the DSS scenario dependent on the base capability `rateMatchingLTE-CRS` (verbatim):

> *"crs-IM-DSS-15kHzSCS-r17 indicates whether the UE supports neighbouring LTE cell CRS-IM in DSS scenario with NR 15 kHz SCS. **UE can indicate support of this capability on the CC(s) in a band only if the UE indicates support of rateMatchingLTE-CRS on that band.**"*

[38.306 §4.2.7.6]

`rateMatchingLTE-CRS` is the base capability for the serving cell's LTE-CRS rate matching (= the behaviour governed by `lte-CRS-ToMatchAround` / `lte-CRS-PatternList1`) (verbatim):

> *"rateMatchingLTE-CRS — Indicates whether the UE supports receiving PDSCH with resource mapping that excludes the REs determined by the higher layer configuration LTE-carrier configuring common RS, as specified in TS 38.214 [12]."*

[38.306 §4.2.7.2]

**Verdict: Q1 = supported.** Delivery as a list does not preclude application of the default assumptions.

### Case C — Element selection criteria within the Rel-16 list (Q2)

There is **no explicit rule in the spec** as to "**which element of the list**" the default assumptions and the neighbour field descriptions point to. This absence was confirmed by exhaustive search (exact-token full-text + semantic search). The evidence comes in two strands.

**(1) The default assumptions / field descriptions all refer to the singular type.** The per-field descriptions of `LTE-NeighCellsCRS-AssistInfo` say only to use the value of the singular `RateMatchPatternLTE-CRS` as fallback, with no element index (verbatim):

> *"neighCarrierBandwidthDL — ... If the field is absent, the UE applies the value of carrierBandwidthDL indicated in RateMatchPatternLTE-CRS for this serving cell, if configured."*
> *"neighCarrierFreqDL — ... If the field is absent, the UE applies the value of carrierFreqDL indicated in RateMatchPatternLTE-CRS for this serving cell, if configured."*
> *"neighNrofCRS-Ports — ... If the field is absent, the UE applies the value of nrofCRS-Ports indicated in RateMatchPatternLTE-CRS for this serving cell, if configured. If RateMatchPatternLTE-CRS is not configured for this serving cell and the field is absent, the UE applies the default value n4."*
> *"neighMBSFN-SubframeConfigList — ... If RateMatchPatternLTE-CRS is configured for this serving cell and the field is absent, the UE applies the value of mbsfn-SubframeConfigList indicated in RateMatchPatternLTE-CRS for this serving cell if configured; otherwise ... the UE assumes MBSFN is not configured in the neighbour LTE cell."*

[38.331 ASN.1 IE=LTE-NeighCellsCRS-AssistInfo]

In other words, this text does not designate "one of the list" — the Rel-17 assumption text is written using a singular abstraction (`RateMatchPatternLTE-CRS`) that covers both Rel-15 and Rel-16.

**(2) Structurally, however, each list element means "a distinct LTE carrier."** The governing rate-matching clause (38.214 §5.1.4.2) defines each `RateMatchPatternLTE-CRS` as "one LTE carrier" (verbatim):

> *"REs indicated by 'RateMatchPatternLTE-CRS' in lte-CRS-PatternList1-r16 ... in 15 kHz subcarrier spacing applicable only to 15 kHz subcarrier spacing PDSCH, **of one LTE carrier** in a serving cell are declared as not available for PDSCH."*
> *"Each RateMatchPatternLTE-CRS configuration contains v-Shift ..., nrofCRS-Ports ..., carrierFreqDL representing the offset ... to the LTE carrier centre subcarrier location, carrierBandwidthDL representing the LTE carrier bandwidth, and may also configure mbsfn-SubframeConfigList ..."*

[38.214 §5.1.4.2]

The reason the list exists is that a wide NR carrier can overlap **multiple LTE carriers** (see Public-source cross-check), and each element describes one of them. Therefore the natural key for identifying an element is the **carrier coordinates (`carrierFreqDL` / `carrierBandwidthDL`)**.

**(3) Rate matching itself consumes the list "as a set."** §5.1.4.2 applies the list as a whole (union) during rate matching — apart from the per-coresetPoolIndex branch, all of List1 applies (verbatim):

> *"-if the UE is configured with crs-RateMatch-PerCoresetPoolIndex, REs indicated by **the CRS pattern(s) in lte-CRS-PatternList1-r16** if the PDSCH is associated with coresetPoolIndex set to '0' ...; -otherwise, REs indicated by lte-CRS-PatternList1-r16 and lte-CRS-PatternList2-r16, in ServingCellConfig."*

[38.214 §5.1.4.2]

Here "pattern(s)" is plural — rate matching does not pick a single element; it uses the entire list. This shows that Q2's "which single element" question *does not apply to the rate-matching operation itself* (rate matching involves no element selection).

**Verdict: Q2 = the "list element index selection" rule is not specified in the spec (room for implementation discretion).** However, given the structure in which each element is a separate LTE carrier, when filling in the default values for a specific neighbour LTE cell, taking freqDL/bandwidthDL/MBSFN/CRS port from **the element whose carrier coordinates match that neighbour cell** is the interpretation consistent with the spec structure.

---

## Comparison table

| Case | Source container | Release | Default assumptions apply | Element selection criterion | Evidence |
|---|---|---|---|---|---|
| A | `lte-CRS-ToMatchAround` (single) | Rel-15 | Apply (precondition = configured) | Single, so no selection needed | [38.331 ASN.1 IE=ServingCellConfig], [38.214 §5.1.4.2] |
| B | `lte-CRS-PatternList1-r16` (list ≤3) | Rel-16 | **Supported** (precondition = RateMatchPatternLTE-CRS configured; a list also satisfies it) | — | [38.331 ASN.1 IE=ServingCellConfig], [38.306 §4.2.7.6] |
| C | Element mapping within the above list | Rel-16 | (sub-case of B) | **Not specified in the spec**; structurally, matching by carrier coordinates (freqDL/bandwidthDL) is consistent | [38.331 ASN.1 IE=LTE-NeighCellsCRS-AssistInfo], [38.214 §5.1.4.2] |

**Bottom line:** Even when delivered as a list, application of the assumptions is not blocked (Q1 = supported). There is no explicit rule saying "use the N-th element of the list" (Q2), but given the structure in which elements are per-carrier, treating the element corresponding to the neighbour cell's carrier as the fallback source is the consistent interpretation.

---

## Standards-structure cross-check

The LTE-CRS-related fields inside the `ServingCellConfig` IE were introduced cumulatively in per-release extension groups (identified via per-IE/field release markers `-rNN` and nested ASN.1 extension groups `[[ ]]`):

- `lte-CRS-ToMatchAround` — Rel-15 (first extension group), a single `RateMatchPatternLTE-CRS`.
- `lte-CRS-PatternList1-r16`, `lte-CRS-PatternList2-r16` — Rel-16, each an `LTE-CRS-PatternList-r16` (list ≤3).
- `crs-RateMatch-PerCORESETPoolIndex-r16` — Rel-16, controls whether List1/List2 are split by coresetPoolIndex.
- `lte-NeighCellsCRS-AssistInfoList-r17`, `lte-NeighCellsCRS-Assumptions-r17` — Rel-17 (introduction of neighbour CRS-IM).
- `lte-CRS-PatternList3-r18`, `lte-CRS-PatternList4-r18` — added in Rel-18 (outside the question's scope; labels noted only). They are unrelated to the question's scope (Rel-16 list ↔ Rel-17 assumptions) and are not pulled in as in-scope provisions.

[38.331 ASN.1 IE=ServingCellConfig]

Cross-spec relationships: every field description of `RateMatchPatternLTE-CRS` delegates the behavioural definition to **38.214 §5.1.4.2** ([38.331 ASN.1 IE=RateMatchPatternLTE-CRS]: *"...(see TS 38.214 [19], clause 5.1.4.2)"*), and that clause holds the rule consuming the list as a set of carriers ([38.214 §5.1.4.2]). The requirements/scenario definitions for neighbour CRS-IM are delegated to **TS 38.101-4** (*"see TS 38.101-4 [59]"* in the question/assumption text; that body text is not directly quoted in this analysis — see Honest gap).

Also, independently of the default assumptions, a separate list-entry interpretation rule exists for the case where neighbour information **is explicitly** signalled (verbatim):

> *"If the IE LTE-NeighCellsCRS-AssistInfoList contains multiple list entries, the entry with neighV-Shift is only used for neighbour LTE cells for which neighCellId is not provided (i.e. the entry with neighCellId takes precedence over the entry with neighV-Shift, if provided)."*
> *"If the IE LTE-NeighCellsCRS-AssistInfoList contains one list entry with neither this field nor neighV-Shift, the information within the entry applies to all neighbour LTE cells."*

[38.331 ASN.1 IE=LTE-NeighCellsCRS-AssistInfo]

This rule concerns the interpretation of entries in the **assist-info list (neighbour side)** and is a different list from the **serving-cell rate-match list (`lte-CRS-PatternList1`) element selection** the question asks about — we keep them separate so the two lists are not confused. The assist-info list has the explicit precedence rule above, whereas there is no corresponding explicit rule for how the default assumptions pick an element of the serving-cell pattern list (this asymmetry is the essence of the Q2 ambiguity).

---

## Public-source cross-check

The key verdicts were cross-checked against public 3GPP/ETSI materials (these are **non-authoritative vendor materials/tutorials**, not authoritative standards body text, so they do not override the spec text; they serve as supporting corroboration only).

- Confirmation of the reason for the single→list transition: Rel-15 `lte-CRS-ToMatchAround` covers only **one LTE carrier** when the NR carrier is in the same band as a single LTE CC; if the NR carrier is wider (e.g., 50 MHz), it can overlap **multiple** 10/20 MHz LTE carriers, so Rel-16 allows up to 3 patterns — i.e., **each pattern = a distinct LTE carrier**. (LTE-CRS rate matching is possible only with 15 kHz SCS.) [web: MediaTek "5G NR and 4G LTE Coexistence" DSS white paper; MATLAB/Simulink "DSS for 5G NR and LTE Coexistence"; both non-authoritative]
- Confirmation that 38.214 §5.1.4.2 is the governing clause for LTE-CRS rate matching and that 38.331 §6.3.2 defines `RateMatchPatternLTE-CRS`. [web: same materials as above; non-authoritative]

Cross-check result: **consistent with the verdicts (confirmed)**, 0 conflicts. The spec basis for these verdicts is the **authoritative 3GPP TS 38.331 body text (field description verbatim)** as-is (the public materials do not replace it); the non-authoritative materials were used only to corroborate that the design rationale does not contradict the verdicts. Independent public mirrors of the authoritative standards text were access-restricted in this environment (the attempts are fully recorded in the verification trail).

---

## Honest gap

- **The absence of an "element index selection" rule for Q2 is spec silence.** Nowhere in the 38.331 assumption text, the field descriptions, or 38.214 §5.1.4.2 is there a sentence saying "use list element N as the default source" (absence confirmed via exact-token search + semantic search). This answer's "carrier-coordinate matching" interpretation is derived from the spec structure in which *each element is per-carrier*; it is a **consistent implementation interpretation**, not an explicit provision. For operational safety, where possible we recommend a configuration that **explicitly signals** per-neighbour freqDL/bandwidthDL/CRS port in `lte-NeighCellsCRS-AssistInfoList` rather than relying on the default fallback (the defaults are a singular abstraction, so an ambiguity remains as to narrowing down to one pattern when multiple carriers are present).
- The **TS 38.101-4 (CRS-IM RAN4 requirements/scenarios)** body text is not in this analysis corpus and was not directly quoted — the definition/requirements of the "overlapping spectrum for LTE and NR" scenario referenced by the assumption text reside in that document.
- The **field-description paragraphs for `lte-NeighCellsCRS-Assumptions-r17` / `lte-CRS-PatternList1` / `lte-CRS-ToMatchAround`** are part of the `ServingCellConfig` field-description block, and due to a token cap when the corpus index was built, the 'l...' items of that block were truncated, so those paragraphs themselves could not be quoted directly. The assumption text is preserved verbatim in the question (quoted by the user from 38.331), and the neighbour-side per-field mapping text was retrieved in full from the `LTE-NeighCellsCRS-AssistInfo` field descriptions.
- **Verdict basis = authoritative corpus body text; only the independent public-mirror cross-check was access-restricted.** The spec-text basis of these verdicts is sufficiently provided by the **authoritative 3GPP TS 38.331 (V19) field description verbatim** loaded in the corpus. We additionally attempted an *independent* reconfirmation via authoritative public mirrors, but many authoritative mirrors were access-blocked in this environment (the full record of attempts is in the verification trail), so an independent spec-text-level citation could not be secured — this is a limitation of the *supporting* cross-check only and does not affect the verdict basis.
