"""CR 서식의 `Clauses affected` 칸을 원문 docx 에서 다시 읽어 CR→절 연결을 대조하고, 대상 절의 본문 보유를 센다 (모델 호출 없음).

대조 대상은 Phase-4 의 `modifiesSection` 연결 전부다(전수). RAN1~RAN4 는 Phase-4 인스턴스 파일을, RAN5 는
`export_chain_graph_phase4.py` 가 RAN5 그래프에서 내보낸 파일을 읽는다. 빌드가 파싱한 서식(`parsed_cr`)과 빌드의
절 번호 파서(`cr_clause`)는 판정에 쓰지 않고, 서식을 이 스크립트의 판독기로 따로 읽는다.

서식 찾기
- 다섯 작업반의 `derived` 아래 docx·doc 를 파일 이름의 기고 번호(`R1-1803552` · `R5s180525` 꼴)로 색인한다.
- 파일 이름에 번호가 여럿이면(`was R3-…` · 합동 CR) 그 파일이 이 CR 의 서식인지 따로 본다. 서식의 `Clauses affected`
  칸 앞 글에 이 CR 의 번호가 적혀 있거나, 파일 이름의 첫 번호가 이 CR 이면 이 CR 의 서식으로 본다.
- 색인에 없으면 빌드가 기록한 원본 경로(`parsed_cr` 의 `source_path`)를 쓴다. 어느 경로로 찾았는지 연결마다 센다.
- 같은 CR 의 사본이 여럿이면 모두 읽고, 하나라도 확인하면 확인으로 센다. 사본끼리 판정이 갈린 연결 수는 따로 센다.

서식 읽기
- `word/document.xml` 의 표를 행·칸으로 읽는다. 지운 글(`w:del` · `w:moveFrom` 안)은 버리고, 넣은 글은 남긴다.
  필드 코드(`w:instrText`)와 지운 글자(`w:delText`)는 `w:t` 가 아니어서 글로 읽지 않는다. 줄 안 하이픈 요소
  (`w:noBreakHyphen`)는 화면에 보이는 대로 "-" 로 읽어 `Table 5.2-1` · `R1-1911675` 의 하이픈을 남기고, 탭·줄바꿈·기호
  요소(`w:tab` · `w:ptab` · `w:br` · `w:cr` · `w:sym`)는 공백으로 읽는다. 필드 코드는 그 칸이
  문서 속성 필드(`DOCPROPERTY "Spec#"`)인지 가리는 데만 쓴다. 칸 안에 표가 있으면 안쪽 글을 바깥 칸의 글에도 넣는다.
- 칸 이름이 `Clauses affected` 인 칸의 같은 행 뒤 칸들이 절 칸, `Release` 칸의 다음 칸이 release,
  `CR` 칸 앞의 규격 번호가 서식 머리의 규격이다. 머리에서 규격을 못 읽으면 파일 이름 앞머리(`38211_CR…`)를 쓴다.
  `Other specs affected` 행부터 `Other comments` 행 앞까지의 규격 번호를 함께 읽는다.
- 칸 이름의 꼴을 서식마다 적는다: 양식 그대로(`label`), 첫 글자 빠짐(`label_missing_initial`), 이름 뒤 덧붙은 글
  (`label_with_residue`), 칸 이름이 지워져 양식의 자리(`Consequences if not approved` 다음 행)로 찾음
  (`position_after_consequences`).
- 절 칸을 둘러싼 표가 닫히면 읽기를 멈춘다. 서식은 문서 앞머리에 있어서 압축을 처음부터 조금씩 푼다.

판정 (연결 하나마다)
- 서식 머리의 규격만 절 기록과 다르고 파일 이름 앞머리의 규격은 같으면 `header_spec_typo` 다. 절 번호가 칸에
  있는지로 `_clause_listed` · `_clause_not_listed` 를 나눈다. 머리 칸으로는 확인되지 않으므로 확인에 넣지 않는다.
- 서식의 규격이 절 기록의 규격과 다르면 `spec_differs` 다. 절 기록의 규격이 서식 어딘가(절 칸·다른 규격 행)에
  적혔는지로 나눈다. 서식에서 규격을 못 읽었으면 `spec_unread` 다.
- 규격이 같으면 절 번호를 칸에서 찾는다. 앞에서부터 처음 맞는 갈래를 쓴다.
  literal                    칸에 절 번호가 낱말로 그대로 있다(앞뒤에 숫자·글자·`.숫자` 가 붙지 않는다)
  typographic                점 뒤 빈칸, 부록 글자 뒤 점 빠짐(`A1`), 낱말 뒤 붙임표(`Annex-H`), 대소문자만 다르다
  abbreviated_sibling        `7.1/2/3` 처럼 앞 번호의 끝자리만 바꿔 적었다
  range_interior             `5.1-5.3` · `5.1 to 5.3` · `5.1.1-3` 같은 범위 안에 든다
  variant_suffix             절 번호 뒤에 시험 변형 꼬리표가 붙었다(`8.1.1.2.4.NR5GC`)
  asn1_ie_clause_listed     ASN.1 이름 절(`RadioBearerConfig`)이고, 그 IE 를 담은 TS 절 번호가 칸에 있다
  table_or_figure_in_clause  `Table 5.2-1` 처럼 그 절의 표·그림 번호만 적혔다
  descendant_of_listed       칸에 적힌 절의 하위 절이다(칸 `5.1`, 연결 `5.1.2`)
  ancestor_of_listed         칸에 적힌 절의 상위 절이다(칸 `5.1.2`, 연결 `5.1`)
  whole_spec_wording         `all` · `whole` · `various` 같은 말로 규격 전체를 가리킨다
  placeholder                `x.x` · `TBD` · `n/a` 처럼 번호 자리만 있다
  cell_empty                 칸이 비었다
  not_listed                 위 어느 것도 아니다
  확인(confirmed)은 literal 과 표기만 다른 typographic · abbreviated_sibling · range_interior · variant_suffix 다.
  그 밖은 미확인이다. 부록 전체 절(`A`)은 `Annex`·`Section` 같은 말 뒤 목록에 있거나 목록 항목 하나가 그 글자뿐일 때만 적힌 것으로 본다.
- 서식이 없거나(`form_not_found`) 읽을 수 없거나(`form_unreadable`) 절 칸이 없으면(`cell_absent`) 미확인과 따로 센다.
- 규격 갈래(`header_spec_typo_*` · `spec_differs_*` · `spec_unread`)는 서식 머리 규격 칸이 문서 속성 필드인지 손으로 친 글인지 센다.
- 확인된 연결은 절 기록의 판(`Rel-N`)이 서식 release 와 같은지 다른지 나눈다. 판이 다르거나 서식 release 를 못 읽은
  연결은 빌드의 판 해소 규칙(다섯 작업반 Phase-4 빌더의 `SectionIndex.resolve` 가 같은 규칙이다: 목표 판 → 목표 이하
  가장 최신 판 → 가장 최신 판, 목표가 없으면 가장 최신 판)을 서식 release 를 목표로 빌더가 쓰는 절 기록 전체에 다시
  적용해, 규칙이 고르는 판과 연결의 판이 같은지 센다. 다르면 빌드가 파싱한 release(`parsed_cr`)를 목표로 한 번 더 적용해
  차이가 release 를 읽은 값에서 왔는지 본다. 이 대조는 판정을 바꾸지 않는다.
- 확인은 칸을 쓰인 그대로 읽는다(빈칸 없는 쉼표도 목록 구분이다). 확인된 연결 가운데 절 번호가 빈칸 없는 쉼표로
  이웃 번호와 이어져 점을 쉼표로 잘못 친 번호(`6,2,3` = 6.2.3)에 기댔을 수 있는 연결을 따로 센다(`comma_joined`).

본문 보유
- 절 본문 글은 Qdrant 의 TS 절 모음(`ran{N}_ts_sections`, 있으면 `_p12` 모음 포함)에만 있다. 그 근거로 Phase-3 절 기록
  파일의 필드 이름·글 값 최대 길이와, Neo4j Section 노드(RAN1·RAN3·RAN4·RAN5)의 속성 이름·글 값 최대 길이를 함께 적는다.
- same_release: 본문이 빈 글이 아닌 조각 가운데 규격 번호·절 번호가 같고 `specReleases` 에 절 기록의 판이 든 조각이 있다.
- any_release: 규격 번호·절 번호가 같은 조각이 판과 상관없이 있다. `specReleases` 가 없는 `_p12` 조각과,
  ASN.1 이름 절이면 같은 규격·같은 IE 이름의 ASN.1 조각도 넣는다.
- same_release_incl_subclauses: 그 절이나, 같은 규격·같은 판에서 번호가 `절 번호.` 로 시작하는 하위 절 하나라도
  same_release 본문 조각을 가진다. 하위 절을 가진 머리 절은 제 글 없이 하위 절 글만 담는 일이 많아서 따로 센다.
- 작업반의 대상 절(서로 다른 절 기록)과, 총회 묶음에 실린 CR 가운데 연결된 절이 모두 본문을 가진 CR 을 센다.
- 대상 절의 모양(하위 절이 있는가 · 절 기록이 `isVoid` 인가)은 Phase-4 빌더가 쓰는 절 기록 전체에서 읽는다. RAN1~RAN3 은
  Phase-3 절 기록 파일, RAN4 · RAN5 는 Neo4j Section 노드다(RAN4 는 Phase-3 디렉터리가 없고 RAN5 의 Phase-3 은 복구한
  절 기록뿐이다). 판 해소 규칙은 빌더처럼 `BELONGS_TO_SPEC` 간선이 있는 Section 노드만 쓴다.
- 대상 절 기록이 `isVoid` 인 연결과, 그 가운데 같은 규격·같은 절 번호의 다른 판 절 기록은 Void 가 아닌 연결을 센다.
- 하위 절까지 넓혀도 본문이 없는 대상 절은 규격·앞 두 마디 번호로 묶고, 같은 규격의 ASN.1 조각(`tsSectionNumber`)이
  그 절이나 하위 절에 있는지 센다.

사용: python3 -I audit_clause_links.py [--wg RAN1 ...] [--workers N] [--unconfirmed-jsonl <path>] --out <json>
저장소 루트에서 실행한다. 쓰는 파일은 `--out` 과 `--unconfirmed-jsonl` 뿐이다.
"""
from __future__ import annotations

