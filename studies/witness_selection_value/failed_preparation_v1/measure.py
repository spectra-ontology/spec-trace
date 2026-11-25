#!/usr/bin/env python3
"""Compare two fixed anchor selections using the same recorded SQL controls."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import shutil
import sqlite3
import sys
import tempfile
import time


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def normalize(rows):
    return sorted(set(tuple(None if cell is None else str(cell) for cell in row) for row in rows))


class UnfilteredPools:
    """Keep exactly the original enumerator's pre-predicate candidate universe."""
    def __init__(self, builder, protocol, wg, path):
        self.builder, self.protocol, self.wg = builder, protocol, wg
        self.counts, self.best = Counter(), {}
        self.digest = hashlib.sha256()
        self.handle = gzip.open(path, "wt", encoding="utf-8", newline="\n")

    def consider(self, stratum, candidate, witness, conditions):
        self.counts[stratum] += 1
        row = {"stratum": stratum, "candidate": candidate,
               "original_predicate_results": conditions, "properties": witness}
        line = canonical(row) + "\n"
        self.digest.update(line.encode())
        self.handle.write(line)
        rank = (self.builder.selection_digest(self.protocol["study"], self.wg, stratum, candidate),
                canonical(candidate))
        if stratum not in self.best or rank < self.best[stratum][0]:
            self.best[stratum] = (rank, {"candidate": candidate, "witness": witness,
                                       "original_predicate_results": conditions})


def independent_relations(connection):
    """Read the raw public relations separately from the original builder parser."""
    members, links, outcomes = defaultdict(set), defaultdict(set), []
    for document, pack in connection.execute("SELECT cr,pack_id FROM cr_in_pack"):
        members[pack].add(document)
    identities = {identifier: (specification, release, clause)
                  for identifier, specification, release, clause in connection.execute(
                      "SELECT id,spec,release,clause FROM section")}
    for document, section in connection.execute("SELECT cr,section_id FROM cr_modifies_section"):
        links[document].add(identities[section])
    resolution_meetings = dict(connection.execute("SELECT id,meeting_id FROM resolution"))
    for document, code, resolution in connection.execute(
            "SELECT target,code,resolution_id FROM disposition "
            "WHERE scope='whole_target' AND evidence_status='source_verified'"):
        outcomes.append((document, code, resolution_meetings[resolution]))
    return members, links, outcomes


def independent_gold(relations, family, anchor):
    members, links, outcomes = relations
    if family == "pack_disposition_counts":
        kind, cohort = anchor
        pairs = {(code, document) for document, code, meeting in outcomes
                 if (document in members[cohort] if kind == "pack" else meeting == cohort)}
        return normalize(Counter(code for code, _ in pairs).items())
    if family in ("shared_clauses", "exclusive_clauses"):
        _, first, second = anchor
        answer = links[first] & links[second] if family == "shared_clauses" else links[first] - links[second]
        return normalize(answer)
    if family in ("both_clause_documents", "conjunction_disposition_counts"):
        pack, first, second = anchor
        selected = {document for document in members[pack]
                    if tuple(first) in links[document] and tuple(second) in links[document]}
        if family == "both_clause_documents":
            return normalize((document.removeprefix("tdoc:"),) for document in selected)
        pairs = {(code, document) for document, code, _ in outcomes if document in selected}
        return normalize(Counter(code for code, _ in pairs).items())
    if family == "largest_clause_footprint":
        counts = {document: len(links[document]) for document in members[anchor[0]]}
        high = max(counts.values())
        return normalize((document.removeprefix("tdoc:"), count)
                         for document, count in counts.items() if count == high)
    if family == "members_without_clause_records":
        return normalize((document.removeprefix("tdoc:"),)
                         for document in members[anchor[0]] if not links[document])
    raise ValueError(("Unknown family", family))


