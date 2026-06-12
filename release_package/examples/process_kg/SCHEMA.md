# Cross-WG process KG schema (metadata-only export)

The released TTL files conform to the SPECTRA OWL ontology
(`ontology/spectra.ttl`) with body-content properties intentionally
omitted.

## Files

Triple counts below are **export-time snapshot values (2026-04-29)**.
Re-parsing the released files with `rdflib` may produce slightly
larger counts (e.g., `ls_routing.ttl` re-parses to 195,968 triples
under rdflib 6.x as of 2026-05-11) because some implementation-side
metadata triples are emitted on parse. The paper Appendix §G ("2.44M
union triples") cites the rounded sum that is reproducible under
either reading; reviewers re-parsing should not interpret a small
delta (≤0.3%) as inconsistency.

| File | Coverage | Triples (export-time, 2026-04-29) |
|------|----------|-------------------:|
| `ls_routing.ttl`         | RAN1–RAN5 LS routing edges        |   195,434 |
| `cr_routing.ttl`         | RAN1–RAN5 CR routing edges        | 1,254,391 |
| `ran1_tdoc_metadata.ttl` | RAN1 TDoc structural metadata     |   991,179 |

## Stripped properties (NOT included)

To respect 3GPP TDoc copyright on body content, the following properties are
removed from every released record:

- `spectra:title`, `spectra:abstract`
- `spectra:reasonForChange`, `spectra:summaryOfChange` (CR body fields)
- `spectra:discussionText`, `spectra:secretaryRemarks`
- Any TR/TS body section content (`spectra:scope`, `spectra:conclusions`,
  `spectra:sectionTitle`, `spectra:specTitle`, captions, etc.)

## Retained properties (released)

Only structural / categorical metadata. The lists below are measured
directly on the released files (predicate census, 2026-06-12):

- Identifiers / categorical values: `spectra:tdocNumber`,
  `spectra:status`, `spectra:type`, `spectra:direction` (LS),
  `spectra:crCategory` (CR), `spectra:crNumber` (CR),
  `spectra:specNumber`, `spectra:releaseName`, `spectra:meetingNumber`,
  `spectra:wgName`, `spectra:workItemCode`, `spectra:uploadedDate`
- Relations: `spectra:presentedAt`, `spectra:submittedBy`,
  `spectra:isRevisionOf`, `spectra:modifies`, `spectra:targetRelease`,
  `spectra:sentTo`, `spectra:originatedFrom`
- `spectra:Company` instances carry their real `spectra:companyName`,
  identical to the source values published in 3GPP's per-meeting
  `TDOC_List.xlsx` and on every TDoc cover page (already public).

Per-file predicate scope: `cr_routing.ttl` carries the CR identifiers
plus `modifies`/`targetRelease`; `ls_routing.ttl` carries the LS
identifiers plus `presentedAt`/`sentTo`/`originatedFrom`;
`ran1_tdoc_metadata.ttl` carries the TDoc identifiers plus
`presentedAt`/`submittedBy`/`isRevisionOf`/`targetRelease`.

Not instantiated in this export: the finer-grained provenance
relations `spectra:references`, `spectra:modifiesSection`,
`spectra:replyIn`, `spectra:replyTo`, `spectra:relatedToWorkItem` and
the data properties `spectra:agendaNumber`, `spectra:specVersion` are
exercised in the per-WG body-text KGs distributed on Zenodo (e.g.,
RAN1: `references` 19,454, `modifiesSection` 4,769, `replyTo` 427,
`agendaNumber` 6,439; `specVersion` appears in RAN2-RAN5), not in
these three metadata-only exports.

## Verifying release integrity

```bash
# 1. Schema conformance (all records satisfy SHACL)
pyshacl -s ../../shapes/spectra-core.shacl.ttl ls_routing.ttl
pyshacl -s ../../shapes/spectra-core.shacl.ttl cr_routing.ttl
pyshacl -s ../../shapes/spectra-core.shacl.ttl ran1_tdoc_metadata.ttl

# 2. Aggregate counts vs validation/*.json
python3 ../../tests/verify_release.py
```
