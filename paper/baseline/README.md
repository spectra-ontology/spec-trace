# SpectraCQ Baseline Harness and Recorded Runs

For current 31 / historical 45 / separate 36 / Core 560 scope relationships,
see the [evaluation scope guide](../../release_package/cqs/contract_repair_v1/README_evaluation_scopes.md).

For explicit named-record task variants and a new matched single-pass/two-round
text comparison, use the [contract companion](../../release_package/cqs/contract_repair_v1/README.md).
It records a separate fixed 36-task measurement with complete-record F1 and
exact-output metrics for all three arms. The original results below remain
historical analyses of the released questions and their original keys.


For comparisons on the original unchanged questions, start with the
[31-item source-aligned retained-output diagnostic](../../release_package/cqs/contract_repair_v1/original_source_aligned/README.md)
before interpreting full-Core or historical annotation-subset scores. Its admission
rule was fixed before reading retained predictions: both source-evidenced AI audits
must judge the full original scoring contract aligned, native reference execution
must be complete, and the declared released/V1 answer-column sets must agree with
source outputs. The fixed cohort contains 11 lookup, 13 aggregation and 7 relational
items, with no multihop item. Native completion concerns the saved reference query;
its original LIMIT clauses and source gaps remain. It re-scores the unchanged 27 original runs of nine
models with the legacy canonical-string value-set scorer, without reconstructing
named records, roles, types, order or multiplicity. V1 is primary; V2 sensitivity
uses the whole identical cohort. This does not recover the paper's default Core/V2
headline or replace the strict 36-variant comparison above.

From the repository root, reproduce the recorded diagnostic without model,
database or retrieval calls and without writing a report:

```bash
python3 -I -B release_package/cqs/contract_repair_v1/original_source_aligned/score_source_aligned_retained_portable_v1.py \
  --bundle release_package/cqs/contract_repair_v1/original_source_aligned \
  --public-root . \
  --expected-manifest-sha256 ef37ec7f075c7d51d87406d20e6c55f050213ef9942eab6cf53cb27277f29813
```

The [all-560 audit dispositions](../../release_package/cqs/contract_repair_v1/source_alignment_audit_v1/semantic_alignment_audit_report_v1.json)
and [345-file audit manifest](../../release_package/cqs/contract_repair_v1/source_alignment_audit_v1/portable_export_manifest_v1.json)
preserve every original item and all 112 attempts. Both audit receipts were usable
for 480 items; 80 retain one or both unavailable raters and are excluded from cohort
admission, without replacement or performance-based selection. Usable receipts do
not imply alignment. Three admitted items retain differences in coarse role aliases;
their diagnostics stay visible and the fixed 31-item cohort is not reselected.
These are fallible AI judgments, not human/domain-expert validation, a representative
sample or a repair of all Core questions. Gold is nonempty; missing-information
abstention remains untested. Historical graph/text evidence access and source cutoffs
are unequal or unverified. The [offline audit verifier and resource appendix](../../release_package/cqs/contract_repair_v1/source_alignment_audit_resources_v1/README.md)
and its [verifier script](../../release_package/cqs/contract_repair_v1/source_alignment_audit_resources_v1/verify_semantic_alignment_audit_export_v1.py)
explain the public checks and the retained private-capture hash commitments.

Complete harness and per-question outputs for the three-condition baseline reported in the
paper: closed-book, RAG over the released text collections, and knowledge-graph-grounded
query generation. From the recorded runs in this directory, `score_core.py --set core`
recomputes offline the Exact and Set F1 values that the paper's baseline table prints for
nine models under three conditions and for its pooled row. Not every printed value is
recomputed here as printed; the exceptions include the table's 95% interval column
(500,000 bootstrap replicates), its Exec column, its full-record rows and the whiskers of
the paper's results figure.

The original 18 closed-book/RAG runs are retained. Per-item outputs for the
later rebuilt text comparators are not retained here, so their reported
results cannot be regenerated from this bundle. The historical 325-item SQL
comparison cohort was not retained as an identifier list; neither that
cohort nor the meaning of the paper's associated `290` label has been
verified from the available artifacts. The recorded 624-row SQL run can be
scored on explicit, published subsets, without reconstructing that historical
comparison. These provenance gaps remain open.
The full-Core SQL/Cypher comparison below is a new retained-output analysis
on the explicit 560-item key; it does not recover that historical comparison.

