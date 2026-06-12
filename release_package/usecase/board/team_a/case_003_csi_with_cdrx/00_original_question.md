# Case-003 — CSI with C-DRX (periodic/aperiodic CSI report vs DRX inactive time)

> Source: internal engineering board (anonymized). Real engineering question from day-to-day standards work (translated from the Korean original; question content preserved verbatim in meaning)
> Case number: case-003

---

## Question body (preserved verbatim in meaning)

[OPEN] CSI with C-DRX Author: the asking engineer / an internal engineering board about an hour ago 1 min read Question Q1 [OPEN] A UE is configured to transmit a periodic CSI report on PUCCH. The CSI report occasion is in slot n, and slot n falls within C-DRX inactive time. However, the most recent CSI-RS measurement occasion used to compute that CSI report was received within DRX Active Time. Should the UE transmit the CSI report, or should it drop it because the report occasion is in inactive time? Q2 [OPEN] The UE has a valid PUCCH resource in slot n where it is supposed to transmit a periodic CSI report. However, due to C-DRX inactive time, it failed to receive the most recent channel measurement CSI-RS occasion or interference measurement CSI-IM occasion linked to that CSI report. Should the UE reuse CSI measured in a previous Active Time and report stale CSI, or should it drop that CSI report? Q3 [OPEN] While monitoring PDCCH during DRX Active Time, the UE received a DCI, and this DCI triggered an aperiodic CSI-RS and an aperiodic CSI report. However, the triggered AP CSI-RS transmission occasion falls within DRX inactive time. Since the UE received the DCI trigger, must it measure the AP CSI-RS and generate the CSI report, or should it drop the report because the CSI-RS occasion is in inactive time?
