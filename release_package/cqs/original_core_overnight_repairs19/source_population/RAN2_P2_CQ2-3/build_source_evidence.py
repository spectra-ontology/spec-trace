#!/usr/bin/env python3
"""Build bounded original-source evidence; never add it to model inputs."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
N = HERE.parent
D = N / 'loop56_RAN2_comeback_whole_rank_source_frontier'
G = N / 'loop57_RAN2_comeback_exact_schema_gate'
ROOT = next(p for p in HERE.parents if (p / 'CLAUDE.md').is_file())
B = next(p for p in HERE.parents if p.name == 'overnight_reaudit')
REPAIR = B.parents[1] / 'original_repair'
IDENTITY = '59abc20c9f7da50b8bf77b9238169a5a70e0d064f28347a7154ec882a8204abc'


def pin(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return {'bytes': Path(path).stat().st_size, 'sha256': h.hexdigest()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dest', type=Path, default=HERE / 'evidence')
    args = ap.parse_args()
    dest = args.dest.resolve()
    assert dest.is_relative_to(N.resolve()) and not dest.exists()
    dest.mkdir(parents=True)
    files, compressed, provenance = {}, {}, {}

    def copy(src, name):
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        assert not target.exists()
        shutil.copyfile(src, target)
        assert pin(src) == pin(target)
        files[name] = pin(target)
        provenance[name] = {'source_path': str(Path(src).resolve()), **pin(src), 'method': 'byte_identical_copy'}

    def compress(src, name):
        target = dest / name
        with target.open('xb') as raw:
            with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as out:
                with Path(src).open('rb') as inp:
                    shutil.copyfileobj(inp, out)
        files[name] = pin(target)
        compressed[name] = {'uncompressed': pin(src)}
        provenance[name] = {'source_path': str(Path(src).resolve()), **pin(src), 'method': 'lossless_gzip_mtime0_no_row_or_value_projection'}

    def write(name, value):
        with (dest / name).open('x') as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.write('\n')
        files[name] = pin(dest / name)

    definition = json.loads((G / 'source_pinned_prospective_original_question_definition.json').read_text())
    assert definition['repair_sha256'] == IDENTITY
    copy(G / 'source_pinned_prospective_original_question_definition.json', 'prospective_definition.json')
    copy(G / 'independent_source_only_seven_unit_review_schema_checked.json', 'independent_child_seven_unit_review.json')
    copy(G / 'source_packet_manifest.json', 'original_absolute_source_packet_manifest_for_provenance.json')
    copy(G / 'actual_canonical_definition_and_secondary_schema_receipt.json', 'canonical_schema_check_receipt.json')
    copy(G / 'actual_packet_pin_and_extra_boundary_witness_receipt.json', 'extra_boundary_and_source_pin_receipt.json')
    copy(D / 'actual_source_frontier_replay_receipt.json', 'fresh_protected_source_replay_receipt.json')
    copy(D / 'actual_six_original_archive_member_binding_receipt.json', 'original_six_archive_binding_receipt.json')
    copy(D / 'whole272_cutoff_dependency_and_order_roles.json', 'whole272_cutoff_and_order_roles.json')
    copy(D / 'all10_latest_original_Agreement_direct_source_role_reviews.json', 'manual10_source_roles.json')
    copy(D / 'actual_original_CQ2_3_category_and_default_Spec_link_supplement.json', 'original_category_default_Spec_binding.json')
    copy(D / 'actual177_occurrence_boundary_audit_receipt.json', 'actual177_source_boundary_audit_receipt.json')
    copy(B / 'RAN2_RAN5/RAN2_P2_CQ2-1_original_documentary_default10_source_only_v3/indexed_complete_original_design.md', 'original_complete_design.md')
    copy(B / 'RAN2_RAN5/RAN2_P2_CQ2-6_original_FFS_marker_source_only_v1/indexed_validation.md', 'original_validation.md')
    copy(B / 'RAN2_RAN5/RAN2_P2_CQ2_3_comeback_original_source_challenge_v2/original_content_pattern_and_authentic_aftercomeback_boundary_packet.json', 'older_Aftercomeback_and_document_leakage_counterexample.json')
    compress(N / 'loop05_RAN2_FFS_rank_prefix_source_dependency_v1/whole_frozen3413_neutral_rank_inputs.jsonl', 'whole_frozen3413_neutral_rank_inputs.jsonl.gz')
    compress(D / 'all3413_frozen_rank_and_source_alignment_diagnostics.jsonl', 'whole3413_source_alignment_diagnostics.jsonl.gz')
    compress(D / 'all5050_source_candidate_lexical_observations_not_membership.jsonl', 'whole5050_source_candidate_observations_not_membership.jsonl.gz')
    compress(D / 'all_six_report_unfiltered_Agreement_candidate_source_panels.jsonl', 'whole483_six_report_unfiltered_source_panels.jsonl.gz')
    compress(D / 'all177_whole_source_occurrence_styled_document_boundary_audit.jsonl', 'all177_source_occurrence_boundary_audit.jsonl.gz')
    copy(REPAIR / 'criteria.json', 'criteria.json')
    copy(REPAIR / 'review_schema.py', 'review_schema.py')
    copy(Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/cqs/original_core_repair/typed_values.py'), 'typed_values.py')
    copy(Path(__file__), 'build_source_evidence.py')
    copy(HERE / 'verify_source_evidence.py', 'verify_source_evidence.py')
    binding = json.loads((D / 'actual_six_original_archive_member_binding_receipt.json').read_text())
    replay = json.loads((D / 'actual_source_frontier_replay_receipt.json').read_text())
    by_meeting = {r['source_meeting']: r for r in replay['reports']}
    archives = []
    for row in binding['reports']:
        src = Path(row['original_archive']['path'])
        assert pin(src) == {k: row['original_archive'][k] for k in ('bytes', 'sha256')}
        name = 'original_archives/' + src.name
        copy(src, name)
        archives.append({
            'meeting': row['source_meeting'], 'archive_file': name,
            'original_archive_relative_to_source_root': str(src.relative_to(ROOT)),
            'original_archive_pin': pin(src),
            'all_member_inventory': row['all_member_inventory'],
            'exact_report_member': row['exact_report_member'],
            'retained_report_relative_to_source_root': str(Path(row['retained_report']['path']).relative_to(ROOT)),
            'retained_report_pin': {k: row['retained_report'][k] for k in ('bytes', 'sha256')},
            'word_document_XML': by_meeting[row['source_meeting']]['word_document_XML'],
            'protected_body_table_paragraphs_n': by_meeting[row['source_meeting']]['whole_body_table_paragraphs_n'],
        })
    write('original_six_archive_portable_locators.json', archives)
    write('provenance_and_replay_boundaries.json', {
        'repair_sha256': IDENTITY,
        'source_scope': 'Original3413 graph-relative Agreement records; default10 selection. Not all physical source Agreement events.',
        'direct_in_this_builder': 'Byte-check and copy all six original archives and exact prior immutable source evidence; no Word transformation.',
        'portable_replay': 'All file SHA/bytes; exact six archive inventories/CRC/member and document.xml; independent standard-library body/table traversal; all3413 captured rows and all272 source predicate dependencies; ten source quotes, four conditional roles, cutoff and sequence disagreements.',
        'optional_source_root_replay': 'Use --source-root PATH to independently reopen the exact original archive paths and compare every retained DOCX byte pin. This does not execute the protected production renderer.',
        'prior_protected_replay_reused': 'Current protected renderer whole74811 body/table paragraphs in six reports is pinned in fresh_protected_source_replay_receipt.json. Its tree, final/marked/tracked extraction and whole-stream hash are not rerun by the stdlib portable verifier.',
        'raw_XML_vs_protected_limit': 'Raw XML paragraph text is independently checked for the exact word predicate and ten plain quote witnesses, not advertised as a replacement for rich field/equation/drawing rendering. Every raw w:p includes nested drawing paragraphs and need not equal body/table paragraph enumeration.',
        'semantic_judgments_not_verified_by_hashes': True,
        'opposing_interpretation_and_conditionality_preserved': True,
        'old_sequence_not_certified': True,
        'verification_fixture_not_prompt_or_retrieval_input': True,
        'model_outputs_or_gold_used_n': 0,
        'API_native_central_public_git_mutations_n': 0,
    })
    write('copied_source_provenance.json', provenance)
    manifest = {
        'id': definition['id'], 'repair_sha256': IDENTITY,
        'kind': 'portable_original_source_evidence_candidate_not_model_input_or_admission',
        'files': files, 'lossless_compressed_files': compressed,
        'scope': {'whole_original_Agreement_records': 3413, 'latest_unfiltered_dependency': 272,
                  'six_source_panels': 483, 'whole_source_candidate_observations': 5050,
                  'source_occurrences': 177, 'manual_effective_flags': 10, 'conditional_reopeners': 4},
        'source_root_is_optional': True,
    }
    with (dest / 'manifest.json').open('x') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({'directory': str(dest), 'manifest': pin(dest / 'manifest.json'),
                      'files_n': len(files), 'total_bytes': sum(x['bytes'] for x in files.values())}))


if __name__ == '__main__':
    main()
