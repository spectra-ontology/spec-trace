#!/usr/bin/env python3
"""Independently verify a bounded empty-store build against source SQLite and Qdrant."""
import argparse
import base64
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import struct


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True).encode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--point-ledger", type=Path, required=True)
    parser.add_argument("--qdrant-path", type=Path, required=True)
    parser.add_argument("--index", action="append", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text())
    points = [json.loads(line) for line in args.point_ledger.read_text().splitlines() if line.strip()]
    assert receipt["passed"] and receipt["limit_per_collection"] > 0
    indices = {wg: sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
               for wg, path in (entry.split("=", 1) for entry in args.index)}
    from qdrant_client import QdrantClient
    client = QdrantClient(path=str(args.qdrant_path))
    try:
        collections = receipt["collections"]
        assert {c.name for c in client.get_collections().collections} == {c["target"] for c in collections.values()}
        checked = []
        for row in points:
            source, point_id = row["collection"], int(row["point_id"])
            db = indices[source.split("_", 1)[0].upper()]
            matches = db.execute("SELECT point_id,chunk_id,text,meta FROM docs WHERE collection=? AND chunk_id=?", (source, row["chunk_id"])).fetchall()
            assert len(matches) == 1
            source_point_id, chunk_id, text, meta = matches[0]
            assert str(source_point_id) == row["point_id"]
            payload = {**json.loads(meta), "chunkId": chunk_id, "text": text}
            target = collections[source]["target"]
            point = client.retrieve(target, [point_id], with_payload=True, with_vectors=True)[0]
            assert canonical(payload) == canonical(point.payload) == row["payload_sha"]
            assert len(point.vector) == 1024 and all(math.isfinite(v) for v in point.vector)
            assert abs(math.sqrt(sum(v*v for v in point.vector)) - 1) < 1e-4
            actual_vector_hash = digest(struct.pack("<" + "f" * len(point.vector), *point.vector))
            reference_bytes = base64.b64decode(row["encoded_vector_float32_base64"], validate=True)
            assert digest(reference_bytes) == row["encoded_vector_sha"]
            reference = struct.unpack("<1024f", reference_bytes)
            delta = max(abs(a - b) for a, b in zip(reference, point.vector))
            assert delta <= 1e-5
            nearest = client.query_points(target, query=point.vector, limit=1, with_payload=False).points
            assert nearest and nearest[0].score > .9999
            # Equal-text vectors may tie in a larger pilot; verify a self score
            # and collection membership rather than assuming a tie order.
            assert any(int(nearest[0].id) == int(r["point_id"]) for r in points if r["collection"] == source)
            checked.append({"collection": source, "point_id": str(point_id), "payload_equal_source": True,
                "stored_vector_sha256_after_reopen": actual_vector_hash,
                "encoded_vector_sha256": row["encoded_vector_sha"], "max_vector_absolute_delta_after_reopen": delta,
                "self_query_score": nearest[0].score})
        for source, block in collections.items():
            assert block["initial_count"] == 0
            expected = len([r for r in points if r["collection"] == source])
            assert client.count(block["target"], exact=True).count == expected == block["loaded_points"]
        result = {"passed": True, "receipt_sha256": digest(args.receipt.read_bytes()),
            "point_ledger_sha256": digest(args.point_ledger.read_bytes()), "collections": len(collections),
            "verified_points": len(checked), "source_payload_checks": checked,
            "fresh_question_retrievals": len(receipt["queries"]),
            "all_fresh_retrieved_payloads_verified": all(q["all_retrieved_payloads_verified"] for q in receipt["queries"])}
        args.out.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({k: result[k] for k in ("passed", "collections", "verified_points", "fresh_question_retrievals")}))
    finally:
        client.close()
        for db in indices.values():
            db.close()


if __name__ == "__main__":
    main()
