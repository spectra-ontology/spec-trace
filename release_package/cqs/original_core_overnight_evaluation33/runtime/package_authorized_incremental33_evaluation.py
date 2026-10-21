#!/usr/bin/env python3
"""Package completed AUTH33 N1 outputs only; never start calls or databases."""
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
IDS = {'RAN1_P2_CQ5-5'}
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
    protocol=load(run/'protocol.json');analysis=load(run/'analysis.json');usage=load(run/'usage.json')
    require(analysis['admitted_n']==protocol['admitted_n']==1,'Full N1 analysis required')
    require(set(protocol['cohort_ids'])==IDS,'Exact one-ID cohort required')
    extension=protocol['authorized_incremental33_extension']
    require(extension['scope_sha256']==sha(auth/'scope.json'),'AUTH33 exact scope differs')
    require(extension['scope_n']==1 and extension['method_items_n']==4 and extension['planned_calls_without_transport_retry']==5,'N1/4/5 protocol mismatch')
    generation=load(run/'generation_complete.json')
    require(generation['completed_method_items']==generation['required']==4,'All four method outcomes required')
    require(all(analysis['tables'][m]['overall']['n']==1 for m in METHODS),'All methods must retain the original ID')
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
    omitted_private=[]
    for path in sorted(run.rglob('*')):
        no_link(path)
        if path.is_dir():continue
        require(path.is_file(),'Nonregular run entry refused')
        require('__pycache__' not in path.parts and path.suffix not in {'.sqlite','.db','.env','.pyc'} and path.name not in {'.env','credentials.json'},'Unnecessary/secret/large runtime input in run tree')
        relative=path.relative_to(run).as_posix()
        if relative == 'credit_floor_guard.jsonl':
            omitted_private.append({'original_relative_path':relative,'sha256':sha(path),'bytes':path.stat().st_size,
                                    'reason':'Private account/key balance observations; actual per-call cost remains in raw responses and usage.'})
            continue
        copy(path,'current/'+relative)
    require(len(omitted_private)==1,'One actual private credit-floor ledger must be hash-preserved, not shipped')
    (target/'authorization').mkdir(exist_ok=True)
    (target/'authorization/private_credit_floor_log_omission.json').write_text(json.dumps({
        'private_account_observations_shipped':False,'omitted_files':omitted_private,
        'scientific_calls_or_responses_omitted':False,'public_usage_and_raw_attempts_preserved':True},indent=2)+'\n')
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
    copy(args.guard,'runtime/AUTH33_root_guarded_native_execution_v1.py',provenance['destination_sha256'])
    original_guard=no_link(project_root/provenance['source_path'])
    copy(original_guard,'runtime/original_guard_scheduler.py',provenance['source_sha256'])
    copy(args.guard_adaptation,'runtime/AUTH33_root_guarded_native_execution_v1.adaptation.json')
    for name in ['verify_incremental33_exact_prompts_and_parsers.py','package_authorized_incremental33_evaluation.py']:
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
        require(source.name != 'credit_floor_guard.jsonl','Private account/key balance ledger is not a public operational proof')
        copy(source,rel)
        operational.append({'file':rel,'sha256':sha(source),'bytes':source.stat().st_size,
                            'original_filename':source.name})
    (target/'operational_provenance/index.json').write_text(json.dumps({'kind':'Explicit actual operational receipts, including failures; no replacement or rerun',
                                                                    'files':operational,'additional_public_admissions_by_packager':0},indent=2)+'\n')
    table=(run/'performance_table.md').read_text()
    (target/'README.md').write_text('# PUSCH repetition decisions: separate first evaluation\n\n'
        'This N1 cohort evaluates the original PUSCH-repetition decision question through the '
        'ontology-linked Agreement and Meeting records. The fixed reference preserves 532 joined '
        'rows and all 16 records eligible at the original latest-meeting boundary. Source replay '
        'checks their own decision contents and 83 operative source bindings. Two separate AI '
        'reviews and 15 typed scorer controls precede this first evaluation.\n\n'
        +table+'\n\n'
        'Five first logical requests produced five complete successful HTTP responses in five '
        'attempts. Returned usage records total actual cost $'+str(usage['known_actual_cost_usd'])+
        '; all actual attempt costs are known. The $'+str(usage['budget_guard_usd'])+
        ' operational budget and reservations are separate from actual spend.\n\n'
        'All five call stages and four method outcomes, including errors and abstentions, are '
        'preserved. The same model, prompts, token settings, parsers, scorer and failure gates '
        'use `anthropic/claude-opus-4.8` through Anthropic, with no quality rerolls or prior-score '
        'transfers. Structured methods receive the original question, public typed contract and '
        'structural schema; retrieval methods receive their saved retrieved passages. Source '
        'proofs, gold and reviews are validation inputs. Raw requests, responses, execution '
        'statuses and actual usage are included. Human/expert validation remains zero.\n\n'
        'Offline replay uses no API or database calls:\n\n'
        '    python3 -B -I runtime/verify_authorized_incremental33_evaluation.py --evidence . --bundle ../original_core_overnight_repairs33\n\n'
        'The registered counts identify the fixed 502-to-503 scope and 57 legacy nonadmitted '
        'questions; the live all-560 taxonomy is in the disposition register. Private account/key '
        'balances are omitted with hash commitments; every scientific attempt remains included.\n')
    # Root-owned exact configured-secret publication scan; this helper is not executed by preparation agents.
    sys.path.insert(0,str(project_root/'scripts/common/common'))
    import credentials
    exact_secret=credentials.secret('OPENROUTER_API_KEY').encode()
    require(bool(exact_secret),'Configured credential unavailable for exact scan')
    # Verifier source is generated before the scan so it too is checked.
    template=(OUT/'verify_authorized_incremental33_evaluation.template.py').read_text()
    verifier_rel='runtime/verify_authorized_incremental33_evaluation.py'
    (target/verifier_rel).write_text(template)
    for path in target.rglob('*'):
        if path.is_file():require(exact_secret not in path.read_bytes(),'Exact configured secret match; publication refused')
    (target/'privacy_check.json').write_text(json.dumps({'exact_configured_credential_bytes_scanned':True,'credential_bytes_exposed':False,'matches':0,
        'authorization_headers_omitted_in_preserved_requests':True,'personal_credit_balance_files_included':False,'private_credit_floor_log_omission_sha256':sha(target/'authorization/private_credit_floor_log_omission.json'),'new_model_calls':0},indent=2)+'\n')
    manifest={'kind':'First four-arm saved evaluation of one source-grounded original question',
        'created_utc':datetime.now(timezone.utc).isoformat(),'additional_n':1,'method_items':4,'new_unique_core_ids':1,
        'planned_first_calls_without_transport_retry':5,'actual_response_attempts':5,'received_complete_response_n':5,'known_actual_cost_usd':usage['known_actual_cost_usd'],'unknown_cost_attempts':usage['unknown_cost_attempts'],'all_actual_costs_known':usage['all_actual_costs_known'],'cost_accounting':'All five actual attempt costs are known from returned usage; operational reservations are separate.','bundle_manifest_sha256':args.bundle_manifest_sha256,
        'protocol_sha256':args.protocol_sha256,'scope_sha256':sha(auth/'scope.json'),'human_expert_validation_n':0,
        'old_scores_transferred':False,'new_api_calls_by_packager':0,'baseline_public_original_n':502,
        'registered_union_n':503,'registered_pending_n':57,'cohort_ids':sorted(IDS),
        'registration_state_note':'Counts identify the fixed authorized evaluation scope, not independently observed public publication.',
        'guard_scheduler_source_sha256':provenance['source_sha256'],'guard_scheduler_destination_sha256':provenance['destination_sha256'],
        'guard_scheduler_adaptation_sha256':sha(args.guard_adaptation),'all_actual_response_attempts_and_failures_preserved':True,
        'generation_adapter_lineage':'Scientific adapters unchanged; prior sequence compatibility retained; serial worker and separately pinned operational credit-floor call wrapper',
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
