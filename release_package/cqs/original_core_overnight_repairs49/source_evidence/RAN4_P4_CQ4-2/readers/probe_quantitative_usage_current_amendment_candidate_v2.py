"""Whole frozen-domain quantitative-use candidate enumeration; no admission.

No fixed parameter/acronym/value/ID is part of the predicate. Existing Agenda
membership binds context, while actual own-act/amendment identity remains a
separate required source certificate. Another Agreement's approval is not used.
"""
from pathlib import Path
import json,re,sqlite3
from collections import defaultdict
import capture_actual_fifteen_reports_47_contexts_v1 as s
import probe_generic_current_amendment_rule_v3 as g
HERE=s.HERE
QUANTITY=re.compile(r'^\s*For\s+(.+?),\s*([-+]?\d+(?:\.\d+)?)\s*([A-Za-z%]+)\s+is\s+used[.;]?\s*$',re.I)
ACRONYM=re.compile(r'\b[A-Z][A-Z0-9-]+\b')
CHANGE=re.compile(r'\b(?:add(?:ed|ing|ition)?|correct(?:ed|ing|ions?)?|updat(?:e|ed|ing)|modif(?:y|ied|ying|ication)|chang(?:e|ed|ing)|remov(?:e|ed|ing|al))\b',re.I)
def candidate(a,c):
 out=[]
 for i,line in g.technical_lines(a):
  m=QUANTITY.match(g.norm(line))
  if not m:continue
  target,number,unit=m.groups();terms=ACRONYM.findall(target)
  if not terms:continue
  for fi,field in enumerate([c.get('reasonForChange')or'',c.get('summaryOfChange')or'']):
   for ci,clause in enumerate(field.splitlines()):
    if CHANGE.search(clause)and all(re.search(r'\b'+re.escape(term)+r'\b',clause,re.I)for term in terms):out.append({'source_line_index':i,'source_line':line,'parameter_topic':target,'quantity':number,'unit':unit,'topic_acronyms':terms,'CR_field':'reasonForChange'if fi==0 else'summaryOfChange','CR_clause_index':ci,'CR_clause':clause})
 return out
def main():
 c=sqlite3.connect((s.R/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/relational/RAN4.sqlite').as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row;c.execute('PRAGMA query_only=ON')
 aa=[dict(r)for r in c.execute('select a.*,m.dst_id meeting_id,b.dst_id agenda_id from Agreement a join rel_MADE_AT m on m.src_id=a.node_id join rel_RESOLUTION_BELONGS_TO b on b.src_id=a.node_id')]
 by=defaultdict(list)
 for r in c.execute('select c.*,m.dst_id meeting_id,b.dst_id agenda_id from CR c join rel_PRESENTED_AT m on m.src_id=c.node_id join rel_BELONGS_TO b on b.src_id=c.node_id where c.reasonForChange is not null'):by[r['meeting_id']].append(dict(r))
 records=[];quant=[]
 for a in aa:
  ll=[{'line_index':i,'line':l}for i,l in g.technical_lines(a)if QUANTITY.match(g.norm(l))]
  if ll:quant.append({'resolutionId':a['resolutionId'],'lines':ll})
  for cr in by[a['meeting_id']]:
   roles=candidate(a,cr)
   if roles:records.append({'Agreement':a,'CR':cr,'candidate_clause_bindings':roles,'source_role_admission':False})
 out={'status':'QUANTITATIVE_USAGE_CANDIDATES_ONLY_ORIGINAL_ROLE_CERTIFICATION_REQUIRED','script':s.pin(Path(__file__)),'source_Agreement_count':len(aa),'all_quantitative_usage_Agreements':quant,'all_candidate_paths':records,'distinct_CR':sorted({r['CR']['tdocNumber']for r in records}),'earlier_than_provisional_boundary':[{'resolutionId':r['Agreement']['resolutionId'],'tdocNumber':r['CR']['tdocNumber']}for r in records if r['CR']['tdocNumber']<='R4-2012300'],'interpretation':'The candidate predicate binds a quantitative-use technical clause to a captured current change on its subject acronym in the same event; Agenda membership is preserved as evidence, not made an extra condition. It does not establish exact quantity/change identity by itself; original own-current-amendment evidence certifies or refutes each frozen result. No CR body is added to runtime/model input.','native_API_public':0,'ROOT_seal':False}
 pin=s.save('diagnostic_quantitative_usage_current_amendment_candidate_v2.json',out);print(json.dumps({'output':pin,'quantity_Agreements':len(quant),'paths':len(records),'distinct':out['distinct_CR'],'prefix':out['earlier_than_provisional_boundary']}))
if __name__=='__main__':main()
