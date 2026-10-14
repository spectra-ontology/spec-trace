#!/usr/bin/env python3
"""Register one new question repair under current value-free physical SQL DDL."""
import argparse
import json
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent
RECHECK=HERE.parent
EMP=RECHECK.parent
sys.path.insert(0,str(EMP))
sys.path.insert(0,str(RECHECK))
import freeze_additional_evaluation
import run_evaluation as runtime


def freeze(bundle,parent,run):
    freeze_additional_evaluation.main(bundle,parent,run)
    protocol=json.loads((run/'protocol.json').read_text())
    if protocol['cohort_ids'] != ['RAN1_P2_CQ2-2']:
        raise ValueError('Unexpected incremental cohort')
    ddl=EMP/'sql_interface_v2/schemas/RAN1_sql.json'
    shutil.copy2(ddl,run/'schemas/RAN1_sql.json')
    protocol['schema_pins']={str(p.relative_to(run)):runtime.sha(p) for p in (run/'schemas').glob('*.json')}
    protocol['generation_workers']=1
    protocol['execution_workers']=1
    protocol['budget_guard_usd']=2.0
    protocol['incremental_registration']={
        'program_sha256':runtime.sha(Path(__file__)),
        'source_semantic_scope':'Named draft explicitly agreed in the original report; no general edge causality.',
        'original_400_bytes_modified':False,
        'model_input':'Unchanged English question, requested output format, ordinary graph/physical SQL schema, and frozen native text retrieval only.',
        'additional_source_appendix':False,
        'SQL_interface':'Same audited value-free physical DDL used for the current SQL interface; SQLite bytes preserved.',
        'source_SQL_DDL_sha256':runtime.sha(ddl),
        'quality_regeneration_allowed':False,
        'paid_calls_before_registration':0,
        'new_cost_cap_usd':2.0,
    }
    runtime.write(run/'protocol.json',protocol)
    runtime.verify_pins(bundle,run)
    print(json.dumps({'status':'FROZEN','n':1,'expected_max_stage_calls_without_transport_retry':5,
                      'budget_cap_usd':2.0,'protocol_sha256':runtime.sha(run/'protocol.json')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--parent',type=Path,required=True)
    parser.add_argument('--run-dir',type=Path,required=True)
    args=parser.parse_args()
    freeze(args.bundle.resolve(),args.parent.resolve(),args.run_dir.resolve())
