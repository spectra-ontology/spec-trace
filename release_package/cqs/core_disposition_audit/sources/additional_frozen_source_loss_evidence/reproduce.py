"""Replay four independently reviewed source classifications from included evidence."""
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

INVENTORY_SHA256 = '807a0d3cfe1b5619271f885281f84eec7dc138f0e7587365b3d4c96f5416a0ee'
EXPECTED_IDS = ['RAN1_P2_CQ5-7', 'RAN1_P2_CQ5-9', 'RAN1_P2_CQ1-7', 'RAN1_P2_CQ1-2']
EXPECTED_CASES = [{'id': 'RAN1_P2_CQ5-7', 'status': 'SEALED_LOCAL', 'decision': 'unsupported_frozen_data', 'subtype': 'own_source_span_loss', 'question_sha256': 'b9622ccfd0b50c7b1397629c397b5a661b48424667801782579dba089649801e', 'query_sha256': '6f4c725979918aa3faeeb35c4561ff57b958ac0f9018f25acf2991c4595693d8', 'criteria_sha256': 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'necessary_member': 'AGR-123-9.3-009', 'ROOT_seal_sha256': '4cfb1bb661f4ca45d882a7021b3f6a4be279fc8479a597c0a746f3f261cb43c5', 'primary': {'path': 'cases/RAN1_P2_CQ5-7/contract/primary.json', 'bytes': 6376, 'sha256': '7a5de32a336c96e69ddd8955fba9feb204fa7fe5ec1f56bcf99d7edd05689758'}, 'secondary': {'path': 'cases/RAN1_P2_CQ5-7/contract/secondary.json', 'bytes': 14788, 'sha256': '56feb936d27930cf9e5294e3ea4d19011d9cfd5a6322baf224258aa580b580e7'}, 'verifier': 'cases/RAN1_P2_CQ5-7/verify_evidence.py', 'expert_validation_n': 0, 'new_admissions': 0}, {'id': 'RAN1_P2_CQ5-9', 'status': 'SEALED_LOCAL', 'decision': 'unsupported_frozen_data', 'subtype': 'own_source_span_loss', 'question_sha256': '7b8fc483bc5b4b867ebd099a84e6bf565e48342f44609c480f74c851791f8b84', 'query_sha256': '409f7242a20e30c402db08ffcdfc493618a5c9911b2f932282bb78807d706a5c', 'criteria_sha256': 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'necessary_member': 'AGR-123-9.3-004', 'ROOT_seal_sha256': 'd457b5dc9ffa9977a2a2a92b1fc820a5e3d8349e8ccfd15134ab8aada35e0aff', 'primary': {'path': 'cases/RAN1_P2_CQ5-9/contract/primary_seven_unit_review.json', 'bytes': 6246, 'sha256': 'a16ed2bf043980dd4f47b5232be4f15c9b18b5bd82068ecb2a634f804e486f4f'}, 'secondary': {'path': 'cases/RAN1_P2_CQ5-9/contract/ROOT_secondary_review.json', 'bytes': 5170, 'sha256': 'fb5fde6759b1faed16d94dd4080a578bd38ae8da6bbf14eaf0e8375d5549a721'}, 'verifier': 'cases/RAN1_P2_CQ5-9/reproduce.py', 'expert_validation_n': 0, 'new_admissions': 0}, {'id': 'RAN1_P2_CQ1-7', 'status': 'SEALED_LOCAL', 'decision': 'unsupported_frozen_data', 'subtype': 'own_source_span_loss', 'question_sha256': 'b6725b079b8eae22ff1566df69a8b7ce1269027f04d84e23582c657aeafcb3a7', 'query_sha256': '763a87501c5baf430405f1ac7b266ae4a42e6bd61df60ef0c0e0dd7bdd34abb8', 'criteria_sha256': 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'necessary_member': 'AGR-123-9.3-010', 'ROOT_seal_sha256': 'ff5edaf97122dab70cb97b776b29092f222e86082830605677eeec19e40dd97c', 'primary': {'path': 'cases/RAN1_P2_CQ1-7/contract/primary_seven_unit_review.json', 'bytes': 5802, 'sha256': 'fa68cbd3d38cf9b6a3052cb748ec7fbd2df8c749cf9197c2e5795a02f4e43107'}, 'secondary': {'path': 'cases/RAN1_P2_CQ1-7/contract/ROOT_secondary_review.json', 'bytes': 5488, 'sha256': '4e6900a82bc9c075b0902da20359f2e3acb59dd3a2c60f8868f2da0fa0a33634'}, 'verifier': 'cases/RAN1_P2_CQ1-7/reproduce.py', 'expert_validation_n': 0, 'new_admissions': 0}, {'id': 'RAN1_P2_CQ1-2', 'status': 'SEALED_LOCAL', 'decision': 'unsupported_frozen_data', 'subtype': 'source_explicit_agreement_amendment_status_unretained', 'question_sha256': 'c457946bfcbc8319fc66dace3d37dee26c4920dcd64405e4cb4de439aa8d9817', 'query_sha256': 'cb94b26a209ef26d275d5093f911a1ac6c85c356136e37da534da876c263ddc8', 'criteria_sha256': 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'necessary_member': 'AGR-100-5.1-003', 'ROOT_seal_sha256': '4083bc15e69931d72993f27599403edfc3e1abe35782af4fc88bc4af6cf47a48', 'primary': {'path': 'cases/RAN1_P2_CQ1-2/local_final_review.json', 'bytes': 17272, 'sha256': 'c34c6e4aca8e42b951b39244cf397861da44f78ad3824187f1b59caa975abfd3'}, 'secondary': {'path': 'cases/RAN1_P2_CQ1-2/contract/ROOT_secondary_exact_seven_unit_review.json', 'bytes': 6114, 'sha256': '94308294a1226ffe6ba1326068eb97f6a82c8dda88433f4b715040dda704baf1'}, 'verifier': 'cases/RAN1_P2_CQ1-2/verify_diagnostic.py', 'expert_validation_n': 0, 'new_admissions': 0}]
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
        require(child.get("status") == "PASS", "Child status")
        if case["id"] == "RAN1_P2_CQ5-7":
            require(child["id"] == case["id"] and child["bounded_recommendation"] == "unsupported_frozen_data", "MIMO classification")
            require(child["public_admissions"] == 0 and type(child["public_admissions"]) is int, "MIMO admission declaration")
        elif case["id"] == "RAN1_P2_CQ1-2":
            require(child["id"] == case["id"] and child["proposed_disposition"] == "unsupported_frozen_data", "UL classification")
            require(child["new_admissions"] == 0 and type(child["new_admissions"]) is int, "UL admission declaration")
        else:
            require(len(child["cases"]) == 1 and child["cases"][0]["id"] == case["id"], "Single case identity")
            require(child["cases"][0]["classification"] == "unsupported_frozen_data", "Single case classification")
            require(child["new_admissions"] == 0 and type(child["new_admissions"]) is int, "Single case admission declaration")
        results.append({"id": case["id"], "classification": case["decision"], "subtype": case["subtype"], "child_result": child})
    print(json.dumps({"status": "PASS", "cases": results, "new_admissions": 0,
                      "expert_validation_n": 0, "model_API_calls": 0, "new_native_calls": 0,
                      "scope": "Included source and frozen-projection replay plus pinned historical whole-database receipts; no fresh full database or model execution."}, ensure_ascii=False))


if __name__ == "__main__":
    main()
