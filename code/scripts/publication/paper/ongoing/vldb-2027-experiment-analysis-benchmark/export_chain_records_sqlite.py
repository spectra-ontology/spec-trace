"""추적 사슬 문항이 쓰는 기록을 인스턴스 JSON-LD에서 SQLite 테이블로 내보낸다 (모델 호출 없음).

작업반마다 DB 파일 하나(`<db-dir>/<WG>.sqlite`)를 만든다. 기록은 걸러 내지 않고 그대로 싣는다.
처분 기록은 근거 상태·범위가 무엇이든 모두 싣고, 묶음 소속과 절 수정은 두 방향 기록을 각각 다른 테이블에 싣는다.
어느 기록을 정답에 쓸지는 이 스크립트가 아니라 질의(`measure_relational_equivalence.py`의 참조 SQL)가 정한다.

테이블
- document(id, number, doc_type, cr_number, spec, target_release, list_status, presented_at, pack_field)
      phase-1 tdocs.jsonld 의 문서. target_release 는 `tdoc:release/Rel_18` 을 `Rel-18` 로 적는다.
- revision(earlier, later)                      문서의 `isRevisionOf`
- meeting(id, label, number_int, wg)            phase-1 meetings.jsonld
- resolution(id, meeting_id)                    phase-2 resolutions_*.jsonld 가운데 `madeAt` 이 있는 기록
- disposition(id, resolution_id, target, code, evidence_status, scope, evidence_path, evidence_sha256)
      phase-2 decision_dispositions.jsonld. scope 는 `assessmentMethod` JSON 의 scope 값
- cr_pack(id, pack_number, tsg_meeting, tsg_number)   phase-4 crpacks.jsonld. tsg_number 는 `RAN#79` 의 79
- cr_in_pack(cr, pack_id)                       CR 쪽 기록 `belongsToCRPack` (cr_extensions.jsonld)
- pack_member(cr, pack_id)                      묶음 쪽 기록 `CRPack.hasCR` (crpacks.jsonld)
- section(id, spec, release, clause)            두 방향 기록에 나온 절 식별자. 식별자 문법에 맞지 않으면 세 칸이 NULL
- cr_modifies_section(cr, section_id)           CR 쪽 기록 `modifiesSection` (cr_extensions.jsonld)
- section_modified_by(cr, section_id)           절 쪽 기록 `Section.modifiedByCR` (section_extensions.jsonld)
      CR 의 대상 release 판 절이 적재되어 있지 않으면 적재기가 다른 판의 같은 번호 절에 잇는다. 그래서
      section.release 와 document.target_release 가 다른 연결이 있다(RAN5 에 많다). 개수는
      `measure_clause_edition_readings.py` 가 센다

입력 파일의 위치는 문항 생성 때와 같다. RAN1~4 의 처분 기록은 `--phase2-root`, RAN5 의 묶음·절 기록은
`--phase4-root` 아래의 같은 이름 파일을 저장된 인스턴스보다 먼저 읽는다.

큰 파일은 하나씩 차례로 읽고, 파일을 읽기 전마다 가용 메모리를 확인해 `--min-available-gib` 미만이면 멈춘다.

사용: python3 export_chain_records_sqlite.py --wg RAN1 RAN2 --db-dir <dir> --min-available-gib 10 \
          [--phase2-root <dir>] [--phase4-root <dir>] --manifest <json>      (저장소 루트에서 실행)
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import re
import sqlite3
from pathlib import Path

INSTANCES = Path("ontology/output/tsg/RAN/formal/instances")
SECTION = re.compile(r"^tdoc:section/(?P<spec>\d{2}\.\d{3}(?:-\d+)?)-(?P<release>Rel-\d+)-(?P<clause>.+)$")
TSG_NUMBER = re.compile(r"^RAN#(\d+)$")

SCHEMA = """
    CREATE TABLE document(id TEXT PRIMARY KEY, number TEXT, doc_type TEXT, cr_number TEXT, spec TEXT,
                          target_release TEXT, list_status TEXT, presented_at TEXT, pack_field TEXT);
    CREATE TABLE revision(earlier TEXT, later TEXT);
    CREATE TABLE meeting(id TEXT PRIMARY KEY, label TEXT, number_int INTEGER, wg TEXT);
    CREATE TABLE resolution(id TEXT PRIMARY KEY, meeting_id TEXT);
    CREATE TABLE disposition(id TEXT PRIMARY KEY, resolution_id TEXT, target TEXT, code TEXT,
                             evidence_status TEXT, scope TEXT, evidence_path TEXT, evidence_sha256 TEXT);
    CREATE TABLE cr_pack(id TEXT PRIMARY KEY, pack_number TEXT, tsg_meeting TEXT, tsg_number INTEGER);
    CREATE TABLE cr_in_pack(cr TEXT, pack_id TEXT);
    CREATE TABLE pack_member(cr TEXT, pack_id TEXT);
    CREATE TABLE section(id TEXT PRIMARY KEY, spec TEXT, release TEXT, clause TEXT);
    CREATE TABLE cr_modifies_section(cr TEXT, section_id TEXT);
    CREATE TABLE section_modified_by(cr TEXT, section_id TEXT);
