import hashlib,json,re,sqlite3,sys,zipfile
from pathlib import Path
from datetime import datetime,timezone
import xml.etree.ElementTree as ET
if sys.flags.optimize:raise SystemExit('Assertions required')
R=Path('/home/sihyeon/workspace/spectra');D=Path(__file__).resolve().parent
P=Path('/home/sihyeon/workspace/spectra-public/spec-trace')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def save(n,x):(D/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
proofpath=D/'actual_adoption_and_amendment_v2/actual_adoption_and_amendment_association.json';proof=json.loads(proofpath.read_text())
source=R/proof['source']['path'];assert sha(source)==proof['source']['sha256']
with zipfile.ZipFile(source)as z:xb=z.read('word/document.xml')
assert hashlib.sha256(xb).hexdigest()==proof['source_XML']['sha256']
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}';body=list(ET.fromstring(xb).find(W+'body'));txt=lambda e:''.join(t.text or ''for t in e.iter(W+'t'))
assert txt(body[419]).strip()=='Clarify the following agreements with changes in red'
assert txt(body[420]).strip()=='Agreements:'and any(e.get(W+'val')=='green'for e in body[420].iter(W+'highlight'))
runs=[e for e in body[423].iter(W+'r')if txt(e)=='scheduled'];assert len(runs)==1
assert runs[0].find(W+'rPr/'+W+'strike')is not None and runs[0].find(W+'rPr/'+W+'color').get(W+'val')=='FF0000'
assert txt(body[421]).startswith('For standalone SUL')
assert 'Case 11T+1T'in txt(body[444])and 'Case 20T+2T'in txt(body[444])
assert txt(body[446]).strip()=='Agreements:'and 'Case 11 Tx on carrier 1 and 1 Tx on carrier 2'in txt(body[447])
c=sqlite3.connect((R/proof['database']['path']).as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row;c.execute('PRAGMA query_only=ON')
nodes=[dict(x)for x in c.execute('SELECT * FROM _node_record WHERE node_id IN(249,251,484,20741,24008) ORDER BY node_id')]
assert nodes==proof['affected_and_historical_nodes'];props={x['node_id']:json.loads(x['properties_json'])for x in nodes}
assert props[249]['content']==props[20741]['content']and 'the scheduled UL transmissions'in props[249]['content']
assert props[484]['resolutionId']=='AGR-100b-5.1-007'and 'For option 1'in props[484]['content']
assert '| Case 1 | 1T+1T |'in props[24008]['content']and '| Case 2 | 0T+2T |'in props[24008]['content']
allprops=[dict(x)for x in c.execute('SELECT * FROM node_property WHERE node_id IN(249,251,484,20741,24008) ORDER BY node_id,key')];assert allprops==proof['affected_and_historical_all_properties']
rows=[dict(x)for x in c.execute(proof['all_switching_properties_SQL'])];assert len(rows)==3140
norm=lambda s:re.sub('[^a-z0-9]','',s.lower())
condition='The switching period is only applicable when the UL transmissions are switched between 1Tx carrier 1 and 2Tx carrier 2'
needles={'unqualified_condition':condition,'scheduled_condition':condition.replace('the UL','the scheduled UL'),'amendment_instruction_without_run_format':txt(body[419]).strip()};matches=[]
for x in rows:
 value=json.loads(x['value_json'])
 if isinstance(value,str):
  hits=[k for k,n in needles.items()if norm(n)in norm(value)]
  if hits:matches.append(dict(x,hits=hits))
assert matches==proof['actual_condition_and_amendment_matches']
edges=[dict(x)for x in c.execute('SELECT * FROM edge WHERE src_id IN(249,251,484,20741,24008) OR dst_id IN(249,251,484,20741,24008) ORDER BY edge_id')];assert edges==proof['affected_and_historical_all_incident_edges']
c.close()
actual={'status':'PASS_ROOT_INDEPENDENT_RAW_AMENDMENT_AND_FROZEN_REOPEN','observed_utc':datetime.now(timezone.utc).isoformat(),'original_DOCX':pin(source),'original_XML_sha256':hashlib.sha256(xb).hexdigest(),'raw_instruction':txt(body[419]),'raw_qualification':txt(body[423]),'struck_word':'scheduled','direct_strike_color':'FF0000','necessary_affected_node':249,'all_affected_properties':allprops,'same_event_WA_numeric_counterevidence':props[24008],'all_switching_property_values_actually_rechecked_n':len(rows),'exact_matches_to_saved_proof':True,'actual_condition_matches':matches,'all_incident_edges':edges,'no_new_native_or_model_calls':True,'source_fidelity_only_not_ontology_superiority':True}
save('ROOT_actual_independent_amendment_and_frozen_reopen.json',actual)
criteria=P/'release_package/cqs/original_core_repair/criteria.json';primary=D/'local_substantive_disposition_review_v3.json';units=json.loads(criteria.read_text())['semantic_units']
reasons=[
 'The original what-was-agreed question requests substantive UL-switching conditions. Under the explicit local amendment instruction, scheduled is struck. Unmarked assertion fails both an active rendering and a faithful marked transcript; requiring this particular condition status does not require all Word formatting.',
 'Named event #100 agenda5.1 has six retained Agreement groups within LIMIT10. Authentic #100-e own instructions419 and Agreement420 precede qualifier423. I reopened source DOCX and frozen nodes independently; no later meeting or universal normative interpretation is substituted.',
 'Retained WA24008 really contains Case1/2 values. This defeats a global numeric-absence argument. Its conditional option2-3 role and shared meeting/agenda do not license promotion to Agreement. Table-cell exclusion is real counterauthority and table absence alone is insufficient.',
 'Keep six Agreement groups and original own content/note roles. WA context is not a seventh Agreement; joining meeting aliases would duplicate facts. The concrete failing qualifier belongs to existing Agreement249 and no extra counting or requirement is introduced.',
 'I rechecked every retained property of249/251/WA and historical99/100b plus all3140 switching-containing property candidates. The only unqualified condition hit is different-event100b inter-band option1. The current249 has unmarked scheduled and identical content to99. The instruction survives under248 but cannot identify which word was deleted.',
 'Original sequence and LIMIT10 select all6, so ordering/tie ambiguities do not drive this disposition. No new ranking rule or source-based answer substitution is admitted.',
 'Restoring the qualifier deletion requires authentic source information absent from checked frozen inputs. An answer-specific replacement or later-event splice is not an existing-frozen repair. I accept only bounded source-explicit amendment-status loss; no general redline policy, exact parser-cause proof, ontology advantage, model-performance claim or permanent unanswerability follows.'
]
review={'id':'RAN1_P2_CQ1-2','reviewer_kind':'ROOT secondary; distinct nonblind AI from main_C','recommendation':'unsupported_frozen_data','subtype':'source_explicit_agreement_amendment_status_unretained','criteria':pin(criteria),'original_question_sha256':'c457946bfcbc8319fc66dace3d37dee26c4920dcd64405e4cb4de439aa8d9817','original_query_sha256':'cb94b26a209ef26d275d5093f911a1ac6c85c356136e37da534da876c263ddc8','semantic_units':[{'semantic_unit':u,'assessment':'BOUNDED_NECESSARY_SOURCE_STATUS_FAILURE','reason':r}for u,r in zip(units,reasons)],'primary':pin(primary),'actual_ROOT_reopen':pin(D/'ROOT_actual_independent_amendment_and_frozen_reopen.json'),'pinned_primary_proof':pin(proofpath),'decisive_fact':'Source explicitly clarifies following agreements with changes in red; scheduled is directly red and struck, but frozen named-event condition asserts it unmarked with no revised/status equivalent in examined inputs.','counterauthority':'Table cells are intentionally outside GraphDB; numeric case values do survive WA. The failure classification rests on the explicit local substantive qualifier amendment, not on demanding all table content or active-only transcription. Note is retained and is not a loss claim.','paper_alignment':'A source-fidelity limitation of the pinned representation. This is neither evidence for SPECTRA ontology effectiveness nor a scored new model comparison. It can support transparent benchmark scope and future source restoration only.','expert_validation_n':0,'nonblind_AI':True,'API_calls':0,'new_native_calls':0,'public_mutations':0,'new_gold':False}
save('ROOT_secondary_exact_seven_unit_review.json',review)
print(json.dumps({'status':'SECONDARY_COMPLETE','review':pin(D/'ROOT_secondary_exact_seven_unit_review.json'),'actual':pin(D/'ROOT_actual_independent_amendment_and_frozen_reopen.json')}))
