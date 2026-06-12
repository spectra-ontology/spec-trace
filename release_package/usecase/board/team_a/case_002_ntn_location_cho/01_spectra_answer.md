# SPECTRA Answer — Execution condition for location/time-based CHO in an NTN moving cell: standalone fulfilment vs AND with a measurement event

> Retrieval method: 3GPP TS spec body text searched with semantic embeddings (vector similarity), cross-verified against the standard's structure and relationships (IE definition locations, conditional reconfiguration IE structure, event definition clauses, cross-spec references) via a Knowledge Graph. Both paths used together. The key verdicts (whether D1/T1 can stand alone · the 1-vs-2-condition AND rule) were independently cross-checked against public 3GPP-related material (see "Cross-check" below) — the standard's body text citations are treated as the primary authority.

---

## Conclusion (one-line bottom line + conditional caveat)

- **The answer depends on what the network has configured for that candidate cell.** The UE executes CHO only when ***all* (AND) of the execution conditions configured for that candidate** are fulfilled.
  - **(a) If *only one* location (D1) / time (T1) event is configured** → CHO is executed as soon as that location/time trigger alone is fulfilled. No measurement event is needed. (A D1/D2/T1-only configuration is explicitly permitted by the standard.)
  - **(b) If a location/time event is configured *together with* a measurement event (A3/A4/A5)** → both conditions must be fulfilled **simultaneously** for execution (AND). That is, location/time alone does not trigger execution.
- Therefore "execute on location/time only vs execute together with measurement" is not a fixed either/or answer but a **function of the per-candidate configuration**. And unless D1/D2/T1 is used standalone, the standard prescribes the network behaviour such that **when D1/D2/T1 is configured, a measurement event (A3/A4/A5) is configured as a second trigger for the same candidate** — i.e. the practical default is the AND form of (b).
- The location/time events in the NTN moving cell context (CondEvent D1/T1) and their NTN-specific variant (D2) were all introduced from Rel-17 onward; the citations in this answer are based on the latest indexed release (see release-scope below).

---

## Terminology decomposition (separating three easily confused concepts first)

The precise answer to this question only emerges when "trigger" is not treated as a single lump but split into concepts at different layers.

- **(i) Trigger event** — an *individual* triggering criterion for one candidate cell. In NTN these are the distance-based **CondEvent D1** (or **D2** for an NTN moving reference), the time-based **CondEvent T1**, and the radio-measurement-based **CondEvent A3/A4/A5**. They are all **alternatives (CHOICE)** inside the same trigger-config structure.
- **(ii) Execution condition** — the *bundle* of trigger events configured for one candidate cell. This bundle may consist of **1 or 2** trigger events (each identified by one `MeasId`). For the UE to execute CHO, ***all* events in this bundle must be fulfilled**.
- **(iii) Execution itself** — the action of selecting one of the fulfilled candidates and applying the stored target reconfiguration.

The question's "is location/time fulfilment alone enough, or must it be together with measurement" is precisely a layer-(ii) question — i.e. a question of **whether the execution-condition bundle contains 1 or 2 events**, and if 2, whether the combination is **AND**.

---

## Case-by-case analysis

The analysis axes are derived from *the structure of the very spec the question concerns*. The conditional reconfiguration clause differentiates behaviour per candidate by (a) the *number* of configured trigger events (1 or 2), and (b) whether those events are of the location/time family or the measurement family. These two axes yield the MECE cases.

### Case A — an execution condition has 1 or 2 triggers per candidate (structural fact)

The body of `CondReconfigToAddMod-r16`, the configuration unit for a single CHO candidate, nails down that the execution condition consists of **1 to 2 triggers (MeasId)** [38.331 ASN.1 IE=CondReconfigToAddMod-r16]:

```asn1
CondReconfigToAddMod-r16 ::= SEQUENCE {
    condReconfigId-r16        CondReconfigId-r16,
    condExecutionCond-r16     SEQUENCE (SIZE (1..2)) OF MeasId   OPTIONAL,  -- Need M
    condRRCReconfig-r16       OCTET STRING (CONTAINING RRCReconfiguration)  OPTIONAL,  -- Cond condReconfigAdd
    ...
}
```

→ **Evidence → conclusion**: Since `condExecutionCond` is `SEQUENCE (SIZE (1..2)) OF MeasId`, **at minimum 1 and at most 2** trigger events are configured for one candidate cell. Hence "location/time only vs together with measurement" are *both possible* by spec structure — which one applies is determined by how many MeasIds, and which ones, the network filled in for that candidate.

