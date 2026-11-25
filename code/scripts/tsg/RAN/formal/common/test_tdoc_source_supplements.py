#!/usr/bin/env python3
"""test_tdoc_source_supplements.py — direct-source identity and revision regression.

Spec: Phase-1 selected source ledgers, independent count prediction and revision identity.
Ontology: CR/Tdoc inheritance, exact endpoints, optional administrative dates.
Cycle: synthetic native cover/report evidence → mutation rejection → deterministic overlay.
배경: missing intermediate revisions must preserve their separate document identities.
사용: python3 -B -m unittest discover -s scripts/tsg/RAN/formal/common -p test_tdoc_source_supplements.py
LLM 호출: 없음. 임시 DOCX·XLSX·검증 기록과 실제 검증 함수만 사용한다.
"""
from contextlib import ExitStack
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
sys.path.insert(0, str(ROOT / 'scripts/tsg/RAN/formal/common'))
import tdoc_source_supplements as s
import tdoc_source_identity_corrections as c
import reconcile_tdoc_source_supplements as r


class BoundSourcePathTests(unittest.TestCase):
    def test_source_ledger_requires_its_own_working_group_document_numbers(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            ledger = root / 'ledger.json'
            with patch.object(s, 'ledger_path', return_value=ledger):
                for target, valid in (('R1-123456', True), ('R2-123456', False)):
                    with self.subTest(target=target):
                        ledger.write_text(json.dumps({'schema': 1, 'wg': 'RAN1', 'records': [{'target': target}]}))
                        if valid:
                            self.assertEqual(s.read_ledger(root, 'RAN1')['records'], [{'target': target}])
                        else:
                            with self.assertRaisesRegex(s.SupplementError, 'identities'):
                                s.read_ledger(root, 'RAN1')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.relative = str(s.review_artifacts.LEGACY_REVIEW_ROOT / 'synthetic-old/proof.json')
        current = 'logs/common/RAN5/verification/ontology-system-review/synthetic-current/proof.json'
        self.contexts = ExitStack()
        self.addCleanup(self.contexts.close)
        self.contexts.enter_context(patch.object(s.review_artifacts, 'RECORDED_FILE_RELOCATIONS',
                                      {self.relative: current}))
        self.raw = b'{"records":[]}\n'
        self.sha = hashlib.sha256(self.raw).hexdigest()
        self.original = self.root / self.relative
        self.current = self.root / s.review_artifacts.relocated_coordinate(self.relative)

    def write(self, path, raw=None):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.raw if raw is None else raw)
        return path

    def test_review_source_reads_exact_original_and_relocated_bytes(self):
        self.write(self.original)
        self.assertEqual(s.checked_path(self.root, self.relative, self.sha), self.original)
        self.current.parent.mkdir(parents=True, exist_ok=True)
        self.original.rename(self.current)
        self.assertEqual(s.checked_path(self.root, self.relative, self.sha), self.current)
        self.assertEqual(self.current.read_bytes(), self.raw)
        self.assertEqual(s.checked_path(self.root, self.current.relative_to(self.root).as_posix(),
                                        self.sha), self.current)

    def test_original_tamper_and_two_coordinates_cannot_borrow_a_good_copy(self):
        self.write(self.original, b'changed')
        with self.assertRaises(s.SupplementError):
            s.checked_path(self.root, self.relative, self.sha)
        self.write(self.current)
        with self.assertRaises(s.SupplementError) as raised:
            s.checked_path(self.root, self.relative, self.sha)
        self.assertIsInstance(raised.exception.__cause__, ValueError)
        self.write(self.original)
        with self.assertRaises(s.SupplementError):
            s.checked_path(self.root, self.relative, self.sha)

    def test_relocated_tamper_missing_and_sha_shape_fail_closed(self):
        with self.assertRaises(s.SupplementError) as raised:
            s.checked_path(self.root, self.relative, self.sha)
        self.assertIsInstance(raised.exception.__cause__, FileNotFoundError)
        self.write(self.current, b'changed')
        with self.assertRaises(s.SupplementError):
            s.checked_path(self.root, self.relative, self.sha)
        self.write(self.current)
        for value in ('0' * 64, self.sha.upper(), None, True, 'bad'):
            with self.subTest(sha=value), self.assertRaises(s.SupplementError):
                s.checked_path(self.root, self.relative, value)

    def test_review_symlink_and_traversal_are_not_relocation_authority(self):
        other = self.write(self.root / 'other.json')
        self.original.parent.mkdir(parents=True)
        self.original.symlink_to(other)
        with self.assertRaises(s.SupplementError):
            s.checked_path(self.root, self.relative, self.sha)
        self.original.unlink()
        self.current.parent.mkdir(parents=True)
        self.current.symlink_to(other)
        with self.assertRaises(s.SupplementError):
            s.checked_path(self.root, self.relative, self.sha)
        self.current.unlink()
        self.write(self.original)
        traversal = str(Path(self.relative).parent / '..' / 'ontology_system_review' / self.original.name)
        with self.assertRaises(s.SupplementError):
            s.checked_path(self.root, traversal, self.sha)
        for relative in ('scripts/../' + self.relative, './' + self.relative,
                         self.relative.replace('/verification/', '//verification/')):
            with self.subTest(path=relative), self.assertRaises(s.SupplementError):
                s.checked_path(self.root, relative, self.sha)

    def test_unknown_review_parent_is_only_read_at_its_existing_coordinate(self):
        relative = 'logs/common/verification/ontology_system_review/unknown/proof.json'
        original = self.write(self.root / relative)
        self.assertEqual(s.checked_path(self.root, relative, self.sha), original)
        original.unlink()
        self.write(self.root / 'logs/common/verification/ontology-system-review/unknown/proof.json')
        with self.assertRaises(s.SupplementError):
            s.checked_path(self.root, relative, self.sha)

    def test_corpus_source_still_uses_its_original_sha_and_repository_boundary(self):
        source = self.write(self.root / 'source.docx')
        self.assertEqual(s.checked_path(self.root, 'source.docx', self.sha), source)
        source.write_bytes(b'changed')
        with self.assertRaisesRegex(s.SupplementError, 'SHA changed'):
            s.checked_path(self.root, 'source.docx', self.sha)
        for relative in ('../outside.docx', str(source)):
            with self.subTest(path=relative), self.assertRaises(s.SupplementError):
                s.checked_path(self.root, relative, self.sha)


class SyntheticSourceInputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from docx import Document
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        import openpyxl
        import cr_form
        import docx_text
        import decision_disposition as disposition
        import document_decision_source as decision_source
        import tdoc_document_supplements as documents
        cls.temp = tempfile.TemporaryDirectory(); cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name); (cls.root / '.git').mkdir()
        cls.directory = cls.root / 'ontology/output/tsg/RAN/formal/instances/phase-1/RAN5'
        cls.directory.mkdir(parents=True)
        cls.references = {'companies': [{'@id': 'tdoc:company/Example_Company',
                'tdoc:companyName': 'Example Company', 'tdoc:aliases': ['Example Alias']}],
            'meetings': [{'@id': 'tdoc:meeting/RAN5_' + n, 'tdoc:meetingNumber': 'RAN5#' + n}
                         for n in ('998-e', '999-e')],
            'specs': [{'@id': 'tdoc:spec/38_521-1', 'tdoc:specNumber': '38.521-1'}],
            'releases': [{'@id': 'tdoc:release/Rel_' + str(n), 'tdoc:releaseName': 'Rel-' + str(n)}
                         for n in (14, 15, 16, 17)],
            'work_items': [{'@id': 'tdoc:workitem/SYNTHETIC_WI', 'tdoc:workItemCode': 'SYNTHETIC_WI'}]}
        cls.instances = []
        cls.rows = []
        cls.corrections = []
        cls.native_rows = []
        cls.ran3_corrections = []
        def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
        def cover(target, *, release='Rel-17', revision='1', number='7100', tracked=False):
            path = cls.root / 'synthetic' / (target + '.docx'); path.parent.mkdir(exist_ok=True)
            doc = Document(); doc.add_paragraph('3GPP TSG-RAN' + target[1] + ' Meeting #999-e ' + target)
            doc.add_paragraph('CHANGE REQUEST')
            cells = [['38.521-1', 'CR', number, 'rev', revision, 'Current version:', '14.1.0'],
                ['Release:', release], ['Title:', 'Synthetic proposal ' + target],
                ['Category:', 'F'], ['Source to WG:', 'Example Alias'], ['Work item code:', 'SYNTHETIC_WI'],
                ['Reason for change:', 'Synthetic reason'], ['Summary of change:', 'Synthetic summary'],
                ['Consequences if not approved:', 'Synthetic consequence'], ['Clauses affected:', '1'],
                ['Synthetic field 1', 'value'], ['Synthetic field 2', 'value']]
            table = doc.add_table(rows=len(cells), cols=7)
            for row, values in zip(table.rows, cells):
                for cell, value in zip(row.cells, values): cell.text = value
            if tracked:
                paragraph = table.cell(0, 2).paragraphs[0]
                for child in list(paragraph._p): paragraph._p.remove(child)
                for kind, value in (('del', 'CR#'), ('ins', number)):
                    change = OxmlElement('w:' + kind); run = OxmlElement('w:r')
                    text = OxmlElement('w:delText' if kind == 'del' else 'w:t'); text.text = value
                    run.append(text); change.append(run); paragraph._p.append(change)
            doc.save(path)
            texts, sha, _ = disposition.source_blocks(str(path))
            return path, texts, sha
        def report(target, *, meeting='RAN5#999-e', prior=None, revised=None,
                   release='Rel-17', revision='1', number='7100', kind='CR', approved_from=None):
            path = cls.root / 'synthetic' / (target + '-report.docx')
            doc = Document()
            lines = [(approved_from or target) + ' Synthetic proposal ' + target,
                     'Type: ' + kind, 'For: Agreement', 'Source: Example Alias']
            if kind == 'CR': lines.append(f'38.521-1 v14.1.0 CR{number} rev {revision} Cat: F ({release})')
            if prior: lines.append('(Replaces ' + prior + ')')
            lines.append('Decision: The document was ' + ('approved as ' + target if approved_from
                else 'revised to ' + revised if revised else 'agreed') + '.')
            for text in lines: doc.add_paragraph(text)
            doc.save(path); texts, sha, _ = disposition.source_blocks(str(path))
            events, _ = decision_source.document_decisions({'meeting_id': meeting,
                'docx_path': path.relative_to(cls.root).as_posix()}, cls.root)
            if len(events) != 1: raise AssertionError('Synthetic report must have one actual decision')
            event = events[0]; start, end = event['body_blocks']
            common = dict(path=path.relative_to(cls.root).as_posix(), sourceSHA256=sha,
                meeting=meeting, startBlock=start, endBlockExclusive=end,
                entry=[dict(block=i, text=texts[i]) for i in range(start, end)],
                title='Synthetic proposal ' + target, target=target, documentType=kind,
                quote=event['content'], decisionId=event['decision_id'],
                sourceDocumentDisposition='revised' if revised else 'agreed',
                documentDecisions=[dict(block=event['sequence'], text=texts[event['sequence']])])
            return common
        def initial(target, **extra):
            node = {'@id': 'tdoc:' + target, '@type': 'tdoc:CR', 'tdoc:tdocNumber': target,
                    'tdoc:crNumber': '7100', 'tdoc:crRevision': '2', 'unrelated': 'retained', **extra}
            cls.instances.append(node); return node
        def correction(target, *, scope='spreadsheet_cover_identity', release='Rel-17',
                       prior=None, revised=None, field='tdoc:crNumber', before='0000', after='7100', tracked=False):
            path, texts, sha = cover(target, release=release, number=after if field == 'tdoc:crNumber' else '0314' if tracked else '7100', tracked=tracked)
            r = report(target, meeting='RAN' + target[1] + '#999-e', prior=prior, revised=revised,
                       release=release, number=after if field == 'tdoc:crNumber' else '0314' if tracked else '7100')
            return dict(target=target, meetingId='RAN' + target[1] + '#999-e', scope=scope,
                review={'actualDocumentEvidence': [dict(path=path.relative_to(cls.root).as_posix(), sha256=sha,
                    locator=f'word/document.xml accepted body blocks [{i},{i + 1})', quote=text)
                    for i, text in enumerate(texts)]}, reportEntry=r,
                deltas=[dict(field=field, before=before, sourceBackedValue=after)])
        chains = [('R5-990101','R5-990102','R5-990103'), ('R5-990104','R5-990105','R5-990106')]
        cls.chains = chains
        source_specs = [(middle, prior, final, '999-e') for prior, middle, final in chains]
        source_specs += [(f'R5-{990201+i}', f'R5-{991301+i}', None, '998-e' if i == 4 else '999-e')
                         for i in range(5)]
        for target, prior, revised, meeting in source_specs:
            initial(prior)
            if revised: initial(revised)
            path, texts, sha = cover(target)
            r = report(target, meeting='RAN5#' + meeting, prior=prior, revised=revised)
            identity = dict(tdocNumber=target, meetingNumber='RAN5#999-e', canonicalMeetingNumber='RAN5#999',
                specNumber='38.521-1', crNumber='7100', crRevision='1', title='Synthetic proposal ' + target,
                sourceToWG='Example Alias', workItem='SYNTHETIC_WI', category='F', currentVersion='14.1.0',
                release='Rel-17', isRevisionOf=[prior])
            if meeting == '998-e':
                # The source cover and the report must identify the same selected meeting.
                doc = Document(path); doc.paragraphs[0].text = '3GPP TSG-RAN5 Meeting #998-e ' + target; doc.save(path)
                texts, sha, _ = disposition.source_blocks(str(path))
                identity.update(meetingNumber='RAN5#998-e', canonicalMeetingNumber='RAN5#998')
            cls.rows.append(dict(target=target, path=path.relative_to(cls.root).as_posix(), sha256=sha,
                meetingSourceFiles=[dict(path=r['path'], sha256=r['sourceSHA256'])],
                coverBlocks=[dict(block=i, text=text) for i, text in enumerate(texts)], sourceIdentity=identity, report=r))
        for index in range(14):
            target = f'R5-{992100+index}'
            if index == 0:
                row = correction(target, release='Rel-15', field='targetRelease',
                    before='tdoc:release/Rel_14', after='tdoc:release/Rel_15')
                initial(target, targetRelease='tdoc:release/Rel_14')
            else:
                row = correction(target); initial(target, **{'tdoc:crNumber': '0000'})
            cls.corrections.append(row)
        for prior, middle, final in chains:
            cls.corrections.append(correction(prior, scope='missing_intermediate_revision_chain', revised=middle,
                field='revisedTo', before=None, after='tdoc:' + middle))
            cls.corrections.append(correction(final, scope='missing_intermediate_revision_chain', prior=middle,
                field='isRevisionOf', before=None, after='tdoc:' + middle))
        for index in range(1, 32):
            target = f'R5-{993000+index}'; kind = 'other' if index <= 24 else 'pCR' if index == 25 else 'CR' if index <= 28 else 'LS out'
            path = cls.root / 'synthetic' / (target + '.docx')
            doc = Document(); doc.add_paragraph(target)
            method = 'own_cover'; locator = 'word/document.xml accepted body blocks [0,1)'; text = target
            if index == 1:
                path = path.with_suffix('.xlsx'); book = openpyxl.Workbook(); book.active['A1'] = target
                book.save(path); book.close(); method = 'own_cover_cell'; locator = "workbook sheet 'Sheet' cell A1"
            else:
                if index == 3:
                    doc = Document(); table = doc.add_table(rows=3, cols=3)
                    for row, values in zip(table.rows, [['Document history','',''],['V1.0.0','R5-994003','old'],['V2.0.0',target,'current']]):
                        for cell, value in zip(row.cells, values): cell.text = value
                    method='latest_document_history_revision'
                if kind in {'CR', 'pCR'}:
                    table = doc.add_table(rows=4, cols=7)
                    for row, values in zip(table.rows, [['38.521-1','CR','','rev','','Current version:','14.1.0'],
                            ['Release:','Rel-17'],['Category:','F'],['Work item code:','SYNTHETIC_WI']]):
                        for cell, value in zip(row.cells, values): cell.text=value
                doc.save(path)
                texts, _, _ = disposition.source_blocks(str(path)); text=texts[0]
            metadata = documents.own_cr_metadata(documents._native_blocks(str(path), digest(path))) if kind in {'CR','pCR'} else {}
            native = dict(kind='document', target=target, path=path.relative_to(cls.root).as_posix(), sha256=digest(path),
                canonicalClass=documents.document_class(kind), meetingSourceFiles=[],
                nativeIdentity=dict(method=method, locator=locator, text=text), ownCRMetadata=metadata,
                sourceIdentity=dict(tdocNumber=target, type=kind, title='Synthetic proposal ' + target,
                    canonicalMeetingNumber='RAN5#999', **{'for': None}),
                report=report(target, kind=kind, approved_from='R5-994002' if index==2 else None))
            if index == 4:
                original = path.with_suffix('.doc'); original.write_bytes(b'Synthetic native binary source')
                native.update(path=original.relative_to(cls.root).as_posix(), sha256=digest(original))
                native['nativeView'] = dict(path=path.relative_to(cls.root).as_posix(), sha256=digest(path),
                    conversionLineage=dict(sourcePath=native['path'], sourceSha256=native['sha256'],
                        derivedPath=path.relative_to(cls.root).as_posix(), derivedSha256=digest(path),
                        tool='synthetic_converter', version='1', method='synthetic_fixture'))
            cls.native_rows.append(native)
        for index in range(3):
            target=f'R3-{995001+index}'
            cls.ran3_corrections.append(correction(target, release='Rel-16', field='targetRelease',
                before='tdoc:release/Rel_15', after='tdoc:release/Rel_16', tracked=index==2))
        for name, values in cls.references.items(): (cls.directory / (name + '.jsonld')).write_text(json.dumps({'@graph': values}))
        (cls.directory / 'tdocs.jsonld').write_text(json.dumps({'@graph': cls.instances}))
        for wg, rows, path in [('RAN5', cls.rows + cls.native_rows, s.ledger_path(cls.root,'RAN5')),
                ('RAN5',cls.corrections,c.ledger_path(cls.root,'RAN5')),
                ('RAN3',cls.ran3_corrections,c.ledger_path(cls.root,'RAN3'))]:
            path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps({'schema':1,'wg':wg,'records':rows}))
        ran3 = cls.root / 'ontology/output/tsg/RAN/formal/instances/phase-1/RAN3'; ran3.mkdir(parents=True)
        for name, values in cls.references.items():
            if name=='meetings': values=[{'@id':'tdoc:meeting/RAN3_999-e','tdoc:meetingNumber':'RAN3#999-e'}]
            (ran3/(name+'.jsonld')).write_text(json.dumps({'@graph':values}))
        (ran3/'tdocs.jsonld').write_text(json.dumps({'@graph':[{'@id':'tdoc:'+row['target'],
            'tdoc:tdocNumber':row['target'],'targetRelease':'tdoc:release/Rel_15','unrelated':'retained'} for row in cls.ran3_corrections]}))
        parser = Path('scripts/tsg/RAN/formal/RAN5/phase-1/jsonld/meeting_id.py')
        (cls.root/parser).parent.mkdir(parents=True); (cls.root/parser).write_bytes((ROOT/parser).read_bytes())
        lists=s.ledger_path(cls.root,'RAN5').parent/'TDoc_List';lists.mkdir()
        for meeting in ('998-e','999-e'):
            book=openpyxl.Workbook();book.save(lists/('TDoc_List_RAN5#'+meeting+'.xlsx'));book.close()
        cls.selected={node['tdoc:meetingNumber'] for node in cls.references['meetings']}
        for cache in (disposition.source_blocks, documents._native_blocks, documents._report_events):
            cls.addClassCleanup(cache.cache_clear)
        cls.addClassCleanup(decision_source._EVENT_CACHE.clear); cls.addClassCleanup(decision_source._ANNEX_CACHE.clear)

    def setUp(self):
        read_bytes,read_text=Path.read_bytes,Path.read_text
        def checked(method):
            def read(path,*args,**kwargs):
                self.assertTrue(path.resolve().is_relative_to(self.root),str(path))
                return method(path,*args,**kwargs)
            return read
        self.contexts = ExitStack()
        self.addCleanup(self.contexts.close)
        self.contexts.enter_context(patch.object(Path,'read_bytes',checked(read_bytes)))
        self.contexts.enter_context(patch.object(Path,'read_text',checked(read_text)))


