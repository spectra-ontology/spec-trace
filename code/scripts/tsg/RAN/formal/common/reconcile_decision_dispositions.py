#!/usr/bin/env python3
"""reconcile_decision_dispositions.py — 원문에 기록된 처리 결과의 live 정합화와 복구 저널.

Spec: docs/tsg/build/standards/decision_disposition_contract.md.
Ontology: verified target-level dispositions complement existing REFERENCES.
Cycle: source validation → read-only plan/preimage → explicit apply → transactional checks.
배경: 승인 관계를 추가할 때도 원래 Resolution·문서 상태·참조 간선을 보존한다.
사용: --wg RAN1 --out /tmp/plan.json; --apply --plan /tmp/plan.json.
LLM 호출: 없음.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from decision_disposition import (ROOT, load_dispositions, neo4j_rows,
                                  prepare_for_wg, validate_dispositions,
                                  resolution_snapshot as snapshot, reports_for_wg,
                                  write_dispositions, coverage_for_wg)
from document_decision_storage import (document_resolution_nodes, source_event_snapshot, durable_json,
                                       retire_absent_document_events)
sys.path.insert(0, str(ROOT / 'scripts/common'))
from common import axis, credentials
from common.atomic_io import write_text_atomic
from neo4j import GraphDatabase, READ_ACCESS


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def plan(wg, rows, driver):
    payload = neo4j_rows(rows)
    ids = sorted({r['resolutionId'] for r in payload})
    source_nodes = document_resolution_nodes(reports_for_wg(wg))
    source_ids = {node['resolutionId'] for node in source_nodes}
    original_ids = sorted(set(ids) - source_ids)
    with driver.session(default_access_mode=READ_ACCESS) as session:
        tx = session.begin_transaction()
        try:
            preimage = snapshot(tx, original_ids)
            event_preimage = source_event_snapshot(tx, sorted(source_ids))
            tdocs = tx.run('MATCH (t:Tdoc) WHERE t.tdocNumber IN $numbers RETURN t.tdocNumber AS number, labels(t) AS labels',
                          numbers=sorted({r['tdocNumber'] for r in payload})).data()
        finally:
            tx.rollback()
    actual_ids = {r['resolutionId'] for r in preimage}
    missing = sorted(set(original_ids) - actual_ids)
    if missing:
        raise ValueError(f'Current Resolution endpoints absent: {missing}')
    target_labels = {r['number']: r['labels'] for r in tdocs}
    approved_crs = [r for r in payload if r['properties']['evidenceStatus'] == 'source_verified'
                   and r['properties']['dispositionCode'] == 'agreed'
                   and 'CR' in target_labels.get(r['tdocNumber'], [])]
    return {'wg': wg, 'mode': 'read_only_plan',
            'assertionSha256': digest(rows), 'resolutionPreimage': preimage,
            'resolutionPreimageSha256': digest(preimage),
            'documentSourceEvents': len(source_nodes),
            'documentSourceSha256': digest(source_nodes),
            'documentSourcePreimage': event_preimage,
            'documentSourcePreimageSha256': digest(event_preimage),
            'counts': dict(Counter(r['dispositionCode'] for r in rows)),
            'sourceVerifiedApprovalsOnCR': len(approved_crs),
            'missingTdocTargets': sorted({r['tdocNumber'] for r in payload} - set(target_labels)),
            'resolutionReferenceStatusMutations': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wg', choices=[f'RAN{x}' for x in range(1, 6)], required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--prepare-and-apply', action='store_true',
                        help='Persist the complete current read-only plan, then apply with transaction preimage fences.')
    parser.add_argument('--retire-absent-events', action='store_true',
                        help='After applying, remove source events the current source no longer yields (journalled).')
    args = parser.parse_args()
    if args.retire_absent_events and not (args.apply or args.prepare_and_apply):
        parser.error('--retire-absent-events requires an apply mode')
    rows = prepare_for_wg(args.wg)
    with GraphDatabase.driver(axis.bolt_uri(args.wg), auth=credentials.neo4j_auth()) as driver:
        current = plan(args.wg, rows, driver)
        if args.prepare_and_apply:
            if args.apply or args.plan is not None:
                parser.error('--prepare-and-apply cannot combine with --apply/--plan')
            args.plan = args.out.with_name(args.out.stem + '.plan.json')
            args.plan.parent.mkdir(parents=True, exist_ok=True)
            durable_json(args.plan, current)
        if args.apply or args.prepare_and_apply:
            if args.plan is None:
                parser.error('--apply requires the complete prior --plan preimage')
            previous = json.loads(args.plan.read_text())
            if (previous['wg'] != args.wg or previous['assertionSha256'] != current['assertionSha256']
                    or previous['resolutionPreimageSha256'] != current['resolutionPreimageSha256']
                    or previous['documentSourceSha256'] != current['documentSourceSha256']
                    or previous['documentSourcePreimageSha256'] != current['documentSourcePreimageSha256']):
                raise ValueError('Source or Resolution/reference preimage changed; create a new plan')
            validate_dispositions(rows)
            output_dir = ROOT / f'ontology/output/tsg/RAN/formal/instances/phase-2/{args.wg}'
            current['sourceArtifacts'] = write_dispositions(reports_for_wg(args.wg), output_dir, prepared_rows=rows)
            coverage = coverage_for_wg(args.wg, rows)
            write_text_atomic(output_dir / 'decision_disposition_coverage.json',
                              json.dumps(coverage, ensure_ascii=False, indent=2) + '\n')
            with driver.session() as session:
                current['applied'] = load_dispositions(session, rows)
                if args.retire_absent_events:
                    current['retired'] = retire_absent_document_events(
                        session, args.wg, document_resolution_nodes(reports_for_wg(args.wg)),
                        [row['properties']['dispositionId'] for row in neo4j_rows(rows)])
            with driver.session(default_access_mode=READ_ACCESS) as session:
                tx = session.begin_transaction()
                try:
                    after = snapshot(tx, sorted(r['resolutionId'] for r in current['resolutionPreimage']))
                    if digest(after) != current['resolutionPreimageSha256']:
                        raise RuntimeError('Resolution or REFERENCES changed during apply')
                    current['liveCounts'] = tx.run('''
                        MATCH (d:DecisionDisposition) WHERE d.dispositionId STARTS WITH $prefix
                        RETURN d.evidenceStatus AS evidenceStatus, d.dispositionCode AS code,
                               count(*) AS count ORDER BY code, evidenceStatus
                    ''', prefix=args.wg + ':').data()
                finally:
                    tx.rollback()
            current['mode'] = 'applied_with_preimage_and_postconditions'
        args.out.parent.mkdir(parents=True, exist_ok=True)
        durable_json(args.out, current)
        print(json.dumps({k: v for k, v in current.items() if k not in ('assertions', 'resolutionPreimage', 'documentSourcePreimage')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
