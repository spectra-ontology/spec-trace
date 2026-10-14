# Existing top-k contract replacements

These ten separately reviewed contracts preserve the original English questions,
original queries and required answer fields. Their reference queries remove only
the final cap and retain the full eligible ranking pool, so any valid selection
at the numeric boundary can be scored. Display order is not required.

This package replaces definitions for ten existing Core IDs. It adds no IDs;
the previous 371-item bundle and its complete 560-item disposition ledger are
preserved unchanged and pinned. The separately published seven-item and local
eight-item additions are not changed by these replacements. Original capped
and uncapped native receipts retain their original IDs and bytes.

The two new AI semantic reviews and retained frozen-source SQL witnesses are
included separately. The offline verifier checks identities, typed native
projections, source guards and actually replays all scorer controls. It does not
rerun SQL databases or certify raw-archive completeness, human review or expert
validation. No new model calls or native executions were used to build this
package. Existing frozen model results remain associated with their original
contracts; any rescoring must be labelled separately.

Run from a fresh copy, supplying the unchanged parent bundle:

```sh
python3 -B verify_replacements.py --bundle . --parent ../original_core_repair --out /tmp/replacement-proof.json
python3 -B -m unittest test_scorer test_native_order test_predictions test_boundary_ties
```
