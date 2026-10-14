import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

S=importlib.util.spec_from_file_location('offline_recovery_check',Path(__file__).with_name('recovery_validation.py'))
M=importlib.util.module_from_spec(S);S.loader.exec_module(M)


class RecoveryValidationTest(unittest.TestCase):
    def fixture(self,root,*,code=402,source='openrouter_in_flight_budget',choices=False):
        calls=root/'calls';calls.mkdir();request=calls/'fixture.request.json'
        request.write_text('{}');raw=calls/'fixture.attempt0.response.json'
        response={'error':{'code':code,'metadata':{'limit_source':source}}}
        if choices:response['choices']=[{'message':{'content':'real malformed output'}}]
        raw.write_text(json.dumps({'http_status':code,'response':response}))
        (calls/'fixture.outcome.json').write_text(json.dumps({'ok':False,'attempts':[{'response_path':'/old/machine/'+raw.name}]}))

    def test_exact402_and403_with_portable_paths(self):
        for code,source in [(402,'openrouter_in_flight_budget'),(403,'openrouter_key_limit')]:
            with tempfile.TemporaryDirectory() as d:
                self.fixture(Path(d),code=code,source=source)
                self.assertTrue(M.original_eligible(Path(d),'fixture'))

    def test_any_real_original_choices_bar_recovery(self):
        with tempfile.TemporaryDirectory() as d:
            self.fixture(Path(d),choices=True)
            self.assertFalse(M.original_eligible(Path(d),'fixture'))

    def test_generic403_not_eligible(self):
        with tempfile.TemporaryDirectory() as d:
            self.fixture(Path(d),code=403,source='provider_error')
            self.assertFalse(M.original_eligible(Path(d),'fixture'))

    def test_changed_payload_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);old=root/'old.json';new=root/'new.json';payload={'messages':[{'role':'user','content':'original question'}]}
            pin=hashlib.sha256(M.serial(payload)).hexdigest();prior={'request_id':'fixture','payload':payload,'payload_sha256':pin}
            old.write_text(json.dumps(prior));now=dict(prior,original_request_sha256=M.sha(old));new.write_text(json.dumps(now))
            self.assertTrue(all(M.payload_identity(old,new).values()))
            now['payload']['messages'][0]['content']='changed question';now['payload_sha256']=hashlib.sha256(M.serial(now['payload'])).hexdigest();new.write_text(json.dumps(now))
            self.assertFalse(M.payload_identity(old,new)['same_payload_bytes'])


if __name__=='__main__':unittest.main()
