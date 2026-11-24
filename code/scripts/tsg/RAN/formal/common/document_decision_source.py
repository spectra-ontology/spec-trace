#!/usr/bin/env python3
"""document_decision_source.py — 회의록 문서 entry의 명시적 처분 사건을 복구한다.

Spec: docs/tsg/build/standards/decision_disposition_contract.md.
Ontology: an explicit document Decision is a Resolution; its target disposition is qualified.
Cycle: accepted DOCX header/Type/Decision → deterministic source event → shared loader.
배경: 기술 Agreement/Conclusion 표지와 문서별 Decision은 서로 다른 회의 사건이다.
사용: document_decisions(report); document_resolution_node(event).
LLM 호출: 없음. 원문 구조와 명시 술어만 사용하고 미지원 문맥을 보존한다.
"""
from __future__ import annotations

from bisect import bisect_right
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import re

HEADER = re.compile(r'^\s*(?P<id>[A-Z][A-Z0-9]{0,2}[-–]\d{6,8})\s+(?P<title>[^\n]+)(?P<tail>.*)', re.S)
TYPE = re.compile(r'^\s*Type\s*:\s*([^\t\n]+)', re.I)
DECISION = re.compile(r'^\s*Decision\s*:\s*(.*)', re.I | re.S)
CR_DESCRIPTOR = re.compile(r'(?m)^\s*\d{2,3}\.\d{3}(?:-\d+)?[^\n]*\bCR\s*[-#]?\s*\d+', re.I)
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
_EVENT_CACHE = {}
_ANNEX_CACHE = {}
LIST_LINE_TYPE = 'list_line_type_unspecified'
LIST_LINE_METHOD = 'list_line_title_matches_tdoc_list'
FORMAL_DOCUMENT_FIELD = re.compile(r'^\s*Decision\s*:\s*(?:The\s+document\b|(?:Agreed|Approved|Endorsed|Noted|Withdrawn|Rejected|Postponed|Deferred|Revised|Not\s+agreed|Not\s+pursued)\b)', re.I)
# A list-line entry may state its disposition without the `Decision:` label: the line opens
# with `=>`, with an e-mail discussion tag `[NNN]`, or with the status word itself.
LIST_STATUS = re.compile(
    r'^\s*(?:=>\s*|\[\d{3}\]\s*)?(?P<field>(?:The\s+(?:CR|document)\s+(?:is|was)\s+)?'
    r'(?:Agreed|Approved|Endorsed|Noted|Withdrawn|Rejected|Postponed|Deferred|Revised|Merged'
    r'|Not\s+agreed|Not\s+pursued|Not\s+treated)\b.*)', re.I | re.S)
STATUS_MARKER = re.compile(r'^\s*(?:=>|\[\d{3}\])')
STATUS_SUBJECT = re.compile(r'^The\s+(?P<kind>CR|document)\s+(?:is|was)\s+', re.I)


def decision_field(text, list_line=False):
    """Return the disposition field of a paragraph, or None when it is not one.

    `Decision: ...` is a field in every entry. A label-less status line is a field
    only in a list-line entry. A status line that ends with a colon captions the
    lines after it (`Withdrawn contributions:`) and is not a field.
    """
    if (match := DECISION.match(text)):
        return match[1]
    if list_line and (match := LIST_STATUS.match(text)) and not text.rstrip().endswith(':'):
        return match['field']
    return None


def _title_key(text):
    return ' '.join(text.split()).casefold()


def _list_titles(report, root):
    """Phase-1 titles of this WG's documents, used only to recognise a list line."""
    from document_decision_storage import _tdoc_index, prop
    wg = report['meeting_id'].split('#')[0]
    path = root / f'ontology/output/tsg/RAN/formal/instances/phase-1/{wg}/tdocs.jsonld'
    if not path.exists():
        return {}, None
    stat = path.stat()
    index, sha = _tdoc_index(str(path), stat.st_mtime_ns, stat.st_size)
    return {number: (_title_key(title), prop(node, 'crNumber'),
                     str(prop(node, 'modifies') or '').split('/')[-1].replace('_', '.'))
            for number, node in index.items() if number and (title := prop(node, 'title'))}, sha


