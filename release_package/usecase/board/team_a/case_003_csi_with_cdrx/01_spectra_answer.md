# SPECTRA Answer — CSI report and C-DRX inactive time (periodic/aperiodic CSI vs Active Time)

> Retrieval method: the 3GPP TS spec body was searched with semantic embeddings (vector similarity), and the standard's structure and relationships (definition locations, section membership, cross-spec references) were cross-checked against a knowledge graph. Both paths were used together. Key conclusions were additionally cross-verified against a public standards mirror (confirmed).

## Conclusion (bottom-line)

When a CSI report meets C-DRX, **two independent gates** must be evaluated separately. Conflating them into one produces the wrong answer.

1. **Measurement validity gate (TS 38.214 §5.1.6.1)** — did the *most recent CSI measurement occasion* used to compute that report (CSI-RS for channel / CSI-IM for interference) occur within DRX Active Time? If not, the measurement is not valid and the report does not materialize.
2. **Transmission gate (TS 38.321 §5.7)** — is the moment the report is *actually transmitted* (the PUCCH occasion or PUSCH) within Active Time? If not in Active Time, periodic/SP CSI on PUCCH is not transmitted.

The answers to the three questions:
- **Q1 — drop (do not transmit).** Even if the measurement was taken in Active Time, if the report occasion itself is inactive, periodic CSI on PUCCH is not transmitted. (Except: if power-saving exceptions such as ps-TransmitOtherPeriodicCSI / ps-TransmitPeriodicL1-RSRP are configured, transmission is allowed within the onDuration window.)
- **Q2 — drop (no stale reuse).** If the linked most recent channel CSI-RS / interference CSI-IM occasion was not received within Active Time, the UE must not reuse measurements from a previous Active Time to report, and that report does not materialize.
- **Q3 — a DCI trigger alone does not make it automatically valid.** The fact that a trigger was received does not forcibly validate the measurement of an AP CSI-RS occasion that lies in inactive time. If, after accounting for all timer effects, that occasion is genuinely in inactive time, the UE cannot obtain a valid measurement and the AP CSI report does not materialize. The §5.7 clause "aperiodic CSI on PUSCH ... when such is expected" is merely a *transmission-gate exception* meaning **it does not block the transmission of a valid AP CSI report when one is expected** — it is not a clause that validates the *measurement* of an inactive occasion.

---

## Terminology decomposition — do not mix the two gates

The single question "should the CSI report happen?" actually bundles two behaviors governed by different layers.

- (i) **Measurement validity** — *is there material to build the report from?* Determined by whether the physical-layer CSI measurements (channel CSI-RS, interference CSI-IM) were validly received within DRX Active Time. Governing clause: **TS 38.214 §5.1.6.1**.
- (ii) **Transmission gating** — *given the material exists, can the report actually be transmitted?* Determined by whether the report occasion (PUCCH/PUSCH) falls in Active Time and whether cqi-Mask/csi-Mask applies. Governing clause: **TS 38.321 §5.7**.

Key point: (i) can pass and still be blocked at (ii), and an exception at (ii) (aperiodic on PUSCH) does not exempt (i). The two gates are in an **AND** relationship; neither overrides the other.

---

## Case-by-case analysis

### Q1 — Measurement in Active Time, report occasion inactive (periodic CSI on PUCCH)

Here the **transmission gate (§5.7)** decides first. Among the rules for UE behavior when not in Active Time:

> *"in current symbol n, if a DRX group would not be in Active Time ... not report CSI on PUCCH and semi-persistent CSI configured on PUSCH in this DRX group;"* — TS 38.321 §5.7

That is, if the report occasion (slot n) is inactive, periodic CSI on PUCCH is **not transmitted.** The fact that the measurement was taken in Active Time does not open the transmission gate — measurement validity is a gate-(i) matter, while whether to transmit is judged separately by gate (ii).

There is, however, an explicit power-saving exception. In the onDuration-related branch of §5.7:

> *"if neither ps-TransmitPeriodicL1-RSRP nor lpwus-TransmitPeriodicL1-RSRP is configured with value true: not report periodic CSI that is L1-RSRP on PUCCH."*
> *"if neither ps-TransmitOtherPeriodicCSI nor lpwus-TransmitOtherPeriodicCSI is configured with value true: not report periodic CSI that is not L1-RSRP on PUCCH."* — TS 38.321 §5.7

Reading these rules in the contrapositive: if **ps-TransmitOtherPeriodicCSI** (periodic CSI other than L1-RSRP) or **ps-TransmitPeriodicL1-RSRP** (periodic L1-RSRP) is configured to true, reporting is allowed within the corresponding onDuration window even while inactive. And in that case the measurement validity in §5.1.6.1 is also extended to the same window (see the §5.1.6.1 quotation below).

