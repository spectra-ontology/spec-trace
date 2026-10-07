#!/usr/bin/env python3
"""Four additional reverse-tail workers; fixed scientific call code unchanged."""
from __future__ import annotations

import argparse
import concurrent.futures
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time

CODE_SHA = "31ec881c17dd4d13aae349f76d0e7395a67bc14eece12a8af1d76ef3c0942d70"
PROTOCOL_SHA = "6c888208774bd32dbe2734ca04283cfe0bcc077d10e293aad8952a1fdd098d3e"
INPUT_SHA = "0d7a50f3eb3c1c441d3000b1c4e9fb553ffd0e8214f902b0c234ddc15f27c080"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def load_audit(base):
    code = base / "semantic_alignment_audit_v1.py"
    if sha(code) != CODE_SHA or sha(base / "semantic_alignment_audit_protocol_v1.json") != PROTOCOL_SHA:
        raise ValueError("scientific code/protocol changed")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("unchanged_semantic_call_for_resource_tail", code)
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    return audit


def operational_counts(out):
    calls = out / "calls"
    counts = {"reservations": 0, "closed_receipts": 0, "original_operational_VALID": 0,
              "original_operational_INVALID": 0}
    for reservation in calls.glob("*/reservation.json"):
        counts["reservations"] += 1
        receipt = reservation.parent / "receipt.json"
        if receipt.is_file():
            # Only operational error presence is used; no judgment is accessed.
            value = read(receipt)
            counts["closed_receipts"] += 1
            counts["original_operational_VALID" if value.get("error") is None else
                   "original_operational_INVALID"] += 1
    return counts


def require_owned_paths(args):
    project = args.base.parents[6]
    expected = project / "logs/publication/paper/under-review/kdd-2027-datasets-benchmarks/baseline-runs/_semantic_alignment_audit_v1/native_signature_v1"
    if (Path(args.out).resolve() != expected.resolve() or
            Path(args.resource_directory).resolve() != (expected.parent / "resource_tail_v1").resolve()):
        raise ValueError("dispatcher is restricted to the original owned audit and single resource directory")


def prepare(args, audit):
    require_owned_paths(args)
    out, destination = Path(args.out).resolve(), Path(args.resource_directory).resolve()
    if sha(out / "frozen_input_manifest.json") != INPUT_SHA:
        raise ValueError("fixed scientific input changed")
    protocol, manifest = audit.verify_preparation(out, args.base / "semantic_alignment_audit_protocol_v1.json")
    jobs = [{"number": n, "batch_id": batch["id"], "rater": rater,
             "call_id": rater + "_" + batch["id"]}
            for n, (batch, rater) in enumerate((b, r) for b in manifest["batches"] for r in ("A", "B"))]
    unreserved = [job for job in reversed(jobs) if not (out / "calls" / job["call_id"] / "reservation.json").exists()]
    value = {"version": 1, "prepared_unix": time.time(), "state": "prepared_only_not_launched",
             "dispatcher_sha256": sha(__file__), "resource_protocol_sha256": sha(args.resource_protocol),
             "scientific_code_sha256": CODE_SHA, "scientific_protocol_sha256": PROTOCOL_SHA,
             "audit_manifest_sha256": INPUT_SHA, "planned_global_attempts": 112,
             "snapshot_operational_counts": operational_counts(out), "extra_workers": 4,
             "combined_max_workers": 8, "jobs": unreserved, "selection": "reverse original fixed112 order, unreserved only",
             "scientific_labels_accessed": False, "scores_accessed": False,
             "new_question_query_schema_or_prompt": False, "wrapper_retries": 0,
             "expanded_185_predictions": "root reports zero; not read or used here"}
    write_new(destination / "frozen_dispatch_jobs_v2.json", value)
    return {"prepared": str(destination / "frozen_dispatch_jobs_v2.json"),
            "sha256": sha(destination / "frozen_dispatch_jobs_v2.json"),
            "unreserved_at_snapshot": len(unreserved), "operational_counts": value["snapshot_operational_counts"]}


