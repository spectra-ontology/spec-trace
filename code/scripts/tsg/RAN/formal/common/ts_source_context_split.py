#!/usr/bin/env python3
"""ts_source_context_split.py — source coordinates and context for TS child excerpts.

Spec: reembedding_policy.md §3.1.1; chunking_standards.md hard token bound.
Ontology: a search excerpt retains its actual source edition, table and row scope.
Cycle: verify unique source spans → bind physical rows → repeat qualified context.
배경: 부분 행과 중복 overlap도 원문 좌표로 결속하고 표 문맥을 함께 보존한다.
사용: bind_source(parent, section, spans, tables); split_bound_source(binding, counter).
LLM 호출: 없음. This pure helper does not write artifacts, models or databases.

The caller supplies the accepted-reader physical-table inventory and a source
section from the same fenced producer generation. Uniqueness of a quotation is
checked here; no row value is inferred from an empty cell. Context labels identify
source material, rather than assign new normative interpretations to it.
"""
from __future__ import annotations

import bisect
from dataclasses import dataclass
import hashlib
import re

from ts_search_presentation import TAG, normalize, project, source_info


class SourceContextError(ValueError):
    """The requested projection cannot satisfy the explicit source contract."""


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def normalized(text):
    return normalize(text)[0]


def explicit_note_references(text):
    """Read written NOTE-number lists; ordinary numbers establish no scope."""
    found = set()
    pattern = r'\bNOTEs?\s*(\d+(?:(?:\s*[,/&]\s*|\s+and\s+)\d+)*)\b'
    for match in re.finditer(pattern, text, flags=re.IGNORECASE):
        tail = text[match.end():]
        if re.match(r'[ \u00a0]*(?::|\t)', tail):
            continue
        found.update(map(int, re.findall(r'\d+', match[1])))
    return found


def render_at(plain, source_norm, roles, start):
    """Project one known source interval, preserving the quotation characters."""
    value, positions = normalize(plain)
    if source_norm[start:start + len(value)] != value:
        raise SourceContextError('quotation differs from its declared source interval')
    result, status = project(plain, value, positions,
                             source_norm[start:start + len(value)],
                             type(roles)([(max(a, start) - start, min(b, start + len(value)) - start, k)
                                          for a, b, k in roles
                                          if a < start + len(value) and b > start]))
    if result is None:
        raise SourceContextError('source role projection: ' + status)
    return result['text']


@dataclass
class BoundSource:
    parent: str
    parent_plain: str
    parent_norm: str
    parent_roles: object
    parent_positions: object
    source_plain: str
    source_norm: str
    source_roles: object
    source_positions: object
    spans: list
    tables: list
    edition: tuple
    section_id: str


def bind_source(parent, section, spans, tables, *, edition, section_id):
    """Verify each maximal run and map the ordered actual tables into the section.

    ``spans`` uses plain-payload character offsets and normalized-source offsets,
    as emitted by ``project_lines``. Overlapping source runs are intentional:
    legacy overlap text can repeat a prefix of the next run.
    """
    pp, pn, parent_roles = source_info(parent)
    _, parent_positions = normalize(pp)
    sp, sn, roles = source_info(section)
    _, positions = normalize(sp)
    checked = []
    cursor = 0
    for raw in spans:
        a, b = raw['payloadStart'], raw['payloadEnd']
        if a != cursor or not a < b <= len(pp):
            raise SourceContextError('source runs do not cover the payload in order')
        quote, mapping = normalize(pp[a:b])
        start = raw['startInNormalizedSource']
        if sn[start:start + len(quote)] != quote:
            raise SourceContextError('maximal source run is not an exact source quotation')
        if sn.find(quote) != start or sn.find(quote, start + 1) >= 0:
            raise SourceContextError('maximal source run is not unique in the actual section')
        checked.append(dict(raw, mapping=mapping, normalized=quote))
        cursor = b
    if cursor != len(pp):
        raise SourceContextError('source runs omit payload characters')
    bound_tables = []
    cursor = 0
    for raw in tables:
        if raw['ownerSectionId'] != section_id:
            raise SourceContextError('physical table belongs to another source section')
        rows = raw['flatRows']
        quote = normalized('\n'.join(rows))
        start = sn.find(quote, cursor)
        if start < 0:
            raise SourceContextError('ordered physical table is absent from the source section')
        # The caller inventories every owned physical table, in producer order.
        # A later identical table is distinguished by this complete ordered list.
        end = start + len(quote)
        row_intervals = []
        offset = start
        for row in rows:
            value = normalized(row)
            row_intervals.append((offset, offset + len(value)))
            offset += len(value) + 1
        if row_intervals and row_intervals[-1][1] != end:
            raise SourceContextError('physical row serialization differs from source text')
        bound_tables.append(dict(raw, start=start, end=end, rowIntervals=row_intervals))
        cursor = end
    return BoundSource(parent, pp, pn, parent_roles, parent_positions, sp, sn, roles, positions, checked,
                       bound_tables, tuple(edition), section_id)


