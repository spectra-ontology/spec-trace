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

**Known defect counted in the numbers above:** 634 of the 4,935
`Contact` nodes are duplicates of a contact already present (RAN3 181,
RAN4 291, RAN5 162; RAN1 and RAN2 zero), so the graphs hold 4,301
distinct contacts and the node total is inflated by 634 (0.066%). The
cause, the per-WG breakdown, and the effect on the two benchmark items
that count `Contact` nodes are documented in `kg/per_wg/README.md`.

Regenerate:

```
python3 release_package/pipeline/count_triples.py               # -> triple_counts.json
```

`graph_counts.json` is written by the authors' replay driver, which is
not part of this package. It uses released artifacts only — it reloads
`kg/per_wg/RAN{1..5}-body.ttl` into a scratch store with the shipped
`pipeline/load_released_kg.py` and reads the live counts back — so the
shipped `tests/verify_benchmark.py --full` reproduces the same numbers
from the same inputs, in the per-WG loader reports it writes.

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
shared `LIMIT`). 0 errors, 0 mismatches. This is *cardinality* parity: it
establishes that the two engines return the same number of rows, not that they
return the same rows.

Regenerate:

```
python3 release_package/pipeline/validate_sparql_parity.py   # -> sparql_parity_results.json
```

**Cell-level comparison (stronger, separate evidence).** The paper reports a
second comparison that puts the full result sets side by side cell by cell
instead of counting rows: **138** of the 142 return the same multiset of rows
and **4** differ, each in a single column. The harness that computes it ships as
`paper/baseline/sparql_row_equivalence.py` (at the repository root, beside
`release_package/`); the paper's appendix states the normalization ladder it
applies, the four disagreements by name, the mutation-sensitivity control and
the RDFS-closure control.

Unlike every other number in this manifest, the recorded JSON output of that
harness is **not** included in this snapshot, so the 138/4 pair is not
independently checkable from the files here — it is reproducible instead of
shipped. Reproducing it needs the SPARQL side (present: the released
`kg/per_wg/RAN1-body.ttl`, the 142 `.rq` files and `ontology/spectra.ttl`, all
read in-process by rdflib, no triplestore server) **and** the Cypher side from a
live Neo4j holding the RAN1 graph, which this package does not contain. Load it
with the shipped `pipeline/load_released_kg.py` first, then:

```
python3 paper/baseline/sparql_row_equivalence.py --bolt bolt://localhost:7687
```

The classification of the 482 untranslated questions that the same appendix
reports needs neither engine and runs directly from the shipped benchmark:

```
python3 paper/baseline/sparql_row_equivalence.py --classify-untranslated-only
```

### 2.2 Splits

Four canonical splits over the 624-question key ship as identifier lists under
`cqs/spectra_cq_v2.0/splits/`: a standard 60/20/20 split stratified over the 20
(working group x track) strata (**374/125/125**), a template-disjoint split that
moves whole leakage groups so no query shape and no question string spans a
boundary (**375/125/124**), a cross-group split holding RAN5 out in full
(**382/128/114**, all 114 RAN5 questions in test), and an evaluation-only
challenge subset of **33** questions satisfying at least four of five per-row
difficulty conditions.

`splits/composition.json` carries the per-track and per-group composition of
every part, the stratification deviation, the leakage audit and the challenge
conditions; `splits/track_assignment.json` carries the stratification axis
(lookup 213, aggregation 195, relational 164, multihop 52). Membership is a
salted SHA-256 function of the question identifier, not a random draw, so a
rebuild reproduces the files byte for byte.

Regenerate and verify (no database, no network):

```
python3 release_package/cqs/spectra_cq_v2.0/splits/rebuild_splits.py
```

### 2.3 Answer contract

`cqs/spectra_cq_v2.0/answer_contract.jsonl` carries one line per SpectraCQ-Core
item (a `_header` line plus **560** items): the graded `answer_type` and
`answer_columns`, the `ordering_key` and `cardinality` governing the reference
query's final `RETURN` (null where none is imposed), and a
`contract_disposition` recording what would have to change for the item to hold
exactly as asked.

---

## 3. Evaluation — baseline suite

Evidence: `paper/baseline/results/scores.json` (at the repository root, beside
`release_package/`), together with the per-condition prediction files under
`paper/baseline/results/`.

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
- The 2.0.0 package (624-CQ scored benchmark + evaluation suite) is published
  as a **new Zenodo version** under concept DOI **10.5281/zenodo.20034871**.
  Cite the concept DOI: it always resolves to the newest published deposit,
  which is the one carrying the 624-CQ benchmark. A citation pinned to an
  individual version DOI keeps pointing at superseded files once a further
  version is deposited.
- **What is in the deposit vs. what is in this repository.** The archives
  under `dist/` are the snapshots as deposited, kept byte-identical to the
  Zenodo files so their checksums in `dist/SHA256SUMS` verify against the
  record. The Git tree is the living release and runs ahead of the newest
  deposit: `cqs/spectra_cq_v2.0/splits/` and
  `cqs/spectra_cq_v2.0/answer_contract.jsonl` were added after the v2.0.0
  archive was built and are present here but not inside that archive. Both
  are plain text and rebuild with no database and no network.

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
sparql_subset      = 142   (142/142 cardinality parity: 80 exact + 62 limit-bound top-k)
sparql_cell_level  = 138/4 (same row multiset / single-column difference;
                            reproducible, output JSON not shipped)
core_items         = 560   (answer_contract.jsonl)
splits             = 374/125/125, 375/125/124, 382/128/114, challenge 33
models             = 9
conditions         = 3
predictions_scored = 16,848
self_replay        = 624/624
blind_reload       = 624/624
```
