"""처분을 묻는 문항 가운데, 근거 문서에 원문 확인·문서 전체 범위가 아닌 처분 기록이 함께 있는 문항을 센다 (모델 호출·DB 접근 없음).

질문이 처분의 범위를 적어야 하는 이유를 재는 측정이다. 문항의 `evidence`에 실린 문서마다 그 문서를 대상으로 한
처분 기록을 모두 읽어, `evidenceStatus`가 `source_verified`가 아니거나 범위가 `whole_target`이 아닌 기록이 하나라도
있으면 그 문항을 센다. 처분 기록은 `--phase2-root` 아래 작업반 폴더의 `decision_dispositions.jsonld` 에서 읽는다
(기본값은 저장된 Phase-2 인스턴스).

사용 (저장소 루트에서 실행): python3 measure_mixed_record_items.py --items <jsonl> [<jsonl> ...] --out <json>
          [--phase2-root <dir>]
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

INSTANCES = Path("ontology/output/tsg/RAN/formal/instances/phase-2")


def other_records(root: Path, wg: str) -> dict[str, list[dict]]:
    found: dict[str, list[dict]] = collections.defaultdict(list)
    for record in json.loads((root / wg / "decision_dispositions.jsonld").read_text())["@graph"]:
        scope = json.loads(record["assessmentMethod"]).get("scope")
        if record["evidenceStatus"] != "source_verified" or scope != "whole_target":
            found[record["dispositionTarget"]].append({"dispositionId": record["dispositionId"], "code": record["dispositionCode"],
                                                       "evidenceStatus": record["evidenceStatus"], "scope": scope})
    return found


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--phase2-root", type=Path, default=INSTANCES)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    counts: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    listed = []
    root = args.phase2_root
    for items_path in args.items:
        items = [json.loads(line) for line in items_path.read_text().splitlines()]
        others = {wg: other_records(root, wg) for wg in sorted({item["wg"] for item in items})}
        for item in items:
            if "disposition" not in item["fields"]:
                continue
            counts[item["family"]]["items"] += 1
            mixed = {entry["document"]: others[item["wg"]]["tdoc:" + entry["document"]] for entry in item["evidence"]
                     if "document" in entry and others[item["wg"]].get("tdoc:" + entry["document"])}
            if mixed:
                counts[item["family"]]["mixed"] += 1
                counts[item["family"]]["mixed:" + item["wg"]] += 1
                listed.append({"id": item["id"], "family": item["family"], "documents": mixed})
    report = {"itemFiles": [str(path) for path in args.items], "phase2Root": str(root),
              "families": {family: dict(counter) for family, counter in sorted(counts.items())},
              "mixedItems": len(listed), "items": listed}
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({key: report[key] for key in ("families", "mixedItems")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