def document_decisions(report, root=None):
    """Read explicit entry structure; never infer decisions from a status spreadsheet.

    Every checked header, including another WG/plenary's document, is a boundary.
    A short title continuation may precede Type. Multiple Decision paragraphs in
    one entry remain separate source events with an explicitly unresolved scope.

    A header without Type or Source fields is also checked when it is a list line:
    the line starts with this WG's document number and continues with that
    document's complete Phase-1 title. The TDoc list identifies the line only; the
    decision is still the explicit Decision paragraph of the report. Such an entry
    ends at the next line that starts with a document number, checked or not.
    A listed line inside an entry with Type or Source metadata that has not yet
    reached its own Decision paragraph is quoted text and starts no entry.
    """
    import decision_disposition as d
    root = root or d.ROOT
    texts, sha, blocks = d.source_blocks(str((root / report['docx_path']).resolve()))
    list_titles, list_sha = _list_titles(report, root)
    cache_key = (str(root), report['docx_path'], report['meeting_id'], sha, list_sha, hashlib.sha256(json.dumps({
        'decisions': [(decision['decision_id'], decision.get('body_blocks'))
                      for group in ('agreements', 'conclusions', 'working_assumptions') for decision in report.get(group, [])],
        'sections': report.get('sections', [])}, sort_keys=True).encode()).hexdigest())
    if cache_key in _EVENT_CACHE:
        return _EVENT_CACHE[cache_key]
    covered = {i for group in ('agreements', 'conclusions', 'working_assumptions')
               for decision in report.get(group, [])
               for i in range(*decision.get('body_blocks', [0, 0]))}
    starts = [section['start_index'] for section in report.get('sections', [])]
    sections = report.get('sections', [])
    para = -1
    agenda_at = []
    candidate_headers = []
    heading_boundaries = set()
    for index, block in enumerate(blocks):
        if block.tag == W + 'p':
            para += 1
        si = bisect_right(starts, para) - 1
        agenda_at.append(sections[si]['agenda_number'] if si >= 0 and para < sections[si]['end_index'] else 'UNKNOWN')
        style = block.find(f'{W}pPr/{W}pStyle')
        name = style.get(W + 'val', '').lower() if style is not None else ''
        if name.startswith(('heading', 'title')) or block.find(f'{W}pPr/{W}outlineLvl') is not None:
            heading_boundaries.add(index)
        match = HEADER.match(texts[index])
        if match:
            candidate_headers.append((index, match))
    headers = []
    for start, header in candidate_headers:
        type_block, metadata = None, None
        for index in range(start + 1, min(start + 5, len(blocks))):
            if HEADER.match(texts[index]) or DECISION.match(texts[index]) or index in heading_boundaries:
                break
            if (match := TYPE.match(texts[index])):
                type_block, metadata = index, match[1].strip()
                break
        type_method = 'explicit_Type_metadata'
        if metadata is None and re.search(r'\bSource\s*:', header['tail'], re.I):
            metadata = 'CR' if CR_DESCRIPTOR.search(header['tail']) else 'legacy_type_unspecified'
            type_method = 'explicit_CR_descriptor' if metadata == 'CR' else 'explicit_Source_header'
        if metadata is None:
            listed = list_titles.get(header['id'].replace('–', '-'))
            # An entry that carries Type or Source metadata stays open until its own
            # Decision paragraph or the next heading. A listed line inside it is text
            # the entry quotes (for example a CR list in an Abstract), not a new entry.
            inside_open_entry = bool(headers) and headers[-1][4] != LIST_LINE_METHOD and not any(
                index in heading_boundaries or DECISION.match(texts[index])
                for index in range(headers[-1][0] + 1, start))
            if listed and not inside_open_entry and _title_key(header['title']).startswith(listed[0]):
                metadata, type_method = LIST_LINE_TYPE, LIST_LINE_METHOD
        if metadata is not None:
            headers.append((start, header, type_block, metadata, type_method))
    candidate_starts = [start for start, _ in candidate_headers]
    events = []
    stats = Counter(reports=1, checkedHeaders=len(headers))
    bound_types = set()
    for offset, (start, header, type_block, metadata, type_method) in enumerate(headers):
        boundary = headers[offset + 1][0] if offset + 1 < len(headers) else len(blocks)
        boundary = min((i for i in heading_boundaries if start < i < boundary), default=boundary)
        if type_method == LIST_LINE_METHOD:
            following = bisect_right(candidate_starts, start)
            if following < len(candidate_starts):
                boundary = min(boundary, candidate_starts[following])
            stats['listLineHeaders'] += 1
        if type_block is not None:
            bound_types.add(type_block)
        stats['checkedDocumentEntries'] += 1
        target = header['id'].replace('–', '-')
        list_line = type_method == LIST_LINE_METHOD
        decision_indices = [i for i in range(start + 1, boundary) if decision_field(texts[i], list_line) is not None]
        document_decision_count = sum(bool(FORMAL_DOCUMENT_FIELD.match(texts[i]) or not DECISION.match(texts[i]))
                                      for i in decision_indices)
        stats['listStatusLines'] += sum(not DECISION.match(texts[i]) for i in decision_indices)
        stats['entriesWithMultipleDecisions'] += len(decision_indices) > 1
        stats['entriesWithoutDecision'] += not decision_indices
        # Cross-WG documents are boundaries, but this WG's target model uses its
        # own R1..R5 document identities; no incoming/plenary target is invented.
        if not re.fullmatch(r'R[1-5]-\d{6,8}', target):
            stats['externalDocumentDecisionParagraphs'] += len(decision_indices)
            continue
        for index in decision_indices:
            if index in covered:
                stats['alreadyRepresentedDecisionParagraphs'] += 1
                continue
            rid = f'DOC-{report["meeting_id"].split("#", 1)[1]}-{target}-b{index}'
            events.append({'decision_id': rid, 'decision_type': 'document_disposition',
                'meeting_id': report['meeting_id'], 'agenda_item': agenda_at[index],
                'content': '\n'.join(texts[start:index + 1]), 'body_blocks': [start, index + 1],
                'sequence': index, 'referenced_tdocs': list(dict.fromkeys([target] + approval_outputs(texts[index]))), 'subject_tdoc': target,
                'document_entry': {'headerBlock': start, 'decisionBlock': index,
                    'sourcePath': report['docx_path'],
                    'entryBoundaryEnd': boundary, 'typeBlock': type_block,
                    'documentType': metadata, 'typeEvidenceMethod': type_method,
                    'headerText': texts[start], 'decisionText': texts[index],
                    'multipleDecisionParagraphs': len(decision_indices) > 1,
                    'formalDocumentDecisionParagraphs': document_decision_count}})
            if not DECISION.match(texts[index]):
                # Whether only other disposition fields stand between the header line and this line.
                events[-1]['document_entry']['statusLineFollowsHeader'] = all(
                    i in decision_indices for i in range(start + 1, index))
                events[-1]['document_entry']['emptyParagraphBeforeStatusLine'] = any(
                    not texts[i].strip() for i in range(start + 1, index))
            if type_method == LIST_LINE_METHOD and list_titles[target][1] and list_titles[target][2]:
                # The header document's own CR identity in the TDoc list. A decision that
                # names a CR by specification and number is compared with it.
                events[-1]['document_entry']['listedCR'] = {
                    'crNumber': str(list_titles[target][1]), 'spec': list_titles[target][2]}
            stats['sourceDecisionEvents'] += 1
            stats['explicitCREvents'] += metadata.lower().replace(' ', '') in {'cr', 'draftcr'}
    stats['headerDecisionEvents'] = stats['sourceDecisionEvents']
    stats['headerExplicitCREvents'] = stats['explicitCREvents']
    annex_events, annex_stats = annex_cr_table_events(report, root)
    events.extend(annex_events)
    stats['sourceDecisionEvents'] = len(events)
    stats['explicitCREvents'] += len(annex_events)
    annex_unbound = annex_stats.pop('annexUnboundRows', None)
    stats.update(annex_stats)
    type_indices = {i for i in range(len(texts)) if TYPE.match(texts[i])}
    result = events, {**dict(stats), 'unboundTypeMetadataBlocks': sorted(type_indices - bound_types),
                     'sourcePath': report['docx_path'], 'sourceSha256': sha}
    if annex_unbound is not None:
        result[1]['annexUnboundRows'] = annex_unbound
    _EVENT_CACHE[cache_key] = result
    return result


ANNEX_CR_HEADING = re.compile(
    r'^Annex\s+[A-Za-z0-9]+\s*:\s*List\s+of\s+agreed\s+CRs'
    r'(?:\s+for\s+RAN\s*#\s*\d+|\s+and\s+in\s+principle\s+agreed\s+draftCRs\s+of\s+RAN2\s*#\s*\S+)?$', re.I)
# RAN1 states the disposition and the meeting in the annex title itself.
ANNEX_CR_HEADING_RAN1 = re.compile(
    r'^Annex\s+[A-Za-z0-9-]+\s*:\s*List\s+of\s+(?:draft\s+)?CRs\s+(?P<kind>agreed|endorsed)\s+at\s+'
    r'RAN1\s*#\s*\d+\s*(?:-?bis|b)?(?:-e)?$', re.I)
# A paragraph between two RAN1 annex tables introduces the table that follows it.
RAN1_LEAD_IN_ENDORSED = re.compile(r'^(?:Endorsed\s+(?:\S+\s+)?CRs(?:/draftCRs)?|The\s+following\s+CRs\s+are\s+endorsed\.?)$', re.I)
RAN1_LEAD_IN_AGREED = re.compile(r'^The\s+following\s+CRs\s+\(although\s+agreed\)\s', re.I)
ANNEX_SCOPE_LABEL = re.compile(
    r'^(?:List\s+of\s+)?(?P<kind>in\s+principle\s+agreed\s+draftCRs|'
    r'agreed\s+CRs|(?:technically\s+)?endorsed\s+CRs)\s*:?$', re.I)
