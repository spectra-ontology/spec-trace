# Matched categorical-domain interface diagnostic

This study gives SQL and Cypher writers the same 50 question/field records and the same joint categorical-domain appendix through their native schemas. Two first submissions per language each achieve 50/50 exact row-set matches in the stored executions. All 200 stored rowsets also equal the selected gold under strict raw row-set comparison. These are four observations of each of 50 fixed strata representatives, supporting a descriptive interface diagnostic at that scope. The full 667-item main and 297-item admitted extension results remain the population evaluations.

| Run | Main strata | Extension strata | Exact row sets | Recorded row-set F1 |
| --- | ---: | ---: | ---: | ---: |
| SQL A | 35 | 15 | 50/50 | 1.0000 |
| Cypher A | 35 | 15 | 50/50 | 1.0000 |
| Cypher B | 35 | 15 | 50/50 | 1.0000 |
| SQL B | 35 | 15 | 50/50 | 1.0000 |

The frozen selector minimizes SHA-256 of the anchor within each suite/WG/family cell, breaking ties by item ID. Its actual candidate pool contains 967 records: 667 main and 300 drawn extension records. The resulting fixed 35 main and 15 extension representatives are preserved; all 15 selected extension records also belong to the separately released 297-item admitted extension set. The original protocol and candidate files retain this distinction.

Four context-isolated Codex writers submitted their first queries with zero execution feedback. The session receipts record the inherited Codex configuration; provider model IDs are unavailable. Assignments were issued in the planned order and sessions overlapped, as the execution pin records. This is a separate Codex diagnostic whose design supports descriptive scores on the fixed sample; causal effects and model rankings require additional evidence. The original protocol's requested Opus invocation reached a subscription limit before any model response; its measurements are zero, and the separate Codex protocol governs these four completed runs.

## Frozen evidence

| Location | Contents |
| --- | --- |
| `frozen/` | Original writer packets, categorical domains, selection, design protocol, parity audit, full selection candidate pools, and the admitted extension contract |
| `provenance/` | Codex protocol, pre-execution pin, generation metadata input, and four original writer receipts |
| `queries/` | Original first-submission JSONL, with query text preserved |
| `gold/` | The 50 selected items and withheld gold used only for scoring |
| `execution/` | Original executed rowsets, errors/statuses, query serialization, metrics, summary, and generation metadata |
| `evidence/` | Original execution/scoring source snapshots and the meeting-identity source used by the original scorer |
| `provenance_manifest.json` | Original paths, complete file SHA-256 values, byte counts, and roles for every copied artifact |
| `validation/` | Actual package check, SQL replay, and mutation-control receipts |

The `.snapshot` files preserve execution provenance as inert text. The portable runners below use the Python standard library and read the frozen artifacts directly.

## Offline reproduction

From the release root:

```sh
free -h
python3 studies/matched_domains/rescore.py --out matched_domains_offline.json
```

The checker verifies all copied artifact hashes, protocol and query pins, the exact hash-minimum selection from the full candidate pool, selected-extension admission, writer question/domain parity, and query → packet ID → selected gold → executed rowset bindings. It recomputes recorded and meeting-identity metrics and the complete original summary. Recorded metrics use trim/lower-case and the original `bis` spelling rule; identity metrics additionally apply the original meeting rule with its retained `ran1#100-e` exception. A strict raw row-set comparison is also reported. The directory is self-contained for this check, including all selection and normalization sources.

## Optional SQL execution

Provide a directory containing the five frozen uncompressed `RAN1.sqlite` through `RAN5.sqlite` exports. The release contains the same exports in `sqlite/`, with RAN2–RAN5 compressed for distribution. After extracting them into a working directory, run from the release root:

```sh
free -h
python3 studies/matched_domains/rescore.py --sqlite-dir restored-sqlite --out matched_domains_sql.json
```

This mode requires the original SQLite 3.37.2 runtime, verifies the database hashes, sets `mode=ro` and `PRAGMA query_only=ON`, and reexecutes the original 100 SQL queries with the original 60-second and 2,000-row caps. It compares each result to its stored raw rowset and confirms unchanged database hashes. The offline mode also verifies all 100 stored Cypher executions; live Cypher execution belongs to the original execution evidence and the independent methods replay.

## Mutation control

```sh
free -h
python3 studies/matched_domains/mutation_control.py --out matched_domains_mutations.json
```

This control changes a query file in a temporary copy, then exercises stored-query and stored-row mutations in separate deep copies after the baseline check. The expected hash, query-binding, and score-recomputation rejections are saved in the receipt. The distributed evidence stays frozen.
