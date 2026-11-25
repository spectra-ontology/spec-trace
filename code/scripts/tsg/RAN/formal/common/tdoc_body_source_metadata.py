#!/usr/bin/env python3
"""tdoc_body_source_metadata.py — keep registered and body-cover metadata distinct.

Spec: retained Phase-1 registration and SHA-bound Phase-6/8 source documents.
Ontology: document registration, retained source identity and approval scope are separate.
Cycle: per-view source ledger → recheck bytes/cover/facts → metadata-only projection.
배경: a retained body can have a different title or CR revision from a registration.
사용: overlays(root, wg, view); overlay_payload(payload, projection).
LLM 호출: none. Local evidence reads only; no embeddings or database writes.
"""
from __future__ import annotations

import copy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re

FIELDS = ('title', 'specNumber', 'crNumber', 'crRevision', 'release')
OVERLAY_KEYS = frozenset(('title', 'registeredTitle', 'coverSourceTitle',
                          'sourceMetadataStatus', 'bodySourceMetadata'))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda: stream.read(1 << 20), b''):
            h.update(part)
    return h.hexdigest()


def clean(value):
    return ' '.join(value.split()) if isinstance(value, str) else value


def checked(root, item):
    path = root / item['path']
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Body-source evidence must be a retained repository file')
    if sha(path) != item['sha256']:
        raise ValueError('Body-source evidence SHA changed: ' + item['path'])
    return path


def registered_facts(node):
    def endpoint(key, prefix, replacement):
        value = node.get(key)
        return value.removeprefix(prefix).replace('_', replacement) if isinstance(value, str) else None
    return dict(title=node.get('tdoc:title'),
                specNumber=endpoint('modifies', 'tdoc:spec/', '.'),
                crNumber=node.get('tdoc:crNumber'), crRevision=node.get('tdoc:crRevision'),
                release=endpoint('targetRelease', 'tdoc:release/', '-'))


def cover_facts(texts):
    """Read explicit cover fields, retaining unassigned values without guessing zero."""
    result = {field: dict(value=None, sourceValue=None, locator=None) for field in FIELDS}
    for index, text in enumerate(texts[:8]):
        locator = f'word/document.xml accepted body blocks [{index},{index + 1})'
        title = re.search(r'(?:^|\|)\s*Title:\s*(?:\|\s*|[\t ]+)([^\n|]+)', text, re.I | re.M)
        if title:
            result['title'] = dict(value=clean(title[1]), sourceValue=title[1], locator=locator)
        header = re.search(r'\|\s*(?:(?:TS|TR)\s*)?(\d{2}\.\d{3}(?:-\d+)?)\s*\|\s*'
                           r'(?:CR|draftCR|darftCR)\s*\|\s*([^|]*)\|\s*(?:⌘\s*)?rev\s*\|\s*'
                           r'([^|]*)\|\s*(?:⌘\s*)?Current version:', text, re.I)
        if header:
            for field, raw in zip(('specNumber', 'crNumber', 'crRevision'), header.groups()):
                raw = raw.strip()
                number = re.fullmatch(r'CR\s*(\d+)', raw, re.I) if field == 'crNumber' else None
                value = number[1] if number else raw if field == 'specNumber' or raw.isdigit() else None
                result[field] = dict(value=value, sourceValue=raw, locator=locator)
        release = re.search(r'Release:\s*\|\s*<?\s*(Rel-\s*\d+)\b', text, re.I)
        if release:
            result['release'] = dict(value=re.sub(r'\s+', '', release[1]), sourceValue=release[1], locator=locator)
    return result


def own_frontmatter(texts):
    """Read current labels before the CR form, keeping explicit predecessors separate.

    Covers can start with an empty paragraph or put the current number on the
    location line. The observed ``Revision of`` field names a predecessor, not
    another current document. Technical-body references never enter this scope.
    Non-CR views retain the existing first-block scope.
    """
    marker = re.compile(r'CR[-\s]*Form\b|CHANGE\s+REQUEST\b|'
                        r'\|\s*(?:TS\s*|TR\s*)?\d{2}\.\d{3}(?:-\d+)?\s*\|\s*'
                        r'(?:CR|draftCR|darftCR)\s*\|', re.I)
    parts, indices, found = [], [], False
    for index, text in enumerate(texts[:8]):
        match = marker.search(text)
        if match:
            if match.start():
                parts.append(text[:match.start()]); indices.append(index)
            found = True
            break
        parts.append(text); indices.append(index)
    if not found:
        parts, indices = list(texts[:1]), list(range(min(1, len(texts))))
    text = '\n'.join(parts)
    identifier = r'(?<![\w-])R[1-5]-\s*\d{6,8}(?![\w-])'
    predecessors = []
    def predecessor(match):
        predecessors.extend(re.sub(r'\s', '', value) for value in re.findall(identifier, match[0]))
        return ''
    current = re.sub(r'\brevision\s+of\s+' + identifier, predecessor, text, flags=re.I)
    # The first numbered header line is the own label. Later frontmatter may
    # identify a related RAN3 document or an earlier revision of this CR.
    own = []
    for line in re.split(r'[\r\n]', current):
        own = [re.sub(r'\s', '', value) for value in re.findall(identifier, line)]
        if own:
            break
    return dict(ownIds=own, predecessorIds=predecessors, blocks=indices)