# Header cells observed in the reports of each WG. A table whose header names a
# column outside these sets, or names one field twice, yields no row event.
ANNEX_COLUMN_NAMES = {
    'RAN2': {'spec': {'spec'}, 'title': {'title'}, 'crNumber': {'cr', 'cr#', 'cr #'},
             'crRevision': {'rev'}, 'release': {'rel', 'release'}, 'wgStatus': {'ran2 status'}},
    'RAN1': {'target': {'td#', 'tdoc #', 'tdoc'}, 'spec': {'ts', 'ts/tr', 'tr', 'spec', 'spec #'},
             'title': {'title'}, 'crNumber': {'cr', 'cr #'},
             'crRevision': {'rev', 'cr rev', 'cr revision #'}, 'release': {'rel', 'release'},
             'wgStatus': {'tdoc status'}},
}


def _annex_columns(header, wg='RAN2'):
    """The observed source schemas of this WG name the target and WG status columns."""
    values = [' '.join(c.split()).casefold() for c in header]
    columns = {}
    aliases = ANNEX_COLUMN_NAMES[wg]
    for index, value in enumerate(values):
        if wg == 'RAN2' and (value in {'tdoc', 'ran2 tdoc'} or re.fullmatch(r'ran2\s*#\S+\s+tdoc', value)):
            if 'target' in columns: return None
            columns['target'] = index
        for key, names in aliases.items():
            if value in names:
                if key in columns: return None
                columns[key] = index
    return columns if {'target', 'title', 'spec', 'crNumber', 'crRevision', 'release'} <= columns.keys() else None


def _annex_source_tables(path, sha, texts, blocks, wg='RAN2'):
    """Keep local table scopes; a following endorsed/in-principle list is separate."""
    import docx_text
    cache_key = (str(path), sha, wg)
    if cache_key in _ANNEX_CACHE:
        return _ANNEX_CACHE[cache_key]
    records = {}
    heading = None
    before = []
    label = None
    for index, block in enumerate(blocks):
        if block.tag == W + 'p':
            text = texts[index]
            normalized = ' '.join(text.split())
            if re.match(r'^Annex\s+[A-Za-z0-9-]+\s*:', normalized, re.I):
                own = ANNEX_CR_HEADING_RAN1.fullmatch(normalized) if wg == 'RAN1' else None
                heading = index if own or (wg == 'RAN2' and ANNEX_CR_HEADING.fullmatch(normalized)) else None
                before = []
                label = (own['kind'].casefold() if own else
                         'ambiguous' if 'in principle' in normalized.casefold() else 'agreed', index, text)
            if heading is None:
                continue
            if match := ANNEX_SCOPE_LABEL.fullmatch(normalized):
                kind = match['kind'].casefold()
                label = ('in_principle' if kind.startswith('in principle') else
                         'endorsed' if 'endorsed' in kind else 'agreed', index, text)
                before = []
            if normalized:
                before.append({'block': index, 'text': text})
            continue
        if heading is None or block.tag != W + 'tbl':
            continue
        rows = docx_text.table_rows(block, para=docx_text.final_text)
        if not rows or (columns := _annex_columns(rows[0], wg)) is None:
            continue
        after = []
        for following in range(index + 1, len(blocks)):
            if wg == 'RAN1' or blocks[following].tag == W + 'tbl': break
            text = texts[following]
            normalized = ' '.join(text.split())
            # RAN1 numbers its annexes with a hyphen (`Annex C-1:`); the next annex title ends this table's context.
            next_annex = r'^Annex\s+[\w-]+\s*:' if wg == 'RAN1' else r'^Annex\s+\w+\s*:'
            if re.match(next_annex, normalized, re.I) or ANNEX_SCOPE_LABEL.fullmatch(normalized): break
            if normalized: after.append({'block': following, 'text': text})
        context = [{'block': heading, 'text': texts[heading]}]
        context += [p for p in before if p['block'] != heading]
        context += after
        context = sorted({p['block']: p for p in context}.values(), key=lambda p: p['block'])
        kind, label_block, label_text = label
        lead_in = [p for p in before if p['block'] != heading] if wg == 'RAN1' else []
        if lead_in:
            # The lead-in states this table's own scope; an unobserved wording leaves it open.
            line = ' '.join(lead_in[-1]['text'].split())
            kind = ('ambiguous' if len(lead_in) > 1 else 'endorsed' if RAN1_LEAD_IN_ENDORSED.fullmatch(line)
                    else kind if RAN1_LEAD_IN_AGREED.match(line) else 'ambiguous')
            label_block, label_text = lead_in[-1]['block'], lead_in[-1]['text']
        # The literal observed footer overrides the short list title. Do not
        # propagate the next list's qualifier back into a preceding agreed list.
        if any(re.search(r'\bagreed\s+' + IN_PRINCIPLE_WORD, p['text'], re.I) for p in after):
            kind = 'in_principle'
        records[index] = dict(headingBlock=heading, headingText=texts[heading],
            tableBlock=index, headerRow=0, headerCells=rows[0], columns=columns,
            governingContext=context, tableScope=kind,
            scopeLabel={'block': label_block, 'text': label_text}, rows=rows)
        before = []
    # Retain only compact table projections, not the complete parsed DOCX trees.
    _ANNEX_CACHE[cache_key] = records
    return records


def _annex_event(report, path, sha, record, row_index, row):
    columns = record['columns']
    if len(row) != len(record['headerCells']): return None
    cell = row[columns['target']].strip()
    wg = report['meeting_id'].split('#')[0]
    if not re.fullmatch(wg.replace('RAN', 'R') + r'-\d{6,8}', cell): return None
    raw = {field: row[columns[field]] for field in ('title', 'spec', 'crNumber', 'crRevision', 'release')}
    source = dict(raw)
    for field in ('crNumber', 'crRevision'):
        value = raw[field].strip()
        source[field] = value if value.isdigit() else None
    spec = raw['spec'].strip()
    source['spec'] = spec if re.fullmatch(r'\d{2,3}\.\d{3}(?:-\d+)?', spec) else None
    release = raw['release'].strip()
    match = re.fullmatch(r'Rel\s*[-_]\s*(\d+)', release, re.I)
    source['release'] = 'Rel-' + match[1] if match else None
    status = dict(kind='explicit_table_scope', value=record['tableScope'])
    if record['tableScope'] == 'in_principle':
        status['kind'] = 'in_principle_table_scope'
    elif 'wgStatus' in columns:
        col = columns['wgStatus']
        status = dict(kind='explicit_WG_status_cell', column=col, value=row[col])
    table = copy.deepcopy({k: v for k, v in record.items() if k != 'rows'})
    table.update(acceptedRow=row_index, rowCells=list(row), targetColumn=columns['target'],
                 sourceSha256=sha, statusSource=status)
    header_quote = '| ' + ' | '.join(record['headerCells']) + ' |'
    row_quote = '| ' + ' | '.join(row) + ' |'
    before = [p['text'] for p in record['governingContext'] if p['block'] < record['tableBlock']]
    after = [p['text'] for p in record['governingContext'] if p['block'] > record['tableBlock']]
    content = '\n'.join(before + [header_quote, row_quote] + after)
    span = [min([record['tableBlock']] + [p['block'] for p in record['governingContext']]),
            max([record['tableBlock']] + [p['block'] for p in record['governingContext']]) + 1]
    rid = f'DOC-{report["meeting_id"].split("#",1)[1]}-{cell}-t{record["tableBlock"]}-r{row_index}'
    return dict(decision_id=rid, decision_type='document_disposition', meeting_id=report['meeting_id'],
        agenda_item='UNKNOWN', content=content, body_blocks=span, sequence=record['tableBlock'],
        referenced_tdocs=[cell], subject_tdoc=cell, document_entry=dict(sourceKind='annex_cr_table_row',
            sourcePath=str(path), documentType='CR', sourceFields=source, sourceFieldRaw=raw,
            decisionText=row_quote, annexTable=table))


