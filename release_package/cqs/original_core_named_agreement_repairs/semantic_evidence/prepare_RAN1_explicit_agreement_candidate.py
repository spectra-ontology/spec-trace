#!/usr/bin/env python3
"""Pin one unchanged question repair with an actual explicit source decision.

This prepares an AI primary judgment, never admission. The other AI reviewer
must inspect the original question and source paragraphs independently.
"""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT=Path('/home/sihyeon/workspace/spectra')
PUB=Path('/home/sihyeon/workspace/spectra-public/spec-trace/release_package/cqs')
HERE=Path(__file__).resolve().parent
ORIG=HERE.parent.parent/'original_repair'
sys.path.insert(0,str(ORIG))
import build


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utfsha(s): return hashlib.sha256(s.encode()).hexdigest()


def main():
    identity='RAN1_P2_CQ2-2'
    benchmark=PUB/'original_core_repair/provenance/original_benchmark.jsonl'
    original=next(json.loads(line) for line in benchmark.read_text().splitlines() if json.loads(line)['id']==identity)
    source_path=HERE/'RAN1_RAN2_named_decision_sources.json'
    source=json.loads(source_path.read_text())
    hits=[h for h in source['hits'] if h['question_identifier']=='R1-2001110']
    assert len(hits)==2 and len({h['source']['sha256'] for h in hits})==1
    actual=hits[0]
    literal={p['paragraph_zero_based']:p['literal_text'] for p in actual['literal_window']}
    assert literal[532]=='Agreement:' and literal[533].startswith('The draft CR in R1-2001110 is agreed with a modification')
    base=ROOT/'logs/publication/paper/under-review/kdd-2027-datasets-benchmarks/baseline-runs/_source_contract_expansion_v1'
    receipt_path=base/'receipts'/f'{identity}.json';rows_path=base/'rows'/f'{identity}.jsonl'
    receipt=json.loads(receipt_path.read_text());rows=[json.loads(line) for line in rows_path.read_text().splitlines()]
    query=original['cypher'];execution=receipt['execution']
    assert execution['query_utf8_sha256']==utfsha(query) and execution['rows_file_sha256']==sha(rows_path)
    assert execution['status']=='OK' and execution['full_json_rows_available'] and not execution['truncated']
    assert len(rows)==execution['row_count_retained']==2
    assert {r[1] for r in rows}=={'AGR-100-6.1-001'}
    assert all(r[2].splitlines()[0]==literal[533] for r in rows)
    db=HERE.parent/'relational/RAN1.sqlite';before=sha(db)
    con=sqlite3.connect('file:'+str(db)+'?mode=ro&immutable=1',uri=True)
    sql="""SELECT a.resolutionId,a.content,m.meetingNumber FROM Agreement a
        JOIN rel_REFERENCES e ON e.src_id=a.node_id JOIN Tdoc t ON t.node_id=e.dst_id
        JOIN rel_MADE_AT em ON em.src_id=a.node_id JOIN Meeting m ON m.node_id=em.dst_id
        WHERE t.tdocNumber='R1-2001110' ORDER BY m.meetingNumber"""
    actual_rows=[list(r) for r in con.execute(sql)];con.close()
    assert sorted((r[1],r[2],r[3]) for r in rows)==sorted(tuple(r) for r in actual_rows)
    assert before==sha(db)
    definition={'id':identity,'question_en':original['question_en'],'original_query':query,'reference_query':query,
                'required_fields':[{'name':'a.resolutionId','type':'string','nullable':False,'source_column_or_expression':'a.resolutionId'}],
                'collection':{'kind':'set'},'cardinality_policy':{'mode':'all'},
                'repair_class':'scorer_only','original_question_preserved':True}
    pin=build.digest(definition);criteria_sha=sha(ORIG/'criteria.json')
    q=original['question_en']
    findings=[
        "Original 'Which agreement' requests the agreement identity. Map a.resolutionId to the unique source-aligned Agreement. TDoc number is the fixed input; full parser content and Meeting aliases are context, not extra required fields. The original retained answer contract also names a.resolutionId, but this judgment is derived from the original English and the actual source rather than copied from that contract.",
        "Use all Agreements that refer to the fixed TDoc in the frozen RAN1 graph. Actual exact-query native output contains one Agreement identity with two MADE_AT aliases (RAN1#100 and RAN1#100-e). All122 retained RAN1/RAN2 report DOCX files were fully read; the two R1-2001110 occurrences are the title and explicit decision in one original RAN1#100-e block. This establishes the retained source context rather than a selected time/release window.",
        "REFERENCES alone was insufficient. New original source evidence explicitly says under 'Agreement:' that 'The draft CR in R1-2001110 is agreed with a modification...', and names its final CR revisions next. The Agreement's first content line equals this exact source decision. This is a contribution-specific adoption decision, rather than a merely incidental citation. No claim is made that this proves later TSG adoption or normative-text incorporation.",
        "The answer unit is Agreement identity, not TDoc, presentation alias or output row. Both full native rows have the same a.resolutionId and exact explicit-decision first line. Set semantics removes duplicate presentation aliases; no numeric count is requested.",
        "The original query has no LIMIT, optional nonnull restriction or additional filter. All actual native rows are retained and verified by the receipt's row count, query SHA and rows SHA. Both rows project to the one same Agreement ID. Full retained source scan found no second separate decision block for the fixed TDoc. No claim about unavailable historical records is added.",
        "The original requests neither answer sequence nor recency. Use an unordered complete identity set; Meeting alias differences and native return-row order do not create answer order requirements. There is no cutoff or boundary tie rule.",
        "The original parenthetical describes contribution tracing; the requested endpoint is an Agreement, not a verified final normative clause. The actual source explicitly adopts the named draft CR with modifications. Do not generalize this result to every REFERENCES edge or to causal influence of every contribution. AI primary only; no human/expert verification, native re-execution, model prediction or admission is claimed."
    ]
    units=json.loads((ORIG/'criteria.json').read_text())['semantic_units']
    clauses=["MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc {tdocNumber: 'R1-2001110'}), (a)-[:MADE_AT]->(m:Meeting)",
             'RETURN t.tdocNumber, a.resolutionId, a.content, m.meetingNumber']
    context={'original_source_scan':{'path':str(source_path.relative_to(ROOT)),'sha256':sha(source_path),'whole_reports_read_n':source['source_reports_n']},
             'actual_original_decision':{'source':actual['source'],'paragraph_zero_based':[531,532,533,534],
                                        'literal_paragraphs':[{k:v for k,v in p.items()} for p in actual['literal_window'] if 531<=p['paragraph_zero_based']<=534]},
             'actual_frozen_sqlite_crosscheck':{'path':str(db.relative_to(ROOT)),'sha256_before':before,'sha256_after':sha(db),
                                                'read_only':True,'query':sql,'rows':actual_rows},
             'actual_native_reference':{'receipt_path':str(receipt_path.relative_to(ROOT)),'receipt_sha256':sha(receipt_path),
                                        'rows_path':str(rows_path.relative_to(ROOT)),'rows_sha256':sha(rows_path),
                                        'query_sha256':utfsha(query),'row_count':len(rows),'full_output':True,
                                        'unique_requested_identity_count':1}}
    primary={'id':identity,'status':'pass','reviewer_kind':'AI source-first primary semantic review',
             'criteria_sha256':criteria_sha,'repair_sha256':pin,'original_question_sha256':utfsha(q),
             'query_choice':'original','repair_class':'scorer_only','required_fields':definition['required_fields'],
             'collection':definition['collection'],'cardinality_policy':definition['cardinality_policy'],
             'semantic_evidence':[{'unit':unit,'status':'pass','original_quote':q,'query_clauses':clauses,
                                   'finding':finding,'source_evidence':context} for unit,finding in zip(units,findings)],
             'expert_validation_n':0,'human_author_review_completed':False}
    build.review_schema.check_pass(primary,q,units,criteria_sha=criteria_sha,identity_key='repair_sha256',identity_sha=pin)
    candidate={**definition,'repair_sha256':pin,'criteria_sha256':criteria_sha,'original_question_sha256':utfsha(q),
               'original_query_sha256':utfsha(query),'reference_query_sha256':utfsha(query),
               'source_context':context,'primary_review':primary,'admitted':False,'new_model_calls':0,
               'integration_gates':['Separate exact-SHA AI secondary semantic judgment','Native provenance source-guard validation','Requested-field strict scorer and negative controls'],
               'repair_reason':'Prior citation-only cause is supplemented by the actual original report explicit named-draft-CR agreement decision. Extra projection fields cease to be required answers.'}
    out=HERE/'RAN1_explicit_agreement_candidates';out.mkdir(exist_ok=True)
    path=out/'candidates.jsonl';path.write_text(build.scorer.get_kernel().json_exact(candidate)+'\n')
    print(json.dumps({'id':identity,'repair_sha256':pin,'candidate_file_sha256':sha(path),'status':'PRIMARY_PASS_REQUIRES_SECONDARY_AND_TECHNICAL_GATES'}))


if __name__=='__main__': main()
