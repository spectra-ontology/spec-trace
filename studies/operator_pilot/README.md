# Source-bound analytical operator pilot

This study tests six additional operations over the released process records: disposition counts, section intersection, section difference, conjunction of section requirements, maximum distinct-section counts with ties, and recorded-link absence. Each operation has one deterministically selected item in each of five working groups. The 30 author-written questions form a small additional workload, with a separate study identity from the 667 main items and the 297 order-sensitive extension items.

`protocol.json` fixes the operator semantics, eligibility, hash-based selection, admission and first-response evaluation condition. `build_operator_suite.py` enumerates eligible anchors using the existing read-only SQLite exports. Python sets and dictionaries derive the gold rows from relation records; separately written reference SQL must return the same complete row sets. `frozen/freeze.json` binds the selected questions, gold, references, complete relevant value domains and source hashes before model responses are obtained.

All 30 planned operator/work-group cells have eligible anchors and Python/SQL agreement. Native section identities retain specification, release and clause. Maxima retain all ties. Recorded absence refers to the released snapshot. These task definitions make the operators explicit while preserving the underlying source-validation scope of the resource.

The [independent semantic check](semantic_validation.json) independently implements all 30 reference tasks and returns the same complete gold sets. Twenty-five deliberately different operator implementations return different sets. Three selected maximum tasks exercise ties. All five disposition-count tasks have one `agreed` group; two distinguish row count from distinct-document count. The selected maxima preserve their answers when section counts collapse releases. The pilot therefore exercises its recorded operation instances, including these specific discrimination boundaries.

The [fresh writer's first response](first_response.json) answers **30/30** items exactly, five per operation and six per working group, with zero execution errors or timeouts. The writer receives only `frozen/writer_questions.json` and `frozen/writer_schema.json`. Its instruction permits reading these two files and writing its first response, and provides zero execution feedback. This is procedural input blinding in a shared workspace. [The completion record](writer_completion_receipt.json) binds the response before execution. The execution script `evaluate_first_response.py` uses SQLite 3.37.2, read-only connections and a 60-second per-query cap. [The execution receipt](first_response_execution.json) retains every query and complete result and verifies source hashes before and after execution.

The questions were authored for this operator study. They characterize operation coverage within this resource. The existing, separately classified engineer-question collection supplies evidence about actual question types; it has its own population and annotation scope. This single-session pilot reports descriptive operation coverage under explicit value-domain access. Natural-question population estimates and causal comparisons require their corresponding study designs.

From the public checkout root, replay into a new local output path with system Python 3.10 and SQLite 3.37.2:

```sh
free -h
python3 -B studies/operator_pilot/evaluate_first_response.py \
  --frozen studies/operator_pilot/frozen \
  --responses studies/operator_pilot/first_response.json \
  --release "$PWD" --database-directory /tmp/spectra-operator-pilot/sqlite \
  --output /tmp/spectra-operator-pilot/replayed.json
```

The scratch output directory must already exist. The evaluator checks every frozen file and database hash, uses the released compressed exports where appropriate, and preserves every execution outcome. Source and evaluator hashes record the exact execution condition. The earlier local-path-only evaluator pin is retained alongside its pre-writer portability revision.

Closest primary work includes [SemBench](https://doi.org/10.14778/3811243.3811249), which varies operators and scenarios for semantic database operators, and [Dr.Spider](https://arxiv.org/abs/2301.08881), which tests language, schema and SQL perturbations. Here the contribution is an additional source-bound process workload and its replayable measurement. These established evaluation ideas retain their attribution.
