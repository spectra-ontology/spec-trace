#!/usr/bin/env python3
"""Closed, relocatable finite-source replay. No network/native/host fallback."""
import argparse, collections, gzip, hashlib, importlib.util, io, json, re, sqlite3
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

BASE=Path(__file__).absolute().parent
INVENTORY_SHA256='68046f0ebe4d9619dba6ce7ce33bb671f8427da414ee16af45049f5da773be76'
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
def sha(b): return hashlib.sha256(b).hexdigest()
def token(s): return None if s is None else sha(json.dumps(s,ensure_ascii=False,separators=(',',':')).encode())
def read(name): return (BASE/name).read_bytes()
def load(name): return json.loads(read(name))
def jsonl(name): return [json.loads(s)for s in read(name).decode().splitlines()]
def ungz(name): return json.loads(gzip.decompress(read(name)))
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,BASE/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def closed_inventory():
    for p in [Path(__file__).absolute(),BASE,*BASE.parents]: assert not p.is_symlink(), ('symlink ancestor',str(p))
    for p in BASE.rglob('*'): assert not p.is_symlink(), ('symlink',str(p))
    inventory_bytes=read('immutable_inventory.json')
    assert sha(inventory_bytes)==INVENTORY_SHA256,'Immutable inventory pin mismatch'
    inventory=json.loads(inventory_bytes)['files']
    expected=set(inventory)|{'immutable_inventory.json','manifest.json','verify_source_evidence.py'}
    actual={str(p.relative_to(BASE))for p in BASE.rglob('*')if p.is_file()}
    assert actual==expected,('closed file tree mismatch',sorted(actual^expected))
    for f,pin in inventory.items():
        assert not Path(f).is_absolute() and '..' not in Path(f).parts
        b=read(f);assert len(b)==pin['bytes'] and sha(b)==pin['sha256'],('immutable file mismatch',f)
    manifest=load('manifest.json')
    assert set(manifest)=={'status','id','scope_and_provenance','source_selected_records','verifier','files'},'Manifest declaration keys differ'
    assert manifest['status']=='PORTABLE_SOURCE_EVIDENCE_NOT_ORIGINAL560_ADMISSION','Source status declaration differs'
    assert manifest['id']=='RAN1_P3_CQ024','Question identity declaration differs'
    expected_scope={'repair_sha256':'7c0122437095d695d0b13dd316463dd2df31f63c8dd41b88e64e090507c796b2','original560_pass_increment':0,'human_expert_n':0}
    assert json.dumps(manifest['scope_and_provenance'],sort_keys=True)==json.dumps(expected_scope,sort_keys=True),'Scope or provenance declaration differs'
    assert manifest['verifier']=='verify_source_evidence.py','Verifier locator differs'
    selected=read('source_selected_records.jsonl')
    expected_selected={'path':'source_selected_records.jsonl','records':10,'bytes':len(selected),'sha256':sha(selected)}
    assert json.dumps(manifest['source_selected_records'],sort_keys=True)==json.dumps(expected_selected,sort_keys=True),'Selected records metadata differs'
    selected_rows=[json.loads(line)for line in selected.decode().splitlines()]
    assert len(selected_rows)==10 and len({row['resolutionId']for row in selected_rows})==10,'Selected cardinality differs'
    assert all(set(row)=={'resolutionId'}and isinstance(row['resolutionId'],str)and row['resolutionId']for row in selected_rows),'Selected role differs'
    listed=manifest['files']
    assert set(listed)==expected-{'manifest.json'},'Manifest inventory mismatch'
    for f,pin in listed.items():
        b=read(f);assert len(b)==pin['bytes'] and sha(b)==pin['sha256'],('manifest pin mismatch',f)
    return manifest