def source_cover(root, source):
    """Re-read the same source view; every quoted accepted block is checked."""
    from decision_disposition import source_blocks
    path = checked(root, source)
    if source.get('kind', 'docx') != 'docx':
        raise ValueError('Only retained Word bodies are currently indexed by this overlay')
    try:
        texts, digest, _ = source_blocks(str(path.resolve()))
        if digest != source['sha256']:
            raise ValueError('Cached body-source bytes changed')
        for evidence in source['evidence']:
            match = re.fullmatch(r'word/document.xml accepted body blocks \[(\d+),(\d+)\)', evidence['locator'])
            if not match or int(match[2]) != int(match[1]) + 1 or texts[int(match[1])] != evidence['quote']:
                raise ValueError('Body-source cover quote/locator changed')
        actual = cover_facts(texts)
        header = own_frontmatter(texts)
        own = header['ownIds']
        if actual != source['facts'] or own != source['ownIds']:
            raise ValueError('Body-source cover facts changed')
        if 'predecessorIds' in source and header['predecessorIds'] != source['predecessorIds']:
            raise ValueError('Body-source predecessor labels changed')
        return actual, own
    finally:
        source_blocks.cache_clear()


def stale_envelope(root, row, source):
    """Permit stale own headers only for the enumerated, byte-bound official envelope."""
    import zipfile
    envelope = source.get('officialEnvelope')
    if not envelope or Path(envelope['path']).name != row['target'] + '.zip':
        raise ValueError('Stale own header lacks a target-numbered official envelope')
    path = checked(root, envelope)
    with zipfile.ZipFile(path) as package:
        data = package.read(envelope['zipMember'])
    if hashlib.sha256(data).hexdigest() != envelope['memberSha256']:
        raise ValueError('Official envelope member changed')
    native = checked(root, dict(path=envelope['exactDerivedNativePath'], sha256=envelope['memberSha256']))
    target_name = re.search(r'(?<![A-Za-z0-9-])' + re.escape(row['target']) + r'(?![A-Za-z0-9-])', Path(source['path']).stem)
    if native.read_bytes() != data or not target_name:
        raise ValueError('Official envelope does not bind this source')
    if native.suffix.lower() == '.docx':
        if envelope['memberSha256'] != source['sha256']:
            raise ValueError('Official OOXML member differs from source bytes')
    elif native.suffix.lower() == '.doc':
        import cr_word_title
        head = cr_word_title._head(str(native))
        shown = cr_word_title._shown(head or '')
        if cr_word_title.doc_title(str(native)) != source['facts']['title']['value']:
            raise ValueError('Native DOC and converted cover titles differ')
        own = own_frontmatter([shown])['ownIds']
        if own != source['ownIds']:
            raise ValueError('Native DOC and converted cover own IDs differ')
        # Cell delimiters survive the native Word story decoder. Bind the assigned
        # CR tuple directly to that original member, not just the conversion name.
        match = re.search(r'(\d{2}\.\d{3}(?:-\d+)?)\s*\x07CR\s*\x07(\d+)\s*\x07rev\s*\x07(\d+)', shown)
        if not match or tuple(match.groups()) != tuple(source['facts'][f]['value'] for f in ('specNumber', 'crNumber', 'crRevision')):
            raise ValueError('Native DOC and converted CR tuples differ')
    else:
        raise ValueError('Unsupported official source member')


def status(field, registered, cover):
    value = cover['value']
    if value is None:
        return 'cover_unassigned' if cover['sourceValue'] is not None else 'cover_not_declared'
    if registered in (None, '', '(reserved)'):
        return 'registration_placeholder' if registered == '(reserved)' else 'registration_not_declared'
    left, right = clean(str(registered)).casefold(), clean(str(value)).casefold()
    if field in ('crNumber', 'crRevision') and left.isdigit() and right.isdigit():
        left, right = str(int(left)), str(int(right))
    return 'same_value' if left == right else 'different_values'


def ledger_path(root, wg):
    return root / f'ontology/input/tsg/RAN/formal/meetings/{wg}/tdoc_body_source_metadata.json'


