#!/usr/bin/env python3
"""Package the one-question source-invariant phase without credentials or live data."""
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


def main(bundle,parent,current,out):
    if out.exists() or not (current/'analysis.json').exists():raise ValueError('Package exists or scoring is incomplete')
    out.mkdir(parents=True)
    def copy_tree(source,target):
        for path in sorted(source.rglob('*')):
            if not path.is_file() or '__pycache__' in path.parts:continue
            if path.is_symlink():raise ValueError('Evidence symlink')
            destination=target/path.relative_to(source);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,destination)
    copy_tree(current,out/'current')
    protocols=[json.loads((phase/'protocol.json').read_text()) for phase in [current]]
    programs=set().union(*(protocol['code_pins'] for protocol in protocols))|{'verify_path_top5_evaluation.py','package_path_top5_publication.py'}
    for name in sorted(programs):
        destination=out/'runtime'/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(BASE/name,destination)
    for wg in ['RAN1','RAN2','RAN3','RAN4','RAN5']:
        destination=out/'source_manifests'/(wg+'.manifest.json');destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(BASE/'relational'/(wg+'.manifest.json'),destination)
    text='''# One new original-question four-method evaluation

This evidence contains fresh predictions for RAN3_P3_CQ4-4. Its original English is unchanged. All139 frozen Spec-number groups are in the native reference pool; two AI semantic judgments and a separate139-row native diagnostic confirm that Resolution, CR-entity, CR-document and structural-path counts yield the same five asked Spec identities. The counts and their order differ. This does not certify raw-archive completeness, causal enactment, all interpretations, or human/expert validation.

All four methods were registered before predictions and remain in the denominator. The pinned Opus4.8 model uses Anthropic only, without model/provider fallback or answer-quality retry. SQL receives complete physical value-free SQLite DDL. The two retrieval arms explicitly abstained; their outcomes are retained and failure-gated. Retrieval context is bounded, and archive-text cutoff equality with the graph remains UNKNOWN. No common supplemental-source appendix is supplied in this phase.

The public repair directory is `release_package/cqs/original_core_path_top5_repairs`; its manifest is2f28cea42ea6fa544a9a9a05db407d7f5ee85cc9028c055245b943615b277872. The separate one-item bundle is verified against the frozen371 parent. Its372 parent-relative scope is not a global current admission count. Earlier contracts, predictions and scores are preserved; the global current index combines this new disjoint ID separately.

Offline verification makes no API or database calls and replays strict requested-field scores and failure gates from stored actual outputs:

```sh
python3 -B -S runtime/verify_path_top5_evaluation.py --evidence . --bundle ../original_core_path_top5_repairs --parent ../original_core_repair --out /tmp/path_top5_report.json
```

Raw requests omit authorization headers. Every package member is hashed. Live native/model reproduction and independent human/raw-source validation remain separate from this offline replay.
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
    manifest={'kind':'Fresh complete four-arm evaluation of one source-invariant original Core question',
              'created_utc':datetime.now(timezone.utc).isoformat(),'additional_n':1,'method_items':4,'new_unique_core_ids':1,
              'bundle_manifest_sha256':runtime.sha(bundle/'manifest.json'),'parent_manifest_sha256':runtime.sha(parent/'manifest.json'),
              'human_expert_validation_n':0,'old_scores_transferred':False,'new_api_calls_by_packager':0,
              'files':{p.relative_to(out).as_posix():runtime.sha(p) for p in sorted(out.rglob('*')) if p.is_file()}}
    runtime.write(out/'manifest.json',manifest)
    print(json.dumps({'status':'PACKAGED','files':len(manifest['files']),'manifest_sha256':runtime.sha(out/'manifest.json')}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['bundle','parent','current','out']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();main(*(getattr(args,name).resolve() for name in ['bundle','parent','current','out']))
