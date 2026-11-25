#!/usr/bin/env python3
"""test_tr_source_review.py — preserve a source review through failed batch updates.

Spec: docs/tsg/build/standards/tr_source_evidence_contract.md.
Ontology: adjudicated evidence remains bound to its retained primary sources.
Cycle: full assessment preimages → guarded batch → readback or owned rollback.
배경: a later input failure must preserve earlier WG assessments and external edits.
사용: python3 -B -m unittest discover -s scripts/tsg/RAN/formal/common -p test_tr_source_review.py
LLM 호출: 없음. All mutations use isolated temporary fixtures.
"""
from __future__ import annotations

import base64
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

import review_tr_impact_sources as review


class AssessmentBatchTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.a = self.root / 'RAN3.json'
        self.b = self.root / 'RAN5.csv'
        self.source = self.root / 'primary.txt'
        self.journal = self.root / 'recovery.json'
        self.before = {self.a:b'{"verified":"retained"}\n', self.b:b'claim,evidence\nold,source\n'}
        self.after = {self.a:b'{"verified":"retained","observation":"new"}\n',
                      self.b:b'claim,evidence\nnew,source\n'}
        for path, raw in self.before.items():
            path.write_bytes(raw)
        self.source.write_text('Actual retained primary text.\n')
        self.fingerprints = {path:hashlib.sha256(path.read_bytes()).hexdigest()
                             for path in (*self.before, self.source)}
        self.replacements = {p:(self.before[p], self.after[p]) for p in self.before}

    def apply(self):
        return review._apply_assessment_updates(self.replacements, self.fingerprints, self.journal)

    def assert_originals(self):
        for path, expected in self.before.items():
            self.assertEqual(path.read_bytes(), expected)

    def test_success_keeps_complete_recovery_bytes_for_every_wg(self):
        report = self.apply()
        self.assertEqual(report['state'], 'committed')
        self.assertEqual(json.loads(self.journal.read_text()), report)
        for entry in report['files']:
            path = Path(entry['path'])
            self.assertEqual(path.read_bytes(), self.after[path])
            for key, expected in (('beforeGzipBase64', self.before[path]),
                                  ('afterGzipBase64', self.after[path])):
                self.assertEqual(gzip.decompress(base64.b64decode(entry[key])), expected)
            self.assertTrue(entry['written'])

    def test_stale_later_wg_stops_before_any_earlier_write(self):
        self.b.write_text('Concurrent later-WG assessment.\n')
        with self.assertRaisesRegex(ValueError, 'source changed'):
            self.apply()
        self.assertEqual(self.a.read_bytes(), self.before[self.a])
        self.assertEqual(self.b.read_text(), 'Concurrent later-WG assessment.\n')
        self.assertFalse(self.journal.exists())

    def test_exception_after_second_replacement_restores_both_exact_preimages(self):
        real_write = review.write_text_atomic
        failed = False
        def interrupted_write(path, text):
            nonlocal failed
            real_write(path, text)
            if path == self.b and not failed:
                failed = True
                raise OSError('Failure after replacement, before confirmation')
        with patch.object(review, 'write_text_atomic', interrupted_write):
            with self.assertRaisesRegex(OSError, 'before confirmation'):
                self.apply()
        self.assert_originals()
        report = json.loads(self.journal.read_text())
        self.assertEqual(report['state'], 'rolled_back')
        self.assertTrue(all(entry['restored'] for entry in report['files']))

    def test_changed_primary_source_rolls_back_owned_outputs_and_preserves_source(self):
        real_write = review.write_text_atomic
        def changed_source(path, text):
            real_write(path, text)
            if path == self.a and text.encode() == self.after[self.a]:
                self.source.write_text('External primary-source revision.\n')
        with patch.object(review, 'write_text_atomic', changed_source):
            with self.assertRaisesRegex(ValueError, 'source changed'):
                self.apply()
        self.assert_originals()
        self.assertEqual(self.source.read_text(), 'External primary-source revision.\n')
        self.assertEqual(json.loads(self.journal.read_text())['state'], 'rolled_back')

    def test_external_output_change_is_preserved_during_recovery(self):
        real_write = review.write_text_atomic
        def external_edit(path, text):
            real_write(path, text)
            if path == self.a and text.encode() == self.after[self.a]:
                self.a.write_text('External assessment edit.\n')
        with patch.object(review, 'write_text_atomic', external_edit):
            with self.assertRaisesRegex(ValueError, 'postimage mismatch'):
                self.apply()
        self.assertEqual(self.a.read_text(), 'External assessment edit.\n')
        self.assertEqual(self.b.read_bytes(), self.before[self.b])
        report = json.loads(self.journal.read_text())
        self.assertEqual(report['state'], 'external_changes_preserved')
        self.assertEqual(report['externalConflicts'], [str(self.a)])

    def test_existing_recovery_journal_is_never_replaced(self):
        self.journal.write_text('Earlier full recovery receipt.\n')
        with self.assertRaisesRegex(ValueError, 'new assessment journal'):
            self.apply()
        self.assert_originals()
        self.assertEqual(self.journal.read_text(), 'Earlier full recovery receipt.\n')

    def test_journal_cannot_replace_a_canonical_input(self):
        with self.assertRaisesRegex(ValueError, 'separate from assessment inputs'):
            review._apply_assessment_updates(self.replacements, self.fingerprints, self.a)
        self.assert_originals()

    def test_update_requires_a_recovery_destination_before_source_processing(self):
        with patch.object(review, '_assessment_source_fingerprints') as collect:
            with self.assertRaisesRegex(ValueError, 'durable journal'):
                review.run(True)
            collect.assert_not_called()

    def test_source_identity_client_closes_on_success_error_and_interrupt(self):
        import reconcile_tr_source_identity as identity
        config = self.root / 'identity.json'
        config.write_text('{"resolutions": []}')
        for error in (None, ValueError, KeyboardInterrupt):
            client = MagicMock()
            with self.subTest(error=error), patch.object(identity, 'ROOT', self.root), \
                    patch.object(identity, 'CONFIG', 'identity.json'), \
                    patch.object(identity, 'QdrantClient', return_value=client), \
                    patch.object(identity, 'durable_json', side_effect=error('synthetic') if error else None), \
                    patch.object(sys, 'argv', ['identity', '--out', str(self.root / 'out.json')]):
                if error:
                    with self.assertRaises(error):
                        identity.main()
                else:
                    identity.main()
            client.close.assert_called_once()

    def test_source_review_counts_only_the_complete_target_identifier(self):
        directory = self.root / 'ontology/input/tsg/RAN/formal/TR/RAN4'
        (directory / '38.999').mkdir(parents=True)
        source = directory / '38.999/source.docx'
        source.write_bytes(b'synthetic parser input')
        row = dict(trNumber='38.999', impactType='ExtendSection', impactsSpec='38.533',
                   impactsSection='', impactDescription='Pending synthetic claim.')
        stream = io.StringIO(); writer = csv.DictWriter(stream, fieldnames=row)
        writer.writeheader(); writer.writerow(row)
        raw = stream.getvalue()
        manifest = directory / 'tr_impact_evidence.json'
        manifest.write_text(json.dumps(dict(originalCsv=dict(contentUtf8=raw),
            claims=[dict(claim=review.claim_of(row), status='pending', originalRow=row)])))
        mapping = directory / 'tr_impact_mapping.csv'; mapping.write_text(raw)
        pins = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (source, manifest, mapping)}
        for token, expected in [('38.533X', 0), ('38.533.2', 0), ('38.533-1', 0),
                                ('138.5330', 0), ('38.533.', 1), ('[38.533]', 1)]:
            paragraphs = ['3GPP TR 38.999', '1 Scope',
                          'A sufficiently long synthetic study scope paragraph.',
                          'This study discusses TS ' + token]
            with self.subTest(token=token), patch.object(review, 'ROOT', self.root), \
                    patch.object(review, 'WGS', ('RAN4',)), \
                    patch.object(review, '_assessment_source_fingerprints', return_value=pins), \
                    patch.object(review, '_source_snapshot', return_value=(paragraphs, pins[source])), \
                    patch.object(review, 'resolution_for', return_value=None), \
                    patch.object(review.review_artifacts, 'current_review_input',
                                 side_effect=lambda root, name: root / name):
                result = review.run()['assertions'][0]
            self.assertEqual(result['sourceReview']['bodyTargetMentionCount'], expected)
            self.assertEqual(len(result['supportedStudyAssertions']), expected)

    def test_discovery_numbers_and_cover_identity_require_complete_tokens(self):
        pattern = review._number_pattern(['38.999'])
        for token, expected in [('38.999X', False), ('38.999.2', False), ('38.999-2', False),
                                ('138.999', False), ('38.999.', True), ('[38.999]', True),
                                ('TS38.999', True), ('TR38.999', True), ('XTS38.999', False),
                                ('A38.999', False)]:
            with self.subTest(token=token):
                self.assertEqual(bool(re.search(pattern, 'Study ' + token)), expected)
        self.assertIsNone(re.search(review._number_pattern([]), 'Any paragraph.'))
        for token, expected in [('38.999X', None), ('38.999.2', None),
                                ('38.999.', '38.999'), ('38.999-2', '38.999-2')]:
            self.assertEqual(review._declared_tr_number('3GPP TR ' + token), expected)
        with patch.object(review, '_source_snapshot', return_value=(
                ['Study 38.999X and 38.999.2; actual reference 38.999.'], 'synthetic-hash')):
            discovered = review._discover_cr_source(('synthetic.docx', pattern))
        self.assertEqual([hit['trNumber'] for hit in discovered['mentions']], ['38.999'])

    def test_source_identity_config_generation_is_fenced_before_mutation(self):
        import reconcile_tr_source_identity as identity
        for case in ('stable', 'after_resolution', 'before_commit',
                     'after_neo4j_commit', 'before_qdrant_write'):
            with self.subTest(case=case):
                config = self.root / 'identity.json'
                initial = {'resolutions': [dict(wg='RAN4', trNumber='38.999', sourcePath='source.txt')]}
                config.write_text(json.dumps(initial))
                digest = hashlib.sha256(config.read_bytes()).hexdigest()
                def change(): config.write_text(json.dumps(dict(initial, concurrent=True)))
                resolved = dict(wg='RAN4', trNumber='38.999', canonicalTitle='Reviewed title',
                                assessmentMethod='synthetic', sourceSha256='1' * 64)
                def resolve(*args):
                    if case == 'after_resolution': change()
                    return resolved
                def point(payload):
                    item = SimpleNamespace(id=7, payload=payload, vector=[0.2, 0.8])
                    item.model_dump = lambda **kwargs: dict(id=7, payload=payload, vector=item.vector)
                    return item
                before = point({'trNumber': '38.999', 'preserve': True})
                client = MagicMock(); client.scroll.return_value = ([before], None)
                current_payload = dict(before.payload)
                def retrieve(*args, **kwargs):
                    if case == 'before_qdrant_write': change()
                    return [point(dict(current_payload))]
                client.retrieve.side_effect = retrieve
                client.set_payload.side_effect = lambda *args, **kwargs: current_payload.update(kwargs['payload'])
                driver = MagicMock(); driver.__enter__.return_value = driver
                session = driver.session.return_value.__enter__.return_value
                tx = session.begin_transaction.return_value.__enter__.return_value
                if case == 'before_commit': tx.run.side_effect = lambda *a, **k: (change() or MagicMock())
                saved = []
                def save(path, value):
                    saved.append(json.loads(json.dumps(value)))
                    if case == 'after_neo4j_commit' and value['resolutions'][-1]['neo4jCommitted']:
                        change()
                with patch.object(identity, 'ROOT', self.root), patch.object(identity, 'CONFIG', 'identity.json'), \
                        patch.object(identity, 'resolution_for', side_effect=resolve), \
                        patch.object(identity, 'QdrantClient', return_value=client), \
                        patch.object(identity.GraphDatabase, 'driver', return_value=driver), \
                        patch.object(identity, 'snapshot', return_value=[{'stable': True}]), \
                        patch.object(identity, 'durable_json', side_effect=save), \
                        patch.object(identity.axis, 'bolt_uri', return_value='synthetic'), \
                        patch.object(identity.credentials, 'neo4j_auth', return_value=('fake', 'fake')), \
                        patch.object(sys, 'argv', ['identity', '--out', str(self.root / 'result.json'), '--apply']):
                    if case == 'stable':
                        identity.main()
                    else:
                        with self.assertRaisesRegex(ValueError, 'configuration changed'):
                            identity.main()
                client.close.assert_called_once()
                self.assertEqual(client.set_payload.call_count, int(case == 'stable'))
                self.assertEqual(tx.commit.call_count, int(case in ('stable', 'after_neo4j_commit', 'before_qdrant_write')))
                if case == 'after_resolution': tx.run.assert_not_called()
                if case == 'stable':
                    self.assertEqual(tx.run.call_args.kwargs['sha'], digest)
                    self.assertEqual(current_payload['sourceIdentityAssessmentSha256'], digest)
                    self.assertEqual(saved[-1]['sourceIdentityConfigSha256'], digest)

    def test_source_identity_close_failure_preserves_the_primary_exception(self):
        import reconcile_tr_source_identity as identity
        (self.root / 'identity.json').write_text('{"resolutions": []}')
        for primary in (None, ValueError, KeyboardInterrupt):
            client = MagicMock(); client.close.side_effect = RuntimeError('close failed')
            with self.subTest(primary=primary), patch.object(identity, 'ROOT', self.root), \
                    patch.object(identity, 'CONFIG', 'identity.json'), \
                    patch.object(identity, 'QdrantClient', return_value=client), \
                    patch.object(identity, 'durable_json', side_effect=primary('primary failure') if primary else None), \
                    patch.object(sys, 'argv', ['identity', '--out', str(self.root / 'result.json')]):
                with self.assertRaises(primary or RuntimeError) as caught:
                    identity.main()
            if primary:
                self.assertTrue(any('close also failed' in note for note in caught.exception.__notes__))

    def test_source_identity_scroll_repetition_and_cycle_stop_before_neo4j(self):
        import reconcile_tr_source_identity as identity
        (self.root / 'identity.json').write_text(json.dumps({'resolutions': [
            dict(wg='RAN4', trNumber='38.999', sourcePath='source.txt')]}))
        for cursors in ((7, 7), ('page-a', 'page-b', 'page-a')):
            client = MagicMock()
            # A fourth request is forbidden even if a regression removes the guard.
            client.scroll.side_effect = [([], cursor) for cursor in cursors] + [AssertionError('cursor sentinel')]
            with self.subTest(cursors=cursors), patch.object(identity, 'ROOT', self.root), \
                    patch.object(identity, 'CONFIG', 'identity.json'), \
                    patch.object(identity, 'QdrantClient', return_value=client), \
                    patch.object(identity, 'resolution_for', return_value=dict(wg='RAN4', trNumber='38.999')), \
                    patch.object(identity.GraphDatabase, 'driver') as driver, \
                    patch.object(sys, 'argv', ['identity', '--out', str(self.root / 'result.json')]):
                with self.assertRaisesRegex(ValueError, 'cursor repeated or cycled'):
                    identity.main()
                driver.assert_not_called()
            self.assertEqual(client.scroll.call_count, len(cursors))
            client.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
