"""추적 사슬 문항의 구축 통과 검사 (모델 호출 없음).

`build_chain_items.py`가 만든 문항마다 아래 여섯 가지를 확인하고, 모두 통과한 문항만 채택 파일에 쓴다.
1. 정답 재유도: 인스턴스 JSON-LD를 SQLite에 싣고 문항 종류별 SQL로 정답을 다시 구해 행 집합이 같은지 본다.
   생성기는 CR 쪽 기록(`belongsToCRPack`·`modifiesSection`)을 따라가고, 이 검사는 반대쪽 기록
   (`CRPack.hasCR`·`Section.modifiedByCR`)을 쓴다. 두 방향 기록이 어긋난 문항은 여기서 걸린다.
2. 요청 필드: 정답 행의 열 수가 요청 필드 수와 같고, 질문 문장이 요청 필드를 모두 말한다.
3. 근거: 근거로 실은 처분 기록의 원문 파일 SHA-256이 현재 파일과 같다.
4. 빈 정답: 빈 정답 문항은 묶음 행이 없고 처분이 묶음 없이 닫히는 코드뿐이다.
5. 묶음 출처 일치: 문항이 살피는 문서 가운데 문서 목록의 묶음 번호(`tdoc:tsgCRPack`)가 묶음 기록의 소속과 다른
   문서가 없다. 두 출처가 갈리는 문서는 어느 쪽을 읽느냐에 따라 답이 달라지므로 정답을 하나로 정할 수 없다.
6. 같은 CR 의 다른 문서: 문서를 묻는 문항(`pack_lookup`·`pack_lookup_empty`·`disposition_pack`·`full_chain`)의
   질문은 문서 번호와 함께 "CR n to TS s"를 적는다. 같은 규격·CR 번호를 가진 다른 문서가 정답에 없는 묶음에
   실렸으면, 질문이 그 CR 을 가리킨다고 읽은 풀이는 그 묶음을 답하므로 정답을 하나로 정할 수 없다. 묶음 기록과
   문서 목록의 묶음 번호를 모두 본다. CR 번호는 숫자만으로 된 경우 앞의 0을 떼고 맞댄다(`0990`과 `990`).

절 단위 종류(`clause_neighbours`·`first_change`·`previous_pack`)도 같은 검사를 거친다. 1의 SQL 은 같은 반대쪽 기록을
쓰고, 총회 회의의 앞뒤는 `pack_order` 뷰가 `RAN#n` 표기에서 읽은 번호로 정한다. 5에서 살피는 문서는 정답이 묶음
소속에 기대는 문서다(`CONSIDERED_THROUGH_CLAUSES`: 같은 절을 고친 같은 release 의 CR, 묶음이 대상이면 그 묶음에
실린 문서도). 6은 걸지 않는다. `clause_neighbours` 의 질문도 "CR n to TS s"를 적지만 대상 문서의 묶음은 정답에
들지 않는다.

사용: python3 verify_chain_items.py --items <chain_items.jsonl> --out-dir <dir>   (저장소 루트에서 실행)
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sqlite3
from pathlib import Path

INSTANCES = Path("ontology/output/tsg/RAN/formal/instances")
CLOSED_WITHOUT_PACK = ("withdrawn", "not_treated", "not_pursued", "rejected", "not_agreed")
# 질문 문장이 요청 필드를 말하는 표현.
FIELD_PHRASE = {
    "cr_pack": r"CR pack document number", "tsg_meeting": r"TSG RAN meeting",
    "disposition": r"disposition", "wg_meeting": r"RAN\d meeting", "clause": r"clause",
    "final_document": r"each such document", "document": r"(?:each|the) document",
    "specification": r"specification",
}
SECTION = re.compile(r"^tdoc:section/(?P<spec>\d{2}\.\d{3}(?:-\d+)?)-(?P<release>Rel-\d+)-(?P<clause>.+)$")

SQL = {
    "pack_lookup": """
        SELECT m.pack, p.tsg FROM pack_member m JOIN pack p ON p.id = m.pack_id WHERE m.cr = :anchor""",
    "disposition_pack": """
        SELECT d.code, d.meeting, m.pack, p.tsg FROM disposition d
        JOIN pack_member m ON m.cr = d.target JOIN pack p ON p.id = m.pack_id WHERE d.target = :anchor""",
    "full_chain": """
        SELECT d.code, d.meeting, m.pack, p.tsg, s.clause FROM disposition d
        JOIN pack_member m ON m.cr = d.target JOIN pack p ON p.id = m.pack_id
        JOIN section_change s ON s.cr = d.target WHERE d.target = :anchor""",
    "revision_chain": """
        WITH RECURSIVE later(id) AS (
            SELECT later FROM revision WHERE earlier = :anchor
            UNION SELECT r.later FROM revision r JOIN later l ON r.earlier = l.id)
        SELECT doc.number, d.code, m.pack FROM later
        JOIN doc ON doc.id = later.id JOIN disposition d ON d.target = later.id
        JOIN pack_member m ON m.cr = later.id""",
    "clause_history": """
        SELECT doc.number, d.code, d.meeting, m.pack FROM section_change s
        JOIN doc ON doc.id = s.cr JOIN disposition d ON d.target = s.cr
        JOIN pack_member m ON m.cr = s.cr WHERE s.section = :anchor AND doc.release = s.release""",
    "pack_origin": """
        SELECT doc.number, d.code, d.meeting FROM pack_member m
        JOIN doc ON doc.id = m.cr JOIN disposition d ON d.target = m.cr WHERE m.pack_id = :anchor""",
    "clause_neighbours": """
        SELECT s.clause, o.number, d.code, d.meeting, m.pack FROM section_change x
        JOIN doc xd ON xd.id = x.cr AND xd.release = x.release
        JOIN section_change s ON s.section = x.section AND s.cr != x.cr
        JOIN doc o ON o.id = s.cr AND o.release = s.release
        JOIN disposition d ON d.target = s.cr JOIN pack_member m ON m.cr = s.cr WHERE x.cr = :anchor""",
    "first_change": """
        SELECT doc.number, s.spec, s.clause FROM pack_member m JOIN pack_order p ON p.id = m.pack_id
        JOIN doc ON doc.id = m.cr JOIN disposition d ON d.target = m.cr
        JOIN section_change s ON s.cr = m.cr AND s.release = doc.release
        WHERE m.pack_id = :anchor AND NOT EXISTS (
            SELECT 1 FROM section_change e JOIN doc ed ON ed.id = e.cr AND ed.release = e.release
            JOIN pack_member em ON em.cr = e.cr JOIN pack_order ep ON ep.id = em.pack_id
            WHERE e.section = s.section AND ep.tsg_number < p.tsg_number)""",
    "previous_pack": """
        WITH touched AS (
            SELECT DISTINCT s.section, s.spec, s.clause, s.release, p.tsg_number AS t
            FROM pack_member m JOIN pack_order p ON p.id = m.pack_id
            JOIN doc ON doc.id = m.cr JOIN disposition d ON d.target = m.cr
            JOIN section_change s ON s.cr = m.cr AND s.release = doc.release WHERE m.pack_id = :anchor),
        earlier AS (
            SELECT t.section, t.spec, t.clause, em.pack, ep.tsg, ep.tsg_number FROM touched t
            JOIN section_change e ON e.section = t.section JOIN doc ed ON ed.id = e.cr AND ed.release = t.release
            JOIN pack_member em ON em.cr = e.cr JOIN pack_order ep ON ep.id = em.pack_id WHERE ep.tsg_number < t.t)
        SELECT spec, clause, pack, tsg FROM earlier
        WHERE tsg_number = (SELECT max(q.tsg_number) FROM earlier q WHERE q.section = earlier.section)""",
}
SQL["pack_lookup_empty"] = SQL["pack_lookup"]

# 문항 종류별로 정답을 정할 때 살피는 문서.
CONSIDERED = {
    "document": "SELECT :anchor",
    "revision_chain": """
        WITH RECURSIVE later(id) AS (
            SELECT later FROM revision WHERE earlier = :anchor
            UNION SELECT r.later FROM revision r JOIN later l ON r.earlier = l.id)
        SELECT id FROM later""",
    "clause_history": """
        SELECT s.cr FROM section_change s JOIN doc ON doc.id = s.cr
        WHERE s.section = :anchor AND doc.release = s.release""",
    "pack_origin": """
        SELECT cr FROM pack_member WHERE pack_id = :anchor
        UNION SELECT id FROM doc WHERE pack_field = :anchor_local""",
}
# 절 단위 종류에서 정답이 묶음 소속에 기대는 문서: 대상이 자기 release 에서 고친 절을 고친 같은 release 의 다른 CR,
# 묶음이 대상이면 그 묶음에 실린 문서(두 출처)와 그 문서가 자기 release 에서 고친 절을 고친 같은 release 의 CR.
CONSIDERED_THROUGH_CLAUSES = {
    "clause_neighbours": """
        SELECT s.cr FROM section_change x JOIN doc xd ON xd.id = x.cr AND xd.release = x.release
        JOIN section_change s ON s.section = x.section AND s.cr != x.cr
        JOIN doc o ON o.id = s.cr AND o.release = s.release WHERE x.cr = :anchor""",
    "first_change": """
        WITH member(id) AS (
            SELECT cr FROM pack_member WHERE pack_id = :anchor UNION SELECT id FROM doc WHERE pack_field = :anchor_local)
        SELECT id FROM member
        UNION SELECT e.cr FROM member JOIN doc ON doc.id = member.id
        JOIN section_change s ON s.cr = member.id AND s.release = doc.release
        JOIN section_change e ON e.section = s.section JOIN doc ed ON ed.id = e.cr AND ed.release = e.release""",
}
CONSIDERED_THROUGH_CLAUSES["previous_pack"] = CONSIDERED_THROUGH_CLAUSES["first_change"]
PACK_SOURCES_DIFFER = """
    SELECT doc.number FROM doc WHERE doc.id IN ({considered}) AND doc.pack_field GLOB 'RP-[0-9]*'
    AND NOT EXISTS (SELECT 1 FROM pack_member m WHERE m.cr = doc.id AND m.pack = doc.pack_field)"""
# 문서를 묻는 문항에서 정답 행의 묶음 번호 열.
CR_PACK_COLUMN = {"pack_lookup": 0, "pack_lookup_empty": 0, "disposition_pack": 2, "full_chain": 2}
# 문항의 문서와 규격·CR 번호가 같은 다른 문서가 실린 묶음(묶음 기록·문서 목록 두 출처).
SAME_IDENTITY_PACKS = """
    SELECT m.pack FROM doc a JOIN doc o ON o.cr = a.cr AND o.spec = a.spec AND o.id != a.id
    JOIN pack_member m ON m.cr = o.id WHERE a.id = :anchor AND a.cr != '' AND a.spec != ''
    UNION SELECT o.pack_field FROM doc a JOIN doc o ON o.cr = a.cr AND o.spec = a.spec AND o.id != a.id
    WHERE a.id = :anchor AND a.cr != '' AND a.spec != '' AND o.pack_field GLOB 'RP-[0-9]*'"""


def as_list(value) -> list[str]:
    return [] if value is None else value if isinstance(value, list) else [value]


def database(wg: str, phase2_root: Path | None = None, phase4_root: Path | None = None) -> sqlite3.Connection:
    roots = {"phase-2": phase2_root, "phase-4": phase4_root}

    def load(rel: str) -> list:
        path = INSTANCES / rel
        root = roots.get(rel.split("/", 1)[0])
        if root and (root / wg / path.name).exists():
            path = root / wg / path.name
        return json.loads(path.read_text())["@graph"]
    db = sqlite3.connect(":memory:")
    db.executescript("""
        CREATE TABLE doc(id TEXT PRIMARY KEY, number TEXT, release TEXT, pack_field TEXT, cr TEXT, spec TEXT);
        CREATE TABLE revision(earlier TEXT, later TEXT);
        CREATE TABLE disposition(target TEXT, code TEXT, meeting TEXT);
        CREATE TABLE pack(id TEXT PRIMARY KEY, tsg TEXT);
        CREATE TABLE pack_member(cr TEXT, pack_id TEXT, pack TEXT);
        CREATE TABLE section_change(cr TEXT, section TEXT, clause TEXT, release TEXT, spec TEXT);
        CREATE VIEW pack_order AS SELECT id, tsg, CAST(substr(tsg, 5) AS INTEGER) AS tsg_number FROM pack
            WHERE tsg GLOB 'RAN#[0-9]*' AND substr(tsg, 5) NOT GLOB '*[^0-9]*';
    """)
    for record in load(f"phase-1/{wg}/tdocs.jsonld"):
        if "tdoc:tdocNumber" not in record:
            continue
        cr = str(record.get("tdoc:crNumber") or "").strip()
        modifies = record.get("modifies")
        db.execute("INSERT INTO doc VALUES (?, ?, ?, ?, ?, ?)", (record["@id"], record["tdoc:tdocNumber"],
                   str(record.get("targetRelease", "")).rsplit("/", 1)[-1].replace("_", "-"),
                   str(record.get("tdoc:tsgCRPack", "")).strip(),
                   (cr.lstrip("0") or "0") if cr.isdigit() else cr,
                   modifies.rsplit("/", 1)[-1].removeprefix("tdoc:").removeprefix("spec/").replace("_", ".")
                   if isinstance(modifies, str) else ""))
        db.executemany("INSERT INTO revision VALUES (?, ?)",
                       [(earlier, record["@id"]) for earlier in as_list(record.get("isRevisionOf"))])
    made_at = {}
    for path in sorted((INSTANCES / f"phase-2/{wg}").glob("resolutions_*.jsonld")):
        for record in load(f"phase-2/{wg}/{path.name}"):
            if "madeAt" in record:
                made_at[record["@id"]] = record["madeAt"].rsplit("/", 1)[-1].replace("_", "#", 1)
    rows = set()
    for record in load(f"phase-2/{wg}/decision_dispositions.jsonld"):
        if (record["evidenceStatus"] == "source_verified" and record["dispositionOf"] in made_at
                and json.loads(record["assessmentMethod"]).get("scope") == "whole_target"):
            rows.add((record["dispositionTarget"], record["dispositionCode"], made_at[record["dispositionOf"]]))
    db.executemany("INSERT INTO disposition VALUES (?, ?, ?)", sorted(rows))
    for record in load(f"phase-4/{wg}/crpacks.jsonld"):
        db.execute("INSERT INTO pack VALUES (?, ?)", (record["@id"], record["tdoc:tsgMeeting"]))
        db.executemany("INSERT INTO pack_member VALUES (?, ?, ?)",
                       [(cr, record["@id"], record["@id"].rsplit("/", 1)[-1])
                        for cr in dict.fromkeys(as_list(record.get("hasCR")))])
    for record in load(f"phase-4/{wg}/section_extensions.jsonld"):
        match = SECTION.match(record["@id"])
        if match:
            db.executemany("INSERT INTO section_change VALUES (?, ?, ?, ?, ?)",
                           [(cr, record["@id"], match["clause"], match["release"], match["spec"])
                            for cr in dict.fromkeys(as_list(record.get("modifiedByCR")))])
    for table, column in (("revision", "earlier"), ("disposition", "target"), ("pack_member", "cr"),
                          ("pack_member", "pack_id"), ("doc", "pack_field"), ("doc", "cr"),
                          ("section_change", "cr"), ("section_change", "section")):
        db.execute(f"CREATE INDEX {table}_{column} ON {table}({column})")
    # 적재를 확정해 열린 쓰기 트랜잭션을 닫는다. 열려 있으면 `Connection.backup` 으로 사본을 뜰 때
    # 원본이 잠긴 것으로 보여 backup 이 끝나지 않는다(`control_chain_gate.with_packed_sibling`).
    db.commit()
    return db


def check(item: dict, db: sqlite3.Connection, sha_of: dict[str, str]) -> list[str]:
    failures = []
    derived = sorted({tuple(row) for row in db.execute(SQL[item["family"]], {"anchor": item["anchor"]})})
    gold = sorted(tuple(row) for row in item["gold"])
    if derived != gold:
        failures.append("gold_differs_from_independent_derivation")
    if any(len(row) != len(item["fields"]) for row in gold):
        failures.append("row_width_differs_from_requested_fields")
    if any(not re.search(FIELD_PHRASE[field], item["question"]) for field in item["fields"]):
        failures.append("question_does_not_name_a_requested_field")
    for source in item["evidence"]:
        if source["path"] not in sha_of:
            sha_of[source["path"]] = hashlib.sha256(Path(source["path"]).read_bytes()).hexdigest()
        if sha_of[source["path"]] != source["sha256"]:
            failures.append("evidence_source_changed")
            break
    considered = CONSIDERED_THROUGH_CLAUSES.get(item["family"]) or CONSIDERED.get(item["family"], CONSIDERED["document"])
    if db.execute(PACK_SOURCES_DIFFER.format(considered=considered),
                  {"anchor": item["anchor"], "anchor_local": item["anchor"].rsplit("/", 1)[-1]}).fetchone():
        failures.append("document_list_pack_differs_from_pack_record")
    column = CR_PACK_COLUMN.get(item["family"])
    if column is not None:
        named = {row[column] for row in gold}
        if {pack for (pack,) in db.execute(SAME_IDENTITY_PACKS, {"anchor": item["anchor"]})} - named:
            failures.append("same_cr_identity_packed_outside_gold")
    if item["expectsEmpty"]:
        codes = {code for (code,) in db.execute(
            "SELECT code FROM disposition WHERE target = ?", (item["anchor"],))}
        if gold or not codes or not codes <= set(CLOSED_WITHOUT_PACK):
            failures.append("empty_gold_not_supported_by_disposition")
    elif not gold:
        failures.append("unexpected_empty_gold")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--phase2-root", type=Path,
                        help="<root>/<WG>/ 아래에 있는 phase-2 파일을 저장된 인스턴스보다 먼저 읽는다")
    parser.add_argument("--phase4-root", type=Path,
                        help="<root>/<WG>/ 아래에 있는 phase-4 파일을 저장된 인스턴스보다 먼저 읽는다")
    args = parser.parse_args()
    items = [json.loads(line) for line in args.items.read_text().splitlines()]
    databases, sha_of = {}, {}
    admitted, rejected = [], []
    counts: collections.Counter[tuple[str, str, str]] = collections.Counter()
    for item in items:
        if item["wg"] not in databases:
            databases[item["wg"]] = database(item["wg"], args.phase2_root, args.phase4_root)
        failures = check(item, databases[item["wg"]], sha_of)
        counts[(item["wg"], item["family"], "admitted" if not failures else "rejected")] += 1
        (rejected if failures else admitted).append({**item, **({"failures": failures} if failures else {})})
    with (args.out_dir / "chain_items_admitted.jsonl").open("w") as handle:
        for item in admitted:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    report = {"checked": len(items), "admitted": len(admitted), "rejected": len(rejected),
              "sourceFilesHashed": len(sha_of),
              "byCell": [{"wg": wg, "family": family, "result": result, "n": n}
                         for (wg, family, result), n in sorted(counts.items())],
              "rejectedItems": [{"id": item["id"], "failures": item["failures"]} for item in rejected]}
    (args.out_dir / "chain_items_gate.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "byCell"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