def dispatch_once(audit, out, protocol, batch, rater, number):
    reservation = out / "calls" / (rater + "_" + batch["id"]) / "reservation.json"
    if reservation.exists():
        return {"call": reservation.parent.name, "state": "existing_reservation_preserved", "new_CLI": False}
    try:
        return audit.run_call(out, protocol, batch, rater, number)
    except FileExistsError as exc:
        # Only the atomic reservation race, before any CLI launch, is a skip.
        # A later receipt/file collision must propagate as an operational error.
        if exc.filename and Path(exc.filename).resolve() == reservation.resolve() and reservation.is_file():
            return {"call": reservation.parent.name, "state": "reservation_race_before_CLI_preserved", "new_CLI": False}
        raise


def owned_groups(out, fixed_calls, proc_root=Path("/proc")):
    targets = {str(out / "calls" / name / "stdout.jsonl") for name in fixed_calls}
    groups = set()
    for process in proc_root.iterdir():
        if not process.name.isdecimal():
            continue
        try:
            if os.readlink(process / "fd" / "1") not in targets:
                continue
            stat = (process / "stat").read_text()
            groups.add(int(stat[stat.rfind(")") + 2:].split()[2]))
        except (FileNotFoundError, ProcessLookupError, PermissionError, OSError):
            continue
    return groups


def mem_available_bytes():
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024
    return None


def run(args, audit):
    require_owned_paths(args)
    out, resource = Path(args.out).resolve(), Path(args.resource_directory).resolve()
    plan_path = resource / "frozen_dispatch_jobs_v2.json"
    plan, authorization = read(plan_path), read(args.authorization)
    if (authorization.get("authorization") != "root_reviewed_fixed_resource_tail_dispatcher" or
            authorization.get("dispatcher_sha256") != sha(__file__) or
            authorization.get("resource_protocol_sha256") != sha(args.resource_protocol) or
            authorization.get("dispatch_manifest_sha256") != sha(plan_path) or
            authorization.get("scientific_code_sha256") != CODE_SHA or
            authorization.get("scientific_protocol_sha256") != PROTOCOL_SHA or
            authorization.get("audit_manifest_sha256") != INPUT_SHA or
            authorization.get("combined_max_workers") != 8):
        raise ValueError("resource authorization absent or does not match exact fixed inputs")
    if (plan["dispatcher_sha256"] != sha(__file__) or plan["resource_protocol_sha256"] != sha(args.resource_protocol) or
            sha(out / "frozen_input_manifest.json") != INPUT_SHA):
        raise ValueError("resource/scientific input pin changed")
    protocol, manifest = audit.verify_preparation(out, args.base / "semantic_alignment_audit_protocol_v1.json")
    batches = {batch["id"]: batch for batch in manifest["batches"]}
    fixed = {r + "_" + b["id"] for b in manifest["batches"] for r in ("A", "B")}
    canonical = {r + "_" + b["id"]: n for n, (b, r) in
                 enumerate((b, r) for b in manifest["batches"] for r in ("A", "B"))}
    if (len(fixed) != 112 or len({job["call_id"] for job in plan["jobs"]}) != len(plan["jobs"]) or
            any(job["call_id"] not in fixed or job["number"] != canonical[job["call_id"]] or
                job["call_id"] != job["rater"] + "_" + job["batch_id"] for job in plan["jobs"])):
        raise ValueError("dispatcher introduces or changes fixed jobs")
    stop, admission_pause = threading.Event(), threading.Event()
    observations = {"max_observed_owned_groups": 0, "peak_sampled_combined_owned_RSS_bytes": 0,
                    "minimum_observed_MemAvailable_bytes": None, "RSS_guard": "two separate 8GiB sampled soft guard budgets (sum16GiB); no shared global or hard cap; transient overshoot possible"}

    def monitor():
        with (resource / "combined_resource_monitor.jsonl").open("x") as handle:
            while not stop.is_set():
                groups = owned_groups(out, fixed)
                rss = sum(audit.group_rss(groups).values())
                available = mem_available_bytes()
                if len(groups) > 8 or (available is not None and available < 8 * 1024**3):
                    admission_pause.set()
                else:
                    admission_pause.clear()
                row = {"unix": time.time(), "owned_groups": len(groups), "combined_owned_RSS_bytes": rss,
                       "MemAvailable_bytes": available, "extra_future_admission_paused": admission_pause.is_set()}
                handle.write(json.dumps(row) + "\n"); handle.flush()
                observations["max_observed_owned_groups"] = max(observations["max_observed_owned_groups"], len(groups))
                observations["peak_sampled_combined_owned_RSS_bytes"] = max(observations["peak_sampled_combined_owned_RSS_bytes"], rss)
                if available is not None:
                    observations["minimum_observed_MemAvailable_bytes"] = min(
                        available, observations["minimum_observed_MemAvailable_bytes"] or available)
                stop.wait(2)

    def job(job):
        while admission_pause.is_set():
            if (out / "calls" / job["call_id"] / "reservation.json").is_file():
                return {"call": job["call_id"], "state": "existing_reservation_preserved", "new_CLI": False}
            time.sleep(1)
        return dispatch_once(audit, out, protocol, batches[job["batch_id"]], job["rater"], job["number"])

    with (resource / ".dispatcher.lock").open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        write_new(resource / "resource_run_started.json", {"started_unix": time.time(), "dispatcher_sha256": sha(__file__),
            "authorization_sha256": sha(args.authorization), "dispatch_manifest_sha256": sha(plan_path),
            "operational_counts_at_start": operational_counts(out), "extra_workers": 4, "combined_max_workers": 8})
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                futures = [pool.submit(job, value) for value in plan["jobs"]]
                results = [future.result() for future in futures]
        finally:
            stop.set(); thread.join()
        result = {"completed_unix": time.time(), "results": results, "observations": observations,
                  "operational_counts_at_dispatcher_finish": operational_counts(out),
                  "all112_closure_must_be_verified_separately": True, "retries": 0,
                  "scientific_labels_accessed": False, "original_runner_or_attempts_killed": False}
        write_new(resource / "resource_dispatcher_completed.json", result)
    return result


