#!/usr/bin/env python3
"""bench_common.py — shared infra for the SpectraCQ baseline campaign.

Env, OpenRouter chat/embedding clients (httpx verify=False for environments
with a TLS-intercepting proxy), Qdrant semantic retrieval, Neo4j Cypher
execution, and lenient JSON parsing. Chat and embeddings both route through
OpenRouter; the embedding model is openai/text-embedding-3-small, the same
model that indexed the released collections. No LLM ever touches the gold
path — gold is pure re-execution of the reference Cypher in the release
package.
"""
import json
import os
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]   # repo root (holds release_package/)
BASE = Path(__file__).resolve().parent       # paper/baseline/
QDRANT = 'http://localhost:6333'
EMBED_MODEL = 'openai/text-embedding-3-small'
NEO4J_PORTS = {'RAN1': 7687, 'RAN2': 7688, 'RAN3': 7689, 'RAN4': 7690, 'RAN5': 7691}
# per-collection text field (tdoc chunks store body under `content`, others `text`)
TEXT_FIELD = {'tdoc_chunks': 'content'}


def load_env():
    """Populate os.environ from project .env (setdefault: real env wins)."""
    env = ROOT / '.env'
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _openai_client():
    import httpx
    from openai import OpenAI
    return OpenAI(
        base_url='https://openrouter.ai/api/v1',
        api_key=os.environ['OPENROUTER_API_KEY'],
        http_client=httpx.Client(verify=False, timeout=120),
    )


# ---------------------------------------------------------------- embeddings
_EMBED_CACHE = {}


def embed(text, retries=5):
    if text in _EMBED_CACHE:
        return _EMBED_CACHE[text]
    client = _openai_client()
    last = None
    for a in range(retries):
        try:
            r = client.embeddings.create(model=EMBED_MODEL, input=text)
            vec = r.data[0].embedding
            _EMBED_CACHE[text] = vec
            return vec
        except Exception as e:  # noqa: BLE001 — network/rate transient
            last = e
            time.sleep(min(2 ** a, 30))
    raise RuntimeError(f'embed failed after {retries}: {last}')


