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

INVENTORY_SHA256 = '3343c3ba0e9dda6c533ef14e555aee9dc38d8ca6ac2fccfa17fec5f36c527afb'
EXPECTED_IDS = ['RAN4_P3_CQ4-4']
EXPECTED_CASES = [{'id': 'RAN4_P3_CQ4-4', 'status': 'SEALED_LOCAL', 'decision': 'clarification_required', 'subtype': 'missing_distinct_Spec_top10_selection_rule', 'question_sha256': '6b3b0679cf3334e8aa0bef7733258fcc2e05ea97248338688d73d0a5b1b132f2', 'query_sha256': 'a81576558564f0a7d979077cf3c46769fbb95bcc80e4003b0df4a406e1b62424', 'criteria_sha256': 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'ROOT_seal_sha256': 'b983c8a138f1137ce51a69baf0afa1d5c862fdb8dbed579cd9b03d71a481396f', 'primary': {'path': 'cases/RAN4_P3_CQ4-4/contract/primary_review.json', 'bytes': 41156, 'sha256': 'bc32bae7b60e5b16fbae561887221c4c284fd6d4ec2062fedc2669a9682f4b20'}, 'secondary': {'path': 'cases/RAN4_P3_CQ4-4/contract/secondary_review.json', 'bytes': 9757, 'sha256': '2f5842c822541c648147fa0a94f6dd683523122c41952727d247fc081c7a989e'}, 'verifier': 'cases/RAN4_P3_CQ4-4/verify.py', 'expert_validation_n': 0, 'new_admissions': 0}]
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
    for key,name in [('final_packet','ROOT_final_packet.json'),('ROOT_actual_portable_relocation','ROOT_actual_portable_replay.json'),('actual_agent_adverse_controls','actual_adverse_controls.json')]:
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
        require(child['status']=='PASS' and child['id']==case['id'] and child['recommendation']=='clarification_required', 'Work Item classification identity')
        require(child['raw_paths']==818 and child['Resolution_nodes']==79 and child['CRs']==809 and child['recorded_Spec_groups']==14 and child['reopened_original_registers']==11, 'Complete recorded trace and source registers')
        require(child['all809_source_metadata'] is True and child['all818_frozen_content_reference_literals'] is True and child['reviewers_in_packet']==2, 'Actual source and independent reviews')
        require(child['new_admissions']==child['API_calls']==child['native_calls']==0 and child['complete79_body_boundary_certification'] is False, 'Classification-only bounded authority')
        require(all(child['no_host_audit'][k]==0 for k in ['host_private_open_attempts','write_open_attempts','network_calls','subprocess_calls','SQL_calls']), 'Offline child private/SQL/network/subprocess/write0')
        results.append({"id": case["id"], "classification": case["decision"], "subtype": case["subtype"], "child_result": child})
    print(json.dumps({"status": "PASS", "cases": results, "new_admissions": 0,
                      "expert_validation_n": 0, "model_API_calls": 0, "new_native_calls": 0,
                      "scope": "Included source and frozen-projection replay plus pinned historical whole-database receipts; no fresh full database or model execution."}, ensure_ascii=False))


if __name__ == "__main__":
    main()
