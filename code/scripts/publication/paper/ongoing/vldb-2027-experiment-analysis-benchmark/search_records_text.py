"""WG 하나의 결정·CR·기고문 청크를 글로 찾아 메타데이터와 함께 보여 준다 (읽기 전용).

텍스트 경로 상한(`measure_text_route_ceiling.py`)이 쓰는 FTS5 색인을 그대로 열어, 사람이 어떤 청크가 어떤 질의로
나오는지 직접 확인할 수 있게 한다. 색인은 읽기 전용으로 열고 Qdrant·Neo4j 에는 접속하지 않는다.
- `--query` 는 상한 측정의 BM25 경로와 같은 방식으로 질의식을 만든다(불용어를 뺀 낱말을 OR 로 묶음).
  `--raw` 를 주면 FTS5 MATCH 문법을 그대로 쓴다(예: `"2403693" AND agreed`).
- `--tdoc` 은 식별자를 정확히 맞춘다. 작업반 문서 번호는 `tdocNumber`, `RP-` 묶음 번호는 `crPackId` 또는
  `tdocNumber` 가 같은 청크만 남긴다. `--query` 와 함께 주면 그 청크들 안에서 BM25 순으로 늘어놓고,
  `--query` 가 없으면 청크 번호 순으로 늘어놓는다.
- `--text-only` 는 기록 구축이 청크에 붙인 메타데이터를 쓰지 않는다. 검색은 청크 본문 열에서만 하고(`--raw` 식도
  본문 열 필터 안에서만 맞춘다), 메타데이터 줄을 찍지 않으며, `--tdoc` 은 청크가 나온 문서 자신의 번호와만 맞춘다
  (CR 묶음 번호로는 맞추지 않는다). 청크 번호와 컬렉션 이름은 원문 파일의 이름에 해당하므로 그대로 보여 준다.

사용 (저장소 루트에서, 색인을 먼저 만든 뒤):
  PYTHONPATH=scripts/common python3 scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/search_records_text.py \
      --wg RAN1 --query "CR pack for R1-1909887"
  PYTHONPATH=scripts/common python3 scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/search_records_text.py \
      --wg RAN1 --tdoc R1-1909887 --chars 0
"""
from __future__ import annotations

import argparse
import json

from measure_text_route_ceiling import WGS, connect_index, query_expression


def search(wg: str, query: str, tdoc: str | None, top: int, collection: str | None, raw: bool,
           text_only: bool = False) -> list[tuple]:
    con = connect_index(wg)
    where, args = [], []
    if tdoc:
        tdoc = tdoc.upper()
        by_pack = tdoc.startswith("RP-") and not text_only
        where.append("(d.tdoc = ? OR d.pack = ?)" if by_pack else "d.tdoc = ?")
        args += [tdoc, tdoc] if by_pack else [tdoc]
    if collection:
        where.append("d.collection = ?")
        args.append(collection)
    expression = query if raw else query_expression(query)
    if query.strip() and not expression:
        raise SystemExit("질의에서 찾을 낱말이 남지 않았다(불용어와 한 글자 낱말은 뺀다)")
    if expression and text_only:
        # 열 필터 안의 열 필터는 교집합이라, 식 안에 `meta :` 를 적어도 본문 열 밖으로 나가지 않는다.
        expression = f"text : ({expression})"
    if expression:
        sql = ("SELECT d.collection, d.chunk_id, bm25(search), d.meta, d.text FROM search "
               "JOIN docs d ON d.id = search.rowid WHERE search MATCH ?"
               + "".join(f" AND {clause}" for clause in where) + " ORDER BY bm25(search), d.id LIMIT ?")
        return con.execute(sql, [expression, *args, top]).fetchall()
    if not where:
        raise SystemExit("--query 나 --tdoc 중 하나는 있어야 한다")
    sql = ("SELECT d.collection, d.chunk_id, NULL, d.meta, d.text FROM docs d WHERE "
           + " AND ".join(where) + " ORDER BY d.collection, d.chunk_id LIMIT ?")
    return con.execute(sql, [*args, top]).fetchall()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--wg", required=True, choices=WGS)
    parser.add_argument("--query", default="", help="찾을 글(빈 글이면 --tdoc 으로만 찾는다)")
    parser.add_argument("--tdoc", help="정확히 맞출 작업반 문서 번호(R1-…) 또는 CR 묶음 번호(RP-…)")
    parser.add_argument("--top", type=int, default=10, help="보여 줄 청크 수")
    parser.add_argument("--chars", type=int, default=1500, help="청크마다 보여 줄 본문 글자 수(0 이면 전체)")
    parser.add_argument("--collection", help="이 컬렉션만 찾는다(예: ran1_cr_chunks)")
    parser.add_argument("--raw", action="store_true", help="--query 를 FTS5 MATCH 문법 그대로 쓴다")
    parser.add_argument("--text-only", action="store_true",
                        help="기록 구축이 붙인 메타데이터를 쓰지도 보여 주지도 않고 청크 본문에서만 찾는다")
    args = parser.parse_args()
    for rank, (collection, chunk_id, score, meta, text) in enumerate(
            search(args.wg, args.query, args.tdoc, args.top, args.collection, args.raw, args.text_only), 1):
        header = {"rank": rank, "collection": collection, "chunkId": chunk_id}
        if score is not None:
            header["bm25"] = round(score, 3)
        print(json.dumps(header, ensure_ascii=False))
        if not args.text_only:
            print(meta)
        print(text if args.chars == 0 else text[:args.chars])
        print()


if __name__ == "__main__":
    main()
