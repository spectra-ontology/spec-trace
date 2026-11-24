"""저장된 Text-to-SQL 실행을 두 SQLite 판(3.37.2 · 3.50.4)에서 다시 돌린 결과와 MATERIALIZED 재실행 결과를 한 파일로 모은다.

읽기 전용 집계이며 질의를 실행하지 않는다. RQ5 둘째 문단의 수치는 이 파일이 쓰는 결과에서만 가져온다.
입력: replay/{WG}_old.json(3.37.2) · replay/{WG}_new.json(3.50.4) · materialize/{WG}.json(3.50.4, 힌트)
      · materialize/sqlite337_control/{WG}.json(3.37.2, 같은 힌트)
사용: <python> -B <이 파일> <out json>   (저장소 루트에서 실행)
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WGS = ["RAN1", "RAN2", "RAN3", "RAN4", "RAN5"]
LOWER_CAPS = (1, 10, 30)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def capped(entry: dict) -> bool:
    return bool(entry.get("replayed") and entry.get("error") and "interrupt" in entry["error"])


def main() -> None:
    out = {"scope": "stored Text-to-SQL executions re-run unchanged and read-only under two SQLite releases with a 60 s cap",
           "inputs": {}, "byGroup": {}}
    total = collections.Counter()
    lost_by_family = collections.Counter()
    gained = []
    stored_differs = []
    for wg in WGS:
        old_file, new_file = load(HERE / f"replay/{wg}_old.json"), load(HERE / f"replay/{wg}_new.json")
        out["inputs"][wg] = {"old": old_file["sqliteLibrary"], "new": new_file["sqliteLibrary"]}
        old = {(r["condition"], r["id"]): r for r in old_file["results"]}
        new = {(r["condition"], r["id"]): r for r in new_file["results"]}
        assert old.keys() == new.keys(), wg
        for key, o in old.items():
            n = new[key]
            side = "opus" if key[0].startswith("opus_run") else "codex"
            total[f"{side}.executions"] += 1
            total[f"{side}.storedExact"] += o.get("storedExact") == 1
            total[f"{side}.oldExact"] += o.get("exact") == 1
            total[f"{side}.newExact"] += n.get("exact") == 1
            total[f"{side}.oldCapped"] += capped(o)
            total[f"{side}.newCapped"] += capped(n)
            total[f"{side}.oldOverOneSecond"] += (o.get("seconds") or 0) > 1
            total[f"{side}.newOverOneSecond"] += (n.get("seconds") or 0) > 1
            # 낮은 상한의 결과: 60초 상한에서 정답인 실행 가운데 기록된 시간이 그 상한 안에 드는 것.
            # 검토 요청의 상한 1 · 10 · 30초를 같은 기록에서 센다(다시 실행하지 않는다).
            for cap in LOWER_CAPS:
                total[f"{side}.oldExactWithin{cap}s"] += o.get("exact") == 1 and (o.get("seconds") or 0) <= cap
                total[f"{side}.newExactWithin{cap}s"] += n.get("exact") == 1 and (n.get("seconds") or 0) <= cap
            same_outcome = (o.get("exact") == 1) == (o.get("storedExact") == 1)
            if not same_outcome:
                stored_differs.append({"key": [wg, *key], "family": o["family"], "storedSeconds": o.get("storedSeconds"),
                                       "replaySeconds": o.get("seconds"), "replayError": o.get("error")})
            total[f"{side}.outcomeDiffersOldNew"] += (o.get("exact") == 1) != (n.get("exact") == 1)
            if o.get("exact") == 1 and n.get("exact") != 1:
                total[f"{side}.lostUnderNew"] += 1
                total[f"{side}.lostUnderNewByCap"] += capped(n)
                lost_by_family[o["family"]] += 1
            if n.get("exact") == 1 and o.get("exact") != 1:
                gained.append({"key": [wg, *key], "family": o["family"], "newSeconds": n.get("seconds"),
                               "oldSeconds": o.get("seconds"), "oldError": o.get("error")})
        if wg == "RAN4":
            continue
        hint = load(HERE / f"materialize/{wg}.json")
        control = {r["key"]: r for r in load(HERE / f"materialize/sqlite337_control/{wg}.json")["results"]}
        out["inputs"][wg].update({"hint": hint["sqliteLibrary"], "hintInterpreter": Path(hint["interpreter"]).parts[-3:]})
        for r in hint["results"]:
            total["hint.newCapped"] += 1
            if r["timedOutOld"]:
                total["hint.cappedUnderBoth"] += 1
                total["hint.cappedUnderBothStillCapped"] += r.get("exact") != 1
                continue
            total["hint.cappedOnlyUnderNew"] += 1
            if not r["appliedCtes"]:
                total["hint.cappedOnlyUnderNewNoFlippedCte"] += 1
                continue
            total["hint.cappedOnlyUnderNewWithFlippedCte"] += 1
            total["hint.goldUnderNewWithHint"] += r.get("exact") == 1
            total["hint.goldUnderOldWithHint"] += control[r["key"]].get("exact") == 1
            total["hint.planMaterializesEveryHintedCte"] += r.get("planMaterializes") == sorted(r["appliedCtes"])
    out["totals"] = dict(sorted(total.items()))
    out["lostUnderNewByFamily"] = dict(lost_by_family.most_common())
    out["gainedUnderNew"] = gained
    out["oldReplayDiffersFromStored"] = stored_differs
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out["totals"], indent=1))
    print(out["lostUnderNewByFamily"])
    print(len(gained), "gained;", len(stored_differs), "old replay differs from stored")


if __name__ == "__main__":
    main()
