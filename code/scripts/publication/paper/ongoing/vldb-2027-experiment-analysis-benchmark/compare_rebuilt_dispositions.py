"""다시 만든 처분 기록 파일이 저장된 파일과 기록 단위로 같은지 본다 (모델 호출 없음).

두 파일을 기록 단위로 흘려 읽어(파일 전체를 한 번에 올리지 않는다) 기록 식별 필드(`--key`, 기본값 dispositionId)의 값마다
정규화한 JSON 의 sha256 을 견준다. 처분 단계가 함께 쓰는 `resolutions_document_dispositions.jsonld` 는 `--key @id` 로 견준다.
결과: 양쪽 기록 수, 한쪽에만 있는 id, 내용이 다른 id 의 수와 다른 필드 이름의 빈도, 파일 머리(기록 밖 줄)가 같은지.
머리가 다르면 다른 줄을 `headDiff` 에 앞에서부터 60줄까지 적고, 더 길면 `headDiffTruncated` 를 참으로 적는다.
바이트 단위로는 파일 전체의 sha256 과, 기록 줄을 파일 차례대로 이은 바이트의 sha256 을 견준다. `recordBlockIdentical` 은
기록 줄의 바이트가 차례까지 같고 양쪽 모두 기록 사이에 다른 줄이 없을 때 참이며, 이때 두 파일의 차이는 기록 묶음 앞뒤의
머리 줄에만 있다. 식별 필드가 없는 기록의 수와 같은 식별 값이 다시 나온 기록의 수도 양쪽 따로 적는다.

사용: python3 compare_rebuilt_dispositions.py --rebuilt <jsonld> --stored <jsonld> --out <json> [--key <field>]
"""
from __future__ import annotations

import argparse
import collections
import difflib
import hashlib
import json
from pathlib import Path

HEAD_DIFF_LINES = 60


def stream(path: Path, key: str, layout: dict):
    """기록을 하나씩 내준다. 다 읽으면 layout 에 머리 줄, 기록 줄 바이트의 sha256, 기록 사이 줄 수를 채운다."""
    buf, head = None, []
    record_lines = hashlib.sha256()
    started = False
    pending = between = before = without_key = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.rstrip("\n") == "    {":
                between += pending
                started, pending, buf = True, 0, [line]
                continue
            if buf is not None:
                buf.append(line)
                if line.startswith("    }"):
                    text = "".join(buf)
                    record_lines.update(text.encode("utf-8"))
                    record = json.loads(text.rstrip().rstrip(","))
                    buf = None
                    if key in record:
                        yield record
                    else:
                        without_key += 1
                continue
            head.append(line)
            if started:
                pending += 1
            else:
                before += 1
    layout.update(head="".join(head), recordLinesSha256=record_lines.hexdigest(), headLinesBeforeRecords=before,
                  linesBetweenRecords=between, recordsWithoutKey=without_key)


def digest(record: dict) -> str:
    return hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def index(path: Path, key: str) -> tuple[dict, dict]:
    out, layout, duplicates = {}, {}, 0
    for record in stream(path, key, layout):
        duplicates += record[key] in out
        out[record[key]] = (digest(record), record)
    layout.update(duplicateKeys=duplicates, bytes=path.stat().st_size, sha256=file_sha256(path))
    return out, layout


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuilt", required=True)
    ap.add_argument("--stored", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--key", default="dispositionId")
    args = ap.parse_args()
    a, la = index(Path(args.rebuilt), args.key)
    b, lb = index(Path(args.stored), args.key)
    differ = [k for k in a.keys() & b.keys() if a[k][0] != b[k][0]]
    fields = collections.Counter()
    examples = []
    for k in differ:
        ra, rb = a[k][1], b[k][1]
        changed = sorted(f for f in ra.keys() | rb.keys() if ra.get(f) != rb.get(f))
        fields.update(changed)
        if len(examples) < 5:
            examples.append({args.key: k, "fields": changed,
                             "rebuilt": {f: ra.get(f) for f in changed}, "stored": {f: rb.get(f) for f in changed}})
    report = {"rebuilt": args.rebuilt, "stored": args.stored, "key": args.key,
              "rebuiltRecords": len(a), "storedRecords": len(b),
              "onlyRebuilt": len(a.keys() - b.keys()), "onlyStored": len(b.keys() - a.keys()),
              "contentDiffers": len(differ), "fieldsDiffering": dict(fields.most_common()),
              "headIdentical": la["head"] == lb["head"], "examples": examples}
    for field in ("recordsWithoutKey", "duplicateKeys", "bytes", "sha256", "headLinesBeforeRecords",
                  "linesBetweenRecords"):
        report[field] = {"rebuilt": la[field], "stored": lb[field]}
    report["bytesIdentical"] = la["sha256"] == lb["sha256"]
    report["recordLinesIdentical"] = la["recordLinesSha256"] == lb["recordLinesSha256"]
    report["recordBlockIdentical"] = (report["recordLinesIdentical"]
                                      and not (la["linesBetweenRecords"] or lb["linesBetweenRecords"]))
    if la["head"] != lb["head"]:
        diff = list(difflib.unified_diff(la["head"].splitlines(), lb["head"].splitlines(), "rebuilt", "stored",
                                         n=0, lineterm=""))
        report["headDiff"] = diff[:HEAD_DIFF_LINES]
        report["headDiffTruncated"] = len(diff) > HEAD_DIFF_LINES
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("examples", "headDiff")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