Furthermore, if cqi-Mask (csi-Mask) is configured, the transmission window narrows further.

> *"if CSI masking (csi-Mask) is setup by upper layers: ... if drx-onDurationTimer of a DRX group would not be running ... not report CSI on PUCCH in this DRX group."* — TS 38.321 §5.7

**Verdict**: in the default case where no ps-Transmit* exception is configured → the report occasion is inactive, so **drop periodic CSI on PUCCH**. In the power-saving case where ps-TransmitOtherPeriodicCSI / ps-TransmitPeriodicL1-RSRP is configured → transmission allowed, limited to the onDuration window.

### Q2 — Valid PUCCH at the report occasion, but the linked most recent CSI-RS/CSI-IM not received in Active Time

This case is decided by the **measurement validity gate (§5.1.6.1)**. The general rule that, under DRX, a measurement occasion must lie within Active Time for the CSI to be reported:

> *"If the UE is configured with DRX and, ... -otherwise, the most recent CSI measurement occasion occurs in DRX active time for CSI to be reported."* — TS 38.214 §5.1.6.1

Here "the most recent CSI measurement occasion" refers to the most recent channel CSI-RS / interference CSI-IM occasion linked to that report. It must lie within Active Time for "CSI to be reported" to materialize. The question's premise is precisely that this most recent occasion was missed because of inactive time, so **there is no valid measurement material.**

When the power-saving exception (ps-TransmitOtherPeriodicCSI / ps-TransmitPeriodicL1-RSRP) is configured, the measurement validity window is extended to onDuration:

> *"... the most recent CSI measurement occasion occurs in DRX active time or during the time duration indicated by drx-onDurationTimer in DRX-Config also outside DRX active time for CSI to be reported;"* — TS 38.214 §5.1.6.1 (ps-TransmitOtherPeriodicCSI / ps-TransmitPeriodicL1-RSRP branch)

But even this extension is valid only "when a measurement was received within that extended window"; in no case is there **any allowance to pull in old measurements from a previous Active Time and report stale CSI.** The standard simply nails down "the most recent measurement occasion shall lie within the (extended) Active window" as the precondition for reporting, and defines no reuse path for expired measurements.

**Verdict**: if the linked most recent channel CSI-RS / interference CSI-IM was not received within Active Time (or, with the power-saving exception, the extended window) → **no stale reuse; drop that CSI report.** Having a valid PUCCH resource only satisfies the (ii) transmission gate; it cannot substitute for (i) measurement validity.

### Q3 — DCI triggered aperiodic CSI-RS / aperiodic CSI report, but the AP CSI-RS occasion falls in inactive time

This case is where the separation of the two gates cuts most sharply. The **transmission gate (§5.7)** has an explicit exception for aperiodic:

> *"Regardless of whether the MAC entity is monitoring PDCCH or not on the Serving Cells in a DRX group, the MAC entity transmits HARQ feedback, aperiodic CSI on PUSCH, mode-A UE-initiated CSI reporting on PUCCH and PUSCH, and aperiodic SRS defined in TS 38.214 [7] on the Serving Cells in the DRX group when such is expected."* — TS 38.321 §5.7

This sentence looks powerful, but one must look at exactly what it exempts — what it exempts is the **transmission gate with respect to "whether PDCCH is being monitored."** In other words: "if a valid AP CSI report is expected, the UE transmits it on PUSCH even if it is not monitoring PDCCH at that moment." The key conditional is **"when such is expected"** — it transmits *when expected*; it does not mean it is *always expected*.

What determines "expected" is, again, the **measurement validity gate (§5.1.6.1)**. For an AP CSI report to be expected, the AP CSI-RS / CSI-IM measurement needed to build that report must be valid. But the general rule of §5.1.6.1 (in the non-power-saving-exception case) requires "the most recent CSI measurement occasion occurs in DRX active time for CSI to be reported." The question's premise is that the post-trigger AP CSI-RS occasion **genuinely lies in inactive time** (even after accounting for all timer effects such as drx-InactivityTimer), therefore:

- Receiving the DCI trigger is a fact bearing only on the §5.7 transmission gate (transmission regardless of PDCCH monitoring); it does not forcibly validate the measurement of an inactive occasion.
- If that occasion is inactive, the UE cannot obtain a valid AP CSI measurement, so a valid AP CSI report is **not expected.** Hence the very premise of "when such is expected" fails to hold.

The common error here is to over-extend §5.7's "aperiodic CSI on PUSCH ... when such is expected" into "whenever a trigger arrives, measure and report unconditionally even if inactive." That clause is a **transmission-gate exception** (it does not block transmission), not a **measurement-validity provision** (it does not validate measurements). That reading mixes the two gates.

