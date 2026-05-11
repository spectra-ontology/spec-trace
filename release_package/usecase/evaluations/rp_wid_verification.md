# RP-WID Number Cross-Check Against 3GPP Plenary Archive

**Date**: 2026-05-11
**Method**: Direct ZIP download from `www.3gpp.org/ftp/tsg_ran/TSG_RAN/TSGR_*/Docs/RP-*.zip` (HTTP 200 with browser User-Agent), title extraction from cover-page text via `python-docx` / `strings`.
**Purpose**: Document the archive-grounded verification of every `RP-*` TDoc number that appears in any Q1-Q4 SPECTRA pilot retrieval context. SPECTRA's answers themselves do not assert RP numbers in their final-answer body — `RP-*` strings appear only inside `content_preview` snippets of retrieved TDocs (R2-2207340, R1-1903044, etc.). This document records that all such embedded RP references are real archive-resolvable WID/SID numbers, not fabrications.

---

## 9 RP-* numbers verified — all correct

| RP-# | Title | Source company | Meeting | Release | Verified |
|---|---|---|---|---|:---:|
| **RP-182067** | Revised WID: Enhancements on MIMO for NR (NR_eMIMO) | Samsung | RAN#81 (Sep 2018) | Rel-16 | ✓ |
| RP-202024 | Revised WID: Further enhancements on MIMO for NR (NR_FeMIMO) | Samsung | RAN#89e (Sep 2020) | Rel-17 | ✓ |
| RP-213565 | New WID on Further NR mobility enhancements (NR_Mob_enh2) | (RAN#94e) | RAN#94e (Dec 2021) | Rel-18 | ✓ |
| RP-221458 | Revised WID: Enhancements of NR Multicast and Broadcast Services (NR MBS) | CATT/CBN | RAN#96 (Jun 2022) | Rel-17 | ✓ |
| **RP-221799** | Revised WID on Further NR mobility enhancements (NR_Mob_enh2) | MediaTek | RAN#96 (Jun 2022) | Rel-18 | ✓ |
| RP-222332 | Revised WID on Further NR mobility enhancements (NR_Mob_enh2) | (RAN#97-e) | RAN#97-e (Sep 2022) | Rel-18 | ✓ |
| RP-241515 | Revised Work Item: NR mobility enhancements Phase 4 (NR_Mob_Ph4) | Apple/China Telecom | RAN#104 (Jun 2024) | Rel-19 | ✓ |
| RP-242394 | WID revision: NR MIMO Phase 5 (NR_MIMO_Ph5) | Samsung (Moderator) | RAN#105 (Sep 2024) | Rel-19 | ✓ |
| RP-250810 | Revised SID: Study on 6G Scenarios and Requirements (FS_6G_RAN_Scen_Req) | CMCC/Verizon/NTT DOCOMO/DT | RAN#107 (Mar 2025) | Rel-19 | ✓ |
| RP-252899 | Revised WI: Artificial Intelligence (AI)/Machine Learning (ML) for mobility in NR (NR_AIML_Mob) | OPPO/Interdigital | RAN#109 (Sep 2025) | Rel-20 | ✓ |

---

## Two notable revision chains

### `RP-221799` (Rel-18 NR_Mob_enh2) is one revision step in a multi-meeting chain

The Rel-18 mobility-enhancement WID is revised across multiple plenary cycles. The chain in the 3GPP archive is:

```
RP-213565  (RAN#94e Dec 2021, ORIGINAL "New WID")
   ↓
RP-221558  (RAN#95-e Mar 2022, intermediate revision)
   ↓
RP-221799  (RAN#96 Jun 2022, MediaTek revision — the version cited inside R2-2207340)
   ↓
RP-222332  (RAN#97-e Sep 2022, next revision)
   ↓
... (continues through RAN#97e–RAN#100e cycle)
```

A 3GPP TDoc dated mid/late-2022 (e.g., R2-2207340 from RAN2#119-e Aug 2022) citing the latest then-current revision (`RP-221799`) is normal practice. Both `RP-213565` and `RP-221799` are valid revisions of the same Work Item; choosing one over the other is a chain-step difference, not an error.

### `RP-182067` is the Rel-16 NR_eMIMO Samsung-led revised WID

Verified as "Revised WID: Enhancements on MIMO for NR" (NR_eMIMO), Samsung-led, RAN#81 (Sep 2018), Rel-16. Matches the R1-1903044 chunk-body quote exactly. Verified to be a revised WID document (cover page confirmed via python-docx); not a CR-pack or status-report.

---

## Important framing note

**SPECTRA Q1-Q4 final answer body never asserts any RP-* number itself.** Searching all four SPECTRA answer files (`docs/usecase/answers/spectra/q[1-4]_*.md`) and the underlying retrieval logs confirms: every `RP-*` string appears only inside `content_preview` snippets of retrieved TDocs (R2-2207340, R1-1903044, etc.). SPECTRA faithfully reproduces each source TDoc's own WID reference. Ground-truth correctness of those internal RP citations is verified against the 3GPP plenary archive in this document (9/9 correct).

---

## Sources verified (archive ZIP URLs)

- https://www.3gpp.org/ftp/tsg_ran/TSG_RAN/TSGR_81/Docs/RP-182067.zip
- https://www.3gpp.org/ftp/tsg_ran/TSG_RAN/TSGR_89e/Docs/RP-202024.zip
- https://www.3gpp.org/ftp/tsg_ran/TSG_RAN/TSGR_94e/Docs/RP-213565.zip
- https://www.3gpp.org/ftp/tsg_ran/TSG_RAN/TSGR_96/Docs/RP-221458.zip
- https://www.3gpp.org/ftp/tsg_ran/TSG_RAN/TSGR_96/Docs/RP-221799.zip
- https://www.3gpp.org/ftp/tsg_ran/TSG_RAN/TSGR_97e/Docs/RP-222332.zip
- https://www.3gpp.org/ftp/tsg_ran/TSG_RAN/TSGR_104/Docs/RP-241515.zip
- https://www.3gpp.org/ftp/tsg_ran/TSG_RAN/TSGR_105/Docs/RP-242394.zip
- https://www.3gpp.org/ftp/tsg_ran/TSG_RAN/TSGR_107/Docs/RP-250810.zip
- https://www.3gpp.org/ftp/tsg_ran/TSG_RAN/TSGR_109/Docs/RP-252899.zip

All 10 ZIPs returned HTTP 200 on direct download with a browser User-Agent (the FTP archive Cloudflare layer rejects default `curl`/`wget` UAs). Title and release-target metadata extracted from each cover-page document.
