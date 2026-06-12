# SPECTRA Answer — NR NTN T430 epochTime: serving/neighbour SFN interpretation of the EpochTime IE and SFN wrap-around conversion

> Retrieval method: the 3GPP TS/TR spec bodies were searched with semantic embeddings (vector similarity), and the standards structure and relationships (IE definition location, T430 start rules, cross-spec references, introducing release) were cross-checked against the Knowledge Graph. Both paths were used together; agreements and the introduction background were checked separately in the CR and contribution-document partitions, and the frame structure in the RAN1 PHY spec body. The key verdicts were independently cross-verified against public 3GPP/ETSI material (see "External cross-verification" below).

---

## Conclusion (one-line bottom-line)

- **Q4 (neighbour interpretation and decision): the asker's interpretation matches the spec intent.** Viewing "nearest SFN" as "the shortest-path distance on 10240 ms" and deciding with a ±5120 threshold conforms exactly to the field description ("nearest") and to the RAN2 agreement that produced that wording (neighbour = the nearest side regardless of past/future, Option 2).
- **Q2 (serving semantics): the asker's interpretation is correct *at frame (SFN) granularity*, but the conclusion that "the epoch can never be in the past" is an *over-extension*.** The rule in the field description is *"the field **sfn** indicates the current SFN or the next upcoming SFN"* — i.e., it only stipulates that the **`sfn` field (frame granularity)** is *the same frame as the reception frame (current SFN) or a later frame*. The `subFrameNR` field (0..9, 1 ms) in the same IE carries *no direction constraint*. Therefore, when the epoch SFN is the "current SFN" (= identical to the reception frame), the epoch's subframe can *precede* the reception subframe, so an epoch that is **a few ms in the past** is permitted by the spec. "Cannot be in the past" elevates a frame-level rule into an absolute guarantee at subframe granularity, which goes beyond the spec wording.
- **Q3 (serving sign-only decision): the asker's logic does not match the spec intent (the reviewer's objection is correct).** When `timeDiff` (= receivedTime − epochTime) is a *small positive number* (the legitimate case where the epoch precedes reception by a few ms within the same SFN), the sign-only logic treats it as a "next-upcoming wrapped into the next cycle" and applies a **−10240 correction**, pushing the epoch *10.24 seconds into the future* — which puts the T430 start reference off by one cycle (up to 10.24 s) (counterexample = Case C). The correct approach is not to look at the sign of a single `timeDiff` collapsed into ms, but to **first interpret the `sfn` field by its own rule (current-or-next-upcoming, frame granularity)** and then place `subFrameNR` within that frame. The neighbour-cell ±5120 (nearest) is a different rule (*regardless of past/future*), so porting it to the serving cell is not the answer either.
- **Q1: the (B) neighbour implementation matches, but the (A) serving implementation (sign-only + the "cannot be in the past" premise) is a *partial mismatch* due to the defects in Q2 and Q3 above.**

---

## Terminology breakdown (to avoid confusion)

Three things often get mixed up when dealing with EpochTime. Let us separate them first.

- **(i) The time granularity of the epoch — two separate fields (SFN + subframe)**: EpochTime is *not a single SFN value but a pair of two fields* — `sfn` (frame number) and `subFrameNR` (the subframe within that frame). The spec defines the epoch as *"the starting time of a DL sub-frame, indicated by a SFN and a sub-frame number"* [38.331 §6.3.2 (EpochTime field descriptions)]. The asker's `epochTime = sfn × 10 + subframeNR` *ms conversion is arithmetically correct*, but this summation **collapses the frame granularity and the subframe granularity into a single ms value**. Since the serving-cell rule places *different* constraints on the two (frame = current-or-next / subframe = unconstrained), the distinction is lost after summation, which is what produces the defect in Q3 (Case C below).
- **(ii) The reference frame of "where the message is received"**: the field description interprets `sfn` relative to "the frame where the message indicating the epochTime is *received*". The asker's `receivedTime` (the reception subframe in ms) corresponds to this reference.
- **(iii) Wrap-around correction (10240 ms)**: SFN is 0..1023 (1024 frames), so the ms axis repeats over 0..10239. The asker's premise that simple subtraction fails to capture the actual temporal relationship when a cycle boundary is crossed is itself correct — but *how* to correct differs between serving and neighbour.

---

## Case-by-case analysis

### Spec passages serving as evidence (verbatim)

**EpochTime IE definition (ASN.1) — two separate fields** [38.331 ASN.1 IE=EpochTime-r17]:

