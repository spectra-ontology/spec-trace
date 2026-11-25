"""Synthetic source-byte binding and evidence-link replacement regressions."""

import hashlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

import tr_impact_evidence as evidence


class EvidenceSnapshots(unittest.TestCase):
    def setUp(self):
        evidence._SOURCE_TEXT_CACHE.clear()
        self.addCleanup(evidence._SOURCE_TEXT_CACHE.clear)

    def test_quote_cannot_be_read_from_a_later_source_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'synthetic.txt'
            before = b'Original synthetic source'
            source.write_bytes(before)
            receipt = {'path': source.name, 'sha256': hashlib.sha256(before).hexdigest(),
                       'quote': 'Replacement synthetic source', 'locator': 'paragraph 1'}
            original_read = Path.read_bytes
            reads = 0
            def replace_after_pinned_read(path):
                nonlocal reads
                raw = original_read(path)
                if path == source:
                    reads += 1
                    # _bound_source verifies by streaming; this is _receipt's snapshot read.
                    if reads == 1:
                        source.write_bytes(b'Replacement synthetic source')
                return raw
            with patch.object(Path, 'read_bytes', replace_after_pinned_read):
                with self.assertRaisesRegex(evidence.ImpactEvidenceError, '인용'):
                    evidence._receipt(root, receipt)
            self.assertNotIn('Replacement synthetic source',
                             evidence._SOURCE_TEXT_CACHE.get((str(source.resolve()), receipt['sha256']), ''))

    def test_docx_parser_accepts_the_pinned_package_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic.docx'
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, 'w') as package:
                package.writestr('word/document.xml',
                    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                    '<w:body><w:p><w:r><w:t>Synthetic paragraph</w:t></w:r></w:p></w:body></w:document>')
            self.assertEqual(evidence.source_text(path, source_bytes=stream.getvalue()), 'Synthetic paragraph')
            self.assertFalse(path.exists())

    def test_pending_manifest_hash_uses_the_bytes_actually_parsed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'ontology/input/tsg/RAN/formal/TR/RAN1/tr_impact_evidence.json'
            path.parent.mkdir(parents=True)
            before = b'{"schema":1,"wg":"RAN1","claims":[]}'
            path.write_bytes(before)
            loads = json.loads
            def edit_after_parse(raw):
                value = loads(raw)
                path.write_bytes(b'{"edited":true}')
                return value
            row = {'trNumber': '38.999', 'impactType': 'NewSection'}
            with patch.object(evidence.json, 'loads', side_effect=edit_after_parse):
                evidence.assess_impacts(root, 'RAN1', [row])
            self.assertEqual(row['evidenceSha256'], hashlib.sha256(before).hexdigest())

    def test_empty_replacement_receipts_clear_stale_evidence_links(self):
        with tempfile.TemporaryDirectory() as directory:
            calls = []
            class Result:
                def single(self):
                    return {'count': 1}
                def consume(self):
                    return None
            class Transaction:
                def run(self, query, **params):
                    calls.append((query, params))
                    return Result()
            session = SimpleNamespace(execute_write=lambda callback: callback(Transaction()))
            row = {'trImpactId': 'synthetic', 'trNumber': '38.999', 'impactType': 'NewSection',
                   'hasEvidence': [{'@id': 'stale synthetic receipt'}]}
            self.assertEqual(evidence.load_assessed_impact_nodes(session, Path(directory), 'RAN1', [row]), 1)
            clear = [(query, params) for query, params in calls if 'HAS_EVIDENCE' in query and 'DELETE r' in query]
            self.assertEqual(len(clear), 1)
            self.assertEqual(clear[0][1]['iid'], 'synthetic')
            self.assertNotIn('hasEvidence', row)

    def test_existing_empty_manifest_is_reported_as_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'ontology/input/tsg/RAN/formal/TR/RAN1/tr_impact_evidence.json'
            path.parent.mkdir(parents=True)
            path.write_bytes(b'')
            with self.assertRaises(json.JSONDecodeError):
                evidence.assess_impacts(root, 'RAN1', [{'impactType': 'NewTS'}])

    def test_discovery_worker_binds_its_quote_to_the_hashed_docx_generation(self):
        import review_tr_impact_sources as review
        def package_bytes(text):
            output = io.BytesIO()
            with zipfile.ZipFile(output, 'w') as package:
                package.writestr('word/document.xml',
                    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                    f'<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>')
            return output.getvalue()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'synthetic.docx'
            before = package_bytes('Original TR 38.999 source')
            path.write_bytes(before)
            read = Path.read_bytes
            def replace_after_read(selected):
                raw = read(selected)
                if selected == path:
                    path.write_bytes(package_bytes('Replacement TR 38.999 source'))
                return raw
            with patch.object(review, 'ROOT', root), patch.object(Path, 'read_bytes', replace_after_read):
                result = review._discover_cr_source((path.name, r'38\.999'))
            self.assertEqual(result['sha256'], hashlib.sha256(before).hexdigest())
            self.assertEqual(result['mentions'][0]['quote'], 'Original TR 38.999 source')
            self.assertNotEqual(result['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_discovery_json_pin_uses_parsed_bytes_despite_replacement(self):
        import review_tr_impact_sources as review
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic.json'
            before = b'{"synthetic":"first"}'
            path.write_bytes(before)
            loads = json.loads
            def edit_after_parse(raw):
                value = loads(raw)
                path.write_bytes(b'{"synthetic":"later"}')
                return value
            with patch.object(review.json, 'loads', side_effect=edit_after_parse):
                value, pin = review._json_snapshot(path)
            self.assertEqual(value, {'synthetic': 'first'})
            self.assertEqual(pin, hashlib.sha256(before).hexdigest())


if __name__ == '__main__':
    unittest.main()
