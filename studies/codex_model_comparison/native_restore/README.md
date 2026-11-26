# Portable inputs for the preserved native Cypher study

This input package reconstructs the graph projection consumed by all 750 executed Cypher queries in the 32-session study. It reuses the release's complete CQ graph topology and adds native-source property overlays. Each capture compares every source node and relationship with its corresponding published topology record, then repeats the complete projected-content fingerprint pass. The retained query files, source manifests, serializer sources, and sidecars are bound by SHA-256.

`dependencies.json` enumerates every executed query and its source-file/query digest. Its 29-property whitelist conservatively includes temporary-map field names. Complete nodes, labels, directed relationship occurrences, endpoints and types support fixed labels, paths, entity comparisons, `startNode`, `endNode`, and `type`. Preserved unbound query parameters reproduce the original missing-parameter outcomes. Each overlay replaces an affected node's complete projected property map; composition with the published base preserves both present and absent values.

## Files

- `source/RANn/manifest.json`: source counts, repeated native fingerprints, complete topology-comparison coverage, property overlay shards, and base-view/helper/adapter bindings.
- `source/RANn/*property-overlay*.jsonl.gz`: typed native property maps for records whose projected properties differ from the reused base.
- `source/RANn/definition_binding.json`, `label_order.json`, and `schema_token_observations.json`: definition and query-visible schema bindings.
- `index_support/RANn.json`: separately captured native Neo4j version/index inventory. Projected-property range indexes support replay performance.
- `receipts/`: completed source preflight, fresh-target content verification, index restoration and original-query comparison records.
- `snapshot.py`: study dependency and property-overlay adapter over the pinned release serializer.
- `support.py`: helper/sidecar preflight and index support.
- `restore_and_replay.py`: one-command fresh restore and native replay into an explicitly supplied empty database.
- `resume_verification.py`: source-pinned administrative readback recovery for the recorded RAN4 process interruption.

The package uses `sources/competency_queries/graph_view/RANn` and `restore/competency_queries` from the same complete release. Keep their relative release layout. `snapshot.py`'s source input is the bundled `source` directory; generated receipts can be written to another directory.

## Restore and compare

Use Python 3 with the release's pinned dependencies and a dedicated, initially empty Neo4j **5.26.0** database. Set `NEO4J_USER` and `NEO4J_PASSWORD` for that target. The target URI is explicit; restore confirms emptiness before creating graph records. Run one working group per empty target:

```sh
python3 -B native_restore/restore_and_replay.py \
  --working-group RAN1 \
  --bolt bolt://127.0.0.1:17787 \
  --output-directory /tmp/spectra-ran1-restored-check
```

Run this command from the study directory containing `analysis.json` and `replay_queries.py`. Use a fresh receipt output directory and a fresh graph for each RAN1–RAN5 run. Each working group verifies 150 executed native query outcomes plus the preserved unanswered slots. The wrapper first checks source/helper digests, composes and verifies every projected input fingerprint, restores typed content, verifies actual restored content and schema observations, applies captured range indexes over retained properties, and compares the original query outcomes and rowsets through `replay_queries.py`.

For an input-only check without a database:

```sh
python3 -B native_restore/support.py verify --working-group RAN1
python3 -B native_restore/snapshot.py check --working-group RAN1
```

Original query files, execution results, and frozen study protocol remain the comparison reference. Runtime Neo4j stores are disposable local verification outputs; the release carries the compressed inputs and verification receipts.

All five restored working groups reproduce **750/750** preserved native query outcomes, including the original 60 execution errors; the 50 unanswered Cypher slots remain unchanged. `verification_summary.json` links each full-content restoration to its 150-query replay receipt. RAN4 completed its empty-target insertion before a supervising-process interruption; its source-pinned recovery receipt records the strict helper-state check and resumed original content/order/schema verification. The resumed process records `initial_counts` as `null` and retains the original insertion checkpoints.
