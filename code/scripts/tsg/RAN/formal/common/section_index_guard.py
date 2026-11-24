"""Phase-4·5가 읽은 절 색인 수를 같은 WG의 Phase-3 파싱 요약과 대조한다.

Phase-4의 CR 연결과 Phase-5의 TRImpact 연결은 이 색인에서 대상 Section을 찾는다.
색인이 일부만 남으면 연결 대상을 찾지 못한 절의 관계가 누락될 수 있으므로,
서로 다른 sectionId 수가 파싱 요약의 ``total.sections``보다 적으면 실행을 중단한다.
요약 경로는 ``parsed_ts/{WG}/parse_summary_release.json``이며 axis에서 결정한다.

Phase-3 JSON-LD 검증기도 release-aware 절 수와 같은 요약 값을 대조한다.
요약 파일이 없거나 값이 양의 정수가 아니면 비교 기준이 없으므로 중단한다.
색인 수가 요약보다 큰 경우에는 다른 출처의 Section이 함께 조회될 수 있어 허용한다.
이 검사는 개수 축소를 판별하며, 각 Section의 신원 일치까지 검증하지는 않는다.
"""
from __future__ import annotations

import json
import sys
from collections.abc import Iterable
from pathlib import Path

_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
_SCRIPTS_COMMON = _ROOT / "scripts" / "common"
if str(_SCRIPTS_COMMON) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_COMMON))
from common import axis  # noqa: E402

SUMMARY_NAME = "parse_summary_release.json"


def summary_path(wg: str, *, root: Path | None = None) -> Path:
    """같은 WG Phase-3 파서의 절 수 요약 파일 경로."""
    return axis.tree_path("ontology_output", wg=wg, doc_type="parsed_ts", root=root) / SUMMARY_NAME


def expected_section_count(wg: str, *, root: Path | None = None) -> int:
    """Phase-3 파서가 센 절 수(`total.sections`). 읽지 못하면 멈춘다."""
    path = summary_path(wg, root=root)
    if not path.is_file():
        raise SystemExit(
            f"[{wg}] Phase-3 절 수 요약이 없어 절 색인의 하한을 세울 수 없다: {path}"
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"[{wg}] Phase-3 절 수 요약을 읽지 못함: {path} ({exc})") from exc
    total = data.get("total") if isinstance(data, dict) else None
    count = total.get("sections") if isinstance(total, dict) else None
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        raise SystemExit(f"[{wg}] Phase-3 절 수 요약의 total.sections 가 양의 정수가 아님: {path}")
    return count


def require_complete_section_index(wg: str, section_ids: Iterable[str], source: str,
                                   *, root: Path | None = None) -> int:
    """읽은 절 색인의 서로 다른 sectionId 수가 Phase-3 파서의 절 수보다 적으면 멈춘다.

    `source` 는 색인을 읽은 곳(파일 경로나 질의 설명)으로, 멈출 때 메시지에 그대로 싣는다.
    통과하면 읽은 절 수를 돌려준다.
    """
    loaded = len({sid for sid in section_ids if sid})
    expected = expected_section_count(wg, root=root)
    if loaded < expected:
        raise SystemExit(
            f"[{wg}] Phase-3 절 색인이 Phase-3 파서가 센 절보다 적다: {loaded} < {expected}\n"
            f"  색인: {source}\n"
            f"  기준: {summary_path(wg, root=root)} total.sections\n"
            f"  덮이거나 일부만 적재된 색인으로 진행하면 절 간선이 오류 없이 빠진다. Phase-3 를 먼저 복구하라."
        )
    return loaded
