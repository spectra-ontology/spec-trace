# SPECTRA Answer — T1=5s / RRCRelease behaviour in the 38.523-1 §11.4.1 de-registration-after-emergency-release test (R5-253194)

> Retrieval method: the 3GPP TS/CR body text was searched with semantic embeddings (vector similarity), and the CR↔Spec↔Section↔revision-chain structure and relations were cross-verified against a Knowledge Graph. Both paths were used together. The governing NAS clause (24.501 §5.5.2.1) is not part of the loaded RAN5 test-spec corpus (the 38.5xx series), so an authoritative public copy was used as supporting evidence for cross-checking.

---

## Conclusion (one-line bottom line)

- **Q1 — T1=5s is not a value derived from any normative spec; it is a test-implementation guard/wait time during which the SS (System Simulator) waits to see "whether the UE will autonomously do something after the emergency call is released."** Nowhere in the R5-253194 CR body is there any NAS/RRC normative basis justifying 5 seconds, and because 24.501 §5.5.2.1 leaves de-registration as a **"may" (optional)** behaviour rather than mandating it, the SS only needs an arbitrary observation window that is "long enough."
- **Q2 — "The UE cannot do it until 5 seconds elapse and may only do it after RRCRelease" is not an accurate reading.** The final version of R5-253194 does **not** put de-registration into the main sequence; it moves it out into a **separate parallel/optional table (11.4.1.3.2-3)** and handles it as something that "may take place *in parallel* to step 3BA." In other words, the UE's de-registration is **not forbidden-then-allowed; it is an optional behaviour that the SS accepts as PASS whether or not it occurs during the T1 window.** RRCRelease (3EA) is not a *precondition* for de-registration; it is a cleanup signal by which the SS tears down the NAS connection and moves on to the next stage (re-registration) when the UE did not de-register.
- **Q3 — Even without RRCRelease, there is no obligation that the UE "must remain emergency-registered."** 24.501 §5.5.2.1 specifies de-registration as **"may" (optional)** and conditions it on the UE **"being in or moving to a suitable cell."** Therefore (i) de-registration is not mandatory, and (ii) if performed, the suitable-cell precondition must hold. RRCRelease is the trigger that sends the UE to RRC_IDLE and thereby enables cell reselection (acquiring a suitable cell), so in the absence of RRCRelease, "not de-registering and remaining registered for emergency services" is **one of the permitted conformant behaviours** — not a mandated requirement.

---

## Terminology decomposition (to avoid confusion)

The three questions blend several distinct things into one word; we separate them first.

- (i) **"de-registration *shall* be performed (mandatory)"** vs **"*may* be performed (optional, may)"** — 24.501 §5.5.2.1 is the latter. This single word ("may") decides the answers to Q2 and Q3.
- (ii) **"T1 timer (= SS-side test behaviour)"** vs **"NAS/RRC normative timer (T3xxx family)"** — T1 is not a protocol timer defined by the spec; it is an SS-side wait timer introduced by the test case itself.
- (iii) **"*when* the UE sends de-registration (NAS procedure)"** vs **"*when* the SS observes/accepts it (test sequence placement)"** — the appearance in the question that "it is only done after RRCRelease" comes from misreading the SS observation placement of (iii) as a UE obligation of (i).

---

## Case-by-case analysis

### Case A — Basis of T1 = 5 seconds (Q1)

The reason-for-change of CR R5-253194 contains **no quantitative NAS/RRC basis whatsoever justifying 5 seconds.** The only normative sentence the CR cites concerns the *optionality* of the behaviour:

> *"UE may perform de-registration procedure after emergency call is released at step 3A of emergency services test case 11.4.1. Currently this is not handled."* [R5-253194, Reason for change]

> *"TS 24.501, clause 5.5.2.1: When upper layers indicate that emergency services are no longer required, the UE if still registered for emergency services, may perform UE-initiated de-registration procedure followed by a re-registration to regain normal services, if the UE is in or moves to a suitable cell."* [R5-253194, Reason for change]

The key point here is that the behaviour is **"may" (a UE implementation choice).** Whether the UE sends de-registration, sends a PDU session release, or sends nothing at all **may differ per implementation, and the timing may differ as well.** The SS must **"observe for a sufficient time"** this non-deterministic (implementation-dependent) autonomous behaviour, and that observation window was set as a 5-second `T1`. In the main sequence body as well, the 5 seconds appears purely as an SS action:

