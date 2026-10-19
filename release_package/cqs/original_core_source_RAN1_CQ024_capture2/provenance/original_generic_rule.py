#!/usr/bin/env python3
"""Read-only generic capture-reference extension over every latest report window.

The rule uses no question, spec number, resolution ID or selected answer. It is
a conservative additive extension for explicit final-CR/capture paragraphs, not
a full reconstruction of every REFERENCES relation or every ownership boundary.
An earlier unclaimed TDoc header makes ownership unknown; it does not prove that
the later contribution is technically unrelated. Existing facts are retained.
"""
import collections
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sqlite3
import xml.etree.ElementTree as ET
import zipfile

OUT = Path(__file__).resolve().parent
OUR = OUT.parent
SRC = OUR / 'loop114_RAN1_ten_report_generic_source_text_and_DMRS_tie_proposal_NOT_ADMITTED/evidence'
DB = OUR.parents[3] / 'relational/RAN1.sqlite'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'
TDOC = re.compile(r'R1-\d{7}(?!\d)')
HEADER = re.compile(r'^\s*R1-\d{7}(?!\d)')
FINAL_INTRO = re.compile(r'^(?:The\s+)?(?:final\s+CRs?\b|draft\s+CR\b.*?\bfinal\s+CR\b)', re.I)
CAPTURE_INTRO = re.compile(r'^The agreement above is captured in:\s*$', re.I)
STATUS = re.compile(r'^\s*\(Rel[^\n]*(?:agreed|endorsed)\b', re.I)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pin(path):
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': sha(data)}


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def read_jsonl_gzip(path):
    with gzip.open(path, 'rt') as f:
        return [json.loads(line) for line in f]


def candidate_blocks(blocks):
    """Identify explicit capture syntax and conservatively guard its ownership.

    A TDoc paragraph is claimed only when it follows a formal capture colon in
    the same uninterrupted capture block. A preceding unclaimed TDoc paragraph
    causes later capture candidates to be held. This is conservative abstention,
    not a global definition of where all Agreement bodies end.
    """
    found, claimed = [], set()
    for i, block in enumerate(blocks):
        text = block['text'].strip()
        if block['kind'] != 'p' or not (FINAL_INTRO.match(text) or CAPTURE_INTRO.fullmatch(text)):
            continue
        # Require a positive recorded statement or a capture-list introducer.
        if not (CAPTURE_INTRO.fullmatch(text) or re.search(r'\b(?:agreed|endorsed)\b', text, re.I) or text.endswith(':')):
            continue
        indices = [i]
        if text.endswith(':'):
            for j in range(i + 1, len(blocks)):
                nxt = blocks[j]
                t = nxt['text'].strip()
                if nxt['kind'] != 'p' or not t:
                    break
                if HEADER.match(t) or STATUS.match(t):
                    indices.append(j)
                else:
                    break
        references = sorted({m.group() for j in indices for m in TDOC.finditer(blocks[j]['text'])})
        if not references:
            continue
        previous_unclaimed_headers = [j for j in range(i) if blocks[j]['kind'] == 'p' and HEADER.match(blocks[j]['text']) and j not in claimed]
        status = 'held_prior_unclaimed_TDoc_header' if previous_unclaimed_headers else 'accepted_explicit_capture_prefix'
        found.append({'intro_offset': i, 'capture_offsets': indices, 'tdoc_ids': references,
                      'status': status, 'prior_unclaimed_header_offsets': previous_unclaimed_headers})
        if status == 'accepted_explicit_capture_prefix':
            claimed.update(indices)
    return found


