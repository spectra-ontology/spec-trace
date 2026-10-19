"""Build a portable additive patch only. Never creates the full source snapshot."""
import argparse, collections, difflib, hashlib, importlib.util, json, shutil, sqlite3, sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('source_snapshot_common',HERE/'source_snapshot_common.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    p.add_argument('--output',type=Path,default=HERE/'package')
    a=p.parse_args();root=a.source_root.resolve();out=a.output
    b=root/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/overnight_reaudit'
    n=b/'root_evidence/two_agent_unresolved_loop/RAN2_RAN5/source_lane13'
    g=n/'RAN4_93_generic_own_summary_projection';r=n/'RAN4_93_default_and_approved_record_authority'
    prior=b/'RAN3_RAN4/RAN4_93_Annex_D_and_whole_document_decision_roles_v1'
    base_sql=b.parent/'relational/RAN4.sqlite';base_rdf=root/'release_package/kg/per_wg/RAN4-body.ttl'
    assert not out.exists(),'Immutable output: choose a new directory'
    assert s.sha(base_sql)=='24b8d938d456472ad7005178a65acb105857eebc3b96bd9ed8027703b8158c0a'
    assert s.sha(base_rdf)=='90c6bf7d4420949b7395e8a0b5700a07f8866ddd461699d4516fe4e4f5deec5d'
    assert s.sha(g/'all1858_generic_own_summary_field_observations.jsonl')=='04e21a2177f2dd2ec858c6cde80bb130450a679e2bc8735432de25cb00e60794'
    assert s.sha(prior/'all1858_CR_family_source_Decision_boundaries.jsonl')=='a387121431a30c051c429641bd822b8d7525403e176bb29f264e0564f64ce901'
    assert s.sha(r/'actual_approved_report_and_rank_boundary_source_receipt.json')=='5948657f662d6cc8d127cb8f33ad021a7c5212d24269970cdedb10d906ba5944'
    (out/'source').mkdir(parents=True);(out/'query').mkdir();(out/'patch').mkdir()
    (out/'pipeline').mkdir();(out/'verification_only').mkdir()
    copies={
      prior/'all3112_actual_source_register_identity_rows.jsonl':'source/all3112_register.jsonl',
      g/'all1858_generic_own_summary_field_observations.jsonl':'source/all1858_observations.jsonl',
      prior/'all1858_CR_family_source_Decision_boundaries.jsonl':'source/all1858_report_decision_boundaries.jsonl',
      r/'actual_approved_report_and_rank_boundary_source_receipt.json':'source/approved_report_authority_receipt.json',
      root/'release_package/pipeline/load_released_kg.py':'pipeline/load_released_kg.py',
      g/'generic_rule_and_scope.json':'source/generic_rule_and_scope.json',
      g/'replay_generic_own_summary.py':'source/original_generic_extraction_helper.py',
      g/'actual_generic_whole1858_source_replay_receipt.json':'verification_only/generic_whole1858_receipt.json',
      g/'actual_finite17_identity_format_boundary_receipt.json':'verification_only/finite17_actual_identity_format_receipt.json',
      g/'all17_complete_identity_form_format_and_decision_review.json':'verification_only/finite17_complete_identity_format_decision_review.json',
      g/'four_frozen_NULL_direct_original_form_XML_review_packet.json':'verification_only/four_original_DOCX_XML_review_packet.json',
      g/'six_existing_non_NULL_conflicts_preserved.json':'verification_only/six_existing_non_NULL_conflicts_preserved.json',
      r/'source_context_contract_and_remaining_execution_gate.json':'verification_only/source_context_contract_review.json',
    }
    inputpins=[]
    for src,dst in copies.items():
        shutil.copy2(src,out/dst);inputpins.append(s.pin(src,str(src.relative_to(root))))
    for f in ['source_snapshot_common.py','build_portable_patch.py','verify_portable_patch.py','materialize_source_snapshot_root.py']:
        shutil.copy2(HERE/f,out/f)
    register=s.rows(out/'source/all3112_register.jsonl')
    observations=s.rows(out/'source/all1858_observations.jsonl')
    roles=s.rows(out/'source/all1858_report_decision_boundaries.jsonl')
    authority=json.loads((out/'source/approved_report_authority_receipt.json').read_text())
    db=sqlite3.connect('file:'+str(base_sql)+'?mode=ro&immutable=1',uri=True)
    anchors=[]
    for rec in sorted(register,key=lambda r:r['tdocNumber']):
        matches=[dict(zip(['node_id','source_iri','labels_json','properties_json','iri'],x)) for x in db.execute(
          'SELECT r.node_id,r.source_iri,r.labels_json,r.properties_json,i.iri FROM Tdoc t JOIN _node_record r USING(node_id) JOIN node_identity i USING(node_id) WHERE t.tdocNumber=? ORDER BY r.node_id',(rec['tdocNumber'],))]
        anchors.append({'tdocNumber':rec['tdocNumber'],'matches':matches,
          'claim':'Literal ID match only; no physical body/version equality inferred.'})
    db.close();s.write_rows(out/'source/exact_frozen_ID_anchors.jsonl',anchors)
    mapping=s.make_graph(register,observations,roles,anchors,authority)
    s.write_json(out/'patch/additive_node_edge_mapping.json',mapping)
    (out/'patch/additive_source_records.ttl').write_bytes(s.ttl_bytes(mapping))
    (out/'query/original_English.txt').write_bytes(s.ORIGINAL_EN.encode())
    (out/'query/original_query.cypher').write_bytes(s.ORIGINAL_QUERY.encode())
    (out/'query/separate_source_query.cypher').write_text(s.SOURCE_CYPHER)
    (out/'query/separate_source_query.sql').write_text(s.SOURCE_SQL)
    diff=''.join(difflib.unified_diff(s.ORIGINAL_QUERY.splitlines(True),s.SOURCE_CYPHER.splitlines(True),
          fromfile='preserved_original_query.cypher',tofile='separate_source_variant_query.cypher'))
    (out/'query/original_to_source_query.diff').write_text(diff)
    caveats={
      'kind':'Separate source graph variant; original English/query immutable, original560 pass increment0.',
      'fullbase_policy':'Copy all80 original SQL table schemas and original records; additive new labels/relationships only. Original RDF exact byte prefix.',
      'source_population':'All3112 original register documentary records;1858 CR/draftCR/pCR;1343 generic own-form unique summary observations,132 missing ZIP,515 unsupported unique summary.',
      'new_labels':['SourceMeetingRecord','SourceMeetingDocument','SourceOwnCRSummary'],
      'query_extent':'Select eligible first10 by originalP4 TdocASC before LEFT/OPTIONAL summary projection. Never skip missing summary or unknown value; answers multiset10/6distinct.',
      'approval_scope':'Final documented WG outcomes in later-approved report packet; no TSG approval, normative incorporation or physical-week timing assertion.',
      'whole1343_certification':False,
      'CFB_caveat':'Five finite17 source fields use existing exact-member legacyDOC conversion; direct CFB text/deletion corroborates them, but originalCFB strike is not decoded. The four new needed values are directoriginalDOCX.',
      'whole_population_format_caveat':'XML deletion/strike/style references retained; full inherited-style semantics not certified for all1343.',
      'six_non_NULL_conflicts':'Preserved as source/frozen separate values. No normalization, overwrite or automatic version identity.',
      'ID_link_caveat':'SOURCE_REGISTER_ID_MATCH encodes exact literal ID only. Never body/version equivalence.',
      'model_input_policy':'If evaluated, allmethods receive the same full source snapshot/schema/common retrieval context. No selected10 fixture/verification_only directory silently added to retrieval.',
      'included_replay_boundary':'Included raw structured observations and source identity pins replay; not a fresh full1858 physical source parser execution. Original replay helper and receipts are pinned.',
      'not_admission':'Root independent seven-unit review, actual isolated native/fullSQL/scorer/fair-input/freeze gates remain required.',
      'API_calls':0,'native_DB_calls':0,'central_changes':0,'public_changes':0,'original560_pass_increment':0,
    }
    s.write_json(out/'scope_and_limitations.json',caveats)
    text="""# RAN4#93 additive source snapshot, separate variant

The original English/query bytes are preserved in query/. The source query uses all3112 original documentary register rows and all1343 generic own-form summary observations. It selects eligibility and first10 before LEFT/OPTIONAL summary projection. The output contract is a multiset of summary strings:10 occurrences,6 distinct. It does not filter unavailable summaries to replace them with later rows.

No frozen Tdoc/CR property, label or relationship is overwritten. All80 old SQLite table schemas and old records are checked by a root-only optional materializer. Original RDF bytes are copied as an exact prefix. New source labels carry role/status/revision and provenance; exact ID edges do not prove physical/version identity.

Whole1343 certification is NOT claimed.132 archives are missing and515 records have no supported unique summary. Original CFB strike is not decoded; five finite17 fields reuse exact-member legacy conversions. Four newly needed summary values were directly checked in original DOCX XML/styles. Six existing non-NULL differences remain separate.

Only included-data patch replay and preflight are run by the source agent. No full snapshot/native/model/public/central execution or original560 pass increment occurs.

Commands, from this directory:

    python3 -B -I verify_portable_patch.py
    python3 -B -I materialize_source_snapshot_root.py --baseline-sql /path/to/RAN4.sqlite --baseline-rdf /path/to/RAN4-body.ttl --preflight-only

Root optional actual isolated materialization (new output required):

    python3 -B -I materialize_source_snapshot_root.py --baseline-sql /path/to/RAN4.sqlite --baseline-rdf /path/to/RAN4-body.ttl --output /new/private/RAN4-source93

verification_only/ is evidence for the gate, not automatically model retrieval input. Every method must share the same full source snapshot/context policy if the variant is later evaluated.
"""
    (out/'README.md').write_text(text)
    files=[s.pin(f,str(f.relative_to(out))) for f in sorted(out.rglob('*')) if f.is_file()]
    manifest={'status':'PROSPECTIVE_ADDITIVE_SEPARATE_SOURCE_GRAPH_PATCH_NOT_FROZEN_ADMISSION',
      'original_id':'RAN4_P4_CQ4-5','working_group':'RAN4',
      'baseline':{'SQLite':s.pin(base_sql,str(base_sql.relative_to(root))),'RDF':s.pin(base_rdf,str(base_rdf.relative_to(root))),
        'nodes':s.BASE_N,'relationships':s.BASE_E,'SQL_tables':80},
      'source_input_pins':inputpins,'files':files,
      'new_node_counts':dict(collections.Counter(n['labels'][0] for n in mapping['nodes'])),
      'new_relationship_counts':dict(collections.Counter(e['rel_type'] for e in mapping['edges'])),
      'source_register_ID_match_multiplicity':dict(collections.Counter(str(len(r['matches'])) for r in anchors)),
      'source_population':{'register':3112,'CR_family':1858,'unique_own_summary':1343,'missing_archive':132,'unsupported_unique_summary':515},
      'all_full1343_certified':False,'no_selected_ID_extraction_predicate':True,
      'no_original_property_overwritten':True,'original_English_sha256':hashlib.sha256(s.ORIGINAL_EN.encode()).hexdigest(),
      'original_query_sha256':hashlib.sha256(s.ORIGINAL_QUERY.encode()).hexdigest(),
      'model_outputs_consulted':False,'API_calls':0,'native_calls':0,'central_changes':0,'public_changes':0,'original560_pass_increment':0,
      'remaining_gates':['Independent final-record approval/default interpretation','Actual isolated native/fullSQL/scorer/fair-input/freeze gates','No generic whole1343 certification claim']}
    s.write_json(out/'manifest.json',manifest)
    result=s.verify_package(out,out/'pipeline/load_released_kg.py')
    s.write_json(HERE/'actual_portable_patch_build_and_included_replay_receipt.json',{
      'status':'PASS_ACTUAL_SMALL_PORTABLE_PATCH_ONLY','manifest':s.pin(out/'manifest.json'),
      'result':result,'full_snapshot_created':False,'original_input_hashes_rechecked':True,
      'builder':s.pin(Path(__file__)),'API_calls':0,'native_calls':0,'central_changes':0,'public_changes':0})
    print(json.dumps({'status':'PASS','manifest':s.pin(out/'manifest.json'),'result':result},ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()

