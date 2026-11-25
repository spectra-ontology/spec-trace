#!/usr/bin/env python3
"""Recount the frozen RAN1 variation/tie tradeoff using complete SQL rowsets."""
import argparse
import collections
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import time

HERE = Path(__file__).resolve().parent
DB_SHA = '5e0d83e8418d887ec17433a883695a7ebcbff25e4c9ff048f4c2bd95f0c16cc1'
ANNOTATION_SHA = '46432b2abd1f04fc7e6beb4b2e0c1891986a47daa1077406a32df826939f5e5a'
PLAN_SHA = '2b9ee26e70db146ffef02003637c66f36953792d71a3a23b405d76fb995f3d22'
ANNOTATION_PATH = 'studies/witness_selection_value/full_candidate_sensitivity/run/candidates_RAN1.jsonl.gz'
SQL = '''WITH members AS (SELECT DISTINCT cr FROM cr_in_pack WHERE pack_id=?), typed AS (SELECT DISTINCT m.cr,s.spec,s.release,s.clause FROM cr_modifies_section m JOIN section s ON s.id=m.section_id), footprints AS (SELECT m.cr,COUNT(t.spec) AS n FROM members m LEFT JOIN typed t ON t.cr=m.cr GROUP BY m.cr) SELECT REPLACE(cr,'tdoc:',''),n FROM footprints WHERE n=(SELECT MAX(n) FROM footprints) ORDER BY cr'''


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', type=Path, required=True, help='Release root containing sqlite/RAN1.sqlite')
    parser.add_argument('--annotation', type=Path, help='Pinned candidates_RAN1.jsonl.gz; defaults to its release-relative location')
    parser.add_argument('--output', type=Path, required=True, help='New result JSON outside the release and installed study')
    args = parser.parse_args()
    release = args.release.resolve()
    annotation = (args.annotation or release / ANNOTATION_PATH).resolve()
    output = args.output.resolve()
    if output.is_relative_to(release) or output.is_relative_to(HERE.parent):
        parser.error('--output must be outside the release and installed study')
    if output.exists():
        parser.error('--output must be a new file')
    if sqlite3.sqlite_version != '3.37.2':
        parser.error('Use the reference SQLite 3.37.2 runtime')
    db = release / 'sqlite/RAN1.sqlite'
    plan = HERE / 'analysis_plan.json'
    pins = {'database': digest(db), 'annotation': digest(annotation), 'plan': digest(plan)}
    expected_pins = {'database': DB_SHA, 'annotation': ANNOTATION_SHA, 'plan': PLAN_SHA}
    if pins != expected_pins:
        raise ValueError({'input_pin_mismatch': pins, 'expected': expected_pins})
    started = time.monotonic()
    with gzip.open(annotation, 'rt') as stream:
        rows = [row for line in stream if (row := json.loads(line))['stratum'] == 'maximum_variation']
    conn = sqlite3.connect(db.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    conn.execute('PRAGMA query_only=ON')
    members = collections.defaultdict(set)
    links = collections.defaultdict(set)
    for cr, pack in conn.execute('select cr,pack_id from cr_in_pack'):
        members[pack].add(cr)
    for cr, spec, release_id, clause in conn.execute('select m.cr,s.spec,s.release,s.clause from cr_modifies_section m join section s on m.section_id=s.id'):
        links[cr].add((spec, release_id, clause))
    table = collections.Counter()
    details = []
    audits = []
    for row in rows:
        pack = row['candidate'][0]
        counts = {doc: len(links[doc]) for doc in sorted(members[pack])}
        eligible = len({value for value in counts.values() if value > 0}) >= 2
        maximum = max(counts.values())
        winners = sorted(doc for doc, value in counts.items() if value == maximum)
        tie = len(winners) > 1
        observed = row['detection_vector'][row['control_names'].index('limit_one')]
        if eligible != row['eligible'] or tie != bool(observed):
            raise AssertionError(('annotation mismatch', pack))
        expected = sorted([[doc.replace('tdoc:', ''), maximum] for doc in winners])
        reference = [list(record) for record in conn.execute(SQL, (pack,))]
        limit_one = [list(record) for record in conn.execute(SQL + ' LIMIT 1', (pack,))]
        if reference != expected or limit_one != expected[:1] or (reference != limit_one) != tie:
            raise AssertionError(('SQL rowset mismatch', pack, reference, limit_one, expected))
        table[eligible, 'packs'] += 1
        table[eligible, 'ties'] += tie
        details.append({'pack': pack, 'eligible': eligible, 'maximum': maximum, 'winners': winners, 'footprint_counts': counts, 'limit_one_detected': tie})
        audits.append({'pack': pack, 'fullReferenceRows': reference, 'limit1Rows': limit_one, 'raw_relation_match': True, 'annotation_match': True})
    conn.close()
    if not (len(rows) == 522 and table[True, 'packs'] == 268 and table[True, 'ties'] == 54 and table[False, 'ties'] == 142):
        raise AssertionError(('frozen recount changed', table))
    if digest(db) != pins['database'] or digest(annotation) != pins['annotation']:
        raise AssertionError('scientific input changed')
    example = next(item for item in details if not item['eligible'] and item['limit_one_detected'] and item['maximum'] > 0)
    example_audit = next(item for item in audits if item['pack'] == example['pack'])
    result = {
        'role': 'AUTHOR exploratory descriptive recount of existing measurements',
        'createdUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'inputSha256': pins,
        'allPacks': len(rows),
        'eligiblePacks': table[True, 'packs'],
        'allTieErrorsDetected': sum(item['limit_one_detected'] for item in details),
        'eligibleTieErrorsDetected': table[True, 'ties'],
        'ineligibleTieErrorsDetected': table[False, 'ties'],
        'interpretation': 'Requiring two distinct positive footprint sizes changes the prevalence of maximum ties; LIMIT1 is detected exactly by multiple maximum rows. Eligible cohort excludes142 tie-exposing packs with fewer than two distinct positive footprint sizes. It complements rather than replaces a tie-specific witness.',
        'sqlExample': {'pack': example['pack'], 'sql': SQL, 'fullReferenceRows': example_audit['fullReferenceRows'], 'limit1Rows': example_audit['limit1Rows'], 'rawCounts': example['footprint_counts']},
        'allCandidateDetails': details,
        'sourceUnchanged': True,
        'paidCalls': 0,
        'sqlAudit': {'status': 'passed', 'packs': len(audits), 'referenceExecutions': len(audits), 'limitOneExecutions': len(audits), 'sql': SQL, 'allRowsets': audits},
        'runtime': {'python': sys.version.split()[0], 'sqlite': sqlite3.sqlite_version, 'seconds': time.monotonic() - started},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('allPacks', 'eligiblePacks', 'allTieErrorsDetected', 'eligibleTieErrorsDetected', 'ineligibleTieErrorsDetected', 'sourceUnchanged', 'paidCalls', 'runtime')}))


if __name__ == '__main__':
    main()
