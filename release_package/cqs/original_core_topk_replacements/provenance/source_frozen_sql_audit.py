#!/usr/bin/env python3
"""Compare retained rank pools to a separate read-only frozen SQL projection."""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[5]
EMP = Path(__file__).resolve().parents[1]
BASE = Path(__file__).resolve().parent / 'topk_replacements'
GX = ROOT / 'logs/publication/paper/under-review/kdd-2027-datasets-benchmarks/gxmb-verification'

QUERIES = {
 'RAN1_P1_CQ3-3': (['c.companyName'], 'tdocCount', """SELECT c.companyName, COUNT(t.node_id), COUNT(DISTINCT t.node_id) FROM Tdoc t JOIN rel_SUBMITTED_BY sb ON sb.src_id=t.node_id JOIN Company c ON c.node_id=sb.dst_id JOIN rel_RELATED_TO rt ON rt.src_id=t.node_id JOIN WorkItem w ON w.node_id=rt.dst_id WHERE w.workItemCode='NR_unlic-Core' GROUP BY c.companyName"""),
 'RAN1_P1_CQ3-6': (['wi.workItemCode'], 'tdocCount', """SELECT w.workItemCode, COUNT(t.node_id), COUNT(DISTINCT t.node_id) FROM Tdoc t JOIN rel_SUBMITTED_BY sb ON sb.src_id=t.node_id JOIN Company c ON c.node_id=sb.dst_id JOIN rel_RELATED_TO rt ON rt.src_id=t.node_id JOIN WorkItem w ON w.node_id=rt.dst_id WHERE c.companyName='Nokia' GROUP BY w.workItemCode"""),
 'RAN1_P2_CQ4-3': (['c.companyName'], 'flCount', """SELECT c.companyName, COUNT(t.node_id), COUNT(DISTINCT t.node_id) FROM Tdoc t JOIN rel_MODERATED_BY mb ON mb.src_id=t.node_id JOIN Company c ON c.node_id=mb.dst_id WHERE t.summaryType='FL' GROUP BY c.companyName"""),
 'RAN1_P4_CQ2-4': (['cr.tdocNumber'], 'affectedSpecCount', """WITH impacts AS (SELECT * FROM rel_AFFECTS_CORE_SPEC UNION ALL SELECT * FROM rel_AFFECTS_TEST_SPEC UNION ALL SELECT * FROM rel_AFFECTS_OM_SPEC) SELECT cr.tdocNumber, COUNT(DISTINCT s.specNumber), COUNT(DISTINCT s.specNumber) FROM CR cr LEFT JOIN impacts e ON e.src_id=cr.node_id LEFT JOIN Spec s ON s.node_id=e.dst_id GROUP BY cr.tdocNumber"""),
 'RAN1_P5_CQ5-3': (['trNumber'], 'referenceCount', """SELECT tr.trNumber, COUNT(DISTINCT src.trNumber), COUNT(DISTINCT src.trNumber) FROM TechnicalReport tr LEFT JOIN rel_REFERENCES_TR e ON e.dst_id=tr.node_id LEFT JOIN TechnicalReport src ON src.node_id=e.src_id GROUP BY tr.trNumber"""),
 'RAN2_P2_CQ1-8': (['ai.agendaNumber', 'ai.meetingNumber'], 'resolutionCount', """SELECT a.agendaNumber,a.meetingNumber,COUNT(r.node_id),COUNT(DISTINCT r.node_id) FROM Resolution r JOIN rel_RESOLUTION_BELONGS_TO e ON e.src_id=r.node_id JOIN AgendaItem a ON a.node_id=e.dst_id WHERE a.agendaNumber<>'UNKNOWN' GROUP BY a.agendaNumber,a.meetingNumber"""),
 'RAN2_P3_CQ1-15': (['s.sectionId'], 'tableCount', """SELECT s.sectionId,COUNT(t.node_id),COUNT(DISTINCT t.node_id) FROM Section s JOIN rel_CONTAINS_TABLE e ON e.src_id=s.node_id JOIN TSTable t ON t.node_id=e.dst_id GROUP BY s.sectionId"""),
 'RAN2_P3_CQ1-16': (['s.sectionId'], 'figCount', """SELECT s.sectionId,COUNT(f.node_id),COUNT(DISTINCT f.node_id) FROM Section s JOIN rel_CONTAINS_FIGURE e ON e.src_id=s.node_id JOIN TSFigure f ON f.node_id=e.dst_id GROUP BY s.sectionId"""),
 'RAN2_P3_CQ2-8': (['s2.sectionId'], 'refCount', """SELECT s2.sectionId,COUNT(*),COUNT(DISTINCT r.edge_id) FROM Section s1 JOIN rel_BELONGS_TO_SPEC b1 ON b1.src_id=s1.node_id JOIN Spec sp ON sp.node_id=b1.dst_id JOIN rel_REFERENCES_SECTION r ON r.src_id=s1.node_id JOIN Section s2 ON s2.node_id=r.dst_id JOIN rel_BELONGS_TO_SPEC b2 ON b2.src_id=s2.node_id AND b2.dst_id=sp.node_id WHERE sp.specNumber='38.331' GROUP BY s2.sectionId,s2.sectionTitle"""),
 'RAN5_P1_CQ1-4': (['meeting'], 'tdocCount', """SELECT m.canonicalMeetingNumber,COUNT(DISTINCT t.node_id),COUNT(DISTINCT t.node_id) FROM Meeting m LEFT JOIN rel_PRESENTED_AT e ON e.dst_id=m.node_id LEFT JOIN Tdoc t ON t.node_id=e.src_id GROUP BY m.canonicalMeetingNumber"""),
}

