"""Offline replay of the finite PDCCH recorded-decision contract.

Included XML is source-bound own-window evidence. Full original reports and the
whole frozen graph are not reopened by this default, standard-library replay.
"""
import sys
if sys.flags.optimize:
    raise SystemExit('Optimized Python disables required verification checks')
import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import xml.etree.ElementTree as E

INVENTORY_SHA='9965cb88c7d5130c7c5879b9bb24faaec921430422f65fbf515ce241a362ed18'
CRITERIA_SHA='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
REPAIR_SHA='f3cfeda047bc3144c45c02e6e5ef1919515d6c6f42b1443bd2b1b0bbc5e1a210'
QUERY_SHA='84d9c0897fa48c358d92c0accfa45be47cbde864d2bd606862934dddd66c086b'
ID='RAN1_P2_CQ1-6'
ROOT=Path(__file__).absolute().parent
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
sha=lambda b:hashlib.sha256(b).hexdigest()
canon=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def regular_path(p):
    for x in [p,*p.parents]:
        if x.is_symlink():raise ValueError('symlink rejected before target read')
    if not p.is_file():raise ValueError('regular file required')
def read(name):
    p=ROOT/name;regular_path(p);return p.read_bytes()
def js(name):return json.loads(read(name))
def jl(name):return [json.loads(x)for x in read(name).decode().splitlines()if x]
def module(name,file):
    p=ROOT/file;regular_path(p)
    spec=importlib.util.spec_from_file_location(name,p)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def own(text):
    if text is None:return None
    lines=text.split('\n')
    for i,line in enumerate(lines):
        if not re.fullmatch(r'R1-[0-9]{7}\t.*',line):continue
        attached=(i+1<len(lines) and re.fullmatch(r'\(Rel-[0-9]+,.*\bCR[0-9]+.*\) is agreed\.',lines[i+1].strip())
                  and any(re.fullmatch(r'(?i).*(?:final\s+CRs?\s+in|comeback\s+for\s+final\s+CR).*',old)for old in lines[:i]))
        if not attached:return '\n'.join(lines[:i])
    return text
