"""Replay retained styled-Section identities, complete saved query dependencies,
exact saved native23 rows and typed scorer controls. No native/model/network is run.
Optional explicit --source-root reopens exactly23 pinned original sources.
"""
import sys
if sys.flags.optimize:
    raise SystemExit('Run without -O/-OO; checks must remain enabled.')
import argparse
import ast
from collections import Counter,defaultdict
from decimal import Decimal,ROUND_HALF_UP
import gzip
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as E
import zipfile
sys.dont_write_bytecode=True
ID='RAN3_P3_CQ5-3'
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
EXPECTED_INVENTORY_SHA='da77464861e7439ded3e9ce05cc9ada99f5eaad7b53a3353ff8eb3f55b178893'
EXPECTED_META={'id': 'RAN3_P3_CQ5-3', 'artifact_type': 'prospective_original_question_source_and_reference_evidence', 'status': 'LOCAL_SOURCE_AND_REFERENCE_GATES_PASS_PENDING_ROOT_SEAL', 'repair_sha256': '7e87afba8d5a79ab6a1cbf5789588c5ae775c4a85b371196529bf68bf3215480', 'criteria_sha256': 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'original_question_preserved': True, 'question_sha256': 'b8e9a37945729c62d0313b112208beb875f030c9cb1ebe46f470dbbbdfb6ae3b', 'query_sha256': 'bcfc0c7a0eab89d2c12e530db5c9c45ab1fec25b118776893aa837afff0eb56f', 'reference_rows': 23, 'native_columns': 4, 'required_fields': 2, 'source_editions': 23, 'styled_Section_identities': 4017, 'expert_validation_n': 0, 'new_model_calls': 0, 'new_native_runs_in_packet_replay': 0, 'original560_increment': 0, 'admitted': False, 'readme_sha256': '0a78e7dcf9b6be947fe3ce1921277246eec6e26a6d0e971613998e5e263c81e5'}
META={'manifest.json','immutable_payload_inventory.json','README.md','verify_source_evidence.py'}
def no_links(p):
    p=Path(p).absolute()
    for x in [p,*p.parents]:
        if x.is_symlink():raise ValueError('Symlink path prohibited: '+str(x))
    return p
ROOT=no_links(Path(__file__).absolute().parent)
no_links(Path(__file__).absolute())
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def same(a,b):return canon(a)==canon(b)
def read(n):return json.loads((ROOT/n).read_bytes())
def module(n,p):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def text(n):
    return ''.join((x.text or '')if x.tag==W+'t'else '\t'if x.tag==W+'tab'else '\n'if x.tag in(W+'br',W+'cr')else ''for x in n.iter())
def tree(n):return [n.tag,sorted(n.attrib.items()),n.text or '',[[tree(c),c.tail or '']for c in n]]
def bootstrap():
    for p in ROOT.rglob('*'):
        no_links(p)
        if not(p.is_file()or p.is_dir()):raise ValueError('Nonregular entry')
    b=(ROOT/'immutable_payload_inventory.json').read_bytes()
    if sha(b)!=EXPECTED_INVENTORY_SHA:raise ValueError('Immutable inventory changed')
    inv=json.loads(b)
    files={p.relative_to(ROOT).as_posix()for p in ROOT.rglob('*')if p.is_file()}
    if files!=set(inv)|META:raise ValueError('Closed file inventory mismatch')
    dirs={a.as_posix()for n in files for a in Path(n).parents}
    for p in ROOT.rglob('*'):
        if p.is_dir()and p.relative_to(ROOT).as_posix()not in dirs:raise ValueError('Unexpected directory')
    for n,pin in inv.items():
        raw=(ROOT/n).read_bytes()
        if len(raw)!=pin['bytes']or sha(raw)!=pin['sha256']:raise ValueError('Immutable payload changed: '+n)
    manifest=read('manifest.json')
    if not same({k:v for k,v in manifest.items()if k!='files'},EXPECTED_META):raise ValueError('Metadata claims changed')
    if sha((ROOT/'README.md').read_bytes())!=manifest['readme_sha256']:raise ValueError('README changed')
    expected=dict(inv)
    for n in META-{'manifest.json'}:
        data=(ROOT/n).read_bytes();expected[n]={'bytes':len(data),'sha256':sha(data)}
    if not same(expected,manifest['files']):raise ValueError('Outer map changed')
    return manifest
