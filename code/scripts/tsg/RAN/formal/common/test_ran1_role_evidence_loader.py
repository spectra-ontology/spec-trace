#!/usr/bin/env python3
"""Exercise source-bound RAN1 report-placement loading without a database.

Spec: docs/tsg/RAN/formal/RAN1/phase-2/step1_parsing.md.
Ontology: reportedUnderAgenda and EvidenceAssertion/Fragment provenance.
Cycle: tiny accepted DOCX and current producer -> guarded mock transaction.
배경: role artifacts and their quoted placement evidence share one source generation.
사용: python3 -B -m unittest discover -s scripts/tsg/RAN/formal/common -p test_ran1_role_evidence_loader.py.
LLM 호출: none. All generated files belong to automatically removed temp directories.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import site
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from docx import Document

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
sys.path.insert(0, str(ROOT / 'scripts/common'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ontology import jsonld_context, rdf_mapping


def load_loader():
    path = ROOT / 'scripts/tsg/RAN/formal/RAN1/phase-2/neo4j/02_load_roles.py'
    spec = importlib.util.spec_from_file_location('_tested_ran1_role_evidence_loader', path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(os.environ, {'NEO4J_PASSWORD': 'isolated-fixture-no-database'}):
        spec.loader.exec_module(module)
    return module


class Result:
    def __init__(self, rows):
        self.rows = rows

    def data(self):
        return self.rows

    def single(self):
        return self.rows[0]

    def consume(self):
        return None

    def __iter__(self):
        return iter(self.rows)


class Transaction:
    """Return explicit endpoint multiplicities and record all writes for review."""
    def __init__(self, endpoint_change=None, fragment_count=0, wrong_count=False):
        self.calls = []
        self.endpoint_change = endpoint_change
        self.fragment_count = fragment_count
        self.wrong_count = wrong_count

    def run(self, query, **parameters):
        self.calls.append((query, parameters))
        if 'AS existingAssertions' in query:
            rows = [dict(assertionId=row['assertionId'], subjects=1,
                         subjectIds=[row['subject']], canonicalSubjects=1, objects=1, existingAssertions=0)
                    for row in parameters['rows']]
            if rows and self.endpoint_change:
                rows[0].update(self.endpoint_change)
            return Result(rows)
        if 'AS existingFragments' in query:
            return Result([dict(id=value, existingFragments=self.fragment_count)
                           for value in parameters['ids']])
        if 'RETURN c.id AS id' in query:
            return Result([dict(id='tdoc:company/Fixture', name='Fixture', aliases=[])])
        if 'AS matched' in query:
            return Result([dict(matched=1)])
        if ' AS n' in query:
            if self.wrong_count and 'MERGE (a:EvidenceAssertion' in query:
                return Result([dict(n=0)])
            return Result([dict(n=len(parameters['rows']) if 'rows' in parameters else 1)])
        return Result([dict(c=0)])


class Session:
    def __init__(self, tx):
        self.tx = tx
        self.write_calls = 0
        self.commits = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def run(self, query, **parameters):
        if 'RETURN sum_cnt, count(sn)' in query:
            return Result([dict(sum_cnt=1, sn_cnt=1)])
        return Result([])

    def execute_write(self, function, *args):
        self.write_calls += 1
        value = function(self.tx, *args)
        self.commits += 1
        return value


class Driver:
    def __init__(self, session):
        self.current_session = session
        self.closed = False

    def session(self):
        return self.current_session

    def close(self):
        self.closed = True


class RoleEvidenceLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loader = load_loader()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='spectra-role-loader-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.out = self.root / 'ontology/output/tsg/RAN/formal/instances/phase-2/RAN1'
        self.parsed = self.root / 'ontology/output/tsg/RAN/formal/parsed_reports/RAN1'
        self.registration = self.root / 'ontology/output/tsg/RAN/formal/instances/phase-1/RAN1/tdocs.jsonld'
        self.source = self.root / 'source.docx'
        doc = Document()
        doc.add_paragraph('6.\tMaintenance', style='Heading 1')
        doc.add_paragraph('R1-1234567\tFL summary of maintenance')
        doc.add_paragraph('R1-1234568\tSession notes for maintenance')
        doc.save(self.source)
        self.out.mkdir(parents=True)
        self.parsed.mkdir(parents=True)
        self.registration.parent.mkdir(parents=True)
        schema = self.root / 'ontology/schema/tdoc-ontology.ttl'
        schema.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / 'ontology/schema/tdoc-ontology.ttl', schema)
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        # A concurrent source reconciliation CLI must not run from this pure
        # fresh-install fixture. An accidental second write remains a failure.
        stack.enter_context(patch.dict(sys.modules, {'reconcile_agenda_placements': SimpleNamespace(
            reconcile=Mock(side_effect=AssertionError('Unexpected second reconciliation after role commit')))}))
        stack.enter_context(patch.object(sys, 'path', [
            str(ROOT / 'scripts/tsg/RAN/formal/RAN1/phase-2/report-parser'), *sys.path]))
        stack.enter_context(patch.object(self.loader, 'PROJECT_ROOT', self.root))
        stack.enter_context(patch.object(self.loader, 'INSTANCES_DIR', self.out))
        stack.enter_context(patch.object(jsonld_context, 'PROJECT_ROOT', self.root))
        stack.enter_context(patch.object(jsonld_context, 'SCHEMA_PATH', schema))
        # Real production rules remain read-only; owned copies model concurrent
        # code edits without changing another session's source files.
        rule_paths = []
        for actual in self.loader._role_rule_paths():
            actual = ROOT / actual.relative_to(self.root) if actual.is_relative_to(self.root) else actual
            target = self.root / actual.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(actual, target)
            rule_paths.append(target)
        self.rule_path = self.root / 'scripts/tsg/RAN/formal/RAN1/phase-2/report-parser/agenda_matcher.py'
        stack.enter_context(patch.object(self.loader, '_role_rule_paths', return_value=set(rule_paths)))
        producer = self.loader._role_generator()
        import reconcile_agendas
        sections, _ = reconcile_agendas.source_sections(self.source)
        self.report = dict(meeting_id='RAN1#100', docx_path='source.docx', sections=sections,
            fl_summaries=[dict(tdoc_number='R1-1234567', title='FL summary of maintenance',
                              company='Fixture', agenda_item='6', paragraph_index=1)],
            session_notes=[dict(tdoc_number='R1-1234568', title='Session notes for maintenance',
                               company='Fixture', agenda_item='6', paragraph_index=2)])
        self.report_path = self.parsed / 'RAN1_100.json'
        self.report_path.write_text(json.dumps(self.report))
        self.registered = {'tdoc:R1-1234567': 'tdoc:agenda/100-5',
                           'tdoc:R1-1234568': 'tdoc:agenda/100-5'}
        self.registration.write_text(json.dumps({'@graph': [
            {'@id': key, 'belongsTo': value} for key, value in self.registered.items()]}))
        self.regenerate_documents()

    def regenerate_documents(self):
        producer = self.loader._role_generator()
        placements = producer.prepare_role_placements([self.report])
        documents = {
            'summaries.jsonld': producer.generate_summaries_jsonld([self.report], self.registered, placements),
            'session_notes.jsonld': producer.generate_session_notes_jsonld([self.report], self.registered, placements),
            'role_agenda_evidence.jsonld': producer.evidence_document(placements.values(), producer.CONTEXT)}
        for name, document in documents.items():
            (self.out / name).write_text(json.dumps(jsonld_context.canonical_document(document, wg='RAN1')))

    def pending_without_heading(self):
        doc = Document()
        doc.add_paragraph('R1-1234567\tFL summary of maintenance')
        doc.add_paragraph('R1-1234568\tSession notes for maintenance')
        doc.save(self.source)
        self.report['sections'] = []
        for index, group in enumerate(('fl_summaries', 'session_notes')):
            self.report[group][0].update(paragraph_index=index, agenda_item='UNKNOWN')
        self.report_path.write_text(json.dumps(self.report))
        self.regenerate_documents()

    def pending_with_approximate_heading(self):
        from docx.enum.style import WD_STYLE_TYPE
        import reconcile_agendas
        doc = Document()
        doc.styles.add_style('toc 1', WD_STYLE_TYPE.PARAGRAPH)
        doc.add_paragraph('6\tMaintenance schedules for radio adaptation\t1', style='toc 1')
        doc.add_paragraph('Maintenance schedule for radio adaptation', style='Heading 1')
        doc.add_paragraph('R1-1234567\tFL summary of maintenance')
        doc.add_paragraph('R1-1234568\tSession notes for maintenance')
        doc.save(self.source)
        self.report['sections'], _ = reconcile_agendas.source_sections(self.source)
        for index, group in enumerate(('fl_summaries', 'session_notes'), start=2):
            self.report[group][0].update(paragraph_index=index, agenda_item='6')
        self.report_path.write_text(json.dumps(self.report))
        self.regenerate_documents()

    def snapshot(self):
        return {path.relative_to(self.root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in self.root.rglob('*') if path.is_file()}

    def assert_no_driver(self, action, message):
        with patch.object(self.loader.GraphDatabase, 'driver') as driver:
            with self.assertRaisesRegex(ValueError, message):
                action()
            driver.assert_not_called()

    def test_standalone_loader_finds_source_rules_before_producer_import(self):
        path = ROOT / 'scripts/tsg/RAN/formal/RAN1/phase-2/neo4j/02_load_roles.py'
        probe = ('import json,runpy,socket,sys; from pathlib import Path; '
                 'sys.path.extend(json.loads(sys.argv[2])); '
                 'deny=lambda *a,**k: (_ for _ in ()).throw(AssertionError("Unexpected transport")); '
                 'socket.socket.connect=deny; socket.create_connection=deny; '
                 'module=runpy.run_path(sys.argv[1], run_name="isolated_role_probe"); '
                 'paths=module["_role_rule_paths"](); '
                 'assert all(path.is_file() for path in paths); '
                 'assert any(path.name=="agenda_source_supplements.py" for path in paths); '
                 'print(len(paths))')
        env = dict(os.environ, NEO4J_PASSWORD='isolated-fixture-no-database')
        # Keep CWD/PYTHONPATH isolated while retaining this interpreter's installed
        # user dependencies (for example neo4j installed with pip --user).
        result = subprocess.run([sys.executable, '-I', '-B', '-c', probe, str(path),
                                 json.dumps([site.getusersitepackages()])],
                                env=env, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertGreaterEqual(int(result.stdout.strip()), 15)

    def test_actual_source_quotes_hashes_and_registered_primary_survive_preflight(self):
        before = self.snapshot()
        with patch.object(self.loader.GraphDatabase, 'driver') as driver:
            inputs = self.loader._accept_inputs()
            driver.assert_not_called()
        self.assertEqual(inputs['summaries.jsonld'][0]['agenda'], 'tdoc:agenda/100-5')
        self.assertEqual(inputs['summaries.jsonld'][0]['reportedUnderAgenda'], 'tdoc:agenda/100-6')
        assertions, fragments = self.loader._role_evidence_rows(inputs)
        self.assertEqual(len(assertions), 2)
        self.assertTrue(all(row['properties']['evidenceSha256'] == hashlib.sha256(self.source.read_bytes()).hexdigest()
                            for row in fragments))
        self.assertTrue(any('source_role_document_entry' in row['properties']['evidenceLocator'] for row in fragments))
        self.assertEqual(self.snapshot(), before)

    def test_each_missing_artifact_blocks_before_driver_with_regeneration_command(self):
        for name in self.loader.ROLE_FILES:
            path = self.out / name
            raw = path.read_bytes()
            path.unlink()
            try:
                self.assert_no_driver(self.loader.main, '01_generate_jsonld.py --roles-only')
            finally:
                path.write_bytes(raw)

    def test_changed_claim_quote_locator_hash_and_direct_placement_are_rejected(self):
        path = self.out / 'role_agenda_evidence.jsonld'
        original = path.read_bytes()
        changes = [('evidenceQuote', 'invented source text'), ('evidenceLocator', 'another paragraph'),
                   ('evidenceSha256', '0' * 64), ('assertionObject', 'tdoc:agenda/100-7'),
                   ('assertionPredicateIRI', 'https://w3id.org/spectra#belongsTo')]
        for field, value in changes:
            document = json.loads(original)
            node = next(row for row in document['@graph'] if field in row)
            node[field] = value
            path.write_text(json.dumps(document))
            self.assert_no_driver(self.loader.main, 'Stale or altered')
        path.write_bytes(original)
        summary = self.out / 'summaries.jsonld'
        document = json.loads(summary.read_bytes())
        document['@graph'][0]['reportedUnderAgenda'] = 'tdoc:agenda/100-5'
        summary.write_text(json.dumps(document))
        self.assert_no_driver(self.loader.main, 'Stale or altered')

    def test_changed_source_bytes_or_registration_block_before_driver(self):
        raw = self.source.read_bytes()
        self.source.write_bytes(raw + b'changed ZIP trailing metadata')
        self.assert_no_driver(self.loader.main, 'Stale or altered')
        self.source.write_bytes(raw)
        document = json.loads(self.registration.read_bytes())
        document['@graph'][0]['belongsTo'] = 'tdoc:agenda/100-9'
        self.registration.write_text(json.dumps(document))
        self.assert_no_driver(self.loader.main, 'Stale or altered')

    def test_source_generation_fence_stops_changed_bytes_and_new_reports_before_tx_calls(self):
        inputs = self.loader._accept_inputs()
        raw = self.source.read_bytes()
        self.source.write_bytes(raw + b'concurrent edit')
        tx = Transaction()
        with self.assertRaisesRegex(ValueError, 'source SHA changed'):
            self.loader.write_role_generation(tx, inputs, 'run')
        self.assertEqual(tx.calls, [])
        self.source.write_bytes(raw)
        (self.parsed / 'RAN1_101.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'source list changed'):
            self.loader.write_role_generation(tx, inputs, 'run')
        self.assertEqual(tx.calls, [])

    def test_missing_ambiguous_or_wrong_identity_endpoints_stop_before_any_write(self):
        inputs = self.loader._accept_inputs()
        changes = [dict(subjects=0, subjectIds=[]), dict(subjects=2), dict(objects=0),
                   dict(objects=2), dict(subjectIds=['tdoc:R1-other']), dict(existingAssertions=2),
                   dict(canonicalSubjects=0), dict(canonicalSubjects=2)]
        for change in changes:
            tx = Transaction(endpoint_change=change)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'status=source_verified'):
                self.loader.write_role_generation(tx, inputs, 'run')
            self.assertTrue(all('MERGE' not in query and 'DELETE' not in query and 'SET ' not in query
                                for query, _ in tx.calls))
        tx = Transaction(fragment_count=2)
        with self.assertRaisesRegex(ValueError, 'fragment identity preflight'):
            self.loader.write_role_generation(tx, inputs, 'run')
        self.assertTrue(all('MERGE' not in query for query, _ in tx.calls))

    def test_pending_claim_with_real_endpoint_is_retained_without_direct_relation(self):
        self.pending_with_approximate_heading()
        inputs = self.loader._accept_inputs()
        assertions, fragments = self.loader._role_evidence_rows(inputs)
        self.assertTrue(all(row['status'] == 'pending' for row in assertions))
        tx = Transaction()
        assertions, fragments, deferred = self.loader._check_role_endpoints(tx, assertions, fragments)
        self.assertEqual(deferred, [])
        stats = self.loader._load_role_evidence(tx, assertions, fragments, 'run')
        direct = next(parameters for query, parameters in tx.calls if 'MERGE (t)-[r:REPORTED_UNDER_AGENDA]' in query)
        self.assertEqual(direct['rows'], [])
        self.assertEqual(stats['assertions'], 2)
        self.assertEqual(stats['confirmedPlacements'], 0)

    def test_actual_pending_unknown_preserves_artifact_and_defers_only_missing_object(self):
        self.pending_without_heading()
        inputs = self.loader._accept_inputs()
        artifact = self.out / 'role_agenda_evidence.jsonld'
        original = artifact.read_bytes()
        assertions, fragments = self.loader._role_evidence_rows(inputs)
        self.assertTrue(all(row['status'] == 'pending' and row['object'].endswith('-UNKNOWN') for row in assertions))
        tx = Transaction(endpoint_change=dict(objects=0))
        _, stats, _ = self.loader.write_role_generation(tx, inputs, 'pending')
        self.assertEqual(stats['deferredIds'], [assertions[0]['assertionId']])
        self.assertEqual(stats['deferredReason'], 'pending_agenda_endpoint_absent')
        self.assertEqual(stats['evidenceArtifactSha256'], hashlib.sha256(original).hexdigest())
        needed = set(assertions[1]['evidence'])
        loaded = next(parameters['rows'] for query, parameters in tx.calls if 'MERGE (e:EvidenceFragment' in query)
        self.assertEqual({row['id'] for row in loaded}, needed)
        retained = next(parameters['rows'] for query, parameters in tx.calls if 'MERGE (a:EvidenceAssertion' in query)
        self.assertEqual([row['assertionId'] for row in retained], [assertions[1]['assertionId']])
        stale = next(parameters['ids'] for query, parameters in tx.calls if 'DETACH DELETE a' in query)
        self.assertEqual(stale, [assertions[1]['assertionId']])
        self.assertEqual(original, artifact.read_bytes())

    def test_pending_subject_identity_and_all_duplicates_still_fail_before_writes(self):
        self.pending_without_heading()
        inputs = self.loader._accept_inputs()
        for change in (dict(subjects=0, subjectIds=[]), dict(subjects=2), dict(canonicalSubjects=2),
                       dict(subjectIds=['tdoc:R1-other']), dict(objects=2), dict(existingAssertions=2)):
            tx = Transaction(endpoint_change=change)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'status=pending.*source.docx'):
                self.loader.write_role_generation(tx, inputs, 'pending')
            self.assertTrue(all('MERGE' not in query and 'DELETE' not in query for query, _ in tx.calls))

    def test_one_atomic_main_write_preserves_primary_and_every_provenance_endpoint(self):
        inputs = self.loader._accept_inputs()
        before = self.snapshot()
        tx = Transaction()
        session = Session(tx)
        driver = Driver(session)
        with patch.object(self.loader, '_accept_inputs', return_value=inputs), \
             patch.object(self.loader.GraphDatabase, 'driver', return_value=driver), \
             contextlib.redirect_stdout(io.StringIO()):
            stats = self.loader.main()
        self.assertEqual((session.write_calls, session.commits), (1, 1))
        self.assertTrue(driver.closed)
        self.assertEqual(stats['role_evidence']['assertions'], 2)
        self.assertEqual(stats['role_evidence']['confirmedPlacements'], 2)
        writes = '\n'.join(query for query, _ in tx.calls if 'MERGE' in query or 'DELETE' in query or 'SET ' in query)
        self.assertNotIn(':BELONGS_TO', writes)
        self.assertNotIn('CREATE (agenda', writes)
        for relationship in ('ASSERTION_SUBJECT', 'ASSERTION_OBJECT', 'HAS_EVIDENCE', 'REPORTED_UNDER_AGENDA'):
            self.assertIn(relationship, writes)
        self.assertEqual(before, self.snapshot())

    def test_every_role_query_uses_the_phase1_scalar_tdoc_number_contract(self):
        inputs = self.loader._accept_inputs()
        tx = Transaction()
        self.loader.write_role_generation(tx, inputs, 'scalar-contract')
        resolver = self.loader.CompanyResolver(tx)
        original_run = tx.run
        def submitter_result(query, **parameters):
            if 'collect(DISTINCT c.id) AS ids' in query:
                tx.calls.append((query, parameters))
                return Result([dict(ids=['tdoc:company/Fixture'])])
            return original_run(query, **parameters)
        tx.run = submitter_result
        self.assertEqual(resolver.resolve(tx, 'Summary', 'R1-1234567', 'tdoc:company/Unlisted'),
                         'tdoc:company/Fixture')
        queries = '\n'.join(query for query, _ in tx.calls)
        self.assertNotRegex(queries, r'\bIN\s+\w+\.tdocNumber\b')
        self.assertIn('t.tdocNumber = row.number', queries)
        self.assertIn('NOT n.tdocNumber IN $declared', queries)

    def test_unregistered_role_creation_keeps_tdoc_number_scalar(self):
        tx = Transaction()
        original_run = tx.run
        def no_registered_match(query, **parameters):
            if 'AS matched' in query:
                tx.calls.append((query, parameters))
                return Result([dict(matched=0)])
            return original_run(query, **parameters)
        tx.run = no_registered_match
        self.loader.create_summary_nodes(tx, [{'tdocNumber': 'R1-1234567', 'title': 'Summary'}])
        self.loader.create_session_notes_nodes(tx, [{'tdocNumber': 'R1-1234568', 'title': 'Notes'}])
        created = [query for query, _ in tx.calls if 'CREATE (' in query]
        self.assertEqual(len(created), 2)
        for query in created:
            with self.subTest(query=query):
                self.assertRegex(query, r'tdocNumber:\s*\$tdocNumber\b')

    def test_end_fence_failure_is_inside_single_transaction_and_driver_is_closed(self):
        inputs = self.loader._accept_inputs()
        tx = Transaction()
        session = Session(tx)
        driver = Driver(session)
        original = self.loader._load_role_evidence
        def change_after_evidence(*args):
            result = original(*args)
            self.source.write_bytes(self.source.read_bytes() + b'concurrent source edit')
            return result
        with patch.object(self.loader, '_accept_inputs', return_value=inputs), \
             patch.object(self.loader, '_load_role_evidence', side_effect=change_after_evidence), \
             patch.object(self.loader.GraphDatabase, 'driver', return_value=driver), \
             contextlib.redirect_stdout(io.StringIO()), \
             self.assertRaisesRegex(ValueError, 'source SHA changed'):
            self.loader.main()
        self.assertEqual((session.write_calls, session.commits), (1, 0))
        self.assertTrue(driver.closed)

    def test_common_rdf_mapping_retains_source_ids_and_schema_predicates(self):
        inputs = self.loader._accept_inputs()
        assertions, fragments = self.loader._role_evidence_rows(inputs)
        self.assertEqual(rdf_mapping.pick_id('EvidenceAssertion', assertions[0]['properties']), assertions[0]['assertionId'])
        for fragment in fragments:
            self.assertEqual(rdf_mapping.pick_id('EvidenceFragment', fragment['properties']), fragment['id'])
        for name in ('REPORTED_UNDER_AGENDA', 'ASSERTION_SUBJECT', 'ASSERTION_OBJECT', 'HAS_EVIDENCE'):
            expected = dict(REPORTED_UNDER_AGENDA='reportedUnderAgenda', ASSERTION_SUBJECT='assertionSubject',
                            ASSERTION_OBJECT='assertionObject', HAS_EVIDENCE='hasEvidence')[name]
            self.assertEqual(str(rdf_mapping.core_relationship_predicate(name)), jsonld_context.SPECTRA_NAMESPACE + expected)

    def test_repeat_generation_keeps_source_identities_and_owned_stale_edge_boundary(self):
        inputs = self.loader._accept_inputs()
        transactions = [Transaction(), Transaction()]
        results = [self.loader.write_role_generation(tx, inputs, run)[1]
                   for tx, run in zip(transactions, ('first', 'second'))]
        self.assertEqual(results[0], results[1])
        payloads = [[parameters['rows'] for query, parameters in tx.calls
                     if 'MERGE (a:EvidenceAssertion' in query or 'MERGE (e:EvidenceFragment' in query]
                    for tx in transactions]
        self.assertEqual(payloads[0], payloads[1])
        for tx in transactions:
            stale = next((query, parameters) for query, parameters in tx.calls
                         if 'coalesce(r._roleAgendaRun' in query)
            self.assertIn('r._roleAgendaOwner=$owner', stale[0])
            self.assertEqual(stale[1]['owner'], self.loader.ROLE_OWNER)
            self.assertTrue(all('CREATE (agenda' not in query for query, _ in tx.calls))

    def test_attachment_count_failure_stays_inside_atomic_write(self):
        inputs = self.loader._accept_inputs()
        tx = Transaction(wrong_count=True)
        session = Session(tx)
        driver = Driver(session)
        with patch.object(self.loader, '_accept_inputs', return_value=inputs), \
             patch.object(self.loader.GraphDatabase, 'driver', return_value=driver), \
             contextlib.redirect_stdout(io.StringIO()), \
             self.assertRaisesRegex(ValueError, 'assertion endpoints: expected 2, attached 0'):
            self.loader.main()
        self.assertEqual((session.write_calls, session.commits), (1, 0))
        self.assertTrue(driver.closed)

    def test_parser_rule_change_during_write_prevents_commit(self):
        inputs = self.loader._accept_inputs()
        tx = Transaction()
        session = Session(tx)
        driver = Driver(session)
        original = self.loader._load_role_evidence
        def change_rule(*args):
            result = original(*args)
            self.rule_path.write_bytes(self.rule_path.read_bytes() + b'\n# concurrent rule edit\n')
            return result
        with patch.object(self.loader, '_accept_inputs', return_value=inputs), \
             patch.object(self.loader, '_load_role_evidence', side_effect=change_rule), \
             patch.object(self.loader.GraphDatabase, 'driver', return_value=driver), \
             contextlib.redirect_stdout(io.StringIO()), \
             self.assertRaisesRegex(ValueError, 'source SHA changed: agenda_matcher.py'):
            self.loader.main()
        self.assertEqual((session.write_calls, session.commits), (1, 0))
        self.assertTrue(driver.closed)


if __name__ == '__main__':
    unittest.main()
