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

INVENTORY_SHA='00632900d3909ff693542b26e941c944da357b14501cff8a1acaf8346f479f11'
REPAIR_SHA='bf274789ab96effb5b4582b419851b0a2d32b8bc3a8e6692f3706ff1790661f3'
CRITERIA_SHA='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
ID='RAN3_P3_CQ4-1'
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
    source=data['source_geometry'];geometry={r['resolution_node']:r for r in source['geometry']}
    assert len(paths)==3778 and len(records)==len(geometry)==428
    assert source['fullcontent_contiguous_n']==402 and source['not_fullcontent_contiguous_n']==26
    refs={};mods={};crs={};specs={}
    for row in paths:
        a=(row['resolution_node'],row['cr_node']);b=(row['cr_node'],row['spec_node'])
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
        assert row['tdocNumber'] in set(re.findall(r'R3-\d{6}',record['content']))
    actual=collections.Counter((r['reference_edge'],r['modifies_edge'],r['specNumber']) for r in paths)
    derived=collections.Counter((ri,mi,specs[sp]) for ri,(r,cr) in refs.items() for mi,(mc,sp) in mods.items() if cr==mc)
    assert actual==derived and len(crs)==3459
    formal=collections.defaultdict(list)
    for row in data['formal_CR_fields']:formal[row['tdocNumber']].append(row['fields'])
    unmatched=[]
    for node,cr in crs.items():
        raw=formal[cr['tdocNumber']];assert raw
        targets={specs[sp] for _,(source,sp) in mods.items() if source==node}
        if not any(targets<=set(re.findall(r'\d{2}\.\d{3}',r['Spec'])) for r in raw):
            unmatched.append(cr['tdocNumber'])
            assert all(r['Type']=='other' and r['Spec']=='' for r in raw)
    assert len(unmatched)==1
    count=collections.Counter(row['specNumber'] for row in paths)
    full=load('execution/expected_SQL_all57_full_two_columns.json')
    assert len(full)==57 and sum(count.values())==3778
    assert collections.Counter((r['sp.specNumber'],r['resolutions']) for r in full)==collections.Counter(count.items())
    assert all(type(r['sp.specNumber']) is str and type(r['resolutions']) is int for r in full)
    assert [r['resolutions'] for r in full]==sorted(count.values(),reverse=True)
    assert full[9]['resolutions']==125 and full[10]['resolutions']==107
    selected=load('execution/expected_SQL_original10_full_two_columns.json');assert selected==full[:10]
    without=collections.Counter(row['specNumber'] for row in paths if row['tdocNumber'] not in unmatched)
    assert {sp for sp,n in without.most_common(10)}=={r['sp.specNumber'] for r in selected}
    return data,selected

