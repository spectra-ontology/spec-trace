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

**Source-fidelity repairs not applied in the numbers above:** the graphs
carry the values before the repair lists of
`validation/source_fidelity_repair_manifest.json`. Applied, those lists
leave the node counts unchanged and change relationships by RAN1 +153, RAN3 -553, RAN4 -426
(total 4,908,024) and RDF triples by RAN1 +153, RAN3 -596, RAN4 -468 (total
12,930,931). `validation/source_fidelity_note.md` states how.

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
graph, plus a row count. Gold-value extraction is automated query execution;
reference-query authorship and column-demand annotations have separate
provenance. This does not independently validate the question's semantics.
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
`contract_disposition` recording annotated contract flags. Disposition 1 means
that no flag is set; under the recorded annotations it bounds the required
column count, not column identity: in **33** of the **241** items with
disposition 1 the one column marked `required` is not the scored answer column.

`cqs/spectra_cq_v2.0/core_answer_gold.jsonl` is the scoring key of Core: for
each of the **560** items, its declared answer column and the gold value set of
that column (**553** from the released reference query, **7** from a
scope-repaired query carried on the same line).
`cqs/spectra_cq_v2.0/splits/contract_exact_241.txt` lists the **241** items with
`contract_disposition` 1. The **64** released questions outside Core are listed,
each with its reason, in `cqs/spectra_cq_v2.0/held/contract_held_out.json`
(560 + 64 = 624); they are distinct from the 30 authored CQs of
`cqs/spectra_cq_v2.0/held/held_cqs.json`.

`cqs/spectra_cq_v2.0/contract_demand_provenance.jsonl` records, for every
returned column of the **624** released CQs (**1,616** columns), whether the
question requires it and what decided that: word-overlap rules between the
column name and the question (**1,339** columns) or a language model
(**277** columns on **232** items).
`cqs/spectra_cq_v2.0/splits/contract_exact_rule_only_149.txt` lists the **149**
legacy items with no language-model verdict.

A Core item enters the annotation-derived 208 when no contract flag is set
and every column marked `required` in `contract_demand_provenance.jsonl` is
the scored answer column; an item may have none marked `required`.
`cqs/spectra_cq_v2.0/splits/contract_exact_asked_208.txt` lists these **208**, and
`cqs/spectra_cq_v2.0/splits/contract_exact_script_fixed_133.txt` the **133** of
them in which every language-model verdict falls on the scored answer column
and no phrase verdict is recorded. The 133's membership is invariant to those
model verdicts with rules, flags and answer column fixed; the rules and flags
can still miss question requirements. The **241** and **149** lists are superseded; **17** of
the **33** items above lie in the **149**.
`python3 cqs/spectra_cq_v2.0/splits/rebuild_contract_splits.py --check`
rebuilds and checks all four lists.

The **132**-item rule-only diagnostic subset is the intersection of the
preserved 149 and 133 lists, with no new membership file. These are annotation
conditions, not human-validated semantic guarantees. The Core scoring key
projects the reference query onto one declared answer column; normalized
value-set scoring ignores other columns, multiplicity and row order. Counts,
relationship roles and ranking can therefore remain ungraded, including
within the 133; `cqs/spectra_cq_v2.0/splits/README.md` gives concrete examples.

`cqs/spectra_cq_v2.0/contract_annotation_diagnostics.json` records a complete
enumeration of unscored returned fields and syntactic query-order/limit signals
over Core and the 133/208, with input hashes and three source-grounded examples.
`cqs/spectra_cq_v2.0/splits/audit_demand_annotations.py --check` checks that
record. These are annotation diagnostics, not semantic error prevalence or
independent practitioner validation; existing data and memberships are preserved.

### 2.4 AI-assisted field-coverage diagnostic

