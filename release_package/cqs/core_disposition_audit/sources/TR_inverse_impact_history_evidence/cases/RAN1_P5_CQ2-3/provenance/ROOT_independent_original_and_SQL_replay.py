"""ROOT actual frozen SQL/source replay and distinct seven-unit bounded classification."""
import csv,datetime,gzip,hashlib,io,json,sqlite3,zipfile
from pathlib import Path
import xml.etree.ElementTree as E
assert __debug__
A=Path(__file__).resolve().parent;F=A/'actual_source_and_frozen'
R=next(p for p in A.parents if (p/'CLAUDE.md').is_file())
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
N={'w':W[1:-1]}
def h(b):return hashlib.sha256(b).hexdigest()
def pin(p):
 b=p.read_bytes();return dict(path=str(p.relative_to(R)),bytes=len(b),sha256=h(b))
def load(p):return json.loads(p.read_bytes())
def text(e):
 if e.tag in (W+'del',W+'moveFrom'):return ''
 if e.tag==W+'t':return e.text or ''
 return ''.join(text(x)for x in e)
def checkpara(p,ps):
 e=ps[p['index']];sty=e.find('w:pPr/w:pStyle',N)
 assert text(e)==p['text'] and (sty.get(W+'val')if sty is not None else None)==p['style']
 assert len(list(e.iter(W+'ins')))==p['insertions'] and len(list(e.iter(W+'del')))==p['deletions']
 assert len(list(e.iter(W+'moveFrom')))==p['moves_from']
sources=load(F/'direct_original_source_and_format.json')
sources.append(load(F/'actual_source_CR2504980_and_named_role_receipt.json'))
assert len(sources)==29 and len({s['key']for s in sources})==29
bodies={};paras={};witnesses=0
for s in sources:
 raw=Path(s['archive']['path']).read_bytes();assert h(raw)==s['archive']['sha256'] and len(raw)==s['archive']['bytes']
 with zipfile.ZipFile(io.BytesIO(raw))as z:xml=z.read('word/document.xml');styles=z.read('word/styles.xml')
 for name,b in [('document_xml',xml),('styles_xml',styles)]:
  assert h(b)==s[name]['sha256'] and len(b)==s[name]['bytes']
  assert gzip.decompress((F/'source'/s['key']/(name.replace('_','.')+'.gz')).read_bytes())==b
 body=E.fromstring(xml).find(W+'body');bodies[s['key']]=body;ps=body.findall(W+'p');paras[s['key']]=ps
 if 'body_children'in s:assert len(body)==s['body_children'] and len(ps)==s['direct_body_paragraphs']
 for p in s.get('all_heading1_paragraphs',[]):checkpara(p,ps)
 for section in s.get('scope_conclusions_and_summary_sections',[]):
  for p in section['direct_body_paragraphs']:checkpara(p,ps)
 for p in s.get('all_target_TS_or_avoid_channel_reference_blocks',[]):
  i=p['body_child'];assert text(body[i])==p['text']
  assert (text(body[i-1])if i else '')==p['preceding_text'] and (text(body[i+1])if i+1<len(body)else '')==p['following_text']
  witnesses+=1
for s in load(F/'actual_original_style_and_scope_role_reopen.json'):
 for p in s['resolved_outline0_headings']:checkpara(p,paras[s['key']])
 for block in s['numeric_scope_and_conclusion_blocks']:
  for p in block['direct_body_paragraphs']:checkpara(p,paras[s['key']])
