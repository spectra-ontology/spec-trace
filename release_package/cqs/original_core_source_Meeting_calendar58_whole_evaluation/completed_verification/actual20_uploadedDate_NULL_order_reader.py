"""Compare all retained structured identities with their immutable source properties."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3

HERE = Path(__file__).resolve().parent
RUN = HERE.parent / 'RAN1/source_variant_OpenRouter_registration/source58_fullbody_v2/run'
OUT = HERE / 'source58_actual_structured20_uploadedDate_NULL_order_diagnostic.json'


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for value in iter(lambda: stream.read(1048576), b''):
            result.update(value)
    return result.hexdigest()


def pin(path):
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def main():
    assert not OUT.exists()
    protocol = json.loads((RUN / 'protocol.json').read_text())
    database = Path(protocol['source_pins']['sql_db_path']['path'])
    before = pin(database)
    assert before == protocol['source_pins']['sql_db_path']
    connection = sqlite3.connect('file:' + str(database) + '?mode=ro&immutable=1', uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA query_only=ON')
    population = [dict(row) for row in connection.execute('''
        SELECT cr.node_id, cr.tdocNumber, cr.uploadedDate, n.properties_json
        FROM CR cr JOIN _node_record n ON n.node_id=cr.node_id
        WHERE EXISTS (
          SELECT 1 FROM rel_MODIFIES link JOIN Spec s ON s.node_id=link.dst_id
          WHERE link.src_id=cr.node_id AND s.specNumber='38.133'
        )
    ''')]
    by_document = {row['tdocNumber']: row for row in population}
    assert len(by_document) == len(population) == 16017
    for row in population:
        assert json.loads(row['properties_json']).get('uploadedDate') == row['uploadedDate']
    native_receipts = {}
    all20 = []
    for method in ('text2cypher', 'text2sql'):
        path = RUN / 'executed' / method / 'RAN4_P3_CQ3-3.json'
        receipt = json.loads(path.read_text())
        assert receipt['status'] == 'OK' and receipt['execution']['complete'] is True
        assert receipt['execution']['truncated'] is False and len(receipt['records']) == 10
        assert 'uploadedDate' in receipt['generated_query'] and 'sourceReported' not in receipt['generated_query']
        observations = []
        for ordinal, answer in enumerate(receipt['records']):
            source = by_document[answer['tdocNumber']]
            meetings = [dict(row) for row in connection.execute('''
              SELECT m.node_id, m.canonicalMeetingNumber, m.sourceReportedStartDate, m.sourceReportedEndDate
              FROM Meeting m JOIN rel_PRESENTED_AT p ON p.dst_id=m.node_id WHERE p.src_id=?
            ''', (source['node_id'],))]
            assert len(meetings) == 1
            raw = json.loads(source['properties_json'])
            row = {'method': method, 'returned_position_zero_based': ordinal,
                'tdocNumber': source['tdocNumber'], 'node_id': source['node_id'],
                'CR_uploadedDate': source['uploadedDate'], 'loaded_node_uploadedDate_present': 'uploadedDate' in raw,
                'loaded_node_uploadedDate': raw.get('uploadedDate'), 'source_Meeting': meetings[0]}
            observations.append(row)
            all20.append(row)
        native_receipts[method] = {'retained_execution_pin': pin(path), 'actual_query': receipt['generated_query'],
            'query_sha256': receipt['query_sha256'], 'actual_uploadedDate_values_in_return_order': [row['CR_uploadedDate'] for row in observations]}
    null_n = sum(row['uploadedDate'] is None for row in population)
    known = [row['uploadedDate'] for row in population if row['uploadedDate'] is not None]
    assert all(type(value) is str for value in known)
    cypher_values = native_receipts['text2cypher']['actual_uploadedDate_values_in_return_order']
    sql_values = native_receipts['text2sql']['actual_uploadedDate_values_in_return_order']
    assert cypher_values == [None] * 10 and all(value is not None for value in sql_values)
    assert sql_values == sorted(known, reverse=True)[:10]
    native_receipts['text2sql']['all_ten_values_equal_full_population_nonnull_DESC_top10'] = True
    native_receipts['text2cypher']['all_ten_source_values_are_NULL_despite_known_population_values'] = True
    result = {'status': 'actual_all20_source_property_corroboration_pass', 'original_query_outputs_modified': False,
        'source_database_pin_before': before, 'source_database_pin_after': pin(database),
        'complete_original_named_spec_CR_population_n': len(population), 'source_uploadedDate_NULL_n': null_n,
        'source_uploadedDate_nonNULL_n': len(known), 'source_uploadedDate_nonNULL_type_counts': dict(Counter(type(value).__name__ for value in known)),
        'actual_retained_structured_executions': native_receipts, 'all20_returned_identity_source_observations': all20,
        'observed_explanation': 'The actual Cypher output contains ten source NULL uploadedDate values, while the actual SQLite output contains the full population non-NULL descending top-ten values. Thus NULL placement separates these saved outputs. The Cypher NULL-group identity selection is unspecified because neither generated query adds a within-equal-value tie break.',
        'semantic_limit': 'Neither query uses the required source-reported Meeting calendar periods. A matching SQL requested-record output is not a proof of calendar-recency semantics. No live Neo4j query or modified query was run by this diagnosis.',
        'helper_pin': pin(Path(__file__)), 'human_author_review_completed': False, 'expert_validation_n': 0,
        'new_native_API_public_calls_n': 0}
    assert result['source_database_pin_before'] == result['source_database_pin_after']
    OUT.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'output_pin': pin(OUT), 'NULL_n': null_n, 'nonNULL_n': len(known)}))


if __name__ == '__main__':
    main()
