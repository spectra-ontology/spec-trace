"""Retained processing-time recovery candidate, pending source admission.

The source-role table is independent. No per-ID or target-value branch is used.
"""
import json,re,sqlite3
from pathlib import Path
from collections import defaultdict
import capture_actual_fifteen_reports_47_contexts_v1 as s
import probe_generic_current_amendment_rule_v3 as old

CONDITIONAL_PROCESSING=re.compile(r'\bIf\s+UE\s+provides\s+the\s+measurement\s+report\b.*?\bthen\s+T_?processing\s+will\s+be\b.*?\bOtherwise\b.*?\bT_?processing\b',re.I)

def roles(a,c):
    lines=[{'line_index':i,'line':l}for i,l in old.technical_lines(a)if CONDITIONAL_PROCESSING.search(l)]
    fields=' '.join(c.get(k)or''for k in ['title','reasonForChange','summaryOfChange'])
    if lines and re.search(r'\bprocessing\s+time\b',fields,re.I)and re.search(r'\bRF\s+warm\s+up\b',fields,re.I)and re.search(r'\baddition\s+delay\b',fields,re.I):
        return[{'branch':'current_conditional_processing_delay_amendment','current_technical_parameter_lines':lines,'requires_finite_source_identity_certificate':True}]
    return[]

def main():
    prior=s.HERE/'actual_generic_current_amendment_candidate_rule_v5.json'
    old_result=json.loads(prior.read_text());db=s.R/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/relational/RAN4.sqlite';before=s.pin(db)
    con=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True);con.row_factory=sqlite3.Row;con.execute('pragma query_only=1')
    aa=[dict(r)for r in con.execute('select a.*,m.dst_id meeting_id from Agreement a join rel_MADE_AT m on m.src_id=a.node_id')]
    crs=defaultdict(list)
    for r in con.execute('select c.*,p.dst_id meeting_id from CR c join rel_PRESENTED_AT p on p.src_id=c.node_id where c.reasonForChange is not null'):crs[r['meeting_id']].append(dict(r))
    pairs={(r['resolutionId'],r['tdocNumber']):r for r in old_result['all_matched_paths']};new=[]
    for a in aa:
        for c in crs[a['meeting_id']]:
            matched=roles(a,c)
            if not matched:continue
            key=(a['resolutionId'],c['tdocNumber'])
            if key not in pairs:pairs[key]={'resolutionId':key[0],'tdocNumber':key[1],'roles':[],'CR':c}
            pairs[key]['roles'].extend(matched);new.append({'resolutionId':key[0],'tdocNumber':key[1],'roles':matched})
    rows=sorted(pairs.values(),key=lambda r:(r['tdocNumber'],r['resolutionId']));uniq={r['tdocNumber']:r['CR']for r in rows}
    complete=[{'tdocNumber':td,'reason':uniq[td]['reasonForChange'],'summary':uniq[td]['summaryOfChange']}for td in sorted(uniq)]
    con.close();assert s.pin(db)==before
    result={'status':'PROSPECTIVE_RETAINED_DOMAIN_V6_CANDIDATE_NOT_GOLD','recognizer':s.pin(Path(__file__)),'base_v5':s.pin(prior),'new_processing_paths':new,'all_matched_paths':rows,'candidate_full_three_fields':complete,'candidate_selected_max5':complete[:5],'all_distinct_candidate_CR':sorted(uniq),'Agreement_count':len(aa),'DB_before_after':before,'source_current_processing_counterexample':s.pin(s.HERE/'actual_87_processing_current_CR_bridge_NOT_gold_v1.json'),'scope':'All retained Agreement and captured nonnull-reason CR inputs are searched. Original DISTINCT/ASC/max5 and captured three fields are preserved. Source-role and earlier-entry completeness remain independent gates. This is a candidate, not final query, source certification or model output.','ROOT_seal':False,'API_native_public_mutations':0}
    output=s.save('actual_generic_current_amendment_candidate_rule_v6.json',result)
    print(json.dumps({'output':output,'paths':len(rows),'distinct':len(uniq),'new_paths':[(r['resolutionId'],r['tdocNumber'])for r in new],'provisional_max5':[r['tdocNumber']for r in complete[:5]]}))

if __name__=='__main__':main()