def main():
    for p in [ROOT,*ROOT.parents]:
        if p.is_symlink():raise ValueError('entry or ancestor symlink rejected')
    invb=read('immutable_inventory.json');assert sha(invb)==INVENTORY_SHA
    inv=json.loads(invb);assert inv['id']==ID
    expected={x['path']:x for x in inv['files']}
    assert len(expected)==len(inv['files'])
    meta={'README.md','manifest.json','immutable_inventory.json','reproduce.py'}
    actual=set()
    for p in ROOT.rglob('*'):
        if p.is_symlink():raise ValueError('tree symlink rejected')
        if p.is_file():actual.add(p.relative_to(ROOT).as_posix())
        elif not p.is_dir():raise ValueError('nonregular tree entry rejected')
    assert actual==set(expected)|meta,'closed file set differs'
    for name,info in expected.items():
        b=read(name);assert len(b)==info['bytes']and sha(b)==info['sha256'],name
    manifest=js('manifest.json')
    assert set(manifest)=={'artifact_type','id','new_admissions','model_calls','inventory_sha256','files','scope'}
    assert manifest['artifact_type']=='local_recorded_decision_contract_evidence'
    assert manifest['id']==ID and type(manifest['new_admissions'])is int and manifest['new_admissions']==0
    assert type(manifest['model_calls'])is int and manifest['model_calls']==0
    assert manifest['inventory_sha256']==INVENTORY_SHA
    assert canon(manifest['files'])==canon(inv['files'])
    assert manifest['scope']=='finite original graph-record question; not full physical-table or current-standard completeness'
    definition=js('contract/definition.json');assert len(definition)==9
    assert sha(canon(definition))==REPAIR_SHA
    q=js('contract/original_question.json')
    assert definition['id']==q['id']==ID
    assert definition['question_en']==q['question_en']
    assert sha(q['question_en'].encode())==q['question_sha256']
    assert definition['original_query']==q['original_query']
    assert sha(q['original_query'].encode())==q['query_sha256']
    assert sha(definition['reference_query'].encode())==QUERY_SHA
    assert sha(read('contract/criteria.json'))==CRITERIA_SHA
    criteria=js('contract/criteria.json')
    checker=module('pdcch_review_schema','scoring/review_schema.py')
    for f in ['contract/primary.json','contract/secondary.json']:
        checker.check_pass(js(f),q['question_en'],criteria['semantic_units'],criteria_sha=CRITERIA_SHA,identity_key='repair_sha256',identity_sha=REPAIR_SHA)
    assert definition['required_fields']==[{'name':'content','type':'string','nullable':False,'source_column_or_expression':'content'}]
    assert definition['collection']=={'kind':'multiset'}
    assert definition['cardinality_policy']=={'mode':'exact','value':10}
    db=js('source/frozen47_generic_projection.json')
    assert len(db['all_original_candidates'])==47 and db['database_before']==db['database_after']
    assert db['database_before']['sha256']=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
    rows=[]
    for r in db['all_original_candidates']:
        f=own(r['content'])
        if 'PDCCH'in f and 'blind'in f:
            x=dict(r);x['own_filter']=f
            x['content']=own(r['contentWithEquations']if r['contentWithEquations']is not None else r['content'])+('\n'+r['note']if r['note']else '')
            rows.append(x)
    rows.sort(key=lambda r:(-r['meetingNumberInt'],r['resolutionId']))
    assert len(rows)==42
    selected=rows[:10]
    full=[{'a.resolutionId':r['resolutionId'],'m.meetingNumber':r['meetingNumber'],'content':r['content']}for r in selected]
    assert canon(full)==canon(jl('execution/independent_SQL_all3.jsonl'))
    native=js('execution/native_case.json');values=jl('execution/native_rows.jsonl')
    columns=['a.resolutionId','m.meetingNumber','content']
    assert native['id']==ID and native['query_sha256']==QUERY_SHA
    assert native['query']==definition['reference_query']and native['columns']==columns
    assert native['status']=='OK'and native['truncated']is False and native['rollback_completed']is True
    assert native['plan_query_type']==native['execution_query_type']=='r'
    assert native['execution_summary_complete']is True
    assert native['rows_retained']==10 and sha(read('execution/native_rows.jsonl'))==native['rows_sha256']
    assert canon([dict(zip(columns,v))for v in values])==canon(full)
    ex=js('execution/native_execution.json');assert ex['source_before']==ex['source_after']and ex['inventory_unchanged']is True
    assert ex['source_before']['source']['sha256']=='9540683df5407bb3f8978ad4d05ddc7f7880f10c94f21273f588d737f145e231'
    outer=js('execution/outer_guard.json');assert outer['status']=='PASS'and outer['child_exit']==0
    assert outer['owned_cleanup']['owned_stopped']is True
    panels=json.loads(gzip.decompress(read('source/selected10_own_XML_panels.json.gz')))
    meta=js('source/selected10_source_metadata.json')['checks']
    assert len(meta)==10 and {r['resolutionId']for r in meta}=={r['resolutionId']for r in selected}
    norm=lambda s:re.sub(r'\s+','',s)
    plain=lambda e:''.join(t.text or ''for t in e.iter(W+'t'))
    totalruns=0;colored=[];deleted=[];inserted=[]
    for rec in meta:
        r=next(x for x in selected if x['resolutionId']==rec['resolutionId'])
        blocks=[x for x in panels if x['resolutionId']==rec['resolutionId']]
        assert [x['raw_body_child0']for x in blocks]==list(range(*rec['own_source_range']))
        elements=[E.fromstring(x['XML'])for x in blocks]
        stylebytes=gzip.decompress(read('source/styles_'+rec['source_DOCX']['sha256']+'.xml.gz'))
        assert sha(stylebytes)==rec['styles_XML_sha256']
        styles=E.fromstring(stylebytes)
        sm={e.get(W+'styleId'):e for e in styles.findall(W+'style')};closure=set()
        def add(k):
            if k in closure:return
            assert k in sm;closure.add(k)
            base=sm[k].find(W+'basedOn')
            if base is not None:add(base.get(W+'val'))
        for s in sm.values():
            if s.get(W+'default')in('1','true','on'):add(s.get(W+'styleId'))
        for el in elements:
            for tag in ('pStyle','rStyle','tblStyle'):
                for s in el.iter(W+tag):add(s.get(W+'val'))
        flags=('strike','dstrike','vanish','webHidden')
        assert not any(list(sm[k].iter(W+f))for k in closure for f in flags)
        defaults=styles.find(W+'docDefaults')
        assert defaults is None or not any(list(defaults.iter(W+f))for f in flags)
        for index,el in enumerate(elements):
            assert not list(el.iter(M+'oMath'))
            parents={child:parent for parent in el.iter()for child in parent}
            for runindex,run in enumerate(el.iter(W+'r')):
                totalruns+=1;rp=run.find(W+'rPr');anc=[];cur=run
                while cur in parents:
                    cur=parents[cur];anc.append(cur.tag.removeprefix(W))
                dtext=''.join(x.text or ''for x in run.iter(W+'delText'))
                if any(x in anc for x in ('del','moveFrom'))or dtext:
                    deleted.append((rec['resolutionId'],blocks[index]['raw_body_child0'],runindex,dtext))
                    assert not plain(run),'Deleted visible text requires additional semantic review'
                if any(x in anc for x in ('ins','moveTo')):
                    inserted.append((rec['resolutionId'],plain(run)))
                if rp is not None:
                    for f in flags:
                        assert not any(x.get(W+'val','true').casefold()not in('0','false','off','no')for x in rp.findall(W+f))
                    col=rp.find(W+'color')
                    if col is not None and col.get(W+'val')not in('000000','auto'):colored.append(plain(run))
            text=plain(el)
            if index==0:text=re.sub(r'^Agreements?\s*:?[\s]*','',text,count=1,flags=re.I)
            units=[plain(c)for row in el.findall(W+'tr')for c in row.findall(W+'tc')]if el.tag==W+'tbl'else [text]
            assert all(norm(u)in norm(r['content'])for u in units if u.strip()),rec['resolutionId']
    assert totalruns==480 and colored==['intra-frequency',' ','inter-frequency']
    assert deleted==[('AGR-103-8.6.2-017',5668,7,'[??%-??%] '),('AGR-103-8.6.2-017',5668,10,'['),('AGR-103-8.6.2-017',5668,11,'??%~??%'),('AGR-103-8.6.2-017',5668,12,']')]
    assert ''.join(text for rid,text in inserted if rid=='AGR-103-8.6.2-017')=='[1.16%~4.60%][2.32%~7.20%]'
    upd=next(r for r in selected if r['resolutionId']=='AGR-103-8.6.2-017')['content']
    assert all(x in upd for x in ['[1.16%~4.60%]','[2.32%~7.20%]','2.85%','5.66%'])
    assert '[??%-??%]'not in upd and '[??%~??%]'not in upd
    coarse=js('source/coarse_equivalent_recovery.json')
    assert norm('PDCCH blind decoding capability in the first MCG and second MCG') in norm(selected[-1]['content'])
    assert coarse['coarse_recovery_observed']is True and coarse['physical104_perFS_or_event_recovered']is False
    requested=[{'content':r['content']}for r in selected]
    assert canon(requested)==canon(jl('execution/requested_records.jsonl'))
    scorer=module('pdcch_unchanged_scorer','scoring/scorer.py')
    score=scorer.score(definition,requested,requested,diagnostic=True);assert score['exact']is True
    controls=js('execution/typed_controls.json');assert controls['n']==12
    for item in controls['checks']:assert item['actual']['exact']is item['expected_exact']
    # Actual independent recomputation of minimum adverse typed-answer controls.
    assert scorer.score(definition,requested,requested[:-1],diagnostic=True)['exact']is False
    assert scorer.score(definition,requested,[{}]+requested[1:],diagnostic=True)['exact']is False
    assert scorer.score(definition,requested,[{'content':1}]+requested[1:],diagnostic=True)['exact']is False
    assert scorer.score(definition,requested,[{'content':'not the decision'}]+requested[1:],diagnostic=True)['exact']is False
    return {'status':'PASS','cases':[{'id':ID,'records':10,'native_full_columns':3,'source_own_runs':480,'source_OMML':0,'tracked_deleted_placeholder_runs':4,'typed_controls':12}],'new_admissions':0,'model_calls':0,'scope':'Saved immutable47-row projection, ten included XML own windows/styles, exact native and typed-scorer replay. Full original30 reports/whole graph not reopened.'}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.parse_args()
    print(json.dumps(main(),ensure_ascii=False))
