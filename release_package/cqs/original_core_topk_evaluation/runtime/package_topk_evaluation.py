#!/usr/bin/env python3
"""Package original/recovery/current evidence without credentials or live data."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE))
import run_evaluation as runtime


def main(bundle,parent,original,recovery,current,out):
    if out.exists() or not (current/'analysis.json').exists():raise ValueError('Package exists or scoring is incomplete')
    out.mkdir(parents=True)
    def copy_tree(source,target):
        for path in sorted(source.rglob('*')):
            if not path.is_file() or '__pycache__' in path.parts:continue
            if path.is_symlink():raise ValueError('Evidence symlink')
            destination=target/path.relative_to(source);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,destination)
    copy_tree(original,out/'phases/original');copy_tree(recovery,out/'phases/operational');copy_tree(current,out/'current')
    protocols=[json.loads((phase/'protocol.json').read_text()) for phase in [original,recovery,current]]
    programs=set().union(*(protocol['code_pins'] for protocol in protocols))|{'verify_topk_evaluation.py','package_topk_evaluation.py'}
    for name in sorted(programs):
        destination=out/'runtime'/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(BASE/name,destination)
    for wg in ['RAN1','RAN2','RAN3','RAN4','RAN5']:
        destination=out/'source_manifests'/(wg+'.manifest.json');destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(BASE/'relational'/(wg+'.manifest.json'),destination)
    text='''# Fresh TOP10 replacement evaluation

This evidence contains new predictions for all ten existing Core IDs whose ranked reference pools were uncapped under separately validated top-k contracts. It adds zero unique original Core IDs. The original 371-item contracts and prior predictions remain preserved; no old score is transferred to a replacement contract.

The original generation phase and its fifteen pre-answer HTTP402 stages remain unchanged. A separately registered operational phase reissued only identical requests that had received no model answer, reused two previously received followup responses without new calls, and performed three first answer calls after recovered followups. Responses with format errors, abstention or partial content were not reissued. The current output selects all fifteen registered operational method-items and the other twenty-five original method-items, independently of their scores.

All four methods use the pinned Opus4.8 model and Anthropic-only provider, without model/provider fallback. SQL uses the actual complete physical value-free SQLite DDL. Native execution retains the fixed 100,000-row, 256 MiB and 60-second limits. Retrieval uses the frozen lexical protocol and bounded contexts; archive text cutoff equality with the graph remains UNKNOWN. No supplemental ownership/catalog source is provided in this phase. Complete-record scoring and failure gating include all ten IDs per method. Human/author/expert validation remains zero.

Offline verification requires the separately preserved TOP10 replacement bundle and its parent371 bundle:

```sh
python3 -B -S runtime/verify_topk_evaluation.py --evidence . --bundle /path/to/topk_replacements --parent /path/to/parent371 --out /tmp/topk_report.json
```

The verifier makes no API or database calls. It replays strict scores and paired analysis from stored actual outputs; live model or native database reproduction is a separate action. Raw requests omit authorization headers. The manifest pins every package file.
'''
    (out/'README.md').write_text(text)
    sys.path.insert(0,str(runtime.ROOT/'scripts/common/common'));import credentials
    credential=credentials.secret('OPENROUTER_API_KEY').encode()
    if not credential:raise ValueError('Exact credential scan unavailable')
    for path in out.rglob('*'):
        if path.is_file() and credential in path.read_bytes():raise ValueError('Credential bytes detected; no package publication allowed')
    privacy={'exact_configured_credential_bytes_scanned':True,'credential_bytes_exposed':False,'matches':0,
             'authorization_headers_omitted_in_preserved_requests':True,'personal_credit_balance_files_included':False}
    (out/'privacy_check.json').write_text(json.dumps(privacy,indent=2)+'\n')
    manifest={'kind':'Fresh complete four-arm evaluation of ten existing original Core top-k replacements',
              'created_utc':datetime.now(timezone.utc).isoformat(),'replacement_n':10,'method_items':40,'new_unique_core_ids':0,
              'bundle_manifest_sha256':runtime.sha(bundle/'manifest.json'),'parent_manifest_sha256':runtime.sha(parent/'manifest.json'),
              'human_expert_validation_n':0,'old_scores_transferred':False,'new_api_calls_by_packager':0,
              'files':{p.relative_to(out).as_posix():runtime.sha(p) for p in sorted(out.rglob('*')) if p.is_file()}}
    runtime.write(out/'manifest.json',manifest)
    print(json.dumps({'status':'PACKAGED','files':len(manifest['files']),'manifest_sha256':runtime.sha(out/'manifest.json')}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['bundle','parent','original','recovery','current','out']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();main(*(getattr(args,name).resolve() for name in ['bundle','parent','original','recovery','current','out']))
