"""세 갈래 묶음 문항(`pack_status3`)의 구축 통과 검사와 음성 대조 (모델 호출 없음).

`build_abstention_items.py` 의 선택 코드를 가져오지 않는다. 인스턴스 파일을 메모리 SQLite 에 따로 싣고, 질문이
주는 판정 차례를 질의로 다시 따라가 문항마다 갈래·정답·근거를 새로 구한 뒤 문항에 적힌 값과 맞댄다.
판정 차례는 질문 문장과 같다.
1) 묶음 기록이 문서를 실으면 answer 다. 정답은 그 묶음들의 (묶음 번호, TSG RAN 회의)다.
   묶음 → CR(`hasCR`)과 CR → 묶음(`belongsToCRPack`)을 따로 싣고 둘이 같은지도 본다.
2) 아니고 원문 확인한 문서 전체 처분이 있고 모두 질문이 든 닫는 처분이면 none 이다. 정답은 빈 행 집합이다.
3) 그 밖은 insufficient 다. 정답은 두 칸이 모두 `INSUFFICIENT_RECORDS` 인 행 하나다.
판정 차례만으로 답이 하나로 정해지게 하려고 만드는 쪽 docstring 이 둔 조건도 다시 따진다. 걸리면 문제 이름을 남긴다.
- 모든 갈래: pack_directions_disagree · document_list_pack_column_disagrees · same_cr_identity_packed_outside_gold ·
  not_a_numbered_change_request
- answer: pack_record_conflicts_with_closure (닫는 처분뿐이거나 문서 목록 상태가 닫힘)
- none: unverified_or_partial_decision_record · document_list_status_conflicts · later_revision_packed ·
  same_cr_or_later_revision_not_settled · closing_record_not_from_wg_meeting_report
- insufficient: has_later_revision · unverified_or_partial_decision_record · document_list_status_conflicts ·
  insufficiency_basis_not_supported (승인 회의가 묶음 기록이 덮는 기간 안에 있다, 보고서 본문에 문서 번호의 숫자가
  나온다, 승인도 닫힘도 아닌 처분이 있다) · same_cr_not_consistent_with_basis
- anchor_in_gated_items: 기준 문서가 지금 채택된 문항의 기준 문서·근거 문서·정답 칸에 나온다.
덮는 기간은 agreed 로 승인한 CR 이 하나라도 묶음 기록에 실린 작업반 회의 가운데 차례가 가장 이른 회의부터 가장 늦은
회의까지다. 회의 차례는 회의 이름(`tdoc:meetingNumber`)의 번호와 bis 표시(`#100b-e` · `#101bis`)로 읽는다.
보고서 본문의 숫자는 docx 의 word/*.xml 을 XML 로 읽어 문단(w:p)마다 w:t 글을 이은 뒤 숫자열을 뽑는다. 줄 안 하이픈
(`w:noBreakHyphen`)은 "-" 로, 탭·줄바꿈·기호 요소(`w:tab` · `w:ptab` · `w:br` · `w:cr` · `w:sym`)는 공백으로 읽어 경계로 둔다.

문항 검사: 위 판정에 더해 갈래·family·basis·expectsEmpty 가 판정과 같은지, 정답 행 집합과 행 너비, id 가 갈래를
드러내지 않는지(`{WG}-pack_status3-{문서 번호}`), 모든 문항의 질문이 기준 문서 부분만 다른 한 틀인지, 근거로 실은
처분 기록이 기준 문서의 원문 확인 처분과 같고 원문 파일 SHA-256 이 지금 파일과 같은지 본다. 끝으로 이 검사의 판정만으로
만든 문항과 통째로 맞대어, 따로 보지 않은 칸(제출 회의 · 덮는 기간 등)도 남지 않게 한다.
묶음 검사: 모든 tdoc:CR 문서를 같은 방식으로 판정해 갈래·근거별 수(채택 문항을 빼기 전·후)를 구해 요약 파일과 맞대고,
자기 모집단에서 seed 뽑기를 다시 해 문항의 기준 문서와 같은지 본다. 입력 파일·보고서·채택 문항 파일의 SHA-256 도 맞댄다.
틀 검사: 공통 질문 틀이 판정 차례 세 문장, 요청 필드 표현, 닫는 처분 다섯 가지, 정해지지 않음 낱말을 모두 담는다.

음성 대조(`--controls`): 문항이나 기록을 한 군데씩 틀리게 바꾸고 검사가 기대한 까닭으로 막는지 센다. 기록을 바꾸는
대조는 SAVEPOINT 안에서 바꾸고 되돌린다. 대상은 뽑힌 문항 전부와, 모집단에 있는데 한 문항도 뽑히지 않은 근거의
모집단 문서로 이 검사가 직접 만든 문항이다. 대조마다 caught_for_expected_reason · caught_for_other_reason · admitted ·
not_applicable 을 센다.

사용: python3 verify_abstention_items.py --items <abstention_items.jsonl> --exclude-items <jsonl> [...] --controls
만들 때 준 `--phase2-root` · `--phase4-root` · `--exclude-items` 를 똑같이 준다. 저장소 루트에서 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import copy
import dataclasses
import functools
import hashlib
import json
import random
import re
import sqlite3
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

INSTANCES = Path("ontology/output/tsg/RAN/formal/instances")
MEETINGS = Path("ontology/input/tsg/RAN/formal/meetings")
WORD = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
# 질문이 닫는 처분으로 드는 말. 처분 코드는 말 사이 빈칸을 밑줄로 쓴 값이다.
CLOSING_WORDS = ("withdrawn", "not treated", "not pursued", "rejected", "not agreed")
CLOSING_CODES = {word.replace(" ", "_") for word in CLOSING_WORDS}
# 만드는 쪽 docstring 이 정한 문서 목록 상태 조건.
NONE_STATUS = set(CLOSING_WORDS) | {"available", "reserved", ""}
AGREED_STATUS = {"agreed", "available", ""}
SILENT_STATUS = {"available", ""}
# 같은 CR 의 다른 판이 가지면 CR 로 읽는 풀이에게 승인 없이 끝났다고 정해지는 처분.
SETTLED_CODES = CLOSING_CODES | {"revised", "noted", "merged"}
APPROVING_CODES = {"agreed", "endorsed", "conditionally_agreed"}
TOKEN = "INSUFFICIENT_RECORDS"
FIELDS = ["cr_pack", "tsg_meeting"]
TEMPLATE = "pack_status3"
BASIS = {"answer": "pack_record", "none": "closed_without_pack", "gap": "agreed_outside_pack_records",
         "silent": "no_decision_recorded", "other": "other_decision"}
CLASSES = ("answer", "none", "insufficient")
ANCHOR_PLACEHOLDER = "change request {doc} (CR {cr} to TS {spec})"
# 공통 틀이 담아야 하는 문장 조각. 앞의 둘은 요청 필드, 다음 셋은 판정 차례, 나머지는 빈 답과 정해지지 않음의 구분이다.
REQUIRED_PHRASES = (
    "CR pack document number", "TSG RAN meeting",
    "First, if a CR pack record lists this change request, give one row for each such CR pack.",
    "Otherwise, if a {wg} meeting report records a decision on the whole document that closed it without approval",
    "Otherwise the records do not determine the CR pack",
    "answer with no rows", f"exactly one row that has {TOKEN} in both fields", "not with an empty answer")
# 기존 `pack_lookup` 의 질문 틀(build_chain_items.py). 판정 차례가 없는 질문으로 바꿔 넣는 대조에 쓴다.
PACK_LOOKUP_QUESTION = ("In which TSG RAN CR pack was change request {doc} (CR {cr} to TS {spec}) submitted? "
                        "Give the CR pack document number and the TSG RAN meeting.")
# 작업 지시가 정한 멈춤 기준. 처분 파일은 수백 MB 이고 읽으면 그 몇 배를 쓴다.
MEMORY_FLOOR_GIB = 8
# 대조가 기록에 넣는 가상 묶음·문서. 실제 번호와 겹치지 않는다.
FAKE_PACK = ("tdoc:crpack/RP-000000", "RP-000000", "RAN#0")
FAKE_SHA = "0" * 64

SCHEMA = """
CREATE TABLE doc (id TEXT PRIMARY KEY, number TEXT, type TEXT, cr TEXT, cr_raw TEXT, spec TEXT,
                  status TEXT, pack_col TEXT, presented TEXT);
