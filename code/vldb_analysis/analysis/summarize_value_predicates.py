"""값 조건 분류(`value_predicates.json`)와 저장된 Cypher 질의를 표로 줄인다 (모델 호출 없음).

처분 조건이 정답 질의에 들어가는 다섯 문항군(한 실행에 481문항)만 센다.
SQL 은 `classify_value_predicates.py` 의 계산 결과를 쓴다. 조건식의 글 형태로 둘로 나눈다.
- exactOnly: 범위 칸에 건 조건이 모두 `=` · `IN` 비교다.
- withPattern: 범위 칸에 건 조건에 `LIKE` · `GLOB` · `INSTR` 이 들어 있다.
Cypher 는 질의 글에서 범위를 어느 속성에 어떤 값 목록으로 물었는지 본다. 그래프에서 처분의 범위는
`assessmentMethod` 글 안에 있고, `Resolution.resolutionScope` 의 저장 값은 `document_disposition` 이다.

사용: python3 -B summarize_value_predicates.py --predicates <json> --out <json>
"""
from __future__ import annotations

import argparse
import collections
import importlib
import json
import re
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
TRACK = "publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
LOGS = ROOT / "logs" / TRACK
sys.path.insert(0, str(ROOT / "scripts" / TRACK))
score = importlib.import_module("score_chain_eval").score
FAMILIES = {"disposition_pack", "full_chain", "revision_chain", "clause_history", "pack_origin"}
STORED_RESOLUTION_SCOPE = "document_disposition"


def normal(value: str) -> str:
    return re.sub(r"[-_ ]", "", value.strip().lower())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predicates", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    rows = json.loads(Path(args.predicates).read_text())["rows"]
    totals = collections.defaultdict(lambda: collections.Counter())
    sql = collections.defaultdict(lambda: collections.Counter())
    sessions = collections.defaultdict(set)
    for row in rows:
        key = row["method"]
        totals[key]["queries"] += 1
        totals[key]["exact"] += row["exact"]
        totals[key]["answerableExact"] += row["exact"] if row["family"] != "pack_lookup_empty" else 0
        totals[key]["runs"] = len({r["run"] for r in rows if r["method"] == key}) if "runs" not in totals[key] else totals[key]["runs"]
        if row["family"] not in FAMILIES:
            sql[key]["otherFamilies"] += 1
            sql[key]["otherFamiliesWithScopePredicate"] += row["scope"] != "no_predicate"
            sql[key]["otherFamiliesExact"] += row["exact"]
            continue
        form = "exactOnly" if row["scopeForm"] == "exact" else "withPattern" if row["scopeForm"] in ("pattern", "several") else "none"
        sql[key][form] += 1
        sql[key][form + "Exact"] += row["exact"]
        sql[key][form + "RejectsStoredValue"] += row["scope"] == "rejects_target"
        sql[key][form + "AcceptsOnlyStoredValue"] += row["scope"] == "accepts_target_only"
        sessions[(key, form)].add((row["run"], row["wg"]))
        sql[key]["evidenceExactOnly"] += row["evidence_statusForm"] == "exact"
        sql[key]["evidenceRejectsStoredValue"] += row["evidence_status"] == "rejects_target"
    for (key, form), members in sessions.items():
        sql[key][form + "Sessions"] = len(members)

    gold = {}
    for name in ("core", "ran5"):
        with (LOGS / f"integration/items_final/gate/{name}/chain_items_admitted.jsonl").open() as handle:
            for line in handle:
                item = json.loads(line)
                gold[item["id"]] = item
    sources = [("opus_schema", LOGS / f"chain_eval/RAN{n}_text2cypher_claude_subagent_run{r}.jsonl") for r in "ABCDEFGHIJ" for n in range(1, 6)]
    sources += [("codex_schema", LOGS / f"chain_eval/codex/chain_cy_RAN{n}_codex.jsonl") for n in range(1, 6)]
    sources += [(f"codex_{m}", LOGS / f"chain_eval/codex_v2/responses/RAN{n}_cy_{m}_codex.jsonl") for m in ("dom", "exp") for n in range(1, 6)]
    cypher = collections.defaultdict(lambda: collections.Counter())
    for method, path in sources:
        with path.open() as handle:
            for line in handle:
                record = json.loads(line)
                item = gold[record["id"]]
                exact = score(item["gold"], record.get("rows"))["exact"]
                cypher[method]["queries"] += 1
                cypher[method]["exact"] += exact
                cypher[method]["answerableExact"] += exact if item["family"] != "pack_lookup_empty" else 0
                if item["family"] not in FAMILIES:
                    continue
                attempts = [a for a in record.get("attempts", []) if a.get("cypher")]
                text = attempts[-1]["cypher"] if attempts else ""
                lists = re.findall(r"resolutionScope[^\n]{0,80}?\bIN\s*\[([^\]]*)\]", text)
                literals = {normal(v) for body in lists for v in re.findall(r"'([^']*)'", body)}
                reads_method = "assessmentMethod" in re.sub(r"'(?:[^'\\]|\\.)*'", "''", text)
                if lists and normal(STORED_RESOLUTION_SCOPE) not in literals:
                    kind = "resolutionScopeListWithoutStoredValue"
                elif lists:
                    kind = "resolutionScopeListWithStoredValue"
                elif reads_method:
                    kind = "readsAssessmentMethod"
                elif "resolutionScope" in text:
                    kind = "resolutionScopeOtherForm"
                else:
                    kind = "noScopeCondition"
                cypher[method][kind] += 1
                cypher[method][kind + "Exact"] += exact
    out = {"families": sorted(FAMILIES), "itemsPerRunInFamilies": 481,
           "totals": {k: dict(v) for k, v in totals.items()},
           "sql": {k: dict(v) for k, v in sql.items()},
           "cypher": {k: dict(v) for k, v in cypher.items()}}
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    for part in ("sql", "cypher"):
        for key, value in out[part].items():
            print(part, key, json.dumps(value, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
