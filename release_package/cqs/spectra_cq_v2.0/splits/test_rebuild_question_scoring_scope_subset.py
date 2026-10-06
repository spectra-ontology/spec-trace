"""Synthetic integrity tests; these do not assess the recorded AI judgments.

Only the published protocol/input and original source files form the fixture.
Synthetic statuses exercise rejection and selection rules without reading any
prediction or score artifact. No released file is modified by these tests.
"""
import copy
from collections import Counter
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import rebuild_question_scoring_scope_subset as checker


class IntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        record = checker.load_json((checker.CQ / checker.RECORD_NAME).read_text(encoding='utf-8'))
        cls.protocol = record['protocol_text']
        cls.bundle = record['input']

    @staticmethod
    def seal(record, reviewer):
        text = json.dumps(record['reviews'][reviewer], ensure_ascii=False, indent=2) + '\n'
        record['individual_review_text'][reviewer] = text
        record['individual_review_sha256'][reviewer] = checker.digest(text.encode('utf-8'))

    @staticmethod
    def summaries(record):
        record['status_counts'] = {
            name: {
                'overall': dict(Counter(row['overall_status'] for row in review['items'])),
                'axes': {axis: dict(Counter(row['axes'][axis]['status'] for row in review['items']))
                         for axis in checker.AXES},
            } for name, review in record['reviews'].items()
        }
        a = {row['id']: row['overall_status'] for row in record['reviews']['a']['items']}
        b = {row['id']: row['overall_status'] for row in record['reviews']['b']['items']}
        record['same_overall_status_count'] = sum(a[cid] == b[cid] for cid in a)

    def fixture(self, status='compatible'):
        rows = [{
            'id': item['id'],
            'axes': {axis: {'status': status,
                            'reason': 'Synthetic integrity-test evidence: `'
                                      + item['scored_answer_column'] + '`.'}
                     for axis in checker.AXES},
            'overall_status': status,
        } for item in self.bundle['items']]
        reviews = {name: {
            'protocol_sha256': checker.PROTOCOL_SHA256,
            'input_sha256': checker.INPUT_SHA256,
            'reviewer_type': checker.REVIEWER_TYPE,
            'items': copy.deepcopy(rows),
        } for name in ('a', 'b')}
        ids = [item['id'] for item in self.bundle['items']] if status == 'compatible' else []
        record = {
            'schema': checker.SCHEMA,
            'protocol_text': self.protocol,
            'protocol_sha256': checker.PROTOCOL_SHA256,
            'input': copy.deepcopy(self.bundle),
            'input_sha256': checker.INPUT_SHA256,
            'reviews': reviews,
            'individual_review_text': {},
            'individual_review_sha256': {},
            'selected_ids': ids,
            'selected_n': len(ids),
            'frozen_before_new_subset_scoring_utc': '2026-10-07T00:00:00+00:00',
            'limits': ['Synthetic tests only; not actual AI judgments.'],
        }
        for name in ('a', 'b'):
            self.seal(record, name)
        self.summaries(record)
        return record

    def test_original_sources_with_synthetic_all_compatible(self):
        record = self.fixture()
        self.assertEqual(checker.validate_record(record), record['selected_ids'])

    def test_source_hash_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            target = Path(name)
            for relative in checker.SOURCE_NAMES:
                output = target / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes((checker.CQ / relative).read_bytes())
            with (target / 'benchmark.jsonl').open('ab') as output:
                output.write(b'\n')
            with self.assertRaisesRegex(ValueError, 'source changed'):
                checker.validate_record(self.fixture(), target)

    def test_protocol_self_consistent_edit_is_rejected(self):
        record = self.fixture()
        record['protocol_text'] += 'Altered protocol\n'
        record['protocol_sha256'] = checker.digest(record['protocol_text'].encode('utf-8'))
        with self.assertRaisesRegex(ValueError, 'fixed protocol hash'):
            checker.validate_record(record)

    def test_input_self_consistent_edit_is_rejected(self):
        record = self.fixture()
        record['input']['items'][0]['question'] += ' Altered'
        record['input_sha256'] = checker.digest(checker.canonical_bytes(record['input']))
        with self.assertRaisesRegex(ValueError, 'fixed input hash'):
            checker.validate_record(record)

    def test_source_reconstruction_even_if_input_hash_rebased(self):
        record = self.fixture()
        record['input']['items'][0]['question'] += ' Altered'
        new_hash = checker.digest(checker.canonical_bytes(record['input']))
        record['input_sha256'] = new_hash
        # Bypass only the pinned-input gate to exercise the independent source
        # reconstruction gate. Production code keeps the original pin.
        with patch.object(checker, 'INPUT_SHA256', new_hash):
            with self.assertRaisesRegex(ValueError, 'input fields differ'):
                checker.validate_record(record)

    def test_raw_review_hash_is_checked(self):
        record = self.fixture()
        record['individual_review_text']['a'] += ' '
        with self.assertRaisesRegex(ValueError, 'raw review hash'):
            checker.validate_record(record)

    def test_raw_parse_equality_is_checked(self):
        record = self.fixture()
        record['reviews']['a']['reviewer_type'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'parsed review differs'):
            checker.validate_record(record)

    def test_duplicate_review_ids_are_rejected(self):
        record = self.fixture()
        record['reviews']['a']['items'][-1] = copy.deepcopy(record['reviews']['a']['items'][0])
        self.seal(record, 'a')
        with self.assertRaisesRegex(ValueError, 'duplicate review IDs'):
            checker.validate_record(record)

    def test_missing_axis_is_rejected(self):
        record = self.fixture()
        del record['reviews']['a']['items'][0]['axes'][checker.AXES[0]]
        self.seal(record, 'a')
        with self.assertRaisesRegex(ValueError, 'four axes'):
            checker.validate_record(record)

    def test_invalid_axis_status_is_rejected(self):
        record = self.fixture()
        record['reviews']['a']['items'][0]['axes'][checker.AXES[0]]['status'] = ['compatible']
        self.seal(record, 'a')
        with self.assertRaisesRegex(ValueError, 'bad axis status'):
            checker.validate_record(record)

    def test_overall_rule_is_checked(self):
        record = self.fixture()
        record['reviews']['a']['items'][0]['axes'][checker.AXES[0]]['status'] = 'incompatible'
        self.seal(record, 'a')
        with self.assertRaisesRegex(ValueError, 'overall rule'):
            checker.validate_record(record)

    def test_missing_literal_anchor_is_rejected(self):
        record = self.fixture()
        record['reviews']['a']['items'][0]['axes'][checker.AXES[0]]['reason'] = 'No literal evidence supplied.'
        self.seal(record, 'a')
        with self.assertRaisesRegex(ValueError, 'missing literal source anchor'):
            checker.validate_record(record)

    def test_non_source_quoted_anchor_is_rejected(self):
        record = self.fixture()
        record['reviews']['a']['items'][0]['axes'][checker.AXES[0]]['reason'] = '`definitely_absent_source_token_123456789`'
        self.seal(record, 'a')
        with self.assertRaisesRegex(ValueError, 'missing literal source anchor'):
            checker.validate_record(record)

    def test_overall_summary_is_checked(self):
        record = self.fixture()
        record['status_counts']['a']['overall'] = {'compatible': 132, 'unclear': 1}
        with self.assertRaisesRegex(ValueError, 'overall status counts.*differs'):
            checker.validate_record(record)

    def test_axis_summary_is_checked(self):
        record = self.fixture()
        record['status_counts']['a']['axes'][checker.AXES[0]] = {'compatible': 132, 'unclear': 1}
        with self.assertRaisesRegex(ValueError, 'record axis counts.*differs'):
            checker.validate_record(record)

    def test_agreement_summary_is_checked(self):
        record = self.fixture()
        record['same_overall_status_count'] = 132
        with self.assertRaisesRegex(ValueError, 'agreement count differs'):
            checker.validate_record(record)

    def test_optional_raw_status_summary_is_checked(self):
        record = self.fixture()
        record['reviews']['a']['status_counts'] = {'compatible': 132}
        self.seal(record, 'a')
        with self.assertRaisesRegex(ValueError, 'review status counts'):
            checker.validate_record(record)

    def test_wrong_intersection_is_rejected(self):
        record = self.fixture()
        record['selected_ids'] = record['selected_ids'][:-1]
        record['selected_n'] -= 1
        with self.assertRaisesRegex(ValueError, 'compatible intersection'):
            checker.validate_record(record)

    def test_intersection_uses_both_reviews(self):
        record = self.fixture()
        first = record['reviews']['b']['items'][0]
        first['axes'][checker.AXES[0]]['status'] = 'unclear'
        first['overall_status'] = 'unclear'
        self.seal(record, 'b')
        self.summaries(record)
        record['selected_ids'] = record['selected_ids'][1:]
        record['selected_n'] = 132
        self.assertEqual(checker.validate_record(record), record['selected_ids'])

    def test_empty_intersection_and_exact_empty_file(self):
        self.assertEqual(checker.validate_record(self.fixture('unclear')), [])
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            path = directory / checker.IDS_NAME
            path.parent.mkdir(parents=True)
            path.write_bytes(b'')
            checker.check_shipped_ids([], directory)
            path.write_bytes(b'\n')
            with self.assertRaisesRegex(ValueError, 'shipped intersection bytes'):
                checker.check_shipped_ids([], directory)

    def test_shipped_ids_require_exact_newlines(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            path = directory / checker.IDS_NAME
            path.parent.mkdir(parents=True)
            path.write_bytes(b'alpha\nbeta\n')
            checker.check_shipped_ids(['alpha', 'beta'], directory)
            path.write_bytes(b'alpha\nbeta')
            with self.assertRaisesRegex(ValueError, 'shipped intersection bytes'):
                checker.check_shipped_ids(['alpha', 'beta'], directory)

    def test_duplicate_json_object_keys_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate JSON object key'):
            checker.load_json('{"id":1,"id":2}')

    def test_timestamp_requires_utc(self):
        record = self.fixture()
        record['frozen_before_new_subset_scoring_utc'] = '2026-10-07T00:00:00'
        with self.assertRaisesRegex(ValueError, 'timestamp must be UTC'):
            checker.validate_record(record)

    def test_incompatible_has_priority_over_unclear(self):
        axes = {axis: {'status': 'unclear'} for axis in checker.AXES}
        axes[checker.AXES[0]]['status'] = 'incompatible'
        self.assertEqual(checker.aggregate_status(axes), 'incompatible')


if __name__ == '__main__':
    unittest.main()
