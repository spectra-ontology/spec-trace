#!/usr/bin/env python3
"""Current formal CQ operational checks through read-only rolled-back transactions.

Spec: docs/common/process/spectra_operations_rulebook.md §3.1, §4.1.
Ontology: identifiers, declared schema, query execution and nonzero contracts only.
Cycle: 25 current CQ datasets → five read-only databases → independent evidence.
배경: execution/guard results are separate from domain meaning and causal truth.
사용: python3 replay_formal_cqs_readonly.py --out /tmp/formal-cq-replay.json
LLM 호출: 없음. No DB writes; every query transaction is rolled back.
"""
import concurrent.futures
import json
import logging
import sys
import time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
sys.path.insert(0, str(ROOT / 'scripts/common'))
sys.path.insert(0, str(ROOT / 'scripts/tsg/RAN/formal/common'))
from common import axis, credentials
from common.atomic_io import write_text_atomic
from neo4j import GraphDatabase, READ_ACCESS
from cq_anchor_guard import guard_defects

logging.getLogger('neo4j').setLevel(logging.CRITICAL)


def audit_wg(wg):
    out = []
    with GraphDatabase.driver(axis.bolt_uri(f'RAN{wg}'),
                              auth=credentials.neo4j_auth()) as driver:
        with driver.session(default_access_mode=READ_ACCESS) as session:
            for phase in range(1, 6):
                dataset = axis.tree_path('logs', wg=f'RAN{wg}', phase=phase, root=ROOT) / 'cq_test_dataset.json'
                for cq in json.loads(dataset.read_text())['questions']:
                    row = {'phase': phase, 'id': cq['id']}
                    started = time.monotonic()
                    tx = session.begin_transaction(timeout=8)
                    try:
                        rows = tx.run(cq['cypher']).data()
                        row['rows'] = len(rows)
                        row['expected_min'] = cq.get('expected_min_rows')
                    except Exception as exc:
                        rows = None
                        row['query_error'] = str(exc)
                    finally:
                        tx.rollback()
                    row['sec'] = round(time.monotonic() - started, 3)
                    try:
                        row['guard_defects'] = guard_defects(session, cq, rows=rows)
                    except Exception as exc:
                        row['guard_error'] = str(exc)
                    out.append(row)
    print(f'RAN{wg}: {len(out)} CQs', flush=True)
    return f'RAN{wg}', out


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        report = dict(pool.map(audit_wg, range(1, 6)))
    path = args.out
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text_atomic(path, json.dumps(report, ensure_ascii=False, indent=2))
    flat = [row for rows in report.values() for row in rows]
    errors = sum(bool(row.get('query_error') or row.get('guard_error') or row.get('guard_defects')) for row in flat)
    shortfalls = sum(row.get('expected_min') is not None and row.get('rows', 0) < row['expected_min'] for row in flat)
    print(f'operational checks only: CQs {len(flat)}, errors/defects {errors}, declared minimum shortfalls {shortfalls}')
    print(path)
    sys.exit(1 if errors or shortfalls else 0)


if __name__ == '__main__':
    main()
