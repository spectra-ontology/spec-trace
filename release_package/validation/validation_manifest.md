# SPECTRA Validation Manifest

This manifest maps every quantitative claim in the accompanying paper to a JSON evidence file in this directory, so reviewers can directly inspect each cited number without access to the internal knowledge graphs.

## Two evidence layers

This directory carries two distinct evidence layers; numbers from one must not be read as contradicting the other:

1. **Design-phase ontology validation (RAN1-first, 137 CQs).** The claim tables below date from the ontology-design phase, in which RAN1 served as the development WG: the 137-CQ coverage matrix, RAN1 instance counts, OOPS! scan, schema-growth series, and SPARQL-portability scan all validate the *schema*. They are kept intact as the paper's design-phase evidence.
2. **Released benchmark reproducibility (5 WGs, 624 scored CQs).** The released SpectraCQ v2.0 benchmark (`cqs/spectra_cq_v2.0/`; 654 authored / 624 released / 30 held out) is governed by `../MANIFEST.md`, the canonical counts manifest. Its reproducibility evidence lives under `cq_replay/`: scratch-reload graph counts (`cq_replay/graph_counts.json`: 966,859 nodes / 4,908,850 relationships; `cq_replay/triple_counts.json`: 12,931,842 RDF triples), five per-WG load reports, five per-WG replay results (624/624 gold match), and `cq_replay/sparql_parity_results.json` (142/142 SPARQL row-count parity — SPARQL translations of all released RAN1 CQs).

The "137" appearing in layer 1 is a design-phase scope label; the SPARQL portability set covers the 142 released RAN1 CQs; the scored benchmark itself is the 624-CQ layer.

## Mapping: paper claim → evidence file

### Structural quality (paper §3, §6.2)

| Paper claim | Evidence file | Field |
|---|---|---|
| 32 classes | `structural_metrics.json` | `classes_total` |
| 53 object properties | `structural_metrics.json` | `object_properties` |
| 81 data properties | `structural_metrics.json` | `data_properties` |
| 134 properties total | `structural_metrics.json` | `properties_total` |
| 20 owl:FunctionalProperty | `structural_metrics.json` | `functional_properties` |
| 2 owl:InverseFunctionalProperty (`hasCR`, `hasTRImpact`) | `structural_metrics.json` | `inverse_functional_properties` |
| 15 inverse property pairs | `structural_metrics.json` | `inverse_property_pairs` |
| 6 owl:IrreflexiveProperty (sec hierarchy + intra-section + TR cross-ref) | `structural_metrics.json` | `irreflexive_properties` |
| 2 owl:AsymmetricProperty (sec hierarchy) | `structural_metrics.json` | `asymmetric_properties` |
| 14 reused external terms (8 DCTERMS + 4 FOAF + 2 VANN; the 5 PROV-O terms are counted separately under `prov_o_alignment`) | `structural_metrics.json` | `reused_external_terms_count`, `reused_dcterms_terms`, `reused_foaf_terms`, `reused_vann_terms` |
| OOPS! results: 0 critical / 2 Important / 2 Minor | `oops_summary.json` | `severity_counts`, `pitfalls` |

### CQ coverage (design-phase RAN1 layer)

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

### Cross-WG queries recounted on the released graphs (paper §6.5)

`cross_wg_use_evidence.json` was measured on the deployed per-WG KGs. `tests/reproduce_scenario_counts.py` recounts each of its 18 counts on the five body-text graphs of the deposit (`kg/per_wg/`) and writes `released_graph_scenario_counts.json`; `compared_with_deployed` sets each count next to its deployed value. 17 of the 18 counts are the same.

| Count | Deployed KG | Released graph | Field |
|---|---|---|---|
| RAN1 LSes to each of the ten recipients listed in `queries[0].result` | ten counts, RAN2 3,644 | the same ten | `s2_ran1_ls_by_recipient.listed`, `s2_ran1_ls_sent_to_ran2` |
| RAN2 LSes originated from RAN1 | 1,450 | 1,450 | `ran2_ls_originated_from_ran1.total` |
| The same, at each of the five meetings listed in `queries[1].top_meetings` | 62, 57, 52, 45, 42 | 62, 57, 52, 45, 42 | `ran2_ls_originated_from_ran1.listed` |
| RAN2 CRs modifying TS 38.300 | 2,039 | 2,039 | `s3_ts_38_300.RAN2.cr_instances` |
| RAN3 CRs modifying TS 38.300 | 270 | 1,249 | `s3_ts_38_300.RAN3.cr_instances` |

The RAN3 count differs. On the released RAN3 graph, 1,249 instances typed `spectra:CR` modify TS 38.300; by their `spectra:type` value, 1,144 draftCR, 105 pCR, and none is CR (`s3_ts_38_300.RAN3.by_type`). The RAN2 count splits into 1,705 CR, 322 draftCR, 12 pCR. Where the paper describes the S2 and S3 cardinalities as reproducible on the released cross-WG graphs, this holds for 17 of the 18 counts and not for the RAN3 count; these files do not establish why the two graphs differ.

