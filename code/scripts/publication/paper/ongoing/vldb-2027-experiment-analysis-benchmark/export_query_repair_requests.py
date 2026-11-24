"""밖에서 쓴 질의 가운데 실행 오류가 난 것을 묶음 id · 그 질의 · 오류 문구로 내보낸다 (모델 호출 없음).

`run_chain_eval.py --queries`(와 `--repair-queries`)의 응답 파일에서 `rows` 가 없는(실행에 모두 실패한) 문항만 고른다.
각 줄은 `{id, <cypher|sql>, error}` 이며, `id` 는 풀이 주체가 받은 묶음 id(`run_chain_eval.packet_id()`)이고,
질의와 오류 문구는 그 문항의 마지막 시도에서 가져온다. 오류 문구는 실행기가 기록한 앞 500자 그대로이며, 로컬 모델의
text2cypher 가 다시 받기 전에 받는 문구와 같다. 이 줄들을 질의를 쓴 풀이 주체에게 그대로 돌려주고, 다시 쓴 질의를
`--repair-queries` 로 실행한다.

사용: python3 export_query_repair_requests.py --items <jsonl> [<jsonl> ...] --responses <jsonl> --out <jsonl>
          (저장소 루트에서 `PYTHONPATH=scripts/common:<이 디렉토리>`)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_chain_eval import packet_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--responses", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    items = {item["id"]: item for path in args.items for item in map(json.loads, path.read_text().splitlines())}
    requests = []
    for record in map(json.loads, args.responses.read_text().splitlines()):
        if record.get("rows") is not None:
            continue
        if record["id"] not in items:
            parser.error(f"문항 파일에 없는 응답 id: {record['id']}")
        last = record["attempts"][-1]
        key = "sql" if "sql" in last else "cypher"
        requests.append({"id": packet_id(items[record["id"]]), key: last[key], "error": last["error"]})
    requests.sort(key=lambda request: request["id"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(request, ensure_ascii=False) + "\n" for request in requests))
    print(json.dumps({"responses": str(args.responses), "failed": len(requests), "out": str(args.out)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
