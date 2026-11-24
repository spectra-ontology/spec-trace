"""추적 사슬 문항을 이 호스트의 모델로 풀게 하고 응답을 그대로 저장한다 (과금 API 없음).

모델은 이 호스트의 ollama 서버가 GPU로 돌리는 공개 모델이고, 임베딩은 로컬 bge-m3다.
외부 API를 부르지 않는다. 채점은 `score_chain_eval.py`가 저장된 응답만으로 따로 한다.

풀이 방법
- closed_book: 질문만 준다.
- dense: 질문을 로컬 bge-m3로 임베딩해 그 WG의 Qdrant 컬렉션(결정·CR·기고문 청크)에서 가까운 청크를 찾아 함께 준다.
- text2cypher: 실행 중인 그래프에서 읽은 스키마와 질문을 주고 Cypher 하나를 받아 읽기 전용으로 실행한다.
  실행 오류가 나면 오류 문구를 돌려주고 다시 받는다(`--repairs` 회까지). 실행 결과 행이 곧 답이다.
- text2sql: 같은 기록을 관계형으로 내보낸 SQLite 파일의 표 정의와 질문을 풀이 주체에게 주고(`--export-packet`),
  밖에서 쓴 SQL(`{id, sql}` JSONL, `--queries`)을 문항마다 읽기 전용으로 실행한다. 실행 결과 행이 곧 답이다.
- 밖에서 쓴 질의(text2cypher · text2sql 의 `--queries`)에 실행 오류가 나면, 풀이 주체가 그 오류 문구를 받고 다시 쓴
  질의를 `--repair-queries` 로 회차 차례대로 준다(`--repairs` 회까지). 문항마다 첫 질의부터 차례로 실행해 처음 성공한
  질의의 결과를 답으로 두고, 실패한 질의는 오류 문구와 함께 `attempts` 에 남긴다. 로컬 모델의 text2cypher 가 받는
  다시 받기 횟수와 같다.
- 묶음(`--export-packet`)은 질문 문장이 알려 주는 것만 싣는다. 문항 id 대신 `packet_id()` 의 값을 쓰고 그 값 차례로
  놓는다. `--queries` · `--repair-queries` 의 id 는 이 묶음 id 이며, 실행 전에 문항 id 로 되돌린다.

모든 방법에서 답은 문항의 `fields` 순서대로 값을 담은 행 목록이다. 기록이 없으면 빈 목록이 정답이다.
응답마다 받은 질문 문장의 SHA-256(`questionSha256`)을 함께 저장한다. 같은 명령을 다시 실행하면 응답이 무엇에 기대는지에 따라
저장된 응답을 다시 쓰거나 새로 만든다.
- closed_book · dense: 모델에 보낸 요청 전체(모델 이름, 메시지, 출력 형식, 생성 설정)의 SHA-256(`requestSha256`)을 저장한다.
  다시 실행하면 문항마다 요청을 새로 만들고(dense 는 검색까지 다시 한다) 저장된 값과 같은 응답만 다시 쓴다. 질문 문장이 같아도
  검색된 청크나 그 메타데이터가 바뀌면 요청이 달라지므로 다시 푼다. `requestSha256` 이 없는 응답도 다시 푼다.
- text2cypher · text2sql: 답이 실행 시점의 그래프나 관계형 파일에 달려 있고 그 상태를 해시로 묶을 수 없으므로, 실행할 때마다
  대상 문항을 모두 다시 실행한다.
결과 파일에는 문항마다 마지막 응답 하나만 남긴다. 실행이 중간에 끊겨 같은 문항이 두 번 적혀 있으면 뒤의 것을 쓴다.

사용: python3 run_chain_eval.py --items <jsonl> --wg RAN4 --method text2cypher --model llama3.1:8b \
        --bolt bolt://localhost:7690 --out <jsonl>
저장소 루트에서 `PYTHONPATH=scripts/common`으로 실행한다.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path

OLLAMA = "http://localhost:11434/api/chat"
QDRANT = "http://localhost:6333"
DENSE_COLLECTIONS = ("resolution_chunks", "cr_chunks", "tdoc_chunks")
TEXT_KEYS = ("text", "content")
ANSWER_RULES = (
    "Answer with a JSON object {\"rows\": [[...], ...]}. Each row lists the requested fields in this order: "
    "%s. Use document numbers, meeting names and clause numbers exactly as written in the records "
    "(for example R4-2205027, RAN4#102-e, RP-221234, RAN#96, 6.2.1). Disposition values are lower-case "
    "codes such as agreed, revised, noted, endorsed, withdrawn, not_pursued. "
    "If the records hold no such row, answer {\"rows\": []}.")
# 질문 문장이 빈 답과 판정 불가 답을 스스로 정하는 문항 틀이다. 이 틀에서는 위 규칙의 마지막 문장이
# 질문의 지시(판정 불가면 INSUFFICIENT_RECORDS 한 행)와 어긋나므로 그 문장만 질문의 지시를 따르라는 문장으로 바꾼다.
# 다른 틀의 규칙 문장은 그대로 두어 이미 저장된 응답이 받은 지시와 같게 유지한다.
SELF_RULED_TEMPLATES = frozenset({"pack_status3"})
SELF_RULED_ENDING = "When the records hold no such row, answer as the question instructs."


def answer_rules(item: dict) -> str:
    rules = ANSWER_RULES % ", ".join(item["fields"])
    if item.get("template") in SELF_RULED_TEMPLATES:
        rules = rules.replace("If the records hold no such row, answer {\"rows\": []}.", SELF_RULED_ENDING)
    return rules


def question_sha(item: dict) -> str:
    return hashlib.sha256(item["question"].encode()).hexdigest()


# 풀이 주체에게 가는 묶음에는 질문 문장이 이미 알려 주는 것만 싣는다. 문항 id·종류 이름·문항 차례는 정답의 모양을
# 알려 줄 수 있다. `pack_lookup_empty` 는 `pack_lookup` 과 같은 질문 틀로 묻고 정답이 빈 목록이라는 점만 다르며,
# 세 갈래 문항 파일은 갈래 차례로 놓여 있다. 그래서 묶음의 id 는 문항 id 의 SHA-256 에서 만든 값이고, 문항은 그 값
# 차례로 놓으며, 종류 이름 자리에는 질문 틀 이름을 쓴다. 풀이 결과는 `item_ids()` 로 문항 id 에 되돌려 놓는다.
QUESTION_TEMPLATE = {"pack_lookup_empty": "pack_lookup"}


def packet_id(item: dict) -> str:
    return f"{item['wg']}-q{hashlib.sha256(('packet:' + item['id']).encode()).hexdigest()[:12]}"


def question_template(item: dict) -> str:
    return item.get("template") or QUESTION_TEMPLATE.get(item["family"], item["family"])


def packet_order(items: list[dict]) -> list[dict]:
    return sorted(items, key=packet_id)


def item_ids(items: list[dict]) -> dict[str, str]:
    """묶음 id 와 문항 id 를 모두 문항 id 로 옮기는 표. 두 이름이 겹치면 멈춘다."""
    table = {item["id"]: item["id"] for item in items}
    for item in items:
        if table.setdefault(packet_id(item), item["id"]) != item["id"]:
            raise SystemExit(f"묶음 id 가 다른 문항 id 와 겹친다: {packet_id(item)}")
    return table


def post(url: str, payload: dict, timeout: int = 600) -> dict:
    request = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={"content-type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def chat_request(model: str, messages: list[dict], context: int) -> dict:
    # 출력 길이는 문맥 길이의 절반으로 묶는다. 온도 0에서 같은 행을 끝없이 되풀이하는 응답이 호출을 붙잡지 않게 한다.
    # 잘린 응답은 JSON으로 읽히지 않아 채점에서 판독 불가로 센다.
    return {"model": model, "messages": messages, "stream": False, "format": "json",
            "options": {"temperature": 0, "seed": 0, "num_ctx": context, "num_predict": context // 2}}


def request_sha(request: dict) -> str:
    return hashlib.sha256(json.dumps(request, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def chat(model: str, messages: list[dict], context: int) -> str:
    return post(OLLAMA, chat_request(model, messages, context))["message"]["content"]


def rows_of(text: str):
    """모델 응답에서 행 목록을 꺼낸다. 형식이 다르면 None이다."""
    try:
        rows = json.loads(text).get("rows")
    except (json.JSONDecodeError, AttributeError):
        return None
    if not isinstance(rows, list) or not all(isinstance(row, list) for row in rows):
        return None
    return [[None if cell is None else str(cell) for cell in row] for row in rows]


def graph_schema(session, samples: bool = False) -> str:
    """실행 중인 그래프에서 레이블별 속성과 관계 유형의 양 끝 레이블을 읽는다.

    `samples`가 참이면 레이블마다 노드 하나를 읽어 속성 옆에 그 값을 예시로 붙인다.
    """
    properties: dict[str, set[str]] = {}
    for row in session.run("CALL db.schema.nodeTypeProperties()"):
        for label in row["nodeLabels"]:
            properties.setdefault(label, set()).update([row["propertyName"]] if row["propertyName"] else [])
    lines = []
    for label, keys in sorted(properties.items()):
        example = {}
        if samples:
            found = session.run(f"MATCH (n:`{label}`) RETURN properties(n) AS p LIMIT 1").single()
            example = found["p"] if found else {}
        lines.append(f"(:{label} {{" + ", ".join(
            key + (f": {json.dumps(str(example[key])[:60], ensure_ascii=False)}" if key in example else "")
            for key in sorted(keys)) + "})")
    # 표본에서 본 유형만 실으므로 드문 관계는 빠질 수 있다. 관계 유형 이름 전체는 따로 싣는다.
    seen = session.run(
        "MATCH (a)-[r]->(b) WITH labels(a)[0] AS a, type(r) AS r, labels(b)[0] AS b, count(*) AS n "
        "RETURN a, r, b ORDER BY n DESC LIMIT 400")
    lines += [f"(:{row['a']})-[:{row['r']}]->(:{row['b']})" for row in seen]
    return "\n".join(lines)


def cypher_task(item: dict, schema: str) -> str:
    return ("You write one read-only Cypher query for a Neo4j graph of 3GPP standardization records. "
            "Graph schema (node labels with properties, then relationship patterns):\n" + schema +
            "\nAnswer with a JSON object {\"cypher\": \"...\"}. The query must RETURN DISTINCT exactly these "
            "columns in this order: " + ", ".join(item["fields"]) + ". " + cypher_clauses(item))


def cypher_clauses(item: dict) -> str:
    """질문이 판정 불가 답(값을 그대로 적은 한 행)을 요구하는 틀에는 그 행을 만들 수 있는 읽기 절을 더 허용한다."""
    if item.get("template") in SELF_RULED_TEMPLATES:
        return ("Use only MATCH, OPTIONAL MATCH, WHERE, WITH, UNWIND, CASE, UNION and RETURN; "
                "when the records hold no such row, answer as the question instructs.")
    return "Use only MATCH, WHERE, WITH, RETURN."


def solve_text2cypher(item: dict, model: str, session, schema: str, repairs: int, context: int,
                      written: list[str] | None = None) -> dict:
    """`written`이 있으면 모델을 부르지 않고 그 질의(첫 질의와 회차별로 다시 쓴 질의)를 차례로 실행한다."""
    messages = [{"role": "system", "content": cypher_task(item, schema)},
                {"role": "user", "content": item["question"]}]
    attempts = []
    for turn in range(len(written) if written is not None else repairs + 1):
        text = json.dumps({"cypher": written[turn]}) if written is not None else chat(model, messages, context)
        try:
            cypher = json.loads(text)["cypher"]
        except (json.JSONDecodeError, KeyError, TypeError):
            attempts.append({"response": text, "error": "response is not {\"cypher\": ...}"})
            return {"rows": None, "attempts": attempts}
        try:
            # 읽기 트랜잭션에서 실행하므로 쓰기 절이 든 질의는 서버가 거부한다.
            rows = session.execute_read(lambda tx: [list(row.values()) for row in tx.run(cypher, timeout=60)])
        except Exception as error:  # 서버가 돌려준 오류 문구를 모델에 그대로 준다
            attempts.append({"cypher": cypher, "error": str(error)[:500]})
            messages += [{"role": "assistant", "content": text},
                         {"role": "user", "content": f"The query failed: {str(error)[:500]}\nReturn a corrected query."}]
            continue
        attempts.append({"cypher": cypher, "rowCount": len(rows)})
        return {"rows": [[None if cell is None else str(cell) for cell in row] for row in rows[:2000]],
                "attempts": attempts}
    return {"rows": None, "attempts": attempts}


def sqlite_schema(db) -> str:
    """관계형 내보내기 파일의 표 정의(CREATE TABLE 문)를 그대로 읽는다. 색인 정의는 싣지 않는다."""
    return "\n".join(sql for (sql,) in db.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND sql IS NOT NULL ORDER BY name"))


def sql_task(item: dict, schema: str) -> str:
    return ("You write one read-only SQLite query for a relational database of 3GPP standardization records. "
            "Database schema (table definitions):\n" + schema +
            "\nAnswer with a JSON object {\"sql\": \"...\"}. The query must SELECT DISTINCT exactly these "
            "columns in this order: " + ", ".join(item["fields"]) + ". Use only SELECT statements (WITH allowed).")


def solve_text2sql(item: dict, db, written: list[str]) -> dict:
    """밖에서 쓴 SQL(첫 질의와 회차별로 다시 쓴 질의)을 읽기 전용 연결에서 차례로 실행하고 처음 성공한 결과를 답으로 둔다.
    질의마다 60초를 넘기면 중단하고 오류로 기록한다."""
    attempts = []
    for sql in written:
        deadline = time.time() + 60
        db.set_progress_handler(lambda: 1 if time.time() > deadline else 0, 100000)
        try:
            rows = db.execute(sql).fetchall()
        except Exception as error:  # 읽기 전용 연결이므로 쓰기 문장은 여기서 거부된다
            attempts.append({"sql": sql, "error": str(error)[:500]})
            continue
        finally:
            db.set_progress_handler(None, 0)
        attempts.append({"sql": sql, "rowCount": len(rows)})
        return {"rows": [[None if cell is None else str(cell) for cell in row] for row in rows[:2000]],
                "attempts": attempts}
    return {"rows": None, "attempts": attempts}


def retrieve(item: dict, top: int) -> list[dict]:
    from common.embedding_registry import embed_query_local
    found = []
    for suffix in DENSE_COLLECTIONS:
        collection = f"{item['wg'].lower()}_{suffix}"
        vector = embed_query_local(collection, item["question"])
        result = post(f"{QDRANT}/collections/{collection}/points/search",
                      {"vector": vector, "limit": top, "with_payload": True}, timeout=120)["result"]
        for point in result:
            payload = point["payload"]
            text = next((payload[key] for key in TEXT_KEYS if payload.get(key)), "")
            found.append({"collection": collection, "chunkId": payload.get("chunkId"), "score": point["score"],
                          "text": text,
                          "meta": {key: payload[key] for key in ("tdocNumber", "meeting", "meetingId", "crPackId",
                                                                 "tsgMeeting", "specNumber", "crNumber",
                                                                 "clausesAffected", "resolutionId") if payload.get(key)}})
    return sorted(found, key=lambda chunk: -chunk["score"])[:top]


def text_request(item: dict, model: str, context: int, chunks: list[dict] | None) -> dict:
    rules = answer_rules(item)
    question = item["question"]
    if chunks is not None:
        passages = "\n\n".join(f"[{n + 1}] {json.dumps(chunk['meta'], ensure_ascii=False)}\n{chunk['text'][:1500]}"
                               for n, chunk in enumerate(chunks))
        question = f"Retrieved records:\n{passages}\n\nQuestion: {question}"
        rules = "Answer from the retrieved records only. " + rules
    return chat_request(model, [{"role": "system", "content": rules}, {"role": "user", "content": question}], context)


def solve_text(request: dict, chunks: list[dict] | None) -> dict:
    text = post(OLLAMA, request)["message"]["content"]
    out = {"rows": rows_of(text), "response": text, "requestSha256": request_sha(request)}
    if chunks is not None:
        out["retrieved"] = [{key: chunk[key] for key in ("collection", "chunkId", "score")} for chunk in chunks]
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, required=True)
    parser.add_argument("--wg", required=True)
    parser.add_argument("--method", required=True, choices=("closed_book", "dense", "text2cypher", "text2sql"))
    parser.add_argument("--sqlite", type=Path,
                        help="text2sql: `export_chain_records_sqlite.py`가 만든 그 WG의 관계형 파일")
    parser.add_argument("--schema-samples", action="store_true",
                        help="text2cypher: 스키마의 속성마다 실제 값 하나를 예시로 붙인다")
    parser.add_argument("--model", required=True)
    parser.add_argument("--bolt")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--top", type=int, default=8, help="dense: 모델에 주는 청크 수")
    parser.add_argument("--repairs", type=int, default=2, help="text2cypher: 실행 오류 뒤 다시 받는 횟수")
    parser.add_argument("--context", type=int, default=16384, help="모델 문맥 길이(토큰)")
    parser.add_argument("--export-packet", type=Path,
                        help="text2cypher: 풀이 주체에게 줄 스키마와 질문(정답 제외)을 이 파일에 쓰고 끝낸다")
    parser.add_argument("--queries", type=Path,
                        help="text2cypher · text2sql: 밖에서 쓴 질의({id, cypher|sql} JSONL)를 문항마다 실행한다")
    parser.add_argument("--repair-queries", type=Path, nargs="*", default=[],
                        help="실행 오류를 받고 다시 쓴 질의({id, cypher|sql} JSONL), 회차 차례대로(--repairs 개까지)")
    parser.add_argument("--limit", type=int, help="문항 종류마다 앞에서부터 푸는 문항 수")
    args = parser.parse_args()
    items = [item for item in map(json.loads, args.items.read_text().splitlines()) if item["wg"] == args.wg]
    wg_items = list(items)
    if args.limit:
        taken: dict[str, int] = {}
        kept = []
        for item in items:
            taken[item["family"]] = taken.get(item["family"], 0) + 1
            if taken[item["family"]] <= args.limit:
                kept.append(item)
        items = kept
    current = {item["id"]: question_sha(item) for item in items}
    # 문항마다 마지막 응답만 남긴다(끊긴 실행이 같은 문항을 두 번 적었으면 뒤의 것).
    stored: dict[str, dict] = {}
    if args.out.exists():
        for record in map(json.loads, args.out.read_text().splitlines()):
            stored[record["id"]] = record
    # 지금 대상 문항의 응답은 질문 문장이 같고, 요청 해시로 다시 쓸 수 있는 방법(closed_book · dense)일 때만 후보로 남긴다.
    # 대상 밖 문항(`--limit` 등)의 응답은 그대로 둔다.
    reusable = args.method in ("closed_book", "dense")
    stored = {identifier: record for identifier, record in stored.items()
              if identifier not in current
              or (reusable and record.get("questionSha256") == current[identifier] and record.get("requestSha256"))}
    args.out.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in stored.values()))
    driver = session = schema = None
    if args.method == "text2cypher":
        from neo4j import GraphDatabase
        from common.credentials import neo4j_auth
        driver = GraphDatabase.driver(args.bolt, auth=neo4j_auth())
        session = driver.session()
        schema = graph_schema(session, args.schema_samples)
        if args.export_packet:
            # 꾸러미 하나는 과제 문장 하나를 공유하므로, 판정 불가 답을 쓰는 틀과 다른 틀을 한 꾸러미에 섞지 않는다.
            if len({item.get("template") in SELF_RULED_TEMPLATES for item in items}) > 1:
                parser.error("--export-packet: 질문이 답 규칙을 정하는 틀과 다른 틀이 한 문항 파일에 섞여 있다")
            args.export_packet.write_text(json.dumps({
                "task": cypher_task({"fields": ["<the item's fields>"],
                                     "template": items[0].get("template") if items else None}, schema),
                "items": [{"id": packet_id(item), "question": item["question"], "fields": item["fields"]}
                          for item in packet_order(items)]}, ensure_ascii=False, indent=1) + "\n")
            return
    db = None
    if args.method == "text2sql":
        import sqlite3
        db = sqlite3.connect(f"file:{args.sqlite}?mode=ro", uri=True)
        if args.export_packet:
            args.export_packet.write_text(json.dumps({
                "task": sql_task({"fields": ["<the item's fields>"]}, sqlite_schema(db)),
                "items": [{"id": packet_id(item), "question": item["question"], "fields": item["fields"]}
                          for item in packet_order(items)]}, ensure_ascii=False, indent=1) + "\n")
            return
        if not args.queries:
            parser.error("text2sql 은 밖에서 쓴 질의(--queries)를 실행만 한다")
    key = "sql" if args.method == "text2sql" else "cypher"
    # 질의 파일의 id 는 묶음 id 다. 묶음 id 를 쓰기 전의 질의 파일도 다시 실행할 수 있게 문항 id 도 받는다.
    written: dict[str, list[str]] = {}
    if args.repair_queries and not args.queries:
        parser.error("--repair-queries 는 --queries 와 함께 쓴다")
    if len(args.repair_queries) > args.repairs:
        parser.error(f"--repair-queries: 다시 쓴 회차가 --repairs({args.repairs})보다 많다")
    if args.queries:
        to_item = item_ids(wg_items)
        for record in map(json.loads, args.queries.read_text().splitlines()):
            if record["id"] not in to_item:
                parser.error(f"--queries: 대상 문항에 없는 id {record['id']}")
            if written.setdefault(to_item[record["id"]], [record[key]]) != [record[key]]:
                parser.error(f"--queries: 한 문항에 질의가 둘 있다 {record['id']}")
        # 회차 k 의 다시 쓴 질의는 그 문항이 k-1 회차까지 질의를 모두 갖고 있을 때만 받는다.
        for turn, path in enumerate(args.repair_queries, start=1):
            seen: set[str] = set()
            for record in map(json.loads, path.read_text().splitlines()):
                identifier = to_item.get(record["id"])
                if identifier is None or identifier not in written:
                    parser.error(f"--repair-queries: 첫 질의가 없는 id {record['id']}")
                if identifier in seen:
                    parser.error(f"--repair-queries: 한 회차에 질의가 둘 있다 {record['id']}")
                if len(written[identifier]) != turn:
                    parser.error(f"--repair-queries: 앞 회차 질의가 없는 id {record['id']}")
                seen.add(identifier)
                written[identifier].append(record[key])
    reused = solved = 0
    with args.out.open("a") as out:
        for item in items:
            started = time.time()
            if args.method in ("closed_book", "dense"):
                chunks = retrieve(item, args.top) if args.method == "dense" else None
                request = text_request(item, args.model, args.context, chunks)
                previous = stored.get(item["id"])
                if previous and previous["requestSha256"] == request_sha(request):
                    reused += 1
                    continue
                result = solve_text(request, chunks)
            elif args.method == "text2cypher":
                if args.queries and item["id"] not in written:
                    continue
                result = solve_text2cypher(item, args.model, session, schema, args.repairs, args.context,
                                           written.get(item["id"]))
            elif args.method == "text2sql":
                if item["id"] not in written:
                    continue
                result = solve_text2sql(item, db, written[item["id"]])
            record = {"id": item["id"], "questionSha256": question_sha(item), "wg": item["wg"], "family": item["family"], "method": args.method + ("+samples" if args.schema_samples else ""),
                      "model": args.model, "seconds": round(time.time() - started, 1), **result}
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()
            stored[item["id"]] = record
            solved += 1
    if driver:
        session.close()
        driver.close()
    args.out.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in stored.values()))
    print(json.dumps({"wg": args.wg, "method": args.method, "model": args.model, "items": len(items),
                      "reused": reused, "solved": solved}))


if __name__ == "__main__":
    main()
