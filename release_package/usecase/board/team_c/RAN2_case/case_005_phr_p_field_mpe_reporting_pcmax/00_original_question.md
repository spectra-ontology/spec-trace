# Case-005 (RAN1/RAN2) — Interpretation of the PHR P field definition (OR condition when mpe-Reporting-FR2 is not configured / on FR1, plus factors that vary PCMAX)

> Source: internal engineering board (anonymized).
> WG / Spec domain: 3GPP RAN1/RAN2 (MAC — Power Headroom Report; P field / MPE / power management). The asker explicitly notes a possible RAN1 association. The cited cross-spec material falls in the RAN4 domain (TS 38.101-1/-2/-3, TS 38.133).
> Spec: TS 38.321 (MAC)
> Case number: RAN2 case-005

---

## Question body (verbatim — the answering session sees only this question and reasons autonomously)

Hello. The Spec is 321, but since the content of the question may be related to RAN1, I have marked it as RAN1/RAN2.

The 38.321 document defines the P value of the PHR field as follows.

> **P:** If mpe-Reporting-FR2 is configured and the Serving Cell operates on FR2, the MAC entity shall set this field to 0 if the applied P-MPR value, to meet MPE requirements, as specified in TS 38.101-2 [15], is less than P-MPR_00 as specified in TS 38.133 [11] and to 1 otherwise. If mpe-Reporting-FR2 is not configured or the Serving Cell operates on FR1, this field indicates whether power backoff is applied due to power management (as allowed by P-MPRc as specified in TS 38.101-1 [14], TS 38.101-2 [15], and TS 38.101-3 [16]). The MAC entity shall set the P field to 1 if the corresponding PCMAX,f,c field would have had a different value if no power backoff due to power management had been applied;

When the mpe-Reporting-FR2 IE is configured, I understand that it is decided based on whether the P-MPR value meets the MPE requirements. However, when that IE is not configured or it is FR1, I do not quite understand the part below.

Are the two conditions below an OR condition?

a. this field indicates whether power backoff is applied due to power management (as allowed by P-MPRc as specified in TS 38.101-1 [14], TS 38.101-2 [15], and TS 38.101-3 [16])
→ The case where power backoff is applied

b. The MAC entity shall set the P field to 1 if the corresponding PCMAX,f,c field would have had a different value if no power backoff due to power management had been applied
→ The case where the P_cmax,c value changes (takes a different value) even if power backoff due to power management was not applied

In 1-b above, I am curious whether there is an example in which the P_cmax,c value can change due to factors other than power backoff. Thank you.
