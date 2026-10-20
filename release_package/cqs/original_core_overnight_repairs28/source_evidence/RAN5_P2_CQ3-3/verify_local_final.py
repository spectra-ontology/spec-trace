"""Replay only the declared prepared gates. No native/API/admission claim."""
import sys
if sys.flags.optimize:
    raise SystemExit('Optimization is unsupported')
import argparse
import collections
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

INVENTORY_SHA = 'bca649cede1bafd5e8117fdc186a9657bec4e605959b1fcbac75b2e7a5f695d4'
EXACT_METADATA = {'id': 'RAN5_P2_CQ3-3', 'artifact_type': 'source_grounded_query_and_scorer_repair_local_final', 'status': 'pass_local_pending_ROOT_seal_and_public_evaluation', 'repair_sha256': '32fa5a317cf6940f5e87fb0e2647665cf889ca58151a1e167ddbe06209a87b48', 'criteria_sha256': 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'ready_for_ROOT_seal': True, 'admitted': False, 'original560_increment': 0, 'new_API_calls': 0, 'new_native_calls': 0, 'included_prior_ROOT_native_runs': 1, 'expert_validation_n': 0, 'default_replay_scope': 'Exact two semantic-review bindings; included source frontier and four XML/style witnesses; all83/all343 query-dependency projection; requested typed rank; saved actual native full two-column output, source inventory, guard and full SQL equality. No new native or API execution.', 'optional_source_root_scope': 'Only explicit --source-root reopens all35 exact original DOCX files and repeats the declared conservative lexical marker frontier; no host fallback.', 'publication_state': 'Local only. Actual public admission and first model evaluation are ROOT-owned subsequent actions.', 'preserved_failures': ['First CIM observation prestart failure before native launch', 'Incorrect outer-set duplicate control expectation corrected without changing definition/scorer/native/criteria']}
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
SHA = lambda b: hashlib.sha256(b).hexdigest()
def reject_symlink_ancestors(p):
    p = p.absolute()
    for q in [p, *p.parents]:
        if q.is_symlink(): raise ValueError('Symlink entry or ancestor is forbidden')
    return p
