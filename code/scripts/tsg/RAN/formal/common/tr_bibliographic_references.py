#!/usr/bin/env python3
"""tr_bibliographic_references.py — bind a bibliography's cited work to its identifier.

Spec: Phase-5 References extraction; bibliography entries retain their original text.
Ontology: referencesTR denotes a cited TechnicalReport, not a title mentioning one.
Cycle: References paragraphs → leading cited identifier → corpus TR endpoint.
배경: a contribution titled 'TP to TR …' cites that contribution as the work.
사용: direct_tr_references(sections, corpus_numbers).
LLM 호출: none; pure text processing, no source or database writes.
"""
from __future__ import annotations

import re

_HEADING = re.compile(r'^(?:\d+\s+)?references?$', re.I)
_CITED_TR = re.compile(
    r'^\s*(?:\[[^\]\r\n]+\]\s*)?(?:3GPP\s+)?TR\s+'
    r'(\d{2}\.\d{3}(?:-\d+)*)(?![\w-]|\.\d)', re.I)


def direct_tr_references(sections, corpus_numbers):
    """Read each entry's leading work identifier; preserve its title as source text."""
    found = set()
    for heading, paragraphs in sections.items():
        if not _HEADING.fullmatch(heading.strip()):
            continue
        for paragraph in paragraphs:
            # Multiple numbered entries can occupy one Word paragraph. A title
            # following an R4/RP identifier never becomes a new cited work.
            entries = re.split(r'(?=\[[0-9]+\])', paragraph)
            for entry in entries:
                match = _CITED_TR.match(entry)
                if match and match[1] in corpus_numbers:
                    found.add(match[1])
    return sorted(found)


