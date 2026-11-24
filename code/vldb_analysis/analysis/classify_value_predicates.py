"""저장된 SQL 질의가 처분 기록의 두 값 칸(`scope` · `evidence_status`)에 건 조건을 전수로 분류한다 (모델 호출 없음).

질의 작성자는 표 정의만 받았고 칸에 저장된 값의 철자는 받지 않았다. 그래서 같은 조건을 여러 방식으로 적는다.
이 스크립트는 질의 글에서 그 칸만 참조하는 조건식을 떼어 내어, 저장된 값 각각을 넣었을 때 참이 되는지를
SQLite 로 직접 계산한다. 분류는 글의 생김새가 아니라 계산 결과로 정한다.

- accepts_target_only: 문항이 요구하는 값만 받아들인다.
- accepts_target_and_more: 요구하는 값과 다른 저장 값을 함께 받아들인다.
- rejects_target: 요구하는 값을 받아들이지 않는다.
- no_predicate: 그 칸에 조건을 걸지 않았다(칸을 아예 쓰지 않았거나 출력 칸으로만 썼다).
- mixed: 한 질의 안의 조건식들이 받아들이는 값 집합이 서로 다르다.
- not_isolated: 칸을 조건에 썼지만 그 칸만으로 계산되는 식을 떼어 내지 못했다.

조건식의 글 형태는 따로 적는다: pattern(LIKE · GLOB · INSTR), exact(= · IN), 그 밖(other).
채점은 `score_chain_eval.py` 의 `score` 를 그대로 쓴다.

사용: python3 -B classify_value_predicates.py --out <json>
"""
from __future__ import annotations

import argparse
import collections
import importlib
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
TRACK = "publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"
LOGS = ROOT / "logs" / TRACK
sys.path.insert(0, str(ROOT / "scripts" / TRACK))
score = importlib.import_module("score_chain_eval").score

ITEMS = [LOGS / "integration/items_final/gate/core/chain_items_admitted.jsonl",
         LOGS / "integration/items_final/gate/ran5/chain_items_admitted.jsonl"]
COLUMNS = {"scope": ("whole_target", ["whole_target", "undetermined", "subdocument"]),
           "evidence_status": ("source_verified", ["source_verified", "pending"])}
# 한 수준 안에서 조건식을 가르는 낱말. OR 는 가르지 않는다(OR 로 이은 대안은 한 조건이다).
SEPARATORS = re.compile(r"\b(?:and|where|on|having|when|then|else|end|select|from|join|union|group|order|limit|as|by|case)\b|,|;")
PATTERN_WORDS = re.compile(r"\b(?:like|glob|instr)\b")
EXACT_WORDS = re.compile(r"(?<![<>!=])=(?!=)|==|\bin\b")


def mask(sql: str) -> str:
    """문자열 상수와 주석을 같은 길이의 `~` 로 가린 소문자 글. 위치가 원문과 같다."""
    out, i, n = [], 0, len(sql)
    while i < n:
        c = sql[i]
        if c == "'":
            j = i + 1
            while j < n:
                if sql[j] == "'":
                    if j + 1 < n and sql[j + 1] == "'":
                        j += 2
                        continue
                    break
                j += 1
            out.append("~" * (min(j, n - 1) - i + 1))
            i = j + 1
        elif sql.startswith("--", i):
            j = sql.find("\n", i)
            j = n if j < 0 else j
            out.append("~" * (j - i))
            i = j
        else:
            out.append(c.lower())
            i += 1
    return "".join(out)


def groups(masked: str) -> list[tuple[int, int]]:
    """괄호 묶음의 (여는 자리, 닫는 자리) 목록."""
    stack, found = [], []
    for i, c in enumerate(masked):
        if c == "(":
            stack.append(i)
        elif c == ")" and stack:
            found.append((stack.pop(), i))
    return found


def segment(masked: str, lo: int, hi: int, at: int, inner: list[tuple[int, int]]) -> tuple[int, int]:
    """[lo, hi) 안에서 at 을 품고, 같은 수준의 가름 낱말 사이에 놓인 구간."""
    flat = list(masked[lo:hi])
    for a, b in inner:                      # 안쪽 괄호 묶음 속의 가름 낱말은 보지 않는다
        if lo <= a and b < hi:
            for k in range(a - lo + 1, b - lo):
                flat[k] = "~"
    text = "".join(flat)
    start, end = 0, len(text)
    for m in SEPARATORS.finditer(text):
        if m.end() <= at - lo:
            start = m.end()
        elif m.start() >= at - lo:
            end = m.start()
            break
    return lo + start, lo + end


def evaluate(db, fragment: str, column_re, values: list[str]):
    """조건식의 칸을 값으로 바꿔 계산한 결과. 그 칸만으로 계산되지 않으면 None."""
    masked = mask(fragment)
    pieces, last = [], 0
    for m in column_re.finditer(masked):
        pieces.append(fragment[last:m.start()])
        pieces.append(":v")
        last = m.end()
    pieces.append(fragment[last:])
    text = "".join(pieces).strip()
    if not text or ":v" not in text:
        return None
    results = []
    for value in values:
        try:
            row = db.execute(f"SELECT ({text})", {"v": value}).fetchone()
        except sqlite3.Error:
            return None
        results.append(row[0])
    if not all(r is None or isinstance(r, int) for r in results):
        return None                          # 값을 내는 식(출력 칸)이지 조건이 아니다
    return tuple(bool(r) for r in results)


