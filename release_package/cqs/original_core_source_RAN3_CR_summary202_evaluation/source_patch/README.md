# Separate RAN3#123 source-summary snapshot

This preserves the original English question and requires one exact authored
summary occurrence per CR accepted in the named WG meeting's archived outcome:
202 occurrences, including repeated strings across distinct CRs.
It does not establish subsequent TSG ratification or incorporation in a TS.
The original frozen-graph question remains pending; this package does not add
an original560 pass or merge model scores with earlier cohorts.

The additive graph property is `CR.sourceAuthoredSummary`. Every old graph byte
is preserved as an exact prefix. Baseline and complete snapshot hashes are in
`graph/original_native_import_manifest.json`; the exact append-only delta is
`graph/additive_source_property_delta.ttl`. Recreate the graph by concatenating
the exact pinned baseline and delta, then use the released graph loader and
the recorded mapping/configuration. Complete TTL and SQLite files are external
pinned build inputs, with sizes and hashes retained in the manifests.

Original source archive/member, document coordinates and conversion witnesses
are retained in `evidence/primary_source_summary_rows.jsonl`. Two AI development
judgments and their exact locally executed gate are retained. They are exposed
development reviews; human/expert review count is zero. Historical temporal
challenges and superseded proposals are preserved in the gate provenance.

Run `python -B verify_summary_source_patch.py --patch .` to verify the package,
exact question/repair, saved source/native/SQL values, review schemas and 21
actual positive/negative scorer controls. This offline command does not render
the original Word archives, execute a database or independently certify source
extraction. Those steps require the external original files and pinned renderer
and conversion dependencies referenced in the source rows and local gate.
The local gate actually reread and compared its recorded original inputs.
Binary DOC access reuses conversions authenticated to the exact original member
hash; it is not a new independent conversion-fidelity certificate. Native
reference execution is historical. The selected reference-source rows are
evaluation evidence and are excluded from retrieval augmentation. Whole-source
retrieval text includes all tracked states and differs from the final-visible
renderer used for the reference cells.

Scoring uses an exact typed-string multiset. It preserves all occurrences but
does not judge semantic paraphrases or whitespace-equivalent formatting. A high
record score does not by itself validate the generated query's source predicate,
provenance, causality, or any optional explanation.
