"""결정 기록의 처분 코드를 3GPP 문서 목록의 문서 상태와 견준다 (모델 호출 · 데이터베이스 질의 없음).

처분 기록(phase-2 `decision_dispositions.jsonld`)은 회의 보고서 본문에서 만들고, 문서 목록의 전역 상태
(phase-1 `tdocs.jsonld` 의 `tdoc:status`)를 쓰지 않는다(`decision_disposition.py` 머리말). 그래서 문서 목록의
상태는 같은 결정을 사무국이 따로 적은 독립 출처다. 다만 상태는 회의가 끝난 시점의 문서 하나당 값 하나이고,
기록은 결정 하나당 하나이므로, 한 문서를 여러 결정이 다루면 앞선 결정의 코드는 최종 상태와 다를 수 있다.

비교 규칙은 이름 일치 하나다: 상태 문자열을 소문자로 바꾸고 공백을 밑줄로 바꾼 값이 처분 코드 이름과 같으면
일치로 센다. 코드 이름이 아닌 상태(available · reserved · treated · approved 등)는 비교 분모에서 빼고 교차표에만
남긴다. 두 파일 모두 줄 단위로 읽는다(파일 전체를 json 으로 올리지 않는다).

사용 (저장소 루트에서):
    .venv/bin/python3 -I scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/measure_disposition_vs_tdoc_status.py --out <json>
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
BASE = ROOT / "ontology/output/tsg/RAN/formal/instances"
WGS = ["RAN1", "RAN2", "RAN3", "RAN4", "RAN5"]
CODES = {"agreed", "withdrawn", "rejected", "noted", "postponed", "revised", "ambiguous", "endorsed", "not_pursued",
         "partially_agreed", "conditionally_agreed", "not_agreed", "not_treated", "merged", "not_concluded", "replied_to"}
FIELD = re.compile(r'^\s*"(dispositionId|dispositionCode|targetTdocNumber|evidenceStatus|assessmentMethod)": (".*"),?$')


def tdoc_status(wg: str) -> dict[str, str]:
    out, current = {}, None
    with (BASE / "phase-1" / wg / "tdocs.jsonld").open(encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r'^\s*"tdoc:tdocNumber": "([^"]+)"', line)
            if m:
                current = m.group(1)
                continue
            m = re.match(r'^\s*"tdoc:status": "([^"]*)"', line)
            if m and current:
                out[current] = m.group(1)
                current = None
    return out


def records(wg: str):
    rec = {}
    with (BASE / "phase-2" / wg / "decision_dispositions.jsonld").open(encoding="utf-8") as fh:
        for line in fh:
            if '"@id": "tdoc:decision-disposition/' in line:
                if "dispositionCode" in rec:
                    yield rec
                rec = {}
                continue
            m = FIELD.match(line)
            if m:
                rec[m.group(1)] = json.loads(m.group(2))
    if "dispositionCode" in rec:
        yield rec


def norm(status: str) -> str:
    return re.sub(r"\s+", "_", status.strip().lower())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = {"rule": "status lowercased, spaces to underscores, equal to the disposition code name", "byWg": {}}
    for wg in WGS:
        status = tdoc_status(wg)
        cross = defaultdict(Counter)
        per_target = defaultdict(set)
        missing = 0
        for r in records(wg):
            if r.get("evidenceStatus") != "source_verified":
                continue
            t = r.get("targetTdocNumber")
            s = status.get(t)
            if s is None:
                missing += 1
                continue
            scope = json.loads(r.get("assessmentMethod") or "{}").get("scope")
            cross[r["dispositionCode"]][s] += 1
            per_target[t].add((r["dispositionCode"], scope))
        comparable = {c: sum(n for s, n in row.items() if norm(s) in CODES) for c, row in cross.items()}
        matched = {c: sum(n for s, n in row.items() if norm(s) == c) for c, row in cross.items()}
        targets_comparable = [t for t in per_target if norm(status[t]) in CODES]
        targets_any = sum(1 for t in targets_comparable if any(c == norm(status[t]) for c, _ in per_target[t]))
        out["byWg"][wg] = {
            "sourceVerifiedRecordsWithoutListedStatus": missing,
            "recordsComparable": sum(comparable.values()), "recordsNameMatch": sum(matched.values()),
            "targetsComparable": len(targets_comparable), "targetsWithAnyRecordMatchingStatus": targets_any,
            "byCode": {c: {"comparable": comparable[c], "nameMatch": matched[c], "statuses": dict(cross[c].most_common())}
                       for c in sorted(cross)},
        }
        w = out["byWg"][wg]
        print(f"{wg}: records {w['recordsNameMatch']}/{w['recordsComparable']} "
              f"targets {targets_any}/{len(targets_comparable)} noStatus={missing}", flush=True)
    # 문서 목록에 없는 코드(부분 · 조건부 승인 · 불승인)는 이름 일치가 구조적으로 불가능하므로 따로 센다.
    listed = {norm(s) for w in out["byWg"].values() for v in w["byCode"].values() for s in v["statuses"]} & CODES
    out["sharedVocabulary"] = sorted(listed)
    out["codesWithoutListedStatus"] = sorted(CODES - listed)
    total = [0, 0]
    for wg, w in out["byWg"].items():
        comp = sum(v["comparable"] for c, v in w["byCode"].items() if c in listed)
        match = sum(v["nameMatch"] for c, v in w["byCode"].items() if c in listed)
        w["sharedVocabulary"] = {"comparable": comp, "nameMatch": match, "share": match / comp}
        total[0] += match
        total[1] += comp
        print(f"{wg}: shared-vocabulary records {match}/{comp} = {match / comp:.4f}")
    out["sharedVocabularyAll"] = {"comparable": total[1], "nameMatch": total[0], "share": total[0] / total[1]}
    print(f"all: shared-vocabulary records {total[0]}/{total[1]} = {total[0] / total[1]:.4f}")
    args.out.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
