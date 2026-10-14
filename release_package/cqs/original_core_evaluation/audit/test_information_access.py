import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('audit_tool', Path(__file__).with_name('information_access.py'))
audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)


class AuditTest(unittest.TestCase):
    def setUp(self):
        self.con = sqlite3.connect(':memory:')
        self.con.execute('CREATE TABLE docs(id INTEGER PRIMARY KEY,collection TEXT,point_id TEXT,chunk_id TEXT,text TEXT)')
        self.con.execute("CREATE VIRTUAL TABLE search USING fts5(text,content='docs',content_rowid='id')")
        self.con.execute("INSERT INTO docs VALUES(1,'fixture','p1','c1','A source document R1-2500001 cites an item.')")
        self.con.execute("INSERT INTO search(search) VALUES('rebuild')")

    def tearDown(self):
        self.con.close()

    def test_literal_presence_does_not_certify_semantics(self):
        value = audit.probe(self.con, 'R1-2500001')
        self.assertEqual(value['status'], 'literal_presence_observed')
        self.assertFalse(value['semantic_answer_support_established'])

    def test_negative_probe_does_not_claim_absence(self):
        value = audit.probe(self.con, 'R1-2500002')
        self.assertEqual(value['status'], 'presence_not_established')
        self.assertTrue(value['candidate_read_complete'])
        self.assertFalse(value['semantic_answer_support_established'])

    def test_anchors_exclude_numeric_answers_and_company_names(self):
        gold = {'records': [{'count': 4, 'company': 'Ericsson', 'id': 'R1-2500001'},
                            {'id': 'R1-2500001'}, {'id': 'AGR-100-a-001'}]}
        self.assertEqual(audit.documentary_anchors(gold, 3), ['R1-2500001', 'AGR-100-a-001'])

    def test_anchor_limit_is_deterministic(self):
        self.assertEqual(audit.documentary_anchors({'records': [{'id': 'R1-2500001'}, {'id': 'R2-2500002'}]}, 1), ['R1-2500001'])

    def test_recursive_private_evidence_is_rejected(self):
        self.assertEqual(audit.forbidden_paths({'contract': {'fields': [{'source_column_or_expression': 'n.id'}]}}), ['/contract/fields/0/source_column_or_expression'])

    def test_missing_request_is_pending(self):
        with tempfile.TemporaryDirectory() as d:
            value = audit.audit_request(Path(d), {'id': 'fixture'}, 'A', 'Text2Cypher', None, None)
            self.assertEqual(value['status'], 'not_present_yet')

    def test_missing_stage_after_completion_is_not_leakage_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'generation_complete.json').write_text('{}')
            value=audit.audit_request(root,{'id':'fixture'},'D','D_answer',None,None)
            self.assertEqual(value['status'],'not_issued_in_complete_generation')

    def test_cached_request_resolves_actual_original_without_new_call(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);old=root/'original';new=root/'supplement';(old/'calls').mkdir(parents=True);new.mkdir()
            path=old/'calls/fixture_Text2SQL.request.json';path.write_text('{}')
            (new/'protocol.json').write_text(json.dumps({'transport_recovery':{'original_run':str(old)}}))
            found,mode=audit.effective_request_path(new,'fixture','Text2SQL')
            self.assertEqual(found,path);self.assertEqual(mode,'cached_actual_original_request_no_new_call')

    def test_partial_written_request_is_pending(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'calls/fixture_Text2Cypher.request.json';p.parent.mkdir();p.write_text('{')
            value = audit.audit_request(Path(d), {'id': 'fixture'}, 'A', 'Text2Cypher', None, None)
            self.assertEqual(value['status'], 'unreadable_pending')

    def test_only_exact_preprovider_budget_pair_is_transient_class(self):
        with tempfile.TemporaryDirectory() as d:
            calls=Path(d)/'calls';calls.mkdir()
            for n,source,code in [('yes','openrouter_in_flight_budget',402),
                                 ('credits','openrouter_credits',402),
                                 ('wrongcode','openrouter_in_flight_budget',403)]:
                value={'request_id':n,'http_status':402,'response':{'error':{'code':code,'metadata':{'limit_source':source}}}}
                (calls/(n+'.attempt0.response.json')).write_text(json.dumps(value))
            report=audit.transport_information(Path(d))
            self.assertEqual(report['distinct_requests_rejected_for_inflight_budget'],1)
            self.assertEqual(report['response_attempt_status_counts']['402'],3)

    def test_exact403_key_limit_is_separate_class(self):
        with tempfile.TemporaryDirectory() as d:
            calls=Path(d)/'calls';calls.mkdir()
            for n,source in [('key','openrouter_key_limit'),('other','provider_error')]:
                value={'request_id':n,'http_status':403,'response':{'error':{'code':403,'metadata':{'limit_source':source}}}}
                (calls/(n+'.attempt0.response.json')).write_text(json.dumps(value))
            report=audit.transport_information(Path(d))
            self.assertEqual(report['distinct_requests_rejected_for_key_limit'],1)

    def test_bad_serialized_private_JSON_is_failure(self):
        class SyntheticStructured:
            @staticmethod
            def messages_for(task,arm):
                return [{'role':'system','content':'fixture'}, {'role':'user','content':'{"question":"fixture"}'}]
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'calls').mkdir();(root/'schemas').mkdir()
            (root/'schemas/RAN1_graph.json').write_text('{"labels":[]}')
            payload={'messages':[{'role':'system','content':'fixture'}, {'role':'user','content':'{"question":"fixture","gold":[1]}'}]}
            value={'payload':payload,'payload_sha256':audit.hashlib.sha256(json.dumps(payload,ensure_ascii=False).encode()).hexdigest()}
            (root/'calls/fixture_Text2Cypher.request.json').write_text(json.dumps(value))
            result=audit.audit_request(root,{'id':'fixture','wg':'RAN1'},'A','Text2Cypher',SyntheticStructured,None)
            self.assertEqual(result['status'],'FAIL')
            self.assertEqual(result['private_evidence_keys_in_caller_authored_JSON'],['/gold'])


if __name__ == '__main__':
    unittest.main()
