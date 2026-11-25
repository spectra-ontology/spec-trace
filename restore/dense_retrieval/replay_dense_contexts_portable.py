#!/usr/bin/env python3
"""Replay archived dense contexts, or explicitly measure fresh local ANN queries.

Every input path is supplied on the command line. The replay mode uses only the
Python standard library, original request-building code and read-only SQLite.
It writes hashes/IDs/metadata only; source passages and answer rows stay local.
"""
from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import struct
import sys
import time
import urllib.parse

META_KEYS = ("tdocNumber", "meeting", "meetingId", "crPackId", "tsgMeeting",
             "specNumber", "crNumber", "clausesAffected", "resolutionId")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            result.update(block)
    return result.hexdigest()


def canonical_hash(value) -> str:
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True).encode())


def rows(path: Path):
    with path.open() as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def save(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("portable_original_dense_request", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("replay", "fresh-query"))
    parser.add_argument("--request-module", required=True, type=Path)
    parser.add_argument("--items", required=True, action="append", type=Path)
    parser.add_argument("--gate", required=True, action="append", type=Path)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--response-dir", type=Path)
    source.add_argument("--context-manifest", type=Path)
    parser.add_argument("--candidate-manifest", type=Path)
    parser.add_argument("--index", action="append", default=[], metavar="WG=SQLITE")
    parser.add_argument("--wg", action="append", choices=[f"RAN{i}" for i in range(1, 6)])
    parser.add_argument("--context-tokens", type=int, default=16384)
    parser.add_argument("--expected-count", type=int, default=1334)
    parser.add_argument("--expected-items", type=int, default=667)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--common-dir", type=Path)
    parser.add_argument("--local-model-module", type=Path)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--qdrant-url")
    parser.add_argument("--torch-threads", type=int, default=2)
    parser.add_argument("--fresh-items", choices=("first-per-wg", "all"), default="first-per-wg")
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        parser.error("--out must name a new or empty output directory")
    if args.torch_threads < 1:
        parser.error("--torch-threads must be positive")
    args.out.mkdir(parents=True, exist_ok=True)
    selected_wgs = set(args.wg or [f"RAN{i}" for i in range(1, 6)])
    module = load_module(args.request_module)
    if not callable(getattr(module, "text_request", None)) or not callable(getattr(module, "request_sha", None)):
        parser.error("request module must provide original text_request and request_sha")
    rejected = {row["id"] for path in args.gate for row in json.loads(path.read_text())["rejectedItems"]}
    items = {}
    for path in args.items:
        for item in rows(path):
            if item["wg"] in selected_wgs and item["id"] not in rejected:
                if item["id"] in items and items[item["id"]] != item:
                    raise ValueError("Conflicting item ID: " + item["id"])
                items[item["id"]] = item
    paths = sorted(args.response_dir.glob("RAN[1-5]_dense_*.jsonl")) if args.response_dir else [args.context_manifest]
    responses = {}
    for path in paths:
        for row in rows(path):
            if row["id"] in items:
                responses[row["id"], row["model"]] = row
    input_hashes = [{"role": role, "name": path.name, "sha256": file_hash(path)} for role, group in (("request_module", [args.request_module]), ("items", args.items), ("gate", args.gate), ("responses", paths)) for path in group]
    summary = {"mode": args.mode, "inputs": input_hashes, "admitted_items": len(items), "responses": len(responses),
               "context_tokens": args.context_tokens, "source_passages_written": False, "answer_model_called": False}
    failures = []
    if len(items) != args.expected_items or len(responses) != args.expected_count:
        failures.append({"kind": "coverage", "expected_items": args.expected_items, "actual_items": len(items), "expected_responses": args.expected_count, "actual_responses": len(responses)})
    if args.mode == "replay":
        if not args.candidate_manifest:
            parser.error("replay requires --candidate-manifest with original full-text/meta hashes")
        candidates = {(r["collection"], r["chunkId"]): r for r in rows(args.candidate_manifest)}
        summary["inputs"].append({"role": "candidate_manifest", "name": args.candidate_manifest.name, "sha256": file_hash(args.candidate_manifest)})
        dbs = {}
        summary["indices"] = {}
        for entry in args.index:
            wg, path = entry.split("=", 1)
            if wg in dbs:
                parser.error("duplicate index WG: " + wg)
            dbs[wg] = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
            dbs[wg].execute("PRAGMA query_only=ON")
            summary["indices"][wg] = {"name": Path(path).name, "bytes": Path(path).stat().st_size,
                                       "docs_schema_sha256": digest(dbs[wg].execute("SELECT sql FROM sqlite_master WHERE name='docs'").fetchone()[0].encode())}
        cache = {}
        details, contexts = [], []
        for (item_id, model), response in sorted(responses.items()):
            item = items[item_id]
            if digest(item["question"].encode()) != response["questionSha256"]:
                failures.append({"kind": "question_hash", "id": item_id, "model": model})
                continue
            chunks = []
            for candidate in response["retrieved"]:
                key = candidate["collection"], candidate["chunkId"]
                if key not in cache:
                    db = dbs.get(item["wg"])
                    if db is None:
                        raise ValueError("Missing --index for " + item["wg"])
                    found = db.execute("SELECT point_id,text,meta FROM docs WHERE collection=? AND chunk_id=? LIMIT 2", key).fetchall()
                    if len(found) != 1 or key not in candidates:
                        raise ValueError("Candidate missing, ambiguous or absent from manifest: " + str(key))
                    point_id, text, meta_json = found[0]
                    meta = json.loads(meta_json)
                    ordered_meta = {key: meta[key] for key in META_KEYS if meta.get(key)}
                    expected = candidates[key]
                    if digest(text.encode()) != expected["text_sha256"] or canonical_hash(ordered_meta) != expected["meta_sha256"] or str(point_id) != expected["point_id"]:
                        failures.append({"kind": "candidate_hash_or_id", "collection": key[0], "chunkId": key[1]})
                    cache[key] = {"text": text, "meta": ordered_meta}
                chunks.append(cache[key])
            request = module.text_request(item, model, args.context_tokens, chunks)
            actual = module.request_sha(request)
            equal = actual == response["requestSha256"]
            detail = {"id": item_id, "model": model, "expected_request_sha256": response["requestSha256"], "actual_request_sha256": actual, "equal": equal}
            details.append(detail)
            if not equal:
                failures.append({"kind": "request_hash", **detail})
            contexts.append({"id": item_id, "wg": item["wg"], "model": model, "questionSha256": response["questionSha256"], "requestSha256": response["requestSha256"], "retrieved": response["retrieved"]})
        for db in dbs.values():
            db.close()
        summary.update(request_hashes_equal=sum(r["equal"] for r in details), unique_candidates=len(cache),
                       scope="Archived ordered top-8 contexts reconstructed from restored SQLite and original request builder.")
        save(args.out / "request_checks.json", details)
        with (args.out / "contexts.jsonl").open("w") as stream:
            for row in contexts:
                stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    else:
        if not all((args.common_dir, args.local_model_module, args.snapshot, args.qdrant_url)):
            parser.error("fresh-query requires --common-dir, --local-model-module, --snapshot and --qdrant-url")
        url = urllib.parse.urlsplit(args.qdrant_url)
        if url.scheme != "http" or url.hostname not in ("localhost", "127.0.0.1", "::1") or url.username or url.password:
            parser.error("fresh-query supports existing localhost HTTP Qdrant only")
        constants = {}
        for node in ast.parse(args.local_model_module.read_text()).body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                try:
                    constants[node.targets[0].id] = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    pass
        checked_files = {}
        for name, expected in constants["BGE_M3_FILES"].items():
            path = args.snapshot / name
            if len(expected) == 64:
                actual = file_hash(path)
            else:
                actual = hashlib.sha1(f"blob {path.stat().st_size}\0".encode() + path.read_bytes()).hexdigest()
            if actual != expected:
                raise ValueError("Pinned model file hash differs: " + name)
            checked_files[name] = {"expected": expected, "equal": True}
        if list(args.snapshot.glob("*.safetensors")) or list(args.snapshot.glob("*.index.json")):
            raise ValueError("Unpinned preferred model weights in snapshot")
        os.environ.update(CUDA_VISIBLE_DEVICES="", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
        sys.path.insert(0, str(args.common_dir.resolve()))
        registry = importlib.import_module("common.embedding_registry")
        import torch
        torch.set_num_threads(args.torch_threads)
        # Select the explicitly hash-verified local snapshot; encoding stays in the original registry.
        registry.local_snapshot_path = lambda encoder: str(args.snapshot.resolve())
        encoder = registry.require_local("ran1_resolution_chunks")
        if (encoder.model != constants["BGE_M3_REPO"] or encoder.revision != constants["BGE_M3_REVISION"]
                or encoder.dim != 1024 or encoder.max_tokens != 8192 or encoder.adapter is not None):
            raise ValueError("Encoder declaration differs from pinned empty-prefix BGE-M3 contract")
        model = registry.load_local_encoder(encoder, device="cpu")
        if str(model.device) != "cpu":
            raise ValueError("fresh-query requires CPU")
        module.QDRANT = args.qdrant_url.rstrip("/")
        original_embed = registry.embed_query_local
        query_vectors = []
        def tracked_embed(collection, question):
            vector = original_embed(collection, question)
            query_vectors.append({"collection": collection, "question_sha256": digest(question.encode()), "dim": len(vector), "float32_sha256": digest(struct.pack("<" + "f" * len(vector), *vector))})
            return vector
        registry.embed_query_local = tracked_embed
        selected = list(items.values())
        if args.fresh_items == "first-per-wg":
            first_by_wg = {}
            for item in selected:
                first_by_wg.setdefault(item["wg"], item)
            selected = list(first_by_wg.values())
        fresh = []
        started = time.monotonic()
        for item in selected:
            chunks = module.retrieve(item, 8)
            actual = [{key: chunk[key] for key in ("collection", "chunkId", "score")} for chunk in chunks]
            checks = []
            actual_ids = [(c["collection"], c["chunkId"]) for c in actual]
            for (item_id, reader), response in responses.items():
                if item_id != item["id"]:
                    continue
                old_ids = [(c["collection"], c["chunkId"]) for c in response["retrieved"]]
                rebuilt = module.request_sha(module.text_request(item, reader, args.context_tokens, chunks))
                checks.append({"model": reader, "candidate_set_equal": set(old_ids) == set(actual_ids), "ordered_candidates_equal": old_ids == actual_ids, "saved_request_sha256": response["requestSha256"], "fresh_request_sha256": rebuilt, "request_equal": rebuilt == response["requestSha256"]})
            fresh.append({"id": item["id"], "actual": actual, "checks": checks})
        summary.update(scope="Fresh CPU query encoding and existing-Qdrant top-8 retrieval; model answers and document vectors retain their recorded state.",
                       device="cpu", torch_threads=args.torch_threads, torch=torch.__version__, python=sys.version,
                       model_repository=constants["BGE_M3_REPO"], model_revision=constants["BGE_M3_REVISION"], model_files=checked_files,
                       seconds=time.monotonic()-started, fresh_items=len(fresh), results=fresh, query_vectors=query_vectors)
    summary["failures"] = failures
    summary["passed"] = not failures
    save(args.out / "receipt.json", summary)
    print(json.dumps({key: summary[key] for key in ("mode", "admitted_items", "responses", "passed")}))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
