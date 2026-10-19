"""Additive RAN4#93 source snapshot. No native/API/public or frozen writes."""
import argparse, collections, difflib, hashlib, importlib.util, json, shutil, sqlite3, sys
from pathlib import Path
sys.dont_write_bytecode = True
BASE_N = 342161
BASE_E = 1592845
FAMILY = {'CR','draftCR','pCR'}
ACCEPTED = {'agreed','approved','endorsed'}
SOURCE_SQL = """WITH selected AS (
 SELECT node_id, tdocNumber
 FROM SourceMeetingDocument
 WHERE meetingNumberInt=93 AND sourceType IN ('CR','draftCR','pCR')
   AND finalDocumentaryStatus IN ('agreed','approved','endorsed')
 ORDER BY tdocNumber ASC
 LIMIT 10
)
SELECT s.sourceSummary AS summary
FROM selected d
LEFT JOIN rel_SOURCE_HAS_OWN_SUMMARY h ON h.src_id=d.node_id
LEFT JOIN SourceOwnCRSummary s ON s.node_id=h.dst_id"""
SOURCE_CYPHER = """MATCH (d:SourceMeetingDocument)
WHERE d.meetingNumberInt = 93
  AND d.sourceType IN ['CR','draftCR','pCR']
  AND d.finalDocumentaryStatus IN ['agreed','approved','endorsed']
WITH d ORDER BY d.tdocNumber ASC LIMIT 10
OPTIONAL MATCH (d)-[:SOURCE_HAS_OWN_SUMMARY]->(s:SourceOwnCRSummary)
RETURN s.sourceSummary AS summary"""
ORIGINAL_EN = "List the change summaries of CRs approved at meeting #93 (meeting-scoped change review)."
ORIGINAL_QUERY = "MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {meetingNumberInt: 93}) WITH a MATCH (a)-[:REFERENCES]->(t:Tdoc) WHERE t.summaryOfChange IS NOT NULL RETURN t.tdocNumber AS tdocNumber, t.summaryOfChange AS summary ORDER BY t.tdocNumber DESC LIMIT 10"

def canonical(v):
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()

def pin(p, path=None):
    p=Path(p)
    return {'path':str(path if path is not None else p),'bytes':p.stat().st_size,'sha256':sha(p)}

