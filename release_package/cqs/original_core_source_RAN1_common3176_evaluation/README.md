# RAN1 common3176 source-variant first-attempt results

This separate cohort evaluates three unchanged questions on one common source-enriched RAN1 graph: SRS configuration, PUCCH resources and DMRS patterns. It adds **zero** admissions to the original560. The current original-question partition remains483 verified,14 requiring clarification and63 awaiting evidence.

All15 first-attempt calls are retained, including failures. The fixed model was `anthropic/claude-opus-4.8`, restricted to provider Anthropic without fallbacks; provider-reported cost totals **$1.463315**. This is saved usage, not a verified account balance. There were no quality retries.

| Method | N | Primary complete-record macro F1 | Exact | Primary failure attribution |
|---|---:|---:|---:|---|
| Text2Cypher |3|0|0|Three local dependency failures before native query execution |
| Text2SQL |3|0|0|Three complete SQL executions with incorrect relationship joins |
| Single retrieval |3|0|0|Three strict answer-parse failures |
| Two-round retrieval |3|0|0|Three strict answer-parse failures |

ROOT launched primary Cypher execution with Python isolation that excluded the already installed Neo4j driver. This was an execution-preflight omission. The primary failures do not establish that all three generated queries are wrong. A **separate environment-only diagnostic**, with unchanged generated query/source/reference/scorer bytes and no further model call, gives SRS exact1, PUCCH exact1 and DMRS CypherSyntaxError0 (Cypher diagnostic macro F1=2/3, N3). It does not replace or pool with the primary results.

SQL prompts used verified physical table/column metadata. The generated SQL nevertheless joined the Agreement-to-AgendaItem relationship to Meeting; all three saved complete10-row answers have zero reference overlap. Six retrieval responses contain prose and fenced JSON despite the JSON-only instruction and requested response format. Their original strict parsers reject them; extracting the inner JSON would change the evaluation. Operational errors, parse failures and model-declared abstention are distinct events.

Download the adjacent [source evidence](../original_core_source_RAN1_common3176/README.md) as well as this directory. To unpack into a new directory and replay saved outputs offline:

```sh
python3 -B -I verify_package.py --output /new/saved-evidence-directory
```

For a different source location, add `--source-evidence /path/to/original_core_source_RAN1_common3176`. The archive contains199 files (9,032,685 uncompressed bytes). The verifier rehashes the71 source files, bridges158 included pre-call pins (58 shared source files and100 evaluation files), reconstructs15 exact prompts, checks raw first responses and exact Decimal cost, and recomputes12 primary and3 diagnostic scores. The3 large TTL/SQL/FTS artifacts remain explicit provenance pins; they are not duplicated in this archive or opened by this replay. The source directory provides a separate rebuild recipe.

The ten-report source extraction reproduces3,176 literal windows and52,981 body blocks. Known foreign-contribution boundary counterexamples remain disclosed. This is not certification of all3,176 ownership boundaries or complete technical-topic semantics. The three semantic reviews are nonblind AI reviews; human expert validation N=0. Bounded retrieval and shared graph facts do not establish equal information exposure or a causal method comparison. All original/frozen evidence, unsuccessful attempts and diagnostic separation remain intact.