def grammar():
    raw=(ROOT/'source/original_parse_ts_docx.py').read_bytes()
    assert sha(raw)=='f97e02094416d137353a44853aaf5512f7becaa8f71b99e09f33721d344f1e31'
    names={'HEADING_LEVEL_MAP','ANNEX_STYLES','BODY_NUM_RE','ANNEX_NUM_RE','ASN1_NAME_RE','ANNEX_HEADING_RE'}
    selected=[]
    for n in ast.parse(raw).body:
        if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id in names for t in n.targets):selected.append(n)
        if isinstance(n,ast.FunctionDef)and n.name=='parse_heading_text':selected.append(n)
    env={'re':re};exec(compile(ast.Module(body=selected,type_ignores=[]),'<pinned_original_pure_heading_grammar>','exec'),env)
    assert names<=set(env)and callable(env['parse_heading_text'])
    return env
def styles(raw):
    return {s.get(W+'styleId'):s.find(W+'name').get(W+'val')for s in E.fromstring(raw).findall(W+'style')if s.find(W+'name')is not None}
def canonical_style(s):
    s=s or ''
    return 'Heading '+s.split()[-1]if s.lower().startswith('heading ')else s
def validate_heading(h,stylemap,env):
    raw=h['XML'].encode();assert sha(raw)==h['XML_sha256']
    n=E.fromstring(raw);ps=n.find('./'+W+'pPr/'+W+'pStyle');sid=ps.get(W+'val')if ps is not None else None
    sty=canonical_style(stylemap.get(sid,sid))
    assert sid==h['styleId']and sty==h['canonical_style']and sty in env['HEADING_LEVEL_MAP']
    num,title=env['parse_heading_text'](text(n).strip(),sty)
    assert num==h['sectionNumber']and title==h['title']
    assert any(env[k].match(num)for k in ('BODY_NUM_RE','ANNEX_NUM_RE','ASN1_NAME_RE'))
    return num
def derive_all_original_headings(doc,stylemap,env):
    out=[];seen=set();coord=-1;stack=[]
    for event,n in E.iterparse(io.BytesIO(doc),events=('start','end')):
        if event=='start':stack.append(n.tag);continue
        if n.tag==W+'p'and len(stack)>1 and stack[-2]==W+'body':
            coord+=1;ps=n.find('./'+W+'pPr/'+W+'pStyle');sid=ps.get(W+'val')if ps is not None else None
            sty=canonical_style(stylemap.get(sid,sid))
            if sty in env['HEADING_LEVEL_MAP']:
                num,title=env['parse_heading_text'](text(n).strip(),sty)
                if num and any(env[k].match(num)for k in ('BODY_NUM_RE','ANNEX_NUM_RE','ASN1_NAME_RE'))and num not in seen:
                    seen.add(num);out.append((coord,num,title,tree(n)))
            n.clear()
        stack.pop()
    return out
