# SPECTRA answer — Interpretation of the P field of the PHR MAC CE (the power management indication when mpe-Reporting-FR2 is not configured / on FR1, and the factors that vary PCMAX,f,c)

> Retrieval method: Using semantic search over the standard body text, the 38.321 PHR MAC CE definition was obtained verbatim, and cross-WG the PCMAX,f,c computation formula (38.101-1/-2) and MPE reporting (38.133) were retrieved together; the IE structure (including release markers) was then cross-validated against the knowledge graph. Externally published material was used only as a supplementary cross-check, and the standard body text is the final authority.

---

## Conclusion (one-line bottom-line + caveat)

- **(a) and (b) are not two independent conditions joined by OR.** (a) is a **semantic definition** explaining "*what* the P field *indicates*" (whether power backoff due to power management is applied), and (b) is the **single set rule** that precisely specifies **when to set P=1** for that meaning. In other words, the same single mechanism is expanded as "indication meaning (a) → operation rule (b)," and the criterion for judging P=1 is (b) alone.
- **The core of (b) is that it looks in isolation at whether PCMAX,f,c changed because of power management (P-MPRc).** Even if PCMAX,f,c changes due to other factors (MPR/A-MPR/ΔTC, etc.), that is not the subject of (b)'s judgment — because (b) asks only "would PCMAX,f,c have had a different value *assuming there had been no backoff* due to power management."
- **PCMAX,f,c changes due to several factors besides power management (P-MPRc)** (MPR, A-MPR, ΔTIB,c, ΔTC,c, ΔTRxSRS, ΔPPowerClass, variations in PEMAX,c, etc.) — the PCMAX computation formula in 38.101-1/-2 §6.2.4 makes this explicit. However, **those variations do not set the P field to 1.** The P field is a flag that points only to the *power management component (P-MPRc)*, not to the *total amount* of PCMAX variation.

---

## Term breakdown (starting from the core of the confusion)

The difficulty of the question arises because three different things appear mixed within a single sentence. Let us separate them first.

- **(i) "What the P field indicates"** — the *meaning* of the P field. Part (a) of 38.321 defines this.
- **(ii) "The condition for setting P=1"** — the *operation rule* of the MAC entity. Part (b) specifies this.
- **(iii) "The factors that change PCMAX,f,c"** — the variation of the *resulting value* of the power computation. This is determined not by 38.321 (MAC) but by **the PCMAX computation formula of 38.101-1/-2 (RAN4)**.

The P field definition sentence joins (i) and (ii) in one paragraph, and the second part of the question ("examples of PCMAX changing other than power backoff") falls in domain (iii) — i.e., the answer comes from another spec (RAN4).

---

## Case-by-case analysis

### Case 1 — The logical relationship of (a) and (b): is it OR?

