# Two-reader disposition study

This bundle connects the recorded two-reader comparison to its sample, original
reader inputs, reader labels and source files. It reproduces the 1,000-record
source-verified result: 98.5% code agreement, Cohen's κ = 0.980528, 997 supported
and 3 jointly contradicted records. On the 997 code-supported records, the stored
scope equals at least one reader's scope in 994 cases. The same workflow checks
the separate 100 pending records and 35 diagnostic rereads. One record occurs in
two sets, giving 1,134 distinct packets.

The archived protocol used a Claude Code subagent for reader A and Codex CLI
(`gpt-6.1-sol`) for reader B, one session per part. Their code and scope labels are
preserved. The three label-aware follow-ups remain separate from the blind
comparison; their performer was unrecorded. The confidence interval estimates
joint-reader contradiction under this protocol. The observed reader agreement
and the follow-ups support a source-bound interpretation of the disposition
codes.

## Recompute labels and statistics

From the release root, run:

```sh
python3 -B studies/disposition_reading/replay.py --release . \
  --mutation-checks --out work/disposition_reading/replay.json
```

This uses the Python standard library, reads the released disposition population,
reselects the frozen SHA-256-ranked samples, checks all packet and reading IDs,
and recomputes the complete comparison. Exact Clopper–Pearson bounds are
calculated by binomial-tail inversion; a tolerance of 1e-12 absolute or 1e-11
relative covers numerical differences from the archived SciPy calculation.
All labels, integer counts and memberships compare exactly. Mutation controls
exercise missing packets, duplicate reader IDs and changed evidence/source hashes.

## Reconstruct the actual reader packets

Report text is represented by source hashes, locators, block digests and packet
digests. The source manifest is a selected subset of
[`sources/manifest.jsonl`](../../sources/manifest.jsonl), using the existing
archive/member/conversion recipes. Restore the selected report files locally:

```sh
python3 -B restore/restore_sources.py \
  --manifest studies/disposition_reading/sources.jsonl \
  --dest work/disposition_reading/sources \
  --work work/disposition_reading/downloads \
  --report work/disposition_reading/restoration.jsonl
python3 -B studies/disposition_reading/replay.py --release . \
  --source-root work/disposition_reading/sources \
  --mutation-checks --out work/disposition_reading/source_replay.json
```

Use the source-restoration dependencies and conversion setup described in
[`REPRODUCING.md`](../../REPRODUCING.md). Restored documents retain their source
terms. The replay uses accepted Word body text, the original four-block context
on either side and the original 4,000-character truncation rule. The portable
loader pins the archived Word-reader file's SHA-256 and binds its project-root
variable to the supplied release code tree in memory. Parsing functions and
archived source bytes are preserved. It checks each
block, each complete packet and all 17 original part-file hashes. These exact
hash comparisons connect the public manifest to the original packets, whose
shown fields were `packetId`, `wg`, `target`, `report` and `blocks`; record codes,
scopes, quotes, rule names, evidence status and sample membership were withheld.

## Files and provenance

| File | Role |
|---|---|
| `plan.json`, `codebook.md`, `reader_prompt.txt` | Byte-preserved archived protocol and reader instructions. |
| `keys.json`, `build_summary.json` | Byte-preserved hidden labels, set membership, sample census and part inventory. |
| `sampling.json` | Frozen sampling seed, selected IDs and diagnostic-cohort binding; checked against the released population. |
| `packets.jsonl`, `sources.jsonl` | All 1,134 packet manifests and selected source-restoration recipes. |
| `readings/A.jsonl`, `readings/B.jsonl` | Original code/scope labels; copied evidence is represented by character count and SHA-256. |
| `comparison.json` | Original comparison with copied evidence projected to the same character counts and SHA-256 digests. |
| `followups.json` | Three archived jointly contradicted cases and the archived follow-up interpretations. |
| `provenance.json`, `reader_B_runs.jsonl` | Original artifact hashes, recorded reader identities and available B-run receipts. |
| `protocol/` | Archived builder and scorer source, retained for inspection in their original repository layout. |
| `replay.py`, `SHA256SUMS` | Portable validation, scoring and complete bundle checksum inventory. |

`provenance.json` distinguishes original-file hashes from the hashes of these
text-free projections. The archived plan's `fixedBeforeReading` declaration is
preserved as recorded. This publication export adds an auditable replay path to
the existing study; it preserves the original labels and measured comparison.

## Finite benchmark-dependent identity inspection

[`finite_identity/`](finite_identity/README.md) supplies a separate fresh Codex
inspection of all 233 dispositions supplying 242 evidence uses to 99 main items.
It connects target-cover identity fields to the report's governing annex text
and target row, preserves 22 case observations, and replays the fresh judgments
against the recorded labels. The frozen source-only packets, role and reading
scope distinguish this inspection from the archived two-reader comparison.