def controls():
    p = lambda text: {'kind': 'p', 'text': text}
    t = lambda text: {'kind': 'tbl', 'text': text}
    cases = []
    def check(name, blocks, expected):
        actual = candidate_blocks(blocks)
        value = [(c['status'], c['tdoc_ids']) for c in actual]
        cases.append({'name': name, 'actual': value, 'expected': expected, 'pass': value == expected})
    good = 'accepted_explicit_capture_prefix'
    held = 'held_prior_unclaimed_TDoc_header'
    check('generic_capture_mirror_pair', [p('Agreement'), p('Final CRs capturing the above TPs are in:'), p('R1-2000001 CR title'), p('(Rel-18, 38.000) is agreed.'), p('R1-2000002 mirror'), p('(Rel-19, 38.000) is agreed.')], [(good, ['R1-2000001', 'R1-2000002'])])
    check('blank_ends_before_unclaimed_header', [p('The agreement above is captured in:'), p('R1-2000001 own'), p(''), p('R1-2000002 later')], [(good, ['R1-2000001'])])
    check('earlier_unclaimed_header_holds_ownership', [p('Agreement'), p('R1-2000002 separately listed'), p('Final CR is agreed in:'), p('R1-2000001 title')], [(held, ['R1-2000001'])])
    check('technical_reason_sentence_is_not_intro', [p('Reason for change: the Final CR used an older parameter R1-2000001.')], [])
    check('table_text_is_not_intro', [t('Final CR is agreed in R1-2000001.')], [])
    check('unaffirmed_proposal_is_not_asserted', [p('Final CR R1-2000001 may be proposed after further study.')], [])
    check('strict_seven_digit_identity', [p('Final CR R1-20000010 is agreed.')], [])
    check('duplicate_reference_in_one_capture_is_idempotent', [p('Final CR R1-2000001 is endorsed in R1-2000001.')], [(good, ['R1-2000001'])])
    check('claimed_capture_headers_do_not_break_next_capture', [p('Final CR is in:'), p('R1-2000001 title'), p('(Rel-18, 38.000) is agreed.'), p('Final CR R1-2000002 is endorsed.')], [(good, ['R1-2000001']), (good, ['R1-2000002'])])
    assert all(x['pass'] for x in cases)
    return cases


