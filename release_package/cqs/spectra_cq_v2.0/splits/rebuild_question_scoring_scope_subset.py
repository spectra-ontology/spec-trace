#!/usr/bin/env python3
"""Check stored AI question/scoring judgments and their fixed intersection.

This checks source bytes, the fixed score-blind input, verbatim evidence anchors,
the recorded four-axis rule and the shipped IDs. It does not repeat the AI
review, establish that its judgments are true, or certify expert validation,
domain correctness or representativeness. Predictions and scores are not read.
A recorded freeze timestamp is metadata, not independent proof of chronology.
Original questions, answer keys and existing split memberships stay unchanged.
"""
import argparse
from collections import Counter
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re
import sys


CQ = Path(__file__).resolve().parent.parent
SCHEMA = 'spectras-question-scoring-scope-v1'
PROTOCOL_SHA256 = '5a932a00d86a5ff840e9e689e6c5a3db7a437b8b32a648406b9b4a7987cdd1e3'
INPUT_SHA256 = '8b879006861610a1daba80690d7b1eb2059ad33ed8081185544e50ba6ce0b4cb'
SOURCE_NAMES = {
    'benchmark.jsonl',
    'core_answer_gold.jsonl',
    'splits/contract_exact_script_fixed_133.txt',
}
CANDIDATE_N = 133
REVIEWERS = {'a', 'b'}
REVIEWER_TYPE = 'fresh isolated Codex AI agent; not human expert'
AXES = (
    'required_fields',
    'scope_and_roles',
    'cardinality_and_truncation',
    'ordering_and_duplicates',
)
STATUSES = {'compatible', 'incompatible', 'unclear'}
SCORING_DEFINITION = (
    'Normalised unordered set of values in the declared answer column; other '
    'fields, row order and duplicates are not graded.'
)
RECORD_NAME = 'question_scoring_scope_review.json'
IDS_NAME = 'splits/question_scoring_scope_reviewed_ids.txt'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(value):
    """The fixed input serialization, including its final newline."""
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, f'duplicate JSON object key: {key}')
        value[key] = item
    return value


def load_json(text):
    return json.loads(text, object_pairs_hook=unique_object)


def read_items(cq, name):
    items = [load_json(line) for line in (cq / name).read_text(encoding='utf-8').splitlines()
             if line.strip()]
    items = [item for item in items if '_header' not in item]
    require(all(isinstance(item, dict) and isinstance(item.get('id'), str) for item in items),
            f'missing item id in {name}')
    require(len(items) == len({item['id'] for item in items}), f'duplicate ids in {name}')
    return {item['id']: item for item in items}


def aggregate_status(axes):
    statuses = [axes[name]['status'] for name in AXES]
    if all(status == 'compatible' for status in statuses):
        return 'compatible'
    if 'incompatible' in statuses:
        return 'incompatible'
    return 'unclear'


def has_literal_anchor(reason, item):
    """At least one quoted span must literally occur in this item's sources.

    This is a source-presence gate, not an assessment of the reason's logic or
    of whether the cited span supports the recorded judgment.
    """
    quoted = re.findall(r'`([^`]+)`|"([^"]+)"', reason)
    for parts in quoted:
        anchor = next(part for part in parts if part)
        if not anchor.strip():
            continue
        if anchor in item['question'] or anchor in item['reference_query']:
            return True
        if any(anchor in column for column in item['returned_columns']) or anchor in item['scored_answer_column']:
            return True
    return False


def check_counts(recorded, actual, label):
    require(isinstance(recorded, dict) and set(recorded) <= STATUSES, f'bad {label} keys')
    require(all(type(count) is int and count >= 0 for count in recorded.values()),
            f'bad {label} counts')
    require({status: recorded.get(status, 0) for status in STATUSES}
            == {status: actual[status] for status in STATUSES}, f'{label} differs')