import argparse
import ast
import collections
import concurrent.futures
import hashlib
import html
import json
import os
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

PHASE4 = Path("ontology/output/tsg/RAN/formal/instances/phase-4")
RAN5_EXPORT = Path("logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/RAN5_graph_export/RAN5")
PARSED_CR = Path("ontology/output/tsg/RAN/formal/parsed_cr")
CR_CORPUS = Path("data/corpus/tsg/RAN/formal/change-requests")
QDRANT = "http://localhost:6333"
PHASE3 = Path("ontology/output/tsg/RAN/formal/instances/phase-3")
# 본문 속성이 Section 노드에 있는지 볼 Neo4j HTTP 포트(컨테이너 포트 연결에서 확인한 값). RAN2 는 재구축 작업이
# 그래프를 쓰는 중이어서 묻지 않는다.
NEO4J_HTTP = {"RAN1": 7474, "RAN3": 7476, "RAN4": 7477, "RAN5": 7478}
# Section 노드 속성 집계가 RAN3(1만 6천 노드)에서 1 초, 절 기록 질의가 RAN4(7만 8천 노드)에서 2 초 걸렸다.
# 가장 큰 그래프에서도 넉넉히 끝날 시간이다.
NEO4J_TIMEOUT_S = 300
WGS = ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")
# 절 기록 전체(모양 · 판 해소)의 출처. Phase-4 빌더가 판 해소에 읽는 곳과 같다(RAN1~RAN3 은 파일, RAN4 · RAN5 는 Neo4j).
STRUCTURE_FILE = {wg: PHASE3 / wg / "release-aware" / "sections.jsonld" for wg in ("RAN1", "RAN2", "RAN3")}
STRUCTURE_NEO4J = {wg: NEO4J_HTTP[wg] for wg in ("RAN4", "RAN5")}
RELEASE_NUMBER = re.compile(r"Rel-(\d+)")
# 작업 지시가 정한 하한. 이보다 적으면 무거운 단계를 시작하지 않는다.
MIN_AVAILABLE_GIB = 8

SECTION = re.compile(r"^tdoc:section/(?P<spec>\d{2}\.\d{3}(?:-\d+)?)-(?P<release>Rel-\d+)-(?P<clause>.+)$")
TDOC = re.compile(r"R[1-5](?:-|s)\d{5,7}", re.I)
SPEC = re.compile(r"(?<![\d.])(\d{2})\.(\d{3})(?:-(\d+))?(?![\d])")
FILE_SPEC = re.compile(r"^(\d{2})(\d{3})(?:-(\d+))?_CR", re.I)
TAG = re.compile(r"<(/?)w:(tbl|tr|tc|p|t|tab|ptab|br|cr|sym|noBreakHyphen|del|moveFrom|instrText|fldSimple)(?=[\s/>])[^>]*?(/?)>")
# 절 칸의 칸 이름. 양식 그대로인 이름, 첫 글자가 빠진 이름(`lauses affected`), 이름 뒤에 글이 덧붙은 칸을 함께 받는다.
LABEL = re.compile(r"(?P<word>clauses?|clause\(s\)|sections?|lauses?) affected(?P<rest>(?: .*)?)", re.S)
LABEL_PREFIX = re.compile(r"(?is)^\W*(?:c?lauses?|clause\(s\)|sections?)\s+affected\s*[:：*]*\s*")
DASHES = dict.fromkeys(map(ord, "‐‑‒–—―−﹘﹣－"), "-")
# 절 번호 낱말: 첫 자리는 숫자(끝에 대문자 하나 가능) 또는 부록 글자, 뒤 자리는 `.숫자[글자]` 나 `.글자`,
# 끝에 시험 변형 표시 `_숫자`. 앞뒤에 숫자·글자·`.`·`_` 가 붙으면 낱말이 아니다.
CLAUSE_TOKEN = r"(?:[A-Z]|\d+[A-Za-z]?)(?:\.(?:\d+[A-Za-z]?|[A-Z]))*(?:_\d+)?"
TOKEN = re.compile(rf"(?<![0-9A-Za-z._]){CLAUSE_TOKEN}(?![0-9A-Za-z_]|\.[0-9A-Za-z])")
RANGE = re.compile(rf"(?<![0-9A-Za-z._])({CLAUSE_TOKEN})\s*(?:-|~|\bto\b|\bthrough\b|\buntil\b|\btill\b)\s*({CLAUSE_TOKEN})"
                   r"(?![0-9A-Za-z_]|\.[0-9A-Za-z])", re.I)
SLASH = re.compile(rf"(?<![0-9A-Za-z._])({CLAUSE_TOKEN})((?:\s*/\s*\d+[A-Za-z]?)+)(?![0-9A-Za-z_]|\.[0-9A-Za-z])")
TABLE = re.compile(r"\b(?:tables?|figures?|tab\.|fig\.)\s*([A-Z]?[0-9A-Za-z.]*\d[A-Za-z]?)-\d+[a-z]?", re.I)
WHOLE = re.compile(r"\b(?:all|whole|entire|complete|throughout|various|several|many|every|overall)\b", re.I)
PLACEHOLDER = re.compile(r"^(?:[\sxX.,;:/\-?<>]|\bTBD\b|\bTBC\b|\bn/?a\b|\bnone\b|\bFFS\b)*$", re.I)
CONFIRMED = ("literal", "typographic", "abbreviated_sibling", "range_interior", "variant_suffix")
# 서식을 읽어 판정할 수 없는 갈래. 미확인(notConfirmed)과 따로 센다.
UNAVAILABLE = ("cell_absent", "form_unreadable", "form_not_found")
# 한 연결에 사본이 여럿일 때 고르는 순서: 확인에 가까운 갈래가 앞이다.
PRIORITY = (*CONFIRMED, "header_spec_typo_clause_listed", "asn1_ie_clause_listed", "table_or_figure_in_clause",
            "descendant_of_listed", "ancestor_of_listed", "whole_spec_wording", "placeholder", "cell_empty",
            "not_listed", "header_spec_typo_clause_not_listed",
            "spec_differs_section_spec_named_on_form", "spec_differs_section_spec_not_named",
            "spec_unread", "cell_absent", "form_unreadable", "form_not_found")


def available_gib() -> float:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 2 ** 20
    return 0.0


def memory_guard(step: str) -> float:
    gib = available_gib()
    if gib < MIN_AVAILABLE_GIB:
        raise SystemExit(f"{step}: 사용 가능 메모리 {gib:.1f} GiB 가 {MIN_AVAILABLE_GIB} GiB 보다 적어 멈춘다.")
    return round(gib, 1)


def as_list(value) -> list:
    return [] if value is None else value if isinstance(value, list) else [value]


def graph(path: Path) -> list[dict]:
    return json.loads(path.read_text())["@graph"]


def spec_text(match: re.Match) -> str:
    return f"{match.group(1)}.{match.group(2)}" + (f"-{match.group(3)}" if match.group(3) else "")


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ").translate(DASHES)).strip()


def label(text: str) -> str:
    return re.sub(r"[\s:：*]+", " ", text).strip().lower()


# ---------------------------------------------------------------- 서식 판독


def read_xml(path: Path) -> tuple[str | None, str]:
    """docx 의 본문 XML 을 앞에서부터 늘려 가며 푼다. 서식 표가 닫히면 (판독 결과, 상태)."""
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        head = path.read_bytes()[:8]
        return None, "binary_doc" if head.startswith(b"\xd0\xcf\x11\xe0") else "not_zip"
    with archive:
        names = archive.namelist()
        part = "word/document.xml" if "word/document.xml" in names else next(
            (n for n in names if re.fullmatch(r"word/document\d*\.xml", n)), None)
        if part is None:
            return None, "no_document_part"
        with archive.open(part) as stream:
            data = b""
            # 서식 표는 대개 문서 앞 수십 KB 안에 있다. 처음 256 KiB 를 풀고 표가 덜 닫혔으면 두 배씩 더 푼다.
            want = 256 * 1024
            while True:
                chunk = stream.read(want - len(data))
                data += chunk
                text = data.decode("utf-8", "ignore")
                done = not chunk or len(data) < want
                parsed = parse_cover(text, final=done)
                if parsed is not None or done:
                    return parsed, "ok"
                want *= 2


