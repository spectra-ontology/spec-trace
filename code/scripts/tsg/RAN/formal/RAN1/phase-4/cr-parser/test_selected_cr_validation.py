#!/usr/bin/env python3
"""CR validation compares the selected parsed population, including small builds."""
import ast
import json
import sys
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
sys.path.insert(0, str(ROOT / 'scripts/common'))
SOURCE = Path(__file__).with_name('04_validate_cr_jsonld.py')


def validate(rows, extensions):
    nodes = [n for n in ast.parse(SOURCE.read_text(encoding='utf-8')).body
             if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in
             ('ValidationResult', 'validate_statistics', 'to_list')]
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        directory.joinpath('cover_sheets.json').write_text(json.dumps({'crpacks': [
            {'cr_pack_id': 'RP-999999'}] if rows else []}))
        directory.joinpath('cr_documents.json').write_text(json.dumps({
            'metadata': {'unique_crs': len(rows)}, 'cr_documents': rows}))
        ns = {'Path': Path, 'json': json, 'PARSED_DIR': directory,
              'log': types.SimpleNamespace(info=lambda *a, **kw: None)}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), 'exec'), ns)
        result = ns['ValidationResult']()
        packs = [{'@id': 'tdoc:crpack/RP-999999', 'tdoc:crPackId': 'RP-999999',
                  'hasCR': ['tdoc:'+r['tdoc_number'] for r in rows]}] if rows else []
        ns['validate_statistics'](result, packs, extensions, [], [])
        return result


def source():
    return {'tdoc_number': 'R1-9999999', 'cr_pack_id': 'RP-999999',
            'reason_for_change': None, 'summary_of_change': 'Synthetic summary'}


def extension():
    return {'@id': 'tdoc:R1-9999999', 'belongsToCRPack': 'tdoc:crpack/RP-999999',
            'tdoc:summaryOfChange': 'Synthetic summary'}


