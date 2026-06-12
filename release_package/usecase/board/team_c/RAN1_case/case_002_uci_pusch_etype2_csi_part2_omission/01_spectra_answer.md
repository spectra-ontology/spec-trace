# [RAN1] Full omission of CSI part 2 in UCI on PUSCH (Enhanced Type II)

> Search method: semantic search over 3GPP TS body text + simultaneous use of the standard structure (sections, contribution documents).
> All quotations are verbatim from the TS body. Cited specs: TS 38.214 (CSI reporting procedures), TS 38.212 (UCI multiplexing/rate matching).

---

## Key answer (summary)

- **Question 1 (whether full omission of CSI part 2 can occur)**: It can occur. The Part 2 CSI of an Enhanced Type II (`typeII-r16` family) report is divided into Group 0 / Group 1 / Group 2, where the priority of Group 0 is **the highest (Priority 0)**, and omission proceeds **from the lowest priority, level by level**. The only exception to "omit all of the information at that priority level" is the sub-report (Part 2 subband CSI) based on `csi-ReportSubConfigToAddModList`, and **there is no exception wording that protects Group 0 (Priority 0)**. Therefore, if the resources are sufficiently small, the entire Part 2 CSI, including Group 0, can be omitted.

- **Question 2 (whether an agreement/discussion on the ambiguity exists)**: The normative basis for determining Q'_CSI1 (the amount of CSI part 1 resources) is the `if there is CSI part 2 to be transmitted on the PUSCH ... else` branch in TS 38.212 §6.3.2.4.1.2. However, **no agreement or conclusion wording that explicitly resolves "how to interpret this branch when CSI part 2 is configured but entirely omitted / how to fill the remaining resources in UCI-only" was found in the corpus.** Related company contributions (discussion documents) exist, but they are not agreements.

---

## 1. Whether full omission of CSI part 2 can occur (Question 1)

### 1-1. Omission unit rule

TS 38.214 §5.2.3 (CSI reporting using PUSCH):

> When CSI reporting on PUSCH comprises two parts, the UE may omit a portion of the Part 2 CSI. Omission of Part 2 CSI is according to the priority order shown in Table 5.2.3-1 ...

> When omitting Part 2 CSI information for a particular priority level, the UE shall omit all of the information at that priority level, except for Part 2 subband CSI when the corresponding CSI report contains one or more CSI sub-reports with Part 2 each corresponding to a sub-configuration from a list of sub-configurations provided by csi-ReportSubConfigToAddModList contained in the CSI-ReportConfig as described in Clause 5.2.1.1.

→ That is, the exception to "omit all of the information at that priority level" is **only the case of a sub-configuration-based sub-report**. There is no separate exception defined that protects Group 0. This matches the asking engineer's interpretation that "it does not seem there is exception handling that omission must not go down to group 0".

### 1-2. Priority structure — Group 0 is the highest (omitted last)

In an Enhanced Type II report, each reported element is bundled by priority value to form Group 0/1/2 (§5.2.3):

> -Group 0 includes indices ... (if reported), ... (if reported) and ... .
> -Group 1 includes ... the highest priority elements of ... .
> -Group 2 includes ... the lowest priority elements of ... .

Table 5.2.3-1 (Priority reporting levels for Part 2 CSI):

> Priority 0: ... Group 0 CSI for CSI reports configured as 'typeII-r16', 'typeII-PortSelection-r16', 'typeII-PortSelection-r17', 'typeII-CJT-r18', ...
> Priority 1: Group 1 CSI for CSI report 1, if configured as 'typeII-r16', ...
> Priority 2: Group 2 CSI for CSI report 1, if configured as 'typeII-r16', ...

→ Since Group 0 = Priority 0 (the highest priority), it is discarded **last** during omission. However, by the rule in 1-1 above, Group 0 (Priority 0) is also not excluded from being an omission target.

### 1-3. Omission termination condition — in particular UCI-only (no transport block)

§5.2.3 proceeds with omission from the lowest priority and stops when a condition is satisfied:

> Part 2 CSI is omitted level by level, beginning with the lowest priority level until the lowest priority level is reached which causes the [number of resource elements available for Part 2 CSI] to be less than or equal to [the allocated value] or [the value derived from nrofBitsInUTO-UCI] when the higher layer parameter nrofBitsInUTO-UCI is configured.

