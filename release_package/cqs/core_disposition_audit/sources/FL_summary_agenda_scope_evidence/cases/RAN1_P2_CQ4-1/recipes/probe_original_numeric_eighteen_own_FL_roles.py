"""Check the strongest numeric-first counterpolicy's 18 actual own role headers."""
import gzip
import hashlib
import io
import json
import re
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

C = Path(__file__).resolve().parent
R = C
while not (R / 'AGENTS.md').is_file():
    R = R.parent
D = C / 'actual_original_scope_v1'
raw = json.loads((D / 'actual_frozen_scope_rank_sensitivities.json').read_bytes())
paths = raw['paths']['authored_numeric_startswith_7_1']
fixture = json.loads(gzip.decompress((C / 'actual_frozen_FL_role_dependency_v1/all_frozen_FL_role_dependency.json.gz').read_bytes()))
companies = {v['node_id']: v for v in fixture['Companies']}
sha = lambda b: hashlib.sha256(b).hexdigest()
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def text(e, tabs=False):
    return ''.join('\t' if n.tag == W + 'tab' else n.text or '' for n in e.iter() if n.tag == W + 't' or (tabs and n.tag == W + 'tab'))


def pin(p):
    return {'path': str(p.relative_to(R)), 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())}


reports, observations = [], []
for meeting in sorted({v['meetingNumber'] for v in paths}):
    wanted = {v['tdocNumber']: v for v in paths if v['meetingNumber'] == meeting}
    name = {'108': '108-e', '110b': '110b-e'}.get(meeting, meeting)
    loader = R / ('ontology/input/tsg/RAN/formal/meetings/RAN1/Final_Report/Final_Report_RAN1-' + name + '.docx')
    data = loader.read_bytes()
    physical = []
    folder = R / ('data/corpus/tsg/RAN/formal/meetings/RAN1/source/TSGR1_' + name + '/Report')
    for ap in sorted(folder.glob('*.zip')):
        with zipfile.ZipFile(ap) as z:
            for zi in z.infolist():
                if zi.filename.lower().endswith('.docx') and sha(z.read(zi)) == sha(data):
                    physical.append({'archive': pin(ap), 'member': zi.filename, 'member_bytes': zi.file_size, 'CRC32': zi.CRC})
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        assert z.testzip() is None
        xml, styles = z.read('word/document.xml'), z.read('word/styles.xml')
    body = list(E.fromstring(xml).find(W + 'body'))
    stack, found = {}, {tid: [] for tid in wanted}
    for i, el in enumerate(body):
        candidates = []
        if el.tag == W + 'p':
            ps = el.find(W + 'pPr/' + W + 'pStyle')
            m = re.fullmatch(r'Heading([1-9])', ps.get(W + 'val', '') if ps is not None else '')
            if m:
                level = int(m[1])
                stack = {k: v for k, v in stack.items() if k < level}
                stack[level] = {'raw_body_child0': i, 'level': level, 'text': text(el)}
            candidates.append((None, text(el, True).split('\t'), el))
        elif el.tag == W + 'tbl':
            for j, tr in enumerate(el.findall(W + 'tr')):
                candidates.append((j, [text(tc) for tc in tr.findall(W + 'tc')], tr))
        for trn, fields, own in candidates:
            tid = fields[0].strip() if fields else ''
            if tid not in wanted or len(fields) < 3:
                continue
            if not re.search(r'(?:FL\s+summary|Feature\s+lead\s+summary)', fields[1], re.I):
                continue
            role = re.search(r'(?:Moderator|Feature\s+Lead)\s*\(([^)]+)\)', fields[2], re.I)
            if role is None:
                continue
            co = companies[wanted[tid]['company_node_id']]
            aliases = json.loads(co['aliases'] or '[]')
            literal = role[1].strip()
            found[tid].append({'raw_body_child0': i, 'direct_table_row0': trn, 'fields': fields,
                               'own_first_field_identity': tid, 'own_role_company_literal': literal,
                               'existing_frozen_companyName': co['companyName'],
                               'source_literal_in_existing_frozen_name_or_aliases': literal in [co['companyName'], *aliases],
                               'heading_stack': list(stack.values()), 'own_XML': E.tostring(own, encoding='unicode')})
    reports.append({'meetingNumber': meeting, 'loader': pin(loader), 'physical_exact_member_matches': physical,
                    'XML_sha256': sha(xml), 'styles_sha256': sha(styles),
                    'own_frozen_numeric_FL_records_expected': len(wanted), 'physical_exact_match_observed': bool(physical)})
    observations.extend({'frozen_path': wanted[tid], 'own_role_headers': found[tid]} for tid in wanted)
closed = sum(len(v['own_role_headers']) == 1 and v['own_role_headers'][0]['source_literal_in_existing_frozen_name_or_aliases'] for v in observations)
record = {'id': 'RAN1_P2_CQ4-1', 'status': 'ACTUAL_NUMERIC18_OWN_FL_ROLE_REOPEN_COMPLETE',
          'numeric_policy_is_selected_gold': False, 'full18_own_company_role_closed': closed == 18,
          'closed_own_role_rows': closed, 'reports': reports, 'observations': observations,
          'limits': ['This tests the original numeric-first scope as counterevidence; it does not choose that interpretation as gold.',
                     'Own role-header fidelity does not establish that an FL technical topic is NR MIMO or causal leadership.',
                     'No missing-source-world entrant completeness or entire source-body correctness claim.'],
          'new_model_calls': 0, 'new_native_calls': 0, 'original560_pass_increment': 0, 'human_expert_n': 0}
p = C / 'actual_original_numeric18_own_FL_role_counterevidence_v1.json'
with p.open('x') as f:
    json.dump(record, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(json.dumps({'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes()),
                  'closed18': closed, 'physical_reports': sum(v['physical_exact_match_observed'] for v in reports),
                  'reports': len(reports)}))
