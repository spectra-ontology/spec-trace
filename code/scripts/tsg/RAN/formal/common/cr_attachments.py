#!/usr/bin/env python3
"""cr_attachments.py — CR 팩 안 CR 폴더에 든 첨부 문서를 CR 기록에서 가린다.

팩 디렉토리 `RP-NNNNNN/` 바로 아래 폴더의 이름이 WG 문서 번호로 시작하면(`R5-187808/`) 그 폴더는 그 번호
CR 의 자리다. 폴더 안에는 CR 본문 말고도 그 CR 을 뒷받침하는 문서가 함께 놓인다(시험점 분석 · 토의 문서).
그런 문서는 자기 WG 번호를 머리글 · 파일 이름에 달고 있어 CR 처럼 읽히지만 이 팩이 다룬 CR 이 아니다.

가리는 기준: 기록의 번호가 폴더 번호와 다르고, 폴더 번호의 CR 은 따로 기록되었다. 폴더 번호의 CR 이
기록되지 않았으면 가리지 않는다(번호를 잘못 읽은 CR 본문일 수 있다).

> 주의: RAN5 RP-182272 의 `R5-187808/38.521-1_TPanalysis_7.9_RxSpurious/` 에 든 문서는 머리글이
> `R5-181830` 인 시험점 분석이고 CR 서식이 없다. RAN#82 CR 시트는 RP-182272 에 `R5-187808` 을 `approved` 로
> 두고 `R5-181830` 은 두지 않는다. 이 문서를 CR 로 받으면 그 번호의 CR 이 이 팩에 소속된다.
>
> 주의: Phase-8 은 Phase-4 의 `cr_folder_attachments` 를 읽어 같은 파일을 청크로 만들지 않는다.
> Phase-4 기록이 없는 파일은 파일 이름으로 번호를 읽으므로, 여기서 가린 파일이 다시 CR 로 들어온다.
>
> 주의: Phase-8 이 CR 식별자를 얻지 못한 파일은 두 부류가 CR 이 아니다. 하나는 Phase-4 가 `tsg_direct_cr` 로
> 남긴 TSG 직접 제출 문서다(Spec Step 7 은 CR 을 WG 번호로만 식별한다). 다른 하나는 번호 없이 CR 폴더 안에
> 놓인 문서로, 그 폴더의 CR 이 같은 실행에서 청크를 냈다. RAN5 의 `R5-181031/4.2.20+4.2.21 TT/` 같은 시험
> 허용치 · 시험점 분석 문서가 이 부류다. 둘을 파싱 실패로 세면 실패 수가 부풀고 RAN5 성공률이 기준 아래로
> 떨어진다. 폴더 CR 이 청크를 내지 못했으면 그 파일은 실패로 남긴다(번호를 못 읽은 CR 본문일 수 있다).
>
> 주의: CR 팩 안에 놓였어도 CR 서식이 없는 문서는 CR 이 아니다(`split_no_form`). RAN1 RP-260581 의
> `Clause7.3_R1-2601731/R1-2601731.docx` 는 Tdoc 목록 Type 이 `discussion` 인 TR 38.769 평가 결과 문서로, 팩
> 표지와 CR 시트에 없다. 기록으로 받으면 그 번호가 팩 디렉토리 소속으로 CRPack 에 들고 `:CR` 레이블을 얻는다.
> RAN5 RP-240954 의 `R5-244000/` 에는 CR 시트 · 표지가 38.903 CR0758 rev2 로 두는 번호에 다른 문서(PRD21
> 완료 선언서)가 들었다. 이 번호의 CR 소속은 표지에서 오므로 기록을 빼도 남고, 빠지는 것은 CR 본문이 아닌
> 글뿐이다. 같은 번호의 사본 가운데 하나라도 서식이 있으면 그 번호는 빼지 않는다(중복 제거가 그 사본을 고른다).
> Phase-8 은 `no_cr_form` 의 경로를 읽어 그 문서를 청크로 만들지 않는다. 번호가 아니라 경로로 가리는 것은
> 이름에 CR 번호가 없는 문서(`R1-2601731.docx`)가 Phase-4 기록이 빠지면 식별자를 얻지 못하기 때문이다.
>
> 주의: 큰 CR 은 본문을 여러 파일로 나눠 한 CR 폴더에 담는다. RAN4 RP-190403 의
> `38.133_CR0064_(Rel-15)_R4-1902690/` 은 CR 서식과 3 · 4 · 6 ~ 10 절을 담은 `38.133-s0-11 after RAN4_90 v3.docx`
> 곁에 부속서 A.1 ~ A.5 · A.6 ~ A.8 · B 를 담은 파일 셋을 두고, 서식의 `Clauses affected` 는 그 부속서 절
> (`A.3` ~ `A.7` · `B.2`)을 적는다. 곁 파일은 번호도 서식도 없어 식별자를 얻지 못하므로, 가르지 않으면 CR 본문의
> 부속서 변경이 청크에서 통째로 빠지고 그 파일은 실패로 남는다. 이어지는 본문은 `continuations` 가 가른다.
> 같은 자리의 시험점 분석 문서(RAN5 `R5-201871/38.521-3_TP_analysis_38.905_….docx`)는 이어지는 본문이 아니다.
> 그 CR 의 영향 절은 서식이 든 파일이 이미 다 담고, 분석 문서의 제목 절은 다른 규격(TR 38.905)의 것이다.
>
> 주의: TSG 직접 제출 팩은 표지 하나와 본문 파일을 함께 둔다(RAN4 RP-182887 의 `RP-182887 Cover.docx` 와
> `RP-182887 CR for 38101-2-f30 ….docx`, RP-190569 의 `company CR 38.133 A1-A5 …` 등). Phase-4 는 서식이 든
> 파일만 `tsg_direct_cr` 로 남기므로 곁의 본문 파일은 식별자 없는 파일이 된다. 같은 디렉토리에 TSG 직접 제출
> 기록이 있고 WG 번호 CR 기록이 하나도 없으면 그 파일도 TSG 직접 제출 문서로 센다(`split_unidentified`).

Spec: docs/tsg/RAN/formal/RAN5/phase-4/design-spec/tdoc_ontology_specs(CR).md Step 7 §2·§3;
      docs/tsg/RAN/formal/RAN5/phase-8/design-spec/tdoc_vectordb_specs(CR).md §2.3.
Ontology: Phase-4 CR 문서 신원과 분류 메타데이터.
Cycle: Phase-4 기록과 Phase-8 입력 분류.
배경: CR 폴더 첨부와 TSG 직접 제출 문서를 CR 본문에서 가른다.
사용: Phase-4와 Phase-8 파서에서 분류 함수를 호출한다.
LLM 호출: 없음.

"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import docx_text  # noqa: E402 — styleId 를 스타일 이름 · 개요 수준으로 푸는 자리

_PACK_DIR = re.compile(r"RP[-_]\d{6}(?!\d)")

METADATA_KEY = "cr_folder_attachments"
NO_FORM_KEY = "no_cr_form"
#: Phase-4 파서가 서식 본문 표(`cr_form.is_form_table`)를 찾지 못한 기록에 남기는 오류.
NO_FORM_ERROR = "CR Form Table not found"


def folder_tdoc(source_path: str, tdoc_re: re.Pattern, norm) -> str | None:
    """팩 디렉토리 바로 아래 폴더 이름의 WG 번호. 파일이 팩 디렉토리에 바로 놓였으면 None."""
    parts = source_path.replace("\\", "/").split("/")
    for i, part in enumerate(parts[:-1]):
        if _PACK_DIR.fullmatch(part):
            if i + 1 >= len(parts) - 1:
                return None
            m = tdoc_re.match(parts[i + 1])
            return norm(m.group(1)) if m else None
    return None


def split(results: list, tdoc_re: re.Pattern, norm) -> tuple[list, dict[str, str]]:
    """(첨부가 아닌 기록, {첨부 문서 경로: 그 폴더의 CR 번호})."""
    own = {r.tdoc_number for r in results if r.tdoc_number}
    kept, attachments = [], {}
    for r in results:
        folder = folder_tdoc(r.source_path, tdoc_re, norm)
        if folder and r.tdoc_number and r.tdoc_number != folder and folder in own:
            attachments[r.source_path] = folder
        else:
            kept.append(r)
    return kept, attachments


def split_no_form(results: list) -> tuple[list, dict[str, str]]:
    """(남길 기록, {CR 서식이 없는 문서 경로: 그 문서 번호}).

    같은 번호의 기록 가운데 서식이 있는 것이 하나도 없는 번호만 뺀다. 번호 없는 기록은 두고 번호 추출 실패로 센다.
    """
    with_form = {r.tdoc_number for r in results if r.tdoc_number and NO_FORM_ERROR not in r.errors}
    kept, no_form = [], {}
    for r in results:
        if r.tdoc_number and r.tdoc_number not in with_form:
            no_form[r.source_path] = r.tdoc_number
        else:
            kept.append(r)
    return kept, dict(sorted(no_form.items()))


def recorded_no_form(cr_documents: Path) -> dict[str, str]:
    """Phase-4 `cr_documents.json` 이 CR 서식이 없어 뺀 {문서 경로(저장소 루트 기준): 문서 번호}. 사본마다 경로가 있다."""
    if not cr_documents.exists():
        return {}
    with open(cr_documents, encoding="utf-8") as f:
        meta = json.load(f).get("metadata", {})
    return dict(meta.get(NO_FORM_KEY) or {})


def recorded_attachments(cr_documents: Path) -> set[str]:
    """Phase-4 `cr_documents.json` 이 첨부로 가린 문서 경로(저장소 루트 기준)."""
    if not cr_documents.exists():
        return set()
    with open(cr_documents, encoding="utf-8") as f:
        meta = json.load(f).get("metadata", {})
    return set(meta.get(METADATA_KEY) or {})


def _tsg_direct_and_wg_dirs(cr_documents: Path) -> tuple[set[str], set[str]]:
    """(TSG 직접 제출 문서 경로, WG 번호 CR 기록이 놓인 디렉토리). 경로는 저장소 루트 기준이다."""
    wg_dirs: set[str] = set()
    tsg_direct = recorded_tsg_direct(cr_documents, wg_dirs=wg_dirs)
    return tsg_direct, wg_dirs


def recorded_tsg_direct(cr_documents: Path, *, wg_dirs: set[str] | None = None) -> set[str]:
    """Phase-4 `cr_documents.json` 이 TSG 직접 제출 문서로 남긴 경로(저장소 루트 기준).

    `wg_dirs` 를 주면 같은 파일의 WG 번호 CR 기록 디렉토리를 그 집합에 추가한다. 파일이 없으면 집합은
    그대로 둔다. 생략하면 WG 기록은 검사하지 않고 TSG 직접 제출 경로만 반환한다.
    """
    if not cr_documents.exists():
        return set()
    with open(cr_documents, encoding="utf-8") as f:
        data = json.load(f)
    meta = data.get("metadata", {})
    tsg_direct = {d["source_path"] for d in meta.get("tsg_direct_cr") or [] if d.get("source_path")}
    if wg_dirs is not None:
        records = data.get("documents") or data.get("cr_documents") or []
        recorded_dirs = {str(Path(r["source_path"]).parent) for r in records
                         if r.get("tdoc_number") and r.get("source_path")}
        wg_dirs.update(recorded_dirs)
    return tsg_direct


def norm_tdoc(tok: str) -> str:
    """폴더 이름의 번호를 표준 꼴로(`R1_1900001` → `R1-1900001`, `R5s 240123` → `R5s240123`)."""
    return tok.replace(" ", "").replace("_", "-")


def split_unidentified(paths: list[str], cr_documents: Path, chunked: set[str],
                       tdoc_re: re.Pattern, norm=norm_tdoc) -> tuple[dict[str, list[str]], list[str]]:
    """식별자를 얻지 못한 파일(저장소 루트 기준 경로)을 CR 이 아닌 문서와 실패로 가른다.

    반환은 ({"tsg_direct": [...], "folder_attachment": [...]}, 실패 경로). `chunked` 는 이 실행에서 청크를 낸
    WG 문서 번호다.
    """
    tsg_direct, wg_dirs = _tsg_direct_and_wg_dirs(cr_documents)
    tsg_dirs = {str(Path(p).parent) for p in tsg_direct}
    excluded: dict[str, list[str]] = {"tsg_direct": [], "folder_attachment": []}
    failures: list[str] = []
    for p in paths:
        parent = str(Path(p).parent)
        if p in tsg_direct or (parent in tsg_dirs and parent not in wg_dirs):
            excluded["tsg_direct"].append(p)
        elif (folder := folder_tdoc(p, tdoc_re, norm)) and folder in chunked:
            excluded["folder_attachment"].append(p)
        else:
            failures.append(p)
    return excluded, failures


#: CR 서식 `Clauses affected` 칸의 절 번호(`6.1` · `8.2` · `A.3` · `B.2`). 문서 번호(`R4-1812082`)의 숫자는 아니다.
_CLAUSE = re.compile(r"(?<![\w.-])([A-Z]\.\d+(?:\.\w+)*|\d+[A-Za-z]?(?:\.\w+)*)")
_PARA = re.compile(r"<w:p[ >].*?</w:p>", re.S)
#: 문단의 스타일 ID 와 문단이 직접 정한 본문 아닌 개요 수준.
_PARA_STYLE = re.compile(r'<w:pStyle w:val="([^"]*)"')
_PARA_OUTLINE = re.compile(r'<w:outlineLvl w:val="[0-8]"')
#: 스타일 부품이 없는 문서에서만 쓰는 제목 스타일 ID 꼴.
_HEADING_ID = re.compile(r"[Hh]eading|berschrift|H\d")
_HEADING_NUMBER = re.compile(r"(?:Annex\s+)?([A-Z]\.\d+(?:\.\w+)*|[A-Z]|\d+[A-Za-z]?(?:\.\w+)*)(?=[\s:(]|$)")
#: CR 서식 표의 판 표지(`CR-Form-v11.2`). 이 글이 든 파일은 다른 CR 이다.
_FORM_MARK = re.compile(r"CR-Form-v\d")


def _document_xml(docx: Path) -> tuple[str, frozenset[str] | None] | None:
    """(`word/document.xml` 글, 제목 스타일 ID). 스타일 부품이 없으면 제목 스타일 ID 는 None."""
    try:
        with zipfile.ZipFile(docx) as z:
            xml = z.read("word/document.xml").decode("utf-8", "replace")
            names, outline = docx_text.style_table(z)
    except (OSError, KeyError, zipfile.BadZipFile):
        return None
    return xml, (frozenset(outline) if names else None)


def heading_clauses(xml: str, heading_styles: frozenset[str] | None = None) -> set[str]:
    """`word/document.xml` 의 제목 문단이 여는 절 번호.

    제목 문단은 스타일이 본문 아닌 개요 수준을 가진 문단(`heading_styles`, `docx_text.style_table` 의 개요 수준 표)과
    문단이 직접 본문 아닌 개요 수준을 정한 문단이다.

    주의: styleId 의 꼴로 제목을 고르지 않는다. 다른 언어판 Word 로 저장한 문서는 제목 스타일의 styleId 가 `2` ·
    `40` · `Titre2` 따위로 바뀌어 `Heading` 으로 시작하지 않고, 숫자 styleId 는 제목이 아닌 스타일에도 붙는다
    (같은 `5` 가 어느 문서에서는 heading 5, 다른 문서에서는 heading 4 의 ID 다). 이름과 개요 수준은 스타일 부품에만
    있다. 스타일 부품이 없는 문서(`heading_styles` 가 None)만 styleId 의 꼴을 본다.
    """
    out: set[str] = set()
    for para in _PARA.findall(xml):
        m = _PARA_STYLE.search(para)
        sid = m.group(1) if m else ""
        if heading_styles is None:
            heading = bool(sid and _HEADING_ID.match(sid))
        else:
            heading = sid in heading_styles
        if not (heading or _PARA_OUTLINE.search(para)):
            continue
        text = re.sub(r"<[^>]+>", "", para.replace("<w:tab/>", "\t")).strip()
        m = _HEADING_NUMBER.match(text)
        if m:
            out.add(m.group(1))
    return out


def _covered(clause: str, heads: set[str]) -> bool:
    return any(h == clause or h.startswith(clause + ".") for h in heads)


def continuations(kept: dict[str, Path], dir_tdocs: dict[Path, set[str]], unresolved: list[Path],
                  clauses: dict[str, str]) -> dict[str, list[Path]]:
    """{CR 번호: 그 CR 본문이 이어지는 파일(읽을 차례)}.

    `kept` 는 {CR 번호: 청크를 만들 파일}, `dir_tdocs` 는 {디렉토리: 그 안에서 식별된 CR 번호}, `unresolved` 는
    식별자를 얻지 못한 파일, `clauses` 는 {CR 번호: 서식의 `Clauses affected` 글}이다. 이어지는 파일은

    * 청크를 만들 파일과 같은 디렉토리에 놓이고, 그 디렉토리는 팩 디렉토리가 아니며 식별된 CR 이 그 하나뿐이다.
    * CR 서식 표가 없다.
    * 서식이 든 파일의 제목 절이 담지 않은 영향 절을 하나라도 제목 절로 연다.

    차례는 그 파일이 처음 여는 영향 절의 서식 순서, 같으면 파일 이름 순서다.

    주의: 영향 절을 서식 파일이 다 담으면 곁 파일은 이어지는 본문이 아니다. 시험점 분석처럼 다른 규격의 절을 다루는
    뒷받침 문서는 그 절 번호가 영향 절과 겹쳐도 여기서 걸러진다.
    """
    by_dir: dict[Path, list[Path]] = {}
    for f in unresolved:
        by_dir.setdefault(f.parent, []).append(f)
    out: dict[str, list[Path]] = {}
    for tdoc, main in kept.items():
        siblings = by_dir.get(main.parent)
        if not siblings or _PACK_DIR.fullmatch(main.parent.name) or dir_tdocs.get(main.parent) != {tdoc}:
            continue
        wanted = list(dict.fromkeys(_CLAUSE.findall(clauses.get(tdoc) or "")))
        main_xml = _document_xml(main)
        if not wanted or main_xml is None:
            continue
        own = heading_clauses(*main_xml)
        missing = [c for c in wanted if not _covered(c, own)]
        if not missing:
            continue
        found = []
        for f in siblings:
            xml = _document_xml(f)
            if xml is None or _FORM_MARK.search(xml[0]):
                continue
            heads = heading_clauses(*xml)
            hits = [i for i, c in enumerate(missing) if _covered(c, heads)]
            if hits:
                found.append((min(hits), f.name, f))
        if found:
            out[tdoc] = [f for *_, f in sorted(found)]
    return out
