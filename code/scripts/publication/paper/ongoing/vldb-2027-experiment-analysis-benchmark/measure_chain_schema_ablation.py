"""기록 요소를 하나씩 비운 뒤 추적 사슬 문항의 통과 검사를 다시 실행해 성립하지 않는 문항을 센다 (모델 호출 없음).

`verify_chain_items.database`가 만든 SQLite에서 요소에 해당하는 표(또는 열)를 비우고 `check`를 다시 실행한다.
요소가 온전할 때 통과한 문항이 그 요소를 비운 뒤 통과하지 못하면 그 문항은 그 요소에 의존한다.
빈 정답 문항은 묶음 소속을 비워도 재유도 결과가 빈 채로 같으므로 통과하며, 처분을 비우면 빈 정답의 근거가 사라져 탈락한다.

사용: python3 measure_chain_schema_ablation.py --items <chain_items_admitted.jsonl> --out <json> [--phase2-root <dir>] [--phase4-root <dir>]
저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

from verify_chain_items import check, database

ABLATIONS = {
    "document_disposition": "DELETE FROM disposition",
    "wg_meeting_of_disposition": "UPDATE disposition SET meeting = NULL",
    "revision_link": "DELETE FROM revision",
    "pack_membership": "DELETE FROM pack_member",
    "tsg_meeting_of_pack": "UPDATE pack SET tsg = NULL",
    "clause_modified_by_cr": "DELETE FROM section_change",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--phase2-root", type=Path, help="재구축한 phase-2 파일이 WG별로 놓인 디렉토리")
    parser.add_argument("--phase4-root", type=Path, help="그래프에서 내보낸 phase-4 파일이 WG별로 놓인 디렉토리")
    args = parser.parse_args()
    items = [json.loads(line) for line in args.items.read_text().splitlines()]
    families = sorted({item["family"] for item in items})
    total = collections.Counter(item["family"] for item in items)
    broken: dict[str, collections.Counter] = {name: collections.Counter() for name in ABLATIONS}
    intact_failures = 0
    for wg in sorted({item["wg"] for item in items}):
        own = [item for item in items if item["wg"] == wg]
        db, sha_of = database(wg, args.phase2_root, args.phase4_root), {}
        intact_failures += sum(bool(check(item, db, sha_of)) for item in own)
        for name, statement in ABLATIONS.items():
            db.execute("SAVEPOINT ablation")
            db.execute(statement)
            for item in own:
                if check(item, db, sha_of):
                    broken[name][item["family"]] += 1
            db.execute("ROLLBACK TO ablation")
            db.execute("RELEASE ablation")
    report = {"items": len(items), "failuresWithAllElements": intact_failures, "itemsByFamily": dict(total),
              "ablations": [{"element": name, "brokenItems": sum(broken[name].values()),
                             "brokenByFamily": {family: broken[name][family] for family in families}}
                            for name in ABLATIONS]}
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
