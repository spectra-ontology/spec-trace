# SQL schema-interface intervention

This separate experiment provides the actual value-free SQLite DDL, including
physical relationship-table names and source/destination columns, for every
one of the previously frozen 378 contracts. The model, provider, original
questions, graph/SQL snapshot, generation budget and answer contract are pinned.
The original SQL predictions are preserved; this is not a selection of failed
questions or a replacement of the earlier published experiment.

| SQL interface | N | Complete-record macro F1 | Exact output |
| --- | ---: | ---: | ---: |
| Earlier interface | 378 | 0.097884 | 37/378 |
| Actual value-free DDL | 378 | 0.609694 | 215/378 |

The paired F1 difference is 0.511811 with a 95% bootstrap interval
[0.461694, 0.561586]. Final statuses retain 346 successful read-only SQL
executions, 23 malformed generation envelopes and 9 abstentions. There are
no final unresolved operational denials. Failures receive zero credit and remain
in the complete denominator. An answered item was never regenerated for quality.
Only the 129 pre-provider HTTP402 requests and the subsequent 20 requests blocked
before sending by the local budget guard were eligible for unchanged-payload
operational recovery. Their original failed attempts remain in the evidence.

Known actual experiment cost is $21.631390; three transport attempts have unknown
cost. One model, anthropic/claude-opus-4.8, uses the Anthropic provider only.
These results use the old 378 contracts, including definitions subsequently
superseded by the separate top-k repairs. They do not establish performance on
all later contracts or an intrinsic causal advantage of either storage medium.
There are no completed independent expert reviews.

The archive preserves protocols, DDL cards, original requests/responses,
generated queries, executed records, source guards, failures, usage, all scores
and paired analyses. Its documented privacy projection masks only private
account/key finances; model inputs, answers and experiment usage are preserved.

From the repository root, without credentials, model calls or database execution:

```sh
python3 -B -S release_package/cqs/original_core_sql_interface_evaluation/verify_archive.py
```

Local preparation, public upload and fresh unauthenticated download verification
are separate states; the presence of this package is not a download certificate.
