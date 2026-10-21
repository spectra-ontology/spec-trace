"""Prospective BWP original-role query repair and read-only SQL reference.

Retained text, not supplied source panels, defines the executable recovery.
No source-derived IDs, features, meetings or answer texts are hardcoded into
the query. Source panels are used only to test its selected answer population.
The output is a candidate, not a native/independent-review/admission result.
"""
import sys
if sys.flags.optimize:
    raise SystemExit('Run without optimization')
import hashlib
import json
from pathlib import Path
import re
import resource
import os
import sqlite3

resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
L=Path(__file__).absolute().parent
R=next(p for p in L.parents if (p/'CLAUDE.md').is_file())
D=L/'recorded_CR_recovery_v4'
D.mkdir(exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest()
def pin(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1024**2),b''):h.update(b)
    return {'path':str(p),'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def save(n,x):
    p=D/n;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');return pin(p)
def jsonl(n,rows):
    p=D/n;p.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n'for x in rows));return pin(p)
j=lambda s:json.dumps(s,ensure_ascii=False)
# Formal syntax shared by retained report fields; no BWP-specific boundary rule.
tdoc=r'R1-[0-9]{7}\t.*'
agreed=r'\(Rel-[0-9]+,.*\bCR[0-9]+.*\) is agreed\.'
cue=r'(?i).*(?:final\s+CRs?\s+in|comeback\s+for\s+final\s+CR).*'
def boundary(lines):
    return ('[i IN range(0,size('+lines+')-1) WHERE '+lines+'[i] =~ '+j(tdoc)+
      ' AND NOT CASE WHEN i+1<size('+lines+') THEN trim('+lines+'[i+1]) =~ '+j(agreed)+
      ' AND any(previous IN '+lines+'[..i] WHERE previous =~ '+j(cue)+') ELSE false END]')
def join(lines,stop):
    return 'coalesce(reduce(s=null,line IN '+lines+'[..coalesce(head('+stop+'),size('+lines+'))] | CASE WHEN s IS NULL THEN line ELSE s+"\\n"+line END),"")'
q=(
 'MATCH (a:Agreement)-[r:MADE_AT]->(m:Meeting)\n'
 "WHERE a.content CONTAINS 'BWP' AND a.content CONTAINS 'switch'\n"
 'WITH a,r,m,split(a.content,"\\n") AS filterLines,split(coalesce(a.contentWithEquations,a.content),"\\n") AS bodyLines\n'
 'WITH a,r,m,filterLines,bodyLines,'+boundary('filterLines')+' AS filterStops,'+boundary('bodyLines')+' AS bodyStops\n'
 'WITH a,r,m,'+join('filterLines','filterStops')+' AS ownFilter,'+join('bodyLines','bodyStops')+' AS ownBody\n'
 "WHERE ownFilter CONTAINS 'BWP' AND ownFilter CONTAINS 'switch'\n"
 'WITH a,r,m,ownFilter,ownBody ORDER BY m.meetingNumberInt DESC LIMIT 10\n'
 'OPTIONAL MATCH (c:CR)\n'
 'WHERE c.summaryOfChange IS NOT NULL AND c.summaryOfChange<>""\n'
 ' AND c.reasonForChange CONTAINS (m.meetingNumber+" agreed on a text proposal")\n'
 ' AND any(fragment IN split(ownFilter,"[")[1..] WHERE fragment CONTAINS "]" AND c.title CONTAINS ("["+trim(head(split(fragment,"]")))+"]"))\n'
 'WITH a,r,m,ownBody,c ORDER BY c.tdocNumber ASC\n'
 'WITH a,r,m,ownBody,collect(CASE WHEN c IS NULL THEN null ELSE "Recorded associated CR "+c.tdocNumber+" summary: "+c.summaryOfChange END) AS summaries\n'
 'RETURN m.meetingNumber,a.resolutionId,ownBody+CASE WHEN a.note IS NULL OR a.note="" THEN "" ELSE "\\n"+a.note END+reduce(s="",summary IN summaries | s+"\\n"+summary) AS content\n'
 'ORDER BY m.meetingNumberInt DESC'
)
meta=json.loads((L/'actual_source_frozen_recovery_v1/original_question_and_query.json').read_text())
definition={'id':meta['id'],'question_en':meta['question_en'],'original_query':meta['original_query'],
 'reference_query':q,'required_fields':[{'name':'content','type':'string','nullable':False,'source_column_or_expression':'content'}],
 'collection':{'kind':'multiset'},'cardinality_policy':{'mode':'exact','value':10},
 'repair_class':'query_and_scorer','original_question_preserved':True}
assert len(definition)==9
repair_sha=sha(json.dumps(definition,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
definition_pin=save('definition.json',definition)
db=R/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/relational/RAN1.sqlite'
dbpin=pin(db);assert dbpin['sha256']=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
c=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row;c.execute('PRAGMA query_only=ON')
def own_text(v):
    lines=v.split('\n')
    for i,t in enumerate(lines):
        if re.fullmatch(tdoc,t) and not(i+1<len(lines)and re.fullmatch(agreed,lines[i+1].strip())and any(re.fullmatch(cue,p)for p in lines[:i])):
            return '\n'.join(lines[:i])
    return v
def own_sql(v):return None if v is None else own_text(v)
c.create_function('own_recorded_text',1,own_sql,deterministic=True)
sql=('SELECT e.edge_id,a.node_id,m.meetingNumber,m.meetingNumberInt,a.resolutionId,'
     'own_recorded_text(a.content) AS own_filter,own_recorded_text(coalesce(a.contentWithEquations,a.content)) AS own_body,a.note '
     "FROM Agreement a JOIN edge e ON e.src_id=a.node_id AND e.rel_type='MADE_AT' JOIN Meeting m ON m.node_id=e.dst_id "
     "WHERE instr(a.content,'BWP')>0 AND instr(a.content,'switch')>0 "
     "AND instr(own_recorded_text(a.content),'BWP')>0 AND instr(own_recorded_text(a.content),'switch')>0 ORDER BY m.meetingNumberInt DESC")
pool=[dict(x)for x in c.execute(sql)]
assert len(pool)==160
crs=[dict(x)for x in c.execute('SELECT node_id,tdocNumber,title,reasonForChange,summaryOfChange FROM CR WHERE summaryOfChange IS NOT NULL AND summaryOfChange<>\'\'')]
frontier=json.loads((L/'actual_source_frozen_recovery_v1/all3176_original_source_broad_frontier.json').read_text())
mapping=json.loads((L/'full10_substantive_mapping_v2/actual_full10_minimum_substantive_mapping.json').read_text())
assert {x['resolutionId']for x in pool[:10]}=={x['resolutionId']for x in mapping['cases']}
assert sum(x['meetingNumberInt']>119 for x in pool)==9
assert sum(x['meetingNumberInt']==119 for x in pool)==1
full_rows=[];associations=[]
for a in pool:
    tokens={s.split(']',1)[0].strip() for s in a['own_filter'].split('[')[1:] if ']'in s}
    prefix=a['meetingNumber']+' agreed on a text proposal'
    matches=sorted([x for x in crs if prefix in (x['reasonForChange']or'') and any('['+token+']'in(x['title']or'')for token in tokens)],key=lambda x:x['tdocNumber'])
    value=a['own_body']+(''if a['note']is None or a['note']==''else'\n'+a['note'])
    for cr in matches:value+='\nRecorded associated CR '+cr['tdocNumber']+' summary: '+cr['summaryOfChange']
    full_rows.append({'m.meetingNumber':a['meetingNumber'],'a.resolutionId':a['resolutionId'],'content':value})
    if matches:associations.append({'resolutionId':a['resolutionId'],'meeting':a['meetingNumber'],'tokens':sorted(tokens),'matched_CR':matches,'edge_id':a['edge_id']})
selected=full_rows[:10]
selected_associations=[x for x in associations if x['resolutionId']in{a['a.resolutionId']for a in selected}]
assert len(selected_associations)==1
assert selected_associations[0]['resolutionId']=='AGR-121-9.14-003'
assert [x['node_id']for x in selected_associations[0]['matched_CR']]==[155012]
assert all(type(v)is str for row in selected for v in row.values())
c.close();assert pin(db)==dbpin
jsonl('expected_native_selected10_all3columns.jsonl',selected)
jsonl('independent_SQL_all160_full3columns.jsonl',full_rows)
jsonl('requested_content_records.jsonl',[{'content':x['content']}for x in selected])
save('retained_generic_association_evidence.json',{'selected_associations':selected_associations,'whole160_associations':associations,'positive_selected_n':len(selected_associations),
 'association_meaning':'Retained CR explicitly states same-meeting agreed-on TP and contains exact shared bracketed feature in its title. It corroborates the selected Agreement, not a new Agreement row, TSG approval, a new mathematical interpretation or complete normative clause.',
 'absence_policy':'No same-meeting/feature CR means append nothing; no unbound guess, feature/CR ID whitelist or outside source is supplied to the query.'})
inp={'id':meta['id'],'wg':'RAN1','status':'development_probe','candidate_query':q}
jsonl('native_input_development_probe.jsonl',[inp])
save('reference_preparation_receipt.json',{'status':'CANDIDATE_SQL_REFERENCE_PASS_NATIVE_AND_INDEPENDENT_SEMANTIC_REVIEW_PENDING',
 'id':meta['id'],'definition':definition_pin,'repair_sha256':repair_sha,'canonical9_key_count':9,
 'candidate_query_sha256':sha(q.encode()),'original_query_sha256':meta['query_sha256'],
 'DB_before_after':dbpin,'SQL':sql,'full_pool_n':160,'selected_n':10,'strictly_above_cutoff119':9,'at_cutoff119':1,'new_secondary_tie':False,
 'selected_ids':[x['a.resolutionId']for x in selected],
 'generic_CR_matches_in_selected':selected_associations,'source_substantive_mapping':pin(L/'full10_substantive_mapping_v2/actual_full10_minimum_substantive_mapping.json'),
 'source_authority':'Original content/equation-aware answer interface, substantive Agreement role and exact original10 selection; linked retained CR summary is explicitly marked additional description of the same agreed TP. New independent seven-unit judgment is required for this actual repair.',
 'not_a_native_or_model_result':True,'old_pending_review_not_reused_as_pass':True,'API_calls':0,'native_calls':0,'DB_mutations':0,'public_mutations':0,'new_admissions':0,
 'files':[pin(D/n)for n in ['expected_native_selected10_all3columns.jsonl','independent_SQL_all160_full3columns.jsonl','requested_content_records.jsonl','retained_generic_association_evidence.json','native_input_development_probe.jsonl']]})
print(json.dumps({'status':'SQL_REFERENCE_PREPARED','definition':definition_pin,'repair_sha256':repair_sha,'selected_n':10,'association_n':len(selected_associations),'native_input':pin(D/'native_input_development_probe.jsonl')},ensure_ascii=False))