Each trigger event (`MeasId` → `condTriggerConfig`) selects what the triggering criterion is [38.331 ASN.1 IE=CondTriggerConfig-r16]:

```asn1
CondTriggerConfig-r16 ::= SEQUENCE {
    condEventId   CHOICE {
        condEventA3      SEQUENCE { a3-Offset ..., hysteresis ..., timeToTrigger ... },
        condEventA5      SEQUENCE { a5-Threshold1 ..., a5-Threshold2 ..., hysteresis ..., timeToTrigger ... },
        ... ,
        condEventA4-r17  SEQUENCE { a4-Threshold-r17 ..., hysteresis-r17 ..., timeToTrigger-r17 ... },
        condEventD1-r17  SEQUENCE {
            distanceThreshFromReference1-r17  INTEGER (0..65525),
            distanceThreshFromReference2-r17  INTEGER (0..65525),
            referenceLocation1-r17  ReferenceLocation-r17,
            referenceLocation2-r17  ReferenceLocation-r17,
            hysteresisLocation-r17  HysteresisLocation-r17,
            timeToTrigger-r17       TimeToTrigger
        },
        condEventT1-r17  SEQUENCE {
            t1-Threshold-r17  INTEGER (0..549755813887),
            duration-r17      INTEGER (1..6000)
        },
        condEventD2-r18  SEQUENCE { distanceThreshFromReference1-r18 ..., distanceThreshFromReference2-r18 ..., hysteresisLocation-r18 ..., timeToTrigger-r18 ... },
        ...
    },
    rsType-r16  NR-RS-Type,
    ...
}
```

→ **Evidence → conclusion**: The location criteria (D1/D2), time criterion (T1), and measurement criteria (A3/A4/A5) are **sibling alternatives of the same CHOICE**. Therefore "location/time triggers" and "measurement triggers" are not mutually exclusive alternatives but parts of the same kind that can be *combined* into the up-to-2 slots per candidate.

### Case B — only a location/time event configured standalone → execution on that condition alone (no measurement needed)

The body text governing candidate configuration explicitly permits using D1/D2/T1 **standalone** [38.331 ASN.1 IE=CondReconfigToAddMod field description, `condExecutionCond`]:

> *"Except for CHO with only event condEventD1, or condEventD2, or condEventT1, if the network configures condEventD1 or condEventD2 or condEventT1 for a candidate cell, the network configures a second triggering event condEventA3, condEventA4 or condEventA5 for the same candidate cell. The network configures at most one from condEventD1, condEventD2 or condEventT1 for the same candidate cell."*

And the evaluation procedure also separately recognises the location/time-only configuration [38.331 §5.3.5.13.4, NOTE 0]:

> *"NOTE 0: For CHO configured with only condEventD1, condEventD2 or condEventT1 (without any RRM measurement event), it is up to UE implementation whether and how to detect the applicable cell."*

→ **Evidence → conclusion**: When the network configures **only *one* D1/D2/T1** for that candidate (i.e. "CHO with only condEventD1/D2/T1"), the execution-condition bundle contains only the one location/time event. In that case **fulfilment of that location/time condition alone executes the CHO**, and no measurement event is required. (This standalone form is a legitimate configuration recognised by the standard, but the way the applicable cell is detected is left to UE implementation.)

### Case C — location/time event + measurement event configured together → both conditions (AND) must be fulfilled for execution

The main clause of the same field description (quoted in Case B) prescribes the network behaviour such that, **unless D1/D2/T1 is used standalone**, a measurement event (A3/A4/A5) is configured **as the second trigger** for the same candidate. In this case, how the combination of the two triggers is evaluated is defined by the evaluation procedure [38.331 §5.3.5.13.4]:

> *"2> if condExecutionCondPSCell is not configured:*
> *3> if event(s) associated to all measId(s) within condTriggerConfig for the applicable cell are fulfilled:*
> *4> consider the applicable cell, associated to that condReconfigId, as a triggered cell;*
> *4> initiate the conditional reconfiguration execution, as specified in 5.3.5.13.5;"*

A NOTE makes explicit that up to 2 may be configured per candidate and that the two may be different events [38.331 §5.3.5.13.4, NOTE 1]:

