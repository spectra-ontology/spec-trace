# SPECTRA Answer — Whether a Registration Request is sent after PDU session release reject (5GSM cause #43, Invalid PDU session identity)

> Retrieval method: the 3GPP TS/TR spec body was searched with semantic embeddings (vector similarity), and the standard's structure and relations (definition locations, clause references, cross-spec references) were cross-checked against the knowledge graph. Both paths were used together. The two clauses of the governing NAS specification (TS 24.501) that directly control this scenario are outside our loaded corpus, so they were supplemented by directly consulting the authoritative source (the publicly available ETSI 24.501 text); those citations are marked `[web: 24.501 §…]` (distinguished from corpus-body citations). External cross-verification result: confirmed (corpus and authoritative text agree, no conflict).

---

## Conclusion (one line + conditional caveat)

**The REF is correct.** In this scenario, where the network rejects the UE-requested release with **cause #43 (Invalid PDU session identity)**, the UE has **no obligation to send a Registration Request for PDU session sync purposes after the local release.** The key point is that the rule the questioner cited ("if there are PDU sessions locally released by the UE, include the PDU session status IE in the Registration Request") is **not a provision that *triggers* a Registration Request, but a sentence that specifies the *content* of a Registration Request that is already being initiated (for some other reason)** — and this #43-reject path is not included among those "other reasons" (the trigger list).

- In other words, the DUT's behavior (sending a Registration Request marking that session as inactive) is **not behavior the specification requires for this trigger.** The REF's reasoning — sync is already aligned, so no additional sync-up is needed — is consistent with the specification.
- However, this does not mean the DUT's behavior is a **specification violation (prohibited).** If it happens to coincide with a situation where a mobility registration must occur anyway for some other independent reason (see Case D below), then filling in that IE is in fact the correct thing to do. For this case taken on its own, "no obligation to send" is the answer.

---

## Term decomposition — is the cited rule a "trigger" or "content"?

In standard NAS procedures, the phrase "include the PDU session status IE" splits into two propositions at different layers. Conflating the two is exactly what causes one to miss the point on which REF and DUT diverge in this question.

- **(i) Trigger layer** — *"What *initiates* the Registration Request procedure?"* The list of reasons that initiate a mobility/periodic registration update is defined separately `[web: 24.501 §5.5.1.3.2]`. Only one item in that list, item m), cites local release as a reason, and **it explicitly restricts which local-release situations it refers to.**
- **(ii) Content layer** — *"What gets filled *into* a Registration Request message that has already been initiated?"* The sentence the questioner cited — "shall include the PDU session status IE … which are locally released by the UE" — belongs here. It states the filling rule for that IE **under the premise that a Registration Request is already being sent.**

The crux of the question is precisely "is this sentence (i) or (ii)?", and **by the structure of the specification it is (ii).** (ii) never fires unless (i) has been satisfied. Therefore one must check whether "#43 reject → local release" itself appears in the trigger list of (i); if it does not, no Registration Request is initiated.

---

## Case-by-case analysis — Registration Request obligation per NAS path on which local release occurs

Dividing the question's trigger axis (= for what reason is the PDU session locally released?) along the NAS specification's own clause structure gives the following. This clause structure is itself the mutually exclusive, collectively exhaustive axis.

### Case A — Network rejects the UE-requested release with #43 (the question's case)

The network rejects with #43 because, on the SMF side, "that PDU session ID is already in the INACTIVE state" `[web: 24.501 §6.4.3.6 a]`:

> *"If the PDU session ID in the PDU SESSION RELEASE REQUEST message belongs to any PDU session in state PDU SESSION INACTIVE in the SMF, the SMF shall send the PDU SESSION RELEASE REJECT message to the UE with the 5GSM cause #43 'Invalid PDU session identity'."*

The clause defining the UE's behavior upon receiving this reject is §6.4.3.4 `[web: 24.501 §6.4.3.4 (Rel-18)]`:

> *"Upon receipt of a PDU SESSION RELEASE REJECT message and a PDU session ID, … the UE shall stop timer T3582, release the allocated PTI value and locally release the PDU session."*

There is **no step here at all instructing the UE to send a Registration Request.** Stop T3582 / release PTI / local release — that is everything. The Rel-15 baseline likewise has no registration step; it merely phrases things in the inverse direction, implying that on #43 the session is (locally) released `[web: 24.501 §6.4.3.4 (Rel-15)]`:

