# SPECTRA Answer — Whether the C-RNTI MAC CE Is Transmitted in MSGA PUSCH During a 2-Step CFRA Handover

> Retrieval method: the body text of the 3GPP TS spec is searched via semantic embeddings (vector similarity), and the standard's structure and relationships (where procedures are defined, IEs, cross-spec references, introduction agreements) are cross-verified against the body text of the Knowledge Graph and of Change Requests (CR) and contributions (TDoc). Both paths are used together. The conclusion is independently verified against publicly available standard documents (see "External cross-verification" below).

## Conclusion (one line + caveat)

- **Q1 — Correct. In 2-step CFRA, the MSGA payload is designed to include the C-RNTI MAC CE (as long as it is not a CCCH transmission).** However, the reason is not "because it is 2-step" but **"because it is a connected-state (non-CCCH) transmission."** The real reason 4-step CFRA does not send a C-RNTI MAC CE is not "because it is 4-step" but **because in 4-step CFRA the UE is identified by the dedicated preamble alone, so the procedure ends at the moment the RAR is received and there is no separate UL MAC PDU (Msg3) at all.** In other words, the key branching axis is not "2-step vs 4-step" but **"is the UE identification completed at the RAR (or MSGB) stage, or must the UE be identified by the UL payload?"**
- **Q2 — Correct. It is the target cell's C-RNTI.** When executing a handover (`reconfigurationWithSync`), the UE applies the `newUE-Identity` contained in the handover command **as the C-RNTI of the target cell (target cell group)**, and since by definition the C-RNTI MAC CE of the MSGA carries "the C-RNTI of that MAC entity," what is carried = the target cell C-RNTI that was just applied.

---

## Term decomposition (first, sorting out the polysemy / confusion axes)

The question "is it designed so that the C-RNTI is transmitted" actually overlaps three distinct branching axes. Without separating them, one ends up with the incorrect causality "it sends because it is 2-step / it does not send because it is 4-step."

- (i) **2-step vs 4-step** — whether the preamble and the payload (equivalent to Msg3) are sent *together* (2-step MSGA) or *separately* (4-step Msg1 → RAR → Msg3).
- (ii) **CFRA vs CBRA** — whether the UE can be identified by a dedicated preamble (CFRA), or it is a contention-based shared preamble (CBRA).
- (iii) **CCCH vs non-CCCH (connected)** — whether the logical channel being transmitted is CCCH (initial access in IDLE/INACTIVE without a C-RNTI yet) or not (a connected UE that already has a C-RNTI; handover falls here).

The axis that *directly* governs whether the C-RNTI MAC CE is included is (iii), while "whether a stage that sends a UL payload exists" is split by (i)/(ii). Since handover is always non-CCCH in (iii), the C-RNTI MAC CE is carried on every path that sends a UL payload.

---

## Case-by-case analysis

### Case A — 2-step (common to CFRA/CBRA), connected/non-CCCH (= handover)

The MSGA assembly rule commands it directly.

> *1> if this is the first MSGA transmission within this Random Access procedure:*
> *  2> if the transmission is not being made for the CCCH logical channel:*
> *    3> indicate to the Multiplexing and assembly entity to include a C-RNTI MAC CE in the subsequent uplink transmission.*
> — TS 38.321 §5.1.3a (MSGA transmission)

This condition makes no CFRA/CBRA distinction. As long as it is "the first MSGA transmission && non-CCCH," inclusion is unconditional. Since handover is a non-CCCH transmission of a connected UE, **the 2-step CFRA handover MSGA includes a C-RNTI MAC CE. → Verdict: included (YES).**

Why it is needed (the design intent) becomes apparent in the response-reception rule. In 2-step, after sending the MSGA the UE monitors PDCCH with two RNTIs.

> *1> if C-RNTI MAC CE was included in the MSGA:*
> *  2> monitor the PDCCH of the SpCell for Random Access Response identified by the C-RNTI while the msgB-ResponseWindow is running.*
> — TS 38.321 §5.1.4a (MSGB reception and contention resolution for 2-step RA type)

That is, the C-RNTI carried in the MSGA is the identifier that lets the gNB **deliver contention resolution / RA completion directly via a C-RNTI-addressed PDCCH.** RAN2 discussion contributions also state the same intent: a connected-mode UE carries a C-RNTI MAC CE in the MsgA so that it can receive a dedicated contention-resolution message on a PDCCH addressed to the C-RNTI (see the standard-structure cross-verification below).