`cqs/spectra_cq_v2.0/field_coverage_review.json` records a fixed protocol and
two mutually isolated Codex AI reviews of all **133** annotation-derived
candidates. Question, reference-query and column inputs were supplied with
predictions, scores, annotation labels and the other review hidden. **67**
items were jointly marked `field_aligned`; their intersection was frozen before
its new subset scoring and is shipped as
`cqs/spectra_cq_v2.0/splits/field_coverage_reviewed_ids.txt`. Mismatch or
ambiguity excluded an item without score-based adjudication; **66** exclusions
do not mean 66 independently confirmed semantic errors. The exact AI model
snapshot was not recorded. This is fallible AI-assisted diagnostic review,
not human or 3GPP expert validation, semantic certification or error prevalence.

The selected cohort has lookup **21**, aggregation **42**, relational **3**,
multihop **1** and **0** declared tuple/mapping items, limiting generalization.
It supplements Core and the 133/208; `score_core.py` retains the
annotation-derived 133 default for compatibility. Questions, reference
queries, gold and original outputs are preserved.
From the repository root, `python3 release_package/cqs/spectra_cq_v2.0/splits/rebuild_field_coverage_subset.py --check`
checks sources, input anchors, stored judgments and their intersection. It
does not repeat the AI review or verify judgment truth.

Review-record SHA256:
`e9ae81f1c3949846ca15627a6b75b8182633a6cf8fe62cb371157022cc212927`.
67-ID-list SHA256:
`404ac91a23db3b439492c940dce7fa4a443302dbb495a85b39b8b434c0cdd2cf`.

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
- **Core and contract-exact scoring.** `paper/baseline/score_core.py` re-scores
  the same prediction files on the annotation-derived **133** (default) or on all **560** Core items
  against `cqs/spectra_cq_v2.0/core_answer_gold.jsonl`, with no network and no
  model call. `--set contract_exact_asked_208` scores the **208** items that
  satisfy the recorded conditions; `--set contract_exact_241` and
  `--set contract_exact_rule_only_149` still select the superseded **241** and
  **149** (section 2.3).
- **Relational arm: 1 run.** claude-opus-4.8 under `sql_grounded`: **624**
  predictions, 0 call errors, in `paper/baseline/relational/runs/`. The model
  writes SQL over SQLite copies of the five graphs, built by
  `paper/baseline/build_relational_db.py`, and is shown
  `paper/baseline/sql_schema_cards.json`. The run is not part of `scores.json`;
  from `paper/baseline/`, `python3 score_core.py --results relational/runs`
  scores it.

The retained original 18 text runs are available, but per-item outputs of the
later rebuilt comparators are absent. The historical 325-item SQL comparison
cohort has no retained identifier list, and the meaning of the paper's
associated `290` label remains unverified. This bundle supports scoring the
retained SQL run on published, explicit subsets; it does not reproduce that
historical cohort or the rebuilt comparator results. See `paper/baseline/README.md`
at the repository root for the precise reproduction scope.

`paper/baseline/analyse_contract_subsets.py` reads these public inputs and the
retained whole-record replays for offline Core/133/208/132 and declared-type,
track, group and composition analyses. It separates answer-column scoring
from full-record S (values sorted within a row), P (column positions) and C
(a gold-oracle common column permutation). P/C still discard row order and
do not validate property roles. Its optional paired bootstrap reselects the
best original 18-arm text comparator within each common item draw; it also
reports a fixed-text comparison. JSON output carries population IDs,
source/input hashes and metric definitions. This path does not reproduce the
unretained rebuilt comparator outputs, historical SQL cohort or original
500,000-replicate paper intervals. See the baseline README for the command
and exact interval protocol.

The recorded [contract_subset_analysis.json](../paper/baseline/results/contract_subset_analysis.json)
contains the actual all-scope run: **30** populations, **52** input/source
hashes, **10,000** paired draws and seed **0**, with the NumPy engine.
SHA256: `c7322b4f0549800bff2c7fcf298501b34eb7ce6cba9380b050b0b87a1dc80aea`.
The CLI also accepts `--ids PATH` for one externally fixed Core identifier
list, records its hash and rejects empty, duplicate or unknown identifiers;
that option overrides the built-in scopes. The retained artifact above uses
the built-in populations.

