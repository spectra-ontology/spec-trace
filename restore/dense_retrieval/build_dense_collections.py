#!/usr/bin/env python3
"""Build fresh, isolated dense collections from restored read-only retrieval SQLite.

Uses only the pinned local document/query encoder. Existing collection names are
refused. A local disk Qdrant client supports bounded construction checks; an
explicit localhost server supports complete collection reconstruction.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import struct
import sys
import time
import urllib.parse

SUFFIXES = ("resolution_chunks", "cr_chunks", "tdoc_chunks")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def canonical(value) -> str:
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True).encode())


def vector_hash(vector) -> str:
    return sha(struct.pack("<" + "f" * len(vector), *vector))


def prepare_document(collection: str, text: str, tdoc_mode: str) -> str:
    if collection.endswith("_tdoc_chunks"):
        return text if tdoc_mode == "full" else text.strip()
    if collection.endswith("_cr_chunks"):
        return text.strip()
    if collection.endswith("_resolution_chunks"):
        return text
    raise ValueError("Unsupported collection: " + collection)


def target_name(prefix: str, source: str) -> str:
    if not re.fullmatch(r"rebuild_[a-z0-9][a-z0-9_]{0,47}_", prefix):
        raise ValueError("--prefix must be rebuild_<label>_ with lowercase letters/digits/underscores")
    if not re.fullmatch(r"ran[1-5]_(resolution|cr|tdoc)_chunks", source):
        raise ValueError("Unsupported source collection: " + source)
    return prefix + source


def checked_snapshot(snapshot: Path, contract: dict) -> dict:
    checked = {}
    for name, pin in contract["model"]["files"].items():
        path = snapshot / name
        actual = file_sha(path)
        if actual != pin["sha256"] or path.stat().st_size != pin["bytes"]:
            raise ValueError("Pinned model file differs: " + name)
        checked[name] = actual
    if list(snapshot.glob("*.safetensors")) or list(snapshot.glob("*.index.json")):
        raise ValueError("Snapshot contains an additional preferred unpinned weight file")
    return checked


def sqlite_rows(db, collection, limit):
    count = 0
    # The restored schema indexes (collection, chunk_id). Stream that order;
    # sorting full text rows by unrelated row IDs would materialize the corpus.
    sql = "SELECT point_id,chunk_id,text,meta FROM docs WHERE collection=? ORDER BY chunk_id"
    for row in db.execute(sql, (collection,)):
        point_id, chunk_id, text, meta = row
        if not text.strip():
            continue
        yield int(point_id), chunk_id, text, json.loads(meta)
        count += 1
        if limit and count >= limit:
            break


def build(args) -> dict:
    started = time.monotonic()
    if args.out.exists() and any(args.out.iterdir()):
        raise ValueError("--out must be new or empty")
    if args.limit_per_collection < 0 or args.batch_size < 1 or args.torch_threads < 1:
        raise ValueError("Limits, batch size and thread count are invalid")
    contract = json.loads(args.contract.read_text())
    checked = checked_snapshot(args.snapshot, contract)
    indices = {}
    for entry in args.index:
        wg, path = entry.split("=", 1)
        if wg not in [f"RAN{i}" for i in range(1, 6)] or wg in indices:
            raise ValueError("Duplicate or unsupported index WG: " + wg)
        indices[wg] = Path(path).resolve()
    if not indices:
        raise ValueError("At least one read-only --index is required")
    sources = [f"{wg.lower()}_{suffix}" for wg in sorted(indices) for suffix in SUFFIXES]
    targets = {source: target_name(args.prefix, source) for source in sources}
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    if args.device == "cpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
    import torch
    torch.set_num_threads(args.torch_threads)
    if args.device == "cuda" and not torch.cuda.is_available():
        raise ValueError("Requested CUDA device is unavailable")
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    if args.qdrant_path:
        if args.qdrant_path.exists() and any(args.qdrant_path.iterdir()):
            raise ValueError("Local Qdrant path must be new or empty")
        client = QdrantClient(path=str(args.qdrant_path))
        backend = "local-disk exact cosine reference"
    else:
        url = urllib.parse.urlsplit(args.qdrant_url)
        if url.scheme != "http" or url.hostname not in ("localhost", "127.0.0.1", "::1") or url.username or url.password:
            raise ValueError("Fresh server builds require an explicit localhost HTTP Qdrant")
        client = QdrantClient(url=args.qdrant_url, timeout=120)
        backend = "localhost Qdrant server"
    try:
        existing = {c.name for c in client.get_collections().collections}
        if existing & set(targets.values()):
            raise ValueError("Target collection already exists: " + str(sorted(existing & set(targets.values()))))
        sys.path.insert(0, str(args.common_dir.resolve()))
        registry = importlib.import_module("common.embedding_registry")
        registry.local_snapshot_path = lambda encoder: str(args.snapshot.resolve())
        enc = registry.require_local(sources[0])
        if (enc.model != contract["model"]["repository"] or enc.revision != contract["model"]["revision"]
                or enc.dim != 1024 or enc.max_tokens != 8192 or enc.adapter is not None):
            raise ValueError("Encoder differs from the pinned empty-prefix BGE-M3 contract")
        model = registry.load_local_encoder(enc, device=args.device)
        args.out.mkdir(parents=True, exist_ok=True)
        audit = sqlite3.connect(args.out / "point_audit.sqlite3")
        audit.execute("CREATE TABLE points(collection TEXT,point_id TEXT,chunk_id TEXT,payload_sha TEXT,input_sha TEXT,encoded_vector_sha TEXT,stored_vector_sha TEXT,encoded_vector_f32 BLOB,PRIMARY KEY(collection,point_id))")
        receipt = {"scope": "bounded empty-collection construction pilot" if args.limit_per_collection else "complete selected-WG collection construction",
            "builder_sha256": file_sha(Path(__file__)), "contract_sha256": file_sha(args.contract),
            "encoding_registry_sha256": file_sha(args.common_dir / "common/embedding_registry.py"),
            "backend": backend, "device": str(model.device), "python": sys.version, "torch": torch.__version__,
            "qdrant_client": importlib.metadata.version("qdrant-client"), "tdoc_preprocessing": args.tdoc_mode,
            "index_origin": args.index_origin,
            "dependencies": {name: importlib.metadata.version(name) for name in ("torch", "transformers", "sentence-transformers", "qdrant-client", "numpy", "huggingface-hub", "safetensors")},
            "model_repository": enc.model, "model_revision": enc.revision, "verified_model_files": checked,
            "limit_per_collection": args.limit_per_collection, "answer_model_called": False,
            "source_indices": {}, "collections": {}, "queries": []}
        for wg, path in sorted(indices.items()):
            stat_before = path.stat()
            db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
            db.execute("PRAGMA query_only=ON")
            receipt["source_indices"][wg] = {"name": path.name, "bytes": stat_before.st_size,
                "docs_schema_sha256": sha(db.execute("SELECT sql FROM sqlite_master WHERE name='docs'").fetchone()[0].encode())}
            for suffix in SUFFIXES:
                source = f"{wg.lower()}_{suffix}"
                config = contract["qdrant"]["collections"][source]
                source_count = db.execute("SELECT count(*) FROM docs WHERE collection=?", (source,)).fetchone()[0]
                if source_count != config["points"]:
                    raise ValueError(f"Source count differs from frozen collection: {source}: {source_count}")
                target = targets[source]
                cfg = config["config"]
                client.create_collection(collection_name=target,
                    vectors_config=models.VectorParams(**cfg["params"]["vectors"]),
                    shard_number=cfg["params"]["shard_number"], replication_factor=cfg["params"]["replication_factor"],
                    write_consistency_factor=cfg["params"]["write_consistency_factor"],
                    on_disk_payload=cfg["params"]["on_disk_payload"],
                    hnsw_config=models.HnswConfigDiff(**cfg["hnsw_config"]),
                    optimizers_config=models.OptimizersConfigDiff(**cfg["optimizer_config"]),
                    wal_config=models.WalConfigDiff(**cfg["wal_config"]))
                initial_count = client.count(target, exact=True).count
                if initial_count != 0:
                    raise ValueError("New collection is not empty: " + target)
                expected = args.limit_per_collection and min(args.limit_per_collection, source_count) or source_count
                loaded, max_vector_delta, batch = 0, 0.0, []
                digest = hashlib.sha256()

                def flush(batch):
                    nonlocal loaded, max_vector_delta
                    inputs = [prepare_document(source, row[2], args.tdoc_mode) for row in batch]
                    prepared, _ = registry.truncate_to_encoder_budget(enc, inputs, input_kind="document")
                    vectors = registry.embed_local(enc, inputs, batch_size=args.batch_size, input_kind="document")
                    payloads = [{**row[3], "chunkId": row[1], "text": row[2]} for row in batch]
                    points = [models.PointStruct(id=row[0], vector=vector, payload=payload)
                              for row, vector, payload in zip(batch, vectors, payloads)]
                    client.upsert(target, points=points, wait=True)
                    stored = {p.id: p for p in client.retrieve(target, ids=[r[0] for r in batch], with_payload=True, with_vectors=True)}
                    if len(stored) != len(batch):
                        raise ValueError("Stored point count differs from batch")
                    for row, vector, payload, text_input in zip(batch, vectors, payloads, prepared):
                        point = stored[row[0]]
                        if canonical(point.payload) != canonical(payload) or len(point.vector) != 1024:
                            raise ValueError("Stored payload or vector dimension differs")
                        delta = max(abs(a - b) for a, b in zip(vector, point.vector))
                        norm = math.sqrt(sum(v*v for v in point.vector))
                        if delta > 1e-5 or abs(norm - 1) > 1e-4:
                            raise ValueError("Stored normalized vector differs from encoded vector")
                        max_vector_delta = max(max_vector_delta, delta)
                        values = (source, str(row[0]), row[1], canonical(payload), sha(text_input.encode()), vector_hash(vector), vector_hash(point.vector))
                        # A bounded pilot retains encoder outputs for an
                        # independent reopen comparison. Local cosine stores
                        # may renormalize on reload, changing float32 bytes.
                        vector_receipt = struct.pack("<" + "f" * len(vector), *vector) if args.limit_per_collection else None
                        audit.execute("INSERT INTO points VALUES(?,?,?,?,?,?,?,?)", (*values, vector_receipt))
                        digest.update((json.dumps(values, ensure_ascii=False) + "\n").encode())
                        loaded += 1
                    audit.commit()

                for row in sqlite_rows(db, source, args.limit_per_collection):
                    batch.append(row)
                    if len(batch) == args.batch_size:
                        flush(batch)
                        batch = []
                if batch:
                    flush(batch)
                final_count = client.count(target, exact=True).count
                if loaded != expected or final_count != expected:
                    raise ValueError(f"Loaded coverage differs: {source}: {loaded}/{expected}/{final_count}")
                receipt["collections"][source] = {"target": target, "source_points": source_count,
                    "initial_count": initial_count, "loaded_points": loaded, "verified_stored_points": final_count,
                    "point_fingerprint_sha256": digest.hexdigest(), "max_stored_vector_absolute_delta": max_vector_delta,
                    "actual_vector_config": client.get_collection(target).config.params.vectors.model_dump(mode="json")}
                print(json.dumps({"collection": source, "loaded": loaded, "verified": final_count}), flush=True)
            db.close()
            stat_after = path.stat()
            if (stat_before.st_size, stat_before.st_mtime_ns) != (stat_after.st_size, stat_after.st_mtime_ns):
                raise ValueError("Read-only source index changed during build: " + wg)
        questions = {}
        for path in args.items:
            for line in path.read_text().splitlines():
                item = json.loads(line)
                if item["wg"] in indices:
                    questions.setdefault(item["wg"], item)
        for wg, item in sorted(questions.items()):
            found, vectors = [], []
            for suffix in SUFFIXES:
                source = f"{wg.lower()}_{suffix}"
                vector = registry.embed_query_local(source, item["question"])
                vectors.append(vector_hash(vector))
                result = client.query_points(targets[source], query=vector, limit=8, with_payload=True).points
                for point in result:
                    expected = audit.execute("SELECT payload_sha FROM points WHERE collection=? AND point_id=?", (source, str(point.id))).fetchone()
                    if expected is None or expected[0] != canonical(point.payload):
                        raise ValueError("Retrieved payload fails loaded-content fingerprint")
                    found.append({"collection": source, "point_id": str(point.id), "chunkId": point.payload["chunkId"], "score": point.score})
            receipt["queries"].append({"id": item["id"], "wg": wg, "question_sha256": sha(item["question"].encode()),
                "per_collection_query_vector_sha256": vectors,
                "merged_top8": sorted(found, key=lambda r: -r["score"])[:8], "all_retrieved_payloads_verified": True})
        if args.items and set(questions) != set(indices):
            raise ValueError("Query pilot lacks a question for one selected WG")
        audit.close()
        receipt["point_audit_sha256"] = file_sha(args.out / "point_audit.sqlite3")
        receipt["seconds"] = time.monotonic() - started
        receipt["passed"] = True
        (args.out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        return receipt
    finally:
        client.close()


def main():
    here = Path(__file__).resolve().parent
    release = here.parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=here / "encoding_retrieval_contract.json")
    parser.add_argument("--common-dir", type=Path, default=release / "code/scripts/common")
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--index", action="append", required=True, metavar="WG=SQLITE")
    parser.add_argument("--index-origin", choices=("restored", "retained_original"), required=True)
    parser.add_argument("--items", type=Path, action="append", default=[])
    parser.add_argument("--tdoc-mode", choices=("full", "incremental"), required=True)
    parser.add_argument("--prefix", required=True)
    backend = parser.add_mutually_exclusive_group(required=True)
    backend.add_argument("--qdrant-path", type=Path)
    backend.add_argument("--qdrant-url")
    parser.add_argument("--limit-per-collection", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--torch-threads", type=int, default=2)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    receipt = build(args)
    print(json.dumps({"passed": receipt["passed"], "collections": len(receipt["collections"]), "queries": len(receipt["queries"]), "seconds": receipt["seconds"]}))


if __name__ == "__main__":
    main()
