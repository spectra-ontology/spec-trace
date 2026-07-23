#!/usr/bin/env python3
"""run_baseline.py — third-party LLM baseline campaign for SpectraCQ.

Three conditions per (model, CQ):
  closed_book  parametric knowledge only (expected ~0 on specific TDoc/CR ids;
               a low score here is the non-memorization evidence, not a failure)
  rag          Qdrant semantic retrieval over the WG chunk collections -> answer set
  kg_grounded  model writes ONE Cypher query from the schema card -> we execute it
               against the live graph -> execution result = the answer (BIRD-style)

Chat routes through OpenRouter; RAG query embedding uses the sanctioned
openai/text-embedding-3-small. The GOLD path has no LLM (see build_cq_gold.py).

Safety / reproducibility:
  * DRY-RUN by default: prints the plan + one rendered prompt per condition and
    makes ZERO paid chat calls. Pass --confirm to actually fire.
  * Resumable: rows already present in an output file (by cq id) are skipped.
  * Concrete model ids are printed before each (condition, model, wg) block.

Output: results/{condition}/{model_slug}/all.jsonl   (one row per CQ)
RAG context cached once per CQ: results/_rag_cache/{wg}/{cq_id}.json (model-agnostic).
"""
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import bench_common as bc

BASE = bc.BASE
RESULTS = BASE / 'results'
RAG_CACHE = RESULTS / '_rag_cache'
BENCH = bc.ROOT / 'release_package/cqs/spectra_cq_v2.0/benchmark.jsonl'

RAG_COLLECTIONS = ['{wg}_ts_sections', '{wg}_tdoc_chunks', '{wg}_cr_chunks',
                   '{wg}_resolution_chunks', '{wg}_tr_sections']

SYS = {
    'closed_book':
        'You are an expert on the 3GPP RAN standardization process (meetings, '
        'TDocs, change requests, specifications, technical reports). Answer the '
        'question using ONLY your own knowledge. Respond with ONLY a JSON object '
        '{"answer": [...]} listing the specific identifiers or values that answer '
        'the question (e.g. TDoc numbers, CR numbers, spec numbers, titles). '
        'If you do not know, return {"answer": []}. No prose.',
    'rag':
        'You are an expert on the 3GPP RAN standardization process. Answer the '
        'question using ONLY the numbered context passages provided. Respond with '
        'ONLY a JSON object {"answer": [...]} listing the specific identifiers or '
        'values that answer the question. If the passages do not contain the '
        'answer, return {"answer": []}. No prose.',
    'kg_grounded':
        'You translate a natural-language question into ONE Cypher query for the '
        'given Neo4j schema of a 3GPP RAN process knowledge graph. The FIRST '
        'returned column must hold the answer values. Use only labels, properties '
        'and relationship types that appear in the schema. Respond with ONLY a '
        'JSON object {"cypher": "..."}. No prose, no comments.',
}


def load_models(names=None):
    roster = json.load(open(BASE / 'models.json'))['roster']
    if names:
        want = set(names)
        roster = [m for m in roster if m['slug'] in want or m['id'] in want]
    return roster


