import copy
import importlib.util
from pathlib import Path
import unittest

S=importlib.util.spec_from_file_location('redaction',Path(__file__).resolve().parents[1]/'public_redaction.py')
M=importlib.util.module_from_spec(S);S.loader.exec_module(M)


class RedactionTest(unittest.TestCase):
    def test_financial_error_redaction_keeps_transport_semantics(self):
        value={'http_status':403,'received_utc':'fixture-timestamp','response':{'error':{'code':403,'message':'Key limit exceeded: $7.12 spent',
          'metadata':{'limit_source':'openrouter_key_limit','scope':'key','limit_usd':7,'spend_usd':7.12,'resets_at':None}},'choices':[]}}
        original=copy.deepcopy(value);new,changes=M.redact_json(value)
        self.assertEqual(value,original);self.assertEqual(new['http_status'],403)
        self.assertEqual(new['response']['error']['code'],403);self.assertEqual(new['response']['error']['metadata']['limit_source'],'openrouter_key_limit')
        self.assertEqual(new['received_utc'],'fixture-timestamp');self.assertEqual(new['response']['choices'],[])
        self.assertNotIn('$',new['response']['error']['message']);self.assertEqual(len(changes),4)
        self.assertTrue(all(set(c)=={'json_pointer','reason'} for c in changes))

    def test_experiment_usage_parameters_and_gold_values_unchanged(self):
        value={'usage':{'cost':.123,'prompt_tokens':6},'max_tokens':8192,'budget_guard_usd':6,
               'records':[{'balance':42,'count':4}],'response':{'choices':[{'message':{'content':'{"records":[1]}'}}]},'timestamp':'fixture'}
        new,changes=M.redact_json(value);self.assertEqual(new,value);self.assertEqual(changes,[])

    def test_private_account_query_data(self):
        value={'endpoint':'https://openrouter.ai/api/v1/key','http_status':200,'data':{'label':'private','limit':7,'usage':4,'limit_remaining':3},'timestamp':'fixture'}
        new,changes=M.redact_json(value);self.assertEqual(new['data'],M.SENTINEL);self.assertEqual(new['http_status'],200)
        self.assertEqual(changes,[{'json_pointer':'/data','reason':'private_provider_account_query'}])

    def test_private_credits_shape_without_endpoint(self):
        new,changes=M.redact_json({'data':{'total_credits':7,'total_usage':4}})
        self.assertEqual(new['data'],M.SENTINEL);self.assertEqual(len(changes),1)

    def test_402_retry_after_preserved(self):
        value={'error':{'code':402,'message':'In-flight budget exhausted','metadata':{'limit_source':'openrouter_in_flight_budget','reason':'in_flight_budget_exhausted','headers':{'Retry-After':'120'},'provider_name':'fixture'}}}
        new,changes=M.redact_json(value);self.assertEqual(new,value);self.assertEqual(changes,[])

    def test_credential_scanner_never_returns_secret(self):
        fake='sk-or-v1-'+('SYNTHETIC'*8);value={'body':fake,'Authorization':'Bearer fixture','safe':'OPENROUTER_API_KEY'}
        findings=M.scan_credentials(value,[fake]);self.assertEqual(len(findings),3)
        self.assertNotIn(fake,str(findings));self.assertTrue(all(set(f)=={'json_pointer','kind'} for f in findings))

    def test_json_pointer_escape_and_idempotence(self):
        value={'a/b':{'error':{'message':'balance: 3','metadata':{'balance':3}}}}
        new,changes=M.redact_json(value);self.assertEqual(changes[0]['json_pointer'],'/a~1b/error/metadata/balance')
        twice,again=M.redact_json(new);self.assertEqual(twice,new);self.assertEqual(again,[])


if __name__=='__main__':unittest.main()
