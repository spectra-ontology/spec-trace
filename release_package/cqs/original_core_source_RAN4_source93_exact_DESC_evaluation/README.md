# RAN4 source93 separate saved evaluation

This is an offline saved first-attempt evaluation supplement for one unchanged original question on a separately source-enriched graph. It adds zero original560 admissions and is not pooled with historical cohorts. Each method has N=1. Text2Cypher and Text2SQL each have complete-record F1=exact1; single retrieval is a valid partial answer with zero matches (F1=0), while two-round retrieval fails the unchanged strict whole-content parser (F1=0). All failures remain in the denominator. No model answer or generated query is replaced.

Five first-attempt HTTP200 calls had provider-reported Decimal cost $0.446060 and zero quality/transport retries. Expert validation N=0. No claim of causal superiority, equal source exposure or retrieval completeness follows from shared underlying facts.

```sh
python3 -B -I verify_package.py --output /tmp/ran4-source93-saved-replay --source-evidence ../original_core_source_RAN4_source93_exact_DESC
```

Choose an output directory that does not exist. Without `--source-evidence`, the sibling directory shown above is used. This command checks immutable archive/source pins, safely extracts the saved evidence outside the package, and runs the saved prompt/parser/scorer verifier in isolation. It makes no provider call, opens no database, runs no search or query, and starts no container. The3 large derived TTL/SQL/FTS sources remain omitted with their historical pins; their contents are not revalidated by this replay. Source correctness and documented acceptance limits are separately described in the source package. Documentary acceptance is not proof of physical-floor timing, TSG approval or normative incorporation. Historical absolute paths are retained as provenance only; no host fallback is allowed.