> *"NOTE 1: Up to 2 MeasId can be configured for each condReconfigId, if condExecutionCondPSCell is not configured. The conditional reconfiguration event of the 2 MeasId may have the same or different event conditions, triggering quantity, time to trigger, and triggering threshold."*

→ **Evidence → conclusion**: The crux of the evaluation rule is *"event(s) associated to **all** measId(s) ... are fulfilled"* — i.e. **all** triggers configured for that candidate must be fulfilled before it is considered a triggered cell (AND). Therefore, for a candidate with both D1/T1 (location/time) and A3/A4/A5 (measurement) configured, **the UE does not execute with only the location/time condition fulfilled**; the measurement condition must also be fulfilled simultaneously for CHO execution. The typical NTN moving cell configuration (narrowing candidates by distance/time and confirming by radio quality) is exactly this AND form.

### Case D — actual execution (triggered cell selection)

Once conditions are fulfilled and a cell has become a triggered cell, the execution is governed by a separate clause [38.331 §5.3.5.13.5]:

> *"1> else if more than one triggered cell exists:*
> *2> select one of the triggered cells as the selected cell for conditional reconfiguration execution;*
> *1> else:*
> *2> consider the triggered cell as the selected cell for conditional reconfiguration execution;*
> *1> for the selected cell(s) of conditional reconfiguration execution:*
> *2> else: 3> apply the stored condRRCReconfig of the selected cell and perform the actions as specified in 5.3.5.3;"*

→ **Evidence → conclusion**: If more than one candidate has its execution condition fulfilled, UE implementation selects one (NOTE: beam/beam quality etc. may be considered). This stage is independent of "how many conditions (AND)", and is the behaviour *after* triggering has been determined in Cases B/C.

---

## Comparison table (case → verdict → supporting spec §)

| Candidate configuration | UE execution criterion | Execute on location/time alone? | Supporting spec § |
|---|---|---|---|
| Only one location/time event (D1·D2·T1) | Execute when that location/time condition is fulfilled | **Yes** (no measurement needed) | 38.331 §5.3.5.13.4 NOTE 0 + `condExecutionCond` field description |
| Location/time + measurement (A3/A4/A5), 2 events | Execute when both conditions (AND) are fulfilled | **No** (both required) | 38.331 §5.3.5.13.4 ("all measId(s) ... fulfilled") + NOTE 1 |
| Number of triggers per candidate | 1 or 2 | — | 38.331 ASN.1 `condExecutionCond SEQUENCE (SIZE (1..2)) OF MeasId` |
| If D1/D2/T1 is configured? | Unless standalone, a measurement event is configured alongside as the second | — | 38.331 `condExecutionCond` field description |
| Candidate selection for execution after fulfilment | If multiple, UE implementation selects | — | 38.331 §5.3.5.13.5 |

**Bottom line**: The answer to "does the UE execute CHO on location/time alone, or must it be together with measurement" **depends on the network configuration — execution requires that *all* configured execution conditions are fulfilled (AND).** If D1/D2/T1 is configured *standalone*, execution happens on location/time alone; if a measurement event is configured alongside, location/time + measurement must be fulfilled simultaneously. Since the standard prescribes that a measurement event be configured as the second trigger unless D1/D2/T1 standalone is used, the practical default is AND.

---

## The triggering criteria of the location/time events themselves (D1·T1 entry/leaving definitions)

Since the question concerns the location/time-based trigger of an NTN moving cell, the *definition* text of those events is also quoted — these are the exact criteria for one trigger slot to be "fulfilled".

**CondEvent D1 (distance-based)** — when far enough from the serving reference and close enough to the target reference [38.331 §5.5.4.15]:

> *"1> consider the entering condition for this event to be satisfied when both condition D1-1 and condition D1-2, as specified below, are fulfilled; 1> consider the leaving condition for this event to be satisfied when condition D1-3 or condition D1-4, i.e. at least one of the two ... are fulfilled;"*
> *"Ml1 is the distance between UE and a reference location for this event (i.e. referenceLocation1 ...). Ml2 is the distance between UE and a reference location for this event (i.e. referenceLocation2 ...). Thresh1 ... distanceThreshFromReference1 ... Thresh2 ... distanceThreshFromReference2 ..."*
> *"NOTE: The definition of Event D1 also applies to CondEvent D1."*