> *"the UE shall stop timer T3582, shall release the allocated PTI value. If the PDU SESSION RELEASE REJECT message includes a 5GSM cause IE with a value different from #43 'invalid PDU session identity', the UE shall consider that the PDU session is not released."*

→ **In this case: no Registration Request obligation.**

### Case B — Collision during UE-requested release (clash with a network-initiated modification/release procedure)

Among the abnormal cases of the UE-requested release procedure, the collision cases (modification collision b, release collision c) are held in our conformance corpus, which quotes the 24.501 §6.4.3.5 text verbatim [38.523-1 §10.1.6.1], [38.523-1 §10.1.6.2]. In both collision cases the behavior is "ignore/abort one procedure and proceed with the other" — **there is no Registration Request step.**

> *"… the UE shall ignore the PDU SESSION MODIFICATION COMMAND message and proceed with the PDU session release procedure."* [38.523-1 §10.1.6.1, quoting 24.501 §6.4.3.5 b]

→ **In this case too: no Registration Request obligation.**

### Case C — Network normally accepts the UE-requested release

If the network accepts the release, it is handled via the network-requested release procedure. The corpus holds the 24.501 §6.4.3.3 text by quotation [38.523-1 §10.1.6.1]:

> *"Upon receipt of a PDU SESSION RELEASE REQUEST message and a PDU session ID, if the SMF accepts the request to release the PDU session, … perform the network-requested PDU session release procedure as specified in subclause 6.3.3."*

This path (§6.3.3 network-requested release) does not itself trigger a Registration Request either (the network commands via PDU SESSION RELEASE COMMAND). → **No Registration Request obligation.**

### Case D — The path where local release *actually does* trigger a Registration Request (the control group)

This is where the IE-inclusion rule the questioner cited actually fires. Trigger item m) of the mobility/periodic registration update cites local release as a reason but **explicitly restricts** the clauses it covers `[web: 24.501 §5.5.1.3.2]`:

> *"m) when the UE needs to indicate PDU session status to the network after performing a local release of PDU session(s) as specified in subclauses 6.4.1.5 and 6.4.3.5;"*

In other words, "send a Registration Request after local release" becomes an obligation **only for the local-release situations specified in §6.4.1.5 (handling of exceeding the maximum number of allowed PDU sessions) and §6.4.3.5 (UE-side abnormal cases).** And even within §6.4.3.5, the Registration Request step is written **explicitly** in just the following two items `[web: 24.501 §6.4.3.5 (Rel-18)]`:

> *"a) Expiry of timer T3582. … on the fifth expiry of timer T3582, the UE shall abort the procedure, release the allocated PTI, perform a local release of the PDU session, and perform the registration procedure for mobility and periodic registration update by sending a REGISTRATION REQUEST message including the PDU session status IE …"*

> *"d) Receipt of an indication that the 5GSM message was not forwarded due to routing failure … the UE shall … perform a local release of the PDU session, and perform the registration procedure for mobility and periodic registration update by sending a REGISTRATION REQUEST message including the PDU session status IE …"*

→ **On this path there IS a Registration Request obligation, with the PDU session status IE filled in.** This is the place where the rule the questioner cited natively applies.

#### The decisive contrast

`§6.4.3.5 a)/d)` **spells out** the registration step in writing, whereas **`§6.4.3.4` (= Case A, #43 reject) does not contain that step, and `6.4.3.4` is also absent from trigger m)'s reference list (`6.4.1.5` and `6.4.3.5`).** The specification authors stated the registration step explicitly wherever registration is required, and deliberately omitted it at the #43-reject location. This "present here vs. absent there" asymmetry settles the answer to this question from the specification text alone.

---

## Comparison table (case → verdict → governing clause)

| Case | Reason for local release | Governing clause | Registration Request obligation? | Basis |
|---|---|---|---|---|
| **A (the question)** | UE-requested release rejected with #43 | §6.4.3.4 | **None** | Only stop T3582 / release PTI / locally release; excluded from trigger m)'s references |
| B | Collision during UE-requested release | §6.4.3.5 b)/c) | None | Only "ignore/abort, then proceed with the other procedure" (corpus quotation) |
| C | Network normally accepts the release | §6.4.3.3 → §6.3.3 | None | Network commands via RELEASE COMMAND (corpus quotation) |
| D | Fifth expiry of T3582 / routing failure / max-session exceeded | §6.4.3.5 a)/d), §6.4.1.5 | **Yes** | "perform the registration procedure … sending a REGISTRATION REQUEST … including the PDU session status IE" stated explicitly |

