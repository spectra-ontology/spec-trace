"""글 검색 도구만 쓰는 풀이 주체에게 줄 문항 묶음을 만든다 (모델 호출 없음).

채택된 문항에서 작업반·문항 종류마다 `--per-cell` 개를 고른다. 고르는 순서는 `--seed` 와 문항 id 를 이은 글의
SHA-256 이라, 문항 파일의 줄 순서와 무관하게 같은 문항이 뽑힌다. 묶음에는 질문·요청 필드·질문 문장의 SHA-256 만
싣고 정답과 근거는 싣지 않는다. 문항 id 는 `run_chain_eval.packet_id()` 의 값으로, 종류 이름은 질문 틀 이름으로 싣고
문항은 묶음 id 차례로 놓는다. 셋 모두 정답의 모양을 드러내지 않게 하려는 것이다(`run_chain_eval` 의 설명 참고).
풀이 주체가 쓴 답은 `collect_packet_answers.py` 가 문항 id 로 되돌린다. 답 형식 규칙은 다른 풀이 방법과 같은
`run_chain_eval.ANSWER_RULES` 를 쓴다.

풀이 주체가 쓸 수 있는 도구는 `search_records_text.py` 하나다. 이 도구는 텍스트 경로 상한 측정과 같은 색인
(결정·CR·기고문 청크와 그 메타데이터)을 읽기 전용으로 연다. 그래프와 관계형 내보내기는 이 조건에서 쓰지 않는다.
`--text-only` 를 주면 도구를 늘 `--text-only` 로 부르게 하는 묶음을 만든다. 기록 구축이 청크에 붙인 메타데이터
(CR 묶음 번호·TSG 회의·결정 식별자 등)를 빼고 청크 본문만 찾게 하는 대조 조건이다.

사용: python3 build_text_search_packets.py --items <jsonl> [<jsonl> ...] --per-cell 2 --seed text-search \
          --out-dir <dir> [--text-only]   (저장소 루트에서 실행)
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path

from run_chain_eval import (ANSWER_RULES, SELF_RULED_ENDING, SELF_RULED_TEMPLATES, item_ids, packet_id,
                            packet_order, question_template)

TOOL = ("PYTHONPATH=scripts/common python3 scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/"
        "search_records_text.py --wg {wg} [--query TEXT] [--tdoc NUMBER] [--top N] [--chars N] "
        "[--collection NAME] [--raw]")

TASK = (
    "You answer questions about 3GPP {wg} standardization records using only a full-text search tool over "
    "the {wg} record chunks (meeting-report decision chunks, CR chunks and contribution chunks, each printed "
    "with its metadata). Run the tool from the repository root with Bash:\n  {tool}\n"
    "--query runs a BM25 search; --raw passes an FTS5 MATCH expression; --tdoc keeps only chunks whose "
    "document number (or, for an RP- number, CR pack number) matches exactly; --chars 0 prints whole chunks. "
    "You may search as many times as you need and follow any identifier you read. Do not open any other file, "
    "database, graph or service. {rules}")
TEXT_ONLY_TOOL = TOOL.replace("--wg {wg}", "--wg {wg} --text-only")
TEXT_ONLY_TASK = (
    "You answer questions about 3GPP {wg} standardization records using only a full-text search tool over "
    "the text of the {wg} record chunks (meeting-report decision chunks, CR chunks and contribution chunks). "
    "Each result shows its collection, its chunk identifier (named after the source document) and its text; "
    "no extracted metadata is shown or searched. Run the tool from the repository root with Bash, always with "
    "--text-only:\n  {tool}\n"
    "--query runs a BM25 search over chunk text; --raw passes an FTS5 MATCH expression over chunk text; --tdoc "
    "keeps only chunks of the document with exactly that number; --chars 0 prints whole chunks. "
    "You may search as many times as you need and follow any identifier you read. Do not open any other file, "
    "database, graph or service. {rules}")


def order_key(seed: str, identifier: str) -> str:
    return hashlib.sha256(f"{seed}:{identifier}".encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--per-cell", type=int, required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--text-only", action="store_true", help="메타데이터를 뺀 본문 검색 대조 조건의 묶음을 만든다")
    args = parser.parse_args()
    task, tool = (TEXT_ONLY_TASK, TEXT_ONLY_TOOL) if args.text_only else (TASK, TOOL)
    cells: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for path in args.items:
        for item in map(json.loads, path.read_text().splitlines()):
            cells[(item["wg"], item["family"])].append(item)
    chosen: dict[str, list[dict]] = collections.defaultdict(list)
    for (wg, _family), items in sorted(cells.items()):
        chosen[wg] += sorted(items, key=lambda item: order_key(args.seed, item["id"]))[:args.per_cell]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"seed": args.seed, "perCell": args.per_cell, "textOnly": args.text_only,
                "items": [str(path) for path in args.items], "byWg": {}}
    for wg, items in sorted(chosen.items()):
        rules = ANSWER_RULES % "<the item's fields>"
        self_ruled = {item.get("template") in SELF_RULED_TEMPLATES for item in items}
        if len(self_ruled) > 1:
            parser.error(f"{wg}: 질문이 빈 답과 판정 불가 답을 정하는 틀과 다른 틀이 한 묶음에 섞였다")
        if self_ruled == {True}:
            rules = rules.replace("If the records hold no such row, answer {\"rows\": []}.", SELF_RULED_ENDING)
        item_ids(items)
        packet = {"task": task.format(wg=wg, tool=tool.format(wg=wg), rules=rules),
                  "items": [{"id": packet_id(item),
                             "family": question_template(item),
                             "question": item["question"],
                             "fields": item["fields"],
                             "questionSha256": hashlib.sha256(item["question"].encode()).hexdigest()}
                            for item in packet_order(items)]}
        (args.out_dir / f"{wg}_packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=1) + "\n")
        manifest["byWg"][wg] = [item["id"] for item in items]
    (args.out_dir / "sample.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n")
    print({wg: len(ids) for wg, ids in manifest["byWg"].items()})


if __name__ == "__main__":
    main()
