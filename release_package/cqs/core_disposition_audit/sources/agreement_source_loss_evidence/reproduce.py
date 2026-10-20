"""Reproduce two bounded necessary-membership diagnostics, entirely offline."""
import sys
if sys.flags.optimize:
    raise SystemExit('Run without -O/-OO; this verifier fails closed')
import gzip
import hashlib
import json
from pathlib import Path
import stat
import xml.etree.ElementTree as ET

ROOT = Path(__file__).absolute().parent
IMMUTABLE_INVENTORY_SHA256 = '08495428373bdc9ff81eaacf827d0658a7f8a475cff19ac8f57afc3999527ca6'
CRITERIA_SHA256 = 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'
DB_SHA256 = 'aef09592ac92a89b901ef1b8b5432b8737e22e0c94d6cd7685de21ab23fba4af'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'


def need(ok, why):
    if not ok:
        raise RuntimeError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def no_links(path):
    for p in (path, *path.parents):
        need(not p.is_symlink(), 'Symlink path forbidden')


def read(name):
    p=ROOT/name
    no_links(p)
    need(p.is_file(), 'Missing regular package file')
    return p.read_bytes()


def load(name):
    return json.loads(read(name))


def gzload(name):
    return json.loads(gzip.decompress(read(name)))


def text(el):
    return ''.join(x.text or '' for x in el.iter(W+'t'))


def geometry_literal(el):
    # Preserve original common3176 extraction, including OfficeMath.
    return ''.join(x.text or '' for x in el.iter() if x.tag in (W+'t',M+'t'))


def check_tree():
    no_links(Path(__file__).absolute())
    inv=load('inventory.json')
    expected=set(inv['files'])|{'inventory.json'}
    files=set()
    dirs=set()
    for p in ROOT.rglob('*'):
        need(not p.is_symlink(), 'Package symlink forbidden')
        mode=p.stat(follow_symlinks=False).st_mode
        if stat.S_ISREG(mode): files.add(p.relative_to(ROOT).as_posix())
        elif stat.S_ISDIR(mode): dirs.add(p.relative_to(ROOT).as_posix())
        else: raise RuntimeError('Nonregular package entry forbidden')
    need(files==expected, 'Closed package file set differs')
    allowed_dirs={str(p) for name in files for p in Path(name).parents if str(p)!='.'}
    need(dirs==allowed_dirs, 'Unexpected or missing package directory')
    for name,pin in inv['files'].items():
        raw=read(name)
        need(type(pin['bytes']) is int and len(raw)==pin['bytes'] and sha(raw)==pin['sha256'], 'Package file pin differs')
    raw=read('immutable_inventory.json')
    need(sha(raw)==IMMUTABLE_INVENTORY_SHA256,'Fixed scientific inventory differs')
    immutable=json.loads(raw)
    need(set(immutable['files'])==files-{'README.md','reproduce.py','inventory.json','immutable_inventory.json'},'Immutable file set differs')
    for name,pin in immutable['files'].items():
        raw=read(name)
        need(len(raw)==pin['bytes'] and sha(raw)==pin['sha256'],'Fixed scientific payload differs')


def check_format(body, styles, g, saved, keys):
    lo,hi=g['source_record_raw_body_child_range']
    stmap={e.get(W+'styleId'):e for e in styles.findall(W+'style')}
    wanted={k for k,e in stmap.items() if e.get(W+'default') in ('1','true','on')}
    for el in body[lo:hi]:
        for tag in ['pStyle','rStyle','tblStyle']:
            wanted.update(e.get(W+'val') for e in el.iter(W+tag))
    closure=set()
    def visit(k):
        if k in closure:return
        need(k in stmap,'Missing referenced style')
        closure.add(k)
        based=stmap[k].find(W+'basedOn')
        if based is not None:visit(based.get(W+'val'))
    for k in wanted:visit(k)
    need(sorted(closure)==saved['style_closure'],'Referenced style closure differs')
    on=lambda e:e.get(W+'val','true').lower() not in ('0','false','off','no')
    flags=['strike','dstrike','vanish','webHidden']
    defaults=styles.find(W+'docDefaults')
    need(defaults is not None,'DocDefaults absent')
    need(not any(on(e) for f in flags for e in defaults.iter(W+f)),'Keyword default format not retained')
    need(not any(on(e) for k in closure for f in flags for e in stmap[k].iter(W+f)),'Keyword style format not retained')
    paras=[]
    for i in range(lo,hi):
        for p in ([body[i]] if body[i].tag==W+'p' else list(body[i].iter(W+'p'))):
            if any(k in text(p) for k in keys):
                need(not any(True for f in ['del','moveFrom'] for e in p.iter(W+f)),'Deleted keyword paragraph')
                need(not any(on(e) for f in flags for e in p.iter(W+f)),'Keyword paragraph has inspected hidden/strike formatting')
                paras.append((i,text(p),sha(ET.tostring(p,encoding='utf-8'))))
    if 'source_keyword_paragraphs' in saved:
        expected=[(p['raw_body_child'],p['text'],p['XML_ET_utf8_sha256']) for p in saved['source_keyword_paragraphs']]
        need(paras==expected,'Exact own SRS keyword paragraphs differ')
    else:
        expected=[(p['text'],p['XML_ET_unicode_sha256']) for p in saved['own_table_paragraphs'] if p['keyword_PUCCH'] or p['keyword_resource']]
        need([(t,h) for _,t,h in paras]==expected,'Exact own PUCCH keyword paragraphs differ')
    return len(paras)


