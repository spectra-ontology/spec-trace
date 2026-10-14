"""Ordering remains enforceable without grading unrequested source metadata."""
from pathlib import Path
import sys
import unittest
from decimal import Decimal
sys.path.append(str(Path(__file__).resolve().parent.parent))
import original_scorer


class NativeOrderTests(unittest.TestCase):
    def setUp(self):
        self.contract = {'validation_status': 'validated',
                         'required_fields': [{'name': 'document', 'type': 'string', 'nullable': False}],
                         'collection': {'kind': 'native_ordered_ties', 'tie_policy': 'any_order_within_equal_keys',
                                        'source_order_keys': [{'source_column': 'meetingInt', 'direction': 'desc'}]},
                         'cardinality_policy': {'mode': 'all'}}
        self.native = [{'document': 'A', 'meetingInt': 109}, {'document': 'B', 'meetingInt': 109},
                       {'document': 'C', 'meetingInt': 108}]
        self.gold = [{'document': x['document']} for x in self.native]
        self.groups = original_scorer.make_order_groups(self.contract, self.native, self.gold)

    def score(self, rows):
        return original_scorer.score(self.contract, self.gold, rows, order_groups=self.groups)

    def test_auxiliary_value_not_required_in_answer(self):
        self.assertTrue(self.score(self.gold)['exact'])

    def test_order_within_real_tie_is_free(self):
        self.assertTrue(self.score([self.gold[1], self.gold[0], self.gold[2]])['exact'])

    def test_crossing_rank_boundary_is_not_exact(self):
        self.assertFalse(self.score([self.gold[2], self.gold[0], self.gold[1]])['exact'])

    def test_unknown_and_missing_documents_fail(self):
        self.assertFalse(self.score([{'document': 'unknown'}] + self.gold[1:])['exact'])
        self.assertFalse(self.score(self.gold[:-1])['exact'])

    def test_wrong_native_sort_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'violate requested ordering'):
            original_scorer.make_order_groups(self.contract, self.native[::-1], self.gold[::-1])

    def test_same_visible_answer_at_two_ranks_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'ambiguous native rank'):
            original_scorer.make_order_groups(self.contract, self.native, [self.gold[0], self.gold[1], self.gold[0]])

    def test_wrong_requested_value_type_fails(self):
        self.assertFalse(self.score([{'document': 1}] + self.gold[1:])['exact'])

    def test_auxiliary_answer_noise_is_ignored(self):
        self.assertTrue(self.score([dict(row, meetingInt=-100) for row in self.gold])['exact'])

    def test_decimal_source_key_keeps_order_without_float_rounding(self):
        native = [dict(row, meetingInt=Decimal(value)) for row, value in zip(
            self.native, ['1.000000000000000000002', '1.000000000000000000001', '1'])]
        groups = original_scorer.make_order_groups(self.contract, native, self.gold)
        self.assertFalse(original_scorer.score(self.contract, self.gold,
                          [self.gold[1], self.gold[0], self.gold[2]], order_groups=groups)['exact'])

    def test_nonfinite_source_key_is_rejected(self):
        native = [dict(self.native[0], meetingInt=Decimal('NaN'))] + self.native[1:]
        with self.assertRaises(ValueError):
            original_scorer.make_order_groups(self.contract, native, self.gold)


if __name__ == '__main__':
    unittest.main()
