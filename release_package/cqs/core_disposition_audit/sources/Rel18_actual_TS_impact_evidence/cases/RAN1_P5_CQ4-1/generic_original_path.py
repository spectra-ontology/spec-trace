"""Generic finite directed-path MATCH/OPTIONAL MATCH and DISTINCT replay."""
import collections,gzip,hashlib,json,re
from pathlib import Path
IDENT=r'[A-Za-z_][A-Za-z0-9_]*'
NODE=re.compile(r'\(('+IDENT+r')(?::('+IDENT+r'))?(?:\s*\{('+IDENT+r"):\s*'([^']*)'\})?\)")
EDGE=re.compile(r'(<-|-)\[:('+IDENT+r')\](->|-)')
def parse_path(text):
 nodes=[];edges=[];offset=0
 while True:
  n=NODE.match(text,offset);assert n,'Node syntax outside generic directed-path grammar'
  var,label,key,val=n.groups();nodes.append({'variable':var,'label':label,'properties':{key:val} if key else {}});offset=n.end()
  if offset==len(text):break
  e=EDGE.match(text,offset);assert e,'Edge syntax outside generic directed-path grammar'
  left,kind,right=e.groups();assert (left,right) in {('-','->'),('<-','-')}
  edges.append({'type':kind,'forward':left=='-'});offset=e.end()
 assert len(nodes)==len(edges)+1
 return {'nodes':nodes,'edges':edges}
def parse_query(query):
 m=re.fullmatch(r'MATCH\s+(.+?)\s+OPTIONAL MATCH\s+(.+?)\s+RETURN\s+(DISTINCT\s+)?(.+?)\s+ORDER BY\s+('+IDENT+r'\.'+IDENT+r')',query);assert m,'Query outside exact generic MATCH/OPTIONAL path grammar'
 mandatory,optional,distinct,projs,order=m.groups()
 p=parse_path(mandatory);o=parse_path(optional);fields=[s.strip() for s in projs.split(',')]
 variables={n['variable'] for group in [p,o] for n in group['nodes']}
 assert len(fields)==len(set(fields)) and o['nodes'][0]['variable'] in {n['variable'] for n in p['nodes']}
 for f in fields+[order]:
  assert re.fullmatch(IDENT+r'\.'+IDENT,f) and f.split('.')[0] in variables
 return {'match':p,'optional_match':o,'distinct':bool(distinct),'projections':fields,'order_by':order}
def run(ast,graph):
 records={x['node_id']:{'labels':json.loads(x['labels_json']),'properties':json.loads(x['properties_json'])} for x in graph['records']}
 outgoing=collections.defaultdict(list);incoming=collections.defaultdict(list)
 for e in sorted(graph['edges'],key=lambda x:x['edge_id']):
  outgoing[(e['src_id'],e['rel_type'])].append(e['dst_id']);incoming[(e['dst_id'],e['rel_type'])].append(e['src_id'])
 def fits(n,nid):
  r=records[nid]
  return (n['label'] is None or n['label'] in r['labels']) and all(r['properties'].get(k)==v for k,v in n['properties'].items())
 def walk(path,row):
  n=path['nodes'][0];var=n['variable']
  seeds=[row[var]] if var in row else sorted(records)
  states=[dict(row,**{var:nid}) for nid in seeds if nid is not None and fits(n,nid)]
  for i,edge in enumerate(path['edges']):
   left=path['nodes'][i]['variable'];right=path['nodes'][i+1];v=right['variable'];nxt=[]
   for st in states:
    neighbors=(outgoing if edge['forward'] else incoming).get((st[left],edge['type']),[])
    for nid in neighbors:
     if v in st and st[v]!=nid:continue
     if fits(right,nid):nxt.append(dict(st,**{v:nid}))
   states=nxt
  return states
 states=walk(ast['match'],{})
 optional_vars={x['variable'] for x in ast['optional_match']['nodes']}
 expanded=[]
 for row in states:
  matches=walk(ast['optional_match'],row)
  expanded.extend(matches if matches else [dict(row,**{k:None for k in optional_vars if k not in row})])
 def val(row,f):
  v,k=f.split('.');nid=row[v];return None if nid is None else records[nid]['properties'].get(k)
 expanded.sort(key=lambda row:(val(row,ast['order_by']) is not None,val(row,ast['order_by']) or ''))
 out=[];seen=set()
 for row in expanded:
  vals=tuple(val(row,f) for f in ast['projections'])
  if ast['distinct'] and vals in seen:continue
  seen.add(vals);out.append(dict(zip(ast['projections'],vals)))
 return out
