#!/usr/bin/env python3
"""test_asn1_fragments.py — scope, exact assembly and primary-FK regressions.

Spec: lossless ASN.1 source-fragment contract.
Ontology: one ASN.1 type, ordered fragments and one primary RRCParameter FK.
Cycle: source fixture → bounded fragments → full assembly / consumer extraction.
배경: full definitions can exceed the encoder window without being source pollution.
사용: python3 -m unittest discover -s scripts/common/common -p test_asn1_fragments.py
LLM 호출: 없음; no database, model or encoder execution.
"""
import copy
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

from asn1_fragments import fragment_definition, assemble_definition, boundaries, context_text, fetch_definition


def fixture():
    text = ('Example ::= SEQUENCE {\nbase INTEGER (0..8) OPTIONAL,\n... ,\n[[\n'
        + ''.join(f'-- field {i} {{ literal }}\nf{i}-r19 SEQUENCE {{\nvalue INTEGER (1..8),\nflag BOOLEAN\n}} OPTIONAL,\n' for i in range(9))
        + 'last BOOLEAN OPTIONAL\n]]\n}')
    return dict(chunkId='38.331-asn1-Example-001', sectionId='38.331-asn1-Example',
        specNumber='38.331', tsSectionNumber='6.3.2', text=text, chunkIndex=1, totalChunks=1,
        asn1={'ieName':'Example', 'ieKind':'SEQUENCE'})


class ASN1Fragments(unittest.TestCase):
    def rows(self):
        return fragment_definition(fixture(), len, 570)

    def test_lossless_complete_fields_and_extension_scope(self):
        rows = self.rows()
        self.assertGreater(len(rows), 1)
        self.assertEqual(assemble_definition(rows), fixture()['text'])
        self.assertEqual(rows[0]['chunkId'], fixture()['chunkId'])
        self.assertTrue(all(len(row['text']) <= 570 for row in rows))
        self.assertTrue(any(row['sourceFragment']['extensionGroupAtStart'] == 1 for row in rows[1:]))
        self.assertTrue(all(row['sourceFragment']['boundaryKind'] == 'complete_outer_field' for row in rows))
        self.assertEqual(''.join(row['sourceText'] for row in rows), fixture()['text'])

    def test_missing_duplicate_changed_scope_and_range_fail_closed(self):
        rows = self.rows()
        for mutation in ('missing','duplicate','text','scope','range','context','identity'):
            with self.subTest(mutation=mutation):
                edited = copy.deepcopy(rows)
                if mutation == 'missing': edited.pop()
                elif mutation == 'duplicate': edited[1] = copy.deepcopy(edited[0])
                elif mutation == 'text': edited[1]['sourceText'] += 'X'
                elif mutation == 'scope': edited[1]['sourceFragment']['extensionGroupAtStart'] = 99
                elif mutation == 'range': edited[1]['sourceFragment']['sourceStart'] += 1
                elif mutation == 'context': edited[1]['sourceFragment']['contextText'] = 'standalone definition'
                elif mutation == 'identity': edited[1]['asn1']['ieName'] = 'Other'
                with self.assertRaises(ValueError): assemble_definition(edited)

    def test_one_giant_complete_field_and_unresolved_definition_are_rejected(self):
        row = fixture()
        row['text'] = 'Example ::= SEQUENCE {\nx SEQUENCE {\n' + 'y BOOLEAN,\n' * 100 + '} OPTIONAL\n}'
        with self.assertRaisesRegex(ValueError, 'complete ASN.1 outer field'):
            fragment_definition(row, len, 570)
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            boundaries('Example ::= SEQUENCE {\nx BOOLEAN\n')

    def test_consistently_renamed_metadata_cannot_change_source_type_identity(self):
        rows = self.rows()
        for row in rows:
            row['asn1']['ieName'] = 'Other'
            item = row['sourceFragment']
            item['typeName'] = 'Other'
            item['contextText'] = context_text('Other', item['extensionGroupAtStart'])
            row['text'] = item['contextText'] + '\n' + row['sourceText']
        with self.assertRaisesRegex(ValueError, 'source declaration'):
            assemble_definition(rows)

    def test_unchanged_definition_and_quoted_braces(self):
        row = fixture()
        self.assertIs(fragment_definition(row, len, 10000)[0], row)
        name, _ = boundaries('Example ::= SEQUENCE {\nx UTF8String DEFAULT "{ [[",\ny BIT STRING DEFAULT \'001\'B\n}')
        self.assertEqual(name, 'Example')

    def test_reversed_scroll_retains_one_primary_entity_and_full_catalog_body(self):
        rows = self.rows()
        root = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
        sys.path.insert(0, str(root / 'scripts/common/ontology'))
        import entity_loader_common as common
        with patch.object(common, 'iter_qdrant_points', return_value=iter(reversed(rows))):
            records = list(common.extract_rrc_parameters(None, 'synthetic'))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].asn1_chunk_id, fixture()['chunkId'])
        class Client:
            def scroll(self, **kwargs):
                return [types.SimpleNamespace(payload=row) for row in reversed(rows)], None
        view = fetch_definition(Client(), 'synthetic', rows[-1])
        self.assertEqual(view['text'], fixture()['text'])
        self.assertTrue(view['sourceFragment']['assembledRetrievalView'])
        self.assertEqual(view['chunkId'], fixture()['chunkId'])

    def test_actual_catalog_assembles_when_first_hit_is_continuation(self):
        root = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
        sys.path.insert(0, str(root / 'scripts/capability/answer/answer_pipeline'))
        import catalog_helpers
        rows = self.rows()
        class Client:
            def scroll(self, **kwargs):
                return [types.SimpleNamespace(payload=row) for row in reversed(rows)], None
        result = catalog_helpers.enumerate_ies_by_prefix(Client(), 'synthetic', 'Example')
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['chunkId'],fixture()['chunkId'])
        self.assertEqual(result[0]['definitionText'],fixture()['text'])
        self.assertEqual(result[0]['assembledSourceFragments'],[row['chunkId'] for row in rows])
        with patch.object(catalog_helpers,'fetch_definition',side_effect=ValueError('missing continuation')):
            with self.assertRaisesRegex(ValueError,'missing continuation'):
                catalog_helpers.enumerate_ies_by_prefix(Client(), 'synthetic', 'Example')

    def test_fetch_rejects_repeated_cursor_and_assembles_advancing_pages(self):
        rows = self.rows()
        points = [types.SimpleNamespace(payload=row) for row in rows]
        for repeated in (True, False):
            with self.subTest(repeated=repeated):
                pages = [(points[:1], 7), ([], 7)] if repeated else [
                    (points[:1], 7), ([], 9), (points[1:], None)]
                client = types.SimpleNamespace(scroll=Mock(side_effect=[*pages,
                    AssertionError('repeated scroll was not refused')]))
                if repeated:
                    with self.assertRaisesRegex(ValueError, '반복'):
                        fetch_definition(client, 'synthetic', rows[-1])
                    self.assertEqual(client.scroll.call_count, 2)
                else:
                    result = fetch_definition(client, 'synthetic', rows[-1])
                    self.assertEqual(result['text'], fixture()['text'])
                    self.assertEqual([c.kwargs['offset'] for c in client.scroll.call_args_list], [None, 7, 9])


if __name__ == '__main__':
    unittest.main()