def raw_source_replay():
    reader=module('word_raw_reader','code/raw_word_formatting_reader.py')
    kernel=module('generic_capture','code/generic_capture_kernel.py')
    reader.FFS=re.compile(r'R1-\d{7}(?!\d)|final\s+CRs?|agreement above is captured',re.I)
    original=read('provenance/original_generic_rule.py').decode()
    assert original[original.index('W = '):original.index('\ndef main():')] in read('code/generic_capture_kernel.py').decode()
    raw_bodies,audits={},{}
    attribution=load('source_attribution.json')
    for source in attribution['reports']:
        label=source['meeting'].split('#')[1]
        xml=gzip.decompress(read(source['document_XML']));styles=gzip.decompress(read(source['styles_XML']))
        assert sha(xml)==source['document_XML_sha256'] and sha(styles)==source['styles_XML_sha256']
        body=list(ET.fromstring(xml).find(W+'body'))
        mem=io.BytesIO()
        with zipfile.ZipFile(mem,'w')as z:z.writestr('word/document.xml',xml);z.writestr('word/styles.xml',styles)
        audited=reader.audit_document(mem.getvalue())
        top=[(i,b)for i,b in enumerate(body)if b.tag in (W+'p',W+'tbl')]
        assert len(top)==len(audited['blocks'])
        assert all(ET.tostring(b)==ET.tostring(audited['blocks'][j])for j,(_,b)in enumerate(top))
        filtered_to_raw={j:i for j,(i,_)in enumerate(top)}
        byraw=collections.defaultdict(list)
        for p in audited['paragraphs']:byraw[filtered_to_raw[p['body_block_index']]].append({k:v for k,v in p.items()if k!='element'})
        raw_bodies[label]=body;audits[label]=byraw
    for cover in attribution['CR_covers']:
        tid=cover['tdocNumber'];xml=gzip.decompress(read('raw/'+tid+'_document.xml.gz'));styles=gzip.decompress(read('raw/'+tid+'_styles.xml.gz'))
        assert sha(xml)==cover['document_xml_sha256'] and sha(styles)==cover['styles_xml_sha256']
        paragraphs=[''.join(n.text or '' for n in p.iter(W+'t'))for p in ET.fromstring(xml).iter(W+'p')]
        paragraphs=[s for s in paragraphs if s.strip()]
        expected=cover['actual_own_cover_nonempty_paragraphs']
        assert paragraphs[:len(expected)]==expected,('CR cover text differs',tid)
        assert tid in paragraphs[0] and 'CHANGE REQUEST'in paragraphs and '38.213'in paragraphs
    geometry=ungz('source_geometry869.json.gz');patch={r['resolutionId']:r['sourceRecordWindowText']for r in ungz('source_literal_windows869.json.gz')}
    frozen=ungz('whole_original_query_dependencies.json.gz')
    rids=collections.defaultdict(list)
    for n,r,_ in frozen['Agreement']:rids[r].append(n)
    tdocs=collections.defaultdict(list)
    for n,t in frozen['Tdoc']:tdocs[t].append(n)
    refs=collections.defaultdict(set)
    for s,d in frozen['rel_REFERENCES']:refs[s].add(d)
    scope,captured,delta=[],[],[]
    for g in sorted(geometry,key=lambda r:r['resolutionId']):
        rid=g['resolutionId'];label=rid.split('-')[1];lo,hi=g['source_record_raw_body_child_range']
        elements=raw_bodies[label][lo:hi]
        blocks=[{'kind':e.tag.rsplit('}',1)[-1],'text':''.join(n.text or ''for n in e.iter()if n.tag in (W+'t',M+'t'))}for e in elements]
        text='\n'.join(b['text']for b in blocks)
        assert text==patch[rid] and sha(text.encode())==g['source_record_literal_sha256'],rid
        assert len(rids[rid])==1;src=rids[rid][0];existing=refs[src]
        found=kernel.candidate_blocks(blocks)
        scope.append({'resolutionId':rid,'src_id':src,'source_DOCX_sha256':g['source_DOCX_sha256'],'raw_body_child_range':[lo,hi],
                      'raw_window_sha256':sha(text.encode()),'existing_reference_count':len(existing),'capture_candidate_count':len(found)})
        for c0 in found:
            c=dict(c0,resolutionId=rid,src_id=src,source_DOCX_sha256=g['source_DOCX_sha256'],source_raw_range=[lo,hi],intro_raw_body_child=lo+c0['intro_offset'])
            c['full_source_window_text']=text;c['capture_blocks']=[];active=True
            for offset in c0['capture_offsets']:
                absolute=lo+offset;occ=[o for p in audits[label][absolute]for o in p['occurrences']]
                a=all(o['active_formatting_status']=='all_active'for o in occ);active=active and a
                c['capture_blocks'].append(dict(blocks[offset],raw_body_child=absolute,XML_sha256=sha(ET.tostring(elements[offset])),formatting_occurrences=occ,all_relevant_markers_active=a))
            c['all_capture_markers_active']=active
            if not active:c['status']='held_removed_or_mixed_formatting'
            c['matched_existing_Tdoc_nodes']=[];c['missing_Tdoc_ids']=[]
            for tid in c['tdoc_ids']:
                if not tdocs[tid]:c['missing_Tdoc_ids'].append(tid)
                for dst in tdocs[tid]:
                    c['matched_existing_Tdoc_nodes'].append({'tdocNumber':tid,'dst_id':dst,'already_exists':dst in existing})
                    if c['status']=='accepted_explicit_capture_prefix' and dst not in existing:
                        delta.append({'src_id':src,'dst_id':dst,'resolutionId':rid,'tdocNumber':tid,'source_DOCX_sha256':g['source_DOCX_sha256'],'intro_raw_body_child':c['intro_raw_body_child']})
            captured.append(c)
    delta={ (e['src_id'],e['dst_id']):e for e in delta};delta=[delta[k]for k in sorted(delta)]
    assert scope==jsonl('recorded/all869_scope_ledger.jsonl'),'Whole869 scope differs'
    assert captured==jsonl('recorded/all_capture_candidates_full_source_and_formatting.jsonl'),'Capture replay differs'
    assert delta==jsonl('recorded/generic_derived_additive_reference_edges.jsonl'),'Source additive delta differs'
    # Scan every included source window for any literal CR identity whose recorded
    # requested-target role is TS38.213, rather than assuming only old REFERENCES
    # edges or selected identities can enter the prefix.
    spec_ids={n for n,s in frozen['Spec']if s=='38.213'};cr_ids=set(frozen['CR'])
    target_nodes={s for s,d in frozen['rel_MODIFIES']if d in spec_ids and s in cr_ids}
    target_ids={t for n,t in frozen['Tdoc']if n in target_nodes}
    possible={rid:sorted(set(kernel.TDOC.findall(text))&target_ids)for rid,text in patch.items()}
    possible={rid:ids for rid,ids in possible.items()if ids}
    source_entries=load('recorded/all_fourteen_possible_entrants_raw_source_and_frozen_links.json')
    assert possible=={r['resolutionId']:r['raw_target_literal_tdocs']for r in source_entries}
    assert len(possible)==14
    geo={g['resolutionId']:g for g in geometry}
    for entry in source_entries:
        rid=entry['resolutionId'];label=rid.split('-')[1]
        assert entry['source_geometry']==geo[rid]
        for block in entry['source_blocks']:
            e=raw_bodies[label][block['raw_body_child0']]
            assert sha(ET.tostring(e,encoding='utf-8'))==block['xml_sha256']
            assert ''.join(n.text or ''for n in e.iter()if n.tag in (W+'t',M+'t'))==block['text']
    roles=load('recorded/explicit_fourteen_own_role_assessments_NOT_ADMISSION.json')
    assert set(roles)==set(possible) and sum(r['eligible']for r in roles.values())==11
    source11=load('recorded/actual_source_valid11_calendar_prefix_independent_comparison.json')
    assert {r['resolutionId']for r in source11['source_valid11']}=={rid for rid,r in roles.items()if r['eligible']}
    source10=source11['source_valid11'][:]
    # Stable keys implement intDESC,labelDESC,IDASC, preserving the authored ID
    # tie-breaker while distinguishing the two meetings with integer122.
    source10.sort(key=lambda r:r['resolutionId'])
    source10.sort(key=lambda r:r['meetingNumber'],reverse=True)
    source10.sort(key=lambda r:r['meetingNumberInt'],reverse=True)
    assert source10[:10]==source11['exact_calendar_source_prefix10']
    assert {r['resolutionId']for r in source10[:10]}=={r['resolutionId']for r in jsonl('source_selected_records.jsonl')}
    accepted=[c for c in captured if c['status']=='accepted_explicit_capture_prefix'];held=[c for c in captured if c not in accepted]
    assert (len(scope),len(captured),len(accepted),len(held),sum(len(c['matched_existing_Tdoc_nodes'])for c in accepted),len(delta))==(869,21,20,1,38,2)
    controls=kernel.controls();assert all(c['pass']for c in controls)
    assert not tdocs['R1-0000000'],'Missing targets may not be created'
    # Preserve rather than conceal a known recognizer limitation.
    assert kernel.candidate_blocks([{'kind':'p','text':'Final CR R1-2000001 is not agreed.'}])
    return frozen,delta,{'windows':869,'capture_blocks':21,'accepted_blocks':20,'accepted_links':38,'new_links':2,'held_links':1,'literal_possible_entrants':14,'recorded_source_eligible':11,'calendar_source_prefix':10,'generic_controls':len(controls)+1,'known_negation_limitation_reproduced':True}