"""
INDEXES = (("revision", "earlier"), ("revision", "later"), ("resolution", "meeting_id"),
           ("disposition", "target"), ("disposition", "resolution_id"),
           ("cr_in_pack", "cr"), ("cr_in_pack", "pack_id"), ("pack_member", "cr"), ("pack_member", "pack_id"),
           ("cr_modifies_section", "cr"), ("cr_modifies_section", "section_id"),
           ("section_modified_by", "cr"), ("section_modified_by", "section_id"))


def as_list(value) -> list[str]:
    return [] if value is None else value if isinstance(value, list) else [value]


def available_gib() -> float:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 1024 / 1024
    raise RuntimeError("MemAvailable 항목이 /proc/meminfo 에 없다")


class Loader:
    """입력 파일을 하나씩 읽고, 읽은 파일의 경로·크기·SHA-256 을 남긴다."""

    def __init__(self, wg: str, phase2_root: Path | None, phase4_root: Path | None, min_available_gib: float):
        self.wg, self.roots, self.floor = wg, {"phase-2": phase2_root, "phase-4": phase4_root}, min_available_gib
        self.inputs: list[dict] = []

    def path(self, rel: str) -> Path:
        root = self.roots.get(rel.split("/", 1)[0])
        staged = root / self.wg / Path(rel).name if root else None
        return staged if staged and staged.exists() else INSTANCES / rel

    def graph(self, rel: str) -> list[dict]:
        gc.collect()
        free = available_gib()
        if free < self.floor:
            raise SystemExit(f"가용 메모리 {free:.1f}GiB 가 하한 {self.floor}GiB 미만이어서 멈춘다: {rel}")
        path = self.path(rel)
        data = path.read_bytes()
        self.inputs.append({"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                            "availableGibBeforeRead": round(free, 1)})
        return json.loads(data)["@graph"]


def export(wg: str, db_path: Path, loader: Loader) -> dict:
    if db_path.exists():
        db_path.unlink()
    db = sqlite3.connect(db_path)
    db.executescript(SCHEMA)

    documents = revisions = 0
    for record in loader.graph(f"phase-1/{wg}/tdocs.jsonld"):
        if "tdoc:tdocNumber" not in record:
            continue
        modifies = record.get("modifies")
        db.execute("INSERT INTO document VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            record["@id"], record["tdoc:tdocNumber"], record.get("@type") if isinstance(record.get("@type"), str) else None,
            record.get("tdoc:crNumber"),
            modifies.rsplit("/", 1)[-1].replace("_", ".") if isinstance(modifies, str) else None,
            str(record["targetRelease"]).rsplit("/", 1)[-1].replace("_", "-") if "targetRelease" in record else None,
            record.get("tdoc:status"),
            record.get("presentedAt") if isinstance(record.get("presentedAt"), str) else None,
            str(record["tdoc:tsgCRPack"]).strip() if "tdoc:tsgCRPack" in record else None))
        documents += 1
        earlier = as_list(record.get("isRevisionOf"))
        db.executemany("INSERT INTO revision VALUES (?, ?)", [(e, record["@id"]) for e in earlier])
        revisions += len(earlier)

    meetings = loader.graph(f"phase-1/{wg}/meetings.jsonld")
    db.executemany("INSERT INTO meeting VALUES (?, ?, ?, ?)", [
        (r["@id"], r["tdoc:meetingNumber"], r.get("tdoc:meetingNumberInt"), r.get("tdoc:workingGroup")) for r in meetings])
    # 날짜를 담은 칸이 회의 기록에 있는지를 그대로 남긴다(경과 일수를 셀 수 있는지의 근거).
    meeting_keys = sorted({key for r in meetings for key in r})

    resolutions = 0
    for path in sorted((INSTANCES / f"phase-2/{wg}").glob("resolutions_*.jsonld")):
        rows = [(r["@id"], r["madeAt"]) for r in loader.graph(f"phase-2/{wg}/{path.name}") if "madeAt" in r]
        db.executemany("INSERT OR IGNORE INTO resolution VALUES (?, ?)", rows)
        resolutions += len(rows)

    dispositions = 0
    for record in loader.graph(f"phase-2/{wg}/decision_dispositions.jsonld"):
        db.execute("INSERT OR IGNORE INTO disposition VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (
            record["@id"], record["dispositionOf"], record["dispositionTarget"], record["dispositionCode"],
            record["evidenceStatus"], json.loads(record["assessmentMethod"]).get("scope"),
            record.get("evidencePath"), record.get("evidenceSha256")))
        dispositions += 1

    sections: dict[str, None] = {}
    packs = members = 0
    for record in loader.graph(f"phase-4/{wg}/crpacks.jsonld"):
        number = TSG_NUMBER.match(record["tdoc:tsgMeeting"])
        db.execute("INSERT INTO cr_pack VALUES (?, ?, ?, ?)", (
            record["@id"], record["tdoc:crPackId"], record["tdoc:tsgMeeting"], int(number[1]) if number else None))
        rows = [(cr, record["@id"]) for cr in dict.fromkeys(as_list(record.get("hasCR")))]
        db.executemany("INSERT INTO pack_member VALUES (?, ?)", rows)
        packs, members = packs + 1, members + len(rows)

    forward_packs = forward_sections = 0
    for record in loader.graph(f"phase-4/{wg}/cr_extensions.jsonld"):
        rows = [(record["@id"], pack) for pack in dict.fromkeys(as_list(record.get("belongsToCRPack")))]
        db.executemany("INSERT INTO cr_in_pack VALUES (?, ?)", rows)
        forward_packs += len(rows)
        rows = [(record["@id"], section) for section in dict.fromkeys(as_list(record.get("modifiesSection")))]
        db.executemany("INSERT INTO cr_modifies_section VALUES (?, ?)", rows)
        forward_sections += len(rows)
        sections.update(dict.fromkeys(section for _, section in rows))

    reverse_sections = 0
    for record in loader.graph(f"phase-4/{wg}/section_extensions.jsonld"):
        rows = [(cr, record["@id"]) for cr in dict.fromkeys(as_list(record.get("modifiedByCR")))]
        db.executemany("INSERT INTO section_modified_by VALUES (?, ?)", rows)
        reverse_sections += len(rows)
        sections[record["@id"]] = None

    unparsed = 0
    for identifier in sections:
        match = SECTION.match(identifier)
        unparsed += match is None
        db.execute("INSERT INTO section VALUES (?, ?, ?, ?)", (
            identifier, *(match.group("spec", "release", "clause") if match else (None, None, None))))

    for table, column in INDEXES:
        db.execute(f"CREATE INDEX {table}_{column} ON {table}({column})")
    db.commit()
    tables = {name: db.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
              for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")}
    db.close()
    return {"wg": wg, "database": db_path.name, "databaseBytes": db_path.stat().st_size, "tableRows": tables,
            "recordsRead": {"documents": documents, "revisionLinks": revisions, "resolutionsWithMeeting": resolutions,
                            "dispositionRecords": dispositions, "packs": packs, "packMemberLinks": members,
                            "crInPackLinks": forward_packs, "crModifiesSectionLinks": forward_sections,
                            "sectionModifiedByLinks": reverse_sections, "sectionIdentifiersNotParsed": unparsed},
            "meetingRecordKeys": meeting_keys, "inputs": loader.inputs}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--wg", nargs="+", required=True)
    parser.add_argument("--db-dir", type=Path, required=True, help="작업반별 SQLite 파일을 둘 디렉토리")
    parser.add_argument("--manifest", type=Path, required=True, help="내보낸 표의 행 수와 입력 파일 해시를 적을 JSON")
    parser.add_argument("--min-available-gib", type=float, required=True,
                        help="파일을 읽기 전 가용 메모리가 이 값 미만이면 멈춘다")
    parser.add_argument("--phase2-root", type=Path)
    parser.add_argument("--phase4-root", type=Path)
    args = parser.parse_args()
    args.db_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(args.manifest.read_text()) if args.manifest.exists() else {"schema": SCHEMA.split("\n"), "exports": {}}
    for wg in args.wg:
        loader = Loader(wg, args.phase2_root, args.phase4_root, args.min_available_gib)
        manifest["exports"][wg] = export(wg, args.db_dir / f"{wg}.sqlite", loader)
        print(wg, json.dumps(manifest["exports"][wg]["tableRows"]), flush=True)
        args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