**Verdict**: if, after fully accounting for the timer calculations, the triggered AP CSI-RS occasion is still in inactive time → the UE cannot take a valid measurement → **drop the AP CSI report.** The fact that a DCI trigger was received only guarantees, at the (ii) transmission gate, "transmit even without PDCCH monitoring if expected"; it does not exempt (i) measurement validity. (Conversely, if timer effects bring that occasion into Active Time, measurement and reporting materialize normally — that is the normal case, distinct from the "drop" case the question describes.)

---

## Comparison table

| Case | Deciding gate | Key basis | Verdict |
|---|---|---|---|
| Q1 measurement in Active / report occasion inactive (periodic on PUCCH) | Transmission gate (38.321 §5.7) | "if a DRX group would not be in Active Time ... not report CSI on PUCCH" | Drop by default; with ps-TransmitOtherPeriodicCSI / ps-TransmitPeriodicL1-RSRP configured, transmit limited to the onDuration window |
| Q2 PUCCH available but most recent channel CSI-RS/interference CSI-IM not received in Active Time | Measurement validity (38.214 §5.1.6.1) | "the most recent CSI measurement occasion occurs in DRX active time for CSI to be reported" | Drop, no stale reuse (valid PUCCH only satisfies the transmission gate) |
| Q3 DCI trigger received, AP CSI-RS occasion inactive | Measurement validity (38.214 §5.1.6.1) + transmission-gate exception (38.321 §5.7) | "aperiodic CSI on PUSCH ... when such is expected" is a transmission-gate exception; whether "expected" is decided by §5.1.6.1 measurement validity | If still inactive after timer accounting, drop (trigger ≠ measurement validation) |

**One-line summary**: measurement validity (38.214 §5.1.6.1) and the transmission gate (38.321 §5.7) are an AND — both must pass for a report to materialize — and the §5.7 aperiodic-on-PUSCH exception exempts only *transmission*, not *measurement validity*.

---

## Standards-structure cross-verification

- **Measurement validity clause** — TS 38.214 §5.1.6.1 "CSI-RS reception procedure". Specifies, in a single clause, the relationship between channel/interference measurement occasions and DRX active time, the ps-TransmitOtherPeriodicCSI / ps-TransmitPeriodicL1-RSRP power-saving exceptions, and the cell DTX branch. This clause is where gate (i), measurement validity, is defined.
- **Transmission gate clause** — TS 38.321 §5.7 "Discontinuous Reception (DRX)". Specifies, in a single clause, the Active Time definition, the "not report CSI on PUCCH / not transmit periodic·SP SRS" behavior when not in Active Time, the additional cqi-Mask (csi-Mask) constraint, and the "regardless of ... monitoring PDCCH ... aperiodic CSI on PUSCH ... when such is expected" exception. This clause is where gate (ii), the transmission gate, is defined.
- **Division of labor between the two clauses**: the standard deliberately splits responsibility so that 38.214 covers "does the CSI to be reported *materialize* (measurement validity)" while 38.321 covers "when is a materialized report *transmitted* (transmission gating)". The very fact that the standard structures these as two separate clauses is itself evidence that the two gates are independent; reading only one clause and concluding misses the other gate (which is the typical cause of wrong answers to Q3).

---

## Honest gap

- The answer is grounded in the body text of the measurement validity clause (TS 38.214 §5.1.6.1) and the transmission gate clause (TS 38.321 §5.7). The *concrete calculation* of whether individual timers such as drx-InactivityTimer place a given slot inside Active Time depends on the §5.7 Active Time definition (onDurationTimer / InactivityTimer / RetransmissionTimer / ra-ContentionResolutionTimer, etc.) and on network configuration values; since the question presupposes "still inactive after all timers are accounted for," the verdict holds under that premise. In a real implementation, the timer state between the trigger moment and the occasion moment must be evaluated directly.
- Constraints such as aperiodic CSI processing time (Z/Z') in §5.4 CSI computation time are a separate layer, orthogonal to the gate verdicts in this answer (to be examined separately if needed).
- Additional branches of §5.7/§5.1.6.1 such as cell DTX, NTN, and multicast DRX are outside the question's scope (generic C-DRX) and were not factored into the verdicts.
- This corpus is a latest-release snapshot. The skeleton of the quoted clauses (the measurement-occasion-in-active-time requirement, the not-report behavior when Active Time is not met, the aperiodic-on-PUSCH exception) are core provisions present since early releases, but some items — the ps-Transmit* power-saving branches, cell DTX, and multicast branches — were added in later releases (the exact introducing release is subject to separate version-history confirmation).
- External cross-check: the §5.7 wording "aperiodic CSI on PUSCH ... when such is expected" and the §5.1.6.1 wording "most recent CSI measurement occasion occurs in DRX active time" were confirmed identically against a public standards mirror (confirmed).
