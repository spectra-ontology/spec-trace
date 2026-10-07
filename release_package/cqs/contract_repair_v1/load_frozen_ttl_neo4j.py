#!/usr/bin/env python3
"""Restore a released TTL into an owned, isolated Neo4j instance.

This wrapper reuses the shipped release restoration code. It never connects
to an operational database, never deletes data, and refuses a nonempty target.
Each invocation loads one working group; invocations share a sequential lock.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import resource
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOADER = HERE.parents[1] / "pipeline" / "load_released_kg.py"
INVENTORY = {
    "RAN1": (163305588, 165418, 848228),
    "RAN2": (166688978, 156288, 939037),
    "RAN3": (81735967, 87980, 481498),
    "RAN4": (295732831, 342161, 1592845),
    "RAN5": (195847852, 215012, 1047242),
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    sha, md5 = hashlib.sha256(), hashlib.md5()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            sha.update(chunk)
            md5.update(chunk)
    return {"sha256": sha.hexdigest(), "md5": md5.hexdigest(),
            "bytes": path.stat().st_size}


def write_json(path, data):
    temporary = path.with_suffix(path.suffix + ".pending")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def docker(*args):
    result = subprocess.run(["docker", *args], check=True, capture_output=True,
                            text=True)
    return result.stdout.strip()


def inspection(name):
    return json.loads(docker("inspect", name))[0]


def guard_container(info, name, port, run_id, source_sha):
    labels = info["Config"].get("Labels") or {}
    required = {"spectra.frozen.owner": "contract_repair_v1",
                "spectra.frozen.run_uuid": run_id,
                "spectra.frozen.source_sha256": source_sha}
    if info["Name"] != "/" + name or any(labels.get(k) != v for k, v in required.items()):
        raise RuntimeError("target container ownership labels do not match")
    host = info["HostConfig"]
    if host.get("Memory") != 2 * 1024**3 or host.get("NanoCpus") != 10**9:
        raise RuntimeError("target resource limits do not match the fixed budget")
    bindings = host.get("PortBindings") or {}
    if bindings != {"7687/tcp": [{"HostIp": "127.0.0.1", "HostPort": str(port)}]}:
        raise RuntimeError("target must expose only the pinned loopback Bolt port")
    if not info["State"]["Running"]:
        raise RuntimeError("target container is not running")


def wait_empty_database(bolt):
    from neo4j import GraphDatabase
    drv = GraphDatabase.driver(bolt, auth=None, connection_timeout=5)
    last_error = None
    for _ in range(60):
        try:
            drv.verify_connectivity()
            with drv.session() as session:
                count = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            if count != 0:
                raise RuntimeError("target is nonempty; refusing to append or erase")
            drv.close()
            return
        except RuntimeError:
            drv.close()
            raise
        except Exception as exc:
            last_error = type(exc).__name__
            time.sleep(2)
    drv.close()
    raise RuntimeError("new database did not become ready: " + str(last_error))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--wg", required=True, choices=sorted(INVENTORY))
    ap.add_argument("--ttl", required=True, type=Path)
    ap.add_argument("--work-dir", type=Path, default=HERE / "_frozen_ttl_v1")
    ap.add_argument("--expected-md5", help="published deposit checksum; mismatch aborts")
    ap.add_argument("--batch-size", type=int, default=2000)
    args = ap.parse_args()
    if args.batch_size <= 0 or args.batch_size > 5000:
        raise ValueError("batch size must be between 1 and 5000")
    args.ttl = args.ttl.resolve(strict=True)
    if args.ttl.name != args.wg + "-body.ttl":
        raise ValueError("source filename must match the selected released working group")
    source = digest(args.ttl)
    expected_bytes, expected_nodes, expected_rels = INVENTORY[args.wg]
    if source["bytes"] != expected_bytes:
        raise ValueError("source size differs from the public released TTL inventory")
    if args.expected_md5 and source["md5"] != args.expected_md5.lower():
        raise ValueError("source MD5 differs from the published deposit checksum")
    source["path"] = str(args.ttl)
    source["published_md5_verified"] = bool(args.expected_md5)
    args.work_dir = args.work_dir.resolve()
    args.work_dir.mkdir(parents=True, exist_ok=True)
    with (args.work_dir / "sequential_import.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        work = args.work_dir / args.wg.lower()
        work.mkdir(exist_ok=True)
        manifest_path = work / "import_manifest.json"
        if manifest_path.exists():
            raise RuntimeError("a prior import manifest exists; no overwrite or replay onto it")
        name = "kdd-db-frozen-v1-" + args.wg.lower()
        port = 57686 + int(args.wg[-1])
        if port not in range(57687, 57692):
            raise RuntimeError("port guard failed")
        existing = set(docker("ps", "-a", "--format", "{{.Names}}").splitlines())
        if name in existing:
            raise RuntimeError("target container already exists; refusing to adopt or modify it")
        run_id = str(uuid.uuid4())
        image_info = json.loads(docker("image", "inspect", "neo4j:5.26.0"))[0]
        manifest = {
            "version": 1, "working_group": args.wg, "status": "starting",
            "created_utc": utc(), "run_uuid": run_id, "source": source,
            "shipped_loader": {"path": str(LOADER), **digest(LOADER)},
            "wrapper": {"path": str(Path(__file__).resolve()), **digest(Path(__file__))},
            "image": {"tag": "neo4j:5.26.0", "id": image_info["Id"]},
            "target": {"container": name, "bolt": f"bolt://127.0.0.1:{port}",
                       "loopback_only": True, "cpu": 1, "memory_bytes": 2 * 1024**3,
                       "heap_mib": 512, "pagecache_mib": 256},
            "parser_address_space_limit_bytes": 8 * 1024**3,
            "batch_size": args.batch_size,
            "published_inventory": {"nodes": expected_nodes, "relationships": expected_rels},
            "meaning": "source restoration measurement, not expert or semantic validation",
        }
        write_json(manifest_path, manifest)
        started = time.monotonic()
        try:
            data_dir = work / "data"
            data_dir.mkdir()
            docker("run", "--detach", "--pull=never", "--name", name,
                   "--cpus=1", "--memory=2g", "--memory-swap=2g",
                   "--publish", f"127.0.0.1:{port}:7687",
                   "--label", "spectra.frozen.owner=contract_repair_v1",
                   "--label", f"spectra.frozen.run_uuid={run_id}",
                   "--label", f"spectra.frozen.source_sha256={source['sha256']}",
                   "--env", "NEO4J_AUTH=none",
                   "--env", "NEO4J_server_memory_heap_initial__size=512m",
                   "--env", "NEO4J_server_memory_heap_max__size=512m",
                   "--env", "NEO4J_server_memory_pagecache_size=256m",
                   "--volume", f"{data_dir}:/data", "neo4j:5.26.0")
            guard_container(inspection(name), name, port, run_id, source["sha256"])
            bolt = manifest["target"]["bolt"]
            wait_empty_database(bolt)
            manifest["status"] = "parsing"
            write_json(manifest_path, manifest)
            resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))
            spec = importlib.util.spec_from_file_location("shipped_released_kg_loader", LOADER)
            loader = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(loader)
            parse_started = time.monotonic()
            nodes, rels, stats = loader.parse_ttl(args.ttl)
            manifest["parse_elapsed_seconds"] = time.monotonic() - parse_started
            manifest["parse_inventory"] = {
                "nodes": len(nodes), "relationships": len(rels),
                "statements": stats["statements"],
                "skipped_non_instance_subjects": stats["skipped_subjects"],
                "class_subjects": dict(stats["class_subjects"]),
                "relationship_predicates": dict(stats["rel_pred_camel"]),
                "property_conflicts_capped_count": len(stats["prop_conflicts"]),
                "property_conflicts_sample": stats["prop_conflicts"][:20],
            }
            if len(nodes) != expected_nodes or len(rels) != expected_rels or stats["prop_conflicts"]:
                raise RuntimeError("parsed graph differs from released inventory or has property conflicts")
            # Recheck ownership immediately before the only database-write call.
            guard_container(inspection(name), name, port, run_id, source["sha256"])
            wait_empty_database(bolt)
            manifest["status"] = "loading"
            write_json(manifest_path, manifest)
            load_started = time.monotonic()
            counts = loader.load_neo4j(bolt, "neo4j", "", nodes, rels, args.batch_size)
            manifest["load_elapsed_seconds"] = time.monotonic() - load_started
            manifest["measured_counts"] = counts
            expected_types = {loader.decode_rel_type(k): v for k, v in stats["rel_pred_camel"].items()}
            mismatch = {
                "nodes": counts["total_nodes"] != len(nodes),
                "labels": {k: {"ttl": v, "neo4j": counts["label_counts"].get(k, 0)}
                           for k, v in stats["class_subjects"].items()
                           if counts["label_counts"].get(k, 0) != v},
                "relationships": {k: {"ttl": v, "neo4j": counts["rel_counts"].get(k, 0)}
                                  for k, v in expected_types.items()
                                  if counts["rel_counts"].get(k, 0) != v},
            }
            manifest["inventory_mismatch"] = mismatch
            if mismatch["nodes"] or mismatch["labels"] or mismatch["relationships"]:
                raise RuntimeError("loaded graph differs from TTL inventory")
            manifest["status"] = "restored_inventory_match"
            print(json.dumps({"wg": args.wg, "status": manifest["status"],
                              "nodes": counts["total_nodes"],
                              "relationships": sum(counts["rel_counts"].values()),
                              "manifest": str(manifest_path)}, ensure_ascii=False), flush=True)
        except BaseException as exc:
            manifest["status"] = "failed_preserved_for_diagnosis"
            manifest["error_type"] = type(exc).__name__
            # No environment or credential values are recorded.
            manifest["error"] = str(exc)[:1000]
            raise
        finally:
            manifest["elapsed_seconds"] = time.monotonic() - started
            manifest["max_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            manifest["updated_utc"] = utc()
            write_json(manifest_path, manifest)


if __name__ == "__main__":
    main()
