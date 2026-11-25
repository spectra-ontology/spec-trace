#!/usr/bin/env python3
"""Phase-1 synthetic source identity checks; no corpus, service or network access."""
import ast
from collections import Counter
import types
import time
import contextlib
import importlib.util
import io
import inspect
import json
import socket
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "scripts/common"))
SOURCE = ROOT / 'scripts/tsg/RAN/formal/RAN2/phase-1/jsonld'


def load_source(name):
    spec = importlib.util.spec_from_file_location('synthetic_ran2_' + name, SOURCE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    with patch.object(sys, 'path', [str(SOURCE), *sys.path]):
        spec.loader.exec_module(module)
    return module


def ls_instance(module, row, meeting, companies):
    args = [row, meeting, companies]
    if 'schema_type' in inspect.signature(module.create_ls_instance).parameters:
        args.append('31col')
    return module.create_ls_instance(*args)


class SourceIdentity(unittest.TestCase):
    def test_ran2_company_input_failure_preserves_catalogs_and_retry(self):
        with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
                patch.object(socket, 'create_connection', side_effect=AssertionError('network forbidden')), \
                patch.object(sys, 'path', sys.path.copy()), \
                tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            import pandas as pd
            with patch.dict(sys.modules):
                for name in ('tdoc_list_binding', 'submitter_roles'):
                    sys.modules.pop(name, None)
                module = load_source('01_company_normalization')
            module.INPUT_DIR = Path(tmp) / 'input'
            module.INPUT_DIR.mkdir()
            module.INTERMEDIATE_DIR = Path(tmp) / 'intermediate'
            module.RAN1_ALIASES_PATH = Path(tmp) / 'absent.json'
            workbook = module.INPUT_DIR / 'synthetic.xlsx'
            def write(values):
                pd.DataFrame(values).to_excel(workbook, index=False)
            def run():
                module.main(['--min-company-tdocs', '1'])
            write({'Source': ['Samsung Electronics', 'Huawei']})
            run()
            output = module.INTERMEDIATE_DIR / 'RAN2/phase-1'
            def snapshot():
                return {path.name: path.read_bytes() for path in output.iterdir()}
            before = snapshot()
            self.assertEqual(set(json.loads(before['company_aliases.json'])), {'Samsung', 'Huawei'})
            (module.INPUT_DIR / 'directory.xlsx').mkdir()
            for values in ({'Other': ['Synthetic']}, {'Source': [' ', None]},
                           {'Source': ['Moderator']}, {'Source': ['TBD']}):
                write(values)
                source = workbook.read_bytes()
                with self.subTest(values=values), self.assertRaises(ValueError):
                    run()
                self.assertEqual(snapshot(), before)
                self.assertEqual(workbook.read_bytes(), source)
                write({'Source': ['Samsung Electronics', 'Huawei']})
                source = workbook.read_bytes()
                run()
                self.assertEqual(snapshot(), before)
                self.assertEqual(workbook.read_bytes(), source)
            duplicate = pd.DataFrame([['Samsung', 'Huawei']], columns=['Source', 'Source'])
            with patch.object(module.pd, 'read_excel', return_value=duplicate), self.assertRaises(ValueError):
                run()
            self.assertEqual(snapshot(), before)
            write({'Source': ['Samsung Electronics', 'Huawei']})
            pd.DataFrame({'Other': ['Synthetic']}).to_excel(module.INPUT_DIR / 'second.xlsx', index=False)
            with self.assertRaises(ValueError):
                run()
            self.assertEqual(snapshot(), before)
            (module.INPUT_DIR / 'second.xlsx').unlink()
            run()
            self.assertEqual(snapshot(), before)
            workbook.unlink()
            with self.assertRaises(SystemExit):
                run()
            self.assertEqual(snapshot(), before)

    def test_ran2_builds_aliases_without_ran1_artifacts(self):
        module = load_source('01_company_normalization')
        with tempfile.TemporaryDirectory() as tmp:
            module.RAN1_ALIASES_PATH = Path(tmp) / 'missing.json'
            with contextlib.redirect_stdout(io.StringIO()):
                base = module.load_ran1_aliases()
            self.assertEqual(base, {})
            self.assertEqual(module.find_canonical_name('Samsung Electronics', base), 'Samsung')
            self.assertEqual(module.find_canonical_name('Synthetic Company', base), 'Synthetic Company')
            module.RAN1_ALIASES_PATH.write_text(json.dumps({'Synthetic Parent': {'aliases': ['Synthetic Subsidiary']}}))
            with contextlib.redirect_stdout(io.StringIO()):
                base = module.load_ran1_aliases()
            self.assertEqual(module.find_canonical_name('Synthetic Subsidiary', base), 'Synthetic Parent')

    def test_raw_entity_identities_keep_distinct_nodes_and_exact_edges(self):
        import pandas as pd
        reference = load_source('02_reference_classes')
        instance = load_source('03_tdoc_instances')
        normalization = load_source('01_company_normalization')
        names = ('Synthetic A B', 'Synthetic A_B', 'Synthetic A/B', 'Synthetic A%2FB', '삼성전자')
        catalog = {name: {'aliases': [name]} for name in names}
        with tempfile.TemporaryDirectory() as tmp:
            aliases = Path(tmp) / 'aliases.json'
            aliases.write_text(json.dumps(catalog))
            companies = reference.generate_companies(aliases)
            from ontology import jsonld_context
            alias_map = jsonld_context._company_aliases(str(aliases), aliases.stat().st_mtime_ns)
            self.assertEqual(normalization.merge_uri_colliding_canonicals(catalog, {}), catalog)
            frame = pd.DataFrame([{'Contact': 'Synthetic', 'Contact ID': name,
                                   'Related WIs': name, 'To': name} for name in names])
            contacts = reference.generate_contacts([frame])
            workitems = reference.generate_work_items([frame])
            groups = {node['tdoc:wgName']: node
                      for node in reference.generate_working_groups([frame]).values()}
            for nodes in (companies, contacts, workitems, groups):
                self.assertEqual(len(reference.merge_by_identity(nodes, 'Synthetic')), len(names))
                self.assertEqual(len({node['@id'] for node in nodes.values()}), len(names))
            for i, name in enumerate(names):
                row = pd.Series({'TDoc': f'R2-999{i}', 'Source': name, 'Contact ID': name,
                                 'Related WIs': name, 'To': name})
                node = ls_instance(instance, row, 'RAN2#999', {name.lower(): name})
                self.assertEqual(node['submittedBy'], [companies[name]['@id']])
                self.assertEqual(node['hasContact'], contacts[name]['@id'])
                self.assertEqual(node['relatedTo'], [workitems[name]['@id']])
                self.assertEqual(node['sentTo'], [groups[name]['@id']])
                with patch.object(jsonld_context, 'company_reference_aliases', return_value=alias_map):
                    document = instance.canonical_document({'@graph': [node]}, wg='RAN2')
                    self.assertEqual(document['@graph'][0]['hasContact'], contacts[name]['@id'])
                    self.assertEqual(document['@graph'][0]['submittedBy'], [companies[name]['@id']])
                    self.assertEqual(instance.canonical_document(document, wg='RAN2'), document)
            placeholders = reference.generate_work_items([pd.DataFrame({'Related WIs': ['?', '삼성전자']})])
            with contextlib.redirect_stdout(io.StringIO()):
                kept = reference.drop_placeholder_nodes(placeholders, 'WorkItem')
            self.assertEqual(set(kept), {'삼성전자'})
            refs = [{'relatedTo': [placeholders['?']['@id'], placeholders['삼성전자']['@id']]}]
            with contextlib.redirect_stdout(io.StringIO()):
                instance.drop_placeholder_references(refs)
            self.assertEqual(refs[0]['relatedTo'], [placeholders['삼성전자']['@id']])

    def test_tiny_company_catalog_uses_explicit_minimum(self):
        module = load_source('01_company_normalization')
        reference = load_source('02_reference_classes')
        instance = load_source('03_tdoc_instances')
        import pandas as pd
        catalog = {'Synthetic Tiny': {'aliases': ['Synthetic Tiny']}}
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            module.INTERMEDIATE_DIR = Path(tmp)
            self.assertEqual(module.save_results(catalog, Counter({'Synthetic Tiny': 1})), {})
            self.assertEqual(module.save_results(catalog, Counter({'Synthetic Tiny': 1}), 1), catalog)
            # WG-local writers keep their own directory name when this shared test is reused.
            aliases = next(Path(tmp).glob('*/phase-1/company_aliases_significant.json'))
            companies = reference.generate_companies(aliases)
            node = ls_instance(instance, pd.Series({'TDoc': 'R2-99999', 'Source': 'Synthetic Tiny'}),
                                               'RAN2#999', {'synthetic tiny': 'Synthetic Tiny'})
            self.assertEqual(node['submittedBy'], [companies['Synthetic Tiny']['@id']])
            for value in (0, -1, True, 1.5, '1.5', 'bad'):
                with self.subTest(value=value), self.assertRaises(module.argparse.ArgumentTypeError):
                    module.positive_company_count(value)

    def test_empty_company_preflight_precedes_database_writes(self):
        path = SOURCE.parent / 'neo4j/01_load_kg.py'
        main = next(node for node in ast.parse(path.read_text()).body
                    if isinstance(node, ast.FunctionDef) and node.name == 'main')
        driver = types.SimpleNamespace(close=lambda: None)
        writes = []
        def rejected(_driver):
            raise RuntimeError('synthetic empty company catalog')
        revision = types.ModuleType('tdoc_revision_evidence')
        revision.preflight_revision_document = lambda *args: {}
        revision.load_evidence = lambda *args: None
        env = dict(__file__=str(path), Path=Path, sys=sys, time=time, URI='synthetic', AUTH=None,
                   GraphDatabase=types.SimpleNamespace(driver=lambda *a, **kw: driver),
                   current_company_ids=rejected, run_query=lambda *a, **kw: writes.append(a))
        with patch.dict(sys.modules, {'tdoc_revision_evidence': revision}), \
                contextlib.redirect_stdout(io.StringIO()), patch.object(sys, 'path', sys.path.copy()):
            exec(compile(ast.Module(body=[main], type_ignores=[]), str(path), 'exec'), env)
            with self.assertRaisesRegex(RuntimeError, 'synthetic empty'):
                env['main']()
        self.assertEqual(writes, [])

    def test_apply_cli_requires_explicit_prune_mode(self):
        path = SOURCE.parent / 'neo4j/01_load_kg.py'
        entry = next(node for node in ast.parse(path.read_text()).body
                     if isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                     and isinstance(node.test.left, ast.Name) and node.test.left.id == '__name__')
        for flags in (['--apply'], ['--apply', '--dry-run', '--prune-orphan-companies']):
            with self.subTest(flags=flags), patch.object(sys, 'argv', [str(path), *flags]), \
                    contextlib.redirect_stderr(io.StringIO()):
                env = {'__name__': '__main__', 'sys': sys,
                       'main': lambda: self.fail('invalid flags started full load')}
                with self.assertRaises(SystemExit) as exc:
                    exec(compile(ast.Module(body=[entry], type_ignores=[]), str(path), 'exec'), env)
                self.assertEqual(exc.exception.code, 2)

    def test_role_wrappers_retain_unicode_companies(self):
        module = load_source('submitter_roles')
        for company in ('삼성전자', 'Établissement', '株式会社'):
            for value in (f'Moderator ({company})', f'{company} (Rapporteur)'):
                with self.subTest(value=value):
                    self.assertEqual(module.unwrap_roles(value), [company])
        for value in ('Moderator', 'RAN1 Chair', 'Vice-Chair'):
            self.assertEqual(module.unwrap_roles(value), [])


class Ran1CompanyPublication(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        for target, attribute in ((socket.socket, 'connect'), (socket, 'create_connection')):
            self.stack.enter_context(patch.object(
                target, attribute, side_effect=AssertionError('network forbidden')))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        import pandas as pd
        self.pd = pd
        wg = getattr(self, 'WG', 'RAN1')
        source = ROOT / 'scripts/tsg/RAN/formal' / wg / 'phase-1/jsonld'
        spec = importlib.util.spec_from_file_location('synthetic_ran1_company',
                                                    source / '01_company_normalization.py')
        self.module = importlib.util.module_from_spec(spec)
        self.atomic_io = importlib.import_module("common.atomic_io")
        with patch.object(sys, 'path', sys.path.copy()), patch.dict(sys.modules), \
                patch.object(Path, 'mkdir') as mkdir:
            for name in ('tdoc_list_binding', 'submitter_roles'):
                sys.modules.pop(name, None)
            spec.loader.exec_module(self.module)
            self.assertEqual(mkdir.call_count, 0, 'import must not create output directories')
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.module.INPUT_DIR = self.root / 'input'
        self.module.INPUT_DIR.mkdir()
        self.module.INTERMEDIATE_DIR = self.root / 'intermediate'
        self.out = self.module.INTERMEDIATE_DIR / f'{wg}/phase-1'
        if hasattr(self.module, 'RAN1_ALIASES_PATH'):
            self.module.RAN1_ALIASES_PATH = self.root / 'absent_base.json'
        self.xlsx = self.module.INPUT_DIR / 'synthetic.xlsx'
        self.write_input({'Source': ['Samsung Electronics', 'Huawei']})
        self.module.main(['--min-company-tdocs', '1'])
        self.before = self.snapshot()

    def write_input(self, values):
        frame = self.pd.DataFrame(values)
        # These WG readers explicitly skip workbooks with fewer than ten columns.
        # Preserve that source policy while exercising nonempty catalog publication.
        if getattr(self, 'WG', 'RAN1') in {'RAN3', 'RAN4', 'RAN5'}:
            for index in range(9):
                frame[f'Synthetic {index}'] = ''
        frame.to_excel(self.xlsx, index=False)

    def snapshot(self):
        return {path.name: path.read_bytes() for path in self.out.iterdir() if path.is_file()}

    def prior_catalogs(self):
        prior = {name: json.dumps({'previous_catalog': name}).encode()
                 for name in self.before}
        for name, content in prior.items():
            (self.out / name).write_bytes(content)
        return prior

    def assert_preserved(self, expected=None):
        self.assertEqual(self.snapshot(), self.before if expected is None else expected)
        self.assertEqual(list(self.out.glob('.json-set-*')), [])

    def retry(self):
        source_bytes = self.xlsx.read_bytes()
        self.module.main(['--min-company-tdocs', '1'])
        self.assert_preserved()
        self.assertEqual(self.xlsx.read_bytes(), source_bytes)

    def test_actual_xlsx_preflight_normal_and_repeat(self):
        aliases = json.loads(self.before['company_aliases.json'])
        self.assertEqual(set(aliases), {'Samsung', 'Huawei'})
        self.assertEqual(json.loads(self.before['company_aliases_significant.json']), aliases)
        (self.module.INPUT_DIR / 'directory.xlsx').mkdir()
        self.retry()
        for values in ({'Other': ['Synthetic']}, {'Source': [' ', None]}, {'Source': ['TBD']}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.write_input(values)
                self.module.main([])
            self.assert_preserved()
        self.write_input({'Source': ['Samsung Electronics', 'Huawei']})
        self.retry()
        self.module.main([])
        self.assertEqual(json.loads((self.out / 'company_aliases_significant.json').read_text()), {})
        self.retry()

    def test_current_input_resets_unknown_canonical_spelling(self):
        self.module.build_company_aliases(['Synthetic Company'], {})
        actual = self.module.build_company_aliases(['SYNTHETIC COMPANY'], {})
        self.assertEqual(actual, {'SYNTHETIC COMPANY': {'aliases': ['SYNTHETIC COMPANY']}})
        for canonical, aliases in self.module.KNOWN_ALIASES.items():
            for alias in aliases:
                with self.subTest(alias=alias):
                    self.assertEqual(self.module.find_canonical_name(alias), canonical)

    def test_missing_input_and_unsafe_outputs_precede_publication(self):
        self.xlsx.unlink()
        with self.assertRaises(SystemExit):
            self.module.main([])
        self.assert_preserved()
        self.write_input({'Source': ['Samsung Electronics', 'Huawei']})
        self.retry()
        target = self.out / 'company_aliases.json'
        outside = self.root / 'user.json'
        outside.write_bytes(self.before[target.name])
        target.unlink()
        target.symlink_to(outside)
        with self.assertRaises(ValueError):
            self.module.main(['--min-company-tdocs', '1'])
        self.assertTrue(target.is_symlink())
        self.assertEqual(outside.read_bytes(), self.before[target.name])
        self.assertEqual(list(self.out.glob('.json-set-*')), [])
        target.unlink()
        target.write_bytes(self.before[target.name])
        with self.assertRaises(ValueError):
            self.module.publish_catalogs([(target, {'invalid': float('nan')})])
        for results in ([], [(target, {}), (target, {})],
                        [(target, {}), (self.root / 'other/output.json', {})]):
            with self.subTest(results=results), self.assertRaises(ValueError):
                self.module.publish_catalogs(results)
        self.assertFalse((self.root / 'other').exists())
        self.assert_preserved()
        self.retry()

    def test_staging_and_backup_failures_preserve_all_three_and_retry(self):
        for name in ('fsync', 'link'):
            for error in (OSError, KeyboardInterrupt):
                with self.subTest(operation=name, error=error.__name__):
                    prior = self.prior_catalogs()
                    with patch.object(self.atomic_io.os, name, side_effect=error('synthetic')):
                        with self.assertRaises(error):
                            self.module.main(['--min-company-tdocs', '1'])
                    self.assert_preserved(prior)
                    self.retry()

    def test_each_publish_failure_or_interrupt_rolls_back_and_retries(self):
        replace = self.atomic_io.os.replace
        for index in (1, 2, 3):
            for error in (OSError, KeyboardInterrupt):
                for after_replace in (False, True):
                    with self.subTest(index=index, error=error.__name__, after=after_replace):
                        prior = self.prior_catalogs()
                        seen = 0
                        def interrupted(source, destination):
                            nonlocal seen
                            publishing = Path(source).parent.name == 'new'
                            if publishing:
                                seen += 1
                            if publishing and seen == index:
                                if after_replace:
                                    replace(source, destination)
                                raise error('synthetic publication')
                            return replace(source, destination)
                        with patch.object(self.atomic_io.os, 'replace', side_effect=interrupted):
                            with self.assertRaises(error):
                                self.module.main(['--min-company-tdocs', '1'])
                        self.assert_preserved(prior)
                        self.retry()

    def test_fresh_output_failure_removes_partial_publication(self):
        replace = self.atomic_io.os.replace
        for error in (OSError, KeyboardInterrupt):
            with self.subTest(error=error.__name__):
                for path in self.out.iterdir():
                    path.unlink()
                seen = 0
                def interrupted(source, destination):
                    nonlocal seen
                    if Path(source).parent.name == 'new':
                        seen += 1
                        if seen == 2:
                            raise error('synthetic fresh publication')
                    return replace(source, destination)
                with patch.object(self.atomic_io.os, 'replace', side_effect=interrupted):
                    with self.assertRaises(error):
                        self.module.main(['--min-company-tdocs', '1'])
                self.assertEqual(list(self.out.iterdir()), [])
                self.retry()

    def test_restore_failure_retains_preimage_and_diagnoses_recovery_path(self):
        prior = self.prior_catalogs()
        replace = self.atomic_io.os.replace
        def interrupted(source, destination):
            source = Path(source)
            if source.parent.name == 'new' and source.name == 'company_aliases_significant.json':
                raise OSError('synthetic publication')
            if source.parent.name == 'previous' and source.name == 'company_aliases.json':
                raise OSError('synthetic rollback')
            return replace(source, destination)
        with patch.object(self.atomic_io.os, 'replace', side_effect=interrupted):
            with self.assertRaisesRegex(RuntimeError, '복구 파일 보존') as caught:
                self.module.main(['--min-company-tdocs', '1'])
        recovery, = self.out.glob('.json-set-*')
        self.assertIn(str(recovery), str(caught.exception))
        backup = recovery / 'previous/company_aliases.json'
        self.assertEqual(backup.read_bytes(), prior['company_aliases.json'])
        self.assertEqual(self.xlsx.read_bytes()[:2], b'PK')
        # 보존된 preimage를 복구한 뒤 현재 입력으로 다시 실행한다.
        replace(backup, self.out / backup.name)
        import shutil
        shutil.rmtree(recovery)
        self.retry()


class Ran3CompanyPublication(unittest.TestCase):
    WG = 'RAN3'
    setUp = Ran1CompanyPublication.setUp
    write_input = Ran1CompanyPublication.write_input
    snapshot = Ran1CompanyPublication.snapshot
    prior_catalogs = Ran1CompanyPublication.prior_catalogs
    assert_preserved = Ran1CompanyPublication.assert_preserved
    retry = Ran1CompanyPublication.retry
    test_staging_and_backup_failures_preserve_all_three_and_retry = Ran1CompanyPublication.test_staging_and_backup_failures_preserve_all_three_and_retry
    test_each_publish_failure_or_interrupt_rolls_back_and_retries = Ran1CompanyPublication.test_each_publish_failure_or_interrupt_rolls_back_and_retries
    test_fresh_output_failure_removes_partial_publication = Ran1CompanyPublication.test_fresh_output_failure_removes_partial_publication
    test_restore_failure_retains_preimage_and_diagnoses_recovery_path = Ran1CompanyPublication.test_restore_failure_retains_preimage_and_diagnoses_recovery_path


class Ran2CompanyPublication(Ran3CompanyPublication):
    WG = 'RAN2'

    def test_normal_publication_preserves_three_schemas_bytes_and_threshold_return(self):
        self.assertEqual(set(self.before), {
            'company_aliases.json', 'company_aliases_significant.json', 'company_raw.json'})
        aliases = json.loads(self.before['company_aliases.json'])
        self.assertEqual(set(aliases), {'Samsung', 'Huawei'})
        for content in self.before.values():
            self.assertEqual(content, json.dumps(
                json.loads(content), ensure_ascii=False, indent=2).encode('utf-8'))
        counts = Counter({'Samsung Electronics': 1, 'Huawei': 1})
        selected = self.module.save_results(aliases, counts, min_company_tdocs=2)
        self.assertEqual(selected, {})
        self.assertEqual((self.out / 'company_aliases.json').read_bytes(),
                         self.before['company_aliases.json'])
        self.assertEqual((self.out / 'company_aliases_significant.json').read_bytes(), b'{}')
        self.assertEqual(json.loads((self.out / 'company_raw.json').read_text()), {
            'total_unique': 2, 'by_frequency': [
                {'name': 'Samsung Electronics', 'count': 1}, {'name': 'Huawei', 'count': 1}]})
        self.assertEqual(list(self.out.glob('.json-set-*')), [])
        self.retry()

    def test_serialization_failure_or_interrupt_preserves_all_three_and_retries(self):
        aliases = json.loads(self.before['company_aliases.json'])
        counts = Counter({'Samsung Electronics': 1, 'Huawei': 1})
        dumps = self.atomic_io.json.dumps
        for index in (1, 2, 3):
            for error in (TypeError, KeyboardInterrupt):
                with self.subTest(index=index, error=error.__name__):
                    prior = self.prior_catalogs()
                    seen = 0

                    def interrupted(value, *args, **kwargs):
                        nonlocal seen
                        seen += 1
                        if seen == index:
                            raise error('synthetic serialization')
                        return dumps(value, *args, **kwargs)

                    with patch.object(self.atomic_io.json, 'dumps', side_effect=interrupted):
                        with self.assertRaises(error):
                            self.module.save_results(aliases, counts, min_company_tdocs=1)
                    self.assertEqual(seen, index)
                    self.assert_preserved(prior)
                    self.retry()

        # A raw frequency name can fail in the third payload after the first two
        # have serialized. None of the existing catalogs may be replaced yet.
        prior = self.prior_catalogs()
        with self.assertRaises(TypeError):
            self.module.save_results(
                {'Synthetic Company': {'aliases': ['Synthetic Company']}},
                Counter({'Synthetic Company': 1, object(): 1}), min_company_tdocs=1)
        self.assert_preserved(prior)
        self.retry()

    def test_each_staging_write_failure_or_interrupt_preserves_all_three_and_retries(self):
        write = self.atomic_io.write_text_atomic
        for index in (1, 2, 3):
            for error in (OSError, KeyboardInterrupt):
                with self.subTest(index=index, error=error.__name__):
                    prior = self.prior_catalogs()
                    seen = 0

                    def interrupted(path, text, **kwargs):
                        nonlocal seen
                        if Path(path).parent.name == 'new':
                            seen += 1
                            if seen == index:
                                Path(path).write_bytes(b'partial synthetic staging write')
                                raise error('synthetic staging write')
                        return write(path, text, **kwargs)

                    with patch.object(self.atomic_io, 'write_text_atomic', side_effect=interrupted):
                        with self.assertRaises(error):
                            self.module.main(['--min-company-tdocs', '1'])
                    self.assertEqual(seen, index)
                    self.assert_preserved(prior)
                    self.retry()


class Ran4CompanyPublication(Ran2CompanyPublication):
    WG = 'RAN4'


class Ran5CompanyPublication(Ran2CompanyPublication):
    WG = 'RAN5'


class Ran1ReferencePublication(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        for target, attribute in ((socket.socket, 'connect'), (socket, 'create_connection')):
            self.stack.enter_context(patch.object(
                target, attribute, side_effect=AssertionError('network forbidden')))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.stack.enter_context(patch.object(sys, 'path', sys.path.copy()))
        self.stack.enter_context(patch.dict(sys.modules))
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        wg = getattr(self, 'WG', 'RAN1')
        source = ROOT / 'scripts/tsg/RAN/formal' / wg / 'phase-1/jsonld'
        sys.path.insert(0, str(ROOT / 'scripts/tsg/RAN/formal/common'))
        for name in ('tdoc_list_binding', 'submitter_roles', 'meeting_id', 'date_swap'):
            sys.modules.pop(name, None)
        def load(name):
            spec = importlib.util.spec_from_file_location('synthetic_reference_' + name,
                                                        source / (name + '.py'))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        normalizer = load('01_company_normalization')
        self.module = load('02_reference_classes')
        self.atomic_io = importlib.import_module('common.atomic_io')
        self.module.PROJECT_ROOT = self.root
        self.module.INPUT_DIR = self.root / 'input'
        self.module.INPUT_DIR.mkdir()
        self.module.INTERMEDIATE_DIR = self.root / 'intermediate'
        self.module.OUTPUT_DIR = self.root / 'output'
        self.module.SPEC_TITLES_FILE = self.root / 'spec_titles.json'
        self.module.SPEC_TITLES_FILE.write_text(json.dumps({'specs': {'38.331': 'Synthetic title'}}))
        import pandas as pd
        prefix = wg.replace('RAN', 'R')
        self.xlsx = self.module.INPUT_DIR / f'TDoc_List_TSG{prefix}_999.xlsx'
        pd.DataFrame([{'TDoc': f'{prefix}-999999', 'Source': 'Synthetic Company',
                       'Release': 'Rel-19', 'Contact': 'Synthetic Contact', 'Contact ID': '999',
                       'Related WIs': 'Synthetic WI', 'Agenda item': '8.1',
                       'Agenda item description': 'Synthetic agenda', 'Spec': '38.331',
                       'To': wg, 'Cc': 'SA2'}]).to_excel(self.xlsx, index=False)
        normalizer.INPUT_DIR = self.module.INPUT_DIR
        normalizer.INTERMEDIATE_DIR = self.module.INTERMEDIATE_DIR
        if hasattr(normalizer, 'RAN1_ALIASES_PATH'):
            normalizer.RAN1_ALIASES_PATH = self.root / 'absent_base.json'
        normalizer.main(['--min-company-tdocs', '1'])
        self.alias_path = (normalizer.INTERMEDIATE_DIR /
                           f'{wg}/phase-1/company_aliases_significant.json')
        self.alias_bytes = self.alias_path.read_bytes()
        from ontology import jsonld_context
        # 실제 canonical_document의 catalog 조회도 이 합성 생산물에만 연결한다.
        aliases = jsonld_context._company_aliases(str(self.alias_path), self.alias_path.stat().st_mtime_ns)
        self.stack.enter_context(patch.object(jsonld_context, 'company_reference_aliases', return_value=aliases))
        self.module.main()
        for path in self.module.OUTPUT_DIR.iterdir():
            path.chmod(0o640)
        self.before = self.snapshot()
        self.source_bytes = self.xlsx.read_bytes()

    def snapshot(self):
        return {path.name: path.read_bytes() for path in self.module.OUTPUT_DIR.iterdir()
                if path.is_file()}

    def prior_outputs(self):
        prior = {name: json.dumps({'previous_reference': name}).encode()
                 for name in self.before}
        for name, data in prior.items():
            (self.module.OUTPUT_DIR / name).write_bytes(data)
        return prior

    def preserved(self, expected):
        self.assertEqual(self.snapshot(), expected)
        self.assertEqual([p.name for p in self.module.OUTPUT_DIR.iterdir()
                          if p.name.startswith('.')], [])
        for name in expected:
            self.assertEqual((self.module.OUTPUT_DIR / name).stat().st_mode & 0o777, 0o640)
        self.assertEqual(self.xlsx.read_bytes(), self.source_bytes)

    def retry(self):
        self.module.main()
        self.preserved(self.before)
        self.assertEqual(self.alias_path.read_bytes(), self.alias_bytes)

    def test_actual_xlsx_catalog_producer_to_eight_reference_documents_and_repeat(self):
        counts = {'meetings': 1, 'releases': 1, 'companies': 1, 'contacts': 1,
                  'work_items': 1, 'agenda_items': 1, 'specs': 1, 'working_groups': 2}
        self.assertEqual(set(self.before), {name + '.jsonld' for name in counts})
        for name, count in counts.items():
            document = json.loads(self.before[name + '.jsonld'])
            self.assertEqual(len(document['@graph']), count)
        company, = json.loads(self.before['companies.jsonld'])['@graph']
        self.assertEqual(company['tdoc:companyName'], 'Synthetic Company')
        self.assertEqual(company['@id'], 'tdoc:company/Synthetic%20Company')
        self.retry()

    def test_invalid_catalog_and_late_dependency_failures_preserve_all_outputs(self):
        for value in ([], {}, {'Synthetic': []}, {'Synthetic': {'aliases': [None]}}):
            prior = self.prior_outputs()
            self.alias_path.write_text(json.dumps(value))
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.module.main()
            self.preserved(prior)
            self.alias_path.write_bytes(self.alias_bytes)
            self.retry()
        self.late_dependency_failures()

    def late_dependency_failures(self):
        """실제 늦은 입력 조회와 일곱 번째 문서 준비 실패를 검사한다."""
        prior = self.prior_outputs()
        titles = self.module.SPEC_TITLES_FILE.read_bytes()
        self.module.SPEC_TITLES_FILE.unlink()
        with self.assertRaises(SystemExit):
            self.module.main()
        self.preserved(prior)
        self.module.SPEC_TITLES_FILE.write_bytes(titles)
        self.retry()
        prior = self.prior_outputs()
        canonical = self.module.canonical_document
        seen = 0
        def failed(document, **kwargs):
            nonlocal seen
            seen += 1
            if seen == 7:
                raise ValueError('synthetic late canonicalization')
            return canonical(document, **kwargs)
        with patch.object(self.module, 'canonical_document', side_effect=failed):
            with self.assertRaisesRegex(ValueError, 'late canonicalization'):
                self.module.main()
        self.preserved(prior)
        self.retry()

    def test_staging_serialization_write_fsync_failure_preserves_eight_and_retries(self):
        dumps = self.atomic_io.json.dumps
        write = self.atomic_io.write_text_atomic
        fsync = self.atomic_io.os.fsync
        for boundary in ('serialize', 'write', 'fsync'):
            for index in (1, 8):
                errors = (TypeError, KeyboardInterrupt) if boundary == 'serialize' else (OSError, KeyboardInterrupt)
                for error in errors:
                    with self.subTest(boundary=boundary, index=index, error=error.__name__):
                        prior = self.prior_outputs()
                        seen = 0

                        def failed_dumps(value, *args, **kwargs):
                            nonlocal seen
                            if kwargs.get('allow_nan') is False:
                                seen += 1
                                if seen == index:
                                    raise error('synthetic reference serialization')
                            return dumps(value, *args, **kwargs)

                        def failed_write(path, text, **kwargs):
                            nonlocal seen
                            if Path(path).parent.name == 'new':
                                seen += 1
                                if seen == index:
                                    Path(path).write_bytes(b'partial synthetic reference')
                                    raise error('synthetic reference write')
                            return write(path, text, **kwargs)

                        def failed_fsync(fd):
                            nonlocal seen
                            seen += 1
                            if seen == index:
                                raise error('synthetic reference fsync')
                            return fsync(fd)

                        owner, attribute, replacement = {
                            'serialize': (self.atomic_io.json, 'dumps', failed_dumps),
                            'write': (self.atomic_io, 'write_text_atomic', failed_write),
                            'fsync': (self.atomic_io.os, 'fsync', failed_fsync),
                        }[boundary]
                        with patch.object(owner, attribute, side_effect=replacement):
                            with self.assertRaises(error):
                                self.module.main()
                        self.assertEqual(seen, index)
                        self.preserved(prior)
                        self.retry()

    def test_eight_output_publish_errors_interrupts_and_retry(self):
        replace = self.atomic_io.os.replace
        for index in range(1, 9):
            for error in (OSError, KeyboardInterrupt):
                for after_replace in (False, True):
                    with self.subTest(index=index, error=error.__name__, after=after_replace):
                        prior = self.prior_outputs()
                        seen = 0
                        def failed(source, destination):
                            nonlocal seen
                            publishing = Path(source).parent.name == 'new'
                            if publishing:
                                seen += 1
                            if publishing and seen == index:
                                if after_replace:
                                    replace(source, destination)
                                raise error('synthetic reference publication')
                            return replace(source, destination)
                        with patch.object(self.atomic_io.os, 'replace', side_effect=failed):
                            with self.assertRaises(error):
                                self.module.main()
                        self.preserved(prior)
                        self.retry()

    def test_single_class_write_preserves_old_bytes_on_fsync_and_retry(self):
        path = self.module.OUTPUT_DIR / 'meetings.jsonld'
        data = self.module.generate_meetings([self.xlsx])
        for error in (OSError, KeyboardInterrupt):
            prior = self.prior_outputs()
            with patch.object(self.atomic_io.os, 'fsync', side_effect=error('synthetic')):
                with self.assertRaises(error):
                    self.module.save_jsonld(data, path, 'Meeting')
            self.preserved(prior)
            self.retry()


class Ran2ReferencePublication(Ran1ReferencePublication):
    """동일한 실제 입력·게시 계약을 RAN2 생성 코드에도 적용한다."""
    WG = 'RAN2'


class Ran3ReferencePublication(Ran1ReferencePublication):
    WG = 'RAN3'


class Ran4ReferencePublication(unittest.TestCase):
    """RAN4의 생성 정책을 유지하며 동일한 실제 게시·복원 경계를 검사한다."""
    WG = 'RAN4'
    setUp = Ran1ReferencePublication.setUp
    snapshot = Ran1ReferencePublication.snapshot
    prior_outputs = Ran1ReferencePublication.prior_outputs
    preserved = Ran1ReferencePublication.preserved
    retry = Ran1ReferencePublication.retry
    late_dependency_failures = Ran1ReferencePublication.late_dependency_failures
    test_actual_xlsx_catalog_producer_to_eight_reference_documents_and_repeat = Ran1ReferencePublication.test_actual_xlsx_catalog_producer_to_eight_reference_documents_and_repeat
    test_late_dependency_failures_preserve_all_outputs = Ran1ReferencePublication.late_dependency_failures
    test_staging_serialization_write_fsync_failure_preserves_eight_and_retries = Ran1ReferencePublication.test_staging_serialization_write_fsync_failure_preserves_eight_and_retries
    test_eight_output_publish_errors_interrupts_and_retry = Ran1ReferencePublication.test_eight_output_publish_errors_interrupts_and_retry
    test_single_class_write_preserves_old_bytes_on_fsync_and_retry = Ran1ReferencePublication.test_single_class_write_preserves_old_bytes_on_fsync_and_retry


class Ran5ReferencePublication(Ran4ReferencePublication):
    WG = 'RAN5'


class Ran1TdocPublication(unittest.TestCase):
    def setUp(self):
        # XLSX → 회사 catalog → 여덟 참조 문서도 실제 생성 코드로 준비합니다.
        Ran1ReferencePublication.setUp(self)
        self.reference = self.module
        wg = getattr(self, 'WG', 'RAN1')
        source = ROOT / 'scripts/tsg/RAN/formal' / wg / 'phase-1/jsonld/03_tdoc_instances.py'
        spec = importlib.util.spec_from_file_location('synthetic_ran1_tdocs', source)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        for name in ('PROJECT_ROOT', 'INPUT_DIR', 'INTERMEDIATE_DIR', 'OUTPUT_DIR'):
            setattr(self.module, name, getattr(self.reference, name))
        self.evidence = self.module.OUTPUT_DIR / 'revision_source_assertions.jsonld'
        self.evidence.write_text('{"previous_revision": true}')
        self.module.main()
        for path in self.module.OUTPUT_DIR.iterdir():
            path.chmod(0o640)
        self.before = self.snapshot()

    snapshot = Ran1ReferencePublication.snapshot

    def preserved(self, expected):
        self.assertEqual(self.snapshot(), expected)
        self.assertEqual([p.name for p in self.module.OUTPUT_DIR.iterdir() if p.name.startswith('.')], [])
        for name in expected:
            self.assertEqual((self.module.OUTPUT_DIR / name).stat().st_mode & 0o777, 0o640)
        self.assertEqual(self.xlsx.read_bytes(), self.source_bytes)
        self.assertEqual(self.alias_path.read_bytes(), self.alias_bytes)

    def prior_outputs(self):
        self.evidence.write_text('{"previous_revision": true}')
        (self.module.OUTPUT_DIR / 'tdocs.jsonld').write_text('{"previous_tdocs": true}')
        for name in ('duplicate_input_merge.txt', 'swapped_date_columns.txt',
                     'skipped_non_tdoc_files.txt', 'contact_scope.txt'):
            (self.module.OUTPUT_DIR / name).write_text('previous ' + name)
        for path in self.module.OUTPUT_DIR.iterdir():
            path.chmod(0o640)
        return self.snapshot()

    def retry(self):
        self.module.main()
        self.preserved(self.before)

    def test_actual_xlsx_to_catalog_reference_tdoc_contact_evidence_and_repeat(self):
        document = json.loads(self.before['tdocs.jsonld'])
        node, = document['@graph']
        self.assertEqual(node['@id'], 'tdoc:' + getattr(self, 'WG', 'RAN1').replace('RAN', 'R') + '-999999')
        self.assertEqual(node['submittedBy'], ['tdoc:company/Synthetic%20Company'])
        contacts = json.loads(self.before['contacts.jsonld'])['@graph']
        self.assertEqual(node['hasContact'], contacts[0]['@id'])
        self.assertEqual(json.loads(self.before[self.evidence.name])['@graph'], [])
        self.retry()
        self.retry()

    def test_invalid_catalog_contacts_late_preparation_and_retry_preserve_bundle(self):
        for value in ([], {}, {'Synthetic': []}, {'Synthetic': {'aliases': [None]}}):
            prior = self.prior_outputs()
            self.alias_path.write_text(json.dumps(value))
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.module.main()
            self.alias_path.write_bytes(self.alias_bytes)
            self.preserved(prior)
            self.retry()
        self.late_preparation_failures()

    def late_preparation_failures(self):
        for value in ([], {'@graph': None}):
            prior = self.prior_outputs()
            path = self.module.OUTPUT_DIR / 'contacts.jsonld'
            path.write_text(json.dumps(value))
            expected = self.snapshot()
            with self.subTest(contacts=value), self.assertRaises(SystemExit):
                self.module.main()
            self.preserved(expected)
            path.write_bytes(prior[path.name])
            self.retry()
        revision = importlib.import_module('tdoc_revision_evidence')
        for target, name in ((self.module, 'canonical_document'), (revision, 'write_evidence')):
            for error in (ValueError, KeyboardInterrupt):
                prior = self.prior_outputs()
                with self.subTest(name=name, error=error.__name__), patch.object(
                        target, name, side_effect=error('synthetic late preparation')):
                    with self.assertRaises(error):
                        self.module.main()
                self.preserved(prior)
                self.retry()

    def test_publish_each_output_and_optional_deletion_failure_interrupt_retry(self):
        replace = self.atomic_io.os.replace
        # 본문 다섯 파일: 병합진단·Contact·Contact진단·revision증거·Tdoc.
        for index in range(1, 6):
            for error in (OSError, KeyboardInterrupt):
                for after in (False, True):
                    prior = self.prior_outputs()
                    seen = 0
                    def failed(source, destination):
                        nonlocal seen
                        source = Path(source)
                        publishing = source.parent.name == 'new' and source.parent.parent.name.startswith('.text-set-')
                        if publishing:
                            seen += 1
                        if publishing and seen == index:
                            if after:
                                replace(source, destination)
                            raise error('synthetic bundle publication')
                        return replace(source, destination)
                    with self.subTest(index=index, error=error.__name__, after=after), patch.object(
                            self.atomic_io.os, 'replace', side_effect=failed):
                        with self.assertRaises(error):
                            self.module.main()
                    self.preserved(prior)
                    self.retry()
        unlink = Path.unlink
        for name in ('swapped_date_columns.txt', 'skipped_non_tdoc_files.txt'):
            for error in (OSError, KeyboardInterrupt):
                for after in (False, True):
                    prior = self.prior_outputs()
                    fired = False
                    def failed(path, *args, **kwargs):
                        nonlocal fired
                        if path == self.module.OUTPUT_DIR / name and not fired:
                            fired = True
                            if after:
                                unlink(path, *args, **kwargs)
                            raise error('synthetic optional deletion')
                        return unlink(path, *args, **kwargs)
                    with self.subTest(delete=name, error=error.__name__, after=after), patch.object(
                            Path, 'unlink', failed):
                        with self.assertRaises(error):
                            self.module.main()
                    self.preserved(prior)
                    self.retry()

    def test_staging_fsync_failure_interrupt_and_no_source_files_preserve_retry(self):
        for error in (OSError, KeyboardInterrupt):
            prior = self.prior_outputs()
            with patch.object(self.atomic_io.os, 'fsync', side_effect=error('synthetic fsync')):
                with self.assertRaises(error):
                    self.module.main()
            self.preserved(prior)
            self.retry()
        prior = self.prior_outputs()
        self.xlsx.rename(self.xlsx.with_suffix('.held'))
        self.xlsx.mkdir()
        try:
            with self.assertRaises(SystemExit):
                self.module.main()
            self.assertEqual(self.snapshot(), prior)
        finally:
            self.xlsx.rmdir()
            self.xlsx.with_suffix('.held').rename(self.xlsx)
        self.retry()

    def test_contact_pruning_is_published_with_tdocs_and_rollback_preserves_both(self):
        self.prior_outputs()
        path = self.module.OUTPUT_DIR / 'contacts.jsonld'
        contacts = json.loads(self.before[path.name])
        contacts['@graph'].append({'@id': 'tdoc:contact/orphan', '@type': 'Contact',
                                   'tdoc:contactName': 'Synthetic orphan'})
        path.write_text(json.dumps(contacts))
        prior = self.snapshot()
        replace = self.atomic_io.os.replace
        def failed(source, destination):
            source, destination = Path(source), Path(destination)
            if source.parent.name == 'new' and destination.name == 'tdocs.jsonld':
                replace(source, destination)
                raise KeyboardInterrupt('synthetic after final publication')
            return replace(source, destination)
        with patch.object(self.atomic_io.os, 'replace', side_effect=failed):
            with self.assertRaises(KeyboardInterrupt):
                self.module.main()
        self.preserved(prior)
        self.module.main()
        self.assertEqual(json.loads(path.read_text()), json.loads(self.before[path.name]))
        self.assertEqual((self.module.OUTPUT_DIR / 'tdocs.jsonld').read_bytes(), self.before['tdocs.jsonld'])
        self.assertIn('tdoc:contact/orphan', (self.module.OUTPUT_DIR / 'contact_scope.txt').read_text())
        self.module.main()
        self.assertNotIn('tdoc:contact/orphan', (self.module.OUTPUT_DIR / 'contact_scope.txt').read_text())

    def test_duplicate_nonfinite_cell_literals_are_preserved_and_repeat(self):
        import pandas as pd
        frame = pd.read_excel(self.xlsx, dtype=object)
        for value in ('inf', '-Infinity', '1e1000'):
            with self.subTest(value=value):
                self.assertEqual(self.module._fold(value), value)
                rows = pd.concat([frame, frame], ignore_index=True)
                rows['Title'] = value
                rows.to_excel(self.xlsx, index=False)
                before = self.xlsx.read_bytes()
                self.module.main()
                path = self.module.OUTPUT_DIR / 'tdocs.jsonld'
                nodes = json.loads(path.read_text())['@graph']
                self.assertEqual(len(nodes), 1)
                self.assertEqual(nodes[0]['tdoc:title'], value)
                output = path.read_bytes()
                self.module.main()
                self.assertEqual(path.read_bytes(), output)
                self.assertEqual(self.xlsx.read_bytes(), before)

    def test_shared_source_split_keeps_catalog_and_submitted_by_identities_equal(self):
        import pandas as pd
        from ontology import jsonld_context
        wg = getattr(self, 'WG', 'RAN1')
        source = ROOT / 'scripts/tsg/RAN/formal' / wg / 'phase-1/jsonld/01_company_normalization.py'
        spec = importlib.util.spec_from_file_location('synthetic_ran1_catalog_chain', source)
        normalizer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(normalizer)
        normalizer.INPUT_DIR = self.module.INPUT_DIR
        normalizer.INTERMEDIATE_DIR = self.module.INTERMEDIATE_DIR
        if hasattr(normalizer, 'RAN1_ALIASES_PATH'):
            normalizer.RAN1_ALIASES_PATH = self.root / 'absent_base.json'
        frame = pd.read_excel(self.xlsx, dtype=object)
        cases = [('Synthetic § Company', ['Synthetic § Company']),
                 ('Synthetic (A (B,C), D), Synthetic Outer',
                  ['Synthetic (A (B,C), D)', 'Synthetic Outer']),
                 ('Moderators (Synthetic A, Synthetic B)', ['Synthetic A', 'Synthetic B'])]
        for value, names in cases:
            with self.subTest(value=value):
                self.assertEqual(normalizer.split_companies(value), names)
                self.assertEqual(self.module.parse_submitters(value, {}), (names, []))
                frame['Source'] = value
                frame.to_excel(self.xlsx, index=False)
                before = self.xlsx.read_bytes()
                normalizer.main(['--min-company-tdocs', '1'])
                aliases = jsonld_context._company_aliases(str(self.alias_path), self.alias_path.stat().st_mtime_ns)
                with patch.object(jsonld_context, 'company_reference_aliases', return_value=aliases):
                    self.reference.main()
                    self.module.main()
                    companies = json.loads((self.module.OUTPUT_DIR / 'companies.jsonld').read_text())['@graph']
                    path = self.module.OUTPUT_DIR / 'tdocs.jsonld'
                    node, = json.loads(path.read_text())['@graph']
                    self.assertEqual(set(node['submittedBy']), {company['@id'] for company in companies})
                    self.assertEqual(len(companies), len(names))
                    current = path.read_bytes()
                    self.module.main()
                    self.assertEqual(path.read_bytes(), current)
                self.assertEqual(self.xlsx.read_bytes(), before)
        roles = importlib.import_module('submitter_roles')
        for value, expected in [('', []), (', ,', []), (' A, B ', ['A', 'B']),
                                ('A (B,C', ['A (B,C']), ('A),B', ['A)', 'B']),
                                ('A\x00B, C', ['A\x00B', 'C'])]:
            self.assertEqual(roles.split_source_parts(value), expected)
            self.assertEqual(normalizer.split_companies(value), expected)
            self.assertEqual(self.module.parse_submitters(value, {}), (expected, []))

    def test_actual_tdoc_cr_ls_classification_and_relations(self):
        import pandas as pd
        frame = pd.read_excel(self.xlsx, dtype=object)
        rows = pd.concat([frame, frame, frame], ignore_index=True)
        rows['TDoc'] = ['R1-999991', 'R1-999992', 'R1-999993']
        rows['Type'] = ['discussion', 'CR', 'LS out']
        rows['Title'] = ['Synthetic Tdoc', 'Synthetic CR', 'Synthetic LS']
        rows.loc[1, 'CR'] = '1234'
        rows.loc[1, 'UICC'] = 'yes'
        rows.to_excel(self.xlsx, index=False)
        before = self.xlsx.read_bytes()
        self.module.main()
        path = self.module.OUTPUT_DIR / 'tdocs.jsonld'
        nodes = json.loads(path.read_text())['@graph']
        self.assertEqual([node['@type'].split(':')[-1] for node in nodes], ['Tdoc', 'CR', 'LS'])
        self.assertEqual(nodes[1]['tdoc:crNumber'], '1234')
        self.assertTrue(nodes[1]['tdoc:affectsUICC'])
        self.assertEqual(nodes[1]['modifies'], 'tdoc:spec/38_331')
        self.assertEqual(nodes[2]['tdoc:direction'], 'out')
        self.assertEqual(nodes[2]['sentTo'], ['tdoc:wg/RAN1'])
        self.assertEqual(nodes[2]['ccTo'], ['tdoc:wg/SA2'])
        current = path.read_bytes()
        self.module.main()
        self.assertEqual(path.read_bytes(), current)
        self.assertEqual(self.xlsx.read_bytes(), before)


class Ran2TdocPublication(unittest.TestCase):
    """게시·복구 계약을 RAN2 실제 생성 코드에 같은 합성 입력으로 적용한다."""
    WG = 'RAN2'
    setUp = Ran1TdocPublication.setUp
    snapshot = Ran1TdocPublication.snapshot
    preserved = Ran1TdocPublication.preserved
    prior_outputs = Ran1TdocPublication.prior_outputs
    retry = Ran1TdocPublication.retry
    late_preparation_failures = Ran1TdocPublication.late_preparation_failures
    test_actual_xlsx_to_catalog_reference_tdoc_contact_evidence_and_repeat = Ran1TdocPublication.test_actual_xlsx_to_catalog_reference_tdoc_contact_evidence_and_repeat
    test_invalid_catalog_contacts_late_preparation_and_retry_preserve_bundle = Ran1TdocPublication.test_invalid_catalog_contacts_late_preparation_and_retry_preserve_bundle
    test_publish_each_output_and_optional_deletion_failure_interrupt_retry = Ran1TdocPublication.test_publish_each_output_and_optional_deletion_failure_interrupt_retry
    test_staging_fsync_failure_interrupt_and_no_source_files_preserve_retry = Ran1TdocPublication.test_staging_fsync_failure_interrupt_and_no_source_files_preserve_retry
    test_contact_pruning_is_published_with_tdocs_and_rollback_preserves_both = Ran1TdocPublication.test_contact_pruning_is_published_with_tdocs_and_rollback_preserves_both
    test_duplicate_nonfinite_cell_literals_are_preserved_and_repeat = Ran1TdocPublication.test_duplicate_nonfinite_cell_literals_are_preserved_and_repeat
    test_shared_source_split_keeps_catalog_and_submitted_by_identities_equal = Ran1TdocPublication.test_shared_source_split_keeps_catalog_and_submitted_by_identities_equal

    def test_source_correction_preparation_failure_preserves_bundle_and_retry(self):
        corrections = importlib.import_module('tdoc_source_identity_corrections')
        for error in (ValueError, KeyboardInterrupt):
            prior = self.prior_outputs()
            with patch.object(corrections, 'overlay_identity_corrections',
                              side_effect=error('synthetic source correction')) as overlay:
                with self.assertRaises(error):
                    self.module.main()
                self.assertEqual(overlay.call_args.args[1], 'RAN2')
            self.preserved(prior)
            self.retry()


class Ran3TdocPublication(unittest.TestCase):
    WG = 'RAN3'
    setUp = Ran1TdocPublication.setUp
    snapshot = Ran1TdocPublication.snapshot
    preserved = Ran1TdocPublication.preserved
    prior_outputs = Ran1TdocPublication.prior_outputs
    retry = Ran1TdocPublication.retry
    late_preparation_failures = Ran1TdocPublication.late_preparation_failures
    test_actual_xlsx_to_catalog_reference_tdoc_contact_evidence_and_repeat = Ran1TdocPublication.test_actual_xlsx_to_catalog_reference_tdoc_contact_evidence_and_repeat
    test_invalid_catalog_contacts_late_preparation_and_retry_preserve_bundle = Ran1TdocPublication.test_invalid_catalog_contacts_late_preparation_and_retry_preserve_bundle
    test_publish_each_output_and_optional_deletion_failure_interrupt_retry = Ran1TdocPublication.test_publish_each_output_and_optional_deletion_failure_interrupt_retry
    test_staging_fsync_failure_interrupt_and_no_source_files_preserve_retry = Ran1TdocPublication.test_staging_fsync_failure_interrupt_and_no_source_files_preserve_retry
    test_contact_pruning_is_published_with_tdocs_and_rollback_preserves_both = Ran1TdocPublication.test_contact_pruning_is_published_with_tdocs_and_rollback_preserves_both
    test_duplicate_nonfinite_cell_literals_are_preserved_and_repeat = Ran1TdocPublication.test_duplicate_nonfinite_cell_literals_are_preserved_and_repeat


class Ran4TdocPublication(unittest.TestCase):
    """RAN4 실제 입력 경로의 준비·게시·반복 실행 경계를 검사합니다."""
    WG = 'RAN4'
    setUp = Ran1TdocPublication.setUp
    snapshot = Ran1TdocPublication.snapshot
    preserved = Ran1TdocPublication.preserved
    prior_outputs = Ran1TdocPublication.prior_outputs
    retry = Ran1TdocPublication.retry
    late_preparation_failures = Ran1TdocPublication.late_preparation_failures
    test_actual_xlsx_to_catalog_reference_tdoc_contact_evidence_and_repeat = Ran1TdocPublication.test_actual_xlsx_to_catalog_reference_tdoc_contact_evidence_and_repeat
    test_publish_each_output_and_optional_deletion_failure_interrupt_retry = Ran1TdocPublication.test_publish_each_output_and_optional_deletion_failure_interrupt_retry
    test_staging_fsync_failure_interrupt_and_no_source_files_preserve_retry = Ran1TdocPublication.test_staging_fsync_failure_interrupt_and_no_source_files_preserve_retry
    test_contact_pruning_is_published_with_tdocs_and_rollback_preserves_both = Ran1TdocPublication.test_contact_pruning_is_published_with_tdocs_and_rollback_preserves_both

    def test_late_input_and_preparation_failures_preserve_bundle_and_retry(self):
        import pandas as pd
        self.late_preparation_failures()
        invalid = self.xlsx.with_name(self.xlsx.stem + '_later.xlsx')
        pd.DataFrame([{f'Other{i}': 'Synthetic' for i in range(10)}]).to_excel(invalid, index=False)
        prior = self.prior_outputs()
        source = invalid.read_bytes()
        try:
            with self.assertRaises(ValueError):
                self.module.main()
            self.preserved(prior)
            self.assertEqual(invalid.read_bytes(), source)
        finally:
            invalid.unlink()
        self.retry()
        revision = importlib.import_module('tdoc_revision_evidence')
        classification = importlib.import_module('tdoc_source_classification')
        targets = [(revision, 'qualify_revisions'),
                   (classification, 'apply_source_classifications')]
        if self.WG == 'RAN5':
            corrections = importlib.import_module('tdoc_source_identity_corrections')
            targets.extend([(self.module, 'supplement_instances'),
                            (corrections, 'overlay_identity_corrections')])
        for target, name in targets:
            for error in (ValueError, KeyboardInterrupt):
                prior = self.prior_outputs()
                with self.subTest(name=name, error=error.__name__), patch.object(
                        target, name, side_effect=error('synthetic source preparation')) as call:
                    with self.assertRaises(error):
                        self.module.main()
                    self.assertEqual(call.call_args.args[1], self.WG)
                self.preserved(prior)
                self.retry()
        scope = self.module.scope_contacts
        for error in (OSError, KeyboardInterrupt):
            prior = self.prior_outputs()
            def failed(*args, **kwargs):
                scope(*args, **kwargs)
                raise error('synthetic after staged Contact write')
            with self.subTest(name='scope_contacts', error=error.__name__), patch.object(
                    self.module, 'scope_contacts', side_effect=failed):
                with self.assertRaises(error):
                    self.module.main()
            self.preserved(prior)
            self.retry()

    def test_partial_staged_write_failure_interrupt_preserves_bundle_and_retries(self):
        writer = self.atomic_io.write_text_atomic
        for index in (1, 5):
            for error in (OSError, KeyboardInterrupt):
                prior = self.prior_outputs()
                seen = 0
                def failed(path, text, **kwargs):
                    nonlocal seen
                    path = Path(path)
                    staging = path.parent.name == 'new' and path.parent.parent.name.startswith('.text-set-')
                    if staging:
                        seen += 1
                    if staging and seen == index:
                        path.write_text('synthetic partial')
                        raise error('synthetic staged write')
                    return writer(path, text, **kwargs)
                with self.subTest(index=index, error=error.__name__), patch.object(
                        self.atomic_io, 'write_text_atomic', side_effect=failed):
                    with self.assertRaises(error):
                        self.module.main()
                self.assertEqual(seen, index)
                self.preserved(prior)
                self.retry()

    def test_real_duplicate_input_diagnostics_and_class_shifts_reset_between_runs(self):
        import pandas as pd
        original = pd.read_excel(self.xlsx, dtype=object)
        original['Type'] = ''
        original['Title'] = 'Synthetic original title'
        original['TDoc Status'] = 'available'
        original.to_excel(self.xlsx, index=False)
        duplicate = self.xlsx.with_name(self.xlsx.stem + '_later.xlsx')
        revised = original.copy()
        revised['Type'] = 'CR'
        revised['Title'] = 'Synthetic revised title'
        revised['TDoc Status'] = 'agreed'
        revised.to_excel(duplicate, index=False)
        sources = {path: path.read_bytes() for path in (self.xlsx, duplicate)}
        self.module.main()
        expected = self.snapshot()
        for _ in range(2):
            self.module.main()
            self.assertEqual(self.snapshot(), expected)
            self.assertEqual(self.module._CLASS_SHIFT, {'Tdoc': -1, 'CR': 1})
            self.assertEqual(len(self.module._FIELD_CONFLICTS), 1)
            self.assertEqual(len(self.module._MERGE_PROMOTED), 1)
            self.assertEqual(len(self.module.SKIPPED_NON_TDOC_FILES), 1)
        node, = json.loads(expected['tdocs.jsonld'])['@graph']
        self.assertEqual(node['@type'], 'tdoc:CR')
        self.assertEqual(node['tdoc:status'], 'agreed')
        for path, before in sources.items():
            self.assertEqual(path.read_bytes(), before)
        self.assertEqual([p.name for p in self.module.OUTPUT_DIR.iterdir() if p.name.startswith('.')], [])


class Ran5TdocPublication(Ran4TdocPublication):
    WG = 'RAN5'


class Ran1LocalHelperContracts(unittest.TestCase):
    setUp = Ran1TdocPublication.setUp
    snapshot = Ran1TdocPublication.snapshot

    def test_date_swap_boundaries_actual_workbook_and_repeat(self):
        import pandas as pd
        from datetime import datetime as dt
        helper = importlib.import_module('date_swap')
        fixed = [dt(2026, 9, 15), dt(2026, 10, 20)]
        cases = [([], []), ([dt(2026, 1, 10)], [dt(2026, 1, 10)]),
                 (fixed, fixed), (fixed + [dt(2026, 10, 1)], fixed + [dt(2026, 10, 1)]),
                 (fixed + [dt(2026, 1, 11)], fixed + [dt(2026, 1, 11)]),
                 (fixed + [dt(2026, 1, 10)], fixed + [dt(2026, 10, 1)])]
        for values, expected in cases:
            with self.subTest(values=values):
                frame = pd.DataFrame({'Reservation date': values})
                notes = []
                self.assertIs(helper.unswap_day_month(frame, 'synthetic.xlsx', notes), frame)
                self.assertEqual(frame['Reservation date'].tolist(), expected)
                previous = list(notes)
                helper.unswap_day_month(frame, 'synthetic.xlsx', notes)
                self.assertEqual(notes, previous)
        frame = pd.concat([pd.read_excel(self.xlsx, dtype=object)] * 3, ignore_index=True)
        prefix = getattr(self, 'WG', 'RAN1').replace('RAN', 'R')
        frame['TDoc'] = [prefix + suffix for suffix in ('-999991', '-999992', '-999993')]
        frame['Reservation date'] = fixed + [dt(2026, 1, 10, 4, 5, 6)]
        frame['Uploaded'] = fixed + [dt(2026, 1, 10, 7, 8, 9)]
        frame.to_excel(self.xlsx, index=False)
        source = self.xlsx.read_bytes()
        self.module.main()
        path = self.module.OUTPUT_DIR / 'tdocs.jsonld'
        nodes = json.loads(path.read_text())['@graph']
        self.assertEqual(nodes[2]['tdoc:reservationDate'], '2026-10-01T04:05:06')
        self.assertEqual(nodes[2]['tdoc:uploadedDate'], '2026-10-01T07:08:09')
        self.assertEqual(len(self.module.DATE_SWAP_NOTES), 2)
        before = self.snapshot()
        self.module.main()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.xlsx.read_bytes(), source)

    def test_meeting_suffixes_reach_reference_and_tdoc_identically(self):
        helper = importlib.import_module('meeting_id')
        wg = getattr(self, 'WG', 'RAN1')
        prefix = wg.replace('RAN', 'R')
        cases = [('112bis-e', '112bis-e', '112bis'),
                 ('112-bis-e', '112bis-e', '112bis'),
                 ('112_BIS_e', '112bis-e', '112bis'),
                 ('112bis_EOM', '112bis', '112bis'),
                 ('100_e', '100-e', '100'),
                 ('100_EOM_v2', '100', '100')]
        if wg == 'RAN1':
            cases.append(('100b_e', '100b-e', '100b'))
        for suffix, retained, canonical in cases:
            with self.subTest(suffix=suffix):
                path = self.xlsx.with_name('TDoc_List_TSG' + prefix + '_' + suffix + '.xlsx')
                self.xlsx.rename(path)
                self.xlsx = path
                source = path.read_bytes()
                self.reference.main()
                self.module.main()
                meeting, = json.loads((self.module.OUTPUT_DIR / 'meetings.jsonld').read_text())['@graph']
                node, = json.loads((self.module.OUTPUT_DIR / 'tdocs.jsonld').read_text())['@graph']
                self.assertEqual(helper.extract_meeting_from_filename(path.name), wg + '#' + retained)
                self.assertEqual(meeting['tdoc:canonicalMeetingNumber'], wg + '#' + canonical)
                self.assertEqual(node['presentedAt'], meeting['@id'])
                before = self.snapshot()
                self.module.main()
                self.assertEqual(self.snapshot(), before)
                self.assertEqual(path.read_bytes(), source)
        other = 'R2' if wg == 'RAN1' else 'R1'
        for value in ('unrelated.xlsx', 'TDoc_List_TSG' + other + '_112.xlsx',
                      'TSG' + prefix + '_112bisX.xlsx', 'TSG' + prefix + '_112garbage.xlsx',
                      wg + '#112bisX.xlsx', wg + '#112garbage.xlsx'):
            self.assertIsNone(helper.extract_meeting_from_filename(value))
        for value in (wg + '#112bis-e', ' ' + wg + '#112-BIS_ELECTRONIC '):
            self.assertEqual(helper.canonical_meeting_id(value), wg + '#112bis')


class Ran2LocalHelperContracts(Ran1LocalHelperContracts):
    WG = 'RAN2'

    def test_binding_nullable_blanks_and_shifted_values(self):
        import pandas as pd
        helper = importlib.import_module('tdoc_list_binding')
        for field in helper.BINDING_DATE_FIELDS + helper.BINDING_REF_FIELDS:
            frame = pd.DataFrame({field: pd.Series([pd.NA, None, ''], dtype='string')})
            self.assertEqual(helper.check_column_binding(frame), [])
        for value in (None, '', float('nan'), pd.NaT, pd.NA):
            self.assertTrue(helper._is_blank(value))
        for value in (False, 0, ' ', 'R2-999999'):
            self.assertFalse(helper._is_blank(value))
        self.assertEqual(helper.check_column_binding(pd.DataFrame({
            'Reservation date': ['2026-10-01', 45761.5],
            'Reply to': ['R2-999999', '2018-07-13-LS from IEEE']})), [])
        for field, value in (('Reservation date', 'R2-999999'),
                             ('Reply to', '2026-10-01')):
            with self.subTest(field=field), self.assertRaises(ValueError):
                helper.assert_column_binding(pd.DataFrame({field: [value]}), self.xlsx)
        duplicate = pd.DataFrame([['2026-10-01', '2026-10-02']],
                                 columns=['Reservation date', 'Reservation date'])
        self.assertIn('같은 이름의 열', helper.check_column_binding(duplicate)[0])


class Ran3LocalHelperContracts(Ran2LocalHelperContracts):
    WG = 'RAN3'


class Ran1ValidationPublication(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        for target, name in ((socket.socket, 'connect'), (socket, 'create_connection')):
            self.stack.enter_context(patch.object(
                target, name, side_effect=AssertionError('network forbidden')))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.stack.enter_context(patch.object(sys, 'path', sys.path.copy()))
        # 모듈 격리 후 복구할 때 NumPy를 반복 로드하지 않도록 먼저 적재한다.
        importlib.import_module('openpyxl')
        self.stack.enter_context(patch.dict(sys.modules))
        self.stack.enter_context(patch.dict('os.environ', {}, clear=True))
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        wg = getattr(self, 'WG', 'RAN1')
        source = ROOT / 'scripts/tsg/RAN/formal' / wg / 'phase-1/jsonld/04_validation.py'
        spec = importlib.util.spec_from_file_location('synthetic_ran1_validation', source)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.contract = importlib.import_module('phase1_count_contract')
        self.atomic = importlib.import_module('common.atomic_io')
        self.module.PROJECT_ROOT = self.root
        self.module.OUTPUT_DIR = self.root / 'output'
        self.module.OUTPUT_DIR.mkdir()
        self.module.REPORT_DIR = self.root / 'logs'
        self.module.REPORT_DIR.mkdir()
        self.report = self.module.REPORT_DIR / 'VALIDATION_REPORT.md'
        self.report.write_bytes(b'previous report')
        self.node = {'@id': 'tdoc:R1-999999', '@type': 'tdoc:Tdoc',
                     'tdoc:tdocNumber': 'R1-999999', 'tdoc:title': 'Synthetic',
                     'tdoc:type': 'discussion', 'tdoc:status': 'noted',
                     'tdoc:reservationDate': '2026-01-01',
                     'hasContact': 'tdoc:contact/999', 'belongsTo': 'tdoc:agenda/999',
                     'presentedAt': 'tdoc:meeting/999'}
        for stem in ('meetings', 'releases', 'companies', 'contacts', 'work_items',
                     'agenda_items', 'specs', 'working_groups'):
            self.write_graph(stem, [])
        for stem, key, kind in (('meetings', 'presentedAt', 'Meeting'),
                                ('contacts', 'hasContact', 'Contact'),
                                ('agenda_items', 'belongsTo', 'AgendaItem')):
            self.write_graph(stem, [{'@id': self.node[key], '@type': 'tdoc:' + kind}])
        self.write_graph('tdocs', [self.node])
        self.module.EXPECTED_COUNTS = {name: 0 for name in self.module.EXPECTED_COUNTS}
        self.module.EXPECTED_COUNTS.update(Meeting=1, Contact=1, AgendaItem=1, Tdoc=1)
        # 합성 입력에는 알려진 운영 WARN이 없으며 실제 fallback 정책을 사용한다.
        self.module.KNOWN_WARN_AXES = set()
        self.source_bytes = {p.name: p.read_bytes() for p in self.module.OUTPUT_DIR.iterdir()}

    def write_graph(self, stem, graph):
        (self.module.OUTPUT_DIR / (stem + '.jsonld')).write_text(
            json.dumps({'@graph': graph}), encoding='utf-8')

    def retry(self):
        self.assertEqual(self.module.main(), 0)
        self.assertIn('모든 검증 통과', self.report.read_text())
        self.assertEqual({p.name: p.read_bytes() for p in self.module.OUTPUT_DIR.iterdir()},
                         self.source_bytes)
        self.assertEqual([p.name for p in self.module.REPORT_DIR.iterdir()], [self.report.name])

    def test_actual_main_four_axes_report_and_repeat(self):
        self.retry()
        self.retry()
        for axis in ('count', 'props', 'refs', 'enum'):
            self.assertEqual(self.module.verdict_exit_code(*[name != axis for name in
                             ('count', 'props', 'refs', 'enum')]), 1)

    def test_actual_validation_errors_report_failure_and_retry(self):
        for key, value in (('tdoc:title', ''), ('hasContact', 'tdoc:contact/missing'),
                           ('tdoc:status', 'synthetic-invalid-status')):
            node = dict(self.node, **{key: value})
            self.write_graph('tdocs', [node])
            with self.subTest(key=key):
                self.assertEqual(self.module.main(), 1)
                self.assertIn('일부 검증 실패', self.report.read_text())
            self.write_graph('tdocs', [self.node])
            self.retry()
        self.module.EXPECTED_COUNTS['Tdoc'] = 2
        self.assertEqual(self.module.main(), 1)
        self.module.EXPECTED_COUNTS['Tdoc'] = 1
        self.retry()

    def test_late_contract_checkpoint_and_bad_input_preserve_report_retry(self):
        for name in ('verify_source_validation_results', 'load_warning_axes',
                     'verify_jsonld_checkpoint'):
            for error in (ValueError, KeyboardInterrupt):
                self.report.write_bytes(b'previous report')
                with self.subTest(name=name, error=error.__name__), \
                        patch.object(self.contract, name, side_effect=error('synthetic')), \
                        self.assertRaises(error):
                    self.module.main()
                self.assertEqual(self.report.read_bytes(), b'previous report')
                self.retry()
        path = self.module.OUTPUT_DIR / 'tdocs.jsonld'
        for invalid in (b'[]', b'{"@graph":null}', b'{invalid', b'\xff'):
            self.report.write_bytes(b'previous report')
            path.write_bytes(invalid)
            with self.subTest(invalid=invalid), self.assertRaises(
                    (SystemExit, ValueError, UnicodeError)):
                self.module.main()
            self.assertEqual(self.report.read_bytes(), b'previous report')
            path.write_bytes(self.source_bytes[path.name])
            self.retry()

    def test_atomic_report_write_interrupt_and_symlink_preserve_retry(self):
        for name in ('fsync', 'replace'):
            for error in (OSError, KeyboardInterrupt):
                self.report.write_bytes(b'previous report')
                with self.subTest(name=name, error=error.__name__), \
                        patch.object(self.atomic.os, name, side_effect=error('synthetic')), \
                        self.assertRaises(error):
                    self.module.main()
                self.assertEqual(self.report.read_bytes(), b'previous report')
                self.assertEqual(list(self.module.REPORT_DIR.iterdir()), [self.report])
                self.retry()
        target = self.root / 'preserved-user-report'
        target.write_bytes(b'user report')
        self.report.unlink()
        self.report.symlink_to(target)
        with self.assertRaises((ValueError, OSError)):
            self.module.main()
        self.assertTrue(self.report.is_symlink())
        self.assertEqual(target.read_bytes(), b'user report')
        self.report.unlink()
        self.retry()


class Ran2ValidationPublication(Ran1ValidationPublication):
    WG = 'RAN2'

    def test_operational_enum_warning_contract(self):
        self.module.KNOWN_WARN_AXES = {'enum'}
        self.assertEqual(self.module.verdict_exit_code(True, True, True, False), 0)
        self.assertEqual(self.module.verdict_exit_code(True, True, True, True), 1)
        self.assertEqual(self.module.verdict_exit_code(False, True, True, False), 1)


class Ran3ValidationPublication(Ran1ValidationPublication):
    WG = 'RAN3'


class Ran1KgPreflight(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        for target, name in ((socket.socket, 'connect'), (socket, 'create_connection')):
            self.stack.enter_context(patch.object(
                target, name, side_effect=AssertionError('network forbidden')))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.stack.enter_context(patch.object(sys, 'path', sys.path.copy()))
        importlib.import_module('neo4j')
        self.stack.enter_context(patch.dict(sys.modules))
        from common import credentials
        import dotenv
        self.stack.enter_context(patch.object(credentials, 'neo4j_auth', return_value=('synthetic', 'synthetic')))
        self.stack.enter_context(patch.object(dotenv, 'load_dotenv', return_value=False))
        revision = types.ModuleType('tdoc_revision_evidence')
        revision.preflight_revision_document = lambda *args: {}
        revision.load_evidence = lambda *args: None
        sys.modules['tdoc_revision_evidence'] = revision
        wg = getattr(self, 'wg', 'RAN1')
        self.path = ROOT / getattr(
            self, 'loader_path', f'scripts/tsg/RAN/formal/{wg}/phase-1/neo4j/01_load_kg.py')
        spec = importlib.util.spec_from_file_location(f'synthetic_{wg.lower()}_kg', self.path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.atomic = importlib.import_module('common.atomic_io')
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.module.ORPHAN_COMPANY_LOG = self.root / 'orphan_company_prune.json'

    class Result:
        def __init__(self, rows):
            self.rows = rows

        def __iter__(self):
            return iter(self.Record(row) for row in self.rows)

        class Record(dict):
            def data(self):
                return dict(self)

        def single(self):
            return self.Record(self.rows[0]) if self.rows else None

        def data(self):
            return self.rows

    class Driver:
        def __init__(self):
            self.closed = 0
            self.queries = []
            self.modes = []
            self.ids, self.count = ['tdoc:company/Synthetic'], 1
            self.orphans = []
            self.deleted = 0
            self.fail = None
            self.batch_failure = False

        def session(self, **kwargs):
            self.modes.append(kwargs)
            return self

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def close(self):
            self.closed += 1

        def execute_write(self, function, *args):
            return function(self, *args)

        def run(self, query, *args, **kwargs):
            self.queries.append(query)
            if self.fail and self.fail[0] in query:
                raise self.fail[1]('synthetic transport')
            if 'AS ids' in query:
                rows = [{'ids': self.ids, 'n': self.count}]
            elif 'ORDER BY id' in query:
                rows = self.orphans
            elif 'MATCH (c:Company) RETURN count(c) AS n' in query:
                rows = [{'n': self.count + len(self.orphans) - self.deleted}]
            elif 'DETACH DELETE c' in query:
                self.deleted += 1
                rows = [{'n': 1}]
            elif 'AS declared' in query:
                rows = [{'declared': 1, 'matched': 1, 'missing': []}]
            elif 'AS sample' in query:
                rows = [{'n': 0, 'sample': []}]
            elif 'labels(n)[0]' in query:
                rows = [{'label': 'Company', 'count': 1}, {'label': 'Tdoc', 'count': 1}]
            elif 'type(r) AS relType' in query:
                rows = [{'relType': 'PRESENTED_AT', 'count': 1}]
            elif 'AS cnt' in query:
                rows = [{'cnt': 2}]
            elif 'RETURN c.id AS id' in query:
                rows = [{'id': 'tdoc:company/Synthetic', 'name': 'Synthetic'}]
            elif 'apoc.periodic.iterate' in query:
                rows = [{'failedBatches': int(self.batch_failure),
                         'errorMessages': {'synthetic': 1} if self.batch_failure else {},
                         'total': 1, 'batches': 1}]
            else:
                rows = [{'count': 1}]
            return Ran1KgPreflight.Result(rows)

    def run_main(self, driver):
        with patch.object(self.module.GraphDatabase, 'driver', return_value=driver):
            return self.module.main()

    def assert_main_result(self, stats):
        self.assertEqual((stats['nodes'], stats['relationships']), (2, 1))

    def test_actual_main_preflight_before_writes_normal_and_repeat(self):
        for ids, count in (([], 0), ([''], 1), ([True], 1), ([0], 1),
                           ([[]], 1), ([{}], 1), ([' '], 1),
                           (['tdoc:company/Synthetic'], 2), ([None], 1)):
            driver = self.Driver()
            driver.ids, driver.count = ids, count
            with self.subTest(ids=ids, count=count), self.assertRaises(RuntimeError):
                self.run_main(driver)
            self.assertEqual(len(driver.queries), 1)
            self.assertEqual(driver.closed, 1)
            self.assertEqual(driver.modes, [{'default_access_mode': 'READ'}])
        for _ in range(2):
            driver = self.Driver()
            stats = self.run_main(driver)
            self.assert_main_result(stats)
            self.assertEqual(driver.closed, 1)
            self.assertGreater(len(driver.queries), 50)

    def test_actual_main_transport_batch_interrupt_close_and_retry(self):
        for marker in getattr(self, 'failure_markers', ('AS ids', 'AS cnt', 'CREATE INDEX')):
            for error in (ValueError, KeyboardInterrupt):
                driver = self.Driver()
                driver.fail = (marker, error)
                with self.subTest(marker=marker, error=error.__name__), self.assertRaises(error):
                    self.run_main(driver)
                self.assertEqual(driver.closed, 1)
        driver = self.Driver()
        driver.batch_failure = True
        with self.assertRaisesRegex(RuntimeError, 'APOC batch failed'):
            self.run_main(driver)
        self.assertEqual(driver.closed, 1)
        self.assert_main_result(self.run_main(self.Driver()))

    def test_prune_journal_failure_interrupt_precedes_delete_and_retry(self):
        from datetime import datetime
        journal = self.module.ORPHAN_COMPANY_LOG
        for operation in ('fsync', 'replace'):
            for error in (OSError, KeyboardInterrupt):
                journal.write_bytes(b'[]')
                journal.chmod(0o640)
                driver = self.Driver()
                driver.orphans = [{'id': 'tdoc:company/Obsolete', 'labels': ['Company'],
                                   'properties': {'recorded': datetime(2026, 1, 1)}, 'rels': []}]
                with self.subTest(operation=operation, error=error.__name__), patch.object(
                        self.atomic.os, operation, side_effect=error('synthetic audit')), \
                        self.assertRaises(error):
                    self.module.prune_orphan_companies(driver, apply=True)
                self.assertEqual(driver.deleted, 0)
                self.assertEqual(journal.read_bytes(), b'[]')
                self.assertEqual(journal.stat().st_mode & 0o777, 0o640)
                self.assertEqual(list(self.root.iterdir()), [journal])
                plan = self.module.prune_orphan_companies(driver, apply=True)
                self.assertEqual((plan['deleted'], plan['company_nodes_after']), (1, 1))
                entry, = json.loads(journal.read_text())
                self.assertEqual(entry['prunable'][0]['properties']['recorded'], '2026-01-01 00:00:00')
                self.assertEqual(journal.stat().st_mode & 0o777, 0o640)

    def test_prune_symlink_journal_preserves_target_before_delete(self):
        target = self.root / 'original.json'
        target.write_bytes(b'[]')
        self.module.ORPHAN_COMPANY_LOG.symlink_to(target)
        driver = self.Driver()
        driver.orphans = [{'id': 'tdoc:company/Obsolete', 'labels': ['Company'],
                           'properties': {}, 'rels': []}]
        with self.assertRaisesRegex(ValueError, '심볼릭 링크'):
            self.module.prune_orphan_companies(driver, apply=True)
        self.assertEqual(driver.deleted, 0)
        self.assertTrue(self.module.ORPHAN_COMPANY_LOG.is_symlink())
        self.assertEqual(target.read_bytes(), b'[]')


class Ran2KgPreflight(Ran1KgPreflight):
    wg = 'RAN2'
    failure_markers = ('AS ids', 'labels(n)[0]', 'CREATE INDEX')

    def assert_main_result(self, stats):
        self.assertIsNone(stats)


class Ran3KgPreflight(Ran2KgPreflight):
    wg = 'RAN3'


class Ran4KgPreflight(Ran2KgPreflight):
    wg = 'RAN4'


class Ran5KgPreflight(Ran2KgPreflight):
    wg = 'RAN5'


class AllWgTdocSubtypeLabels(unittest.TestCase):
    setUp = Ran1KgPreflight.setUp
    Driver = Ran1KgPreflight.Driver
    run_main = Ran1KgPreflight.run_main

    def test_actual_main_reconciles_only_owned_cr_and_ls_labels(self):
        """Capture actual main queries; the fake driver does not execute Cypher."""
        expected = """
            item['@type'] = 'tdoc:CR', 'REMOVE t:LS SET t:CR',
            item['@type'] = 'tdoc:LS', 'REMOVE t:CR SET t:LS'
            ], 'REMOVE t:CR, t:LS', {t: t})
        """
        for wg in (f'RAN{i}' for i in range(1, 6)):
            with self.subTest(wg=wg):
                path = ROOT / f'scripts/tsg/RAN/formal/{wg}/phase-1/neo4j/01_load_kg.py'
                spec = importlib.util.spec_from_file_location(f'synthetic_{wg.lower()}_subtypes', path)
                self.module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(self.module)
                self.module.ORPHAN_COMPANY_LOG = self.root / f'{wg}-orphan-company-prune.json'
                driver = self.Driver()
                self.run_main(driver)
                query, = [query for query in driver.queries if 'CALL apoc.do.case([' in query]
                self.assertIn("MERGE (t:Tdoc {id: item['@id']})", query)
                branches = query.split('CALL apoc.do.case([', 1)[1].split('YIELD value', 1)[0]
                self.assertEqual(' '.join(branches.split()), ' '.join(expected.split()))
                # Whole-label replacement would also remove user and other-phase labels.
                self.assertNotIn('setLabels', '\n'.join(driver.queries))
                self.assertEqual(driver.closed, 1)


class Ran2CqValidation(unittest.TestCase):
    wg = 'RAN2'
    loader_path = 'scripts/tsg/RAN/formal/RAN2/phase-1/validation/01_validate_cq_cypher.py'

    def setUp(self):
        Ran1KgPreflight.setUp(self)
        self.module.CQ_DATASET_PATH = self.root / 'dataset.json'
        self.module.OUTPUT_PATH = self.root / 'results.json'
        self.cq = {'id': 'Synthetic', 'category': 'synthetic', 'question': 'Synthetic count',
                   'cypher': 'RETURN 1 AS count', 'nonzero_columns': ['count'],
                   'nonnull_columns': ['count']}
        self.module.CQ_DATASET_PATH.write_text(json.dumps({'questions': [self.cq]}))
        guards = self.module.guard_defects.__globals__
        self.module.guard_defects = lambda session, cq, rows=None: (
            guards['nonzero_defects'](cq, rows) + guards['nonnull_defects'](cq, rows))

    class Driver(Ran1KgPreflight.Driver):
        def __init__(self):
            super().__init__()
            self.rows = [{'count': 1}]

        def run(self, query, *args, **kwargs):
            self.queries.append(query)
            if self.fail:
                raise self.fail('synthetic query failure')
            return Ran1KgPreflight.Result(self.rows)

    def run_validation(self, driver):
        with patch.object(self.module.GraphDatabase, 'driver', return_value=driver):
            return self.module.run_validation()

    def test_result_row_guards_read_mode_and_retry(self):
        source = self.module.CQ_DATASET_PATH.read_bytes()
        for rows, status in (([{'count': 1}], 'PASS'), ([{'count': 0}], 'FAIL'),
                             ([{'count': None}], 'FAIL'), ([{}], 'FAIL'), ([], 'NO_DATA')):
            driver = self.Driver()
            driver.rows = rows
            with self.subTest(rows=rows):
                result, = self.run_validation(driver)
                self.assertEqual(result['status'], status)
                self.assertEqual(driver.closed, 1)
                self.assertEqual(driver.modes, [{'default_access_mode': 'READ'}])
                stored = json.loads(self.module.OUTPUT_PATH.read_text())
                self.assertEqual(stored['results'][0]['status'], status)
        for _ in range(2):
            result, = self.run_validation(self.Driver())
            self.assertEqual(result['status'], 'PASS')
        self.assertEqual(self.module.CQ_DATASET_PATH.read_bytes(), source)

    def test_driver_cleanup_on_session_query_and_input_failure(self):
        output = self.module.OUTPUT_PATH
        output.write_bytes(b'previous report')
        for error in (ValueError, KeyboardInterrupt):
            driver = self.Driver()
            with patch.object(self.Driver, '__enter__', side_effect=error('synthetic entry')), \
                    self.assertRaises(error):
                self.run_validation(driver)
            self.assertEqual(driver.closed, 1)
            self.assertEqual(output.read_bytes(), b'previous report')
        driver = self.Driver()
        driver.fail = KeyboardInterrupt
        with self.assertRaises(KeyboardInterrupt):
            self.run_validation(driver)
        self.assertEqual(driver.closed, 1)
        self.assertEqual(output.read_bytes(), b'previous report')
        driver = self.Driver()
        driver.fail = ValueError
        result, = self.run_validation(driver)
        self.assertEqual(result['status'], 'FAIL')
        self.assertIn('synthetic query failure', result['error'])
        self.assertEqual(driver.closed, 1)
        driver = self.Driver()
        self.module.CQ_DATASET_PATH.write_text(json.dumps({'questions': [{}]}))
        with self.assertRaises(KeyError):
            self.run_validation(driver)
        self.assertEqual(driver.closed, 1)

    def test_report_failure_interrupt_preserves_previous_and_retry(self):
        output = self.module.OUTPUT_PATH
        source = self.module.CQ_DATASET_PATH.read_bytes()
        for operation in ('fsync', 'replace'):
            for error in (OSError, KeyboardInterrupt):
                output.write_bytes(b'previous report')
                driver = self.Driver()
                with self.subTest(operation=operation, error=error.__name__), patch.object(
                        self.atomic.os, operation, side_effect=error('synthetic report')), \
                        self.assertRaises(error):
                    self.run_validation(driver)
                self.assertEqual(driver.closed, 1)
                self.assertEqual(output.read_bytes(), b'previous report')
                self.assertEqual(set(self.root.iterdir()), {output, self.module.CQ_DATASET_PATH})
                result, = self.run_validation(self.Driver())
                self.assertEqual(result['status'], 'PASS')
        output.write_bytes(b'previous report')
        driver = self.Driver()
        driver.rows = [{'count': float('nan')}]
        with self.assertRaises(ValueError):
            self.run_validation(driver)
        self.assertEqual(output.read_bytes(), b'previous report')
        self.assertEqual(driver.closed, 1)
        self.assertEqual(self.module.CQ_DATASET_PATH.read_bytes(), source)


class Ran3CqValidation(Ran2CqValidation):
    wg = 'RAN3'
    loader_path = 'scripts/tsg/RAN/formal/RAN3/phase-1/validation/01_validate_cq_cypher.py'


class SharedSourceHelpers(unittest.TestCase):
    def test_reverse_wg_helper_imports_keep_local_patch_bindings(self):
        modules = {}
        with patch.object(sys, 'path', sys.path.copy()):
            for number in range(5, 0, -1):
                wg = f'RAN{number}'
                source = ROOT / 'scripts/tsg/RAN/formal' / wg / 'phase-1/jsonld/submitter_roles.py'
                spec = importlib.util.spec_from_file_location(f'reverse_submitter_roles_{wg}', source)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                modules[wg] = module
                self.assertEqual(module.split_source_parts('Moderators (삼성전자, Nokia), Établissement'),
                                 ['Moderators (삼성전자, Nokia)', 'Établissement'])
            for wg, module in modules.items():
                with self.subTest(patched_wg=wg), \
                        patch.object(module, 'split_source_parts', return_value=['local replacement']):
                    self.assertEqual(module.split_source_parts('input'), ['local replacement'])
                    for other_wg, other in modules.items():
                        if other_wg != wg:
                            self.assertEqual(other.split_source_parts('Alpha, Beta'), ['Alpha', 'Beta'])

    def test_every_wg_instance_import_accepts_cached_ran5_role_helper(self):
        with patch.object(sys, 'path', sys.path.copy()), patch.dict(sys.modules):
            source = ROOT / 'scripts/tsg/RAN/formal/RAN5/phase-1/jsonld/submitter_roles.py'
            spec = importlib.util.spec_from_file_location('submitter_roles', source)
            helper = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(helper)
            sys.modules['submitter_roles'] = helper
            for number in range(5, 0, -1):
                wg = f'RAN{number}'
                # 회의·시트 판독은 WG별 구현을 읽고 역할 helper 캐시만 공유한다.
                for name in ('tdoc_list_binding', 'meeting_id', 'date_swap'):
                    sys.modules.pop(name, None)
                source = ROOT / 'scripts/tsg/RAN/formal' / wg / 'phase-1/jsonld/03_tdoc_instances.py'
                spec = importlib.util.spec_from_file_location(f'reverse_instances_{wg}', source)
                module = importlib.util.module_from_spec(spec)
                with self.subTest(wg=wg):
                    spec.loader.exec_module(module)
                    self.assertIs(module.unwrap_roles, helper.unwrap_roles)
                    if wg in ('RAN1', 'RAN2'):
                        self.assertIs(module.split_source_parts, helper.split_source_parts)

    def test_every_wg_preserves_role_names_and_conservative_date_correction(self):
        import pandas as pd
        from datetime import datetime as dt
        for number in range(1, 6):
            wg = f'RAN{number}'
            with self.subTest(wg=wg), patch.object(sys, 'path', sys.path.copy()):
                source = ROOT / 'scripts/tsg/RAN/formal' / wg / 'phase-1/jsonld'
                modules = {}
                for name in ('submitter_roles', 'date_swap'):
                    spec = importlib.util.spec_from_file_location(f'shared_{name}_{wg}', source / (name + '.py'))
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    modules[name] = module
                roles, dates = modules['submitter_roles'], modules['date_swap']
                self.assertEqual(roles.unwrap_roles('Moderators (삼성전자, Nokia)'), ['삼성전자', 'Nokia'])
                self.assertEqual(roles.unwrap_roles('Établissement (Rapporteur)'), ['Établissement'])
                self.assertEqual(roles.unwrap_roles('RAN1 Chair'), [])
                self.assertEqual(roles.unwrap_roles('Unchanged Company'), ['Unchanged Company'])
                fixed = [dt(2026, 9, 15), dt(2026, 10, 20)]
                values = fixed + [dt(2026, 1, 10)]
                frame = pd.DataFrame({'Reservation date': values})
                notes = []
                dates.unswap_day_month(frame, 'synthetic.xlsx', notes)
                self.assertEqual(frame['Reservation date'].tolist(), fixed + [dt(2026, 10, 1)])
                self.assertEqual(len(notes), 1)
                dates.unswap_day_month(frame, 'synthetic.xlsx', notes)
                self.assertEqual(len(notes), 1)
                # 한 날짜라도 기존 해석으로 범위 안에 있으면 열 전체를 유지한다.
                values.append(dt(2026, 10, 2))
                frame = pd.DataFrame({'Reservation date': values})
                dates.unswap_day_month(frame, 'synthetic.xlsx', [])
                self.assertEqual(frame['Reservation date'].tolist(), values)


if __name__ == '__main__':
    unittest.main()