def parse_cover(xml: str, final: bool):
    """표를 행·칸으로 읽어 서식 칸을 고른다. 절 칸을 담은 바깥 표가 닫혔거나 문서 끝이면 결과, 덜 읽었으면 None."""
    rows: list[list[list[str]]] = []
    depths: list[int] = []
    row_stack: list[list[list[str]]] = []
    cell_stack: list[list[str]] = []
    preamble: list[str] = []
    para: list[str] = []
    fields: dict[int, str] = {}
    depth = deleted = 0
    t_start = instr_start = None

    def flush() -> None:
        # 칸 안에 표를 넣은 서식(절 칸 안의 한 칸짜리 표)이 있어, 안쪽 칸의 글을 그 칸을 담은 바깥 칸들에도 넣는다.
        text = "".join(para)
        for cell in cell_stack or [preamble]:
            cell.append(text)
        para.clear()

    def field(instruction: str) -> None:
        # 서식 머리의 `Spec#` · `Cr#` 칸은 문서 속성 필드(`DOCPROPERTY`)로 채워지는 양식이 있다.
        found = re.search(r"DOCPROPERTY\s+\"?([^\"\s\\]+)", instruction, re.I)
        if found and cell_stack:
            fields.setdefault(id(cell_stack[-1]), f"docproperty:{found.group(1)}")

    for m in TAG.finditer(xml):
        closing, name, selfclose = m.group(1) == "/", m.group(2), m.group(3) == "/"
        if name == "t":
            if closing and t_start is not None:
                if not deleted:
                    para.append(html.unescape(xml[t_start:m.start()]))
                t_start = None
            elif not closing and not selfclose:
                t_start = m.end()
        elif name == "instrText":
            if closing and instr_start is not None:
                field(html.unescape(xml[instr_start:m.start()]))
                instr_start = None
            elif not closing and not selfclose:
                instr_start = m.end()
        elif name == "fldSimple":
            instruction = re.search(r'w:instr="([^"]*)"', m.group(0))
            if not closing and instruction:
                field(html.unescape(instruction.group(1)))
        elif name in ("del", "moveFrom"):
            if not selfclose:
                deleted += -1 if closing else 1
                deleted = max(deleted, 0)
        elif name in ("tab", "ptab", "br", "cr", "sym"):
            if not deleted and not closing:
                para.append(" ")
        elif name == "noBreakHyphen":
            if not deleted and not closing:
                para.append("-")
        elif name == "p" and (closing or selfclose):
            flush()
        elif name == "tc":
            if closing:
                if para:
                    flush()
                if cell_stack:
                    cell_stack.pop()
            elif row_stack:
                cell: list[str] = []
                row_stack[-1].append(cell)
                cell_stack.append(cell)
        elif name == "tr":
            if closing:
                if row_stack:
                    row_stack.pop()
            else:
                row: list[list[str]] = []
                rows.append(row)
                depths.append(depth)
                row_stack.append(row)
        elif name == "tbl":
            depth += -1 if closing else 1
            depth = max(depth, 0)
            if closing and depth == 0:
                found = find_label(rows)
                if found is not None:
                    return summarize_cover(rows, depths, fields, preamble, found)
    if final:
        return summarize_cover(rows, depths, fields, preamble, find_label(rows))
    return None


def cell_text(cell: list[str]) -> str:
    return "\n".join(cell)


def find_label(rows) -> tuple[int, int, str, str] | None:
    """(행, 칸, 칸 이름의 꼴, 칸 이름 뒤에 덧붙은 글).

    양식 그대로인 칸 이름(첫 글자가 빠진 이름 포함)을 먼저 찾는다. 없으면 이름 뒤에 글이 덧붙은 칸(`Clauses affected:1`)을,
    그것도 없으면 칸 이름이 지워진 서식에서 `Consequences if not approved` 행 다음 첫 행(첫 칸이 비고 `Y`/`N` 행이 아닌 행)을
    절 칸 행으로 본다. 양식에서 절 칸 행은 그 자리에 있다.
    """
    residue = None
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            found = LABEL.fullmatch(label(cell_text(cell)))
            if not found:
                continue
            if not found["rest"].strip():
                return r, c, "label_missing_initial" if found["word"].startswith("lause") else "label", ""
            if residue is None:
                residue = (r, c, "label_with_residue", clean(LABEL_PREFIX.sub("", cell_text(cell), count=1)))
    if residue is not None:
        return residue
    for r, row in enumerate(rows):
        if not any(label(cell_text(cell)).startswith("consequences if not approved") for cell in row):
            continue
        for r2 in range(r + 1, len(rows)):
            texts = [clean(cell_text(cell)) for cell in rows[r2]]
            filled = [t for t in texts if t]
            if not filled:
                continue
            if texts[0] or all(t.lower() in ("y", "n") for t in filled) or label(filled[0]).startswith("other specs"):
                return None
            return r2, 0, "position_after_consequences", ""
        return None
    return None


def summarize_cover(rows, depths: list[int], fields: dict[int, str], preamble: list[str], found) -> dict:
    texts = [[cell_text(cell) for cell in row] for row in rows]
    out = {"clauses": None, "label_kind": None, "label_residue": None, "release_raw": None, "header_spec": None,
           "header_spec_raw": None, "header_spec_cell": None, "current_version": None,
           "other_specs": [], "tdocs_before_label": []}
    label_row = found[0] if found else None
    # 서식 전체를 담은 틀 표의 행(절 칸 행보다 얕은 행)은 절 칸 뒤의 글까지 담고 있어 머리·앞 글로 쓰지 않는다.
    level = depths[label_row] if found else 0
    head_rows = [i for i in range(label_row if found else 0) if depths[i] >= level]
    before = " ".join(preamble) + " " + " ".join(" ".join(texts[i]) for i in head_rows)
    out["tdocs_before_label"] = sorted({t.upper().replace("R5S", "R5s") for t in TDOC.findall(before)})
    if not found:
        return out
    _, at, kind, residue = found
    row = texts[label_row]
    start = 0 if kind == "position_after_consequences" else at + 1
    value = clean(" ; ".join(cell for cell in row[start:] if cell.strip()))
    # 칸 이름 뒤에 덧붙은 글은 값 칸이 비었을 때만 값으로 쓴다(값을 칸 이름 칸에 함께 적은 서식).
    out["clauses"] = value or residue
    out["label_kind"] = kind
    out["label_residue"] = residue or None
    for i in head_rows:
        row = texts[i]
        labels = [label(cell) for cell in row]
        for j, name in enumerate(labels):
            if name == "release" and out["release_raw"] is None:
                out["release_raw"] = clean(next((cell for cell in row[j + 1:] if cell.strip()), ""))
            if name == "cr" and out["header_spec"] is None:
                for k in range(j - 1, -1, -1):
                    if row[k].strip() and out["header_spec_raw"] is None:
                        out["header_spec_raw"] = clean(row[k])[:40]
                    spec = SPEC.search(row[k])
                    if spec:
                        out["header_spec"] = spec_text(spec)
                        out["header_spec_cell"] = fields.get(id(rows[i][k]), "typed")
                        break
            if name.startswith("current version") and out["current_version"] is None:
                out["current_version"] = clean(next((cell for cell in row[j + 1:] if cell.strip()), ""))
    other, inside = set(), False
    for row in texts[label_row + 1:]:
        labels = [label(cell) for cell in row]
        if any(name.startswith("other specs") for name in labels):
            inside = True
        elif any(name.startswith(("other comments", "this cr's revision", "this cr’s revision")) for name in labels):
            break
        if inside:
            other.update(spec_text(m) for cell in row for m in SPEC.finditer(cell))
    out["other_specs"] = sorted(other)
    return out


def release_of(raw: str | None) -> str | None:
    if not raw:
        return None
    found = re.search(r"rel(?:ease)?[\s\-_.]*(\d{1,2})\b", raw, re.I) or re.search(r"\bR(\d{2})\b", raw)
    return f"Rel-{int(found.group(1))}" if found else None


def read_form(path_text: str) -> dict:
    """서식 하나를 읽는다. 병렬 작업자가 부른다."""
    path = Path(path_text)
    try:
        digest = hashlib.sha1(path.read_bytes()).hexdigest()
        cover, status = read_xml(path)
    except (OSError, zipfile.BadZipFile, RuntimeError, ValueError, EOFError) as error:
        return {"path": path_text, "status": "read_error", "error": type(error).__name__}
    if status != "ok":
        return {"path": path_text, "status": status, "sha1": digest}
    if cover is None or cover["clauses"] is None:
        return {"path": path_text, "status": "cell_absent", "sha1": digest,
                **({"tdocs_before_label": cover["tdocs_before_label"]} if cover else {})}
    name_spec = FILE_SPEC.match(path.name)
    return {"path": path_text, "status": "ok", "sha1": digest, **cover,
            "release": release_of(cover["release_raw"]),
            "file_spec": spec_text(name_spec) if name_spec else None}


# ---------------------------------------------------------------- 절 판정


def components(clause: str) -> list[tuple]:
    """절 번호를 자리별 비교 키로 나눈다. 숫자 자리가 부록 글자 자리보다 앞선다."""
    base, _, variant = clause.partition("_")
    keys = []
    for part in base.split("."):
        digits = re.fullmatch(r"(\d+)([A-Za-z]?)", part)
        keys.append((0, int(digits.group(1)), digits.group(2).lower()) if digits else (1, 0, part.upper()))
    if variant:
        keys.append((2, int(variant), ""))
    return keys


def comparable(clause: str) -> bool:
    return bool(re.fullmatch(CLAUSE_TOKEN, clause))


def masked(cell: str) -> tuple[str, set[str], set[str]]:
    """규격·release·표 번호를 가린 칸 글과, 칸에 적힌 규격 번호 · 표·그림이 속한 절 번호."""
    specs = {spec_text(m) for m in SPEC.finditer(cell)}
    tables = {m.group(1).rstrip(".") for m in TABLE.finditer(cell)}
    text = TABLE.sub(" ; ", cell)
    # 칸에 적힌 규격 번호(`38.101-1` · `TS 38.331`)와 release·판 표기(`Rel-15` · `V15.2.0`)는 절 번호가 아니다.
    text = re.sub(r"\b(?:TS|TR)\s*\d{2}\.\d{3}(?:-\d+)?", " ; ", text)
    text = re.sub(r"(?<![\d.])\d{2}\.\d{3}-\d+\b|(?<![\d.])3[4-8]\.\d{3}(?![\d.])", " ; ", text)
    # 제목 낱말 `Release` 바로 뒤의 절 번호(`RRC Connection Release 5.3.10.`)는 release 표기가 아니므로 가리지 않는다.
    text = re.sub(r"\bRel(?:ease)?[\s\-]*\d+\b(?!\.\d)|\b[Vv]\d+\.\d+\.\d+\b", " ; ", text)
    # 범위 표기 가운데 끝이 앞보다 작은 `6.2.4-2` 는 표 번호다(`Table` 낱말을 빠뜨린 꼴).
    def table_like(match: re.Match) -> str:
        start, end = match.group(1), match.group(2)
        if re.fullmatch(r"\d+", end) and start.count(".") and int(end) <= components(start)[-1][1]:
            tables.add(start)
            return " ; "
        return match.group(0)
    text = re.sub(rf"(?<![0-9A-Za-z._])({CLAUSE_TOKEN})-(\d+)(?![0-9A-Za-z_.])", table_like, text)
    return text, specs, tables


