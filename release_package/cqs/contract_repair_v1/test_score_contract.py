"""Counterexamples to identifier-only, bag-of-values, and unordered scoring.

These synthetic tests establish scorer behavior, not measured benchmark results
or domain-expert validation of any original question.
"""
import copy
import importlib.util
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("contract_repair_score", ROOT / "score_contract.py")
sc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sc)


def contract(fields=(('company', 'string'), ('count', 'integer')), kind='set', constraints=()):
    return {
        'version': 1, 'item_id': 'synthetic_counterexample', 'status': 'ready',
        'required_fields': [{'name': name, 'type': kind, 'role': name,
                             'source_anchor': 'synthetic question requests ' + name}
                            for name, kind in fields],
        'collection': {'kind': kind}, 'constraints': list(constraints),
        'unresolved_reasons': [],
    }


class RequiredNamedCells(unittest.TestCase):
    def test_wrong_count_cannot_receive_complete_record_credit(self):
        result = sc.score_contract(contract(), [{'company': 'A', 'count': 2}], [{'company': 'A', 'count': 99}])
        self.assertEqual(result['exact'], 0)
        self.assertEqual(result['partial_named_cells']['f1'], 0.5)
        self.assertEqual(result['output_full_records']['f1'], 0)

    def test_missing_required_count_is_penalized_in_both_denominators(self):
        result = sc.score_contract(contract(), [{'company': 'A', 'count': 2}], [{'company': 'A'}])
        self.assertEqual(result['exact'], 0)
        self.assertEqual(result['partial_named_cells']['precision'], 0.5)
        self.assertEqual(result['partial_named_cells']['recall'], 0.5)

    def test_swapped_mapping_roles_are_wrong_despite_same_value_bag(self):
        spec = contract((('sender', 'string'), ('recipient', 'string')))
        result = sc.score_contract(spec, [{'sender': 'A', 'recipient': 'B'}], [{'sender': 'B', 'recipient': 'A'}])
        self.assertEqual(result['exact'], 0)
        self.assertEqual(result['partial_named_cells']['f1'], 0.0)

    def test_wrong_names_cannot_match_the_same_values(self):
        result = sc.score_contract(contract(), [{'company': 'A', 'count': 2}], [{'organization': 'A', 'total': 2}])
        self.assertEqual(result['partial_named_cells']['f1'], 0.0)

    def test_unrequested_field_is_not_an_additional_demand(self):
        result = sc.score_contract(contract(), [{'company': 'A', 'count': 2}],
                                   [{'count': 2, 'company': 'A', 'extra': 'not requested'}])
        self.assertEqual(result['exact'], 1)

    def test_numeric_string_and_boolean_are_not_integer_counts(self):
        for value in ('2', True, 2.0):
            with self.subTest(value=value):
                result = sc.score_contract(contract(), [{'company': 'A', 'count': 2}], [{'company': 'A', 'count': value}])
                self.assertEqual(result['exact'], 0)
                self.assertEqual(result['partial_named_cells']['f1'], 0.5)

    def test_number_equivalence_has_no_rounding_tolerance(self):
        spec = contract((('rate', 'number'),))
        self.assertEqual(sc.score_contract(spec, [{'rate': 1}], [{'rate': 1.0}])['exact'], 1)
        self.assertEqual(sc.score_contract(spec, [{'rate': 0.1}], [{'rate': 0.10001}])['exact'], 0)
        self.assertEqual(sc.score_contract(spec, [{'rate': 10 ** 40}], [{'rate': 10 ** 40 + 1}])['exact'], 0)

    def test_nonfinite_numbers_are_not_valid_gold(self):
        with self.assertRaisesRegex(ValueError, 'gold record'):
            sc.score_contract(contract((('rate', 'number'),)), [{'rate': float('nan')}], [])

    def test_missing_gold_field_blocks_comparison(self):
        with self.assertRaisesRegex(ValueError, 'gold record'):
            sc.score_contract(contract(), [{'company': 'A'}], [{'company': 'A'}])

    def test_string_identifiers_preserve_case_and_whitespace(self):
        spec = contract((('id', 'string'),))
        for predicted in ('a', ' A'):
            self.assertEqual(sc.score_contract(spec, [{'id': 'A'}], [{'id': predicted}])['exact'], 0)


