"""Checks for fixed-denominator structured access analysis, without services."""
import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import analyse_structured_access as analysis


def row(cid, values, status='OK', **extra):
    return {'id': cid, 'predicted_values': values, 'exec_status': status,
            'error': None, 'condition': 'sql_grounded', 'model_slug': analysis.MODEL,
            'model_id': 'anthropic/' + analysis.MODEL, **extra}


class FixedPopulation(unittest.TestCase):
    def test_missing_and_errors_remain_zero_in_denominator(self):
        ids = ['ok', 'failed', 'missing']
        key = {cid: {'values': {'answer'}} for cid in ids}
        records = {'ok': row('ok', ['answer']), 'failed': row('failed', [], 'ERROR')}
        scores, summary = analysis.score_arm(ids, key, records, {'ok': 1, 'failed': 1})
        self.assertEqual(summary['n_denominator'], 3)
        self.assertEqual(summary['n_scored_including_zero'], 3)
        self.assertEqual(summary['n_attempted'], 2)
        self.assertEqual(summary['n_query_ok'], 1)
        self.assertEqual(summary['n_query_error'], 1)
        self.assertEqual(summary['n_missing'], 1)
        self.assertEqual(summary['metrics']['f1'], .333333)
        self.assertEqual(scores['failed']['exact'], 0)
        self.assertEqual(scores['missing']['f1'], 0)

    def test_failed_nonempty_prediction_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'nonempty'):
            analysis.score_arm(['a'], {'a': {'values': {'a'}}},
                               {'a': row('a', ['a'], 'ERROR')}, {'a': 1})

    def test_error_cannot_gain_empty_gold_exact_credit(self):
        scores, _ = analysis.score_arm(['a'], {'a': {'values': set()}},
                                       {'a': row('a', [], 'ERROR')}, {'a': 1})
        self.assertEqual(scores['a']['exact'], 0)

    def test_answer_values_normalized_with_order_and_duplicates_ignored(self):
        scores, _ = analysis.score_arm(['a'], {'a': {'values': {'answer one', 'b'}}},
                                       {'a': row('a', [' B ', 'ANSWER   ONE', 'b'])}, {'a': 1})
        self.assertEqual(scores['a']['exact'], 1)

    def test_duplicate_first_record_policy_is_accounted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'all.jsonl.gz'
            with gzip.open(path, 'wt') as stream:
                stream.write(json.dumps(row('a', ['wrong'])) + '\n')
                stream.write(json.dumps(row('a', ['answer'])) + '\n')
                stream.write(json.dumps(row('outside', ['answer'])) + '\n')
            records, counts = analysis.read_run(path, 'sql_grounded')
            scores, summary = analysis.score_arm(['a'], {'a': {'values': {'answer'}}}, records, counts)
            self.assertEqual(scores['a']['f1'], 0)
            self.assertEqual(summary['n_duplicate_ids'], 1)
            self.assertEqual(summary['n_duplicate_records'], 1)
            self.assertEqual(summary['source_log']['n_records'], 3)
            self.assertEqual(summary['source_log']['n_outside_core'], 1)

    def test_foreign_model_record_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'all.jsonl'
            path.write_text(json.dumps(row('a', [], model_slug='different')) + '\n')
            with self.assertRaisesRegex(ValueError, 'model'):
                analysis.read_run(path, 'sql_grounded')

    def test_current_core_membership_and_key_condition(self):
        key, metadata = analysis.load_core(analysis.CQ)
        self.assertEqual(len(key), 560)
        self.assertEqual(set(key), set(metadata))
        self.assertEqual(sum(row['scope_repaired'] for row in metadata.values()), 7)
        # This LS item is scored on direction, not the reference query's first
        # tdoc column. The declared Core key, rather than first-column gold,
        # must therefore supply its label.
        self.assertEqual(metadata['RAN4_P1_CQ4-2']['answer_column'], 'ls.direction')
        self.assertEqual(key['RAN4_P1_CQ4-2']['values'], {'in'})


class PairedBootstrap(unittest.TestCase):
    def test_identical_vectors_have_zero_difference_every_resample(self):
        out = analysis.paired_interval([0., 1., .4], [0., 1., .4], 200, 0, 'python')
        self.assertEqual(out['sql_minus_cypher_f1_ci95'], [0., 0.])
        self.assertFalse(out['sql_above_cypher'])
        self.assertFalse(out['sql_below_cypher'])

    def test_constant_sql_minus_cypher_direction(self):
        out = analysis.paired_interval([.9, .6], [.7, .4], 200, 0, 'python')
        self.assertEqual(out['sql_minus_cypher_f1_ci95'], [.2, .2])
        self.assertTrue(out['sql_above_cypher'])
        reverse = analysis.paired_interval([.7, .4], [.9, .6], 200, 0, 'python')
        self.assertEqual(reverse['sql_minus_cypher_f1_ci95'], [-.2, -.2])
        self.assertTrue(reverse['sql_below_cypher'])

    def test_rounded_zero_does_not_exclude_zero(self):
        out = analysis.paired_interval([1e-8, 1e-8], [0., 0.], 40, 0, 'python')
        self.assertFalse(out['sql_above_cypher'])

    def test_disjoint_item_populations_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'lengths'):
            analysis.paired_interval([1., 0.], [0.], 40, 0, 'python')


class InputSafety(unittest.TestCase):
    def test_scoring_input_and_release_output_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'overwrite'):
            analysis.check_output(analysis.SQL_LOG, [analysis.SQL_LOG])
        with self.assertRaisesRegex(ValueError, 'release datasets'):
            analysis.check_output(analysis.CQ / 'new_result.json', [analysis.SQL_LOG])
        analysis.check_output(analysis.bc.BASE / 'results/new_result.json', [analysis.SQL_LOG])


if __name__ == '__main__':
    unittest.main()
