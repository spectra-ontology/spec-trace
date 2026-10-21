"""Reproduce a bounded scope conflict diagnostic, never a new answer gold."""
import sys
if sys.flags.optimize:
    raise SystemExit('Optimization is unsupported: scientific checks must execute')
import collections
import gzip
import hashlib
import io
import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

INVENTORY_SHA256 = 'cc3b87220eb09c88026dff1da21b17bf46524e1cb25dc0434c01c5481a932e6a'
ROOT = Path(__file__).absolute().parent
for p in [ROOT, *ROOT.parents]:
    if p.is_symlink():
        raise SystemExit('Symlink boundary is unsupported')
def sha(b):
    return hashlib.sha256(b).hexdigest()
def load(n):
    return json.loads((ROOT/n).read_text())
def exact_json(a, b):
    return json.dumps(a, sort_keys=True, separators=(',',':')) == json.dumps(b, sort_keys=True, separators=(',',':'))
files=set()
dirs=set()
for p in ROOT.rglob('*'):
    if p.is_symlink():
        raise SystemExit('Symlink entry rejected')
    if p.is_file(): files.add(p.relative_to(ROOT).as_posix())
    elif p.is_dir(): dirs.add(p.relative_to(ROOT).as_posix())
    else: raise SystemExit('Nonregular entry rejected')
invbytes=(ROOT/'immutable_inventory.json').read_bytes()
assert sha(invbytes)==INVENTORY_SHA256
inventory=json.loads(invbytes)
metas={'README.md','manifest.json','immutable_inventory.json','reproduce.py'}
assert files == set(inventory['files'])|metas
expected_dirs=set()
for n in files:
    expected_dirs.update(p.as_posix() for p in Path(n).parents if p.as_posix()!='.')
assert dirs==expected_dirs
for n,spec in inventory['files'].items():
    b=(ROOT/n).read_bytes()
    assert len(b)==spec['bytes'] and sha(b)==spec['sha256']
manifest=load('manifest.json')
assert set(manifest)=={'fixed_metadata','inventory_sha256','files','reproduce_sha256'}
assert exact_json(manifest['fixed_metadata'], {
    'id':'RAN1_P2_CQ3-3',
    'artifact_type':'original_source_scope_diagnostic',
    'recommendation':'clarification_required',
    'new_admissions':0,
    'API_calls':0,
    'native_executions':0,
    'complete_NR_MIMO_classifier':False,
    'all_company_attributions_source_certified':False,
})
assert manifest['inventory_sha256']==INVENTORY_SHA256
assert exact_json(manifest['files'],inventory['files'])
assert manifest['reproduce_sha256']==sha((ROOT/'reproduce.py').read_bytes())

orig=load('contract/original_question_and_query.json')
assert orig['id']=='RAN1_P2_CQ3-3'
assert orig['question_en']=='Which companies contributed most to resolutions under NR MIMO (Agenda 7.1)? Top 10.'
assert sha(orig['question_en'].encode())=='1558bcdf6940b5e99049245452034297541ad8e4afdeca6a2ff022f91ea41886'
assert sha(orig['original_cypher'].encode())=='5722fc5de43df1afb077b3cffd4e193a4ed9dfb15f5acbfe2e725929879ec2b7'
assert sha((ROOT/'contract/criteria.json').read_bytes())=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
criteria=load('contract/criteria.json')
primary=load('contract/primary_review.json')
assert primary['recommendation']=='clarification_required'
assert [x['unit'] for x in primary['semantic_units']]==criteria['semantic_units']
assert all(x['original_quote'] in orig['question_en'] for x in primary['semantic_units'])
secondary=load('contract/secondary_review.json')
assert secondary['id']==orig['id']
assert secondary['recommendation']=='clarification_required'
assert secondary['question_sha256']==orig['question_sha256']
assert secondary['original_query_sha256']==orig['query_sha256']
assert secondary['criteria_sha256']==sha((ROOT/'contract/criteria.json').read_bytes())
assert [x['unit'] for x in secondary['seven_unit_review']]==criteria['semantic_units']
p1=(ROOT/'authority/phase1_original_HEAD.md').read_text()
p2=(ROOT/'authority/phase2_original_HEAD.md').read_text()
assert '같은 agendaNumber가 다른 미팅에서 다른 description을 가질 수 있음' in p1
assert 'meetingNumber' in p1 and 'agendaNumber' in p1
assert 'references' in p2 and 'resolutionBelongsTo' in p2

