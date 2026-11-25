#!/usr/bin/env python3
"""ts_search_presentation.py — project source script roles onto existing TS bodies.

Spec: docs/tsg/build/standards/reembedding_policy.md; generated Word script markup.
Ontology: bind a search presentation to its actual source span and physical table.
Cycle: normalize source/body → require equivalent source presentations → annotate.
배경: 기존 청크 경계·표 머리글을 유지하며 원문의 첨자 역할만 보존한다.
사용: source_info(generated_search_text), project(...) 또는 project_lines(...).
LLM 호출: 없음. No file, source, artifact, model or database writes.

Inputs must carry generated <sup>/<sub> markers and a separately verified plain
projection. Literal source text resembling those markers requires another token
representation before this adapter can be used. A successful match establishes
text/typography correspondence, not telecom semantics or normative approval.
"""
from __future__ import annotations
from array import array
import bisect
import re
TAG = re.compile('<(/?)(sup|sub)>')

class Positions:
    """Compact normalized-character to original-character spans."""

    def __init__(self):
        self.starts = array('I')
        self.ends = array('I')

    def append(self, pair):
        self.starts.append(pair[0])
        self.ends.append(pair[1])

    def __iter__(self):
        return zip(self.starts, self.ends)

    def __getitem__(self, i):
        return (self.starts[i], self.ends[i])

def normalize(s):
    """Collapse whitespace for matching while retaining original character spans."""
    out = []
    mapping = Positions()
    pending = None
    for (i, c) in enumerate(s):
        if c.isspace():
            if out:
                pending = (pending[0] if pending else i, i + 1)
        else:
            if pending is not None:
                out.append(' ')
                mapping.append(pending)
                pending = None
            out.append(c)
            mapping.append((i, i + 1))
    return (''.join(out), mapping)

class ScriptRanges(list):
    """Sorted disjoint script ranges for bounded source-span lookups."""

    def __init__(self, values):
        super().__init__(values)
        self.starts = [a for (a, b, k) in values]
        self.ends = [b for (a, b, k) in values]
        if any((self.ends[i] > self.starts[i + 1] for i in range(len(values) - 1))):
            raise ValueError('source script roles overlap')

def source_info(text):
    """Decode generated flat script tags into exact plain text and role ranges."""
    pieces = []
    ranges = []
    offset = 0
    pos = 0
    stack = []
    for m in TAG.finditer(text):
        bit = text[pos:m.start()]
        pieces.append(bit)
        offset += len(bit)
        if not m[1]:
            stack.append((m[2], offset))
        else:
            if not stack or stack[-1][0] != m[2]:
                raise ValueError('unbalanced source script tags')
            (kind, start) = stack.pop()
            ranges.append((start, offset, kind))
        pos = m.end()
    pieces.append(text[pos:])
    plain = ''.join(pieces)
    if stack:
        raise ValueError('unclosed script tags')
    (norm, mapping) = normalize(plain)
    starts = [a for (a, b) in mapping]
    ends = [b for (a, b) in mapping]
    nr = []
    for (a, b, kind) in ranges:
        i = bisect.bisect_right(ends, a)
        j = bisect.bisect_left(starts, b)
        if i < j:
            nr.append((i, j, kind))
    return (plain, norm, ScriptRanges(sorted(nr)))

