"""Check conditional list extents while holding calendar order and counts fixed."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sqlite3

HERE = Path(__file__).resolve().parent


def reproduce_extent(database=None):
    witness = json.loads((HERE / 'witnesses/recent_meeting_extent.json').read_text())
    rows = witness['meeting_rows']
    assert len(rows) == len({r['node_id'] for r in rows}) == 58
    assert len({r['canonicalMeetingNumber'] for r in rows}) == 58
    for row in rows:
        assert type(row['tdocs']) is int and row['tdocs'] >= 0
        assert row['tdocs'] == row['presentation_join_occurrences']
        assert row['sourceReportedStartDate'] <= row['sourceReportedEndDate']
    ordered = sorted(rows, key=lambda r: r['sourceReportedEndDate'], reverse=True)
    assert rows == ordered
    comparisons = 0
    for first, second in itertools.combinations(rows, 2):
        assert first['sourceReportedStartDate'] > second['sourceReportedStartDate']
        assert first['sourceReportedEndDate'] > second['sourceReportedEndDate']
        assert tuple(first['existing_identifier_key']) > tuple(second['existing_identifier_key'])
        comparisons += 1
    assert comparisons == 1653
    expected = witness['expected_conditional_results']
    assert expected['k5'] == rows[:5]
    assert expected['k10'] == rows[:10]
    assert {r['node_id'] for r in expected['k5']} < {r['node_id'] for r in expected['k10']}
    case = json.loads((HERE / 'extent_classification_candidates.json').read_text())['cases'][0]
    assert case['id'] == witness['id'] == 'RAN4_P1_CQ5-2'
    assert hashlib.sha256(case['original_question'].encode()).hexdigest() == case['question_sha256']
    assert hashlib.sha256(case['original_query'].encode()).hexdigest() == case['query_sha256']
    criteria = json.loads((HERE / 'sources/semantic_review_criteria.json').read_text())
    for path in case['two_separate_nonblind_AI_reviews']:
        review = json.loads((HERE / path).read_text())
        assert review['id'] == case['id']
        assert review['original_question_sha256'] == case['question_sha256']
        assert set(review['semantic_evidence']) == set(criteria['semantic_units'])
        assert review['admission'] is False
        assert review['expert_validation_n'] == 0
    private_count_replay = 'NOT_RUN; bundled counts are derived observations'
    if database is not None:
        receipt = json.loads((HERE / 'sources/recent_extent_actual_SQL_source_replay.json').read_text())
        connection = sqlite3.connect(database.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
        connection.execute('PRAGMA query_only=ON')
        connection.row_factory = sqlite3.Row
        actual = [dict(row) for row in connection.execute(receipt['SQL'])]
        connection.close()
        assert actual == receipt['whole58_rows']
        for row in actual:
            item = next(item for item in rows if item['node_id'] == row['node_id'])
            assert all(item[key] == value for key, value in row.items())
        private_count_replay = 'PASS; actual immutable database query over58 meetings'
    return {
        'id': case['id'], 'conditional_extent_verification': 'PASS',
        'meeting_records': len(rows), 'calendar_direction_comparisons': comparisons,
        'conditional_result_sizes': [5, 10], 'different_membership': True,
        'archived_graph_count_replay': private_count_replay,
        'replacement_gold_selected': False, 'new_admissions': 0, 'expert_validation_n': 0,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path)
    arguments = parser.parse_args()
    print(json.dumps(reproduce_extent(arguments.database), ensure_ascii=False))
