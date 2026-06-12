# Case-008 — Full vs stored frequency scan during periodic HPLMN/higher priority PLMN search in automatic network selection

> Source: internal engineering board (anonymized). Real engineering question from day-to-day standards work (translated from the Korean original; question content preserved verbatim in meaning)
> WG / Spec domain: NAS PLMN selection (Higher Priority PLMN / periodic HPLMN search) + idle-mode frequency scanning (BPLMN search). The exact spec sources (e.g., TS 23.122 / TS 38.304) are confirmed against the corpus when the SPECTRA answer is generated.
> Case number: case-008

---

## Question body (preserved verbatim in meaning)

> If the UE is in automatic network selection mode and it finds a registered PLMN or a PLMN in the Allowed PLMN list,,,, it shall periodically attempt to obtain service on its HPLMN or higher priority PLMN.

The question here is: when searching for the HPLMN, the search is done via BPLMN — in this case, does the search have to be performed in full frequency mode, or is it acceptable to scan only the stored frequencies on which the UE previously camped? (From a current-consumption perspective the latter is advantageous, but if we implement it that way, would it violate the 3GPP spec?)
