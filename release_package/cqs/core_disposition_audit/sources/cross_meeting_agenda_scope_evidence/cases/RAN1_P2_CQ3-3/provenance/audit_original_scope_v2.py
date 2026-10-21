"""Read-only scope/relationship audit; diagnostic predicates are not a new gold."""
import sys
if sys.flags.optimize:
    raise SystemExit('Assertions must remain enabled')
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import sqlite3
import subprocess
import zipfile
import xml.etree.ElementTree as ET

resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
ap = argparse.ArgumentParser()
ap.add_argument('--repo', type=Path, required=True)
ap.add_argument('--cqs', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True)
args = ap.parse_args()
R, C, D = args.repo.resolve(), args.cqs.resolve(), args.out.resolve()
D.mkdir(parents=True, exist_ok=False)
sha = lambda b: hashlib.sha256(b).hexdigest()
def pin(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024**2), b''):
            h.update(b)
    return {'path': str(p), 'bytes': p.stat().st_size, 'sha256': h.hexdigest()}
def save(n, x):
    p = D / n
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2) + '\n')
    return pin(p)

qid = 'RAN1_P2_CQ3-3'
original = next(json.loads(l) for l in (C / 'original_core_repair/provenance/original_benchmark.jsonl').read_text().splitlines() if json.loads(l)['id'] == qid)
assert sha(original['question_en'].encode()) == '1558bcdf6940b5e99049245452034297541ad8e4afdeca6a2ff022f91ea41886'
assert sha(original['cypher'].encode()) == '5722fc5de43df1afb077b3cffd4e193a4ed9dfb15f5acbfe2e725929879ec2b7'
save('original_question_and_query.json', {'id': qid, 'wg': original['wg'], 'phase': original['phase'], 'question_en': original['question_en'], 'question_sha256': sha(original['question_en'].encode()), 'original_cypher': original['cypher'], 'query_sha256': sha(original['cypher'].encode()), 'legacy_gold_read_during_prior_context': True, 'this_audit_uses_gold_to_choose_scope': False})
criteria = pin(C / 'original_core_repair/criteria.json')
assert criteria['sha256'] == 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
authority = []
for label, path in [('phase1', 'docs/RAN/formal/RAN1/phase-1/design-spec/tdoc_ontology_specs(Tdoc_list).md'), ('phase2', 'docs/RAN/formal/RAN1/phase-2/design-spec/tdoc_ontology_specs(Final_report).md'), ('phase2_validation', 'docs/RAN/formal/RAN1/phase-2/step3_validation.md')]:
    b = subprocess.check_output(['git', 'show', 'HEAD:' + path], cwd=R)
    (D / (label + '_original_HEAD.md')).write_bytes(b)
    authority.append({'historical_path': path, 'snapshot': pin(D / (label + '_original_HEAD.md'))})

db = R / 'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/relational/RAN1.sqlite'
db_before = pin(db)
assert db_before['sha256'] == 'aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
conn = sqlite3.connect(db.as_uri() + '?mode=ro&immutable=1', uri=True)
conn.row_factory = sqlite3.Row
conn.execute('pragma query_only=on')
rows = lambda q: [dict(x) for x in conn.execute(q)]
base = '''select c.node_id,c.companyName,count(distinct a.node_id) contributionCount,count(*) path_count_diagnostic
from Agreement a join rel_REFERENCES rf on rf.src_id=a.node_id join Tdoc t on t.node_id=rf.dst_id
join rel_SUBMITTED_BY sb on sb.src_id=t.node_id join Company c on c.node_id=sb.dst_id
join rel_RESOLUTION_BELONGS_TO rb on rb.src_id=a.node_id join AgendaItem ai on ai.node_id=rb.dst_id
where {predicate} group by c.node_id order by contributionCount desc'''
component = "(ai.agendaNumber='7.1' or ai.agendaNumber like '7.1.%')"
parent = lambda term: "exists(select 1 from AgendaItem p where p.meetingNumber=ai.meetingNumber and lower(p.agendaDescription) like '%"+term+"%' and (p.agendaNumber=ai.agendaNumber or ai.agendaNumber like p.agendaNumber||'.%'))"
policies = {
    'authored_literal_prefix': "ai.agendaNumber like '7.1%'",
    'component_7_1': component,
    'numeric_component_AND_lexical_MIMO_parent': component + ' and ' + parent('mimo'),
    'lexical_MIMO_parent_without_numeric_limit': parent('mimo'),
    'explicit_NR_MIMO_parent_without_numeric_limit': parent('nr mimo'),
}
ranks = {}
for label, pred in policies.items():
    rr = rows(base.format(predicate=pred))
    cut = rr[9]['contributionCount'] if len(rr) >= 10 else None
    ranks[label] = {'predicate': pred, 'whole': rr, 'top10': rr[:10], 'boundary_count': cut, 'at_boundary': [x for x in rr if x['contributionCount']==cut]}