ROOT = reject_symlink_ancestors(Path(__file__)).parent
def canonical(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def load(n): return json.loads((ROOT/n).read_text())
def closed_tree():
    actual_files, actual_dirs = set(), set()
    for p in ROOT.rglob('*'):
        rel = p.relative_to(ROOT).as_posix()
        if p.is_symlink(): raise ValueError('Symlink in closed tree')
        if p.is_file(): actual_files.add(rel)
        elif p.is_dir(): actual_dirs.add(rel)
        else: raise ValueError('Nonregular closed-tree entry')
    meta = load('manifest.json')
    if set(meta) != set(EXACT_METADATA)|{'files'}:
        raise ValueError('Manifest metadata key set changed')
    if canonical({k:v for k,v in meta.items()if k!='files'}) != canonical(EXACT_METADATA):
        raise ValueError('Prepared status, identity or strict metadata changed')
    inv_raw=(ROOT/'immutable_inventory.json').read_bytes()
    if SHA(inv_raw)!=INVENTORY_SHA:raise ValueError('Immutable inventory changed')
    inv=json.loads(inv_raw)
    if set(inv)!={'files'}:raise ValueError('Inventory schema changed')
    def fmap(entries):
        if type(entries)is not list:raise ValueError('File inventory must be a list')
        out={}
        for e in entries:
            if type(e)is not dict or set(e)!={'path','bytes','sha256'}:raise ValueError('File entry shape')
            n=e['path']
            if type(n)is not str or Path(n).is_absolute()or '..'in Path(n).parts or n in out:
                raise ValueError('Unsafe or duplicate inventory path')
            if type(e['bytes'])is not int or type(e['sha256'])is not str:raise ValueError('Pin type')
            out[n]=e
        return out
    scientific=fmap(inv['files']);listed=fmap(meta['files'])
    meta_files={'README.md','manifest.json','verify_local_final.py','immutable_inventory.json'}
    if actual_files!=set(scientific)|meta_files or set(listed)!=actual_files-{'manifest.json'}:
        raise ValueError('Closed file namespace differs')
    expected_dirs={p.as_posix()for n in actual_files for p in Path(n).parents if p.as_posix()!='.'}
    if actual_dirs!=expected_dirs:raise ValueError('Extra or missing directory')
    for n,e in listed.items():
        b=(ROOT/n).read_bytes()
        if len(b)!=e['bytes']or SHA(b)!=e['sha256']:raise ValueError('Outer file pin changed:'+n)
    for n,e in scientific.items():
        if canonical(listed[n])!=canonical(e):raise ValueError('Scientific pin changed:'+n)
    return len(actual_files)

def text(p):
    return ''.join((e.text or '')if e.tag in{W+'t',W+'delText'}else'\t'if e.tag==W+'tab'else'\n'if e.tag in{W+'br',W+'cr'}else''for e in p.iter())
marker=re.compile(r'\bconclusions?\s*:',re.I)
tdoc=re.compile(r'\bR5-\d{6}\b')
def is_marker(t):return marker.search(t)is not None or t.strip().casefold()in{'conclusion','conclusions'}
def boundary(p,t):
    if re.match(r'^\s*Decision\s*:',t,re.I):return 'document_Decision_field'
    if re.match(r'^\s*R5-\d{6}\b',t):return 'new_Tdoc_heading'
    if is_marker(t):return 'next_Conclusion_candidate'
    style=p.find(W+'pPr/'+W+'pStyle');outline=p.find(W+'pPr/'+W+'outlineLvl')
    if t.strip()and((style is not None and re.match(r'heading\d',style.get(W+'val',''),re.I))or outline is not None):return 'Word_heading'
    return None
def candidates(meeting,body):
    ps=list(body.iter(W+'p'));ts=[text(p)for p in ps];out=[]
    for i,(p,t)in enumerate(zip(ps,ts)):
        if not is_marker(t):continue
        stop,why=len(ps),'end_of_body'
        for j in range(i+1,len(ps)):
            b=boundary(ps[j],ts[j])
            if b:stop,why=j,b;break
        m=marker.search(t);head=t[m.end():]if m else''
        own='\n'.join([head]+ts[i+1:stop]).strip()
        out.append({'meeting':meeting,'w_p_ordinal':i,'marker_text':t,
            'marker_XML_sha256_ET_default':SHA(ET.tostring(p)),
            'own_text':own,'literal_Tdoc_ids':sorted(set(tdoc.findall(own))),
            'boundary_ordinal':stop,'boundary_reason':why,'boundary_text':ts[stop]if stop<len(ps)else None,
            'nearby':[{'ordinal':k,'text':ts[k],'XML_sha256_ET_default':SHA(ET.tostring(ps[k]))}
                      for k in range(max(0,i-3),min(len(ps),stop+3))]})
    return out
def module(name):
    spec=importlib.util.spec_from_file_location('prepared_'+name,ROOT/(name+'.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=Path);args=ap.parse_args()
    n=closed_tree()
    definition=load('contract/definition.json');binding=load('contract/canonical_binding.json')
    keys={'id','question_en','original_query','reference_query','required_fields','collection','cardinality_policy','repair_class','original_question_preserved'}
    if set(definition)!=keys or SHA(canonical(definition))!=EXACT_METADATA['repair_sha256']:
        raise ValueError('Canonical nine-key definition mismatch')
    authority=load('source/original_authority.json');criteria=load('criteria.json')
    if definition['question_en']!=authority['question_en']or definition['original_query']!=authority['original_query']:
        raise ValueError('Original bytes changed')
    if SHA((ROOT/'criteria.json').read_bytes())!=EXACT_METADATA['criteria_sha256']:
        raise ValueError('Original criteria mismatch')
    primary=load('contract/primary.json')
    module('review_schema').check_pass(primary,definition['question_en'],criteria['semantic_units'],
        criteria_sha=EXACT_METADATA['criteria_sha256'],identity_key='repair_sha256',identity_sha=EXACT_METADATA['repair_sha256'])
    raw=load('source/all89_marker_candidates_NOT_89_certified_Conclusions.json')
    report_pins=load('source/all35_raw_report_pins.json')
    if [p['meeting']for p in report_pins]!=list(range(76,111))or len(raw)!=89:
        raise ValueError('Saved declared source frontier mismatch')
    positive=[x for x in raw if x['literal_Tdoc_ids']]
    fragments=load('source/fragment_index.json')
    if len(positive)!=4 or len(fragments)!=4:raise ValueError('Four own-reference witnesses changed')
    for fr in fragments:
        source=fr['source_marker']
        if source not in positive:raise ValueError('Fragment/source frontier binding changed')
        ps={}
        for x in fr['paragraphs']:
            b=(ROOT/x['file']).read_bytes()
            if SHA(b)!=x['sha256']:raise ValueError('Fragment hash changed')
            ps[x['w_p_ordinal_including_tables']]=ET.fromstring(b)
        for near in source['nearby']:
            p=ps[near['ordinal']]
            if text(p)!=near['text']or SHA(ET.tostring(p))!=near['XML_sha256_ET_default']:
                raise ValueError('Exact source neighborhood or XML changed')
        t=text(ps[source['w_p_ordinal']]);m=marker.search(t)
        own='\n'.join([t[m.end():]if m else'']+[text(ps[j])for j in range(source['w_p_ordinal']+1,source['boundary_ordinal'])]).strip()
        if own!=source['own_text']or sorted(set(tdoc.findall(own)))!=source['literal_Tdoc_ids']:
            raise ValueError('Own reference span changed')
        if boundary(ps[source['boundary_ordinal']],text(ps[source['boundary_ordinal']]))!='document_Decision_field':
            raise ValueError('Original document boundary absent')
        for h in fr['own_Tdoc_header']['context']:
            if text(ps[h['paragraph']])!=h['text']or SHA(ET.tostring(ps[h['paragraph']]))!=h['xml_sha256_ET_default']:
                raise ValueError('Own Tdoc role source changed')
        if SHA((ROOT/fr['styles']['file']).read_bytes())!=fr['styles']['sha256']:
            raise ValueError('Original source styles changed')
    proj=load('frozen/query_dependency_projection.json')
    if len(proj['resolutions'])!=83 or len(proj['references'])!=343:raise ValueError('Original frozen frontier changed')
    rs={x['node_id']:x for x in proj['resolutions']};ts={x['node_id']:x for x in proj['tdocs']}
    ss={x['node_id']:x for x in proj['specs']};cs={x['node_id']:x for x in proj['companies']}
    mods=collections.defaultdict(list);subs=collections.defaultdict(list)
    for x in proj['modifies']:mods[x['src_id']].append(x['dst_id'])
    for x in proj['submitted_by']:subs[x['src_id']].append(x['dst_id'])
    own_ids=sorted(t for r in rs.values()for t in set(tdoc.findall((r['content']or'').split('\nDecision:',1)[0])))
    if own_ids!=sorted(t for x in positive for t in x['literal_Tdoc_ids']):
        raise ValueError('Frozen own-reference frontier differs from original source positives')
    groups=collections.defaultdict(set)
    for e in proj['references']:
        r=rs.get(e['src_id']);t=ts.get(e['dst_id'])
        if r is None or t is None:continue
        if t['tdocNumber']not in(r['content']or'').split('\nDecision:',1)[0]:continue
        for sn in mods[t['node_id']]:
            if sn not in ss:continue
            for cn in subs[t['node_id']]:
                if cn in cs:groups[(ss[sn]['specNumber'],cs[cn]['companyName'])].add(t['node_id'])
    actual_groups=[{'spec':s,'company':c,'tdoc_count':len(docs)}for(s,c),docs in groups.items()]
    actual_groups.sort(key=lambda x:(x['spec'],-x['tdoc_count'],x['company']))
    saved=load('frozen/saved_SQL.json')
    if actual_groups!=saved['all_source_own_groups']:raise ValueError('Distinct Tdoc/source role aggregation changed')
    byspec=collections.defaultdict(list)
    for g in actual_groups:byspec[g['spec']].append(g['company'])
    records=[{'spec':s,'contributors':cs[:10]}for s,cs in sorted(byspec.items())]
    expected=[json.loads(l)for l in(ROOT/'frozen/expected_full_projection.jsonl').read_text().splitlines()]
    if records!=expected or records!=saved['records']:raise ValueError('Full requested two-column projection mismatch')
    scorer=module('scorer')
    if not scorer.score(definition,records,records,diagnostic=True)['exact']:raise ValueError('Typed reference failed')
    if not scorer.score(definition,records,list(reversed(records)),diagnostic=True)['exact']:raise ValueError('Outer set semantics failed')
    for pred in [[],records[:-1],records+[{}],
                 [dict(r,contributors=None)for r in records],
                 [dict(r,contributors=[True])for r in records],
                 [dict(r,contributors=list(reversed(r['contributors'])))for r in records]]:
        if scorer.score(definition,records,pred,diagnostic=True)['exact']:raise ValueError('Typed adverse control accepted')
    controls=load('controls/typed_actual.json')
    if len(controls['checks'])!=25 or not all(x['pass']is True for x in controls['checks']):raise ValueError('Saved typed control evidence changed')
    secondary=load('contract/secondary.json')
    module('review_schema').check_pass(secondary,definition['question_en'],criteria['semantic_units'],
        criteria_sha=EXACT_METADATA['criteria_sha256'],identity_key='repair_sha256',identity_sha=EXACT_METADATA['repair_sha256'])
    if canonical(primary)==canonical(secondary)or primary['review_role']==secondary['review_role']:
        raise ValueError('Primary and separate secondary judgment are not distinct')
    root_source=load('source/ROOT_fresh_all35_and_SQL_replay.json')
    if root_source['status']!='PASS'or root_source['immutable_query_only']is not True or root_source['all83_frozen_rows_reopened_equal']is not True:
        raise ValueError('ROOT actual source/SQL evidence failed')
    if root_source['database_sha256_fresh_before_and_after']!=proj['original_SQL_pin']['sha256']:
        raise ValueError('ROOT fresh full SQL identity mismatch')
    if root_source['full_typed_SQL_records']!=records or root_source['broad_markers']!=len(raw):
        raise ValueError('ROOT complete source/SQL projection mismatch')
    expected_reports={x['meeting']:x for x in report_pins}
    if len(root_source['source_reports_reopened'])!=35:raise ValueError('ROOT original source frontier missing')
    for x in root_source['source_reports_reopened']:
        rp=expected_reports[x['meeting']]
        if x['file_sha256']!=rp['file']['sha256']or x['xml_sha256']!=rp['xml_sha256']or x['all_paragraphs']!=rp['all_w_p_n']:
            raise ValueError('ROOT source input disagrees with original pins')
    prefix_map={r['resolutionId']:(r['content']or'').split('\nDecision:',1)[0].strip()for r in rs.values()}
    if {x['resolutionId']:x['prefix']for x in root_source['all83_own_prefixes']}!=prefix_map:
        raise ValueError('ROOT all83 own prefix mismatch')
    native=load('native/metadata.json');native_raw=(ROOT/'native/rows.jsonl').read_bytes()
    if native['query']!=definition['reference_query']or native['query_sha256']!=SHA(definition['reference_query'].encode()):
        raise ValueError('Actual native query is not the exact canonical repair')
    if native['columns']!=['spec','contributors']or native['status']!='OK':raise ValueError('Native full column identity failed')
    for key in ['rollback_completed','execution_summary_complete','full_rows_available']:
        if native[key]is not True:raise ValueError('Incomplete native evidence:'+key)
    if native['truncated']is not False or native['plan_query_type']!='r'or native['execution_query_type']!='r':
        raise ValueError('Native read/full-output evidence failed')
    if SHA(native_raw)!=native['rows_sha256']or len(native_raw)!=native['bytes_retained']:
        raise ValueError('Complete native rows pin failed')
    positional=[json.loads(l)for l in native_raw.decode().splitlines()]
    if any(type(r)is not list or len(r)!=2 for r in positional):raise ValueError('Native positional row shape')
    named=[dict(zip(native['columns'],r))for r in positional]
    if named!=records or native['rows_retained']!=len(records):raise ValueError('Native all rows/all columns differ from SQL')
    if not scorer.score(definition,records,named,diagnostic=True)['exact']:raise ValueError('Native requested projection failed typed comparison')
    execution=load('native/execution_RAN5.json')
    if execution['input_sha256']!=SHA((ROOT/'contract/native_input_development_probe.jsonl').read_bytes()):
        raise ValueError('Native input bytes differ')
    if canonical(execution['source_before'])!=canonical(execution['source_after'])or execution['inventory_unchanged']is not True:
        raise ValueError('Native source before/after differs')
    if execution['source_before']['source']['sha256']!='1ab414b785a155b58218a209be71ed9d1dacc1ea86ae13abbacfbaea27808f5e':
        raise ValueError('Actual native archived graph identity differs')
    if execution['source_before']['nodes']!=215012 or execution['source_before']['relationships']!=1047242:
        raise ValueError('Actual native complete graph inventory differs')
    if execution['items']!=[{'id':EXACT_METADATA['id'],'status':'OK','query_sha256':native['query_sha256'],'rows':len(records)}]:
        raise ValueError('Native execution event disagrees')
    protocol=load('native/execution_protocol.json');guard=load('native/actual_guard.json')
    if protocol['container_memory_bytes']!=2*1024**3 or protocol['container_cpu_cores']!=1:
        raise ValueError('Owned native caps changed')
    if guard['status']!='PASS'or guard['child_started']is not True or guard['child_exit']!=0:
        raise ValueError('Actual owned native guard did not pass')
    if guard['prestart_available_minimum_bytes']!=26*1024**3 or guard['continuous_reserve_minimum_bytes']!=16*1024**3:
        raise ValueError('Actual memory guard thresholds changed')
    if guard['owned_cleanup']['owned_stopped']is not True or guard['owned_cleanup']['common_lock_held']is not True:
        raise ValueError('Owned native cleanup/lock evidence missing')
    for host in ['Linux_available_bytes','Windows_available_bytes']:
        if guard['initial_memory'][host]<26*1024**3:raise ValueError('Actual native admission sample below threshold')
        if any(x[host]<16*1024**3 for x in guard['memory_samples']):raise ValueError('Actual native continuous sample below threshold')
    rootgate=load('native/ROOT_full_typed_SQL_and_scorer_gate.json')
    if rootgate['status']!='PASS'or rootgate['repair_sha256']!=EXACT_METADATA['repair_sha256']or rootgate['all_rows']!=records:
        raise ValueError('ROOT full SQL/native/controls gate mismatch')
    if rootgate['full_typed_native_SQL_equal']is not True or rootgate['source_inventory_before_after_equal']is not True:
        raise ValueError('ROOT full typed or inventory gate failed')
    for x in rootgate['controls']:
        if type(x['expected_exact'])is not bool or x['outcome']['exact']is not x['expected_exact']:
            raise ValueError('ROOT actual adverse scoring control failed')
    failure=load('native/preserved_first_CIM_prestart_failure.json')
    correction=load('native/preserved_control_expectation_correction.json')
    if failure['status']!='FAIL_PRESERVED'or correction['first_attempt_status']!='FAIL_PRESERVED':
        raise ValueError('Historical operational/test failure not preserved')
    if correction['correct_expected_exact']is not True or correction['actual_result']['exact']is not True:
        raise ValueError('Outer-set duplicate correction changed the contract')

    optional=False
    if args.source_root is not None:
        base=reject_symlink_ancestors(args.source_root)
        if not base.is_dir():raise ValueError('Explicit source root is not a directory')
        rederived=[]
        for rp in report_pins:
            p=reject_symlink_ancestors(base/f'ontology/input/tsg/RAN/formal/meetings/RAN5/Final_Report/Final_Report_RAN5-{rp["meeting"]}.docx')
            if not p.is_file()or SHA(p.read_bytes())!=rp['file']['sha256']:raise ValueError('Explicit original source pin mismatch')
            with zipfile.ZipFile(p)as z:
                xml=z.read('word/document.xml');info=z.getinfo('word/document.xml')
            if SHA(xml)!=rp['xml_sha256']or len(xml)!=rp['xml_bytes']or f'{info.CRC:08x}'!=rp['xml_crc32']:
                raise ValueError('Original ZIP member/XML pin mismatch')
            rederived.extend(candidates(rp['meeting'],ET.fromstring(xml).find(W+'body')))
        if rederived!=raw:raise ValueError('Whole35 original lexical frontier differs from saved evidence')
        optional=True
    print(json.dumps({'status':'LOCAL_FINAL_GATES_PASS_NOT_PUBLIC_ADMISSION','id':EXACT_METADATA['id'],
        'files_checked':n,'repair_sha256':EXACT_METADATA['repair_sha256'],
        'saved_source_positive_witnesses':4,'frozen_dependency_rows':{'Resolution':83,'REFERENCES':343},
        'projection_rows':len(records),'requested_columns':['spec','contributors'],
        'optional_all35_original_DOCX_frontier_reopened':optional,
        'native_executed':False,'secondary_review_included':True,'admitted':False,
        'original560_increment':0,'API_calls':0},ensure_ascii=False))

if __name__=='__main__':main()
