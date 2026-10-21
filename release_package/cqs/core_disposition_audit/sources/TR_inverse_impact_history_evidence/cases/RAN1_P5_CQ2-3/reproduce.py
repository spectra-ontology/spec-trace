"""Replay original TR-impact evidence and all included SQL roles without external services."""
import collections,csv,gzip,hashlib,io,json,re,sqlite3,sys
from pathlib import Path
import xml.etree.ElementTree as ET
if sys.flags.optimize:raise SystemExit('Enabled checks required')
INVENTORY_SHA256='f56c922c1992c38e90975967bfd2df1d554fe5a25b48ab6a60a1a057dc708c94'
N={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};W='{'+N['w']+'}'
def digest(b):return hashlib.sha256(b).hexdigest()
def read(D,n):
 p=D/n
 if p.is_file():return json.loads(p.read_bytes())
 return json.loads(gzip.decompress((D/(n+'.gz')).read_bytes()))
def active_text(x):
 out=[]
 def visit(y):
  if y.tag in {W+'del',W+'moveFrom'}:return
  if y.tag==W+'t':out.append(y.text or '')
  for z in y:visit(z)
 visit(x);return ''.join(out)
def para(x,i):
 sty=x.find('w:pPr/w:pStyle',N)
 return {'index':i,'style':sty.get(W+'val') if sty is not None else None,'text':active_text(x),
  'insertions':len(x.findall('.//w:ins',N)),'deletions':len(x.findall('.//w:del',N)),
  'moves_from':len(x.findall('.//w:moveFrom',N))}
def parse_original_query(cypher):
 """Exact generic three-node path grammar, including either edge direction."""
 ident=r'[A-Za-z_][A-Za-z0-9_]*'
 node=r'\(('+ident+r'):('+ident+r')(?:\s*\{('+ident+r'):\s*\'([^\']*)\'\})?\)'
 edge=r'(<-|-)[\[]:('+ident+r')\](->|-)'
 m=re.fullmatch(r'MATCH\s+'+node+edge+node+edge+node+r'\s+RETURN\s+(.+?)\s+ORDER BY\s+('+ident+r'\.'+ident+r')',cypher)
 assert m,'Original query outside exact generic path grammar'
 g=m.groups();nodes=[]
 for offset in [0,7,14]:
  v,label,k,value=g[offset:offset+4];nodes.append({'variable':v,'label':label,'properties':{k:value} if k else {}})
 fields=[x.strip() for x in g[18].split(',')];order=g[19]
 aliases={x['variable']:x['label'] for x in nodes}
 assert len(aliases)==3 and len(fields)==len(set(fields))
 for f in fields+[order]:
  v,k=f.split('.');assert v in aliases and re.fullmatch(ident,k)
 relations=[];sql='SELECT '+','.join(f'{f} AS "{f}"' for f in fields)+' FROM "'+nodes[0]['label']+'" '+nodes[0]['variable']
 params=[]
 for i,offset in enumerate([4,11]):
  left,kind,right=g[offset:offset+3];assert (left,right) in {('-','->'),('<-','-')}
  av=nodes[i]['variable'];bv=nodes[i+1]['variable'];forward=left=='-'
  first,last=('src_id','dst_id') if forward else ('dst_id','src_id')
  src,dst=(av,bv) if forward else (bv,av)
  relations.append({'source':src,'type':kind,'target':dst})
  sql+=f' JOIN edge e{i} ON e{i}.{first}={av}.node_id AND e{i}.rel_type=? JOIN "{nodes[i+1]["label"]}" {bv} ON {bv}.node_id=e{i}.{last}'
  params.append(kind)
 where=[]
 for n in nodes:
  for k,v in n['properties'].items():where.append(n['variable']+'."'+k+'"=?');params.append(v)
 sql+=' WHERE '+' AND '.join(where)+' ORDER BY '+order
 return {'nodes':nodes,'relationships':relations,'projections':fields,'order_by':order},sql,params