assert 'avoid any changes to physical layer channels and signals' in text(bodies['TR38742'][186])
assert 'TS 38.211' in text(bodies['TR38742'][437])
assert 'Conclusions' in text(paras['TR38742'][630])
db=R/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/authorized_incremental48_OpenRouter_release/evaluation/runtime/relational/RAN1.sqlite'
before=pin(db);assert before['sha256']=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
c=sqlite3.connect(db.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row
role_results=[]
diagnostics=[load(F/'actual_immutable_SQL_diagnostics.json'),load(F/'actual_named_workitem_recovery_SQL.json')]
for group in diagnostics:
 for name,x in group.items():
  assert h(x['sql'].encode())==x['sql_sha256']
  actual=[dict(x)for x in c.execute(x['sql'])]
  assert actual==x['rows'] and len(actual)==x['row_count'],name
  role_results.append(dict(role=name,rows=len(actual),all_columns_all_rows_equal=True))
c.close();assert pin(db)==before and len(role_results)==11
orig=diagnostics[0]['original_projection']['rows']
assert orig==diagnostics[0]['inverse_alias_projection']['rows'] and len(orig)==11
mapping=list(csv.DictReader(io.StringIO((F/'original_tr_impact_mapping.csv').read_text())))
mapped=sorted([x for x in mapping if x['impactsSpec']=='38.211'],key=lambda x:x['trNumber'])
assert [(x['tr.trNumber'],x['ti.impactType'],x['ti.affectedSection'],x['ti.impactDescription'])for x in orig]==[(x['trNumber'],x['impactType'],x['impactsSection'],x['impactDescription'])for x in mapped]
primary=load(A/'primary_exact_seven_unit_source_role_review.json')
contract=load(A/'bounded_source_role_contract.json')
assert contract['question_sha256']==primary['question_sha256']=='637c5d0d507b546f584420bfa8a5ee864c401b121c78497bbfad16d9be6936ce'
units=[
("requested answer roles and fields","Preserve every TR identity and each actual impact type requested by the original TS38.211 revision-history question. Title, section and description remain supporting projections; their correctness is not introduced as a new mandatory natural-language output field."),
("population and source context","Keep all26 retained TRs and original target38.211; neither the manual11 rows nor current Rel19 chapters define a new population restriction. Twenty-nine actual source ZIP/XML/style pairs and all original role queries were independently reopened."),
("filters and relationship meaning","The original author defines NewSection as an added existing-TS section and ExtendSection as extension. Original planned ISAC addition and current study scope do not alone establish actual incorporation. The741/742 discussion does not certify a historical no-change finding. Positive original NR-U and SBFD implementation CRs are preserved as implementation evidence. Distinguish input assertions, study recommendations, candidate naming correspondences and attributed actual changes without converting one role into another."),
("counting unit and join multiplicity","Requested facts are TR/type pairs, allowing each independently supported type. Eleven original records,8402 physical study LEFT rows,28 naming-WI candidates and595 CR/section rows have separate units. ROOT independently reproduced each diagnostic with all columns and all rows."),
("cardinality and completeness","Every requires a complete source-attributed set. The manual11-row inverse view is faithfully executable but does not establish the requested full history. Complete direct study-WI and reproducible normative naming alternatives were checked. No replacement answer cardinality or zero-effect count is fabricated."),
("ordering and ties when requested","No ranking or cutoff appears in the original EN/KR. Original trNumber ascending is deterministic presentation, not an added membership or temporal gate."),
("unverified additional inputs or external interpretation","The bounded disposition concerns this frozen input and original relationship meaning. It does not classify the natural question as permanently impossible. A complete source-enriched TR/implementation/type oracle would be new reviewed input. No model run, expert endorsement or final causal attribution was invented.")
]
assert [u[0]for u in units]==[x['semantic_unit']for x in primary['semantic_units']]
# Correct the isolated typographic reference without changing a substantive predicate.
units=[(k,v.replace('741/742','TR38.742'))for k,v in units]
out=A/'ROOT_independent_exact_seven_source_role_review_v2.json';assert not out.exists()
receipt=dict(id='RAN1_P5_CQ2-3',status='ROOT_SECONDARY_BOUNDED_CLASSIFICATION_CONFIRMED',reviewer='/root distinct nonblind AI',human_expert_validation_n=0,reviewed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),question_sha256=primary['question_sha256'],criteria=primary['criteria'],original_question_en=primary['original_question_en'],classification='unsupported_frozen_data',subtype='study_to_actual_spec_impact_attribution_not_retained',bounded_to_original_frozen_input=True,original_source_XML_style_pairs=29,actual_original_target_witnesses_reopened=witnesses,actual_immutable_SQL_roles=role_results,immutable_database=before,original_manual_mapping_equal=True,units=[dict(semantic_unit=k,decision='classification_confirmed',reason=v)for k,v in units],primary=pin(A/'primary_exact_seven_unit_source_role_review.json'),contract=pin(A/'bounded_source_role_contract.json'),counterauthority=pin(A/'counterauthority_and_alternate_recovery_decisions.json'),source=pin(F/'direct_original_source_and_format.json'),style_roles=pin(F/'actual_original_style_and_scope_role_reopen.json'),model_API_calls=0,native_calls=0,public_mutations=0,new_benchmark_admissions=0)
out.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(status=receipt['status'],receipt=pin(out),source_XML_pairs=29,SQL_roles=11)))

