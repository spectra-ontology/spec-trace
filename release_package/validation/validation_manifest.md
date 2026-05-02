# SPECTRA Validation Manifest

This manifest maps every quantitative claim in the accompanying paper to a JSON evidence file in this directory, so reviewers can directly inspect each cited number without access to the internal knowledge graphs.

## Mapping: paper claim → evidence file

### Structural quality (paper §3, §6.2)

| Paper claim | Evidence file | Field |
|---|---|---|
| 26 classes | `structural_metrics.json` | `classes_total` |
| 53 object properties | `structural_metrics.json` | `object_properties` |
| 81 data properties | `structural_metrics.json` | `data_properties` |
| 134 properties total | `structural_metrics.json` | `properties_total` |
| 20 owl:FunctionalProperty | `structural_metrics.json` | `functional_properties` |
| 2 owl:InverseFunctionalProperty (`hasCR`, `hasTRImpact`) | `structural_metrics.json` | `inverse_functional_properties` |
| 15 inverse property pairs | `structural_metrics.json` | `inverse_property_pairs` |
| 6 owl:IrreflexiveProperty (sec hierarchy + intra-section + TR cross-ref) | `structural_metrics.json` | `irreflexive_properties` |
| 2 owl:AsymmetricProperty (sec hierarchy) | `structural_metrics.json` | `asymmetric_properties` |
| 8 reused external terms (5 DC + 1 DCTERMS + 2 FOAF) | `structural_metrics.json` | `reused_external_terms_count`, `reused_dc_terms`, `reused_foaf_terms` |
| OOPS! results: 0 critical / 2 Important / 2 Minor | `oops_summary.json` | `severity_counts`, `pitfalls` |

### CQ coverage (paper §6.1)

| Paper claim | Evidence file | Field |
|---|---|---|
| 137 CQs (137/137) return non-empty results | `cq_coverage.json` + `cq_results.json` | `metadata.total_cqs`; `cq_results.json::summary.pass_rate_pct=100.0`; per-CQ status in `cq_results.json::results[]` |
| 137 CQs span Phases 1-5 (25/34/45/15/18) | `cq_coverage.json` | `phase_coverage` |
| 137 CQs exercise 20/26 classes (77%) | `cq_coverage.json` | `summary.classes_covered`, `summary.classes_total` |
| 137 CQs exercise 31/53 OPs (58%) | `cq_coverage.json` | `summary.ops_covered`, `summary.ops_total` |
| Uncovered classes (Chart, Figure, LS, SessionNotes, Summary, Table) | `cq_coverage.json` | `summary.classes_uncovered_list` |

### Instantiation at scale (paper §6.3)

| Paper claim | Evidence file | Field |
|---|---|---|
| 123,677 Tdocs in RAN1 instantiation | `ran1_instance_counts.json` | `RAN1.counts.Tdoc` |
| 60 RAN1 meetings | `ran1_instance_counts.json` | `RAN1.counts.Meeting` |
| `submittedBy` referential integrity = 99.36% | `ran1_instance_counts.json` | `RAN1.referential_integrity.tdoc_submittedBy_completeness_pct` |
| 1,000 missing `submittedBy` links / 155,525 Tdoc-Company associations | `ran1_instance_counts.json` | `RAN1.referential_integrity.tdoc_missing_submittedBy`, `…tdoc_total` (sum-with-companies = 155,525) |
| Per-class counts (CR 10,715; LS 6,343; Resolution 24,710; …) | `ran1_instance_counts.json` | `RAN1.counts.*` |

### Cross-WG generality (paper §6.4)

| Paper claim | Evidence file | Field |
|---|---|---|
| RAN2-5 vs RAN1: +0 classes, +1 OP (`REFERENCES_SPEC`), +22 DPs (20 loader-local + 2 genuine) | `cross_wg_schema_diff.json` | `aggregate_non_ran1.{classes,object_properties,data_properties}` |
| Per-WG ontology-level extensions (RAN2 0/1/0, RAN3 0/1/1 `summaryId`, RAN4 0/1/0, RAN5 0/1/1 `discussionText`) | `cross_wg_schema_diff.json` | `per_wg.RAN{2,3,4,5}.*.wg_extensions` |
| Per-WG class coverage (RAN1 26/26, RAN2 22/26, RAN3 23/26, RAN4 24/26, RAN5 20/26) | `per_wg_class_coverage.json` | `per_wg_class_coverage` |

### Cross-WG queries on deployed KGs (paper §6.5)

| Paper claim | Evidence file | Field |
|---|---|---|
| RAN1 KG: 3,644 LSes addressed to RAN2 (RAN4 1,457; RAN3 380) | `cross_wg_use_evidence.json` | `queries[0].result` |
| RAN2 KG: 1,450 LSes originated from RAN1; peak RAN2#118-e (62) | `cross_wg_use_evidence.json` | `queries[1].total`, `queries[1].top_meetings` |
| TS 38.300 jointly modified by 2,039 RAN2 CRs and 270 RAN3 CRs | `cross_wg_use_evidence.json` | `queries[2].result` |

## Reproducibility

Structural metrics, OOPS! results, and cross-WG schema diff are reproducible against the released ontology TTL (`ontology/spectra.ttl`) using rdflib / OOPS! / pySHACL with no further data dependencies.

