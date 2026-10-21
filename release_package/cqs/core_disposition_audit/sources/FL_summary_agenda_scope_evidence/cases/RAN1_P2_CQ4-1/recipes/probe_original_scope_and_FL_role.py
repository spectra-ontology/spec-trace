"""Immutable original-scope sensitivity, not a repaired question or gold."""
import argparse,datetime,hashlib,io,json,re,sqlite3,subprocess,zipfile
from pathlib import Path
import xml.etree.ElementTree as E
import sys
if sys.flags.optimize:
    raise RuntimeError('Optimization is unsupported')
R=Path(__file__).resolve()
while not (R/'AGENTS.md').is_file():R=R.parent
C=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
D=a.output.absolute();D.mkdir(exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest()
def pin(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024**2),b''):h.update(b)
    return {'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def save(n,d):
    q=D/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');return pin(q)
qid='RAN1_P2_CQ4-1'
bp=R.parent/'spectra-public/spec-trace/release_package/cqs/original_core_repair/provenance/original_benchmark.jsonl'
original=next(json.loads(x) for x in bp.read_text().splitlines() if json.loads(x)['id']==qid)
assert sha(original['question_en'].encode())=='471a52294d3de115ff2f1cc2921ad407f6834c3c5cd80ae2e9e84a9554850375'
oq={k:original[k] for k in ['id','wg','phase','question_en','cypher']}
oq.update(question_sha256=sha(oq['question_en'].encode()),query_sha256=sha(oq['cypher'].encode()),legacy_gold_exposure=True,legacy_gold_used_to_choose_scope=False)
save('original_question_and_query.json',oq)
cp=R/'logs/pending-tasks/spectracq-core-contract-2026-10-13/original_repair/criteria.json'
assert sha(cp.read_bytes())=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
(D/'criteria.json').write_bytes(cp.read_bytes())
authorities=[]
for label,path in [
 ('phase1','docs/RAN/formal/RAN1/phase-1/design-spec/tdoc_ontology_specs(Tdoc_list).md'),
 ('phase2','docs/RAN/formal/RAN1/phase-2/design-spec/tdoc_ontology_specs(Final_report).md'),
 ('validation','docs/RAN/formal/RAN1/phase-2/step3_validation.md')]:
    raw=subprocess.check_output(['git','show','HEAD:'+path],cwd=R)
    dest=D/(label+'_HEAD.md');dest.write_bytes(raw)
    authorities.append({'git_path':path,'git_blob_oid':subprocess.check_output(['git','rev-parse','HEAD:'+path],cwd=R,text=True).strip(),'snapshot':pin(dest)})
db=R/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/relational/RAN1.sqlite'
before=pin(db);assert before['sha256']=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
con=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True);con.row_factory=sqlite3.Row;con.execute('pragma query_only=on')
rows=lambda q:[dict(v) for v in con.execute(q)]
base='''from Tdoc t join rel_BELONGS_TO b on b.src_id=t.node_id join AgendaItem ai on ai.node_id=b.dst_id
join rel_MODERATED_BY mo on mo.src_id=t.node_id join Company c on c.node_id=mo.dst_id
where t.summaryType='FL' and {predicate}'''
parent=lambda term:"exists(select 1 from AgendaItem p where p.meetingNumber=ai.meetingNumber and lower(p.agendaDescription) like '%"+term+"%' and (ai.agendaNumber=p.agendaNumber or ai.agendaNumber like p.agendaNumber||'.%'))"
component="(ai.agendaNumber='7.1' or ai.agendaNumber like '7.1.%')"
policies={
 'authored_numeric_startswith_7_1':"ai.agendaNumber like '7.1%'",
 'numeric_component_7_1':component,
 'numeric_component_7_1_AND_MIMO_parent':component+' and '+parent('mimo'),
 'MIMO_parent_any_numeric_agenda':parent('mimo'),
 'explicit_NR_MIMO_parent_any_numeric_agenda':parent('nr mimo'),
}
ranks={};paths={}
for name,predicate in policies.items():
    # Group by company node matches the original Cypher grouping expression.
    qr='select c.node_id,c.companyName,count(t.node_id) flCount,count(distinct t.node_id) distinctTdocDiagnostic '+base.format(predicate=predicate)+' group by c.node_id order by flCount desc,c.companyName'
    rr=rows(qr)
    qp='select t.node_id,t.tdocNumber,t.title,t.summaryType,ai.node_id agenda_node_id,ai.meetingNumber,ai.agendaNumber,ai.agendaDescription,c.node_id company_node_id,c.companyName '+base.format(predicate=predicate)+' order by ai.meetingNumber,ai.agendaNumber,t.tdocNumber,c.companyName'
    pp=rows(qp)
    ranks[name]={'predicate':predicate,'query':qr,'whole':rr,'top5':rr[:5],'count_unit':'original count(t), each original matched path; distinct is a separate diagnostic'}
    paths[name]=pp