The supplementary [field_coverage_subset_analysis.json](../paper/baseline/results/field_coverage_subset_analysis.json)
records the actual `--ids` run on the fixed 67-item AI-review intersection,
with **10,000** paired seed-**0** resamples and the same original 18 text arms.
Answer-column pooled F1 is **0.650757**, versus best original answer-column
text F1 **0.074627**; all **9** graph models have positive paired intervals
against per-resample reselected text. Full-record S/P/C pooled F1 is
**0.428063** under each rule, with **9** positive intervals under each;
the text comparator remains answer-column F1. These are selected-cohort
diagnostics, not an expert-validated replacement benchmark.
SHA256: `39f15093b37aead6e2a318bd707e197ca1ef492da2df37aebbd4d99a7beaca1c`.
The baseline README gives a separate-output reproduction command and the
field-review limits; the field judgments are AI-assisted, while re-scoring
executes no model or database query.

The subsequent [question/scoring review](cqs/spectra_cq_v2.0/question_scoring_scope_review.json)
records **133** items reviewed by two fresh isolated Codex AI agents on four
axes: required fields, scope/roles, cardinality/truncation and
ordering/duplicates. Overall compatibility requires all four compatible;
selection is the fixed intersection of the two compatible lists. Review A
has compatible/incompatible/unclear counts **51/40/42**, review B **46/38/49**,
with overall agreement **124/133**. Its **45** IDs are contained in the
preserved 67, frozen at **2026-10-06 22:42:02 UTC** before new subset scoring.
Designers had already seen parent Core/133/208/67 metrics. These AI judgments
are fallible, not human expert validation or complete semantic certification;
the 88 exclusions are not 88 confirmed semantic errors. Composition is
**14 lookup, 30 aggregation, 1 relational, 0 multihop**, with original type
labels **40 scalar_set, 5 ranked_top_k** and no tuple/mapping item. Set scoring
still ignores returned ranks; this selection limits generalization.

The [question_scoring_scope_subset_analysis.json](../paper/baseline/results/question_scoring_scope_subset_analysis.json)
records the actual retained-output `--ids` run on those **45** items,
**52** input/source hashes and **10,000** paired seed-**0** NumPy resamples.
Answer-column pooled F1 is **0.712346**, versus best original answer-column
text F1 **0.049708**; full-record S/P/C pooled F1 is **0.504993** under each
rule. Each comparison has **9/9** positive model-minus-reselected-text
intervals; record rules retain the answer-column text comparator. The
baseline README gives separate-output reproduction commands; the
[membership checker](cqs/spectra_cq_v2.0/splits/rebuild_question_scoring_scope_subset.py)
verifies sources, recorded judgments and the fixed intersection, without
certifying judgment truth or independently proving chronology. All earlier
questions, keys, outputs, subsets and the 133 scorer default remain unchanged.
Model-rank Spearman agreement with Core under the **same scorer** is
**0.850000** for answer column (2/9 ranks changed), **0.583333** for P
(6/9 changed), and **0.600000** for S/C (6/9 each). P compares P45 with
PCore, with claude-opus-4.8 first in both; answer-column rank agreement
does not establish full-record rank stability.

- Review record SHA256: `205b4d050ae997b9e76d60a0795989367e7ee26533f18f16249badb3780016c3`.
- [45-ID file](cqs/spectra_cq_v2.0/splits/question_scoring_scope_reviewed_ids.txt) SHA256: `fe99b088e685e4ab534745a288d6c7dfddc15b2b1eabdd410ab5ef146367d1ac`.
- Recorded analysis SHA256: `c2ab4c9051c2def86875f95e0ee02a704931b3f31e88e475e6872f5f99f4307a`.

