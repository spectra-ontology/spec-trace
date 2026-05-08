# SPECTRA Use Scenarios — Release File Mapping

This document maps the seven use scenarios (S1–S7) discussed in §6.5 / Table 9
of the SPECTRA ISWC 2026 paper to the concrete artifacts in this release.

The mapping is conservative: where a scenario does not have a dedicated
end-to-end query in `queries/`, the scenario can still be exercised by
composing against the bundled TTL data with the schema fragment cited in
the paper. Where v1.0.0 does not populate the scenario at all (S4), this
document says so explicitly rather than implying it is.

The release ships per-Phase representative CQ queries in
`queries/cypher/` and `queries/sparql/` (one per Phase plus a
`MULTI_HOP_traceability` query); the larger 137-CQ benchmark is at
`cqs/spectra_cq_v1.0/`.

| Code | Scenario                          | Status in v1.0.0           | Where to find / how to run                                                                                                                                                                                |
|------|-----------------------------------|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| S1   | Multi-hop clause-lineage trace    | populated (synthetic E2E)  | `examples/end_to_end/data.ttl`, `examples/end_to_end/query.sparql`, `examples/end_to_end/query.cypher`, `examples/end_to_end/expected_output.txt`. Representative phase-agnostic queries: `queries/cypher/MULTI_HOP_traceability.cypher` and `queries/sparql/MULTI_HOP_traceability.rq`. |
| S2   | Cross-WG LS impact                | populated (real metadata)  | `examples/process_kg/ls_routing.ttl` (25 586 distinct LSs across RAN1–RAN5; per-WG breakdown and de-duplication note in `examples/process_kg/_export_summary.txt`). No dedicated single-file query ships; LS-fan-out queries are composed using `originatedFrom` / `sentTo` against this TTL.  |
| S3   | Release-scoped CR analytics       | populated (real metadata)  | `examples/process_kg/cr_routing.ttl` (192 967 CRs; per-WG breakdown in `_export_summary.txt`). Phase-4 representative CQ at `queries/cypher/P4_CQ1-1.cypher` and `queries/sparql/CQ4-1_cr_reason_for_change.rq` exercises the CR layer and can be parameterised by Release.                  |
| S4   | Working-Assumption promotion lineage | **schema-only pattern** in v1.0.0 — *not* populated in the released or deployed snapshots; data-side population by enhanced ingest is future work | Schema fragment: `WorkingAssumption --promotedTo--> Agreement`, joined on `madeAt`. Defined in `ontology/spectra.ttl` (object property `promotedTo`). No instance file or scenario query ships in v1.0.0. |
| S5   | TR → TS impact propagation        | populated (RAN1 KG)        | `validation/ran1_instance_counts.json` reports `TRImpact = 29`. Phase-5 representative CQ at `queries/cypher/P5_CQ1-1.cypher` and `queries/sparql/CQ5-1_trs_impacting_spec.rq` exercises the reified TR-to-TS chain via `hasTRImpact` / `impactsSection`.                                  |
| S6   | Per-company contribution profile  | populated (real metadata)  | `examples/process_kg/ran1_tdoc_metadata.ttl` (123 678 RAN1 TDocs with `submittedBy`). Phase-1 representative CQ filtered by Company at `queries/cypher/P1_CQ1-3.cypher`; the SPARQL counterpart `queries/sparql/CQ1-1_tdocs_by_meeting_and_workitem.rq` is parameterisable on `submittedBy`. |
| S7   | Work-Item-scoped lineage          | populated (real metadata)  | `examples/process_kg/ran1_tdoc_metadata.ttl` carries `relatedToWorkItem`; `validation/ran1_instance_counts.json` reports WorkItem = 423. Representative CQ joining Meeting and WorkItem at `queries/cypher/P1_CQ1-1.cypher` and `queries/sparql/CQ1-1_tdocs_by_meeting_and_workitem.rq`.    |

## Notes

* "Populated" means the released TTL/JSON files contain real or
  representative instance data sufficient to exercise the schema fragment
  end-to-end. "Schema-only" means the OWL property/class is defined but no
  instance triples ship in v1.0.0.
* The `examples/process_kg/` exports retain verbatim public 3GPP company
  identifiers (consistent with the per-meeting `TDOC_List.xlsx` and the
  3GPP attribution policy in `ARTIFACT.md`).
* Per-WG body-text TTLs (`kg/per_wg/RAN{1..5}-body.ttl`) are deposited on
  Zenodo (DOI [10.5281/zenodo.20034872](https://doi.org/10.5281/zenodo.20034872))
  and are not redistributed in the GitHub package. Scenarios S2/S3/S6 are
  fully exercisable on the metadata-only `examples/process_kg/` artifacts;
  body-text-dependent queries (e.g., free-text retrieval over CR / TR
  rendered prose) require the Zenodo deposit.
* `tests/verify_release.py` exits 0 with 37/37 PASS on the dev tree
  (with body TTLs locally) and 32/32 PASS + 5 SKIP on the public mirror
  (body TTLs deferred to Zenodo per §7 of the paper).

## Re-deriving the per-WG counts above

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
