#!/usr/bin/env python3
"""Extract anonymous first-submission cost evidence from retained local sessions.

The raw session transcripts are private inputs. Public outputs contain only event
times, hashed identifiers, usage, tool counts and pointers to released packets and
answers. Original session accounting and response files are read without edits.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

GROUPS = {
    "text2sql": ["text2sql_runA_runB", "text2sql_runs_C_to_E", "text2sql_runs_F_to_J"],
    "text2cypher": ["text2cypher_runA_runB", "text2cypher_runs_C_to_E", "text2cypher_runs_F_to_J"],
    "text_search": ["text_search", "text_search_runB", "text_search_runC"],
    "text_only": ["text_search_text_only", "text_search_text_only_runB", "text_search_text_only_runC"],
    "raw_text": ["raw_index_runA", "raw_index_runB"],
    "dense_tool": ["dense_tool_runA", "dense_tool_runB"],
    "dense_capped": ["dense_tool_capped_runA"],
}
TOKENS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stamp(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def read_jsonl(path: Path) -> list[dict]:
    with path.open() as stream:
        return [json.loads(line) for line in stream if line.strip()]


def public_pin(base: Path, package: Path, path: Path) -> dict:
    relative = str(path.resolve().relative_to(base.resolve()))
    public_path = "responses/" + relative
    public = package / public_path
    if not public.is_file():
        raise ValueError(f"Missing released input: {public_path}")
    return {"path": public_path, "sha256": digest(public.read_bytes()), "bytes": public.stat().st_size,
            "source_sha256": digest(path.read_bytes()), "source_bytes_equal_public": path.read_bytes() == public.read_bytes()}


def binding(base: Path, package: Path, route: str, condition: str, wg: str, entry: dict,
            admitted: dict[str, dict]) -> dict:
    if route in ("text2sql", "text2cypher"):
        run = entry["run"]
        packet_folder = "subagent_packets_sql" if route == "text2sql" else "subagent_packets"
        packet = base / "chain_eval" / packet_folder / f"{wg}_schema.json"
        answer = base / "chain_eval/subagent_queries" / f"{wg}_{route}_{run}.jsonl"
        execution = base / (f"chain_eval/text2sql/{wg}_text2sql_{run}.jsonl" if route == "text2sql"
                            else f"chain_eval/{wg}_text2cypher_claude_subagent_{run}.jsonl")
    else:
        prompt = (base / "chain_eval" / entry["prompt"]).read_text()
        candidates = sorted(set(re.findall(r"[\w./-]+/parts/[\w.-]+\.json", prompt)))
        if len(candidates) != 1:
            raise ValueError(f"Ambiguous packet mapping: {condition}/{wg}/{entry.get('part')}")
        old = candidates[0]
        # Resolve the recorded legacy track component to the current same track.
        prefix = "logs/publication/paper/ongoing/sigir-2027-research/"
        if prefix not in old:
            raise ValueError(f"Unrecognized original packet path: {old}")
        packet = base / old.split(prefix, 1)[1]
        part = entry["part"]
        if route == "text_search":
            suffix = "" if condition == "text_search" else "_" + condition.rsplit("_", 1)[1]
            folder = base / f"chain_eval/text_search_full{suffix}/solver_logs"
        elif condition == "text_search_text_only":
            folder = base / "chain_eval/text_only_full/solver_logs"
        else:
            kind = {"text_only": "text_only_agent", "raw_text": "raw_agent", "dense_tool": "dense_agent",
                    "dense_capped": "dense_capped_agent"}[route]
            run = "runA" if route == "dense_capped" else condition.rsplit("_", 1)[1]
            folder = base / f"final/supplement_cycle/{kind}/{run}/collected/session_outputs"
        answer = folder / f"{wg}_{part}_answers.jsonl"
        execution = None
    packet_items = json.loads(packet.read_text())["items"]
    answers = read_jsonl(answer)
    expected_ids = [r["id"] for r in packet_items]
    answer_ids = [r["id"] for r in answers]
    if len(set(answer_ids)) != len(answer_ids) or set(answer_ids) != set(expected_ids):
        raise ValueError(f"Packet/answer identity mismatch: {answer}")
    result = {"items": len(expected_ids), "item_ids_sha256": digest(json.dumps(sorted(expected_ids)).encode()),
              "packet": public_pin(base, package, packet), "answers": public_pin(base, package, answer),
              "answer_packet_id_sets_equal": True, "execution_seconds": 0.0}
    if execution:
        rows = read_jsonl(execution)
        # The original solver packet deliberately blinds canonical item IDs.
        # Reconstruct the exact run_chain_eval.packet_id mapping, then validate
        # both the question bytes and the execution's canonical question hash.
        blind = {f"{r['wg']}-q{digest(('packet:' + r['id']).encode())[:12]}": r
                 for r in admitted.values() if r["wg"] == wg}
        canonical = [blind[r["id"]] for r in packet_items]
        if any(p["question"] != c["question"] for p, c in zip(packet_items, canonical)):
            raise ValueError(f"Packet/admitted question mismatch: {packet}")
        question_hashes = {r["id"]: digest(r["question"].encode()) for r in canonical}
        rows = [r for r in rows if question_hashes.get(r["id"]) == r.get("questionSha256")]
        if len(rows) != len(expected_ids) or {r["id"] for r in rows} != set(question_hashes):
            raise ValueError(f"Execution/question binding mismatch: {execution}")
        query_key = "sql" if route == "text2sql" else "cypher"
        query_by_canonical_id = {blind[r["id"]]["id"]: r[query_key] for r in answers}
        if any(len(r.get("attempts", [])) != 1 or r["attempts"][0].get(query_key) != query_by_canonical_id[r["id"]]
               for r in rows):
            raise ValueError(f"Initial execution/query bytes differ: {execution}")
        result["first_execution_query_text_equals_retained_original"] = True
        result["canonical_item_ids_sha256"] = digest(json.dumps(sorted(question_hashes)).encode())
        repair = answer.with_name(answer.stem + "_repair1.jsonl")
        if repair.is_file():
            repair_rows = read_jsonl(repair)
            if len({r["id"] for r in repair_rows}) != len(repair_rows) or not {r["id"] for r in repair_rows} <= set(expected_ids):
                raise ValueError(f"Repair IDs differ from original packet: {repair}")
            result["separate_repair"] = {"artifact": public_pin(base, package, repair), "items": len(repair_rows),
                "queries_changed": sum(r[query_key] != next(q[query_key] for q in answers if q["id"] == r["id"])
                                       for r in repair_rows)}
        result["execution_seconds"] = sum(r["seconds"] for r in rows)
        result["execution"] = public_pin(base, package, execution)
    return result


def extract(path: Path, session_key: str) -> tuple[dict, list[dict]]:
    raw = path.read_bytes()
    lines = raw.splitlines()
    if any(not line.strip() for line in lines):
        raise ValueError(f"Blank transcript lines would make line receipts ambiguous: {path.name}")
    rows = [json.loads(line) for line in lines]
    messages, terminals = {}, []
    result_events = {}
    timestamps = [(i, row["timestamp"]) for i, row in enumerate(rows, 1) if row.get("timestamp")]
    for line, row in enumerate(rows, 1):
        message = row.get("message") or {}
        content = message.get("content") or []
        content = content if isinstance(content, list) else []
        if row.get("type") == "user":
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    result_events[block.get("tool_use_id")] = (line, row.get("timestamp"), block.get("is_error", False))
        if row.get("type") != "assistant" or not message.get("id"):
            continue
        message_id = message["id"]
        key = digest(message_id.encode())
        record = messages.setdefault(message_id, {"session_key": session_key, "message_key": key,
            "first_line": line, "last_line": line, "first_timestamp": row.get("timestamp"),
            "last_timestamp": row.get("timestamp"), "usage": None, "tools": {}})
        record["last_line"] = line
        record["last_timestamp"] = row.get("timestamp")
        if message.get("usage"):
            record["usage"] = {name: message["usage"].get(name) or 0 for name in TOKENS}
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                tool_id = block["id"]
                record["tools"][tool_id] = block.get("name")
                if block.get("name") == "SubagentHandback":
                    report = (block.get("input") or {}).get("message", "")
                    terminals.append({"line": line, "timestamp": row.get("timestamp"), "message_id": message_id,
                        "tool_id": tool_id, "kind": "SubagentHandback", "report": report})
            elif block.get("type") == "text" and message.get("stop_reason") == "end_turn":
                terminals.append({"line": line, "timestamp": row.get("timestamp"), "message_id": message_id,
                    "tool_id": None, "kind": "assistant_end_turn", "report": block.get("text", "")})
    terminals.sort(key=lambda r: r["line"])
    first = terminals[0] if terminals else None
    # A plain end_turn report in a handback-enforced harness has not yet reached
    # the caller. Include the immediately requested handback delivery, rather
    # than treating its usage as a repair or excluding required delivery cost.
    if first and first["kind"] == "assistant_end_turn":
        handback = next((r for r in terminals if r["kind"] == "SubagentHandback"), None)
        if handback:
            between = rows[first["line"]:handback["line"] - 1]
            texts = [str((r.get("message") or {}).get("content", "")) for r in between if r.get("type") == "user"]
            if any("[handback-send-enforce]" in t for t in texts) and not any("execution-error feedback" in t for t in texts):
                first = handback
    cutoff = None
    acknowledged = False
    unresolved_status = "unresolved_no_completion_event"
    if first:
        message = messages[first["message_id"]]
        cutoff = (message["last_line"], message["last_timestamp"])
        if first["tool_id"]:
            ack = result_events.get(first["tool_id"])
            if ack and ack[2]:
                raise ValueError(f"First handback failed: {path.name}:{ack[0]}")
            if ack and not ack[2]:
                cutoff = ack[:2]
                acknowledged = True
            elif not ack:
                # A tool invocation alone does not establish caller delivery.
                # Preserve the session as unresolved until its successful
                # acknowledgment is present in the retained transcript.
                cutoff = None
                unresolved_status = "unresolved_missing_handback_acknowledgment"
    events = []
    for message in messages.values():
        if cutoff and message["first_line"] <= cutoff[0] < message["last_line"]:
            raise ValueError(f"One streamed message crosses the selected cutoff: {path.name}")
        message["tool_count"] = len(message.pop("tools"))
        message["interval"] = ("first_submission" if message["last_line"] <= cutoff[0] else "after_first_submission") if cutoff else "uncut"
        events.append(message)
    final = timestamps[-1]
    row = {"session_key": session_key, "transcript_sha256": digest(raw), "transcript_bytes": len(raw),
        "transcript_lines": len(rows), "started": timestamps[0][1], "full_session_ended": final[1],
        "full_session_seconds": (stamp(final[1]) - stamp(timestamps[0][1])).total_seconds(),
        "cutoff_status": "identified" if cutoff else unresolved_status,
        "first_submission_seconds": (stamp(cutoff[1]) - stamp(timestamps[0][1])).total_seconds() if cutoff else None,
        "first_submission_cutoff": None if not cutoff else {"line": cutoff[0], "timestamp": cutoff[1],
            "completion_kind": first["kind"], "completion_message_key": digest(first["message_id"].encode()),
            "completion_call_line": first["line"], "completion_call_timestamp": first["timestamp"],
            "report_sha256": digest(first["report"].encode()), "report_bytes": len(first["report"].encode()),
            "tool_result_acknowledged": acknowledged},
        "completion_report_output_basenames": sorted(set(re.findall(r"[A-Za-z0-9_.-]+\.jsonl", first["report"]))) if first else [],
        "completion_events": len(terminals)}
    return row, sorted(events, key=lambda r: r["first_line"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source-base", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--transcript-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source_provenance = args.source_base / "chain_eval/subagent_model_provenance.json"
    provenance = json.loads(source_provenance.read_text())
    admitted = {row["id"]: row for gate in ("core", "ran5") for row in
                read_jsonl(args.source_base / f"integration/items_final/gate/{gate}/chain_items_admitted.jsonl")}
    sessions, messages = [], []
    for route, conditions in GROUPS.items():
        for condition in conditions:
            for wg, entries in provenance["conditions"][condition].items():
                for entry in entries:
                    key = digest(f"{condition}/{wg}/{entry.get('run')}/{entry.get('part')}/{entry['agentId']}".encode())
                    path = args.transcript_root / entry["session"] / "subagents" / f"agent-{entry['agentId']}.jsonl"
                    session, events = extract(path, key)
                    session.update({"route": route, "condition": condition, "wg": wg,
                                    "run": entry.get("run"), "part": entry.get("part"),
                                    "provenance_agent_key": digest(entry["agentId"].encode()),
                                    "binding": binding(args.source_base, args.package, route, condition, wg, entry, admitted)})
                    if route in ("text2sql", "text2cypher") and Path(session["binding"]["answers"]["path"]).name not in session["completion_report_output_basenames"]:
                        raise ValueError(f"Initial report does not identify the retained original: {condition}/{wg}")
                    sessions.append(session)
                    messages.extend(events)
    args.out.mkdir(parents=True, exist_ok=True)
    for name, records in [("sessions.jsonl", sessions), ("message_usage.jsonl", messages)]:
        (args.out / name).write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in records))
    receipt = {"source_provenance_sha256": digest(source_provenance.read_bytes()), "sessions": len(sessions),
        "messages": len(messages), "raw_transcript_text_published": False,
        "unresolved": [{k: r[k] for k in ("session_key", "route", "wg", "run", "part", "cutoff_status")}
                       for r in sessions if r["cutoff_status"] != "identified"],
        "collection_method": "first caller-delivered completion: explicit SubagentHandback (including enforced handback after end_turn) or assistant end_turn; complete streamed message usage counted once; successful handback acknowledgment included"}
    (args.out / "collection_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    build = []
    for wg in ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5"):
        folder = args.source_base / "final/next_cycle/build_cost"
        tm, cmp = folder / f"{wg}.time.txt", folder / f"{wg}.compare.json"
        text, comparison = tm.read_text(), json.loads(cmp.read_text())
        match = re.search(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): (?:(\d+):)?(\d+):(\d+\.\d+)", text)
        if not match or any(comparison[k] for k in ("onlyRebuilt", "onlyStored", "contentDiffers")) or comparison["rebuiltRecords"] != comparison["storedRecords"]:
            raise ValueError(f"Unverified build evidence: {wg}")
        build.append({"wg": wg, "wall_seconds": int(match[1] or 0) * 3600 + int(match[2]) * 60 + float(match[3]),
            "records": comparison["storedRecords"], "rebuilt_equals_stored": True,
            "time_file_sha256": digest(tm.read_bytes()), "comparison_file_sha256": digest(cmp.read_bytes())})
    (args.out / "build_records.json").write_text(json.dumps({"scope": "disposition build from prepared document text", "records": build}, indent=2) + "\n")
    manifest = {name: {"sha256": digest((args.out / name).read_bytes()), "bytes": (args.out / name).stat().st_size}
                for name in ("sessions.jsonl", "message_usage.jsonl", "collection_receipt.json", "build_records.json")}
    (args.out / "evidence_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