UNIVERSES = {
 'RAN1_P1_CQ3-3': """SELECT c.companyName, COUNT(DISTINCT CASE WHEN w.workItemCode='NR_unlic-Core' THEN t.node_id END) FROM Company c LEFT JOIN rel_SUBMITTED_BY sb ON sb.dst_id=c.node_id LEFT JOIN Tdoc t ON t.node_id=sb.src_id LEFT JOIN rel_RELATED_TO rt ON rt.src_id=t.node_id LEFT JOIN WorkItem w ON w.node_id=rt.dst_id GROUP BY c.companyName""",
 'RAN1_P1_CQ3-6': """SELECT w.workItemCode, COUNT(DISTINCT CASE WHEN c.companyName='Nokia' THEN t.node_id END) FROM WorkItem w LEFT JOIN rel_RELATED_TO rt ON rt.dst_id=w.node_id LEFT JOIN Tdoc t ON t.node_id=rt.src_id LEFT JOIN rel_SUBMITTED_BY sb ON sb.src_id=t.node_id LEFT JOIN Company c ON c.node_id=sb.dst_id GROUP BY w.workItemCode""",
 'RAN1_P2_CQ4-3': """SELECT c.companyName, COUNT(DISTINCT CASE WHEN t.summaryType='FL' THEN t.node_id END) FROM Company c LEFT JOIN rel_MODERATED_BY mb ON mb.dst_id=c.node_id LEFT JOIN Tdoc t ON t.node_id=mb.src_id GROUP BY c.companyName""",
 'RAN2_P2_CQ1-8': """SELECT a.agendaNumber,a.meetingNumber,COUNT(DISTINCT r.node_id) FROM AgendaItem a LEFT JOIN rel_RESOLUTION_BELONGS_TO e ON e.dst_id=a.node_id LEFT JOIN Resolution r ON r.node_id=e.src_id GROUP BY a.agendaNumber,a.meetingNumber""",
 'RAN2_P3_CQ1-15': """SELECT s.sectionId,COUNT(DISTINCT t.node_id) FROM Section s LEFT JOIN rel_CONTAINS_TABLE e ON e.src_id=s.node_id LEFT JOIN TSTable t ON t.node_id=e.dst_id GROUP BY s.sectionId""",
 'RAN2_P3_CQ1-16': """SELECT s.sectionId,COUNT(DISTINCT f.node_id) FROM Section s LEFT JOIN rel_CONTAINS_FIGURE e ON e.src_id=s.node_id LEFT JOIN TSFigure f ON f.node_id=e.dst_id GROUP BY s.sectionId""",
 'RAN2_P3_CQ2-8': """SELECT s2.sectionId,COUNT(DISTINCT CASE WHEN b1.dst_id=b2.dst_id THEN r.edge_id END) FROM Section s2 JOIN rel_BELONGS_TO_SPEC b2 ON b2.src_id=s2.node_id JOIN Spec sp ON sp.node_id=b2.dst_id LEFT JOIN rel_REFERENCES_SECTION r ON r.dst_id=s2.node_id LEFT JOIN Section s1 ON s1.node_id=r.src_id LEFT JOIN rel_BELONGS_TO_SPEC b1 ON b1.src_id=s1.node_id WHERE sp.specNumber='38.331' GROUP BY s2.sectionId,s2.sectionTitle""",
}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    BASE.mkdir(exist_ok=True)
    index = json.loads((GX / 'mechanical/native_top_k_artifact_index.json').read_text())
    proposals = {x['id']: x for x in map(json.loads, (GX / 'correction_candidate/candidate_contracts.jsonl').read_text().splitlines())}
    native_report = json.loads((GX / 'mechanical/native_top_k_report.json').read_text())
    groups = {x['wg']: x for x in native_report['groups']}
    public = ROOT.parent / 'spectra-public/spec-trace/release_package/cqs/original_core_repair'
    frozen_sources = json.loads((public / 'manifest.json').read_text())['graph_sources']
    report = {'kind': 'Independent full-pool captured-output and frozen SQL count-unit comparison',
              'new_model_calls': 0, 'new_neo4j_calls': 0, 'raw_source_validation_n': 0,
              'human_expert_validation_n': 0, 'items': []}
    connections, database_pins = {}, {}
    try:
        for item in index['items']:
            item_id = item['id']
            wg = item_id.split('_')[0]
            db = EMP / 'relational' / (wg + '.sqlite')
            if wg not in connections:
                database_pins[wg] = sha(db)
                connections[wg] = sqlite3.connect('file:' + str(db) + '?mode=ro&immutable=1', uri=True)
                connections[wg].execute('PRAGMA query_only=ON')
                budget = {'steps': 0}
                def guard(budget=budget):
                    budget['steps'] += 1
                    return 1 if budget['steps'] > 200000 else 0
                connections[wg].set_progress_handler(guard, 1000)
            group = groups[wg]
            assert group['source_before'] == group['source_after'] == frozen_sources[wg]
            assert group['inventory_and_source_pins_unchanged']
            run = item['runs']['uncapped']
            receipt_path = GX / 'mechanical' / run['receipt_file']
            rows_path = GX / 'mechanical' / run['rows_file']
            receipt = json.loads(receipt_path.read_text())
            rows = [json.loads(line) for line in rows_path.read_text().splitlines()]
            candidate = proposals[item_id]
            assert sha(receipt_path) == run['receipt_sha256']
            assert sha(rows_path) == run['rows_sha256'] == receipt['rows_sha256']
            assert receipt['id'] == item_id + '__uncapped'
            assert receipt['query'] == candidate['reference_query']
            assert receipt['query_sha256'] == hashlib.sha256(candidate['reference_query'].encode()).hexdigest()
            assert len(rows) == receipt['rows_retained'] == run['row_count']
            assert receipt['status'] == 'OK' and receipt['rollback_completed'] and receipt['full_rows_available']
            assert not receipt['truncated'] and receipt['execution_summary_complete']
            assert receipt['execution_query_type'] == receipt['plan_query_type'] == 'r'
            named = [dict(zip(receipt['columns'], row)) for row in rows]
            ids, count_field, query = QUERIES[item_id]
            captured = {tuple(row[field] for field in ids): row[count_field] for row in named}
            assert len(captured) == len(named)
            actual = connections[wg].execute(query).fetchall()
            separate = {tuple(row[:-2]): row[-2] for row in actual}
            assert len(separate) == len(actual)
            assert captured == separate
            count_differences = sum(row[-2] != row[-1] for row in actual)
            limit = candidate['cardinality_policy']['value']
            cutoff = sorted(captured.values(), reverse=True)[min(limit, len(captured))-1]
            universe = None
            if item_id in UNIVERSES:
                complete = connections[wg].execute(UNIVERSES[item_id]).fetchall()
                full = {tuple(row[:-1]): row[-1] for row in complete}
                assert len(full) == len(complete)
                positive = {key:value for key,value in full.items() if value > 0}
                assert positive == captured and cutoff > 0
                universe = {'query': UNIVERSES[item_id], 'all_identity_n': len(full),
                            'zero_count_identity_n': sum(value == 0 for value in full.values()),
                            'all_positive_identity_and_count_exact': True,
                            'omitted_zero_cannot_reach_positive_boundary': True,
                            'scope': 'This frozen source only; uncapped retained native is a positive pool, not every zero-count entity.'}
            record = {'id': item_id, 'native_receipt_id': receipt['id'], 'repair_sha256': candidate['repair_sha256'],
                      'retained_n': len(rows), 'native_query_sha256': receipt['query_sha256'],
                      'receipt_file': str(receipt_path.relative_to(ROOT)), 'receipt_sha256': sha(receipt_path),
                      'rows_file': str(rows_path.relative_to(ROOT)), 'rows_sha256': sha(rows_path),
                      'source_guards_match_published_parent': True, 'distinct_requested_identity_n': len(captured),
                      'null_requested_identity_n': sum(any(v is None for v in identity) for identity in captured),
                      'independent_sql': query, 'independent_sql_all_pool_exact': True,
                      'count_multiplicity_difference_n': count_differences,
                      'positive_boundary_value': cutoff, 'explicit_k': limit,
                      'complete_zero_inclusive_source_witness': universe,
                      'source_scope': 'Frozen graph/SQL equality; original archive content not validated by this check'}
            report['items'].append(record)
    finally:
        for connection in connections.values():
            connection.close()
    report['sql_source_pins'] = {wg: {'sha256_before': value, 'sha256_after': sha(EMP / 'relational' / (wg + '.sqlite'))}
                                 for wg, value in database_pins.items()}
    assert all(x['sha256_before'] == x['sha256_after'] for x in report['sql_source_pins'].values())
    report['captured_native_rows_n'] = sum(x['retained_n'] for x in report['items'])
    report['all_pool_exact_n'] = len(report['items'])
    report['status'] = 'PASS'
    out = BASE / 'source_native_audit.json'
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': 'PASS', 'items': len(report['items']), 'rows': report['captured_native_rows_n'],
                      'multiplicity_differences': {x['id']:x['count_multiplicity_difference_n'] for x in report['items']},
                      'sha256': sha(out)}))


if __name__ == '__main__':
    main()
