"""링크를 한 번 물질화하는 경로와 질문마다 문서에서 이끌어 내는 경로의 비용을 기록 파일에서 나란히 계산한다 (모델 호출 없음).

입력
1. `final/next_cycle/cost/agent_session_cost.json` (`measure_agent_session_cost.py` 결과): 조건별 세션의 토큰 · 도구 호출 ·
   벽시계 초와 채점에 들어간 답 수.
2. `final/next_cycle/build_cost/{WG}.time.txt` 와 `{WG}.compare.json`: 처분 단계 재구축의 `/usr/bin/time -v` 기록과
   저장본 대조 결과. 재구축이 저장본과 같은 WG 만 구축 비용에 넣는다.

3. `chain_eval/subagent_model_provenance.json`: 세션마다 맡은 문항 수를 정한다. 비용 기록의 세션 순서는 이 파일의
   조건 → WG → 세션 순서와 같다. 문서 경로 세션은 프롬프트가 가리키는 묶음 파일(`parts/*.json`)의 `items` 수,
   기록 질의 세션은 그 WG · 실행의 답 파일 줄 수다. 세션 문항 수의 합이 조건의 답 수와 다르면 멈춘다.
4. 기록 질의 경로의 실행 기록(`EXEC`): 하위 에이전트가 쓴 질의를 세션이 끝난 뒤 실행기(`run_chain_eval.py`)가
   SQLite · Neo4j 에서 실행하고 문항마다 남긴 `seconds`. 지금 문항 집합에 있고 `questionSha256` 이 지금 질문과 같은
   줄만 센다. 센 줄 수가 세션 문항 수와 다르면 멈춘다.

조건 묶음은 `GROUPS` 가 정한다. 토큰과 도구 호출의 문항당 값은 세션 합을 답 수 합으로 나눈 값이다.
입력 토큰은 새 입력 · 캐시 쓰기 · 캐시 읽기를 모두 더한 처리량이다.
문항당 초는 세션마다 (세션 초 ÷ 세션 문항 수) 를 구한 뒤 묶음 안 세션의 중앙값으로 둔다. 세션 초는 첫 기록과 마지막
기록 사이의 벽시계 시간이라, 세션 하나가 대기로 멈춘 시간이 합에 그대로 들어간다. 중앙값은 그런 세션 하나에
흔들리지 않으므로 잘라 낼 기준값을 따로 정하지 않는다. 합 ÷ 답 수 값도 `secondsMean` 으로 함께 남긴다.
문서 경로 세션은 검색 도구 실행을 세션 안에서 하므로 세션 초에 실행 시간이 이미 들어 있다. 기록 질의 경로는 질의 실행이
세션 밖에 있으므로 세션의 실행 초 합을 세션 초에 더한 뒤 같은 방식으로 문항당 초를 구한다. 질의를 쓰는 데만 든 값은
`writeSeconds` 로, 실행 초의 합 ÷ 답 수는 `executionSecondsMean` 으로 따로 남긴다.

손익분기 문항 수 = 다섯 WG 처분 단계의 벽시계 초 합 ÷ (문서 경로의 문항당 초 − 기록 질의 경로의 문항당 초).
같은 식을 `secondsMean` 으로 계산한 값도 `itemsByMean` 으로 남긴다(멈춘 세션이 평균을 끌어올리는 정도를 보인다).
두 경로 모두 문서에서 뽑아 둔 본문 텍스트에서 출발하므로 그 추출 비용은 양쪽에 같아 넣지 않는다.

사용 (저장소 루트에서 실행):
  python3 measure_materialize_vs_derive.py --next-cycle <logs/.../final/next_cycle> --out <json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
from pathlib import Path

WGS = ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")
GROUPS = {
    "text2sql": ["text2sql_runA_runB", "text2sql_runs_C_to_E", "text2sql_runs_F_to_J"],
    "text2cypher": ["text2cypher_runA_runB", "text2cypher_runs_C_to_E", "text2cypher_runs_F_to_J"],
    "text_search": ["text_search", "text_search_runB", "text_search_runC"],
    "text_only": ["text_search_text_only", "text_search_text_only_runB", "text_search_text_only_runC"],
    "raw_text": ["raw_index_runA", "raw_index_runB"],
    "dense_tool": ["dense_tool_runA", "dense_tool_runB"],
    "dense_capped": ["dense_tool_capped_runA"],
}
MATERIALIZED = ("text2sql", "text2cypher")
DERIVED = "raw_text"


QW = "subagent_queries"
QW_KIND = {"text2sql": "text2sql", "text2cypher": "text2cypher"}
EXEC = {"text2sql": "chain_eval/text2sql/{wg}_text2sql_{run}.jsonl",
        "text2cypher": "chain_eval/{wg}_text2cypher_claude_subagent_{run}.jsonl"}
ITEM_FILES = ("integration/items_final/gate/core/chain_items_admitted.jsonl",
              "integration/items_final/gate/ran5/chain_items_admitted.jsonl")


def current_questions(base: Path) -> dict[str, str]:
    """지금 문항 id → 지금 질문 문장의 sha256."""
    out = {}
    for name in ITEM_FILES:
        for line in (base / name).read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                out[item["id"]] = hashlib.sha256(item["question"].encode()).hexdigest()
    return out


def execution_seconds(base: Path, kind: str, wg: str, run: str, qsha: dict[str, str]) -> tuple[float, int]:
    """기록 질의 세션 하나의 질의를 실행기가 실행한 시간의 합과 그 줄 수."""
    total, counted = 0.0, 0
    path = base / EXEC[kind].format(wg=wg, run=run)
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if qsha.get(record["id"]) == record.get("questionSha256"):
            total += record["seconds"]
            counted += 1
    return total, counted


def session_items(base: Path, cond: str, wg: str, entry: dict) -> int:
    """세션 하나가 맡은 문항 수. base 는 chain_eval/ 를 담은 논문 logs 디렉토리."""
    kind = next((k for k in QW_KIND if cond.startswith(k + "_")), None)
    if kind:
        f = base / "chain_eval" / QW / f"{wg}_{kind}_{entry['run']}.jsonl"
        return sum(1 for line in f.read_text(encoding="utf-8").splitlines() if line.strip())
    prompt = (base / "chain_eval" / entry["prompt"]).read_text(encoding="utf-8")
    parts = sorted(set(re.findall(r"[\w./-]+/parts/[\w.-]+\.json", prompt)))
    if len(parts) != 1:
        raise SystemExit(f"{cond} {wg} {entry['prompt']}: expected one packet part, found {parts}")
    return len(json.loads(Path(parts[0]).read_text(encoding="utf-8"))["items"])


def group_cost(conds: dict, prov: dict, base: Path, names: list[str], kind: str | None, qsha: dict) -> dict:
    """kind 가 기록 질의 경로(text2sql · text2cypher)면 세션 밖의 질의 실행 시간을 세션 초에 더한다."""
    tot = {"items": 0, "sessions": 0, "input": 0, "output": 0, "tools": 0, "seconds": 0.0, "executionSeconds": 0.0}
    rates, write_rates = [], []
    for n in names:
        t = conds[n]["total"]
        if t["missing"]:
            raise SystemExit(f"{n}: {t['missing']} sessions without a transcript")
        entries = [(wg, e) for wg, es in prov[n].items() for e in es]
        sessions = conds[n]["sessions"]
        if len(entries) != len(sessions):
            raise SystemExit(f"{n}: {len(entries)} provenance entries, {len(sessions)} cost sessions")
        counted = 0
        for (wg, e), s in zip(entries, sessions):
            if s["wg"] != wg or s.get("run") != e.get("run"):
                raise SystemExit(f"{n}: session order differs at {wg} {e.get('run')}")
            k = session_items(base, n, wg, e)
            counted += k
            executed = 0.0
            if kind:
                executed, lines = execution_seconds(base, kind, wg, e["run"], qsha)
                if lines != k:
                    raise SystemExit(f"{n} {wg} {e['run']}: {lines} executed answers, session holds {k}")
            tot["executionSeconds"] += executed
            write_rates.append(s["seconds"] / k)
            rates.append((s["seconds"] + executed) / k)
        if counted != t["items"]:
            raise SystemExit(f"{n}: sessions cover {counted} items, answers hold {t['items']}")
        tok = t["tokens"]
        tot["items"] += t["items"]
        tot["sessions"] += t["sessions"]
        tot["input"] += tok["input"] + tok["cacheWrite"] + tok["cacheRead"]
        tot["output"] += tok["output"]
        tot["tools"] += t["tools"]
        tot["seconds"] += t["seconds"]
    per = {k: tot[k] / tot["items"] for k in ("input", "output", "tools")}
    q1, med, q3 = statistics.quantiles(rates, n=4, method="inclusive")
    per["seconds"] = med
    per["secondsMean"] = (tot["seconds"] + tot["executionSeconds"]) / tot["items"]
    per["secondsQuartiles"] = [q1, q3]
    per["secondsRange"] = [min(rates), max(rates)]
    if kind:
        per["writeSeconds"] = statistics.median(write_rates)
        per["executionSecondsMean"] = tot["executionSeconds"] / tot["items"]
    return {"conditions": names, **tot, "perItem": per}


def wg_build(bc: Path, wg: str) -> dict | None:
    cmp, tm = bc / f"{wg}.compare.json", bc / f"{wg}.time.txt"
    if not cmp.exists() or not tm.exists():
        return None
    c = json.loads(cmp.read_text())
    t = tm.read_text()
    m = re.search(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): (?:(\d+):)?(\d+):(\d+\.\d+)", t)
    rss = re.search(r"Maximum resident set size \(kbytes\): (\d+)", t)
    cpu = re.search(r"Percent of CPU this job got: (\d+)%", t)
    if not m or not rss:
        return None
    wall = int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    identical = not (c["onlyRebuilt"] or c["onlyStored"] or c["contentDiffers"]) and c["rebuiltRecords"] == c["storedRecords"]
    return {"records": c["storedRecords"], "identical": identical, "wallSeconds": wall,
            "maxRssGB": int(rss.group(1)) * 1024 / 1e9, "cpuPercent": int(cpu.group(1)) if cpu else None,
            "modelTokens": 0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--next-cycle", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    nc = Path(a.next_cycle)
    cost = json.loads((nc / "cost" / "agent_session_cost.json").read_text())
    conds = cost["conditions"]
    prov_path = Path(cost["provenance"])
    base = prov_path.parents[1]
    prov = json.loads(prov_path.read_text(encoding="utf-8"))["conditions"]
    qsha = current_questions(base)
    routes = {g: group_cost(conds, prov, base, names, g if g in MATERIALIZED else None, qsha)
              for g, names in GROUPS.items()}
    build = {wg: wg_build(nc / "build_cost", wg) for wg in WGS}
    complete = all(b and b["identical"] for b in build.values())
    out = {"routes": routes, "build": build, "buildComplete": complete}
    if complete:
        wall = sum(b["wallSeconds"] for b in build.values())
        out["buildTotal"] = {"wallSeconds": wall, "records": sum(b["records"] for b in build.values()),
                             "maxRssGB": max(b["maxRssGB"] for b in build.values()), "modelTokens": 0}
        out["breakEven"] = {}
        for g in MATERIALIZED:
            saved = routes[DERIVED]["perItem"]["seconds"] - routes[g]["perItem"]["seconds"]
            saved_mean = routes[DERIVED]["perItem"]["secondsMean"] - routes[g]["perItem"]["secondsMean"]
            out["breakEven"][g] = {"derivedRoute": DERIVED, "secondsSavedPerItem": saved,
                                   "items": wall / saved,
                                   "secondsSavedPerItemByMean": saved_mean, "itemsByMean": wall / saved_mean,
                                   "inputTokenRatio": routes[DERIVED]["perItem"]["input"] / routes[g]["perItem"]["input"]}
    Path(a.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    for g, r in routes.items():
        p = r["perItem"]
        print(f"{g:13s} items={r['items']:6d} in={p['input']:9.0f} out={p['output']:6.0f} tools={p['tools']:5.2f} s={p['seconds']:6.2f} q={p['secondsQuartiles'][0]:.2f}..{p['secondsQuartiles'][1]:.2f} mean={p['secondsMean']:6.2f}")
    for wg, b in build.items():
        print(wg, b)
    if complete:
        print("buildTotal", out["buildTotal"])
        print("breakEven", out["breakEven"])


if __name__ == "__main__":
    main()
