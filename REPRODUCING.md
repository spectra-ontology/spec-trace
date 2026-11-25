# Reproducing the paper

The release connects process records, generated questions and recorded experimental outcomes. Begin with the offline replay in the [README](README.md#start-with-the-published-results); then choose the source checks or benchmark construction relevant to your use. [Experimental interfaces and inputs](EXPERIMENTS.md) identifies the information available in each measured condition.

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
| WG and plenary retrieval indexes | [Text-free frontiers and restoration commands](restore/retrieval/README.md), source locators and local downloaded/parsed documents | Reconstructs five WG FTS indexes and the plenary index. Preparation checked 4,753,237 WG chunks and extracted all 31,023 plenary source files containing 672,580 chunks. Per-stage receipts identify source acquisition, conversion, parsing and assembly scope. |
| Lexical containment diagnostic | [Portable lexical workflow](restore/lexical_containment/README.md), restored WG indexes and 667 admitted items | Reproduces all 8,004 route records against the current recorded reference. |
| Raw-source containment diagnostic | [Raw-source replay command](restore/retrieval/README.md#replay-the-measured-retrieval-interfaces), five restored WG indexes and restored plenary index | Reproduces scientific judgment fields and route orders for all 667 admitted items against the current raw-source reference. |
| Recorded dense-reader contexts | [Portable dense-context replay](restore/dense_retrieval/README.md), restored WG indexes and the recorded candidate frontier | Checks 1,334 request digests for 667 items. A fresh vector search has separate model, document-vector and runtime requirements described in that workflow. |
| Complete corpus-wide source audits | [Source inventory, metadata and original readers](restore/census/README.md), with a local source tree | Whole-corpus execution from the original local sources reproduces the recorded scientific outputs. Fresh-download and native-conversion pilots retain their enumerated coverage and receipts. |
| Further measurements and recorded diagnoses | `code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/`, `code/vldb_analysis/analysis/`, `responses/`, `diagnosis/` | Script dependencies and result provenance are listed in `code_report.md` and `code_manifest.json`. Each measurement retains its own engine, input and timing scope. |

## Runtime and access

The offline replay requires Python 3.11 or later and the pinned NumPy dependency. It reads the compressed SQLite files through a disposable workspace; the source download and full graph services are separate workflows. Its receipt reports elapsed time on the executing machine. SQLite release and timeout affect SQL execution measurements, so those measurements retain their recorded environments.

For source checks, install `requirements-sources.txt` and LibreOffice, then follow [Restore sources and evidence](README.md#restore-sources-and-evidence) and [Rebuild and gate the benchmark](README.md#rebuild-and-gate-the-benchmark). Network restoration checks the specific archive, member and conversion hashes. Restored documents remain governed by their source terms.

For retrieval and corpus-audit reconstruction, use the runtime and native-tool
instructions in their linked workflows. Retrieval parsing uses
`requirements-retrieval.txt`, the original tokenizer, and LibreOffice/PyUNO for
the native formats covered by each source recipe. The plenary instructions
also preserve the converter date used for cached presentation fields. These
source-processing dependencies are separate from the lightweight offline
score replay.

The released query projection has 552,138 documents, 358,062 dispositions, 4,345 CR packs and 41,337 clauses. `sources/released_record_counts.json` separates these counts by WG. CQ receipts describe the original loaded process graph; report restoration and the benchmark gate are fresh checks of their respective released inputs.

## Extending a comparison

Use the admitted item identifiers, requested fields and gold row sets in `benchmark/items_final/gate/`. Store one response per item in the response format used by the corresponding released condition and run the packaged scorer. Preserve the question version, model configuration, tool/evidence access, engine release and timeout with the result. The stored-response workflows above provide an executable reference for scoring and aggregation. New response generation is an author-run experiment with its own execution requirements.

Use the repository issue tracker for reproducibility reports. Include the commit, command, environment and the failing receipt or item identifier. Source quotations can remain local; file hashes and locators identify the evidence.
