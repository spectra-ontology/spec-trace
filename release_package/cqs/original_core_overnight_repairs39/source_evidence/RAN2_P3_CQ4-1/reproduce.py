"""Replay the pinned original recorded trace and finite approved-Spec witnesses."""
import sys
if sys.flags.optimize:
    raise SystemExit('Optimization unsupported')
sys.dont_write_bytecode=True
import collections
import gzip
import hashlib
import importlib.util
import json
import pathlib
import re
import stat
import xml.etree.ElementTree as E

INVENTORY_SHA='988a54fcb32afd4d5664261b788c83f7538ed4f884f59fb4f5825f74e4829edc'
REPAIR_SHA='09970f9006ab395e7b68551906817b616364feb4ce4c19b7c83304614d45ffdf'
CRITERIA_SHA='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
ID='RAN2_P3_CQ4-1'
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
X='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
ROOT=pathlib.Path(__file__).absolute().parent

def no_symlink(p):
    for item in (p,*p.parents):
        if item.is_symlink():raise ValueError('symlink path forbidden')
no_symlink(pathlib.Path(__file__).absolute())
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(obj):return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def load(name):
    p=ROOT/name
    raw=p.read_bytes()
    return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)
def word_text(p):
    return ''.join(e.text or '' if e.tag==W+'t' else '\t' if e.tag==W+'tab' else '\n' if e.tag in {W+'br',W+'cr'} else '' for e in p.iter())
def norm(value):return ' '.join(value.split())
def field_values(row,strings):
    out={}
    for cell in row.findall(X+'c'):
        v=cell.find(X+'v');value=v.text if v is not None else ''
        if cell.get('t')=='s':value=''.join(t.text or '' for t in E.fromstring(strings[value]).iter(X+'t'))
        elif cell.get('t')=='inlineStr':value=''.join(t.text or '' for t in cell.iter(X+'t'))
        out[re.sub(r'\d','',cell.get('r'))]=value or ''
    return out

def verify_inventory():
    allowed_meta={'README.md','manifest.json','inventory.json','reproduce.py'}
    no_symlink(ROOT/'inventory.json')
    assert stat.S_ISREG((ROOT/'inventory.json').lstat().st_mode)
    raw=(ROOT/'inventory.json').read_bytes()
    assert sha(raw)==INVENTORY_SHA,'immutable scientific inventory changed'
    inventory=json.loads(raw)
    expected=set(inventory)|allowed_meta
    actual=set()
    parents=set()
    for name in expected:
        p=pathlib.PurePosixPath(name)
        assert p.as_posix()==name and not p.is_absolute() and '..' not in p.parts
        parents.update(q.as_posix() for q in p.parents if q.as_posix()!='.')
    for p in ROOT.rglob('*'):
        mode=p.lstat().st_mode;name=p.relative_to(ROOT).as_posix()
        if stat.S_ISLNK(mode):raise ValueError('tree symlink forbidden')
        if stat.S_ISREG(mode):actual.add(name)
        elif stat.S_ISDIR(mode):assert name in parents,'unlisted directory'
        else:raise ValueError('nonregular tree entry forbidden')
    assert actual==expected,'closed file inventory differs'
    for name,entry in inventory.items():
        p=ROOT/name;raw=p.read_bytes()
        assert type(entry['bytes']) is int and entry['bytes']==len(raw)
        assert sha(raw)==entry['sha256'],name
    manifest=load('manifest.json')
    assert canonical(manifest)==canonical({
        'id':ID,'artifact_type':'local_original_recorded_trace_evidence',
        'repair_sha256':REPAIR_SHA,'scientific_inventory_sha256':INVENTORY_SHA,
        'local_validation_status':'completed_local_gates',
        'new_admissions':0,'API_calls':0,
        'files':{name:{'bytes':(ROOT/name).stat().st_size,'sha256':sha((ROOT/name).read_bytes())}
                 for name in sorted(expected) if name!='manifest.json'}})
    return inventory

