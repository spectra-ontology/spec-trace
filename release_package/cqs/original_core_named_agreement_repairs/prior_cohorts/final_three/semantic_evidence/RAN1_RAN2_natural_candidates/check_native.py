"""Verify the exact native breadcrumb and strict requested sequence controls."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PREP = HERE.parents[2]
sys.path.insert(0, str(PREP))
sys.path.insert(0, str(PREP / 'original_repair'))
import continue_original as implementation


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    output = HERE / 'native_scorer_checks.json'
    assert not output.exists()
    task = implementation.read(HERE / 'candidates.jsonl')[0]
    secondary = implementation.read(HERE / 'secondary.jsonl')[0]
    criteria_path = PREP / 'original_repair/criteria.json'
    criteria = json.loads(criteria_path.read_text())
    assert implementation.digest({key: task[key] for key in implementation.DEFINITION_KEYS}) == task['repair_sha256']
    for review in [task['primary_review'], secondary]:
        implementation.review_schema.check_pass(review, task['question_en'], criteria['semantic_units'],
            criteria_sha=sha(criteria_path), identity_key='repair_sha256', identity_sha=task['repair_sha256'])
    previous = implementation.native.BASE
    try:
        implementation.native.BASE = HERE
        rows, receipt = implementation.native.references({'id': task['id'], 'candidate_query': task['reference_query']})
    finally:
        implementation.native.BASE = previous
    assert rows is not None and len(rows) == 1
    run = json.loads((HERE / 'execution_RAN1.json').read_text())
    assert run['inventory_unchanged'] and run['source_before'] == run['source_after']
    assert run['source_before']['source']['sha256'] == task['source_graph']['sha256']
    witness_path = HERE.parent / 'RAN1_RAN2_natural_edition_witness.json'
    assert sha(witness_path) == task['completeness_witness']['sha256']
    witness = next(row for row in json.loads(witness_path.read_text())['items'] if row['id'] == task['id'])
    expected = [{'breadcrumb': [section['sectionNumber'] for section in row['natural_records'][0]['breadcrumb']]}
                for row in witness['edition_results']]
    assert len(expected) == 5 and all(record == rows[0] for record in expected)
    projected = implementation.native.answer_projection(rows, task['required_fields'], receipt['columns'])
    checks = implementation.checks(task, projected)
    path = projected[0]['breadcrumb']

    def require(name, value):
        result = implementation.original_scorer.score(task, projected, [{'breadcrumb': value}], diagnostic=True)
        checks.append({'check': name, 'pass': result['exact'] is False})

    require('reversed_breadcrumb_order', list(reversed(path)))
    shuffled = path[:]
    shuffled[0], shuffled[1] = shuffled[1], shuffled[0]
    require('shuffled_breadcrumb_order', shuffled)
    require('missing_root_ancestor', path[1:])
    require('duplicate_ancestor', path[:1] + path)
    require('wrong_natural_section_number', path[:-1] + ['__WRONG_SECTION__'])
    require('wrong_nested_element_type', path[:-1] + [5])
    assert all(check['pass'] for check in checks)
    historical = task['original_korean_source']
    phase_path = Path(historical['file'])
    phase = json.loads(phase_path.read_text())
    actual_question = next(row['question'] for row in phase['questions'] if row['id'] == 'CQ003')
    assert actual_question == historical['question_ko']
    errata = {
        'scope': 'Provenance metadata only; candidate definition/question/query/scorer and both semantic judgments are unchanged',
        'candidate_file_sha256': sha(HERE / 'candidates.jsonl'), 'repair_sha256': task['repair_sha256'],
        'historical_phase_source_pin': historical,
        'current_phase_source_pin': {'path': str(phase_path), 'sha256': sha(phase_path)},
        'actual_Korean_question_unchanged': True,
        'preserved_original_context_record': {'path': str(HERE.parent / 'RAN1_RAN2.jsonl'),
            'sha256': sha(HERE.parent / 'RAN1_RAN2.jsonl'), 'id': task['id']},
        'finding': 'The whole currentphase3 file changed after the earlier source audit; the Korean question itself remains identical. HistoricalSHA is preserved as historical and is not asserted to match current file bytes. Original benchmark English/query and frozen graph define task scope; later file metadata/defaults are not authority.',
    }
    errata_path = HERE / 'provenance_errata.json'
    assert not errata_path.exists()
    errata_path.write_text(json.dumps(errata, ensure_ascii=False, indent=2) + '\n')
    result = {'status': 'PASS', 'id': task['id'], 'repair_sha256': task['repair_sha256'],
        'candidate_n': 1, 'native_rows': 1, 'records': projected, 'scorer_controls_n': len(checks),
        'scorer_controls': checks, 'reference_receipt': receipt, 'run_report_sha256': sha(HERE / 'execution_RAN1.json'),
        'all_matching_editions_independent_source_projection_equal': True,
        'full_number_and_title_invariance_source_witness_sha256': sha(witness_path),
        'tool_sha256': sha(__file__), 'candidates_sha256': sha(HERE / 'candidates.jsonl'),
        'secondary_sha256': sha(HERE / 'secondary.jsonl'), 'criteria_sha256': sha(criteria_path),
        'execution_protocol_sha256': sha(HERE / 'execution_protocol.json'),
        'provenance_errata': {'path': str(errata_path), 'sha256': sha(errata_path)},
        'secondary_primary_exposure_disclosed': True, 'blind_review_claim': False,
        'new_admitted_n_by_this_check': 0, 'new_model_calls': 0,
        'human_author_review_completed': False, 'expert_validation_n': 0}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': 'PASS', 'native_rows': 1, 'scorer_controls': len(checks), 'sha256': sha(output)}))


if __name__ == '__main__':
    main()
