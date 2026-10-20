# Three original questions: separate fresh evaluation

This N3 cohort evaluates the original RAN1 recorded SSB-burst content and RAN1/RAN2 recent Release Tdoc lists. Registration starts from491 active contracts; prospective494/14/52 is not a publication claim. Earlier cohorts and scores remain separate.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 3 | 0.0000 | 0/3 | 0 |
| text2sql | 3 | 0.0000 | 0/3 | 0 |
| single_retrieval | 3 | 0.0000 | 0/3 | 3 |
| iterative_retrieval | 3 | 0.0000 | 0/3 | 3 |

All four methods retain all three questions, including errors, partial answers and abstentions. Fifteen first-call stages use the unchanged protocol. All actual requests, responses, usage, generated queries, execution failures and scores are retained. Quality retries0; human/expert validation0.

SSB returns recorded plain content with own notes, rather than certifying current normative wording. The two recent-document questions follow their own authored meeting-recency policies, not upload-time sorting. Exact archived full five-column native records are reused and compared with fresh SQL; historical native execution is not presented as a new run. Original-source selection boundaries and the distinction between recorded plain text and active tracked-change text remain explicit. Source verification does not enrich model inputs.

Offline replay uses no API, live database or retrieval query:

```sh
python3 -B -I runtime/verify_authorized_incremental27_evaluation.py --evidence . --bundle ../original_core_overnight_repairs27
```

Large graphs, databases and retrieval indexes are omitted. Source manifests and original protocol pins remain. Raw local paths are provenance, never offline dependencies. No graphwide factuality, full original-source rendering or expert certification is claimed.
