"""실무 질문 유형 판정을 두 번째 판정자의 판정과 대조해 일치 수를 센다 (모델 호출 없음).

첫 판정은 `measure_practitioner_question_sources.py` 의 결과 파일(`judgments`)에서 읽는다. 두 번째 판정은 정의·문항 종류
예시·질문 파일만 받은 별도 에이전트가 적은 목록이며, 첫 판정과 측정 산출물은 보지 않았다. 이 스크립트는 판정을 만들지
않고 다음을 검사·집계한다.

- 두 판정의 질문 단위가 1:1로 일치하는지 검사한다(빠지거나 남는 단위가 있으면 종료 코드 1).
- 두 번째 판정이 근거로 적은 인용 구절이 그 단위의 질문 파일에 글자 그대로 있는지 검사한다(없으면 종료 코드 1).
- 유형(`type`)이 같은 단위 수, 그리고 첫 판정에서 과정 기록을 묻는 단위(`process_trace`·`mixed`) 가운데
  대응(`familyMapping`)이 같은 단위 수를 센다. 다른 단위는 두 판정을 나란히 적는다.

사용: python3 measure_practitioner_judge_agreement.py --first <practitioner_question_sources.json>
          --second <second-judge judgments json> --out <json>   (저장소 루트에서 실행)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from measure_practitioner_question_sources import IDENTIFYING, question_units

SECOND_JUDGE = "정의·문항 종류 예시·질문 파일만 받은 별도 에이전트(첫 판정과 측정 산출물은 보지 않음)"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    first = {row["unit"]: row for row in json.loads(args.first.read_text())["judgments"]}
    second = {row["unit"]: row for row in json.loads(args.second.read_text())["secondJudgments"]}
    units = question_units()
    problems = [f"두 번째 판정이 없는 단위: {u}" for u in sorted(set(first) - set(second))]
    problems += [f"첫 판정이 없는 단위: {u}" for u in sorted(set(second) - set(first))]
    problems += [f"사례 폴더에 없는 단위: {u}" for u in sorted(set(second) - set(units))]
    for unit, row in second.items():
        text = "\n".join(path.read_text() for path in units.get(unit, ()))
        if row["quote"] not in text:
            problems.append(f"인용 구절이 질문 파일에 없음: {unit}: {row['quote']}")
        if IDENTIFYING.search(row["quote"]):
            problems.append(f"인용 구절에 식별 정보 표지: {unit}")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        raise SystemExit(1)

    shared = sorted(first)
    type_diff = [{"unit": u, "first": first[u]["type"], "second": second[u]["type"]}
                 for u in shared if first[u]["type"] != second[u]["type"]]
    process = [u for u in shared if first[u]["type"] != "interpretation"]
    mapping_diff = [{"unit": u, "first": first[u]["familyMapping"], "second": second[u]["familyMapping"],
                     "secondNearestFamily": second[u]["nearestFamily"]}
                    for u in process if first[u]["familyMapping"] != second[u]["familyMapping"]]
    report = {
        "units": len(shared), "secondJudge": SECOND_JUDGE,
        "typeAgreement": [len(shared) - len(type_diff), len(shared)], "typeDisagreements": type_diff,
        "mappingAgreementOnProcessOrMixed": [len(process) - len(mapping_diff), len(process)],
        "mappingDisagreements": mapping_diff,
        "secondJudgments": [second[u] for u in shared],
    }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "secondJudgments"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
