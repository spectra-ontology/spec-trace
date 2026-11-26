#!/usr/bin/env python3
"""Replay preserved first queries against explicitly supplied native databases.

Offline scores are checked first. Fresh executions are written to a separate
receipt; original queries, execution records, and analysis stay unchanged.
SQL uses the standard library. Cypher additionally requires the neo4j driver.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import logging
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
GROUPS = tuple(f"RAN{i}" for i in range(1, 6))


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def rowset(rows):
    return None if rows is None else {tuple(row) for row in rows}


class SqlInputs:
    def __init__(self, args, matched):
        require(sqlite3.sqlite_version == "3.37.2", "SQLite 3.37.2 is required; found " + sqlite3.sqlite_version)
        require(args.sqlite_dir is not None, "--sqlite-dir is required for SQL")
        protocol = load(matched / "frozen/protocol.json")
        self.connections, self.paths, self.hashes = {}, {}, {}
        try:
            for wg in GROUPS:
                path = (args.sqlite_dir / (wg + ".sqlite")).resolve()
                require(path.is_file(), "SQLite export is missing: " + wg)
                self.paths[wg] = path
                self.hashes[wg] = digest(path)
                require(self.hashes[wg] == protocol["databases"][wg]["sqliteSha256"], "SQLite input hash differs: " + wg)
                db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
                self.connections[wg] = db
                db.execute("PRAGMA query_only=ON")
                require(db.execute("PRAGMA query_only").fetchone()[0] == 1, "query_only check failed: " + wg)
        except Exception:
            self.close()
            raise
        self.metadata = {"sqliteVersion": sqlite3.sqlite_version, "mode": "ro", "queryOnly": True,
                         "databaseSha256": self.hashes}

    def execute(self, wg, query, started):
        require(re.match(r"\s*(SELECT|WITH)\b", query, re.I), "SQL must start with SELECT/WITH")
        db = self.connections[wg]
        db.set_progress_handler(lambda: int(time.monotonic() - started > 60), 10000)
        try:
            cursor = db.execute(query)
            fields = [column[0] for column in cursor.description]
            found = cursor.fetchmany(2001)
            return fields, found
        finally:
            db.set_progress_handler(None, 0)

    def close(self):
        for db in self.connections.values():
            db.close()
        self.connections.clear()

    def verify_unchanged(self):
        after = {wg: digest(path) for wg, path in self.paths.items()}
        require(after == self.hashes, "SQLite export changed during replay")
        return {"databaseHashesUnchanged": True}


class CypherInputs:
    def __init__(self, args, matched):
        from neo4j import GraphDatabase, READ_ACCESS
        self.read_access = READ_ACCESS
        require(args.graph_identity, "--graph-identity is required for Cypher")
        endpoints = {}
        for value in args.bolt:
            wg, sep, uri = value.partition("=")
            require(sep and wg in GROUPS and wg not in endpoints, "Supply one --bolt RANn=URI per WG")
            parsed = urlsplit(uri)
            require(parsed.scheme in {"bolt", "bolt+s", "bolt+ssc", "neo4j", "neo4j+s", "neo4j+ssc"}
                    and parsed.hostname and parsed.username is None and parsed.password is None,
                    "Bolt URI must contain a host and use environment credentials")
            endpoints[wg] = uri
        selected = (args.working_group,) if args.working_group else GROUPS
        require(set(selected).issubset(endpoints), "Cypher requires a --bolt mapping for each selected WG")
        user = os.environ.get(args.neo4j_user_env)
        password = os.environ.get(args.neo4j_password_env)
        require(user is not None and password is not None, "Set the selected Neo4j credential environment variables")
        logging.getLogger("neo4j").setLevel(logging.CRITICAL)
        self.connections, self.before = {}, {}
        try:
            for wg in selected:
                driver = GraphDatabase.driver(endpoints[wg], auth=(user, password), connection_timeout=5,
                                              max_transaction_retry_time=0)
                self.connections[wg] = driver
                with driver.session(default_access_mode=READ_ACCESS, database=args.neo4j_database) as session:
                    with session.begin_transaction(timeout=60) as tx:
                        components = [dict(r) for r in tx.run("CALL dbms.components() YIELD versions RETURN versions")]
                        require(any("5.26.0" in r["versions"] for r in components), "Neo4j 5.26.0 is required: " + wg)
                        keys = tx.run("MATCH (n:DecisionDisposition) RETURN count(n) AS n, count(n.assessmentMethod) AS scoped").single()
                        require(keys["scoped"] > 0, "Native assessmentMethod input is required: " + wg)
                        meetings = tx.run("MATCH (m:Meeting) RETURN count(m.workingGroup) AS groups").single()
                        require(meetings["groups"] > 0, "Native Meeting.workingGroup input is required: " + wg)
                        self.before[wg] = self.inventory(tx)
                        tx.rollback()
        except Exception:
            self.close()
            raise
        self.database = args.neo4j_database
        self.metadata = {"neo4jVersion": "5.26.0", "graphIdentity": args.graph_identity,
                         "endpoints": {wg: endpoints[wg] for wg in selected},
                         "database": self.database, "accessMode": "READ",
                         "transactionPolicy": "explicit rollback", "beforePopulation": self.before,
                         "inputIdentity": "user-declared native graph; per-query stored-row comparison below"}

    @staticmethod
    def inventory(tx):
        nodes = tx.run("MATCH (n) RETURN count(n) AS n").single()["n"]
        edges = tx.run("MATCH ()-[r]->() RETURN count(r) AS n").single()["n"]
        return {"nodes": nodes, "relationships": edges}

    def execute(self, wg, query, started):
        syntax = re.sub(r"'(?:[^'\\]|\\.)*'", "''", query)
        require(not re.search(r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|LOAD|CALL)\b", syntax, re.I),
                "Disallowed Cypher write/procedure clause")
        with self.connections[wg].session(default_access_mode=self.read_access, database=self.database) as session:
            with session.begin_transaction(timeout=60) as tx:
                result = tx.run(query)
                fields = list(result.keys())
                found = [list(record.values()) for record in result]
                tx.rollback()
        return fields, found

    def verify_unchanged(self):
        after = {}
        for wg, driver in self.connections.items():
            with driver.session(default_access_mode=self.read_access, database=self.database) as session:
                with session.begin_transaction(timeout=60) as tx:
                    after[wg] = self.inventory(tx)
                    tx.rollback()
        require(after == self.before, "Graph population changed during replay")
        return {"afterPopulation": after, "graphPopulationUnchanged": True,
                "populationCheckScope": "node/relationship counts; content equality is checked through stored query rows"}

    def close(self):
        for driver in self.connections.values():
            driver.close()
        self.connections.clear()


def replay(args):
    study = args.study.resolve()
    matched = (args.matched_study or study.parent / "matched_domains").resolve()
    require(matched.is_dir(), "Keep studies/matched_domains beside this study or pass --matched-study")
    # The public checker validates frozen inputs, preserved query bytes, stored
    # rows, gold, first-write dispositions, and analysis before database access.
    verified = subprocess.run([sys.executable, "-B", str(study / "analyze.py"), "--check"],
                              text=True, capture_output=True)
    require(verified.returncode == 0, "Offline input/score verification failed: " + verified.stderr[-2000:])
    module_spec = importlib.util.spec_from_file_location("matched_native_replay_scorer", matched / "rescore.py")
    scorer = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(scorer)
    analysis = load(study / "analysis.json")
    gold = {scorer.packet_id(item): item for item in load(matched / "gold/selected_items.json")}
    kept = set(load(matched / "evidence/meeting_identity_source.json")["rules"]["keptElectronicSpellings"])
    report = {"receiptKind": "fresh_native_query_replay", "startedUtc": datetime.now(timezone.utc).isoformat(),
              "language": args.language, "replayScriptSha256": digest(Path(__file__)),
              "originalAnalysisSha256": digest(study / "analysis.json"),
              "offlineVerification": "pass", "timeoutSeconds": 60, "rowCap": 2000,
              "workingGroups": [args.working_group] if args.working_group else list(GROUPS),
              "columnPolicy": "exact requested field count", "skippedFirstBatches": [], "items": []}
    source = SqlInputs(args, matched) if args.language == "sql" else CypherInputs(args, matched)
    report["inputs"] = source.metadata
    try:
        for rid, run in analysis["runs"].items():
            if run["language"] != args.language:
                continue
            if run["nativeQueriesExecuted"] == 0:
                unanswered = run["missingFirstQueries"] if args.working_group is None else run["missingFirstQueries"] // 5
                report["skippedFirstBatches"].append({"runId": rid, "unanswered": unanswered,
                                                     "outputAssemblyViolation": run["outputAssemblyViolation"]})
                continue
            folder = study / "submissions" / rid
            commitment = load(folder / "commitment.json")
            query_path = folder / commitment["queryFile"]
            require(digest(query_path) == commitment["querySha256"], "Original query-file hash differs: " + rid)
            queries = [json.loads(line) for line in query_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            stored = load(study / "execution" / rid / "scoring_only" / (args.language + "_" + run["repetition"] + ".json"))
            require(len(queries) == len(stored) == 50, "Expected 50 original queries: " + rid)
            for query_record, historical in zip(queries, stored):
                query, pid = query_record["query"], query_record["id"]
                require(pid == historical["packetId"] and query == historical["query"], "Query bytes/order differ: " + rid)
                item = gold[pid]
                if args.working_group and item["wg"] != args.working_group:
                    continue
                started = time.monotonic()
                rows, error, blocked = None, None, False
                try:
                    fields, found = source.execute(item["wg"], query, started)
                    require(len(found) <= 2000, "Output exceeds historic 2000-row cap")
                    require(len(fields) == len(item["fields"]), "Wrong column count: " + str(fields))
                    rows = [[None if cell is None else str(cell) for cell in row] for row in found]
                except Exception as exc:
                    error = str(exc)[:1200]
                    blocked = "ServiceUnavailable" in type(exc).__name__ or "AuthError" in type(exc).__name__
                metrics = scorer.score(item["gold"], rows)
                identity = scorer.score(scorer.identity_rows(item, item["gold"], kept),
                                        scorer.identity_rows(item, rows, kept))
                same = (not blocked and rowset(rows) == rowset(historical["rows"])
                        and error == historical["error"] and metrics == historical["scores"]
                        and identity == historical["identityScores"])
                report["items"].append({"runId": rid, "packetId": pid, "wg": item["wg"],
                                        "querySha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
                                        "rows": rows, "error": error, "blocked": blocked,
                                        "elapsedSeconds": time.monotonic() - started, "scores": metrics,
                                        "identityScores": identity, "storedRowsetAndScoresEqual": same,
                                        "storedErrorTextEqual": error == historical["error"],
                                        "historicalExecutionError": bool(historical["error"])})
        report.update(source.verify_unchanged())
    finally:
        source.close()
    report["queriesReexecuted"] = len(report["items"])
    report["matchingStoredOutcomes"] = sum(row["storedRowsetAndScoresEqual"] for row in report["items"])
    report["expectedExecutionErrorsReproduced"] = sum(row["historicalExecutionError"] and row["storedRowsetAndScoresEqual"]
                                                       for row in report["items"])
    report["status"] = "pass" if report["matchingStoredOutcomes"] == report["queriesReexecuted"] else "mismatch"
    report["finishedUtc"] = datetime.now(timezone.utc).isoformat()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", required=True, choices=("sql", "cypher"))
    parser.add_argument("--working-group", choices=GROUPS, help="Replay only this WG; default replays all five")
    parser.add_argument("--study", type=Path, default=HERE)
    parser.add_argument("--matched-study", type=Path)
    parser.add_argument("--sqlite-dir", type=Path)
    parser.add_argument("--bolt", action="append", default=[], metavar="RANn=URI")
    parser.add_argument("--neo4j-user-env", default="NEO4J_USER")
    parser.add_argument("--neo4j-password-env", default="NEO4J_PASSWORD")
    parser.add_argument("--neo4j-database", default="neo4j")
    parser.add_argument("--graph-identity", help="Identity/provenance of the explicitly supplied native graph")
    parser.add_argument("--out", type=Path, required=True, help="New receipt outside the preserved study directory")
    args = parser.parse_args()
    require(not args.out.resolve().is_relative_to(args.study.resolve()), "Write fresh receipts outside the preserved study")
    require(not args.out.exists(), "Receipt already exists; choose a new --out")
    try:
        report = replay(args)
    except Exception as exc:
        report = {"receiptKind": "fresh_native_query_replay", "status": "input_or_runtime_error",
                  "language": args.language, "errorType": type(exc).__name__, "error": str(exc)[:2000]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({key: value for key, value in report.items() if key in
                      {"status", "language", "queriesReexecuted", "matchingStoredOutcomes", "expectedExecutionErrorsReproduced", "errorType", "error"}}))
    return 0 if report["status"] == "pass" else (1 if report["status"] == "mismatch" else 2)


if __name__ == "__main__":
    sys.exit(main())
