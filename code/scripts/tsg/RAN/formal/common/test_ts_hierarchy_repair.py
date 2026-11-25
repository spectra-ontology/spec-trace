#!/usr/bin/env python3
"""test_ts_hierarchy_repair.py — non-leaf repair ownership and source identity.

Spec: Phase-3 exact source-closure repair. Ontology: Section parent/inverse identity.
Cycle: reviewed parsed/live preimages → permitted delta → foreign preservation.
배경: a missing numbered parent changes depth and edges, never unrelated facts.
사용: python -m unittest discover -s scripts/tsg/RAN/formal/common -p test_ts_hierarchy_repair.py.
LLM 호출: none; in-memory fixtures only.
"""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from ts_hierarchy_repair import project_sections, verify_delta


def section(number, level, parent, children):
    prefix = '38.533-Rel-18-'
    return dict(sectionId=prefix + number, sectionNumber=number, sectionTitle='Title ' + number,
                level=level, isVoid=False, parentSectionId=prefix + parent if parent else None,
                childSectionIds=[prefix + n for n in children], references=[], referencesSpec=[])


class HierarchyRepair(unittest.TestCase):
    def publication_fixture(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        source_plan = root / 'review.json'; source_plan.write_text('synthetic review')
        parsed = root / 'parsed.json'; parsed.write_text(json.dumps(self.document))
        raw = parsed.read_bytes()
        projected, selected = project_sections(self.document, self.review)
        review = dict(self.review, foreignOrQualifiedEdgesToPreserve=[])
        pins = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (source_plan, parsed)}
        return root, source_plan, parsed, (review, pins, parsed, raw, projected, selected)

    def run_fixture(self, root, source_plan, output, prepared):
        import ts_hierarchy_repair as repair
        driver = MagicMock()
        session = driver.__enter__.return_value.session.return_value.__enter__.return_value
        tx = session.begin_transaction.return_value
        with patch.object(repair, 'ROOT', root), patch.object(repair, 'prepare', return_value=prepared), \
                patch.object(repair, 'snapshot', side_effect=[self.before, self.before, self.after, self.after]), \
                patch('neo4j.GraphDatabase.driver', return_value=driver), \
                patch.object(repair.axis, 'bolt_uri', return_value='synthetic'), \
                patch.object(repair.credentials, 'neo4j_auth', return_value=('fake', 'fake')):
            try:
                return repair.run(source_plan, output, apply=True)
            except BaseException:
                tx.rollback.assert_called_once()
                tx.close.assert_called_once()
                raise

    def test_publication_failure_restores_current_attempt_and_retries(self):
        import ts_hierarchy_repair as repair
        from common import atomic_io
        for operation in ('fsync', 'post_replace'):
            for error in (OSError, KeyboardInterrupt):
                with self.subTest(operation=operation, error=error):
                    root, plan, parsed, prepared = self.publication_fixture()
                    before = parsed.read_bytes()
                    original_write = repair.write_text_atomic
                    fired = False
                    def fail_once(path, text):
                        nonlocal fired
                        if Path(path) == parsed and not fired:
                            fired = True
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
                    with patch.object(repair, 'write_text_atomic', side_effect=fail_once):
                        with self.assertRaises(error):
                            self.run_fixture(root, plan, root / 'failed', prepared)
                    self.assertEqual(parsed.read_bytes(), before)
                    self.assertFalse(list(root.rglob('*.tmp')))
                    self.assertEqual(self.run_fixture(root, plan, root / 'retry', prepared)['status'], 'complete')
                    self.assertEqual(json.loads(parsed.read_text()), prepared[4])

    def test_publication_rollback_preserves_concurrent_generation(self):
        import ts_hierarchy_repair as repair
        root, plan, parsed, prepared = self.publication_fixture()
        original_write = repair.write_text_atomic
        def concurrent(path, text):
            original_write(path, text)
            if Path(path) == parsed:
                parsed.write_text('concurrent generation')
                raise KeyboardInterrupt('after concurrent replacement')
        with patch.object(repair, 'write_text_atomic', side_effect=concurrent):
            with self.assertRaises(KeyboardInterrupt):
                self.run_fixture(root, plan, root / 'receipt', prepared)
        self.assertEqual(parsed.read_text(), 'concurrent generation')

    def setUp(self):
        root = section('19', 1, None, ['19.5.1'])
        child = section('19.5.1', 2, '19', [])
        parent = section('19.5', 2, '19', ['19.5.1'])
        after_root = section('19', 1, None, ['19.5'])
        after_child = section('19.5.1', 3, '19.5', [])
        def update(a, b):
            return {'sectionId': a['sectionId'], 'before': a, 'after': b,
                    'deltas': {k: {'before': a[k], 'after': b[k]} for k in a if a[k] != b[k]}}
        self.review = {'updates': [update(root, after_root), update(child, after_child)],
                       'addedSections': [parent], 'removedSectionIds': [],
                       'parentOwnershipDeltas': [dict(sectionId=parent['sectionId'], oldParent=None, newParent=root['sectionId']),
                           dict(sectionId=child['sectionId'], oldParent=root['sectionId'], newParent=parent['sectionId'])]}
        self.document = dict(spec_number='38.533', release='Rel-18', stats=dict(sections=2),
                             sections=copy.deepcopy([root, child]), tables=[{'preserve': 1}], unknown={'preserve': 'all'})
        def node(sec, eid):
            props = {k: sec[k] for k in ('sectionId', 'sectionNumber', 'sectionTitle', 'level', 'isVoid')}
            props.update(specNumber='38.533', granularity='section')
            return dict(eid=eid, labels=['ConformanceTest', 'Section'], properties=props)
        def edge(eid, a, rel, b, props=None):
            return dict(eid=eid, start=a, type=rel, end=b, properties=props or {})
        spec = dict(eid='spec', labels=['Spec'], properties={'specNumber': '38.533', 'specRelease': 'Rel-18'})
        retained = [edge('b1', 'root', 'BELONGS_TO_SPEC', 'spec'), edge('b2', 'child', 'BELONGS_TO_SPEC', 'spec'),
                    edge('foreign', 'foreign', 'MODIFIES_SECTION', 'child', {'source': 'preserved'})]
        self.before = dict(nodes=[node(root, 'root'), node(child, 'child')], spec=spec,
                           edges=retained + [edge('p1', 'child', 'PARENT_SECTION', 'root'), edge('p2', 'root', 'HAS_SUB_SECTION', 'child')])
        self.after = dict(nodes=[node(after_root, 'root'), node(after_child, 'child'), node(parent, 'parent')], spec=spec,
                          edges=retained + [edge('n1', 'parent', 'BELONGS_TO_SPEC', 'spec'),
                            edge('n2', 'parent', 'PARENT_SECTION', 'root'), edge('n3', 'root', 'HAS_SUB_SECTION', 'parent'),
                            edge('n4', 'child', 'PARENT_SECTION', 'parent'), edge('n5', 'parent', 'HAS_SUB_SECTION', 'child')])

    def test_closes_non_leaf_without_replacing_other_canonical_data(self):
        result, ids = project_sections(self.document, self.review)
        self.assertEqual([s['sectionNumber'] for s in result['sections']], ['19', '19.5', '19.5.1'])
        self.assertEqual(result['tables'], self.document['tables'])
        self.assertEqual(result['unknown'], self.document['unknown'])
        self.assertEqual(result['stats']['sections'], 3)
        self.assertEqual(len(ids), 3)
        verify_delta(self.before, self.after, self.review, '38.533')

    def test_stale_canonical_preimage_is_rejected(self):
        self.document['sections'][1]['sectionTitle'] = 'Concurrent source change'
        with self.assertRaisesRegex(ValueError, 'preimage'):
            project_sections(self.document, self.review)

    def test_topic_or_identity_edits_are_outside_hierarchy_scope(self):
        self.review['updates'][1]['after']['sectionTitle'] = 'Other topic'
        with self.assertRaisesRegex(ValueError, 'non-owned'):
            project_sections(self.document, self.review)

    def test_exact_numbered_parent_and_depth_are_required(self):
        for field, value in [('parentSectionId', '38.533-Rel-18-19'), ('level', 2)]:
            review = copy.deepcopy(self.review)
            review['updates'][1]['after'][field] = value
            a, b = review['updates'][1]['before'], review['updates'][1]['after']
            review['updates'][1]['deltas'] = {k: {'before': a[k], 'after': b[k]} for k in a if a[k] != b[k]}
            with self.assertRaises(ValueError):
                project_sections(self.document, review)

    def test_parent_child_projections_cannot_disagree(self):
        self.review['addedSections'][0]['childSectionIds'] = []
        with self.assertRaisesRegex(ValueError, 'inverse'):
            project_sections(self.document, self.review)

    def test_foreign_relationship_must_be_exactly_preserved(self):
        self.after['edges'] = [e for e in self.after['edges'] if e['eid'] != 'foreign']
        with self.assertRaises(ValueError):
            verify_delta(self.before, self.after, self.review, '38.533')

    def test_extra_owned_relationship_is_rejected(self):
        self.after['edges'].append(dict(eid='extra', start='child', end='root', type='PARENT_SECTION', properties={}))
        with self.assertRaisesRegex(ValueError, 'Created'):
            verify_delta(self.before, self.after, self.review, '38.533')

    def test_existing_unknown_node_properties_are_protected(self):
        self.after['nodes'][1]['properties']['foreign'] = 'new'
        with self.assertRaisesRegex(ValueError, 'outside'):
            verify_delta(self.before, self.after, self.review, '38.533')


if __name__ == '__main__':
    unittest.main()