# ---------------------------------------------------------------- qdrant
def _qpost(path, body, timeout=30.0):
    req = urllib.request.Request(
        QDRANT + path, data=json.dumps(body).encode(),
        headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def existing_collections():
    req = urllib.request.Request(QDRANT + '/collections')
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.loads(r.read().decode())
    return {c['name'] for c in d['result']['collections']}


def _text_of(collection, payload):
    suffix = collection.split('_', 1)[1] if '_' in collection else collection
    field = TEXT_FIELD.get(suffix, 'text')
    return payload.get(field) or payload.get('text') or payload.get('content') or ''


def retrieve_context(wg, question, collections, top_per_col=6, keep=10, char_cap=800):
    """Embed question, search each existing WG collection, merge global top-`keep`.

    Returns (context_text, provenance list). Model-agnostic — cache by cq id.
    """
    vec = embed(question)
    pool = []
    for col in collections:
        try:
            r = _qpost(f'/collections/{col}/points/query',
                       {'query': vec, 'limit': top_per_col, 'with_payload': True})
        except Exception:  # noqa: BLE001 — a missing/empty collection must not abort
            continue
        for pt in r['result']['points']:
            pl = pt.get('payload', {})
            txt = ' '.join(_text_of(col, pl).split())
            if not txt:
                continue
            pool.append({
                'collection': col, 'score': round(float(pt['score']), 4),
                'chunkId': pl.get('chunkId'),
                'spec': pl.get('specNumber') or pl.get('trNumber') or pl.get('tdocNumber'),
                'section': pl.get('sectionNumber'),
                'text': txt[:char_cap],
            })
    pool.sort(key=lambda h: h['score'], reverse=True)
    top = pool[:keep]
    blocks = []
    for i, h in enumerate(top, 1):
        tag = f"{h['collection']}"
        if h['spec']:
            tag += f" {h['spec']}"
        if h['section']:
            tag += f" §{h['section']}"
        blocks.append(f"[{i}] ({tag}, sim={h['score']})\n{h['text']}")
    return '\n\n'.join(blocks), top


# ---------------------------------------------------------------- chat
def chat(model_id, messages, temperature=0.0, max_tokens=1500, retries=5):
    """One OpenRouter chat completion. Returns dict with text/usage/cost/latency."""
    client = _openai_client()
    last = None
    for a in range(retries):
        try:
            t0 = time.time()
            resp = client.chat.completions.create(
                model=model_id, messages=messages,
                temperature=temperature, max_tokens=max_tokens,
                extra_body={'usage': {'include': True}})
            dt = round(time.time() - t0, 2)
            txt = resp.choices[0].message.content or ''
            u = getattr(resp, 'usage', None)
            usage = {}
            cost = None
            if u is not None:
                usage = {'prompt_tokens': getattr(u, 'prompt_tokens', None),
                         'completion_tokens': getattr(u, 'completion_tokens', None),
                         'total_tokens': getattr(u, 'total_tokens', None)}
                cost = getattr(u, 'cost', None)
                if cost is None:
                    d = getattr(u, 'model_dump', lambda: {})() or {}
                    cost = d.get('cost')
            return {'text': txt, 'usage': usage, 'cost': cost, 'latency_s': dt,
                    'finish': resp.choices[0].finish_reason, 'error': None}
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(min(2 ** a, 30))
    return {'text': '', 'usage': {}, 'cost': None, 'latency_s': None,
            'finish': None, 'error': f'{type(last).__name__}: {last}'}


# ---------------------------------------------------------------- parsing
def parse_json_obj(text):
    """Best-effort first balanced {...} -> dict. Tolerates ```json fences/prose."""
    if not text:
        return None
    m = re.search(r'```(?:json)?\s*(.*?)```', text, re.DOTALL)
    body = m.group(1) if m else text
    start = body.find('{')
    while start != -1:
        depth = 0
        for i in range(start, len(body)):
            if body[i] == '{':
                depth += 1
            elif body[i] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(body[start:i + 1])
                    except Exception:  # noqa: BLE001
                        break
        start = body.find('{', start + 1)
    return None


def parse_answer_list(text):
    """Extract the answer set. Accepts {"answer":[...]}, a bare [...] array, or
    newline/comma-separated identifiers as a last resort. Returns list[str]."""
    obj = parse_json_obj(text)
    if isinstance(obj, dict):
        for k in ('answer', 'answers', 'values', 'result', 'results'):
            if isinstance(obj.get(k), list):
                return [str(x).strip() for x in obj[k] if str(x).strip()]
    # [^\[\]] already spans newlines; the old (?:[^\[\]]|\n)* form made the two
    # alternatives overlap on \n, which backtracks exponentially on a '[' with no
    # closing ']'. A plain negated class is linear and matches the same strings.
    m = re.search(r'\[[^\[\]]*\]', text or '')
    if m:
        try:
            arr = json.loads(m.group(0))
            if isinstance(arr, list):
                return [str(x).strip() for x in arr if str(x).strip()]
        except Exception:  # noqa: BLE001
            pass
    return []


def parse_cypher(text):
    obj = parse_json_obj(text)
    if isinstance(obj, dict):
        for k in ('cypher', 'query', 'cql'):
            if isinstance(obj.get(k), str) and obj[k].strip():
                return obj[k].strip()
    m = re.search(r'```(?:cypher)?\s*(MATCH.*?)```', text or '', re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r'\b(MATCH\b.*?RETURN\b.*)', text or '', re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else None


# ---------------------------------------------------------------- neo4j exec
def canon(v):
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True, default=str)
    return str(v)


def exec_cypher(wg, cypher, row_cap=2000, timeout_s=30):
    """Execute a candidate Cypher read-only-ish; return first-column canon values.

    Returns dict {status, error, columns, primary_column, primary_values, row_count}.
    Guards against obvious write clauses so a hallucinated query can't mutate data.
    """
    from neo4j import GraphDatabase
    lowered = (cypher or '').lower()
    for bad in (' create ', ' merge ', ' delete ', ' set ', ' remove ', ' drop '):
        if bad in f' {lowered} ':
            return {'status': 'REJECTED_WRITE', 'error': f'write clause {bad.strip()}',
                    'columns': [], 'primary_column': None, 'primary_values': [], 'row_count': 0}
    pw = os.environ.get('NEO4J_PASSWORD')
    if not pw:
        raise SystemExit('set NEO4J_PASSWORD to your Neo4j bolt password before running')
    drv = GraphDatabase.driver(f'bolt://localhost:{NEO4J_PORTS[wg]}', auth=('neo4j', pw))
    try:
        with drv.session() as s:
            # timeout must be a transaction-level timeout; passing it to
            # session.run() would silently bind it as a no-op Cypher parameter.
            with s.begin_transaction(timeout=timeout_s) as tx:
                recs = list(tx.run(cypher))
                datas = [r.data() for r in recs]
                cols = list(recs[0].keys()) if recs else []
            pcol = cols[0] if cols else None
            pvals = sorted({canon(d.get(pcol)) for d in datas}) if pcol else []
            return {'status': 'OK', 'error': None, 'columns': cols,
                    'primary_column': pcol, 'primary_values': pvals[:5000],
                    'row_count': len(recs)}
    except Exception as e:  # noqa: BLE001
        return {'status': 'ERROR', 'error': f'{type(e).__name__}: {str(e)[:300]}',
                'columns': [], 'primary_column': None, 'primary_values': [], 'row_count': 0}
    finally:
        drv.close()
