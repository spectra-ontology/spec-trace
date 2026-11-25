#!/usr/bin/env python3
"""test_tr_bibliographic_references.py — source-referent regression tests.

Spec: Phase-5 cited-work identity. Ontology: referencesTR endpoint roles.
Cycle: literal bibliography entries → direct TR citations.
배경: contribution titles and standards identifiers have distinct referents.
사용: python -m unittest discover -s scripts/tsg/RAN/formal/common -p test_tr_bibliographic_references.py.
LLM 호출: none; fixtures only.
"""
import hashlib
import json
import tempfile
import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
sys.path.insert(0, str(ROOT / "scripts/common"))
from tr_bibliographic_references import direct_tr_references


class BibliographicReferents(unittest.TestCase):
    def publication_fixture(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        source = root / 'source.txt'; source.write_text('synthetic native source')
        producer = root / 'scripts/tsg/RAN/formal/RAN4/phase-5/tr-parser/01_parse_tr_docs.py'
        producer.parent.mkdir(parents=True)
        producer.write_text('def extract_heading1_sections(document):\n    return {"References": []}\n')
        review = root / 'review.json'
        review.write_text(json.dumps({'canonicalPairs': {'RAN4': [['38.900', '38.901']]},
            'sourceDocuments': [{'wg': 'RAN4', 'trNumber': '38.900', 'source': {
                'path': 'source.txt', 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}}]}))
        rows = [{'trNumber': '38.900', 'referencesTR': ['38.901'], 'title': 'retained'}]
        parsed = root / 'ontology/output/tsg/RAN/formal/parsed_tr/RAN4/tr_documents.json'
        canonical = root / 'ontology/output/tsg/RAN/formal/instances/phase-5/RAN4/tr_ontology.jsonld'
        for path, value in ((parsed, rows), (canonical, {'@graph': rows})):
            path.parent.mkdir(parents=True); path.write_text(json.dumps(value))
        return root, review, parsed, canonical

    def reconcile_fixture(self, root, review, output):
        import tr_bibliographic_references as bibliography
        code = root / 'reviewed-code.py'
        code.write_bytes(Path(bibliography.__file__).read_bytes())
        driver = MagicMock()
        driver.__enter__.return_value.session.return_value.__enter__.return_value.run.return_value = []
        with patch.object(bibliography, '__file__', str(code)), \
                patch('neo4j.GraphDatabase.driver', return_value=driver), \
                patch('common.axis.bolt_uri', return_value='synthetic'), \
                patch('common.credentials.neo4j_auth', return_value=('fake', 'fake')), \
                patch('docx_text.open_document', return_value=object()):
            return bibliography.reconcile_reviewed_citations(root, review, output, apply=True)

    def test_publication_failure_restores_current_attempt_and_retries(self):
        from common import atomic_io
        for operation in ('fsync', 'post_replace'):
            for error in (OSError, KeyboardInterrupt):
                with self.subTest(operation=operation, error=error):
                    root, review, parsed, canonical = self.publication_fixture()
                    before = {p: p.read_bytes() for p in (parsed, canonical)}
                    original_write = atomic_io.write_text_atomic
                    def write(path, text):
                        if Path(path) == parsed:
                            if operation == 'fsync':
                                with patch.object(atomic_io.os, 'fsync', side_effect=error('synthetic')):
                                    return original_write(path, text)
                            replace = atomic_io.os.replace
                            def replaced(source, destination):
                                replace(source, destination)
                                raise error('after replacement')
                            with patch.object(atomic_io.os, 'replace', side_effect=replaced):
                                return original_write(path, text)
                        return original_write(path, text)
                    # Fail once so rollback can use the real writer.
                    fired = False
                    def fail_once(path, text):
                        nonlocal fired
                        if Path(path) == parsed and not fired:
                            fired = True
                            return write(path, text)
                        return original_write(path, text)
                    with patch.object(atomic_io, 'write_text_atomic', side_effect=fail_once):
                        with self.assertRaises(error):
                            self.reconcile_fixture(root, review, root / 'failed')
                    self.assertEqual({p: p.read_bytes() for p in before}, before)
                    self.assertFalse(list(root.rglob('*.tmp')))
                    self.assertEqual(self.reconcile_fixture(root, review, root / 'retry')['status'], 'complete')
                    self.assertEqual(json.loads(parsed.read_text())[0]['referencesTR'], [])

    def test_second_projection_interruption_restores_both_preimages(self):
        from common import atomic_io
        root, review, parsed, canonical = self.publication_fixture()
        before = {p: p.read_bytes() for p in (parsed, canonical)}
        write = atomic_io.write_text_atomic
        fired = False
        def interrupt(path, text):
            nonlocal fired
            if Path(path) == canonical and not fired:
                fired = True
                replace = atomic_io.os.replace
                def replaced(source, destination):
                    replace(source, destination)
                    raise KeyboardInterrupt('after second replacement')
                with patch.object(atomic_io.os, 'replace', side_effect=replaced):
                    return write(path, text)
            return write(path, text)
        with patch.object(atomic_io, 'write_text_atomic', side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.reconcile_fixture(root, review, root / 'failed')
        self.assertEqual({p: p.read_bytes() for p in before}, before)
        self.assertFalse(list(root.rglob('*.tmp')))
        self.assertEqual(self.reconcile_fixture(root, review, root / 'retry')['status'], 'complete')

    def test_publication_rollback_preserves_concurrent_generation(self):
        from common import atomic_io
        root, review, parsed, canonical = self.publication_fixture()
        canonical_before = canonical.read_bytes()
        original_write = atomic_io.write_text_atomic
        def concurrent(path, text):
            original_write(path, text)
            if Path(path) == parsed:
                parsed.write_text('concurrent generation')
                raise KeyboardInterrupt('after concurrent replacement')
        with patch.object(atomic_io, 'write_text_atomic', side_effect=concurrent):
            with self.assertRaises(KeyboardInterrupt):
                self.reconcile_fixture(root, review, root / 'receipt')
        self.assertEqual(parsed.read_text(), 'concurrent generation')
        self.assertEqual(canonical.read_bytes(), canonical_before)

    def test_review_replaced_after_read_cannot_bind_old_claims_to_new_sha(self):
        root, review, parsed, canonical = self.publication_fixture()
        before = {path: path.read_bytes() for path in (parsed, canonical)}
        original_read_bytes, original_read_text = Path.read_bytes, Path.read_text
        replaced = False
        def replace_after_read(method):
            def read(path, *args, **kwargs):
                nonlocal replaced
                value = method(path, *args, **kwargs)
                if path == review and not replaced:
                    replaced = True
                    changed = json.loads(value)
                    changed['reviewGeneration'] = 'concurrent replacement'
                    review.write_text(json.dumps(changed))
                return value
            return read
        output = root / 'receipt'
        with patch.object(Path, 'read_bytes', replace_after_read(original_read_bytes)), \
                patch.object(Path, 'read_text', replace_after_read(original_read_text)):
            with self.assertRaisesRegex(ValueError, 'Citation input changed before write'):
                self.reconcile_fixture(root, review, output)
        self.assertTrue(replaced)
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        self.assertFalse((output / 'plan.json').exists())
        self.assertFalse((output / 'result.json').exists())

    def test_contribution_title_is_not_a_report_reference(self):
        entries = ['[17]\tR4-2503479 TP to TR 38.755 on Clause 5, RAN4#114bis, CATT',
                   '[8]\tR4-2110978, “TP for TR 38.860: Filter option B1”, Qualcomm',
                   '[10]\tR4-2220016, "TP for TR 38.892: n105 compatibility", T-Mobile']
        self.assertEqual(direct_tr_references({'2\tReferences': entries}, {'38.755', '38.860', '38.892'}), [])

    def test_actual_direct_entry_and_part_number(self):
        sections = {'2 References': ['[10]\tTR 38.817-01: “General aspects for UE RF for NR”.',
                                    '[4]\t3GPP\u00a0TR\u00a038.869: "Study …".']}
        self.assertEqual(direct_tr_references(sections, {'38.817-01', '38.869'}), ['38.817-01', '38.869'])

    def test_corpus_boundary_and_multiple_entries(self):
        sections = {'References': ['[1] 3GPP TS 38.211: … [2] TR 38.900: … [3] TR 38.901: …'],
                    '3 Findings': ['TR 38.802 is discussed.']}
        self.assertEqual(direct_tr_references(sections, {'38.900', '38.802'}), ['38.900'])

    def test_citation_can_legitimately_name_own_report(self):
        self.assertEqual(direct_tr_references({'References': ['[1] TR 38.755: actual cited report']}, {'38.755'}), ['38.755'])

    def test_complete_identifier_and_sentence_punctuation(self):
        for token, expected in [('38.900X', []), ('38.9000', []),
                                ('38.900-1', []), ('38.900.1', []),
                                ('38.900.', ['38.900']), ('38.900:', ['38.900']),
                                ('38.900)', ['38.900'])]:
            with self.subTest(token=token):
                self.assertEqual(direct_tr_references(
                    {'References': ['TR ' + token]}, {'38.900'}), expected)


if __name__ == '__main__':
    unittest.main()
