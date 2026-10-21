#!/usr/bin/env python3
"""Spec: immutable authorized_incremental48 original Core questions; four measured methods.
Ontology: frozen SPECTRA graphs and byte-identical full relational projections.
Cycle: KDD2027 Datasets/Benchmarks Cycle1, authorized overnight extension.
배경: register exact 1 source-reviewed repair before any new predictions.
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

SCOPE_SHA = 'ca25947eeb9206e6826915a45a350f8318a5d6b096c8d91a3fba2c9d6e9a7b61'
RESERVE_BYTES = 26 * 1024**3

"""Inserted only into the registered AUTH48 controller before its first freeze."""
PROSPECTIVE_RUNTIME_PINS = {'score_predictions_joint_sample.py': '485b7054923f6a1bf87b1be29503168ef17ce402dbcc521e19a0e1ea72ece4c6', 'analyze_predictions_joint_sample.py': '3cbc240c49061de48ed13b11e68f0a971b73b221acbe4aaf7b0ea367624790b2', 'item_scorer_dispatch.py': '6cb3a3e7d4a16f944ca21d3d44d2a75b357f15f2d5d0372d8e1b768ae89172d6', 'one_record_sample_scorer.py': 'a9a40495742a650bcdd33628ec7ea10c94f8247c94982d3f372c771374f08b9f', 'preparation_receipt.json': 'c03d465917b295b6a9729fec63b67606843f749c64376720ed128be986f0a0ff', 'AUTH48_explicit_joint_analysis_runner.py': '88932194bea97aec2d6fb59990d659cea2a264c6452b1bb5ee9abb3661367ba1'}
PROSPECTIVE_BUNDLE_PINS = {'scorer.py': 'c6db2d2423e12e29f97746afdf9f22f143c948db89a4fe4dce14847e932ccdbd', 'typed_values.py': 'd7eee66cce2dabe3ef48c173e84fac47192266bdd3e8ce78214f8361df5161ba', 'source_pins.json': 'a86fad1201ca0225a798d2f48a278fe66c58d326907d959772a6ea05f3266f92', 'original_scorer.py': '1af0744df717abafe8115d560ac2db695ebea8a4b7d2ee104736dabf233badeb', 'contract_checks.py': '139ff636a4ca512d104521a3e36b0efbbdeeb885fc329331b3531416b2b8a44f', 'review_schema.py': '42d7019ed86d6ad92f7aef785419ca3cecbe207be4515760ecaf758e7cb3ae55', 'score_predictions.py': 'af6c07778ca6bc6d5fc431eed5b56142cb6871d089e0ac5263a4d3528a07a69a', 'score_predictions_joint_sample.py': '485b7054923f6a1bf87b1be29503168ef17ce402dbcc521e19a0e1ea72ece4c6', 'item_scorer_dispatch.py': '6cb3a3e7d4a16f944ca21d3d44d2a75b357f15f2d5d0372d8e1b768ae89172d6', 'one_record_sample_scorer.py': 'a9a40495742a650bcdd33628ec7ea10c94f8247c94982d3f372c771374f08b9f'}

def prospective_item_scoring_pins(bundle):
    for name, expected in PROSPECTIVE_RUNTIME_PINS.items():
        if runtime.sha(BASE / name) != expected:
            raise ValueError('Prospective AUTH48 scoring runtime changed: ' + name)
    for name, expected in PROSPECTIVE_BUNDLE_PINS.items():
        if runtime.sha(bundle / name) != expected:
            raise ValueError('Prospective AUTH48 scoring bundle changed: ' + name)
    tasks = runtime.read(bundle / 'tasks.jsonl')
    if len(tasks) != 1 or tasks[0]['id'] != 'RAN1_P4_CQ2-3' or tasks[0]['repair_sha256'] != '032c4939f0b9e2640d29f874fbf53b725533a261545e12400cce6e9f9abeb541':
        raise ValueError('Joint sample scoring is authorized only for the exact AUTH48 item')
    if tasks[0]['collection']['kind'] != 'one_record_with_unordered_sample':
        raise ValueError('Prospective joint collection changed')
    return {'cohort':'AUTH48','id':'RAN1_P4_CQ2-3',
        'repair_sha256':tasks[0]['repair_sha256'],
        'collection_kind':'one_record_with_unordered_sample',
        'metric_unit':'one complete target/count/sample record',
        'entrypoint':'score_predictions_joint_sample.py',
        'sample_pool_location':'original gold sidecar only; absent from public tasks',
        'runtime_file_pins':PROSPECTIVE_RUNTIME_PINS,'bundle_file_pins':PROSPECTIVE_BUNDLE_PINS,
        'historical_scores_changed':False,'shared_scorer_files_byte_exact':True,
        'original_question_parser_model_provider_and_caps_unchanged':True}



def available_memory():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1])*1024
    raise RuntimeError('Cannot verify host memory reserve')


def immutable_scope(bundle):
    if runtime.sha(AUTH/'scope.json') != SCOPE_SHA:
        raise ValueError('The authorized_incremental48 scope changed')
    scope = json.loads((AUTH/'scope.json').read_text())
    tasks = runtime.read(bundle/'tasks.jsonl')
    expected = {r['id']:r['repair_sha256'] for r in scope['cases']}
    actual = {r['id']:r['repair_sha256'] for r in tasks}
    if len(tasks) != 1 or len(actual) != 1 or actual != expected:
        raise ValueError('Bundle differs from immutable authorized_incremental48, including repair identities')
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
    item_scoring = prospective_item_scoring_pins(bundle)
    if workers != 1 or not 0 < budget <= 1.0:
        raise ValueError('Invalid resource/budget bound')
    memory = available_memory()
    if memory < RESERVE_BYTES + 1024**3:
        raise RuntimeError('Cannot retain 26GiB host reserve plus retrieval-worker allowance')
    import subprocess
    child = subprocess.run([sys.executable, '-B', '-I', '-S',
        str(bundle/'verify_additions.py'), '--bundle', str(bundle)],
        capture_output=True, text=True, timeout=240)
    if child.returncode:
        raise RuntimeError('Isolated full offline validator failed: '+child.stderr[-3000:])
    proof = json.loads(child.stdout)
    if proof.get('status') != 'PASS' or proof.get('local_validated_n') != 1 or proof.get('candidate_n') != 1 or proof.get('new_public_admissions') != 0:
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
    protocol['code_pins']['authorized_incremental48_evaluation.py'] = runtime.sha(__file__)
    protocol['prospective_item_scoring'] = item_scoring
    protocol['code_pins'].update(item_scoring['runtime_file_pins'])
    protocol['budget_guard_usd'] = budget
    protocol['generation_workers'] = workers
    protocol['account_and_key_credit_floor_usd'] = 5.0
    protocol['credit_floor_guard_sha256'] = runtime.sha(BASE/'credit_floor_guard.py')
    protocol['execution_workers'] = 2
    protocol['SQL_interface'] = 'Byte-exact complete value-free physical SQLite DDL; preserved SQL interface v2.'
    protocol['authorized_incremental48_extension'] = {
        'registered_utc':datetime.now(timezone.utc).isoformat(),
        'scope_sha256':SCOPE_SHA,'scope_path':str(AUTH/'scope.json'),
        'admission_inputs_sha256':runtime.sha(AUTH/'admission_inputs.json'),
        'source_copy_receipt_sha256':runtime.sha(BASE/'runtime_source_copy_receipt.json'),
        'bundle_validator_sha256':runtime.sha(bundle/'verify_additions.py'),
        'scope_n':1,'method_items_n':4,'planned_calls_without_transport_retry':5,
        'baseline_public_original_n':518,'this_phase_original_union_n':519,'this_phase_pending_n':41,
        'live_admission_registry_used':False,'common_supplemental_source_supplied':False,
        'selection_used_phase_predictions':False,'new_model_calls_before_registration':0,
        'quality_regeneration_authorized':False,'human_expert_validation_n':0,
        'repair_validation_before_calls':proof,
        'raw_runtime_freeze_sha256':runtime.sha(run/'runtime_freeze_base.json'),
        'historical_four_method_spend_estimate_usd':1*91.705970/371,
        'historical_estimate_is_not_a_guarantee':True,
        'max_output_cost_usd_excludes_input_and_transport_retry':protocol['max_output_cost_without_transport_retry_usd'],
        'host_MemAvailable_bytes_before_freeze':memory,'host_reserve_bytes':RESERVE_BYTES,
        'worker_policy':'Exactly1 serial generation worker; unchanged scientific payload, model, max_tokens, transport retry and methods. Each retrieval SQLite cache32MiB, one SQLite thread. Native execution remains root-serialized.',
        'protocol_model_provider_unchanged':True}
    runtime.write(run/'schema_preflight.json',{'status':'PASS','groups':audits,'business_values_read':False})
    protocol['schema_preflight_sha256'] = runtime.sha(run/'schema_preflight.json')
    runtime.write(run/'protocol.json',protocol)
    verify(bundle,run)
    print(json.dumps({'status':'FROZEN_AUTHORIZED_INCREMENTAL48','question_n':1,'method_items_n':4,
                      'planned_calls_without_transport_retry':5,'protocol_sha256':runtime.sha(run/'protocol.json'),
                      'budget_guard_usd':budget,'generation_workers':workers,'new_model_calls':0}),flush=True)


def verify(bundle, run):
    _,tasks = immutable_scope(bundle)
    if runtime.sha(BASE/'credit_floor_guard.py') != 'c4193f523bec9d6b0282311850957530bd8b7ec237d8446a0e0c94cd18f0451e':
        raise ValueError('Pinned USD5 account/key credit guard changed')
    protocol = runtime.verify_pins(bundle,run)
    if protocol['prospective_item_scoring'] != prospective_item_scoring_pins(bundle):
        raise ValueError('Prospective current-item scoring pins changed')
    if protocol['generation_workers'] != 1 or protocol['account_and_key_credit_floor_usd'] != 5.0 or protocol['credit_floor_guard_sha256'] != runtime.sha(BASE/'credit_floor_guard.py'):
        raise ValueError('Serial generation or credit-floor registration differs')
    scope = protocol['authorized_incremental48_extension']
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
            or protocol['authorized_incremental48_extension']['quality_regeneration_authorized'] is not False):
        raise ValueError('Pinned model/provider or no-quality-retry rule changed')
    return protocol


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['freeze','verify','generate','execute','analyze'])
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--budget-usd',type=float)
    parser.add_argument('--workers',type=int,choices=[1],default=1)
    args = parser.parse_args()
    bundle,run = args.bundle.resolve(),args.run_dir.resolve()
    if args.action == 'freeze':
        if args.budget_usd is None:
            parser.error('freeze requires explicit --budget-usd within verified account credit')
        freeze(bundle,run,args.budget_usd,args.workers)
    else:
        verify(bundle,run)
        if args.action == 'verify':
            print(json.dumps({'status':'PASS','scope_n':1,'model_calls_started_by_verify':0}))
        elif args.action == 'generate':
            if available_memory() < RESERVE_BYTES + 1024**3:
                raise RuntimeError('26GiB host reserve unavailable before generation')
            runtime.generate(bundle,run)
        elif args.action == 'execute':
            runtime.execute(bundle,run)
        else:
            import analyze_predictions_joint_sample as analyze_predictions
            output=analyze_predictions.run(bundle,run)
            print(json.dumps({'question_n':output['admitted_n'],'methods':list(output['tables'])}))
