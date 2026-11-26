#!/usr/bin/env python3
"""Export a dependency-checked CQ view and restore it into an explicitly empty graph."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
import logging
import math
import os
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from runner import verify, canonical_digest, file_digest

logging.getLogger("neo4j").setLevel(logging.CRITICAL)

HELPER_LABEL = "_SpectraCQRestore"
HELPER_KEY = "_spectraCQSourceId"
ORDER_KEY = "_spectraCQSourceOrder"
TEXT_PROPERTIES = {"content", "contentWithEquations"}
TEXT_LABELS = {"Resolution", "Agreement", "Conclusion", "WorkingAssumption"}
CAP = 50_000_000


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def property_type(value):
    if isinstance(value, dict):
        return value["$neo4j"]
    if isinstance(value, list):
        return "list[" + ",".join(sorted({property_type(item) for item in value})) + "]"
    return type(value).__name__


def dependencies(root, contract, datasets):
    spec = importlib.util.spec_from_file_location("cq_dependency_guard", root / contract["guard"]["path"])
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)

    def projection_parts(value):
        depth, parts, start = 0, [], 0
        for index, character in enumerate(value):
            depth += character in "([{"
            depth -= character in ")] }".replace(" ", "")
            if character == "," and depth == 0:
                parts.append(value[start:index]); start = index + 1
        parts.append(value[start:])
        return parts

    def entity_reads(value, variables):
        """Conservatively find entity values left after explicit scalar uses.

        This is a dependency gate for the supported query forms, rather than a
        general Cypher parser. Unproven entity expressions require a reviewed
        projection instead of silently dropping their properties.
        """
        # A list generator binds an entity, while its body must project scalars.
        value = re.sub(r"\[\s*[A-Za-z_]\w*\s+IN\s+(?:nodes|relationships)\s*\(\s*[A-Za-z_]\w*\s*\)\s*\|",
                       "[", value, flags=re.I)
        # These functions consume identity/structure or return scalar values.
        # Mask complete balanced calls, including count(CASE ... entity END).
        scalar = re.compile(r"\b(?:count|labels|type|id|elementId|length|size|exists)\s*\(", re.I)
        while match := scalar.search(value):
            depth, end = 1, match.end()
            while end < len(value) and depth:
                depth += value[end] == "("
                depth -= value[end] == ")"
                end += 1
            if depth:
                raise ValueError("Unbalanced scalar expression needs an explicit projection proof")
            value = value[:match.start()] + " __scalar__ " + value[end:]
        for variable in sorted(variables, key=len, reverse=True):
            escaped = re.escape(variable)
            value = re.sub(rf"\b{escaped}\s*\.\s*`?[A-Za-z_]\w*`?", " __property__ ", value)
            value = re.sub(rf"\b{escaped}\s+IS\s+(?:NOT\s+)?NULL\b", " __presence__ ", value, flags=re.I)
        return {variable for variable in variables
                if re.search(rf"(?<![\w.]){re.escape(variable)}\b(?!\s*:)", value)}

    properties = {"specRelease"}
    consumption = []
    for item, questions in datasets:
        for cq in questions:
            syntax, _ = guard._query_syntax(cq["cypher"])
            key = f"{item['working_group']}/phase-{item['phase']}/{cq['id']}"
            identity_syntax = re.sub(r"\bid\(a\)\s*<\s*id\(b\)", "__preserved_relative_node_order__", syntax)
            if re.search(r"\b(?:keys|properties|id|elementId)\s*\(", identity_syntax, re.I):
                raise ValueError(f"Whole-property/identity access needs an explicit projection proof: {key}")
            variables = {m.group(1) for m in guard._NODE_AT.finditer(syntax) if m.group(1) and
                         (m.start() == 0 or not (syntax[m.start() - 1].isalnum() or syntax[m.start() - 1] == "_"))}
            variables.update(re.findall(r"\[\s*([A-Za-z_]\w*)\s*:", syntax))
            variables.update(re.findall(r"-\s*\[\s*([A-Za-z_]\w*)\b", syntax))
            variables.update(re.findall(r"\b([A-Za-z_]\w*)\s*=\s*(?:(?:shortestPath|allShortestPaths)\s*\()?\s*\(", syntax, re.I))
            if re.search(r"\(\s*`|-\s*\[\s*`", syntax):
                raise ValueError(f"Quoted graph variables need an explicit projection proof: {key}")
            variables.update(re.findall(r"\bUNWIND\s+(?:nodes|relationships)\s*\([^)]*\)\s+AS\s+([A-Za-z_]\w*)", syntax, re.I))
            variables.update(re.findall(r"\[\s*([A-Za-z_]\w*)\s+IN\s+(?:nodes|relationships)\s*\(", syntax, re.I))
            with_parts = [part.strip() for clause in re.finditer(
                r"\bWITH\b(.*?)(?=\b(?:MATCH|OPTIONAL|WHERE|RETURN|UNWIND|ORDER|SKIP|LIMIT|CALL|UNION|WITH)\b|$)",
                syntax, re.I | re.S) for part in projection_parts(clause.group(1))]
            # Propagate direct entity aliases and the supported collect(n)[i]
            # entity selection before checking dynamic access and RETURN values.
            changed = True
            while changed:
                changed = False
                for part in with_parts:
                    alias = re.search(r"\s+AS\s+([A-Za-z_]\w*)\s*$", part, re.I)
                    if not alias:
                        continue
                    value = re.sub(r"^DISTINCT\s+", "", part[:alias.start()].strip(), flags=re.I)
                    selected = re.fullmatch(r"collect\s*\(\s*(?:DISTINCT\s+)?([A-Za-z_]\w*)\s*\)\s*\[\s*\d+\s*\]", value, re.I)
                    source = selected.group(1) if selected else value
                    if source in variables and alias.group(1) not in variables:
                        variables.add(alias.group(1)); changed = True
            for variable in variables:
                escaped = re.escape(variable)
                if re.search(rf"\b{escaped}\s*\[", syntax):
                    raise ValueError(f"Dynamic graph property access needs an explicit dependency: {key}")
                if re.search(rf"\b{escaped}\s*\{{\s*\.", syntax):
                    raise ValueError(f"Whole-node map projection needs an explicit dependency: {key}")
                if re.search(rf"\bRETURN\s+(?:DISTINCT\s+)?{escaped}\s*(?:,|$|\bAS\b)", syntax, re.I):
                    raise ValueError(f"Whole graph entity return needs an explicit dependency: {key}")
            for part in with_parts:
                value = re.sub(r"\s+AS\s+\w+\s*$", "", part, flags=re.I)
                value = re.sub(r"^DISTINCT\s+", "", value, flags=re.I)
                selected = re.fullmatch(r"collect\s*\(\s*(?:DISTINCT\s+)?([A-Za-z_]\w*)\s*\)\s*\[\s*\d+\s*\]", value, re.I)
                if entity_reads(value, variables) and value not in variables and not (selected and selected.group(1) in variables):
                    raise ValueError(f"Whole graph entity projection in WITH needs an explicit dependency: {key}")
            for unwind in re.finditer(r"\bUNWIND\s+(.*?)\s+AS\s+[A-Za-z_]\w*", syntax, re.I | re.S):
                value = unwind.group(1).strip()
                if entity_reads(value, variables) and not re.fullmatch(r"(?:nodes|relationships)\s*\(\s*[A-Za-z_]\w*\s*\)", value, re.I):
                    raise ValueError(f"Whole graph entity UNWIND needs an explicit dependency: {key}")
            for clause in re.finditer(r"\bRETURN\b(.*?)(?=\b(?:ORDER|SKIP|LIMIT|WITH|UNION)\b|$)", syntax, re.I | re.S):
                for part in projection_parts(clause.group(1)):
                    value = re.sub(r"\s+AS\s+\w+\s*$", "", part.strip(), flags=re.I)
                    value = re.sub(r"^DISTINCT\s+", "", value, flags=re.I)
                    if value == "*" or entity_reads(value, variables):
                        raise ValueError(f"Whole graph entity return needs an explicit dependency: {key}")
            if re.search(r"\.\s*\*|\$[A-Za-z_]", syntax):
                raise ValueError(f"Wildcard/parameterized property access needs an explicit dependency: {key}")
            used = set(re.findall(r"\b[A-Za-z_]\w*\s*\.\s*`?([A-Za-z_]\w*)`?", syntax))
            used.update(re.findall(r"(?:\{|,)\s*`?([A-Za-z_]\w*)`?\s*:", syntax))
            properties.update(used)
            labels = defaultdict(set)
            for node in guard._NODE_AT.finditer(syntax):
                if node.group(1):
                    labels[node.group(1)].update(guard._labels(node.group(2)))
                if re.search(r"(?:\{|,)\s*`?(?:contentWithEquations|content)`?\s*:", node.group(0)):
                    if not set(guard._labels(node.group(2))).intersection(TEXT_LABELS):
                        raise ValueError(f"Text property map consumer has no proven Resolution-family label: {key}")
            for relationship in re.finditer(r"-\s*\[[^\]]*\]", syntax):
                if re.search(r"(?:\{|,)\s*`?(?:contentWithEquations|content)`?\s*:", relationship.group(0)):
                    raise ValueError(f"Relationship text property map needs an explicit projection proof: {key}")
            for variable, prop in re.findall(r"\b([A-Za-z_]\w*)\s*\.\s*`?(contentWithEquations|content)\b`?", syntax):
                if not labels[variable].intersection(TEXT_LABELS):
                    raise ValueError(f"Text property consumer has no proven Resolution-family label: {key}/{variable}.{prop}")
            consumption.append({"key": key, "query_sha256": hashlib.sha256(cq["cypher"].encode()).hexdigest(),
                                "properties": sorted(used)})
    return {"properties": sorted(properties), "text_properties": sorted(TEXT_PROPERTIES),
            "text_labels": sorted(TEXT_LABELS), "questions": consumption,
            "structure": "All nodes, all labels, all relationship occurrences, directions and properties consumed by queries/guards.",
            "property_rule": "Retain whitelisted properties globally; content/contentWithEquations apply to Resolution-family nodes. Relationship properties use the same whitelist.",
            "guard_dependencies": "Anchor values use query properties; schema warnings use original token inventories; Spec roles use every adjacent relationship and specRelease; remaining guards use query text and returned values.",
            "source_text": "Resolution report passages are source-derived text; source rights and provenance apply."}


def encode(value):
    from neo4j.time import Date, Time, DateTime, Duration
    from neo4j.spatial import Point
    if isinstance(value, (Date, Time, DateTime)):
        return {"$neo4j": type(value).__name__, "value": value.iso_format()}
    if isinstance(value, Duration):
        return {"$neo4j": "Duration", "months": value.months, "days": value.days,
                "seconds": value.seconds, "nanoseconds": value.nanoseconds}
    if isinstance(value, Point):
        return {"$neo4j": "Point", "srid": value.srid, "coordinates": list(value)}
    if isinstance(value, (bytes, bytearray)):
        return {"$neo4j": "Bytes", "hex": bytes(value).hex()}
    if isinstance(value, float) and not math.isfinite(value):
        return {"$neo4j": "Float", "value": repr(value)}
    if isinstance(value, list):
        return [encode(item) for item in value]
    if value is None or type(value) in (str, bool, int, float):
        return value
    raise TypeError(f"Unsupported Neo4j property type: {type(value).__name__}")


def decode(value):
    if isinstance(value, list):
        return [decode(item) for item in value]
    if not isinstance(value, dict):
        return value
    from neo4j.time import Date, Time, DateTime, Duration
    from neo4j.spatial import CartesianPoint, WGS84Point
    kind = value["$neo4j"]
    if kind in ("Date", "Time", "DateTime"):
        return {"Date": Date, "Time": Time, "DateTime": DateTime}[kind].from_iso_format(value["value"])
    if kind == "Duration":
        return Duration(**{key: value[key] for key in ("months", "days", "seconds", "nanoseconds")})
    if kind == "Point":
        point = (WGS84Point if value["srid"] in (4326, 4979) else CartesianPoint)(value["coordinates"])
        if point.srid != value["srid"]:
            raise ValueError("Unsupported point SRID")
        return point
    if kind == "Bytes":
        return bytes.fromhex(value["hex"])
    if kind == "Float":
        return float(value["value"])
    raise ValueError(f"Unknown encoded property type: {kind}")


def project(properties, labels, dependency):
    whitelist = set(dependency["properties"])
    keep_text = bool(set(labels).intersection(dependency["text_labels"]))
    return {key: encode(value) for key, value in properties.items()
            if key in whitelist and (key not in TEXT_PROPERTIES or keep_text)}


class Fingerprint:
    """Order-independent pair of full SHA-256 accumulators and record count."""
    def __init__(self):
        self.count = self.xor = self.total = 0

    def add(self, row):
        number = int.from_bytes(hashlib.sha256(canonical(row)).digest(), "big")
        self.count += 1
        self.xor ^= number
        self.total = (self.total + number) % (1 << 256)

    def value(self):
        return {"count": self.count, "sha256_xor": f"{self.xor:064x}", "sha256_sum": f"{self.total:064x}"}


class Shards:
    """Concatenated gzip members keep every compressed shard below the file cap."""
    def __init__(self, directory, prefix):
        self.directory, self.prefix = directory, prefix
        self.files, self.handle, self.size, self.index = [], None, 0, 0

    def write(self, rows):
        block = gzip.compress(b"".join(canonical(row) + b"\n" for row in rows), mtime=0)
        if len(block) >= CAP:
            if len(rows) == 1:
                raise ValueError("Single projected record exceeds compressed shard limit")
            middle = len(rows) // 2
            self.write(rows[:middle]); self.write(rows[middle:])
            return
        if self.handle is None or self.size + len(block) >= CAP:
            self.close_current()
            path = self.directory / f"{self.prefix}-{self.index:04d}.jsonl.gz"
            self.index += 1
            self.handle = path.open("wb")
            self.size = 0
        self.handle.write(block)
        self.size += len(block)

    def close_current(self):
        if self.handle is not None:
            path = Path(self.handle.name)
            self.handle.close()
            self.files.append({"path": path.name, "sha256": file_digest(path), "bytes": path.stat().st_size})
            self.handle = None


def schema(session, timeout):
    from neo4j import Query
    result = {}
    for key, query in [("labels", "CALL db.labels() YIELD label RETURN label AS value"),
                       ("relationship_types", "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType AS value"),
                       ("property_keys", "CALL db.propertyKeys() YIELD propertyKey RETURN propertyKey AS value")]:
        result[key] = sorted(row["value"] for row in session.run(Query(query, timeout=timeout)))
    return result


def counts(session, timeout):
    from neo4j import Query
    return {name: session.run(Query(query, timeout=timeout)).single()["n"] for name, query in [
        ("nodes", "MATCH (n) RETURN count(n) AS n"), ("relationships", "MATCH ()-[r]->() RETURN count(r) AS n")]}


def label_orders(session, timeout):
    from neo4j import Query
    return session.run(Query("MATCH (n) WITH labels(n) AS labels RETURN labels, count(*) AS nodes ORDER BY labels", timeout=timeout)).data()


def capture_label_order(connection, args):
    from neo4j import GraphDatabase, READ_ACCESS, Query
    directory = args.snapshot.resolve()
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    with GraphDatabase.driver(connection["uri"], auth=(connection["user"], os.environ[connection["password_env"]])) as driver:
        with driver.session(database=connection.get("database", "neo4j"), default_access_mode=READ_ACCESS) as session:
            observed = label_orders(session, args.timeout)
            source_order = [row["label"] for row in session.run(Query("CALL db.labels() YIELD label RETURN label", timeout=args.timeout))]
            repeated = label_orders(session, args.timeout)
    if observed != repeated or sum(row["nodes"] for row in observed) != manifest["before_counts"]["nodes"]:
        raise ValueError("Observed label populations changed or differ from snapshot")
    edges, degrees = defaultdict(set), {label: 0 for label in source_order}
    for row in observed:
        for left, right in zip(row["labels"], row["labels"][1:]):
            if right not in edges[left]:
                edges[left].add(right); degrees[right] += 1
    token_order = []
    while len(token_order) < len(degrees):
        ready = [label for label in source_order if degrees[label] == 0 and label not in token_order]
        if not ready:
            raise ValueError("Observed label orders have incompatible token-order constraints")
        selected = ready[0]
        token_order.append(selected)
        for target in edges[selected]:
            degrees[target] -= 1
    data = {"scope": "Repeated complete observed labels(n) population signatures used to preserve CQ-visible label order.",
            "working_group": args.working_group, "captured_utc": datetime.now(timezone.utc).isoformat(),
            "observed_signatures": observed, "token_creation_order": token_order}
    target = directory / "label_order.json"
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    manifest["label_order"] = {"path": target.name, "sha256": file_digest(target)}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"label_order_captured": args.working_group, "signatures": len(observed), "manifest_sha256": file_digest(manifest_path)}))


def token_probes(root, contract, datasets):
    spec = importlib.util.spec_from_file_location("cq_schema_token_guard", root / contract["guard"]["path"])
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    candidates = set()
    for _, questions in datasets:
        for question in questions:
            syntax, _ = guard._query_syntax(question["cypher"])
            candidates.update(re.findall(r"[:|]\s*`?([A-Za-z_]\w*)`?", syntax))
    return {"labels": sorted(candidates), "relationship_types": sorted(candidates),
            "property_keys": dependencies(root, contract, datasets)["properties"]}


def observe_schema_tokens(session, probes, timeout):
    from neo4j import Query
    unknown_codes = {"labels": "Neo.ClientNotification.Statement.UnknownLabelWarning",
                     "relationship_types": "Neo.ClientNotification.Statement.UnknownRelationshipTypeWarning",
                     "property_keys": "Neo.ClientNotification.Statement.UnknownPropertyKeyWarning"}
    observed = []
    for kind, names in probes.items():
        for name in names:
            query = {"labels": f"EXPLAIN MATCH (n:{ident(name)}) RETURN count(n) AS n",
                     "relationship_types": f"EXPLAIN MATCH ()-[r:{ident(name)}]->() RETURN count(r) AS n",
                     "property_keys": f"EXPLAIN MATCH (n) RETURN n.{ident(name)} AS value LIMIT 0"}[kind]
            notes = session.run(Query(query, timeout=timeout)).consume().notifications or []
            observed.append({"kind": kind, "name": name, "known": all(note.get("code") != unknown_codes[kind] for note in notes),
                             "notifications": [{"code": note.get("code"), "description": note.get("description")} for note in notes]})
    return observed


def capture_schema_tokens(root, contract, datasets, connection, args):
    from neo4j import GraphDatabase, READ_ACCESS
    directory = args.snapshot.resolve()
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    probes = token_probes(root, contract, datasets)
    with GraphDatabase.driver(connection["uri"], auth=(connection["user"], os.environ[connection["password_env"]])) as driver:
        with driver.session(database=connection.get("database", "neo4j"), default_access_mode=READ_ACCESS) as session:
            before = counts(session, args.timeout)
            observed = observe_schema_tokens(session, probes, args.timeout)
            repeated = observe_schema_tokens(session, probes, args.timeout)
            after = counts(session, args.timeout)
    if observed != repeated or before != after or before != manifest["before_counts"]:
        raise ValueError("Source schema observations/populations changed")
    result = {"format": "spectra-cq-schema-token-observations-1", "working_group": args.working_group,
              "scope": "Repeated read-only EXPLAIN observations of query-referenced names, including source-known tokens with empty current populations.",
              "captured_utc": datetime.now(timezone.utc).isoformat(), "snapshot_manifest_sha256": file_digest(manifest_path),
              "definition_contract": contract["definition_contract"], "source_counts": before,
              "probes": probes, "observations": observed, "repeated_probes_match": True,
              "known_tokens": {kind: [row["name"] for row in observed if row["kind"] == kind and row["known"]]
                               for kind in probes}}
    path = directory / "schema_token_observations.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"schema_tokens_captured": args.working_group,
                      "known_token_counts": {kind: len(values) for kind, values in result["known_tokens"].items()}}), flush=True)


def export_pass(session, dependency, timeout, output=None):
    from neo4j import Query
    fingerprints = {}
    queries = {
        "nodes": "MATCH (n) RETURN elementId(n) AS id, id(n) AS source_order, labels(n) AS labels, properties(n) AS properties ORDER BY source_order",
        "relationships": "MATCH (a)-[r]->(b) RETURN elementId(r) AS id, elementId(a) AS start, elementId(b) AS end, type(r) AS type, properties(r) AS properties"}
    for kind, query in queries.items():
        fingerprint, batch = Fingerprint(), []
        shards = Shards(output, kind) if output is not None else None
        tx = session.begin_transaction(timeout=timeout)
        try:
            for record in tx.run(query):
                row = record.data()
                if kind == "nodes":
                    row["labels"] = sorted(row["labels"])
                    row["properties"] = project(row["properties"], row["labels"], dependency)
                else:
                    row["properties"] = project(row["properties"], (), dependency)
                fingerprint.add(row)
                if shards:
                    batch.append(row)
                    if len(batch) == 1000:
                        shards.write(batch); batch = []
            if batch:
                shards.write(batch)
        finally:
            tx.rollback()
            if shards:
                shards.close_current()
        fingerprints[kind] = {"fingerprint": fingerprint.value()}
        if shards:
            fingerprints[kind]["files"] = shards.files
        print(json.dumps({"stage": "export" if output else "stability_read", "kind": kind, "count": fingerprint.count}), flush=True)
    return fingerprints


def export(root, contract, datasets, summary, connection, args):
    from neo4j import GraphDatabase, READ_ACCESS
    dependency = dependencies(root, contract, datasets)
    destination = args.output / args.working_group
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Snapshot output must be empty; preserve prior runs separately")
    destination.mkdir(parents=True, exist_ok=True)
    metadata = {"format": "spectra-cq-view-1", "working_group": args.working_group,
                "started_utc": datetime.now(timezone.utc).isoformat(), "cq_contract_sha256": summary["contract_sha256"],
                "dependency": dependency, "historical_graph_identity": "unrecorded; this is a separately captured current graph view"}
    with GraphDatabase.driver(connection["uri"], auth=(connection["user"], os.environ[connection["password_env"]])) as driver:
        with driver.session(database=connection.get("database", "neo4j"), default_access_mode=READ_ACCESS,
                            fetch_size=1000) as session:
            metadata["before_counts"] = counts(session, args.timeout)
            metadata["schema_tokens"] = schema(session, args.timeout)
            if (HELPER_LABEL in metadata["schema_tokens"]["labels"] or
                    {HELPER_KEY, ORDER_KEY}.intersection(metadata["schema_tokens"]["property_keys"])):
                raise ValueError("Source already uses reserved snapshot helper names")
            metadata["records"] = export_pass(session, dependency, args.timeout, destination)
            second = export_pass(session, dependency, args.timeout)
            metadata["after_counts"] = counts(session, args.timeout)
            metadata["after_schema_tokens"] = schema(session, args.timeout)
    stable = (metadata["before_counts"] == metadata["after_counts"] and metadata["schema_tokens"] == metadata["after_schema_tokens"] and
              all(metadata["records"][kind]["fingerprint"] == second[kind]["fingerprint"] for kind in second) and
              all(metadata["records"][kind]["fingerprint"]["count"] == metadata["before_counts"][kind] for kind in second))
    metadata["consistency"] = {"repeated_content_fingerprints_match": stable,
                               "isolation": "Sequential read transactions with complete repeated content fingerprints and before/after counts; concurrent writes invalidate reuse when detected."}
    metadata["finished_utc"] = datetime.now(timezone.utc).isoformat()
    (destination / "manifest.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    if not stable:
        raise ValueError("Graph view changed during capture; discard this snapshot as an execution input")
    print(json.dumps({"snapshot": str(destination), "manifest_sha256": file_digest(destination / "manifest.json"),
                      "counts": metadata["before_counts"], "compressed_bytes": sum(f["bytes"] for record in metadata["records"].values() for f in record["files"])}))


def read_records(directory, record):
    for artifact in record["files"]:
        path = (directory / artifact["path"]).resolve()
        if not path.is_relative_to(directory.resolve()) or path.stat().st_size != artifact["bytes"] or file_digest(path) != artifact["sha256"]:
            raise ValueError("Snapshot shard path, size or digest differs")
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                yield json.loads(line)


def ident(value):
    return "`" + value.replace("`", "``") + "`"


def restore(root, contract, datasets, connection, args):
    from neo4j import GraphDatabase, Query
    directory = args.snapshot.resolve()
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    selected_view = next((view for view in contract["graph_views"]
                          if view["working_group"] == args.working_group), None)
    if (selected_view is None or (root / selected_view["manifest_path"]).resolve() != manifest_path or
            file_digest(manifest_path) != selected_view["manifest_sha256"]):
        raise ValueError("Restore requires the selected graph manifest pinned by the definition sidecar")
    if manifest["dependency"] != dependencies(root, contract, datasets):
        raise ValueError("Snapshot dependency projection differs from current definitions/guard")
    binding = json.loads((root / selected_view["definition_binding_path"]).read_text())
    observation = json.loads((root / binding["schema_token_observations"]["path"]).read_text())
    if observation["probes"] != token_probes(root, contract, datasets):
        raise ValueError("Schema token probes differ from current query dependencies")
    if manifest["format"] != "spectra-cq-view-1" or not manifest["consistency"]["repeated_content_fingerprints_match"]:
        raise ValueError("Snapshot format/consistency check failed")
    if manifest["working_group"] != args.working_group:
        raise ValueError("Snapshot working group differs from the selected target")
    label_binding = manifest["label_order"]
    label_path = (directory / label_binding["path"]).resolve()
    if not label_path.is_relative_to(directory) or file_digest(label_path) != label_binding["sha256"]:
        raise ValueError("Label-order contract digest/path differs")
    label_contract = json.loads(label_path.read_text())
    fingerprints, input_types = {}, {}
    for kind, record in manifest["records"].items():
        fp, types = Fingerprint(), Counter()
        for row in read_records(directory, record):
            fp.add(row)
            types.update(f"{key}:{property_type(value)}" for key, value in row["properties"].items())
        if fp.value() != record["fingerprint"]:
            raise ValueError(f"Snapshot logical content differs: {kind}")
        fingerprints[kind] = fp.value()
        input_types[kind] = dict(types)
    if not args.confirm_empty_target:
        raise ValueError("Restore requires --confirm-empty-target and a dedicated scratch database")
    with GraphDatabase.driver(connection["uri"], auth=(connection["user"], os.environ[connection["password_env"]])) as driver:
        with driver.session(database=connection.get("database", "neo4j")) as session:
            initial = counts(session, args.timeout)
            if any(initial.values()):
                raise ValueError("Restore target contains graph records; choose an empty scratch database")
            session.run(f"CREATE CONSTRAINT spectra_cq_source_id FOR (n:{ident(HELPER_LABEL)}) REQUIRE n.{ident(HELPER_KEY)} IS UNIQUE").consume()
            order_seed_id = session.run("CREATE (n) RETURN elementId(n) AS id").single()["id"]
            for label in label_contract["token_creation_order"]:
                session.run(f"MATCH (n) WHERE elementId(n)=$id SET n:{ident(label)}", id=order_seed_id).consume()
            def write_batch(kind, rows):
                groups = defaultdict(list)
                if kind == "nodes":
                    prepared = [{**row, "properties": {key: decode(value) for key, value in row["properties"].items()}}
                                for row in rows]
                    session.run(Query(f"UNWIND $rows AS row WITH row ORDER BY row.source_order "
                                      f"CREATE (n:{ident(HELPER_LABEL)}) SET n = row.properties, "
                                      f"n.{ident(HELPER_KEY)} = row.id, n.{ident(ORDER_KEY)} = row.source_order", timeout=args.timeout),
                                rows=prepared).consume()
                for row in rows:
                    row = dict(row)
                    row["properties"] = {key: decode(value) for key, value in row["properties"].items()}
                    groups[tuple(row["labels"]) if kind == "nodes" else row["type"]].append(row)
                for group, batch in groups.items():
                    if kind == "nodes":
                        for label in group:
                            query = (f"UNWIND $rows AS row MATCH (n:{ident(HELPER_LABEL)} {{{ident(HELPER_KEY)}:row.id}}) "
                                     f"SET n:{ident(label)}")
                            session.run(Query(query, timeout=args.timeout), rows=batch).consume()
                        continue
                    else:
                        query = (f"UNWIND $rows AS row MATCH (a:{ident(HELPER_LABEL)} {{{ident(HELPER_KEY)}:row.start}}), "
                                 f"(b:{ident(HELPER_LABEL)} {{{ident(HELPER_KEY)}:row.end}}) "
                                 f"CREATE (a)-[r:{ident(group)}]->(b) SET r = row.properties, r.{ident(HELPER_KEY)} = row.id")
                    session.run(Query(query, timeout=args.timeout), rows=batch).consume()
            for kind in ("nodes", "relationships"):
                batch = []
                for row in read_records(directory, manifest["records"][kind]):
                    batch.append(row)
                    if len(batch) == 1000:
                        write_batch(kind, batch); batch = []
                if batch:
                    write_batch(kind, batch)
                print(json.dumps({"stage": "restore", "kind": kind, "count": fingerprints[kind]["count"]}), flush=True)
            actual_fingerprints = {}
            restored_queries = {
                "nodes": (f"MATCH (n:{ident(HELPER_LABEL)}) RETURN n.{ident(HELPER_KEY)} AS id, "
                          f"n.{ident(ORDER_KEY)} AS source_order, labels(n) AS labels, properties(n) AS properties"),
                "relationships": (f"MATCH (a:{ident(HELPER_LABEL)})-[r]->(b:{ident(HELPER_LABEL)}) "
                                  f"RETURN r.{ident(HELPER_KEY)} AS id, a.{ident(HELPER_KEY)} AS start, "
                                  f"b.{ident(HELPER_KEY)} AS end, type(r) AS type, properties(r) AS properties")}
            for kind, query in restored_queries.items():
                actual = Fingerprint()
                for record in session.run(Query(query, timeout=args.timeout)):
                    row = record.data()
                    if kind == "nodes":
                        row["labels"] = sorted(label for label in row["labels"] if label != HELPER_LABEL)
                    row["properties"] = {key: encode(value) for key, value in row["properties"].items()
                                         if key not in (HELPER_KEY, ORDER_KEY)}
                    actual.add(row)
                actual_fingerprints[kind] = actual.value()
                if actual.value() != fingerprints[kind]:
                    raise ValueError(f"Actual restored projected content differs from input: {kind}")
                print(json.dumps({"stage": "restored_content_verified", "kind": kind, "count": actual.count}), flush=True)
            prior_source = prior_target = -1
            order_checked = 0
            for row in session.run(Query(f"MATCH (n:{ident(HELPER_LABEL)}) RETURN n.{ident(ORDER_KEY)} AS source_order, "
                                         "id(n) AS target_order ORDER BY source_order", timeout=args.timeout)):
                if row["source_order"] <= prior_source or row["target_order"] <= prior_target:
                    raise ValueError("Source relative node ID order was not preserved")
                prior_source, prior_target = row["source_order"], row["target_order"]
                order_checked += 1
            # Retain source token inventories, including optional properties/types with empty populations.
            tokens = {kind: sorted(set(manifest["schema_tokens"][kind]) | set(observation["known_tokens"][kind]))
                      for kind in manifest["schema_tokens"]}
            label_text = ":".join(ident(label) for label in tokens["labels"])
            seed = session.run(f"CREATE (n:{label_text}) SET n = $properties RETURN elementId(n) AS id",
                               properties={key: "" for key in tokens["property_keys"]}).single()["id"]
            for relationship_type in tokens["relationship_types"]:
                session.run(f"MATCH (n) WHERE elementId(n)=$id CREATE (n)-[:{ident(relationship_type)}]->(n)", id=seed).consume()
            session.run("MATCH (n) WHERE elementId(n)=$id DETACH DELETE n", id=seed).consume()
            session.run("MATCH (n) WHERE elementId(n)=$id DELETE n", id=order_seed_id).consume()
            session.run(Query(f"MATCH ()-[r]->() CALL {{ WITH r REMOVE r.{ident(HELPER_KEY)} }} "
                              "IN TRANSACTIONS OF 10000 ROWS RETURN count(*) AS n", timeout=args.timeout)).consume()
            session.run(Query(f"MATCH (n:{ident(HELPER_LABEL)}) CALL {{ WITH n REMOVE n.{ident(HELPER_KEY)}, "
                              f"n.{ident(ORDER_KEY)}, n:{ident(HELPER_LABEL)} }} "
                              "IN TRANSACTIONS OF 10000 ROWS RETURN count(*) AS n", timeout=args.timeout)).consume()
            session.run("DROP CONSTRAINT spectra_cq_source_id").consume()
            final = counts(session, args.timeout)
            if final != manifest["before_counts"]:
                raise ValueError("Restored graph population differs")
            actual_label_orders = label_orders(session, args.timeout)
            if actual_label_orders != label_contract["observed_signatures"]:
                raise ValueError("Restored CQ-visible labels(n) order/populations differ")
            actual_schema = observe_schema_tokens(session, observation["probes"], args.timeout)
            schema_signature = lambda rows: [{key: row[key] for key in ("kind", "name", "known")} for row in rows]
            if schema_signature(actual_schema) != schema_signature(observation["observations"]):
                raise ValueError("Restored query-visible schema token observations differ")
    receipt = {"scope": "Fresh restoration of the CQ view into an initially empty target.",
               "snapshot_manifest_sha256": file_digest(directory / "manifest.json"),
               "definition_contract": contract["definition_contract"],
               "schema_token_observations": binding["schema_token_observations"],
               "schema_token_probes_checked": len(actual_schema),
               "initial_counts": initial, "restored_counts": final, "verified_input_fingerprints": fingerprints,
               "actual_restored_fingerprints": actual_fingerprints,
               "input_property_types": input_types,
               "source_relative_node_order_checked": order_checked,
               "observed_label_order_signatures_checked": actual_label_orders,
               "next_check": "Execute original and restored graph CQs and compare all outcomes, row counts and guard defects."}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / f"{manifest['working_group']}-restore.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("dependencies", "export", "restore", "label-order", "schema-tokens"))
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--connections", type=Path)
    parser.add_argument("--working-group", choices=[f"RAN{wg}" for wg in range(1, 6)])
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--confirm-empty-target", action="store_true")
    args = parser.parse_args()
    contract, datasets, summary = verify(args.release.resolve())
    if args.mode == "dependencies":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(dependencies(args.release.resolve(), contract, datasets), indent=2) + "\n")
        return
    if not args.connections or not args.working_group:
        parser.error("export/restore require --connections and --working-group")
    connection = json.loads(args.connections.read_text())[args.working_group]
    if args.mode == "export":
        export(args.release.resolve(), contract, datasets, summary, connection, args)
    elif args.mode == "schema-tokens":
        if not args.snapshot:
            parser.error("schema-tokens requires --snapshot")
        capture_schema_tokens(args.release.resolve(), contract, datasets, connection, args)
    elif args.mode == "label-order":
        if not args.snapshot:
            parser.error("label-order requires --snapshot")
        capture_label_order(connection, args)
    else:
        if not args.snapshot:
            parser.error("restore requires --snapshot")
        restore(args.release.resolve(), contract, datasets, connection, args)


if __name__ == "__main__":
    main()
