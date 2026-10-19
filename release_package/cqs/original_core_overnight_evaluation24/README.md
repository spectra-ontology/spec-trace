# Three named original questions: separate fresh evaluation

This N3 cohort preserves the exact original English and authored lookup queries. The independent publication scope starts from the observed 484-task baseline. Registration, public integration and anonymous replay are separate ROOT-owned states; packaging does not establish them. Earlier cohorts and their scores remain separate.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 3 | 1.0000 | 3/3 | 0 |
| text2sql | 3 | 1.0000 | 3/3 | 0 |
| single_retrieval | 3 | 0.0000 | 0/3 | 2 |
| iterative_retrieval | 3 | 0.3333 | 1/3 | 0 |

Every method retains all three questions, including query errors, strict parser failures, empty outputs and abstentions. Fifteen planned stages use the unchanged frozen four-method protocol. Saved original request payloads, every actual response attempt, usage, generated queries, execution failures, scores and actual operational receipts are retained. No answer-quality retry or historical-score transfer is allowed.

The finite full header fields and nullable company/spec roles follow the exact seven-unit contract. JSON null, string None, missing attributes and empty strings remain distinct. Register submitting-company relations do not imply corporate affiliation; CR modifies means a recorded requested target and does not imply approval or incorporation. Human/expert validation remains0; reviews are nonblind AI development checks.

Offline replay uses no API, live database or retrieval query:

```sh
python3 -B -I runtime/verify_authorized_incremental24_evaluation.py --evidence . --bundle ../original_core_overnight_repairs24 --out /tmp/AUTH24-offline-replay.json
```

Complete graph/text cutoff equality and graphwide source factuality are not established. Large frozen graphs, relational databases and retrieval indexes are omitted; source manifests/protocol pins are preserved. This verifies saved results and strict scoring rather than rerunning queries. Original local paths inside raw receipts are provenance, never offline dependencies. No storage-medium causal advantage or representativeness is claimed.
