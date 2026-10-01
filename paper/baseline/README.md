# SpectraCQ Baseline Harness and Recorded Runs

Complete harness and per-question outputs for the three-condition baseline reported in the
paper: closed-book, RAG over the released text collections, and knowledge-graph-grounded
query generation. Every number in the paper's baseline table and results figure can be
recomputed offline from the files in this directory.

## Layout

```
bench_common.py           shared infra: env, OpenRouter chat/embeddings, Qdrant search, Neo4j exec
run_baseline.py           campaign runner (dry-run by default; --confirm to call APIs)
score.py                  deterministic re-scorer (no network, no LLM)
score_core.py             re-scores the recorded runs on SpectraCQ-Core (560) or its
                          contract-exact subset (241, the default); no network, no LLM
score_full_record.py      scores the kg_grounded runs on SpectraCQ-Core by whole
                          returned records, from the replay files below; its replay
                          step needs a Neo4j holding the released graph
protocol_bounds.py        recomputes the paper's protocol-level bounds from recorded
                          artifacts (retrieval coverage at top-k, KG failure accounting,
                          gold cardinality); no network, no LLM
make_results_figure.py    regenerates the results figure from results/scores.json
sparql_row_equivalence.py compares the 142 RAN1 SPARQL translations against their
                          Cypher references cell by cell rather than by row count;
                          needs a live Neo4j holding the RAN1 graph for the Cypher
                          side, but --classify-untranslated-only runs offline.
                          See release_package/MANIFEST.md §2.1
build_relational_db.py    flattens each per-WG Neo4j graph into SQLite for the
                          relational (NL-to-SQL) arm; needs the Neo4j graphs
models.json               the nine-model roster (OpenRouter catalog IDs)
schema_cards.json         per-WG Neo4j schema cards shown to kg_grounded models
sql_schema_cards.json     per-WG SQLite schema cards shown to the sql_grounded model
results/scores.json       aggregate metrics for all 27 (model x condition) runs
results/{condition}/{model}/all.jsonl.gz   one JSON row per question (624 each), 27 runs
results/_rag_cache/{wg}/{cq_id}.json       per-question retrieval log shared by all RAG runs
results/_full_record/{wg}.jsonl.gz         kg_grounded queries replayed on the released graph
relational/runs/sql_grounded/{model}/all.jsonl.gz  relational arm: 1 run, 624 rows
```

## Conditions

All three conditions answer the same 624 released questions
(`release_package/cqs/spectra_cq_v2.0/benchmark.jsonl` at the repository root) and are
scored against the same query-defined gold (`gold_primary_values`).

**closed_book** — system prompt (verbatim):

> You are an expert on the 3GPP RAN standardization process (meetings, TDocs, change
> requests, specifications, technical reports). Answer the question using ONLY your own
> knowledge. Respond with ONLY a JSON object {"answer": [...]} listing the specific
> identifiers or values that answer the question. If you do not know, return
> {"answer": []}. No prose.

**rag** — same prompt except the model must answer "using ONLY the numbered context
passages provided". Retrieval configuration:

- The question is embedded with `openai/text-embedding-3-small` — the same model that
  indexed the released collections, so retriever and index share one embedding space.
- Five per-WG collections are searched: `{wg}_ts_sections`, `{wg}_tdoc_chunks`,
  `{wg}_cr_chunks`, `{wg}_resolution_chunks`, `{wg}_tr_sections`.
- Top 6 chunks per collection by cosine score, merged into a global top 10, each passage
  truncated to 800 characters.
- Retrieval is model-agnostic and cached once per question in `results/_rag_cache/`:
  each file holds the exact `context` string sent to every model plus full `provenance`
  (`collection`, `score`, `chunkId`, `spec`, `section`, `text` per retrieved chunk), so
  any retrieval decision can be audited after the fact.

**kg_grounded** — the model sees the per-WG schema card (`schema_cards.json`) and must
return one Cypher query; the harness executes it read-only against the graph and scores
the first returned column. System prompt (verbatim):

