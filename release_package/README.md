# SPECTRA: process knowledge graph and executable benchmark

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

## Start with the current release

SPECTRA releases a shared process graph and source-linked benchmark for tracing
3GPP submissions, recorded outcomes, CRs and specification targets. The dataset
contains **966,859 nodes, 4,908,850 relationships and 12,931,842 RDF triples**.
The original **624-question collection** is preserved alongside the current
**560-question Core register: 522 verified contracts, 21 clarification diagnostics
and 17 frozen-input-dependent source-role diagnostics**. Every Core identity has
a completed disposition.

| Goal | Entry point |
| --- | --- |
| Select current executable tasks | [Current Core index](cqs/current_core/README.md), organized into record/decision retrieval, process aggregation and decision/study tracing |
| Inspect measured results | [N=12 process questions](cqs/original_core_overnight_evaluation15/README.md) and [N=3 named records](cqs/original_core_overnight_evaluation24/README.md), each with its own inputs, first responses and denominator |
| Verify current evidence | [Artifact walkthrough](ARTIFACT.md), [current saved-evidence launcher](cqs/verify_current_release.py) and [all-560 register](cqs/core_disposition_audit/README.md) |
| Obtain or rebuild graph data | [Body-graph inventory](kg/per_wg/README.md), [construction pipeline](pipeline/README.md) and [tests](tests/README.md) |

Run from the repository root:

```bash
pip install rdflib pyshacl
python3 -B release_package/tests/verify_benchmark.py --quick --out /tmp/spectra-quick-check
python3 -B -I release_package/cqs/verify_current_release.py
```

The first command checks Git-distributed files and schema artifacts. The current
launcher verifies the contract index, complete disposition register and saved
evaluations 23–51 without model or database calls. Individual cohort READMEs
provide exact score-replay commands. Full graph reconstruction uses the archived
body graphs and a scratch database; fresh passage ranking uses its original
full-text corpus. Current Git contracts and evidence have their own commit
references alongside the frozen version 2.0.0 graph deposit.

## Two-channel distribution

To accommodate GitHub's 100 MB-per-file limit, this release is split:

- **GitHub repository (this repo)** — ontology, SHACL, SpectraCQ v2.0 (624-CQ scored benchmark), schema-instantiation process-KG TTLs (`examples/process_kg/`, ~89 MB, each file under the 100 MB limit), validation JSONs, scripts, supplement, parsing pipeline.
- **Zenodo deposit** — large files: per-WG body-text Knowledge Graphs (`RAN{1..5}-body.ttl`, ~903 MB total). See `kg/per_wg/README.md` for the inventory and the DOI link.

