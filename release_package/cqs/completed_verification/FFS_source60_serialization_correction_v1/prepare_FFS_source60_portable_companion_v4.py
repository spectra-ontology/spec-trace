#!/usr/bin/env python3
"""Build a separate FFS contract over the byte-preserved source60 dependency.

Spec: exact RAN1_P2_CQ1-5 with full4635 native records and14 actual controls.
Ontology: Agreement FFS marker, Agenda order and own reported Meeting periods.
Cycle: completed root gate to portable source companion; frozen pending unchanged.
배경: reuse authentic192 front8 windows without asserting complete report text.
사용: run only after the root full native/SQL/control gate completes.
LLM 호출: none; no provider, graph container, central or public write here.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
B = HERE.parent
TASK = B.parents[1]
WORK = HERE / 'P2_CQ1_5_original_FFS_marker_calendar_source_variant_v1'
PRIOR = B / 'RAN3_RAN4/source60_portable_public_patch_v1'
OUT = HERE / 'FFS_source60_portable_companion_v4'

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''): h.update(block)
    return h.hexdigest()

def save(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as f: json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')

def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    assert not dst.exists()
    shutil.copy2(src, dst)

def main():
    assert not OUT.exists()
    assert sha(PRIOR / 'manifest.json') == '90efdbdb3537e270ac3686e1d04167d4b1561f56012cabf32d384af55c7f5823'
    gate_path = WORK / 'actual_complete_native_SQL_and14_controls_gate_v3.json'
    gate = json.loads(gate_path.read_text())
    assert gate['status'] == 'source_variant_execution_and_semantic_gates_complete'
    assert gate['all_actual_controls_pass'] and gate['actual_controls_n'] == 14 and gate['full_native_SQL_rows_n'] == 4635
    OUT.mkdir()
    prior = json.loads((PRIOR / 'manifest.json').read_text())
    for item in prior['files']:
        src = PRIOR / item['path']
        assert sha(src) == item['sha256'] and src.stat().st_size == item['bytes']
        copy(src, OUT / 'calendar_source_patch' / item['path'])
    copy(PRIOR / 'manifest.json', OUT / 'calendar_source_patch/manifest.json')
    for src in (WORK / 'source_only_independent_review_v1').iterdir():
        assert src.is_file()
        copy(src, OUT / 'original_context' / src.name)
    for name in ('score_predictions.py', 'scorer.py', 'typed_values.py', 'original_scorer.py', 'source_pins.json', 'contract_checks.py'):
        copy(PRIOR / 'evaluation' / name, OUT / 'evaluation' / name)
    for name in ('review_schema.py', 'criteria.json'):
        copy(TASK / 'original_repair' / name, OUT / 'evaluation' / name)
    definition = json.loads(Path(gate['definition_pin']['path']).read_text())
    task = dict(definition, validation_status='validated')
    (OUT / 'evaluation/tasks.jsonl').write_text(json.dumps(task, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')
    copies = {
        'evaluation/reference_gold.jsonl': gate['full_projected_gold_pin']['path'],
        'evaluation/actual14_controls.json': gate['controls_input_pin']['path'],
        'evaluation/full_uncapped_SQL.sql': WORK / 'full_SQL_native_gate_inputs_v1/independent_full_FFS_calendar_SQL.sql',
        'evidence/full_native_all4635_records.jsonl': gate['native_all_fields_records_pin']['path'],
        'evidence/root_independent_full_SQL_all4635_records.jsonl': gate['root_independent_SQL_records_pin']['path'],
        'evidence/actual_complete_gate.json': gate_path,
        'evidence/actual_full_native_capture.json': gate['actual_full_native_pin']['path'],
        'evidence/preserved_failed_native_attempt_v1.json': WORK / 'root_native_capture_adapter_v1/root_actual_queries_v1/full_queries.json',
        'evidence/preserved_failed_native_attempt_v2.json': WORK / 'root_native_capture_adapter_v1/root_actual_queries_v2/full_queries.json',
        'evidence/root_only_native_capture_reader.py': HERE / 'capture_P2_CQ1_5_calendar_FFS_Agreement_full_native_v1.py',
        'evidence/actual_complete_gate_reader.py': HERE / 'verify_P2_CQ1_5_actual_calendar_native_SQL_and14_controls_v3.py',
        'evidence/root_independent_SQL_receipt.json': gate['actual_root_independent_SQL_receipt_pin']['path'],
        'evidence/root_independent_SQL_preregistration.json': B / 'root_evidence/FFS_source60_Meeting_first_SQL_preregistration_v1.json',
        'evidence/predeclared_missing_key_invariance_plan.json': WORK / 'predeclared_missing_secondary_key_boundary_invariance_plan_v1.json',
        'evidence/actual_missing_key_invariance_receipt.json': WORK / 'actual_predeclared_missing_secondary_key_boundary_invariance_receipt_v1.json',
        'evidence/all21058_unfiltered_marker_default_calendar_operands.jsonl': WORK / 'all21058_unfiltered_Agreement_marker_default_key_and_calendar_operands.jsonl',
        'evidence/independent_whole_operand_and_hazard_source_receipt.json': B / 'RAN2_RAN5/RAN1_FFS_original_source_whole_operand_and_bounded_default_key_independent_check_v1.json',
    }
    for rel, src in copies.items(): copy(Path(src), OUT / rel)
    for review in gate['exact_two_reviews']:
        src = Path(review['pin']['path'])
        assert sha(src) == review['pin']['sha256']
        copy(src, OUT / f"evidence/{review['role']}_exact_original_semantic_review.json")
    template_path = HERE / 'prepare_Qualcomm_source60_portable_companion_v1.py'
    spec = importlib.util.spec_from_file_location('preserved_source60_companion_verifier_template', template_path)
    template = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(template)
    verifier = template.VERIFIER
    for before, after in [('Qualcomm', 'FFS-marker'), ('1094', '4635'), ('actual15_controls.json', 'actual14_controls.json'), ('len(controls)==15', 'len(controls)==14'), ("'actual_controls_n':15", "'actual_controls_n':14"), ('all_three_native_and_root_SQL_fields_and_order_equal', 'all_five_native_and_root_SQL_fields_and_order_equal'), ("c['input_records']", "c['predictions']"), ("c['actual']", "c['actual_diagnostic']")]:
        verifier = verifier.replace(before, after)
    verifier = verifier.replace('documentary attribution plus source-reported Meeting periods.', 'retained FFS marker, Agenda order and source-reported Meeting periods.')
    verifier = verifier.replace("    assert len(native)==len(root_sql)==4635 and native==root_sql", "    assert len(native)==len(root_sql)==4635 and native==root_sql\n    assert all(set(r)=={'resolutionId','content','meetingPeriodEndDate','agendaNumber','sequence'} for r in native)\n    actual_gate=load(HERE/'evidence/actual_complete_gate.json')\n    assert actual_gate['status']=='source_variant_execution_and_semantic_gates_complete' and actual_gate['all_five_fields_multiset_and_presentation_order_equal'] is True\n    assert sha(HERE/'evidence/actual_complete_gate.json')==manifest['actual_complete_gate_sha256']")
    assert 'Qualcomm' not in verifier and '1094' not in verifier and 'actual15' not in verifier
    compile(verifier, str(OUT / 'verify_companion.py'), 'exec')
    (OUT / 'verify_companion.py').write_text(verifier)
    copy(Path(__file__), OUT / 'evidence/companion_preparation_reader.py')
    copy(template_path, OUT / 'evidence/preserved_verifier_template_reader.py')
    (OUT / 'README.md').write_text('''# Separate FFS-marker Agreement calendar companion

This unchanged question asks for recent agreements carrying an FFS marker. The contract evaluates retained marker presence and authentic own reported Meeting periods. It does not establish present-world issue finality, complete physical report extraction, or truth of optional explanatory prose.

The source60 dependency is preserved byte for byte under `calendar_source_patch/`, manifest `90efdbdb3537e270ac3686e1d04167d4b1561f56012cabf32d384af55c7f5823`, also published at `release_package/cqs/original_core_source_Meeting_calendar60/portable_patch`. It supplies60 Meeting periods from exactly eight authored paragraphs of each of192 report members. These windows include every supporting period witness; they are not complete report bodies. Parsed dates, reference queries, gold and reviews are excluded from model retrieval.

This companion contains all4,635 native records and all five returned fields, rank groups, two AI judgments, root independent SQL and14 actual typed controls. Required answer role is Agreement identity. Original list10, AgendaASC and sequenceASC follow event-date recency. Equal complete-key boundary records are interchangeable. All147 missing-sequence records remain in the full reference; their latest event is older than at least ten complete-key records, so unspecified NULL placement cannot affect the requested top10. No general NULL convention is inferred.

Run `python -B verify_companion.py` for exact payload/source/contract/control replay. `--existing-sql <source60 RAN1.sqlite>` checks all five fields and order of every record. Alternatively pass `--base-sql <frozen RAN1.sqlite> --base-ttl <frozen RAN1-body.ttl> --rebuild-dir <new directory>` to rebuild the preserved calendar dependency and check this contract. The dependency preserves every original column in all89 tables and the original RDF byte prefix. Neither verifier invokes a provider or graph container.

The frozen original remains pending; this separate source variant is not added to the frozen index. These are nonblind AI development judgments, with no human author review or expert validation. Paid model outputs belong to a separate retained evaluation. Historical absolute paths are immutable provenance; payload and dependency files use relative hash-pinned paths.
''')
    files = [{'path': str(p.relative_to(OUT)), 'sha256': sha(p), 'bytes': p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file()]
    assert not any('__pycache__' in x['path'] or x['path'].endswith('.pyc') for x in files)
    save(OUT / 'manifest.json', {'kind': 'Separate FFS-marker Agreement source60 companion', 'id': task['id'], 'repair_sha256': task['repair_sha256'], 'actual_complete_gate_sha256': sha(gate_path), 'reused_calendar_dependency': {'path': 'calendar_source_patch/manifest.json', 'manifest_sha256': sha(PRIOR / 'manifest.json'), 'payload_bytes_unchanged': True, 'original_case_id': 'RAN1_P3_CQ017', 'published_dependency_path': 'release_package/cqs/original_core_source_Meeting_calendar60/portable_patch'}, 'required_fields': ['resolutionId'], 'auxiliary_fields': ['content', 'meetingPeriodEndDate', 'agendaNumber', 'sequence'], 'full_native_population_n': 4635, 'actual_controls_n': 14, 'raw_report_n': 192, 'raw_paragraph_window_n': 8, 'whole_report_body_equivalence_claimed': False, 'frozen_original_question_status': 'pending', 'frozen_original_index_modified_or_merged': False, 'human_author_review_completed': False, 'expert_validation_n': 0, 'child_API_native_public_calls_n': 0, 'files': files})
    print(json.dumps({'path': str(OUT), 'manifest_sha256': sha(OUT / 'manifest.json'), 'payload_files_n': len(files), 'payload_bytes': sum(x['bytes'] for x in files)}))

if __name__ == '__main__': main()
