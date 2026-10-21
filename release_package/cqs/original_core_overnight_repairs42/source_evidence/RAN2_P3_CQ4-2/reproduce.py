"""Replay the completed direct-outcome trace package using the standard library."""
import sys
if sys.flags.optimize:
    raise SystemExit("Optimization unsupported")
sys.dont_write_bytecode = True
import collections, hashlib, importlib.util, json, pathlib, re

F = pathlib.Path(__file__).absolute().parent
ID = "RAN2_P3_CQ4-2"
REPAIR = "e932ae9fdc67fc5ce77fbd321a52a0d55e6933721618262aebf6fd446c66aad0"
INVENTORY_SHA = "68ea12ebaf01a40a871dd3edd51baf4f824ecf447343c8ffe81e0b67fb1ee800"
CRITERIA_SHA = "bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4"
COLS = ["r.resolutionId", "cr.tdocNumber"]

def canonical(v):
    return json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()

def digest(b):
    return hashlib.sha256(b).hexdigest()

def safe(path):
    path = pathlib.Path(path).absolute()
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError("symlink entry or ancestor rejected")
    return path

def read(path):
    return json.loads(safe(path).read_bytes())

def mod(name, path):
    spec = importlib.util.spec_from_file_location(name, safe(path))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

def checked_tree():
    safe(F)
    files = {}
    for path in F.rglob("*"):
        if path.is_symlink():
            raise ValueError("tree symlink rejected")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError("nonregular entry rejected")
        files[path.relative_to(F).as_posix()] = path
    for path in F.rglob("*"):
        if path.is_dir() and not any(p.is_relative_to(path) for p in files.values()):
            raise ValueError("empty extra directory rejected")
    inventory_bytes = safe(F / "inventory.json").read_bytes()
    assert digest(inventory_bytes) == INVENTORY_SHA
    inventory = json.loads(inventory_bytes)
    assert set(files) == set(inventory) | {"inventory.json", "manifest.json", "README.md", "reproduce.py"}
    for relative, pin in inventory.items():
        parts = pathlib.PurePosixPath(relative)
        assert not parts.is_absolute() and ".." not in parts.parts
        raw = files[relative].read_bytes()
        assert pin == {"bytes": len(raw), "sha256": digest(raw)}
    manifest = read(F / "manifest.json")
    expected_meta = {
        "id": ID, "artifact_type": "local_direct_CR_outcome_trace_evidence",
        "repair_sha256": REPAIR, "scientific_inventory_sha256": INVENTORY_SHA,
        "local_validation_status": "completed_local_gates", "new_admissions": 0, "API_calls": 0
    }
    assert set(manifest) == set(expected_meta) | {"files"}
    assert canonical({k: v for k, v in manifest.items() if k != "files"}) == canonical(expected_meta)
    assert set(manifest["files"]) == set(files) - {"manifest.json"}
    for relative, pin in manifest["files"].items():
        raw = files[relative].read_bytes()
        assert pin == {"bytes": len(raw), "sha256": digest(raw)}
    return inventory