`analyse_contract_subsets.py` provides an offline path for the later
annotation-subset, declared-type and column-position sensitivity analyses,
including paired intervals against a reselected best original text run.
Its inputs are the public annotations, original prediction logs and retained
full-record replay files. It does not rerun a model or a database query.

## Layout

```
bench_common.py           shared infra: env, OpenRouter chat/embeddings, Qdrant search, Neo4j exec
run_baseline.py           campaign runner (dry-run by default; --confirm to call APIs)
score.py                  deterministic re-scorer (no network, no LLM)
score_core.py             re-scores the recorded runs on SpectraCQ-Core (560) or a
                          annotation-derived subset (133, the default); no network, no model call
score_full_record.py      scores the kg_grounded runs on SpectraCQ-Core by whole
                          returned records, from the replay files below; its replay
                          step needs a Neo4j holding the released graph
analyse_contract_subsets.py offline subset/type/column-position sensitivity and paired
                          bootstrap versus the original 18 text arms; no model/query execution
analyse_structured_access.py offline retained SQL/Cypher comparison on all Core560,
                          using the same repaired answer-column key and paired intervals
protocol_bounds.py        recomputes the paper's protocol-level bounds from recorded
                          artifacts (retrieval coverage at top-k, KG failure accounting,
                          gold cardinality); no network, no LLM
make_results_figure.py    draws a grouped bar chart of the Set F1 values in
                          results/scores.json, without error bars
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

Run the scoring commands below from `paper/baseline/`. Starting at the repository
root, change directory first:

```bash
cd paper/baseline
```

`score.py` is fully deterministic and offline. Gold and prediction values are normalized
(canonicalization, whitespace collapse, casefold) and compared as sets:

- `exact` — strict normalized value-set equality; for kg_grounded this compares
  the executed query's first-column values with the reference answer set;
- set-level `precision`, `recall`, `f1` — partial credit for multi-value answers;
- all metrics macro-averaged over questions.

Re-score everything from the recorded outputs:

```bash
gunzip -k results/*/*/all.jsonl.gz
python3 score.py          # rewrites results/scores.json
```

`make_results_figure.py` then draws a grouped bar chart of the Set F1 values in
`scores.json`, without the whiskers of the paper's results figure.

### SpectraCQ-Core and the annotation-derived contract subsets

`score.py` scores the released key: the first returned column of all 624 questions.
`score_core.py` scores the same recorded outputs on the 560 SpectraCQ-Core items against
`release_package/cqs/spectra_cq_v2.0/core_answer_gold.jsonl`. It reads the `.gz` logs
directly and writes nothing unless `--json` is given. The gold is the reference query's
declared answer-column projection; the KG predictions retained in the original logs are
the first returned column of the model's query. The scorer compares these value sets; it
does not verify that the model selected the requested property or relationship role.

```bash
python3 score_core.py --set contract_exact_script_fixed_133  # historical annotation diagnostic
python3 score_core.py --set contract_exact_asked_208   # annotation-derived 208
python3 score_core.py --set core         # all 560 Core items
python3 score_core.py --set contract_exact_241   # superseded: the 241 items with contract_disposition 1
python3 score_core.py --set contract_exact_rule_only_149   # superseded: the 149 of the 241 with no language-model verdict
python3 score_core.py --set core --gold released   # all 560 Core items, but the 7 scope-repaired items keep the released query's values
```

Every run is scored over the whole set, so a question a run never answered scores zero.

A Core item enters the annotation-derived 208 when no contract flag is set in
`answer_contract.jsonl` and every column marked `required` in
`contract_demand_provenance.jsonl` (both files are under `release_package/cqs/spectra_cq_v2.0/`)
is the scored answer column. An item may have no column marked `required`. The 133 are
those of the 208 in which every column verdict
made by a language model falls on the scored answer column and no phrase verdict is
recorded. Their membership is invariant to changes in those model verdicts with the rule
verdicts, flags and answer column fixed. The 241 and 149 are superseded: disposition 1
bounds the recorded demand count, not column identity, and in 33 of the 241 the one column
marked `required` is not the scored answer column. They stay selectable for historical
reproduction. The 132-item rule-only diagnostic subset is `149 ∩ 133`, with no new
membership file. These conditions do not independently validate the questions or certify
that count, routing and ranking requirements are graded. Normalized set scoring ignores
value multiplicity and row order, including `ORDER BY` requirements. See
`release_package/cqs/spectra_cq_v2.0/splits/README.md` for composition and concrete examples.

### Full-record scoring

`score_core.py` scores each Core item on one column. `score_full_record.py` scores the
kg_grounded runs on whole returned records: a record is the tuple of its normalized values
sorted within the row, so a value is not tied to the column that returned it, and the
predicted and gold record sets are compared, so column names, column order, row order and
duplicate rows do not matter. Exact is 1 when the two sets are equal;
precision, recall and F1 are those of their overlap. Each model is averaged over all 560
Core items, and an item whose query is missing or does not execute scores zero. The gold
records are the rows in `release_package/cqs/spectra_cq_v2.0/gold/{WG}_gold.json`; for the
7 scope-repaired items they are the rows of their `repaired_cypher`, and `--gold released`
keeps the released rows for them.

The run logs keep only the first returned column of each query, so the records come from
executing again, on the released graph of each working group, all 5,520
queries the kg_grounded runs recorded, together with the released and repaired reference
queries. The five files in `results/_full_record/` hold that replay, so scoring needs no
database. These are replayed query outputs, not the original run's whole returned rows.
The original logs retain a sorted value set, which loses original row order; the replay
rows retain the ordering of this later execution:

```bash
python3 score_full_record.py score                   # repaired rows for the 7 items (default)
python3 score_full_record.py score --gold released   # released rows for the 7 items
python3 score_full_record.py score --set contract_exact_script_fixed_133 --ci   # annotation-derived 133, with intervals
python3 score_full_record.py score --answer-type tuple_set,mapping  # Core items whose answer is a tuple set or a mapping
```

`--set` takes the subset names of `score_core.py`, and `--answer-type` keeps the items whose
`answer_type` in `answer_contract.jsonl` is one of the listed types; both change which items
are averaged, not how an item is scored. `--ci` adds a 95% interval to each model's F1 from a
paired item bootstrap: 10,000 resamples of the selected items drawn with `random.Random(0)`,
one resample shared by every model, the interval running from the 251st to the 9,750th
sorted resample mean. A model pair counts as separated when the interval of its difference
excludes zero. The integrity counts below always cover all 560 Core items.

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
for example with `python3 ../../release_package/tests/verify_benchmark.py --full --wg RAN1`
(plus `--bolt`, `--user` and `--password`), then run
`python3 score_full_record.py replay --wg RAN1 --ttl ../../release_package/kg/per_wg/RAN1-body.ttl`
with the same connection options; `--ttl` records the loaded file in the header.

### Offline subset and scoring-sensitivity analysis

From this directory:

```bash
python3 analyse_contract_subsets.py --scope headline
python3 analyse_contract_subsets.py --scope all --ci --n-boot 10000 --seed 0 --json results/contract_subset_analysis.recomputed.json
python3 -m unittest discover -s tests -p 'test_analyse_contract_subsets.py'
```

The recorded [contract_subset_analysis.json](results/contract_subset_analysis.json)
contains all 30 populations from `--scope all --ci --n-boot 10000 --seed 0`,
using the NumPy engine. It records 52 input/source hashes and each population's
identifiers. Its SHA256 is
`c7322b4f0549800bff2c7fcf298501b34eb7ce6cba9380b050b0b87a1dc80aea`.
The recomputation command writes a separate result file, leaving this record
available for comparison.

The default `headline` scope reports Core560 and the annotation-derived
133, 208 and rule-only132 (`149 ∩ 133`). `typed` adds the 141 declared
tuple/mapping items and their separate type populations. `tracks` and
`groups` report the 133/208 by track and working group. `composition` reports
surface query features within the 133; `all` combines these scopes. No
membership, gold or original output is changed. The JSON records each
population's identifiers, input/source SHA256 values and metric definitions.

`--ids PATH` instead analyzes one externally fixed list of Core identifiers as
`external_subset`, overriding `--scope`. Fix membership before inspecting the
scores. Identifiers are sorted internally; empty lists, duplicates and unknown
identifiers are rejected. The output records the ID-file hash and checks that
it did not change during analysis. For example, the existing 133 list can be
passed explicitly without creating a new subset:

```bash
python3 analyse_contract_subsets.py --ids ../../release_package/cqs/spectra_cq_v2.0/splits/contract_exact_script_fixed_133.txt --ci --json results/fixed_subset_analysis.json
```

Seven graph scoring variants are reported separately:

| Variant | Comparison |
|---|---|
| `answer_column` | Original retained prediction value set against the declared Core answer-column gold |
| `full_record_S` | Replay row sets, sorting normalized values within each row |
| `full_record_P` | Replay row sets with normalized values in `RETURN` column positions |
| `full_record_C` | Maximum row-set overlap over one common column permutation per item/model, using gold as an oracle; differing widths fall back to P |
| `declared_type_S/P/C` | Corresponding record rule on declared tuple/mapping items, answer-column scoring on other types |

P compares positions, not property names; C is an oracle alignment sensitivity
measure. Neither validates the requested property or relationship role. All
record variants ignore outer row order, ranking and duplicate-row multiplicity.
An observed C=S equality is a result for these retained outputs, not a general
integrity condition. Text always uses the original 18 closed-book/RAG
answer-column runs. Comparisons of a record variant with that text score use
different answer representations; they do not provide a text full-record baseline.

With `--ci`, the same item resample is shared by every model, graph scoring
variant and text run. The output includes a fixed best-text comparison and a
comparison that reselects the best of the 18 text runs within each resample.
The default uses 10,000 draws from `random.Random(0)`; sorted endpoints at
indices 250 and 9,749 are rounded to six decimals, then a lower endpoint >0
counts as above text and an upper endpoint <0 as below. These are individual
item-bootstrap intervals with no adjustment for template/cluster dependence
or multiple comparisons. `--bootstrap-engine python` uses the standard library;
`auto` uses NumPy when available to accelerate the same item draws. The
historical 500,000-replicate paper intervals and absent rebuilt text runs
remain outside this analysis's reproduction scope.

The recorded artifact gives nine models above the reselected original-text
bar for each of the 133, 208 and 132 under answer-column and full-record
S/P/C scoring. On the 141 declared tuple/mapping items, full-record S/P/C
give 6/5/6 models above that bar. These are findings for the retained outputs
under the stated comparison, and do not validate the semantic completeness
of the annotation-derived subsets.

### AI-assisted field-coverage diagnostic

The [field-coverage review](../../release_package/cqs/spectra_cq_v2.0/field_coverage_review.json)
stores two isolated Codex AI reviews of every item in the annotation-derived
133. Their supplied inputs hid predictions and item/aggregate scores while
they compared each question's requested fields, counts, mappings, order and
multiplicity with the reference query, its evident scope/caps and the
declared answer-column set score. The 67-item intersection of both
`field_aligned` judgments was frozen
before it was re-scored; mismatch or ambiguity excluded an item, without
score-based adjudication. The [subset README](../../release_package/cqs/spectra_cq_v2.0/splits/README.md)
gives the protocol, composition and limits. This is AI-assisted diagnostic
review, not human or 3GPP expert validation; the exact model snapshot was
not recorded, and the excluded 66 are not confirmed semantic-error counts.

From this directory, check the fixed list and re-score the retained outputs:

```bash
python3 ../../release_package/cqs/spectra_cq_v2.0/splits/rebuild_field_coverage_subset.py --check
python3 analyse_contract_subsets.py --ids ../../release_package/cqs/spectra_cq_v2.0/splits/field_coverage_reviewed_ids.txt --ci --n-boot 10000 --seed 0 --json results/field_coverage_subset_analysis.recomputed.json
```

The first command checks source/input anchors, recorded judgments and their
intersection; it does not repeat the AI review or establish judgment truth.
The second performs offline scoring and bootstrap resampling, with no new
model or query execution. The field judgments themselves were AI-assisted.
The [recorded field_coverage_subset_analysis.json](results/field_coverage_subset_analysis.json)
contains the fixed 67 IDs, their input hash and 10,000 paired seed-0 resamples.

| Scoring rule | Pooled graph F1 | Best original answer-column text F1 | Models above reselected text, paired CI |
|---|---:|---:|---:|
| Answer column | 0.650757 | 0.074627 | 9/9 |
| Full record S/P/C (same F1 on this cohort) | 0.428063 | 0.074627 | 9/9 under each rule |

Pooled F1 here averages the unrounded model/item scores. The answer-column
model-rank correlation with Core under that same rule is Spearman
0.833333. The record comparison retains the answer-column text comparator,
as defined above. All 67 are outside the declared tuple/mapping types; its
21 lookup and 42 aggregation items leave only 3 relational and 1 multihop
item. This selected-cohort evidence therefore does not establish broad
multi-field or track performance. Selection for value-set field coverage
also makes this cohort unrepresentative of Core. It is supplementary to Core and the
133/208, and `score_core.py` keeps the annotation-derived 133 as its
compatibility default. No question, gold value or original output changed.

### Four-axis question/scoring follow-up

The subsequent [question/scoring review](../../release_package/cqs/spectra_cq_v2.0/question_scoring_scope_review.json)
stores two fresh isolated Codex AI reviews of all 133 original candidates,
with separate required-field, scope/role, cardinality/truncation and
ordering/duplicate judgments. Overall compatibility requires all four axes
compatible; an incompatible axis excludes the item, as does remaining
uncertainty. The joint 45-item list was recorded as frozen at
2026-10-06 22:42:02 UTC before its new scores. It is a subset of the
earlier 67; that earlier diagnostic and its results above remain available.

Reviewers saw the fixed protocol and question/query/column input, with
predictions, scores, earlier judgments and demand labels hidden. The
designers had already seen parent Core/133/208/67 results. This is a
subsequent AI-assisted diagnostic, with no human or 3GPP expert validation
or full semantic certification. The exact model snapshot was not recorded;
the 88 exclusions are not a count of confirmed semantic errors. The
[subset README](../../release_package/cqs/spectra_cq_v2.0/splits/README.md)
describes the fixed rule, agreement, composition and source/selection checks.

From this directory:

```bash
python3 ../../release_package/cqs/spectra_cq_v2.0/splits/rebuild_question_scoring_scope_subset.py --check
python3 -m unittest discover -s ../../release_package/cqs/spectra_cq_v2.0/splits -p 'test_rebuild_question_scoring_scope_subset.py'
python3 analyse_contract_subsets.py --ids ../../release_package/cqs/spectra_cq_v2.0/splits/question_scoring_scope_reviewed_ids.txt --ci --n-boot 10000 --seed 0 --json results/question_scoring_scope_subset_analysis.recomputed.json
```

The checker verifies pinned source/input/protocol hashes, stored raw reviews,
literal anchors, the four-axis rule and exact IDs; it does not repeat AI
judgments or establish their truth. The scoring command re-evaluates retained
outputs, with no new model or query execution, and writes a separate artifact.
The judgments themselves were AI-assisted. The pinned
[question_scoring_scope_subset_analysis.json](results/question_scoring_scope_subset_analysis.json)
records 45 IDs, their input hash, the same 52 input/source hashes and
10,000 paired seed-0 resamples with best-text reselection over the original
18 arms.

| Scoring rule | Pooled graph F1 | Best original answer-column text F1 | Models above reselected text, paired CI |
|---|---:|---:|---:|
| Answer column | 0.712346 | 0.049708 | 9/9 |
| Full record S/P/C (same F1 on this cohort) | 0.504993 | 0.049708 | 9/9 under each rule |

Model-rank agreement compares the 45 with Core under the **same scoring
metric** in each row:

| Metric compared with itself on Core | Spearman correlation | Models changing rank |
|---|---:|---:|
| Answer column | 0.850000 | 2/9 |
| Full record P | 0.583333 | 6/9 |
| Full record S / C | 0.600000 under each | 6/9 under each |

The P comparison is P45 versus PCore; claude-opus-4.8 stays first. The
answer-column rank result does not establish full-record rank stability.

The smallest paired lower bounds across graph models are 0.320000 for
answer-column scoring and 0.195556 for each record rule. Record scoring
still uses the answer-column text comparator; P checks tuple positions,
not property names, and all record rules discard row order and multiplicity.
The 45 contain 14 lookup, 30 aggregation, 1 relational and 0 multihop items,
with no declared tuple/mapping item. Original type labels are 40 `scalar_set`
and 5 `ranked_top_k`; this does not establish that returned ranks are correct.
This composition and source-based selection limit generalization to richer
answers and other tracks. The result supplements Core, the 133/208 and the
preserved 67; it does not replace them or change the 133-item compatibility
default. No question, reference query, key, original prediction or existing
subset was changed.

## Relational (NL-to-SQL) arm

A fourth condition, `sql_grounded`, asks the model to answer in SQL over SQLite copies of
the same graphs, providing an alternative access representation.
`build_relational_db.py` builds `relational/{WG}.sqlite` from each
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
python3 score_core.py --results relational/runs --set contract_exact_script_fixed_133  # historical annotation diagnostic
python3 score_core.py --results relational/runs --set core    # all 560 Core items
```

