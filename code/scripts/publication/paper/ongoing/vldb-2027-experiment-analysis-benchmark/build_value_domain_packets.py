"""질의 작성 묶음(packet)의 과제 문장 끝에 저장값의 값 영역 설명을 덧붙인 새 묶음을 만든다 (모델 호출 없음).

그래프 묶음은 과제 문장에 적힌 (레이블, 속성)마다, 관계형 묶음은 내보내기 파일의 (표, 열)마다 같은 절차로 값 영역을
잰다. 그래프는 읽기 전용 세션으로, 관계형 파일은 읽기 전용으로 연다.

1. 모든 WG · 두 언어의 (소유자, 이름)마다 서로 다른 값의 수를 센다. 문턱값은 이 분포에서 고른다: 서로 다른 값의 수를
   log10 으로 바꾼 경험적 누적분포와, 그 양 끝을 잇는 직선 사이의 세로 거리가 가장 큰 점(Kneedle 무릎점)의 값이다.
   두 언어 각각의 무릎점과 합친 분포의 무릎점을 함께 적고, 합친 분포의 값을 두 언어에 똑같이 쓴다.
2. 값 이름 길이 상한도 같은 방식으로 고른다: 서로 다른 값이 문턱값 이하인 문자열 (소유자, 이름)마다 가장 긴 값의
   길이를 재고, 그 log10 누적분포의 무릎점을 쓴다. 길이가 이보다 긴 값은 이름표가 아니라 글이나 긴 식별자로 본다.
3. 서로 다른 값이 문턱값 이하이고, 문자열이면 가장 긴 값도 길이 상한 이하일 때 값 전부를 기록 수와 함께 적는다.
   아니면 값 종류(정수 · 식별자 · 글)에 맞는 형식 설명(정수는 범위, 식별자는 길이 · 글자 종류 · 모양, 글은 길이)과
   시드로 뽑은 예시 세 개를 적는다. 목록 값은 원소를 같은 절차로 잰다. 식별자는 공백 없는 문자열, 글은 공백이 있는
   문자열이다. 모양은 숫자를 `9` 로 바꾸고 숫자가 없는 값은 글자도 `A`/`a` 로 바꾼 꼴이며, 서로 다른 모양이 문턱값
   이하일 때만 모두 적는다. 넘으면 글자도 모두 `A`/`a` 로 바꾼 꼴로 다시 세고, 그래도 넘으면 모양은 적지 않는다.
4. 예시에서는 667 문항의 정답 행 칸 값 · 시작점(anchor) 값과 같거나 그것을 낱말 경계로 품은 값, 그리고 문항 문장
   어디에든 낱말 경계로 나타나는 값을 모두 뺀다. 소유자 · 이름마다 뺀 값의 수를 이유별로 적는다. 값 전부를 적는
   목록에 정답 · 문항 값이 몇 개 들어 있는지도 따로 적는다.
5. 예시가 길이 상한보다 길면 상한에서 자르고 원래 길이를 함께 적는다.
6. 그래프 자체 IRI(w3id.org 아래)의 이름공간 낱말은 원래 묶음에 없는 저장소 이름이라 `<ns>` 로 바꾸어 적고, 바꾼 수를
   기록한다. 이 값들은 정답 · 문항 어디에도 쓰이지 않는다.

같은 정보를 두 언어에 준다: 문턱값 · 종류 판정 · 빼는 규칙 · 예시 수가 같다.

사용: python3 build_value_domain_packets.py --cypher-packets <dir> --sql-packets <dir> --sqlite-dir <dir> \
          --items <jsonl> [<jsonl> ...] --bolt RAN1=bolt://localhost:7687 [--bolt ...] --out-dir <dir> [--seed 20271]
`<dir>/RAN{N}_schema.json` 을 읽어 `<out-dir>/{cypher,sql}_RAN{N}.json` 과 `<out-dir>/domain_report.json` 을 쓴다.
저장소 루트에서 `PYTHONPATH=scripts/common:scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark` 로 실행한다.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import random
import re
import sqlite3
import statistics
from pathlib import Path

from neo4j import GraphDatabase

from common.credentials import neo4j_auth
from crosscheck_chain_items_graph import graph_key

SCHEMA_LINE = re.compile(r"^\(:(\w+) \{([^}]*)\}\)$")
RUN = re.compile(r"[a-z0-9]+")
EDGE = re.compile(r"^[^a-z0-9]+|[^a-z0-9]+$")
# 숫자 모양(`w9id`)으로 바뀐 꼴도 함께 잡는다.
NAMESPACE_WORD = re.compile(r"(?<=w[39]id\.org/)[^#/\s\"]+(?=#)")
EXAMPLES = 3


class LeakIndex:
    """정답 칸 · 시작점 값과 문항 문장으로 예시 후보가 새는지 본다. 비교는 소문자로, 낱말 경계는 [a-z0-9] 밖의 글자다."""

    def __init__(self, terms: set[str], questions: list[str]):
        self.terms = {t.lower().strip() for t in terms if t and RUN.search(t.lower())}
        self.cores = {EDGE.sub("", t) for t in self.terms}
        self.by_first: dict[str, set[str]] = collections.defaultdict(set)
        for core in self.cores:
            self.by_first[RUN.match(core).group()].add(core)
        self.slices: set[str] = set()
        for question in questions:
            text = question.lower()
            spans = [m.span() for m in RUN.finditer(text)]
            for i in range(len(spans)):
                for j in range(i, len(spans)):
                    self.slices.add(text[spans[i][0]:spans[j][1]])

    def reason(self, value) -> str | None:
        text = str(value).lower().strip()
        if not RUN.search(text):
            return None
        core = EDGE.sub("", text)
        if text in self.terms or core in self.cores:
            return "equalsGoldOrAnchor"
        if core in self.slices:
            return "occursInQuestion"
        for run in RUN.finditer(text):
            for term in self.by_first.get(run.group(), ()):
                if text.startswith(term, run.start()):
                    end = run.start() + len(term)
                    if end == len(text) or not RUN.match(text[end]):
                        return "containsGoldOrAnchor"
        return None


def kneedle(values: list[int]) -> dict:
    """양의 정수 값들의 log10 경험적 누적분포에서 양 끝을 잇는 직선과의 세로 거리가 가장 큰 값."""
    ordered = sorted(v for v in values if v >= 1)
    logs = [math.log10(v) for v in ordered]
    low, high = logs[0], logs[-1]
    best = None
    for i, value in enumerate(ordered):
        if i + 1 < len(ordered) and ordered[i + 1] == value:
            continue
        share = (i + 1) / len(ordered)
        distance = share - ((logs[i] - low) / (high - low) if high > low else 0.0)
        if best is None or distance > best["distance"]:
            best = {"threshold": value, "ecdfAtThreshold": round(share, 4), "distance": round(distance, 4)}
    return {**best, "properties": len(ordered)}


def cypher_pairs(task: str) -> list[tuple[str, str]]:
    return [(m.group(1), name.strip()) for line in task.splitlines() if (m := SCHEMA_LINE.match(line.strip()))
            for name in m.group(2).split(",") if name.strip()]


def sql_pairs(db) -> list[tuple[str, str]]:
    return [(table, column[1]) for (table,) in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            for column in db.execute(f'PRAGMA table_info("{table}")')]


def scalar_kind(value) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    return type(value).__name__


def shape(text: str) -> str:
    if any(c.isdigit() for c in text):
        return re.sub(r"\d", "9", text)
    return "".join("A" if c.isupper() else "a" if c.isalpha() else c for c in text)


def render(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def masked(text: str) -> str:
    return "".join("A" if c.isupper() else "a" if c.isalpha() else c for c in text)


def characters(values) -> str:
    """식별자에 쓰인 글자 종류. 문장부호와 기호는 글자 그대로 적는다."""
    classes, symbols = set(), set()
    for value in values:
        for c in value:
            if c.isdigit():
                classes.add("digits")
            elif c.isascii() and c.isupper():
                classes.add("uppercase")
            elif c.isascii() and c.islower():
                classes.add("lowercase")
            elif c.isalpha():
                classes.add("other letters")
            else:
                symbols.add(c)
    order = ["digits", "lowercase", "uppercase", "other letters"]
    return ", ".join([c for c in order if c in classes] + [render("".join(sorted(symbols)))] * bool(symbols))


def flatten(raw: collections.Counter) -> collections.Counter:
    """목록 값(튜플)은 원소로 펼치고 스칼라는 그대로 둔 값별 기록 수."""
    elements = collections.Counter()
    for value, n in raw.items():
        for element in (value if isinstance(value, tuple) else (value,)):
            elements[element] += n
    return elements


def low_cardinality_max_length(raw: collections.Counter, threshold: int) -> int | None:
    """서로 다른 (원소) 값이 문턱값 이하인 문자열 속성의 가장 긴 값 길이. 해당하지 않으면 None."""
    values = flatten(raw)
    if not values or len(values) > threshold or not all(isinstance(v, str) for v in values):
        return None
    return max(len(v) for v in values)


def describe_values(counts: collections.Counter, threshold: int, label_cap: int, leak: LeakIndex,
                    rng: random.Random) -> dict:
    """값(스칼라)과 기록 수에서 종류 · 값 목록 또는 형식 설명과 예시를 만든다."""
    if not counts:
        return {"distinct": 0, "records": 0, "kind": "none", "mode": "full_list", "values": [],
                "listedValuesInLeakSet": 0}
    kinds = collections.Counter(scalar_kind(v) for v in counts)
    kind = kinds.most_common(1)[0][0] if len(kinds) == 1 else "mixed(" + ",".join(sorted(kinds)) + ")"
    out: dict = {"distinct": len(counts), "records": sum(counts.values())}
    longest = max((len(v) for v in counts if isinstance(v, str)), default=0)
    if len(counts) <= threshold and longest <= label_cap:
        listed = sorted(counts.items(), key=lambda kv: (-kv[1], str(kv[0])))
        out.update({"kind": "categorical" if kind == "string" else kind, "mode": "full_list",
                    "values": [[v, n] for v, n in listed],
                    "listedValuesInLeakSet": sum(1 for v in counts if leak.reason(v))})
        return out
    if kind == "string":
        kind = "text" if any(any(c.isspace() for c in v) for v in counts) else "identifier"
    out.update({"kind": kind, "mode": "format_and_examples"})
    excluded = collections.Counter()
    candidates = []
    for value in sorted(counts, key=str):
        why = leak.reason(value)
        if why:
            excluded[why] += 1
        else:
            candidates.append(value)
    out["exclusions"] = {"candidates": len(counts), "excluded": sum(excluded.values()), "byReason": dict(excluded),
                         "remaining": len(candidates)}
    out["examples"] = rng.sample(candidates, min(EXAMPLES, len(candidates)))
    if kind in ("integer", "float"):
        out["range"] = [min(counts), max(counts)]
        out["rangeEndpointsInLeakSet"] = sum(1 for v in out["range"] if leak.reason(v))
    elif kind in ("identifier", "text"):
        lengths = sorted(len(v) for v in counts)
        out["length"] = {"min": lengths[0], "median": statistics.median(lengths), "max": lengths[-1]}
        if kind == "identifier":
            out["characters"] = characters(counts)
            total = sum(counts.values())
            for level, form in (("digits_masked", shape), ("letters_and_digits_masked", lambda v: masked(shape(v)))):
                shapes = collections.Counter()
                for value, n in counts.items():
                    shapes[form(value)] += n
                out["distinctShapes"] = {**out.get("distinctShapes", {}), level: len(shapes)}
                if len(shapes) <= threshold:
                    out["shapeLevel"] = level
                    out["shapes"] = [[masked(s) if leak.reason(s) else s, round(100 * n / total, 1)]
                                     for s, n in shapes.most_common()]
                    out["shapesMaskedForLeak"] = sum(1 for s in shapes if leak.reason(s))
                    break
    return out


def describe(raw: collections.Counter, threshold: int, label_cap: int, leak: LeakIndex,
             rng: random.Random) -> dict:
    """속성 · 열의 저장값(목록 값은 튜플)과 기록 수. 목록이 섞이면 원소를 펼쳐 같은 절차로 잰다."""
    lists = {v: n for v, n in raw.items() if isinstance(v, tuple)}
    if not lists:
        return describe_values(raw, threshold, label_cap, leak, rng)
    scalars = {v: n for v, n in raw.items() if not isinstance(v, tuple)}
    body = describe_values(flatten(raw), threshold, label_cap, leak, rng)
    sizes = sorted(len(v) for v, n in lists.items() for _ in range(n))
    return {"container": "list" if not scalars else "list_or_scalar",
            "listRecords": sum(lists.values()), "scalarRecords": sum(scalars.values()),
            "emptyLists": lists.get((), 0), "listLength": {"min": sizes[0], "max": sizes[-1]},
            "element": body}


def clip(value, cap: int):
    if isinstance(value, str) and len(value) > cap:
        return value[:cap] + f"… [{len(value)} chars]"
    return value


def line_for(owner_text: str, info: dict, cap: int) -> str:
    def body(part: dict) -> str:
        head = f"{part['kind']}; {part['records']} values, {part['distinct']} distinct"
        if part["mode"] == "full_list":
            if not part["values"]:
                return head + "; no values"
            return head + "; all values (count): " + ", ".join(f"{render(v)} ({n})" for v, n in part["values"])
        pieces = [head]
        if "range" in part:
            pieces.append(f"range {part['range'][0]}..{part['range'][1]}")
        if "length" in part:
            length = part["length"]
            pieces.append(f"length {length['min']}..{length['max']} (median {length['median']})")
        if "characters" in part:
            pieces.append(f"characters: {part['characters']}")
        if "shapes" in part:
            shapes = ", ".join(f"{render(s)} {p}%" for s, p in part["shapes"])
            legend = ("digits shown as 9" if part["shapeLevel"] == "digits_masked"
                      else "digits shown as 9, letters as A/a")
            pieces.append(f"all shapes ({legend}; share of values): {shapes}")
        pieces.append("examples: " + (", ".join(render(clip(v, cap)) for v in part["examples"]) or "none"))
        return "; ".join(pieces)

    if "container" in info:
        where = "list of" if info["container"] == "list" else "string or list of"
        head = (f"{owner_text} — {where} values ({info['listRecords']} lists, {info['scalarRecords']} scalars, "
                f"{info['emptyLists']} empty lists, list length {info['listLength']['min']}..{info['listLength']['max']})"
                f"; elements: ")
        return head + body(info["element"])
    return f"{owner_text} — " + body(info)


def fetch_graph(session, label: str, prop: str) -> collections.Counter:
    counts = collections.Counter()
    for record in session.execute_read(lambda tx: list(tx.run(
            f"MATCH (x:`{label}`) WHERE x.`{prop}` IS NOT NULL RETURN x.`{prop}` AS v, count(*) AS n"))):
        value = record["v"]
        counts[tuple(value) if isinstance(value, list) else value] += record["n"]
    return counts


def fetch_sql(db, table: str, column: str) -> collections.Counter:
    return collections.Counter(dict(db.execute(
        f'SELECT "{column}", count(*) FROM "{table}" WHERE "{column}" IS NOT NULL GROUP BY "{column}"')))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--cypher-packets", type=Path, required=True)
    parser.add_argument("--sql-packets", type=Path, required=True)
    parser.add_argument("--sqlite-dir", type=Path, required=True)
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--bolt", action="append", required=True, help="WG=bolt URL, WG 마다 한 번")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20271)
    args = parser.parse_args()
    bolts = dict(entry.split("=", 1) for entry in args.bolt)
    wgs = sorted(bolts)

    items = [json.loads(line) for path in args.items for line in path.read_text().splitlines() if line.strip()]
    terms = {str(cell) for item in items for row in item["gold"] for cell in row}
    terms |= {graph_key(item["anchor"]) for item in items}
    leak = LeakIndex(terms, [item["question"] for item in items])

    packets, pairs, distinct = {}, {}, []
    for wg in wgs:
        packets[("cypher", wg)] = json.loads((args.cypher_packets / f"{wg}_schema.json").read_text())
        packets[("sql", wg)] = json.loads((args.sql_packets / f"{wg}_schema.json").read_text())
        pairs[("cypher", wg)] = cypher_pairs(packets[("cypher", wg)]["task"])
        db = sqlite3.connect(f"file:{args.sqlite_dir / f'{wg}.sqlite'}?mode=ro", uri=True)
        pairs[("sql", wg)] = sql_pairs(db)
        for table, column in pairs[("sql", wg)]:
            (n,) = db.execute(f'SELECT count(DISTINCT "{column}") FROM "{table}"').fetchone()
            distinct.append(("sql", wg, table, column, n))
        db.close()
        with GraphDatabase.driver(bolts[wg], auth=neo4j_auth()) as driver, \
                driver.session(default_access_mode="READ") as session:
            for label, prop in pairs[("cypher", wg)]:
                n = session.execute_read(lambda tx: tx.run(
                    f"MATCH (x:`{label}`) WHERE x.`{prop}` IS NOT NULL RETURN count(DISTINCT x.`{prop}`) AS d"
                ).single()["d"])
                distinct.append(("cypher", wg, label, prop, n))
    knees = {"cypher": kneedle([d[-1] for d in distinct if d[0] == "cypher"]),
             "sql": kneedle([d[-1] for d in distinct if d[0] == "sql"]),
             "pooled": kneedle([d[-1] for d in distinct])}
    threshold = knees["pooled"]["threshold"]

    def each_property(wanted):
        """(언어, WG, 소유자, 이름, 저장값 계수기). `wanted` 가 거짓인 항목은 읽지 않는다."""
        for wg in wgs:
            db = sqlite3.connect(f"file:{args.sqlite_dir / f'{wg}.sqlite'}?mode=ro", uri=True)
            for table, column in pairs[("sql", wg)]:
                if wanted(("sql", wg, table, column)):
                    yield "sql", wg, table, column, fetch_sql(db, table, column)
            db.close()
            with GraphDatabase.driver(bolts[wg], auth=neo4j_auth()) as driver, \
                    driver.session(default_access_mode="READ") as session:
                for label, prop in pairs[("cypher", wg)]:
                    if wanted(("cypher", wg, label, prop)):
                        yield "cypher", wg, label, prop, fetch_graph(session, label, prop)

    # 목록 값은 원소 기준으로 세므로 저장값 기준 개수(1단계)로는 고를 수 없다. 모두 한 번 읽고, 원소 기준으로
    # 문턱값 이하인 것만 들고 있다가 나머지는 기술 단계에서 다시 읽는다.
    cached, longest = {}, []
    for lang, wg, owner, name, raw in each_property(lambda key: True):
        if len(flatten(raw)) <= threshold:
            cached[(lang, wg, owner, name)] = raw
        length = low_cardinality_max_length(raw, threshold)
        if length is not None:
            longest.append(length)
    label_knee = kneedle(longest)
    cap = label_knee["threshold"]

    described: dict[tuple[str, str], list[tuple[str, str, dict]]] = collections.defaultdict(list)
    held = frozenset(cached)
    fetched = each_property(lambda key: key not in held)
    for wg in wgs:
        for lang, keys in (("sql", pairs[("sql", wg)]), ("cypher", pairs[("cypher", wg)])):
            for owner, name in keys:
                key = (lang, wg, owner, name)
                if key in cached:
                    raw = cached.pop(key)
                else:
                    got = next(fetched)
                    assert got[:4] == key, (got[:4], key)
                    raw = got[4]
                rng = random.Random(f"{args.seed}:{lang}:{wg}:{owner}:{name}")
                described[(lang, wg)].append((owner, name, describe(raw, threshold, cap, leak, rng)))

    def parts(info: dict) -> dict:
        return info.get("element", info)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    report_packets = {}
    for (lang, wg), entries in sorted(described.items()):
        lines = [line_for(f"(:{o}).{n}" if lang == "cypher" else f"{o}.{n}", info, cap) for o, n, info in entries]
        header = (f"\n\nStored value domains, measured on this {'graph' if lang == 'cypher' else 'database'} "
                  f"for every {'label property' if lang == 'cypher' else 'table column'} above. "
                  f"When a {'property' if lang == 'cypher' else 'column'} has at most {threshold} distinct values, "
                  f"all of them are listed with their record counts; otherwise its value kind, a format description "
                  f"and up to {EXAMPLES} example values are given. Values longer than {cap} characters are never "
                  f"listed in full and examples longer than that are cut. For list values the elements are "
                  f"described.\n")
        packet = packets[(lang, wg)]
        body, withheld = NAMESPACE_WORD.subn("<ns>", "\n".join(lines))
        if withheld:
            header += ("The namespace word of the graph's own w3id.org IRIs is withheld and shown as <ns>; the "
                       "stored values contain that word instead.\n")
        task = packet["task"] + header + body
        out = {"task": task, "items": packet["items"]}
        path = args.out_dir / f"{lang}_{wg}.json"
        path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
        modes = collections.Counter(parts(info)["mode"] for _, _, info in entries)
        kinds = collections.Counter(parts(info)["kind"] for _, _, info in entries)
        report_packets[f"{lang}_{wg}"] = {
            "path": str(path), "bytes": path.stat().st_size, "taskChars": len(task),
            "originalTaskChars": len(packet["task"]), "items": len(packet["items"]),
            "namespaceWordWithheld": withheld,
            "properties": len(entries), "byMode": dict(modes), "byKind": dict(kinds),
            "fullListValuesInLeakSet": sum(parts(info).get("listedValuesInLeakSet", 0) for _, _, info in entries),
            "exampleCandidates": sum(parts(info)["exclusions"]["candidates"] for _, _, info in entries
                                     if "exclusions" in parts(info)),
            "exampleExclusions": sum(parts(info)["exclusions"]["excluded"] for _, _, info in entries
                                     if "exclusions" in parts(info)),
            "exampleExclusionsByReason": dict(sum((collections.Counter(parts(info)["exclusions"]["byReason"])
                                                   for _, _, info in entries if "exclusions" in parts(info)),
                                                  collections.Counter())),
            "propertiesWithoutLeakFreeExample": [f"{o}.{n}" for o, n, info in entries
                                                 if "exclusions" in parts(info) and not parts(info)["examples"]],
            "entries": [{"owner": o, "name": n, **{k: v for k, v in info.items()
                                                    if k not in ("values", "examples", "shapes")},
                         **({"element": {k: v for k, v in info["element"].items()
                                         if k not in ("values", "examples", "shapes")}} if "element" in info else {})}
                        for o, n, info in entries],
        }
    report = {
        "scope": "value-domain descriptions appended to the schema packets; graph read in READ sessions, "
                 "relational exports opened read-only",
        "threshold": {"value": threshold, "rule": "Kneedle knee of the empirical CDF of log10(distinct values) "
                      "over every (WG, owner, name) of both languages; the pooled knee is used for both languages",
                      "knees": knees,
                      "distinctCountHistogram": {lang: dict(sorted(collections.Counter(
                          d[-1] for d in distinct if d[0] == lang).items())) for lang in ("cypher", "sql")}},
        "labelLengthCap": {"value": cap, "rule": "Kneedle knee of the empirical CDF of log10(longest value length) "
                           "over every string (WG, owner, name) of both languages with at most threshold distinct "
                           "(element) values; longer low-cardinality strings get a format description instead of a "
                           "full list, and examples are cut at this length", "knee": label_knee},
        "leakSet": {"terms": len(leak.terms), "questionSlices": len(leak.slices),
                    "rule": "examples exclude values equal to or containing (word-boundary) any gold cell or anchor "
                            "key of the 667 items, and values occurring (word-boundary) in any question text"},
        "namespaceWord": {"rule": "the namespace word between w3id.org/ (or its digit-masked shape w9id.org/) and # "
                          "in the graph's own IRIs is replaced by <ns> in the appended text; the original packets "
                          "do not contain it", "perPacket": "packets.*.namespaceWordWithheld"},
        "seed": args.seed, "examplesPerProperty": EXAMPLES,
        "packets": report_packets,
    }
    (args.out_dir / "domain_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({"threshold": report["threshold"]["value"], "knees": knees, "labelLengthCap": label_knee,
                      "packets": {k: {f: v[f] for f in ("bytes", "taskChars", "byMode", "exampleExclusions",
                                                        "fullListValuesInLeakSet")}
                                  for k, v in report_packets.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
