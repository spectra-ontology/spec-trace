# Separate source correction: ten omitted TS 38.133 tables

This published additive patch restores ten actual source-authored Word tables in TS 38.133 section 9.2.5.1 across the retained Rel-15 and Rel-16 editions. It uses the existing TSTable class and exact edition owners. The unchanged original question RAN4_P3_CQ1-5 yields 80 source caption identities in this separate snapshot: 62 actual Word tables and 18 authored Void captions. The frozen 70-record task and the current 447-item index remain intact.

[Portable reconstruction inputs and evidence](portable_patch/README.md) include exact source DOCX member bytes, source hashes and CRCs, a 140-triple patch, full source/native/SQL observations and 23 scoring controls. Actual independent fresh reconstructions preserve all old SQL tables and rows and reproduce the RDF bytes. SQLite database bytes can differ after reconstruction; [complete logical comparison](completed_verification/source10_portable_actual_rebuilt_SQL_full_all_new_and_old_columns_logical_equivalence.json) checks every column and all rows of all 80 tables in both directions, including the new data.

The portable manifest retains its local preparation status as an immutable historical input. This wrapper records publication of those exact bytes. This is a Git addition; the frozen deposited release is unchanged. Fresh four-method model evaluation is being registered separately and no model-performance result is claimed here. The source census covers the named section and retained editions; human/expert validation is zero.

Verify without network access or a database server:

```sh
python3 -B portable_patch/verify_rebuild.py
python3 -B portable_patch/evaluation/verify_controls.py
```

To reconstruct a separate RDF and SQLite snapshot, use the pinned baseline files and an unused output directory as described in the portable README. Source documents and derived content retain their original 3GPP attribution under the repository license.
