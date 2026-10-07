# SpectraCQ v2.0 — Scored Competency-Question Benchmark for the SPECTRA KG

SpectraCQ packages the competency questions (CQs) authored to design and
validate the SPECTRA ontology across all five 3GPP RAN working groups, now
released as a **scored benchmark**: each released CQ pairs a natural-language
question with an executable Cypher reference query and a **deterministic gold
answer set** obtained by executing that query against the released per-WG
knowledge graphs. Gold-value extraction is automated query execution; the
reference queries and the separate column-demand annotations have their own
provenance. Query replay is not independent semantic validation of a question.

Canonical counts for every number below: `../../MANIFEST.md`.

## Benchmark composition

| WG | Authored | Released (scored) | Held-out |
|----|---------:|------------------:|---------:|
| RAN1 | 145 | 142 | 3 |
| RAN2 | 132 | 128 | 4 |
| RAN3 | 129 | 123 | 6 |
| RAN4 | 125 | 117 | 8 |
| RAN5 | 123 | 114 | 9 |
| **Total** | **654** | **624** | **30** |

Released CQs by design phase:

| Phase | Domain | Released CQs |
|-------|---------------------|-------------:|
| P1 | TDoc metadata | 123 |
| P2 | Meeting resolutions | 112 |
| P3 | TS structure | 233 |
| P4 | CR documents | 75 |
| P5 | Technical Reports | 81 |
| **Total** | | **624** |

The 30 held-out CQs are those whose gold answer against the current graph is
empty or uniformly zero/false; they are excluded from scoring to avoid
degenerate set-comparison and shipped under `held/` with their Cypher and
status.

## Gold answer definition

Each released CQ's gold is the **set of values in the first RETURN column**
obtained by executing its reference Cypher against the released graph, plus a
row count. The original reference queries retain their released ordering
and `LIMIT` clauses. Stored answer-set self-replay does not certify stable
whole-record ordering: equal sort keys at a cutoff and unordered `collect`
can change which richer records are returned. Reproducibility evidence
(scratch-reload self-replay, 624/624 primary-value-set gold match) lives at
`../../validation/cq_replay/ran{1..5}_replay_results.json`.

For explicit named records, use the separate [contract sidecar](../contract_repair_v1/README_contract_audit.md).
It provides a typed scorer and source-defined task variants with declared
collection semantics and deterministic ranking rules. Original questions,
queries, gold, splits and recorded scores remain available; this addition
does not certify or replace all 624 original questions.

## Distribution

- `questions.json` — 624 released CQ entries: `{id, wg, phase, category,
  question_en, schema_area, cypher_file, gold_file, gold}`, where `gold`
  carries the answer-set summary (`status`, `row_count`, `columns`,
  `primary_column`, preview of primary values).
- `benchmark.jsonl` — the scored benchmark, one JSON object per line
  (624 rows): question + gold answer set + row count.
- `answer_contract.jsonl` — one line per SpectraCQ-Core item (a `_header`
  line plus 560 items): the graded `answer_type` and `answer_columns`, the
  `ordering_key` and `cardinality` read from the clauses that govern the
  reference query's final `RETURN` (null where none is imposed), and a
  `contract_disposition` recording the annotated contract flags. Disposition
  1 means that no flag is set. Under the recorded column-demand annotations,
  this bounds the number of required columns, not their identity: in 33 of
  the 241 items with disposition 1 the column marked `required` is not the
  scored answer column. The annotation-derived 208-item subset corrects
  that recorded identity mismatch; it is not a semantic validation of each
  question's full requirements.
- `core_answer_gold.jsonl`: the scoring key of SpectraCQ-Core (a `_header`
  line plus 560 items): each item's declared answer column
  (`answer_columns[0]` of `answer_contract.jsonl`) and the gold value set of
  that column. For 553 items the set comes from the released reference
  query. For the other 7, whose reference query restricts a property to a
  literal list of values the question does not all state, it comes from the
  same query with that restriction replaced by `true`; the line carries that
  query as `repaired_cypher` and keeps the released query's values as
  `gold_values_released_query`. Scored by `paper/baseline/score_core.py` at
  the repository root.
