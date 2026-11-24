"""질문이 가리키는 CR 묶음 번호가 청크 본문에 나오는지, 기록 구축이 붙인 메타데이터에만 있는지 센다 (모델 호출 없음).

CR 묶음 번호(`RP-…`)는 TSG 총회가 매기는 번호라 작업반 문서에는 대개 적히지 않고, 기록 구축이 총회 기록에서
CR 과 묶음을 이어 청크 메타데이터(`crPackId`)에 붙인다. 이 스크립트는 텍스트 경로 상한 측정의 FTS5 색인을
읽기 전용으로 열어, 질문에 적힌 묶음 번호마다 본문 열에서 맞는 청크 수와 메타데이터 열에서 맞는 청크 수를
센다. 두 열은 같은 토큰화(`unicode61`)를 쓰므로 `RP-223307` 은 두 열 모두 `"rp 223307"` 구절로 찾는다.

문항 단위로는 질문의 묶음 번호가 모두 본문에 한 번 이상 나오는지(`allPacksInText`)를 적고, 작업반·문항 종류마다
집계한다.

사용: PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark \
          python3 measure_pack_link_text_presence.py --items <jsonl> [<jsonl> ...] --out <json>   (저장소 루트에서 실행)
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

from measure_text_route_ceiling import PACK_RE, connect_index

COUNT = "SELECT count(*) FROM search WHERE search MATCH ?"


def phrase(column: str, pack: str) -> str:
    return f'{column} : ("rp {pack.split("-", 1)[1]}")'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    items = [item for path in args.items for item in map(json.loads, path.read_text().splitlines())]
    by_wg: dict[str, list[dict]] = collections.defaultdict(list)
    for item in items:
        by_wg[item["wg"]].append(item)

    rows, packs_seen = [], {}
    for wg, group in sorted(by_wg.items()):
        con = connect_index(wg)
        for item in group:
            packs = list(dict.fromkeys(match.upper() for match in PACK_RE.findall(item["question"])))
            if not packs:
                continue
            counts = {}
            for pack in packs:
                if (wg, pack) not in packs_seen:
                    packs_seen[(wg, pack)] = {"text": con.execute(COUNT, (phrase("text", pack),)).fetchone()[0],
                                              "meta": con.execute(COUNT, (phrase("meta", pack),)).fetchone()[0]}
                counts[pack] = packs_seen[(wg, pack)]
            rows.append({"id": item["id"], "wg": wg, "family": item["family"], "answerable": bool(item["gold"]),
                         "packs": counts, "allPacksInText": all(c["text"] > 0 for c in counts.values()),
                         "anyPackInMeta": any(c["meta"] > 0 for c in counts.values())})
        con.close()

    cells: dict[tuple[str, str], dict[str, int]] = collections.defaultdict(
        lambda: {"items": 0, "answerable": 0, "allPacksInText": 0, "answerableAllPacksInText": 0, "anyPackInMeta": 0})
    for row in rows:
        for cell_key in ((row["wg"], row["family"]), (row["wg"], "*"), ("*", "*")):
            cell = cells[cell_key]
            cell["items"] += 1
            cell["answerable"] += row["answerable"]
            cell["allPacksInText"] += row["allPacksInText"]
            cell["answerableAllPacksInText"] += row["answerable"] and row["allPacksInText"]
            cell["anyPackInMeta"] += row["anyPackInMeta"]
    distinct = collections.Counter((wg, c["text"] > 0, c["meta"] > 0) for (wg, _), c in packs_seen.items())
    report = {
        "scope": "items whose question names an RP- CR pack; FTS5 phrase match per column of the text-route index",
        "items": [str(path) for path in args.items], "itemsNamingPack": len(rows),
        "cells": [{"wg": wg, "family": family, **cell} for (wg, family), cell in sorted(cells.items())],
        "distinctPacks": [{"wg": wg, "inText": t, "inMeta": m, "packs": n}
                          for (wg, t, m), n in sorted(distinct.items())],
        "perItem": rows,
    }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"itemsNamingPack": len(rows),
                      "total": next(c for c in report["cells"] if c["wg"] == "*"),
                      "byWg": [c for c in report["cells"] if c["family"] == "*" and c["wg"] != "*"],
                      "distinctPacks": report["distinctPacks"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