@lru_cache(maxsize=12)
def overlays(root, wg, view):
    """Validate per-view original covers and unchanged registration facts once per process."""
    root = Path(root)
    if view not in ('tdoc', 'cr'):
        raise ValueError('Explicit tdoc or cr source view required')
    path = ledger_path(root, wg)
    if not path.exists():
        return {}
    ledger_sha = sha(path)
    ledger = json.loads(path.read_text())
    if ledger.get('schema') != 1 or ledger.get('wg') != wg:
        raise ValueError('Invalid body-source metadata ledger')
    rows = ledger['records']
    if len({row['target'] for row in rows}) != len(rows):
        raise ValueError('Duplicate body-source target')
    phase1 = root / f'ontology/output/tsg/RAN/formal/instances/phase-1/{wg}/tdocs.jsonld'
    nodes = {node['@id']: node for node in json.loads(phase1.read_text())['@graph']}
    generation = sha(phase1)
    result = {}
    for row in rows:
        source = row['views'].get(view)
        if source is None:
            continue
        if not re.fullmatch('R' + wg[-1] + r'-\d{6,8}', row['target']):
            raise ValueError('Body-source target outside ledger working group')
        registered = registered_facts(nodes['tdoc:' + row['target']])
        if registered != row['registeredFacts']:
            raise ValueError('Registration facts changed; body-source ledger needs review: ' + row['target'])
        facts, own = source_cover(root, source)
        identity = 'target_own_id_matches'
        if row['target'] not in own:
            stale_envelope(root, row, source)
            identity = 'official_envelope_with_stale_own_id'
        fields = {field: status(field, registered[field], facts[field]) for field in FIELDS}
        provenance = dict(schema=1, view=view, ledger=dict(path=path.relative_to(root).as_posix(), sha256=ledger_sha),
            sourceIdentityStatus=identity, decisionAttributionStatus=row['decisionIdentityStatus'],
            registered=dict(values=registered, evidence=dict(path=phase1.relative_to(root).as_posix(),
                sha256=generation, nodeId='tdoc:' + row['target'], factsSha256=hashlib.sha256(canonical(registered)).hexdigest())),
            cover=dict(values={f: facts[f]['value'] for f in FIELDS}, ownIds=own,
                evidence=dict(path=source['path'], sha256=source['sha256']), fields=facts), fieldStatus=fields)
        result[row['target']] = dict(registeredTitle=registered['title'], coverSourceTitle=facts['title']['value'],
            sourceMetadataStatus='different_or_partial_metadata' if any(s != 'same_value' for s in fields.values()) else 'matching_metadata',
            bodySourceMetadata=provenance)
    if sha(phase1) != generation or sha(path) != ledger_sha:
        raise ValueError('Registration or source ledger changed during metadata validation')
    return result


def overlay_payload(payload, projection):
    """Keep every body, point/chunk identity and unknown field; show the cover title."""
    after = dict(payload)
    after.update(copy.deepcopy(projection))
    if projection['coverSourceTitle']:
        after['title'] = projection['coverSourceTitle']
    if {k: v for k, v in after.items() if k not in OVERLAY_KEYS} != {k: v for k, v in payload.items() if k not in OVERLAY_KEYS}:
        raise ValueError('Body-source projection changed an unrelated field')
    return after


def project(root, wg, view, target, payload):
    projection = overlays(Path(root), wg, view).get(target)
    return overlay_payload(payload, projection) if projection is not None else dict(payload)


def validate_source_selection(root, wg, view, target, paths):
    """A new source variant needs review before inheriting an older cover projection."""
    projection = overlays(Path(root), wg, view).get(target)
    if projection is None:
        return
    expected = (Path(root) / projection['bodySourceMetadata']['cover']['evidence']['path']).resolve()
    if len(paths) != 1 or Path(paths[0]).resolve() != expected:
        raise ValueError('Body-source selection differs from reviewed per-view source: ' + target)


def source_inputs(root, wg):
    """Current byte-generation fences for validated per-view source metadata."""
    root = Path(root)
    path = ledger_path(root, wg)
    if not path.exists():
        return {}
    # Revalidation is explicit for one-shot maintenance tools. Producer processes
    # can retain the immutable validated mapping in their normal generation.
    overlays.cache_clear()
    overlays(root, wg, 'tdoc'); overlays(root, wg, 'cr')
    files = {path, root / f'ontology/output/tsg/RAN/formal/instances/phase-1/{wg}/tdocs.jsonld', Path(__file__)}
    for row in json.loads(path.read_text())['records']:
        for source in row['views'].values():
            files.add(root / source['path'])
            envelope = source.get('officialEnvelope')
            if envelope:
                files.add(root / envelope['path']); files.add(root / envelope['exactDerivedNativePath'])
    return {p.relative_to(root).as_posix(): sha(p) for p in files}
