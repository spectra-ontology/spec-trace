# Changelog

All notable changes to the SPECTRA release package are documented in this file.
Version numbers follow [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html).

## [1.0.1] — 2026-06-12

Resource-package improvements responding to the ISWC 2026 reviews. The
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

First public release accompanying the ISWC 2026 Resources Track submission
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