def literal(text: str, clause: str, flags=0) -> bool:
    if re.search(r"[A-Za-z]{2}", clause):
        pattern = rf"(?<![0-9A-Za-z_\-]){re.escape(clause)}(?![0-9A-Za-z_\-])"
    else:
        pattern = rf"(?<![0-9A-Za-z._]){re.escape(clause)}(?![0-9A-Za-z_]|\.[0-9A-Za-z])"
    if re.fullmatch(r"[A-Z]", clause):
        # 부록 전체(`A`)는 영어 낱말 `A` 와 구별되지 않는다. `Annex`·`Section` 같은 말 뒤의 목록(`Annex A-C, F, G`)에
        # 들었거나, 칸의 목록 항목 하나가 그 글자뿐일 때(`F, G, H`)만 적힌 것으로 본다. 대소문자를 가린다.
        item = r"[A-Z](?:\s*-\s*[A-Z])?(?:\.[0-9A-Za-z.]*)?"
        after_word = rf"\b(?i:annex(?:es)?|appendix|appendices|sections?|clauses?)\s*(?:{item}\s*(?:,|;|&|\band\b)\s*)*{pattern}"
        alone = rf"(?:^|[,;&(>]|\band\b)\s*{re.escape(clause)}\s*(?=$|[,;&()]|\band\b|-\s*>)"
        return re.search(after_word, text) is not None or re.search(alone, text) is not None
    return re.search(pattern, text, flags) is not None


def typographic(text: str) -> str:
    """점 앞뒤 빈칸, 부록 글자 뒤 점 빠짐(`A1`)·점 대신 빈칸(`A 4.5.1`), 낱말에 붙은 번호(`clause5.1` · `Annex-H`)를
    고친 칸 글."""
    text = re.sub(r"(?i)\b((?:sub)?clauses?|sections?|annex(?:es)?)\s*-?\s*(?=[0-9A-Z])", r"\1 ", text)
    # 점 뒤 빈칸은 다음이 숫자나 홀로 선 대문자일 때만 붙인다. `5.3.5. RRC Connection` 의 제목 낱말은 붙이지 않는다.
    text = re.sub(r"(?<=[0-9A-Za-z])\s*\.\s+(?=\d|[A-Z](?![A-Za-z]))|(?<=[0-9A-Za-z])\s+\.\s*(?=[0-9])", ".", text)
    text = re.sub(r"(?<![0-9A-Za-z._])([A-Z])\s+(?=\d+\.\d)", r"\1.", text)
    return re.sub(r"(?<![0-9A-Za-z._])([A-Z])(\d+)", r"\1.\2", text)


def comma_joined(cell: str, clause: str) -> str | None:
    """확인 판정이 점을 쉼표로 잘못 친 번호(`6,2,3` = 6.2.3)에 기댔을 수 있는가.

    칸의 다른 자리는 쉼표 뒤에 빈칸을 두는데 이 절 번호가 빈칸 없는 쉼표로 이웃 번호와 이어져 있고, 이은 두 쪽
    가운데 하나가 숫자나 글자 하나뿐이면 `possible` 이다. 같은 사슬 안에서 뒤 번호가 앞 번호보다 작아 오름차순
    목록으로 읽히지 않으면(`8.3.4,2` · `7,6,2` · `B,2,15`) `probable` 이다. 둘 다 아니면 None.
    판정 자체는 쓰인 그대로(쉼표 = 목록 구분)이고, 이 값은 그 판정이 서식의 오기에 기댔을 수 있는 범위를 따로 센다.
    """
    text = masked(cell)[0]
    if not re.search(r",\s", text):
        return None
    verdict = None
    for m in re.finditer(r"(?<![0-9A-Za-z._])([0-9A-Z][0-9A-Za-z.]*(?:,[0-9A-Z][0-9A-Za-z.]*)+)(?![0-9A-Za-z_.])", text):
        parts = m.group(1).split(",")
        if clause not in parts:
            continue
        pairs = list(zip(parts, parts[1:]))
        fragment = any(re.fullmatch(r"\d+|[A-Z]", p) for p in parts)
        if not fragment:
            continue
        if any(comparable(a) and comparable(b) and components(b) < components(a) for a, b in pairs):
            return "probable"
        verdict = "possible"
    return verdict


def in_range(clause: str, start: str, end: str) -> bool:
    if not (comparable(clause) and comparable(start) and comparable(end)):
        return False
    c, s, e = components(clause), components(start), components(end)
    if len(e) == 1 and len(s) > 1 and e[0][0] == 0 and e[0][1] > s[-1][1]:
        e = s[:-1] + e
    if not s < e:
        return False
    return s <= c <= e or c[: len(e)] == e


def judge_clause(cell: str, clause: str, ie_clauses: set[str]) -> str:
    if not cell.strip():
        return "cell_empty"
    text, _, tables = masked(cell)
    if literal(text, clause):
        return "literal"
    loose = typographic(text)
    if literal(loose, clause) or literal(loose, clause, re.I):
        return "typographic"
    # 점 뒤 빈칸을 붙인 글에서는 `e.g. 7.1/2` 가 `e.g.7.1/2` 로 앞 낱말에 붙어 아래 꼴을 못 찾으므로 두 글을 다 본다.
    forms = (text, loose)
    for m in (m for form in forms for m in SLASH.finditer(form)):
        head = m.group(1)
        stem = head.rsplit(".", 1)[0] if "." in head else None
        if stem and clause in {f"{stem}.{n.strip()}" for n in m.group(2).split("/") if n.strip()}:
            return "abbreviated_sibling"
    for m in (m for form in forms for m in RANGE.finditer(form)):
        if in_range(clause, m.group(1), m.group(2)):
            return "range_interior"
    # 시험 규격의 변형 꼬리표: `8.1.1.2.4.NR5GC` 는 절 8.1.1.2.4 의 시험 항목을 NR5GC 변형으로 고친다는 뜻이다.
    # 꼬리는 글자로 시작하는 두 자 이상(`NR5GC` · `N5GC` · `ENDC`)이다. 절 번호 뒤 자리에 오는 부록 글자는 맨 앞에만
    # 오고, 숫자 자리 꼬리(`.1a`)는 숫자로 시작하므로 절 번호 자리와 겹치지 않는다.
    if comparable(clause) and any(re.search(
            rf"(?<![0-9A-Za-z._]){re.escape(clause)}\.[A-Za-z][0-9A-Za-z]+(?![0-9A-Za-z_]|\.[0-9A-Za-z])", form)
            for form in forms):
        return "variant_suffix"
    listed = {m.group(0) for m in TOKEN.finditer(loose)}
    if ie_clauses and listed & ie_clauses:
        return "asn1_ie_clause_listed"
    if clause in tables:
        return "table_or_figure_in_clause"
    if any(clause.startswith(t + ".") or clause.startswith(t + "_") for t in listed if t):
        return "descendant_of_listed"
    if any(t.startswith(clause + ".") or t.startswith(clause + "_") for t in listed | tables):
        return "ancestor_of_listed"
    if WHOLE.search(cell):
        return "whole_spec_wording"
    if PLACEHOLDER.fullmatch(cell) or re.search(r"\b[xX](?:\.[xXyYzZ0-9])+\b|\bTBD\b", cell):
        return "placeholder"
    return "not_listed"


def judge(form: dict, spec: str, clause: str, ie_clauses: set[str]) -> tuple[str, str | None]:
    """(갈래, 서식 규격을 읽은 곳)."""
    form_spec, where = (form["header_spec"], "header") if form["header_spec"] else (form["file_spec"], "file_name")
    if form_spec is None:
        return "spec_unread", None
    if form_spec != spec and form["header_spec"] and form["file_spec"] == spec:
        # 서식 머리의 규격 칸만 다르고 파일 이름(`38213_CR0035_…`)의 규격은 절 기록과 같다. 머리 칸의 오기로 따로 센다.
        listed = judge_clause(form["clauses"], clause, ie_clauses) in CONFIRMED
        return ("header_spec_typo_clause_listed" if listed else "header_spec_typo_clause_not_listed"), where
    if form_spec != spec:
        named = spec in form["other_specs"] or spec in masked(form["clauses"])[1]
        return ("spec_differs_section_spec_named_on_form" if named else "spec_differs_section_spec_not_named"), where
    return judge_clause(form["clauses"], clause, ie_clauses), where


# ---------------------------------------------------------------- 입력


def load_links(wg: str) -> dict:
    root = RAN5_EXPORT if wg == "RAN5" else PHASE4 / wg
    records = graph(root / "cr_extensions.jsonld")
    links = [(r["@id"].removeprefix("tdoc:"), s) for r in records for s in as_list(r.get("modifiesSection"))]
    reverse = {(as_list_value.removeprefix("tdoc:"), r["@id"]) for r in graph(root / "section_extensions.jsonld")
               for as_list_value in as_list(r.get("modifiedByCR"))}
    forward = set(links)
    pack = {r["@id"].removeprefix("tdoc:"): r["belongsToCRPack"].rsplit("/", 1)[-1]
            for r in records if r.get("belongsToCRPack")}
    return {"source": str(root), "records": len(records), "links": links, "pack": pack,
            "directionAgreement": {"onlyInModifiesSection": len(forward - reverse),
                                   "onlyInModifiedByCR": len(reverse - forward)}}


