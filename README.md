# SPECTRA: An Ontology and Benchmark for 3GPP Traceability [Experiment, Analysis & Benchmark]

This package provides the query graph of five 3GPP Radio Access Network working groups in JSON-LD and SQLite, the vocabulary and constraints it instantiates, 667 admitted chain questions, stored model responses, scores, and executable build and checking tools. The graph connects contributions, target-specific dispositions, meetings, CR packs and clauses. Its measured footprint is in `sources/released_record_counts.json`.

The source documents are identified by archive path, SHA-256 and locator. The package distributes their structured projection; `restore/` retrieves the cited reports and rehydrates source passages locally. Original disposition statuses describe the source graph. Local rehydration supplies the quote fields used by evidence-shape validation.

## Start with the published results

Use Python 3.11 or later.

```sh
git clone --branch vldb-2027 --single-branch https://github.com/spectra-ontology/spec-trace.git
cd spec-trace
python3 -m venv .venv
. .venv/bin/activate
.venv/bin/python -m pip install -r requirements-replay.txt
.venv/bin/python restore/reproduce.py --out work/replay
```

The last command works offline after dependency installation. It verifies every package checksum, replays the 60 historical score entries, and reproduces all 37 current conditions with their template/session bootstraps. It uses the shipped responses and compressed databases. Successful execution writes `work/replay/report.json` and a current-table report with `matches_expected_output: true`. Model generation, source downloads and database services are separate from this replay.

[Reproducing the paper](REPRODUCING.md) maps the evidence to commands and expected outputs. [Experimental interfaces and inputs](EXPERIMENTS.md) lists each condition's corpus, attached fields, tool budget and reproduction status. [Benchmark families and requested fields](BENCHMARK.md) gives the computed main and extension inventory. [The datasheet](datasheet.md) describes the population, question construction and distribution terms. The [vocabulary](docs/spectra.ttl) and [shapes](docs/spectra-shapes.ttl) define the records used by the benchmark.

## Follow-up studies

Each study preserves its own inputs, complete outputs and execution receipts. Choose a study for the comparison you want to reproduce.

| Study | Reuse | Recorded result |
|---|---|---|
| [Operator pilot](studies/operator_pilot/README.md) | Six analytical operations across five WGs | One schema-and-domain first submission answers 30/30 authored items. |
| [Scope-value replay](studies/scope_intervention/README.md) | A one-literal intervention on fixed saved queries | All 298 preclassified scope failures recover their gold sets. |
| [Semantic witnesses](studies/semantic_witnesses/README.md) and [anchor comparison](studies/witness_selection_value/README.md) | Data that distinguish grouping, set, tie and composition errors | In the same 66 available cells, witness selection detects 162/200 fixed controls versus 93/200 under the hash baseline. |
| [Matched domains](studies/matched_domains/README.md) | SQL/Cypher first submissions on the same 50 fixed representatives | Two sessions per language each return 50/50; the archived configuration retains unknown provider-model identity. |
| [Engineer questions](studies/practitioner_questions/README.md) | 33 de-identified question units and a documentary subquery in an actual request | Two SQL formulations reproduce the same 28 rows; question interpretation remains a separate step. |

## Contents

