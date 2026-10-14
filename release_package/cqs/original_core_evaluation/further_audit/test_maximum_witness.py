"""Exercise the new source-pool admission gate without DB/model calls."""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import further_original as admission


class MaximumPoolGateTests(unittest.TestCase):
    def test_all_zero_pool_requires_every_identity(self):
        maximum, records = admission.derive_complete_maximum(
            [{'sectionId':'s1','referenceCount':0}, {'sectionId':'s2','referenceCount':0}], ['sectionId'])
        self.assertEqual(maximum, 0)
        self.assertEqual(records, [{'sectionId':'s1'}, {'sectionId':'s2'}])

    def test_duplicate_source_identity_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicated'):
            admission.derive_complete_maximum(
                [{'sectionId':'s','referenceCount':1}, {'sectionId':'s','referenceCount':2}], ['sectionId'])

    def test_bool_is_not_frequency_count(self):
        with self.assertRaisesRegex(ValueError, 'type invalid'):
            admission.derive_complete_maximum([{'sectionId':'s','referenceCount':True}], ['sectionId'])

    def test_invalid_or_extra_pool_field_rejected(self):
        with self.assertRaisesRegex(ValueError, 'fields differ'):
            admission.derive_complete_maximum([{'sectionId':'s','referenceCount':2,'extra':'x'}], ['sectionId'])

    def test_actual_two_captured_argmax_sets_and_mutations(self):
        proposals, reviews, selected = admission.inputs()
        admission.continuation.RUN = admission.RUN
        for identifier in sorted(admission.MAXIMUM_REQUIRED):
            task = selected[identifier]
            rows, receipt = admission.continuation.references(task)
            self.assertIsNotNone(rows)
            records = admission.continuation.native.answer_projection(rows, task['required_fields'], receipt['columns'])
            witness = admission.maximum_witness(task, records, receipt)
            self.assertTrue(witness['native_argmax_matches_complete_source_pool'])
            self.assertEqual(witness['maximum_tie_n'], len(records))
            self.assertGreater(len(records), 1)
            # Cache only the source files already hash-checked by the positive
            # gate. These mutations exercise answer equivalence, not I/O.
            real_sha = admission.continuation.sha
            cache = {}
            def cached_sha(path):
                key = str(path)
                if key not in cache:
                    cache[key] = real_sha(path)
                return cache[key]
            with patch.object(admission.continuation, 'sha', side_effect=cached_sha):
                with self.assertRaisesRegex(ValueError, 'omits or changes'):
                    admission.maximum_witness(task, records[:-1], receipt)
                with self.assertRaisesRegex(ValueError, 'omits or changes'):
                    admission.maximum_witness(task, records + [records[0]], receipt)
                incorrect = copy.deepcopy(records)
                incorrect[0][task['required_fields'][0]['name']] = '__unseen_wrong_identity__'
                with self.assertRaisesRegex(ValueError, 'omits or changes'):
                    admission.maximum_witness(task, incorrect, receipt)
            with patch.object(admission, 'MAXIMUM_SOURCE_WITNESS_SHA', '0' * 64):
                with self.assertRaisesRegex(ValueError, 'bytes changed'):
                    admission.maximum_witness(task, records, receipt)


if __name__ == '__main__':
    unittest.main()
