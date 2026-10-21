"""Replay a sealed original-question status from included original evidence."""
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

INVENTORY_SHA256 = '2ae4e457947f7cc1d7dcf91754b5c3bfb1673df1d2ef289f7dcd34717b648cb5'
EXPECTED_IDS = ['RAN1_P2_CQ3-3']
EXPECTED_CASES = [{'id': 'RAN1_P2_CQ3-3', 'status': 'SEALED_LOCAL', 'decision': 'clarification_required', 'subtype': 'cross_meeting_numeric_agenda_and_technology_scope_conflict', 'question_sha256': '1558bcdf6940b5e99049245452034297541ad8e4afdeca6a2ff022f91ea41886', 'query_sha256': '5722fc5de43df1afb077b3cffd4e193a4ed9dfb15f5acbfe2e725929879ec2b7', 'criteria_sha256': 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'ROOT_seal_sha256': 'a31d880ce9957e2919903244df9a526e9cbf9ca8a7a05362ebdcab5eb3a660cb', 'primary': {'path': 'cases/RAN1_P2_CQ3-3/contract/primary_review.json', 'bytes': 16443, 'sha256': 'f310651a9cc23dd079147633d15fa0e861fb9cbe26d370c3ccfd769fab1121f4'}, 'secondary': {'path': 'cases/RAN1_P2_CQ3-3/contract/secondary_review.json', 'bytes': 15838, 'sha256': '1684a579e0a82e115ab77167e0ea0faaeea129e5d1657d9a397914b281bd0fa5'}, 'verifier': 'cases/RAN1_P2_CQ3-3/reproduce.py', 'expert_validation_n': 0, 'new_admissions': 0}]
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
        "classification": 'clarification_required',
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
    seal=json.loads(read('ROOT_final_seal.json'))
    case=bindings[0]
    require(pin('ROOT_final_seal.json')['sha256']==case['ROOT_seal_sha256'], 'ROOT seal identity')
    require(seal['status']=='SEALED_LOCAL_CLASSIFICATION_PENDING_SCOPED_PUBLICATION' and seal['decision']==case['decision'] and seal['criteria_sha256']==CRITERIA_SHA256, 'Sealed classification authority')
    require(seal['original560_pass_increment']==0 and seal['separate_API_evaluation_required'] is False, 'Classification versus answer admission')
    for key,name in [('final_packet','ROOT_final_packet.json'),('ROOT_actual_replay','ROOT_actual_portable_replay.json'),('actual_adverse_controls','actual_adverse_controls.json')]:
        require(exact(pin(name),{k:seal[key][k] for k in ['bytes','sha256']}), 'Actual sealed publication evidence')
    results = []
    for case in bindings:
        require(case["status"] == "SEALED_LOCAL" and case["decision"] == 'clarification_required', "Unsealed case")
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
        require(child['status']=='PASS' and child['new_admissions']==0 and len(child['cases'])==1, 'Agenda diagnostic identity')
        value=child['cases'][0]
        require(value['id']==case['id'] and value['recommendation']=='clarification_required' and value['source_reports']==2 and value['frozen_documentary_paths']==5905 and value['full_NR_MIMO_truth_claimed'] is False, 'Agenda source and documentary count scope')
        results.append({"id": case["id"], "classification": case["decision"], "subtype": case["subtype"], "child_result": child})
    print(json.dumps({"status": "PASS", "cases": results, "new_admissions": 0,
                      "expert_validation_n": 0, "model_API_calls": 0, "new_native_calls": 0,
                      "scope": "Included source and frozen-projection replay plus pinned historical whole-database receipts; no fresh full database or model execution."}, ensure_ascii=False))


if __name__ == "__main__":
    main()
