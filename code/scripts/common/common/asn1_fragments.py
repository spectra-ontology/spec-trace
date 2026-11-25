#!/usr/bin/env python3
"""asn1_fragments.py — lossless bounded ASN.1 source fragments and assembly.

Spec: encoder budget and complete source-definition preservation.
Ontology: one ASN.1 type has one primary chunk and ordered source fragments.
Cycle: complete definition → field-boundary fragments → verified ordered assembly.
배경: large ASN.1 SEQUENCE definitions exceed the local encoder input window.
사용: fragment_definition / assemble_definition / fetch_definition; no writes.
LLM 호출: 없음. Caller supplies the actual local tokenizer measurement.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import re

if __package__:
    from .qdrant_generation import check_scroll_progress
else:
    from qdrant_generation import check_scroll_progress


def text_sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _line_code(line):
    """Discard ASN.1 comments and quoted literals only for scope accounting."""
    out, quote, index = [], None, 0
    while index < len(line):
        char = line[index]
        if quote:
            if char == quote:
                if index + 1 < len(line) and line[index + 1] == quote:
                    index += 2
                    continue
                quote = None
            index += 1
            continue
        if line[index:index + 2] == '--':
            break
        if char in ('"', "'"):
            quote = char
        else:
            out.append(char)
        index += 1
    if quote:
        raise ValueError('ASN.1 literal crosses a paragraph boundary')
    return ''.join(out)


def boundaries(text):
    """Safe cuts after whole outer fields, with explicit extension-group scope.

    A nested SEQUENCE/CHOICE/ENUMERATED is kept whole. Extension additions may
    span fragments, whose inherited [[ group number is recorded explicitly.
    An unsupported large single field fails before any source is changed.
    """
    header = re.match(r'^([A-Z][A-Za-z0-9-]*)\s*::=\s*SEQUENCE\s*\{', text)
    if not header:
        raise ValueError('bounded fragments currently require an outer SEQUENCE')
    depth, group, ordinal, offset = 0, None, 0, 0
    result = [(0, None)]
    for line in text.splitlines(keepends=True):
        code = _line_code(line)
        index = 0
        while index < len(code):
            pair = code[index:index + 2]
            if pair == '[[':
                if depth != 1 or group is not None:
                    raise ValueError('unsupported nested ASN.1 extension group')
                ordinal += 1
                group = ordinal
                index += 2
                continue
            if pair == ']]':
                if depth != 1 or group is None:
                    raise ValueError('unbalanced ASN.1 extension group')
                group = None
                index += 2
                continue
            if code[index] == '{':
                depth += 1
            elif code[index] == '}':
                depth -= 1
            if depth < 0:
                raise ValueError('unbalanced ASN.1 braces')
            index += 1
        offset += len(line)
        if code.strip() and depth in (0, 1):
            result.append((offset, group))
    if depth or group is not None or result[-1][0] != len(text):
        raise ValueError('incomplete ASN.1 definition boundary')
    return header.group(1), result


def context_text(name, extension_group):
    scope = 'outer SEQUENCE'
    if extension_group is not None:
        scope += f'; inherited extension addition group {extension_group} ([[ ... ]])'
    return (f'[ASN.1 source fragment of {name} ::= SEQUENCE; scope at fragment start: {scope}. '
            'Partial source text; ordered sourceText ranges reconstruct the complete definition.]')


def fragment_definition(chunk, count, maximum=6500):
    """Keep unchanged definitions exact; split only over-budget full definitions."""
    text = chunk['text']
    if count(text) <= maximum:
        return [chunk]
    name, cuts = boundaries(text)
    if name != chunk['asn1']['ieName']:
        raise ValueError('source declaration and ASN.1 type identity differ')
    pieces, start_index = [], 0
    while start_index < len(cuts) - 1:
        start, group = cuts[start_index]
        context = context_text(name, group)
        end_index = start_index
        for candidate in range(start_index + 1, len(cuts)):
            body = context + '\n' + text[start:cuts[candidate][0]]
            if count(body) > maximum:
                break
            end_index = candidate
        if end_index == start_index:
            raise ValueError('complete ASN.1 outer field exceeds encoder budget')
        end = cuts[end_index][0]
        pieces.append((start, end, group, context))
        start_index = end_index
    primary = chunk['chunkId']
    if not primary.endswith('-001'):
        raise ValueError('primary ASN.1 identity must end with -001')
    result = []
    for index, (start, end, group, context) in enumerate(pieces, 1):
        row = deepcopy(chunk)
        row.update(chunkId=primary if index == 1 else primary[:-3] + f'{index:03d}',
            chunkIndex=index, totalChunks=len(pieces), sourceUnitKind='asn1_source_fragment',
            sourceText=text[start:end], text=context + '\n' + text[start:end])
        row['sourceFragment'] = dict(schema=1, primaryChunkId=primary, typeName=name,
            fragmentIndex=index, fragmentCount=len(pieces), sourceStart=start, sourceEnd=end,
            definitionLength=len(text), definitionSHA256=text_sha(text),
            sourceTextSHA256=text_sha(row['sourceText']), extensionGroupAtStart=group,
            contextText=context, boundaryKind='complete_outer_field')
        if count(row['text']) > maximum:
            raise ValueError('final ASN.1 fragment exceeds encoder budget')
        result.append(row)
    assemble_definition(result)
    return result


def assemble_definition(payloads):
    """Validate every fragment and return the exact complete source definition.

    The returned full text is a retrieval view, never an encoder input. A partial
    or mixed-edition fragment population raises instead of returning a definition.
    """
    rows = sorted(payloads, key=lambda row: row.get('sourceFragment', {}).get('fragmentIndex', 0))
    if not rows or any('sourceFragment' not in row for row in rows):
        raise ValueError('ordered ASN.1 fragments are required')
    first = rows[0]
    receipt = first['sourceFragment']
    expected_count = receipt['fragmentCount']
    if len(rows) != expected_count or receipt['primaryChunkId'] != first['chunkId']:
        raise ValueError('incomplete ASN.1 fragment population')
    offset, raw = 0, []
    stable = ('primaryChunkId', 'typeName', 'fragmentCount', 'definitionLength', 'definitionSHA256')
    for index, row in enumerate(rows, 1):
        item = row['sourceFragment']
        if any(item.get(key) != receipt.get(key) for key in stable):
            raise ValueError('mixed ASN.1 fragment identity')
        if any(row.get(key) != first.get(key) for key in ('specNumber', 'sectionId', 'tsSectionNumber', 'asn1', 'sourceDefinition')):
            raise ValueError('mixed ASN.1 fragment source or type')
        text = row['sourceText']
        if (item['fragmentIndex'] != index or row['chunkIndex'] != index or row['totalChunks'] != expected_count
                or item['sourceStart'] != offset or item['sourceEnd'] != offset + len(text)
                or item['sourceTextSHA256'] != text_sha(text)
                or row['text'] != item['contextText'] + '\n' + text):
            raise ValueError('invalid ASN.1 fragment range or source text')
        expected_cid = receipt['primaryChunkId'][:-3] + f'{index:03d}'
        if row['chunkId'] != expected_cid:
            raise ValueError('invalid ASN.1 continuation identity')
        raw.append(text)
        offset += len(text)
    text = ''.join(raw)
    if len(text) != receipt['definitionLength'] or text_sha(text) != receipt['definitionSHA256']:
        raise ValueError('ASN.1 definition reconstruction changed source')
    name, cuts = boundaries(text)
    if name != receipt['typeName'] or name != first['asn1']['ieName']:
        raise ValueError('source declaration and ASN.1 type identity differ')
    scopes = dict(cuts)
    for row in rows:
        item = row['sourceFragment']
        if (item['sourceStart'] not in scopes or item['sourceEnd'] not in scopes
                or item['extensionGroupAtStart'] != scopes[item['sourceStart']]
                or item['contextText'] != context_text(item['typeName'], scopes[item['sourceStart']])):
            raise ValueError('ASN.1 fragment scope does not match its complete source')
    return text


def fetch_definition(client, collection, payload):
    """Fetch all exact primary-linked continuations and expose a complete view."""
    if not payload.get('sourceFragment'):
        return payload
    from qdrant_client import models
    primary = payload['sourceFragment']['primaryChunkId']
    query = models.Filter(must=[models.FieldCondition(key='sourceFragment.primaryChunkId',
        match=models.MatchValue(value=primary))])
    rows, offset = [], None
    seen_offsets = set()
    while True:
        points, offset = client.scroll(collection_name=collection, scroll_filter=query,
            offset=offset, limit=128, with_payload=True, with_vectors=False)
        check_scroll_progress(offset, seen_offsets)
        rows.extend(point.payload for point in points)
        if offset is None:
            break
    text = assemble_definition(rows)
    first = next(row for row in rows if row['chunkId'] == primary)
    view = deepcopy(first)
    view.update(text=text, sourceUnitKind='asn1_definition',
        assembledSourceFragments=[row['chunkId'] for row in sorted(rows, key=lambda row: row['chunkIndex'])])
    view['sourceFragment']['assembledRetrievalView'] = True
    return view
