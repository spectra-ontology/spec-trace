# First SQL responses on the fixed semantic-witness questions

This author-side follow-up executes one fresh Codex session's first SQL response on all 66 existing semantic-witness tasks. The writer received only the frozen questions, SQL schema, identifier conventions and complete relevant categorical domains. It received no database access, reference/control SQL, gold answers, previous measurements or execution feedback. The first response was frozen in full before evaluation. The service is recorded; its exact provider model identifier is unavailable.

The original 66 tasks span seven operator families and 65 distinct family/anchor pairs. Every task and its existing gold answer is retained in the original order, using masked writer IDs W001–W066. This is a separate fixed-data follow-up to the 30-item pilot, rather than another run of the original Opus experiment. The protocol was fixed after the earlier studies and before this writer's output.

The pinned SQLite 3.37.2 execution returned exact complete row sets on 66/66 tasks, with zero errors and zero timeouts. Every task's SQL, full returned rows and missing/extra row lists are retained in `first_response_execution.json`. The seven families give 26/26 grouped pack counts, 8/8 conjunctions, 6/6 intersections, 6/6 differences, 10/10 maximum footprints, 5/5 absence tasks and 5/5 aggregation compositions. Input databases and compressed source hashes were unchanged.

The result establishes successful query writing in this supplied-domain condition on the fixed tasks. Semantic witnesses still measure the data's ability to expose specified operator errors; their control-detection rates have a different denominator and purpose. The result describes one session and these tasks. The independent execution audit is recorded separately under `independent/`.

Run from the public artifact root with an interpreter whose `sqlite3.sqlite_version` is exactly 3.37.2:

```bash
python3 -B studies/semantic_witnesses/first_queries/evaluate_first_response.py \
  --frozen studies/semantic_witnesses/first_queries/frozen \
  --responses studies/semantic_witnesses/first_queries/first_response.json \
  --output /tmp/spectra-witness-first-replay.json \
  --release . \
  --database-directory /tmp/spectra-witness-first-databases
```

The evaluator is byte-identical to the previously released 30-item pilot evaluator. It verifies frozen file hashes, requires a new output path, opens databases read-only, caps each query at 60 seconds and compares complete normalized sets. A compressed database is materialized into the scratch directory as needed. New model generation is outside this replay command; it executes the preserved first response.

The independent [portable checker](independent/portable_check.py) reads raw relations and computes gold with Python sets and grouping, reexecutes all 66 submitted queries and all 66 references, and checks the complete original witness-to-masked-ID mapping. Its [execution receipt](independent/portable_receipt.json) records 875 passing checks. This is author-side independent-code validation. Run it from the artifact root after selecting the pinned interpreter:

```sh
/usr/bin/python3 -B studies/semantic_witnesses/first_queries/independent/portable_check.py \
  --release . --database-dir /tmp/spectra-witness-first-databases \
  --output /tmp/spectra-witness-first-independent.json
```
