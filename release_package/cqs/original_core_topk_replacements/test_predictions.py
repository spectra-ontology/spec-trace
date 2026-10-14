"""Contract identity gates prevent transferring old or mismatched predictions."""
from pathlib import Path
import json
import tempfile
import unittest
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
import score_predictions


class PredictionIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.task = {'id': 'fixture', 'repair_sha256': 'exact-repair', 'validation_status': 'validated',
                     'required_fields': [{'name': 'count', 'type': 'integer'}],
                     'collection': {'kind': 'set'}, 'cardinality_policy': {'mode': 'all'}}
        self.gold = {'id': 'fixture', 'repair_sha256': 'exact-repair', 'records': [{'count': 135}], 'order_groups': None}
        self.write('tasks', [self.task]); self.write('gold', [self.gold])

    def write(self, name, rows):
        path = self.base / name
        path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
        return path

    def run_predictions(self, rows):
        predictions = self.write('predictions', rows)
        return score_predictions.run(self.base / 'tasks', self.base / 'gold', predictions)

    def prediction(self, **changes):
        return dict({'id': 'fixture', 'repair_sha256': 'exact-repair', 'records': [{'count': 135}]}, **changes)

    def test_correct_count_passes_but_wrong_count_does_not(self):
        self.assertTrue(self.run_predictions([self.prediction()])['outcomes'][0]['exact'])
        self.assertFalse(self.run_predictions([self.prediction(records=[{'count': 25}])])['outcomes'][0]['exact'])

    def test_old_definition_hash_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'different or unvalidated contract'):
            self.run_predictions([self.prediction(repair_sha256='old-definition')])

    def test_duplicate_prediction_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.run_predictions([self.prediction(), self.prediction()])

    def test_unadmitted_prediction_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'must belong'):
            self.run_predictions([self.prediction(id='unadmitted')])


if __name__ == '__main__':
    unittest.main()
