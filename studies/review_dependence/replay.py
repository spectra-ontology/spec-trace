#!/usr/bin/env python3
"""Recompute review-dependent gold and all 37 stored-response subset scores."""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from datetime import datetime, timezone
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import re
import resource
import shutil
import sqlite3
import sys
import tempfile
import time

TRACK = 'logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark'
SCRIPTS = 'code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark'
WGS = [f'RAN{n}' for n in range(1, 6)]
E_BEFORE_BIS = re.compile(r'(#\d+)-e-b(?:is)?(?![a-z0-9])')
BIS_MARK = re.compile(r'(#\d+)-?b(?:is)?(?![a-z0-9])')
MEETING_FIELDS = {'tsg_meeting', 'wg_meeting'}


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


class Inputs:
    def __init__(self, release):
        self.release = release
        self.before = {}

    def add(self, path):
        relative = str(path.relative_to(self.release))
        if relative not in self.before:
            self.before[relative] = sha(path)
        return path

    def final(self):
        after = {name: sha(self.release / name) for name in self.before}
        if self.before != after:
            raise ValueError('An input changed during replay')
        return {'before': self.before, 'after': after, 'unchanged': True}


def json_lines(path):
    with path.open(encoding='utf-8') as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def dispositions(path):
    """Stream the released, pretty-printed JSON-LD graph one record at a time."""
    opener = gzip.open if path.suffix == '.gz' else open
    pending = None
    with opener(path, 'rt', encoding='utf-8') as handle:
        for line in handle:
            if line.rstrip('\r\n') == '    {':
                if pending is not None:
                    raise ValueError('Unexpected nested graph record')
                pending = [line]
            elif pending is not None:
                pending.append(line)
                if line.startswith('    }'):
                    record = json.loads(''.join(pending).rstrip().rstrip(','))
                    pending = None
                    if 'dispositionId' in record:
                        yield record
    if pending is not None:
        raise ValueError('Incomplete graph record')


def document_review_key(row, target=None):
    evidence = row['decisionEvidence']
    return (row.get('targetTdocNumber', target), evidence['path'], evidence['sha256'], evidence['locator'])


