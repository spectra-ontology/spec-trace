The CR reconstruction bundle binds every indexed CR in RAN1–RAN5 to an official source URL, archive/member identity, pinned parser, frozen structural metadata, and the original chunk IDs, text digests, and output positions. The five complete manifests cover 56,806 documents and 596,399 chunks. Their complete target positions and source URL coverage were checked in `all_wg_recipe_inventory.json`.

| WG | Documents | Chunks | Complete manifest |
|---|---:|---:|---|
| RAN1 | 2,120 | 12,506 | `ran1_restore_recipes.jsonl.gz` |
| RAN2 | 8,201 | 73,948 | `ran2_complete_recipes.jsonl.gz` |
| RAN3 | 3,040 | 27,652 | `ran3_restore_recipes.jsonl.gz` |
| RAN4 | 14,020 | 202,133 | `ran4_restore_recipes.jsonl.gz` |
| RAN5 | 29,425 | 280,160 | `ran5_snapshot_recipes.jsonl.gz` |

The runner regenerates the reason, summary, consequences, and affected-clause form fields directly from acquired DOCX. It executes the hash-pinned original Phase-4 and Phase-8 functions through an explicit metadata-resolver adapter, then checks both the four form-field digests and the entire chunk ID/text-digest sequence. Metadata contains titles, organization names, work-item codes, and structural identifiers. Original pack-cover clause labels are retained as structural metadata. `metadata_text_audit.json` records the complete field/type/length audit; source narrative and chunk text are acquired and parsed locally.

The execution evidence has three distinct scopes. The complete retained-source RAN3 replay matched all 3,040 documents and 27,652 chunks, including all four form-field digests (`ran3_local_raw_batch_receipt.json`). Official network acquisition pilots cover seven RAN3 documents/320 chunks and five RAN2 documents/908 chunks. A 17-document RAN5 official-download pilot acquired three archives totaling 6,918,941 bytes: all source/form digests matched, and the original parser matched 14 of 17 chunk sequences. The three remaining sequences contained an extra LF at the first heading boundary. The declared RAN5 snapshot bridge deletes that single LF only when the resulting whole-text digest matches the frozen target. Replaying the same acquired archives with that bridge matched all 17 documents/332 chunks, applying 142 single-LF deletions. Both attempts and their distinct network/cache states are preserved. Complete five-WG manifests describe source and reconstruction coverage; complete five-WG raw execution has its own future receipt.

An isolated code-layout check copied code, the redacted credentials stub, and eight local DOCX inputs into `/tmp`, used an empty `PYTHONPATH`, and replayed one case per WG. All 1,101 chunks matched; all loaded repository modules came from the staged code root (`standalone_receipt.json`). The RAN4 case includes three continuation documents. `source_guard_controls_final.json` checks rejection of an altered exact-member source with a forged output-only sidecar, acceptance of a pinned native conversion, and rejection of a mismatching native digest. Resume and assembly controls also check raw-field mismatches, altered cached text, and target-position length mismatches.

Preserve the `scripts/...` layout in `CODE_ROOT`, with a `.git` root marker for the original helper modules. The code list and SHA256 pins are in `dependency_pins_final.json`; use the selected redacted `credentials.py` stub. Dependencies and the measured runtime are in `public_selection.json`. Parsing uses the cached BAAI/bge-m3 tokenizer in offline mode. Native Word source paths use the pinned LibreOffice conversion procedure; successful native-conversion acquisition receipts identify LibreOffice 7.3.7.2 and, where specified, the tracked-change acceptance procedure.

```sh
python3 CR_BUNDLE/restore_cr_probe.py acquired-batch \
  --repository CODE_ROOT \
  --recipes CR_BUNDLE/ran3_restore_recipes.jsonl.gz \
  --cache LOCAL_CACHE/archives --source-root LOCAL_CACHE/sources \
  --text-cache LOCAL_CACHE/text --receipt-dir LOCAL_CACHE/receipts \
  --report LOCAL_CACHE/acquired_summary.json --download

python3 CR_BUNDLE/restore_cr_probe.py assemble \
  --recipes CR_BUNDLE/ran3_restore_recipes.jsonl.gz \
  --text-cache LOCAL_CACHE/text --output-root LOCAL_CACHE/parsed \
  --report LOCAL_CACHE/assemble_receipt.json
```

Run the acquisition command separately for each WG manifest; add `--resume` to validate and reuse prior successful local outputs. Acquisition outcomes stream to a referenced JSONL file, and the summary records its SHA256 and execution modes. The assembled local JSON preserves the complete original target order for the parent index-restoration procedure. The selected public bundle contains reconstruction code, metadata, hashes, and receipts; locally parsed text belongs in the chosen local cache. Package integration, source terms, publication, and external download verification are recorded by the parent release workflow.

This is an implementation contribution. The earlier independent review and its verdict remain a separate assessment.
