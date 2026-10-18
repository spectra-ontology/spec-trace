#!/usr/bin/env python3
"""Spec: offline replay of source-snapshot four-method evaluation evidence.
Ontology: output scoring and documentary provenance are separate roles.
Cycle: KDD Datasets and Benchmarks Cycle1.
배경: preserve first responses, failures, original inputs and runtime hashes.
사용: --evidence PATH; no credentials, network, database or container needed.
LLM 호출: none.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
METHODS = ('text2cypher', 'text2sql', 'single_retrieval', 'iterative_retrieval')
def load(p): return json.loads(Path(p).read_text())
def read(p): return [json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]
def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()
def require(ok, message):
    if not ok: raise ValueError(message)
def pure_retrieval(path):
    functions = {'canonical', 'structural_schema', 'public_contract', 'parse_answer'}
    constants = {'QUERY_INSTRUCTION', 'ANSWER_INSTRUCTION'}
    selected = []
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.FunctionDef) and node.name in functions: selected.append(node)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in constants for t in node.targets): selected.append(node)
    env = {'json': json}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec'), env)
    require(functions | constants <= set(env), 'incomplete prompt/parser projection')
    return env


def verify(evidence):
    e = Path(evidence).resolve(); m = load(e / 'evaluation_manifest.json')
    actual = {str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name != 'evaluation_manifest.json'}
    require(actual == set(m['files']), 'evaluation file set differs')
    for name, pin in m['files'].items():
        path = (e / name).resolve()
        require(path.is_relative_to(e) and sha(path) == pin['sha256'] and path.stat().st_size == pin['bytes'], 'file differs: ' + name)
    run = e / 'results'; reg = e / 'runtime/registration'
    protocol = load(run / 'protocol.json'); config = load(run / 'source_config.json')
    contract_path = load(e / 'evaluation_contract_location.json')['evaluation_contract_subdir']
    contract_dir = (e / contract_path).resolve(); require(contract_dir.is_relative_to(e), 'contract path escapes evidence')
    task, = read(contract_dir / 'tasks.jsonl'); public, = read(run / 'public_tasks.jsonl')
    require(protocol['model'] == 'anthropic/claude-opus-4.8' and protocol['provider'] == 'Anthropic', 'provider/model differs')
    require(protocol['generation_workers'] == 8 and protocol['execution_workers'] == 2 and protocol['retry_policy']['answer_quality_retry'] is False, 'execution protocol differs')
    require(protocol['cohort_n'] == 1 and protocol['cohort_ids'] == [task['id']], 'denominator/identity differs')
    require(public['id'] == task['id'] and public['repair_sha256'] == task['repair_sha256'] == protocol['repair_sha256'], 'repair differs')
    require(public['question_en'] == task['question_en'] and hashlib.sha256(task['question_en'].encode()).hexdigest() == protocol['question_sha256'], 'English differs')
    require(sha(run / 'public_tasks.jsonl') == protocol['public_tasks_sha256'] and sha(run / 'source_config.json') == protocol['source_config_sha256'], 'frozen input differs')
    for name, expected in protocol['code_pins'].items(): require(sha(reg / name) == expected, 'frozen runtime differs: ' + name)
    for name, expected in protocol['schema_pins'].items(): require(sha(run / name) == expected, 'frozen schema differs')
    require(sha(run / 'retrieval_corpus_inventory.json') == protocol['retrieval_inventory_sha256'], 'corpus inventory differs')
    for key, rel in m['packaged_source_pin_locations'].items(): require(sha(e / rel) == protocol['source_pins'][key]['sha256'], 'source pin differs: ' + key)
    for key, rel in m.get('packaged_source_pin_shards', {}).items():
        descriptor_path = (e / rel).resolve()
        require(descriptor_path.is_relative_to(e), 'shard descriptor escapes evidence')
        descriptor = load(descriptor_path)
        compressed_shards = descriptor['format'] == 'ordered_exact_byte_contiguous_gzip_shards_v1'
        require(compressed_shards or descriptor['format'] == 'ordered_exact_byte_contiguous_shards_v1', 'shard format differs')
        expected_pin = protocol['source_pins'][key]
        require(descriptor['sha256'] == expected_pin['sha256'] and descriptor['bytes'] == expected_pin['bytes'], 'whole raw shard pin differs')
        concat, offset, seen = hashlib.sha256(), 0, set()
        for part in descriptor['parts']:
            part_path = (descriptor_path.parent / part['path']).resolve()
            require(part_path.is_relative_to(descriptor_path.parent) and part['path'] not in seen, 'unsafe or duplicate shard path')
            seen.add(part['path'])
            require(part['offset_bytes'] == offset and part_path.stat().st_size == part['bytes']
                    and 0 < part['bytes'] <= descriptor['max_shard_bytes'] and sha(part_path) == part['sha256'], 'raw shard bytes/order differ')
            import gzip
            opener = gzip.open if compressed_shards else open
            h, n = hashlib.sha256(), 0
            with opener(part_path, 'rb') as raw:
                for block in iter(lambda: raw.read(2 ** 20), b''):
                    concat.update(block); h.update(block); n += len(block)
            if compressed_shards:
                require(n == part['uncompressed_bytes'] and h.hexdigest() == part['uncompressed_sha256'], 'decompressed shard differs')
            else:
                require(n == part['bytes'] and h.hexdigest() == part['sha256'], 'raw shard differs')
            offset += n
        require(offset == descriptor['bytes'] and concat.hexdigest() == descriptor['sha256'], 'raw exact concatenation differs')
    # Lossless export compression does not change registered runtime inputs.
    import gzip
    for key, item in m.get('packaged_source_pin_compressed', {}).items():
        compressed_path = (e / item['path']).resolve()
        require(compressed_path.is_relative_to(e) and item['format'] == 'exact_gzip_stream_v1', 'unsafe compressed pin')
        require(sha(compressed_path) == item['sha256'] and compressed_path.stat().st_size == item['bytes'], 'compressed bytes differ')
        expected_pin = protocol['source_pins'][key]
        h, n = hashlib.sha256(), 0
        with gzip.open(compressed_path, 'rb') as source:
            for block in iter(lambda: source.read(2 ** 20), b''):
                h.update(block); n += len(block)
        require(h.hexdigest() == item['uncompressed_sha256'] == expected_pin['sha256']
                and n == item['uncompressed_bytes'] == expected_pin['bytes'], 'lossless decompression differs')
    require(sha(e / 'inputs/actual_gate.json') == config['actual_gate_pin']['sha256'], 'completed source gate differs')
    spec = importlib.util.spec_from_file_location('offline_structured', reg / 'runtime/structured_adapter.py')
    structured = importlib.util.module_from_spec(spec); spec.loader.exec_module(structured)
    structured.reject_private(public)
    ret = pure_retrieval(reg / 'runtime/retrieval_adapter.py')
    identifier, wg = task['id'], public['wg']
    ids = {identifier + '_' + x for x in ('Text2Cypher', 'Text2SQL', 'C_answer', 'D_followup', 'D_answer')}
    requests = {load(f)['request_id']: load(f) for f in (run / 'calls').glob('*.request.json')}
    require(set(requests) == ids and len(requests) == 5, 'first request set differs')
    expected = {}
    for arm, kind, tag in [('A', 'graph', 'Text2Cypher'), ('B', 'sql', 'Text2SQL')]:
        inp = dict(public); inp[kind + '_schema'] = load(run / 'schemas' / (wg + '_' + kind + '.json'))
        expected[identifier + '_' + tag] = structured.messages_for(inp, arm)
    contract = ret['public_contract'](public)
    for arm in ('C', 'D'):
        base = run / 'retrieval' / arm / identifier
        initial, final = load(base / 'initial_context.json'), load(base / 'final_context.json')
        require(len(final['documents']) <= protocol['retrieval_protocol']['final_context_documents'], 'context cap differs')
        prefix = ret['canonical']({'question': public['question_en'], 'contract': contract}) + '\nSOURCE PASSAGES:\n'
        if arm == 'D': expected[identifier + '_D_followup'] = [{'role': 'system', 'content': ret['QUERY_INSTRUCTION']}, {'role': 'user', 'content': prefix + '\n\n'.join(d['formatted'] for d in initial['documents'])}]
        expected[identifier + '_' + arm + '_answer'] = [{'role': 'system', 'content': ret['ANSWER_INSTRUCTION']}, {'role': 'user', 'content': prefix + '\n\n'.join(d['formatted'] for d in final['documents'])}]
    cost, unknown, responses_n, content = 0.0, 0, 0, {}
    for rid, request in requests.items():
        payload = request['payload']
        require(payload['messages'] == expected[rid], 'prompt reconstruction differs: ' + rid)
        require(payload['model'] == protocol['model'] and payload['provider'] == {'only': ['Anthropic'], 'allow_fallbacks': False, 'require_parameters': True}, 'provider request differs')
        require(request['payload_sha256'] == hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode()).hexdigest() and request['authorization_header_omitted'] is True, 'payload bytes/authorization differs')
        files = sorted((run / 'calls').glob(rid + '.attempt*.response.json'))
        require(1 <= len(files) <= protocol['retry_policy']['transport_attempts'], 'transport attempts exceeded')
        outcome = load(run / 'calls' / (rid + '.outcome.json'))
        for f in files:
            response = load(f); require(response['request_id'] == rid, 'response identity differs')
            raw = response.get('response')
            if isinstance(raw, dict):
                charge = raw.get('usage', {}).get('cost')
                if type(charge) in (int, float): cost += charge
                else: unknown += 1
            responses_n += 1
        response = load(files[-1]); raw = response['response']
        require(response['http_status'] == 200 and raw['model'] == protocol['model'] and raw['provider'] == protocol['provider'], 'actual terminal response differs')
        require(raw['choices'][0]['finish_reason'] == 'stop' and outcome['ok'] is True, 'terminal response status differs')
        content[rid] = raw['choices'][0]['message']['content']
        require(outcome['content'] == content[rid], 'response content differs')
    require(load(run / 'generation_complete.json') == {'completed_method_items': 4, 'required': 4}, 'method denominator differs')
    guard = load(run / 'source_guards' / (wg + '.json'))
    require(guard['unchanged'] is True and guard['before'] == guard['after'], 'execution source guard failed')
    require(guard['before']['ttl_sha256'] == protocol['source_pins']['graph_ttl_path']['sha256'] and guard['before']['import_manifest_sha256'] == protocol['source_pins']['graph_import_manifest_path']['sha256'] and guard['sql_sha256'] == protocol['source_pins']['sql_db_path']['sha256'], 'native source pin mismatch')
    parse_failure_replays = 0
    structured_format_failure_replays = 0
    for method in METHODS:
        pred, = read(run / method / 'predictions.jsonl'); status, = read(run / method / 'statuses.jsonl')
        require(pred['id'] == status['id'] == identifier and pred['repair_sha256'] == status['repair_sha256'] == task['repair_sha256'], 'method identity differs')
        outcome = load(run / status['artifact'])
        require(pred['records'] == outcome['records'] and status['status'] == outcome['status'].upper(), 'prediction/status projection differs')
        if method in ('text2cypher', 'text2sql'):
            tag = 'Text2Cypher' if method == 'text2cypher' else 'Text2SQL'
            try:
                generated = json.loads(content[identifier + '_' + tag])
                if (not isinstance(generated, dict) or set(generated) != {'query', 'abstain'}
                        or type(generated['query']) is not str or type(generated['abstain']) is not bool
                        or len(generated['query'].encode()) > 65536
                        or generated['abstain'] and generated['query'].strip()
                        or not generated['abstain'] and not generated['query'].strip()):
                    raise ValueError('invalid generated query envelope')
            except (TypeError, ValueError, KeyError) as exc:
                require(status['status'] == 'GENERATION_FORMAT_ERROR' and outcome['error_class'] == type(exc).__name__
                        and outcome['records'] == [] and outcome['abstain'] is True
                        and outcome['generated_query'] is None and outcome['query_sha256'] is None
                        and outcome['execution'] is None, 'structured format failure not exactly reproducible')
                structured_format_failure_replays += 1
                continue
            require(generated == {'query': outcome['generated_query'], 'abstain': outcome.get('abstain', False)} or generated == {'query': outcome['generated_query'], 'abstain': False}, 'generated query differs')
            require(outcome['query_sha256'] == hashlib.sha256(outcome['generated_query'].encode()).hexdigest(), 'query hash differs')
            if generated['abstain']:
                require(status['status'] == 'ABSTAIN' and outcome['records'] == [], 'structured abstention differs')
            else:
                receipt = outcome['execution']
                require(receipt['status'] == status['status'], 'execution status differs')
                if status['status'] == 'OK':
                    require(receipt['complete'] and not receipt['truncated'] and outcome['records'] == receipt['rows'], 'saved complete execution differs')
                    if method == 'text2cypher': require(receipt['plan_query_type'] == receipt['execution_query_type'] == 'r' and receipt['execution_summary_complete'] and receipt['rollback_completed'], 'native read/rollback receipt differs')
                else:
                    require(not receipt['complete'] and outcome['records'] == [] and outcome['abstain'] is True, 'failed execution became answer records')
                    require(status['status'] in {'ERROR','ROW_CAP','BYTE_CAP','TIMEOUT','SOURCE_MISMATCH','REJECTED','DUPLICATE_COLUMNS'}, 'unexpected structured failure')
        else:
            arm = 'C' if method == 'single_retrieval' else 'D'
            try: parsed = ret['parse_answer'](content[identifier + '_' + arm + '_answer'])
            except (ValueError, TypeError, KeyError) as exc:
                require(status['status'] == 'ANSWER_PARSE_ERROR' and outcome['records'] == [] and outcome['error'] == str(exc), 'parse failure not exactly reproducible')
                parse_failure_replays += 1
            else:
                derived = 'ABSTAINED' if parsed['abstain'] else ('OK' if parsed['complete'] else 'PARTIAL')
                require(status['status'] == derived and parsed['records'] == outcome['records'], 'retrieval parse projection differs')
    usage = load(e / 'actual_call_usage.json')
    require(usage['requests_n'] == 5 and usage['actual_http_responses_n'] == responses_n and usage['unknown_cost_responses_n'] == unknown and abs(usage['known_cost_usd'] - cost) < 1e-12 and usage['quality_regeneration_n'] == 0, 'usage receipt differs')
    sys.path.insert(0, str(e / 'tools'))
    from score_retained_four_methods import calculate
    scores, analysis = calculate(e)
    require(analysis == load(run / 'analysis.json'), 'analysis replay differs')
    for method, values in scores.items():
        for name, value in values.items(): require(value == load(run / method / (name + '.json')), 'score replay differs')
    return {'status': 'PASS', 'evaluation_manifest_sha256': sha(e / 'evaluation_manifest.json'),
            'files_verified': len(actual), 'cohort_n': 1, 'method_items': 4, 'requests': 5,
            'actual_http_responses_n': responses_n, 'known_cost_usd': cost, 'unknown_cost_responses_n': unknown,
            'quality_regeneration_n': 0, 'exact_prompt_reconstruction_n': 5,
            'retrieval_parse_failure_replays_n': parse_failure_replays, 'structured_format_failure_replays_n': structured_format_failure_replays, 'strict_score_replays_n': 4,
            'limitations': 'Retained prompts, response parsing and strict requested-record metrics only. Live provider, graph, SQL and retrieval are not rerun. Does not judge generated query semantics/provenance, merge frozen cohorts or establish complete graph/text coverage equality.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--evidence', type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args(); print(json.dumps(verify(args.evidence), ensure_ascii=False))