def _atom_spans(binding):
    """Keep original characters; break at actual lines, runs and NOTE paragraphs."""
    text = binding.parent_plain
    cuts = {0, len(text)}
    cuts.update(m.end() for m in re.finditer('\n', text))
    cuts.update(s['payloadStart'] for s in binding.spans)
    cuts.update(s['payloadEnd'] for s in binding.spans)
    # A flattened physical notes cell can contain many separate paragraphs.
    # These are only split points; note ownership is verified independently.
    cuts.update(m.start() for m in re.finditer(r'(?<!\w)(?:NOTE|Note)\s+\d+[ \u00a0]*(?::|\t)', text))
    cuts = sorted(cuts)
    return [(a, b) for a, b in zip(cuts, cuts[1:]) if a < b]


def _source_interval(binding, a, b):
    span = next((s for s in binding.spans
                 if s['payloadStart'] <= a and b <= s['payloadEnd']), None)
    if span is None:
        raise SourceContextError('excerpt crosses an unpartitioned maximal run boundary')
    quote = binding.parent_plain[a:b]
    qn, _ = normalize(quote)
    if not qn:
        return None
    leading = len(quote) - len(quote.lstrip())
    trailing = len(quote) - len(quote.rstrip())
    local_a = a - span['payloadStart'] + leading
    local_b = b - span['payloadStart'] - trailing
    mapping = span['mapping']
    first = bisect.bisect_right(mapping.ends, local_a)
    last = bisect.bisect_left(mapping.starts, local_b) - 1
    if first >= len(mapping.starts) or last < first:
        raise SourceContextError('nonempty excerpt has no normalized source coordinates')
    start = span['startInNormalizedSource'] + first
    end = span['startInNormalizedSource'] + last + 1
    if binding.source_norm[start:end] != qn:
        raise SourceContextError('excerpt interval changes source characters')
    return start, end


def _source_slice(binding, a, b):
    while a < b and binding.source_norm[a].isspace():
        a += 1
    while b > a and binding.source_norm[b - 1].isspace():
        b -= 1
    if a >= b:
        return ''
    positions = binding.source_positions
    quote = binding.source_plain[positions[a][0]:positions[b - 1][1]]
    return render_at(quote, binding.source_norm, binding.source_roles, a)


def _row_text(binding, table, ri):
    a, _ = table['rowIntervals'][ri]
    return render_at(table['flatRows'][ri], binding.source_norm,
                     binding.source_roles, a)


def _parent_slice(binding, a, b):
    quote = binding.parent_plain[a:b]
    if not quote.strip():
        return quote
    first_char = a + len(quote) - len(quote.lstrip())
    first = bisect.bisect_right(binding.parent_positions.ends, first_char)
    return render_at(quote, binding.parent_norm, binding.parent_roles, first)


