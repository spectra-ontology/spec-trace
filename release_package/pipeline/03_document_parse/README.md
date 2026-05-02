# Stage 03 — Document Parse (CR / TR DOCX bodies)

Two sanitized parsers extract structured fields from CR (Change Request)
and TR (Technical Report) DOCX bodies into JSON-LD records that target the
SPECTRA core ontology.

| Script | Input artifact | Output |
| --- | --- | --- |
| `parse_cr.py` | `<TDoc>.docx` whose Type=`CR` (3GPP CR cover-template) | `cr_bodies.jsonld` (CR `reasonForChange`, `summaryOfChange`, modified-section list) |
| `parse_tr.py` | `<TR>.docx` (3GPP TR — TR 38.xxx series) | `tr_bodies.jsonld` (TR `scope`, `conclusions`, TRImpact reified relations) |

## `parse_cr.py`

Reads a CR DOCX and extracts the cover-template fields documented in
3GPP TR 21.801 (CR template):

* `Reason for change:` → `spectra:reasonForChange`
* `Summary of change:` → `spectra:summaryOfChange`
* `Other comments:` → `spectra:crOtherComments`
* `Clauses affected:` (multi-section column) → `spectra:modifiesSection` per
  affected clause (anchored on `<Spec>:<section_number>`)

The deterministic logic preserved from the production parser:

* DOCX table walking via `python-docx` to locate the cover-template grid
  (the cover template is conventionally a 2-column or 4-column table at
  the top of the document).
* "Clauses affected" cell is split on commas/semicolons; each clause is
  mapped to a `Section` IRI under the parent `Spec` (e.g.,
  `spectra:section/38.214/5.1.3`).
* Stage-2 vs Stage-3 CR pairing is *not* attempted at this stage — it
  is handled by the bulk loader (Stage 05) using `crNumber` and the
  paired specification numbers.

## `parse_tr.py`

Reads a TR DOCX (e.g., TR 38.913 for NR scenarios/requirements) and
extracts:

* TR `Scope` clause (TR §1) → `spectra:trScope`
* TR `Conclusions` clause (last clause of the TR) → `spectra:trConclusions`
* TR Impact rows (typically a closing summary table that lists impacted
  Specs and sections) → reified `spectra:TRImpact` records with
  `spectra:impactType` ∈ {`NewTS`, `NewSection`, `ExtendSection`,
  `NoChange`} and links to `spectra:impactsSpec` / `spectra:impactsSection`

## Sanitization scope

* No internal monitoring / Slack hooks / authentication wrappers.
* Hard-coded internal paths replaced with CLI arguments.
* The deterministic table-walking and clause-extraction logic preserved.

## Usage

```bash
python parse_cr.py  --in /path/to/CR.docx --out cr_bodies.jsonld
python parse_tr.py  --in /path/to/TR_38.913.docx --tr-number 38.913 --out tr_bodies.jsonld
```

## Dependencies

`python-docx>=1.1.0` (see top-level `requirements.txt`).