def main():
    check_tree()
    criteria=load('contract/criteria.json')
    need(sha(read('contract/criteria.json'))==CRITERIA_SHA256,'Original criteria differ')
    config=load('cases.json')
    need(config['classification']=='unsupported_frozen_data' and config['subtype']=='own_source_span_loss' and type(config['new_admissions']) is int and config['new_admissions']==0,'Diagnostic is not an admission')
    geometry=[json.loads(l) for l in gzip.decompress(read('source/identity_and_source_geometry.jsonl.gz')).splitlines()]
    need(len(geometry)==3176 and len({g['resolutionId'] for g in geometry})==3176,'Complete retained geometry differs')
    provenance=load('source/original_archive_and_XML_provenance.json')
    spec=provenance['shared_report']
    xb=gzip.decompress(read('source/RAN1_123_document.xml.gz'))
    sb=gzip.decompress(read('source/RAN1_123_styles.xml.gz'))
    need(sha(xb)==spec['document_XML_sha256'] and sha(sb)==spec['styles_XML_sha256'],'Actual raw XML pins differ')
    body=list(ET.fromstring(xb).find(W+'body'))
    styles=ET.fromstring(sb)
    latest=[g for g in geometry if g['meeting']=='RAN1#123']
    need(len(latest)==286,'Complete latest own-window frontier differs')
    source={}
    for g in latest:
        lo,hi=g['source_record_raw_body_child_range']
        need(type(lo) is int and type(hi) is int and 0<=lo<hi<len(body),'Own window out of range')
        need(text(body[lo]).startswith('Agreement'),'Own Agreement label absent')
        geometry_t='\n'.join(geometry_literal(e) for e in body[lo:hi])
        need(sha(geometry_t.encode())==g['source_record_literal_sha256'],'Own source literal differs from original Word-plus-math geometry')
        # Historical sealed literal membership used Word w:t only; do not broaden it.
        t='\n'.join(text(e) for e in body[lo:hi])
        source[g['resolutionId']]=(g,t)
    frozen=gzload('frozen/complete_retained3176_dependency_projection.json.gz')
    agreements={r['node_id']:r for r in frozen['Agreement']}
    meetings={r['node_id']:r for r in frozen['Meeting']}
    need(len(agreements)==3176 and {r['resolutionId'] for r in agreements.values()}=={g['resolutionId'] for g in geometry},'Frozen/source3176 identity mismatch')
    paths=[]
    for e in frozen['MADE_AT']:
        need(e['rel_type']=='MADE_AT' and e['src_id'] in agreements and e['dst_id'] in meetings,'Invalid projected MADE_AT role')
        paths.append((agreements[e['src_id']],meetings[e['dst_id']]))
    need(len(paths)==3176,'Full retained MADE_AT count differs')
    need(max(m['meetingNumberInt'] for a,m in paths)==123,'Fresh latest-meeting bound differs')
    need({a['resolutionId'] for a,m in paths if m['meetingNumberInt']==123}==set(source),'Latest source/frozen identity mismatch')
    dbproof=load('frozen/fresh_projection_provenance.json')
    need(dbproof['DB_sha256_before']==dbproof['DB_sha256_after']==DB_SHA256 and dbproof['DB_mutations']==0,'Fresh immutable DB provenance differs')
    need(dbproof['excluded_max_meetingNumberInt']==116 and dbproof['whole_original_Agreement_n']==21058 and dbproof['whole_original_Agreement_MADE_AT_paths_n']==21288,'Whole graph versus retained-scope boundary differs')
    outcomes=[]
    for case in config['cases']:
        qid=case['id'];prefix='cases/'+qid+'/'
        original=load(prefix+'original_question_and_query.json')
        query=original.get('cypher',original.get('original_Cypher'))
        need(sha(original['question_en'].encode())==original['question_sha256'] and sha(query.encode())==original['query_sha256'],'Exact original question/query binding differs')
        sealed=load(prefix+'ROOT_final.json')
        need(sealed['id']==qid and sealed['question_sha256']==original['question_sha256'] and sealed['original_query_sha256']==original['query_sha256'],'ROOT original binding differs')
        need(sealed['recommended_final_classification']=='unsupported_frozen_data' and sealed['remaining_gate'] is None,'Sealed classification not complete')
        for field,name in [('minimum_necessary_contract','minimum_contract.json'),('primary_seven_unit_review','primary_seven_unit_review.json'),('ROOT_secondary_review','ROOT_secondary_seven_unit_review.json'),('counterauthority_and_alternatives','counterauthority_and_alternatives.json')]:
            need(sha(read(prefix+name))==sealed[field]['sha256'],'Sealed semantic/counterauthority evidence pin differs')
        for name in ['primary_seven_unit_review.json','ROOT_secondary_seven_unit_review.json']:
            review=load(prefix+name)
            need(review['id']==qid and review['criteria']['sha256']==CRITERIA_SHA256,'Review identity/criteria differ')
            need([u['semantic_unit'] for u in review['semantic_units']]==criteria['semantic_units'],'Exact original seven units differ')
        keys=['PUCCH','resource'] if qid.endswith('13') else ['SRS','configuration']
        need(all("a.content CONTAINS '"+k+"'" in query for k in keys) and query.endswith(' LIMIT 10'),'Authored literal-instance contract differs')
        historical=[json.loads(l) for l in gzip.decompress(read(prefix+'historical_latest286_frontier.jsonl.gz')).splitlines()]
        need(len(historical)==286 and {r['resolutionId'] for r in historical}==set(source),'Historical source frontier scope differs')
        for r in historical:
            g,t=source[r['resolutionId']]
            need(r['own_literal_sha256']==sha(t.encode()) and r.get('own_raw_text',r.get('text'))==t,'Independently rebuilt source frontier differs')
        candidates=sorted(rid for rid,(g,t) in source.items() if all(k in t for k in keys))
        rid=case['witness'];rank=candidates.index(rid)+1
        need(rank==case['source_literal_rank'] and rank<=10 and len(candidates)==(6 if qid.endswith('13') else 8),'Necessary selected-prefix source membership differs')
        result=[{'meetingNumber':m['meetingNumber'],'resolutionId':a['resolutionId'],'content':a['content']} for a,m in sorted(paths,key=lambda x:(-x[1]['meetingNumberInt'],x[0]['resolutionId'])) if a['content'] is not None and all(k in a['content'] for k in keys)][:10]
        fresh=load(prefix+'fresh_full_original_SQL10.json')
        historical_sql=load(prefix+'historical_original_SQL10.json')
        need(result==fresh['records']==historical_sql['records'] and len(result)==10,'Independent projection replay differs from actual whole-graph original SQL10')
        need(rid not in {r['resolutionId'] for r in result},'Necessary source member no longer excluded by frozen query')
        selected_paths=[(a,m) for a,m in paths if a['resolutionId'] in {r['resolutionId'] for r in result}]
        need(min(m['meetingNumberInt'] for a,m in selected_paths)>dbproof['excluded_max_meetingNumberInt'],'Omitted old paths could enter prefix')
        g,t=source[rid];saved=load(prefix+'direct_source_and_format.json')
        need(g['source_record_raw_body_child_range']==saved['raw_body_child_range'],'Witness ownership geometry differs')
        nformat=check_format(body,styles,g,saved,keys)
        alt=load(prefix+'historical_whole_frozen_alternatives.json')
        typed=alt.get('typed_Agreement',alt.get('witness_typed_Agreement'))
        actual=next(r for r in agreements.values() if r['resolutionId']==rid)
        need(actual==typed and not actual['note'] and not actual['contentWithEquations'] and not all(k in actual['content'] for k in keys),'Frozen content/note/equation alternative changed')
        roles=alt.get('all_incident_edges',alt.get('witness_all_incident_edges'))
        need({e['rel_type'] for e in roles}=={'MADE_AT','RESOLUTION_BELONGS_TO'},'Historical source-association alternate roles differ')
        need(alt['DB_before']['sha256']==alt['DB_after']['sha256']==DB_SHA256 and alt['all_node_records_scanned']==165418,'Historical full-scan provenance differs')
        need(any(alt['global_fragment_hits'].values()),'Historical positive counterevidence must be retained')
        outcomes.append({'id':qid,'classification':'unsupported_frozen_data','subtype':'own_source_span_loss','latest_retained_source_records':286,'source_literal_candidates':len(candidates),'witness':rid,'witness_literal_rank':rank,'frozen_original_SQL10_contains_witness':False,'keyword_paragraphs_format_checked':nformat,'scope':'Necessary own-record membership for the original literal-search instance; no corrected technical gold or global impossibility claim.'})
    need({x['id'] for x in outcomes}=={'RAN1_P2_CQ5-13','RAN1_P2_CQ5-3'},'Case set differs')
    print(json.dumps({'status':'PASS','cases':outcomes,'new_admissions':0},ensure_ascii=False))


if __name__=='__main__':
    main()
