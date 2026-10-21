"""Replay the sealed original LP-WUS actual-new-section classification."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

if sys.flags.optimize:
    raise SystemExit('Run without optimization')
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
INVENTORY_SHA256 = '198fb45f6943cb478c8b0e88fca7536cb24e68f307c2df020ceb58ba4f2b7704'
SEAL_SHA256 = '8e0f2162b1a63772f493e268a18c4c24cceeed3f50563db694a4e831fbfbcbdc'
ID = 'RAN1_P5_CQ3-2'


def pin(path):
    b = path.read_bytes()
    return {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}


def main():
    assert pin(HERE / 'immutable_inventory.json')['sha256'] == INVENTORY_SHA256
    inv = json.loads((HERE / 'immutable_inventory.json').read_bytes())
    for name, value in inv['files'].items():
        p = HERE / name
        assert not p.is_symlink() and p.is_file() and pin(p) == value, name
    observed = {p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file()}
    assert observed == set(inv['files']) | {'immutable_inventory.json', 'manifest.json', 'reproduce.py'}
    seal = json.loads((HERE / 'ROOT_final_seal.json').read_bytes())
    assert pin(HERE / 'ROOT_final_seal.json')['sha256'] == SEAL_SHA256
    assert seal['id'] == ID and seal['classification'] == 'unsupported_frozen_data'
    assert seal['criteria_sha256'] == 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
    assert seal['two_nonblind_AI_semantic_judgments'] is True and seal['human_expert_n'] == 0
    assert seal['whole_original_question_verified_pass'] is False
    case = HERE / 'cases' / ID
    for name, field in [('contract/primary_exact_seven_unit_source_role_review.json', 'primary_review'),
                        ('contract/ROOT_secondary_review.json', 'independent_ROOT_review'),
                        ('provenance/actual_ROOT_independent_original_and_SQL_replay.json', 'original_source_and_SQL_replay'),
                        ('contract/bounded_source_role_contract.json', 'source_role_contract'),
                        ('contract/counterauthority_and_alternate_recovery_decisions.json', 'counterauthority_and_alternate_recovery'),
                        ('manifest.json', 'portable_manifest')]:
        assert pin(case / name) == {k: seal[field][k] for k in ['bytes', 'sha256']}
    assert seal['primary_review']['sha256'] != seal['independent_ROOT_review']['sha256']
    assert pin(HERE / 'actual_ROOT_final_portable_independent_relocated_replay.json') == {k:seal['ROOT_final_relocated_portable_replay'][k] for k in ['bytes','sha256']}
    assert pin(HERE / 'actual_portable_relocation_and_scientific_adverse_controls.json') == {k:seal['agent_actual_final_adverse_controls'][k] for k in ['bytes','sha256']}
    controls = json.loads((HERE / 'actual_portable_relocation_and_scientific_adverse_controls.json').read_bytes())
    assert controls['status'] == 'PASS' and controls['adverse_control_n'] == 8
    assert controls['packet_manifest'] == pin(case / 'manifest.json')
    assert all(x['scientific_rejected'] and x['mutation_completed'] for x in controls['adverse_controls'])
    assert controls['scientific_controls_bypass_inventory_checks'] is True
    assert controls['positive_relocation']['exit_code'] == 0
    proc = subprocess.run([sys.executable, '-B', '-I', '-S', str(case / 'reproduce.py')],
                          text=True, capture_output=True, stdin=subprocess.DEVNULL)
    assert proc.returncode == 0, proc.stderr
    child = json.loads(proc.stdout)
    assert child['status'] == 'PASS' and child['id'] == ID and child['AI_reviews'] == 2 and child['nonblind_AI'] is True and child['phase'] in ['independent_reviewed','final_sealed']
    assert child['classification'] == seal['classification'] and child['human_expert_reviews'] == 0
    assert child['new_original_admissions'] == child['new_model_evaluations'] == child['API_calls'] == child['native_calls'] == child['P_mutations'] == 0
    print(json.dumps({'status': 'PASS', 'cases': [{'id': ID, 'classification': seal['classification'],
          'subtype': seal['subtype'], 'child_result': child}], 'new_admissions': 0,
          'expert_validation_n': 0, 'model_API_calls': 0, 'new_native_calls': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