> *"3B  SS starts timer T1 = 5 seconds."* / *"3BA  Timer T1=5 seconds expires."* [38.523-1 §11.4.1.3.2, Table 11.4.1.3.2-1]

Sibling CRs in the same emergency family state the same design intent even more directly — i.e., the problem was that "the UE may autonomously send de-registration too early/unexpectedly, catching the SS off guard (test failure)":

> *"UE may perform de-registration immediatedly which is unexpected by SS. ... Add note so that SS allowed UE to send de-registration request immediatedly ..."* [R5-243594, Reason/Summary of change — sibling TC 11.5.5]

> *"UE may perform UE-initiated de-registration procedure after step 10A emergency PDU session release. ... Added optional Step ... to handle the DEREGISTRATION REQUEST from UE."* [R5-227575, Reason/Summary of change — sibling TC 11.4.5]

**Verdict:** T1=5s is **not a normatively derived value; it is a test-implementation guard time for observing and accommodating optional, implementation-dependent UE behaviour.** The exact derivation of the 5-second figure is not documented in the CR body (see Honest gap below). Consistently with the sibling CRs, the purpose is to ensure that "a conformant UE that autonomously sends de-reg/PDU-release does not unfairly fail" — per the CR's *Consequences if not approved*: *"A conformant UE may unfairly fail the test case."* [R5-253194].

### Case B — Is it "no de-reg until T1, and only after RRCRelease" (Q2)?

Re-checking the question's premise against the structure of the final CR shows that **the premise is partially off.** The *Summary of change* of R5-253194 does not force de-registration into the main flow; it handles it by **adding a separate parallel table**:

> *"Summary of change: 1. Updated main behavior table 11.4.1.3.2-1. 2. Added specific message contents tables 11.4.1.3.2-3 and 11.4.1.3.2-4."* [R5-253194]

That newly added table 11.4.1.3.2-3 is precisely the DEREGISTRATION sequence, and the EXCEPTION in the main table explicitly states that it **"may take place" in parallel to 3BA**:

> *"EXCEPTION: ... In parallel to step 3BA below, the steps specified in Tables 11.4.1.3.2-3 and 11.4.1.3.2-4 may take place."* [38.523-1 §11.4.1.3.2, Table 11.4.1.3.2-1]

> *(Table 11.4.1.3.2-3, Parallel Behaviour)* *"1  The UE transmits a DEREGISTRATION REQUEST message with De-registration type IE set to 'Normal de-registration'."* → *"2  The SS transmits a DEREGISTRATION ACCEPT message."* [38.523-1 §11.4.1.3.2]

So de-registration is **not "forbidden for 5 seconds → then allowed"** but rather **"an optional parallel behaviour that may or may not arrive during the 5-second window."** (This parallel-table + EXCEPTION structure is the final form confirmed directly in the §11.4.1 body. The internal table structure of intermediate revisions was not body-verified within the scope of this retrieval, so we do not assert any design-evolution narrative about "how it was initially" — see Honest gap below.)

What, then, is **the role of RRCRelease (3EA)?** If the UE did not send de-registration (or only did a PDU release), the SS must tear down the NAS signalling connection and send the UE to RRC_IDLE so that the next stage (re-registration on NR Cell 1, steps 9A3 onward) can proceed cleanly:

> *"3EA  The SS transmits an RRCRelease message."* (`NR RRC: RRCRelease`) → *"3EB  SS configures the RA Response."* → *"9A3 – 9A21a1  Steps 2-20a1 of Table 4.5.2.2-2: Registration procedure for initial registration ... are performed on NR Cell 1."* [38.523-1 §11.4.1.3.2]

**Verdict:** RRCRelease is not a *prior precondition* for de-registration. De-registration is allowed as parallel/optional within the T1 window. RRCRelease is (regardless of whether de-reg occurred) a **test-progression cleanup signal** that sends the UE to IDLE, tears down the connection, and moves things to the re-registration stage. No mandated ordering of "de-reg only possible after RRCRelease" exists normatively.

### Case C — Without RRCRelease, must the UE remain emergency-registered (Q3)?