def predicates(db, sql: str, column: str, values: list[str]) -> dict:
    masked = mask(sql)
    aliases = set(re.findall(rf"(?<![\w.])(?:\w+\.)?{column}\s+as\s+(\w+)", masked)) - {column}
    names = "|".join(sorted({column} | aliases, key=len, reverse=True))
    column_re = re.compile(rf"(?<![\w.])(?:\w+\.)?(?:{names})(?!\w)")
    occurrences = [m.start() for m in column_re.finditer(masked)]
    if not occurrences:
        return {"occurrences": 0, "found": [], "notIsolated": 0}
    all_groups = groups(masked)
    found, spans, not_isolated = [], set(), 0
    for at in occurrences:
        enclosing = sorted((g for g in all_groups if g[0] < at < g[1]), key=lambda g: g[1] - g[0])
        levels = [(g[0] + 1, g[1]) for g in enclosing] + [(0, len(masked))]
        best = None
        for lo, hi in levels:
            a, b = segment(masked, lo, hi, at, all_groups)
            result = evaluate(db, sql[a:b], column_re, values)
            if result is not None:
                best = (a, b, result)        # 바깥 수준일수록 넓다. 계산되는 가장 넓은 식을 쓴다
        if best is None:
            window = masked[max(0, at - 60):at + 80]
            if re.search(r"\b(?:like|glob|in|is|instr)\b|[=<>]", window[55:]):
                not_isolated += 1
            continue
        if (best[0], best[1]) in spans:
            continue
        spans.add((best[0], best[1]))
        text = masked[best[0]:best[1]]
        form = "pattern" if PATTERN_WORDS.search(text) else "exact" if EXACT_WORDS.search(text) else "other"
        found.append({"accepts": best[2], "form": form, "text": " ".join(sql[best[0]:best[1]].split())})
    return {"occurrences": len(occurrences), "found": found, "notIsolated": not_isolated}


def classify(info: dict, target_index: int = 0) -> tuple[str, str]:
    found = info["found"]
    if not found:
        return ("not_isolated" if info["notIsolated"] else "no_predicate"), "none"
    forms = {f["form"] for f in found}
    form = forms.pop() if len(forms) == 1 else "several"
    sets = {f["accepts"] for f in found}
    if len(sets) > 1:
        return "mixed", form
    accepts = next(iter(sets))
    if not accepts[target_index]:
        return "rejects_target", form
    if any(accepts[i] for i in range(len(accepts)) if i != target_index):
        return "accepts_target_and_more", form
    return "accepts_target_only", form


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    gold = {}
    for path in ITEMS:
        with path.open() as handle:
            for line in handle:
                item = json.loads(line)
                gold[item["id"]] = item
    sources = []
    for run in "ABCDEFGHIJ":
        for n in range(1, 6):
            sources.append(("opus_schema", f"run{run}", f"RAN{n}", LOGS / f"chain_eval/text2sql/RAN{n}_text2sql_run{run}.jsonl"))
    for n in range(1, 6):
        sources.append(("codex_schema", "single", f"RAN{n}", LOGS / f"chain_eval/codex/chain_sql_RAN{n}_codex.jsonl"))
    for mode in ("dom", "exp"):
        for n in range(1, 6):
            sources.append((f"codex_{mode}", "single", f"RAN{n}", LOGS / f"chain_eval/codex_v2/responses/RAN{n}_sql_{mode}_codex.jsonl"))
    db = sqlite3.connect(":memory:")
    budget = {"n": 0}

    def guard():
        budget["n"] += 1
        return 1 if budget["n"] > 200 else 0
    db.set_progress_handler(guard, 10000)
    rows, sessions = [], []
    for method, run, wg, path in sources:
        tally = collections.Counter()
        with path.open() as handle:
            for line in handle:
                record = json.loads(line)
                item = gold[record["id"]]
                attempts = [a for a in record.get("attempts", []) if a.get("sql")]
                sql = attempts[-1]["sql"] if attempts else ""
                exact = score(item["gold"], record.get("rows"))["exact"]
                entry = {"method": method, "run": run, "wg": wg, "id": record["id"], "family": item["family"], "exact": exact}
                for column, (target, values) in COLUMNS.items():
                    budget["n"] = 0
                    info = predicates(db, sql, column, values)
                    label, form = classify(info)
                    entry[column] = label
                    entry[column + "Form"] = form
                    entry[column + "Texts"] = sorted({f["text"] for f in info["found"]})
                rows.append(entry)
                tally[(entry["scope"], entry["scopeForm"])] += 1
        sessions.append({"method": method, "run": run, "wg": wg, "file": str(path.relative_to(ROOT)),
                         "scope": {f"{k[0]}|{k[1]}": v for k, v in sorted(tally.items())}})
    Path(args.out).write_text(json.dumps({"columns": COLUMNS, "rows": rows, "sessions": sessions}, ensure_ascii=False) + "\n")
    print("queries", len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
