"""실무자 질문 한 건을 clause_history 문항으로 바꿔 쓰고 정답 행을 기록에서 유도한다 (모델 호출 없음).

대상은 실무자 질문 단위 `CP_SW_team/CP_SW_case_004_pc1_5_max_output_power_clause_removed_v17` 하나다. 질문은
TS 38.101 v16 에 있던 PC1.5 단일 포트 문장이 v17 에 없다며, 왜 빠졌는지와 회의가 있었는지를 묻는다.
1. 절 찾기: 규격 원문 docx 의 문단에서 그 문장을 찾아 파일·문단 번호·절 제목·판본을 적는다. 38.101 의 모든 부(part)와
   release 판본을 같은 방법으로 훑어 다른 판본에 그 문장이 있는지도 본다. 찾은 절이 SQLite 의 section 표와 Neo4j 의
   Section 노드에 있는지 확인한다.
2. 문항: `build_chain_items.FAMILIES["clause_history"]` 질문 틀에 그 절과 Rel-17 을 넣는다. 질문 틀의 release 는
   절 판본의 release 이고, CR 은 대상 release 가 그와 같을 때만 센다.
3. 정답: `measure_relational_equivalence.SQL["clause_history"]` 두 벌(cr_side·container_side)을 SQLite 에 실행하고
   `crosscheck_chain_items_graph.CYPHER["clause_history"]` 를 Neo4j 에 실행해 행 집합을 맞댄다. 조건 하나를 뺀 대조
   질의도 돌린다. 같은 SQL·Cypher 를 채택 문항 파일의 RAN4 clause_history 문항에 돌려 gold 와 같은지도 본다.
   `--with-generator` 를 주면 생성기(`build_chain_items.Chain`)로도 같은 절의 정답 행을 구한다(메모리를 많이 쓴다).
4. 정답 밖 정보: 정답 CR 의 제목·표지(변경 이유·변경 요약)와 CR 본문 docx 의 변경 표시(삽입·삭제)에서 PC1.5 단일 포트
   문장에 관한 변경을 찾는다. 같은 절의 Rel-16 정답 행도 맥락으로 같이 훑는다. `--with-corpus-scan` 을 주면
   TS 38.101-1 을 대상으로 하는 CR 기록 전부의 본문을 같은 방법으로 훑고, 그 문장을 바꾼 문서와 Rel-16 삽입 CR 이
   합쳤다고 적은 초안과 제목이 같은 문서의 기록·회의록 결정 문장을 적는다. 이 정보는 정답이 아니다.
5. 앞선 답변과의 비교: 정답을 정한 뒤 사례 폴더의 앞선 답변에 적힌 문서 번호·회의를 정답 행과 맞댄다.
   맞댄 결과만 적고 정답은 바꾸지 않는다.

`--db` 는 `export_chain_records_sqlite.py` 가 RAN4 에 대해 내보낸 SQLite 파일이다(처분 기록은 `--phase2-root` 재구축본).
Neo4j 는 읽기만 한다. 접속 정보는 `common.credentials.neo4j_auth()` 로 얻는다.

사용: PYTHONPATH=scripts/common python3 derive_practitioner_chain_item.py --db <RAN4.sqlite> [--with-generator]
     [--with-earlier-answer] [--with-corpus-scan [--workers N]]
저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import io
import json
import re
import sqlite3
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from neo4j import GraphDatabase

from build_chain_items import FAMILIES, SECTION, Chain, local
from common.credentials import neo4j_auth
from crosscheck_chain_items_graph import CYPHER, graph_key
from measure_relational_equivalence import CONTROLS, SQL, VARIANTS

UNIT = "CP_SW_team/CP_SW_case_004_pc1_5_max_output_power_clause_removed_v17"
CASE_DIR = Path("docs/capability/answer/cases") / UNIT
WG = "RAN4"
FAMILY = "clause_history"
SPEC = "38.101-1"
ASKED_RELEASE = "Rel-17"
CONTEXT_RELEASE = "Rel-16"
TS_ROOT = Path("data/corpus/tsg/RAN/formal/TS/RAN4/source")
CR_ROOT = Path("data/corpus/tsg/RAN/formal/change-requests/RAN4")
PHASE2_ROOT = Path("logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/disposition_rebuild")
ADMITTED = Path("logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/chain_items_rebuilt/chain_items_admitted.jsonl")
OUT = Path("logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/practitioner_chain_item.json")
MIN_AVAILABLE_GIB = 8.0

# 질문이 인용한 문장. 두 문장을 따로 찾는다(원문의 철자 오류 `tranmissions` · `a UEs` 도 그대로 둔다).
SENTENCES = (
    "for ue power class 1.5 the maximum output power for single-port transmission is defined as the sum of the "
    "maximum output power from both ue antenna connectors.",
    "for pusch tranmissions, a ues supporting pc1.5 shall meet the maximum output power requirement when scheduled "
    "by dci format 0_0 or by dci format 0_1 configured for single antenna port.",
)
# CR 본문에서 그 문장을 가리키는 조각. 문장이 여러 run 으로 쪼개져도 문단 단위로 붙여서 찾는다.
FRAGMENTS = ("maximum output power for single-port transmission is defined as the sum",
             "supporting pc1.5 shall meet the maximum output power requirement when scheduled by dci format 0_0")
# CR 제목·표지에서 찾는 낱말.
COVER_TERMS = {
    "pc1.5": re.compile(r"PC\s?1\.5|power class 1\.5|PC1dot5", re.I),
    "single_port_text": re.compile(r"single[- ]port|single antenna port|both UE antenna connectors|DCI format 0_[01]", re.I),
}
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
HEADING = re.compile(r"^(?P<number>(?:\d+|[A-Z])(?:\.[0-9A-Za-z]+)*)\s*(?P<title>\S.*)$")
VERSION = re.compile(r"3GPP TS (?P<spec>[\d.\-]+) V(?P<version>\d+\.\d+\.\d+) \((?P<date>[\d-]+)\)")
SECTION_CYPHER = "MATCH (s:Section {sectionId: $key}) RETURN s.sectionNumber AS number, s.sectionTitle AS title"
CR_CYPHER = """MATCH (cr:CR {tdocNumber: $number})
    RETURN cr.title AS title, cr.crNumber AS crNumber, cr.crCategory AS category,
           cr.reasonForChange AS reason, cr.summaryOfChange AS summary"""
EARLIER_ANSWER = ("01_spectra_answer.md", "01_spectra_answer_audit_trail.md")
TDOC = re.compile(r"\b(?:R4|RP)-\d{6,7}\b")
WG_MEETING = re.compile(r"RAN4\s?#\s?\d+(?:bis)?(?:-e)?", re.I)
REPORTS = Path("ontology/input/tsg/RAN/formal/meetings/RAN4/Final_Report")
REPORT_PATHS: dict[str, dict[str, Path]] = {}
# R4-2211252 표지가 합쳤다고 적은 PC1.5 정의 초안. 같은 제목의 다른 문서(다른 release 판 등)를 찾는 데 쓴다.
MERGED_DRAFT = "R4-2208743"
DECISION = re.compile(r"(?:Decision:\s*)?The document was [a-z ]+\.")
# 정답을 정한 뒤 앞선 답변 두 파일을 읽고 적은 메모. 숫자 대조는 earlierAnswerComparison 의 다른 필드가 맡는다.
READING_NOTE = (
    "앞선 답변은 질문 문단이 Rel-16 6.2.1 에 있고, RAN4#103-e 에서 R4-2208743 을 합친 CR1120(R4-2211252, 묶음 "
    "RP-221655, RAN#96)으로 들어갔다고 적는다. 이는 Rel-16 맥락 행(R4-2211252 agreed RAN4#103-e RP-221655)과 "
    "4단계의 본문 삽입 표시와 같다. 앞선 답변이 적은 문서 번호 가운데 정답 28행에 있는 것은 없다. 회의 이름 "
    "RAN4#100-e·RAN4#103-e 와 묶음 RP-221655 는 정답에도 나오지만, 정답에서 그 자리에 있는 것은 앞선 답변이 적지 않은 "
    "다른 CR 이다(goldDocsAtSharedMeetings). 앞선 답변이 Rel-17 쪽 근거로 드는 R4-2115100(CR0914, RAN4#100-e, RP-211897), "
    "R4-2303679(CR1431, RAN4#106, RP-230519), R4-2118550 은 기록에서 R4-2115100 은 Rel-17 6.2G·6.2.2 등을, R4-2303679 는 "
    "Rel-17 6.2G.1 만 고치고 6.2.1 은 고치지 않으며, R4-2118550 은 revised 처분이고 절·묶음 기록이 없다. 그래서 두 결과의 "
    "차이는 범위의 차이다. 문항은 Rel-17 6.2.1 을 고친 CR 을 묻고, 앞선 답변은 같은 내용을 Rel-17 이 6.2G(Tx Diversity)에서 "
    "규정한다는 설명을 근거로 든다. 앞선 답변도 Rel-17 에서 그 문장을 지운 승인 CR 은 특정하지 못했다고 적는다. 이 결과"
    "(Rel-17 정답 CR 본문 어디에도 그 문장의 변경이 없고, Rel-16 에는 RAN4#103-e 에서 삽입)와 같은 방향이다. 앞선 답변과 "
    "검색 기록(retrieval_log.json 73건, retrieval_log_bodies.jsonl 93건의 서로 다른 문서 번호)에는 정답 CR 이 하나도 없고, "
    "4단계 corpus 검색이 찾은 Rel-17 쪽 기록 R4-2208744(RAN4#103-e 회의록 결정 postponed)와 R4-2212773(CR1153, 본문이 "
    "Rel-17 6.2.1 에 그 문장을 삽입, RAN4#104-e 회의록 결정 not pursued)도 없다. 질문의 '회의가 있었나' 에 가장 가까운 "
    "기록은 이 두 건이다. 앞선 답변이 비교한 판본(V16.5.0·V16.12.1·V17.5.0·V17.9.0·V17.23.0·V19.7.0)은 corpus 의 "
    "판본(V16.26.0·V17.21.0)과 달라 여기서 확인하지 않았다. 정답은 바꾸지 않았다.")
CAVEATS = [
    "문항이 묻는 것은 Rel-17 판본 6.2.1 을 고친 CR 과 그 처분·WG 회의·묶음이다. 실무자 질문의 '왜 빠졌나' 는 변경 내용과 "
    "근거라서 E1~E6 밖이고 정답에 넣지 않았다. '회의가 있었나' 는 정답 행의 WG 회의 열이 답한다.",
    "질문은 38.101 의 부(part)를 적지 않았다. 38.101-1~-5 의 모든 corpus 판본을 훑어 그 문장이 38.101-1 Rel-16 판본의 "
    "6.2.1 한 문단에만 있음을 보고 38.101-1 로 정했다.",
    "corpus 에는 release 마다 판본이 하나다(38.101-1 Rel-16 V16.26.0, Rel-17 V17.21.0). 질문의 v16·v17 이 어느 판본인지는 "
    "알 수 없다.",
    "그 문장은 corpus 의 Rel-17·18·19 판본 어디에도 없고, 기록에서는 Rel-16 에 R4-2211252(CR1120, RAN4#103-e agreed)가 "
    "삽입했다. Rel-17 정답 CR 28건의 본문 어디에도 그 문장의 삽입·삭제 표시가 없다. 기록이 보여 주는 것은 'Rel-17 에서 "
    "지웠다' 가 아니라 'Rel-16 유지보수에서 넣었고 Rel-17 판본에는 들어가지 않았다' 이다.",
    "Rel-17 쪽 대응 변경은 정답 밖에 있다. R4-2211252 가 합쳤다고 적은 초안 R4-2208743(Rel-16, RAN4#103-e endorsed)과 "
    "제목이 같은 Rel-17 문서 R4-2208744 는 RAN4#103-e 회의록 결정이 postponed 이고, 같은 제목의 R4-2212773(CR1153, "
    "Rel-17)은 본문이 Rel-17 6.2.1 에 그 문장을 삽입하며 RAN4#104-e 회의록 결정이 not pursued(source_verified, "
    "whole_target)이다. R4-2212773 의 회의록 요약은 'Cat-A postponed at RAN4#103-e' 라고 적는다. 두 건 모두 묶음 기록과 "
    "절 기록(modifiesSection)이 없어 clause_history 질문 틀에는 구조상 들어올 수 없다. 둘 사이의 개정(revision) 기록도 없다. "
    "회의록은 결정만 적고 미루거나 진행하지 않은 이유는 적지 않는다(E1~E6 밖).",
    "R4-2208744 는 회의록이 postponed 라고 적는데 처분(disposition) 기록이 없다. R4-2208743·R4-2208744 는 본문 파일이 없어 "
    "본문 변경을 확인하지 못했다.",
    "corpus 검색은 TS 38.101-1 을 대상으로 하는 CR 기록 8070건 전부를 대상으로 했다. 본문을 읽은 것은 3393건이고, 4590건은 "
    "본문 파일이 없으며, 나머지는 압축 파일이 깨졌거나 .doc 만 있어 읽지 못했다(withUnreadableBodyFile). 읽지 못한 기록에 "
    "그 문장을 바꾼 문서가 더 있는지는 알 수 없다.",
    "R4-2100119 는 회의록 처분이 not_treated(source_verified, whole_target)인데 문서 목록 상태는 agreed 이고 묶음 "
    "RP-210190 에 들어 있다. 질문 틀은 처분 코드를 거르지 않으므로 정답에 남는다. 두 출처가 갈리는 행이다.",
    "조건 하나를 뺀 대조 질의 두 개가 이 절에서는 정답과 같은 행 집합을 낸다. 이 문항에서는 두 조건이 판별하지 못한다.",
    "Rel-17 정답 CR 28건은 모두 본문 docx 를 읽었다. Rel-16 맥락 행의 R4-1907781 은 압축 파일에 .doc 만 있어 읽지 못했다.",
    "CR 제목·표지의 PC1.5 언급은 정규식 검색 결과다. 표지에 PC1.5 가 나오는 Rel-17 정답 CR 은 대역 추가·duty cycle "
    "능력과 그에 따른 power class fallback 규칙에 관한 것이고 그 문장에 관한 것이 아니다.",
    "정답을 정하기 전에 저장소 grep 결과에서 앞선 답변 작업의 파일 이름(logs/capability/answer/case004-fresh-regeneration/ "
    "아래 R4-2208743·R4-2211252 원문 텍스트, logs/capability/answer/date-prose-regeneration/worker-cp004-005/004/"
    "execution_receipts.json)을 보았으나 열지 않았다. 정답은 SQL 결과라 영향이 없다. R4-2211252 는 Rel-16 맥락 SQL 행으로, "
    "R4-2208743 은 R4-2211252 표지로 따로 닿았다.",
    "처분 기록은 disposition_rebuild 재구축본으로 내보낸 SQLite 이고, 이 절과 채택 문항의 RAN4 clause_history 문항에서 "
    "Neo4j RAN4 와 행 집합이 같다.",
]


def available_gib() -> float:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 1024 ** 2
    raise RuntimeError("MemAvailable 없음")


def require_memory(step: str) -> float:
    gib = available_gib()
    if gib < MIN_AVAILABLE_GIB:
        raise SystemExit(f"{step}: 가용 메모리 {gib:.1f} GiB < {MIN_AVAILABLE_GIB} GiB, 멈춘다")
    return round(gib, 1)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(text: str) -> str:
    text = re.sub(r"[‐‑‒–]", "-", text.replace("\xa0", " "))
    return re.sub(r"single port", "single-port", re.sub(r"\s+", " ", text)).strip().lower()


def runs(node, state: str, out: list[tuple[str, str]]) -> None:
    """문단 안의 글을 (상태, 글) 차례로 모은다. 상태는 plain · inserted · deleted 다."""
    if node.tag in (W + "ins", W + "moveTo"):
        state = "inserted"
    elif node.tag in (W + "del", W + "moveFrom"):
        state = "deleted"
    if node.tag == W + "t":
        out.append((state, node.text or ""))
    elif node.tag == W + "delText":
        out.append(("deleted", node.text or ""))
    elif node.tag == W + "noBreakHyphen":
        out.append((state, "-"))
    elif node.tag in (W + "tab", W + "br"):
        out.append((state, " "))
    for child in node:
        runs(child, state, out)


def paragraphs(docx: bytes):
    """docx 문단마다 (번호, 스타일 이름, 바뀌기 전 글, 바뀐 뒤 글)을 낸다.

    스타일 식별자는 문서마다 다르다(`Heading3` 또는 `30`). styles.xml 의 이름(`heading 3`)으로 바꿔 낸다.
    """
    archive = zipfile.ZipFile(io.BytesIO(docx))
    names = {}
    if "word/styles.xml" in archive.namelist():
        for style in ET.fromstring(archive.read("word/styles.xml")).iter(W + "style"):
            name = style.find(W + "name")
            names[style.get(W + "styleId")] = name.get(W + "val") if name is not None else ""
    root = ET.fromstring(archive.read("word/document.xml"))
    for index, paragraph in enumerate(root.find(W + "body").iter(W + "p")):
        style = paragraph.find(f"{W}pPr/{W}pStyle")
        identifier = style.get(W + "val") if style is not None else ""
        out: list[tuple[str, str]] = []
        runs(paragraph, "plain", out)
        before = "".join(text for state, text in out if state != "inserted")
        after = "".join(text for state, text in out if state != "deleted")
        yield index, names.get(identifier) or identifier, before, after


def cover_version(directory: Path) -> dict | None:
    for path in sorted(directory.glob("*_cover.docx")):
        for _, _, _, text in paragraphs(path.read_bytes()):
            if match := VERSION.search(text):
                return {"file": str(path), **match.groupdict()}
    return None


def locate_sentence() -> dict:
    """38.101 모든 부·release 판본에서 질문이 인용한 문장을 찾는다."""
    releases = []
    for directory in sorted(TS_ROOT.glob("38.101-*/Rel-*")):
        hits, files = [], []
        for path in sorted(directory.glob("*.docx")):
            if path.name.endswith("_cover.docx"):
                continue
            files.append({"file": str(path), "sha256": sha256(path)})
            heading = None
            for index, style, _, text in paragraphs(path.read_bytes()):
                flat = normalize(text)
                if style.lower().startswith("heading") and (match := HEADING.match(text.strip())):
                    heading = {"style": style, "number": match["number"], "title": match["title"].strip()}
                found = [n for n, sentence in enumerate(SENTENCES, 1) if sentence in flat]
                if found:
                    hits.append({"file": str(path), "paragraphIndex": index, "sentencesFound": found,
                                 "underHeading": heading, "text": text.strip()})
        releases.append({"spec": directory.parent.name, "release": directory.name,
                         "version": cover_version(directory), "filesScanned": files, "hits": hits})
    return {"method": "docx word/document.xml 의 body 아래 모든 w:p 를 차례로 세고(문단 번호 0부터), w:t 글을 이어 붙여 "
                      "소문자·공백 정규화한 문단에 인용 문장 두 개가 들어 있는지 본다. 문단 앞의 가장 가까운 heading "
                      "스타일 문단을 그 문단의 절로 적는다.",
            "sentences": SENTENCES, "byRelease": releases}


def rows_sql(db: sqlite3.Connection, sql: str, anchor: str) -> set[tuple]:
    return {tuple(row) for row in db.execute(sql, {"anchor": anchor})}


def rows_cypher(session, anchor: str) -> set[tuple]:
    return {tuple(row.values()) for row in session.run(CYPHER[FAMILY], anchor=graph_key(anchor))}


def derive(db: sqlite3.Connection, session, anchor: str) -> dict:
    """한 절의 정답 행을 SQL 두 벌과 Cypher 로 구하고 대조 질의를 돌린다."""
    sql = {variant: rows_sql(db, SQL[FAMILY].format(**names), anchor) for variant, names in VARIANTS.items()}
    graph = rows_cypher(session, anchor)
    controls = {}
    for name, (clause, families) in CONTROLS.items():
        if FAMILY not in families:
            continue
        full = SQL[FAMILY].format(**VARIANTS["cr_side"])
        loose = rows_sql(db, full.replace(clause, ""), anchor)
        controls[name] = {"removedFromSql": clause.strip(), "rows": len(loose),
                          "sameAsGold": loose == sql["cr_side"],
                          "onlyWithoutCondition": sorted(loose - sql["cr_side"])}
    return {"rows": sorted(sql["cr_side"]),
            "agreement": {"crSideRows": len(sql["cr_side"]), "containerSideRows": len(sql["container_side"]),
                          "cypherRows": len(graph), "crSideEqualsContainerSide": sql["cr_side"] == sql["container_side"],
                          "sqlEqualsCypher": sql["cr_side"] == graph,
                          "onlyInSql": sorted(sql["cr_side"] - graph), "onlyInCypher": sorted(graph - sql["cr_side"])},
            "conditionControls": controls}


def pack_sources(db: sqlite3.Connection, numbers: list[str]) -> list[dict]:
    """문서 목록의 묶음 번호와 묶음 기록의 소속이 갈리는 문서(`verify_chain_items.py` 검사 5의 조건)."""
    differ = []
    for number in numbers:
        field, = db.execute("SELECT pack_field FROM document WHERE number = ?", (number,)).fetchone()
        packs = sorted(p for p, in db.execute(
            "SELECT p.pack_number FROM cr_in_pack m JOIN cr_pack p ON p.id = m.pack_id "
            "JOIN document d ON d.id = m.cr WHERE d.number = ?", (number,)))
        if field and field.startswith("RP-") and field not in packs:
            differ.append({"document": number, "listPackField": field, "packRecords": packs})
    return differ


def closed_code_rows(db: sqlite3.Connection, rows: list[tuple]) -> list[dict]:
    """처분 코드가 agreed·approved·endorsed 가 아닌 정답 행의 문서 기록을 함께 적는다."""
    out = []
    for number, code, meeting, pack in rows:
        if code in ("agreed", "approved", "endorsed"):
            continue
        status, release = db.execute("SELECT list_status, target_release FROM document WHERE number = ?",
                                     (number,)).fetchone()
        records = [dict(zip(("code", "meeting", "evidenceStatus", "scope", "evidencePath"), r)) for r in db.execute(
            "SELECT d.code, g.label, d.evidence_status, d.scope, d.evidence_path FROM disposition d "
            "JOIN resolution r ON r.id = d.resolution_id JOIN meeting g ON g.id = r.meeting_id "
            "JOIN document doc ON doc.id = d.target WHERE doc.number = ?", (number,))]
        out.append({"row": [number, code, meeting, pack], "tdocListStatus": status, "targetRelease": release,
                    "allDispositionRecords": records})
    return out


def cr_body_files(number: str) -> list[Path]:
    found = sorted(CR_ROOT.glob(f"source/Rel-*/wg_docs/{number}.zip"))
    return found or sorted(CR_ROOT.glob(f"derived/Rel-*/TSG/*/*{number}*.docx"))


def scan_body(number: str) -> dict:
    """CR 본문 docx 에서 인용 문장 조각이 삽입·삭제·그대로 중 어디에 있는지 본다."""
    files, hits = [], []
    for path in cr_body_files(number):
        try:
            archive = None if path.suffix == ".docx" else zipfile.ZipFile(path)
        except zipfile.BadZipFile:
            files.append({"file": str(path), "readable": False, "error": "BadZipFile"})
            continue
        members = [(path.name, path.read_bytes())] if archive is None else [
            (name, archive.read(name)) for name in archive.namelist()
            if name.lower().endswith(".docx") and not name.startswith("__MACOSX")]
        if not members:
            files.append({"file": str(path), "readable": False, "members": archive.namelist()})
        for name, data in members:
            try:
                heading = None
                for index, style, before, after in paragraphs(data):
                    if style.lower().startswith("heading") and (match := HEADING.match(after.strip())):
                        heading = f"{match['number']} {match['title'].strip()}"
                    old, new = normalize(before), normalize(after)
                    for fragment in FRAGMENTS:
                        if fragment in old or fragment in new:
                            kind = ("unchanged" if fragment in old and fragment in new
                                    else "deleted" if fragment in old else "inserted")
                            hits.append({"member": name, "paragraphIndex": index, "underHeading": heading,
                                         "fragment": fragment, "change": kind, "textAfter": after.strip()[:400],
                                         "textBefore": before.strip()[:400]})
                files.append({"file": str(path), "member": name, "readable": True})
            except (zipfile.BadZipFile, KeyError, ET.ParseError) as error:
                files.append({"file": str(path), "member": name, "readable": False, "error": type(error).__name__})
    return {"files": files, "hits": hits}


def scan_cover(session, number: str) -> dict:
    record = session.run(CR_CYPHER, number=number).single()
    if record is None:
        return {"inGraph": False}
    lines = {}
    for field in ("title", "reason", "summary"):
        for line in (record[field] or "").splitlines():
            for term, pattern in COVER_TERMS.items():
                if pattern.search(line):
                    lines.setdefault(field, []).append({"term": term, "line": line.strip()[:300]})
    return {"inGraph": True, "title": record["title"], "crNumber": record["crNumber"],
            "category": record["category"], "matchingLines": lines}


def pc15_scan(session, rows: list[tuple]) -> list[dict]:
    out = []
    for number in sorted({row[0] for row in rows}):
        cover, body = scan_cover(session, number), scan_body(number)
        changed = sorted({h["change"] for h in body["hits"] if h["change"] != "unchanged"})
        out.append({"document": number, "cover": cover, "body": body,
                    "coverMentionsPc15": any(l["term"] == "pc1.5" for ls in cover.get("matchingLines", {}).values()
                                             for l in ls),
                    "coverMentionsSinglePortText": any(l["term"] == "single_port_text"
                                                       for ls in cover.get("matchingLines", {}).values() for l in ls),
                    "bodyChangesQuotedSentence": changed,
                    "bodyShowsQuotedSentenceUnchanged": any(h["change"] == "unchanged" for h in body["hits"])})
    return out


def generator_rows(anchor: str) -> dict:
    gib = require_memory("generator")
    chain = Chain(WG, phase2_root=PHASE2_ROOT)
    for section, _, rows, _ in chain.candidates(FAMILY):
        if section == anchor:
            return {"availableGibBefore": gib, "rows": sorted(set(rows))}
    return {"availableGibBefore": gib, "rows": []}


def control_items(db: sqlite3.Connection, session, path: Path) -> dict:
    """채택 문항 파일의 RAN4 clause_history 문항에 같은 SQL·Cypher 를 돌려 gold 와 같은지 센다."""
    items = [i for i in map(json.loads, path.read_text().splitlines()) if i["wg"] == WG and i["family"] == FAMILY]
    differ = []
    for item in items:
        gold = {tuple(r) for r in item["gold"]}
        result = derive(db, session, item["anchor"])
        if set(map(tuple, result["rows"])) != gold or not result["agreement"]["sqlEqualsCypher"]:
            differ.append(item["id"])
    return {"itemFile": str(path), "items": len(items), "sameAsGold": len(items) - len(differ), "differ": differ}


def document_record(db: sqlite3.Connection, number: str) -> dict:
    """문서 하나의 기록: 대상 release, 고치는 38.101-1 절, 처분, 묶음과 묶음의 총회."""
    row = db.execute("SELECT id, doc_type, cr_number, spec, target_release, list_status, presented_at FROM document "
                     "WHERE number = ?", (number,)).fetchone()
    if row is None:
        pack = db.execute("SELECT tsg_meeting FROM cr_pack WHERE pack_number = ?", (number,)).fetchone()
        return {"document": number, "record": "cr_pack" if pack else None, "tsgMeeting": pack[0] if pack else None}
    identifier, kind, cr, spec, release, status, presented = row
    sections = sorted(s.removeprefix("tdoc:section/") for s, in db.execute(
        "SELECT section_id FROM cr_modifies_section WHERE cr = ?", (identifier,)))
    return {"document": number, "record": kind, "crNumber": cr, "spec": spec, "targetRelease": release,
            "listStatus": status, "presentedAt": presented, "sectionsModified": sections,
            "dispositions": [list(r) for r in db.execute(
                "SELECT d.code, g.label, d.evidence_status, d.scope, d.evidence_path FROM disposition d "
                "JOIN resolution r ON r.id = d.resolution_id JOIN meeting g ON g.id = r.meeting_id "
                "WHERE d.target = ?", (identifier,))],
            "packs": [list(r) for r in db.execute(
                "SELECT p.pack_number, p.tsg_meeting FROM cr_in_pack m JOIN cr_pack p ON p.id = m.pack_id "
                "WHERE m.cr = ?", (identifier,))]}


def report_paths() -> dict[str, Path]:
    """회의 ID(`RAN4#84bis`) -> 회의록 파일. 파일명의 회의 표기(`84Bis` · `103-e`)는 phase-1 의 정본 규칙으로 읽는다."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "meeting_id_RAN4", "scripts/tsg/RAN/formal/RAN4/phase-1/jsonld/meeting_id.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    paths = {}
    for path in sorted(REPORTS.glob("Final_Report_RAN4-*.docx")):
        meeting = module.extract_meeting_from_filename(f"TSGR4_{path.stem.removeprefix('Final_Report_RAN4-')}")
        if not meeting or meeting in paths:
            raise SystemExit(f"{path.name}: no meeting or a second report for {meeting}")
        paths[meeting] = path
    return paths


