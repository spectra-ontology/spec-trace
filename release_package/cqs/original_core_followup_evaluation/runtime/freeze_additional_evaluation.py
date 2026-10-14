#!/usr/bin/env python3
"""Register a disjoint, actually admitted additional cohort before model calls."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
EMP = BASE.parent
sys.path.insert(0, str(EMP))
import run_evaluation as runtime
import verify_additions


def main(bundle, parent, run):
    proof = verify_additions.verify(bundle, parent)
    if run.exists():
        raise ValueError('Refuse to overwrite an evaluation registration')
    tasks = runtime.read(bundle/'tasks.jsonl')
    previous = runtime.read(parent/'tasks.jsonl')
    if {t['id'] for t in tasks} & {t['id'] for t in previous}:
        raise ValueError('Overlap with preserved 371-item cohort')
    run.mkdir(parents=True)
    runtime.freeze(bundle, run)
    protocol = json.loads((run/'protocol.json').read_text())
    protocol['budget_guard_usd'] = 6.0
    protocol['generation_workers'] = 2
    protocol['execution_workers'] = 2
    protocol['extension_registration'] = {
        'registered_utc': datetime.now(timezone.utc).isoformat(),
        'registration_program_sha256': runtime.sha(__file__),
        'parent_manifest_sha256': runtime.sha(parent/'manifest.json'),
        'parent_admitted_n': len(previous),
        'prior_disjoint_additions_n': proof['global_admitted_union_n']-len(previous)-len(tasks),
        'additional_n': len(tasks),
        'global_admitted_n': proof['global_admitted_union_n'],
        'global_unresolved_n': proof['global_unresolved_n'],
        'legacy_unresolved_n_field_scope': 'Core IDs outside this additional phase; global unresolved count is above.',
        'selection': 'Every separately passed exact original-question repair in the additional bundle; no new performance was available at selection.',
        'selection_used_new_performance': False,
        'prior_results_modified': False,
        'new_calls_already_made': 0,
        'historical_empirical_cost_estimate_usd': len(tasks)*91.705970/371,
        'estimate_scope': 'Prior four-arm actual spend per item; not a guarantee or prepaid cost.',
        'repair_validation_before_calls': proof,
    }
    runtime.write(run/'protocol.json', protocol)
    print(json.dumps({'additional_n':len(tasks), 'global_admitted_n':proof['global_admitted_union_n'],
        'protocol_sha256':runtime.sha(run/'protocol.json'), 'new_model_calls':0,
        'budget_cap_usd':protocol['budget_guard_usd']}))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--parent',type=Path,required=True)
    parser.add_argument('--run-dir',type=Path,required=True)
    args=parser.parse_args()
    main(args.bundle.resolve(),args.parent.resolve(),args.run_dir.resolve())
