# Finite document-identity source inspection

This audit connects all 233 disposition records in the benchmark's
review-dependence cohort to their report decision passages and target-document
covers. Those records supply 242 gold-evidence uses across 99 main benchmark
items. Direct Codex inspection supported each target attribution and matched
the recorded code and scope in all 233 cases: 232 `agreed` and one `endorsed`.
The per-case readings preserve 22 observations about metadata, document-number
formatting and the governing decision text.

The protocol was saved before preparing and reading the source-only packets.
The packets withheld the recorded code, scope and earlier identity verdict.
One Codex session read the annex governing text, the complete target row and the
target-cover identity fields, saved fresh judgments, then joined the historical
labels. This finite inspection assesses source-bound document identity and the
decision expressed in those passages. Its scope is separate from the archived
two-reader study and from technical validation of the CR contents or source
recall across complete reports.

The observations remain visible even where the decision matched. For example,
case `finite-107` follows the local table's endorsement instruction within a
broader agreed-CR annex. Cases `finite-138` and `finite-139` have document-number
entries with otherwise empty annex metadata; their target covers provide the
corresponding document identity. The 22 observations are recorded individually
in `readings.jsonl`.

## Replay the comparison

From the release root:

```sh
python3 -B studies/disposition_reading/finite_identity/replay.py --release . \
  --out work/disposition_reading/finite_identity.json
```

This checks all bundle hashes, the frozen cohort and reading-file hashes, every
case ID, source binding, fresh-versus-recorded label comparison, and the
242 evidence-use/99-item dependencies.

## Reconstruct the source-only packets

With the hash-pinned report and target files in their recorded relative paths:

```sh
python3 -B studies/disposition_reading/finite_identity/replay.py --release . \
  --source-root /path/to/source-tree-root \
  --out work/disposition_reading/finite_identity_source.json
```

The replay verifies the 55 report and 233 target-document hashes and reconstructs
each source-only packet, checking both all 233 packet digests and the original
packet-file digest. Source restoration follows
[`restore/census/README.md`](../../../restore/census/README.md) and
[`REPRODUCING.md`](../../../REPRODUCING.md). The target paths, hashes and source
locators are retained in the case manifests; this release validation used the
existing local source files.

| File | Role |
|---|---|
| `protocol.json` | Frozen cohort, inspection procedure and completion criteria. |
| `packets.jsonl` | Source-only packet manifests with block and complete-packet digests. |
| `readings.jsonl` | Fresh Codex judgments, exact inspection scope, reasons, observations and source locations. |
| `reading_freeze.json` | Protocol, packet-file and reading-file hashes saved before the historical-label comparison. |
| `comparison.json` | Case-level historical-label join and evidence-use dependencies. |
| `replay.py` | Offline comparison and optional local source reconstruction. |
