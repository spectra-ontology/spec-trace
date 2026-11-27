# Native query generation across four Codex configurations

This study compares native query generation with schema documentation and with added categorical values on SPECTRA's traceability questions. It supplies all 32 planned sessions, their preserved responses, 1,500 native query executions, 100 unanswered first-submission slots, and reproducible paired comparisons. The same 50 questions connect source-verified decisions, revisions, CR packs, release editions, and clauses through SQL and Cypher interfaces.

Sol, Astra, and Terra improve from 10/50 exact matches with schema documentation to 50/50 with categorical domains in every SQL repetition. Cypher exposes additional variation: Terra's domain-informed repetitions reach 50/50 and 43/50, while Luna produces execution failures, an empty batch, and a 23/50 repetition. These outcomes show how the resource distinguishes categorical grounding, query construction, and chronological reasoning under a common question set.

## Design and model configuration

The four configured model identifiers are `gpt-6.2-sol`, `gpt-6.2-astra`, `gpt-6.1-terra`, and `gpt-6-luna`. Each subject requests `medium` reasoning effort in a fresh Codex session. The provenance records bind requested identifiers to observed local `turn_context` configuration and session identifiers. These are local session configuration records; independent backend routing certification is outside the recorded metadata. The selected identifiers describe the versions offered for these conditions in this session.

The design crosses four configurations, two native languages, two documentation conditions, and two prespecified repetitions (A/B): 32 sessions and 1,600 planned question slots. Requested reasoning effort and the 50-question task are shared; actual token use and elapsed time are recorded where available, with no enforced common numerical token or time budget. The earlier matched-domain experiment remains in the sibling `matched_domains` study: four context-isolated Codex writers used their inherited configuration, with provider model IDs unavailable. Its four completed sessions retain their separate provenance and results.

The fixed cohort comprises 35 main questions and 15 order-extension questions across all five working groups. Selection minimizes SHA-256 of the anchor within each suite/WG/family cell, breaking ties by item ID. It uses the historical 667 main and 300 drawn extension candidates; all 15 selected extension questions belong to the 297 admitted items. Both languages and both conditions use identical question IDs, wording, requested fields, and order. `schema_domains` adds the same joint low-cardinality SQL/Cypher value dictionaries to `schema_only`. The scope-to-`assessmentMethod` interface mapping appears in both conditions.

Subjects receive their assigned frozen packet and instructions to read that packet and write their assigned submission once. Owner inspection of observed tool calls audits this instruction boundary. The preserved protocol, packet bytes, analysis addenda, and exposure audit document the actual conditions. Query authors receive no gold, examples, execution results, score feedback, or outcome-driven retry. Repetition B is prespecified for every cell and retains its first outcome.

## Results and complete first-submission accounting

Each cell below is meeting-identity exact unordered row-set matches out of the same 50 questions. A/B are separate first submissions. The retained electronic meeting spelling rule is shared with `matched_domains` and is executable in `analyze.py`.

| Configured model | Native language | Schema A | Schema B | Domains A | Domains B |
|---|---|---:|---:|---:|---:|
| `gpt-6.2-sol` | SQL | 10 | 10 | 50 | 50 |
| `gpt-6.2-sol` | Cypher | 10 | 10 | 50 | 50 |
| `gpt-6.2-astra` | SQL | 10 | 10 | 50 | 50 |
| `gpt-6.2-astra` | Cypher | 10 | 10 | 50 [I] | 50 |
| `gpt-6.1-terra` | SQL | 10 | 10 | 50 | 50 |
| `gpt-6.1-terra` | Cypher | 10 [I] | 10 | 50 | 43 |
| `gpt-6-luna` | SQL | 5 | 5 | 0 | 0 [W] |
| `gpt-6-luna` | Cypher | 10 | 0 [E] | 0 | 23 |

The two **[I] input-transport deviations** preserve incomplete RAN4 schema exposure after truncated tool responses. All 50 question records were visible and their query outcomes remain included above. In each type of comparison, the all-planned summary retains both pairs involving an affected session. The complete-input analysis uses the other 14 pairs.

The **[W] first-write assembly deviation** is Luna domains SQL B. The first successful write contains ten complete query objects inside an unfinished, unparsable JSON batch. A later append assembled 50 queries. The first-submission rule retains the exact first-write bytes and the later assembled response separately, records 50 unanswered slots, and executes zero queries from that session. The primary complete-input scope counts these unanswered slots in both the documentation and language contrasts. An additional sensitivity analysis uses pairs with conformant output assembly.

The **[E] empty first submission** is Luna schema Cypher B: its first saved response is `{"queries":[]}`. It contributes 50 unanswered slots and zero native queries. This valid empty batch contributes to the complete-input and output-assembly sensitivity analyses. These four records have distinct dispositions; all original responses remain available, with no rerolls or query repairs.

