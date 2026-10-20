"""Bounded final-report condition-deletion witness plus whole frozen scalar search."""
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
ROOT = next(p for p in HERE.parents if (p/'CLAUDE.md').exists())
TASK = ROOT/'logs/pending-tasks/spectracq-core-contract-2026-10-13'
OLD = TASK/'empirical/overnight_reaudit/root_evidence/two_agent_unresolved_loop/RAN1_RAN3_RAN4'
SRC = OLD/'loop114_RAN1_ten_report_generic_source_text_and_DMRS_tie_proposal_NOT_ADMITTED/evidence'
DB = TASK/'empirical/relational/RAN1.sqlite'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
TARGETS = {
    'AGR-121-9.11.3-007': (4485, 'The above agreement applies to PUCCH with repetitions'),
    'AGR-121-9.11.3-008': (4489, 'The above agreement applies to different priority indexes for PUCCH/PUSCH'),
}
PHRASE = 'if no additional specification impact is identified'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pin(p):
    b = p.read_bytes()
    return {'path': str(p.resolve()), 'sha256': sha(b), 'bytes': len(b)}


def norm(x):
    return re.sub(r'\s+', ' ', x).strip().casefold()


def strings(v, path='$'):
    if isinstance(v, str):
        yield path, v
    elif isinstance(v, dict):
        for k, x in v.items():
            yield from strings(x, path+'.'+k)
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from strings(x, path+f'[{i}]')


def truth(el):
    return el is not None and el.get(W+'val', 'true').casefold() not in ('0', 'false', 'off', 'no')