def write_json(p,v):
    Path(p).write_text(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')

def write_rows(p,rows):
    with Path(p).open('w',encoding='utf-8') as f:
        for r in rows:f.write(canonical(r)+'\n')

def rows(p):
    with Path(p).open(encoding='utf-8') as f:return [json.loads(l) for l in f if l.strip()]

def quote(s):
    return '"'+s.replace('"','""')+'"'

def check_pin(p,rec):
    assert Path(p).is_file() and Path(p).stat().st_size==rec['bytes'] and sha(p)==rec['sha256'],str(p)

def source_iri(label, key):
    return 'https://w3id.org/spectra/inst/RAN4/'+label+'/'+key

def native_type(value):
    return {type(None):'null',bool:'boolean',int:'integer',float:'number',str:'string',list:'array',dict:'object'}[type(value)]

def encoded(value):
    if type(value) in (list,dict):return canonical(value)
    if type(value) is bool:return int(value)
    return value

def observation_provenance(o):
    # Identical field policy for the whole1858; prefix-only verification detail is excluded.
    fields=[]
    for f in o.get('source_fields',[]):
        fields.append({k:f.get(k) for k in [
            'member','access','derivative','word_document_XML_sha256','styles_XML_sha256',
            'cover_first30_ownID_present','cover_first30_R4_tokens','field_status','summary',
            'summary_rows','native_CFB_summary_literal_whitespace_fold_match']})
    return {
        'archive':o.get('archive'),'archive_exists':o['archive_exists'],'members':o.get('members',[]),
        'generic_summary_status':o['generic_summary_status'],'source_fields':fields,
        'rule_version':'EXPLICIT_OWN_CR_FORM_SUMMARY_V1',
        'certification_limit':'Generic extraction observation. All1343 are not individually certified; full inherited-style and original CFB strikethrough remain unproved.',
    }

def make_graph(register, observations, roles, anchors, meeting_provenance):
    assert len(register)==3112 and len(observations)==1858 and len(roles)==1858
    assert len({r['tdocNumber'] for r in register})==3112
    obs={r['tdocNumber']:r for r in observations}; role={r['tdocNumber']:r for r in roles}
    reg={r['tdocNumber']:r for r in register}
    assert set(obs)==set(role)=={k for k,r in reg.items() if r['properties']['Type'] in FAMILY}
    nodes=[];edges=[]
    def add_node(label,key,props):
        nid=BASE_N+len(nodes)+1;iri=source_iri(label,key)
        node={'node_id':nid,'source_iri':iri,'loader_iri':iri.replace('/inst/RAN4/','/inst/_/',1),
              'labels':[label],'properties':props}
        nodes.append(node);return node
    def add_edge(src,rel,dst):
        e={'edge_id':BASE_E+len(edges)+1,'src_id':src['node_id'],'rel_type':rel,'dst_id':dst['node_id'],
           'source_iri':src['source_iri'],'target_iri':dst['source_iri']}
        edges.append(e)
    meeting=add_node('SourceMeetingRecord','RAN4-93',{
        'workingGroup':'RAN4','meetingNumberInt':93,
        'recordType':'approved WG documentary meeting-outcome record',
        'sourceProvenanceJSON':canonical({k:meeting_provenance[k] for k in ['approved_report_identity','whole_original93_register']}),
        'scopeCaveat':'Final documented WG outcomes; no physical-week timing, TSG approval, or normative incorporation claim.',
    })
    anchors={r['tdocNumber']:r for r in anchors}
    for t in sorted(reg):
        r=reg[t];p=r['properties'];o=obs.get(t)
        props={
          'workingGroup':'RAN4','meetingNumberInt':93,'tdocNumber':t,
          'sourceType':p['Type'],'sourceCRFamily':p['Type'] in FAMILY,
          'finalDocumentaryStatus':p['TDoc Status'],'sourceTitle':p['Title'],
          'sourceRevisionOf':p['Is revision of'],'sourceRevisedTo':p['Revised to'],
          'sourceCRNumber':p['CR'],'sourceCRRevision':p['CR revision'],
          'sourceSpec':p['Spec'],'sourceVersion':p['Version'],'sourceRelease':p['Release'],
          'sourceRegisterExcelRow':r['excel_row'],'sourceRegisterXMLRowHash':r['ET_UTF8_row_sha256'],
          'sourceRegisterPropertiesJSON':canonical(p),
          'sourceRegisterMemberHash':meeting_provenance['whole_original93_register']['embedded_XLSX_sha256'],
          'sourceSummaryExtractionStatus':o['generic_summary_status'] if o else 'OUTSIDE_DOCUMENTARY_CR_FAMILY',
          'sourceArchiveAccessStatus':('PRESENT' if o['archive_exists'] else 'MISSING') if o else 'NOT_PROBED_OUTSIDE_CR_FAMILY',
        }
        if o:
            assert o['original_type']==p['Type'] and o['original_final_status']==p['TDoc Status']
            assert o['original_revised_to']==p['Revised to'] and o['original_register_row']==r['excel_row']
            props['sourceOwnFieldProvenanceJSON']=canonical(observation_provenance(o))
            props['sourceReportDecisionBoundaryJSON']=canonical(role[t])
        d=add_node('SourceMeetingDocument','93-'+t,props)
        add_edge(d,'SOURCE_RECORDED_AT',meeting)
        a=anchors.get(t)
        if a and len(a['matches'])==1:
            old=a['matches'][0]
            add_edge(d,'SOURCE_REGISTER_ID_MATCH',old)
        if o and o['generic_summary_status']=='UNIQUE_EXPLICIT_OWN_CR_FORM_SUMMARY':
            value=o['source_summary'];assert isinstance(value,str) and value
            s=add_node('SourceOwnCRSummary','93-'+t,{
               'workingGroup':'RAN4','meetingNumberInt':93,'tdocNumber':t,'sourceSummary':value,
               'extractionStatus':o['generic_summary_status'],
               'sourceOwnFieldProvenanceJSON':canonical(observation_provenance(o)),
               'sourceCertifiedForWholePopulation':False,
               'formatCaveat':'No whole1343 inherited-style certification. Exact-member DOC conversion is distinguished from original DOCX; original CFB strikethrough is not decoded.',
            })
            add_edge(d,'SOURCE_HAS_OWN_SUMMARY',s)
    assert collections.Counter(n['labels'][0] for n in nodes)=={
        'SourceMeetingRecord':1,'SourceMeetingDocument':3112,'SourceOwnCRSummary':1343}
    assert all(n['node_id']>BASE_N for n in nodes)
    return {'nodes':nodes,'edges':edges}

def camel(rel):
    p=rel.split('_')
    return p[0].lower()+''.join(x[:1].upper()+x[1:].lower() for x in p[1:])

def literal(value):
    if type(value) is bool:return str(value).lower()
    if type(value) is int:return str(value)
    if type(value) is float:raise ValueError('Floating-point source values not expected')
    assert isinstance(value,str)
    return json.dumps(value,ensure_ascii=False)

def ttl_bytes(mapping):
    by_src=collections.defaultdict(list)
    for e in mapping['edges']:by_src[e['src_id']].append(e)
    lines=['\n@prefix spectra: <https://w3id.org/spectra#> .',
           '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .','']
    for n in mapping['nodes']:
        parts=['a spectra:'+n['labels'][0]]
        parts += ['spectra:'+k+' '+literal(v) for k,v in sorted(n['properties'].items())]
        parts += ['spectra:'+camel(e['rel_type'])+' <'+e['target_iri']+'>' for e in by_src[n['node_id']]]
        lines.append('<'+n['source_iri']+'> '+(' ;\n  '.join(parts))+' .\n')
    return ('\n'.join(lines)+'\n').encode('utf-8')

def create_new_tables(db,mapping):
    labels=sorted({n['labels'][0] for n in mapping['nodes']})
    for label in labels:
        assert not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(label,)).fetchone(),label
        keys=sorted({k for n in mapping['nodes'] if label in n['labels'] for k in n['properties']})
        db.execute('CREATE TABLE '+quote(label)+'(node_id INTEGER PRIMARY KEY,'+
                   ','.join(quote(k)+' ANY' for k in keys)+') STRICT')
    rels=sorted({e['rel_type'] for e in mapping['edges']})
    for r in rels:
        assert not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",('rel_'+r,)).fetchone()
        db.execute('CREATE TABLE '+quote('rel_'+r)+'(edge_id INTEGER PRIMARY KEY,src_id INTEGER NOT NULL,dst_id INTEGER NOT NULL) STRICT')

