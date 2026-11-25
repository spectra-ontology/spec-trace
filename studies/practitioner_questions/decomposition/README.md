# Trace context in five actual question units

The decomposition covers all five process or mixed units in the existing [33-unit question analysis](../question_analysis.json): U003, U004, U015, U021 and U023. It retains both original classifications, including U003's none/partial mapping disagreement. `decomposition.json` records the requested goal, supplied anchor, documentary contribution and next technical evidence for each unit.

## Two source-context illustrations

U003 explicitly names **R5-253194**. The executed curated lookup returns CR 5008 to TS 38.523-1, Rel-19, agreed at RAN5#107, in pack RP-251118 at RAN#108, with typed clause 11.4.1. The exact source report passage was restored using the released binding checker. The [official CR details](https://portal.3gpp.org/DesktopModules/CRs/CrDetails.aspx?CrId=576852) corroborate these fields and provide their own reason-for-change, which concerns emergency-call release and points to TS 24.501. The request's timing, RRCRelease sequencing and cross-spec behavior call for further specification and discussion reading.

U004's existing [clause-history inspection](../workflow_example.json) supplies 28 candidate CR/disposition/meeting/pack rows for a curated TS 38.101-1, Rel-17, clause 6.2.1 anchor. Its requested edition comparison and rationale remain technical interpretation steps. The other three units retain their original mappings and their stated discovery and interpretation requirements.

These are documented trace-context/subquery illustrations within the original convenience sample. Original question counts, mappings and model scores remain fixed. Each requested goal is retained separately from its documentary context.

## Replay the U003 lookup

From the release root, use Python with SQLite 3.37.2 and the standard library:

```sh
mkdir -p work/question_context
gzip -dc sqlite/RAN5.sqlite.gz > work/question_context/RAN5.sqlite
/usr/bin/python3 -B studies/practitioner_questions/decomposition/inspect_trace.py \
  --release . --database work/question_context/RAN5.sqlite \
  --output work/question_context/execution.json
```

Use ordinary Python execution with its assertion checks enabled. The program checks the public compressed database's decompressed digest, opens the supplied database read-only and immutable, checks categorical predicate domains, retains all returned fields and rows, and verifies unchanged input bytes. It also copies the five existing question units directly from their released analysis. Recorded execution used a 60-second cap and returned one row. The stored `lookup.seconds` includes post-query hashing and describes the whole lookup section rather than pure SQL execution time.

To restore the original report passage locally, first obtain the RAN5#107 report using the [source restoration guide](../../../README.md#restore-sources-and-evidence). Then use a source-root directory containing the original relative report path:

```sh
python3 -B restore/restore_bindings.py --release . --source-root work/sources \
  --wg RAN5 --ids-from studies/practitioner_questions/decomposition/source_manifest.json \
  --out work/question_context/restored.jsonld --report work/question_context/restoration.json
```

`source_restore_receipt.json` records one checked, passage-verified, direct-rule-agreeing record. `source_record.json` retains its path, file digest, span and assigning rule; restored source prose is produced locally. `official_portal_check.json` records the separate portal inspection and its field/rationale scope.

## Development provenance

`protocol.json` preserves the plan fixed before the successful lookup, with its original historical input path and input hash. The public input is `../question_analysis.json`. The first author implementation used the unknown scope spelling `whole_document`, producing a null disposition in a left join. `failed_scope_setup/` retains that code and output; `implementation_amendment.json` records the repair to the stored `whole_target` value. This development correction belongs to a curated author lookup, with zero new model responses and no benchmark score change.

`execution.json` preserves the corrected successful result. The exact provider labels and question mappings are inherited from the original question analysis. `SHA256SUMS` binds the files in this directory.

## Independent native-span verification

The [independent receipt](independent/receipt.json) separately checks raw document/disposition tables, both pack directions and both clause directions, then reconstructs the exact accepted native OOXML span using a separate standard-library reader. It agrees with the original quote digest and direct target-entry decision. Its portal scope is the root's existing portal inspection.

To rerun it, copy this small study directory into scratch and restore the passage there. Use the previously obtained source-root directory:

```sh
cp -R studies/practitioner_questions/decomposition work/question_context/decomposition
python3 -B restore/restore_bindings.py --release . --source-root work/sources \
  --wg RAN5 --ids-from studies/practitioner_questions/decomposition/source_manifest.json \
  --out work/question_context/decomposition/source_restored.jsonld \
  --report work/question_context/decomposition/source_restore_receipt.json
/usr/bin/python3 -B studies/practitioner_questions/decomposition/independent/verify_records.py \
  --release . --analysis work/question_context/decomposition \
  --database work/question_context/RAN5.sqlite --source-root work/sources \
  --output work/question_context/independent.json
```

Native report evidence verifies the document entry and disposition. The pack and clause checks independently compare structured record directions; the separate official portal corroborates those fields.