> You translate a natural-language question into ONE Cypher query for the given Neo4j
> schema. The FIRST returned column must hold the answer values. Use only labels,
> properties and relationship types that appear in the schema. Respond with ONLY a JSON
> object {"cypher": "..."}.

## Decoding

Identical across models and conditions: `temperature 0.0`, `max_tokens` 2000 for
kg_grounded and 1200 otherwise, up to 5 retries on transport errors, JSON-object output.
Per-row records include `raw_text`, parsed `predicted_values`, token `usage`, `cost`,
`latency_s`, and finish/error status; kg_grounded rows additionally record the generated
`cypher`, `exec_status`, `exec_row_count`, `exec_columns`, and `exec_error`.

## Scoring

`score.py` is fully deterministic and offline. Gold and prediction values are normalized
(canonicalization, whitespace collapse, casefold) and compared as sets:

- `exact` — strict set equality (for kg_grounded this is execution accuracy in the
  BIRD sense: the executed query's value set equals the reference query's value set);
- set-level `precision`, `recall`, `f1` — partial credit for multi-value answers;
- all metrics macro-averaged over questions.

Re-score everything from the recorded outputs:

```bash
gunzip -k results/*/*/all.jsonl.gz
python3 score.py          # rewrites results/scores.json
```

`make_results_figure.py` then regenerates the results figure from `scores.json`.

### SpectraCQ-Core and the contract-exact subset

`score.py` scores the released key: the first returned column of all 624 questions.
`score_core.py` scores the same recorded outputs on the 560 SpectraCQ-Core items, each
on its declared answer column, against
`release_package/cqs/spectra_cq_v2.0/core_answer_gold.jsonl`. It reads the `.gz` logs
directly and writes nothing unless `--json` is given.

```bash
python3 score_core.py                    # the 241 contract-exact items (default)
python3 score_core.py --set core         # all 560 Core items
python3 score_core.py --gold released    # as the default, but the 7 scope-repaired items keep the released query's values
```

Every run is scored over the whole set, so a question a run never answered scores zero.

### Full-record scoring

`score_core.py` scores each Core item on one column. `score_full_record.py` scores the
kg_grounded runs on whole returned records: a record is the sorted tuple of its normalized
values, and the predicted and gold record sets are compared, so column names, column
order, row order and duplicate rows do not matter. Exact is 1 when the two sets are equal;
precision, recall and F1 are those of their overlap. Each model is averaged over all 560
Core items, and an item whose query is missing or does not execute scores zero. The gold
records are the rows in `release_package/cqs/spectra_cq_v2.0/gold/{WG}_gold.json`; for the
7 scope-repaired items they are the rows of their `repaired_cypher`, and `--gold released`
keeps the released rows for them.

The run logs keep only the first returned column of each query, so the records come from
executing again, on the released graph of each working group, all 5,520
queries the kg_grounded runs recorded, together with the released and repaired reference
queries. The five files in `results/_full_record/` hold that replay, so scoring needs no
database:

```bash
python3 score_full_record.py score                   # repaired rows for the 7 items (default)
python3 score_full_record.py score --gold released   # released rows for the 7 items
```

Scores from these files with the default gold:

| Model | Full record Exact | Full record F1 | Answer column Exact | Answer column F1 |
|---|---:|---:|---:|---:|
| claude-haiku-4.5 | 0.0929 | 0.1229 | 0.2071 | 0.3028 |
| claude-opus-4.8 | 0.1286 | 0.1649 | 0.2446 | 0.3519 |
| deepseek-v3.1 | 0.1125 | 0.1500 | 0.2268 | 0.3325 |
| gemini-2.5-flash | 0.0857 | 0.1123 | 0.2000 | 0.2669 |
| gemini-2.5-pro | 0.0821 | 0.1061 | 0.1821 | 0.2503 |
| gpt-5-mini | 0.0714 | 0.0964 | 0.1518 | 0.1962 |
| gpt-5.1 | 0.0946 | 0.1199 | 0.1982 | 0.2802 |
| llama-3.3-70b | 0.0625 | 0.0770 | 0.1304 | 0.1784 |
| qwen3-235b | 0.0696 | 0.0864 | 0.1357 | 0.1929 |
| pooled | 0.0889 | 0.1151 | 0.1863 | 0.2614 |

