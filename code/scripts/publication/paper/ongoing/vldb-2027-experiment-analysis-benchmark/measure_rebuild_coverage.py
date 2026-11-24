"""재구축한 처분 기록이 반영 전 인스턴스에 견주어 넓힌 범위를 센다 (모델 호출·DB 접근 없음).

작업반마다 반영 전 인스턴스(`integration/before/{WG}`)와 재구축 산출물(`disposition_rebuild/{WG}`)을 같은 방법으로 센다.
- records: 처분 기록 수
- sourceVerified: 그중 `evidenceStatus`가 `source_verified`인 기록 수
- packCrs: 총회 CR 묶음에 실린 CR 수(CR 확장 기록에 `belongsToCRPack`이 있는 CR)
- packCrsWithDisposition: 그중 문항 생성기와 같은 조건(원문 확인 · 문서 전체 범위 · 회의에 결속된 결정)의 처분이 있는 CR 수

사용 (저장소 루트에서 실행): PYTHONPATH=scripts/common python3 measure_rebuild_coverage.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_chain_items import Chain  # noqa: E402

LOGS = Path("logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark")
STATES = {"stored": LOGS / "integration/before", "rebuilt": LOGS / "disposition_rebuild"}


def measure(wg: str, root: Path) -> dict:
    records = json.loads((root / wg / "decision_dispositions.jsonld").read_text())["@graph"]
    chain = Chain(wg, phase2_root=root)
    pack_crs = [identifier for identifier, packs in chain.pack_of.items() if packs]
    return {"records": len(records),
            "sourceVerified": sum(record["evidenceStatus"] == "source_verified" for record in records),
            "packCrs": len(pack_crs),
            "packCrsWithDisposition": sum(bool(chain.dispositions.get(identifier)) for identifier in pack_crs)}


def main() -> None:
    report = {wg: {state: measure(wg, root) for state, root in STATES.items()} for wg in ("RAN1", "RAN2", "RAN3", "RAN4")}
    (LOGS / "rebuild_coverage.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    for wg, states in report.items():
        print(wg, json.dumps(states))


if __name__ == "__main__":
    main()
