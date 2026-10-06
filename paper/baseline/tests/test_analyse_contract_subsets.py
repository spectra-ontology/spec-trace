"""Checks for alignment and bootstrap behavior, without graph/model services."""
import itertools
import random
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import analyse_contract_subsets as analysis
import query_features as features


class RecordRules(unittest.TestCase):
    def test_one_permutation_for_all_rows(self):
        gold = {('a', 'b'), ('c', 'd')}
        scores, _ = analysis.score_records([['b', 'a'], ['d', 'c']], 2, gold, 2)
        self.assertEqual(scores['P']['f1'], 0)
        self.assertEqual(scores['C']['f1'], 1)

    def test_sorted_values_do_not_prove_consistent_roles(self):
        # Each row has the right value bag but the two rows require different
        # alignments. A row-wise oracle would incorrectly report C=1.
        gold = {('a', 'b'), ('d', 'c')}
        scores, collapse = analysis.score_records([['a', 'b'], ['c', 'd']], 2, gold, 2)
        self.assertFalse(collapse)
        self.assertEqual(scores['S']['f1'], 1)
        self.assertEqual(scores['C']['f1'], .5)

    def test_collapse_is_not_a_general_c_le_s_invariant(self):
        gold = {('a', 'b'), ('b', 'a'), ('e', 'f')}
        scores, collapse = analysis.score_records([['a', 'b'], ['b', 'a'], ['c', 'd']], 2, gold, 2)
        self.assertTrue(collapse)
        self.assertGreater(scores['C']['f1'], scores['S']['f1'])

    def test_width_mismatch_and_empty_sets(self):
        scores, _ = analysis.score_records([['a']], 1, {('a', 'b')}, 2)
        self.assertEqual(scores['C'], scores['P'])
        scores, _ = analysis.score_records([], 2, set(), 2)
        self.assertEqual(scores['C']['exact'], 1)
        scores, _ = analysis.score_records([], 2, {('a', 'b')}, 2)
        self.assertEqual(scores['C']['f1'], 0)

    def test_oracle_matches_brute_force_with_duplicates(self):
        rng = random.Random(730)
        for width in range(1, 5):
            for _ in range(35):
                rows = [[rng.choice('abc') for _ in range(width)] for _ in range(rng.randrange(5))]
                gold = {tuple(rng.choice('abc') for _ in range(width)) for _ in range(rng.randrange(5))}
                scored, _ = analysis.score_records(rows, width, gold, width)
                pred = {tuple(row) for row in rows}
                expected = max(analysis.sf.score_sets(
                    {tuple(row[j] for j in perm) for row in pred}, gold)['f1']
                    for perm in itertools.permutations(range(width)))
                self.assertAlmostEqual(scored['C']['f1'], expected)


class Bootstrap(unittest.TestCase):
    def inputs(self):
        return {'answer_column': {'a': [.6, .6], 'b': [.6, .6]}}, {'closed_book/a': [1., 0.], 'rag/b': [0., 1.]}

    def test_reselection_and_common_draws(self):
        graph, text = self.inputs()
        out = analysis.paired_bootstrap(graph, text, 400, 0, 'python', 17)
        scores = out['scores']['answer_column']
        self.assertEqual(scores['model_pair_difference_ci95']['a - b'], [0., 0.])
        self.assertLess(scores['reselected']['model_minus_text_ci95']['a'][1],
                        scores['fixed']['model_minus_text_ci95']['a'][1])
        self.assertEqual(scores['reselected']['models_clear'], 0)

    def test_batch_size_preserves_protocol(self):
        graph, text = self.inputs()
        self.assertEqual(analysis.paired_bootstrap(graph, text, 400, 0, 'python', 1),
                         analysis.paired_bootstrap(graph, text, 400, 0, 'python', 71))

    def test_optional_numpy_matches_standard_library_endpoints(self):
        try:
            import numpy  # noqa: F401
        except ImportError:
            self.skipTest('NumPy is optional')
        graph, text = self.inputs()
        python = analysis.paired_bootstrap(graph, text, 400, 0, 'python')
        numpy = analysis.paired_bootstrap(graph, text, 400, 0, 'numpy')
        python.pop('engine')
        numpy.pop('engine')
        self.assertEqual(python, numpy)

    def test_rounded_zero_does_not_clear(self):
        graph = {'answer_column': {'a': [1e-8, 1e-8]}}
        out = analysis.paired_bootstrap(graph, {'closed_book/a': [0., 0.]}, 40, 0, 'python')
        self.assertEqual(out['scores']['answer_column']['reselected']['models_clear'], 0)


class MeanBoundsAndFeatures(unittest.TestCase):
    def test_external_membership_sorted_and_hashed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ids.txt'
            path.write_text('b\na\n')
            ids, metadata = analysis.load_ids(path, {'a', 'b', 'c'})
            self.assertEqual(ids, ['a', 'b'])
            self.assertEqual(metadata['sha256'], analysis.sha256(path))

    def test_external_membership_rejects_empty_duplicate_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ids.txt'
            for text in ('\n', 'a a', 'a outside'):
                path.write_text(text)
                with self.subTest(text=text), self.assertRaises(ValueError):
                    analysis.load_ids(path, {'a', 'b'})

    def test_mean_bound_against_all_subsets(self):
        rng = random.Random(14)
        lower, upper = ['a', 'b'], list('abcde')
        for _ in range(30):
            values = {i: rng.uniform(-1, 1) for i in upper}
            exhaustive = [sum(values[i] for i in lower + list(extra)) / (2 + len(extra))
                          for size in range(4) for extra in itertools.combinations('cde', size)]
            self.assertAlmostEqual(analysis.extreme_mean(values, lower, upper)[0], min(exhaustive))
            self.assertAlmostEqual(analysis.extreme_mean(values, lower, upper, True)[0], max(exhaustive))

    def test_inverse_arrow_and_string_literal(self):
        query = "MATCH (a:A)<-[:R]-(b:B) WHERE b.x='(c:C)-[:FAKE]->(d:D)' RETURN a"
        triples = features.parse_patterns(query)
        self.assertEqual(triples, [({'B'}, ['R'], {'A'}, False, 'left')])
        self.assertEqual(features.node_labels(query), {'A', 'B'})

    def test_function_map_is_not_a_node(self):
        self.assertEqual(features.node_labels('RETURN f({x: 3})'), set())


if __name__ == '__main__':
    unittest.main()
