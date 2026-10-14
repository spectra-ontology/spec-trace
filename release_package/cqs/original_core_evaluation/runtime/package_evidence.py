#!/usr/bin/env python3
"""Stage measured evidence without mutating frozen runs or the public checkout."""
import argparse
import gzip
import hashlib
import json
import io
from pathlib import Path
import shutil
import tarfile
from public_redaction import redact_json

BASE = Path(__file__).resolve().parent
ORIGINAL = BASE.parent / 'original_repair'
METHODS = ('text2cypher', 'text2sql', 'single_retrieval', 'iterative_retrieval')
REDACTIONS = []


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def public_bytes(source, published_path):
    """Private attempts stay byte-identical; only account finances are masked publicly."""
    data = source.read_bytes()
    pointers = []
    if source.suffix == '.json':
        value = json.loads(data)
        value, pointers = redact_json(value)
        if pointers:
            data = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    elif source.suffix == '.jsonl':
        lines = []
        for n, line in enumerate(data.decode().splitlines()):
            if not line.strip():
                continue
            value, changed = redact_json(json.loads(line))
            pointers.extend({'line': n + 1, 'location': p} for p in changed)
            lines.append(json.dumps(value, ensure_ascii=False, allow_nan=False))
        if pointers:
            data = ('\n'.join(lines) + '\n').encode()
    if pointers:
        REDACTIONS.append({'published_path': published_path,
            'private_original_sha256': sha(source),
            'published_sha256': hashlib.sha256(data).hexdigest(),
            'masked_locations': pointers,
            'scope': 'Account/key finance only; model inputs, model outputs, status, error code and experiment cost unchanged.'})
    return data


