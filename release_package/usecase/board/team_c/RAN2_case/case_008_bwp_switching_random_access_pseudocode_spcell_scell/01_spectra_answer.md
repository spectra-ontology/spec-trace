# SPECTRA Answer — Interpreting the BWP switching pseudo-code at Random Access (SpCell vs SCell) (TS 38.321 Rel-15)

> Search method: We searched the body of the 3GPP TS spec by semantic embedding (vector similarity) and cross-verified the standard structure and relations (clause location, IE definition, introducing CR, cross-WG references) against a knowledge graph. The RA-initiation BWP pseudo-code and the unpaired-spectrum pairing sentence come from the RAN2 MAC (38.321) body; the DL/UL BWP linking rule was checked cross-WG in RAN1 PHY (38.213 §12); and the introduction background was checked separately in the RAN2 CR partition. The core verdicts were independently cross-verified against public material (see "External cross-verification" below). Because the question fixed the **V15.5.0 (Rel-15)** version, the (e)RedCap branch (added in Rel-17) of the latest corpus version (V19.0.0) is demarcated as out of scope.

---

## Conclusion (one-line bottom-line)

- **Q1: The action that aligns the DL BWP to the same bwp-Id as the UL BWP is a pairing rule for *unpaired spectrum (TDD)* — it does not apply to FDD (paired).** In TDD, DL/UL share one carrier, so the active DL and UL BWPs must have the same bwp-Id (+the same center frequency) and BWP switching is common to DL/UL; therefore, when RA changes the UL BWP, the DL must follow to the same bwp-Id so the pair is not broken. The asker's premise "the same even in FDD" **needs correction**: in FDD, the DL/UL BWPs are configured and switched independently.
- **Q2: Correct (reasoning reinforced).** SCell RA is *always* PDCCH order CFRA (`ra-PreambleIndex ≠ 0`), so the network arranges a PRACH occasion on the active UL BWP in advance → the line 1 condition becomes false and no UL BWP switching occurs. Rather than "one does not need to check," the precise statement is "the check is performed, but because it is CFRA it always passes (switching not needed)."
- **Q2-1: Because the SCell's DL is received not on its own cell but on the *SpCell*'s DL BWP.** Since the RAR (msg2 etc.) is received on the SpCell DL BWP (line 12), there is no reason to align the SCell's own DL/UL bwp-Id — pairing alignment (line 6-8) is needed only on the SpCell where DL reception happens.
- **Q3: Correct.** Line 12 means "the RA's DL is on the *SpCell*'s active DL BWP, and the UL is on the active UL BWP of *this Serving Cell*." For SCell RA, the preamble is sent on the SCell UL BWP, but the RAR is received on the SpCell DL BWP (both SCell and SpCell are involved in the RA — CR0685r2 NOTE).
- **Q4: bwp-InactivityTimer is, in essence, a single ServingCellConfig timer tied to the *DL BWP*.** It is a timer that, on expiry, falls back to the default DL BWP; in TDD, because DL/UL switch together, the effect reaches the UL as well, but the timer itself is DL-anchored. The pseudo-code's "associated with the active DL BWP" is accurate.

---

## Terminology breakdown (to prevent confusion)

- **(i) paired (FDD) vs unpaired (TDD) spectrum**: Almost all the subtlety of this question hinges here. In unpaired (TDD), DL/UL are on the same carrier → BWPs are bound as a pair and switch together. In paired (FDD), DL/UL are on separate carriers → BWPs are independent.
- **(ii) roles of SpCell vs SCell**: The RA's *DL (RAR reception)* is always on the SpCell, and the *UL (preamble transmission)* is on the "this Serving Cell" that initiated the RA. Even for SCell RA, the DL crosses to the SpCell.
- **(iii) meaning of bwp-Id**: BWP identifier. Value 0 is reserved for the initial BWP; the network assigns consecutively from 1 [38.331 BWP-Downlink/Uplink field desc].

---

## Per-question analysis

### Spec body that serves as the basis (verbatim)

**RA-initiation BWP pseudo-code + unpaired pairing** [38.321 §5.15.1 "Downlink and Uplink"] — verbatim:

