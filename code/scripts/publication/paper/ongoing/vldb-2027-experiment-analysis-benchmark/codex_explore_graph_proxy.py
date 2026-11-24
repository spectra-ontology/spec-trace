"""읽기 전용 탐색 조건에서 질의 작성자가 그래프에 읽기 질의를 보내는 중계 서버.

작업 폴더의 도우미(`query_graph.py`)는 접속 정보 없이 이 서버의 localhost 포트로 질의 한 줄만 보낸다. 접속 정보는 이
서버만 가지며, 질의마다 세 겹으로 쓰기를 막는다.

1. 문자열 · 주석을 지운 질의에 쓰기 · 관리 절(CREATE · MERGE · DELETE · SET · REMOVE · DROP · LOAD CSV · FOREACH ·
   USE · 절차 호출 CALL · IN TRANSACTIONS 등)이 있거나 문장이 둘 이상이면 실행하지 않고 거부한다.
2. 남은 질의는 READ 접근 방식 세션의 읽기 트랜잭션에서 실행하므로 쓰기는 서버가 다시 거부한다.
3. 질의마다 실행 시간 상한을 두고, 결과는 평가 실행기와 같은 방식(칸마다 str, 없음은 null)으로 바꾸어 상한 행까지만
   돌려준다. 상한을 넘으면 `truncated` 를 참으로 둔다.

받은 질의는 모두 기록 파일에 한 줄씩 남긴다(시각 · 질의 · 결과 상태 · 행 수 · 걸린 시간).

사용: python3 codex_explore_graph_proxy.py --bolt bolt://localhost:7687 --port 47687 --log <jsonl> \
          [--max-rows 2000] [--timeout 60]
저장소 루트에서 `PYTHONPATH=scripts/common` 으로 실행한다. 종료는 SIGTERM 이나 SIGINT 로 한다.
"""
from __future__ import annotations

import argparse
import json
import re
import signal
import socketserver
import threading
import time
from pathlib import Path

from neo4j import GraphDatabase, unit_of_work

from common.credentials import neo4j_auth

FORBIDDEN = re.compile(
    r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|ALTER|RENAME|GRANT|DENY|REVOKE|LOAD|FOREACH|USE|"
    r"START|STOP|TERMINATE|ENABLE|DISABLE|IMPORT|TRANSACTIONS|SHOW|DBMS|APOC|GDS)\b", re.I)
PROCEDURE_CALL = re.compile(r"\bCALL\s+(?![({])", re.I)
STRINGS = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|`(?:[^`]|``)*`")
COMMENTS = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)


def rejection(cypher: str) -> str | None:
    """실행 전에 거부할 이유. 문자열 · 이름 따옴표 · 주석을 먼저 지워서 그 안의 낱말은 보지 않는다."""
    bare = COMMENTS.sub(" ", STRINGS.sub("''", cypher))
    if not bare.strip():
        return "empty query"
    if ";" in bare.strip().rstrip(";"):
        return "more than one statement"
    found = FORBIDDEN.search(bare)
    if found:
        return f"write or administration keyword not allowed: {found.group(0)}"
    if PROCEDURE_CALL.search(bare):
        return "procedure calls are not allowed (CALL subqueries with { or ( are allowed)"
    return None


class Handler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        started = time.time()
        line = self.rfile.readline(1 << 22)
        try:
            cypher = json.loads(line)["cypher"]
            if not isinstance(cypher, str):
                raise TypeError("cypher must be a string")
        except Exception as error:  # 형식이 틀린 요청은 실행하지 않는다
            reply = {"error": f"bad request: {error}"}
            self.server.record({"status": "bad_request", "raw": line[:2000].decode("utf-8", "replace")}, started)
            self.wfile.write((json.dumps(reply) + "\n").encode())
            return
        cypher = cypher.strip().rstrip(";")
        why = rejection(cypher)
        if why:
            reply = {"error": f"rejected: {why}"}
            self.server.record({"status": "rejected", "cypher": cypher, "reason": why}, started)
        else:
            reply = self.server.execute(cypher)
            self.server.record({"status": "error" if "error" in reply else "ok", "cypher": cypher,
                                **({"error": reply["error"]} if "error" in reply else
                                   {"rowCount": reply["rowCount"], "truncated": reply["truncated"]})}, started)
        self.wfile.write((json.dumps(reply, ensure_ascii=False) + "\n").encode())


class Proxy(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, port: int, bolt: str, log: Path, max_rows: int, timeout: float):
        super().__init__(("127.0.0.1", port), Handler)
        self.driver = GraphDatabase.driver(bolt, auth=neo4j_auth())
        self.log, self.max_rows, self.timeout = log, max_rows, timeout
        self.lock = threading.Lock()

    def execute(self, cypher: str) -> dict:
        try:
            with self.driver.session(default_access_mode="READ") as session:
                @unit_of_work(timeout=self.timeout)
                def work(tx):
                    result = tx.run(cypher)
                    columns = list(result.keys())
                    rows = []
                    for record in result:
                        rows.append([None if cell is None else str(cell) for cell in record.values()])
                        if len(rows) > self.max_rows:
                            break
                    result.consume()
                    return columns, rows
                columns, rows = session.execute_read(work)
        except Exception as error:  # 서버 오류 문구를 그대로 돌려준다
            return {"error": str(error)[:1000]}
        truncated = len(rows) > self.max_rows
        return {"columns": columns, "rows": rows[:self.max_rows], "rowCount": min(len(rows), self.max_rows),
                "truncated": truncated}

    def record(self, entry: dict, started: float) -> None:
        entry = {"at": round(started, 3), "seconds": round(time.time() - started, 3), **entry}
        with self.lock, self.log.open("a") as out:
            out.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--bolt", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--max-rows", type=int, default=2000, help="평가 실행기가 남기는 행 상한과 같은 값")
    parser.add_argument("--timeout", type=float, default=60, help="평가 실행기의 질의당 시간 상한과 같은 값(초)")
    args = parser.parse_args()
    args.log.parent.mkdir(parents=True, exist_ok=True)
    proxy = Proxy(args.port, args.bolt, args.log, args.max_rows, args.timeout)
    stop = lambda *_: threading.Thread(target=proxy.shutdown, daemon=True).start()
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    print(json.dumps({"listening": f"127.0.0.1:{args.port}", "bolt": args.bolt, "maxRows": args.max_rows,
                      "timeout": args.timeout}), flush=True)
    try:
        proxy.serve_forever()
    finally:
        proxy.driver.close()
        proxy.server_close()


if __name__ == "__main__":
    main()
