"""반복 질의 작성 실행을 사전 분석 계획(final/repeated_runs/analysis_plan.json)대로 집계한다 (모델 호출 없음).

대상 풀이는 계획의 두 풀이(claude_text2cypher · claude_text2sql)이고, Codex 의 Cypher · SQL 한 번 실행
(codex_text2cypher · codex_text2sql)을 함께 낸다. 실행은 있는 만큼 쓴다. 한 실행은 다섯 작업반의 응답 파일이 모두 있고
667 문항 모두에 현재 질문의 응답이 있을 때만 풀이 평균에 넣는다. 넣지 못한 실행은 까닭과 함께 따로 적는다.

- 문항 채점은 `score_chain_eval.score` 다. 질문 SHA-256 이 현재 질문과 다른 응답(staleQuestion)은 빼고 그 수를 적는다.
- 주 지표: 첫 질의의 정확 일치. 실행마다 667 · 정답 있는 581 · 빈 정답 86 문항의 정확 일치 수를 세고,
  풀이마다 실행 평균 비율과 실행 사이 최소 · 최대를 낸다.
- 구간: 35개 (wg, family) 군집을 복원 추출하고 뽑힌 군집의 모든 문항 · 모든 실행을 함께 넣는 군집 부트스트랩의
  백분위 95% 구간(667 문항의 실행 평균 정확 일치 비율). 반복 10,000회, 씨앗 20261112.
  군집 재추출은 씨앗에서 한 번 뽑아 모든 풀이와 모든 비교에 같이 쓴다.
- 풀이 비교: 실행 평균 정확 일치 비율의 차(앞 풀이 − 뒤 풀이)와 같은 군집 재추출로 낸 짝 군집 부트스트랩 95% 구간.
  claude_text2cypher − claude_text2sql, claude_text2cypher − codex_text2cypher, claude_text2sql − codex_text2sql.
  구간이 0 을 품는 차이는 구간으로 적고 같다는 뜻으로 읽지 않는다.
- repaired: 같은 값을 기록된 다시 쓴 회차 뒤의 응답으로 다시 낸다. 응답 파일 `<이름>_repair.jsonl` 이 있으면 그
  작업반의 응답을 그것으로 바꾸고, 없으면 첫 질의 응답을 그대로 쓴다(다시 쓴 회차가 없거나 실행 오류가 없던 경우).
  바꾼 파일마다 첫 질의와 첫 질의가 성공한 문항의 결과 행이 주 지표 응답과 같은지 센다. 실행 오류로 답이 없는 문항이
  있는데 다시 쓴 회차 응답이 없는 파일은 그 수와 함께 errorsWithoutRepairRound 에 적는다(그 작업반의 repaired 값은 주 지표와 같다).

사용: python3 summarize_repeated_runs.py [--out <json>]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path

import numpy as np

from score_chain_eval import score

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
L = "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
PLAN = f"{L}/final/repeated_runs/analysis_plan.json"
RESAMPLES = 10_000
SEED = 20261112
WGS = ["RAN1", "RAN2", "RAN3", "RAN4", "RAN5"]
CLUSTERS = 35
SUBSETS = ("all", "answerable", "emptyGold")
COMPARISONS = [("claude_text2cypher", "claude_text2sql"),
               ("claude_text2cypher", "codex_text2cypher"),
               ("claude_text2sql", "codex_text2sql")]


def response_files(method: str, run: str) -> list[str]:
    if method == "claude_text2cypher":
        return [f"{L}/chain_eval/{wg}_text2cypher_claude_subagent_{run}.jsonl" for wg in WGS]
    if method == "claude_text2sql":
        return [f"{L}/chain_eval/text2sql/{wg}_text2sql_{run}.jsonl" for wg in WGS]
    language = {"codex_text2cypher": "cy", "codex_text2sql": "sql"}[method]
    return [f"{L}/chain_eval/codex/chain_{language}_{wg}_codex.jsonl" for wg in WGS]


def repaired_file(path: str) -> str | None:
    candidate = path.removesuffix(".jsonl") + "_repair.jsonl"
    return candidate if (ROOT / candidate).exists() else None


def first_query(record: dict) -> str | None:
    attempts = record.get("attempts") or []
    return (attempts[0].get("cypher") or attempts[0].get("sql")) if attempts else None


def read_run(files: list[str], items: dict, digest: dict, language: str, model: str | None) -> dict:
    """응답 파일들을 읽어 문항 id → 응답 기록 표와 그 실행의 확인 값을 돌려준다."""
    answered: dict[str, dict] = {}
    stale = unknown = 0
    labels = set()
    for path in files:
        for record in map(json.loads, (ROOT / path).read_text().splitlines()):
            labels.add((record.get("method"), record.get("model")))
            if record["id"] not in items:
                unknown += 1
                continue
            if record.get("questionSha256") != digest[record["id"]]:
                stale += 1
                continue
            if record["id"] in answered:
                raise SystemExit(f"{path}: 같은 문항 {record['id']} 의 응답이 두 번 있다")
            answered[record["id"]] = record
    problems = []
    models = {label[1] for label in labels}
    if {label[0] for label in labels} != {language}:
        problems.append(f"method 칸 {sorted(map(str, {label[0] for label in labels}))}")
    if len(models) != 1 or (model is not None and models != {model}):
        problems.append(f"model 칸 {sorted(map(str, models))}")
    return {"answered": answered, "staleQuestion": stale, "unknownIds": unknown,
            "model": sorted(map(str, models))[0] if len(models) == 1 else sorted(map(str, models)), "problems": problems}


def subset_of(item: dict) -> str:
    return "answerable" if item["gold"] else "emptyGold"


def run_counts(read: dict, items: dict) -> dict:
    exact = collections.Counter()
    scored = collections.Counter()
    for identifier, record in read["answered"].items():
        part = subset_of(items[identifier])
        hit = score(items[identifier]["gold"], record.get("rows"))["exact"]
        for subset in ("all", part):
            exact[subset] += hit
            scored[subset] += 1
    records = read["answered"].values()
    return {"exact": {subset: exact[subset] for subset in SUBSETS},
            "items": {subset: scored[subset] for subset in SUBSETS},
            "missing": len(items) - len(read["answered"]),
            "staleQuestion": read["staleQuestion"], "unknownIds": read["unknownIds"],
            "noRows": sum(record.get("rows") is None for record in records),
            "attemptsBeyondFirst": sum(max(len(record.get("attempts") or []) - 1, 0) for record in records)}


def no_rows(path: Path) -> int:
    """응답 파일에서 실행 오류로 결과 행이 없는 레코드 수."""
    return sum(json.loads(line).get("rows") is None for line in path.read_text().splitlines())


def compare_repaired(primary: Path, repaired: Path) -> dict:
    """다시 쓴 회차 응답이 첫 질의 응답과 첫 질의 · 첫 질의가 성공한 문항의 결과 행에서 같은지 센다."""
    first = {r["id"]: r for r in map(json.loads, primary.read_text().splitlines())}
    second = {r["id"]: r for r in map(json.loads, repaired.read_text().splitlines())}
    shared = sorted(set(first) & set(second))
    succeeded = [i for i in shared if first[i].get("rows") is not None]
    return {"primary": str(primary.relative_to(ROOT)), "repaired": str(repaired.relative_to(ROOT)),
            "idsOnlyInOne": len(set(first) ^ set(second)),
            "firstQueryDiffers": sum(first_query(first[i]) != first_query(second[i]) for i in shared),
            "firstAttemptSucceeded": len(succeeded),
            "rowsDifferWhereFirstSucceeded": sum(first[i]["rows"] != second[i]["rows"] for i in succeeded),
            "noRowsBefore": sum(first[i].get("rows") is None for i in shared),
            "noRowsAfter": sum(second[i].get("rows") is None for i in shared),
            "repairedItems": sum(len(second[i].get("attempts") or []) > 1 for i in shared)}


def summarize(runs: dict, items: dict, cluster_of: dict, cluster_names: list, resample: np.ndarray) -> dict:
    """풀이마다 실행별 수 · 실행 평균 · 최소 최대 · 군집 부트스트랩 구간, 그리고 풀이 비교를 낸다."""
    methods, rates, point = {}, {}, {}
    for method, entries in runs.items():
        pooled = [entry for entry in entries if entry["pooled"]]
        result = {"runs": [{k: v for k, v in entry.items() if k != "read"} for entry in entries],
                  "runsPooled": [entry["run"] for entry in pooled]}
        if pooled:
            result["meanExactCount"] = {s: round(sum(e["exact"][s] for e in pooled) / len(pooled), 4) for s in SUBSETS}
            result["meanExactRate"] = {s: round(sum(e["exact"][s] for e in pooled) / sum(e["items"][s] for e in pooled), 4)
                                       for s in SUBSETS}
            for name, pick in (("minExact", min), ("maxExact", max)):
                result[name] = {}
                for s in SUBSETS:
                    value = pick(e["exact"][s] for e in pooled)
                    result[name][s] = {"count": value, "of": pooled[0]["items"][s],
                                       "runs": [e["run"] for e in pooled if e["exact"][s] == value]}
            hits = np.zeros(len(cluster_names))
            totals = np.zeros(len(cluster_names))
            for entry in pooled:
                for identifier, record in entry["read"]["answered"].items():
                    c = cluster_of[identifier]
                    hits[c] += score(items[identifier]["gold"], record.get("rows"))["exact"]
                    totals[c] += 1
            rate = hits[resample].sum(axis=1) / totals[resample].sum(axis=1)
            rates[method] = rate
            point[method] = hits.sum() / totals.sum()
            result["clusterBootstrap95"] = [round(float(x), 4) for x in np.percentile(rate, [2.5, 97.5])]
        methods[method] = result
    comparisons = []
    for first, second in COMPARISONS:
        if first not in rates or second not in rates:
            comparisons.append({"first": first, "second": second, "available": False})
            continue
        difference = rates[first] - rates[second]
        observed = float(point[first] - point[second])
        low, high = (round(float(x), 4) for x in np.percentile(difference, [2.5, 97.5]))
        comparisons.append({"first": first, "second": second, "available": True,
                            "runsFirst": methods[first]["runsPooled"], "runsSecond": methods[second]["runsPooled"],
                            "meanExactRateDifference": round(observed, 4),
                            "pairedClusterBootstrap95": [low, high], "intervalExcludesZero": low > 0 or high < 0})
    return {"methods": methods, "comparisons": comparisons}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, default=ROOT / L / "final/repeated_runs/summary_available.json")
    parser.add_argument("--plan", type=Path, default=ROOT / PLAN, help="회차 목록을 담은 사전 분석 계획 (기본: 다섯 회차 계획)")
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    items = {item["id"]: item for path in plan["items"] for item in map(json.loads, (ROOT / path).read_text().splitlines())}
    digest = {identifier: hashlib.sha256(item["question"].encode()).hexdigest() for identifier, item in items.items()}
    counts = {"all": len(items), "answerable": sum(bool(i["gold"]) for i in items.values()),
              "emptyGold": sum(not i["gold"] for i in items.values())}
    if (counts["all"], counts["answerable"], counts["emptyGold"]) != (plan["itemCount"], plan["answerableItems"],
                                                                         plan["emptyGoldItems"]):
        raise SystemExit(f"문항 수가 계획과 다르다: {counts}")
    cluster_names = sorted({(item["wg"], item["family"]) for item in items.values()})
    if len(cluster_names) != CLUSTERS:
        raise SystemExit(f"군집 수가 계획과 다르다: {len(cluster_names)}")
    index = {name: c for c, name in enumerate(cluster_names)}
    cluster_of = {identifier: index[(item["wg"], item["family"])] for identifier, item in items.items()}
    resample = np.random.default_rng(SEED).integers(0, len(cluster_names), size=(RESAMPLES, len(cluster_names)))

    methods = {name: [(run, f"claude-opus-subagent-{run}") for run in names] for name, names in plan["runs"].items()}
    methods["codex_text2cypher"] = [("single", None)]
    methods["codex_text2sql"] = [("single", None)]
    language = {name: "text2sql" if name.endswith("text2sql") else "text2cypher" for name in methods}
    blocks = {"primary": {}, "repaired": {}}
    not_present, substitutions = [], []
    for method, runs in methods.items():
        for block in blocks.values():
            block[method] = []
        for run, model in runs:
            files = response_files(method, run)
            present = [path for path in files if (ROOT / path).exists()]
            if not present:
                not_present.append({"method": method, "run": run})
                continue
            for name, paths in (("primary", files), ("repaired", [repaired_file(p) or p for p in files])):
                entry = {"run": run, "responses": [p for p in paths if (ROOT / p).exists()],
                         "missingResponseFiles": [p for p in paths if not (ROOT / p).exists()]}
                read = read_run(entry["responses"], items, digest, language[method], model)
                entry.update({"model": read["model"], **run_counts(read, items)})
                if name == "repaired":
                    entry["repairResponseFiles"] = [p for p in paths if p not in files]
                    entry["errorsWithoutRepairRound"] = [
                        {"responses": p, "noRows": no_rows(ROOT / p)} for p in files
                        if (ROOT / p).exists() and not repaired_file(p) and no_rows(ROOT / p)]
                reasons = list(read["problems"])
                if entry["missingResponseFiles"]:
                    reasons.append(f"응답 파일 없음 {len(entry['missingResponseFiles'])}")
                if entry["missing"]:
                    reasons.append(f"현재 질문의 응답이 없는 문항 {entry['missing']}")
                if name == "primary" and entry["attemptsBeyondFirst"]:
                    reasons.append(f"첫 질의 뒤의 시도 {entry['attemptsBeyondFirst']}")
                entry["pooled"] = not reasons
                if reasons:
                    entry["notPooledBecause"] = reasons
                entry["read"] = read
                blocks[name][method].append(entry)
            for path in files:
                if repaired_file(path) and (ROOT / path).exists():
                    substitutions.append(compare_repaired(ROOT / path, ROOT / repaired_file(path)))

    report = {
        "plan": str(args.plan.resolve().relative_to(ROOT)), "planSha256": hashlib.sha256(args.plan.read_bytes()).hexdigest(),
        "items": plan["items"], "itemCounts": counts,
        "clusters": [{"wg": wg, "family": family, "items": sum(c == index[(wg, family)] for c in cluster_of.values())}
                     for wg, family in cluster_names],
        "bootstrap": {"resamples": RESAMPLES, "seed": SEED, "unit": "(wg, family) cluster", "interval": "percentile 95%",
                      "sharedResamples": "one cluster resample matrix drawn once and used for every method and comparison"},
        "runsUsed": {method: [e["run"] for e in entries if e["pooled"]] for method, entries in blocks["primary"].items()},
        "runsNotPresent": not_present,
        "primary": summarize(blocks["primary"], items, cluster_of, cluster_names, resample),
        "repaired": {**summarize(blocks["repaired"], items, cluster_of, cluster_names, resample),
                     "repairResponseChecks": substitutions},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")

    print("사용한 실행:", "; ".join(f"{m} {','.join(r) or '없음'}" for m, r in report["runsUsed"].items()))
    if not_present:
        print("응답 파일이 없는 실행:", ", ".join(f"{e['method']} {e['run']}" for e in not_present))
    for name in ("primary", "repaired"):
        print(f"[{name}]")
        for method, result in report[name]["methods"].items():
            for entry in result["runs"]:
                e, n = entry["exact"], entry["items"]
                flag = "" if entry["pooled"] else f"  (평균에서 뺌: {'; '.join(entry['notPooledBecause'])})"
                print(f"  {method} {entry['run']}: {e['all']}/{n['all']} · 정답 있음 {e['answerable']}/{n['answerable']}"
                      f" · 빈 정답 {e['emptyGold']}/{n['emptyGold']} · 답 없음 {entry['noRows']}"
                      f" · stale {entry['staleQuestion']}{flag}")
                for left in entry.get("errorsWithoutRepairRound", []):
                    print(f"    다시 쓴 회차 없이 실행 오류 {left['noRows']}: {left['responses']}")
            if result["runsPooled"]:
                print(f"  {method} 평균 {result['meanExactRate']['all']} (실행 {len(result['runsPooled'])}개,"
                      f" 최소 {result['minExact']['all']['count']} · 최대 {result['maxExact']['all']['count']}),"
                      f" 군집 부트스트랩 95% {result['clusterBootstrap95']}")
        for c in report[name]["comparisons"]:
            if c["available"]:
                print(f"  {c['first']} − {c['second']}: {c['meanExactRateDifference']} 짝 군집 부트스트랩 95%"
                      f" {c['pairedClusterBootstrap95']}")
    for check in substitutions:
        print(f"다시 쓴 회차 응답 {check['repaired']}: 첫 질의가 다른 문항 {check['firstQueryDiffers']},"
              f" 첫 질의가 성공한 {check['firstAttemptSucceeded']} 문항 중 결과 행이 다른 문항"
              f" {check['rowsDifferWhereFirstSucceeded']}, 답 없음 {check['noRowsBefore']} → {check['noRowsAfter']}")
    print("저장:", args.out.resolve().relative_to(ROOT) if args.out.resolve().is_relative_to(ROOT) else args.out)


if __name__ == "__main__":
    main()
