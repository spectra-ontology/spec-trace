#!/usr/bin/env python3
"""prepare_ts_source_context_split.py — prepare source-qualified TS split shadows.

Spec: reembedding_policy.md §3.1.1; source-owned physical table inventory.
Ontology: preserve source edition/section/table/row bindings across child excerpts.
Cycle: fence inputs → read exact source cells → split with context → verify coverage.
배경: 행 중간에서 끊긴 과거 청크도 원문 좌표와 명시적 표 문맥을 유지한다.
사용: --catalog FILE --census FILE --bodies FILE --stages DIR --output DIR.
LLM 호출: 없음. Only evidence/shadow output is written; no database or model writes.
"""
from __future__ import annotations

import argparse
import collections
from datetime import datetime, timezone
import gc
import gzip
import hashlib
import inspect
import json
from pathlib import Path
import re
import sys
import time

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
sys.path.insert(0, str(ROOT / 'scripts/common'))
import docx_text as d
from docx_search_styles import SearchStyles
from common.chunker import count_tokens
from common.atomic_io import write_bytes_atomic
from ts_search_presentation import TAG, source_info
from ts_source_context_split import bind_source, split_bound_source, SourceContextError, sha

W = '{' + d.W_NS + '}'


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for bit in iter(lambda: handle.read(1 << 20), b''):
            h.update(bit)
    return h.hexdigest()


def read(path):
    path = Path(path)
    with (gzip.open(path, 'rt') if path.suffix == '.gz' else path.open()) as handle:
        return json.load(handle)


