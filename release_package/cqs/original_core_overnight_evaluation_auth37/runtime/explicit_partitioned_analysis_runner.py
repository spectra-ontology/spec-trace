"""Analyze the same first responses through the declared partitioned supplement."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
if sys.flags.optimize:raise ValueError('Enabled checks required')
BASE=Path(__file__).absolute().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['analyze']);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--run-dir',type=Path,required=True)
    a=p.parse_args();bundle=a.bundle.absolute();run=a.run_dir.absolute()
    for path in [bundle,run,BASE]:
        for item in [path,*path.parents]:
            if item.is_symlink():raise ValueError('Symlink input or ancestor')
    sys.path[:0]=[str(bundle),str(BASE)]
    import cohort_evaluation as controller
    protocol=controller.verify(bundle,run)
    declared=protocol['declared_partitioned_analysis']
    if declared['analysis_entry']!='explicit_partitioned_analysis_runner.py' or declared['effective_score_entry']!='score_predictions_partitioned_reader.py' or declared['canonical_scientific_modules_changed_n']!=0:raise ValueError('Analysis dispatch declaration differs')
    for name in ['explicit_partitioned_analysis_runner.py','analyze_predictions_partitioned.py']:
        if protocol['code_pins'][name]!=sha(BASE/name):raise ValueError('Analysis implementation differs')
    if declared['bundle_effective_reader_sha256']!=sha(bundle/'score_predictions_partitioned_reader.py') or declared['dispatch_declaration_sha256']!=sha(bundle/'dispatch_declaration.json'):raise ValueError('Effective scorer differs')
    receipt=json.loads((BASE/'runtime_source_copy_receipt.json').read_text())
    if any(sha(BASE/r['file'])!=r['sha256'] for r in receipt['scientific_runtime_nine']):raise ValueError('Scientific runtime bytes differ')
    protected={p:sha(p) for p in list(bundle.rglob('*'))+list((run/'calls').glob('*'))+list(run.glob('*/predictions.jsonl'))+list(run.glob('*/statuses.jsonl')) if p.is_file()}
    protected[run/'protocol.json']=sha(run/'protocol.json')
    if (run/'analysis.json').exists():raise ValueError('Preserve previous analysis')
    spec=importlib.util.spec_from_file_location('declared_partitioned_analysis',BASE/'analyze_predictions_partitioned.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    output=module.run(bundle,run)
    if output['admitted_n']!=1 or any(t['overall']['n']!=1 for t in output['tables'].values()):raise ValueError('Complete four-method N1 denominator changed')
    if any(sha(p)!=s for p,s in protected.items()):raise ValueError('Protected scientific inputs/outputs changed')
    result={'status':'PASS_FIRST_RESPONSES_EXPLICIT_PARTITIONED_COMPLETE_WI_ANALYSIS','question_n':1,'methods':list(output['tables']),'effective_score_entry':'score_predictions_partitioned_reader.py','metric_unit':'one complete outer WI record','lawful_nested_answers':5,'canonical_scientific_modules_changed_n':0,'protected_files_unchanged':len(protected),'new_API_calls':0,'new_native_calls':0,'quality_rerolls':0}
    with (run/'explicit_partitioned_analysis_receipt.json').open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
