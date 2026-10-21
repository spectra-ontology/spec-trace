#!/usr/bin/env python3
"""Replay complete-tie source fidelity, retaining the clean-ten counterexample."""
import argparse,copy,hashlib,io,json,os,re,stat,sys,xml.etree.ElementTree as E,zipfile
from pathlib import Path
sys.dont_write_bytecode=True
INVENTORY_SHA256='9c2923673fdcccac79857998aa7e6aa4f2c67b99e21d4ec7905046663b48cd40'
DECLARATIONS={'id': 'RAN1_P2_CQ5-4', 'artifact_type': 'bounded_frozen_complete_tie_reference_source_diagnostic', 'original560_pass_increment': 0, 'human_expert_n': 0, 'nonblind_AI': True, 'independent_semantic_reviews': 2, 'actual_archived_native_rows': 10, 'full_latest_tie_candidates': 31, 'clean_literal_counterwitness_n': 14, 'actual_native_contains_LPWUS_pair': False, 'all_legal_ten_fail_claimed': False, 'new_model_calls': 0, 'new_native_calls': 0, 'ROOT_seal_included': False, 'recommended_disposition': 'unsupported_frozen_data', 'diagnostic_subtype': 'source_explicit_agreement_amendment_status_unretained'}
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
ID='RAN1_P2_CQ5-4'
def need(ok,msg):
 if not ok: raise ValueError(msg)
def safe(p):
 p=Path(os.path.abspath(p))
 for q in [p,*p.parents]: need(not q.is_symlink(),'symlink forbidden: '+str(q))
 return p
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
def text(el):return ''.join(v.text or '' for v in el.iter() if v.tag in {W+'t',M+'t'})
def struck(el):
 out=[]
 for r in el.iter(W+'r'):
  rp=r.find(W+'rPr')
  if rp is not None and any(v.tag in {W+'strike',W+'dstrike'} and v.get(W+'val','true') not in {'0','false','off'} for v in rp):out.append(''.join(t.text or '' for t in r.iter(W+'t')))
 return out
