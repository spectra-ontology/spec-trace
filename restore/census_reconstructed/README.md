# Reconstructed census verification

This helper verifies a reconstructed RP-180200 tree against a text-free expected fixture derived from the released historical frontier and the original scientific readers. The gate combines exact archive/native bytes, complete selected path coverage, validated conversion receipts, and the unchanged full pack/clause auditors. All original code and source files remain read-only.

`expected_rp180200.json` binds the public commit, the historical frontier, the source archive, all 14 selected file paths and byte identities, and reader-output digests covering every selected Word path. The six reconstructed CR forms and one reconstructed cover match their applicable original readers. Seven retained native DOC files use exact size/SHA256/SHA1 checks. Seven generated DOCX files use an exact native progenitor, a successful pinned constructor event, full ZIP CRC/XML validation, and the original reader-output digests. The comparisons exclude only the clause reader's path and SHA1. The full auditor receives each reconstructed file's actual SHA1, preserving its original deduplication semantics.

`conversion_proof_rp180200.json` binds the measured constructor outputs to their native inputs. The original conversion policy has two explicit branches: five direct exports pass the original strict ZIP/XML predicate; one original native recovery and one explicit fixed-field recovery additionally carry native accepted-full-text/reopen equality receipts. This distinction is retained in the proof. The gate establishes equivalence for the pinned census readers; the two full-text recovery receipts additionally establish their stated accepted-text condition.

`census_tree_gate.py` is importable and provides `fixture`, `conversion-proof`, `verify`, `run-audit`, and `certify` commands. `verify` checks selected inputs. `certify` additionally requires both complete original audit comparisons, their pinned code/reference/output identities, unchanged selected inputs, and observed reads of every applicable reconstructed CR form and cover. A selected input pass alone leaves certification pending.

For a public user, the publisher-supplied expected fixture is the independent reference. Generate a new conversion proof for that user's constructor outputs; retain the expected fixture unchanged. Regenerate the expected fixture with `fixture` only when intentionally building a new trusted reference from the historical original tree. Expected fixtures and public receipts contain metadata and hashes; full local audit output and source documents stay in local scratch storage.

From the public checkout root, set local scratch paths for reconstructed inputs and outputs:

```bash
free -h
CENSUS_PACKAGE="$PWD"
CENSUS_CODE="$CENSUS_PACKAGE/code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
CENSUS_HELPER="$CENSUS_PACKAGE/restore/census_reconstructed"
CENSUS_NATIVE="$CENSUS_PACKAGE/code/scripts/tsg/RAN/formal/common/native_word_conversion.py"
CENSUS_TREE=path/to/reconstructed
CENSUS_CONSTRUCTOR_RECEIPT=path/to/construction_receipt.json
CENSUS_OUTPUT=path/to/new/local_output
export PYTHONPATH="$CENSUS_PACKAGE/code/scripts/common:$CENSUS_CODE"

python3 "$CENSUS_HELPER/census_tree_gate.py" conversion-proof \
  --code "$CENSUS_CODE" --native-module "$CENSUS_NATIVE" \
  --fixture "$CENSUS_HELPER/expected_rp180200.json" \
  --root "$CENSUS_TREE" --constructor "$CENSUS_CONSTRUCTOR_RECEIPT" \
  --out "$CENSUS_OUTPUT/conversion_proof.json"

python3 "$CENSUS_HELPER/census_tree_gate.py" verify \
  --code "$CENSUS_CODE" --native-module "$CENSUS_NATIVE" \
  --fixture "$CENSUS_HELPER/expected_rp180200.json" \
  --root "$CENSUS_TREE" --proof "$CENSUS_OUTPUT/conversion_proof.json" \
  --out "$CENSUS_OUTPUT/input_gate.json"
```

Stage census metadata with the original `restore_census_artifact.py stage` command. For the measured local condition, the staged tree attaches the original local corpus; `--original-root` identifies that corpus and the adapter substitutes the explicitly selected reconstructed paths. For a staged reconstructed tree, both arguments can identify the reconstructed root. Run both unchanged auditors and certify the identical selected input set against the current public projected references:

```bash
CENSUS_LOGICAL_ROOT=path/to/logical_corpus_root
CENSUS_STAGE=path/to/census_stage
python3 "$CENSUS_HELPER/projected_audit_gate.py" run \
  --code "$CENSUS_CODE" --native-module "$CENSUS_NATIVE" \
  --fixture "$CENSUS_HELPER/expected_rp180200.json" \
  --root "$CENSUS_TREE" --proof "$CENSUS_OUTPUT/conversion_proof.json" \
  --original-root "$CENSUS_LOGICAL_ROOT" --stage "$CENSUS_STAGE" \
  --artifact "$CENSUS_PACKAGE/restore/census/inputs" \
  --reference "$CENSUS_PACKAGE/responses" \
  --execution-directory "$CENSUS_OUTPUT/full_audit" \
  --comparison-directory "$CENSUS_OUTPUT/full_audit_comparison" \
  --out "$CENSUS_OUTPUT/certification.json"
```

`projected_audit_gate.py` retains the original comparison predicate and every compared field. The public reference replaces some diagnostic text with SHA256/character-count markers and some filenames with inline markers. The helper checks each raw value against that digest and size, verifies visible path components, and then invokes the unchanged original comparison functions on the corresponding projection. It records the raw execution receipt separately from the public comparison receipt. The measured comparison validates 124 withheld strings and 524 inline filenames. Five mutation controls reject changed diagnostic text, filenames, marker hashes, missing fields, and changed visible counts. The local `--original-reference` option additionally checks the unprojected historical reference; public users use the released projected reference directly. Existing full executions can be checked with the `compare` command and the same arguments other than the execution-only stage/root options.

The measured bounded condition preserves the complete original base frontier and replaces this archive's seven converted files in applicable scientific reads. The original `verify-derived` command checks all 148,110 base-file bytes. `complete_frontier_coverage.py` additionally compares the complete file/directory sets, including unexpected paths. The original base-byte receipt, exact path receipt, selected fixture/proof, and complete audit comparisons together describe that hybrid condition. `fullCorpusReconstructionCertified` remains false because the executed reconstruction covers one archive.

To extend this route to a fresh entire corpus, publish expected scientific digests for all converted paths, together with the complete historical frontier. `fixture` can generate the selected expected reference from original historical files and the relevant constructor receipt. Complete path coverage, exact unconverted bytes, per-conversion bindings/validation, and the full original audits remain required at that scope. Path counts alone establish inventory size; per-path byte or scientific-digest comparisons establish the corresponding equality.

`negative_controls.py` executes eight controls: missing native input, extra path, changed native bytes, changed clause label with a rebound output digest, malformed XML with a rebound output digest, conversion source-binding tampering, omitted full audit, and historical SHA1 substitution. All source originals remain unchanged. Two earlier implementation attempts are retained as local diagnostics: cwd-dependent path resolution, then a process-pool pickling failure. The final execution uses absolute runtime paths and a top-level clause read adapter while preserving the original auditor process pool.
