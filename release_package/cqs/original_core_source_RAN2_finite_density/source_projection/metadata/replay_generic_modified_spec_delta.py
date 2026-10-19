#!/usr/bin/env python3
"""Reconstruct a prospective metadata delta without graph or source-policy adoption.

The included complete frozen-CR projection and merged metadata witnesses are
derived evidence. Their raw-workbook and frozen-source provenance are pinned
separately. This replay is not an independent raw-source parse or native proof.
"""
from pathlib import Path
from collections import Counter
from decimal import Decimal
import gzip
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent


def load(name):
    return json.loads((HERE / name).read_text())


def records(name):
    with gzip.open(HERE / name, 'rt', encoding='utf-8') as f:
        return [json.loads(line) for line in f]


def canonical(meeting):
    value = re.sub(r'[-_](?:e|electronic)$', '', meeting.strip(), flags=re.I)
    return re.sub(r'[-_]?bis', 'bis', value, flags=re.I)


def normalize_specs(value):
    if value is None or isinstance(value, str) and value.strip().lower() in ('', 'nan', 'nat', 'none'):
        return []
    if isinstance(value, bool):
        raise ValueError('Boolean metadata is not a specification number')
    pieces = [f'{Decimal(str(value)):.3f}'] if isinstance(value, (int, float)) else re.split(r'\s*[,;]\s*|(?<=\d)\.\s+', str(value).strip())
    result = []
    for piece in pieces:
        piece = re.sub(r'^(?:TS|TR)\s+', '', piece, flags=re.I)
        piece = re.sub(r'^(\d{2})\s+(\d{3})', r'\1.\2', piece)
        if re.fullmatch(r'\d{2}\.\d{3}(?:-\d{1,2}){0,2}', piece) and piece not in result:
            result.append(piece)
    return result


def requested_specs(witness):
    fields = witness['fields']
    if fields['Type'] not in ('CR', 'draftCR', 'pCR'):
        raise ValueError('A source metadata record with a non-CR type is not a modified-spec witness')
    numbers = normalize_specs(fields['Spec'])
    if not numbers and isinstance(fields['Spec'], str) and re.fullmatch(r'Rel-\d{1,2}', fields['Spec'].strip(), re.I):
        numbers = normalize_specs(fields['Version'])
    return numbers


def resolve(number, specs):
    expected = 'tdoc:spec/' + number.replace('.', '_')
    exact = [r for r in specs if r['id'] == expected]
    if exact:
        if len(exact) != 1 or exact[0]['specNumber'] != number or exact[0]['specRelease'] is not None:
            raise ValueError('Conflicting exact identity')
        return exact[0], 'original_production_exact_id'
    hubs = [r for r in specs if r['specNumber'] == number and r['specRelease'] is None]
    if len(hubs) != 1:
        raise ValueError('Missing or ambiguous existing semantic hub')
    return hubs[0], 'proposed_unique_existing_hub_legacy_id_fallback'


def derive(frozen, witnesses, specs, allowed_meetings=None):
    indexed = {}
    for row in witnesses:
        if row['tdoc'] in indexed:
            raise ValueError('Merged metadata must have one record per TDoc identity')
        if requested_specs(row) != row['modified_spec_numbers']:
            raise ValueError('Normalized metadata is not equivalent to its included named fields')
        indexed[row['tdoc']] = row
    proposals = []
    missing_witness_n = 0
    for row in frozen:
        source = indexed.get(row['tdoc'])
        if source is None:
            missing_witness_n += 1
            continue
        if allowed_meetings is not None and canonical(source['meeting']) not in allowed_meetings:
            continue
        old_numbers = {x['specNumber'] for x in row['frozen_targets'] if x['specRelease'] is None and 'Spec' in x['target_labels']}
        for number in requested_specs(source):
            if number in old_numbers:
                continue
            target, route = resolve(number, specs)
            proposals.append({'source_CR_iri': row['frozen_CR_iri'], 'tdocNumber': row['tdoc'],
                              'relationship': 'MODIFIES', 'modified_spec_number': number,
                              'target_source_iri': target['source_iri'], 'target_node_id': target['node_id'],
                              'resolution_route': route, 'source_meeting': source['meeting'],
                              'source_witness_key': source['tdoc']})
    return sorted(proposals, key=lambda x: (x['source_CR_iri'], x['modified_spec_number'])), missing_witness_n