→ **Evidence → conclusion**: The "fulfilment" of the single event D1 itself requires **two distance inequalities (D1-1 AND D1-2)** to hold simultaneously. This is the entering condition *inside one trigger slot*, and is at a different layer from the "1 or 2 in the execution-condition bundle" discussed in Cases A–C (intra-slot vs inter-slot combination).

**CondEvent T1 (time-based)** — when the time measured at the UE lies within a certain interval after a threshold [38.331 §5.5.4.16]:

> *"The UE shall: 1> consider the entering condition for this event to be satisfied when condition T1-1, as specified below, is fulfilled; 1> consider the leaving condition for this event to be satisfied when condition T1-2, as specified below, is fulfilled; Inequality T1-1 (Entering condition): Mt > Thresh1. Inequality T1-2 (Leaving condition): Mt > Thresh1 + Duration. Mt is the time measured at UE. Thresh1 is the threshold parameter for this event (i.e. t1-Threshold ...). Duration is the duration parameter for this event (i.e. duration ...). Mt is expressed in ms."*

→ **Evidence → conclusion**: T1 defines a time window from the `t1-Threshold` instant (entry) until `duration` has elapsed (leaving) — the trigger slot is fulfilled only while inside this time window. Both distance (D1) and time (T1) are triggering criteria tailored to the NTN moving cell scenario, where the future handover instant can be predicted from distance/time information.

---

## Cross-verification of standard structure (IE definition locations · cross-spec relationships)

**(1) The conditional reconfiguration IE family and its defining spec.** The conditional reconfiguration (CHO/CPA/CPC) IEs are all defined in the RRC spec 38.331 (12 members of the `Cond*` family confirmed in the Knowledge Graph). Key members:

| ieName | Kind | Introducing release (by name notation) |
|---|---|---|
| ConditionalReconfiguration-r16 | SEQUENCE | Rel-16 |
| CondReconfigToAddMod-r16 | SEQUENCE | Rel-16 |
| CondReconfigId-r16 | INTEGER | Rel-16 |
| CondTriggerConfig-r16 | SEQUENCE | Rel-16 |
| VarConditionalReconfig | SEQUENCE (UE variable) | Rel-16 |
| CondExecutionCondToAddMod-r18 | SEQUENCE | Rel-18 (subsequent CPAC) |
| SubsequentCondReconfig-r18 | SEQUENCE | Rel-18 |

→ The CHO skeleton (`ConditionalReconfiguration-r16`/`CondReconfigToAddMod-r16`/`CondTriggerConfig-r16`) came in at Rel-16, while **the location/time event alternatives inside it (`condEventD1-r17`/`condEventT1-r17`) carry Rel-17 notation**, the NTN moving-reference `condEventD2-r18` carries Rel-18 notation, and the altitude-combined `condEventA3H1/H2-r19`·`condEventA5H1/H2-r19` carry Rel-19 notation (see the release-scope note below).

**(2) Procedure definition locations.** The conditional reconfiguration procedures are gathered under 38.331 §5.3.5.13 — General [38.331 §5.3.5.13.1], add/mod [38.331 §5.3.5.13.3], **evaluation (condition evaluation)** [38.331 §5.3.5.13.4], **execution** [38.331 §5.3.5.13.5]. The event *definitions* are located in the same clause as the measurement events [38.331 §5.5.4.15 (D1) / §5.5.4.15a (D2) / §5.5.4.16 (T1)]. All of these clauses are confirmed to exist in the standard's structure.

**(3) Linkage of trigger evaluation to measConfig.** The evaluation procedure treats each `MeasId` carried in `condExecutionCond` as a measId of the measurement configuration (`VarMeasConfig`) and judges that event's entry/leaving [38.331 §5.3.5.13.4]:

> *"2> if condExecutionCond is configured: ... 4> in the remainder of the procedure, consider each measId indicated in the condExecutionCond as a measId in the VarMeasConfig associated with the MCG measConfig;"*

→ That is, location/time events enter the evaluation pipeline on a measId basis exactly like measurement events, and the final gate is "**all measId(s) ... fulfilled**" (AND).

**(4) Constraint when 2 events are configured for the same candidate.** When configuring 2 triggers per candidate, the network ensures both refer to the same measObject [38.331 ASN.1 IE=CondReconfigToAddMod field description, `condExecutionCond`]:

> *"When configuring 2 triggering events (Meas Ids) for a candidate cell, the network ensures that both refer to the same measObject."*

---

