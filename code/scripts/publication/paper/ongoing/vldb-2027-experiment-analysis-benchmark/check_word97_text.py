"""옛 .doc 판독기(`word97_text.doc_text`)가 LibreOffice 변환 + OOXML 판독과 같은 글을 내는지 표본으로 잰다.

TSG 총회 문서 묶음(`meetings/TSG_RAN/source/TSGR_*/{Docs,Report}/*.zip`) 바로 아래의 .doc 항목 가운데
`sha256(zip 경로 + 항목 이름)` 이 작은 차례로 `--sample` 개를 고른다. 문서마다

- 바로 읽기: `word97_text.doc_text` 의 글과 걸린 시간,
- 비교 기준: LibreOffice 로 docx 로 바꾼 뒤 `raw_source_text.word_text` 로 읽은 글과 변환 시간(문서 하나씩,
  `--timeout` 초를 넘으면 시간 초과로 센다)

을 얻어 두 글을 견준다. 견줌은 `[DEL]` 표지를 뺀 뒤 공백을 하나로 접고 `|` 를 공백으로 바꾼 글에서 한다.

- 줄 일치: 한쪽의 (정규화한) 줄이 다른 쪽 글 전체 안에 그대로 있는 비율 — 양쪽 방향.
- 낱말 재현: 기준 글 낱말 주머니 가운데 바로 읽은 글에도 있는 낱말의 비율(차례 무시).
- 지운 글: 양쪽 `[DEL]…[/DEL]` 안 글자 수.
- 다른 줄의 갈래: 기준 글에만 있는 줄 가운데, 줄 차례를 맞춘(`difflib`) 바로 읽은 표 행과 칸 수가 같고 다른 칸이
  모두 "바로 읽은 쪽은 비고 기준 쪽은 바로 위 행의 같은 칸과 같다"이면 세로 합친 칸의 되풀이로 센다(OOXML 판독이
  합친 칸 글을 아래 행마다 되풀이한다). 나머지는 그 밖으로 세고 다섯 줄까지 보인다.
- 수식 개체: 복합 파일 안 `Equation Native` 흐름 수(수식 편집기 3.0 · MathType 개체). 바로 읽기는 개체 안 수식을
  읽지 않는다.

결과: `logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/raw_source_route/word97_check.json`.
"""

from __future__ import annotations

import argparse
import collections
import difflib
import hashlib
import json
import re
import shutil
import statistics
import subprocess
import tempfile
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import raw_source_text as rst
import word97_text

ROOT = rst.ROOT
MEETINGS = Path("data/corpus/tsg/RAN/formal/meetings/TSG_RAN/source")
OUT = Path("logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/raw_source_route/word97_check.json")
DEL_SPAN = re.compile(re.escape(rst.DEL_OPEN) + r"(.*?)" + re.escape(rst.DEL_CLOSE), re.S)


def norm(text: str) -> str:
    text = text.replace(rst.DEL_OPEN, " ").replace(rst.DEL_CLOSE, " ").replace("|", " ")
    return " ".join(text.split())


def deleted_chars(text: str) -> int:
    return sum(len(m.group(1)) for m in DEL_SPAN.finditer(text))


def line_share(lines: list[str], other: str) -> tuple[int, int]:
    keys = [norm(line) for line in lines]
    keys = [k for k in keys if k]
    return sum(k in other for k in keys), len(keys)


def cells(line: str) -> list[str] | None:
    if not (line.startswith("| ") and line.endswith(" |")):
        return None
    return [norm(c) for c in line[2:-2].split(" | ")]