def report_decision(number: str, presented: str | None) -> dict:
    """문서를 낸 WG 회의 회의록에서 그 문서 번호 뒤 첫 처분 문장(과 요지 문장)을 적는다. 제출 회사는 옮기지 않는다."""
    if not presented:
        return {"report": None}
    meeting = presented.removeprefix("tdoc:meeting/").replace("_", "#", 1)
    path = REPORT_PATHS.setdefault("index", report_paths()).get(meeting)
    if path is None:
        return {"report": meeting, "exists": False}
    texts = [re.sub(r"\s+", " ", text).strip() for _, _, _, text in paragraphs(path.read_bytes())]
    found = []
    for index, text in enumerate(texts):
        if not text.startswith(number):
            continue
        entry = {"paragraphIndex": index}
        for later in range(index + 1, min(index + 8, len(texts))):
            if texts[later] == "Abstract:" and later + 1 < len(texts):
                entry["abstract"] = texts[later + 1][:300]
            if match := DECISION.search(texts[later]):
                entry["decision"] = match.group(0)
                break
        found.append(entry)
    return {"report": str(path), "sha256": sha256(path), "mentions": found}


def corpus_scan(db: sqlite3.Connection, session, workers: int) -> dict:
    """정답 밖: TS 38.101-1 을 대상으로 하는 RAN4 CR 기록 전부의 본문과, 합친 초안과 제목이 같은 문서를 본다."""
    numbers = [n for n, in db.execute("SELECT number FROM document WHERE spec = ? AND doc_type = 'tdoc:CR' "
                                      "ORDER BY number", (SPEC,))]
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
        bodies = dict(zip(numbers, pool.map(scan_body, numbers, chunksize=32)))
    title = session.run("MATCH (c:Tdoc {tdocNumber: $n}) RETURN c.title AS t", n=MERGED_DRAFT).single()["t"]
    same_title = sorted(r["n"] for r in session.run("MATCH (c:Tdoc {title: $t}) RETURN c.tdocNumber AS n", t=title))
    changed = sorted(n for n, b in bodies.items() if any(h["change"] != "unchanged" for h in b["hits"]))
    records = []
    for number in sorted(set(changed) | set(same_title)):
        record = document_record(db, number)
        body = bodies.get(number) or scan_body(number)
        records.append({**record, "bodyHits": [{k: h[k] for k in ("member", "paragraphIndex", "underHeading",
                                                                  "fragment", "change")} for h in body["hits"]],
                        "bodyReadable": any(f["readable"] for f in body["files"]),
                        "wgReport": report_decision(number, record.get("presentedAt"))})
    return {"scope": f"document 표에서 spec = {SPEC}, doc_type = tdoc:CR 인 기록 전부",
            "crRecords": len(numbers),
            "withReadableBody": sum(any(f["readable"] for f in b["files"]) for b in bodies.values()),
            "withoutBodyFile": sum(not b["files"] for b in bodies.values()),
            "withUnreadableBodyFile": sum(bool(b["files"]) and not any(f["readable"] for f in b["files"])
                                          for b in bodies.values()),
            "crsChangingQuotedText": changed, "mergedDraft": MERGED_DRAFT, "mergedDraftTitle": title,
            "sameTitleDocuments": same_title, "records": records}