The governing clause is 24.501 §5.5.2.1, and two qualifying words are decisive.

> *"... the UE if still registered for emergency services, **may** perform UE-initiated de-registration procedure ... if the UE is in or moves to a **suitable cell**."* [24.501 §5.5.2.1, quoted verbatim in R5-253194; web cross-checked]

- **(1) "may" → de-registration is not an obligation.** Therefore the causal chain "no RRCRelease, so no de-reg possible → must remain" does not hold. *Not* performing de-reg is itself already a conformant option.
- **(2) "if the UE is in or moves to a suitable cell" → de-reg presupposes acquiring a suitable cell.** Immediately after emergency call release, the UE may still be in connected state, tied to the emergency cell. RRCRelease is the trigger that sends the UE to RRC_IDLE and thereby enables **cell reselection (moving to a suitable cell).** Without RRCRelease, the suitable-cell precondition is hard to satisfy, so the UE **not de-registering and keeping its registration is in fact more consistent with §5.5.2.1.**

Therefore the intuition behind Q3 — "without RRCRelease, the UE does not de-register and remains registered for emergency services" — is a **permitted conformant behaviour.** With one correction of wording: the accurate statement is not "it *must* remain (mandatory)" but "it *may conformantly* remain (permitted)." De-registration is something the UE implementation may optionally do (when a suitable cell is available); RRCRelease does not create any such obligation.

The 24.501 NAS body (the de-reg trigger arises only when the upper layers indicate that "emergency is no longer required") points in the same direction — while the emergency call is alive, the de-reg trigger itself does not exist.

---

## Comparison table

| Question | Core verdict | Basis |
|---|---|---|
| Q1 Basis of T1=5s | Not normatively derived — a **test guard time** for observing optional autonomous UE behaviour | R5-253194 Reason ("may ... Currently not handled") + §11.4.1.3.2 table (SS-only action) + sibling CRs R5-243594/R5-227575 design intent |
| Q2 De-reg only after RRCRelease? | No — de-reg is **parallel/optional at T1**; RRCRelease is an IDLE-transition/cleanup signal | §11.4.1.3.2 EXCEPTION ("in parallel to 3BA ... may take place") + Table 11.4.1.3.2-3 + Summary of change |
| Q3 Must remain if no RRCRelease? | Remaining is **conformant** (not an obligation). De-reg is "may" + suitable-cell conditional | 24.501 §5.5.2.1 "may" + "suitable cell"; RRCRelease as the IDLE→reselection trigger |

**Bottom line:** All three questions share a single root — *under 24.501 §5.5.2.1, de-registration is not mandatory but an optional behaviour the UE "may perform if in a suitable cell."* Hence (Q1) the SS provides not a prescribed correct-answer instant but a 5-second window to wait for autonomous behaviour, (Q2) it accepts that behaviour as parallel/optional rather than in the main flow, and (Q3) the UE omitting that behaviour is also conformant.

---

## Standards-structure cross-verification

The position and relations of CR R5-253194 are confirmed in the Knowledge Graph as follows (1:1 consistent with the quoted body text).

- **Target spec / clause:** R5-253194 → modifies the §11.4.1 conformance test section of 38.523-1. The clause title is *"5GMM-REGISTERED.NORMAL-SERVICE / 5GMM-IDLE / Emergency call / ... / Network failing the authentication check (5G AKA)"* — identical to the §11.4.1 title in the CR body.
- **CR metadata:** CR number 5008 (rev 2), Current version 19.0.0, **Target Release = Rel-19**, Category F (correction), Source = Qualcomm Incorporated, Work item code = `TEI15_Test, 5GS_NR_LTE-UEConTest`, meeting = RAN5#107 (Malta, 2025-05).
- **Revision chain:** **R5-252598 → R5-253081 → R5-253194** (R5-253194 = revision of R5-253081, whose root is R5-252598) — confirmed via the revision relations of the three TDocs. The final approved version (R5-253194) can be cited as CR body text, but the intermediate working versions (R5-252598, R5-253081) are **preserved only as meeting contributions (TDocs)**: only the §11.4.1 clause structure (Test Purpose, conformance requirement, table titles) is confirmed for them, and **the test-procedure step rows (de-reg/T1/RRCRelease) are not confirmed.** Therefore there is no basis to determine "how the step structure changed across revisions"; no design-evolution narrative is asserted, and the assessment of the step structure is limited to the current §11.4.1 body reflecting the final version.
- **Sibling TCs:** At the same meeting and on the same 24.501 §5.5.2.1 basis, 11.4.5 (R5-253195), and earlier 11.4.5 (R5-227575) and 11.5.5 (R5-243594), were modified with the same pattern (accommodating optional UE de-reg) → "unhandled optional de-reg after emergency release" was a defect common to the emergency family.
- **Referenced but out-of-corpus clauses:** 24.501 §5.5.2.1 / §5.4.1.3.7 and the 23.501 emergency clauses are not part of the loaded RAN5 test-spec corpus (the 38.5xx series). The §5.5.2.1 body was grounded only on the range quoted verbatim by the CR plus cross-checking against an authoritative public copy (Honest gap).

