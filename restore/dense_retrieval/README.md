# Reconstruct dense collections and replay recorded reader inputs

This bundle reconstructs the **1,334 recorded requests for 667 admitted questions and two local readers** from restored retrieval chunks. It connects the ordered candidate IDs to full-text and metadata hashes, then calls the released original request builder and checks the resulting request SHA-256. Python's standard library is sufficient for this replay; the restored SQLite files remain read-only.

The released checkout and all five independently restored WG indices passed this verification: **1,334/1,334 request hashes** and all **777 unique candidate payload hashes/point IDs** agreed. `stored_context_replay_receipt.json` records the input hashes and checks.

The recorded ordered contexts are fixed experimental inputs. A fresh query-embedding and ANN run is a separate measurement: equal-score candidates can appear in a different order and therefore produce a different reader request. The released CPU pilot recovered all five candidate sets, the order of four sets, and eight of ten reader request hashes. The RAN2 difference exchanges three candidates tied at both the recorded and fresh scores. `fresh_pilot_summary.json` preserves that comparison, runtime and source receipt hash. It covers five fixed questions, with document vectors and answer-model outputs retaining their recorded state.

The document-vector constructor additionally connects read-only retrieval SQLite
to the pinned BGE-M3 document encoder and fresh Qdrant collections. Its completed
empty-store pilot created all 15 WG/type collections, encoded and loaded one
chunk per collection, and executed five fresh question retrievals. A separate
checker reopened the store and verified all 15 source point IDs, payload hashes,
vector dimensions, normalized vectors and self-retrieval scores. This bounded
construction test used all five independently restored retrieval indexes, CPU and
full-load TDoc preprocessing; the receipts distinguish it from corpus restoration
and from the complete historical-vector query pilot above.

## Construct fresh document-vector collections

Restore the five WG retrieval SQLite files following the
[corpus construction guide](../retrieval/README.md). The builder accepts those
files as read-only inputs. Install the versions recorded in
[`requirements-dense.txt`](requirements-dense.txt) in a separate Python 3.10
environment and prepare the verified local snapshot described below. The
executed construction receipt records Python, Torch, library versions and
all ten model-file hashes.

```sh
free -h
dense_release=/path/to/released-checkout
dense_indices=/path/to/restored-retrieval-indices
dense_snapshot=/path/to/official-pinned-bge-m3-snapshot
dense_build=/path/to/new-dense-build
python3 -B "$dense_release/restore/dense_retrieval/build_dense_collections.py" \
  --snapshot "$dense_snapshot" \
  --index "RAN1=$dense_indices/ran1_restored.sqlite3" \
  --index "RAN2=$dense_indices/ran2_restored.sqlite3" \
  --index "RAN3=$dense_indices/ran3_restored.sqlite3" \
  --index "RAN4=$dense_indices/ran4_restored.sqlite3" \
  --index "RAN5=$dense_indices/ran5_restored.sqlite3" \
  --index-origin restored \
  --items "$dense_release/benchmark/items_final/gate/core/chain_items_admitted.jsonl" \
  --items "$dense_release/benchmark/items_final/gate/ran5/chain_items_admitted.jsonl" \
  --tdoc-mode full --prefix rebuild_check_ \
  --qdrant-path "$dense_build/qdrant" \
  --limit-per-collection 1 --device cpu --torch-threads 2 \
  --out "$dense_build/results"
python3 -B "$dense_release/restore/dense_retrieval/test_dense_builder.py"
```

For complete selected-WG construction, set `--limit-per-collection 0` and use
`--qdrant-url http://localhost:6333` for a local Qdrant server with capacity for
the complete vectors. The `rebuild_<label>_` prefix creates isolated collection
names; existing targets are rejected. Collection counts are checked against
the frozen 15-collection contract. Each encoded batch is retrieved after upload
to verify the original point IDs, reader text/metadata payloads and normalized
vectors. The audit stores per-point content/input/vector hashes; bounded pilots
also retain the encoded float32 vectors. Local cosine stores may renormalize
when reopening, so the independent checker compares vectors to their retained
encoder outputs with an absolute tolerance of 1e-5.

`--tdoc-mode full` preserves original content; `incremental` strips its encoding
input and preserves the original payload. CR encoding strips text and retains
its payload; Resolution encoding uses the restored projected chunk text.
Both paths use the original registry's 8,192-token truncation and normalization.
The selected preprocessing mode is recorded in every receipt. The local-disk
backend provides exact cosine reference retrieval; the localhost server accepts
the frozen HNSW/optimizer/WAL settings for full collection construction.

[`empty_collection_pilot_receipt.json`](empty_collection_pilot_receipt.json)
records the executed 15-point build and five question retrievals.
[`empty_collection_point_ledger.jsonl`](empty_collection_point_ledger.jsonl)
provides source IDs, content hashes and encoded float32 vector receipts.
[`empty_collection_pilot_verification.json`](empty_collection_pilot_verification.json)
records the independent reopened-store check.
`verify_dense_build.py` accepts these receipts, the local Qdrant path and explicit
`WG=SQLITE` paths to repeat that check. Full-corpus document re-encoding and its
runtime are measured when the complete build command is executed.

## Files and code

