"""Export the entire recorded FL-role path dependency, not selected top5 answers."""
import gzip
import hashlib
import json
import sqlite3
from pathlib import Path

C = Path(__file__).resolve().parent
R = C
while not (R / 'AGENTS.md').is_file():
    R = R.parent
DB = R / 'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/relational/RAN1.sqlite'
OUT = C / 'actual_frozen_FL_role_dependency_v1'
OUT.mkdir(exist_ok=False)


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(2**20), b''):
            h.update(b)
    return h.hexdigest()


before = sha(DB)
assert before == 'aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
con = sqlite3.connect(DB.as_uri() + '?mode=ro&immutable=1', uri=True)
con.row_factory = sqlite3.Row
con.execute('PRAGMA query_only=ON')
queries = {
    'FL_Tdocs': "SELECT node_id,tdocNumber,title,summaryType FROM Tdoc WHERE summaryType='FL' ORDER BY node_id",
    'AgendaItems': 'SELECT * FROM AgendaItem ORDER BY node_id',
    'Companies': 'SELECT * FROM Company ORDER BY node_id',
    'BELONGS_TO': "SELECT e.edge_id,e.src_id,e.dst_id FROM edge e JOIN Tdoc t ON t.node_id=e.src_id WHERE t.summaryType='FL' AND e.rel_type='BELONGS_TO' ORDER BY e.edge_id",
    'MODERATED_BY': "SELECT e.edge_id,e.src_id,e.dst_id FROM edge e JOIN Tdoc t ON t.node_id=e.src_id WHERE t.summaryType='FL' AND e.rel_type='MODERATED_BY' ORDER BY e.edge_id"
}
data = {k: [dict(v) for v in con.execute(q)] for k, q in queries.items()}
assert len(data['FL_Tdocs']) == 2743 and len(data['AgendaItems']) == 6439 and len(data['Companies']) == 222
for rel in ['BELONGS_TO', 'MODERATED_BY']:
    projected = [dict(v) for v in con.execute(f"SELECT e.edge_id,e.src_id,e.dst_id FROM rel_{rel} e JOIN Tdoc t ON t.node_id=e.src_id WHERE t.summaryType='FL' ORDER BY e.edge_id")]
    assert projected == data[rel]
assert len({v['companyName'] for v in data['Companies']}) == len(data['Companies'])
full_sql = '''SELECT t.node_id,t.tdocNumber,t.title,t.summaryType,ai.node_id agenda_node_id,
ai.meetingNumber,ai.agendaNumber,ai.agendaDescription,c.node_id company_node_id,c.companyName
FROM Tdoc t JOIN rel_BELONGS_TO b ON b.src_id=t.node_id JOIN AgendaItem ai ON ai.node_id=b.dst_id
JOIN rel_MODERATED_BY mo ON mo.src_id=t.node_id JOIN Company c ON c.node_id=mo.dst_id
WHERE t.summaryType='FL' ORDER BY ai.meetingNumber,ai.agendaNumber,t.tdocNumber,c.companyName'''
paths = [dict(v) for v in con.execute(full_sql)]
data['all_FL_role_paths'] = paths
data['provenance'] = {
    'frozen_SQL_sha256': before,
    'frozen_SQL_bytes': DB.stat().st_size,
    'complete_dependency_projection': 'All frozen FL Tdoc nodes, all AgendaItem/Company rows, all their outgoing BELONGS_TO/MODERATED_BY edges; no question-specific scope or top5 selection applied.',
    'source_certification': 'No full source-world FL completeness or topic-classifier certification. This is a retained-frozen-facts projection for scope sensitivity only.'
}
con.close()
raw = (json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode()
p = OUT / 'all_frozen_FL_role_dependency.json.gz'
p.write_bytes(gzip.compress(raw, mtime=0))
after = sha(DB)
assert after == before
receipt = {
    'id': 'RAN1_P2_CQ4-1', 'status': 'ACTUAL_FULL_RETAINED_FL_DEPENDENCY_EXPORT_PASS',
    'queries': queries, 'full_path_query': full_sql,
    'counts': {k: len(v) for k, v in data.items() if isinstance(v, list)},
    'typed_edge_vs_relational_views_exact': True,
    'SQL_before_sha256': before, 'SQL_after_sha256': after,
    'SQL_open_mode': 'mode=ro&immutable=1; PRAGMA query_only=ON',
    'projection': {'path': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p), 'uncompressed_bytes': len(raw), 'uncompressed_sha256': hashlib.sha256(raw).hexdigest()},
    'gold_selected': False, 'new_model_calls': 0, 'new_native_calls': 0, 'public_queue_central_changes': 0,
    'human_expert_n': 0,
}
q = OUT / 'receipt.json'
q.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'receipt': str(q), 'bytes': q.stat().st_size, 'sha256': sha(q), 'counts': receipt['counts']}, ensure_ascii=False))
