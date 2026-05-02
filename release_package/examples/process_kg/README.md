# Cross-WG metadata-only process knowledge graph

This directory hosts the **metadata-only cross-WG process knowledge graph** referenced in the paper §6.5 and Resource Availability Statement.

## Scope (v1.0)

A SPECTRA-conformant KG export covering 3GPP RAN1--RAN5 with all body content stripped:

- **Cross-WG routing edges** for all five WGs:
  - LS routing (`ls_routing.ttl`): source WG, target WG, meeting, time
  - CR routing (`cr_routing.ttl`): CR id, target Spec, target Release, status
- **RAN1 TDoc-level metadata** (`ran1_tdoc_metadata.ttl`):
  - TDoc number, agenda item, source company, target Release, status
  - Structural relations: presentedAt, submittedBy, isRevisionOf, references
- **Source-company names are kept verbatim**, identical to the values
  3GPP publishes per meeting in `TDOC_List.xlsx` and on every TDoc cover
  page; redistribution does not introduce information that is not already
  publicly observable.
- **Body content stripped**: titles, abstracts, chairman notes, CR
  reasonForChange/summaryOfChange, LS body all removed

## Reproducibility

Every record passes SHACL validation against `shapes/spectra-core.shacl.ttl`. Schema-level statistics (counts, per-WG class coverage, cross-WG schema diff) are pre-computed in `validation/*.json`.

Run `tests/verify_release.py` to re-derive aggregate statistics independently.

## Scope note

This metadata-only export complements the per-WG body-text KGs (`kg/per_wg/`) shipped in the same v1.0.0 release; detailed RAN2--RAN5 TDoc-level metadata analogous to `ran1_tdoc_metadata.ttl` is a planned addition in a subsequent minor release.

## Source

Generated from the deployed RAN1--RAN5 Neo4j knowledge graphs (snapshot 2026-04-29) by the operational parsing pipeline. Body-text rendered records are in the parent release's `kg/per_wg/` (with 3GPP attribution per the project's Terms-of-Use note); this directory contains only the structural / routing metadata layer for graph-analytics queries that do not require the full body.

## License

CC-BY 4.0 (matches the parent SPECTRA release).
