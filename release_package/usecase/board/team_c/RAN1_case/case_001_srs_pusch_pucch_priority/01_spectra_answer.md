# [RAN1] Same-symbol SRS / PUCCH·PUSCH transmission in a CA environment — capability and priority

> Search method: semantic search over 3GPP TS body text + concurrent use of the standard's structure (sections, capability items).
> All citations are verbatim from the TS body. Cited specs: TS 38.214 (PHY procedures), TS 38.306 (UE radio access capability).

---

## Key answer (summary)

1. **Sending SRS on one carrier and PUCCH/PUSCH on another carrier on the same symbol** simultaneously is tied to the `parallelTxSRS-PUCCH-PUSCH` (and, for intra-band non-contiguous, `parallelTxSRS-PUCCH-PUSCH-intraBand-r17`) capability. **For a UE that does not support this capability, it is specified not that "the UE drops the SRS" but that "such a collision is not indicated/configured/scheduled in the first place"** (TS 38.214 §6.2.1). In other words, a cross-carrier collision is handled as a network scheduling constraint rather than as a UE drop behavior.

2. **For "can SRS take priority over PUSCH/PUCCH," limited to periodic SRS** → **in principle it does not take priority.** On the same carrier, when periodic/semi-persistent SRS overlaps with PUCCH (HARQ-ACK/SR/CSI, etc.) or with priority index 1 PUSCH/PUCCH, the SRS side is not transmitted. The only case in the standard where SRS beats a channel is when **aperiodic SRS** overlaps with "a PUCCH carrying only periodic/semi-persistent CSI-type reports" (in which case the PUCCH is dropped), and this does not apply to periodic SRS.

---

## 1. Same-symbol cross-carrier SRS + PUCCH/PUSCH — capability and behavior

### 1-1. Capability definition

The capability mentioned in the question is defined in TS 38.306 §4.2.7.4 (CA-ParametersNR, applied per band combination) as follows.

> **parallelTxSRS-PUCCH-PUSCH** — Indicates whether the UE supports parallel transmission of SRS and PUCCH/PUSCH across CCs in an inter-band CA band combination for NR SA or NR SCG in (NG)EN-DC.

> **parallelTxSRS-PUCCH-PUSCH-intraBand-r17** — Indicates whether the UE supports parallel transmission of SRS and PUCCH/PUSCH across CCs in an intra-band non-contiguous CA band combination for NR SA or NR SCG in (NG)EN-DC.

→ Inter-band CA corresponds to `parallelTxSRS-PUCCH-PUSCH`, and intra-band non-contiguous CA corresponds to `parallelTxSRS-PUCCH-PUSCH-intraBand-r17`; both capabilities are reported per band combination.

### 1-2. Behavior when the capability is not supported — "not scheduled" rather than "drop"

TS 38.214 §6.2.1 (UE sounding procedure) specifies the conditions for cross-carrier simultaneous transmission.

> In case of intra-band contiguous carrier aggregation, or in inter-band or intra-band non-contiguous CA band combination if simultaneous SRS and PUCCH/PUSCH transmissions are not supported by UE, the UE is not expected to be indicated with a SRS transmission from a carrier and to be configured or scheduled with a PUSCH/UL DM-RS/UL PT-RS/PUCCH transmission from a different carrier in the same symbol.

→ That is, for the question "is a UE that does not support the capability specified to drop the SRS," the exact spec wording is **"the UE is not expected to be ... configured or scheduled."** The standard does not define a behavior in which the UE discards the SRS upon collision; rather, it specifies that **such a same-symbol collision (SRS on one carrier + PUSCH/PUCCH on another carrier) is not indicated, configured, or scheduled in the first place.** For a UE without the capability, having such a situation configured/scheduled is a case the standard does not assume ("not expected").

For intra-band contiguous CA, the above "not expected" constraint applies regardless of the capability (i.e., contiguous intra-band does not assume cross-CC same-symbol SRS+PUCCH/PUSCH at all). For inter-band and intra-band non-contiguous, simultaneous transmission is permitted only when the above capability is supported.

### 1-3. When the capability is supported — simultaneous transmission permitted

TS 38.214 §6.2.1.3 (UE sounding procedure between component carriers) specifies that simultaneous transmission is permitted.

> In case of inter-band carrier aggregation, a UE can simultaneously transmit SRS and PUCCH/PUSCH across component carriers in different bands subject to the UE's capability.

→ A UE that supports the capability can simultaneously transmit SRS and PUCCH/PUSCH on CCs in different bands, so in this case the problem of dropping one side does not arise.

