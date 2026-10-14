#!/usr/bin/env python3
"""Append complete retained raw CRDB rows to an isolated lexical source snapshot."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(2**20),b''):h.update(block)
    return h.hexdigest()


def ident(p):
    s=Path(p).stat();return {'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}


def dump(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def main(base,raw,out):
    if out.exists():raise ValueError('Refuse to overwrite source snapshot')
    if Path(str(base)+'-wal').exists() and Path(str(base)+'-wal').stat().st_size:
        raise ValueError('Base corpus has a nonempty WAL')
    before=ident(base);base_sha=sha(base);raw_sha=sha(raw)
    records=[json.loads(s) for s in raw.read_text().splitlines() if s.strip()]
    if len(records)!=240 or len({r['source_row'] for r in records})!=240:
        raise ValueError('Expected complete unique 240-row raw source selection')
    if any(set(r)!={'source_row','fields','source_cell_coordinates'} for r in records):
        raise ValueError('Only original raw fields and source coordinates are permitted')
    out.mkdir(parents=True);target=out/'ran2.sqlite3'
    subprocess.run(['cp','--reflink=auto','--',str(base),str(target)],check=True)
    copied_sha=sha(target)
    if copied_sha!=base_sha:raise ValueError('Source clone differs before augmentation')
    con=sqlite3.connect(target)
    con.execute('PRAGMA journal_mode=DELETE');con.execute('PRAGMA synchronous=FULL')
    con.execute('PRAGMA temp_store=FILE');con.execute('PRAGMA cache_size=-32768')
    con.execute('PRAGMA threads=1');con.execute('PRAGMA mmap_size=0')
    before_n=con.execute('SELECT count(*) FROM docs').fetchone()[0]
    collection='official_CRDB_20260319_RAN2_RAN110_raw'
    if con.execute('SELECT count(*) FROM docs WHERE collection=?',(collection,)).fetchone()[0]:
        raise ValueError('Source augmentation collection already exists')
    for record in records:
        fields=record['fields']
        metadata={'source':'Original official CRDB_20260319.xlsx register fields',
                  'filename':'CRDB_20260319.xlsx','origin':'retained_raw_source_augmentation',
                  'meetingNumber':fields.get('Meeting TSG-level'),
                  'tdocNumber':fields.get('WG Tdoc'),'specNumber':fields.get('Spec number')}
        text=json.dumps(record,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
        cur=con.execute('INSERT INTO docs(collection,point_id,chunk_id,metadata,text) VALUES(?,?,?,?,?)',
                        (collection,'source_row_'+str(record['source_row']),
                         'CRDB_20260319_row_'+str(record['source_row']),
                         json.dumps(metadata,ensure_ascii=False,sort_keys=True),text))
        con.execute('INSERT INTO search(rowid,text) VALUES(?,?)',(cur.lastrowid,text))
    con.commit()
    after_n=con.execute('SELECT count(*) FROM docs').fetchone()[0]
    if after_n-before_n!=240:raise ValueError('Unexpected corpus population change')
    for record in records:
        row=con.execute('SELECT text FROM docs WHERE collection=? AND point_id=?',
                        (collection,'source_row_'+str(record['source_row']))).fetchone()
        if json.loads(row[0])!=record:raise ValueError('Stored augmentation is not exact raw source')
    fts_probe=con.execute("SELECT count(*) FROM search JOIN docs ON docs.id=search.rowid WHERE search MATCH '110' AND collection=?",(collection,)).fetchone()[0]
    con.execute("INSERT INTO search(search,rank) VALUES('integrity-check',1)")
    con.commit();con.close()
    for p in base.parent.glob('*.snapshot.json'):shutil.copy2(p,out/p.name)
    dump(out/(collection+'.snapshot.json'),{
        'kind':'Original raw source rows appended without answer projection',
        'stored_points':240,'source_records_path':str(raw),'source_records_sha256':raw_sha,
        'source_selection':'All retained original RAN2 CRDB rows at the requested TSG meeting; fixed before performance',
        'no_reference_gold_or_review_text':True})
    if ident(base)!=before or sha(raw)!=raw_sha:raise ValueError('Original source changed')
    result={'kind':'Isolated existing lexical corpus plus complete original raw-source augmentation',
            'created_utc':datetime.now(timezone.utc).isoformat(),
            'base_path':str(base),'base_sha256':base_sha,'base_file_before_after_unchanged':True,
            'clone_before_augmentation_sha256':copied_sha,
            'raw_source_path':str(raw),'raw_source_sha256':raw_sha,'raw_rows_n':240,
            'path':str(target),'sha256':sha(target),'bytes':target.stat().st_size,
            'base_docs_n':before_n,'new_docs_n':after_n,'new_raw_source_docs_n':240,
            'raw_docs_reparsed_exactly':True,'augmented_FTS_MATCH_110_rows':fts_probe,
            'FTS_external_content_integrity_check':True,
            'selection_used_gold_query_or_model_scores':False,
            'graph_text_whole_snapshot_equality':'Not established; source augmentation facts are paired, prior text/graph cutoffs remain distinct.',
            'retrieval_algorithm_and_budgets_changed':False}
    dump(out/'augmentation_manifest.json',result)
    print(json.dumps({'status':'SOURCE_SNAPSHOT_READY','raw_rows_n':240,'new_docs_n':after_n,
                      'manifest_sha256':sha(out/'augmentation_manifest.json')}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True)
    p.add_argument('--raw-records',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();main(a.base.resolve(),a.raw_records.resolve(),a.out.resolve())
