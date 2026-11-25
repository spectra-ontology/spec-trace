# Reconstruct the retrieval corpora

The restoration frontiers preserve the five WG indexes' 4,753,237 chunk identities, metadata, source pointers and text digests. The plenary frontier binds 31,023 archives and 672,580 indexed chunks. Official source archives and the reconstructed document text reside in the reader's local directories. The released query-relation databases in `sqlite/` serve the separate SQL and Cypher experiments.

The WG constructor checks every recovered text row before rebuilding its FTS index. The plenary constructor runs the original recursive archive and document readers, checks each frozen chunk and writes local verified caches for assembly. Reconstruction retains original indexed identities, including the original extractor's recorded member exclusions. Source acquisition, native parsing, index assembly and query comparison have separate execution receipts.

## Runtime and local paths

The index replay was executed with CPython 3.10.12 and SQLite 3.37.2. Native readers use LibreOffice 7.3.7.2 with PyUNO, 7-Zip and native libarchive. [The dependency file](../../requirements-retrieval.txt) records the Python source-reader versions; the score replay uses its separate Python 3.11 environment. The TDoc parsers use the pinned BGE-M3 tokenizer locally for chunking. The deterministic replay commands execute parsing and search without answer-model generation.

Run from the package root and select empty local work directories:

```sh
free -h
retrieval_release="$PWD"
retrieval_code="$retrieval_release/code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
retrieval_inputs="$retrieval_release/restore/retrieval"
retrieval_work=/tmp/spectra-retrieval-replay
mkdir -p "$retrieval_work" "$retrieval_release/code/.git"
/usr/bin/python3 -m venv --system-site-packages "$retrieval_work/environment"
retrieval_python="$retrieval_work/environment/bin/python"
"$retrieval_python" -m pip install -r "$retrieval_release/requirements-retrieval.txt"
export PYTHONPATH="$retrieval_release/code/scripts/common:$retrieval_code"
```

The environment inherits the system PyUNO installation. Check `sqlite3.sqlite_version` in that environment before timing an original-runtime query comparison. Prepare the pinned tokenizer cache before parsing contribution documents:

```sh
free -h
export HF_HUB_CACHE="$retrieval_work/huggingface"
"$retrieval_python" "$retrieval_code/prepare_retrieval_tokenizer.py" \
  --repository "$retrieval_release/code" --cache "$HF_HUB_CACHE" \
  --report "$retrieval_work/tokenizer-acquisition.json" --download
```

The helper checks all five tokenizer/configuration file digests before loading the tokenizer. The source parsers then resolve this revision from the local cache. [The dense-reader contract](../dense_retrieval/encoding_retrieval_contract.json) additionally records the model files and vector-encoding settings for optional fresh dense retrieval.

## WG reports and contribution documents

Each WG's `raw/` directory contains its report source manifest, Resolution recipes and ordered TDoc recipe shards. For RAN3:

```sh
free -h
"$retrieval_python" "$retrieval_code/export_retrieval_artifact.py" acquire-reports \
  --sources "$retrieval_inputs/raw/RAN3/reports.json" \
  --cache "$retrieval_work/archive-cache" --output "$retrieval_work/report-sources" \
  --report "$retrieval_work/ran3-report-acquisition.json" --download

"$retrieval_python" "$retrieval_code/export_retrieval_artifact.py" restore-resolutions \
  --repository "$retrieval_release/code" \
  --recipes "$retrieval_inputs/raw/RAN3/resolution/manifest.json" \
  --sources "$retrieval_inputs/raw/RAN3/reports.json" \
  --source-root "$retrieval_work/report-sources" --output "$retrieval_work/parsed" \
  --report "$retrieval_work/ran3-resolution-replay.json"

"$retrieval_python" "$retrieval_code/export_retrieval_artifact.py" restore-tdocs \
  --repository "$retrieval_release/code" --recipes "$retrieval_inputs/raw/RAN3/tdoc/manifest.json" \
  --cache "$retrieval_work/archive-cache" --source-root "$retrieval_work/tdoc-sources" \
  --output "$retrieval_work/parsed" --report "$retrieval_work/ran3-tdoc-replay.json" --download
```

`--start` and `--stop` select a zero-based, half-open range of the fixed TDoc recipe order. Each execution writes a summary and an outcome JSONL; existing verified source and parsed files support checked reruns with a new report path. The recipes bind 511,655 TDoc documents across all five WGs. This mapping count describes the executable frontier; actual acquisition and parser execution coverage is recorded separately.