def main():
    checked_tree()
    definition = read(F / "definition.json")
    assert len(definition) == 9 and digest(canonical(definition)) == REPAIR
    assert digest((F / "criteria.json").read_bytes()) == CRITERIA_SHA
    criteria = read(F / "criteria.json")
    schema = mod("cq4_2_portable_review_schema", F / "review_schema.py")
    reviews = [read(F / "primary_exact_seven_unit_review.json"), read(F / "independent_secondary_exact_seven_unit_review.json")]
    for review in reviews:
        schema.check_pass(review, definition["question_en"], criteria["semantic_units"],
                          criteria_sha=CRITERIA_SHA, identity_key="repair_sha256", identity_sha=REPAIR)
    assert reviews[0]["reviewer"] != reviews[1]["reviewer"]
    authority = read(F / "exact_original_authority_spans.json")
    for index, item in enumerate(authority["sources"]):
        raw = (F / ("authority/original_design_" + str(index) + ".md")).read_bytes()
        assert digest(raw) == item["source"]["sha256"] and len(raw) == item["source"]["bytes"]
        lines = raw.decode().splitlines()
        for span in item["spans"]:
            assert "\n".join(lines[span["lo"] - 1:span["hi"]]) == span["text"]
    source_module = mod("cq4_2_prepared_source_replay", F / "verify_prepared_source_payload_v2.py")
    source = source_module.main()
    assert source["status"] == "PASS_PREPARED_SOURCE_ONLY" and source["repair_sha256"] == REPAIR
    assert (source["original_paths"], source["source_prefix_paths"], source["source_prefix_Resolution_n"]) == (857, 45, 19)
    assert source["selected_rows"] == 10 and source["requested_Resolution_identity_n"] == 8
    # The source-only function deliberately retains its historical pending labels.
    # Completed review/native gates are checked separately below.
    root_source = read(F / "source/ROOT_independent_source_proof.json")
    assert str(root_source["status"]).startswith("PASS")

    case = read(F / "execution/native_case.json")
    rows_raw = (F / "execution/native_rows.jsonl").read_bytes()
    rows = [json.loads(line) for line in rows_raw.splitlines()]
    query_sha = digest(definition["reference_query"].encode())
    assert case["id"] == ID and case["status"] == "OK" and case["query"] == definition["reference_query"]
    assert case["query_sha256"] == query_sha and case["columns"] == COLS
    assert case["rows_sha256"] == digest(rows_raw) and case["bytes_retained"] == len(rows_raw)
    assert case["rows_retained"] == len(rows) == 10 and case["truncated"] is False
    assert all(type(row) is list and len(row) == 2 and all(type(v) is str for v in row) for row in rows)
    assert case["plan_query_type"] == case["execution_query_type"] == "r"
    assert all(case[k] is True for k in ("rollback_completed", "execution_summary_complete", "full_rows_available"))
    selected = read(F / "expected_SQL_selected10_full_two_columns.json")
    expected = [(r[COLS[0]], r[COLS[1]]) for r in selected]
    assert collections.Counter(map(tuple, rows)) == collections.Counter(expected)
    assert [r[0] for r in rows] == sorted((r[0] for r in rows), reverse=True)
    full = read(F / "expected_SQL_all160_full_two_columns.json")
    assert len(full) == 160 and len({r[COLS[0]] for r in full}) == 92
    assert full[9][COLS[0]] > full[10][COLS[0]]

    execution = read(F / "execution/native_execution.json")
    protocol = read(F / "execution/native_protocol.json")
    outer = read(F / "execution/outer_guard.json")
    assert execution["source_before"] == execution["source_after"] and execution["inventory_unchanged"] is True
    assert execution["input_sha256"] == digest((F / "native_input_development_probe.jsonl").read_bytes())
    assert execution["source_before"]["nodes"] == 156288 and execution["source_before"]["relationships"] == 939037
    assert len(execution["items"]) == 1 and execution["items"][0]["status"] == "OK"
    assert execution["items"][0]["query_sha256"] == query_sha and execution["items"][0]["rows"] == 10
    assert protocol["container_memory_bytes"] == 2 * 1024**3 and protocol["container_cpu_cores"] == 1
    assert protocol["query_timeout_seconds"] == 20
    assert outer["status"] == "PASS" and outer["child_started"] is True
    assert type(outer["child_exit"]) is int and outer["child_exit"] == 0
    assert outer["prestart_available_minimum_bytes"] == 26 * 1024**3
    assert outer["continuous_reserve_minimum_bytes"] == 16 * 1024**3
    assert outer["owned_cleanup"]["owned_stopped"] is True and outer["owned_cleanup"]["common_lock_held"] is True
    assert set(outer["initial_memory"]) == {"Linux_available_bytes", "Windows_available_bytes"}
    assert all(type(v) is int and v >= 26 * 1024**3 for v in outer["initial_memory"].values())
    observations = [json.loads(line) for line in (F / "execution/fresh_memory_observations.jsonl").read_bytes().splitlines()]
    assert observations and len({r["session"] for r in observations}) == 1
    assert len({r["nonce"] for r in observations}) == len(observations)
    for row in observations:
        assert row["status"] == "FRESH_NUMERIC_OBSERVATION"
        assert type(row["windows_available_bytes"]) is int and row["windows_available_bytes"] >= 16 * 1024**3
        assert type(row["Get_CimInstance_calls_for_this_request"]) is int and row["Get_CimInstance_calls_for_this_request"] == 1
        assert type(row["cached_values_used"]) is int and row["cached_values_used"] == 0
    binding = read(F / "execution/actual_native_SQL_binding.json")
    assert binding["status"] == "PASS" and binding["repair_sha256"] == REPAIR
    assert binding["DB_before"] == binding["DB_after"]
    assert binding["native_full_two_columns_typed_multiset_equal_fresh_SQL"] is True
    assert binding["native_ID_DESC_order"] is True and binding["full_SQL160_typed_multiset_equal_saved_projection"] is True
    assert binding["native_rows_n"] == 10 and binding["full_SQL_paths_n"] == 160
    for key, relative in {
        "native_case": "execution/native_case.json", "native_rows": "execution/native_rows.jsonl",
        "native_execution": "execution/native_execution.json", "native_protocol": "execution/native_protocol.json",
        "outer_guard": "execution/outer_guard.json", "fresh_memory_observations": "execution/fresh_memory_observations.jsonl",
        "secondary": "independent_secondary_exact_seven_unit_review.json",
        "source_proof": "source/ROOT_independent_source_proof.json"
    }.items():
        raw = (F / relative).read_bytes()
        assert binding[key]["sha256"] == digest(raw) and binding[key]["bytes"] == len(raw)

    requested = [{"resolutionId": row[0]} for row in rows]
    assert len({r["resolutionId"] for r in requested}) == 8
    sys.path.insert(0, str(F / "unchanged_scoring"))
    scorer = mod("cq4_2_portable_original_scorer", F / "unchanged_scoring/original_scorer.py")
    controls = read(F / "actual_strict_requested_identity_controls.json")
    assert controls["tests_n"] == len(controls["tests"]) == 18 and controls["repair_sha256"] == REPAIR
    for test in controls["tests"]:
        actual = scorer.score(definition, requested, test["prediction"], diagnostic=True)
        assert actual == test["actual"] and actual["exact"] is test["expected_exact"]
    predicate = read(F / "actual_direct_source_event_predicate_controls.json")
    components = read(F / "actual_generic_predicate_translation_receipt.json")["regex_components"]
    assert predicate["tests_n"] == len(predicate["tests"]) == 14 and predicate["repair_sha256"] == REPAIR
    for test in predicate["tests"]:
        tdoc, body = test["tdocNumber"], test["body"]
        actual = bool(re.fullmatch(components["header_prefix"] + tdoc + components["header_suffix"], body)
                      or re.fullmatch(components["named_prefix"] + tdoc + components["named_suffix"], body))
        assert actual is test["actual"] and actual is test["expected"]
    return {
        "status": "PASS", "id": ID, "repair_sha256": REPAIR, "new_admissions": 0, "API_calls": 0,
        "original_recorded_paths": 2351, "target_spec_paths": 857, "qualified_paths": 160,
        "original_source_prefix_paths": 45, "original_source_Resolution_groups": 19,
        "saved_native_rows": 10, "native_columns": COLS, "requested_Resolution_identity_n": 8,
        "independent_semantic_reviews": 2, "requested_field_scorer_controls": 18,
        "direct_event_predicate_controls": 14, "fresh_nonce_memory_observations": len(observations),
        "source_scope": "Included original XML/styles, register cells and native Word lexical records reproduce the complete finite cutoff frontier; saved owned native execution and fresh immutable SQL bind the repaired trace.",
        "native_CFB_format_scope": source["source_native_CFB_scope"]
    }

if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False))

