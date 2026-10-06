# SPECTRA — A Traceability Ontology for 3GPP RAN Standardization

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Ontology: OWL 2](https://img.shields.io/badge/Ontology-OWL_2-blue.svg)](https://www.w3.org/TR/owl2-overview/)
[![Persistent IRI](https://img.shields.io/badge/IRI-w3id.org%2Fspectra-success.svg)](https://w3id.org/spectra)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20034871.svg)](https://doi.org/10.5281/zenodo.20034871)

**License**: CC-BY 4.0 (SPECTRA-authored components); 3GPP-derived literal content carries explicit 3GPP attribution (see `LICENSE` Tier 2)
**Release package version**: v2.0.0 (see `CHANGELOG.md`)
**Ontology version**: v1.1.1 (six entity-layer classes plus LOV-conformant vocabulary metadata; see `ontology/spectra.ttl` header for authoritative version)
**Persistent identifier**: [`https://w3id.org/spectra`](https://w3id.org/spectra) (registered via [`perma-id/w3id.org`](https://github.com/perma-id/w3id.org))
**Zenodo DOI**: [`10.5281/zenodo.20034871`](https://doi.org/10.5281/zenodo.20034871) (concept DOI — locates the newest deposited version; each deposit's version DOI pins its archival bytes. Git-only additions also require a commit reference.)
**Repository**: https://github.com/spectra-ontology/spec-trace

## Two-channel distribution

To accommodate GitHub's 100 MB-per-file limit, this release is split:

- **GitHub repository (this repo)** — ontology, SHACL, SpectraCQ v2.0 (624-CQ scored benchmark), schema-instantiation process-KG TTLs (`examples/process_kg/`, ~89 MB, each file under the 100 MB limit), validation JSONs, scripts, supplement, parsing pipeline. Git-channel total ~94 MB.
- **Zenodo deposit** — large files: per-WG body-text Knowledge Graphs (`RAN{1..5}-body.ttl`, ~903 MB total). See `kg/per_wg/README.md` for the inventory and the DOI link.

A machine-readable DCAT/VoID description of every dataset in both
channels (triple counts, class partitions, distributions, licenses)
is provided in [`metadata/dcat_void.ttl`](https://github.com/spectra-ontology/spec-trace/blob/main/release_package/metadata/dcat_void.ttl).

This follows the academic two-tier distribution pattern of TSpec-LLM and GSMA telecom-kg-rel19. The `verify_release.py` test accepts either layout (Git checkout: body files absent by design; Zenodo download: body files present).

## What this package releases

This is the **publicly released** component of the SPECTRA ontology resource described in the accompanying paper *"SPECTRA: A Traceability Ontology for 3GPP Standardization"* (currently under review). Every headline count in this README (nodes, relationships, triples, CQ counts) is governed by `MANIFEST.md`, the canonical counts manifest; when a document disagrees with `MANIFEST.md`, the manifest is authoritative.

```
release_package/
├── README.md                          # this file
├── ontology/
│   └── spectra.ttl                    # SPECTRA OWL 2 ontology (Turtle, 914 triples incl. PROV-O alignment)
├── docs/
│   └── spectra.html                   # PyLODE-generated HTML documentation
├── shapes/
│   └── spectra-core.shacl.ttl         # SHACL shapes (8 NodeShapes, core cardinality/range)
├── diagrams/
│   ├── schema_overview.md             # high-level schema summary
│   └── cq_distribution.png            # category-by-phase distribution of the 624 released CQs
├── cqs/
│   ├── cq_index.md                    # index of all 624 released CQs (verbatim 3GPP company names where present)
│   │                                  # (id, WG, phase, category, schema area)
│   ├── representative_cqs.md          # 14 representative CQs with full text + Cypher
│   └── spectra_cq_v2.0/               # ★ SpectraCQ v2.0 — 624-CQ scored benchmark (654 authored / 30 held out)
│       ├── README.md                  # benchmark description + how to use
│       ├── LICENSE                    # CC-BY 4.0
│       ├── CITATION.cff               # citation metadata (machine-readable)
│       ├── citation.bib               # BibTeX for citing SpectraCQ
│       ├── croissant.json             # Croissant ML dataset metadata
│       ├── questions.json             # 624 CQ × {id, wg, phase, category, question_en, schema_area, cypher_file, gold_file, gold}
│       ├── benchmark.jsonl            # 624 scored rows (one JSON object per line: question + gold answer set + row count)
│       ├── answer_contract.jsonl      # answer contract of the 560 SpectraCQ-Core items (Git tree only)
│       ├── core_answer_gold.jsonl     # Core scoring key: answer column + gold value set per item (Git tree only)
│       ├── contract_demand_provenance.jsonl # column-demand verdicts behind the answer contract, each with what decided it (Git tree only)
│       ├── cypher/                    # 624 executable Cypher reference queries (one per released CQ)
│       ├── sparql/                    # 142 SPARQL translations (all released RAN1 CQs; see MANIFEST.md §2.1)
│       ├── gold/                      # deterministic gold answer sets (RAN{1..5}_gold.json, 654 authored + _gold_summary.json)
│       ├── splits/                    # four canonical splits and contract-exact subsets of Core, with the scripts that rebuild them (Git tree only):
│       │                              # annotation-derived 208 and 133 (Core scorer default), superseded 241 and 149
│       └── held/                      # 30 held-out CQs (degenerate/empty gold; excluded from scoring)
│                                      # contract_held_out.json: 64 released CQs outside Core, with reasons (Git tree only)
├── queries/
│   ├── cypher/                        # 15 Cypher translations (incl. MULTI_HOP_traceability)
│   └── sparql/                        # 6 representative SPARQL examples (full set: cqs/spectra_cq_v2.0/sparql/)
├── examples/
│   ├── instantiation_snippet.ttl      # small synthetic instantiation
│   ├── end_to_end/                    # full E2E synthetic example (data + queries + expected)
│   │   ├── README.md
│   │   ├── data.ttl                   # synthetic 4-hop scenario (Turtle)
│   │   ├── data.cypher                # same data as Neo4j Cypher CREATE
│   │   ├── query.sparql               # multi-hop traceability query (SPARQL)
│   │   ├── query.cypher               # same query in Cypher
│   │   └── expected_output.txt        # expected result row(s)
│   ├── real_world_mini/               # ★ metadata-only mini sample (1 RAN1 meeting structure)
│   │   ├── README.md                  # explains: metadata only, no copyrighted body content
│   │   ├── data.ttl                   # 8 TDocs + 2 Resolutions + 1 TS + 1 Section
│   │   ├── queries/                   # Q1 traceability + Q2 cross-WG LS (SPARQL)
│   │   └── expected_outputs/          # verified expected query rows
│   └── process_kg/                    # ★ cross-WG process KG (metadata-only, body stripped)
│       ├── README.md                  # describes scope and anonymization policy
│       ├── SCHEMA.md                  # field-level schema for the three TTL files
│       ├── ls_routing.ttl             # RAN1–RAN5 LS routing (~26.8K LSs, ~195K triples)
│       ├── cr_routing.ttl             # RAN1–RAN5 CR routing (~193K CRs, ~1.25M triples)
│       ├── ran1_tdoc_metadata.ttl     # full RAN1 TDoc structural metadata (~124K TDocs, ~991K triples)
│       └── _export_summary.txt        # entity counts per file
├── kg/                                 # ★ per-WG knowledge graph deposits (paper §6.4, §7)
│   ├── per_wg/                        # body-text TTLs (RAN{1..5}-body.ttl, ~903 MB) — Zenodo deposit only
│   │   └── README.md                  # explains where to download + IRI scheme
│   └── per_wg_schema/                 # schema-instantiation TTLs (RAN{1..5}-schema.ttl, ~14 KB each)
│       ├── README.md                  # cross-WG schema-fit verification recipe
│       └── RAN1-schema.ttl ... RAN5-schema.ttl
├── pipeline/                           # ★ sanitized parsing pipeline (5 stages)
│   ├── 01_extract/   02_metadata_parse/   03_document_parse/
│   ├── 04_shacl_validate/             05_neo4j_load/
│   └── README.md
├── supplement/                         # ★ paper companion (trimmed from main PDF for page limit)
│   ├── README.md                      # what is here and why
│   ├── PAPER_APPENDIX.tex             # original Appendix A-G (TTL/SHACL/SPARQL excerpts, etc.)
│   └── LLM_EVAL_PILOT.tex             # single-evaluator LLM-baseline pilot (was §6.6 in body draft)
├── validation/                         # ★ JSON evidence for paper's quantitative claims (15 JSONs)
│   ├── validation_manifest.md         # paper claim → JSON file mapping
│   ├── structural_metrics.json        # class/property/axiom counts
│   ├── oops_summary.json              # OOPS! pitfall scanner result
│   ├── cq_coverage.json               # design-phase RAN1 137-CQ × ontology coverage matrix
│   ├── cypher_to_sparql_portability.json # 137/137 SPARQL-translatable classification (design-phase RAN1 layer)
│   ├── cross_wg_schema_diff.json      # RAN1 vs RAN2-5 schema diff
│   ├── cross_wg_use_evidence.json     # cross-WG query counts on deployed KGs
│   ├── per_wg_class_coverage.json     # per-WG class instantiation coverage
│   ├── ran1_instance_counts.json      # RAN1 KG per-class counts + integrity stats
│   ├── ran1_relation_integrity.json   # per-relation domain coverage + integrity %
│   ├── cq_results.json                # design-phase RAN1 137-CQ pass/fail evidence
│   ├── example_queries_results.json   # bundled example queries → verified result rows
│   ├── schema_growth_evidence.json    # schema growth evidence across WG onboarding
│   ├── chart_parser_fidelity_note.md  # chart-parser fidelity caveat
│   ├── source_fidelity_note.md        # source-fidelity repairs and quarantine: state, application, reach
│   ├── source_fidelity_repair_manifest.json # repair lists (not applied in the 2.0.0 graph)
│   ├── source_fidelity_quarantine.json # 334 held records
│   ├── released_graph_scenario_counts.json # cross-WG query counts recounted on the released graphs
│   └── cq_replay/                     # ★ 624-CQ benchmark reproducibility evidence (see MANIFEST.md §4)
│       ├── graph_counts.json          # per-WG loaded node/relationship counts (966,859 / 4,908,850)
│       ├── triple_counts.json         # per-WG RDF triple counts (12,931,842)
│       ├── ran{1..5}_load_report.json # scratch-reload reports (shipped loader on shipped TTLs)
│       ├── ran{1..5}_replay_results.json # 624/624 self-replay evidence (per-CQ gold match)
│       └── sparql_parity_results.json # 142/142 SPARQL/Cypher row-count parity (released RAN1 CQs)
├── tests/                              # ★ reproducibility scripts (rdflib + pyshacl)
│   ├── README.md
│   ├── reproduce_scenario_counts.py    # recount the cross-WG query counts on the released graphs
│   ├── reproduce_structural_metrics.py # recompute Table 4 numbers from spectra.ttl
│   ├── test_e2e_sparql.py              # run multi-hop traceability against synthetic data
│   ├── verify_benchmark.py             # one-command gate over the whole release
│   └── verify_release.py               # deterministic per-claim verifier
├── metadata/
│   └── dcat_void.ttl                  # DCAT/VoID machine-readable description of both channels
├── w3id/
│   ├── htaccess                       # to be submitted to perma-id/w3id.org
│   └── PR_DESCRIPTION.md              # PR text for w3id registration
├── ARTIFACT.md                         # full artifact narrative (Tier 1 / Tier 2 boundary)
├── MANIFEST.md                         # canonical counts manifest (single source of truth for headline numbers)
├── CITATION.cff                       # citation metadata (machine-readable)
├── CONTRIBUTING.md                    # contribution guide
├── CHANGELOG.md                       # release history
├── RELEASE_PROCESS.md                 # release process record (v1.0.0 completed)
├── TUTORIAL.md                        # short walkthrough for new users
├── codemeta.json                      # software/data metadata
└── LICENSE                            # CC-BY 4.0 (Tier 1) + 3GPP attribution (Tier 2)
```

## What is *not* in this package

The following artifacts are part of the paper's **internal validation evidence** and are *not* redistributed:

- Internal cumulative-regression run logs and per-phase intermediate KG snapshots used during the five-phase development. The scored benchmark (624 released CQs of 654 authored, 30 held out; English text + executable reference Cypher + deterministic gold answer sets) is publicly released at `cqs/spectra_cq_v2.0/`; only the regression run-history is retained internally.
- Neo4j instance dumps (`.dump`) and VectorDB embeddings: regenerable from the released per-WG body-text KGs (`kg/per_wg/`) and sanitized parsing pipeline (`pipeline/`); not bundled because raw dumps exceed the archival package's size budget. Original 3GPP TDocs remain publicly accessible via the 3GPP portal: https://www.3gpp.org
- Internal operational deployment glue: company-specific monitoring, authentication, and Slack/incident hooks around the parsing pipeline; the deterministic parser logic itself is released at `pipeline/`.

## Known data quality issues

- **Duplicated `Contact` nodes.** 634 of the 4,935 `Contact` nodes in the
  per-WG body-text KGs are duplicates of a contact already present (RAN3
  181, RAN4 291, RAN5 162; RAN1 and RAN2 zero), so the graphs hold 4,301
  distinct contacts. The cause is a float-rendered contact identifier
  producing a second IRI for the same contact. This inflates the node
  totals reported in `MANIFEST.md` §1 by 634 (0.066%) and makes the two
  benchmark items that count `Contact` nodes report the node count rather
  than the distinct-contact count. Full breakdown and effects:
  `kg/per_wg/README.md`.
- **Source-fidelity repairs not applied.** A content-fidelity audit flags
  2,637 rows that a correct conversion cannot produce. Its repair lists
  and its 334 held records ship in `validation/`, but the 2.0.0 graph
  carries the values before repair. Gold answers are defined on the graph
  as deposited, so the lists change no gold answer. How to apply them, what
  they change and which benchmark items they reach:
  `validation/source_fidelity_note.md`.
- **One cross-WG count differs on the released graphs.** RAN3 change
  requests on TS 38.300 number 270 on the deployed KG behind
  `validation/cross_wg_use_evidence.json` and 1,249 on the released RAN3
  graph (1,144 draftCR, 105 pCR); the other 17 counts of that file are the
  same. `tests/reproduce_scenario_counts.py` recounts all 18 into
  `validation/released_graph_scenario_counts.json`.

## Anonymization policy (asymmetric by design)

Different artifact tiers follow different policies, each driven by what 3GPP itself publishes:

| Artifact tier | Companies | Rationale |
|---|---|---|
| `examples/process_kg/` (LS/CR routing + RAN1 TDoc metadata) | **verbatim** | Redistributes metadata that is already public on every TDoc cover page and on 3GPP's per-meeting `TDOC_List.xlsx`; anonymization would discard recoverable information without adding privacy. |
| `cqs/spectra_cq_v2.0/` (NL questions, Cypher) | **verbatim** (real 3GPP company names from public `TDOC_List.xlsx`, where present in 49 of the 624 released reference queries) | The 49 CQs that name companies cite contributors who are already public on every TDoc cover sheet; anonymizing would damage CQ portability against the released KG. The other 575 reference queries name no specific company. |
| `examples/real_world_mini/`, `examples/end_to_end/` | **synthetic** | Templates for instantiation; no real-world data is implied. |
| Body content (CR/TR/TS text, `discussionText` *values*) | **verbatim under 3GPP attribution** | Sentence-level rendered text retained with explicit 3GPP attribution per the project's Terms-of-Use note, following the same redistribution framing as TSpec-LLM and GSMA telecom-kg-rel19. |

The `tests/verify_release.py` anonymization check (Section 7 of the script) targets the SpectraCQ files only, making this policy boundary a syntactic invariant.

## Ontology summary

- **32 classes** organized around: contributions (`Tdoc` and its subclasses `CR`, `LS`, `Summary`, `SessionNotes`), resolutions (`Resolution` → `Agreement`, `Conclusion`, `WorkingAssumption`), specifications (`Spec`, `Section`, `TSTable`, `TSFigure`, `TechnicalReport`, `TRImpact`), organizational entities (`Meeting`, `Company`, `Contact`, `WorkItem`, `AgendaItem`, `Release`, `WorkingGroup`), artefacts (`Figure`, `Table`, `Chart`, `CRPack`), and spec-body entities (`Feature`, `Procedure`, `RRCParameter`, `CapabilityItem`, `PerformanceRequirement`, `ConformanceTest`).
- **53 object properties** + **81 data properties** (134 total).
- Reuses **DCMI Terms** (`dcterms:title`, `dcterms:description`, `dcterms:creator`, `dcterms:publisher`, `dcterms:issued`, `dcterms:modified`, `dcterms:rights`, `dcterms:license`), **FOAF** (`foaf:Person`, `foaf:Organization`, `foaf:name`, `foaf:homepage`), and **VANN** (`vann:preferredNamespacePrefix`, `vann:preferredNamespaceUri`); the legacy DC Elements 1.1 (`dc:`) namespace is not used.
- Axiomatization: 20 `owl:FunctionalProperty`, 2 `owl:InverseFunctionalProperty`, 15 inverse property pairs, 6 `owl:IrreflexiveProperty`, 2 `owl:AsymmetricProperty`.

> **Entity-layer instances in the KG exports.** Beyond the 26 process-layer classes, the per-WG TTL exports carry instances of the six entity-layer classes — `Feature` (22 per WG), `Procedure` (RAN1 79 / RAN2 81 / RAN3 60), `RRCParameter` (RAN2 2,281 / RAN3 2,950), `CapabilityItem` (RAN2 86), `PerformanceRequirement` (RAN4 20,449), and `ConformanceTest` (RAN4 1,126 / RAN5 73,033). 28 of the 624 released CQs query these labels (the `P3-S8` group in `cqs/cq_index.md`). All six classes are declared in `ontology/spectra.ttl` (32 classes total). The auxiliary annotation properties the exports attach to these instances (`_definedInSection`, `_disjointWith`, `granularity`) remain undeclared annotation-layer terms; under OWL open-world semantics the exports remain valid RDF, and the export counts above match the deployed graphs exactly.

## Quick start

### Load with RDFLib (Python)
```python
import rdflib
g = rdflib.Graph()
g.parse("ontology/spectra.ttl", format="turtle")
print(f"Triples: {len(g)}")
```

### Open in Protégé
File → Open → select `ontology/spectra.ttl`.

### Validate an instance with SHACL (pySHACL)
```bash
pip install pyshacl
pyshacl -s shapes/spectra-core.shacl.ttl examples/instantiation_snippet.ttl
# Expected: "Conforms: True"
```

### Browse the HTML documentation
Open `docs/spectra.html` in any browser (PyLODE-generated; no server required).

### Run a representative Cypher query
See `queries/cypher/` for examples executable against any Neo4j instance conforming to the SPECTRA schema.

### Run a representative SPARQL query

No public SPARQL endpoint is operated. To run the bundled queries locally:

**Option 1 — RDFLib (single Python process, no server):**
```python
import rdflib
g = rdflib.Graph()
g.parse('ontology/spectra.ttl', format='turtle')
g.parse('examples/end_to_end/data.ttl', format='turtle')
q = open('examples/end_to_end/query.sparql').read()
for row in g.query(q): print(row)
```
Or use the bundled wrapper: `python3 tests/test_e2e_sparql.py` (asserts the expected R1-2599998 / RAN1#121 row).

**Option 2 — Apache Jena Fuseki (local server):**
```bash
fuseki-server --file=ontology/spectra.ttl --file=examples/end_to_end/data.ttl /spectra
# then in another terminal:
curl -G --data-urlencode "query=$(cat examples/end_to_end/query.sparql)" \
     http://localhost:3030/spectra/sparql
```

**Option 3 — load the larger metadata-only process KG (~2.44M triples)** for graph-analytics queries (e.g., LS routing, CR-pack analytics):
```bash
fuseki-server --file=ontology/spectra.ttl \
              --file=examples/process_kg/ls_routing.ttl \
              --file=examples/process_kg/cr_routing.ttl \
              --file=examples/process_kg/ran1_tdoc_metadata.ttl \
              /spectra-process
```

See `queries/sparql/` for additional example queries.

### Reproducibility tests (rdflib + pyshacl)
```bash
pip install rdflib pyshacl
python3 tests/reproduce_structural_metrics.py   # exit 0 on agreement with validation/structural_metrics.json
python3 tests/test_e2e_sparql.py                # exit 0 on returning the expected R1-2599998 / RAN1#121 row
python3 tests/verify_release.py                 # file-level release gate, no arguments, no database
```

### Release gate
`tests/verify_benchmark.py` is the one-command gate over the whole
release. `--quick` needs no database and runs 52 checks, of which 47
apply to a Git-only checkout (the other five need the body-text deposit).
`--full` reloads the released graphs into a scratch store and re-derives
all 624 published answer sets; it wipes the database it connects to, so
`--bolt` and `--password` have no defaults. See `tests/README.md`.

### Cross-WG query counts on the released graphs
`tests/reproduce_scenario_counts.py` recounts the 18 counts of
`validation/cross_wg_use_evidence.json` on the body-text graphs of the
deposit (standard library, no database) and compares the result with
`validation/released_graph_scenario_counts.json`. 17 of the 18 are
the same; the one that differs is listed under Known data quality issues.

### SpectraCQ scored benchmark
The scored benchmark — 624 released CQs (of 654 authored; 30 held out) with English question text, executable reference Cypher, and deterministic gold answer sets (`benchmark.jsonl`) — is at `cqs/spectra_cq_v2.0/`. It is independently citable via `cqs/spectra_cq_v2.0/citation.bib` and licensed CC-BY 4.0. Reproducibility evidence (624/624 self-replay on a scratch reload) lives under `validation/cq_replay/`; canonical counts are in `MANIFEST.md`.

Self-replay checks the reference queries' stored outputs. The Core answer-column
gold and the annotation-derived 133/208 subsets do not establish that every
question requirement is scored: counts, relationship roles and ranking can
remain ungraded. Their definitions and examples are in the benchmark README
and `splits/README.md`. The contract data, subset lists and later analysis
tools are Git additions outside the frozen Zenodo 2.0.0 archives; cite the
Git commit when using them. An individual Zenodo version DOI pins archival
bytes, while the concept DOI locates the newest deposit. The baseline README
states which recorded results can be recomputed and which historical inputs
or rebuilt outputs were not retained.
Its offline analysis artifact records 30 populations, their identifiers and
input/source hashes, with 10,000 paired seed-0 resamples; the baseline README
provides the reproduction commands and metric definitions.
An additional AI-assisted field-coverage diagnostic reviewed all 133
candidates and froze the 67-item intersection before re-scoring. Its protocol,
stored judgments, identifiers and offline scores are linked from the benchmark
and baseline READMEs. It is not expert validation or a replacement for Core
or the 133/208; the compatibility scorer default remains the annotation-derived
133. The selected cohort is mostly lookup/aggregation and has no declared
tuple/mapping items, limiting generalization to other answer types and tracks.
A subsequent review separately assessed required fields, scope/roles,
cardinality/truncation and ordering/duplicates for all 133 candidates. Two
fresh isolated AI reviews yielded a 45-item intersection, fixed before its
new scores. The designers had already seen the Core/133/208/67 metrics.
The stored protocol, judgments, source hashes, membership checker and offline
analysis are documented in the same READMEs; the earlier 67-item evidence is
preserved. The 45 have 14 lookup, 30 aggregation and 1 relational item,
with no multihop or declared tuple/mapping item. The original answer-type
labels are 40 scalar sets and 5 ranked top-k; set scoring still ignores order.
This remains a selected AI-assisted diagnostic, without human expert
validation or full semantic certification; it changes no question, key,
original output or scorer default.
Model ranks change more under full-record scoring; the baseline README
compares each metric's subset ranks with that same metric on Core.
The baseline bundle also records an all-Core560 retained SQL/Cypher comparison
with the same repaired answer-column key. The paired difference interval
includes zero; this adds a reproducible current comparison without recovering
the historical SQL cohort or establishing a causal graph-engine advantage.

## Citation

If you reuse SPECTRA, please cite the accompanying paper (currently under review; BibTeX will be added once the venue assigns a citation key) and this software/data record via the metadata in `CITATION.cff` (machine-readable) or `codemeta.json`.

## Authors

- **Sihyeon Choi** — *Project Owner* — System LSI Business, Device Solutions Division, Samsung Electronics — shyun12.choi@samsung.com

## License

SPECTRA-authored components (the ontology, SHACL shapes, SpectraCQ, queries, synthetic/metadata-only examples, validation scripts, parsing pipeline source, and PyLODE documentation) are released under Creative Commons Attribution 4.0 (CC-BY 4.0). 3GPP-derived text literals included in the per-WG body-text KGs are retained with explicit 3GPP attribution under the applicable ETSI/3GPP terms and are not relicensed as original SPECTRA-authored content. See `LICENSE` for the full CC-BY 4.0 text.