Rebuilding the SQLite files needs the `neo4j` Python driver, `NEO4J_PASSWORD` and the Neo4j
graphs at ports 7687-7691, as `kg_grounded` execution does (below). The five files are not
tracked (1.48 GB in the recorded build). A rebuild or `--verify-only` also writes
`relational/manifest.json` with per-table row counts against the graph, likewise not
tracked. The loader prints `parity=False` for a group whose graph differs from
`schema_cards.json`; `--cards-only` rewrites `sql_schema_cards.json` from the live graphs.

### Retained SQL/Cypher comparison on all Core560

`analyse_structured_access.py` compares the retained `sql_grounded` and
`kg_grounded` runs of claude-opus-4.8 on the same current repaired Core
answer-column key, including its seven scope repairs. All 560 fixed items
enter both arms; failed or missing predictions score zero. The actual runs
have no missing or duplicate Core records. This re-scores stored predictions,
without executing a query, building a database or calling a model.

From this directory:

```bash
python3 analyse_structured_access.py --ci --n-boot 10000 --seed 0 --bootstrap-engine python --json results/structured_access_core_analysis.recomputed.json
python3 -m unittest discover -s tests -p 'test_analyse_structured_access.py'
```

The recorded [structured_access_core_analysis.json](results/structured_access_core_analysis.json)
contains all 560 identifiers, per-item scores/statuses and 13 input/source
hashes. The command writes a separate result for comparison.

| Retained arm | Answer-column F1 | Exact matches | Query OK | Query errors |
|---|---:|---:|---:|---:|
| SQL | 0.373614 | 146/560 | 547 | 13 |
| Cypher | 0.351949 | 137/560 | 544 | 16 |

SQL-minus-Cypher F1 is 0.021665. Its paired item-bootstrap 95% interval is
[-0.001249, 0.044760], using 10,000 common seed-0 draws and six-decimal
endpoints; it includes zero and does not separate the arms under this
protocol. The denominator remains 560, including all query errors. Status
decompositions in the artifact are descriptive and do not select the headline
cohort. The item intervals do not adjust for schema/template clusters.

This is one model's recorded-run comparison: languages, prompts and queries
differ, so it does not identify a causal graph-engine benefit. The recorded
SQL database byte snapshot is not retained; loader/schema-card hashes give
provenance without reconstructing it. This analysis also does not recover the
historical 325-item cohort or `290` label, or validate the full question
contract: scoring compares normalized answer-column sets, ignoring other
fields, whole records, ranking and multiplicity.

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