def load_bench(wgs=None, limit=None):
    rows = []
    with open(BENCH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if wgs and r['wg'] not in wgs:
                continue
            rows.append(r)
    if limit:
        # even sample across WGs so a --limit smoke test still touches every WG
        by = {}
        for r in rows:
            by.setdefault(r['wg'], []).append(r)
        out, i = [], 0
        while len(out) < limit and any(i < len(v) for v in by.values()):
            for wg in sorted(by):
                if i < len(by[wg]) and len(out) < limit:
                    out.append(by[wg][i])
            i += 1
        rows = out
    return rows


def load_schema_cards():
    return json.load(open(BASE / 'schema_cards.json'))


def get_context(cq, existing_cols):
    """Return (context_text, provenance). Cache per cq id (model-agnostic)."""
    wg = cq['wg']
    cpath = RAG_CACHE / wg / f"{cq['id']}.json"
    if cpath.exists():
        d = json.load(open(cpath))
        return d['context'], d['provenance']
    cols = [c.format(wg=wg.lower()) for c in RAG_COLLECTIONS]
    cols = [c for c in cols if c in existing_cols]
    ctx, prov = bc.retrieve_context(wg, cq['question_en'], cols)
    cpath.parent.mkdir(parents=True, exist_ok=True)
    cpath.write_text(json.dumps({'cq_id': cq['id'], 'context': ctx,
                                 'provenance': prov}, ensure_ascii=False))
    return ctx, prov


def build_messages(condition, cq, cards, existing_cols):
    q = cq['question_en']
    if condition == 'closed_book':
        return [{'role': 'system', 'content': SYS['closed_book']},
                {'role': 'user', 'content': f'Question: {q}'}], None
    if condition == 'rag':
        ctx, prov = get_context(cq, existing_cols)
        user = (f'Context passages:\n{ctx}\n\n' if ctx else 'Context passages: (none retrieved)\n\n')
        user += f'Question: {q}'
        return [{'role': 'system', 'content': SYS['rag']},
                {'role': 'user', 'content': user}], prov
    if condition == 'kg_grounded':
        card = cards[cq['wg']]['card']
        user = f'{card}\n\nQuestion: {q}\n\nReturn one Cypher query as {{"cypher": "..."}}.'
        return [{'role': 'system', 'content': SYS['kg_grounded']},
                {'role': 'user', 'content': user}], None
    raise ValueError(condition)


def done_ids(path):
    if not path.exists():
        return set()
    ids = set()
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    ids.add(json.loads(line)['id'])
                except Exception:  # noqa: BLE001
                    pass
    return ids


def run_one(condition, model, cq, cards, existing_cols):
    messages, prov = build_messages(condition, cq, cards, existing_cols)
    res = bc.chat(model['id'], messages,
                  max_tokens=2000 if condition == 'kg_grounded' else 1200)
    row = {'id': cq['id'], 'wg': cq['wg'], 'phase': cq['phase'],
           'condition': condition, 'model_slug': model['slug'], 'model_id': model['id'],
           'raw_text': res['text'], 'usage': res['usage'], 'cost': res['cost'],
           'latency_s': res['latency_s'], 'finish': res['finish'], 'error': res['error']}
    if condition == 'kg_grounded':
        cy = bc.parse_cypher(res['text'])
        row['cypher'] = cy
        if cy:
            ex = bc.exec_cypher(cq['wg'], cy)
            row['exec_status'] = ex['status']
            row['exec_error'] = ex['error']
            row['predicted_values'] = ex['primary_values']
            row['exec_columns'] = ex['columns']
            row['exec_row_count'] = ex['row_count']
        else:
            row['exec_status'] = 'NO_CYPHER'
            row['predicted_values'] = []
    else:
        row['predicted_values'] = bc.parse_answer_list(res['text'])
        if condition == 'rag':
            row['rag_provenance'] = [{'collection': p['collection'], 'score': p['score'],
                                      'chunkId': p['chunkId']} for p in (prov or [])]
    return row


def dry_run(models, conditions, wgs, rows, cards, existing_cols):
    print('=== DRY-RUN (no paid chat calls) ===')
    print(f'benchmark rows selected : {len(rows)}')
    print(f'WGs                     : {wgs or "all"}')
    print(f'conditions              : {conditions}')
    print(f'models ({len(models)}):')
    for m in models:
        print(f'    {m["slug"]:16s} -> {m["id"]}  ({m["family"]}/{m["tier"]})')
    total = len(models) * len(conditions) * len(rows)
    print(f'total chat calls if confirmed: {len(models)} x {len(conditions)} x '
          f'{len(rows)} = {total}')
    ex = rows[0]
    print(f'\n--- example prompts for CQ {ex["id"]} ({ex["wg"]}) ---')
    print(f'Q: {ex["question_en"]}')
    for cond in conditions:
        if cond == 'rag':
            print(f'\n[{cond}] (context retrieved live at run time from '
                  f'{[c.format(wg=ex["wg"].lower()) for c in RAG_COLLECTIONS]})')
            print(f'  system: {SYS[cond][:110]}...')
            continue
        msgs, _ = build_messages(cond, ex, cards, existing_cols)
        print(f'\n[{cond}]')
        print(f'  system: {msgs[0]["content"][:110]}...')
        u = msgs[1]['content']
        print(f'  user  : {u[:400]}{"..." if len(u) > 400 else ""}')
    print('\nRe-run with --confirm to execute. Rows already logged are skipped.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--confirm', action='store_true', help='actually make paid calls')
    ap.add_argument('--models', nargs='*', help='subset of model slugs/ids')
    ap.add_argument('--wg', nargs='*', help='subset of WGs, e.g. RAN1 RAN2')
    ap.add_argument('--conditions', nargs='*',
                    default=['closed_book', 'rag', 'kg_grounded'])
    ap.add_argument('--limit', type=int, help='cap number of CQs (even WG sample)')
    ap.add_argument('--workers', type=int, default=1,
                    help='concurrent CQs per (condition, model) block')
    ap.add_argument('--build-rag-cache', action='store_true',
                    help='only build the RAG context cache (embeddings), no chat')
    args = ap.parse_args()

    bc.load_env()
    if 'OPENROUTER_API_KEY' not in __import__('os').environ:
        print('ERROR: OPENROUTER_API_KEY not in env/.env', file=sys.stderr)
        return 2

    wgs = args.wg
    rows = load_bench(wgs, args.limit)
    cards = load_schema_cards()
    existing_cols = bc.existing_collections()

    if args.build_rag_cache:
        print(f'building RAG cache for {len(rows)} CQs...')
        for i, cq in enumerate(rows, 1):
            get_context(cq, existing_cols)
            if i % 25 == 0 or i == len(rows):
                print(f'  cached {i}/{len(rows)}', flush=True)
        return 0

    models = load_models(args.models)
    if not args.confirm:
        dry_run(models, args.conditions, wgs, rows, cards, existing_cols)
        return 0

    RESULTS.mkdir(parents=True, exist_ok=True)
    totals = {'calls': 0, 'cost': 0.0, 'errors': 0}
    for cond in args.conditions:
        for m in models:
            outp = RESULTS / cond / m['slug'] / 'all.jsonl'
            outp.parent.mkdir(parents=True, exist_ok=True)
            done = done_ids(outp)
            todo = [r for r in rows if r['id'] not in done]
            print(f'\n### {cond} | {m["slug"]} ({m["id"]}) | {len(todo)} to run '
                  f'({len(done)} cached) | workers={args.workers} ###', flush=True)
            if not todo:
                continue
            done_n = [0]
            with open(outp, 'a') as f:
                def _emit(row):
                    f.write(json.dumps(row, ensure_ascii=False) + '\n')
                    f.flush()
                    done_n[0] += 1
                    totals['calls'] += 1
                    if row['error']:
                        totals['errors'] += 1
                    if isinstance(row['cost'], (int, float)):
                        totals['cost'] += row['cost']
                    if done_n[0] % 20 == 0 or done_n[0] == len(todo):
                        print(f'  {cond}/{m["slug"]}: {done_n[0]}/{len(todo)}  '
                              f'cost~${totals["cost"]:.3f}  err={totals["errors"]}',
                              flush=True)
                if args.workers <= 1:
                    for cq in todo:
                        _emit(run_one(cond, m, cq, cards, existing_cols))
                else:
                    with ThreadPoolExecutor(max_workers=args.workers) as ex:
                        futs = {ex.submit(run_one, cond, m, cq, cards, existing_cols): cq
                                for cq in todo}
                        for fut in as_completed(futs):
                            try:
                                _emit(fut.result())
                            except Exception as e:  # noqa: BLE001
                                cq = futs[fut]
                                _emit({'id': cq['id'], 'wg': cq['wg'], 'phase': cq['phase'],
                                       'condition': cond, 'model_slug': m['slug'],
                                       'model_id': m['id'], 'raw_text': '', 'usage': {},
                                       'cost': None, 'latency_s': None, 'finish': None,
                                       'predicted_values': [],
                                       'error': f'{type(e).__name__}: {e}'})
    print(f'\n=== DONE: {totals["calls"]} calls, ~${totals["cost"]:.3f}, '
          f'{totals["errors"]} errors ===')
    return 0


if __name__ == '__main__':
    sys.exit(main())
