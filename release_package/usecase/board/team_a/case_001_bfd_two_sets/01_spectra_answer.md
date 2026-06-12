# SPECTRA Answer — SpCell two BFD-RS sets: BFR Random Access trigger and BFD relaxation applicability criteria

> Retrieval method: 3GPP TS/TR spec bodies were searched via semantic embeddings (vector similarity), and standards structure and relationships (definition locations, IEs, cross-spec references, CR/meeting history) were cross-verified through a Knowledge Graph. Both paths were used together. The key conclusions were independently cross-checked against public 3GPP/patent sources (see "External cross-verification" below).

## Conclusion (bottom-line)

- **Q1 — No.** When only set1 reaches the threshold, BFR is triggered for set1 only, and this is handled **not by SpCell Random Access but by transmission of the (Enhanced/Truncated) BFR MAC CE for that BFD-RS set**. **The only condition for initiating RA on the SpCell is "BFR has been triggered for both BFD-RS sets and the BFR has not been successfully completed for any of the sets"** [38.321 §5.17]. Therefore the UE must not initiate SpCell RA based on a set1-only failure, and "wait until both sets are triggered" is not an accurate description either — precisely, **each set independently triggers and handles its own BFR immediately**, while **the heavier recovery action of SpCell RA fires only when both sets are in the failed state simultaneously**.
- **Q2 — (Conservative conclusion) This scenario does not even arise as a valid configuration under the standard.** When two BFD-RS sets are configured on the SpCell, **the field that configures BFD relaxation (`goodServingCellEvaluationBFD`) is itself restricted to be absent** — i.e., with a two-set configuration, SpCell BFD relaxation is never enabled in the first place [R2-2213050 (38.331 §6.3.2 CR), 38.331 §6.3.2]. Therefore the generalization "set1 alone satisfies the relaxation condition, so relax set2 as well" **has no basis in the standard.** Nor should one assert that "relaxation is per serving cell, so it propagates across all sets".

---

## Terminology decomposition (to avoid confusion)

In Q1 and Q2 a single word refers to behaviors at different layers, so we separate them first.

- (i) **per-set BFD evaluation** — the behavior in which each BFD-RS set independently counts beam failures with its own `BFI_COUNTER`, `beamFailureDetectionTimer`, and `beamFailureInstanceMaxCount` (independent per set).
- (ii) **per-set BFR trigger and its recovery means** — when one set's counter reaches the threshold, "a BFR for that set" is triggered, and its recovery is carried out by transmission of a BFR MAC CE (Enhanced/Truncated).
- (iii) **SpCell Random Access initiation** — a heavier recovery procedure separate from (ii) above. The action of initiating RA via PRACH on the SpCell. It fires only under the specific condition that both sets fail simultaneously.
- (iv) **Whether BFD relaxation can be configured** — whether relaxation can be *configured* at all (= presence of the `goodServingCellEvaluationBFD` field) is a separate layer from whether, once configured, *the relaxation is applied when the condition is met*. Q2 asks about "propagation of application", but the actual decision is made at the "configurability" layer.

---

## Case-by-case analysis — Q1 (only set1 fails BFD → SpCell RA?)

Premise: both `failureDetectionSet1` and `failureDetectionSet2` are configured on the SpCell. 38.321 §5.17 handles "the case where the Serving Cell is configured with two BFD-RS sets" and "the other case" as separate branches, and in the two-set branch each action is specified **per set**.

### Case A — set1's counter reaches the threshold (set1 only)

The two-set branch of 38.321 §5.17 specifies per-set handling as follows:

> *"if the Serving Cell is configured with two BFD-RS sets: if beam failure instance indication for a BFD-RS set has been received from lower layers: start or restart the beamFailureDetectionTimer of the BFD-RS set; increment BFI_COUNTER of the BFD-RS set by 1; if BFI_COUNTER of the BFD-RS set >= beamFailureInstanceMaxCount: trigger a BFR for this BFD-RS set of the Serving Cell;"* [38.321 §5.17]

→ When set1's `BFI_COUNTER` reaches set1's `beamFailureInstanceMaxCount`, **only a BFR for set1 is triggered**. By itself this does not initiate SpCell RA.

The *recovery means* of a set1-only BFR is a MAC CE, not RA. 38.300 §9.2.8 summarizes the same behavior procedurally:

> *"After beam failure is detected for a BFD-RS set of a Serving Cell, the UE: triggers beam failure recovery by initiating a transmission of a BFR MAC CE for this BFD-RS set; selects a suitable beam for this BFD-RS set (if available) and indicates whether the suitable (new) beam is found or not along with the information about the beam failure in the BFR MAC CE for this BFD-RS set."* [38.300 §9.2.8]

