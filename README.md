# From Contribution to Clause: Source-Bound Traceability Records and a Chain-Question Benchmark for the 3GPP Standardization Process [Experiment, Analysis & Benchmark]

This package provides the query graph of five 3GPP Radio Access Network working groups in JSON-LD and SQLite, the vocabulary and constraints it instantiates, 667 admitted chain questions, stored model responses, scores, and executable build and checking tools. The graph connects contributions, target-specific dispositions, meetings, CR packs and clauses. Its measured footprint is in `sources/released_record_counts.json`.

The source documents are identified by archive path, SHA-256 and locator. The package distributes their structured projection; `restore/` retrieves the cited reports and rehydrates source passages locally. Original disposition statuses describe the source graph. Local rehydration supplies the quote fields used by evidence-shape validation.

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
| `diagnosis/` | 187 diagnosis files for the main and five-hop conditions. |
| `code/` | Measurement scripts and their repository dependencies, plus analysis scripts and results. `code_manifest.json` lists each shipped source and hash. |
| `receipts/` | Ten target-identity review receipts. |
| `sources/competency_queries/index.json` | 25 sanitized original graph execution receipts: 644 PASS and 10 NO_DATA, with source and projected-file hashes. |
| `sources/manifest.jsonl` | URLs and hashes for 280 cited reports and their conversions. |
| `sources/disposition_bindings.jsonl.gz` | 358,062 text-free quote-hash receipts, decision spans and source-field locators. |
| `restore/` | Source retrieval, passage rehydration, SHACL validation, clean benchmark rebuild/gate and stored-response rescoring. |
| `records_redactions.jsonl`, `results_redactions.jsonl`, `code_redactions.jsonl` | Changed-file provenance and original/released hashes. |
| `SHA256SUMS` | Package file hashes, excluding this hash list itself. |

## Preparation

Run commands from the package root with Python 3.11 or later. The builder, gate and scorer use the Python standard library. Source restoration uses `lxml` and LibreOffice for the reports marked for conversion; passage rehydration uses `lxml`, `python-docx` and `openpyxl`; shape validation uses `rdflib` and `pyshacl`. The current-table analysis uses `numpy`. Additional historical analysis scripts have the dependencies listed in `code_report.md`.

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
python3 restore/restore_sources.py --manifest sources/manifest.jsonl \
  --dest work/sources --work work/downloads --report work/source_restore.json

python3 restore/restore_bindings.py --release . --source-root work/sources \
  --limit 20 --out work/dispositions_100.jsonld --report work/bindings_100.json

python3 restore/validate_bindings.py --release . --records work/dispositions_100.jsonld \
  --report work/shacl_100.json
```

`--limit 20` checks the first 20 dispositions per WG. Removing it selects every disposition in the selected WGs; `--wg RAN1` selects a partition. Passage rehydration checks the source file SHA-256, restores accepted body blocks or the precise annex row with its governing text, and compares the recovered quote's exact SHA-256 and character count with its producer receipt before emitting it. The report separately counts agreement of the direct target-predicate reread. Target-identity reviews remain separate evidence.

The local preparation check rehydrated 100/100 passages, agreed with 100/100 direct rule readings, and conformed to all 44 released node shapes for this sample. The validator normalizes RDF 1.1 simple strings and explicit `xsd:string` literals to the same representation while retaining every shape constraint. This is a sample validation; the previously measured corpus-wide locator audit remains in `responses/final/next_cycle/analysis/locator_recompute.json`.

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

The namespace is `https://w3id.org/spectra#`. The first public ontology release is archived under DOI [10.5281/zenodo.20034872](https://doi.org/10.5281/zenodo.20034872). Package version 1.2.0 retains the preceding public creator, publisher, issue date, license and namespace metadata and supplies the current 37 named classes, 86 object properties, 112 datatype properties, 44 node shapes and 16 disposition codes. `docs/ontology_build.json` records the source snapshots and their hashes. This resource package is available on the repository’s `vldb-2027` branch.

The package uses CC BY 4.0 (`LICENSE`). Cite the authors and manuscript listed in `CITATION.cff`. Restored 3GPP source documents and locally rehydrated passages retain the terms of 3GPP and its Organizational Partners. Earlier archived releases remain associated with the concept DOI [10.5281/zenodo.20034871](https://doi.org/10.5281/zenodo.20034871); this preparation creates no new DOI.
