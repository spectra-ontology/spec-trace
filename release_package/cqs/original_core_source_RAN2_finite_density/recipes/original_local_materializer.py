#!/usr/bin/env python3
"""Create a separate frozen-RAN2 clone plus generic finite dependency facts.

Execution requires a pinned matching secondary semantic review and an explicit
--execute. No native service, model/API or public repository is touched. All
original facts/storage remain byte/value identical; the broader latest-source
hierarchy/reference/caption replacement policy is not used.
"""
from pathlib import Path
from collections import Counter,defaultdict
import argparse,gzip,hashlib,importlib.util,json,re,shutil,sqlite3,sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if(p/'CLAUDE.md').exists())
OUT=HERE.parent;N=OUT/'RAN2_density_finite_identity_dependency_variant_v2'
V=OUT/'RAN2_density_all14_declared_source_vs_frozen_owned_facts_v2'
L=OUT/'RAN2_density_latest14_release_slice_reconstruction_proposal_v1'
T=OUT/'RAN2_density_canonical_target_and_Section_recipe_v2/prospective_current64_small_recipe_v1'
BASE_TTL=ROOT/'release_package/kg/per_wg/RAN2-body.ttl'
BASE_SQL=ROOT/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/relational/RAN2.sqlite'
TTL_SHA='f0997bbfb5fd5844837514cd29cfe943b8cb2d0240f0ea5579c5e69b4e547d6c'
SQL_SHA='8c4c23348e2d0861e8ecf11393eb01a65d2add247b3e5f0df68f093500d8ddfd'
PACKET_SHA='1b70409a85d3ce60ea9f0e813756ffde1a49694d7483515c38d0495ef6974aeb'
LEXER=ROOT.parent/'spectra-public/spec-trace/release_package/pipeline/load_released_kg.py'
LEXER_SHA='9499ac120ea4fcf1c2707f6e3151e399530d9b4f43f5aec9d2d93040792d6e25'
BUILDER=HERE/'build_generic_graph_corpus.py'
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def load(p):return json.loads(p.read_text())
def gz(p):
 with gzip.open(p,'rt')as f:return json.load(f)
