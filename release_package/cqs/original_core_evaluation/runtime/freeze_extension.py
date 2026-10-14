#!/usr/bin/env python3
"""Register the additional original-ID cohort before its first model request."""
from datetime import datetime, timezone
import json
from pathlib import Path

import run_evaluation as runtime

BASE = Path(__file__).resolve().parent
ORIGINAL = BASE.parent / 'original_repair'
bundle = ORIGINAL / 'extension_bundle'
run = BASE / 'runs/additional-originals'
run.mkdir(parents=True, exist_ok=True)
if (run / 'protocol.json').exists():
    raise ValueError('Extension is already registered; no uncontrolled restart')
tasks = runtime.read(bundle / 'tasks.jsonl')
main = json.loads((BASE / 'runs/original-core-main/protocol.json').read_text())
union = runtime.read(ORIGINAL / 'final_staging_expanded/release_package/cqs/original_core_repair/tasks.jsonl')
if len(tasks) != 21 or len(union) != 371 or set(main['cohort_ids']) & {t['id'] for t in tasks}:
    raise ValueError('Extension must be the exact 21 additional original IDs')
if set(main['cohort_ids']) | {t['id'] for t in tasks} != {t['id'] for t in union}:
    raise ValueError('Main and additional cohorts do not cover the admitted union')
runtime.freeze(bundle, run)
configuration = json.loads((run / 'protocol.json').read_text())
configuration['budget_guard_usd'] = 6.0
configuration['generation_workers'] = 2
configuration['extension_registration'] = {
    'registered_utc': datetime.now(timezone.utc).isoformat(),
    'registration_program_sha256': runtime.sha(__file__),
    'main_protocol_sha256': runtime.sha(BASE / 'runs/original-core-main/protocol.json'),
    'additional_original_ids': [t['id'] for t in tasks],
    'global_admitted_n': 371,
    'global_unresolved_n': 189,
    'extension_nonselected_core_ids': 539,
    'legacy_unresolved_n_field_scope': 'Core IDs outside this 21-ID phase, not global unrepaired IDs.',
    'selection': 'All additionally admitted original-English-preserving repairs; selected by fixed semantic/native/scorer gates before seeing new performance.',
    'performance_used_to_select_extension': False,
    'main_scientific_inputs_modified': False,
    'new_calls_already_made': 0,
    'worker_count_reason': 'Limit simultaneous provider reservations while current account credits decrease; scientific messages/settings are unchanged.',
}
runtime.write(run / 'protocol.json', configuration)
print(json.dumps({'extension_n': 21, 'global_admitted_n': 371,
                  'new_cost_cap_usd': 6, 'generation_workers': 2,
                  'protocol_sha256': runtime.sha(run / 'protocol.json'),
                  'model_calls': 0}))
