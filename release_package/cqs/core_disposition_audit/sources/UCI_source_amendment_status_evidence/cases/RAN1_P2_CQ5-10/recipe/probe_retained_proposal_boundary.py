"""Readonly UCI boundary experiment; no native gold or semantic pass is asserted."""
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / 'CLAUDE.md').is_file())
TASK = ROOT / 'logs/pending-tasks/spectracq-core-contract-2026-10-13'
BASE = TASK / 'empirical/overnight_reaudit'
OLD = BASE / 'root_evidence/two_agent_unresolved_loop/RAN1_RAN3_RAN4'
SOURCE = OLD / 'loop114_RAN1_ten_report_generic_source_text_and_DMRS_tie_proposal_NOT_ADMITTED/evidence'
DB = TASK / 'empirical/relational/RAN1.sqlite'
BENCH = Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/cqs/original_core_repair/provenance/original_benchmark.jsonl')
QID = 'RAN1_P2_CQ5-10'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'
HEADER = re.compile(r'R1-[0-9]{6,8}\t[^\t]+\t.+')
PROPOSAL = re.compile(r'Proposal\s+[0-9]+(?:\.[0-9]+)*\s*:.*', re.I)
CAPTION = re.compile(r'TP\s+for\s+.+\s*:', re.I)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pin(p):
    p = p.resolve()
    b = p.read_bytes()
    return {'path': str(p), 'sha256': sha(b), 'bytes': len(b)}


def gzrows(name):
    with gzip.open(SOURCE / name, 'rt') as f:
        return [json.loads(x) for x in f]


def owned_prefix(text):
    lines = text.split('\n')
    boundaries = []
    for i, line in enumerate(lines):
        if HEADER.fullmatch(line.strip()):
            boundaries.append((i, 'retained_three_column_Tdoc_header'))
        if PROPOSAL.fullmatch(line.strip()):
            j = i - 1
            while j >= 0 and not lines[j].strip():
                j -= 1
            begin = j if j >= 0 and CAPTION.fullmatch(lines[j].strip()) else i
            boundaries.append((begin, 'numbered_Proposal_with_optional_TP_caption'))
    cut, reason = min(boundaries) if boundaries else (len(lines), None)
    return '\n'.join(lines[:cut]), {'line0': cut if reason else None, 'rule': reason}


def block_packet(el, i):
    math = []
    for j, eq in enumerate(el.iter(M + 'oMath')):
        raw = ET.tostring(eq, encoding='utf-8')
        math.append({'ordinal': j, 'math_literal_tokens': ''.join(t.text or '' for t in eq.iter(M + 't')),
                     'XML': raw.decode(), 'XML_sha256': sha(raw)})
    return {'raw_body_child0': i, 'tag': el.tag.split('}')[-1],
            'word_text': ''.join(t.text or '' for t in el.iter(W + 't')),
            'XML': ET.tostring(el, encoding='unicode'), 'OMML': math,
            'OLE_object_count': sum(x.tag.endswith('OLEObject') for x in el.iter()),
            'direct_strike_runs': [{'text': ''.join(t.text or '' for t in r.iter(W + 't')),
                                   'rPr_XML': ET.tostring(r.find(W + 'rPr'), encoding='unicode')}
                                  for r in el.iter(W + 'r') if r.find(W + 'rPr/' + W + 'strike') is not None]}


