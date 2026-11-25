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

Recompute this inventory from the checkout:

```sh
free -h
python3 restore/describe_workload.py --release . --out work/workload_inventory.json --markdown work/BENCHMARK.md
```

[The builder](code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/build_chain_items.py) defines the family contracts; [reproduction instructions](REPRODUCING.md) connect fixed-anchor construction, independent admission and scoring. Preserve item identity, requested fields and gold row sets when adding a comparison.
