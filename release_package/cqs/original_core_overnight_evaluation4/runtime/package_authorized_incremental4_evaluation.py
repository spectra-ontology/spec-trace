#!/usr/bin/env python3
"""Package completed authorized_incremental4 outputs byte exactly, never initiate calls."""
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
AUTH = B / 'authorized_incremental4_OpenRouter_release'
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
    assert protocol['authorized_incremental4_extension']['scope_sha256'] == sha(AUTH / 'scope.json')
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
         protocol['authorized_incremental4_extension']['source_copy_receipt_sha256'])
    early_path = RUNTIME / 'early_execution_reader_copy_receipt.json'
    if early_path.exists():
        early = load(early_path)
        assert early['source_sha256'] == early['copy_sha256']
        assert early['generation_and_adapter_code_modified'] is False
        assert early['execution_scheduling_only'] is True
        copy(RUNTIME / 'execute_ready.py', 'runtime/execute_ready.py', early['copy_sha256'])
        copy(early_path, 'runtime/early_execution_reader_copy_receipt.json')
        copy(B / 'execute_authorized_incremental4_ready_WG_guarded.py', 'runtime/execute_authorized_incremental4_ready_WG_guarded.py')
    copy(OUT / 'verify_authorized_incremental4_evaluation_v2.py', 'runtime/verify_authorized_incremental4_evaluation_v2.py')
    copy(Path(__file__), 'runtime/package_authorized_incremental4_evaluation.py')
    for wg, item in protocol['sql_manifests'].items():
        copy(RUNTIME / 'relational' / (wg + '.manifest.json'), 'source_manifests/' + wg + '.manifest.json', item['sha256'])
    for name in ('scope.json', 'admission_inputs.json', 'additional_budget_authorization.json'):
        copy(AUTH / name, 'authorization/' + name)
    evidence_files = {
        'root_fresh_original_source_context.json': B / 'root_evidence/RAN3_P1_CQ1-4_full_original_unfiltered_source_context_read_v2.json',
        'root_independent_inverse_SQL_native_agreement.json': B / 'root_evidence/RAN3_P1_CQ1-4_root_independent_inverse_SQL_full_native_agreement_v2.json',
        'actual_full20_controls_and_inverse_SQL.json': OUT / 'RAN3_P1_CQ1-4_recorded_release_context_v3/actual_native_full_inverse_SQL_and_requested_identity_controls.json',
        'root_exact_seven_unit_semantic_review.json': B / 'root_evidence/RAN3_P1_CQ1-4_independent_root_exact_semantic_review.json',
    }
    expected_evidence = {
        'root_fresh_original_source_context.json': '1a6d4684666dc697bc01f122ecfa7a471f9c311b92259cef197017e05ed4e2b2',
        'root_independent_inverse_SQL_native_agreement.json': '006e5f92ea87c9a7d6eebf4e0d89dc8170438bbe2281d9b776ee92b4ef5aef19',
        'actual_full20_controls_and_inverse_SQL.json': '279a2efcdbb80e0e792ce0dabe0d0034d4b87919aa55b3edfea189c8e85dd4ae',
        'root_exact_seven_unit_semantic_review.json': '5d978ce3bea05b9d04d1b3b0551794ae1ac0c9d244d4b82994d8a8a9546de989',
    }
    for name, source in evidence_files.items():
        copy(source, 'gate_evidence/' + name, expected_evidence[name])
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
        'cohort adds to the previously published 447 questions, yielding 448/560 original-question contracts '
        'and 112 pending in its registered snapshot. Later admissions and earlier model results '
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
        '```sh\npython3 -B -S runtime/verify_authorized_incremental4_evaluation_v2.py --evidence . '
        '--bundle ../original_core_overnight_repairs4 --out /tmp/authorized_incremental4-replay.json\n```\n\n'
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