The source-acquisition and Resolution replay runs verified all 387,651 indexed contents. RAN1 through RAN4 reproduced 42,767, 49,797, 61,105 and 168,499 contents respectively. RAN5 reproduced 63,840 contents from 36 reports and all 1,643 contents from the indexed historical report112 draft. [The aggregate receipt](receipts/resolution_all_wg.json) binds the separately executed runs. [The historical subset](raw/RAN5/historical112/manifest.json), [official acquisition receipt](raw/RAN5/historical112/acquisition.json) and [replay receipt](raw/RAN5/historical112/replay_receipt.json) identify the successful official `history/` URL, the original source hash and the unchanged readers. The full RAN5 source manifest tries this history URL first. Earlier old-URL HTTP 403 outcomes and the current-revision 1,641/1,643 comparison remain in their original receipts as acquisition and version measurements. Negative controls changed source bytes, a reader-code pin and an expected-content digest; each was rejected before parsed output was emitted.

For the bounded historical-report execution, use the acquisition and Resolution commands above with `raw/RAN5/historical112/reports.json` as `--sources` and `raw/RAN5/historical112/manifest.json` as `--recipes`.

The fixed native-format TDoc follow-up cohort reproduced all 95 originally failed cases under the pinned readers and explicitly recorded source-range/conversion rules. This cohort is a parser-validation scope; the 511,655-document recipe count describes the full executable mapping frontier.

## CR raw forms and chunk assembly

The CR recipes map 56,806 documents and 596,399 chunks. They bind raw form extraction, original parsing and chunk assembly to source and expected-output digests. For RAN3:

```sh
free -h
retrieval_cr="$retrieval_inputs/raw/cr"
"$retrieval_python" "$retrieval_cr/restore_cr_probe.py" acquired-batch \
  --repository "$retrieval_release/code" \
  --recipes "$retrieval_cr/ran3_restore_recipes.jsonl.gz" \
  --cache "$retrieval_work/archive-cache" --source-root "$retrieval_work/cr-sources" \
  --text-cache "$retrieval_work/cr-text" --receipt-dir "$retrieval_work/cr-receipts" \
  --report "$retrieval_work/cr-acquired.json" --download

"$retrieval_python" "$retrieval_cr/restore_cr_probe.py" assemble \
  --recipes "$retrieval_cr/ran3_restore_recipes.jsonl.gz" \
  --text-cache "$retrieval_work/cr-text" --output-root "$retrieval_work/parsed" \
  --report "$retrieval_work/cr-assemble.json"
```

Use the corresponding WG's recipe file for each partition. Raw-source acquisition and parsing receipts enumerate the actually executed documents; complete mappings and those execution scopes are recorded separately. The assembled `parsed` directory supplies the Resolution, CR and TDoc paths consumed by the WG frontier.

## Assemble a WG index

The parsed tree must contain its Resolution, CR and TDoc inputs at the recipe paths. Supply that tree to the frontier constructor:

```sh
free -h
"$retrieval_python" "$retrieval_code/export_retrieval_artifact.py" restore-wg \
  --bundle "$retrieval_inputs/frontier/RAN3" --repository "$retrieval_work/parsed" \
  --output "$retrieval_work/ran3_restored.sqlite3" --report "$retrieval_work/ran3-fts-replay.json"
```

Use the matching `RAN1` through `RAN5` frontier for each partition. The executed five-WG index reconstruction used the read-only original parsed inputs and verified all 4,753,237 recovered text rows. Raw-source parsing has the separate measured coverage described above. The constructor requires complete locator coverage, checks each text SHA-256, recreates the original schema and FTS configuration, and checks SQLite integrity. Rebuilt SQLite page layouts may differ while their logical records and query results agree.

## Reconstruct the plenary index

The recorded extraction of one presentation contains automatic date fields. Its repeatable conversion uses the date displayed in the indexed rendering, supported by the original index timestamp and verified chunk text. The calendar setting is scoped to the converter's subprocess environment. Build [libfaketime from the pinned upstream commit](https://github.com/wolfcw/libfaketime/tree/c88b79b4e9cc1c94294037b4677b69185861c2a1) with `make -C src`; supply its local `libfaketimeMT.so.1` path. The parent process and host clock retain their normal settings.

```sh
free -h
retrieval_clock_library=/path/to/libfaketime/src/libfaketimeMT.so.1
"$retrieval_python" "$retrieval_code/restore_plenary_artifact.py" \
  --bundle "$retrieval_inputs/frontier/plenary" --cache "$retrieval_work/plenary-archives" \
  --converter-date 2026-11-14 --converter-clock-library "$retrieval_clock_library" \
  --text-cache "$retrieval_work/plenary-text" --report "$retrieval_work/plenary-extraction.json"

"$retrieval_python" "$retrieval_code/assemble_plenary_artifact.py" \
  --bundle "$retrieval_inputs/frontier/plenary" --text-cache "$retrieval_work/plenary-text" \
  --out-index "$retrieval_work/plenary_restored.sqlite3" --report "$retrieval_work/plenary-assembly.json"
```