def context_for(binding, atoms):
    """Return explicit source context and its exact provenance for these atoms."""
    hits = {}
    intervals = []
    for a, b in atoms:
        interval = _source_interval(binding, a, b)
        if interval is None:
            continue
        x, y = interval
        intervals.append((a, b, x, y))
        for ti, table in enumerate(binding.tables):
            if x < table['end'] and y > table['start']:
                for ri, (ra, rb) in enumerate(table['rowIntervals']):
                    if x < rb and y > ra:
                        hits.setdefault(ti, set()).add(ri)
    units = []
    def add(kind, text, **where):
        if text.strip():
            source_info(text)  # balanced generated search roles
            units.append(dict(kind=kind, text=text, plainSHA256=sha(TAG.sub('', text)), **where))
    reviewed_hits = bool(hits) and all('reviewedSectionOpeningUnits' in binding.tables[ti] for ti in hits)
    if binding.tables and not reviewed_hits:
        first = binding.tables[0]['start']
        if first:
            add('section_opening_before_first_table', _source_slice(binding, 0, first),
                normalizedSourceStart=0, normalizedSourceEnd=first)
    for ti, rows in sorted(hits.items()):
        t = binding.tables[ti]
        locator = dict(path=t['path'], tableXPath=t['tableXPath'], tableIndex=ti)
        if reviewed_hits:
            for paragraph in t['reviewedSectionOpeningUnits']:
                add('reviewed_governing_source_paragraph', paragraph['presentation'],
                    **locator, paragraphXPath=paragraph['paragraphXPath'],
                    rationale=t['reviewedScopeRationale'])
            for source_table in t.get('reviewedGoverningTables', []):
                prior = [other for other in binding.tables
                         if other['tableXPath'] == source_table['tableXPath']]
                if len(prior) != 1 or prior[0]['producerTableTextSHA256'] != source_table['producerTableTextSHA256']:
                    raise SourceContextError('reviewed governing table lost its source binding')
                prior = prior[0]
                caption = prior.get('presentationCaption') or (prior.get('actualAdjacentCaption') or {}).get('quote', '')
                add('reviewed_governing_physical_table', caption + '\n' + '\n'.join(
                    _row_text(binding, prior, ri) for ri in range(len(prior['flatRows']))),
                    **locator, governingTableXPath=prior['tableXPath'])
        cap = t.get('presentationCaption') or (t.get('actualAdjacentCaption') or {}).get('quote')
        if cap:
            add('table_caption', cap, **locator,
                paragraphXPath=(t.get('actualAdjacentCaption') or {}).get('paragraphXPath'))
        # First row is labelled as opening context, not interpreted as a header.
        opening = {0} if t['flatRows'] else set()
        explicit = {h['renderedLine'] for h in t.get('explicitHeaders', [])}
        opening.update(t.get('sourceLeadingBoldRows', []))
        opening.update(t.get('reviewedHeaderRows', []))
        for ri in sorted(opening | explicit):
            grid = t.get('sourceGridRows', {}).get(str(ri))
            header = (_row_text(binding, t, ri) if not grid else ' | '.join(
                f"column {c['column'] + 1}" +
                (f"–{c['column'] + c['span']}" if c['span'] != 1 else '') + ': ' +
                (c['presentation'] if c['presentation'] else '[empty source cell]') for c in grid))
            kind = ('explicit_header' if ri in explicit else
                    'reviewed_column_header_row' if ri in t.get('reviewedHeaderRows', [])
                    else 'source_table_opening_row')
            add(kind, header, **locator, renderedRow=ri,
                reviewedRationale=t.get('reviewedHeaderRationale'))
        if ti:
            # Preceding non-table source prose is quoted as preceding material.
            # It is not asserted to be a global condition of later tables.
            a = binding.tables[ti - 1]['end']
            if a < t['start']:
                gap = _source_slice(binding, a, t['start'])
                # Table-specific NOTE definitions from an earlier table are not
                # distributed across later tables just because they precede it.
                paragraphs = [p for p in gap.splitlines()
                              if not re.match(r'^\s*(?:NOTE|Note)\b', TAG.sub('', p))]
                add('source_prose_before_table', '\n'.join(paragraphs), **locator,
                    normalizedSourceStart=a, normalizedSourceEnd=t['start'])
        wanted = set(t.get('reviewedGoverningTableNotes', []))
        for ri in rows | opening | explicit:
            ref = t.get('sourceRowNoteReferences', {}).get(str(ri), {})
            wanted.update(ref.get('numbers', []))
            wanted.update(t.get('reviewedRowFootnoteReferences', {}).get(str(ri), {}).get('numbers', []))
            # Explicit NOTE/Note N references are textual evidence, not numbers
            # guessed from units or a superscript's visual appearance.
            text = t['flatRows'][ri]
            wanted.update(explicit_note_references(text))
        if cap:
            wanted.update(explicit_note_references(TAG.sub('', cap)))
        dependency = t.get('reviewedSymbolNoteDependencies')
        if dependency:
            row_rule = dependency['rowSymbols']
            if any(any(symbol in TAG.sub('', t['flatRows'][ri]) for symbol in row_rule['symbols'])
                   for ri in rows):
                wanted.add(row_rule['number'])
            term_rule = dependency['selectedNoteTerm']
            selected = [n['quote'] for num in wanted
                        for n in t.get('sourceNumberedNotes', {}).get(str(num), [])]
            if any(re.search(term_rule['pattern'], quote) for quote in selected):
                wanted.add(term_rule['number'])
        for num in sorted(wanted):
            notes = t.get('sourceNumberedNotes', {}).get(str(num), [])
            if not notes:
                notes = t.get('adjacentNumberedNotes', {}).get(str(num), [])
            if not notes:
                notes = t.get('explicitSharedNumberedNotes', {}).get(str(num), [])
            texts = {n.get('presentation', n['quote']) for n in notes}
            if not texts:
                # Preserve an inconsistent reference in the source itself.
                # This reports its unresolved status; it supplies no invented
                # definition and does not borrow a same-numbered foreign NOTE.
                add('unresolved_source_note_reference',
                    f'NOTE {num} is referenced in this physical source table; its numbered definition is absent from this table and its explicit note scope.',
                    **locator, number=num, status='source_definition_not_found',
                    numberedDefinitionsPresent=sorted(set(t.get('sourceNumberedNotes', {})) |
                        set(t.get('adjacentNumberedNotes', {})) |
                        set(t.get('explicitSharedNumberedNotes', {}))))
                continue
            if len(texts) != 1:
                raise SourceContextError(f'NOTE {num} has no unique table-local source definition')
            for note in notes:
                if 'explicitScope' in note:
                    scope = note['explicitScope']
                    add('explicit_note_scope_declaration', scope['quote'], **locator,
                        paragraphXPath=scope['paragraphXPath'], tableXPaths=scope['tableXPaths'])
            add('direct_numbered_note', next(iter(texts)), **locator, number=num,
                paragraphXPaths=[n['paragraphXPath'] for n in notes],
                explicitScopes=[n['explicitScope'] for n in notes if 'explicitScope' in n],
                dependencyContract=t.get('reviewedSymbolNoteDependencies'),
                sourceFieldFootnoteRows=[ri for ri in sorted(rows | opening | explicit)
                    if num in t.get('reviewedRowFootnoteReferences', {}).get(str(ri), {}).get('numbers', [])])
        for note in t.get('sourceUnnumberedNotes', []):
            add('table_local_unnumbered_note', note['presentation'], **locator,
                paragraphXPath=note['paragraphXPath'])
        # Only XML-declared vertical merging supplies an earlier cell's value.
        # The quotation remains labelled as a source merge anchor. Empty cells
        # without vMerge never inherit an earlier row's value.
        for ri in sorted(rows):
            for anchor in t.get('sourceMergeAnchors', {}).get(str(ri), []):
                add('explicit_vertical_merge_anchor', anchor['presentation'], **locator,
                    renderedRow=ri, anchorRenderedRow=anchor['anchorRenderedRow'],
                    column=anchor['column'], span=anchor['span'])
        # Retain column positions that the legacy flat-row rendering discarded.
        for ri in sorted(rows):
            grid = t.get('sourceGridRows', {}).get(str(ri))
            if grid and (t.get('sourceEmptyCellColumns', {}).get(str(ri))
                         or any(c['span'] != 1 for c in grid)):
                if len(grid) == 1:
                    # A wide notes cell can contain every table NOTE. Repeating
                    # that entire value would distribute unrelated conditions.
                    c = grid[0]
                    add('source_excerpt_cell_position',
                        f"Source excerpt belongs to columns {c['column'] + 1}–{c['column'] + c['span']} of this physical row.",
                        **locator, renderedRow=ri, cellXPath=c.get('cellXPath'))
                    continue
                cells = [f"column {c['column'] + 1}" +
                         (f"–{c['column'] + c['span']}" if c['span'] != 1 else '') +
                         ': ' + (c['presentation'] if c['presentation'] else '[empty source cell]')
                         for c in grid]
                add('source_row_column_positions', ' | '.join(cells), **locator, renderedRow=ri)
    # Identical context quotations are repeated only once within a child. Their
    # provenance remains a list, so multiple actual table scopes are retained.
    unique = {}
    for u in units:
        key = u['kind'], u['text']
        if key not in unique:
            unique[key] = dict(u, provenance=[])
        unique[key]['provenance'].append({k: v for k, v in u.items() if k not in ('text', 'kind', 'plainSHA256')})
    return list(unique.values()), intervals, hits


