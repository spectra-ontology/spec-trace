# Reproducing the paper

The release connects process records, generated questions and recorded experimental outcomes. Begin with the offline replay in the [README](README.md#start-with-the-published-results); then choose the source checks or benchmark construction relevant to your use.

| Evidence | Inputs and command | Expected output and interpretation |
|---|---|---|
| Current agent scores, family/session analysis and uncertainty | `restore/reproduce_current_tables.py`, released responses, 667 admitted items, `sources/current_tables_reference.json` | 37 conditions, both scoring rules and 10,000-draw bootstraps; complete output hash equals the published reference. |
| Historical main score entries | `restore/rescore_stored.py` | 60 entries equal their stored scores, with released response paths. These entries and the 37 current conditions are distinct replay targets. |
| Ontology and competency-query outcomes | `restore/recount_resources.py` | 37 classes, 86 object properties, 112 datatype properties, 44 node shapes; recounts 644 PASS and 10 NO_DATA from 25 original loaded-graph execution receipts. |
| Report access and passage reconstruction | `restore/restore_sources.py`, then `restore/restore_bindings.py` | Archive/member/converted-file hashes and quote digests are checked against the manifest and text-free receipts. `--limit 20` selects the first 20 records per WG. |
| Shape conformance after evidence restoration | `restore/validate_bindings.py` | Applies the released 44 node shapes to the selected restored records. The documented preparation check covers 100 records. |
| Question and gold construction | `restore/check_benchmark.py` after report restoration | Rebuilds the five WGs from fixed anchors, runs the independent SQLite gate and compares the 670 drawn and 667 admitted items byte for byte. |
| Benchmark CR–clause source links | `restore/source_links/check_source_links.py`; [instructions and scope](restore/source_links/README.md) | For 604 distinct pairs: 549 native-form confirmations, 2 table-identifier cases and 53 source-format/URL availability outcomes. Checks archive/member hashes and released item membership. |
| Stored-SQL synthetic contract stress | `restore/semantic_stress/reproduce.py`; [fixed design and results](restore/semantic_stress/README.md) | Fast pilot by default; optional 35-anchor full run. SQLite 3.37.2, no network or model calls. Separates baseline eligibility, synthetic perturbations, reference controls and historical scores. |
| Further measurements and recorded diagnoses | `code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/`, `code/vldb_analysis/analysis/`, `responses/`, `diagnosis/` | Script dependencies and result provenance are listed in `code_report.md` and `code_manifest.json`. Each measurement retains its own engine, input and timing scope. |

## Runtime and access

The offline replay requires Python 3.11 or later and the pinned NumPy dependency. It reads the compressed SQLite files through a disposable workspace; the source download and full graph services are separate workflows. Its receipt reports elapsed time on the executing machine. SQLite release and timeout affect SQL execution measurements, so those measurements retain their recorded environments.

For source checks, install `requirements-sources.txt` and LibreOffice, then follow [Restore sources and evidence](README.md#restore-sources-and-evidence) and [Rebuild and gate the benchmark](README.md#rebuild-and-gate-the-benchmark). Network restoration checks the specific archive, member and conversion hashes. Restored documents remain governed by their source terms.

The released query projection has 552,138 documents, 358,062 dispositions, 4,345 CR packs and 41,337 clauses. `sources/released_record_counts.json` separates these counts by WG. CQ receipts describe the original loaded process graph; report restoration and the benchmark gate are fresh checks of their respective released inputs.

## Extending a comparison

Use the admitted item identifiers, requested fields and gold row sets in `benchmark/items_final/gate/`. Store one response per item in the response format used by the corresponding released condition and run the packaged scorer. Preserve the question version, model configuration, tool/evidence access, engine release and timeout with the result. The stored-response workflows above provide an executable reference for scoring and aggregation. New response generation is an author-run experiment with its own execution requirements.

Use the repository issue tracker for reproducibility reports. Include the commit, command, environment and the failing receipt or item identifier. Source quotations can remain local; file hashes and locators identify the evidence.
