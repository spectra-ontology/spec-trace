"""반복 질의 작성 실행에서 틀린 문항이 (wg, family) 군집에 어떻게 몰려 있는지 센다 (모델 호출 없음).

`summarize_repeated_runs.py` 가 쓴 요약(final/repeated_runs/summary_runs_A_to_E.json)의 `primary` 에 적힌
실행마다의 응답 파일을 그대로 읽는다. 문항 채점은 `score_chain_eval.score` 의 정확 일치다.
질문 SHA-256 이 현재 질문과 다른 응답(staleQuestion)은 틀린 것으로 세지 않고 그 수를 따로 적는다.

실행마다 다음을 낸다.
- misses: 정확 일치가 아닌 문항 수(응답 없음 · 실행 오류 포함).
- missesInFullyMissedClusters: 그 실행이 군집의 모든 문항을 틀린 군집들에 속한 틀린 문항 수.
  fullyMissedClusters 는 그 군집 목록과 문항 수다.
- partialClusters: 일부 문항만 틀린 군집과 (틀린 수, 군집 문항 수).
- recoveredByMeetingSuffix: 틀린 문항 가운데 회의 칸의 끝 `-e` 를 양쪽에서 떼면 일치하는 문항 수
  (`score_meeting_suffix_insensitive.py` 와 같은 규칙). recoveredInFullyMissedClusters 는 그 가운데
  모든 문항을 틀린 군집에 속한 수다.
- otherMisses: 모든 문항을 틀린 군집 밖에 있으면서 `-e` 규칙으로도 일치하지 않는 문항의 id 와 군집.
- causes: 틀린 문항마다 하나의 원인 범주를 붙여 센다. 차례대로 처음 맞는 범주를 쓴다.
  timeout(실행 시간 상한에 걸려 중단됨, 오류 문구 `interrupted` 또는 시간 초과) ·
  executionError:<오류 코드>(그 밖의 실행 오류) · meetingSuffix(`-e` 규칙으로 일치) ·
  emptyWithoutStoredScope(빈 결과이고, SQL 질의가 `scope` 칸을 거르면서 그 칸에 저장된 값 `whole_target` 을
  적지 않음. 그래프에서는 범위가 다른 속성에 저장되므로 Cypher 질의에는 이 검사를 걸지 않는다) ·
  emptyResult(그 밖의 빈 결과) · otherRows(다른 행).

사용: python3 summarize_repeated_run_misses.py [--summary <json>] [--out <json>]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path

from score_chain_eval import score
from score_meeting_suffix_insensitive import matches

ROOT = next(path for path in Path(__file__).resolve().parents if (path / ".git").exists())
TRACK = ROOT / "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
DEFAULT_SUMMARY = TRACK / "final/repeated_runs/summary_runs_A_to_E.json"
DEFAULT_OUT = TRACK / "final/repeated_runs/miss_clusters.json"


def question_sha(item: dict) -> str:
    return hashlib.sha256(item["question"].encode("utf-8")).hexdigest()


STORED_SCOPE = "whole_target"


def miss_cause(item: dict, response: dict | None) -> str:
    """틀린 문항 하나의 원인 범주(모듈 docstring 의 causes 차례)."""
    if response is None:
        return "noResponse"
    rows = response.get("rows")
    attempts = response.get("attempts") or [{}]
    first = attempts[0]
    if rows is None:
        error = str(first.get("error") or "")
        if "interrupted" in error or "timeout" in error.lower() or "timed out" in error.lower():
            return "timeout"
        code = error.split("}", 1)[0].removeprefix("{code: ").strip() if error.startswith("{code:") else "other"
        return f"executionError:{code}"
    if matches(item, rows, strip=True):
        return "meetingSuffix"
    if not rows:
        compact = str(first.get("sql") or "").lower().replace("_", "").replace("-", "").replace(" ", "")
        if "scope" in compact and STORED_SCOPE.replace("_", "") not in compact:
            return "emptyWithoutStoredScope"
        return "emptyResult"
    return "otherRows"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    summary = json.loads(args.summary.read_text())
    items = {}
    for path in summary["items"]:
        for line in (ROOT / path).open():
            item = json.loads(line)
            items[item["id"]] = item
    cluster_size = collections.Counter((item["wg"], item["family"]) for item in items.values())

    result = {"summary": str(args.summary.relative_to(ROOT)) if args.summary.is_absolute() else str(args.summary),
              "itemCount": len(items), "clusterCount": len(cluster_size), "methods": {}}
    for method, block in summary["primary"]["methods"].items():
        runs_out = []
        for run in block["runs"]:
            responses = {}
            for path in run["responses"]:
                for line in (ROOT / path).open():
                    response = json.loads(line)
                    responses[response["id"]] = response
            missed = collections.Counter()
            stale = 0
            recovered_ids = set()
            missed_ids = []
            causes = collections.Counter()
            for item_id, item in items.items():
                response = responses.get(item_id)
                if response is not None and response.get("questionSha256") not in (None, question_sha(item)):
                    stale += 1
                    continue
                rows = None if response is None else response.get("rows")
                if rows is not None and score(item["gold"], rows)["exact"]:
                    continue
                missed[(item["wg"], item["family"])] += 1
                missed_ids.append(item_id)
                causes[miss_cause(item, response)] += 1
                if matches(item, rows, strip=True):
                    recovered_ids.add(item_id)
            full = {f"{wg}|{family}": count for (wg, family), count in sorted(missed.items())
                    if count == cluster_size[(wg, family)]}
            partial = {f"{wg}|{family}": [count, cluster_size[(wg, family)]]
                       for (wg, family), count in sorted(missed.items())
                       if count != cluster_size[(wg, family)]}
            full_keys = {(wg, family) for (wg, family), count in missed.items()
                         if count == cluster_size[(wg, family)]}
            in_full = {item_id for item_id in missed_ids
                       if (items[item_id]["wg"], items[item_id]["family"]) in full_keys}
            others = [item_id for item_id in missed_ids if item_id not in in_full and item_id not in recovered_ids]
            runs_out.append({
                "run": run["run"],
                "misses": sum(missed.values()),
                "staleQuestion": stale,
                "missesInFullyMissedClusters": sum(full.values()),
                "fullyMissedClusters": full,
                "partialClusters": partial,
                "recoveredByMeetingSuffix": len(recovered_ids),
                "recoveredInFullyMissedClusters": len(recovered_ids & in_full),
                "otherMisses": {item_id: f"{items[item_id]['wg']}|{items[item_id]['family']}" for item_id in others},
                "causes": dict(sorted(causes.items())),
            })
        result["methods"][method] = {
            "runs": runs_out,
            "misses": sum(run["misses"] for run in runs_out),
            "missesInFullyMissedClusters": sum(run["missesInFullyMissedClusters"] for run in runs_out),
            "recoveredByMeetingSuffix": sum(run["recoveredByMeetingSuffix"] for run in runs_out),
            "recoveredInFullyMissedClusters": sum(run["recoveredInFullyMissedClusters"] for run in runs_out),
            "otherMisses": sum(len(run["otherMisses"]) for run in runs_out),
            "causes": dict(sorted(sum((collections.Counter(run["causes"]) for run in runs_out),
                                      collections.Counter()).items())),
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=1) + "\n")
    for method, block in result["methods"].items():
        print(method, {key: value for key, value in block.items() if key != "runs"})
        for run in block["runs"]:
            print("  ", run["run"], run["misses"], run["missesInFullyMissedClusters"],
                  run["recoveredByMeetingSuffix"], run["recoveredInFullyMissedClusters"], run["otherMisses"])


if __name__ == "__main__":
    main()
