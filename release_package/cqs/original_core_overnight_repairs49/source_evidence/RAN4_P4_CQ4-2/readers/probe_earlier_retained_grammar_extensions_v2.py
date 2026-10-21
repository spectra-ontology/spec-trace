"""Exploratory data-derived retained grammar for earlier source-positive amendments.

These candidate clauses remain separate from independent source adjudication.
No query/native freeze, answer IDs, target numeric values or minimum word-count
thresholds are used by the predicates.
"""
import json,re,sqlite3
from pathlib import Path
from collections import defaultdict
import capture_actual_fifteen_reports_47_contexts_v1 as s
import probe_generic_current_amendment_rule_v3 as old

SAME=re.compile(r'^\s*(?P<entity>.+?)\s+(?:shall|should|must)\s+have\s+the\s+same\s+(?P<feature>.+?)\s+in\s+terms\s+of\s+(?P<attribute>.+?)\s+for\s+both\s+(?P<state1>.+?)\s+and\s+(?P<state2>.+?)[.\s]*$',re.I)
REUSE=re.compile(r'^\s*for\s+(?:the\s+)?(?P<target>.+?),\s*(?:the\s+)?(?P<feature>.+?)\s+from\s+(?P<prior>.+?)\s+can\s+be\s+reused[.\s]*$',re.I)
Q_SPEC=re.compile(r'\brequirement\s+(?:shall|should|must)\s+be\s+\d+(?:\.\d+)?\s*\S+\s+for\s+(?P<qualified_entity>.+?)\s+in\s+TS\s*(?P<spec>\d{2}\.\d{3}(?:-\d+)?)\b',re.I)

def tokens(v):
    v=(v or'').lower().replace('de-activated','deactivated').replace('(s)','s')
    return [x[:-1]if len(x)>1 and x.endswith('s')and not x.endswith('ss')else x for x in re.findall(r'[a-z0-9]+',v)]
def canon(v):return ' '.join(tokens(v))
def target_tokens(v):
    # Structural prepositions/articles and the inherited source RAT label are
    # removed only for this reuse grammar; the exact original target is saved.
    # E-UTRA and LTE are paired explicitly in the source reuse proposition.
    v=re.sub(r'\bE-UTRA\b','LTE',v,flags=re.I)
    return [x for x in tokens(v)if x not in {'the','on','in','of','for','to','a','an'}]
def own_header(a,c):
    return any((m:=old.HEADER.match(l))and m.group(1)==c['tdocNumber']for l in old.retained_body(a).splitlines())
def matches(a,c,specs):
    if not own_header(a,c):return []
    text=canon((c.get('title')or'')+' '+(c.get('reasonForChange')or'')+' '+(c.get('summaryOfChange')or''))
    words=set(text.split());out=[]
    for i,line in old.technical_lines(a):
        m=SAME.match(line)
        if m:
            d=m.groupdict()
            if all(x in words for part in ['entity','feature','attribute','state1']for x in tokens(d[part])):
                out.append({'branch':'same_feature_in_attribute_for_both_states','line_index':i,'line':line,'parsed_source_roles':d})
        m=REUSE.match(line)
        if m:
            d=m.groupdict();target=target_tokens(d['target']);feature=target_tokens(d['feature'])
            prior=tokens(d['prior'])
            # Prior LTE and E-UTRA are explicitly the same source network in
            # this retained act, not a learned title-similarity threshold.
            if all(x in words for x in target+feature+prior):
                out.append({'branch':'reuse_same_target_requirements_from_named_source','line_index':i,'line':line,'parsed_source_roles':d,'canonical_target_tokens':target})
        m=Q_SPEC.search(line)
        if m:
            d=m.groupdict();parts=d['qualified_entity'].split()
            # The last word is the entity head; preceding qualifiers are the
            # data-derived qualifiers of the explicitly named target Spec.
            qualifiers=parts[:-1]
            if d['spec']in specs and qualifiers and all(x in words for q in qualifiers for x in tokens(q)):
                out.append({'branch':'current_quantified_requirement_in_explicit_spec','line_index':i,'line':line,'parsed_source_roles':d,'qualifiers':qualifiers})
    return out

def main():
    db=s.R/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/relational/RAN4.sqlite'
    before=s.pin(db);c=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row;c.execute('pragma query_only=1')
    aa=[dict(r)for r in c.execute('select a.*,m.node_id as meeting_id,m.meetingNumberInt as meeting_int from Agreement a join rel_MADE_AT e on e.src_id=a.node_id join Meeting m on m.node_id=e.dst_id')]
    crs=defaultdict(list)
    for r in c.execute('select c.*,e.dst_id as meeting_id from CR c join rel_PRESENTED_AT e on e.src_id=c.node_id where c.reasonForChange is not null'):crs[r['meeting_id']].append(dict(r))
    specs=defaultdict(set)
    for r in c.execute('select x.src_id,s.specNumber from rel_MODIFIES x join Spec s on s.node_id=x.dst_id'):specs[r[0]].add(r[1])
    results=[];grammar_acts=[]
    for a in aa:
        acts=[{'line_index':i,'line':l}for i,l in old.technical_lines(a)if SAME.match(l)or REUSE.match(l)or Q_SPEC.search(l)]
        if acts:grammar_acts.append({'resolutionId':a['resolutionId'],'acts':acts})
        for cr in crs[a['meeting_id']]:
            roles=matches(a,cr,specs[cr['node_id']])
            if roles:results.append({'resolutionId':a['resolutionId'],'tdocNumber':cr['tdocNumber'],'roles':roles,'CR':cr})
    c.close();assert s.pin(db)==before
    seen={r['tdocNumber']:r['CR']for r in results}
    out={'status':'EXPLORATORY_ADDITIONAL_RETAINED_GRAMMAR_NOT_SOURCE_ADJUDICATED_OR_GOLD','recognizer':s.pin(Path(__file__)),'base_recognizer_not_modified':s.pin(s.HERE/'probe_generic_current_amendment_rule_v3.py'),
    'Agreement_count':len(aa),'all_grammar_matching_technical_acts':grammar_acts,'all_additional_paths':results,'additional_distinct_CRs':sorted(seen),
    'source_status':'Independent actual source packets and ROOT role verdicts are separate. Source-positive completeness and pending normative incorporation/principle-acceptance cases must be resolved before any query or gold freezes.',
    'whole_domain_execution_not_global_role_certification':True,'DB_before_after':before,'ROOT_seal':False,'API_native_public_mutations':0}
    pin=s.save('diagnostic_earlier_retained_grammar_extensions_v2.json',out)
    print(json.dumps({'output':pin,'grammar_acts':len(grammar_acts),'paths':len(results),'candidate_CR':sorted(seen)}))
if __name__=='__main__':main()