def _assemble(binding, atoms):
    units, intervals, hits = context_for(binding, atoms)
    context = []
    for unit in units:
        label = unit['kind'].replace('_', ' ')
        context.append('[' + label + ']\n' + unit['text'])
    # Blank characters between atoms are part of the original excerpt too.
    core = ''
    for a, b in atoms:
        core += _parent_slice(binding, a, b)
    if TAG.sub('', core) != ''.join(binding.parent_plain[a:b] for a, b in atoms):
        raise SourceContextError('excerpt source characters changed during role projection')
    text = '\n\n'.join(context + ['[Source excerpt]\n' + core])
    source_info(text)
    return dict(text=text, coreText=core, coreSpans=[list(x) for x in atoms],
                context=units, sourceIntervals=[dict(payloadStart=a, payloadEnd=b,
                    normalizedSourceStart=x, normalizedSourceEnd=y) for a, b, x, y in intervals],
                sourceRows=[dict(tableIndex=ti, path=binding.tables[ti]['path'],
                    tableXPath=binding.tables[ti]['tableXPath'], renderedRows=sorted(rows))
                    for ti, rows in sorted(hits.items())])


def split_bound_source(binding, count_tokens, *, hard_max=6500, target=2000):
    """Greedily partition original units, counting each full qualified postimage.

    This deliberately has no character-cut fallback. A single source unit plus
    its explicit context that exceeds the budget is a reported blocking case.
    It must be subdivided at an actual cell/paragraph boundary by the caller.
    """
    atoms = _atom_spans(binding)
    output = []
    pending = []
    def finish(group):
        image = _assemble(binding, group)
        image['tokens'] = count_tokens(image['text'])
        if image['tokens'] > hard_max:
            raise SourceContextError('one source unit and its qualified context exceed hard_max')
        image['textSHA256'] = sha(image['text'])
        image['corePlainSHA256'] = sha(TAG.sub('', image['coreText']))
        return image
    for atom in atoms:
        candidate = _assemble(binding, pending + [atom])
        tokens = count_tokens(candidate['text'])
        core_tokens = count_tokens(''.join(binding.parent_plain[a:b] for a, b in pending + [atom]))
        if pending and (tokens > hard_max or core_tokens > target):
            output.append(finish(pending))
            pending = [atom]
        else:
            pending.append(atom)
    if pending:
        output.append(finish(pending))
    reconstructed = ''.join(TAG.sub('', child['coreText']) for child in output)
    if reconstructed != binding.parent_plain:
        raise SourceContextError('child source excerpts do not reconstruct the complete parent')
    return output
