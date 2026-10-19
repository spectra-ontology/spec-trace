#!/usr/bin/env python3
"""Package completed authorized_incremental22 outputs byte exactly, never initiate calls."""
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


def verify_normalization_bridge(bridge_path, original_guard, intermediate_guard, new_guard):
    bridge = load(bridge_path)
    assert bridge['status'] == 'PASS_EXACT_GUARD_NORMALIZATION_EQUIVALENCE'
    assert bridge['actual_preparer'] == 'prepare_AUTH22_runtime_root.py'
    assert bridge['actual_adaptation_provenance'] == 'AUTH19; preserved unchanged after freeze'
    assert bridge['AUTH21_to22_exact_name_occurrences'] == 7
    assert bridge['same_effective_guard_bytes'] is True
    assert bridge['AUTH22_guard_was_not_regenerated'] is True
    assert bridge['protocol_or_input_mutations'] == 0
    assert bridge['v2_preparer_executed'] is False
    expected = {
        'AUTH19_root_guarded_native_execution_v1.py': sha(original_guard),
        'AUTH21_root_guarded_native_execution_v1.py': sha(intermediate_guard),
        'AUTH22_root_guarded_native_execution_v1.py': sha(new_guard)}
    sources = bridge['guard_sources']
    assert len(sources) == 3
    by_name = {}
    for relative, digest in sources.items():
        path = Path(relative)
        assert not path.is_absolute() and '..' not in path.parts and '\\' not in relative
        assert path.name not in by_name
        by_name[path.name] = digest
    assert by_name == expected
    assert intermediate_guard.read_text().count('authorized_incremental21') == 7
    assert intermediate_guard.read_text().replace('authorized_incremental21', 'authorized_incremental22') == new_guard.read_text()
    return bridge