all_agendas=rows("select * from AgendaItem where agendaNumber like '7.1%' or lower(agendaDescription) like '%mimo%' order by meetingNumber,agendaNumber")
save('actual_frozen_scope_rank_sensitivities.json',{'id':qid,'policies':ranks,'paths':paths,'agenda_scope_rows':all_agendas,'limits':['Parent-description literal MIMO contrasts are diagnostic predicates, not an expert-certified complete NR MIMO topic classifier.','No scope policy is selected as gold.','A missing graph path does not establish source-world absence.','Counts are graph paths using the original query, not a causal leadership metric.']})
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
text=lambda e:''.join(x.text or '' for x in e.iter(W+'t'))
scope_sources=[]
for meeting,indices in [('84',[458,1116]),('115',[612,1643,5465])]:
    loader=R/f'ontology/input/tsg/RAN/formal/meetings/RAN1/Final_Report/Final_Report_RAN1-{meeting}.docx'
    raw=loader.read_bytes();matches=[]
    for ap in sorted((R/f'data/corpus/tsg/RAN/formal/meetings/RAN1/source/TSGR1_{meeting}/Report').glob('Final*.zip')):
        with zipfile.ZipFile(ap) as z:
            for zi in z.infolist():
                if zi.filename.lower().endswith('.docx') and sha(z.read(zi))==sha(raw):matches.append({'archive':pin(ap),'member':zi.filename,'CRC32':zi.CRC,'bytes':zi.file_size})
    assert matches
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        xml=z.read('word/document.xml');styles=z.read('word/styles.xml')
    body=list(E.fromstring(xml).find(W+'body'))
    snippets=[{'raw_body_child0':i,'text':text(body[i]),'pStyle':[v.get(W+'val') for v in body[i].iter(W+'pStyle')],'XML':E.tostring(body[i],encoding='unicode')} for i in indices]
    toc=[]
    for i,e in enumerate(body):
        if e.tag==W+'p':
            t=text(e)
            if re.match(r'^(7\.1|8\.1)(?:\D|$)',t) and ('Maintenance' in t or 'MIMO' in t):toc.append({'raw_body_child0':i,'text':t,'XML':E.tostring(e,encoding='unicode')})
    assert snippets and toc
    (D/f'source_{meeting}.docx').write_bytes(raw)
    scope_sources.append({'meeting':meeting,'loader':pin(loader),'original_archive_exact_matches':matches,'document_XML_sha256':sha(xml),'styles_XML_sha256':sha(styles),'own_heading_snippets':snippets,'TOC_number_title_snippets':toc,'coordinate':'unfiltered raw w:body child ordinal0'})
save('actual_two_original_report_scope_reopen.json',{'sources':scope_sources,'limits':['Two original exact archives and selected original Heading/TOC witnesses. This is not a full source attribution or topic classifier.']})
# Reopen the two numbered7.1 FL own headers in115, so this question has actual role evidence rather than borrowing a contribution verdict.
raw=(D/'source_115.docx').read_bytes()
with zipfile.ZipFile(io.BytesIO(raw)) as z:body=list(E.fromstring(z.read('word/document.xml')).find(W+'body'))
own=[]
for row in paths['authored_numeric_startswith_7_1']:
    if row['meetingNumber']!='115':continue
    tid=row['tdocNumber'];hits=[]
    pat=re.compile(r'(?<![A-Za-z0-9])'+re.escape(tid)+r'(?![0-9])')
    for i,e in enumerate(body):
        if pat.search(text(e)):
            hits.append({'raw_body_child0':i,'text':text(e),'XML':E.tostring(e,encoding='unicode'),'next_two_blocks':[{'raw_body_child0':j,'text':text(body[j])} for j in range(i+1,min(len(body),i+3))]})
    assert hits
    own.append({'frozen_path':row,'actual_id_occurrences':hits})
save('actual_two_115_FL_header_occurrences.json',{'observations':own,'limits':['Every exact ID occurrence is retained, including citations if present. Own role needs header-column reading, not any-cell filename attribution.','No full18-header source census or missing-entrant closure claimed.']})
con.close();after=pin(db);assert before==after
receipt={'id':qid,'status':'ACTUAL_IMMUTABLE_SCOPE_AND_TWO_SOURCE_REOPEN_COMPLETE','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'question_sha256':oq['question_sha256'],'original_query_sha256':oq['query_sha256'],'criteria':pin(cp),'authorities':authorities,'DB_before':before,'DB_after':after,'DB_read_only':True,'rank_policy_diagnostics':len(policies),'original_numeric_matching_paths':len(paths['authored_numeric_startswith_7_1']),'source_reports_reopened':['84','115'],'original_numeric_115_FL_headers_reopened':len(own),'new_model_calls':0,'native_calls':0,'public_queue_central_changes':0,'gold_selected':False,'human_expert_n':0}
print(json.dumps({'receipt':save('receipt.json',receipt),'top5_diagnostics':{k:v['top5'] for k,v in ranks.items()}},ensure_ascii=False))
