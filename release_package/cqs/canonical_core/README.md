# Revised canonical Core contracts

This additive bundle accounts for all 560 original Core IDs and supplies an
explicit revised question, population, reference query, required named fields,
types, collection/cardinality and ordering policy for each. Native read-only
query outputs and their required-field gold projections are retained in full.

Start with the [review guide and itemized changes](REVIEW_GUIDE.md) to inspect
what changed for each ID and which checks support it.

The revisions comprise 383 proposed clarifications and 177 substantive variants. Variants
change an ambiguous or unsupported original demand into a stated graph task;
they do not certify that the original question was resolved. Both the original
question and query, the change rationale and scoped AI cross-review are retained.
`validated` means local technical checks and AI-assisted contract review passed.
Author semantic review and independent 3GPP expert validation remain pending.

No new model predictions or performance results are supplied. Historical Core
scores, the 31 original-question diagnostic and the separate 36 variants retain
their original scope. New predictions under these revised definitions are
required for any evaluation of this bundle. See [claim scope](claim_scope.md)
and [adoption plan](adoption_plan.md).

Run from this directory with Python 3.10 or later; no database or third-party
Python dependency is required for the offline checks:

```bash
python3 -B verify_release.py
python3 -B -m unittest test_scorer test_cli
python3 -B score_predictions.py --predictions /path/to/predictions.jsonl --output /tmp/canonical-results.json
```

Each prediction is `{"id":"...","definition_sha256":"...","status":"answer","records":[...]}`.
Provide exactly one prediction for each of the 560 IDs. Explicit abstention is
`status="abstain", records=null` and receives no credit. `records=[]` is an
answer asserting a formal empty result. Only required roles are graded;
additional context columns in a prediction do not substitute for required roles.
Named fields, primitive and nested types, nullability, duplicates, order and
cardinality follow each task's definition. Definition hashes prevent accidental
use of a different contract; this scorer cannot certify generation provenance.

`canonical_tasks.jsonl` and `canonical_reference_gold.jsonl` are the current
technical definitions and projected gold. `reference_outputs/` retains the
complete native columns, positional rows and execution receipts. `provenance/`
keeps the exact candidate records used for definition hashing, scoped reviews,
original source snapshots and execution summaries. Historic absolute source
paths are informational provenance; the offline verifier uses only this bundle's
relative files. `manifest.json` pins every shipped file and the five graph
restorations. It is an integrity inventory, not an independent attestation.

Offline verification rechecks the captured native outputs and projection. It
does not execute the graphs or reproduce prior model generations. The recorded
executions used archived graph restorations with pinned TTL/import hashes,
read-only plans and transactions, and matching before/after node and relation
inventories. Matching inventories do not detect arbitrary external property
mutations. The two catalog tasks use an explicitly supplied, uncurated feature
catalog; that input is not independent domain truth. Graph-derived answers do
not establish causal interpretation, expert correctness or practical utility.

This is a Git addition when adopted. It is separate from the existing frozen
DOI archives; no updated deposit or DOI is asserted. Existing benchmark bytes
and historical measurements remain preserved. Author/expert checks and any
new model evaluation must be documented separately before stronger claims.
