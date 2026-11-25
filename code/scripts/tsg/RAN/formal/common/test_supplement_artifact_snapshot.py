"""Synthetic streaming CR append uses one recoverable source generation."""

import gzip
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import json_stream
import tdoc_supplement_vectors as supplements


class SupplementArtifactSnapshots(unittest.TestCase):
    @staticmethod
    def document(chunks):
        return {'metadata': {'total_chunks': len(chunks), 'total_cr_files': len(chunks),
                             'strategy_distribution': {'synthetic': len(chunks)},
                             'header_chunks': 0, 'body_chunks': len(chunks)},
                'chunks': chunks, 'syntheticExtension': {'preserved': True}}

    @staticmethod
    def chunk(target):
        return {'tdocNumber': target, 'chunkId': target + '-000', 'text': 'Synthetic ' + target,
                'strategy': 'synthetic', 'chunkType': 'body'}

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.run = self.root / 'run'
        self.run.mkdir()
        self.path = self.root / 'synthetic.json'
        patcher = patch.object(supplements, 'ROOT', self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_append_preserves_extensions_and_binds_recovery_to_original_bytes(self):
        old, added = self.chunk('R5-000001'), self.chunk('R5-000002')
        before = json.dumps(self.document([old])).encode()
        self.path.write_bytes(before)
        receipt = supplements.append_cr_artifact(self.path, [added], self.run)
        after = json.loads(self.path.read_bytes())
        self.assertEqual(after['chunks'], [old, added])
        self.assertEqual(after['syntheticExtension'], {'preserved': True})
        self.assertEqual(after['metadata']['total_chunks'], 2)
        self.assertEqual(after['metadata']['total_cr_files'], 2)
        self.assertEqual(after['metadata']['body_chunks'], 2)
        self.assertEqual(gzip.decompress((self.root / receipt['backup']).read_bytes()), before)
        self.assertEqual(receipt['sha256'], hashlib.sha256(before).hexdigest())

    def test_edit_after_initial_scan_is_preserved_and_blocks_append(self):
        self.path.write_text(json.dumps(self.document([])))
        added = self.chunk('R5-000002')
        external = json.dumps(self.document([added])).encode()
        original_iter = json_stream.iter_array
        def mutate_after_inspection(*args, **kwargs):
            yield from original_iter(*args, **kwargs)
            self.path.write_bytes(external)
        with patch.object(json_stream, 'iter_array', mutate_after_inspection):
            with self.assertRaisesRegex(RuntimeError, 'changed before atomic append'):
                supplements.append_cr_artifact(self.path, [added], self.run)
        self.assertEqual(self.path.read_bytes(), external)
        self.assertFalse(list(self.root.glob('*.tmp')))

    def test_no_additions_leave_no_unnecessary_recovery_files(self):
        chunk = self.chunk('R5-000001')
        before = json.dumps(self.document([chunk])).encode()
        self.path.write_bytes(before)
        self.assertIsNone(supplements.append_cr_artifact(self.path, [chunk], self.run))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.run.iterdir()), [])

    def test_existing_recovery_file_cannot_be_overwritten(self):
        self.path.write_bytes(b'Original synthetic source')
        receipt = supplements.backup_file(self.path, self.run)
        backup = self.root / receipt['backup']
        before = backup.read_bytes()
        self.path.write_bytes(b'Changed synthetic source')
        second = supplements.backup_file(self.path, self.run)
        self.assertNotEqual(second['backup'], receipt['backup'])
        self.assertEqual(backup.read_bytes(), before)
        self.assertEqual(gzip.decompress((self.root / second['backup']).read_bytes()),
                         b'Changed synthetic source')

    def test_streaming_reader_keeps_caller_owned_stream_open(self):
        with io.StringIO('{"chunks":[{"synthetic":true}]}') as stream:
            self.assertEqual(list(json_stream.iter_array(stream, 'chunks')), [{'synthetic': True}])
            self.assertFalse(stream.closed)


if __name__ == '__main__':
    unittest.main()