def insert_new_records(db,mapping,include_generic=True):
    for n in mapping['nodes']:
        nid,p=n['node_id'],n['properties']
        if include_generic:
            labs=canonical(n['labels'])
            db.execute('INSERT INTO _node_record VALUES(?,?,?,?)',(nid,n['source_iri'],labs,canonical(p)))
            db.execute('INSERT INTO node VALUES(?,?)',(nid,labs))
            db.execute('INSERT INTO node_identity VALUES(?,?)',(nid,n['loader_iri']))
            db.executemany('INSERT INTO node_label VALUES(?,?)',[(nid,k) for k in n['labels']])
            db.executemany('INSERT INTO node_property VALUES(?,?,?,?)',
                           [(nid,k,native_type(v),canonical(v)) for k,v in p.items()])
        for label in n['labels']:
            columns=[r[1] for r in db.execute('PRAGMA table_info('+quote(label)+')')]
            db.execute('INSERT INTO '+quote(label)+' VALUES('+','.join('?' for _ in columns)+')',
                       [nid if k=='node_id' else encoded(p.get(k)) for k in columns])
    for e in mapping['edges']:
        if include_generic:
            db.execute('INSERT INTO edge VALUES(?,?,?,?)',(e['edge_id'],e['src_id'],e['rel_type'],e['dst_id']))
        db.execute('INSERT INTO '+quote('rel_'+e['rel_type'])+' VALUES(?,?,?)',(e['edge_id'],e['src_id'],e['dst_id']))

