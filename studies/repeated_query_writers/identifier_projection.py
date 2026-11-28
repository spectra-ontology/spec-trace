"""Recount fixed SQL outputs after resolving stored keys to requested labels in typed answer columns."""
import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile

FIELD_TABLE = {'document': 'document', 'final_document': 'document', 'wg_meeting': 'meeting',
               'tsg_meeting': 'meeting', 'cr_pack': 'cr_pack', 'disposition': 'disposition'}
LABEL_COLUMN = {'document': 'number', 'meeting': 'label', 'cr_pack': 'pack_number', 'disposition': 'code'}
EXAMPLE_RUN = 'claude-fable__sql__RAN4_A'
EXAMPLE_ITEM = 'RAN4-revision_chain-R4-2418926'


def load(path):
    return json.loads(path.read_bytes())


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as fp:
        for block in iter(lambda: fp.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def label_maps(wg, release, sqlite_dir, temporary):
    grouped = {}
    database = (sqlite_dir or release / 'sqlite') / f'{wg}.sqlite'
    if not database.is_file():
        compressed = database.with_suffix('.sqlite.gz')
        database = temporary / database.name
        with gzip.open(compressed, 'rb') as src, database.open('wb') as dst:
            shutil.copyfileobj(src, dst)
    expected = load(release / 'studies/matched_domains/frozen/protocol.json')['databases'][wg]['sqliteSha256']
    if sha(database) != expected:
        raise ValueError(f'SQLite export differs from the experiment input for {wg}')
    db = sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)
    try:
        for table, label in LABEL_COLUMN.items():
            mappings = {}
            for key, value in db.execute(f'SELECT id, {label} FROM {table} WHERE {label} IS NOT NULL'):
                if key in mappings and mappings[key] != value:
                    raise ValueError(f'Ambiguous {table} key in {wg}')
                mappings[key] = value
            grouped[table] = mappings
    finally:
        db.close()
    if database.parent == temporary:
        database.unlink()
    return grouped, expected


def public_records(study, witness_path, gold, scorer, kept, fingerprint, model):
    with gzip.open(witness_path,'rt',encoding='utf-8') as stream:
        witnesses = {(row['id'],row['fingerprint']):row['rows'] for row in map(json.loads,stream)}
    runs = {row['run']:row for row in load(study/'runs.json') if row['study']=='full667' and row['language']=='sql' and (model is None or row['model']==model)}
    used = set()
    empty = hashlib.sha256(b'[]').hexdigest()
    with gzip.open(study/'full667.jsonl.gz','rt',encoding='utf-8') as stream:
        for row in map(json.loads,stream):
            rid = row['run']
            if rid not in runs:
                continue
            item = gold[row['id']]
            digest = row['returnedIdentitySetSha256']
            if row['exact']:
                raw = item['gold']
            elif digest is None:
                raw = None
            elif digest == empty:
                raw = []
            else:
                key = row['id'],digest
                raw = witnesses[key]
                used.add(key)
            if fingerprint(scorer,item,raw,kept) != digest:
                raise ValueError(f'Returned-set fingerprint mismatch for {rid} {row["id"]}')
            yield {'runId':rid, 'model':runs[rid]['model'], 'wg':row['wg'],
                   'id':row['id'], 'rows':raw, 'exact':row['exact']}
    if used != set(witnesses):
        raise ValueError('Unreferenced returned-row witness')


