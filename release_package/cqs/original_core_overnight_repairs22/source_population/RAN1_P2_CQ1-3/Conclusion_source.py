"""Re-derive Conclusion IDs from report TOC/headings and direct raw body labels.

Broad windows are evidence containers, not certified complete adopted content.
Coordinates are raw w:body child ordinals, including non-p/tbl children.
"""
import collections
import hashlib
import re
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'


def literal(el):
    return ''.join((e.text or '') if e.tag == W+'t' else '\t' if e.tag == W+'tab'
                   else '\n' if e.tag in (W+'br', W+'cr') else '' for e in el.iter())


def audit_conclusions(data, marker_reader):
    old_pattern = marker_reader.FFS
    marker_reader.FFS = re.compile(r'\bConclusion\b', re.I)
    try:
        audit = marker_reader.audit_document(data)
    finally:
        marker_reader.FFS = old_pattern
    body = ET.fromstring(audit['xml']).find(W+'body')
    source_paragraphs = list(body.iter(W+'p'))
    assert len(source_paragraphs) == len(audit['paragraphs'])
    p_audit = {id(p): a for p, a in zip(source_paragraphs, audit['paragraphs'])}
    blocks = []
    toc = collections.defaultdict(set)
    for i, element in enumerate(body):
        style_node = element.find(W+'pPr/'+W+'pStyle')
        style = style_node.get(W+'val', '') if style_node is not None else ''
        text = literal(element)
        if style.startswith('TOC'):
            parts = [x.strip() for x in text.split('\t') if x.strip()]
            if len(parts) >= 3 and re.fullmatch(r'\d+(?:\.\d+)*', parts[0]):
                toc[re.sub(r'\s+', ' ', parts[1]).strip()].add(parts[0])
        blocks.append({'raw_body_child_ordinal': i, 'style': style,
                       'literal': text, 'element': element})
    counts = collections.Counter()
    agenda = heading = None
    annex = False
    markers, candidates = [], []
    decision = re.compile(r'^(Agreement|Conclusion|Working\s+Assumption)(?:\b|\s*[:：])', re.I)
    own = re.compile(r'^Conclusion(?:\s*[:：].*)?$', re.I | re.S)
    for block in blocks:
        text = block['literal'].strip()
        if block['style'].startswith('Heading'):
            if text.startswith('Annex '):
                annex = True
            choices = toc.get(re.sub(r'\s+', ' ', text).strip(), set())
            if len(choices) == 1:
                agenda = next(iter(choices))
            heading = {'raw_body_child_ordinal': block['raw_body_child_ordinal'],
                       'literal': text, 'TOC_number_candidates': sorted(choices), 'agenda': agenda}
        if block['element'].tag != W+'p' or block['style'].startswith('TOC') or annex:
            continue
        if re.match(r'^Conclusions?\b', text, re.I):
            candidates.append({'raw_body_child_ordinal': block['raw_body_child_ordinal'],
                               'literal': text, 'strict_own_pattern': bool(own.fullmatch(text))})
        if not own.fullmatch(text):
            continue
        counts[agenda] += 1
        start = block['raw_body_child_ordinal']
        end = next((x['raw_body_child_ordinal'] for x in blocks[start+1:]
                    if x['style'].startswith('Heading') or
                    (x['element'].tag == W+'p' and decision.match(x['literal'].strip()))), len(blocks))
        span = blocks[start:end]
        token = [o for o in p_audit[id(block['element'])]['occurrences']
                 if o['start'] <= len(block['literal'])-len(block['literal'].lstrip())+1]
        assert len(token) == 1
        status = token[0]['active_formatting_status']
        markers.append({'resolutionId': f'CON-121-{agenda}-{counts[agenda]:03d}',
                        'sequence': counts[agenda], 'heading': heading,
                        'raw_body_child_range': [start, end], 'source_own_label_literal': text,
                        'label_formatting_status': status, 'label_active': status == 'all_active',
                        'explicit_withdrawal_literal': bool(re.search(r'following is deleted', text, re.I)),
                        'full_broad_window_literal': '\n'.join(x['literal'] for x in span),
                        'full_broad_window_XML': [ET.tostring(x['element'], encoding='unicode') for x in span],
                        'broad_window_limitation': 'Stops at next direct decision or heading. Following Tdoc/Friday lines can be present; this is not a full-content ownership claim.',
                        'OMML_count': sum(len(x['element'].findall('.//'+M+'oMath')) for x in span),
                        'source_next_boundary_literal': blocks[end]['literal'] if end < len(blocks) else None})
    return {'records': markers, 'candidates': candidates,
            'document_XML_sha256': hashlib.sha256(audit['xml']).hexdigest(),
            'styles_XML_sha256': hashlib.sha256(audit['styles_xml']).hexdigest()}
