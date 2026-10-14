"""Compute complete source frequency pools for max/all-ties without a DB."""
import collections
import hashlib
import importlib.util
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
loader_path = Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/pipeline/load_released_kg.py')
spec = importlib.util.spec_from_file_location('loader', loader_path)
loader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loader)


def hash_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read(wg):
    path = ROOT / 'release_package/kg/per_wg' / (wg + '-body.ttl')
    nodes = {}
    memberships = collections.defaultdict(set)
    references = set()
    with path.open() as stream:
        for statement in loader.StatementReader(stream):
            if 'spectra:Section' not in statement and 'spectra:Spec' not in statement:
                continue
            parsed = loader.parse_statement(statement)
            if parsed is None:
                continue
            iri, predicates = parsed
            labels = {value[1] for (prefix, name), objects in predicates
                      if (prefix, name) == ('rdf', 'type') for kind, value in objects
                      if kind == 'pname' and value[0] == 'spectra'}
            props = {name: next((value for kind, value in objects if kind == 'lit'), None)
                     for (prefix, name), objects in predicates
                     if prefix == 'spectra' and name in {'sectionId', 'specNumber'}}
            nodes[iri] = {'labels': labels, 'props': props}
            for (prefix, name), objects in predicates:
                if prefix == 'spectra' and name == 'belongsToSpec':
                    memberships[iri].update(value for kind, value in objects if kind == 'iri')
                if prefix == 'spectra' and name == 'referencesSection':
                    references.update((iri, value) for kind, value in objects if kind == 'iri')
    sections = {iri for iri, node in nodes.items() if 'Section' in node['labels']}
    references = {(a, b) for a, b in references if a in sections and b in sections}
    return path, nodes, sections, memberships, references


results = []
path, nodes, sections, memberships, references = read('RAN5')
pair_edges = collections.defaultdict(set)
for source, target in references:
    for source_spec in memberships[source]:
        for target_spec in memberships[target]:
            from_spec = nodes.get(source_spec, {}).get('props', {}).get('specNumber')
            to_spec = nodes.get(target_spec, {}).get('props', {}).get('specNumber')
            if from_spec is not None and to_spec is not None and from_spec != to_spec:
                pair_edges[(from_spec, to_spec)].add((source, target))
pool = [{'fromSpec': key[0], 'toSpec': key[1], 'referenceCount': len(edges)}
        for key, edges in sorted(pair_edges.items())]
maximum = max((record['referenceCount'] for record in pool), default=None)
maxima = [{key: value for key, value in record.items() if key != 'referenceCount'}
          for record in pool if record['referenceCount'] == maximum]
results.append({'id': 'RAN5_P3_CQ2-4', 'graph_source_path': str(path.relative_to(ROOT)),
                'graph_source_sha256': hash_file(path), 'pool': pool, 'maximum': maximum,
                'maximal_requested_records': maxima})

path, nodes, sections, memberships, references = read('RAN3')
eligible = {target for target in sections if any(nodes.get(owner, {}).get('props', {}).get('specNumber') == '38.413'
                                              for owner in memberships[target])}
incoming = collections.Counter(target for source, target in references)
pool = [{'sectionId': nodes[target]['props'].get('sectionId'), 'referenceCount': incoming[target]}
        for target in sorted(eligible)]
maximum = max((record['referenceCount'] for record in pool), default=None)
maxima = [{'sectionId': record['sectionId']} for record in pool if record['referenceCount'] == maximum]
pool_path = BASE / 'source_pool_RAN3_P3_CQ2-3.jsonl'
pool_path.write_text(''.join(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n' for record in pool))
results.append({'id': 'RAN3_P3_CQ2-3', 'graph_source_path': str(path.relative_to(ROOT)),
                'graph_source_sha256': hash_file(path), 'pool_count': len(pool),
                'pool_path': str(pool_path.relative_to(ROOT)), 'pool_sha256': hash_file(pool_path),
                'zero_count': sum(record['referenceCount'] == 0 for record in pool),
                'maximum': maximum, 'maximal_requested_records': maxima})

output = BASE / 'max_frequency_source_witness.json'
output.write_text(json.dumps({'kind': 'Independent direct full frozenTTL frequency derivation, no native DB/model execution',
                              'parser_sha256': hash_file(loader_path), 'results': results}, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'path': str(output), 'sha256': hash_file(output), 'results': results}, ensure_ascii=False))
