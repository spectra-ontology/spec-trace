"""Synthetic development checks, not benchmark measurements or model outputs."""
import copy
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import types
import unittest
from unittest.mock import patch

import build_frozen_sqlite as builder
import structured_adapter as adapter

ROOT=Path(__file__).resolve().parents[4]
LOADER=Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/pipeline/load_released_kg.py')
TOY='''@prefix spectra: <https://w3id.org/spectra#> .
<https://w3id.org/spectra/inst/RAN1/CR/a> a spectra:CR, spectra:Tdoc ;
 spectra:id "001" ; spectra:rank 7 ; spectra:ratio 1.0 ; spectra:isVoid false ;
 spectra:tags "b", "a" ; spectra:note "line\\nnext" ;
 spectra:references <https://w3id.org/spectra/inst/RAN1/Tdoc/a>, <https://w3id.org/spectra/inst/RAN1/Tdoc/a> .
<https://w3id.org/spectra/inst/RAN1/Tdoc/a> a spectra:Tdoc ; spectra:id "001" ; spectra:isVoid true .
'''


class MockCaller:
    def __init__(self,content='{"query":"RETURN 1 AS n","abstain":false}',finish_reason='stop'):
        self.content=content;self.finish_reason=finish_reason;self.messages=None;self.max_tokens=None
    def call(self,request_id,messages,max_tokens):
        self.messages=messages;self.max_tokens=max_tokens
        return {'ok':True,'content':self.content,'provider':'synthetic-mock',
                'finish_reason':self.finish_reason,'usage':{},'error':None}