> *"For unpaired spectrum, a DL BWP is paired with a UL BWP, and BWP switching is common for both UL and DL."*
>
> *"perform the Random Access procedure on the active DL BWP of SpCell and active UL BWP of this Serving Cell."*

**SCell RA = PDCCH order CFRA** [38.321 §5.1.1 "Random Access procedure initialization"] — verbatim:

> *"The Random Access procedure on an SCell or an LTM candidate cell shall only be initiated by a PDCCH order with ra-PreambleIndex different from 0b000000."*

**DL/UL BWP linking rule (cross-WG, RAN1 PHY)** [38.213 §12 "Bandwidth part operation"] — verbatim:

> *"For unpaired spectrum operation, a DL BWP from the set of configured DL BWPs with index provided by BWP-Id is linked with an UL BWP from the set of configured UL BWPs with index provided by BWP-Id when the DL BWP index and the UL BWP index are same."*
>
> *"For unpaired spectrum operation, a UE does not expect to receive a configuration where the center frequency for a DL BWP is different than the center frequency for an UL BWP when the BWP-Id of the DL BWP is same as the BWP-Id of the UL BWP."*

**TDD BWP-pair center frequency** [38.331 BWP field descriptions] — verbatim:

> *"In case of TDD, a BWP-pair (UL BWP and DL BWP with the same bwp-Id) must have the same center frequency (see TS 38.213, clause 12)."*

**bwp-InactivityTimer meaning** [38.331 ServingCellConfig field desc] — verbatim:

> *"bwp-InactivityTimer — The duration in ms after which the UE falls back to the default Bandwidth Part (see TS 38.321, clause 5.15)."*

---

### Q1 — Reason for aligning the SpCell DL BWP to the same bwp-Id as the UL, and applicability to FDD

Pseudo-code line 3-4 (PRACH-not-configured branch) and line 6-8 (else branch) both **align the active DL BWP to the UL BWP's bwp-Id when the Serving Cell is a SpCell**. The *reason* is the unpaired (TDD) pairing rule:

- 38.321 §5.15.1 pins it down: *"For unpaired spectrum, a DL BWP is paired with a UL BWP, and BWP switching is common for both UL and DL."* In TDD, DL/UL time-share one carrier, so the active DL and UL BWPs *must have the same bwp-Id and the same center frequency* [38.213 §12; 38.331 BWP field desc "TDD … must have the same center frequency"].
- Therefore, when RA switches the UL BWP (to initialUplinkBWP or another BWP), the DL BWP must switch to the same bwp-Id to keep the pair invariant. Line 4 (to initialDownlinkBWP) and line 8 (to the same bwp-Id as UL) are that alignment action.

**FDD (paired) is different.** In paired spectrum, DL/UL are on separate carriers, so BWPs are not bound as a pair and are configured/switched independently (the linking rule and center-frequency constraint of 38.213 §12 are explicitly scoped to *"For unpaired spectrum operation"*). That is, "align the DL to the same bwp-Id as the UL" is a **TDD-specific action**, and the asker's understanding that it "behaves the same in FDD" needs correction.

→ **Q1 verdict: reason for the action = unpaired (TDD) pairing. The FDD premise is corrected.** (The pseudo-code body itself does not place an explicit "if unpaired" guard at line 6-8, but its underlying rule [38.213 §12] is scoped to unpaired, so in FDD there is no need for alignment in the first place — this "absence of a guard" part is marked as *inference* because the corpus does not explicitly state the duplex branch.)

### Q2 — Does the SCell not need to check the presence of a PRACH occasion

§5.1.1 prescribes: *"The Random Access procedure on an SCell … shall only be initiated by a PDCCH order with ra-PreambleIndex different from 0b000000."* That is, **SCell RA is, without exception, PDCCH order CFRA**. Since CFRA has the network designate the preamble/resources, for that RA to function the network must have arranged a PRACH occasion on the active UL BWP. As a result, the condition of line 1 ("if PRACH occasions are not configured for the active UL BWP") becomes **false**, so the UL BWP switching of line 2 does not occur.

