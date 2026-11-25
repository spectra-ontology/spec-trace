"""Metadata proposals bind their before image to the bytes actually parsed."""
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import reconcile_tdoc_source_metadata as metadata
import tdoc_source_metadata as source_metadata


class MetadataInputBinding(unittest.TestCase):
    def test_independent_identity_ledgers_merge_fields_and_reject_conflicts(self):
        corrections = [{'target':'R1-123456', 'deltas':[
            {'field':'targetRelease', 'sourceBackedValue':'tdoc:release/Rel_18'}]}]
        for release, valid in ((None, True), ('tdoc:release/Rel_18', True), ('tdoc:release/Rel_19', False)):
            rows = [{'target':'R1-123456', 'deltas':[
                {'field':'tdoc:type', 'sourceBackedValue':'CR'}]}]
            if release:
                rows[0]['deltas'].append({'field':'targetRelease', 'sourceBackedValue':release})
            source_metadata.identity_fields.cache_clear()
            self.addCleanup(source_metadata.identity_fields.cache_clear)
            with self.subTest(release=release), patch.object(source_metadata, 'validated_corrections', return_value=corrections), patch.object(
                    source_metadata, 'validated_classifications', return_value=rows):
                if valid:
                    self.assertEqual(source_metadata.identity_fields(Path('/synthetic'), 'RAN1'),
                                     {'R1-123456':{'release':'Rel-18','document_type':'CR'}})
                else:
                    with self.assertRaisesRegex(ValueError, 'Conflicting'):
                        source_metadata.identity_fields(Path('/synthetic'), 'RAN1')

    def test_full_points_stops_cyclic_empty_cursor(self):
        client = Mock()
        client.scroll.side_effect = [([], 'a'), ([], 'b'), ([], 'a'),
                                     AssertionError('unbounded scroll')]
        with self.assertRaisesRegex(ValueError, 'Repeated'):
            metadata.full_points(client, 'synthetic', ['R1-000001'])
        self.assertEqual(client.scroll.call_count, 3)

    def test_json_pin_survives_an_edit_after_parsing(self):
        with tempfile.TemporaryDirectory(prefix='spectra-metadata-input-') as folder:
            path = Path(folder) / 'synthetic.json'
            before = b'{"synthetic": "first"}'
            path.write_bytes(before)
            original_loads = json.loads
            def edit_after_read(value):
                decoded = original_loads(value)
                path.write_bytes(b'{"synthetic": "later"}')
                return decoded
            with patch.object(metadata.json, 'loads', side_effect=edit_after_read):
                value, source_sha = metadata.read_json_pinned(path)
            self.assertEqual(value, {'synthetic': 'first'})
            self.assertEqual(source_sha, hashlib.sha256(before).hexdigest())
            self.assertNotEqual(source_sha, metadata.sha(path))

    def test_actual_phase4_projection_exports_its_parsed_input_pin(self):
        with tempfile.TemporaryDirectory(prefix='spectra-metadata-phase4-') as folder:
            root = Path(folder)
            path = root / 'ontology/output/tsg/RAN/formal/parsed_cr/RAN1/cr_documents.json'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'documents': [{'tdoc_number': 'R1-000001'}],
                'metadata': {'total_cr_docs_found': 1}}))
            original = path.read_bytes()
            projection = dict(sourceSupplements=[], sourceClassifications=[],
                              sourceNativeBodies=[], identityCorrections={})
            def project(*args, **kwargs):
                path.write_text('{"changed": true}')
                return projection
            fences = {}
            with patch.object(metadata, 'ROOT', root), \
                 patch.object(metadata, 'phase4_parser_path', return_value=root/'unused.py'), \
                 patch.object(metadata, 'load_module', return_value=SimpleNamespace()), \
                 patch.object(metadata, 'phase4_sources', side_effect=project):
                actual_path, before, after, added, _ = metadata.phase4_projection('RAN1', input_fences=fences)
                with self.assertRaisesRegex(ValueError, 'SHA fence changed'):
                    metadata.source_fence({path.relative_to(root).as_posix(): fences[path]})
            self.assertEqual(actual_path, path)
            self.assertEqual(before['documents'], after['documents'])
            self.assertEqual(added, [])
            self.assertEqual(fences[path], hashlib.sha256(original).hexdigest())
            self.assertNotEqual(fences[path], metadata.sha(path))


if __name__ == '__main__':
    unittest.main()