def verify_package(package,loader=None):
    package=Path(package);m=json.loads((package/'manifest.json').read_text())
    for rec in m['files']:check_pin(package/rec['path'],rec)
    register=rows(package/'source/all3112_register.jsonl')
    observations=rows(package/'source/all1858_observations.jsonl')
    roles=rows(package/'source/all1858_report_decision_boundaries.jsonl')
    anchors=rows(package/'source/exact_frozen_ID_anchors.jsonl')
    authority=json.loads((package/'source/approved_report_authority_receipt.json').read_text())
    mapping=json.loads((package/'patch/additive_node_edge_mapping.json').read_text())
    regenerated=make_graph(register,observations,roles,anchors,authority)
    assert regenerated==mapping
    assert ttl_bytes(mapping)==(package/'patch/additive_source_records.ttl').read_bytes()
    assert (package/'query/original_English.txt').read_bytes()==ORIGINAL_EN.encode()
    assert (package/'query/original_query.cypher').read_bytes()==ORIGINAL_QUERY.encode()
    assert hashlib.sha256(ORIGINAL_QUERY.encode()).hexdigest()=='4bd3f2e20f49f49c8a41be53fe72744bb4e76d47a1445e0200138ffe41836023'
    assert hashlib.sha256(ORIGINAL_EN.encode()).hexdigest()=='a546f9a18c4636bde0fb1bf14376701620ce1cb0567fd914be90b2bfaa98a513'
    assert (package/'query/separate_source_query.cypher').read_text()==SOURCE_CYPHER
    assert (package/'query/separate_source_query.sql').read_text()==SOURCE_SQL
    # Separate tiny in-memory projection only; this never opens a native graph.
    db=sqlite3.connect(':memory:');create_new_tables(db,mapping);insert_new_records(db,mapping,False)
    actual=db.execute(SOURCE_SQL).fetchall()
    eligible=sorted([r for r in register if r['properties']['Type'] in FAMILY
                     and r['properties']['TDoc Status'] in ACCEPTED],key=lambda r:r['tdocNumber'])
    selected=eligible[:10];o={r['tdocNumber']:r for r in observations}
    expected=[(o[r['tdocNumber']]['source_summary'],) for r in selected]
    assert collections.Counter(actual)==collections.Counter(expected) and len(actual)==10
    assert len({r[0] for r in actual})==6
    # A missing selected summary must stay as a NULL occurrence; never pull row11.
    missing_id=selected[0]['tdocNumber']
    with db:
        db.execute('DELETE FROM SourceOwnCRSummary WHERE tdocNumber=?',(missing_id,))
    missing=db.execute(SOURCE_SQL).fetchall()
    assert len(missing)==10 and sum(v is None for (v,) in missing)==1
    assert collections.Counter(missing)==collections.Counter([(None,)]+expected[1:])
    # A duplicate occurrence is substantive; set collapse must fail count10.
    assert len(set(expected))!=len(expected)
    # Source-only generic role population includes unsupported and inactive records.
    family=[r for r in register if r['properties']['Type'] in FAMILY]
    counts=collections.Counter(r['generic_summary_status'] for r in observations)
    assert counts=={'UNIQUE_EXPLICIT_OWN_CR_FORM_SUMMARY':1343,'NO_SUPPORTED_UNIQUE_SUMMARY':515}
    assert sum(not r['archive_exists'] for r in observations)==132
    tdoc_nodes={n['properties']['tdocNumber']:n for n in mapping['nodes'] if n['labels']==['SourceMeetingDocument']}
    assert len(tdoc_nodes)==3112 and all(tdoc_nodes[r['tdocNumber']]['properties']['sourceSummaryExtractionStatus']==r['generic_summary_status'] for r in observations)
    assert all(not any(k.startswith('selected') or k.startswith('cutoff') or k.startswith('answer') for k in n['properties']) for n in mapping['nodes'])
    result={'status':'PASS_PORTABLE_ADDITIVE_PATCH_AND_IN_MEMORY_SOURCE_PROJECTION_ONLY',
      'new_node_counts':dict(collections.Counter(n['labels'][0] for n in mapping['nodes'])),
      'new_relationship_counts':dict(collections.Counter(e['rel_type'] for e in mapping['edges'])),
      'source_register_records':3112,'source_CR_family_records':len(family),'summary_observations':1343,
      'unsupported_unique_summary':515,'missing_archive':132,
      'eligible_population':len(eligible),'selected_occurrences':10,'distinct_summary_strings':6,
      'no_nonnull_skip_control':'PASS_DELETE_ONE_SELECTED_SUMMARY_STILL10_WITH_NULL',
      'multiset_multiplicity_control':'PASS_SET_COLLAPSE_LOSES4_OCCURRENCES',
      'selected_source_document_IDs':[r['tdocNumber'] for r in selected],
      'materialized_full_snapshot':False,'native_executions':0,'API_calls':0,
      'original560_pass_increment':0,'whole1343_source_certified':False}
    if loader:
        # Shipped parser roundtrip, not a new parser of our own.
        spec=importlib.util.spec_from_file_location('shipped_source_parser',loader)
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        nodes,rels,stats=mod.parse_ttl(package/'patch/additive_source_records.ttl')
        assert {k:{'labels':sorted(v['labels']),'props':v['props']} for k,v in nodes.items()}=={
          n['source_iri']:{'labels':n['labels'],'props':n['properties']} for n in mapping['nodes']}
        assert rels=={(e['source_iri'],e['rel_type'],e['target_iri']) for e in mapping['edges']}
        assert not stats['prop_conflicts'] and not stats['skipped_subjects']
        result['shipped_TTL_parser_roundtrip']='PASS_ALL_NEW_NODES_PROPERTIES_RELATIONSHIPS_EXACT'
    return result

