#!/usr/bin/env python3
"""Check recorded AI field judgments and reproduce their fixed intersection.

This reproduces a selection from two stored AI reviews. It does not repeat the
AI review or certify question semantics, domain correctness or practitioner
demand. No predictions or model scores are read. Original questions/keys stay
unchanged; every mismatch or ambiguous judgment excludes an item.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

CQ = Path(__file__).resolve().parent.parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_items(name):
    items = [json.loads(line) for line in (CQ / name).read_text().splitlines() if line.strip()]
    items = [item for item in items if '_header' not in item]
    require(len(items) == len({item['id'] for item in items}), f'duplicate ids in {name}')
    return {item['id']: item for item in items}


def validate_record(record):
    for name, expected in record['source_sha256'].items():
        require(digest((CQ / name).read_bytes()) == expected, f'source changed: {name}')
    benchmark, keys = read_items('benchmark.jsonl'), read_items('core_answer_gold.jsonl')
    candidates = (CQ / 'splits/contract_exact_script_fixed_133.txt').read_text().splitlines()
    require(candidates == sorted(set(candidates)), 'candidate ids not sorted/unique')
    rows = record['items']
    require([row['id'] for row in rows] == candidates, 'review rows differ from fixed candidate set')
    allowed = {'field_aligned', 'mismatch', 'ambiguous'}
    counts, same, selected, inputs, originals = {'a': Counter(), 'b': Counter()}, 0, [], [], {'a': [], 'b': []}
    for row in rows:
        cid = row['id']
        item, key = benchmark[cid], keys[cid]
        expected = {'id': cid, 'question': item['question_en'], 'reference_query': item['cypher'],
                    'returned_columns': item['gold_columns'], 'scored_answer_column': key['answer_column']}
        require({name: row[name] for name in expected} == expected, f'review input differs: {cid}')
        inputs.append(expected)
        require(set(row['judgments']) == {'a', 'b'}, f'expect two reviews: {cid}')
        for reviewer, judgment in row['judgments'].items():
            require(judgment['id'] == cid and judgment['status'] in allowed, f'bad judgment: {cid}/{reviewer}')
            require(judgment['rationale'].strip(), f'empty rationale: {cid}/{reviewer}')
            phrase, anchor = judgment['question_phrase'], judgment['query_or_column_anchor']
            require(phrase.strip() and phrase in row['question'], f'question anchor differs: {cid}/{reviewer}')
            require(anchor.strip() and (anchor in row['reference_query'] or anchor in row['returned_columns']),
                    f'query anchor differs: {cid}/{reviewer}')
            counts[reviewer][judgment['status']] += 1
            originals[reviewer].append(judgment)
        same += row['judgments']['a']['status'] == row['judgments']['b']['status']
        if all(judgment['status'] == 'field_aligned' for judgment in row['judgments'].values()):
            selected.append(cid)
    # Input serialization matches the prepared score-blind bundle. This checks
    # its recorded hash without adding demand labels or scores to that bundle.
    bundle = {'protocol_sha256': record['review_protocol_sha256'], 'inputs': record['source_sha256'],
              'scoring_definition': record['scoring_definition'], 'items': inputs}
    require(digest((json.dumps(bundle, ensure_ascii=False, indent=1) + '\n').encode()) == record['review_input_sha256'],
            'score-blind input hash differs')
    require({key: dict(sorted(count.items())) for key, count in counts.items()} == record['status_counts'], 'status counts differ')
    require(same == record['same_status_count'], 'agreement count differs')
    require(selected == record['selected_ids'] and len(selected) == record['selected_n'], 'intersection differs')
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='check shipped IDs without writing')
    parser.add_argument('--out', type=Path, help='write reproduced IDs outside the release datasets')
    args = parser.parse_args()
    record = json.loads((CQ / 'field_coverage_review.json').read_text())
    ids = validate_record(record)
    rendered = ''.join(cid + '\n' for cid in ids)
    if args.check:
        require((CQ / 'splits/field_coverage_reviewed_ids.txt').read_text() == rendered, 'shipped intersection differs')
    if args.out:
        require(not args.out.resolve().is_relative_to(CQ.resolve()), 'output must remain outside released inputs')
        args.out.write_text(rendered)
    print(f'PASS: {len(record["items"])} stored AI-reviewed items; {len(ids)} jointly field-aligned IDs; not expert validation')


if __name__ == '__main__':
    main()
