"""인용문이 기록된 범위에서 다시 읽히지 않은 처분 기록(`locator_recompute.json` 의 `misses`)마다 까닭을 가린다 (모델 호출 없음).

`measure_locator_recompute.py` 는 공용 판독기(`docx_text.open_document` + `body_blocks` + `chunk_text`
+ `table_line_rows` + `box_text`)로 범위의 글을 읽고, 인용문 조각(줄바꿈 · `|` 로 나누고 공백을 뺀 네 글자 이상)이
모두 그 안에 있는지 본다. 이 스크립트는 맞지 않은 기록마다 같은 근거 파일을 판독 방식만 하나씩 바꿔 다시 읽고,
처음으로 조각이 모두 맞는 방식을 까닭으로 적는다.

  audit_chunk      측정 스크립트와 같은 읽기(수식 자리에 선형 표기 · 수식 개체 글을 넣는다)
  audit_final      같은 트리(`open_document`)에서 수식을 빼고 읽기(`paragraph_text(math=False)`, 글상자 글 포함)
  audit_omml_only  같은 트리에서 OMML 수식(`m:oMath`)의 선형 표기만 넣고 수식 개체 · 수식 그림 글은 빼고 읽기
                   (audit_final 은 맞고 이것이 맞으면 수식 개체 · 그림 글만으로 갈라진 것이다)
  builder          처분 기록을 만든 읽기(`decision_disposition.source_blocks`: `zip_part` + `iter_blocks` + `final_text`)

그 밖에 기록마다 다음을 적는다.
- 생산기 판독(builder)으로 읽은 범위 글이 저장된 `evidenceQuote` 와 글자 그대로 같은가(생산기 검사
  `validate_dispositions` 의 등식과 같다). 같지 않으면 기록이 만들어진 뒤 판독기가 바뀐 것이다.
- 범위 안 블록의 수식(`m:oMath`) · 수식 개체(`w:object`) · 그림 단위 · 글상자 · 필드 · 기호(`w:sym`) 수.
- 맞지 않은 첫 조각에서 인용문과 감사 판독이 갈라지는 자리(앞뒤 글).
- 벤치마크 문항(`chain_items_admitted.jsonl` 의 `evidence[].dispositionId`)이 그 기록을 쓰는지.
  보조로 (문서 번호, WG 회의) 쌍이 같은 문항 근거도 센다.

사용 (저장소 루트에서 실행):
  .venv/bin/python3 -I scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/classify_quote_span_misses.py \
      --misses logs/.../analysis/locator_recompute.json --out logs/.../analysis/quote_span_misses.json
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "scripts/tsg/RAN/formal/common"))
sys.path.insert(0, str(HERE))
import docx_text  # noqa: E402
import decision_disposition as dd  # noqa: E402
import measure_locator_recompute as mlr  # noqa: E402

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
ITEMS = ROOT / "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/integration/items_final/gate"
ITEM_FILES = (ITEMS / "core/chain_items_admitted.jsonl", ITEMS / "ran5/chain_items_admitted.jsonl")
MODES = (docx_text.DROP, docx_text.MARK, docx_text.KEEP)


def audit_variant(doc, mode: str, math) -> list[str]:
    """`open_document` 트리를 `math` 값만 바꿔 측정 스크립트와 같은 꼴로 읽는다(공백을 뺀 블록 글)."""
    def read(paragraph) -> str:
        return docx_text.paragraph_text(getattr(paragraph, "_p", paragraph), deleted=mode, math=math)

    out = []
    for block in docx_text.body_blocks(doc):
        if docx_text.is_table(block):
            out.append("\n".join(docx_text.table_line_rows(block, para=read, deleted=mode)))
            continue
        text = read(block)
        box = docx_text.box_text(block, read=read)
        out.append(text + ("\n" + box if box else ""))
    return [mlr.squash(t) for t in out]


def features(blocks, a: int, b: int) -> dict:
    c = collections.Counter()
    for blk in blocks[a:b]:
        for e in blk.iter():
            tag = e.tag
            if tag == M + "oMath":
                c["oMath"] += 1
            elif tag == W + "object":
                c["object"] += 1
            elif tag in (W + "drawing", W + "pict"):
                c["drawingOrPict"] += 1
            elif tag == W + "txbxContent":
                c["textBox"] += 1
            elif tag in (W + "fldChar", W + "fldSimple"):
                c["field"] += 1
            elif tag == W + "sym":
                c["sym"] += 1
            elif tag in (W + "ins", W + "del"):
                c["trackedChange"] += 1
            elif tag == W + "tbl":
                c["table"] += 1
    return dict(c)


def first_divergence(pieces: list[str], span: str) -> dict | None:
    for piece in pieces:
        if piece in span:
            continue
        lo, hi = 0, len(piece)
        while lo < hi:  # 범위 글 안에 있는 가장 긴 앞머리
            mid = (lo + hi + 1) // 2
            if piece[:mid] in span:
                lo = mid
            else:
                hi = mid - 1
        pos = span.find(piece[:lo]) if lo else -1
        return {"piece": piece[:160], "matchedPrefixChars": lo,
                "quoteContinues": piece[lo:lo + 60],
                "auditContinues": span[pos + lo:pos + lo + 80] if pos >= 0 else None}
    return None


def meeting_of(path: str) -> str:
    stem = Path(path).stem.removeprefix("Final_Report_")
    wg, _, rest = stem.partition("-")
    return f"{wg}#{rest}".lower()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--misses", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    misses = json.loads(Path(args.misses).read_text())["misses"]
    wanted = {m[1]: {"wg": m[0], "status": m[2], "auditBranch": m[3], "path": m[4], "span": m[5]} for m in misses}
    for wg in sorted({m["wg"] for m in wanted.values()}):
        for r in mlr.stream_dispositions(wg):
            if r["dispositionId"] in wanted:
                wanted[r["dispositionId"]].update(
                    quote=r["evidenceQuote"], locator=r["evidenceLocator"], sha=r["evidenceSha256"],
                    target=r.get("targetTdocNumber"), code=r.get("dispositionCode"),
                    rule=json.loads(r.get("assessmentMethod") or "{}").get("rule"))

    by_path = collections.defaultdict(list)
    for ident, rec in wanted.items():
        by_path[rec["path"]].append(ident)

    rows = []
    for p, idents in sorted(by_path.items()):
        path = ROOT / p
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        doc = docx_text.open_document(path)
        chunk = {m: mlr.block_texts(path, m) for m in MODES}
        final = {m: audit_variant(doc, m, False) for m in MODES}
        omml = {m: audit_variant(doc, m, lambda eq, m=m: docx_text.math_linear(eq, m)) for m in MODES}
        btexts, bsha, bblocks = dd.source_blocks.__wrapped__(str(path))
        builder = [mlr.squash(t) for t in btexts[0:len(btexts)]]
        for ident in idents:
            rec = wanted[ident]
            a, b = rec["span"]
            pcs = mlr.pieces(rec["quote"])
            builder_quote = "\n".join(btexts[a:b])

            def hit(texts) -> bool:
                return all(x in "".join(texts[a:b]) for x in pcs)

            reading = {"audit_chunk": any(hit(t) for t in chunk.values()),
                       "audit_final": any(hit(t) for t in final.values()),
                       "audit_omml_only": any(hit(t) for t in omml.values()),
                       "builder": hit(builder)}
            first = next((k for k in ("audit_chunk", "audit_final", "builder") if reading[k]), None)
            span_chunk = "".join(chunk[docx_text.DROP][a:b])
            changed_blocks = [i for i in range(a, b) if chunk[docx_text.DROP][i] != final[docx_text.DROP][i]]
            rows.append({
                "wg": rec["wg"], "dispositionId": ident, "status": rec["status"], "auditBranch": rec["auditBranch"],
                "path": p, "span": [a, b], "target": rec.get("target"), "dispositionCode": rec.get("code"),
                "rule": rec.get("rule"), "meeting": meeting_of(p),
                "shaMatchesRecord": sha == rec["sha"] == bsha,
                "builderReadingEqualsStoredQuote": builder_quote == rec["quote"],
                "blockCountAudit": len(chunk[docx_text.DROP]), "blockCountBuilder": len(btexts),
                "readingMatches": reading, "firstMatchingReading": first,
                "spanBlocksWhereMathChangesAuditText": len(changed_blocks),
                "features": features(bblocks, a, b),
                "divergence": first_divergence(pcs, span_chunk)})

    # 원인 분류: 관찰한 판독 차이로만 정한다.
    for r in rows:
        f = r["features"]
        if not r["builderReadingEqualsStoredQuote"]:
            cause = "stored_quote_differs_from_current_builder_reading"
        elif r["firstMatchingReading"] == "audit_final":
            cause = ("audit_inserts_equation_object_or_picture_text" if r["readingMatches"]["audit_omml_only"]
                     else "audit_inserts_omml_equation_linear_text")
        elif r["firstMatchingReading"] == "builder":
            cause = "audit_tree_differs_from_builder_tree"
        elif r["firstMatchingReading"] is None:
            cause = "unexplained_no_reading_matches"
        else:
            cause = "matches_under_audit_reading_on_rerun"
        r["cause"] = cause

    # 벤치마크 문항 근거와 맞대기
    evid = []
    for file in ITEM_FILES:
        for line in file.read_text().splitlines():
            item = json.loads(line)
            for e in item.get("evidence", []):
                evid.append((item["id"], item["family"], e))
    miss_ids = {r["dispositionId"]: r for r in rows}
    pair_index = collections.defaultdict(list)
    for r in rows:
        pair_index[(r["target"], r["meeting"])].append(r["dispositionId"])
    by_id, by_pair = collections.defaultdict(set), collections.defaultdict(set)
    for item_id, family, e in evid:
        if e.get("dispositionId") in miss_ids:
            by_id[e["dispositionId"]].add(item_id)
        for ident in pair_index.get((e.get("document"), (e.get("wgMeeting") or "").lower()), []):
            by_pair[ident].add(item_id)
    for r in rows:
        r["itemsByDispositionId"] = sorted(by_id.get(r["dispositionId"], ()))
        r["itemsByDocumentMeetingPair"] = sorted(by_pair.get(r["dispositionId"], ()))

    def summary(sel):
        causes = collections.Counter(r["cause"] for r in sel)
        per_wg = collections.defaultdict(collections.Counter)
        examples = collections.defaultdict(list)
        for r in sel:
            per_wg[r["cause"]][r["wg"]] += 1
            if len(examples[r["cause"]]) < 3:
                examples[r["cause"]].append({"dispositionId": r["dispositionId"], "divergence": r["divergence"],
                                             "features": r["features"]})
        return {"records": len(sel), "causes": dict(causes),
                "causesPerWg": {k: dict(v) for k, v in per_wg.items()},
                "builderReadingEqualsStoredQuote": sum(r["builderReadingEqualsStoredQuote"] for r in sel),
                "shaMatchesRecord": sum(r["shaMatchesRecord"] for r in sel),
                "blockCountsAgree": sum(r["blockCountAudit"] == r["blockCountBuilder"] for r in sel),
                "readingMatches": {k: sum(r["readingMatches"][k] for r in sel)
                                   for k in ("audit_chunk", "audit_final", "audit_omml_only", "builder")},
                "withOmml": sum(bool(r["features"].get("oMath")) for r in sel),
                "withEquationObject": sum(bool(r["features"].get("object")) for r in sel),
                "examples": dict(examples),
                "goldByDispositionId": {"dispositions": sum(bool(r["itemsByDispositionId"]) for r in sel),
                                        "items": len({i for r in sel for i in r["itemsByDispositionId"]})},
                "goldByDocumentMeetingPair": {"dispositions": sum(bool(r["itemsByDocumentMeetingPair"]) for r in sel),
                                              "items": len({i for r in sel for i in r["itemsByDocumentMeetingPair"]})}}

    sv = [r for r in rows if r["status"] == "source_verified"]
    result = {"script": Path(__file__).name, "input": args.misses,
              "itemFiles": [str(f.relative_to(ROOT)) for f in ITEM_FILES],
              "itemEvidenceEntries": len(evid),
              "goldMatchingRule": "item.evidence[].dispositionId == record.dispositionId (exact); "
                                  "secondary: (evidence.document, evidence.wgMeeting) == (targetTdocNumber, meeting of evidencePath), case-insensitive meeting",
              "sourceVerified": summary(sv), "allMisses": summary(rows), "rows": rows}
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=1))
    print(json.dumps({k: result["sourceVerified"][k] for k in ("records", "causes", "builderReadingEqualsStoredQuote",
                                                               "readingMatches", "goldByDispositionId",
                                                               "goldByDocumentMeetingPair")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
