#!/usr/bin/env python3
"""
CQ Validation: 페르소나 시나리오 기반 CQ (v3.0 현재 34개) 검증
- cq_test_dataset.json에서 CQ를 읽어 직접 Cypher 쿼리로 Neo4j 검증
- 상세 답변 포함 리포트 생성
- 실제 CQ 개수는 데이터셋 파일에서 동적으로 로드되며, 버전 변경 시 자동 반영

Single Source of Truth: logs/RAN/formal/RAN1/phase-2/cq_test_dataset.json
"""

import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(next(p for p in Path(__file__).resolve().parents if (p / ".git").exists()) / ".env")

URI = "bolt://localhost:7687"
AUTH = ("neo4j", os.getenv("NEO4J_PASSWORD", "password123"))

# validation/ → RAN1/ → phase-2/ → scripts/ → spectra/ (5 levels up)
PROJECT_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
CQ_DATASET_PATH = PROJECT_ROOT / "logs" / "RAN" / "formal" / "RAN1" / "phase-2" / "cq_test_dataset.json"
OUTPUT_PATH = PROJECT_ROOT / "logs" / "RAN" / "formal" / "RAN1" / "phase-2" / "cq_cypher_results.json"


def load_cq_dataset() -> list[dict]:
    """CQ 데이터셋 로드 (Single Source of Truth)."""
    with open(CQ_DATASET_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    questions = data["questions"]
    version = data.get("metadata", {}).get("version", "unknown")
    print(f"CQ 데이터셋 로드: {CQ_DATASET_PATH.name} (v{version}, {len(questions)}개)")
    return questions


def run_validation():
    """CQ 전체 검증 실행 (데이터셋 파일의 개수 자동 반영)"""
    # Load from JSON (Single Source of Truth)
    questions = load_cq_dataset()

    driver = GraphDatabase.driver(URI, auth=AUTH)
    results = []

    print("=" * 80)
    print(f"CQ Validation: 페르소나 시나리오 기반 CQ {len(questions)}개 검증")
    print("=" * 80)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    pass_count = 0
    no_data_count = 0
    fail_count = 0

    with driver.session() as session:
        for cq in questions:
            cq_id = cq["id"]
            category = cq["category"]
            question = cq["question"]
            query = cq["cypher"]

            try:
                result = session.run(query)
                records = list(result)

                if len(records) > 0:
                    status = "PASS"
                    pass_count += 1
                else:
                    status = "NO_DATA"
                    no_data_count += 1

                # 결과 저장
                answer_data = []
                for rec in records[:5]:  # 최대 5개만 저장
                    rec_dict = dict(rec)
                    answer_data.append(rec_dict)

                results.append({
                    "id": cq_id,
                    "category": category,
                    "question": question,
                    "query": query,
                    "status": status,
                    "result_count": len(records),
                    "sample_answers": answer_data
                })

                print(f"[{cq_id}] {status} ({len(records)}건) - {category}: {question[:50]}...")

            except Exception as e:
                fail_count += 1
                results.append({
                    "id": cq_id,
                    "category": category,
                    "question": question,
                    "query": query,
                    "status": "FAIL",
                    "error": str(e),
                    "result_count": 0,
                    "sample_answers": []
                })
                print(f"[{cq_id}] FAIL - {str(e)[:50]}")

    driver.close()

    total = len(questions)

    # 요약 출력
    print()
    print("=" * 80)
    print("검증 결과 요약")
    print("=" * 80)
    print(f"PASS: {pass_count}개 ({pass_count * 100 // total}%)")
    print(f"NO_DATA: {no_data_count}개 ({no_data_count * 100 // total}%)")
    print(f"FAIL: {fail_count}개 ({fail_count * 100 // total}%)")
    print(f"쿼리 성공률: {(pass_count + no_data_count) * 100 // total}%")

    # 카테고리별 결과
    print()
    print("카테고리별 결과:")
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"pass": 0, "no_data": 0, "fail": 0}
        if r["status"] == "PASS":
            categories[cat]["pass"] += 1
        elif r["status"] == "NO_DATA":
            categories[cat]["no_data"] += 1
        else:
            categories[cat]["fail"] += 1

    for cat, counts in categories.items():
        cat_total = counts["pass"] + counts["no_data"] + counts["fail"]
        print(f"  {cat}: PASS {counts['pass']}/{cat_total}, NO_DATA {counts['no_data']}, FAIL {counts['fail']}")

    # NO_DATA 상세
    no_data_items = [r for r in results if r["status"] == "NO_DATA"]
    if no_data_items:
        print()
        print("NO_DATA 상세:")
        for r in no_data_items:
            print(f"  [{r['id']}] {r['question'][:60]}...")

    # 결과 저장
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "version": "5.0",
                "date": datetime.now().isoformat(),
                "source": str(CQ_DATASET_PATH),
                "total": total,
                "pass": pass_count,
                "no_data": no_data_count,
                "fail": fail_count
            },
            "results": results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n결과 저장: {OUTPUT_PATH}")

    return results


if __name__ == "__main__":
    run_validation()
