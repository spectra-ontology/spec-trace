#!/usr/bin/env python3
"""backfill_section_spec_number.py — 이미 적재된 그래프에서 빠진 Section.specNumber 를 채운다.

정의는 `scripts/common/common/section_spec_number.py` 에 있다. 값은 그 절의 유일한
`BELONGS_TO_SPEC` 대상(release-키 Spec)의 `specNumber` 다. 적재기도 같은 값을 적재할 때
쓰므로, 이 도구는 그 SET 없이 적재된 그래프의 빈자리만 메운다.

채우는 것과 채우지 않는 것
--------------------------
상태가 `missing` 이고 sectionId 머리(`{specNumber}-{specRelease}-`)가 소속 Spec 과 맞는 절만
채운다. 값이 이미 있는 절은 같든 다르든 건드리지 않는다. 다른 값(`disagree`)이나 정의로 값을
정할 수 없는 절(`noOwner` · `multiOwner` · `badOwner`), 머리가 어긋난 절(`ownerIdMismatch`)은
관계 쪽이 틀렸을 수 있으므로 보고만 하고 exit 1 로 끝낸다. 그 절들은 TS 구조를 다시 적재하거나
`ts_hierarchy_repair.py` 로 소속을 바로잡을 일이다.

기록
----
`--apply` 는 쓰기 전에 채울 절의 elementId · sectionId · 옮길 값과 소속 Spec 을
`logs/tsg/RAN/formal/<WG>/phase-3/section_spec_number_backfill.json` 에 덧적는다. 사전 상태는
"값 없음" 하나이므로 되돌리기는 기록된 elementId 의 `specNumber` 를 지우는 것이다. 기록에
실패하면 쓰지 않는다. 쓰기는 소속 Spec 하나마다 한 트랜잭션이고, 기록 뒤 사전 상태가 바뀐
절이 하나라도 있으면 그 트랜잭션을 되돌린다.

기본은 dry-run 이고 dry-run 은 읽기 전용 세션만 연다. 다시 돌리면 채울 것이 없어 아무것도
하지 않는다.

Spec:     docs/tsg/RAN/formal/RAN1/phase-3/design-spec/tdoc_ontology_specs(TS).md Step 5 §3.1 · Step 6 §3
Gate:     scripts/common/data-integrity/check_section_spec_number.py
Cycle:    Section 신원 속성의 정의 · 적재 · 감사를 한 정의로 묶는다.
LLM 호출: 없음

사용:
    python3 scripts/tsg/RAN/formal/common/backfill_section_spec_number.py --wg ALL
    python3 ... --wg RAN2 --apply
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from neo4j import READ_ACCESS, WRITE_ACCESS, GraphDatabase

PROJECT_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
_SCRIPTS_COMMON = PROJECT_ROOT / "scripts" / "common"
if str(_SCRIPTS_COMMON) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_COMMON))
from common import axis, credentials, section_spec_number  # noqa: E402
from document_decision_storage import durable_json  # noqa: E402

BOLT_PORTS = axis.bolt_ports(("RAN",), include_plenary=True)
JOURNAL = "section_spec_number_backfill.json"
UNFIXABLE = ("disagree", "noOwner", "multiOwner", "badOwner", "ownerIdMismatch")


def _record(wg: str, entries: list[dict]) -> Path:
    path = axis.tree_path("logs", wg=wg, phase="phase-3") / JOURNAL
    path.parent.mkdir(parents=True, exist_ok=True)
    runs = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    runs.append({"applied_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "tool": Path(__file__).resolve().relative_to(PROJECT_ROOT).as_posix(),
                 "preimage": "specNumber absent",
                 "entries": entries})
    durable_json(path, runs)
    return path


def _report(wg: str, r: dict, examples: int) -> None:
    print(f"[{wg}] Section {r['sections']} · agree {r['agree']} · missing {r['missing']} · "
          f"disagree {r['disagree']} · noOwner {r['noOwner']} · multiOwner {r['multiOwner']} · "
          f"badOwner {r['badOwner']} · ownerIdMismatch {r['ownerIdMismatch']}")
    for key in ("missing", *UNFIXABLE):
        for ex in (r.get(f"{key}Examples") or [])[:examples]:
            print(f"  {key}: {ex}")


def run_wg(wg: str, apply: bool, examples: int) -> int:
    # 예시 수집은 상태가 다른 행의 null 을 일부러 건너뛴다. 그 사실을 알리는 서버 경고를 끈다.
    driver = GraphDatabase.driver(axis.bolt_uri(wg), auth=credentials.neo4j_auth(),
                                  notifications_min_severity="OFF")
    try:
        with driver.session(default_access_mode=READ_ACCESS) as session:
            before = section_spec_number.audit(session, examples)
            plan = section_spec_number.fill_plan(session) if before["missing"] else []
        _report(wg, before, examples)
        if before["sections"] == 0:
            print("  Section 라벨 없음 — 채울 것 없음")
            return 0

        fill = sum(len(g["sections"]) for g in plan)
        print(f"  채울 절 {fill} (소속 Spec {len(plan)}개) · 보류 {before['missing'] - fill}")
        for g in plan[:examples]:
            print(f"    {g['specNumber']} {g['specRelease']}: {len(g['sections'])}절 "
                  f"(예 {g['sections'][0]['sectionId']})")
        unfixable = sum(before[k] for k in UNFIXABLE)
        if unfixable:
            print(f"  🔴 이 도구가 고치지 않는 상태 {unfixable}건 — 소속 관계를 먼저 바로잡을 일")

        if not plan:
            return 1 if unfixable else 0
        if not apply:
            print("  (dry-run. 채우려면 --apply)")
            return 1 if unfixable else 0

        entries = [{"spec": g["spec"], "specNumber": g["specNumber"],
                    "specRelease": g["specRelease"], "sections": g["sections"]} for g in plan]
        path = _record(wg, entries)
        print(f"  되돌림 기록: {path.relative_to(PROJECT_ROOT)}")
        with driver.session(default_access_mode=WRITE_ACCESS) as session:
            written = sum(section_spec_number.fill_group(session, g) for g in plan)
        print(f"  specNumber {written} 채움")

        with driver.session(default_access_mode=READ_ACCESS) as session:
            after = section_spec_number.audit(session, examples)
        _report(wg, after, examples)
        left = section_spec_number.blocking_count(after)
        if written != fill or after["missing"] != before["missing"] - fill or left:
            print(f"  🔴 채운 뒤에도 남음: {left}")
            return 1
        return 0
    finally:
        driver.close()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wg", required=True, choices=["ALL", *BOLT_PORTS])
    ap.add_argument("--apply", action="store_true", help="실제로 채운다 (기본은 dry-run)")
    ap.add_argument("--examples", type=int, default=5, help="상태마다 보일 예시 수")
    args = ap.parse_args(argv[1:])
    targets = list(BOLT_PORTS) if args.wg == "ALL" else [args.wg]
    return max(run_wg(wg, args.apply, args.examples) for wg in targets)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
