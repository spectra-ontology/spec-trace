#!/usr/bin/env python3
"""보완 주기의 풀이 세션 답(작업반 3분할 × 15세션)을 묶음과 대조해 모으고 세 표기 규칙으로 채점한다 (모델 호출 없음).

한 조건의 한 실행은 `text_search_packets_full/parts/{WG}_part{k}.json` 열다섯 묶음에 세션 하나씩이 쓴
`{part}_answers.jsonl` 이다. 분할마다 답의 묶음 id 와 순서, 질문 해시를 묶음과 대조하고, 어긋나면 멈춘다.
맞으면 `collect_packet_answers.py` 로 문항 id 로 되돌린 응답 파일을 작업반별로 쓰고,
`score_meeting_spelling_sensitivity.py` 의 `recorded` · `same_meeting` · `literal` 규칙으로 정확 일치를 센다.
답이 없는 분할(세션이 끝나지 않은 분할)은 `--allow-missing` 을 줄 때만 받아 그 문항을 오답으로 센다.

사용: python3 score_supplement_solver_runs.py --condition raw_index --run runA --answers-dir <dir> --out-dir <dir>
      (저장소 루트에서 `PYTHONPATH=scripts/common:<이 폴더>`)
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import score_meeting_spelling_sensitivity as sens

ROOT = sens.ROOT
PARTS = f"{sens.TRACK}/chain_eval/text_search_packets_full/parts"
ITEMS = sens.ITEMS
WGS = sens.WGS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--condition", required=True)
    parser.add_argument("--run", required=True)
    parser.add_argument("--answers-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--allow-missing", action="store_true")
    args = parser.parse_args()

    items = {item["id"]: item for path in ITEMS for item in map(json.loads, (ROOT / path).read_text().splitlines())}
    sessions = args.out_dir / "session_outputs"
    sessions.mkdir(parents=True, exist_ok=True)
    parts_report, missing_parts = [], []
    for wg in WGS:
        merged = []
        for k in (1, 2, 3):
            part = f"{wg}_part{k}"
            packet = json.loads((ROOT / PARTS / f"{part}.json").read_text())
            expected = [(entry["id"], entry.get("questionSha256")) for entry in packet["items"]]
            source = args.answers_dir / f"{part}_answers.jsonl"
            if not source.exists():
                if not args.allow_missing:
                    raise SystemExit(f"답 파일이 없다: {source}")
                missing_parts.append(part)
                parts_report.append({"part": part, "packetItems": len(expected), "answers": 0, "missing": True})
                continue
            lines = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
            got = [(line["id"], line.get("questionSha256")) for line in lines]
            if [g[0] for g in got] != [e[0] for e in expected]:
                raise SystemExit(f"{part}: 답의 묶음 id 순서가 묶음과 다르다 ({len(got)} / {len(expected)})")
            if any(e[1] and g[1] and e[1] != g[1] for g, e in zip(got, expected)):
                raise SystemExit(f"{part}: 질문 해시가 묶음과 다르다")
            if any(not isinstance(line.get("rows"), list) for line in lines):
                raise SystemExit(f"{part}: rows 가 행 목록이 아니다")
            shutil.copyfile(source, sessions / source.name)
            trace = args.answers_dir / f"{part}_trace.jsonl"
            if trace.exists():
                shutil.copyfile(trace, sessions / trace.name)
            merged.extend(lines)
            parts_report.append({"part": part, "packetItems": len(expected), "answers": len(lines),
                                 "emptyAnswers": sum(not line["rows"] for line in lines), "traceKept": trace.exists()})
        if not merged:
            continue
        joined = args.out_dir / f"{wg}_packet_answers.jsonl"
        joined.write_text("".join(json.dumps(line, ensure_ascii=False) + "\n" for line in merged))
        out = args.out_dir / f"{wg}_{args.condition}_claude_subagent.jsonl"
        subprocess.run([sys.executable, "-B", str(Path(__file__).with_name("collect_packet_answers.py")),
                        "--items", *[str(ROOT / path) for path in ITEMS], "--answers", str(joined),
                        "--method", args.condition, "--model", "claude-subagent", "--out", str(out)],
                       check=True, stdout=subprocess.DEVNULL)

    paths = [str((args.out_dir / f"{wg}_{args.condition}_claude_subagent.jsonl").resolve().relative_to(ROOT))
             for wg in WGS if (args.out_dir / f"{wg}_{args.condition}_claude_subagent.jsonl").exists()]
    responses, tally = sens.read_responses(paths, items)
    kept = sens.separately_recorded_meetings()
    result = {"condition": args.condition, "run": args.run, "items": len(items), "answered": len(responses),
              "responseTally": tally, "missingParts": missing_parts, "parts": parts_report, "exact": {}}
    for rule in sens.RULES:
        key = sens.make_row_key(rule, kept)
        hit = {identifier: sens.exact(item, (responses.get(identifier) or {}).get("rows"), key)
               for identifier, item in items.items()}
        answerable = [i for i, item in items.items() if item["gold"]]
        empty = [i for i, item in items.items() if not item["gold"]]
        families, by_wg = {}, {}
        for identifier, item in items.items():
            for table, name in ((families, item["family"]), (by_wg, item["wg"])):
                cell = table.setdefault(name, {"exact": 0, "of": 0})
                cell["exact"] += hit[identifier]
                cell["of"] += 1
        result["exact"][rule] = {"all": sum(hit.values()), "answerable": sum(hit[i] for i in answerable),
                                 "answerableOf": len(answerable), "emptyGold": sum(hit[i] for i in empty),
                                 "emptyGoldOf": len(empty), "byFamily": families, "byWg": by_wg,
                                 "missed": sorted(i for i, ok in hit.items() if not ok)}
    (args.out_dir / "scores.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
    for rule in sens.RULES:
        cell = result["exact"][rule]
        print(f"{args.condition} {args.run} {rule}: {cell['all']}/{len(items)} · 정답 있음 {cell['answerable']}/"
              f"{cell['answerableOf']} · 빈 정답 {cell['emptyGold']}/{cell['emptyGoldOf']}")


if __name__ == "__main__":
    main()
