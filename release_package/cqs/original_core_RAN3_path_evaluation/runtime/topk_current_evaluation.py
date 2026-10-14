#!/usr/bin/env python3
"""Fresh four-arm predictions for all ten retained top-k replacements.

This phase replaces contracts for existing Core IDs; it adds no new IDs and
does not change any earlier contract, prediction, score, or runtime.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sqlite3
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import run_evaluation as runtime


def replacement_proof(bundle, parent):
    # The package's offline validator also checks exact original questions,
    # fixed criteria, both semantic reviews, uncapped native pools and controls.
    sys.path.insert(0, str(bundle))
    import verify_replacements
    proof = verify_replacements.verify(bundle, parent)
    if proof['status'] != 'PASS' or proof['replacement_n'] != 10:
        raise ValueError('Expected the complete, verified ten-contract phase')
    return proof


def ddl_audit(wg, card):
    db = BASE/'relational'/(wg+'.sqlite')
    manifest = json.loads((BASE/'relational'/(wg+'.manifest.json')).read_text())
    expected = manifest.get('sqlite_sha256', manifest.get('db_sha256', manifest.get('output_sha256')))
    if runtime.sha(db) != expected:
        raise ValueError('Frozen SQLite source differs: '+wg)
    connection = sqlite3.connect(db.resolve().as_uri()+'?mode=ro&immutable=1', uri=True)
    try:
        catalog = connection.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE '\_%' ESCAPE '\\' ORDER BY name").fetchall()
        ddl = '\n'.join(sql+';' for _, sql in catalog)
        if card['ddl'] != ddl:
            raise ValueError('SQL schema does not equal the complete public DDL: '+wg)
        return {'wg':wg, 'status':'PASS', 'table_n':len(catalog),
                'complete_public_ddl_byte_exact':True, 'value_rows_read':False,
                'sqlite_sha256':expected,
                'card_sha256':runtime.sha(BASE/'sql_interface_v2/schemas'/(wg+'_sql.json'))}
    finally:
        connection.close()


def freeze(bundle, parent, run):
    if run.exists():
        raise ValueError('Refuse to overwrite a phase registration')
    proof = replacement_proof(bundle, parent)
    tasks = runtime.read(bundle/'tasks.jsonl')
    previous = runtime.read(parent/'tasks.jsonl')
    if len(previous) != 371 or not {t['id'] for t in tasks} <= {t['id'] for t in previous}:
        raise ValueError('Replacement scope is not the preserved public 371 cohort')
    audits = []
    for wg in ['RAN1','RAN2','RAN3','RAN4','RAN5']:
        card = json.loads((BASE/'sql_interface_v2/schemas'/(wg+'_sql.json')).read_text())
        audits.append(ddl_audit(wg, card))
    run.mkdir(parents=True)
    runtime.freeze(bundle, run)
    raw_protocol = run/'protocol.json'
    shutil.copy2(raw_protocol, run/'runtime_freeze_base.json')
    protocol = json.loads(raw_protocol.read_text())
    for wg in ['RAN1','RAN2','RAN3','RAN4','RAN5']:
        shutil.copy2(BASE/'sql_interface_v2/schemas'/(wg+'_sql.json'), run/'schemas'/(wg+'_sql.json'))
    protocol['schema_pins'] = {str(p.relative_to(run)):runtime.sha(p) for p in sorted((run/'schemas').glob('*.json'))}
    protocol['code_pins']['topk_current_evaluation.py'] = runtime.sha(__file__)
    protocol['SQL_interface'] = 'Actual complete value-free physical SQLite DDL; identical cards to SQL interface v2.'
    protocol['budget_guard_usd'] = 4.0
    protocol['generation_workers'] = 3
    protocol['execution_workers'] = 2
    protocol['replacement_scope'] = {
        'registered_utc':datetime.now(timezone.utc).isoformat(),
        'parent_manifest_sha256':runtime.sha(parent/'manifest.json'),
        'parent_tasks_sha256':runtime.sha(parent/'tasks.jsonl'),
        'parent_admitted_n':371, 'replacement_n':10, 'new_original_core_id_n':0,
        'selection':'All ten source-audited uncapped top-k contract replacements, fixed before this phase predictions.',
        'selection_used_this_phase_performance':False,
        'old_contracts_predictions_scores_unchanged':True,
        'new_model_calls_before_registration':0,
        'common_supplemental_source_supplied':False,
        'legacy_admitted_n_field_scope':'This ten-item phase, not the global original Core admission count.',
        'legacy_unresolved_n_field_scope':'Core IDs outside this replacement phase; no change to the preserved disposition ledger.',
        'repair_validation_before_calls':proof,
        'raw_runtime_freeze_sha256':runtime.sha(run/'runtime_freeze_base.json'),
        'expected_arms':['A','B','C','D'], 'planned_method_items':40,
        'planned_calls_without_transport_retry':50,
        'cost_estimate_usd':10*91.705970/371,
        'estimate_scope':'Historical four-arm actual spend per item; not a guarantee.'}
    runtime.write(run/'schema_preflight.json', {'status':'PASS','groups':audits,'business_values_read':False})
    protocol['schema_preflight_sha256'] = runtime.sha(run/'schema_preflight.json')
    runtime.write(raw_protocol, protocol)
    print(json.dumps({'status':'FROZEN_TOP10','n':10,'method_items':40,
                      'protocol_sha256':runtime.sha(raw_protocol),'budget_guard_usd':4.0,
                      'generation_workers':3,'new_model_calls':0}), flush=True)


def verify(bundle, parent, run):
    protocol = runtime.verify_pins(bundle, run)
    scope = protocol['replacement_scope']
    checks = [(parent/'manifest.json', scope['parent_manifest_sha256']),
              (parent/'tasks.jsonl', scope['parent_tasks_sha256']),
              (bundle/'tasks.jsonl', protocol['tasks_sha256']),
              (bundle/'reference_gold.jsonl', protocol['gold_sha256']),
              (run/'runtime_freeze_base.json', scope['raw_runtime_freeze_sha256']),
              (run/'schema_preflight.json', protocol['schema_preflight_sha256'])]
    if any(runtime.sha(path) != expected for path, expected in checks):
        raise ValueError('Frozen phase inputs changed')
    if len(runtime.read(run/'public_tasks.jsonl')) != 10:
        raise ValueError('Complete replacement cohort differs')
    return protocol


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['freeze','generate','execute'])
    for name in ['bundle','parent','run-dir']:
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    bundle, parent, run = args.bundle.resolve(), args.parent.resolve(), args.run_dir.resolve()
    if args.action == 'freeze':
        freeze(bundle, parent, run)
    else:
        verify(bundle, parent, run)
        getattr(runtime, args.action)(bundle, run)