→ **Q2 verdict: the conclusion is correct, with reinforced wording.** Not "because it is a SCell, it *does not check* the PRACH occasion," but rather "SCell RA is CFRA (PDCCH order), so a PRACH occasion is *already guaranteed* on the active UL BWP, the line 1 condition is always false → switching is not needed" is precise. (What the asker called "information received from MAC-CE" is, precisely, the *PDCCH order (DCI)* delivering the ra-PreambleIndex.)

### Q2-1 — Reason the SCell does not check DL/UL bwp-Id match

Line 12 explicitly states that the RA's DL is performed on the *SpCell's active DL BWP*. Even for SCell RA, the DL such as RAR (msg2) is received on the SpCell DL BWP (not the SCell's own DL BWP), so there is no need to align the SCell's DL/UL bwp-Id. Hence line 6-8 (DL↔UL bwp-Id alignment) applies **only to the SpCell where DL reception actually happens**.

→ **Q2-1 verdict: matches.** Since the SCell does not receive the RA DL on its own DL BWP, pairing alignment is meaningless. Basis: line 12 verbatim + CR0685r2 NOTE *"If a Random Access procedure is initiated on an SCell, both this SCell and the SpCell are associated with this Random Access procedure"* [R2-2002382].

### Q3 — Interpretation of line 12 (SpCell DL+UL, SCell UL-only)

Line 12: *"perform the Random Access procedure on the active DL BWP of SpCell and active UL BWP of this Serving Cell."* Decomposed:

- **DL (RAR reception / msg2·msg4)**: always the *SpCell*'s active DL BWP.
- **UL (preamble / msg1·msg3)**: the active UL BWP of *this Serving Cell* that initiated the RA.
- SpCell initiates → "this Serving Cell" = SpCell → both DL and UL on the SpCell.
- SCell initiates → the preamble is on the SCell UL BWP, but the RAR is on the SpCell DL BWP (cross-carrier).

→ **Q3 verdict: matches (refined).** The understanding "SpCell does RA on DL+UL, SCell on UL" is correct; precisely, the key point is that *the DL (RAR) of SCell RA is received on the SpCell DL BWP*. The fact that SCell and SpCell are involved together in the RA is confirmed by the CR0685r2 NOTE.

### Q4 — Is bwp-InactivityTimer limited to the DL BWP

38.331 ServingCellConfig defines bwp-InactivityTimer as a timer that *"falls back to the default Bandwidth Part."* This timer is **one per serving cell**, is (re)started by PDCCH activity on the DL BWP, and on expiry returns the active *DL* BWP to the default DL BWP — it is essentially **DL-anchored**. In unpaired (TDD), because DL/UL switch together, the default DL BWP fallback affects the UL as well, but this is due to pairing, not because the timer separately monitors the UL.

→ **Q4 verdict: limited to DL is correct.** The pseudo-code's *"bwp-InactivityTimer associated with the active DL BWP"* expression is accurate. What looks like "monitors both DL and UL" is merely a consequence of TDD pairing (common switching); the timer definition itself is based on the DL BWP.

---

## Comparison table

| Query | Asker's understanding | Spec basis | Verdict |
|---|---|---|---|
| Q1 reason for DL=UL bwp-Id alignment | same action including FDD | unpaired pairing "switching common for both" [38.321 §5.15.1]; "linked … same bwp-Id" / center-freq [38.213 §12]; "TDD BWP-pair same center frequency" [38.331 BWP desc] | reason = TDD pairing; **FDD premise corrected** |
| Q2 SCell does not check PRACH occasion | SCell need not check | "SCell RA … only by PDCCH order, ra-PreambleIndex ≠ 0" [38.321 §5.1.1] | conclusion correct (CFRA, so line1 always false) |
| Q2-1 SCell does not check DL/UL alignment | curious about reason | RA DL is on SpCell DL BWP [38.321 §5.15.1 line12]; SCell+SpCell associated [CR0685r2/R2-2002382] | matches |
| Q3 line 12 (SpCell DL+UL, SCell UL) | SpCell DL+UL / SCell UL | line 12 verbatim; SCell RAR = SpCell DL | matches (SCell DL = SpCell) |
| Q4 timer limited to DL | both DL and UL? | "falls back to default (DL) BWP" [38.331 ServingCellConfig]; TDD common switching | DL-anchored correct |

**Bottom-line:** Q2, Q2-1, Q3, Q4 — the asker's understanding is correct (after reinforcement/refinement). Only Q1 needs correction of the premise "the same in FDD" — aligning DL↔UL to the same bwp-Id is a rule specific to unpaired (TDD).

---

## Standard-structure cross-verification

- **Clause location (corpus KG)**: In the latest corpus version (V19.0.0), the RA-initiation BWP pseudo-code is in 38.321 §5.15.1 (Downlink and Uplink), whereas in the asker's V15.5.0 (~p.46) it was under §5.1. The operative logic is identical, and the (e)RedCap branch added by V19 is Rel-17, hence out of Rel-15 scope.
- **Introducing CR (Rel-15)**: The behavior related to §5.15 BWP operation was settled in Rel-15 by CR0406r2 (R2-1816908, "bwp-InactivityTimer when PDCCH indicating BWP switching", cat-F, agreed) / CR0409r3 (R2-1819131, "RRC triggered BWP switching while RACH is ongoing", cat-F, agreed) — showing that the interaction of BWP switching while RACH is ongoing was a design consideration from the start.
- **cross-WG (RAN1)**: The *physical-layer* constraint that links DL/UL BWP by bwp-Id and keeps the center frequency identical is in 38.213 §12 — cross-WG confirming that the MAC pseudo-code's (38.321) alignment action is to satisfy the PHY constraint.
- **release introduction**: BWP/RA behavior exists from the very first NR (Rel-15) and matches the question's version. Only the (e)RedCap-specific branch is Rel-17.

---

## External cross-verification

We independently cross-checked the core verdicts against public material.

- **Confirmed**: the NOTE that SCell RA is associated with both SCell and SpCell (Q3) — confirmed.
- **Confirmed**: 38.213's DL/UL BWP bwp-Id linking + center-frequency constraint applies to *unpaired (TDD)* (Q1) — confirmed.
- **Confirmed (core nuance of Q1)**: FDD (paired) configures/switches DL/UL BWP independently, while TDD (unpaired) switches them together — confirmed by public NR BWP commentary (FDD vs TDD pairing).
- **Confirmed**: bwp-InactivityTimer falls back to the default DL BWP (Q4) — confirmed.
- **Some authoritative source blocked**: the itecspec 38.321 §5.15 mirror returned HTTP 403. However, the identical pseudo-code/sentences exist byte-identically in the corpus TS body and CRs, so the basis is satisfied by the corpus (the external mirror block is not regarded as a weakness of the verdict). The attempt log is recorded in the audit trail.

---

## Honest gap

- **Whether line 6-8 executes in FDD (unspecified area)**: The pseudo-code body does not place an explicit "if unpaired/TDD" guard at line 6-8. The *underlying rule* of that alignment action (38.213 §12 linking/center-freq) is scoped to unpaired, so "in FDD there is no need for alignment" is a reasonable interpretation; however, "whether line 6-8, even if formally executed in FDD, is harmless" is an area the corpus does not directly regulate, hence *inference*.
- **Version difference (V15.5.0 vs V19)**: The question is fixed to V15.5.0 (Rel-15). The verbatim text of this analysis was retrieved from corpus V19.0.0 (38.321) / V18.7.0 (38.331), and the quoted sentences use only the operative parts that are identical from Rel-15. The V19 (e)RedCap branch is Rel-17 and was excluded from quotation/application (scope demarcation). The precise version history of "at which frozen V-number the wording reached its current form" is not determined from a single-snapshot corpus.
- **"MAC-CE vs PDCCH order" wording**: The asker described the SCell CFRA resources as "information received from MAC-CE," but precisely, the PDCCH order (DCI) delivers the ra-PreambleIndex. This distinction does not change the Q2 conclusion (both are CFRA), but it has been reinforced terminologically.