The P field definition of the 38.321 Single Entry PHR MAC CE (identical to the question's original text):

> *If mpe-Reporting-FR2 is configured and the Serving Cell operates on FR2, the MAC entity shall set this field to 0 if the applied P-MPR value, to meet MPE requirements, as specified in TS 38.101-2 [15], is less than P-MPR_00 as specified in TS 38.133 [11] and to 1 otherwise. If mpe-Reporting-FR2 is not configured or the Serving Cell operates on FR1, this field indicates whether power backoff is applied due to power management (as allowed by P-MPRc as specified in TS 38.101-1 [14], TS 38.101-2 [15], and TS 38.101-3 [16]). The MAC entity shall set the P field to 1 if the corresponding PCMAX,f,c field would have had a different value if no power backoff due to power management had been applied;*

Looking at the sentence structure:

- First sentence "this field **indicates whether** power backoff is applied due to power management ..." — the verb is *indicates*. This is a statement explaining **what meaning this bit holds**, not a **set command** of the form "if this condition, then 1."
- Second sentence (the last sentence of the full quote above, *"The MAC entity shall set the P field to 1 if the corresponding PCMAX,f,c field would have had a different value if no power backoff due to power management had been applied"*) — the verb is *shall set*. This is the **only normative sentence that mandates actual behavior**.

Therefore (a) is a semantic declaration (declarative) and (b) is the operation rule (normative), and the two sentences are not in an OR relationship of "if either one is true." **The determination of P=1 is made by (b) alone.** (a) is *interpretation guidance* meaning "and so this bit denotes whether there was power management backoff."

Intuitively: "This bit indicates *whether backoff was applied due to power management* (=a). That judgment is made by *whether PCMAX,f,c would have differed assuming there had been no power management backoff* (=b)." (b) is (a) defined in a measurable form.

**Case 1 verdict: Not OR. (a)=meaning, (b)=the only set rule.**

### Case 2 — In (b), does PCMAX,f,c changing due to "factors other than power backoff" cause P=1?

(b) is designed with a very narrow conditional clause:

> *... if the corresponding PCMAX,f,c field would have had a different value **if no power backoff due to power management had been applied**;*

Here the comparison is between "the actual PCMAX,f,c" and "a hypothetical PCMAX,f,c with **only the power management backoff removed**." If the two values differ → power management actually pulled PCMAX,f,c down → P=1. If the two values are equal → power management had no effect on the determination of PCMAX,f,c → P=0.

The key is that **other factors (MPR/A-MPR/ΔTC, etc.) remain unchanged in the hypothetical value as well.** Since (b) removes *only the single power management component* before comparing, even if MPR or A-MPR changed PCMAX,f,c, that change is reflected *identically* in the actual value and the hypothetical value and thus cancels out. In other words, **PCMAX variation due to factors other than power management does not set the P field to 1.**

Therefore the question's "example of the PCMAX,c value changing other than power backoff in 1-b" should be viewed *separately from the determination of the P field*. It is true that PCMAX,f,c changes due to other factors (see Case 3), but that is not what the P field points to. The P field, throughout, is a flag that indicates **the presence or absence of the power management (P-MPRc) component**.

**Case 2 verdict: PCMAX variation due to factors other than power management does not trigger P=1 (because (b)'s comparison structure isolates that component alone).**

### Case 3 — The actual factors by which PCMAX,f,c changes other than power management (cross-WG: RAN4 computation formula)

The value of PCMAX,f,c is determined not by MAC (38.321) but by the computation formula of **38.101-1 §6.2.4 (Configured transmitted power)**:

> *PCMAX_L,f,c = MIN {PEMAX,c – ∆TC,c, (PPowerClass – ΔPPowerClass + ΔPPowerBoost) – MAX(MAX(MPRc+∆MPRc, A-MPRc) + ΔTIB,c + ∆TC,c + ∆TRxSRS, P-MPRc)}*
> *PCMAX_H,f,c = MIN {PEMAX,c, PPowerClass – ΔPPowerClass + ΔPPowerBoost}*

In this formula, PCMAX,f,c changes **in addition to P-MPRc (=power management)** due to the following terms:

- **MPRc + ∆MPRc** (Maximum Power Reduction) — backoff depending on the modulation scheme and the position/number of allocated RBs. It can change every slot if scheduling changes.
- **A-MPRc** (Additional MPR) — additional backoff depending on the NS value signaled by the network (spurious/coexistence requirements for specific bands).
- **ΔTIB,c** (intra-band CA tolerance), **∆TC,c** (band-edge tolerance).
- **∆TRxSRS** — additional backoff applied during the SRS antenna switching transmission interval.
- **ΔPPowerClass** — power class adjustment (varies due to, e.g., PC2/PC1.5, the SUL default power class, uplink duty cycle/P-max conditions, pi/2 BPSK power boost, etc.). The 38.321 Single Entry PHR MAC CE even defines a dedicated **DPC field** (ΔPPowerClass) for reporting this component separately, making it an independent factor of PCMAX variation.
- **PEMAX,c** — the upper bound given by the p-Max IE or the additionalPmax of NR-NS-PmaxList. If it changes via RRC reconfiguration, PCMAX also changes.

The structure is the same for FR2. **38.101-2 §6.2.4** places the same factors (MPR, A-MPR, ΔMBP,n, P-MPR, tolerance) into the PCMAX range on an EIRP basis:

> *PPowerclass + DPIBE – MAX(MAX(MPRf,c, A-MPRf,c) + ΔMBP,n, P-MPRf,c) – MAX{T(MAX(MPRf,c, A-MPRf,c)), T(P-MPRf,c)} ≤ PUMAX,f,c ≤ EIRPmax*

In other words, **the answer to "examples of PCMAX,f,c changing other than power backoff (power management)" is: MPR (modulation/RB allocation change), A-MPR (NS signaling), ΔPPowerClass (power class/duty cycle adjustment), ∆TC/ΔTIB (band tolerances), ∆TRxSRS (SRS antenna switching), PEMAX change (p-Max reconfiguration)**, and so on. All are regular factors explicitly specified in the standard computation formula.

However, to re-emphasize — even if PCMAX changes due to these factors, **the P field remains 0** (Case 2). Although they can *trigger* a PHR (see cross-validation below), they are not what the P field points to.

**Case 3 verdict: PCMAX,f,c varies due to numerous factors other than power management (MPR/A-MPR/ΔPPowerClass/ΔTC/ΔTRxSRS/PEMAX). Basis = the 38.101-1/-2 §6.2.4 computation formula.**

---

## Comparison table

| Category | What it is | Does it cause P=1 | Basis spec § |
|---|---|---|---|
| (a) "indicates whether power backoff ..." | The **semantic definition** of the P field (descriptive) | (not a direct set rule) | 38.321 §6.1.3.8 |
| (b) "shall set ... if PCMAX would have had a different value if no power backoff due to power management had been applied" | The **only set rule** (normative) | Yes — only when the power management component changed PCMAX | 38.321 §6.1.3.8 |
| PCMAX variation due to factors other than power management (MPR/A-MPR/ΔPPowerClass/ΔTC/ΔTRxSRS/PEMAX) | Regular terms of the PCMAX computation | **No** (canceled out in (b)'s comparison) | 38.101-1/-2 §6.2.4 |

**Bottom-line:** (a)/(b) are a "meaning → rule" pair, not an OR, and the P field points only to *the single power management component* among the PCMAX variations. PCMAX itself changes due to several other factors, but that variation is unrelated to the P field.

---

## Standard structure cross-validation

- **Where the P field lives / the group of related fields** — In the Single Entry PHR MAC CE (38.321), the P field is defined within one octet structure together with the **PCMAX,f,c field**, the **MPE field** (the power backoff index for meeting MPE when FR2 and P=1), and the **DPC field** (FR1, indicating ΔPPowerClass). The very fact that the DPC field reports ΔPPowerClass *separately* is structural evidence that the standard recognizes ΔPPowerClass as an independent factor of PCMAX variation distinct from P-MPRc. The PCMAX,f,c field, in its definition, delegates the value computation to **TS 38.213** and the measurement mapping to **TS 38.133**.

- **Separation of PHR trigger vs. P field indication** — The reporting procedure (38.321 Power Headroom Reporting) defines *when to send a PHR*. One of the triggers is *"phr-ProhibitTimer expiry + pathloss varied by phr-Tx-PowerFactorChange dB or more,"* and others include periodicTimer expiry, (re)configuration, etc. In other words, PCMAX/pathloss variation may be a **trigger that causes the PHR to be sent again**, but that and the **P field value** are separate decisions — the trigger answers "whether to send," and the P field answers "whether power management changed PCMAX." This separation is the intuitive basis for Case 2.

- **IE structure / release markers** — The PHR-Config IE (SEQUENCE) sets the PCMAX/pathloss-variation trigger threshold with `phr-Tx-PowerFactorChange ENUMERATED {dB1, dB3, dB6, infinity}`, and in its extension group it places `mpe-Reporting-FR2` (enables FR2 MPE reporting), `dpc-Reporting-FR1` (enables FR1 DPC reporting), etc. The IE-introduction markers (`-r16`/`-r17`/`-r18` suffixes) suggest that MPE reporting was introduced in Rel-16 and extended in subsequent releases, and that DPC reporting was added in Rel-18. By contrast, the P field and PCMAX,f,c definitions themselves carry no separate release marker, so the exact introduction release is not asserted from this system's corpus alone (see the honest gap below).

- **External published material cross-check** — Externally published material on the interpretation of the P field also showed the same conclusion that "the P field indicates whether power management (P-MPR) caused PCMAX,f,c to differ," and it is confirmed that the same wording has been used as a single condition since LTE (TS 36.321) and was inherited into NR — which agrees with the body-text interpretation that (b) is *one set rule* rather than an OR of two conditions. However, since the retrieved external material is mostly non-authoritative sources such as tutorials/patents, the final authority is the standard body-text quotations above. [web: LTE/NR PHR explanatory material — techlteworld.com tutorial; connectinglteandiot.wordpress.com blog; EP2659720B1 patent (all non-authoritative, used only to confirm consistency with the body text)]

---

## Honest gap

- **The PCMAX,f,c usage / PH computation body text (TS 38.213 §7.1.1)** was not retrieved verbatim directly from the relevant WG index of this system's corpus (38.213 is in the RAN1 spec domain). Therefore the basis for the PCMAX variation factors was presented via the 38.101-1/-2 §6.2.4 computation formula, and 38.213 was mentioned only as the reference to which 38.321 delegates the PCMAX,f,c value computation.
- **The exact introduction release of each PCMAX term (MPR/A-MPR/ΔTC/ΔTRxSRS, etc.)**, and the baseline release of the P field/PCMAX definitions, could not be confirmed from an authoritative version-history source beyond the IE suffixes, so they are not asserted (the absence of a suffix is no basis for "Rel-15 baseline" — it is merely silence).
- All spec quotations in this answer are based on the latest snapshot body text. If you review pinned to a specific release, we recommend cross-checking once more, in the frozen version of that release, whether the computation-formula terms and extension groups are present.