def main():
    out = HERE/'actual_deleted_condition_alternatives_v1'
    out.mkdir(exist_ok=False)
    xml = gzip.decompress((SRC/'RAN1_121_document.xml.gz').read_bytes())
    body = list(ET.fromstring(xml).find(W+'body'))
    c = sqlite3.connect(DB.resolve().as_uri()+'?mode=ro&immutable=1', uri=True)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA query_only=ON')
    scalar_hits = []
    scanned = 0
    for row in c.execute('SELECT * FROM _node_record ORDER BY node_id'):
        scanned += 1
        props = json.loads(row['properties_json'])
        matched = []
        for field, value in strings(props):
            n = norm(value)
            keys = [rid for rid, (_, stem) in TARGETS.items() if norm(stem) in n]
            if keys or norm(PHRASE) in n:
                matched.append({'field': field, 'literal': value, 'matched_identity_stems': keys,
                                'contains_condition': norm(PHRASE) in n})
        if matched:
            scalar_hits.append({'node_id': row['node_id'], 'source_iri': row['source_iri'],
                                'labels': json.loads(row['labels_json']), 'matches': matched,
                                'resolutionId': props.get('resolutionId'),
                                'own_meetings': [dict(x) for x in c.execute('SELECT m.* FROM edge e JOIN Meeting m ON m.node_id=e.dst_id WHERE e.src_id=? AND e.rel_type="MADE_AT"', (row['node_id'],))]})
    observations = []
    for rid, (coord, stem) in TARGETS.items():
        f = dict(c.execute('SELECT * FROM Agreement WHERE resolutionId=?', (rid,)).fetchone())
        para = body[coord]
        text = ''.join(x.text or '' for x in para.iter(W+'t'))
        runs = []
        for i, r in enumerate(para.iter(W+'r')):
            value = ''.join(x.text or '' for x in r.iter(W+'t'))
            strike = truth(r.find(W+'rPr/'+W+'strike')) or truth(r.find(W+'rPr/'+W+'dstrike'))
            runs.append({'run0': i, 'literal': value, 'direct_strike': strike,
                         'XML': ET.tostring(r, encoding='unicode')})
        struck = ''.join(x['literal'] for x in runs if x['direct_strike'])
        active = ''.join(x['literal'] for x in runs if not x['direct_strike'])
        if norm(struck) != norm(PHRASE):
            raise AssertionError(('unexpected strike extent', rid, struck))
        if norm(PHRASE) not in norm(f['content']) or f['contentWithEquations'] is not None or f['note'] is not None:
            raise AssertionError(('unexpected retained representation', rid))
        if norm(stem) not in norm(active) or norm(PHRASE) in norm(active):
            raise AssertionError(('unexpected active wording', rid))
        node = dict(c.execute('SELECT * FROM _node_record WHERE node_id=?', (f['node_id'],)).fetchone())
        edges = [dict(x) for x in c.execute('SELECT * FROM edge WHERE src_id=? OR dst_id=?', (f['node_id'], f['node_id']))]
        observations.append({'resolutionId': rid, 'raw_body_child0': coord,
                             'original_paragraph_XML': ET.tostring(para, encoding='unicode'),
                             'literal_with_retained_markup_removed': text, 'direct_struck_phrase': struck,
                             'direct_active_text': active, 'runs': runs, 'frozen_Agreement': f,
                             'frozen_node_record': node, 'all_incident_edges': edges,
                             'neighboring_source_blocks': [{'raw_body_child0': i,
                                 'literal': ''.join(z.text or '' for z in body[i].iter(W+'t')),
                                 'XML': ET.tostring(body[i], encoding='unicode')}
                                for i in range(coord-2, coord+2)]})
    # A source-only counterfactual proves the plain-text serializer is non-injective.
    # This does not assert that every source markup choice is a valid final decision.
    counterfactuals = []
    for o in observations:
        original = ET.fromstring(o['original_paragraph_XML'])
        altered = ET.fromstring(o['original_paragraph_XML'])
        removed = 0
        for r in altered.iter(W+'r'):
            rp = r.find(W+'rPr')
            if rp is not None:
                for mark in list(rp):
                    if mark.tag in (W+'strike', W+'dstrike'):
                        rp.remove(mark)
                        removed += 1
        literal = lambda p: ''.join(x.text or '' for x in p.iter(W+'t'))
        if removed != 1 or literal(original) != literal(altered):
            raise AssertionError('counterfactual serialization')
        counterfactuals.append({'resolutionId': o['resolutionId'], 'removed_direct_strike_markers': removed,
                                'original_and_no_strike_word_text_equal': True,
                                'source_actual_active_text': o['direct_active_text'],
                                'counterfactual_not_actual_no_strike_active_text': literal(altered),
                                'scope': 'Source serializer information-loss control, not a second actual source version.'})
    repaired = json.loads((HERE/'actual_retained_proposal_boundary_v1/all_prospectively_repaired_positive_rows.json').read_text())
    current = [x for x in repaired if x['meetingNumberInt']>=121]
    if len(current) != 10 or not set(TARGETS)<= {x['resolutionId'] for x in current}:
        raise AssertionError('cutoff binding')
    receipt = {'status': 'ACTUAL_SOURCE_EXPLICIT_CONDITION_DELETION_AND_RETAINED_ALTERNATIVES_PROBE',
               'id': 'RAN1_P2_CQ5-10', 'utc': datetime.now(timezone.utc).isoformat(),
               'source_member': {'path': 'word/document.xml', 'bytes': len(xml), 'sha256': sha(xml)},
               'source_gzip': pin(SRC/'RAN1_121_document.xml.gz'),
               'whole_frozen_nodes_scanned': scanned, 'matched_alternate_nodes': len(scalar_hits),
               'target_exact_stem_hits': {rid: sorted({x['node_id'] for x in scalar_hits for y in x['matches'] if rid in y['matched_identity_stems']}) for rid in TARGETS},
               'source_deletion_witnesses': list(TARGETS),
               'corrected_latest10_contains_both_witnesses': True,
               'original_6above_plus_any4of5_boundary_includes_at_least_one_witness': True,
               'mathematical_reason': 'Two witness IDs are among five tied candidates. Any four of five contains at least one; removing the foreign mandatory candidate requires all five ties.',
               'claims_not_made': ['No automatic entire-question unsupported or final classification.',
                   'No new active-only policy is declared; original answer roles and the explicit revised-text source must be independently interpreted.',
                   'No absence of every semantically paraphrased alternate follows from exact-stem search alone.',
                   'No source-enriched graph or native query was run.'],
               'next_test': 'Read all alternate matches and all same-event retained properties to check whether a deletion/amendment link or unconditioned same-event adopted statement is recoverable without source-only flags.',
               'API_native_public_central_actions': 0, 'human_expert_n': 0, 'nonblind_AI': True, 'original560_pass_increment': 0}
    for name, value in [('two_actual_source_deletion_witnesses.json', observations),
                        ('all_frozen_scalar_alternative_matches.json', scalar_hits),
                        ('source_plain_text_information_loss_controls.json', counterfactuals),
                        ('receipt.json', receipt)]:
        (out/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