def project(payload, normalized, mapping, source_norm, ranges):
    """Project only when every matching source occurrence has the same typography."""
    start = source_norm.find(normalized)
    if start < 0:
        return (None, 'no_body_match')
    first = None
    first_start = None
    occurrences = 0
    while start >= 0:
        edits = []
        end = start + len(normalized)
        lo = bisect.bisect_right(ranges.ends, start)
        hi = bisect.bisect_left(ranges.starts, end)
        for (a, b, kind) in ranges[lo:hi]:
            i = max(0, a - start)
            j = min(len(normalized), b - start)
            if i < j:
                edits.append((mapping[i][0], mapping[j - 1][1], kind))
        edits.sort()
        out = []
        last = 0
        for (a, b, kind) in edits:
            if a < last:
                return (None, 'overlapping_source_styles')
            out.extend((payload[last:a], '<' + kind + '>', payload[a:b], '</' + kind + '>'))
            last = b
        out.append(payload[last:])
        text = ''.join(out).replace('</sup><sup>', '').replace('</sub><sub>', '')
        if TAG.sub('', text) != payload:
            raise ValueError('payload plain text changed')
        if first is None:
            first = text
            first_start = start
        elif text != first:
            return (None, 'repeated_span_style_ambiguous')
        occurrences += 1
        start = source_norm.find(normalized, start + 1)
    return ({'text': first, 'startInNormalizedSource': first_start, 'samePresentationOccurrences': occurrences}, 'matched')

def project_lines(payload, source_norm, ranges, tables=()):
    """Match maximal source runs; bind repeated headers to their actual physical table."""
    bits = payload.splitlines(keepends=True)
    runs = []
    index = 0
    offset = 0
    while index < len(bits):
        if not normalize(bits[index])[0]:
            runs.append({'raw': bits[index], 'offset': offset, 'empty': True})
            offset += len(bits[index])
            index += 1
            continue
        if source_norm.find(normalize(bits[index])[0]) < 0:
            return (None, 'multiline_no_body_match')
        lo = index + 1
        hi = len(bits) + 1
        while lo + 1 < hi:
            middle = (lo + hi) // 2
            candidate = normalize(''.join(bits[index:middle]))[0]
            if source_norm.find(candidate) >= 0:
                lo = middle
            else:
                hi = middle
        raw = ''.join(bits[index:lo])
        (pn, pm) = normalize(raw)
        (result, status) = project(raw, pn, pm, source_norm, ranges)
        runs.append({'raw': raw, 'normalized': pn, 'mapping': pm, 'offset': offset, 'result': result, 'status': status})
        offset += len(raw)
        index = lo
    for (i, run) in enumerate(runs):
        if run.get('empty') or run['result'] is not None:
            continue
        if run['status'] != 'repeated_span_style_ambiguous':
            return (None, 'multiline_' + run['status'])
        following = next((x for x in runs[i + 1:] if not x.get('empty') and x['result'] is not None and (x['result']['samePresentationOccurrences'] == 1)), None)
        candidates = []
        if following:
            anchor = following['result']['startInNormalizedSource']
            end = anchor + len(normalize(following['raw'].splitlines()[0])[0])
            for table in tables:
                if table['headerPlain'] == run['normalized'] and table['start'] <= anchor and (end <= table['end']):
                    (result, status) = project(run['raw'], run['normalized'], run['mapping'], table['headerPlain'], ScriptRanges(table['headerRoles']))
                    if result is not None:
                        candidates.append((result, table))
        if not candidates:
            return (None, 'multiline_' + run['status'])
        texts = {x[0]['text'] for x in candidates}
        if len(texts) != 1:
            return (None, 'actual_table_header_presentation_ambiguous')
        (result, table) = candidates[0]
        run['result'] = dict(result, headerSourceBinding={k: table[k] for k in ('path', 'sha256', 'locator', 'start', 'end')})
        run['status'] = 'matched'
    parts = []
    spans = []
    for run in runs:
        if run.get('empty'):
            parts.append(run['raw'])
            continue
        result = run['result']
        parts.append(result['text'])
        spans.append({'payloadStart': run['offset'], 'payloadEnd': run['offset'] + len(run['raw']), **{k: v for (k, v) in result.items() if k != 'text'}})
    text = ''.join(parts)
    if TAG.sub('', text) != payload:
        raise ValueError('run projection plain text changed')
    return ({'text': text, 'sourceLineSpans': spans, 'projectionMethod': 'maximal_source_runs_with_exact_actual_table_header_context_all_candidate_presentations_equal'}, 'matched')
