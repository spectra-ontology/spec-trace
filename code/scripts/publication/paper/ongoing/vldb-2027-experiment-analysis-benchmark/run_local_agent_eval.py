"""이 호스트의 공개 가중치 모델이 도구를 쓰며 추적 사슬 문항을 풀게 하고 응답과 도구 사용 기록을 저장한다 (과금 API 없음).

모델은 ollama 서버가 GPU 로 돌리는 공개 모델이다. 외부 API 를 부르지 않는다. 채점은 `score_chain_eval.py` 가 저장된
응답만으로 따로 한다. 문항 하나가 한 세션이고, 세션은 다른 문항의 대화를 이어받지 않는다.

경로
- sql_explore: 관계형 내보내기(`integration/sqlite_final/{WG}.sqlite`)의 표 정의와 질문을 주고, 모델이 읽기 전용 SQL 을
  원하는 만큼 실행해 결과를 본 뒤 답이 될 SQL 하나를 낸다. 그 SQL 의 실행 결과 행이 답이다. 질의마다 `run_chain_eval` 과
  같은 60초 상한을 둔다.
- text_search: `search_records_text.search` 로 결정 · CR · 기고문 청크를 메타데이터와 함께 찾고, 모델이 행 목록을 직접
  답한다. 색인과 메타데이터 줄은 Opus 전문 검색 조건이 쓴 것과 같다.

세션의 한계는 문맥 길이 하나다. 문맥은 로컬 독자 조건과 같은 `--context` (기본 16,384 토큰)이다. 도구 결과 하나는
로컬 dense 조건이 한 번에 보여 주는 분량(청크 8개 × 1,500자)을 넘지 않게 자른다. 모델 응답 뒤 ollama 가 알려 준 누적
토큰(prompt_eval_count + eval_count)이 문맥의 절반을 넘으면 다음 차례에 답을 내라고 알리고, 그 차례의 응답이 답이
아니면 판독 불가(`rows` = null)로 둔다. 차례 수 상한은 따로 두지 않는다.

모델은 차례마다 JSON 객체 하나를 낸다. 형식이 다르거나 모르는 동작이면 그 사실을 도구 결과 자리에 돌려준다.
같은 명령을 다시 실행하면 이미 저장된 문항(질문 SHA-256 이 같은 응답)은 건너뛴다.

사용: PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/sigir-2027-research python3 run_local_agent_eval.py \
          --items <jsonl> [<jsonl> ...] --route sql_explore|text_search --model qwen2.5:14b --out-dir <dir> \
          [--context 16384] [--limit N]   (저장소 루트에서 실행)
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import time
from pathlib import Path

from run_chain_eval import OLLAMA, answer_rules, chat_request, post, question_sha, rows_of, sqlite_schema

ROOT = next(path for path in Path(__file__).resolve().parents if (path / ".git").exists())
EXPORT_DIR = ROOT / "logs/publication/paper/ongoing/sigir-2027-research/integration/sqlite_final"
RESULT_CHUNKS, CHUNK_CHARS = 8, 1500  # 로컬 dense 조건이 한 번에 보여 주는 청크 수와 청크당 글자 수
RESULT_CHARS = RESULT_CHUNKS * CHUNK_CHARS
QUERY_SECONDS = 60  # run_chain_eval 의 질의 실행 상한

SQL_TASK = (
    "You answer a question about 3GPP {wg} standardization records held in a read-only SQLite database. "
    "Database schema (table definitions):\n{schema}\n"
    "Reply with exactly one JSON object per turn. To look at the data, reply "
    "{{\"action\": \"query\", \"sql\": \"SELECT ...\"}}; the result rows are returned to you (long results are cut). "
    "You may run as many queries as you need. When you know the query that answers the question, reply "
    "{{\"action\": \"answer\", \"sql\": \"SELECT ...\"}}. That query is executed once and its rows are your answer: it "
    "must SELECT DISTINCT exactly these columns in this order: {fields}. Use only SELECT statements (WITH allowed). "
    "Use document numbers, meeting names and clause numbers exactly as stored. If the records hold no such row, "
    "the answer query returns no rows.")
TEXT_TASK = (
    "You answer a question about 3GPP {wg} standardization records using only a full-text search tool over the {wg} "
    "record chunks (meeting-report decision chunks, CR chunks and contribution chunks, each shown with its metadata). "
    "Reply with exactly one JSON object per turn. To search, reply {{\"action\": \"search\", \"query\": \"TEXT\", "
    "\"tdoc\": \"NUMBER\"}}: query runs a BM25 search, and tdoc (optional) keeps only chunks whose document number "
    "(or, for an RP- number, CR pack number) matches exactly; either may be omitted. Add \"raw\": true to pass query "
    "as an FTS5 MATCH expression, or \"collection\": \"NAME\" to search one collection. Each search returns up to "
    f"{RESULT_CHUNKS} chunks. You may search as many times as you need and follow any identifier you read. When you "
    "know the answer, reply {{\"action\": \"answer\", \"rows\": [[...], ...]}}. {rules}")
FINAL_NOTICE = "The context budget is reached. Reply now with the answer action."


def cut(text: str) -> str:
    return text if len(text) <= RESULT_CHARS else text[:RESULT_CHARS] + "\n[cut]"


def run_sql(db, sql: str):
    """읽기 전용 연결에서 질의 하나를 실행한다. (행 목록, None) 또는 (None, 오류 문구)를 돌려준다."""
    deadline = time.time() + QUERY_SECONDS
    db.set_progress_handler(lambda: 1 if time.time() > deadline else 0, 100000)
    try:
        rows = db.execute(sql).fetchall()
    except Exception as error:  # 읽기 전용 연결이므로 쓰기 문장도 여기서 거부된다
        return None, str(error)[:500]
    finally:
        db.set_progress_handler(None, 0)
    return [[None if cell is None else str(cell) for cell in row] for row in rows], None


def show_rows(rows: list[list]) -> str:
    lines = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    return cut(f"{len(rows)} rows\n{lines}")


def show_chunks(found: list[tuple]) -> str:
    parts = []
    for rank, (collection, chunk_id, score, meta, text) in enumerate(found, 1):
        header = {"rank": rank, "collection": collection, "chunkId": chunk_id}
        if score is not None:
            header["bm25"] = round(score, 3)
        parts.append(f"{json.dumps(header, ensure_ascii=False)}\n{meta}\n{text[:CHUNK_CHARS]}")
    return "\n\n".join(parts) if parts else "0 chunks"


def act(route: str, wg: str, db, reply: dict):
    """모델의 동작 하나를 실행한다. (도구 결과 글, 끝났는가, 답 행, 기록)을 돌려준다."""
    action = reply.get("action")
    if route == "sql_explore" and action in ("query", "answer") and isinstance(reply.get("sql"), str):
        rows, error = run_sql(db, reply["sql"])
        log = {"action": action, "sql": reply["sql"], **({"error": error} if error else {"rowCount": len(rows)})}
        if action == "answer":
            return "", True, rows, log
        return (f"Error: {error}" if error else show_rows(rows)), False, None, log
    if route == "text_search" and action == "search":
        from search_records_text import search
        query, tdoc = str(reply.get("query") or ""), reply.get("tdoc") or None
        log = {"action": "search", "query": query, "tdoc": tdoc, "raw": bool(reply.get("raw")),
               "collection": reply.get("collection") or None}
        try:
            found = search(wg, query, str(tdoc) if tdoc else None, RESULT_CHUNKS, log["collection"], log["raw"])
        except (SystemExit, sqlite3.Error) as error:
            log["error"] = str(error)[:500]
            return f"Error: {log['error']}", False, None, log
        log["chunks"] = len(found)
        return show_chunks(found), False, None, log
    if route == "text_search" and action == "answer":
        rows = rows_of(json.dumps({"rows": reply.get("rows")}))
        return "", True, rows, {"action": "answer", "rowCount": None if rows is None else len(rows)}
    return "Error: reply with one JSON object using one of the actions described.", False, None, {"action": "invalid"}


def solve(item: dict, route: str, model: str, context: int, db, schema: str) -> dict:
    if route == "sql_explore":
        task = SQL_TASK.format(wg=item["wg"], schema=schema, fields=", ".join(item["fields"]))
    else:
        task = TEXT_TASK.format(wg=item["wg"], rules=answer_rules(item))
    messages = [{"role": "system", "content": task}, {"role": "user", "content": item["question"]}]
    trace, started, used, final, ended, rows = [], time.time(), 0, False, "answer", None
    while True:
        response = post(OLLAMA, chat_request(model, messages, context))
        content = response["message"]["content"]
        used = response.get("prompt_eval_count", 0) + response.get("eval_count", 0)
        messages.append({"role": "assistant", "content": content})
        try:
            reply = json.loads(content)
        except json.JSONDecodeError:
            reply = None
        result, done, rows, log = act(route, item["wg"], db, reply) if isinstance(reply, dict) else (
            "Error: the reply was not a JSON object.", False, None, {"action": "unparsed"})
        trace.append({**log, "tokens": used})
        if done:
            break
        if final:
            ended = "no_answer_at_budget"
            break
        if used > context // 2:
            final = True
            result = f"{result}\n\n{FINAL_NOTICE}"
        messages.append({"role": "user", "content": result})
    return {"id": item["id"], "wg": item["wg"], "family": item["family"], "method": f"local_agent_{route}",
            "model": model, "questionSha256": question_sha(item), "rows": rows, "endedBy": ended,
            "turns": len(trace), "tokens": used, "contextOverflow": used >= context,
            "seconds": round(time.time() - started, 1), "trace": trace}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", nargs="+", required=True)
    parser.add_argument("--route", required=True, choices=("sql_explore", "text_search"))
    parser.add_argument("--model", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--context", type=int, default=16384)
    parser.add_argument("--limit", type=int, help="작업반마다 앞에서부터 이 수만 푼다(도구 점검용)")
    args = parser.parse_args()
    items = [json.loads(line) for path in args.items for line in open(path, encoding="utf-8") if line.strip()]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = args.model.replace(":", "_").replace(".", "_")
    for wg in sorted({item["wg"] for item in items}):
        todo = sorted((item for item in items if item["wg"] == wg), key=lambda item: item["id"])[:args.limit]
        path = out_dir / f"{wg}_{args.route}_{tag}.jsonl"
        done = {}
        if path.exists():
            done = {record["id"]: record["questionSha256"] for record in map(json.loads, open(path, encoding="utf-8"))}
        db = sqlite3.connect(f"file:{EXPORT_DIR / (wg + '.sqlite')}?mode=ro", uri=True)
        schema = sqlite_schema(db)
        with open(path, "a", encoding="utf-8") as out:
            for item in todo:
                if done.get(item["id"]) == question_sha(item):
                    continue
                out.write(json.dumps(solve(item, args.route, args.model, args.context, db, schema),
                                     ensure_ascii=False) + "\n")
                out.flush()
        db.close()
        print(wg, args.route, args.model, len(todo), flush=True)


if __name__ == "__main__":
    main()
