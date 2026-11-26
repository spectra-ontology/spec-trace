# Benchmark CR source check

This checker checks the official native CR forms behind the released
benchmark's 604 distinct CR-to-section pairs. It downloads official 3GPP pack
archives, verifies pinned archive and member SHA-256 values, checks released
record and benchmark-item membership, identifies the CR form, and runs the
released independent form/spec/clause reader. Python's standard library is
sufficient; no database service or model call is used.

## How the graph resolves affected clauses

The CR cover sheet supplies a specification, a target release and a
`Clauses affected` field. The [clause parser](../../code/scripts/tsg/RAN/formal/common/cr_clause.py)
reads that field as ordered candidate clause labels. The builder tries each
candidate in order within the same specification and keeps the first Section
it can resolve. For each candidate the [Section index](../../code/scripts/tsg/RAN/formal/common/phase-4/cr_section_index.py)
uses this priority:

1. The Section for the requested release and clause label.
2. The most recent indexed release at or below the requested release that has
   a Section with that label.
3. The most recent indexed release with that label, when all matching Sections
   are in later releases.

An absent or unreadable target release selects the most recent indexed
release with that label. The builder skips a reference if none of its labels
resolves. Both the
[RAN1–RAN4 JSON-LD construction path](../../code/scripts/tsg/RAN/formal/RAN1/phase-4/cr-parser/03_generate_cr_jsonld.py)
and the [RAN5 graph loader](../../code/scripts/tsg/RAN/formal/RAN5/phase-4/neo4j/01_load_cr_ontology.py)
call the same parser and index.

`MODIFIES_SECTION` (RDF `spectra:modifiesSection`, SQLite
`cr_modifies_section`) preserves the resolved clause-label reference. A
fallback endpoint gives that label an address in an available edition of the
same specification. The requested edition and the linked edition remain
distinct. The [benchmark answer contract](../../benchmark/ANSWER_CONTRACT.md)
uses the clause label in `full_chain` and requires
`document.target_release = section.release` for edition-specific families.
The SQLite comparison uses the target release projected from the phase-1
document record.

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

## Reconstruct the 53 source-format and URL exceptions

The follow-up manifest `reconstructed_source_manifest.json` covers the complete
53-pair exception frontier: 34 CR forms, 29 admitted items and 29 archives. It
supplies the resolved official URL, each nested member name and SHA-256, the
historical form hash, and a text-free digest of every scientific-reader field.
All 53 pairs agree with the current released records and gold answers.

The reconstruction checks 31 legacy Word forms, two native DOCX forms inside
nested ZIPs, and one native DOCX form whose official meeting URL is now pinned.
The legacy forms account for 48 pairs; the three native DOCX forms account for
five. An executed fresh-download check verifies all 29 archives (86,299,243 bytes)
from their official URLs. A separate fresh-conversion run invokes the unchanged
original census constructor on all 31 legacy forms. All 34 forms pass strict
OOXML validation and the complete scientific-reader comparison, including CR
identity, specification and affected-clause fields. The primary
`reconstructed_source_receipt.json` and `reconstructed_source_official_access.json`
record these executions. Three mutation controls detect changed archive bytes,
native-member hashes and expected reader digests.

A supplementary accepted-native/export/reopen check verifies the whole accepted
text of 28 legacy forms after Unicode NFC and layout-whitespace normalization.
`reconstructed_source_accepted_validation.json` records those additional text
digests and the three forms' separate reopen behavior. The primary benchmark
restoration predicate is complete scientific-reader equivalence.

Install LibreOffice and its Python UNO bindings, then run from the release root:

```sh
python3 restore/source_links/check_reconstructed_sources.py \
  --release . \
  --manifest restore/source_links/reconstructed_source_manifest.json \
  --conversion-python /usr/bin/python3 \
  --workers 2 \
  --work work/cr_reconstructed \
  --report work/cr_reconstructed.json
```

The default conversion policy invokes the unchanged original census constructor
and compares the resulting scientific-reader digest with the pinned historical
digest. `--conversion-policy accepted` selects the stronger whole-accepted-text
predicate where supported. Native/output hashes bind each reusable conversion
receipt. The reader receives the historical form basename because the original
reader also interprets the specification in that name. Source and converted
bytes remain local under `--work`; the distributed fixtures and receipts contain
identifiers, locators, digests and outcomes.

Repeat with the same cache and `--offline` for the offline replay. The original
549 native confirmations plus these 53 reconstructed/native confirmations give
602 confirmed pairs; the two table-identifier cases retain their classification.
The original 549/2/53 reports remain available as the initial measurement.
The [corpus-wide reconstruction gate](../census_reconstructed/README.md) covers
its separate selected-input and complete-audit comparison scopes.

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

The benchmark replay confirms CR identity, specification and clause label.
It records the reread form release and the linked Section release as separate
fields. The [corpus source audit](../../code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/audit_clause_links.py)
first tests specification and clause-label agreement for each stored pair
and then reports release concordance on the confirmed pairs. It reapplies the
edition resolver for confirmed pairs with a different or unread form release.
The [stored-link edition census](../../diagnosis/section_editions/README.md)
reports the release comparison for the full stored relation using the
relational document projection. Clause-body coverage, pack membership and
dispositions each have their own audit. The benchmark's 5,610 raw-passing
source links include several relation types.

