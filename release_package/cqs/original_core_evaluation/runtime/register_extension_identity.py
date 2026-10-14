#!/usr/bin/env python3
"""Expose the declared anonymous-item output convention before any new call."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

import run_evaluation as runtime

BASE = Path(__file__).resolve().parent
run = BASE / 'runs/additional-originals'
if any((run / 'calls').glob('*')) or (run / 'generation_complete.json').exists():
    raise ValueError('Identity convention must be registered before any generation')
if (run / 'output_identity_registration.json').exists():
    raise ValueError('Output identity is already registered')
identifiers = {'RAN3_P2_CQ1-8', 'RAN3_P2_CQ4-2', 'RAN4_P1_CQ3-1', 'RAN4_P2_CQ1-8'}
tasks = runtime.read(run / 'public_tasks.jsonl')
if identifiers - {t['id'] for t in tasks}:
    raise ValueError('Expected additional agenda tasks unavailable')
prior = {'protocol_sha256': runtime.sha(run / 'protocol.json'),
         'public_tasks_sha256': runtime.sha(run / 'public_tasks.jsonl')}
shutil.copyfile(run / 'protocol.json', run / 'protocol_before_output_identity.json')
shutil.copyfile(run / 'public_tasks.jsonl', run / 'public_tasks_before_output_identity.jsonl')
for task in tasks:
    if task['id'] in identifiers:
        task['identity_format'] = {
            'field': 'agendaId',
            'rule': 'Use the agenda item business ID when available; otherwise use its deterministic loader identity. Keep different agenda entities distinct.',
            'loader_identity_codec': 'https://w3id.org/spectra/inst/_/{class}/{local_id}',
            'note': 'This is an output-identity convention, not an answer value or a filter excluding anonymous items.',
        }
(run / 'public_tasks.jsonl').write_text(''.join(json.dumps(t, ensure_ascii=False) + '\n' for t in tasks))
registration = {
    'registered_utc': datetime.now(timezone.utc).isoformat(),
    'program_sha256': runtime.sha(__file__),
    'prior': prior,
    'new_public_tasks_sha256': runtime.sha(run / 'public_tasks.jsonl'),
    'affected_ids': sorted(identifiers),
    'model_calls_before_registration': 0,
    'scope': 'The frozen repair definitions already require loader identity for missing business IDs; all four methods receive this same answer-free convention.',
    'reference_query_or_gold_exposed': False,
    'frozen_main350_modified': False,
}
runtime.write(run / 'output_identity_registration.json', registration)
protocol = json.loads((run / 'protocol.json').read_text())
protocol['public_tasks_sha256'] = registration['new_public_tasks_sha256']
protocol['output_identity_registration_sha256'] = runtime.sha(run / 'output_identity_registration.json')
runtime.write(run / 'protocol.json', protocol)
print(json.dumps({'new_protocol_sha256': runtime.sha(run / 'protocol.json'),
                  'updated_answer_free_identity_cards': len(identifiers), 'model_calls': 0}))
