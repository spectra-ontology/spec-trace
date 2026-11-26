#!/usr/bin/env python3
"""Owner-only blind-study input validation, commitment, and original native scorer.

There are no model calls. Do not expose this file or its source paths to subjects.
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "CLAUDE.md").is_file())
STUDY = ROOT / "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/release_preparation/vldb_release/studies/matched_domains"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate():
    protocol = load(HERE / "protocol.json")
    schedule = load(HERE / "schedule.json")
    assert len(schedule) == 32 == len({x["runId"] for x in schedule})
    assert sha(HERE / "schedule.json") == protocol["scheduleSha256"]
    assert sha(HERE / "cohort_manifest.json") == protocol["cohortManifestSha256"]
    assert protocol["requestedModels"] == ["gpt-6.2-sol", "gpt-6.2-astra", "gpt-6.1-terra", "gpt-6-luna"]
    for name, expected in protocol["sources"].items():
        assert sha(ROOT / name) == expected, name
    common = None
    domains = load(STUDY / "frozen/categorical_domains.json")
    for key, pin in protocol["packets"].items():
        assert sha(HERE / pin["path"]) == pin["sha256"], key
        assert sha(HERE / pin["jsonPath"]) == pin["jsonSha256"], key
        groups = load(HERE / pin["jsonPath"])
        language = key.split("_", 1)[0]
        original = json.loads((STUDY / f"frozen/writer_{language}.txt").read_text().split("\n\n", 1)[1])
        view = []
        for g, old in zip(groups, original):
            assert g["schema"] == old["schema"] and g["items"] == old["items"]
            assert g["interface_mapping"] == domains[g["wg"]]["Encoding fact"]
            assert set(g) == {"wg", "schema", "interface_mapping", "items"} | ({"categorical_domains"} if key.endswith("schema_domains") else set())
            if key.endswith("schema_domains"):
                assert g["categorical_domains"] == {k: v for k, v in domains[g["wg"]].items() if k != "Encoding fact"}
            assert all(set(item) == {"id", "question", "fields"} for item in g["items"])
            view.extend(g["items"])
        assert len(view) == len({x["id"] for x in view}) == 50
        assert common is None or common == view
        common = view
    for model in protocol["requestedModels"]:
        cells = [(r["language"], r["condition"], r["repetition"]) for r in schedule if r["requestedModel"] == model]
        assert len(set(cells)) == len(cells) == 8
    return {"packets": 4, "questionsPerPacket": 50, "questionSchemaBytesMatchFrozen": True,
            "domainsParity": True, "subjectsStartedByHarness": 0, "sessionsPlanned": 32}


def check_lock():
    lock = load(HERE / "protocol_lock.json")
    for name, expected in lock["files"].items():
        assert sha(HERE / name) == expected, "Frozen file changed: " + name
    return lock


def freeze():
    assert not (HERE / "protocol_lock.json").exists(), "Already frozen"
    assert not (HERE / "submissions").exists(), "First response preceded protocol freeze"
    result = validate()
    names = ["prepare.py", "harness.py", "README.md", "protocol.json", "schedule.json", "cohort_manifest.json"]
    names.extend(str(p.relative_to(HERE)) for p in sorted((HERE / "packets").iterdir()))
    write(HERE / "protocol_lock.json", {"frozenAtUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
          "files": {n: sha(HERE / n) for n in names}, "validation": result, "queriesGeneratedBeforeFreeze": 0})
    return result


def commit(run_id, response_path, receipt_path):
    check_lock()
    run = next(r for r in load(HERE / "schedule.json") if r["runId"] == run_id)
    receipt = load(receipt_path)
    assert receipt["requestedModel"] == run["requestedModel"]
    assert receipt["subjectSessionId"] and receipt["forkTurns"] == "none"
    assert receipt["reasoningEffort"] == "medium" and receipt["firstSubmission"] is True
    assert receipt["feedbackBeforeSubmission"] is False
    destination = HERE / "submissions" / run_id
    assert not destination.exists(), "Committed response cannot be replaced"
    destination.mkdir(parents=True)
    shutil.copyfile(response_path, destination / "response.raw")
    shutil.copyfile(receipt_path, destination / "session_receipt.json")
    result = {"run": run, "committedAtUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "rawSha256": sha(destination / "response.raw"), "receiptSha256": sha(destination / "session_receipt.json")}
    try:
        text = response_path.read_text(encoding="utf-8")
        try:
            decoded = json.loads(text)
            queries = decoded["queries"] if isinstance(decoded, dict) else decoded
        except json.JSONDecodeError:
            queries = [json.loads(line) for line in text.splitlines() if line.strip()]
        order = load(HERE / "cohort_manifest.json")["packetOrder"]
        assert isinstance(queries, list) and len(queries) == 50
        assert [q["id"] for q in queries] == order, "Missing, duplicated or reordered packet IDs"
        assert all(set(q) == {"id", "query"} and isinstance(q["query"], str) and q["query"].strip() for q in queries)
        output = destination / (run["language"] + "_" + run["repetition"] + ".jsonl")
        output.write_text("".join(json.dumps(q, ensure_ascii=False) + "\n" for q in queries))
        result.update(status="complete", items=50, queryFile=output.name, querySha256=sha(output))
    except Exception as exc:
        result.update(status="invalid_first_submission", error=f"{type(exc).__name__}: {exc}")
    write(destination / "commitment.json", result)
    return result


def score(run_id):
    check_lock()
    schedule = load(HERE / "schedule.json")
    run = next(r for r in schedule if r["runId"] == run_id)
    # Global primary commitment prevents score feedback during the A generation wave.
    required = [r for r in schedule if r["repetition"] == run["repetition"]]
    assert all((HERE / "submissions" / r["runId"] / "commitment.json").is_file() for r in required), "Commit all16 phase sessions first"
    directory = HERE / "submissions" / run_id
    commit_record = load(directory / "commitment.json")
    assert sha(directory / "response.raw") == commit_record["rawSha256"]
    assert sha(directory / "session_receipt.json") == commit_record["receiptSha256"]
    assert commit_record["status"] == "complete", "Preserve invalid first response; record missingness rather than fabricate a model query. Partial-batch execution requires an explicit owner extension."
    assert sha(directory / commit_record["queryFile"]) == commit_record["querySha256"]
    receipt = load(directory / "session_receipt.json")
    name = run["language"] + "_" + run["repetition"]
    metadata = {name: {"actualModels": receipt.get("actualModels", []), "modelIdentityStatus": "unavailable" if not receipt.get("actualModels") else "observed",
                       "requestedModel": run["requestedModel"], "provenanceReceipt": str(directory / "session_receipt.json"),
                       "querySha256": commit_record["querySha256"]}}
    write(directory / "generation_metadata_input.json", metadata)
    source = HERE.parent.parent / "matched_interface/experiment.py"
    spec = importlib.util.spec_from_file_location("matched_original_native_execution", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.RUNS = [(run["language"], run["repetition"])]
    destination = HERE / "execution" / run_id
    assert not destination.exists(), "First execution already recorded; do not rerun selectively"
    module.score(directory, directory / "generation_metadata_input.json", destination)
    return {"scored": run_id, "output": str(destination), "sourceSha256": sha(source)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["validate", "freeze", "commit", "score"])
    parser.add_argument("--run-id")
    parser.add_argument("--response", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    if args.action == "validate": result = validate()
    elif args.action == "freeze": result = freeze()
    elif args.action == "commit": result = commit(args.run_id, args.response, args.receipt)
    else: result = score(args.run_id)
    print(json.dumps(result, ensure_ascii=False))
