#!/usr/bin/env python3
"""Compare supplied named records under a source-anchored sidecar contract.

This generic scorer is separate from the released value-set/positional scorers.
It performs no question inference, model calls, query execution, source-truth
certification or expert validation. Re-scoring retained outputs is an output
contract diagnostic; it is not a new model-performance experiment.

Exact output match requires every required named field and its declared type.
Extra unrequested fields are ignored except fields named by a scope guard.
Set semantics remove identical projected rows, multiset semantics retain them,
sequence semantics preserve positions, and ordered_ties preserve the sequence of
equal-order-key groups while allowing permutations within each group.

Partial named-cell precision and recall use the number of correct required cells
in an optimal one-to-one row assignment, divided by predicted/gold row count
times required field count. Thus missing fields consume opportunities, wrong
roles cannot match each other, and no cell from one prediction is reused for
multiple gold rows. Sequence assigns by position; ordered_ties assigns only
within corresponding groups with identical keys. This is diagnostic credit,
not evidence that the complete record was correct.

The final exact result is null if the contract or a constraint is unresolved.
Output match and partial scores remain explicitly conditional on supplied gold.
Observable scope guards and cardinality guards can veto an otherwise exact
match. Gold completeness, query scope and tie membership are not established
merely because their source anchors are recorded.
"""
import argparse
from collections import Counter
from fractions import Fraction
import json
import math
from pathlib import Path


TYPES = {"string", "integer", "number", "boolean", "null", "json"}
KINDS = {"set", "multiset", "sequence", "ordered_ties"}
MISSING = ("missing", "")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def valid_anchor(anchor):
    return ((isinstance(anchor, str) and bool(anchor))
            or (isinstance(anchor, dict)
                and all(isinstance(anchor.get(key), str) and anchor[key] for key in ("question", "query"))))


def validate_contract(contract):
    """Check scorer invariants; contract_schema.json defines the interchange form."""
    require(isinstance(contract, dict), "contract must be an object")
    require(type(contract.get("version")) is int and contract["version"] == 1, "unsupported contract version")
    require(isinstance(contract.get("item_id"), str) and contract["item_id"], "missing item_id")
    require(contract.get("status") in {"ready", "unresolved"}, "invalid contract status")
    fields = contract.get("required_fields")
    require(isinstance(fields, list) and fields, "required_fields must be nonempty")
    names = []
    for field in fields:
        require(isinstance(field, dict), "field must be an object")
        require(isinstance(field.get("name"), str) and field["name"], "missing field name")
        require(field.get("type") in TYPES, "unsupported field type")
        require(isinstance(field.get("role"), str) and field["role"], "missing named role")
        require(valid_anchor(field.get("source_anchor")), "missing field source anchor")
        require(isinstance(field.get("nullable", False), bool), "nullable must be boolean")
        names.append(field["name"])
    require(len(set(names)) == len(names), "duplicate required field names")
    collection = contract.get("collection", {})
    require(collection.get("kind") in KINDS, "unsupported collection kind")
    if collection["kind"] == "ordered_ties":
        keys = collection.get("order_keys")
        require(isinstance(keys, list) and keys, "ordered_ties needs order keys")
        require(collection.get("tie_policy") == "any_order_within_equal_keys", "unsupported tie policy")
        for key in keys:
            require(key.get("field") in names, "order key must be a required named field")
            require(key.get("direction") in {"asc", "desc"}, "invalid order direction")
            field = next(f for f in fields if f["name"] == key["field"])
            require(field["type"] in {"string", "integer", "number"} and not field.get("nullable"),
                    "order keys need nonnullable string or numeric fields")
        require(len({k["field"] for k in keys}) == len(keys), "duplicate order keys")
    else:
        require("order_keys" not in collection and "tie_policy" not in collection,
                "only ordered_ties accepts order keys and a tie policy")
    require(isinstance(contract.get("constraints"), list), "constraints must be a list")
    require(isinstance(contract.get("unresolved_reasons"), list), "unresolved_reasons must be a list")
    require(all(isinstance(reason, str) and reason for reason in contract["unresolved_reasons"]),
            "unresolved reasons must be nonempty strings")
    for constraint in contract["constraints"]:
        require(constraint.get("kind") in {"scope", "cardinality"}, "unknown constraint kind")
        require(valid_anchor(constraint.get("source_anchor")),
                "missing constraint source anchor")
        if constraint["kind"] == "scope":
            require(isinstance(constraint.get("field"), str) and constraint["field"], "missing scope field")
            require("value" in constraint, "missing scope value")
            require(constraint.get("verification") in {"record_field", "reference_query", "unresolved"}, "invalid scope verification")
        else:
            require(constraint.get("mode") in {"exact", "at_most", "all", "top_k", "unresolved"},
                    "invalid cardinality mode")
            require(constraint.get("verification") in {"gold_records", "unresolved"}, "invalid cardinality verification")
            if constraint["mode"] in {"exact", "at_most", "top_k"}:
                require(type(constraint.get("value")) is int and constraint["value"] >= 0,
                        "cardinality value must be a nonnegative integer")
            if constraint["mode"] == "top_k" and constraint["verification"] == "gold_records":
                require(constraint.get("tie_policy") in {"exact_k", "include_cutoff_ties"},
                        "top_k needs an explicit cutoff tie policy")


