#!/usr/bin/env python3
"""Package the two-question observed trend phase without credentials or live data."""
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
    programs=set().union(*(protocol['code_pins'] for protocol in protocols))|{'verify_observed_trend_evaluation.py','package_observed_trend_evaluation.py'}
    for name in sorted(programs):
        destination=out/'runtime'/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(BASE/name,destination)
    for wg in ['RAN1','RAN2','RAN3','RAN4','RAN5']:
        destination=out/'source_manifests'/(wg+'.manifest.json');destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(BASE/'relational'/(wg+'.manifest.json'),destination)
    text='''# Two original observed-agenda-trend questions: four-method evaluation

This phase fixes RAN3_P2_CQ6-1 and RAN4_P2_CQ6-1 before predictions. Their original English wording is preserved. The source-relative task counts distinct recorded Resolution nodes for the requested agenda at every retained Meeting, including zero counts, in ascending numeric meeting chronology. Equal ordinals allow any within-tie order. The auxiliary meeting ordinal is not a requested answer field. These are observed agenda-number trends, not a proof of stable topic semantics across meetings.

All eight method items remain in the denominator. The Anthropic Opus4.8 model has no provider/model fallback or quality retry. A/B receive frozen graph schema and exact complete physical SQLite DDL. C/D use the preserved bounded lexical retrieval protocol; complete archive-text/graph cutoff equality is not established. The output format supplies only value-free ordering rules, with no reference query, gold, answer values, retained meeting count or review material.

The two-item source repair bundle is checked against the preserved371 parent. Parent-relative373 is not the global admission count. Earlier contracts, predictions, scores and all original snapshot bytes remain preserved. This phase is separate from the new RAN2 source-enrichment snapshot experiment. Independent human/expert validation remains0.

Offline verification performs no API or database calls and replays strict requested-field scores and failure gates from actual retained outputs:

```sh
python3 -B -S runtime/verify_observed_trend_evaluation.py --evidence . --bundle /path/to/observed_trend_bundle --parent /path/to/parent371 --out /tmp/observed_trend_report.json
```

Raw requests omit authorization headers. Every package member is hashed. Live model/data reproduction remains distinct from this offline stored-output replay.
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
    manifest={'kind':'Fresh complete four-arm evaluation of two observed-agenda-trend original Core questions',
              'created_utc':datetime.now(timezone.utc).isoformat(),'additional_n':2,'method_items':8,'new_unique_core_ids':2,
              'bundle_manifest_sha256':runtime.sha(bundle/'manifest.json'),'parent_manifest_sha256':runtime.sha(parent/'manifest.json'),
              'human_expert_validation_n':0,'old_scores_transferred':False,'new_api_calls_by_packager':0,
              'files':{p.relative_to(out).as_posix():runtime.sha(p) for p in sorted(out.rglob('*')) if p.is_file()}}
    runtime.write(out/'manifest.json',manifest)
    print(json.dumps({'status':'PACKAGED','files':len(manifest['files']),'manifest_sha256':runtime.sha(out/'manifest.json')}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['bundle','parent','current','out']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();main(*(getattr(args,name).resolve() for name in ['bundle','parent','current','out']))
