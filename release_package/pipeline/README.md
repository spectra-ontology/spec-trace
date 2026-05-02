# SPECTRA Parsing Pipeline (Sanitized)

This directory contains the **sanitized parsing pipeline** that produces a
SPECTRA-conformant knowledge graph from 3GPP source documents. The pipeline
is documented and released for inspection and re-execution by reusers; raw
3GPP documents are not bundled and must be supplied by the user from the
public 3GPP portal at <https://www.3gpp.org/ftp/>.

## License

CC-BY 4.0 (SPECTRA-authored). See top-level `LICENSE`. The pipeline does
not bundle 3GPP body text; it processes user-supplied 3GPP documents into
RDF/Cypher under the user's own attribution responsibility per the 3GPP
Terms of Use.

## Sanitization scope

The released code excludes Samsung-internal operational glue (monitoring,
Slack/incident hooks, internal authentication, hard-coded paths) and
preserves the deterministic parser logic + transformation stages described
in the paper §7.

## Five-stage architecture

1. **Scrape** — fetch TDoc/CR/TR cover pages and document binaries from
   3GPP portal listings. Reusers supply their own 3GPP credentials and
   respect 3GPP rate limits.
2. **Metadata parse** — deterministic extraction of TDoc and Resolution
   cover-sheet metadata into JSON-LD records.
3. **Document parse** — `python-docx`-based parser for CR/TR structured
   fields (CR `reasonForChange` / `summaryOfChange`, TR scope / conclusions,
   Section/Subsection hierarchy).
4. **SHACL validation** — every JSON-LD record is validated against
   `shapes/spectra-core.shacl.ttl` before loading; failures are logged
   without aborting the load to support data-quality auditing.
5. **Bulk load** — parallel Cypher `CREATE` statements populate Neo4j;
   duplicates are detected via SPECTRA functional-property declarations.

## Per-stage scripts

Each stage directory contains a `README.md` and one or more sanitized
Python scripts (argparse-driven, environment-variable-driven; no
hard-coded paths or credentials):

- `pipeline/01_extract/extract_tdoc_metadata.py` — 3GPP portal scrape
- `pipeline/02_metadata_parse/parse_tdoc_cover.py`,
  `parse_resolution.py` — TDoc cover / chairman-note resolution → JSON-LD
- `pipeline/03_document_parse/parse_cr.py`, `parse_tr.py` — CR cover
  template + TR scope/conclusions/impact tables → JSON-LD
- `pipeline/04_shacl_validate/validate_shacl.py` — pyshacl wrapper
  (`--strict` to fail on first violation)
- `pipeline/05_neo4j_load/load_neo4j.py` — parallel `MERGE` loader
  (`NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD` env vars)

Top-level `requirements.txt` lists the Python dependencies common to
the stages. Reusers supply 3GPP source documents from
<https://www.3gpp.org/ftp/> under their own attribution responsibility.

## Reproducibility

The deterministic verification of release-shipped artifacts is provided by
`tests/verify_release.py` at the release root (does not require this
pipeline). Reusers wanting to re-instantiate SPECTRA on new 3GPP TDocs need
this pipeline plus user-supplied 3GPP documents.

## Contact

Issues and contributions: <https://github.com/spectra-ontology/spec-trace/issues>.
