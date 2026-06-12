# SPECTRA Answer — Why the PC1.5 single-port max output power wording exists in 38.101-1 v16 but not in v17

> Regenerated: via the SPECTRA retrieval pipeline
> Question source: `00_original_question.md`

---

## Conclusion (summary)

The wording you asked about was **not "removed" in v17 — it is a correction sentence that was added late, and only to Rel-16**. Direct version-by-version comparison of the original texts in the official 3GPP archive shows that this sentence **never existed in any Rel-17 version (v17.0.0 through v17.6.0 checked)**. On the Rel-16 side, it was **first added in v16.12.0 (2022-06)** and has remained in v16.x ever since. So the situation is that "comparing a (late) v16 version against v17 makes it look like the sentence disappeared," and the actual sequence of events is as follows.

- **Rel-16**: PC1.5 (29 dBm) was defined only via a NOTE in Table 6.2.1-1 ("Achieved via dual Tx"). Since, per the principle in §6.1, transmitter requirements apply per connector unless otherwise stated, there was no normative basis for meeting 29 dBm by summing the outputs of the two antenna connectors in single-port transmission. To close this gap, the two sentences in your question were added to §6.2.1 (RAN4#103-e endorsed draft CR R4-2208743 → merged into Big CR CR1120 (R4-2211252), approved at RAN#96 (RP-221655) → v16.12.0).
- **Rel-17**: The same problem was solved **structurally, not by a single sentence, but through the Tx Diversity requirement framework (newly created §6.2G + the single antenna port fallback provisions of §6.2D)** (NR_RF_TxD work item). Hence there was no need for a PC1.5-specific sentence in §6.2.1, and no Rel-17 mirror of the Rel-16 correction was created.

## 1. Version-by-version facts (direct comparison of original texts in the official 3GPP archive)

| Version (published) | Sentence in question (§6.2.1) | §6.2G (TxD) | Notes |
|---|---|---|---|
| v16.4.0 (2020-06) | Absent | Absent | Table 6.2.1-1 has no PC1.5 column at all |
| v16.6.0 (2020-12) | Absent | Absent | PC1.5 introduced (CR0432r1, RAN4#96-e); only the NOTE "Achieved via dual Tx" exists |
| v16.8.0~v16.11.0 (2021-06~2022-03) | Absent | Absent | |
| **v16.12.0 (2022-06)** | **Present (first)** | Absent | change history: RP-221655, **CR1120** "Big CR for TS 38.101-1 Maintenance Part-1 (Rel-16)" |
| v16.15.0 (2023-03) | Present | Absent | Confirmed identical to the sentence quoted in the question, down to the typos ("tranmissions", "a UEs") |
| v17.0.0 (2020-12) / v17.1.0 (2021-03) | Absent | Absent | |
| **v17.3.0 (2021-09)** | Absent | **Newly created** | **CR0914** (R4-2115100, RAN4#100-e): "Transmitter power for Tx Diversity" |
| v17.6.0 (2022-06) | Absent | Present | Not mirrored into Rel-17 even in the same quarter the sentence was added to Rel-16 (intentional) |

Key point: **there is no history of the sentence ever being added to and then removed from Rel-17.** Since the Rel-16 addition (2022-06) came after the creation of Rel-17 §6.2G (2021-09), by the time the correction was made, Rel-17 had already solved the issue through its separate structure.

## 2. Why Rel-16 needed this sentence

Original "Reason for change" text of the endorsed draft CR that added the sentence to Rel-16, **R4-2208743 "Definition of PC1.5 and applicability of extensions of power-class parameters"** (merged into CR1120):

> "Define UE power class 1.5 for Rel-16. This cannot be defined by a note in a table (NOTE 5). In clause 6.1 it is specified that transmitter requirements apply per connector unless otherwise stated. TxD indication with the associated verifcation across two connectors (suffix G in the Rel-17 version) is not mandatory for PC1.5."

That is, in Rel-16:
1. PC1.5's "29 dBm achieved by summing two PAs" existed only as a NOTE in a table → it needed to be elevated to a normative definition.
2. §6.1 stipulates that "requirements apply per connector unless otherwise stated" → without an explicit sentence allowing summation across the two connectors in single-port transmission, a PC1.5 UE would read as having to deliver 29 dBm from a single connector.
3. Rel-16 has no TxD verification framework like Rel-17's §6.2G (suffix G) → the gap was closed with a sentence directly in §6.2.1.

## 3. Why Rel-17 does not have this sentence — absorbed into the TxD requirement framework

The Rel-17 NR_RF_TxD work item specified the same content in a generalized structure.

**(1) Creation of §6.2G — CR0914 (R4-2115100, RAN4#100-e, Cat B) → v17.3.0:**

> "6.2G.1 UE maximum output power for Tx Diversity — For UE supporting Tx Diversity, the maximum output power as indicated by UE power class in Table 6.2.1-1 is defined as the sum of the maximum output power from both UE antenna connectors."

The "summation across two connectors" provision, previously PC1.5-specific, became **a general TxD provision for all power classes**, and the PC1.5 dual-Tx MPR table (6.2G.2-2) was created at the same time.

**(2) Single antenna port fallback provisions — RAN4#102-e agreement (R4-2206519), reflected in running CR CR1021 (R4-2205574):**

> "6.2D.1: The requirements in 6.2 are the baseline for single-port transmissions, an exception granted for TxD."

The requirements applicable when scheduled by DCI format 0_0 or DCI format 0_1 with a single antenna port were systematized in §6.2D (current text: "If the UE is scheduled for single antenna-port PUSCH transmission by DCI format 0_0 or by DCI format 0_1 for single antenna port codebook based transmission, the requirements in clause 6.2.2 apply for the power class as indicated by the ue-PowerClass field..."). The background of this agreement, and the Single Tx/Dual Tx applicability matrix per ULFPTx mode and per TxD indication, are recorded in TR 38.837 §5.3.1 (Table 5.3.1-1).

**(3) Clarification that TxD is implicitly applicable for PC1.5 — CR1431r1 (R4-2303679, RAN4#106, Rel-17 Cat F) / CR1432 (R4-2302440, Rel-18 Cat A):**

> "When a UE indicates PC1.5 for a given band it achieves maximum power by means of Tx Diversity in the current version of the spec. Therefore, Tx Diversity is implied for PC1.5 even if the UE does not indicate txDiversity-r16 in the UE capabilities."

This sentence is in the current §6.2G.1. In other words, from Rel-17 onward, the basis for a PC1.5 UE meeting maximum output power in single-port transmission by summing the two connectors is not the dedicated sentence in §6.2.1 but **§6.2G.1 (TxD) — which applies to PC1.5 even without capability signalling**.

## 4. Summary of relevant meetings

| Meeting | Timing | Content |
|---|---|---|
| RAN4#96-e | 2020-11 | CR0432r1: PC1.5 (29 dBm) introduced — NOTE "Achieved via dual Tx" |
| RAN4#100-e | 2021-08 | CR0914: §6.2G "Transmitter power for Tx Diversity" created (Rel-17, v17.3.0) |
| RAN4#102-e | 2022-02/03 | R4-2206519 agreed: single antenna port fallback (DCI 0_0/0_1) requirements systematized → CR1021 |
| RAN4#103-e | 2022-05 | R4-2208743 endorsed: sentence in question added to Rel-16 §6.2.1 → CR1120 (approved at RAN#96, v16.12.0) |
| RAN4#106 | 2023-02/03 | CR1431r1/CR1432: "Tx Diversity is implied for PC1.5" clarified (§6.2G.1) |

## 5. Implementation perspective

- **Implementing against Rel-16**: The sentence in §6.2.1 is the basis for PC1.5 single-port operation (summation across two connectors + meeting MOP when scheduled with DCI 0_0/0_1 single antenna port).
- **Implementing against Rel-17 and later**: The basis clause for the same behavior moves to §6.2G.1 (+ the single antenna port fallback provisions of §6.2D). For PC1.5, TxD requirements apply even if the TxD capability is not reported (explicit in §6.2G.1). The substance of the requirement (29 dBm via summation across two connectors) is preserved; what was added is the applicability structure and the per-ULFPTx-mode refinement (TR 38.837 Table 5.3.1-1).

## Verification scope and limitations

- Presence/absence per version was confirmed directly against the original texts of v16.4.0/v16.6.0/v16.8.0/v16.10.0/v16.11.0/v16.12.0/v16.15.0/v17.0.0/v17.1.0/v17.3.0/v17.6.0 in the official 3GPP archive. The status of intermediate versions not checked (v16.13.0~14.0, v17.2.0, etc.) is inferred from adjacent versions.
- The full diff of the endorsed draft CR R4-2208743 (the change-marked original of the sentences added to §6.2.1) was confirmed in the standards document collection down to the "Reason for change" text, and the quotation above is verbatim from that original.
- The course of the meeting discussion at RAN4#103-e when this draft CR was endorsed (e.g., which company raised it) was not verified within the scope of this answer.