### Case B — 4-step CFRA, connected/non-CCCH (the comparison target of the question)

Your observation that "4-step CFRA does not send a C-RNTI MAC CE" is **correct.** However, the mechanism is as follows. The instruction to include a C-RNTI MAC CE in Msg3 in 4-step comes out inside the RAR-reception processing (§5.1.4), but *before* reaching that instruction, the CFRA (dedicated preamble) path ends the procedure first.

> *4> if the Random Access Preamble was not selected by the MAC entity among the contention-based Random Access Preamble(s):*
> *  5> consider the Random Access procedure successfully completed.*
> *4> else:*
> *  5> set the TEMPORARY_C-RNTI to the value received in the Random Access Response;*
> *  5> if this is the first successfully received Random Access Response within this Random Access procedure:*
> *    6> if the transmission is not being made for the CCCH logical channel:*
> *      7> indicate to the Multiplexing and assembly entity to include a C-RNTI MAC CE in the subsequent uplink transmission.*
> — TS 38.321 §5.1.4 (Random Access Response reception)

Here "the case where the preamble was *not* selected from the contention-based set" = a **dedicated preamble (CFRA).** In this case, RAR reception alone makes it "Random Access procedure successfully completed," so the subsequent UL transmission (Msg3) itself does not occur. The C-RNTI MAC CE inclusion instruction (the `else` branch, line 7>) is reached only when a contention-based preamble is used, i.e., in **4-step CBRA.** Therefore, **4-step CFRA has no Msg3, so it has no C-RNTI MAC CE either. → Verdict: not transmitted (N/A — there is no UL payload stage at all).**

### Case C — 4-step CBRA, connected/non-CCCH (for contrast — the case where 4-step does send it)

Because it reaches the `else` branch of §5.1.4 above, a connected UE's 4-step CBRA includes a C-RNTI MAC CE in Msg3. And contention resolution is resolved via that C-RNTI-addressed PDCCH.

> *2> if the C-RNTI MAC CE was included in Msg3:*
> *  3> ... if the Random Access procedure was initiated by the MAC sublayer itself or by the RRC sublayer and the PDCCH transmission is addressed to the C-RNTI and contains a UL grant for a new transmission:*
> *    4> consider this Contention Resolution successful; ... consider this Random Access procedure successfully completed.*
> — TS 38.321 §5.1.5 (Contention Resolution)

→ Verdict: included (YES). What this case shows: **the generalization "if it is 4-step, no C-RNTI MAC CE is sent" is wrong;** the actual branch is "identification finished at the RAR stage by a dedicated preamble (CFRA) vs identification that must be done by the UL payload (CBRA / 2-step)."

### Q2 — Which cell's C-RNTI

Definition of the C-RNTI MAC CE:

> *- C-RNTI: This field contains the C-RNTI of the MAC entity. The length of the field is 16 bits.*
> — TS 38.321 §6.1.3.2 (C-RNTI MAC CE)

What "the C-RNTI of that MAC entity" is, is determined by the handover execution procedure. When executing `reconfigurationWithSync`, the UE applies the `newUE-Identity` contained in the handover command as the C-RNTI of the target cell.

> *3> apply the value of the newUE-Identity as the C-RNTI in the target cell group;*
> *3> apply the value of the newUE-Identity as the C-RNTI for this cell group;*
> — TS 38.331 §5.3.5.5.2 (Reconfiguration with sync)

Therefore, the C-RNTI MAC CE of the MSGA (or the 4-step CBRA Msg3) carries **the C-RNTI of the target cell (target cell group) that was just applied = the `newUE-Identity` value.** It is not the source cell's C-RNTI. → **Verdict: the target cell's C-RNTI (YES).**

Reinforcement: the fact that the target cell directed the handover via 2-step CFRA means that the handover command carried the target cell's dedicated RA resources (the 2-step resources of `rach-ConfigDedicated`) together with `newUE-Identity` (= the target C-RNTI). After applying that C-RNTI, the UE carries that value in the MSGA's C-RNTI MAC CE so that the target cell can immediately complete the RA via a C-RNTI-addressed PDCCH (§5.1.4a).

---

## Comparison table