class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.base=Path(cls.temp.name)
        cls.ttl=cls.base/'RAN1-body.ttl';cls.ttl.write_text(TOY)
        cls.db=cls.base/'RAN1.sqlite'
        cls.manifest=builder.build(cls.ttl,cls.db,LOADER,expected_inventory=(2,1))
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def task(self):
        return {'id':'RAN1_SYNTHETIC','repair_sha256':'fixture','question_en':'Return the count.',
                'required_fields':[{'name':'n','type':'integer','nullable':False}],
                'collection':{'kind':'set'},'cardinality_policy':{'mode':'exact','value':1},
                'graph_schema':{'labels':['Tdoc'],'properties_by_label':{'Tdoc':{}},'directed_relationships':[]},
                'sql_schema':self.manifest['schema']}
    def sql(self,q,fields=None,**kw):
        return adapter.run_sql_query(self.db,q,fields or [],expected_db_sha=self.manifest['db_sha256'],**kw)
    def test_exact_source_registry(self):
        self.assertEqual(self.manifest['complete_native_record_sha256'],self.manifest['complete_sql_record_sha256'])
        self.assertEqual(self.manifest['complete_source_edge_sha256'],self.manifest['complete_sql_edge_sha256'])
    def test_no_business_identifier_merge(self):
        self.assertEqual(self.sql('SELECT count(*) AS n FROM node')['rows'],[{'n':2}])
    def test_multilabel_shared_identity(self):
        rows=self.sql('SELECT c.node_id FROM CR c JOIN Tdoc t USING(node_id)')['rows']
        self.assertEqual(len(rows),1)
    def test_duplicate_edge_policy(self):
        self.assertEqual(self.manifest['raw_relationship_occurrences'],2)
        self.assertEqual(self.manifest['identical_directed_edges_collapsed'],1)
        self.assertEqual(self.sql('SELECT count(*) AS n FROM rel_REFERENCES')['rows'],[{'n':1}])
    def test_numeric_string_not_coerced(self):
        self.assertEqual(self.sql('SELECT id,typeof(id) AS storage FROM CR')['rows'],[{'id':'001','storage':'text'}])
    def test_float_type_preserved(self):
        self.assertEqual(self.sql('SELECT ratio,typeof(ratio) AS storage FROM CR')['rows'],[{'ratio':1.0,'storage':'real'}])
    def test_boolean_predeclared_decode(self):
        rows=self.sql('SELECT isVoid FROM CR',[{'name':'isVoid','type':'boolean'}])['rows']
        self.assertEqual(rows,[{'isVoid':False}]);self.assertIs(type(rows[0]['isVoid']),bool)
    def test_array_predeclared_decode(self):
        self.assertEqual(self.sql('SELECT tags FROM CR',[{'name':'tags','type':'json'}])['rows'],[{'tags':['a','b']}])
    def test_missing_property_null(self):
        self.assertEqual(self.sql('SELECT ratio FROM Tdoc WHERE ratio IS NULL')['rows'],[{'ratio':None}])
    def test_private_identity_table_denied(self):
        self.assertEqual(self.sql('SELECT * FROM _node_record')['status'],'ERROR')
    def test_batch_identity_guard(self):
        stat=adapter.file_identity(self.db)
        result=self.sql('SELECT count(*) AS n FROM CR',source_guard_batch_verified=True,expected_db_stat=stat)
        self.assertEqual(result['status'],'OK');self.assertTrue(result['source_guard_batch_verified'])
        bad=dict(stat,mtime_ns=stat['mtime_ns']+1)
        self.assertEqual(self.sql('SELECT 1',source_guard_batch_verified=True,expected_db_stat=bad)['status'],'SOURCE_MISMATCH')
    def test_mutation_denied(self):
        for q in ['DELETE FROM CR','ATTACH DATABASE "x" AS x','PRAGMA schema_version','SELECT load_extension("x")','WITH c AS (SELECT 1) DELETE FROM CR']:
            self.assertNotEqual(self.sql(q)['status'],'OK')
        self.assertEqual(self.sql('SELECT count(*) AS n FROM CR')['rows'],[{'n':1}])
    def test_two_statements_denied(self):
        self.assertEqual(self.sql('SELECT 1; SELECT 2')['status'],'ERROR')
    def test_cap_explicit(self):
        r=self.sql('SELECT node_id FROM node',row_cap=1)
        self.assertEqual(r['status'],'ROW_CAP');self.assertFalse(r['complete']);self.assertTrue(r['truncated'])
    def test_byte_cap_explicit(self):
        self.assertEqual(self.sql('SELECT id FROM CR',byte_cap=1)['status'],'BYTE_CAP')
    def test_full_exact_boundary_not_truncated(self):
        r=self.sql('SELECT node_id FROM node',row_cap=2)
        self.assertEqual(r['status'],'OK');self.assertTrue(r['complete'])
    def test_timeout_explicit(self):
        r=self.sql('WITH RECURSIVE x(n) AS (SELECT 0 UNION ALL SELECT n+1 FROM x) SELECT n FROM x',timeout_s=0.002)
        self.assertEqual(r['status'],'TIMEOUT');self.assertFalse(r['complete'])
    def test_nested_records(self):
        q='SELECT json_object("items",json_array(1,2),"valid",json("true")) AS payload FROM CR'
        rows=self.sql(q,[{'name':'payload','type':'json'}])['rows']
        self.assertEqual(rows,[{'payload':{'items':[1,2],'valid':True}}])
    def test_nested_boolean_declared_codec(self):
        field={'name':'payload','type':'json','json_schema':{'type':'object','properties':{
             'valid':{'type':'boolean'},'n':{'type':'integer'},'id':{'type':'string'},
             'items':{'type':'array','items':{'type':['boolean','null']}}}}}
        rows=adapter.decode_sql_record({'payload':'{"valid":0,"n":1,"id":"001","items":[1,null]}'},[field])
        self.assertEqual(rows,{'payload':{'valid':False,'n':1,'id':'001','items':[True,None]}})
        self.assertIs(type(rows['payload']['n']),int)
    def test_ambiguous_numeric_boolean_no_guess(self):
        self.assertIs(type(adapter.decode_json_sql(1,{'type':['integer','boolean']})),int)
    def test_private_input_rejected(self):
        t=self.task();t['reference_query']='secret'
        with self.assertRaises(ValueError):adapter.messages_for(t,'A')
    def test_contract_auxiliary_not_prompted(self):
        t=self.task();t['required_fields'][0]['source_column_or_expression']='private_alias'
        t['collection']={'kind':'native_ordered_ties','source_order_keys':[{'source_column':'secret_sort_alias','direction':'desc'}]}
        rendered=json.dumps(adapter.messages_for(t,'A'))
        self.assertNotIn('private_alias',rendered);self.assertNotIn('secret_sort_alias',rendered)
    def test_generate_deferred_and_one_shot(self):
        with tempfile.TemporaryDirectory() as out:
            caller=MockCaller();r=adapter.evaluate(self.task(),'A',caller,out)
            self.assertEqual(r['status'],'QUERY_READY');self.assertIsNone(r['execution'])
            self.assertEqual(caller.max_tokens,4096)
            with self.assertRaises(ValueError):adapter.evaluate(self.task(),'A',caller,out)
    def test_truncated_model_never_executed(self):
        with tempfile.TemporaryDirectory() as out:
            r=adapter.evaluate(self.task(),'A',MockCaller(finish_reason='length'),out)
            self.assertEqual(r['status'],'GENERATION_TRUNCATED')
    def test_invalid_query_envelope(self):
        with tempfile.TemporaryDirectory() as out:
            r=adapter.evaluate(self.task(),'A',MockCaller('{"query":"x","abstain":"false"}'),out)
            self.assertEqual(r['status'],'GENERATION_FORMAT_ERROR')
    def graph_fixture(self,rows=None,plan_type='r',execution_type='r',row_cap=100000):
        """All graph/container calls mocked; no server or scientific data."""
        rows=rows or [{'n':1},{'n':2}]
        state={'rollback':False,'queries':[],'owned_guards':0,'summaries':0}
        counter=types.SimpleNamespace(contains_updates=False,contains_system_updates=False)
        summary=lambda kind:types.SimpleNamespace(query_type=kind,counters=counter,plan={})
        class Cursor:
            def __init__(self,explain):self.explain=explain
            def keys(self):return ['n']
            def __iter__(self):return iter([types.SimpleNamespace(data=lambda row=row:row) for row in rows])
            def consume(self):
                state['summaries']+=1
                return summary(plan_type if self.explain else execution_type)
        class Tx:
            def run(self,q):state['queries'].append(q);return Cursor(q.startswith('EXPLAIN '))
            def rollback(self):state['rollback']=True
        class Session:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def begin_transaction(self,**kw):return Tx()
        class Driver:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def session(self,**kw):return Session()
        expected={'wg':'RAN1','import_manifest_sha256':'fixture'}
        executor=types.SimpleNamespace(source_guard=lambda wg:expected,PORTS={'RAN1':57687})
        def owned(wg):state['owned_guards']+=1
        def require(plan):
            if plan.query_type!='r':raise ValueError('synthetic nonread plan')
        guard=types.SimpleNamespace(screen_query=lambda q:q,owned_container_guard=owned,require_read_plan=require)
        fake_neo4j=types.SimpleNamespace(GraphDatabase=types.SimpleNamespace(driver=lambda *a,**kw:Driver()),READ_ACCESS='READ')
        with patch.dict('sys.modules',{'neo4j':fake_neo4j}), \
             patch.object(adapter.importlib.util,'module_from_spec',side_effect=[executor,guard]), \
             patch.object(adapter.importlib.util,'spec_from_file_location',return_value=types.SimpleNamespace(loader=types.SimpleNamespace(exec_module=lambda mod:None))):
            result=adapter.run_cypher_query('RAN1','RETURN 1 AS n',self.base,source_guard_expected=expected,row_cap=row_cap)
        return result,state
    def test_graph_ordinary_read_and_rollback(self):
        result,state=self.graph_fixture()
        self.assertEqual(result['status'],'OK');self.assertTrue(result['execution_summary_complete'])
        self.assertTrue(result['rollback_completed']);self.assertTrue(state['rollback'])
        self.assertEqual(state['owned_guards'],2);self.assertEqual(state['summaries'],2)
    def test_graph_nonread_plan_rejected_before_execution(self):
        result,state=self.graph_fixture(plan_type='rw')
        self.assertEqual(result['status'],'ERROR');self.assertEqual(len(state['queries']),1)
        self.assertTrue(result['rollback_completed'])
    def test_graph_nonread_execution_rejected(self):
        result,state=self.graph_fixture(execution_type='rw')
        self.assertEqual(result['status'],'ERROR');self.assertFalse(result['execution_summary_complete'])
        self.assertTrue(result['rollback_completed'])
    def test_graph_capped_output_incomplete(self):
        result,state=self.graph_fixture(row_cap=1)
        self.assertEqual(result['status'],'ROW_CAP');self.assertFalse(result['complete'])
        self.assertFalse(result['execution_summary_complete']);self.assertTrue(result['rollback_completed'])


if __name__=='__main__':unittest.main()
