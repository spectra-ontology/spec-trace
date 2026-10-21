"""Reproduce the original Rel18 study population and preserved source-role evidence.

Generic queries reconstruct retained diagnostics. Source checks audit the bounded
classification and retain concrete normative recovery as a separate evidence role.
"""
import csv,gzip,hashlib,importlib.util,io,json,re,sys
import xml.etree.ElementTree as E
from pathlib import Path
if sys.flags.optimize:raise SystemExit('Enabled checks required')
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent
INVENTORY_SHA256='808b48a3c9efe52a1c7f3349297cc6e6ec518e620cb904e8b4841687b88cde24'
N={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};W='{'+N['w']+'}'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(name):
 p=D/name;b=p.read_bytes();return json.loads(gzip.decompress(b) if name.endswith('.gz') else b)
def active(x):
 if x.tag in {W+'del',W+'moveFrom'}:return ''
 return ((x.text or '') if x.tag==W+'t' else '')+''.join(active(y) for y in x)
def module(name):
 spec=importlib.util.spec_from_file_location('rel18_'+name,D/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def verify_inventory():
 inv=D/'immutable_inventory.json';assert sha(inv.read_bytes())==INVENTORY_SHA256,'Pinned payload inventory differs'
 rows=json.loads(inv.read_bytes());paths=[]
 for x in rows:
  name=x['path'];p=Path(name);assert not p.is_absolute() and '..' not in p.parts and '\\' not in name
  b=(D/name).read_bytes();assert len(b)==x['bytes'] and sha(b)==x['sha256'],'Inventoried payload differs: '+name;paths.append(name)
 actual=sorted(str(p.relative_to(D)) for p in D.rglob('*') if p.is_file() and p.name not in ['manifest.json','immutable_inventory.json','reproduce.py'])
 assert actual==sorted(paths) and len(paths)==len(set(paths)),'Payload membership differs'
 mf=load('manifest.json');b=(D/'reproduce.py').read_bytes()
 assert mf['inventory']=={'bytes':inv.stat().st_size,'sha256':INVENTORY_SHA256}
 assert mf['reproduce']=={'bytes':len(b),'sha256':sha(b)}
 assert mf['id']=='RAN1_P5_CQ4-1' and mf['classification']=='unsupported_frozen_data' and mf['new_admissions']==0
 return len(paths)

def source_checks():
 metadata=load('source/source_originals_metadata_and_locators.json');parsed={};n=0
 for m in metadata:
  key=m['key'];xml=gzip.decompress((D/m['source_dir']/'document.xml.gz').read_bytes());styles=gzip.decompress((D/m['source_dir']/'styles.xml.gz').read_bytes())
  root=E.fromstring(xml);body=root.find('w:body',N);st=E.fromstring(styles);paras=body.findall('w:p',N);texts=[active(p) for p in paras]
  parsed[key]={'xml':xml,'styles':styles,'body':body,'texts':texts,'cover':[{'body_child':i,'text':active(x)} for i,x in enumerate(body) if i<9]}
  for s in m.get('source_scope_conclusions',[]):
   for r in s['direct_body_paragraphs']:assert texts[r['index']]==r['text'],'Original source paragraph role differs: '+key;n+=1
 # These are source-role invariants, separate from byte inventory checks.
 assert set(parsed)=={'TR38858','TR38859','TR38864','TR38865','TR38867','TR38869','CR2504980'}
 for key,p in parsed.items():
  if key.startswith('TR'):assert any('Release 18' in x['text'] for x in p['cover']),'Study release selector differs: '+key
 assert 'potential impacts' in parsed['TR38858']['texts'][351]
 assert 'potential specification impact' in parsed['TR38858']['texts'][4312]
 assert 'way forward toward normative work' in parsed['TR38859']['texts'][115]
 assert 'recommended for normative work' in parsed['TR38859']['texts'][1621]
 assert 'further identified during the normative phase' in parsed['TR38864']['texts'][760]
 assert 'decided during WI phase' in parsed['TR38865']['texts'][624]
 assert 'recommended to be specified' in parsed['TR38867']['texts'][239]
 assert 'based on the final agreed waveforms' in parsed['TR38869']['texts'][2900]
 cr=parsed['CR2504980'];body=cr['body'];cover=active(body[6])
 assert 'Category:BRelease:Rel-19' in cover,'Positive normative witness release/category role differs'
 assert 'B  (addition of feature)' in cover and 'Specification of muting resources for CLI measurements' in cover
 assert active(body[50])=='6.2.1Muting resource' and body[50].find('w:pPr/w:rPr/w:ins',N) is not None,'Actual inserted heading witness differs'
 assert active(body[9])=='5.3.2OFDM baseband signal generation for PRACH' and body[9].find('w:pPr/w:rPr/w:ins',N) is None,'Existing-heading amendment witness differs'
 assert any('sbfd-RACHSingleConfig' in active(p) for p in list(body)[10:50]),'Current existing-clause SBFD amendment differs'
 for m in metadata:
  for k,raw in [('document_xml',parsed[m['key']]['xml']),('styles_xml',parsed[m['key']]['styles'])]:
   assert {x:m[k][x] for x in ['bytes','sha256']}=={'bytes':len(raw),'sha256':sha(raw)},'Original XML/style pin differs'
 secondary=load('source/secondary_actual_original_cover_scope_conclusion_text_v1.json.gz')
 for s in secondary:
  assert s['cover_current_blocks']==parsed[s['key']]['cover']
  for group in s['scope_conclusion_sections']:
   for row in group['paragraphs']:assert row['text']==parsed[s['key']]['texts'][row['direct_paragraph']]
 rootcover=load('source/actual_ROOT_original_release_covers_and_CR_source_role_v2.json')
 assert rootcover['status']=='PASS_SOURCE_COVERS_PARSED_FROM_ORIGINAL_XML'
 heads=load('source/actual_ROOT_SBFD_source_category_and_heading_roles_v1.json')
 assert heads['status']=='PASS_ORIGINAL_XML_FORMAT_ROLE_DIAGNOSTIC'
 for h in heads['resolved_named_heading_style_rows']:
  p=body[h['body_child']];style=p.find('w:pPr/w:pStyle',N)
  assert active(p)==h['text'] and style.get(W+'val')==h['style'] and (p.find('w:pPr/w:rPr/w:ins',N) is not None)==h['paragraph_mark_inserted']
 return {'source_pairs':len(metadata),'scope_conclusion_paragraphs':n,'all_six_original_release_covers':'Release18','normative_positive_category':'B','normative_positive_effect_release':'Rel-19','inserted_heading':'6.2.1','existing_heading_amendment':'5.3.2'}

def semantic_and_SQL_checks():
 q=load('contract/original_question_and_query.json');original=json.loads((D/'contract/original_benchmark_record.jsonl').read_bytes());crit=load('contract/criteria.json');contract=load('contract/bounded_source_role_contract.json')
 assert q['original_record']==original
 assert sha(original['question_en'].encode())==q['question_sha256']=='9b6364d79aad4a4af0b626e2d43753133030a3d937f6629406354ab96d67b130'
 assert sha(original['cypher'].encode())==q['query_sha256']=='f462c7cb2c2816f59f8b36563b18e52f13dae28490f3cac0079cb41f7dbad433'
 assert sha((D/'contract/criteria.json').read_bytes())=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
 author=load('contract/original_author_CQ_dataset.json');kr=next(x for x in author['questions'] if x['id']=='CQ4-1');assert kr==q['original_Korean_record'] and kr['cypher']==original['cypher']
 assert contract['classification_candidate']=='unsupported_frozen_data' and contract['new_admission'] is False,'Bounded disposition promoted to admission'
 assert contract['requested_roles']==['study identity selected by original TARGET_RELEASE Rel-18','actual type(s) of effect on TS, associated with TS identity where reported'],'Actual impact request replaced by declared label retrieval'
 assert contract['expert_validation_n']==0
 assert contract['scope_conditions']==['Preserve original question bytes and allsix studies','No all-clause, all-history, fresh-event, finalCR or latestTS requirement','No arbitrary approved-only or effectRelease18 gate','No new per-study type whitelist or source labels in runtime selection'],'Original scope conditions changed'
 for name in ['primary_seven_unit_review.json','secondary_seven_unit_review.json']:
  review=load('contract/'+name)
  assert review['id']==original['id'] and review['question_sha256']==q['question_sha256'] and review['original_query_sha256']==q['query_sha256']
  assert [x['semantic_unit'] for x in review['semantic_units']]==crit['semantic_units'],'Exact seven semantic units differ'
  assert review['recommendation']=='unsupported_frozen_data' and review['whole_original_question_verified_pass'] is False and review['complete_answer_oracle_created'] is False and review['expert_validation_n']==0 and review['nonblind_AI'] is True
 secondary=load('contract/secondary_seven_unit_review.json');assert secondary['distinct_from_ROOT_primary'] is True and secondary['human_review_n']==0
 actual=load('provenance/secondary_actual_original_source_and_SQL_review_v1.json')
 assert actual['status']=='PASS_SECONDARY_ACTUAL_SEVEN_RAW_ARCHIVES_NINE_SQL_AND_COMPLETE_INCIDENT_REPLAY'
 assert actual['complete_incident_all_rows_equal'] is True and actual['frozen_database_unchanged'] is True and actual['frozen_before_after']['sha256']=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
 assert [x['row_count'] for x in actual['SQL_roles']]==[26,7,7,2684,5,12,662,1,53],'Independent actual SQL source-role coverage differs'
 b=(D/'provenance/secondary_actual_original_source_and_SQL_review_v1.json').read_bytes()
 assert secondary['actual_independent_source_SQL_receipt']=={'file':'secondary_actual_original_source_and_SQL_review_v1.json','bytes':len(b),'sha256':sha(b)}
 graph=load('frozen/complete_records_and_edges.json.gz');schemas=load('frozen/original_SQL_table_schemas.json');mem=module('memory_graph');c,records=mem.memory_graph(graph,schemas)
 assert (len(graph['complete_incident_core_node_ids']),len(records),len(graph['edges']))==(367,9634,12428)
 assert c.execute('SELECT count(*) FROM WorkItem').fetchone()[0]==423
 diags=load('frozen/original_eight_SQL_roles.json.gz');roles={}
 for name,role in diags.items():
  assert sha(role['sql'].encode())==role['sql_sha256'];rows=[dict(x) for x in c.execute(role['sql'])]
  assert rows==role['rows'] and len(rows)==role['row_count'],'Retained SQLite role differs: '+name
  roles[name]=len(rows)
 direct=load('frozen/all_five_direct_CR_incidence.json.gz');assert sha(direct['sql'].encode())==direct['sql_sha256']
 rows=[dict(x) for x in c.execute(direct['sql'])];assert rows==direct['rows'] and len(rows)==direct['row_count']==53,'Direct study CR role differs';roles['all_five_direct_CR_incidence']=len(rows)
 generic=module('generic_original_path');ast=generic.parse_query(original['cypher']);out=generic.run(ast,graph)
 expected=[{f:r[f.split('.')[1]] for f in ast['projections']} for r in diags['original_projection']['rows']]
 assert out==expected and ast['projections']==original['gold_columns'] and len(out)==7,'Original generic OPTIONAL/DISTINCT projection differs'
 own=load('provenance/actual_ROOT_generic_original_MATCH_OPTIONAL_replay_v1.json');assert own['AST']==ast and own['actual_all_rows']==out
 ids=sorted({r['tr.trNumber'] for r in out});assert ids==['38.858','38.859','38.864','38.865','38.867','38.869']
 no_role=[r['tr.trNumber'] for r in out if r['ti.impactType'] is None and r['sp.specNumber'] is None];assert no_role==['38.858','38.859'],'Absent optional role relabeled as actual NoChange'
 manual=list(csv.DictReader((D/'author_context/original_tr_impact_mapping.csv').read_text().splitlines()))
 assert all(any(r['trNumber']==tr and r['impactType']=='NoChange' for r in manual) for tr in no_role),'Original omitted NoChange assertions differ'
 directcr=diags['complete_six_direct_study_CR']['rows'];crids={r['node_id'] for r in directcr};assert len(crids)==5
 numbers=sorted({json.loads(r['properties_json']).get('specNumber') for r in direct['rows'] if r['rel_type']=='MODIFIES'});assert numbers==['38.858','38.859','38.864'],'Informative study CR object role differs'
 for r in directcr:assert r['node_id'] in records
 cr=diags['SBFD_original_CR_source_witness']['rows'];assert len(cr)==1 and cr[0]['tdocNumber']=='R1-2504980' and cr[0]['crCategory']=='B','CR category replaced by Section-impact type'
 candidates=diags['complete_six_naming_candidates']['rows'];joined=diags['complete_six_naming_CR_spec_section_projection']['rows']
 recovered={r['node_id'] for r in directcr+joined+cr};assert len(candidates)==12 and len(joined)==662 and len(recovered)==294
 core={r[0] for r in c.execute('SELECT node_id FROM TechnicalReport UNION SELECT node_id FROM TRImpact')}|recovered|{r['node_id'] for r in candidates}
 core|={r[0] for r in c.execute("SELECT w.node_id FROM WorkItem w JOIN rel_RELATED_TO_WORK_ITEM k ON k.dst_id=w.node_id JOIN TechnicalReport tr ON tr.node_id=k.src_id JOIN rel_TARGET_RELEASE rr ON rr.src_id=tr.node_id JOIN Release r ON r.node_id=rr.dst_id WHERE r.releaseName='Rel-18'")}
 assert sorted(core)==graph['complete_incident_core_node_ids'] and sorted({r[0] for r in c.execute('SELECT node_id FROM WorkItem')}-core)==graph['identity_only_WorkItems']
 assert all(e['src_id'] in core or e['dst_id'] in core for e in graph['edges'])
 assert all('impactType' not in records[n]['properties'] for n in recovered),'Candidate CR metadata silently assigned study-impact types'
 c.close()
 return {'SQL_roles':roles,'all_rows_and_fields_equal':True,'original_query_AST':ast,'original_query_rows':out,'original_population_studies':len(ids),'original_optional_role_null_studies':no_role,'candidate_CR_union':len(recovered),'complete_core_nodes':len(core),'records':len(records),'edges':len(graph['edges']),'source_labels_or_answer_whitelist_in_query_selection':False}

def main():
 payload_n=verify_inventory();sources=source_checks();proof=semantic_and_SQL_checks()
 out={'status':'PASS','id':'RAN1_P5_CQ4-1','classification':'unsupported_frozen_data','subtype':'Rel18_study_to_actual_TS_impact_type_role_requires_source_attribution','source_role_checks':sources,'retained_replay':proof,'inventoried_payload_files':payload_n,'new_admissions':0,'complete_answer_oracle_created':False,'source_grounded_positive_recovery_preserved':True,'expert_validation_n':0,'human_review_n':0,'model_API_calls':0,'new_native_calls':0,'public_writes':0}
 print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
