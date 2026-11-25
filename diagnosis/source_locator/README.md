# Source-locator follow-up

These text-free receipts connect every saved `source_verified` locator exception
to its exact native report, original body-block span and producer quote digest.
Fresh reads cover 368 dispositions in 79 DOCX reports (82,549,770 bytes): 216 in
RAN1 and 152 in RAN4. All 368 source hashes, original spans and exact quotes agree.
The accepted-prose rendering reconstructs every quote; rich chunk rendering
inserts equation text into those passages (247 OMML cases and 121 equation-object
or picture cases). This explains the saved locator-check outcomes while keeping
the original source bytes, locators, records and initial measurements fixed.

`public_population_manifest.json` enumerates the complete 368-record class.
`public_manifest.json` separately records its 11 dispositions used by seven
current main-benchmark items, with direct target/code/scope checks. The selected
public rehydration replay also records 368/368 direct rule agreements. These
rule readings and the source-binding checks have their respective scopes in the
receipts.

After [restoring the cited reports](../../README.md#restore-sources-and-evidence),
run from the release root:

```sh
python3 restore/restore_bindings.py --release . --source-root work/sources \
  --ids-from diagnosis/source_locator/public_population_manifest.json \
  --out work/source_locator_368.jsonld --report work/source_locator_368.json

python3 restore/validate_bindings.py --release . \
  --records work/source_locator_368.jsonld --report work/source_locator_368_shacl.json
```

The executed public workflow is recorded in `m1_public_rehydration.json` and
`m1_public_rehydration_shacl.json`. It checks all selected source and quote hashes,
rehydrates 368 passages and applies the 44 released shapes. Quotations remain
in the local output; the distributed manifests and reports contain digests,
locators, counts and outcomes.

The [CR-form follow-up](../../restore/source_links/README.md#reconstruct-the-53-source-format-and-url-exceptions)
restores its separate 53-pair benchmark frontier. The
[corpus-wide reconstruction workflow](../../restore/census_reconstructed/README.md)
retains the full-audit comparisons and their selected conversion proofs.