def validate_input(record, cq):
    require(record.get('schema') == SCHEMA, 'record schema differs')
    protocol = record.get('protocol_text')
    require(isinstance(protocol, str), 'protocol_text must be the original UTF-8 text')
    require(record.get('protocol_sha256') == PROTOCOL_SHA256
            and digest(protocol.encode('utf-8')) == PROTOCOL_SHA256, 'fixed protocol hash differs')
    bundle = record.get('input')
    require(isinstance(bundle, dict), 'input must be the original input object')
    require(record.get('input_sha256') == INPUT_SHA256
            and digest(canonical_bytes(bundle)) == INPUT_SHA256, 'fixed input hash differs')
    require(bundle.get('protocol_sha256') == PROTOCOL_SHA256, 'input protocol hash differs')
    require(bundle.get('scoring_definition') == SCORING_DEFINITION, 'scoring definition differs')
    sources = bundle.get('inputs')
    require(isinstance(sources, dict) and set(sources) == SOURCE_NAMES, 'input source names differ')
    for name, expected in sources.items():
        require(digest((cq / name).read_bytes()) == expected, f'source changed: {name}')
    benchmark, keys = read_items(cq, 'benchmark.jsonl'), read_items(cq, 'core_answer_gold.jsonl')
    candidates = (cq / 'splits/contract_exact_script_fixed_133.txt').read_text(encoding='utf-8').splitlines()
    require(len(candidates) == CANDIDATE_N and candidates == sorted(set(candidates)),
            'candidate IDs must be the original sorted, unique 133 IDs')
    expected_items = []
    for cid in candidates:
        require(cid in benchmark and cid in keys, f'candidate missing from source: {cid}')
        item, key = benchmark[cid], keys[cid]
        expected_items.append({
            'id': cid,
            'question': item['question_en'],
            'reference_query': item['cypher'],
            'returned_columns': item['gold_columns'],
            'scored_answer_column': key['answer_column'],
        })
    require(bundle.get('items') == expected_items, 'score-blind input fields differ from original sources')
    # The pinned input retains its earlier field-input provenance hash. This
    # checker reconstructs the source fields above, not that earlier review.
    return candidates, {item['id']: item for item in expected_items}


