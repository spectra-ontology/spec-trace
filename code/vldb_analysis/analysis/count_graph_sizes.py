"""다섯 작업반 그래프의 노드 수와 관계 수를 읽어 기록한다.

두 질의 모두 Neo4j 의 개수 저장소로 답하므로 그래프를 훑지 않는다.

사용: PYTHONPATH=scripts/common python3 -B count_graph_sizes.py --out <json>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import neo4j
from neo4j import GraphDatabase

from common.credentials import neo4j_auth

BOLT_PORT = {"RAN1": 7687, "RAN2": 7688, "RAN3": 7689, "RAN4": 7690, "RAN5": 7691}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    auth = neo4j_auth()
    groups = {}
    for wg, port in BOLT_PORT.items():
        driver = GraphDatabase.driver(f"bolt://localhost:{port}", auth=auth)
        with driver.session() as session:
            nodes = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            rels = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
            version = session.run(
                "CALL dbms.components() YIELD name, versions, edition "
                "RETURN name, versions[0] AS version, edition").single()
            groups[wg] = {"bolt": f"bolt://localhost:{port}", "nodes": nodes, "relationships": rels,
                          "server": f"{version['name']} {version['version']} {version['edition']}"}
        driver.close()
        print(wg, groups[wg], flush=True)
    total = {"nodes": sum(g["nodes"] for g in groups.values()),
             "relationships": sum(g["relationships"] for g in groups.values())}
    record = {"scope": "작업반별로 적재한 그래프 전체(벤치마크가 쓰는 레코드와 그 밖의 노드를 모두 포함)",
              "driver": neo4j.__version__, "groups": groups, "total": total}
    Path(args.out).write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("total", total)


if __name__ == "__main__":
    main()
