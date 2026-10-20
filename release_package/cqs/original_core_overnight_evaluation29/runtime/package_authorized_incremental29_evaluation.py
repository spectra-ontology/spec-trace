#!/usr/bin/env python3
"""Package completed AUTH29 N2 outputs only; never start calls or databases."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys

sys.dont_write_bytecode = True
if sys.flags.optimize != 0:
    raise RuntimeError('Optimized packager execution unsupported')
OUT = Path(os.path.abspath(__file__)).parent
IDS = {'RAN1_P3_CQ030', 'RAN1_P3_CQ025'}
METHODS = ('text2cypher','text2sql','single_retrieval','iterative_retrieval')

def require(value,reason):
    if not value:raise ValueError(reason)

def no_link(path):
    p=Path(os.path.abspath(path))
    for q in [*reversed(p.parents),p]:
        require(not q.is_symlink(),'symlink refused before target read: '+str(q))
    return p

def sha(path):return hashlib.sha256(no_link(path).read_bytes()).hexdigest()
def load(path):return json.loads(no_link(path).read_text())
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)

def main(args):
    bundle,run,target,auth,project_root,runtime=map(no_link,(args.bundle,args.run,args.target,args.auth,args.project_root,args.runtime))
    require(not target.exists(),'Preserve earlier output; target must be new')
    require(sha(run/'protocol.json')==args.protocol_sha256,'Final actual frozen protocol differs')
    require(sha(bundle/'manifest.json')==args.bundle_manifest_sha256,'Final actual bundle differs')
    protocol=load(run/'protocol.json');analysis=load(run/'analysis.json')
    require(analysis['admitted_n']==protocol['admitted_n']==2,'Full N2 analysis required')
    require(set(protocol['cohort_ids'])==IDS,'Exact two-ID cohort required')
    extension=protocol['authorized_incremental29_extension']
    require(extension['scope_sha256']==sha(auth/'scope.json'),'AUTH29 exact scope differs')
    require(extension['scope_n']==2 and extension['method_items_n']==8 and extension['planned_calls_without_transport_retry']==10,'N2/8/10 protocol mismatch')
    generation=load(run/'generation_complete.json')
    require(generation['completed_method_items']==generation['required']==8,'All eight method outcomes required')
    require(all(analysis['tables'][m]['overall']['n']==2 for m in METHODS),'All methods must retain both IDs')
    require(args.operational_proof,'Preserve actual operational lifecycle/failure receipts with --operational-proof')
    target.mkdir(parents=True)
    def copy(source,relative,expected=None):
        source=no_link(source);rel=PurePosixPath(relative)
        require(not rel.is_absolute() and '..' not in rel.parts,'Unsafe publication relative path')
        require(source.is_file(),'Nonregular source refused: '+str(source))
        actual=sha(source)
        require(expected is None or actual==expected,'Frozen source changed: '+str(source))
        dest=no_link(target/relative);dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():require(sha(dest)==actual,'Conflicting duplicate package destination')
        else:shutil.copyfile(source,dest)
    for path in sorted(run.rglob('*')):
        no_link(path)
        if path.is_dir():continue
        require(path.is_file(),'Nonregular run entry refused')
        require('__pycache__' not in path.parts and path.suffix not in {'.sqlite','.db','.env','.pyc'} and path.name not in {'.env','credentials.json'},'Unnecessary/secret/large runtime input in run tree')
        copy(path,'current/'+path.relative_to(run).as_posix())
    for name,expected in protocol['code_pins'].items():copy(runtime/name,'runtime/'+name,expected)
    copy(runtime/'runtime_source_copy_receipt.json','runtime/runtime_source_copy_receipt.json',extension['source_copy_receipt_sha256'])
    early_path=runtime/'early_execution_reader_copy_receipt.json'
    if early_path.exists():
        early=load(early_path)
        require(early['source_sha256']==early['copy_sha256'] and early['generation_and_adapter_code_modified'] is False and early['execution_scheduling_only'] is True,'Early reader adaptation changed method code')
        copy(runtime/'execute_ready.py','runtime/execute_ready.py',early['copy_sha256'])
        copy(early_path,'runtime/early_execution_reader_copy_receipt.json')
    provenance=load(args.guard_adaptation)
    require(provenance['native_lock_memory_cpu_readonly_protocol_unchanged'] is True and provenance['API_calls']==0,'Guard source review/provenance required')
    copy(args.guard,'runtime/AUTH29_root_guarded_native_execution_v1.py',provenance['destination_sha256'])
    original_guard=no_link(project_root/provenance['source_path'])
    copy(original_guard,'runtime/original_guard_scheduler.py',provenance['source_sha256'])
    copy(args.guard_adaptation,'runtime/AUTH29_root_guarded_native_execution_v1.adaptation.json')
    for name in ['verify_incremental29_exact_prompts_and_parsers.py','package_authorized_incremental29_evaluation.py']:
        copy(OUT/name,'runtime/'+name)
    sql_root=no_link(args.sql_manifest_root)
    sql_resolution=[]
    for wg,item in protocol['sql_manifests'].items():
        explicit=no_link(sql_root/(wg+'.manifest.json'))
        require(Path(item['path']).resolve()==explicit,'Explicit real SQL manifest does not resolve the frozen runtime alias')
        copy(explicit,'source_manifests/'+wg+'.manifest.json',item['sha256'])
        sql_resolution.append({'wg':wg,'protocol_source_path':item['path'],'explicit_real_source_path':str(explicit),'sha256':item['sha256'],'before_read_symlink_check_on_explicit_path':True})
    (target/'source_manifests/copy_resolution_provenance.json').write_text(json.dumps({'kind':'Explicit frozen SQL manifest resolution only; no database reads','files':sql_resolution,'runtime_alias_followed_as_input':False,'new_database_calls':0},indent=2)+'\n')
    for name in ['scope.json','admission_inputs.json']:
        copy(auth/name,'authorization/'+name)
    # The frozen scientific scope retains the private authorization hash. Personal
    # credit observations and account budget bookkeeping are not release inputs.
    if (auth/'additional_budget_authorization.json').exists():
        (target/'authorization/private_budget_provenance_omitted.json').write_text(json.dumps({
            'private_file_sha256':sha(auth/'additional_budget_authorization.json'),
            'private_account_observations_shipped':False,
            'scope_bytes_unchanged':True,
            'note':'Private account/budget provenance is hash-referenced by the original scope; actual model usage and per-call costs remain fully public.'},indent=2)+'\n')
    operational=[]
    for number,source in enumerate(args.operational_proof):
        source=no_link(source)
        require(source.is_file(),'Operational proof must be an explicit regular file')
        rel='operational_provenance/'+str(number).zfill(2)+'_'+sha(source)[:8]+'_'+source.name
        copy(source,rel)
        operational.append({'file':rel,'sha256':sha(source),'bytes':source.stat().st_size,
                            'original_filename':source.name})
    (target/'operational_provenance/index.json').write_text(json.dumps({'kind':'Explicit actual operational receipts, including failures; no replacement or rerun',
                                                                    'files':operational,'additional_public_admissions_by_packager':0},indent=2)+'\n')
    table=(run/'performance_table.md').read_text()
    (target/'README.md').write_text('# Two original questions: separate first evaluation\n\nThis N2 cohort evaluates a finite CSI-related table metadata lookup and recorded Agreement counts per TS. Registration starts from495 active contracts; prospective497/14/49 is not itself a publication claim. Earlier cohorts and results remain separate.\n\n{table}\n\nThe source-reviewed reference contracts were fixed before model calls. Original questions are unchanged. CQ030 preserves the original finite20 metadata path-row multiset and reuses its exact original saved native result. CQ025 repairs the count table to retain all eight TS families, including two zeros, and uses the exact repaired guarded native result. Source-positive raw excerpts, complete SQL comparisons, separate nonblind AI reviews and typed adverse controls are retained. Human/expert validation remains zero.\n\nA real non-caption CSI parameter table and real missing documentary CR citations are disclosed. The accepted tasks cover the authored finite metadata operation and captured reference-path counts; they do not certify all CSI tables, complete source citations, approval or consensus quality. Source verification does not enrich model inputs.\n\nAll first outcomes, errors, abstentions, requests, responses, cost and prompts remain in the denominator. No quality rerolls or earlier-score transfers are used. The runtime reuses the prior explicitly registered sequence-compatibility fix without further method changes. Offline replay calls no API or database:\n\n    python3 -B -I runtime/verify_authorized_incremental29_evaluation.py --evidence . --bundle ../original_core_overnight_repairs29\n\nLarge graphs, databases and retrieval indexes are omitted. Local provenance paths are not offline dependencies. No whole-graph factuality or expert certification is claimed.\n'.replace('{table}',table))
    # Root-owned exact configured-secret publication scan; this helper is not executed by preparation agents.
    sys.path.insert(0,str(project_root/'scripts/common/common'))
    import credentials
    exact_secret=credentials.secret('OPENROUTER_API_KEY').encode()
    require(bool(exact_secret),'Configured credential unavailable for exact scan')
    # Verifier source is generated before the scan so it too is checked.
    template=(OUT/'verify_authorized_incremental29_evaluation.template.py').read_text()
    verifier_rel='runtime/verify_authorized_incremental29_evaluation.py'
    (target/verifier_rel).write_text(template)
    for path in target.rglob('*'):
        if path.is_file():require(exact_secret not in path.read_bytes(),'Exact configured secret match; publication refused')
    (target/'privacy_check.json').write_text(json.dumps({'exact_configured_credential_bytes_scanned':True,'credential_bytes_exposed':False,'matches':0,
        'authorization_headers_omitted_in_preserved_requests':True,'personal_credit_balance_files_included':any('credit' in f['original_filename'].lower() for f in operational),'new_model_calls':0},indent=2)+'\n')
    manifest={'kind':'First four-arm saved evaluation of two source-grounded original questions',
        'created_utc':datetime.now(timezone.utc).isoformat(),'additional_n':2,'method_items':8,'new_unique_core_ids':2,
        'planned_first_calls_without_transport_retry':10,'bundle_manifest_sha256':args.bundle_manifest_sha256,
        'protocol_sha256':args.protocol_sha256,'scope_sha256':sha(auth/'scope.json'),'human_expert_validation_n':0,
        'old_scores_transferred':False,'new_api_calls_by_packager':0,'baseline_public_original_n':495,
        'registered_union_n':497,'registered_pending_n':63,'cohort_ids':sorted(IDS),
        'registration_state_note':'Counts identify the fixed authorized evaluation scope, not independently observed public publication.',
        'guard_scheduler_source_sha256':provenance['source_sha256'],'guard_scheduler_destination_sha256':provenance['destination_sha256'],
        'guard_scheduler_adaptation_sha256':sha(args.guard_adaptation),'all_actual_response_attempts_and_failures_preserved':True,
        'generation_adapter_lineage':'Prior registered runtime including declared sequence compatibility; no new method or source enrichment',
        'operational_provenance_files':operational,
        'files':{p.relative_to(target).as_posix():sha(p) for p in sorted(target.rglob('*')) if p.is_file()}}
    meta={k:v for k,v in manifest.items() if k!='files'}
    payload={k:v for k,v in manifest['files'].items() if k!=verifier_rel}
    generated=template.replace('__EXPECTED_METADATA_SHA256__',hashlib.sha256(canonical(meta).encode()).hexdigest()).replace('__EXPECTED_PAYLOAD_MAP_SHA256__',hashlib.sha256(canonical(payload).encode()).hexdigest()).replace('__EXPECTED_BUNDLE_MANIFEST_SHA256__',args.bundle_manifest_sha256)
    require('__EXPECTED_' not in generated,'Unfilled final verifier commitment')
    (target/verifier_rel).write_text(generated)
    manifest['files'][verifier_rel]=sha(target/verifier_rel)
    (target/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'PACKAGED_REQUIRE_ACTUAL_OFFLINE_REPLAY','files':len(manifest['files']),
                      'manifest_sha256':sha(target/'manifest.json'),'verifier_sha256':sha(target/verifier_rel),
                      'target':str(target),'new_model_calls':0,'new_public_writes':0}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['bundle','run','target','auth','project-root','runtime','guard','guard-adaptation','sql-manifest-root']:
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--protocol-sha256',required=True)
    p.add_argument('--bundle-manifest-sha256',required=True)
    p.add_argument('--operational-proof',type=Path,action='append',required=True)
    main(p.parse_args())