The first command acquires pinned official archives as needed. `--source-root /path/to/source-tree` additionally accepts matching local original archives, and `--offline` requires matching local or cached bytes. `--file-id` selects explicit archive identities. For independent workers, use `--shard-count N --shard-index I`, a separate report for each shard and the same verified cache directory. Assembly requires all 31,023 files and checks every chunk against the frontier before writing the complete index.

[The source coverage receipt](receipts/plenary_source_coverage.json) records all 31,023 successful archive re-extractions and 672,580 verified chunks. It preserves the failed pypdf 6.6.0 case and the successful pypdf 6.10.2 retries. The same Python 3.10 runtime with only the PDF reader changed reproduced that archive's ten chunks. This establishes the pinned PDF-reader requirement. The coverage receipt distinguishes local original-archive reuse from fresh network acquisition.

## Replay the measured retrieval interfaces

The [lexical containment bundle](../lexical_containment/README.md) recomputes twelve deterministic routes for every admitted question. Its completed execution reproduced all 8,004 route records, including context sizes, row classifications and field counts, against the current 667-item reference. [The dense-context bundle](../dense_retrieval/README.md) reconstructs all 1,334 recorded local-reader requests and verifies 777 unique candidate payloads. It also documents the separately executed fresh CPU query-retrieval pilot and tied-score ordering behavior.

The raw-source replay additionally uses the restored plenary index. Its completed execution reproduced all scientific judgment fields and stored route orders for all 667 admitted items; [the five-WG receipt](receipts/raw_containment_all_items.json) links each partition's execution. Elapsed time and physical index fingerprints retain their fresh execution values.

After constructing the five WG indexes and plenary index, run:

```sh
free -h
"$retrieval_python" "$retrieval_code/reproduce_raw_containment_portable.py" \
  --module-dir "$retrieval_code" --common-dir "$retrieval_release/code/scripts/common" \
  --items "$retrieval_release/benchmark/items_final/gate/core/chain_items_admitted.jsonl" \
  --items "$retrieval_release/benchmark/items_final/gate/ran5/chain_items_admitted.jsonl" \
  --index RAN1="$retrieval_work/ran1_restored.sqlite3" \
  --index RAN2="$retrieval_work/ran2_restored.sqlite3" \
  --index RAN3="$retrieval_work/ran3_restored.sqlite3" \
  --index RAN4="$retrieval_work/ran4_restored.sqlite3" \
  --index RAN5="$retrieval_work/ran5_restored.sqlite3" \
  --plenary "$retrieval_work/plenary_restored.sqlite3" \
  --reference-items "$retrieval_release/responses/final/raw_source_route/items.jsonl" \
  --reference-orders "$retrieval_release/responses/final/raw_source_route/orders.jsonl" \
  --expected-items 667 --out "$retrieval_work/raw-containment"
```

The independent verifiers `verify_restored_retrieval.py` and `verify_restored_plenary.py` compare every logical table with an available read-only experimental index and exercise the original search functions. [The complete WG comparison](receipts/independent_all_wg.json) checks all 4,753,237 rows and 1,334 original BM25 searches, covering every admitted question in both metadata and text-only modes. These comparison tools serve reconstruction verification; new users run the released retrieval interfaces against their restored files.

| Reconstructed input or replay | Executed scope and receipt |
|---|---|
| WG FTS indexes | [Every logical row and all 1,334 benchmark searches](receipts/independent_all_wg.json) |
| Plenary source extraction | [31,023 source files and 672,580 chunks](receipts/plenary_source_coverage.json) |
| Plenary index assembly | [Complete checked-cache assembly](receipts/plenary_assembly.json) |
| Plenary logical rows and search | [All seven tables, 667 questions and 100 evenly spaced owner filters](receipts/plenary_independent_comparison.json) |
| Raw-source containment | [All 667 item judgments and route orders](receipts/raw_containment_all_items.json) |
| Lexical containment | [All 8,004 deterministic route records](../lexical_containment/README.md) |
| Recorded dense contexts | [All 1,334 request digests](../dense_retrieval/README.md) |
| Native conversion and corpus audit | [Selected-archive conversion and original-corpus audit scopes](../census/README.md) |
