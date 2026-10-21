"""Read-only source-role and retained-text recovery audit; not native or gold generation."""
import sys
if sys.flags.optimize:
    raise SystemExit('Assertions must remain enabled')
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import sqlite3
import zipfile
import xml.etree.ElementTree as ET

resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
ap=argparse.ArgumentParser()
ap.add_argument('--repo',type=Path,required=True)
ap.add_argument('--cqs',type=Path,required=True)
ap.add_argument('--out',type=Path,required=True)
args=ap.parse_args(); R,C,D=args.repo.resolve(),args.cqs.resolve(),args.out.resolve()
D.mkdir(parents=True,exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest()
def pin(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024**2),b''): h.update(b)
    return {'path':str(p),'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def save(n,x):
    p=D/n;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');return pin(p)
qid='RAN1_P2_CQ5-8'; W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'; M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
plain=lambda el:''.join(t.text or ''for t in el.iter(W+'t'))
literal=lambda el:''.join(t.text or ''for t in el.iter()if t.tag in(W+'t',M+'t'))
norm=lambda s:re.sub(r'\W+','',s).casefold()
positive=lambda s:'BWP'in s and 'switch'in s
base=C/'original_core_repair'
line=next(l for l in (base/'provenance/original_benchmark.jsonl').read_bytes().splitlines()if json.loads(l)['id']==qid)
q=json.loads(line)
assert sha(q['question_en'].encode())=='fa90e3fc9bf9d6207a5ce712c8fa94f386ac17828b61dadb5dae6be458146bb1'
assert sha(q['cypher'].encode())=='01da1619fc313bbacde6657e9c9ea2189f1c6aa3622ceadcc48ac3745b3d0c0c'
assert pin(base/'criteria.json')['sha256']=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
save('original_question_and_query.json',{'id':qid,'question_en':q['question_en'],'question_sha256':sha(q['question_en'].encode()),'original_query':q['cypher'],'query_sha256':sha(q['cypher'].encode()),'original_row_sha256':sha(line),'criteria':pin(base/'criteria.json'),'original_ordering':'meetingNumberInt DESC only; no secondary tie is introduced','legacy_gold_used_for_choice':False,'nonblind_original_row_read':True})

# The rule uses retained string syntax only, with no topic, ID, or answer whitelist.
tdoc=re.compile(r'^R1-\d{7}\t')
agreed=re.compile(r'^\(Rel-\d+,.*\bCR\d+.*\) is agreed\.$')
cue=re.compile(r'(?i)(?:final\s+CRs?\s+in|comeback\s+for\s+final\s+CR)')
def own_text(s):
    ls=s.splitlines();stop=len(ls)
    for i,t in enumerate(ls):
        if tdoc.match(t):
            attached=i+1<len(ls)and bool(agreed.match(ls[i+1].strip()))and any(cue.search(p)for p in ls[:i])
            if not attached:stop=i;break
    return '\n'.join(ls[:stop]),stop

# These ranges are direct source-boundary observations, not query ID exclusions.
# They permit a falsifiable independent comparison of the generic retained-text rule.
own_ends={
 'AGR-123-8.8-001':1310,'AGR-123-8.8-003':1343,'AGR-123-9.2-015':1607,
 'AGR-122b-UNKNOWN-020':594,'AGR-122b-8.8-003':1538,
 'AGR-122b-10.2.2-001':2298,'AGR-122b-10.2.2-002':2306,'AGR-122b-10.2.2-007':2335,
 'AGR-121-7-005':497,'AGR-121-7-021':736,'AGR-121-7-022':753,
 'AGR-121-7-029':855,'AGR-121-9.14-003':5005,
 'AGR-120-7-005':506,'AGR-120b-5-001':216,
 'AGR-119-7-003':446,'AGR-119-7-004':483,'AGR-119-8.1-019':847,
}
raw=C/'original_core_source_RAN1_common3176/raw_extraction'
manifest=json.loads((raw/'manifest.json').read_text())
with gzip.open(raw/'identity_and_source_geometry.jsonl.gz','rt')as f: geometry=[json.loads(l)for l in f]
assert len(geometry)==3176
sources={};frontier=[];heading_extra=[];panels=[]
for spec in manifest['source_documents']:
    archive=R/spec['original_archive']['path'];assert pin(archive)['sha256']==spec['original_archive']['sha256']
    with zipfile.ZipFile(archive)as z:
        zi=z.getinfo(spec['original_archive']['member']);doc=z.read(zi)
    assert sha(doc)==spec['original_DOCX_sha256']
    with zipfile.ZipFile(io.BytesIO(doc))as z:xb,sb=z.read('word/document.xml'),z.read('word/styles.xml')
    assert sha(xb)==spec['document_XML_sha256']and sha(sb)==spec['styles_XML_sha256']
    meet=spec['meeting']; body=list(ET.fromstring(xb).find(W+'body'))
    gs=[g for g in geometry if g['meeting']==meet]
    known_heads={g['source_record_raw_body_child_range'][0]for g in gs}
    positive_g=[]
    for g in gs:
        lo,hi=g['source_record_raw_body_child_range'];s='\n'.join(literal(e)for e in body[lo:hi]);p=positive(s)
        frontier.append({'resolutionId':g['resolutionId'],'meeting':meet,'meetingNumberInt':g['meetingNumberInt'],'range':[lo,hi],'broad_literal_sha256':sha(s.encode()),'broad_keyword_positive':p})
        if p and g['meetingNumberInt']>=119:
            positive_g.append(g);assert g['resolutionId']in own_ends
            end=own_ends[g['resolutionId']];assert lo<end<=hi
            own='\n'.join(literal(e)for e in body[lo:end])
            blocks=[{'raw_body_child0':i,'kind':body[i].tag.rsplit('}',1)[-1],'plain_text':plain(body[i]),'literal_text':literal(body[i]),'XML':ET.tostring(body[i],encoding='unicode')}for i in range(lo,min(hi,end+2))]
            panels.append({'resolutionId':g['resolutionId'],'meeting':meet,'meetingNumberInt':g['meetingNumberInt'],'broad_range':[lo,hi],'direct_own_range':[lo,end],'own_positive':positive(own),'blocks':blocks,'OMML_count':sum(len(list(e.iter(M+'oMath')))for e in body[lo:end]),'source_boundary_scope':'Direct own heading, adopted TP and explicitly attached final-CR paragraphs. Subsequent independent contribution catalog and next agenda heading are not owned.'})
    # Extra literal markers are retained as an upper-bound challenge, not admitted Agreements.
    if gs[0]['meetingNumberInt']>=119:
        markers=[]
        for i,e in enumerate(body):
            for j,p in enumerate([e]if e.tag==W+'p'else e.iter(W+'p')):
                if re.match(r'^Agreement\b',plain(p).strip(),re.I):markers.append((i,j,plain(p)))
        for i,j,t in markers:
            hi=next((k for k,_,_ in markers if k>i),len(body))
            s='\n'.join(literal(e)for e in body[i:hi])
            if i not in known_heads and positive(s):heading_extra.append({'meeting':meet,'range':[i,hi],'paragraph_within_child0':j,'heading':t,'body_literal':s})
    sources[meet]={'archive':pin(archive),'member':zi.filename,'CRC32':f'{zi.CRC:08x}','DOCX_sha256':sha(doc),'document_XML_sha256':sha(xb),'styles_XML_sha256':sha(sb),'retained_geometry_n':len(gs),'original_broad_keyword_positive_n':len(positive_g)}
save('all3176_original_source_broad_frontier.json',frontier)
save('all_broad_positive_source_panels_through_cutoff119.json',panels)
save('extra_literal_Agreement_heading_positive_challenge.json',heading_extra)
assert len(panels)==18

db=R/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/relational/RAN1.sqlite';dbpin=pin(db)
assert dbpin['sha256']=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
c=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row;c.execute('PRAGMA query_only=ON')
sql="SELECT a.*,m.meetingNumber,m.meetingNumberInt FROM Agreement a JOIN edge e ON e.src_id=a.node_id AND e.rel_type='MADE_AT' JOIN Meeting m ON m.node_id=e.dst_id WHERE instr(a.content,'BWP')>0 AND instr(a.content,'switch')>0 ORDER BY m.meetingNumberInt DESC"
rows=[dict(x)for x in c.execute(sql)];assert len(rows)==170
recovered=[]
for a in rows:
    s,stop=own_text(a['content'])
    if positive(s):recovered.append({**a,'own_content':s,'first_foreign_line0':stop})
assert len(recovered)==160
selected=recovered[:10];assert selected[-1]['meetingNumberInt']==119
assert len([a for a in recovered if a['meetingNumberInt']>=119])==10
source_ids={p['resolutionId']for p in panels if p['own_positive']}
assert {a['resolutionId']for a in selected}==source_ids
checks=[]
for p in panels:
    a=dict(c.execute('SELECT * FROM Agreement WHERE resolutionId=?',(p['resolutionId'],)).fetchone())
    retained,stop=own_text(a['content']); retained_own_positive=positive(retained)
    if a['content']and positive(a['content']):assert retained_own_positive==p['own_positive']
    # Body w:t, including strike/deleted text, is compared as a recorded literal.
    # OMML and clean normative adoption are deliberately NOT certified by this test.
    missing=[]
    for b in p['blocks']:
        if b['raw_body_child0']>=p['direct_own_range'][1]:continue
        t=re.sub(r'^Agreement\s*:?\s*','',b['plain_text'],count=1)
        if norm(t)and norm(t)not in norm(a['content']or''):missing.append({'raw_body_child0':b['raw_body_child0'],'text':t})
    checks.append({'resolutionId':p['resolutionId'],'source_own_positive':p['own_positive'],'frozen_original_positive':positive(a['content']or''),'generic_recovered_positive':retained_own_positive,'first_foreign_line0':stop,'source_plain_blocks_absent_from_frozen':missing,'source_OMML_count':p['OMML_count'],'contentWithEquations_null':a['contentWithEquations']is None,'note_null':a['note']is None})
c.close();assert pin(db)==dbpin
save('original170_and_generic_recovered160_frozen_rows.json',{'SQL':sql,'original_rows':rows,'recovered_rows':recovered,'selected10':selected,'no_new_order_tiebreaker':True,'no_ID_or_topic_exclusion_in_recovery_rule':True})
save('source_own_and_frozen_plain_retention_checks.json',checks)
receipt={'status':'BOUNDED_RETAINED_TEXT_QUERY_REPAIR_PROPOSAL_NOT_ADMITTED','id':qid,'utc':datetime.now(timezone.utc).isoformat(),'sources':sources,'source_geometry':pin(raw/'identity_and_source_geometry.jsonl.gz'),'source_frontier':pin(D/'all3176_original_source_broad_frontier.json'),'source_panels':pin(D/'all_broad_positive_source_panels_through_cutoff119.json'),'extra_literal_heading_positive_challenge':pin(D/'extra_literal_Agreement_heading_positive_challenge.json'),'extra_unbound_positive_n':len(heading_extra),'frozen':dbpin,'original170_recovered160':pin(D/'original170_and_generic_recovered160_frozen_rows.json'),'source_checks':pin(D/'source_own_and_frozen_plain_retention_checks.json'),'selected10_ids':[a['resolutionId']for a in selected],'boundary':{'strictly_above119':9,'at119_positive_n':1,'selected_at119':1,'no_secondary_tie_added':True},'recorded_plain_fidelity_issues':[x for x in checks if x['source_own_positive']and x['source_plain_blocks_absent_from_frozen']],'remaining_gate':'Original seven-unit semantic judgment must resolve whether source-authorized recorded-plain fallback suffices; no clean normative TP/equation-completeness claim. Exact Cypher native and portable gates not executed. Extra heading candidates, if any, require direct own-boundary adjudication.','API_calls':0,'native_calls':0,'DB_mutations':0,'public_mutations':0,'new_admissions':0,'expert_validation_n':0,'nonblind_AI':True}
save('receipt.json',receipt)
print(json.dumps({'status':receipt['status'],'original_n':len(rows),'recovered_n':len(recovered),'selected10':receipt['selected10_ids'],'source_own_positive_n':len(source_ids),'extra_heading_positive_n':len(heading_extra),'recorded_plain_fidelity_issue_ids':[x['resolutionId']for x in receipt['recorded_plain_fidelity_issues']]},ensure_ascii=False))
