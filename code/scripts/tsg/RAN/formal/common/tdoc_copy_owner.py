"""같은 회의의 중복 문서를 제목과 파일명으로 대조해 TDoc별 입력을 선택한다.

서로 다른 TDoc 폴더에 바이트가 같은 문서가 있으면 KG의 TDoc 메타데이터와
파싱 본문이 같은 자료를 가리키는지 확인한다. 파일명이 변경된 사본도 있으므로
제목을 먼저 비교한 뒤 파일명 앞부분의 TDoc 번호를 확인한다.

1. 문서의 첫 ``Title:`` 문단과 같은 회의 KG의 제목을 비교한다. 문단의 값이
   비어 있으면 다음 문단을 읽는다. 두 제목의 영문·숫자 토큰 집합이 비어 있지
   않고 한 집합이 다른 집합에 포함되면 일치로 판정한다. 중복 묶음 안에서 일부
   제목만 일치할 때 나머지 TDoc의 문서 선택을 제외한다.
2. 제목으로 구분되지 않으면 파일명 앞의 번호를 확인한다. 현재 TDoc와 다른
   번호이고 그 번호가 같은 중복 묶음에 있을 때 현재 선택을 제외한다.
3. 구분할 근거가 없거나 묶음 전체가 제외될 경우에는 기존 선택을 유지한다.

토큰 추출은 영문 연속 문자열과 숫자 연속 문자열을 분리한다. 예를 들어
``TS38.213``과 ``TS 38.213``은 같은 토큰 집합이 된다. 부분 겹침 비율의
임계값을 사용하지 않으며, 집합 포함 관계만 검사한다.

제외된 TDoc 폴더에 다른 DOCX·DOCM 파일이 있으면 ``own_document``가
현재 TDoc 제목에만 일치하는 후보를 찾는다. 기존 중복 문서와 바이트가 같은
후보는 제외하고, 유일한 후보가 있을 때만 반환한다.
선택이 폴더의 기본 규칙과 달라지면 03 본문 파서가 ``RECORD``에 상대 경로를
저장한다. 04 그림 추출과 05 수식 추출은 이 기록을 읽어 같은 문서를 사용한다.

호출자는 KG 제목 조회를 현재 회의로 제한해야 한다. 다른 회의의 제목을
함께 조회하면 문서와 등록 메타데이터의 대응을 잘못 판정할 수 있다.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable, Iterable

import docx_text

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(ROOT / "scripts/common"))
from common.atomic_io import write_json_atomic

_FIELD = re.compile(r"Title\s*:\s*(.*)$", re.I | re.S)
_TOKEN = re.compile(r"[a-z]+|\d+")
_LEAD = re.compile(r"(?:draft[\s_-]*)?([A-Za-z]+\d*)[-_ ](\d+)(?!\d)", re.I)


def doc_title(docx: Path) -> str:
    """문서 본문의 제목 칸 값. 칸이 없거나 본문을 읽지 못하면 빈 문자열."""
    try:
        with zipfile.ZipFile(docx) as z:
            root = ET.fromstring(docx_text.zip_part(z, "word/document.xml"))
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError):
        return ""
    paras = [text for p in root.iter(docx_text._P) if (text := docx_text.final_text(p))]
    for i, p in enumerate(paras):
        m = _FIELD.match(p)
        if m:
            v = m.group(1).strip()
            return v or (paras[i + 1] if i + 1 < len(paras) else "")
    return ""


def title_tokens(s: str) -> set[str]:
    return set(_TOKEN.findall(s.lower()))


def titles_agree(doc: str, kg: str) -> bool:
    d, k = title_tokens(doc), title_tokens(kg)
    return bool(d) and bool(k) and (d <= k or k <= d)


def lead_number(file_name: str) -> str | None:
    """파일 이름 앞머리의 TDoc 번호(`X-N` 꼴, 초안 표시 허용). 없으면 None."""
    m = _LEAD.match(file_name)
    return f"{m.group(1).upper()}-{m.group(2)}" if m else None


def byte_groups(picks: dict[str, Path]) -> list[list[str]]:
    """크기가 같은 후보의 SHA를 비교하여 동일 바이트 문서의 TDoc 묶음을 반환한다."""
    by_size: dict[int, list[str]] = {}
    for n, p in picks.items():
        try:
            by_size.setdefault(p.stat().st_size, []).append(n)
        except OSError:
            continue
    groups: list[list[str]] = []
    for nums in by_size.values():
        if len(nums) < 2:
            continue
        by_digest: dict[str, list[str]] = {}
        for n in nums:
            h = hashlib.sha256()
            with open(picks[n], "rb") as fh:
                for block in iter(lambda: fh.read(1 << 20), b""):
                    h.update(block)
            by_digest.setdefault(h.hexdigest(), []).append(n)
        groups.extend(sorted(g) for g in by_digest.values() if len(g) > 1)
    return sorted(groups)


def foreign_copies(picks: dict[str, Path],
                   kg_titles: Callable[[Iterable[str]], dict[str, str]],
                   number_of: Callable[[str], str]) -> dict[str, tuple[str, list[str]]]:
    """한 회의의 문서 선택에서 제외할 TDoc와 판정 근거를 반환한다.

    입력은 {TDoc 번호: 선택 문서}이고 반환값은 {번호: (``title`` 또는 ``name``,
    같은 중복 묶음의 다른 번호 목록)}이다. ``kg_titles``는 현재 회의의 제목을
    조회하고, ``number_of``는 WG 파서의 TDoc 번호 정규화 규칙을 적용한다.
    """
    groups = byte_groups(picks)
    if not groups:
        return {}
    titles = kg_titles(sorted({n for g in groups for n in g}))
    out: dict[str, tuple[str, list[str]]] = {}
    for g in groups:
        dt = doc_title(picks[g[0]])
        agree = {n: titles_agree(dt, titles.get(n, "")) for n in g}
        if any(agree.values()) and not all(agree.values()):
            how, drop = "title", [n for n in g if not agree[n]]
        else:
            members = set(g)
            how = "name"
            drop = []
            for n in g:
                lead = lead_number(picks[n].name)
                if lead and number_of(lead) != number_of(n) and number_of(lead) in members:
                    drop.append(n)
        if len(drop) == len(g):
            continue
        for n in drop:
            out[n] = (how, [m for m in g if m != n])
    return out


def _same_bytes(a: Path, b: Path) -> bool:
    try:
        if a.stat().st_size != b.stat().st_size:
            return False
    except OSError:
        return False
    return a.read_bytes() == b.read_bytes()


def own_document(tdoc_folder: Path, picks: Iterable[Path], kg_title: str,
                 other_titles: Iterable[str]) -> Path | None:
    """중복 문서가 제외된 TDoc 폴더에서 제목이 유일하게 일치하는 문서를 찾는다.

    후보는 폴더 아래의 `.docx` · `.docm` 이다(하위 폴더 포함, `__MACOSX` · `._*` · `~$*` 제외). `picks` 는 이
    회의에서 번호마다 고른 문서(제외된 번호 포함)이고, 그중 어느 것과 바이트가 같은 후보는 제외한다.
    남은 후보 가운데 제목 칸이 `kg_title` 과 맞고 `other_titles`(같은 묶음 다른 번호의 KG 제목) 어느 것과도
    맞지 않는 문서가 꼭 하나일 때만 그 문서를 돌려준다. 둘 이상이면 고를 근거가 없다.
    """
    others = [t for t in other_titles if t]
    taken = list(picks)
    hits = []
    for f in sorted(tdoc_folder.rglob("*")):
        if (not f.is_file() or f.suffix.lower() not in (".docx", ".docm")
                or f.name.startswith(("._", "~$")) or "__MACOSX" in f.relative_to(tdoc_folder).parts):
            continue
        if any(_same_bytes(f, t) for t in taken):
            continue
        dt = doc_title(f)
        if titles_agree(dt, kg_title) and not any(titles_agree(dt, o) for o in others):
            hits.append(f)
    return hits[0] if len(hits) == 1 else None


#: 03 이 폴더 규칙과 다른 문서를 읽은 번호의 산출 폴더에 두는 기록 — TDoc 폴더 기준 상대 경로 목록.
RECORD = "documents.json"


def _recorded_path(tdoc_folder: Path, relative: str) -> Path:
    """기록은 TDoc 폴더 안의 상대 문서 경로만 가리킨다. 존재 여부는 호출자가 판정한다."""
    if not isinstance(relative, str) or not relative:
        raise ValueError("Recorded document paths must be nonempty strings")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or path == Path("."):
        raise ValueError("Recorded document paths must stay inside the TDoc folder")
    document = tdoc_folder / path
    if not document.resolve().is_relative_to(tdoc_folder.resolve()):
        raise ValueError("Recorded document symlinks must stay inside the TDoc folder")
    return document


def sync_record(parsed_dir: Path, tdoc_folder: Path, documents: Iterable[Path] | None) -> None:
    """`documents` 가 있으면 기록을 쓰고, None 이면(폴더 규칙대로 읽는 번호) 남은 기록을 지운다."""
    rec = parsed_dir / RECORD
    if documents is None:
        rec.unlink(missing_ok=True)
        return
    relative = [str(Path(d).relative_to(tdoc_folder)) for d in documents]
    for name in relative:
        _recorded_path(tdoc_folder, name)
    parsed_dir.mkdir(parents=True, exist_ok=True)
    write_json_atomic(rec, {"documents": relative})


def recorded_documents(parsed_dir: Path, tdoc_folder: Path) -> list[Path] | None:
    """03 이 기록한 문서 목록. 기록이 없으면 None — 폴더 규칙(`tdoc_documents`)을 따른다."""
    rec = parsed_dir / RECORD
    if not rec.is_file():
        return None
    record = json.loads(rec.read_text(encoding="utf-8"))
    if not isinstance(record, dict) or not isinstance(record.get("documents"), list):
        raise ValueError("Recorded documents must be a list of relative paths")
    return [_recorded_path(tdoc_folder, name) for name in record["documents"]]
