"""같은 문항 묶음을 다른 검색 도구 조건으로 옮기고 풀이 주체에게 줄 지시문을 만든다 (모델 호출 없음).

글 검색 묶음(`build_text_search_packets.py` 의 parts)에서 문항은 그대로 두고 `task` 글만 조건의 도구 설명으로 바꾼다.
문항 id·질문·요청 필드·질문 SHA-256 과 답 형식 규칙은 원래 묶음과 같으므로 조건 사이의 차이는 도구뿐이다.
조건은 셋이다.
- raw: `search_raw_text.py` — 구축이 붙인 표지와 메타데이터가 없는 원문 본문과 TSG 총회 문서를 찾는다.
- dense: `search_records_dense.py` — 질의를 로컬 임베딩으로 바꿔 기록 청크를 찾는다.
- dense_capped: 같은 도구를 호출당 결과 수 상한이 걸린 서버(`--serve --max-top`)에 물린다. 상한은 문항 정답 중
  가장 큰 것의 행 수(`DENSE_CAP`)로, 순위가 완전하면 한 번의 호출로 어느 정답이든 담을 수 있는 가장 작은 값이다.
지시문은 실행(run)마다 따로 만들고, 풀이 주체가 쓸 작업 폴더와 사용 기록 표지만 다르다.

사용: python3 build_tool_condition_packets.py --parts <dir> --condition raw|dense|dense_capped --runs A B --out-dir <dir> \
          --work-root <dir>   (저장소 루트에서 실행)
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCRIPTS = "scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
DENSE_CAP = 61  # 667 문항 정답의 최대 행 수
DENSE_CAPPED_PORT = 18734
CONDITIONS = {
    "raw": {
        "method": "raw_text_search",
        "task": (
            "You answer questions about 3GPP {wg} standardization records using only a full-text search tool over "
            "the source text for {wg}: the text of the working-group source documents (meeting-report excerpts, "
            "change requests and contributions) as extracted from the files, and the TSG plenary archive documents "
            "for the same period. No extracted metadata or labels are shown or searched; a result header shows only "
            "its source, an identifier, the document kind and, when the file name carries one, the document number. "
            "Run the tool from the repository root with Bash:\n  {tool}\n"
            "--query runs a BM25 search over the text; --raw passes an FTS5 MATCH expression; --doc keeps only "
            "text from the file with exactly that document number (R{n}-... or RP-...); --source chooses the "
            "working-group documents, the plenary documents or both; --chars 0 prints whole chunks. "
            "You may search as many times as you need and follow any identifier you read. Do not open any other "
            "file, database, graph or service. {rules}"),
        "tool": ("PYTHONPATH=scripts/common:" + SCRIPTS + " python3 " + SCRIPTS + "/search_raw_text.py --wg {wg} "
                 "[--query TEXT] [--doc NUMBER] [--source wg|plenary|both] [--top N] [--chars N] [--raw]"),
        "prefix": "RAW_SEARCH_USAGE_LOG={usage}",
    },
    "dense": {
        "method": "dense_search",
        "task": (
            "You answer questions about 3GPP {wg} standardization records using only a dense retrieval tool over "
            "the {wg} record chunks (meeting-report decision chunks, CR chunks and contribution chunks, each printed "
            "with its metadata). The tool embeds your query text and prints the nearest chunks by similarity. "
            "Run the tool from the repository root with Bash:\n  {tool}\n"
            "--query is the text to embed; --top sets how many chunks are printed; --collection restricts the search "
            "to one collection named in the output; --chars 0 prints whole chunks. "
            "You may search as many times as you need and follow any identifier you read. Do not open any other "
            "file, database, graph or service. {rules}"),
        "tool": ("python3 " + SCRIPTS + "/search_records_dense.py --wg {wg} --query TEXT [--top N] [--chars N] "
                 "[--collection NAME]"),
        "prefix": "DENSE_SEARCH_LABEL={label}",
    },
    "dense_capped": {
        "method": "dense_search_capped",
        "task": (
            "You answer questions about 3GPP {wg} standardization records using only a dense retrieval tool over "
            "the {wg} record chunks (meeting-report decision chunks, CR chunks and contribution chunks, each printed "
            "with its metadata). The tool embeds your query text and prints the nearest chunks by similarity. "
            "Run the tool from the repository root with Bash:\n  {tool}\n"
            "--query is the text to embed; --top sets how many chunks are printed, and one call returns at most " + str(DENSE_CAP) + " chunks; "
            "--collection restricts the search "
            "to one collection named in the output; --chars 0 prints whole chunks. "
            "You may search as many times as you need and follow any identifier you read. Do not open any other "
            "file, database, graph or service. {rules}"),
        "tool": ("python3 " + SCRIPTS + "/search_records_dense.py --wg {wg} --query TEXT [--top N] [--chars N] "
                 "[--collection NAME]"),
        "prefix": "DENSE_SEARCH_PORT=" + str(DENSE_CAPPED_PORT) + " DENSE_SEARCH_LABEL={label}",
    },
}

PROMPT = """You are a solver in a controlled evaluation. Work in the repository {root} (run every command from that directory).