class SourceLedgerTests(SyntheticSourceInputs):
    def source_overlay(self):
        nodes = copy.deepcopy(self.instances)
        additions = s.supplement_instances(self.root, 'RAN5', nodes, self.references, self.selected)
        nodes.extend(additions)
        changes = c.overlay_identity_corrections(self.root, 'RAN5', nodes, self.references, self.selected)
        return nodes, additions, changes

    def test_actual_seven_dispositions_are_five_agreed_two_revised(self):
        from collections import Counter
        self.assertEqual(Counter(x['report']['sourceDocumentDisposition'] for x in self.rows), {'agreed': 5, 'revised': 2})
        self.assertEqual(len(self.rows), 7)

    def test_selected_meetings_scope_and_electronic_alias(self):
        self.assertEqual([x['target'] for x in s.validated_records(self.root, 'RAN5', {'RAN5#998'})
                          if x.get('kind') != 'document'], ['R5-990205'])
        self.assertEqual(s.validated_records(self.root, 'RAN5', {'RAN5#1'}), [])
        self.assertEqual(c.validated_corrections(self.root, 'RAN5', {'RAN5#1'}), [])

    def test_no_fabricated_dates_contacts_or_prior_metadata(self):
        nodes = s.supplement_instances(self.root, 'RAN5', [], self.references, set())
        self.assertEqual(nodes, [])
        all_nodes, _, _ = self.source_overlay()
        wanted = {x['target'] for x in self.rows}
        for node in all_nodes:
            if node['tdoc:tdocNumber'] in wanted:
                self.assertNotIn('tdoc:reservationDate', node)
                self.assertNotIn('tdoc:uploadedDate', node)
                self.assertNotIn('hasContact', node)
                self.assertEqual(node['@type'], 'tdoc:CR')

    def test_company_alias_and_electronic_meeting_are_exact_existing_ids(self):
        nodes, _, _ = self.source_overlay()
        n = next(x for x in nodes if x['tdoc:tdocNumber'] == 'R5-990201')
        self.assertEqual(n['submittedBy'], ['tdoc:company/Example_Company'])
        self.assertEqual(n['presentedAt'], 'tdoc:meeting/RAN5_999-e')
        self.assertEqual(n['targetRelease'], 'tdoc:release/Rel_17')

    def test_complete_report_span_and_disposition_cannot_be_forged(self):
        row = copy.deepcopy(self.rows[0]); row['report']['entry'].pop()
        with self.assertRaises(s.SupplementError): s.validate_record(self.root, row)
        row = copy.deepcopy(next(x for x in self.rows if x['target'] == 'R5-990102'))
        row['report']['sourceDocumentDisposition'] = 'agreed'
        with self.assertRaises(s.SupplementError): s.validate_record(self.root, row)

    def test_cover_and_sha_cannot_be_forged(self):
        row = copy.deepcopy(self.rows[0]); row['sourceIdentity']['release'] = 'Rel-19'
        with self.assertRaises(s.SupplementError): s.validate_record(self.root, row)
        row = copy.deepcopy(self.rows[0]); row['sha256'] = '0' * 64
        with self.assertRaises(s.SupplementError): s.validate_record(self.root, row)

    def test_fourteen_identity_rows_and_four_chain_nodes_are_distinct(self):
        from collections import Counter
        self.assertEqual(Counter(x['scope'] for x in self.corrections), {'spreadsheet_cover_identity': 14, 'missing_intermediate_revision_chain': 4})

    def test_target_release_comes_from_cover_field_not_current_version(self):
        row = next(x for x in self.corrections if x['target'] == 'R5-992100')
        self.assertEqual(row['deltas'][0]['sourceBackedValue'], 'tdoc:release/Rel_15')
        bad = copy.deepcopy(row); bad['deltas'][0]['sourceBackedValue'] = 'tdoc:release/Rel_14'
        with self.assertRaises(s.SupplementError): c.validate_correction(self.root, bad)

    def test_immediate_revision_chain_keeps_all_three_documents_distinct(self):
        nodes, _, _ = self.source_overlay(); index = {x['@id']: x for x in nodes}
        for prior, middle, final in [('R5-990101', 'R5-990102', 'R5-990103'), ('R5-990104', 'R5-990105', 'R5-990106')]:
            p, m, f = ['tdoc:' + x for x in (prior, middle, final)]
            self.assertEqual(index[p]['revisedTo'], m)
            self.assertEqual(index[m]['isRevisionOf'], p)
            self.assertEqual(index[m]['revisedTo'], f)
            self.assertEqual(index[f]['isRevisionOf'], m)
            self.assertEqual(len({p, m, f}), 3)
        self.assertEqual(index['tdoc:R5-990103']['tdoc:crRevision'], '2')

    def test_overlay_is_idempotent_and_preserves_unrelated_properties(self):
        nodes, _, _ = self.source_overlay()
        old = copy.deepcopy(nodes)
        self.assertEqual(s.supplement_instances(self.root, 'RAN5', nodes, self.references, self.selected), [])
        self.assertEqual(c.overlay_identity_corrections(self.root, 'RAN5', nodes, self.references, self.selected), [])
        self.assertEqual(nodes, old)
        before = {x['@id']: x for x in self.instances}
        deltas = {(f'tdoc:{row["target"]}', d['field']) for row in self.corrections for d in row['deltas']}
        for node in nodes:
            if node['@id'] in before:
                for field, value in before[node['@id']].items():
                    if (node['@id'], field) not in deltas:
                        self.assertEqual(node[field], value)

    def test_unreviewed_canonical_identity_fails_closed(self):
        nodes, _, _ = self.source_overlay()
        next(n for n in nodes if n['tdoc:tdocNumber'] == 'R5-992101')['tdoc:crNumber'] = '9999'
        with self.assertRaises(s.SupplementError): c.overlay_identity_corrections(self.root, 'RAN5', nodes, self.references, self.selected)

    def test_count_baseline_is_explicit_ledger_addition(self):
        from collections import Counter
        additions = Counter(r.get('canonicalClass', 'CR') for r in s.validated_records(self.root, 'RAN5'))
        baseline = {'CR': 40, 'Tdoc': 10}
        expected = {**baseline, **{kind: baseline.get(kind, 0) + count for kind, count in additions.items()}}
        self.assertEqual(s.legacy_expected_counts(self.root, 'RAN5', baseline), expected)