CREATE INDEX doc_identity ON doc (cr, spec);
CREATE TABLE revision (earlier TEXT, later TEXT, PRIMARY KEY (earlier, later));
CREATE TABLE meeting (id TEXT PRIMARY KEY, label TEXT, num INTEGER, bis INTEGER);
CREATE TABLE disp (rid TEXT, target TEXT, code TEXT, usable INTEGER, meeting TEXT, did TEXT, path TEXT,
                   sha TEXT, locator TEXT);
CREATE INDEX disp_target ON disp (target);
CREATE TABLE pack (id TEXT PRIMARY KEY, number TEXT, tsg TEXT);
CREATE TABLE member (pack TEXT, cr TEXT, PRIMARY KEY (pack, cr));
CREATE INDEX member_cr ON member (cr);
CREATE TABLE member_fwd (cr TEXT, pack TEXT, PRIMARY KEY (cr, pack));
CREATE TABLE mention (digits TEXT PRIMARY KEY);
"""


def available_gib() -> float:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 2 ** 20
    raise RuntimeError("MemAvailable not found")


@functools.lru_cache(maxsize=None)
def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def records(path: Path) -> list[dict]:
    return json.loads(path.read_text())["@graph"]


def listed(value) -> list:
    if value is None:
        return []
    return list(value) if isinstance(value, list) else [value]


def bare(identifier: str) -> str:
    """`tdoc:R3-204999` · `tdoc:crpack/RP-181238` 의 문서 번호 부분."""
    return re.sub(r"^.*[/:]", "", identifier)


def input_files(wg: str, phase2_root: Path | None, phase4_root: Path | None) -> dict[str, list[Path]]:
    """읽을 입력 파일. phase-2·phase-4 는 `<root>/<WG>/<파일>` 이 있으면 그 파일이 인스턴스 파일을 갈음한다."""
    def chosen(phase: str, name: str, root: Path | None) -> Path:
        if root and (root / wg / name).exists():
            return root / wg / name
        return INSTANCES / phase / wg / name

    resolution_names = sorted({path.name for folder in (INSTANCES / "phase-2" / wg, phase2_root / wg if phase2_root else None)
                               if folder and folder.exists() for path in folder.glob("resolutions_*.jsonld")})
    return {"tdocs": [INSTANCES / "phase-1" / wg / "tdocs.jsonld"],
            "meetings": [INSTANCES / "phase-1" / wg / "meetings.jsonld"],
            "resolutions": [chosen("phase-2", name, phase2_root) for name in resolution_names],
            "dispositions": [chosen("phase-2", "decision_dispositions.jsonld", phase2_root)],
            "crExtensions": [chosen("phase-4", "cr_extensions.jsonld", phase4_root)],
            "crPacks": [chosen("phase-4", "crpacks.jsonld", phase4_root)]}


GLYPH_SEPARATORS = {WORD + "noBreakHyphen": "-", **{WORD + name: " " for name in ("tab", "ptab", "br", "cr", "sym")}}


def paragraph_numbers(report: Path) -> set[str]:
    """보고서 docx 의 word/*.xml 에서 문단마다 w:t 글을 이어 뽑은 숫자열. 안쪽 문단이 시작·끝나는 곳도 경계로 둔다."""
    found: set[str] = set()
    with zipfile.ZipFile(report) as archive:
        for name in archive.namelist():
            if not (name.startswith("word/") and name.endswith(".xml")):
                continue
            pieces: list[str] = []
            with archive.open(name) as stream:
                for event, element in ET.iterparse(stream, events=("start", "end")):
                    if element.tag == WORD + "p":
                        found.update(re.findall(r"[0-9]+", "".join(pieces)))
                        pieces = []
                    elif event == "end" and element.tag == WORD + "t":
                        pieces.append(element.text or "")
                    elif event == "start" and element.tag in GLYPH_SEPARATORS:
                        pieces.append(GLYPH_SEPARATORS[element.tag])
                    if event == "end":
                        element.clear()
            found.update(re.findall(r"[0-9]+", "".join(pieces)))
    return found


def load(wg: str, files: dict[str, list[Path]], reports: list[Path]) -> sqlite3.Connection:
    db = sqlite3.connect(":memory:", isolation_level=None)
    db.executescript(SCHEMA)
    rows = []
    revisions = []
    for r in records(files["tdocs"][0]):
        if "tdoc:tdocNumber" not in r:
            continue
        raw = str(r.get("tdoc:crNumber") or "").strip()
        cr = str(int(raw)) if re.fullmatch(r"[0-9]+", raw) else (raw or None)
        target = r.get("modifies")
        match = re.search(r"spec/([^/]+)$", target) if isinstance(target, str) else None
        rows.append((r["@id"], r["tdoc:tdocNumber"], r.get("@type"), cr, raw, match.group(1).replace("_", ".") if match else None,
                     str(r.get("tdoc:status") or "").strip().lower(), str(r.get("tdoc:tsgCRPack") or "").strip(),
                     r["presentedAt"] if isinstance(r.get("presentedAt"), str) else None))
        revisions += [(earlier, r["@id"]) for earlier in listed(r.get("isRevisionOf"))]
        revisions += [(r["@id"], later) for later in listed(r.get("revisedTo"))]
    db.executemany("INSERT INTO doc VALUES (?,?,?,?,?,?,?,?,?)", rows)
    db.executemany("INSERT OR IGNORE INTO revision VALUES (?,?)", revisions)
    meetings = []
    for r in records(files["meetings"][0]):
        match = re.search(r"#(\d+)(b)?", str(r.get("tdoc:meetingNumber") or ""))
        if match:
            meetings.append((r["@id"], r["tdoc:meetingNumber"], int(match.group(1)), int(bool(match.group(2)))))
    db.executemany("INSERT INTO meeting VALUES (?,?,?,?)", meetings)
    made_at = {r["@id"]: r["madeAt"] for path in files["resolutions"] for r in records(path) if r.get("madeAt")}
    dispositions = []
    for r in records(files["dispositions"][0]):
        method = r.get("assessmentMethod")
        method = json.loads(method) if isinstance(method, str) else (method or {})
        meeting = made_at.get(r.get("dispositionOf"))
        usable = r.get("evidenceStatus") == "source_verified" and method.get("scope") == "whole_target" and bool(meeting)
        dispositions.append((r["@id"], r["dispositionTarget"], r["dispositionCode"], int(usable), meeting,
                             r.get("dispositionId"), r.get("evidencePath"), r.get("evidenceSha256"),
                             json.dumps(r.get("evidenceLocator"), sort_keys=True)))
    db.executemany("INSERT INTO disp VALUES (?,?,?,?,?,?,?,?,?)", dispositions)
    for r in records(files["crPacks"][0]):
        db.execute("INSERT INTO pack VALUES (?,?,?)", (r["@id"], r["tdoc:crPackId"], r["tdoc:tsgMeeting"]))
        db.executemany("INSERT OR IGNORE INTO member VALUES (?,?)", [(r["@id"], cr) for cr in listed(r.get("hasCR"))])
    db.executemany("INSERT OR IGNORE INTO member_fwd VALUES (?,?)",
                   [(r["@id"], pack) for r in records(files["crExtensions"][0]) for pack in listed(r.get("belongsToCRPack"))])
    numbers: set[str] = set()
    for report in reports:
        numbers |= paragraph_numbers(report)
    db.executemany("INSERT INTO mention VALUES (?)", [(n,) for n in numbers])
    return db


def gated_numbers(paths: list[Path]) -> set[str]:
    """채택 문항 파일에 기준 문서·근거 문서·정답 칸으로 나온 문서 번호."""
    numbers = set()
    for path in paths:
        for line in path.read_text().splitlines():
            item = json.loads(line)
            numbers.add(bare(item["anchor"]))
            numbers.update(source["document"] for source in item.get("evidence", []) if source.get("document"))
            numbers.update(str(cell).strip() for row in item["gold"] for cell in row)
    return numbers


@dataclasses.dataclass
class Coverage:
    keys: dict[str, tuple[int, int]]
    labels: dict[str, str]
    agreed: collections.Counter
    packed: collections.Counter
    low: tuple[int, int]
    high: tuple[int, int]

    def outside(self, meeting: str) -> bool:
        return meeting in self.keys and not self.low <= self.keys[meeting] <= self.high

    def period(self) -> list[str]:
        """덮는 기간의 처음과 끝 회의 이름."""
        ends = sorted((self.keys[m], self.labels[m]) for m, n in self.packed.items() if n and m in self.keys)
        return [ends[0][1], ends[-1][1]]


def coverage(db: sqlite3.Connection) -> Coverage:
    """agreed 로 승인한 CR 이 묶음 기록에 실린 작업반 회의의 차례 범위와 회의마다의 승인·실림 수."""
    keys = {m: (num, bis) for m, num, bis in db.execute("SELECT id, num, bis FROM meeting")}
    labels = dict(db.execute("SELECT id, label FROM meeting"))
    agreed, packed = collections.Counter(), collections.Counter()
    for meeting, is_packed in db.execute("""
            SELECT d.meeting, EXISTS (SELECT 1 FROM member m WHERE m.cr = d.target)
                              OR EXISTS (SELECT 1 FROM member_fwd f WHERE f.cr = d.target)
            FROM disp d JOIN doc c ON c.id = d.target
            WHERE d.usable = 1 AND d.code = 'agreed' AND c.type = 'tdoc:CR' AND c.cr IS NOT NULL AND c.spec IS NOT NULL
            GROUP BY d.meeting, d.target"""):
        agreed[meeting] += 1
        packed[meeting] += int(bool(is_packed))
    covered = [keys[m] for m, n in packed.items() if n and m in keys]
    return Coverage(keys, labels, agreed, packed, min(covered), max(covered))


@dataclasses.dataclass
class Context:
    wg: str
    gated: set[str]
    cover: Coverage
    form: str
    reports: int


def column(db: sqlite3.Connection, sql: str, *args) -> list:
    return [row[0] for row in db.execute(sql, args)]


def packs_of(db: sqlite3.Connection, identifier: str) -> tuple[set[str], set[str]]:
    return (set(column(db, "SELECT pack FROM member_fwd WHERE cr = ?", identifier)),
            set(column(db, "SELECT pack FROM member WHERE cr = ?", identifier)))


def usable_decisions(db: sqlite3.Connection, identifier: str) -> list[tuple]:
    return db.execute("SELECT code, meeting, did, path, sha, locator FROM disp WHERE target = ? AND usable = 1",
                      (identifier,)).fetchall()


def unverified(db: sqlite3.Connection, identifier: str) -> int:
    return db.execute("SELECT count(*) FROM disp WHERE target = ? AND usable = 0", (identifier,)).fetchone()[0]


def judge(db: sqlite3.Connection, identifier: str, ctx: Context) -> dict:
    """질문의 판정 차례로 구한 갈래·근거·정답과, 답을 하나로 정하는 조건에서 걸린 문제."""
    row = db.execute("""SELECT number, type, cr, cr_raw, spec, status, pack_col, presented,
                                 (SELECT label FROM meeting WHERE meeting.id = doc.presented)
                          FROM doc WHERE id = ?""", (identifier,)).fetchone()
    if row is None:
        return {"class": None, "problems": ["anchor_not_in_document_list"], "gated": False}
    number, kind, cr, cr_raw, spec, status, pack_col, presented, presented_label = row
    problems = []
    if kind != "tdoc:CR" or cr is None or spec is None:
        problems.append("not_a_numbered_change_request")
    to_pack, from_pack = packs_of(db, identifier)
    if to_pack != from_pack:
        problems.append("pack_directions_disagree")
    packs = to_pack | from_pack
    gold_packs = sorted(db.execute(f"SELECT number, tsg FROM pack WHERE id IN ({','.join('?' * len(packs))})", sorted(packs))) if packs else []
    if len(gold_packs) != len(packs):
        problems.append("pack_record_missing")
    named = {n for n, _ in gold_packs}
    if pack_col and pack_col not in named:
        problems.append("document_list_pack_column_disagrees")
    siblings = db.execute("SELECT id, pack_col FROM doc WHERE cr = ? AND spec = ? AND id <> ?",
                          (cr, spec, identifier)).fetchall() if cr is not None and spec is not None else []
    for other, other_col in siblings:
        if set().union(*packs_of(db, other)) - packs or other_col not in named | {"", "-"}:
            problems.append("same_cr_identity_packed_outside_gold")
            break
    decided = usable_decisions(db, identifier)
    codes = {code for code, *_ in decided}
    pending = unverified(db, identifier)
    if packs:
        verdict, gold = "answer", [tuple(p) for p in gold_packs]
        basis = BASIS["answer"]
        if (codes and codes <= CLOSING_CODES) or status in set(CLOSING_WORDS):
            problems.append("pack_record_conflicts_with_closure")
    elif codes and codes <= CLOSING_CODES:
        verdict, gold, basis = "none", [], BASIS["none"]
        if pending:
            problems.append("unverified_or_partial_decision_record")
        if status not in NONE_STATUS:
            problems.append("document_list_status_conflicts")
        if any(Path(path).parent != MEETINGS / ctx.wg / "Final_Report" for _, _, _, path, _, _ in decided):
            problems.append("closing_record_not_from_wg_meeting_report")
        later = set(column(db, """
            WITH RECURSIVE chain(id) AS (
                SELECT later FROM revision WHERE earlier = :x
                UNION SELECT r.later FROM revision r JOIN chain ON r.earlier = chain.id)
            SELECT id FROM chain WHERE id <> :x""", identifier))
        if any(set().union(*packs_of(db, other)) or column(db, "SELECT 1 FROM doc WHERE id = ? AND pack_col <> ''", other)
               for other in later):
            problems.append("later_revision_packed")
        for other in later | {other for other, _ in siblings}:
            other_codes = {code for code, *_ in usable_decisions(db, other)}
            if unverified(db, other) or not other_codes or other_codes - SETTLED_CODES:
                problems.append("same_cr_or_later_revision_not_settled")
                break
    else:
        verdict, gold = "insufficient", [(TOKEN, TOKEN)]
        if column(db, "SELECT 1 FROM revision WHERE earlier = ?", identifier):
            problems.append("has_later_revision")
        if codes == {"agreed"}:
            basis = BASIS["gap"]
            if pending:
                problems.append("unverified_or_partial_decision_record")
            if status not in AGREED_STATUS:
                problems.append("document_list_status_conflicts")
            if not all(ctx.cover.outside(meeting) for _, meeting, *_ in decided):
                problems.append("insufficiency_basis_not_supported")
            if any(unverified(db, other) or any(code in APPROVING_CODES and not ctx.cover.outside(meeting)
                                                for code, meeting, *_ in usable_decisions(db, other))
                   for other, _ in siblings):
                problems.append("same_cr_not_consistent_with_basis")
        elif not codes:
            basis = BASIS["silent"]
            if pending:
                problems.append("unverified_or_partial_decision_record")
            if status not in SILENT_STATUS:
                problems.append("document_list_status_conflicts")
            digits = re.search(r"([0-9]+)$", number)
            if not digits or column(db, "SELECT 1 FROM mention WHERE digits = ?", digits.group(1)):
                problems.append("insufficiency_basis_not_supported")
            if any(column(db, "SELECT 1 FROM disp WHERE target = ? LIMIT 1", other) for other, _ in siblings):
                problems.append("same_cr_not_consistent_with_basis")
        else:
            basis = BASIS["other"]
            problems.append("insufficiency_basis_not_supported")
    order = sorted(decided, key=lambda d: (ctx.cover.keys.get(d[1], (0, 0)), d[2] or ""))
    return {"class": verdict, "basis": basis, "gold": sorted(gold), "problems": problems, "gated": number in ctx.gated,
            "number": number, "cr_raw": cr_raw, "spec": spec, "status": status, "pack_col": pack_col,
            "presented": presented_label if presented else None, "decisions": order}


def anchor_phrase(verdict: dict) -> str:
    return f"change request {verdict['number']} (CR {verdict['cr_raw']} to TS {verdict['spec']})"


def placeholder_form(question: str, verdict: dict, wg: str) -> str:
    return question.replace(anchor_phrase(verdict), ANCHOR_PLACEHOLDER).replace(wg, "{wg}")


def filled(form: str, verdict: dict, wg: str) -> str:
    return (form.replace(ANCHOR_PLACEHOLDER, anchor_phrase(verdict)).replace("{wg}", wg))


def evidence_of(verdict: dict, cover: Coverage) -> list[dict]:
    return [{"document": verdict["number"], "disposition": code, "wgMeeting": cover.labels.get(meeting),
             "dispositionId": did, "path": path, "sha256": sha, "locator": json.loads(locator)}
            for code, meeting, did, path, sha, locator in verdict["decisions"]]


def support_of(verdict: dict, ctx: Context) -> dict:
    support = {"documentListStatus": verdict["status"], "documentListPackColumn": verdict["pack_col"],
               "presentedAt": verdict["presented"]}
    if verdict["basis"] == BASIS["gap"]:
        support["agreedAt"] = [{"wgMeeting": ctx.cover.labels.get(meeting), "agreedCRs": ctx.cover.agreed[meeting],
                                "agreedCRsInPackRecords": ctx.cover.packed[meeting]} for _, meeting, *_ in verdict["decisions"]]
        support["packRecordPeriod"] = ctx.cover.period()
    if verdict["basis"] == BASIS["silent"]:
        support["reportsScanned"] = ctx.reports
    return support


def build_item(identifier: str, verdict: dict, ctx: Context) -> dict:
    """이 검사의 판정만으로 만든 문항. 뽑히지 않은 근거의 대조 대상과 바꿔 넣기 대조에 쓴다."""
    return {"id": f"{ctx.wg}-{TEMPLATE}-{verdict['number']}", "wg": ctx.wg, "family": f"{TEMPLATE}_{verdict['class']}",
            "template": TEMPLATE, "answerClass": verdict["class"], "basis": verdict["basis"], "hops": 1, "anchor": identifier,
            "question": filled(ctx.form, verdict, ctx.wg), "fields": list(FIELDS), "gold": [list(r) for r in verdict["gold"]],
            "expectsEmpty": verdict["class"] == "none", "evidence": evidence_of(verdict, ctx.cover),
            "support": support_of(verdict, ctx)}


def evidence_key(entry: dict) -> tuple:
    return (entry.get("document"), entry.get("disposition"), entry.get("wgMeeting"), entry.get("dispositionId"),
            entry.get("path"), entry.get("sha256"), json.dumps(entry.get("locator"), sort_keys=True))


def check_item(db: sqlite3.Connection, item: dict, ctx: Context) -> list[str]:
    failures = []
    if item.get("wg") != ctx.wg:
        failures.append("wg_differs")
    if item.get("template") != TEMPLATE:
        failures.append("template_differs")
    if item.get("hops") != 1:
        failures.append("hops_differs")
    if item.get("fields") != FIELDS:
        failures.append("fields_differ")
    verdict = judge(db, item.get("anchor", ""), ctx)
    failures += verdict["problems"]
    if verdict["gated"]:
        failures.append("anchor_in_gated_items")
    if verdict["class"] is None:
        return failures
    if item.get("id") != f"{ctx.wg}-{TEMPLATE}-{verdict['number']}":
        failures.append("id_not_class_neutral")
    question = str(item.get("question", ""))
    if anchor_phrase(verdict) not in question:
        failures.append("question_does_not_name_anchor")
    if placeholder_form(question, verdict, ctx.wg) != ctx.form:
        failures.append("question_not_shared_template")
    if item.get("answerClass") != verdict["class"]:
        failures.append("answer_class_differs")
    if item.get("family") != f"{TEMPLATE}_{item.get('answerClass')}":
        failures.append("family_differs_from_class")
    if item.get("basis") != verdict["basis"]:
        failures.append("basis_label_differs")
    if item.get("expectsEmpty") is not (verdict["class"] == "none"):
        failures.append("expects_empty_differs")
    gold = item.get("gold") or []
    if any(len(row) != len(FIELDS) for row in gold):
        failures.append("row_width_differs_from_requested_fields")
    if sorted(tuple(row) for row in gold) != verdict["gold"]:
        failures.append("gold_differs_from_independent_derivation")
    evidence = item.get("evidence") or []
    if any(not entry.get("path") or not Path(entry["path"]).exists() or file_sha(Path(entry["path"])) != entry.get("sha256")
           for entry in evidence):
        failures.append("evidence_source_changed")
    if sorted(map(evidence_key, evidence)) != sorted(map(evidence_key, evidence_of(verdict, ctx.cover))):
        failures.append("evidence_differs_from_anchor_decisions")
    support = item.get("support") or {}
    expected = support_of(verdict, ctx)

    def meetings(entries) -> list[str]:
        return sorted(json.dumps(entry, sort_keys=True) for entry in entries or [])

    if any(support.get(key) != value for key, value in expected.items() if key != "agreedAt") \
            or meetings(support.get("agreedAt")) != meetings(expected.get("agreedAt")):
        failures.append("support_differs")
    # 위 검사가 보지 않는 칸이 남지 않도록, 이 검사의 판정만으로 만든 문항과 통째로도 맞댄다.
    if json.dumps(item, sort_keys=True) != json.dumps(build_item(item["anchor"], verdict, ctx), sort_keys=True):
        failures.append("item_differs_from_independent_build")
    return list(dict.fromkeys(failures))


def template_failures(form: str) -> list[str]:
    failures = [f"template_lacks:{phrase}" for phrase in REQUIRED_PHRASES if phrase not in form]
    listed_words = re.search(r"without approval \(([^()]*)\)", form)
    words = re.split(r", | or ", listed_words.group(1)) if listed_words else []
    if sorted(words) != sorted(CLOSING_WORDS):
        failures.append("template_closing_words_differ")
    return failures


@dataclasses.dataclass
class Population:
    pools: dict[str, list[str]]
    before: collections.Counter
    by_basis: collections.Counter
    before_basis: collections.Counter
    problems: collections.Counter
    gated_clean: dict[str, list[str]]
    basis_of: dict[str, str]
    change_requests: int


def population(db: sqlite3.Connection, ctx: Context) -> Population:
    pools: dict[str, list[str]] = {c: [] for c in CLASSES}
    before, by_basis, before_basis, problems = (collections.Counter() for _ in range(4))
    gated_clean: dict[str, list[str]] = collections.defaultdict(list)
    basis_of = {}
    identifiers = sorted(column(db, "SELECT id FROM doc WHERE type = 'tdoc:CR'"))
    for identifier in identifiers:
        verdict = judge(db, identifier, ctx)
        if verdict["problems"]:
            problems.update(set(verdict["problems"]))
            continue
        before[verdict["class"]] += 1
        before_basis[verdict["basis"]] += 1
        if verdict["gated"]:
            gated_clean[verdict["class"]].append(identifier)
            continue
        pools[verdict["class"]].append(identifier)
        by_basis[verdict["basis"]] += 1
        basis_of[identifier] = verdict["basis"]
    return Population(pools, before, by_basis, before_basis, problems, dict(gated_clean), basis_of, len(identifiers))


def drawn(pool: list[str], seed: int, wg: str, answer_class: str, per_class: int) -> list[str]:
    return sorted(random.Random(f"{seed}:{wg}:{answer_class}").sample(pool, min(per_class, len(pool))))


def check_set(items: list[dict], summary: dict, pop: Population, ctx: Context, observed: dict) -> list[str]:
    failures = []
    if summary.get("wg") != ctx.wg or summary.get("template") != TEMPLATE:
        failures.append("summary_scope_differs")
    for key in ("inputs", "reportsScanned", "excludeItems"):
        if {e["path"]: e["sha256"] for e in summary.get(key, [])} != observed[key]:
            failures.append(f"{key}_hash_differs")
    if summary.get("changeRequests") != pop.change_requests:
        failures.append("change_request_count_differs")
    mine = {"population": {c: len(pop.pools[c]) for c in CLASSES},
            "populationBeforeExcludingCurrentItems": {c: pop.before[c] for c in CLASSES},
            "populationByBasis": dict(pop.by_basis),
            "populationByBasisBeforeExcludingCurrentItems": dict(pop.before_basis)}
    for key, value in mine.items():
        if {k: v for k, v in summary.get(key, {}).items() if v} != {k: v for k, v in value.items() if v}:
            failures.append("population_differs_from_summary")
            break
    period = summary.get("packRecordPeriod", {})
    names = {label: key for key, label in ((ctx.cover.keys.get(m), lab) for m, lab in ctx.cover.labels.items())}
    outside = sorted((ctx.cover.labels[m], n) for m, n in ctx.cover.agreed.items() if ctx.cover.outside(m))
    if [names.get(period.get("firstWgMeeting")), names.get(period.get("lastWgMeeting"))] != [ctx.cover.low, ctx.cover.high] \
            or sorted((e["wgMeeting"], e["agreedCRs"]) for e in period.get("meetingsOutside", [])) != outside:
        failures.append("pack_record_period_differs")
    ids = [item.get("id") for item in items]
    anchors = [item.get("anchor") for item in items]
    if len(set(ids)) != len(ids) or len(set(anchors)) != len(anchors):
        failures.append("duplicate_item")
    seed, per_class = summary.get("seed"), summary.get("perClass")
    for answer_class in CLASSES:
        chosen = sorted(item.get("anchor") for item in items if item.get("answerClass") == answer_class)
        if chosen != drawn(pop.pools[answer_class], seed, ctx.wg, answer_class, per_class):
            failures.append("seeded_draw_not_reproduced")
            break
    if summary.get("itemsByClass") != dict(collections.Counter(item.get("answerClass") for item in items)) \
            or summary.get("items") != len(items):
        failures.append("item_counts_differ")
    return failures + template_failures(ctx.form)


# 대조: (이름, 기대 실패 사유, 대상 조건, 바꾸기). 바꾸기는 (문항 사본, db, 문맥, 바꿔 넣을 문서 찾기)를 받는다.
GOLD = "gold_differs_from_independent_derivation"


def first_decision_meeting(db, item) -> str | None:
    rows = column(db, "SELECT meeting FROM disp WHERE target = ? AND usable = 1 ORDER BY did", item["anchor"])
    return rows[0] if rows else None


def link(db, identifier: str, pack: str) -> None:
    db.execute("INSERT OR IGNORE INTO member VALUES (?,?)", (pack, identifier))
    db.execute("INSERT OR IGNORE INTO member_fwd VALUES (?,?)", (identifier, pack))


def fake_pack(db) -> str:
    db.execute("INSERT OR IGNORE INTO pack VALUES (?,?,?)", FAKE_PACK)
    return FAKE_PACK[0]


def add_doc(db, identifier: str, cr: str, spec: str, pack_col: str = "") -> None:
    db.execute("INSERT INTO doc VALUES (?,?,?,?,?,?,?,?,NULL)",
               (identifier, bare(identifier), "tdoc:CR", cr, cr, spec, "", pack_col))


def doc_identity(db, identifier: str) -> tuple[str, str]:
    return db.execute("SELECT cr, spec FROM doc WHERE id = ?", (identifier,)).fetchone()


def an_existing_pack(db) -> str:
    return column(db, "SELECT id FROM pack ORDER BY id LIMIT 1")[0]


def recode_or_insert_closure(db, item) -> None:
    if item["basis"] == BASIS["gap"]:
        db.execute("UPDATE disp SET code = 'withdrawn' WHERE target = ? AND usable = 1", (item["anchor"],))
    else:
        meeting = column(db, "SELECT id FROM meeting ORDER BY num, bis LIMIT 1")[0]
        db.execute("INSERT INTO disp VALUES ('control', ?, 'withdrawn', 1, ?, 'control', ?, ?, '\"control\"')",
                   (item["anchor"], meeting, str(MEETINGS / item["wg"] / "Final_Report" / "control.docx"), FAKE_SHA))


def packed_agreed_at_gap_meeting(db, item) -> None:
    add_doc(db, "tdoc:CONTROL-agreed-packed", "CONTROL", "CONTROL")
    db.execute("INSERT INTO disp VALUES ('control', 'tdoc:CONTROL-agreed-packed', 'agreed', 1, ?, 'control', '', '', 'null')",
               (first_decision_meeting(db, item),))
    link(db, "tdoc:CONTROL-agreed-packed", an_existing_pack(db))


def packed_sibling(db, item) -> None:
    cr, spec = doc_identity(db, item["anchor"])
    add_doc(db, "tdoc:CONTROL-sibling", cr, spec)
    link(db, "tdoc:CONTROL-sibling", fake_pack(db))


def later_revision(db, item, packed: bool) -> None:
    cr, spec = doc_identity(db, item["anchor"])
    add_doc(db, "tdoc:CONTROL-later", cr, spec)
    db.execute("INSERT INTO revision VALUES (?, 'tdoc:CONTROL-later')", (item["anchor"],))
    if packed:
        link(db, "tdoc:CONTROL-later", an_existing_pack(db))


def tamper_sha(db, item) -> None:
    db.execute("UPDATE disp SET sha = ? WHERE target = ? AND usable = 1", (FAKE_SHA, item["anchor"]))
    for entry in item["evidence"]:
        entry["sha256"] = FAKE_SHA


def other_family(item) -> str:
    return f"{TEMPLATE}_{next(c for c in CLASSES if c != item['answerClass'])}"


A, E, U = {"answer"}, {"none"}, {"insufficient"}
ALL = A | E | U
ITEM_CONTROLS = [
    # (이름, 기대 사유, 갈래, 근거 조건, 문항 바꾸기)
    ("alter_pack", GOLD, A, None, lambda it: it["gold"][0].__setitem__(0, "RP-000000")),
    ("empty_answer", GOLD, A | U, None, lambda it: it.__setitem__("gold", [])),
    ("token_answer", GOLD, A | E, None, lambda it: it.__setitem__("gold", [[TOKEN, TOKEN]])),
    ("narrow_token", "row_width_differs_from_requested_fields", U, None, lambda it: it.__setitem__("gold", [[TOKEN]])),
    ("drop_evidence", "evidence_differs_from_anchor_decisions", ALL, "evidence", lambda it: it["evidence"].pop()),
    ("leak_id", "id_not_class_neutral", ALL, None,
     lambda it: it.__setitem__("id", it["id"].replace(f"-{TEMPLATE}-", f"-{TEMPLATE}_{it['answerClass']}-"))),
    ("reword_question", "question_not_shared_template", ALL, None,
     lambda it: it.__setitem__("question", PACK_LOOKUP_QUESTION.format(
         doc=bare(it["anchor"]), **re.search(r"\(CR (?P<cr>.+?) to TS (?P<spec>[^)]+)\)", it["question"]).groupdict()))),
    ("family_mismatch", "family_differs_from_class", ALL, None, lambda it: it.__setitem__("family", other_family(it))),
    ("basis_mislabel", "basis_label_differs", ALL, None,
     lambda it: it.__setitem__("basis", BASIS["silent"] if it["basis"] != BASIS["silent"] else BASIS["gap"])),
    ("expects_empty_flip", "expects_empty_differs", ALL, None, lambda it: it.__setitem__("expectsEmpty", not it["expectsEmpty"])),
]
RECORD_CONTROLS = [
    ("add_pack_member", GOLD, E | U, None, lambda db, it: link(db, it["anchor"], an_existing_pack(db))),
    ("closure_recorded", GOLD, U, None, recode_or_insert_closure),
    ("add_packed_sibling", "same_cr_identity_packed_outside_gold", ALL, None, packed_sibling),
    ("add_report_mention", "insufficiency_basis_not_supported", U, BASIS["silent"],
     lambda db, it: db.execute("INSERT OR IGNORE INTO mention VALUES (?)", (re.search(r"([0-9]+)$", bare(it["anchor"])).group(1),))),
    ("pack_agreed_at_gap_meeting", "insufficiency_basis_not_supported", U, BASIS["gap"], packed_agreed_at_gap_meeting),
    ("add_pending_record", "unverified_or_partial_decision_record", E | U, None,
     lambda db, it: db.execute("INSERT INTO disp VALUES ('control', ?, 'postponed', 0, NULL, 'control', '', '', 'null')", (it["anchor"],))),
    ("list_status_conflict", "document_list_status_conflicts", E | U, None,
     lambda db, it: db.execute("UPDATE doc SET status = ? WHERE id = ?",
                               ("agreed" if it["answerClass"] == "none" else "withdrawn", it["anchor"]))),
    ("list_status_closed_on_packed", "pack_record_conflicts_with_closure", A, None,
     lambda db, it: db.execute("UPDATE doc SET status = 'withdrawn' WHERE id = ?", (it["anchor"],))),
    ("pack_column_conflict", "document_list_pack_column_disagrees", ALL, None,
     lambda db, it: db.execute("UPDATE doc SET pack_col = 'RP-000000' WHERE id = ?", (it["anchor"],))),
    ("unrecorded_later_revision", {"none": "same_cr_or_later_revision_not_settled", "insufficient": "has_later_revision"},
     E | U, None, lambda db, it: later_revision(db, it, packed=False)),
    ("packed_later_revision", "later_revision_packed", E, None, lambda db, it: later_revision(db, it, packed=True)),
    ("one_direction_pack_record", "pack_directions_disagree", ALL, None,
     lambda db, it: db.execute("INSERT OR IGNORE INTO member_fwd VALUES (?,?)", (it["anchor"], fake_pack(db)))),
    ("bad_sha", "evidence_source_changed", ALL, "evidence", None),
]
SWAP_CONTROLS = [
    # (이름, 기대 사유, 갈래, 바꿔 넣을 문서의 모집단)
    ("swap_to_packed", GOLD, E | U, "answer"),
    ("swap_to_closed", GOLD, A | U, "none"),
    ("swap_to_gap", GOLD, A | E, "gap"),
    ("swap_to_gated", "anchor_in_gated_items", ALL, "gated"),
]


def outcome(failures: list[str], expected: str) -> str:
    if not failures:
        return "admitted"
    return "caught_for_expected_reason" if expected in failures else "caught_for_other_reason"


def applies(item: dict, classes: set[str], condition: str | None) -> bool:
    if item["answerClass"] not in classes:
        return False
    if condition == "evidence":
        return bool(item.get("evidence"))
    return condition is None or item["basis"] == condition


def run_controls(db, targets: list[dict], ctx: Context, pop: Population, seed: int, verdicts: dict) -> dict:
    tally: dict[str, dict] = {}
    anchors = {item["anchor"] for item in targets}

    def record(name, expected_of, item, failures):
        expected = expected_of[item["answerClass"]] if isinstance(expected_of, dict) else expected_of
        entry = tally.setdefault(name, {"expected": expected_of, **{k: 0 for k in (
            "caught_for_expected_reason", "caught_for_other_reason", "admitted", "not_applicable")}, "otherReasons": {}})
        result = outcome(failures, expected)
        entry[result] += 1
        if result != "caught_for_expected_reason":
            entry["otherReasons"][item["id"]] = failures

    def skip(name, expected_of):
        tally.setdefault(name, {"expected": expected_of, **{k: 0 for k in (
            "caught_for_expected_reason", "caught_for_other_reason", "admitted", "not_applicable")}, "otherReasons": {}})
        tally[name]["not_applicable"] += 1

    def under(change, item):
        db.execute("SAVEPOINT control")
        try:
            change(db, item)
            return check_item(db, item, dataclasses.replace(ctx, cover=coverage(db)))
        finally:
            db.execute("ROLLBACK TO control")
            db.execute("RELEASE control")

    swap_pools = {"answer": pop.pools["answer"], "none": pop.pools["none"],
                  "gap": [i for i in pop.pools["insufficient"] if pop.basis_of[i] == BASIS["gap"]]}
    for item in targets:
        for name, expected, classes, condition, change in ITEM_CONTROLS:
            if not applies(item, classes, condition):
                skip(name, expected)
                continue
            copied = copy.deepcopy(item)
            change(copied)
            record(name, expected, item, check_item(db, copied, ctx))
        for name, expected, classes, condition, change in RECORD_CONTROLS:
            if not applies(item, classes, condition):
                skip(name, expected)
                continue
            copied = copy.deepcopy(item)
            if name == "bad_sha":
                record(name, expected, item, under(lambda d, _it: tamper_sha(d, copied), copied))
            else:
                record(name, expected, item, under(change, copied))
        for name, expected, classes, source in SWAP_CONTROLS:
            if not applies(item, classes, None):
                skip(name, expected)
                continue
            if source == "gated":
                candidates = sorted(pop.gated_clean.get(item["answerClass"], []) or
                                    [i for pool in pop.gated_clean.values() for i in pool])
            else:
                candidates = [i for i in swap_pools[source] if i not in anchors]
            if not candidates:
                skip(name, expected)
                continue
            partner = random.Random(f"{seed}:{ctx.wg}:{name}:{item['id']}").choice(candidates)
            swapped = build_item(partner, verdicts.get(partner) or judge(db, partner, ctx), ctx)
            for key in ("gold", "answerClass", "family", "basis", "expectsEmpty"):
                swapped[key] = copy.deepcopy(item[key])
            record(name, expected, item, check_item(db, swapped, ctx))
    return tally


def set_controls(items: list[dict], summary: dict, pop: Population, ctx: Context, observed: dict, db) -> dict:
    trials = []
    drawn_anchors = {item["anchor"] for item in items}
    for answer_class in CLASSES:
        spare = [i for i in pop.pools[answer_class] if i not in drawn_anchors]
        position = next((n for n, item in enumerate(items) if item["answerClass"] == answer_class), None)
        if spare and position is not None:
            replaced = list(items)
            replaced[position] = build_item(spare[0], judge(db, spare[0], ctx), ctx)
            trials.append(("replace_with_undrawn_pool_doc", "seeded_draw_not_reproduced", replaced, summary,
                           check_item(db, replaced[position], ctx)))
            trials.append(("drop_item", "seeded_draw_not_reproduced", items[:position] + items[position + 1:], summary, []))
        altered = copy.deepcopy(summary)
        altered["population"][answer_class] += 1
        trials.append(("alter_summary_population", "population_differs_from_summary", items, altered, []))
    trials.append(("duplicate_item", "duplicate_item", items + [items[0]], summary, []))
    altered = copy.deepcopy(summary)
    altered["inputs"][0]["sha256"] = FAKE_SHA
    trials.append(("tamper_input_hash", "inputs_hash_differs", items, altered, []))
    tally: dict[str, dict] = {}
    for name, expected, trial_items, trial_summary, item_failures in trials:
        failures = check_set(trial_items, trial_summary, pop, ctx, observed)
        entry = tally.setdefault(name, {"expected": expected, "caught_for_expected_reason": 0, "caught_for_other_reason": 0,
                                        "admitted": 0, "replacementItemFailures": []})
        entry[outcome(failures, expected)] += 1
        if item_failures:
            entry["replacementItemFailures"].append(item_failures)
    return tally


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, required=True)
    parser.add_argument("--summary", type=Path, help="기본값: 문항 파일 옆의 abstention_items_summary.json")
    parser.add_argument("--exclude-items", type=Path, nargs="+", required=True, help="만들 때 준 채택 문항 파일")
    parser.add_argument("--out-dir", type=Path, help="기본값: 문항 파일이 있는 디렉토리")
    parser.add_argument("--phase2-root", type=Path)
    parser.add_argument("--phase4-root", type=Path)
    parser.add_argument("--controls", action="store_true", help="음성 대조도 실행한다")
    args = parser.parse_args()
    if available_gib() < MEMORY_FLOOR_GIB:
        raise SystemExit(f"available memory {available_gib():.1f} GiB is below {MEMORY_FLOOR_GIB} GiB; stopped")
    summary_path = args.summary or args.items.parent / "abstention_items_summary.json"
    out_dir = args.out_dir or args.items.parent
    items = [json.loads(line) for line in args.items.read_text().splitlines()]
    summary = json.loads(summary_path.read_text())
    wg = summary["wg"]
    files = input_files(wg, args.phase2_root, args.phase4_root)
    reports = sorted((MEETINGS / wg / "Final_Report").glob("*.docx"))
    observed = {"inputs": {str(p): file_sha(p) for paths in files.values() for p in paths},
                "reportsScanned": {str(p): file_sha(p) for p in reports},
                "excludeItems": {str(p): file_sha(p) for p in args.exclude_items}}
    db = load(wg, files, reports)
    ctx = Context(wg, gated_numbers(args.exclude_items), coverage(db), "", len(reports))
    verdicts = {item["anchor"]: judge(db, item["anchor"], ctx) for item in items}
    forms = collections.Counter(placeholder_form(item["question"], verdicts[item["anchor"]], wg)
                                for item in items if verdicts[item["anchor"]]["class"])
    ctx.form = forms.most_common(1)[0][0]
    pop = population(db, ctx)
    item_failures = {item["id"]: check_item(db, item, ctx) for item in items}
    set_failures = check_set(items, summary, pop, ctx, observed) + (["items_do_not_share_one_template"] if len(forms) > 1 else [])
    admitted = [item for item in items if not item_failures[item["id"]]]
    result = {
        "wg": wg, "items": str(args.items), "summary": str(summary_path),
        "itemsChecked": len(items), "itemsAdmitted": len(admitted),
        "itemFailures": {key: value for key, value in item_failures.items() if value},
        "setFailures": set_failures,
        "population": {c: len(pop.pools[c]) for c in CLASSES},
        "populationBeforeExcludingCurrentItems": {c: pop.before[c] for c in CLASSES},
        "populationByBasis": dict(pop.by_basis),
        "populationByBasisBeforeExcludingCurrentItems": dict(pop.before_basis),
        "changeRequests": pop.change_requests,
        "changeRequestsWithProblem": dict(sorted(pop.problems.items())),
        "cleanButInCurrentItems": {c: len(v) for c, v in pop.gated_clean.items()},
        "packRecordPeriod": ctx.cover.period(),
        "reportsScanned": len(reports),
        "inputs": [{"path": path, "sha256": sha} for path, sha in observed["inputs"].items()],
    }
    passed = not result["itemFailures"] and not set_failures
    if args.controls:
        drawn_bases = {item["basis"] for item in items}
        extra = []
        for identifier in sorted(i for pool in pop.pools.values() for i in pool):
            if pop.basis_of[identifier] not in drawn_bases:
                extra.append(build_item(identifier, judge(db, identifier, ctx), ctx))
        extra_failures = {item["id"]: check_item(db, item, ctx) for item in extra}
        targets = items + extra
        controls = run_controls(db, targets, ctx, pop, summary["seed"], verdicts)
        whole = set_controls(items, summary, pop, ctx, observed, db)
        result["controlTargets"] = {"drawnItems": len(items), "poolItemsForUndrawnBases": [item["id"] for item in extra],
                                    "poolItemFailuresBeforeControl": {k: v for k, v in extra_failures.items() if v}}
        result["controls"] = controls
        result["setControls"] = whole
        missed = [name for name, entry in {**controls, **whole}.items()
                  if entry["caught_for_other_reason"] or entry["admitted"]]
        result["controlsNotCaughtForExpectedReason"] = missed
        passed = passed and not missed and not result["controlTargets"]["poolItemFailuresBeforeControl"]
    result["result"] = "pass" if passed else "fail"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "abstention_items_verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    (out_dir / "abstention_items_admitted.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in admitted))
    print(json.dumps({key: result[key] for key in ("wg", "result", "itemsChecked", "itemsAdmitted", "setFailures",
                                                   "population", "populationByBasis")}
                     | ({"controlsNotCaughtForExpectedReason": result["controlsNotCaughtForExpectedReason"]}
                        if args.controls else {}), ensure_ascii=False))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
