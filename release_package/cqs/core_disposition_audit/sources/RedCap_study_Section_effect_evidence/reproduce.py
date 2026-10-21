"""Replay the sealed original RedCap study-to-Section effect classification."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

if sys.flags.optimize:
    raise SystemExit('Run without optimization')
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
INVENTORY_SHA256 = '4089df4c5576741251264b568688985dc5055e5c887684e32f21a287a375a38f'
SEAL_SHA256 = 'b152bb925f6ab4fb506cb625b97d32628233267039b4fc67645af22498b91888'
ID = 'RAN1_P5_CQ3-1'


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
    for name, field in [('contract/primary_seven_unit_review.json', 'primary_review'),
                        ('contract/ROOT_secondary_review.json', 'independent_ROOT_review'),
                        ('provenance/actual_ROOT_direct_11_sources_and_frozen_9_roles_v1.json', 'original_source_and_SQL_replay'),
                        ('contract/bounded_source_role_contract.json', 'source_role_contract'),
                        ('contract/counterauthority_and_alternate_recovery_decisions.json', 'counterauthority_and_alternate_recovery')]:
        assert pin(case / name) == {k: seal[field][k] for k in ['bytes', 'sha256']}
    assert seal['primary_review']['sha256'] != seal['independent_ROOT_review']['sha256']
    assert pin(case / 'manifest.json') == {k:seal['portable_manifest'][k] for k in ['bytes','sha256']}
    replay_path = HERE / 'actual_ROOT_final_portable_independent_relocated_replay_v2.json'
    assert pin(replay_path) == {k:seal['ROOT_final_relocated_portable_replay'][k] for k in ['bytes','sha256']}
    replay = json.loads(replay_path.read_bytes())
    assert replay['status'] == 'PASS_ROOT_FINAL_RELOCATED_PORTABLE_SOURCE_ROLE_REPLAY'
    assert replay['executed_by'] == 'ROOT AI agent' and replay['exit_code'] == 0
    assert replay['manifest_sha256'] == pin(case / 'manifest.json')['sha256']
    assert replay['inventory_sha256'] == pin(case / 'immutable_inventory.json')['sha256']
    assert replay['verifier_sha256'] == pin(case / 'reproduce.py')['sha256']
    assert replay['new_API_native_calls'] == 0
    controls_path = HERE / 'actual_agent_final_portable_relocation_and_controls_v2.json'
    assert pin(controls_path)['sha256'] == replay['agent_eight_adverse_controls_receipt_sha256']
    controls = json.loads(controls_path.read_bytes())
    assert controls['status'] == 'PASS' and controls['control_count'] == 8
    assert controls['bundle_manifest'] == pin(case / 'manifest.json')
    assert controls['actual_relocated_execution']['exit_code'] == 0
    assert all(x['re_inventoried_before_execution'] is True and x['actual']['exit_code'] != 0 for x in controls['scientific_adverse_controls'])
    assert all(x['result'] == 'REJECTED_AS_REQUIRED' for x in controls['scientific_adverse_controls'])
    proc = subprocess.run([sys.executable, '-B', '-I', '-S', str(case / 'reproduce.py')],
                          text=True, capture_output=True, stdin=subprocess.DEVNULL)
    assert proc.returncode == 0, proc.stderr
    child = json.loads(proc.stdout)
    assert child['status'] == 'PASS' and child['id'] == ID and child['two_nonblind_AI_reviews'] is True
    assert child['classification'] == seal['classification'] and child['expert_validation_n'] == 0
    assert child['new_admissions'] == child['model_API_calls'] == child['native_calls'] == 0
    assert child == replay['result'] == json.loads(replay['stdout'])
    assert child['original_source_XML_style_pairs'] == 11 and len(child['original_SQL_role_checks']) == 9
    print(json.dumps({'status': 'PASS', 'cases': [{'id': ID, 'classification': seal['classification'],
          'subtype': seal['subtype'], 'child_result': child}], 'new_admissions': 0,
          'expert_validation_n': 0, 'model_API_calls': 0, 'new_native_calls': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
