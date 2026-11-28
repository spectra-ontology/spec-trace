# Output identifiers in SQL answers

The fixed 667-question study includes 10 repetitions of each SQL writer. A query can find the requested entity and still return its internal record key in a field that calls for a document number, meeting label, disposition code, or pack number. For example, Fable returned `tdoc:R4-2419837` for the final document in the R4-2418926 revision chain. The frozen document table maps that key to the requested number `R4-2419837`. The disposition and pack already agree with the reference answer.

We examined this pattern after inspecting the outputs. For each requested field, the diagnostic applies an exact key lookup in its working group's released SQLite export. It maps `document.id` to `document.number` for document and final-document columns, `meeting.id` to `meeting.label` for working-group and plenary meeting columns, `cr_pack.id` to `cr_pack.pack_number` for pack columns, and `disposition.id` to `disposition.code` for disposition columns. Each lookup changes only matching output cells. The diagnostic passes the translated rows to the original identity scorer, which compares sets. A disposition code can describe many records, so agreement on that field establishes agreement on the requested code. The benchmark score uses the writer's original output.

Among Fable's 6,670 SQL assignments, 2,099 originally returned the exact set. Another 3,450 returned a nonempty incorrect set. In all 3,450, field-specific key lookup recovered the reference answer. These observations span 501 distinct questions. Three relations account for the changes in this model: documents, meetings and packs.

Across all eight models, 5,654 of 53,360 SQL assignments returned a nonempty incorrect set. The lookup recovered all 5,654, covering 521 distinct questions. The cases occurred in Fable (3,450), Opus (1,044), Haiku (960) and Sonnet (200). The four Codex writers returned 7,905 exact sets, 18,673 empty sets for a nonempty reference answer and 102 execution errors. The complete SQL census includes the original scores, transformed scores and per-model and per-family breakdowns. [Eight-model census](all_sql_projection.json)

Run from the release root with Python 3.10 or newer. Adjust the script location to its directory in the study.

```sh
python3 -B studies/repeated_query_writers/identifier_projection.py --release .
python3 -B studies/repeated_query_writers/identifier_projection.py --all-models --release .
```

The script verifies the digests of the five SQLite exports. Supply `--sqlite-dir DIRECTORY` to use uncompressed copies. The default reads the release's `sqlite/` directory and decompresses one export at a time. For each nonempty incorrect output, the script binds a deduplicated row set to the original returned-set fingerprint in `full667.jsonl.gz`, resolves the requested display fields and repeats the score. The Fable check covers 50 working-group batches and uses 801 question-and-result-set witnesses. The receipt includes the original and diagnostic totals by family and the example's actual rows.
