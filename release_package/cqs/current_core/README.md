# Current original Core contract index

All 560 original IDs are retained: **475 pass the stated repair checks and 85 remain pending**. Original English questions are unchanged. Ten admitted IDs use separate full-ranking-pool replacements without adding IDs.

`current_tasks.jsonl` routes each admitted question to its immutable definition, reference records, requested fields, scorer and evidence. `all_core_dispositions.jsonl` retains every pending ID and its reasons. Historical bundles, gold and model results retain their original bytes.

The latest [twelve-question repair bundle](../original_core_overnight_repairs15/README.md) and [four-method evaluation](../original_core_overnight_evaluation15/README.md) retain 20,593 complete native reference records, full independent SQL agreement, 103 generic scorer controls and 138 additional controls on actual populations. All 60 received first-call responses and 48 method outcomes are preserved, including failures and abstentions. No answer-quality retry was performed. The model cost was $2.673905, with no unknown-cost attempts.

The earlier 467-pass snapshot is preserved under the latest bundle's `baseline467/`. Four former passes are now pending after original-source factuality reassessments; twelve new passes give a net increase of eight. The [quarantine registry](../original_core_overnight_repairs15/source_factuality/quarantines.json) includes both reviews and source receipts:

| ID | Unresolved source issue |
| --- | --- |
| RAN1_P2_CQ1-1 | Agenda 7.1 and the named MIMO topic identify different source sections. |
| RAN3_P4_CQ2-3 | A Text Proposal has attributes belonging to a different formal CR. |
| RAN4_P1_CQ6-3 | Counted CR labels include discussion, WF and email-summary documents. |
| RAN5_P1_CQ6-3 | Counted CR class stubs include authentic discussion and liaison documents. |

No complete corrected gold or historical extraction cause is claimed for these four. Historical passes remain inspectable and do not contribute to the current pass count.

Run from the repository root, without credentials, API calls or database execution:

```sh
python3 -B -S release_package/cqs/current_core/verify_index.py
python3 -B -S release_package/cqs/original_core_overnight_repairs15/verify_additions.py --bundle release_package/cqs/original_core_overnight_repairs15
python3 -B -S release_package/cqs/original_core_overnight_evaluation15/runtime/verify_authorized_incremental15_evaluation_v1.py --evidence release_package/cqs/original_core_overnight_evaluation15 --bundle release_package/cqs/original_core_overnight_repairs15 --out /tmp/repair15-replay.json
```

Pass means two AI semantic judgments, pinned stored-source consistency, captured native executions, independent SQL agreement and actual scorer checks. Human and independent domain-expert reviews remain incomplete. These checks do not establish causal adoption, complete raw-archive coverage, calendar chronology, or physical-source truth for the entire graph.

Each cohort keeps its actual model, inputs, information access and denominator. Scores are not transferred to later contracts. The public source-order protocol differs from the first 37-question cohort; inherited exact-share hooks are inactive for the twelve ordinary tasks. Source-enriched experiments remain separate from these 475 frozen-graph contracts.

The index manifest links every historical cohort. The compact [review evidence archive](review_evidence.tar.gz), [Core402 archive](latest_additions.tar.gz) and [observed-trend archive](observed_trend.tar.gz) preserve the 400-, 402- and 404-item historical snapshots respectively. They do not contain the complete current index. Their original inventories, manifests and download verifiers are unchanged. Use this Git checkout and its pinned cohort files to replay the current contracts.

The named-Agreement proposal's historical `admitted: false` field is retained; completed validation is established by its pinned reviews, capture and bundle. Earlier pending triage inside historical ledger entries remains historical. Preparation, public upload and fresh anonymous download verification are distinct recorded states.
