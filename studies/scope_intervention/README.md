# Portable replay of the paired scope intervention

This CLI replays the separate follow-up intervention on all 298 frozen stored SQL failures (198 unique WG/item pairs across three sessions). It uses the released evaluator functions, the original 60-second query limit, and the frozen Python 3.10.12 / SQLite 3.37.2 runtime. All original model scores remain the recorded scores.

Keep `replay_scope_intervention.py` and its `payload/` directory together. Supply the public release checkout and a new scratch output directory; the command works from any working directory and requires no `AGENTS.md` file.

```bash
python -B replay_scope_intervention.py \
  --release /path/to/spec-trace \
  --output /path/to/new-scratch-output
```

The CLI checks its runtime and every frozen release input before executing. It decompresses the two hash-pinned SQLite databases into scratch, opens them as read-only immutable databases, and loads only imports and functions from the byte-preserved original intervention script. The original `solve_text2sql`, `score`, and paired replay functions perform execution and scoring. Explicit command-line paths replace the original workspace discovery. A single worker, the original query progress handler, the original batch checkpoint, and a 2 GiB process limit apply.

Scratch contains the frozen manifest/protocol/pin, decompressed databases, `paired_results.jsonl`, `summary.json`, the evaluator's `full_execution_receipt.json`, and `portable_replay_receipt.json`. The portable receipt records the wrapper and frozen-source hashes, before/after release-input hashes, and a comparison of all 298 pairs with the original results. It compares complete normalized row sets, gold sets, question/query hashes, scores, errors, status and returned row counts. Execution times and physical row order may vary. An incomplete batch or any mismatch makes the command fail while retaining its scratch evidence.

The payload preserves the original 298-case manifest, protocol, script, pre-execution pin, and original paired results without editing their bytes. The replay is a controlled change to a stored SQL literal in three recorded sessions. It provides a result for this fixed database snapshot and does not generate new model responses.

`validation_receipt.json` records an actual fresh replay against the independent public checkout, whose directory and ancestors contained no `AGENTS.md`. All 298 pairs (596 SQL executions) matched the frozen outputs on every compared field, with zero comparison differences and unchanged release inputs. This validation took 151.60 seconds. Its fresh raw outputs are preserved in `validation_paired_results.jsonl`, with execution metadata in `validation_execution_receipt.json` and the progress log in `validation.stdout`. The fresh raw result SHA256 is `b6210b66356446e2e6dad47f10279716eb7b907f6eafda58942ab7cdd3e652ce`.
