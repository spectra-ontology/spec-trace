"""Replay the sealed RAN4 approval-target classification from included source evidence."""
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

INVENTORY_SHA256 = 'b398e26d763a4f8959665dee2c013bb004dbe7280ce6eb8c4ed994dd6383a0bc'
EXPECTED_IDS = ['RAN4_P3_CQ4-2']
EXPECTED_CASES = [{'id': 'RAN4_P3_CQ4-2', 'status': 'SEALED_LOCAL', 'decision': 'unsupported_frozen_data', 'subtype': 'own_approval_object_binding_loss', 'question_sha256': 'c4bb53e46e8ebb35bc1596af0b23d4138f66bf1f3e3d67215165c712d0d1cbc9', 'query_sha256': 'ec1b35eaa2ff59fe6bcd340725cf2263088230790076b5e11e591111b5b756bf', 'criteria_sha256': 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'ROOT_seal_sha256': 'ca775055e558435471ac95a1605be6647954c4bbdad8ef232ffd1c6d1aab99ef', 'primary': {'path': 'cases/RAN4_P3_CQ4-2/contract/primary.json', 'bytes': 15959, 'sha256': 'a5e64ac55f4984023d9db7aaf0de69e98669ad83c500b5d5ca0afb6c1207ab65'}, 'secondary': {'path': 'cases/RAN4_P3_CQ4-2/contract/secondary.json', 'bytes': 14891, 'sha256': '67d3a8740d4b0a58e47e5a703c161e74fa47019da16c6f970a646c4791a6f36c'}, 'verifier': 'cases/RAN4_P3_CQ4-2/reproduce.py', 'expert_validation_n': 0, 'new_admissions': 0}]
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
    seal = json.loads(read("ROOT_final_seal.json"))
    case = bindings[0]
    require(pin("ROOT_final_seal.json")["sha256"] == case["ROOT_seal_sha256"], "ROOT seal fixed identity")
    require(seal["id"] == case["id"] and seal["status"] == "SEALED_LOCAL_CLASSIFICATION_PENDING_SCOPED_PUBLICATION", "ROOT sealed classification")
    require(seal["decision"] == case["decision"] and seal["subtype"] == case["subtype"] and seal["criteria_sha256"] == CRITERIA_SHA256, "Sealed meaning and criteria")
    require(exact(seal["original560_pass_increment"], 0) and seal["public_admission"] is False and seal["separate_API_evaluation_required"] is False, "Classification authority")
    for key, name in [("final_packet", "ROOT_final_packet.json"), ("ROOT_direct_source_SQL_reopening", "ROOT_direct_source_SQL_reopening.json"), ("ROOT_actual_replay", "ROOT_actual_portable_replay.json"), ("actual_adverse_controls", "actual_adverse_controls.json")]:
        require(exact(pin(name), {k: seal[key][k] for k in ("bytes", "sha256")}), "Actual sealed evidence: " + key)
    prefix = "cases/" + case["id"] + "/"
    require(exact(pin(prefix + "inventory.json"), {k: seal["portable_inventory"][k] for k in ("bytes", "sha256")}), "Unchanged portable inventory")
    require(exact(pin(prefix + "reproduce.py"), {k: seal["portable_verifier"][k] for k in ("bytes", "sha256")}), "Unchanged portable verifier")
    original = json.loads(read(prefix + "contract/original_row.jsonl"))
    require(original["id"] == case["id"], "Original row identity")
    require(hashlib.sha256(original["question_en"].encode()).hexdigest() == seal["question_sha256"] == case["question_sha256"], "Original English binding")
    require(hashlib.sha256(original["cypher"].encode()).hexdigest() == seal["original_query_sha256"] == case["query_sha256"], "Original query binding")
    require(exact(original["gold_primary_values"], ["216"]) and exact(original["gold_row_count"], 1), "Historical baseline preserved")
    criteria = json.loads(read(prefix + "authority/criteria.json"))
    require(pin(prefix + "authority/criteria.json")["sha256"] == CRITERIA_SHA256, "Fixed official criteria")
    primary = json.loads(read(case["primary"]["path"]))
    secondary = json.loads(read(case["secondary"]["path"]))
    require([unit["unit"] for unit in primary["meaning_units"]] == criteria["semantic_units"] == [unit["unit"] for unit in secondary["meaning_units"]], "Exact official seven meaning units")
    require(primary["reviewer"] != secondary["reviewer"] and primary["independent"] is False, "Separate primary and secondary review roles")
    require(primary["recommendation"] == secondary["decision"] == seal["decision"] and primary["subtype"] == secondary["subtype"] == seal["subtype"], "Review disposition")
    require(secondary["primary_review_seen"]["sha256"] == case["primary"]["sha256"], "Secondary exact primary binding")
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
        require(child.get("status") == "PASS" and len(child["cases"]) == 1, "Child status and case count")
        result = child["cases"][0]
        require(result["id"] == case["id"] and result["classification"] == case["decision"] and result["subtype"] == case["subtype"], "Child classification identity")
        require(result["classification_state"] == "two_AI_semantic_judgments_agree_awaiting_ROOT_final_seal", "Preserved pre-seal child state")
        require(exact(result["original_domain_Resolution_n"], 216) and exact(result["original_domain_path_n"], 1766) and exact(result["source91_original_paragraphs_replayed"], 31), "Actual replay scope")
        require(result["original_benchmark_value_preserved"] == "216" and result["adopted_count_gold"] is None, "Historical value versus answer gold")
        require(exact(result["count_level_positive_alternatives_preserved"], [21690, 21691, 23086]), "Count-level positive recovery alternatives")
        require(exact(child["new_admissions"], 0) and exact(child["native_calls"], 0) and exact(child["API_calls"], 0) and child["whole_CQ_final_adjudication_complete"] is False, "Portable evidence versus ROOT seal authority")
        results.append({"id": case["id"], "classification": case["decision"], "subtype": case["subtype"], "child_result": child})
    print(json.dumps({"status": "PASS", "cases": results, "new_admissions": 0,
                      "expert_validation_n": 0, "model_API_calls": 0, "new_native_calls": 0,
                      "scope": "Included source and frozen-projection replay plus pinned historical whole-database receipts; no fresh full database or model execution."}, ensure_ascii=False))


if __name__ == "__main__":
    main()
