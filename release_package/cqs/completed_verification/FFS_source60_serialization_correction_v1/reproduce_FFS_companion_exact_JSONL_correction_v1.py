"""Reproduce the retained serialization correction without touching prior outputs.

Spec: same FFS task, records, rank groups, controls and scoring inputs.
Ontology: no source, graph, property or relation changes.
Cycle: immutable companion V3 to exact retained V4 in a new output directory.
배경: line-oriented CLI rejected pretty JSON stored under a JSONL suffix.
사용: --prior <retained V3> --output <new directory> --receipt <new JSON>.
LLM 호출: none. No database, provider or public mutation.
"""
import argparse, hashlib, json, shutil
from pathlib import Path

PRIOR_SHA='c78fd403f72d9e2e829e46c786aaf932f566acee8b6af5b18097d18d5acaa153'
AFTER_SHA='689a76b39f8825a83248c58f8048189d24e22c4655cbb53c3091b8e1598f2e5f'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
    a=argparse.ArgumentParser();a.add_argument('--prior',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--receipt',type=Path,required=True);v=a.parse_args()
    assert not v.output.exists() and not v.receipt.exists()
    assert sha(v.prior/'manifest.json')==PRIOR_SHA
    m=json.loads((v.prior/'manifest.json').read_text())
    v.output.mkdir(parents=True)
    for f in m['files']:
        src=v.prior/f['path'];dst=v.output/f['path']
        assert sha(src)==f['sha256'] and src.stat().st_size==f['bytes']
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    gold=v.output/'evaluation/reference_gold.jsonl'
    original=json.loads(gold.read_text())
    assert sha(gold)=='4a169b8c6bb9f53674c66d6cee30394d1d2bdb30de8861d29a52f811748161ec'
    gold.write_text(json.dumps(original,ensure_ascii=False,separators=(',',':'))+'\n')
    assert json.loads(gold.read_text())==original
    assert sha(gold)=='6065d8309e83fcfcac293e8878c3fcd40567a59e2ea42cf44441cc1bb9e828da'
    correction={
      'kind':'Serialization-only portable CLI correction',
      'prior_companion_manifest_sha256':PRIOR_SHA,
      'failed_export_path':'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/RAN1/source_variant_evaluation_exports/source60_FFS_Agreement_eval_v1',
      'actual_failure':'JSONDecodeError from line-oriented JSONL parser on pretty-printed single JSON object before model scoring',
      'changed_payload_only':'evaluation/reference_gold.jsonl: same parsed JSON object, now one line',
      'original_gold_sha256':'4a169b8c6bb9f53674c66d6cee30394d1d2bdb30de8861d29a52f811748161ec',
      'new_gold_sha256':sha(gold),
      'parsed_gold_definition_records_order_groups_equal':True,
      'source_runtime_provider_prompts_responses_queries_native_SQL_controls_scores_changed':False,
      'old_companion_and_failed_export_preserved':True}
    save(v.output/'jsonl_serialization_correction_receipt.json',correction)
    m['files']=[{'path':str(p.relative_to(v.output)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(v.output.rglob('*')) if p.is_file()]
    m['serialization_correction_receipt']='jsonl_serialization_correction_receipt.json'
    m['prior_immutable_manifest_sha256']=PRIOR_SHA
    save(v.output/'manifest.json',m)
    assert sha(v.output/'manifest.json')==AFTER_SHA
    after={f['path']:f for f in m['files']}
    before={f['path']:f for f in json.loads((v.prior/'manifest.json').read_text())['files']}
    assert set(after)-set(before)=={'jsonl_serialization_correction_receipt.json'}
    assert [p for p in before if before[p]!=after[p]]==['evaluation/reference_gold.jsonl']
    save(v.receipt,{'status':'PASS','prior_manifest_sha256':PRIOR_SHA,'actual_reconstructed_manifest_sha256':AFTER_SHA,
       'payload_changed_only':['evaluation/reference_gold.jsonl'],'payload_added_only':['jsonl_serialization_correction_receipt.json'],
       'parsed_gold_equal':True,'other_payload_bytes_equal':True,'originals_modified':False,'script_sha256':sha(Path(__file__))})
    print(json.dumps({'status':'PASS','manifest_sha256':AFTER_SHA,'receipt_sha256':sha(v.receipt)}))
if __name__=='__main__':main()