def earlier_answer(db: sqlite3.Connection, gold: list[tuple], context: list[tuple], outside: list[str]) -> dict:
    """앞선 답변 파일에 적힌 문서 번호·회의를 정답 행·Rel-16 맥락 행·정답 밖 검색 문서와 맞대고, 그 문서들의 기록을 적는다."""
    gold_docs, context_docs, outside_docs = {r[0] for r in gold}, {r[0] for r in context}, set(outside)
    gold_meetings = {r[2].lower() for r in gold}
    files, named = [], set()
    for name in EARLIER_ANSWER:
        path = CASE_DIR / name
        text = path.read_text()
        tdocs = sorted(set(TDOC.findall(text)))
        named |= set(tdocs)
        meetings = sorted({re.sub(r"\s", "", m).lower() for m in WG_MEETING.findall(text)})
        files.append({"file": str(path), "sha256": sha256(path), "tdocsMentioned": tdocs,
                      "inGold": sorted(set(tdocs) & gold_docs), "inRel16Context": sorted(set(tdocs) & context_docs),
                      "packsInGold": sorted(set(tdocs) & {r[3] for r in gold}),
                      "wgMeetingsMentioned": meetings, "wgMeetingsInGold": sorted(set(meetings) & gold_meetings),
                      # 회의 이름이 겹쳐도 그 회의의 정답 CR 을 답변이 적었는지는 따로 본다.
                      "goldDocsAtSharedMeetings": {m: sorted(r[0] for r in gold if r[2].lower() == m)
                                                   for m in sorted(set(meetings) & gold_meetings)},
                      "corpusScanDocsMentioned": sorted(set(tdocs) & outside_docs)})
    # 검색 기록은 답변이 무엇을 보았는지만 센다(본문을 옮기지 않는다).
    logs = []
    for path in sorted(CASE_DIR.glob("retrieval_log*")):
        tdocs = set(TDOC.findall(path.read_text()))
        logs.append({"file": str(path), "sha256": sha256(path), "distinctTdocs": len(tdocs),
                     "goldDocsSeen": sorted(tdocs & gold_docs), "rel16ContextDocsSeen": sorted(tdocs & context_docs),
                     "corpusScanDocsSeen": sorted(tdocs & outside_docs)})
    return {"answerFiles": files, "retrievalLogs": logs,
            "namedDocumentRecords": [document_record(db, n) for n in sorted(named)]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--bolt", default="bolt://localhost:7690")
    parser.add_argument("--items", type=Path, default=ADMITTED)
    parser.add_argument("--with-generator", action="store_true")
    parser.add_argument("--with-earlier-answer", action="store_true",
                        help="정답을 정한 뒤에만 준다. 사례 폴더의 앞선 답변을 읽어 맞댄다")
    parser.add_argument("--with-corpus-scan", action="store_true",
                        help="TS 38.101-1 CR 기록 전부의 본문에서 인용 문장의 삽입·삭제를 찾는다")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    memory = {"availableGibAtStart": require_memory("start")}

    location = locate_sentence()
    hits = [h for r in location["byRelease"] for h in r["hits"]]
    clause = hits[0]["underHeading"] if len(hits) == 1 and hits[0]["sentencesFound"] == [1, 2] else None
    if clause is None:
        raise SystemExit(f"인용 문장이 한 판본의 한 문단에서만 나와야 하는데 {len(hits)} 곳에서 나왔다")
    found_in = next(r for r in location["byRelease"] if r["hits"])
    asked = f"tdoc:section/{SPEC}-{ASKED_RELEASE}-{clause['number']}"
    context = f"tdoc:section/{SPEC}-{CONTEXT_RELEASE}-{clause['number']}"
    names = {**SECTION.match(asked).groupdict(), "wg": WG}
    item = {"id": f"{WG}-{FAMILY}-{local(asked)}", "wg": WG, "family": FAMILY, "hops": FAMILIES[FAMILY]["hops"],
            "anchor": asked, "question": FAMILIES[FAMILY]["question"].format(**names),
            "fields": FAMILIES[FAMILY]["fields"]}

    db = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    with GraphDatabase.driver(args.bolt, auth=neo4j_auth()) as driver, driver.session() as session:
        anchors = {}
        for anchor in (asked, context):
            row = db.execute("SELECT spec, release, clause FROM section WHERE id = ?", (anchor,)).fetchone()
            node = session.run(SECTION_CYPHER, key=graph_key(anchor)).single()
            anchors[anchor] = {"sqliteSection": dict(zip(("spec", "release", "clause"), row)) if row else None,
                               "neo4jSection": dict(node) if node else None}
        result = derive(db, session, asked)
        context_result = derive(db, session, context)
        gold = [tuple(r) for r in result["rows"]]
        context_rows = [tuple(r) for r in context_result["rows"]]
        result["agreement"]["admittedItemControl"] = control_items(db, session, args.items)
        if args.with_generator:
            generated = generator_rows(asked)
            result["agreement"]["generator"] = {"availableGibBefore": generated["availableGibBefore"],
                                                "rows": len(generated["rows"]),
                                                "equalsSql": set(map(tuple, generated["rows"])) == set(gold)}
        memory["availableGibBeforeCrScan"] = require_memory("cr scan")
        scan = pc15_scan(session, gold)
        context_scan = pc15_scan(session, context_rows)
        outside = corpus_scan(db, session, args.workers) if args.with_corpus_scan else None

    changed = [s["document"] for s in scan if s["bodyChangesQuotedSentence"] or s["coverMentionsSinglePortText"]]
    report = {
        "unitId": UNIT,
        "rephrasedQuestion": item,
        "family": {"name": FAMILY, "fields": FAMILIES[FAMILY]["fields"], "hops": FAMILIES[FAMILY]["hops"],
                   "template": FAMILIES[FAMILY]["question"],
                   "templateRelease": "질문 틀의 {release} 는 절 판본(anchor)의 release 다. 이 문항은 Rel-17 판본의 절을 "
                                      "묻고, SQL·Cypher·생성기 모두 CR 의 대상 release 가 Rel-17 인 CR 만 센다."},
        "clause": {"spec": SPEC, "clause": clause["number"], "title": clause["title"], "askedAnchor": asked,
                   "contextAnchor": context, "foundIn": {"release": found_in["release"], "version": found_in["version"],
                                                         "hit": found_in["hits"][0]},
                   "anchorRecords": anchors, "howLocated": location},
        "goldRows": [list(r) for r in gold],
        "rel16ContextRows": {"note": "같은 절의 Rel-16 판본에 같은 질의를 돌린 행. 정답이 아니다.",
                             "rows": [list(r) for r in context_rows], "agreement": context_result["agreement"]},
        "sql": {variant: " ".join(SQL[FAMILY].format(**names).split()) for variant, names in VARIANTS.items()},
        "cypher": " ".join(CYPHER[FAMILY].split()),
        "agreement": {**result["agreement"], "conditionControls": result["conditionControls"],
                      "packSourcesDiffer": pack_sources(db, sorted({r[0] for r in gold})),
                      "rowsWithClosedCode": closed_code_rows(db, gold)},
        "pc15Rows": {
            "note": "정답이 아니다. 문장이 왜 빠졌는지는 변경 내용·근거라서 E1~E6(처분·회의·개정·CR→묶음·묶음→총회·CR→절) 밖이다.",
            "goldCrsIndicatingChangeToQuotedText": changed,
            "goldCrsMentioningPc15Otherwise": [s["document"] for s in scan
                                               if s["coverMentionsPc15"] and s["document"] not in changed],
            "goldScan": scan,
            "rel16ContextCrsChangingQuotedText": [s["document"] for s in context_scan if s["bodyChangesQuotedSentence"]],
            "rel16ContextScan": context_scan,
            "outsideGold": outside},
        "memory": memory,
        "inputs": {"db": str(args.db), "dbSha256": sha256(args.db), "bolt": args.bolt, "itemFile": str(args.items)},
    }
    if args.with_earlier_answer:
        outside_docs = [r["document"] for r in outside["records"]] if outside else []
        report["earlierAnswerComparison"] = {**earlier_answer(db, gold, context_rows, outside_docs),
                                             "readingNote": READING_NOTE}
    report["caveats"] = CAVEATS
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("clause:", SPEC, found_in["release"], clause["number"], clause["title"], found_in["version"]["version"],
          "paragraph", found_in["hits"][0]["paragraphIndex"])
    print("question:", item["question"])
    print("gold rows:", len(gold))
    for row in gold:
        print("  ", *row)
    print("agreement:", {k: v for k, v in result["agreement"].items() if not isinstance(v, (list, dict))},
          result["agreement"]["admittedItemControl"] | {"differ": result["agreement"]["admittedItemControl"]["differ"]},
          result["agreement"].get("generator"))
    print("controls:", {k: (v["rows"], v["sameAsGold"]) for k, v in result["conditionControls"].items()})
    print("rel16 context rows:", len(context_rows), context_result["agreement"]["sqlEqualsCypher"])
    print("gold CRs changing quoted text:", changed)
    print("gold CRs mentioning PC1.5 otherwise:", report["pc15Rows"]["goldCrsMentioningPc15Otherwise"])
    print("rel16 context CRs changing quoted text:", report["pc15Rows"]["rel16ContextCrsChangingQuotedText"])
    if outside:
        print("corpus scan:", outside["crRecords"], "records,", outside["withReadableBody"], "readable,",
              outside["withoutBodyFile"], "without file,", outside["withUnreadableBodyFile"], "unreadable;",
              "changing quoted text", outside["crsChangingQuotedText"],
              "; same title as", MERGED_DRAFT, outside["sameTitleDocuments"])
        for entry in outside["records"]:
            print("  ", entry["document"], entry.get("crNumber"), entry.get("targetRelease"), entry.get("listStatus"),
                  [d[:2] for d in entry.get("dispositions", [])], entry.get("packs"),
                  {(h["underHeading"], h["change"]) for h in entry["bodyHits"]},
                  [m.get("decision") for m in entry["wgReport"].get("mentions", [])])
    if args.with_earlier_answer:
        comparison = report["earlierAnswerComparison"]
        for entry in comparison["answerFiles"]:
            print("earlier:", entry["file"], "tdocs", entry["tdocsMentioned"], "inGold", entry["inGold"],
                  "inRel16Context", entry["inRel16Context"], "meetingsInGold", entry["wgMeetingsInGold"],
                  "corpusScanDocs", entry["corpusScanDocsMentioned"])
        for entry in comparison["retrievalLogs"]:
            print("earlier log:", entry["file"], "tdocs", entry["distinctTdocs"], "goldSeen", entry["goldDocsSeen"],
                  "rel16ContextSeen", entry["rel16ContextDocsSeen"], "corpusScanSeen", entry["corpusScanDocsSeen"])
        for entry in comparison["namedDocumentRecords"]:
            print("  named:", entry["document"], entry.get("targetRelease"), entry.get("sectionsModified", [])[:10],
                  entry.get("dispositions"), entry.get("packs"), entry.get("tsgMeeting") or "")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
