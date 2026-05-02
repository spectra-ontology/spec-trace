# Stage 02 - Metadata Parse (TDoc cover sheets and Resolution)

Two sanitized parsers convert raw 3GPP cover-sheet and chairman-notes
artifacts into JSON-LD records that target the SPECTRA core ontology.

| Script | Source artifact | Output |
| --- | --- | --- |
| `parse_tdoc_cover.py` | `TDoc_List/*.xlsx` (TDoc inventory) | `tdocs.jsonld` (Tdoc / CR / LS instances) |
| `parse_resolution.py` | Chairman notes paragraphs in DOCX | `resolutions.jsonld` (Agreement / Conclusion / WorkingAssumption) |

## `parse_tdoc_cover.py`

Reads each meeting's TDoc list spreadsheet, classifies each row as
`Tdoc`, `CR`, or `LS` based on the `Type` column (Spec §4.5), normalises
the `Source` column into Company / Working-Group references (Spec §7.6.3),
and emits a single `tdocs.jsonld` graph.

The deterministic logic preserved from the production parser:

* TDoc-prefix → working-group inference (`R1-...` → `RAN1`,
  `S2-...` → `SA2`, etc.).
* CR / LS / Tdoc classification by the `Type` field.
* Composite agenda key `tdoc:agenda/{meeting}-{agenda}` (e.g.
  `tdoc:agenda/100-8.1`).
* Boolean affect flags for CRs (`affectsUICC` / `affectsME` /
  `affectsRAN` / `affectsCN`).
* Cross-record relations (`isRevisionOf`, `revisedTo`, `replyTo`,
  `replyIn`) emitted as `@id` references.

### Usage

```bash
export SPECTRA_DATA_DIR=/path/to/spectra-corpus
python parse_tdoc_cover.py --working-group RAN1 \
    --output ./out/tdocs.jsonld
```

Inputs are read from `${SPECTRA_DATA_DIR}/<WG>/TDoc_List/*.xlsx`.

## `parse_resolution.py`

Walks the chairman-notes DOCX of a meeting, scans for the regex-detected
keywords `Agreement`, `Conclusion`, `Working Assumption`, and extracts
the body content until the next decision / heading. The parser then
emits a JSON-LD graph keyed by the source meeting and agenda.

Preserved logic:

* Header-only vs. inline keyword pattern (`Agreement:` line vs.
  `Agreement: The UE shall ...`).
* Negative-consensus regex (Spec §4.3) sets `hasConsensus = false`.
* `FFS` / `TBD` markers preserved verbatim.
* Annex sections (`Annex A` ...) are skipped.

### Usage

```bash
python parse_resolution.py \
    --meeting-id RAN1#104b-e \
    --chairman-notes /path/to/RAN1_104b-e_chair_notes.docx \
    --output ./out/resolutions.jsonld
```

## Outputs

Both scripts emit JSON-LD with the SPECTRA `tdoc:` context. Each record
carries an `@id`, `@type`, scalar literals, and `@id`-typed relation
properties so that the file can be loaded directly via Neo4j's
`apoc.load.json()` (see Stage 05).