| Path | Content |
|---|---|
| `records/` | 48 JSON-LD files, partitioned by phase and WG; eight large files use gzip. RAN5 pack/clause records are in `records/RAN5_graph_export/RAN5/`. |
| `sqlite/` | Five query databases, each with 11 tables; four use gzip. `SHA256SUMS.txt` covers the database bytes before and after compression. |
| `ontology/` | The internal 7.3.0 vocabulary and SHACL snapshots used during construction. |
| `docs/` | The package vocabulary 1.2.0, 44 companion SHACL shapes, documentation and build provenance. Current term sets match the internal snapshot. |
| `benchmark/` | 670 drawn main items, their 667 admitted items and gate reports; fixed anchors; 300 drawn five-hop items and 297 admitted items. |
| `abstention/` | 160 abstention items, checks, packets, stored responses and scores, in 133 files. |
| `responses/` | 3,052 stored response, query, score and analysis files. |
| `diagnosis/` | Per-item diagnoses for the main and five-hop conditions, with source-locator follow-up evidence. |
| `code/` | Measurement scripts and their repository dependencies, plus analysis scripts and results. `code_manifest.json` lists each shipped source and hash. |
| `receipts/` | Ten target-identity review receipts. |
| `sources/competency_queries/index.json` | 25 sanitized original graph execution receipts: 644 PASS and 10 NO_DATA, with source and projected-file hashes. |
| `sources/manifest.jsonl` | URLs and hashes for 280 cited reports and their conversions. |
| `sources/disposition_bindings.jsonl.gz` | 358,062 text-free quote-hash receipts, decision spans and source-field locators. |
| `restore/source_links/` | Official archive/member manifests, native and reconstructed CR-form checkers, and receipts for the 604 distinct CR–clause pairs in the main benchmark. |
| `restore/retrieval/` | Text-free frontiers, official source recipes and constructors for all five WG search indexes and the plenary index, with source-version and execution receipts. |
| `restore/lexical_containment/`, `restore/dense_retrieval/` | Portable deterministic-route replay and reconstruction of the recorded dense-reader requests. |
| `restore/census/`, `restore/census_native/` | Complete source inventories, metadata, original corpus auditors and an executed native-field preservation fallback. |
| `restore/census_reconstructed/` | Executed selected reconstruction checks, complete original audit comparisons, text-free expected digests and public-reference projection verification. |
| `studies/operator_pilot/`, `studies/scope_intervention/`, `studies/semantic_witnesses/` | Analytical operations, fixed-cohort scope intervention and complete semantic witness pools, with frozen inputs, complete outputs and portable replay. |
| `studies/matched_domains/`, `studies/practitioner_questions/` | Fixed-sample matched-value first submissions and de-identified real-question context, with separate protocols, data and portable verification. |
| `studies/interface_condition/`, `studies/correspondence_context/` | Archived input-condition audit and identity-free contextual correspondence analysis, each with its own stated scope. |
| `restore/` | Source retrieval, passage rehydration, SHACL validation, clean benchmark rebuild/gate and stored-response rescoring. |
| `records_redactions.jsonl`, `results_redactions.jsonl`, `code_redactions.jsonl` | Changed-file provenance and original/released hashes. |
| `SHA256SUMS` | Package file hashes, excluding this hash list itself. |

## Preparation

Run commands from the package root with Python 3.11 or later, with `. .venv/bin/activate` in each shell used below. `requirements-replay.txt` pins the tested table-replay dependency; `requirements-sources.txt` adds the tested source and shape-validation dependencies. The builder, gate and scorer use the Python standard library. Source restoration uses LibreOffice 7.3.7.2 for the reports marked for conversion; conversion hashes bind the tested output bytes. Additional historical analysis scripts have the dependencies listed in `code_report.md`.

```sh
sha256sum -c SHA256SUMS
mkdir -p work code/.git
```

The empty `code/.git` marker gives copied repository modules a root for their existing path discovery. It contains no repository history. To use all five SQLite databases, decompress the four compressed partitions and verify their bytes:

```sh
gzip -dk sqlite/RAN2.sqlite.gz sqlite/RAN3.sqlite.gz sqlite/RAN4.sqlite.gz sqlite/RAN5.sqlite.gz
(cd sqlite && sha256sum -c SHA256SUMS.txt)
```

## Restore sources and evidence

```sh
python3 -m pip install -r requirements-sources.txt
python3 restore/restore_sources.py --manifest sources/manifest.jsonl \
  --dest work/sources --work work/downloads --report work/source_restore.json

python3 restore/restore_bindings.py --release . --source-root work/sources \
  --limit 20 --out work/dispositions_100.jsonld --report work/bindings_100.json

python3 restore/validate_bindings.py --release . --records work/dispositions_100.jsonld \
  --report work/shacl_100.json
```

