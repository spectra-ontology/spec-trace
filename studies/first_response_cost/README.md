# First-submission batch accounting

This study connects each retained solver batch to its released question packet,
original answers, initial execution records and first caller-delivered completion.
It covers 265 sessions across seven routes. Explicit completion events establish
264 cutoffs; the dense-tool RAN4 runB part3 record retains its unresolved status.
All 220 sessions in the five headline routes have identified cutoffs.

Run from the release root, using Python 3.10 or later:

```bash
python3 -B studies/first_response_cost/analyze.py --out /tmp/first_response_cost.json
python3 -B studies/first_response_cost/test_accounting.py
```

The analyzer verifies the evidence hashes, packet/answer IDs, initial query text,
question hashes and recorded execution seconds before aggregating the public
anonymous ledger. The five regression checks cover late repairs, streamed usage,
enforced handback delivery, missing acknowledgments and unresolved completions.

## Measurement

The initial interval starts at the first timestamped session record and ends at
the first completed caller delivery. A `SubagentHandback` call includes its
successful tool-result acknowledgment. An ordinary `end_turn` ends the interval
when it delivers the result; a harness request to deliver that report through
`SubagentHandback` includes the required handback in the initial interval.
Execution-error feedback and the resulting repair belong to the subsequent
interval. Each assistant message ID contributes its final recorded usage once.
The anonymous ledger preserves message hashes, line numbers, timestamps, token
usage and tool counts. Its transcript hashes identify the retained private
sources. Raw session text stays in the source archive.

SQL and Cypher each use 50 whole-WG batches covering 6,670 question instances.
Chunk and document-body search each use 45 one-third-WG batches covering 2,001
instances; raw search uses 30 batches covering 1,334 instances. Elapsed seconds
divided by batch size describe this recorded batch workload. Query routes add
the separately recorded initial database execution time; document routes execute
their retrieval tools inside the session. Inputs count processed new tokens,
cache writes and cache reads. These units support batch resource accounting.

## Results

| Route | Completed sessions | Instances | Processed input / instance | Median elapsed / batch item | Mean elapsed / batch item |
|---|---:|---:|---:|---:|---:|
| SQL | 50 | 6,670 | 5,672.81 | 2.6480 s | 3.3160 s |
| Cypher | 50 | 6,670 | 4,756.39 | 2.2699 s | 2.4189 s |
| Chunk search | 45 | 2,001 | 141,087.46 | 18.9916 s | 19.6755 s |
| Document bodies | 45 | 2,001 | 282,765.33 | 31.2817 s | 55.8097 s |
| Raw document search | 30 | 1,334 | 252,254.07 | 31.7063 s | 34.5499 s |

The SQL and Cypher processed-input ratios to raw search are 2.24885% and
1.88556%. The separate subsequent interval contains 775,795 SQL input tokens
and 1,055,790 Cypher input tokens. Its elapsed span includes the coordinator
waiting period before repair feedback.

All 100 query batches identify their original answer filename in the initial
completion report. All 13,340 initial execution records contain exactly one
attempt whose query text equals the corresponding retained original query.
The four sessions receiving repair feedback store repairs in separate files.
Their original generators and pre-submission source edits were recovered from
the retained transcript and executed against an in-memory filesystem; the four
recovered JSONL artifacts match the retained originals byte for byte.
`initial_artifact_recovery.json` contains the anonymous receipts. This binds
the first-stage accounting to the initial execution artifacts.

`build_records.json` records the 3,573.48-second disposition build from prepared
document text and the verified 358,062-record result. `summary.json` also exposes
descriptive build-time equivalents under the observed unequal batch sizes. It
uses exact seconds and rounds an item threshold upward: median equivalents are
123 SQL items and 122 Cypher items; mean equivalents are 115 and 112. The
underlying batches provide the interpretation of those arithmetic values.

## Evidence and regeneration

- `sessions.jsonl`: anonymous session boundaries, cutoffs and released-artifact pins.
- `message_usage.jsonl`: one usage record per unique assistant message.
- `collection_receipt.json`: population and unresolved-cutoff receipt.
- `initial_artifact_recovery.json`: recovery receipts for the four repaired sessions.
- `evidence_manifest.json`: byte counts and hashes of the accounting evidence.
- `summary.json`: replayable route aggregates and processed-input ratios.

`collect.py` regenerates the ledger from the retained source tree and private
session archive. `recover_initial_artifacts.py` regenerates the four recovery
receipts using those same private inputs. Public analysis uses the anonymous
outputs above.

```bash
python3 -B studies/first_response_cost/collect.py \
  --source-base /path/to/retained/paper/logs \
  --package . \
  --transcript-root /path/to/retained/session/archive \
  --out studies/first_response_cost
python3 -B studies/first_response_cost/recover_initial_artifacts.py \
  --source-base /path/to/retained/paper/logs \
  --transcript-root /path/to/retained/session/archive \
  --evidence studies/first_response_cost
```