def main(bundle, run, target, auth, project_root, protocol_sha256, bundle_manifest_sha256, guard, adaptation, normalization_bridge, normalization_bridge_sha256):
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
    assert set(protocol['cohort_ids']) == {'RAN1_P2_CQ1-3'}
    assert protocol['authorized_incremental22_extension']['scope_sha256'] == sha(AUTH / 'scope.json')
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
         protocol['authorized_incremental22_extension']['source_copy_receipt_sha256'])
    early_path = RUNTIME / 'early_execution_reader_copy_receipt.json'
    if early_path.exists():
        early = load(early_path)
        assert early['source_sha256'] == early['copy_sha256']
        assert early['generation_and_adapter_code_modified'] is False
        assert early['execution_scheduling_only'] is True
        copy(RUNTIME / 'execute_ready.py', 'runtime/execute_ready.py', early['copy_sha256'])
        copy(early_path, 'runtime/early_execution_reader_copy_receipt.json')
    provenance = load(adaptation)
    assert provenance['native_lock_memory_cpu_readonly_protocol_unchanged'] is True and provenance['API_calls'] == 0
    copy(guard, 'runtime/AUTH22_root_guarded_native_execution_v1.py', provenance['destination_sha256'])
    assert guard == (ROOT / provenance['destination_path']).resolve()
    original_guard = ROOT / provenance['source_path']
    copy(original_guard, 'runtime/original_guard_scheduler.py', provenance['source_sha256'])
    previous = set(re.findall(r'authorized_incremental(\d+)_OpenRouter_release', original_guard.read_text()))
    assert len(previous) == 1
    old_increment = previous.pop()
    before_choices="choices=['RAN1','RAN2','RAN4','RAN5']"
    after_choices="choices=['RAN1']"
    assert provenance['argument_choices_before']==['RAN1','RAN2','RAN4','RAN5']
    assert provenance['argument_choices_after']==['RAN1']
    assert original_guard.read_text().count(before_choices)==1
    expected_guard=original_guard.read_text().replace('authorized_incremental' + old_increment, 'authorized_incremental22').replace(before_choices,after_choices).replace('--wg RAN3','--wg RAN1')
    assert expected_guard==guard.read_text(), 'Only seven AUTH19-to22 path substitutions, one WG restriction and the declared command-example correction are allowed'
    assert old_increment == '19'
    assert provenance['replacement'] == {'authorized_incremental19': 'authorized_incremental22'}
    replacement_n = original_guard.read_text().count('authorized_incremental19')
    assert replacement_n == 7
    copy(adaptation, 'runtime/AUTH22_root_guarded_native_execution_v1.adaptation.json')
    assert sha(normalization_bridge) == normalization_bridge_sha256
    bridge = load(normalization_bridge)
    source21 = [ROOT / name for name in bridge['guard_sources']
                if Path(name).name == 'AUTH21_root_guarded_native_execution_v1.py']
    assert len(source21) == 1
    verify_normalization_bridge(normalization_bridge, original_guard, source21[0], guard)
    copy(source21[0], 'runtime/AUTH21_original_guard_normalization_reference.py')
    copy(normalization_bridge, 'runtime/guard_scheduler_AUTH21_byte_equivalence.json', normalization_bridge_sha256)
    copy(OUT / 'verify_authorized_incremental22_evaluation.py', 'runtime/verify_authorized_incremental22_evaluation.py')
    copy(OUT / 'verify_incremental22_exact_prompts_and_parsers.py', 'runtime/verify_incremental22_exact_prompts_and_parsers.py')
    copy(Path(__file__), 'runtime/package_authorized_incremental22_evaluation.py')
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
        'The exact question and contract were fixed before these predictions. This separate '
        'cohort adds to the previously published 482 questions, yielding 483/560 original-question contracts '
        'and 77 nonadmitted in its registered snapshot. Later admissions and earlier model results '
        'remain separate. No historical scores transfer.\n\n' + table + '\n'
        'The one ID in every method remains in the denominator, including parsing errors, query failures, '
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
        '```sh\npython3 -B -S runtime/verify_authorized_incremental22_evaluation.py --evidence . '
        '--bundle ../original_core_overnight_repairs22 --out /tmp/authorized_incremental22-replay.json\n```\n\n'
        'The registered generation, adapter and analysis programs are byte-identical to their pre-call '
        'pins. The separately registered one-question wrapper and guarded native scheduler retain '
        'their own source receipts and package hashes. Original local helper paths are preserved as '
        'provenance. Fresh live execution additionally '
        'requires restored pinned graphs, relational projections, retrieval corpus and credentials; '
        'the supplied command verifies saved outputs and strict scoring only. Local packaging, '
        'public push and fresh anonymous download verification are separate states.\n\n'
        'RAN1 lists the original15 Conclusion identities of the named historical meeting121. '
        'Original English and query remain byte-identical; the required answer is an unordered ID set. '
        'The source pack retains all64 own-label candidates,63 active source records, all64 frozen '
        'query operands, active/inactive counterevidence and the same exact first15 selection. '
        'Two-column typed native/SQL agreement does not certify authentic optional content rendering. '
        'No present-day latest-meeting or still-open issue status is asserted. Answer-bearing source '
        'fixtures were not supplied to prompts or retrieval. Historical quarantines, the explicit '
        'RAN5 readmission and14 clarification diagnostics stay separate. No old scores transfer.\n')
    manifest = {'kind': 'Fresh complete four-arm evaluation of immutable supplemental one original question',
        'created_utc': datetime.now(timezone.utc).isoformat(), 'additional_n': 1, 'method_items': 4,
        'new_unique_core_ids': 1, 'planned_first_calls_without_transport_retry': 5, 'bundle_manifest_sha256': sha(bundle / 'manifest.json'),
        'protocol_sha256': sha(run / 'protocol.json'), 'scope_sha256': sha(AUTH / 'scope.json'),
        'human_expert_validation_n': 0, 'old_scores_transferred': False, 'new_api_calls_by_packager': 0,
        'baseline_public_original_n': 482, 'registered_union_n': 483, 'registered_pending_n': 77,
        'cohort_ids': sorted(protocol['cohort_ids']),
        'guard_scheduler_replacement_n': replacement_n,
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
    parser.add_argument('--guard-normalization-bridge', type=Path, required=True)
    parser.add_argument('--guard-normalization-bridge-sha256', required=True)
    args = parser.parse_args()
    main(args.bundle.resolve(), args.run.resolve(), args.target.resolve(), args.auth.resolve(), args.project_root.resolve(),
         args.protocol_sha256, args.bundle_manifest_sha256, args.guard.resolve(), args.guard_adaptation.resolve(), args.guard_normalization_bridge.resolve(), args.guard_normalization_bridge_sha256)
