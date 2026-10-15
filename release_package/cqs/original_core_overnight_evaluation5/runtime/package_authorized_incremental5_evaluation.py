#!/usr/bin/env python3
"""Spec: package completed AUTH5 four-arm outputs byte exactly.
Ontology: original CQ038 full3942 pool, two SQL witnesses and unchanged kernel.
Cycle: authorized supplemental evaluation5; root executes separately.
배경: preserve every first response, failure, prompt and source guard.
사용: --bundle ... --run ... --target ... (new immutable version only).
LLM 호출: none; offline copy and credential absence scan only.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
B = OUT.parent
AUTH = B / 'authorized_incremental5_OpenRouter_release'
RUNTIME = AUTH / 'evaluation/runtime'
ROOT = Path('/home/sihyeon/workspace/spectra')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p):
    return json.loads(p.read_text())


def main(bundle, run, target):
    assert not target.exists(), 'preserve previous package, choose new version'
    assert (run / 'analysis.json').is_file(), 'all1/all4 actual execution and analysis required'
    protocol = load(run / 'protocol.json')
    analysis = load(run / 'analysis.json')
    assert analysis['admitted_n'] == protocol['admitted_n'] == 1
    assert protocol['authorized_incremental5_extension']['scope_sha256'] == sha(AUTH / 'scope.json')
    generation = load(run / 'generation_complete.json')
    assert generation['completed_method_items'] == generation['required'] == 4
    for method in ('text2cypher', 'text2sql', 'single_retrieval', 'iterative_retrieval'):
        assert analysis['tables'][method]['overall']['n'] == 1
    target.mkdir(parents=True)

    def copy(source, relative, expected=None):
        assert not source.is_symlink(), ('do not publish symlink', source)
        actual = sha(source)
        assert expected is None or actual == expected, ('frozen bytes changed', source)
        destination = target / relative
        assert destination.resolve().is_relative_to(target.resolve())
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    for path in sorted(run.rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts:
            continue
        assert path.suffix not in {'.sqlite', '.db', '.env'} and path.name not in {'.env', 'credentials.json'}
        copy(path, 'current/' + path.relative_to(run).as_posix())
    for name, expected in protocol['code_pins'].items():
        copy(RUNTIME / name, 'runtime/' + name, expected)
    copy(RUNTIME / 'runtime_source_copy_receipt.json', 'runtime/runtime_source_copy_receipt.json',
         protocol['authorized_incremental5_extension']['source_copy_receipt_sha256'])
    early_path = RUNTIME / 'early_execution_reader_copy_receipt.json'
    if early_path.exists():
        early = load(early_path)
        assert early['source_sha256'] == early['copy_sha256']
        assert early['generation_and_adapter_code_modified'] is False
        assert early['execution_scheduling_only'] is True
        copy(RUNTIME / 'execute_ready.py', 'runtime/execute_ready.py', early['copy_sha256'])
        copy(early_path, 'runtime/early_execution_reader_copy_receipt.json')
        copy(B / 'root_evidence/AUTH5_root_guarded_native_execution.py', 'runtime/AUTH5_root_guarded_native_execution.py')
        copy(B / 'root_evidence/AUTH5_root_guarded_native_execution.adaptation.json', 'runtime/AUTH5_root_guarded_native_execution.adaptation.json')
    copy(OUT / 'verify_authorized_incremental5_evaluation_v2.py', 'runtime/verify_authorized_incremental5_evaluation_v2.py')
    copy(Path(__file__), 'runtime/package_authorized_incremental5_evaluation.py')
    for wg, item in protocol['sql_manifests'].items():
        copy(RUNTIME / 'relational' / (wg + '.manifest.json'), 'source_manifests/' + wg + '.manifest.json', item['sha256'])
    for name in ('scope.json', 'admission_inputs.json', 'additional_budget_authorization.json'):
        copy(AUTH / name, 'authorization/' + name)
    evidence_files = {
        'complete_actual_question_gate_v5.json': Path('/home/sihyeon/workspace/spectra/logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/RAN1/CQ038_original_recorded_Section_reference_and_available_CR_field_scope/complete_actual_question_gate_v5/manifest.json'),
        'root_native_and_two_SQL_agreement.json': Path('/home/sihyeon/workspace/spectra/logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/root_evidence/CQ038_root_actual_native_full3942_and_independent_inverse_SQL_agreement_v5.json'),
        'root_inverse_SQL_preregistered_plan.json': Path('/home/sihyeon/workspace/spectra/logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/root_evidence/CQ038_root_independent_fullpool_inverse_SQL_v1/preregistered_plan.json'),
        'root_inverse_SQL_receipt.json': Path('/home/sihyeon/workspace/spectra/logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/root_evidence/CQ038_root_independent_fullpool_inverse_SQL_v1/receipt.json'),
        'root_inverse_SQL_full3942.jsonl': Path('/home/sihyeon/workspace/spectra/logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/root_evidence/CQ038_root_independent_fullpool_inverse_SQL_v1/all3942_independent_fullpool_records.jsonl'),
        'proposer_independent_SQL_full3942.jsonl': Path('/home/sihyeon/workspace/spectra/logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/RAN1/CQ038_original_recorded_Section_reference_and_available_CR_field_scope/full_SQL_rank_pool_and_controls_v5/RAN1_P3_CQ038_full_uncapped_SQL_records.jsonl'),
        'proposer_full_SQL_and_12_controls_manifest.json': Path('/home/sihyeon/workspace/spectra/logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/RAN1/CQ038_original_recorded_Section_reference_and_available_CR_field_scope/full_SQL_rank_pool_and_controls_v5/manifest.json'),
        'actual_typed_top10_and_CR_count_controls.json': Path('/home/sihyeon/workspace/spectra/logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/RAN1/CQ038_original_recorded_Section_reference_and_available_CR_field_scope/full_SQL_rank_pool_and_controls_v5/actual_typed_top10_and_CR_count_controls.json'),
        'actual12_controls_replayed_against_complete_native_pool.json': Path('/home/sihyeon/workspace/spectra/logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/RAN1/CQ038_original_recorded_Section_reference_and_available_CR_field_scope/complete_actual_question_gate_v5/actual12_controls_replayed_against_complete_native_pool.json'),
        'integration_requested_field_controls.json': Path('/home/sihyeon/workspace/spectra/logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/RAN1/CQ038_original_recorded_Section_reference_and_available_CR_field_scope/complete_actual_question_gate_v5/integration_requested_field_controls.json'),
        'exact_original_source_ancillary_relocation.json': Path('/home/sihyeon/workspace/spectra/logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/RAN1/CQ038_original_recorded_Section_reference_and_available_CR_field_scope/complete_actual_question_gate_v5/exact_original_RAN1_design_ancillary_source_relocation.json'),
        'exact_primary_review_v5.json': Path('/home/sihyeon/workspace/spectra/logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/RAN1/CQ038_original_recorded_Section_reference_and_available_CR_field_scope/CQ038_exact_original_pure_Cypher_ordinal_reference_count_primary_v5.json'),
        'exact_secondary_review_v5.json': Path('/home/sihyeon/workspace/spectra/logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit/RAN2_RAN5/crossreview_RAN1_P3_CQ038_recorded_reference_and_available_CR_field_scope_pure_v5.json'),
    }
    expected_evidence = {'complete_actual_question_gate_v5.json': '47deac34355f08b9ba6e9817d9188dba212437da26cc15e69207fc57af29f209', 'root_native_and_two_SQL_agreement.json': '2cbf0ffcd8f81255f2196d30287e04fe592029ab2817fd4a340601fec3f139bf', 'root_inverse_SQL_preregistered_plan.json': '97ffd0e74d2b7c466d52378dea4118a05b398b3019fa735c3412f20d88f0a9aa', 'root_inverse_SQL_receipt.json': 'd2c26cd25fae607581fe65056df97d4f1f1ec2196e3a05ad267a01148357990b', 'root_inverse_SQL_full3942.jsonl': 'd0957f6490e4e26a9cb17f35cda570f505ac8099491dc9e87bae5bab76366794', 'proposer_independent_SQL_full3942.jsonl': 'fc74eb0ae4c1fda8c4e729620a1de83fe132383f7476bc75d5b56b8f3451d459', 'proposer_full_SQL_and_12_controls_manifest.json': '6ea4071fdbef56cbd9a9cf6045d7849d2752f42f4a9fdb7eacbebdc944a0b071', 'actual_typed_top10_and_CR_count_controls.json': 'edfdb13f0ea01c74da4c0765d42c609eeee2f621f1487032e6b709e4c413a5b2', 'actual12_controls_replayed_against_complete_native_pool.json': '9144ced1b2b8af2c232891562aaa887668e7c83c206a67698eb4a9f7950f03e4', 'integration_requested_field_controls.json': '2148f6fd2d949c0398560356a5361205b67e6f04e15e966c46fa3daca6141cb8', 'exact_original_source_ancillary_relocation.json': '21003514e10c8f0f6408d2e0d911beec2be3cd9996db7a888660cb735531d54b', 'exact_primary_review_v5.json': 'c48bc1fff3de45bee91dc5b889cb829cddbf1412f7e9f514b948ef656df6f510', 'exact_secondary_review_v5.json': 'a24447fa39563172468a83ab7204ad328944d9d77e910b463aec1a337206cd34'}
    for name, source in evidence_files.items():
        copy(source, 'gate_evidence/' + name, expected_evidence[name])
    copy(OUT / 'AUTH5_offline_export_helper_adaptation.json', 'runtime/AUTH5_offline_export_helper_adaptation.json')
    sys.path.insert(0, str(ROOT / 'scripts/common/common'))
    import credentials
    exact_secret = credentials.secret('OPENROUTER_API_KEY').encode()
    assert exact_secret, 'configured credential unavailable for exact publication scan'
    for path in target.rglob('*'):
        if path.is_file():
            assert exact_secret not in path.read_bytes(), 'credential match: prevent publication'
    privacy = {'exact_configured_credential_bytes_scanned': True, 'credential_bytes_exposed': False,
        'matches': 0, 'authorization_headers_omitted_in_preserved_requests': True,
        'personal_credit_balance_files_included': False, 'new_model_calls': 0}
    (target / 'privacy_check.json').write_text(json.dumps(privacy, indent=2) + '\n')
    table = (run / 'performance_table.md').read_text()
    (target / 'README.md').write_text(
        '# Additional original question: fresh four-method evaluation\n\n'
        'The exact one question and contracts were fixed before these predictions. This separate '
        'cohort adds to the previously published 448 questions, yielding 449/560 original-question contracts '
        'and 111 pending in its registered snapshot. Later admissions and earlier model results '
        'remain separate. No historical scores transfer.\n\n' + table + '\n'
        'The ID in every method remains in the denominator, including parsing errors, query failures, '
        'empty answers and abstentions. The pinned model is Anthropic Claude Opus4.8 through '
        'OpenRouter, with no model/provider fallback or answer-quality retry. An identical transport '
        'retry is retained only when the predeclared transport policy permits it. Raw request '
        'payloads, every retained response attempt, usage, model outputs, execution artifacts, '
        'failure gates, strict scores and paired analysis are supplied. Authorization headers '
        'and configured credential bytes are absent.\n\n'
        'Text2Cypher receives the frozen graph schema, and Text2SQL receives complete value-free '
        'physical SQLite DDL. Single and two-round retrieval retain the earlier bounded lexical '
        'retrieval protocol. No common supplemental source was supplied. Complete graph/text '
        'archive-cutoff equality and representativeness for all560 original questions are not '
        'established. These method differences and one model prohibit claims of a causal advantage '
        'of graph storage. Two nonblind AI semantic judgments are development diagnosis; human '
        'and independent expert validation remain0.\n\n'
        'Offline replay uses no API or database execution:\n\n'
        '```sh\npython3 -B -S runtime/verify_authorized_incremental5_evaluation_v2.py --evidence . '
        '--bundle ../original_core_overnight_repairs5 --out /tmp/authorized_incremental5-replay.json\n```\n\n'
        'The eight registered evaluation runtime programs are byte-identical to their pre-call '
        'pins. Separate execution scheduling, packaging and replay helpers retain their own '
        'source receipts and package hashes. Original local helper paths are preserved as '
        'provenance. Fresh live execution additionally '
        'requires restored pinned graphs, relational projections, retrieval corpus and credentials; '
        'the supplied command verifies saved outputs and strict scoring only. Local packaging, '
        'public push and fresh anonymous download verification are separate states.\n')
    manifest = {'kind': 'Fresh complete four-arm evaluation of immutable supplemental one original question',
        'created_utc': datetime.now(timezone.utc).isoformat(), 'additional_n': 1, 'method_items': 4,
        'new_unique_core_ids': 1, 'bundle_manifest_sha256': sha(bundle / 'manifest.json'),
        'protocol_sha256': sha(run / 'protocol.json'), 'scope_sha256': sha(AUTH / 'scope.json'),
        'human_expert_validation_n': 0, 'old_scores_transferred': False, 'new_api_calls_by_packager': 0,
        'files': {p.relative_to(target).as_posix(): sha(p) for p in sorted(target.rglob('*')) if p.is_file()}}
    (target / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': 'PACKAGED_REQUIRE_OFFLINE_REPLAY', 'files': len(manifest['files']),
        'manifest_sha256': sha(target / 'manifest.json'), 'target': str(target)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('bundle', 'run', 'target'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    main(args.bundle.resolve(), args.run.resolve(), args.target.resolve())
