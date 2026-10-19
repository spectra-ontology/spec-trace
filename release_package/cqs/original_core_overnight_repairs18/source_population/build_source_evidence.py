#!/usr/bin/env python3
"""Build source evidence only; no runtime, API, native DB or public mutation.

The full fixture is verification evidence, not model prompt/retrieval material.
Preserve prior outputs by passing a fresh --dest for every rebuild.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
N = HERE.parent
R = Path('/home/sihyeon/workspace/spectra')
B = next(p for p in HERE.parents if p.name == 'overnight_reaudit')


def pin(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return dict(bytes=p.stat().st_size, sha256=h.hexdigest())


def load(p):
    return json.loads(p.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dest', type=Path, default=HERE / 'evidence')
    args = parser.parse_args()
    dest = args.dest.resolve()
    assert not dest.exists(), 'use a fresh private output directory'
    assert dest.is_relative_to(N), 'private child outputs only'
    dest.mkdir(parents=True)
    files = {}

    def write(name, value):
        p = dest / name
        with p.open('x') as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.write('\n')
        files[name] = pin(p)

    def copy(source, name):
        target = dest / name
        assert not target.exists()
        shutil.copyfile(source, target)
        assert pin(target) == pin(source)
        files[name] = pin(target)

    scopeP = N / 'loop49_original35_file_scope_population_binding/original35_file_scope_population_binding_receipt.json'
    scope = load(scopeP)
    definitionP = N / 'loop50_CR_proportion_original_source_context_final_review/source_pinned_prospective_original_question_definition.json'
    definition = load(definitionP)
    reviewP = definitionP.parent / 'independent_source_only_seven_unit_review_schema_checked.json'
    review = load(reviewP)
    assert definition['repair_sha256'] == '1fea2e469078260e6542ecd49a411e43b27cc92518bc5200b298202d47b96f3f'
    assert review['repair_sha256'] == definition['repair_sha256']
    sourceP = R / scope['exhaustive_original35_provenance']['compressed']['path']
    assert pin(sourceP) == {k: scope['exhaustive_original35_provenance']['compressed'][k] for k in ('bytes', 'sha256')}
    originalP = B.parents[1] / 'original_repair/final_staging_expanded/release_package/cqs/original_core_repair/provenance/original_benchmark.jsonl'
    original = next(json.loads(l) for l in originalP.read_text().splitlines() if json.loads(l)['id'] == definition['id'])
    copy(definitionP, 'prospective_definition.json')
    copy(reviewP, 'independent_child_source_only_seven_unit_review.json')
    copy(sourceP, 'whole_original35_identifier_type_provenance.jsonl.gz')
    copy(scopeP, 'original35_population_binding_receipt.json')
    copy(definitionP.parent / 'actual_whole_original35_type_to_frozen_field_and_SQL_certificate.json', 'actual_whole_Type_field_SQL_certificate.json')
    copy(N / 'loop47_CR_count_whole_question_scope_and_identity_boundary/all63_CR_only_nodes_exact_source_provenance.json', 'all63_CR_only_nodes_exact_source_provenance.json')
    copy(N / 'loop47_CR_count_whole_question_scope_and_identity_boundary/whole_question_scope_and_identity_boundary_pending_review.json', 'prior_scope_counterreadings_diagnostic.json')
    copy(Path(__file__), 'build_source_evidence.py')
    copy(HERE / 'verify_source_evidence.py', 'verify_source_evidence.py')
    write('original_question_and_query_identity.json', dict(
        id=original['id'], question_en=original['question_en'], original_query=original['cypher'],
        wg=original['wg'], phase=original['phase'],
        original_complete_jsonl_pin=dict(path=str(originalP.relative_to(R)), **pin(originalP)),
        source_row_all_keys=sorted(original), old_gold_not_copied_or_used_to_select_scope=True))
    write('original_design_required_excerpts.json', dict(
        source=scope['inputs']['original_design'],
        extraction='Exact original lines and file hash; surrounding full original is not embedded. Historical Appendix numeric baseline tables are omitted.',
        authority=review['original_source_authority']))
    write('original35_workbook_source_pins.json', dict(
        selection_policy=scope['file_selection_policy'],
        original_design=scope['inputs']['original_design'],
        selected_files=scope['selected_files'],
        selected_families=scope['selected_families'],
        excluded_retained_files=scope['excluded_retained_files'],
        header_sheets_n=scope['header_sheets_n'],
        local_workbook_rehash_in_loop49=True,
        current_builder_does_not_reparse_original_XML=True,
        XML_replay_not_claimed_by_offline_fixture_verifier=True))
    write('four_seven_digit_source_records_schema_defect.json', dict(
        defect='Original constructor admits six digits, but four observed original metadata IDs have seven digits. Preserve their exact recorded identifiers and Type; do not assert official physical identity, collapse aliases or silently fix them.',
        source_records=scope['source_seven_digit_records'],
        original_constructor_excerpt=review['original_source_authority']['dedup_and_unique_identifier_count_units']))
    write('provenance_and_replay_boundaries.json', dict(
        repair_sha256=definition['repair_sha256'],
        source_contract='The current whole frozen Tdoc metadata population is exhaustively bound to the original35 source register identifiers. CR count is the authored Type subset of this same population.',
        interpretation_status='Source-context AI inference; original wording/query are preserved. Independent root semantic/native/scorer gates remain separate.',
        direct_in_loop50=['Whole compressed fixture streamed and IDs/Types compared against immutable whole Tdoc SQL table; both count fields independently recomputed.'],
        reused=['Original XML-authored rows and workbook physical provenance from loop07.', 'Whole35 source fixture and source-to-current-ID binding from loop49.', 'Own-cover and wider-register evidence for all63 CR-only nodes from loop47; no new Word/CFB rendering in this builder.'],
        offline_replay=['Check all embedded file SHA/bytes, decompress full62069-row fixture, verify every original Type and source workbook reference, recompute metadata counts, preserve all four defective IDs and all63 opposing class nodes.'],
        offline_not_replayed=['35 original XLSX/XML files are pinned but not embedded; fixture verification is not an independent original-XML extraction.', 'Raw551MB source authored-row universe,612MB SQLite database, live Cypher execution and CFB conversion are not embedded or executed here. Their hashes/receipts remain linked.', 'Semantic truth and the choice of source context cannot be established by passing hash or numeric equality checks.'],
        source_fixture_not_runtime_input=True,
        runtime_input_policy='Do not add this answer-bearing verification fixture or selected values to model prompts/retrieval. Root controls any evaluation freeze and must disclose actual source availability separately.',
        no_gold_or_historical_numeric_match_as_selection_reason=True,
        original_7digit_defects_and_CR_only_opposition_preserved=True,
        newly_executed_API_native_central_public_git_writes_n=0))
    manifest = dict(kind='minimal_public_source_evidence_candidate', id=definition['id'],
        repair_sha256=definition['repair_sha256'], files=files,
        fixture=dict(file='whole_original35_identifier_type_provenance.jsonl.gz',
            **{k:v for k,v in scope['exhaustive_original35_provenance'].items() if k != 'compressed'}),
        verification_scope='Portable full-fixture evidence replay only; no original XML/native/API claim.',
        candidate_only=True, admission_by_child=False)
    with (dest / 'manifest.json').open('x') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2); f.write('\n')
    print(json.dumps(dict(directory=str(dest), manifest=pin(dest / 'manifest.json'), files_n=len(files), total_bytes=sum(v['bytes'] for v in files.values())), ensure_ascii=False))


if __name__ == '__main__':
    main()