def copy_public(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.name == '.env' or source.is_symlink():
        raise ValueError('Unsafe public input')
    target.write_bytes(public_bytes(source, str(target)))


def copy_tree(source, target):
    for path in sorted(source.rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
            copy_public(path, target / path.relative_to(source))


def archive(source, target, arcname):
    """Preserve every retained file; exclude Python cache only."""
    inventory = {}
    original_inventory = {}
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('wb') as stream, gzip.GzipFile(fileobj=stream, mode='wb', mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode='w|') as output:
            for path in sorted(source.rglob('*')):
                if not path.is_file() or '__pycache__' in path.parts or path.suffix == '.pyc':
                    continue
                if path.name == '.env' or path.is_symlink():
                    raise ValueError('Secret configuration must never be archived')
                rel = str(path.relative_to(source))
                original_inventory[rel] = sha(path)
                data = public_bytes(path, str(target) + '::' + arcname + '/' + rel)
                inventory[rel] = hashlib.sha256(data).hexdigest()
                member = output.gettarinfo(str(path), arcname=arcname + '/' + rel)
                member.size = len(data)
                member.uid = member.gid = 0
                member.uname = member.gname = ''
                output.addfile(member, io.BytesIO(data))
    write(target.with_suffix(target.suffix + '.inventory.json'), {
        'archive_sha256': sha(target), 'archive_bytes': target.stat().st_size,
        'files': inventory, 'file_n': len(inventory),
        'private_original_files': original_inventory,
        'public_bytes_are_identical_except_explicit_account_finance_redaction': True,
    })
    if target.stat().st_size >= 95 * 1024 ** 2:
        raise ValueError('Archive requires separate large-asset publication: ' + str(target))


def check_run(run, bundle):
    tasks = {t['id']: t for t in rows(bundle / 'tasks.jsonl')}
    if len(tasks) != len(rows(bundle / 'tasks.jsonl')):
        raise ValueError('Duplicate contract IDs')
    protocol = load(run / 'protocol.json')
    if protocol['tasks_sha256'] != sha(bundle / 'tasks.jsonl') or protocol['gold_sha256'] != sha(bundle / 'reference_gold.jsonl'):
        raise ValueError('Run concerns a different frozen contract')
    completion = load(run / 'generation_complete.json')
    if completion['completed_method_items'] != len(tasks) * 4:
        raise ValueError('Generation disposition inventory incomplete')
    analysis = load(run / 'analysis.json')
    if analysis['admitted_n'] != len(tasks):
        raise ValueError('Incomplete score denominator')
    for method in METHODS:
        for name in ('predictions.jsonl', 'statuses.jsonl'):
            output = rows(run / method / name)
            if len(output) != len(tasks) or {p['id'] for p in output} != set(tasks):
                raise ValueError('Missing prediction or status IDs')
            if any(p['repair_sha256'] != tasks[p['id']]['repair_sha256'] for p in output):
                raise ValueError('Prediction repair hash mismatch')
    return analysis


def write_readme(destination, expanded, phases):
    union = next((a for label, run, bundle, a in phases if label == 'admitted_union'), None)
    lines = ['# New evaluation of repaired original Core questions', '',
        'This companion preserves new predictions from one model, `anthropic/claude-opus-4.8`,',
        'restricted to the Anthropic provider without model fallback. The unchanged original',
        'questions are evaluated under frozen, typed, requested-field contracts. The original',
        '350-item cohort and the disjoint 21-item addition were fixed separately before their',
        'model calls. Their union contains each of the 371 admitted IDs exactly once.', '',
        'The original Core contains 560 IDs: 371 repairs are admitted (119 scorer-only and',
        '252 query-and-scorer repairs), and 189 remain pending. The admitted set is not a',
        'representative sample of all 560. No independent human/expert validation is claimed.', '',
        '## Measured results', '',
        'The following table includes every admitted ID. Execution failures and abstentions',
        'receive F1=0 and exact=false, including an item whose gold answer is empty.',
        'A parsed self-reported partial answer can receive record credit; it cannot establish',
        'an empty-gold success. `analysis.json` also reports WG, phase, output shape,',
        'multiple requested fields, all execution statuses, and paired bootstrap intervals.', '']
    if union:
        lines.extend((destination / 'results/admitted_union/performance_table.md').read_text().splitlines())
    else:
        lines.append('No combined-cohort result is published in this package.')
    lines.extend(['', 'Original attempts and pre-provider transport recovery are reported separately',
        'under `results/` and `retained_runs/`. Only recorded HTTP402 in-flight-budget or',
        'HTTP403 key-limit failures with no provider response content were eligible for',
        'recovery. Actual model responses, invalid queries, incomplete outputs, and incorrect',
        'answers were retained without quality retries. Existing query executions, including',
        'their failures, were reused only when their pinned generation and source guards matched.', '',
        '## Interpretation and information access', '',
        'Text2Cypher and Text2SQL use the same graph-derived records. SQL conversion checks',
        'preserve types, duplicate/parallel relations, null semantics, and source snapshots.',
        'The generated SQL results include many relationship-table naming and syntax errors:',
        'physical tables use a `rel_` prefix. The frozen interface and these failures were',
        'retained. Low SQL performance therefore does not establish an intrinsic limitation',
        'of SQL or a causal advantage of graph storage.', '',
        'The text cache contains 3,901,610 chunks from five RAN working groups, but equality',
        'of its cutoff/content with the frozen graphs remains unverified. Single retrieval',
        'allows one search; iterative retrieval allows one follow-up search and an additional',
        'model call. Each answer context is limited to 12 documents, 4,000 characters per',
        'document and 48,000 characters in total. Corpus presence and actual prompt-context',
        'coverage are separate diagnostics. Finite retrieval cannot establish full-population',
        'aggregates. Retrieval timeouts and incomplete outputs remain in the denominator.', '',
        'Raw-document checks are limited to the explicitly linked examples in',
        '`source_semantic_audit.json` and `repair_case_evidence.json`; successful graph execution',
        'or agreement between AI reviewers is not full raw-document factual/completeness',
        'validation. Source-first expert packets are prepared, with zero completed expert reviews.', '',
        '## Offline verification and score replay', '',
        'From the repository root, with Python 3 and no credentials or database:', '', '```bash',
        'python3 -B -S release_package/cqs/original_core_repair/verify_release.py',
        'python3 -B -S release_package/cqs/original_core_evaluation/runtime/verify_evidence.py \\',
        '  --evidence release_package/cqs/original_core_evaluation \\',
        '  --bundle release_package/cqs/original_core_repair \\',
        '  --out /tmp/spectra_evidence_verification.json', '```', '',
        'The evidence verifier checks file/archive inventories, full prediction/status ID',
        'coverage, repair hashes, and recomputes published complete-record scores with the',
        'released scorer. It does not generate model answers or execute graph/SQL queries.',
        'The frozen 350 and 21 contract bundles are also archived under `inputs/`.', '',
        'Fresh generation requires the pinned graph snapshots, SQLite exports and local',
        'retrieval corpus, Neo4j, and an explicitly configured OpenRouter credential.',
        'Runtime scripts, frozen requests, responses, generated queries, executed rows,',
        'protocols and usage receipts are retained so the original configuration can be',
        'inspected. Do not resume an already completed run or transfer historical nine-model',
        'scores to these contracts.', '',
        '## Provenance and public privacy', '',
        'The sibling original_core_repair manifest is `' + sha(expanded / 'manifest.json') + '`.',
        'Private original attempts remain unchanged. Public raw artifacts mask only provider',
        'account/key financial error details. `public_redactions.json` maps original and public',
        'hashes and the affected fields; model input/output content and experiment cost/usage',
        'are unchanged. Archive inventories distinguish published bytes from private originals.',
        'Preparation, upload and external download verification are separate operations.',
        '`scope.json` and `evidence_manifest.json` record the preparation state; publication',
        'and independent download verification are recorded separately in the repository',
        'publication handoff rather than being assumed from a staged directory.', ''])
    (destination / 'README.md').write_text('\n'.join(lines))


def stage(destination, expanded, extension, combined):
    if destination.exists():
        raise ValueError('Staging destination already exists; preserve prior evidence')
    main_bundle = ORIGINAL / 'final_staging/release_package/cqs/original_core_repair'
    main = BASE / 'runs/original-core-main'
    recovered = BASE / 'runs/original-core-transport-supplement'
    main_analysis = check_run(main, main_bundle)
    recovered_analysis = check_run(recovered, main_bundle)
    if load(recovered / 'generation_complete.json')['original_artifacts_unchanged'] is not True:
        raise ValueError('Original attempt artifacts changed')
    latest = rows(expanded / 'tasks.jsonl')
    if len(latest) != 371:
        raise ValueError('Expected measured 350 + 21 contract union')
    phases = [('original_attempt', main, main_bundle, main_analysis),
              ('transport_recovered', recovered, main_bundle, recovered_analysis)]
    if extension:
        extension_bundle = ORIGINAL / 'extension_bundle'
        first_extension = BASE / 'runs/additional-originals'
        phases.append(('additional_original_attempt', first_extension, extension_bundle, check_run(first_extension, extension_bundle)))
        phases.append(('additional_originals_recovered', extension, extension_bundle, check_run(extension, extension_bundle)))
        if load(extension / 'generation_complete.json')['original_artifacts_unchanged'] is not True:
            raise ValueError('Original additional-cohort artifacts changed')
    if combined:
        phases.append(('admitted_union', combined, expanded, check_run(combined, expanded)))
    destination.mkdir(parents=True)
    runtime = destination / 'runtime'
    runtime.mkdir()
    for source in BASE.glob('*.py'):
        copy_public(source, runtime / source.name)
    excluded = {'information_access_report.json', 'information_access_report.summary.json',
                'main_final_information_access.json', 'main_final_information_access.summary.json'}
    for source in (BASE / 'audit').rglob('*'):
        if source.is_file() and source.name not in excluded and '__pycache__' not in source.parts and source.suffix != '.pyc':
            copy_public(source, destination / 'audit' / source.relative_to(BASE / 'audit'))
    for name in ('model_catalog.json', 'model_endpoints.json', 'structured_interface.json',
                 'sql_encoding_verification.json', 'sql_source_information.json',
                 'sql_generation_schema_diagnostic.json'):
        copy_public(BASE / name, destination / name)
    if (BASE / 'sql_generation_schema_diagnostic_recovered.json').exists():
        copy_public(BASE / 'sql_generation_schema_diagnostic_recovered.json',
                    destination / 'sql_generation_schema_diagnostic_recovered.json')
    relational = destination / 'relational_manifests'
    relational.mkdir()
    for source in (BASE / 'relational').glob('*.manifest.json'):
        copy_public(source, relational / source.name)
    for label, run, bundle, analysis in phases:
        folder = destination / 'results' / label
        folder.mkdir(parents=True)
        for name in ('protocol.json', 'analysis.json', 'performance_table.md', 'usage.json', 'generation_complete.json'):
            if (run / name).exists():
                copy_public(run / name, folder / name)
        for method in METHODS:
            copy_tree(run / method, folder / method)
        if label != 'admitted_union':
            archive(run, destination / 'retained_runs' / (label + '.tar.gz'), run.name)
    archive(main_bundle, destination / 'inputs/main350_bundle.tar.gz', 'main350_bundle')
    if extension:
        archive(ORIGINAL / 'extension_bundle', destination / 'inputs/additional21_bundle.tar.gz', 'additional21_bundle')
    source_audit = ORIGINAL / 'empirical/source_semantic_audit.json'
    copy_public(source_audit, destination / 'source_semantic_audit.json')
    for name in ('repair_case_evidence.json', 'repair_case_evidence.md', 'claim_evidence_index.json'):
        if (ORIGINAL / 'empirical' / name).exists():
            copy_public(ORIGINAL / 'empirical' / name, destination / name)
    copy_tree(ORIGINAL / 'expert_review_bundle', destination / 'expert_review_main350')
    if (ORIGINAL / 'expert_review_extension21').exists():
        copy_tree(ORIGINAL / 'expert_review_extension21', destination / 'expert_review_additional21')
    further = ORIGINAL / 'further_expansion'
    proof = destination / 'further_audit'
    proof.mkdir()
    for source in further.glob('*.json'):
        copy_public(source, proof / source.name)
    for source in further.glob('*.py'):
        copy_public(source, proof / source.name)
    protocol_notes = {
        'published': False, 'external_download_verified': False,
        'original_total': 560, 'original_question_contracts_admitted': len(latest),
        'unresolved_original_questions': 560 - len(latest),
        'main_frozen_cohort_n': 350, 'additional_frozen_cohort_n': 21,
        'new_model_evaluation_ids_completed': 350 + (21 if extension else 0),
        'additional21_model_evaluation_completed': bool(extension),
        'original_attempt_and_transport_recovery_reported_separately': True,
        'human_author_semantic_review_completed': False, 'independent_expert_review_n': 0,
        'archive_text_vs_graph_cutoff_and_content_equality': 'unverified',
        'raw_source_check_scope': 'See source_semantic_audit.json; native graph execution is distinct from raw-document factual completeness.',
        'historical_nine_model_results_transferred': False,
        'limitations': ['One newly evaluated model and a nonrepresentative admitted subset.',
                        'Finite retrieved context cannot establish full-population aggregates.',
                        'SQL and graph share records; text has different and incompletely matched information access.',
                        'SQL query-generation errors include physical relationship-table naming failures; this is not evidence of an intrinsic limitation of SQL.',
                        'Saved prediction scoring is reproducible offline; fresh retrieval requires the pinned external local corpus.',
                        'A prepared expert review bundle is not completed expert review.'],
    }
    write(destination / 'scope.json', protocol_notes)
    original_usage = load(main / 'usage.json')
    recovery_usage = load(recovered / 'usage.json')
    costs = {'original350_known_cost_usd': original_usage['known_actual_cost_usd'],
             'original350_unknown_cost_attempts': original_usage['unknown_cost_attempts'],
             'transport350_known_new_cost_usd': recovery_usage['known_supplement_cost_usd'],
             'transport350_unknown_new_cost_attempts': recovery_usage['unknown_new_cost_attempts']}
    if extension:
        first_usage = load((BASE / 'runs/additional-originals') / 'usage.json')
        additional_usage = load(extension / 'usage.json')
        costs.update({'original21_known_cost_usd': first_usage['known_actual_cost_usd'],
                      'original21_unknown_cost_attempts': first_usage['unknown_cost_attempts'],
                      'transport21_known_new_cost_usd': additional_usage['known_supplement_cost_usd'],
                      'transport21_unknown_new_cost_attempts': additional_usage['unknown_new_cost_attempts']})
    costs['known_benchmark_generation_cost_usd'] = sum(v for k, v in costs.items() if k.endswith('_cost_usd'))
    costs['unknown_cost_attempts'] = sum(v for k, v in costs.items() if k.endswith('_attempts'))
    costs['complete_total_cost_known'] = costs['unknown_cost_attempts'] == 0
    costs['scope'] = 'Four-method benchmark generation phases only; prior repair-review costs and private account/key finances are separate.'
    write(destination / 'experiment_costs.json', costs)
    for record in REDACTIONS:
        prefix = str(destination) + '/'
        if record['published_path'].startswith(prefix):
            record['published_path'] = record['published_path'][len(prefix):]
    write(destination / 'public_redactions.json', {'private_originals_preserved': True,
        'model_payloads_and_model_answer_content_redacted': False,
        'scope': 'Provider account/key finance; experiment usage and costs remain public.',
        'redacted_file_occurrences': len(REDACTIONS), 'files': REDACTIONS})
    write_readme(destination, expanded, phases)
    pins = {str(p.relative_to(destination)): sha(p) for p in sorted(destination.rglob('*')) if p.is_file()}
    write(destination / 'evidence_manifest.json', {'files': pins, 'file_n': len(pins),
        'prepared_local': True, 'published': False, 'external_download_verified': False})
    print(json.dumps({'staged': str(destination), 'files': len(pins), 'manifest_sha256': sha(destination / 'evidence_manifest.json')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--expanded', type=Path, required=True)
    parser.add_argument('--extension', type=Path)
    parser.add_argument('--combined', type=Path)
    args = parser.parse_args()
    stage(args.destination, args.expanded, args.extension, args.combined)
