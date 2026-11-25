# Recompute lexical and identifier containment

This bundle computes twelve containment routes for the 667 admitted benchmark questions from the five restored retrieval SQLite indices. It uses the released original `Index`, BM25 query, identifier lookup, one-hop expansion and containment judge. Every route is compared to the current 667-item reference at `responses/final/text_route_ceiling/items.jsonl`.

The fresh results reproduce the recorded route details: chunk and document counts, context character counts, gold-row location labels, field containment counts, and hop expansion counts. The receipt also checks question and gold hashes and the item metadata. `items.jsonl` contains the fresh per-item judgments; `summary.json` applies the original aggregation to the twelve recomputed routes.

## Run from the released checkout

Place this bundle at `restore/lexical_containment`. Restore `ran1_restored.sqlite3` through `ran5_restored.sqlite3` using the corpus restoration instructions, then supply the checkout and index locations. Every input path is a CLI option, and the working directory can be chosen independently.

```sh
free -h
lexical_release=/path/to/released-checkout
lexical_indices=/path/to/restored-retrieval-indices
python3 "$lexical_release/restore/lexical_containment/replay_lexical_containment_portable.py" \
  --route-module "$lexical_release/code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/measure_text_route_ceiling.py" \
  --items "$lexical_release/benchmark/items_final/core/chain_items.jsonl" \
  --items "$lexical_release/benchmark/items_final/ran5/chain_items.jsonl" \
  --gate "$lexical_release/benchmark/items_final/gate/core/chain_items_gate.json" \
  --gate "$lexical_release/benchmark/items_final/gate/ran5/chain_items_gate.json" \
  --historical-items "$lexical_release/responses/final/text_route_ceiling/items.jsonl" \
  --index "RAN1=$lexical_indices/ran1_restored.sqlite3" \
  --index "RAN2=$lexical_indices/ran2_restored.sqlite3" \
  --index "RAN3=$lexical_indices/ran3_restored.sqlite3" \
  --index "RAN4=$lexical_indices/ran4_restored.sqlite3" \
  --index "RAN5=$lexical_indices/ran5_restored.sqlite3" \
  --expected-items 667 --out ./lexical-containment-replay
```

The command opens SQLite read-only and writes fresh judgments and a receipt to a new or empty output directory. A strict difference produces a failing exit code. `--wg RAN3 --expected-items 140` selects one WG while retaining the same explicit input paths. Independent WGs can run as separate processes, with a separate output directory and admitted-item count for each: RAN1 110, RAN2 140, RAN3 140, RAN4 139 and RAN5 138. The original module enforces its available-memory guard.

The routes are `bm25_8x1500`, `bm25_12x4000`, `tdoc_1500`, `tdoc_full`, `idkey_1500`, `idkey_full`, `idany_1500`, `idany_full`, `hopkey_1500`, `hopkey_full`, `hopany_1500` and `hopany_full`. The wrapper directly calls the [released original functions](../../code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/measure_text_route_ceiling.py), retaining their context construction and judge. It explicitly blocks the module's dense retrieval and rank-fusion entry points. Python's standard library is sufficient.

The verification covers the twelve deterministic routes and their saved judgment fields. Dense and RRF routes require a fresh retrieval measurement; runtime is measured afresh and recorded separately. The historical containment file stores judgment summaries rather than candidate-ID lists, so the strict historical comparison concerns the listed fields. The recorded reference generation is identified by its file SHA-256 in `receipt.json`. These files contain IDs, hashes, counts and labels; source passages remain in the separately restored read-only indices.
