"""clause_history 문항의 release 를 두 가지로 읽었을 때 정답 행이 갈리는 문항을 센다 (모델 호출 없음).

질문 "Which Rel-N change requests that modify clause c of TS t ..." 의 Rel-N 은 두 가지로 읽힌다.
- CR 의 대상 release 가 Rel-N 이다 (생성기가 정답을 만드는 방식)
- Rel-N 판의 절 기록에 연결된 CR 이다 (절 기록의 판만 보는 방식)

CR 의 대상 release 판 절이 적재되어 있지 않으면 적재기가 CR 을 다른 판의 같은 번호 절에 잇는다
(RAN5 `01_load_cr_ontology.py` 의 `SectionIndex.resolve`: 같은 판 → 이전 판 중 최신 → 이후 판).
그런 연결이 문항의 절 기록에 있으면 두 독해의 행이 갈린다. 문항마다 절 기록에 연결된 CR 가운데
대상 release 가 절 기록의 판과 다른 CR 을 세고, 작업반별 절 연결 전체에서 판이 다른 연결도 센다.

입력은 `export_chain_records_sqlite.py` 가 만든 작업반별 SQLite 다.
사용: python3 measure_clause_edition_readings.py --items <jsonl> [<jsonl> ...] --db-dir <dir> --out <json>
저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import json
import sqlite3
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--db-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    items = [json.loads(line) for path in args.items for line in path.read_text().splitlines()]
    databases: dict[str, sqlite3.Connection] = {}
    per_wg: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    divergent = []
    for item in items:
        if item["family"] != "clause_history":
            continue
        wg = item["wg"]
        if wg not in databases:
            databases[wg] = sqlite3.connect(f"file:{args.db_dir / f'{wg}.sqlite'}?mode=ro", uri=True)
        db = databases[wg]
        edition = db.execute("SELECT release FROM section WHERE id = ?", (item["anchor"],)).fetchone()[0]
        other = sorted({number for number, in db.execute(
            "SELECT d.number FROM section_modified_by m JOIN document d ON d.id = m.cr "
            "WHERE m.section_id = ? AND d.target_release IS NOT ?", (item["anchor"], edition))})
        per_wg[wg]["items"] += 1
        if other:
            per_wg[wg]["itemsWithOtherReleaseCR"] += 1
            divergent.append({"id": item["id"], "anchor": item["anchor"], "edition": edition,
                              "goldRows": len(item["gold"]), "otherReleaseCRs": other})
    links = {}
    for wg, db in sorted(databases.items()):
        total, other, unrecorded = db.execute(
            "SELECT COUNT(*), SUM(d.target_release != s.release), "
            "SUM(d.target_release IS NULL OR s.release IS NULL) FROM cr_modifies_section x "
            "JOIN document d ON d.id = x.cr JOIN section s ON s.id = x.section_id").fetchone()
        links[wg] = {"clauseLinks": total, "linksToOtherEdition": other or 0,
                     "linksWithReleaseNotRecorded": unrecorded or 0}
    report = {"items": [str(path) for path in args.items], "dbDir": str(args.db_dir),
              "clauseHistoryItems": {wg: dict(counter) for wg, counter in sorted(per_wg.items())},
              "divergentItems": divergent, "clauseLinks": links}
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("clauseHistoryItems", "clauseLinks")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
