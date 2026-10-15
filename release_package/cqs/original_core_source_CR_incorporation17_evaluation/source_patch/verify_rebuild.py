"""Spec: independently rebuild the documentary Source17 local source snapshot.
Ontology: new observations and documentary edges; preserve all frozen records.
Cycle: KDD2027 Datasets/Benchmarks Cycle1 separate-source CQ045 contract.
배경: approval, citation, TS history incorporation and causality are distinct.
사용: --package PATH [--base-sql DB --base-ttl TTL --out-dir NEWDIR].
LLM 호출: none; no Docker, model generation or public mutation.
"""
from pathlib import Path
import argparse,hashlib,json,sqlite3,shutil,zipfile,io
import xml.etree.ElementTree as E
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
S='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def canon(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def load(p):return json.loads(p.read_text())
def q(v):return '"'+v.replace('"','""')+'"'
def visible(p):return ''.join(t.text or '' for t in p.iter(W+'t'))
def verify_source(package,m):
 for f in m['files']:
  p=package/f['path'];assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256'],f['path']
 packet=load(package/'source/original_source_packet.json')
 inventory=load(package/'source/original_archive_inventory.json')
 paths={r['sha256']:package/r['portable_path'] for r in inventory}
 cache={}
 def member(archive,name,digest):
  p=paths[archive['sha256']];assert sha(p)==archive['sha256']
  key=(archive['sha256'],name)
  if key not in cache:
   with zipfile.ZipFile(p) as z:cache[key]=z.read(name)
  assert hashlib.sha256(cache[key]).hexdigest()==digest
  return cache[key]
 def doc(archive,name,digest,xmlsha):
  raw=member(archive,name,digest)
  with zipfile.ZipFile(io.BytesIO(raw)) as z:xml=z.read('word/document.xml')
  assert hashlib.sha256(xml).hexdigest()==xmlsha
  return E.fromstring(xml)
 pack=packet['original_source_whole_CR_pack'];pdocs={}
 for pm in pack['all18_original_members']:
  raw=member(pack['archive'],pm['member_name'],pm['member_sha256'])
  if pm['member_name'].lower().endswith(('.docx','.docm')):
   tree=doc(pack['archive'],pm['member_name'],pm['member_sha256'],pm['full_XML_sha256']);pdocs[pm['member_name']]=tree
   tables=list(tree.iter(W+'tbl'))
   for r in pm['all_cover_table_rows']:
    row=tables[r['table_zero_based']].findall(W+'tr')[r['row_zero_based']]
    actual=E.tostring(row,encoding='utf-8')
    assert actual.decode()==r['row_XML_utf8'] and hashlib.sha256(actual).hexdigest()==r['row_XML_sha256']
    assert ['\n'.join(visible(p) for p in c.findall(W+'p')) for c in row.findall(W+'tc')]==r['literal_cells']
 reg=packet['original_source_register'];wb=member(reg['archive'],reg['member'],reg['member_sha256'])
 with zipfile.ZipFile(io.BytesIO(wb)) as z:
  book=E.fromstring(z.read('xl/workbook.xml'));rels={r.attrib['Id']:r.attrib['Target'] for r in E.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
  rid=next(s.attrib[R+'id'] for s in book.find(S+'sheets') if s.attrib['name']=='CRs_RAN_97e')
  target=rels[rid];target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
  sheetxml=z.read(target);sheet=E.fromstring(sheetxml);srows={int(r.attrib['r']):r for r in sheet.find(S+'sheetData')}
 hist={}
 for h in packet['whole_three_TS_change_history_source']:
  tree=doc(h['archive'],h['member'],h['member_sha256'],h['full_XML_sha256'])
  hist[h['specNumber']]=(h,list(tree.iter(W+'tbl')))
 for key in ['original_source_TSG_final_approval_report','original_source_RAN1_final_agreement_report']:
  r=packet[key];tree=doc(r['archive'],r['member'],r['member_sha256'],r['full_XML_sha256']);ps=list(tree.iter(W+'p'))
  contexts=r.get('actual_CR_pack_approval_context',[])
  if key.endswith('agreement_report'):contexts=[p for a in r['actual_final_CR_agreement_contexts'] for p in a['context']]
  for p in contexts:
   xml=E.tostring(ps[p['paragraph_zero_based']],encoding='utf-8')
   assert xml.decode()==p['raw_XML_utf8'] and hashlib.sha256(xml).hexdigest()==p['raw_XML_sha256']
 mapping=load(package/'patch/source17_node_edge_mapping.json');assert len(mapping['new_nodes'])==17
 for r in mapping['new_nodes']:
  p=r['properties'];assert len(p)==42 and p['individualTSGStatus']=='approved' and p['CRBaseVersionLiteral']=='17.2.0' and p['normativeHistoryNewVersion']=='17.3.0'
  rx=E.tostring(srows[p['sourceRegisterRowOneBased']],encoding='utf-8')
  assert rx.decode()==p['sourceRegisterRowXML'] and hashlib.sha256(rx).hexdigest()==p['sourceRegisterRowXMLSha256']
  assert hashlib.sha256(sheetxml).hexdigest()==p['sourceRegisterSheetXMLSha256']
  h,tables=hist[p['specNumber']];row=tables[p['sourceHistoryTableZeroBased']].findall(W+'tr')[p['sourceHistoryRowZeroBased']]
  hx=E.tostring(row,encoding='utf-8')
  assert hx.decode()==p['sourceHistoryRowXML'] and hashlib.sha256(hx).hexdigest()==p['sourceHistoryRowXMLSha256']
  assert ['\n'.join(visible(p) for p in c.findall(W+'p')) for c in row.findall(W+'tc')]==json.loads(p['sourceHistoryLiteralCellsJSON'])
  assert len(r['relationships'])==2 and [e['rel_type'] for e in r['relationships']]==['HAS_SOURCE_INCORPORATION_OBSERVATION','DOCUMENTS_SPEC']
 return mapping,{'status':'PASS','original_archives_n':len(inventory),'whole_pack_original_members_n':18,'new_documentary_observations_n':17,'source_properties_per_observation':42,'documentary_edges_n':34,'legacy_DOC_exact_XML_identity_claimed':False}

def rebuild(package,m,mapping,base_sql,base_ttl,out):
 assert not out.exists(),'Refuse overwrite';out.mkdir()
 assert sha(base_sql)==m['baseline']['SQLite']['sha256'] and sha(base_ttl)==m['baseline']['RDF']['sha256']
 oldsqlstat=base_sql.stat().st_mtime_ns
 target=out/'RAN1.sqlite';shutil.copy2(base_sql,target)
 c=sqlite3.connect(target);c.execute('PRAGMA journal_mode=DELETE');c.execute('PRAGMA temp_store=FILE');c.execute('PRAGMA cache_size=-32768')
 c.execute('ATTACH DATABASE ? AS frozen',(str(base_sql),))
 oldtables=[r[0] for r in c.execute("SELECT name FROM frozen.sqlite_master WHERE type='table' ORDER BY name")];assert len(oldtables)==89
 max_n=c.execute('SELECT max(node_id) FROM node').fetchone()[0];max_e=c.execute('SELECT max(edge_id) FROM edge').fetchone()[0]
 cls='SourceCRNormativeIncorporationObservation';columns=sorted(mapping['new_nodes'][0]['properties'])
 with c:
  c.execute('CREATE TABLE '+q(cls)+'(node_id INTEGER PRIMARY KEY,'+','.join(q(k)+' ANY' for k in columns)+') STRICT')
  for rel in ['HAS_SOURCE_INCORPORATION_OBSERVATION','DOCUMENTS_SPEC']:
   c.execute('CREATE TABLE '+q('rel_'+rel)+'(edge_id INTEGER PRIMARY KEY,src_id INTEGER NOT NULL,dst_id INTEGER NOT NULL) STRICT')
  for r in mapping['new_nodes']:
   for a in [r['CR_anchor'],r['Spec_anchor']]:
    stored=c.execute('SELECT source_iri,labels_json,properties_json FROM _node_record WHERE node_id=?',(a['node_id'],)).fetchone()
    assert stored==(a['source_iri'],a['labels_json'],a['properties_json'])
   nid=r['node_id'];p=r['properties'];labs=canon(r['labels'])
   c.execute('INSERT INTO _node_record VALUES(?,?,?,?)',(nid,r['source_iri'],labs,canon(p)))
   c.execute('INSERT INTO node VALUES(?,?)',(nid,labs));c.execute('INSERT INTO node_label VALUES(?,?)',(nid,cls));c.execute('INSERT INTO node_identity VALUES(?,?)',(nid,r['loader_iri']))
   c.executemany('INSERT INTO node_property VALUES(?,?,?,?)',[(nid,k,'integer' if type(v)is int else 'string',canon(v)) for k,v in p.items()])
   c.execute('INSERT INTO '+q(cls)+' VALUES('+','.join('?' for _ in range(43))+')',[nid]+[p[k] for k in columns])
   for e in r['relationships']:
    c.execute('INSERT INTO edge VALUES(?,?,?,?)',(e['edge_id'],e['src_id'],e['rel_type'],e['dst_id']))
    c.execute('INSERT INTO '+q('rel_'+e['rel_type'])+' VALUES(?,?,?)',(e['edge_id'],e['src_id'],e['dst_id']))
  assert c.execute('SELECT count(*) FROM node').fetchone()[0]==165435 and c.execute('SELECT count(*) FROM edge').fetchone()[0]==848262
 preservation={}
 for t in oldtables:
  cols=[r[1] for r in c.execute('PRAGMA frozen.table_info('+q(t)+')')];p=','.join(q(x) for x in cols)
  limit=' WHERE node_id<='+str(max_n) if 'node_id' in cols else (' WHERE edge_id<='+str(max_e) if 'edge_id' in cols else '')
  missing=c.execute('SELECT count(*) FROM (SELECT '+p+' FROM frozen.'+q(t)+' EXCEPT SELECT '+p+' FROM main.'+q(t)+limit+')').fetchone()[0]
  extra=c.execute('SELECT count(*) FROM (SELECT '+p+' FROM main.'+q(t)+limit+' EXCEPT SELECT '+p+' FROM frozen.'+q(t)+')').fetchone()[0]
  assert missing==extra==0,t;preservation[t]={'missing_n':missing,'changed_n':extra}
 c.close()
 rdf=out/'RAN1-source17-body.ttl'
 with rdf.open('wb') as f,base_ttl.open('rb') as src:
  shutil.copyfileobj(src,f);f.write((package/'patch/source17_additions.ttl').read_bytes())
 assert sha(rdf)==m['expected_rebuilt_RDF_sha256']
 assert base_sql.stat().st_mtime_ns==oldsqlstat and sha(base_sql)==m['baseline']['SQLite']['sha256'] and sha(base_ttl)==m['baseline']['RDF']['sha256']
 receipt={'status':'PASS','new_nodes_n':17,'new_edges_n':34,'old_tables_preserved_n':89,'old_table_comparison':preservation,
    'nodes':165435,'relationships':848262,'rebuilt_SQL_sha256':sha(target),'rebuilt_RDF_sha256':sha(rdf),'baseline_bytes_unchanged':True,
    'model_calls_n':0,'native_calls_n':0,'question_or_model_performance_claims':False}
 (out/'actual_portable_rebuild_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');return receipt

def main():
 a=argparse.ArgumentParser();a.add_argument('--package',type=Path,required=True);a.add_argument('--base-sql',type=Path);a.add_argument('--base-ttl',type=Path);a.add_argument('--out-dir',type=Path);x=a.parse_args()
 m=load(x.package/'manifest.json');mapping,receipt=verify_source(x.package,m)
 if any([x.base_sql,x.base_ttl,x.out_dir]):
  assert all([x.base_sql,x.base_ttl,x.out_dir]);receipt['rebuild']=rebuild(x.package,m,mapping,x.base_sql,x.base_ttl,x.out_dir)
 print(canon(receipt),flush=True)
if __name__=='__main__':main()