def memory_graph(slice_data, original_schemas):
    c = sqlite3.connect(':memory:')
    c.row_factory = sqlite3.Row
    records = {}
    for r in slice_data['records']:
        assert r['node_id'] not in records
        records[r['node_id']] = {'labels': json.loads(r['labels_json']),
                                 'properties': json.loads(r['properties_json'])}
    schemas = {}
    for r in records.values():
        for label in r['labels']:
            assert re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', label)
            schemas.setdefault(label, set()).update(r['properties'])
    for label, columns in original_schemas.items():
        schemas.setdefault(label, set()).update(x['name'] for x in columns if x['name'] != 'node_id')
    for label, properties in schemas.items():
        names = sorted(properties)
        assert all(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', k) for k in names)
        columns = ','.join('"' + k + '"' for k in names)
        c.execute('CREATE TABLE "' + label + '"(node_id INTEGER PRIMARY KEY' + (',' + columns if columns else '') + ')')
        for nid, r in records.items():
            if label in r['labels']:
                vals = [r['properties'].get(k) for k in names]
                vals = [json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else x for x in vals]
                c.execute('INSERT INTO "' + label + '" VALUES(' + ','.join('?' for _ in range(1 + len(names))) + ')', [nid] + vals)
    c.execute('CREATE TABLE edge(edge_id INTEGER PRIMARY KEY,src_id INTEGER,rel_type TEXT,dst_id INTEGER)')
    for e in slice_data['edges']:
        assert e['src_id'] in records and e['dst_id'] in records
        c.execute('INSERT INTO edge VALUES(?,?,?,?)', [e[k] for k in ['edge_id', 'src_id', 'rel_type', 'dst_id']])
    for kind in {e['rel_type'] for e in slice_data['edges']}:
        assert re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', kind)
        c.execute('CREATE TABLE "rel_' + kind + '" AS SELECT edge_id,src_id,dst_id FROM edge WHERE rel_type=?', (kind,))
    c.execute('CREATE TABLE node(node_id INTEGER PRIMARY KEY,labels TEXT)')
    for nid,r in records.items():
        c.execute('INSERT INTO node VALUES(?,?)',(nid,json.dumps(r['labels'],separators=(',',':'))))
    return c, records


def semantic_checks(D):
 q=read(D,'contract/original_question_and_query.json');orig=read(D,'contract/original_benchmark_record.jsonl')
 assert orig==q['original_record']
 assert digest((D/'contract/original_benchmark_record.jsonl').read_bytes())==q['raw_record_sha256']
 assert digest(orig['question_en'].encode())==q['question_sha256']
 assert digest(orig['cypher'].encode())==q['query_sha256']
 criteria=read(D,'contract/criteria.json');assert digest((D/'contract/criteria.json').read_bytes())==q['criteria']['sha256']
 primary=read(D,'contract/primary_seven_unit_review.json')
 assert primary['id']==orig['id'] and primary['question_sha256']==q['question_sha256']
 assert primary['recommendation']=='unsupported_frozen_data' and primary['nonblind_AI'] is True and primary['expert_validation_n']==0
 assert [u['semantic_unit'] for u in primary['semantic_units']]==criteria['semantic_units']
 secondary=D/'contract/ROOT_secondary_review.json'
 if secondary.is_file():
  sec=read(D,'contract/ROOT_secondary_review.json')
  assert sec['id']==orig['id'] and sec.get('classification',sec.get('recommendation',sec.get('decision')))=='unsupported_frozen_data'
  assert [u.get('semantic_unit',u.get('unit')) for u in sec.get('semantic_units',sec.get('units',[]))]==criteria['semantic_units']
 sources=read(D,'source/direct_original_source_and_format.json');assert len(sources)==28
 bodies={};styles={};source_checks=0
 extra=read(D,'source/actual_source_CR2504980_and_named_role_receipt.json')
 for s in sources+[extra]:
  key=s['key'];xml=gzip.decompress((D/'source'/key/'document.xml.gz').read_bytes());sty=gzip.decompress((D/'source'/key/'styles.xml.gz').read_bytes())
  for raw,meta in [(xml,s['document_xml']),(sty,s['styles_xml'])]:assert len(raw)==meta['bytes'] and digest(raw)==meta['sha256']
  body=ET.fromstring(xml).find('w:body',N);bodies[key]=body;styles[key]=ET.fromstring(sty);ps=body.findall('w:p',N)
  if key=='CR2504980':
   tables=[{'body_child':i,'rows':[[active_text(tc) for tc in tr.findall('w:tc',N)] for tr in x.findall('w:tr',N)]} for i,x in enumerate(body) if x.tag==W+'tbl' and re.search(r'Work item code|Clauses affected|CHANGE REQUEST',active_text(x),re.I)]
   assert tables==s['cover_tables']
   assert tables[1]['rows'][6][1]=='NR_duplex_evo-Core' and tables[1]['rows'][8][1]=='B'
  else:
   assert len(body)==s['body_children'] and len(ps)==s['direct_body_paragraphs']
   paras=[para(x,i) for i,x in enumerate(ps)]
   assert [p for p in paras if p['style']=='Heading1']==s['all_heading1_paragraphs']
   for sec in s['scope_conclusions_and_summary_sections']:
    assert [paras[x['index']] for x in sec['direct_body_paragraphs']]==sec['direct_body_paragraphs']
   refs=[]
   for i,x in enumerate(body):
    t=active_text(x)
    if re.search(r'(?:TS\s*)?38[. ]211|avoid any changes to physical layer channels|no\s+(?:new\s+)?(?:physical\s+)?channels?\s+or\s+signals?',t,re.I):
     refs.append({'body_child':i,'tag':x.tag.removeprefix(W),'text':t,'preceding_text':active_text(body[i-1]) if i else '',
      'following_text':active_text(body[i+1]) if i+1<len(body) else '',
      'table_rows':[[active_text(tc) for tc in tr.findall('w:tc',N)] for tr in x.findall('w:tr',N)]})
   assert refs==s['all_target_TS_or_avoid_channel_reference_blocks']
   if key=='CR1913630':
    rows=[{'row':i,'cells':[active_text(tc) for tc in tr.findall('w:tc',N)]} for i,tr in enumerate(body[s['cover_table_body_child']].findall('w:tr',N))]
    assert rows==s['cover_rows'] and rows[6]['cells'][1]=='NR_unlic-Core' and rows[8]['cells'][1]=='B'
    for x in s['all_heading_or_inserted_4446_blocks']:assert {'body_child':x['body_child'],**para(body[x['body_child']],x['body_child'])}==x
  source_checks+=1
 role=read(D,'source/actual_original_style_and_scope_role_reopen.json');assert len(role)==26
 for s in role:
  key=s['key'];body=bodies[key];ps=body.findall('w:p',N);paras=[para(x,i) for i,x in enumerate(ps)]
  sm={x.get(W+'styleId'):x for x in styles[key] if x.tag==W+'style'}
  def outline(style,seen=()):
   if style not in sm or style in seen:return None
   el=sm[style];v=el.find('w:pPr/w:outlineLvl',N)
   if v is not None:return int(v.get(W+'val'))
   nm=el.find('w:name',N)
   if nm is not None and re.fullmatch(r'heading\s*1',nm.get(W+'val',''),re.I):return 0
   par=el.find('w:basedOn',N)
   return outline(par.get(W+'val'),seen+(style,)) if par is not None else None
  heads=[];sections=[]
  for i,p in enumerate(ps):
   row=paras[i];direct=p.find('w:pPr/w:outlineLvl',N);level=int(direct.get(W+'val')) if direct is not None else outline(row['style'])
   if level==0:heads.append(row)
   if re.fullmatch(r'\d+\s*(?:Scope|Conclusions?|Summary)(?:\s+and\s+recommendations)?\s*',row['text'],re.I):
    end=len(ps)
    for j in range(i+1,len(ps)):
     pr=ps[j];ol=pr.find('w:pPr/w:outlineLvl',N);lev=int(ol.get(W+'val')) if ol is not None else outline(paras[j]['style'])
     if lev==0 or re.match(r'Annex\s+[<A-Z]',paras[j]['text']):end=j;break
    sections.append({'heading':row,'heading_outline':level,'direct_body_paragraphs':paras[i:end]})
  assert heads==s['resolved_outline0_headings'] and sections==s['numeric_scope_and_conclusion_blocks']
 assert 'avoid any changes to physical layer channels and signals' in active_text(bodies['TR38742'][186])
 ts=[para(x,i) for i,x in enumerate(bodies['TS38211'].findall('w:p',N))]
 assert [int(re.match(r'^(\d+)',x['text']).group(1)) for x in ts if x['style']=='Heading1' and re.match(r'^\d+',x['text'])]==list(range(1,9))
 assert any(active_text(x).startswith('4.4.4.6') and x.findall('.//w:ins',N) for x in bodies['CR1913630'])
 slice_data=read(D,'frozen/compact_complete_own_role_slice.json');schemas=read(D,'frozen/original_SQL_table_schemas.json')
 c,records=memory_graph(slice_data,schemas)
 assert len([x for x in records.values() if 'TechnicalReport' in x['labels']])==26
 diagnostics=read(D,'frozen/actual_immutable_SQL_diagnostics.json');alternates=read(D,'frozen/actual_named_workitem_recovery_SQL.json')
 ast,sql,params=parse_original_query(orig['cypher']);generic=[dict(x) for x in c.execute(sql,params)]
 assert generic==diagnostics['original_projection']['rows'] and len(generic)==11
 checked=[]
 for group in [diagnostics,alternates]:
  for name,x in group.items():
   assert digest(x['sql'].encode())==x['sql_sha256']
   actual=[dict(r) for r in c.execute(x['sql'])]
   assert actual==x['rows'] and len(actual)==x['row_count'],name
   checked.append({'role':name,'rows':len(actual)})
 assert len(checked)==11
 assert all(r['cr_node'] is None for r in diagnostics['TR_workitem_CR_target_alternative']['rows'])
 assert next(x for x in diagnostics['all_original_TRs_and_all_impacts']['rows'] if x['trNumber']=='38.742')['conclusions'] is None
 assert len(alternates['all_WorkItem_identities']['rows'])==423 and len(alternates['full_prefix_candidate_CR_target_projection']['rows'])==595
 mapping=list(csv.DictReader(io.StringIO((D/'source/original_tr_impact_mapping.csv').read_text())))
 selected=sorted([x for x in mapping if x['impactsSpec']=='38.211'],key=lambda x:x['trNumber'])
 assert len(selected)==11
 assert [(r['tr.trNumber'],r['ti.impactType'],r['ti.affectedSection'],r['ti.impactDescription']) for r in generic]==[(r['trNumber'],r['impactType'],r['impactsSection'],r['impactDescription']) for r in selected]
 assert len({r['tr.trNumber'] for r in generic})==11
 assert collections.Counter(x['impactType'] for x in diagnostics['all_target_TS38211_impacts_and_sections']['rows'])=={'NewSection':6,'ExtendSection':5}
 c.close()
 return {'status':'PASS','id':orig['id'],'classification':'unsupported_frozen_data','source_XML_style_pairs':source_checks,
  'original_generic_AST':ast,'original_five_column_query_rows':len(generic),'original_SQL_role_checks':checked,
  'two_nonblind_AI_reviews':secondary.is_file(),'expert_validation_n':0,'new_admissions':0,'model_API_calls':0,'native_calls':0,
  'scope':'Original source and complete own-role diagnostics; no source-enriched answer oracle or causal completeness is invented.'}
def main():
 D=Path(__file__).resolve().parent;inventory=D/'immutable_inventory.json'
 assert digest(inventory.read_bytes())==INVENTORY_SHA256
 inv=read(D,'immutable_inventory.json')['files']
 observed={p.relative_to(D).as_posix() for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}}
 assert observed==set(inv)|{'immutable_inventory.json','manifest.json','reproduce.py'}
 for n,pin in inv.items():
  p=D/n;assert p.is_file() and not p.is_symlink();b=p.read_bytes();assert len(b)==pin['bytes'] and digest(b)==pin['sha256']
 manifest=read(D,'manifest.json');b=(D/'reproduce.py').read_bytes()
 assert manifest['verifier']['sha256']==digest(b) and manifest['verifier']['bytes']==len(b)
 print(json.dumps(semantic_checks(D),ensure_ascii=False))
if __name__=='__main__':main()
