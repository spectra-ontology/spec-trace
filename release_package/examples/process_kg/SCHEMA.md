# Cross-WG process KG schema (metadata-only export)

The released TTL files conform to the SPECTRA OWL ontology
(`ontology/spectra.ttl`) with body-content properties intentionally
omitted.

## Files

| File | Coverage | Triples (measured) |
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

Only structural / categorical metadata:

- `spectra:tdocNumber`, `spectra:agendaNumber`, `spectra:status`,
  `spectra:type`, `spectra:direction` (LS), `spectra:crCategory` (CR),
  `spectra:specVersion` (CR), `spectra:uploadedDate`
- Relations: `spectra:presentedAt`, `spectra:submittedBy`,
  `spectra:isRevisionOf`, `spectra:references`, `spectra:modifies`,
  `spectra:modifiesSection`, `spectra:targetRelease`, `spectra:sentTo`,
  `spectra:originatedFrom`, `spectra:replyIn`, `spectra:replyTo`,
  `spectra:relatedToWorkItem`
- `spectra:Company` instances carry their real `spectra:companyName`,
  identical to the source values published in 3GPP's per-meeting
  `TDOC_List.xlsx` and on every TDoc cover page (already public).

## Verifying release integrity

```bash
# 1. Schema conformance (all records satisfy SHACL)
pyshacl -s ../../shapes/spectra-core.shacl.ttl ls_routing.ttl
pyshacl -s ../../shapes/spectra-core.shacl.ttl cr_routing.ttl
pyshacl -s ../../shapes/spectra-core.shacl.ttl ran1_tdoc_metadata.ttl

# 2. Aggregate counts vs validation/*.json
python3 ../../tests/verify_release.py
```