def annex_cr_table_events(report, root=None):
    """Recover the explicit row identities of a WG's agreed-CR annex without transferring TSG status."""
    wg = report['meeting_id'].split('#')[0]
    if wg not in ANNEX_COLUMN_NAMES:
        return [], {}
    import decision_disposition as d
    root = root or d.ROOT
    path = root / report['docx_path']
    texts, sha, blocks = d.source_blocks(str(path.resolve()))
    records = _annex_source_tables(path, sha, texts, blocks, wg)
    events, unbound = [], []
    for record in records.values():
        for index, row in enumerate(record['rows'][1:], 1):
            event = _annex_event(report, report['docx_path'], sha, record, index, row)
            if event is None:
                unbound.append({'tableBlock': record['tableBlock'], 'acceptedRow': index,
                                'rowCells': list(row), 'reason': 'no_single_explicit_target_in_WG_tdoc_column'})
            else:
                events.append(event)
    return events, dict(annexSourceTables=len(records), annexSourceRowEvents=len(events),
                        annexUnboundRows=unbound)


def annex_source_evidence(event, root=None):
    """Independently rebind this precise accepted row, its header and governing text."""
    import decision_disposition as d
    root = root or d.ROOT
    field = event['document_entry']
    if field.get('sourceKind') != 'annex_cr_table_row':
        raise ValueError('An explicit Annex row source is required')
    path = (root / field['sourcePath']).resolve()
    path.relative_to(root.resolve())
    actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    texts, cached_sha, blocks = d.source_blocks(str(path))
    table = field['annexTable']
    if actual_sha != cached_sha or actual_sha != table['sourceSha256']:
        raise ValueError('Annex source bytes changed')
    record = _annex_source_tables(path, actual_sha, texts, blocks, event['meeting_id'].split('#')[0]).get(table['tableBlock'])
    if record is None or not (1 <= table['acceptedRow'] < len(record['rows'])):
        raise ValueError('Annex row locator is not a checked source row')
    expected = _annex_event({'meeting_id': event['meeting_id']}, field['sourcePath'], actual_sha,
                            record, table['acceptedRow'], record['rows'][table['acceptedRow']])
    if expected is None or any(event.get(k) != expected[k] for k in expected):
        raise ValueError('Annex row, header, governing scope, identity or source fields changed')
    if hashlib.sha256(path.read_bytes()).hexdigest() != actual_sha:
        raise ValueError('Annex source generation changed during row verification')
    start, end = event['body_blocks']
    return dict(path=str(path.relative_to(root.resolve())), sha256=actual_sha,
        locator=f'word/document.xml accepted table block {table["tableBlock"]} row {table["acceptedRow"]}; governing body blocks [{start},{end})',
        quote=event['content'], decisionText=field['decisionText'], subjectChecked=True)


# An approval that names the document it produced (`agreed in R2-y`, `approved as R5-y`)
# may carry qualifiers between the approval verb and the output number. The reports use a
# closed set of them: the in-principle reading, `unseen`, the change applied to produce the
# output (`with these changes`, `without change #2`), the output CR's own descriptor
# (`as CR0778 to 36.213 (Rel-14)`, `in a new CR 1432 rev6`, `as v0.6.0`), and any of these
# in parentheses. One grammar finds the output for the event's targets and reads the field,
# so a qualified approval and a direct one name their output the same way.
OUTPUT_NUMBER = r'R[1-5]-\d{6,8}'
# A change phrase ends before a nested approval, a coordinated outcome (`but then revised by
# MCC in`, `and merged in`), a colon or the output itself. `as in R2-x` compares with another
# document and is not an output, so the phrase never ends in `as`. `final version in R2-x`
# is the phrasing of `Agreed, final version in R2-x`, which this grammar does not read as an
# approval naming its output, so a change phrase does not run into it either.
_CHANGE_STOP = (r'(?!\b(?:as|in)\s+' + OUTPUT_NUMBER + r'\b|\b(?:agreed|approved|accepted|but|then)\b|\bfinal\s+version\b'
                r'|\band\s+(?:is\s+|was\s+)?(?:revised|merged|endorsed|noted|withdrawn|replaced|superseded)\b)')
_CHANGE_BODY = (r'(?:' + _CHANGE_STOP + r'(?:[^.;:\n()]|\.(?=\d)|\((?:(?!' + OUTPUT_NUMBER + r')[^()\n])*\)))+?'
                r'(?<![\s,])(?<!\bas)')
# The in-principle qualifier as the reports spell it, with the misspellings they contain
# (`in-principle`, `inprinciple`, `in princple`, `in principe`, `in principel`, `in principal`,
# `in priciple`). The statement classifier reads the same spellings.
IN_PRINCIPLE_WORD = r'in[\s-]*(?:principle|princple|principe|principel|principal|priciple)\b'
_IN_PRINCIPLE = r'-?' + IN_PRINCIPLE_WORD
_CR_DESCRIPTOR = (r'CR\s*#?\s*\d+(?:\s*r(?:ev\.?)?\s*\d+)?(?:\s+to\s+(?:TS\s*)?\d{2}\.\d{3}(?:-\d+)?)?'
                  r'(?:\s*\([^()\n]*\))?')
_OUTPUT_QUALIFIER = (
    r'(?:' + _IN_PRINCIPLE + r'|unseen\b|with(?:out)?\s+' + _CHANGE_BODY
    + r'|as\s+(?:rev(?:ision)?\s*\d+(?:\s+of\s+' + _CR_DESCRIPTOR + r')?|' + _CR_DESCRIPTOR + r')'
    + r'|as\s+v\d+\.\d+\.\d+|in\s+a\s+new\s+CR\s*#?\s*\d+(?:\s*r\d+|\s+rev\s*\d+)?'
    + r'|\(\s*(?:' + _IN_PRINCIPLE + r'|unseen|with(?:out)?\s+' + _CHANGE_BODY + r')\s*\))')
# The output follows `in`/`as`, or stands alone in the parenthesis that closes a change phrase
# (`Agreed with the above change (R2-y)`, `Agreed with the correction on the cover page (R2-y)`):
# the change produced that number, as `with the change above in R2-y` states it.
_APPROVAL_OUTPUT = (r'\b(?:agreed|approved|accepted)(?P<leading>(?:[\s,]*' + _OUTPUT_QUALIFIER + r')*)'
                    r'\s*,?\s*(?:(?:as|in)\s+|(?P<paren>\(\s*)(?=' + OUTPUT_NUMBER + r'\s*\)))'
                    r'(?P<output>' + OUTPUT_NUMBER + r')\b(?(paren)\s*\))')
