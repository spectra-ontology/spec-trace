"""Prospective generic retained-input recognizer. Candidate, not final adjudication.

No IDs, meeting constants, domain parameter values, requested answer values or
minimum string length occur in the recognizer. The source-role matrix remains
independent of rule matches.
"""
import json,re,sqlite3
from pathlib import Path
from collections import defaultdict
import capture_actual_fifteen_reports_47_contexts_v1 as s
HERE=s.HERE
HEADER=re.compile(r'^\s*(R4-[0-9]{6,7})[\t ]+\S')
DECISION=re.compile(r'^\s*Decision\s*:',re.I)
POSITIVE=re.compile(r'^\s*Decision\s*:\s*(?:(?:the\s+)?document\s+(?:was\s+|is\s+)?)?(?:agreed|approved|endorsed|accepted)\b',re.I)
# A finite linguistic predicate marks a proposition, never a bare shared token.
ACTION=re.compile(r'\b(?:shall|must|should|will|(?:is|are|be)\s+(?:not\s+)?(?:allowed|required|defined|introduced|assumed|used|applied|configured|supported|increased|decreased|changed|set|agreed|approved|endorsed)|no\s+requirement|additional\s+delay\s+can\s+be\s+expected|not\s+required|do\s+not\s+define)\b',re.I)
CAUSE=re.compile(r'^\s*Interruptions\s+on\s+(.+?)\s+are\s+allowed\b.*?\bdue\s+to\s+(.+?)(?:\s+in\s+|[.;]|$)',re.I)
def norm(t):return ' '.join((t or'').split())
def semantic_norm(t):return norm((t or'').lower().replace('measurements','measurement').replace(' carrier based switching',' carrier switching'))
def retained_body(a):return (a.get('contentWithEquations')or a.get('content')or'')+'\n'+(a.get('note')or'')
def technical_lines(a):
 out=[];abstract=False
 for i,l in enumerate(retained_body(a).splitlines()):
  if DECISION.match(l):break
  if re.match(r'^\s*Abstract\s*:',l,re.I):abstract=True;continue
  if re.match(r'^\s*Discussion\s*:',l,re.I):abstract=False;continue
  if not abstract and l.strip():out.append((i,l))
 return out
def foreign_agreement_reference(c,meeting_int):
 # The explicit older source Agreement is retained rather than reattributed to
 # the current CR report's reused Agreement label. Direct own-CR branch is
 # independent and can still attest an actual current approval.
 ids=[int(v)for v in re.findall(r'\bagreement\s+in\s+RAN4\s*#\s*([0-9]+)',c.get('reasonForChange')or'',re.I)]
 return bool(ids)and all(n!=meeting_int for n in ids)
def operative_matches(a,c,meeting_int):
 if foreign_agreement_reference(c,meeting_int):return []
 fields=[norm(c.get(k))for k in ['reasonForChange','summaryOfChange']];sf=[semantic_norm(v)for v in fields];out=[]
 for i,l in technical_lines(a):
  n=norm(l)
  if ACTION.search(n)and any(n in v for v in fields):out.append({'branch':'exact_current_operative_proposition','line_index':i,'line':l})
  m=CAUSE.match(l)
  if m:
   target,cause=map(semantic_norm,m.groups())
   if target and cause and any(target in v and cause in v and re.search(r'\b(?:impact|impacted|interrupt|interrupted|interruption|delay|delayed)\b',v)for v in sf):out.append({'branch':'same_current_causal_measurement_amendment','line_index':i,'line':l,'target':target,'cause':cause})
 return out
def main():
 c=sqlite3.connect((s.R/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/relational/RAN4.sqlite').as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row;c.execute('PRAGMA query_only=ON')
 aa=[dict(r)for r in c.execute('select a.*,m.node_id as meeting_id,m.meetingNumberInt as meeting_int,ar.dst_id as agenda_id from Agreement a join rel_MADE_AT ma on ma.src_id=a.node_id join Meeting m on m.node_id=ma.dst_id join rel_RESOLUTION_BELONGS_TO ar on ar.src_id=a.node_id')]
 crs=defaultdict(list)
 for r in c.execute('select c.*,p.dst_id as meeting_id from CR c join rel_PRESENTED_AT p on p.src_id=c.node_id where c.reasonForChange is not null'):crs[r['meeting_id']].append(dict(r))
 resolutions={}
 for r in c.execute('select r.*,ar.dst_id as agenda_id from Agreement r join rel_RESOLUTION_BELONGS_TO ar on ar.src_id=r.node_id'):resolutions[(r['agenda_id'],r['sequence'])]=dict(r)
 bytd={r['tdocNumber']:r for rows in crs.values()for r in rows};results=[]
 for a in aa:
  for cr in crs[a['meeting_id']]:
   roles=operative_matches(a,cr,a['meeting_int'])
   if roles:results.append({'resolutionId':a['resolutionId'],'tdocNumber':cr['tdocNumber'],'roles':roles,'CR':cr})
  prev=resolutions.get((a['agenda_id'],a['sequence']-1))
  if prev:
   lines=retained_body(prev).splitlines();hh=[(i,HEADER.match(l))for i,l in enumerate(lines)if HEADER.match(l)]
   if hh:
    hi,h=hh[-1];tail=lines[hi+1:];cr=bytd.get(h.group(1));cur=retained_body(a).splitlines();ds=[(i,l)for i,l in enumerate(cur)if DECISION.match(l)]
    if cr and cr['meeting_id']==a['meeting_id']and not any(DECISION.match(l)for l in tail)and ds:
     di,dl=ds[0]
     if POSITIVE.match(dl)and not any(HEADER.match(l)for l in cur[:di]):results.append({'resolutionId':a['resolutionId'],'tdocNumber':cr['tdocNumber'],'roles':[{'branch':'preceding_open_own_CR_current_positive_decision','previous_resolutionId':prev['resolutionId'],'header':lines[hi],'current_decision':dl}],'CR':cr})
 # Order determines selected membership only; output serialization is a set.
 seen={r['tdocNumber']:r['CR']for r in results};ordered=sorted(seen)
 out={'status':'GENERIC_PROSPECTIVE_RULE_CANDIDATE_SOURCE_ADJUDICATION_PENDING','recognizer':s.pin(Path(__file__)),'input_Agreement':len(aa),'input_reason_nonnull_CRs':len(bytd),'all_matched_paths':results,'all_distinct_candidate_CR':ordered,'candidate_selected_max5':[{k:seen[t][col]for k,col in [('tdocNumber','tdocNumber'),('reason','reasonForChange'),('summary','summaryOfChange')]}for t in ordered[:5]],'scope':'Whole retained input execution candidate; independent source matrix certifies only the first selection dependency frontier, never a global approval classifier. Named conditional97 inputs and later98 positive source cases remain archived separately, outside current first5 dependency frontier.','API_native_public_mutations':0,'ROOT_seal':False}
 pin=s.save('actual_generic_current_amendment_candidate_rule_v3.json',out);print(json.dumps({'output':pin,'paths':len(results),'all_distinct':ordered,'selected':ordered[:5]}))
if __name__=='__main__':main()