def token(value, field):
    """Typed equality, without string/number coercion or role normalization."""
    if value is None and field.get("nullable", False):
        return ("null", "")
    kind = field["type"]
    if kind == "string" and isinstance(value, str):
        return (kind, value)
    if kind == "integer" and type(value) is int:
        return (kind, str(value))
    if kind == "number" and type(value) in {int, float} and (type(value) is int or math.isfinite(value)):
        exact = Fraction(str(value))
        return (kind, f"{exact.numerator}/{exact.denominator}")
    if kind == "boolean" and type(value) is bool:
        return (kind, str(value))
    if kind == "null" and value is None:
        return (kind, "")
    if kind == "json":
        try:
            return (kind, json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False))
        except (TypeError, ValueError):
            pass
    return ("invalid", kind)


def project(records, fields, *, gold=False):
    require(isinstance(records, list), "records must be a list")
    rows = []
    for index, record in enumerate(records):
        require(isinstance(record, dict), f"record {index} must be a named object")
        row = tuple(token(record[field["name"]], field) if field["name"] in record else MISSING
                    for field in fields)
        if gold:
            require(all(cell[0] not in {"invalid", "missing"} for cell in row),
                    f"gold record {index} has a missing or wrongly typed required field")
        rows.append(row)
    return rows


def max_cell_assignment(predicted, gold):
    """Maximum named-cell overlap with a polynomial-time Hungarian assignment."""
    if not predicted or not gold:
        return 0
    # An identical, fully valid record can always be paired first: exchanging
    # cross-pairs cannot reduce equal-name cell overlap (Hamming triangle rule).
    # This leaves the assignment only the residual rows and keeps an almost
    # exact long list from creating a large cubic assignment problem.
    pred_counts, gold_counts = Counter(predicted), Counter(gold)
    shared = pred_counts & gold_counts
    shared = Counter({row: count for row, count in shared.items()
                      if all(cell[0] not in {"missing", "invalid"} for cell in row)})
    base = sum(shared.values()) * len(gold[0])
    predicted, gold = list((pred_counts - shared).elements()), list((gold_counts - shared).elements())
    if not predicted or not gold:
        return base
    weights = [[sum(p == g and p[0] not in {"missing", "invalid"}
                    for p, g in zip(pred, expected)) for expected in gold]
               for pred in predicted]
    # The rectangular assignment needs no more rows than columns.
    if len(weights) > len(weights[0]):
        weights = [list(column) for column in zip(*weights)]
    n, m = len(weights), len(weights[0])
    ceiling = max(max(row) for row in weights)
    costs = [[ceiling - weight for weight in row] for row in weights]
    u, v, assignment, way = [0] * (n + 1), [0] * (m + 1), [0] * (m + 1), [0] * (m + 1)
    for i in range(1, n + 1):
        assignment[0] = i
        j0, minimum, used = 0, [float("inf")] * (m + 1), [False] * (m + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = assignment[j0], float("inf"), 0
            for j in range(1, m + 1):
                if not used[j]:
                    current = costs[i0 - 1][j - 1] - u[i0] - v[j]
                    if current < minimum[j]:
                        minimum[j], way[j] = current, j0
                    if minimum[j] < delta:
                        delta, j1 = minimum[j], j
            for j in range(m + 1):
                if used[j]:
                    u[assignment[j]] += delta
                    v[j] -= delta
                else:
                    minimum[j] -= delta
            j0 = j1
            if assignment[j0] == 0:
                break
        while True:
            j1 = way[j0]
            assignment[j0] = assignment[j1]
            j0 = j1
            if j0 == 0:
                break
    return base + sum(weights[assignment[j] - 1][j - 1] for j in range(1, m + 1) if assignment[j])


def consecutive_groups(rows, positions):
    groups = []
    for row in rows:
        key = tuple(row[position] for position in positions)
        if groups and groups[-1][0] == key:
            groups[-1][1].append(row)
        else:
            groups.append((key, [row]))
    return groups


def validate_gold_order(records, collection):
    for previous, current in zip(records, records[1:]):
        for key in collection["order_keys"]:
            left, right = previous[key["field"]], current[key["field"]]
            if left == right:
                continue
            ordered = left < right if key["direction"] == "asc" else left > right
            require(ordered, "gold records violate declared ordering")
            break


def compare_rows(predicted, gold, fields, collection):
    kind = collection["kind"]
    if kind == "set":
        predicted, gold = list(dict.fromkeys(predicted)), list(dict.fromkeys(gold))
    if kind in {"set", "multiset"}:
        exact = Counter(predicted) == Counter(gold)
        complete_rows = sum((Counter(predicted) & Counter(gold)).values())
        cells = len(gold) * len(fields) if exact else max_cell_assignment(predicted, gold)
    elif kind == "sequence":
        exact = predicted == gold
        complete_rows = sum(pred == expected for pred, expected in zip(predicted, gold))
        cells = sum(p == g and p[0] not in {"missing", "invalid"}
                    for pred, expected in zip(predicted, gold) for p, g in zip(pred, expected))
    else:
        positions = [next(i for i, field in enumerate(fields) if field["name"] == key["field"])
                     for key in collection["order_keys"]]
        predicted_groups, gold_groups = consecutive_groups(predicted, positions), consecutive_groups(gold, positions)
        exact = len(predicted_groups) == len(gold_groups) and all(
            pk == gk and Counter(pr) == Counter(gr)
            for (pk, pr), (gk, gr) in zip(predicted_groups, gold_groups))
        complete_rows = sum(sum((Counter(pr) & Counter(gr)).values()) for (pk, pr), (gk, gr)
                            in zip(predicted_groups, gold_groups) if pk == gk)
        cells = len(gold) * len(fields) if exact else sum(max_cell_assignment(pr, gr) for (pk, pr), (gk, gr)
                    in zip(predicted_groups, gold_groups) if pk == gk)
    return int(exact), cells, complete_rows, len(predicted), len(gold)


def check_constraints(constraints, records, row_count, gold_count):
    checks = []
    for constraint in constraints:
        result = {"kind": constraint["kind"], "source_anchor": constraint["source_anchor"]}
        if constraint["verification"] == "reference_query":
            result.update(status="unverifiable", reason="reference-query restriction is provenance only; prediction scope is not observable from supplied records")
        elif constraint["verification"] == "unresolved" or constraint.get("mode") == "unresolved":
            result.update(status="unverifiable", reason="source audit has not resolved this requirement")
        elif constraint["kind"] == "scope":
            field, expected = constraint["field"], constraint["value"]
            # JSON serialization keeps booleans distinct from numeric values.
            serialize = lambda value: json.dumps(value, sort_keys=True, allow_nan=False)
            passed = all(field in record and serialize(record[field]) == serialize(expected) for record in records)
            result.update(status="pass" if passed else "fail", field=field,
                          reason="scope field checked on every supplied record; query provenance is not certified")
        else:
            mode = constraint["mode"]
            if mode == "exact":
                passed = row_count == constraint["value"]
            elif mode == "at_most":
                passed = row_count <= constraint["value"]
            elif mode == "all":
                passed = row_count == gold_count
            elif constraint["tie_policy"] == "exact_k":
                passed = row_count == constraint["value"]
            else:
                passed = row_count == gold_count and gold_count >= constraint["value"]
            result.update(status="pass" if passed else "fail", mode=mode,
                          reason="supplied record count checked; population completeness and cutoff membership are conditional on gold")
        checks.append(result)
    return checks


def score_contract(contract, gold_records, prediction):
    """Return conditional output scores and unresolved/failed constraint status."""
    validate_contract(contract)
    predicted_records = prediction.get("records") if isinstance(prediction, dict) else prediction
    fields, collection = contract["required_fields"], contract["collection"]
    gold = project(gold_records, fields, gold=True)
    predicted = project(predicted_records, fields)
    if collection["kind"] == "ordered_ties":
        validate_gold_order(gold_records, collection)
    output_exact, cells, complete_rows, n_predicted, n_gold = compare_rows(predicted, gold, fields, collection)
    gold_checks = check_constraints(contract["constraints"], gold_records, n_gold, n_gold)
    require(all(check["status"] != "fail" for check in gold_checks), "supplied gold violates contract constraints")
    checks = check_constraints(contract["constraints"], predicted_records, n_predicted, n_gold)
    unresolved = (contract["status"] == "unresolved" or bool(contract["unresolved_reasons"])
                  or any(check["status"] == "unverifiable" for check in checks))
    precision = cells / (n_predicted * len(fields)) if n_predicted else float(not n_gold)
    recall = cells / (n_gold * len(fields)) if n_gold else float(not n_predicted)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    row_precision = complete_rows / n_predicted if n_predicted else float(not n_gold)
    row_recall = complete_rows / n_gold if n_gold else float(not n_predicted)
    row_f1 = 2 * row_precision * row_recall / (row_precision + row_recall) if row_precision + row_recall else 0.0
    return {
        "item_id": contract["item_id"],
        "measurement_scope": "supplied_records_only",
        "semantic_validation": False,
        "assessment": "indeterminate" if unresolved else "output_comparison",
        "exact": None if unresolved else int(output_exact and all(check["status"] == "pass" for check in checks)),
        "output_exact": output_exact,
        "partial_named_cells": {"precision": precision, "recall": recall, "f1": f1,
                                "correct_cells": cells, "predicted_opportunities": n_predicted * len(fields),
                                "gold_opportunities": n_gold * len(fields)},
        "output_full_records": {"precision": row_precision, "recall": row_recall, "f1": row_f1,
                                "correct_records": complete_rows, "predicted_records": n_predicted,
                                "gold_records": n_gold},
        "constraint_checks": checks,
        "unresolved_reasons": contract["unresolved_reasons"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True, help="JSON list of named gold records, or {records: [...]} envelope")
    parser.add_argument("--prediction", type=Path, required=True, help="JSON list of named records, or {records: [...]} envelope")
    args = parser.parse_args()
    contract, gold, prediction = (json.loads(path.read_text()) for path in (args.contract, args.gold, args.prediction))
    if isinstance(gold, dict):
        gold = gold.get("records")
    print(json.dumps(score_contract(contract, gold, prediction), ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
