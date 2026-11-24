"""풀이 주체가 묶음 id 로 쓴 답을 문항 id 로 되돌려 채점기가 읽는 응답 파일로 옮긴다 (모델 호출 없음).

묶음(`build_text_search_packets.py`)은 문항 id 대신 `run_chain_eval.packet_id()` 의 값을 싣는다. 풀이 주체가 쓴 답의
`id` 는 그 묶음 id 다. 이 스크립트는 문항 파일에서 묶음 id → 문항 id 표를 다시 만들어 답을 옮기고, 작업반·종류는
풀이 주체가 적은 값이 아니라 문항 파일의 값으로 채운다. 아래 경우에는 아무것도 쓰지 않고 멈춘다.
- 답의 id 가 어느 문항에도 맞지 않는다.
- 한 문항에 답이 둘 있다.
- 답에 적힌 `questionSha256` 이 문항 질문 문장의 SHA-256 과 다르다.
- `rows` 가 행 목록이 아니다.
묶음에 실린 문항 가운데 답이 없는 문항은 `--packet` 을 주면 세어 보고한다(채점기가 missing 으로 센다).

사용: python3 collect_packet_answers.py --items <jsonl> [<jsonl> ...] --answers <jsonl> --method text_search \
          --model claude-subagent --out <jsonl> [--packet <packet.json>]   (저장소 루트에서 `PYTHONPATH=scripts/common`)
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from run_chain_eval import item_ids


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--answers", type=Path, required=True)
    parser.add_argument("--method", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--packet", type=Path, help="답이 빠진 묶음 문항을 세어 보고한다")
    args = parser.parse_args()
    items = [item for path in args.items for item in map(json.loads, path.read_text().splitlines())]
    by_id = {item["id"]: item for item in items}
    to_item = item_ids(items)
    records: dict[str, dict] = {}
    for line in args.answers.read_text().splitlines():
        if not line.strip():
            continue
        answer = json.loads(line)
        if answer["id"] not in to_item:
            parser.error(f"어느 문항에도 맞지 않는 id: {answer['id']}")
        item = by_id[to_item[answer["id"]]]
        if item["id"] in records:
            parser.error(f"한 문항에 답이 둘 있다: {answer['id']}")
        if answer.get("questionSha256") != hashlib.sha256(item["question"].encode()).hexdigest():
            parser.error(f"질문 문장 해시가 다르다: {answer['id']}")
        rows = answer.get("rows")
        if not isinstance(rows, list) or not all(isinstance(row, list) for row in rows):
            parser.error(f"rows 가 행 목록이 아니다: {answer['id']}")
        records[item["id"]] = {"id": item["id"], "packetId": answer["id"], "wg": item["wg"], "family": item["family"],
                               "method": args.method, "model": args.model,
                               "questionSha256": answer["questionSha256"], "rows": rows}
    missing = None
    if args.packet:
        packet = json.loads(args.packet.read_text())
        missing = sorted(entry["id"] for entry in packet["items"] if to_item.get(entry["id"]) not in records)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records.values()))
    print(json.dumps({"answers": len(records), "out": str(args.out),
                      **({"packetItemsWithoutAnswer": missing} if missing is not None else {})}, ensure_ascii=False))


if __name__ == "__main__":
    main()