def reconcile_reviewed_citations(root, review_path, output, *, apply=False):
    """Replay retained sources, then change only disproven bibliography endpoints.

    The retained review selects the source documents; it never supplies replacement
    triples. Each replacement is derived again from the native Word document.
    Live data is read for comparison and is never written by this utility.
    """
    import copy
    import gzip
    import hashlib
    import importlib.util
    import json
    import sys
    from pathlib import Path
    from common.atomic_io import write_text_atomic
    from common import axis, credentials
    from neo4j import GraphDatabase, READ_ACCESS
    import docx_text

    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    root, review_path, output = Path(root).resolve(), Path(review_path).resolve(), Path(output).resolve()
    review_bytes = review_path.read_bytes()
    review = json.loads(review_bytes)
    pins = {review_path: hashlib.sha256(review_bytes).hexdigest(),
            Path(__file__): sha(Path(__file__))}
    sources, desired, original_pairs = [], {}, review['canonicalPairs']
    for wg in original_pairs:
        desired[wg] = set()
    modules = {}
    for row in review['sourceDocuments']:
        wg, number = row['wg'], row['trNumber']
        path = root / row['source']['path']
        if sha(path) != row['source']['sha256']:
            raise ValueError('Reviewed native source changed: ' + str(path))
        pins[path] = sha(path)
        if wg not in modules:
            producer = root / f'scripts/tsg/RAN/formal/{wg}/phase-5/tr-parser/01_parse_tr_docs.py'
            spec = importlib.util.spec_from_file_location('tr_citations_' + wg, producer)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            modules[wg] = module
            pins[producer] = sha(producer)
        module = modules[wg]
        document = docx_text.open_document(str(path))
        extractor = getattr(module, 'extract_heading1_sections', None) or module.extract_sections_by_heading
        sections = extractor(document)
        corpus = {a for pair in original_pairs[wg] for a in pair}
        references = direct_tr_references(sections, corpus)
        desired[wg].update((number, target) for target in references)
        sources.append({'wg': wg, 'trNumber': number, 'path': path.relative_to(root).as_posix(),
                        'sha256': pins[path], 'directReferences': references})
    changes, projections, live = [], [], {}
    for wg, pairs in original_pairs.items():
        old = set(map(tuple, pairs))
        if not desired[wg] <= old:
            raise ValueError('New citations require a separate source review')
        with GraphDatabase.driver(axis.bolt_uri(wg), auth=credentials.neo4j_auth()) as driver:
            with driver.session(default_access_mode=READ_ACCESS) as session:
                live[wg] = sorted((r['source'], r['target']) for r in session.run(
                    'MATCH(a:TechnicalReport)-[:REFERENCES_TR]->(b:TechnicalReport) '
                    'RETURN a.trNumber AS source,b.trNumber AS target'))
        if set(live[wg]) != desired[wg]:
            raise ValueError('Live citations differ from source-verified direct bibliography')
        if old == desired[wg]:
            continue
        parsed = root / f'ontology/output/tsg/RAN/formal/parsed_tr/{wg}/tr_documents.json'
        canonical = root / f'ontology/output/tsg/RAN/formal/instances/phase-5/{wg}/tr_ontology.jsonld'
        for path, is_rdf in ((parsed, False), (canonical, True)):
            raw = path.read_bytes()
            value = json.loads(raw)
            before = copy.deepcopy(value)
            rows = value['@graph'] if is_rdf else value
            observed = set()
            for node in rows:
                source = node.get('trNumber') or node.get('@id', '').removeprefix('tr:')
                refs = node.get('referencesTR', [])
                targets = [(a.get('@id', '').removeprefix('tr:') if isinstance(a, dict) else a) for a in refs]
                observed.update((source, target) for target in targets)
                filtered = [a for a, target in zip(refs, targets) if (source, target) in desired[wg]]
                if filtered != refs:
                    node['referencesTR'] = filtered
                    changes.append({'path': path.relative_to(root).as_posix(), 'sourceTR': source,
                                    'before': refs, 'after': filtered})
            if observed != old:
                raise ValueError('Canonical citation generation differs from reviewed input')
            # Structural comparison proves every other field is retained.
            for a, b in zip((before['@graph'] if is_rdf else before), rows):
                if {k: v for k, v in a.items() if k != 'referencesTR'} != {k: v for k, v in b.items() if k != 'referencesTR'}:
                    raise ValueError('Non-citation field changed')
            pins[path] = hashlib.sha256(raw).hexdigest()
            projections.append((path, raw, json.dumps(value, ensure_ascii=False, indent=2) + '\n'))
    output.mkdir(parents=True, exist_ok=True)
    if (output / 'plan.json').exists() or (output / 'result.json').exists():
        raise ValueError('Citation receipt directory already contains a plan/result')
    for path, raw, encoded in projections:
        backup = output / (path.parent.name + '_' + path.name + '.before.gz')
        if backup.exists():
            if gzip.decompress(backup.read_bytes()) != raw:
                raise ValueError('Existing preimage differs from current canonical bytes')
        else:
            with gzip.open(backup, 'wb') as stream:
                stream.write(raw)
    def fence():
        for path, expected in pins.items():
            if sha(path) != expected:
                raise ValueError('Citation input changed before write: ' + str(path))
    fence()
    report = {'status': 'planned', 'nativeSourcesReplayed': len(sources), 'sources': sources,
              'sourcePairsBefore': sum(map(len, original_pairs.values())),
              'directPairsAfter': sum(map(len, desired.values())), 'changes': changes,
              'livePairs': live, 'databaseWrites': 0,
              'inputSHA256': {str(p.relative_to(root)): h for p, h in pins.items()}}
    write_text_atomic(output / 'plan.json', json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if apply:
        written = []
        try:
            fence()
            for path, raw, encoded in projections:
                if sha(path) != pins[path]:
                    raise ValueError('Canonical citation CAS failed')
                written.append((path, raw, hashlib.sha256(encoded.encode()).hexdigest()))
                write_text_atomic(path, encoded)
            for path, raw, digest in written:
                if sha(path) != digest:
                    raise ValueError('Canonical citation readback failed')
            report['status'] = 'complete'
            report['outputSHA256'] = {str(p.relative_to(root)): sha(p) for p, _, _ in projections}
        except BaseException:
            for path, raw, digest in reversed(written):
                if sha(path) == digest:
                    write_text_atomic(path, raw.decode())
            raise
    write_text_atomic(output / 'result.json', json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    import argparse
    from pathlib import Path
    import sys
    root = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
    sys.path.insert(0, str(root / 'scripts/common'))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    result = reconcile_reviewed_citations(root, args.review, args.out, apply=args.apply)
    print({k: result[k] for k in ('status', 'nativeSourcesReplayed', 'sourcePairsBefore', 'directPairsAfter', 'databaseWrites')})
