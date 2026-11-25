#!/usr/bin/env python3
"""Publication identity, exact parent matching and sibling preservation regressions.

Spec: standard numeric nested CID; explicit section-local ordering contract.
Ontology: a split retains the original section target and source provenance.
Cycle: colliding existing child → new nested identities → exact sibling checks.
배경: ID 충돌과 이웃 payload의 부수 변경을 실제 조건으로 막는다.
사용: python3 -B test_ts_source_context_publication.py.
LLM 호출: 없음.
"""
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import ts_source_context_publication as publication
from ts_source_context_publication import replace_and_reindex
from ts_source_context_split import sha, SourceContextError


def child(text):
    return dict(text=text, textSHA256=sha(text), coreText=text, tokens=len(text),
                corePlainSHA256=sha(text), sourceRows=[], sourceIntervals=[], context=[])


class Publication(unittest.TestCase):
    def test_binary_writer_preserves_modes_and_exclusive_publication(self):
        from common import atomic_io
        with tempfile.TemporaryDirectory(prefix='spectra-context-bytes-') as folder:
            root = Path(folder)
            path = root / 'bytes'
            atomic_io.write_bytes_atomic(path, b'\x00\xffcomplete', overwrite=False)
            self.assertEqual(path.read_bytes(), b'\x00\xffcomplete')
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            path.chmod(0o640)
            atomic_io.write_bytes_atomic(path, b'replaced')
            self.assertEqual(path.stat().st_mode & 0o777, 0o640)
            atomic_io.write_bytes_atomic(path, b'explicit', mode=0o600)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            for target in (path, root / 'dangling'):
                if target != path:
                    target.symlink_to(root / 'absent')
                with self.assertRaises(FileExistsError):
                    atomic_io.write_bytes_atomic(target, b'conflict', overwrite=False)
            self.assertTrue((root / 'dangling').is_symlink())
            self.assertEqual(path.read_bytes(), b'explicit')
            with self.assertRaises(ValueError):
                atomic_io.write_bytes_atomic(path, b'invalid', overwrite=1)
            with self.assertRaises(FileNotFoundError):
                atomic_io.write_bytes_atomic(root / 'missing/bytes', b'new')
            self.assertFalse((root / 'missing').exists())
            text = root / 'text'
            atomic_io.write_text_atomic(text, '본문\n', encoding='utf-16')
            self.assertEqual(text.read_bytes(), '본문\n'.encode('utf-16'))
            self.assertEqual({p.name for p in root.iterdir()}, {'bytes', 'dangling', 'text'})

    def test_plan_writer_syncs_deterministic_plain_and_gzip_bytes(self):
        import prepare_ts_source_context_split as prepare
        from common import atomic_io
        value = {'text': '본문', 'records': [0, None, True]}
        raw = (json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n').encode()
        for suffix in ('.json', '.json.gz'):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory(prefix='spectra-context-write-') as folder:
                path = Path(folder) / ('plan' + suffix)
                path.write_bytes(b'previous')
                path.chmod(0o640)
                expected = gzip.compress(raw, mtime=0) if suffix.endswith('.gz') else raw
                for _ in range(2):
                    with patch.object(atomic_io.os, 'fsync', wraps=atomic_io.os.fsync) as sync:
                        prepare.write(path, value)
                    self.assertEqual(sync.call_count, 1)
                    self.assertEqual(path.read_bytes(), expected)
                    self.assertEqual(path.stat().st_mode & 0o777, 0o640)
                    self.assertEqual(list(Path(folder).iterdir()), [path])
                self.assertEqual(json.loads(gzip.decompress(expected) if suffix.endswith('.gz') else expected), value)

    def test_plan_writer_partial_write_sync_replace_and_interrupt_preserve_retry(self):
        from contextlib import contextmanager
        import prepare_ts_source_context_split as prepare
        from common import atomic_io
        value = {'text': 'complete 본문'}
        named_temporary = atomic_io.tempfile.NamedTemporaryFile
        for suffix in ('.json', '.json.gz'):
            with tempfile.TemporaryDirectory(prefix='spectra-context-failure-') as folder:
                path = Path(folder) / ('plan' + suffix)
                for operation in ('write', 'fsync', 'replace'):
                    for error_type in (OSError, KeyboardInterrupt):
                        with self.subTest(suffix=suffix, operation=operation, error=error_type.__name__):
                            path.write_bytes(b'previous complete bytes')
                            path.chmod(0o640)
                            @contextmanager
                            def broken_stream(**kwargs):
                                with named_temporary(**kwargs) as stream:
                                    write = stream.write
                                    def partial_write(data):
                                        write(data[:3])
                                        stream.flush()
                                        raise error_type('synthetic partial write')
                                    with patch.object(stream, 'write', side_effect=partial_write):
                                        yield stream
                            failure = (patch.object(atomic_io.tempfile, 'NamedTemporaryFile', broken_stream)
                                       if operation == 'write' else
                                       patch.object(atomic_io.os, operation, side_effect=error_type('synthetic failure')))
                            with failure, self.assertRaises(error_type):
                                prepare.write(path, value)
                            self.assertEqual(path.read_bytes(), b'previous complete bytes')
                            self.assertEqual(path.stat().st_mode & 0o777, 0o640)
                            self.assertEqual(list(Path(folder).iterdir()), [path])
                            prepare.write(path, value)
                            raw = path.read_bytes()
                            self.assertEqual(json.loads(gzip.decompress(raw) if suffix.endswith('.gz') else raw), value)
                            self.assertEqual(list(Path(folder).iterdir()), [path])

    def test_plan_writer_preparation_errors_preserve_previous_bytes(self):
        import prepare_ts_source_context_split as prepare
        for suffix in ('.json', '.json.gz'):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory(prefix='spectra-context-prepare-') as folder:
                path = Path(folder) / ('plan' + suffix)
                path.write_bytes(b'previous')
                for value in ({'bad': float('nan')}, {'bad': object()}):
                    with self.assertRaises((ValueError, TypeError)):
                        prepare.write(path, value)
                    self.assertEqual(path.read_bytes(), b'previous')
                if suffix.endswith('.gz'):
                    for error_type in (OSError, KeyboardInterrupt):
                        with patch.object(prepare.gzip, 'compress', side_effect=error_type('synthetic compression')), \
                                self.assertRaises(error_type):
                            prepare.write(path, {'text': 'new'})
                        self.assertEqual(path.read_bytes(), b'previous')
                self.assertEqual(list(Path(folder).iterdir()), [path])

    def test_plan_and_hash_share_one_read_for_both_producer_paths(self):
        edition = ['RAN1', '38.000', 'Rel-18']
        value = {'records': [{'edition': edition, 'sourceFences': {},
                             'producerChunkId': 'synthetic-001', 'groups': []}],
                 'sourceSections': [{'edition': edition, 'sectionId': 'synthetic'}]}
        raw = json.dumps(value).encode()
        original = gzip.compress(raw, mtime=0)
        digest = hashlib.sha256(original).hexdigest()
        real_loads = json.loads
        for route in ('context', 'already_qualified'):
            with self.subTest(route=route), tempfile.TemporaryDirectory(prefix='spectra-context-plan-') as folder:
                root = Path(folder)
                path = root / 'ontology/config/ts_source_context_splits.json.gz'
                path.parent.mkdir(parents=True)
                path.write_bytes(original)

                def parse_then_change(source, *args, **kwargs):
                    result = real_loads(source, *args, **kwargs)
                    if source == raw or source == raw.decode():
                        path.write_bytes(gzip.compress(json.dumps(dict(value, concurrent=True)).encode(), mtime=0))
                    return result

                with patch.object(json, 'loads', side_effect=parse_then_change), \
                     patch.object(publication, 'file_sha', side_effect=AssertionError('plan must use captured bytes')):
                    if route == 'context':
                        context = publication.producer_source_context(*edition, [], root)
                        self.assertEqual(context['plan'], value)
                        self.assertEqual(context['planSHA256'], digest)
                    else:
                        chunks = [{'chunkId': f'synthetic-{index:03d}', 'sectionId': 'synthetic',
                                   'sourceContext': {'planSHA256': digest}} for index in range(1, 6)]
                        self.assertIs(publication.qualify_producer_chunks(chunks, *edition, [], root), chunks)
                self.assertNotEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    def test_collision_and_explicit_section_order_preserve_sibling_fields(self):
        parent = dict(chunkId='38.1-1-005', sectionId='38.1-1', sectionNumber='1',
                      chunkIndex=5, totalChunks=2, text='ab', specReleases=['Rel-19'], extra={'x': 3})
        sibling = dict(parent, chunkId='38.1-1-005-001', chunkIndex=6, text='sibling')
        record = dict(groups=[dict(children=[child('a'), child('b')], sourceBindings=[dict(edition=['RAN1', '38.1', 'Rel-19'])])])
        before = deepcopy(sibling)
        after, seen = replace_and_reindex([parent, sibling], {parent['chunkId']: record}, plan_sha='plan')
        self.assertEqual([c['chunkId'] for c in after], ['38.1-1-005-002', '38.1-1-005-003', sibling['chunkId']])
        self.assertEqual([c['chunkIndex'] for c in after], [5, 6, 7])
        self.assertTrue(all(c['totalChunks'] == 3 for c in after))
        self.assertEqual({k:v for k,v in after[-1].items() if k not in ('chunkIndex','totalChunks')},
                         {k:v for k,v in before.items() if k not in ('chunkIndex','totalChunks')})
        self.assertTrue(all(c['sectionId'] == '38.1-1' and c['extra'] == {'x':3} for c in after))
        self.assertEqual(seen, {parent['chunkId']})
        self.assertEqual(sibling, before)

    def test_changed_source_parent_cannot_reuse_a_plan(self):
        parent = dict(chunkId='38.1-1-001', sectionId='38.1-1', chunkIndex=1, text='changed')
        record = dict(groups=[dict(children=[child('a'), child('b')], sourceBindings=[])])
        with self.assertRaisesRegex(SourceContextError, 'regenerate'):
            replace_and_reindex([parent], {parent['chunkId']:record}, plan_sha='plan')

    def test_other_section_indices_and_identity_remain_exact(self):
        parent = dict(chunkId='38.1-1-001', sectionId='38.1-1', chunkIndex=0, text='ab')
        other = dict(chunkId='38.1-2-001', sectionId='38.1-2', chunkIndex=1, totalChunks=1, text='other')
        record = dict(groups=[dict(children=[child('a'), child('b')], sourceBindings=[])])
        after, _ = replace_and_reindex([parent, other], {parent['chunkId']:record}, plan_sha='plan')
        self.assertEqual(after[-1], other)
        self.assertEqual([c['chunkIndex'] for c in after[:-1]], [0,1])


class SourceCatalogPublication(unittest.TestCase):
    def fixture(self, root):
        import publish_ts_source_context_plan as publisher
        source = root / 'original.txt'
        source.write_text('Original source.')
        digest = publisher.file_sha(source)
        edition = ['RAN1', '38.001', 'Rel-18']
        sid = '38.001-1'
        fences = {'original.txt': digest}
        stage = root / 'RAN1_38.001_Rel-18.json.gz'
        stage.write_bytes(gzip.compress(json.dumps({'sections': [
            {'sectionId': sid, 'newText': 'Original source.'}]}).encode(), mtime=0))
        binding = dict(edition=edition, sectionId=sid, childSourceProvenance=[dict(
            textSHA256=digest, sourceRows=[], sourceIntervals=[], context=[])])
        shadow = dict(errors=[], summary=dict(completeParents=1, parents=1),
            sourceFences=fences, sourceShadowSHA256={str(stage): publisher.file_sha(stage)},
            records=[dict(chunkId='38.001-Rel-18-1-001', groups=[dict(
                sourceBindings=[binding], children=[dict(text='Original source.',
                    textSHA256=digest, context=[])])])])
        catalog = dict(editions=[dict(edition=edition, sourceFences=fences)])
        contexts = dict(sourceFences=fences, tables=[])
        paths = [root / (name + '.json') for name in ('shadow', 'catalog', 'contexts')]
        paths[1].write_text(json.dumps(catalog))
        catalog_sha = publisher.file_sha(paths[1])
        shadow['inputSHA256'] = {str(paths[1]): catalog_sha}
        contexts['catalogSHA256'] = catalog_sha
        paths[0].write_text(json.dumps(shadow))
        paths[2].write_text(json.dumps(contexts))
        return publisher, paths, catalog

    def test_source_catalog_must_match_prepared_source_generation(self):
        import contextlib
        import io
        for case in ('valid', 'other_source', 'missing_source', 'duplicate_edition',
                     'conflicting_hash', 'changed_catalog', 'missing_catalog_pin', 'changed_context_pin'):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                publisher, paths, catalog = self.fixture(root)
                if case == 'other_source':
                    other = root / 'other.txt'
                    other.write_text('Different source.')
                    catalog['editions'][0]['sourceFences'] = {'other.txt': publisher.file_sha(other)}
                elif case == 'missing_source':
                    catalog['editions'][0]['sourceFences'] = {}
                elif case == 'duplicate_edition':
                    catalog['editions'].append(deepcopy(catalog['editions'][0]))
                elif case == 'conflicting_hash':
                    catalog['editions'].append(dict(edition=['RAN1', '38.001', 'Rel-19'],
                                                   sourceFences={'original.txt': '0' * 64}))
                elif case == 'changed_catalog':
                    catalog['editions'][0]['edition'][2] = 'Rel-19'
                elif case == 'missing_catalog_pin':
                    shadow = json.loads(paths[0].read_text())
                    shadow['inputSHA256'] = {}
                    paths[0].write_text(json.dumps(shadow))
                elif case == 'changed_context_pin':
                    contexts = json.loads(paths[2].read_text())
                    contexts['catalogSHA256'] = '0' * 64
                    paths[2].write_text(json.dumps(contexts))
                paths[1].write_text(json.dumps(catalog))
                output = root / 'plan.json'
                output.write_text('previous-complete')
                with patch.object(publisher, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                    if case == 'valid':
                        publisher.publish(paths[0], paths[1], output, paths[2])
                        value = json.loads(output.read_text())
                        self.assertEqual(value['records'][0]['sourceFences'], catalog['editions'][0]['sourceFences'])
                    else:
                        with self.assertRaises(SourceContextError):
                            publisher.publish(paths[0], paths[1], output, paths[2])
                        self.assertEqual(output.read_text(), 'previous-complete')


if __name__ == '__main__':
    unittest.main()
