"""원문 판정 두 판독자의 결과를 처분 기록과 견준다 (모델 호출 없음). 비교 규칙은 `plan.json` 에 판독 전에 고정했다.

- 판독자 사이 일치: 코드 원일치율과 Cohen's kappa(표본 종류별 · WG 별).
- 기록 반박: 두 판독자가 같은 코드를 고르고 둘 다 cannot_tell 이 아니며 그 코드가 기록과 다르면 반박으로 센다.
- 기록 지지: 한 판독자 이상이 기록 코드를 고르고 다른 판독자가 그와 다른 공유 코드로 반박하지 않는다.
- random_verified 의 반박 비율에 정확한(Clopper-Pearson) 95% 구간을 붙이고, 합친 값은 WG 모집단 가중으로도 낸다.
- 반박 사례와 한 판독자만 다른 사례는 저자가 원문으로 다시 읽도록 목록으로 남긴다.

사용: python3 score_disposition_adjudication.py --dir <adjudication dir> --readers A B --out <json>
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

from scipy.stats import beta


def clopper_pearson(k: int, n: int) -> list[float]:
    if n == 0:
        return [0.0, 1.0]
    lo = 0.0 if k == 0 else float(beta.ppf(0.025, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(0.975, k + 1, n - k))
    return [lo, hi]


def kappa(pairs: list[tuple[str, str]]) -> float | None:
    n = len(pairs)
    if not n:
        return None
    po = sum(a == b for a, b in pairs) / n
    ca = collections.Counter(a for a, _ in pairs)
    cb = collections.Counter(b for _, b in pairs)
    pe = sum(ca[c] * cb[c] for c in ca) / (n * n)
    return None if pe == 1 else (po - pe) / (1 - pe)


def load(path: Path) -> dict:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            row = json.loads(line)
            out[row["packetId"]] = row
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--readers", nargs=2, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    base = Path(args.dir)
    keys = json.loads((base / "keys.json").read_text(encoding="utf-8"))
    summary = json.loads((base / "build_summary.json").read_text(encoding="utf-8"))
    readings = {}
    for r in args.readers:
        readings[r] = {}
        for f in sorted((base / "readings" / r).glob("part*.jsonl")):
            readings[r].update(load(f))
    ra, rb = args.readers

    rows = []
    for pid, k in keys.items():
        a, b = readings[ra].get(pid), readings[rb].get(pid)
        ca, cb = (a or {}).get("code"), (b or {}).get("code")
        both = ca is not None and cb is not None
        contradicted = both and ca == cb and ca != "cannot_tell" and ca != k["code"]
        supported = (ca == k["code"] or cb == k["code"]) and not contradicted
        rows.append({"packetId": pid, **k, "A": ca, "B": cb, "scopeA": (a or {}).get("scope"),
                     "scopeB": (b or {}).get("scope"), "evidenceA": (a or {}).get("evidence"),
                     "evidenceB": (b or {}).get("evidence"), "missing": not both,
                     "contradicted": contradicted, "supported": supported,
                     "split": both and (ca == k["code"]) != (cb == k["code"])})

    report = {"readers": args.readers, "packets": len(keys), "bySet": {}}
    for s in ("random_verified", "random_pending", "reread_differences"):
        sub = [r for r in rows if s in r["sets"]]
        per = {}
        for wg in sorted({r["wg"] for r in sub}) + ["all"]:
            g = [r for r in sub if wg == "all" or r["wg"] == wg]
            read = [r for r in g if not r["missing"]]
            k = sum(r["contradicted"] for r in read)
            per[wg] = {
                "n": len(g), "read": len(read),
                "readerAgreement": sum(r["A"] == r["B"] for r in read) / len(read) if read else None,
                "kappa": kappa([(r["A"], r["B"]) for r in read]),
                "supported": sum(r["supported"] for r in read),
                "contradicted": k, "contradictedCI95": clopper_pearson(k, len(read)),
                "split": sum(r["split"] for r in read),
                "cannotTellAny": sum("cannot_tell" in (r["A"], r["B"]) for r in read),
                "recordCodes": dict(collections.Counter(r["code"] for r in g)),
            }
            sup = [r for r in read if r["supported"]]
            per[wg]["scopeAgreementOnSupported"] = (
                sum(r["scope"] in (r["scopeA"], r["scopeB"]) for r in sup) / len(sup) if sup else None)
        report["bySet"][s] = per
    rv = report["bySet"]["random_verified"]
    pops = {wg: summary["census"][wg]["population"]["source_verified"] for wg in summary["census"]}
    total = sum(pops[wg] for wg in rv if wg != "all")
    report["weightedContradictedShare"] = sum(
        pops[wg] / total * rv[wg]["contradicted"] / rv[wg]["read"] for wg in rv if wg != "all" and rv[wg]["read"])
    report["toReread"] = [r for r in rows if r["contradicted"] or r["split"] or r["missing"]]
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({s: report["bySet"][s]["all"] for s in report["bySet"]}, indent=1))
    print("weighted contradicted share", report["weightedContradictedShare"], "to reread", len(report["toReread"]))


if __name__ == "__main__":
    main()
