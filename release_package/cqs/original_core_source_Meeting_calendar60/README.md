Separate source-calendar correction for original RAN1_P3_CQ017. Adds two own-report meeting-period properties to 60 existing Meeting nodes (120 properties, no new nodes or edges); frozen 447/560 index and prior results remain unchanged.

The actual native reference includes all 3,041 eligible CRs and supports any 20-row answer containing 18 strictly newer records plus any 2 of 46 boundary records. These are meeting-period dates, not upload/approval timestamps. All 192 authored frontmatter windows are retained; full report body equality is not established.

The separate actual model experiment is in [original_core_source_Meeting_calendar60_evaluation](../original_core_source_Meeting_calendar60_evaluation). Five HTTP200 calls cost $0.181755 with no quality retry: requested-record macro F1 Text2Cypher 0.10, Text2SQL 1.00, single retrieval 0, two-round retrieval 0. Both retrieval arms abstain. Text2SQL orders uploadedDate and ignores added meeting dates; its exact answer records do not verify that generated predicate or establish a causal effect of this correction. Human/expert validation is 0.

Use portable_patch/verify_rebuild.py and portable_patch/evaluation/verify_controls.py; unchanged original stores are required only for a fresh separate rebuild.
