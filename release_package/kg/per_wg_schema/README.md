# Per-WG Schema-Instantiation Snapshots

These five TTL files are **schema-only** snapshots: each contains the OWL
classes / object properties / datatype properties from the released
`ontology/spectra.ttl` that have **at least one instance** in the
corresponding RAN Working Group's Knowledge Graph.

| File | Classes | OPs | DPs | Coverage % |
|---|---:|---:|---:|---:|
| `RAN1-schema.ttl` | 26 | 49 | 77 | 100% (reference) |
| `RAN2-schema.ttl` | 22 | 39 | 68 | 84.6% |
| `RAN3-schema.ttl` | 23 | 39 | 68 | 88.5% |
| `RAN4-schema.ttl` | 24 | 40 | 73 | 92.3% |
| `RAN5-schema.ttl` | 20 | 39 | 66 | 76.9% |

Each axiom is annotated with `spectra:instanceCount`, the number of nodes /
relationships of that type observed in the WG-specific Neo4j snapshot.

## Purpose: reproducible cross-WG generality check

These files let any reader verify the cross-WG schema-fit claim without
downloading the much larger body-text Knowledge Graphs (deposited
separately on Zenodo, ~922 MB total):

1. **No new classes were required by RAN2-RAN5** (`wg_specific_extensions: []`
   in `validation/per_wg_class_coverage.json`). After excluding 20
   loader-local underscore-prefixed and internal scaffolding properties
   from the raw observation, the paper reports **1 OP and 2 DP extension
   candidates** (RAN3 `summaryId`, RAN5 `discussionText`, plus one OP).
   Diff `RAN{2..5}-schema.ttl` against `ontology/spectra.ttl` to inspect
   exactly which SPECTRA classes/OPs/DPs each WG instantiates.

2. **Coverage percentages in §6** match the per-WG class counts above.

## Body text is **not** included here

These TTLs contain only the schema-level declarations (with usage
counts). They contain **no** TDoc body literals, no Resolution
`content`, no Section text. The body-text Knowledge Graphs (Tier 2:
3GPP-derived literals) are deposited separately on Zenodo as
`RAN{1..5}-body.ttl`; see `kg/per_wg/README.md`.

## Regeneration

These files are produced by a read-only exporter that queries the five
source Neo4j instances directly. That exporter belongs to the authors'
build pipeline and is **not part of this release package**, because it is
meaningless without those instances.

What a third party can check against the deposit instead: OWL-diff each
schema TTL against `../../ontology/spectra.ttl` (the cross-WG generality
numbers in the paper), and re-derive the class and property census with
`../../tests/reproduce_structural_metrics.py`.
