"""cr_identity.py — CR 문서 파일의 식별자(spec · CR 번호 · tdoc)를 Phase-4 기록에서 받는다.

Phase-8 CR 파서가 파일명을 정규식 하나로 따로 해석하면 두 가지가 틀어진다.

    정규식이 거절한 파일명     `RP-190773 Correction to …` · 번호 뒤에 작업 항목이 붙은 꼴 등.
                               그 CR 은 경고 한 줄만 남기고 청크에서 통째로 빠진다
    파일명 오타                `…_R3-2229341.docx` 의 틀린 tdoc 이 그대로 식별자가 된다

Phase-4 는 같은 입력 파일마다 CR 기록을 남기고, 그 기록이 Neo4j 에 올라간 CR 의 정본이다.
그래서 식별자는 Phase-4 기록에서 받는다.

    tdoc     `cr_documents.json` 의 `tdoc_number`
    spec     같은 기록의 `spec_number` → 표지(`cover_sheets.json`)의 `spec` → 파일명
    CR 번호  파일명의 `_CR0123r1` → 표지의 `cr_number`(+ `rev`) → 같은 기록의 `cr_number`(+ `rev`, CR 서식에서 읽은 값)

기록과 파일은 입력 디렉토리 아래의 상대 경로로 잇는다(기록의 `source_path` 에서 입력 디렉토리의
`{WG}/…` 부분 뒤). 기록이 없는 파일(같은 CR 을 다른 Release 폴더 · 팩에 다시 배포한 사본 · 표지 ·
CR 묶음 문서 · Phase-4 가 거절한 파일)은 다음 차례로 기록을 찾는다.

    Phase-4 중복 표 Phase-4 가 중복으로 걸러 낸 사본의 경로 → tdoc(`metadata.duplicate_paths`).
                      다른 팩에 `RP-… was R3-…` 처럼 이름을 바꿔 다시 실린 사본은 이 길로만 닿는다
    같은 파일 이름    그 이름의 기록이 하나뿐일 때. 사본은 이름이 같고, 이름이 파일명 정규식에
                      읽히지 않는 사본(`RP-…` 이름 · 작업 항목이 붙은 꼴)은 이 길로만 기록에 닿는다
    파일명의 tdoc     파일명 해석이 되고 그 tdoc 이 기록에 있을 때

어느 쪽도 없으면 파일명 해석을 그대로 쓴다.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

#: 파일명 해석. `(spec, "CR0123r1", tdoc)` 또는 None. 각 WG 파서의 `parse_filename`.
FilenameParser = Callable[[str], "tuple[str, str, str] | None"]

_CR_IN_NAME = re.compile(r"_CR(\d+(?:r\d+)?)_")


def _records(data: dict) -> list[dict]:
    return data.get("documents") or data.get("cr_documents") or []


def cr_label(entry: dict) -> str:
    """`cr_number`(숫자) 와 `rev` 를 가진 표지 칸 · Phase-4 기록 → `CR0123r1` 꼴 라벨. 개정이 없거나 0 이면 `CR0123`."""
    number = (entry.get("cr_number") or "").strip()
    if not number:
        return ""
    rev = (entry.get("rev") or "").strip()
    return f"CR{number}r{rev}" if rev.isdigit() and rev != "0" else f"CR{number}"


class CRIdentity:
    """한 WG 의 CR 입력 파일 → `(spec, cr_number, tdoc)`."""

    def __init__(self, wg: str, phase4_dir: Path, input_dir: Path, parse_filename: FilenameParser):
        self.input_dir = input_dir
        self.parse_filename = parse_filename
        parts = input_dir.parts
        marker = "/" + "/".join(parts[parts.index(wg):]) + "/"

        self.by_tail: dict[str, dict] = {}
        self.by_tdoc: dict[str, dict] = {}
        self.by_name: dict[str, dict | None] = {}
        self.dup_tail: dict[str, str] = {}
        doc_path = phase4_dir / "cr_documents.json"
        if doc_path.exists():
            with open(doc_path, encoding="utf-8") as f:
                data = json.load(f)
            for source, tdoc in (data.get("metadata", {}).get("duplicate_paths") or {}).items():
                source = "/" + source.replace("\\", "/")
                if marker in source:
                    self.dup_tail[source.split(marker, 1)[1]] = tdoc
            for rec in _records(data):
                tdoc = rec.get("tdoc_number") or ""
                if not tdoc:
                    continue
                self.by_tdoc[tdoc] = rec
                source = "/" + (rec.get("source_path") or "").replace("\\", "/")
                if marker in source:
                    self.by_tail[source.split(marker, 1)[1]] = rec
                name = source.rsplit("/", 1)[1]
                self.by_name[name] = None if name in self.by_name else rec

        self.cover: dict[str, dict] = {}
        cover_path = phase4_dir / "cover_sheets.json"
        if cover_path.exists():
            with open(cover_path, encoding="utf-8") as f:
                data = json.load(f)
            for pack in data.get("crpacks", data.get("cover_sheets", [])):
                for entry in pack.get("cr_entries", []):
                    if entry.get("tdoc_number"):
                        self.cover[entry["tdoc_number"]] = entry

    def recorded(self, path: Path) -> bool:
        """Phase-4 가 이 파일 자체를 기록했는가."""
        return self._tail(path) in self.by_tail

    def _tail(self, path: Path) -> str:
        try:
            return path.relative_to(self.input_dir).as_posix()
        except ValueError:
            return path.name

    def record(self, path: Path) -> dict | None:
        """이 파일의 Phase-4 기록. 경로 → 중복 표 → 같은 파일 이름 → 파일명의 tdoc 차례로 찾는다."""
        tail = self._tail(path)
        rec = self.by_tail.get(tail)
        if rec is None and tail in self.dup_tail:
            rec = self.by_tdoc.get(self.dup_tail[tail])
        if rec is None:
            rec = self.by_name.get(path.name)
        if rec is None:
            from_name = self.parse_filename(path.name)
            if from_name:
                rec = self.by_tdoc.get(from_name[2])
        return rec

    def resolve(self, path: Path) -> tuple[str, str, str] | None:
        """`(spec, cr_number, tdoc)`. 기록도 없고 파일명도 읽히지 않으면 None."""
        from_name = self.parse_filename(path.name)
        rec = self.record(path)
        if rec is None:
            return from_name

        tdoc = rec["tdoc_number"]
        cover = self.cover.get(tdoc, {})
        spec = (rec.get("spec_number") or cover.get("spec") or (from_name[0] if from_name else "")).strip()
        if from_name:
            cr_number = from_name[1]
        else:
            m = _CR_IN_NAME.search(path.name)
            cr_number = f"CR{m.group(1)}" if m else (cr_label(cover) or cr_label(rec))
        return spec, cr_number, tdoc
