#!/usr/bin/env python3
"""Replay the frozen PUSCH case without host files, network, or a model call.

This verifies a captured case and its diagnostic controls. It does not decide
question meaning or turn a local check into an independent review/native run.
"""
from __future__ import annotations

import argparse
import collections
import copy
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
if sys.flags.optimize:
    raise SystemExit('Verification requires enabled checks; -O/-OO refused.')
HERE = Path(os.path.abspath(__file__)).parent
INVENTORY_SHA256 = 'ec19f9afd5f185768ed31967b836073b205760883fc8d0bcd3063b303041be83'
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
      "m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}
W = "{" + NS["w"] + "}"
TEXT_TAGS = {W + "t", "{" + NS["m"] + "}t"}
FIELDS = ["m.meetingNumber", "a.resolutionId", "a.content"]
RANK = "__source_order_meetingNumberInt"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_pairs(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, "duplicate JSON object key")
        out[key] = value
    return out


def parse_json(raw):
    return json.loads(raw, object_pairs_hook=unique_pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def read_json(name):
    path = safe(HERE / name)
    raw = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
    return parse_json(raw)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe(path):
    path = Path(os.path.abspath(path))
    for ancestor in (path, *path.parents):
        require(not ancestor.is_symlink(), 'symlink forbidden: ' + str(ancestor))
    if path.exists():
        mode = path.lstat().st_mode
        require(stat.S_ISREG(mode) or stat.S_ISDIR(mode), 'nonregular entry forbidden: ' + str(path))
    return path


def local_module(name):
    # Explicit members support -I -S and prevent ambient/PYTHONPATH fallbacks.
    path = safe(HERE / (name + '.py'))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def no_host_audit():
    counts = {'network_calls': 0, 'subprocess_calls': 0, 'SQL_calls': 0,
              'host_private_open_attempts': 0, 'write_open_attempts': 0,
              'packet_read_opens': 0, 'stdlib_read_opens': 0}
    stdlib = Path(os.__file__).resolve().parent
    def hook(event, args):
        if event.startswith(('socket.', 'http.client.', 'urllib.')):
            counts['network_calls'] += 1
            raise RuntimeError('No-host replay forbids network: ' + event)
        if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.posix_spawnp', 'os.fork', 'os.exec', 'os.spawn'}:
            counts['subprocess_calls'] += 1
            raise RuntimeError('No-host replay forbids subprocess: ' + event)
        if event.startswith('sqlite3.'):
            counts['SQL_calls'] += 1
            raise RuntimeError('No-host replay forbids SQL: ' + event)
        if event == 'open':
            path, mode, flags = args
            if isinstance(path, int):
                counts['host_private_open_attempts'] += 1
                raise RuntimeError('No-host replay forbids descriptor file opens')
            if (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC)):
                counts['write_open_attempts'] += 1
                raise RuntimeError('No-host replay forbids file writes')
            target = Path(os.path.abspath(os.fsdecode(path)))
            if target.is_relative_to(HERE):
                safe(target)
                counts['packet_read_opens'] += 1
            elif target.is_relative_to(stdlib):
                counts['stdlib_read_opens'] += 1
            else:
                counts['host_private_open_attempts'] += 1
                raise RuntimeError('No-host replay forbids host-private open: ' + str(target))
    sys.addaudithook(hook)
    return counts


def token(row, fields=FIELDS):
    require(type(row) is dict and set(row) == set(fields), "unexpected native/requested columns")
    require(all(type(row[k]) is str for k in FIELDS), "requested fields must all be strings")
    if RANK in fields:
        require(type(row[RANK]) is int, "source numeric rank must be an integer")
    return tuple((k, type(row[k]).__name__, row[k]) for k in fields)


def combined(element):
    return "".join(e.text or "" for e in element.iter() if e.tag in TEXT_TAGS)


def norm(value):
    return re.sub(r"\s+", "", value).casefold()


def project(row, candidates):
    cw = row.get("contentWithEquations")
    body = cw if isinstance(cw, str) and cw.strip() else row["content"]
    for candidate in candidates:
        if candidate["node_id"] == row["node_id"]:
            body = body.replace(candidate["pair"]["surface"], candidate["new_candidate"])
    note = row.get("note")
    if isinstance(note, str) and note.strip():
        body += "\nNote: " + note
    return {"m.meetingNumber": row["meetingNumber"],
            "a.resolutionId": row["resolutionId"], "a.content": body}