def validate_record(record, cq=CQ):
    cq = Path(cq)
    candidates, inputs = validate_input(record, cq)
    reviews = record.get('reviews')
    texts = record.get('individual_review_text')
    hashes = record.get('individual_review_sha256')
    for name, value in [('reviews', reviews), ('individual_review_text', texts),
                        ('individual_review_sha256', hashes)]:
        require(isinstance(value, dict) and set(value) == REVIEWERS, f'expect two {name}')
    counts, by_id, axis_counts_by_reviewer = {}, {}, {}
    for reviewer in sorted(REVIEWERS):
        text = texts[reviewer]
        require(isinstance(text, str), f'raw review text missing: {reviewer}')
        require(digest(text.encode('utf-8')) == hashes[reviewer], f'raw review hash differs: {reviewer}')
        require(load_json(text) == reviews[reviewer], f'parsed review differs from raw text: {reviewer}')
        review = reviews[reviewer]
        require(isinstance(review, dict), f'review must be an object: {reviewer}')
        require(review.get('protocol_sha256') == PROTOCOL_SHA256
                and review.get('input_sha256') == INPUT_SHA256, f'review input/protocol hash differs: {reviewer}')
        require(review.get('reviewer_type') == REVIEWER_TYPE, f'reviewer type differs: {reviewer}')
        rows = review.get('items')
        require(isinstance(rows, list) and len(rows) == CANDIDATE_N, f'expect 133 judgments: {reviewer}')
        require(all(isinstance(row, dict) and isinstance(row.get('id'), str) for row in rows),
                f'bad review item: {reviewer}')
        require(len({row['id'] for row in rows}) == len(rows), f'duplicate review IDs: {reviewer}')
        require(sorted(row['id'] for row in rows) == candidates, f'review IDs differ: {reviewer}')
        by_id[reviewer] = {}
        counts[reviewer] = Counter()
        axis_counts = {axis: Counter() for axis in AXES}
        for row in rows:
            cid = row['id']
            axes = row.get('axes')
            require(isinstance(axes, dict) and set(axes) == set(AXES), f'four axes differ: {cid}/{reviewer}')
            for axis in AXES:
                judgment = axes[axis]
                require(isinstance(judgment, dict) and isinstance(judgment.get('status'), str)
                        and judgment['status'] in STATUSES,
                        f'bad axis status: {cid}/{reviewer}/{axis}')
                reason = judgment.get('reason')
                require(isinstance(reason, str) and reason.strip(), f'empty reason: {cid}/{reviewer}/{axis}')
                require(has_literal_anchor(reason, inputs[cid]), f'missing literal source anchor: {cid}/{reviewer}/{axis}')
                axis_counts[axis][judgment['status']] += 1
            require(row.get('overall_status') == aggregate_status(axes), f'overall rule differs: {cid}/{reviewer}')
            counts[reviewer][row['overall_status']] += 1
            by_id[reviewer][cid] = row['overall_status']
        axis_counts_by_reviewer[reviewer] = axis_counts
        # Optional summaries in the unmodified raw review must agree when they
        # use these explicitly named fields; unspecified metadata is retained.
        if 'status_counts' in review:
            check_counts(review['status_counts'], counts[reviewer], f'review status counts: {reviewer}')
        if 'axis_status_counts' in review:
            require(isinstance(review['axis_status_counts'], dict)
                    and set(review['axis_status_counts']) == set(AXES), f'bad review axis counts: {reviewer}')
            for axis in AXES:
                check_counts(review['axis_status_counts'][axis], axis_counts[axis], f'axis counts: {reviewer}/{axis}')
    recorded_counts = record.get('status_counts')
    require(isinstance(recorded_counts, dict) and set(recorded_counts) == REVIEWERS, 'bad record status counts')
    for reviewer in REVIEWERS:
        summary = recorded_counts[reviewer]
        require(isinstance(summary, dict) and set(summary) == {'overall', 'axes'},
                f'bad record summary: {reviewer}')
        check_counts(summary['overall'], counts[reviewer], f'record overall status counts: {reviewer}')
        require(isinstance(summary['axes'], dict) and set(summary['axes']) == set(AXES),
                f'bad record axis counts: {reviewer}')
        for axis in AXES:
            check_counts(summary['axes'][axis], axis_counts_by_reviewer[reviewer][axis],
                         f'record axis counts: {reviewer}/{axis}')
    if 'same_overall_status_count' in record:
        same = sum(by_id['a'][cid] == by_id['b'][cid] for cid in candidates)
        require(type(record['same_overall_status_count']) is int
                and record['same_overall_status_count'] == same, 'overall agreement count differs')
    selected = [cid for cid in candidates if all(by_id[reviewer][cid] == 'compatible' for reviewer in REVIEWERS)]
    require(record.get('selected_ids') == selected, 'recorded compatible intersection differs')
    require(type(record.get('selected_n')) is int and record['selected_n'] == len(selected), 'selected count differs')
    frozen = record.get('frozen_before_new_subset_scoring_utc')
    require(isinstance(frozen, str) and frozen.strip(), 'freeze timestamp missing')
    timestamp = datetime.fromisoformat(frozen.replace('Z', '+00:00'))
    require(timestamp.tzinfo is not None and timestamp.utcoffset() == timedelta(0), 'freeze timestamp must be UTC')
    require(isinstance(record.get('limits'), (str, list, dict)) and bool(record['limits']), 'review limits missing')
    return selected


def render_ids(ids):
    # A valid empty intersection is the empty file, never an empty ID line.
    return ''.join(cid + '\n' for cid in ids).encode('utf-8')


def check_shipped_ids(ids, cq=CQ):
    require((Path(cq) / IDS_NAME).read_bytes() == render_ids(ids), 'shipped intersection bytes differ')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true', help='check sources, stored reviews and shipped IDs without writing (default)')
    mode.add_argument('--out', type=Path, help='also write reproduced IDs outside the release dataset')
    args = parser.parse_args()
    try:
        record = load_json((CQ / RECORD_NAME).read_text(encoding='utf-8'))
        require(isinstance(record, dict), 'record must be an object')
        ids = validate_record(record)
        check_shipped_ids(ids)
        if args.out:
            require(not args.out.resolve().is_relative_to(CQ.resolve()), 'output must remain outside released inputs')
            require(args.out.resolve() != Path(__file__).resolve(), 'output must not overwrite this checker')
            args.out.write_bytes(render_ids(ids))
        print(f'PASS: {CANDIDATE_N} stored AI-reviewed items; {len(ids)} jointly four-axis-compatible IDs; '
              'source/selection check, not judgment truth or expert validation')
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
