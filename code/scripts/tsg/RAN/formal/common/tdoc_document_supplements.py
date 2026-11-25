#!/usr/bin/env python3
"""tdoc_document_supplements.py — validate native document identity supplements.

Spec: Phase-1 source identity/count contract; Phase-6 Word source coverage.
Ontology: Tdoc, CR-family and LS identities retain their original document kinds.
Cycle: native cover/cell/history evidence + complete report entry → exact source node.
배경: work plans, liaison outputs and text proposals can follow a list snapshot.
사용: validate_document(root, row); document_instance(row, references, resolve).
LLM 호출: none. Retained local bytes and explicit report decisions only.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re


def document_class(kind):
    """Use the maintained Phase-1 classification, including unnumbered pCRs."""
    return 'CR' if kind in {'CR', 'draftCR', 'pCR'} else 'LS' if kind in {'LS out', 'LS in'} else 'Tdoc'


def _has_document_id(text, target):
    return bool(re.search(r'(?<![\w-])' + re.escape(target) + r'(?![\w-])', text, re.I))


@lru_cache(maxsize=96)
def _native_blocks(path_string, sha):
    """Read real OOXML text with native locators; never use shared-string indices."""
    path = Path(path_string)
    if path.suffix.lower() in {'.docx', '.docm'}:
        from decision_disposition import source_blocks
        texts, actual, _ = source_blocks(str(path.resolve()))
        if actual != sha:
            raise ValueError('Accepted Word view differs from its source SHA')
        return {f'word/document.xml accepted body blocks [{i},{i + 1})': text
                for i, text in enumerate(texts)}
    if path.suffix.lower() == '.pptx':
        from pptx import Presentation
        result = {}
        for i, slide in enumerate(Presentation(path).slides, 1):
            paragraphs = []
            for shape in slide.shapes:
                if shape.has_text_frame:
                    paragraphs.extend(p.text for p in shape.text_frame.paragraphs)
                if shape.has_table:
                    paragraphs.extend(' | '.join(c.text for c in row.cells) for row in shape.table.rows)
            result[f'presentation slide {i}'] = '\n'.join(paragraphs)
        return result
    if path.suffix.lower() == '.xlsx':
        from openpyxl import load_workbook
        book = load_workbook(path, read_only=True, data_only=False)
        try:
            return {f'workbook sheet {sheet.title!r} cell {cell.coordinate}': str(cell.value)
                    for sheet in book for row in sheet for cell in row if cell.value is not None}
        finally:
            book.close()
    raise ValueError('A checked native view is required for this source format: ' + path.suffix)


def native_blocks(root, row):
    from tdoc_source_supplements import checked_path
    original = checked_path(root, row['path'], row['sha256'])
    view = row.get('nativeView')
    if view:
        lineage = view['conversionLineage']
        if (lineage['sourcePath'] != row['path'] or lineage['sourceSha256'] != row['sha256']
                or lineage['derivedPath'] != view['path'] or lineage['derivedSha256'] != view['sha256']
                or not lineage.get('tool') or not lineage.get('version') or not lineage.get('method')):
            raise ValueError('Native view is missing its original-to-derived conversion lineage')
    path, sha = (checked_path(root, view['path'], view['sha256']), view['sha256']) if view else (original, row['sha256'])
    return _native_blocks(str(path.resolve()), sha)


def own_cr_metadata(blocks):
    """Read descriptor cells from an accepted CR form, including text proposals."""
    text = '\n'.join(list(blocks.values())[:12])
    spec = re.search(r'\|\s*(\d{2}\.\d{3}(?:-\d+)?)\s*\|\s*CR\s*\|', text)
    release = re.search(r'Release:\s*\|\s*(Rel-\d+)\b', text)
    category = re.search(r'Category:\s*\|\s*([A-F])\b', text)
    work_item = re.search(r'Work item code:\s*\|\s*([^|\n]+)', text)
    return {key: match[1].strip() for key, match in [('specNumber', spec), ('release', release),
            ('category', category), ('workItem', work_item)] if match}


@lru_cache(maxsize=96)
def _report_events(root_string, path, meeting, sha):
    from document_decision_source import document_decisions
    return document_decisions({'docx_path': path, 'meeting_id': meeting}, Path(root_string))[0]


def validate_document(root, row):
    """Assert own identity and the named decision target independently."""
    from tdoc_source_supplements import SupplementError, checked_path, normalized, canonical_meeting
    from decision_disposition import source_blocks
    from document_decision_source import classify_document_decision
    target, identity, report = row['target'], row['sourceIdentity'], row['report']
    for item in row['meetingSourceFiles']:
        checked_path(root, item['path'], item['sha256'])
    blocks = native_blocks(root, row)
    proof = row['nativeIdentity']
    quote = blocks.get(proof['locator'])
    if quote != proof['text'] or not _has_document_id(quote or '', target):
        raise SupplementError('Native document identity evidence changed: ' + target)
    method = proof['method']
    if method == 'own_cover':
        if not (proof['locator'] == 'word/document.xml accepted body blocks [0,1)' or proof['locator'] == 'presentation slide 1'):
            raise SupplementError('An own-cover proof must refer to the actual opening header')
    elif method == 'own_cover_cell':
        if not proof['locator'].startswith('workbook sheet ') or normalized(quote) != target:
            raise SupplementError('An own-cover cell must contain the exact document identity')
    elif method == 'latest_document_history_revision':
        revisions = [line for line in quote.splitlines() if re.match(r'^\|\s*V\d+(?:\.\d+)+\s*\|', line)]
        if 'Document history' not in quote or not revisions or not _has_document_id(revisions[-1], target):
            raise SupplementError('History evidence does not identify the current document revision')
    else:
        raise SupplementError('Unsupported native identity qualification')
    report_path = checked_path(root, report['path'], report['sourceSHA256'])
    texts, actual_sha, _ = source_blocks(str(report_path.resolve()))
    start, end = report['startBlock'], report['endBlockExclusive']
    if actual_sha != report['sourceSHA256'] or '\n'.join(texts[start:end]) != report['quote']:
        raise SupplementError('Complete source report entry changed')
    events = _report_events(str(root.resolve()), report['path'], report['meeting'], actual_sha)
    matches = [e for e in events if e['decision_id'] == report['decisionId']]
    if len(matches) != 1:
        raise SupplementError('A source supplement needs one actual report decision')
    event = matches[0]
    code, _, _ = classify_document_decision(event, target)
    field = event['document_entry']
    if (event['body_blocks'] != [start, end] or event['content'] != report['quote']
            or target not in event['referenced_tdocs'] or code != report['sourceDocumentDisposition']
            or field['documentType'] != report['documentType']
            or canonical_meeting(event['meeting_id']) != identity['canonicalMeetingNumber']):
        raise SupplementError('Source decision and recovered identity disagree: ' + target)
    kind = field['documentType'] if field['documentType'] != 'legacy_type_unspecified' else 'other'
    if (identity['tdocNumber'] != target or identity['type'] != kind
            or row['canonicalClass'] != document_class(kind)):
        raise SupplementError('Source document class/type differs from Phase-1 classification')
    if row.get('ownCRMetadata', {}) != (own_cr_metadata(blocks) if row['canonicalClass'] == 'CR' else {}):
        raise SupplementError('Source-owned CR-family metadata changed')
    # The source header owns the entry title; an approved-as output has the same
    # checked entry provenance, while its named identity is proved independently.
    from document_decision_source import HEADER
    title = HEADER.match(field['headerText'])['title'].strip()
    if identity['title'] != title:
        raise SupplementError('Source title differs from the checked report entry')
    for_value = re.search(r'(?m)^\s*Type:[^\n]*?\bFor:\s*([^\n\t]+)', report['quote'])
    if identity.get('for') != (for_value[1].strip() if for_value else None):
        raise SupplementError('Document purpose lacks exact report-field support')
    return row


def document_instance(row, references, resolve):
    """Materialize proven document fields, without inventing numbered CR metadata."""
    from tdoc_source_supplements import canonical_meeting, normalized, SupplementError
    identity = row['sourceIdentity']
    names = {n['tdoc:meetingNumber']: n['@id'] for n in references['meetings']}
    matches = [value for name, value in names.items()
               if canonical_meeting(name) == identity['canonicalMeetingNumber']]
    if len(matches) != 1:
        raise SupplementError('Supplement meeting is missing or ambiguous')
    node = {'@id': 'tdoc:' + row['target'], '@type': 'tdoc:' + row['canonicalClass'],
            'tdoc:tdocNumber': row['target'], 'tdoc:title': identity['title'],
            'tdoc:type': identity['type'], 'tdoc:status': row['report']['sourceDocumentDisposition'].replace('_', ' '),
            'presentedAt': matches[0]}
    if identity.get('for'):
        node['tdoc:for'] = identity['for']
    if row['canonicalClass'] == 'LS':
        node['tdoc:direction'] = identity['type'].split()[-1]
    metadata = row.get('ownCRMetadata', {})
    if metadata.get('specNumber'):
        node['modifies'] = resolve('specs', 'tdoc:specNumber', metadata['specNumber'])
    if metadata.get('release'):
        node['targetRelease'] = resolve('releases', 'tdoc:releaseName', metadata['release'])
    if metadata.get('category'):
        node['tdoc:crCategory'] = metadata['category']
    if metadata.get('workItem'):
        matches = [n['@id'] for n in references['work_items'] if n.get('tdoc:workItemCode') == metadata['workItem']]
        if len(matches) == 1:
            node['relatedTo'] = matches
    # An exact existing submitter is optional. The complete literal source stays
    # in the checked report proof when it is a group of rapporteurs or companies.
    source = re.search(r'(?m)^\s*Source:\s*(.+)$', row['report']['quote'])
    if source:
        value = normalized(source[1]).casefold()
        companies = [n['@id'] for n in references['companies'] if value in {
            normalized(v).casefold() for v in [n.get('tdoc:companyName', '')] + n.get('tdoc:aliases', [])}]
        if len(companies) == 1:
            node['submittedBy'] = companies
    return node
