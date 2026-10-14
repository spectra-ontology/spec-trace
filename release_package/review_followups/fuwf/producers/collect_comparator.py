#!/usr/bin/env python3
"""Inspect pinned primary comparator artifacts; no model evaluation or graph mutation."""
import argparse
import collections
import hashlib
import json
import re
import shutil
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone

REVISION = 'e6487ae660852b56e6d9952680f661215a53ec46'
BASE = 'https://huggingface.co/datasets/otellm/telecom-kg-rel19/resolve/' + REVISION + '/'
NS = '{http://graphml.graphdrawing.org/xmlns}'
PROCESS_ID = re.compile(r'\b(?:R[1-5P]-\d{6,8}|(?:TSG\s*)?RAN\s*(?:WG\s*)?[1-5]?\s*#\s*\d+)\b', re.I)
EXPECTED = {
    'telecom-kg-rel19.graphml': (31915826, 'ff86efd5f70b66221df1a0d100de9a5664e06e5d679bfe8371a184c2b0770b0c'),
    'telecom-kg-rel19-chunks.jsonl': (207220421, '6dc003338cdc7e90e5f514144b42c71d2da698002ffad5c1b16732ba88e050cd'),
}


def write(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def download(url, destination, cap, previous=None):
    digest = hashlib.sha256()
    size = 0
    headers = {'User-Agent': 'SPECTRA-source-scope-audit/1'}
    if previous is not None and previous.exists():
        with previous.open('rb') as source, destination.open('xb') as handle:
            while chunk := source.read(1024 * 1024):
                digest.update(chunk)
                size += len(chunk)
                handle.write(chunk)
        if destination.name in EXPECTED and size == EXPECTED[destination.name][0]:
            if digest.hexdigest() != EXPECTED[destination.name][1]:
                raise ValueError('Existing complete artifact has wrong published LFS SHA-256')
            return {'url': url, 'bytes': size, 'sha256': digest.hexdigest(),
                    'path': str(destination), 'reused_verified_input': str(previous)}
        if destination.name not in EXPECTED:
            return {'url': url, 'bytes': size, 'sha256': digest.hexdigest(),
                    'path': str(destination), 'copied_prior_receipted_input': str(previous)}
        headers['Range'] = 'bytes=' + str(size) + '-'
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        if 'Range' in headers:
            if response.status != 206 or not response.headers.get('Content-Range', '').startswith('bytes ' + str(size) + '-'):
                raise ValueError('Resume server did not honor exact byte range')
        with destination.open('ab' if size else 'xb') as handle:
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > cap:
                    raise ValueError('Artifact exceeds declared size cap')
                digest.update(chunk)
                handle.write(chunk)
        metadata = {'url': url, 'bytes': size,
                    'sha256': digest.hexdigest(), 'path': str(destination)}
    if destination.name in EXPECTED and (size, digest.hexdigest()) != EXPECTED[destination.name]:
        raise ValueError('Incomplete or changed artifact; does not match published LFS size and SHA-256')
    return metadata


def inspect_graph(path):
    keys = {}
    counts = collections.Counter()
    attributes = {'node': collections.Counter(), 'edge': collections.Counter()}
    types = {'node': collections.Counter(), 'edge': collections.Counter()}
    examples = {'node': [], 'edge': []}
    process_mentions = {'node': [], 'edge': []}
    process_mentions_n = collections.Counter()
    # Clear at record boundaries, after consuming child data. This scans the full graph.
    for event, item in ET.iterparse(path, events=('end',)):
        tag = item.tag.removeprefix(NS)
        if tag == 'key':
            keys[item.attrib['id']] = dict(item.attrib)
            item.clear()
        elif tag in ('node', 'edge'):
            counts[tag] += 1
            fields = {keys.get(x.attrib.get('key'), {}).get('attr.name', x.attrib.get('key')):
                      x.text or '' for x in item.findall(NS + 'data')}
            attributes[tag].update(fields.keys())
            for key, value in fields.items():
                if any(token in key.lower() for token in ('type', 'label', 'relation')):
                    types[tag][key + ':' + value] += 1
            if len(examples[tag]) < 3:
                examples[tag].append({'record_attributes': dict(item.attrib), 'data': fields})
            matches = sorted(set(PROCESS_ID.findall(' '.join(fields.values()))))
            if matches:
                process_mentions_n[tag] += 1
                if len(process_mentions[tag]) < 20:
                    process_mentions[tag].append({'record': dict(item.attrib), 'mentions': matches})
            item.clear()
    return {'counts': dict(counts), 'keys': keys,
            'attribute_population': {k: dict(v) for k, v in attributes.items()},
            'type_or_label_values': {k: dict(v.most_common()) for k, v in types.items()},
            'first_three_examples': examples,
            'process_id_mention_records_n': dict(process_mentions_n),
            'process_id_mentions_examples': process_mentions,
            'mention_scope': 'Literal regular-expression mentions, not typed process relations or semantic absence.'}


def inspect_chunks(path):
    fields = collections.Counter()
    records = 0
    matches_n = 0
    examples = []
    first = []
    for line in path.open(encoding='utf-8'):
        if not line.strip():
            continue
        row = json.loads(line)
        records += 1
        fields.update(row.keys())
        if len(first) < 2:
            first.append(row)
        matches = sorted(set(PROCESS_ID.findall(json.dumps(row, ensure_ascii=False))))
        if matches:
            matches_n += 1
            if len(examples) < 20:
                examples.append({'line': records, 'mentions': matches,
                                 'record': row})
    return {'records': records, 'field_population': dict(fields),
            'first_two_examples': first, 'process_id_mention_records_n': matches_n,
            'process_id_mentions_examples': examples,
            'limitation': 'An ID can occur in specification prose. This does not supply a meeting decision, CR cover or liaison routing record.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--previous', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    metadata = []
    for remote, local, cap in [
        ('README.md', 'telecom-kg-rel19-README.txt', 1024 * 1024),
        ('kg/rel19_3gpp_telecom_kg.graphml', 'telecom-kg-rel19.graphml', 40 * 1024**2),
        ('chunks/rel19_text_chunks.jsonl', 'telecom-kg-rel19-chunks.jsonl', 220 * 1024**2),
    ]:
        metadata.append(download(BASE + remote, args.output / local, cap,
                                 args.previous / local if args.previous else None))
        print(json.dumps({'downloaded': local, 'bytes': metadata[-1]['bytes']}), flush=True)
    metadata.append(download('https://aclanthology.org/2026.findings-acl.1343.pdf',
                             args.output / 'DeepSpecs.pdf', 10 * 1024**2,
                             args.previous / 'DeepSpecs.pdf' if args.previous else None))
    write(args.output / 'downloads.json', {'revision': REVISION, 'artifacts': metadata,
                                         'retrieved_utc': datetime.now(timezone.utc).isoformat()})
    graph = inspect_graph(args.output / 'telecom-kg-rel19.graphml')
    chunks = inspect_chunks(args.output / 'telecom-kg-rel19-chunks.jsonl')
    write(args.output / 'artifact_scope.json', {
        'producer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'comparator': 'otellm/telecom-kg-rel19', 'revision': REVISION,
        'graph': graph, 'chunks': chunks,
        'not_measured': ['question-answering accuracy', 'practitioner utility',
                        'SPECTRA superiority', 'capability after adding new source documents'],
        'human_expert_reviews': 0, 'model_calls': 0})
    print(json.dumps({'graph_counts': graph['counts'], 'chunk_records': chunks['records']}), flush=True)


if __name__ == '__main__':
    main()
