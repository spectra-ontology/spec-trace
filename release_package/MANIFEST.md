# SPECTRA Release — Canonical Counts Manifest

Single source of truth for every headline count that appears in the paper, the
README/CHANGELOG, and the artifact metadata. Each number is paired with the
released file that produces it and, where relevant, the command that
regenerates that file. When any document disagrees with a number here, this
file is authoritative and the document is wrong.

All counts below are measured on the released per-WG body knowledge graphs
under `kg/per_wg/` and the released benchmark under
`cqs/spectra_cq_v2.0/`. Node / relationship counts come from loading each
released TTL with the shipped loader; triple counts come from streaming the
same TTLs with the shipped parser (no database); benchmark counts come from the
shipped benchmark files directly.

---

## 1. Dataset — per-WG body knowledge graphs

Evidence: `validation/cq_replay/graph_counts.json` (nodes, relationships,
labels, relationship types — from the live graph after loading each TTL with
the shipped loader) and `validation/cq_replay/triple_counts.json` (RDF triples
— from streaming the TTLs with the shipped parser).

| WG | Nodes | Relationships | RDF triples |
|----|------:|--------------:|------------:|
| RAN1 | 165,418 | 848,228 | 2,254,591 |
| RAN2 | 156,288 | 939,037 | 2,371,016 |
| RAN3 | 87,980 | 481,498 | 1,204,524 |
| RAN4 | 342,161 | 1,592,845 | 4,297,525 |
| RAN5 | 215,012 | 1,047,242 | 2,804,186 |
| **Total** | **966,859** | **4,908,850** | **12,931,842** |

- Node labels (distinct, across all five graphs): **32**
- Relationship types (distinct, across all five graphs): **59**
- Cross-check: for every WG the loaded node count equals the number of
  instance subjects the parser sees in the TTL (`nodes_eq_parse = true` in
  `graph_counts.json`; per-WG `instance_subjects` in `triple_counts.json`
  equal the node counts above). The loaded relationship count equals the
  number of unique relation triples the parser sees (`rels_eq_parse = true`).

These are three different granularities of the same graphs, all reported
separately and never conflated:

- **Nodes** = merged distinct instance subjects loaded into Neo4j (966,859).
- **Relationships** = distinct relation edges in Neo4j (4,908,850).
- **RDF triples** = every (subject, predicate, object) statement in the TTL,
  including literal-valued data properties (12,931,842). A triple count is
  necessarily larger than the node+relationship count because most triples are
  literal attributes, not edges.

Regenerate:

```
python3 scripts/paper/replay_released_cqs.py \
    --bolt bolt://localhost:7697 --user neo4j --password <pw>   # -> graph_counts.json
python3 release_package/pipeline/count_triples.py               # -> triple_counts.json
```

---

## 2. Benchmark — SpectraCQ v2.0 (competency questions)

Evidence: `cqs/spectra_cq_v2.0/benchmark.jsonl` (released scored CQs, one JSON
object per line), `cqs/spectra_cq_v2.0/questions.json` (`metadata` block),
`cqs/spectra_cq_v2.0/gold/_gold_summary.json` (authored / released / held
split), `cqs/spectra_cq_v2.0/held/held_cqs.json` (the held-out set).

| WG | Authored | Released (scored) | Held-out |
|----|---------:|------------------:|---------:|
| RAN1 | 145 | 142 | 3 |
| RAN2 | 132 | 128 | 4 |
| RAN3 | 129 | 123 | 6 |
| RAN4 | 125 | 117 | 8 |
| RAN5 | 123 | 114 | 9 |
| **Total** | **654** | **624** | **30** |

- **Authored CQs: 654** — every CQ written across the five WGs. Gold answer
  sets for all 654 live under `cqs/spectra_cq_v2.0/gold/` (the authored
  superset is kept intact; it is not the released scored set).
- **Released (scored) CQs: 624** — the CQs shipped for scoring. This is the
  headline benchmark size. Equals the line count of `benchmark.jsonl`, the
  number of `.cypher` files under `cypher/`, and the length of the `cqs` list
  in `questions.json`.
  - Released by phase: P1 123 / P2 112 / P3 233 / P4 75 / P5 81.
- **Held-out CQs: 30** — CQs whose gold answer against the current graph is
  empty or uniformly zero/false (entity-layer constructs not materialized in
  the operational graph, or genuinely-empty answer sets). Held out of scoring
  to avoid degenerate set-scoring, and shipped under `held/` with their Cypher
  and status. Because their gold is degenerate/empty, holding them out leaks
  nothing about the released set.