def write(path, value):
    path = Path(path)
    raw = (json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n').encode()
    write_bytes_atomic(path, gzip.compress(raw, mtime=0) if path.suffix == '.gz' else raw)


def _enabled(node):
    return node is not None and node.get(W + 'val', 'true') not in ('0', 'false', 'off')


def _bold_row(cells):
    runs = [r for c in cells for r in c.tc.iter(W + 'r')
            if any((t.text or '').strip() for t in r.iter(W + 't'))]
    return bool(runs) and all(_enabled(r.find(W + 'rPr/' + W + 'b')) for r in runs)


def _note_match(plain):
    # A tab is the actual DOCX paragraph delimiter in several numbered NOTE
    # definitions. Bare 'Note N' in a formula is a reference, not a definition.
    return re.match(r'\s*(?:NOTE|Note)\s*(\d+)[ \u00a0]*(?::|\t)', plain)


def shared_note_scope(tree, records, styles):
    """Read notes explicitly declared to apply to the preceding owned tables.

    The records are the complete accepted-reader inventory for one actual
    source section/file. The literal scope sentence supplies the binding;
    proximity alone never promotes one table's NOTE to a section-wide rule.
    """
    if not records:
        return {}
    last = tree.xpath(records[-1]['tableXPath'], namespaces={'w': d.W_NS})[0]
    following = last.getnext()
    while following is not None and following.tag == W + 'p' and not d.final_text(following).strip():
        following = following.getnext()
    if following is None or following.tag != W + 'p':
        return {}
    declaration = d.boxed_text(following, read=styles.read)
    if ' '.join(TAG.sub('', declaration).split()).lower().rstrip('.:') not in (
            'the following notes are applied to the above tables',
            'the following notes apply to the above tables'):
        return {}
    scope = dict(quote=declaration, paragraphXPath=following.getroottree().getpath(following),
                 ownerSectionId=records[0]['ownerSectionId'],
                 tableXPaths=[r['tableXPath'] for r in records])
    notes = collections.defaultdict(list)
    following = following.getnext()
    while following is not None and following.tag == W + 'p':
        text = d.boxed_text(following, read=styles.read)
        plain = TAG.sub('', text)
        if not plain.strip():
            following = following.getnext()
            continue
        # This paragraph is inside an explicit, closed numbered-note block.
        # The source's NOTE 14 has no colon; retain its actual wording as-is.
        match = _note_match(plain) or re.match(r'^\s*NOTE\s+(\d+)\s+(?=[A-Z])', plain)
        if not match:
            break
        number = str(int(match[1]))
        notes[number].append(dict(number=int(number), quote=d.chunk_text(following),
            presentation=text, paragraphXPath=following.getroottree().getpath(following),
            explicitScope=scope))
        following = following.getnext()
    return dict(notes)


def qualify_note_dependencies(table):
    """Bind reviewed table-family notation to its actual numbered definitions.

    A superscript in a CA configuration/bandwidth field is a footnote marker
    when the source explicitly declares a numbered scope for these tables.
    This rule does not treat arbitrary mathematical exponents as footnotes.
    The co-existence table defines F_DL symbols and the SCS convention for
    notes mentioning RB; those exact definitions qualify the dependent rows.
    """
    caption = ' '.join((table.get('actualAdjacentCaption') or {}).get('quote', '').split())
    shared = table.get('explicitSharedNumberedNotes', {})
    if ('NR CA configurations and bandwidth combinations' in caption and shared
            and 'NR CA configuration' in table['flatRows'][0]
            and 'Channel bandwidth' in table['flatRows'][0]):
        refs = {}
        for ri, cells in table['sourceGridRows'].items():
            wanted = set()
            for cell in cells:
                for marker in re.findall(r'<sup>([0-9, /&]+)</sup>', cell['presentation']):
                    wanted.update(map(int, re.findall(r'\d+', marker)))
            if wanted:
                refs[ri] = dict(numbers=sorted(wanted), method='source-declared CA field footnote notation',
                    explicitScope=next(iter(shared.values()))[0]['explicitScope'])
        table['reviewedRowFootnoteReferences'] = refs
    notes = table.get('sourceNumberedNotes', {})
    first, third = notes.get('1', []), notes.get('3', [])
    if ('Requirements for spurious emissions for UE co-existence' in caption
            and len(first) == len(third) == 1
            and 'FDL_low and FDL_high refer to each frequency band' in first[0]['quote']
            and '15 kHz SCS is assumed when RB is mentioned in the note' in third[0]['quote']):
        table['reviewedSymbolNoteDependencies'] = dict(
            rowSymbols=dict(number=1, symbols=['FDL_low', 'FDL_high']),
            selectedNoteTerm=dict(number=3, pattern=r'\bRBs?\b'),
            method='actual table-local definitions of frequency bounds and RB/SCS convention')
    return table


def apply_reviewed_table_fields(table, plan):
    """Apply literal source-pinned header/field reviews without value inference."""
    if (table['path'] != plan['sourcePath'] or table['tableXPath'] != plan['tableXPath']
            or (table.get('actualAdjacentCaption') or {}).get('quote') != plan['captionQuote']
            or table['flatRows'][:len(plan['firstRenderedRows'])] != plan['firstRenderedRows']):
        raise SourceContextError('reviewed source table fields changed: ' + table['path'] + ':' + table['tableXPath'])
    if 'renderedHeaderRows' in plan:
        table['reviewedHeaderRows'] = plan['renderedHeaderRows']
        table['reviewedHeaderRationale'] = plan['rationale']
    if 'footnoteColumns' in plan:
        for example in plan['examples']:
            cells = [c for c in table['sourceGridRows'][str(example['renderedRow'])]
                     if c['column'] == example['column']]
            if len(cells) != 1 or cells[0]['presentation'] != example['presentation']:
                raise SourceContextError('reviewed numeric footnote field changed')
        actual = {}
        for key in ('sourceNumberedNotes', 'adjacentNumberedNotes', 'explicitSharedNumberedNotes'):
            actual.update(table.get(key, {}))
        for number, definitions in plan['numberedNoteDefinitions'].items():
            # A paragraph can contain two literal NOTE labels. The collector
            # keeps the whole source paragraph under both numbers.
            found = {n['quote'] for n in actual.get(number, [])}
            if not {n['quote'] for n in definitions}.issubset(found):
                raise SourceContextError('reviewed numeric footnote definition changed')
        refs = table.setdefault('reviewedRowFootnoteReferences', {})
        for ri, cells in table['sourceGridRows'].items():
            wanted = set(refs.get(ri, {}).get('numbers', []))
            for cell in cells:
                if cell['column'] in plan['footnoteColumns']:
                    for marker in re.findall(r'<sup>([0-9, /&]+)</sup>', cell['presentation']):
                        wanted.update(map(int, re.findall(r'\d+', marker)))
            if wanted:
                refs[ri] = dict(numbers=sorted(wanted), method=plan['rationale'])
    return table


def apply_reviewed_scope(table, supplemented, plan, tree, styles, owned):
    """Apply an exact source-bound review, never a keyword-based truncation."""
    if (plan['sourcePath'] != table['path'] or plan['sectionId'] != table['ownerSectionId']
            or plan['tableXPath'] != table['tableXPath']
            or plan['captionQuote'] != (table.get('actualAdjacentCaption') or {}).get('quote')):
        raise SourceContextError('reviewed physical-table context identity changed')
    opening = []
    target = tree.xpath(table['tableXPath'], namespaces={'w': d.W_NS})[0]
    for quote in plan['sectionOpeningParagraphs']:
        found = tree.xpath(quote['paragraphXPath'], namespaces={'w': d.W_NS})
        if (len(found) != 1 or found[0].tag != W + 'p'
                or d.final_text(found[0]) != quote['quote']
                or target.getparent() is not found[0].getparent()
                or target.getparent().index(found[0]) >= target.getparent().index(target)):
            raise SourceContextError('reviewed governing paragraph differs from its actual source')
        opening.append(dict(presentation=d.boxed_text(found[0], read=styles.read), **quote))
    for prior in plan['governingPhysicalTables']:
        actual = [t for t in owned if t['tableXPath'] == prior['tableXPath']]
        if len(actual) != 1 or actual[0]['producerTableTextSHA256'] != prior['producerTableTextSHA256']:
            raise SourceContextError('reviewed governing physical table differs from source inventory')
    supplemented.update(reviewedSectionOpeningUnits=opening,
        reviewedGoverningTables=plan['governingPhysicalTables'],
        reviewedGoverningTableNotes=plan['governingTableNoteNumbers'],
        reviewedScopeRationale=plan['rationale'])
    return supplemented


def supplement_table(table, record, styles):
    """Read physical grid/merge/paragraph context without propagating blank cells."""
    result = dict(record)
    grid = d.table_grid(table)
    rendered_map = {r['acceptedGridRow']: r['renderedLine'] for r in record['sourceRowMap']}
    source_grid, anchors, notes, unnumbered = {}, {}, collections.defaultdict(list), []
    active_merges = {}
    leading_bold = []
    still_leading_bold = True
    def present(p):
        return d.boxed_text(p, read=styles.read)
    for ri, (_, cells) in enumerate(grid):
        li = rendered_map.get(ri)
        if li is None:
            continue
        row = []
        for cell in cells:
            text = d.cell_text(cell.tc, para=present)
            source_info(text)
            row.append(dict(column=cell.col, span=cell.span, presentation=text,
                            vMerge=cell.vmerge, cellXPath=cell.tc.getroottree().getpath(cell.tc)))
            if cell.vmerge == 'restart':
                active_merges[cell.col] = dict(column=cell.col, span=cell.span,
                    anchorRenderedRow=li, presentation=text,
                    cellXPath=cell.tc.getroottree().getpath(cell.tc))
            elif cell.vmerge == 'continue':
                if cell.col in active_merges:
                    anchors.setdefault(str(li), []).append(active_merges[cell.col])
                else:
                    raise SourceContextError('vertical continuation has no actual restart cell')
            else:
                active_merges.pop(cell.col, None)
            for p in d.iter_all_paragraphs(cell.tc):
                text = present(p)
                plain = TAG.sub('', text)
                match = _note_match(plain)
                locator = p.getroottree().getpath(p)
                if match:
                    number = str(int(match[1]))
                    notes[number].append(dict(number=int(number), quote=d.chunk_text(p),
                        presentation=text, paragraphXPath=locator))
                    for additional in re.finditer(r'\bNOTE\s+(\d+)[ \u00a0]*(?::|\t)', plain[match.end():]):
                        other = str(int(additional[1]))
                        if other != number:
                            notes[other].append(dict(number=int(other), quote=d.chunk_text(p),
                                presentation=text, paragraphXPath=locator))
                elif re.match(r'\s*(?:NOTE|Note)\s*:', plain):
                    unnumbered.append(dict(presentation=text, paragraphXPath=locator))
        source_grid[str(li)] = row
        if still_leading_bold and _bold_row(cells):
            leading_bold.append(li)
        else:
            still_leading_bold = False
    result.update(sourceGridRows=source_grid, sourceMergeAnchors=anchors,
                  sourceNumberedNotes=dict(notes), sourceUnnumberedNotes=unnumbered,
                  sourceLeadingBoldRows=leading_bold,
                  openingRowMethod='first actual row plus explicit tblHeader and leading all-direct-bold rows')
    caption = record.get('actualAdjacentCaption')
    if caption:
        found = table.getroottree().xpath(caption['paragraphXPath'], namespaces={'w': d.W_NS})
        if len(found) != 1 or d.final_text(found[0]) != caption['quote']:
            raise SourceContextError('adjacent physical caption no longer matches its source locator')
        result['presentationCaption'] = present(found[0])
    # Notes immediately following this physical table are table-local source
    # material. Stop at any other nonempty paragraph or another physical table.
    adjacent = collections.defaultdict(list)
    after = table.getnext()
    while after is not None and after.tag == W + 'p':
        text = present(after)
        plain = TAG.sub('', text)
        if not plain.strip():
            after = after.getnext()
            continue
        match = _note_match(plain)
        if match:
            num = str(int(match[1]))
            adjacent[num].append(dict(number=int(num), quote=d.chunk_text(after),
                presentation=text, paragraphXPath=after.getroottree().getpath(after)))
        elif re.match(r'\s*(?:NOTE|Note)\s*:', plain):
            unnumbered.append(dict(presentation=text, paragraphXPath=after.getroottree().getpath(after)))
        else:
            break
        after = after.getnext()
    result['adjacentNumberedNotes'] = dict(adjacent)
    return result


def prepare(args):
    started = time.time()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    files = [Path(args.catalog), Path(args.census), Path(args.bodies)]
    if args.caption_completion:
        files.append(Path(args.caption_completion))
    if args.context_plan:
        files.append(Path(args.context_plan))
    inputs = {str(p): file_sha(p) for p in files}
    code_paths = [Path(__file__), Path(__file__).with_name('ts_source_context_split.py'),
                  Path(__file__).with_name('ts_search_presentation.py'),
                  Path(__file__).with_name('docx_text.py'), Path(__file__).with_name('docx_search_styles.py'),
                  ROOT / 'scripts/common/common/chunker.py', ROOT / 'scripts/common/common/embedding_registry.py']
    codes = {str(p.relative_to(ROOT)): file_sha(p) for p in code_paths}
    bundle, census = read(args.catalog), read(args.census)
    wanted = {(r['collection'], str(r['pointId'])) for r in census['records']}
    all_bodies = {(r['collection'], str(r['pointId'])): r for r in read(args.bodies)}
    bodies = {k: v for k, v in all_bodies.items() if k in wanted}
    if set(bodies) != wanted:
        raise SourceContextError('candidate full bodies do not cover the selected current parents')
    editions = {tuple(e['edition']): e for e in bundle['editions']}
    fences = {}
    for e in editions.values():
        for path, expected in e['sourceFences'].items():
            if path in fences and fences[path] != expected:
                raise SourceContextError('different source hashes for the same input file')
            fences[path] = expected
    for path, expected in fences.items():
        if file_sha(ROOT / path) != expected:
            raise SourceContextError('source file drift: ' + path)
    reviewed = {}
    reviewed_fields = collections.defaultdict(list)
    if args.context_plan:
        context_plan = read(args.context_plan)
        for field in ('headerCases', 'numericFootnoteCases'):
            for plan in context_plan.get(field, []):
                if fences.get(plan['sourcePath']) != plan['sourceSHA256']:
                    raise SourceContextError('reviewed table-field source edition bytes changed')
                reviewed_fields[tuple(plan['edition']), plan['sourcePath'], plan['tableXPath']].append(plan)
        for plan in context_plan['cases']:
            if fences.get(plan['sourcePath']) != plan['sourceSHA256']:
                raise SourceContextError('reviewed context source edition bytes changed')
            key = tuple(plan['edition']), plan['sourcePath'], plan['tableXPath']
            if key in reviewed:
                raise SourceContextError('duplicate reviewed physical-table context')
            reviewed[key] = plan
    completions = []
    if args.caption_completion:
        for proof in read(args.caption_completion):
            key = proof['collection'], str(proof['pointId'])
            if key not in bodies:
                continue
            recipient = bodies[key]
            donor = all_bodies[proof['donorCollection'], str(proof['pointId'])]
            if (recipient['chunkId'] != donor['chunkId'] or recipient['chunkId'] != proof['chunkId']
                    or recipient['oldBodySHA256'] != donor['oldBodySHA256']
                    or sha(recipient['newText']) != proof['oldProposedBodySHA256']
                    or sha(donor['newText']) != proof['newBodySHA256']
                    or TAG.sub('', recipient['newText']) != TAG.sub('', donor['newText'])):
                raise SourceContextError('caption completion changes the fenced body identity or plain source coordinates')
            editions_needed = {tuple(s['edition']) for s in recipient['sources']}
            editions_proved = {tuple(s['edition']) for s in proof['sourceBindings']}
            if not editions_needed.issubset(editions_proved):
                raise SourceContextError('caption completion omits a recipient source edition')
            for source in proof['sourceBindings']:
                if fences.get(source['source']) != source['sha256']:
                    raise SourceContextError('caption completion source differs from the actual source edition fence')
            recipient['newText'] = donor['newText']
            recipient['newBodySHA256'] = proof['newBodySHA256']
            recipient['captionEdits'] = donor['captionEdits']
            completions.append(proof)
    table_refs = collections.defaultdict(list)
    for ed, e in editions.items():
        for ti, table in enumerate(e['targetTables']):
            table_refs[table['path']].append((ed, ti, table))
    collector_sha = sha('\n'.join(inspect.getsource(f) for f in
        (_enabled, _bold_row, _note_match, shared_note_scope, qualify_note_dependencies,
         apply_reviewed_table_fields, apply_reviewed_scope, supplement_table)))
    plan_sha = file_sha(args.context_plan) if args.context_plan else None
    reader_fences = {p: v for p, v in codes.items() if p.endswith(('docx_text.py', 'docx_search_styles.py'))}
    supplements = {}
    if args.contexts:
        cached = read(args.contexts)
        if (cached['sourceFences'] != fences or cached['readerSHA256'] != reader_fences
                or cached['collectorFunctionSHA256'] != collector_sha
                or cached.get('reviewedContextPlanSHA256') != plan_sha
                or cached['catalogSHA256'] != inputs[str(Path(args.catalog))]):
            raise SourceContextError('cached actual source context generation differs')
        supplements = {(tuple(r['edition']), r['tableIndex']): r['table'] for r in cached['tables']}
        if set(supplements) != {(ed, ti) for ed, e in editions.items() for ti in range(len(e['targetTables']))}:
            raise SourceContextError('cached source contexts omit a physical table')
    else:
        for index, (path, targets) in enumerate(sorted(table_refs.items()), 1):
            document = d.open_document(ROOT / path)
            styles = SearchStyles(document.styles.element)
            tree = document.element.getroottree()
            owned = collections.defaultdict(list)
            for ed, ti, table in targets:
                owned[(ed, table['ownerSectionId'])].append(table)
            shared = {key: shared_note_scope(tree, rows, styles) for key, rows in owned.items()}
            for ed, ti, table in targets:
                found = tree.xpath(table['tableXPath'], namespaces={'w': d.W_NS})
                if len(found) != 1 or found[0].tag != W + 'tbl':
                    raise SourceContextError('physical table XPath is absent or nonunique')
                supplemented = supplement_table(found[0], table, styles)
                supplemented['explicitSharedNumberedNotes'] = shared[(ed, table['ownerSectionId'])]
                supplemented = qualify_note_dependencies(supplemented)
                for plan in reviewed_fields.get((ed, table['path'], table['tableXPath']), []):
                    supplemented = apply_reviewed_table_fields(supplemented, plan)
                if (ed, table['path'], table['tableXPath']) in reviewed:
                    supplemented = apply_reviewed_scope(table, supplemented,
                        reviewed[(ed, table['path'], table['tableXPath'])], tree, styles,
                        owned[(ed, table['ownerSectionId'])])
                supplements[(ed, ti)] = supplemented
            del tree, styles, document
            gc.collect()
            print(json.dumps(dict(stage='source_context', completed=index, files=len(table_refs),
                                  seconds=round(time.time() - started, 2))), flush=True)
        write(output / 'actual_source_contexts.json.gz', dict(sourceFences=fences,
            readerSHA256=reader_fences, collectorFunctionSHA256=collector_sha,
            reviewedContextPlanSHA256=plan_sha,
            catalogSHA256=inputs[str(Path(args.catalog))], tables=[dict(edition=list(ed), tableIndex=ti,
                table=table) for (ed, ti), table in supplements.items()]))
    stages, stage_fences = {}, {}
    records, errors = [], []
    for ordinal, key in enumerate(sorted(wanted), 1):
        body = bodies[key]
        pp = source_info(body['newText'])[0]
        grouped = {}
        for source in body['sources']:
            ed, sid = tuple(source['edition']), source['sectionId']
            if ed not in stages:
                path = Path(args.stages) / ('_'.join(ed) + '.json.gz')
                actual = file_sha(path)
                if actual != editions[ed]['stageSHA256']:
                    raise SourceContextError('source shadow generation drift')
                stage_fences[str(path)] = actual
                stages[ed] = {s['sectionId']: s for s in read(path)['sections']}
            section = stages[ed][sid]['newText']
            tables = [supplements[(ed, ti)] for ti, t in enumerate(editions[ed]['targetTables'])
                      if t['ownerSectionId'] == sid]
            spans = source.get('sourceLineSpans', [dict(source, payloadStart=0, payloadEnd=len(pp))])
            try:
                bound = bind_source(body['newText'], section, spans, tables,
                                    edition=ed, section_id=sid)
                children = split_bound_source(bound, count_tokens)
                sig = tuple(c['textSHA256'] for c in children)
                group = grouped.setdefault(sig, dict(sourceBindings=[], children=children))
                group['sourceBindings'].append(dict(edition=list(ed), sectionId=sid,
                    stageSHA256=editions[ed]['stageSHA256'], verifiedSourceSpans=spans,
                    childSourceProvenance=[dict(textSHA256=c['textSHA256'],
                        sourceRows=c['sourceRows'], sourceIntervals=c['sourceIntervals'],
                        context=[{k: v for k, v in u.items() if k != 'text'} for u in c['context']])
                        for c in children]))
            except SourceContextError as error:
                errors.append(dict(collection=key[0], pointId=key[1], edition=list(ed),
                                   sectionId=sid, error=str(error)))
        records.append(dict(collection=key[0], pointId=key[1], chunkId=body['chunkId'],
            oldPayloadSHA256=body['oldPayloadSHA256'], oldBodySHA256=body['oldBodySHA256'],
            candidateBodySHA256=sha(body['newText']), groups=list(grouped.values())))
        if ordinal % 10 == 0 or ordinal == len(wanted):
            print(json.dumps(dict(stage='qualified_children', completed=ordinal,
                                  parents=len(wanted), errors=len(errors), seconds=round(time.time() - started, 2))), flush=True)
    for path, expected in fences.items():
        if file_sha(ROOT / path) != expected:
            raise SourceContextError('source file changed during preparation')
    if any(file_sha(ROOT / p) != expected for p, expected in codes.items()):
        raise SourceContextError('maintained code changed during preparation')
    if any(file_sha(p) != expected for p, expected in inputs.items()):
        raise SourceContextError('proposal input changed during preparation')
    if any(file_sha(p) != expected for p, expected in stage_fences.items()):
        raise SourceContextError('source shadow changed during preparation')
    children = [c for r in records for g in r['groups'] for c in g['children']]
    unresolved = [dict(collection=r['collection'], pointId=r['pointId'], childIndex=ci,
        sourceBindings=g['sourceBindings'], unit=u)
        for r in records for g in r['groups'] for ci, c in enumerate(g['children'])
        for u in c['context'] if u['kind'] == 'unresolved_source_note_reference']
    manifest = dict(schema='ts-source-context-split-shadow',
        createdUTC=datetime.now(timezone.utc).isoformat(), inputSHA256=inputs,
        codeSHA256=codes, sourceFences=fences, sourceShadowSHA256=stage_fences,
        records=records, errors=errors, unresolvedSourceNoteReferences=unresolved,
        captionCompletions=completions,
        summary=dict(parents=len(records), completeParents=sum(bool(r['groups']) and not any(
            e['collection'] == r['collection'] and e['pointId'] == r['pointId'] for e in errors) for r in records),
            failedParents=len({(e['collection'], e['pointId']) for e in errors}),
            failedSourceBindings=len(errors),
            childrenWithUnresolvedSourceNotes=len({(u['collection'], u['pointId'],
                tuple(tuple(s['edition']) for s in u['sourceBindings']), u['childIndex']) for u in unresolved}),
            sourceBindings=sum(len(b['sources']) for b in bodies.values()),
            childGroups=sum(len(r['groups']) for r in records), children=len(children),
            maxTokens=max((c['tokens'] for c in children), default=0),
            sourceFiles=len(fences), errors=len(errors), durationSeconds=time.time() - started),
        boundary=['A source excerpt is byte-exact after removing generated script tags; concatenated child cores reconstruct its complete proposed parent.',
            'Context is quoted from actual source edition/section/physical table; empty cells without explicit vertical merging do not inherit values.',
            'First table row and direct-bold opening rows are source opening material, not a claim of expert classification of all semantic dependencies.',
            'Explicit NOTE references, literal above-tables scope declarations and the source-bound reviewed conditional notes retain their exact scope. Source references with no numbered definition in that scope are flagged without inventing a definition. Visual superscripts alone do not establish a NOTE reference.',
            'Postimage point identities, canonical artifact integration, fresh database preimage comparison and embedding are the applying reconciler responsibility.'],
        writes=dict(source=0, canonicalArtifact=0, database=0, embedding=0, evidenceOnly=True))
    write(output / 'qualified_children.json.gz', manifest)
    summary = {k: v for k, v in manifest.items() if k != 'records'}
    summary['manifest'] = dict(path=str(output / 'qualified_children.json.gz'),
                              sha256=file_sha(output / 'qualified_children.json.gz'))
    write(output / 'receipt.json', summary)
    print(json.dumps(summary['summary']), flush=True)
    return 1 if errors else 0


def default_context_plan(root=None):
    """Use this PC's reviewed scopes when present; fresh sources need no old ledger."""
    path = (Path(root) if root is not None else ROOT) / 'ontology/config/ts_source_context_scopes.json'
    return path if path.is_file() else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('catalog', 'census', 'bodies', 'stages', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--contexts', type=Path, help='Reuse exact fenced accepted-reader table context bytes.')
    parser.add_argument('--caption-completion', type=Path, help='Exact source-bound twin caption completion receipt.')
    parser.add_argument('--context-plan', type=Path,
        default=default_context_plan(),
        help='Reviewed XPath/quote/source-SHA-bound physical-table context scopes.')
    return prepare(parser.parse_args())


if __name__ == '__main__':
    raise SystemExit(main())