class NativeDocumentTests(SyntheticSourceInputs):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rows = cls.native_rows
        s.ledger_path(cls.root, 'RAN5').write_text(json.dumps({'schema': 1, 'wg': 'RAN5', 'records': cls.rows}))

    def test_actual_native_identities_have_separate_cr_family_ls_and_tdoc_classes(self):
        from collections import Counter
        self.assertEqual(Counter(row['canonicalClass'] for row in self.rows), {'Tdoc': 24, 'CR': 4, 'LS': 3})
        selected = {node['tdoc:meetingNumber'] for node in self.references['meetings']}
        # The temporary ledger contains only native documents in this fixture.
        nodes = s.supplement_instances(self.root, 'RAN5', [], self.references, selected)
        self.assertEqual(len(nodes), 31)
        for node in nodes:
            self.assertNotIn('tdoc:reservationDate', node)
            self.assertNotIn('isRevisionOf', node)
            if node['tdoc:type'] == 'pCR':
                self.assertEqual(node['@type'], 'tdoc:CR')
                self.assertNotIn('tdoc:crNumber', node)
                self.assertIn('modifies', node)
            if node['@type'] == 'tdoc:LS':
                self.assertEqual(node['tdoc:direction'], 'out')

    def test_cover_substring_is_not_an_exact_native_document_identity(self):
        row = copy.deepcopy(next(r for r in self.rows if r['target'] == 'R5-993001'))
        row['target'] += '1'
        row['sourceIdentity']['tdocNumber'] = row['target']
        with self.assertRaises(s.SupplementError):
            s.validate_record(self.root, row)

    def test_named_approved_output_is_distinct_from_its_revised_predecessor(self):
        row = copy.deepcopy(next(r for r in self.rows if r['target'] == 'R5-993002'))
        self.assertEqual(row['report']['sourceDocumentDisposition'], 'agreed')
        self.assertTrue(row['report']['quote'].startswith('R5-994002'))
        row['report']['sourceDocumentDisposition'] = 'revised'
        with self.assertRaises(s.SupplementError):
            s.validate_record(self.root, row)

    def test_a_past_history_mention_cannot_prove_current_document_identity(self):
        row = copy.deepcopy(next(r for r in self.rows if r['target'] == 'R5-993003'))
        row['target'] = 'R5-994003'
        row['sourceIdentity']['tdocNumber'] = row['target']
        with self.assertRaises(s.SupplementError):
            s.validate_record(self.root, row)

    def test_native_view_requires_original_to_derived_lineage(self):
        row = copy.deepcopy(next(r for r in self.rows if r['target'] == 'R5-993004'))
        row['nativeView']['conversionLineage']['sourceSha256'] = '0' * 64
        with self.assertRaises(ValueError):
            s.validate_record(self.root, row)

    def test_ran3_correction_reads_assigned_identity_in_accepted_tracked_changes(self):
        rows = c.validated_corrections(self.root, 'RAN3')
        self.assertEqual({row['target'] for row in rows}, {'R3-995001', 'R3-995002', 'R3-995003'})
        tracked = next(row for row in rows if row['target'] == 'R3-995003')
        self.assertTrue(any('| 0314 |' in item['quote'] for item in tracked['review']['actualDocumentEvidence']))
        self.assertEqual(c.validate_correction(self.root, tracked), tracked)

    def test_ran3_overlay_corrects_only_enumerated_release_fields(self):
        directory = self.root / 'ontology/output/tsg/RAN/formal/instances/phase-1/RAN3'
        nodes = json.loads((directory / 'tdocs.jsonld').read_text())['@graph']
        references = s.reference_graphs(directory)
        targets = {row['target'] for row in c.validated_corrections(self.root, 'RAN3')}
        for node in nodes:
            if node['tdoc:tdocNumber'] in targets:
                node['targetRelease'] = 'tdoc:release/Rel_15'
        before = copy.deepcopy(nodes)
        changed = c.overlay_identity_corrections(self.root, 'RAN3', nodes, references,
            {meeting['tdoc:meetingNumber'] for meeting in references['meetings']})
        self.assertEqual(len(changed), 3)
        for old, new in zip(before, nodes):
            expected = dict(old, targetRelease='tdoc:release/Rel_16') if old['tdoc:tdocNumber'] in targets else old
            self.assertEqual(new, expected)


if __name__ == '__main__':
    unittest.main()
