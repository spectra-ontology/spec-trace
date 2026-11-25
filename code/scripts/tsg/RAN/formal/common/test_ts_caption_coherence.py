#!/usr/bin/env python3
"""test_ts_caption_coherence.py — source-section and edition-bound captions.

Spec: primary/P12 equivalent source-body presentation.
Ontology: source identifiers, rather than list offsets, bind actual evidence.
Cycle: sparse source IDs → exact caption line → reject edition/content drift.
배경: filtering a census preserves original candidate identifiers.
사용: python3 -B -m unittest discover -s scripts/tsg/RAN/formal/common -p test_ts_caption_coherence.py
LLM 호출: 없음.
"""
from copy import deepcopy
import unittest

from ts_caption_coherence import complete_twins, sha


class CoherentSourceCaptions(unittest.TestCase):
    def setUp(self):
        old, new = 'Table 5-1: X2', 'Table 5-1: X<sub>2</sub>'
        source = {'edition': ['RAN5', '38.533', 'Rel-19'], 'sectionId': '38.533-5'}
        edit = {'lineIndex': 0, 'oldCaption': old, 'replacementCaption': new,
                'oldLineSHA256': sha(old + '\n'), 'newLineSHA256': sha(new + '\n'), 'sourceCandidateIds': [91]}
        self.a = {'collection': 'ran5_ts_sections', 'pointId': 17, 'chunkId': '38.533-5-001',
                  'oldBodySHA256': sha('original'), 'newBodySHA256': sha(new + '\nbody'),
                  'captionEdits': [edit], 'sources': [source]}
        self.b = {**deepcopy(self.a), 'collection': 'ran5_ts_sections_p12', 'newBodySHA256': sha(old + '\nbody')}
        self.b.pop('captionEdits')
        self.bodies = {('ran5_ts_sections', '17'): new + '\nbody', ('ran5_ts_sections_p12', '17'): old + '\nbody'}
        self.candidates = [{'candidate': 91, 'wg': 'RAN5', 'spec': '38.533', 'release': 'Rel-19',
                            'oldCaption': old, 'replacementCaption': new,
                            'observedSourceSections': [{'sectionNumber': '5'}],
                            'source': 'source.docx', 'sourceSHA256': 'sourceSHA', 'sourceLocator': 'actual p[4]'}]

    def test_sparse_source_identifier_newline_hash_and_exact_body_completion(self):
        originals = deepcopy([self.a, self.b])
        records, bodies, changes = complete_twins([self.a, self.b], self.bodies, self.candidates)
        self.assertEqual(bodies['ran5_ts_sections', '17'], bodies['ran5_ts_sections_p12', '17'])
        self.assertEqual(records[0]['newBodySHA256'], records[1]['newBodySHA256'])
        self.assertEqual(len(changes), 1)
        self.assertEqual([self.a, self.b], originals)

    def test_other_editions_and_other_source_sections_are_rejected(self):
        for field, value in [('release', 'Rel-18'), ('observedSourceSections', [{'sectionNumber': '6'}])]:
            candidates = deepcopy(self.candidates); candidates[0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'source-section/edition'):
                complete_twins([self.a, self.b], self.bodies, candidates)

    def test_body_difference_outside_caption_is_rejected(self):
        self.bodies['ran5_ts_sections_p12', '17'] += ' another statement'
        with self.assertRaisesRegex(ValueError, 'outside'):
            complete_twins([self.a, self.b], self.bodies, self.candidates)

    def test_distinct_historical_bodies_are_not_merged(self):
        self.b['oldBodySHA256'] = sha('another source')
        with self.assertRaisesRegex(ValueError, 'historical bodies'):
            complete_twins([self.a, self.b], self.bodies, self.candidates)


if __name__ == '__main__':
    unittest.main()
