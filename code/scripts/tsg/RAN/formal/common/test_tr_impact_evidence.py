#!/usr/bin/env python3
"""TRImpact 근거 게이트의 합성 입력 및 쓰기 전 차단 회귀 검사.

Spec: docs/common/process/spectra_operations_rulebook.md §3.1, §4.1.
Ontology: 검증된 반영 인과와 검증 대기 후보를 구분한다.
Cycle: 원래 CSV → 원본 자료의 SHA·인용의 검증 기록 → 생성·적재 사전 검사.
배경: 근거 검증 대기 주장을 검증된 인과관계로 등록하려는 경우에 오류를 내는지 확인한다.
사용: python3 -m unittest discover -s scripts/tsg/RAN/formal/common -p test_tr_impact_evidence.py
LLM 호출: 없음.
"""
import ast
import csv
import hashlib
import json
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from tr_impact_evidence import (ImpactEvidenceError, claim_of, coverage_counts,
                                require_verified_impacts, assess_impacts, evidence_instance, load_assessed_impact_nodes)

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
BASE = ROOT / 'scripts/tsg/RAN/formal'


class EvidenceGate(unittest.TestCase):
    def setUp(self):
        # Source-only regressions read public code/schema and synthetic temporary inputs.
        # Any accidental dependency on the developer's corpus or prior output fails here.
        forbidden = tuple(ROOT / part for part in
                          ('logs', 'data', 'ontology/input', 'ontology/output'))
        self.private_input_reads = []
        for method in ('read_bytes', 'read_text'):
            original = getattr(Path, method)
            def guarded(path, *args, _original=original, **kwargs):
                absolute = path.resolve()
                if any(absolute == base or base in absolute.parents for base in forbidden):
                    self.private_input_reads.append(str(absolute))
                    raise AssertionError('Regression attempted to read a developer corpus or prior result')
                return _original(path, *args, **kwargs)
            guard = patch.object(Path, method, guarded)
            guard.start()
            self.addCleanup(guard.stop)
        self.addCleanup(self.assertEqual, self.private_input_reads, [])

    def mixed_fixture(self, wg):
        quote = ('Synthetic decision: TR 38.903 corrects TS 38.533 and discusses TS 38.534. '
                 'The independent TR 38.906 example leaves its selected TS 38.533 scope unchanged.')
        root, source, base_row, path, base_entry = self.fixture(quote, wg=wg)
        rows = [dict(base_row),
                dict(base_row, impactsSpec='38.532', impactDescription='Synthetic pending target claim.'),
                dict(base_row, trNumber='38.905', impactDescription='Synthetic rejected claim.'),
                dict(base_row, trNumber='38.906', impactType='NoChange',
                     impactDescription='The synthetic selected scope remains unchanged.'),
                dict(base_row, impactsSpec='38.534', impactDescription='Synthetic discovered correction.')]
        statuses = ('verified', 'pending', 'rejected', 'verified', 'verified')
        entries = []
        for index, (row, status) in enumerate(zip(rows, statuses)):
            evidence = dict(base_entry['incorporationEvidence'])
            entry = {'claim': claim_of(row), 'status': status,
                     'sourceReview': {'verdict': status,
                         'reviewExplanation': 'Synthetic source assessed for this exact claim.'},
                     'sourceEvidence': [dict(evidence)]}
            if index < 4:
                entry['originalRow'] = dict(row)
            else:
                entry.update(inputOrigin='source_discovery', discoveredInputRow=dict(row),
                             discoveryEvidence=dict(evidence))
            if status == 'verified':
                scope = 'explicit_no_change' if row['impactType'] == 'NoChange' else 'existing_section_change'
                if scope == 'explicit_no_change':
                    evidence['kind'] = 'explicit_no_change'
                    entry['boundedScope'] = 'Synthetic TS 38.533 decision scope only.'
                entry.update(verifiedImpactDescription=row['impactDescription'],
                             reviewExplanation='Synthetic source explicitly supports this bounded claim.',
                             verifiedImpactScope=scope, incorporationEvidence=evidence,
                             scopeAssessment={'scope': scope, 'explanation': 'Synthetic bounded operation.',
                                              'evidence': [dict(evidence)]})
            else:
                entry['reason'] = 'Synthetic source review retains this claim without causal promotion.'
            if index in (0, 4):
                entry['supportedStudyAssertions'] = [{
                    'targetSpecNumber': row['impactsSpec'], 'predicate': 'discussesSpec',
                    'evidence': dict(evidence), 'description': 'Synthetic noncausal source finding.'}]
            entries.append(entry)
        csv_text = io.StringIO(newline='')
        writer = csv.DictWriter(csv_text, fieldnames=list(base_row))
        writer.writeheader()
        writer.writerows(rows[:4])
        historical = csv_text.getvalue()
        writer.writerow(rows[4])
        current = csv_text.getvalue()
        manifest = {'schema': 1, 'wg': wg, 'claims': entries,
                    'assessmentCoverage': coverage_counts(entries),
                    'originalCsv': {'path': str(path.with_name('tr_impact_mapping.csv').relative_to(root)),
                        'contentUtf8': historical,
                        'sha256': hashlib.sha256(historical.encode()).hexdigest()}}
        path.write_text(json.dumps(manifest))
        path.with_name('tr_impact_mapping.csv').write_text(current)
        return root, source, rows, path, manifest

    def test_original_rows_and_bytes_are_preserved(self):
        causal = verified = original_count = discovered_count = 0
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            root, source, rows, path, manifest = self.mixed_fixture(wg)
            original = manifest['originalCsv']
            self.assertEqual(hashlib.sha256(original['contentUtf8'].encode()).hexdigest(), original['sha256'])
            historical = [e for e in manifest['claims'] if e.get('originalRow')]
            discovered = [e for e in manifest['claims'] if e.get('inputOrigin') == 'source_discovery']
            self.assertEqual([e['originalRow'] for e in historical],
                             list(csv.DictReader(io.StringIO(original['contentUtf8']))))
            self.assertEqual(len(historical) + len(discovered), len(manifest['claims']))
            self.assertTrue(all(e['discoveryEvidence'] and not e.get('originalRow') for e in discovered))
            expected = coverage_counts(manifest['claims'])
            self.assertEqual({k: manifest['assessmentCoverage'][k] for k in expected}, expected)
            original_count += len(historical)
            discovered_count += len(discovered)
            causal += sum(e['claim']['impactType'] in {'NewTS', 'NewSection', 'ExtendSection'}
                          for e in manifest['claims'])
            verified += sum(e['status'] == 'verified' for e in manifest['claims'])
        self.assertEqual((original_count, discovered_count, causal, verified), (20, 5, 20, 15))

    def test_all_verified_rows_match_current_primary_source(self):
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            root, source, rows, path, manifest = self.mixed_fixture(wg)
            verified = [r for r in rows if any(e['status'] == 'verified' and e['claim'] == claim_of(r)
                                             for e in manifest['claims'])]
            require_verified_impacts(root, wg, verified)

    def test_stale_assessment_coverage_blocks_generation(self):
        root, source, rows, path, manifest = self.mixed_fixture('RAN5')
        verified = [r for r in rows if any(e['status'] == 'verified' and e['claim'] == claim_of(r)
                                         for e in manifest['claims'])]
        require_verified_impacts(root, 'RAN5', verified, _manifest=manifest)
        manifest['assessmentCoverage']['sourceDiscoveredClaims'] -= 1
        with self.assertRaisesRegex(ImpactEvidenceError, 'assessmentCoverage'):
            require_verified_impacts(root, 'RAN5', verified, _manifest=manifest)

    def test_every_current_mixed_batch_stops_before_promotion(self):
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            root, source, rows, path, manifest = self.mixed_fixture(wg)
            with self.subTest(wg=wg), self.assertRaisesRegex(ImpactEvidenceError, '출처 검증 대기'):
                require_verified_impacts(root, wg, rows)

    def fixture(self, source_quote='TR 38.903 is incorporated into TS 38.533.', *, wg='RAN5'):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        source = root / 'decision.txt'
        source.write_text(source_quote)
        row = {'trNumber': '38.903', 'impactType': 'ExtendSection', 'impactsSpec': '38.533',
               'impactsSection': '', 'impactDescription': 'Explicit incorporated change.'}
        entry = {'claim': claim_of(row), 'status': 'verified',
                 'reviewExplanation': 'Explicit incorporation decision.',
                 'verifiedImpactDescription': row['impactDescription'],
                 'incorporationEvidence': {'kind': 'incorporation', 'path': 'decision.txt',
                     'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                     'quote': source_quote, 'locator': 'paragraph 1'}}
        entry['verifiedImpactScope'] = 'existing_section_change'
        entry['scopeAssessment'] = {'scope': 'existing_section_change',
            'explanation': 'The synthetic source specifies a correction in an existing clause.',
            'evidence': [entry['incorporationEvidence']]}
        directory = root / f'ontology/input/tsg/RAN/formal/TR/{wg}'
        directory.mkdir(parents=True)
        manifest = directory / 'tr_impact_evidence.json'
        manifest.write_text(json.dumps({'schema': 1, 'wg': wg, 'claims': [entry]}))
        return root, source, row, manifest, entry

    def test_stale_source_and_invented_quote_are_rejected(self):
        root, source, row, manifest, e = self.fixture()
        require_verified_impacts(root, 'RAN5', [row])
        inflated = dict(row, impactDescription='Every future feature is supported.')
        with self.assertRaisesRegex(ImpactEvidenceError, '검증된 범위'):
            require_verified_impacts(root, 'RAN5', [inflated])
        source.write_text('Changed decision.')
        with self.assertRaisesRegex(ImpactEvidenceError, 'SHA'):
            require_verified_impacts(root, 'RAN5', [row])
        e['incorporationEvidence']['sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
        manifest.write_text(json.dumps({'schema': 1, 'wg': 'RAN5', 'claims': [e]}))
        with self.assertRaisesRegex(ImpactEvidenceError, '인용'):
            require_verified_impacts(root, 'RAN5', [row])

    def test_receipt_requires_nonblank_string_quote_and_locator(self):
        from tr_impact_evidence import _receipt
        root, source, row, manifest, entry = self.fixture()
        evidence = entry['incorporationEvidence']
        _receipt(root, evidence)
        for field in ('quote', 'locator'):
            for value in ('', ' \t\n ', None, 1, [], {}):
                with self.subTest(field=field, value=value), self.assertRaises(ImpactEvidenceError):
                    _receipt(root, dict(evidence, **{field: value}))

    def test_study_finding_requires_the_complete_target_number(self):
        from tr_impact_evidence import study_assertion_instances
        root, source, row, manifest, entry = self.fixture()
        for text, valid in (('TS 38.533: reviewed scope.', True),
                            ('(38.533), reviewed scope.', True),
                            ('Reviewed TS 38.533.', True),
                            ('138.5330', False), ('38.533-1', False),
                            ('38.5330', False), ('38.533X', False)):
            source.write_text(text)
            evidence = dict(entry['incorporationEvidence'], quote=text,
                            sha256=hashlib.sha256(source.read_bytes()).hexdigest())
            entry['supportedStudyAssertions'] = [{'targetSpecNumber': '38.533',
                'predicate': 'discussesSpec', 'evidence': evidence, 'description': 'Fixture finding.'}]
            manifest.write_text(json.dumps({'schema': 1, 'wg': 'RAN5', 'claims': [entry]}))
            with self.subTest(text=text):
                if valid:
                    self.assertEqual(len(study_assertion_instances(root, 'RAN5')), 1)
                else:
                    with self.assertRaisesRegex(ImpactEvidenceError, 'exact target'):
                        study_assertion_instances(root, 'RAN5')

    def test_study_document_publication_preserves_old_output_on_failure(self):
        import tr_impact_evidence as impact
        from common import atomic_io
        root, source, row, manifest, entry = self.fixture()
        output = root / 'assertions.jsonld'
        for operation in ('fsync', 'replace'):
            for error in (OSError, KeyboardInterrupt):
                output.write_text('prior-complete')
                before = sorted(p.name for p in root.iterdir())
                with self.subTest(operation=operation, error=error), \
                        patch.object(impact, 'study_assertion_instances', return_value=[]), \
                        patch.object(atomic_io.os, operation, side_effect=error('fixture')):
                    with self.assertRaises(error):
                        impact.write_study_assertions_document(root, 'RAN5', output_path=output)
                self.assertEqual(output.read_text(), 'prior-complete')
                self.assertEqual(sorted(p.name for p in root.iterdir()), before)
        with patch.object(impact, 'study_assertion_instances', return_value=[]):
            self.assertEqual(impact.write_study_assertions_document(root, 'RAN5', output_path=output), output)
        self.assertEqual(json.loads(output.read_text())['@graph'], [])

    def recorded_fixture(self):
        from common import review_artifacts
        root, source, row, manifest, entry = self.fixture()
        recorded = str(review_artifacts.LEGACY_REVIEW_ROOT / 'synthetic-old/sources/decision.txt')
        relocated = str((review_artifacts.review_role(root, 'tr-claims', wg='RAN5')
                         / 'synthetic-current/decision.txt').relative_to(root))
        mapping = patch.object(review_artifacts, 'RECORDED_FILE_RELOCATIONS', {recorded: relocated})
        mapping.start()
        self.addCleanup(mapping.stop)
        original = root / recorded
        original.parent.mkdir(parents=True)
        source.rename(original)
        entry['incorporationEvidence'].update(path=recorded, bytes=original.stat().st_size)
        manifest.write_text(json.dumps({'schema': 1, 'wg': 'RAN5', 'claims': [entry]}))
        return root, original, root / relocated, row, manifest, entry

    def test_relocated_source_preserves_claim_quote_annotation_and_fragment_identity(self):
        from tr_impact_evidence import fragment_of
        root, original, moved, row, manifest, entry = self.recorded_fixture()
        before = manifest.read_bytes()
        fragment = fragment_of(entry['incorporationEvidence'])
        annotated = evidence_instance(root, 'RAN5', dict(row))
        require_verified_impacts(root, 'RAN5', [row])
        moved.parent.mkdir(parents=True)
        original.rename(moved)
        require_verified_impacts(root, 'RAN5', [row])
        self.assertEqual(evidence_instance(root, 'RAN5', dict(row)), annotated)
        self.assertEqual(fragment_of(entry['incorporationEvidence']), fragment)
        self.assertEqual(manifest.read_bytes(), before)
        self.assertEqual(hashlib.sha256(moved.read_bytes()).hexdigest(), entry['incorporationEvidence']['sha256'])

    def test_source_binding_rejects_missing_ambiguous_and_changed_relocated_sources(self):
        root, original, moved, row, manifest, entry = self.recorded_fixture()
        moved.parent.mkdir(parents=True)
        moved.write_bytes(original.read_bytes())
        with self.assertRaisesRegex(ImpactEvidenceError, 'ambiguous') as caught:
            require_verified_impacts(root, 'RAN5', [row])
        self.assertIsInstance(caught.exception.__cause__, ValueError)
        original.unlink()
        moved.write_text('Different retained bytes.')
        with self.assertRaisesRegex(ImpactEvidenceError, 'SHA256 mismatch'):
            require_verified_impacts(root, 'RAN5', [row])
        moved.unlink()
        with self.assertRaisesRegex(ImpactEvidenceError, 'absent') as caught:
            require_verified_impacts(root, 'RAN5', [row])
        self.assertIsInstance(caught.exception.__cause__, FileNotFoundError)

    def test_source_binding_requires_strict_sha_and_optional_explicit_byte_count(self):
        from tr_impact_evidence import _bound_source
        root, source, row, manifest, entry = self.fixture()
        evidence = entry['incorporationEvidence']
        self.assertEqual(_bound_source(root, evidence), source)
        for bad in (None, True, -1, 1.0, '1', source.stat().st_size + 1):
            with self.subTest(bytes=bad), self.assertRaises(ImpactEvidenceError):
                _bound_source(root, dict(evidence, bytes=bad))
        self.assertEqual(_bound_source(root, dict(evidence, bytes=source.stat().st_size)), source)
        for bad in (None, 'invented', evidence['sha256'].upper(), '0' * 64):
            with self.subTest(sha256=bad), self.assertRaises(ImpactEvidenceError):
                _bound_source(root, dict(evidence, sha256=bad))

    def test_source_binding_rejects_leaf_and_ancestor_symlinks(self):
        from tr_impact_evidence import _bound_source
        for ancestor in (False, True):
            root, source, row, manifest, entry = self.fixture()
            if ancestor:
                directory = root / 'alias'
                directory.symlink_to(root, target_is_directory=True)
                recorded = 'alias/decision.txt'
            else:
                (root / 'alias.txt').symlink_to(source)
                recorded = 'alias.txt'
            with self.subTest(ancestor=ancestor), self.assertRaisesRegex(ImpactEvidenceError, 'symlink'):
                _bound_source(root, dict(entry['incorporationEvidence'], path=recorded))

    def test_unknown_recorded_branch_cannot_borrow_a_similar_current_source(self):
        from common.review_artifacts import LEGACY_REVIEW_ROOT, REVIEW_ROOT
        from tr_impact_evidence import _bound_source
        root, source, row, manifest, entry = self.fixture()
        relative = 'unregistered_sources/decision.txt'
        original = root / LEGACY_REVIEW_ROOT / relative
        original.parent.mkdir(parents=True)
        source.rename(original)
        evidence = dict(entry['incorporationEvidence'], path=str(LEGACY_REVIEW_ROOT / relative))
        self.assertEqual(_bound_source(root, evidence), original)
        moved = root / REVIEW_ROOT / relative
        moved.parent.mkdir(parents=True)
        original.rename(moved)
        with self.assertRaisesRegex(ImpactEvidenceError, 'unknown legacy'):
            _bound_source(root, evidence)

    def test_source_discovery_uses_strict_relocated_binding_and_keeps_claim_checks(self):
        root, original, moved, row, manifest, entry = self.recorded_fixture()
        entry.update(inputOrigin='source_discovery', discoveredInputRow=dict(row),
                     discoveryEvidence=dict(entry['incorporationEvidence']))
        def save():
            manifest.write_text(json.dumps({'schema': 1, 'wg': 'RAN5', 'claims': [entry]}))
        save()
        require_verified_impacts(root, 'RAN5', [row])
        moved.parent.mkdir(parents=True)
        original.rename(moved)
        require_verified_impacts(root, 'RAN5', [row])
        for key, bad in (('sha256', 'invented'), ('bytes', None), ('bytes', True),
                         ('bytes', moved.stat().st_size + 1)):
            entry['discoveryEvidence'] = dict(entry['incorporationEvidence'], **{key: bad})
            save()
            with self.subTest(key=key, value=bad), self.assertRaisesRegex(ImpactEvidenceError, 'source-discovery'):
                require_verified_impacts(root, 'RAN5', [row])
        entry['discoveryEvidence'] = dict(entry['incorporationEvidence'])
        entry['discoveredInputRow'] = dict(row, impactsSpec='38.999')
        save()
        with self.assertRaisesRegex(ImpactEvidenceError, 'source-discovery'):
            require_verified_impacts(root, 'RAN5', [row])
        entry.update(discoveredInputRow=dict(row), originalRow=dict(row))
        save()
        with self.assertRaisesRegex(ImpactEvidenceError, 'source-discovery'):
            require_verified_impacts(root, 'RAN5', [row])

    def test_standalone_import_initializes_common_path_before_any_entrypoint_setup(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run([sys.executable, '-B', '-c',
                'import sys; sys.path.insert(0, sys.argv[1]); '
                'import tr_impact_evidence; '
                'assert callable(tr_impact_evidence.resolve_recorded_path)',
                str(BASE / 'common')], cwd=temporary, capture_output=True, text=True,
                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': ''})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_topic_candidates_remain_candidates(self):
        require_verified_impacts(ROOT, 'TSG_RAN', [{'impactType': 'TopicalCandidate'}])
        require_verified_impacts(ROOT, 'RAN1', [{'impactType': 'NoChange'}])

    def test_agreed_change_claim_requires_target_specific_source_disposition(self):
        root, source, row, manifest, entry = self.fixture(
            'R5-236822: The document was agreed. TR 38.903 is incorporated into TS 38.533.')
        row['impactDescription'] = 'Agreed CR R5-236822 specifies a TR-derived correction.'
        entry['verifiedImpactDescription'] = row['impactDescription']
        entry['incorporationEvidence']['changeDocument'] = 'R5-236822'
        def save():
            manifest.write_text(json.dumps({'schema': 1, 'wg': 'RAN5', 'claims': [entry]}))
        save()
        with self.assertRaisesRegex(ImpactEvidenceError, 'target-specific'):
            require_verified_impacts(root, 'RAN5', [row])
        entry['approvalEvidence'] = dict(entry['incorporationEvidence'],
            kind='target_specific_document_agreement', targetTdocNumber='R5-236823',
            dispositionCode='agreed', assessmentMethod='Exact source document final decision.')
        save()
        with self.assertRaisesRegex(ImpactEvidenceError, 'target-specific'):
            require_verified_impacts(root, 'RAN5', [row])
        entry['approvalEvidence']['targetTdocNumber'] = 'R5-236822'
        save()
        require_verified_impacts(root, 'RAN5', [row])

    def test_raw_clause_number_stays_metadata_without_a_release_key(self):
        root, source, row, manifest, entry = self.fixture()
        row['impactsSection'] = 'F'
        entry['claim'] = claim_of(row)
        manifest.write_text(json.dumps({'schema': 1, 'wg': 'RAN5', 'claims': [entry]}))
        instance = evidence_instance(root, 'RAN5', row)
        self.assertEqual(instance['affectedSection'], 'F')
        self.assertNotIn('impactsSection', instance)
        self.assertNotIn('candidateImpactsSection', instance)
        self.assertEqual(instance['evidenceStatus'], 'source_verified')

    def test_mixed_batches_preserve_candidates_and_verified_assertions(self):
        from collections import Counter
        counts = Counter()
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            root, source, rows, path, manifest = self.mixed_fixture(wg)
            originals = [claim_of(r) for r in rows]
            assess_impacts(root, wg, rows)
            self.assertEqual([claim_of(r) for r in rows], originals)
            counts.update(r['evidenceStatus'] for r in rows)
            for row in rows:
                status = row['evidenceStatus']
                inst = evidence_instance(root, wg, dict(row))
                self.assertEqual(inst['evidenceStatus'], status)
                self.assertEqual(inst['impactType'], row['impactType'])
                if status != 'source_verified':
                    self.assertNotIn('impactsSpec', inst)
                    self.assertNotIn('impactsSection', inst)
                else:
                    self.assertTrue(inst['evidenceQuote'])
                    if row['impactType'] == 'NoChange':
                        self.assertEqual(inst['verifiedImpactScope'], 'explicit_no_change')
                        self.assertNotIn('impactsSpec', inst)
                        self.assertNotIn('impactsSection', inst)
                    else:
                        self.assertTrue(inst['impactsSpec'])
        self.assertEqual(sum(counts.values()), 25)
        self.assertEqual(counts['source_verified'], 15)
        self.assertEqual(counts['pending'], 5)
        self.assertEqual(counts['rejected'], 5)

    def test_source_transaction_fence_detects_receipt_or_source_changes(self):
        import reconcile_tr_impact_evidence as reconcile
        root, source, row, manifest, entry = self.fixture()
        (manifest.parent / 'tr_impact_mapping.csv').write_text('trNumber\n38.903\n')
        self.fingerprint_code_fixture(root)
        with patch.object(reconcile, 'ROOT', root):
            expected = reconcile.source_fingerprints('RAN5')
            reconcile.check_source_fingerprints(expected, 'RAN5')
            source.write_text('Different retained source bytes.')
            with self.assertRaisesRegex(ValueError, 'source inputs changed'):
                reconcile.check_source_fingerprints(expected, 'RAN5')

    def fingerprint_code_fixture(self, root):
        import reconcile_tr_impact_evidence as reconcile
        import tr_impact_evidence
        import tr_source_identity
        from common import review_artifacts
        paths = [Path(module.__file__).resolve() for module in
                 (reconcile, tr_impact_evidence, tr_source_identity, review_artifacts)]
        for path in paths:
            target = root / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
        return [str(path.relative_to(ROOT)) for path in paths]

    def test_source_fingerprints_separate_historical_csv_and_current_inputs_after_move(self):
        import reconcile_tr_impact_evidence as reconcile
        root, original, moved, row, manifest, entry = self.recorded_fixture()
        code = self.fingerprint_code_fixture(root)
        current = manifest.parent / 'tr_impact_mapping.csv'
        current.write_text('trNumber\n38.903\n')
        historical = 'trNumber\n38.888\n'
        payload = json.loads(manifest.read_text())
        payload['originalCsv'] = {'path': str(current.relative_to(root)), 'contentUtf8': historical,
                                  'sha256': hashlib.sha256(historical.encode()).hexdigest()}
        manifest.write_text(json.dumps(payload))
        before = manifest.read_bytes()
        with patch.object(reconcile, 'ROOT', root):
            old = reconcile.source_fingerprints('RAN5')
            self.assertEqual(old[str(current.relative_to(root))], hashlib.sha256(current.read_bytes()).hexdigest())
            self.assertNotEqual(old[str(current.relative_to(root))], payload['originalCsv']['sha256'])
            for path in code:
                self.assertEqual(old[path], hashlib.sha256((root / path).read_bytes()).hexdigest())
            moved.parent.mkdir(parents=True)
            original.rename(moved)
            new = reconcile.source_fingerprints('RAN5')
            expected = dict(old)
            expected[str(moved.relative_to(root))] = expected.pop(str(original.relative_to(root)))
            self.assertEqual(new, expected)
            reconcile.check_source_fingerprints(new, 'RAN5')
            with self.assertRaisesRegex(ValueError, 'source inputs changed'):
                reconcile.check_source_fingerprints(old, 'RAN5')
            self.assertEqual(manifest.read_bytes(), before)
            payload['originalCsv']['contentUtf8'] = 'A changed historical CSV.'
            manifest.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, 'Historical original CSV'):
                reconcile.source_fingerprints('RAN5')

    def test_source_fingerprints_do_not_skip_missing_or_changed_claim_bindings(self):
        import reconcile_tr_impact_evidence as reconcile
        for failure in ('missing', 'sha', 'bytes', 'code'):
            root, source, row, manifest, entry = self.fixture()
            code = self.fingerprint_code_fixture(root)
            (manifest.parent / 'tr_impact_mapping.csv').write_text('trNumber\n38.903\n')
            with patch.object(reconcile, 'ROOT', root):
                expected = reconcile.source_fingerprints('RAN5')
                if failure == 'missing':
                    source.unlink()
                elif failure == 'code':
                    (root / code[-1]).write_text('Changed address resolver implementation.')
                else:
                    entry['incorporationEvidence'][{'sha': 'sha256', 'bytes': 'bytes'}[failure]] = (
                        '0' * 64 if failure == 'sha' else None)
                    manifest.write_text(json.dumps({'schema': 1, 'wg': 'RAN5', 'claims': [entry]}))
                with self.subTest(failure=failure), self.assertRaisesRegex(ValueError, 'source inputs changed'):
                    reconcile.check_source_fingerprints(expected, 'RAN5')

    def identity_proof_fixture(self):
        import tr_source_identity as identity
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        source = root / '38716-04-01-g00.docx'
        with zipfile.ZipFile(source, 'w') as package:
            package.writestr('word/document.xml',
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body><w:p><w:r><w:t>Retained source identity passage.</w:t></w:r></w:p></w:body></w:document>')
        raw = source.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        entry = {'wg': 'RAN4', 'trNumber': '38.716-04-01', 'sourcePath': source.name,
                 'sourceSha256': sha, 'sourceCoverNumber': '36.716-04-01',
                 'bodyIdentityQuotes': ['Retained source identity passage.']}
        proof = {'localPath': source.name, 'localSha256': sha, 'officialSources': [
            {'url': 'https://www.3gpp.org/ftp/Specs/archive/38_series/38.716-04-01/38716-04-01-g00.zip',
             'status': 200, 'archiveSha256': '1' * 64,
             'members': [{'name': source.name, 'bytes': len(raw), 'sha256': sha, 'matchesLocal': True}]},
            {'url': 'https://www.3gpp.org/ftp/Specs/archive/36_series/36.716-04-01/36716-04-01-g00.zip',
             'status': 200, 'archiveSha256': '2' * 64,
             'members': [{'name': '36716-04-01-g00.docx', 'bytes': 123, 'sha256': '3' * 64,
                          'matchesLocal': False}]}]}
        entry['officialArchiveEvidence'] = proof
        entry['officialArchiveEvidenceSha256'] = identity.evidence_sha256(proof)
        config = root / identity.CONFIG
        config.parent.mkdir(parents=True)
        config.write_text(json.dumps({'schema': 1, 'resolutions': [entry]}))
        return root, source, config, entry, proof

    def test_authored_identity_proof_works_in_fresh_root_without_logs(self):
        from tr_source_identity import resolution_for
        root, source, config, entry, proof = self.identity_proof_fixture()
        before = (source.read_bytes(), config.read_bytes())
        self.assertFalse((root / 'logs').exists())
        self.assertEqual(resolution_for(root, 'RAN4', '38.716-04-01', source), entry)
        self.assertIsNone(resolution_for(root, 'RAN4', '38.803', source))
        self.assertEqual((source.read_bytes(), config.read_bytes()), before)
        self.assertFalse((root / 'logs').exists())

    def test_authored_identity_rejects_changed_source_and_missing_body_quotes(self):
        from tr_source_identity import resolution_for
        for failure in ('source', 'quote', 'empty_quotes'):
            root, source, config, entry, proof = self.identity_proof_fixture()
            if failure == 'source':
                source.write_bytes(source.read_bytes() + b'Changed source bytes.')
            else:
                entry['bodyIdentityQuotes'] = ['Absent body passage.'] if failure == 'quote' else []
                config.write_text(json.dumps({'schema': 1, 'resolutions': [entry]}))
            with self.subTest(failure=failure), self.assertRaises(ValueError):
                resolution_for(root, 'RAN4', '38.716-04-01', source)

    def test_authored_identity_rejects_proof_drift_and_ambiguous_resolution(self):
        from tr_source_identity import resolution_for
        for failure in ('missing', 'proof_drift', 'duplicate'):
            root, source, config, entry, proof = self.identity_proof_fixture()
            entries = [entry]
            if failure == 'missing':
                del entry['officialArchiveEvidence']
            elif failure == 'proof_drift':
                proof['officialSources'][0]['archiveSha256'] = '4' * 64
            else:
                entries.append(dict(entry))
            config.write_text(json.dumps({'schema': 1, 'resolutions': entries}))
            with self.subTest(failure=failure), self.assertRaises(ValueError):
                resolution_for(root, 'RAN4', '38.716-04-01', source)

    def test_authored_identity_rejects_invalid_rehashed_archive_comparisons(self):
        from tr_source_identity import resolution_for, evidence_sha256
        for failure in ('url', 'number', 'member', 'bytes', 'local_sha', 'local_path',
                        'matches_bool', 'status_bool', 'cover_matches', 'ambiguous_archive', 'ambiguous_member'):
            root, source, config, entry, proof = self.identity_proof_fixture()
            observed = proof['officialSources'][0]
            member = observed['members'][0]
            if failure == 'url':
                observed['url'] = observed['url'].replace('www.3gpp.org', 'example.test')
            elif failure == 'number':
                observed['url'] = observed['url'].replace('/38.716-04-01/', '/38.716-04-02/')
            elif failure == 'member':
                member['name'] = 'another.docx'
            elif failure == 'bytes':
                member['bytes'] += 1
            elif failure == 'local_sha':
                proof['localSha256'] = '0' * 64
            elif failure == 'local_path':
                proof['localPath'] = 'another.docx'
            elif failure == 'matches_bool':
                member['matchesLocal'] = 1
            elif failure == 'status_bool':
                observed['status'] = True
            elif failure == 'cover_matches':
                proof['officialSources'][1]['members'][0]['sha256'] = entry['sourceSha256']
            elif failure == 'ambiguous_archive':
                proof['officialSources'][1] = dict(observed)
            else:
                observed['members'].append(dict(member))
            entry['officialArchiveEvidenceSha256'] = evidence_sha256(proof)
            config.write_text(json.dumps({'schema': 1, 'resolutions': [entry]}))
            with self.subTest(failure=failure), self.assertRaises(ValueError):
                resolution_for(root, 'RAN4', '38.716-04-01', source)

    def test_assessment_inputs_bind_authored_identity_and_current_code_without_logs(self):
        import reconcile_tr_impact_evidence as reconcile
        import review_tr_impact_sources as review
        from common import review_artifacts
        root, source, config, entry, proof = self.identity_proof_fixture()
        selected = {source.name: hashlib.sha256(source.read_bytes()).hexdigest()}
        with patch.object(review, 'ROOT', root), patch.object(review, 'WGS', ('RAN4',)), \
                patch.object(reconcile, 'source_fingerprints', return_value=selected):
            before = review._assessment_source_fingerprints()
            self.assertIn(config, before)
            identity = Path(review.__file__).with_name('tr_source_identity.py')
            self.assertEqual(before[identity], hashlib.sha256(identity.read_bytes()).hexdigest())
            resolver = Path(review_artifacts.__file__).resolve()
            self.assertEqual(before[resolver], hashlib.sha256(resolver.read_bytes()).hexdigest())
            self.assertFalse(any(p.name in {'tr_cr_candidate_inventory.json', 'tr_source_assessments.json'}
                                 for p in before))
            self.assertFalse((root / 'logs').exists())
            review._check_fingerprints(before)
            proof['officialSources'][0]['archiveSha256'] = '4' * 64
            config.write_text(json.dumps({'schema': 1, 'resolutions': [entry]}))
            with self.assertRaisesRegex(ValueError, 'Assessment source changed'):
                review._check_fingerprints(before)

    def test_published_definition_reuse_is_bound_to_its_current_target_scope(self):
        from tr_impact_evidence import _receipt
        quote = ('Synthetic TS 38.533 v19.4.0 clause A.8.1 reuses definitions '
                 'from 5.2.2 and 5.2.3 of synthetic TR 38.903.')
        root, source, row, manifest, entry = self.fixture(quote, wg='RAN4')
        entry['verifiedImpactScope'] = 'published_definition_reuse'
        entry['scopeAssessment']['scope'] = 'published_definition_reuse'
        evidence = entry['incorporationEvidence']
        evidence.update(basis='published_target_definition_reuse',
                        targetSpecVersion='19.4.0', targetClause='A.8.1')
        entry['additionalSourceEvidence'] = [dict(evidence)]
        manifest.write_text(json.dumps({'schema': 1, 'wg': 'RAN4', 'claims': [entry]}))
        require_verified_impacts(root, 'RAN4', [row])
        self.assertEqual(entry['status'], 'verified')
        self.assertEqual((evidence['basis'], evidence['targetSpecVersion'], evidence['targetClause']),
                         ('published_target_definition_reuse', '19.4.0', 'A.8.1'))
        self.assertIn('5.2.2', evidence['quote'])
        self.assertIn('5.2.3', evidence['quote'])
        self.assertTrue(entry['additionalSourceEvidence'])
        for additional in entry['additionalSourceEvidence']:
            _receipt(root, additional)
        self.assertNotIn('first introduced', entry['verifiedImpactDescription'].lower())

    def test_verified_no_change_requires_bounded_explicit_negative_evidence(self):
        root, source, row, manifest, entry = self.fixture(
            source_quote='This decision leaves TS 38.533 unchanged between v17.1.0 and v17.2.0.')
        row.update(impactType='NoChange', impactsSpec='')
        entry['claim']=claim_of(row)
        manifest.write_text(json.dumps({'schema':1,'wg':'RAN5','claims':[entry]}))
        with self.assertRaisesRegex(ImpactEvidenceError,'explicit negative evidence'):
            assess_impacts(root,'RAN5',[dict(row)])
        entry.update(boundedScope='TS 38.533 v17.1.0 versus v17.2.0 for this change decision')
        entry['incorporationEvidence']['kind']='explicit_no_change'
        entry['verifiedImpactScope']='explicit_no_change'
        entry['scopeAssessment']['scope']='explicit_no_change'
        manifest.write_text(json.dumps({'schema':1,'wg':'RAN5','claims':[entry]}))
        instance=evidence_instance(root,'RAN5',dict(row))
        self.assertEqual(instance['evidenceStatus'],'source_verified')
        self.assertNotIn('impactsSpec',instance)
        self.assertNotIn('impactsSection',instance)

    def test_verified_operation_scope_is_required_and_keeps_reuse_distinct(self):
        root, source, row, manifest, entry = self.fixture()
        entry.pop('verifiedImpactScope')
        manifest.write_text(json.dumps({'schema': 1, 'wg': 'RAN5', 'claims': [entry]}))
        with self.assertRaisesRegex(ImpactEvidenceError, 'operation scope'):
            require_verified_impacts(root, 'RAN5', [row])
        entry['verifiedImpactScope'] = 'published_analysis_reuse'
        entry['scopeAssessment']['scope'] = 'published_analysis_reuse'
        manifest.write_text(json.dumps({'schema': 1, 'wg': 'RAN5', 'claims': [entry]}))
        instance = evidence_instance(root, 'RAN5', dict(row))
        self.assertEqual(instance['impactType'], 'ExtendSection')
        self.assertEqual(instance['verifiedImpactScope'], 'published_analysis_reuse')
        pending = dict(row, trNumber='38.999', verifiedImpactScope='existing_section_change')
        assess_impacts(root, 'RAN5', [pending])
        self.assertEqual(pending['evidenceStatus'], 'pending')
        self.assertNotIn('verifiedImpactScope', pending)

    def test_completed_study_negative_keeps_its_rule_premise_and_output_scope(self):
        from tr_impact_evidence import _receipt
        premise_quote = "Synthetic rule: the example study's direct outputs contain reports only."
        role_quotes = [
            ('exact_study_identity', 'Synthetic study identity STUDY-EXAMPLE.'),
            ('explicit_study_item_classification', 'Synthetic classification: Study Item.'),
            ('closed_expected_output_table_single_TR_row', 'Synthetic expected output: TR 38.906 only.'),
            ('completion_report_study_item_100_percent', 'Synthetic completion: 100%.'),
            ('completion_report_CR_list_single_TR918_CR', 'Synthetic change list: R5-990001 only.'),
            ('completion_change_actual_deliverable_release', 'Synthetic output release: Rel-18.'),
        ]
        root, source, row, manifest, entry = self.fixture(
            '\n'.join([premise_quote, *(quote for role, quote in role_quotes)]))
        row.update(trNumber='38.906', impactType='NoChange', impactsSpec='',
                   impactDescription='The synthetic study has no direct specification deliverable.')
        entry.update(claim=claim_of(row), originalRow=dict(row),
                     verifiedImpactDescription=row['impactDescription'],
                     verifiedImpactScope='explicit_no_change',
                     boundedScope='STUDY-EXAMPLE: Direct standardization deliverables in this synthetic case.',
                     reviewExplanation='Rule-based bounded deduction over the synthetic completed study.')
        premise = entry['incorporationEvidence']
        premise.update(kind='explicit_no_change', quote=premise_quote)
        entry['scopeAssessment']['scope'] = 'explicit_no_change'
        entry['sourceEvidence'] = [dict(premise, evidenceRole=role, quote=quote,
                                        locator=f'synthetic premise/{role}')
                                   for role, quote in role_quotes]
        manifest.write_text(json.dumps({'schema': 1, 'wg': 'RAN5', 'claims': [entry]}))
        instance = evidence_instance(root, 'RAN5', dict(row))
        self.assertEqual(instance['evidenceStatus'], 'source_verified')
        self.assertEqual(instance['verifiedImpactScope'], 'explicit_no_change')
        self.assertEqual(entry['originalRow']['impactType'], 'NoChange')
        self.assertIn('STUDY-EXAMPLE', entry['boundedScope'])
        self.assertIn('Direct standardization deliverables', entry['boundedScope'])
        self.assertIn('Rule-based bounded deduction', entry['reviewExplanation'])
        # A separate, hash-bound rule premise supports the bounded negative conclusion.
        _receipt(root, premise)
        self.assertEqual(premise['quote'], premise_quote)
        for (role, quote), expected in zip(role_quotes,
                ('STUDY-EXAMPLE', 'Study Item', '38.906', '100%', 'R5-990001', 'Rel-18')):
            receipt = next(r for r in entry['sourceEvidence'] if r['evidenceRole'] == role)
            _receipt(root, receipt)
            self.assertIn(expected, receipt['quote'])

    def test_retained_and_discovered_assertions_have_source_assessments_and_exact_receipts(self):
        from tr_impact_evidence import _receipt, study_assertion_instances
        count = findings = 0
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            root, source, rows, path, manifest = self.mixed_fixture(wg)
            for entry in manifest['claims']:
                count += 1
                self.assertTrue(entry['sourceReview']['verdict'])
                self.assertTrue(entry['sourceReview']['reviewExplanation'])
                self.assertTrue(entry['sourceEvidence'])
                for receipt in entry['sourceEvidence']:
                    _receipt(root, receipt)
            findings += len(study_assertion_instances(root, wg))
        self.assertEqual(count, 25)
        self.assertEqual(findings, 10)

    def test_source_discovery_keeps_legacy_rows_and_target_identity_separate(self):
        from reconcile_tr_impact_evidence import retained_claim_keys
        for wg in ('RAN4', 'RAN5'):
            root, source, rows, path, manifest = self.mixed_fixture(wg)
            old = next(e for e in manifest['claims'] if e['claim']['impactsSpec'] == '38.532')
            new = next(e for e in manifest['claims'] if e.get('inputOrigin') == 'source_discovery')
            self.assertEqual(old['claim']['trNumber'], new['claim']['trNumber'])
            self.assertNotEqual(old['claim']['impactsSpec'], new['claim']['impactsSpec'])
            self.assertEqual(old['status'], 'pending')
            self.assertTrue(old['originalRow'])
            self.assertNotIn('originalRow', new)
            self.assertEqual(len(retained_claim_keys(new)), 1)
            self.assertEqual(new['inputOrigin'], 'source_discovery')
        root, source, row, manifest, entry = self.fixture()
        entry['inputOrigin'] = 'source_discovery'
        entry['discoveredInputRow'] = dict(row)
        entry['discoveryEvidence'] = {'path': 'decision.txt', 'sha256': 'invented'}
        manifest.write_text(json.dumps({'schema': 1, 'wg': 'RAN5', 'claims': [entry]}))
        with self.assertRaisesRegex(ImpactEvidenceError, 'source-discovery'):
            require_verified_impacts(root, 'RAN5', [row])

    def test_source_template_identity_resolution_uses_official_archive_and_body(self):
        from tr_source_identity import resolution_for
        root, source, config, entry, proof = self.identity_proof_fixture()
        entry['canonicalTitle'] = 'Synthetic inter-band source identity example'
        config.write_text(json.dumps({'schema': 1, 'resolutions': [entry]}))
        result = resolution_for(root, 'RAN4', '38.716-04-01', source)
        self.assertEqual(result['sourceCoverNumber'], '36.716-04-01')
        self.assertEqual(result['trNumber'], '38.716-04-01')
        self.assertEqual(result['canonicalTitle'], entry['canonicalTitle'])
        self.assertIsNone(resolution_for(root, 'RAN4', '38.803', source))

    def test_noncausal_source_finding_does_not_become_a_feature_or_tr_impact(self):
        from tr_impact_evidence import study_assertion_instances
        from rdflib import Graph, Namespace, RDF, URIRef, Literal
        from rdflib.namespace import XSD
        from owlrl import DeductiveClosure, RDFS_Semantics
        root, source, rows, path, manifest = self.mixed_fixture('RAN3')
        t = Namespace('https://w3id.org/spectra#')
        g = Graph().parse(ROOT / 'ontology/schema/tdoc-ontology.ttl')
        finding = study_assertion_instances(root, 'RAN3')[0]
        node = URIRef(finding['@id'])
        g.add((node, RDF.type, t.EvidenceAssertion))
        g.add((node, t.assertionId, Literal(finding['assertionId'], datatype=XSD.string)))
        g.add((node, t.assertionSubject, URIRef(finding['assertionSubject']['@id'])))
        g.add((node, t.assertionObject, URIRef(finding['assertionObject']['@id'])))
        g.add((node, t.assertionPredicateIRI, Literal(finding['assertionPredicateIRI'], datatype=XSD.anyURI)))
        DeductiveClosure(RDFS_Semantics).expand(g)
        self.assertNotIn((node, RDF.type, t.FeatureAssertion), g)
        self.assertNotIn((node, RDF.type, t.TRImpact), g)

    def test_nonunique_target_hub_cannot_silently_materialize_a_causal_edge(self):
        from tr_impact_evidence import link_assessed_impact_targets
        root, source, row, manifest, entry = self.fixture()
        row['trImpactId']='fixture-impact'
        class AmbiguousTarget:
            def run(self,query,**params):return self
            def single(self):return {'count':0}
        with self.assertRaisesRegex(ImpactEvidenceError,'not unique'):
            link_assessed_impact_targets(AmbiguousTarget(),root,'RAN5',[row])

    def test_actual_five_generators_preserve_all_input_assertions(self):
        import importlib.util
        for wg in ('RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5'):
            filename = '01_parse_tr_docs.py' if wg == 'RAN5' else '02_generate_tr_jsonld.py'
            path = BASE / wg / 'phase-5/tr-parser' / filename
            spec = importlib.util.spec_from_file_location('generator_' + wg, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            root, source, rows, manifest, payload = self.mixed_fixture(wg)
            csvpath = manifest.with_name('tr_impact_mapping.csv')
            with patch.object(module, 'PROJECT_ROOT', root):
                if wg == 'RAN1':
                    instances = [module.create_tr_impact_instance(r) for r in rows]
                elif wg in ('RAN2', 'RAN3'):
                    instances = module.generate_impact_instances(rows)
                elif wg == 'RAN4':
                    instances = module.generate_jsonld([], rows)['@graph']
                else:
                    with patch.object(module, 'IMPACT_CSV', csvpath):
                        instances = module.load_impact_mapping()
            self.assertEqual(len(instances), len(rows), wg)
            for instance in instances:
                status = instance.get('tdoc:evidenceStatus', instance.get('evidenceStatus'))
                self.assertIn(status, ('source_verified', 'pending', 'rejected'))
                if status != 'source_verified':
                    self.assertNotIn('impactsSpec', instance)
                    self.assertNotIn('tdoc:impactsSpec', instance)

    def test_clause_specific_assertions_keep_distinct_ids_and_reject_duplicates(self):
        import importlib.util
        for wg in ('RAN2', 'RAN3'):
            path = BASE / wg / 'phase-5/tr-parser/02_generate_tr_jsonld.py'
            spec = importlib.util.spec_from_file_location('identity_' + wg, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            root, source, row, manifest, entry = self.fixture(wg=wg)
            original = {'trNumber': '38.999', 'impactType': 'ExtendSection',
                        'impactsSpec': '38.423', 'impactsSection': '',
                        'impactDescription': 'Synthetic unreviewed study claim'}
            first = dict(original, impactsSection='8.2.1.2')
            second = dict(original, impactsSection='8.2.4.2')
            with self.subTest(wg=wg), patch.object(module, 'PROJECT_ROOT', root):
                # Unknown synthetic claims stay pending while their IDs remain distinct.
                instances = module.generate_impact_instances([dict(original), first, second])
                self.assertEqual([i['tdoc:trImpactId'] for i in instances],
                                 ['38.999-38.423', '38.999-38.423-S8.2.1.2',
                                  '38.999-38.423-S8.2.4.2'])
                self.assertTrue(all(i['tdoc:evidenceStatus'] == 'pending' for i in instances))
                with self.assertRaisesRegex(SystemExit, 'trImpactId'):
                    module.generate_impact_instances([dict(first), dict(first)])

    def test_loader_persists_pending_without_causal_promotion(self):
        class Result:
            def __init__(self, data): self.data = data
            def single(self): return self.data
            def consume(self): return None
        class Session:
            def __init__(self): self.calls = []
            def execute_write(self, f): return f(self)
            def run(self, query, **params):
                self.calls.append((query, params)); return Result({'count': len(params.get('rows', []))})
        row = {'trImpactId': 'test-pending', 'trNumber': '38.999', 'impactType': 'NewTS', 'impactsSpec': '38.999', 'impactDescription': 'Unreviewed input'}
        session = Session()
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(load_assessed_impact_nodes(session, Path(directory), 'RAN1', [row]), 1)
        self.assertEqual(session.calls[0][1]['rows'][0]['evidenceStatus'], 'pending')
        self.assertIn('DELETE r', session.calls[0][0])
        self.assertNotIn('MERGE (imp)-[:IMPACTS_SPEC]', session.calls[0][0])

    def test_verified_status_cannot_be_forged_or_reused_for_inflated_claim(self):
        root, source, valid, manifest, entry = self.fixture(wg='RAN1')
        row = {'trImpactId': 'forged', 'trNumber': '38.999', 'impactType': 'NewTS',
               'impactsSpec': '38.999', 'evidenceStatus': 'source_verified'}
        assess_impacts(root, 'RAN1', [row])
        self.assertEqual(row['evidenceStatus'], 'pending')
        root, source, row, manifest, entry = self.fixture()
        row['impactDescription'] = 'All TS content originates from the TR.'
        with self.assertRaisesRegex(ImpactEvidenceError, '검증된 범위'):
            assess_impacts(root, 'RAN5', [row])


if __name__ == '__main__':
    unittest.main()
