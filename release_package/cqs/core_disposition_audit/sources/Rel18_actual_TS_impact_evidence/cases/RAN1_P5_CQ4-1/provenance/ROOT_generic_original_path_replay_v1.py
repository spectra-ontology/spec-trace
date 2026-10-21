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
if __name__=='__main__':
 d=Path(__file__).resolve().parent;f=d/'actual_original_sources_and_complete_frozen_v1';q=json.loads((f/'original_question_and_query.json').read_bytes())
 graph=json.loads(gzip.decompress((f/'complete_own_source_records_and_edges.json.gz').read_bytes()));diag=json.loads(gzip.decompress((f/'actual_original_eight_SQL_roles.json.gz').read_bytes()))
 ast=parse_query(q['original_record']['cypher']);assert ast['projections']==q['original_record']['gold_columns']
 rows=run(ast,graph);expected=[{field:x[field.split('.')[1]] for field in ast['projections']} for x in diag['original_projection']['rows']]
 assert rows==expected
 out=d/'actual_ROOT_generic_original_MATCH_OPTIONAL_replay_v1.json';assert not out.exists()
 value={'status':'PASS_GENERIC_ORIGINAL_MATCH_OPTIONAL_DISTINCT_REPLAY','id':q['original_record']['id'],'question_sha256':q['question_sha256'],'query_sha256':q['query_sha256'],'AST':ast,'actual_all_rows':rows,'row_count':len(rows),'same_as_independent_SQL_all_rows_and_fields':True,'source_labels_or_answer_whitelist_in_query_selection':False,'new_answer_oracle_created':False,'API_calls':0,'native_calls':0,'public_writes':0}
 out.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':value['status'],'rows':len(rows),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))