def verify_sources(data,source_root=None):
    assert data['id']==ID and len(data['sources'])==23
    env=grammar();total=0;byedition={};outlines={}
    for s in data['sources']:
        assert s['release']=='Rel-19'
        sty=s['styles_xml_utf8'].encode();assert sha(sty)==s['styles_xml_sha256'];sm=styles(sty)
        hs=s['source_original_styled_rule_headings'];numbers=[validate_heading(h,sm,env)for h in hs]
        assert len(set(numbers))==len(numbers)
        ids={s['specNumber']+'-'+s['release']+'-'+n for n in numbers}
        frozen=s['frozen_Sections'];assert len({x['node_id']for x in frozen})==len(frozen)
        assert len({x['sectionId']for x in frozen})==len(frozen)
        assert ids=={x['sectionId']for x in frozen}
        assert len(hs)==len(frozen)==s['styled_source_heading_count']==s['frozen_Section_count']
        assert not s['source_only_original_styled_identities']and not s['frozen_only_identities']
        cover=s['cover_version_addendum'];cp=cover['actual_cover'];assert sha(cp['XML'].encode())==cp['XML_sha256']
        assert text(E.fromstring(cp['XML'])).strip()==cp['text']
        assert re.search(re.escape(s['specNumber'])+r'\s*V'+re.escape(cp['cover_version']),cp['text'])
        assert cover['frozen_specVersion']==s['frozen_specVersion']
        if s['frozen_specVersion']is not None:assert s['frozen_specVersion']==cp['cover_version']
        else:assert s['specNumber']=='38.471'and cp['cover_version']=='19.0.0'
        for h in s['direct_outline_supplement_candidates_not_adopted']:
            raw=h['XML'].encode();assert sha(raw)==h['XML_sha256'];n=E.fromstring(raw)
            assert n.find('./'+W+'pPr/'+W+'pStyle')is None
            ol=n.find('./'+W+'pPr/'+W+'outlineLvl');assert ol is not None and ol.get(W+'val')==h['direct_outline']
            num,title=env['parse_heading_text'](text(n).strip(),'Heading '+str(int(h['direct_outline'])+1))
            assert num==h['sectionNumber']and title==h['title']and num not in numbers
            outlines.setdefault(s['specNumber'],[]).append(num)
        if source_root is not None:
            dp=no_links(source_root/s['DOCX']['path']);b=dp.read_bytes();assert len(b)==s['DOCX']['bytes']and sha(b)==s['DOCX']['sha256']
            ap=no_links(source_root/s['archive']['path']);a=ap.read_bytes();assert len(a)==s['archive']['bytes']and sha(a)==s['archive']['sha256']
            with zipfile.ZipFile(io.BytesIO(a))as z:
                zi=z.getinfo(s['member']['name']);assert zi.CRC==s['member']['CRC']and zi.file_size==s['member']['file_size']and z.read(zi)==b
            with zipfile.ZipFile(io.BytesIO(b))as z:
                doc=z.read('word/document.xml');st=z.read('word/styles.xml')
                assert sha(doc)==s['document_xml']['sha256']and len(doc)==s['document_xml']['bytes']and z.getinfo('word/document.xml').CRC==s['document_xml']['CRC']
                assert st==sty
            derived=derive_all_original_headings(doc,sm,env)
            assert derived==[(h['direct_body_paragraph_index'],h['sectionNumber'],h['title'],tree(E.fromstring(h['XML'])))for h in hs]
        assert s['edition_node_id']not in byedition;byedition[s['edition_node_id']]=s
        total+=len(hs)
    assert total==4017 and outlines=={'38.460':['9'],'38.470':['5.2.17']}
    return byedition,{'latest_editions':23,'original_styled_identities':total,'physical_outline_only_counterexamples':outlines,'optional_whole_DOCX_reopened':23 if source_root else 0}
