"""회의 보고서 처분과 TDoc 목록 상태가 다른 문서를 표본으로 뽑아 원문을 다시 읽게 하고 판정을 센다 (모델 호출 없음).

모집단은 `measure_cross_source_agreement.py` 가 맞대는 문서 가운데 목록 상태가 그 문서의 처분 코드 집합에 없는
문서다(같은 기록 조건 · 같은 표기 맞춤 · 목록이 처분을 적지 않은 문서 제외). 범위는 `--scope` 로 고른다.

`sample` 은 작업반마다 차이 문서를 문서 id 순으로 정렬하고 `random.Random(seed)` 를 작업반마다 새로 만들어
`--sample` 건을 비복원 추출한다. 문서마다 근거 파일(수락본)에서 인용문이 걸친 줄을 다시 찾아 발췌를 만든다.
인용문이 원문의 이어진 줄이 아니면(부속서의 표 머리와 대상 행) 인용문 줄마다 그 줄을 담은 원문 줄을 차례로 찾는다.
인용문 첫 줄이 문서 목록 줄이면 그 문서 항목 전체(문서 자신의 줄과 이메일 토론 블록)를 발췌에 넣는다.
줄 찾기와 항목 경계는 `audit_list_line_dispositions.py` 의 함수를 그대로 쓴다.
판정용 묶음(`--packet`)에는 문서 번호와 발췌만 싣고, 목록 상태와 기록의 처분 코드는 답지(`--key`)에만 둔다.

`score` 는 판정(문서 id → 회의록이 그 문서 자체에 적은 결과 코드 목록)을 답지와 맞대어 문서마다 하나로 나눈다.
- `recordSupported`: 기록의 처분 코드가 판정 코드에 있다. 회의록을 바르게 읽었고 두 원자료가 다르게 적었다.
  그 가운데 목록 상태도 판정 코드에 있으면 `reportStatesBoth`(회의록이 두 결과를 함께 적었다),
  목록 상태가 revised · merged 이고 목록이 다음 판(revisedTo)을 적었으면 `listRecordsLaterRevision`,
  나머지는 `sourcesDiffer` 다.
- `listOnly`: 판정 코드에 목록 상태만 있다. 기록이 회의록을 잘못 읽은 경우다.
- `neither`: 판정 코드에 둘 다 없다(회의록이 그 문서의 결과를 적지 않았다는 판정 포함). 역시 기록의 오독이다.
작업반마다 차이 문서 가운데 오독(`listOnly` + `neither`) 비율과 Wilson 95% 구간을 내고, 그 비율을 맞댄 문서 수에
대한 비율로도 옮긴다(차이 비율 × 오독 비율).

사용 (저장소 루트에서):
  python3 classify_cross_source_differences.py sample --sample 40 --seed 20261112 --packet <jsonl> --key <json>
  python3 classify_cross_source_differences.py score --key <json> --judgments <json> [<json> …] --out <json>
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_list_line_dispositions import compact, entry_lines, find_anchor, load_docx, wilson  # noqa: E402
from measure_cross_source_agreement import INSTANCES, LIST_WITHOUT_DISPOSITION, canonical  # noqa: E402

WGS = ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")
SCOPES = {"allDocuments": lambda r: True,
          "cr": lambda r: r.get("@type") == "tdoc:CR" and r.get("tdoc:type") == "CR",
          "crForm": lambda r: r.get("@type") == "tdoc:CR"}
CODES = ("agreed", "endorsed", "conditionally agreed", "partially agreed", "noted", "revised", "merged",
         "not pursued", "not agreed", "not treated", "postponed", "withdrawn", "rejected")
MAX_LINES, MAX_CHARS = 40, 4000


def differences(wg: str, scope: str) -> tuple[list[dict], int]:
    """(차이 문서 목록, 맞댄 문서 수). 문서마다 목록 상태 · 기록 코드 · 근거 기록."""
    load = lambda rel: json.loads((INSTANCES / rel).read_text())["@graph"]
    tdocs = {r["@id"]: r for r in load(f"phase-1/{wg}/tdocs.jsonld") if "tdoc:status" in r}
    records: dict[str, list[dict]] = collections.defaultdict(list)
    for record in load(f"phase-2/{wg}/decision_dispositions.jsonld"):
        if (record["evidenceStatus"] == "source_verified"
                and json.loads(record["assessmentMethod"]).get("scope") == "whole_target"):
            records[record["dispositionTarget"]].append(record)
    keep, compared, rows = SCOPES[scope], 0, []
    for target in sorted(records):
        listed = tdocs.get(target)
        if listed is None or not keep(listed):
            continue
        status = canonical(listed["tdoc:status"])
        if status in LIST_WITHOUT_DISPOSITION:
            continue
        compared += 1
        codes = sorted({canonical(r["dispositionCode"]) for r in records[target]})
        if status in codes:
            continue
        rows.append({"id": target, "wg": wg, "listStatus": status, "reportCodes": codes,
                     "listRevisedTo": listed.get("revisedTo"),
                     "records": [{"dispositionId": r["dispositionId"], "code": canonical(r["dispositionCode"]),
                                  "rule": json.loads(r["assessmentMethod"]).get("rule"),
                                  "path": r["evidencePath"], "sha256": r["evidenceSha256"],
                                  "locator": r["evidenceLocator"], "quote": r["evidenceQuote"]}
                                 for r in sorted(records[target], key=lambda r: r["dispositionId"])]})
    return rows, compared


def excerpt(record: dict, prefix: str) -> dict:
    """근거 파일에서 인용문이 걸친 줄을 다시 찾고, 목록 줄이면 문서 항목 전체로 넓힌 발췌."""
    sha, lines, _, _ = load_docx(record["path"])
    quote = record["quote"]
    head = " ".join(quote.split("\n")[0].split())
    anchor, candidates = find_anchor(lines, quote, record["locator"])
    if anchor is None:
        # 첫 줄이 문단 하나와 같지 않은 인용(표 머리와 행 따위)은 첫 줄을 담은 첫 줄 자리부터 잇는다.
        hits = [i for i, (_, text) in enumerate(lines) if head and head in " ".join(text.split())]
        anchor, candidates = (hits[0], len(hits)) if hits else (None, 0)
    if anchor is None:
        return {"found": False, "shaMatches": sha == record["sha256"]}
    want, got, end = compact(quote), "", anchor
    while len(got) < len(want) and end < len(lines):
        got += compact(lines[end][1])
        end += 1
    span = [text for _, text in lines[anchor:max(end, anchor + 1)]]
    covered = got.startswith(want)
    if not covered:
        # 표 머리와 대상 행처럼 떨어진 줄을 이은 인용은 인용문 줄마다 그 줄을 담은 원문 줄을 차례로 찾는다.
        picked, cursor = [], anchor
        for piece in (piece for piece in quote.split("\n") if piece.strip()):
            target = compact(piece)
            hit = next((i for i in range(cursor, len(lines)) if target in compact(lines[i][1])), None)
            if hit is None:
                break
            picked.append(hit)
            cursor = hit
        else:
            covered = True
        span = [lines[i][1] for i in sorted(set(picked))] or span
    list_line = re.match(rf"^\s*{prefix}-\d{{5,7}}\b", head) is not None
    if list_line:
        own, email, _ = entry_lines(lines, anchor, prefix)
        span = [lines[anchor][1].split("\n")[0]]
        for _, text in own + email:
            span.append(text)
    text = "\n".join(piece for piece in span if piece.strip())
    clipped = len(span) > MAX_LINES or len(text) > MAX_CHARS
    text = "\n".join(text.split("\n")[:MAX_LINES])[:MAX_CHARS]
    return {"found": True, "shaMatches": sha == record["sha256"], "anchorCandidates": candidates,
            "listEntry": list_line, "quoteCovered": covered, "clipped": clipped, "text": text}


def sample(args) -> None:
    key, packet = {"scope": args.scope, "sample": args.sample, "seed": args.seed, "wgs": {}}, []
    for wg in WGS:
        rows, compared = differences(wg, args.scope)
        drawn = random.Random(args.seed).sample(rows, min(args.sample, len(rows)))
        drawn.sort(key=lambda row: (row["records"][0]["path"], row["id"]))
        items = []
        for row in drawn:
            pieces = [excerpt(record, f"R{wg[-1]}") for record in row["records"]]
            items.append({**{k: row[k] for k in ("id", "listStatus", "reportCodes", "listRevisedTo")},
                          "rules": sorted({r["rule"] for r in row["records"]}),
                          "excerpts": [{k: v for k, v in piece.items() if k != "text"} for piece in pieces]})
            packet.append({"id": row["id"], "wg": wg, "document": row["id"].split(":", 1)[1],
                           "excerpts": [piece.get("text", "") for piece in pieces]})
        key["wgs"][wg] = {"compared": compared, "differences": len(rows), "items": items,
                          "pairs": collections.Counter(f"{r['listStatus']} | {'+'.join(r['reportCodes'])}"
                                                       for r in rows).most_common(10)}
        print(wg, "compared", compared, "differences", len(rows), "drawn", len(items),
              "excerpt missing", sum(not e["found"] for i in items for e in i["excerpts"]), flush=True)
    random.Random(args.seed).shuffle(packet)
    args.packet.write_text("".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in packet))
    args.key.write_text(json.dumps(key, ensure_ascii=False, indent=2) + "\n")


def classify(item: dict, judged: set[str]) -> str:
    if set(item["reportCodes"]) & judged:
        if item["listStatus"] in judged:
            return "reportStatesBoth"
        if item["listStatus"] in ("revised", "merged") and item["listRevisedTo"]:
            return "listRecordsLaterRevision"
        return "sourcesDiffer"
    return "listOnly" if item["listStatus"] in judged else "neither"


def score(args) -> None:
    key = json.loads(args.key.read_text())
    judges = [json.loads(path.read_text()) for path in args.judgments]
    result = {"scope": key["scope"], "judges": [str(p) for p in args.judgments], "wgs": {}}
    for wg, block in key["wgs"].items():
        counts: collections.Counter[str] = collections.Counter()
        split, items = [], []
        for item in block["items"]:
            labels = []
            for judge in judges:
                codes = {canonical(c) for c in judge[item["id"]]["codes"]}
                unknown = codes - set(CODES)
                if unknown:
                    raise SystemExit(f"{item['id']}: 알 수 없는 판정 코드 {sorted(unknown)}")
                labels.append(classify(item, codes))
            final = labels[0] if len(set(labels)) == 1 else "judgesDisagree"
            if final == "judgesDisagree":
                split.append(item["id"])
            counts[final] += 1
            items.append({"id": item["id"], "listStatus": item["listStatus"], "reportCodes": item["reportCodes"],
                          "labels": labels, "final": final})
        n = len(block["items"])
        misread = counts["listOnly"] + counts["neither"]
        decided = n - counts["judgesDisagree"]
        share = block["differences"] / block["compared"] if block["compared"] else 0.0
        result["wgs"][wg] = {"compared": block["compared"], "differences": block["differences"], "sampled": n,
                             "counts": dict(counts), "judgesDisagree": split,
                             "misreadShareOfDifferences": round(misread / decided, 4) if decided else None,
                             "misreadWilson95": wilson(misread, decided) if decided else None,
                             "misreadShareOfCompared": round(share * misread / decided, 5) if decided else None,
                             "items": items}
        print(wg, dict(counts), "misread", misread, "/", decided, flush=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("sample", help="차이 문서를 뽑아 판정 묶음과 답지를 쓴다")
    run.add_argument("--scope", choices=sorted(SCOPES), default="allDocuments")
    run.add_argument("--sample", type=int, required=True, help="작업반별 추출 건수")
    run.add_argument("--seed", type=int, required=True)
    run.add_argument("--packet", type=Path, required=True, help="판정용 묶음(JSONL, 목록 상태 · 기록 코드 없음)")
    run.add_argument("--key", type=Path, required=True, help="답지(JSON)")
    grade = sub.add_parser("score", help="판정을 답지와 맞대어 나눈다")
    grade.add_argument("--key", type=Path, required=True)
    grade.add_argument("--judgments", type=Path, nargs="+", required=True,
                       help="판정 JSON 하나 이상(문서 id → {\"codes\": [...], \"line\": \"...\"}). 둘 이상이면 판정이 갈린 문서를 따로 둔다")
    grade.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    sample(args) if args.command == "sample" else score(args)


if __name__ == "__main__":
    main()
