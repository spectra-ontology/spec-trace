"""Analyze saved AUTH48 first responses using the explicit joint-record reader."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
if sys.flags.optimize:
    raise SystemExit('Enabled checks required')
BASE = Path(__file__).absolute().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def require(ok, why):
    if not ok:
        raise ValueError(why)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['analyze'])
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--run-dir', type=Path, required=True)
    args = parser.parse_args()
    bundle, run = args.bundle.resolve(), args.run_dir.resolve()
    receipt = json.loads((BASE / 'preparation_receipt.json').read_bytes())
    require(sha(bundle / 'score_predictions.py') == receipt['original_reader']['sha256'], 'Original shared reader preserved')
    require(sha(BASE / 'analyze_predictions.py') == receipt['analysis_original']['sha256'], 'Original analysis preserved')
    for name, field in [('score_predictions_joint_sample.py', 'reader_copy'),
                        ('analyze_predictions_joint_sample.py', 'analysis_explicit_reader_import'),
                        ('item_scorer_dispatch.py', 'new_dispatcher'),
                        ('one_record_sample_scorer.py', 'prospective_joint_wrapper')]:
        require(sha(BASE / name) == receipt[field]['sha256'], 'Prospective runtime scoring:' + name)
        if name != 'analyze_predictions_joint_sample.py':
            require(sha(bundle / name) == sha(BASE / name), 'Exact runtime/bundle scoring:' + name)
    text = (bundle / 'score_predictions.py').read_text()
    for before, after in receipt['exact_replacements']:
        require(text.count(before) == 1, 'Exact explicit reader adaptation')
        text = text.replace(before, after)
    require(text == (BASE / 'score_predictions_joint_sample.py').read_text(), 'Exact joint input/dispatcher adaptation')
    protected = {path: sha(path) for path in list(bundle.rglob('*')) + list((run / 'calls').glob('*'))
        + list(run.glob('*/predictions.jsonl')) + list(run.glob('*/statuses.jsonl')) if path.is_file()}
    protected[run / 'protocol.json'] = sha(run / 'protocol.json')
    require(not (run / 'analysis.json').exists(), 'Preserve previous first-response analysis')
    sys.path[:0] = [str(bundle), str(BASE)]
    import authorized_incremental48_evaluation as controller
    controller.verify(bundle, run)
    spec = importlib.util.spec_from_file_location('auth48_explicit_joint_analysis', BASE / 'analyze_predictions_joint_sample.py')
    analysis = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(analysis)
    output = analysis.run(bundle, run)
    require(all(sha(path) == digest for path, digest in protected.items()), 'Saved responses/predictions/protocol/bundle unchanged')
    result = {'status': 'PASS_SAME_FIRST_RESPONSES_EXPLICIT_JOINT_RECORD_SCORING',
        'question_n': output['admitted_n'], 'methods': list(output['tables']),
        'protected_scientific_files_unchanged': len(protected),
        'reader_receipt_sha256': sha(BASE / 'preparation_receipt.json'),
        'scoring_scope': 'AUTH48 RAN1_P4_CQ2-3 one complete three-field record only',
        'historical_scores_or_predictions_changed': False, 'sys_modules_monkeypatch': False,
        'new_API_calls': 0, 'new_native_calls': 0, 'quality_rerolls': 0}
    with (run.parent.parent / 'actual_ROOT_explicit_joint_reader_analysis.json').open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result))

if __name__ == '__main__':
    main()
