# Per-WG Body-Text Knowledge Graphs (RAN1–RAN5)

This directory hosts the per-WG body-text knowledge graphs accompanying
SPECTRA v1.0.0. Each TTL file materializes the sentence-level rendered
text of the relevant 3GPP corpus (TDocs, CRs, LSs, TS sections, TR scope
text) into RDF using the SPECTRA schema.

## License and attribution

The text literals in the per-WG KGs are **3GPP-derived content**
redistributed with explicit 3GPP source attribution (see top-level
`LICENSE`, Tier 2). They are NOT relicensed under CC-BY 4.0. Reusers
must preserve 3GPP source attribution. Original 3GPP documents remain
freely accessible at <https://www.3gpp.org/ftp/>.

The schema, structure, and parsing/encoding work that materializes 3GPP
text into RDF is SPECTRA-authored and falls under CC-BY 4.0 (Tier 1).

This release follows the academic redistribution practice established
by prior 3GPP-text resources such as TSpec-LLM (Nikbakht et al., 2024)
and the GSMA telecom-kg-rel19 release.

## Files (planned, deposited at v1.0.0 camera-ready)

| File | WG | TDoc count (operational snapshot) |
|---|---|---|
| `ran1_body_text.ttl` | RAN1 | ~123,677 unique TDocs |
| `ran2_body_text.ttl` | RAN2 | (per the released RAN2 KG) |
| `ran3_body_text.ttl` | RAN3 | (per the released RAN3 KG) |
| `ran4_body_text.ttl` | RAN4 | (per the released RAN4 KG) |
| `ran5_body_text.ttl` | RAN5 | (per the released RAN5 KG) |

Each TTL file carries a header comment with:
- `dcterms:source` = `<https://www.3gpp.org/ftp/>`,
- `dcterms:rights` = applicable 3GPP attribution clause,
- `dcterms:created` = export timestamp,
- SPECTRA schema version.

## Status

Body-text export, SHACL conformance check, and attribution headers are
scheduled for v1.0.0 camera-ready (2026-08-06). Until then, this
`README.md` documents the intended structure and the licensing tier.

## Reproducibility

The schema-level claims (class/property counts, OOPS! results, structural
metrics) are reproducible without these body-text KGs via
`tests/verify_release.py` and the SPECTRA ontology TTL. Re-instantiating
the schema on user-supplied 3GPP corpora requires the sanitized parsing
pipeline at `pipeline/`.

## Contact

Issues and corrections: <https://github.com/spectra-ontology/spec-trace/issues>.