And successful completion of a set-only BFR is also determined not by RA completion but by reception of an uplink grant for the MAC CE:

> *"if a PDCCH addressed to C-RNTI indicating uplink grant for a new transmission is received for the HARQ process used for the transmission of the Enhanced BFR MAC CE or Truncated Enhanced BFR MAC CE which contains beam failure recovery information of a BFD-RS set of the Serving Cell: set BFI_COUNTER of the BFD-RS set to 0; consider the Beam Failure Recovery procedure successfully completed for this BFD-RS set and cancel all the triggered BFRs of this BFD-RS set of the Serving Cell."* [38.321 §5.17]

→ **Verdict: a set1-only failure immediately triggers a set1 BFR, which is handled by transmission of the (Enhanced/Truncated) BFR MAC CE for that set. SpCell RA is not initiated.**

### Case B — BFR is triggered for both sets and neither has been successfully completed

Only in this case does SpCell RA fire:

> *"if BFR is triggered for both BFD-RS sets of the SpCell and the Beam Failure Recovery procedure is not successfully completed for any of the BFD-RS sets: initiate a Random Access procedure (see clause 5.1) on the SpCell;"* [38.321 §5.17]

38.300 §9.2.8 likewise specifies concurrent failure as the trigger for SpCell RA:

> *"After beam failure is detected for both BFD-RS sets of SpCell concurrently, the UE: triggers beam failure recovery by initiating a Random Access procedure on the SpCell; ... upon completion of the Random Access procedure, beam failure recovery for both BFD-RS sets of SpCell is considered complete."* [38.300 §9.2.8]

Upon completion:

> *"if the Serving Cell is SpCell and the Random Access procedure initiated for beam failure recovery of both BFD-RS sets of SpCell is successfully completed (see clause 5.1): set BFI_COUNTER of each BFD-RS set of SpCell to 0. consider the Beam Failure Recovery procedure successfully completed."* [38.321 §5.17]

→ **Verdict: SpCell RA is initiated only under the combined condition "BFR triggered for both sets + neither set successfully completed".**

### Case C — contrast with the single-set (legacy, non-two-set) configuration (for reference)

This differs from the question's premise (two-set), but we contrast it to make the branch distinction clear. In the general case where the Serving Cell is *not* configured with two sets, the else branch of §5.17 specifies:

> *"else: if beam failure instance indication has been received from lower layers: ... if BFI_COUNTER >= beamFailureInstanceMaxCount: ... else: initiate a Random Access procedure (see clause 5.1) on the SpCell;"* [38.321 §5.17]

That is, **on a single-set SpCell, SpCell RA fires as soon as the single counter reaches the threshold**. The key difference is that in the two-set configuration this directness is replaced by the stricter combined condition of "both sets failing concurrently". (This is why a set-only failure does not lead directly to RA.)

### Q1 comparison table

| Case | Situation | UE behavior | Basis |
|---|---|---|---|
| A | two-set, only set1's counter at threshold | set1 BFR trigger → transmission of the (Enhanced/Truncated) BFR MAC CE for that set (not SpCell RA) | 38.321 §5.17 / 38.300 §9.2.8 |
| B | two-set, both sets triggered & neither completed | initiate SpCell Random Access | 38.321 §5.17 / 38.300 §9.2.8 |
| C (reference) | single-set SpCell, counter at threshold | immediate SpCell Random Access | 38.321 §5.17 (else branch) |

**Q1 one-line conclusion:** set1-only failure → set1 BFR (MAC CE) only; SpCell RA only when both sets are concurrently uncompleted. Not "wait for both sets", but "each set handled independently; only RA requires the concurrent condition".

---

## Case-by-case analysis — Q2 (only set1 meets the relaxation condition → relax set2 too?)

Q2 presupposes "an SpCell configured with two BFD-RS sets" and asks about set-level relaxation propagation. However, the decisive point is that **the presupposed configuration itself is not permitted by the standard** — and this is confirmed not in the TS body but in **the CR (WG agreement) that introduced it**.

### Case A — whether relaxation can be configured (the decisive layer)

SpCell BFD relaxation is enabled by the `goodServingCellEvaluationBFD` field, and with a two-set configuration this field is restricted to be absent. The reason and the change content of the CR that introduced this restriction (targeting 38.331 §6.3.2):