def materialize(package,base_sql,base_rdf,output,preflight_only=False):
    package=Path(package);base_sql=Path(base_sql);base_rdf=Path(base_rdf)
    result=verify_package(package,package/'pipeline/load_released_kg.py')
    m=json.loads((package/'manifest.json').read_text())
    check_pin(base_sql,m['baseline']['SQLite']);check_pin(base_rdf,m['baseline']['RDF'])
    ro=sqlite3.connect('file:'+str(base_sql.resolve())+'?mode=ro&immutable=1',uri=True)
    old_tables=[r[0] for r in ro.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    old_columns={t:[r[1] for r in ro.execute('PRAGMA table_info('+quote(t)+')')] for t in old_tables}
    assert len(old_tables)==80 and ro.execute('SELECT max(node_id) FROM node').fetchone()[0]==BASE_N
    assert ro.execute('SELECT max(edge_id) FROM edge').fetchone()[0]==BASE_E
    for rec in rows(package/'source/exact_frozen_ID_anchors.jsonl'):
        actual=[dict(zip(['node_id','source_iri','labels_json','properties_json','iri'],r)) for r in ro.execute(
          'SELECT r.node_id,r.source_iri,r.labels_json,r.properties_json,i.iri FROM Tdoc t JOIN _node_record r USING(node_id) JOIN node_identity i USING(node_id) WHERE t.tdocNumber=? ORDER BY r.node_id',(rec['tdocNumber'],))]
        assert actual==rec['matches'],rec['tdocNumber']
    ro.close()
    result['baseline_80_tables_and_3112_exact_ID_anchor_replay']='PASS'
    if preflight_only:
        result['status']='PASS_PREFLIGHT_ONLY_NO_FULL_SNAPSHOT_CREATED'
        return result
    output=Path(output)
    assert not output.exists(),'Refuse overwrite; select a new isolated output directory'
    assert output.resolve()!=base_sql.resolve() and output.resolve()!=base_rdf.resolve()
    output.mkdir(parents=True)
    sql_out=output/'RAN4-source93.sqlite';rdf_out=output/'RAN4-source93-body.ttl'
    shutil.copy2(base_sql,sql_out)
    db=sqlite3.connect(sql_out);mapping=json.loads((package/'patch/additive_node_edge_mapping.json').read_text())
    with db:
        create_new_tables(db,mapping);insert_new_records(db,mapping)
    db.execute('ATTACH DATABASE ? AS frozen',(base_sql.resolve().as_uri()+'?mode=ro&immutable=1',))
    preserved={}
    for t in old_tables:
        cols=old_columns[t];fieldlist=','.join(quote(k) for k in cols)
        restriction=' WHERE node_id<='+str(BASE_N) if 'node_id' in cols else (' WHERE edge_id<='+str(BASE_E) if 'edge_id' in cols else '')
        old='SELECT '+fieldlist+' FROM frozen.'+quote(t)
        new='SELECT '+fieldlist+' FROM main.'+quote(t)+restriction
        minus=db.execute('SELECT count(*) FROM ('+old+' EXCEPT '+new+')').fetchone()[0]
        plus=db.execute('SELECT count(*) FROM ('+new+' EXCEPT '+old+')').fetchone()[0]
        oldn=db.execute('SELECT count(*) FROM frozen.'+quote(t)).fetchone()[0]
        newn=db.execute('SELECT count(*) FROM main.'+quote(t)+restriction).fetchone()[0]
        assert minus==plus==0 and oldn==newn,t
        preserved[t]={'old_rows':oldn,'missing_or_changed':minus,'unexpected_old_population':plus}
        # No old table schema or pre-existing columns are edited.
        assert list(db.execute('PRAGMA main.table_info('+quote(t)+')'))==list(db.execute('PRAGMA frozen.table_info('+quote(t)+')')),t
    assert db.execute('SELECT count(*) FROM node').fetchone()[0]==BASE_N+len(mapping['nodes'])
    assert db.execute('SELECT count(*) FROM edge').fetchone()[0]==BASE_E+len(mapping['edges'])
    actual=[dict(zip(['summary'],r)) for r in db.execute(SOURCE_SQL)]
    assert len(actual)==10 and len({canonical(r) for r in actual})==6
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    db.close()
    with rdf_out.open('wb') as dst,base_rdf.open('rb') as src:
        shutil.copyfileobj(src,dst)
        with (package/'patch/additive_source_records.ttl').open('rb') as delta:shutil.copyfileobj(delta,dst)
    # The original RDF is an exact byte prefix, not reserialized.
    h=hashlib.sha256()
    with rdf_out.open('rb') as f:
        remain=base_rdf.stat().st_size
        while remain:
            b=f.read(min(1048576,remain));assert b;h.update(b);remain-=len(b)
    assert h.hexdigest()==m['baseline']['RDF']['sha256']
    check_pin(base_sql,m['baseline']['SQLite']);check_pin(base_rdf,m['baseline']['RDF'])
    write_rows(output/'source_reference_projection_NOT_original_frozen_gold.jsonl',actual)
    result.update(status='PASS_ISOLATED_ADDITIVE_SNAPSHOT_FULL_80_TABLE_PRESERVATION',
       materialized_full_snapshot=True,original_RDF_exact_prefix=True,
       old_SQL_table_preservation=preserved,output_SQL=pin(sql_out),output_RDF=pin(rdf_out))
    write_json(output/'actual_root_materialization_receipt.json',result)
    return result

def verify_main():
    p=argparse.ArgumentParser(description='Verify included additive source patch; no native/API.')
    home=Path(__file__).resolve().parent
    p.add_argument('--package',type=Path,default=home if (home/'manifest.json').exists() else home/'package')
    a=p.parse_args()
    print(json.dumps(verify_package(a.package,a.package/'pipeline/load_released_kg.py'),ensure_ascii=False,sort_keys=True))

def materialize_main():
    p=argparse.ArgumentParser(description='Root-only optional isolated additive materializer; refuses existing output.')
    home=Path(__file__).resolve().parent
    p.add_argument('--package',type=Path,default=home if (home/'manifest.json').exists() else home/'package')
    p.add_argument('--baseline-sql',type=Path,required=True);p.add_argument('--baseline-rdf',type=Path,required=True)
    p.add_argument('--output',type=Path);p.add_argument('--preflight-only',action='store_true')
    a=p.parse_args()
    assert a.preflight_only or a.output is not None
    print(json.dumps(materialize(a.package,a.baseline_sql,a.baseline_rdf,a.output,a.preflight_only),ensure_ascii=False,sort_keys=True))