def classify_missing(reference: list[str], native: list[str]) -> tuple[int, int, list[str]]:
    """기준에만 있는 줄을 (세로 합친 칸 되풀이, 그 밖, 그 밖 보기) 로 가른다."""
    ref = [line for line in reference if norm(line)]
    nat = [line for line in native if norm(line)]
    native_text = norm("\n".join(nat))
    vmerge, other, shown = 0, 0, []
    matcher = difflib.SequenceMatcher(None, [norm(x) for x in ref], [norm(x) for x in nat], autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        for k in range(i1, i2):
            if norm(ref[k]) in native_text:
                continue
            explained = False
            j = j1 + (k - i1)
            if tag == "replace" and j < j2 and k > 0:
                r, n, above = cells(ref[k]), cells(nat[j]), cells(ref[k - 1])
                if r and n and above and len(r) == len(n) == len(above):
                    diff = [c for c in range(len(r)) if r[c] != n[c]]
                    explained = bool(diff) and all(not n[c] and r[c] == above[c] for c in diff)
            if explained:
                vmerge += 1
            else:
                other += 1
                if len(shown) < 5:
                    shown.append(norm(ref[k])[:160])
    return vmerge, other, shown


def sample_members(count: int) -> list[tuple[str, str]]:
    ranked = []
    seen = set()
    for path in sorted((ROOT / MEETINGS).glob("TSGR_*/*/*.zip")):
        stat = path.stat()
        if (stat.st_dev, stat.st_ino) in seen:
            continue
        seen.add((stat.st_dev, stat.st_ino))
        try:
            with zipfile.ZipFile(path) as archive:
                names = [i.filename for i in archive.infolist()
                         if not i.is_dir() and i.filename.lower().endswith(".doc") and "__MACOSX" not in i.filename]
        except (zipfile.BadZipFile, OSError):
            continue
        rel = str(path.relative_to(ROOT))
        for name in names:
            ranked.append((hashlib.sha256(f"{rel}\n{name}".encode()).hexdigest(), rel, name))
    ranked.sort()
    return [(rel, name) for _, rel, name in ranked[:count]]


def check(job: tuple[str, str, int, str]) -> dict:
    rel, name, timeout, scratch = job
    work = Path(tempfile.mkdtemp(prefix="word97-", dir=scratch))
    record = {"zip": rel, "member": name}
    try:
        with zipfile.ZipFile(ROOT / rel) as archive:
            data = archive.read(name)
        record["bytes"] = len(data)
        source = work / "m.doc"
        source.write_bytes(data)
        started = time.perf_counter()
        try:
            native = word97_text.doc_text(data)
            record["native"] = {"ok": True}
        except rst.ExtractError as error:
            native = ""
            record["native"] = {"ok": False, "reason": error.reason, "detail": error.detail}
        except Exception as error:  # 판독기의 예상 밖 실패도 그대로 센다
            native = ""
            record["native"] = {"ok": False, "reason": "예외", "detail": f"{type(error).__name__}: {error}"[:200]}
        record["native"]["seconds"] = round(time.perf_counter() - started, 4)
        record["native"]["chars"] = len(native)
        try:
            record["equationObjects"] = word97_text.Compound(data).stream_names.count("equation native")
        except rst.ExtractError:
            record["equationObjects"] = None
        started = time.perf_counter()
        profile = work / "profile"
        converted = rst.convert_legacy([source], work / "out", profile, timeout)
        seconds = time.perf_counter() - started
        record["libreoffice"] = {"seconds": round(seconds, 2)}
        if source not in converted:
            record["libreoffice"]["ok"] = False
            record["libreoffice"]["reason"] = "변환 시간 초과" if seconds >= timeout else "변환 실패"
            return record
        try:
            reference = rst.word_text(converted[source])
        except rst.ExtractError as error:
            record["libreoffice"].update(ok=False, reason=error.reason)
            return record
        record["libreoffice"].update(ok=True, chars=len(reference))
        if not record["native"]["ok"]:
            return record
        native_norm, reference_norm = norm(native), norm(reference)
        found, total = line_share(reference.split("\n"), native_norm)
        back, back_total = line_share(native.split("\n"), reference_norm)
        ref_words = collections.Counter(reference_norm.split())
        nat_words = collections.Counter(native_norm.split())
        common = sum((ref_words & nat_words).values())
        record["compare"] = {
            "referenceLinesInNative": [found, total],
            "nativeLinesInReference": [back, back_total],
            "referenceWordsInNative": [common, sum(ref_words.values())],
            "nativeWords": sum(nat_words.values()),
            "deletedCharsReference": deleted_chars(reference),
            "deletedCharsNative": deleted_chars(native),
            "identicalNormalized": native_norm == reference_norm,
        }
        vmerge, other, shown = classify_missing(reference.split("\n"), native.split("\n"))
        record["compare"].update(missingVerticalMerge=vmerge, missingOther=other)
        if shown:
            record["compare"]["missingOtherExamples"] = shown
        return record
    finally:
        subprocess.run(["pkill", "-f", f"UserInstallation=file://{work / 'profile'}"], check=False)
        shutil.rmtree(work, ignore_errors=True)


def summarize(records: list[dict]) -> dict:
    compared = [r for r in records if "compare" in r]

    def total(key: str, index: int) -> int:
        return sum(r["compare"][key][index] for r in compared)

    lo_ok = [r["libreoffice"]["seconds"] for r in records if r["libreoffice"].get("ok")]
    lo_all = [r["libreoffice"]["seconds"] for r in records]
    native = [r["native"]["seconds"] for r in records]
    return {
        "documents": len(records),
        "nativeOk": sum(r["native"]["ok"] for r in records),
        "nativeFailures": collections.Counter(r["native"].get("reason") for r in records
                                              if not r["native"]["ok"]).most_common(),
        "libreofficeOk": len(lo_ok),
        "libreofficeFailures": collections.Counter(r["libreoffice"].get("reason") for r in records
                                                   if not r["libreoffice"].get("ok")).most_common(),
        "compared": len(compared),
        "identicalNormalized": sum(r["compare"]["identicalNormalized"] for r in compared),
        "referenceLinesInNative": [total("referenceLinesInNative", 0), total("referenceLinesInNative", 1)],
        "nativeLinesInReference": [total("nativeLinesInReference", 0), total("nativeLinesInReference", 1)],
        "referenceWordsInNative": [total("referenceWordsInNative", 0), total("referenceWordsInNative", 1)],
        "nativeWords": sum(r["compare"]["nativeWords"] for r in compared),
        "deletedCharsReference": sum(r["compare"]["deletedCharsReference"] for r in compared),
        "deletedCharsNative": sum(r["compare"]["deletedCharsNative"] for r in compared),
        "missingVerticalMerge": sum(r["compare"]["missingVerticalMerge"] for r in compared),
        "missingOther": sum(r["compare"]["missingOther"] for r in compared),
        "documentsWithMissingOther": sum(r["compare"]["missingOther"] > 0 for r in compared),
        "documentsWithEquationObjects": sum(bool(r.get("equationObjects")) for r in records),
        "missingOtherInDocumentsWithEquationObjects": sum(r["compare"]["missingOther"] for r in compared
                                                          if r.get("equationObjects")),
        "nativeSeconds": {"total": round(sum(native), 3), "median": round(statistics.median(native), 4),
                          "max": round(max(native), 4)},
        "libreofficeSeconds": {"totalAll": round(sum(lo_all), 1), "medianAll": round(statistics.median(lo_all), 2),
                               "maxAll": round(max(lo_all), 1),
                               "atLeast60s": sum(s >= 60 for s in lo_all)},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sample", type=int, default=48)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--timeout", type=int, default=300, help="LibreOffice 문서 하나 변환 제한(초)")
    parser.add_argument("--scratch", required=True)
    args = parser.parse_args()
    members = sample_members(args.sample)
    jobs = [(rel, name, args.timeout, args.scratch) for rel, name in members]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(check, jobs))
    result = {
        "rule": {"sample": "TSG 총회 zip 바로 아래 .doc 항목, sha256(zip 경로 + '\\n' + 항목 이름) 작은 차례",
                 "reference": "LibreOffice --convert-to docx 뒤 raw_source_text.word_text",
                 "normalize": "[DEL]/[/DEL] 표지 빼기, '|' → 공백, 공백 접기",
                 "lineMatch": "정규화한 줄이 다른 쪽 정규화 글 전체의 부분 문자열",
                 "timeoutSeconds": args.timeout},
        "summary": summarize(records),
        "documents": records,
    }
    out = ROOT / OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(result["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
