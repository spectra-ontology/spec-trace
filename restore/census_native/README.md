# Preserve accepted native text during census reconstruction

The explicit fallback adapter completes the seven native DOC conversions in the RP-180200 reconstruction pilot while preserving the original scientific readers. The original extractor and converter execute first. When the original accepted-native export/reopen comparison identifies a changed field display, the adapter materializes the accepted display in a new scratch DOCX and retains the original field instructions, cached values and pre-transform package as local evidence. The original XML, source-identity, redline and full-text comparison checks remain in force.

The executed constructor pilot reconstructed **14 files: seven original native files and seven fresh DOCX files**. All seven native byte hashes agree. The original clause readers agree for **14/14 files**, including **12/12 CR-form filename inputs**; the original pack-cover readers agree for **2/2 applicable files**. The original converter handles six conversions and the field-preservation fallback handles one. `constructor_receipt.json` records these outcomes and code/input hashes.

For the repaired CR, the accepted and reopened main text both contain **205,946 characters**, with **169,558 characters** and an identical SHA-256 under the original whitespace normalization. The adapter preserves all **102 field records** in its local sidecar. A separate diagnostic verifies the same whole-text predicate and original CR-form reader for all six CR documents. The cover retains the original direct-conversion/cover-reader route: its native text API includes sixteen U+0000 separators that a normal DOCX reopen omits, and the unchanged whole-text predicate records that diagnostic failure. `native_policy_receipt.json` preserves the complete seven-document outcome.

The original full census was also rerun over the read-only local corpus with one explicitly reconstructed CR form replacing its original read. It reproduces **54,487 pack links with 54,460 confirmed** and **105,363 clause links with 104,125 confirmed**, together with the original corpus and body diagnostics. `census_replacement_receipt.json` identifies that one replacement by hash and records the actual audit comparisons. This measured condition combines the original local corpus and one reconstructed form; the separate constructor pilot covers the selected archive. Fresh DOCX container identities are recorded separately from reader and scientific-output equality.

## Execute the explicit fallback

Place this bundle at `restore/census_native`. The CLI forwards the original constructor's options after `--`. Set the checkout, local archive cache and a new scratch directory. Official source archives can be prepared through the existing census source-restoration instructions.

```sh
free -h
native_release=/path/to/released-checkout
native_archives=/path/to/pinned-native-archive-cache
native_scratch=/path/to/new-native-reconstruction
python3 "$native_release/restore/census_native/reconstruct_census_fixed_field_fallback.py" \
  --runner-module "$native_release/code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/restore_census_artifact.py" \
  --fixed-field-adapter "$native_release/restore/census_native/recover_native_word_fixed_fields.py" \
  --native-module "$native_release/code/scripts/tsg/RAN/formal/common/native_word_conversion.py" \
  --fallback-evidence "$native_scratch/field-evidence" \
  --fallback-receipt "$native_scratch/fallback-receipt.json" -- \
  --inventory "$native_release/restore/census/source_inventory/archives.jsonl.gz" \
  --code-root "$native_release/code" --cache "$native_archives" \
  --destination "$native_scratch/corpus" \
  --selection "$native_release/restore/census_native/selection_rp180200.json" \
  --limit 1 --offline --convert --receipt "$native_scratch/construction.json"
```

The original constructor supports the full selected source inventory when the selection and limit options are omitted. The selection above reproduces the measured seven-conversion archive pilot. `--local-source-root /path/to/local-corpus-root` supports read-only local archive inputs, and `--compare-root /path/to/original-corpus-root` runs the original scientific-reader comparisons where that reference corpus is available.

System Python with PyUNO, LibreOffice and `lxml` supports the field adapter. The original archive constructor additionally uses its documented archive tools. Every source, code, cache, scratch and receipt path is explicit. The wrapper selects the fallback only for the original accepted-text/reopen error; its receipt preserves the original failure and the successful strict fallback check.

## Verify scientific reads and text-loss sensitivity

`replay_census_form_replacements.py` executes the original full pack/clause auditors with explicit reconstructed form reads. It retains the logical corpus path and the reconstructed file's actual SHA-1, so the original deduplication and judgment rules operate on the measured inputs. Supply `--runner-module`, `--stage`, `--artifact`, `--reference`, `--replacement ORIGINAL_DOCX=RECONSTRUCTED_DOCX`, `--workers 1` and a new `--out`. The two original audits and every unchanged input remain read-only.

`probe_native_fixed_fields_batch.py` reruns the original seven-file native pilot under the fixed-display policy and compares the original applicable readers. `verify_docx_reopen_against_text.py` opens actual DOCX candidates read-only in an isolated LibreOffice process and applies the original strict predicate to a captured native baseline. The executed negative controls preserve the positive artifact, delete one body character in a scratch copy, and alter one required CR-form version value in another. Actual reopens retain the positive pass and reject both altered copies; the original CR-form reader also identifies the required-value change. `negative_controls_receipt.json` records the artifact hashes and results.

Local evidence directories retain accepted/reopened source text, field instruction/cache XML and complete pre-transform packages. This public bundle contains executable restoration code and metadata-only receipts, including hashes, lengths, counts, policies and strict results. `manifest.json` binds every selected public file.
