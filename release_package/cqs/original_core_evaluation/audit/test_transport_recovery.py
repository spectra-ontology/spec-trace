import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

spec=importlib.util.spec_from_file_location('recovery',Path(__file__).resolve().parents[1]/'transport_recovery.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


class FakeResponse:
    status=200
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self):return json.dumps({'provider':'Anthropic','model':'synthetic-model','choices':[{'message':{'content':'{"query":"SELECT 1","abstain":false}'},'finish_reason':'stop'}],'usage':{'cost':.01}}).encode()


class RecoveryTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);self.old=self.base/'old';self.new=self.base/'new';self.old.mkdir();self.new.mkdir()
        self.payload={'model':'synthetic-model','messages':[{'role':'user','content':'fixture'}],'max_tokens':20,'provider':{'only':['Anthropic']},'response_format':{'type':'json_object'},'reasoning':{'enabled':False},'stream':False}

    def tearDown(self):self.tmp.cleanup()

    def error(self,status=402,source='openrouter_in_flight_budget',choices=None):
        value={'error':{'code':status,'metadata':{'limit_source':source}}}
        if choices is not None:value['choices']=choices
        return {'http_status':status,'response':value}

    def original(self,error):
        request=self.old/'calls/fixture.request.json';r.write(request,{'request_id':'fixture','payload':self.payload,'payload_sha256':hashlib.sha256(r.serialized(self.payload)).hexdigest()})
        response=self.old/'calls/fixture.attempt0.response.json';r.write(response,error)
        r.write(self.old/'calls/fixture.outcome.json',{'ok':False,'attempts':[{'response_path':str(response)}]})
        return request

    def test_403_key_limit_and_402_exact_source_only(self):
        self.assertTrue(r.exact_budget_rejection(self.error()))
        self.assertTrue(r.exact_budget_rejection(self.error(403,'openrouter_key_limit')))
        self.assertFalse(r.exact_budget_rejection(self.error(403,'guardrail')))
        self.assertFalse(r.exact_budget_rejection(self.error(402,'openrouter_credits')))
        self.assertFalse(r.exact_budget_rejection(self.error(402,choices=[{'message':{'content':'real'}}])))

    def test_original_choice_prevents_eligibility(self):
        self.original(self.error(402,choices=[{'message':{'content':'real'}}]))
        self.assertFalse(r.eligible(self.old,'fixture'))

    def test_replay_has_identical_payload_and_one_new_model_output(self):
        self.original(self.error());transport=r.RecoveryTransport(self.old,self.new,'synthetic-secret',5,6)
        sent=[]
        def fake(req,timeout):sent.append(req.data);return FakeResponse()
        with patch.object(r.urllib.request,'urlopen',side_effect=fake):value=transport.replay('fixture')
        self.assertTrue(value['ok']);self.assertEqual(sent,[r.serialized(self.payload)])
        self.assertEqual(len(value['attempts']),1)
        self.assertTrue(r.read(self.new/'calls/fixture.request.json')['identical_original_payload'])

    def test_changed_payload_is_rejected_before_network(self):
        request=self.original(self.error());transport=r.RecoveryTransport(self.old,self.new,'synthetic-secret',5,6)
        changed=dict(self.payload,max_tokens=21)
        with patch.object(r.urllib.request,'urlopen') as call:
            with self.assertRaises(ValueError):transport.call_payload('fixture',changed,original_request=request)
            call.assert_not_called()

    def test_three_402_replays_max_no_quality_retry(self):
        self.original(self.error());transport=r.RecoveryTransport(self.old,self.new,'synthetic-secret',5,6);transport.await_cooldown=lambda:None
        def rejected(req,timeout):raise urllib.error.HTTPError('fixture',402,'fixture',{'Retry-After':'120'},io.BytesIO(json.dumps(self.error()['response']).encode()))
        with patch.object(r.urllib.request,'urlopen',side_effect=rejected) as call:value=transport.replay('fixture')
        self.assertEqual(call.call_count,3);self.assertEqual(value['error'],'http_402');self.assertEqual(len(value['attempts']),3)

    def test_zero_added_budget_makes_no_paid_call(self):
        self.original(self.error());transport=r.RecoveryTransport(self.old,self.new,'synthetic-secret',5,5)
        with patch.object(r.urllib.request,'urlopen') as call:value=transport.replay('fixture');call.assert_not_called()
        self.assertEqual(value['error'],'aggregate_original_plus_recovery_budget_guard')

    def test_paid_start_without_confirmation_rejected_before_credentials(self):
        with self.assertRaises(ValueError):r.run(self.old,self.new,self.base,20,False)

    def test_repeated_key_limit403_is_not_automatically_retried(self):
        self.original(self.error(403,'openrouter_key_limit'));transport=r.RecoveryTransport(self.old,self.new,'synthetic-secret',5,6)
        def rejected(req,timeout):raise urllib.error.HTTPError('fixture',403,'fixture',{},io.BytesIO(json.dumps(self.error(403,'openrouter_key_limit')['response']).encode()))
        with patch.object(r.urllib.request,'urlopen',side_effect=rejected) as call:value=transport.replay('fixture')
        self.assertEqual(call.call_count,1);self.assertEqual(value['error'],'http_403')


if __name__=='__main__':unittest.main()
