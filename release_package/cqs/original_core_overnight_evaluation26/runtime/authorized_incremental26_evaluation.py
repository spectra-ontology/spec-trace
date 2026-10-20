#!/usr/bin/env python3
"""Spec: immutable authorized_incremental26 original Core questions; four measured methods.
Ontology: frozen SPECTRA graphs and byte-identical full relational projections.
Cycle: KDD2027 Datasets/Benchmarks Cycle1, authorized overnight extension.
배경: register exact 2 source-reviewed repairs before any new predictions.
사용: freeze/verify/generate/execute/analyze --bundle ... --run-dir ... .
LLM 호출: only generate; pinned OpenRouter Opus4.8/Anthropic, no quality retry.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sqlite3
import sys

sys.dont_write_bytecode = True
if sys.flags.optimize:
    raise SystemExit('Run without -O/-OO; registration checks must remain enabled.')
BASE = Path(__file__).resolve().parent
AUTH = BASE.parent.parent
sys.path.insert(0, str(BASE))
import run_evaluation as runtime
import structured_adapter as structured
import retrieval_adapter as retrieval

SCOPE_SHA = '501897c934e076b2a0db0793e1d1a2b9b4ac34a85917e7c6528f62049f34243e'
RESERVE_BYTES = 26 * 1024**3


def available_memory():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1])*1024
    raise RuntimeError('Cannot verify host memory reserve')


def immutable_scope(bundle):
    if runtime.sha(AUTH/'scope.json') != SCOPE_SHA:
        raise ValueError('The authorized_incremental26 scope changed')
    scope = json.loads((AUTH/'scope.json').read_text())
    tasks = runtime.read(bundle/'tasks.jsonl')
    expected = {r['id']:r['repair_sha256'] for r in scope['cases']}
    actual = {r['id']:r['repair_sha256'] for r in tasks}
    if len(tasks) != 2 or len(actual) != 2 or actual != expected:
        raise ValueError('Bundle differs from immutable authorized_incremental26, including repair identities')
    for record in scope['cases']:
        pin = record['definition']
        if runtime.sha(pin['path']) != pin['sha256']:
            raise ValueError('Authorized original definition changed: '+record['id'])
    return scope, tasks


def full_ddl_audit(wg, card):
    db = BASE/'relational'/(wg+'.sqlite')
    manifest = json.loads((BASE/'relational'/(wg+'.manifest.json')).read_text())
    expected = manifest.get('sqlite_sha256', manifest.get('db_sha256', manifest.get('output_sha256')))
    if runtime.sha(db) != expected:
        raise ValueError('Frozen SQLite changed: '+wg)
    connection = sqlite3.connect(db.resolve().as_uri()+'?mode=ro&immutable=1', uri=True)
    try:
        catalog = connection.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE '\\_%' ESCAPE '\\' ORDER BY name").fetchall()
        ddl = '\n'.join(sql+';' for _,sql in catalog)
        if card['ddl'] != ddl:
            raise ValueError('Actual complete DDL differs: '+wg)
        return {'wg':wg,'status':'PASS','table_n':len(catalog),'sqlite_sha256':expected,
                'value_rows_read':False,'complete_public_ddl_byte_exact':True,
                'card_sha256':runtime.sha(BASE/'sql_interface_v2/schemas'/(wg+'_sql.json'))}
    finally:
        connection.close()


def freeze(bundle, run, budget, workers):
    if run.exists():
        raise ValueError('Refuse to overwrite registration; preserve failures and use a separately authorized path')
    scope, tasks = immutable_scope(bundle)
    if not 1 <= workers <= 8 or budget <= 0:
        raise ValueError('Invalid resource/budget bound')
    memory = available_memory()
    if memory < RESERVE_BYTES + 1024**3:
        raise RuntimeError('Cannot retain 26GiB host reserve plus retrieval-worker allowance')
    sys.path.insert(0,str(bundle))
    spec = importlib.util.spec_from_file_location('authorized_incremental26_bundle_validator', bundle/'verify_additions.py')
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    proof = validator.verify(bundle)
    if proof.get('status') != 'PASS' or proof.get('local_validated_n') != 2 or proof.get('candidate_n') != 2 or proof.get('new_public_admissions') != 0:
        raise ValueError('Need full offline 2-review/native/SQL/scorer validation before model calls')
    groups = sorted({t['id'].split('_')[0] for t in tasks})
    audits = [full_ddl_audit(wg,json.loads((BASE/'sql_interface_v2/schemas'/(wg+'_sql.json')).read_text())) for wg in groups]
    run.mkdir(parents=True)
    # Prior runtime prepares all five source inventories, never old predictions.
    runtime.freeze(bundle,run)
    shutil.copy2(run/'protocol.json',run/'runtime_freeze_base.json')
    protocol = json.loads((run/'protocol.json').read_text())
    for wg in ['RAN1','RAN2','RAN3','RAN4','RAN5']:
        shutil.copy2(BASE/'sql_interface_v2/schemas'/(wg+'_sql.json'),run/'schemas'/(wg+'_sql.json'))
    protocol['schema_pins'] = {str(p.relative_to(run)):runtime.sha(p) for p in sorted((run/'schemas').glob('*.json'))}
    protocol['code_pins']['authorized_incremental26_evaluation.py'] = runtime.sha(__file__)
    protocol['budget_guard_usd'] = budget
    protocol['generation_workers'] = workers
    protocol['execution_workers'] = 2
    protocol['SQL_interface'] = 'Byte-exact complete value-free physical SQLite DDL; preserved SQL interface v2.'
    protocol['authorized_incremental26_extension'] = {
        'registered_utc':datetime.now(timezone.utc).isoformat(),
        'scope_sha256':SCOPE_SHA,'scope_path':str(AUTH/'scope.json'),
        'admission_inputs_sha256':runtime.sha(AUTH/'admission_inputs.json'),
        'source_copy_receipt_sha256':runtime.sha(BASE/'runtime_source_copy_receipt.json'),
        'bundle_validator_sha256':runtime.sha(bundle/'verify_additions.py'),
        'scope_n':2,'method_items_n':8,'planned_calls_without_transport_retry':10,
        'baseline_public_original_n':489,'this_phase_original_union_n':491,'this_phase_pending_n':69,
        'live_admission_registry_used':False,'common_supplemental_source_supplied':False,
        'selection_used_phase_predictions':False,'new_model_calls_before_registration':0,
        'quality_regeneration_authorized':False,'human_expert_validation_n':0,
        'repair_validation_before_calls':proof,
        'raw_runtime_freeze_sha256':runtime.sha(run/'runtime_freeze_base.json'),
        'historical_four_method_spend_estimate_usd':2*91.705970/371,
        'historical_estimate_is_not_a_guarantee':True,
        'max_output_cost_usd_excludes_input_and_transport_retry':protocol['max_output_cost_without_transport_retry_usd'],
        'host_MemAvailable_bytes_before_freeze':memory,'host_reserve_bytes':RESERVE_BYTES,
        'worker_policy':'At most8 interleaved method jobs, preserving the prior protocol; each retrieval SQLite cache32MiB, one SQLite thread. Native execution remains root-serialized.',
        'protocol_model_provider_unchanged':True}
    runtime.write(run/'schema_preflight.json',{'status':'PASS','groups':audits,'business_values_read':False})
    protocol['schema_preflight_sha256'] = runtime.sha(run/'schema_preflight.json')
    runtime.write(run/'protocol.json',protocol)
    verify(bundle,run)
    print(json.dumps({'status':'FROZEN_AUTHORIZED_INCREMENTAL26','question_n':2,'method_items_n':8,
                      'planned_calls_without_transport_retry':10,'protocol_sha256':runtime.sha(run/'protocol.json'),
                      'budget_guard_usd':budget,'generation_workers':workers,'new_model_calls':0}),flush=True)


def verify(bundle, run):
    _,tasks = immutable_scope(bundle)
    protocol = runtime.verify_pins(bundle,run)
    scope = protocol['authorized_incremental26_extension']
    checks = [(bundle/'tasks.jsonl',protocol['tasks_sha256']),
              (bundle/'reference_gold.jsonl',protocol['gold_sha256']),
              (bundle/'verify_additions.py',scope['bundle_validator_sha256']),
              (AUTH/'admission_inputs.json',scope['admission_inputs_sha256']),
              (BASE/'runtime_source_copy_receipt.json',scope['source_copy_receipt_sha256']),
              (run/'runtime_freeze_base.json',scope['raw_runtime_freeze_sha256']),
              (run/'schema_preflight.json',protocol['schema_preflight_sha256'])]
    if any(runtime.sha(path) != expected for path,expected in checks):
        raise ValueError('Registered evaluation input changed')
    visible = runtime.read(run/'public_tasks.jsonl')
    if {t['id']:t['repair_sha256'] for t in visible} != {t['id']:t['repair_sha256'] for t in tasks}:
        raise ValueError('Model-visible cohort differs')
    for task in visible:
        structured.reject_private(task)
    if (protocol['model'] != 'anthropic/claude-opus-4.8' or protocol['provider'] != 'Anthropic'
            or protocol['authorized_incremental26_extension']['quality_regeneration_authorized'] is not False):
        raise ValueError('Pinned model/provider or no-quality-retry rule changed')
    return protocol


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['freeze','verify','generate','execute','analyze'])
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--budget-usd',type=float)
    parser.add_argument('--workers',type=int,default=8)
    args = parser.parse_args()
    bundle,run = args.bundle.resolve(),args.run_dir.resolve()
    if args.action == 'freeze':
        if args.budget_usd is None:
            parser.error('freeze requires explicit --budget-usd within verified account credit')
        freeze(bundle,run,args.budget_usd,args.workers)
    else:
        verify(bundle,run)
        if args.action == 'verify':
            print(json.dumps({'status':'PASS','scope_n':2,'model_calls_started_by_verify':0}))
        elif args.action == 'generate':
            if available_memory() < RESERVE_BYTES + 1024**3:
                raise RuntimeError('26GiB host reserve unavailable before generation')
            runtime.generate(bundle,run)
        elif args.action == 'execute':
            runtime.execute(bundle,run)
        else:
            import analyze_predictions
            output=analyze_predictions.run(bundle,run)
            print(json.dumps({'question_n':output['admitted_n'],'methods':list(output['tables'])}))
