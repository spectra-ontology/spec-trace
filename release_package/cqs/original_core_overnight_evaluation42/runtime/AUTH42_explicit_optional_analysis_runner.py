"""Analyze original first responses with the explicit optional-group reader copy."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
if sys.flags.optimize:raise SystemExit('Enabled checks required')
BASE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['analyze']);parser.add_argument('--bundle',type=Path,required=True);parser.add_argument('--run-dir',type=Path,required=True)
args=parser.parse_args();bundle=args.bundle.resolve();run=args.run_dir.resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((BASE/'preparation_receipt.json').read_text())
assert sha(bundle/'score_predictions.py')==receipt['original_reader']['sha256']
assert sha(BASE/'score_predictions_optional_order_groups.py')==receipt['reader_copy']['sha256']
assert sha(BASE/'analyze_predictions.py')==receipt['analysis_original']['sha256']
assert sha(BASE/'analyze_predictions_optional_order_groups.py')==receipt['analysis_explicit_reader_import']['sha256']
assert (BASE/'score_predictions_optional_order_groups.py').read_text()==(bundle/'score_predictions.py').read_text().replace(receipt['exact_before'],receipt['exact_after'])
protected={p:sha(p) for p in list(bundle.rglob('*'))+list((run/'calls').glob('*'))+list(run.glob('*/predictions.jsonl'))+list(run.glob('*/statuses.jsonl')) if p.is_file()}
protected[run/'protocol.json']=sha(run/'protocol.json')
assert not (run/'analysis.json').exists()
sys.path[:0]=[str(bundle),str(BASE)]
import authorized_incremental42_evaluation as controller
controller.verify(bundle,run)
spec=importlib.util.spec_from_file_location('auth41_explicit_analysis',BASE/'analyze_predictions_optional_order_groups.py')
analysis=importlib.util.module_from_spec(spec);spec.loader.exec_module(analysis)
output=analysis.run(bundle,run)
assert all(sha(p)==s for p,s in protected.items())
result={'status':'PASS_SAME_FIRST_RESPONSES_EXPLICIT_OPTIONAL_INPUT_READER','question_n':output['admitted_n'],'methods':list(output['tables']),'protected_scientific_files_unchanged':len(protected),'reader_receipt_sha256':sha(BASE/'preparation_receipt.json'),'sys_modules_monkeypatch':False,'new_API_calls':0,'new_native_calls':0,'quality_rerolls':0}
with (run.parent.parent/'actual_ROOT_explicit_optional_reader_analysis.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