Each list of the evidence file has one name outside it with the same count as the lowest entry of the list: one recipient with 26 LSes and one meeting with 42 (`unlisted_at_or_above_lowest_listed`). The 25,586 LS instances of the five graphs carry 25,586 distinct `spectra:tdocNumber` values (`ls_total`, `ls_distinct_tdoc_number`), the canonical distinct LS count in the notes on inter-artefact count differences below.

`queries[0].cypher` sorts on `count`, a name the query does not bind, so as written it stops with a syntax error; the recount counts the same pattern. `queries[1]` records no query text.

### Source fidelity of the released graph (paper appendix)

| Paper claim | Evidence file | Field |
|---|---|---|
| 2,637 flagged rows: 2,303 cleared by the repair, 334 held | `source_fidelity_note.md` | tables "Checks" and "Held records" |
| 334 held records, each naming the invariant it violates and the conflicting values | `source_fidelity_quarantine.json` | `records[]`: `class`, `wg`, `record`, `evidence`, `why` |
| Repair lists: 2,035 value repairs, 153 missing inverse revision links, 979 undeclared origin edges | `source_fidelity_repair_manifest.json` | `repairs[]`, `inverse_edges[]`, `undeclared_origin_edges[]` |

The released 2.0.0 graph carries the values before repair. `source_fidelity_note.md` states how to apply the lists, what they change and which benchmark items they reach.

## Reproducibility

Structural metrics, OOPS! results, and cross-WG schema diff are reproducible against the released ontology TTL (`ontology/spectra.ttl`) using rdflib / OOPS! / pySHACL with no further data dependencies.

The RAN1 instance counts (`ran1_instance_counts.json`) come from the internal SPECTRA-conformant KGs and are reproducible only against a SPECTRA-conformant instantiation; the queries are recorded inside the JSON for re-execution by reusers who instantiate the schema from public 3GPP TDocs. The cross-WG use-evidence counts (`cross_wg_use_evidence.json`) were measured on the same internal KGs; `tests/reproduce_scenario_counts.py` recounts them on the released graphs (17 of 18 the same, see above), and the note above on its query text applies.

## Files

- `structural_metrics.json` — class/property counts and axiom totals (rdflib-derived from `ontology/spectra.ttl`).
- `oops_summary.json` — OOPS! pitfall scanner output for `ontology/spectra.ttl`.
- `cq_coverage.json` — 137-CQ × ontology coverage matrix (which classes/OPs each CQ exercises, derived from internal Cypher patterns).
- `cross_wg_schema_diff.json` — class/OP/DP diff between each per-WG KG and the released SPECTRA TTL.
- `cross_wg_use_evidence.json` — Cypher counts measured on the deployed per-WG KGs for cross-WG use-evidence claims.
- `per_wg_class_coverage.json` — per-WG class-coverage breakdown (which RAN1 classes each non-RAN1 WG instantiates).
- `ran1_instance_counts.json` — full per-class counts of the RAN1 SPECTRA instantiation, plus referential-integrity statistics for `submittedBy`.
- `cq_results.json` — 137 CQ × {phase, id, category, status, source_file} produced by re-executing each CQ's reference Cypher against the internal RAN1 Neo4j KG; the per-phase 100% pass rate reported inline in §6.1 (P1=25/25, P2=34/34, P3=45/45, P4=15/15, P5=18/18) is reconstructable from this file's `summary.by_phase`. (Design-phase record. In the released benchmark, per-CQ execution status is carried as `gold.status` inside `cqs/spectra_cq_v2.0/questions.json`, and benchmark-wide replay evidence lives under `cq_replay/`.)
- `ran1_relation_integrity.json` — per-relation integrity metrics on the operational RAN1 KG: `submittedBy` referential integrity (99.36%), `presentedAt`/`madeAt` loader-enforced (100%), `references`/`modifiesSection` machine-resolvable linkage coverage (51.55%/34.66%). Each metric carries an explicit denominator and source.
- `schema_growth_evidence.json` — per-phase counts (classes / OPs / DPs / cumulative CQs) for Figure on schema growth (§5.1), with refactoring notes for the Released v1.0.0 bar (net −6 DPs, +2 OPs, classes and 137 CQs unchanged).
- `cypher_to_sparql_portability.json` — static-scan classification of the 137 RAN1-subset SpectraCQ Cypher queries by SPARQL-translation portability: 137/137 schema-level translatable, 0 Neo4j-specific. Executed row-count parity for the shipped SPARQL set — all 142 released RAN1 CQs — is recorded in `cq_replay/sparql_parity_results.json` (142/142 match).
- `example_queries_results.json` — execution results of the 6 bundled representative SPARQL queries (`queries/sparql/*.rq`) against the released `kg/per_wg/RAN1-body.ttl` (row counts, first-row samples, per-query elapsed time).
- `source_fidelity_repair_manifest.json`: the repair lists of the source-fidelity audit, namely value repairs (`repairs[]`), missing inverse revision links (`inverse_edges[]`) and origin edges no source field declares (`undeclared_origin_edges[]`). Not applied in the released 2.0.0 graph; see `source_fidelity_note.md`.
- `source_fidelity_quarantine.json`: the 334 held records, each with the invariant it violates (`class`), the conflicting values (`evidence`) and the reason (`why`).
- `released_graph_scenario_counts.json`: the 18 counts of `cross_wg_use_evidence.json` recounted on the released body-text graphs by `tests/reproduce_scenario_counts.py`, with the digests of the graph files read (`inputs`) and each count next to its deployed value (`compared_with_deployed`).