`--limit 20` checks the first 20 dispositions per WG. Removing it selects every disposition in the selected WGs; `--wg RAN1` selects a partition. Passage rehydration checks the source file SHA-256, restores accepted body blocks or the precise annex row with its governing text, and compares the recovered quote's exact SHA-256 and character count with its producer receipt before emitting it. The report separately counts agreement of the direct target-predicate reread. Target-identity reviews remain separate evidence.

The local preparation check rehydrated 100/100 passages, agreed with 100/100 direct rule readings, and conformed to all 44 released node shapes for this sample. The validator normalizes RDF 1.1 simple strings and explicit `xsd:string` literals to the same representation while retaining every shape constraint. This is a sample validation; the previously measured corpus-wide locator audit remains in `responses/final/next_cycle/analysis/locator_recompute.json`.

The [source-locator follow-up](diagnosis/source_locator/README.md) additionally rehydrates the complete 368-record saved `source_verified` exception class from 79 reports, checks its exact source/quote hashes and validates the restored records with the released shapes. It explains the original rich-rendering mismatches through accepted-prose rendering, with the original locator-census outputs preserved. Its 11-disposition intersection with seven main items has separate target/code/scope receipts.

## Check CR form links

The [CR source check](restore/source_links/README.md) connects the main benchmark's 604 distinct CR–clause pairs to pinned official archive members. It runs with the Python standard library and the released independent reader:

```sh
python3 restore/source_links/check_source_links.py --release . \
  --manifest restore/source_links/benchmark_clause_manifest.json \
  --work work/cr_sources --report work/cr_source_check.json
```

