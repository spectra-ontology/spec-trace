# Reproduce the pack and clause source audits

The census adapter executes the original auditors against released relation records and hash-verified metadata. The completed local-source replay reproduces 54,487 pack links with 54,460 confirmations and 105,363 clause links with 104,125 confirmations. Its clause reader processes 97,782 forms under the original `--no-qdrant` condition. Execution evidence is in [receipts/full_replay.json](receipts/full_replay.json).

The package provides 43 projected metadata inputs, official source locators for 107,854 archive identities across 111,299 paths, and a derived-file frontier. Source archives and reconstructed documents reside in the reader's local work directory.

| Input or executed check | Evidence |
|---|---|
| Portal, CR-list, parsed-CR locator and structural resolver inputs | `inputs/manifest.json`; `receipts/offline_verification.json` checks the original readers' logical outputs |
| Every original archive identity and byte count | `source_inventory/archives.jsonl.gz`; `receipts/local_archive_recheck.json` checks 107,854 identities containing 20,352,011,956 bytes |
| Additional official URL mappings | `source_inventory/network_restoration.json` and `network_restoration_resume.json`; 71 byte-identical official acquisitions, including the recorded network retry |
| Derived inputs | `receipts/derived_files.jsonl.gz` binds 148,110 files and 12,554 directories by path and file hashes |
| Native extraction | `receipts/native_pack_pilot.json`; five pack archives, seven placements and 76 extracted files match their original bytes |
| Original reader behavior after conversion | `receipts/native_conversion_applicability.json`; 11 CR-form inputs and two pack-cover inputs produce identical reader results |
| Accepted-field preservation during conversion | [Explicit native fallback](../census_native/README.md); seven conversions, 14/14 clause reads, 12/12 CR-form reads and 2/2 applicable cover reads agree in the selected archive pilot |

## Verify metadata and run the original audits

From the released checkout, choose an empty staging directory and the source-tree root. The source root follows the original `data/corpus/tsg/RAN/formal/` layout.

```sh
free -h
census_release="$PWD"
census_inputs="$census_release/restore/census"
census_code="$census_release/code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
census_sources=/path/to/source-tree-root
census_work=/tmp/spectra-census-replay
export PYTHONPATH="$census_release/code/scripts/common:$census_code"

python3 "$census_code/export_census_artifact.py" verify \
  --artifact "$census_inputs/inputs" --code-directory "$census_code" \
  --report "$census_work/metadata-check.json"

python3 "$census_code/restore_census_artifact.py" stage \
  --artifact "$census_inputs/inputs" --release "$census_release" \
  --destination "$census_work/stage" --local-source-root "$census_sources" \
  --source-mode local_original_read_only_inputs --receipt "$census_work/stage.json"

python3 "$census_code/restore_census_artifact.py" audit \
  --stage "$census_work/stage" --artifact "$census_inputs/inputs" \
  --reference "$census_release/responses" --out "$census_work/audit" \
  --workers 1 --source-mode local_original_read_only_inputs
```

The adapter verifies the original auditor hashes, stages 20 released record files and two source-agreement diagnostics, and runs the original algorithms. It compares all pack totals and WG summaries, clause WG summaries, complete corpus diagnostics and the body-text condition. The original examples retain staging paths, so comparison excludes those lists. The receipt records the source mode, source-code hashes, reference hashes, execution time and any comparison differences. A difference returns a failing exit status.

## Acquire and reconstruct source inputs

The native constructor selects the TSG pack archives consumed by the original CR pipeline. It uses the bundled original recursive extractor and Word converter. `--scope all` additionally selects WG-document archives. Official downloads are checked against archive size and SHA-256; `--offline` uses an existing verified cache. The native cache names files `<SHA-256>.zip`.

```sh
free -h
python3 "$census_code/restore_census_artifact.py" reconstruct \
  --inventory "$census_inputs/source_inventory/archives.jsonl.gz" \
  --code-root "$census_release/code" --cache "$census_work/archives" \
  --destination "$census_work/reconstructed" --convert \
  --receipt "$census_work/construction.json"
```

For a bounded execution using the same five-archive selection as the native pilot, add `--selection "$census_inputs/receipts/pack_native_selection.json"`. The constructor writes into a new tree and records each source, member, extraction outcome and conversion outcome. Conversion validation sidecars reside outside the audited corpus.

The accompanying plenary restoration uses `<SHA-256>/source.archive` cache entries. After that acquisition, stage their original meeting names with:

```sh
free -h
python3 "$census_code/restore_census_artifact.py" stage-plenary-sources \
  --frontier "$census_release/restore/retrieval/frontier/plenary/files.jsonl.gz" \
  --frontier-sha256 7715bb2f488b7b804575a9d037cb92d3394c72bf171f36a46c4a9a8bde12ac66 \
  --cache "$census_work/plenary-archives" --destination "$census_work/reconstructed" \
  --receipt "$census_work/plenary-layout.json"
```

The `verify-derived` command verifies the historical exact-byte frontier. For converted Word files, [reconstructed census verification](../census_reconstructed/README.md) combines exact archive and native bytes, complete selected paths, pinned conversion receipts, expected scientific-reader digests and both complete original audits. The executed RP-180200 condition verifies seven native files and six reconstructed CR forms plus one cover over the complete original base frontier. Its public-reference comparison retains every compared diagnostic field and validates withheld values by hash and length. Whole-corpus reconstruction certification extends these gates to every derived path.

## Execution scope and environment

The full audit receipt above uses the read-only original local source tree.
The [explicit field-display fallback](../census_native/README.md) completes the
selected archive's seven native conversions: six use the original converter,
and one preserves accepted field displays in a scratch DOCX under the original
strict text predicate. Clause, CR-form and applicable cover reader results
agree. A second whole-corpus audit with that one reconstructed form replacing
its original read reproduces every compared scientific count and corpus/body
diagnostic. These are separately recorded execution scopes.

Fresh DOCX container hashes differ from the historical converted containers;
native-byte identity, strict text checks and original scientific-reader outputs
have their own receipts. The additional seven-document strict-text diagnostic
retains the cover's native-API NUL-separator outcome, while the constructor
uses its successful original cover conversion and reader path. Complete fresh
derived-tree reconstruction retains its own frontier and final-audit gates.

Metadata verification and audit staging use Python's standard library. The original native constructor also uses `tqdm`; conversion uses LibreOffice 7.3.7.2 and system Python with PyUNO, with 7-Zip and libarchive for the recorded archive fallbacks. Processing checks for at least 8 GiB available memory. Reconstructed documents retain their source terms.