W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
literal=lambda el: ''.join(t.text or '' for t in el.iter(W+'t'))
sources=load('source/two_report_scope_headings.json')['source_witnesses']
own=load('source/own_Heading_scope_addendum.json')['exact_own_headings']
for s in sources:
    m=s['meeting']
    arcbytes=(ROOT/f'source/archive_{m}.zip').read_bytes()
    apin=s['archive_matches'][0]
    assert sha(arcbytes)==apin['archive']['sha256']
    assert len(arcbytes)==apin['archive']['bytes']
    with zipfile.ZipFile(io.BytesIO(arcbytes)) as z:
        zi=z.getinfo(apin['member'])
        assert f'{zi.CRC:08x}'==apin['member_CRC32'] and zi.file_size==apin['member_size']
        doc=z.read(zi)
    assert sha(doc)==s['original_docx_sha256']==s['loader_DOCX']['sha256']
    assert len(doc)==s['loader_DOCX']['bytes']
    with zipfile.ZipFile(io.BytesIO(doc)) as z:
        xb,sb=z.read('word/document.xml'),z.read('word/styles.xml')
    assert sha(xb)==s['document_XML_sha256'] and sha(sb)==s['styles_XML_sha256']
    body=list(ET.fromstring(xb).find(W+'body'))
    for h in s['headings']+[h for h in own if h['meeting']==m]:
        el=body[h['raw_body_child0']]
        assert literal(el)==h['text']
        assert ET.tostring(el,encoding='unicode')==h['XML']
        assert [p.get(W+'val') for p in el.iter(W+'pStyle')]==h['pStyle']
    assert s['archive_matches']
assert any(x['meeting']=='84' and 'E-UTRA Releases 8' in x['text'] for x in own)
assert any(x['meeting']=='84' and 'MIMO for LTE' in x['text'] for x in own)
assert any(x['meeting']=='115' and x['raw_body_child0']==1643 and 'NR MIMO' in x['text'] for x in own)

with gzip.open(ROOT/'frozen/frozen_scope_path_projection.json.gz','rt') as f: projection=json.load(f)
assert len(projection['AgendaItem'])==6439 and len(projection['paths'])==5905
agendas={x['node_id']:x for x in projection['AgendaItem']}
assert len(agendas)==6439
assert not [ai for ai in agendas.values() if ai['agendaNumber'].startswith('7.1') and not (ai['agendaNumber']=='7.1' or ai['agendaNumber'].startswith('7.1.'))]
projection_receipt=load('frozen/projection_receipt.json')
assert projection_receipt['status']=='PASS' and projection_receipt['read_only_immutable'] is True
assert projection_receipt['sha256_before']==projection_receipt['sha256_after']=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
assert projection_receipt['projection_sha256']==sha((ROOT/'frozen/frozen_scope_path_projection.json.gz').read_bytes())
bymeeting=collections.defaultdict(list)
for ai in agendas.values(): bymeeting[ai['meetingNumber']].append(ai)
def topic(ai,term):
    return any(term in (p['agendaDescription'] or '').lower() and (p['agendaNumber']==ai['agendaNumber'] or ai['agendaNumber'].startswith(p['agendaNumber']+'.')) for p in bymeeting[ai['meetingNumber']])
membership={}
for ai in agendas.values():
    n=ai['agendaNumber']
    comp=n=='7.1' or n.startswith('7.1.')
    membership[ai['node_id']]={
        'authored_literal_prefix':n.startswith('7.1'),
        'component_7_1':comp,
        'numeric_component_AND_lexical_MIMO_parent':comp and topic(ai,'mimo'),
        'lexical_MIMO_parent_without_numeric_limit':topic(ai,'mimo'),
        'explicit_NR_MIMO_parent_without_numeric_limit':topic(ai,'nr mimo'),
    }
recorded=load('frozen/actual_scope_ranks.json')['ranks']
tops={}
for policy,expected in recorded.items():
    companynames={}
    counted=collections.defaultdict(set)
    path_counts=collections.Counter()
    for path in projection['paths']:
        if membership[path['agenda_node']][policy]:
            c=path['company_node']
            companynames[c]=path['companyName']
            counted[c].add(path['agreement_node'])
            path_counts[c]+=1
    actual={c:(companynames[c],len(a),path_counts[c]) for c,a in counted.items()}
    expected_dict={x['node_id']:(x['companyName'],x['contributionCount'],x['path_count_diagnostic']) for x in expected['whole']}
    assert actual==expected_dict
    cut=sorted((len(v) for v in counted.values()),reverse=True)[9]
    tops[policy]={c for c,v in counted.items() if len(v)>=cut}
    assert len(tops[policy])==10
    assert tops[policy]=={x['node_id'] for x in expected['top10']}
assert tops['authored_literal_prefix']==tops['component_7_1']
assert tops['authored_literal_prefix']!=tops['numeric_component_AND_lexical_MIMO_parent']
assert tops['authored_literal_prefix']!=tops['lexical_MIMO_parent_without_numeric_limit']
assert tops['authored_literal_prefix']!=tops['explicit_NR_MIMO_parent_without_numeric_limit']
assert secondary['wrong_component_prefix_actual_n']==0
for policy, diag in secondary['actual_ROOT_diagnostics'].items():
    assert tops[policy]=={x['node_id'] for x in diag['top10']}
    assert {x['node_id']:x['contributionCount'] for x in diag['top10']}=={x['node_id']:x['contributionCount'] for x in recorded[policy]['top10']}
print(json.dumps({'status':'PASS','cases':[{'id':'RAN1_P2_CQ3-3','diagnostic':'original_source_scope_and_observed_membership_conflict','recommendation':'clarification_required','source_reports':2,'frozen_documentary_paths':5905,'full_NR_MIMO_truth_claimed':False}],'new_admissions':0},ensure_ascii=False))