class CollectionSemantics(unittest.TestCase):
    fields = (('id', 'string'),)

    def test_set_discards_duplicate_rows(self):
        result = sc.score_contract(contract(self.fields, 'set'), [{'id': 'A'}, {'id': 'B'}],
                                   [{'id': 'A'}, {'id': 'A'}, {'id': 'B'}])
        self.assertEqual(result['exact'], 1)
        self.assertEqual(result['partial_named_cells']['predicted_opportunities'], 2)

    def test_multiset_penalizes_missing_duplicate(self):
        result = sc.score_contract(contract(self.fields, 'multiset'), [{'id': 'A'}, {'id': 'A'}, {'id': 'B'}],
                                   [{'id': 'A'}, {'id': 'B'}])
        self.assertEqual(result['exact'], 0)
        self.assertEqual(result['partial_named_cells']['precision'], 1)
        self.assertAlmostEqual(result['partial_named_cells']['recall'], 2 / 3)
        self.assertAlmostEqual(result['partial_named_cells']['f1'], 0.8)

    def test_multiset_penalizes_extra_duplicate(self):
        result = sc.score_contract(contract(self.fields, 'multiset'), [{'id': 'A'}, {'id': 'B'}],
                                   [{'id': 'A'}, {'id': 'A'}, {'id': 'B'}])
        self.assertEqual(result['exact'], 0)
        self.assertAlmostEqual(result['partial_named_cells']['precision'], 2 / 3)
        self.assertEqual(result['partial_named_cells']['recall'], 1)

    def test_sequence_rejects_wrong_order(self):
        spec = contract(self.fields, 'sequence')
        result = sc.score_contract(spec, [{'id': 'A'}, {'id': 'B'}], [{'id': 'B'}, {'id': 'A'}])
        self.assertEqual(result['exact'], 0)
        self.assertEqual(result['partial_named_cells']['f1'], 0)

    def test_tie_group_permutation_allowed_but_group_order_not_allowed(self):
        spec = contract((('id', 'string'), ('score', 'integer')), 'ordered_ties')
        spec['collection'].update(order_keys=[{'field': 'score', 'direction': 'desc'}],
                                  tie_policy='any_order_within_equal_keys')
        gold = [{'id': 'A', 'score': 3}, {'id': 'B', 'score': 3}, {'id': 'C', 'score': 2}]
        self.assertEqual(sc.score_contract(spec, gold, [gold[1], gold[0], gold[2]])['exact'], 1)
        wrong = sc.score_contract(spec, gold, [gold[2], gold[0], gold[1]])
        self.assertEqual(wrong['exact'], 0)
        self.assertEqual(wrong['partial_named_cells']['f1'], 0)

    def test_noncontiguous_tie_group_is_wrong(self):
        spec = contract((('id', 'string'), ('score', 'integer')), 'ordered_ties')
        spec['collection'].update(order_keys=[{'field': 'score', 'direction': 'desc'}],
                                  tie_policy='any_order_within_equal_keys')
        gold = [{'id': 'A', 'score': 3}, {'id': 'B', 'score': 3}, {'id': 'C', 'score': 2}]
        result = sc.score_contract(spec, gold, [gold[0], gold[2], gold[1]])
        self.assertEqual(result['exact'], 0)
        self.assertLess(result['partial_named_cells']['f1'], 1)

    def test_unsorted_gold_is_not_relabelled_as_model_failure(self):
        spec = contract((('id', 'string'), ('score', 'integer')), 'ordered_ties')
        spec['collection'].update(order_keys=[{'field': 'score', 'direction': 'desc'}],
                                  tie_policy='any_order_within_equal_keys')
        with self.assertRaisesRegex(ValueError, 'gold records violate'):
            sc.score_contract(spec, [{'id': 'A', 'score': 2}, {'id': 'B', 'score': 3}], [])

    def test_optimal_assignment_avoids_greedy_cell_credit(self):
        spec = contract((('left', 'string'), ('right', 'string')), 'multiset')
        gold = [{'left': 'A', 'right': 'X'}, {'left': 'A', 'right': 'Y'}]
        predicted = [{'left': 'A', 'right': 'Y'}, {'left': 'B', 'right': 'X'}]
        result = sc.score_contract(spec, gold, predicted)
        self.assertEqual(result['partial_named_cells']['correct_cells'], 3)
        self.assertEqual(result['partial_named_cells']['f1'], 0.75)

    def test_assignment_matches_exhaustive_small_oracle(self):
        rng = random.Random(17)
        for n, m in itertools.product(range(1, 5), repeat=2):
            for _ in range(12):
                predicted = [tuple(('string', rng.choice('ABC')) for _ in range(3)) for _ in range(n)]
                gold = [tuple(('string', rng.choice('ABC')) for _ in range(3)) for _ in range(m)]
                left, right = (predicted, gold) if n <= m else (gold, predicted)
                expected = max(sum(sum(a == b for a, b in zip(row, right[j]))
                                   for row, j in zip(left, selected))
                               for selected in itertools.permutations(range(len(right)), len(left)))
                self.assertEqual(sc.max_cell_assignment(predicted, gold), expected)

    def test_exact_2000_record_set_and_multiset_skip_assignment(self):
        records = [{'id': str(index), 'count': index} for index in range(2000)]
        for kind in ('set', 'multiset'):
            with mock.patch.object(sc, 'max_cell_assignment', side_effect=AssertionError('unnecessary assignment')):
                result = sc.score_contract(contract((('id', 'string'), ('count', 'integer')), kind), records, records)
            self.assertEqual(result['output_exact'], 1)
            self.assertEqual(result['partial_named_cells']['correct_cells'], 4000)
            self.assertEqual(result['output_full_records']['correct_records'], 2000)

    def test_one_wrong_cell_in_2000_records_has_residual_assignment(self):
        records = [{'id': str(index), 'count': index} for index in range(2000)]
        prediction = copy.deepcopy(records)
        prediction[-1]['count'] = -1
        result = sc.score_contract(contract((('id', 'string'), ('count', 'integer'))), records, prediction)
        self.assertEqual(result['partial_named_cells']['correct_cells'], 3999)
        self.assertEqual(result['output_full_records']['correct_records'], 1999)


