#!/usr/bin/env python3
"""Prepare an anonymous, source-attributed local reviewer attachment."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile


def digest(data):return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--zip',type=Path,required=True);a=p.parse_args();r=a.base/'refinement'
    safety=json.loads((r/'safety_final.json').read_text());assert safety['status']=='PASS'
    added_safety=json.loads((r/'safety_additional.json').read_text());assert added_safety['status']=='PASS'
    current_safety=json.loads((r/'safety_source_mapped.json').read_text());assert current_safety['status']=='PASS'
    latest_safety=json.loads((r/'safety_accounted.json').read_text());assert latest_safety['status']=='PASS'
    mapped=json.loads((r/'review-evidence/results.json').read_text());assert mapped['status']=='PASS'
    a.output.mkdir(exist_ok=False);assert not a.zip.exists()
    old=a.base/'fuwf-review-supplement.zip';original_zip_hash=digest(old.read_bytes())
    with zipfile.ZipFile(old) as z:
        for name in z.namelist():
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
        z.extractall(a.output)
    history=a.output/'history';history.mkdir()
    for name in ['README.md','SHA256.json','claim_source_map.json','package_provenance.json','response_draft.txt']:
        path=a.output/name
        if path.exists():path.rename(history/('previous_'+name))
    provenance=[]
    workspace=str(Path.cwd().resolve())
    home=str(Path.home())
    def copy(src,dest):
        data=src.read_bytes();text=data.decode('utf-8')
        text=text.replace(workspace+'/', '').replace(workspace,'<WORKSPACE>')
        text=text.replace(home+'/', '<HOME>/').replace(home,'<HOME>')
        encoded=text.encode('utf-8');dst=a.output/dest;dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_bytes(encoded)
        provenance.append({'package_path':str(dest),'source_path':str(src.resolve().relative_to(Path.cwd().resolve())),
            'original_artifact_sha256':digest(data),'packaged_sha256':digest(encoded),
            'path_anonymization_changed_bytes':data!=encoded})
    copy(r/'REVIEW_GUIDE.txt',Path('REVIEW_GUIDE.txt'))
    copy(r/'REVIEW_ENTRY_POINT.txt',Path('REVIEW_ENTRY_POINT.txt'))
    copy(r/'response_final_candidate.txt',Path('response_draft.txt'))
    copy(r/'response_extended_reference.txt',Path('response_extended_reference.txt'))
    copy(r/'comment_title.txt',Path('comment_title.txt'))
    copy(r/'manuscript_claim_revisions.txt',Path('manuscript_claim_revisions.txt'))
    files=['latest_audit_summary.json','routing_frozen_alignment.json','disposition_protocol.json',
        'cr_dispositions_unapplied.json','source_derived_cr_additions.json','audit_summary.json',
        'normative-root-verification.json','report-native-root-verification.json',
        'safety_final.json','safety_additional.json','safety_source_mapped.json','safety_accounted.json',
        'review_units.json','openreview_comment_form.json','other-session-contract-review.json',
        'external-source-examples/verification.json','external-source-examples/verification_with_routing.json',
        'normative-trace/evidence-excerpt.json','normative-trace/README.md',
        'normative-trace/rp-difference-check.json','normative-trace/producer.py',
        'normative-trace/verify_trace.py','normative-trace/export_excerpt.py',
        'normative-trace/rp_difference_check.py']
    for directory in ['cr-binding','legacy-doc-fallback','legacy-doc-fallback-corrected',
            'cr-literal-lists','cr-literal-lists-complete','graph-cr-literal-lists',
            'graph-cr-literal-lists-complete','native-verification','native-verification-meeting',
            'frozen-target-scope']:
        for name in ['protocol.json','results.json','producer.py','source_bindings_before_graph.json']:
            if (r/directory/name).exists():files.append(directory+'/'+name)
    for src in sorted((r/'source-derived-cr-declarations').iterdir()):
        if src.is_file():files.append('source-derived-cr-declarations/'+src.name)
    for directory in ['report-source-extension-corrected','executable-source-views','review-evidence']:
        for src in sorted((r/directory).iterdir()):
            if src.is_file() and src.suffix in ['.json','.sql','.nt']:
                files.append(directory+'/'+src.name)
    for name in files:copy(r/name,Path('refinement')/name)
    scripts=Path(__file__).parent
    for name in ['refine_cr_binding.py','refine_dispositions.py','verify_native_refinement.py',
            'native_doc_fallback.py','complete_cr_literal_lists.py','refine_graph_cover_lists.py',
            'diagnose_frozen_target_scope.py','materialize_refinement_views.py',
            'verify_normative_example.py','verify_refinement_safety.py','record_contract_status.py',
            'refine_report_provenance.py','verify_report_originals.py','execute_source_views.py',
            'record_evidence_boundaries.py',Path(__file__).name]:
        copy(scripts/name,Path('producers')/name)
    copy(scripts/'verify_refinement.py',Path('verify_refinement.py'))
    claims={
        'status':'LOCAL_PREPARED_NOT_POSTED_OR_UPLOADED',
        'current_reply':'response_draft.txt','complete_guide':'REVIEW_GUIDE.txt',
        'reviewer_entry_point':'REVIEW_ENTRY_POINT.txt',
        'comment_form_and_actual_length':'refinement/openreview_comment_form.json',
        'detailed_reading_version_not_comment_text':'response_extended_reference.txt',
        'case_counts_and_metric_units':'refinement/review_units.json',
        'fixed_five_relation_results':'refinement/latest_audit_summary.json',
        'current_source_first_CR':'refinement/cr-literal-lists-complete/results.json',
        'current_graph_first_CR':'refinement/graph-cr-literal-lists-complete/results.json',
        'extended_original_report_authentication':'refinement/report-source-extension-corrected/results.json',
        'executable_source_derived_queries':'refinement/executable-source-views/queries_and_gold.json',
        'actual_SQL_SPARQL_results':'refinement/executable-source-views/query_results.json',
        'standalone_source_view_reproducer':'producers/execute_source_views.py',
        'native_ID_correction':'refinement/cr-binding/results.json',
        'frozen_section_scope':'refinement/frozen-target-scope/results.json',
        'all_literal_cover_declarations':'refinement/source-derived-cr-declarations/manifest.json',
        'all_source_first_CR_differences':'refinement/source-derived-cr-declarations/discrepancies_unapplied.json',
        'all50_native_liaison_fields':'refinement/native-verification-meeting/results.json',
        'source_normalized_routing':'verified-routing-slice/manifest.json',
        'canonical_frozen_routing_alignment':'refinement/routing_frozen_alignment.json',
        'documentary_normative_example':'refinement/normative-trace/evidence-excerpt.json',
        'frozen_links_vs_source_investigation':'refinement/review-evidence/trace_boundary.json',
        'accessible_official_final_document':'refinement/review-evidence/external_document_access.json',
        'pinned_comparator_routing_record_scope':'refinement/review-evidence/comparator_scope.json',
        'public_vs_local_disclosure_ownership':'refinement/review-evidence/public_disclosure.json',
        'root_native_example_verification':'refinement/normative-root-verification.json',
        'retained75_trials':'matched/analysis.json',
        'public371_contracts':'https://github.com/spectra-ontology/spec-trace/blob/2b6f57e9b0cac90252b9fb4c8847bd67315a3222/release_package/cqs/original_core_repair/REVIEW_GUIDE.md',
        'public371_revision_accounting':'https://github.com/spectra-ontology/spec-trace/blob/2b6f57e9b0cac90252b9fb4c8847bd67315a3222/release_package/cqs/original_core_repair/README.md',
        'local_followup_audit_of_public_repair_scorers':'refinement/other-session-contract-review.json',
        'proposed_manuscript_text':'manuscript_claim_revisions.txt',
        'expert_reviews':0,'new_model_calls_by_refinement':0,
        'limits':'The current guide supersedes historical labels; old data and scripts remain to make corrections inspectable. The exports and documentary example do not establish population accuracy, completeness, automated tracing performance, practitioner utility, or representation superiority.'}
    (a.output/'claim_source_map.json').write_text(json.dumps(claims,ensure_ascii=False,indent=2)+'\n')
    (a.output/'README.txt').write_text('Start with REVIEW_ENTRY_POINT.txt, then REVIEW_GUIDE.txt and response_draft.txt.\nRequires Python 3.10+ and rdflib 7.6.0 for executable RDF checks.\nRun python3 -B verify_refinement.py for offline verification, including fresh SQL/SPARQL execution.\nStatus: locally prepared; not posted or uploaded. Expert reviews: zero.\nThe earlier README and claim map are retained under history and are superseded.\nOriginal-source excerpts remain attributed to their 3GPP providers.\n')
    # The old archive is immutable. Original pins and packaged bytes are distinct.
    package={'previous_archive_sha256':original_zip_hash,
        'previous_archive_entries':428,'previous_archive_preserved_on_disk':True,
        'new_file_provenance':provenance,'full_native_sources_included':False,
        'native_authentication_vs_offline_check':'Original input/producer hashes refer to source artifacts; SHA256.json authenticates packaged bytes after private-path anonymization.',
        'excluded':'Full native DOC/DOCX/FODT, LibreOffice profiles, frozen TTL/PDF, original downloads, comparator datasets, host/process logs and model-thread identifiers. The new source-derived RDF N-Triples is included; no operational database or native full document is packaged.',
        'status':'LOCAL_PREPARED_NOT_POSTED_OR_UPLOADED'}
    (a.output/'package_provenance.json').write_text(json.dumps(package,ensure_ascii=False,indent=2)+'\n')
    hits=[]
    private=re.compile(r'/home/(?!<)[A-Za-z0-9_.-]+|sk-(?:or-v1-)?[A-Za-z0-9_-]{20,}|Authorization\s*:\s*Bearer\s+\S+',re.I)
    for file in a.output.rglob('*'):
        if file.is_file() and private.search(file.read_text()):hits.append(str(file.relative_to(a.output)))
    assert not hits,hits
    hashes={str(file.relative_to(a.output)):digest(file.read_bytes()) for file in sorted(a.output.rglob('*')) if file.is_file() and file.name!='SHA256.json'}
    (a.output/'SHA256.json').write_text(json.dumps(hashes,sort_keys=True,indent=2)+'\n')
    with zipfile.ZipFile(a.zip,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for file in sorted(a.output.rglob('*')):
            if file.is_file():
                info=zipfile.ZipInfo(str(file.relative_to(a.output)),date_time=(1980,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
                z.writestr(info,file.read_bytes())
    report={'status':'LOCAL_PREPARED','ZIP':str(a.zip),'ZIP_sha256':digest(a.zip.read_bytes()),
        'ZIP_bytes':a.zip.stat().st_size,'files':len(hashes)+1,'hashes':len(hashes),
        'privacy_pattern_hits':hits,'previous_archive_sha256':original_zip_hash,
        'fresh_extracted_verification':'Still required; preparation alone is not verification.'}
    (r/'bundle_preparation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