---

## External (public standards) cross-check

- **24.501 §5.5.2.1 wording confirmed:** search results from public standards mirrors (tech-invite / itecspec, unofficial mirrors of the official 3GPP TS 24.501 body) match the CR quotation **down to the exact wording** — *"When upper layers indicate that emergency services are no longer required, the UE if still registered for emergency services, may perform UE-initiated de-registration procedure followed by a re-registration to regain normal services, if the UE is in or moves to a suitable cell."* [web: 24.501 §5.5.2.1, tech-invite/itecspec mirror]. The qualifying words "may" and "suitable cell" are confirmed as-is, supporting the Q3 verdict.
- **Absence of a normative basis for T1=5s confirmed:** no normative quantitative basis defining or justifying "T1=5 seconds" was found in the public 38.523-1/38.508-1 copies or in general search — consistent with the Q1 "test guard time" verdict (no counter-evidence).
- **Authority classification:** 24.501/38.523-1 are official 3GPP/ETSI standards (authoritative). Patents that also surfaced in search (US10887749B1 etc.) and vendor wikis are **non-authoritative** and were not used as evidence in this answer (not treated as a conflict with the standards). There was no conflict between the authoritative standards and the CR quotations.

---

## Honest gap

- **The exact derivation of T1=5s is not confirmed in any document.** Neither the R5-253194 body, the 38.508-1 generic test framework, nor public search contains a quantitative formula for "why 5 seconds." This answer's "observation guard time" verdict is an **inference** from (a) the "may" in §5.5.2.1 (non-deterministic UE behaviour), (b) the fact that T1 in the table is a pure SS action, and (c) the explicit design intent of the sibling CRs (the SS must accommodate autonomous de-reg) — there is no sentence in the CR explicitly justifying the 5 seconds.
- **The bodies of 24.501 §5.5.2.1 / §5.4.1.3.7 and the 23.501 emergency clauses are outside the RAN5 test-spec corpus** (they are CT1/SA2 specs). §5.5.2.1 was grounded only up to the CR verbatim quotation plus authoritative public-copy cross-check, and the body of the **23.501** emergency registration/release clauses could not be directly quoted (public search confirmed only the general §5.16.4 emergency-registration material). Since 23.501 deals with emergency-registration system behaviour rather than directly specifying the "when/how" of de-registration, the primary basis for this question (de-reg trigger and conditions) is 24.501 §5.5.2.1.
- **Direct fetch of some public copies was blocked:** some standards mirrors could not be fetched directly in this environment due to TLS inspection (substituted with search snippets and reachability of the official PDFs), so exact wording was cross-checked against search-result snippets.
- **Intermediate working versions confirmed only at clause-structure level:** unlike the final approved version, the intermediate working versions (R5-252598, R5-253081) are not in the corpus as CR body text and survive only as meeting contributions; only the §11.4.1 clause structure and table titles are confirmed, and the test-procedure step rows are not. Step-level design evolution is therefore outside the evidence scope, and the step-structure assessment is limited to the current §11.4.1 body of the final version (no assertion is made about step placement in the intermediate working versions).
- **Index-version limitation:** the search index is the latest snapshot. 38.523-1 received this CR in Rel-19 (v19.x), and this answer is based on R5-253194 (rev 2, current version 19.0.0). Future revisions may change the procedure again.
