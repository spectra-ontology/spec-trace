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
protocol_bounds.py        recomputes the paper's protocol-level bounds from recorded
                          artifacts (retrieval coverage at top-k, KG failure accounting,
                          gold cardinality); no network, no LLM
make_results_figure.py    regenerates the results figure from results/scores.json
sparql_row_equivalence.py compares the 142 RAN1 SPARQL translations against their
                          Cypher references cell by cell rather than by row count;
                          needs a live Neo4j holding the RAN1 graph for the Cypher
                          side, but --classify-untranslated-only runs offline.
                          See release_package/MANIFEST.md §2.1
models.json               the nine-model roster (OpenRouter catalog IDs)
schema_cards.json         per-WG Neo4j schema cards shown to kg_grounded models
results/scores.json       aggregate metrics for all 27 (model x condition) runs
results/{condition}/{model}/all.jsonl.gz   one JSON row per question (624 each), 27 runs
results/_rag_cache/{wg}/{cq_id}.json       per-question retrieval log shared by all RAG runs
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