- `contract_demand_provenance.jsonl`: one line per released CQ (a `_header`
  line plus 624 items) with one verdict per returned column: whether the
  question requires that column (`required`, `not_required` or
  `undecidable`), the method that decided it, and the words it rests on.
  Word-overlap rules between the column name and the question decide
  1,339 of the 1,616 columns. A language model decides the other 277,
  on 232 items: columns after the first that the rules leave
  undecidable (275), and 2 columns where its verdict replaced a rule
  verdict. The header defines every method.
- `splits/` — the four canonical splits as identifier lists, with their
  per-track and per-group composition, the leakage audit, and a
  deterministic rebuild script. See `splits/README.md`.
- `splits/contract_exact_script_fixed_133.txt`: the 133 items of the
  annotation-derived 208 in which every language-model column verdict falls
  on the scored answer column and no phrase verdict is recorded. Membership
  is invariant to those model verdicts with rule verdicts, flags and answer
  column fixed. One identifier per line. The default set of
  `paper/baseline/score_core.py` at the repository root.
- `splits/contract_exact_asked_208.txt`: the 208 Core items with no contract
  flag set and every column marked `required` in
  `contract_demand_provenance.jsonl` equal to the scored answer column
  `answer_columns[0]`; an item may have none marked `required`. One identifier
  per line. These conditions do not certify question-level semantic validity.
- `splits/contract_exact_241.txt`: superseded. The 241 Core items whose
  `contract_disposition` is 1, that is, with no contract flag set. In 33 of
  them the one column marked `required` is not the scored answer column.
  Kept so that earlier scores can be reproduced.
- `splits/contract_exact_rule_only_149.txt`: superseded. The 149 items of
  `splits/contract_exact_241.txt` with no column or phrase verdict made by a
  language model (`method` in `contract_demand_provenance.jsonl`); 17 of the
  33 above are among them. Kept so that earlier scores can be reproduced.
- `splits/rebuild_contract_splits.py`: rebuilds the four lists above from
  `answer_contract.jsonl`, `contract_demand_provenance.jsonl` and
  `core_answer_gold.jsonl` and checks them byte for byte. All four are
  evaluation subsets of Core, not splits; see `splits/README.md`.
- `field_coverage_review.json`: a fixed protocol and two stored AI-assisted
  field-coverage judgments for every item of the annotation-derived 133,
  with source hashes, question/query anchors and limitations.
- `splits/field_coverage_reviewed_ids.txt`: the 67 items both AI reviews
  marked `field_aligned`. A supplementary diagnostic subset, with its
  composition and rebuild command in `splits/README.md`.
- `question_scoring_scope_review.json`: the protocol, original score-blind
  input and raw texts of two subsequent AI reviews, with four separate
  question/scoring axes, hashes, judgments and limits for all 133 candidates.
- `splits/question_scoring_scope_reviewed_ids.txt`: the 45 items both reviews
  marked `compatible` on all four axes; a supplementary subset of the 67.
  `splits/rebuild_question_scoring_scope_subset.py` checks the pinned sources,
  stored reviews and exact membership without certifying judgment truth.
- `cypher/{WG}_P{phase}_{id}.cypher` — 624 executable Cypher reference
  queries (one per released CQ).
- `sparql/P{phase}_{id}.rq` — 142 SPARQL translations covering **all
  released RAN1 CQs** (translated from the reference Cypher; each carries
  the CQ text and a pointer to its Cypher source, and parses under rdflib).
  Class-membership guards default to `FILTER EXISTS` so greedy join
  planners do not form class-enumeration cross products; positive
  `rdf:type` triples are used where the type pattern is itself the
  query, is anchored to a constant, or (with an engine note in the
  query) replaces a pattern rdflib evaluates too slowly. Row-count
  parity against the Cypher replay: 142/142 match
  (`../../validation/cq_replay/sparql_parity_results.json`). The 142 is
  the RAN1 portability slice, distinct from the 624-query full Cypher
  benchmark (see `../../MANIFEST.md` §2.1).
- `gold/RAN{1..5}_gold.json` — gold answer sets for all 654 authored CQs
  (the authored superset is kept intact), plus `gold/_gold_summary.json`
  recording the 654 / 624 / 30 split.
- `held/held_cqs.json` — the 30 held-out CQs with Cypher and status.
- `held/contract_held_out.json`: the 64 released CQs outside
  SpectraCQ-Core, each with its question, gold columns, gold row count and a
  reason in one of 5 classes. Core (560) and these 64 make up the
  624 released CQs. They are distinct from the 30 authored CQs of
  `held/held_cqs.json`, which are not among the 624.