def index_corpus() -> dict[str, list[tuple[Path, int]]]:
    """파일 이름의 기고 번호 → (경로, 그 번호가 이름의 몇째 번호인가)."""
    found: dict[str, list[tuple[Path, int]]] = collections.defaultdict(list)
    for wg in WGS:
        for path in sorted((CR_CORPUS / wg / "derived").rglob("*")):
            if path.suffix.lower() not in (".docx", ".doc") or not path.is_file():
                continue
            seen: list[str] = []
            for token in TDOC.findall(path.name):
                token = token.upper().replace("R5S", "R5s")
                if token not in seen:
                    seen.append(token)
            for position, token in enumerate(seen):
                found[token].append((path, position))
    return found


def build_parse(wg: str) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """빌드가 기록한 CR 별 원본 경로와 release. 판정에는 쓰지 않는다. 경로는 서식을 못 찾았을 때 대신 읽고,
    release 는 판이 다른 연결이 어디서 왔는지 볼 때만 쓴다."""
    data = json.loads((PARSED_CR / wg / "cr_documents.json").read_text())
    paths: dict[str, set[str]] = collections.defaultdict(set)
    releases_read: dict[str, set[str]] = collections.defaultdict(set)
    for form in data.get("cr_documents") or data.get("documents") or []:
        if form.get("source_path"):
            paths[form["tdoc_number"]].add(form["source_path"])
        if form.get("release"):
            releases_read[form["tdoc_number"]].add(str(form["release"]))
    return paths, releases_read


def release_number(name: str | None) -> int:
    match = RELEASE_NUMBER.search(name or "")
    return int(match.group(1)) if match else -1


def load_structure(wg: str) -> dict:
    """Phase-4 빌더가 쓰는 절 기록 전체.

    `shape`: 절 기록 id → (isVoid, 하위 절이 있는가). `keys`: 판 해소에 쓰는 (규격, 판, 절 번호).
    `releases`: 규격 → 판 목록(최신 먼저). 판 해소 열쇠는 빌더처럼 id 가 `-{절 번호}` 로 끝나고 `-Rel-` 를 담은 기록만 만든다.
    """
    if wg in STRUCTURE_FILE:
        source = str(STRUCTURE_FILE[wg])
        rows = [(r.get("sectionId"), r.get("sectionNumber"), r.get("isVoid"), bool(as_list(r.get("hasSubSection"))), True)
                for r in graph(STRUCTURE_FILE[wg])]
    else:
        source = f"neo4j http:{STRUCTURE_NEO4J[wg]}"
        rows = neo4j_rows(STRUCTURE_NEO4J[wg],
                          "MATCH (s:Section) RETURN s.sectionId, s.sectionNumber, s.isVoid, "
                          "COUNT { (s)-[:HAS_SUB_SECTION]->(:Section) } > 0, COUNT { (s)-[:BELONGS_TO_SPEC]->(:Spec) } > 0")
    shape: dict[str, tuple[bool, bool]] = {}
    keys: set[tuple[str, str, str]] = set()
    editions: dict[str, set[str]] = collections.defaultdict(set)
    tally = collections.Counter()
    for section_id, number, void, parent, in_spec in rows:
        if not section_id:
            tally["recordsWithoutSectionId"] += 1
            continue
        section_id = str(section_id).removeprefix("tdoc:section/")
        tally[f"isVoidValue_{void!r}"] += 1
        shape["tdoc:section/" + section_id] = (void is True, bool(parent))
        number = str(number)
        stem = section_id[: -(len(number) + 1)] if section_id.endswith("-" + number) else ""
        if not in_spec:
            tally["recordsWithoutBelongsToSpec"] += 1
        elif "-Rel-" not in stem:
            tally["recordsOutsideResolverKey"] += 1
        else:
            spec, tail = stem.rsplit("-Rel-", 1)
            keys.add((spec, f"Rel-{tail}", number))
            editions[spec].add(f"Rel-{tail}")
    return {"source": source, "records": len(rows), "tally": dict(tally), "shape": shape, "keys": keys,
            "releases": {spec: sorted(names, key=release_number, reverse=True) for spec, names in editions.items()}}


def resolve(structure: dict, spec: str, clause: str, target: str | None) -> tuple[str | None, str]:
    """빌드의 판 해소 규칙(`SectionIndex.resolve`)을 다시 적용한다. (고른 판, 방법)."""
    editions = structure["releases"].get(spec)
    if not editions:
        return None, "drop_no_spec"
    if target is None or release_number(target) < 0:
        target, method = editions[0], "latest"
    else:
        method = "exact"
    if (spec, target, clause) in structure["keys"]:
        return target, method
    for name in editions:
        if release_number(name) <= release_number(target) and (spec, name, clause) in structure["keys"]:
            return name, "fallback_le"
    for name in editions:
        if (spec, name, clause) in structure["keys"]:
            return name, "fallback_fwd"
    return None, "drop_no_section"


# ---------------------------------------------------------------- Qdrant


def qdrant(method: str, path: str, body: dict | None = None) -> dict:
    request = urllib.request.Request(QDRANT + path, method=method, headers={"Content-Type": "application/json"},
                                     data=json.dumps(body).encode() if body is not None else None)
    with urllib.request.urlopen(request) as response:
        return json.load(response)["result"]


def scroll(collection: str):
    offset = None
    while True:
        body = {"limit": 512, "with_vector": False, "with_payload": [
            "specNumber", "sectionNumber", "specReleases", "text", "content", "asn1", "tsSectionNumber", "chunkId"]}
        if offset is not None:
            body["offset"] = offset
        result = qdrant("POST", f"/collections/{collection}/points/scroll", body)
        yield from result["points"]
        offset = result.get("next_page_offset")
        if offset is None:
            return


def releases(value) -> list[str]:
    if isinstance(value, str):
        try:
            value = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            value = [value]
    return [str(v) for v in as_list(value)]


def load_bodies() -> dict:
    """작업반별 (규격, 절 번호) → 본문이 있는 판 집합. 판이 없는 조각은 `None` 으로 넣는다."""
    names = sorted(c["name"] for c in qdrant("GET", "/collections")["collections"])
    out = {"collections": {}, "held": {}, "asn1": {}, "asn1_clauses": {}}
    for wg in WGS:
        prefix = wg.lower()
        held: dict[tuple[str, str], set] = collections.defaultdict(set)
        asn1: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
        overlap = {}
        for name in (f"{prefix}_ts_sections", f"{prefix}_ts_sections_p12", f"{prefix}_ts_asn1_chunks"):
            if name not in names:
                continue
            stats = collections.Counter()
            keys = set()
            for point in scroll(name):
                payload = point["payload"]
                stats["points"] += 1
                body = payload.get("text") or payload.get("content") or ""
                field = "text" if payload.get("text") else "content" if payload.get("content") else "none"
                stats[f"bodyField_{field}"] += 1
                if not str(body).strip():
                    stats["emptyBody"] += 1
                    continue
                spec, number = str(payload.get("specNumber") or ""), str(payload.get("sectionNumber") or "")
                if name.endswith("asn1_chunks"):
                    ie = (payload.get("asn1") or {}).get("ieName")
                    if ie:
                        asn1[(spec, ie)].add(str(payload.get("tsSectionNumber") or ""))
                    continue
                listed = releases(payload.get("specReleases"))
                stats["withSpecReleases" if listed else "withoutSpecReleases"] += 1
                held[(spec, number)].update(listed or [None])
                keys.add((spec, number))
            if name.endswith("_p12"):
                main_keys = {k for k, v in held.items() if v - {None}}
                overlap = {"p12SectionKeys": len(keys), "p12SectionKeysAlsoInMain": len(keys & main_keys)}
            out["collections"][name] = dict(stats)
        if overlap:
            out["collections"][f"{prefix}_ts_sections_p12"].update(overlap)
        out["held"][wg] = held
        out["asn1"][wg] = asn1
    return out


def field_profile(records: list[dict]) -> dict:
    """필드 이름 → (그 필드를 가진 기록 수, 글 값의 최대 길이). 본문 필드가 있는지 보는 근거다."""
    keys: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0])
    for record in records:
        for key, value in record.items():
            keys[key][0] += 1
            if isinstance(value, str):
                keys[key][1] = max(keys[key][1], len(value))
    return {k: {"records": n, "maxStringLength": m} for k, (n, m) in sorted(keys.items())}


def phase3_evidence() -> dict:
    out = {}
    for wg in WGS:
        root = PHASE3 / wg
        if not root.is_dir():
            out[wg] = {"note": f"{root} 디렉터리가 없다"}
            continue
        out[wg] = {str(path): {"records": len(records), "fields": field_profile(records)}
                   for path in sorted(root.rglob("*section*.jsonld")) for records in [graph(path)]}
    return out


def neo4j_rows(port: int, cypher: str) -> list[list]:
    """읽기 전용 질의 하나를 HTTP 로 보내 행 목록을 받는다."""
    if "scripts/common" not in sys.path:
        sys.path.insert(0, "scripts/common")
    from common.credentials import neo4j_http_authorization

    request = urllib.request.Request(
        f"http://localhost:{port}/db/neo4j/tx/commit", method="POST",
        headers={"Content-Type": "application/json", "Authorization": neo4j_http_authorization()},
        data=json.dumps({"statements": [{"statement": cypher}]}).encode())
    with urllib.request.urlopen(request, timeout=NEO4J_TIMEOUT_S) as response:
        result = json.load(response)
    if result.get("errors"):
        raise RuntimeError(result["errors"][0].get("code"))
    return [row["row"] for row in result["results"][0]["data"]]


