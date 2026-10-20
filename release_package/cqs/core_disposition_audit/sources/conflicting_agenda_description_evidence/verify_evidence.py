"""Bind the source-replayed conditional diagnostic to two separate AI judgments."""
import sys
if sys.flags.optimize:
    raise SystemExit('Verification requires assertions; optimized execution is refused.')
import hashlib
import json
import os
from pathlib import Path
import subprocess

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def no_symlink(path):
    for item in (path, *path.parents):
        require(not item.is_symlink(), 'Symlink boundary rejected')

no_symlink(Path(os.path.abspath(__file__)))
HERE = Path(__file__).resolve().parent
for path in HERE.rglob('*'):
    no_symlink(path)
    require(path.is_file() or path.is_dir(), 'Nonregular entry rejected')
PINS = {'reviews/ROOT_secondary_seven_units.json': {'sha256': 'efbc5185b693cc955fc1f2a24aef626fc88ca6da83db9cc17e825e25a1a77027', 'bytes': 4692}, 'reviews/ROOT_final_portable_binding.json': {'sha256': 'a4b5393f1dec592ae8a02134a61b886050f0ad8480a92be86458a939686842ae', 'bytes': 4067}, 'reviews/ROOT_final_seal.json': {'sha256': '6d6c7f23eac7232840c9bd759c82b5e16a9544964f406b96607bf51e54d4586f', 'bytes': 1196}}
for name, expected in PINS.items():
    data = (HERE / name).read_bytes()
    require(len(data) == expected['bytes'] and hashlib.sha256(data).hexdigest() == expected['sha256'], 'ROOT review binding changed: ' + name)

def load(name):
    return json.loads((HERE / name).read_bytes())

def pin(name, expected):
    data = (HERE / name).read_bytes()
    require(len(data) == expected['bytes'] and hashlib.sha256(data).hexdigest() == expected['sha256'], 'Included dependency changed: ' + name)

review = load('reviews/ROOT_secondary_seven_units.json')
criteria = load('diagnostic/canonical/criteria.json')
require([item['unit'] for item in review['exact_seven_unit_findings']] == criteria['semantic_units'], 'ROOT seven-unit coverage differs')
require(review['id'] == 'RAN1_P2_CQ1-1' and review['recommendation'] == 'clarification_required' and review['classification_is_conditional'] is True, 'ROOT conditional classification differs')
require(review['not_a_blind_or_human_review'] is True and review['expert_validation_n'] == 0 and review['public_admission'] is False, 'Review attribution/admission differs')
pin('diagnostic/primary_exact_seven_unit_classification_review.json', review['primary_review'])
pin('diagnostic/ROOT_actual_source_numeric_and_conflicting_description_replay.json', review['ROOT_actual_source_and_typed_value_replay'])
binding = load('reviews/ROOT_final_portable_binding.json')
pin('reviews/ROOT_secondary_seven_units.json', binding['ROOT_review'])
pin('diagnostic/manifest.json', binding['portable_manifest'])
pin('diagnostic/verify_diagnostic.py', binding['portable_verifier'])
seal = load('reviews/ROOT_final_seal.json')
pin('reviews/ROOT_final_portable_binding.json', seal['final_packet'])
require(seal['id'] == 'RAN1_P2_CQ1-1' and seal['final_local_decision'] == 'clarification_required' and seal['public_admission'] is False, 'Final seal differs')
require(seal['human_expert_validation_n'] == 0 and seal['new_model_calls'] == 0, 'Seal attribution/calls differ')
environment = {'PATH': os.environ.get('PATH','/usr/bin:/bin'), 'LANG':'C.UTF-8', 'PYTHONDONTWRITEBYTECODE':'1'}
run = subprocess.run([sys.executable, '-B', '-I', '-S', str(HERE/'diagnostic/verify_diagnostic.py')], cwd=HERE, env=environment, text=True, capture_output=True, timeout=120)
require(run.returncode == 0, 'Source diagnostic failed: ' + run.stderr)
result = json.loads(run.stdout)
require(result['status'] == 'PASS_BOUNDED_CONDITIONAL_CLARIFICATION_REPLAY' and result['API_calls'] == 0 and result['fresh_native_executions'] == 0, 'Unexpected diagnostic result')
print(json.dumps({'status':'PASS', 'id':'RAN1_P2_CQ1-1', 'classification':'clarification_required', 'classification_is_conditional':True, 'root_secondary_seven_unit_reviews_verified_n':1, 'two_separate_nonblind_AI_reviews':True, 'expert_validation_n':0, 'new_admissions':0, 'new_model_calls':0, 'source_diagnostic':result}, ensure_ascii=False))
