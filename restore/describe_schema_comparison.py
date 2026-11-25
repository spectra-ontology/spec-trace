"""Recompute the current typed-slot comparison from frozen evidence and review."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bound_json(release, binding):
    path = release / binding["path"]
    if digest(path) != binding["sha256"]:
        raise ValueError("Source SHA-256 mismatch: " + binding["path"])
    return json.loads(path.read_text(encoding="utf-8"))


def describe(release):
    review_path = release / "sources/schema_comparison_review.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    frozen = bound_json(release, review["frozen_report"])
    elements = [element["key"] for element in review["elements"]]
    if len(elements) != len(set(elements)):
        raise ValueError("Repeated element key")
    element_set = set(elements)
    families, identities = Counter(), set()
    for binding in review["item_sources"]:
        path = release / binding["path"]
        if digest(path) != binding["sha256"]:
            raise ValueError("Item SHA-256 mismatch: " + binding["path"])
        for line in path.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            if item["id"] in identities:
                raise ValueError("Repeated item identity: " + item["id"])
            identities.add(item["id"])
            families[item["family"]] += 1
    if sum(families.values()) != frozen["items"] or set(families) != set(frozen["needs"]):
        raise ValueError("Main workload differs from the frozen comparison contract")
    for family, needs in frozen["needs"].items():
        if not set(needs) <= element_set:
            raise ValueError("Unknown required element: " + family)

    original = {row["name"]: row for row in frozen["resources"]}
    overrides = {row["name"]: row for row in review["overrides"]}
    if len(original) != len(frozen["resources"]) or len(overrides) != len(review["overrides"]):
        raise ValueError("Repeated resource name")
    if not set(overrides) <= set(original):
        raise ValueError("Review overrides an unknown resource")
    if review["process_resource"]["name"] in original:
        raise ValueError("Process resource duplicates a comparison resource")

    resources = []
    for name in [*original, review["process_resource"]["name"]]:
        assessment = (overrides.get(name, original.get(name))
                      if name in original else review["process_resource"])
        present = set(assessment["has"])
        unknown = set(assessment.get("undetermined", []))
        if not (present | unknown) <= element_set or present & unknown:
            raise ValueError("Invalid slot assessment: " + name)
        absent = element_set - present - unknown
        by_family, expressible, undetermined = {}, 0, 0
        for family, count in sorted(families.items()):
            needs = set(frozen["needs"][family])
            missing, uncertain = sorted(needs & absent), sorted(needs & unknown)
            state = False if missing else (None if uncertain else True)
            if state is True:
                expressible += count
            elif state is None:
                undetermined += count
            by_family[family] = {"items": count, "expressible": state,
                                 "missing": missing, "undetermined": uncertain}
        row = {
            "name": name,
            "assessment": ("review_override" if name in overrides else
                           "frozen_report" if name in original else "released_process_schema"),
            "cells": {element["id"]: ("typed" if element["key"] in present else
                      "undetermined" if element["key"] in unknown else "absent")
                      for element in review["elements"]},
            "has": [key for key in elements if key in present],
            "undetermined": [key for key in elements if key in unknown],
            "expressibleItems": None if undetermined else expressible,
            "knownExpressibleItems": expressible,
            "undeterminedItems": undetermined,
            "byFamily": by_family,
            "source": assessment["source"],
            "basis": assessment["basis"],
        }
        if name in original:
            row["frozenExpressibleItems"] = original[name]["expressibleItems"]
        if "reviewed_scope" in assessment:
            row["reviewed_scope"] = assessment["reviewed_scope"]
        resources.append(row)
    return {
        "scope": review["scope"],
        "items": sum(families.values()),
        "familyCounts": dict(sorted(families.items())),
        "needs": frozen["needs"],
        "elementsEveryFamilyNeeds": sorted(set.intersection(
            *(set(needs) for needs in frozen["needs"].values()))),
        "comparisonResources": len(original),
        "review": {"path": "sources/schema_comparison_review.json", "sha256": digest(review_path)},
        "frozenReport": review["frozen_report"],
        "itemSources": review["item_sources"],
        "elements": review["elements"],
        "resources": resources,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = describe(args.release.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"items": result["items"], "comparison_resources": result["comparisonResources"],
                      "process_resources": 1, "out": str(args.out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
