# Stage 01 - Extract (TDoc Listing & Document Acquisition)

This stage acquires raw 3GPP source artifacts that the rest of the pipeline
processes:

1. **TDoc list spreadsheets** (per meeting): `TDoc_List/*.xlsx`
   downloaded from the meeting folder on the 3GPP FTP portal.
2. **CR / TR / TS document binaries** (`.docx`) referenced by those lists.

The released SPECTRA pipeline does **not** bundle 3GPP body text. Reusers
fetch the artifacts themselves from the public portal and place them under
the directory layout that Stages 02-05 expect (see "Output layout" below).

## Why a thin wrapper

The published version of this stage is a small reference scraper. The
production scraper that generated the SPECTRA v1.0.0 corpus is intentionally
omitted from the release because it carries operational glue (corporate
proxy auth, rate-limit feedback loops, internal logging) that is not
relevant to reusers and not part of the reproducible-research contribution.

The reference scraper:

- accepts a meeting URL (e.g. `https://www.3gpp.org/ftp/tsg_ran/WG1_RL1/TSGR1_104b-e/`)
- downloads the TDoc list spreadsheet and CR / TR / TS attachments listed
  for that meeting
- writes results under `${SPECTRA_DATA_DIR}/RAN1/...`

You are expected to:

- respect the 3GPP FTP terms of use and rate limits,
- substitute your own credentials / network policy if needed,
- and bring your own retry / resume logic for large bulk fetches.

## Usage

```bash
export SPECTRA_DATA_DIR=/path/to/your/spectra-corpus  # raw 3GPP store
python extract_tdoc_metadata.py \
    --meeting-url https://www.3gpp.org/ftp/tsg_ran/WG1_RL1/TSGR1_104b-e/ \
    --working-group RAN1
```

## Output layout (consumed by Stages 02-05)

```
${SPECTRA_DATA_DIR}/
  RAN1/
    TDoc_List/
      TSGR1_104b-e.xlsx
    CR/
      Rel-17/TSG/RP-220XYZ/
        R1-2207890.docx
        RP-220XYZ_cover.docx
    TR/
      38900-i00.docx
    TS/
      38214/38214-j10.docx
```

## Inputs / outputs

| Input | Output |
| --- | --- |
| 3GPP FTP meeting URL | `TDoc_List/*.xlsx`, `*.docx` binaries |
| 3GPP credentials (optional) | logs in `${SPECTRA_DATA_DIR}/.spectra/extract.log` |

## What the released stage does NOT do

- No corporate proxy / SSO authentication.
- No Slack / paging / monitoring webhook calls.
- No write to Samsung-internal mirror servers.
- No automatic credential storage.
