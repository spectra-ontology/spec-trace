"""Replay the unchanged RedCap Section question and observed source-role recovery."""
import collections,csv,gzip,hashlib,io,json,re,sqlite3,sys
from pathlib import Path
import xml.etree.ElementTree as ET
if sys.flags.optimize:raise SystemExit('Enabled checks required')
sys.dont_write_bytecode=True
INVENTORY_SHA256='62064bfaeba603195218794e5aac2fd40797890cfdfcef990acb94545b75e8ba'
N={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};W='{'+N['w']+'}'
def digest(b):return hashlib.sha256(b).hexdigest()
def read(D,n):
 p=D/n
 if p.is_file():return json.loads(p.read_bytes())
 return json.loads(gzip.decompress((D/(n+'.gz')).read_bytes()))
def active_text(x):
 if x.tag in {W+'del',W+'moveFrom'}:return ''
 return (x.text or '') if x.tag==W+'t' else ''.join(active_text(y) for y in x)
def body_blocks(body):
 return [{'body_child':i,'tag':x.tag.removeprefix(W),'text':active_text(x),'table_rows':[[active_text(tc) for tc in row.findall('w:tc',N)] for row in x.findall('w:tr',N)]} for i,x in enumerate(body)]

def parse_original_query(cypher):
 """Exact generic three-node path grammar, including either edge direction."""
 ident=r'[A-Za-z_][A-Za-z0-9_]*'
 node=r'\(('+ident+r'):('+ident+r')(?:\s*\{('+ident+r'):\s*\'([^\']*)\'\})?\)'
 edge=r'(<-|-)[\[]:('+ident+r')\](->|-)'
 m=re.fullmatch(r'MATCH\s+'+node+edge+node+edge+node+r'\s+RETURN\s+(.+?)\s+ORDER BY\s+('+ident+r'\.'+ident+r')',cypher)
 assert m,'Original query outside exact generic path grammar'
 g=m.groups();nodes=[]
 for offset in [0,7,14]:
  v,label,k,value=g[offset:offset+4];nodes.append({'variable':v,'label':label,'properties':{k:value} if k else {}})
 fields=[x.strip() for x in g[18].split(',')];order=g[19]
 aliases={x['variable']:x['label'] for x in nodes}
 assert len(aliases)==3 and len(fields)==len(set(fields))
 for f in fields+[order]:
  v,k=f.split('.');assert v in aliases and re.fullmatch(ident,k)
 relations=[];sql='SELECT '+','.join(f'{f} AS "{f}"' for f in fields)+' FROM "'+nodes[0]['label']+'" '+nodes[0]['variable']
 params=[]
 for i,offset in enumerate([4,11]):
  left,kind,right=g[offset:offset+3];assert (left,right) in {('-','->'),('<-','-')}
  av=nodes[i]['variable'];bv=nodes[i+1]['variable'];forward=left=='-'
  first,last=('src_id','dst_id') if forward else ('dst_id','src_id')
  src,dst=(av,bv) if forward else (bv,av)
  relations.append({'source':src,'type':kind,'target':dst})
  sql+=f' JOIN edge e{i} ON e{i}.{first}={av}.node_id AND e{i}.rel_type=? JOIN "{nodes[i+1]["label"]}" {bv} ON {bv}.node_id=e{i}.{last}'
  params.append(kind)
 where=[]
 for n in nodes:
  for k,v in n['properties'].items():where.append(n['variable']+'."'+k+'"=?');params.append(v)
 sql+=' WHERE '+' AND '.join(where)+' ORDER BY '+order
 return {'nodes':nodes,'relationships':relations,'projections':fields,'order_by':order},sql,params


