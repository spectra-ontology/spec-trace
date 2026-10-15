#!/usr/bin/env python3
"""Offline exact six-task request, parser, and saved read-guard reconstruction."""
import argparse,ast,hashlib,importlib.util,json,sys,tempfile
from pathlib import Path
sys.dont_write_bytecode=True
IDS={'RAN2_P2_CQ2-1','RAN1_P3_CQ026','RAN3_P2_CQ1-6','RAN4_P2_CQ1-6','RAN2_P2_CQ2-5','RAN1_P2_CQ4-2'}
def load(p):return json.loads(p.read_text())
def rows(p):return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(evidence,out):
    assert not out.exists(), 'Preserve prior proof/failure'
    cur,rt=evidence/'current',evidence/'runtime';protocol=load(cur/'protocol.json')
    public={t['id']:t for t in rows(cur/'public_tasks.jsonl')};assert set(public)==IDS
    assert {v['wg'] for v in public.values()}=={'RAN1','RAN2','RAN3','RAN4'}
    for name,pin in protocol['code_pins'].items():assert sha(rt/name)==pin,name
    sys.path.insert(0,str(rt));spec=importlib.util.spec_from_file_location('auth9_saved_structured',rt/'structured_adapter.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    functions={'canonical','structural_schema','public_contract','parse_answer'};constants={'QUERY_INSTRUCTION','ANSWER_INSTRUCTION'};selected=[]
    for n in ast.parse((rt/'retrieval_adapter.py').read_text()).body:
        if isinstance(n,ast.FunctionDef) and n.name in functions:selected.append(n)
        elif isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in constants for t in n.targets):selected.append(n)
    retr={'json':json};exec(compile(ast.Module(body=selected,type_ignores=[]),'<pinned auth9 retrieval projection>','exec'),retr);assert functions|constants<=set(retr)
    expected={};structured={}
    for ident,p in public.items():
        for arm,kind,tag in [('A','graph','Text2Cypher'),('B','sql','Text2SQL')]:
            task=dict(p);task[kind+'_schema']=load(cur/'schemas'/(p['wg']+'_'+kind+'.json'));structured[(ident,tag)]=task;expected[ident+'_'+tag]=adapter.messages_for(task,arm)
        for arm in ['C','D']:
            base=cur/'retrieval'/arm/ident;initial,final=load(base/'initial_context.json'),load(base/'final_context.json');prefix=retr['canonical']({'question':p['question_en'],'contract':retr['public_contract'](p)})+'\nSOURCE PASSAGES:\n'
            if arm=='D':expected[ident+'_D_followup']=[{'role':'system','content':retr['QUERY_INSTRUCTION']},{'role':'user','content':prefix+'\n\n'.join(d['formatted'] for d in initial['documents'])}]
            expected[ident+'_'+arm+'_answer']=[{'role':'system','content':retr['ANSWER_INSTRUCTION']},{'role':'user','content':prefix+'\n\n'.join(d['formatted'] for d in final['documents'])}]
    requests={load(p)['request_id']:load(p) for p in (cur/'calls').glob('*.request.json')};assert set(requests)==set(expected) and len(expected)==30
    outcomes={}
    for rid,r in requests.items():assert r['payload']['messages']==expected[rid],rid;outcomes[rid]=load(cur/'calls'/(rid+'.outcome.json'))
    class SavedCaller:
        def call(self,request_id,messages,**kwargs):assert messages==expected[request_id];return outcomes[request_id]
    parser_n=0;parse_failures=0;structured_n=0;read_guards=[];statuses={}
    for ident,p in public.items():
        statuses[ident]={}
        for method,tag in [('text2cypher','Text2Cypher'),('text2sql','Text2SQL')]:
            saved=load(cur/'predictions'/tag/(ident+'.json'));exe=load(cur/'executed'/method/(ident+'.json'))
            with tempfile.TemporaryDirectory(prefix='spectra-auth9-offline-parser-') as td:replay=adapter.evaluate(structured[(ident,tag)],tag,SavedCaller(),Path(td))
            assert replay==saved,(ident,tag,'generation parser');structured_n+=1
            if replay['status']!='QUERY_READY':assert adapter.execute_generated(replay,p)==exe;read_guards.append({'id':ident,'method':tag,'status':exe['status'],'not_executed_nonready_passthrough':True})
            else:
                assert exe['generated_query']==replay['generated_query'] and exe['query_sha256']==replay['query_sha256'];ex=exe['execution'];assert ex is not None
                assert exe['records']==(ex['rows'] if ex['complete'] else []) and exe['abstain']==(not ex['complete'])
                guard={'id':ident,'method':tag,'status':exe['status'],'complete':ex['complete'],'truncated':ex['truncated']}
                if ex['complete']:
                    assert exe['status']=='OK' and not ex['truncated']
                    if tag=='Text2Cypher':assert ex['plan_query_type']==ex['execution_query_type']=='r' and ex['rollback_completed'] and ex['execution_summary_complete'];guard['actual_read_plan_summary_rollback']=True
                    else:assert ex['immutable_read_only'] is True;guard['actual_immutable_read_only']=True
                else:guard['partial_rows_not_scored']=True
                read_guards.append(guard)
            statuses[ident][method]=exe['status'];parser_n+=1
        for method,arm in [('single_retrieval','C'),('iterative_retrieval','D')]:
            result=load(cur/'arm_outputs'/method/(ident+'.json'));o=outcomes[ident+'_'+arm+'_answer']
            if not o.get('ok') or o.get('finish_reason') in {'length','max_tokens'}:
                assert result['records']==[] and result['status'].upper() in {'GENERATION_ERROR','ANSWER_TRUNCATED','GENERATION_TRUNCATED','ERROR'}
            else:
                try:parsed=retr['parse_answer'](o['content'])
                except (ValueError,TypeError,KeyError) as error:assert result['status'].upper()=='ANSWER_PARSE_ERROR' and result['records']==[] and result['error']==str(error);parse_failures+=1
                else:assert result['status'].upper()==('ABSTAINED' if parsed['abstain'] else ('OK' if parsed['complete'] else 'PARTIAL')) and result['records']==parsed['records']
            statuses[ident][method]=result['status'];parser_n+=1
    assert structured_n==len(read_guards)==12 and parser_n==24
    for wg in {'RAN1','RAN2','RAN3','RAN4'}:
        g=load(cur/'source_guards'/(wg+'.json'));assert g['before']==g['after']==protocol['graph_sources'][wg]
    receipt={'status':'EXACT30_PROMPTS_ALL24_OUTPUT_PARSERS_AND12_STRUCTURED_READ_GUARD_PATHS_REPLAY_PASS','protocol_sha256':sha(cur/'protocol.json'),'evaluation_manifest_sha256':sha(evidence/'manifest.json'),'question_n':6,'working_groups_n':4,'prompt_reconstruction_n':30,'output_parser_replay_n':24,'structured_generation_parser_replay_n':12,'retrieval_parse_failure_replay_n':parse_failures,'saved_structured_read_guard_paths':read_guards,'actual_statuses':statuses,'new_model_or_database_calls_n':0,'limitations':'Incomplete/error executions retain original failure status and empty scored records; guard assertions apply to successful actual reads. Saved generation/parser replay does not reexecute queries or prove optional commentary truth.'}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.evidence.resolve(),a.out.resolve())
