"""Exact, journalled projection of live Resolution content into its vector channel.

Spec: docs/tsg/RAN/email/RAN2/phase-3/design-spec/hard_anchor_spec.md
Ontology: Resolution.resolutionId is the graph/vector foreign key.
Cycle: ontology semantic reconciliation, source generation fencing.
Only exact same-text vectors within the declared collection space are reused.
New text uses the pinned local encoder. Every replaced/deleted point is archived
with its vector before mutation; absent points are pruned after positive coverage.
"""
from __future__ import annotations

from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path

from common import axis, credentials, review_artifacts
from common.service_endpoints import QDRANT_URL
from common.atomic_io import copy_file_atomic, write_text_atomic
from common.chunker import count_tokens, split_giant_section_v2
from common.embedding_registry import encoder_for, embed_local, force_hf_offline
from common.gpu_duty import rested
from common.qdrant_generation import check_scroll_progress

FIELDS = ("resolutionId", "chunkId", "isAgreement", "resolutionType", "text", "charLen", "tokenLen", "resolutionScope")
SOURCE_QUERY = """MATCH (r:Resolution)
RETURN r.resolutionId AS rid, r.content AS content,
       'Agreement' IN labels(r) AS isAgreement, r.resolutionScope AS resolutionScope ORDER BY rid"""


def point_id(chunk_id: str) -> int:
    return int(hashlib.md5(chunk_id.encode()).hexdigest()[:16], 16)


def source_digest(rows: list[dict]) -> str:
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def console_summary(summary):
    """Keep full recovery identities in the durable journal, not console copies."""
    return {key: (len(value) if key == 'newPointIds' else value)
            for key, value in summary.items()}


def read_source(wg: str) -> list[dict]:
    from neo4j import GraphDatabase, READ_ACCESS
    with GraphDatabase.driver(axis.bolt_uri(wg), auth=credentials.neo4j_auth()) as driver:
        with driver.session(default_access_mode=READ_ACCESS) as session:
            return [dict(row) for row in session.run(SOURCE_QUERY)]


def projection(rows: list[dict]) -> dict[int, dict]:
    if not rows:
        raise ValueError("Resolution source population is empty")
    result, seen = {}, set()
    for row in rows:
        rid, content = row["rid"], row["content"]
        if not isinstance(rid, str) or not rid.strip() or rid in seen:
            raise ValueError("Missing or duplicate Resolution identity")
        if type(row.get("isAgreement")) is not bool:
            raise ValueError(f"Resolution Agreement label must be Boolean: {rid}")
        seen.add(rid)
        prefix = rid.split("-", 1)[0]
        document_event = prefix == 'DOC' and row.get('resolutionScope') == 'document_disposition'
        if not document_event and (prefix not in {"AGR", "CON", "WA"} or
                                   (prefix == "AGR") != row["isAgreement"]):
            raise ValueError(f"Resolution kind/label mismatch: {rid}")
        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"Resolution content is empty: {rid}")
        chunks = split_giant_section_v2([content], target=2000, overlap=100, hard_max=7500)
        if not chunks:
            raise ValueError(f"Resolution produced zero chunks: {rid}")
        for i, text in enumerate(chunks):
            cid = f"{rid}#{i}"
            pid = point_id(cid)
            if pid in result:
                raise ValueError(f"Point identity collision: {cid}")
            result[pid] = dict(resolutionId=rid, chunkId=cid, isAgreement=row["isAgreement"],
                               resolutionType=prefix, text=text, charLen=len(text),
                               tokenLen=count_tokens(text), resolutionScope=row.get('resolutionScope'))
    return result


def payload_equal(actual: dict, expected: dict) -> bool:
    return all(actual.get(key) == expected[key] for key in FIELDS)


def plan(expected: dict[int, dict], existing: dict[int, dict]) -> dict:
    by_text = {}
    for pid, payload in existing.items():
        text = payload.get("text")
        if isinstance(text, str):
            by_text.setdefault(text, pid)
    unchanged, metadata, reuse, embed = [], [], {}, []
    for pid, payload in expected.items():
        old = existing.get(pid)
        if old is not None and payload_equal(old, payload):
            unchanged.append(pid)
        elif old is not None and old.get("text") == payload["text"]:
            metadata.append(pid)
        elif payload["text"] in by_text:
            reuse[pid] = by_text[payload["text"]]
        else:
            embed.append(pid)
    return dict(unchanged=unchanged, metadata=metadata, reuse=reuse, embed=embed,
                prune=sorted(set(existing) - set(expected)))


