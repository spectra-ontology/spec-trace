"""Offline synthetic execution-reuse gates; no DB or model calls."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import unittest

PATH=Path(__file__).resolve().parents[1]/'execute_transport_supplement.py'
SPEC=importlib.util.spec_from_file_location('execution_supplement',PATH)
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)


class ReuseTest(unittest.TestCase):
    def setUp(self):
        self.task={'id':'RAN1_SYNTHETIC','repair_sha256':'repair'}
        self.g={'id':self.task['id'],'repair_sha256':'repair','method':'Text2Cypher','wg':'RAN1',
                'status':'QUERY_READY','abstain':False,'generated_query':'MATCH (n) RETURN count(n)',
                'query_sha256':hashlib.sha256(b'MATCH (n) RETURN count(n)').hexdigest(),
                'adapter_sha256':'adapter','prompt_sha256':'prompt'}
        self.e=dict(self.g,status='OK',execution={'status':'OK','complete':True,'rows':[{'n':3}]},records=[{'n':3}])

    def test_exact_actual_success_reuse(self):
        self.assertTrue(M.reusable(self.g,dict(self.g,transport_provenance={'mode':'cache'}),self.e,self.task))

    def test_actual_failure_reuse_without_quality_rerun(self):
        failed=dict(self.e,status='ERROR',execution={'status':'ERROR','complete':False,'rows':[]},records=[])
        self.assertTrue(M.reusable(self.g,self.g,failed,self.task))

    def test_different_query_cannot_reuse(self):
        new=dict(self.g,generated_query='MATCH (n) RETURN n',query_sha256=hashlib.sha256(b'MATCH (n) RETURN n').hexdigest())
        self.assertFalse(M.reusable(self.g,new,self.e,self.task))

    def test_changed_repair_prompt_adapter_cannot_reuse(self):
        for field in ['repair_sha256','prompt_sha256','adapter_sha256']:
            with self.subTest(field=field):self.assertFalse(M.reusable(self.g,dict(self.g,**{field:'changed'}),self.e,self.task))

    def test_generation_query_hash_tamper_rejected(self):
        bad=dict(self.g,query_sha256='bad')
        self.assertFalse(M.reusable(bad,bad,dict(self.e,query_sha256='bad'),self.task))

    def test_old_execution_different_query_rejected(self):
        self.assertFalse(M.reusable(self.g,self.g,dict(self.e,generated_query='RETURN 99'),self.task))

    def test_missing_actual_execution_rejected(self):
        self.assertFalse(M.reusable(self.g,self.g,dict(self.e,execution=None),self.task))

    def test_cached_nonready_has_no_db_execution_requirement(self):
        g=dict(self.g,status='GENERATION_ERROR',generated_query=None,query_sha256=None,abstain=True)
        self.assertTrue(M.reusable(g,g,dict(g,execution=None),self.task))

    def test_source_guard_exact(self):
        before={'wg':'RAN1','source':{'sha256':'ttl'},'nodes':1,'relationships':2}
        p={'graph_sources':{'RAN1':before}}
        guard={'before':before,'after':copy.deepcopy(before),'unchanged':True,'sql_sha256':'db'}
        M.verify_original_guard(guard,p,'RAN1','db')
        bad=copy.deepcopy(guard);bad['after']['nodes']=2
        with self.assertRaises(ValueError):M.verify_original_guard(bad,p,'RAN1','db')
        with self.assertRaises(ValueError):M.verify_original_guard(guard,p,'RAN1','different')


if __name__=='__main__':unittest.main()
