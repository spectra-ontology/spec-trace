# Case-007 — TS 38.101-1 Rel-16→Rel-17 "single-port transmission" vs "single antenna-port" terminology interpretation

> Source: internal engineering board (anonymized). Real engineering question from day-to-day standards work (translated from the Korean original; question content preserved verbatim in meaning)
> WG / Spec domain: 3GPP RAN4 (RF — NR UE radio transmission and reception; TS 38.101-1, PC1.5 PUSCH max output power; Rel-16 → Rel-17 §6.2D.1)
> Case number: case-007

---

## Question body (preserved verbatim in meaning)

Regarding the document changes in 3GPP TS 38.101‑1 from Rel 16 to Rel 17:

1️⃣ In Rel 16, the text reads as follows.

> For UE power class 1.5 the maximum output power for single‑port transmission is defined as the sum of the maximum output power from both UE antenna connectors. For PUSCH transmissions, a UE supporting PC1.5 shall meet the maximum output power requirement when scheduled by DCI format 0_0 or by DCI format 0_1 configured for **single antenna port**.

2️⃣ From Rel 17 onward, the above wording disappears, and instead in §6.2D.1 only the following expression remains:

> If the UE is scheduled for **single antenna‑port** PUSCH transmission by DCI format 0_0 or DCI format 0_1 …

### Question

Can the two expressions above — "single‑port transmission" and "single‑antenna‑port" — be interpreted as semantically identical? Is it correct to interpret the "single antenna port" mentioned here as referring not to a physical single antenna (one antenna connector), but to one logical antenna port scheduled by DCI 0_0 or 0_1?
