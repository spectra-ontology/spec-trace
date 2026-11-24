"""원본 문서 파일에서 글자를 꺼내고, 색인 청크에서 기록으로 만든 글을 걷어 내는 공용 함수.

원본 글 조건(raw-source)은 독해 모델이 **원본 문서에 적힌 글자와 그 문서 자신의 번호(파일 이름)** 만
보게 한다. 두 가지 일을 한 자리에 둔다.

- `file_text(path)`: 원본 파일 하나(docx · xlsx · pptx · pdf · txt · htm)를 글로 바꾼다. 워드 문서는 다섯 WG 의
  TS · CR · 기고문 파서가 쓰는 공용 판독기 `scripts/tsg/RAN/formal/common/docx_text.py` 로 읽는다 — 청크
  본문과 같은 규칙(`chunk_text`: 수식은 선형 표기, 지운 글은 `[DEL]…[/DEL]`, 표는 행마다 `| 칸 | 칸 |`,
  글상자 글은 그 문단 뒤)이다. 옛 이진 형식(doc · xls · ppt · rtf)은 `convert_legacy` 가 LibreOffice 로
  OOXML 로 바꾼 뒤 같은 함수로 읽는다. zip 은 부르는 쪽이 푼다.
- `raw_chunk_text(collection, chunk_id, text)`: 색인 청크 본문에서 기록 필드로 만든 줄을 걷어 낸다.
  걷어 내는 근거는 `source_text_audit.json` 에 있다.

글로 바꾸지 못한 파일은 조용히 빼지 않고 `ExtractError(reason)` 로 올려 보내, 부르는 쪽이 까닭별로 센다.
"""

from __future__ import annotations

import html
import html.parser
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
DEL_OPEN, DEL_CLOSE = "[DEL]", "[/DEL]"
OOXML_WORD = (".docx", ".docm", ".dotx", ".dotm")
OOXML_SHEET = (".xlsx", ".xlsm", ".xltx", ".xltm")
OOXML_SLIDE = (".pptx", ".pptm", ".ppsx")
LEGACY = {".doc": "docx", ".dot": "docx", ".rtf": "docx", ".odt": "docx", ".xls": "xlsx", ".ods": "xlsx",
          ".ppt": "pptx", ".pps": "pptx", ".odp": "pptx"}
PLAIN = (".txt", ".csv", ".asn", ".asn1", ".xml", ".json", ".diff", ".url")
MARKUP = (".htm", ".html")
NESTED = (".zip",)
#: 글이 없는 형식(그림 · 실행 파일 따위). 까닭 "글 없는 형식" 으로 센다.
NO_TEXT = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".emf", ".wmf", ".exe", ".dll", ".mp4",
           ".avi", ".wav", ".mp3", ".bin", ".dat", ".db")


