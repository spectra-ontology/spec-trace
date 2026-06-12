# Case-003 (RAN2) — Whether the C-RNTI MAC CE Is Transmitted in MSGA PUSCH During a 2-Step CFRA Handover

> Source: internal engineering board (anonymized).
> WG / Spec domain: 3GPP RAN2 (MAC — Random Access; 2-step CFRA / MSGA). Owing to the nature of the topic, this crosses over to RAN1 PHY (msgA PUSCH).
> Spec: TS 38.321 (citations as written by the questioner)
> Case number: RAN2 case-003

---

## Question body (original, verbatim — the answering session sees only this question and makes its own judgment)

Hello, I have a question about the MSGA PUSCH content when performing a handover via 2-step CFRA.

Because of the following passage in the 38.321 spec, my understanding is that in the case of 2-step CFRA the C-RNTI MAC CE must be transmitted together in the MSGA.

```
1> if this is the first MSGA transmission within this Random Access procedure:
  2> if the transmission is not being made for the CCCH logical channel:
    3> indicate to the Multiplexing and assembly entity to include a C-RNTI MAC CE
       in the subsequent uplink transmission.
```

**Q1.** In the case of 4-step CFRA, my understanding is that the RACH procedure ends with the preamble transmission and RAR reception, and then the MAC PDU is scheduled using the UL grant allocated via the RAR. In this case my understanding is that the C-RNTI MAC CE is not transmitted separately. Could you please confirm whether in 2-step CFRA it is designed so that the C-RNTI is transmitted?

**Q2.** When the C-RNTI MAC CE is transmitted in the 2-step CFRA MSGA PUSCH, could you please confirm that it is correct to set and send the target cell's C-RNTI?
