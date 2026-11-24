"""clause_history 문항을 하위 조항 포함 독해로 다시 풀었을 때 정답 행 집합이 달라지는 문항을 센다.

clause_history 문항은 "clause X 를 고치는 CR" 을 묻는다. 정답은 CR 의 수정 조항 기록이 정확히 X 인 경우만 담는다.
같은 문장을 "X 와 그 아래 조항(X.1, X.2.3 …)을 고치는 CR" 로 읽으면 행이 늘 수 있다. 이 스크립트는 문항마다
두 독해의 행 집합을 같은 SQLite 기록에서 계산하고, 하위 조항 독해에서만 나오는 행이 있는 문항을 WG 별로 센다.
조건은 정답 생성과 같다: 처분 기록이 원문 확인·문서 전체 대상이고, CR 의 대상 release 가 조항 기록의 release 와 같고,
CR 이 TSG CR pack 에 들어 있다.
`--responses` 를 주면 두 독해가 갈리는 문항에서 각 응답이 어느 독해와 같은지 센다. 행 비교는 채점기
(`score_chain_eval.key`)와 같다.

사용: python3 measure_clause_subclause_reading.py --db-dir <sqlite 폴더> --items <admitted.jsonl>... --out <json>
      [--responses <응답 jsonl>...]
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sqlite3

from score_chain_eval import key

VERIFIED = "d.evidence_status = 'source_verified' AND d.scope = 'whole_target'"
SELECT = """
    SELECT DISTINCT doc.number, d.code, g.label, p.pack_number, s.clause
    FROM cr_modifies_section c
    JOIN section s ON s.id = c.section_id JOIN document doc ON doc.id = c.cr
    JOIN disposition d ON d.target = c.cr
    JOIN resolution r ON r.id = d.resolution_id JOIN meeting g ON g.id = r.meeting_id
    JOIN cr_in_pack m ON m.cr = c.cr JOIN cr_pack p ON p.id = m.pack_id
    JOIN section a ON a.id = :anchor
    WHERE s.spec = a.spec AND s.release = a.release
      AND (s.clause = a.clause OR s.clause LIKE a.clause || '.%')
      AND doc.target_release = s.release AND """ + VERIFIED


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-dir", required=True)
    parser.add_argument("--items", required=True, nargs="+")
    parser.add_argument("--out", required=True)
    parser.add_argument("--responses", nargs="*", default=[])
    args = parser.parse_args()
    db_dir = pathlib.Path(args.db_dir)
    items = [json.loads(line) for path in args.items for line in open(path) if line.strip()]
    items = [item for item in items if item["family"] == "clause_history"]
    connections: dict[str, sqlite3.Connection] = {}
    rows, by_wg = [], collections.defaultdict(lambda: {"items": 0, "goldReproduced": 0, "differs": 0, "extraRows": 0})
    for item in items:
        wg = item["wg"]
        if wg not in connections:
            connections[wg] = sqlite3.connect(f"file:{db_dir / (wg + '.sqlite')}?mode=ro", uri=True)
        found = connections[wg].execute(SELECT, {"anchor": item["anchor"]}).fetchall()
        anchor_clause = item["anchor"].rsplit("-", 1)[1]
        exact = {tuple(r[:4]) for r in found if r[4] == anchor_clause}
        inclusive = {tuple(r[:4]) for r in found}
        gold = {tuple(r) for r in item["gold"]}
        extra = sorted(inclusive - gold)
        subclauses = sorted({r[4] for r in found if r[4] != anchor_clause})
        cell = by_wg[wg]
        cell["items"] += 1
        cell["goldReproduced"] += exact == gold
        cell["differs"] += bool(extra)
        cell["extraRows"] += len(extra)
        rows.append({"id": item["id"], "wg": wg, "anchorClause": anchor_clause, "goldRows": len(gold),
                     "exactReadingEqualsGold": exact == gold, "inclusiveRows": len(inclusive),
                     "extraRows": [list(r) for r in extra], "subclausesWithRows": subclauses,
                     "inclusive": [list(r) for r in sorted(inclusive)]})
    total = {k: sum(c[k] for c in by_wg.values()) for k in ("items", "goldReproduced", "differs", "extraRows")}
    result = {"method": __doc__.split("\n")[0], "items": args.items, "dbDir": args.db_dir,
              "total": total, "byWorkingGroup": dict(sorted(by_wg.items())), "rows": rows}
    split = {r["id"]: r for r in rows if r["extraRows"]}
    gold_by_id = {item["id"]: item["gold"] for item in items}
    responses = []
    for path in args.responses:
        records = {}
        for line in open(path):
            if line.strip():
                record = json.loads(line)
                records[record["id"]] = record
        counts = collections.Counter()
        for item_id, row in split.items():
            if item_id not in records:
                continue
            given = records[item_id].get("rows")
            if given is None:
                counts["unreadable"] += 1
                continue
            given = {key(r) for r in given}
            gold = {key(r) for r in gold_by_id[item_id]}
            inclusive = {key(r) for r in row["inclusive"]}
            extra = {key(r) for r in row["extraRows"]}
            counts["answered"] += 1
            counts["equalsExactReading"] += given == gold
            counts["equalsInclusiveReading"] += given == inclusive
            counts["containsSubclauseRow"] += bool(given & extra)
        responses.append({"file": path, **{k: counts[k] for k in ("answered", "unreadable", "equalsExactReading",
                                                                  "equalsInclusiveReading", "containsSubclauseRow")}})
    result["splitItems"] = sorted(split)
    result["responses"] = responses
    json.dump(result, open(args.out, "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"total": total, "byWorkingGroup": result["byWorkingGroup"]}, ensure_ascii=False))
    for entry in responses:
        print(pathlib.Path(entry["file"]).name, {k: v for k, v in entry.items() if k != "file"})


if __name__ == "__main__":
    main()
