# SPECTRA Use Scenarios — Release File Mapping

This document maps the seven use scenarios (S1–S7) discussed in §6.5 / Table 9
of the SPECTRA paper to the concrete artifacts in this release.

The table distinguishes the metadata files in this checkout, the body-text
graphs downloaded from Zenodo, and small illustrative samples. A schema
declaration or a synthetic example does not establish that a relation is
populated in the released corpus. See also the
[requirements-to-schema mapping](PROCESS_REQUIREMENTS.md).

The release ships per-Phase representative CQ queries in
`queries/cypher/` and `queries/sparql/` (one per Phase plus a
`MULTI_HOP_traceability` query); the larger 624-CQ benchmark is at
`cqs/spectra_cq_v2.0/`.

| Code | Scenario                          | Status in v1.0.0           | Where to find / how to run                                                                                                                                                                                |
|------|-----------------------------------|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| S1   | Multi-hop clause-lineage trace    | synthetic illustration; CR/section and TR/spec paths in the RAN1 body graph | `examples/end_to_end/` illustrates a meeting-context join, not a verified causal path from a contribution to a clause. The released-graph queries `queries/cypher/MULTI_HOP_traceability.cypher` and `queries/sparql/MULTI_HOP_traceability.rq` join the CR and TR layers by `specNumber`; they do not recover a complete TDoc/Resolution/CR chain. |
| S2   | Cross-WG LS routing               | populated (real metadata)  | `examples/process_kg/ls_routing.ttl` (25 586 distinct LSs across RAN1–RAN5; per-WG breakdown and de-duplication note in `examples/process_kg/_export_summary.txt`). Routing queries use `originatedFrom` / `sentTo`; these record sender/recipient direction and do not measure downstream impact. |
| S3   | Release-scoped CR analytics       | populated (real metadata)  | `examples/process_kg/cr_routing.ttl` (192 967 CRs; per-WG breakdown in `_export_summary.txt`) supports joins on `modifies` and `targetRelease`. The Phase-4 queries `queries/cypher/P4_CQ1-1.cypher` and `queries/sparql/CQ4-1_cr_reason_for_change.rq` additionally read CR body fields and require the body-text graph. |
| S4   | Working-Assumption promotion lineage | **schema-only pattern** in v1.0.0 — *not* populated in the released or deployed corpus snapshots; data-side population by enhanced ingest is future work | `WorkingAssumption --promotedTo--> Agreement` is declared in `ontology/spectra.ttl`. No corpus population is provided. The `end_to_end/` sample supplies a synthetic edge and query solely to illustrate the pattern. |
| S5   | TR → TS impact propagation        | populated (RAN1 KG)        | `validation/ran1_instance_counts.json` reports `TRImpact = 29`. `queries/sparql/CQ5-1_trs_impacting_spec.rq` exercises the reified TR-to-spec chain via `impactsSpec`; the Cypher TR-impact chain is in `queries/cypher/MULTI_HOP_traceability.cypher` (TR layer), and `queries/cypher/P5_CQ1-1.cypher` returns TR-level attributes (scope, conclusions).                                  |
| S6   | Per-company contribution profile  | populated (real metadata)  | `examples/process_kg/ran1_tdoc_metadata.ttl` has 123 678 RAN1 TDoc records and `submittedBy` links for metadata profiles. `queries/cypher/P1_CQ1-3.cypher` filters by Company and additionally returns document titles, requiring the body-text graph. Clause-level company profiles also require the finer-grained body-graph relations. |
| S7   | Work-Item-scoped lineage          | requires the RAN1 body-text graph | The TDoc-to-WorkItem relation is `relatedTo`, omitted from `examples/process_kg/ran1_tdoc_metadata.ttl`. `validation/ran1_instance_counts.json` reports WorkItem = 423 in the RAN1 graph. `queries/cypher/P1_CQ1-1.cypher` and `queries/sparql/CQ1-1_tdocs_by_meeting_and_workitem.rq` exercise this relation. The `real_world_mini/` sample illustrates it separately. |

## Notes

* "Populated" refers to the corpus or metadata export named in the row.
  The `end_to_end/` sample is synthetic. Its `promotedTo` edge illustrates
  S4, but this edge is absent from the released and deployed corpus snapshots.
* The `examples/process_kg/` exports retain verbatim public 3GPP company
  identifiers (consistent with the per-meeting `TDOC_List.xlsx` and the
  3GPP attribution policy in `ARTIFACT.md`).
* Per-WG body-text TTLs (`kg/per_wg/RAN{1..5}-body.ttl`) are deposited on
  Zenodo (DOI [10.5281/zenodo.20034871](https://doi.org/10.5281/zenodo.20034871))
  and are not redistributed in the GitHub package. Metadata routing,
  release-target and company-profile counts for S2/S3/S6 can be exercised
  on `examples/process_kg/`; queries returning titles, CR/TR rendered prose
  or finer-grained clause links require the Zenodo body-text deposit.
* `tests/verify_release.py` re-verifies the shipped counts and evidence
  (run from `release_package/`); checks that require the per-WG body TTLs
  are skipped when only the GitHub package is present (body TTLs deferred
  to Zenodo per §7 of the paper).

## Snapshot-specific scenario counts

[cross_wg_use_evidence.json](../validation/cross_wg_use_evidence.json)
records the deployed graph measurements from 2026-04-27. The separate
[released_graph_scenario_counts.json](../validation/released_graph_scenario_counts.json)
records a recount of the deposited body-text graphs and their file hashes.
The latter is the source for counts on the downloadable corpus:

| Query | Released body-text graph | Earlier deployed graph record |
|---|---:|---:|
| RAN1 LSs sent to RAN2 | 3,644 | 3,644 |
| CR instances modifying TS 38.300 in RAN2 | 2,039 | 2,039 |
| CR instances modifying TS 38.300 in RAN3 | **1,249** | 270 |

The RAN3 released count includes 1,144 `draftCR` and 105 `pCR` instances;
it is not a count restricted to formal CRs. The 270 in the paper's scenario
table comes from the earlier deployed record and must not be used as the
released-corpus count. The original measurements remain available above.

With the five downloaded body-text files in `kg/per_wg/`, run from
`release_package/`:

```bash
python3 tests/reproduce_scenario_counts.py
```

This verifies the saved released-graph result and displays its differences
from the deployed record. It makes no claim that routing counts establish
causal propagation or that the full contribution-to-clause path is complete.

## Re-deriving the metadata-export counts above

```
# Distinct LSs across RAN1–RAN5 union:
grep -E 'spectra:tdocNumber\s+"' examples/process_kg/ls_routing.ttl \
  | grep -oE '"[A-Z0-9-]+"' | sort -u | wc -l
# Expected: 25586

# Per-WG LS routing entry count (a cross-WG LS is counted once per endpoint):
grep -c "a spectra:LS\b" examples/process_kg/ls_routing.ttl
# Expected: 26791

# CR routing total:
grep -c "a spectra:CR\b" examples/process_kg/cr_routing.ttl
# Expected: 192967

# RAN1 TDocs in metadata-only snapshot:
grep -c "a spectra:Tdoc\b" examples/process_kg/ran1_tdoc_metadata.ttl
# Expected: 123678 (123 677 distinct identifiers + 1 re-tabled record)
```

The same counts are recorded in `examples/process_kg/_export_summary.txt`
(both the per-WG sum and the de-duplicated distinct-LS count).