The cross-WG use-evidence counts (`cross_wg_use_evidence.json`) and RAN1 instance counts (`ran1_instance_counts.json`) come from the internal SPECTRA-conformant KGs and are reproducible only against a SPECTRA-conformant instantiation; the queries are recorded inside the JSON for re-execution by reusers who instantiate the schema from public 3GPP TDocs.

## Files

- `structural_metrics.json` — class/property counts and axiom totals (rdflib-derived from `ontology/spectra.ttl`).
- `oops_summary.json` — OOPS! pitfall scanner output for `ontology/spectra.ttl`.
- `cq_coverage.json` — 137-CQ × ontology coverage matrix (which classes/OPs each CQ exercises, derived from internal Cypher patterns).
- `cross_wg_schema_diff.json` — class/OP/DP diff between each per-WG KG and the released SPECTRA TTL.
- `cross_wg_use_evidence.json` — Cypher counts measured on the deployed per-WG KGs for cross-WG use-evidence claims.
- `per_wg_class_coverage.json` — per-WG class-coverage breakdown (which RAN1 classes each non-RAN1 WG instantiates).
- `ran1_instance_counts.json` — full per-class counts of the RAN1 SPECTRA instantiation, plus referential-integrity statistics for `submittedBy`.
- `cq_results.json` — 137 CQ × {phase, id, category, status, source_file} produced by re-executing each CQ's reference Cypher against the internal RAN1 Neo4j KG; the per-phase 100% pass rate reported inline in §6.1 (P1=25/25, P2=34/34, P3=45/45, P4=15/15, P5=18/18) is reconstructable from this file's `summary.by_phase`. Also surfaced as a `verdict` field in `release_package/cqs/spectra_cq_v1.0/questions.json` for per-CQ inspection.
- `ran1_relation_integrity.json` — per-relation integrity metrics on the operational RAN1 KG: `submittedBy` referential integrity (99.36%), `presentedAt`/`madeAt` loader-enforced (100%), `references`/`modifiesSection` machine-resolvable linkage coverage (51.55%/34.66%). Each metric carries an explicit denominator and source.
- `schema_growth_evidence.json` — per-phase counts (classes / OPs / DPs / cumulative CQs) for Figure on schema growth (§5.1), with refactoring notes for the Released v1.0.0 bar (net −6 DPs, +2 OPs, classes and 137 CQs unchanged).
- `cypher_to_sparql_portability.json` — static-scan classification of the 137 SpectraCQ Cypher queries by SPARQL-translation portability (graph-pattern + standard-aggregate vs Neo4j-specific). Backs the 136/137 portability indicator quoted in §7.

**Total: 11 JSON evidence files** under `validation/`. The deterministic verification (`tests/verify_release.py` §6) walks `validation_manifest.md` and resolves every `*.json` reference.

## PROV-O alignment (paper §4.3)

| Paper claim | Evidence |
|---|---|
| 6 `rdfs:subClassOf` axioms (Resolution⊑prov:Activity, Tdoc⊑prov:Entity, Company⊑prov:Agent + Company⊑foaf:Organization, Contact⊑prov:Agent + Contact⊑foaf:Person) — 6 triples | `ontology/spectra.ttl` lines following "Optional PROV-O alignment" comment block; `structural_metrics.json::prov_o_alignment.subclass_axioms` (6 entries) |
| Total triples 887 (after dropping 3 spurious owl:FunctionalProperty declarations on multi-valued links: presentedAt, modifies, originatedFrom) | `structural_metrics.json::triples_total=887`; reproducible by `tests/reproduce_structural_metrics.py` |

## Schema growth (paper §5.1, Figure 4)

| Paper claim | Evidence |
|---|---|
| Schema grew from 11 classes (P1+P2) to 26 classes (P5); v1.0.0 incorporates cross-phase refactoring (net -6 DPs and +2 OPs, classes and 137 CQs unchanged) | `schema_growth_evidence.json` (per-phase counts of classes / OPs / DPs / cumulative CQs + refactoring notes for the Released bar) |

## Per-relation integrity (paper §6.3)

| Paper claim | Evidence |
|---|---|
| `submittedBy` integrity 99.36% on RAN1 | `ran1_relation_integrity.json::relations.submittedBy.pct` |
| `presentedAt` (Tdoc→Meeting) and `madeAt` (Resolution→Meeting) at 100% (loader-enforced); `references` (Resolution→Tdoc) 51.55% and `modifiesSection` (CR→Section) 34.66% reflect 3GPP citation granularity rather than schema gaps | `ran1_relation_integrity.json::relations.{presentedAt,madeAt,references,modifiesSection}` |

## Parsing pipeline (paper §7)

| Paper claim | Evidence |
|---|---|
| 5-stage pipeline (scrape → deterministic Tdoc/Resolution metadata parse → deterministic CR/TR document parse via python-docx → SHACL → bulk Neo4j load); LLM (Gemini-2.5-flash) is used only for downstream validation (NL-CQ → Cypher, answer-quality scoring), not in the KG-population path | `scripts/paper/generate_metadata_kg_snapshot.py` (whitelist of 89 metadata fields, 20 excluded text fields documents the parser output schema); paper §7 |
| Throughput claim "$O(10^3)$ TDocs/min on a single workstation" | Internal benchmark; not part of the public release artifact (see "Reproducibility" caveat below) |
