"""Independently read captured artifacts; no execution or scorer mutation."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
ORIG = BASE.parent
RUN = BASE / 'native_capture'
sys.path.insert(0, str(ORIG))
import build


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_type(value, field):
    if value is None:
        return field['nullable']
    return {'string': lambda: isinstance(value, str),
            'integer': lambda: isinstance(value, int) and not isinstance(value, bool),
            'boolean': lambda: isinstance(value, bool)}[field['type']]()


paths = [RUN / name for name in ('tasks.jsonl', 'reference_gold.jsonl', 'scorer_checks.jsonl', 'verification.json')]
input_hashes = {str(path): sha(path) for path in paths}
tasks = build.read(RUN / 'tasks.jsonl')
gold = build.index(build.read(RUN / 'reference_gold.jsonl'))
controls = build.index(build.read(RUN / 'scorer_checks.jsonl'))
originals = build.index(build.read(build.native.PUBLIC / 'spectra_cq_v2.0/benchmark.jsonl'))
prior = build.index(build.read(ORIG / 'final_staging/release_package/cqs/original_core_repair/tasks.jsonl'))
criteria_sha = sha(ORIG / 'criteria.json')
units = json.loads((ORIG / 'criteria.json').read_text())['semantic_units']
keys = ('id', 'question_en', 'original_query', 'reference_query', 'required_fields', 'collection',
        'cardinality_policy', 'repair_class', 'original_question_preserved')
errors = []
findings = []
metadata_notes = []
source_audits = {wg: json.loads((BASE / ('secondary_source_audit_' + wg + '.json')).read_text())
                 for wg in ('RAN3', 'RAN4', 'RAN5')}
maximum_witness_path = BASE / 'max_frequency_source_witness.json'
maximum_witnesses = {row['id']: row for row in json.loads(maximum_witness_path.read_text())['results']}
ran2_cr_audit = json.loads((BASE / 'RAN2_structure_audit.json').read_text())
ran5_other_specs = json.loads((BASE / 'other_specs_secondary_source_RAN5.json').read_text())
meeting130 = json.loads((BASE / 'meeting130_secondary_source_RAN3.json').read_text())
all_rows = 0

for task in tasks:
    identifier = task['id']
    item_errors = []
    original = originals[identifier]
    receipt = task['reference_evidence']
    if identifier in prior:
        item_errors.append('overlaps frozen350')
    if task['question_en'] != original['question_en'] or task['original_query'] != original['cypher']:
        item_errors.append('original bytes differ')
    if build.digest({key: task[key] for key in keys}) != task['repair_sha256']:
        item_errors.append('repair SHA mismatch')
    if task['criteria_sha256'] != criteria_sha:
        item_errors.append('criteria SHA mismatch')
    for review in (task['primary_review'], task['secondary_review']):
        try:
            build.review_schema.check_pass(review, task['question_en'], units,
                                           criteria_sha=criteria_sha, identity_key='repair_sha256',
                                           identity_sha=task['repair_sha256'])
        except ValueError as error:
            item_errors.append(str(error))
    query_sha = hashlib.sha256(task['reference_query'].encode()).hexdigest()
    if receipt['query'] != task['reference_query'] or receipt['query_sha256'] != query_sha:
        item_errors.append('captured query differs')
    if not (receipt['status'] == 'OK' and receipt['truncated'] is False
            and receipt['full_rows_available'] is True and receipt['execution_summary_complete'] is True
            and receipt['rollback_completed'] is True):
        item_errors.append('native complete/rollback flags fail')
    receipt_path = Path(receipt['receipt_path'])
    rows_path = RUN / receipt['rows_file']
    if sha(receipt_path) != receipt['receipt_sha256'] or sha(rows_path) != receipt['rows_sha256']:
        item_errors.append('native file SHA mismatch')
    raw = build.read(rows_path)
    if len(raw) != receipt['rows_retained'] or len(raw) != task['native_rows']:
        item_errors.append('native row count mismatch')
    native_records = [dict(zip(receipt['columns'], row)) for row in raw]
    if any(len(row) != len(receipt['columns']) for row in raw):
        item_errors.append('native row width differs from declared columns')
    projection = build.native.answer_projection(native_records, task['required_fields'], receipt['columns'])
    if build.digest(projection) != task['projected_records_sha256'] or projection != gold[identifier]['records']:
        item_errors.append('requested projection/gold mismatch')
    if gold[identifier]['repair_sha256'] != task['repair_sha256']:
        item_errors.append('gold repair SHA mismatch')
    types = {field['name']: dict(Counter(type(record[field['name']]).__name__
                                       for record in projection)) for field in task['required_fields']}
    for field in task['required_fields']:
        if any(not check_type(record[field['name']], field) for record in projection):
            item_errors.append('requested field type/nullability mismatch: ' + field['name'])
    projected_duplicates = len(projection) - len({build.digest(record) for record in projection})
    if projected_duplicates:
        item_errors.append('requested identity projection has duplicates')
    if controls[identifier]['repair_sha256'] != task['repair_sha256'] or not controls[identifier]['pass']:
        item_errors.append('control metadata fails')
    if not all(record['pass'] for record in controls[identifier]['checks']):
        item_errors.append('recorded strict scorer control fails')
    wg = identifier.split('_')[0]
    pool_evidence = None
    audit = source_audits.get(wg)
    if audit and receipt['provenance']['graph_source_sha256'] != audit['graph_source_sha256']:
        item_errors.append('native source pin differs from direct source audit')
    if identifier in {'RAN3_P2_CQ1-8', 'RAN4_P2_CQ1-8', 'RAN4_P1_CQ3-1'}:
        expected = audit['identity_audits']['AgendaItem']['population']
        if len(raw) != expected:
            item_errors.append('complete AgendaItem pool differs from full source')
        count_name = 'tdocCount' if identifier == 'RAN4_P1_CQ3-1' else 'resolutionCount'
        relation = 'belongsTo' if identifier == 'RAN4_P1_CQ3-1' else 'resolutionBelongsTo'
        index = receipt['columns'].index(count_name)
        values = [record[index] for record in raw]
        expected_sum = (audit['agenda_role_checks'][relation]['edges_to_agenda']
                        - audit['agenda_role_checks'][relation]['unexpected_source_label'])
        expected_zeros = audit['agenda_role_checks'][relation]['zero_agenda_items']
        if sum(values) != expected_sum or values.count(0) != expected_zeros:
            item_errors.append('agenda count/zero population differs from direct source')
        pool_evidence = {'unit': 'all source AgendaItem entities', 'expected_pool': expected,
                         'actual_pool': len(raw), 'expected_count_sum': expected_sum,
                         'actual_count_sum': sum(values), 'expected_zero_n': expected_zeros,
                         'actual_zero_n': values.count(0)}
    elif identifier in {'RAN3_P3_CQ2-4', 'RAN4_P3_CQ2-3'}:
        expected = audit['identity_audits']['Section']['population']
        values = [record[receipt['columns'].index('referenceCount')] for record in raw]
        if len(raw) != expected:
            item_errors.append('complete Section pool differs from full source')
        expected_sum = audit['reference_unit_equivalence']['distinct_section_reference_source_target_pairs']
        if sum(values) != expected_sum:
            item_errors.append('incoming-reference sum differs from direct source')
        pool_evidence = {'unit': 'all source Section entities', 'expected_pool': expected,
                         'actual_pool': len(raw), 'expected_reference_sum': expected_sum,
                         'actual_reference_sum': sum(values), 'actual_zero_n': values.count(0)}
    elif identifier == 'RAN4_P5_CQ5-3':
        expected = audit['identity_audits']['TechnicalReport']['population']
        if len(raw) != expected:
            item_errors.append('complete TR pool differs from source')
        pool_evidence = {'unit': 'all unique source TR numbers', 'expected_pool': expected, 'actual_pool': len(raw)}
    elif identifier == 'RAN4_P2_CQ2-4':
        sp = audit['identity_audits']['Spec']
        expected = sp['population'] - sum(value - 1 for value in sp['effective_identity_duplicates'].values())
        if len(raw) != expected:
            item_errors.append('complete Spec-number pool differs from source')
        pool_evidence = {'unit': 'all unique source specNumbers', 'expected_pool': expected, 'actual_pool': len(raw)}
    elif identifier == 'RAN3_P2_CQ4-2':
        expected = audit['zte_moderation_lookup']['distinct_agenda_nodes']
        if len(raw) != expected:
            item_errors.append('moderated Agenda pool differs from source')
        pool_evidence = {'unit': 'ZTE moderated Summary-linked Agenda identities', 'expected_pool': expected,
                         'actual_pool': len(raw)}
    elif identifier in {'RAN2_P4_CQ2-4', 'RAN5_P4_CQ2-4'}:
        source = ran2_cr_audit if identifier.startswith('RAN2') else ran5_other_specs
        source_sha = source.get('source_sha256', source.get('graph_source_sha256'))
        expected = source['CR_entities']
        if source_sha != receipt['provenance']['graph_source_sha256'] or len(raw) != expected:
            item_errors.append('complete eligible CR pool differs from full frozen-source identity audit')
        pool_evidence = {'unit': 'all source CR entities, including zero declared-impact counts',
                         'expected_pool': expected, 'actual_pool': len(raw),
                         'source_graph_sha256': source_sha,
                         'metric': 'declared relationship instances' if identifier.startswith('RAN2') else 'distinct declared other Spec numbers'}
    elif identifier == 'RAN5_P4_CQ4-4':
        expected = set(ran5_other_specs['Samsung_all_declared_specNumbers'])
        actual = {record['spec'] for record in projection}
        if actual != expected or receipt['provenance']['graph_source_sha256'] != ran5_other_specs['graph_source_sha256']:
            item_errors.append('Samsung full declared-Spec union differs from full frozen-source scan')
        pool_evidence = {'unit': 'full declared OtherSpecs union for preserved Company-name CONTAINS Samsung scope',
                         'expected_pool': len(expected), 'actual_pool': len(actual),
                         'source_submitting_CR_n': ran5_other_specs['Samsung_CONTAINS_submittingCR_n']}
    elif identifier == 'RAN5_P4_CQ2-1':
        expected = {record['specNumber'] for record in ran5_other_specs['fixedCR_targets']
                    if record['role'].startswith('affects')}
        if {record['spec'] for record in projection} != expected:
            item_errors.append('fixed CR declared OtherSpecs differs from independent source-role scan')
        pool_evidence = {'unit': 'fixed CR declared OtherSpecs form role', 'expected_pool': len(expected),
                         'actual_pool': len(raw),
                         'original_DOCX_member_sha256': ran5_other_specs['original_docx']['member_sha256']}
    elif identifier == 'RAN3_P1_CQ1-9':
        expected = set(meeting130['direct_agendaNumbers'])
        if {record['agendaNumber'] for record in projection} != expected:
            item_errors.append('covered meeting130 Agenda population differs from full source scope scan')
        pool_evidence = {'unit': 'source AgendaItem meetingNumber 130, including Summary-covered agenda2.5',
                         'expected_pool': len(expected), 'actual_pool': len(raw),
                         'old_uncapped_Tdoc_proxy_pool': meeting130['old_uncapped_positive_agenda_nodes']}
    if identifier in maximum_witnesses:
        witness = maximum_witnesses[identifier]
        if receipt['provenance']['graph_source_sha256'] != witness['graph_source_sha256']:
            item_errors.append('maximum source witness graph SHA differs')
        expected_answers = {build.digest(record) for record in witness['maximal_requested_records']}
        actual_answers = {build.digest(record) for record in projection}
        if actual_answers != expected_answers:
            item_errors.append('native maximum/all-ties answer differs from complete frozen-source derivation')
        if 'referenceCount' in receipt['columns']:
            rank_column = receipt['columns'].index('referenceCount')
            if any(row[rank_column] != witness['maximum'] for row in raw):
                item_errors.append('native maximum auxiliary differs from complete frozen-source maximum')
        pool_evidence = {'unit': 'full eligible source frequency pool, including all maximum ties',
                         'source_witness_sha256': sha(maximum_witness_path),
                         'source_pool_n': witness.get('pool_count', len(witness.get('pool', []))),
                         'source_maximum': witness['maximum'],
                         'native_count_auxiliary_present': 'referenceCount' in receipt['columns'],
                         'source_maximum_tie_n': len(expected_answers), 'actual_maximum_tie_n': len(actual_answers)}
    source_context = task['primary_review'].get('source_context', {})
    if wg == 'RAN1' and 'RAN2' in source_context.get('actual_cross_spec_loader_path', ''):
        errata = [row for row in task.get('metadata_errata', [])
                  if row['field'] == 'primary_review.source_context.actual_cross_spec_loader_path']
        if (len(errata) != 1 or errata[0].get('raw_primary_preserved') is not True
                or errata[0].get('definition_sha256_unchanged') is not True
                or errata[0].get('recorded_value') != source_context['actual_cross_spec_loader_path']):
            item_errors.append('irrelevant RAN2 source path lacks exact metadata-only erratum')
        metadata_notes.append({'id': identifier, 'field': 'primary_review.source_context.actual_cross_spec_loader_path',
                               'issue': 'RAN2 cross-spec loader provenance is irrelevant to this RAN1 submitted-CR lookup',
                               'exact_metadata_only_erratum_recorded': len(errata) == 1,
                               'raw_primary_and_nine_key_definition_preserved': True})
    if task['collection']['kind'] == 'top_k_boundary_ties':
        rank_column = task['collection']['source_order_keys'][0]['source_column']
        ranks = [record[receipt['columns'].index(rank_column)] for record in raw]
        if any(not isinstance(value, int) or isinstance(value, bool) for value in ranks):
            item_errors.append('rank auxiliary is not an integer')
        if ranks != sorted(ranks, reverse=True):
            item_errors.append('native rank pool is not descending')
        groups = build.original_scorer.make_order_groups(task, native_records, projection)
        if groups != gold[identifier]['order_groups']:
            item_errors.append('rank group witness differs')
    all_rows += len(raw)
    errors.extend({'id': identifier, 'issue': issue} for issue in item_errors)
    findings.append({'id': identifier, 'repair_sha256': task['repair_sha256'],
                     'status': 'pass' if not item_errors else 'fail', 'rows': len(raw),
                     'requested_field_type_counts': types, 'requested_duplicates_n': projected_duplicates,
                     'strict_recorded_control_n': len(controls[identifier]['checks']),
                     'source_population_witness': pool_evidence,
                     'complete_native_receipt_sha256': receipt['receipt_sha256']})

stable = input_hashes == {str(path): sha(path) for path in paths}
if not stable:
    errors.append({'issue': 'root capture/admission inputs changed during audit; rerun against completed snapshot'})
report = {'kind': 'Separate direct artifact audit; no new rating, model/DB execution or candidate generation',
          'status': 'pass' if not errors else 'fail', 'audited_task_n': len(tasks), 'native_rows_read': all_rows,
          'inputs_stable_during_audit': stable, 'input_file_sha256': input_hashes,
          'checks': findings, 'errors': errors, 'metadata_notes': metadata_notes,
          'expert_validation_n': 0, 'human_author_review_completed': False,
          'scope': 'Checks exact stored definitions, both item AI records, original bytes, query/row/receipt hashes, typed requested projection, strict recorded controls and available direct-source complete-pool sums. Original edition/scope pending items are not converted to pass.'}
out = BASE / 'captured_artifact_independent_audit.json'
out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'path': str(out), 'sha256': sha(out), 'audited_task_n': len(tasks),
                  'native_rows_read': all_rows, 'errors': errors, 'metadata_notes': metadata_notes}, ensure_ascii=False))