def neo4j_evidence() -> dict:
    """Section 노드의 속성 이름별 노드 수와 글 값 최대 길이(읽기 전용 질의)."""
    cypher = ("MATCH (s:Section) UNWIND keys(s) AS k WITH k, s[k] AS v "
              "RETURN k, count(*) AS n, max(CASE WHEN v IS :: STRING THEN size(v) END) AS maxLen ORDER BY k")
    out = {}
    for wg, port in NEO4J_HTTP.items():
        try:
            rows = neo4j_rows(port, cypher)
        except (OSError, ValueError, RuntimeError) as error:
            out[wg] = {"error": str(error) if isinstance(error, RuntimeError) else type(error).__name__}
            continue
        out[wg] = {name: {"nodes": nodes, "maxStringLength": longest} for name, nodes, longest in rows}
    return out


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------- 집계


def release_key(name: str):
    return (not name.startswith("Rel-"), int(name[4:]) if name[4:].isdigit() else 0, name)


def share(part: int, whole: int) -> float | None:
    return round(part / whole, 4) if whole else None


def audit_wg(wg: str, data: dict, forms_by_cr: dict, bodies: dict | None, examples: int, unconfirmed: list,
             structure: dict, build_release: dict[str, set[str]]) -> dict:
    # ASN.1 이름 절(`RadioBearerConfig`)은 IE 이름이 절 번호 자리에 든 절 기록이다. (규격, IE 이름) → 그 IE 를 담은 TS 절 번호.
    ie_clauses_of = collections.defaultdict(set)
    for asn1 in (bodies["asn1"].values() if bodies else ()):
        for (spec, ie), numbers in asn1.items():
            ie_clauses_of[(spec, ie)].update(n for n in numbers if n)
    outcome = collections.Counter()
    by_class_examples: dict[str, list] = collections.defaultdict(list)
    located = collections.Counter()
    release_split = collections.Counter()
    spec_where = collections.Counter()
    disagree = 0
    disagree_examples = []
    single_letter_or_number = collections.Counter()
    label_kind = collections.Counter()
    header_cell = collections.defaultdict(collections.Counter)
    comma_flag = collections.Counter()
    comma_links: list[dict] = []
    edition_rule = collections.Counter()
    edition_rule_other: list[dict] = []
    for cr, section_id in data["links"]:
        parsed = SECTION.match(section_id)
        spec, release, clause = parsed["spec"], parsed["release"], parsed["clause"]
        entry = forms_by_cr.get(cr, {"locator": "none", "copies": [], "unreadable": []})
        located[entry["locator"]] += 1
        readable = [f for f in entry["copies"] if f["status"] == "ok"]
        if not entry["copies"] and not entry["unreadable"]:
            verdicts = [("form_not_found", None, None)]
        elif not entry["copies"]:
            verdicts = [("form_unreadable", None, None)]
        elif not readable:
            verdicts = [("cell_absent", None, None)]
        else:
            ie = ie_clauses_of.get((spec, clause), set()) if re.search(r"[A-Za-z]{2}", clause) else set()
            verdicts = [(*judge(form, spec, clause, ie), form) for form in readable]
        verdicts.sort(key=lambda v: PRIORITY.index(v[0]))
        best, where, form = verdicts[0]
        if len({v[0] in CONFIRMED for v in verdicts}) > 1:
            disagree += 1
            if len(disagree_examples) < examples:
                disagree_examples.append({"cr": cr, "section": section_id,
                                          "copies": [{"class": v[0], "path": v[2]["path"], "clauses": v[2]["clauses"]}
                                                     for v in verdicts]})
        outcome[best] += 1
        if where:
            spec_where[where] += 1
        if form:
            label_kind[form["label_kind"]] += 1
        if best.startswith(("header_spec_typo", "spec_differs", "spec_unread")) and form:
            header_cell[best][form.get("header_spec_cell") or "no_spec_in_header"] += 1
        if best in CONFIRMED:
            form_release = form.get("release")
            split = ("form_release_unread" if form_release is None
                     else "same_release" if form_release == release else "other_release")
            release_split[split] += 1
            if split != "same_release":
                chosen, method = resolve(structure, spec, clause, form_release)
                edition_rule[f"{split}:{method}:{'link_edition' if chosen == release else 'other_edition'}"] += 1
                if chosen != release:
                    # 빌드가 파싱한 release 로 같은 규칙을 적용하면 연결의 판이 나오는지 본다.
                    parsed = sorted(build_release.get(cr, ()))
                    by_parsed = sorted({resolve(structure, spec, clause, r)[0] for r in parsed} - {None})
                    edition_rule["differs:linkEditionFromBuildParsedRelease" if release in by_parsed
                                 else "differs:notFromBuildParsedRelease"] += 1
                    edition_rule_other.append({"cr": cr, "section": section_id, "formRelease": form.get("release_raw"),
                                               "ruleEdition": chosen, "method": method,
                                               "buildParsedRelease": parsed, "ruleEditionFromBuildParsed": by_parsed,
                                               "formPath": form["path"]})
            if re.fullmatch(r"[A-Z]|\d+", clause):
                single_letter_or_number[clause] += 1
            joined = comma_joined(form["clauses"], clause)
            if joined:
                comma_flag[joined] += 1
                comma_links.append({"cr": cr, "section": section_id, "flag": joined, "class": best,
                                    "formPath": form["path"], "clauses": form["clauses"][:600]})
        record = {"cr": cr, "section": section_id, "class": best, "locator": entry["locator"],
                  **({"formPath": form["path"], "formSpec": form["header_spec"] or form["file_spec"],
                      "headerSpecRaw": form["header_spec_raw"], "headerSpecCell": form["header_spec_cell"],
                      "fileNameSpec": form["file_spec"], "labelKind": form["label_kind"],
                      "formRelease": form.get("release_raw"), "clauses": form["clauses"][:600],
                      "otherSpecs": form["other_specs"]} if form else
                     {"paths": [f["path"] for f in entry["copies"] + entry["unreadable"]][:4],
                      "statuses": [f["status"] for f in entry["copies"] + entry["unreadable"]][:4]})}
        if best not in CONFIRMED:
            unconfirmed.append({"wg": wg, **record})
            if len(by_class_examples[best]) < examples:
                by_class_examples[best].append(record)
    total = len(data["links"])
    confirmed = sum(outcome[c] for c in CONFIRMED)
    return {
        "links": total,
        "distinctCr": len({cr for cr, _ in data["links"]}),
        "distinctSections": len({s for _, s in data["links"]}),
        "confirmed": confirmed,
        "confirmedShare": share(confirmed, total),
        "confirmedBy": {c: outcome[c] for c in CONFIRMED},
        "notConfirmed": {c: outcome[c] for c in PRIORITY if c not in CONFIRMED + UNAVAILABLE and outcome[c]},
        "notConfirmedTotal": sum(outcome[c] for c in PRIORITY if c not in CONFIRMED + UNAVAILABLE),
        "formUnavailable": {c: outcome[c] for c in UNAVAILABLE},
        "formUnavailableTotal": sum(outcome[c] for c in UNAVAILABLE),
        "headerSpecCellKind": {c: dict(v) for c, v in sorted(header_cell.items())},
        "labelKind": dict(label_kind),
        "confirmedReleaseSplit": dict(release_split),
        "confirmedEditionRule": {"tally": dict(sorted(edition_rule.items())), "otherEditionLinks": edition_rule_other},
        "confirmedSingleTokenClauses": dict(single_letter_or_number.most_common()),
        "confirmedOnCommaJoinedNumber": {"possible": comma_flag["possible"], "probable": comma_flag["probable"],
                                         "links": comma_links},
        "formSpecReadFrom": dict(spec_where),
        "locator": dict(located),
        "linksWhereCopiesDisagree": disagree,
        "disagreementExamples": disagree_examples,
        "examples": dict(by_class_examples),
    }


def dotted_prefixes(number: str) -> list[str]:
    """`A.7.6` → [`A`, `A.7`, `A.7.6`]. 하위 절 번호가 `절 번호.` 로 시작하는지를 모음 조회로 바꾸려고 쓴다."""
    parts = number.split(".")
    return [".".join(parts[: i + 1]) for i in range(len(parts))]


