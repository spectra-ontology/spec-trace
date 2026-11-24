"""처분 기록 감사(`audit_decision_disposition.py`)에서 기록 코드와 재판독 코드가 다른 사례를 줄의 형태로 가른다.

재판독은 `Decision:` 줄 전체에서 처음 맞는 처분어를 고른다. 한 줄이 두 문서의 결과를 함께 적으면(초안은
endorsed, 최종본은 대상 번호로 agreed) 재판독은 대상 문서가 아닌 쪽의 처분어를 읽는다. 차이마다 아래 순서로
처음 맞는 종류를 고른다. 대상 번호는 처분 기록 id 의 마지막 성분이다.

- outcome_stated_for_target: 줄이 대상 번호를 적고, 대상 번호 바로 앞 절(문장·쉼표·"and" 로 나눈 마지막 조각)이
  기록 코드의 처분어를 담는다. 기록 코드가 대상 문서에 대한 결과다.
- target_revised_into_other_number: 줄이 대상 번호를 적지 않고 다른 문서 번호를 결과의 자리("in <번호>")로 적으며,
  기록 코드가 `revised` 다. 대상 문서는 그 번호로 고쳐졌다.
- conditional_wording: 기록 코드가 `conditionally_agreed` 이고 줄에 조건 표현("in principle"·"assuming")이 있다.
- other: 위 셋이 아니다.

사용: python3 classify_disposition_reread_differences.py --audit <decision_disposition_audit.json> --out <json>
"""
from __future__ import annotations

import argparse
import collections
import json
import re

CODE_WORDS = {
    "agreed": r"\b(?:agreed|approved)\b",
    "endorsed": r"\bendorsed\b",
    "revised": r"\brevised\b",
    "conditionally_agreed": r"\bin principle\b|\bassuming\b",
}
NUMBER = re.compile(r"\bR\d-\d{6,7}\b")


def classify(target: str, recorded: str, line: str) -> str:
    if target in line:
        before = line[: line.index(target)]
        clause = re.split(r"[.;,]\s+|\band\b", before)[-1]
        if re.search(CODE_WORDS.get(recorded, r"$^"), clause, flags=re.I):
            return "outcome_stated_for_target"
    others = [n for n in NUMBER.findall(line) if n != target]
    if recorded == "revised" and target not in line and any(re.search(rf"\bin\s+{re.escape(n)}", line) for n in others):
        return "target_revised_into_other_number"
    if recorded == "conditionally_agreed" and re.search(CODE_WORDS["conditionally_agreed"], line, flags=re.I):
        return "conditional_wording"
    return "other"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    audit = json.load(open(args.audit))
    result = {"audit": args.audit, "workingGroups": []}
    for group in audit["workingGroups"]:
        rows = []
        for diff in group["codeDifferences"]:
            target = diff["dispositionId"].rsplit(":", 1)[1]
            rows.append({**diff, "target": target, "kind": classify(target, diff["recorded"], diff["decisionLine"])})
        result["workingGroups"].append({
            "wg": group["wg"], "withDecisionLine": group["counts"].get("with_decision_line", 0),
            "codeMatch": group["counts"].get("code_match", 0), "differences": len(rows),
            "byKind": dict(collections.Counter(r["kind"] for r in rows)), "rows": rows})
    json.dump(result, open(args.out, "w"), ensure_ascii=False, indent=1)
    for group in result["workingGroups"]:
        print(group["wg"], group["codeMatch"], "/", group["withDecisionLine"], group["byKind"])


if __name__ == "__main__":
    main()