def batches(values, size=128):
    values = list(values)
    for start in range(0, len(values), size):
        yield values[start:start + size]


def scan(client, collection: str) -> dict[int, dict]:
    result, offset = {}, None
    seen_offsets = set()
    while True:
        points, offset = client.scroll(collection, limit=512, offset=offset,
                                       with_payload=True, with_vectors=False)
        check_scroll_progress(offset, seen_offsets)
        for point in points:
            if not isinstance(point.id, int) or point.id in result:
                raise ValueError("Unexpected or duplicate Resolution vector identity")
            result[point.id] = point.payload or {}
        if offset is None:
            return result


def valid_vector(vector, dim: int) -> bool:
    return (isinstance(vector, list) and len(vector) == dim
            and all(isinstance(v, (int, float)) and math.isfinite(v) for v in vector)
            and any(v != 0 for v in vector))


def reconcile(wg: str, *, apply=False, report_root: Path | None = None) -> dict:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import PointStruct, PointIdsList, VectorParams, Distance, PayloadSchemaType

    collection = axis.qdrant_collection(wg, "resolution_chunks")
    encoder = encoder_for(collection)
    if encoder.provider != "local":
        raise ValueError("Resolution reconciliation requires the declared local encoder")
    with closing(QdrantClient(url=QDRANT_URL, timeout=120)) as client:
        rows = read_source(wg)
        expected = projection(rows)
        existed = client.collection_exists(collection)
        if existed:
            config = client.get_collection(collection).config.params.vectors
            if not hasattr(config, "size") or config.size != encoder.dim or str(config.distance).casefold() != "cosine":
                raise ValueError("Collection vector configuration differs from its declared space")
        existing = scan(client, collection) if existed else {}
        changes = plan(expected, existing)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        run_dir = (review_artifacts.review_run(axis.PROJECT_ROOT, "resolution-vectors", stamp, wg)
                   if report_root is None else report_root / review_artifacts.review_run_name(stamp, wg))
        run_dir.mkdir(parents=True, exist_ok=False)
        digest = source_digest(rows)
        summary = dict(wg=wg, collection=collection, apply=apply, sourceResolutions=len(rows),
                       expectedPoints=len(expected), beforePoints=len(existing), beforeCollectionExists=existed,
                       sourceSha256=digest,
                       counts={key: len(value) for key, value in changes.items()},
                       reportDirectory=str(run_dir.relative_to(axis.PROJECT_ROOT)), status="planned")
        write_text_atomic(run_dir / "status.json", json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(console_summary(summary), ensure_ascii=False), flush=True)
        if not apply:
            return summary

        changed_ids = set(changes["metadata"]) | set(changes["reuse"]) | set(changes["embed"])
        touched = (changed_ids & set(existing)) | set(changes["prune"])
        backups = {}
        backup_path = run_dir / "before_points.jsonl.gz"
        # Finish and close the durable archive before the first point mutation.
        with gzip.open(backup_path, "wt", encoding="utf-8") as handle:
            for ids in batches(sorted(touched)):
                found = {p.id: p for p in client.retrieve(collection, ids, with_payload=True, with_vectors=True)}
                if set(found) != set(ids):
                    raise RuntimeError("A planned preimage disappeared before journalling")
                for pid in ids:
                    point = found[pid]
                    if point.payload != existing[pid]:
                        raise RuntimeError("A planned point changed before journalling")
                    if not valid_vector(point.vector, encoder.dim):
                        raise ValueError(f"Invalid vector preimage: {pid}")
                    handle.write(json.dumps(dict(id=pid, payload=point.payload, vector=point.vector),
                                            ensure_ascii=False, separators=(",", ":")) + "\n")
                    backups[pid] = point
        with backup_path.open("rb") as handle:
            import os
            os.fsync(handle.fileno())
        summary["backupSha256"] = hashlib.sha256(backup_path.read_bytes()).hexdigest()
        summary["newPointIds"] = sorted(changed_ids - set(existing))
        write_text_atomic(run_dir / "status.json", json.dumps(summary, ensure_ascii=False, indent=2) + "\n")

        reuse_sources = set(changes["reuse"].values())
        source_points = {pid: backups[pid] for pid in reuse_sources if pid in backups}
        for ids in batches(sorted(reuse_sources - set(source_points))):
            source_points.update({p.id: p for p in client.retrieve(collection, ids, with_payload=True, with_vectors=True)})
        for pid in reuse_sources:
            point = source_points.get(pid)
            if point is None or point.payload != existing[pid] or not valid_vector(point.vector, encoder.dim):
                raise RuntimeError("Exact-text vector reuse preimage is invalid or changed")
        if source_digest(read_source(wg)) != digest:
            raise RuntimeError("Resolution source changed before mutation")
        if not existed:
            client.create_collection(collection_name=collection,
                                     vectors_config=VectorParams(size=encoder.dim, distance=Distance.COSINE))
            for field in ("resolutionId", "chunkId", "resolutionType"):
                client.create_payload_index(collection, field, PayloadSchemaType.KEYWORD, wait=True)
            client.create_payload_index(collection, "isAgreement", PayloadSchemaType.BOOL, wait=True)

        def merged_payload(pid, *, embedded=False, source_pid=None):
            payload = dict(existing.get(pid, {}))
            # Text-specific provenance belongs to the actual vector, not the old ID.
            if pid in changes["embed"] or pid in changes["reuse"]:
                for key in list(payload):
                    if key.startswith("embedding") or key.startswith("vectorReuse"):
                        del payload[key]
            payload.update(expected[pid])
            payload["sourceGenerationSha256"] = digest
            if embedded:
                payload.update(embeddingModel=encoder.model, embeddingRevision=encoder.revision,
                               embeddingEncoderKey=encoder.key)
            elif source_pid is not None:
                old = source_points[source_pid].payload
                payload.update({k: v for k, v in old.items() if k.startswith("embedding")})
                payload.update(vectorReuseSourcePointId=str(source_pid),
                               vectorReuseTextSha256=hashlib.sha256(payload["text"].encode()).hexdigest(),
                               observedCollectionEncoderKey=encoder.key)
            return payload

        for ids in batches(changes["metadata"]):
            points = [PointStruct(id=pid, vector=backups[pid].vector, payload=merged_payload(pid)) for pid in ids]
            client.upsert(collection, points, wait=True)
        for ids in batches(changes["reuse"]):
            points = [PointStruct(id=pid, vector=source_points[changes["reuse"][pid]].vector,
                                  payload=merged_payload(pid, source_pid=changes["reuse"][pid])) for pid in ids]
            client.upsert(collection, points, wait=True)
        if changes["embed"]:
            force_hf_offline()
            for ids in batches(changes["embed"], size=64):
                vectors = rested(embed_local, encoder, [expected[pid]["text"] for pid in ids], batch_size=4)
                if len(vectors) != len(ids) or not all(valid_vector(v, encoder.dim) for v in vectors):
                    raise ValueError("New local embeddings violate vector cardinality/space")
                client.upsert(collection, [PointStruct(id=pid, vector=v, payload=merged_payload(pid, embedded=True))
                                           for pid, v in zip(ids, vectors)], wait=True)
                print(f"{wg}: embedded {ids[-1]} ({len(ids)} points)", flush=True)

        # Verify complete positive coverage before deleting any obsolete generation.
        for ids in batches(expected):
            found = {p.id: p.payload or {} for p in client.retrieve(collection, ids, with_payload=True, with_vectors=False)}
            if set(found) != set(ids) or any(not payload_equal(found[pid], expected[pid]) for pid in ids):
                raise RuntimeError("Positive source projection verification failed; obsolete points retained")
        if source_digest(read_source(wg)) != digest:
            raise RuntimeError("Resolution source changed; obsolete points retained")
        for ids in batches(changes["prune"]):
            client.delete(collection, PointIdsList(points=ids), wait=True)
        after = scan(client, collection)
        if set(after) != set(expected) or any(not payload_equal(after[pid], expected[pid]) for pid in expected):
            raise RuntimeError("Post-mutation generation differs from the exact source projection")
        if source_digest(read_source(wg)) != digest:
            raise RuntimeError("Source changed during final verification; rerun reconciliation")
        summary.update(status="verified", afterPoints=len(after), missingForeignKeys=0,
                       sourcePayloadMismatches=0, remainingChanges={k: len(v) for k, v in plan(expected, after).items() if k != "unchanged"})
        counts = Counter(payload["resolutionId"] for payload in expected.values())
        type_counts = Counter(AGR=0, CON=0, WA=0)
        type_counts.update("AGR" if row["isAgreement"] else row["rid"].split("-", 1)[0]
                           for row in rows)
        metrics = dict(resolutions=len(rows), chunks=len(expected), points=len(after),
                       multi_chunk_resolutions=sum(count > 1 for count in counts.values()),
                       type_counts=dict(type_counts),
                       embed_failed=0, tokens=sum(payload["tokenLen"] for payload in expected.values()),
                       sourceSha256=digest, collection=collection, status="verified")
        # Publish the CQ input only after full source generation verification succeeds.
        metrics_text = "##METRICS##\n" + json.dumps(metrics, ensure_ascii=False) + "\n"
        log_dir = axis.tree_path("logs", wg=wg, track="email", phase=3, root=axis.PROJECT_ROOT)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "resolution_embed_run.log"
        if log_path.is_symlink():
            raise ValueError("Resolution metrics output must not be a symlink")
        if log_path.exists():
            before_log = run_dir / "before_resolution_embed_run.log"
            copy_file_atomic(log_path, before_log)
            summary["previousMetricsSha256"] = hashlib.sha256(before_log.read_bytes()).hexdigest()
        summary["metrics"] = metrics
        write_text_atomic(run_dir / "status.json", json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
        write_text_atomic(log_path, metrics_text)
        print(json.dumps(console_summary(summary), ensure_ascii=False), flush=True)
        print(metrics_text, end="", flush=True)
        return summary


def select_resolution_hit(hits, helpers, *, bracket, meetings, subject, res_meet, res_tokens):
    """Use the established E-3 total order for equal-score candidates."""
    if not hits:
        raise ValueError("A nonempty Resolution generation returned no candidate")
    if any(not math.isfinite(h.score) for h in hits):
        raise ValueError("Invalid Resolution candidate cosine")
    best = max(h.score for h in hits)
    if best < 0:
        raise ValueError("Invalid Resolution candidate cosine")
    return min((h for h in hits if h.score == best), key=lambda h: helpers.tiebreak_key(
        h, "resolution", bracket, meetings, subject, res_meet, res_tokens))


def reconcile_anchors(wg: str, *, apply=False) -> dict:
    """Refresh the complete Resolution candidate channel after source drift.

    Reuse the WG's E-3 top-k, tie order and measured pruning threshold. The
    threshold is an existing retrieval policy, not an accuracy measurement.
    Other anchor channels and their policies retain their own generation.
    """
    import importlib.util
    import struct
    from neo4j import GraphDatabase, READ_ACCESS
    from qdrant_client import QdrantClient, models as qm

    verified = reconcile(wg, apply=False)
    if any(n for key, n in verified["counts"].items() if key != "unchanged"):
        raise ValueError("Refresh the exact vector generation before its anchors")
    root = axis.PROJECT_ROOT
    path = axis.tree_path("scripts", wg=wg, track="email", phase=3, root=root) / "neo4j/01_generate_hard_anchors.py"
    spec = importlib.util.spec_from_file_location(f"resolution_anchors_{wg}", path)
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    threshold_path = axis.tree_path("logs", wg=wg, track="email", phase=3, root=root) / "s4_theta_derivation.json"
    policy_bytes = threshold_path.read_bytes()
    policy = json.loads(policy_bytes)
    threshold = policy["theta"]["resolution"]["theta"]
    if not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or not 0 <= threshold < 1:
        raise ValueError("A measured Resolution pruning policy is required")
    email_collection = axis.qdrant_collection(wg, "email_chunks")
    resolution_collection = axis.qdrant_collection(wg, "resolution_chunks")
    with closing(QdrantClient(url=QDRANT_URL, timeout=120)) as client:
        encoder = encoder_for(resolution_collection)
        email_encoder = encoder_for(email_collection)
        if (encoder.model, encoder.revision, encoder.dim) != (email_encoder.model, email_encoder.revision, email_encoder.dim):
            raise ValueError("Email and Resolution query vectors use different declared spaces")
        fields = ["chunkId", "messageId", "subject", "bracketIds", "meetingAnchors"]
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        run_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        run_dir = review_artifacts.review_run(root, "resolution-vectors", stamp, wg, variant="anchors")
        run_dir.mkdir(parents=True, exist_ok=False)
        query_before = """MATCH (m)-[a:ANCHORS]->(r)
            WHERE a.channel='resolution' AND a.state='candidate'
            RETURN elementId(a) AS edgeId, elementId(m) AS sourceId,
                   elementId(r) AS targetId, properties(a) AS properties
            ORDER BY edgeId"""
        driver = GraphDatabase.driver(axis.bolt_uri(wg), auth=credentials.neo4j_auth())
        try:
            with driver.session(default_access_mode=READ_ACCESS) as session:
                before = session.run(query_before).data()
                email_ids = {r["mid"] for r in session.run("MATCH (m:EmailMessage) RETURN m.id AS mid")}
            tdocs, res_meet, res_tokens, _ = helpers.preload(driver)
            with gzip.open(run_dir / "before_anchors.json.gz", "wt", encoding="utf-8") as handle:
                json.dump(before, handle, ensure_ascii=False, separators=(",", ":"))
            with (run_dir / "before_anchors.json.gz").open("rb") as handle:
                import os
                os.fsync(handle.fileno())
            before_sha = source_digest(before)
            candidates, seen, context_ids, email_count = [], set(), set(), 0
            fingerprint = hashlib.sha256()

            def fingerprint_point(digest, point):
                digest.update(json.dumps([point.id, point.payload], ensure_ascii=False,
                                         sort_keys=True, separators=(",", ":")).encode())
                digest.update(struct.pack(f"<{len(point.vector)}f", *point.vector))

            offset = None
            seen_offsets = set()
            while True:
                points, offset = client.scroll(email_collection, limit=256, offset=offset,
                                               with_payload=fields, with_vectors=True)
                check_scroll_progress(offset, seen_offsets)
                requests = []
                for point in points:
                    payload = point.payload or {}
                    if (point.id in seen or not payload.get("chunkId") or payload["chunkId"] in context_ids
                            or payload.get("messageId") not in email_ids
                            or not valid_vector(point.vector, encoder.dim)):
                        raise ValueError("Invalid, duplicate or orphan email query source")
                    seen.add(point.id)
                    context_ids.add(payload["chunkId"])
                    fingerprint_point(fingerprint, point)
                    requests.append(qm.QueryRequest(query=point.vector, limit=helpers.TOP_K,
                                                   with_payload=["resolutionId"]))
                responses = client.query_batch_points(resolution_collection, requests=requests) if requests else []
                if len(responses) != len(points):
                    raise ValueError("Resolution query response cardinality differs from its source")
                for point, response in zip(points, responses):
                    payload = point.payload
                    bracket = helpers.extract_bracket_tdocs(payload.get("bracketIds"))
                    meetings = {helpers.norm_meet_key(t) for t in payload.get("meetingAnchors", [])} - {None}
                    subject = helpers.tokenize(payload.get("subject") or "")
                    hit = select_resolution_hit(response.points, helpers, bracket=bracket,
                        meetings=meetings, subject=subject, res_meet=res_meet, res_tokens=res_tokens)
                    rid = (hit.payload or {}).get("resolutionId")
                    if rid not in res_tokens:
                        raise ValueError("Retrieved Resolution target is absent from the graph")
                    score = float(hit.score) if hit.score < 1.0 else 0.9999
                    if score >= threshold:
                        r_meets = res_meet.get(rid)
                        properties = dict(context_chunk_id=payload["chunkId"], entity_URI=rid,
                            relevance_score=score, channel="resolution", state="candidate",
                            source_tier=helpers.SOURCE_TIER, temporal_validity=run_ts,
                            corr_bracketId_match=False, corr_meeting_match=bool(meetings & r_meets) if meetings and r_meets else None,
                            corr_subject_overlap=helpers.jaccard(subject, res_tokens[rid]),
                            corr_bracketId_tdoc_direct=bool(bracket & tdocs),
                            sourceGenerationSha256=verified["sourceSha256"],
                            pruningPolicySha256=hashlib.sha256(policy_bytes).hexdigest())
                        candidates.append(dict(mid=payload["messageId"], rid=rid, properties=properties))
                email_count += len(points)
                if email_count and email_count % 25600 == 0:
                    print(f"{wg}: refreshed Resolution candidates for {email_count} email chunks", flush=True)
                if offset is None:
                    break
            if email_count == 0 or client.count(email_collection, exact=True).count != email_count:
                raise ValueError("Email candidate refresh did not cover the complete population")
            # Independently reread every input payload/vector before a DB mutation.
            after_fingerprint, offset, after_count = hashlib.sha256(), None, 0
            seen_offsets = set()
            while True:
                points, offset = client.scroll(email_collection, limit=512, offset=offset,
                                               with_payload=fields, with_vectors=True)
                check_scroll_progress(offset, seen_offsets)
                for point in points:
                    fingerprint_point(after_fingerprint, point)
                after_count += len(points)
                if offset is None:
                    break
            if after_count != email_count or after_fingerprint.digest() != fingerprint.digest():
                raise RuntimeError("Email vector generation changed during candidate refresh")
            if source_digest(read_source(wg)) != verified["sourceSha256"] or threshold_path.read_bytes() != policy_bytes:
                raise RuntimeError("Resolution source or measured pruning policy changed")
            summary = dict(wg=wg, apply=apply, status="planned", emailChunks=email_count,
                           sourceSha256=verified["sourceSha256"], emailSourceSha256=fingerprint.hexdigest(),
                           previousAnchors=len(before), expectedAnchors=len(candidates),
                           measuredThreshold=threshold, policyPath=str(threshold_path.relative_to(root)),
                           policySha256=hashlib.sha256(policy_bytes).hexdigest(),
                           backupSha256=hashlib.sha256((run_dir / "before_anchors.json.gz").read_bytes()).hexdigest())
            write_text_atomic(run_dir / "status.json", json.dumps(summary, indent=2) + "\n")
            if apply:
                def write(tx):
                    if source_digest(tx.run(query_before).data()) != before_sha:
                        raise RuntimeError("Resolution anchors changed before the write transaction")
                    tx.run("""MATCH ()-[a:ANCHORS]->()
                        WHERE a.channel='resolution' AND a.state='candidate' DELETE a""").consume()
                    written = 0
                    for rows in batches(candidates, size=2000):
                        written += tx.run("""UNWIND $rows AS row
                            MATCH (m:EmailMessage {id:row.mid})
                            MATCH (r:Resolution {resolutionId:row.rid})
                            CREATE (m)-[a:ANCHORS]->(r) SET a = row.properties
                            RETURN count(a) AS n""", rows=rows).single()["n"]
                    if written != len(candidates):
                        raise RuntimeError("Candidate endpoint coverage failed; transaction rolled back")
                    actual = tx.run("""MATCH (m)-[a:ANCHORS]->(r)
                        WHERE a.channel='resolution' AND a.state='candidate'
                        RETURN m.id AS mid, r.resolutionId AS rid, properties(a) AS properties
                        ORDER BY mid,rid,a.context_chunk_id""").data()
                    expected = [{**r, "properties": {k:v for k,v in r["properties"].items() if v is not None}} for r in candidates]
                    key = lambda r: (r["mid"], r["rid"], r["properties"]["context_chunk_id"])
                    if actual != sorted(expected, key=key):
                        raise RuntimeError("Final candidate properties differ; transaction rolled back")
                    return written
                with driver.session() as session:
                    summary["writtenAnchors"] = session.execute_write(write)
                summary["status"] = "verified"
                write_text_atomic(run_dir / "status.json", json.dumps(summary, indent=2) + "\n")
            print(json.dumps(summary), flush=True)
            return summary
        finally:
            driver.close()