def rows(p):
 with gzip.open(p,'rt')as f:return [json.loads(x)for x in f]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def pin(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def save(name,x):
 with(HERE/name).open('x')as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def mod(p,name):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def ro(p):
 c=sqlite3.connect(p.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);c.execute('PRAGMA query_only=ON');c.execute('PRAGMA cache_size=-32768');return c
def quote(x):return '"'+x.replace('"','""')+'"'
def verify_manifest(directory):
 for r in load(directory/'manifest.json')['files']:
  p=ROOT/r['path']if r['path'].startswith('logs/')else directory/r['path']
  assert p.stat().st_size==r['bytes']and sha(p)==r['sha256'],p

def derive():
 """Use full source populations, never an answer/spec/ID whitelist."""
 products=gz(V/'all14_declared_parsed_source_products.json.gz')
 projection=gz(V/'complete_baseline_phase3_identity_projection.json.gz')
 old={tuple(x['identity']):x['nodes'][0]for x in projection['records']};assert all(len(x['nodes'])==1for x in projection['records'])
 source={s['sectionId']:(p,s)for p in products for s in p['sections']}
 missing={('Section',x)for x in source}-set(old)
 stems={old[k]['source_iri'][:-len(k[1])]for k in old if k[0]=='Section'and old[k]['source_iri'].endswith(k[1])};assert len(stems)==1;stem=next(iter(stems))
 byfile=defaultdict(list)
 for r in gz(L/'all_latest14_source_Section_heading_raw_and_complete_owned_reference_inputs.json.gz'):byfile[r['heading_raw_OOXML']['source_path']].append(r)
 nodes=[];edges=[]
 for path,witnesses in sorted(byfile.items()):
  stack=[]
  for witness in sorted(witnesses,key=lambda r:r['heading_raw_OOXML']['raw_body_child_ordinal_zero_based']):
   style=witness['heading_raw_OOXML']['style'];level=1 if style=='Heading 8'else int(style[8:])if re.fullmatch(r'Heading [1-7]',style)else 6 if style=='H6'else None
   assert level is not None
   while stack and stack[-1][1]>=level:stack.pop()
   ident=witness['sectionId']
   if ('Section',ident)in missing:
    p,s=source[ident];assert level==4 and stack and stack[-1][1]==3
    parent=old['Section',stack[-1][0]];owner=old['Spec',p['spec_number'],p['release']]
    assert parent['properties']['level']==3 and s['parentSectionId']==stack[-1][0]
    iri=stem+ident;props={k:s[k]for k in ['sectionId','sectionNumber','sectionTitle','isVoid']};props['level']=level
    nodes.append({'identity':['Section',ident],'source_iri':iri,'labels':['Section'],'properties':props})
    edges.extend([{'source_iri':iri,'relationship':'BELONGS_TO_SPEC','target_iri':owner['source_iri']},{'source_iri':iri,'relationship':'PARENT_SECTION','target_iri':parent['source_iri']},{'source_iri':parent['source_iri'],'relationship':'HAS_SUB_SECTION','target_iri':iri}])
   stack.append((ident,level))
 m=mod(T/'replay_generic_modified_spec_delta.py','generic_complete_CR_source_metadata')
 metadata,unknown=m.derive(rows(T/'evidence/all_frozen_CR_to_MODIFIES_source_comparisons.jsonl.gz'),rows(T/'evidence/all_retained_input_CR_MODIFIES_metadata_witnesses.jsonl.gz'),load(T/'evidence/all_original_Spec_nodes.json'))
 assert len(metadata)==107 and len(nodes)==8 and len(edges)==24
 edges=[{'source_iri':d['source_CR_iri'],'relationship':'MODIFIES','target_iri':d['target_source_iri']}for d in metadata]+edges
 assert canon(nodes)==canon(load(N/'generic_derived_eight_Section_nodes.json'))
 assert edges==load(N/'generic_derived_all_131_additive_edges.json')
 return nodes,edges

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--execute',action='store_true');parser.add_argument('--secondary-review',type=Path,required=True);args=parser.parse_args()
 assert args.execute,'This is a draft until ROOT authorizes --execute after the source gate.'
 assert sha(N/'manifest.json')==PACKET_SHA
 for d in [N,V,L,T]:verify_manifest(d)
 definition=load(N/'prospective_finite_dependency_source_variant_definition.json');criteria=load(N/'criteria.json')
 for source_pin in definition['source_input_pins']:
  path=ROOT/source_pin['path'];assert path.stat().st_size==source_pin['bytes']and sha(path)==source_pin['sha256'],path
 schema=mod(OUT/'RAN4_source93_exact_DESC_portable_staging_v1/bundle_v3/contract/review_schema.py','record_schema')
 for p in [N/'primary_exact_seven_unit_finite_dependency_source_policy_review.json',args.secondary_review]:schema.check_pass(load(p),definition['question_en'],criteria['semantic_units'],criteria_sha=definition['criteria_sha256'],identity_key='repair_sha256',identity_sha=definition['repair_sha256'])
 assert args.secondary_review.resolve()!= (N/'primary_exact_seven_unit_finite_dependency_source_policy_review.json').resolve()
 assert sha(args.secondary_review)!=sha(N/'primary_exact_seven_unit_finite_dependency_source_policy_review.json'),'A copied primary is not an independent secondary.'
 assert sha(BASE_SQL)==SQL_SHA and sha(BASE_TTL)==TTL_SHA and sha(LEXER)==LEXER_SHA
 nodes,edges=derive();db=ro(BASE_SQL)
 oldmaxnode=db.execute('SELECT max(node_id)FROM node').fetchone()[0];oldmaxedge=db.execute('SELECT max(edge_id)FROM edge').fetchone()[0]
 iri_to_id=dict(db.execute('SELECT source_iri,node_id FROM _node_record'))
 source_iristem={iri[:-len(ident)]for iri,ident in db.execute('SELECT r.source_iri,s.sectionId FROM _node_record r JOIN Section s USING(node_id)')if iri.endswith(ident)}
 identity_stem={iri[:-len(ident)]for iri,ident in db.execute('SELECT i.iri,s.sectionId FROM node_identity i JOIN Section s USING(node_id)')if iri.endswith(ident)}
 assert len(source_iristem)==len(identity_stem)==1
 idstem=next(iter(identity_stem));assert all(db.execute('SELECT iri FROM node_identity WHERE node_id=?',(nid,)).fetchone()[0]==idstem+ident for nid,ident in db.execute('SELECT node_id,sectionId FROM Section'))
 for i,n in enumerate(sorted(nodes,key=lambda n:n['source_iri']),1):
  assert n['source_iri']not in iri_to_id
  n['new_node_id']=oldmaxnode+i;iri_to_id[n['source_iri']]=n['new_node_id'];n['original_storage_identity_iri']=idstem+n['properties']['sectionId']
 for e in edges:
  e['src_id']=iri_to_id[e['source_iri']];e['dst_id']=iri_to_id[e['target_iri']]
  assert not db.execute('SELECT 1 FROM edge WHERE src_id=?AND rel_type=?AND dst_id=?',(e['src_id'],e['relationship'],e['dst_id'])).fetchone()
 # Serialization retains the entire old TTL as an exact byte prefix.
 lexer=mod(LEXER,'pinned_public_graph_lexer');patch='\n'
 for n in sorted(nodes,key=lambda n:n['source_iri']):
  patch+='<'+n['source_iri']+'> a spectra:Section ;\n'
  fields=sorted(n['properties'].items())
  for i,(key,value)in enumerate(fields):
   literal=canon(value)
   patch+='    spectra:'+key+' '+literal+(' .\n'if i==len(fields)-1 else' ;\n')
 for e in sorted(edges,key=lambda e:(e['source_iri'],e['relationship'],e['target_iri'])):
  pred=lexer.screaming_to_camel(e['relationship']);assert lexer.decode_rel_type(pred)==e['relationship']
  patch+='<'+e['source_iri']+'> spectra:'+pred+' <'+e['target_iri']+'> .\n'
 (HERE/'generic_source_additive_patch.ttl').write_text(patch)
 target_ttl=HERE/'RAN2-finite-dependency-body.ttl';target_sql=HERE/'RAN2-finite-dependency.sqlite'
 assert not target_ttl.exists()and not target_sql.exists()
 with BASE_TTL.open('rb')as a,target_ttl.open('xb')as b:shutil.copyfileobj(a,b);b.write(patch.encode())
 shutil.copy2(BASE_SQL,target_sql);w=sqlite3.connect(target_sql);w.execute('PRAGMA foreign_keys=ON');w.execute('BEGIN IMMEDIATE')
 native_type=lambda x:'boolean'if isinstance(x,bool)else'integer'if isinstance(x,int)else'string'if isinstance(x,str)else None
 for n in nodes:
  i=n['new_node_id'];props=n['properties'];labels=canon(n['labels'])
  w.execute('INSERT INTO _node_record VALUES(?,?,?,?)',(i,n['source_iri'],labels,canon(props)));w.execute('INSERT INTO node VALUES(?,?)',(i,labels));w.execute('INSERT INTO node_label VALUES(?,?)',(i,'Section'));w.execute('INSERT INTO node_identity VALUES(?,?)',(i,n['original_storage_identity_iri']))
  for k,v in props.items():
   assert native_type(v)is not None;w.execute('INSERT INTO node_property VALUES(?,?,?,?)',(i,k,native_type(v),canon(v)))
  keys=['isVoid','level','sectionId','sectionNumber','sectionTitle'];w.execute('INSERT INTO Section(node_id,'+','.join(map(quote,keys))+')VALUES('+','.join('?'for _ in range(6))+')',(i,*[props[k]for k in keys]))
 for i,e in enumerate(sorted(edges,key=lambda e:(e['source_iri'],e['relationship'],e['target_iri'])),1):
  eid=oldmaxedge+i;w.execute('INSERT INTO edge VALUES(?,?,?,?)',(eid,e['src_id'],e['relationship'],e['dst_id']));w.execute('INSERT INTO '+quote('rel_'+e['relationship'])+' VALUES(?,?,?)',(eid,e['src_id'],e['dst_id']))
 w.commit();assert w.execute('PRAGMA integrity_check').fetchone()[0]=='ok';w.close()
 new=ro(target_sql);new.execute('ATTACH DATABASE ? AS frozen',(BASE_SQL.resolve().as_uri()+'?mode=ro&immutable=1',))
 assert db.execute('SELECT type,name,tbl_name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type,name').fetchall()==new.execute('SELECT type,name,tbl_name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type,name').fetchall()
 names=[r[0]for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")];assert len(names)==79
 node_tables={'_node_record','node','node_label','node_property','node_identity','Section'};edge_tables={'edge',*('rel_'+e['relationship']for e in edges)};preserved=[]
 for name in names:
  q=quote(name);cols=[r[1]for r in db.execute('PRAGMA table_info('+q+')')];expr=','.join(quote(k)+',typeof('+quote(k)+')'for k in cols)
  suffix=' WHERE node_id<='+str(oldmaxnode)if name in node_tables else' WHERE edge_id<='+str(oldmaxedge)if name in edge_tables else''
  before='SELECT '+expr+' FROM frozen.'+q;after='SELECT '+expr+' FROM main.'+q+suffix
  assert new.execute('SELECT count(*)FROM('+before+' EXCEPT '+after+')').fetchone()[0]==0,name
  assert new.execute('SELECT count(*)FROM('+after+' EXCEPT '+before+')').fetchone()[0]==0,name
  nold=db.execute('SELECT count(*)FROM '+q).fetchone()[0];nretained=new.execute('SELECT count(*)FROM '+q+suffix).fetchone()[0];assert nold==nretained
  preserved.append({'table':name,'old_rows':nold,'typed_original_rows_preserved':True,'new_rows':new.execute('SELECT count(*)FROM '+q).fetchone()[0]-nold})
 for name in names:
  if name.startswith('rel_'):
   typ=name[4:];q=quote(name)
   assert new.execute('SELECT count(*)FROM '+q+' r LEFT JOIN edge e ON e.edge_id=r.edge_id WHERE e.edge_id IS NULL OR e.src_id!=r.src_id OR e.dst_id!=r.dst_id OR e.rel_type!=?',(typ,)).fetchone()[0]==0
   assert new.execute('SELECT count(*)FROM '+q).fetchone()[0]==new.execute('SELECT count(*)FROM edge WHERE rel_type=?',(typ,)).fetchone()[0]
 assert new.execute('SELECT count(*)FROM node').fetchone()[0]==156296 and new.execute('SELECT count(*)FROM edge').fetchone()[0]==939168
 with BASE_TTL.open('rb')as a,target_ttl.open('rb')as b:
  for data in iter(lambda:a.read(1048576),b''):assert b.read(len(data))==data
  assert b.read()==patch.encode()
 builder=mod(BUILDER,'generic_all_fact_corpus');records,parsed_edges=builder.read_graph(target_ttl,builder.load_lexer(LEXER))
 assert len(records)==156296
 for iri,labels,props in new.execute('SELECT source_iri,labels_json,properties_json FROM _node_record'):
  r=records[iri];assert r['labels']==sorted(json.loads(labels))and canon(r['properties'])==canon(json.loads(props)),iri
 alliri={i:iri for i,iri in new.execute('SELECT node_id,source_iri FROM _node_record')}
 expected_edges={(alliri[a],t,alliri[b])for a,t,b in new.execute('SELECT src_id,rel_type,dst_id FROM edge')};assert parsed_edges==expected_edges and len(parsed_edges)==939168
 save('actual_all79_tables_and_full_graph_fact_equivalence.json',{'status':'PASS_ALL_OLD_TYPED_FACTS_PRESERVED_PLUS_FINITE_ADDITIONS','all79_storage_tables':preserved,'old_TTL_exact_byte_prefix':True,'whole_nodes':len(records),'whole_edges':len(parsed_edges),'all_global_and_typed_edges_consistent':True,'public_lexer':pin(LEXER),'generic_builder':pin(BUILDER),'new_SQL':pin(target_sql),'new_TTL':pin(target_ttl),'original560_increment':0,'full_source_graph_fidelity_claim':False})
 # Evaluation-only query reference: downstream from full graph construction.
 sql="""WITH cr_counts AS(SELECT hub.node_id,hub.specNumber,count(cr.node_id)AS crCnt FROM Spec hub JOIN rel_MODIFIES x ON x.dst_id=hub.node_id JOIN CR cr ON cr.node_id=x.src_id WHERE hub.specRelease IS NULL GROUP BY hub.node_id), ranked_releases AS(SELECT c.*,rk.node_id AS rk_id,CAST(replace(rk.specRelease,'Rel-','')AS INTEGER)AS releaseInt,row_number()OVER(PARTITION BY c.node_id ORDER BY CAST(replace(rk.specRelease,'Rel-','')AS INTEGER)DESC)AS rank FROM cr_counts c JOIN edge ir ON ir.dst_id=c.node_id AND ir.rel_type='IN_RELEASE_OF' JOIN Spec rk ON rk.node_id=ir.src_id), density_rows AS(SELECT r.specNumber,r.crCnt,count(s.node_id)AS secCnt,round(1.0*r.crCnt/count(s.node_id),2)AS density FROM ranked_releases r JOIN rel_BELONGS_TO_SPEC bs ON bs.dst_id=r.rk_id JOIN Section s ON s.node_id=bs.src_id WHERE r.rank=1 GROUP BY r.node_id,r.specNumber,r.crCnt)SELECT specNumber,crCnt,secCnt,density FROM density_rows ORDER BY density DESC"""
 complete=[dict(zip(['specNumber','crCnt','secCnt','density'],r))for r in new.execute(sql)];selected=complete[:5];assert len(complete)==14 and len(selected)==5
 assert selected[-1]['density']>complete[5]['density'],'Need allowable-cutoff-tie handling, never an invented tiebreaker.'
 save('actual_new_full_SQL_density_reference.json',{'status':'SQL_ONLY_REFERENCE_NATIVE_PENDING','columns':['specNumber','crCnt','secCnt','density'],'SQL_full_pool':sql,'SQL_selected':sql+' LIMIT 5','complete_pool_rows':complete,'selected_records':selected,'strict_fifth_sixth_gap':True,'reference_query':definition['original_query'],'reference_query_sha256':definition['original_query_sha256'],'rounding_native_equivalence_pending':True,'API_calls':0,'native_calls':0})
 with(HERE/'requested_records.jsonl').open('x')as f:
  for r in selected:f.write(canon(r)+'\n')
 (HERE/'reference_query.cypher').write_bytes(definition['original_query'].encode())
 save('actual_materialization_manifest.json',{'status':'PASS_ISOLATED_WHOLE_BASE_PLUS_FINITE_SOURCE_DEPENDENCY_FACTS','base_SQL':pin(BASE_SQL),'base_TTL':pin(BASE_TTL),'source_SQL':pin(target_sql),'source_TTL':pin(target_ttl),'source_packet_manifest':pin(N/'manifest.json'),'definition':pin(N/'prospective_finite_dependency_source_variant_definition.json'),'primary_review':pin(N/'primary_exact_seven_unit_finite_dependency_source_policy_review.json'),'secondary_review':pin(args.secondary_review),'new_Section_nodes':nodes,'new_edges':edges,'whole_nodes':156296,'whole_edges':939168,'old_tables':79,'full_fact_proof':pin(HERE/'actual_all79_tables_and_full_graph_fact_equivalence.json'),'SQL_reference':pin(HERE/'actual_new_full_SQL_density_reference.json'),'requested_records':pin(HERE/'requested_records.jsonl'),'API_calls':0,'native_calls':0,'expert_validation_n':0,'original560_increment':0,'full_source_reconstruction_claim':False})
 assert sha(BASE_SQL)==SQL_SHA and sha(BASE_TTL)==TTL_SHA
 print(json.dumps({'status':'PASS','manifest':pin(HERE/'actual_materialization_manifest.json')}))
if __name__=='__main__':main()
