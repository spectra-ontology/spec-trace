"""Codex 재실행 질의에 정답 값이 글자 그대로 박혀 있는지 센다 (모델 호출 없음 · 질의는 실행하지 않는다).

탐색 조건에서는 질의 작성자가 데이터베이스의 행을 볼 수 있으므로, 질의가 답을 찾는 대신 본 답을 상수로 적어 넣었는지
확인한다. 질의마다 다음을 본다.

1. 질의 글에서 따옴표로 묶인 문자열 상수를 모두 뽑는다.
2. 그 문항의 정답 칸 값 가운데 질문 문장에 나오지 않는 값(질문만으로는 알 수 없는 값)이 상수로 들어 있는지 본다.
   대소문자는 구별하지 않고 상수와 값이 같을 때만 센다.
3. 찾은 값이 그 언어의 원래 묶음 과제 문장이나 값 영역 묶음 과제 문장에도 나오면 그 사실을 따로 적는다(묶음이 준
   값이면 형식 정보로 쓴 것이다).
4. 그래프 질의에 MATCH 가, 관계형 질의에 FROM 이 없는 질의(데이터를 읽지 않는 질의)를 따로 센다.
5. 개수처럼 숫자인 정답은 따옴표 없이 적힐 수 있으므로, 문자열 상수를 지운 질의 글에서 숫자 낱말을 뽑아 질문에 없는
   숫자 정답 값과 같은지 따로 센다. 이름 안의 숫자(`r17` 의 17 같은 것)는 낱말 경계로 걸러 낸다.

사용: python3 check_codex_v2_answer_literals.py --items <jsonl> [...] --responses <jsonl> [...] \
          --packets-original-cypher <dir> --packets-original-sql <dir> --packets-domain <dir> --out <json>
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

STRING = re.compile(r"'((?:[^'\\]|\\.|'')*)'|\"((?:[^\"\\]|\\.)*)\"")


NUMBER = re.compile(r"(?<![\w.$])\d+(?:\.\d+)?(?![\w.])")


def literals(query: str) -> set[str]:
    return {(a if a is not None else b).replace("''", "'").lower()
            for match in STRING.finditer(query) for a, b in [match.groups()]}


def numbers(query: str) -> set[str]:
    return set(NUMBER.findall(STRING.sub(" ", query)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--items", type=Path, nargs="+", required=True)
    parser.add_argument("--responses", type=Path, nargs="+", required=True)
    parser.add_argument("--packets-original-cypher", type=Path, required=True)
    parser.add_argument("--packets-original-sql", type=Path, required=True)
    parser.add_argument("--packets-domain", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    items = {item["id"]: item for path in args.items for item in map(json.loads, path.read_text().splitlines())}
    tasks: dict[tuple[str, str, str], str] = {}
    for wg in sorted({item["wg"] for item in items.values()}):
        tasks[("original", "cypher", wg)] = json.loads((args.packets_original_cypher / f"{wg}_schema.json").read_text())["task"].lower()
        tasks[("original", "sql", wg)] = json.loads((args.packets_original_sql / f"{wg}_schema.json").read_text())["task"].lower()
        for lang in ("cypher", "sql"):
            tasks[("domain", lang, wg)] = json.loads((args.packets_domain / f"{lang}_{wg}.json").read_text())["task"].lower()
    runs: dict[tuple[str, str], dict] = {}
    for path in args.responses:
        for record in map(json.loads, path.read_text().splitlines()):
            run = runs.setdefault((record["method"], record["model"]), {
                "queries": 0, "noDataRead": [], "withHiddenGoldLiteral": 0, "hiddenGoldLiteralByPacket": collections.Counter(),
                "withHiddenGoldNumber": [], "examples": []})
            item = items[record["id"]]
            lang = "sql" if record["method"] == "text2sql" else "cypher"
            query = (record.get("attempts") or [{}])[0].get(lang, "")
            run["queries"] += 1
            reads = re.search(r"\bFROM\b", query, re.I) if lang == "sql" else re.search(r"\bMATCH\b", query, re.I)
            if not reads:
                run["noDataRead"].append(record["id"])
            question = item["question"].lower()
            hidden = {str(cell).lower() for row in item["gold"] for cell in row
                      if cell is not None and str(cell).strip() and str(cell).lower() not in question}
            hidden_numbers = {value for value in hidden if NUMBER.fullmatch(value)}
            numeric = sorted(hidden_numbers & numbers(query))
            if numeric:
                run["withHiddenGoldNumber"].append({"id": record["id"], "values": numeric, "query": query[:600]})
            found = sorted(hidden & literals(query))
            if found:
                run["withHiddenGoldLiteral"] += 1
                for value in found:
                    where = ("originalPacket" if value in tasks[("original", lang, item["wg"])]
                             else "domainPacketOnly" if value in tasks[("domain", lang, item["wg"])] else "inNoPacket")
                    run["hiddenGoldLiteralByPacket"][where] += 1
                    if where == "inNoPacket" and len(run["examples"]) < 20:
                        run["examples"].append({"id": record["id"], "value": value, "query": query[:600]})
    report = {"rule": __doc__.split("\n\n")[1].replace("\n", " "), "runs": [
        {"method": method, "model": model, **{key: (dict(value) if isinstance(value, collections.Counter) else value)
                                              for key, value in run.items()},
         "noDataReadCount": len(run["noDataRead"]), "withHiddenGoldNumberCount": len(run["withHiddenGoldNumber"])}
        for (method, model), run in sorted(runs.items())]}
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    for run in report["runs"]:
        print(run["method"], run["model"], "queries", run["queries"], "noDataRead", run["noDataReadCount"],
              "hiddenGoldLiteralQueries", run["withHiddenGoldLiteral"], run["hiddenGoldLiteralByPacket"],
              "hiddenGoldNumberQueries", run["withHiddenGoldNumberCount"])


if __name__ == "__main__":
    main()
