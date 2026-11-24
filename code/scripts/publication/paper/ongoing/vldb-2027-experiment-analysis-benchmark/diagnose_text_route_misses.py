"""검색 경로가 틀린 문항을 행 단위로 진단한다 (모델 호출 없음).

`--route` 가 진단할 경로를 고른다: `text_search`(메타데이터 포함 전문 검색, 기본값), `text_search_text_only`
(본문만 전문 검색), `raw_index`(원문 색인 검색), `dense_tool`(밀집 검색 도구), `dense_tool_capped`(한 번에
돌려주는 청크 수에 상한을 둔 밀집 검색 도구). `--run` 이 그 경로의 실행을 고른다(기본값 runA). 실행 목록은
`summarize_text_route_full.RUN_DIRS`(메타데이터 포함 runA · runB · runC, 본문만 runA)와 보충 주기의
`analyze_supplement_cycle.COLLECTED`(본문만 runB · runC, 원문 색인 · 밀집 도구 runA · runB, 상한 둔 밀집 도구
runA)를 합친 것이다. 출력 기본 경로는 그 실행 폴더(보충 주기 실행은 응답이 든 `collected/` 의 상위 폴더)의
`miss_diagnosis.json` 이다.

채점과 같은 정규화(`score_chain_eval.cell_key`)로 정답 행과 응답 행을 비교해 문항마다
더한 행(extra) · 빠진 행(missing) · 갈래(`summarize_text_route_full.miss_kind`)를 적는다.
갈래가 partial 이면 빠진 행마다 가장 가까운 더한 행과 다른 칸 수를 센다.
clause_history 문항의 더한 행은 그 CR 의 기록(`clausesAffected`)에 질문의 절이 그대로 있는지,
본문 조각의 절 표지(`[CR … | Section <절>]`)가 그 절을 적는지를 전문 색인의 모든 조각에서 확인한다.

사용: python3 diagnose_text_route_misses.py \
          [--route text_search|text_search_text_only|raw_index|dense_tool|dense_tool_capped] \
          [--run runA|runB|runC] [--out <json>]
저장소 루트에서 `PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark` 로 실행한다.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from analyze_supplement_cycle import COLLECTED
from measure_text_route_ceiling import connect_index
from score_chain_eval import cell_key, score
from summarize_text_route_full import ITEMS, ROOT, ROUTES, RUN_DIRS, TRACK, WGS, miss_kind, read_responses

DESCRIPTION = {
    "text_search": "메타데이터 포함 전문 검색 경로가 틀린 문항을 행 단위로 진단한다 (모델 호출 없음).",
    "text_search_text_only": "본문만 전문 검색 경로가 틀린 문항을 행 단위로 진단한다 (모델 호출 없음).",
    "raw_index": "원문 색인 검색 경로가 틀린 문항을 행 단위로 진단한다 (모델 호출 없음).",
    "dense_tool": "밀집 검색 도구 경로가 틀린 문항을 행 단위로 진단한다 (모델 호출 없음).",
    "dense_tool_capped": "한 번에 돌려주는 청크 수에 상한을 둔 밀집 검색 도구 경로가 틀린 문항을 행 단위로 진단한다 (모델 호출 없음).",
}
# 경로 → 실행 → 응답 파일 꼴. 보충 주기 실행의 응답은 실행 폴더의 `collected/` 에 있고 진단은 그 실행 폴더에 쓴다
RESPONSES = {route: {**ROUTES.get(route, {}), **COLLECTED.get(route, {})} for route in DESCRIPTION}
OUT_DIRS = {route: {**{run: f"{TRACK}/chain_eval/{folder}" for run, folder in RUN_DIRS.get(route, {}).items()},
                    **{run: Path(path).parent.parent.as_posix() for run, path in COLLECTED.get(route, {}).items()}}
            for route in DESCRIPTION}
SECTION_LABEL = re.compile(r"\[CR [^\]]*\| Section ([^\]]+)\]")


def normalise(row, width: int) -> tuple[str, ...]:
    return tuple(cell_key(cell) for cell in row[:width])


def clause_of(item: dict) -> str:
    return item["id"].rsplit("-", 1)[1]


def record_and_body(connection, document: str, clause: str) -> dict:
    affected, labels, chunks = set(), set(), 0
    for collection, meta, text in connection.execute(
            "SELECT collection, meta, text FROM docs WHERE tdoc=?", [document]):
        chunks += 1
        affected.update(json.loads(meta).get("clausesAffected") or [])
        label = SECTION_LABEL.match(text)
        if label and collection.endswith("_cr_chunks"):
            labels.add(label.group(1).strip())
    return {"document": document, "chunks": chunks,
            "clauseInRecord": clause in affected,
            "recordParents": sorted(a for a in affected if clause.startswith(a + ".")),
            "clauseInBodyLabel": clause in labels}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--route", choices=sorted(RESPONSES), default="text_search")
    parser.add_argument("--run", default="runA", help="경로의 실행(RUN_DIRS · COLLECTED)")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.run not in RESPONSES[args.route]:
        parser.error(f"{args.route} 의 실행은 {sorted(RESPONSES[args.route])} 이다")
    out_path = args.out or ROOT / OUT_DIRS[args.route][args.run] / "miss_diagnosis.json"
    route = RESPONSES[args.route][args.run]

    items = {item["id"]: item for path in ITEMS for item in map(json.loads, (ROOT / path).read_text().splitlines())}
    responses, stale = read_responses([route.format(wg=wg) for wg in WGS], items)
    if stale or set(items) - set(responses):
        raise SystemExit(f"응답이 문항과 맞지 않는다: stale {stale}, missing {len(set(items) - set(responses))}")

    connections, misses = {}, []
    for identifier, item in items.items():
        rows = responses[identifier].get("rows")
        if rows is not None and score(item["gold"], rows)["exact"]:
            continue
        width = len(item["fields"])
        gold = {normalise(row, width) for row in item["gold"]}
        got = {normalise(row, width) for row in rows or []}
        entry = {"id": identifier, "wg": item["wg"], "family": item["family"], "fields": item["fields"],
                 "expectsEmpty": item["expectsEmpty"],
                 "kind": "fabricated" if item["expectsEmpty"] else miss_kind(item, rows),
                 "goldRows": len(gold), "responseRows": len(got),
                 "extra": sorted(got - gold), "missing": sorted(gold - got)}
        if entry["kind"] == "partial":
            entry["cellsDifferingPerMissingRow"] = [
                min(sum(a != b for a, b in zip(row, other)) for other in got - gold) for row in sorted(gold - got)]
        if item["family"] == "clause_history" and entry["extra"]:
            connection = connections.setdefault(item["wg"], connect_index(item["wg"]))
            column = item["fields"].index("document")
            entry["extraDocuments"] = [record_and_body(connection, row[column].upper(), clause_of(item))
                                       for row in entry["extra"]]
        misses.append(entry)

    kinds: dict[str, int] = {}
    for entry in misses:
        kinds[entry["kind"]] = kinds.get(entry["kind"], 0) + 1
    body_only = [entry["id"] for entry in misses if entry.get("extraDocuments") and all(
        not d["clauseInRecord"] and d["clauseInBodyLabel"] for d in entry["extraDocuments"])]
    out = {
        "description": DESCRIPTION[args.route],
        "route": route,
        "misses": len(misses),
        "kinds": dict(sorted(kinds.items())),
        "supersetsWhoseExtraRowsAreBodyLabelOnly": body_only,
        "partialsDifferingInOneCell": [e["id"] for e in misses if e["kind"] == "partial"
                                       and e["cellsDifferingPerMissingRow"] == [1] * len(e["missing"])],
        "items": misses,
    }
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "items"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
