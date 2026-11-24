"""원본 문서의 글만으로 찾는 검색 도구 (읽기 전용): 작업반 청크의 원문 본문과 TSG 총회 문서.

원본 글 식별자 따라가기(`measure_raw_source_route.py`)가 쓰는 두 색인을 그대로 연다. 기록 구축이 만든
메타데이터는 찾지도 보여 주지도 않는다.
- 작업반 청크는 본문 열에서만 찾고, CR 청크에서 기록 필드로 만든 줄(`raw_chunk_text` 가 걷는 줄)은 걷어 낸 뒤
  보여 준다. 걷어 낸 줄에만 맞은 청크는 결과에서 뺀다(걷은 본문을 같은 토크나이저의 임시 색인에 넣어 다시 맞춘다).
- 결과 머리에는 원본 파일 이름에서 오는 것만 적는다: 작업반 기고문 · CR 은 문서 번호, 결정 기록(회의록) 청크는
  번호 없음, 총회 청크는 바깥 파일 이름과 zip 안 경로.
- `--doc` 은 문서 자신의 번호와 정확히 맞춘다(작업반은 파일 이름의 문서 번호, 총회는 바깥 파일 이름의 RP 번호와
  zip 안 경로의 문서 번호).
- 작업반과 총회는 색인이 달라 BM25 점수를 섞지 않고 차례로 따로 보여 준다.

사용 (저장소 루트에서):
  PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark python3 \
      scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/search_raw_text.py --wg RAN1 --query "R1-1909887"
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import time

from measure_raw_source_route import PLENARY, RESOLUTION
from measure_text_route_ceiling import WGS, connect_index, query_expression
from raw_source_text import raw_chunk_text

OVERFETCH = 5
USAGE_LOG_ENV = "RAW_SEARCH_USAGE_LOG"


def still_matches(expression: str, text: str) -> bool:
    con = sqlite3.connect(":memory:")
    con.execute("CREATE VIRTUAL TABLE probe USING fts5(text, tokenize='unicode61 remove_diacritics 2')")
    con.execute("INSERT INTO probe(text) VALUES (?)", (text,))
    return con.execute("SELECT 1 FROM probe WHERE probe MATCH ?", (expression,)).fetchone() is not None


def search_wg(wg: str, expression: str, doc: str | None, top: int) -> list[dict]:
    con = connect_index(wg)
    resolution_like = "%" + RESOLUTION.replace("_", "\\_")
    if expression:
        sql = ("SELECT d.id, d.collection, d.chunk_id, d.tdoc, bm25(search), d.text FROM search "
               "JOIN docs d ON d.id = search.rowid WHERE search MATCH ?"
               + (" AND d.tdoc = ? AND d.collection NOT LIKE ? ESCAPE '\\'" if doc else "")
               + " ORDER BY bm25(search), d.id LIMIT ?")
        args = [f"text : ({expression})"] + ([doc, resolution_like] if doc else []) + [top * OVERFETCH]
    else:
        sql = ("SELECT d.id, d.collection, d.chunk_id, d.tdoc, NULL, d.text FROM docs d WHERE d.tdoc = ? "
               "AND d.collection NOT LIKE ? ESCAPE '\\' ORDER BY d.id LIMIT ?")
        args = [doc, resolution_like, top]
    found = []
    for row_id, collection, chunk_id, tdoc, score, text in con.execute(sql, args):
        raw, removed = raw_chunk_text(collection, chunk_id or "", text)
        if expression and removed and not still_matches(expression, raw):
            continue
        resolution = collection.endswith(RESOLUTION) or not tdoc
        header = {"source": "wg", "id": f"w{row_id}", "kind": "meeting report excerpt" if resolution else "document",
                  "document": None if resolution else tdoc}
        if score is not None:
            header["bm25"] = round(score, 3)
        found.append({"header": header, "text": raw})
        if len(found) == top:
            break
    return found


def search_plenary(expression: str, doc: str | None, top: int) -> list[dict]:
    con = sqlite3.connect(f"file:{PLENARY}?mode=ro", uri=True)
    owned = None
    if doc:
        owned = [row[0] for row in con.execute(
            "SELECT c.id FROM owners o JOIN chunks c ON c.file_id = o.file_id WHERE o.own = ?", (doc,))]
        owned += [row[0] for row in con.execute(
            "SELECT c.id FROM member_owner m JOIN chunks c ON c.member_id = m.member_id WHERE m.own = ?", (doc,))]
        owned = sorted(set(owned))
        if not owned:
            return []
    if expression:
        sql = ("SELECT c.id, c.file_id, c.member_id, bm25(search), c.text FROM search JOIN chunks c ON c.id = search.rowid "
               "WHERE search MATCH ?" + (f" AND c.id IN ({','.join(map(str, owned))})" if owned else "")
               + " ORDER BY bm25(search), c.id LIMIT ?")
        rows = con.execute(sql, (expression, top)).fetchall()
    else:
        rows = con.execute(f"SELECT c.id, c.file_id, c.member_id, NULL, c.text FROM chunks c WHERE c.id IN "
                           f"({','.join(map(str, owned))}) ORDER BY c.file_id, c.member_id, c.seq LIMIT ?",
                           (top,)).fetchall()
    found = []
    for row_id, file_id, member_id, score, text in rows:
        names = json.loads(con.execute("SELECT names FROM files WHERE id = ?", (file_id,)).fetchone()[0])
        chain = con.execute("SELECT chain FROM members WHERE id = ?", (member_id,)).fetchone()[0]
        header = {"source": "plenary", "id": f"t{row_id}", "file": "; ".join(dict.fromkeys(names)), "inside": chain}
        if score is not None:
            header["bm25"] = round(score, 3)
        found.append({"header": header, "text": text})
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--wg", required=True, choices=WGS)
    parser.add_argument("--query", default="", help="찾을 글(빈 글이면 --doc 으로만 찾는다)")
    parser.add_argument("--doc", help="정확히 맞출 문서 번호(파일 이름의 번호: R1-… 또는 RP-…)")
    parser.add_argument("--source", choices=("wg", "plenary", "both"), default="both")
    parser.add_argument("--top", type=int, default=10, help="출처마다 보여 줄 청크 수")
    parser.add_argument("--chars", type=int, default=1500, help="청크마다 보여 줄 본문 글자 수(0 이면 전체)")
    parser.add_argument("--raw", action="store_true", help="--query 를 FTS5 MATCH 문법 그대로 쓴다")
    args = parser.parse_args()
    started = time.time()
    expression = args.query if args.raw else query_expression(args.query)
    if args.query.strip() and not expression:
        raise SystemExit("질의에서 찾을 낱말이 남지 않았다(불용어와 한 글자 낱말은 뺀다)")
    doc = args.doc.upper() if args.doc else None
    if not expression and not doc:
        raise SystemExit("--query 나 --doc 중 하나는 있어야 한다")
    found = []
    if args.source in ("wg", "both"):
        found += search_wg(args.wg, expression, doc, args.top)
    if args.source in ("plenary", "both"):
        found += search_plenary(expression, doc, args.top)
    for rank, hit in enumerate(found, 1):
        print(json.dumps({"rank": rank, **hit["header"]}, ensure_ascii=False))
        print(hit["text"] if args.chars == 0 else hit["text"][:args.chars])
        print()
    if not found:
        print("(no result)")
    import os
    log = os.environ.get(USAGE_LOG_ENV)
    if log:
        with open(log, "a") as out:
            out.write(json.dumps({"wg": args.wg, "query": args.query, "doc": doc, "source": args.source,
                                  "top": args.top, "chars": args.chars, "raw": args.raw, "results": len(found),
                                  "seconds": round(time.time() - started, 3)}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