Read exactly one input file: {packet} . Its "task" field defines the only tool you may use and the answer format; its "items" field lists {count} questions. Follow the task text exactly. In particular:
- The only data access allowed is the search tool command given in the task. Put `{prefix}` in front of every tool command (it only records usage). You may run the tool as many times as you like and save its printed output under {work}/ and post-process that saved output with your own small Python or shell code.
- Do not open, grep, list or query any other file, directory, database, graph, index or service (no other logs, item files, gold answers, earlier answers, scripts' source, Neo4j, Qdrant or the SQLite files directly). Do not read the tool's source code. Do not search the web.
- Answer each item only from what the tool prints. If the printed text does not support a row, do not invent it; if nothing supports any row, answer {{"rows": []}}.

Write two files:
1. {answers} — one JSON object per item, in packet order, with keys: "id", "wg" ("{wg}"), "family" (copied from the packet item), "method" ("{method}"), "model" ("claude-subagent"), "questionSha256" (copied verbatim from the packet item), "rows" (list of rows, each row a list of strings in the item's field order).
2. {trace} — one JSON object per item with keys "id", "searches" (number of tool runs for that item), "commands" (the full tool command lines you ran for that item, verbatim), "note" (one short sentence on how you derived the rows or why the answer is empty).

Finish all {count} items. In your final message report: number of items answered, total tool runs, and confirm in one sentence that you accessed no data other than the packet and the tool output. Keep the final message short."""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--parts", type=Path, required=True)
    parser.add_argument("--condition", choices=sorted(CONDITIONS), required=True)
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    args = parser.parse_args()
    spec = CONDITIONS[args.condition]
    root = Path.cwd()
    parts_out = args.out_dir / "packets" / "parts"
    parts_out.mkdir(parents=True, exist_ok=True)
    report = {"condition": args.condition, "method": spec["method"], "sourceParts": str(args.parts),
              "runs": args.runs, "parts": []}
    for source in sorted(args.parts.glob("RAN*_part*.json")):
        packet = json.loads(source.read_text())
        wg = source.name.split("_")[0]
        marker = "Answer with a JSON object"
        rules = marker + packet["task"].split(marker, 1)[1]
        task = spec["task"].format(wg=wg, n=wg[-1], tool=spec["tool"].format(wg=wg), rules=rules)
        target = parts_out / source.name
        target.write_text(json.dumps({"task": task, "items": packet["items"]}, ensure_ascii=False, indent=1))
        report["parts"].append({
            "part": source.stem, "items": len(packet["items"]),
            "itemsSha256": hashlib.sha256(json.dumps(packet["items"], sort_keys=True).encode()).hexdigest(),
            "sourceSha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "packetSha256": hashlib.sha256(target.read_bytes()).hexdigest()})
        for run in args.runs:
            label = f"{args.condition}_run{run}"
            work = args.work_root / label
            prompts = args.out_dir / f"run{run}" / "prompts"
            prompts.mkdir(parents=True, exist_ok=True)
            usage = root / args.out_dir / f"run{run}" / "usage" / f"{source.stem}.jsonl"
            usage.parent.mkdir(parents=True, exist_ok=True)
            prefix = spec["prefix"].format(usage=usage, label=f"{label}_{source.stem}")
            (prompts / f"{source.stem}.txt").write_text(PROMPT.format(
                root=root, packet=target, count=len(packet["items"]), prefix=prefix,
                work=work / f"work_{source.stem}", answers=work / f"{source.stem}_answers.jsonl",
                trace=work / f"{source.stem}_trace.jsonl", wg=wg, method=spec["method"]))
    (args.out_dir / "packets" / "build_report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps({"condition": args.condition, "parts": len(report["parts"]),
                      "items": sum(p["items"] for p in report["parts"]), "runs": args.runs}))


if __name__ == "__main__":
    main()
