"""Prepare a new whole-authored-input config for the immutable shared runner."""
import importlib.util
import json
import os
from pathlib import Path
import resource
import shutil
from prepare_RAN4_calendar58_authored_raw_retrieval_inputs_v1 import HERE,B,ROOT,pin,read,save,canon

REG=B/'RAN1/source_variant_OpenRouter_registration'
PRIOR=REG/'source58'
OUT=REG/'source58_fullbody_v2'
RAW=HERE/'calendar58_authored_full_raw_retrieval_inputs_v2'

def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3))
    assert not OUT.exists();OUT.mkdir();(OUT/'schemas').mkdir()
    ip=RAW/'whole_authored_raw_inventory.json';inventory=json.loads(ip.read_text())
    assert inventory['status']=='all342_whole_Word_bodies_and4_whole_PPTX_XML_text_freshly_projected'
    assert inventory['original_Word_body_observations_n']==342 and inventory['whole_PPTX_packages_n']==4
    raw=Path(inventory['raw_inputs_pin']['path']);assert pin(raw)==inventory['raw_inputs_pin']
    ledger=read(HERE/'RAN4_actual_calendar_Meeting_source_context_v2/own_event_period_resolution_v3_authored_calendar_corroboration/all58_original_Meeting_source_reported_period_ledger.jsonl')
    wanted={}
    for item in ledger:
        for s in item['all_identity_matched_source_report_witnesses']:
            key=(s['original_source_file_pin']['path'],s['archive_member'])
            for role in ['actual_title_paragraph','actual_immediately_following_period_paragraph']:
                p=s[role];wanted.setdefault(key,{})[p['all_document_raw_paragraph_zero_based']]=p['literal_authored_text_with_tabs_and_breaks']
    found=set();rows=0;paragraphs=0;seen=set()
    with raw.open()as stream:
        for line in stream:
            r=json.loads(line);assert set(r)=={'source_row','fields','source_cell_coordinates'}and r['source_row']not in seen
            seen.add(r['source_row']);rows+=1;c=r['source_cell_coordinates']
            start,end=c['paragraph_range_zero_based'];values=r['fields'].get('paragraph_texts_in_document_order',r['fields'].get('paragraph_texts_in_part_order'))
            assert end-start+1==len(values);paragraphs+=len(values)
            key=(str(ROOT/c['original_source_relative_path']),r['fields']['filename'])
            if 'document_XML_sha256'in c:
                for index,literal in wanted.get(key,{}).items():
                    if start<=index<=end:
                        assert values[index-start]==literal;found.add((key,index))
    assert rows==inventory['raw_rows_n']and paragraphs==inventory['actual_raw_paragraphs_n']
    assert found=={(key,index)for key,items in wanted.items()for index in items}
    support_path=OUT/'whole_raw_all58_own_period_source_support.json'
    save(support_path,{'status':'pass','whole_authored_inventory_pin':pin(ip),'whole_raw_inputs_pin':pin(raw),
        'whole_Word_body_observations_n':342,'whole_PPTX_packages_n':4,'all_source_own_date_witnesses_n':321,
        'all_title_and_adjacent_date_coordinates_supported':True,'unique_supported_raw_coordinates_n':len(found),
        'all58_Meeting_nodes_supported':True,'raw_rows_n':rows,'raw_paragraphs_n':paragraphs,
        'all_original_member_packages_preserved_in_bin_shards':True,'text_projection_is_not_OCR_or_binary_object_semantics':True,
        'human_author_review_completed':False,'expert_validation_n':0,'API_native_calls_n':0,'helper_pin':pin(Path(__file__))})
    for name in ['tasks.jsonl']:
        shutil.copy2(PRIOR/name,OUT/name)
    for p in(PRIOR/'schemas').glob('*.json'):shutil.copy2(p,OUT/'schemas'/p.name)
    prior_config=json.loads((PRIOR/'source_config.json').read_text())
    gate=json.loads((PRIOR/'complete_actual_source58_question_gate.json').read_text())
    gate.update(raw_source_variant='whole_all342_document_bodies_and4_whole_PPTX_XML_paragraphs',
        whole_authored_inventory_pin=pin(ip),whole_raw_support_pin=pin(support_path),
        prior_window_actual_gate_pin=pin(PRIOR/'complete_actual_source58_question_gate.json'),
        original_native_semantic_source_materialization_gates_unchanged=True,
        whole_report_body_raw_text_provided=True,full_binary_object_semantics_established=False,
        legacy_DOC_access_derivatives_n=23)
    gate_path=OUT/'complete_actual_source58_whole_input_question_gate.json';save(gate_path,gate)
    corpus=OUT/'retrieval_corpus'
    config={**prior_config,'candidate_path':str(OUT/'tasks.jsonl'),'raw_records_path':str(raw),'expected_raw_rows_n':rows,
        'graph_schema_path':str(OUT/'schemas/RAN4_graph.json'),'sql_schema_path':str(OUT/'schemas/RAN4_sql.json'),
        'retrieval_corpus_dir':str(corpus),'retrieval_augmentation_manifest_path':str(corpus/'augmentation_manifest.json'),
        'actual_gate_pin':pin(gate_path),
        'retrieval_source_disclosure':'Base lexical corpus plus all342 authentic retained report Word bodies and all XML paragraph text of4 authored arrangements PPTX packages, including slides, notes, masters and layouts. All raw tracked runs, empty paragraphs and tabs/breaks are retained in consecutive paragraph-boundary chunks.23 legacy DOC observations use pinned access derivatives; original member/derivative bytes are preserved separately.',
        'paired_source_disclosure':'Every one of321 own-report title/adjacent-period witnesses supporting58 calendar records occurs in the whole authored raw inputs. No computed ISO dates, canonical meeting labels, gold, reviews, reference query or filtered CR answers enter retrieval. All actual document.xml body paragraphs are projected; OCR, embedded binary-object semantics and equality of the prior lexical corpus to the graph are not established.'}
    cp=OUT/'source_config.json';save(cp,config)
    builder_path=REG/'build_retrieval_snapshot.py';builder=module(builder_path,'source58_fullbody_immutable_builder')
    base=ROOT/'logs/publication/paper/under-review/kdd-2027-datasets-benchmarks/baseline-runs/_matched_retrieval_v1/corpus/ran4.sqlite3'
    builder.main(base,raw,corpus,'RAN4',rows,'source58_all342_whole_report_bodies_and4_whole_PPTX_XML')
    ready=OUT/'ready_source58_whole_body_evaluation_manifest.json'
    save(ready,{'status':'separate_source58_whole_authored_inputs_prepared_no_model_native_calls','config_pin':pin(cp),
        'task_pin':pin(OUT/'tasks.jsonl'),'original_window_ready_pin':pin(PRIOR/'ready_source58_evaluation_manifest.json'),
        'whole_authored_inventory_pin':pin(ip),'whole_raw_inputs_pin':pin(raw),'raw_support_pin':pin(support_path),
        'actual_gate_pin':pin(gate_path),'augmentation_pin':pin(corpus/'augmentation_manifest.json'),
        'whole_report_bodies_n':342,'whole_PPTX_packages_n':4,'raw_rows_n':rows,'actual_raw_paragraphs_n':paragraphs,
        'existing_shared_runner_pin':pin(REG/'source_enriched_evaluation.py'),'existing_shared_builder_pin':pin(builder_path),
        'existing_window_config_and_all_shared_runtime_bytes_unchanged':True,'native_API_public_calls_n':0,
        'human_author_review_completed':False,'expert_validation_n':0,'builder_pin':pin(Path(__file__))})
    print(canon({'ready_manifest':pin(ready),'source_config':pin(cp),'raw_rows_n':rows,'native_API_calls_n':0}),flush=True)

if __name__=='__main__':main()
