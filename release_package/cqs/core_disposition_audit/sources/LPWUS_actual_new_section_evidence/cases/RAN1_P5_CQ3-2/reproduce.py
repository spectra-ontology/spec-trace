"""Replay original LP-WUS study/implementation source roles and frozen-input diagnostics.

All query translation is structural and generic. Source witness assertions audit the
classification; they do not supply an answer whitelist to a reference query.
"""
import csv, gzip, hashlib, io, json, re, sqlite3, sys
import xml.etree.ElementTree as E
from pathlib import Path
if sys.flags.optimize:
    raise SystemExit('Run without optimization')
N={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W='{'+N['w']+'}'
INVENTORY_SHA256='e3c42d14fb6521217332f47fb6e6d473b7b1848b13815faeeb38f61c45f5ebb2'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(D,name):
    b=(D/name).read_bytes()
    return json.loads(gzip.decompress(b) if name.endswith('.gz') else b)
def pin_bytes(b):return {'bytes':len(b),'sha256':sha(b)}
def parse_original_query(cypher):
    """Generic exact grammar for this preserved node/property/edge path and projection."""
    ident = r'[A-Za-z_][A-Za-z0-9_]*'
    literal = r"'([^']*)'"
    node = r'\((' + ident + r'):(' + ident + r')\s*\{(' + ident + r'):\s*' + literal + r'\}\)'
    last = r'\((' + ident + r'):(' + ident + r')\)'
    edge = r'-\[:(' + ident + r')\]->'
    pattern = r'MATCH\s+' + node + edge + node + edge + last + r'\s+RETURN\s+(.+?)\s+ORDER BY\s+(' + ident + r'\.' + ident + r')'
    m = re.fullmatch(pattern, cypher)
    assert m, 'Original query outside the independently implemented exact grammar'
    av, al, ak, astring, e1, bv, bl, bk, bstring, e2, cv, cl, projections, order = m.groups()
    aliases = {av: al, bv: bl, cv: cl}
    fields = [x.strip() for x in projections.split(',')]
    assert len(fields) == len(set(fields))
    for field in fields + [order]:
        v, k = field.split('.')
        assert v in aliases and re.fullmatch(ident, k)
    ast = {'nodes': [{'variable': av, 'label': al, 'properties': {ak: astring}},
                     {'variable': bv, 'label': bl, 'properties': {bk: bstring}},
                     {'variable': cv, 'label': cl, 'properties': {}}],
           'relationships': [{'source': av, 'type': e1, 'target': bv},
                             {'source': bv, 'type': e2, 'target': cv}],
           'projections': fields, 'order_by': order}
    select = ','.join(f'{f} AS "{f}"' for f in fields)
    sql = f'SELECT {select} FROM "{al}" {av} JOIN edge e1 ON e1.src_id={av}.node_id AND e1.rel_type=? JOIN "{bl}" {bv} ON {bv}.node_id=e1.dst_id JOIN edge e2 ON e2.src_id={bv}.node_id AND e2.rel_type=? JOIN "{cl}" {cv} ON {cv}.node_id=e2.dst_id WHERE {av}."{ak}"=? AND {bv}."{bk}"=? ORDER BY {order}'
    return ast, sql, (e1, e2, astring, bstring)

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


def active_text(x):
 if x.tag in {W+'del',W+'moveFrom'}:return ''
 return ((x.text or '') if x.tag==W+'t' else '')+''.join(active_text(y) for y in x)

def source_roles(key,xml,styles):
 body=E.fromstring(xml).find('w:body',N);st=E.fromstring(styles)
 sm={x.get(W+'styleId'):x for x in st if x.tag==W+'style'}
 def outline(k,seen=()):
  if k not in sm or k in seen:return None
  el=sm[k];v=el.find('w:pPr/w:outlineLvl',N)
  if v is not None:return int(v.get(W+'val'))
  nm=el.find('w:name',N)
  if nm is not None and re.fullmatch(r'heading\s*[1-9]',nm.get(W+'val',''),re.I):return int(re.search('[1-9]',nm.get(W+'val')).group())-1
  parent=el.find('w:basedOn',N)
  return outline(parent.get(W+'val'),seen+(k,)) if parent is not None else None
 paragraphs=[];heads=[];cover=[]
 for i,x in enumerate(body):
  if x.tag==W+'tbl':
   if re.search(r'Work item code|Clauses affected|CHANGE REQUEST',active_text(x),re.I):cover.append({'body_child':i,'rows':[[active_text(tc) for tc in tr.findall('w:tc',N)] for tr in x.findall('w:tr',N)]})
   continue
  if x.tag!=W+'p':continue
  s=x.find('w:pPr/w:pStyle',N);style=s.get(W+'val') if s is not None else None
  direct=x.find('w:pPr/w:outlineLvl',N);level=int(direct.get(W+'val')) if direct is not None else outline(style)
  row={'body_child':i,'style':style,'outline':level,'text':active_text(x),'insertions':len(x.findall('.//w:ins',N)),'deletions':len(x.findall('.//w:del',N)),'moves_from':len(x.findall('.//w:moveFrom',N)),'paragraph_mark_inserted':x.find('w:pPr/w:rPr/w:ins',N) is not None}
  paragraphs.append(row)
  if level is not None and level<9:heads.append(row)
 sections=[]
 for j,row in enumerate(paragraphs):
  if re.fullmatch(r'\d+\s*(?:Scope|Conclusions?)(?:\s+and\s+recommendations)?\s*',row['text'],re.I):
   end=next((k for k in range(j+1,len(paragraphs)) if paragraphs[k]['outline']==0 or re.match(r'Annex\s*[A-Z]?$',paragraphs[k]['text'])),len(paragraphs))
   sections.append({'heading':row,'paragraphs':paragraphs[j:end]})
 mentions=[row for row in paragraphs if re.search(r'38[.]211|38[.]213|38[.]869|NR_LPWUS|new.{0,25}clause|clause.{0,25}new|WI phase|work item|study item',row['text'],re.I)]
 return {'key':key,'document_xml':{'bytes':len(xml),'sha256':sha(xml)},'styles_xml':{'bytes':len(styles),'sha256':sha(styles)},'body_children':len(body),'resolved_headings':heads,'inserted_numbered_headings':[x for x in heads if x['paragraph_mark_inserted'] and re.match(r'\d',x['text'])],'scope_conclusion_sections':sections,'cover_tables':cover,'all_target_or_workitem_context_mentions':mentions}

def section_number(text):
    m=re.match(r'\d+(?:\.\d+[a-z]?)*(?:[A-Z](?=[A-Z]{2,}))?',text)
    return m.group() if m else None


def semantic_checks(D):
    q=load(D,'contract/original_question_and_query.json')
    raw=(D/'contract/original_benchmark_record.jsonl').read_bytes()
    original=json.loads(raw)
    assert original==q['original_record']
    assert sha(raw)==q['raw_record_sha256']
    assert sha(original['question_en'].encode())==q['question_sha256']
    assert sha(original['cypher'].encode())==q['query_sha256']
    author=load(D,'contract/original_author_CQ_dataset.json')
    criteria=load(D,'contract/criteria.json')
    contract=load(D,'contract/bounded_source_role_contract.json')
    primary=load(D,'contract/primary_exact_seven_unit_source_role_review.json')
    counter=load(D,'contract/counterauthority_and_alternate_recovery_decisions.json')
    assert contract['question_sha256']==primary['question_sha256']==q['question_sha256']
    assert contract['original_query_sha256']==primary['original_query_sha256']==q['query_sha256']
    for field,name in [('criteria','criteria.json'),('bounded_contract','bounded_source_role_contract.json'),('counterauthority','counterauthority_and_alternate_recovery_decisions.json')]:
        assert pin_bytes((D/'contract'/name).read_bytes())=={k:primary[field][k] for k in ['bytes','sha256']}
    assert [x['semantic_unit'] for x in primary['semantic_units']]==criteria['semantic_units']
    assert len(primary['semantic_units'])==7
    assert contract['classification_candidate']==primary['recommendation']=='unsupported_frozen_data'
    assert contract['subtype']==primary['subtype']=='study_to_actual_new_section_extent_not_retained'
    assert contract['new_admission'] is False and primary['new_admission'] is False
    assert primary['nonblind_AI'] is True and primary['expert_validation_n']==0
    assert all(primary[k]==0 for k in ['API_calls','native_calls','P_mutations'])
    assert contract['retained_supporting_query_projections']==original['gold_columns']
    assert contract['answer_roles']==['identities of actual new sections with their target TS identity']
    ast,sql,params=parse_original_query(original['cypher'])
    assert ast['projections']==original['gold_columns']
    assert contract['original_question_ko']==q['author_CQ_record']['question']
    assert q['author_CQ_record'] in author['questions']
    sources=load(D,'source/direct_original_source_format_and_scope.json')
    bykey={x['key']:x for x in sources}
    assert len(sources)==len(bykey)==9
    for x in sources:
        k=x['key'];xml=gzip.decompress((D/'source'/k/'document.xml.gz').read_bytes());styles=gzip.decompress((D/'source'/k/'styles.xml.gz').read_bytes())
        assert source_roles(k,xml,styles)=={a:b for a,b in x.items() if a!='archive'},k
    witness={}
    for spec,key in [('38.211','CR2504981'),('38.213','CR2504971')]:
        src=bykey[key];declared=contract['source_addition_witnesses'][spec]
        assert [x['text'] for x in src['inserted_numbered_headings']]==declared['headings']
        assert len(src['inserted_numbered_headings'])==declared['inserted_heading_n']
        witness[spec]=[section_number(x['text']) for x in src['inserted_numbered_headings']]
        assert len(witness[spec])==len(set(witness[spec]))
        cover=next(x['rows'] for x in src['cover_tables'] if any('Work item code:' in r for r in x['rows']))
        assert next(r for r in cover if r and r[0]=='Work item code:')[1]=='NR_LPWUS-Core'
        cat=next(r for r in cover if r and r[0]=='Category:')
        assert cat[1]=='B' and cat[4]=='Rel-19'
        current={section_number(x['text']) for x in bykey['TS'+spec.replace('.','')]['resolved_headings']}
        assert set(witness[spec])<=current
    assert len(witness['38.211'])==11 and len(witness['38.213'])==2
    assert '7.4.4.1.2' in witness['38.211'] and '7.4.1.2' not in witness['38.211'] and '7.1.2' not in witness['38.211']
    assert set(witness['38.213'])=={'10.4C','10.4D'}
    for k in ['CR2506651','CR2506659','CR2509636','CR2509707']:
        assert bykey[k]['inserted_numbered_headings']==[]
    headings213=bykey['TS38213']['resolved_headings']
    original14=next(x for x in headings213 if section_number(x['text'])=='14' and x['outline']==0)
    assert original14['text'].strip()=='14Integrated access-backhaul operation'
    assert not any(section_number(x['text'])=='17' and x['outline']==0 for x in bykey['TS38211']['resolved_headings'])
    conclusion='\n'.join(x['text'] for s in bykey['TR38869']['scope_conclusion_sections'] for x in s['paragraphs'])
    assert 'Details are to be decided in WI phase.' in conclusion
    assert 'Detailed design is to be decided in WI.' in conclusion

    graph=load(D,'frozen/expanded_complete_literal_and_own_role_slice.json.gz')
    c,records=memory_graph(graph,load(D,'frozen/original_SQL_table_schemas.json'))
    diagnostics=load(D,'frozen/actual_immutable_SQL_diagnostics.json.gz')
    global_sql=load(D,'frozen/actual_global_literal_recovery_SQL.json.gz')
    combined={**diagnostics,**global_sql}
    assert len(combined)==15
    replay={}
    for role,d in combined.items():
        assert sha(d['sql'].encode())==d['sql_sha256']
        cur=c.execute(d['sql']);rows=[dict(x) for x in cur]
        assert rows==d['rows'] and len(rows)==d['row_count'],role
        if rows:assert list(rows[0])==list(d['rows'][0]),role
        replay[role]=len(rows)
    original_rows=[dict(x) for x in c.execute(sql,params)]
    assert original_rows==diagnostics['original_projection']['rows']==diagnostics['inverse_projection']['rows']==contract['original_projection']
    assert len(original_rows)==1
    own=diagnostics['all_own_impacts_and_section_titles']['rows']
    assert len(own)==2
    assert {(x['specNumber'],x['affectedSection']) for x in own}=={('38.211','17'),('38.213','14')}
    actual_pairs=[{'spec':x['specNumber'],'affectedSection':x['affectedSection'],'impactType':x['impactType'],'sectionId':x['sectionId'],'sectionTitle':x['sectionTitle']} for x in own]
    assert actual_pairs==contract['manual_impact_pairs']
    resolved=[x for x in own if x['sectionId'] is not None]
    assert len(resolved)==1 and resolved[0]['sectionTitle']=='Integrated access-backhaul operation'
    assert resolved[0]['sectionId']=='38.213-Rel-19-14'
    selected=[x for x in csv.DictReader(io.StringIO((D/'source/original_tr_impact_mapping.csv').read_text())) if x['trNumber']=='38.869']
    assert len(selected)==2
    for x in own:
        v=next(y for y in selected if y['impactsSpec']==x['specNumber'])
        assert v['impactsSection']==x['affectedSection'] and v['impactType']==x['impactType']=='NewSection'
        assert v['impactDescription']==x['impactDescription']
    def node_by_tdoc(t):
        rows=[(nid,r) for nid,r in records.items() if 'CR' in r['labels'] and r['properties'].get('tdocNumber')==t]
        assert len(rows)==1;return rows[0]
    def modified_numbers(nid):
        return {records[e['dst_id']]['properties']['sectionNumber'] for e in graph['edges'] if e['src_id']==nid and e['rel_type']=='MODIFIES_SECTION'}
    n211,r211=node_by_tdoc('R1-2504981');n213,r213=node_by_tdoc('R1-2504971')
    mod211=modified_numbers(n211);mod213=modified_numbers(n213)
    assert len(mod211)==12 and {'7.1.2','7.4.1.2'}<=mod211 and '7.4.4.1.2' not in mod211
    assert '7.4.4.1.2' not in r211['properties']['clausesAffected']
    assert mod213=={'3.3'}
    parsed_new=re.findall(r'(\d+(?:\.\d+)*[A-Za-z]?)\s*\(new\)',r213['properties']['clausesAffected'])
    assert set(parsed_new)==set(witness['38.213'])
    for key in ['CR2504981','CR2504971']:
        src=bykey[key];n,r=node_by_tdoc('R1-'+key[2:])
        cover=next(x['rows'] for x in src['cover_tables'] if any('Clauses affected:' in row for row in x['rows']))
        text=next(row[1] for row in cover if row and row[0]=='Clauses affected:')
        assert text==r['properties']['clausesAffected']
    # Recovery also retains candidates having only CRPack membership.
    for t in ['R1-2601590','R1-2601741']:
        nid,_=node_by_tdoc(t)
        assert t in {x['tdocNumber'] for x in global_sql['all_topic_CR_fields_without_required_Spec_or_WI_edge']['rows']}
        assert any(e['src_id']==nid or e['dst_id']==nid for e in graph['edges'])
    frontier=load(D,'frozen/whole_decoded_LPWUS_literal_frontier.json.gz')
    assert frontier['nodes_scanned']==165418 and frontier['decoded_string_scalars_scanned']==1112204
    def strings(v):
        if isinstance(v,str):yield v
        elif isinstance(v,list):
            for x in v:yield from strings(x)
        elif isinstance(v,dict):
            for x in v.values():yield from strings(x)
    hits=[]
    for nid,r in sorted(records.items()):
        for v in strings(r['properties']):
            if re.search(r'38[.]869|LP[-_ ]?WUS|LP[-_ ]?WUR|low[- ]power wake',v,re.I):hits.append({'node_id':nid,'labels':r['labels'],'value':v})
    assert hits==frontier['literal_values']
    assert len(hits)==1881 and len({x['node_id'] for x in hits})==1797
    assert {x['node_id'] for x in hits}<=set(graph['core_node_ids'])
    assert len(graph['core_node_ids'])==1813 and len(records)==8248 and len(graph['edges'])==15877
    assert all(e['src_id'] in graph['core_node_ids'] or e['dst_id'] in graph['core_node_ids'] for e in graph['edges'])
    for file in ['actual_source_and_frozen_reopen_receipt.json','actual_global_recovery_receipt.json']:
        receipt=load(D,'provenance/'+file)
        assert receipt['sqlite_before']==receipt['sqlite_after']
        assert all(receipt[k]==0 for k in ['API_calls','native_calls','public_writes'])
    c.close()
    phase='primary_preparation'
    ai_reviews=1
    if (D/'contract/ROOT_secondary_review.json').is_file():
        secondary=load(D,'contract/ROOT_secondary_review.json')
        su=secondary.get('semantic_units',secondary.get('units'))
        assert [x.get('semantic_unit',x.get('unit')) for x in su]==criteria['semantic_units']
        assert secondary['id']==original['id']
        decision=secondary.get('decision',secondary.get('recommendation',secondary.get('classification')))
        assert decision=='unsupported_frozen_data' and secondary['subtype']==contract['subtype']
        assert secondary['question_sha256']==q['question_sha256'] and secondary['original_query_sha256']==q['query_sha256']
        assert secondary['criteria_sha256']==sha((D/'contract/criteria.json').read_bytes())
        assert secondary['two_nonblind_AI_review_context'] is True and secondary['expert_validation_n']==0
        assert secondary['whole_original_question_verified_pass'] is False and secondary['complete_answer_oracle_created'] is False
        replay_path=D/'provenance/actual_ROOT_independent_original_and_SQL_replay.json'
        assert sha(replay_path.read_bytes())==secondary['actual_ROOT_direct_replay']['sha256']
        root_replay=json.loads(replay_path.read_bytes())
        assert root_replay['status']=='PASS_ROOT_INDEPENDENT_DIRECT_ORIGINAL_SOURCE_AND_FROZEN_ROLE_REPLAY'
        assert root_replay['id']==original['id'] and root_replay['source_XML_style_pair_n']==9 and root_replay['SQL_role_n']==15
        assert {x['role'] for x in root_replay['actual_immutable_SQL_roles']}==set(combined)
        for x in root_replay['actual_immutable_SQL_roles']:
            assert x['sql_sha256']==combined[x['role']]['sql_sha256'] and x['actual_rows']==replay[x['role']]
        for x in root_replay['actual_direct_original_sources']:
            src=bykey[x['key']]
            assert x['archive_sha256']==src['archive']['sha256'] and x['document_xml_sha256']==src['document_xml']['sha256'] and x['styles_xml_sha256']==src['styles_xml']['sha256']
            assert x['inserted_numbered_headings_reparsed']==src['inserted_numbered_headings']
        assert root_replay['frozen_DB_before_sha256']==root_replay['frozen_DB_after_sha256']=='aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
        assert all(root_replay[k]==secondary[k]==0 for k in ['API_calls','native_calls','public_writes'])
        ai_reviews=2;phase='independent_reviewed'
        if (D/'contract/ROOT_final_disposition.json').is_file():
            seal=load(D,'contract/ROOT_final_disposition.json')
            assert seal['id']==original['id']
            assert seal['classification']==seal['local_status']=='unsupported_frozen_data'
            assert seal['subtype']==contract['subtype']
            assert seal['original_question_sha256']==q['question_sha256']
            assert seal['criteria_sha256']==sha((D/'contract/criteria.json').read_bytes())
            assert seal['two_nonblind_AI_semantic_judgments'] is True and seal['human_expert_n']==0
            assert seal['whole_original_question_verified_pass'] is False
            assert seal['complete_source_enriched_oracle_created'] is False
            for role,name in [('primary_review','contract/primary_exact_seven_unit_source_role_review.json'),('independent_ROOT_review','contract/ROOT_secondary_review.json'),('source_role_contract','contract/bounded_source_role_contract.json'),('counterauthority_and_alternate_recovery','contract/counterauthority_and_alternate_recovery_decisions.json'),('original_source_and_SQL_replay','provenance/actual_ROOT_independent_original_and_SQL_replay.json')]:
                assert pin_bytes((D/name).read_bytes())=={k:seal[role][k] for k in ['bytes','sha256']},role
            phase='final_sealed'
    return {'status':'PASS','id':original['id'],'phase':phase,'classification':'unsupported_frozen_data','subtype':contract['subtype'],'source_XML_style_pairs_reparsed':len(sources),'SQL_roles_all_rows_and_columns_replayed':replay,'source_inserted_heading_witnesses':witness,'source_witnesses_are_answer_gold':False,'generic_original_query_AST':ast,'generic_translated_SQL_sha256':sha(sql.encode()),'complete_incident_core_nodes':len(graph['core_node_ids']),'literal_recovery_values':len(hits),'graph_records':len(records),'graph_edges':len(graph['edges']),'AI_reviews':ai_reviews,'nonblind_AI':True,'human_expert_reviews':0,'new_original_admissions':0,'new_model_evaluations':0,'API_calls':0,'native_calls':0,'P_mutations':0,'scope':'Replays included bounded graph/source witnesses and full recorded SQL results. Original immutable DB/archive reopening is a separate supplied-input operation; literal recovery is candidate coverage, not arbitrary causal closure.'}


def verify(D):
    inventory_bytes=(D/'immutable_inventory.json').read_bytes()
    assert sha(inventory_bytes)==INVENTORY_SHA256
    inv=json.loads(inventory_bytes)
    for name,pin in inv['files'].items():
        p=D/name
        assert p.is_file() and not p.is_symlink()
        assert pin_bytes(p.read_bytes())==pin,name
    manifest=load(D,'manifest.json')
    actual={p.relative_to(D).as_posix() for p in D.rglob('*') if p.is_file() and p.name!='manifest.json'}
    assert set(manifest['files'])==actual
    for name,pin in manifest['files'].items():assert pin_bytes((D/name).read_bytes())==pin,name
    result=semantic_checks(D)
    assert result['AI_reviews']==manifest['AI_reviews']
    assert result['phase']==manifest['phase']
    assert manifest['new_model_evaluations']==manifest['new_original_admissions']==0
    return result

if __name__=='__main__':
    print(json.dumps(verify(Path(__file__).resolve().parent),ensure_ascii=False))
