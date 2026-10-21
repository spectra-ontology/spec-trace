"""Explicit prospective runtime reader for the partitioned top-k supplement.

Unlike the unchanged generic score_predictions, this declared entry point reads
the complete partition population and invokes the complete outer-WI metric.
It never changes the canonical modules or treats a source fixture as native.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
D = Path(__file__).resolve().parent
P = D.parent
sys.path[:0] = [str(P), str(P / 'canonical'), str(D)]
import scorer
import original_scorer
import verify_release
import bound_partition_adapter
import partitioned_complete_record_score as metrics

def run(task, fixed_definition, policy, limited_native_records, population,
        prediction, declaration):
    """Use already read values after byte pins have been verified by read_run."""
    identity = verify_release.digest(fixed_definition)
    if (type(task) is not dict or task.get('validation_status') != 'validated'
            or task.get('repair_sha256') != identity or task.get('id') != fixed_definition['id']):
        raise ValueError('task envelope does not identify this validated exact contract')
    if (declaration.get('id') != fixed_definition['id'] or declaration.get('repair_sha256') != identity
            or declaration.get('dispatch') != 'explicit_partitioned_top_k_complete_outer_WI_record'
            or declaration.get('limited_native_is_eligibility_population') is not False):
        raise ValueError('explicit dispatch declaration or native/eligibility distinction differs')
    if (prediction.get('id') != task['id'] or prediction.get('repair_sha256') != identity
            or set(prediction) != {'id', 'repair_sha256', 'records'}):
        raise ValueError('prediction envelope differs')
    # Validate actual limited records independently of the model prediction.
    bridge = metrics.score(fixed_definition, policy, population, limited_native_records,
        scorer, original_scorer, verify_release, bound_partition_adapter,
        diagnostic=False, validated_task=task)
    if bridge['exact'] is not True:
        raise ValueError('actual limited native records fail their full eligibility bridge')
    result = metrics.score(fixed_definition, policy, population, prediction['records'],
        scorer, original_scorer, verify_release, bound_partition_adapter,
        diagnostic=False, validated_task=task)
    return dict(id=task['id'], **result)

def read_run(root, declaration_path, predictions_path):
    root = Path(root).absolute()
    def regular(path):
        path = Path(path).absolute()
        for part in [path, *path.parents]:
            if part.is_symlink():
                raise ValueError('symlink input or ancestor is forbidden')
        if not path.is_file():
            raise ValueError('input must be a regular file')
        return path
    declaration = json.loads(regular(declaration_path).read_text())
    required = {'task', 'definition', 'policy', 'limited_native_records', 'full_native_partition_population',
                'metric_code', 'dispatch_code', 'metric_specification'}
    if set(declaration['files']) != required:
        raise ValueError('declared input set differs')
    values = {}
    for role, entry in declaration['files'].items():
        relative = Path(entry['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('input is not package-relative')
        path = regular(root / relative)
        raw = path.read_bytes()
        if type(entry['bytes']) is not int or len(raw) != entry['bytes'] or hashlib.sha256(raw).hexdigest() != entry['sha256']:
            raise ValueError('declared input byte identity differs: ' + role)
        values[role] = raw
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != declaration['files']['dispatch_code']['sha256']:
        raise ValueError('running dispatch differs from the declared code')
    if hashlib.sha256(Path(metrics.__file__).read_bytes()).hexdigest() != declaration['files']['metric_code']['sha256']:
        raise ValueError('running metric differs from the declared code')
    loads = scorer.get_kernel().loads_exact
    task, definition, policy, population = (loads(values[key].decode()) for key in
        ['task', 'definition', 'policy', 'full_native_partition_population'])
    native = [loads(s) for s in values['limited_native_records'].decode().splitlines() if s.strip()]
    predictions = [loads(s) for s in regular(predictions_path).read_text().splitlines() if s.strip()]
    if len(predictions) != 1:
        raise ValueError('one explicit partitioned task prediction envelope required')
    return run(task, definition, policy, native, population, predictions[0], declaration)

if __name__ == '__main__':
    if sys.flags.optimize:
        raise RuntimeError('optimized Python is not supported')
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--declaration', type=Path, required=True)
    parser.add_argument('--predictions', type=Path, required=True)
    args = parser.parse_args()
    print(scorer.get_kernel().json_exact(read_run(args.root, args.declaration, args.predictions)))
