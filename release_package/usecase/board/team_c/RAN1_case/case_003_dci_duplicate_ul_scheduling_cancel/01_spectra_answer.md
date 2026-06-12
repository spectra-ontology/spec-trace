# SPECTRA Answer — Whether the first DCI's scheduling is invalidated when two DCIs' uplink resource allocations overlap

> Question source: an internal engineering board (anonymized).

---

## Conclusion (summary)

1. **Initial question (BWP change case)** — The outcome-level understanding that "the first PUSCH ends up not being transmitted" is correct, but the mechanism is **not the rule that "the second DCI invalidates (overrides) the first scheduling."** No such override rule exists in the specification. The actual mechanism consists of two things layered together: (i) per the sentence of TS 38.213 §12 that you cited, during the BWP switching interval the obligation to transmit/receive is waived, and (ii) a UE that receives a BWP indicator changes the active UL BWP itself to the new BWP (there is only one active UL BWP per cell), so the first resource allocation on the old BWP has no place to be transmitted. And more fundamentally, (iii) scheduling in which the two uplink allocations overlap in time is bundled by the specification as an **error case that the UE "is not expected to" handle (= one the network must not create).**
2. **Additional question (a second DCI that gives only a resource allocation without a BWP change)** — **It is not invalidated.** Two time-overlapping PUSCH schedulings on the same cell are prohibited by TS 38.214 §6.1 ("the UE is not expected to transmit a PUSCH that overlaps in time with another PUSCH"), and it is also prohibited for a later PDCCH to schedule a PUSCH that starts earlier than the earlier-scheduled PUSCH (out-of-order). In other words, the general principle that "if a new DCI arrives before transmission begins, the previous scheduling is cancelled" does not exist in NR; when cancellation is needed, the specification provides a **separate, explicit mechanism** (priority-based cancellation, UL cancellation indication — all features from Rel-16 onward).

## 1. Initial question — the precise behavior in the BWP change case

### 1-1. What the cited sentence stipulates: "waiver," not "cancellation"

The relevant sentence of the current TS 38.213 §12 (the same intent as the V15.3.0 quotation in the question, with the wording generalized from "DCI format 0_1" to "a DCI format"):

> "If a UE detects a DCI format indicating an active UL BWP change for a cell, the UE is not required to receive or transmit in the cell during a time duration from the end of the third symbol of a slot where the UE receives the PDCCH that includes the DCI format in the scheduling cell until the beginning of a slot indicated by the slot offset value of the time domain resource assignment field..."

This sentence does not say that it "invalidates" the first scheduling; it only stipulates that during that switching interval the UE has **no obligation** (not required) to transmit/receive. If the first PUSCH resource falls within this interval, the UE does not have to transmit it, and in fact during the switch it cannot transmit either.

### 1-2. After the BWP switch, the old BWP's resources have no place to stand

The same §12 stipulates the behavior of a UE that receives a BWP indicator as follows:

> "If a bandwidth part indicator field is configured in a DCI format and indicates an UL BWP ... different from the active UL BWP ..., the UE shall ... **set the active UL BWP ... to the UL BWP ... indicated by the bandwidth part indicator in the DCI format**"

After the active UL BWP is changed to the second BWP, the first BWP is no longer active, so the resources allocated by the first DCI (the resources on the first BWP) cannot become a transmission target. In addition, §12 stipulates that the UE does not even expect the slot offset of a DCI indicating a BWP change to come with a value smaller than the BWP switching delay (TS 38.133) ("A UE does not expect to detect a DCI format with a BWP indicator field that indicates an active DL BWP or an active UL BWP change with the corresponding time domain resource assignment field providing a slot offset value for a PDSCH reception or PUSCH transmission that is smaller than a delay required by the UE for an active DL BWP change or UL BWP change") — that is, the second PUSCH is designed to always be located after the switch is complete.

### 1-3. Even so, scheduling the two allocations to overlap is an error case

The stipulation about overlap itself is not in the BWP clause but in TS 38.214 §6.1 (see §2). As seen there, two time-overlapping PUSCHs on the same cell are "not expected" from the scheduling stage onward, so the scenario in the question is not "a case where an override occurs" but **a case that the network must not create**, and that is precisely why there is no "first-scheduling cancellation procedure" in the specification either.

## 2. Additional question — a second DCI that gives "only a resource allocation" without a BWP change

### 2-1. Overlapping scheduling is prohibited (TS 38.214 §6.1)

> "For any HARQ process ID(s) in a given scheduled cell, **the UE is not expected to transmit a PUSCH that overlaps in time with another PUSCH.**"

> "...for any two HARQ process IDs in a given scheduled cell, if the UE is scheduled to start a first PUSCH transmission starting in symbol j by a PDCCH ending in symbol i on a scheduling cell, **the UE is not expected to be scheduled to transmit a PUSCH starting earlier than the end of the first PUSCH by a PDCCH that ends later than symbol i** of the scheduling cell."

