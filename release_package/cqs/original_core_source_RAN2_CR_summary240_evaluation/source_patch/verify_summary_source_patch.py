#!/usr/bin/env python3
"""Replay a separate source-summary contract and saved source/native evidence.

Does not query databases, render Word documents, call a provider, or certify
TSG approval. Original archives and renderer pins remain external provenance.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
DEFINITION_KEYS = ('id', 'question_en', 'original_query', 'reference_query',
                  'required_fields', 'collection', 'cardinality_policy',
                  'repair_class', 'original_question_preserved')
def load(p): return json.loads(p.read_text())
def rows(p): return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def canonical(v): return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(2 ** 20), b''): h.update(b)
    return h.hexdigest()


def verify(base):
    manifest = load(base / 'manifest.json')
    actual = {str(p.relative_to(base)) for p in base.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    assert actual == set(manifest['files'])
    for name, pin in manifest['files'].items():
        p = (base / name).resolve()
        assert p.is_relative_to(base) and sha(p) == pin['sha256'] and p.stat().st_size == pin['bytes'], name
    sys.path.insert(0, str(base / 'evaluation'))
    import scorer
    import original_scorer
    import contract_checks
    import review_schema
    task, = rows(base / 'evaluation/tasks.jsonl')
    gold_row, = rows(base / 'evaluation/reference_gold.jsonl')
    original = load(base / 'evidence/unchanged_source_definition.json')
    definition = {k: task[k] for k in DEFINITION_KEYS}
    assert definition == {k: original[k] for k in DEFINITION_KEYS}
    assert hashlib.sha256(scorer.get_kernel().json_exact(definition).encode()).hexdigest() == task['repair_sha256']
    assert task['validation_status'] == 'validated' and task['required_fields'] == [{'name': 'summary', 'type': 'string', 'nullable': False, 'source_column_or_expression': 'summary'}]
    assert task['collection'] == {'kind': 'multiset'} and task['cardinality_policy'] == {'mode': 'all'}
    assert gold_row['repair_sha256'] == task['repair_sha256'] and gold_row['id'] == task['id']
    gold = gold_row['records']; native = rows(base / 'evidence/full_native_records.jsonl')
    sql = rows(base / 'evidence/full_SQL_records.jsonl'); source = rows(base / 'evidence/primary_source_summary_rows.jsonl')
    assert native == sql and len(source) == len(gold) == len(native) == manifest['source_occurrences_n']
    assert [{'summary': r['summary']} for r in native] == gold
    assert Counter(r['sourceAuthoredSummary'] for r in source) == Counter(r['summary'] for r in gold)
    assert len({r['tdocNumber'] for r in source}) == len(source)
    receipt = load(base / 'evidence/historical_native_query_receipts.json')
    query = next(q for q in receipt['queries'] if q['name'] == 'full_source_question')
    assert query['query'] == task['reference_query']
    assert receipt['status'] == 'complete_native_SQL_authored_summary_match'
    assert query['full_rows_available'] and query['rows'] == len(native)
    assert query['rollback_completed'] and query['read_plan'] and query['read_execution']
    assert query['records_sha256'] == sha(base / 'evidence/full_native_records.jsonl')
    criteria = load(base / 'evaluation/criteria.json')
    root_review = load(base / 'evidence/fresh_root_review.json')
    agent_review = load(base / 'evidence/fresh_agent_review.json')
    # Review adapters are the exact locally checked lossless projections.
    for review in (root_review, agent_review):
        review_schema.check_pass(review, task['question_en'], criteria['semantic_units'],
            criteria_sha=sha(base / 'evaluation/criteria.json'), identity_key='repair_sha256', identity_sha=task['repair_sha256'])
        assert review['expert_validation_n'] == 0 and not review['human_author_review_completed']
    assert root_review['reviewer_kind'] != agent_review['reviewer_kind']
    basic = contract_checks.checks(task, gold)
    assert len(basic) == 7 and all(x['pass'] for x in basic)
    old_rows = rows(base / 'evidence/preserved_original_query_rows.jsonl')
    old = [{'summary': r['c.summaryOfChange'] if manifest['wg'] == 'RAN3' else r['summary']} for r in old_rows]
    changed = lambda v: [dict(gold[0], summary=v)] + gold[1:]
    unique = list({canonical(r): r for r in gold}.values())
    assert len(unique) < len(gold)
    cases = [('all_summary_occurrences', gold, True), ('any_display_order', list(reversed(gold)), True),
        ('auxiliary_ID_relabelled_and_not_required', [dict(r, sourceTdocNumber='unscored auxiliary') for r in gold], True),
        ('JSON_escape_round_trip', json.loads(json.dumps(gold, ensure_ascii=True)), True),
        ('deduplicated_summary_text_omits_CR_occurrences', unique, False),
        ('one_missing_occurrence', gold[:-1], False), ('one_extra_occurrence', gold + [gold[0]], False),
        ('wrong_summary_value', changed('invalid unrelated summary'), False),
        ('null_required_summary', changed(None), False), ('integer_required_summary', changed(12), False),
        ('wrong_required_field', [{'content': r['summary']} for r in gold], False),
        ('prior_incomplete_original_query', old, False),
        ('old_frozen_values_without_source_recovery', [{'summary': r['frozen_summaryOfChange']} for r in source], False)]
    last = [dict(r) for r in gold]
    if manifest['wg'] == 'RAN2':
        i = next(i for i, r in enumerate(native) if r['sourceTdocNumber'] == 'R2-2508568')
        last[i]['summary'] = last[i]['summary'].split('\n')[0]
        cases.append(('nested_source_table_content_omitted', last, False))
    else:
        i = next(i for i, r in enumerate(native) if r['sourceTdocNumber'] == 'R3-240941')
        assert '⇒' in last[i]['summary']
        last[i]['summary'] = last[i]['summary'].replace('⇒', '')
        cases.append(('source_Symbol_implication_lost', last, False))
    historical = load(base / 'evidence/historical_controls.json')
    saved = {r['name']: r for r in historical['source_content_controls']}
    for name, prediction, exact in cases:
        result = original_scorer.score(task, gold, prediction, diagnostic=True)
        assert result['exact'] is exact and result == saved[name]['actual_score'], name
    imported = load(base / 'graph/original_native_import_manifest.json')
    assert sha(base / 'graph/additive_source_property_delta.ttl') == imported['delta']['sha256']
    assert imported['base_bytes_preserved_as_exact_prefix']
    return {'status': 'PASS', 'id': task['id'], 'source_occurrences_n': len(source),
        'unique_literal_summaries_n': len(unique), 'files_verified_n': len(actual),
        'strict_basic_controls_n': len(basic), 'actual_source_mutation_controls_n': len(cases),
        'native_full_records_and_saved_SQL_and_saved_source_values_equal': True,
        'fresh_exact_semantic_reviews_n': 2, 'human_expert_reviews_n': 0,
        'new_provider_calls_n': 0, 'native_execution_replayed': False,
        'original_source_extraction_replayed': False,
        'limits': 'Checks retained literal source values and native/SQL receipts, definitions, AI development review schemas, and scorer corruptions. Original Word rendering/extraction and live graph/SQL require external pinned inputs and are not rerun.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--patch', type=Path, default=Path(__file__).resolve().parent)
    print(json.dumps(verify(parser.parse_args().patch.resolve()), ensure_ascii=False))
