#!/usr/bin/env python3
"""결과 표(tab:results)의 조건별 정확 일치 수를 문항 계열과 홉 수로 나눈다.

저장된 문항별 응답을 고치지 않은 채점기 `score_chain_eval.score`(기록 표기 규칙)로 다시 채점한다.
조건마다 먼저 표의 Answerable 칸과 Empty-gold 칸을 응답 파일에서 다시 만들어 원고의 칸과 글자로 견주고,
같은 조건만 계열 · 홉 수로 나눈다. 같지 않은 조건은 얻은 수를 그대로 적고 나누지 않는다.

둘째 규칙(같은 회의의 두 표기를 하나로 보는 규칙)은 저장소가 이미 가진 채점 함수
`score_meeting_spelling_sensitivity.make_row_key("same_meeting", …)` · `exact` 를 그대로 쓰고,
표의 Second rule 칸을 같은 방식으로 먼저 다시 만든 뒤에 나눈다.

채점기 CLI 를 실행마다 한 번 불러(`--out /dev/stdout`, 디스크에 쓰지 않는다) 계열 · 홉 수별 정확 일치가
이 스크립트의 집계와 같은지도 본다. 모델 · 네트워크 · 서비스 호출이 없고 저장된 파일을 읽기만 한다.
저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import subprocess
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path.cwd()
TRACK = "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
SCRIPTS = "scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
MANUSCRIPT = "docs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/manuscript/main.tex"
ITEM_FILES = (f"{TRACK}/integration/items_final/gate/core/chain_items_admitted.jsonl",
              f"{TRACK}/integration/items_final/gate/ran5/chain_items_admitted.jsonl")
SCORER = f"{SCRIPTS}/score_chain_eval.py"
SECOND_RULE_SCORER = f"{SCRIPTS}/score_meeting_spelling_sensitivity.py"
CE = f"{TRACK}/chain_eval"
SUP = f"{TRACK}/final/supplement_cycle"
CAP_RECORD = f"{SUP}/dense_capped_agent/design_record.json"
DEFAULT_OUT = f"{TRACK}/final/next_cycle/work/vldb_draft/analysis/breakdown_by_family.json"
WGS = ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")
RUNS = [f"run{letter}" for letter in "ABCDEFGHIJ"]
STACKED = re.compile(r"\\begin\{tabular\}(?:\[\w\])?\{@\{\}l@\{\}\}(.*)\\end\{tabular\}")

if not (ROOT / ".git").exists() or not (ROOT / SCORER).exists():
    sys.exit("저장소 루트에서 실행한다: 현재 폴더에 .git 과 채점기가 없다")
sys.path[:0] = [str(ROOT / "scripts/common"), str(ROOT / SCRIPTS)]

import score_meeting_spelling_sensitivity as SENS  # noqa: E402
from score_chain_eval import score  # noqa: E402


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def jsonl(path: Path):
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def mean1(values: list[int]) -> str:
    return str((Decimal(sum(values)) / Decimal(len(values))).quantize(Decimal("0.1"), ROUND_HALF_UP))


def runs_cell(values: list[int]) -> str:
    return f"{mean1(values)} ({min(values)}--{max(values)})"


def count_cell(values: list[int], n: int) -> str:
    return f"{values[0]}/{n}" if len(set(values)) == 1 else runs_cell(values)


def answerable_cell(shape: str, values: list[int], n: int) -> str:
    """표 칸의 세 모양: single(실행 하나) · count(검색 에이전트 여러 실행) · query(질의 작성 열 실행)."""
    if shape == "single":
        (k,) = values
        return f"{k}/{n}"
    if shape == "count":
        return count_cell(values, n)
    return runs_cell(values)


def leading_count(cell: str | None) -> str | None:
    """`k/n [구간]` 칸에서 구간을 떼어 낸 앞부분. 구간은 이 스크립트가 다시 만들지 않는다."""
    return None if cell is None else cell.split(" [")[0]


def read_table(path: Path) -> tuple[list[str], dict]:
    """주석 줄을 뺀 뒤 `\\label{tab:results}` 를 담은 table* 하나의 행을 (Access, Solver) 로 읽는다."""
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("%")]
    label = next(i for i, line in enumerate(lines) if r"\label{tab:results}" in line)
    start = max(i for i in range(label + 1) if lines[i].lstrip().startswith(r"\begin{table*}"))
    end = next(i for i in range(label, len(lines)) if lines[i].lstrip().startswith(r"\end{table*}"))
    body = [line.strip() for line in lines[start:end + 1] if line.rstrip().endswith("\\\\") and " & " in line]
    header = [cell.strip() for cell in body[0][:-2].split(" & ")]
    rows = {}
    for line in body[1:]:
        cells = [cell.strip() for cell in line[:-2].split(" & ")]
        stacked = STACKED.fullmatch(cells[0])
        if stacked:
            cells[0] = " ".join(part.strip() for part in stacked.group(1).split("\\\\"))
        rows[(cells[0], cells[1])] = dict(zip(header, cells))
    return header, rows


def per_wg(template: str) -> list[str]:
    return [template.format(wg=wg) for wg in WGS]


def collected(agent: str, run: str, name: str) -> list[str]:
    return per_wg(f"{SUP}/{agent}/{run}/collected/{{wg}}_{name}_claude_subagent.jsonl")


def conditions(cap: int) -> list[tuple]:
    """(id, 표 Access, 표 Solver, 합친 행 안의 조건, 칸 모양, {실행: 응답 파일})."""
    local = ("llama3.1:8b", "qwen2.5:14b")
    codex, opus = "gpt-6.1-sol (Codex)", "Opus 5.5"
    text_only = {"runA": per_wg(f"{CE}/text_only_full/{{wg}}_text_search_text_only_claude_subagent.jsonl"),
                 **{run: collected("text_only_agent", run, "text_only") for run in ("runB", "runC")}}
    text_search = {run: per_wg(f"{CE}/{folder}/{{wg}}_text_search_claude_subagent.jsonl") for run, folder in
                   (("runA", "text_search_full"), ("runB", "text_search_full_runB"), ("runC", "text_search_full_runC"))}
    raw = {run: collected("raw_agent", run, "raw_index") for run in ("runA", "runB")}
    dense = {run: collected("dense_agent", run, "dense_tool") for run in ("runA", "runB")}
    capped = {"runA": collected("dense_capped_agent", "runA", "dense_tool_capped")}
    sql = {run: per_wg(f"{CE}/text2sql/{{wg}}_text2sql_{run}.jsonl") for run in RUNS}
    cypher = {run: per_wg(f"{CE}/{{wg}}_text2cypher_claude_subagent_{run}.jsonl") for run in RUNS}

    def single(template: str) -> dict:
        return {"single": per_wg(f"{CE}/{template}")}

    return [
        ("T01a", "Closed-book", ", ".join(local), local[0], "single", single("{wg}_closed_book_llama3_1_8b.jsonl")),
        ("T01b", "Closed-book", ", ".join(local), local[1], "single", single("{wg}_closed_book_qwen2_5_14b.jsonl")),
        ("T02", "Dense, 8 chunks", local[0], "", "single", single("{wg}_dense_llama3_1_8b.jsonl")),
        ("T03", "Dense, 8 chunks", local[1], "", "single", single("{wg}_dense_qwen2_5_14b.jsonl")),
        ("T04", "Oracle evidence", local[0], "", "single",
         single("oracle_evidence/{wg}_oracle_evidence_llama3_1_8b.jsonl")),
        ("T05", "Oracle evidence", local[1], "", "single",
         single("oracle_evidence/{wg}_oracle_evidence_qwen2_5_14b.jsonl")),
        ("T06", "Oracle evidence, text only", local[0], "", "single",
         single("oracle_evidence/{wg}_oracle_evidence_textonly_llama3_1_8b.jsonl")),
        ("T07", f"Text search, text only, {len(text_only)} runs", opus, "", "count", text_only),
        ("T08", f"Text search, {len(text_search)} runs", opus, "", "count", text_search),
        ("T09", f"Raw-text search, {len(raw)} runs", opus, "", "count", raw),
        ("T10", f"Dense tool, {len(dense)} runs", opus, "", "count", dense),
        ("T11", f"Dense tool, {cap} chunks per call", opus, "", "single", capped),
        ("T12", f"Text-to-SQL, {len(sql)} runs", opus, "", "query", sql),
        ("T13", f"Text-to-Cypher, {len(cypher)} runs", opus, "", "query", cypher),
        ("T14", "Text-to-SQL, schema", codex, "", "single", single("codex/chain_sql_{wg}_codex.jsonl")),
        ("T15a", "Text-to-SQL, value domains or exploration", codex, "value domains", "single",
         single("codex_v2/responses/{wg}_sql_dom_codex.jsonl")),
        ("T15b", "Text-to-SQL, value domains or exploration", codex, "exploration", "single",
         single("codex_v2/responses/{wg}_sql_exp_codex.jsonl")),
        ("T16", "Text-to-Cypher, schema", codex, "", "single", single("codex/chain_cy_{wg}_codex.jsonl")),
        ("T17a", "Text-to-Cypher, value domains or exploration", codex, "value domains", "single",
         single("codex_v2/responses/{wg}_cy_dom_codex.jsonl")),
        ("T17b", "Text-to-Cypher, value domains or exploration", codex, "exploration", "single",
         single("codex_v2/responses/{wg}_cy_exp_codex.jsonl")),
    ]


def read_run(paths: list[str], items: dict, qsha: dict) -> tuple[dict, dict]:
    """한 실행의 응답을 문항 id 로 모은다. 지금 문항에 없는 id 와 질문 해시가 다른 응답은 빼고, 같은 id 는 뒤 줄이 이긴다."""
    responses: dict[str, dict] = {}
    tally = {"lines": 0, "notInItems": 0, "staleQuestion": 0, "repeatedId": 0, "rowsNone": 0, "rowsAsString": 0}
    for path in paths:
        for record in jsonl(ROOT / path):
            tally["lines"] += 1
            identifier = record["id"]
            if identifier not in items:
                tally["notInItems"] += 1
                continue
            if record.get("questionSha256") != qsha[identifier]:
                tally["staleQuestion"] += 1
                continue
            if identifier in responses:
                tally["repeatedId"] += 1
            responses[identifier] = record
    tally["kept"] = len(responses)
    tally["itemsWithoutResponse"] = len(items) - len(responses)
    tally["rowsNone"] = sum(record.get("rows") is None for record in responses.values())
    tally["rowsAsString"] = sum(isinstance(record.get("rows"), str) for record in responses.values())
    return responses, tally


def grade(responses: dict, items: dict, row_key) -> tuple[dict, dict]:
    """문항마다 두 규칙의 정확 일치(응답이 없으면 틀림). 첫째는 채점기의 score, 둘째는 저장소의 same_meeting 판정."""
    primary, second = {}, {}
    for identifier, item in items.items():
        rows = responses[identifier].get("rows") if identifier in responses else None
        primary[identifier] = bool(score(item["gold"], rows)["exact"])
        second[identifier] = bool(SENS.exact(item, rows, row_key))
    return primary, second


def tabulate(exact: dict, items: dict, families: list[str], hops: list[str]) -> dict:
    by_family = {family: 0 for family in families}
    hops_answerable = {hop: 0 for hop in hops}
    hops_all = {hop: 0 for hop in hops}
    answerable = empty = 0
    for identifier, item in items.items():
        hit = int(exact[identifier])
        by_family[item["family"]] += hit
        hops_all[str(item["hops"])] += hit
        if item["expectsEmpty"]:
            empty += hit
        else:
            answerable += hit
            hops_answerable[str(item["hops"])] += hit
    return {"answerable": answerable, "emptyGold": empty, "all": answerable + empty, "family": by_family,
            "hopsAnswerable": hops_answerable, "hopsAllItems": hops_all}


def stat(values: list[int]) -> dict:
    """실행 평균. 합과 실행 수를 함께 남겨 정확한 값을 되찾을 수 있게 한다."""
    return {"sum": sum(values), "runs": len(values), "mean": sum(values) / len(values), "mean1": mean1(values),
            "min": min(values), "max": max(values)}


def over_runs(per_run: dict) -> dict:
    runs = list(per_run.values())
    out = {name: stat([run[name] for run in runs]) for name in ("answerable", "emptyGold", "all")}
    for group in ("family", "hopsAnswerable", "hopsAllItems"):
        out[group] = {key: stat([run[group][key] for run in runs]) for key in runs[0][group]}
    return out


def cli_groups(paths: list[str]) -> dict:
    """고치지 않은 채점기 CLI 를 한 번 불러 계열 · 홉 수별 정확 일치를 WG 파일에 걸쳐 더한다."""
    command = [sys.executable, "-B", str(ROOT / SCORER), "--items", *[str(ROOT / path) for path in ITEM_FILES],
               "--responses", *[str(ROOT / path) for path in paths], "--out", "/dev/stdout"]
    done = subprocess.run(command, capture_output=True, text=True, cwd=ROOT, check=True)
    report, _ = json.JSONDecoder().raw_decode(done.stdout)
    totals: dict[str, dict[str, int]] = {"family": collections.Counter(), "hops": collections.Counter(),
                                         "expectsEmpty": collections.Counter()}
    for run in report:
        for group in run["groups"]:
            if group["by"] in totals:
                totals[group["by"]][group["value"]] += group["exact"]
    return {by: dict(counter) for by, counter in totals.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, default=Path(DEFAULT_OUT), help="결과 JSON 경로(저장소 루트 기준)")
    parser.add_argument("--skip-cli-check", action="store_true", help="채점기 CLI 와의 대조를 건너뛴다")
    args = parser.parse_args()

    items = {item["id"]: item for path in ITEM_FILES for item in jsonl(ROOT / path)}
    qsha = {identifier: sha(item["question"]) for identifier, item in items.items()}
    answerable = [i for i, item in items.items() if not item["expectsEmpty"]]
    empty = [i for i, item in items.items() if item["expectsEmpty"]]
    families = sorted({item["family"] for item in items.values()})
    hops = sorted({str(item["hops"]) for item in items.values()})
    family_info = {}
    for family in families:
        members = [item for item in items.values() if item["family"] == family]
        family_info[family] = {"items": len(members), "hops": sorted({item["hops"] for item in members}),
                               "expectsEmpty": sorted({bool(item["expectsEmpty"]) for item in members}),
                               "byWg": dict(sorted(collections.Counter(item["wg"] for item in members).items()))}
    item_block = {
        "total": len(items), "answerable": len(answerable), "emptyGold": len(empty), "byFamily": family_info,
        "answerableByHops": {hop: sum(str(items[i]["hops"]) == hop for i in answerable) for hop in hops},
        "allByHops": {hop: sum(str(item["hops"]) == hop for item in items.values()) for hop in hops},
        "emptyGoldEqualsEmptyGoldList": set(empty) == {i for i, item in items.items() if not item["gold"]}}

    header, table = read_table(ROOT / MANUSCRIPT)
    kept = SENS.separately_recorded_meetings()
    row_key = SENS.make_row_key("same_meeting", kept)
    cap = json.loads((ROOT / CAP_RECORD).read_text())["cap"]
    listed = conditions(cap)

    reproduction, breakdown, not_reproduced, cli_check = [], {}, [], {}
    n_answerable, n_empty = len(answerable), len(empty)
    for cid, access, solver, sub, shape, runs in listed:
        row = table.get((access, solver))
        per_run = {"primary": {}, "second": {}}
        tallies, empty_responses = {}, 0
        for run, paths in runs.items():
            responses, tally = read_run(paths, items, qsha)
            tallies[run] = tally
            empty_responses += sum(identifier in responses for identifier in empty)
            primary, second = grade(responses, items, row_key)
            per_run["primary"][run] = tabulate(primary, items, families, hops)
            per_run["second"][run] = tabulate(second, items, families, hops)
            if not args.skip_cli_check:
                mine = per_run["primary"][run]
                seen = cli_groups(paths)
                expected = {"family": {f: c for f, c in mine["family"].items()},
                            "hops": {h: c for h, c in mine["hopsAllItems"].items()}}
                got = {"family": {f: seen["family"].get(f, 0) for f in families},
                       "hops": {h: seen["hops"].get(h, 0) for h in hops}}
                cli_check[f"{cid}:{run}"] = {"agrees": expected == got, **({} if expected == got else
                                                                           {"thisScript": expected, "cli": got})}
        got_answerable = {rule: answerable_cell(shape, [v["answerable"] for v in per_run[rule].values()], n_answerable)
                          for rule in per_run}
        empty_values = [v["emptyGold"] for v in per_run["primary"].values()]
        got_empty = "--" if empty_responses == 0 else count_cell(empty_values, n_empty)
        table_cells = None if row is None else {name: row.get(name) for name in ("Answerable", "Second rule", "Empty-gold")}
        status = {}
        if row is None:
            status = {"primary": "table row not found", "second": "table row not found"}
        else:
            primary_ok = (leading_count(row.get("Answerable")) == got_answerable["primary"]
                          and row.get("Empty-gold") == got_empty)
            second_ok = leading_count(row.get("Second rule")) == got_answerable["second"]
            status = {"primary": "reproduced" if primary_ok else "not reproduced",
                      "second": "reproduced" if second_ok else "not reproduced"}
        entry = {
            "id": cid, "access": access, "solver": solver, "condition": sub, "shape": shape,
            "runs": {run: paths for run, paths in runs.items()},
            "table": table_cells,
            "reproduced": {"Answerable": got_answerable["primary"], "Second rule": got_answerable["second"],
                           "Empty-gold": got_empty},
            "perRun": {rule: {run: {name: v[name] for name in ("answerable", "emptyGold", "all")}
                              for run, v in per_run[rule].items()} for rule in per_run},
            "emptyGoldResponsesStored": empty_responses,
            "status": status, "responseTally": tallies}
        reproduction.append(entry)
        breakdown[cid] = {}
        for rule in ("primary", "second"):
            if status[rule] == "reproduced":
                breakdown[cid][rule] = {"perRun": per_run[rule], "overRuns": over_runs(per_run[rule])}
            else:
                not_reproduced.append({"id": cid, "rule": rule, "access": access, "solver": solver, "condition": sub,
                                       "table": table_cells, "obtained": entry["reproduced"]})

    covered = {(access, solver) for _, access, solver, *_ in listed}
    result = {
        "description": "tab:results 의 조건별 정확 일치를 문항 계열 · 홉 수로 나눈 표. 조건마다 표 칸을 응답에서 먼저 다시 "
                       "만들어 원고와 견주고(reproduction), 같은 조건만 나눈다(breakdown). 구간(Wilson)은 다시 만들지 "
                       "않고 `k/n` 앞부분만 견준다.",
        "inputs": {"manuscript": MANUSCRIPT, "items": list(ITEM_FILES), "primaryRuleScorer": f"{SCORER}::score",
                   "secondRuleScorer": f"{SECOND_RULE_SCORER}::make_row_key('same_meeting', kept) · exact",
                   "denseToolCapRecord": CAP_RECORD},
        "rules": {"primary": "기록 표기 규칙. score(gold, rows)['exact'], 응답이 없으면 틀림",
                  "second": "같은 회의 규칙. 회의 열의 끝 '-e' 를 양쪽에서 떼되 기록이 따로 담은 회의 이름은 둔다",
                  "secondRuleKeptMeetings": sorted(kept),
                  "responseFilter": "id 가 지금 문항에 있고 questionSha256 이 지금 질문의 sha256 과 같은 줄만, 같은 id 는 뒤 줄"},
        "items": item_block,
        "tableHeader": header,
        "tableRowsNotCovered": sorted(f"{a} | {s}" for a, s in set(table) - covered),
        "reproduction": reproduction,
        "notReproduced": not_reproduced,
        "breakdown": breakdown,
        "cliCrossCheck": {"skipped": args.skip_cli_check,
                          "what": "채점기 CLI(--out /dev/stdout)의 family · hops 묶음 exact 합이 이 스크립트의 기록 표기 집계와 "
                                  "같은가. CLI 의 hops 묶음은 빈 정답 문항을 1홉에 함께 센다(hopsAllItems 와 견준다).",
                          "runsChecked": len(cli_check),
                          "runsAgreeing": sum(v["agrees"] for v in cli_check.values()),
                          "disagreements": {k: v for k, v in cli_check.items() if not v["agrees"]}},
    }
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"items {len(items)} answerable {n_answerable} emptyGold {n_empty}; kept meetings {sorted(kept)}")
    for entry in reproduction:
        cells = entry["table"] or {}
        print(f"{entry['id']:5} {entry['status']['primary']:15} {entry['status']['second']:15} "
              f"A table={leading_count(cells.get('Answerable'))!s:18} got={entry['reproduced']['Answerable']:18} "
              f"S table={leading_count(cells.get('Second rule'))!s:18} got={entry['reproduced']['Second rule']:18} "
              f"E table={cells.get('Empty-gold')!s:14} got={entry['reproduced']['Empty-gold']}")
    print(f"cli cross-check: {result['cliCrossCheck']['runsAgreeing']}/{result['cliCrossCheck']['runsChecked']} runs agree")
    print(f"not reproduced: {len(not_reproduced)}; table rows not covered: {result['tableRowsNotCovered']}")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
