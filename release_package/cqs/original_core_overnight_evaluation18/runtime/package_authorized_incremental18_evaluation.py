#!/usr/bin/env python3
"""Package completed authorized_incremental18 outputs byte exactly, never initiate calls."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p):
    return json.loads(p.read_text())


def main(bundle, run, target, auth, project_root, protocol_sha256, bundle_manifest_sha256, guard, adaptation):
    AUTH = auth
    RUNTIME = AUTH / 'evaluation/runtime'
    B = AUTH.parent
    ROOT = project_root
    assert run == AUTH / 'evaluation/run'
    assert sha(run / 'protocol.json') == protocol_sha256
    assert sha(bundle / 'manifest.json') == bundle_manifest_sha256 
    assert not target.exists(), 'preserve previous package, choose new version'
    assert (run / 'analysis.json').is_file(), 'all1/all4 actual execution and analysis required'
    protocol = load(run / 'protocol.json')
    analysis = load(run / 'analysis.json')
    assert analysis['admitted_n'] == protocol['admitted_n'] == 1
    assert protocol['authorized_incremental18_extension']['scope_sha256'] == sha(AUTH / 'scope.json')
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
         protocol['authorized_incremental18_extension']['source_copy_receipt_sha256'])
    early_path = RUNTIME / 'early_execution_reader_copy_receipt.json'
    if early_path.exists():
        early = load(early_path)
        assert early['source_sha256'] == early['copy_sha256']
        assert early['generation_and_adapter_code_modified'] is False
        assert early['execution_scheduling_only'] is True
        copy(RUNTIME / 'execute_ready.py', 'runtime/execute_ready.py', early['copy_sha256'])
        copy(early_path, 'runtime/early_execution_reader_copy_receipt.json')
    provenance = load(adaptation)
    copy(guard, 'runtime/AUTH18_root_guarded_native_execution_v1.py', provenance['adapted']['sha256'])
    original_guard = ROOT / provenance['source']['path']
    copy(original_guard, 'runtime/original_guard_scheduler.py', provenance['source']['sha256'])
    previous = set(re.findall(r'authorized_incremental(\d+)_OpenRouter_release', original_guard.read_text()))
    assert len(previous) == 1
    old_increment = previous.pop()
    assert original_guard.read_text().replace('authorized_incremental' + old_increment, 'authorized_incremental18') == guard.read_text()
    assert provenance['replacement_old'] == 'authorized_incremental' + old_increment
    assert provenance['replacement_new'] == 'authorized_incremental18'
    assert provenance['replacement_n'] == original_guard.read_text().count(provenance['replacement_old']) == 7
    copy(adaptation, 'runtime/AUTH18_root_guarded_native_execution_v1.adaptation.json')
    copy(OUT / 'verify_authorized_incremental18_evaluation.py', 'runtime/verify_authorized_incremental18_evaluation.py')
    copy(OUT / 'verify_incremental18_exact_prompts_and_parsers.py', 'runtime/verify_incremental18_exact_prompts_and_parsers.py')
    copy(Path(__file__), 'runtime/package_authorized_incremental18_evaluation.py')
    for wg, item in protocol['sql_manifests'].items():
        copy(RUNTIME / 'relational' / (wg + '.manifest.json'), 'source_manifests/' + wg + '.manifest.json', item['sha256'])
    for name in ('scope.json', 'admission_inputs.json', 'additional_budget_authorization.json'):
        copy(AUTH / name, 'authorization/' + name)
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
        '# One additional original question: fresh four-method evaluation\n\n'
        'The exact one question and contracts were fixed before these predictions. This separate '
        'cohort adds to the previously published 477 questions, yielding 478/560 original-question contracts '
        'and 82 pending in its registered snapshot. Later admissions and earlier model results '
        'remain separate. No historical scores transfer.\n\n' + table + '\n'
        'The ID in every method remains in the denominator, including parsing errors, query failures, '
        'empty answers and abstentions. The pinned model is Anthropic Claude Opus4.8 through '
        'OpenRouter, with no model/provider fallback or answer-quality retry. An identical transport '
        'retry is retained only when the predeclared transport policy permits it. Raw request '
        'payloads, every retained response attempt, usage, model outputs, execution artifacts, '
        'failure gates, strict scores and paired analysis are supplied. Authorization headers '
        'and configured credential bytes are absent.\n\n'
        'Text2Cypher receives the frozen graph schema, and Text2SQL receives complete value-free '
        'physical SQLite DDL. Single and two-round retrieval retain the registered AUTH37 byte-identical bounded lexical '
        'retrieval protocol. No common supplemental source was supplied. Complete graph/text '
        'archive-cutoff equality and representativeness for all560 original questions are not '
        'established. These method differences and one model prohibit claims of a causal advantage '
        'of graph storage. Two nonblind AI semantic judgments are development diagnosis; human '
        'and independent expert validation remain0.\n\n'
        'Offline replay uses no API or database execution:\n\n'
        '```sh\npython3 -B -S runtime/verify_authorized_incremental18_evaluation.py --evidence . '
        '--bundle ../original_core_overnight_repairs18 --out /tmp/authorized_incremental18-replay.json\n```\n\n'
        'The registered generation, adapter and analysis programs are byte-identical to their pre-call '
        'pins. The separately registered one-question wrapper and guarded native scheduler retain '
        'their own source receipts and package hashes. Original local helper paths are preserved as '
        'provenance. Fresh live execution additionally '
        'requires restored pinned graphs, relational projections, retrieval corpus and credentials; '
        'the supplied command verifies saved outputs and strict scoring only. Local packaging, '
        'public push and fresh anonymous download verification are separate states.\n\n'
        'The underlying contract retains the original registered Tdoc scope and the root-approved '
        'literal CR/draftCR/pCR type predicate. Distinct Tdoc identifiers form the count unit. '
        'The exact registered input scope, source membership and alternative interpretations are '
        'preserved in the companion repair bundle. These counts do not establish physical CR '
        'forms, approval, incorporation, or source factuality.\n')
    manifest = {'kind': 'Fresh complete four-arm evaluation of immutable supplemental one original question',
        'created_utc': datetime.now(timezone.utc).isoformat(), 'additional_n': 1, 'method_items': 4,
        'new_unique_core_ids': 1, 'bundle_manifest_sha256': sha(bundle / 'manifest.json'),
        'protocol_sha256': sha(run / 'protocol.json'), 'scope_sha256': sha(AUTH / 'scope.json'),
        'human_expert_validation_n': 0, 'old_scores_transferred': False, 'new_api_calls_by_packager': 0,
        'baseline_public_original_n': 477, 'registered_union_n': 478, 'registered_pending_n': 82,
        'guard_scheduler_source_increment': old_increment,
        'all_actual_response_attempts_and_failures_preserved': True,
        'generation_adapter_lineage': 'AUTH37 byte-identical registered adapters; no source-order/exact-share prompt hook installation',
        'files': {p.relative_to(target).as_posix(): sha(p) for p in sorted(target.rglob('*')) if p.is_file()}}
    (target / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': 'PACKAGED_REQUIRE_OFFLINE_REPLAY', 'files': len(manifest['files']),
        'manifest_sha256': sha(target / 'manifest.json'), 'target': str(target)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('bundle', 'run', 'target'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--auth', type=Path, required=True)
    parser.add_argument('--project-root', type=Path, required=True, help='Root-owned credential scan only when this packager is explicitly executed')
    parser.add_argument('--protocol-sha256', required=True, help='Actual frozen protocol; never inferred from a later rerun')
    parser.add_argument('--bundle-manifest-sha256', required=True)
    parser.add_argument('--guard', type=Path, required=True)
    parser.add_argument('--guard-adaptation', type=Path, required=True)
    args = parser.parse_args()
    main(args.bundle.resolve(), args.run.resolve(), args.target.resolve(), args.auth.resolve(), args.project_root.resolve(),
         args.protocol_sha256, args.bundle_manifest_sha256, args.guard.resolve(), args.guard_adaptation.resolve())
