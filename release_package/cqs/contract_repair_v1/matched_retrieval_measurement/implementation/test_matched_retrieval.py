"""Offline tests; never launch a model or connect to Qdrant."""
import multiprocessing
import tempfile
import time
import unittest
from pathlib import Path
import matched_retrieval as m


def reserve_worker(directory, component, queue):
    m.OUT=Path(directory)
    caller=m.Caller({'protocol':{'overall_call_cap':3,'component_call_caps':{'retrieval':2,'kg':1}}},component=component)
    queue.put(caller.reserve(component))


def slot_worker(directory, queue):
    m.OUT=Path(directory)
    handle=m.Caller.acquire_slot()
    start=time.monotonic()
    time.sleep(0.05)
    end=time.monotonic()
    handle.close()
    queue.put((start,end))


class OfflineTest(unittest.TestCase):
    def test_shared_component_and_overall_cap(self):
        with tempfile.TemporaryDirectory(prefix='matched_counter_test_') as directory:
            queue=multiprocessing.Queue()
            workers=[multiprocessing.Process(target=reserve_worker,args=(directory,c,queue)) for c in ('retrieval','retrieval','retrieval','kg','kg')]
            for p in workers:p.start()
            for p in workers:p.join(5);self.assertEqual(p.exitcode,0)
            values=[queue.get(timeout=1) for _ in workers]
            self.assertEqual(sorted(x for x in values if x is not None),[1,2,3])
            self.assertEqual(len(list((Path(directory)/'calls').glob('*.reservation.json'))),3)

    def test_shared_two_slots(self):
        with tempfile.TemporaryDirectory(prefix='matched_slots_test_') as directory:
            (Path(directory)/'calls').mkdir()
            queue=multiprocessing.Queue()
            workers=[multiprocessing.Process(target=slot_worker,args=(directory,queue)) for _ in range(4)]
            for p in workers:p.start()
            for p in workers:p.join(5);self.assertEqual(p.exitcode,0)
            intervals=[queue.get(timeout=1) for _ in workers]
            events=sorted([(a,1) for a,b in intervals]+[(b,-1) for a,b in intervals])
            active=peak=0
            for t,change in events:active+=change;peak=max(peak,active)
            self.assertEqual(peak,2)

    def test_reader_excludes_gold_reference_and_hidden_cardinality(self):
        task={'id':'synthetic','wg':'ran1','task_question':'Which documents?',
              'reference_query':'SECRET-CYPHER','gold':['SECRET-GOLD'],
              'required_fields':[{'name':'doc','type':'string','role':'document identifier','source_anchor':'SECRET-ANCHOR'}],
              'collection_kind':'set','constraints':[{'kind':'cardinality','value':999}]}
        safe=m.sanitize_task(task)
        prompt=m.prompt_for(m.FINAL_INSTRUCTION,safe,[])
        for secret in ('SECRET-CYPHER','SECRET-GOLD','SECRET-ANCHOR','999'):
            self.assertNotIn(secret,prompt)
        self.assertEqual(set(m.output_schema(safe)['properties']),{'records','abstain'})

    def test_typed_output_keeps_bool_distinct_from_integer(self):
        schema={'type':'object','properties':{'n':{'type':'integer'}},'required':['n'],'additionalProperties':False}
        m.validate_output({'n':1},schema)
        for output in ({'n':True},{'n':'1'}, {}, {'n':1,'extra':'x'}):
            with self.assertRaises(ValueError):m.validate_output(output,schema)

    def test_explicit_json_fields_validate_nested_types(self):
        fields=[{'name':'affectedSpecs','type':'json','role':'sorted unique specification identifiers',
                 'json_schema':{'type':'array','items':{'type':'string'}}},
                {'name':'topCompanies','type':'json','role':'ordered companies and counts',
                 'json_schema':{'type':'array','items':{'type':'object',
                     'properties':{'company':{'type':'string'},'count':{'type':'integer'}},
                     'required':['company','count'],'additionalProperties':False}}}]
        task=m.sanitize_task({'id':'synthetic_json','wg':'ran1','task_question':'Use the declared fields.',
                              'required_fields':fields,'collection_kind':'set'})
        schema=m.output_schema(task)
        valid={'records':[{'affectedSpecs':['TS 1'], 'topCompanies':[{'company':'A','count':1}]}], 'abstain':False}
        m.validate_output(valid,schema)
        for specs,companies in (([1],[{'company':'A','count':1}]),
                                (['TS 1'],[{'company':'A','count':True}]),
                                (['TS 1'],[{'company':'A','count':'1'}]),
                                (['TS 1'],[{'company':'A','count':1,'gold':'SECRET'}]),
                                (['TS 1'],[{'company':'A'}])):
            with self.assertRaises(ValueError):
                m.validate_output({'records':[{'affectedSpecs':specs,'topCompanies':companies}],'abstain':False},schema)
        for banned_key in ('const','enum','examples','description'):
            unsafe={'type':'array','items':{'type':'string'},banned_key:'SECRET'}
            with self.assertRaises(ValueError):m.sanitize_json_schema(unsafe)

    def test_public_export_excludes_raw_transport(self):
        record={'stderr':'SECRET-TRANSPORT','events':[{'header':'SECRET-HEADER'}],
                'error':'ValueError: SECRET-EXCEPTION','output':{'records':[],'abstain':True}}
        exported=m.export_public_call(record)
        self.assertNotIn('SECRET',str(exported))
        self.assertEqual(exported['error_category'],'ValueError')


if __name__=='__main__':unittest.main()
