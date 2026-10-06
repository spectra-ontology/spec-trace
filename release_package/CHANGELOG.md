# Changelog

All notable changes to the SPECTRA release package are documented in this file.
Version numbers follow [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **SpectraCQ-Core scoring key** (`cqs/spectra_cq_v2.0/core_answer_gold.jsonl`):
  for each of the 560 Core items, its declared answer column and the gold
  value set of that column; 553 sets come from the released reference query
  and 7 from a scope-repaired query carried on the same line.
- **Contract-exact subset** (`cqs/spectra_cq_v2.0/splits/contract_exact_241.txt`):
  the 241 Core items whose `contract_disposition` is 1, that is, with no
  contract flag set. An evaluation subset, not a fifth split; superseded (see
  Changed).
- **Column-demand provenance** (`cqs/spectra_cq_v2.0/contract_demand_provenance.jsonl`):
  for each returned column of the 624 released CQs, whether the question
  requires it, the method that decided it and the words it rests on. Rules
  decide 1,339 of the 1,616 columns; a language model decides 277, on 232 items.
- **Rule-only legacy contract subset** (`cqs/spectra_cq_v2.0/splits/contract_exact_rule_only_149.txt`):
  the 149 legacy items with no language-model verdict. An evaluation
  subset, not a fifth split; superseded (see Changed).
- **Annotation-derived contract subsets**
  (`cqs/spectra_cq_v2.0/splits/contract_exact_asked_208.txt`,
  `cqs/spectra_cq_v2.0/splits/contract_exact_script_fixed_133.txt`): the 208
  Core items in which no contract flag is set and every column marked
  `required` is the scored answer column, and the 133 of them whose membership
  is invariant to model verdicts with the rules, flags and answer column fixed.
  Evaluation subsets, not splits or semantic validation sets; historical
  filenames and annotation labels are preserved.
- **Contract-exact list rebuild** (`cqs/spectra_cq_v2.0/splits/rebuild_contract_splits.py`):
  rebuilds the four contract-exact lists from three files in
  `cqs/spectra_cq_v2.0/` and checks them byte for byte, with no database and
  no network.
- **Annotation diagnostic** (`cqs/spectra_cq_v2.0/contract_annotation_diagnostics.json`
  and `cqs/spectra_cq_v2.0/splits/audit_demand_annotations.py`): complete
  enumeration of unscored returned fields and syntactic query-order/limit
  signals, input hashes and three source-grounded examples. These diagnose
  scoring scope; they are not semantic error prevalence or expert validation.
- **Contract held-out list** (`cqs/spectra_cq_v2.0/held/contract_held_out.json`):
  the 64 released CQs outside Core, with question, gold columns, gold row
  count and one of 5 reason classes. Distinct from the 30 CQs of
  `cqs/spectra_cq_v2.0/held/held_cqs.json`.
- **Core scorer** (`paper/baseline/score_core.py`, at the repository root):
  re-scores the recorded runs on a contract-exact subset (the 133, by default)
  or on all of Core against the Core scoring key, with no network and no model
  call.
- **Full-record scorer** (`paper/baseline/score_full_record.py`, at the
  repository root) and its replay files (`paper/baseline/results/_full_record/`):
  every query the graph-grounded runs recorded, executed again on the released
  graph of its group together with the reference queries, so that the 560 Core
  items can be scored on whole returned records rather than on the answer
  column alone. Scoring reads the replay files and needs no database.
- **Full-record scorer options** (`paper/baseline/score_full_record.py score`):
  `--set` and `--answer-type` average over a subset of Core, and `--ci` adds
  paired bootstrap 95% intervals of each model's F1 and counts the model pairs
  they separate. The default output is unchanged.
- **Offline scoring-sensitivity analysis** (`paper/baseline/analyse_contract_subsets.py`):
  derives the 133/208/132 populations from public annotations and preserved
  lists, separates answer-column and whole-record S/P/C scoring, and reports
  declared-type, track, group and surface query composition analyses. Optional
  paired item intervals compare each graph model with both fixed and
  per-resample reselected original 18-arm text comparators. The JSON records
  input/source hashes, population identifiers, metric definitions and limits;
  no new model or database query is run.
- **Recorded scoring-sensitivity artifact** (`paper/baseline/results/contract_subset_analysis.json`):
  actual all-scope analysis of 30 populations, with 52 input/source hashes,
  10,000 paired seed-0 resamples and fixed/reselected original-text comparisons.
  The CLI's `--ids PATH` also supports one externally fixed Core identifier
  list, hashing it and rejecting empty, duplicate or unknown identifiers.
- **AI-assisted field-coverage diagnostic** (`cqs/spectra_cq_v2.0/field_coverage_review.json`,
  `splits/field_coverage_reviewed_ids.txt` and `splits/rebuild_field_coverage_subset.py`
  under that CQ directory): two isolated Codex AI reviews of all 133
  candidates, with a fixed question/query/column protocol, stored judgments
  and anchors, and their 67-item intersection frozen before re-scoring.
  The checker reproduces the stored intersection without repeating AI
  judgments or certifying semantics. This is not human or expert validation;
  excluded mismatch/ambiguous items do not estimate semantic error prevalence.
- **Recorded field-coverage subset analysis** (`paper/baseline/results/field_coverage_subset_analysis.json`):
  offline `--ids` scoring of the fixed 67, with 10,000 paired seed-0
  resamples. Answer-column pooled F1 is 0.650757; full-record S/P/C is
  0.428063 under each rule, with 9 models above reselected original-text
  scoring under each. The cohort has no declared tuple/mapping items and is
  concentrated in lookup/aggregation. It supplements Core and the 133/208;
  the annotation-derived 133 remains the compatibility default. Questions,
  gold and recorded outputs are unchanged; the field judgments are AI-assisted.
- **Relational (NL-to-SQL) arm** (under `paper/baseline/`, at the repository
  root): the loader `build_relational_db.py`, which flattens each group's graph
  into SQLite; the schema cards `sql_schema_cards.json` the model is shown; and
  one recorded run of 624 rows under `relational/runs/`. The SQLite files
  are rebuilt by the loader and are not tracked.
- **Retained full-Core SQL/Cypher comparison** (`paper/baseline/analyse_structured_access.py`
  and `paper/baseline/results/structured_access_core_analysis.json`): the two
  claude-opus-4.8 runs scored on the same repaired 560-item answer-column key,
  retaining failed queries as zero. SQL/Cypher F1 is 0.373614/0.351949;
  the difference 0.021665 has paired seed-0/10,000-draw CI
  [-0.001249, 0.044760], including zero. Per-item results and 13 input/source
  hashes are retained. No new model, query or database execution occurs;
  this does not restore the historical SQL325/290 comparison or its database
  snapshot, establish engine causality or certify all question requirements.
- **Source-fidelity lists** (`validation/source_fidelity_repair_manifest.json`,
  `validation/source_fidelity_quarantine.json`, `validation/source_fidelity_note.md`):
  the repair lists and the 334 held records of the content-fidelity
  audit, with a note on their state (not applied in the 2.0.0 graph), how to
  apply them and the benchmark items they reach.
- **Scenario recount** (`tests/reproduce_scenario_counts.py`,
  `validation/released_graph_scenario_counts.json`): the 18 cross-WG query
  counts of `validation/cross_wg_use_evidence.json` recounted on the
  body-text graphs of the deposit. 17 are the same; the RAN3 count of
  change requests on TS 38.300 is 1,249 rather than 270.

These additions are in the Git tree only; none is inside the 2.0.0 deposit.

### Changed
- **Core scorer default** (`paper/baseline/score_core.py`): the default set is
  now `contract_exact_script_fixed_133`. `contract_exact_241` and
  `contract_exact_rule_only_149` stay selectable and are superseded:
  disposition 1 bounds the recorded required-column count, not identity, and
  in 33 of the 241 the one column marked `required` is not the scored answer column. No
  scoring rule changed. The docstring of `paper/baseline/score_full_record.py`
  now states that a returned row is compared as its values sorted within the
  row.
- **Scoring and reproduction scope documentation:** the 133/208 conditions
  are now stated as properties of recorded annotations, with count and
  ordering counterexamples to a semantic guarantee. The 132 diagnostic subset
  is explicitly `149 ∩ 133`. Documentation distinguishes answer-column value
  scoring, whole-record replay and frozen Zenodo bytes from Git additions.
  It also records the missing historical SQL325 cohort identifiers, the
  unverified meaning of the associated `290` label and the absent per-item
  outputs of rebuilt text comparators. These are disclosed limitations; the
  benchmark, gold, annotations, subset membership and recorded runs are unchanged.
- **Ontology 1.1.1** (`ontology/spectra.ttl`, mirrored at `docs/spectra.ttl`):
  metadata-only change making the vocabulary conform to the Linked Open
  Vocabularies (LOV) submission requirements. Adds
  `vann:preferredNamespacePrefix` / `vann:preferredNamespaceUri`, replaces
  the literal creator string with the author's ORCID iD as a
  `dcterms:creator` URI (typed `foaf:Person`), adds a `dcterms:publisher`
  organization URI (typed `foaf:Organization`), and adds `rdfs:label`,
  `dcterms:issued` and `dcterms:modified`. The five DC Elements 1.1
  properties the header used are migrated to DCMI Terms, so the `dc:`
  prefix no longer appears in the ontology file; the hand-written example
  instance data under `examples/` still uses it. No class, property, or
  axiom is added, changed, or removed — 32 classes and 53/81 object/data
  properties are unchanged; the triple count rises 904 → 914 and reused
  external terms 8 → 14 (8 DCTERMS + 4 FOAF + 2 VANN) purely from the
  added metadata statements. Structural metrics, release gates
  (`verify_release.py`), DCAT/VoID metadata, README, ARTIFACT and supplement
  appendix updated to the new counts.
- **Ontology serialization** (`ontology/spectra.ttl`): the namespace
  `https://w3id.org/spectra#` is bound to the prefix `spectra:` instead of
  `tdoc:`, so the file agrees with its own `vann:preferredNamespacePrefix`
  and with the prefix already used by the SpectraCQ SPARQL suite, the
  released KG exports and the example queries. Prefix binding is
  file-local Turtle syntax and carries no meaning: apart from the
  `rdfs:label` literal the two graphs are isomorphic, checked with
  `rdflib.compare.to_isomorphic` (913 shared triples, one replaced).
  Three declared-but-unused prefixes are dropped, `prov:` is declared so
  the six PROV-O alignment axioms read in prefixed form rather than as
  full IRIs, `rdfs:label` carries the full ontology title instead of the
  bare string "SPECTRA", and the closing comment loses a version stamp
  that had been left behind at 1.0.0.
- **HTML documentation** (`docs/spectra.html`): regenerated with
  pyLODE 2.13.2 from the 1.1.1 TTL. The previous file carried a
  hand-edited author line with no triple behind it; the generated page
  now derives everything it shows from the ontology — ORCID iD,
  publisher organization, `dcterms:issued` / `dcterms:modified`, the
  full title, and `default (spectra)` in the namespace table.
- **DCAT/VoID description** (`metadata/dcat_void.ttl`): the catalog
  publisher is now the same `foaf:Organization` URI used by the ontology
  header instead of a blank node, and the ontology dataset's measured
  `void:triples` (914) and `dcat:byteSize` (55,202 bytes) are re-measured
  against the new TTL (208 → 209 triples in this description file).

## [2.0.0] — 2026-07-23

Major release for the KDD 2027 Datasets & Benchmarks submission.

### Added
- **Canonical splits** (`cqs/spectra_cq_v2.0/splits/`): four evaluation
  splits over the 624-question key — standard 60/20/20 stratified over the
  20 (working group x track) strata, a template-disjoint split, a
  cross-group split holding RAN5 out in full, and a 33-question challenge
  subset — with the stratification axis, the composition and leakage audit,
  and `rebuild_splits.py`, which reproduces every list byte for byte with
  no database and no network.
- **Answer contract** (`cqs/spectra_cq_v2.0/answer_contract.jsonl`): one
  line per SpectraCQ-Core item (560) recording the graded answer type and
  columns, the ordering key and cardinality the reference query imposes,
  and annotated contract flags (historically described as changes needed to
  hold exactly as asked; see the scope clarification under Unreleased).
- **Release verifier** (`tests/verify_benchmark.py`): two modes — a quick
  mode that checks the shipped files against the recorded answer key with
  no database, and a full mode that reloads and replays.
- **Cell-level SPARQL/Cypher comparison harness**
  (`paper/baseline/sparql_row_equivalence.py`, at the repository root): puts
  the full result sets side by side cell by cell rather than counting rows,
  with a stated normalization ladder, a mutation-sensitivity control and an
  RDFS-closure control. This supersedes the "value-level cross-engine
  comparison tracked as future work" noted under 1.0.0 below; see
  `MANIFEST.md` §2.1 for the result and for what is and is not shipped.

### Changed
- **Ontology 1.1.0** (`ontology/spectra.ttl`, mirrored at `docs/spectra.ttl`):
  declares the six entity-layer classes (`RRCParameter`, `CapabilityItem`,
  `Feature`, `Procedure`, `PerformanceRequirement`, `ConformanceTest`) whose
  instances the per-WG body KG exports already carry, alongside the 26
  process-layer classes — 32 classes, 904 triples. Adds `owl:versionIRI`
  and `owl:priorVersion` to the ontology header. Object/data property
  counts (53/81) and all axiom counts are unchanged.
- **SpectraCQ v2.0** (`cqs/spectra_cq_v2.0/`, directory renamed from
  `cqs/spectra_cq_v1.0/`): the released question set is now the full
  scored 5-WG suite — 624 scored CQs (654 authored; 30 held out under
  `held/`) with per-WG deterministic gold answer sets — replacing the
  137 design-phase CQ set shipped in v1.0.x. Dataset metadata
  (`questions.json`, `croissant.json`, `CITATION.cff`, `citation.bib`)
  and all living references updated to the new path and version.
- **SpectraCQ gold regeneration with deterministic tie-breaks**: gold
  answers regenerated from the deployed graphs with explicit deterministic
  ordering; replay now reproduces 624/624 released CQs exactly.
- **Per-WG body KG exports**: 3,214 repo-relative path literals (internal
  build-environment artifacts) removed from the TTL exports; graph
  structure and all entity/relationship content unchanged.
- **Authorship de-anonymized** for the Datasets & Benchmarks submission:
  author attribution restored in release metadata.
- Structural metrics, release gates (`verify_release.py`,
  `paper_claim_verifier.py`), DCAT/VoID metadata, README, and schema
  overview updated to the 32-class / 904-triple state.
- Repository URLs corrected across metadata and docs
  (`spectra-ontology/spectra` → `spectra-ontology/spec-trace`; the former
  was never a live repository).
- Supplement (`supplement/standalone_appendix.tex`, `supplement/README.md`)
  aligned with the unified single-author, venue-neutral release metadata.

## [1.0.1] — 2026-06-12

Resource-package improvements responding to peer-review feedback. The
ontology (`spectra.ttl`), SHACL shapes, SpectraCQ question set, and all
released KG data files are byte-identical to v1.0.0; this patch adds
metadata, queries, documentation, and reproducibility tooling only.

### Added

- **DCAT/VoID dataset description** (`metadata/dcat_void.ttl`): every
  released dataset in both distribution channels (GitHub + Zenodo)
  described as `dcat:Dataset`/`void:Dataset` with measured triple
  counts, class partitions, byte sizes, distributions, and licenses
  (208 triples; validates with rdflib).
- **Full SPARQL translation of SpectraCQ**
  (`cqs/spectra_cq_v1.0/sparql/`): all 137 CQs translated from the
  reference Cypher (previously 6 illustrative examples under
  `queries/sparql/`); each file parses under rdflib (137/137) and
  carries the CQ text and source pointer. Class-membership guards
  default to `FILTER EXISTS` rather than positive `rdf:type` patterns
  so that greedy join planners (e.g. rdflib) do not form
  class-enumeration cross products; positive type triples appear only
  where the type pattern is itself the query (instance censuses), is
  anchored to a constant lookup, or — in two queries, documented by
  per-file engine notes — replaces a per-row `FILTER EXISTS` that
  rdflib evaluates too slowly at that join size. Row-count parity
  against the Cypher replay is verified by
  `pipeline/validate_sparql_parity.py`: 137/137 row-count match, all
  non-empty, no errors. The validator further classifies each match by
  re-running every `LIMIT` query unbounded: 75 are exact-cardinality
  (the count is the full result-set size) and 62 are top-N bounded by a
  shared `LIMIT` (cardinality parity only — N == N is guaranteed by the
  shared truncation, so it does not yet establish row-level equivalence).
  A value-level cross-engine result-set comparison is tracked as future
  work (`validation/cq_replay/sparql_parity_results.json`).
- **Public end-to-end CQ replay tooling** (`pipeline/load_released_kg.py`,
  `pipeline/run_cq_suite.py`, `pipeline/validate_sparql_parity.py`,
  `pipeline/validate_example_queries.py`):
  loads the released per-WG TTL into a fresh Neo4j container and
  re-executes the 137-CQ suite from released artifacts only; the replay
  evidence (load report + 137/137 PASS results) ships under
  `validation/cq_replay/`.
- **Contributor guide** (`CONTRIBUTING.md`): CQ proposal workflow,
  ontology-extension policy (SemVer + regression gates), cross-WG/SDO
  instantiation guidance, bug-report conventions.

### Fixed

- `queries/sparql/` representative examples: of the six v1.0.0 example
  queries, only CQ1-1 returned rows when executed against the released
  `RAN1-body.ttl`. The other five carried schema-level constants or
  predicate names that do not occur in the released data (a section
  with no cover-sheet CRs, a CR with no clause edge, `impactOfTR`
  vs. the released `impactOfTr`, the Agreement/Resolution paired-IRI
  realization, and a meeting hop the released CR individuals do not
  carry). All five are rewritten with constants verified against the
  released TTL and notes documenting the realization; execution results
  are recorded by `pipeline/validate_example_queries.py`.
- `examples/process_kg/SCHEMA.md`: the "Retained properties" list now
  reflects a direct predicate census of the released files; properties
  exercised only in the per-WG body-text KGs are listed separately
  (previously seven of them were wrongly implied to be present in the
  metadata-only exports).
- `README.md`: corrected the GitHub-channel size description (the
  schema-instantiation process-KG TTLs total ~93 MB; the earlier
  "~5 MB" predated their inclusion) and linked the DCAT/VoID file.
- `validation/validation_manifest.md`: reworded the note about the
  per-WG LS-coverage range so the deterministic reference checker no
  longer misreads a documented-as-absent artefact name as a missing
  file (restores `tests/verify_release.py` to all-pass).

## [1.0.0] — 2026-05-08 (camera-ready; Zenodo DOI [10.5281/zenodo.20034872](https://doi.org/10.5281/zenodo.20034872) minted)

First public release accompanying the paper
*"SPECTRA: A Traceability Ontology for the 3GPP RAN Standardization Process"*.

### Included

- **Ontology** (`ontology/spectra.ttl`): 26 classes, 53 object properties, 81
  data properties, 886 triples; PROV-O alignment as 6 optional
  `rdfs:subClassOf` axioms; reuses Dublin Core, DCTERMS, FOAF.
- **SHACL shapes** (`shapes/spectra-core.shacl.ttl`): 8 `sh:NodeShape`s
  covering the lifecycle classes; cardinality and range constraints captured
  portably; rationales for shape relaxations (`presentedAt`, `modifies`,
  `originatedFrom`, `sentTo`) annotated inline.
- **PyLODE HTML documentation** (`docs/spectra.html`).
- **SpectraCQ v1.0** (`cqs/spectra_cq_v1.0/`): 137 competency questions ×
  {phase, category, NL question, schema area, executable Cypher, verdict};
  separately citable under CC-BY 4.0 with its own CITATION.bib.
- **Representative queries** (`queries/`): 15 Cypher + 6 SPARQL examples
  (all 137 SpectraCQ Cypher queries are schema-level patterns directly
  translatable to SPARQL via the same schema; the 6 SPARQL examples
  illustrate this for the most-cited scenarios).
- **Synthetic and metadata-only examples**: end-to-end synthetic 4-hop
  traceability scenario (`examples/end_to_end/`); metadata-only real-world
  mini sample of one RAN1 meeting (`examples/real_world_mini/`); cross-WG
  process KG over RAN1–RAN5 (`examples/process_kg/`; LS routing 195K
  triples, CR routing 1.25M triples, RAN1 TDoc structural metadata 991K
  triples; 2.44M-triple union conforms to the SHACL shapes with zero
  violations).
- **Per-WG body-text KGs** (`kg/per_wg/`): sentence-level rendered text
  retained with 3GPP attribution per the project's Terms-of-Use note,
  following the same redistribution framing as TSpec-LLM
  (Nikbakht et al., 2024) and the GSMA `telecom-kg-rel19` release.
- **Sanitized parsing pipeline source** (`pipeline/`): 5-stage recipe
  (scrape → metadata parse → CR/TR document parse via `python-docx` →
  SHACL → bulk Neo4j load); company-internal monitoring/auth wrappers
  removed.
- **Reproducibility tests** (`tests/verify_release.py`): deterministic
  checks across all manifest-referenced claims; expected: all checks PASS on a clean release. Sections cover: TTL parse + 886 triples;
  instantiation snippet SHACL conformance; process-KG union SHACL
  conformance; end-to-end SPARQL; SpectraCQ counts/verdict; structural
  metrics; manifest references; synthetic-instantiation sanity; release directory
  inventory). Depends only on `rdflib` and `pyshacl`; runs in any
  Python 3.10+ environment with no Samsung-internal infrastructure
  required.
