#!/usr/bin/env python3
"""Separate frozen matches, source-derived views and unapplied corrections."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path.cwd()
B = ROOT/'logs/publication/paper/under-review/kdd-2027-datasets-benchmarks/reviews/fUWF-follow-up'
R = B/'refinement'
S = ROOT/'scripts/publication/paper/under-review/kdd-2027-datasets-benchmarks/rebuttal/fuwf_followup'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(name, data):
    with (R/name).open('x') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main():
    spec = importlib.util.spec_from_file_location('recipient_grammar', S/'source_pool.py')
    grammar = importlib.util.module_from_spec(spec); spec.loader.exec_module(grammar)
    ls = json.loads((B/'recipient_field_extension.json').read_text())
    pool = json.loads((B/'routing_pool.json').read_text())
    cr = json.loads((R/'cr-binding/results.json').read_text())
    write('disposition_protocol.json', {
        'producer_sha256': sha(Path(__file__)),
        'recipient_rule': 'Apply the existing fully-consumed RAN/SA/CT wrapper grammar to each frozen target identity after underscore-to-space normalization. A graph target must resolve to exactly ONE group; compound targets are retained as differences, not silently split.',
        'scope': 'Same source-first50; no replacement and no frozen data modification.',
        'pins': {n: sha(B/n) for n in ['recipient_field_extension.json','routing_pool.json']},
        'cr_pin': sha(R/'cr-binding/results.json'), 'human_reviews': 0, 'model_calls': 0})
    routing = []
    for old in ls['cases']:
        row = dict(old); canonical, unknown = [], []
        for target in old['graph_set']:
            ids, complete, residue = grammar.normalize_recipients(target.replace('_', ' '))
            if complete and len(ids) == 1:
                canonical += ids
            else:
                unknown.append({'frozen_target': target, 'parsed_ids': ids, 'unconsumed': residue})
        row.update(canonical_graph_set=sorted(set(canonical)), unbound_graph_targets=unknown)
        if old['graph_identities'] != 1:
            row['canonical_status'] = 'unresolved_graph_identity'
        elif unknown or sorted(set(canonical)) != old['normalized_source_set']:
            row['canonical_status'] = 'recipient_set_difference'
        else:
            row['canonical_status'] = 'canonical_recipient_set_match'
        row['alias_normalization_required'] = old['graph_set'] != row['canonical_graph_set']
        routing.append(row)
    write('routing_frozen_alignment.json', {
        'selected_n': 50, 'source_normalized_n': len(routing),
        'strict_identity_counts': ls['counts'],
        'canonical_counts': dict(Counter(r['canonical_status'] for r in routing)),
        'excluded_n': len(pool['exclusions']), 'exclusions': pool['exclusions'],
        'cases': routing,
        'derivative_47_record_slice': 'New source-normalized CSV view, not the unchanged frozen KG; 37 strict matches + 6 explicit wrapper aliases agree with frozen recipient sets. One compound target differs; three selected records lack a unique graph identity.',
        'graph_changes_applied': False, 'expert_reviews': 0})
    dispositions, additions = [], []
    for row in cr['cases']:
        if row['status'] != 'native_cover_set_difference':
            continue
        comp = row['comparison']; block = row['graph_matches'][0]['frozen_block']
        target_release = re.findall(r'spectra:targetRelease\s+<([^>]*)>', block)
        rec = {
            'identity': row['identity'], 'tdoc': row['current_tdoc'], 'wg': row['wg'],
            'native_header_witnesses': row['header_witnesses'], 'spec': row['specs'][0],
            'native_release': row['releases'][0], 'source_set': comp['source_set'],
            'frozen_set': comp['graph_set'], 'frozen_target_release_IRIs': target_release,
            'native_archive': row['archive'], 'native_archive_sha256': row['archive_sha256'],
            'native_member': row['member'], 'native_member_sha256': row['member_sha256'],
            'clauses_field': row['fields'][0], 'frozen_subject': row['graph_matches'][0]['subject'],
            'frozen_block_sha256': row['graph_matches'][0]['block_sha256'],
            'status': 'confirmed_native_cover_vs_frozen_target_set_difference',
            'classification': 'missing_clause_target_set' if not comp['graph_set'] else 'section_release_disagrees_with_native_cover',
            'production_root_cause': 'not_established', 'applied_to_frozen_graph': False}
        dispositions.append(rec)
        additions.append(dict(rec, derivative_status='SOURCE_DERIVED_CLAUSE_VIEW_ONLY',
                              incorporation_or_adoption_verified=False))
    write('cr_dispositions_unapplied.json', {
        'corrected_fixed_sample_n': 50, 'differences_n': len(dispositions),
        'classification_counts': dict(Counter(d['classification'] for d in dispositions)),
        'cases': dispositions,
        'root_cause_scope': 'Current TDoc bindings confirmed from native headers. Seven empty frozen clause sets are observed omissions; their pipeline causes remain unknown. One target has Rel-15 while both native cover and frozen targetRelease say Rel-17. These findings are distinct from later-version guesses.',
        'expert_reviews': 0, 'frozen_modifications': 0})
    write('source_derived_cr_additions.json', {
        'records_n': len(additions), 'clause_memberships_n': sum(len(r['source_set']) for r in additions),
        'records': additions, 'version': 'fUWF-native-source-view-v2',
        'status': 'LOCAL_SOURCE_DERIVED_VIEW_NOT_APPLIED_TO_FROZEN_GRAPH',
        'selection': 'All eight differences among the fixed50, not a positive-match selection. This derivative cannot establish original KG accuracy.',
        'source_role': 'Clauses affected on the retained CR cover; no normative incorporation assertion.'})
    # Keep every fixed case and explain exactly which evidence supersedes old labels.
    summary = {
        'selected_total_n': 491, 'planned_n': 500, 'unfilled_n': 9,
        'table': [
            {'relation':'MODIFIES_SECTION','graph_first':[26,3,21,0], 'source_first':[25,8,17,0],
             'scope':'Native cover-set field comparison; source-first native ID correction retained40 changed bindings.'},
            {'relation':'REFERENCES','graph_first':[4,0,46,0], 'source_first':[6,0,35,0],
             'scope':'Citation token sets;41 source-first selected,9 unfilled; no semantic validation.'},
            {'relation':'MADE_AT','graph_first':[9,0,41,0], 'source_first':[4,0,46,0],
             'scope':'Original report identity/meeting-label comparison.'},
            {'relation':'RESOLUTION_BELONGS_TO','graph_first':[0,1,49,0], 'source_first':[0,1,49,0],
             'scope':'Automatic heading candidates, not adjudicated agenda relationship errors.'},
            {'relation':'SENT_TO','graph_first':[33,0,17,0], 'source_first':[43,1,3,3],
             'scope':'Source-first43 includes6 explicit wrapper-alias normalizations;3 malformed/external original fields excluded. Graph-first remains original grammar result.'}],
        'columns':['match','difference','unresolved','excluded'],
        'not_population_estimates': True,
        'old_labels': 'Preserved in original files and old ZIP; source-first10/19/21 must not be presented as confirmed missing links. New25/8/17 uses independently native-bound IDs on the same50.',
        'no_expert_reviews': True, 'source_sampling_frame_caveat': 'The original filename regex also affected eligibility. Fixed-case correction is not a repaired population sampling frame.'}
    write('audit_summary.json', summary)
    print(json.dumps({'routing':dict(Counter(r['canonical_status'] for r in routing)),
        'cr_dispositions':len(dispositions),'source_derived_clause_memberships':sum(len(r['source_set']) for r in additions)}))


if __name__ == '__main__':
    main()
