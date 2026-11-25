"""Bind parsed repair plans to the exact bytes read, including concurrent edits."""
import hashlib
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from docx import Document

import ts_hierarchy_repair as hierarchy
import ts_structure_reconcile as structure
import publish_ts_source_context_plan as context_plan


class RepairPlanBinding(unittest.TestCase):
    def test_published_context_plan_pins_each_actual_parsed_input(self):
        values = {'shadow': {'errors': [], 'summary': {'completeParents': 0, 'parents': 0},
                             'sourceFences': {}, 'sourceShadowSHA256': {}, 'records': []},
                  'catalog': {'editions': []}, 'contexts': {'sourceFences': {}, 'tables': []}}
        fields = {'shadow': 'preparation', 'catalog': 'sourceCatalog', 'contexts': 'actualSourceContexts'}
        for name in values:
            with self.subTest(input=name), tempfile.TemporaryDirectory(prefix='spectra-context-binding-') as folder:
                root = Path(folder)
                paths = {key: root / (key + ('.json.gz' if key == name else '.json')) for key in values}
                catalog_raw = json.dumps(values['catalog']).encode()
                catalog_bytes = (gzip.compress(catalog_raw, mtime=0)
                                 if paths['catalog'].suffix == '.gz' else catalog_raw)
                catalog_pin = hashlib.sha256(catalog_bytes).hexdigest()
                values['shadow']['inputSHA256'] = {str(paths['catalog']): catalog_pin}
                values['contexts']['catalogSHA256'] = catalog_pin
                for key, path in paths.items():
                    raw = json.dumps(values[key]).encode()
                    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == '.gz' else raw)
                original = paths[name].read_bytes()
                decoded = gzip.decompress(original)
                real_loads = json.loads

                def parse_then_edit(raw, *args, **kwargs):
                    result = real_loads(raw, *args, **kwargs)
                    if raw == decoded or raw == decoded.decode():
                        paths[name].write_bytes(gzip.compress(json.dumps(dict(values[name], concurrent=True)).encode(), mtime=0))
                    return result

                output = root / 'published.json'
                with patch.object(json, 'loads', side_effect=parse_then_edit):
                    context_plan.publish(paths['shadow'], paths['catalog'], output, paths['contexts'])
                published = real_loads(output.read_text())
                pin = published[fields[name]]['sha256']
                self.assertEqual(pin, hashlib.sha256(original).hexdigest())
                self.assertNotEqual(pin, hashlib.sha256(paths[name].read_bytes()).hexdigest())

    def test_leaf_plan_pin_matches_the_bytes_parsed_before_a_concurrent_edit(self):
        root = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
        # The production resolver requires source paths under the project root.
        # Only this disposable fixture directory is written, never input/DB trees.
        with tempfile.TemporaryDirectory(prefix='.ts-repair-test-', dir=root) as directory:
            folder = Path(directory)
            source = folder / 'synthetic.docx'
            document = Document()
            document.add_paragraph('1.2\tSynthetic purpose')
            document.save(source)
            section = dict(sectionId='38.508-1-Rel-18-1.2', sectionNumber='1.2',
                           sectionTitle='Synthetic purpose', parentSectionId='38.508-1-Rel-18-1',
                           childSectionIds=[], isVoid=False, references=[], referencesSpec=[])
            previous = dict(sectionId='38.508-1-Rel-18-1.1', references=[], referencesSpec=[])
            parsed = folder / 'parsed.json'
            parsed.write_text(json.dumps({'sections': [section, previous], 'tables': []}))
            plan = folder / 'plan.json'
            value = {'repairs': [{'section': section, 'specNumber': '38.508-1', 'release': 'Rel-18',
                     'parsedPath': parsed.relative_to(root).as_posix(), 'previousSectionId': previous['sectionId'],
                     'previousAfter': previous, 'previousBefore': previous, 'tableMoves': [],
                     'sourcePath': source.relative_to(root).as_posix(),
                     'sourceSHA256': hashlib.sha256(source.read_bytes()).hexdigest(),
                     'paragraphIndex': 0, 'sourceQuote': '1.2\tSynthetic purpose'}],
                     'artifactPins': [{'path': parsed.relative_to(root).as_posix(),
                                       'sha256': hashlib.sha256(parsed.read_bytes()).hexdigest()}]}
            original = json.dumps(value).encode()
            changed = json.dumps(dict(value, concurrent='new plan bytes')).encode()
            plan.write_bytes(original)
            real_loads = json.loads

            def parse_then_edit(raw, *args, **kwargs):
                result = real_loads(raw, *args, **kwargs)
                if raw == original or raw == original.decode():
                    plan.write_bytes(changed)
                return result

            with patch.object(json, 'loads', side_effect=parse_then_edit):
                repairs, pins = structure._missing_section_inputs(plan)
            self.assertEqual(repairs, value['repairs'])
            self.assertEqual(pins[str(plan)], hashlib.sha256(original).hexdigest())
            self.assertNotEqual(pins[str(plan)], hashlib.sha256(plan.read_bytes()).hexdigest())

    def test_hierarchy_plan_pin_matches_the_bytes_parsed_before_a_concurrent_edit(self):
        with tempfile.TemporaryDirectory(prefix='spectra-hierarchy-binding-') as directory:
            root = Path(directory)
            parsed = root / 'synthetic/parsed_ts/synthetic.json'
            parsed.parent.mkdir(parents=True)
            parsed.write_text(json.dumps({'spec_number': '38.533', 'release': 'Rel-18',
                                         'sections': [], 'stats': {'sections': 0}}))
            source = root / 'synthetic_s16-s19.docx'
            Document().save(source)
            plan = root / 'plan.json'
            value = {'sourceFences': {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in (parsed, source)},
                     'updates': [], 'addedSections': [], 'removedSectionIds': [],
                     'sourceHeadingEvidence': []}
            original = json.dumps(value).encode()
            changed = json.dumps(dict(value, concurrent='new plan bytes')).encode()
            plan.write_bytes(original)
            real_loads = json.loads

            def parse_then_edit(raw, *args, **kwargs):
                result = real_loads(raw, *args, **kwargs)
                if raw == original or raw == original.decode():
                    plan.write_bytes(changed)
                return result

            with patch.object(json, 'loads', side_effect=parse_then_edit):
                review, pins, *_ = hierarchy.prepare(root, plan)
            self.assertEqual(review, value)
            self.assertEqual(pins[plan], hashlib.sha256(original).hexdigest())
            self.assertNotEqual(pins[plan], hashlib.sha256(plan.read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main()