Each replay file starts with a header recording the loaded graph (node and relationship
counts, Neo4j and APOC versions, and the name, size and SHA-256 of the body TTL, which is
the file of the Zenodo deposit), the row cap, the transaction timeout and a digest of the
executing code; each record carries its execution time. The replay executes each query as
`bench_common.exec_cypher` does, with its 30-second transaction timeout, and keeps up to
2,000 rows, the result cap the benchmark declares; a query that times out scores zero
and a query that reaches the cap is scored on the rows kept. The recorded runs did not
apply the row cap: 250 recorded executions return more than 2,000 rows. None of their
errors is a timeout. Of the 4,959 replayed queries on Core items,
6 time out and 248 reach the cap.

The same run checks the replay against the release. On the loaded graphs the released
reference queries return the gold records for 542 of the 560 Core items. Of the
291 recorded execution errors, 290 recur, 1 now times out and
0 now execute. Of the queries that executed in the recorded run,
5 time out in the replay and 0 fail. Of the 5,224
queries that executed in both, 4,599 return the same first column; of the rest,
236 reach the row cap in the replay, 172 carry a LIMIT and
217 differ otherwise.

To replay a working group, load its body TTL into an empty Neo4j 5.26 with the APOC plugin,
for example with `python3 release_package/tests/verify_benchmark.py --full --wg RAN1`
(plus `--bolt`, `--user` and `--password`), then run
`python3 score_full_record.py replay --wg RAN1 --ttl ../../release_package/kg/per_wg/RAN1-body.ttl`
with the same connection options; `--ttl` records the loaded file in the header.

## Relational (NL-to-SQL) arm

A fourth condition, `sql_grounded`, asks the model to answer in SQL over SQLite copies of
the same graphs, so that a gap against `kg_grounded` reflects the access structure rather
than the records. `build_relational_db.py` builds `relational/{WG}.sqlite` from each
group's Neo4j graph: one table per node label, one join table per relationship type and a
`node` registry (the mapping is documented at the top of the script).
`sql_schema_cards.json` holds the cards the model was shown; its `kg_card_parity` field
records, per group, whether the graph the tables came from has the same labels,
relationship patterns and properties as `schema_cards.json`, and it holds for all five
groups in the recorded cards.

One run is recorded: claude-opus-4.8, 624 rows, no call errors, under `relational/runs/`.
It sits outside `results/`, so `score.py`, `scores.json` and the results figure do not see
it. Score it with the Core scorer:

```bash
python3 score_core.py --results relational/runs               # 241 contract-exact items
python3 score_core.py --results relational/runs --set core    # all 560 Core items
```

Rebuilding the SQLite files needs the `neo4j` Python driver, `NEO4J_PASSWORD` and the Neo4j
graphs at ports 7687-7691, as `kg_grounded` execution does (below). The five files are not
tracked (1.48 GB in the recorded build). A rebuild or `--verify-only` also writes
`relational/manifest.json` with per-table row counts against the graph, likewise not
tracked. The loader prints `parity=False` for a group whose graph differs from
`schema_cards.json`; `--cards-only` rewrites `sql_schema_cards.json` from the live graphs.

## Re-running the campaign

Re-scoring needs nothing but Python. Re-running the model calls needs:

- `OPENROUTER_API_KEY` in the environment or a repo-root `.env` (chat and embeddings both
  route through OpenRouter);
- for `rag` with a cold cache: a Qdrant instance at `localhost:6333` loaded with the
  released collections (with a warm `_rag_cache/`, retrieval is replayed from disk);
- for `kg_grounded` execution: Neo4j graphs at ports 7687-7691 (RAN1-RAN5). The released
  RAN1 snapshot can be rebuilt from the repository's release package; RAN2-RAN5
  cardinalities in the paper come from the deployed instances.

`run_baseline.py` is dry-run by default and prints what it would call; pass `--confirm`
to spend API credit. Runs are resumable: existing rows in `all.jsonl` are skipped.