APPROVAL_OUTPUT = re.compile(_APPROVAL_OUTPUT, re.I)
# The whole decision field: an optional document subject and revision, the approval with
# its leading qualifiers and output, and the remaining text that qualifies the output.
APPROVAL_OUTPUT_FIELD = re.compile(
    r'(?:The\s+document\s+(?:was|is)\s+)?(?:revised\s+and\s+)?(?:email\s+)?'
    + _APPROVAL_OUTPUT + r'(?P<trailing>.*)', re.I | re.S)
# A number after agreement with a proposal or view, or after a source participle
# (`the changes proposed in R2-x`), is the document the content came from.
CONCURRENCE_NOUN = re.compile(
    r'\b(?:proposals?|views?|suggestions?|understandings?|conclusions?|approach(?:es)?|observations?)\b', re.I)
SOURCE_PARTICIPLE = re.compile(
    r'\b(?:proposed|suggested|described|provided|shown|listed|contained|given|presented|discussed|captured|'
    r'indicated|explained|mentioned|raised|included|documented|specified|outlined)\s*,?\s*$', re.I)
IN_PRINCIPLE = re.compile(r'(?:^|[\s,(])' + _IN_PRINCIPLE, re.I)
# The text after the output qualifies it as the text before it does, so the word order of a
# qualifier does not change the reading. The output's own descriptor may follow the number
# (`in R2-y r1`, `in R2-y CR rev 2`, `in R1-y 36213CR0948r1`, `in R1-y 38.802 CR0003 Rel-14, F`,
# `in R1-y (TS36.213, Rel-15, CR1190)`, `in R1-y as Cat-F`), and a change phrase after it
# (`agreed in R2-y with the change above`) describes, as one before it does (`agreed with the
# change above in R2-y`), how the header became the output. A change phrase names a change; a
# condition (`assuming the following update`) or another relation (`with shadow CRs in R2-z`)
# is not one and is read as stated.
CHANGE_WORD = re.compile(r'\b(?:chang|updat|addi|add|modif|delet|correct|clarif|revis|remov|replac|edit|fix)\w*', re.I)
_STATUS_WORD = r'\b(?:agreed|approved|accepted|endorsed|noted|revised|merged|withdrawn|postponed|rejected|not)\b'
_TRAILING_CHANGE = (r'\(\s*with(?:out)?\s+[^()\n]*\)'
                    r'|with(?:out)?\s+(?:' + _CHANGE_STOP + r'(?:[^.;:\n()]|\.(?=\d)|\((?:(?!' + OUTPUT_NUMBER
                    + r')[^()\n])*\)))+')
_OUTPUT_DESCRIPTOR = (r'r\d+\b|CR\s*rev\.?\s*\d+\b|\d{5}(?:-\d+)?CR\d+(?:r\d+)?\b'
                      r'|CR\s*#?\s*\d+(?:\s*r(?:ev\.?)?\s*\d+)?(?:\s+to\s+(?:TS\s*)?\d{2}\.\d{3}(?:-\d+)?)?\b'
                      r'|\d{2}\.\d{3}(?:-\d+)?\s+CR\s*#?\s*\d+(?:r\d+)?(?:\s+Rel-\d+)?(?:\s*,\s*[A-F]\b)?'
                      r'|\((?:(?!' + OUTPUT_NUMBER + r'|' + _STATUS_WORD + r'|\bwith(?:out)?\b)[^()\n])*\)'
                      r'|as\s+Cat-?[A-F]\b')
TRAILING_QUALIFIER = re.compile(
    r'[\s,]*(?P<item>' + _IN_PRINCIPLE + r'|unseen\b|as\s+(?:rev(?:ision)?\s*\d+(?:\s+of\s+' + _CR_DESCRIPTOR + r')?|'
    + _CR_DESCRIPTOR + r')|as\s+v\d+\.\d+\.\d+|' + _OUTPUT_DESCRIPTOR + r'|(?P<change>' + _TRAILING_CHANGE + r'))', re.I)
# A change phrase after the output may name the document the change came from (`agreed in R1-y,
# with reflecting the change in R1-z`, as `with the changes from R1-z` does); that number
# belongs to the change, and the output is already named.
CHANGE_SOURCE = re.compile(r'\s*(?:in|as|from|of)\s+' + OUTPUT_NUMBER + r'\b', re.I)


def output_qualifiers_end(trailing):
    """Return where the output's own qualifiers end in the text after the output."""
    end = 0
    while (match := TRAILING_QUALIFIER.match(trailing, end)) and match.end() > end:
        if match['change'] and not CHANGE_WORD.search(match['change']):
            break
        end = match.end()
        if match['change'] and (source := CHANGE_SOURCE.match(trailing, end)):
            end = source.end()
    return end
# An agreement to put the paper's content into another document is not the paper's own whole
# unconditional approval (contract §15): the approved artifact is the receiving document, a
# rapporteur, running, mega or merged CR, a TR, TS, TP or baseline, or another numbered document.
# The reports state it as a purpose (`to be included in the running CR`, `to include TP in
# running CR`), as a coordinated outcome (`agreed and merged into R2-x`, `Agreed, merge with
# rapporteur CR`) or in parentheses (`Agreed (To be included in the baseline)`). A receiver
# phrase ends at a clause word, so a later clause is never read as the receiver. A negated
# incorporation (`not to be merged`) states none.
_INCORPORATED = r'(?:added|included|merged|captured|incorporated|reflected|folded|put|implemented|integrated)'
_INCORPORATE = r'(?:add|include|merge|capture|incorporate|reflect|fold|put|implement|integrate)'
_INTO = r'(?:in|into|to|with|within)'
_CLAUSE_WORD = r'(?:and|or|but|then|which|that|is|are|was|were|be|been|will|would|should|shall|can|may|not)'
_RECEIVER = (r'(?:(?:the|a|an)\s+)?(?:(?!' + _CLAUSE_WORD + r'\b)[\w.\'’/-]+\s+)*?'
             r'(?:CRs?|TPs?|text\s+proposals?|TR|TS|baseline|spec(?:ification)?s?)\b'
             r'|' + OUTPUT_NUMBER + r'\b')
INCORPORATION = re.compile(
    r'\bto\s+be\s+' + _INCORPORATED + r'\s+' + _INTO + r'\s+(?:' + _RECEIVER + r')'
    r'|\bto\s+' + _INCORPORATE + r'\b(?:(?!\b(?:and|or|but|then)\b)[^.;:\n()])*?\b' + _INTO + r'\s+(?:' + _RECEIVER + r')'
    r'|(?:^|[,;(]|\band\b)\s*(?:(?:the\s+)?(?:agreed\s+)?changes?\s+)?(?:(?:is|are|was|were)\s+)?'
    r'(?:' + _INCORPORATED + r'|' + _INCORPORATE + r')\s+' + _INTO + r'\s+(?:' + _RECEIVER + r')', re.I | re.M)
NEGATED = re.compile(r'\b(?:not|never)\s*$', re.I)
INCORPORATION_RULE = 'incorporation_agreement_requires_adjudication'


