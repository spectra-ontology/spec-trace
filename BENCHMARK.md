# Benchmark families and requested fields

The released questions exercise documentary operations over contributions, dispositions, meetings, packs and clauses. This inventory is computed from the admitted item records, with each source file bound by SHA-256 in [the machine-readable inventory](sources/workload_inventory.json).

| Workload | Family | Items | Empty gold | Record hops | Requested fields | WG item counts |
|---|---|---:|---:|---|---|---|
| Main | `clause_history` | 100 | 0 | 4 | `document`, `disposition`, `wg_meeting`, `cr_pack` | RAN1: 20, RAN2: 20, RAN3: 20, RAN4: 20, RAN5: 20 |
| Main | `disposition_pack` | 99 | 0 | 3 | `disposition`, `wg_meeting`, `cr_pack`, `tsg_meeting` | RAN1: 20, RAN2: 20, RAN3: 20, RAN4: 20, RAN5: 19 |
| Main | `full_chain` | 100 | 0 | 4 | `disposition`, `wg_meeting`, `cr_pack`, `tsg_meeting`, `clause` | RAN1: 20, RAN2: 20, RAN3: 20, RAN4: 20, RAN5: 20 |
| Main | `pack_lookup` | 100 | 0 | 1 | `cr_pack`, `tsg_meeting` | RAN1: 20, RAN2: 20, RAN3: 20, RAN4: 20, RAN5: 20 |
| Main | `pack_lookup_empty` | 86 | 86 | 1 | `cr_pack`, `tsg_meeting` | RAN1: 7, RAN2: 20, RAN3: 20, RAN4: 19, RAN5: 20 |
| Main | `pack_origin` | 100 | 0 | 3 | `document`, `disposition`, `wg_meeting` | RAN1: 20, RAN2: 20, RAN3: 20, RAN4: 20, RAN5: 20 |
| Main | `revision_chain` | 82 | 0 | 4 | `final_document`, `disposition`, `cr_pack` | RAN1: 3, RAN2: 20, RAN3: 20, RAN4: 20, RAN5: 19 |
| Order-sensitive extension | `clause_neighbours` | 100 | 0 | 5 | `clause`, `document`, `disposition`, `wg_meeting`, `cr_pack` | RAN1: 20, RAN2: 20, RAN3: 20, RAN4: 20, RAN5: 20 |
| Order-sensitive extension | `first_change` | 98 | 0 | 5 | `document`, `specification`, `clause` | RAN1: 20, RAN2: 20, RAN3: 19, RAN4: 19, RAN5: 20 |
| Order-sensitive extension | `previous_pack` | 99 | 0 | 5 | `specification`, `clause`, `cr_pack`, `tsg_meeting` | RAN1: 20, RAN2: 20, RAN3: 19, RAN4: 20, RAN5: 20 |

Record hops describe each family's construction contract. A solver may answer the released projection with a different number of joins. The item records retain their anchor, evidence and complete gold row set; the independent gate derives answers from the released relations.

Seven main family labels include an empty-gold variant of pack lookup. The three extension families add clause-set comparison and meeting-order conditions. Main and extension results retain their separate analysis scopes.

The [family answer contract](benchmark/ANSWER_CONTRACT.md) defines each family's record universe, identity, eligibility, clause and ordering rules. Its executable checker compares all 964 main/extension gold sets in both record directions and exercises meaning-changing boundary cases. The [historical task-exposure audit](benchmark/task_exposure/README.md) records the actual instructions supplied to the original solvers.

## Main-workload structure and answer contract

The 667 main items use 667 distinct working-group/anchor pairs. Of the 581 answerable items, 411 return one row. Row count measures output size; the inventory separately records the actual directed revision path when `--check-snapshot-contract` is selected.

An empty answer refers to the exact TDoc and specification/CR identity in the fixed released snapshot and its meeting coverage. The gate checks pack membership and the corresponding list fields for that identity. The source disposition codes of the 86 empty items are `not_agreed`: 1, `not_pursued`: 25, `not_treated`: 18, `withdrawn`: 42. Later revisions retain their own document and CR identities.

The database check confirms all 86 empty snapshot contracts. The 82 revision questions have shortest paths to their returned documents at these depths: 1: 62 items, 2: 18 items, 9: 1 items, 12: 1 items. All 82 return one row. The inventory also records the different-identity successor of R1-167179, including its separate specification, CR number and pack field.

Recompute this inventory from the checkout:

```sh
free -h
python3 restore/describe_workload.py --release . --out work/workload_inventory.json --markdown work/BENCHMARK.md --check-snapshot-contract
```

[The builder](code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/build_chain_items.py) defines the family contracts; [reproduction instructions](REPRODUCING.md) connect fixed-anchor construction, independent admission and scoring. Preserve item identity, requested fields and gold row sets when adding a comparison.

## Public-schema comparison

[The current schema review](sources/schema_comparison_review.json) records the six typed process elements, the exact frozen comparison report, and the primary-text scope for the three KG schema reassessments. It reproduces the manuscript's comparison of 15 public resources and the released process records across all 667 main items. The calculation keeps undetermined slots and counts (`null`) distinct from assessed absent slots and zero expressible items; expressibility measures schema support independently of slot population. The original report remains available as the historical measurement.

```sh
free -h
python3 restore/describe_schema_comparison.py --release . --out work/schema_comparison.json
```

## Data that expose operator mistakes

The [witness design](studies/semantic_witnesses/README.md) fixes 19 data properties across five WGs and retains every candidate and predicate outcome. In the 66 available property/WG cells, the [paired anchor comparison](studies/witness_selection_value/README.md) holds query templates, the hash rule and 200 error controls fixed. Witness selection detects 162/200 controls; applying the same hash rule before the final witness predicate detects 93/200. Both arms retain query-validity and shared-identity preconditions. Of the 113 controls directly involved in selection, the respective counts are 113 and 56; for the other 87, they are 49 and 37. Full candidate universes, selected queries and raw row sets support independent replay. This measures sensitivity to the specified operator mistakes on released records, separately from model accuracy.

## Using a documentary subquery in a real question

The [engineer-question analysis](studies/practitioner_questions/README.md) gives de-identified summaries and model classifications of 33 existing question units, separately from the generated benchmark. A power-class wording question illustrates a supported clause-history subquery: the released SQL retrieves 28 source-bound documentary rows for TS 38.101-1 clause 6.2.1 in Rel-17. Those rows identify candidate CRs and their recorded dispositions, meetings and packs for subsequent inspection of the technical text and discussion. The example preserves its curated derivation and source context.

The [matched-domain diagnostic](studies/matched_domains/README.md) offers a small executable interface check: one hash-selected representative for each main or extension family/WG cell, 50 in total. Both languages receive the same categorical appendix. The four archived first submissions each answer all 50; selection, inputs, query bytes, complete returned sets and unknown provider-model identity are retained. The main and extension benchmark scores keep their own populations and historical input conditions.