def projection_recount(frozen,delta):
    db=sqlite3.connect(':memory:')
    for name,ddl in [('Agreement','node_id INTEGER,resolutionId TEXT,contentToken TEXT'),('Meeting','node_id INTEGER,meetingNumber TEXT,meetingNumberInt ANY'),('Spec','node_id INTEGER,specNumber TEXT'),('CR','node_id INTEGER'),('Tdoc','node_id INTEGER,tdocNumber TEXT'),('rel_MADE_AT','src_id INTEGER,dst_id INTEGER'),('rel_REFERENCES','src_id INTEGER,dst_id INTEGER'),('rel_MODIFIES','src_id INTEGER,dst_id INTEGER')]:
        db.execute('CREATE TABLE '+name+'('+ddl+')')
        values=[[v]for v in frozen[name]]if name=='CR'else frozen[name]
        width=len(values[0]);db.executemany('INSERT INTO '+name+' VALUES('+','.join('?'for _ in range(width))+')',values)
    db.executemany('INSERT INTO rel_REFERENCES VALUES(?,?)',[(e['src_id'],e['dst_id'])for e in delta])
    actual=load('recorded/actual_new_full_SQL_calendar_reference.json')
    query=actual['SQL'].replace('COALESCE(a.contentWithEquations,a.content)','a.contentToken')
    rows=[list(r)for r in db.execute(query)]
    pool=[list(r)for r in db.execute(query.rsplit(' LIMIT 10',1)[0])]
    expected=lambda rs:[[r[0],token(r[1]),r[2],r[3]]for r in rs]
    assert rows==expected(actual['rows']) and pool==expected(actual['complete_pool_rows'])
    assert len(pool)==497 and len(rows)==10
    assert len({r[0]for r in pool})==494
    records=[{'resolutionId':r[0]}for r in rows]
    assert collections.Counter(r['resolutionId']for r in records)==collections.Counter(r['resolutionId']for r in jsonl('source_selected_records.jsonl'))
    assert len({r['resolutionId']for r in records})==10
    assert all('UNKNOWN-020'not in r['resolutionId']for r in records)
    # Calendar label correction: the #122bis group precedes #122 for equal integer122.
    assert all(r[2]=='RAN1#122b'for r in rows[2:])
    mapping=load('original_identity_reference_and_role_mapping.json')
    assert len(mapping['all869_original_Agreement_identity_mapping'])==869
    identities={r:n for n,r,_ in frozen['Agreement']};refs=set(map(tuple,frozen['rel_REFERENCES']))
    mods=set(map(tuple,frozen['rel_MODIFIES']));specs=dict(frozen['Spec'])
    for r in mapping['all869_original_Agreement_identity_mapping']:assert identities[r['resolutionId']]==r['src_id']
    generic=mapping['all38_generic_capture_original_reference_and_target_role_mapping'];assert len(generic)==38
    for r in generic:
        assert ((r['src_id'],r['dst_id'])in refs)==r['already_exists']
        assert set(x['spec_node_id']for x in r['target_all_MODIFIES_roles'])=={d for s,d in mods if s==r['dst_id']}
        for m in r['target_all_MODIFIES_roles']:assert specs[m['spec_node_id']]==m['spec_properties']['specNumber']
    edge_map={(r['src_id'],r['dst_id']):r for r in generic}
    ttl='\n'+''.join('<'+edge_map[(e['src_id'],e['dst_id'])]['src_source_iri']+'> spectra:references <'+edge_map[(e['src_id'],e['dst_id'])]['dst_source_iri']+'> .\n'for e in delta)
    assert ttl.encode()==read('recipe/source_derived_additive_references.ttl')
    return {'Agreement_nodes':len(frozen['Agreement']),'all_MADE_AT_edges':len(frozen['rel_MADE_AT']),'full_eligible_four_column_records':len(pool),'unique_eligible_resolutionIds':len({r[0]for r in pool}),'selected_identity_set':len(records)}