- **Validation evidence** (`validation/`): 11 JSON files +
  `validation_manifest.md` mapping every quantitative claim in the paper
  to its supporting evidence file.
- **Croissant metadata** (`cqs/spectra_cq_v1.0/croissant.json`):
  ML Commons Croissant 1.0 dataset description for the SpectraCQ
  competency-benchmark dataset, enabling discovery in dataset registries
  (Hugging Face, Zenodo, Google Dataset Search).
- **License**: two-tier — SPECTRA-authored components under CC-BY 4.0;
  bundled per-WG body-text KGs are 3GPP-derived literals retained with
  3GPP attribution under applicable ETSI/3GPP terms (see `LICENSE`).

### Not bundled

- **Raw Neo4j instance dumps** (`.dump`): exceed the Zenodo size cap;
  regenerable from `kg/per_wg/` plus `pipeline/`.
- **VectorDB embeddings** (used internally for retrieval-augmented CQ
  answering): planned for a subsequent minor release; regenerable
  deterministically from the bundled body-text KGs and a documented
  embedding configuration.

### Conventions

- Version numbers in this changelog refer to the release package
  (`release_package/`); SpectraCQ has its own version number tracked in
  `cqs/spectra_cq_v1.0/citation.bib`.
- Authoritative version of the ontology is in the file header of
  `ontology/spectra.ttl` (the `owl:versionInfo` triple).
