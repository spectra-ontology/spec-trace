# SPECTRA Board Use Cases — Real Engineering Questions from Practitioners

This directory contains **real, unedited engineering questions** raised by practicing
engineers in three organizationally separate engineering teams, together with the
answers produced by SPECTRA (semantic retrieval over the 3GPP TS/TR corpus,
cross-verified against the standardization knowledge graph).

Unlike the four cross-WG benchmark questions in [`../`](../README.md), these cases were
not designed for evaluation — they are questions the teams actually needed answered in
day-to-day modem development, protocol implementation, and 3GPP standardization work,
covering NAS procedures, RRC/MAC beam-failure and handover handling, NTN timing and
ASN.1 encoding, RF terminology, PHY UCI/CSI multiplexing, and DCI bit-size derivation,
among others.

## Anonymization

To protect individual contributors, the teams are identified only as **Teams A–C** and
**no case is bound to a named organizational unit**. The three teams sit in separate
management lines, so these are arm's-length uses beyond the resource's authoring team.
All company, division, product, and personal names have been removed; only the 3GPP
technical content and the cited standard references remain.

## Contributing Teams

| Folder | Team | Engineering focus |
|---|---|---|
| [`team_a/`](team_a/README.md) | Team A | Cellular-modem design — physical layer and modem subsystem |
| [`team_b/`](team_b/README.md) | Team B | Protocol-software stack — NAS, RRC, MAC, and upper layers |
| [`team_c/`](team_c/README.md) | Team C | 3GPP RAN standardization — RAN1 (PHY) and RAN2 (RRC/MAC) contributions |

## Case Layout

Each case directory contains:

- `00_original_question.md` — the engineer's question (translated from the Korean
  original; technical content preserved verbatim in meaning)
- `01_spectra_answer.md` — the SPECTRA answer, with every conclusion cited to specific
  3GPP spec clauses, Change Requests, or meeting documents

Team C groups its cases by the 3GPP working group the question concerns
(`RAN1_case/`, `RAN2_case/`).

## Provenance Notes

- Questions and answers were originally written in Korean and translated to English for
  this release; all 3GPP references, IE/field names, and quoted spec text are unchanged.
- Answers are generated exclusively from the 3GPP corpus indexed by SPECTRA — no
  external tools or model prior knowledge — and each cites its sources inline.
- Internal review/audit artifacts are not included in this public release.
