"""Independently compare original-source prefix, immutable SQL and native output."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import gzip
import hashlib
import json
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
B = next(p for p in HERE.parents if p.name == 'overnight_reaudit')
ROOT = next(p for p in HERE.parents if (p / 'CLAUDE.md').exists())
PUBLIC = Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/cqs/original_core_repair')
sys.path.insert(0, str(PUBLIC))
import scorer
import original_scorer
import contract_checks


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    definition = json.loads((HERE / 'definition.json').read_text())
    source = ROOT / 'ontology/input/tsg/RAN/formal/meetings/RAN1/Final_Report/Final_Report_RAN1-123.docx'
    assert sha(source) == '0fc4f4da372d682fef7585d8f72d2e5ebac3f46e41f8205658e8742b48e11b71'
    packet = HERE.parent / 'RAN1_RAN3_RAN4/loop81_RAN1_FFS_123_full_own_span_and_marker_census'
    with zipfile.ZipFile(source) as archive:
        xml = archive.read('word/document.xml')
        styles = ET.fromstring(archive.read('word/styles.xml'))
    assert hashlib.sha256(xml).hexdigest() == '361ad487a69a1980d91690d792ccaeaa819063572be9d58cafc94fd005bc3ed2'
    w = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    body = list(ET.fromstring(xml).find(w + 'body'))
    pairs = [(i, n) for i, n in enumerate(body) if n.tag in {w + 'p', w + 'tbl'}]
    blocks = [n for _, n in pairs]
    text = lambda n: ''.join(t.text or '' for t in n.iter(w + 't'))
    serial = lambda n: ET.tostring(n, encoding='unicode')
    with gzip.open(packet / 'all286_retained_Agreement_full_raw_own_spans.jsonl.gz', 'rt') as stream:
        spans = list(map(json.loads, stream))
    assert len(spans) == len({r['resolutionId'] for r in spans}) == 286
    positive, coordinates = [], []
    for r in spans:
        lo, hi = r['body_blocks']
        assert [serial(n) for n in blocks[lo:hi]] == r['raw_body_block_xml']
        assert serial(blocks[hi]) == r['next_boundary_block']['xml']
        assert re.match(r'^Agreement(?:\s*[:(]|$)', text(blocks[lo]).strip())
        coordinates.append({'resolutionId': r['resolutionId'], 'filtered_p_tbl_range': [lo, hi],
                            'actual_body_children': [pairs[i][0] for i in range(lo, hi)]})
        if any('FFS' in text(n) for n in blocks[lo:hi]):
            positive.append(r)
    assert len(positive) == 43
    selected = sorted(positive, key=lambda r: r['resolutionId'])[:15]
    source_ids = [r['resolutionId'] for r in selected]
    style_map = {s.get(w + 'styleId'): s for s in styles.findall(w + 'style')}
    special = {w + a for a in ['strike', 'dstrike', 'vanish', 'webHidden']}
    assert not any(n.tag in special for n in styles.find(w + 'docDefaults').iter())
    marker_observations = []
    for row in selected:
        style_ids, markers = {'Normal'}, []
        lo, hi = row['body_blocks']
        for block in blocks[lo:hi]:
            paragraphs = [block] if block.tag == w + 'p' else list(block.iter(w + 'p'))
            for p in paragraphs:
                if 'FFS' not in text(p):
                    continue
                for n in p.iter(w + 'pStyle'):
                    style_ids.add(n.get(w + 'val'))
                assert not any('FFS' in text(n) for tag in ['del', 'moveFrom'] for n in p.iter(w + tag))
                # Selected FFS paragraphs have no removal/hidden declaration in
                # any contributing run; preserve the XML rather than erase it.
                assert not any(n.tag in special for n in p.iter())
                for n in p.iter(w + 'rStyle'):
                    style_ids.add(n.get(w + 'val'))
                markers.append(text(p))
        for style_id in list(style_ids):
            seen = set()
            while style_id:
                assert style_id not in seen
                seen.add(style_id)
                s = style_map[style_id]
                assert not any(n.tag in special for n in s.iter())
                parent = s.find(w + 'basedOn')
                style_id = parent.get(w + 'val') if parent is not None else None
        assert markers
        marker_observations.append({'resolutionId': row['resolutionId'], 'active_FFS_paragraphs': markers})

    database = B.parent / 'relational/RAN1.sqlite'
    assert sha(database) == 'aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
    sql = ('SELECT a.resolutionId,a.content,m.meetingNumber FROM Agreement a '
           'JOIN rel_MADE_AT e ON e.src_id=a.node_id JOIN Meeting m ON m.node_id=e.dst_id '
           'WHERE a.hasFFS=1 ORDER BY m.meetingNumberInt DESC,a.resolutionId ASC LIMIT 15')
    (HERE / 'RAN1_P2_CQ1-5.sql').write_text(sql + ';\n')
    with sqlite3.connect(database.as_uri() + '?mode=ro&immutable=1', uri=True) as db:
        db.execute('PRAGMA query_only=ON')
        relational = [list(row) for row in db.execute(sql)]
        raw_population = list(db.execute('SELECT a.node_id,a.resolutionId,m.node_id,m.meetingNumberInt '
            'FROM Agreement a LEFT JOIN rel_MADE_AT e ON e.src_id=a.node_id '
            'LEFT JOIN Meeting m ON m.node_id=e.dst_id'))
    assert len(relational) == len({r[0] for r in relational}) == 15
    assert [r[0] for r in relational] == source_ids
    calendar_path = B / 'RAN1/P2_CQ1_5_original_FFS_marker_calendar_source_variant_v1/source_only_independent_review_v1/all60_original_Meeting_and_source_calendar_operands.json'
    calendar = json.loads(calendar_path.read_text())
    dates = {r['node_id']: r['sourceReportedEndDate'] for r in calendar}
    assert len(dates) == 60
    assert len(raw_population) == 21288
    assert len({r[0] for r in raw_population}) == 21058
    assert all(r[2] in dates for r in raw_population)
    latest_end = max(dates[r[2]] for r in raw_population)
    assert latest_end == '2025-11-21'
    selected_ids = set(source_ids)
    assert all(dates[r[2]] == latest_end for r in raw_population if r[1] in selected_ids)

    query_sha = hashlib.sha256(definition['reference_query'].encode()).hexdigest()
    native_dir = HERE / 'native/reference_outputs' / definition['id']
    receipt_path = native_dir / (query_sha + '.json')
    receipt = json.loads(receipt_path.read_text())
    assert receipt['status'] == 'OK' and receipt['rows_retained'] == 15
    assert receipt['query'] == definition['original_query']
    assert receipt['plan_query_type'] == receipt['execution_query_type'] == 'r'
    assert receipt['full_rows_available'] and receipt['rollback_completed'] and not receipt['truncated']
    native_path = native_dir / (query_sha + '.jsonl')
    assert sha(native_path) == receipt['rows_sha256']
    native = [json.loads(s) for s in native_path.read_text().splitlines()]
    assert scorer.get_kernel().json_exact(native) == scorer.get_kernel().json_exact(relational)
    records = [{'resolutionId': row[0]} for row in native]
    checks = contract_checks.checks(definition, records)
    predictions = original_scorer.reference_prediction(definition, records)
    additions = [('answer_order_permutation', list(reversed(predictions)), True),
                 ('missing_one_distinct_ID', predictions[:-1], False),
                 ('duplicate_replaces_distinct_ID', predictions[:-1] + predictions[:1], False),
                 ('extra_distinct_ID', predictions + [{'resolutionId': '__EXTRA_AGREEMENT__'}], False)]
    for name, prediction, expected in additions:
        result = original_scorer.score(definition, records, prediction, diagnostic=True)
        checks.append({'check': name, 'pass': result['exact'] is expected})
    assert all(c['pass'] for c in checks)
    output = HERE / 'actual_root_source_SQL_native_and_controls.json'
    assert not output.exists()
    report = {'status': 'PASS_ACTUAL_SOURCE_SQL_NATIVE_AND_CONTROLS',
              'checked_utc': datetime.now(timezone.utc).isoformat(),
              'id': definition['id'], 'repair_sha256': definition['repair_sha256'],
              'source_member_sha256': sha(source), 'document_xml_sha256': hashlib.sha256(xml).hexdigest(),
              'all286_physical_raw_spans_reopened_and_matched': True,
              'source_marker_candidates': 43, 'source_selected_IDs': source_ids,
              'actual_coordinate_mapping': coordinates,
              'root_directly_read_all15_full_span_text': True,
              'selected_active_marker_observations': marker_observations,
              'database_sha256': sha(database), 'SQL': sql,
              'native_receipt_sha256': sha(receipt_path), 'native_rows_sha256': sha(native_path),
              'native_SQL_all3_columns_exact_typed_agreement': True,
              'native_rows': len(native), 'unique_selected_IDs': len(selected_ids),
              'all21058_calendar_operands_present': True, 'actual_madeAt_join_rows': len(raw_population),
              'calendar_evidence_reuse': {'path': str(calendar_path), 'sha256': sha(calendar_path),
                  'actual_today_header_reextraction_claimed': False},
              'source_event_end_for_all_selected': latest_end,
              'actual_scorer_checks': checks, 'new_API_calls': 0, 'admitted': False,
              'limits': ['Optional content/native SQL agreement does not prove authentic content rendering.',
                         'Root reused the previously source-audited all60 calendar ledger; it did not reextract every calendar today.',
                         'Retained286 spans are parser-assisted, with separate heading census counterevidence retained.',
                         'No current-open lifecycle, physical-source universal completeness or whole chronology claim.']}
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    (HERE / 'root_requested_records.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in records))
    print(json.dumps({'status': report['status'], 'proof_sha256': sha(output),
                      'source_spans': 286, 'native_SQL_rows': 15, 'scorer_checks': len(checks), 'API_calls': 0}))


if __name__ == '__main__':
    main()