- `croissant.json` — Croissant ML dataset metadata.
- `CITATION.cff` / `citation.bib` — citation metadata.
- `LICENSE` — CC-BY 4.0.

## Scoring scope and annotation limits

The 132-item rule-only diagnostic subset is the intersection of the 149
and 133 lists; no new membership file replaces the preserved lists. The
subset names and labels in frozen annotations are historical. They describe
annotation conditions, without validating all natural-language requirements.

The Core gold projects a reference query onto its declared answer column.
Exact and Set-F1 compare normalized value sets, discarding duplicate values
and row order; other returned columns receive no credit or penalty. In
`RAN4_P1_CQ5-1` the question asks for counts by label, but the scored column
is `label`. In `RAN5_P1_CQ1-5` the question asks for Samsung's TDocs newest
first, but set scoring does not compare their order. Both belong to the
133. Replaying a reference query checks its stored outputs, not that this
projection fully answers the question. See [subset definitions](splits/README.md)
and the [baseline README](../../../paper/baseline/README.md) for the limits of
the recorded predictions and whole-record diagnostics.

The [annotation diagnostic](contract_annotation_diagnostics.json), generated
by [audit_demand_annotations.py](splits/audit_demand_annotations.py), enumerates
unscored returned fields and syntactic `ORDER BY`/`LIMIT` signals for all Core
items and the 133/208 subsets, checks the denominator of the later-column
demand count, and gives three source-grounded count, recipient and ranking
examples. These signals are not an estimate of semantic error prevalence or
independent practitioner validation. It preserves questions, annotations,
gold and subset membership.

The [AI-assisted field-coverage review](field_coverage_review.json) examined
all 133 candidates using their question, reference Cypher, returned column
names and scored answer column. Two mutually isolated Codex AI agents saw
neither the other review nor demand/type labels, predictions or item scores.
The protocol tested whether the requested fields, counts, mapping, order and
multiplicity could be represented by the scored unordered value set, and
whether an evident query scope or cap conflicted with the question. Explicit
top-k membership can be set-scored when its k and criterion are specified;
explicit rank/order cannot. The exact AI model snapshot was not recorded.

One review recorded 70 `field_aligned`, 54 `mismatch` and 9 `ambiguous`; the
other recorded 67, 56 and 10. They gave the same status on 129 of 133 items.
The [67-item intersection](splits/field_coverage_reviewed_ids.txt) was frozen
before its new subset scores were computed. Any mismatch or ambiguity
excluded an item, without score-based adjudication. The 66 excluded items
are not 66 independently confirmed semantic errors. These are fallible
AI judgments, not human or 3GPP expert validation, semantic certification or
an estimate of error prevalence.

The intersection contains 21 lookup, 42 aggregation, 3 relational and
1 multihop item, and no declared tuple/mapping item. This composition limits
generalization to richer answer types and tracks. Its recorded offline
scores and reproduction commands are in the
[baseline README](../../../paper/baseline/README.md). The diagnostic preserves
all questions, reference queries, gold and original outputs; it replaces
neither Core nor the 133/208. The Core scorer default remains the
annotation-derived 133 for compatibility, without a semantic-validity guarantee.

### Four-axis question/scoring follow-up

The subsequent [question/scoring review](question_scoring_scope_review.json)
examined every original 133 candidate on four separate axes:
`required_fields`, `scope_and_roles`, `cardinality_and_truncation` and
`ordering_and_duplicates`. Its embedded protocol is fixed and each judgment
has a literal question/query/column anchor. An overall judgment is
`compatible` only when all four axes are compatible, `incompatible` when
any axis is incompatible, and `unclear` otherwise. Selection takes the
intersection of the two overall-compatible lists; no score-based
adjudication changes it.

Two fresh, mutually isolated Codex AI agents received only that protocol
and the question, reference query, returned columns and scored column.
Predictions, scores, earlier judgments and demand labels were hidden from
the reviewers. The designers had already seen Core/133/208/67 metrics,
so this is a subsequent diagnostic with those earlier results known.
The exact AI model snapshot was not recorded. Neither review is a human
or 3GPP expert assessment, and agreement does not certify domain truth or
complete question semantics.