def self_test(audit):
    passed = []
    with tempfile.TemporaryDirectory(prefix="synthetic_tail_reservation_") as temporary:
        out = Path(temporary)
        batch = {"id": "SYNTHETIC"}
        reservation = out / "calls" / "A_SYNTHETIC" / "reservation.json"
        reservation.parent.mkdir(parents=True)
        write_new(reservation, {"synthetic_only": True})
        called = []
        original = audit.run_call
        audit.run_call = lambda *values: called.append(values)
        assert dispatch_once(audit, out, {}, batch, "A", 0)["new_CLI"] is False and not called
        passed.append("existing_reservation_never_enters_scientific_call")
        reservation.unlink()
        def race(*values):
            write_new(reservation, {"synthetic_only": True})
            raise FileExistsError(17, "synthetic atomic reservation race", str(reservation))
        audit.run_call = race
        assert dispatch_once(audit, out, {}, batch, "A", 0)["state"] == "reservation_race_before_CLI_preserved"
        passed.append("only_pre_CLI_atomic_reservation_collision_is_skip_no_retry")
        audit.run_call = original
    return {"status": "PASS", "tests": passed, "actual_CLI_calls": 0, "actual_receipts_or_labels_read": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "run", "self-test"])
    parser.add_argument("--out")
    parser.add_argument("--resource-directory")
    parser.add_argument("--authorization")
    parser.add_argument("--resource-protocol")
    args = parser.parse_args()
    args.base = Path(__file__).resolve().parent
    audit = load_audit(args.base)
    if args.command == "self-test":
        result = self_test(audit)
    elif args.command == "prepare":
        result = prepare(args, audit)
    else:
        result = run(args, audit)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