Of the 1,500 native query executions, Luna domains SQL A and Luna domains Cypher A each produce 50 execution errors; Terra schema Cypher A produces ten. The primary denominator retains these outcomes. Terra domains Cypher B has 35/35 exact main answers and 8/15 exact extension answers, with overall macro row-set F1 0.8870. Luna domains Cypher B has 19/35 main and 4/15 extension exact answers, overall F1 0.4600. `analysis.json` gives recorded-spelling, meeting-identity, strict raw, family, and execution/completion results for every session.

### Paired documentation comparisons

Entries show exact gains/losses when adding categorical domains, matched by question within each configured model, native language, and repetition. Each pair has 50 slots. [I] marks input delivery and [W] marks output assembly. All planned pairs remain visible.

The primary paired scope uses both first submissions in each of the 14 complete-input pairs. For Luna SQL B, the 5 to 0 change therefore contributes a decrease. The 13-pair sensitivity further requires conformant first-write assembly, retaining valid empty batches. This last scope is the historical `eligibleControlledContrast` flag. The analysis exports that flag, `completeInputPair`, and summaries for all three scopes under `pairedContrastScopes`.

| Configured model | Native language | A gains/losses | B gains/losses |
|---|---|---:|---:|
| `gpt-6.2-sol` | SQL | 40/0 | 40/0 |
| `gpt-6.2-sol` | Cypher | 40/0 | 40/0 |
| `gpt-6.2-astra` | SQL | 40/0 | 40/0 |
| `gpt-6.2-astra` | Cypher | 40/0 [I] | 40/0 |
| `gpt-6.1-terra` | SQL | 40/0 | 40/0 |
| `gpt-6.1-terra` | Cypher | 40/0 [I] | 33/0 |
| `gpt-6-luna` | SQL | 0/5 | 0/5 [W] |
| `gpt-6-luna` | Cypher | 0/10 | 23/0 |

The table counts pair-level directions by comparing exact counts on all 50 questions in each pair.

| Scope | Domains minus schema: improved / tied / declined | Cypher minus SQL: improved / tied / declined |
|---|---:|---:|
| All planned pairs (16 each) | 13 / 0 / 3 | 2 / 12 / 2 |
| Complete input (14 each) | 11 / 0 / 3 | 2 / 10 / 2 |
| Complete input and conformant output assembly (13 each) | 11 / 0 / 2 | 1 / 10 / 2 |

In the domain sensitivity, Sol and Astra's eligible pairs and Terra SQL gain +0.8000 macro F1. Terra Cypher B gains +0.6870. Luna changes by −0.1000 (SQL A), −0.2000 (Cypher A), and +0.4600 (Cypher B). In the language comparison, Terra domains B has a Cypher-minus-SQL macro F1 difference of −0.1130. `analysis.json` supplies every paired discordance and F1 difference for the full cohort, main subset, and extension subset.

These are descriptive comparisons on 50 fixed strata representatives. Repetitions measure new submissions on those same questions; the 667-item main and 297-item admitted extension evaluations retain their own population scope.

## Recompute the published results offline

Keep this directory at `studies/codex_model_comparison` with the sibling `studies/matched_domains` directory in the full release. Python 3.10 or later and its standard library are sufficient. From the release root:

```bash
python3 -B studies/codex_model_comparison/analyze.py --check
```

The checker verifies frozen protocol/input hashes and the study's `SHA256SUMS`, response/query commitments, exact original query strings, execution-row bindings, gold, first-write dispositions, every per-item score, and the resulting `analysis.json`. It makes no model or database calls. To verify the byte manifest separately:

```bash
(cd studies/codex_model_comparison && sha256sum -c SHA256SUMS)
```

Run `analyze.py` without `--check` in a working copy to recompute `analysis.json`. The scorer dependency, selected gold, and meeting-identity rules are pinned to files in `matched_domains`.

## Replay original SQL queries

`replay_queries.py` executes the preserved native query strings and writes a fresh receipt outside the study directory. Supply the five uncompressed `RAN1.sqlite` through `RAN5.sqlite` exports from the release's `sqlite/` directory; the distributed compressed files can be extracted into a working directory. Use Python linked to SQLite **3.37.2**, as recorded in the original executions:

```bash
python3 -B studies/codex_model_comparison/replay_queries.py \
  --language sql --sqlite-dir restored-sqlite \
  --out codex-model-sql-replay.json
```

The replay verifies each frozen database hash, opens SQLite in `mode=ro` with `PRAGMA query_only=ON`, and retains the original 60-second, 2,000-row, and requested-column-count rules. It replays the 750 original SQL queries, compares exact stored row sets, both gold scores, and error text, and rechecks unchanged database hashes. The first-write assembly outcome remains an unanswered batch. A replay receipt records a new verification run independently of the original experiment.