**Bottom line:** the IE-inclusion rule the questioner cited is a *content* rule living in the table's Case D. The question's #43-reject (Case A) is not a *trigger* in that table, so the very premise on which that rule would fire does not hold. → **REF is correct.**

---

## Cross-verification against the standard's structure (definition locations / clause references / cross-spec relations)

- **Factual basis of the scenario and the meaning of sync** — our conformance knowledge graph holds the conditions for #43 verbatim. The rule that the UE sets #43 in a 5GSM STATUS when it receives a command/response for a session in the INACTIVE state appears in [38.523-1 §10.1.2.2] (quoting 24.501 §7.3.2 b) and [38.523-1 §10.1.3.2] (quoting 24.501 §6.3.3.x). In other words, **#43 is a signal that "both sides regard this session as INACTIVE"** — and that is the specification-level basis for the REF's logic of "already in sync, no additional sync-up needed."
- **The structural separation of trigger ≠ content** — the registration trigger list (§5.5.1.3.2) and the PDU session status IE filling rule (the message-content provision of the same procedure) are located in different clauses. The fact that trigger m) references only `6.4.1.5` and `6.4.3.5` (an inter-clause reference relation) structurally proves that the two layers are distinct.
- **The network-side sync mechanism (supporting evidence)** — in mobility registration, sync is fundamentally a structure in which **the network informs the UE "which sessions remain alive" via the PDU session status IE of the REGISTRATION ACCEPT.** This point is stated in the rationale of a standards change that updated the conformance default-message definitions (verbatim below). Put differently, the authoritative alignment point for sync is the network's ACCEPT response; with the state already aligned via #43, there is no specification-level warrant for the UE to spontaneously launch a Registration Request.

> *"for mobility registration, when the UE may have active PDU sessions, the UE will expect the network to indicate the PDU sessions that remain active … set the [PDU session status IE of REGISTRATION ACCEPT] to the same value as received in the last REGISTRATION REQUEST message."* [38.508-1 conformance-spec change rationale text]

---

## Honest gap

- **The two clauses that directly govern this scenario (24.501 §5.5.1.3.2 trigger list, §6.4.3.4 reject handling) are not in our loaded corpus.** The governing NAS specification TS 24.501 (under CT1's remit) lies outside the loading scope of the RAN-domain corpus (38.xxx). The text of these two clauses was therefore quoted by **directly downloading** the authoritative public release (the 3GPP frozen 24.501 as published by ETSI), marked `[web:]`. The public standard text does not substitute for the spec text loaded in the corpus, but in this case it serves as the key evidence filling the corpus gap — we state this honestly.
- What the corpus contributed is the **factual basis of the scenario, the meaning of #43, and the sync mechanism** (§10.1.2.2 / §10.1.3.2 / §10.1.6.x + the network-side ACCEPT alignment), plus **parts of 24.501 §6.4.3.2/6.4.3.3/6.4.3.5 embedded** in the conformance text. Note, however, that the corpus's §6.4.3.5 quotations cover only the collision cases (b/c); items a)/d), where the registration step is written, and the reject clause §6.4.3.4 were supplemented from the authoritative public release.
- We confirmed the verdict is **identical in both the Rel-15 baseline and the latest Rel-18 text** (trigger m)'s referenced clauses, and the absence of registration in §6.4.3.4). The conclusion does not diverge by release.
- Independent external cross-verification (authoritative public release + supplementary tutorial material) found **no conflict** with this verdict. Tutorial-class supplementary material is non-authoritative and was not used as a basis for the verdict (authoritative standard text only).
- One practical caveat: if the DUT's Registration Request is, in its implementation, sent because it coincides with **another independent trigger** (Case D, or another item of §5.5.1.3.2), then filling in that IE is legitimate. The "no obligation" in this answer is limited to **treating the #43-reject alone as the trigger.**
