"""Own paragraph-header identity and literal Moderator role, preserving Word tabs."""
from pathlib import Path
import hashlib,io,json,re,sqlite3,zipfile,xml.etree.ElementTree as E
C=Path(__file__).resolve().parent
R=C
while not (R/'AGENTS.md').is_file():R=R.parent
D=C/'actual_original_scope_v1'
data=json.loads((D/'actual_frozen_scope_rank_sensitivities.json').read_bytes())
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
text=lambda e:''.join(x.text or '' for x in e.iter(W+'t'))
def tabtext(e):return ''.join((x.text or '') if x.tag==W+'t' else '\t' for x in e.iter() if x.tag in {W+'t',W+'tab'})
raw=(D/'source_115.docx').read_bytes()
with zipfile.ZipFile(io.BytesIO(raw)) as z:
    assert z.testzip() is None
    xml=z.read('word/document.xml');styles=z.read('word/styles.xml')
body=list(E.fromstring(xml).find(W+'body'))
sources={}
for name in ['authored_numeric_startswith_7_1','explicit_NR_MIMO_parent_any_numeric_agenda']:
    for row in data['paths'][name]:
        if row['meetingNumber']=='115':sources[row['tdocNumber']]=row
assert len(sources)==9
db=R/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/relational/RAN1.sqlite'
dbsha=hashlib.sha256(db.read_bytes()).hexdigest()
assert dbsha=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
con=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True);con.row_factory=sqlite3.Row;con.execute('pragma query_only=on')
company={x['node_id']:dict(x) for x in con.execute('select * from Company')}
con.close()
all_headings=[];stack={};out=[]
for i,block in enumerate(body):
    if block.tag!=W+'p':continue
    sp=block.find(W+'pPr/'+W+'pStyle')
    if sp is not None:
        m=re.fullmatch('Heading([1-9])',sp.get(W+'val',''))
        if m:
            level=int(m[1]);stack={k:v for k,v in stack.items() if k<level}
            stack[level]={'raw_body_child0':i,'level':level,'text':text(block)}
            all_headings.append(stack[level])
    fields=tabtext(block).split('\t')
    tid=fields[0].strip()
    if tid not in sources:continue
    assert len(fields)>=3
    title,role=fields[1],fields[2]
    assert re.search(r'(?:FL\s+summary|Feature\s+lead\s+summary)',title,re.I)
    moderator=re.search(r'(?:Moderator|Feature\s+Lead)\s*\(([^)]+)\)',role,re.I)
    assert moderator
    co=company[sources[tid]['company_node_id']]
    aliases=json.loads(co['aliases']) if co['aliases'] is not None else []
    assert moderator[1].strip() in [co['companyName'],*aliases]
    out.append({'frozen_path':sources[tid],'own_first_tab_field_identity':tid,'raw_body_child0':i,'fields_preserving_Word_tabs':fields,'own_role_company_literal':moderator[1].strip(),'original_frozen_Company':co,'literal_role_in_existing_name_or_aliases':True,'nearest_heading_stack':list(stack.values()),'XML':E.tostring(block,encoding='unicode')})
assert len(out)==9 and len({x['own_first_tab_field_identity'] for x in out})==9
numeric=[x for x in out if x['frozen_path']['agendaNumber']=='7.1']
technology=[x for x in out if x['frozen_path']['agendaNumber']=='8.1' or x['frozen_path']['agendaNumber'].startswith('8.1.')]
assert len(numeric)==2 and len(technology)==7
assert all(any(h['raw_body_child0']==612 for h in x['nearest_heading_stack']) for x in numeric)
assert all(any(h['raw_body_child0']==1643 for h in x['nearest_heading_stack']) for x in technology)
obj={'id':'RAN1_P2_CQ4-1','status':'ACTUAL_NINE_OWN_PARAGRAPH_FL_ROLE_AND_PARENT_SCOPE_REOPEN_PASS','source_DOCX_sha256':hashlib.sha256(raw).hexdigest(),'XML_sha256':hashlib.sha256(xml).hexdigest(),'styles_sha256':hashlib.sha256(styles).hexdigest(),'source_coordinate':'unfiltered raw w:body child ordinal0; native w:tab delimits header fields','own_header_rows':out,'numeric_7_1_own_FL_rows':len(numeric),'actual_NR_MIMO_8_1_own_FL_rows':len(technology),'source_scope_own_headings':[x for x in all_headings if x['raw_body_child0'] in [612,1643]],'DB_sha256':dbsha,'counterevidence':['Numeric7.1 contains CSI-related and SUL-related FL summaries. A maintenance heading does not establish that every document under it is technically unrelated to MIMO.','Seven actually recorded FL summaries appear under the source-authored NR-MIMO8.1 parent; these are excluded by the authored numeric7.1 predicate.','Both groups have own Moderator company roles corroborated here. This is not a whole original FL census.','InterDigital, Inc. is preserved as a literal source role and linked by existing frozen Company aliases, not by inventing a new company merge.'],'auditor_correction':'Initial v1 incorrectly expected w:tbl rows. Actual115 headers are tab-separated Word paragraphs. The v1 assertion failure and script remain preserved; original source bytes and graph facts are unchanged.','new_model_calls':0,'native_calls':0,'public_queue_central_changes':0,'gold_selected':False,'human_expert_n':0}
p=C/'actual_same_report_nine_own_FL_scope_role_counterwitnesses_v2.json'
with p.open('x') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'own_FL_rows':len(out)}))