> *"In TS 38.331, the current BFD relaxation can be configured alone with the BFD, however, after checking with the current RAN4 spec and the progress about the BFD for mTRP in RAN4, we think the current RAN4 specification does not support to relax the BFD for mTRP. So we think, at least the current stage, the BFD relaxation cannot be configured when there are two BFD-RS sets are configured."* [R2-2213050, RAN2#120, type=CR, release=Rel-17]

> *"Summary of change: Add the restriction 'this field is absent if failureDetectionSetN is present for the S(p)Cell' in the field description of goodServingCellEvaluationBFD."* [R2-2213050, RAN2#120, type=CR, release=Rel-17]

The 38.331 field description body in which this change is reflected:

> *"goodServingCellEvaluationBFD Indicates the criterion for a UE to detect the good serving cell quality for BFD relaxation in the SpCell in RRC_CONNECTED. The field is always configured when the network enables BFD relaxation for the UE in this SpCell. This field is absent if failureDetectionSetN is present for the SpCell."* [38.331 §6.3.2]

→ **Verdict: if two BFD-RS sets (`failureDetectionSetN`) are present on the SpCell, `goodServingCellEvaluationBFD` is absent → SpCell BFD relaxation cannot be configured at all.** Therefore the situation "only set1 meets the relaxation condition" does not occur in a valid SpCell configuration. The question's "may set2 also be relaxed" rests on a premise that has no standing under the standard.

### Case B — the native unit of relaxation application (where configuration is permitted, for reference)

In the general cases where relaxation is permitted (e.g., BFD on an SCell, or an SpCell that is not two-set), the unit of the relaxation evaluation is **per serving cell**, defined as a fulfillment condition on the BFD-RS resource:

> *"The relaxed measurement criterion of good serving cell quality for BFD is fulfilled when the downlink radio link quality on the configured BFD-RS resource is evaluated to be better than the threshold Qin+XdB, wherein ... X is the parameter offset in goodServingCellEvaluationBFD for the evaluated serving cell."* [38.331 §5.7.13.2]

The RAN4 requirements spec likewise specifies relaxation via the `bfd-Relaxation-r17` capability plus a serving-cell-level good-serving-cell condition:

> *"For the UE supports bfd-Relaxation-r17 and configured with dedicated signalling goodServingCellEvaluationBFD ... the relaxed requirements ... are allowed to apply to the relaxed BFD measurements on the serving cell after fulfilling the following conditions: ... the good serving cell quality criterion defined in clause 5.7.13.2 of TS 38.331 is fulfilled for the serving cell configured with BFD-RS ..."* [38.133 §8.5.1.1]

→ Relaxation is natively defined **per serving cell**, and no set-level propagation rule such as "relax only one side per BFD-RS set" exists in the standard text. And if that serving cell is an SpCell with two sets, relaxation configuration is blocked by Case A — so the set-level partial relaxation that Q2 asks about has no standards basis via either path.

### Q2 comparison table

| Case | Situation | Conclusion | Basis |
|---|---|---|---|
| A | SpCell two-set (the question's premise) | BFD relaxation cannot be configured (`goodServingCellEvaluationBFD` absent) → scenario does not arise | R2-2213050 / 38.331 §6.3.2 |
| B (reference) | relaxation-permitted cases | relaxation is per serving cell; no rule for partial propagation at BFD-RS set level | 38.331 §5.7.13.2 / 38.133 §8.5.1.1 |

**Q2 one-line conclusion:** "set1 alone fulfilled → relax set2 too" has no standards basis. On an SpCell with two sets, BFD relaxation configuration is blocked in the first place. It cannot be asserted either as serving-cell aggregate propagation or as set-level partial relaxation — conservatively, "not configurable" is the correct answer.

---

## Standards-structure cross-verification

- **Where the BFR procedure is defined**: the normative text for the per-set vs SpCell-RA branching is 38.321 §5.17 (MAC). The procedural summary is 38.300 §9.2.8. Physical-layer link recovery (beam failure instance indication, definition of set1/set2) is 38.213 §6 (*"the UE can be provided respective two sets and of periodic CSI-RS resource configuration indexes by failureDetectionSet1 and failureDetectionSet2 ..."* [38.213 §6]). RLM and the link recovery RS limit (maximum 2 for link recovery) are in 38.213 §5.
- **Configuration IEs**: the ENUMERATED candidate values for the two sets' counters/timers are defined in `BeamFailureDetectionSet-r17`, and the recovery resources in `BeamFailureRecoveryConfig` (ASN.1 below). The relaxation-enabling field `goodServingCellEvaluationBFD` is located in `SpCellConfig` (38.331 §6.3.2), and the CR restriction above is reflected in the same clause.
- **Relaxation requirements (perf-req) cross-WG**: the applicability requirements for BFD relaxation are in RAN4 38.133 §8.5, and the RAN2 CR's stated reason explicitly relies on "the RAN4 spec does not support mTRP BFD relaxation" — a cross-WG dependency directly linking the RAN2 RRC restriction with the RAN4 requirements.
- **Release/history**: the change introducing the Q2 restriction is confirmed via structural metadata to be a Rel-17 CR (R2-2213050) agreed at meeting RAN2#120 under work item NR_UE_pow_sav_enh (UE power saving enhancements) (detailed source and version in the audit trail).

### Key ASN.1 (verbatim)

Per-set counter/timer (independently configured for each of the two sets):

```asn1
BeamFailureDetectionSet-r17 ::= SEQUENCE {
    bfdResourcesToAddModList-r17     SEQUENCE (SIZE (1..maxNrofBFDResourcePerSet-r17)) OF BeamLinkMonitoringRS-r17    OPTIONAL,  -- Need N
    bfdResourcesToReleaseList-r17    SEQUENCE (SIZE (1..maxNrofBFDResourcePerSet-r17)) OF BeamLinkMonitoringRS-Id-r17  OPTIONAL,  -- Need N
    beamFailureInstanceMaxCount-r17  ENUMERATED {n1, n2, n3, n4, n5, n6, n8, n10}                                      OPTIONAL,  -- Need R
    beamFailureDetectionTimer-r17    ENUMERATED {pbfd1, pbfd2, pbfd3, pbfd4, pbfd5, pbfd6, pbfd8, pbfd10}              OPTIONAL,  -- Need R
    ...
}
```

SpCell BFR recovery resources (RA-based):

```asn1
BeamFailureRecoveryConfig ::= SEQUENCE {
    rootSequenceIndex-BFR    INTEGER (0..137)                                                     OPTIONAL,  -- Need M
    rach-ConfigBFR           RACH-ConfigGeneric                                                   OPTIONAL,  -- Need M
    rsrp-ThresholdSSB        RSRP-Range                                                           OPTIONAL,  -- Need M
    candidateBeamRSList      SEQUENCE (SIZE (1..maxNrofCandidateBeams)) OF PRACH-ResourceDedicatedBFR OPTIONAL,  -- Need M
    ...
    beamFailureRecoveryTimer ENUMERATED {ms10, ms20, ms40, ms60, ms80, ms100, ms150, ms200}      OPTIONAL,  -- Need M
    ...
    [[ spCell-BFR-CBRA-r16  ENUMERATED {true}  OPTIONAL ]]  -- Need R
}
```

Relaxation-enabling field offset (in the permitted cases):

```asn1
GoodServingCellEvaluation-r17 ::= SEQUENCE {
    offset-r17  ENUMERATED {db2, db4, db6, db8}  OPTIONAL  -- Need S
}
```

---

## External cross-verification

- **Q1 confirmed.** A public mirror of the 3GPP 38.321 §5.17 text and public patent literature on multi-TRP BFR agree with this answer's key verdict that "when BFR is triggered for both BFD-RS sets of the SpCell, the UE performs Random Access on the SpCell, and upon successful completion for both sets the BFI_COUNTER of each set is set to 0". The independence of per-set counters/timers also matches.
- **Q2 — a discrepancy with a non-authoritative source resolved in favor of the standard.** One public patent document (US 12402025) proposes a mechanism for applying BFD relaxation *independently per TRP/per set* in a multi-TRP cell (one set relaxed while the other keeps the standard periodicity). However, that is merely a vendor patent's *proposed design*, not a standards agreement, and **what 3GPP actually agreed is the opposite** — when two BFD-RS sets are configured, SpCell BFD relaxation is *blocked from being configured at all* (R2-2213050). Given that the RAN2 agreement's rationale was "RAN4 does not support mTRP BFD relaxation at the current stage", the per-set relaxation described in the patent is a direction not adopted by the standard. This answer follows the authoritative sources (standard text + agreed CR).

---

## Honest gap

- The SCell BFR branch of 38.321 §5.17 (BFR MAC CE/SR triggering) and the NCR/PSCell-deactivated branches are outside the direct scope of this question (SpCell two-set) and are not quoted in detail. Only the MAC CE handling of a set-only BFR is quoted as question-relevant scope.
- The follow-on procedural details of 38.213 §6 (link recovery) — the full candidate beam selection algorithm — are quoted only up to the set1/set2 definition portion; the full physical-layer measurement details are outside the quoted scope.
- This corpus is a latest-release snapshot. The clauses underpinning the Q1/Q2 verdicts correspond to the two-BFD-RS-set behavior introduced/finalized in Rel-17 (`-r17`-suffixed IEs + a Rel-17 CR); earlier releases have no two-set branch at all. Possible further changes in Rel-18/19 remain a separate item to verify.
- The exact identifier and version number of the plenary CR pack that introduced the Q2 restriction are not included in the body and were cross-verified only via structural metadata (release/meeting/work item) — see the audit trail for the exact identifiers.