def verify(frozen_sql=None):
 need(sys.flags.optimize==0,'optimization unsupported')
 entry=safe(__file__);root=entry.parent
 mp,ip=safe(root/'manifest.json'),safe(root/'immutable_inventory.json')
 invraw=ip.read_bytes();need(sha(invraw)==INVENTORY_SHA256,'immutable inventory mismatch')
 inv=json.loads(invraw);m=load(mp)
 need(set(m)=={'declarations','inventory_sha256','verifier_sha256'},'exact manifest keys')
 need(json.dumps(m['declarations'],sort_keys=True)==json.dumps(DECLARATIONS,sort_keys=True),'strict scientific declarations')
 need(m['inventory_sha256']==INVENTORY_SHA256 and m['verifier_sha256']==sha(entry.read_bytes()),'manifest and verifier pins')
 actual=set()
 for p in root.rglob('*'):
  safe(p);mode=p.lstat().st_mode;need(stat.S_ISREG(mode) or stat.S_ISDIR(mode),'nonregular file')
  if stat.S_ISREG(mode):actual.add(p.relative_to(root).as_posix())
 need(actual==set(inv)|{'manifest.json','immutable_inventory.json',entry.name},'closed inventory')
 for rel,pin in inv.items():
  need(not Path(rel).is_absolute() and '..' not in Path(rel).parts and Path(rel).as_posix()==rel,'inventory path')
  need(set(pin)=={'bytes','sha256'} and type(pin['bytes']) is int and type(pin['sha256']) is str,'inventory pin types')
  b=safe(root/rel).read_bytes();need(len(b)==pin['bytes'] and sha(b)==pin['sha256'],'payload changed: '+rel)
 q=load(root/'contract/original_question.json')
 need(q['id']==ID and sha(q['question_en'].encode())=='ed8d176731df8121965dd70174728f1a2c5c647f96c0b1462489b10a079bb45c','original question')
 need(sha(q['cypher'].encode())=='84330a55da07466ebee7188296ddba0c45234feebf0503570d67418aff7a2a34','original query')
 need(sha((root/'contract/criteria.json').read_bytes())=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4','criteria')
 source=(root/'source/Final_Report_RAN1-123.docx').read_bytes()
 need(sha(source)=='0fc4f4da372d682fef7585d8f72d2e5ebac3f46e41f8205658e8742b48e11b71','actual source DOCX')
 with zipfile.ZipFile(io.BytesIO(source)) as z:
  need(z.testzip() is None,'source CRC');raw=z.read('word/document.xml');sty=z.read('word/styles.xml')
  need(z.getinfo('word/document.xml').CRC==3601561713,'source XML CRC')
 need(sha(raw)=='361ad487a69a1980d91690d792ccaeaa819063572be9d58cafc94fd005bc3ed2','original XML')
 need(sha(sty)=='9d607daff9d87d6392163e27ddfdc8f6a9449e9098813533bf999afeb9f78121','original styles')
 style=E.fromstring(sty);need(not list(style.iter(W+'strike')) and not list(style.iter(W+'dstrike')),'bounded style strike observation')
 body=list(E.fromstring(raw).find(W+'body'))
 matrix=load(root/'evidence/all31_frozen_and_source.json');need(len(matrix)==31,'latest tied population')
 ix={v['resolutionId']:v for v in matrix};need(len(ix)==31,'unique latest IDs')
 reopened=0
 for row in matrix:
  need(row['frozen_row']['meetingNumber']=='RAN1#123','latest meeting identity')
  for b in row['actual_original_source_blocks']:
   el=body[b['raw_body_child0']]
   need(text(el)==b['literal_w_and_m_t'],'actual raw child literal')
   need(struck(el)==[v['text'] for v in b['direct_struck_runs']],'actual direct-strike source')
   need(len(list(el.iter(M+'oMath')))==len(b['OMML']),'bounded OMML count')
   reopened+=1
 need(struck(body[1147])==['msg4-NumberofRepetitions '],'actual selected old-name deletion')
 need(len(struck(body[1151]))==13 and 'pdsch-AggregationFactor-r19' in text(body[1151]),'actual second old-name deletions')
 need(text(body[1145]).strip()=='Agreement' and text(body[1149]).strip()=='Agreement','own Agreement markers')
 need('Adopt the following TP' in text(body[1146]) and 'Adopt the following TP' in text(body[1150]),'own explicit adoption')
 for n in [1147,1151]:
  changed=copy.deepcopy(body[n])
  for rp in changed.iter(W+'rPr'):
   for ch in list(rp):
    if ch.tag in {W+'strike',W+'dstrike'}:rp.remove(ch)
  need(text(changed)==text(body[n]) and not struck(changed),'finite plain-text status loss control')
 nr=load(root/'native/receipt.json');rows=[json.loads(line) for line in (root/'native/rows.jsonl').read_text().splitlines()]
 need(nr['reference_query_utf8_sha256']==sha(q['cypher'].encode()),'archived actual query identity')
 ex=nr['execution']
 need(ex['status']=='OK' and ex['truncated'] is False and ex['full_json_rows_available'] is True and ex['rollback_completed'] is True and ex['query_modified'] is False,'actual complete read-only capture')
 need(ex['rows_file_sha256']==sha((root/'native/rows.jsonl').read_bytes()),'actual receipt full rows pin')
 proof=load(root/'evidence/actual_native_reopen_and_SQL_match.json')
 need(sha((root/'native/receipt.json').read_bytes())==proof['actual_native_receipt']['sha256'],'actual receipt provenance')
 need(sha((root/'native/rows.jsonl').read_bytes())==proof['actual_native_positional_rows']['sha256'],'actual rows provenance')
 need(len(rows)==10 and all(type(v) is list and len(v)==3 and all(type(a) is str for a in v) for v in rows),'full native10 three typed columns')
 need(len({v[1] for v in rows})==10,'unique native IDs')
 need({'AGR-123-8.7.1-001','AGR-123-8.7.1-002'} <= {v[1] for v in rows},'decisive witnesses actually selected')
 for mnum,rid,content in rows:
  r=ix[rid];f=r['frozen_row'];need([f['meetingNumber'],rid,f['content']]==[mnum,rid,content],'native full row equals bounded frozen witness')
  need(f['contentWithEquations'] is None,'actual selected alternate property observation')
 counter=load(root/'evidence/all31_tie_counterwitness.json')
 clean=[]
 for row in matrix:
  lo,hi=row['geometry']['source_record_raw_body_child_range'];elements=body[lo:hi]
  own=''.join(text(e) for e in elements[1:]);norm=lambda s:re.sub(r'[\s|]+','',s)
  same=norm(own)==norm(row['frozen_row']['content'])
  direct=any(struck(e) for e in elements)
  pstrike=any(e.tag in {W+'strike',W+'dstrike'} and e.get(W+'val','true') not in {'0','false','off'} for block in elements for p in block.iter(W+'pPr') for e in p.iter())
  state=any(e.tag in {W+n for n in ['del','moveFrom','ins','moveTo','delText','fldSimple','instrText']} for block in elements for e in block.iter())
  objects=any(e.tag in {M+'oMath','{urn:schemas-microsoft-com:office:office}OLEObject',W+'drawing',W+'pict'} for block in elements for e in block.iter())
  if same and not direct and not pstrike and not state and not objects:clean.append(row['resolutionId'])
 need(clean==counter['clean_literal_counterwitness_ids'] and len(clean)==14,'good14 counterevidence preserved, not gold selection')
 need(counter['selected_or_published_gold'] is False and counter['possible_ten_subsets_of_clean_literal_counterwitnesses']==1001,'not all legal10 fail')
 primary=load(root/'contract/primary_review.json')
 need(primary['id']==ID and primary['criteria_sha256']==sha((root/'contract/criteria.json').read_bytes()),'primary identity')
 need(len(primary['seven_unit_review'])==7 and primary['root_seal_required'] is True,'primary seven units')
 secondary=load(root/'contract/secondary_review.json')
 units=load(root/'contract/criteria.json')['semantic_units']
 for review in [primary,secondary]:
  need(review['id']==ID and review['criteria_sha256']==sha((root/'contract/criteria.json').read_bytes()),'review exact task and criteria')
  need(review['recommended_disposition']=='unsupported_frozen_data' and review['diagnostic_subtype']=='source_explicit_agreement_amendment_status_unretained','bounded recommendation identity')
  need([v['unit'] for v in review['seven_unit_review']]==units,'seven original review units')
  need(all(type(v.get('assessment')) is str and v['assessment'] and type(v.get('judgment')) is str and v['judgment'] for v in review['seven_unit_review']),'actual semantic assessments')
 need(primary['reviewer']!=secondary['reviewer'] and primary!=secondary,'separate AI judgments')
 for rid,rawchild in [('AGR-123-8.6-003',1066),('AGR-123-8.6-004',1073)]:
  f=ix[rid]['all_original_frozen_fields'];props=f['properties']
  need('contentWithEquations' not in props and 'note' not in props,'bounded own alternative fields')
  need(sorted(e['rel_type'] for e in ix[rid]['all_incident_edges_with_neighbor_fields'])==['MADE_AT','RESOLUTION_BELONGS_TO'],'bounded original relations')
  need(struck(body[rawchild]),'actual source applicability deletion')
  need(rid not in {v[1] for v in rows},'LPWUS defect is not in archived native10')
 sys.path.insert(0,str(root/'canonical'))
 import original_scorer
 diagnostic=load(root/'evidence/LPWUS_minimum_roles_and_canonical_diagnostic.json')
 dc=diagnostic['contract_for_diagnostic_only']
 gold=[{'content':v['frozen_row']['content']} for v in matrix]
 order=[{'meetingNumberInt':v['frozen_row']['meetingNumberInt']} for v in matrix]
 groups=original_scorer.make_order_groups(dc,order,gold)
 need(len(groups)==1 and len(groups[0])==31,'full original boundary population')
 for test in diagnostic['actual_unchanged_canonical_scorer_tests']:
  lo,hi=ix[test['resolutionId']]['geometry']['source_record_raw_body_child_range']
  deleted=''.join(t for el in body[lo:hi] for t in struck(el))
  squash=lambda s:re.sub(r'\s+','',s)
  need(squash(test['source_bound_removed_fragment']) in squash(deleted),'diagnostic fragment is actually source-struck in this own record')
  pred=[{'content':ix[rid]['frozen_row']['content']} for rid in test['selected_ids']]
  stale=original_scorer.score(dc,gold,pred,diagnostic=True,order_groups=groups)
  need(stale==test['stale_flattened_candidate'] and stale['exact'] is True,'actual stale-condition diagnostic')
  pattern=r'\s+'.join(re.escape(t) for t in test['source_bound_removed_fragment'].split())
  corrected,n=re.subn(pattern,'',pred[-1]['content']);need(n==1,'source-bound one-fragment correction')
  pred[-1]['content']=corrected
  need(sha(corrected.encode())==test['one_fragment_corrected_content_sha256'],'diagnostic changed value')
  changed=original_scorer.score(dc,gold,pred,diagnostic=True,order_groups=groups)
  need(changed==test['one_fragment_corrected_candidate'] and changed['exact'] is False and changed['matched_records']==9,'unchanged canonical scorer rejects this faithful local condition correction')
 need(diagnostic['pool_evidence']['actual_native_contains_LPWUS_pair'] is False,'do not confuse native10 and eligible31')
 need(diagnostic['original560_pass_increment']==0 and diagnostic['human_expert_n']==0,'not admission or expert validation')
 need(primary['public_change_supported'] is False and primary['classification_only_original_pass_increment']==0,'no automatic admission')
 sqlmatch=False
 if frozen_sql is not None:
  import sqlite3
  p=safe(frozen_sql);need(p.is_file(),'explicit SQL file')
  need(sha(p.read_bytes())=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af','explicit frozen SQL SHA')
  con=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True);con.row_factory=sqlite3.Row;con.execute('PRAGMA query_only=ON')
  for row in matrix:
   dbrow=con.execute('SELECT * FROM Agreement WHERE node_id=?',(row['frozen_row']['node_id'],)).fetchone()
   need(dbrow['content']==row['frozen_row']['content'] and dbrow['contentWithEquations']==row['frozen_row']['contentWithEquations'],'explicit current SQL values')
  con.close();sqlmatch=True
 return {'status':'PASS_BOUNDED_DIAGNOSTIC_REPLAY_NOT_FINAL_CLASSIFICATION','id':ID,'actual_native_rows':10,'native_full_columns':3,'latest_tied_candidates':31,'actual_raw_source_blocks_reopened':reopened,'eligible_LPWUS_status_witnesses':2,'actual_native_contains_LPWUS_pair':False,'canonical_fidelity_diagnostic_pairs':2,'all_legal_ten_fail_claimed':False,'independent_semantic_reviews':2,'ROOT_seal_present':False,'explicit_SQL_replay':sqlmatch,'model_calls':0,'new_native_calls':0,'original560_pass_increment':0,'human_expert_n':0}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--frozen-sql',type=Path);a=p.parse_args();print(json.dumps(verify(a.frozen_sql),sort_keys=True))