def memory_graph(slice_data, original_schemas):
    c = sqlite3.connect(':memory:')
    c.row_factory = sqlite3.Row
    records = {}
    for r in slice_data['records']:
        assert r['node_id'] not in records
        records[r['node_id']] = {'labels': json.loads(r['labels_json']),
                                 'properties': json.loads(r['properties_json'])}
    schemas = {}
    for r in records.values():
        for label in r['labels']:
            assert re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', label)
            schemas.setdefault(label, set()).update(r['properties'])
    for label, columns in original_schemas.items():
        schemas.setdefault(label, set()).update(x['name'] for x in columns if x['name'] != 'node_id')
    for label, properties in schemas.items():
        names = sorted(properties)
        assert all(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', k) for k in names)
        columns = ','.join('"' + k + '"' for k in names)
        c.execute('CREATE TABLE "' + label + '"(node_id INTEGER PRIMARY KEY' + (',' + columns if columns else '') + ')')
        for nid, r in records.items():
            if label in r['labels']:
                vals = [r['properties'].get(k) for k in names]
                vals = [json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else x for x in vals]
                c.execute('INSERT INTO "' + label + '" VALUES(' + ','.join('?' for _ in range(1 + len(names))) + ')', [nid] + vals)
    c.execute('CREATE TABLE edge(edge_id INTEGER PRIMARY KEY,src_id INTEGER,rel_type TEXT,dst_id INTEGER)')
    for e in slice_data['edges']:
        assert e['src_id'] in records and e['dst_id'] in records
        c.execute('INSERT INTO edge VALUES(?,?,?,?)', [e[k] for k in ['edge_id', 'src_id', 'rel_type', 'dst_id']])
    for kind in {e['rel_type'] for e in slice_data['edges']}:
        assert re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', kind)
        c.execute('CREATE TABLE "rel_' + kind + '" AS SELECT edge_id,src_id,dst_id FROM edge WHERE rel_type=?', (kind,))
    c.execute('CREATE TABLE node(node_id INTEGER PRIMARY KEY,labels TEXT)')
    for nid,r in records.items():
        c.execute('INSERT INTO node VALUES(?,?)',(nid,json.dumps(r['labels'],separators=(',',':'))))
    return c, records


def semantic_checks(D):
 q=read(D,'contract/original_question_and_query.json');orig=read(D,'contract/original_benchmark_record.jsonl')
 assert orig==q['original_record'] and orig['id']=='RAN1_P5_CQ3-1'
 assert digest((D/'contract/original_benchmark_record.jsonl').read_bytes())==q['raw_record_sha256']
 assert digest(orig['question_en'].encode())==q['question_sha256']=='207dc910ba229fbffeca93071efafa061ff11d5a785839b0b1d49c6e9ce1146c'
 assert digest(orig['cypher'].encode())==q['query_sha256']
 author=read(D,'contract/original_author_CQ_dataset.json')
 aq=[x for x in author['questions'] if x['id']=='CQ3-1'];assert aq==[q['original_Korean_record']] and aq[0]['cypher']==orig['cypher']
 criteria=read(D,'contract/criteria.json')
 assert digest((D/'contract/criteria.json').read_bytes())=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
 primary=read(D,'contract/primary_seven_unit_review.json');contract=read(D,'contract/bounded_source_role_contract.json')
 assert primary['id']==orig['id'] and primary['question_sha256']==q['question_sha256']
 assert primary['recommendation']==contract['classification_recommendation']=='unsupported_frozen_data'
 assert primary['nonblind_AI'] is True and primary['expert_validation_n']==0
 assert primary['whole_original_question_verified_pass'] is False and primary['source_grounded_partial_recovery'] is True
 assert contract['complete_source_enriched_oracle_created'] is False
 assert [x['semantic_unit'] for x in primary['semantic_units']]==criteria['semantic_units']
 secondary=D/'contract/ROOT_secondary_review.json'
 if secondary.is_file():
  sec=read(D,'contract/ROOT_secondary_review.json')
  assert sec['id']==orig['id'] and sec.get('classification',sec.get('recommendation',sec.get('decision')))=='unsupported_frozen_data'
  assert [x.get('semantic_unit',x.get('unit')) for x in sec.get('semantic_units',sec.get('units',[]))]==criteria['semantic_units']
  assert sec['reviewer']=='ROOT AI agent' and sec['nonblind_AI'] is True and sec['expert_validation_n']==0
  assert sec['question_sha256']==q['question_sha256'] and sec['query_sha256']==q['query_sha256']
  assert sec['criteria_sha256']==digest((D/'contract/criteria.json').read_bytes())
  assert sec['primary_review_sha256']==digest((D/'contract/primary_seven_unit_review.json').read_bytes())
  assert sec['source_capsule_sha256']==digest((D/'contract/readable_actual_original_source_capsule.json').read_bytes())
  root_actual=read(D,'provenance/actual_ROOT_direct_11_sources_and_frozen_9_roles_v1.json')
  assert sec['actual_ROOT_execution_receipt']['sha256']==digest((D/'provenance/actual_ROOT_direct_11_sources_and_frozen_9_roles_v1.json').read_bytes())
  assert root_actual['status']=='PASS_ROOT_INDEPENDENT_DIRECT_ORIGINAL_SOURCE_AND_FROZEN_ROLE_REPLAY'
  assert root_actual['reviewer']=='ROOT AI agent' and root_actual['id']==orig['id']
  assert root_actual['source_XML_style_pair_n']==11 and root_actual['SQL_role_n']==9
  assert root_actual['semantic_CR_candidates']==146 and root_actual['semantic_candidate_membership_equal'] is True
  assert root_actual['frozen_DB_before_sha256']==root_actual['frozen_DB_after_sha256']=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
  assert root_actual['API_calls']==root_actual['native_calls']==root_actual['public_writes']==0
 else:raise AssertionError('Final source-role diagnostic requires the actual independent ROOT review')
 sources=[read(D,'source/TR38875_all_original_active_body_blocks.json')]+read(D,'source/actual_original_amendment_and_TS_active_body_blocks.json')
 assert len(sources)==contract['actual_original_source_XML_style_pairs']==11
 metadata=read(D,'source/source_XML_metadata.json');assert len(metadata)==11
 root_sources={x['key']:x for x in root_actual['actual_direct_original_source_reopens']};assert len(root_sources)==11
 by_key={};source_n=0
 for s,m in zip(sources,metadata):
  assert m['key']==s.get('key','TR38875')
  xml=gzip.decompress((D/m['retained_source_directory']/'document.xml.gz').read_bytes());sty=gzip.decompress((D/m['retained_source_directory']/'styles.xml.gz').read_bytes())
  for b,p in [(xml,m['document_xml']),(sty,m['styles_xml'])]:assert len(b)==p['bytes'] and digest(b)==p['sha256']
  body=ET.fromstring(xml).find('w:body',N);assert body is not None
  ET.fromstring(sty)
  blocks=body_blocks(body);assert blocks==s['blocks']
  by_key[m['key']]={'blocks':blocks,'metadata':m};source_n+=1
  rs=root_sources[m['key']]
  assert rs['archive_sha256']==m['archive']['sha256'] and rs['document_xml_sha256']==digest(xml) and rs['styles_xml_sha256']==digest(sty)
  assert rs['actual_body_children']==len(blocks)
 tr=by_key['TR38875']['blocks']
 assert any('This document captures the findings from the study item' in b['text'] for b in tr)
 assert any('8.2.5Analysis of specification impacts'==b['text'] for b in tr)
 impacts=read(D,'source/TR38875_all_actual_analysis_of_specification_impact_sections.json')
 actual=[s for s in impacts['sections'] if s['heading']['body_child']>200];assert len(actual)==12
 for s in impacts['sections']:
  assert tr[s['heading']['body_child']]==s['heading']
  assert [tr[b['body_child']] for b in s['blocks']]==s['blocks']
 assert 'foreseen' in tr[1080]['text'] and 'may include' in tr[1081]['text']
 assert '17 (new), 17.1 (new), 17.2 (new)' in by_key['CR2112935']['blocks'][6]['text']
 assert by_key['CR2112935']['blocks'][52]['text']=='17UE with reduced capabilities'
 assert by_key['CR2112935']['blocks'][54]['text']=='17.1RedCap UE procedures '
 assert '6.1.2.1' in by_key['CR2112954']['blocks'][6]['text'] and 'HD-FDD RedCap UE' in by_key['CR2112954']['blocks'][6]['text']
 assert by_key['CR2112954']['blocks'][11]['text']=='6.1.2.1Resource allocation in time domain'
 assert '5.3.2' in by_key['CR2401911']['blocks'][6]['text'] and 'initialUplinkBWP-RedCap' in by_key['CR2401911']['blocks'][16]['text']
 assert by_key['TS38211']['blocks'][638]['text']=='5.3OFDM baseband signal generation'
 assert by_key['TS38212']['blocks'][720]['text']=='5.5Code block concatenation'
 assert by_key['TS38213']['blocks'][5045]['text']=='17UE with reduced capabilities'
 capsule=read(D,'contract/readable_actual_original_source_capsule.json')
 assert len(capsule['all_12_actual_TR_specification_impact_analysis_sections'])==12
 for s in capsule['source_amendment_and_TS_capsules']:
  for b in s['selected_original_blocks']:assert by_key[s['key']]['blocks'][b['body_child']]==b
 graph=read(D,'frozen/source_records_and_edges.json');schemas=read(D,'frozen/original_SQL_table_schemas.json')
 c,records=memory_graph(graph,schemas)
 diag=read(D,'frozen/actual_immutable_SQL_diagnostics.json');extra=read(D,'frozen/actual_additional_SQL_diagnostics.json')
 own=read(D,'frozen/all_RedCap_candidate_frozen_CR_role_summary.json')['direct_study_workitem_typed_CR_query']
 ast,sql,params=parse_original_query(orig['cypher'])
 generic=[dict(x) for x in c.execute(sql,params)]
 assert ast['projections']==['tr.trNumber','tr.trTitle','ti.impactType','s.sectionId','ti.impactDescription']
 assert generic==diag['original_projection']['rows'] and len(generic)==2
 assert diag['inverse_alias_projection']['rows']==generic
 checked=[]
 root_roles={x['role']:x for x in root_actual['actual_immutable_SQL_roles']};assert len(root_roles)==9
 for group in [diag,extra,{'direct_study_workitem_typed_CR_query':own}]:
  for name,x in group.items():
   assert digest(x['sql'].encode())==x['sql_sha256']
   actual=[dict(r) for r in c.execute(x['sql'])]
   assert actual==x['rows'] and len(actual)==x['row_count'],name
   checked.append({'role':name,'rows':len(actual)})
   rr=root_roles[name]
   assert rr['actual_rows']==len(actual) and rr['sql_sha256']==x['sql_sha256']
   assert rr['complete_rows_sha256']==digest(json.dumps(actual,ensure_ascii=False,sort_keys=True).encode())
 assert len(checked)==9 and own['rows']==[]
 assert len(diag['all_WorkItem_identities']['rows'])==423
 raw=diag['all_own_impacts_specs_and_optional_sections']['rows'];assert len(raw)==3
 assert [(r['specNumber'],r['affectedSection'],r['sectionId']) for r in raw]==[('38.211','5.3','38.211-Rel-19-5.3'),('38.212','5.5','38.212-Rel-19-5.5'),('38.213','8.9',None)]
 assert all(r['releaseName']=='Rel-17' for r in raw)
 assert len(diag['own_affected_sections_same_number_all_spec_releases']['rows'])==10
 mapping=list(csv.DictReader(io.StringIO((D/'source/original_tr_impact_mapping.csv').read_text())))
 own_mapping=[r for r in mapping if r['trNumber']=='38.875'];assert len(own_mapping)==3
 assert [(r['specNumber'],r['affectedSection'],r['impactDescription']) for r in raw]==[(r['impactsSpec'],r['impactsSection'],r['impactDescription']) for r in own_mapping]
 cand=diag['all_RedCap_named_workitem_CR_TS_Section_candidates']['rows']
 core=[r for r in cand if r['workItemCode']=='NR_redcap-Core' and r['id']]
 assert len({r['node_id'] for r in core})==137 and len({r['sectionId'] for r in core if r['sectionId']})==78
 intro=[r for r in core if r['id']=='tdoc:R1-2112935'];assert len(intro)==1 and intro[0]['clausesAffected'] is None and intro[0]['sectionId'] is None
 known=[r for r in core if r['id']=='tdoc:R1-2112954'];assert len(known)==1 and known[0]['sectionId']=='38.214-Rel-17-6.1.2.1'
 semantic=extra['all_semantic_CR_candidates'];assert len(semantic['candidate_node_ids_from_original_full_property_scan'])==146
 all_named={r['node_id'] for r in cand if r['id']};assert len(set(semantic['candidate_node_ids_from_original_full_property_scan'])-all_named)==21
 c.close()
 return {'status':'PASS','id':orig['id'],'classification':'unsupported_frozen_data','two_nonblind_AI_reviews':secondary.is_file(),'original_source_XML_style_pairs':source_n,'original_generic_AST':ast,'original_query_diagnostic_rows':len(generic),'original_SQL_role_checks':checked,'full_recovery_incident_core_n':len(graph['complete_incident_core_node_ids']),'source_record_n':len(graph['records']),'incident_edge_n':len(graph['edges']),'expert_validation_n':0,'new_admissions':0,'model_API_calls':0,'native_calls':0,'scope':'Portable original-source and complete observed recovery-role diagnostics, with positive actual amendments. No complete source-enriched answer oracle is created.'}
def main():
 D=Path(__file__).resolve().parent
 assert digest((D/'immutable_inventory.json').read_bytes())==INVENTORY_SHA256
 inv=read(D,'immutable_inventory.json')['files']
 observed={p.relative_to(D).as_posix() for p in D.rglob('*') if p.is_file()}
 assert observed==set(inv)|{'immutable_inventory.json','manifest.json','reproduce.py'}
 for n,v in inv.items():
  p=D/n;assert p.is_file() and not p.is_symlink();b=p.read_bytes();assert len(b)==v['bytes'] and digest(b)==v['sha256'],n
 manifest=read(D,'manifest.json');ver=(D/'reproduce.py').read_bytes()
 assert manifest['verifier']=={'path':'reproduce.py','bytes':len(ver),'sha256':digest(ver)}
 print(json.dumps(semantic_checks(D),ensure_ascii=False))
if __name__=='__main__':main()