def verify_approved_identity_witnesses(data,selected):
    roles=load('source/ten_affirmative_witnesses.json.gz')
    witnesses=roles['witnesses'];prefixes=load('source/ten_loader_source_prefixes.json.gz')
    by_spec={x['specNumber']:x for x in prefixes}
    styles={x['report']['sha256']:x['XML'] for x in load('source/ten_loader_style_parts.json.gz')}
    assert len(witnesses)==10 and set(by_spec)=={r['sp.specNumber'] for r in selected}=={w['specNumber'] for w in witnesses}
    formal={}
    for part in load('source/ten_original_register_parts.json.gz'):
        strings=part['shared_strings']
        header={v:k for k,v in field_values(E.fromstring(part['header_XML']),strings).items()}
        row=field_values(E.fromstring(part['row_XML']),strings)
        named={k:row.get(header.get(k,''),'') for k in part['expected_fields']}
        assert named==part['expected_fields'] and named['TDoc']==part['tdocNumber']
        assert part['specNumber'] in re.findall(r'\d{2}\.\d{3}',named['Spec'])
        formal[named['TDoc']]=named
    keys=('resolution_node','cr_node','spec_node','reference_edge','modifies_edge')
    paths={tuple(r[k] for k in keys):r for r in data['paths']}
    spec=importlib.util.spec_from_file_location('cq46_binary',ROOT/'source/binary_reader.py')
    binary=importlib.util.module_from_spec(spec);spec.loader.exec_module(binary)
    spec=importlib.util.spec_from_file_location('cq46_binary_styles',ROOT/'source/binary_stylesheet.py')
    bst=importlib.util.module_from_spec(spec);spec.loader.exec_module(bst)
    raw=gzip.decompress((ROOT/'source/original_93bis_report.doc.gz').read_bytes())
    native_text,direct,meta=binary.parse_doc(raw);sty=bst.stylesheet(raw)
    assert sty['nonempty_styles']==129 and sty['watched_style_operations']==[]
    flags={W+n for n in ('strike','dstrike','vanish','webHidden')}
    def active(p):
        assert not list(p.iter(W+'del')) and not list(p.iter(W+'moveFrom'))
        assert not [x for x in p.iter() if x.tag in flags and x.get(W+'val','true').lower() not in ('0','false','off')]
    formats=collections.Counter();outcomes=collections.Counter();cp_n=0
    for witness in witnesses:
        path=witness['graph_path'];sp=witness['specNumber'];td=path['tdocNumber']
        assert paths[tuple(path[k] for k in keys)]==path
        row=formal[td];assert row['Type'] in ('CR','draftCR','pCR')
        outcome=witness['same_CR_source_outcome'];assert outcome in ('agreed','endorsed')
        assert row['TDoc Status']==path['status']==outcome
        outcomes[outcome]+=1;part=by_spec[sp];source=witness['source'];formats[source['format']]+=1
        frag=part['source_prefix'];start=part['header_p_ordinal'];end=max(part['outcome_p_ordinals'])
        assert end<part['next_Tdoc_header_p_ordinal']
        own=[x for x in frag if start<=x['p_ordinal']<=end]
        assert [x['p_ordinal'] for x in own]==list(range(start,end+1))
        assert own[0]['text'].startswith(td+'\t')
        assert any(sp in p['text'] for p in own[:-1]),'same-CR header metadata lacks target Spec'
        assert all(not re.match(r'^R3-\d{6}[\t ]',x['text']) for x in own[1:])
        assert re.search(r'Decision:\s*The document was '+outcome+r'\.',own[-1]['text'])
        for p in frag:assert word_text(E.fromstring(p['XML']))==p['text']
        if source['format']=='original_OOXML_byte_identical_loader':
            style=E.fromstring(styles[part['report']['sha256']]);active(style)
            for p in own:active(E.fromstring(p['XML']))
            assert part['archive_matches'] and source['archive']==part['archive_matches'][0]
        else:
            assert source['format']=='original_CFB_separately_checked_converted_loader'
            assert sha(raw)==source['member_sha256'] and len(raw)==source['member_bytes']
            assert meta==source['binary_parse']
            lo=source['header_cp_start'];hi=source['next_header_cp'];segment=native_text[lo:hi]
            assert segment==source['literal'] and norm(own[0]['text']) in norm(segment)
            assert norm(own[-1]['text']) in norm(segment)
            # Check native header/spec/source and actual positive outcome CPs.
            first_line_end=native_text.index('\r',lo+1)
            for a,b in ((lo,first_line_end),(source['outcome_cp_start'],source['outcome_cp_end'])):
                for cp in range(a,b):
                    d=direct(cp);ops=d['direct_PRLs']+d['piece_character_PRLs'];cp_n+=1
                    assert not [x for x in ops if int(x['sprm'],16) in (0x0800,0x0802,0x0837,0x083c,0x2a53)]
    assert outcomes=={'agreed':8,'endorsed':2}
    assert formats=={'original_OOXML_byte_identical_loader':6,'original_CFB_separately_checked_converted_loader':4}
    return cp_n

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
    assert execution['source_before']['nodes']==87980 and execution['source_before']['relationships']==481498
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
        'recorded_paths':3778,'recorded_Resolution_records':428,'CR_identities':3459,
        'full_Spec_population':57,'explicit_positive_identity_witnesses':10,
        'original_CFB_active_header_outcome_CP':runs,'native_full_columns':2,'scoring_controls':controls}],
        'new_admissions':0,'API_calls':0,
        'source_replay_scope':'Saved complete recorded frontier plus exact finite source XML/register fragments; original source audits and scope are pinned separately.'}))
if __name__=='__main__':main()
