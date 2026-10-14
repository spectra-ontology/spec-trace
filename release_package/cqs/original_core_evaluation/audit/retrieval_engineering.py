#!/usr/bin/env python3
"""Gold-free SQLite FTS5 query-plan and stable-boundary development audit."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import time

FROZEN = ('SELECT d.id,d.collection,d.point_id,bm25(search) AS bm25_native '
          'FROM search JOIN docs d ON d.id=search.rowid WHERE search MATCH ? '
          'ORDER BY bm25_native ASC,d.collection ASC,d.point_id ASC LIMIT ?')
FAST = 'SELECT rowid,rank FROM search WHERE search MATCH ? ORDER BY rank ASC'


def boundary_candidate(con, expression, maximum):
    """DEV ONLY: exhaust complete BM25 boundary group before stable metadata sort.

    No claim of efficient completion for arbitrarily large equal-score groups.
    The streaming FTS ordering uses default rank=BM25, just like the frozen score.
    """
    retained = []; boundary = None; cursor = con.execute(FAST, (expression,))
    for rowid, rank in cursor:
        if boundary is not None and rank > boundary:
            break
        retained.append((rowid, rank))
        if len(retained) == maximum:
            boundary = rank
    cursor.close()
    hydrated = []
    for rowid, rank in retained:
        collection, point = con.execute('SELECT collection,point_id FROM docs WHERE id=?', (rowid,)).fetchone()
        hydrated.append((rowid, collection, point, rank))
    return sorted(hydrated, key=lambda r: (r[3], r[1], r[2]))[:maximum], len(retained)


def fixture(dense):
    con = sqlite3.connect(':memory:')
    con.execute('CREATE TABLE docs(id INTEGER PRIMARY KEY,collection TEXT,point_id TEXT,text TEXT)')
    con.execute("CREATE VIRTUAL TABLE search USING fts5(text,content='docs',content_rowid='id',tokenize='unicode61 remove_diacritics 2')")
    rows = [(i+1, 'fixture', f'p{2000-i:05}', 'target term ' + ('word ' * (5 if dense else i % 50))) for i in range(2000)]
    con.executemany('INSERT INTO docs VALUES(?,?,?,?)', rows); con.execute("INSERT INTO search(search) VALUES('rebuild')")
    expression = '"target" OR "term"'
    began = time.monotonic(); exact = con.execute(FROZEN, (expression, 160)).fetchall(); exact_time=time.monotonic()-began
    began = time.monotonic(); candidate, retained = boundary_candidate(con, expression, 160); candidate_time=time.monotonic()-began
    naive = []
    for rowid, rank in con.execute(FAST+' LIMIT 160', (expression,)):
        collection, point=con.execute('SELECT collection,point_id FROM docs WHERE id=?',(rowid,)).fetchone()
        naive.append((rowid,collection,point,rank))
    report={'fixture_kind':'all matching scores equal' if dense else 'mixed lengths with boundary ties',
            'documents':len(rows),'maximum':160,'full_stable_frozen_rows_equal_complete_boundary_variant':exact==candidate,
            'naive_rank_only_limit_rows_equal_frozen':exact==naive,
            'complete_boundary_rows_hydrated':retained,'frozen_seconds':exact_time,'boundary_variant_seconds':candidate_time,
            'scope':'Synthetic development fixture; no benchmark gold or model calls; timings do not measure actual archive baseline speed.'}
    con.close(); return report


def audit(path, expression):
    con=sqlite3.connect(path.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
    plans={'frozen':con.execute('EXPLAIN QUERY PLAN '+FROZEN,(expression,160)).fetchall(),
           'rank_stream_only':con.execute('EXPLAIN QUERY PLAN '+FAST,(expression,)).fetchall(),
           'rank_with_rowid_tie':con.execute('EXPLAIN QUERY PLAN '+FAST.replace('rank ASC','rank ASC,rowid ASC')+' LIMIT 160',(expression,)).fetchall()}
    configuration=con.execute('SELECT * FROM search_config').fetchall()
    con.close()
    return {'actual_retained_corpus_query_plans':plans,'sqlite_version':sqlite3.sqlite_version,
            'actual_FTS_configuration':configuration,
            'rank_uses_default_BM25':not any(row[0]=='rank' for row in configuration),
            'synthetic_fixtures':[fixture(False),fixture(True)],
            'interpretation':'Frozen BM25-plus-metadata-tie query uses FTS unsorted matching scan and a temporary ORDER BY B-tree. Pure rank order uses FTS sorted-rank virtual index. Stable tie fields prevent that direct optimization. A complete-boundary two-stage variant can preserve exact top-160 values but naive rank-only LIMIT cannot; huge equal-score boundaries can still approach the full match population.',
            'frozen_run_changed':False,'new_model_calls':0,'actual_baseline_optimized_rerun_performed':False,
            'representativeness_limit':'Frozen bounded implementation results include engineering deadline failures and cannot establish a general failure of text retrieval or corpus absence. Query plans demonstrate an implementation limit, not universal baseline invalidity.'}


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--corpus',type=Path,required=True);a.add_argument('--expression',required=True);a.add_argument('--output',type=Path,required=True)
    args=a.parse_args();value=audit(args.corpus,args.expression);value['tool_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'query_plans':value['actual_retained_corpus_query_plans'],'fixtures':value['synthetic_fixtures']},ensure_ascii=False))
