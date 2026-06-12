# Case-001 — Transmission priority when Pcell/Scell each transmit SRS vs PUSCH/PUCCH on the same symbol

> Source: internal engineering board (anonymized).
> Stored: 2026-05-29
> WG / Spec domain: 3GPP RAN1 (38.213 §7.5 prioritization for transmission power reductions)
> Case number: case-001

---

## Question text (preserved as originally written)

**Title**: [RAN1] Case where Pcell/Scell each transmit SRS/PUXCH on the same symbol

> Hello,
>
> In CA, my understanding is that to transmit 1) SRS on the pcell and PUXCH on the scell, or 2) PUXCH on the pcell and SRS on the scell, on the same symbol, the UE must support a UE capability called parallelTxSRS-PUCCH-PUSCH. For a UE that does not support this capa, I would like to ask whether the UE is specified to drop the SRS. Thank you.

---

## Comments (human answers — 3, in chronological order)

### Comment [3] — 2026-05-11 17:54 (standards team, first answer)

> Hello. This is the standards team.
>
> It is not always a drop. In TS38.213 section 7.5, the prioritizations for transmission power reductions rules are defined as follows, based on v16.17.0.
>
> - PRACH transmission on the PCell
> - PUCCH or PUSCH transmissions with higher priority index according to clause 9
>
> For PUCCH or PUSCH transmissions with same priority index
>
> - PUCCH transmission with HARQ-ACK information, and/or SR, and/or LRR, or PUSCH transmission with HARQ-ACK information
> - PUCCH transmission with CSI or PUSCH transmission with CSI
> - PUSCH transmission without HARQ-ACK information or CSI and, for Type-2 random access procedure, PUSCH transmission on the PCell
> - SRS transmission, with aperiodic SRS having higher priority than semi-persistent and/or periodic SRS, or PRACH transmission on a serving cell other than the PCell

### Comment [2] — 2026-05-11 18:33 (asking engineer, follow-up question)

> Hello, thank you for the answer.
>
> For example, in the case where the Pcell transmits SRS and the scell transmits PUSCH/PUCCH, can the SRS transmission take priority?
>
> If not.. in what case can the SRS transmission take priority over the PUSCH/PUCCH transmission? (Here SRS is limited to periodic SRS.)

### Comment [1] — 2026-05-12 16:38 (standards team, second answer)

> The text I attached should be regarded as the priority that applies identically to all cells, regardless of Pcell/Scell.
>
> For the case you mentioned, PUSCH/PUCCH takes priority.

---

## Key conclusions from the human answers

1. **SRS is not always dropped** (conditional)
2. The priority is based on **TS 38.213 §7.5 v16.17.0**
3. The same priority applies to **all cells, with no Pcell/Scell distinction**
4. When SRS + PUSCH/PUCCH transmissions collide on the same symbol → **PUSCH/PUCCH takes priority** (in the context of the question limited to periodic SRS)
5. SRS is **near the very bottom** of the priority list — periodic SRS has the lowest priority
6. Among SRS, the order is **aperiodic > semi-persistent / periodic**

## Evaluation criteria for the SPECTRA answer

For this case, the SPECTRA answer must satisfy the following:

- **Accuracy**: verbatim citation of the TS 38.213 §7.5 priority list (the same spec section as the human answer)
- **Completeness**: definition of the parallelTxSRS-PUCCH-PUSCH UE capability + confirmation of its location in 38.306
- **Added value**: content not present in the human answer (e.g., explicitly stating the behavioral difference between when parallelTxSRS-PUCCH-PUSCH is present vs absent)
- **Zero hallucination**: no expressions not in the spec / no arbitrary paraphrase
- **Audience-friendly**: zero exposure of internal system terms
