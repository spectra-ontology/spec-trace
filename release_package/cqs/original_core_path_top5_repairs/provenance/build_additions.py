#!/usr/bin/env python3
"""Prepare additional evidence only after separate reviews and native checks."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

BASE = Path(__file__).resolve().parent
EMP = BASE.parent
PREP = EMP.parent
ORIG = PREP / 'original_repair'
PARENT = Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/cqs/original_core_repair')
sys.dont_write_bytecode = True
sys.path.insert(0, str(PREP))
sys.path.insert(0, str(ORIG))
import continue_original as implementation


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonfile(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main(specification, destination):
    if destination.exists():
        raise ValueError('refuse to replace an already prepared addition bundle')
    protocol = json.loads((BASE / 'protocol.json').read_text())
    if sha(PARENT / 'manifest.json') != protocol['public_manifest_sha256']:
        raise ValueError('published parent changed during recheck')
    spec = json.loads(specification.read_text())
    originals = implementation.unique(implementation.read(PARENT / 'provenance/original_benchmark.jsonl'))
    parent_tasks = implementation.unique(implementation.read(PARENT / 'tasks.jsonl'))
    prior_tasks = {}
    prior_sources = []
    for prior in spec.get('prior_additional_cohorts', []):
        source = Path(prior['source'])
        verified = __import__('subprocess').run(
            [sys.executable, '-B', '-S', str(source/'verify_additions.py'), '--bundle', str(source),
             '--parent', str(PARENT)], check=True, capture_output=True, text=True)
        proof = json.loads(verified.stdout)
        current = implementation.unique(implementation.read(source/'tasks.jsonl'))
        if set(current) & (set(parent_tasks) | set(prior_tasks)):
            raise ValueError('Prior additional cohorts overlap')
        prior_tasks.update(current)
        prior_sources.append((source, prior['relative'], proof))
    criteria = json.loads((PARENT / 'criteria.json').read_text())
    proposals = {}
    outcomes = []
    accepted = []
    for group in spec['groups']:
        primary_rows = [row for row in implementation.read(Path(group['proposals'])) if 'id' in row]
        secondary_rows = [row for row in implementation.read(Path(group['secondary'])) if 'id' in row]
        second = implementation.unique(secondary_rows)
        for task in primary_rows:
            identifier = task['id']
            if identifier in proposals or identifier in parent_tasks or identifier in prior_tasks:
                raise ValueError('duplicate candidate or overlap with frozen parent')
            proposals[identifier] = task
            original = originals[identifier]
            definition = {key: task[key] for key in implementation.DEFINITION_KEYS}
            if (task['question_en'] != original['question_en'] or task['original_query'] != original['cypher']
                    or task['original_question_preserved'] is not True
                    or task['repair_sha256'] != implementation.digest(definition)
                    or task['criteria_sha256'] != sha(PARENT / 'criteria.json')):
                raise ValueError('candidate differs from the original or pinned definition')
            review = second.get(identifier)
            if not review or review.get('status') != 'pass' or task['primary_review'].get('status') != 'pass':
                outcomes.append({'id': identifier, 'status': 'pending', 'reason': 'Both separate fixed-unit semantic judgments have not passed.'})
                continue
            for judgment in (task['primary_review'], review):
                implementation.review_schema.check_pass(judgment, original['question_en'], criteria['semantic_units'],
                    criteria_sha=task['criteria_sha256'], identity_key='repair_sha256', identity_sha=task['repair_sha256'])
            prior_base = implementation.native.BASE
            try:
                implementation.native.BASE = Path(group['native_base'])
                rows, receipt = implementation.native.references({'id': identifier, 'candidate_query': task['reference_query']})
            finally:
                implementation.native.BASE = prior_base
            if rows is None:
                outcomes.append({'id': identifier, 'status': 'pending', 'reason': 'Complete exact-query native output unavailable.'})
                continue
            records = implementation.native.answer_projection(rows, task['required_fields'], receipt['columns'])
            groups = implementation.original_scorer.make_order_groups(task, rows, records) if task['collection']['kind'] in {
                'native_ordered_ties', 'top_k_boundary_ties'} else None
            controls = implementation.checks(task, records, groups)
            if not all(control['pass'] for control in controls):
                outcomes.append({'id': identifier, 'status': 'pending', 'reason': 'Actual requested-field scorer control failed.'})
                continue
            accepted.append((task, review, receipt, records, groups, controls))
            outcomes.append({'id': identifier, 'status': 'pass', 'repair_sha256': task['repair_sha256']})
    if not accepted:
        raise ValueError('no actually completed additional repairs')
    destination.mkdir(parents=True)

    def copy(source, relative):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        return relative

    for name in ('criteria.json', 'score_predictions.py', 'original_scorer.py', 'scorer.py', 'typed_values.py',
                 'contract_checks.py', 'review_schema.py', 'source_pins.json'):
        copy(PARENT / name, name)
    copy(BASE / 'verify_additions.py', 'verify_additions.py')
    copy(specification, 'provenance/build_inputs.json')
    copy(BASE / 'build_additions.py', 'provenance/build_additions.py')
    prior_cohorts = []
    for source, relative, proof in prior_sources:
        target = destination/relative
        if not target.resolve().is_relative_to(destination.resolve()) or target.exists():
            raise ValueError('Unsafe or reused prior-cohort path')
        shutil.copytree(source, target)
        prior_cohorts.append({'relative':relative, 'manifest_sha256':sha(source/'manifest.json'),
                              'admitted_n':proof['additional_admitted_n']})
    tasks = []
    gold = []
    checks = []
    for task, second, receipt, records, groups, controls in accepted:
        identifier = task['id']
        root = 'reference_outputs/' + identifier + '/' + task['reference_query_sha256']
        receipt_file = copy(Path(receipt['receipt_path']), root + '.json')
        receipt_source = json.loads(Path(receipt['receipt_path']).read_text())
        source_rows = Path(receipt['rows_file']) if 'execution' in receipt_source else Path(receipt['receipt_path']).parent / (task['reference_query_sha256'] + '.jsonl')
        rows_file = copy(source_rows, root + '.jsonl')
        provenance = receipt['provenance']
        run_file = copy(Path(provenance['run_report_path']), 'provenance/native_run_' + sha(Path(provenance['run_report_path'])) + '.json')
        completed = dict(task, secondary_review=second, validation_status='validated',
            reference_evidence=receipt, native_rows=len(records), projected_records_sha256=implementation.digest(records),
            completeness_witness=None, human_author_review_completed=False, expert_validation_n=0, model_calls=0,
            model_call_scope='No benchmark predictions for these newly admitted IDs yet; separate AI reviews recorded.',
            portable_native_evidence={'receipt_file': receipt_file, 'receipt_sha256': sha(destination/receipt_file),
                'rows_file': rows_file, 'rows_sha256': sha(destination/rows_file), 'run_report_file': run_file,
                'source_kind': 'retained_original_query' if 'execution' in receipt_source else 'captured_repaired_query'})
        chain = {}
        if 'execution' in receipt_source:
            for name in ('frozen_manifest.json', 'input_manifest.json'):
                chain[name] = copy(implementation.native.OLD_NATIVE/name, 'provenance/'+name)
        else:
            native_base = Path(receipt['receipt_path']).parents[2]
            for name, source in [('execution_inputs', native_base/'execution_inputs'/(identifier.split('_')[0]+'.jsonl')),
                                 ('execution_protocol', native_base/'execution_protocol.json')]:
                chain[name] = copy(source, 'provenance/'+sha(source)+source.suffix)
        completed['portable_native_evidence']['chain'] = chain
        source_checks = second.get('source_checks', {})
        if source_checks.get('source_zip_path'):
            archive = Path(source_checks['source_zip_path'])
            if sha(archive) != source_checks['source_zip_sha256']:
                raise ValueError('Original source ZIP changed')
            relative = 'source_evidence/'+source_checks['source_zip_sha256']+'.zip'
            copy(archive, relative)
            with zipfile.ZipFile(archive) as zipped:
                member = zipped.read(source_checks['source_member'])
            if hashlib.sha256(member).hexdigest() != source_checks['source_member_sha256']:
                raise ValueError('Original source DOCX changed')
            completed['portable_source_evidence'] = {'archive_file':relative,
                'archive_sha256':sha(archive),'member':source_checks['source_member'],
                'member_sha256':source_checks['source_member_sha256'],
                'passage_text_runs':source_checks['source_passage_text_runs'],
                'scope':'Specific source-form field only; not full archive or expert verification.'}
        tasks.append(completed)
        gold.append({'id': identifier, 'repair_sha256': task['repair_sha256'], 'records': records, 'order_groups': groups})
        checks.append({'id': identifier, 'repair_sha256': task['repair_sha256'], 'checks': controls, 'pass': True})
    for name, rows in [('tasks.jsonl', tasks), ('reference_gold.jsonl', gold), ('scorer_checks.jsonl', checks), ('candidate_dispositions.jsonl', outcomes)]:
        implementation.write(destination/name, rows)
    ledger = implementation.unique(implementation.read(PARENT/'all_core_dispositions.jsonl'))
    for task in list(prior_tasks.values()) + tasks:
        ledger[task['id']] = {'id':task['id'], 'status':'pass', 'repair_class':task['repair_class'], 'repair_sha256':task['repair_sha256'], 'question_preserved':True}
    implementation.write(destination/'all_core_dispositions.jsonl', sorted(ledger.values(),key=lambda row:row['id']))
    for extra in spec.get('additional_provenance', []):
        copy(Path(extra['source']), extra['relative'])
    (destination/'README.md').write_text(
        '# Additional original Core repairs\n\n'
        f'This additive bundle admits {len(tasks)} disjoint original IDs after separate fixed-unit AI reviews, '
        'complete exact-query native evidence, and actual requested-field scorer controls. '
        f'The union with the preserved parent and prior disjoint additions contains {len(parent_tasks)+len(prior_tasks)+len(tasks)} items; '
        f'{560-len(parent_tasks)-len(prior_tasks)-len(tasks)} remain unresolved. Questions retain their original English wording and meaning.\n\n'
        'The parent cohort and its 371-item model results are preserved. This repair manifest contains no '
        'new model predictions. AI review and source-linked programmatic checks are not human or independent '
        'expert validation. Source evidence has the item-specific scope recorded in each task.\n\n'
        'Run `python3 -B verify_additions.py` from this directory. Model evaluations, when actually executed, '
        'must be published separately with their own frozen cohort, protocol, raw predictions and full denominator.\n')
    parent_manifest = json.loads((PARENT/'manifest.json').read_text())
    manifest = {'kind':'Additional original-question repairs; parent cohort and model results preserved',
        'parent_public_commit':protocol['public_commit'], 'parent_bundle_manifest_sha256':sha(PARENT/'manifest.json'),
        'admitted_n':len(tasks), 'cohort_ids':[task['id'] for task in tasks],
        'prior_additional_cohorts':prior_cohorts,
        'global_admitted_union_n':len(parent_tasks)+len(prior_tasks)+len(tasks), 'global_unresolved_n':560-len(parent_tasks)-len(prior_tasks)-len(tasks),
        'native_rows':sum(task['native_rows'] for task in tasks), 'actual_scorer_controls':sum(len(row['checks']) for row in checks),
        'repair_classes':dict(Counter(task['repair_class'] for task in tasks)),
        'graph_sources':parent_manifest['graph_sources'], 'model_predictions_n':0,
        'expert_validation_n':0,'human_author_review_completed':False,
        'files':{str(path.relative_to(destination)):sha(path) for path in destination.rglob('*') if path.is_file()}}
    jsonfile(destination/'manifest.json',manifest)
    print(json.dumps({'additional_completed_n':len(tasks),'global_completed_n':manifest['global_admitted_union_n'],
                      'native_rows':manifest['native_rows'],'scorer_controls':manifest['actual_scorer_controls']},ensure_ascii=False))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--specification',type=Path,required=True)
    parser.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args()
    main(args.specification,args.destination)