def incorporation(text):
    """Return the first incorporation of the paper's content into another document, or None."""
    for match in INCORPORATION.finditer(text):
        if not NEGATED.search(text, 0, match.start()):
            return match
    return None


# An approval whose object is the paper's text proposal (`Agreed TP and editor will reflect
# it`, `Agreed TPs for 36.211 and 36.300 (not 36.301)`) accepts the TP the paper carries, a
# part of the paper, not the whole paper (contract §9).
TP_OBJECT_APPROVAL = re.compile(
    r'(?:The\s+document\s+(?:was|is)\s+)?(?:agreed|approved|accepted)\s+(?:the\s+|all\s+)?(?:TPs?|text\s+proposals?)\b',
    re.I)
# An approval predicate whose object is a bare number other than the header (`Agreed
# R2-1702219`, `The CR is agreed R2-2313963 with the changes above`, `The CR is agreed in
# principle R2-1711860`) names no relation between the header and that number: neither `in`/`as`
# (the header became the output) nor a merge. The header's own disposition is then unresolved
# (contract §11), and the number is not an output.
BARE_NUMBER_APPROVAL = re.compile(
    r'\b(?:agreed|approved|accepted)\s*(?:' + _IN_PRINCIPLE + r'\s*)?[,:]?\s*(?:the\s+)?(?:(?:CR|LS|TP|document)\s+)?'
    r'(?P<number>' + OUTPUT_NUMBER + r')\b',
    re.I)


# The output's own clause may be one clause of a longer field (`The document is noted and
# agreed as CR0223 ... in R1-x`, `The draft LS is endorsed. Final LS is approved in R1-x`,
# `CR0751r1 ... is agreed in R1-x and CR0752r1 ... is agreed in R1-y`). Each output is read
# from its own clause alone (contract §46); the header keeps the reading of its own predicate.
# A clause opens the field, a sentence, a dated email or GTW decision preamble, or an `and`
# coordination; after a comma it needs its own subject and copula (`..., final LS is approved
# in R1-x`), since a bare `, agreed in R1-x` can continue a plan or an apposition. Its subject
# names the output document: a document kind (document, CR, LS, version, TP, revision) with its
# modifiers, recipients, title, CR descriptor or the number of the draft it came from, or a bare
# CR descriptor. The kinds and modifiers are the ones the accepted RAN1-RAN5 reports use for an
# approval clause naming an output.
_CLAUSE_PREAMBLE = (r'As\s+per\s+(?:email\s+|GTW\s+)?(?:decision\s+)?(?:posted\s+)?on\s+'
                    r'[A-Z][a-z]+\.?\s*\d{1,2}(?:st|nd|rd|th)?\s*,\s*')
_CLAUSE_BOUNDARY = r'(?:(?:^|[.;]\s+)(?:' + _CLAUSE_PREAMBLE + r')?|(?:[.;,]\s*|\s+)(?:and|&)\s+)'
_SUBJECT_MODIFIER = r'(?:final|finally|draft|reply|replay|jumbo|shadow|corresponding|updated|Rel-\d+)'
_SUBJECT_KIND = (r'(?:document|CRs?(?:\s*#?\s*\d+(?:\s*r(?:ev\.?)?\s*\d+)?)?|LS|version|TP|revision(?:\s+\d+\s+of\s+'
                 + _CR_DESCRIPTOR + r')?)')
_SUBJECT_TEXT = r'(?:(?!\b(?:is|are|was|were|be|been|agreed|approved|accepted|endorsed|noted|revised)\b)[^.;:\n])+?'
_SUBJECT_POST = (r'(?:\s*\([^()\n]*\)|\s+in\s+' + OUTPUT_NUMBER + r')*'
                 r'(?:\s+(?:response\s+)?(?:to|on|for)\s+' + _SUBJECT_TEXT + r')?')
_CLAUSE_SUBJECT = (r'(?:(?:the\s+)?(?:' + _SUBJECT_MODIFIER + r'\s+)*(?:' + _SUBJECT_KIND + r'|' + _CR_DESCRIPTOR
                   + r')' + _SUBJECT_POST + r'|(?:the\s+)?(?:final\s+)?\([^()\n]*\))')
APPROVAL_CLAUSE_LEAD = re.compile(
    r'(?:' + _CLAUSE_BOUNDARY + r'(?:' + _CLAUSE_SUBJECT + r'\s+(?:(?:is|are|was|were)\s+)?|(?:is|was)\s+)?'
    r'|,\s+' + _CLAUSE_SUBJECT + r'\s+(?:is|are|was|were)\s+)(?:finally\s+)?(?:email\s+)?\Z', re.I)
REVISED_AGAIN = re.compile(r'(?<!\bas\s)\brevised\b(?!\s+title)', re.I)
# A future, conditional or assumed approval in the clause's own sentence names no approval;
# text after the output qualifies it as it does a whole-field approval.
CLAUSE_MODALITY = re.compile(
    r'\b(?:will|would|should|could|can|may|shall|to\s+be|if|unless|once|provided\s+that|subject\s+to|'
    r'pending|assum(?:e|ed|ing))\b', re.I)


def _names_output(match):
    leading = match['leading']
    if match['paren'] and not (re.search(r'\bwith(?:out)?\b', leading, re.I) and CHANGE_WORD.search(leading)):
        # A parenthesized number names the output only after the change that produced it.
        return False
    return not CONCURRENCE_NOUN.search(leading) and not SOURCE_PARTICIPLE.search(leading)


def approval_outputs(text):
    return [match['output'].upper() for match in APPROVAL_OUTPUT.finditer(text) if _names_output(match)]


def approval_output_clause(text, output):
    """Return the approval clause that names `output` inside a longer field, or None."""
    if APPROVAL_OUTPUT_FIELD.fullmatch(text):
        return None
    clauses = [m for m in APPROVAL_OUTPUT.finditer(text) if _names_output(m)]
    leads = [APPROVAL_CLAUSE_LEAD.search(text, 0, m.start()) for m in clauses]
    # Each clause opens its own statement, or the field relates its clauses (`agreed as CR0216
    # in R1-x, then further agreed as rev1 in R1-y`) and no clause settles its output alone.
    mine = [i for i, m in enumerate(clauses) if m['output'].upper() == output.upper()]
    if not all(leads) or len(mine) != 1:
        return None
    i = mine[0]
    start, end = clauses[i].start(), leads[i + 1].start() if i + 1 < len(clauses) else len(text)
    sentence = max(m.end() for m in re.finditer(r'^|[.;](?=\s)', text[:start]))
    # A dated preamble (`As per email decision posted on May 20th,`) names a date, not a modality.
    preamble = re.compile(r'\s*' + _CLAUSE_PREAMBLE, re.I).match(text, sentence, start)
    if CLAUSE_MODALITY.search(text, preamble.end() if preamble else sentence, start):
        return None
    # Another mention of the output, by number or by its `x` short form, is another statement
    # about it (`... R1-x is considered withdrawn`, `The FFS parts in R1-x ...`). The clause
    # does not settle the output then.
    mention = re.compile(r'\b(?:' + re.escape(clauses[i]['output']) + r'|x' + clauses[i]['output'][-4:] + r')\b', re.I)
    if mention.search(text, 0, start) or mention.search(text, clauses[i].end('output')):
        return None
    # A clause that revises its approved output again (`approved in R1-x, further revised to
    # correct the WI code`, `revised post-meeting in R1-y`) gives the output two dispositions in
    # one field; the clause does not settle it.
    if REVISED_AGAIN.search(text, clauses[i].end('output'), end):
        return None
    return APPROVAL_OUTPUT_FIELD.fullmatch(text, start, end)


