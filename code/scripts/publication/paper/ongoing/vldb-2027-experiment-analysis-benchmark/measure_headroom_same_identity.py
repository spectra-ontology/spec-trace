#!/usr/bin/env python3
"""헤드룸 세 계열의 채택 문항에서 같은 CR 식별자를 가진 다른 문서가 어디에 놓이는지 센다.

같은 CR 식별자 = 규격 번호와 CR 번호가 같은 다른 문서(개정본이 대표적이다).
관문의 같은-식별자 검사(`verify_chain_items.SAME_IDENTITY_PACKS`)는 정답이 anchor CR 의 묶음을
이름 짓는 계열(`verify_chain_items.CR_PACK_COLUMN`)에만 정의돼 있어 세 계열에는 실행되지 않는다.
이 스크립트는 그 범위를 숫자로 기록한다: anchor 문서(또는 anchor 묶음의 구성 문서)에 같은 식별자
문서가 있는 문항 수와, 그런 문서가 정답 행에 들어 있는 문항 수.

점수를 본 뒤에 더한 측정이다. 문항 · 정답 · 채점 · 분석 계획은 건드리지 않고 읽기만 한다.

사용:
    PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark \
        python3 -B scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/measure_headroom_same_identity.py [--out 경로]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True

PROJECT_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
os.chdir(PROJECT_ROOT)
L = Path("logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark")
S = Path("scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark")
H = L / "final/next_cycle/headroom"
sys.path[:0] = [str(PROJECT_ROOT / "scripts/common"), str(PROJECT_ROOT / S)]

import verify_chain_items as GATE  # noqa: E402

# 관문을 돌릴 때 쓴 것과 같은 그래프 원본: RAN5 만 따로 내보낸 phase-4 사본을 읽는다.
PHASE4_ROOT = {"core": None, "ran5": L / "RAN5_graph_export"}

SIBLINGS_OF_DOCUMENT = """
    SELECT o.id, o.number FROM doc a JOIN doc o ON o.cr = a.cr AND o.spec = a.spec AND o.id != a.id
    WHERE a.id = :anchor AND a.cr != '' AND a.spec != ''"""
MEMBERS_OF_PACK = "SELECT cr FROM pack_member WHERE pack_id = :anchor"


def jsonl(path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def measure() -> dict:
    record = json.loads((H / "implementation_record.json").read_text(encoding="utf-8"))
    families: dict[str, dict] = {}
    for part, entry in record["itemFiles"].items():
        text = Path(entry["path"]).read_bytes()
        assert hashlib.sha256(text).hexdigest() == entry["sha256"], f"item file differs from the implementation record: {part}"
        databases: dict = {}
        for item in jsonl(entry["path"]):
            if item["wg"] not in databases:
                databases[item["wg"]] = GATE.database(item["wg"], None, PHASE4_ROOT[part])
            db = databases[item["wg"]]
            anchor_is_pack = item["anchor"].startswith("tdoc:crpack/")
            documents = ([cr for (cr,) in db.execute(MEMBERS_OF_PACK, {"anchor": item["anchor"]})]
                         if anchor_is_pack else [item["anchor"]])
            siblings = {number for document in documents
                        for _, number in db.execute(SIBLINGS_OF_DOCUMENT, {"anchor": document})}
            gold_documents = ({row[item["fields"].index("document")] for row in item["gold"]}
                              if "document" in item["fields"] else None)
            cell = families.setdefault(item["family"], {
                "anchorKind": "cr_pack" if anchor_is_pack else "document", "items": 0,
                "itemsWithSameIdentityDocument": 0, "goldNamesDocuments": gold_documents is not None,
                "itemsWithSameIdentityDocumentInGold": 0 if gold_documents is not None else None,
                "idsWithSameIdentityDocumentInGold": [] if gold_documents is not None else None})
            cell["items"] += 1
            cell["itemsWithSameIdentityDocument"] += bool(siblings)
            if gold_documents is not None:
                # 묶음이 anchor 인 계열에서는 구성 문서 자신이 정답에 있으므로, 정답 문서의 '형제'만 센다.
                own = {number for document in documents
                       for (number,) in db.execute("SELECT number FROM doc WHERE id = ?", (document,))}
                inside = sorted((siblings - own) & gold_documents)
                if inside:
                    cell["itemsWithSameIdentityDocumentInGold"] += 1
                    cell["idsWithSameIdentityDocumentInGold"].append({"id": item["id"], "documents": inside})
        for db in databases.values():
            db.close()
    return {
        "purpose": "Where documents with the same CR identity (same specification and CR number) sit for the admitted "
                   "items of the three headroom families, on which the gate's same-identity check is not defined.",
        "status": "added after the scores were seen; reads items and gate databases only",
        "gateCheckDefinedFor": sorted(GATE.CR_PACK_COLUMN),
        "definition": {
            "sameIdentityDocument": "another document with the same non-empty specification and CR number "
                                    "(the join of verify_chain_items.SAME_IDENTITY_PACKS without its pack clause)",
            "documentAnchor": "counted on the anchor document",
            "packAnchor": "counted on the documents the anchor pack lists (pack_member rows of the gate database)",
            "inGold": "a same-identity document named in the document field of a gold row; for pack anchors only "
                      "documents outside the anchor pack count",
        },
        "families": {family: families[family] for family in sorted(families)},
        "itemFiles": {part: entry["sha256"] for part, entry in record["itemFiles"].items()},
        "scripts": {name: hashlib.sha256((S / name).read_bytes()).hexdigest()
                    for name in ("measure_headroom_same_identity.py", "verify_chain_items.py")},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="헤드룸 세 계열 채택 문항의 같은-CR-식별자 문서 분포를 센다(읽기 전용 측정).")
    parser.add_argument("--out", type=Path, default=H / "same_identity_scope.json", help="기록을 쓸 경로")
    args = parser.parse_args()
    result = measure()
    result["recordedAtUtc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for family, cell in result["families"].items():
        print(family, {key: value for key, value in cell.items() if key != "idsWithSameIdentityDocumentInGold"})
    print("wrote", args.out)


if __name__ == "__main__":
    main()
