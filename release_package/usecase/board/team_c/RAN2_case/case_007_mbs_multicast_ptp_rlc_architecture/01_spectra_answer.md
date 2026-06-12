# SPECTRA answer — RLC entity configuration for MBS multicast PTP transmission (the purpose of UL RLC-UM, the intent behind Option 5, and whether Option 4 omits a case)

> Regenerated via the SPECTRA retrieval pipeline.
> Question source: `00_original_question.md`

---

## Conclusion (summary)

1. **Q1 — No.** The user data (UP data) of multicast is downlink-only (DL), and the UL RLC-UM entity in the PTP configuration is not for uplink user data. What this entity carries is the **PDCP Control PDU that the receiving-side PDCP entity sends upward** — what is explicitly certain in the text is the feedback of ROHC/EHC header compression, and during the standardization discussions it was intended as a path for uplink control information in general, such as PDCP status reports.
2. **Q2 — Because an RLC UM entity is uni-directional by definition.** In TS 38.322, a UM RLC entity is configured either as a transmitting entity or a receiving entity (unlike AM, a single entity does not hold both sides). Therefore, to provide an uplink control path in UM-mode PTP, one more UL entity is required separately from the DL entity, and the result is the 3-entity configuration of Option 5. The intent of its adoption is the flexibility of "supporting uplink control information without forcing AM (keeping UM), and leaving the RLC combination to the service requirement and the network decision" (meeting contribution quoted below).
3. **Q3 — That case is not omitted; it is exactly the same configuration as Option 5.** "Bidirectional RLC-UM," when expanded at the entity level, is always 'a DL UM entity + a UL UM entity', i.e. **two** entities (a single bidirectional UM entity does not exist). Therefore "Bidirectional RLC-UM (PTP) + DL only RLC-UM (PTM)" = DL UM (PTP) + UL UM (PTP) + DL UM (PTM) = **the three RLC-UM entities of Option 5** itself. It only looks like a different case because the notation level (configuration unit vs entity unit) differs between Option 1 and Option 5.

## 1. Starting point — the multicast MRB configurations enumerated in TS 38.300 §16.10.3

The items 1–5 you organized correspond exactly to the following list in TS 38.300 §16.10.3:

> "- Multicast MRB with DL only RLC-UM or bidirectional RLC-UM configuration for PTP transmission;
> - Multicast MRB with RLC-AM entity configuration for PTP transmission;
> - Multicast MRB with DL only RLC-UM entity for PTM transmission;
> - Multicast MRB with two RLC-UM entities, one DL only RLC-UM entity for PTP transmission and the other DL only RLC-UM entity for PTM transmission;
> - Multicast MRB with three RLC-UM entities, one DL RLC-UM entity and one UL RLC-UM entity for PTP transmission and the other DL only RLC-UM entity for PTM transmission;
> - Multicast MRB with two RLC entities, one RLC-AM entity for PTP transmission and the other DL only RLC-UM entity for PTM transmission."

Here, the first line (item 1 of the question) uses the configuration-unit notation "bidirectional RLC-UM **configuration**," whereas the fifth line (item 5 of the question) uses the entity-unit notation "one DL RLC-UM **entity** and one UL RLC-UM **entity**" — this difference in notation is the crux of Q3 (§4).

## 2. Q1 — What the UL RLC-UM carries: not uplink user data but a PDCP Control PDU

- **Multicast user data is DL-only.** Nowhere in the MRB configuration list of TS 38.300 §16.10.3 is there delivery of uplink user data; PTM is "DL only," and the UL leg of PTP is for the control purpose below.
- **Explicit basis ① — header-compression feedback.** TS 38.300 §16.10.3 includes in the PDCP functions of a multicast MRB "Header compression and decompression using the ROHC protocol or EHC protocol." The decompressor feedback of ROHC/EHC is a **PDCP Control PDU** as specified in TS 38.323 §5.7.4 ("standalone packets not associated with a PDCP SDU, i.e. interspersed ROHC feedback... not associated with a PDCP SN and are not ciphered"), and for the UE (receiving side) to send it, an uplink RLC path is required. Since a UM entity is uni-directional (§3), in UM-mode PTP the UL UM entity is that path.
- **Explicit basis ② — entity-association provision.** TS 38.323 §4.2.1 specifies that the PDCP entity of a UM MRB can be associated with "three UM RLC entities (one for MTCH, one for downlink DTCH, and one for uplink DTCH)" — the fact that the uplink leg is itself a **DTCH** (dedicated channel) and not an MTCH (multicast traffic channel) shows that this leg is for the UE's individual uplink transmission (control information), not for multicast traffic.
- **Intent in the standardization discussion.** RAN2 MBS contributions explicitly address the purpose of this UL leg: "In UL direction: The feedback/status report is delivered via the PTP-RLC entity" (R2-2105096), "whether to support 'PTP of UM mode (two entities of both UL and DL)' therefore to support any UL control information, e.g, PDCP Status and ROCH control info bits" (R2-2110653).
- **One honest limitation**: In the case of the PDCP status report, the explicit trigger text in the current TS 38.323 §5.4.1 exists only for **AM MRBs** ("For AM MRBs configured by upper layers to send a PDCP status report in the uplink (statusReportRequired): ... PDCP entity re-establishment; PDCP data recovery"). We did not find a status-report trigger for UM MRBs in the §5.4.1 text we cross-checked. Therefore the payload that is explicitly certain for the UM-mode UL leg is ROHC/EHC feedback, and the reading most faithful to the current wording is that the status report operates in AM-mode PTP (where no separate UL entity is needed — the AM entity holds its own uplink path).