def main():
    geometry = {x['resolutionId']: x for x in read_jsonl_gzip(SRC / 'identity_and_source_geometry.jsonl.gz')}
    patch = {x['resolutionId']: x['sourceRecordWindowText'] for x in read_jsonl_gzip(SRC / 'generic_property_patch.jsonl.gz')}
    reader_path = SRC / 'raw_word_formatting_reader.py'
    spec = importlib.util.spec_from_file_location('independent_word_run_reader', reader_path)
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    reader.FFS = re.compile(r'R1-\d{7}(?!\d)|final\s+CRs?|agreement above is captured', re.I)
    source_receipts, raw_bodies, paragraph_audits = [], {}, {}
    for label in ['123', '122b', '122']:
        path = OUR / f'loop102_RAN1_DMRS_original_prefix_source_reused_identity_and_checkpoints/source_{label}.docx'
        data = path.read_bytes()
        with zipfile.ZipFile(path) as z:
            xml, styles = z.read('word/document.xml'), z.read('word/styles.xml')
        assert xml == gzip.open(SRC / f'RAN1_{label}_document.xml.gz', 'rb').read()
        assert styles == gzip.open(SRC / f'RAN1_{label}_styles.xml.gz', 'rb').read()
        raw = list(ET.fromstring(xml).find(W + 'body'))
        audited = reader.audit_document(data)
        top = [(i, b) for i, b in enumerate(raw) if b.tag in (W + 'p', W + 'tbl')]
        assert len(top) == len(audited['blocks'])
        assert all(ET.tostring(b) == ET.tostring(audited['blocks'][j]) for j, (_, b) in enumerate(top))
        filtered_to_raw = {j: i for j, (i, _) in enumerate(top)}
        audits = collections.defaultdict(list)
        for paragraph in audited['paragraphs']:
            audits[filtered_to_raw[paragraph['body_block_index']]].append({k: v for k, v in paragraph.items() if k != 'element'})
        raw_bodies[label], paragraph_audits[label] = raw, audits
        source_receipts.append({'report': label, 'DOCX': pin(path), 'document_xml_sha256': sha(xml), 'styles_xml_sha256': sha(styles),
                                'coordinate_system': 'zero-based all w:body child ordinal; end exclusive'})

    assert DB.is_file(), DB
    db = sqlite3.connect(f'file:{DB}?mode=ro&immutable=1', uri=True)
    db.execute('PRAGMA query_only=ON')
    db.row_factory = sqlite3.Row
    tdocs = collections.defaultdict(list)
    for row in db.execute('SELECT node_id,tdocNumber FROM Tdoc'):
        tdocs[row['tdocNumber']].append(row['node_id'])
    captured, scope, delta = [], [], []
    for rid in sorted(geometry):
        label = rid.split('-')[1]
        if label not in raw_bodies:
            continue
        g = geometry[rid]
        lo, hi = g['source_record_raw_body_child_range']
        elements = raw_bodies[label][lo:hi]
        blocks = [{'kind': e.tag.rsplit('}', 1)[-1], 'text': ''.join(n.text or '' for n in e.iter() if n.tag in (W + 't', M + 't'))} for e in elements]
        assert '\n'.join(b['text'] for b in blocks) == patch[rid], rid
        srcs = db.execute('SELECT node_id FROM Agreement WHERE resolutionId=?', (rid,)).fetchall()
        assert len(srcs) == 1, rid
        src_id = srcs[0]['node_id']
        existing = {r[0] for r in db.execute('SELECT dst_id FROM rel_REFERENCES WHERE src_id=?', (src_id,))}
        found = candidate_blocks(blocks)
        scope.append({'resolutionId': rid, 'src_id': src_id, 'source_DOCX_sha256': g['source_DOCX_sha256'],
                      'raw_body_child_range': [lo, hi], 'raw_window_sha256': sha(patch[rid].encode()),
                      'existing_reference_count': len(existing), 'capture_candidate_count': len(found)})
        for capture in found:
            c = dict(capture, resolutionId=rid, src_id=src_id, source_DOCX_sha256=g['source_DOCX_sha256'],
                     source_raw_range=[lo, hi], intro_raw_body_child=lo + capture['intro_offset'])
            c['full_source_window_text'] = patch[rid]
            c['capture_blocks'] = []
            all_active = True
            for offset in capture['capture_offsets']:
                absolute = lo + offset
                paragraphs = paragraph_audits[label][absolute]
                occurrences = [o for p in paragraphs for o in p['occurrences']]
                active = all(o['active_formatting_status'] == 'all_active' for o in occurrences)
                all_active = all_active and active
                c['capture_blocks'].append(dict(blocks[offset], raw_body_child=absolute,
                    XML_sha256=sha(ET.tostring(elements[offset])), formatting_occurrences=occurrences,
                    all_relevant_markers_active=active))
            c['all_capture_markers_active'] = all_active
            if not all_active:
                c['status'] = 'held_removed_or_mixed_formatting'
            c['matched_existing_Tdoc_nodes'], c['missing_Tdoc_ids'] = [], []
            for tid in capture['tdoc_ids']:
                if not tdocs[tid]:
                    c['missing_Tdoc_ids'].append(tid)
                for dst in tdocs[tid]:
                    link = {'tdocNumber': tid, 'dst_id': dst, 'already_exists': dst in existing}
                    c['matched_existing_Tdoc_nodes'].append(link)
                    if c['status'] == 'accepted_explicit_capture_prefix' and dst not in existing:
                        delta.append({'src_id': src_id, 'dst_id': dst, 'resolutionId': rid, 'tdocNumber': tid,
                                      'source_DOCX_sha256': g['source_DOCX_sha256'],
                                      'intro_raw_body_child': c['intro_raw_body_child']})
            captured.append(c)
    accepted = [c for c in captured if c['status'] == 'accepted_explicit_capture_prefix']
    held = [c for c in captured if c['status'] != 'accepted_explicit_capture_prefix']
    # Derive an additive set; no existing edge can be removed or duplicated.
    unique_delta = {(e['src_id'], e['dst_id']): e for e in delta}
    delta = [unique_delta[k] for k in sorted(unique_delta)]
    checks = controls()
    # Missing targets are never synthesized, independently of parser candidates.
    missing_test_ids = ['R1-0000000']
    checks.append({'name': 'missing_TDoc_does_not_create_a_node_or_edge', 'pass': not [d for t in missing_test_ids for d in tdocs.get(t, [])],
                   'scope': 'strict existing-node lookup only; no INSERT or graph writer exists in this script'})
    assert all(c['pass'] for c in checks)
    for name, data in [('all869_scope_ledger.jsonl', scope), ('all_capture_candidates_full_source_and_formatting.jsonl', captured), ('generic_derived_additive_reference_edges.jsonl', delta)]:
        (OUT / name).write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in data))
    dump('generic_capture_rule_controls.json', checks)
    counted = {'windows': len(scope), 'windows_by_report': dict(collections.Counter(x['resolutionId'].split('-')[1] for x in scope)),
               'all_existing_references_preserved': sum(s['existing_reference_count'] for s in scope),
               'capture_candidate_blocks': len(captured), 'accepted_capture_blocks': len(accepted), 'held_capture_blocks': len(held),
               'accepted_existing_Tdoc_links': sum(len(c['matched_existing_Tdoc_nodes']) for c in accepted),
               'accepted_already_existing_links': sum(x['already_exists'] for c in accepted for x in c['matched_existing_Tdoc_nodes']),
               'new_unique_generic_reference_edges': len(delta),
               'held_links': sum(len(c['matched_existing_Tdoc_nodes']) for c in held),
               'unknown_or_missing_Tdoc_ids': sum(len(c['missing_Tdoc_ids']) for c in captured),
               'all_relevant_markers_active_for_accepted': all(c['all_capture_markers_active'] for c in accepted),
               'controls_passed': sum(c['pass'] for c in checks)}
    receipt = {'status': 'PROSPECTIVE_GENERIC_ADDITIVE_SOURCE_DELTA_NOT_ADMITTED', 'counts': counted,
               'sources': source_receipts, 'source_SQL_readonly': pin(DB), 'generic_rule_code': pin(Path(__file__)),
               'formatting_reader': pin(reader_path), 'new_edges': delta,
               'held_candidates': [{k: c[k] for k in ['resolutionId', 'intro_raw_body_child', 'status', 'prior_unclaimed_header_offsets', 'matched_existing_Tdoc_nodes']} for c in held],
               'scope': 'Every one of869 stable loaded Agreement windows in latest3 reports. Only explicit formal capture/final-CR syntax is an additive repair class; no total REFERENCES rebuild is claimed.',
               'limits': ['The earlier unclaimed TDoc-header guard means ownership is unproved; it is not proof of a technically unrelated contribution.',
                          'Original references are all retained, including previously documented foreign spillover outside the requested prefix.',
                          'All source windows reproduce raw XML; only the accepted capture spans receive this own-role/active-marker judgment.',
                          'Existing target nodes are resolved by literal TDoc ID; the rule creates no TDoc, CR, Spec, or status claim.',
                          'CR requested-target mapping does not establish new approval, TS incorporation, or causal credit.',
                          'Prospective CQ024 semantics/calendar correction require independent review and whole-snapshot/equal-input/native gates before any API or admission.'],
               'native_calls': 0, 'API_calls': 0, 'central_changes': 0, 'public_changes': 0, 'expert_validation_n': 0}
    dump('actual_generic_capture_delta_receipt.json', receipt)
    print(json.dumps({'status': receipt['status'], 'counts': counted, 'receipt': pin(OUT / 'actual_generic_capture_delta_receipt.json')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