def summarize_arm(items):
    all_controls = [control for item in items for control in item["controls"]]
    families, groups = {}, {}
    for key, target in (("family", families), ("wg", groups)):
        for label in sorted({item[key] for item in items}):
            subset = [item for item in items if item[key] == label]
            controls = [control for item in subset for control in item["controls"]]
            target[label] = {"tasks": len(subset), "controls": len(controls),
                             "discriminating": sum(row["discriminating"] for row in controls),
                             "wrong_output_classes": sum(item["wrong_output_classes"] for item in subset)}
    anchors = Counter(canonical([item["wg"], item["family"], item["anchor"]]) for item in items)
    unique_controls = {}
    for item in items:
        for control in item["controls"]:
            identity = canonical([item["wg"], item["family"], item["anchor"], control["name"]])
            if identity in unique_controls:
                assert unique_controls[identity] == control["discriminating"]
            unique_controls[identity] = control["discriminating"]
    return {"tasks": len(items), "unique_family_anchors": len(anchors),
            "anchor_repetitions": [{"identity": json.loads(key), "occurrences": value}
                                   for key, value in sorted(anchors.items()) if value > 1],
            "reference_python_agreements": sum(item["reference_python_equal"] for item in items),
            "controls": len(all_controls),
            "unique_family_anchor_controls": len(unique_controls),
            "unique_discriminating_family_anchor_controls": sum(unique_controls.values()),
            "tasks_with_discriminating_control": sum(any(row["discriminating"] for row in item["controls"]) for item in items),
            "successful_controls": sum(row["execution"]["status"] == "ok" for row in all_controls),
            "discriminating_controls": sum(row["discriminating"] for row in all_controls),
            "required_controls": sum(row["required"] for row in all_controls),
            "required_discriminating": sum(row["required"] and row["discriminating"] for row in all_controls),
            "wrong_output_classes": sum(item["wrong_output_classes"] for item in items),
            "by_family": families, "by_working_group": groups}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, default=Path(__file__).with_name("protocol.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if sqlite3.sqlite_version != "3.37.2":
        raise RuntimeError("This comparison pins SQLite 3.37.2")
    resource.setrlimit(resource.RLIMIT_AS, (2 << 30, 2 << 30))
    plan = json.loads(args.protocol.read_text())
    if sha(Path(__file__)) != plan["implementation_sha256"]:
        raise ValueError("Implementation differs from the pre-execution protocol")
    study = args.release / "studies/semantic_witnesses"
    for relative, expected in plan["input_sha256"].items():
        if sha(study / relative) != expected:
            raise ValueError(("Frozen input differs", relative))
    specification = importlib.util.spec_from_file_location("original_witness_builder", study / "build_semantic_witnesses.py")
    builder = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(builder)
    original_protocol = json.loads((study / "protocol.json").read_text())
    original = json.loads((study / "measurement/selection_and_gold.json").read_text())
    initial = json.loads((study / "measurement/execution.json").read_text())
    extra = json.loads((study / "supplementary_omitted_controls.json").read_text())
    control_contract = {item["id"]: {row["name"]: row for row in item["mutations"]} for item in initial["items"]}
    for item in extra["items"]:
        rows = item.get("mutations", item.get("controls"))
        if rows is None:
            rows = [item]
        for row in rows:
            identity = item.get("id", row.get("item_id"))
            control_contract[identity][row["name"]] = row
    assert sum(map(len, control_contract.values())) == 200
    old_cells = {(cell["wg"], cell["stratum"]): cell for cell in original["cells"]}
    old_tasks = {item["id"]: item for item in original["items"]}
    definitions = {row["id"]: row for row in original_protocol["strata"]}
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    selected, inputs, censuses = [], [], []
    executions = {"witness": [], "hash_without_final_witness_predicates": []}
    prepared = {arm: [] for arm in executions}
    pins = json.loads((study / "database_inputs.json").read_text())["inputs"]
    for wg in original_protocol["working_groups"]:
        pin = next(row for row in pins if row["wg"] == wg)
        plain = args.release / "sqlite" / (wg + ".sqlite")
        source = plain if plain.exists() else plain.with_suffix(".sqlite.gz")
        assert sha(source) == pin["source_sha256"]
        with tempfile.TemporaryDirectory(prefix="witness_anchor_comparison_") as temporary:
            database = source
            if source.suffix == ".gz":
                database = Path(temporary) / (wg + ".sqlite")
                with gzip.open(source, "rb") as origin, database.open("wb") as target:
                    shutil.copyfileobj(origin, target)
            assert sha(database) == pin["database_sha256"]
            connection = sqlite3.connect("file:" + str(database.resolve()) + "?mode=ro&immutable=1", uri=True)
            connection.execute("PRAGMA query_only=ON")
            connection.execute("PRAGMA cache_size=-16384")
            data = builder.data_from_connection(connection)
            relations = independent_relations(connection)
            pool_path = args.output / ("candidate_universe_" + wg + ".jsonl.gz")
            pool = UnfilteredPools(builder, original_protocol, wg, pool_path)
            builder.enumerate_pools(data, pool)
            pool.handle.close()
            for definition in original_protocol["strata"]:
                name = definition["id"]
                old = old_cells[wg, name]
                assert pool.counts[name] == old["candidate_universe_count"], (wg, name)
                record = {"wg": wg, "stratum": name, "family": definition["family"],
                          "pre_predicate_candidates": pool.counts[name],
                          "original_witness_eligible": old["eligible_candidates"],
                          "original_status": old["status"]}
                if old["status"] != "available":
                    record["comparison_status"] = "unmatched_original_unavailable"
                    censuses.append(record)
                    continue
                rank, best = pool.best[name]
                baseline_cell = dict(old, selected=best, selection_sha256=rank[0])
                baseline_task = builder.task(data, baseline_cell)
                identity = wg + "-witness-" + name
                witness_task = old_tasks[identity]
                record.update(comparison_status="paired", witness_anchor=witness_task["anchor"],
                              baseline_anchor=baseline_task["anchor"], baseline_selection_sha256=rank[0],
                              baseline_original_predicate_results=best["original_predicate_results"],
                              same_anchor=witness_task["anchor"] == baseline_task["anchor"])
                censuses.append(record)
                selected.append(record)
                for arm, task in (("witness", witness_task),
                                  ("hash_without_final_witness_predicates", baseline_task)):
                    gold = independent_gold(relations, task["family"], task["anchor"])
                    assert gold == normalize(task["gold"]), (arm, identity, "Python derivations differ")
                    prepared[arm].append(dict(task, independently_derived_gold=gold,
                                              planned_control_names=sorted(control_contract[identity])))
            connection.close()
            unchanged = sha(database) == pin["database_sha256"] and sha(source) == pin["source_sha256"]
            assert unchanged
            inputs.append(dict(pin, source_unchanged=True, database_unchanged=True))
            inputs[-1].update(candidate_file=pool_path.name, candidate_file_sha256=sha(pool_path),
                              candidate_uncompressed_sha256=pool.digest.hexdigest())
        print(json.dumps({"stage": "prepare", "wg": wg,
                          "paired_cells": sum(row["wg"] == wg for row in selected)}, sort_keys=True), flush=True)
    assert len(selected) == 66 and len(censuses) == 95
    save(args.output / "selection.json", {"protocol_sha256": sha(args.protocol), "inputs": inputs,
                                          "cells": censuses, "prepared_arms": prepared})
    save(args.output / "selection_freeze.json", {
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_sha256": sha(args.protocol), "implementation_sha256": sha(Path(__file__)),
        "state": "All candidate universes and both complete anchor selections frozen before any reference or control execution",
        "reference_executions_so_far": 0, "control_executions_so_far": 0,
        "files": {path.name: sha(path) for path in sorted(args.output.iterdir()) if path.is_file()}})
    print(json.dumps({"stage": "selection_frozen", "sha256": sha(args.output / "selection_freeze.json")}), flush=True)
    for wg in original_protocol["working_groups"]:
        pin = next(row for row in pins if row["wg"] == wg)
        plain = args.release / "sqlite" / (wg + ".sqlite")
        source = plain if plain.exists() else plain.with_suffix(".sqlite.gz")
        assert sha(source) == pin["source_sha256"]
        with tempfile.TemporaryDirectory(prefix="witness_anchor_comparison_measure_") as temporary:
            database = source
            if source.suffix == ".gz":
                database = Path(temporary) / (wg + ".sqlite")
                with gzip.open(source, "rb") as origin, database.open("wb") as target:
                    shutil.copyfileobj(origin, target)
            assert sha(database) == pin["database_sha256"]
            connection = sqlite3.connect("file:" + str(database.resolve()) + "?mode=ro&immutable=1", uri=True)
            connection.execute("PRAGMA query_only=ON")
            connection.execute("PRAGMA cache_size=-16384")
            relations = independent_relations(connection)
            for arm, tasks in prepared.items():
                for task in (item for item in tasks if item["wg"] == wg):
                    identity, name = task["id"], task["stratum"]
                    definition = definitions[name]
                    gold = independent_gold(relations, task["family"], task["anchor"])
                    assert gold == task["independently_derived_gold"]
                    reference = builder.execute(connection, task["reference_sql"])
                    assert reference["status"] == "ok" and reference["rows"] == gold, (arm, identity, reference)
                    controls = []
                    for control_name in sorted(control_contract[identity]):
                        sql = task["mutations"][control_name]
                        outcome = builder.execute(connection, sql)
                        different = outcome["status"] == "ok" and outcome["rows"] != gold
                        if arm == "witness":
                            assert sql == control_contract[identity][control_name]["sql"]
                            assert outcome["status"] == control_contract[identity][control_name]["status"]
                            assert outcome.get("rows") == normalize(control_contract[identity][control_name].get("rows", []))
                        controls.append({"name": control_name, "required": control_name in definition["mutations"],
                                         "sql": sql, "execution": outcome, "discriminating": different})
                    wrong_classes = {canonical(control["execution"]["rows"]) for control in controls if control["discriminating"]}
                    output_classes = defaultdict(list)
                    output_classes[canonical(gold)].append("reference")
                    for control in controls:
                        if control["execution"]["status"] == "ok":
                            output_classes[canonical(control["execution"]["rows"])].append(control["name"])
                    executions[arm].append({"id": identity, "wg": wg, "stratum": name, "family": task["family"],
                                            "anchor": task["anchor"], "question": task["question"], "fields": task["fields"],
                                            "selection_sha256": task["selection_sha256"], "gold": gold,
                                            "reference_sql": task["reference_sql"], "reference": reference,
                                            "reference_python_equal": reference["rows"] == gold,
                                            "controls": controls, "wrong_output_classes": len(wrong_classes),
                                            "output_equivalence_classes": [{"rows": json.loads(rows), "queries": names,
                                                                            "is_reference_class": "reference" in names}
                                                                           for rows, names in sorted(output_classes.items())]})
            connection.close()
            unchanged = sha(database) == pin["database_sha256"] and sha(source) == pin["source_sha256"]
            assert unchanged
        print(json.dumps({"stage": "measure", "wg": wg}, sort_keys=True), flush=True)
    summaries = {arm: summarize_arm(items) for arm, items in executions.items()}
    observed = summaries["witness"]
    assert observed["discriminating_controls"] == 162 and observed["required_discriminating"] == 113
    pair_matrix = []
    for witness, baseline in zip(executions["witness"], executions["hash_without_final_witness_predicates"]):
        assert witness["id"] == baseline["id"]
        for first, second in zip(witness["controls"], baseline["controls"]):
            assert first["name"] == second["name"]
            pair_matrix.append({"task": witness["id"], "wg": witness["wg"], "family": witness["family"],
                                "control": first["name"], "witness": first["discriminating"],
                                "hash_without_final_witness_predicates": second["discriminating"],
                                "witness_status": first["execution"]["status"],
                                "baseline_status": second["execution"]["status"]})
    patterns = Counter((row["witness"], row["hash_without_final_witness_predicates"]) for row in pair_matrix)
    summary = {"protocol_sha256": sha(args.protocol), "implementation_sha256": sha(Path(__file__)),
               "planned_original_cells": 95, "paired_available_cells": 66,
               "unpaired_original_unavailable_cells": [row for row in censuses if row["comparison_status"] != "paired"],
               "same_anchor_pairs": sum(row["same_anchor"] for row in selected),
               "arms": summaries, "paired_control_patterns": {f"witness_{int(a)}_baseline_{int(b)}": n for (a, b), n in sorted(patterns.items())},
               "python_version": sys.version, "sqlite_version": sqlite3.sqlite_version,
               "elapsed_seconds": time.monotonic() - started,
               "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               "fresh_model_responses": 0, "input_unchanged": all(row["source_unchanged"] and row["database_unchanged"] for row in inputs)}
    save(args.output / "execution.json", {"protocol_sha256": sha(args.protocol), "arms": executions, "paired_control_matrix": pair_matrix})
    save(args.output / "summary.json", summary)
    save(args.output / "freeze.json", {"protocol_sha256": sha(args.protocol), "implementation_sha256": sha(Path(__file__)),
                                       "files": {path.name: sha(path) for path in sorted(args.output.iterdir()) if path.is_file()}})
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
