#!/usr/bin/env python3
"""Reopen raw source covers and reproduce the bounded graph repair evidence.

Default mode uses files only. A pinned public Turtle baseline can optionally
reproduce the complete frozen-universe and full-pool evidence. This verifier
does not call a model, contact a network service or open a database.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
from io import BytesIO
from pathlib import Path, PurePosixPath
import re
import sys
from zipfile import ZipFile
from lxml import etree

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
RELATIONS = {'core': 'AFFECTS_CORE_SPEC', 'test': 'AFFECTS_TEST_SPEC', 'om': 'AFFECTS_OM_SPEC'}
PREDICATES = {'core': 'affectsCoreSpec', 'test': 'affectsTestSpec', 'om': 'affectsOmSpec'}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text())


def module(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def check_manifest():
    manifest = load('manifest.json')
    expected = set(manifest['artifacts'])
    actual = {str(path.relative_to(ROOT)) for path in ROOT.rglob('*') if path.is_file()}
    assert actual == expected | {'manifest.json'}, 'Missing or unpinned bundle file'
    for name, pin in manifest['artifacts'].items():
        path = PurePosixPath(name)
        assert not path.is_absolute() and '..' not in path.parts
        data = (ROOT / name).read_bytes()
        assert len(data) == pin['bytes'] and digest(data) == pin['sha256'], name
    return manifest


def check_contract():
    definition = load('contract/definition.json')
    assert digest(definition['question_en'].encode()) == definition['original_question_sha256']
    assert digest(definition['original_query'].encode()) == definition['original_query_sha256']
    assert definition['reference_query'] == definition['original_query']
    assert definition['reference_query_sha256'] == definition['original_query_sha256']
    assert definition['collection'] == {'kind': 'set'}
    assert definition['cardinality_policy'] == {'mode': 'exact', 'value': 10}
    assert definition['required_fields'] == [{'name': 'tdocNumber', 'type': 'string', 'nullable': False,
                                            'source_column_or_expression': 'c.tdocNumber'}]
    assert definition['repair_class'] == 'scorer_only'
    assert definition['data_repair_class'] == 'additive_source_enrichment'
    assert definition['admitted'] is False and definition['expert_validation_n'] == 0
    assert digest((ROOT / 'runtime/criteria.json').read_bytes()) == definition['criteria_sha256']
    criteria = load('runtime/criteria.json')
    schema = module('runtime/review_schema.py', 'portable_review_schema')
    for name in ['reviews/primary.json', 'reviews/secondary.json']:
        review = load(name)
        assert review['definition_file_sha256'] == digest((ROOT / 'contract/definition.json').read_bytes())
        assert review['original_question_sha256'] == definition['original_question_sha256']
        assert review['original_query_sha256'] == definition['original_query_sha256']
        assert review['expert_validation_n'] == 0
        schema.check_pass(review, definition['question_en'], criteria['semantic_units'],
                          criteria_sha=definition['criteria_sha256'], identity_key='repair_sha256',
                          identity_sha=definition['repair_sha256'])
    assert definition['complete_prefix_proof_sha256'] == digest((ROOT / 'proof/source_delta_and_complete_prefix_proof.json').read_bytes())
    assert definition['generic_source_parser_sha256'] == digest((ROOT / 'runtime/source_affected_role_parser.py').read_bytes())
    return definition


def check_function_lineage():
    lineage = load('recipes/function_lineage.json')
    original = (ROOT / 'history/original_full_clone_preparer.py.txt').read_text()
    portable = (ROOT / 'recipes/graph_source_recipe.py').read_text()
    assert digest(original.encode()) == lineage['original_preparer_sha256']
    old = {node.name: ast.get_source_segment(original, node) for node in ast.parse(original).body
           if isinstance(node, ast.FunctionDef)}
    new = {node.name: ast.get_source_segment(portable, node) for node in ast.parse(portable).body
           if isinstance(node, ast.FunctionDef)}
    for name, pin in lineage['unchanged_function_body_sha256'].items():
        assert old[name] == new[name] and digest(new[name].encode()) == pin, name


def source_controls(parser, raw_parts):
    lexical = load('proof/actual_boundary_and_structure_controls.json')['lexical_controls']
    for row in lexical:
        assert parser.named_specs(row['input']) == row['expected'], row['name']
    W = parser.W
    positive = lambda parsed: any('38.473' in field['specs'] for field in parsed['fields'])
    positive_id = next(ident for ident, (_, _, parsed) in raw_parts.items()
                       if any(field['active_value'].startswith('TS38.473CR') for field in parsed['fields']))
    negative_id = next(ident for ident, (_, _, parsed) in raw_parts.items()
                       if ident > positive_id and not positive(parsed))
    pos_xml, pos_styles, parsed = raw_parts[positive_id]
    neg_xml, neg_styles, _ = raw_parts[negative_id]
    core = next(field for field in parsed['fields'] if field['role'] == 'core')

    def cells(tree):
        table = tree.find(W + 'body').findall(W + 'tbl')[core['table_index']]
        return table.findall(W + 'tr')[core['row_index']].findall(W + 'tc')

    def replace(cell, value):
        for child in list(cell):
            if child.tag != W + 'tcPr':
                cell.remove(child)
        run = etree.SubElement(etree.SubElement(cell, W + 'p'), W + 'r')
        etree.SubElement(run, W + 't').text = value
        return run

    def mutate(xml, operation):
        tree = etree.fromstring(xml)
        operation(tree)
        return etree.tostring(tree)

    controls = []

    def check(name, xml, styles, ident, predicate=None, reject=False):
        rejected = False
        try:
            value = parser.parse_parts(xml, styles, ident)
        except (ValueError, StopIteration):
            value, rejected = None, True
        assert rejected if reject else not rejected and predicate(value), name
        controls.append({'name': name, 'pass': True, 'expected_rejection': reject,
                         'rejected': rejected, 'mutation_document_xml_sha256': digest(xml)})

    check('own_active_core_positive', pos_xml, pos_styles, positive_id, positive)
    check('wrong_own_identity_rejected', pos_xml, pos_styles, negative_id, reject=True)

    def strike(tree):
        run = replace(cells(tree)[core['label_column'] + 1], 'TS38.473CR 1676')
        etree.SubElement(etree.SubElement(run, W + 'rPr'), W + 'strike')

    check('struck_own_role_not_active_positive', mutate(pos_xml, strike), pos_styles,
          positive_id, lambda value: not positive(value))

    def delete(tree):
        run = replace(cells(tree)[core['label_column'] + 1], 'TS38.473CR 1676')
        parent = run.getparent()
        parent.remove(run)
        etree.SubElement(parent, W + 'del').append(run)

    check('deleted_own_role_not_active_positive', mutate(pos_xml, delete), pos_styles,
          positive_id, lambda value: not positive(value))
    check('explicit_NO_conflict_rejected', mutate(pos_xml, lambda tree: replace(cells(tree)[core['label_column'] - 1], 'X')),
          pos_styles, positive_id, reject=True)
    check('missing_required_role_rejected', mutate(pos_xml, lambda tree: replace(cells(tree)[core['label_column']], 'Missing role label')),
          pos_styles, positive_id, reject=True)

    def body_only(tree):
        p = etree.SubElement(tree.find(W + 'body'), W + 'p')
        etree.SubElement(etree.SubElement(p, W + 'r'), W + 't').text = 'Normative text mentions TS38.473CR1676'

    check('body_target_cannot_become_affected_role', mutate(neg_xml, body_only), neg_styles,
          negative_id, lambda value: not positive(value))

    def modified_only(tree):
        for table in tree.find(W + 'body').findall(W + 'tbl'):
            for row in table.findall(W + 'tr'):
                table_cells = row.findall(W + 'tc')
                for index, cell in enumerate(table_cells):
                    literal = ''.join(cell.xpath('.//w:t/text()', namespaces={'w': W[1:-1]})).strip()
                    if literal == 'CR' and index:
                        replace(table_cells[index - 1], '38.473')
                        return
        raise AssertionError('Own modified-spec cell absent from fixture')

    check('own_modified_spec_cannot_become_affected_role', mutate(neg_xml, modified_only), neg_styles,
          negative_id, lambda value: not positive(value))
    return {'lexical_n': len(lexical), 'structural_n': len(controls), 'structural': controls, 'all_pass': True}


def check_source(definition):
    packet = load('source/actual_all38_original_own_cover_observations.json')
    observations = packet['observations']
    for name, pin in packet['archives'].items():
        raw = (ROOT / name).read_bytes()
        assert len(raw) == pin['bytes'] and digest(raw) == pin['sha256']
    assert len(packet['archives']) == 6
    parser = module('runtime/source_affected_role_parser.py', 'portable_affected_role_parser')
    original_comparison = load('proof/actual_original_vs_improved_affected_parser_same38_receipt.json')
    assert digest((ROOT / 'authority/original_CR_parser.py.txt').read_bytes()) == original_comparison['original_parser_sha256']
    assert digest((ROOT / 'authority/original_shared_cr_form.py.txt').read_bytes()) == original_comparison['shared_cr_form_sha256']
    assert original_comparison['original_methods_executed'] == ['find_cr_form_table', 'extract_other_specs']
    assert original_comparison['source_CR_covers'] == 38 and original_comparison['source_role_fields'] == 114
    comparisons = {row['tdocNumber']: row for row in original_comparison['all38_actual_results']}
    raw_parts, source_edges = {}, set()
    fields_n = 0
    for row in observations:
        ident = row['tdocNumber']
        assert ident not in raw_parts
        with ZipFile(ROOT / row['archive']) as archive:
            member = archive.read(row['member'])
        assert len(member) == row['member_bytes'] and digest(member) == row['member_sha256']
        with ZipFile(BytesIO(member)) as document:
            xml, styles = document.read('word/document.xml'), document.read('word/styles.xml')
        assert digest(xml) == row['document_xml_sha256'] and digest(styles) == row['styles_xml_sha256']
        parsed = parser.parse_parts(xml, styles, ident)
        comparison = comparisons[ident]
        assert comparison['same_original_member_sha256'] == row['member_sha256']
        assert comparison['archive'] == row['archive'] and comparison['member'] == row['member']
        assert comparison['improved_parser_actual_roles'] == {field['role']: field['specs'] for field in parsed['fields']}
        assert parsed['header_text'] == row['own_header_text']
        assert parsed['header_ids'] == row['own_header_ids'] == [ident]
        for field in parsed['fields']:
            old = next(value for value in row['affected_roles'] if value['role'] == field['role'])
            for key in ['table_index', 'row_index', 'label_column', 'active_value', 'row_xml']:
                assert field[key] == old[key], (ident, field['role'], key)
            assert field['specs'] == old['active_specs']
            assert field['yes'] == old['active_yes_checkbox'] and field['no'] == old['active_no_checkbox']
            source_edges.update((ident, field['role'], spec) for spec in field['specs'])
        fields_n += len(parsed['fields'])
        raw_parts[ident] = xml, styles, parsed
    universe = load('source/all19974_frozen_CR_identity_universe.json')
    assert len(universe) == len({row['subject'] for row in universe}) == len({row['tdocNumber'] for row in universe}) == 19974
    bound = load('source/actual_frozen_universe_tail_receipt.json')['tail_bound']
    tail = [row for row in universe if row['tdocNumber'] >= bound]
    assert {row['tdocNumber'] for row in tail} == set(raw_parts) and len(tail) == 38 and fields_n == 114
    assert tail == load('source/complete_frozen_lexical_tail_identity_and_source_mapping.json')
    role_by_predicate = {name: role for role, name in PREDICATES.items()}
    frozen_edges = {(row['tdocNumber'], role_by_predicate[edge['predicate']], edge['target_specNumber'])
                    for row in tail for edge in row['affected_edges']}
    added, removed = source_edges - frozen_edges, frozen_edges - source_edges
    expected_diff = load('proof/all_role_edge_diff.json')
    transform = lambda triples: [{'tdocNumber': ident, 'role': role, 'specNumber': spec} for ident, role, spec in sorted(triples)]
    assert sorted(expected_diff['added'], key=lambda row: (row['tdocNumber'], row['role'], row['specNumber'])) == transform(added)
    assert sorted(expected_diff['removed'], key=lambda row: (row['tdocNumber'], row['role'], row['specNumber'])) == transform(removed)
    assert len(frozen_edges) == 46 and len(source_edges) == 48 and len(added) == 2 and not removed
    assert set(comparisons) == set(raw_parts)
    recorded_original_edges = {(ident, role, spec) for ident, comparison in comparisons.items()
                               for role, specs in comparison['original_parser_actual_roles'].items() for spec in specs}
    assert recorded_original_edges == frozen_edges
    assert original_comparison['changed_CR_covers'] == original_comparison['changed_role_fields'] == 2
    proof = load('proof/source_delta_and_complete_prefix_proof.json')
    canonical_targets = proof['canonical_targets_for_all_source_specs']
    subjects = {row['tdocNumber']: row['frozen_subject'] for row in observations}
    actual_added = [[subjects[ident], RELATIONS[role], canonical_targets[spec]['canonical_hub_iri']]
                    for ident, role, spec in sorted(added)]
    assert actual_added == proof['actual_added_edges'] and proof['actual_removed_edges'] == []
    target = re.search(r"specNumber: '([^']+)'", definition['original_query']).group(1)
    source_positive = {ident for ident, _, spec in source_edges if spec == target}
    prefix = sorted(source_positive, reverse=True)[:definition['cardinality_policy']['value']]
    assert prefix == proof['source_first10_identity']
    assert prefix == [row[0] for row in proof['enriched_original_query_independent_rows']]
    assert min(prefix) >= bound and all(row['tdocNumber'] < bound for row in universe if row['tdocNumber'] not in raw_parts)
    native = load('proof/actual_native_original_two_column_capture.json')
    assert native['selected']['literal_query'] == definition['original_query']
    assert native['selected']['rows'] == proof['enriched_original_query_independent_rows']
    assert native['selected']['row_n'] == 10 and native['whole_matching_pool']['row_n'] == 354
    assert native['selected']['complete'] and not native['selected']['truncated']
    native_manifest = load('proof/actual_native_manifest.json')
    assert native_manifest['source']['sha256'] == definition['new_snapshot_sha256']
    assert native_manifest['loader']['sha256'] == digest((ROOT / 'runtime/load_released_kg.py').read_bytes())
    assert native_manifest['capture']['sha256'] == digest((ROOT / 'proof/actual_native_original_two_column_capture.json').read_bytes())
    controls = source_controls(parser, raw_parts)
    return {'raw_archives': 6, 'raw_own_covers': 38, 'own_affected_role_fields': fields_n,
            'frozen_CR_universe': len(universe), 'all_potential_entrants': len(tail), 'old_tail_role_edges': len(frozen_edges),
            'source_tail_role_edges': len(source_edges), 'derived_added_edges': len(added), 'removed_edges': len(removed),
            'target_positive_covers': len(source_positive), 'target_negative_covers': len(raw_parts) - len(source_positive),
            'source_prefix_equals_exact_authored_selected10': True, 'controls': controls}


def verify(base_ttl=None):
    manifest = check_manifest()
    definition = check_contract()
    check_function_lineage()
    source = check_source(definition)
    full = False
    if base_ttl is not None:
        recipe = module('recipes/graph_source_recipe.py', 'portable_full_graph_recipe')
        recipe.complete_base_proof(base_ttl)
        full = True
    return {'status': 'PASS', 'bundle_manifest_sha256': digest((ROOT / 'manifest.json').read_bytes()),
            'bundle_artifacts': len(manifest['artifacts']), 'source': source,
            'recorded_AI_reviews': 2, 'units_per_AI_review': 7, 'human_expert_validation_n': 0,
            'actual_optional_full_base_replay': full, 'recorded_native_and_SQL_proof_only_in_default_mode': True,
            'original_560_admissions': 0, 'new_model_native_SQL_calls': 0, 'public_operational_mutations': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-ttl', type=Path)
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    result = verify(args.base_ttl)
    if args.receipt is not None:
        assert not args.receipt.exists()
        args.receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