**Summary (question 1)**: Transmitting PCell SRS + SCell PUxCH (or vice versa) on the same symbol is, in the inter-band case, subject to `parallelTxSRS-PUCCH-PUSCH` (for intra-band non-contiguous, `...-intraBand-r17`). For a UE that does not support it, the standard specifies that the collision is **not configured/scheduled**, and it is not described as "the UE drops the SRS."

---

## 2. Can periodic SRS take priority over PUSCH/PUCCH

In the question, SRS is limited to periodic SRS. Let us separate the cross-carrier and same-carrier situations.

### 2-1. Cross-carrier (PCell SRS, SCell PUSCH/PUCCH, i.e., a different cell)

Per the §6.2.1 provision above, when the capability is not supported the same-symbol collision is not scheduled, and when it is supported the transmissions occur simultaneously. Therefore, **in the cross-carrier case the situation "SRS takes priority over PUSCH/PUCCH" does not arise at all** — either simultaneous transmission is possible (capable), or no collision is created (incapable).

### 2-2. Same-carrier (SRS vs PUCCH/PUSCH within the same serving cell)

The priority when SRS overlaps with PUCCH/PUSCH on the same carrier is specified in TS 38.214 §6.2.1.

Priority-index-based rules:

> If a PUSCH with a priority index 0 and SRS configured by SRS-Resource are transmitted in the same slot on a serving cell, the UE may only be configured to transmit SRS after the transmission of the PUSCH and the corresponding DM-RS.

> If a PUSCH transmission with a priority index 1 or a PUCCH transmission with a priority index 1 would overlap in time with an SRS transmission on a serving cell, the UE does not transmit the SRS in the overlapping symbol(s).

PUCCH and SRS collision rule:

> For PUCCH and SRS on the same carrier, a UE shall not transmit SRS when semi-persistent or periodic SRS is configured in the same symbol(s) with PUCCH carrying only CSI report(s), or only L1-RSRP report(s), or only L1-SINR report(s) , or only P-CRI/P-SSBRI/P-L1-RSRP report(s), or only RS-PAI report(s). A UE shall not transmit SRS when semi-persistent or periodic SRS is configured or aperiodic SRS is triggered to be transmitted in the same symbol(s) with PUCCH carrying HARQ-ACK, link recovery request (as defined in clause 9.2.4 of [6, 38.213]), SR, and/or UEIRI. In the case that SRS is not transmitted due to overlap with PUCCH, only the SRS symbol(s) that overlap with PUCCH symbol(s) are dropped. PUCCH shall not be transmitted when aperiodic SRS is triggered to be transmitted to overlap in the same symbol with PUCCH carrying semi-persistent/periodic CSI report(s) or semi-persistent/periodic L1-RSRP report(s) only, or only L1-SINR report(s), or only P-CRI/P-SSBRI/P-L1-RSRP report(s), or only RS-PAI report(s) ...

→ From the text above, **periodic/semi-persistent SRS, when it overlaps with PUCCH (HARQ-ACK/SR/CSI-type), is always not transmitted (the overlapping symbols are dropped).** In the standard, the only case where the SRS side takes priority and the PUCCH is dropped is when **"aperiodic SRS"** overlaps with "a PUCCH carrying only periodic/semi-persistent CSI-type reports" ("PUCCH shall not be transmitted ...").

**Summary (question 2)**: Limited to periodic SRS, there is no case in the standard where periodic SRS takes priority over PUSCH/PUCCH. When it overlaps with priority index 1 PUSCH/PUCCH, the SRS is not transmitted in those symbols, and when it is in the same slot as a priority index 0 PUSCH, the UE may be configured to transmit the SRS only after the PUSCH and DM-RS transmission. The only provision where SRS beats a channel is aperiodic SRS vs "a PUCCH carrying only CSI-type reports," and it does not apply to periodic SRS.

---

## 3. Citation scope / limitations (honest disclosure)

- The priority/drop provisions in this answer are based on the TS 38.214 §6.2.1 and §6.2.1.3 (UE sounding procedure) body text. The capability definitions are based on TS 38.306 §4.2.7.4 (CA-ParametersNR).
- The SRS carrier switching scenario (sounding while one carrier has no PUSCH/PUCCH configured) has separate detailed prioritization/dropping rules in §6.2.1.3 (srs-SwitchFromServCellIndex, etc.), but since the question is interpreted as a general CA situation where both PCell/SCell are normally configured, the answer focuses on the cross-carrier provisions of §6.2.1. If you are also using a carrier switching configuration, the additional rules of §6.2.1.3 would need to be reviewed.
- The transmission priority aspect due to power limitation (power scaling/reduction) is a separate provision area in the TS 38.213 §7.x family, and this answer is limited to the transmission/drop provisions upon time-symbol collisions.