The original official-download execution fetched 251 archives and confirmed 549 pairs. A [reconstruction follow-up](restore/source_links/README.md#reconstruct-the-53-source-format-and-url-exceptions) restores the remaining 53 source-format/URL cases from 29 pinned official archives and confirms their complete scientific-reader fields against the historical forms and current gold. Together the checks confirm 602 of the 604 pairs. The two remaining forms enumerate tables within the named clauses and retain the reader's `table_or_figure_in_clause` classification. The original manifests and measurements are preserved.

The reconstruction command uses LibreOffice and a Python interpreter with PyUNO (commonly the operating system's `/usr/bin/python3`):

```sh
python3 restore/source_links/check_reconstructed_sources.py --release . \
  --manifest restore/source_links/reconstructed_source_manifest.json \
  --conversion-python /usr/bin/python3 --workers 2 \
  --work work/cr_reconstructed --report work/cr_reconstructed.json
```

Repeat either checker with `--offline` to verify cached bytes. The linked guide explains conversion provenance, reader equivalence and the separate whole-corpus audit paths.

## Reconstruct retrieval and audit inputs

[Retrieval restoration](restore/retrieval/README.md) supplies the five WG and plenary frontiers, official source recipes, native parsing commands and FTS construction. [Lexical containment](restore/lexical_containment/README.md) reproduces twelve deterministic routes for all 667 admitted questions. [Dense-reader input replay](restore/dense_retrieval/README.md) reconstructs the 1,334 recorded local-reader requests and documents its separate fresh-query pilot. [The census adapter](restore/census/README.md) provides the original pack and clause auditors with pinned metadata and complete source inventories. Each workflow records its actual source, parsing and execution coverage.

## Test stored SQL with synthetic counterexamples

The [relational contract check](restore/semantic_stress/README.md) runs a fast
offline pilot and supplies the full fixed-design measurement. It adds marked
synthetic rows to disposable memory copies and preserves the released gold,
records and responses. Its separate runtime requires SQLite 3.37.2; check the
linked instructions before running it. This complements stored-score replay
with explicit tests of snapshot-correct queries under changed scope values.

## Rebuild and gate the benchmark

After source restoration, the following command creates a clean workspace, stages only released records, rebuilds each WG sequentially from its fixed anchors, runs the independent SQL gate and compares drawn and admitted files byte for byte with their stored counterparts:

```sh
python3 restore/check_benchmark.py --release . --source-root work/sources \
  --work work/benchmark_check --report work/benchmark_check.json
```

Use an empty `--work` directory. The five-hop families use the same builder with `--families clause_neighbours first_change previous_pack` and the stored five-hop anchor sets. The lower-level scripts are under `code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/`; `restore/rebuild_items.sh` exposes the main builder check for selected WGs.

Local preparation rebuilt all 670 drawn items and independently admitted the same 667 items, byte for byte, across all five WGs. `sources/package_checks.json` records this check.

The JSON-LD records and the five SQLite databases represent the same query graph. `sources/released_record_counts.json` reports table counts by WG; the forward CR links and reverse pack/clause links support independent gold derivation. These counts describe this released query projection; the wider SPECTRA process graph is a separate resource.

## Rescore stored responses

```sh
python3 restore/rescore_stored.py --release . --out work/rescored.json
```

This command replays all 60 historical stored-score entries with the released scorer and 667 admitted items. Local preparation reproduced 60/60 entries in every field except the response path. The broader historical score-report check and its per-entry coverage are recorded in `datasheet.md`; the package preserves the original response and score bytes.

## Reproduce the current result tables

```sh
mkdir -p code/.git
python3 restore/reproduce_current_tables.py --release . \
  --out work/m2_template_session.json --report work/m2_reproduction.json \
  --expected sources/current_tables_reference.json
```

This offline command reconstructs all 37 current analysis conditions on the 667 admitted questions. It runs the packaged scoring and template/session analysis unchanged, including both scoring rules and 10,000-draw cluster and session bootstraps. A temporary filesystem adapter maps released responses, packets and databases into the expected input layout. The output matches the reference SHA-256 byte for byte; the report records condition totals and the original analysis-source hashes. These current-table conditions and the 60 historical score entries above are separate replay targets.

## Provenance paths

Stored results retain their original repository paths under `logs/publication/paper/ongoing/sigir-2027-research/`; executable commands use the current VLDB directory. For the historical log prefix, `chain_eval/` and `final/` map to `responses/`, `integration/items_final/` to `benchmark/items_final/`, `abstention3/` to `abstention/`, and the fixed anchor directories to the matching directories under `benchmark/`. `RAN5_graph_export/` maps to `records/RAN5_graph_export/`.

Text copied from source documents and personal/company attributions are represented in stored results by hash-and-length withholding markers. The root-level redaction lists preserve the original and released file hashes. `datasheet.md` gives the field-level distribution policy and audit scope.

## Ontology and license

The packaged vocabulary and stored outcomes can be recounted with `python3 restore/recount_resources.py --release . --out work/resource_counts.json`.

The original loaded-graph competency-query receipts are indexed in [sources/competency_queries/index.json](sources/competency_queries/index.json). They retain identifiers, outcomes, counts, guard checks and project-authored queries, with original-file and projected-file hashes. Their scope is the original loaded process graph; these stored outcomes are separate from the fresh benchmark gate over the released query projection. Raw answer samples and source-text fields stay in the original receipts.

The namespace is `https://w3id.org/spectra#`. The first release links its ontology and shapes in the companion GitHub repository; DOI [10.5281/zenodo.20034872](https://doi.org/10.5281/zenodo.20034872) archives its five WG body graphs. Package version 1.2.0 on the `vldb-2027` branch supplies the current ontology, shapes and benchmark artifacts. It retains the preceding public creator, publisher, issue date, license and namespace metadata and supplies the current 37 named classes, 86 object properties, 112 datatype properties, 44 node shapes and 16 disposition codes. `docs/ontology_build.json` records the source snapshots and their hashes. This resource package is available on the repository’s `vldb-2027` branch.

The package uses CC BY 4.0 (`LICENSE`). Cite the authors and manuscript listed in `CITATION.cff`. Restored 3GPP source documents and locally rehydrated passages retain the terms of 3GPP and its Organizational Partners. Earlier archived releases remain associated with the concept DOI [10.5281/zenodo.20034871](https://doi.org/10.5281/zenodo.20034871); this preparation creates no new DOI.