**Gold answer definition:** each released CQ's gold is the SET of values in the
first RETURN column obtained by executing its reference Cypher against the
graph, plus a row count. No LLM and no human annotation is in the gold path.
Reference queries whose ranking is truncated by `LIMIT` carry a data-intrinsic
tie-break so the top-k set is reload-stable.

### 2.1 Query artifacts

- **Cypher reference queries: 624** — one per released CQ, under
  `cqs/spectra_cq_v2.0/cypher/*.cypher`. This is the full benchmark: every
  released CQ has an executable Cypher reference query.
- **SPARQL portability set: 142** — under
  `cqs/spectra_cq_v2.0/sparql/*.rq`. These are SPARQL translations of all
  142 released RAN1 CQs; they demonstrate that the CQs are answerable over
  the standard RDF serialization, not that all 624 have SPARQL forms. The 142
  is the **RAN1 slice for portability**, distinct from the 624-query full
  Cypher benchmark — the two counts must never be presented as the same thing.

SPARQL/Cypher parity (evidence: `validation/cq_replay/sparql_parity_results.json`):
executing all 142 SPARQL translations over the released `RAN1-body.ttl` and
comparing row counts against the Cypher replay oracle yields **142/142
row-count match**, of which **80 are exact_cardinality** (the count is the true
unbounded result-set size) and **62 are limit_bound_topn** (the count equals a
shared `LIMIT` — cardinality parity, with row-level cross-engine equivalence
tracked as future work). 0 errors, 0 mismatches.

Regenerate:

```
python3 release_package/pipeline/validate_sparql_parity.py   # -> sparql_parity_results.json
```

---

## 3. Evaluation — baseline suite

Evidence: `scripts/paper/baseline/results/scores.json`.

- **Models: 9** — claude-opus-4.8, claude-haiku-4.5, deepseek-v3.1,
  gemini-2.5-pro, gemini-2.5-flash, gpt-5.1, gpt-5-mini, llama-3.3-70b,
  qwen3-235b.
- **Conditions: 3** — closed_book, rag, kg_grounded.
- **Predictions scored: 16,848** = 624 released CQs × 9 models × 3 conditions
  (`rows_scored` in `scores.json`; `gold_cqs = 624`; every one of the 27
  model×condition cells has n = 624; duplicates_skipped = 0,
  rows_without_gold = 0, rows_with_call_error = 0).

---

## 4. Reproducibility checks

- **Benchmark self-replay: 624/624.** Wipe a scratch Neo4j, load each released
  TTL with the shipped loader, run every shipped reference Cypher, and compare
  its primary-column answer SET + row count against the shipped gold in
  `benchmark.jsonl`. Every WG reproduces every released CQ
  (`validation/cq_replay/ran{1..5}_replay_results.json`, each with
  `pass == total`, `expected_compared == total`, `mismatches_vs_expected == 0`;
  aggregate 142+128+123+117+114 = 624/624).
- **Independent blind reload: 624/624, 0 mismatch.** An independent reload of
  the released artifacts (TTL + loader + queries + gold) reproduces every
  published answer set with no re-normalization.

---

## 5. Publication status (honest)

- **DOI 10.5281/zenodo.20034872** identifies the **prior** deposited release:
  the SPECTRA ontology (v1.0.0) with the **137-CQ** SpectraCQ v1.0 subset and the
  per-WG body KGs. It does **not** contain the 624-CQ scored benchmark
  described here.
- **Version naming (resolved):** the 624-CQ scored set is labeled
  **SpectraCQ v2.0** (`cqs/spectra_cq_v2.0/`), distinct from the deposited
  137-CQ SpectraCQ v1.0; the release package version is 2.0.0 (see
  `CHANGELOG.md`).
- The 2.0.0 package (624-CQ scored benchmark + evaluation suite) is prepared
  as a **new Zenodo version** under concept DOI **10.5281/zenodo.20034871**;
  its version DOI is minted when the deposit is published. Until publication,
  no DOI should be cited for the 624-CQ benchmark.

---

## Frozen count set (quick reference)

```
nodes              = 966,859
relationships      = 4,908,850
rdf_triples        = 12,931,842
node_labels        = 32
relationship_types = 59
authored_cqs       = 654
released_cqs       = 624
held_cqs           = 30
cypher_queries     = 624
sparql_subset      = 142   (142/142 parity: 80 exact + 62 limit-bound top-k)
models             = 9
conditions         = 3
predictions_scored = 16,848
self_replay        = 624/624
blind_reload       = 624/624
```