**Total: 15 JSON evidence files** at the top level of `validation/` (the 2.0.0 deposit carries all but the two source-fidelity lists and the scenario recount), plus the `cq_replay/` benchmark-reproducibility directory (graph/triple counts, five per-WG load reports, five per-WG replay results, SPARQL parity), `chart_parser_fidelity_note.md` and `source_fidelity_note.md`. The deterministic verification (`tests/verify_release.py` §6) walks `validation_manifest.md` and resolves every `*.json` reference.

## PROV-O alignment (paper §4.3)

| Paper claim | Evidence |
|---|---|
| 6 `rdfs:subClassOf` axioms (Resolution⊑prov:Activity, Tdoc⊑prov:Entity, Company⊑prov:Agent + Company⊑foaf:Organization, Contact⊑prov:Agent + Contact⊑foaf:Person) — 6 triples | `ontology/spectra.ttl` lines following "Optional PROV-O alignment" comment block; `structural_metrics.json::prov_o_alignment.subclass_axioms` (6 entries) |
| Total triples 914 (after dropping 3 spurious owl:FunctionalProperty declarations on multi-valued links: presentedAt, modifies, originatedFrom) | `structural_metrics.json::triples_total=914`; reproducible by `tests/reproduce_structural_metrics.py` |

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
| 5-stage pipeline (scrape → deterministic Tdoc/Resolution metadata parse → deterministic CR/TR document parse via python-docx → SHACL → bulk Neo4j load); LLM (Gemini-2.5-flash) is used only for downstream validation (NL-CQ → Cypher, answer-quality scoring), not in the KG-population path | The metadata-snapshot generator in the authors' build pipeline (whitelist of 89 metadata fields, 20 excluded text fields documents the parser output schema) is not part of the public release artifact, because it runs against the five source Neo4j instances; its output schema is visible in `examples/process_kg/_export_summary.txt`; paper §7 |
| Throughput claim "$O(10^3)$ TDocs/min on a single workstation" | Internal benchmark; not part of the public release artifact (see "Reproducibility" caveat below) |

## Notes on inter-artefact count differences (paper-side numbers unchanged)

The following small deltas exist between the operational-KG snapshot (the `validation/*.json` artefacts that source paper Tables 6–8) and the metadata-only TTL export at `examples/process_kg/_export_summary.txt`. **All paper-cited numbers remain those in the operational-KG snapshot; the deltas below are export-time properties of the public TTL bundle and do not change any paper claim.**

- **CR per-RAN1**: `ran1_instance_counts.json` (Table 6 source) = **10,715**; `_export_summary.txt` "RAN1 TDoc metadata > CR" = **10,671**. The 44-CR delta arises because the metadata-only export strips body content and applies stricter join semantics on cross-referencing fields; reviewers diffing the two artefacts should not interpret the delta as inconsistency.
- **Summary per-RAN1**: `ran1_instance_counts.json` = **3,468**; `_export_summary.txt` = **3,469**. Same export-side cause; +1 cell delta.
- **LS aggregate across RAN1–RAN5**: `_export_summary.txt` shows two figures on adjacent lines:
  - `PER-WG-ENDPOINT SUM: 26,791` — **NOT a distinct-LS count**; each cross-WG LS is counted once per endpoint WG it touches. This figure should NOT be cited as the distinct LS total.
  - `CANONICAL DISTINCT LS COUNT: 25,586` — paper-cited figure; de-duplicated by `tdocNumber` across the union. This is the value paper Appendix §A.dq cites as "1,556 of 25,586 distinct LSs (6.1%)".
  The `_export_summary.txt` header makes this distinction prominent to reduce the risk of downstream consumers accidentally citing 26,791 instead of 25,586.
- **`ls_routing.ttl` triple count**: `examples/process_kg/SCHEMA.md` reports `195,434 triples` (export-time snapshot, 2026-04-29). Re-parsing the same file under `rdflib 6.x` as of 2026-05-11 yields `195,968 triples` — a +0.27% delta from implementation-side metadata triples that rdflib emits on parse. Paper Appendix §G "2.44M union triples" is reproducible under either reading.
- **Per-WG outgoing LS coverage range (51.9–96.6%)** mentioned in Appendix §A.dq is computed per RAN-WG over `ls_routing.ttl` and is not currently exposed as a separate per-WG LS-coverage JSON artefact. Future v1.0.x releases may add such a JSON; in the interim the range is reproducible via offline parse of the released `examples/process_kg/ls_routing.ttl`.
