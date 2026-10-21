"""Prospective retained-domain recovery, not a source admission or gold.

New current amendment candidates are separated from their source-role proof.
No Tdoc/Agreement ID, meeting number or target numerical value is a predicate.
"""
import json,re,sqlite3
from pathlib import Path
from collections import defaultdict
import capture_actual_fifteen_reports_47_contexts_v1 as s
import probe_generic_current_amendment_rule_v3 as old
import probe_earlier_retained_grammar_extensions_v2 as gramm

TIMING=re.compile(r'^\s*(MRTD|MTTD)\s*=\s*[-+]?\d+(?:\.\d+)?\s*(?:us|µs|μs)\s*$',re.I)
RATIO=re.compile(r'[-+]?\d+(?:\.\d+)?\s*%\s*of\s*CP\b',re.I)
INTERRUPT=re.compile(r'^\s*PCell\s+interruption\s+length\s+for\s+(?:inter-band\s+)?(?P<subject>[A-Z][A-Z0-9-]+)\s*:\s*\d+(?:\.\d+)?\s+subframes?\s+each\s*$',re.I)

def extra(a,c,sections):
    lines=old.technical_lines(a);body=old.retained_body(a)
    fields=' '.join(c.get(k)or''for k in ['title','reasonForChange','summaryOfChange'])
    out=[]
    tl=[{'line_index':i,'line':l}for i,l in lines if TIMING.match(l)]
    ss=[x for x in sections if x['sectionTitle']and x['sectionTitle'].lower()=='timing']
    if tl and ss and re.search(r'\bendorsed\s+draft\s*CRs?\b',fields,re.I):
        out.append({'branch':'compiled_endorsed_current_timing_amendment','current_technical_parameter_lines':tl,'retained_modified_Timing_sections':ss,'requires_finite_source_identity_certificate':True})
    ratios=[{'line_index':i,'line':l}for i,l in lines if RATIO.search(l)]
    if ratios and re.search(r'\bEVM\s+window\s+length\b',body,re.I)and re.search(r'\bEVM\s+window\s+length\b',fields,re.I):
        out.append({'branch':'current_CP_ratio_EVM_window_compilation','current_technical_ratio_lines':ratios,'retained_named_target':'EVM window length','requires_finite_source_identity_certificate':True})
    for i,l in lines:
        m=INTERRUPT.match(l)
        if not m:continue
        subject=m.group('subject')
        if re.search(r'\b'+re.escape(subject)+r'\b',fields,re.I)and re.search(r'\b(?:introduc(?:e|ed|ing|tion)|added\s+reference)\b',fields,re.I):
            out.append({'branch':'current_interruption_subject_normative_incorporation_candidate','line_index':i,'line':l,'subject':subject,'requires_finite_source_identity_and_normative_incorporation_adjudication':True})
    return out

def main():
    prior=json.loads((s.HERE/'actual_generic_current_amendment_candidate_rule_v4.json').read_text());before=s.pin(s.R/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/relational/RAN4.sqlite')
    db=s.R/before['path'];c=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row;c.execute('pragma query_only=1')
    aa=[dict(r)for r in c.execute('select a.*,m.dst_id meeting_id from Agreement a join rel_MADE_AT m on m.src_id=a.node_id')]
    by=defaultdict(list);secs=defaultdict(list);specs=defaultdict(set)
    for r in c.execute('select c.*,m.dst_id meeting_id from CR c join rel_PRESENTED_AT m on m.src_id=c.node_id where c.reasonForChange is not null'):by[r['meeting_id']].append(dict(r))
    for r in c.execute('select x.src_id,s.*from rel_MODIFIES_SECTION x join Section s on s.node_id=x.dst_id'):
        d=dict(r);secs[d.pop('src_id')].append(d)
    for r in c.execute('select x.src_id,s.specNumber from rel_MODIFIES x join Spec s on s.node_id=x.dst_id'):specs[r[0]].add(r[1])
    pairs={(r['resolutionId'],r['tdocNumber']):r for r in prior['all_matched_paths']}
    for a in aa:
        for cr in by[a['meeting_id']]:
            roles=gramm.matches(a,cr,specs[cr['node_id']])+extra(a,cr,secs[cr['node_id']])
            if not roles:continue
            key=(a['resolutionId'],cr['tdocNumber'])
            if key not in pairs:pairs[key]={'resolutionId':a['resolutionId'],'tdocNumber':cr['tdocNumber'],'roles':[],'CR':cr}
            pairs[key]['roles'].extend(roles)
    rows=sorted(pairs.values(),key=lambda r:(r['tdocNumber'],r['resolutionId']));uniq={r['tdocNumber']:r['CR']for r in rows};full=[{'tdocNumber':td,'reason':uniq[td]['reasonForChange'],'summary':uniq[td]['summaryOfChange']}for td in sorted(uniq)]
    c.close();assert s.pin(db)==before
    out={'status':'PROSPECTIVE_RETAINED_DOMAIN_V5_CANDIDATE_NOT_GOLD','recognizer':s.pin(Path(__file__)),'base_v4':s.pin(s.HERE/'actual_generic_current_amendment_candidate_rule_v4.json'),'earlier_grammar':s.pin(s.HERE/'probe_earlier_retained_grammar_extensions_v2.py'),'all_matched_paths':rows,'candidate_full_three_fields':full,'candidate_selected_max5':full[:5],'all_distinct_candidate_CR':sorted(uniq),'Agreement_count':len(aa),'DB_before_after':before,'scope':'Source certification of exact current amendment identities and every earlier eligible entrant is independent. These lexical/structural recognizers are finite-domain candidates, not a universal approval classifier. No source body is added to model/runtime inputs. Original DISTINCT/tdoc ASC/LIMIT maximum5/three captured fields preserved.','pending_gate':'Independent original-role adjudication of normative incorporation, new compiled cases and full earlier prefix completeness; no query freeze/native/API.','ROOT_seal':False,'API_native_public_mutations':0}
    pin=s.save('actual_generic_current_amendment_candidate_rule_v5.json',out);print(json.dumps({'output':pin,'paths':len(rows),'distinct':len(uniq),'selected':[r['tdocNumber']for r in full[:5]],'prefix_paths':[(r['resolutionId'],r['tdocNumber'])for r in rows if r['tdocNumber']<='R4-1808472']}))
if __name__=='__main__':main()