class SelectedCRValidation(unittest.TestCase):
    def test_one_selected_record_with_source_present_fields_passes(self):
        result = validate([source()], [extension()])
        self.assertEqual(result.failed, 0, result.details)

    def test_missing_selected_record_fails(self):
        self.assertGreater(validate([source()], []).failed, 0)

    def test_empty_input_fails(self):
        self.assertGreater(validate([], []).failed, 0)

    def test_wrong_identity_or_lost_field_fails(self):
        for update in ({'@id': 'tdoc:R1-8888888'}, {'tdoc:summaryOfChange': None}):
            with self.subTest(update=update):
                self.assertGreater(validate([source()], [{**extension(), **update}]).failed, 0)

    def test_consequences_are_preserved_when_present_and_optional_when_absent(self):
        row = {**source(), 'consequences_if_not_approved': 'Source consequence'}
        node = {**extension(), 'tdoc:consequencesIfNotApproved': 'Source consequence'}
        self.assertEqual(validate([row], [node]).failed, 0)
        for changed in (extension(), {**node, 'tdoc:consequencesIfNotApproved': 'Changed'}):
            self.assertGreater(validate([row], [changed]).failed, 0)

    def test_relationships_require_exact_inverses_and_single_pack_ownership(self):
        nodes = [n for n in ast.parse(SOURCE.read_text(encoding='utf-8')).body
                 if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in
                 ('ValidationResult', 'to_list', 'validate_relationships')]
        pid, other, cid, sid = 'tdoc:crpack/a', 'tdoc:crpack/b', 'tdoc:R1-9999999', 'tdoc:section/s'
        ns = dict(PHASE3_DIR=Path('synthetic/phase3'), PHASE1_DIR=Path('synthetic/phase1'),
                  PHASE4_DIR=Path('synthetic/phase4'), log=types.SimpleNamespace(info=lambda *a: None),
                  require_complete_section_index=lambda *a: None,
                  load_jsonld=lambda path: [{'@id': sid, 'sectionId': 's'}]
                      if path.name == 'sections.jsonld' else [])
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), 'exec'), ns)
        pack = {'@id': pid, 'hasCR': cid}
        cr = {'@id': cid, 'belongsToCRPack': pid, 'modifiesSection': sid}
        section = {'@id': sid, 'modifiedByCR': cid}

        def check(packs, crs, sections):
            result = ns['ValidationResult']()
            ns['validate_relationships'](result, packs, crs, sections)
            return result

        self.assertEqual(check([pack], [cr], [section]).failed, 0)

        self.assertEqual(check([pack], [], []).failed, 0)  # Cover-only CR.
        cases = [([pack], [{**cr, 'belongsToCRPack': None}], [section]),
                 ([{**pack, 'hasCR': []}], [cr], [section]),
                 ([pack, {'@id': other, 'hasCR': cid}], [cr], [section]),
                 ([pack, {'@id': other, 'hasCR': []}],
                  [{**cr, 'belongsToCRPack': [pid, other]}], [section]),
                 ([pack], [cr], []),
                 ([pack], [{**cr, 'modifiesSection': []}], [section]),
                 ([pack], [cr], [{**section, 'modifiedByCR': [cid, 'tdoc:unexpected']}])]
        for args in cases:
            with self.subTest(args=args):
                self.assertGreater(check(*args).failed, 0)
        self.assertEqual(check([pack], [cr], [section]).failed, 0)

    def test_actual_main_validates_local_rdf_mutations_and_retries(self):
        import importlib.util
        with patch.object(sys, 'path', [
                str(ROOT / 'scripts/tsg/RAN/formal/common'), *sys.path]):
            spec = importlib.util.spec_from_file_location('selected_cr_validator', SOURCE)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            import section_index_guard
            from ontology import jsonld_context
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            parsed, outputs = directory / 'parsed', directory / 'outputs'
            parsed.mkdir(); outputs.mkdir()
            phase1, phase3 = directory / 'phase1', directory / 'phase3'
            phase1.mkdir(); (phase3 / 'release-aware').mkdir(parents=True)
            pid, cid = 'tdoc:crpack/RP-999999', 'tdoc:R1-9999999'
            sid, spid = 'tdoc:section/38.201-Rel-19-1', 'tdoc:spec/38_300'
            row = {**source(), 'consequences_if_not_approved': 'Consequence'}
            (parsed / 'cover_sheets.json').write_text(json.dumps({'crpacks': [{'cr_pack_id': 'RP-999999'}]}))
            (parsed / 'cr_documents.json').write_text(json.dumps({'metadata': {'unique_crs': 1}, 'cr_documents': [row]}))
            summary = directory / 'summary.json'
            summary.write_text(json.dumps({'total': {'sections': 1}}))
            graphs = {'crpacks.jsonld': [{'@id': pid, '@type': 'CRPack',
                        'tdoc:crPackId': 'RP-999999', 'hasCR': cid}],
                      'cr_extensions.jsonld': [{**extension(), '@type': 'tdoc:CR',
                        'tdoc:consequencesIfNotApproved': 'Consequence',
                        'modifiesSection': sid, 'affectsCoreSpec': spid}],
                      'section_extensions.jsonld': [{'@id': sid, '@type': 'Section', 'modifiedByCR': cid}],
                      'spec_dynamic.jsonld': [{'@id': spid, '@type': 'tdoc:Spec', 'tdoc:specNumber': '38.300'}]}

            def save(path, graph):
                path.write_text(json.dumps(jsonld_context.canonical_document({'@graph': graph})))

            with patch.object(jsonld_context, 'company_reference_aliases', return_value={}):
                for name, graph in graphs.items(): save(outputs / name, graph)
                save(phase1 / 'specs.jsonld', [])
                save(phase3 / 'release-aware/sections.jsonld', [{'@id': sid, '@type': 'Section',
                    'sectionId': '38.201-Rel-19-1', 'sectionNumber': '1'}])
            originals = {p: p.read_bytes() for p in directory.rglob('*') if p.is_file()}
            with patch.multiple(module, PARSED_DIR=parsed, PHASE4_DIR=outputs,
                                PHASE1_DIR=phase1, PHASE3_DIR=phase3), \
                 patch.object(module, 'configure_logging'), \
                 patch.object(section_index_guard, 'summary_path', return_value=summary):
                for _ in range(2): self.assertEqual(module.main(), 0)
                changes = [('cr_extensions.jsonld', [{**graphs['cr_extensions.jsonld'][0], 'belongsToCRPack': None}]),
                           ('cr_extensions.jsonld', [{**graphs['cr_extensions.jsonld'][0],
                                                     'tdoc:consequencesIfNotApproved': 'Changed'}]),
                           ('spec_dynamic.jsonld', graphs['spec_dynamic.jsonld'] * 2),
                           ('section_extensions.jsonld', [{**graphs['section_extensions.jsonld'][0],
                                                          'modifiedByCR': 'tdoc:R1-8888888'}])]
                for name, graph in changes:
                    with self.subTest(name=name, graph=graph), \
                         patch.object(jsonld_context, 'company_reference_aliases', return_value={}):
                        path = outputs / name
                        save(path, graph)
                        self.assertEqual(module.main(), 1)
                        path.write_bytes(originals[path])
                        for _ in range(2): self.assertEqual(module.main(), 0)
            self.assertTrue(all(p.read_bytes() == data for p, data in originals.items()))



if __name__ == '__main__':
    unittest.main()