EMAIL_DECISION_PREFIX = re.compile(
    r'^As\s+per\s+(?:email\s+)?decision\s+(?:posted\s+)?on\s+[A-Z][a-z]+\.?\s*\d{1,2}(?:st|nd|rd|th)?\s*,\s*', re.I)
CR_TUPLE_AGREED = re.compile(r'(?:CR\s*)?\((?P<descriptor>[^()]+)\)\s+is\s+agreed\s*\.?', re.I)
CR_TO_SPEC_AGREED = re.compile(
    r'CR\s*#?\s*(?P<number>\d+)\s+to\s+(?:TS\s*)?(?P<spec>\d{2}\.\d{3}(?:-\d+)?)(?:\s*\([^()]*\))?\s+is\s+agreed\s*\.?', re.I)
# The subject of a decision sentence may carry a parenthetical descriptor of the paper
# (`The document (CR0246 to 36.211) is noted ...`); both compound readings accept it.
NOTED_SUBJECT = r'The\s+document(?:\s*\([^()]*\))?\s+(?:was|is)\s+noted'
NOTED_AND = re.compile(NOTED_SUBJECT + r'\s+and\s+(?P<rest>.+)', re.I | re.S)
NOTED_CR_AGREED = re.compile(
    r'(?:shadow\s+)?(?:Rel-\d+\s+)?CR\s*#?\s*(?P<number>\d+)(?:\s+cat\s+[A-F])?\s+to\s+(?:TS\s*)?(?:Rel-\d+\s+)?'
    r'(?P<spec>\d{2}\.\d{3}(?:-\d+)?)(?:\s*\([^()]*\)|\s+Rel-\d+)?\s+is\s+agreed\s*\.?', re.I)
NOTED_THEN = re.compile(NOTED_SUBJECT + r'\b(?P<rest>.*)', re.I | re.S)
SECOND_OUTCOME = re.compile(
    r'\b(?:agreed|approved|accepted|endorsed|revised|merged|withdrawn|postponed|rejected)\b', re.I)
CR_SPEC = re.compile(r'(?<![\d.])\d{2}\.\d{3}(?:-\d+)?(?![\d.])')
CR_NUMBER = re.compile(r'\bCR\s*#?\s*(\d+)(?P<revision>r\d+)?\b', re.I)


def named_cr_agreement(text):
    """Return (spec, CR number) when the whole field agrees exactly one named CR."""
    text = EMAIL_DECISION_PREFIX.sub('', text, count=1)
    if (match := CR_TO_SPEC_AGREED.fullmatch(text)):
        return match['spec'], int(match['number'])
    if (match := CR_TUPLE_AGREED.fullmatch(text)):
        specs = CR_SPEC.findall(match['descriptor'])
        numbers = list(CR_NUMBER.finditer(match['descriptor']))
        if len(specs) == 1 and len(numbers) == 1 and not numbers[0]['revision']:
            return specs[0], int(numbers[0][1])
    return None


def _checked_status_field(event, target, text, d):
    """Read a checked status field as a statement about its header document."""
    # A revision/output number inside a document field is retained in the quote,
    # never substituted for the checked header's target or independently approved.
    normalized = re.sub(r'^The\s+document\b', event['subject_tdoc'], text, flags=re.I)
    if not re.match(r'^The\s+document\b', text, re.I):
        normalized = event['subject_tdoc'] + ' is ' + text
    # Accepted reports use past email decisions, including the literal typo
    # "was for email approved". Normalize only this checked status field;
    # future tense, negation, conditions and subsequent text remain intact.
    normalized = re.sub(r'^(R[1-5]-\d{6,8}\s+(?:was|is)\s+)(?:for\s+)?email\s+'
                        r'(?=(?:agreed|approved|endorsed)\b)', r'\1', normalized, flags=re.I)
    normalized = re.sub(r'^(R[1-5]-\d{6,8}\s+was\s+)for\s+(?=revised\b)',
                        r'\1', normalized, flags=re.I)
    return d.classify_statement(normalized, target, subject=True, meeting_id=event['meeting_id'])


def _output_reading(event, match, d):
    """Classify the approval clause as a statement about its named output."""
    # A change phrase on either side of the number describes how the header became the
    # output; the output carries it already. An in-principle reading qualifies the approval
    # itself, so it is read on the output wherever it stands.
    output = match['output'].upper()
    end = output_qualifiers_end(match['trailing'])
    qualifiers, rest = match['trailing'][:end], match['trailing'][end:]
    principle = ' in principle' if IN_PRINCIPLE.search(match['leading']) or IN_PRINCIPLE.search(qualifiers) else ''
    code, _, _ = d.classify_statement(output + ' is approved' + principle + rest, output,
                                      meeting_id=event['meeting_id'])
    return code