The second sentence (out-of-order prohibition) is precisely the provision that blocks the situation in the question — a later-arriving DCI scheduling an earlier/overlapping PUSCH before the PUSCH of the earlier-arriving DCI finishes. The same applies for the same HARQ process:

> "The UE is not expected to be scheduled to transmit another PUSCH by DCI format 0_0, 0_1, 0_2 or 0_3 scrambled by C-RNTI, CS-RNTI or MCS-C-RNTI **for a given HARQ process with the DCI received before the end of the expected transmission of the last PUSCH for that HARQ process**..."

That is, the general principle "receiving a new DCI before transmission begins → invalidation of the previous scheduling" does not exist, and that situation itself is a region for which the UE has not been given a defined response (UE behavior upon violating a scheduling constraint is unspecified — an implementation matter).

### 2-2. The "cancellation" mechanisms the specification actually provides are separate features

The standard mechanisms in NR for breaking an already-scheduled PUSCH are the following two, and both require explicit configuration and conditions:

- **Priority-based cancellation (TS 38.213 §9)**: "if a transmission of a first PUSCH of larger priority index scheduled by a DCI format in a PDCCH reception would overlap in time with a repetition of the transmission of a second PUCCH of smaller priority index, the UE cancels the repetition..." — when two transmissions with different priority indices overlap, the lower one is cancelled before the first overlapping symbol. The related behavior is combined with higher-layer configurations such as prioLowDG-HighCG/prioHighDG-LowCG.
- **UL cancellation indication (TS 38.213 §11.2A)**: "If a UE is provided UplinkCancellation, the UE is provided ... search space sets ... for detection of a DCI format 2_4 ... with a CI-RNTI" — a separate group-common DCI (format 2_4) cancels part of an already-scheduled UL resource.

These two features and the out-of-order exception of §6.1 (between PDCCHs of different coresetPoolIndex, when the UE has reported the outOfOrderOperationUL-r16/-r18 capability) are, as shown by the `-r16`/`-r18` release suffixes on those parameters, additions from Rel-16 onward. At the Rel-15 (V15.3.0) time point cited in the question, it is natural to view the structure as one in which the overlap/out-of-order prohibitions applied unconditionally, without these exceptions/cancellation features; however, that specific older-version text itself was not collated in this answer (see the limitations below).

### 2-3. "A later grant overrides an earlier grant" — a direction that was discussed but not adopted

In the Rel-16 URLLC/IIoT discussions there were proposals in exactly this direction: "Proposal 3: Later UL grant can override earlier UL grant if the UE is unable to transmit two PUSCHs simultaneously within processing timeline" (R1-1902337), "UE can follow the later received UL grant ... and to cancel PUSCH scheduled by the first UL grant entirely or partially" (R1-1910224). However, what made it into the final specification is the **priority-index-based cancellation and the cancellation indication** of §2-2 above, not a rule that "a later grant generally invalidates an earlier grant" — an exhaustive review of usages of 'override' in the current 38.213/38.214 text found only two instances (flexible-symbol override in a TDD-specific configuration, and the override of an SRS spatial relation by an activation command), and both are unrelated to UL grants.

## Summary

| Scenario | Fate of the first scheduling | Basis structure |
|---|---|---|
| Second DCI indicates a UL BWP change | Not transmitted — but not by a "cancellation rule"; rather by the transmit/receive waiver during the switching interval (38.213 §12) + deactivation of the old BWP's resources due to the active BWP change | 38.213 §12 |
| Second DCI gives only a resource allocation on the same BWP | Not invalidated — overlapping scheduling itself is "UE not expected" (error case), which the network must avoid | 38.214 §6.1 |
| When standardized cancellation is needed | Priority-based cancellation or DCI 2_4 cancellation indication (separate configuration required) | 38.213 §9 / §11.2A |

## Scope and limitations of verification

- Collation scope: the full text of TS 38.213 §12 (BWP operation), the relevant portion of §9 (UCI/priority clause), §11.2A (cancellation indication), the full text of TS 38.214 §6.1, and 2 RAN1 discussion contributions (R1-1902337/R1-1910224). Usages of 'override' were checked across the full clause scope of 38.213/38.214. Cross-checking against externally published material also agreed with the out-of-order prohibition structure and the conclusion that "override is in the proposal/patent realm."
- The quotations in this answer are based on the text of the **currently ingested version**. A word-for-word collation against the original V15.3.0 (Rel-15) text cited in the question was not performed, and the statement that "Rel-15 had no exceptions/cancellation features" is an identification based on the `-r16`/`-r18` capability suffixes in the current text, not the result of an examination of the older-version original.
- UE behavior upon violating a scheduling constraint ("not expected") is an unspecified region of the standard, and this answer likewise does not assert any specific UE behavior (e.g., dropping one of the two) as standard behavior.
- The HARQ entity behavior of the MAC layer (TS 38.321) (from the grant-overwrite perspective) is under RAN2's purview and is outside the scope of this answer — I can address it separately if needed.
