# Case-007 (RAN2) — MBS multicast user-plane protocol architecture (RLC entity configuration for PTP transmission)

> Source: internal engineering board (anonymized).
> WG / Spec domain: 3GPP RAN2 (overall architecture — MBS multicast user-plane protocol architecture; PTP/PTM, RLC entity configuration). TS 38.300 is jointly owned by RAN2/RAN3.
> Spec: TS 38.300
> Case number: RAN2 case-007

---

## Question body (as originally written — the answering session sees only this question and decides autonomously)

Hello. When I organize the multicast protocol architecture for MBS in 38.300, my understanding is as follows. For PTP transmission, there is a part of the architecture that I do not fully understand, so I have some questions.

```
1. PTP transmission: DL only RLC-UM or Bidirectional RLC-UM
2. PTP transmission: RLC-AM
3. PTM transmission: DL only RLC-UM

4. PTP and PTM (Two RLC entities)
   - DL only RLC-UM (PTP) and DL only RLC-UM (PTM)
   - RLC AM (PTP) and DL only RLC-UM (PTM)

5. PTP, PTP, and PTM (Three RLC entities)
   - DL RLC-UM (PTP), UL RLC-UM (PTP), and DL only RLC-UM (PTM)
```

**Q1.** A UL RLC-UM is defined for PTP transmission. Should I understand this as "there is a service in multicast PTP transmission where UP data comes down from the upper L2 layers"?

**Q2.** In Option 5, the PTP-purpose RLC entities appear to be used as DL and UL uni-directional entities respectively. I am curious about the intent behind adopting such an option.

**Q3.** In Option 4, is there a particular reason why a case such as "RLC-UM Bidirectional (PTP) and DL only RLC-UM (PTM)" was not considered?
