#!/usr/bin/env python3
"""Independently check packaged refinement identities, exports and scores."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import runpy
import subprocess
import sys
import tempfile


def main():
    root=Path(__file__).resolve().parent
    def load(p):return json.loads((root/p).read_text())
    hashes=load('SHA256.json')
    for p,h in hashes.items():assert hashlib.sha256((root/p).read_bytes()).hexdigest()==h,p
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='SHA256.json'}
    assert actual==set(hashes)
    sample=load('source-audit/sampling.json')
    assert sample['selected_n']==491 and sample['requested_n']==500
    units=load('refinement/review_units.json')
    assert units['status']=='PASS'
    for path,pin in units['inputs_sha256'].items():
        assert hashlib.sha256((root/path).read_bytes()).hexdigest()==pin,path
    fixed_counts=Counter((c['relation'],c['direction']) for c in sample['cases'])
    unit_rows=units['audit']['by_relation_and_direction']
    for row in unit_rows:
        assert row['graph_first_cases']==fixed_counts[row['relation'],'graph_first']
        assert row['source_first_cases']==fixed_counts[row['relation'],'source_first']
        assert row['total_cases']==row['graph_first_cases']+row['source_first_cases']
    assert sum(r['total_cases'] for r in unit_rows)==units['audit']['selected_cases']==491
    assert units['audit']['graph_first_cases']==sum(r['graph_first_cases'] for r in unit_rows)==250
    assert units['audit']['source_first_cases']==sum(r['source_first_cases'] for r in unit_rows)==241
    relation_totals={r['relation']:r['total_cases'] for r in unit_rows}
    assert relation_totals=={'MODIFIES_SECTION':100,'REFERENCES':91,'MADE_AT':100,
                            'RESOLUTION_BELONGS_TO':100,'SENT_TO':100}
    assert units['audit']['unfilled_slots']==sample['requested_n']-sample['selected_n']==9
    source_fixed={c['sample_identity'] for c in sample['cases'] if c['relation']=='MODIFIES_SECTION' and c['direction']=='source_first'}
    graph_fixed={c['sample_identity'] for c in sample['cases'] if c['relation']=='MODIFIES_SECTION' and c['direction']=='graph_first'}
    bound=load('refinement/cr-binding/results.json')
    source=load('refinement/cr-literal-lists-complete/results.json')
    graph=load('refinement/graph-cr-literal-lists-complete/results.json')
    assert len(source_fixed)==len(graph_fixed)==50
    assert {c['identity'] for c in bound['cases']}=={c['identity'] for c in source['cases']}==source_fixed
    assert {c['identity'] for c in graph['cases']}==graph_fixed
    assert bound['binding_changed_n']==40 and bound['binding_confirmed_n']==50
    frozen_by_id={c['identity']:c for c in bound['cases']}
    for data,expected in [(source,[30,15,5]),(graph,[33,7,10])]:
        counts=Counter(c['status'] for c in data['cases'])
        assert dict(counts)==data['counts']
        assert [counts[k] for k in ['native_cover_set_match','native_cover_set_difference','unresolved']]==expected
        for c in data['cases']:
            if c['status']=='unresolved':continue
            comp=c['comparison'];native=set(comp['source_set']);actual_=set(comp['graph_set'])
            assert native and comp['exact_equal']==(native==actual_)
            assert (c['status']=='native_cover_set_match')==comp['exact_equal']
            if data is source:
                declared={c['spec']+'-'+c['release']+'-'+p for p in c['literal_clauses']}
                assert declared==native
                old=frozen_by_id[c['identity']]
                assert c['member_sha256']==old['member_sha256']
                assert c['archive_sha256']==old['archive_sha256']
    view=load('refinement/source-derived-cr-declarations/manifest.json')
    with (root/'refinement/source-derived-cr-declarations/records.csv').open(newline='') as f:records=list(csv.DictReader(f))
    with (root/'refinement/source-derived-cr-declarations/declared_clauses.csv').open(newline='') as f:members=list(csv.DictReader(f))
    assert len(records)==view['parsed_record_n']==45
    assert len(members)==view['declared_membership_n']==112
    for name,pin in view['files_sha256'].items():
        assert hashlib.sha256((root/'refinement/source-derived-cr-declarations'/name).read_bytes()).hexdigest()==pin
    expected_records={c['identity']:c for c in source['cases'] if 'comparison' in c}
    assert {c['source_identity'] for c in records}==set(expected_records)
    assert {tuple(c[k] for k in ['source_identity','declared_clause']) for c in members}=={
        (identity,clause) for identity,c in expected_records.items() for clause in c['literal_clauses']}
    assert len(view['unresolved_cases'])==5
    assert Counter(c['frozen_alignment'] for c in records)=={'native_cover_set_match':30,'native_cover_set_difference':15}
    ledger=load('refinement/source-derived-cr-declarations/discrepancies_unapplied.json')
    assert ledger['case_n']==len(ledger['cases'])==15
    assert ledger['observed_kind_counts']=={
        'declared_section_outside_frozen_definition_scope':12,
        'missing_link_to_defined_section':1,'different_release_target':2}
    for c in ledger['cases']:assert not c['applied_to_frozen_release'] and not c['applied_to_production']
    routing=load('refinement/routing_frozen_alignment.json')
    assert len(routing['cases'])==47 and routing['excluded_n']==3
    assert Counter(c['canonical_status'] for c in routing['cases'])==routing['canonical_counts']
    assert routing['canonical_counts']=={'canonical_recipient_set_match':43,'unresolved_graph_identity':3,'recipient_set_difference':1}
    assert sum(c.get('alias_normalization_required',False) for c in routing['cases'] if c['canonical_status']=='canonical_recipient_set_match')==6
    for c in routing['cases']:
        if c['graph_identities']!=1:continue
        canonical=[];unbound=[]
        for raw in c['graph_set']:
            token=re.sub(r'[ _-]', '',raw).upper()
            m=re.fullmatch(r'(?:3GPP)?(?:TSG)?(?:WG)?(RAN|SA|CT)(?:WG)?(\d*)',token)
            if m:canonical.append(m[1]+m[2])
            else:unbound.append(raw)
        assert sorted(set(canonical))==c['canonical_graph_set']
        assert sorted(unbound)==sorted(v['frozen_target'] for v in c['unbound_graph_targets'])
        match=not unbound and set(canonical)==set(c['normalized_source_set'])
        assert match==(c['canonical_status']=='canonical_recipient_set_match')
    native=load('refinement/native-verification-meeting/results.json')
    assert native['status']=='PASS' and native['LS_fixed_n']==50
    assert native['LS_original_alignment_counts']=={'original_TDoc_To_Type_fields_agree':50}
    assert native['current_CR_header_IDs_checked_n']==50 and not native['input_drift_paths']
    source_ls={c['sample_identity'] for c in sample['cases']
               if c['relation']=='SENT_TO' and c['direction']=='source_first'}
    assert source_ls=={c['identity'] for c in native['LS_cases']}
    assert source_ls=={c['identity'] for c in routing['cases']}|{c['identity'] for c in routing['exclusions']}
    with (root/'verified-routing-slice/records.csv').open(newline='') as f:
        ls_records=list(csv.DictReader(f))
    with (root/'verified-routing-slice/addressed_recipients.csv').open(newline='') as f:
        ls_memberships=list(csv.DictReader(f))
    assert {c['source_path']+'#'+c['sheet']+'!'+c['row'] for c in ls_records}=={c['identity'] for c in routing['cases']}
    liaison_units=units['source_first_liaison']
    assert liaison_units['selected_cases']==liaison_units['original_TDoc_To_Type_fields_reopened']==len(source_ls)==50
    assert liaison_units['admitted_records']==len(ls_records)==47
    assert liaison_units['recipient_memberships']==len(ls_memberships)==62
    assert liaison_units['excluded_complete_source_fields']==len(routing['exclusions'])==3
    assert liaison_units['record_level_frozen_alignment']=={
        'strict_matches':37,'matches_after_explicit_WG_wrapper_alias':6,
        'merged_recipient_differences':1,'unresolved_graph_identities':3}
    trace=load('refinement/normative-trace/evidence-excerpt.json')
    verified=load('refinement/normative-root-verification.json')
    assert verified['status']=='PASS' and verified['source_archives_reopened_n']==5
    assert verified['before_occurrences']==0 and verified['after_occurrences']==1
    assert verified['complete_inserted_paragraph_exactly_equal'] and verified['RP_tracked_insertion_equals_WG']
    assert trace['evidence'][2]['normalized_complete_paragraph_sha256']==trace['evidence'][4]['normalized_complete_paragraph_sha256']
    assert all(trace['sources'][k]['official_url'].startswith('https://www.3gpp.org/') for k in trace['sources'])
    claims=load('claim_source_map.json')
    for key,path in claims.items():
        if isinstance(path,str) and not path.startswith('https://') and (path.endswith('.json') or path.endswith('.txt') or path.endswith('.py')):
            assert (root/path).is_file(),(key,path)
    boundary=load('refinement/review-evidence/trace_boundary.json')
    assert boundary['status']=='PASS' and len(boundary['frozen_records'])==6
    assert boundary['frozen_input_sha256']==load('decision_trace_actual_graph.json')['frozen_sha256']['RAN1']
    prefix='https://w3id.org/spectra/inst/RAN1/'
    blocks=boundary['frozen_records']
    resolution=blocks[prefix+'Resolution/AGR-110b-8.12-007']['text']
    cr=blocks[prefix+'Tdoc/tdoc:R1-2210700']['text']
    for block in blocks.values():
        assert hashlib.sha256(block['text'].encode()).hexdigest()==block['block_sha256']
    assert 'spectra:references' in resolution and '<'+prefix+'Tdoc/tdoc:R1-2210700>' in resolution
    assert 'spectra:modifiesSection <'+prefix+'Section/38.213-Rel-17-18>' in cr
    assert 'spectra:tsgCRPack "RP-222864"' in cr
    comparator=load('refinement/review-evidence/comparator_scope.json')
    assert comparator['status']=='PASS' and comparator['revision']=='e6487ae660852b56e6d9952680f661215a53ec46'
    with (root/'verified-routing-slice/records.csv').open(newline='') as f:
        routing_ids={c['tdoc_number'] for c in csv.DictReader(f)}
    assert set(comparator['liaison_slice_TDoc_ids_checked'])==routing_ids
    assert not comparator['graph_literal_slice_TDoc_mentions'] and not comparator['chunk_literal_slice_TDoc_mentions']
    assert comparator['graph_records']=={'node':21540,'edge':31718}
    assert comparator['chunk_records']==comparator['empty_chunk_text_records']==896453
    disclosure=load('refinement/review-evidence/public_disclosure.json')
    assert disclosure['status']=='PASS' and disclosure['defect_count']==8
    assert hashlib.sha256(disclosure['public_guide_content'].encode()).hexdigest()==disclosure['public_guide_receipt']['sha256']
    assert not re.search(r'cutoff.?tie|67 retained controls|eight.*defects',disclosure['public_guide_content'],re.I)
    external=load('refinement/review-evidence/external_document_access.json')
    assert external['status']=='PASS' and external['ETSI_receipt']['http_status']==200
    assert external['normative_sentence_printed_page']==248 and external['change_history_printed_page']==260
    assert external['normative_sentence_normalized_sha256']==trace['evidence'][2]['normalized_complete_paragraph_sha256']
    assert external['complete_sentence_equal_after_declared_PDF_line_wrap_normalization']
    assert all(x in external['change_history_row'] for x in ['RP-222864','0388','17.4.0'])
    matrix=load('refinement/latest_audit_summary.json')
    assert sum(sum(r[x]) for r in matrix['table'] for x in ['graph_first','source_first'])==491
    assert matrix['table'][0]['graph_first']==[33,7,10,0] and matrix['table'][0]['source_first']==[30,15,5,0]
    report_extension=load('refinement/report-source-extension-corrected/results.json')
    report_fixed={(c['sample_identity'],c['relation'],c['direction']) for c in sample['cases']
                  if c['relation'] in ['REFERENCES','MADE_AT','RESOLUTION_BELONGS_TO']}
    assert len(report_fixed)==report_extension['fixed_report_case_n']==291
    assert {(c['fixed_identity'],c['relation'],c['direction']) for c in report_extension['cases']}==report_fixed
    assert report_extension['status']=='PASS' and not report_extension['input_drift_paths']
    expected_changed={}
    for case in report_extension['cases']:
        if case['status']!=case['previous_status']:
            expected_changed[(case['fixed_identity'],case['relation'],case['direction'])]=(case['previous_status'],case['status'])
        if case['status']=='unresolved':continue
        assert case['graph_identity_n']==1
        assert all(c['native_mappings'] and c['original_complete_paragraph_span_equal'] for c in case['occurrences'])
        comp=case['comparison'];equal=set(comp['source_set'])==set(comp['graph_set'])
        assert equal==comp['exact_set_equal']
        assert (case['status'].endswith('_match'))==equal
        if case['relation']=='RESOLUTION_BELONGS_TO':
            candidates=[]
            for occurrence in case['occurrences']:
                for mapping in occurrence['native_mappings']:
                    heading=mapping['nearest_native_heading']
                    match=re.match(r'^\s*(\d+(?:\.\d+){0,6})\.?\s+\S',heading['native_heading_text'])
                    assert match and match[1]==heading['explicit_agenda_candidate']
                    candidates.append(match[1])
            assert set(candidates)==set(comp['source_set'])
    assert expected_changed=={(c['identity'],c['relation'],c['direction']):(c['before'],c['after']) for c in report_extension['changed_cases']}
    status_kinds=['match','difference','unresolved','excluded']
    for row in matrix['table']:
        if row['relation'] not in ['REFERENCES','MADE_AT','RESOLUTION_BELONGS_TO']:continue
        for direction in ['graph_first','source_first']:
            fixed=[c for c in report_extension['cases'] if c['relation']==row['relation'] and c['direction']==direction]
            counts=Counter('unresolved' if c['status']=='unresolved' else 'difference' if c['status'].endswith('_mismatch') else 'match' for c in fixed)
            assert row[direction]==[counts[k] for k in status_kinds]
            assert Counter(c['status'] for c in fixed)==report_extension['counts'][row['relation']+'/'+direction]
    executable=load('refinement/executable-source-views/results.json')
    assert executable['status']=='PASS' and executable['query_pairs_n']==37
    assert executable['table_record_counts']=={'cr':45,'declared_clause':112,'discrepancy':15,'cr_unresolved':5,'liaison':47,'recipient':62,'ls_excluded':3}
    with tempfile.TemporaryDirectory(prefix='fuwf-source-view-replay-') as temporary:
        replay=Path(temporary)/'replay'
        execution=subprocess.run([sys.executable,'-B',str(root/'producers/execute_source_views.py'),
            '--root',str(root),'--output',str(replay),
            '--compare',str(root/'refinement/executable-source-views')],capture_output=True,text=True,timeout=60)
        assert execution.returncode==0,execution.stderr
        replay_report=json.loads((replay/'results.json').read_text())
        assert replay_report['status']=='PASS' and replay_report['fresh_replay_equal']
    contracts=load('refinement/other-session-contract-review.json')
    assert contracts['contracts_in_public_supplement']==371
    assert contracts['cutoff_tie_counterexamples_n']==len(contracts['confirmed_cutoff_tie_counterexamples'])==8
    assert not contracts['local_proposals_admitted'] and not contracts['local_proposals_published']
    assert not contracts['official_scores_modified']
    assert all(not c['published_exact_for_valid_alternative'] for c in contracts['confirmed_cutoff_tie_counterexamples'])
    # Original verifier also recomputes all75 retained trial scores and gold sets.
    runpy.run_path(str(root/'verify_review_bundle.py'),run_name='__main__')
    analysis=load('matched/analysis.json');manifest=load('matched/manifest.json')
    diagnostic=units['diagnostic']
    assert {r['task_id'] for r in analysis['tasks']}=={r['id'] for r in manifest['tasks']}
    assert diagnostic['tasks_per_arm']==len(analysis['tasks'])==25
    assert diagnostic['retained_attempts']==75 and diagnostic['empty_answer_tasks']==10
    assert diagnostic['successful_both_empty_F1']==1.0 and diagnostic['any_failed_call_F1']==0.0
    for arm in manifest['arms']:
        rows=[r['arms'][arm] for r in analysis['tasks']];stored=diagnostic['arms'][arm]
        assert stored['tasks']==len(rows)==25
        assert stored['failed_calls']==sum(bool(r['error']) for r in rows)==analysis['arms'][arm]['errors']
        assert stored['exact_answers']==sum(r['exact'] for r in rows)==analysis['arms'][arm]['exact_matches']
        assert abs(stored['mean_record_set_F1']-sum(r['record_f1'] for r in rows)/len(rows))<1e-12
        assert abs(stored['mean_record_set_F1']-analysis['arms'][arm]['mean_record_f1'])<1e-12
        assert stored['successful_nonexact_answers']==sum(not r['error'] and not r['exact'] for r in rows)
    form=load('refinement/openreview_comment_form.json');comment=(root/'response_draft.txt').read_text()
    assert form['status']=='PASS' and form['comment_limit_characters']==5000
    assert len(comment)==form['comment_characters_including_Markdown_links_spaces_newlines']<=5000
    assert len(comment.encode('utf-16-le'))//2==form['comment_UTF16_code_units']<=5000
    assert hashlib.sha256(comment.encode()).hexdigest()==form['comment_sha256']
    assert len(comment.split())==form['comment_words']
    assert (root/'comment_title.txt').read_text().strip()==form['optional_title']
    assert form['extended_reference_is_not_comment_text'] and not form['attachment_field_shown_in_provided_form']
    print(json.dumps({'refinement_status':'PASS','packaged_hashes':len(hashes),
        'fixed_relation_cases':491,'source_first_CR':[30,15,5],'graph_first_CR':[33,7,10],
        'source_derived_declarations':[45,112],'routing':[47,62],
        'routing_canonical':[43,1,3,3],'original_LS_fields_reopened':50,
        'named_normative_example':'before0/after1 with native CR/version history',
        'retained_trials_rescored':75,'expert_reviews':0,
        'historical_371_cutoff_tie_defects':8,'historical_proposal_snapshot_retained':True,
        'native_bytes_reauthenticated_by_this_offline_run':False,
        'fresh_source_view_SQL_executions':37,'fresh_source_view_SPARQL_executions':37,
        'fixed_report_extension_cases':291,
        'model_calls_by_this_offline_run':0,'operational_DB_calls_by_this_offline_run':0},indent=2))


if __name__=='__main__':main()