| Case | Does a UL payload stage exist? | C-RNTI MAC CE included? | Spec § basis |
|---|---|---|---|
| A. 2-step CFRA/CBRA, non-CCCH (handover) | Yes (MSGA payload) | **Included** | 38.321 §5.1.3a, §5.1.4a |
| B. 4-step CFRA, non-CCCH | No (dedicated preamble → completed at RAR, no Msg3) | Not transmitted | 38.321 §5.1.4 |
| C. 4-step CBRA, non-CCCH | Yes (Msg3) | **Included** | 38.321 §5.1.4, §5.1.5 |
| (Q2) which C-RNTI at handover | — | target cell C-RNTI (= newUE-Identity) | 38.321 §6.1.3.2, 38.331 §5.3.5.5.2 |

Bottom-line: **the real trigger for including the C-RNTI MAC CE is "whether a non-CCCH UL payload transmission occurs"; 2-step always sends an MSGA payload, so it is included, whereas 4-step CFRA has no payload at all, so it is not transmitted. The C-RNTI at handover is the target cell C-RNTI.**

---

## Standard-structure cross-verification

- **Where procedures are defined**: 2-step MSGA assembly = TS 38.321 §5.1.3a, MSGB / contention resolution = §5.1.4a, 4-step RAR processing = §5.1.4, 4-step contention resolution = §5.1.5, procedure completion = §5.1.6. C-RNTI MAC CE definition = §6.1.3.2. Applying the C-RNTI at handover = TS 38.331 §5.3.5.5.2. That is, "what is carried in the MSGA" is specified by MAC (38.321) and "which C-RNTI value" by RRC (38.331) — a cross-spec division-of-labor structure.
- **RNTI usage table**: TS 38.321 §7.1 (RNTI usage) shows that the C-RNTI handles a connected UE's dynamically scheduled transmissions and contention resolution, and Temporary C-RNTI / MSGB-RNTI are used only when no valid C-RNTI exists yet (CCCH initial access) — a handover UE already holds the target C-RNTI, so it is identified via the C-RNTI path.
- **Design-introduction agreement (rationale)**: at the time 2-step RACH was introduced, a RAN2 contribution explicitly stated *"For CONNECTED mode UEs, the C-RNTI MAC CE is reported in MsgA which can be used to receive a dedicated message for contention resolution scheduled on the PDCCH addressed to C-RNTI"* (RAN2#107 discussion contribution), which backs the causality of this answer that "a connected UE's MsgA C-RNTI MAC CE = identification/completion based on a C-RNTI-addressed PDCCH." (This is not final standard body text but introduction-era WG discussion material; the confirmed normative text is the 38.321 body text above.)

---

## External cross-verification

The core verdicts of this answer (the C-RNTI MAC CE is included in the 2-step CFRA non-CCCH MSGA, and the target C-RNTI is used) were independently checked against public standard documents / public materials.

- The publicly available TS 38.321 standard text and technical explanatory materials all agree that "in 2-step CFRA the gNB allocates a dedicated preamble + PUSCH, the MSGA payload can include a C-RNTI MAC CE, and the RA is completed upon receiving a C-RNTI-addressed PDCCH" → **confirmed, no conflict.**
- Some search results were non-authoritative materials such as patents and vendor tutorials; these were not used as a basis for the standard norm (every verdict in this answer is grounded in the verbatim body text of 38.321 / 38.331 in the corpus).

---

## Honest gap

- **Limit on verbatim ASN.1 body text**: the IE structures of `RACH-ConfigDedicated` (2-step CFRA resources = `cfra-TwoStep`) and `ReconfigurationWithSync` were confirmed to exist in the Knowledge Graph, but the corresponding ASN.1 index entries in this corpus are structural stubs, so field-level verbatim citation was substituted with the 38.331 procedure body text (§5.3.5.5.2). The verbatim ASN.1 of the 2-step CFRA resource fields of `rach-ConfigDedicated` itself could not be cited.
- **release-scope**: this answer is based on the latest loaded edition in the corpus. The cited §5.1.3a / §5.1.4a, etc. are norms in place since the introduction of 2-step RACH (Rel-16), and some branches within the body text such as BFR / SDT / LTM / NTN are additions from later releases — since the question did not pin a release, no separate release restriction was applied, and the core of the C-RNTI MAC CE inclusion rule (first MSGA, non-CCCH) has been consistent since the 2-step introduction. The exact introduction version requires a separate comparison against the authoritative change history, so it is not asserted.
- **Limit on direct citation of external documents**: an attempt was made to directly extract (verbatim re-cite) the relevant clause from the public standard PDF, but the document extraction did not capture that clause, so the external comparison is limited to "confirmation that the conclusions agree." The normative basis is sufficiently grounded by the verbatim corpus body text.
