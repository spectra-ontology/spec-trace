"""처분 기록의 원문 판정용 묶음을 만든다 (모델 호출 없음).

판독자는 기록의 처분 코드와 범위를 보지 않고, 기록이 가리킨 회의 보고서 본문만 읽어 대상 문서의 처분을 고른다.
표본과 비교 규칙은 `plan.json` 에 판독 전에 고정했다. 이 스크립트는 그 계획대로 다음을 만든다.

- 표본: WG 마다 source_verified 기록 200건과 pending 기록 20건을 SHA-256(seed + 식별자) 순으로 고르고,
  재판독 차이 파일의 기록을 모두 더한다.
- 묶음: 대상 문서 번호, 보고서 파일 이름, 기록 범위의 네 블록 앞부터 네 블록 뒤까지의 본문(범위 블록 표시).
  본문은 해시가 기록과 같은 근거 파일의 accepted 글(지운 글 빼기)로 읽는다. 4000자를 넘는 블록은 대상 번호의
  첫 언급을 가운데 두고 4000자로 자르고 자른 곳을 표시한다.
- 열쇠: 묶음 번호마다 기록 식별자 · 처분 코드 · 범위 · 표본 종류. 판독자에게 주지 않는다.

사용 (저장소 루트에서 실행):
  python3 build_disposition_adjudication_packets.py --plan <plan.json> --reread <reread_differences.json> --out <dir>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "scripts/tsg/RAN/formal/common"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import docx_text  # noqa: E402  다섯 WG 보고서 파서의 공용 판독기
from measure_locator_recompute import LOCATOR, WGS, stream_dispositions  # noqa: E402

CONTEXT = 4
BLOCK_CAP = 4000
PART_SIZE = 70
VERIFIED_PER_WG = 200
PENDING_PER_WG = 20


def rank(seed: str, tag: str, ident: str) -> str:
    return hashlib.sha256(f"{seed}|{tag}{ident}".encode()).hexdigest()


def readable_blocks(path: Path) -> list[str]:
    doc = docx_text.open_document(path)

    def read(paragraph) -> str:
        return docx_text.chunk_text(paragraph, deleted=docx_text.DROP)

    out = []
    for block in docx_text.body_blocks(doc):
        if docx_text.is_table(block):
            out.append("\n".join(docx_text.table_line_rows(block, para=read, deleted=docx_text.DROP)))
            continue
        text = read(block)
        box = docx_text.box_text(block, read=read)
        out.append(text + ("\n" + box if box else ""))
    return out


def cap(text: str, target: str) -> tuple[str, bool]:
    if len(text) <= BLOCK_CAP:
        return text, False
    at = text.find(target)
    start = 0 if at < 0 else max(0, min(at - BLOCK_CAP // 2, len(text) - BLOCK_CAP))
    return ("[cut] " if start else "") + text[start:start + BLOCK_CAP] + " [cut]", True


def scope_of(record: dict) -> str | None:
    try:
        return json.loads(record.get("assessmentMethod") or "{}").get("scope")
    except json.JSONDecodeError:
        return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--reread", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    seed = json.loads(Path(args.plan).read_text(encoding="utf-8"))["seed"]
    reread = {row["dispositionId"] for g in json.loads(Path(args.reread).read_text(encoding="utf-8"))["workingGroups"]
              for row in g.get("rows", [])}

    chosen = []
    census = {}
    for wg in WGS:
        verified, pending, extra = [], [], []
        population = {"source_verified": 0, "pending": 0}
        for r in stream_dispositions(wg):
            status = r.get("evidenceStatus")
            if status in population:
                population[status] += 1
            keep = {k: r.get(k) for k in ("dispositionId", "dispositionCode", "targetTdocNumber", "evidencePath",
                                          "evidenceSha256", "evidenceLocator", "evidenceStatus")}
            keep["scope"] = scope_of(r)
            keep["wg"] = wg
            ident = r["dispositionId"]
            if status == "source_verified":
                verified.append((rank(seed, "", ident), keep))
            elif status == "pending":
                pending.append((rank(seed, "pending|", ident), keep))
            if ident in reread:
                extra.append(keep)
        verified.sort(key=lambda x: x[0])
        pending.sort(key=lambda x: x[0])
        sets = {}
        for _, k in verified[:VERIFIED_PER_WG]:
            sets.setdefault(k["dispositionId"], (k, []))[1].append("random_verified")
        for _, k in pending[:PENDING_PER_WG]:
            sets.setdefault(k["dispositionId"], (k, []))[1].append("random_pending")
        for k in extra:
            sets.setdefault(k["dispositionId"], (k, []))[1].append("reread_differences")
        chosen.extend(sets.values())
        census[wg] = {"population": population, "chosen": len(sets), "rereadFound": len(extra)}
        print(wg, census[wg], flush=True)

    texts: dict[str, list[str] | None] = {}
    packets, keys, skipped = [], {}, []
    for k, sets in chosen:
        path = ROOT / k["evidencePath"]
        m = LOCATOR.search(k["evidenceLocator"] or "")
        if not path.is_file() or path.suffix != ".docx" or not m:
            skipped.append([k["dispositionId"], "no_docx_or_locator"])
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != k["evidenceSha256"]:
            skipped.append([k["dispositionId"], "hash_differs"])
            continue
        if k["evidencePath"] not in texts:
            texts[k["evidencePath"]] = readable_blocks(path)
        blocks = texts[k["evidencePath"]]
        a, b = int(m.group(1)), int(m.group(2))
        shown, cut = [], False
        for i in range(max(0, a - CONTEXT), min(len(blocks), b + CONTEXT)):
            text, was_cut = cap(blocks[i], k["targetTdocNumber"])
            cut = cut or was_cut
            if text.strip():
                shown.append({"block": i, "cited": a <= i < b, "text": text})
        pid = rank(seed, "packet|", k["dispositionId"])[:12]
        packets.append({"packetId": pid, "wg": k["wg"], "target": k["targetTdocNumber"],
                        "report": path.name, "blocks": shown})
        keys[pid] = {"dispositionId": k["dispositionId"], "wg": k["wg"], "code": k["dispositionCode"],
                     "scope": k["scope"], "status": k["evidenceStatus"], "sets": sets, "blockCut": cut}

    packets.sort(key=lambda p: p["packetId"])
    out = Path(args.out)
    (out / "packets").mkdir(parents=True, exist_ok=True)
    parts = []
    for n in range(0, len(packets), PART_SIZE):
        name = f"part{n // PART_SIZE + 1:02d}"
        (out / "packets" / f"{name}.json").write_text(
            json.dumps({"packets": packets[n:n + PART_SIZE]}, ensure_ascii=False, indent=1), encoding="utf-8")
        parts.append(name)
    (out / "keys.json").write_text(json.dumps(keys, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "build_summary.json").write_text(json.dumps(
        {"census": census, "packets": len(packets), "parts": parts, "skipped": skipped}, indent=1), encoding="utf-8")
    print("packets", len(packets), "parts", len(parts), "skipped", len(skipped))


if __name__ == "__main__":
    main()