def main():
    out = HERE / 'actual_retained_proposal_boundary_v1'
    out.mkdir(exist_ok=False)
    rawline = next(x for x in BENCH.read_bytes().splitlines() if json.loads(x)['id'] == QID)
    original = json.loads(rawline)
    c = sqlite3.connect(DB.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA query_only=ON')
    query = '''SELECT a.node_id,a.resolutionId,a.content,a.contentWithEquations,a.note,
    m.meetingNumber,m.meetingNumberInt FROM Agreement a JOIN edge e
    ON e.src_id=a.node_id AND e.rel_type='MADE_AT' JOIN Meeting m ON m.node_id=e.dst_id'''
    joins = [dict(x) for x in c.execute(query)]
    positive = [x for x in joins if isinstance(x['content'], str) and 'UCI' in x['content'] and 'multiplex' in x['content']]
    repaired = []
    changes = []
    for x in positive:
        own, boundary = owned_prefix(x['content'])
        keep = 'UCI' in own and 'multiplex' in own
        if boundary['rule']:
            changes.append({'resolutionId': x['resolutionId'], 'meetingNumberInt': x['meetingNumberInt'],
                            'predicate_kept': keep, 'boundary': boundary, 'owned_prefix': own,
                            'retained_original_content': x['content']})
        if keep:
            repaired.append(x)
    repaired.sort(key=lambda x: (-x['meetingNumberInt'], x['resolutionId']))
    cutoff = repaired[9]['meetingNumberInt']
    frontier = [x for x in positive if x['meetingNumberInt'] >= cutoff]
    selected_frontier = [x for x in repaired if x['meetingNumberInt'] >= cutoff]
    geom = {x['resolutionId']: x for x in gzrows('identity_and_source_geometry.jsonl.gz')}
    patches = gzrows('generic_property_patch.jsonl.gz')
    broad = [x for x in patches if 'UCI' in x['sourceRecordWindowText'] and 'multiplex' in x['sourceRecordWindowText']]
    broad_frontier = [x for x in broad if geom[x['resolutionId']]['meetingNumberInt'] >= cutoff]
    unbound = [x for x in gzrows('all112_unbound_full_source_windows.jsonl.gz')
               if 'UCI' in x['full_source_candidate_window_literal'] and 'multiplex' in x['full_source_candidate_window_literal']]
    packets = []
    roots = {}
    for x in sorted(frontier, key=lambda y: (-y['meetingNumberInt'], y['resolutionId'])):
        g = geom[x['resolutionId']]
        label = g['meeting'].split('#')[1]
        if label not in roots:
            xml = gzip.decompress((SOURCE / f'RAN1_{label}_document.xml.gz').read_bytes())
            roots[label] = list(ET.fromstring(xml).find(W + 'body'))
        lo, hi = g['source_record_raw_body_child_range']
        raw = roots[label]
        own, boundary = owned_prefix(x['content'])
        packets.append({'frozen': x, 'predicate_kept': 'UCI' in own and 'multiplex' in own,
                        'retained_boundary': boundary, 'source_geometry': g,
                        'actual_source_blocks': [block_packet(raw[i], i) for i in range(max(0, lo-1), min(len(raw), hi+2))],
                        'frozen_original_node': dict(c.execute('SELECT * FROM _node_record WHERE node_id=?', (x['node_id'],)).fetchone()),
                        'frozen_incident_edges': [dict(z) for z in c.execute('SELECT * FROM edge WHERE src_id=? OR dst_id=?', (x['node_id'], x['node_id']))]})
    controls = []
    for name, text, expected in [
        ('deferred numbered proposal caption', 'Endorse TP for TS38.211.\nTP for UCI multiplexing:\nProposal 2.3.1: Adopt TP.', False),
        ('keywords in preceding own agreement retained', 'Agree UCI multiplexing.\nTP for another topic:\nProposal 1: Later work.', True),
        ('inline proposal mention retained', 'The UCI multiplexing proposal 2.3.1 is agreed.', True),
        ('table proposal cell retained', 'Agree:\n| Proposal 1: UCI multiplexing |', True),
        ('own titled accepted numbered proposal is known false cut', 'The following is agreed:\nProposal 1: UCI multiplexing.', False),
    ]:
        prefix, boundary = owned_prefix(text)
        actual = 'UCI' in prefix and 'multiplex' in prefix
        if actual != expected:
            raise AssertionError(name)
        controls.append({'name': name, 'input': text, 'actual_kept': actual, 'boundary': boundary})
    receipt = {'status': 'ACTUAL_RETAINED_BOUNDARY_AND_SOURCE_FRONTIER_PROBE_NOT_FINAL',
               'id': QID, 'utc': datetime.now(timezone.utc).isoformat(),
               'question_en': original['question_en'], 'question_sha256': sha(original['question_en'].encode()),
               'original_query': original['cypher'], 'original_query_sha256': sha(original['cypher'].encode()),
               'original_source_record_sha256': sha(rawline), 'benchmark': pin(BENCH),
               'criteria': pin(OLD / 'loop171_Huawei_original15_documentary_Tdoc_identity_source_contract/criteria.json'),
               'all_Agreement_nodes_loaded': c.execute('SELECT count(*) FROM Agreement').fetchone()[0],
               'MADE_AT_join_rows': len(joins), 'original_positive_rows': len(positive),
               'repaired_positive_rows': len(repaired), 'frontier_original_rows': len(frontier),
               'frontier_repaired_rows': len(selected_frontier), 'cutoff_meeting_int': cutoff,
               'strictly_before_cutoff': sum(x['meetingNumberInt'] > cutoff for x in selected_frontier),
               'boundary_rows': sum(x['meetingNumberInt'] == cutoff for x in selected_frontier),
               'source_broad_frontier_IDs': sorted(x['resolutionId'] for x in broad_frontier),
               'frozen_original_frontier_IDs': sorted(x['resolutionId'] for x in frontier),
               'source_broad_vs_frozen_frontier_IDs_equal': {x['resolutionId'] for x in broad_frontier} == {x['resolutionId'] for x in frontier},
               'unbound_all_ten_reports_literal_positive_count': len(unbound),
               'remaining': ['Substantive answer content and §8 contentWithEquations authority need original-source semantic review.',
                             '13 and 9 raw OMML objects in two mandatory source TP tables require actual retained-alternative and necessity checks.',
                             'Generic numbered-proposal boundary has a preserved own-adopted-proposal false-cut control; no global extractor correctness claimed.',
                             'No independent SQL implementation or native query execution is claimed by this first probe.'],
               'native_gold_created': False, 'nonblind_AI': True, 'human_expert_n': 0,
               'API_native_public_central_actions': 0, 'original560_pass_increment': 0}
    for name, data in [('original_question.json', original), ('all_original_positive_rows.json', positive),
                       ('all_prospectively_repaired_positive_rows.json', repaired), ('generic_boundary_changes.json', changes),
                       ('all_possible_prefix_full_source_packets.json', packets), ('unbound_literal_positive_windows.json', unbound),
                       ('actual_generic_controls.json', controls), ('receipt.json', receipt)]:
        (out / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    (out / 'readonly_original_projection.sql').write_text(query + ';\n')
    print(json.dumps({k: v for k, v in receipt.items() if k not in ['remaining', 'original_query', 'benchmark', 'criteria']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