## Replay original Cypher queries

Cypher mode uses explicitly supplied Neo4j **5.26.0** native process graphs matching the frozen packet schema. Install `neo4j==5.28.3`, set `NEO4J_USER` and `NEO4J_PASSWORD` through your credential manager, and provide all five connection URIs:

```bash
python3 -B studies/codex_model_comparison/replay_queries.py \
  --language cypher \
  --bolt RAN1=bolt://localhost:7687 \
  --bolt RAN2=bolt://localhost:7688 \
  --bolt RAN3=bolt://localhost:7689 \
  --bolt RAN4=bolt://localhost:7690 \
  --bolt RAN5=bolt://localhost:7691 \
  --graph-identity 'provenance of the supplied native process graphs' \
  --out codex-model-cypher-replay.json
```

The replay checks the server version and native `DecisionDisposition.assessmentMethod` and `Meeting.workingGroup` inputs, then runs 750 preserved Cypher queries in read transactions with explicit rollback. It retains the original timeout, row cap, column count, and write/procedure guard, compares every outcome with its stored rows, gold scores, and error text, and records before/after graph populations. Environment-variable names and the database name are configurable through `--help`; credentials stay outside receipts. The command uses running services supplied by the reader.

### Restore a native input and replay one working group

[`native_restore/`](native_restore/README.md) supplies query-bound native property overlays over the release's complete graph topology. Its dependency file lists all 750 executed query digests and a conservative 29-property whitelist, including native `assessmentMethod` and `workingGroup`. Capture compares every node and relationship with the reused topology and checks two complete native projected-content fingerprints. Overlay maps retain the properties consumed by this study; the separate CQ workflow uses its own dependency projection for the 654 competency queries.

Prepare a dedicated, initially empty Neo4j 5.26.0 database and set its `NEO4J_USER` and `NEO4J_PASSWORD`. From the release root, restore and replay one working group with:

```bash
python3 -B studies/codex_model_comparison/native_restore/restore_and_replay.py \
  --working-group RAN1 --bolt bolt://localhost:17787 \
  --output-directory /tmp/spectra-ran1-restored-check
```

The command verifies source and helper hashes, composes the native graph, restores it into the empty target, checks its actual content and schema observations, applies source-bound indexes over retained properties, and runs the 150 preserved native queries for that working group. Fresh receipts identify the restored input separately from the original executions. Repeat for RAN1–RAN5 with a fresh graph and output directory for each group. The full release supplies the referenced base topology in `sources/competency_queries/graph_view/` and serializers in `restore/competency_queries/`; keep their relative release layout. The [input guide](native_restore/README.md) also gives database-free fingerprint checks.

## Completed native replay checks

Fresh verification reproduces all 750 preserved SQL outcomes against the hash-matched released databases, including 50 recorded execution errors. It also reproduces all 750 Cypher outcomes on the five portable restored inputs, including 60 recorded execution errors; every restored graph passes complete projected-content, source-order, and schema checks. The separate replay receipts preserve the original first-submission accounting: 50 unanswered SQL slots and 50 unanswered Cypher slots, for 100 in the 1,600-slot study. `replay_validation/` records comparison against original native inputs, and `native_restore/receipts/` records the restored-input checks and their administrative recovery history. These verification executions reuse the committed queries and original outcomes.

## Artifact map

- `frozen/`: prespecified protocol, packet bytes, cohort, schedule, preparation code, and their original lock.
- `submissions/`: all committed responses, receipts, and exact native query files for complete collected batches. The assembled SQL B file is preserved as an administrative record.
- `first_write/` and `first_write_deviations.json`: exact recovered initial bytes and evidence for the assembly disposition.
- `execution/`: original query copies, native rows, execution status, and recorded/meeting-identity scores for 30 executable batches.
- `provenance/` and `tool_scope_review.json`: session configuration, observed usage and tool-call digests, with the independent semantic tool-scope audit. Complete source traces remain in the owner audit.
- `input_*`, `output_deviation_analysis_addendum.json`, and `preflight.json`: input exposure, recorded exclusion decisions, and execution readiness evidence.
- `analyze.py`, `analysis.json`, and `replay_queries.py`: portable offline scoring, paired results, and separate fresh native replay.
- `replay_validation/`: separate fresh verification receipts for the preserved SQL and Cypher queries against their original native inputs.
- `native_restore/`: native property overlays, source-bound graph/index definitions, empty-target restoration commands, and their verification receipts; it reuses the full release's base graph topology.
- `owner_audit_sources/`: source snapshots for collection, exposure auditing, and original scoring coordination.
- `SHA256SUMS`: byte identities for this study's published files.
