"""Replay the independently reviewed UCI source classification from included evidence."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

if sys.flags.optimize != 0:
    raise RuntimeError("Optimized Python is unsupported for evidence verification")
sys.dont_write_bytecode = True

INVENTORY_SHA256 = 'd51865bc6419d08df4c946a656d8ec101da510b54aedf5fc5f845aee8898bfeb'
EXPECTED_IDS = ['RAN1_P2_CQ5-10']
EXPECTED_CASES = [{'id': 'RAN1_P2_CQ5-10', 'status': 'SEALED_LOCAL', 'decision': 'unsupported_frozen_data', 'subtype': 'source_explicit_agreement_amendment_status_unretained', 'question_sha256': 'caeee40fdb6e5ec6848deda1fd54c9e553e10e244c5696ca64e7d797bb1b4727', 'query_sha256': 'bb4d3c24f9fd6d58410de3ab17bf9695a75d6890aa50ad41b0df6332cf2f3192', 'criteria_sha256': 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'necessary_member': 'AGR-121-9.11.3-007 and AGR-121-9.11.3-008', 'ROOT_seal_sha256': '55e1564ed93ea5da9ae84d0597b942d72be64bb25bb17db2a8a2c3688e821dba', 'primary': {'path': 'cases/RAN1_P2_CQ5-10/contract/primary_seven_unit_review.json', 'bytes': 13760, 'sha256': '3226a207ca3c2c536915ca8e6830017d4538529c516e2c8543179f711b3363c2'}, 'secondary': {'path': 'cases/RAN1_P2_CQ5-10/contract/ROOT_secondary_exact_seven_unit_review.json', 'bytes': 5950, 'sha256': '5d07e780e03b3c6dfbb60b07960fc27ce585086147b53f6ba2dbd698761ff50c'}, 'verifier': 'cases/RAN1_P2_CQ5-10/verify.py', 'expert_validation_n': 0, 'new_admissions': 0}]
CRITERIA_SHA256 = "bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def no_symlink(path):
    path = Path(os.path.abspath(path))
    for part in (path, *path.parents):
        require(not part.is_symlink(), "Symlink path: " + str(part))
    return path


HERE = no_symlink(__file__).parent


def read(name):
    rel = Path(name)
    require(not rel.is_absolute() and ".." not in rel.parts, "Unsafe evidence path")
    path = no_symlink(HERE / rel)
    require(stat.S_ISREG(path.stat().st_mode), "Nonregular evidence file: " + name)
    return path.read_bytes()


def pin(name):
    data = read(name)
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def exact(actual, expected):
    return type(actual) is type(expected) and (
        set(actual) == set(expected) and all(exact(actual[k], expected[k]) for k in actual)
        if isinstance(expected, dict) else
        len(actual) == len(expected) and all(exact(a, b) for a, b in zip(actual, expected))
        if isinstance(expected, list) else actual == expected
    )


def main():
    inventory_bytes = read("immutable_inventory.json")
    require(hashlib.sha256(inventory_bytes).hexdigest() == INVENTORY_SHA256, "Inventory fixed pin")
    inventory = json.loads(inventory_bytes)
    require(set(inventory) == {"files"} and type(inventory["files"]) is dict, "Inventory shape")
    files = inventory["files"]
    for name, expected in files.items():
        require(exact(pin(name), expected), "Evidence pin: " + name)
    observed = set()
    for path in HERE.rglob("*"):
        mode = path.lstat().st_mode
        require(not stat.S_ISLNK(mode), "Evidence symlink")
        if stat.S_ISDIR(mode):
            continue
        require(stat.S_ISREG(mode), "Nonregular evidence entry")
        observed.add(path.relative_to(HERE).as_posix())
    require(observed == set(files) | {"manifest.json", "immutable_inventory.json", "reproduce.py"}, "Closed evidence tree")
    manifest = json.loads(read("manifest.json"))
    expected_manifest = {
        "status": "COMPLETED_BOUNDED_SOURCE_CLASSIFICATION_EVIDENCE",
        "ids": EXPECTED_IDS,
        "classification": "unsupported_frozen_data",
        "new_admissions": 0,
        "expert_validation_n": 0,
        "model_API_calls": 0,
        "new_native_calls": 0,
        "inventory": {"path": "immutable_inventory.json", **pin("immutable_inventory.json")},
        "verifier": {"path": "reproduce.py", **pin("reproduce.py")},
    }
    require(exact(manifest, expected_manifest), "Manifest semantic declarations or verifier identity")
    bindings = json.loads(read("sealed_classification_bindings.json"))
    require(exact(bindings, EXPECTED_CASES), "Fixed sealed case bindings")
    results = []
    for case in bindings:
        require(case["status"] == "SEALED_LOCAL" and case["decision"] == "unsupported_frozen_data", "Unsealed case")
        require(case["criteria_sha256"] == CRITERIA_SHA256, "Original criteria identity")
        for review in (case["primary"], case["secondary"]):
            require(exact(pin(review["path"]), {k: review[k] for k in ("bytes", "sha256")}), "Review identity")
        require(case["primary"]["sha256"] != case["secondary"]["sha256"], "Distinct reviews required")
        proc = subprocess.run(
            [sys.executable, "-B", "-I", "-S", str(HERE / case["verifier"])],
            stdin=subprocess.DEVNULL, capture_output=True, text=True,
            env={"PATH": os.environ.get("PATH", ""), "PYTHONHASHSEED": "0"},
        )
        require(proc.returncode == 0, "Child verifier failed: " + case["id"] + " " + proc.stderr[-2000:])
        child = json.loads(proc.stdout)
        require(child['status'] == 'PASS_BOUNDED_SOURCE_STATUS_DIAGNOSTIC' and child['id'] == case['id'], 'UCI diagnostic identity')
        require(child['source_DOCX_replayed'] == 2 and child['affected_condition_status_records'] == 2 and
            child['distinct_nonblind_AI_reviews'] == 2 and child['all_original_cutoff_combinations'] == 5,
            'UCI source/amendment/tie scope')
        require(child['new_native_executions'] == child['new_model_calls'] == child['original560_pass_increment'] == 0 and
            child['optional_full_frozen_SQL_replayed'] is False and child['whole_semantic_absence_claim'] is False,
            'UCI diagnostic versus new admission/execution scope')
        results.append({"id": case["id"], "classification": case["decision"], "subtype": case["subtype"], "child_result": child})
    print(json.dumps({"status": "PASS", "cases": results, "new_admissions": 0,
                      "expert_validation_n": 0, "model_API_calls": 0, "new_native_calls": 0,
                      "scope": "Included source and frozen-projection replay plus pinned historical whole-database receipts; no fresh full database or model execution."}, ensure_ascii=False))


if __name__ == "__main__":
    main()
