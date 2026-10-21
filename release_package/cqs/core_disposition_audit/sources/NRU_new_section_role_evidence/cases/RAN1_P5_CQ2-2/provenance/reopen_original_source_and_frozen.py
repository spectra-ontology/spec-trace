"""Read original NR-U scope and immutable graph evidence; no admission or model call."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

if sys.flags.optimize:
    raise SystemExit('Run without optimization')
ap = argparse.ArgumentParser()
ap.add_argument('--sqlite', type=Path, required=True)
ap.add_argument('--public-root', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True)
a = ap.parse_args()
L = Path(__file__).resolve().parent
R = next(p for p in L.parents if (p / 'CLAUDE.md').is_file())
D = a.out.resolve()
assert not D.exists()
D.mkdir(parents=True)
N = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{' + N['w'] + '}'
ID = 'RAN1_P5_CQ2-2'


def digest(b):
    return hashlib.sha256(b).hexdigest()


def pin(p):
    p = Path(p)
    b = p.read_bytes()
    return {'path': str(p), 'bytes': len(b), 'sha256': digest(b)}


def save(name, value):
    p = D / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    return pin(p)


def copy(name, p):
    dst = D / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(p.read_bytes())
    return pin(p)


def active_text(x):
    out = []
    def visit(y):
        if y.tag in {W + 'del', W + 'moveFrom'}:
            return
        if y.tag == W + 't':
            out.append(y.text or '')
        for z in y:
            visit(z)
    visit(x)
    return ''.join(out)


def paragraph(x, index):
    sty = x.find('w:pPr/w:pStyle', N)
    return {'index': index, 'style': sty.get(W + 'val') if sty is not None else None,
            'text': active_text(x), 'insertions': len(x.findall('.//w:ins', N)),
            'deletions': len(x.findall('.//w:del', N)),
            'moves_from': len(x.findall('.//w:moveFrom', N))}


benchmark = a.public_root / 'release_package/cqs/original_core_repair/provenance/original_benchmark.jsonl'
raw = [b for b in benchmark.read_bytes().splitlines(keepends=True)
       if json.loads(b)['id'] == ID]
assert len(raw) == 1
q = json.loads(raw[0])
assert q['question_en'] == 'Which new sections did the NR-U study (TR 38.889) add to TS 38.211-38.214? (PHY-layer reference)'
(D / 'original_benchmark_record.jsonl').write_bytes(raw[0])
criteria = a.public_root / 'release_package/cqs/original_core_overnight_repairs48/criteria.json'
assert pin(criteria)['sha256'] == 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
copy('criteria.json', criteria)
cqpath = R / 'logs/tsg/RAN/formal/RAN1/phase-5/cq_test_dataset.json'
cq = json.loads(cqpath.read_bytes())
def find_cq(x):
    if isinstance(x, dict):
        if x.get('id') == 'CQ2-2' or x.get('cq_id') == 'CQ2-2':
            yield x
        for v in x.values():
            yield from find_cq(v)
    elif isinstance(x, list):
        for v in x:
            yield from find_cq(v)
own = list(find_cq(cq))
assert len(own) == 1
copy('original_author_CQ_dataset.json', cqpath)
save('original_question_and_query.json', {
    'id': ID, 'original_record': q, 'raw_record_sha256': digest(raw[0]),
    'question_sha256': digest(q['question_en'].encode()),
    'query_sha256': digest(q['cypher'].encode()), 'criteria': pin(criteria),
    'original_benchmark': pin(benchmark), 'author_CQ_file': pin(cqpath),
    'author_CQ_record': own[0],
    'scope_rule': 'Original NR-U study, target TS38.211 through TS38.214, actual newly added sections. Manual mapping counts and unrelated work-item expansions are diagnostics only.'})

authority = []
for rel, spans in [
    ('docs/tsg/RAN/formal/RAN1/phase-5/step1_tr_parsing.md', [(1, 34), (58, 108)]),
    ('docs/tsg/RAN/formal/RAN1/phase-5/step2_neo4j_loading.md', [(35, 58)]),
    ('docs/tsg/RAN/formal/RAN1/phase-5/step3_validation.md', [(1, 37)]),
    ('scripts/tsg/RAN/formal/RAN1/phase-5/tr-parser/02_generate_tr_jsonld.py', [(130, 202), (260, 313)])]:
    p = R / rel
    ls = p.read_text().splitlines()
    authority.append({'source': pin(p), 'role': 'Current implementation and counterauthority; not a replacement for original question scope',
                      'spans': [{'first_line': lo, 'last_line': hi, 'text': '\n'.join(ls[lo-1:hi])} for lo, hi in spans]})
save('author_implementation_and_counterauthority_spans.json', authority)
for src, dest in [('tr_impact_mapping.csv', 'original_TR_impact_mapping.csv'),
                  ('tr_workitem_mapping.csv', 'original_TR_workitem_mapping.csv')]:
    p = R / 'ontology/input/tsg/RAN/formal/TR/RAN1' / src
    copy(dest, p)
    rows = list(csv.DictReader(io.StringIO(p.read_text())))
    save(dest + '.selected.json', {'source': pin(p), 'all_rows': len(rows),
                                  'selected': [x for x in rows if x['trNumber'] == '38.889']})

sources = []
source_defs = [('TR38889', R / 'ontology/input/tsg/RAN/formal/TR/RAN1/38.889/38889-g00.docx')]
for spec in ['38.211', '38.212', '38.213', '38.214']:
    ps = list((R / 'ontology/input/tsg/RAN/formal/TS/RAN1' / spec).glob('*.docx'))
    assert len(ps) == 1
    source_defs.append(('TS' + spec.replace('.', ''), ps[0]))
for key, pattern in [('CR1913630', '*1913630*'), ('CR1913631', '*1913631*')]:
    ps = list((R / 'ontology/input/tsg/RAN/formal/CR/RAN1').rglob(pattern))
    assert len(ps) == 1
    source_defs.append((key, ps[0]))
for key, p in source_defs:
    with zipfile.ZipFile(p) as z:
        xml = z.read('word/document.xml')
        styles = z.read('word/styles.xml')
        root = ET.fromstring(xml)
        body = root.find('w:body', N)
        ps = body.findall('w:p', N)
        paras = [paragraph(x, i) for i, x in enumerate(ps)]
        src = {'key': key, 'archive': pin(p), 'document_xml': {'bytes': len(xml), 'sha256': digest(xml)},
               'styles_xml': {'bytes': len(styles), 'sha256': digest(styles)},
               'body_children': len(body), 'direct_body_paragraphs': len(ps)}
        for name, b in [('document.xml', xml), ('styles.xml', styles)]:
            out = D / 'source' / key / (name + '.gz')
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(gzip.compress(b, mtime=0))
        if key == 'TR38889':
            src['scope'] = paras[159:166]
            src['conclusions'] = paras[1176:1205]
            src['own_reference_to_TS38213_section13'] = paras[871:875]
            src['all_TS38_211_to_214_mentions'] = [x for x in paras if re.search(r'38\.21[1-4]', x['text'])]
        elif key.startswith('TS'):
            src['top_level_headings'] = [x for x in paras if x['style'] == 'Heading1']
            if key == 'TS38213':
                src['section16_start'] = paras[4362:4373]
        else:
            tbl = body[6]
            assert tbl.tag == W + 'tbl'
            rows = []
            for i, tr in enumerate(tbl.findall('w:tr', N)):
                rows.append({'row': i, 'cells': [active_text(tc) for tc in tr.findall('w:tc', N)]})
            src['cover_table_body_child'] = 6
            src['cover_rows'] = rows
            src['all_heading_or_explicit_new_section_paragraphs'] = [
                {'body_child': i, **paragraph(x, i)} for i, x in enumerate(body)
                if x.tag == W + 'p' and (
                    ((x.find('w:pPr/w:pStyle', N) is not None) and
                     x.find('w:pPr/w:pStyle', N).get(W + 'val', '').startswith('Heading'))
                    or re.match(r'6\.3\.2\.(1\.[34]|4\.1\.[45]|4\.2\.[45])\D', active_text(x)))]
        sources.append(src)
save('direct_original_source_and_format.json', sources)

before = pin(a.sqlite)
c = sqlite3.connect(a.sqlite.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
c.row_factory = sqlite3.Row
save('original_SQL_table_schemas.json', {t: [dict(x) for x in c.execute('PRAGMA table_info("' + t + '")')]
    for t in ['TechnicalReport', 'TRImpact', 'Spec', 'Section', 'CR']})
queries = {
    'original_projection': '''SELECT tr.trNumber AS "tr.trNumber",ti.affectedSection AS "ti.affectedSection",s.sectionId AS "s.sectionId",ti.impactDescription AS "ti.impactDescription"
FROM TechnicalReport tr JOIN rel_HAS_TR_IMPACT h ON h.src_id=tr.node_id JOIN TRImpact ti ON ti.node_id=h.dst_id
JOIN rel_IMPACTS_SECTION i ON i.src_id=ti.node_id JOIN Section s ON s.node_id=i.dst_id
WHERE tr.trNumber='38.889' AND ti.impactType='NewSection' ORDER BY s.sectionId''',
    'scope_only_filter_diagnostic': '''SELECT tr.trNumber,ti.affectedSection,s.sectionId,ti.impactDescription,sp.specNumber
FROM TechnicalReport tr JOIN rel_HAS_TR_IMPACT h ON h.src_id=tr.node_id JOIN TRImpact ti ON ti.node_id=h.dst_id
JOIN rel_IMPACTS_SECTION i ON i.src_id=ti.node_id JOIN Section s ON s.node_id=i.dst_id
JOIN rel_IMPACTS_SPEC m ON m.src_id=ti.node_id JOIN Spec sp ON sp.node_id=m.dst_id
WHERE tr.trNumber='38.889' AND ti.impactType='NewSection' AND sp.specNumber IN ('38.211','38.212','38.213','38.214') ORDER BY s.sectionId''',
    'all_own_impacts': '''SELECT tr.trNumber,ti.node_id AS impact_node,ti.trImpactId,ti.impactType,ti.affectedSection,ti.impactDescription,
sp.node_id AS spec_node,sp.specNumber,sp.specRelease,sp.specVersion,s.node_id AS section_node,s.sectionId,s.sectionNumber,s.sectionTitle
FROM TechnicalReport tr JOIN rel_HAS_TR_IMPACT h ON h.src_id=tr.node_id JOIN TRImpact ti ON ti.node_id=h.dst_id
LEFT JOIN rel_IMPACTS_SPEC m ON m.src_id=ti.node_id LEFT JOIN Spec sp ON sp.node_id=m.dst_id
LEFT JOIN rel_IMPACTS_SECTION i ON i.src_id=ti.node_id LEFT JOIN Section s ON s.node_id=i.dst_id
WHERE tr.trNumber='38.889' ORDER BY sp.specNumber,s.sectionId''',
    'TR_all_incident_edges': '''SELECT e.* FROM TechnicalReport tr JOIN edge e ON e.src_id=tr.node_id OR e.dst_id=tr.node_id WHERE tr.trNumber='38.889' ORDER BY e.edge_id''',
    'workitem_frontier': '''SELECT w.workItemCode,e.rel_type,n.labels,count(*) AS n FROM WorkItem w
JOIN edge e ON e.src_id=w.node_id OR e.dst_id=w.node_id JOIN node n ON n.node_id=CASE WHEN e.src_id=w.node_id THEN e.dst_id ELSE e.src_id END
WHERE w.workItemCode IN ('FS_NR_unlic','NR_unlic','NR_unlic-Core') GROUP BY w.workItemCode,e.rel_type,n.labels ORDER BY w.workItemCode,e.rel_type,n.labels''',
    'NRU_CR_alternative': '''SELECT cr.node_id,cr.id,cr.title,cr.status,cr.crCategory,cr.clausesAffected,cr.reasonForChange,cr.summaryOfChange,
sp.specNumber,s.sectionId,s.sectionTitle FROM CR cr JOIN rel_RELATED_TO r ON r.src_id=cr.node_id JOIN WorkItem w ON w.node_id=r.dst_id
LEFT JOIN rel_MODIFIES m ON m.src_id=cr.node_id LEFT JOIN Spec sp ON sp.node_id=m.dst_id
LEFT JOIN rel_MODIFIES_SECTION k ON k.src_id=cr.node_id LEFT JOIN Section s ON s.node_id=k.dst_id
WHERE w.workItemCode='NR_unlic-Core' AND sp.specNumber IN ('38.211','38.212','38.213','38.214') ORDER BY cr.id,s.sectionId''',
    'explicit_new_sections_in_CR38212_source': '''SELECT s.node_id,s.sectionId,s.sectionTitle,cr.id AS directly_linked_CR
FROM Section s LEFT JOIN rel_MODIFIES_SECTION m ON m.dst_id=s.node_id
LEFT JOIN CR cr ON cr.node_id=m.src_id AND cr.tdocNumber='R1-1913631'
WHERE s.sectionId LIKE '38.212-Rel-16-%' AND s.sectionNumber IN ('6.3.2.1.3','6.3.2.1.4','6.3.2.4.1.4','6.3.2.4.1.5','6.3.2.4.2.4','6.3.2.4.2.5')
ORDER BY s.sectionId,cr.id'''
}
results = {}
for name, sql in queries.items():
    rs = [dict(x) for x in c.execute(sql)]
    results[name] = {'sql': sql, 'sql_sha256': digest(sql.encode()), 'rows': rs, 'row_count': len(rs)}
save('actual_immutable_SQL_diagnostics.json', results)

# All source-TR and own-impact incident edges are retained, including incoming aliases.
trids = {x[0] for x in c.execute("SELECT node_id FROM TechnicalReport WHERE trNumber='38.889'")}
assert len(trids) == 1
impact_ids = {x[0] for x in c.execute("SELECT h.dst_id FROM TechnicalReport t JOIN rel_HAS_TR_IMPACT h ON h.src_id=t.node_id WHERE t.trNumber='38.889'")}
crids = {x[0] for x in c.execute("SELECT node_id FROM CR WHERE tdocNumber IN ('R1-1913630','R1-1913631')")}
assert len(crids) == 2
core = trids | impact_ids | crids
marks = ','.join('?' for _ in core)
edges = [dict(x) for x in c.execute('SELECT * FROM edge WHERE src_id IN (' + marks + ') OR dst_id IN (' + marks + ') ORDER BY edge_id', tuple(sorted(core)) * 2)]
nodes = core | {e[k] for e in edges for k in ['src_id', 'dst_id']}
records = [dict(x) for nid in sorted(nodes) for x in c.execute('SELECT * FROM _node_record WHERE node_id=?', (nid,))]
save('own_TR_impact_and_two_CR_all_incident_frozen_slice.json', {'core_node_ids': sorted(core), 'records': records, 'edges': edges,
     'scope': 'Complete incident-edge slice for the original TR, its four impacts and two source-counterexample CRs; not a complete replacement frozen graph.'})

scalars_scanned = 0
hits = {'TR_number': [], 'new_marker': []}
def strings(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, list):
        for y in x: yield from strings(y)
    elif isinstance(x, dict):
        for y in x.values(): yield from strings(y)
node_count = 0
for row in c.execute('SELECT node_id,labels_json,properties_json FROM _node_record ORDER BY node_id'):
    node_count += 1
    vals = list(strings(json.loads(row['properties_json'])))
    scalars_scanned += len(vals)
    for s in vals:
        if '38.889' in s:
            hits['TR_number'].append({'node_id': row['node_id'], 'labels': json.loads(row['labels_json']), 'value': s})
        if re.search(r'6\.3\.2\.(?:1\.[34]|4\.1\.[45]|4\.2\.[45])\s*\(new\)', s, re.I):
            hits['new_marker'].append({'node_id': row['node_id'], 'labels': json.loads(row['labels_json']), 'value': s})
save('whole_decoded_frozen_explicit_role_frontier.json', {
    'all_node_records_scanned': node_count, 'decoded_string_scalars_scanned': scalars_scanned, 'hits': hits,
    'meaning': 'Literal TR-identity and explicit original CR new-marker alternatives only. Keyword absence alone is not a proof of arbitrary unrecoverability; full own incidence and concrete source-role counterexamples are separate.'})
c.close()
after = pin(a.sqlite)
assert before == after
save('actual_source_and_frozen_reopen_receipt.json', {
    'id': ID, 'sqlite_before': before, 'sqlite_after': after,
    'mode': 'sqlite mode=ro&immutable=1; independent from Cypher and no native driver',
    'original_question_sha256': digest(q['question_en'].encode()),
    'original_query_sha256': digest(q['cypher'].encode()), 'criteria': pin(criteria),
    'source_archives': [s['archive'] for s in sources],
    'all_nodes_scanned': node_count, 'all_strings_scanned': scalars_scanned,
    'native_calls': 0, 'API_calls': 0, 'DB_mutations': 0, 'P_mutations': 0,
    'classification_status': 'Evidence prepared; independent semantic judgments and ROOT seal remain separate.'})
print(json.dumps({'out': str(D), 'original_projection_rows': results['original_projection']['row_count'],
                  'own_impacts': results['all_own_impacts']['row_count'], 'sources': len(sources),
                  'nodes_scanned': node_count, 'receipt': pin(D / 'actual_source_and_frozen_reopen_receipt.json')}))