The [structured_access_core_analysis.json](../paper/baseline/results/structured_access_core_analysis.json)
and `paper/baseline/analyse_structured_access.py` provide a separate retained
SQL/Cypher comparison for claude-opus-4.8 on all **560** Core IDs and the same
current repaired answer-column key. SQL F1 is **0.373614**, Exact **146/560**,
query OK/error **547/13**; Cypher F1 is **0.351949**, Exact **137/560**,
query OK/error **544/16**. Both have **0** missing or duplicate Core records;
failed queries remain in the 560-item denominator with zero scores.
SQL-minus-Cypher F1 is **0.021665**, paired seed-0/10,000-draw CI
**[-0.001249, 0.044760]**, which includes zero. The artifact carries **13**
input/source hashes and per-item results; its SHA256 is
`86c23ee876209cf4fafa9d5802fa9d2cb796a642c1cd3d5885fbc152ba81edb5`.
It executes no new query, model or database and reconstructs neither the
historical 325/290 comparison nor the unretained SQL database byte snapshot.
Different prompts/languages and one model do not identify a causal
graph-engine benefit; the answer-column comparison is not full question-contract
validation. The baseline README gives the separate-output reproduction command.

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

- **Cross-WG scenario counts on the released graphs: 17 of 18 the same.**
  `tests/reproduce_scenario_counts.py` recounts the 18 counts of
  `validation/cross_wg_use_evidence.json` on the five body-text graphs and
  writes `validation/released_graph_scenario_counts.json`. The RAN3 count of
  change requests on TS 38.300 is 270 on the deployed KG and 1,249 on the
  released graph (1,144 draftCR, 105 pCR). The 25,586 LS instances of the five
  graphs carry 25,586 distinct document numbers. See
  `validation/validation_manifest.md`.

These reload checks compare query-defined outputs. They do not establish
expert-validated natural-language correctness or full question coverage of
the answer-column scoring projection.

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
  The concept DOI locates the newest published deposit. An individual version
  DOI pins the immutable archival bytes and is appropriate for reproducing
  that version. Cite a Git commit as well when using additions that are only
  in the repository: neither DOI identifies the current Git overlay.
- **What is in the deposit vs. what is in this repository.** The archives
  under `dist/` are the snapshots as deposited, kept byte-identical to the
  Zenodo files so their checksums in `dist/SHA256SUMS` verify against the
  record. The Git tree is the living release and runs ahead of the newest
  deposit: `cqs/spectra_cq_v2.0/splits/` and
  `cqs/spectra_cq_v2.0/answer_contract.jsonl` were added after the v2.0.0
  archive was built and are present here but not inside that archive. Both
  are plain text; the identifier lists under `splits/` rebuild with no
  database and no network from files in `cqs/spectra_cq_v2.0/`, and
  `answer_contract.jsonl` ships as data.
  `cqs/spectra_cq_v2.0/core_answer_gold.jsonl`,
  `cqs/spectra_cq_v2.0/held/contract_held_out.json` and
  `cqs/spectra_cq_v2.0/splits/contract_exact_241.txt` were added after those two
  and are likewise present here but not inside that archive.
  `cqs/spectra_cq_v2.0/contract_demand_provenance.jsonl` and
  `cqs/spectra_cq_v2.0/splits/contract_exact_rule_only_149.txt` came after those
  and are likewise present here but not inside that archive.
  `cqs/spectra_cq_v2.0/splits/contract_exact_asked_208.txt`,
  `cqs/spectra_cq_v2.0/splits/contract_exact_script_fixed_133.txt` and
  `cqs/spectra_cq_v2.0/splits/rebuild_contract_splits.py` came after those
  and are likewise present here but not inside that archive.
  The annotation diagnostic and its generating script, and
  `paper/baseline/analyse_contract_subsets.py` with its recorded analysis,
  are likewise Git additions outside the frozen 2.0.0 archives. They retain
  the existing questions, annotations, gold, split lists and original outputs.
  The AI-assisted field-review record, fixed 67-item list, intersection
  checker and recorded field-coverage analysis are also Git-only additions;
  the deposited archival bytes are unchanged.
  The full-Core retained SQL/Cypher analysis code and result are also Git-only
  additions and do not reconstruct or replace the frozen historical SQL comparison.

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
