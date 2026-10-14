# New evaluation of repaired original Core questions

This companion preserves new predictions from one model, `anthropic/claude-opus-4.8`,
restricted to the Anthropic provider without model fallback. The unchanged original
questions are evaluated under frozen, typed, requested-field contracts. The original
350-item cohort and the disjoint 21-item addition were fixed separately before their
model calls. Their union contains each of the 371 admitted IDs exactly once.

The original Core contains 560 IDs: 371 repairs are admitted (119 scorer-only and
252 query-and-scorer repairs), and 189 remain pending. The admitted set is not a
representative sample of all 560. No independent human/expert validation is claimed.

## Measured results

The following table includes every admitted ID. Execution failures and abstentions
receive F1=0 and exact=false, including an item whose gold answer is empty.
A parsed self-reported partial answer can receive record credit; it cannot establish
an empty-gold success. `analysis.json` also reports WG, phase, output shape,
multiple requested fields, all execution statuses, and paired bootstrap intervals.

| Method | N | Complete-record macro F1 | Exact output | Failures |
| --- | ---: | ---: | ---: | ---: |
| text2cypher | 371 | 0.6722 | 228/371 | 19 |
| text2sql | 371 | 0.0997 | 37/371 | 324 |
| single_retrieval | 371 | 0.0116 | 3/371 | 318 |
| iterative_retrieval | 371 | 0.0203 | 6/371 | 307 |

Original attempts and pre-provider transport recovery are reported separately
under `results/` and `retained_runs/`. Only recorded HTTP402 in-flight-budget or
HTTP403 key-limit failures with no provider response content were eligible for
recovery. Actual model responses, invalid queries, incomplete outputs, and incorrect
answers were retained without quality retries. Existing query executions, including
their failures, were reused only when their pinned generation and source guards matched.

## Interpretation and information access

Text2Cypher and Text2SQL use the same graph-derived records. SQL conversion checks
preserve types, duplicate/parallel relations, null semantics, and source snapshots.
The generated SQL results include many relationship-table naming and syntax errors:
physical tables use a `rel_` prefix. The frozen interface and these failures were
retained. Low SQL performance therefore does not establish an intrinsic limitation
of SQL or a causal advantage of graph storage.

The text cache contains 3,901,610 chunks from five RAN working groups, but equality
of its cutoff/content with the frozen graphs remains unverified. Single retrieval
allows one search; iterative retrieval allows one follow-up search and an additional
model call. Each answer context is limited to 12 documents, 4,000 characters per
document and 48,000 characters in total. Corpus presence and actual prompt-context
coverage are separate diagnostics. Finite retrieval cannot establish full-population
aggregates. Retrieval timeouts and incomplete outputs remain in the denominator.

Raw-document checks are limited to the explicitly linked examples in
`source_semantic_audit.json` and `repair_case_evidence.json`; successful graph execution
or agreement between AI reviewers is not full raw-document factual/completeness
validation. Source-first expert packets are prepared, with zero completed expert reviews.

## Offline verification and score replay

From the repository root, with Python 3 and no credentials or database:

```bash
python3 -B -S release_package/cqs/original_core_repair/verify_release.py
python3 -B -S release_package/cqs/original_core_evaluation/runtime/verify_evidence.py \
  --evidence release_package/cqs/original_core_evaluation \
  --bundle release_package/cqs/original_core_repair \
  --out /tmp/spectra_evidence_verification.json
```

The evidence verifier checks file/archive inventories, full prediction/status ID
coverage, repair hashes, and recomputes published complete-record scores with the
released scorer. It does not generate model answers or execute graph/SQL queries.
The frozen 350 and 21 contract bundles are also archived under `inputs/`.

Fresh generation requires the pinned graph snapshots, SQLite exports and local
retrieval corpus, Neo4j, and an explicitly configured OpenRouter credential.
Runtime scripts, frozen requests, responses, generated queries, executed rows,
protocols and usage receipts are retained so the original configuration can be
inspected. Do not resume an already completed run or transfer historical nine-model
scores to these contracts.

## Provenance and public privacy

The sibling original_core_repair manifest is `1b42bef40acce3497c0f8e5a693f18fc268196e1cd5b5abb7bf24be2fb5f186e`.
Private original attempts remain unchanged. Public raw artifacts mask only provider
account/key financial error details. `public_redactions.json` maps original and public
hashes and the affected fields; model input/output content and experiment cost/usage
are unchanged. Archive inventories distinguish published bytes from private originals.
Preparation, upload and external download verification are separate operations.
`scope.json` and `evidence_manifest.json` record the preparation state; publication
and independent download verification are recorded separately in the repository
publication handoff rather than being assumed from a staged directory.
