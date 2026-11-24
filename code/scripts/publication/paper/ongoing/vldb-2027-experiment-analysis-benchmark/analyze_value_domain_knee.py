"""값 영역 묶음의 두 무릎점(서로 다른 값 62 개 · 값 길이 88 자)이 어떤 속성을 값 전부 목록에 넣는지, 이웃 경계에서 무엇이 바뀌는지 잰다 (모델 호출 없음).

무엇을 재는가.
- 입력은 `build_value_domain_packets.py` 가 남긴 `chain_eval/codex_v2/packets_domain/domain_report.json` 이다.
  속성마다 원소 기준 서로 다른 값 수 · 종류 · 기록된 방식(`full_list` / `format_and_examples`) · 형식 방식 문자열의
  길이 최댓값이 들어 있다. 값 전부 목록 방식인 문자열 속성의 가장 긴 값 길이는 보고서에 없으므로 다시 잰다.
  그래프는 작업반별 Neo4j 읽기 세션에서 빌더의 `fetch_graph` 로, 관계형은 `integration/sqlite_final` 에서 빌더의
  `fetch_sql` 로 읽는다. 다시 읽은 원소 수가 보고서와 다르면 그래프가 바뀐 것으로 적는다.
- 무릎점 재현: 보고서의 언어별 서로 다른 값 수 막대그림(목록 값은 통째로 센 수)으로 빌더의 `kneedle` 을 다시 돌려
  62 를 얻는지, 원소 수 62 이하 문자열 속성의 가장 긴 값 길이로 88 을 얻는지 본다. Kneedle 거리가 큰 후보 다섯도 적는다.
- 그림용 분포: 언어별 서로 다른 값 수의 경험적 누적분포(log10)와 길이 분포, 원소 수 62 이하 문자열 속성의 가장 긴
  값 길이 분포.
- 경계 이동: 속성이 값 전부 목록에 들어가는 규칙(원소 수 ≤ T, 문자열이면 가장 긴 값 ≤ C)을 (T, C) = (62, 88) 과,
  한쪽을 고정한 채 다른 쪽을 실제로 집합이 바뀌는 바로 앞 · 바로 뒤 값으로 옮긴 넷에서 계산해 집합 차이를 적는다.
  T 와 C 를 넓게 훑은 곡선(목록 속성 수)도 적는다.
- 정답에 쓰이는 열: 참조 SQL(`measure_relational_equivalence.SQL` 두 벌)이 읽는 (표, 열)을 SQLite 권한 콜백으로,
  참조 Cypher(`crosscheck_chain_items_graph.CYPHER`)가 쓰는 (레이블, 속성)을 질의 문자열에서 모은다.
  레이블 없는 변수 `cr` 의 레이블은 667 문항의 시작점으로 질의를 실행해 `labels(cr)` 로 확인한다.
  이 열들이 위 경계 이동에서 목록에 들어가거나 빠지는지 본다.

사용 (저장소 루트에서, Neo4j RAN1~RAN5 가 7687~7691 에 떠 있어야 한다):
    .venv/bin/python3 -I scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/analyze_value_domain_knee.py [--out <json>]
기본 출력은 `final/next_cycle/analysis/m14_value_domain_knee.json` 이다.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(path for path in HERE.parents if (path / ".git").exists())
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts" / "common"))

from neo4j import GraphDatabase  # noqa: E402

from build_value_domain_packets import fetch_graph, fetch_sql, flatten, kneedle  # noqa: E402
from common.credentials import neo4j_auth  # noqa: E402
from crosscheck_chain_items_graph import CYPHER, graph_key  # noqa: E402
from measure_relational_equivalence import SQL, VARIANTS  # noqa: E402

TRACK = "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
REPORT = f"{TRACK}/chain_eval/codex_v2/packets_domain/domain_report.json"
SQLITE = f"{TRACK}/integration/sqlite_final"
ITEMS = [f"{TRACK}/integration/items_final/gate/core/chain_items_admitted.jsonl",
         f"{TRACK}/integration/items_final/gate/ran5/chain_items_admitted.jsonl"]
DEFAULT_OUT = f"{TRACK}/final/next_cycle/analysis/m14_value_domain_knee.json"
WGS = [f"RAN{n}" for n in range(1, 6)]
BOLT = {wg: f"bolt://localhost:{7686 + n}" for n, wg in enumerate(WGS, start=1)}
STRING_KINDS = {"categorical", "identifier", "text"}


def kneedle_candidates(values: list[int], top: int = 5) -> list[dict]:
    """`kneedle` 과 같은 거리로 매긴 후보 상위 `top` 개."""
    ordered = sorted(v for v in values if v >= 1)
    logs = [math.log10(v) for v in ordered]
    low, high = logs[0], logs[-1]
    out = []
    for i, value in enumerate(ordered):
        if i + 1 < len(ordered) and ordered[i + 1] == value:
            continue
        share = (i + 1) / len(ordered)
        out.append({"value": value, "ecdf": round(share, 4),
                    "distance": round(share - (logs[i] - low) / (high - low), 4)})
    return sorted(out, key=lambda c: -c["distance"])[:top]


def ecdf_points(values: list[int]) -> list[list]:
    """(값, log10 값, 누적 비율) 점. 같은 값은 마지막 위치 하나로 묶는다."""
    ordered = sorted(v for v in values if v >= 1)
    points = []
    for i, value in enumerate(ordered):
        if i + 1 < len(ordered) and ordered[i + 1] == value:
            continue
        points.append([value, round(math.log10(value), 4), round((i + 1) / len(ordered), 4)])
    return points


def included(props: dict, threshold: int, cap: int) -> set:
    return {key for key, p in props.items()
            if p["distinct"] <= threshold and (p["longest"] or 0) <= cap}


def reference_sql_columns() -> dict:
    """참조 SQL 두 벌이 읽는 (표, 열). 반환 열은 SELECT 목록에서 별칭으로 따로 모은다."""
    db = sqlite3.connect(f"file:{ROOT / SQLITE / 'RAN1.sqlite'}?mode=ro", uri=True)
    reads: dict[str, set] = collections.defaultdict(set)
    current = {"family": None}

    def authorizer(action, first, second, _db, _source):
        if action == sqlite3.SQLITE_READ and first and second:
            reads[current["family"]].add((first, second))
        return sqlite3.SQLITE_OK

    db.set_authorizer(authorizer)
    projected: dict[str, set] = collections.defaultdict(set)
    for variant, names in VARIANTS.items():
        for family, text in SQL.items():
            sql = text.format(**names)
            current["family"] = family
            db.execute(sql, {"anchor": "none"}).fetchall()
            aliases = {alias: table for table, alias in re.findall(
                r"\b(?:FROM|JOIN)\s+(\w+)(?:\s+(?!(?:JOIN|ON|WHERE)\b)(\w+))?", sql) if alias}
            select = re.search(r"SELECT DISTINCT (.*?)\s+FROM", " ".join(sql.split())).group(1)
            for alias, column in re.findall(r"(\w+)\.(\w+)", select):
                projected[family].add((aliases[alias], column))
    db.set_authorizer(None)
    db.close()
    real = {(t, c) for cols in reads.values() for t, c in cols if t not in ("later",)}
    return {"read": sorted(real), "projected": sorted({x for v in projected.values() for x in v}),
            "byFamily": {f: sorted(c for c in cols if c[0] != "later") for f, cols in sorted(reads.items())}}


def reference_cypher_properties(items: list[dict]) -> dict:
    """참조 Cypher 가 쓰는 (레이블, 속성). 레이블 없는 `cr` 은 실행해서 레이블을 얻는다."""
    found, projected, unlabeled = set(), set(), collections.defaultdict(set)
    for family, text in CYPHER.items():
        flat = " ".join(text.split())
        labels = dict(re.findall(r"\((\w+):(\w+)", flat))
        for label, body in re.findall(r"\(\w*:(\w+) \{([^}]*)\}", flat):
            for prop in re.findall(r"(\w+):", body):
                found.add((label, prop))
        returned = flat.split(" RETURN ", 1)[1]
        for var, prop in re.findall(r"\b(\w+)\.(\w+)", flat):
            if var in labels:
                found.add((labels[var], prop))
                if f"{var}.{prop}" in returned:
                    projected.add((labels[var], prop))
            else:
                unlabeled[family].add((var, prop))
    resolved = collections.defaultdict(set)
    by_family = collections.defaultdict(list)
    for item in items:
        by_family[(item["wg"], item["family"])].append(item)
    for wg in WGS:
        with GraphDatabase.driver(BOLT[wg], auth=neo4j_auth()) as driver, \
                driver.session(default_access_mode="READ") as session:
            for family, pairs in unlabeled.items():
                variables = sorted({var for var, _ in pairs})
                head = " ".join(CYPHER[family].split()).split(" RETURN ", 1)[0]
                probe = head + " RETURN DISTINCT " + ", ".join(f"labels({v}) AS {v}" for v in variables)
                for item in by_family[(wg, family)]:
                    for record in session.run(probe, anchor=graph_key(item["anchor"])):
                        for var in variables:
                            resolved[(family, var)].add(tuple(sorted(record[var])))
    for family, pairs in unlabeled.items():
        returned = " ".join(CYPHER[family].split()).split(" RETURN ", 1)[1]
        for var, prop in pairs:
            for label_set in resolved[(family, var)]:
                for label in label_set:
                    found.add((label, prop))
                    if f"{var}.{prop}" in returned:
                        projected.add((label, prop))
    return {"used": sorted(found), "projected": sorted(projected),
            "unlabeledVariableLabels": {f"{f}:{v}": sorted(map(list, s)) for (f, v), s in sorted(resolved.items())}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, default=ROOT / DEFAULT_OUT)
    args = parser.parse_args()
    report = json.loads((ROOT / REPORT).read_text())
    threshold, cap = report["threshold"]["value"], report["labelLengthCap"]["value"]

    # 1. 무릎점 재현
    histogram = report["threshold"]["distinctCountHistogram"]
    raw = {lang: [int(v) for v, n in histogram[lang].items() for _ in range(n)] for lang in histogram}
    reproduced = {lang: kneedle(values) for lang, values in raw.items()}
    reproduced["pooled"] = kneedle(raw["cypher"] + raw["sql"])

    # 2. 속성 표
    props: dict[tuple, dict] = {}
    for key, packet in report["packets"].items():
        lang, wg = key.split("_")
        for entry in packet["entries"]:
            body = entry.get("element", entry)
            longest = body.get("length", {}).get("max") if body["kind"] in STRING_KINDS else 0
            props[(lang, wg, entry["owner"], entry["name"])] = {
                "distinct": body["distinct"], "kind": body["kind"], "mode": body["mode"],
                "container": entry.get("container"), "longest": longest,
                "longestSource": ("notString" if body["kind"] not in STRING_KINDS
                                  else "report" if longest is not None else None)}

    # 3. 값 전부 목록 방식 문자열의 가장 긴 값 다시 재기
    drift = []
    need = [k for k, p in props.items() if p["longest"] is None]
    for wg in WGS:
        db = sqlite3.connect(f"file:{ROOT / SQLITE / (wg + '.sqlite')}?mode=ro", uri=True)
        for key in [k for k in need if k[0] == "sql" and k[1] == wg]:
            values = flatten(fetch_sql(db, key[2], key[3]))
            props[key].update(longest=max(len(v) for v in values if isinstance(v, str)), longestSource="sqlite")
            if len(values) != props[key]["distinct"]:
                drift.append({"key": list(key), "report": props[key]["distinct"], "now": len(values)})
        db.close()
        with GraphDatabase.driver(BOLT[wg], auth=neo4j_auth()) as driver, \
                driver.session(default_access_mode="READ") as session:
            for key in [k for k in need if k[0] == "cypher" and k[1] == wg]:
                values = flatten(fetch_graph(session, key[2], key[3]))
                props[key].update(longest=max(len(v) for v in values if isinstance(v, str)), longestSource="neo4j")
                if len(values) != props[key]["distinct"]:
                    drift.append({"key": list(key), "report": props[key]["distinct"], "now": len(values)})

    # 4. 기록된 방식 재현과 길이 무릎점 재현
    base = included(props, threshold, cap)
    recorded = {k for k, p in props.items() if p["mode"] == "full_list"}
    low_strings = [p["longest"] for p in props.values() if p["kind"] in STRING_KINDS and p["distinct"] <= threshold]
    cap_knee = kneedle(low_strings)

    # 5. 이웃 경계
    eligible_t = sorted({p["distinct"] for p in props.values() if (p["longest"] or 0) <= cap})
    eligible_c = sorted({p["longest"] for p in props.values() if p["kind"] in STRING_KINDS and p["distinct"] <= threshold})
    t_prev = max(v for v in eligible_t if v < threshold)
    t_next = min(v for v in eligible_t if v > threshold)
    c_prev = max(v for v in eligible_c if v < cap)
    c_next = min(v for v in eligible_c if v > cap)
    t_at = threshold in eligible_t
    c_at = cap in eligible_c

    sql_cols = reference_sql_columns()
    items = list({item["id"]: item for path in ITEMS
                  for item in map(json.loads, (ROOT / path).read_text().splitlines())}.values())
    cypher_props = reference_cypher_properties(items)
    gold_keys = {("sql", wg, t, c) for wg in WGS for t, c in sql_cols["read"]} | \
                {("cypher", wg, l, p) for wg in WGS for l, p in cypher_props["used"]}
    projected_keys = {("sql", wg, t, c) for wg in WGS for t, c in sql_cols["projected"]} | \
                     {("cypher", wg, l, p) for wg in WGS for l, p in cypher_props["projected"]}

    def describe_key(key):
        p = props.get(key)
        return {"key": "/".join(key), **({k: p[k] for k in ("distinct", "kind", "longest", "container")} if p
                                         else {"missing": True})}

    def shift(t: int, c: int) -> dict:
        other = included(props, t, c)
        entered, left = sorted(other - base), sorted(base - other)
        return {"threshold": t, "cap": c, "fullList": len(other),
                "entered": [describe_key(k) for k in entered], "left": [describe_key(k) for k in left],
                "goldColumnsEntered": [describe_key(k) for k in entered if k in gold_keys],
                "goldColumnsLeft": [describe_key(k) for k in left if k in gold_keys]}

    neighbours = {"thresholdPrevious": shift(t_prev, cap), "thresholdNext": shift(t_next, cap),
                  "capPrevious": shift(threshold, c_prev), "capNext": shift(threshold, c_next)}
    # Kneedle 거리 상위 후보로 바꿨을 때와, 정답이 반환하는 회의 열이 빠지기 시작하는 문턱 아래 값들.
    candidate_t = [c["value"] for c in kneedle_candidates(raw["cypher"] + raw["sql"])]
    candidate_c = [c["value"] for c in kneedle_candidates(low_strings)]
    lower_t = sorted({v for v in eligible_t if threshold - 25 <= v < threshold})
    alternatives = {"thresholdCandidates": [shift(t, cap) for t in candidate_t if t != threshold],
                    "capCandidates": [shift(threshold, c) for c in candidate_c if c != cap],
                    "thresholdsBelow": [{k: row[k] for k in ("threshold", "fullList")} |
                                        {"left": len(row["left"]), "goldLeft": [g["key"] for g in row["goldColumnsLeft"]],
                                         "projectedGoldLeft": [g["key"] for g in row["goldColumnsLeft"]
                                                               if tuple(g["key"].split("/")) in projected_keys]}
                                        for row in (shift(t, cap) for t in lower_t)]}
    neighbours["alternatives"] = alternatives
    sweep_t = sorted({v for v in eligible_t if v <= 10_000})
    sweep = {"threshold": [[t, len(included(props, t, cap))] for t in sweep_t],
             "cap": [[c, len(included(props, threshold, c))]
                     for c in sorted({p["longest"] for p in props.values() if p["longest"]})]}

    gold_status = []
    for key in sorted(gold_keys):
        p = props.get(key)
        gold_status.append({**describe_key(key), "projected": key in projected_keys,
                            "fullListAtKnee": key in base if p else None})

    out = {
        "source": REPORT,
        "knees": {"recorded": {"threshold": report["threshold"]["knees"], "cap": report["labelLengthCap"]["knee"]},
                  "reproducedThreshold": reproduced, "reproducedCap": cap_knee,
                  "thresholdCandidates": {lang: kneedle_candidates(v) for lang, v in
                                          {**raw, "pooled": raw["cypher"] + raw["sql"]}.items()},
                  "capCandidates": kneedle_candidates(low_strings)},
        "properties": len(props),
        "propertiesByLanguage": dict(collections.Counter(k[0] for k in props)),
        "recordedModeReproduced": {"fullListRecorded": len(recorded), "fullListRecomputed": len(base),
                                   "onlyRecorded": ["/".join(k) for k in sorted(recorded - base)],
                                   "onlyRecomputed": ["/".join(k) for k in sorted(base - recorded)]},
        "graphDriftSinceBuild": drift,
        "longestRemeasured": dict(collections.Counter(p["longestSource"] for p in props.values())),
        "distributions": {
            "rawDistinctEcdfByLanguage": {lang: ecdf_points(v) for lang, v in raw.items()},
            "rawDistinctEcdfPooled": ecdf_points(raw["cypher"] + raw["sql"]),
            "elementDistinctByProperty": [["/".join(k), p["distinct"], p["kind"], p["longest"]]
                                          for k, p in sorted(props.items())],
            "longestOfLowCardinalityStringsEcdf": ecdf_points(low_strings),
        },
        "boundaries": {"knee": {"threshold": threshold, "cap": cap, "fullList": len(base),
                                "thresholdIsObservedBreakpoint": t_at, "capIsObservedBreakpoint": c_at},
                       "neighbours": neighbours},
        "sweep": sweep,
        "goldColumns": {"definition": "columns read by the reference SQL (both variants, SQLite authorizer) and "
                                      "properties used by the reference Cypher; projected marks those returned",
                        "sql": sql_cols, "cypher": cypher_props, "status": gold_status},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print("reproduced", reproduced["pooled"], cap_knee)
    print("full list recorded", len(recorded), "recomputed", len(base), "drift", len(drift))
    for name, row in ((n, r) for n, r in neighbours.items() if n != "alternatives"):
        print(name, row["threshold"], row["cap"], row["fullList"], len(row["entered"]), len(row["left"]),
              len(row["goldColumnsEntered"]), len(row["goldColumnsLeft"]))


if __name__ == "__main__":
    main()