## Cross-WG perspective (RAN4 RRM/perf-req)

The CHO execution *decision logic* (1 vs 2 conditions, AND) is closed within RRC (38.331), so RAN4 performance requirements do not change the verdict. However, the RRM side of location/time CHO (RAN4 requirements on distance/time evaluation · NTN measurement requirements) spans cross-WG into RAN4 38.133 — the primary basis of this analysis is the RRC body text, and **the RAN4 38.133 clauses on distance/time evaluation accuracy·timing requirements for NTN CHO were not retrieved as direct citation targets in this analysis** (see Honest gap below). This has no impact on the verdict for Q1 (whether execution is AND).

---

## Cross-check (against external public material)

The key verdicts were independently cross-checked against public 3GPP-related material on the web. The standard's body text citations are the primary authority; the supporting sources below are only for checking agreement with that verdict.

- **(Authoritative body text) location/time-only permitted + AND when combined** → directly settled by the 38.331 body text in the corpus (§5.3.5.13.4 NOTE 0/NOTE 1, the `condExecutionCond` field description, ASN.1 `SIZE (1..2)`). This is the primary authority.
- **(Supporting, agrees) Rel-17 NTN CHO = D1/T1** → public tutorial/commentary material agrees: *"Release 17 supports time-based CHO triggering condition condEventT1 and location-based condEventD1"*, *"the UE can execute the CHO ... only within the time interval"* (T1), *"the UE can execute the CHO ... if the distance ... is longer than threshold1 and ... shorter than threshold2"* (D1) `[web: WirelessBrew CHO / Ofinno NTN — non-authoritative commentary]`.
- **(Supporting, agrees) 2 trigger events per candidate** → public commentary mentions *"2 trigger events for same execution condition"* as a UE capability, consistent with the ASN.1 `SIZE (1..2)` structure `[web: ShareTechnote 5G_CHO — non-authoritative tutorial]`.
- **No conflict**: the supporting sources above (all non-authoritative) do not conflict with the standard body-text verdict. (One authoritative 38.331 body-text mirror [tech-invite 38.331 ToC] could not be reached due to a TLS certificate error — since the same body text exists in authoritative form in the corpus, this does not affect the authority of the verdict.)

---

## Honest gap (spec/§ not cited · uncertainty boundaries · release-scope)

- **Release-scope (introducing release)**: the location/time CHO events are identified by IE name notation as `condEventD1-r17`/`condEventT1-r17` (Rel-17), `condEventD2-r18` for the NTN moving reference (Rel-18), and the altitude-combined `condEventA3H1/H2-r19`·`condEventA5H1/H2-r19` (Rel-19). This notation is an IE/field-level marker, and this analysis did not directly cross-check each item's *exact first introducing release/version* against an authoritative Change History row — so "D1/T1 introduced in Rel-17" is corroborated by the IE notation and supporting public material, not asserted at the level of citing a frozen-version row. Since the question did not pin a specific release, the answer is based on the latest indexed body text.
- **Applicable cell detection (D1/D2/T1 standalone)**: the standard delegates to UE implementation how the applicable cell is detected for location/time-only CHO ([38.331 §5.3.5.13.4 NOTE 0]). The concrete candidate detection/evaluation behaviour of the standalone form is an area the standard does not constrain.
- **RAN4 38.133 NTN CHO requirements**: the RAN4 RRM accuracy·timing requirements for distance/time evaluation of location/time CHO (NTN-related clauses of 38.133) were not retrieved as direct citation targets in this search. This does not affect the RRC decision logic (AND), but the RAN4 timing side of NTN CHO is outside this answer's direct citation scope.
- **NES/PSCell branches**: the evaluation procedure has further branches such as the NES-specific CHO event (`nesEvent`) and candidate SCG (`condExecutionCondPSCell`) ([38.331 §5.3.5.13.4]), but as these are outside the direct scope of the question (location/time vs measurement for a single PCell candidate), this answer judges along the main-cell (no PSCell configured) path.
- **Domain terminology mapping**: the core terms of this answer (CHO/CondEvent D1·T1/condExecutionCond) are used exactly as in the spec body text; a separate alias mapping to the 38.306 capability item naming layer was not decisive for this RRC-procedure question — the UE capability side is only mentioned by the supporting sources above as "2 trigger event support" as a capability, and the corresponding capability item body text was not retrieved as a direct citation target in this analysis.
