"""에이전트가 쓰는 밀집 검색 도구 (읽기 전용): 제 질의를 로컬 bge-m3 로 임베딩해 가까운 기록 청크를 보여 준다.

단일 프롬프트 밀집 검색(`run_chain_eval.retrieve`)과 같은 세 컬렉션(결정 · CR · 기고문 청크)과 같은 인코더를 쓴다.
다른 점은 질의를 에이전트가 정하고 몇 번이든 다시 찾을 수 있다는 것뿐이다. 식별자 정확 일치 걸러 내기와 낱말
검색식은 없다. 결과마다 글 검색 도구(`search_records_text.py`)와 같은 메타데이터 줄과 본문을 찍는다.

인코더를 호출마다 다시 올리지 않도록 작은 로컬 서버가 모델을 들고 있는다.
  서버:   PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark python3 \
              scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/search_records_dense.py --serve
  도구:   python3 scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/search_records_dense.py \
              --wg RAN1 --query "which CR pack carried R1-1909887"
서버는 127.0.0.1 에서만 듣고, 호출마다 한 줄씩 사용 기록(질의 · 결과 수 · 걸린 시간)을 남긴다.
`--serve --max-top N` 으로 띄운 서버는 한 번의 호출이 돌려주는 청크 수를 N 으로 묶는다(순위 상한 조건).
그 서버는 `--port` 와 `--usage-log` 로 따로 두고, 도구는 환경 변수 `DENSE_SEARCH_PORT` 로 서버를 고른다.
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WGS = ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")
HOST, PORT = "127.0.0.1", 18733
META_KEYS = ("tdocNumber", "meeting", "meetingId", "crPackId", "tsgMeeting", "specNumber", "crNumber",
             "clausesAffected", "resolutionId")
ROOT = Path(__file__).resolve().parents[5]
USAGE_LOG = ROOT / "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/supplement_cycle/dense_tool/usage.jsonl"


def serve(port: int, max_top: int | None, usage_log: Path) -> None:
    import threading

    from common.embedding_registry import embed_query_local
    from run_chain_eval import DENSE_COLLECTIONS, QDRANT, TEXT_KEYS, post

    lock = threading.Lock()
    usage_log.parent.mkdir(parents=True, exist_ok=True)

    def search(wg: str, query: str, top: int, collection: str | None) -> list[dict]:
        found = []
        for suffix in DENSE_COLLECTIONS:
            name = f"{wg.lower()}_{suffix}"
            if collection and collection != name:
                continue
            with lock:
                vector = embed_query_local(name, query)
            result = post(f"{QDRANT}/collections/{name}/points/search",
                          {"vector": vector, "limit": top, "with_payload": True}, timeout=120)["result"]
            for point in result:
                payload = point["payload"]
                found.append({"collection": name, "chunkId": payload.get("chunkId"), "score": point["score"],
                              "meta": {key: payload[key] for key in META_KEYS if payload.get(key)},
                              "text": next((payload[key] for key in TEXT_KEYS if payload.get(key)), "")})
        return sorted(found, key=lambda chunk: -chunk["score"])[:top]

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            started = time.time()
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            try:
                top = int(body["top"]) if max_top is None else min(int(body["top"]), max_top)
                found = search(body["wg"], body["query"], top, body.get("collection"))
                status, out = 200, {"result": found, "maxTop": max_top}
            except Exception as error:  # 도구 쪽에 까닭을 그대로 돌려준다
                status, out = 500, {"error": repr(error)}
            data = json.dumps(out, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            with lock, usage_log.open("a") as log:
                log.write(json.dumps({"wg": body.get("wg"), "query": body.get("query"), "top": body.get("top"),
                                      "collection": body.get("collection"), "label": body.get("label"),
                                      "maxTop": max_top, "results": len(out.get("result", [])),
                                      "seconds": round(time.time() - started, 3)}, ensure_ascii=False) + "\n")

        def log_message(self, *args):
            pass

    search("RAN1", "warm up", 1, None)
    print(json.dumps({"ready": f"{HOST}:{port}", "maxTop": max_top}), flush=True)
    ThreadingHTTPServer((HOST, port), Handler).serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--serve", action="store_true", help="인코더를 들고 있는 로컬 서버를 띄운다")
    parser.add_argument("--wg", choices=WGS)
    parser.add_argument("--query", help="찾을 글(임베딩해서 가까운 청크를 찾는다)")
    parser.add_argument("--top", type=int, default=8, help="보여 줄 청크 수")
    parser.add_argument("--chars", type=int, default=1500, help="청크마다 보여 줄 본문 글자 수(0 이면 전체)")
    parser.add_argument("--collection", help="이 컬렉션만 찾는다(예: ran1_cr_chunks)")
    parser.add_argument("--port", type=int, default=PORT, help="--serve 가 들을 포트")
    parser.add_argument("--max-top", type=int, help="--serve: 한 번의 호출이 돌려주는 청크 수의 상한")
    parser.add_argument("--usage-log", type=Path, default=USAGE_LOG, help="--serve 가 사용 기록을 남길 파일")
    args = parser.parse_args()
    if args.serve:
        serve(args.port, args.max_top, args.usage_log)
        return
    if not args.wg or not (args.query or "").strip():
        raise SystemExit("--wg 와 --query 가 있어야 한다")
    request = urllib.request.Request(
        f"http://{HOST}:{os.environ.get('DENSE_SEARCH_PORT', PORT)}/", method="POST", headers={"Content-Type": "application/json"},
        data=json.dumps({"wg": args.wg, "query": args.query, "top": args.top, "collection": args.collection,
                         "label": os.environ.get("DENSE_SEARCH_LABEL")}).encode())
    with urllib.request.urlopen(request, timeout=300) as response:
        answer = json.loads(response.read())
    found, max_top = answer["result"], answer.get("maxTop")
    for rank, chunk in enumerate(found, 1):
        print(json.dumps({"rank": rank, "collection": chunk["collection"], "chunkId": chunk["chunkId"],
                          "similarity": round(chunk["score"], 4)}, ensure_ascii=False))
        print(json.dumps(chunk["meta"], ensure_ascii=False))
        print(chunk["text"] if args.chars == 0 else chunk["text"][:args.chars])
        print()
    if not found:
        print("(no result)")
    if max_top is not None:
        print(f"(at most {max_top} chunks are returned per call)")


if __name__ == "__main__":
    main()