class ExtractError(Exception):
    """글로 바꾸지 못한 까닭. `reason` 은 집계 열쇠(짧은 낱말)다."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


def _docx_text():
    folder = str(ROOT / "scripts/tsg/RAN/formal/common")
    if folder not in sys.path:
        sys.path.insert(0, folder)
    import docx_text

    return docx_text


def word_text(path: Path) -> str:
    """워드 문서 본문의 글. 머리글 · 바닥글 · 각주는 싣지 않는다(청크 파서와 같다)."""
    docx_text = _docx_text()
    try:
        doc = docx_text.open_document(path)
    except Exception as error:  # python-docx · lxml · zipfile 이 깨진 파일마다 다른 예외를 낸다
        raise ExtractError("워드 문서 열기 실패", f"{type(error).__name__}: {error}"[:200])

    def read(paragraph) -> str:
        return docx_text.chunk_text(paragraph, deleted=docx_text.MARK)

    out: list[str] = []
    try:
        for block in docx_text.body_blocks(doc):
            if docx_text.is_table(block):
                out.extend(docx_text.table_line_rows(block, para=read, deleted=docx_text.MARK))
                continue
            out.append(read(block))
            box = docx_text.box_text(block, read=read)
            if box:
                out.append(box)
    except Exception as error:
        raise ExtractError("워드 본문 읽기 실패", f"{type(error).__name__}: {error}"[:200])
    return "\n".join(out)


def sheet_text(path: Path) -> str:
    import openpyxl

    try:
        book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    except Exception as error:  # openpyxl 은 깨진 파일마다 다른 예외를 낸다
        raise ExtractError("표 문서 읽기 실패", f"{type(error).__name__}: {error}"[:200])
    out: list[str] = []
    try:
        for sheet in book.worksheets:
            out.append(sheet.title)
            for row in sheet.iter_rows(values_only=True):
                cells = ["" if value is None else str(value).strip() for value in row]
                while cells and not cells[-1]:
                    cells.pop()
                if any(cells):
                    out.append("| " + " | ".join(cells) + " |")
    except Exception as error:
        raise ExtractError("표 문서 읽기 실패", f"{type(error).__name__}: {error}"[:200])
    finally:
        book.close()
    return "\n".join(out)


def slide_text(path: Path) -> str:
    import pptx

    try:
        deck = pptx.Presentation(str(path))
    except Exception as error:
        raise ExtractError("발표 문서 읽기 실패", f"{type(error).__name__}: {error}"[:200])
    out: list[str] = []

    def shape_lines(shape) -> None:
        if getattr(shape, "has_text_frame", False) and shape.has_text_frame:
            out.extend(paragraph.text for paragraph in shape.text_frame.paragraphs)
        if getattr(shape, "has_table", False) and shape.has_table:
            for row in shape.table.rows:
                cells = [cell.text.replace("\n", " ").strip() for cell in row.cells]
                if any(cells):
                    out.append("| " + " | ".join(cells) + " |")
        for inner in getattr(shape, "shapes", []) or []:
            shape_lines(inner)

    for slide in deck.slides:
        for shape in slide.shapes:
            shape_lines(shape)
    return "\n".join(out)


def pdf_text(path: Path) -> str:
    import pypdf

    try:
        reader = pypdf.PdfReader(str(path))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                raise ExtractError("암호 걸린 PDF")
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except ExtractError:
        raise
    except Exception as error:
        raise ExtractError("PDF 읽기 실패", f"{type(error).__name__}: {error}"[:200])


class _Markup(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag in ("p", "br", "tr", "div", "li", "h1", "h2", "h3", "h4", "table"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def decode(data: bytes) -> str:
    for encoding in ("utf-8", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1")


def suffix(name: str) -> str:
    return Path(name).suffix.lower()


def file_text(path: Path) -> str:
    """OOXML · PDF · 글 파일 하나의 글. 옛 이진 형식과 zip 은 부르는 쪽이 먼저 바꾸거나 푼다."""
    ext = suffix(path.name)
    if ext in OOXML_WORD:
        return word_text(path)
    if ext in OOXML_SHEET:
        return sheet_text(path)
    if ext in OOXML_SLIDE:
        return slide_text(path)
    if ext == ".pdf":
        return pdf_text(path)
    if ext in PLAIN:
        return decode(path.read_bytes())
    if ext in MARKUP:
        parser = _Markup()
        parser.feed(decode(path.read_bytes()))
        return html.unescape("".join(parser.parts))
    if ext in LEGACY:
        raise ExtractError("옛 형식 변환 필요", ext)
    if ext in NO_TEXT:
        raise ExtractError("글 없는 형식", ext)
    raise ExtractError("다루지 않는 형식", ext or "(확장자 없음)")


def convert_legacy(paths: list[Path], out_dir: Path, profile: Path, timeout: int) -> dict[Path, Path]:
    """옛 이진 형식 파일들을 LibreOffice 로 한꺼번에 OOXML 로 바꾼다. 바뀐 파일만 돌려준다.

    형식마다 따로 부른다(`--convert-to` 는 한 번에 한 형식). 줄기 이름이 겹치면 바뀐 파일이 서로 덮으므로
    부르는 쪽이 파일마다 다른 줄기 이름을 준다. 사용자 설정 폴더(`profile`)를 따로 주어 다른 LibreOffice
    실행과 잠금을 나누지 않는다.
    """
    done: dict[Path, Path] = {}
    by_target: dict[str, list[Path]] = {}
    for path in paths:
        by_target.setdefault(LEGACY[path.suffix.lower()], []).append(path)
    for target, group in by_target.items():
        command = ["soffice", f"-env:UserInstallation=file://{profile}", "--headless", "--norestore",
                   "--convert-to", target, "--outdir", str(out_dir), *map(str, group)]
        try:
            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            subprocess.run(["pkill", "-f", f"UserInstallation=file://{profile}"], check=False)
        for path in group:
            converted = out_dir / f"{path.stem}.{target}"
            if converted.exists() and converted.stat().st_size:
                done[path] = converted
    return done


# 색인 청크에서 걷어 낼 표지. 만든 자리는 `scripts/tsg/RAN/formal/RAN{N}/phase-8/cr-parser/01_parse_cr_chunks.py`
# 의 헤더 청크(`[CR 번호 for 규격]` 첫 줄, 전략 A 의 `Change text: ` 이름표)와 본문 청크 표지
# (`[CR 번호 | 규격 | Section 절]` 따위, RAN4 는 `[CR 번호 for 규격] 제목` 다음 줄에 `Section 절` · `Part i/N` ·
# `Clauses affected: …`). 본문 청크는 절 여러 개를 이어 붙이므로 표지가 청크 가운데에도 온다.
# RAN5 의 표 · 그림 제목 문단은 서식에서 붙인 `[Table] ` · `[Figure] ` 머리를 단다. 근거: source_text_audit.json.
CR_LABEL = re.compile(r"\[CR (?P<cr>[^\]\n|]*?)(?: for [^\]\n|]*| \|[^\]\n]*)?\](?P<title> .*)?")
CR_SECOND = re.compile(r"(?:Clauses affected: .*|Section \S+|Part \d+/\d+)")
CAPTION = re.compile(r"^\[(?:Table|Figure)\] ", re.M)
CHANGE_LABEL = "\nChange text: "


def raw_chunk_text(collection: str, chunk_id: str, text: str) -> tuple[str, list[str]]:
    """청크 본문에서 기록 필드로 만든 줄을 걷어 낸 글과 걷어 낸 줄 목록.

    결정 기록 · 기고문 청크는 그대로 둔다. CR 청크에서는 `[CR …]` 표지 줄(CR 번호 · 규격 · 절 번호 · 제목은
    기록 필드에서 온다)과 RAN4 표지의 둘째 줄을 걷고, 헤더 청크의 `Change text: ` 이름표를 걷되 뒤의 변경
    본문은 남긴다. RAN5 CR 청크는 표 · 그림 제목의 머리말만 걷는다.
    """
    if not collection.endswith("_cr_chunks"):
        return text, []
    removed: list[str] = []
    header = chunk_id.endswith("-header")
    if collection.startswith("ran5_"):
        removed.extend(match.group(0) for match in CAPTION.finditer(text))
        text = CAPTION.sub("", text)
    else:
        lines = text.split("\n")
        kept: list[str] = []
        index = 0
        while index < len(lines):
            line = lines[index]
            match = CR_LABEL.fullmatch(line)
            if match is None:
                kept.append(line)
                index += 1
                continue
            removed.append(line)
            index += 1
            if (match.group("title") and not header and index < len(lines)
                    and CR_SECOND.fullmatch(lines[index])):
                removed.append(lines[index])
                index += 1
        text = "\n".join(kept)
    if header and CHANGE_LABEL in "\n" + text:
        text = ("\n" + text).replace(CHANGE_LABEL, "\n", 1)[1:]
        removed.append(CHANGE_LABEL.strip("\n"))
    return text, removed
