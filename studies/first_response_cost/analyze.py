#!/usr/bin/env python3
"""Recompute first-submission batch accounting from the anonymous event ledger."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import statistics

TOKEN_KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def verify_binding(binding: dict, package: Path) -> None:
    for key in ("packet", "answers", "execution"):
        if key in binding:
            pin = binding[key]
            data = (package / pin["path"]).read_bytes()
            assert sha(data) == pin["sha256"] and len(data) == pin["bytes"], pin["path"]
    packet = json.loads((package / binding["packet"]["path"]).read_text())["items"]
    answers = jsonl(package / binding["answers"]["path"])
    assert len(answers) == binding["items"] == len(packet)
    assert len({r["id"] for r in answers}) == len(answers)
    assert {r["id"] for r in answers} == {r["id"] for r in packet}
    assert sha(json.dumps(sorted(r["id"] for r in packet)).encode()) == binding["item_ids_sha256"]
    if "execution" in binding:
        by_blind_id = {r["id"]: r for r in packet}
        answer_by_id = {r["id"]: r for r in answers}
        matching = []
        for row in jsonl(package / binding["execution"]["path"]):
            blind = f"{row['wg']}-q{sha(('packet:' + row['id']).encode())[:12]}"
            if blind not in by_blind_id:
                continue
            item = by_blind_id[blind]
            assert sha(item["question"].encode()) == row["questionSha256"]
            key = "sql" if "sql" in answer_by_id[blind] else "cypher"
            assert len(row["attempts"]) == 1 and row["attempts"][0][key] == answer_by_id[blind][key]
            matching.append(row)
        assert len(matching) == binding["items"]
        assert abs(sum(r["seconds"] for r in matching) - binding["execution_seconds"]) < 1e-7
    if "separate_repair" in binding:
        repair = binding["separate_repair"]
        data = (package / repair["artifact"]["path"]).read_bytes()
        assert sha(data) == repair["artifact"]["sha256"]
        rows = [json.loads(line) for line in data.splitlines()]
        assert len(rows) == repair["items"]
        assert len({r["id"] for r in rows}) == len(rows)
        assert {r["id"] for r in rows} <= {r["id"] for r in answers}


def summarize(sessions: list[dict], messages: list[dict], build_records: dict) -> dict:
    by_session = collections.defaultdict(list)
    seen = set()
    for message in messages:
        key = (message["session_key"], message["message_key"])
        assert key not in seen, "Duplicate message usage"
        seen.add(key)
        by_session[message["session_key"]].append(message)
    route_rows = collections.defaultdict(list)
    for session in sessions:
        events = by_session[session["session_key"]]
        assert events, session["session_key"]
        cutoff = session["first_submission_cutoff"]
        if cutoff:
            assert any(m["message_key"] == cutoff["completion_message_key"] for m in events)
            for message in events:
                assert not (message["first_line"] <= cutoff["line"] < message["last_line"])
                expected = "first_submission" if message["last_line"] <= cutoff["line"] else "after_first_submission"
                assert message["interval"] == expected
            assert session["first_submission_seconds"] <= session["full_session_seconds"]
        route_rows[session["route"]].append(session)
    output = {"measurement": "batch accounting through first caller-delivered completion; external first-query execution added separately",
        "input_tokens": "processed new input + cache creation + cache reads", "routes": {}}
    for route, all_rows in route_rows.items():
        completed = [s for s in all_rows if s["cutoff_status"] == "identified"]
        k = sum(s["binding"]["items"] for s in completed)
        result = {"observed_sessions": len(all_rows), "completed_sessions": len(completed), "completed_items": k,
            "unresolved_sessions": len(all_rows) - len(completed)}
        for interval in ("first_submission", "full_session", "after_first_submission"):
            selected = [m for s in completed for m in by_session[s["session_key"]]
                        if interval == "full_session" or m["interval"] == interval]
            tokens = {key: sum((m["usage"] or {}).get(key, 0) for m in selected)
                      for key in (*TOKEN_KEYS, "output_tokens")}
            processed = sum(tokens[key] for key in TOKEN_KEYS)
            elapsed = [(s["first_submission_seconds"] if interval == "first_submission" else
                        s["full_session_seconds"] if interval == "full_session" else
                        s["full_session_seconds"] - s["first_submission_seconds"]) for s in completed]
            execution = sum(s["binding"]["execution_seconds"] for s in completed) if interval != "after_first_submission" else 0
            rates = [(t + (s["binding"]["execution_seconds"] if interval != "after_first_submission" else 0))/s["binding"]["items"]
                     for s, t in zip(completed, elapsed)]
            result[interval] = {"usage": tokens, "processed_input_tokens": processed,
                "processed_input_tokens_per_item": processed/k, "output_tokens_per_item": tokens["output_tokens"]/k,
                "tool_calls": sum(m["tool_count"] for m in selected), "session_elapsed_seconds": sum(elapsed),
                "external_initial_query_execution_seconds": execution,
                "batch_allocated_seconds_median": statistics.median(rates),
                "batch_allocated_seconds_mean": (sum(elapsed) + execution)/k,
                "batch_allocated_seconds_quartiles": statistics.quantiles(rates, n=4, method="inclusive")[::2],
                "batch_allocated_seconds_range": [min(rates), max(rates)]}
        result["repair_file_items"] = sum(s["binding"].get("separate_repair", {}).get("items", 0) for s in completed)
        output["routes"][route] = result
    raw = output["routes"]["raw_text"]["first_submission"]
    build_seconds = sum(r["wall_seconds"] for r in build_records["records"])
    output["build"] = {"wall_seconds": build_seconds, "scope": build_records["scope"],
        "records": sum(r["records"] for r in build_records["records"])}
    output["record_query_to_raw_input_ratio"] = {route: output["routes"][route]["first_submission"]["processed_input_tokens_per_item"]/raw["processed_input_tokens_per_item"]
        for route in ("text2sql", "text2cypher")}
    output["descriptive_build_time_equivalents"] = {}
    for route in ("text2sql", "text2cypher"):
        equivalents = {}
        for kind in ("median", "mean"):
            key = f"batch_allocated_seconds_{kind}"
            saved = raw[key] - output["routes"][route]["first_submission"][key]
            equivalents[kind] = {"seconds_difference": saved, "fractional_item_equivalent": build_seconds/saved,
                "whole_item_ceiling": math.ceil(build_seconds/saved)}
        output["descriptive_build_time_equivalents"][route] = equivalents
    output["comparison_scope"] = "record writers use whole-WG batches; search uses one-third-WG batches; elapsed/item describes retained batch throughput; build-time equivalents use these unequal batches"
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--evidence", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    for name, pin in json.loads((args.evidence / "evidence_manifest.json").read_text()).items():
        data = (args.evidence / name).read_bytes()
        assert sha(data) == pin["sha256"] and len(data) == pin["bytes"], name
    sessions, messages = jsonl(args.evidence / "sessions.jsonl"), jsonl(args.evidence / "message_usage.jsonl")
    for session in sessions:
        verify_binding(session["binding"], args.package)
    recovered = json.loads((args.evidence / "initial_artifact_recovery.json").read_text())["receipts"]
    repaired_sessions = {s["session_key"]: s for s in sessions if "separate_repair" in s["binding"]}
    assert {r["session_key"] for r in recovered} == set(repaired_sessions)
    for receipt in recovered:
        session = repaired_sessions[receipt["session_key"]]
        original = session["binding"]["answers"]
        assert receipt["transcript_sha256"] == session["transcript_sha256"]
        assert all(line <= session["first_submission_cutoff"]["line"] for line in receipt["recipe"].values())
        assert receipt["retained_original_bytes_equal"]
        assert receipt["recovered_original_sha256"] == original["source_sha256"]
        assert receipt["recovered_items"] == repaired_sessions[receipt["session_key"]]["binding"]["items"]
    summary = summarize(sessions, messages, json.loads((args.evidence / "build_records.json").read_text()))
    text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text)
    print(json.dumps({"completed_sessions": sum(r["completed_sessions"] for r in summary["routes"].values()),
        "unresolved_sessions": sum(r["unresolved_sessions"] for r in summary["routes"].values()),
        "record_query_to_raw_input_ratio": summary["record_query_to_raw_input_ratio"],
        "output": str(args.out) if args.out else None}))


if __name__ == "__main__":
    main()
