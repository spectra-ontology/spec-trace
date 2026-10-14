#!/usr/bin/env python3
"""Offline information-access audit; never generates/retries/scorers model calls.

Inputs are frozen task/gold files and already retained requests/retrieval logs.
Optional source probes check a small deterministic set of documentary IDs, not
answer support. Every admitted ID remains in the denominator, including IDs
whose requests have not been created. Outputs live outside the runtime bundle.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import sqlite3
import sys
import time

AUDIT_PARENT = Path(__file__).resolve().parents[1]
# Local development keeps runtime scripts beside audit/. The released evidence
# package preserves their bytes under runtime/ instead. Never substitute a
# runtime implementation merely because the public layout differs.
BASE = AUDIT_PARENT if (AUDIT_PARENT / 'structured_adapter.py').exists() else AUDIT_PARENT / 'runtime'
ARMS = {'A': 'text2cypher', 'B': 'text2sql', 'C': 'single_retrieval', 'D': 'iterative_retrieval'}
STAGES = {'A': ['Text2Cypher'], 'B': ['Text2SQL'], 'C': ['C_answer'], 'D': ['D_followup', 'D_answer']}
PRIVATE_KEYS = {'reference_query', 'original_query', 'gold', 'gold_rows', 'reference_outputs',
                'primary_review', 'secondary_review', 'semantic_evidence', 'source_column_or_expression',
                'source_order_keys', 'native_rows', 'order_groups', 'scorer_checks', 'repair_reason'}
DOCUMENT_ID = re.compile(r'^(?:R[1-5]-\d{6,}(?:r\d+)?|(?:AGR|CON|WA|RES)-[A-Za-z0-9_.-]+)$', re.I)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    path = Path(path)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        # Writers can be in progress during the interim audit. Never turn this
        # into a completed, leaked or failed scientific prediction.
        return {'_audit_unreadable_pending': True}


def read_lines(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]


def forbidden_paths(value, prefix=''):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            name = prefix + '/' + str(key)
            if key in PRIVATE_KEYS:
                found.append(name)
            found.extend(forbidden_paths(child, name))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(forbidden_paths(child, prefix + '/' + str(index)))
    return found


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    item = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(item)
    return item


def paths_context(run, arm, identifier, stage):
    context = 'initial_context.json' if stage == 'D_followup' else 'final_context.json'
    return run / 'retrieval' / arm / identifier / context


def effective_request_path(run, identifier, stage):
    """Cached supplement outcomes keep their actual original request, not a new call."""
    path=run/'calls'/(identifier+'_'+stage+'.request.json')
    if path.exists():return path,'actual_request_in_this_run'
    protocol=load(run/'protocol.json') or {}
    original=(protocol.get('transport_recovery') or {}).get('original_run')
    if original:
        # Packaged runs can be replayed side by side without the authors'
        # absolute filesystem paths; every selected artifact is still hashed.
        original=Path(original)
        sibling=run.parent/original.name
        if sibling.exists():original=sibling
        old=original/'calls'/(identifier+'_'+stage+'.request.json')
        if old.exists():return old,'cached_actual_original_request_no_new_call'
    return path,'absent'


def audit_request(run, public, arm, stage, structured, retrieval):
    path,request_origin=effective_request_path(run,public['id'],stage)
    value = load(path)
    if value is None:
        closed=(run/'generation_complete.json').exists()
        return {'stage': stage, 'status': 'not_issued_in_complete_generation' if closed else 'not_present_yet',
                'request_origin':request_origin,
                'scope':'Planned stage remains in denominator; no request/no model output is not a leakage PASS.'}
    if value.get('_audit_unreadable_pending'):
        return {'stage': stage, 'status': 'unreadable_pending'}
    expected = None
    context_hash = None
    if arm in {'A', 'B'}:
        kind = 'graph' if arm == 'A' else 'sql'
        task = dict(public)
        task[kind + '_schema'] = load(run / 'schemas' / (public['wg'] + '_' + kind + '.json'))
        expected = structured.messages_for(task, arm)
    else:
        context_path = paths_context(run, arm, public['id'], stage)
        context = load(context_path)
        if context is None or context.get('_audit_unreadable_pending'):
            return {'stage': stage, 'status': 'context_evidence_not_ready', 'request_sha256': sha(path)}
        passages = '\n\n'.join(d['formatted'] for d in context['documents'])
        context_hash = sha(context_path)
        instruction = retrieval.QUERY_INSTRUCTION if stage == 'D_followup' else retrieval.ANSWER_INSTRUCTION
        visible = {'question': public['question_en'], 'contract': retrieval.public_contract(public)}
        expected = [{'role': 'system', 'content': instruction},
                    {'role': 'user', 'content': canonical(visible) + '\nSOURCE PASSAGES:\n' + passages}]
    payload = value.get('payload', {})
    serialized_hash = hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode()).hexdigest()
    actual = payload.get('messages')
    prompt_match = actual == expected
    # Check the structured, caller-authored JSON before source passages. Source
    # documents may legitimately contain ordinary words such as "gold".
    visible = None
    if actual and len(actual) == 2:
        try:
            visible = json.loads(actual[1]['content'].split('\nSOURCE PASSAGES:\n', 1)[0])
        except (KeyError, TypeError, ValueError):
            pass
    bad = forbidden_paths(visible)
    replay_identity=None
    if value.get('identical_original_payload'):
        old=Path(value['original_request'])
        protocol=load(run/'protocol.json') or {}
        root=(protocol.get('transport_recovery') or {}).get('original_run')
        if root:
            packaged=run.parent/Path(root).name/'calls'/old.name
            if packaged.exists():old=packaged
        prior=load(old)
        replay_identity=bool(prior and sha(old)==value.get('original_request_sha256')
              and prior['payload']==payload and prior['payload_sha256']==serialized_hash)
    return {'stage': stage, 'status': 'PASS' if prompt_match and not bad and serialized_hash == value.get('payload_sha256') and replay_identity is not False else 'FAIL',
            'request_sha256': sha(path), 'serialized_payload_sha256': serialized_hash,
            'request_origin':request_origin,'request_path':str(path),
            'exact_original_replay_payload_verified':replay_identity,
            'conditional_predeclared_new_D_answer':value.get('conditional_predeclared_new_D_answer',False),
            'recorded_payload_hash_matches': serialized_hash == value.get('payload_sha256'),
            'exact_messages_reconstructed_from_public_inputs_and_retained_context': prompt_match,
            'private_evidence_keys_in_caller_authored_JSON': bad,
            'context_file_sha256': context_hash,
            'scope': 'Exact retained serialized request; not a claim about unavailable provider-side internals.'}


def documentary_anchors(gold, maximum):
    """Only unmistakable documentary IDs; numeric answers/company names excluded."""
    found = []
    for record in gold.get('records', []):
        for value in record.values():
            if isinstance(value, str) and DOCUMENT_ID.fullmatch(value) and value not in found:
                found.append(value)
                if len(found) == maximum:
                    return found
    return found


def probe(con, anchor, timeout=.35, cap=200):
    began = time.monotonic()
    # Phrase matching is a bounded candidate lookup. Exact string presence is
    # confirmed separately; an absent lookup does not establish corpus absence.
    expression = '"' + anchor.replace('"', '""') + '"'
    con.set_progress_handler(lambda: int(time.monotonic() - began > timeout), 1000)
    candidates = 0
    evidence = []
    complete = False
    error = None
    try:
        cur = con.execute('SELECT d.collection,d.point_id,d.chunk_id,d.text FROM search '
                          'JOIN docs d ON d.id=search.rowid WHERE search MATCH ? LIMIT ?',
                          (expression, cap + 1))
        for collection, point, chunk, text in cur:
            candidates += 1
            if candidates > cap:
                break
            if anchor in text:
                evidence.append({'collection': collection, 'point_id': point, 'chunk_id': chunk})
                if len(evidence) >= 2:
                    break
        else:
            complete = True
    except sqlite3.Error as exc:
        error = str(exc)
    finally:
        con.set_progress_handler(None, 0)
    return {'anchor': anchor, 'anchor_sha256': hashlib.sha256(anchor.encode()).hexdigest(),
            'status': 'literal_presence_observed' if evidence else 'presence_not_established',
            'candidate_documents_read': min(candidates, cap), 'candidate_read_complete': complete,
            'literal_witness_documents': evidence, 'error': error,
            'elapsed_seconds': round(time.monotonic() - began, 5),
            'semantic_answer_support_established': False}


def corpus_connection(shard, root):
    path = Path(shard['path'])
    path = path if path.is_absolute() else root / path
    st = path.stat()
    if st.st_size != shard['bytes'] or st.st_mtime_ns != shard['mtime_ns']:
        raise ValueError('Retained corpus file identity changed')
    con = sqlite3.connect(path.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    for statement in ['PRAGMA query_only=ON', 'PRAGMA cache_size=-16384', 'PRAGMA temp_store=FILE', 'PRAGMA threads=1']:
        con.execute(statement)
    return con


def context_information(run, arm, task, anchors):
    folder = run / 'retrieval' / arm / task['id']
    rounds = []
    for number in (1, 2):
        report = load(folder / ('retrieval_round_' + str(number) + '.json'))
        if report and not report.get('_audit_unreadable_pending'):
            rounds.append({'round': number, 'status': report.get('status'), 'matching_documents': report.get('matching_documents'),
                           'ranked_candidates_retained': len(report.get('hits', [])),
                           'candidate_truncated': report.get('context_candidate_truncated'),
                           'candidate_population_read_complete': report.get('matched_population_read_complete'),
                           'query_sha256': report.get('query_sha256'), 'elapsed_seconds': report.get('elapsed_seconds')})
    value = load(folder / 'final_context.json')
    context_ready = bool(value and not value.get('_audit_unreadable_pending'))
    docs = value.get('documents', []) if context_ready else []
    literal = {anchor: [d['point_id'] for d in docs if anchor in d.get('formatted', '')] for anchor in anchors}
    result = load(run / 'arm_outputs' / ARMS[arm] / (task['id'] + '.json'))
    if result and result.get('_audit_unreadable_pending'):
        result = None
    return {'retrieval_rounds': rounds, 'final_context_ready': context_ready,
            'actually_sent_answer_request_present': effective_request_path(run,task['id'],arm+'_answer')[0].exists(),
            'selected_context_documents': len(docs),
            'context_stats': value.get('stats') if context_ready else None,
            'context_documents_truncated': sum(bool(d.get('source_text_truncated') or d.get('source_header_truncated')) for d in docs),
            'gold_documentary_anchor_literal_in_context': literal,
            'retained_outcome_status': result.get('status') if result else 'not_finished_yet',
            'model_self_reported_complete': result.get('self_reported_complete') if result else None,
            'requested_population_completeness_verified': False,
            'semantic_answer_support_status': 'unestablished_by_this_lexical_audit',
            'note': 'Lexical corpus matches, presence of selected IDs and finite context do not certify the requested relations, count or entire answer population.'}


def schema_information(run, protocol, relational, source_schema):
    original = json.loads(source_schema.read_text())
    results = {}
    for wg, group in original['working_groups'].items():
        graph_path = run / 'schemas' / (wg + '_graph.json')
        sql_path = run / 'schemas' / (wg + '_sql.json')
        graph, sql = load(graph_path), load(sql_path)
        manifest_path = relational / (wg + '.manifest.json')
        manifest = load(manifest_path)
        expected = {label: {f['name'] for f in fields} for label, fields in group['label_properties'].items()}
        gprops = {label: set(props) - {'iri'} for label, props in graph['properties_by_label'].items()}
        sprops = {label: set(props) - {'node_id'} for label, props in sql['label_tables'].items()}
        patterns = {(r['from_label'], r['relationship'], r['to_label']) for r in group['relationship_triples']}
        pin_checks = {str(p.relative_to(run)): sha(p) == protocol['schema_pins'][str(p.relative_to(run))]
                      for p in (graph_path, sql_path)}
        manifest_match = sha(manifest_path) == protocol['sql_manifests'][wg]['sha256']
        card_match = sql == manifest['schema']
        checks = {'schema_pins_match': all(pin_checks.values()), 'SQL_manifest_pin_match': manifest_match,
                  'SQL_card_equals_frozen_manifest_schema': card_match,
                  'graph_source_property_sets_equal': gprops == expected,
                  'SQL_source_property_sets_equal': sprops == expected,
                  'directed_relationship_patterns_equal': set(map(tuple, graph['directed_relationships'])) == patterns == set(map(tuple, sql['directed_relationships'])),
                  'common_loader_identity_in_graph_and_SQL_cards': bool(sql.get('node_identity')) and all('iri' in p for p in graph['properties_by_label'].values())}
        results[wg] = {'status': 'PASS' if all(checks.values()) else 'FAIL', 'checks': checks,
                       'nodes': manifest['nodes'], 'relationships': manifest['relationships'],
                       'full_value_equivalence_evidence': 'sql_encoding_verification.json and SQL construction manifests; static schema equality alone does not prove values.',
                       'db_sha256': manifest['db_sha256'], 'manifest_sha256': sha(manifest_path)}
    return results


def SQL_null_duplicates(relational):
    """Lightweight read-only diagnostics; constraints retain entity/edge identity."""
    result = {}
    for wg in ['RAN1', 'RAN2', 'RAN3', 'RAN4', 'RAN5']:
        path = relational / (wg + '.sqlite')
        con = sqlite3.connect(path.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
        con.execute('PRAGMA query_only=ON'); con.execute('PRAGMA cache_size=-16384')
        types = dict(con.execute('SELECT native_type,count(*) FROM node_property GROUP BY native_type'))
        agenda = con.execute('SELECT count(*),count(id),count(DISTINCT id) FROM AgendaItem').fetchone()
        identity = con.execute('SELECT count(*),count(iri),count(DISTINCT iri) FROM node_identity').fetchone()
        indexed = {table: [dict(name=row[1], unique=bool(row[2])) for row in con.execute('PRAGMA index_list("' + table + '")')]
                   for table in ['node_label', 'node_property', 'edge', 'node_identity']}
        con.close()
        result[wg] = {'native_property_type_counts': types, 'explicit_null_native_properties': types.get('null', 0),
                       'agenda_rows': agenda[0], 'agenda_business_ID_nonnull': agenda[1],
                       'agenda_business_ID_distinct_nonnull': agenda[2],
                       'agenda_null_business_IDs': agenda[0] - agenda[1],
                       'agenda_repeated_business_IDs': agenda[1] - agenda[2],
                       'loader_identity_rows': identity[0], 'loader_identity_nonnull': identity[1], 'loader_identity_unique': identity[2],
                       'actual_unique_indexes': indexed,
                       'null_policy': 'Absent wide property is SQL NULL; node_property registry retains explicit native values separately. Anonymous agenda entities use shared auxiliary loader identity in three declared contracts.',
                       'duplicate_policy': 'Repeated business IDs do not merge distinct node_id entities. Same identity in multiple label tables denotes the same entity. Unique (src,rel,dst) edges follow the frozen RDF restoration rather than inventing multiplicity.'}
    return result


def transport_information(run):
    statuses = Counter(); sources = Counter(); requests = set(); key_requests=set(); provider_outputs = 0
    example = None;key_example=None
    for path in sorted((run / 'calls').glob('*.response.json')):
        value = load(path)
        if not value or value.get('_audit_unreadable_pending'):
            continue
        statuses[str(value.get('http_status'))] += 1
        response = value.get('response') or {}
        error = response.get('error') or {}
        meta = error.get('metadata') or {}
        if meta.get('limit_source'):
            sources[meta['limit_source']] += 1
        if (value.get('http_status') == 402 and meta.get('limit_source') == 'openrouter_in_flight_budget'
                and error.get('code')==402 and not response.get('choices')):
            requests.add(value['request_id'])
            if example is None:
                example = {'artifact': str(path.relative_to(run)), 'sha256': sha(path), 'http_status': 402,
                           'reason': meta.get('reason'), 'limit_source': meta['limit_source']}
        if (value.get('http_status') == 403 and error.get('code')==403
                and meta.get('limit_source')=='openrouter_key_limit' and not response.get('choices')):
            key_requests.add(value['request_id'])
            if key_example is None:key_example={'artifact':str(path.relative_to(run)),'sha256':sha(path),
                                  'http_status':403,'limit_source':meta['limit_source']}
        provider_outputs += bool(response.get('choices'))
    return {'response_attempt_status_counts': dict(statuses), 'limit_source_counts': dict(sources),
            'distinct_requests_rejected_for_inflight_budget': len(requests),
            'distinct_requests_rejected_for_key_limit':len(key_requests),
            'response_attempts_with_provider_choices': provider_outputs,
            'inflight_budget_error_example': example,
            'key_limit_error_example':key_example,
            'official_primary_sources': ['https://openrouter.ai/docs/api_reference/limits', 'https://openrouter.ai/docs/api_reference/errors-and-debugging'],
            'interpretation': 'Exact402/openrouter_in_flight_budget and exact403/openrouter_key_limit with no provider choices are distinct pre-provider infrastructure limits. A key spend cap needs external unblocking; other403 or402 sources are not eligible by inference. Original frozen policy did not retry these statuses; separately registered recovery preserves original attempts. These are actual response-attempt diagnostics, not final request eligibility; earlier real choices would bar recovery.'}


def audit(args):
    started = time.monotonic(); observed_start = datetime.now(timezone.utc).isoformat()
    run, bundle = args.run.resolve(), args.bundle.resolve()
    protocol = load(run / 'protocol.json')
    tasks = read_lines(bundle / 'tasks.jsonl'); gold = {x['id']: x for x in read_lines(bundle / 'reference_gold.jsonl')}
    public = read_lines(run / 'public_tasks.jsonl'); byid = {x['id']: x for x in public}
    ids = [t['id'] for t in tasks]
    if ids != protocol['cohort_ids'] or len(ids) != protocol['admitted_n'] or set(byid) != set(ids) or set(gold) != set(ids):
        raise ValueError('Frozen task/public/gold denominator differs')
    if any(sha(bundle / f) != protocol[k] for f, k in [('tasks.jsonl', 'tasks_sha256'), ('reference_gold.jsonl', 'gold_sha256')]):
        raise ValueError('Frozen offline task/gold changed')
    if sha(run / 'public_tasks.jsonl') != protocol['public_tasks_sha256']:
        raise ValueError('Frozen public task changed')
    code_checks = {name: sha(BASE / name) == pin for name, pin in protocol['code_pins'].items()}
    if not all(code_checks.values()):
        raise ValueError('Frozen runtime code changed; do not reconstruct prompts using another implementation')
    sys.path.insert(0, str(BASE))
    structured = module('_information_structured', BASE / 'structured_adapter.py')
    retrieval = module('_information_retrieval', BASE / 'retrieval_adapter.py')
    inventory = load(run / 'retrieval_corpus_inventory.json')
    if sha(run / 'retrieval_corpus_inventory.json') != protocol['retrieval_inventory_sha256']:
        raise ValueError('Frozen corpus inventory changed')
    root = args.root.resolve()
    connections = {s['WG']: corpus_connection(s, root) for s in inventory['shards']} if args.probe_source else {}
    probes = {}; records = []
    try:
        for task in tasks:
            p = byid[task['id']]
            if p['question_en'] != task['question_en'] or p['repair_sha256'] != task['repair_sha256']:
                raise ValueError('Original question or repaired contract identity differs')
            private = forbidden_paths(p)
            # cardinality notes are deliberately allowed in retained public task,
            # but reconstructed serialized messages mask them before model use.
            if private:
                raise ValueError('Private evidence in public task: ' + repr(private))
            anchors = documentary_anchors(gold[task['id']], args.anchor_limit)
            source_probes = []
            for anchor in anchors:
                key = (p['wg'], anchor)
                if args.probe_source:
                    if key not in probes:
                        probes[key] = probe(connections[p['wg']], anchor)
                    source_probes.append(probes[key])
            whole_population = task['cardinality_policy'].get('mode') in {'all', 'top_k'} or bool(re.search(r'\b(count|counts|how many|most|distribution|total)\b', task['question_en'], re.I))
            row = {'id': task['id'], 'wg': p['wg'], 'repair_sha256': p['repair_sha256'],
                   'gold_reference_records_offline_only': len(gold[task['id']]['records']),
                   'whole_population_or_ranking_requirement': whole_population,
                   'documentary_anchor_policy': 'First <= ' + str(args.anchor_limit) + ' unique unmistakable documentary IDs in retained gold record order; no numeric answer/content/company anchors; probes occur offline after freezing, never passed to model.',
                   'anchors_selected_n': len(anchors), 'corpus_literal_probes': source_probes,
                   'semantic_source_support_established': False, 'arms': {}}
            for arm in ARMS:
                arm_record = {'serialized_request_checks': [audit_request(run, p, arm, stage, structured, retrieval) for stage in STAGES[arm]]}
                if arm in {'C', 'D'}:
                    arm_record['information_access'] = context_information(run, arm, task, anchors)
                else:
                    outcome = load(run / 'arm_outputs' / ARMS[arm] / (task['id'] + '.json'))
                    execution = load(run / 'executed' / ARMS[arm] / (task['id'] + '.json'))
                    arm_record['generation_status'] = outcome.get('status') if outcome and not outcome.get('_audit_unreadable_pending') else 'not_finished_yet'
                    arm_record['execution_status'] = execution.get('status') if execution and not execution.get('_audit_unreadable_pending') else 'not_executed_yet'
                row['arms'][arm] = arm_record
            records.append(row)
    finally:
        for con in connections.values():
            con.close()
    summaries = {}
    for arm in ARMS:
        leak = Counter(c['status'] for r in records for c in r['arms'][arm]['serialized_request_checks'])
        access = [r['arms'][arm].get('information_access') for r in records]
        access = [a for a in access if a is not None]
        summaries[arm] = {'task_denominator': len(ids), 'planned_request_stage_denominator': len(ids) * len(STAGES[arm]),
                          'serialized_request_statuses': dict(leak)}
        if access:
            summaries[arm].update({'contexts_ready': sum(a['final_context_ready'] for a in access),
                                  'answer_request_present': sum(a['actually_sent_answer_request_present'] for a in access),
                                  'finished_outcome_statuses': dict(Counter(a['retained_outcome_status'] for a in access)),
                                  'any_retrieval_interrupted': sum(any(q['status'] == 'search_interrupted' for q in a['retrieval_rounds']) for a in access),
                                  'ready_but_empty_contexts': sum(a['final_context_ready'] and not a['selected_context_documents'] for a in access),
                                  'semantic_support_certified_tasks': 0})
    report = {'audit_kind': 'Offline source-access, exact-request leakage, and representation encoding diagnostic',
              'snapshot_utc': datetime.now(timezone.utc).isoformat(), 'tool_sha256': sha(__file__),
              'observation_started_utc': observed_start,
              'observation_atomic': False,
              'generation_complete_observed':(run/'generation_complete.json').exists(),
              'observation_note': 'While generation is active, artifacts are observed sequentially and totals can refer to different instants. Re-run after all experiment artifacts are complete for a stable final audit.',
              'protocol_sha256': sha(run / 'protocol.json'), 'protocol_claimed_frozen_n': protocol['admitted_n'],
              'original_benchmark_n': protocol['original_total'], 'full_admitted_denominator': len(ids),
              'all_original560_complete': False, 'runtime_code_pins_match': code_checks,
              'task_sha256': protocol['tasks_sha256'], 'offline_gold_sha256': protocol['gold_sha256'],
              'source_schema_pin_matches': sha(args.source_schema) == protocol['source_schema_sha256'],
              'shared_structured_information': schema_information(run, protocol, args.relational, args.source_schema),
              'SQL_null_duplicate_diagnostic': SQL_null_duplicates(args.relational) if args.SQL_diagnostic else 'not_requested',
              'corpus_inventory_sha256': protocol['retrieval_inventory_sha256'],
              'corpus_cutoff_content_equality_to_frozen_graph': 'unverified',
              'arms': summaries, 'source_literal_probe_n': len(probes),
              'transport': transport_information(run), 'model_calls_by_this_tool': 0,
              'limits': ['Lexical candidate presence is not answer or relation support.',
                         'Positive documentary ID witnesses establish only literal presence in a retained chunk.',
                         'A bounded negative probe does not establish corpus absence.',
                         'Finite retrieved context cannot certify entire populations, distributions or count answers.',
                         'Model completeness is a self-report. This diagnostic creates no expert/human validation.',
                         'Missing request stages remain in the planned-stage denominator; a closed generation may legitimately omit D_answer after a failed/invalid followup, without receiving a leakage PASS.'],
              'elapsed_seconds': round(time.monotonic() - started, 3), 'items': records}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.output.with_suffix('.tmp')
    tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    os.replace(tmp, args.output)
    summary = {key: value for key, value in report.items() if key not in {'items', 'SQL_null_duplicate_diagnostic'}}
    summary['full_itemized_artifact'] = {'path': args.output.name, 'sha256': sha(args.output), 'item_n': len(records)}
    if isinstance(report['SQL_null_duplicate_diagnostic'], dict):
        summary['SQL_null_duplicate_diagnostic'] = {wg: {key: value for key, value in group.items()
            if key not in {'actual_unique_indexes', 'null_policy', 'duplicate_policy'}}
            for wg, group in report['SQL_null_duplicate_diagnostic'].items()}
    summary['tasks_with_documentary_literal_source_witness'] = sum(any(p['status'] == 'literal_presence_observed'
        for p in row['corpus_literal_probes']) for row in records)
    summary['literal_presence_is_semantic_support'] = False
    summary_path = args.output.with_name(args.output.stem + '.summary.json')
    summary_tmp = summary_path.with_suffix('.tmp'); summary_tmp.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    os.replace(summary_tmp, summary_path)
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', type=Path, required=True); ap.add_argument('--bundle', type=Path, required=True)
    ap.add_argument('--root', type=Path, required=True); ap.add_argument('--relational', type=Path, required=True)
    ap.add_argument('--source-schema', type=Path, required=True); ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--probe-source', action='store_true'); ap.add_argument('--SQL-diagnostic', action='store_true')
    ap.add_argument('--anchor-limit', type=int, default=3)
    args = ap.parse_args()
    if not 1 <= args.anchor_limit <= 5:
        raise ValueError('Anchor limit must be 1..5')
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 ** 3, 2 * 1024 ** 3))
    if hasattr(os, 'sched_getaffinity'):
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    report = audit(args)
    print(json.dumps({k: report[k] for k in ['full_admitted_denominator', 'arms', 'source_literal_probe_n', 'elapsed_seconds']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
