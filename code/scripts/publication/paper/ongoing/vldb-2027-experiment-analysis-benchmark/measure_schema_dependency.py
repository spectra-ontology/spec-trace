"""현행 Core 문항의 정답 질의가 어느 스키마 요소에 의존하는지 센다 (모델 호출 없음).

각 문항의 `reference_query`(Cypher)에서 노드 라벨과 관계 유형을 정적으로 추출한다.
요소 하나를 스키마에서 제거하면 그 요소를 쓰는 질의는 성립하지 않으므로,
요소별 문항 수는 그 요소가 지탱하는 문항 수의 상한이다(대체 경로가 있으면 실제 값은 더 작다).

사용: python3 measure_schema_dependency.py --release <공개 저장소 체크아웃 루트> --out <json>
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

NODE = re.compile(r"\(\s*[A-Za-z_][A-Za-z0-9_]*?\s*:\s*([A-Za-z_][A-Za-z0-9_|:&\s]*?)\s*[{)\s]")
ANON_NODE = re.compile(r"\(\s*:\s*([A-Za-z_][A-Za-z0-9_|:&\s]*?)\s*[{)\s]")
REL = re.compile(r"\[\s*[A-Za-z_]?[A-Za-z0-9_]*\s*:\s*([A-Za-z_][A-Za-z0-9_|:\s]*?)\s*[\]{*]")
STRING = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")


def elements(query: str) -> tuple[set[str], set[str]]:
    bare = STRING.sub("''", query)
    split = lambda hits: {name for hit in hits for name in re.split(r"[|:&\s]+", hit) if name}
    return split(NODE.findall(bare) + ANON_NODE.findall(bare)), split(REL.findall(bare))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    index = [json.loads(line) for line in
             (args.release / "release_package/cqs/current_core/current_tasks.jsonl").open()]
    wanted = {row["id"]: row["bundle"] for row in index}
    queries: dict[str, str] = {}
    for bundle in sorted(set(wanted.values())):
        for line in (args.release / bundle / "tasks.jsonl").open():
            task = json.loads(line)
            if wanted.get(task["id"]) == bundle:
                queries[task["id"]] = task["reference_query"]
    labels: collections.Counter[str] = collections.Counter()
    relations: collections.Counter[str] = collections.Counter()
    per_question = {}
    for qid, query in sorted(queries.items()):
        node_set, rel_set = elements(query)
        labels.update(node_set)
        relations.update(rel_set)
        per_question[qid] = {"labels": sorted(node_set), "relations": sorted(rel_set)}
    result = {"questions": len(index), "queriesFound": len(queries),
              "withoutExtractedLabel": sorted(q for q, e in per_question.items() if not e["labels"]),
              "labelDependency": dict(labels.most_common()),
              "relationDependency": dict(relations.most_common()),
              "perQuestion": per_question}
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
    print(result["questions"], result["queriesFound"], len(result["withoutExtractedLabel"]))
    print(dict(labels.most_common()))
    print(dict(relations.most_common()))


if __name__ == "__main__":
    main()