Review A recorded 51 compatible, 40 incompatible and 42 unclear items;
review B recorded 46, 38 and 49. They gave the same overall status on
124/133. The [45-item intersection](splits/question_scoring_scope_reviewed_ids.txt)
was recorded as frozen at 2026-10-06 22:42:02 UTC before its new subset
scores. The remaining 88 include disagreements and uncertainty and are
not 88 confirmed semantic errors. The 45 are contained in the earlier
67-item field-coverage intersection, whose judgments and scores remain
available.

The 45 contain 14 lookup, 30 aggregation, 1 relational and 0 multihop
items, with no declared tuple/mapping item. Their original answer-type
labels are 40 `scalar_set` and 5 `ranked_top_k`; scoring remains unordered
and does not validate returned rank order. The ordering axis assesses the
question's explicit requirements. Selection and this composition limit
generalization to Core, richer answer types and all tracks. The
[subset README](splits/README.md) gives the source/selection checker;
the [baseline README](../../../paper/baseline/README.md) gives retained-output
scores and separate-output reproduction commands. This diagnostic changes
no question, reference query, answer key, original output or existing subset,
and leaves the annotation-derived 133 scorer default in place.
The baseline analysis compares model ranks with Core under the same metric:
answer-column Spearman is 0.850000, full-record P is 0.583333 and S/C
are 0.600000. Six of nine models change rank under P, so answer-column
rank agreement does not establish full-record rank stability.

The [baseline README](../../../paper/baseline/README.md) also links a retained
SQL/Cypher comparison on all 560 Core items using the same repaired
answer-column key, with query failures included as zero. Its paired interval
includes zero; it does not establish an engine's causal advantage or validate
all question requirements, and it does not reconstruct the historical SQL cohort.

## Company-name policy

The 49 of the 624 released reference queries that mention companies retain
the **verbatim** public 3GPP identifiers (Huawei, Samsung, Qualcomm, ...) as
they appear on the public per-meeting `TDOC_List.xlsx`. The other 575
reference queries name no specific company. The legacy mapping is
intentionally not published in v1.0.

## How to use

```bash
# Inspect questions
jq '.cqs[0]' questions.json

# Inspect one scored benchmark row
head -1 benchmark.jsonl | jq .

# Run a single CQ against a SPECTRA-conformant Neo4j (example: RAN1 P1 CQ1-1)
cypher-shell -u neo4j -p <pass> < cypher/RAN1_P1_CQ1-1.cypher

# Run a SPARQL translation against the released RDF (rdflib; RAN1 subset)
python3 -c "import rdflib; g=rdflib.Graph(); g.parse('../../kg/per_wg/RAN1-body.ttl');
print(len(list(g.query(open('sparql/P1_CQ1-1.rq').read()))))"
```

Scoring convention: compare a system's predicted answer set against the gold
set (`benchmark.jsonl`) over the primary column with set-level exact match
and set precision / recall / F1 on normalised values.

## Companion releases

- SPECTRA OWL ontology (this benchmark's schema): https://w3id.org/spectra
- Paper: "SPECTRA: A Traceability Ontology for the 3GPP RAN Standardization
  Process" (currently under review).

## Citation

See `CITATION.cff` / `citation.bib`. Cite the concept DOI
**10.5281/zenodo.20034871**, which always resolves to the newest published
deposit; the 624-CQ scored benchmark is carried by the release-package 2.0.0
deposit under that concept. Two additions in this directory, `splits/` and
`answer_contract.jsonl`, were made after the 2.0.0 archive was built and are
present in the Git tree only. Both are plain text: the identifier lists under
`splits/` rebuild offline from files in this directory, and
`answer_contract.jsonl` ships as data. See section 5 of `../../MANIFEST.md`
for the deposit-versus-repository split. Eight later additions,
`core_answer_gold.jsonl`, `held/contract_held_out.json`,
`splits/contract_exact_241.txt`, `contract_demand_provenance.jsonl`,
`splits/contract_exact_rule_only_149.txt`,
`splits/contract_exact_asked_208.txt`,
`splits/contract_exact_script_fixed_133.txt` and
`splits/rebuild_contract_splits.py`, are likewise in the Git tree only.

## License

CC-BY 4.0. You are free to share and adapt; please cite.
