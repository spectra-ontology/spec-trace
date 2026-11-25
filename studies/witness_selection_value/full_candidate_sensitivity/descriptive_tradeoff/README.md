# Descriptive variation and tie recount

This exploratory descriptive analysis explains a concrete tradeoff within the frozen full-candidate census. Across the 87 other controls, the equal-cell expected discrimination increases from **40.1% to 47.3%**; its 49 nonempty cells comprise **16 increases, 17 ties and 16 decreases**. Eligibility changes the distribution of operation-specific witnesses within each cell, so the positive average accompanies heterogeneous cell contrasts. The [complete cell contrasts](../cell_mean_contrasts.csv) retain each direction.

The RAN1 `maximum_variation` cell illustrates complementary witness properties. Its eligible cohort requires at least two distinct strictly positive typed-footprint sizes. All **522** candidate packs contain **196** maximum ties that distinguish the reference query from `LIMIT 1`; the **268** eligible packs contain **54** such ties. The other **254** packs contribute **142** tie-exposing cases. Equal maximum footprints can expose truncation while offering a single positive footprint size: pack `RP-191277` contains `R1-1905823` and `R1-1905888`, each with footprint size **1**. The complete reference returns both rows, and `LIMIT 1` returns the first. A variation witness and a tie-specific witness therefore cover complementary relational properties.

This recount reconstructs typed footprints from `cr_in_pack`, `cr_modifies_section` and `section`, then executes the reference and `LIMIT 1` SQL on **every one of the 522 packs**. All **1,044** executions agree with the raw-relation reconstruction and the frozen candidate annotations. It explains the already measured RAN1 contrast within the aggregate heterogeneity. Its scope is existing source data and known SQL operations; it introduces an exploratory descriptive analysis rather than a model experiment or causal estimate.

| File | Evidence |
|---|---|
| [analysis_plan.json](analysis_plan.json) | Preserved author analysis plan |
| [recount.py](recount.py) | Portable standard-library recount, pinned inputs and complete SQL comparisons |
| [result.json](result.json) | All 522 raw-count reconstructions, reference and truncated rowsets, aggregate counts and runtime receipt |

## Portable replay

Run from the release root with Python linked to **SQLite 3.37.2**; the recorded runtime is Python 3.10.12. The tool verifies the released database, compressed annotation and plan byte hashes before reading the data. `--release` can point to a downloaded release or its minimal input closure containing `sqlite/RAN1.sqlite` and the pinned candidate annotation. `--annotation` explicitly selects that downloaded annotation. A temporary directory receives the new output.

```sh
free -h
TASK_RELEASE=$(pwd -P)
TASK_OUTPUT=$(mktemp -d "${TMPDIR:-/tmp}/spectra-descriptive-tradeoff.XXXXXX")
python3 -B studies/witness_selection_value/full_candidate_sensitivity/descriptive_tradeoff/recount.py --help
python3 -B studies/witness_selection_value/full_candidate_sensitivity/descriptive_tradeoff/recount.py \
  --release "$TASK_RELEASE" \
  --annotation "$TASK_RELEASE/studies/witness_selection_value/full_candidate_sensitivity/run/candidates_RAN1.jsonl.gz" \
  --output "$TASK_OUTPUT/result.json"
```

Compare the five aggregate count fields, `inputSha256`, `allCandidateDetails`, `sqlExample` and `sqlAudit` with the included result. `createdUtc` and `runtime` record the fresh execution. All scientific input files are read-only; the tool checks their final hashes. Execution uses the Python standard library and requires zero model, server or paid API calls. This AUTHOR packaging and execution is separate from the earlier independent resource reviews.

Project-authored files use the release's [CC BY 4.0 license](../../../../LICENSE). Citation metadata is in `CITATION.cff` at the release root.