def count_dependence(release, output, inputs):
    items = {}
    evidence = defaultdict(list)
    gold_rows = 0
    for group in ('core', 'ran5'):
        path = inputs.add(release / f'benchmark/items_final/gate/{group}/chain_items_admitted.jsonl')
        for item in json_lines(path):
            if item['id'] in items:
                raise ValueError('Duplicate item id: ' + item['id'])
            items[item['id']] = item
            for index, row in enumerate(item.get('evidence', [])):
                gold_rows += 1
                if row.get('dispositionId'):
                    evidence[row['dispositionId']].append({'itemId': item['id'], 'evidenceIndex': index})
    receipt_index = {}
    receipt_counts = {}
    for wg in WGS:
        for kind in ('document', 'disposition'):
            path = release / f'receipts/{wg}/{kind}_decision_identity_reviews.json'
            if kind == 'disposition':
                path = release / f'receipts/{wg}/decision_disposition_identity_reviews.json'
            if not path.exists():
                continue
            payload = json.loads(inputs.add(path).read_text())
            receipt_counts[str(path.relative_to(release))] = len(payload['reviews'])
            for index, review in enumerate(payload['reviews']):
                key = (wg, kind, review['dispositionId'] if kind == 'disposition' else document_review_key(review))
                if key in receipt_index:
                    raise ValueError('Duplicate review-receipt key')
                receipt_index[key] = {'path': str(path.relative_to(release)), 'reviewIndex': index,
                                      'meetingId': review.get('meetingId'),
                                      'status': review['assessment'] if kind == 'disposition' else review['identityStatus']}
    dependent = set()
    rows_per_wg = Counter()
    items_per_wg = defaultdict(set)
    statuses = Counter()
    embedding_counts = Counter()
    record_count = 0
    matches = 0
    with (output / 'gold_dependence_trace.jsonl').open('w', encoding='utf-8') as trace:
        for wg in WGS:
            path = release / f'records/phase-2/{wg}/decision_dispositions.jsonld'
            if not path.exists():
                path = path.with_suffix('.jsonld.gz')
            for record in dispositions(inputs.add(path)):
                record_count += 1
                method = json.loads(record.get('assessmentMethod') or '{}')
                review = method.get('identityReview')
                if not review:
                    continue
                embedding_counts[wg] += 1
                golds = evidence.get(record['dispositionId'], [])
                if not golds:
                    continue
                kind = 'disposition' if 'dispositionId' in review else 'document'
                key = (wg, kind, review['dispositionId'] if kind == 'disposition' else document_review_key(review, record['targetTdocNumber']))
                if key not in receipt_index:
                    raise ValueError('Gold-linked review is absent from public receipts')
                matches += 1
                rows_per_wg[wg] += len(golds)
                ids = {row['itemId'] for row in golds}
                dependent.update(ids)
                items_per_wg[wg].update(ids)
                statuses[record['evidenceStatus']] += len(golds)
                trace.write(json.dumps({
                    'wg': wg, 'dispositionId': record['dispositionId'],
                    'sourceRecordFile': str(path.relative_to(release)),
                    'evidencePath': record.get('evidencePath'), 'evidenceSha256': record.get('evidenceSha256'),
                    'evidenceLocator': record.get('evidenceLocator'), 'evidenceStatus': record['evidenceStatus'],
                    'assignmentRule': method.get('rule'), 'identityReview': review,
                    'reviewReceipt': receipt_index[key], 'goldEvidenceReferences': golds
                }, ensure_ascii=False, sort_keys=True) + '\n')
    summary = {'items': len(items), 'goldEvidenceRows': gold_rows, 'dispositionRecordsRead': record_count,
               'goldRowsDependingOnAnyReview': sum(rows_per_wg.values()),
               'itemsDependingOnAnyReview': len(dependent), 'itemIdsDependingOnAnyReview': sorted(dependent),
               'goldRowsByWg': dict(rows_per_wg), 'itemsByWg': {wg: len(v) for wg, v in items_per_wg.items()},
               'dependentRowsEvidenceStatus': dict(statuses),
               'reviewEmbeddingDispositionsByWg': dict(embedding_counts),
               'matchedGoldDispositions': matches, 'publicReviewReceiptRows': receipt_counts,
               'matchingRule': 'exact evidence[].dispositionId to record.dispositionId; document reviews join by WG, target, source path/SHA256/locator; disposition reviews join by dispositionId',
               'scope': 'Public record dependence; reason-text origin is a separate build-input provenance analysis.'}
    expected = (667, 1640, 358062, 242, 99, {'RAN1': 53, 'RAN2': 46})
    actual = (len(items), gold_rows, record_count, sum(rows_per_wg.values()), len(dependent), summary['itemsByWg'])
    if actual != expected:
        raise ValueError(('Frozen dependence population differs', actual))
    save(output / 'review_dependence.json', summary)
    return items, dependent, summary


def condition_specs(release, inputs):
    """Reuse only pure file-list constructors; no module initialization or .git lookup."""
    path = inputs.add(release / SCRIPTS / 'analyze_template_session.py')
    tree = ast.parse(path.read_text(), filename=str(path))
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ('per_wg', 'conditions')]
    if {node.name for node in nodes} != {'per_wg', 'conditions'}:
        raise ValueError('Frozen condition constructors are unavailable')
    namespace = {'WGS': WGS, 'RUNS': 'ABCDEFGHIJ', 'CE': TRACK + '/chain_eval',
                 'SUPPLEMENT': TRACK + '/final/supplement_cycle'}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    specs = namespace['conditions']()
    if len(specs) != 37 or len({s['name'] for s in specs}) != 37:
        raise ValueError('Expected 37 distinct frozen conditions')
    for spec in specs:
        mapped = []
        for name in spec['files']:
            if name.startswith(TRACK + '/chain_eval/'):
                mapped.append(release / 'responses/chain_eval' / name.split('/chain_eval/', 1)[1])
            elif name.startswith(TRACK + '/final/'):
                mapped.append(release / 'responses/final' / name.split('/final/', 1)[1])
            else:
                raise ValueError('Unexpected historical condition path')
        spec['publicFiles'] = [inputs.add(path) for path in mapped]
    return specs


def kept_meetings(release, inputs):
    labels = set()
    with tempfile.TemporaryDirectory(prefix='spectra-review-dependence-db-') as temporary:
        for wg in WGS:
            path = release / f'sqlite/{wg}.sqlite'
            if path.is_file():
                inputs.add(path)
            else:
                source = inputs.add(path.with_suffix('.sqlite.gz'))
                path = Path(temporary) / f'{wg}.sqlite'
                with gzip.open(source, 'rb') as src, path.open('wb') as out:
                    shutil.copyfileobj(src, out)
            connection = sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True)
            try:
                connection.execute('PRAGMA query_only=ON')
                labels.update(str(row[0]).strip().lower() for row in connection.execute(
                    'SELECT label FROM meeting UNION SELECT tsg_meeting FROM cr_pack') if row[0])
            finally:
                connection.close()
    return {label + '-e' for label in labels if label + '-e' in labels}


