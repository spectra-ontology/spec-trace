#!/usr/bin/env python3
"""Compile the selected source-defined tasks before any model outcomes.

Original questions/queries and earlier definitions stay in separate inputs.
The explicit amendments here resolve definition defects found in source review;
they are not model-result-based selection or repair of the original benchmark.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compile_tasks(directory):
    sources = [directory / 'prospective_task_variants_RAN1_RAN2_RAN3_v1.json',
               directory / 'prospective_task_variants_RAN4_RAN5_v2.json']
    selection_path = directory / 'prospective_selection_v1.json'
    selection = json.loads(selection_path.read_text())
    items = [item for path in sources for item in json.loads(path.read_text())['items']]
    amendments = []
    for item in items:
        item.setdefault('original_id', item['id'])
        if item.get('task_variant'):
            item.setdefault('variant_id', item['id'] + '__explicit_graph_task')
        question = item.get('task_question')
        if question:
            changed = (question.replace('the 10 CR nodes', 'up to 10 CR nodes')
                       .replace('Choose exactly the first 10', 'Choose up to the first 10')
                       .replace('Return exactly the first five', 'Return up to the first five')
                       .replace('sectionId distinguishes release versions', 'retain the recorded sectionId')
                       .replace('Section IDs distinguish stored versions.', 'Retain the recorded Section IDs.'))
            if changed != question:
                amendments.append({'id': item['id'], 'kind': 'definition',
                                   'reason': 'Do not assume at least k results or unaudited ID uniqueness.'})
                item['task_question'] = changed
        if item['id'] == 'RAN1_P3_CQ014':
            item['task_question'] = item['task_question'].replace(
                'order pairs lexicographically by (sectionIdA,sectionIdB)',
                'order records lexicographically by (sectionIdA,sectionIdB,sectionA,sectionB)')
            item['reference_query'] = item['reference_query'].replace(
                'ORDER BY sectionIdA,sectionIdB LIMIT 20',
                'ORDER BY sectionIdA,sectionIdB,sectionA,sectionB LIMIT 20')
            amendments.append({'id': item['id'], 'kind': 'definition',
                               'reason': 'Complete deterministic ordering even if an endpoint has multiple spec display paths.'})
        if item['id'] == 'RAN3_P3_CQ1-2':
            item['task_question'] = (
                'Within the recorded RAN3 graph, choose the release-specific Spec node for 38.413 '
                'with the highest numeric Rel-N, breaking ties by Spec id ascending. Among its '
                'Sections numbered 9.3.1, choose the first by sectionId ascending. List all immediate '
                'HAS_SUB_SECTION children of that Section. Return sectionId, sectionNumber and '
                'sectionTitle as an unordered set; no child output cap. Retain recorded Section IDs.')
            item['reference_query'] = (
                "MATCH (rk:Spec {specNumber:'38.413'}) WHERE rk.specRelease IS NOT NULL "
                "WITH rk ORDER BY toInteger(replace(rk.specRelease,'Rel-','')) DESC,rk.id ASC LIMIT 1 "
                "MATCH (p:Section {sectionNumber:'9.3.1'})-[:BELONGS_TO_SPEC]->(rk) "
                "WITH p ORDER BY p.sectionId ASC LIMIT 1 "
                "MATCH (p)-[:HAS_SUB_SECTION]->(c:Section) RETURN DISTINCT c.sectionId AS sectionId,"
                "c.sectionNumber AS sectionNumber,c.sectionTitle AS sectionTitle")
            amendments.append({'id': item['id'], 'kind': 'definition',
                               'reason': 'Choose latest Spec independently of parent-section presence, and state parent tie handling.'})
        if item['id'] == 'RAN2_P2_CQ3-3':
            item['task_question'] = item['task_question'].replace(
                'the first five Work Items', 'up to the first five Work Items').replace(
                'linked to at least one TDoc referenced by a Resolution',
                'linked to at least one company-submitted TDoc referenced by a Resolution')
            amendments.append({'id': item['id'], 'kind': 'definition',
                               'reason': 'State the company-submission predicate that defines the Work Item population, and allow fewer than five.'})
        if item['id'] == 'RAN5_P3_P3-S8-CQ02':
            item['task_question'] += ' A node contributes once to each of the listed class labels it bears.'
            item['reference_query'] = (
                "MATCH (n) WHERE n.granularity='item' "
                "UNWIND [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure',"
                "'PerformanceRequirement','ConformanceTest']] AS class "
                "WITH n,class,exists((n)-[:definedInSection]->(:Section)) AS linked "
                "RETURN class,count(n) AS total,sum(CASE WHEN linked THEN 1 ELSE 0 END) AS linked,"
                "round(100.0*sum(CASE WHEN linked THEN 1 ELSE 0 END)/count(n),1) AS link_pct")
            item['source_audit']['reason'] = (
                'Original yes/no task was graded by class identity. This separate diagnostic '
                'variant requires all per-class coverage quantities; multilabel contribution is explicit.')
            amendments.append({'id': item['id'], 'kind': 'definition',
                               'reason': 'Specify per-label contribution rather than arbitrary first-label selection.'})
        for field in item['required_fields']:
            if field['name'] == 'affectedSpecs' and field['type'] == 'json':
                field['json_schema'] = {'type': 'array', 'items': {'type': 'string'}}
            if field['name'] == 'topCompanies' and field['type'] == 'json':
                field['json_schema'] = {
                    'type': 'array', 'items': {'type': 'object',
                    'properties': {'company': {'type': 'string'}, 'count': {'type': 'integer'}},
                    'required': ['company', 'count'], 'additionalProperties': False}}
        item['source_audit']['scope'] = (
            'Formal querying task over the restored deposited WG TTL; independent domain semantics '
            'and original-question validity are not certified.')
    items.sort(key=lambda item: item['id'])
    selected_ids = selection.get('selected_ids') or selection.get('task_ids')
    if selected_ids is None:
        selected_ids = [item['id'] for item in selection.get('items', [])]
    assert len(items) == 40 and len({item['id'] for item in items}) == 40
    assert set(selected_ids) == {item['id'] for item in items}, 'selection changed'
    return {
        'kind': 'prospective explicit task definitions; separate from original SpectraCQ questions',
        'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'input_artifacts': [{'file': path.name, 'sha256': digest(path)} for path in sources],
        'selection_file': selection_path.name, 'selection_sha256': digest(selection_path),
        'selection': selection,
        'eligibility_rule': {
            'frozen_before_model_outcomes': True,
            'require_explicit_task_and_typed_complete_reference_execution': True,
            'reference_timeout_seconds': 30, 'reference_row_cap': 2000,
            'unresolved_error_timeout_or_capped_tasks': 'Retain in all-40 disposition table; no outcome-based replacements.',
            'empty_gold': 'Eligible formal query result, reported separately; not certified missing-evidence abstention.'},
        'amendments': amendments,
        'original_benchmark_modified': False, 'domain_expert_validation': False,
        'all_40_are_original_contract_valid': False,
        'items': items}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = compile_tasks(args.directory)
    with args.output.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print('selected', len(result['items']), 'sha256', digest(args.output))


if __name__ == '__main__':
    main()
