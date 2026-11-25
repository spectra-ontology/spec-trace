"""Source slide repair validates every changed body's returned vector."""
import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import reconcile_pptx_search_text as repair


class RepairVectors(unittest.TestCase):
    def setUp(self):
        self.changes = [{'pointId': str(i), 'newPayload': {'content': f'synthetic {i}'}} for i in (1, 2)]
        self.before = {str(i): {'vector': [0.0, 1.0]} for i in (1, 2)}
        self.encoder = SimpleNamespace(dim=2)

    def test_short_or_long_embedding_batch_fails_before_any_prepared_vector_changes(self):
        for count in (0, 1, 3):
            desired = copy.deepcopy(self.before)
            with self.subTest(count=count), patch.object(repair, 'embed_local', return_value=[[1.0, 0.0]] * count):
                with self.assertRaisesRegex(ValueError, 'cardinality mismatch'):
                    repair.prepare_vectors(self.encoder, self.changes, desired)
            self.assertEqual(desired, self.before)

    def test_matching_vectors_are_assigned_to_their_source_points(self):
        desired = copy.deepcopy(self.before)
        vectors = [[1.0, 0.0], [0.0, 1.0]]
        with patch.object(repair, 'embed_local', return_value=vectors) as embed:
            repair.prepare_vectors(self.encoder, self.changes, desired)
        embed.assert_called_once_with(self.encoder, ['synthetic 1', 'synthetic 2'], batch_size=1)
        self.assertEqual([desired[str(i)]['vector'] for i in (1, 2)], vectors)

    def test_wrong_dimension_nonfinite_or_nonunit_vector_is_rejected(self):
        for vector in ([1.0], [float('nan'), 0.0], [float('inf'), 0.0], [2.0, 0.0]):
            with self.subTest(vector=vector), patch.object(repair, 'embed_local', return_value=[vector, [1.0, 0.0]]):
                with self.assertRaisesRegex(ValueError, 'invalid new embedding'):
                    repair.prepare_vectors(self.encoder, self.changes, copy.deepcopy(self.before))

    def test_atomic_bytes_failure_cleans_owned_staging_and_allows_retry(self):
        for stage in ('fsync', 'replace'):
            for error in (OSError, KeyboardInterrupt):
                with self.subTest(stage=stage, error=error), tempfile.TemporaryDirectory() as folder:
                    path = Path(folder) / 'receipt.json'
                    path.write_bytes(b'previous')
                    path.chmod(0o640)
                    with patch.object(repair.os, stage, side_effect=error('synthetic')):
                        with self.assertRaises(error):
                            repair.atomic_bytes(path, b'next')
                    self.assertEqual(path.read_bytes(), b'previous')
                    self.assertEqual(list(Path(folder).iterdir()), [path])
                    repair.atomic_bytes(path, b'next')
                    self.assertEqual(path.read_bytes(), b'next')
                    self.assertEqual(path.stat().st_mode & 0o777, 0o640)

    def test_atomic_bytes_keeps_foreign_fixed_temporary_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'receipt.json'
            foreign = path.with_name(path.name + '.tmp')
            foreign.write_bytes(b'foreign')
            repair.atomic_bytes(path, b'new')
            self.assertEqual(path.read_bytes(), b'new')
            self.assertEqual(foreign.read_bytes(), b'foreign')

    def test_snapshot_stops_repeated_empty_cursor(self):
        client = Mock()
        client.scroll.side_effect = [([], 'same'), ([], 'same'),
                                     AssertionError('unbounded scroll')]
        with self.assertRaisesRegex(ValueError, 'Repeated'):
            repair.snapshot(client, 'synthetic', ['R5-000001'])
        self.assertEqual(client.scroll.call_count, 2)


if __name__ == '__main__':
    unittest.main()