def controls():
    def spec(number='38.331', ident='tdoc:spec/38_331', release=None, node=1):
        return {'specNumber': number, 'id': ident, 'specRelease': release, 'node_id': node, 'source_iri': 'urn:node:' + str(node)}
    tests = []
    def check(name, fn, expected):
        try:
            result = fn()
            actual = result if isinstance(result, bool) else True
        except ValueError:
            actual = False
        assert actual == expected, name
        tests.append({'control': name, 'actual': actual, 'expected': expected, 'pass': True})
    check('exact hub identity', lambda: resolve('38.331', [spec()]), True)
    check('unique legacy identity requires explicit new fallback', lambda: resolve('37.320', [spec('37.320', 'tdoc:spec/37_32')]), True)
    check('release-only target rejected', lambda: resolve('38.331', [spec(ident='copy', release='Rel-19')]), False)
    check('duplicate semantic hubs rejected', lambda: resolve('37.320', [spec('37.320', 'a'), spec('37.320', 'b', node=2)]), False)
    check('wrong-number exact ID rejected before fallback', lambda: resolve('38.331', [spec('38.300'), spec(ident='legacy', node=2)]), False)
    check('duplicate exact IDs rejected', lambda: resolve('38.331', [spec(), spec(node=2)]), False)
    check('missing target rejected', lambda: resolve('38.331', []), False)
    check('electronic suffix canonicalized but bis retained', lambda: canonical('RAN2#113-bis-e') == 'RAN2#113bis', True)
    check('numeric cell padding preserves actual spreadsheet number', lambda: normalize_specs(38.3) == ['38.300'], True)
    check('text short decimal is not silently padded', lambda: normalize_specs('38.3') == [], True)
    check('affected CR ID not interpreted as modified spec', lambda: normalize_specs('R2-2601234') == [], True)
    check('duplicate source spec values retain one semantic fact', lambda: normalize_specs('38.331;38.331') == ['38.331'], True)
    check('non-CR type rejected', lambda: requested_specs({'fields': {'Type':'LS', 'Spec':'38.331', 'Version':None}}), False)
    check('release-shift salvage limited to explicit Rel pattern', lambda: requested_specs({'fields': {'Type':'CR', 'Spec':'Rel-19', 'Version':'38.331'}}) == ['38.331'], True)
    check('ordinary blank Spec is not filled from arbitrary Version', lambda: requested_specs({'fields': {'Type':'CR', 'Spec':None, 'Version':'38.331'}}) == [], True)
    return tests


def main():
    inventory = load('input_inventory.json')
    for row in inventory['files']:
        path = HERE / row['path']
        if path.is_symlink() or path.stat().st_size != row['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Input identity failed: ' + row['path'])
    frozen = records('evidence/all_frozen_CR_to_MODIFIES_source_comparisons.jsonl.gz')
    witnesses = records('evidence/all_retained_input_CR_MODIFIES_metadata_witnesses.jsonl.gz')
    specs = load('evidence/all_original_Spec_nodes.json')
    files = load('evidence/current64_file_and_original58_cutoff_manifest.json')
    original_meetings = {r['canonical_meeting'] for r in files if r['inside_original58_Meeting_identity_set']}
    all_delta, absent = derive(frozen, witnesses, specs)
    same_meeting_delta, _ = derive(frozen, witnesses, specs, original_meetings)
    expected = load('evidence/prior_missing107_canonical_proposals.json')
    actual_keys = {(r['source_CR_iri'], r['modified_spec_number'], r['target_source_iri']) for r in all_delta}
    expected_keys = {(r['source_CR_iri'], r['modified_spec_number'], r['target']['source_iri']) for r in expected}
    assert actual_keys == expected_keys
    receipt = {'status': 'DERIVED_CURRENT64_PROSPECTIVE_DELTA_REPLAYED_NOT_POLICY_ADOPTED',
               'all_frozen_CR_nodes': len(frozen), 'all_merged_source_CR_metadata_records': len(witnesses),
               'all_original_Spec_nodes': len(specs), 'current64_missing_semantic_pairs': len(all_delta),
               'same58_meeting_identity_scope_missing_pairs': len(same_meeting_delta),
               'outside_original58_meeting_scope_pairs': len(all_delta) - len(same_meeting_delta),
               'current64_delta_by_source_meeting': dict(Counter(canonical(r['source_meeting']) for r in all_delta)),
               'legacy_fallback_pair_count': sum(r['resolution_route'] != 'original_production_exact_id' for r in all_delta),
               'frozen_CR_nodes_without_source_CR_witness': absent,
               'raw_source_parse_performed_by_this_replay': False,
               'source_policy_adopted': False, 'graph_mutations':0, 'native_calls':0, 'API_calls':0,
               'expert_validation_n':0, 'original560_increment':0,
               'controls': controls(),
               'limits': ['Included complete projections and metadata witnesses are derived evidence with separately pinned raw sources.',
                          'Same meeting identities do not reconstruct the historical58 file versions.',
                          'Missing witnesses are unknown; old graph facts are never deleted.',
                          'Eight Section identities are separately proposed; their full generic reference/table ownership diff is pending.']}
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
