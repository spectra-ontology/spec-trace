"""Replay the bounded A50 evidence; this is not an approval-count oracle."""
from pathlib import Path
import gzip
import hashlib
import json
import sys
import xml.etree.ElementTree as E

if sys.flags.optimize != 0:
    raise SystemExit('Optimization is unsupported: evidence checks must run.')

ROOT = Path(__file__).absolute().parent
INVENTORY_SHA256 = 'fd841b0c0ea47636ab379f06d84e0c43531889e8bfbcc3407dbcc6ea22e95228'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def require(value, reason):
    if not value:
        raise SystemExit(reason)

def digest(b):
    return hashlib.sha256(b).hexdigest()

for item in [ROOT, *ROOT.parents, Path(__file__).absolute()]:
    require(not item.is_symlink(), 'Symlink at entry or ancestor')
paths = []
for p in ROOT.rglob('*'):
    require(not p.is_symlink(), 'Symlink in package')
    require(p.is_file() or p.is_dir(), 'Nonregular entry')
    if p.is_file():
        paths.append(p.relative_to(ROOT).as_posix())
inventory_bytes = (ROOT / 'inventory.json').read_bytes()
require(digest(inventory_bytes) == INVENTORY_SHA256, 'Inventory pin mismatch')
inventory = json.loads(inventory_bytes)
require(set(paths) == set(inventory['files']) | {'inventory.json', 'reproduce.py'}, 'Closed file set mismatch')
for name, expected in inventory['files'].items():
    b = (ROOT / name).read_bytes()
    require(len(b) == expected['bytes'] and digest(b) == expected['sha256'], 'Payload mismatch: ' + name)

def read(name):
    b = (ROOT / name).read_bytes()
    return json.loads(gzip.decompress(b) if name.endswith('.gz') else b)

original = read('authority/original.json')
criteria = read('authority/criteria.json')
primary = read('contract/primary.json')
require(digest((ROOT / 'authority/criteria.json').read_bytes()) == 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'Criteria changed')
require(original['id'] == primary['id'] == 'RAN4_P3_CQ4-2', 'ID mismatch')
require(digest(original['question_en'].encode()) == 'c4bb53e46e8ebb35bc1596af0b23d4138f66bf1f3e3d67215165c712d0d1cbc9', 'Question changed')
require(digest(original['original_query'].encode()) == 'ec1b35eaa2ff59fe6bcd340725cf2263088230790076b5e11e591111b5b756bf', 'Query changed')
require([u['unit'] for u in primary['meaning_units']] == criteria['semantic_units'], 'Seven units changed')
require(primary['recommendation'] == 'unsupported_frozen_data' and primary['canonical_9_key_repair_binding'] is None, 'Primary metadata changed')

secondary = read('contract/secondary.json')
baseline_row = read('contract/original_row.jsonl')
require(digest((ROOT / 'contract/original_row.jsonl').read_bytes()) == 'dfc8d722368a55877c2164c691352e9d44934e85771463fde97bd39c4aa7ade8', 'Original baseline row changed')
require(baseline_row['question_en'] == original['question_en'] and baseline_row['cypher'] == original['original_query'], 'Original question/query row mismatch')
require(baseline_row['gold_primary_values'] == ['216'], 'Historical value not preserved')
require(secondary['decision'] == primary['recommendation'] == 'unsupported_frozen_data', 'Two-review decision mismatch')
require(secondary['subtype'] == primary['subtype'] == 'own_approval_object_binding_loss', 'Two-review subtype mismatch')
require([u['unit'] for u in secondary['meaning_units']] == criteria['semantic_units'], 'Independent seven units changed')
require(secondary['reviewer'] != primary['reviewer'], 'Independent reviewer identity lost')
require(secondary['primary_review_seen']['sha256'] == digest((ROOT / 'contract/primary.json').read_bytes()), 'Secondary/primary binding mismatch')
require(secondary['question_sha256'] == primary['question_sha256'] and secondary['original_query_sha256'] == primary['original_query_sha256'], 'Independent original binding mismatch')
require(secondary['scalar_gold'] is None and secondary['canonical_repair'] is None, 'Classification replaced by scalar repair')

frontier = read('data/complete_recorded_frontier.json.gz')
matrix = read('data/count_impact_matrix.json.gz')
rs = {r['node_id']: r for r in frontier['resolutions']}
require(len(rs) == len(matrix['rows']) == 216, '216 frontier changed')
require(len(frontier['paths']) == 1766 and len(frontier['CRs']) == 1733, 'Path/CR frontier changed')
require(set(rs) == {r['node_id'] for r in matrix['rows']} == {p['r_node'] for p in frontier['paths']}, 'Frontier identity mismatch')
require(matrix['adopted_scalar'] is None and matrix['API_calls'] == matrix['native_calls'] == 0, 'Diagnostic mistaken for gold')
classes = {}
for row in matrix['rows']:
    classes[row['classification']] = classes.get(row['classification'], 0) + 1
    require(row['content_sha256'] == digest(rs[row['node_id']]['content'].encode()), 'Matrix/body binding mismatch')
    require(row['recorded_38_133_path_n'] == sum(p['r_node'] == row['node_id'] for p in frontier['paths']), 'Multiplicity mismatch')
