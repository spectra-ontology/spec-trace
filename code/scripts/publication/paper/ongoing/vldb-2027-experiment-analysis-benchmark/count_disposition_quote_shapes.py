"""원문 확인(`source_verified`) 처분 기록의 인용문이 어떤 형태로 결과를 적는지 WG 별로 센다.

처분 기록 감사(`audit_decision_disposition.py`)는 `Decision:` 줄이 있는 인용에서만 처분 코드를 다시 읽는다.
이 스크립트는 그 줄이 없는 인용이 결과를 어디에 적는지 나눈다. 인용마다 아래 순서로 처음 맞는 형태를 고른다.

- decision_line: 인용에 `Decision:` 이 있다.
- annex_list_row: 인용이 부속서 제목(`Annex …`)이나 표 행(`| … |`)으로 시작한다(합의 CR 목록의 행).
- entry_then_outcome: 인용이 문서 번호와 탭으로 시작한다(문서 항목 줄 아래에 결과어가 온다).
- other: 위 셋이 아니다.

사용: python3 count_disposition_quote_shapes.py --out <json>
저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

INSTANCES = Path("ontology/output/tsg/RAN/formal/instances/phase-2")


def shape(quote: str) -> str:
    text = quote.lstrip()
    if "Decision:" in quote:
        return "decision_line"
    if text.startswith("Annex") or text.startswith("|"):
        return "annex_list_row"
    if re.match(r"R\d-\d+\t", text):
        return "entry_then_outcome"
    return "other"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = {"method": __doc__.split("\n")[0], "workingGroups": {}}
    for wg in range(1, 6):
        graph = json.loads((INSTANCES / f"RAN{wg}" / "decision_dispositions.jsonld").read_text())["@graph"]
        verified = [r for r in graph if r.get("evidenceStatus") == "source_verified"]
        counts = collections.Counter(shape(r.get("evidenceQuote", "")) for r in verified)
        result["workingGroups"][f"RAN{wg}"] = {"sourceVerified": len(verified), **dict(sorted(counts.items()))}
        print(f"RAN{wg}", len(verified), dict(sorted(counts.items())))
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
