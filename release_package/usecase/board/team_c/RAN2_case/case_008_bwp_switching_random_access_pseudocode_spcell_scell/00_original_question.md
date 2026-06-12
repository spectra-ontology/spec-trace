# Case-008 (RAN2) — Interpreting the BWP switching pseudo-code at Random Access (SpCell vs SCell)

> Source: internal engineering board (anonymized).
> WG / Spec domain: 3GPP RAN2 (MAC — Random Access; BWP operation / switching). Related RRC (TS 38.331: bwp-InactivityTimer, initialUplinkBWP/initialDownlinkBWP) and RAN1 PHY (BWP/PRACH) cross-WG.
> Spec: TS 38.321 V15.5.0 (specified by the asker — Rel-15 version fixed)
> Case number: RAN2 case-008

---

## Question body (verbatim — the answering session judges autonomously seeing only this question)

Hello, I have a question about the pseudo-code on page 46 of TS 38.321 V15.5.0.

```
1>  if PRACH occasions are not configured for the active UL BWP:
2>    switch the active UL BWP to BWP indicated by initialUplinkBWP;
3>    if the Serving Cell is a SpCell:
4>      switch the active DL BWP to BWP indicated by initialDownlinkBWP.
5>  else:
6>    if the Serving Cell is a SpCell:
7>      if the active DL BWP does not have the same bwp-Id as the active UL BWP:
8>        switch the active DL BWP to the DL BWP with the same bwp-Id as the active UL BWP.
9>  stop the bwp-InactivityTimer associated with the active DL BWP of this Serving Cell, if running.
10> if the Serving Cell is SCell:
11>   stop the bwp-InactivityTimer associated with the active DL BWP of SpCell, if running.
12> perform the Random Access procedure on the active DL BWP of SpCell and active UL BWP of this Serving Cell.
```

**Q1.** As in line 3-4 and line 6-8, when the Serving cell is a SpCell and the DL BWP-Id is not the same as the UL BWP-Id, there is an action that sets it equal to the UL BWP-Id. I understand this behaves the same way even in FDD, and I'm curious why this action is done.

**Q2.** Looking at line 10-11, in the SCell case it does stop even the SpCell's bwp-InactivityTimer, but it appears no BWP switching is done. In the SCell case, since CFRA is performed using information received from MAC-CE, I understand that one does not need to check the presence/absence of a PRACH occasion as in line 1. Is my understanding correct?

**Q2-1.** In the SCell case, it seems the match between DL BWP-Id and UL BWP-Id is not checked, and I'm curious about the reason for this too.

**Q3.** I have a question about line 12 because the expression is hard to understand. To summarize, I understand that a SpCell performs the RA procedure on both the active DL BWP and the active UL BWP, while a SCell performs the RA procedure only on the active UL BWP. I don't quite understand this part.

**Q4.** Looking at the RRC standard, I understand that bwp-InactivityTimer checks the inactivity of both the DL BWP and the UL BWP. But in the pseudo-code above it says "bwp-InactivityTimer associated with the active DL BWP", so I'm curious whether it is limited to the DL BWP.

Thank you.