def row_key(fields, row, identity, kept):
    cells = []
    for index, cell in enumerate(row):
        value = '' if cell is None else str(cell).strip().lower()
        value = BIS_MARK.sub(r'\1bis', E_BEFORE_BIS.sub(r'\1bis-e', value))
        if identity and index < len(fields) and fields[index] in MEETING_FIELDS and value not in kept:
            value = re.sub(r'-e$', '', value)
        cells.append(value)
    return tuple(cells)


def rescore(items, dependent, specs, kept):
    scriptless = {i for i in dependent if i.startswith('RAN2-')}
    subsets = {'all': set(items), 'withoutScriptless': set(items) - scriptless,
               'withoutAnyReview': set(items) - dependent, 'onlyDependent': dependent}
    result = {'items': len(items), 'dependent': len(dependent), 'scriptlessDependent': len(scriptless),
              'subsetSizes': {k: len(v) for k, v in subsets.items()}, 'conditions': {},
              'scoring': {'identityRule': 'same_meeting with separately recorded electronic meetings preserved',
                          'keptElectronicSpellings': sorted(kept)}}
    question_hashes = {i: hashlib.sha256(item['question'].encode()).hexdigest() for i, item in items.items()}
    for spec in specs:
        records = {}
        tally = Counter()
        for path in spec['publicFiles']:
            for record in json_lines(path):
                identifier = record['id']
                if identifier not in items:
                    tally['notInItems'] += 1
                    continue
                if identifier in records:
                    tally['duplicate'] += 1
                if record.get('questionSha256') != question_hashes[identifier]:
                    tally['staleQuestion'] += 1
                    continue
                records[identifier] = record
        tally['missing'] = len(set(items) - set(records))
        condition = {'checks': dict(tally)}
        for rule in ('identity', 'recorded'):
            matches = {}
            for identifier, item in items.items():
                rows = records[identifier].get('rows') if identifier in records else None
                matches[identifier] = rows is not None and (
                    {row_key(item['fields'], r, rule == 'identity', kept) for r in item['gold']}
                    == {row_key(item['fields'], r, rule == 'identity', kept) for r in rows})
            condition[rule] = {name: {'correct': sum(matches[i] for i in ids),
                                      'count': len(ids), 'share': sum(matches[i] for i in ids) / len(ids)}
                               for name, ids in subsets.items()}
        result['conditions'][spec['name']] = condition
    return result


def compare_reference(actual, expected):
    differences = []
    for key in ('items', 'dependent', 'scriptlessDependent', 'subsetSizes'):
        if actual[key] != expected[key]:
            differences.append({'field': key, 'actual': actual[key], 'expected': expected[key]})
    if set(actual['conditions']) != set(expected['conditions']):
        differences.append({'field': 'conditionNames'})
    checked = 0
    for name, reference in expected['conditions'].items():
        row = actual['conditions'].get(name, {})
        if row.get('checks') != reference['checks']:
            differences.append({'condition': name, 'field': 'checks'})
        for rule in ('identity', 'recorded'):
            for subset, target in reference[rule].items():
                checked += 1
                value = row.get(rule, {}).get(subset, {})
                wanted = dict(target, count=expected['subsetSizes'][subset])
                if value != wanted:
                    differences.append({'condition': name, 'rule': rule, 'subset': subset,
                                        'actual': value, 'expected': wanted})
    for key in ('identityRule', 'keptElectronicSpellings'):
        if actual['scoring'][key] != expected['scoring'][key]:
            differences.append({'field': 'scoring.' + key})
    return {'conditionCount': len(actual['conditions']), 'scoringRules': 2, 'subsetsPerRule': 4,
            'completeScoreCellsCompared': checked, 'countsCorrectAndSharesAllMatch': not differences,
            'differences': differences}


