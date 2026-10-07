# Retained matched measurement

This folder records a completed comparison on 36 source-defined task variants. The pool of 40 original question IDs was selected by a fixed hash rule across working groups and released track labels. Source execution and declared output types determined eligibility before model generation: 36 qualified and four did not. All 36 use explicit task variants; their original IDs and questions remain available in the fixtures. These results do not replace the released Core 560 scores or certify the original questions' semantics.

| Arm | Mean complete-record F1 | Exact output match |
| --- | ---: | ---: |
| Single lexical retrieval | 0.000000 | 0/36 |
| Two-round lexical retrieval | 0.011188 | 0/36 |
| Structured query generation | 0.783356 | 27/36 |

The [primary report](matched_measurement_report_v1.json) contains every task, subgroup, paired interval, failure and captured cost. The scorer compares required named fields, types and collection semantics against graph-relative reference records. Its semantic exactness remains unresolved; no independent domain experts validated these variants. The [supplementary execution replay](supplementary_execution_replay_analysis_v1.json) is separate from the primary measurement.

The two text arms share one retained live text corpus, lexical index and final reader configuration. Single retrieval searches once. The iterative arm generates one grounded follow-up query, searches again and merges ranks using RRF with `k=60`. Both readers receive up to ten passages of at most 800 characters, with at most six per collection. The iterative helper adds 36 model calls and additional usage. This is a bounded adaptation informed by [IRCoT](https://aclanthology.org/2023.acl-long.557/) and [Iter-RetGen](https://aclanthology.org/2023.findings-emnlp.620/), with [RRF](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf); it is not a complete reproduction of either retrieval method.

The structured arm generates a read query over the restored deposited graph. It has graph access beyond the text readers' capped passages, and the live text cutoff is not certified equal to the deposited graph cutoff. Comparisons involving that arm are descriptive and cannot isolate a causal benefit of graph storage. Three primary structured trials failed query validation or execution and remain in the denominator. Across all arms, 144 model CLI invocations were captured; the separate setup probe is not a scored task. The requested model was `gpt-6.1-sol` with medium reasoning effort. The full built-in system prompt, actual provider backend model identity and internal HTTP retries were not observed.

## Reproduce the scores without model calls

From the repository root, run:

```bash
python3 -B release_package/cqs/contract_repair_v1/matched_retrieval_measurement/matched_analysis.py \
  --require-complete --out /tmp/spectra-matched-replay.json
```

Use a new output filename; the script refuses to overwrite a report. This reads the shipped predictions, caller metadata, task definitions, eligibility, graph-relative reference records and scorer. It needs Python 3.10 or later and its standard library. It does not contact a model, graph database or text service. Scores, subgroups and paired bootstrap intervals use the fixed [analysis protocol](scientific_analysis_protocol.json).

The prediction and call files retain the reader contexts, questions, declared output contracts and outputs. [The caller sidecar](caller_returncodes_v1.json) preserves process return codes and tool-action counts without raw transport logs. [The build registry](publication_build_registry_v1.json) identifies original and published hashes and records sanitization. Host filesystem paths, authentication material and raw stderr/events are omitted. The [current delivery manifest](public_delivery_manifest_v3.json) lists the current companion and its transformations. Earlier packing lists record local snapshots before the final documentation link and credential-pattern audit were added.

The [isolated replay verification](isolated_public_replay_verification_v1.json) records exact reproduction of scores, subgroups, intervals and costs from copied public inputs without git metadata or network access. To repeat that check:

```bash
python3 -B release_package/cqs/contract_repair_v1/matched_retrieval_measurement/verify_public_replay.py \
  --out /tmp/spectra-matched-portability-check.json
```

## Inspect the retrieval implementation

```bash
python3 -B release_package/cqs/contract_repair_v1/matched_retrieval_measurement/implementation/matched_retrieval.py self-test
python3 -B release_package/cqs/contract_repair_v1/matched_retrieval_measurement/implementation/test_matched_retrieval.py
```

The published [implementation](implementation/matched_retrieval.py) includes payload extraction, the SQLite FTS5 corpus schema, retrieval, bounded snippet merging, typed output validation, prompt construction and the shared CLI caller. Its output location was changed to an explicit `KDD_MATCHED_OUTPUT` directory or local `local_run`; the transformation is recorded. The original scientific runner and its frozen hashes were preserved. This portable copy is therefore not byte-identical to that original runner.

The complete retained SQLite ranking corpus contains 3,901,610 text chunks and occupies 19,779,813,376 bytes (about 18.42 GiB). It is not included or newly deposited here. Stored hits and prompts support inspection and score/reader-input replay; reproducing the original full lexical ranking requires that retained corpus. The source snapshot hashes, actual physical checks and execution audit are in [provenance](provenance). No full-corpus retrieval reproduction, expert validation, outside-RAN transfer or missing-evidence abstention evaluation is claimed by this folder.
