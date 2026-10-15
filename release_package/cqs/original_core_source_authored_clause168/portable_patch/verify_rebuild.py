"""Verify original168 CR cover cells and reconstruct their additive string field.

Standard library only; baseline read-only, no database service or model calls.
"""
import argparse,hashlib,json,re,shutil,sqlite3,zipfile
from pathlib import Path
from io import BytesIO
from xml.etree import ElementTree as ET
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
KEY='sourceAuthoredClausesAffected'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def read(p):return json.loads(Path(p).read_text())
def q(x):return '"'+x.replace('"','""')+'"'
def visible(p):
 return ''.join((x.text or '') if x.tag==W+'t' else '\t' if x.tag==W+'tab' else '\n' if x.tag in {W+'br',W+'cr'} else '' for x in p.iter())
def cell_text(c):return '\n'.join(visible(p) for p in c.iter(W+'p'))
def at(root,coordinate):
 parts=coordinate.split('/');assert parts.pop(0)=='document'
 for part in parts:
  m=re.fullmatch(r'([A-Za-z0-9]+)\[([1-9][0-9]*)\]',part);assert m,coordinate
  root=root.findall(W+m.group(1))[int(m.group(2))-1]
 return root
def verify_source(p,m):
 for f in m['files']:
  path=(p/f['path']).resolve();assert path.is_relative_to(p.resolve())
  assert path.stat().st_size==f['bytes'] and sha(path)==f['sha256'],f['path']
 rows=[json.loads(s) for s in (p/'source/all168_original_authored_clause_cell_observations.jsonl').read_text().splitlines()]
 mapping=read(p/'patch/existing_node_property_mapping168.json');by={r['tdocNumber']:r for r in mapping}
 transport={r['sha256']:r for r in read(p/'source/portable_original_ZIP_sources.json')}
 assert len(rows)==len(mapping)==len(transport)==168
 diagnostics={'raw_literal_equal':0,'raw_visible_difference':0,'paragraph_trim_equal':0,'paragraph_boundary_difference':0}
 for r in rows:
  assert not r['read_errors'] and len(r['authored_observations'])==1;o=r['authored_observations'][0]
  archive=p/transport[o['physical_ZIP_pin']['sha256']]['path'];assert sha(archive)==o['physical_ZIP_pin']['sha256'] and archive.stat().st_size==o['physical_ZIP_pin']['bytes']
  with zipfile.ZipFile(archive) as z:assert z.testzip() is None;member=z.read(o['member'])
  assert hashlib.sha256(member).hexdigest()==o['member_sha256']
  with zipfile.ZipFile(BytesIO(member)) as z:assert z.testzip() is None;xml=z.read('word/document.xml')
  assert hashlib.sha256(xml).hexdigest()==o['raw_document_XML_sha256'];root=ET.fromstring(xml)
  headers=o['formal_currentVersion_header_observations'];decls=o['all_exact_formal_clause_rows'];assert len(headers)==len(decls)==1
  h=headers[0];header=at(root,h['raw_XML_path']);assert hashlib.sha256(ET.tostring(header,encoding='us-ascii')).hexdigest()==h['raw_row_XML_sha256']
  cells=[cell_text(c) for c in header.findall(W+'tc')];assert cells==h['cells'] and len(cells)==9 and cells[2].strip()=='CR' and cells[4].strip()=='rev' and cells[6].strip()=='Current version:'
  assert int(cells[3].strip())==int(r['original_recorded_properties']['crNumber'])
  assert cells[1].strip() in {x['properties']['specNumber'] for x in r['original_MODIFIES_inputs']}
  rev=cells[5].strip();assert (int(rev)==int(r['original_recorded_properties']['crRevision'])) if rev not in {'','-'} else r['original_recorded_properties'].get('crRevision') is None
  d=decls[0];row=at(root,d['raw_XML_path']);assert hashlib.sha256(ET.tostring(row,encoding='us-ascii')).hexdigest()==d['raw_row_XML_sha256']
  cells=row.findall(W+'tc');assert cell_text(cells[d['label_cell0']]).strip()=='Clauses affected:' and len(d['following_cells'])==1
  e=d['following_cells'][0];cell=at(root,e['raw_XML_path']);assert cell is cells[d['label_cell0']+1]
  assert hashlib.sha256(ET.tostring(cell,encoding='us-ascii')).hexdigest()==e['raw_cell_XML_sha256']
  ps=list(cell.iter(W+'p'));assert len(ps)==len(e['paragraphs'])
  for a,b in zip(ps,e['paragraphs']):assert visible(a)==b['visible_text'] and hashlib.sha256(ET.tostring(a,encoding='us-ascii')).hexdigest()==b['raw_paragraph_XML_sha256']
  for tag in ['sym','drawing','object','instrText','del','delText','fldSimple']:assert not list(cell.iter(W+tag))
  assert not list(cell.iter(M+'oMath')) and not list(cell.iter(M+'oMathPara'))
  authored=cell_text(cell);assert authored==e['paragraph_joined_final_visible_text']==by[r['tdocNumber']][KEY]
  assert r['original_sourceIRI']==by[r['tdocNumber']]['sourceIRI']
  diagnostics['raw_literal_equal' if authored==r['original_recorded_properties']['clausesAffected'] else 'raw_visible_difference']+=1
  trimmed='\n'.join(visible(a).strip() for a in ps).strip();diagnostics['paragraph_trim_equal' if trimmed==r['original_recorded_properties']['clausesAffected'] else 'paragraph_boundary_difference']+=1
 assert diagnostics=={'raw_literal_equal':157,'raw_visible_difference':11,'paragraph_trim_equal':166,'paragraph_boundary_difference':2}
 return mapping,diagnostics
