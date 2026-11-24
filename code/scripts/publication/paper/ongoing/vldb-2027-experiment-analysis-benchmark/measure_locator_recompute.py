"""처분 기록의 인용문을 기록된 위치(`body blocks [시작, 끝)`)만으로 근거 파일에서 다시 읽을 수 있는지 센다 (모델 호출 없음).

공개 기록은 인용문의 글을 빼고 경로 · 해시 · 위치 · 규칙 이름을 남긴다. 이 스크립트는 그 위치가 인용문을 되살리기에
충분한지 잰다. 처분 기록마다 다음을 본다.

- 근거 파일이 docx 이고 SHA-256 이 기록과 같은가(같지 않으면 위치를 따지지 않고 따로 센다).
- 인용문을 줄바꿈과 `|` 로 나눈 조각(공백을 뺀 뒤 네 글자 이상)이 모두 그 범위의 블록 글 안에 있는가.
  블록 번호는 다섯 WG 보고서 파서가 쓰는 공용 판독기 `docx_text.body_blocks` 의 문서 순서다.
  문단은 `chunk_text`, 표는 행마다 `| 칸 | 칸 |`(`table_line_rows`), 글상자 글은 그 문단 뒤에 둔다.
  지운 글은 세 방식(빼기 · 표시 · 표시 없이 함께)으로 읽고 어느 하나에서 맞으면 범위 안으로 센다.
- 범위 안에서 맞지 않으면 문서 본문 전체에서 맞는지를 따로 센다(위치만 어긋난 기록과 글이 다른 기록을 가른다).
  맞지 않은 기록은 모두 `misses` 에 WG · 식별자 · 상태 · 갈래 · 경로 · 범위로 남긴다(문항 근거와 맞대기 위함).

사용 (저장소 루트에서 실행):
  python3 measure_locator_recompute.py --out <json> [--wg RAN1 ...]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "scripts/tsg/RAN/formal/common"))
import docx_text  # noqa: E402  다섯 WG 보고서 파서의 공용 판독기

INSTANCES = ROOT / "ontology/output/tsg/RAN/formal/instances"
LOCATOR = re.compile(r"body blocks \[(\d+),\s*(\d+)\)")
WGS = ("RAN1", "RAN2", "RAN3", "RAN4", "RAN5")
MODES = (docx_text.DROP, docx_text.MARK, docx_text.KEEP)


def stream_dispositions(wg: str):
    """처분 기록 파일을 레코드 단위로 읽는다(파일 전체를 한 번에 올리지 않는다)."""
    buf = None
    with open(INSTANCES / f"phase-2/{wg}/decision_dispositions.jsonld", encoding="utf-8") as f:
        for line in f:
            if line.rstrip("\n") == "    {":
                buf = [line]
                continue
            if buf is not None:
                buf.append(line)
                if line.startswith("    }"):
                    record = json.loads("".join(buf).rstrip().rstrip(","))
                    buf = None
                    if "dispositionId" in record:
                        yield record


def squash(text: str) -> str:
    text = text.replace("[DEL]", "").replace("[/DEL]", "")
    return re.sub(r"\s+", "", text)


def pieces(quote: str) -> list[str]:
    return [p for p in (squash(x) for x in re.split(r"[\n|]", quote)) if len(p) >= 4]


def block_texts(path: Path, mode: str) -> list[str]:
    doc = docx_text.open_document(path)

    def read(paragraph) -> str:
        return docx_text.chunk_text(paragraph, deleted=mode)

    out = []
    for block in docx_text.body_blocks(doc):
        if docx_text.is_table(block):
            out.append("\n".join(docx_text.table_line_rows(block, para=read, deleted=mode)))
            continue
        text = read(block)
        box = docx_text.box_text(block, read=read)
        out.append(text + ("\n" + box if box else ""))
    return [squash(t) for t in out]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--wg", nargs="*", default=list(WGS))
    args = ap.parse_args()

    by_path: dict[str, list[dict]] = collections.defaultdict(list)
    counts = collections.Counter()
    for wg in args.wg:
        for r in stream_dispositions(wg):
            counts["records"] += 1
            m = LOCATOR.search(r.get("evidenceLocator") or "")
            q = r.get("evidenceQuote") or ""
            p = r.get("evidencePath") or ""
            if not (m and q and p):
                counts["incomplete"] += 1
                continue
            if not pieces(q):
                counts["quoteWithoutPiece"] += 1
                continue
            by_path[p].append({"wg": wg, "id": r["dispositionId"], "sha": r.get("evidenceSha256"),
                               "status": r.get("evidenceStatus"), "span": (int(m.group(1)), int(m.group(2))),
                               "pieces": pieces(q)})

    per_wg = collections.defaultdict(collections.Counter)
    samples = collections.defaultdict(list)
    misses = []
    for p, recs in sorted(by_path.items()):
        path = ROOT / p if not Path(p).is_absolute() else Path(p)
        if not path.is_file() or path.suffix.lower() != ".docx":
            for r in recs:
                per_wg[r["wg"]]["fileUnavailable"] += 1
            continue
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        try:
            texts = {mode: block_texts(path, mode) for mode in MODES}
        except Exception as error:  # 깨진 파일은 까닭과 함께 센다
            for r in recs:
                per_wg[r["wg"]]["unreadable"] += 1
            samples["unreadable"].append([p, f"{type(error).__name__}: {error}"[:160]])
            continue
        for r in recs:
            c = per_wg[r["wg"]]
            c["checked"] += 1
            if r["sha"] != sha:
                c["shaDiffers"] += 1
                continue
            a, b = r["span"]
            in_span = any(all(x in "".join(t[a:b]) for x in r["pieces"]) for t in texts.values())
            if in_span:
                c["inSpan"] += 1
                c[f"inSpan:{r['status']}"] += 1
                continue
            in_body = any(all(x in "".join(t) for x in r["pieces"]) for t in texts.values())
            c["outsideSpanInBody" if in_body else "notInBody"] += 1
            c[f"miss:{r['status']}"] += 1
            misses.append([r["wg"], r["id"], r["status"], "outsideSpanInBody" if in_body else "notInBody", p, [a, b]])
            if len(samples[r["wg"]]) < 5:
                samples[r["wg"]].append([r["id"], p, [a, b], len(texts[docx_text.DROP]), r["pieces"][:2]])

    total = collections.Counter()
    for c in per_wg.values():
        total.update(c)
    result = {"script": Path(__file__).name, "counts": dict(counts), "files": len(by_path),
              "total": dict(total), "perWg": {k: dict(v) for k, v in sorted(per_wg.items())},
              "samples": dict(samples), "misses": misses}
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=1))
    print(json.dumps({"counts": dict(counts), "total": dict(total)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
