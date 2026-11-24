"""문서 목록의 묶음 번호(`tdoc:tsgCRPack`)와 묶음 기록(`CRPack.hasCR`)의 일치를 작업반별로 센다 (모델 호출 없음).

묶음 소속을 말하는 출처는 둘이다. 문서 목록은 문서마다 묶음 번호 한 칸을 두고, 묶음 기록은 묶음마다 소속 CR을 든다.
문항의 정답은 묶음 기록에서 나오므로, 두 출처가 갈리는 문서가 얼마나 되는지와 그 문서가 문항에 들어갔는지를 본다.
문항 쪽 차단은 `verify_chain_items.py`의 묶음 출처 일치 검사가 맡는다.

사용 (저장소 루트에서 실행):
  python3 measure_pack_source_agreement.py --wg RAN1 RAN2 RAN3 RAN4 --out <json>
  python3 measure_pack_source_agreement.py --wg RAN5 --phase4-root <root> --out <json>
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

INSTANCES = Path("ontology/output/tsg/RAN/formal/instances")
PACK_NUMBER = re.compile(r"RP-\d+")


def as_list(value) -> list[str]:
    return [] if value is None else value if isinstance(value, list) else [value]


def measure(wg: str, phase4_root: Path | None) -> dict:
    packs = INSTANCES / f"phase-4/{wg}/crpacks.jsonld"
    if phase4_root and (phase4_root / wg / packs.name).exists():
        packs = phase4_root / wg / packs.name
    member = collections.defaultdict(set)
    for record in json.loads(packs.read_text())["@graph"]:
        for cr in as_list(record.get("hasCR")):
            member[cr].add(record["@id"].rsplit("/", 1)[-1])
    counts: collections.Counter[str] = collections.Counter()
    for record in json.loads((INSTANCES / f"phase-1/{wg}/tdocs.jsonld").read_text())["@graph"]:
        if "tdoc:tdocNumber" not in record:
            continue
        value = str(record.get("tdoc:tsgCRPack", "")).strip()
        recorded = member.get(record["@id"], set())
        if not PACK_NUMBER.fullmatch(value):
            counts["packRecordOnly" if recorded else "neither"] += 1
        elif value in recorded:
            counts["same"] += 1
        elif recorded:
            counts["differentPack"] += 1
        else:
            counts["documentListOnly"] += 1
    return {"wg": wg, "packRecords": str(packs), **{key: counts[key] for key in
            ("same", "differentPack", "documentListOnly", "packRecordOnly", "neither")}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--wg", nargs="+", required=True)
    parser.add_argument("--phase4-root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = {"byWg": [measure(wg, args.phase4_root) for wg in args.wg]}
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