A machine-readable DCAT/VoID description of every dataset in both
channels (triple counts, class partitions, distributions, licenses)
is provided in [`metadata/dcat_void.ttl`](https://github.com/spectra-ontology/spec-trace/blob/main/release_package/metadata/dcat_void.ttl).

This follows the academic two-tier distribution pattern of TSpec-LLM and GSMA telecom-kg-rel19. The `verify_release.py` test accepts either layout (Git checkout: body files absent by design; Zenodo download: body files present).

## What this package releases

This package accompanies *"SPECTRA: A Knowledge Graph Dataset and Benchmark for Tracing the 3GPP Standardization Process"* (currently under review). Every headline count in this README (nodes, relationships, triples, CQ counts) is governed by `MANIFEST.md`, the canonical counts manifest; `MANIFEST.md` is authoritative for those snapshot totals; the [current index](cqs/current_core/README.md) and [disposition summary](cqs/core_disposition_audit/partition/summary.json) select the current contract and classification counts.

<details>
<summary>Complete package inventory</summary>

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
│   ├── current_core/                 # current 522 typed contracts, pinned evidence and complete cohort catalogue
│   ├── core_disposition_audit/       # all 560 original IDs: 522 / 21 / 17 / 0 completed dispositions
│   ├── original_core_overnight_repairs*/    # immutable contract/source evidence cohorts
│   ├── original_core_overnight_evaluation*/ # saved first responses and complete-record score replay
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
│       ├── gold/                      # stored query-derived answer sets (RAN{1..5}_gold.json, 654 authored + _gold_summary.json)
│       ├── splits/                    # four canonical splits and annotation-derived evaluation subsets, with historical compatibility filenames (Git tree only):
│       │                              # annotation-derived 208 and 133 (historical compatibility default), superseded 241 and 149
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
│   ├── source_fidelity_quarantine.json # 334 held entries over 332 distinct records
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

</details>

## Reconstruction inputs and build provenance

The release includes the deterministic parser logic, graph serializations and
benchmark references needed for the documented reconstruction paths. Supporting
build and deployment records have the following scopes:

- Internal cumulative-regression logs and per-phase intermediate KG snapshots
  preserve development history. The public original benchmark contains 624
  released questions from 654 authored questions, with 30 held out, English
  questions, executable Cypher and stored query-derived answers.
- Neo4j instance dumps (`.dump`) and VectorDB embeddings are reconstruction
  outputs from the released per-WG body-text KGs and parsing pipeline; dump
  sizes exceed the archival package budget. Original TDocs remain accessible
  through the [3GPP portal](https://www.3gpp.org).
- Company-specific deployment glue covers monitoring, authentication and
  Slack/incident hooks. The reusable deterministic parser logic is released
  in [pipeline/](pipeline/README.md).

## Source annotations and versioned validation

- **Contact identity annotations.** The frozen body graphs contain 4,935
  Contact nodes representing 4,301 distinct contacts. A float-rendered identifier
  creates 634 duplicate nodes: RAN3 181, RAN4 291 and RAN5 162; RAN1/RAN2 zero.
  These account for 0.066% of the node total. Two Contact-count items use the
  recorded node count. [The inventory](kg/per_wg/README.md) gives the breakdown.
- **Graph 2.0.0 and source-fidelity inventory.** The audit inventories 2,637
  conversion-fidelity rows and 334 held entries over 332 distinct records. The deposited graph preserves
  its pre-repair values, and its gold uses that fixed snapshot. The released
  repair lists therefore leave the deposited gold unchanged. [The source note](validation/source_fidelity_note.md)
  describes application, affected fields and benchmark reach.
- **Released/deployed count provenance.** RAN3 has 1,249 recorded CRs targeting
  TS38.300 in the released graph (1,144 draftCR and 105 pCR), compared with 270
  in the earlier deployed snapshot. The other 17 of 18 cross-WG counts agree.
  [reproduce_scenario_counts.py](tests/reproduce_scenario_counts.py) recounts the
  released graph against [its recorded counts](validation/released_graph_scenario_counts.json).

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

## Ontology and graph examples

Commands in this section run from `release_package/`. Current benchmark and
saved-score commands above run from the repository root.



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

The bundled SPARQL queries run locally using any of these options:

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
the same; the remaining snapshot-specific count is documented under Source annotations and versioned validation.

## Evidence catalogue and historical evaluation scopes

For current typed contracts, use the [current Core index](cqs/current_core/README.md).
Its [complete cohort catalogue](cqs/current_core/README.md#evidence-catalogue)
retains every linked contract/evaluation bundle. The following earlier experiments
retain their own original questions or formal variants, scorers and denominators.

### Complete-record formal variants

The [contract companion](cqs/contract_repair_v1/README.md) evaluates 36 formally
defined task variants from 40 IDs fixed before generation. Requested named fields,
types, roles and collection rules determine complete-record F1 and exact output;
partial field credit is secondary. The remaining four retain their original
dispositions: three references exceeded the row cap and one definition required
further specification. The package supplies saved contexts, usage and graph-relative
gold from deposited-TTL restorations for single-pass text, two-round text and
generated Cypher. Its scope is this fixed variant cohort.

Run from the repository root with a new output filename:

```bash
python3 -B release_package/cqs/contract_repair_v1/matched_retrieval_measurement/matched_analysis.py \
  --require-complete --out /tmp/spectra-strict-record-replay.json
```

The replay uses saved outputs and contexts without model or database calls;
new output filenames preserve each report.

### Original-question retained-output diagnostic

The [31-item source-aligned diagnostic](cqs/contract_repair_v1/original_source_aligned/README.md)
re-scores 27 unchanged runs of nine models. Admission was fixed before reading
predictions: both source-evidenced AI audits must judge the full original scoring
contract aligned, native reference execution must be complete, and released/V1
answer-column sets must agree with source outputs. The fixed composition is 11
lookup, 13 aggregation and 7 relational items, with multihop n=0. Saved query
LIMITs and source availability define the operative scope. The legacy
canonical-string value-set scorer evaluates the primary answer column; named
records, role distinctions, types, order and multiplicity belong to the later
typed contracts. V1 is primary; V2 sensitivity uses the identical whole cohort.
This diagnostic retains its own denominator alongside the historical Core/V2
analysis and 36-variant complete-record measurement.

Run from the repository root; this command uses saved artifacts without model,
database or retrieval calls and writes no report:

```bash
python3 -I -B release_package/cqs/contract_repair_v1/original_source_aligned/score_source_aligned_retained_portable_v1.py \
  --bundle release_package/cqs/contract_repair_v1/original_source_aligned \
  --public-root . \
  --expected-manifest-sha256 ef37ec7f075c7d51d87406d20e6c55f050213ef9942eab6cf53cb27277f29813
```

The [original all-560 audit dispositions](cqs/contract_repair_v1/source_alignment_audit_v1/semantic_alignment_audit_report_v1.json)
and [345-file manifest](cqs/contract_repair_v1/source_alignment_audit_v1/portable_export_manifest_v1.json)
preserve every original item and all 112 attempts. Receipt availability covers
480 items with both raters and 80 with one or both unavailable. Admission requires
alignment as well as usable receipts and uses the fixed rule without replacement
or performance-based selection. The fixed 31 retain three coarse-role-alias
differences and their diagnostics. Its fixed denominator, nonempty reference
answers and historical scorer define the measured task.

Both historical protocols retain complete graph access and bounded text passages
with their recorded source cutoffs; graph/text cutoff equivalence is unverified.
Fresh passage ranking uses the separate original full-text corpus. Their review
provenance records nonblind AI development judgments, human/domain-expert n=0.
The [offline audit verifier and resource appendix](cqs/contract_repair_v1/source_alignment_audit_resources_v1/README.md)
and [verifier script](cqs/contract_repair_v1/source_alignment_audit_resources_v1/verify_semantic_alignment_audit_export_v1.py)
explain public checks and retained private-capture hash commitments.

### Original collection and value-set analyses

The [original benchmark](cqs/spectra_cq_v2.0/README.md) retains 624 released
questions from 654 authored questions, Cypher references and stored primary-column
value sets. Its [self-replay evidence](validation/cq_replay/) checks those sets
against a scratch reload. Current question meaning and whole-record order are
checked through the separately versioned typed contracts. The original collection
has its own [citation record](cqs/spectra_cq_v2.0/citation.bib) and CC BY 4.0 license.

The [baseline documentation](../paper/baseline/README.md) preserves the nine-model
Core scores, 133-item historical compatibility default, 208 annotation subset,
later 67/45 AI diagnostics and retained all-Core SQL/Cypher comparison. These
remain value-set analyses with their recorded AI review provenance. The retained
SQL/Cypher interval includes zero; its interpretation is an end-to-end pipeline
comparison under the stated access conditions. Original questions and runs remain
unchanged. Cite the Git commit for these additions alongside the frozen archives.

### Separately declared source-input experiments

The [source supplement guide](cqs/source_supplements_README.md) connects changed-input
snapshots to their own source reconstruction and four-method measurements.

- The [TS38.133 ten-table additive patch](cqs/original_core_source_table_correction10/README.md)
  supplies source/native/SQL validation. Its 80 caption identities comprise 62
  actual Word tables and 18 authored Void captions; the frozen 70-record task is
  preserved. The [separate source10 first-trial evaluation](cqs/original_core_source_table_correction10_evaluation/README.md)
  retains actual responses, failures and offline replay: all four requested-record
  F1 values are 0 on this one-question snapshot.
- [Documentary approval and normative incorporation for 17 CRs](cqs/original_core_source_CR_incorporation17/README.md)
  supplies original sources and reconstruction checks. In its [separate source17
  evaluation](cqs/original_core_source_CR_incorporation17_evaluation/README.md),
  Text2SQL returns all three requested identities with F1=1; source-predicate
  fidelity is inspected separately because its query omits approval/incorporation.
- The own-report Meeting calendar60 snapshot supplies [source reconstruction](cqs/original_core_source_Meeting_calendar60)
  and [actual four-method results](cqs/original_core_source_Meeting_calendar60_evaluation).
  Complete-record F1 measures answer recovery; source-predicate validation uses
  the linked query and source evidence.

## Citation

If you reuse SPECTRA, please cite the accompanying paper (currently under review; BibTeX will be added once the venue assigns a citation key) and this software/data record via the metadata in `CITATION.cff` (machine-readable) or `codemeta.json`.

## Authors

- **Sihyeon Choi** — *Project Owner* — System LSI Business, Device Solutions Division, Samsung Electronics — shyun12.choi@samsung.com

## License

SPECTRA-authored components (the ontology, SHACL shapes, SpectraCQ, queries, synthetic/metadata-only examples, validation scripts, parsing pipeline source, and PyLODE documentation) are released under Creative Commons Attribution 4.0 (CC-BY 4.0). 3GPP-derived text literals included in the per-WG body-text KGs are retained with explicit 3GPP attribution under the applicable ETSI/3GPP terms and are not relicensed as original SPECTRA-authored content. See `LICENSE` for the full CC-BY 4.0 text.