def coverage_wg(wg: str, data: dict, bodies: dict, forms_by_cr: dict, structure: dict, examples: int) -> dict:
    held = bodies["held"][wg]
    asn1 = bodies["asn1"].get(wg, {})
    other_wgs = [w for w in WGS if w != wg]
    # (규격, 판) → 그 판에 본문 조각이 있는 절과 그 모든 상위 절. 대상 절이 여기 있으면 자신이나 하위 절이 본문을 가진다.
    subtree_held: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    for (spec, number), found in held.items():
        for name in found - {None}:
            subtree_held[(spec, name)].update(dotted_prefixes(number))
    # 규격 → ASN.1 조각이 담긴 TS 절 번호와 그 상위 절.
    asn1_at_or_below: dict[str, set[str]] = collections.defaultdict(set)
    for (spec, _ie), numbers in asn1.items():
        for number in numbers - {""}:
            asn1_at_or_below[spec].update(dotted_prefixes(number))
    shape_of = structure["shape"]

    def status(section_id: str) -> tuple[bool, bool, bool, bool]:
        parsed = SECTION.match(section_id)
        key = (parsed["spec"], parsed["clause"])
        found = held.get(key, set())
        same = parsed["release"] in found
        anyrel = bool(found) or (parsed["spec"], parsed["clause"]) in asn1
        elsewhere = not anyrel and any(key in bodies["held"][w] for w in other_wgs)
        subtree = same or parsed["clause"] in subtree_held.get((parsed["spec"], parsed["release"]), ())
        return same, anyrel, elsewhere, subtree

    def shape(section_id: str) -> str:
        if section_id not in shape_of:
            return "not_in_structure_source"
        void, parent = shape_of[section_id]
        return "void" if void else "has_subsections" if parent else "leaf"

    sections = sorted({s for _, s in data["links"]})
    state = {s: status(s) for s in sections}
    per_release = collections.defaultdict(collections.Counter)
    by_shape = collections.defaultdict(collections.Counter)
    edition_without_chunk = 0
    not_held_groups = collections.Counter()
    not_held_asn1 = 0
    for s in sections:
        parsed = SECTION.match(s)
        rel = parsed["release"]
        same, anyrel, elsewhere, subtree = state[s]
        per_release[rel]["targetSections"] += 1
        per_release[rel]["heldSameRelease"] += same
        per_release[rel]["heldSameReleaseInclSubclauses"] += subtree
        per_release[rel]["heldAnyRelease"] += anyrel
        per_release[rel]["heldOnlyInAnotherWgCollection"] += elsewhere
        cell = by_shape[shape(s)]
        cell["targetSections"] += 1
        cell["heldSameRelease"] += same
        cell["heldSameReleaseInclSubclauses"] += subtree
        if not same and (parsed["spec"], rel) not in subtree_held:
            edition_without_chunk += 1
        if not subtree:
            asn1_here = parsed["clause"] in asn1_at_or_below.get(parsed["spec"], ())
            not_held_asn1 += asn1_here
            group = f'{parsed["spec"]} {".".join(parsed["clause"].split(".")[:2])}'
            not_held_groups[group + (" (asn1 chunk at or below)" if asn1_here else "")] += 1
    # 대상 절 기록이 Void 인 연결. 같은 규격·같은 절 번호의 Void 가 아닌 절 기록이 다른 판에 있는지 함께 본다.
    nonvoid_editions: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    for section_id, (void, _parent) in shape_of.items():
        parsed = SECTION.match(section_id)
        if parsed and not void:
            nonvoid_editions[(parsed["spec"], parsed["clause"])].add(parsed["release"])
    void_tally = collections.Counter()
    void_examples: dict[str, list] = collections.defaultdict(list)
    for cr, s in data["links"]:
        if shape(s) != "void":
            continue
        parsed = SECTION.match(s)
        others = sorted(nonvoid_editions.get((parsed["spec"], parsed["clause"]), ()), key=release_key)
        kind = "nonVoidRecordInOtherEdition" if others else "voidInEveryEditionHeld"
        void_tally[kind] += 1
        if len(void_examples[kind]) < examples:
            void_examples[kind].append({"cr": cr, "section": s, "nonVoidEditions": others})
    targets = collections.defaultdict(list)
    for cr, s in data["links"]:
        targets[cr].append(s)
    cr_release = {}
    for cr in data["pack"]:
        copies = [f for f in forms_by_cr.get(cr, {}).get("copies", []) if f["status"] == "ok" and f.get("release")]
        cr_release[cr] = copies[0]["release"] if copies else "release_not_read"
    cr_cells = collections.defaultdict(collections.Counter)
    for cr in data["pack"]:
        for group in ("all", cr_release[cr]):
            cell = cr_cells[group]
            cell["packCr"] += 1
            if cr in targets:
                cell["packCrWithLinks"] += 1
                cell["everyLinkedClauseHeldSameRelease"] += all(state[s][0] for s in targets[cr])
                cell["everyLinkedClauseHeldSameReleaseInclSubclauses"] += all(state[s][3] for s in targets[cr])
                cell["everyLinkedClauseHeldAnyRelease"] += all(state[s][1] for s in targets[cr])
    for cell in cr_cells.values():
        for name in ("everyLinkedClauseHeldSameRelease", "everyLinkedClauseHeldSameReleaseInclSubclauses",
                     "everyLinkedClauseHeldAnyRelease"):
            cell[f"{name}ShareOfPackCr"] = share(cell[name], cell["packCr"])
            cell[f"{name}ShareOfPackCrWithLinks"] = share(cell[name], cell["packCrWithLinks"])
    total = sum(per_release.values(), collections.Counter())
    return {
        "targetSections": len(sections),
        "heldSameRelease": total["heldSameRelease"],
        "heldSameReleaseShare": share(total["heldSameRelease"], len(sections)),
        "heldSameReleaseInclSubclauses": total["heldSameReleaseInclSubclauses"],
        "heldSameReleaseInclSubclausesShare": share(total["heldSameReleaseInclSubclauses"], len(sections)),
        "heldAnyRelease": total["heldAnyRelease"],
        "heldAnyReleaseShare": share(total["heldAnyRelease"], len(sections)),
        "heldOnlyInAnotherWgCollection": total["heldOnlyInAnotherWgCollection"],
        "byShape": {k: {**dict(v), "heldSameReleaseShare": share(v["heldSameRelease"], v["targetSections"]),
                        "heldSameReleaseInclSubclausesShare": share(v["heldSameReleaseInclSubclauses"], v["targetSections"])}
                    for k, v in sorted(by_shape.items())},
        "notHeldSameReleaseEditionWithoutAnyChunk": edition_without_chunk,
        "notHeldInclSubclauses": {"targetSections": len(sections) - total["heldSameReleaseInclSubclauses"],
                                  "asn1ChunkAtOrBelow": not_held_asn1,
                                  "bySpecAndTwoLeadingNumbers": dict(not_held_groups.most_common())},
        "linksToVoidRecord": {"links": sum(void_tally.values()), **dict(void_tally),
                              "examples": dict(void_examples)},
        "byRelease": {r: dict(per_release[r]) for r in sorted(per_release, key=release_key)},
        "packCr": {g: dict(cr_cells[g]) for g in sorted(cr_cells, key=lambda g: (g != "all", release_key(g)))},
        "linksNotInPack": sum(cr not in data["pack"] for cr, _ in data["links"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--wg", nargs="+", default=list(WGS))
    # 기본값은 논리 CPU 의 절반이다. 함께 도는 다른 작업이 나머지 절반을 쓴다.
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    # 갈래마다 보관할 예시 수. 사람이 직접 읽고 고를 만큼(갈래당 2~3건 보고)에 여유를 둔 값이다.
    parser.add_argument("--examples", type=int, default=10)
    parser.add_argument("--no-qdrant", action="store_true", help="본문 보유를 세지 않는다")
    parser.add_argument("--unconfirmed-jsonl", type=Path, help="미확인 연결 전부를 한 줄씩 쓴다")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    memory = {"start": memory_guard("시작")}

    loaded = {wg: load_links(wg) for wg in args.wg}
    structures = {wg: load_structure(wg) for wg in args.wg}
    memory["afterStructure"] = memory_guard("절 기록 읽기 뒤")
    corpus = index_corpus()
    build = {wg: build_parse(wg) for wg in args.wg}
    fallback = {wg: build[wg][0] for wg in args.wg}
    # CR → [(경로, 파일 이름에서 이 번호의 차례, 묶음 디렉터리 안인가)] 와 빌드 원본 경로.
    wanted_by_cr: dict[str, dict] = {}
    for wg in args.wg:
        crs = set(loaded[wg]["pack"]) | {cr for cr, _ in loaded[wg]["links"]}
        for cr in crs:
            pack = loaded[wg]["pack"].get(cr)
            wanted_by_cr[cr] = {"indexed": [(str(p), pos, bool(pack and pack in p.parts)) for p, pos in corpus.get(cr, [])],
                                "build": sorted(fallback[wg].get(cr, ()))}
    paths = sorted({p for entry in wanted_by_cr.values() for p in [x[0] for x in entry["indexed"]] + entry["build"]})
    memory["beforeForms"] = memory_guard("서식 읽기 전")
    with concurrent.futures.ProcessPoolExecutor(args.workers) as pool:
        read = {r["path"]: r for r in pool.map(read_form, paths, chunksize=64)}
    memory["afterForms"] = memory_guard("서식 읽기 뒤")
    read_status = collections.Counter(r["status"] for r in read.values())
    # 서식 머리의 규격과 파일 이름 앞머리의 규격이 얼마나 일치하는가(머리 칸 오기 판정의 바탕).
    header_vs_file = collections.Counter(
        "header_unread" if not r.get("header_spec") else "file_name_without_spec" if not r.get("file_spec")
        else "agree" if r["header_spec"] == r["file_spec"] else "differ" for r in read.values() if r["status"] == "ok")
    label_kinds = collections.Counter(r.get("label_kind") for r in read.values() if r["status"] == "ok")
    # 본문 부분이 없는 파일(`.doc` 이름의 zip 등)마다 같은 이름의 `.docx` 가 있고 읽혔는지 본다.
    no_part = collections.Counter()
    for path_text, r in read.items():
        if r["status"] in ("no_document_part", "binary_doc", "not_zip"):
            sibling = read.get(str(Path(path_text).with_suffix(".docx")))
            no_part[(Path(path_text).suffix.lower(), r["status"],
                     "docx_sibling_read_ok" if sibling and sibling["status"] == "ok"
                     else "docx_sibling_other_status" if sibling else "no_docx_sibling_read")] += 1

    forms_by_cr: dict[str, dict] = {}
    identity = collections.Counter()
    unreadable_status = ("binary_doc", "not_zip", "no_document_part", "read_error")
    for cr, entry in wanted_by_cr.items():
        copies, unreadable, seen_hash, in_pack = [], [], set(), False
        for path, position, pack_dir in entry["indexed"]:
            form = read[path]
            if form["status"] in unreadable_status:
                # 읽을 수 없는 사본은 이 CR 의 서식인지 가릴 수 없다. 파일 이름의 첫 번호일 때만 이 CR 의 것으로 센다.
                if position == 0:
                    unreadable.append(form)
                continue
            if cr in form.get("tdocs_before_label", []):
                identity["cr_number_in_form_text"] += 1
            elif position == 0:
                identity["first_number_in_file_name"] += 1
            else:
                identity["rejected_not_this_cr"] += 1
                continue
            if form.get("sha1") in seen_hash:
                identity["duplicate_bytes"] += 1
                continue
            seen_hash.add(form.get("sha1"))
            copies.append(form)
            in_pack |= pack_dir
        locator = ("pack_directory" if in_pack else "other_directory") if copies else None
        if not copies:
            # 색인에서 이 CR 의 서식을 못 찾았을 때만 빌드가 기록한 원본 경로를 읽는다.
            for path in entry["build"]:
                form = read[path]
                if form["status"] in unreadable_status:
                    unreadable.append(form)
                elif form.get("sha1") not in seen_hash:
                    seen_hash.add(form.get("sha1"))
                    copies.append(form)
                    identity["build_source_path"] += 1
            locator = "build_source_path" if copies else "unreadable_only" if unreadable else "none"
        forms_by_cr[cr] = {"locator": locator, "copies": copies, "unreadable": unreadable}

    bodies = None if args.no_qdrant else load_bodies()
    memory["afterQdrant"] = memory_guard("Qdrant 읽기 뒤")
    location = None if args.no_qdrant else {"phase3": phase3_evidence(), "neo4jSectionProperties": neo4j_evidence()}
    unconfirmed: list[dict] = []
    report = {
        "unit": {
            "links": "Phase-4 `modifiesSection` 의 (CR, 절 기록) 쌍. 같은 쌍은 한 번 센다",
            "confirmed": "서식 규격이 절 기록의 규격과 같고 절 번호가 `Clauses affected` 칸에 literal·typographic·"
                         "abbreviated_sibling·range_interior·variant_suffix 로 적힌 연결",
            "confirmedOnCommaJoinedNumber": "확인된 연결 가운데 절 번호가 빈칸 없는 쉼표로 이웃 번호와 이어진 연결. "
                                           "possible = 칸의 다른 자리는 쉼표 뒤에 빈칸을 두고 이은 쪽 하나가 숫자나 글자 하나뿐, "
                                           "probable = 그 사슬이 오름차순이 아니다(점을 쉼표로 친 오기로 읽힌다). 확인 수에는 그대로 들어 있다",
            "notConfirmed": "서식의 절 칸을 읽었으나 위 조건을 못 채운 연결의 갈래별 수. formUnavailable 은 넣지 않는다",
            "formUnavailable": "서식이 없거나(form_not_found) 읽을 수 없거나(form_unreadable) 절 칸이 없는(cell_absent) 연결",
            "links = confirmed + notConfirmedTotal + formUnavailableTotal": "세 묶음은 겹치지 않는다",
            "headerSpecCellKind": "규격 갈래 연결의 서식 머리 규격 칸이 문서 속성 필드(docproperty:Spec#)인지 손으로 친 글(typed)인지",
            "labelKind": "판정에 쓴 사본의 절 칸 이름 꼴(label · label_missing_initial · label_with_residue · "
                         "position_after_consequences)",
            "confirmedReleaseSplit": "확인된 연결 가운데 절 기록의 판이 서식 Release 칸과 같은지",
            "confirmedEditionRule": "판이 다르거나(other_release) 서식 Release 를 못 읽은(form_release_unread) 확인된 연결에 빌드의 "
                                    "판 해소 규칙을 서식 Release 를 목표로 다시 적용한 결과. `갈래:방법:판` 의 판이 link_edition 이면 "
                                    "규칙이 연결의 판을 고른다. differs:* 는 other_edition 연결을 빌드가 파싱한 release 로 다시 적용해 "
                                    "연결의 판이 나오는지(linkEditionFromBuildParsedRelease) 나눈 수다",
            "targetSections": "연결 대상인 서로 다른 절 기록(규격·판·절 번호)",
            "heldSameRelease": "본문이 빈 글이 아닌 Qdrant TS 절 조각 가운데 규격·절 번호가 같고 specReleases 에 그 판이 든 조각이 있는 절",
            "heldSameReleaseInclSubclauses": "heldSameRelease 이거나, 같은 규격·같은 판에서 번호가 `절 번호.` 로 시작하는 "
                                             "하위 절 하나라도 heldSameRelease 인 절",
            "heldAnyRelease": "규격·절 번호가 같은 본문 조각이 판과 상관없이 있는 절(specReleases 없는 _p12 조각, "
                              "ASN.1 이름 절의 같은 IE 조각 포함)",
            "byShape": "대상 절을 절 기록의 모양으로 나눈 수. void = isVoid 인 절 기록, has_subsections = 하위 절 간선이 있는 절 기록, "
                       "leaf = 그 밖, not_in_structure_source = 절 기록 전체에 없는 id",
            "notHeldSameReleaseEditionWithoutAnyChunk": "heldSameRelease 가 아닌 대상 절 가운데 그 규격·그 판의 본문 조각이 하나도 없는 절",
            "notHeldInclSubclauses": "하위 절까지 넓혀도 같은 판 본문이 없는 대상 절. asn1ChunkAtOrBelow 는 같은 규격의 ASN.1 조각 "
                                     "(tsSectionNumber, 판 정보 없음)이 그 절이나 하위 절에 있는 수",
            "linksToVoidRecord": "대상 절 기록이 isVoid 인 연결. nonVoidRecordInOtherEdition = 같은 규격·같은 절 번호의 Void 가 아닌 "
                                 "절 기록이 다른 판에 있다",
            "packCr": "총회 CR 묶음(belongsToCRPack)에 실린 CR. release 는 그 CR 서식의 Release 칸",
            "everyLinkedClauseHeld*": "연결이 하나 이상 있고 연결된 절 기록이 모두 본문을 가진 묶음 CR",
        },
        "excluded": {
            "parsedCrAndCrClause": "빌드가 파싱한 서식 값과 빌드의 절 번호 파서는 판정에 쓰지 않는다(원본 경로를 찾는 대체 경로로만 쓴다)",
            "RAN2Neo4jAndPhase2": "RAN2 Neo4j 와 Phase-2 파일은 읽지 않는다(재구축 작업이 쓰는 중이다)",
            "neo4jSectionNodes": "Section 노드 속성에 본문이 없어(bodyText.evidenceNoBodyElsewhere) 본문 보유는 Qdrant 만 본다",
            "crChunks": "`ran{N}_cr_chunks` 는 CR 이 바꾼 글이지 규격 절 본문이 아니어서 넣지 않는다",
            "copiesRejected": "파일 이름에 이 CR 번호가 둘째 이후로만 있고 서식 글에도 없는 파일은 이 CR 의 사본으로 보지 않는다",
            "duplicateBytes": "같은 CR 의 바이트가 같은 사본은 한 번만 판정한다",
            "dispositionRecords": "처분(disposition) 기록은 읽지 않는다. RAN1 그래프에 처분 조정이 적용되는 동안 실행했으나 "
                                  "이 측정이 읽는 RAN1 입력은 Phase-4 파일의 modifiesSection·belongsToCRPack, Phase-3 절 기록 "
                                  "파일, Neo4j Section 노드의 속성 이름뿐이다",
        },
        "structureSources": {wg: {"source": structures[wg]["source"], "records": structures[wg]["records"],
                                  "tally": structures[wg]["tally"], "resolverKeys": len(structures[wg]["keys"])}
                             for wg in args.wg},
        "sources": {wg: {"links": loaded[wg]["source"],
                         "sha256": {name: sha256(Path(loaded[wg]["source"]) / name)
                                    for name in ("cr_extensions.jsonld", "section_extensions.jsonld")},
                         "fallbackFormPaths": str(PARSED_CR / wg / "cr_documents.json")}
                    for wg in args.wg},
        "corpus": {"root": str(CR_CORPUS), "indexedFileNameNumbers": len(corpus), "filesRead": len(paths),
                   "readStatus": dict(read_status), "copyIdentity": dict(identity),
                   "headerSpecVersusFileNameSpec": dict(header_vs_file),
                   "labelKindOfReadForms": {str(k): v for k, v in label_kinds.items()},
                   "unreadableFilesBySiblingDocx": {" / ".join(k): v for k, v in sorted(no_part.items())}},
        "memoryAvailableGiB": memory,
        "workers": args.workers,
        "bodyText": None if bodies is None else {
            "location": "Qdrant TS 절 모음의 `text`(또는 `content`) 필드",
            "collections": bodies["collections"],
            "evidenceNoBodyElsewhere": location,
        },
        "wg": {},
    }
    for wg in args.wg:
        result = {"recordsInSource": loaded[wg]["records"], "packCr": len(loaded[wg]["pack"]),
                  "directionAgreement": loaded[wg]["directionAgreement"],
                  "linkAudit": audit_wg(wg, loaded[wg], forms_by_cr, bodies, args.examples, unconfirmed,
                                        structures[wg], build[wg][1])}
        if bodies is not None:
            result["bodyCoverage"] = coverage_wg(wg, loaded[wg], bodies, forms_by_cr, structures[wg], args.examples)
        report["wg"][wg] = result
        audit = result["linkAudit"]
        print(wg, "links", audit["links"], "confirmed", audit["confirmed"], audit["confirmedShare"],
              "notConfirmed", audit["notConfirmedTotal"], audit["notConfirmed"],
              "unavailable", audit["formUnavailableTotal"],
              result.get("bodyCoverage", {}).get("heldSameReleaseShare"),
              result.get("bodyCoverage", {}).get("heldSameReleaseInclSubclausesShare"),
              result.get("bodyCoverage", {}).get("heldAnyReleaseShare"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if args.unconfirmed_jsonl:
        args.unconfirmed_jsonl.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in unconfirmed))


if __name__ == "__main__":
    sys.exit(main())