```asn1
EpochTime-r17 ::= SEQUENCE {
    sfn-r17           INTEGER (0..1023),
    subFrameNR-r17    INTEGER (0..9)
}
```

`sfn` is 0..1023 (→ 1024 frames → 10240 ms wrap), `subFrameNR` is 0..9 (→ 10 subframes per frame, subframe = 1 ms). The key point: the serving/neighbour rules in the field description are **attached to the `sfn` field**, and there is *no* direction rule for `subFrameNR` [38.331 §6.3.2; ASN.1 IE=EpochTime-r17].

**EpochTime field description (serving vs neighbour asymmetry)** [38.331 §6.3.2 (EpochTime field descriptions)] — verbatim:

> *"For serving cell, it indicates the current SFN or the next upcoming SFN after the frame where the message indicating the epochTime is received. For neighbour or target cell, it indicates the SFN nearest to the frame where the message indicating the epochTime is received."*

(Here "it" = the field that the field description is describing, i.e. **`sfn`**. The asker also correctly attributed it to the `sfn` field in the original question, quoting *"the field sfn indicates the current SFN or the next upcoming SFN"*.)

**Frame structure (10 subframes / frame, 1024-frame wrap)** [38.211 §4.3.1] — verbatim:

> *"Downlink, uplink, and sidelink transmissions are organized into frames with [10 ms] duration, each consisting of ten subframes of [1 ms] duration. ... Each frame is divided into two equally-sized half-frames of five subframes each with half-frame 0 consisting of subframes 0 – 4 and half-frame 1 consisting of subframes 5 – 9."*

**T430 start rule (the epoch subframe is the timing reference)** [38.331 §5.2.2.4.21 (Actions upon reception of SIB19)] — verbatim:

> *"Upon receiving SIB19 in an NTN cell, the UE in RRC_CONNECTED shall: start or restart T430 for serving cell with the timer value set to ntn-UlSyncValidityDuration for the serving cell from the subframe indicated by epochTime for the serving cell."*

---

### Case A — Serving cell interpretation (Q1-A, Q2)

For the serving cell, the field description says *"[the field sfn] indicates the current SFN or the next upcoming SFN after the frame where the message ... is received"* [38.331 §6.3.2]. What this sentence constrains must be read precisely, granularity by granularity:

- **What is constrained = the `sfn` field (frame granularity).** The two candidates ("current SFN" / the subsequent "next upcoming SFN") concern the *frame number*. That is, the epoch's **frame** is *the same as (current) or later than (next upcoming)* the reception frame — there is no candidate that points to a frame earlier than reception.
- **What is not constrained = the `subFrameNR` field (subframe granularity).** The `subFrameNR (0..9)` in the same IE has no direction rule. In the branch where the epoch SFN is the "current SFN" (the same frame as reception), `subFrameNR` can be *smaller* than the reception subframe, in which case the epoch is a point **a few ms earlier (in the past)** than the reception instant within that frame — and this is permitted by the spec wording.
- **Why the "current SFN" branch permits a sub-frame past — the two-branch structure of the wording is decisive.** The field description distinguishes two branches: *"the current SFN **or** the next upcoming SFN **after the frame** where the message ... is received"*. The forward qualifier *"after the frame ... received"* attaches **only to (B) "next upcoming SFN"** — (A) "current SFN" *is the reception frame itself*, so the qualifier "after that frame" cannot grammatically apply to it. Therefore, in branch (A) the epoch frame = the reception frame, and if the unconstrained `subFrameNR` is earlier than the reception subframe, the epoch lies *a few ms in the past within the same SFN*. This also arises naturally in practice: if the network indicates the SIB transmission subframe as the epoch and the UE finishes decoding a few subframes later, the epoch is an *earlier subframe* of the same SFN (= a few ms before reception). (The NOTE in the T430-expiry clause — *"... can be from the subframe indicated by epochTime **and optionally before the subframe indicated by epochTime**"* [38.331 §5.2.2.6] — is a separate degree of freedom allowing the *UL sync acquisition time* to lie before the epoch subframe; it is not evidence about the epoch-vs-reception ordering, so it is not used as direct evidence for this verdict.)

That this asymmetry (serving: the frame is current-or-next; neighbour: nearest) is *intentional* is confirmed by the RAN2 agreement:

