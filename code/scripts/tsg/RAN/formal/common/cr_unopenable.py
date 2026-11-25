"""현재 파서로 열 수 없음을 확인한 CR 문서 목록과 파싱 오류의 분류 규칙.

Phase-4 CR 문서 파서는 오류가 있는 CR 이 하나라도 있으면 1 로 끝나 Phase-11 CR-1 연쇄를 멈춘다.
코퍼스에는 암호화된 OOXML을 OLE 형식으로 저장한 문서나 IRM으로 보호된 문서가 있다.
이 목록은 확인한 파일의 열기 실패를 일반 파싱 오류와 구분한다. 경로와 파일 해시가 일치하는
실패를 따로 집계하고, 새 파일이나 내용이 바뀐 파일의 열기 실패는 일반 오류로 유지한다.

그래서 열 수 없음을 확인한 파일을 WG 마다 고정 목록(파서 옆 `known_unopenable.json`)에 적고,
목록에 있는 실패만 따로 센다. 목록 항목은 경로 · sha256 · 원인 · 확인 방법을 갖는다.

목록에 있는 실패로 인정하는 조건(셋 다):
- 그 CR 의 오류가 모두 문서 열기 실패에서 나온 것이다(`OPEN_FAILURE_PREFIXES`). 열린 뒤에 난
  오류(서식 표 없음 등)는 목록과 무관하게 오류다.
- `source_path` 가 목록에 있다.
- 지금 파일의 sha256 이 목록에 적은 값과 같다. 바이트가 바뀌었으면 확인 근거도 사라졌으므로
  오류로 센다(목록을 다시 확인하라는 신호).

목록에 있지만 이번 결과에서 확인되지 않은 항목은 `stale`로 돌려준다. 선택 범위에 없는 파일도
포함될 수 있으므로, 전체 처리 대상과 실제 파일을 확인한 뒤 목록의 갱신 여부를 판단한다.
이 반환값은 종료 코드를 바꾸지 않는다.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

LIST_NAME = "known_unopenable.json"

# 문서를 열지 못했을 때 파서가 남기는 오류 문구의 머리. 두 번째는 열지 못해 번호도 못 읽었을 때 붙는다.
OPEN_FAILURE_PREFIXES = (
    "DOCX open failed",
    "tdocNumber extraction failed (no filename match, cannot open doc)",
)

REQUIRED_KEYS = ("path", "sha256", "cause", "checked_by")


def list_path(parser_dir: Path) -> Path:
    return parser_dir / LIST_NAME


def load(path: Path) -> dict[str, dict]:
    """목록 파일을 읽어 `path → 항목` 으로 돌려준다. 파일이 없으면 빈 목록이다.

    항목에 필수 키가 빠졌거나 같은 경로가 두 번 나오면 목록 자체가 잘못된 것이므로 예외를 낸다.
    """
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    out: dict[str, dict] = {}
    for entry in data.get("entries", []):
        missing = [k for k in REQUIRED_KEYS if not entry.get(k)]
        if missing:
            raise ValueError(f"{path}: 항목에 {missing} 가 없음")
        if entry["path"] in out:
            raise ValueError(f"{path}: 같은 경로가 두 번 나옴")
        out[entry["path"]] = entry
    return out


def is_open_failure_only(errors: list[str]) -> bool:
    return bool(errors) and all(e.startswith(OPEN_FAILURE_PREFIXES) for e in errors)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def split(results, listed: dict[str, dict], project_root: Path):
    """오류가 있는 결과를 `(목록 밖 오류, 확인된 열기 실패, 이번 결과에서 확인되지 않은 목록 경로, sha 불일치 경로)`로 나눈다.

    `results` 는 `errors` · `source_path` 속성을 가진 파서 결과다. 오류가 없는 결과는 어느 쪽에도
    넣지 않는다.
    """
    unlisted, known, sha_mismatch = [], [], []
    seen = set()
    for r in results:
        if not r.errors:
            continue
        entry = listed.get(r.source_path)
        if entry is None or not is_open_failure_only(r.errors):
            unlisted.append(r)
            continue
        p = project_root / r.source_path
        if not p.is_file() or file_sha256(p) != entry["sha256"]:
            sha_mismatch.append(r.source_path)
            unlisted.append(r)
            continue
        seen.add(r.source_path)
        known.append(r)
    stale = sorted(set(listed) - seen - set(sha_mismatch))
    return unlisted, known, stale, sha_mismatch
