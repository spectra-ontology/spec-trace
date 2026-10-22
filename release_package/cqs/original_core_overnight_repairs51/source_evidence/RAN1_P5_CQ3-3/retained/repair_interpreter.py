"""Independent graph and immutable SQL interpreters for the source-certified repair."""
import json,re,sqlite3
from collections import defaultdict

def regex_select(value,family,allcodes,single):
 if single:return [value.strip()] if value.strip() else []
 keep=[];active=False
 for p in re.split(r'\n\s*\n|\n(?=In (?:sections?|clauses?)\b)',value,flags=re.I):
  p=p.strip()
  if not p:continue
  tokens=[z.strip() for z in re.split(',|\n',p) if z.strip()]
  if tokens and all(z in allcodes for z in tokens):active=family in tokens
  elif active or family.replace('-Core','').split('_')[-1].casefold() in p.casefold():keep.append(p)
 return keep

def literal_select(value,family,allcodes,single):
 value=value.strip()
 if single:return [value] if value else []
 for s in ['\nIn section','\nIn clause','\nIn Section','\nIn Clause']:value=value.replace(s,'\n'+s)
 parts=[p.strip() for p in value.split('\n\n') if p.strip()]
 output=[];bound=False
 for part in parts:
  header=[t.strip() for t in part.replace('\n',',').split(',') if t.strip()]
  if header and all(t in allcodes for t in header):bound=family in header
  elif bound or family[:-5].split('_')[-1].lower() in part.lower():output.append(part)
 return output

def sec_bound(section,pieces):
 return any(re.search(r'(?<![0-9.])'+re.escape(str(section))+r'(?![0-9.])',p) for p in pieces)

def graph_components(root):
 x=json.loads((root/'retained/frozen_graph_roles.json').read_text())
 rec={z['node_id']:{'labels':json.loads(z['labels_json']),**json.loads(z['properties_json'])} for z in x['records']}
 rel=x['relations'];outgoing={}
 for name,edges in rel.items():
  d=defaultdict(list)
  for e in edges:d[e['src_id']].append(e['dst_id'])
  outgoing[name]=d
 allcodes={r['workItemCode'] for r in rec.values() if 'WorkItem' in r['labels']}
 families={i:r for i,r in rec.items() if 'WorkItem' in r['labels']}
 trs={i:r for i,r in rec.items() if 'TechnicalReport' in r['labels'] and r.get('trNumber')=='38.824'}
 answer=[];types={};candidates=set()
 for ti,tr in trs.items():
  for impact in outgoing['rel_HAS_TR_IMPACT'][ti]:
   for sp in outgoing['rel_IMPACTS_SPEC'][impact]:types[rec[sp]['specNumber']]=rec[impact]['impactType']
  studycodes={rec[s]['workItemCode'] for s in outgoing['rel_RELATED_TO_WORK_ITEM'][ti]}
  for study in studycodes:
   if not study.startswith('FS_'):continue
   family=study[3:]+'-Core'
   wis={i for i,r in families.items() if r['workItemCode']==family}
   for ci,cr in rec.items():
    if 'CR' not in cr['labels']:continue
    crwis={rec[w]['workItemCode'] for w in outgoing['rel_RELATED_TO'].get(ci,[]) if w in families}
    if family not in crwis:continue
    for sp in outgoing['rel_MODIFIES'].get(ci,[]):
     target=rec[sp]['specNumber']
     if target not in ['38.211','38.214']:continue
     candidates.add(cr['id'])
     if cr.get('status')!='agreed':continue
     for field in ['reasonForChange','summaryOfChange']:
      pieces=regex_select(cr.get(field) or '',family,allcodes,len(crwis)==1)
      if not pieces:continue
      secs=sorted({rec[s]['sectionNumber'] for s in outgoing['rel_MODIFIES_SECTION'].get(ci,[]) if len(crwis)==1 or sec_bound(rec[s]['sectionNumber'],pieces)})
      answer.append({'specNumber':target,'CRid':cr['id'],'field':field,'sections':secs,'pieces':pieces})
 return sorted(answer,key=lambda r:(r['specNumber'],r['CRid'],r['field'])),types,len(candidates)

def sql_components(root):
 c=sqlite3.connect((root/'retained/frozen_dependency_projection.sqlite').resolve().as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row
 rows=list(c.execute((root/'retained/independent_role_fetch.sql').read_text()));crs={(r['node_id'],r['specNumber']):dict(r) for r in rows}
 codes={r[0] for r in c.execute('SELECT workItemCode FROM WorkItem')};components=[]
 for (ci,target),cr in crs.items():
  if cr['status']!='agreed':continue
  cw={r[0] for r in c.execute('SELECT w.workItemCode FROM rel_RELATED_TO e JOIN WorkItem w ON w.node_id=e.dst_id WHERE e.src_id=?',(ci,))}
  for field in ['reasonForChange','summaryOfChange']:
   pieces=literal_select(cr[field] or '',cr['workItemCode'],codes,len(cw)==1)
   if not pieces:continue
   secs=sorted({r[0] for r in c.execute('SELECT s.sectionNumber FROM rel_MODIFIES_SECTION e JOIN Section s ON s.node_id=e.dst_id WHERE e.src_id=?',(ci,)) if len(cw)==1 or sec_bound(r[0],pieces)})
   components.append({'specNumber':target,'CRid':cr['id'],'field':field,'sections':secs,'pieces':pieces})
 types={r[0]:r[1] for r in c.execute('SELECT sp.specNumber,ti.impactType FROM TechnicalReport tr JOIN rel_HAS_TR_IMPACT e ON e.src_id=tr.node_id JOIN TRImpact ti ON ti.node_id=e.dst_id JOIN rel_IMPACTS_SPEC m ON m.src_id=ti.node_id JOIN Spec sp ON sp.node_id=m.dst_id WHERE tr.trNumber=?',('38.824',))}
 c.close()
 return sorted(components,key=lambda r:(r['specNumber'],r['CRid'],r['field'])),types,len(crs)

def aggregate(components,types):
 rows=[]
 for spec in sorted({z['specNumber'] for z in components}):
  cs=[z for z in components if z['specNumber']==spec];sections=sorted({s for z in cs for s in z['sections']})
  desc='\n\n'.join(z['CRid'].split(':',1)[1]+' '+z['field']+': '+p for z in cs for p in z['pieces'])
  rows.append({'tr.trNumber':'38.824','sp.specNumber':spec,'ti.impactType':types[spec],'ti.affectedSection':', '.join(sections),'ti.impactDescription':desc})
 return rows

