"""다시 만든 SQLite 내보내기가 저장된 파일과 표 단위로 같은지 본다 (모델 호출 없음).

두 파일을 읽기 전용으로 열어 다음을 견준다.
- 스키마: `sqlite_master` 의 종류·이름·표·SQL (페이지 위치 `rootpage` 는 빼고 본다)
- 표마다 행 수와 행의 다중집합: 행마다 값과 저장 형식을 함께 묶은 sha256 의 개수를 양쪽에서 센다
- 표마다 rowid 순서의 행 배열이 같은지
- 주 키가 있는 표: 키마다 행 내용이 같은지, 한쪽에만 있는 키의 수
두 파일 바이트의 sha256 은 참고로 적는다. SQLite 파일 머리에는 변경 횟수 같은 칸이 있어 내용이 같아도 바이트가 다를 수 있다.

`--wg` 와 두 내보내기 기록(`--rebuilt-manifest`, `--stored-manifest`)을 주면 그 작업반 항목의 표 행 수·읽은 기록 수·
회의 기록 키·DB 크기·입력 파일(파일 이름·크기·SHA-256)을 견준다. 입력 경로와 읽기 전 가용 메모리는 실행마다 달라질 수 있어
같음 판정에 넣지 않고 경로만 따로 적는다.

사용: python3 compare_rebuilt_sqlite.py --rebuilt <sqlite> --stored <sqlite> --out <json>
          [--wg <WG> --rebuilt-manifest <json> --stored-manifest <json>]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sqlite3
from pathlib import Path


def connect(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def schema(db: sqlite3.Connection) -> list[tuple]:
    return sorted(db.execute("SELECT type, name, tbl_name, sql FROM sqlite_master"), key=repr)


def row_digest(row: tuple) -> bytes:
    return hashlib.sha256(repr(tuple((type(v).__name__, v) for v in row)).encode()).digest()


def table_rows(db: sqlite3.Connection, table: str) -> tuple[list[bytes], list[int], list[tuple]]:
    """rowid 순서의 행 digest, 주 키 열 위치, 행 원본(주 키가 있는 표의 예시용)."""
    pk = [info[1] for info in sorted(db.execute(f'PRAGMA table_info("{table}")'), key=lambda i: i[5]) if info[5] > 0]
    columns = [info[1] for info in db.execute(f'PRAGMA table_info("{table}")')]
    rows = list(db.execute(f'SELECT * FROM "{table}" ORDER BY rowid'))
    return [row_digest(r) for r in rows], [columns.index(c) for c in pk], rows


def compare_table(a: sqlite3.Connection, b: sqlite3.Connection, table: str) -> dict:
    da, pk, ra = table_rows(a, table)
    db_, _, rb = table_rows(b, table)
    ca, cb = collections.Counter(da), collections.Counter(db_)
    result = {"rebuiltRows": len(da), "storedRows": len(db_),
              "onlyRebuilt": sum((ca - cb).values()), "onlyStored": sum((cb - ca).values()),
              "orderIdentical": da == db_}
    if pk:
        ka = {tuple(r[i] for i in pk): (d, r) for d, r in zip(da, ra)}
        kb = {tuple(r[i] for i in pk): (d, r) for d, r in zip(db_, rb)}
        differ = [k for k in ka.keys() & kb.keys() if ka[k][0] != kb[k][0]]
        result.update({"primaryKeyColumns": len(pk), "onlyRebuiltKeys": len(ka.keys() - kb.keys()),
                       "onlyStoredKeys": len(kb.keys() - ka.keys()), "contentDiffers": len(differ),
                       "examples": [{"key": list(k), "rebuilt": list(ka[k][1]), "stored": list(kb[k][1])}
                                    for k in sorted(differ, key=repr)[:5]]})
    return result


def compare_manifest(rebuilt: Path, stored: Path, wg: str) -> dict:
    a = json.loads(rebuilt.read_text(encoding="utf-8"))["exports"][wg]
    b = json.loads(stored.read_text(encoding="utf-8"))["exports"][wg]

    def inputs(entry: dict) -> list[list]:
        return [[Path(i["path"]).name, i["bytes"], i["sha256"]] for i in entry["inputs"]]

    fields = {key: a.get(key) == b.get(key) for key in ("tableRows", "recordsRead", "meetingRecordKeys", "databaseBytes")}
    fields["inputs"] = inputs(a) == inputs(b)
    return {"rebuilt": str(rebuilt), "stored": str(stored), "fieldsIdentical": fields,
            "identical": all(fields.values()),
            "rebuiltInputPaths": [i["path"] for i in a["inputs"]], "storedInputPaths": [i["path"] for i in b["inputs"]]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuilt", required=True, type=Path)
    ap.add_argument("--stored", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--wg")
    ap.add_argument("--rebuilt-manifest", type=Path)
    ap.add_argument("--stored-manifest", type=Path)
    args = ap.parse_args()
    a, b = connect(args.rebuilt), connect(args.stored)
    sa, sb = schema(a), schema(b)
    tables = sorted({row[1] for row in sa + sb if row[0] == "table"})
    names_a = {row[1] for row in sa if row[0] == "table"}
    names_b = {row[1] for row in sb if row[0] == "table"}
    per_table = {t: compare_table(a, b, t) for t in tables if t in names_a and t in names_b}
    report = {"rebuilt": str(args.rebuilt), "stored": str(args.stored), "sqliteVersion": sqlite3.sqlite_version,
              "schemaIdentical": sa == sb, "tablesOnlyRebuilt": sorted(names_a - names_b),
              "tablesOnlyStored": sorted(names_b - names_a),
              "rebuiltRecords": sum(t["rebuiltRows"] for t in per_table.values()),
              "storedRecords": sum(t["storedRows"] for t in per_table.values()),
              "onlyRebuilt": sum(t["onlyRebuilt"] for t in per_table.values()),
              "onlyStored": sum(t["onlyStored"] for t in per_table.values()),
              "contentDiffers": sum(t.get("contentDiffers", 0) for t in per_table.values()),
              "orderIdentical": all(t["orderIdentical"] for t in per_table.values()),
              "rebuiltSha256": file_sha256(args.rebuilt), "storedSha256": file_sha256(args.stored),
              "tables": per_table}
    report["bytesIdentical"] = report["rebuiltSha256"] == report["storedSha256"]
    report["identical"] = (report["schemaIdentical"] and not report["tablesOnlyRebuilt"] and not report["tablesOnlyStored"]
                           and all(t["rebuiltRows"] == t["storedRows"] and t["onlyRebuilt"] == 0 and t["onlyStored"] == 0
                                   for t in per_table.values()))
    if args.wg and args.rebuilt_manifest and args.stored_manifest:
        report["manifest"] = compare_manifest(args.rebuilt_manifest, args.stored_manifest, args.wg)
    a.close()
    b.close()
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("tables", "manifest")}, ensure_ascii=False))
    if "manifest" in report:
        print(json.dumps({"manifestIdentical": report["manifest"]["identical"], **report["manifest"]["fieldsIdentical"]}))


if __name__ == "__main__":
    main()