require(classes == matrix['classification_counts'], 'Review bucket recount failed')

saved_root = read('proof/ROOT_22588_reopen.json')
positive = read('proof/count_level_alternatives.json.gz')
xml = gzip.decompress((ROOT / 'source/report91_document.xml.gz').read_bytes())
styles = gzip.decompress((ROOT / 'source/report91_styles.xml.gz').read_bytes())
require(digest(xml) == positive['source91']['document_xml_sha256'], 'Original XML pin mismatch')
require(digest(styles) == positive['source91']['styles_xml_sha256'], 'Original styles pin mismatch')
paragraphs = list(E.fromstring(xml).iter(W + 'p'))

def sig(e):
    return (e.tag, tuple(sorted(e.attrib.items())), e.text, e.tail, tuple(sig(x) for x in e))

actual = {}
for p in saved_root['actual_original_paragraphs']:
    e = paragraphs[p['paragraph']]
    text = ''.join(t.text or '' for t in e.iter(W + 't'))
    require(text == p['text'] and digest(repr(sig(e)).encode()) == p['xml_tree_sha256'], 'Original paragraph mismatch')
    for name, tags in [('direct_strike_n', ['strike', 'dstrike']), ('tracked_delete_n', ['del']), ('hidden_n', ['vanish'])]:
        require(sum(len(list(e.iter(W + tag))) for tag in tags) == p[name], 'Direct format observation changed')
    actual[p['paragraph']] = text
quote = 'except E-UTRA PSCell and E-UTRA SCell carrier frequencies'
require(quote in actual[2071] and 'Agreement:' in actual[2071], 'Own source text changed')
require('R4-1907768' in actual[2066] and '38.133' in actual[2066], 'Own source carrier/target changed')
require(actual[2072].replace(' ', '').endswith('Endorsed'), 'Own source outcome changed')
require(actual[2078].replace(' ', '').endswith('Noted'), 'Following object outcome changed')
own = rs[22588]['content']
require(own == saved_root['frozen_own_resolution']['content'], 'Frozen own body mismatch')
require(own.startswith('“” can be further improved.\nDecision:\t\tEndorsed\nR4-1906404'), 'Own binding-loss witness changed')
require(quote not in own and 'R4-1907768' not in own, 'Own loss premise changed')
own_paths = [p for p in frontier['paths'] if p['r_node'] == 22588]
require(len(own_paths) == 1 and own_paths[0]['tdocNumber'] == 'R4-1906404', 'Recorded pair counterevidence changed')
require(saved_root['complete_node_property_scan']['nodes'] == 342161 and saved_root['complete_node_property_scan']['properties'] == 2281290, 'Saved global audit scope changed')
require(saved_root['complete_node_property_scan']['normalized_lost_technical_quote_matches'] == [], 'Saved global absence premise changed')
require({x['node_id'] for x in saved_root['complete_node_property_scan']['all_current_CR_identity_mentions']} == {221795, 340859}, 'Surviving CR/BigCR counterevidence changed')

rows105 = positive['requested_count_recovery_positive_105']['rows']
require(len(rows105) == 1 and rows105[0]['specNumber'] == '38.133' and rows105[0]['sectionNumber'] == 'A.15.2' and rows105[0]['canonicalMeetingNumber'] == 'RAN4#105', 'Positive count-level alternative lost')
alt96 = positive['substantive_recovery_positive_23086']
require(alt96['normalized_quote_exact_substring'] is True and alt96['target'] == '38.133' and alt96['own_retained_prefix'] in alt96['CR_reason'], 'Positive reason alternative lost')
for node in [22090, 22131, 22330, 22987]:
    row = next(r for r in matrix['rows'] if r['node_id'] == node)
    require(row['prefix_affirmative_outcomes'] and row['source_context']['nearest_header_CR_targets'] == [], 'Non-CR affirmative countercase changed')

print(json.dumps({
    'status': 'PASS', 'cases': [{'id': 'RAN4_P3_CQ4-2',
        'classification_state': 'two_AI_semantic_judgments_agree_awaiting_ROOT_final_seal',
        'classification': primary['recommendation'], 'subtype': primary['subtype'], 'separate_AI_reviews': 2, 'original_benchmark_value_preserved': '216', 'original_domain_Resolution_n': len(rs),
        'original_domain_path_n': len(frontier['paths']), 'source91_original_paragraphs_replayed': len(actual),
        'whole_frozen_absence_scope': 'saved pinned ROOT audit, not a fresh342161-node scan by this portable replay',
        'count_level_positive_alternatives_preserved': [21690, 21691, 23086],
        'adopted_count_gold': None, 'source_scope': 'full original91 XML/styles plus original216 frozen projection and pinned completed audits'}],
    'new_admissions': 0, 'native_calls': 0, 'API_calls': 0,
    'whole_CQ_final_adjudication_complete': False,
}, ensure_ascii=False))
