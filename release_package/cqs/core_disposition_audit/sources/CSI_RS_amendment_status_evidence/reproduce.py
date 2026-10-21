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

INVENTORY_SHA256 = '81b5f9a4d745026e5b7eb8f0c08e20b517a8d3ce66a9a72abf9a797887de52cc'
EXPECTED_IDS = ['RAN1_P2_CQ5-1']
EXPECTED_CASES = [{'id': 'RAN1_P2_CQ5-1', 'status': 'SEALED_LOCAL', 'decision': 'unsupported_frozen_data', 'subtype': 'source_explicit_agreement_amendment_status_unretained', 'question_sha256': '420fcb6befc294a67781e7a3d231fdb12191e7d171152675f0c7a1ca54ae1750', 'query_sha256': '3aaf20190a53f22c477f0ffe85957bc91486914951c5529cd871d64d14bdbd40', 'criteria_sha256': 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'ROOT_seal_sha256': '469f889ea594b766a2f0071f77caa99e03997a76e9fa70dac2447c1af5fbdebe', 'primary': {'path': 'cases/RAN1_P2_CQ5-1/contract/primary_review.json', 'bytes': 21337, 'sha256': '167a5c0ff4237d070c6091095bebf5d033a70465a5091e9c9be40518bcd17d34'}, 'secondary': {'path': 'cases/RAN1_P2_CQ5-1/contract/secondary_review.json', 'bytes': 15621, 'sha256': 'a2a06668ecf00f16b842edf7a43c37818ac027d28cb28cf5d73cf2722fe5dfbb'}, 'verifier': 'cases/RAN1_P2_CQ5-1/verify.py', 'expert_validation_n': 0, 'new_admissions': 0}]
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
        require(child['status']=='PASS_BOUNDED_TWO_REVIEW_SOURCE_REPLAY_NOT_PUBLIC_ADMISSION' and child['id']==case['id'], 'CSI-RS diagnostic identity')
        require(child['actual_archived_native_rows']==15 and child['native_full_columns']==3 and child['raw_frontier_records']==47 and child['raw_source_blocks_reopened']==1215, 'CSI-RS source/native scope')
        require(child['independent_semantic_reviews']==2 and child['original_cutoff_mandatory']==10 and child['original_cutoff_ties']==6 and child['original_boundary_choose']==5, 'CSI-RS original cutoff/reviews')
        require(child['generic_candidate_mandatory']==14 and child['generic_candidate_ties']==27 and child['source_active_minimum_retained'] is True and child['all_legal_fifteen_fail_claimed'] is False, 'CSI-RS positive counterevidence')
        require(child['original560_pass_increment']==child['model_calls']==child['new_native_calls']==child['human_expert_n']==0 and child['explicit_SQL_replay'] is False, 'CSI-RS classification authority')
        results.append({"id": case["id"], "classification": case["decision"], "subtype": case["subtype"], "child_result": child})
    print(json.dumps({"status": "PASS", "cases": results, "new_admissions": 0,
                      "expert_validation_n": 0, "model_API_calls": 0, "new_native_calls": 0,
                      "scope": "Included source and frozen-projection replay plus pinned historical whole-database receipts; no fresh full database or model execution."}, ensure_ascii=False))


if __name__ == "__main__":
    main()