agenda = rows("select ai.*,(select count(*) from rel_RESOLUTION_BELONGS_TO r join Agreement a on a.node_id=r.src_id where r.dst_id=ai.node_id) agreement_count from AgendaItem ai where ai.agendaNumber like '7.1%' order by ai.meetingNumber,ai.agendaNumber")
memberships = rows("""select a.node_id,a.resolutionId,ai.meetingNumber,ai.agendaNumber,ai.agendaDescription,count(distinct c.node_id) company_n
from Agreement a join rel_RESOLUTION_BELONGS_TO rb on rb.src_id=a.node_id join AgendaItem ai on ai.node_id=rb.dst_id
join rel_REFERENCES rf on rf.src_id=a.node_id join Tdoc t on t.node_id=rf.dst_id
join rel_SUBMITTED_BY sb on sb.src_id=t.node_id join Company c on c.node_id=sb.dst_id
where ai.agendaNumber like '7.1%' group by a.node_id,ai.node_id order by ai.meetingNumber,ai.agendaNumber,a.resolutionId""")
save('actual_fresh_SQL_scope_ranks_and_membership.json', {'query_template': base, 'ranks': ranks, 'literal_prefix_agendas': agenda, 'literal_prefix_contributing_agreements': memberships,
    'diagnostic_limits': ['Lexical MIMO and explicit NR MIMO predicates are source-grounded contrast tests, not certified complete NR MIMO topic classifiers.', 'No diagnostic is selected as gold here.', 'Top10 serialization shown uses SQLite stable execution output only; no unrequested secondary sort was added.']})

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
text = lambda el: ''.join(x.text or '' for x in el.iter(W + 't'))
source_witnesses = []
for meeting in ['84','115']:
    loader = R / ('ontology/input/tsg/RAN/formal/meetings/RAN1/Final_Report/Final_Report_RAN1-' + meeting + '.docx')
    doc = loader.read_bytes()
    archive_dir = R / ('data/corpus/tsg/RAN/formal/meetings/RAN1/source/TSGR1_' + meeting + '/Report')
    archive_matches=[]
    for archive in sorted(archive_dir.glob('Final*.zip')):
        with zipfile.ZipFile(archive) as z:
            for zi in z.infolist():
                if zi.filename.lower().endswith('.docx'):
                    member = z.read(zi)
                    if sha(member)==sha(doc):
                        archive_matches.append({'archive':pin(archive),'member':zi.filename,'member_CRC32':f'{zi.CRC:08x}','member_size':zi.file_size})
    assert archive_matches, 'No exact original ZIP matches loader DOCX'
    with zipfile.ZipFile(io.BytesIO(doc)) as z:
        xb,sb = z.read('word/document.xml'), z.read('word/styles.xml')
    body=list(ET.fromstring(xb).find(W+'body'))
    candidates=[]
    for i,e in enumerate(body):
        if e.tag != W+'p': continue
        tt=text(e)
        if ((re.match(r'^7\.1(?:\D|$)',tt) and ('Maintenance' in tt or 'MIMO' in tt)) or ('NR MIMO' in tt and len(tt)<180) or (meeting=='84' and 'full-dimension MIMO for LTE' in tt and len(tt)<200)):
            candidates.append({'raw_body_child0':i,'text':tt,'pStyle':[x.get(W+'val') for x in e.iter(W+'pStyle')],'XML':ET.tostring(e,encoding='unicode')})
    with gzip.open(D / ('original_' + meeting + '_document.xml.gz'), 'wb') as f: f.write(xb)
    with gzip.open(D / ('original_' + meeting + '_styles.xml.gz'), 'wb') as f: f.write(sb)
    assert candidates
    source_witnesses.append({'meeting':meeting,'loader_DOCX':pin(loader),'original_docx_sha256':sha(doc),'archive_matches':archive_matches,'document_XML_sha256':sha(xb),'styles_XML_sha256':sha(sb),'headings':candidates})
save('actual_original_two_report_scope_headings.json', {'source_witnesses':source_witnesses,'scope':'Two exact original archive-matching reports, headings only; not source-completeness of all company contributions.'})
conn.close()
db_after=pin(db)
assert db_before==db_after
save('receipt.json', {'status':'PASS','id':qid,'criteria':criteria,'original_authority':authority,'frozen_SQL_before':db_before,'frozen_SQL_after':db_after,'read_only_immutable':True,'source_reports_reopened':['84','115'],'new_admissions':0,'native_executions':0,'API_calls':0,'scope':'Actual bounded scope diagnostic, no semantic scope selection or answer admission','scientific_claims_not_made':['All NR MIMO source population is classified','All company attributions are source-certified','Historical gold is a scope authority']})
print(json.dumps({'status':'PASS','output':str(D),'rank_policies':len(ranks),'source_reports':2,'new_admissions':0}))