def native_rows(path, fields):
    path = Path(path)
    raw = gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes()
    try:
        data = parse_json(raw)
    except json.JSONDecodeError:
        data = [parse_json(line) for line in raw.splitlines() if line.strip()]
    if isinstance(data, dict):
        require(set(data) >= {"rows"}, "native JSON object must contain rows")
        if "columns" in data:
            require(data["columns"] == fields, "native column order differs")
        data = data["rows"]
    require(type(data) is list, "native rows must be a JSON list or JSONL records")
    out = []
    for row in data:
        if type(row) is list:
            require(len(row) == len(fields), "native positional row width differs")
            row = dict(zip(fields, row))
        token(row, fields)
        out.append(row)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-full-rows")
    parser.add_argument("--native-rank-rows")
    parser.add_argument("--native-limited-rows")
    args = parser.parse_args()
    safe(HERE / 'verify.py')
    audit = no_host_audit()
    inventory_raw = safe(HERE / 'immutable_inventory.json').read_bytes()
    require(sha(inventory_raw) == INVENTORY_SHA256, 'fixed payload inventory changed')
    inventory = parse_json(inventory_raw)['files']
    manifest = read_json("manifest.json")
    require(manifest["id"] == "RAN1_P2_CQ5-5", "wrong case")
    require(manifest['files'] == inventory and manifest['immutable_inventory_sha256'] == INVENTORY_SHA256, 'manifest inventory declaration differs')
    actual = set()
    for path in HERE.rglob('*'):
        safe(path)
        mode = path.lstat().st_mode
        require(stat.S_ISREG(mode) or stat.S_ISDIR(mode), 'nonregular entry forbidden: ' + str(path))
        if stat.S_ISREG(mode):
            actual.add(path.relative_to(HERE).as_posix())
    require(actual == set(inventory) | {'manifest.json', 'immutable_inventory.json', 'verify.py'}, 'missing or extra payload file')
    for name, pin in inventory.items():
        relative = Path(name)
        require(type(name) is str and name and '\\' not in name and not relative.is_absolute() and '..' not in relative.parts, 'unsafe payload path')
        path = safe(HERE / relative)
        raw = path.read_bytes()
        require(len(raw) == pin["bytes"] and sha(raw) == pin["sha256"], "pin mismatch: " + name)
    require(sha((HERE / 'verify.py').read_bytes()) == manifest['verifier_sha256'], 'verifier differs')
    declarations = read_json('packet_declarations.json')
    require(set(manifest) == set(declarations) | {'files', 'immutable_inventory_sha256', 'verifier_sha256'}, 'unexpected manifest declaration')
    require(all(manifest.get(k) == v for k, v in declarations.items()), 'scientific declaration differs')
    local_module('scorer')
    rule = local_module('frozen_rule')
    original_scorer = local_module('original_scorer')
    contract_checks = local_module('contract_checks')

    receipt = read_json("data/source_capture.json")
    question = receipt["original_question"]
    require(sha(question["question_en"].encode()) == receipt["question_sha256"], "question bytes")
    require(sha(question["cypher"].encode()) == receipt["query_sha256"], "original query bytes")
    require(sha((HERE / "data/criteria.json").read_bytes()) == manifest["criteria_sha256"], "criteria bytes")
    require(sha((HERE / "queries/candidate.cypher").read_bytes()) == manifest["candidate_query_sha256"], "candidate bytes")
    require(receipt["SQLite_before"] == receipt["SQLite_after"], "source immutable capture pin changed")
    report_path = HERE / "source/Final_Report_RAN1-123.docx"
    require(sha(report_path.read_bytes()) == receipt["source"]["sha256"], "raw DOCX bytes")
    with zipfile.ZipFile(report_path) as archive:
        document = archive.read("word/document.xml")
        require(sha(document) == receipt["document_xml"]["sha256"], "raw document XML")
        require(archive.getinfo("word/document.xml").CRC == receipt["document_xml"]["CRC"], "XML CRC")
        require(sha(archive.read("word/styles.xml")) == receipt["styles_xml"]["sha256"], "raw styles XML")
    blocks = list(ET.fromstring(document).find("w:body", NS))
    source_rows = read_json("data/source16.json.gz")
    source_by_id = {r["resolutionId"]: r for r in source_rows}
    require(len(source_by_id) == len(source_rows) == 16, "source16 cardinality/identity")
    source_blocks_checked = 0
    for row in source_rows:
        start, stop = row["raw_own_range_half_open"]
        captured = row["actual_own_source_blocks"]
        require([b["raw_child0"] for b in captured] == list(range(start, stop)), "own source span gap")
        for captured_block in captured + row["following_foreign_source_blocks"]:
            raw_block = blocks[captured_block["raw_child0"]]
            require(combined(raw_block) == captured_block["literal_w_m_t"], "captured literal differs from DOCX")
            source_blocks_checked += 1
    matrix = read_json("data/minimum_role_matrix.json")
    require(set(matrix["all16_tie_pool"]) == set(source_by_id), "matrix source population")
    fragments_checked = 0
    for item in matrix["matrix"]:
        row = source_by_id[item["resolutionId"]]
        props = row["all_frozen_fields"]["properties"]
        source_text = "\n".join(combined(blocks[b["raw_child0"]]) for b in row["actual_own_source_blocks"])
        for check in item["evidence_fragment_checks"]:
            retained = props.get("content" if check["frozen_field"] == "body" else "note") or ""
            fragment = norm(check["role_fragment"])
            require(fragment in norm(retained) and fragment in norm(source_text), "operative role binding: " + item["resolutionId"])
            fragments_checked += 1
    require(fragments_checked == 83, "unexpected minimum-role check count")

    inputs = read_json("data/frozen_inputs.json.gz")
    agreements, sections = inputs["agreements"], inputs["sections"]
    require(len(agreements) == 21058, "incomplete generic frozen Agreement input")
    inference = rule.infer(agreements, sections)
    require(len(inference["all_header_matches"]) == 7, "header population differs")
    require(len(inference["direct_candidates"]) == 6 and len(inference["propagated_candidates"]) == 1, "frozen inference differs")
    dependency_controls = rule.controls(agreements, sections, inference)
    require(len(dependency_controls) == 7 and all(c["passed"] for c in dependency_controls), "dependency negative controls")
    candidates = inference["direct_candidates"] + inference["propagated_candidates"]
    saved_inference = read_json("data/inference_result.json")
    for key in ("direct_candidates", "propagated_candidates"):
        require(inference[key] == saved_inference[key], "captured generic candidate differs")
    pool = read_json("data/full_SQL_pool.json.gz")
    require(len(pool) == 532 and len({r["resolutionId"] for r in pool}) == 520, "full pool multiplicity differs")
    by_node = {a["node_id"]: a for a in agreements}
    require(all(r["content"] == by_node[r["node_id"]]["content"] and "PUSCH" in r["content"] and "repetition" in r["content"] for r in pool), "literal frozen pool predicate")
    require([r["meetingNumberInt"] for r in pool] == sorted((r["meetingNumberInt"] for r in pool), reverse=True), "full numeric meeting order")
    projected = [project(row, candidates) for row in pool]
    expected = read_json("data/projected_full532.json.gz")
    require(list(map(token, projected)) == list(map(token, expected)), "full532 typed value projection")
    top_indices = [i for i, r in enumerate(pool) if r["meetingNumberInt"] == pool[0]["meetingNumberInt"]]
    gold = [projected[i] for i in top_indices]
    require(len(gold) == 16 and {r["a.resolutionId"] for r in gold} == set(source_by_id), "complete boundary16 differs")
    rank_rows = [dict(projected[i], **{RANK: pool[i]["meetingNumberInt"]}) for i in top_indices]
    full_rank_expected = [dict(p, **{RANK: r["meetingNumberInt"]}) for p, r in zip(projected, pool)]
    original_native = [parse_json(line) for line in (HERE / "data/original_native_rows.jsonl").read_bytes().splitlines() if line.strip()]
    require(len(original_native) == 10 and all(type(r) is list and len(r) == 3 for r in original_native), "archived native row shape")
    original_ids = [r[1] for r in original_native]
    require(original_ids == matrix["original_native10"], "archived native10 original order")
    original_pool = collections.Counter((r["meetingNumber"], r["resolutionId"], r["content"]) for r in pool)
    require(not (collections.Counter(map(tuple, original_native)) - original_pool), "archived original native outside original SQL pool")
    by_id = collections.defaultdict(list)
    for row in pool:
        by_id[row["resolutionId"]].append(row)
    require(all(len(by_id[ident]) == 1 for ident in original_ids), "original native identity ambiguous")
    fixed = [project(by_id[ident][0], candidates) for ident in original_ids]
    require(fixed == read_json("data/projected_original_native10.json"), "archived10 generic projection changed")

    # The frozen inference is generated before raw-format evaluation of its member.
    candidate = inference["propagated_candidates"][0]
    own = source_by_id[candidate["resolutionId"]]
    old_runs, new_runs = [], []
    for item in own["actual_own_source_blocks"]:
        for run in blocks[item["raw_child0"]].iter(W + "r"):
            text = "".join(e.text or "" for e in run.iter(W + "t"))
            strike = run.find("w:rPr/w:strike", NS)
            is_struck = strike is not None and strike.get(W + "val", "true") not in ("false", "0", "off")
            if candidate["old_candidate"] in text:
                old_runs.append(is_struck)
            if candidate["new_candidate"] in text:
                new_runs.append(is_struck)
    require(any(old_runs) and new_runs and not any(new_runs), "source old/active name attribution")
    target = next(p for p in projected if p["a.resolutionId"] == candidate["resolutionId"])
    require(candidate["old_candidate"] not in target["a.content"] and candidate["new_candidate"] in target["a.content"], "projected active member")
    # Preserve actual formula loss rather than fabricating an equation answer.
    quantity = next(p for p in projected if p["a.resolutionId"] == "AGR-123-8.3-002")
    equations = list(blocks[753].iter("{" + NS["m"] + "}oMath"))
    require(len(equations) == 6 and all(combined(e) == "N∙K" for e in equations), "source baseline math witness changed")
    require("N∙K" not in quantity["a.content"], "unrecovered baseline math was invented")
    hopping = next(r for r in pool if r["resolutionId"] == "AGR-123-10.4.1-010")
    exception = "intra-slot frequency hopping is not supported unless the repetition time is 1"
    require(exception in project(hopping, candidates)["a.content"], "hopping exception absent")
    without_note = dict(hopping, note=None)
    require(exception not in project(without_note, candidates)["a.content"], "note ablation failed to detect answer-bearing condition")
    contract = read_json("data/scoring_contract.json")
    groups = original_scorer.make_order_groups(contract, rank_rows, gold)
    scoring_controls = contract_checks.checks(contract, gold, groups)
    scoring_controls += [
        {"check": "archived_native10_projection_legal", "pass": original_scorer.score(contract, gold, fixed, diagnostic=True, order_groups=groups)["exact"]},
        {"check": "legal_boundary10_can_exclude_math_witness", "pass": original_scorer.score(contract, gold, [p for p in gold if p["a.resolutionId"] != "AGR-123-8.3-002"][:10], diagnostic=True, order_groups=groups)["exact"]},
        {"check": "lost_baseline_quantity_not_invented", "pass": "N∙K" not in quantity["a.content"]},
    ]
    require(len(scoring_controls) == 18 and all(c["pass"] for c in scoring_controls), "scoring negative controls")
    native_flags = [args.native_full_rows, args.native_rank_rows, args.native_limited_rows]
    require(not any(native_flags) or all(native_flags), "provide all three native captures together")
    native_receipt_checks = {"present": False}
    if (HERE / 'native_capture_index.json').is_file():
        index = read_json('native_capture_index.json')
        execution = read_json(index['execution_receipt'])
        require(execution['inventory_unchanged'] is True and execution['source_before'] == execution['source_after'], 'native inventory capture changed')
        require(execution['source_before']['nodes'] == 165418 and execution['source_before']['relationships'] == 848228, 'native graph inventory differs')
        guard = read_json(index['guard_receipt'])
        require(guard['status'] == 'PASS' and guard['child_exit'] == 0 and guard['quality_rerolls'] == 0, 'native wrapper guard')
        require(guard['owned_cleanup']['owned_stopped'] is True and guard['owned_cleanup']['common_lock_held'] is True, 'owned native cleanup')
        require(guard['prestart_available_minimum_bytes'] == 26*1024**3 and guard['continuous_reserve_minimum_bytes'] == 16*1024**3, 'native guard threshold definition')
        require(min(guard['initial_memory']['Linux_available_bytes'], guard['initial_memory']['Windows_available_bytes']) >= guard['prestart_available_minimum_bytes'], 'native initial reserve below threshold')
        require(all(min(s['Linux_available_bytes'], s['Windows_available_bytes']) >= guard['continuous_reserve_minimum_bytes'] for s in guard['memory_samples']), 'native continuous reserve sample below threshold')
        binding = read_json(index['ROOT_binding'])
        require(binding['candidate_query_sha256'] == manifest['candidate_query_sha256'], 'ROOT binding candidate differs')
        require(binding['all_three_field_types_values_and_relationship_multiplicities_equal'] and binding['full_plus_rank_typed_equal'] and binding['read_plan_execution_and_rollback_all_three'], 'ROOT native binding incomplete')
        require(binding['SQLite_before'] == binding['SQLite_after'] == receipt['SQLite_before'], 'ROOT SQL capture pin differs')
        require(binding['source_document']['sha256'] == sha(report_path.read_bytes()), 'ROOT source pin differs')
        require(len(binding['all16_original_source_checks']) == 16 and sum(x['operative_fragment_checks'] for x in binding['all16_original_source_checks']) == 83 and all(x['source_and_executed_output_match'] for x in binding['all16_original_source_checks']), 'ROOT all16 own source binding incomplete')
        primary = read_json('data/primary_exact_seven_unit_review.json')
        secondary = read_json('native/ROOT_secondary_source_definition.json')
        supplement = read_json('data/primary_native_completion_supplement.json')
        require(primary['reviewer'] != secondary['reviewer'] and primary['reviewer_kind'] == 'nonblind_AI_primary' and secondary['reviewer_kind'] == 'distinct_nonblind_AI_secondary', 'two distinct nonblind AI reviews absent')
        require(primary['criteria_sha256'] == secondary['criteria_sha256'] == supplement['criteria_sha256'] == manifest['criteria_sha256'], 'review criteria differ')
        require(primary['candidate_query_sha256'] == secondary['candidate_query_sha256'] == supplement['candidate_query_sha256'] == manifest['candidate_query_sha256'], 'review definitions differ')
        require(len(primary['seven_unit_review']) == len(secondary['seven_unit_review']) == len(supplement['seven_unit_review']) == 7, 'seven-unit review incomplete')
        require([x['unit'] for x in primary['seven_unit_review']] == [x['unit'] for x in secondary['seven_unit_review']] == [x['unit'] for x in supplement['seven_unit_review']], 'review units differ')
        require(primary['human_expert_n'] == secondary['human_expert_n'] == supplement['human_expert_n'] == 0, 'human review count fabricated')
        native_by_kind = {}
        for kind, item in index['queries'].items():
            native_receipt = read_json(item['receipt'])
            raw_rows = gzip.decompress((HERE / item['rows']).read_bytes()) if item['rows'].endswith('.gz') else (HERE / item['rows']).read_bytes()
            query_bytes = (HERE / item['query']).read_bytes()
            query_sha = sha(query_bytes)
            require(native_receipt['id'] == manifest['id'] and native_receipt['wg'] == 'RAN1' and native_receipt['status'] == 'OK', 'native receipt identity/status')
            require(native_receipt['query_sha256'] == query_sha == sha(native_receipt['query'].encode()), 'actual native query bytes differ')
            require(native_receipt['columns'] == item['columns'], 'native requested column names/order differ')
            require(native_receipt['plan_query_type'] == native_receipt['execution_query_type'] == 'r', 'native execution is not read-only classified')
            require(native_receipt['rollback_completed'] is True and native_receipt['execution_summary_complete'] is True and native_receipt['truncated'] is False and native_receipt['full_rows_available'] is True, 'native capture incomplete/rollback absent')
            require(sha(raw_rows) == native_receipt['rows_sha256'] and len(raw_rows) == native_receipt['bytes_retained'], 'native retained row bytes differ')
            actual_rows = native_rows(HERE / item['rows'], item['columns'])
            require(len(actual_rows) == native_receipt['rows_retained'] == item['row_count'], 'native retained row cardinality')
            require(any(i['status'] == 'OK' and i['query_sha256'] == query_sha and i['rows'] == len(actual_rows) for i in execution['items']), 'native execution ledger missing query')
            native_by_kind[kind] = str(HERE / item['rows'])
            if kind == 'limited':
                require([r['a.resolutionId'] for r in actual_rows] == binding['actual_limited10_ids'] == supplement['observed_fresh_native10'], 'observed fresh native10 replaced/reordered')
        require(set(native_by_kind) == {'full', 'rank', 'limited'}, 'native capture has missing/extra query roles')
        require(execution['model_calls'] == 0, 'native capture unexpectedly contains model calls')
        native_receipt_checks = {'present': True, 'all_query_bytes_and_row_pins_match': True, 'read_only_plan_execution_and_rollback': True, 'native_inventory_unchanged': True, 'guard26_16GiB_and_owned_cleanup_pass': True, 'quality_rerolls': 0, 'ROOT_binding_532_and83_matches': True, 'distinct_nonblind_AI_review_records': 2, 'observed_fresh_native10_preserved': True}
        if not any(native_flags):
            args.native_full_rows, args.native_rank_rows, args.native_limited_rows = [native_by_kind[k] for k in ('full', 'rank', 'limited')]
            native_flags = [args.native_full_rows, args.native_rank_rows, args.native_limited_rows]
    native_checks = {"provided": False, "execution_claim": "No native execution is performed or inferred by this verifier."}
    if all(native_flags):
        full = native_rows(args.native_full_rows, FIELDS)
        ranked = native_rows(args.native_rank_rows, FIELDS + [RANK])
        limited = native_rows(args.native_limited_rows, FIELDS)
        require(collections.Counter(map(token, full)) == collections.Counter(map(token, projected)), "native full532 typed multiset differs")
        require(collections.Counter(token(r, FIELDS + [RANK]) for r in ranked) == collections.Counter(token(r, FIELDS + [RANK]) for r in full_rank_expected), "native full532 requested fields plus rank differ")
        require([r[RANK] for r in ranked] == sorted((r[RANK] for r in ranked), reverse=True), "native full rank order differs")
        require(original_scorer.score(contract, gold, limited, diagnostic=True, order_groups=groups)["exact"], "actual limited10 is not a legal full-record boundary answer")
        native_checks = {"provided": True, "full_rows": len(full), "rank_rows": len(ranked), "limited_rows": len(limited),
                         "limited_IDs_actual_order": [r["a.resolutionId"] for r in limited],
                         "typed_full_multiset_and_rank_equal": True, "limited10_boundary_valid": True,
                         "execution_claim": "Supplied rows match; native execution, read-only plan, rollback and inventory require the independently pinned ROOT receipts."}
    result = {"id": manifest["id"], "status": "PASS_PORTABLE_CAPTURE_AND_CONTROLS_NOT_FINAL_ADJUDICATION",
              "packet_hash_pins_checked": len(manifest["files"]), "actual_source_blocks_checked": source_blocks_checked,
              "own_source_records": 16, "operative_fragment_bindings": fragments_checked, "frozen_Agreement_inputs": len(agreements),
              "full_SQL_rows": len(pool), "full_SQL_distinct_IDs": len(by_id), "boundary_rows": len(gold),
              "generic_inference_dependency_controls": dependency_controls, "complete_record_scorer_controls": scoring_controls,
              "answer_bearing_note_ablation_pass": True, "source_active_parameter_attribution_pass": True,
              "baseline_formula_loss_preserved_without_invention": True, "native_row_checks": native_checks,
              "pinned_native_receipt_checks": native_receipt_checks,
              "default_no_host_audit": audit,
              "API_calls": 0, "native_calls_performed_here": 0, "human_expert_n": 0,
              "scope": "Capture consistency and negative controls; semantic adjudication remains the separately recorded primary and ROOT seven-unit reviews."}
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    print(json.dumps({k: v for k, v in result.items() if k not in {"generic_inference_dependency_controls", "complete_record_scorer_controls"}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