* `contexts.jsonl`: admitted question/model identifiers, question/request hashes and ordered candidate IDs/scores. These records contain neither source passages nor model answers.
* `candidates.jsonl`: 777 unique admitted candidates, their point IDs and full-text/metadata hashes.
* `encoding_retrieval_contract.json`: pinned model files, encoding and retrieval settings, and all 15 collection configurations/counts.
* `fresh_pilot_summary.json`: a direct comparison of the completed five-question CPU query-retrieval pilot with the archived candidates and requests.
* `fresh_query_pilot_receipt.json`: the underlying completed pilot's candidate IDs/scores, request comparisons and query-vector hashes.
* `stored_context_replay_receipt.json`: the complete five-WG fixed-context replay receipt.
* `manifest.json`: bundle hashes and validation receipts.
* `replay_dense_contexts_portable.py`: explicit-path replay and fresh-query CLI.

The original [request and retrieval code](../../code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/run_chain_eval.py), [encoding registry](../../code/scripts/common/common/embedding_registry.py), and [pinned model file contract](../../code/scripts/common/common/local_model.py) define the corresponding operations. Place this bundle at `restore/dense_retrieval` in the released checkout to use these relative links and the following commands. The CLI accepts every input path explicitly, so the checkout and restored databases can live anywhere.

## Replay the fixed contexts

First restore the five WG retrieval SQLite files using the corpus restoration instructions. Set `dense_release` to the checkout and `dense_indices` to the directory containing `ran1_restored.sqlite3` through `ran5_restored.sqlite3`.

```sh
free -h
dense_release=/path/to/released-checkout
dense_indices=/path/to/restored-retrieval-indices
python3 "$dense_release/restore/dense_retrieval/replay_dense_contexts_portable.py" replay \
  --request-module "$dense_release/code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/run_chain_eval.py" \
  --items "$dense_release/benchmark/items_final/core/chain_items.jsonl" \
  --items "$dense_release/benchmark/items_final/ran5/chain_items.jsonl" \
  --gate "$dense_release/benchmark/items_final/gate/core/chain_items_gate.json" \
  --gate "$dense_release/benchmark/items_final/gate/ran5/chain_items_gate.json" \
  --context-manifest "$dense_release/restore/dense_retrieval/contexts.jsonl" \
  --candidate-manifest "$dense_release/restore/dense_retrieval/candidates.jsonl" \
  --index "RAN1=$dense_indices/ran1_restored.sqlite3" \
  --index "RAN2=$dense_indices/ran2_restored.sqlite3" \
  --index "RAN3=$dense_indices/ran3_restored.sqlite3" \
  --index "RAN4=$dense_indices/ran4_restored.sqlite3" \
  --index "RAN5=$dense_indices/ran5_restored.sqlite3" \
  --expected-items 667 --expected-count 1334 --out ./dense-fixed-replay
```

Success requires all candidate point IDs and full-text/metadata hashes to agree and all 1,334 request hashes to match. A coverage or hash mismatch produces a failing exit code. The output contains `receipt.json`, per-request hash checks, and a reconstructed metadata-only `contexts.jsonl`. To build the context manifest directly from the released response files, replace `--context-manifest ...` with `--response-dir "$dense_release/responses/chain_eval"`.

## Pinned local model and fresh query replay

The model is [BAAI/bge-m3 at revision 5617a9f61b028005a4858fdac845db406aefb181](https://huggingface.co/BAAI/bge-m3/tree/5617a9f61b028005a4858fdac845db406aefb181). Its pinned upstream model card declares MIT. Prepare those official files in a local snapshot directory and verify the file hashes in `encoding_retrieval_contract.json`; model weights stay in that separate local cache. The CLI verifies all ten files before loading the model and selects CPU explicitly. Installed local Torch, Transformers, Sentence Transformers and Hugging Face dependencies support this optional measurement.

The contract uses CLS pooling, 1,024 dimensions, normalized vectors and an 8,192-token budget with the original tokenizer/truncation procedure. Document and query prefixes are empty. A query searches Resolution, CR and TDoc collections separately at limit k, then merges by descending score and keeps k. The original code supplies the server's default ANN search parameters. Each k in the recorded sweep is searched separately. Document-vector reconstruction also preserves the loader's full/incremental preprocessing choice documented in the contract.

The following command measures the first admitted question per WG against an existing restored Qdrant service. It encodes query vectors locally, records their hashes, retrieves fresh candidates and builds request hashes using the original code. Its output records the measured runtime and environment. It performs the query/retrieval stage only.

```sh
free -h
dense_release=/path/to/released-checkout
dense_snapshot=/path/to/official-pinned-bge-m3-snapshot
CUDA_VISIBLE_DEVICES='' python3 "$dense_release/restore/dense_retrieval/replay_dense_contexts_portable.py" fresh-query \
  --request-module "$dense_release/code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/run_chain_eval.py" \
  --items "$dense_release/benchmark/items_final/core/chain_items.jsonl" \
  --items "$dense_release/benchmark/items_final/ran5/chain_items.jsonl" \
  --gate "$dense_release/benchmark/items_final/gate/core/chain_items_gate.json" \
  --gate "$dense_release/benchmark/items_final/gate/ran5/chain_items_gate.json" \
  --context-manifest "$dense_release/restore/dense_retrieval/contexts.jsonl" \
  --common-dir "$dense_release/code/scripts/common" \
  --local-model-module "$dense_release/code/scripts/common/common/local_model.py" \
  --snapshot "$dense_snapshot" --qdrant-url http://localhost:6333 \
  --torch-threads 2 --fresh-items first-per-wg --out ./dense-fresh-queries
```

`--fresh-items all` selects all admitted questions. Every fresh measurement writes to a new output directory; archived responses and the fixed context manifest remain read-only. Candidate-set agreement, candidate order and request-hash agreement are recorded separately in the fresh receipt.
