"""ROOT-only AUTH48 registration and preparation; this module performs no work on import."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
if sys.flags.optimize:
    raise SystemExit('Enabled checks required')
PREP = Path(__file__).absolute().parent
Q = next(p for p in PREP.parents if p.name == 'resumed_deep_verification')
R = next(p for p in PREP.parents if (p / 'CLAUDE.md').is_file())
B = next(p for p in PREP.parents if p.name == 'overnight_reaudit')
P = R.parent / 'spectra-public/spec-trace'
OLD = B / 'authorized_incremental47_OpenRouter_release'
NEW = B / 'authorized_incremental48_OpenRouter_release'
EXPECTED = {'RAN1_P4_CQ2-3': '032c4939f0b9e2640d29f874fbf53b725533a261545e12400cce6e9f9abeb541'}
NINE = ['add_loader_identity.py','analyze_predictions.py','build_frozen_sqlite.py','credit_floor_guard.py',
        'execute_ready.py','openrouter_client.py','retrieval_adapter.py','run_evaluation.py','structured_adapter.py']

def require(ok, why):
    if not ok:
        raise ValueError(why)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path):
    return json.loads(path.read_bytes())

def pin(path):
    return {'path': str(path.absolute()), 'bytes': path.stat().st_size, 'sha256': sha(path)}

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def replace_once(text, before, after):
    require(text.count(before) == 1, 'Exact adaptation source:' + before[:100])
    return text.replace(before, after)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--proof', type=Path, required=True)
    parser.add_argument('--expected-baseline', type=int, required=True)
    parser.add_argument('--credit-observation', type=Path, required=True)
    args = parser.parse_args()
    bundle, proof_path = args.bundle.absolute(), args.proof.absolute()
    require(not NEW.exists(), 'Preserve previous registration')
    require(subprocess.check_output(['git','-C',str(P),'status','--porcelain']) == b'', 'Clean public baseline')
    commit = subprocess.check_output(['git','-C',str(P),'rev-parse','HEAD'], text=True).strip()
    proof = load(proof_path)
    if 'stdout' in proof:
        require(proof.get('exit_code', proof.get('returncode')) == 0, 'Actual offline verifier exited0')
        proof = json.loads(proof['stdout'])
    require(proof['status'] == 'PASS' and proof['candidate_n'] == proof['local_validated_n'] == 1, 'Actual offline local pass')
    require({row['id']: row['repair_sha256'] for row in proof['items']} == EXPECTED, 'Exact reviewed candidate')
    tasks = [json.loads(line) for line in (bundle / 'tasks.jsonl').read_bytes().splitlines() if line.strip()]
    require({row['id']: row['repair_sha256'] for row in tasks} == EXPECTED, 'Exact original-question task')
    require(sha(bundle / 'criteria.json') == 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'Original criteria unchanged')
    credit_path = args.credit_observation.absolute()
    require(credit_path.is_file() and not credit_path.is_symlink(), 'Actual private credit observation')
    require((credit_path.stat().st_mode & 0o777) == 0o600, 'Credit observation private0600')
    credit = load(credit_path)
    require(credit['model']['id'] == 'anthropic/claude-opus-4.8' and credit['new_paid_calls'] == 0, 'Fresh free observation of the unchanged model')
    available = min(Decimal(credit['account_remaining_credit_usd']), Decimal(str(credit['key']['limit_remaining']))) - Decimal('5')
    require(available >= Decimal('1'), 'Account and key USD5 floor plus this cohortUSD1 cap')
    prices = credit['model']['pricing']
    require(max(Decimal(prices[k]) for k in ['prompt','input_cache_read','input_cache_write','input_cache_write_1h']) <= Decimal('.000010')
            and Decimal(prices['completion']) <= Decimal('.000025'), 'Verified prior price guard')
    compatibility = load(PREP / 'explicit_reader_compatibility/preparation_receipt.json')
    plan = load(PREP / 'prospective_runtime_plan.json')
    require(plan['id'] in EXPECTED and plan['repair_sha256'] == EXPECTED[plan['id']], 'Prepared prospective scoring plan')
    for name, info in plan['runtime_extra_files'].items():
        source = PREP / info['prepared_path']
        require(sha(source) == info['sha256'], 'Reviewed prospective scoring bytes:' + name)
    index = load(P / 'release_package/cqs/current_core/index_manifest.json')
    partition = load(P / 'release_package/cqs/core_disposition_audit/partition/summary.json')['partition_counts']
    baseline = index['repaired_n']
    require(baseline == partition['contract_verified'] == args.expected_baseline and 0 < baseline < 560, 'Observed current public baseline')
    NEW.mkdir()
    snapshots = {}
    for name in ['index_manifest.json','all_core_dispositions.jsonl','current_tasks.jsonl']:
        source = P / 'release_package/cqs/current_core' / name
        destination = NEW / 'baseline_source/release_package/cqs/current_core' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        snapshots[name] = pin(destination)
    inputs, cases = [], []
    for task in tasks:
        ident = task['id']
        seal = PREP.parent / 'ROOT_final_disposition.json'
        require(load(seal)['decision'] == 'pass_local' and load(seal)['repair_sha256'] == task['repair_sha256'], 'Actual ROOT seal')
        paths = {'definition': bundle / 'definitions' / (ident + '.json'),
                 **{name: bundle / 'gate_evidence' / ident / (name + '.json') for name in ['primary','secondary']}}
        inputs.append({key: str(value.relative_to(B)) for key, value in paths.items()})
        cases.append({'id': ident, 'repair_sha256': task['repair_sha256'], 'definition': pin(paths['definition']),
            'required_fields': task['required_fields'], 'gate_files': {**{key: pin(value) for key, value in paths.items() if key != 'definition'},
                'ROOT_final_disposition': pin(seal), 'actual_offline_replay': pin(proof_path)},
            'prospective_item_scoring_plan': pin(PREP / 'prospective_runtime_plan.json')})
    write(NEW / 'admission_inputs.json', inputs)
    write(NEW / 'additional_budget_authorization.json', {'user_instruction': 'Publish verified finalized decisions with economical unchanged first responses and account/key USD5 floor.',
        'prior_authorization': pin(OLD / 'additional_budget_authorization.json'), 'fresh_credit_and_price_observation': pin(credit_path),
        'observation_is_not_a_future_live_balance': True, 'fresh_guard_before_each_dispatch': True,
        'account_and_key_floor_usd': 5, 'this_cohort_max_budget_usd': 1, 'generation_workers': 1,
        'quality_regeneration_authorized': False, 'new_model_calls': 0})
    target = dict(partition)
    target['contract_verified'] += 1
    target['evidence_pending'] -= 1
    scope = {'authorization_utc': datetime.now(timezone.utc).isoformat(), 'authorized_original_frozen_repair_n': 1,
        'baseline_public_pass_n': baseline, 'authorized_target_original_frozen_union_n': baseline + 1,
        'authorized_target_pending_n': 560 - baseline - 1,
        'legacy_pending_alias_meaning': 'All original560 outside verified union, including clarification/unsupported; distinct from evidence_pending.',
        'baseline_public_commit_observed': commit, 'baseline_public_snapshot_pins': snapshots,
        'target_partition_if_published': target, 'cases': cases, 'offline_bundle_before_calls': pin(bundle / 'manifest.json'),
        'actual_offline_verification': proof, 'source_registry_pins': {'admission_inputs.json': sha(NEW / 'admission_inputs.json')},
        'authorization_evidence_sha256': sha(NEW / 'additional_budget_authorization.json'),
        'saved_exact_native_captures_reused': 2, 'new_native_executions_by_registration': 0,
        'generation_workers': 1, 'account_and_key_floor_USD': 5, 'cohort_max_budget_USD': 1,
        'quality_regeneration_authorized': False, 'selection_used_phase_predictions': False,
        'new_API_calls_started': False, 'published': False, 'human_expert_validation_n': 0,
        'prospective_item_scoring_plan': pin(PREP / 'prospective_runtime_plan.json')}
    write(NEW / 'scope.json', scope)
    src, dst = OLD / 'evaluation/runtime', NEW / 'evaluation/runtime'
    dst.mkdir(parents=True)
    copies = []
    for name in NINE:
        require(sha(src / name) == compatibility['original_nine_runtime_files'][name]['sha256'], 'Prior scientific runtime unchanged:' + name)
        shutil.copyfile(src / name, dst / name)
        require((src / name).read_bytes() == (dst / name).read_bytes(), 'Byte-exact runtime copy')
        copies.append({'file': name, 'source': pin(src / name), 'copy': pin(dst / name)})
    shutil.copyfile(src / 'early_execution_reader_copy_receipt.json', dst / 'early_execution_reader_copy_receipt.json')
    shutil.copytree(src / 'sql_interface_v2', dst / 'sql_interface_v2')
    (dst / 'relational').mkdir()
    for path in (src / 'relational').iterdir():
        require(path.is_file() and not path.is_symlink(), 'Actual relational files')
        os.link(path, dst / 'relational' / path.name)
    for name, info in plan['runtime_extra_files'].items():
        shutil.copyfile(PREP / info['prepared_path'], dst / name)
    old_scope_sha, scope_sha = sha(OLD / 'scope.json'), sha(NEW / 'scope.json')
    source_wrapper = src / 'authorized_incremental47_evaluation.py'
    wrapper = source_wrapper.read_text()
    require(old_scope_sha in wrapper, 'Actual prior scope pin')
    wrapper = wrapper.replace(old_scope_sha, scope_sha).replace('authorized_incremental47', 'authorized_incremental48').replace('FROZEN_AUTHORIZED_INCREMENTAL47', 'FROZEN_AUTHORIZED_INCREMENTAL48')
    wrapper = replace_once(wrapper, "'baseline_public_original_n':517,'this_phase_original_union_n':518,'this_phase_pending_n':42",
        f"'baseline_public_original_n':{baseline},'this_phase_original_union_n':{baseline + 1},'this_phase_pending_n':{560 - baseline - 1}")
    support = (PREP / 'AUTH48_prospective_scoring_pin_support.py').read_text()
    require('RUNTIME_PINS_PLACEHOLDER' in support and 'BUNDLE_PINS_PLACEHOLDER' in support, 'Explicit prospective pin template')
    runtime_pins = {name: info['sha256'] for name, info in plan['runtime_extra_files'].items()}
    bundle_pins = {**{name: info['sha256'] for name, info in compatibility['original_public_seven_files'].items()},
        **{name: runtime_pins[name] for name in ['score_predictions_joint_sample.py','item_scorer_dispatch.py','one_record_sample_scorer.py']}}
    support = support.replace('RUNTIME_PINS_PLACEHOLDER', repr(runtime_pins)).replace('BUNDLE_PINS_PLACEHOLDER', repr(bundle_pins))
    wrapper = replace_once(wrapper, 'RESERVE_BYTES = 26 * 1024**3\n', 'RESERVE_BYTES = 26 * 1024**3\n\n' + support + '\n')
    wrapper = replace_once(wrapper, '    scope, tasks = immutable_scope(bundle)\n', '    scope, tasks = immutable_scope(bundle)\n    item_scoring = prospective_item_scoring_pins(bundle)\n')
    wrapper = replace_once(wrapper, "    protocol['budget_guard_usd'] = budget", "    protocol['prospective_item_scoring'] = item_scoring\n    protocol['code_pins'].update(item_scoring['runtime_file_pins'])\n    protocol['budget_guard_usd'] = budget")
    wrapper = replace_once(wrapper, '    protocol = runtime.verify_pins(bundle,run)\n', "    protocol = runtime.verify_pins(bundle,run)\n    if protocol['prospective_item_scoring'] != prospective_item_scoring_pins(bundle):\n        raise ValueError('Prospective current-item scoring pins changed')\n")
    wrapper = replace_once(wrapper, '            import analyze_predictions\n', '            import analyze_predictions_joint_sample as analyze_predictions\n')
    compile(wrapper, 'authorized_incremental48_evaluation.py', 'exec')
    (dst / 'authorized_incremental48_evaluation.py').write_text(wrapper)
    (dst / 'AUTH48_wrapper_scoring_adaptation.diff').write_text(''.join(difflib.unified_diff(source_wrapper.read_text().splitlines(True), wrapper.splitlines(True), fromfile='AUTH47_wrapper', tofile='AUTH48_wrapper')))
    write(dst / 'runtime_source_copy_receipt.json', {'runtime_files': copies, 'source_wrapper': pin(source_wrapper),
        'new_wrapper_sha256': sha(dst / 'authorized_incremental48_evaluation.py'), 'scientific_adapters_byte_exact': True,
        'prompts_model_tokens_parser_retry_unchanged': True, 'shared_scorer_files_byte_exact': True,
        'prospective_current_item_joint_scoring_extension': pin(PREP / 'prospective_runtime_plan.json'),
        'scoring_extension_frozen_before_first_prediction': True, 'historical_scores_changed': False,
        'new_API_calls': 0})
    guards = NEW / 'operational_guards'
    guards.mkdir()
    old_bundle = str((Q / 'AUTH47_preparation/portable_addition/release_package/cqs/original_core_overnight_repairs47').absolute())
    adaptations = []
    names = ['fresh_windows_memory.py','run_native_with_fresh_windows_probe.py','AUTH47_root_guarded_native_execution.py',
        'run_root_guarded_evaluation_stage_persistent_cim.py','run_root_guarded_native_and_assembly_persistent_cim.py',
        'run_root_guarded_freeze_retry_v2.py','run_fresh_memory_coordinator_v2.py','run_root_guarded_explicit_optional_analysis.py']
    for name in names:
        source = OLD / 'operational_guards' / name
        before = source.read_text()
        substitutions = [(old_scope_sha, scope_sha), (old_bundle, str(bundle)),
            ('authorized_incremental47','authorized_incremental48'), ('AUTH47','AUTH48'),
            ('execute_RAN4','execute_RAN1'), ("choices=['RAN4']", "choices=['RAN1']"),
            ('run_root_guarded_explicit_optional_analysis.py','run_root_guarded_explicit_joint_analysis.py'),
            ('AUTH48_explicit_optional_analysis_runner.py','AUTH48_explicit_joint_analysis_runner.py'),
            ('actual_guarded_persistent_cim_explicit_optional_','actual_guarded_persistent_cim_explicit_joint_')]
        text = before
        applied = []
        for old, new in substitutions:
            if old in text:
                text = text.replace(old, new)
                applied.append((old, new))
        # Shield the relocated bundle path while reversing the broader AUTH48
        # token substitution; the forward guard bytes are unchanged.
        reverse_path_marker = '__RELOCATED_BUNDLE_REVERSE_ONLY__'
        require(reverse_path_marker not in text, 'Reserved reverse-check marker')
        reversed_text = text.replace(str(bundle), reverse_path_marker)
        for old, new in reversed(applied):
            if old != old_bundle:
                reversed_text = reversed_text.replace(new, old)
        reversed_text = reversed_text.replace(reverse_path_marker, old_bundle)
        require(reversed_text == before, 'Guard reverse-equivalence:' + name)
        target_name = name.replace('AUTH47','AUTH48').replace('explicit_optional','explicit_joint')
        target_path = guards / target_name
        compile(text, str(target_path), 'exec')
        target_path.write_text(text)
        adaptations.append({'source': pin(source), 'copy': pin(target_path), 'reverse_equivalence': True, 'allowed_substitutions': applied})
    receipt = {'status':'REGISTERED_NOT_FROZEN_NO_API_CALLS','scope_sha256':scope_sha,
        'bundle_manifest_sha256':sha(bundle/'manifest.json'),'baseline_public_commit':commit,
        'scope_n':1,'method_items_n':4,'runtime_files_byte_exact':9,'guard_adaptations':adaptations,
        'dual_host_26GiB_admission_16GiB_continuous_unchanged':True,
        'owned_2GiB_1CPU_readonly_cleanup_unchanged':True,'planned_first_calls':5,
        'budget_usd':1,'account_and_key_floor_usd':5,'prospective_joint_reader_no_sys_modules_monkeypatch':True,
        'prospective_scoring_pinned_in_freeze_protocol':True,'original_question_and_parser_unchanged':True,
        'new_API_calls':0,'public_mutations':0}
    write(PREP / 'actual_registration_and_runtime_preparation.json', receipt)
    print(json.dumps({'status':'REGISTERED_NOT_FROZEN','scope_sha256':scope_sha,'baseline_public_commit':commit,'new_API_calls':0}))

if __name__ == '__main__':
    main()
