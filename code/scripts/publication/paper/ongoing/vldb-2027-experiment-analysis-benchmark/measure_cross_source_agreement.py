"""회의 보고서에서 읽은 처분과 TDoc 목록의 상태 값을 문서별로 맞대어 센다 (모델 호출 없음).

두 값은 서로 다른 원자료에서 온다. 처분 기록(DecisionDisposition)은 Final Report 본문에서,
`tdoc:status`는 사무국 TDoc 목록(XLSX)에서 읽은 값이다. 원문 대조를 통과하고 문서 전체를
대상으로 한(`whole_target`) 처분 기록을 가진 문서마다, 목록의 상태 값이 그 문서의 처분 코드
집합에 들어 있는지 센다. 처분 코드와 목록 상태는 표기만 맞춘다(`not_pursued` = `not pursued`,
`approved` = `agreed`, `endorsed (bl)` = `endorsed`). 목록 상태가 `available`·`reserved`인 문서는
목록에 처분이 적히지 않은 경우이므로 일치·불일치에서 빼고 따로 센다.

문서 범위는 셋으로 나눈다. `allDocuments`는 목록의 모든 문서, `cr`은 목록이 유형 `CR`로 적은 문서
(`tdoc:type == "CR"`, 추적 연결률의 전체 CR 모집단과 같은 정의), `crForm`은 CR 양식을 쓰는 문서 전부
(`@type == tdoc:CR`, `draftCR` · `pCR` 포함)다.

사용: python3 measure_cross_source_agreement.py --out <json>   (저장소 루트에서 실행)
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

INSTANCES = Path("ontology/output/tsg/RAN/formal/instances")
SAME = {"approved": "agreed", "endorsed (bl)": "endorsed"}
LIST_WITHOUT_DISPOSITION = {"available", "reserved"}


def canonical(value: str) -> str:
    value = value.strip().lower().replace("_", " ")
    return SAME.get(value, value)


def measure(wg: str) -> dict:
    load = lambda rel: json.loads((INSTANCES / rel).read_text())["@graph"]
    tdocs = {r["@id"]: r for r in load(f"phase-1/{wg}/tdocs.jsonld") if "tdoc:status" in r}
    codes: dict[str, set[str]] = collections.defaultdict(set)
    for record in load(f"phase-2/{wg}/decision_dispositions.jsonld"):
        if (record["evidenceStatus"] == "source_verified"
                and json.loads(record["assessmentMethod"]).get("scope") == "whole_target"):
            codes[record["dispositionTarget"]].add(canonical(record["dispositionCode"]))
    result = {}
    scopes = (("allDocuments", lambda r: True),
              ("cr", lambda r: r.get("@type") == "tdoc:CR" and r.get("tdoc:type") == "CR"),
              ("crForm", lambda r: r.get("@type") == "tdoc:CR"))
    for label, keep in scopes:
        pairs: collections.Counter[tuple[str, str]] = collections.Counter()
        compared = agree = missing_target = list_silent = 0
        for target, code_set in codes.items():
            record = tdocs.get(target)
            if record is None:
                missing_target += label == "allDocuments"
                continue
            if not keep(record):
                continue
            status = canonical(record["tdoc:status"])
            if status in LIST_WITHOUT_DISPOSITION:
                list_silent += 1
                continue
            compared += 1
            if status in code_set:
                agree += 1
            else:
                pairs[(status, "+".join(sorted(code_set)))] += 1
        result[label] = {
            "listWithoutDisposition": list_silent, "compared": compared, "agree": agree,
            "agreeShare": round(agree / compared, 4) if compared else None,
            "differences": [{"listStatus": s, "reportCodes": c, "n": n}
                            for (s, c), n in pairs.most_common(15)],
        }
        if label == "allDocuments":
            result[label]["targetsAbsentFromTdocList"] = missing_target
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = {wg: measure(wg) for wg in ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")}
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    for wg, row in result.items():
        for label in ("allDocuments", "cr", "crForm"):
            cell = row[label]
            print(wg, label, cell["listWithoutDisposition"], cell["compared"], cell["agree"], cell["agreeShare"],
                  [(d["listStatus"], d["reportCodes"], d["n"]) for d in cell["differences"][:5]])


if __name__ == "__main__":
    main()