def relation_regression(actual):
    conditions = actual['conditions']

    def fraction(name, subset):
        cell = conditions[name]['identity'][subset]
        return Fraction(cell['correct'], cell['count'])

    def mean(prefix, subset):
        values = [fraction(name, subset) for name in conditions if name.startswith(prefix)]
        return sum(values) / len(values)

    def relation(first, second):
        return 'above' if first > second else 'below' if first < second else 'equal'

    aggregates = {}
    for subset in actual['subsetSizes']:
        cy, raw, sql = (mean(prefix, subset) for prefix in ('claude_text2cypher_run', 'raw_index_run', 'claude_text2sql_run'))
        aggregates[subset] = {'cypherMean': float(cy), 'rawMean': float(raw), 'sqlMean': float(sql),
                              'cypherVsRaw': relation(cy, raw), 'sqlVsRaw': relation(sql, raw)}
    examples = {}
    expected_relations = {'claude_text2sql_runD': {'all': 'above', 'withoutAnyReview': 'below'},
                          'claude_text2cypher_runI': {'all': 'above', 'withoutAnyReview': 'equal'}}
    checks = []
    for name, subsets in expected_relations.items():
        examples[name] = {}
        for subset, target in subsets.items():
            value, raw = fraction(name, subset), mean('raw_index_run', subset)
            observed = relation(value, raw)
            examples[name][subset] = dict(conditions[name]['identity'][subset], rawMean=float(raw), relation=observed)
            checks.append({'condition': name, 'subset': subset, 'expectedRelation': target,
                           'observedRelation': observed, 'pass': observed == target})
    for subset in ('all', 'withoutAnyReview'):
        a = aggregates[subset]
        checks.append({'aggregateSubset': subset, 'expected': 'Cypher > raw text > SQL',
                       'pass': a['cypherVsRaw'] == 'above' and a['sqlVsRaw'] == 'below'})
    return {'scope': 'Relations compare identity-score accuracy with the mean of the two raw-text runs.',
            'aggregateResults': aggregates, 'individualRunExamples': examples,
            'allIndividualRunsPreserveTheirStrictRelation': False,
            'checks': checks, 'allChecksPass': all(row['pass'] for row in checks)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', type=Path, required=True, help='Public release checkout')
    parser.add_argument('--output', type=Path, required=True, help='New scratch output directory')
    args = parser.parse_args()
    release, output = args.release.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    start_utc = datetime.now(timezone.utc).isoformat()
    reference = Path(__file__).with_name('reference_sensitivity.json')
    inputs = Inputs(release)
    items, dependent, dependence = count_dependence(release, output, inputs)
    specs = condition_specs(release, inputs)
    kept = kept_meetings(release, inputs)
    actual = rescore(items, dependent, specs, kept)
    save(output / 'sensitivity.json', actual)
    comparison = compare_reference(actual, json.loads(reference.read_text()))
    save(output / 'reference_comparison.json', comparison)
    regression = relation_regression(actual)
    save(output / 'relation_regression.json', regression)
    for name in ('score_chain_eval.py', 'score_meeting_spelling_sensitivity.py',
                 'score_meeting_suffix_insensitive.py', 'measure_identity_reviews.py',
                 'measure_review_dependence_sensitivity.py'):
        inputs.add(release / SCRIPTS / name)
    snapshots = inputs.final()
    receipt = {'startedUtc': start_utc, 'finishedUtc': datetime.now(timezone.utc).isoformat(),
               'python': sys.version, 'executable': sys.executable, 'sqlite': sqlite3.sqlite_version,
               'implementationSha256': sha(Path(__file__)), 'referenceSummarySha256': sha(reference),
               'releaseLayout': 'public checkout root selected by --release',
               'outputLayout': 'new scratch directory selected by --output',
               'elapsedSeconds': time.monotonic() - started, 'maxRssKiB': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               'publicInputFiles': len(snapshots['before']), 'inputSha256': snapshots,
               'scope': 'Public raw disposition-to-gold dependence reconstruction and independent row-set scoring. Original pure condition-list functions only; no module import initialization, .git marker or historical workspace required.',
               'freshModelResponses': 0, 'networkRequests': 0,
               'referenceComparisonPass': comparison['countsCorrectAndSharesAllMatch'],
               'relationRegressionPass': regression['allChecksPass']}
    save(output / 'replay_receipt.json', receipt)
    if not comparison['countsCorrectAndSharesAllMatch'] or not regression['allChecksPass']:
        raise SystemExit('Sensitivity or relation regression differs; inspect preserved output')
    print(json.dumps({'status': 'pass', 'goldEvidenceRows': dependence['goldEvidenceRows'],
                       'dependentGoldRows': dependence['goldRowsDependingOnAnyReview'],
                       'dependentItems': len(dependent), 'itemsByWg': dependence['itemsByWg'],
                       'completeScoreCellsCompared': comparison['completeScoreCellsCompared'],
                       'inputsUnchanged': True, 'elapsedSeconds': receipt['elapsedSeconds']}))


if __name__ == '__main__':
    main()