def reconstruct_density(proj,byedition):
    assert proj['id']==ID and len(proj['abstract_positive_hubs'])==117 and len(proj['counted_CR_MODIFIES_paths'])==19537 and len(proj['all_release_edges_of_positive_hubs'])==115
    hubs={h['node_id']:h for h in proj['abstract_positive_hubs']};assert len(hubs)==117
    assert all(h['specRelease']is None for h in hubs.values())
    paths=proj['counted_CR_MODIFIES_paths'];assert len({p['edge_id']for p in paths})==19537
    crs=defaultdict(list);types=Counter()
    for p in paths:
        assert p['dst_id']in hubs and p['type']in {'CR','pCR','draftCR'}and p['Tdoc_role_type']==p['type']
        crs[p['dst_id']].append(p);types[p['type']]+=1
    assert set(crs)==set(hubs)and dict(types)=={'CR':13961,'pCR':2883,'draftCR':2693}
    for ps in crs.values():assert len(ps)==len({p['src_id']for p in ps})==len({p['tdocNumber']for p in ps})
    editions=defaultdict(list)
    for e in proj['all_release_edges_of_positive_hubs']:
        assert e['dst_id']in hubs;editions[e['dst_id']].append(e)
    assert len(editions)==23 and len(set(hubs)-set(editions))==94
    rows=[]
    for hub_id,es in editions.items():
        maxrel=max(int(e['specRelease'].replace('Rel-',''))for e in es)
        newest=[e for e in es if int(e['specRelease'].replace('Rel-',''))==maxrel]
        assert len(newest)==1;latest=newest[0];s=byedition[latest['src_id']]
        assert latest['specNumber']==hubs[hub_id]['specNumber']==s['specNumber']and latest['specRelease']==s['release']and latest['specVersion']==s['frozen_specVersion']
        cnt=len(crs[hub_id]);sec=len(s['frozen_Sections']);assert sec>0
        ratio=(Decimal(cnt)/Decimal(sec)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
        rows.append({'specNumber':s['specNumber'],'crCnt':cnt,'secCnt':sec,'density':float(ratio)})
    rows.sort(key=lambda r:(-r['density'],r['specNumber']))
    assert len(rows)==23
    return rows,{'positive_abstract_hubs':117,'release_linked_hubs':23,'without_retained_edition_excluded_by_original_inner_match':94,'nonzero_latest_denominators':23,'counted_CR_paths':19537,'counted_type_paths':dict(types)}
def verify_guard_receipt(guard,definition_sha,wrapper_sha):
    """Validate saved observations; this does not create a memory observation."""
    assert guard['status']=='PASS'and guard['stage']=='execute_RAN3'
    assert guard['child_started']is True and type(guard['child_exit'])is int and guard['child_exit']==0
    assert type(guard['quality_rerolls'])is int and guard['quality_rerolls']==0
    assert guard['failure']is None
    exact_ints={'prestart_available_minimum_bytes':26*1024**3,'continuous_reserve_minimum_bytes':16*1024**3,
                'Linux_check_seconds':2,'Windows_check_seconds':10,'Windows_probe_timeout_seconds':20}
    for key,wanted in exact_ints.items():assert type(guard[key])is int and guard[key]==wanted
    initial=guard['initial_memory'];assert type(initial)is dict and set(initial)=={'Linux_available_bytes','Windows_available_bytes'}
    assert all(type(value)is int and value>=26*1024**3 for value in initial.values())
    samples=guard['memory_samples'];assert type(samples)is list and len(samples)>0
    elapsed=[]
    for sample in samples:
        assert type(sample)is dict and set(sample)=={'elapsed_seconds','Linux_available_bytes','Windows_available_bytes'}
        assert all(type(sample[key])is int and sample[key]>=16*1024**3 for key in ['Linux_available_bytes','Windows_available_bytes'])
        value=sample['elapsed_seconds'];assert type(value)in (int,float)and math.isfinite(value)and value>=0
        elapsed.append(value)
    assert elapsed==sorted(elapsed)
    cleanup=guard['owned_cleanup'];assert cleanup['owned_stopped']is True and cleanup['common_lock_held']is True
    assert type(cleanup['fallback_stop'])is bool and cleanup['container']=='kdd-db-frozen-v1-ran3'
    assert type(cleanup['container_identity'])is str and len(cleanup['container_identity'])>0
    assert guard['scope_sha256']==definition_sha and guard['wrapper_sha256']==wrapper_sha
    return {'initial_observed_hosts':2,'saved_reserve_samples':len(samples),'freshness_limit':'Saved Windows observations may be reused between nominal10-second probes; probe duration can extend that interval.'}
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source-root',type=Path);args=ap.parse_args()
    manifest=bootstrap();definition=read('contract/definition.json');criteria=read('contract/criteria.json')
    repair=sha(canon(definition).encode());assert len(definition)==9 and repair==manifest['repair_sha256']
    assert definition['id']==ID and definition['original_question_preserved']is True
    assert definition['question_en']=='Return CR density (CRs per section) for each spec (change-intensity metric).'
    assert definition['original_query'].endswith(' LIMIT 5')and definition['reference_query']==definition['original_query'][:-8]
    assert definition['repair_class']=='query_and_scorer'and definition['collection']=={'kind':'set'}and definition['cardinality_policy']=={'mode':'all'}
    assert definition['required_fields']==[{'name':'specNumber','type':'string','nullable':False,'source_column_or_expression':'specNumber'},{'name':'density','type':'number','nullable':False,'source_column_or_expression':'density'}]
    schema=module('density_schema',ROOT/'runtime/review_schema.py')
    for n in ['primary','secondary']:
        schema.check_pass(read('contract/'+n+'.json'),definition['question_en'],criteria['semantic_units'],criteria_sha=sha((ROOT/'contract/criteria.json').read_bytes()),identity_key='repair_sha256',identity_sha=repair)
    assert (ROOT/'contract/primary.json').read_bytes()!=(ROOT/'contract/secondary.json').read_bytes()
    sources=json.loads(gzip.decompress((ROOT/'source/latest23_styled_identity_and_own_XML.json.gz').read_bytes()))
    byedition,source_result=verify_sources(sources,no_links(args.source_root)if args.source_root else None)
    proj=json.loads(gzip.decompress((ROOT/'reference/complete_frozen_density_dependency_projection.json.gz').read_bytes()))
    rows,funnel=reconstruct_density(proj,byedition)
    sql=read('reference/fresh_SQL_full23.json')['rows']
    fields=['specNumber','crCnt','secCnt','density']
    assert same(rows,[{k:r[k]for k in fields}for r in sql])
    native=read('native/receipt.json')
    assert native['status']=='OK'and native['id']==ID and native['wg']=='RAN3'
    assert native['query']==definition['reference_query']and native['query_sha256']==sha(definition['reference_query'].encode())
    assert native['columns']==fields and native['full_rows_available']is True and native['truncated']is False
    assert native['rollback_completed']is True and native['execution_summary_complete']is True and native['plan_query_type']==native['execution_query_type']=='r'
    raw=(ROOT/'native/rows.jsonl').read_bytes();assert sha(raw)==native['rows_sha256']
    nr=[json.loads(x)for x in raw.splitlines()if x.strip()];assert len(nr)==native['rows_retained']==23
    assert Counter(canon(r)for r in nr)==Counter(canon([r[f]for f in fields])for r in rows)
    assert all(a[3]>=b[3]for a,b in zip(nr,nr[1:]))
    execution=read('native/execution_RAN3.json');assert execution['input_sha256']==sha((ROOT/'native/input.jsonl').read_bytes())
    assert execution['inventory_unchanged']is True and same(execution['source_before'],execution['source_after'])and execution['model_calls']==0 and type(execution['model_calls'])is int
    source_guard=execution['source_before']
    assert source_guard['wg']=='RAN3'and source_guard['source']['sha256']=='d9791c08773a0e38b89869b3882d3098d879a37ddd7109630c346200d6776e95'
    assert source_guard['import_manifest_sha256']=='6a325f06f5c5fe903d6b382635e7096a107c4b620e3a9288cf5a18852e30c0a5'
    assert source_guard['nodes']==87980 and source_guard['relationships']==481498
    assert source_guard['shipped_loader_sha256']=='9499ac120ea4fcf1c2707f6e3151e399530d9b4f43f5aec9d2d93040792d6e25'
    inp=[json.loads(x)for x in(ROOT/'native/input.jsonl').read_bytes().splitlines()if x.strip()]
    assert len(inp)==1 and inp[0]['id']==ID and inp[0]['wg']=='RAN3'and inp[0]['candidate_query']==definition['reference_query']
    assert execution['items']==[{'id':ID,'status':'OK','query_sha256':sha(definition['reference_query'].encode()),'rows':23}]
    guard=read('native/outer_guard_receipt.json')
    guard_result=verify_guard_receipt(guard,sha((ROOT/'contract/definition.json').read_bytes()),sha((ROOT/'native/outer_guard.py').read_bytes()))
    gold=read('reference/requested_records.json');assert same(gold,[{'specNumber':r['specNumber'],'density':r['density']}for r in rows])
    scorer=module('density_scorer',ROOT/'runtime/scorer.py');controls=read('reference/typed_controls.json')
    assert controls['repair_sha256']==repair and len(controls['tests'])==62
    for c in controls['tests']:
        actual=scorer.score(definition,gold,c['prediction'],diagnostic=True)
        assert same(actual,c['actual'])and actual['exact']is c['expected_exact']
    independent=read('reference/ROOT_independent_generic_SQL.json')
    assert independent['status']=='PASS'and independent['all7_output_columns_match_first_SQL']is True
    assert same(independent['rows'],sql)and independent['original_styled_Section_total']==4017
    print(json.dumps({'status':'PASS','id':ID,'repair_sha256':repair,'reference_query_changed_only':'removed final LIMIT5','native_rows':23,'native_columns':4,'requested_fields':2,'typed_controls':62,'source':source_result,'funnel':funnel,'saved_guard_observations':guard_result,'API_calls':0,'new_native_runs':0,'public_admissions':0}))
if __name__=='__main__':main()