In summary, the accurate understanding is not "there is a service where UP data comes down from the upper L2 layers" but rather **"there is a control PDU that the receiving L2 layer (PDCP) generates and sends upward."**

## 3. Q2 — Why two uni-directional DL/UL entities: a UM entity is uni-directional by definition

TS 38.322 §4.2.1:

> "An UM RLC entity is configured either as a **transmitting UM RLC entity** or a **receiving UM RLC entity**." (UM)
>
> "An AM RLC entity consists of a **transmitting side and a receiving side**." (AM)

That is, in UM there is no 'bidirectional entity' at all. The RRC configuration structure is likewise — in the TS 38.331 RLC-Config, bidirectional UM is not a single entity but a pair of uplink/downlink configurations:

```asn1
um-Bi-Directional    SEQUENCE {
    ul-UM-RLC            UL-UM-RLC,
    dl-UM-RLC            DL-UM-RLC
},
um-Uni-Directional-UL  SEQUENCE { ul-UM-RLC  UL-UM-RLC },
um-Uni-Directional-DL  SEQUENCE { dl-UM-RLC  DL-UM-RLC },
```

On top of this structure, the meeting contributions directly state the intent behind adopting Option 5:

- **To support uplink control information while keeping UM**: "whether to support 'PTP of UM mode (two entities of both UL and DL)' therefore to support any UL control information, e.g, PDCP Status and ROCH control info bits" (R2-2110653). If one were to solve this with AM alone, the ARQ behavior (retransmission and status reporting) would come along, so for a service that needs only a feedback path without that burden, the UM 3-entity combination is meaningful.
- **To not restrict the combination in the standard, leaving it to the network decision**: "There is no need to limit the possibility of the RLC combination which can be left to the service requirement and network decision" (R2-2110653). That is, it is a design that keeps both Option 4 (2-entity without a UL leg) and Option 5 (3-entity with a UL leg) open, and lets the network choose according to service characteristics such as whether header compression is used.

For reference, the PTM leg (MTCH reception) is distinguished by the `isPTM-Entity` field in the RRC configuration, and "When the field is absent the RLC entity is used for PTP transmission/reception" (TS 38.331 RLC-BearerConfig field description).

## 4. Q3 — "Bidirectional RLC-UM (PTP) + DL only RLC-UM (PTM)" is not an unconsidered case; it is Option 5

As seen in §3, 'bidirectional RLC-UM' is necessarily two entities (a UL UM entity + a DL UM entity) at the entity level. TS 38.323 §4.2.1 uses the same counting method:

> "For UM MRBs, each PDCP entity is associated with one UM RLC entity (for MTCH or for downlink DTCH), two UM RLC entities (one for MTCH and one for downlink DTCH, **or one for downlink DTCH and one for uplink DTCH**), or three UM RLC entities (one for MTCH, one for downlink DTCH, and one for uplink DTCH)"

Therefore:

| Notation (configuration unit) | Entity-unit notation of the same thing | Position in the 38.300 list |
|---|---|---|
| DL only RLC-UM (PTP) + DL only RLC-UM (PTM) | 2 entities | Option 4, first |
| **Bidirectional RLC-UM (PTP)** + DL only RLC-UM (PTM) | DL UM(PTP) + UL UM(PTP) + DL UM(PTM) = **3 entities** | **= Option 5** |
| RLC-AM (PTP) + DL only RLC-UM (PTM) | 2 entities (in AM one entity is bidirectional) | Option 4, second / 38.300 sixth bullet |

That is, the list in 38.300 §16.10.3 uses the configuration-unit notation "DL only or bidirectional ... configuration" for the PTP-only cases (items 1 and 2 of the question), and uses the entity-count notation for the cases combined with PTM (items 4 and 5) — but the **"bidirectional UM (PTP) + PTM" combination itself is already in the list as Option 5.** The reason the AM (PTP) + PTM combination is "two RLC entities" is the same counting method — since AM holds both the transmitting side and the receiving side within a single entity, it is counted as one even when bidirectional.

## Scope and limitations of verification

- Scope cross-checked: TS 38.300 §16.10.3 (MRB configuration list and PDCP functions), §16.10.5.2/§16.10.5.4; TS 38.323 §4.2.1 (entity association), §5.4.1 (status report trigger), §5.7.4 (interspersed ROHC feedback), §5.1.2; TS 38.322 §4.2.1 (UM/AM entity directionality); TS 38.331 RLC-Config ASN.1 and RLC-BearerConfig field description; and 3 RAN2 MBS meeting contributions (R2-2101677/R2-2105096/R2-2110653). External public materials (patent literature and technical papers) cross-checked the same structure (delivery of feedback/status via the PTP leg, one PDCP ↔ multiple RLC association).
- The cited meeting contributions are individual-company proposal documents, not the agreement text itself — the "intent of adoption" is a synthesis grounded in the fact that the relevant discussion flow is consistent with the final standard structure (the 3-entity combination of 38.300/38.323), and we did not trace down to the original-text level of the final agreement (the agreement line of the meeting report).
- The absence of a PDCP status report trigger for UM MRBs is based on the current 38.323 §5.4.1 text we hold; whether it changed in a later release is outside the scope of this answer.
- The constraint that only PTM (DL only UM) applies for RRC_INACTIVE reception (38.300) is not directly relevant to the scope of this question, so it was not elaborated.
