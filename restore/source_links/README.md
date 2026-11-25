# Benchmark CR source check

This checker checks the official native CR forms behind the released
benchmark's 604 distinct CR-to-section pairs. It downloads official 3GPP pack
archives, verifies pinned archive and member SHA-256 values, checks released
record and benchmark-item membership, identifies the CR form, and runs the
released independent form/spec/clause reader. Python's standard library is
sufficient; no database service or model call is used.

## Measured expansion

The actual official-download run fetched 251 distinct archives (555,353,060
bytes). The final checker then ran offline against all five working-group
caches. Both runs produced 549 confirmed pairs, 2 `table_or_figure_in_clause`
pairs, and 53 `source_unavailable` pairs. The 53 comprise 52 forms whose derived
OOXML bytes differ from an exact native archive member and one unresolved
official meeting URL. They stay in the manifest and denominator.

The two table-identifier cases are R4-2108887 → A.7.6.3.2.2 and R5-263191 →
F.1.1.3. Their official forms enumerate tables within these clauses. They match
the same two entries in the released `gold_links_in_audit_remainder.json`;
`table_identifier_followup.json` records the direct comparison. The checker
retains the released reader's conservative classification.

`benchmark_expansion_summary.json` records per-group counts, archive bytes,
timings, checker hash and receipt hashes. `benchmark_online_RAN1.json` through
`RAN5.json` record the actual network runs. `benchmark_offline_RAN1.json`
through `RAN5.json` record the final code with no URL opened. The sum of group
times is a work measure; groups ran concurrently and it is not wall time.

## Run from a public-release checkout

From the release root, use a fresh cache for an official-download replay:

```sh
python3 restore/source_links/check_source_links.py \
  --release . \
  --manifest restore/source_links/benchmark_clause_manifest.json \
  --work /tmp/spectra-cr-source-replay \
  --report /tmp/spectra-cr-source-online.json
```

Repeat with the same cache and `--offline`:

```sh
python3 restore/source_links/check_source_links.py \
  --release . \
  --manifest restore/source_links/benchmark_clause_manifest.json \
  --work /tmp/spectra-cr-source-replay \
  --report /tmp/spectra-cr-source-offline.json \
  --offline
```

`--wg RAN1` (or another group) supports a smaller replay. The deterministic
10-pair `pilot_manifest.json` supports a quick run; 9 native pairs were actually
confirmed online and offline and one remained outside the supported source
format. A corrupted-cache control was executed and rejected before form
parsing; `tamper_control_receipt.json` preserves that result.

The original expanded run used one cache per group under
`/tmp/spectra-cr-source-benchmark/RAN1` through `RAN5`. Its final offline command
also supplied `--wg RAN1` through `RAN5` for the matching cache. Receipt cache
paths describe that execution and do not configure future runs.

## Scope and preparation

`benchmark_clause_manifest.json` is the executable pinned input. It identifies
the public release commit and SHA-256 of the released reader. The checker imports
only its form-reading functions and never invokes its server-dependent main
routine. `build_manifest.py` is separate preparation provenance: it requires the
original local corpus to determine exact native archive/member hashes.
External users can run the checker with the prepared manifest and public
release alone.

`benchmark_source_inventory.json` counts 1,532 gold CR/pack pairs over 601 packs,
including 604 distinct clause pairs over 303 CRs. All 601 original archives
(1,310,339,863 bytes) were locally present during preparation. The 604 clause
pairs reference 280 locally hashed archives (641,652,303 bytes); 551 pairs over
251 archives have a supported exact native member and official URL. Archive
presence is distinct from native-member support and fresh official access.

This replay supports native OOXML form/spec/clause confirmation. The published
5,610 raw-pass links include other relation types. Whole-census audits, release
resolution, clause-body coverage, pack membership and disposition checks retain
their existing separate procedures and evidence. The pinned manifest and receipts identify the release inputs used in these checks.

