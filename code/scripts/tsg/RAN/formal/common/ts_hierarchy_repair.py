#!/usr/bin/env python3
"""ts_hierarchy_repair.py — repair an explicitly reviewed non-leaf TS closure.

Spec: Phase-3 Section hierarchy and source-preserving incremental reconciliation.
Ontology: release-qualified Section identity, parentSection/hasSubSection inverses.
Cycle: native headings + full parsed preimage → exact owned delta → guarded readback.
배경: a fused heading can hide a parent and flatten all its descendants.
사용: --source-plan retained-plan.json --out new-receipt-directory [--apply].
LLM 호출: none. No embeddings, source edits, broad reloads, or foreign-edge removal.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import gc
import gzip
import hashlib
import json
from pathlib import Path
import sys
import zipfile
from xml.etree import ElementTree as ET

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())
sys.path.insert(0, str(ROOT / 'scripts/common'))
from common import axis, credentials, review_artifacts
from common.atomic_io import write_text_atomic
import docx_text


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def project_sections(document, review):
    """Accept only complete before-images and a connected, unchanged-identity closure."""
    result = copy.deepcopy(document)
    rows = {s['sectionId']: s for s in result['sections']}
    if len(rows) != len(result['sections']):
        raise ValueError('Duplicate canonical Section identity')
    selected = set()
    for update in review['updates']:
        sid = update['sectionId']
        if sid in selected or rows.get(sid) != update['before']:
            raise ValueError('Reviewed Section preimage differs from current canonical input')
        selected.add(sid)
        before, after = update['before'], update['after']
        delta = {k for k in before.keys() | after.keys() if before.get(k) != after.get(k)}
        if not delta <= {'level', 'parentSectionId', 'childSectionIds'}:
            raise ValueError('Hierarchy repair would change a non-owned Section field')
        if update['deltas'] != {k: {'before': before[k], 'after': after[k]} for k in delta}:
            raise ValueError('Declared Section delta differs from its full preimages')
        rows[sid] = copy.deepcopy(after)
    for section in review['addedSections']:
        sid = section['sectionId']
        if sid in rows or sid in selected:
            raise ValueError('New Section is already present')
        rows[sid] = copy.deepcopy(section)
        selected.add(sid)
    if review.get('removedSectionIds'):
        raise ValueError('Hierarchy closure repair never deletes a Section')
    prefix = f"{document['spec_number']}-{document['release']}-"
    for sid in selected:
        section = rows[sid]
        number = section['sectionNumber']
        if sid != prefix + number or section['level'] != number.count('.') + 1:
            raise ValueError('Section identity/depth does not match the source number')
        parent = section['parentSectionId']
        expected_parent = prefix + number.rsplit('.', 1)[0] if '.' in number else None
        if parent != expected_parent or parent and parent not in rows:
            raise ValueError('Hierarchy closure lacks the exact immediate numbered parent')
        children = sorted(s['sectionId'] for s in rows.values() if s['parentSectionId'] == sid)
        if children != sorted(section['childSectionIds']):
            raise ValueError('Parent/child inverse projections disagree')
    # The parser's original ordering is retained; only new source sections are inserted.
    order = [s['sectionId'] for s in document['sections']]
    for section in review['addedSections']:
        descendants = [i for i, sid in enumerate(order) if sid.startswith(section['sectionId'] + '.')]
        if not descendants:
            raise ValueError('Non-leaf closure addition lacks its existing descendant boundary')
        order.insert(min(descendants), section['sectionId'])
    result['sections'] = [rows[sid] for sid in order]
    result['stats']['sections'] = len(result['sections'])
    return result, selected


def snapshot(tx, ids, spec, release):
    nodes = tx.run('MATCH(n:Section) WHERE n.sectionId IN $ids '
                   'RETURN elementId(n) AS eid,labels(n) AS labels,properties(n) AS properties ORDER BY eid', ids=ids).data()
    for node in nodes:
        node['labels'].sort()
    edges = tx.run('MATCH(n:Section)-[r]-(m) WHERE n.sectionId IN $ids '
                   'WITH DISTINCT r RETURN elementId(r) AS eid,elementId(startNode(r)) AS start,'
                   'elementId(endNode(r)) AS end,type(r) AS type,properties(r) AS properties ORDER BY eid', ids=ids).data()
    specs = tx.run('MATCH(n:Spec {specNumber:$spec,specRelease:$release}) '
                   'RETURN elementId(n) AS eid,labels(n) AS labels,properties(n) AS properties',
                   spec=spec, release=release).data()
    for node in specs:
        node['labels'].sort()
    if len(specs) != 1:
        raise ValueError('Release-qualified Spec endpoint absent or ambiguous')
    return {'nodes': nodes, 'edges': edges, 'spec': specs[0]}


def verify_delta(before, after, review, spec_number):
    old = {n['properties']['sectionId']: n for n in before['nodes']}
    new = {n['properties']['sectionId']: n for n in after['nodes']}
    additions = {s['sectionId']: s for s in review['addedSections']}
    if len(old) != len(before['nodes']) or len(new) != len(after['nodes']) or new.keys() != old.keys() | additions.keys():
        raise ValueError('Section node population differs from the exact closure delta')
    if before['spec'] != after['spec']:
        raise ValueError('Spec endpoint changed')
    updates = {s['sectionId']: s['after'] for s in review['updates']}
    for sid, item in old.items():
        expected = copy.deepcopy(item)
        expected['properties']['level'] = updates[sid]['level']
        if new[sid] != expected:
            raise ValueError('Existing Section changed outside the reviewed level field')
    for sid, section in additions.items():
        expected = {k: section[k] for k in ('sectionId', 'sectionNumber', 'sectionTitle', 'level', 'isVoid')}
        expected.update(specNumber=spec_number, granularity='section')
        if new[sid]['properties'] != expected or new[sid]['labels'] != ['ConformanceTest', 'Section']:
            raise ValueError('New Section differs from maintained loader contract')
    removed, created = Counter(), Counter()
    eid = lambda sid: new[sid]['eid']
    for change in review['parentOwnershipDeltas']:
        sid, previous, parent = change['sectionId'], change['oldParent'], change['newParent']
        if previous:
            removed.update([(eid(sid), 'PARENT_SECTION', eid(previous)), (eid(previous), 'HAS_SUB_SECTION', eid(sid))])
        created.update([(eid(sid), 'PARENT_SECTION', eid(parent)), (eid(parent), 'HAS_SUB_SECTION', eid(sid))])
    for sid in additions:
        created.update([(eid(sid), 'BELONGS_TO_SPEC', after['spec']['eid'])])
    old_edges = {e['eid']: e for e in before['edges']}
    new_edges = {e['eid']: e for e in after['edges']}
    for identifier in old_edges.keys() & new_edges.keys():
        if old_edges[identifier] != new_edges[identifier]:
            raise ValueError('Existing incident edge properties changed')
    def signatures(edges, ids):
        result = Counter()
        for identifier in ids:
            edge = edges[identifier]
            if edge['properties']:
                raise ValueError('Qualified/foreign relationship would be replaced')
            result.update([(edge['start'], edge['type'], edge['end'])])
        return result
    if signatures(old_edges, old_edges.keys() - new_edges.keys()) != removed:
        raise ValueError('Removed relationships exceed the reviewed owned parent delta')
    if signatures(new_edges, new_edges.keys() - old_edges.keys()) != created:
        raise ValueError('Created relationships differ from the source closure')


def prepare(root, source_plan):
    review_bytes = source_plan.read_bytes()
    review = json.loads(review_bytes)
    pins = {source_plan: hashlib.sha256(review_bytes).hexdigest(), Path(__file__).resolve(): sha(__file__)}
    # Historical proofs preserve their original paths; the resolver verifies moved bytes.
    needed = ('parse_ts_docx.py', 'docx_text.py', 'ts_section_number.py', 'ts_citation.py')
    parsed = None
    sources = []
    for recorded, digest in review['sourceFences'].items():
        if recorded.endswith('.docx') or '/parsed_ts/' in recorded or Path(recorded).name in needed:
            path = review_artifacts.resolve_recorded_path(root, recorded, digest)
            pins[path] = digest
            if '/parsed_ts/' in recorded:
                parsed = path
            if recorded.endswith('_s16-s19.docx'):
                sources.append(path)
    if parsed is None or len(sources) != 1:
        raise ValueError('Missing canonical input or exact source part')
    original = parsed.read_bytes()
    document = json.loads(original)
    projected, selected = project_sections(document, review)
    with zipfile.ZipFile(sources[0]) as archive:
        xml = ET.fromstring(archive.read('word/document.xml'))
    paragraphs = list(xml.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'))
    headings = review['sourceHeadingEvidence']
    numbers = set()
    quotes = {}
    for evidence in headings:
        quote = docx_text.final_text(paragraphs[evidence['paragraphIndex']])
        if quote != evidence['quote']:
            raise ValueError('Native heading quote differs from its source locator')
        numbers.update(evidence['sourceNumbers'])
        for number in evidence['sourceNumbers']:
            quotes.setdefault(number, []).append(quote)
    for section in projected['sections']:
        if section['sectionId'] in selected and section['sectionNumber'] not in numbers:
            raise ValueError('Selected hierarchy Section has no native heading proof')
        if section['sectionId'] in selected and not any(
                section['sectionNumber'] + '\t' + section['sectionTitle'] in quote
                for quote in quotes[section['sectionNumber']]):
            raise ValueError('Native numbered heading does not support the Section title')
    del paragraphs, xml
    gc.collect()
    return review, pins, parsed, original, projected, selected


def run(source_plan, output, apply=False):
    from neo4j import GraphDatabase, READ_ACCESS
    source_plan, output = Path(source_plan).resolve(), Path(output).resolve()
    review, pins, parsed, raw, projected, selected = prepare(ROOT, source_plan)
    output.mkdir(parents=True, exist_ok=True)
    if (output / 'plan.json').exists() or (output / 'result.json').exists():
        raise ValueError('Hierarchy receipt directory already contains a plan/result')
    encoded = json.dumps(projected, ensure_ascii=False, indent=2) + '\n'
    proposed_sha = hashlib.sha256(encoded.encode()).hexdigest()
    backup = output / 'parsed.before.json.gz'
    if backup.exists():
        if gzip.decompress(backup.read_bytes()) != raw:
            raise ValueError('Existing canonical preimage differs from current bytes')
    else:
        with gzip.open(backup, 'wb') as stream:
            stream.write(raw)
    def fence(canonical_written=False):
        for path, digest in pins.items():
            expected = proposed_sha if canonical_written and path == parsed else digest
            if sha(path) != expected:
                raise ValueError('Source/code/canonical generation changed: ' + str(path))
    fence()
    with GraphDatabase.driver(axis.bolt_uri('RAN5'), auth=credentials.neo4j_auth()) as driver:
        with driver.session(**({} if apply else {'default_access_mode': READ_ACCESS})) as session:
            before = snapshot(session, sorted(selected), projected['spec_number'], projected['release'])
            old = {s['sectionId'] for s in review['updates']}
            if {n['properties']['sectionId'] for n in before['nodes']} != old:
                raise ValueError('Live Section population differs from reviewed current closure')
            for node in before['nodes']:
                section = next(s['before'] for s in review['updates'] if s['sectionId'] == node['properties']['sectionId'])
                for field in ('sectionNumber', 'sectionTitle', 'level', 'isVoid'):
                    if node['properties'].get(field) != section[field]:
                        raise ValueError('Live Section does not match full canonical preimage')
            report = {'status': 'planned', 'sourcePlan': str(source_plan.relative_to(ROOT)),
                      'inputSHA256': {str(p.relative_to(ROOT)): h for p, h in pins.items()},
                      'canonicalPath': str(parsed.relative_to(ROOT)), 'canonicalBeforeSHA256': sha(parsed),
                      'canonicalProposedSHA256': proposed_sha, 'selectedSections': len(selected),
                      'newSections': len(review['addedSections']), 'preimage': before,
                      'foreignAndQualifiedEdgesToPreserve': review['foreignOrQualifiedEdgesToPreserve']}
            write_text_atomic(output / 'plan.json', json.dumps(report, ensure_ascii=False, indent=2) + '\n')
            if not apply:
                return report
            tx = session.begin_transaction(timeout=240)
            written = False
            try:
                tx.run('MATCH(n:Section) WHERE n.sectionId IN $ids SET n.level=n.level', ids=sorted(old)).consume()
                if snapshot(tx, sorted(selected), projected['spec_number'], projected['release']) != before:
                    raise ValueError('Full live preimage changed before apply')
                fence()
                for section in review['addedSections']:
                    props = {k: section[k] for k in ('sectionId', 'sectionNumber', 'sectionTitle', 'level', 'isVoid')}
                    props.update(specNumber=projected['spec_number'], granularity='section')
                    tx.run('MATCH(sp:Spec {specNumber:$spec,specRelease:$release}) '
                           'CREATE(n:Section:ConformanceTest) SET n=$properties CREATE(n)-[:BELONGS_TO_SPEC]->(sp)',
                           spec=projected['spec_number'], release=projected['release'], properties=props).consume()
                tx.run('UNWIND $rows AS row MATCH(n:Section {sectionId:row.id}) SET n.level=row.level',
                       rows=[{'id': s['sectionId'], 'level': s['after']['level']} for s in review['updates']]).consume()
                for change in review['parentOwnershipDeltas']:
                    args = {'child': change['sectionId'], 'parent': change['newParent'], 'old': change['oldParent']}
                    if change['oldParent']:
                        tx.run('MATCH(c:Section {sectionId:$child})-[a:PARENT_SECTION]->(p:Section {sectionId:$old}), '
                               '(p)-[b:HAS_SUB_SECTION]->(c) DELETE a,b', **args).consume()
                    tx.run('MATCH(c:Section {sectionId:$child}),(p:Section {sectionId:$parent}) '
                           'CREATE(c)-[:PARENT_SECTION]->(p),(p)-[:HAS_SUB_SECTION]->(c)', **args).consume()
                after = snapshot(tx, sorted(selected), projected['spec_number'], projected['release'])
                verify_delta(before, after, review, projected['spec_number'])
                fence()
                written = True
                write_text_atomic(parsed, encoded)
                fence(canonical_written=True)
                tx.commit()
            except BaseException:
                tx.rollback()
                if written and sha(parsed) == proposed_sha:
                    write_text_atomic(parsed, raw.decode())
                raise
            finally:
                tx.close()
            readback = snapshot(session, sorted(selected), projected['spec_number'], projected['release'])
            verify_delta(before, readback, review, projected['spec_number'])
            fence(canonical_written=True)
            report.update(status='complete', postimage=readback, canonicalAfterSHA256=sha(parsed),
                          foreignEdgesPreserved=True, sourceBytesPreserved=True)
            write_text_atomic(output / 'result.json', json.dumps(report, ensure_ascii=False, indent=2) + '\n')
            return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-plan', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    result = run(args.source_plan, args.out, args.apply)
    print({k: result[k] for k in ('status', 'selectedSections', 'newSections')})
