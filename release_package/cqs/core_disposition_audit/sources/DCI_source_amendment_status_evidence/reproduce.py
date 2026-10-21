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

INVENTORY_SHA256 = '7338933747c9c9a395d75b8827ae97e47252c0ef20c3cc86539aa83f9a1bbf16'
EXPECTED_IDS = ['RAN1_P2_CQ5-4']
EXPECTED_CASES = [{'id': 'RAN1_P2_CQ5-4', 'status': 'SEALED_LOCAL', 'decision': 'unsupported_frozen_data', 'subtype': 'source_explicit_agreement_amendment_status_unretained', 'question_sha256': 'ed8d176731df8121965dd70174728f1a2c5c647f96c0b1462489b10a079bb45c', 'query_sha256': '84330a55da07466ebee7188296ddba0c45234feebf0503570d67418aff7a2a34', 'criteria_sha256': 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'ROOT_seal_sha256': 'dcafbebf009561d6d8f610a1af370a00ea0dd9de2dc49ed7952d876a1c03e1a2', 'primary': {'path': 'cases/RAN1_P2_CQ5-4/contract/primary_review.json', 'bytes': 22127, 'sha256': '16743a3c1a3f926f73ba9965bab3f23e628ef772836c08b8f215cdf0e5562725'}, 'secondary': {'path': 'cases/RAN1_P2_CQ5-4/contract/secondary_review.json', 'bytes': 8903, 'sha256': '9d55ccfd9832331c26626eea832418b0477fa5c1e338e385c1e9786855dde082'}, 'verifier': 'cases/RAN1_P2_CQ5-4/verify.py', 'expert_validation_n': 0, 'new_admissions': 0}]
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
        "classification": 'unsupported_frozen_data',
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
        require(case["status"] == "SEALED_LOCAL" and case["decision"] == 'unsupported_frozen_data', "Unsealed case")
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
        require(child['status']=='PASS_BOUNDED_DIAGNOSTIC_REPLAY_NOT_FINAL_CLASSIFICATION' and child['id']==case['id'], 'DCI diagnostic identity')
        require(child['actual_raw_source_blocks_reopened']==232 and child['actual_native_rows']==10 and child['native_full_columns']==3 and child['latest_tied_candidates']==31, 'DCI source/native/tie scope')
        require(child['independent_semantic_reviews']==2 and child['eligible_LPWUS_status_witnesses']==2 and child['canonical_fidelity_diagnostic_pairs']==2, 'DCI classification witnesses')
        require(child['model_calls']==child['new_native_calls']==child['original560_pass_increment']==0 and child['all_legal_ten_fail_claimed'] is False and child['actual_native_contains_LPWUS_pair'] is False and child['explicit_SQL_replay'] is False, 'DCI bounded diagnostic declarations')
        results.append({"id": case["id"], "classification": case["decision"], "subtype": case["subtype"], "child_result": child})
    print(json.dumps({"status": "PASS", "cases": results, "new_admissions": 0,
                      "expert_validation_n": 0, "model_API_calls": 0, "new_native_calls": 0,
                      "scope": "Included source and frozen-projection replay plus pinned historical whole-database receipts; no fresh full database or model execution."}, ensure_ascii=False))


if __name__ == "__main__":
    main()
