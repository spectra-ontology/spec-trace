"""Analyze preserved first responses with the explicit optional-group reader."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
assert not sys.flags.optimize
BASE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('stage',choices=['analyze']);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--run-dir',type=Path,required=True);args=p.parse_args()
bundle,run=args.bundle.resolve(),args.run_dir.resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((BASE/'optional_order_group_reader_receipt.json').read_text())
assert sha(bundle/'manifest.json')==receipt['frozen_bundle_manifest_sha256'] and sha(run/'protocol.json')==receipt['frozen_protocol_sha256']
assert sha(bundle/'score_predictions.py')==receipt['original_reader_sha256'] and sha(BASE/'score_predictions_optional_order_groups.py')==receipt['compatibility_reader_sha256']
assert (BASE/'score_predictions_optional_order_groups.py').read_text()==(bundle/'score_predictions.py').read_text().replace(receipt['exact_original_expression'],receipt['exact_compatibility_expression'])
assert sha(bundle/'original_scorer.py')==receipt['original_kernel_sha256']
protected={p:sha(p)for p in list(bundle.rglob('*'))+list((run/'calls').glob('*'))+list(run.glob('*/predictions.jsonl'))+list(run.glob('*/statuses.jsonl'))if p.is_file()}
protected[run/'protocol.json']=sha(run/'protocol.json')
assert not (run/'analysis.json').exists()
sys.path[:0]=[str(bundle),str(BASE)]
spec=importlib.util.spec_from_file_location('score_predictions',BASE/'score_predictions_optional_order_groups.py');module=importlib.util.module_from_spec(spec);sys.modules['score_predictions']=module;spec.loader.exec_module(module)
import authorized_incremental35_evaluation as controller
controller.verify(bundle,run)
import analyze_predictions
output=analyze_predictions.run(bundle,run)
assert all(sha(p)==s for p,s in protected.items())
result={'status':'PASS_ANALYZED_SAME_FIRST_RESPONSES_OPTIONAL_READER_ONLY','question_n':output['admitted_n'],'methods':list(output['tables']),'protected_scientific_files_unchanged':len(protected),'reader_receipt_sha256':sha(BASE/'optional_order_group_reader_receipt.json'),'new_API_calls':0,'new_native_calls':0,'quality_rerolls':0}
with (run.parent.parent/'actual_ROOT_optional_group_reader_analysis.json').open('x')as f:json.dump(result,f,indent=2)
print(json.dumps(result))
