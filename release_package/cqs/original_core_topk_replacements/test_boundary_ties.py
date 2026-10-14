"""Top-k answers accept genuine boundary alternatives and reject rank errors."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.append(str(Path(__file__).resolve().parent.parent))
import original_scorer
import contract_checks


class BoundaryTiesTests(unittest.TestCase):
    def setUp(self):
        self.contract = {
            'validation_status': 'validated',
            'required_fields': [{'name': 'entity', 'type': 'string', 'nullable': False}],
            'collection': {'kind': 'top_k_boundary_ties', 'value': 3,
                           'source_order_keys': [{'source_column': 'count', 'direction': 'desc'}],
                           'tie_policy': 'any_subset_at_boundary', 'within_tie_order': 'any',
                           'require_rank_order': False},
            'cardinality_policy': {'mode': 'top_k', 'value': 3, 'tie_policy': 'any_subset_at_boundary'}}
        self.native = [{'entity': key, 'count': value} for key, value in
                       [('A', 9), ('B', 8), ('C', 8), ('D', 8), ('E', 7)]]
        self.gold = [{'entity': row['entity']} for row in self.native]
        self.groups = original_scorer.make_order_groups(self.contract, self.native, self.gold)

    def score(self, keys):
        return original_scorer.score(self.contract, self.gold, [{'entity': k} for k in keys],
                                     order_groups=self.groups)

    def test_boundary_subset_is_not_fixed_to_arbitrary_ids(self):
        self.assertTrue(self.score(['A', 'B', 'C'])['exact'])
        self.assertTrue(self.score(['A', 'C', 'D'])['exact'])

    def test_top_selection_does_not_impose_unrequested_display_order(self):
        self.assertTrue(self.score(['D', 'A', 'C'])['exact'])

    def test_explicit_rank_order_keeps_freedom_within_boundary(self):
        self.contract['collection']['require_rank_order'] = True
        self.assertTrue(self.score(['A', 'D', 'C'])['exact'])
        self.assertFalse(self.score(['D', 'A', 'C'])['exact'])

    def test_higher_rank_is_mandatory(self):
        self.assertFalse(self.score(['B', 'C', 'D'])['exact'])

    def test_lower_rank_cannot_displace_boundary(self):
        self.assertFalse(self.score(['A', 'B', 'E'])['exact'])

    def test_duplicate_and_unknown_records_fail(self):
        self.assertFalse(self.score(['A', 'B', 'B'])['exact'])
        self.assertFalse(self.score(['A', 'B', 'unknown'])['exact'])

    def test_requested_type_and_exact_cardinality_stay_strict(self):
        self.assertFalse(self.score(['A', 'B'])['exact'])
        self.assertFalse(self.score(['A', 'B', 'C', 'D'])['exact'])
        self.assertFalse(self.score(['A', 'B', 1])['exact'])

    def test_unrequested_count_cannot_change_eligibility(self):
        rows = [dict(row, count=-1) for row in self.gold[:3]]
        self.assertTrue(original_scorer.score(self.contract, self.gold, rows, order_groups=self.groups)['exact'])

    def test_requested_count_is_checked_with_entity(self):
        self.contract['required_fields'].append({'name': 'count', 'type': 'integer', 'nullable': False})
        groups = original_scorer.make_order_groups(self.contract, self.native, self.native)
        rows = [dict(row) for row in self.native[:3]]
        rows[1]['count'] = 100
        self.assertFalse(original_scorer.score(self.contract, self.native, rows, order_groups=groups)['exact'])

    def test_small_population_and_empty_population(self):
        for n in [0, 2]:
            rows, gold = self.native[:n], self.gold[:n]
            groups = original_scorer.make_order_groups(self.contract, rows, gold)
            self.assertTrue(original_scorer.score(self.contract, gold, gold, order_groups=groups)['exact'])

    def test_duplicate_or_ambiguous_rank_source_is_rejected(self):
        with self.assertRaises(ValueError):
            original_scorer.make_order_groups(self.contract, self.native[:2], [self.gold[0], self.gold[0]])

    def test_partial_credit_denominator_is_requested_k(self):
        result = self.score(['A', 'B', 'E'])
        self.assertEqual(result['matched_records'], 2)
        self.assertEqual(result['gold_records'], 3)
        self.assertAlmostEqual(result['f1'], 2 / 3)

    def test_actual_positive_and_negative_controls(self):
        self.assertTrue(all(check['pass'] for check in contract_checks.checks(self.contract, self.gold, self.groups)))

    def test_inconsistent_boundary_definition_is_rejected(self):
        self.contract['cardinality_policy']['value'] = 2
        with self.assertRaises(ValueError):
            self.score(['A', 'B', 'C'])


if __name__ == '__main__':
    unittest.main()