def assess(records, gold, scorer, kept, maps):
    counts, models, families, changed_tables = Counter(), {}, {}, Counter()
    distinct_runs, distinct_items, distinct_cells = set(), set(), set()
    example = None
    for r in records:
        rid, model, wg = r['runId'], r['model'], r['wg']
        item = gold[r['id']]
        assert item['wg'] == wg
        cell = (rid,r['id'])
        if cell in distinct_cells:
            raise ValueError(f'Duplicate run and question: {cell}')
        distinct_cells.add(cell)
        distinct_runs.add(rid)
        raw = r['rows']
        target = scorer.identity_rows(item, item['gold'], kept)
        def exact(rows):
            return scorer.score(target, scorer.identity_rows(item, rows, kept))['exact']
        original = exact(raw)
        if original != r['exact']:
            raise ValueError(f'Published score mismatch for {cell}')
        touched = set()
        transformed = None if raw is None else []
        for row in raw or []:
            output = []
            for field, value in zip(item['fields'], row, strict=True):
                table = FIELD_TABLE.get(field)
                translated = maps[wg][table].get(value, value) if table else value
                if translated != value:
                    touched.add(table)
                output.append(translated)
            transformed.append(output)
        resolved = exact(transformed)
        def add(counter):
            counter['positions'] += 1
            counter['originalExact'] += original
            counter['resolvedExact'] += resolved
            counter['wrongNonempty'] += int(bool(raw) and not original)
            counter['changedOutput'] += int(bool(touched))
            counter['gains'] += int(resolved and not original)
            counter['losses'] += int(original and not resolved)
        add(counts)
        add(models.setdefault(model, Counter()))
        add(families.setdefault(item['family'], Counter()))
        if resolved and not original:
            distinct_items.add(r['id'])
            changed_tables['+'.join(sorted(touched))] += 1
        if rid == EXAMPLE_RUN and r['id'] == EXAMPLE_ITEM:
            example = {'runId': rid, 'id': r['id'], 'fields': item['fields'], 'gold': item['gold'],
                       'original': raw, 'resolved': transformed}
    return {'sqlWorkingGroupBatches':len(distinct_runs), 'distinctRecoveredItems':len(distinct_items),
            'overall':counts,'byModel':models,'byFamily':families,
            'gainsByChangedTables':changed_tables,'example':example}


def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release',type=Path,required=True)
    parser.add_argument('--sqlite-dir',type=Path,help='Optional uncompressed exports; all five are verified by digest')
    parser.add_argument('--study',type=Path,help='Location of the repeated-query study within the release')
    parser.add_argument('--all-models',action='store_true',help='Use the companion complete eight-model census')
    parser.add_argument('--out',type=Path,help='Optionally write the recomputed result to this path')
    args = parser.parse_args()
    study = args.study or args.release/'studies/repeated_query_writers'
    spec = importlib.util.spec_from_file_location('study_verify',study/'verify.py')
    verify = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verify)
    scorer, kept, gold_lists = verify.gold_inputs(args.release)
    gold = {i['id']:i for i in gold_lists['full667']}
    if len(gold) != 667:
        raise ValueError('Expected 667 unique main-workload items')
    with tempfile.TemporaryDirectory() as directory:
        maps, digests = {}, {}
        for wg in ['RAN1','RAN2','RAN3','RAN4','RAN5']:
            maps[wg], digests[wg] = label_maps(wg,args.release,args.sqlite_dir,Path(directory))
    model = None if args.all_models else 'claude-fable-5-2'
    prefix = 'all_sql' if args.all_models else 'fable_sql'
    records = public_records(study,here/f'{prefix}_witnesses.jsonl.gz',gold,scorer,kept,verify.fingerprint,model)
    report = assess(records,gold,scorer,kept,maps)
    batches, jobs = (400,53360) if args.all_models else (50,6670)
    if report['sqlWorkingGroupBatches'] != batches or report['overall']['positions'] != jobs:
        raise ValueError('Replayed assignment count differs from the scheduled study.')
    report['sourceSQLiteSha256']=digests
    report['fieldToRelation']=FIELD_TABLE
    report['relationToDisplayColumn']=LABEL_COLUMN
    if report != load(here/f'{prefix}_projection.json'):
        raise ValueError('Recomputed diagnosis differs from the saved native-row census')
    if args.out:
        args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(f"{report['overall']['gains']} gained exact matches among {report['overall']['positions']} SQL assignments")

if __name__=='__main__':
    main()