def file_sha(p):
    h=hashlib.sha256();n=0
    with open(p,'rb')as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b);n+=len(b)
    return n,h.hexdigest()
def projection(db):
    return {'Agreement':[[n,r,token(c)]for n,r,c in db.execute('SELECT node_id,resolutionId,COALESCE(contentWithEquations,content) FROM Agreement ORDER BY node_id')],
       'Meeting':[list(r)for r in db.execute('SELECT node_id,meetingNumber,meetingNumberInt FROM Meeting ORDER BY node_id')],
       'Spec':[list(r)for r in db.execute('SELECT node_id,specNumber FROM Spec ORDER BY node_id')],
       'CR':[r[0]for r in db.execute('SELECT node_id FROM CR ORDER BY node_id')],
       'Tdoc':[list(r)for r in db.execute('SELECT node_id,tdocNumber FROM Tdoc ORDER BY node_id')],
       **{t:[list(r)for r in db.execute('SELECT src_id,dst_id FROM '+t+' ORDER BY edge_id')]for t in ['rel_MADE_AT','rel_REFERENCES','rel_MODIFIES']}}
def optional_checks(args,frozen):
    pins=load('scope_and_pins.json')['omitted_large_inputs'];done={}
    for arg,key in [('base_ttl','base_TTL'),('base_sql','base_SQL'),('source_sql','source_SQL'),('fts','generic_FTS')]:
        p=getattr(args,arg)
        if p is None:continue
        assert not Path(p).is_symlink(),'Optional input symlink rejected'
        n,s=file_sha(p);assert s==pins[key]['sha256'] and ('bytes'not in pins[key]or n==pins[key]['bytes']),(key,'pin mismatch')
        if arg=='base_ttl':
            h=hashlib.sha256()
            with open(p,'rb')as f:
                for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
            h.update(read('recipe/source_derived_additive_references.ttl'));assert h.hexdigest()==pins['source_TTL']['sha256']
            done[key]='PIN_AND_EXACT_BASE_PLUS_GENERIC_APPEND_REPLAY_PASS'
        elif arg in ['base_sql','source_sql']:
            db=sqlite3.connect('file:'+str(Path(p).resolve())+'?mode=ro&immutable=1',uri=True);db.execute('PRAGMA query_only=ON')
            if arg=='base_sql':assert projection(db)==frozen;done[key]='PIN_AND_ALL_QUERY_DEPENDENCY_PROJECTION_ROWS_PASS'
            else:
                actual=load('recorded/actual_new_full_SQL_calendar_reference.json');assert [list(r)for r in db.execute(actual['SQL'])]==actual['rows'];done[key]='PIN_AND_FOUR_COLUMN_REFERENCE_REPLAY_PASS'
            db.close()
        else:done[key]='PIN_ONLY_NO_FTS_QUERY_OR_RECONSTRUCTION'
    return done
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--base-ttl');parser.add_argument('--base-sql');parser.add_argument('--source-sql');parser.add_argument('--fts');args=parser.parse_args()
    manifest=closed_inventory();definition=load('definition.json')
    canonical=json.dumps(definition,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    assert sha(canonical)==manifest['scope_and_provenance']['repair_sha256']=='7c0122437095d695d0b13dd316463dd2df31f63c8dd41b88e64e090507c796b2'
    assert sha(read('definition.json'))=='2d563b6159f8ae2ae21e1cceefa154ba56ea4d9b5c60ed4e79591d133c7e3cbd'
    assert sha(read('reviews/primary_seven_unit_review.json'))=='21551c521043d9d7ab0aab5f457c74109d8c0cdd44228ed545080c616c19de6f'
    assert sha(read('reviews/secondary_seven_unit_review.json'))=='509cf51859eaf436e89f6501212a78103f0bbe92663adca50abb4da62c2450cd'
    frozen,delta,source=raw_source_replay();counts=projection_recount(frozen,delta);optional=optional_checks(args,frozen)
    print(json.dumps({'status':'PASS','scope':'FINITE_SOURCE_REPLAY_AND_CONDITIONAL_FROZEN_DEPENDENCY_RECOUNT','id':'RAN1_P3_CQ024','source':source,'projection':counts,'optional_explicit_checks':optional,'original560_increment':0,'native_executed':False,'API_calls':0,'human_expert_n':0},ensure_ascii=False))
if __name__=='__main__':main()