def verify_contract_and_reviews():
    definition=load('contract/definition.json')
    assert set(definition)=={'id','question_en','original_query','reference_query','required_fields','collection','cardinality_policy','repair_class','original_question_preserved'}
    assert sha(canonical(definition))==REPAIR_SHA
    assert definition['id']==ID and definition['original_query']==definition['reference_query']
    assert definition['required_fields']==[{'name':'specNumber','type':'string','nullable':False,'source_column_or_expression':'sp.specNumber'}]
    assert definition['collection']=={'kind':'set'} and definition['cardinality_policy']=={'mode':'exact','value':10}
    criteria=load('contract/criteria.json')
    assert sha((ROOT/'contract/criteria.json').read_bytes())==CRITERIA_SHA
    spec=importlib.util.spec_from_file_location('recorded_trace_fixed_review_schema',ROOT/'contract/review_schema.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    for name in ('primary_exact_seven_unit_review.json','independent_secondary_exact_seven_unit_review.json'):
        module.check_pass(load('contract/'+name),definition['question_en'],criteria['semantic_units'],criteria_sha=CRITERIA_SHA,identity_key='repair_sha256',identity_sha=REPAIR_SHA)
    return definition

def verify_frontier():
    data=load('source/complete_recorded_frontier_projection.json.gz')
    paths=data['paths'];records={r['node_id']:r for r in data['Resolution_content']}
    geometry={r['node_id']:r for r in data['source_geometry']}
    assert len(paths)==2351 and len(records)==len(geometry)==474
    refs={};mods={};crs={};specs={}
    for row in paths:
        a=(row['resolution_node'],row['cr_node'])
        b=(row['cr_node'],row['spec_node'])
        assert row['reference_edge'] not in refs or refs[row['reference_edge']]==a
        assert row['modifies_edge'] not in mods or mods[row['modifies_edge']]==b
        refs[row['reference_edge']]=a;mods[row['modifies_edge']]=b
        fields={k:row[k] for k in ('tdocNumber','title','status','crNumber','crRevision')}
        assert row['cr_node'] not in crs or crs[row['cr_node']]==fields
        crs[row['cr_node']]=fields
        assert row['spec_node'] not in specs or specs[row['spec_node']]==row['specNumber']
        specs[row['spec_node']]=row['specNumber']
        record=records[row['resolution_node']];g=geometry[row['resolution_node']]
        assert record['resolutionId']==row['resolutionId']==g['resolutionId']
        assert sha(record['content'].encode())==g['content_sha256']
        assert row['tdocNumber'] in set(re.findall(r'R2-\d{7}',record['content']))
        assert row['tdocNumber'] in g['full_source_capture_R2_literals']
    # Reconstruct join multiplicity from saved directed edge identity, not a
    # count stored in the source witness or an answer list.
    actual=collections.Counter((r['reference_edge'],r['modifies_edge'],r['specNumber']) for r in paths)
    derived=collections.Counter((ri,mi,specs[spec]) for ri,(res,cr) in refs.items() for mi,(mcr,spec) in mods.items() if cr==mcr)
    assert actual==derived and len(crs)==2164
    formal=collections.defaultdict(list)
    for row in data['formal_CR_fields']:formal[row['tdocNumber']].append(row['fields'])
    for node,cr in crs.items():
        raw=formal[cr['tdocNumber']]
        targets={specs[target] for _,(source,target) in mods.items() if source==node}
        assert any(targets<=set(re.findall(r'(?<![0-9])\d{2}\.\d{3}(?![0-9])',r['Spec'])) for r in raw)
        assert any(cr['status']==r['TDoc Status'] for r in raw)
        assert all(r['Type'] in {'CR','draftCR','pCR'} for r in raw)
    count=collections.Counter(row['specNumber'] for row in paths)
    full=load('execution/expected_SQL_all34_full_two_columns.json')
    assert len(full)==34 and sum(count.values())==2351
    assert collections.Counter((r['sp.specNumber'],r['resolutions']) for r in full)==collections.Counter(count.items())
    assert all(type(r['sp.specNumber']) is str and type(r['resolutions']) is int for r in full)
    assert [r['resolutions'] for r in full]==sorted(count.values(),reverse=True)
    assert full[9]['resolutions']==52 and full[10]['resolutions']==50
    selected=load('execution/expected_SQL_original10_full_two_columns.json')
    assert selected==full[:10]
    return data,selected

def active_predicate(paragraph,styles):
    tree=E.fromstring(styles)
    styles_by_id={s.get(W+'styleId'):s for s in tree.findall(W+'style')}
    def chain(name):
        seen=set();out=[]
        while name:
            assert name in styles_by_id and name not in seen
            seen.add(name);s=styles_by_id[name];out.append(s)
            b=s.find(W+'basedOn');name=b.get(W+'val') if b is not None else None
        return out
    default=tree.find(W+'docDefaults/'+W+'rPrDefault/'+W+'rPr')
    ps=paragraph.find(W+'pPr/'+W+'pStyle')
    pstyles=chain(ps.get(W+'val')) if ps is not None else [s for d in tree.findall(W+'style') if d.get(W+'type')=='paragraph' and d.get(W+'default') in {'1','true','on'} for s in chain(d.get(W+'styleId'))]
    parents={c:p for p in paragraph.iter() for c in p};runs=0
    for run in paragraph.iter(W+'r'):
        if not ''.join(t.text or '' for t in run.iter(W+'t')).strip():continue
        runs+=1;rp=run.find(W+'rPr');rs=None if rp is None else rp.find(W+'rStyle')
        rstyles=chain(rs.get(W+'val')) if rs is not None else []
        for holder in [default]+[s.find(W+'rPr') for s in pstyles+rstyles]+[rp]:
            if holder is None:continue
            for name in ('strike','dstrike','vanish','webHidden'):
                prop=holder.find(W+name)
                assert prop is None or prop.get(W+'val','true').lower() in {'0','false','off'}
        p=parents.get(run)
        while p is not None:
            assert p.tag not in {W+'del',W+'moveFrom'};p=parents.get(p)
    assert runs
    return runs

def verify_approved_identity_witnesses(data,selected):
    witnesses=load('source/ten_affirmative_witnesses.json')
    parts=load('source/ten_original_source_prefixes.json.gz')
    styles={r['member_sha256']:r for r in load('source/seven_original_style_parts.json.gz')}
    by_spec={r['specNumber']:r for r in parts}
    assert set(by_spec)=={r['sp.specNumber'] for r in selected}=={r['specNumber'] for r in witnesses}
    formal=collections.defaultdict(list)
    for part in load('source/ten_affirmative_CR_original_register_cells.json.gz'):
        strings=part['selected_shared_strings']
        header={value:key for key,value in field_values(E.fromstring(part['header_row_XML']),strings).items()}
        for row in part['rows']:
            decoded=field_values(E.fromstring(row['row_XML']),strings)
            named={name:decoded.get(header.get(name,''),'') for name in row['expected_fields']}
            assert named==row['expected_fields']
            formal[named['TDoc']].append(named)
    paths={tuple(row[k] for k in ('resolution_node','cr_node','spec_node','reference_edge','modifies_edge')):row for row in data['paths']}
    runs=0
    for witness in witnesses:
        spec=witness['specNumber'];path=witness['path'];part=by_spec[spec]
        assert paths[tuple(path[k] for k in ('resolution_node','cr_node','spec_node','reference_edge','modifies_edge'))]==path
        assert path['specNumber']==spec and path['status']=='agreed'
        assert any(r['Type']=='CR' and r['TDoc Status']=='agreed' and spec in re.findall(r'\d{2}\.\d{3}',r['Spec']) for r in formal[path['tdocNumber']])
        assert part['tdocNumber']==path['tdocNumber'] and part['resolutionId']==path['resolutionId']
        fragments=part['prefix_through_predicate'];first=part['marker_p_ordinal']
        assert [p['body_p_ordinal'] for p in fragments]==list(range(first,first+len(fragments)))
        assert fragments[-1]['body_p_ordinal']<part['next_retained_marker_p_ordinal']
        assert norm(fragments[0]['text'])==norm(witness['source_geometry']['marker_text'])
        for p in fragments:assert word_text(E.fromstring(p['XML']))==p['text']
        assert [p['raw_body_child'] for p in fragments]==sorted(set(p['raw_body_child'] for p in fragments))
        chosen=[]
        for retained in witness['original_paragraphs']:
            p=fragments[retained['original_paragraph']['body_p_ordinal']-first]
            assert p==retained['original_paragraph']
            literal=retained['literal'];text=p['text']
            assert norm(literal)==norm(text) or literal.split('\t')[:10]==text.split('\t')[:10]
            chosen.append(p)
        outcome=chosen[-1]
        assert re.search(r'\b(?:is|are) agreed\b',outcome['text'],re.I) or re.fullmatch(r'(?:=>\s*)?(?:the CR is )?Agreed[.!]?',outcome['text'].strip(),re.I)
        assert not re.search(r'not agreed|can be agreed',outcome['text'],re.I)
        if len(chosen)==1:assert path['tdocNumber'] in outcome['text']
        else:
            assert chosen[0]['text'].startswith(path['tdocNumber']+'\t')
            for p in fragments[chosen[0]['body_p_ordinal']-first+1:outcome['body_p_ordinal']-first]:
                assert not re.match(r'^R2-\d{7}\t',p['text'])
        raw_styles=styles[part['member_sha256']]
        assert sha(raw_styles['XML'].encode())==part['styles_XML_sha256']==raw_styles['styles_XML_sha256']
        runs+=active_predicate(E.fromstring(outcome['XML']),raw_styles['XML'])
    assert runs==25
    return runs

def verify_native_and_score(definition,selected):
    case=load('execution/native_case.json');execution=load('execution/native_execution.json')
    protocol=load('execution/native_protocol.json');guard=load('execution/outer_guard.json')
    assert case['id']==ID and case['query']==definition['reference_query']
    assert case['query_sha256']==sha(case['query'].encode())
    assert case['status']=='OK' and case['rows_retained']==10
    for name in ('rollback_completed','execution_summary_complete','full_rows_available'):assert case[name] is True
    assert case['truncated'] is False and case['plan_query_type']==case['execution_query_type']=='r'
    assert case['columns']==['sp.specNumber','resolutions']
    raw=(ROOT/'execution/native_rows.jsonl').read_bytes()
    assert sha(raw)==case['rows_sha256'] and len(raw)==case['bytes_retained']
    positional=[json.loads(line) for line in raw.splitlines()]
    assert all(type(row) is list and len(row)==2 and type(row[0]) is str and type(row[1]) is int for row in positional)
    assert [dict(zip(case['columns'],row)) for row in positional]==selected
    assert execution['input_sha256']==sha((ROOT/'execution/native_input.jsonl').read_bytes())
    assert execution['source_before']==execution['source_after'] and execution['inventory_unchanged'] is True
    assert execution['source_before']['nodes']==156288 and execution['source_before']['relationships']==939037
    item=[i for i in execution['items'] if i['id']==ID]
    assert len(item)==1 and item[0]['status']=='OK' and item[0]['rows']==10 and item[0]['query_sha256']==case['query_sha256']
    assert protocol['container_memory_bytes']==2*1024**3 and protocol['container_cpu_cores']==1 and protocol['query_timeout_seconds']==20
    assert guard['status']=='PASS' and guard['child_started'] is True and type(guard['child_exit']) is int and guard['child_exit']==0
    assert guard['prestart_available_minimum_bytes']==26*1024**3 and guard['continuous_reserve_minimum_bytes']==16*1024**3
    assert guard['owned_cleanup']['owned_stopped'] is True and guard['owned_cleanup']['common_lock_held'] is True
    for value in guard['initial_memory'].values():assert type(value)is int and value>=26*1024**3
    observations=[json.loads(line) for line in (ROOT/'execution/fresh_memory_observations.jsonl').read_bytes().splitlines()]
    assert observations and len({x['session'] for x in observations})==1
    assert len({x['nonce'] for x in observations})==len(observations)
    for x in observations:
        assert x['status']=='FRESH_NUMERIC_OBSERVATION'
        assert type(x['windows_available_bytes']) is int and x['windows_available_bytes']>0
        assert x['Get_CimInstance_calls_for_this_request']==1 and x['cached_values_used']==0
    sys.path.insert(0,str(ROOT/'scoring'))
    spec=importlib.util.spec_from_file_location('recorded_trace_unchanged_scorer',ROOT/'scoring/original_scorer.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    gold=[{'specNumber':row['sp.specNumber']} for row in selected]
    controls=load('execution/actual_strict_requested_identity_controls.json')
    assert len(controls['tests'])==controls['tests_n']==16
    for control in controls['tests']:
        score=module.score(definition,gold,control['prediction'],diagnostic=True)
        assert score==control['actual'] and score['exact'] is control['expected_exact']
    return len(controls['tests'])

def main():
    verify_inventory()
    definition=verify_contract_and_reviews()
    data,selected=verify_frontier()
    runs=verify_approved_identity_witnesses(data,selected)
    controls=verify_native_and_score(definition,selected)
    print(json.dumps({'status':'PASS','cases':[{'id':ID,'repair_sha256':REPAIR_SHA,
        'requested_fields':['specNumber'],'collection':'set','rows':10,
        'recorded_paths':2351,'recorded_Resolution_records':474,'CR_identities':2164,
        'full_Spec_population':34,'explicit_agreed_identity_witnesses':10,
        'active_predicate_runs':runs,'native_full_columns':2,'scoring_controls':controls}],
        'new_admissions':0,'API_calls':0,
        'source_replay_scope':'Saved complete recorded frontier plus exact finite source XML/register fragments; original source audits and scope are pinned separately.'}))
if __name__=='__main__':main()