> *"For the serving cell, the configured epochTime refers to the current SFN or the next upcoming SFN ... Observation 4: When the UE receives the NTN-config (incl. UL sync info) of the serving cell, the UE starts the validity timer T430 at the SFN/subframe indicated by the epochTime **in the future** (i.e., Option 1)."* [R2-2209799, RAN2#119bis-e, ai=NTN, type=discussion, release=Rel-17]

The *"in the future (Option 1)"* in this contribution is a **design choice (an Observation)** — serving puts the timer reference on the "future side" (Option 1), while neighbour uses the "nearest past/future" (Option 2) — contrasted at the *frame/SFN level*. The normative field description merely translated this design into `sfn` = "current-or-next"; it was not written as a guarantee that *at subframe granularity the epoch can never precede reception*. In other words, "Option 1 = future side" is a frame-selection rule, not an ms-level inequality.

→ **Q2 verdict: match at frame granularity; making "cannot be in the past" absolute is an over-extension (partial mismatch).** Reading "current SFN or next upcoming SFN" as "the epoch frame is the same as or later than the reception frame" is correct. But extending it to "the epoch can never be in the past" *down to subframe granularity* elevates a rule attached only to the `sfn` field into an ms-level guarantee for the epoch as a whole, going beyond the spec wording — in the current-SFN branch the epoch can be a few ms in the past.

→ **Q1-A verdict: partial mismatch.** The *directionality* is correct at frame granularity, but the "cannot be in the past" premise and the sign-only implementation built on it (Q3) break in the current-SFN sub-frame-past case.

### Case B — Neighbour cell interpretation (Q1-B, Q4)

For neighbour/target, the field description says *"the SFN nearest to the frame where the message ... is received"* [38.331 §6.3.2]. "Nearest" does not restrict the direction (past/future); it only stipulates *distance*. The same RAN2 agreement states this explicitly:

> *"When the UE receives the NTN-config (incl. UL sync info) of the neighbor cells, the UE assumes to start the validity timer T430 at the SFN/subframe indicated by the epochTime **in the past or in the future (dependent on which is the nearest one)** (i.e., Option 2)."* [R2-2209799, RAN2#119bis-e, ai=NTN, type=discussion, release=Rel-17]

On a 10240 ms cycle, the "nearest" point is precisely the **shortest-path distance**, and the dividing point is the half-cycle (5120 ms). If `|timeDiff| > 5120`, the cycle in the opposite direction is closer, so applying a ±10240 correction according to the sign is the standard modular-distance way of implementing "nearest".

→ **Q4 verdict: match.** The interpretation "nearest = the SFN at the shortest-path distance on 10240 ms" and the ±5120-threshold decision conform to the spec wording ("nearest") + the RAN2 agreement ("past or future, whichever nearest").

→ **Q1-B verdict: match.** The asker's four neighbour cases (0<diff≤5120 past / −5120≤diff≤0 future / diff<−5120 previous cycle +10240 / diff>5120 next cycle −10240) are consistent with the ±5120 split. (Which case the boundary value 5120 is assigned to is an implementation choice the spec does not stipulate — see Honest gaps below.)

### Case C — The defect in the serving-cell "sign-only" decision (Q3)

The asker's logic (convention from the original question: `timeDiff = receivedTime − epochTime`, positive = epoch in the past): for serving, no correction if `timeDiff ≤ 0` (the epoch is the same instant or in the future); if `timeDiff > 0` (the epoch *appears* to be in the past), treat it as a "next-upcoming wrapped into the next cycle" and apply a **−10240 correction** (no ±5120 threshold used).

**Why this is defective — counterexample.** Suppose the message is received in subframe 7 of SFN n, and the network indicates the epoch as **subframe 2 of SFN n** (same SFN, an earlier subframe). Under the field rule, the epoch `sfn` (= n) = the SFN of the reception frame (= n), so this is the *"current SFN"* branch, and since `subFrameNR (2)` is unconstrained, this is **legal under the spec**.

- `receivedTime = n×10 + 7`, `epochTime = n×10 + 2` → `timeDiff = 7 − 2 = +5` (positive).
- **Sign-only logic**: `timeDiff > 0` → −10240 correction → places the epoch `10240 − 5 = 10235 ms` in the *future* (the next-upcoming of the next cycle). ✗
- **Actual (spec)**: epoch `sfn` = reception SFN → "current SFN" → the epoch is subframe 2 of the *current frame* = **5 ms in the past** relative to reception (subframe 7). No wrap. ✓

That is, sign-only rests on the (over-extended) premise that "the epoch cannot be in the past" and forces *every* positive `timeDiff` into a next-cycle wrap, thereby misjudging the **legal current-SFN 5 ms past** above as *10.235 seconds in the future*. Since T430 starts *"from the subframe indicated by epochTime"* [38.331 §5.2.2.4.21], this misjudgment shifts the timer start (and hence expiry) by up to one cycle (10.24 s).

**Root cause — a representation that collapses granularity.** `timeDiff = receivedTime − epochTime` is a difference taken after *merging frame and subframe into a single ms value* via `sfn×10 + subFrameNR`. But the serving rule attaches "current-or-next" only to `sfn` (the frame) and leaves `subFrameNR` free. Once merged, "a sub-frame past within the current SFN" and "a next-upcoming that must roll into the next cycle" *cannot be distinguished by the sign of the merged value alone*. Hence neither sign-only nor a fixed ±5120 threshold (borrowed from neighbour) is the right tool.

**The correct method (it is deterministic).** Interpreting the **`sfn` field by its own rule before merging** removes the ambiguity:
- epoch `sfn` == reception SFN → *current SFN* → epoch frame = the current frame. Place `subFrameNR` within it (it may be before or after reception). No wrap.
- epoch `sfn` != reception SFN → *next upcoming SFN* → the first frame after the reception frame at which that SFN value occurs (future). Place `subFrameNR` within that frame.

Branching first at frame granularity in this way and then applying the subframe determines the absolute time of the epoch uniquely — no sign test and no ±5120 threshold is needed.

→ **Q3 verdict: mismatch.** Logic that decides serving-cell wrap from the sign of a single `timeDiff` alone corrupts a legal epoch lying a few ms in the past within the current SFN into 10.24 s in the future, and therefore does not match the spec intent (the reviewer's objection is correct). The correct decision is to interpret the `sfn` field as current-or-next-upcoming at frame granularity and then apply `subFrameNR`; the neighbour-cell ±5120 (nearest) must not be ported to serving either (it is a different rule).

---

## Comparison table

| Question | Asker's interpretation/logic | Spec basis | verdict |
|---|---|---|---|
| Q1-A serving directionality & implementation | epoch = present/future (no past), sign-only wrap | `sfn` = "current/next upcoming SFN" (frame granularity) [38.331 §6.3.2]; `subFrameNR` unconstrained [ASN.1 EpochTime-r17] | Partial mismatch (frame OK, subframe past ignored) |
| Q1-B neighbour directionality & implementation | nearest regardless of past/future, ±5120 | "SFN nearest" [38.331 §6.3.2]; "past or future, whichever nearest" [R2-2209799] | Match |
| Q2 serving semantics | "present/near future, cannot be past" | frame granularity = OK; "no past" over-extends the `sfn` rule to subframe/ms level [38.331 §6.3.2] | Partial mismatch (over-extension) |
| Q3 serving decision | sign only (no threshold) | corrupts a legal current-SFN sub-frame past into 10.24 s future via −10240; interpreting the `sfn` field first is the right answer [38.331 §6.3.2; ASN.1 EpochTime-r17] | Mismatch |
| Q4 neighbour decision | ±5120 shortest-path | "nearest" = modular shortest distance [38.331 §6.3.2] | Match |

**Bottom-line:** For the neighbour cell (Q1-B, Q4) the asker's logic matches the spec. For the serving cell (Q1-A, Q2, Q3) it is correct *at frame granularity*, but as a result of over-extending the "current-or-next" rule — which attaches only to the `sfn` field — into an ms-level "no past" guarantee for the epoch as a whole, the sign-only decision corrupts a legal sub-frame past within the same SFN into one cycle (up to 10.24 s) in the future. The correct implementation is to interpret the `sfn` field first at frame granularity (current-or-next-upcoming) and then apply `subFrameNR`.

---

## Standards-structure cross-verification

- **IE definition location and granularity**: EpochTime is a 38.331 RRC IE with the structure `SEQUENCE { sfn-r17 (0..1023), subFrameNR-r17 (0..9) }`, expressing the epoch with *two separate fields* (SFN + subframe) [38.331 ASN.1 IE=EpochTime-r17]. The serving/neighbour rules in the field description are attributed to *the `sfn` field*, and `subFrameNR` has no direction rule [38.331 §6.3.2]. This field separation is the crux of the Q2/Q3 analysis.
- **Connection to T430**: EpochTime is not used on its own; it is the *start reference* for T430. Upon receiving SIB19, the UE shall *"start or restart T430 ... from the subframe indicated by epochTime"* [38.331 §5.2.2.4.21]. This is precisely why the UE must convert the absolute time of the epoch subframe accurately relative to the reception time — if the wrap correction is wrong, the start of T430 (and hence its expiry) is off by one cycle (up to 10.24 s) (the sign-only defect of Case C produces exactly this error).
- **Consequence of T430 expiry**: *"if T430 for serving cell expires ... inform lower layers that UL synchronisation is lost; acquire SIB19"* [38.331 §5.2.2.6]. The NOTE in the same clause — *"... from the subframe indicated by epochTime and optionally before the subframe indicated by epochTime"* — reconfirms that the epoch subframe is the reference for UL sync acquisition [38.331 §5.2.2.6].
- **Higher-level procedural context (38.300)**: an NTN UE shall *"compute the RTT between UE and the RP based on the GNSS position, the ephemeris, and the Common TA parameters ... and autonomously pre-compensate"* [38.300 §16.14.2.2]. epochTime is the reference time for *when* this ephemeris/Common TA assistance is valid, so an epoch conversion error translates directly into an error in the TA pre-compensation reference time.
- **Frame-structure authority (38.211)**: 1 frame = 10 subframes, half-frame 0 (0–4)/1 (5–9), SFN 0..1023 → 10240 ms period [38.211 §4.3.1]. This is the source of the asker's 10240 ms wrap premise.
- **Introducing release (authoritative metadata)**: the IE/field names are uniformly tagged `-r17` (`EpochTime-r17`, `sfn-r17`, `subFrameNR-r17`), indicating that the NTN epoch feature was introduced in **Release 17** [38.331 ASN.1 IE=EpochTime-r17]. Public 3GPP material also confirms `-r17 = Release 17` (see External cross-verification below). However, the version history of "from exactly which frozen version onward" cannot be pinned down directly from a single corpus snapshot, so it is placed under Honest gaps.

---

## External cross-verification

The key verdicts were independently checked against public 3GPP/ETSI material.

- **Confirmed**: `EpochTime-r17`/`sfn-r17 (0..1023)`/`subFrameNR-r17 (0..9)` and `-r17 = Release 17` — public search results confirm the same structure and release. The points that the field description stipulates serving = "current/next upcoming SFN" and neighbour = "nearest" for *the `sfn` field*, and that `subFrameNR` carries no such direction rule, also match the public 38.331 text — this is the basis for the Q2/Q3 corrections.
- **Confirmed**: that T430 starts *"from the subframe indicated by epochTime"* upon SIB19 reception with the timer value set to `ntn-UlSyncValidityDuration`, and that upon expiry UL sync becomes invalid → SIB19 must be re-acquired — public NTN explainers/summaries describe the same.
- **Authoritative original text partially blocked**: the *exact wording* of the serving/neighbour field description could not be re-quoted directly from a public PDF, because the ETSI 138.331 V18 PDF/mirrors returned 403. However, the identical wording exists byte-identical in the TS IE body within the corpus and in multiple CRs (versions across several meetings), so the authoritative basis is satisfied. The attempts are recorded in the audit trail.

---

## Honest gaps

- **Maximum forward distance of "next upcoming" unspecified**: the serving definition only states that the epoch `sfn` is "current or next upcoming"; 38.331 does not numerically limit how far into the future (up to 1023 frames ≈ 10.23 s) the next-upcoming may be placed (a network-configuration matter). However, the correct decision (interpreting the `sfn` field first) is deterministic regardless of this distance.
- **Tie and boundary cases**: when epoch `sfn` == reception SFN and `subFrameNR` == reception subframe (difference 0), or for neighbour when `|timeDiff| = 5120` (exactly the half-cycle, equidistant in both directions), the assignment is an implementation/operational choice the spec does not numerically stipulate. It is common to assume the network avoids configuring such boundary epochs, but that is inference, not corpus evidence.
- **RAN1 NTN timing text not directly quoted**: 38.213 clause 4.2/4.3 (K_offset, TA application) and the ta-Common-related details of 38.211 §4.3.1 were not directly quoted in this analysis beyond confirming the frame structure — interpreting the epoch SFN/subframe itself is an RRC (38.331) layer matter, so this suffices, but examining TA application timing would require separately consulting the 38.213 text.
- **RAN4 NTN requirements (38.108/38.133) timing accuracy**: TA adjustment accuracy requirements were found in 38.133 (e.g., §7.3C TA adjustment accuracy) but do not bear directly on the epoch SFN interpretation itself, so they were not quoted in the body. The quantitative boundary of whether an epoch conversion error leads to an actual TA accuracy violation requires separately consulting the RAN4 text.
- **Release version history**: that the NTN epoch was introduced in Rel-17 is confirmed by the `-r17` tags + public material, but the exact version history of "from which frozen V-number the serving/neighbour wording took its *current form*" could not be determined from the single-snapshot corpus and the blocked public PDFs (undetermined).
