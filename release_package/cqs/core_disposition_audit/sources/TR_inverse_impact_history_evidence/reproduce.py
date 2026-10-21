"""Replay the sealed original study-to-specification impact history classification."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

if sys.flags.optimize:
    raise SystemExit('Run without optimization')
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
INVENTORY_SHA256 = '9df55805f9f6b6830fb0122c729160ae3f9195bb05e3bd3a35acdf9469738ed0'
SEAL_SHA256 = '7d4a8e5250f9a20bb1fab9f1b3114cfa459fdea951a5fca841d59e3b7359da6d'
ID = 'RAN1_P5_CQ2-3'


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
                        ('provenance/actual_ROOT_independent_original_and_SQL_replay.json', 'original_source_and_SQL_replay')]:
        assert pin(case / name) == {k: seal[field][k] for k in ['bytes', 'sha256']}
    assert seal['primary_review']['sha256'] != seal['independent_ROOT_review']['sha256']
    controls = json.loads((HERE / 'actual_portable_relocation_and_scientific_adverse_controls.json').read_bytes())
    assert controls['status'] == 'PASS' and controls['control_count'] == 6
    assert controls['bundle_manifest_sha256'] == pin(case / 'manifest.json')['sha256']
    assert all(x['result'] == 'REJECTED_AS_REQUIRED' for x in controls['scientific_adverse_controls'])
    proc = subprocess.run([sys.executable, '-B', '-I', '-S', str(case / 'reproduce.py')],
                          text=True, capture_output=True, stdin=subprocess.DEVNULL)
    assert proc.returncode == 0, proc.stderr
    child = json.loads(proc.stdout)
    assert child['status'] == 'PASS' and child['id'] == ID and child['two_nonblind_AI_reviews'] is True
    assert child['classification'] == seal['classification'] and child['expert_validation_n'] == 0
    assert child['new_admissions'] == child['model_API_calls'] == child['native_calls'] == 0
    print(json.dumps({'status': 'PASS', 'cases': [{'id': ID, 'classification': seal['classification'],
          'subtype': seal['subtype'], 'child_result': child}], 'new_admissions': 0,
          'expert_validation_n': 0, 'model_API_calls': 0, 'new_native_calls': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