def classify_document_decision(event, target=None):
    """The explicit Decision field governs its checked document header only."""
    import decision_disposition as d
    field = event['document_entry']
    target = target or event['subject_tdoc']
    if field.get('sourceKind') == 'annex_cr_table_row':
        if target != event['subject_tdoc']:
            return 'ambiguous', field['decisionText'], 'annex_row_does_not_dispose_other_target'
        status = field['annexTable']['statusSource']
        raw = ' '.join(status['value'].split()).casefold().rstrip('.')
        if status['kind'] == 'in_principle_table_scope':
            return 'ambiguous', field['decisionText'], 'annex_in_principle_requires_final_source'
        code = {'agreed': 'agreed', 'endorsed': 'endorsed'}.get(raw, 'ambiguous')
        return code, field['decisionText'], 'checked_annex_row:' + status['kind']
    if field['formalDocumentDecisionParagraphs'] > 1:
        return 'ambiguous', field['decisionText'], 'multiple_document_decisions_require_adjudication'
    labelled = DECISION.match(field['decisionText']) is not None
    text = decision_field(field['decisionText'], field.get('typeEvidenceMethod') == LIST_LINE_METHOD).strip()
    if not labelled:
        # A label-less status line reads as the header document's status field. `The CR`
        # names the header document only when the TDoc list registers it as a CR.
        subject = STATUS_SUBJECT.match(text)
        if subject and subject['kind'].lower() == 'cr' and 'listedCR' not in field:
            return 'ambiguous', text, 'CR_subject_on_header_not_listed_as_CR'
        bare = not subject and not STATUS_MARKER.match(field['decisionText'])
        if bare and field['emptyParagraphBeforeStatusLine']:
            # An empty paragraph closes the entry; a bare status word after it speaks for
            # the group of documents listed above, with no document named.
            return 'ambiguous', text, 'bare_status_line_detached_by_empty_paragraph'
        if bare and not field['statusLineFollowsHeader'] and 'listedCR' not in field:
            # A bare status word after discussion text in a non-CR entry can close a
            # proposal of that discussion instead of the header document.
            return 'ambiguous', text, 'bare_status_line_after_discussion_in_non_CR_entry'
        stated = 'The document was ' + text[subject.end() if subject else 0:]
        code, _, rule = classify_document_decision(
            {**event, 'document_entry': {**field, 'decisionText': 'Decision: ' + stated}}, target)
        return code, text, rule
    # These observed formal status fields describe this checked document only.
    # Full matching retains future, conditional, historical and other-meeting
    # qualifiers as unresolved, and never transfers a merge/reply to its output.
    if target == event['subject_tdoc']:
        if re.fullmatch(r'The\s+document\s+was\s+withdrrawn\s*\.?', text, re.I):
            return 'withdrawn', text, 'explicit_formal_document_observed_withdrawn_typo'
        status = re.fullmatch(
            r'The\s+document\s+(?:was|is)\s+'
            r'(?P<status>not\s+treated|merged|not\s+concluded|replied\s+to)'
            r'(?:\s+(?:to|in)\s+R[1-5]-\d{6,8})?\s*\.?', text, re.I)
        if status:
            code = re.sub(r'\s+', '_', status['status'].lower())
            return code, text, 'explicit_formal_document_status_field'
        if re.fullmatch(r'The\s+document\s+(?:was|is)\s+technically\s+endorsed\s*\.?', text, re.I):
            return 'endorsed', text, 'explicit_formal_document_technical_endorsement'
        if re.fullmatch(r'The\s+document\s+(?:was|is)\s+partially[\s-]+(?:approved|agreed)\s*\.?', text, re.I):
            return 'partially_agreed', text, 'explicit_formal_document_partial_approval'
    # A technical discussion that happens to follow an entry is not the entry's
    # whole-document disposition. Recognize the formal document subject or the
    # report's terse status-field grammar, and retain every other field pending.
    # An output named by one approval clause of a longer field is read from that clause,
    # whatever the field says about the header.
    clause = approval_output_clause(text, target) if target != event['subject_tdoc'] else None
    if clause is not None:
        code = _output_reading(event, clause, d)
        if code == 'agreed' and incorporation(clause['trailing']):
            return 'ambiguous', text, INCORPORATION_RULE
        return code, text, 'explicit_document_revision_output_clause_approval'
    formal = re.match(r'^(?:The\s+document\b|(?:Agreed|Approved|Endorsed|Noted|Withdrawn|Rejected|Postponed|Deferred|Revised|Not\s+agreed|Not\s+pursued)\b)', text, re.I)
    if not formal:
        # A list-line entry of a CR may state its approval by naming the CR. The
        # field counts only when the named specification and CR number are the
        # header document's own; a revision-qualified or different CR stays pending.
        named = named_cr_agreement(text) if 'listedCR' in field else None
        if named and target == event['subject_tdoc']:
            listed = field['listedCR']
            if (listed['crNumber'].isdigit() and int(listed['crNumber'])
                    and (listed['spec'], int(listed['crNumber'])) == named):
                return 'agreed', text, 'explicit_own_CR_descriptor_agreement'
            return 'ambiguous', text, 'named_CR_differs_from_header_document'
        return 'ambiguous', text, 'unsupported_document_decision_field'
    # `The document is noted and CR<n> to <spec> is agreed` on a list-line entry of a CR
    # states two things: the paper was noted and the named CR was agreed. The field
    # agrees the header document only when the named specification and CR number are
    # its own and nothing else qualifies the clause; a revision-qualified, in-principle
    # or otherwise extended agreement of a CR stays pending instead of reading as `noted`.
    compound = NOTED_AND.fullmatch(text) if 'listedCR' in field and target == event['subject_tdoc'] else None
    if (compound and re.search(r'\bCR', compound['rest'], re.I) and re.search(r'\bagreed\b', compound['rest'], re.I)
            and not re.search(r'\bnot\s+agreed\b', compound['rest'], re.I)):
        listed, named = field['listedCR'], NOTED_CR_AGREED.fullmatch(compound['rest'].strip())
        if (named and listed['crNumber'].isdigit() and int(listed['crNumber'])
                and (listed['spec'], int(listed['crNumber'])) == (named['spec'], int(named['number']))):
            return 'agreed', text, 'noted_document_own_CR_descriptor_agreement'
        return 'ambiguous', text, 'noted_document_CR_agreement_requires_adjudication'
    # `The document is noted` followed by a second outcome (`and agreed as CR<n> in
    # R1-...`, `. Further revised in R1-...`, `and TP is agreed`) states two things in one
    # field. One code cannot carry both, so the field stays pending instead of reading
    # as `noted`; text after `noted` that names no further outcome keeps the code.
    if target == event['subject_tdoc'] and (noted := NOTED_THEN.fullmatch(text)) and SECOND_OUTCOME.search(noted['rest']):
        return 'ambiguous', text, 'noted_document_with_second_outcome_requires_adjudication'
    outputs = approval_outputs(text)
    if outputs:
        # The approved revision is a named output, not an approval of the
        # header's predecessor. Retain every qualifier when classifying it.
        match = APPROVAL_OUTPUT_FIELD.fullmatch(text)
        if match is None or not _names_output(match) or len(set(outputs)) != 1:
            # The output stays pending when the field is not one approval of one named
            # output. The header's own predicate still holds: a field that opens by
            # revising the header (`Revised ..., agreed unseen in R2-x`) keeps `revised`.
            if target == event['subject_tdoc']:
                code, _, rule = _checked_status_field(event, target, text, d)
                if code == 'revised':
                    return code, text, 'checked_document_decision_field:' + rule
            return 'ambiguous', text, 'unsupported_document_revision_output_context'
        output = match['output'].upper()
        code = _output_reading(event, match, d)
        if target == output:
            if code == 'agreed' and incorporation(match['trailing']):
                return 'ambiguous', text, INCORPORATION_RULE
            return code, text, 'explicit_document_revision_output_approval'
        if target == event['subject_tdoc'] and code in {'agreed', 'partially_agreed', 'conditionally_agreed'}:
            return 'revised', text, 'document_approval_names_a_different_revision_output'
        return 'ambiguous', text, 'unresolved_document_revision_output_context'
    code, context, rule = _checked_status_field(event, target, text, d)
    if target == event['subject_tdoc'] and code in {'agreed', 'partially_agreed', 'conditionally_agreed'}:
        if any(m['number'].upper() != target.upper() for m in BARE_NUMBER_APPROVAL.finditer(text)):
            return 'ambiguous', text, 'approval_of_another_number_without_relation'
        if (code == 'agreed' and TP_OBJECT_APPROVAL.match(text)
                and all(n.upper() == target.upper() for n in re.findall(OUTPUT_NUMBER, text, re.I))):
            return 'partially_agreed', text, 'document_TP_object_approval'
        if code == 'agreed' and incorporation(text):
            return 'ambiguous', text, INCORPORATION_RULE
    return code, text, 'checked_document_decision_field:' + rule


def document_resolution_node(event, root=None):
    """Materialize the source event; evidence remains on its qualified assertion."""
    from document_decision_storage import document_resolution_node as canonical_node
    return canonical_node(event, root)
