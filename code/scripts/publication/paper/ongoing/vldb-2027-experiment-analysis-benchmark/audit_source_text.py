"""글 색인 청크 본문이 원본 문서의 글자 그대로인지, 기록에서 만든 글인지 가려 `source_text_audit.json` 에 쓴다.

원본 글 조건(raw-source)에는 원본 문서의 글자만 들어가야 한다. 이 스크립트는 두 가지를 적는다.

1. 만든 자리: 세 모음(`ran{N}_resolution_chunks` · `ran{N}_cr_chunks` · `ran{N}_tdoc_chunks`)을 만든 코드의
   파일:줄. 줄마다 기대한 글이 그 줄에 실제로 있는지 실행 때 다시 읽어 확인하고, 줄의 글을 함께 남긴다.
2. 대조: 모음 종류마다 WG 별로 청크를 몇 개씩 고정 규칙(청크 ID 의 SHA-256 오름차순)으로 골라, 원본 파일
   (data/corpus 아래 zip · docx)에서 꺼낸 글과 줄 단위로 맞춰 본다. `raw_source_text.raw_chunk_text` 로
   걷어 낸 줄은 따로 세고, 그 줄이 원본에 없다는 것도 확인한다.

맞추는 규칙: 양쪽 모두 `[DEL]` · `[/DEL]` 표지를 지우고(지운 글은 남긴다) 표의 칸 구분 `|` 를 빈칸으로 바꾼 뒤
빈칸을 하나로 줄인다. 청크의 줄 하나가 원본 글 안에 부분 문자열로 들어 있으면 일치로 센다. 일치하지 않는 줄은
6 낱말 조각 가운데 원본에 있는 조각의 비율을 함께 적는다.

사용:
    PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark \\
        .venv/bin/python scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/audit_source_text.py
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sqlite3
import tempfile
import zipfile
from pathlib import Path

import raw_source_text as rst

ROOT = Path(__file__).resolve().parents[5]
TRACK = Path("logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark")
INDEX_DIR = TRACK / "text_route_ceiling/index"
CORPUS = Path("data/corpus/tsg/RAN/formal")
OUT = TRACK / "final/raw_source_route/source_text_audit.json"
SHINGLE = 6

# 만든 자리. (파일, 줄, 그 줄에 있어야 할 글, 뜻). 줄 번호는 실행 때 다시 확인한다.
BUILDERS = {
    "cr_chunks": [
        ("scripts/tsg/RAN/formal/RAN1/phase-8/cr-parser/01_parse_cr_chunks.py", 830,
         'f"[CR {cr_number} for {spec_number}]\\n"', "헤더 청크 첫 줄: CR 번호 · 규격은 기록 필드"),
        ("scripts/tsg/RAN/formal/RAN1/phase-8/cr-parser/01_parse_cr_chunks.py", 838,
         'text += f"\\nChange text: {body_snippet}"', "전략 A 헤더에 붙이는 이름표(양식에 없는 글)"),
        ("scripts/tsg/RAN/formal/RAN1/phase-8/cr-parser/01_parse_cr_chunks.py", 916,
         'prefix = f"[CR {cr_number} | {spec_number} | Clauses: {clauses_str}]"', "본문 청크 표지(전략 B)"),
        ("scripts/tsg/RAN/formal/RAN1/phase-8/cr-parser/01_parse_cr_chunks.py", 940,
         'prefix = f"[CR {cr_number} | {spec_number} | Preamble]"', "본문 청크 표지(머리말)"),
        ("scripts/tsg/RAN/formal/RAN1/phase-8/cr-parser/01_parse_cr_chunks.py", 949,
         'prefix = f"[CR {cr_number} | {spec_number} | Section {h.section_number}]"', "본문 청크 표지(절)"),
        ("scripts/tsg/RAN/formal/RAN1/phase-8/cr-parser/01_parse_cr_chunks.py", 977,
         'prefix = f"[CR {cr_number} | {spec_number} | Part {i+1}/{total}]"', "본문 청크 표지(전략 D)"),
        ("scripts/tsg/RAN/formal/RAN1/phase-8/cr-parser/01_parse_cr_chunks.py", 1118,
         "cr_number = tsg_cr_decision.sheet_cr_label(cr_number, tdoc_number, pack_id)",
         "표지의 CR 번호는 TSG 시트 기록에서 온다"),
        ("scripts/tsg/RAN/formal/RAN1/phase-8/cr-parser/01_parse_cr_chunks.py", 1126,
         'reason = cr_doc.get("reason_for_change", "") or ""', "헤더 값은 Phase-4 cr_documents.json"),
        ("scripts/tsg/RAN/formal/RAN1/phase-4/cr-parser/02_parse_cr_documents.py", 362,
         'result.reason_for_change = cr_form_slot.form_value(cr_table, "reason for change")',
         "Phase-4 값은 같은 CR 문서 표지 양식의 칸 글"),
        ("scripts/tsg/RAN/formal/RAN4/phase-8/cr-parser/01_parse_cr_chunks.py", 953,
         'prefix = f"[CR {cr_number} for {spec_number}] {title}\\nSection {h.section_number}"',
         "RAN4 본문 표지: 제목 줄 + 절 줄"),
        ("scripts/tsg/RAN/formal/RAN4/phase-8/cr-parser/01_parse_cr_chunks.py", 985,
         'prefix = f"[CR {cr_number} for {spec_number}] {title}\\nPart {i+1}/{total}"',
         "RAN4 본문 표지: 제목 줄 + 조각 줄"),
        ("scripts/tsg/RAN/formal/RAN5/phase-8/cr-parser/01_parse_cr_chunks.py", 851,
         'parts.append(f"Title: {form.title}")', "RAN5 헤더는 같은 문서 표지 양식의 칸 글(extract_cr_form)"),
        ("scripts/tsg/RAN/formal/RAN5/phase-8/cr-parser/01_parse_cr_chunks.py", 748,
         'current_body.append(f"[Table] {text}")', "RAN5 표 제목 문단 머리말(서식에서 붙임)"),
        ("scripts/tsg/RAN/formal/RAN5/phase-8/cr-parser/01_parse_cr_chunks.py", 1024,
         'header_text = f"{header_text}\\nChange text: {body_text}"', "RAN5 전략 A 이름표"),
    ],
    "tdoc_chunks": [
        ("scripts/tsg/RAN/formal/RAN1/phase-6/qdrant/02_load_qdrant.py", 429,
         '"content": chunk.get("content", ""),', "적재 글은 파서가 만든 chunks.json 의 content"),
        ("scripts/tsg/RAN/formal/RAN1/phase-6/tdoc-parser/parse_tdoc_lib.py", 396,
         "def _region_marks(", "표지 · 목차 · 참고문헌 구역은 청크에서 뺀다"),
        ("scripts/tsg/RAN/formal/RAN1/phase-6/tdoc-parser/parse_tdoc_lib.py", 481,
         '_CR_FORM_FIELDS = {"reasonforchange": "Reason for change"', "CR 양식 칸은 `이름: 값` 줄로 다시 쓴다"),
        ("scripts/tsg/RAN/formal/RAN1/phase-6/tdoc-parser/parse_tdoc_lib.py", 574,
         "latex: str", "수식은 OMML 을 LaTeX 로 바꿔 싣는다(05_enhance_equations.py)"),
    ],
    "resolution_chunks": [
        ("scripts/tsg/RAN/email/RAN1/phase-3/qdrant/01_load_resolution_chunks.py", None,
         "resolution_vectors", "다섯 WG 적재기가 공용 모듈을 부른다"),
        ("scripts/common/common/resolution_vectors.py", 29, "SOURCE_QUERY", "글은 Neo4j Resolution.content"),
        ("scripts/common/common/resolution_vectors.py", 74, "split_giant_section_v2", "content 를 2000 자 목표로 나눈다"),
        ("scripts/tsg/RAN/formal/common/document_decision_source.py", 179,
         "'content': '\\n'.join(texts[start:index + 1])", "문서 처분 사건: 회의록 블록 글 그대로"),
        ("scripts/tsg/RAN/formal/common/document_decision_source.py", 358,
         "content = '\\n'.join(before + [header_quote, row_quote] + after)",
         "부록 표 사건: 회의록 표의 머리 행과 해당 행을 칸 그대로 `|` 로 잇는다"),
    ],
}


# 모음마다 원본 글 조건에 넣는가와 그 까닭. 까닭은 BUILDERS 의 파일:줄이 보이는 동작이고, 수치는 실행 때
# 대조한 `summary` 에서 붙인다.
VERDICTS = {
    "tdoc_chunks": ("admit", "기고문 원본 문서의 문단 글이다. 표지 · 목차 · 참고문헌 구역은 빠지고, CR 양식 칸은 같은 "
                    "문서의 칸 이름과 칸 글을 `이름: 값` 한 줄로 잇고, OMML 수식은 LaTeX 로 바뀐다. 기록 필드에서 "
                    "만든 줄은 없다."),
    "cr_chunks": ("admit after stripping", "본문은 CR 문서의 글이지만, `[CR 번호 for 규격]` 표지 줄과 RAN4 표지 둘째 "
                  "줄 · `Change text: ` 이름표 · RAN5 `[Table] ` 머리말은 기록 필드나 서식에서 만든 글이다. "
                  "`raw_source_text.raw_chunk_text` 로 걷어 낸 나머지만 넣는다."),
    "resolution_chunks": ("admit", "Neo4j Resolution.content 이고, 그 글은 회의록 블록 · 회의록 표의 머리 행과 해당 "
                          "행을 칸 그대로 이은 것이다. 기록 필드에서 만든 줄은 없다."),
}


def verdicts(summary: dict) -> dict:
    out = {}
    for kind, (decision, reason) in VERDICTS.items():
        row = summary[kind]
        out[kind] = {"decision": decision, "reason": reason,
                     "linesVerbatim": f"{row['linesVerbatim']}/{row['lines']}",
                     "charsVerbatim": f"{row['charsVerbatim']}/{row['chars']}",
                     "chunksAllLinesVerbatim": f"{row['chunksAllLinesVerbatim']}/{row['chunks']}",
                     "strippedLinesFoundInSource": f"{row['removedFoundInSource']}/{row['removedLines']}"}
    return out


def builder_evidence() -> dict:
    out = {}
    for kind, rows in BUILDERS.items():
        checked = []
        for path, line, expected, meaning in rows:
            lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
            if line is None:
                hits = [i + 1 for i, text in enumerate(lines) if expected in text]
                line = hits[0] if hits else None
            actual = lines[line - 1].strip() if line else ""
            checked.append({"file": path, "line": line, "meaning": meaning, "lineText": actual[:240],
                            "expectedPresent": bool(line) and expected in lines[line - 1]})
        out[kind] = checked
    return out


def norm(text: str) -> str:
    text = text.replace(rst.DEL_OPEN, " ").replace(rst.DEL_CLOSE, " ").replace("|", " ")
    return re.sub(r"\s+", " ", text).strip()


def shingles(words: list[str]) -> set[tuple[str, ...]]:
    return {tuple(words[i:i + SHINGLE]) for i in range(max(1, len(words) - SHINGLE + 1))}


class Source:
    """원본 파일 하나(zip 이면 안의 글 문서 전부)를 맞춰 보기 좋은 글로 바꿔 둔다."""

    def __init__(self, path: Path, scratch: Path):
        self.path = path
        self.members: list[str] = []
        self.failed: list[dict] = []
        parts = []
        if path.suffix.lower() == ".zip":
            self._walk_zip(path.name, path.read_bytes(), parts, scratch)
        else:
            self._one(path.name, path.read_bytes(), parts, scratch)
        self.text = norm("\n".join(parts))
        self._shingles = None

    def _walk_zip(self, name: str, data: bytes, parts: list[str], scratch: Path) -> None:
        try:
            package = zipfile.ZipFile(io.BytesIO(data))
        except zipfile.BadZipFile:
            self.failed.append({"member": name, "reason": "zip 아님"})
            return
        for info in package.infolist():
            if info.is_dir():
                continue
            member = f"{name}/{info.filename}"
            payload = package.read(info)
            if rst.suffix(info.filename) in rst.NESTED:
                self._walk_zip(member, payload, parts, scratch)
            else:
                self._one(member, payload, parts, scratch)

    def _one(self, name: str, data: bytes, parts: list[str], scratch: Path) -> None:
        ext = rst.suffix(name)
        stem = hashlib.sha256(name.encode()).hexdigest()[:16]
        local = scratch / f"{stem}{ext}"
        local.write_bytes(data)
        try:
            if ext in rst.LEGACY:
                converted = rst.convert_legacy([local], scratch, scratch / "profile", timeout=300)
                if local not in converted:
                    raise rst.ExtractError("옛 형식 변환 실패", ext)
                local = converted[local]
            parts.append(rst.file_text(local))
            self.members.append(name)
        except rst.ExtractError as error:
            self.failed.append({"member": name, "reason": error.reason})

    def coverage(self, line: str) -> float:
        if self._shingles is None:
            self._shingles = shingles(self.text.split(" "))
        pieces = shingles(line.split(" "))
        return sum(piece in self._shingles for piece in pieces) / len(pieces)


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_absolute() else str(path)


def locate_document(wg: int, tdoc: str, tree: str) -> list[Path]:
    if tree == "cr":
        found = sorted((ROOT / CORPUS / f"change-requests/RAN{wg}/source").glob(f"*/wg_docs/{tdoc}.zip"))
        found = found or sorted((ROOT / CORPUS / f"change-requests/RAN{wg}/source").glob(f"**/{tdoc}.zip"))
        # CR 트리에 받아 두지 않은 CR 은 작업반 회의 문서 폴더에 같은 번호의 기고문으로 있다.
        return found or sorted((ROOT / CORPUS / f"meetings/RAN{wg}/source").glob(f"*/Docs/{tdoc}.zip"))
    return sorted((ROOT / CORPUS / f"meetings/RAN{wg}/source").glob(f"*/Docs/{tdoc}.zip"))


def meeting_token(resolution_id: str) -> str:
    """결정 ID(`AGR-104-e-7.2.4-013` · `DOC-109bis-e-R2-…`)에서 회의 표기를 꺼낸다."""
    body = resolution_id.split("-", 1)[1]
    match = re.match(r"(\d+[A-Za-z]*(?:-e)?)(?=-)", body)
    return match.group(1).lower() if match else ""


def locate_report(wg: int, resolution_id: str) -> list[Path]:
    token = meeting_token(resolution_id)
    found = []
    for meeting in sorted((ROOT / CORPUS / f"meetings/RAN{wg}/source").iterdir()):
        name = meeting.name.split("_", 1)[1].replace("_", "-").lower() if "_" in meeting.name else ""
        if not (name == token or name.startswith(token + "-")):
            continue
        for folder in ("Report", "Reports"):
            base = meeting / folder
            if base.is_dir():
                found.extend(sorted(p for p in base.rglob("*") if p.is_file()
                                    and rst.suffix(p.name) in (".zip", ".docx", ".doc")))
    return found


def candidates(db: sqlite3.Connection, collection: str, where: str = "") -> list[tuple]:
    rows = db.execute(f"select chunk_id, meta, text from docs where collection=? {where}", (collection,))
    return sorted(rows, key=lambda row: hashlib.sha256(row[0].encode()).hexdigest())


def check_chunk(collection: str, chunk_id: str, text: str, sources: list[Source]) -> dict:
    clean, removed = rst.raw_chunk_text(collection, chunk_id, text)
    lines = [norm(line) for line in clean.split("\n")]
    lines = [line for line in lines if line]
    best = None
    for source in sources:
        hit = sum(line in source.text for line in lines)
        if best is None or hit > best[0]:
            best = (hit, source)
    hit, source = best
    unmatched = [line for line in lines if line not in source.text]
    return {
        "chunkId": chunk_id,
        "source": relative(source.path),
        "sourceMembersRead": source.members,
        "sourceMembersFailed": source.failed,
        "lines": len(lines),
        "linesVerbatim": hit,
        "chars": sum(map(len, lines)),
        "charsVerbatim": sum(len(line) for line in lines if line in source.text),
        "unmatched": [{"excerpt": line[:160], "chars": len(line),
                       "shingleCoverage": round(source.coverage(line), 3)} for line in unmatched[:8]],
        "unmatchedCount": len(unmatched),
        "removedLines": removed,
        "removedFoundInSource": sum(norm(line) in source.text for line in removed if norm(line)),
    }


def audit(wgs: list[int], per: int, tries: int, scratch: Path) -> dict:
    samples = {"tdoc_chunks": [], "cr_chunks": [], "resolution_chunks": []}
    misses = {key: [] for key in samples}
    cache: dict[Path, Source] = {}
    for wg in wgs:
        db = sqlite3.connect(f"file:{ROOT / INDEX_DIR / f'ran{wg}.sqlite3'}?mode=ro", uri=True)
        plans = [
            ("tdoc_chunks", f"ran{wg}_tdoc_chunks", "and rowid % 997 = 0", per),
            ("cr_chunks", f"ran{wg}_cr_chunks", "and chunk_id like '%-header'", per),
            ("cr_chunks", f"ran{wg}_cr_chunks", "and chunk_id not like '%-header' and rowid % 13 = 0", per),
            ("resolution_chunks", f"ran{wg}_resolution_chunks", "and rowid % 7 = 0", per),
        ]
        # 파서가 다시 쓴 CR 양식 칸(`Reason for change: 값`)을 담은 기고문 청크를 한 개씩 더 본다.
        plans.append(("tdoc_chunks", f"ran{wg}_tdoc_chunks",
                      "and rowid % 101 = 0 and substr(text, 1, 18) = 'Reason for change:'", 1))
        if wg != 5:
            # 표지가 청크 가운데에도 오는 본문 청크(절을 이어 붙인 청크)를 한 개씩 더 본다.
            plans.append(("cr_chunks", f"ran{wg}_cr_chunks",
                          "and chunk_id not like '%-header' and instr(substr(text, 2), char(10) || '[CR ') > 0 "
                          "and rowid % 11 = 0", 1))
        else:
            # RAN5 의 표 제목 머리말(`[Table] `)을 단 본문 청크를 한 개 더 본다.
            plans.append(("cr_chunks", f"ran{wg}_cr_chunks",
                          "and chunk_id not like '%-header' and instr(text, '[Table] ') > 0 and rowid % 11 = 0", 1))
        for kind, collection, where, want in plans:
            taken = 0
            for chunk_id, meta, text in candidates(db, collection, where)[:tries]:
                meta = json.loads(meta)
                if kind == "resolution_chunks":
                    paths = locate_report(wg, meta["resolutionId"])
                else:
                    paths = locate_document(wg, meta["tdocNumber"], "cr" if kind == "cr_chunks" else "tdoc")
                if not paths:
                    misses[kind].append({"chunkId": chunk_id, "reason": "원본 파일을 찾지 못함"})
                    continue
                sources = [cache.setdefault(path, Source(path, scratch)) if path not in cache else cache[path]
                           for path in paths]
                if not any(source.text for source in sources):
                    misses[kind].append({"chunkId": chunk_id, "reason": "원본에서 글을 꺼내지 못함",
                                         "failed": [f for s in sources for f in s.failed]})
                    continue
                record = check_chunk(collection, chunk_id, text, sources)
                record["wg"] = f"RAN{wg}"
                samples[kind].append(record)
                taken += 1
                if taken == want:
                    break
        db.close()
    summary = {}
    for kind, records in samples.items():
        summary[kind] = {
            "chunks": len(records),
            "lines": sum(r["lines"] for r in records),
            "linesVerbatim": sum(r["linesVerbatim"] for r in records),
            "chars": sum(r["chars"] for r in records),
            "charsVerbatim": sum(r["charsVerbatim"] for r in records),
            "chunksAllLinesVerbatim": sum(r["unmatchedCount"] == 0 for r in records),
            "removedLines": sum(len(r["removedLines"]) for r in records),
            "removedFoundInSource": sum(r["removedFoundInSource"] for r in records),
            "locateMisses": len(misses[kind]),
        }
    return {"summary": summary, "samples": samples, "locateMisses": misses}


def label_scan(wgs: list[int]) -> dict:
    """걷어 낼 표지 규칙이 CR 청크 전체에서 몇 줄을 걷는지, 그 줄의 CR 번호가 청크 기록의 CR 번호와 같은지 센다."""
    out = {}
    for wg in wgs:
        db = sqlite3.connect(f"file:{ROOT / INDEX_DIR / f'ran{wg}.sqlite3'}?mode=ro", uri=True)
        chunks = removed = same = other = 0
        for chunk_id, meta, text in db.execute(
                "select chunk_id, meta, text from docs where collection=?", (f"ran{wg}_cr_chunks",)):
            chunks += 1
            cr = json.loads(meta).get("crNumber") or ""
            _, lines = rst.raw_chunk_text(f"ran{wg}_cr_chunks", chunk_id, text)
            removed += len(lines)
            for line in lines:
                match = rst.CR_LABEL.fullmatch(line)
                if match:
                    if match.group("cr") == cr:
                        same += 1
                    else:
                        other += 1
        out[f"RAN{wg}"] = {"chunks": chunks, "removedLines": removed, "labelLinesSameCrAsRecord": same,
                           "labelLinesOtherCr": other}
        db.close()
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--wg", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    parser.add_argument("--per", type=int, default=2, help="WG · 모음 갈래마다 맞춰 볼 청크 수")
    parser.add_argument("--tries", type=int, default=40, help="원본을 찾지 못할 때 다음 후보로 넘어가는 최대 수")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="source-audit-") as scratch:
        result = {
            "rule": {"normalize": "remove [DEL]/[/DEL] markers, '|' -> space, collapse whitespace",
                     "verbatimLine": "normalized chunk line is a substring of the normalized source text",
                     "shingleWords": SHINGLE, "sampleOrder": "sha256(chunkId) ascending within a rowid stride"},
            "builders": builder_evidence(),
            "labelScan": label_scan(args.wg),
            **audit(args.wg, args.per, args.tries, Path(scratch)),
        }
    result["verdicts"] = verdicts(result["summary"])
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"builders": {k: [r["expectedPresent"] for r in v] for k, v in result["builders"].items()},
                      "summary": result["summary"], "verdicts": result["verdicts"]}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