def rebuild(p,m,rows,base_sql,base_ttl,out):
 assert not out.exists() and sha(base_sql)==m['baseline']['SQLite']['sha256'] and sha(base_ttl)==m['baseline']['RDF']['sha256'];out.mkdir(parents=True)
 db=out/'RAN2.sqlite';rdf=out/'RAN2-source168-body.ttl';shutil.copy2(base_sql,db)
 c=sqlite3.connect(db.as_uri()+'?mode=rw',uri=True);c.row_factory=sqlite3.Row;c.execute('PRAGMA cache_size=-8192');c.execute('PRAGMA temp_store=FILE');c.execute('PRAGMA threads=1')
 tables=[r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")];columns={t:[r[1] for r in c.execute('PRAGMA table_info('+q(t)+')')] for t in tables};assert len(tables)==79
 assert c.execute('SELECT count(*) FROM node').fetchone()[0]==156288 and c.execute('SELECT count(*) FROM edge').fetchone()[0]==939037
 with c:
  for t in ['CR','Tdoc']:assert KEY not in columns[t];c.execute('ALTER TABLE '+q(t)+' ADD COLUMN '+q(KEY)+' ANY')
  for row in rows:
   nid,value=row['node_id'],row[KEY];stored=c.execute('SELECT * FROM _node_record WHERE node_id=?',(nid,)).fetchone();assert stored['source_iri']==row['sourceIRI']
   props=json.loads(stored['properties_json']);assert props['tdocNumber']==row['tdocNumber'] and KEY not in props;props[KEY]=value
   c.execute('UPDATE _node_record SET properties_json=? WHERE node_id=?',(canon(props),nid));c.execute('INSERT INTO node_property VALUES(?,?,?,?)',(nid,KEY,'string',canon(value)))
   for t in ['CR','Tdoc']:assert c.execute('UPDATE '+q(t)+' SET '+q(KEY)+'=? WHERE node_id=?',(value,nid)).rowcount==1
 c.execute('ATTACH DATABASE ? AS frozen',(base_sql.as_uri()+'?mode=ro&immutable=1',));preserved={}
 for t in tables:
  fields=','.join(map(q,columns[t]));old='SELECT '+fields+' FROM frozen.'+q(t);new='SELECT '+fields+' FROM main.'+q(t)
  if t=='_node_record':new="SELECT node_id,source_iri,labels_json,json_remove(properties_json,'$.sourceAuthoredClausesAffected') AS properties_json FROM main._node_record"
  elif t=='node_property':new+=" WHERE key<>'sourceAuthoredClausesAffected'"
  counts=[c.execute('SELECT count(*) FROM ('+a+' EXCEPT '+b+')').fetchone()[0] for a,b in [(old,new),(new,old)]]
  oldn=c.execute('SELECT count(*) FROM ('+old+')').fetchone()[0];newn=c.execute('SELECT count(*) FROM ('+new+')').fetchone()[0];assert counts==[0,0] and oldn==newn,t
  preserved[t]=dict(original_columns=columns[t],original_rows_n=oldn,normalized_new_rows_n=newn,two_way_EXCEPT_n=counts)
 assert c.execute('SELECT count(*) FROM node_property WHERE key=?',(KEY,)).fetchone()[0]==168
 for t in ['CR','Tdoc']:
  actual={r['node_id']:r[KEY] for r in c.execute('SELECT node_id,'+q(KEY)+' FROM '+q(t)+' WHERE '+q(KEY)+' IS NOT NULL')};assert actual=={r['node_id']:r[KEY] for r in rows}
 for r in rows:
  value=c.execute('SELECT native_type,value_json FROM node_property WHERE node_id=? AND key=?',(r['node_id'],KEY)).fetchone();assert value['native_type']=='string' and json.loads(value['value_json'])==r[KEY]
 assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok';c.close()
 with rdf.open('wb') as dst,base_ttl.open('rb') as src:shutil.copyfileobj(src,dst);dst.write(b'\n');dst.write((p/'patch/sourceAuthoredClausesAffected168_add.ttl').read_bytes())
 assert sha(rdf)==m['expected_rebuilt_RDF_sha256'] and sha(base_sql)==m['baseline']['SQLite']['sha256'] and sha(base_ttl)==m['baseline']['RDF']['sha256']
 result=dict(status='PASS_FRESH_ISOLATED_ADDITIVE168_REBUILD',original79_all_columns_bidirectional_EXCEPT=preserved,full168_string_fields_equal=True,new_nodes_n=0,new_edges_n=0,new_properties_n=168,SQL_sha256=sha(db),RDF_sha256=sha(rdf),baseline_unchanged=True,native_execution_n=0,model_API_calls_n=0)
 (out/'rebuild_receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--package',type=Path,required=True);a.add_argument('--base-sql',type=Path);a.add_argument('--base-ttl',type=Path);a.add_argument('--out-dir',type=Path);x=a.parse_args();p=x.package.resolve();m=read(p/'manifest.json');rows,diagnostic=verify_source(p,m);r=dict(status='PASS_ALL168_AUTHENTIC_RAW_COVER_CELLS',source_diagnostics=diagnostic,source_variant_only=True,remaining1996_unknown=True)
 if any([x.base_sql,x.base_ttl,x.out_dir]):assert all([x.base_sql,x.base_ttl,x.out_dir]);r['isolated_rebuild']=rebuild(p,m,rows,x.base_sql.resolve(),x.base_ttl.resolve(),x.out_dir.resolve())
 print(json.dumps(r,ensure_ascii=False))