class ScopeExtentAndUnresolved(unittest.TestCase):
    def test_wrong_or_missing_scope_vetoes_matching_requested_values(self):
        guard = {'kind': 'scope', 'field': 'wg', 'value': 'RAN4',
                 'verification': 'record_field', 'source_anchor': 'synthetic question says RAN4'}
        spec = contract(constraints=[guard])
        gold = [{'company': 'A', 'count': 2, 'wg': 'RAN4'}]
        for predicted in ({'company': 'A', 'count': 2, 'wg': 'RAN5'}, {'company': 'A', 'count': 2}):
            result = sc.score_contract(spec, gold, [predicted])
            self.assertEqual(result['output_exact'], 1)
            self.assertEqual(result['exact'], 0)
            self.assertEqual(result['constraint_checks'][0]['status'], 'fail')

    def test_unobservable_scope_is_indeterminate_not_a_pass(self):
        guard = {'kind': 'scope', 'field': 'wg', 'value': 'RAN4',
                 'verification': 'unresolved', 'source_anchor': 'scope not returned by reference query'}
        gold = [{'company': 'A', 'count': 2}]
        result = sc.score_contract(contract(constraints=[guard]), gold, gold)
        self.assertEqual(result['output_exact'], 1)
        self.assertIsNone(result['exact'])
        self.assertEqual(result['assessment'], 'indeterminate')
        self.assertFalse(result['semantic_validation'])

    def test_reference_query_scope_does_not_certify_prediction_scope(self):
        guard = {'kind': 'scope', 'field': 'source_population', 'value': 'RAN4',
                 'verification': 'reference_query', 'source_anchor':
                 {'question': 'synthetic RAN4 task', 'query': 'synthetic scoped reference query'}}
        gold = [{'company': 'A', 'count': 2}]
        result = sc.score_contract(contract(constraints=[guard]), gold, gold)
        self.assertEqual(result['output_exact'], 1)
        self.assertEqual(result['output_full_records']['f1'], 1)
        self.assertIsNone(result['exact'])
        self.assertEqual(result['constraint_checks'][0]['status'], 'unverifiable')

    def test_unspecified_cap_does_not_gain_contract_certification(self):
        guard = {'kind': 'cardinality', 'mode': 'unresolved', 'verification': 'unresolved',
                 'source_anchor': 'list all question has unrequested LIMIT 10'}
        gold = [{'company': 'A', 'count': 2}]
        result = sc.score_contract(contract(constraints=[guard]), gold, gold)
        self.assertIsNone(result['exact'])
        self.assertEqual(result['constraint_checks'][0]['status'], 'unverifiable')

    def test_declared_extent_catches_truncated_and_oversized_outputs(self):
        guard = {'kind': 'cardinality', 'mode': 'exact', 'value': 2,
                 'verification': 'gold_records', 'source_anchor': 'return exactly two records'}
        spec = contract((('id', 'string'),), constraints=[guard])
        gold = [{'id': 'A'}, {'id': 'B'}]
        for prediction in (gold[:1], gold + [{'id': 'C'}]):
            result = sc.score_contract(spec, gold, prediction)
            self.assertEqual(result['exact'], 0)
            self.assertEqual(result['constraint_checks'][0]['status'], 'fail')

    def test_gold_that_violates_declared_cap_is_rejected(self):
        guard = {'kind': 'cardinality', 'mode': 'at_most', 'value': 1,
                 'verification': 'gold_records', 'source_anchor': 'top one question'}
        with self.assertRaisesRegex(ValueError, 'gold violates'):
            sc.score_contract(contract((('id', 'string'),), constraints=[guard]), [{'id': 'A'}, {'id': 'B'}], [])

    def test_top_k_with_cutoff_ties_requires_complete_supplied_tie_group(self):
        guard = {'kind': 'cardinality', 'mode': 'top_k', 'value': 2, 'tie_policy': 'include_cutoff_ties',
                 'verification': 'gold_records', 'source_anchor': 'top two including all cutoff ties'}
        spec = contract((('id', 'string'), ('score', 'integer')), 'ordered_ties', [guard])
        spec['collection'].update(order_keys=[{'field': 'score', 'direction': 'desc'}],
                                  tie_policy='any_order_within_equal_keys')
        gold = [{'id': 'A', 'score': 3}, {'id': 'B', 'score': 2}, {'id': 'C', 'score': 2}]
        self.assertEqual(sc.score_contract(spec, gold, [gold[0], gold[2], gold[1]])['exact'], 1)
        truncated = sc.score_contract(spec, gold, gold[:2])
        self.assertEqual(truncated['exact'], 0)
        self.assertEqual(truncated['constraint_checks'][0]['status'], 'fail')

    def test_top_k_without_tie_policy_is_not_implicitly_completed(self):
        guard = {'kind': 'cardinality', 'mode': 'top_k', 'value': 2,
                 'verification': 'gold_records', 'source_anchor': 'top two, ties unspecified'}
        with self.assertRaisesRegex(ValueError, 'cutoff tie policy'):
            sc.score_contract(contract((('id', 'string'),), constraints=[guard]), [], [])

    def test_unresolved_contract_keeps_conditional_score_without_exact_claim(self):
        spec = contract()
        spec.update(status='unresolved', unresolved_reasons=['required role cannot be resolved from available source'])
        gold = [{'company': 'A', 'count': 2}]
        result = sc.score_contract(spec, gold, gold)
        self.assertIsNone(result['exact'])
        self.assertEqual(result['output_exact'], 1)
        self.assertEqual(result['partial_named_cells']['f1'], 1)

    def test_source_anchor_and_unique_names_are_required(self):
        for mutate in (lambda spec: spec['required_fields'][0].pop('source_anchor'),
                       lambda spec: spec['required_fields'].append(copy.deepcopy(spec['required_fields'][0]))):
            spec = contract()
            mutate(spec)
            with self.assertRaises(ValueError):
                sc.validate_contract(spec)

    def test_empty_and_failed_prediction_have_explicit_opportunities(self):
        spec = contract((('id', 'string'),))
        result = sc.score_contract(spec, [{'id': 'A'}], [])
        self.assertEqual(result['exact'], 0)
        self.assertEqual(result['partial_named_cells']['f1'], 0)
        self.assertEqual(result['partial_named_cells']['predicted_opportunities'], 0)
        self.assertEqual(sc.score_contract(spec, [], [])['exact'], 1)

    def test_cli_scores_named_envelope_without_modifying_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / name for name in ('contract.json', 'gold.json', 'prediction.json')]
            content = [contract(), {'records': [{'company': 'A', 'count': 2}]},
                       {'records': [{'company': 'A', 'count': 2}], 'abstain': False}]
            for path, value in zip(paths, content):
                path.write_text(json.dumps(value))
            before = [path.read_bytes() for path in paths]
            process = subprocess.run([sys.executable, str(ROOT / 'score_contract.py'),
                                      '--contract', str(paths[0]), '--gold', str(paths[1]),
                                      '--prediction', str(paths[2])], capture_output=True, text=True, check=True)
            result = json.loads(process.stdout)
            self.assertEqual(result['exact'], 1)
            self.assertEqual(before, [path.read_bytes() for path in paths])
            self.assertEqual(result['measurement_scope'], 'supplied_records_only')


if __name__ == '__main__':
    unittest.main()
