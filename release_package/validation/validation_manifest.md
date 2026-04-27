# SPECTRA Validation Manifest

This manifest maps every quantitative claim in the accompanying paper to the JSON evidence file in this directory, so that reviewers can directly inspect the numbers without access to the internal knowledge graphs.

## Mapping: paper claim → evidence file

| Paper claim | Section | Evidence file |
|---|---|---|
| 26 classes, 53 object properties, 81 data properties, 134 properties total | §3, §6.2 | `structural_metrics.json` |
| 23 owl:FunctionalProperty, 2 owl:InverseFunctionalProperty (`hasCR`, `hasTRImpact`) | §3, §6.2 | `structural_metrics.json` |
| 15 inverse property pairs | §3, §6.2 | `structural_metrics.json` |
| 6 owl:IrreflexiveProperty (sec. hierarchy + intra-section + TR cross-ref) | §3 | `structural_metrics.json` |
| 2 owl:AsymmetricProperty (sec. hierarchy) | §3 | `structural_metrics.json` |
| 6 reused external terms (4 DC + 2 FOAF) | §3 | `structural_metrics.json` |
| OOPS! results: 0 critical / 2 Important / 2 Minor | §6.2 | `oops_summary.json` |
| RAN2-5 vs RAN1 schema diff: 0 classes, 1 OP (`REFERENCES_SPEC`), 22 DPs (20 loader-local + 2 genuine) | §6.4 | `cross_wg_schema_diff.json` |
| Per-WG ontology-level extensions: RAN2 0/1/0, RAN3 0/1/1 (`summaryId`), RAN4 0/1/0, RAN5 0/1/1 (`discussionText`) | §6.4 | `cross_wg_schema_diff.json` |
| RAN1 KG: 3,644 LSes addressed to RAN2 (RAN4: 1,457, RAN3: 380, ...) | §6.5 | `cross_wg_use_evidence.json` |
| RAN2 KG: 1,450 LSes originated from RAN1; peak meeting RAN2 #118-e (62 incoming) | §6.5 | `cross_wg_use_evidence.json` |
| TS 38.300 jointly modified by 2,039 RAN2 CRs and 270 RAN3 CRs | §6.5 | `cross_wg_use_evidence.json` |

## Reproducibility

The structural metrics, OOPS results, and cross-WG schema diff are reproducible against the released ontology TTL (`ontology/spectra.ttl`) using rdflib / OOPS! / pySHACL with no further data dependencies.

The cross-WG use-evidence counts (`cross_wg_use_evidence.json`) come from the internal SPECTRA-conformant KGs and are reproducible only against a SPECTRA-conformant instantiation; the queries themselves are recorded in the same JSON for inspection and re-execution by reusers who instantiate the schema from public 3GPP TDocs.

## Files

- `structural_metrics.json` — class/property counts and axiom totals (rdflib-derived from `ontology/spectra.ttl`).
- `oops_summary.json` — OOPS! pitfall scanner output for `ontology/spectra.ttl`.
- `cross_wg_schema_diff.json` — class/OP/DP diff between each per-WG KG and the released SPECTRA TTL (reduces "what extra schema did each non-RAN1 WG need?" to a JSON).
- `cross_wg_use_evidence.json` — Cypher counts measured on the deployed per-WG KGs for cross-WG use-evidence claims (LS recipient WG distribution, TS 38.300 multi-WG modification).