The asking engineer's case of **UCI only (PUSCH without UL-SCH)** transmission:

> When part 2 CSI is transmitted on PUSCH with no transport block, lower priority bits are omitted until Part 2 CSI code rate, which is given by [the expression using parameters in clause 6.3.2.4 of [5, 38.212]] before HARQ-ACK puncturing part 2 CSI if any, is below a threshold code rate lower than one ...

→ Nowhere in these termination conditions is there a floor stating "Group 0 (Priority 0) must be kept". If the resource/code rate condition so requires, Priority 0 can be reached and the entire Part 2 CSI can be omitted.

**Summary (Question 1)**: In eType II, full omission of CSI part 2 (including Group 0) is structurally possible, and there is no exception provision in §5.2.3 that prevents it.

---

## 2. Ambiguity of CSI part 1 resource amount (Q') and whether an agreement exists (Question 2)

### 2-1. Normative branch — "if there is CSI part 2 to be transmitted"

The point the asking engineer raised, that "the Q' calculation formula for CSI part 1 differs depending on whether CSI part 2 exists", is stated in TS 38.212 §6.3.2.4.1.2 (PUSCH without UL-SCH, i.e., the UCI-only case):

> For CSI part 1 transmission on PUSCH without UL-SCH, the number of coded modulation symbols per layer for CSI part 1 transmission, denoted as [Q'_CSI1], is determined as follows:
> if there is CSI part 2 to be transmitted on the PUSCH,
>   [...]
> else
>   [...]
> end if

→ The branching criterion is **"there is CSI part 2 to be transmitted on the PUSCH"**. This wording is a judgment at the level of the report configuration (whether it is composed as a two-part CSI report so that CSI part 2 resources are calculated and reserved), and omission is a procedure applied **after** the part 1/part 2 resource calculation. Following this interpretation, as long as the report is configured as two-part, CSI part 2 is regarded as "to be transmitted" (corresponding to the asking engineer's interpretation 2), so no ambiguity arises in the Q'_CSI1 calculation, and the gNB only needs to decode part 1 once.

### 2-2. Honest limitation — explicit agreement wording not confirmed

- The interpretation in 2-1 above is based on the normative wording ("to be transmitted") of §6.3.2.4.1.2 and on the procedural structure in which omission is applied after the resource calculation. However, **the point of "which way to interpret this branch in the edge case where CSI part 2 is configured but entirely omitted", as well as agreement or conclusion wording that explicitly pins down "the handling of the remaining resources after part 2 is emptied in UCI-only", could not be confirmed verbatim in the corpus.** That is, the part the asking engineer raised, that "there should be a related explicit statement", is not, within the current search scope, established as a separate explicit provision.

- The corpus contains **company discussion contributions** close to this topic (e.g., "Discussion on UCI issues for eType II CSI", "Remaining issues on UCI multiplexing", "Discussion on coefficients partition in eT2 CSI"). However, these are individual companies' discussion documents, and **they are not wording confirmed as a WG agreement that resolves this edge case.** Therefore, they are not cited as a basis for an agreement.

**Summary (Question 2)**: The normative basis for the Q'_CSI1 branch is "if there is CSI part 2 to be transmitted on the PUSCH" in §6.3.2.4.1.2. The natural interpretation is to regard CSI part 2 as "to be transmitted" (as long as the report is two-part), removing the ambiguity; however, no agreement wording that explicitly resolves the full-omission edge case and the handling of the remaining resources was confirmed in the current corpus.

---

## 3. Citation scope / limitations (honest disclosure)

- Basis specs: TS 38.214 §5.2.3 (omission rules, Table 5.2.3-1, UCI-only termination condition), TS 38.212 §6.3.2.4.1.2 (Q' branch for CSI part 1 on PUSCH without UL-SCH), §6.3.2.4.2.2/§6.3.2.4.2.3 (CSI part 1/2 resource calculation).
- The formula symbols (Q', α, code rate threshold, etc.) are denoted only as symbols in the body, so specific numerical values are not quoted. Please refer directly to the above 38.212 clauses for the exact formulas.
- The "whether an agreement/discussion exists" in Question 2 is a result based on the searched scope. There may be a non-public agreement of a particular meeting or a contribution that was not captured in the search, so if confirmation is needed, we recommend directly checking the meeting agreement records of the relevant feature (eType II UCI multiplexing).
