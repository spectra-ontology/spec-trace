# Fresh TOP10 replacement evaluation

This evidence contains new predictions for all ten existing Core IDs whose ranked reference pools were uncapped under separately validated top-k contracts. It adds zero unique original Core IDs. The original 371-item contracts and prior predictions remain preserved; no old score is transferred to a replacement contract.

The original generation phase and its fifteen pre-answer HTTP402 stages remain unchanged. A separately registered operational phase reissued only identical requests that had received no model answer, reused two previously received followup responses without new calls, and performed three first answer calls after recovered followups. Responses with format errors, abstention or partial content were not reissued. The current output selects all fifteen registered operational method-items and the other twenty-five original method-items, independently of their scores.

All four methods use the pinned Opus4.8 model and Anthropic-only provider, without model/provider fallback. SQL uses the actual complete physical value-free SQLite DDL. Native execution retains the fixed 100,000-row, 256 MiB and 60-second limits. Retrieval uses the frozen lexical protocol and bounded contexts; archive text cutoff equality with the graph remains UNKNOWN. No supplemental ownership/catalog source is provided in this phase. Complete-record scoring and failure gating include all ten IDs per method. Human/author/expert validation remains zero.

Offline verification requires the separately preserved TOP10 replacement bundle and its parent371 bundle:

```sh
python3 -B -S runtime/verify_topk_evaluation.py --evidence . --bundle /path/to/topk_replacements --parent /path/to/parent371 --out /tmp/topk_report.json
```

The verifier makes no API or database calls. It replays strict scores and paired analysis from stored actual outputs; live model or native database reproduction is a separate action. Raw requests omit authorization headers. The manifest pins every package file.
