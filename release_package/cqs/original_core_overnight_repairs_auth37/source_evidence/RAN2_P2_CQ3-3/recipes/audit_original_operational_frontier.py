#!/usr/bin/env python3
"""Read-only original recorded-reference contract and finite source-dependency audit.

This is an evidence audit, not native capture, gold construction, or a causal metric.
"""
import argparse, collections, gzip, hashlib, json, re, sqlite3, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
X='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
def sha(b): return hashlib.sha256(b).hexdigest()
def norm(t): return ''.join(t.split()).replace('\x07','')
def canon(t): return re.sub('[^a-z0-9]','',t.casefold())
def must(v, why):
    if not v: raise RuntimeError(why)
def pin(p,root):
    b=p.read_bytes(); return {'path':p.resolve().relative_to(root).as_posix(),'bytes':len(b),'sha256':sha(b)}
def workbook(p, wanted):
    found=[]; members=[]
    with zipfile.ZipFile(p) as z:
        must(z.testzip() is None,'XLSX CRC')
        ss=[''.join(n.text or '' for n in e.iter(X+'t')) for e in ET.fromstring(z.read('xl/sharedStrings.xml'))] if 'xl/sharedStrings.xml' in z.namelist() else []
        for name in sorted(n for n in z.namelist() if re.fullmatch(r'xl/worksheets/sheet[0-9]+\.xml',n)):
            raw=z.read(name); headers=None
            for row in ET.fromstring(raw).iter(X+'row'):
                cells={}
                for cell in row:
                    col=re.sub('[0-9]','',cell.get('r','')); v=cell.find(X+'v'); val=(v.text or '') if v is not None else ''
                    if cell.get('t')=='s': val=ss[int(val)] if val else ''
                    elif cell.get('t')=='inlineStr': val=''.join(n.text or '' for n in cell.iter(X+'t'))
                    cells[col]=val
                if headers is None:
                    if 'TDoc' in cells.values(): headers=cells
                    continue
                vals={headers[k]:v for k,v in cells.items() if k in headers}
                # Identity is only the named TDoc column, never Replaces/other cells.
                if vals.get('TDoc','').strip() in wanted:
                    found.append({'member':name,'row':row.get('r'),'literal_row':vals})
            members.append({'path':name,'bytes':len(raw),'sha256':sha(raw),'CRC':z.getinfo(name).CRC})
    return found,members

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source-root',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    must(not a.output.exists(),'refuse existing output'); root=a.source_root.resolve(); case=Path(__file__).resolve().parent.parent
    portable=case/'source_portable_v2'; projection=portable/'data/retained_resolution_and_path_projection.json.gz'
    fixture=json.loads(gzip.decompress(projection.read_bytes())); res={r['node_id']:r for r in fixture['Resolution']}
    db=root/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/relational/RAN2.sqlite'; dbbefore=pin(db,root)
    con=sqlite3.connect('file:'+str(db)+'?mode=ro&immutable=1',uri=True); con.execute('pragma query_only=on'); con.row_factory=sqlite3.Row
    q='''SELECT r.node_id rn,r.resolutionId,t.node_id tn,t.tdocNumber,w.node_id wn,w.workItemCode,c.node_id cn,c.companyName FROM Resolution r JOIN rel_REFERENCES e ON e.src_id=r.node_id JOIN Tdoc t ON t.node_id=e.dst_id JOIN rel_RELATED_TO rw ON rw.src_id=t.node_id JOIN WorkItem w ON w.node_id=rw.dst_id JOIN rel_SUBMITTED_BY sc ON sc.src_id=t.node_id JOIN Company c ON c.node_id=sc.dst_id'''
    paths=[dict(r) for r in con.execute(q)]
    ct=lambda rows:collections.Counter(tuple(sorted(r.items())) for r in rows)
    must(ct(paths)==ct(fixture['paths']),'SQL/projection full paths')
    tdocs={r['tdocNumber']:r['node_id'] for r in con.execute('SELECT node_id,tdocNumber FROM Tdoc')}
    expected={(r['node_id'],tdocs[t]) for r in fixture['Resolution'] for t in set(re.findall(r'R2-\d{7}',r['content'] or '')) if t in tdocs}
    actual={(r[0],r[1]) for r in con.execute('SELECT e.src_id,e.dst_id FROM rel_REFERENCES e JOIN Resolution r ON r.node_id=e.src_id JOIN Tdoc t ON t.node_id=e.dst_id')}
    must(expected==actual,'authored7digit REFERENCES difference')
    groups=collections.defaultdict(set)
    for p in paths: groups[p['workItemCode'],p['companyName']].add(p['rn'])
    codes=sorted({w for w,c in groups}); first=codes[:5]; dep=[p for p in paths if p['workItemCode'] in first]; rids={p['rn'] for p in dep}; tids={p['tn'] for p in dep}
    must(len(paths)==13654 and len(res)==3773,'recorded scope changed')
    group_rows=[{'workItemCode':w,'company':c,'count':len(v),'resolution_nodes':sorted(v)} for (w,c),v in groups.items()]
    group_rows.sort(key=lambda x:(x['workItemCode'],-x['count'],x['company']))
    nonliteral=[p for p in paths if p['tdocNumber'] not in set(re.findall(r'(?<![A-Za-z0-9])R2-[0-9]{6,8}(?![0-9])',res[p['rn']]['content'] or ''))]
    must(not any(p['rn'] in rids and p['workItemCode'] in first for p in nonliteral),'first5 nonliteral width diagnostic')
    source=json.loads((case/'actual_source_reopened_recorded_frontier_diagnostic_v2.json').read_text()); loc=json.loads((portable/'data/original_source_location_map.json').read_text())
    source_cases=[]; cache={}
    for ca in source['cases']:
        if ca['node_id'] not in rids: continue
        original=source['source_reports'][ca['source_meeting']]['pin']; p=Path(original['path']); raw=p.read_bytes(); must(sha(raw)==original['sha256'],'source archive pin')
        if p not in cache:
            with zipfile.ZipFile(p) as z:
                must(z.testzip() is None,'DOCX CRC'); xml=z.read('word/document.xml'); styles=z.read('word/styles.xml'); members={n:{'bytes':len(z.read(n)),'sha256':sha(z.read(n)),'CRC':z.getinfo(n).CRC} for n in ('word/document.xml','word/styles.xml')}
            recorded=loc['DOCX_XML'][str(p)]
            must(xml==gzip.decompress((portable/recorded['members']['word/document.xml']['path']).read_bytes()),'included original XML')
            must(styles==gzip.decompress((portable/recorded['members']['word/styles.xml']['path']).read_bytes()),'included original styles')
            bs=list(ET.fromstring(xml).find(W+'body'))
            texts=[''.join((v.text or '') if v.tag==W+'t' else '\t' if v.tag==W+'tab' else '\n' for v in e.iter() if v.tag in (W+'t',W+'tab',W+'br',W+'cr')) for e in bs]
            annex=[]
            for i,e in enumerate(bs):
                sty=e.find(W+'pPr/'+W+'pStyle'); sid=sty.get(W+'val','') if sty is not None else ''
                if re.match(r'^Annex\s+[A-G]\s*:',texts[i].strip(),re.I) and 'toc' not in sid.lower(): annex.append(i)
            cache[p]=(texts,annex,members)
        texts,annex,members=cache[p]; content=res[ca['node_id']]['content']; needle=norm(content); found=[]
        for pos in ca['position_candidates']:
            start=pos['start_body_child']; joined=''; end=start
            while end<len(texts) and len(norm(joined))<len(needle)+500:
                joined+='\n'+texts[end]; end+=1
                if needle in norm(joined):found.append([start,end]); break
        must(found,'whole retained content source match '+ca['resolutionId']); must(annex and all(b<=annex[0] for x,b in found),'preAnnex fullcontent dependency')
        ps=[p for p in dep if p['rn']==ca['node_id']]
        must(all(p['tdocNumber'] in set(re.findall(r'R2-\d{7}',content)) for p in ps),'source-address incidence')
        source_cases.append({'resolution_node':ca['node_id'],'resolutionId':ca['resolutionId'],'source_archive':pin(p,root),'source_members':members,'raw_body_children_fullcontent_matches':found,'first_Annex_body_child':annex[0],'retained_content_bytes':len(content.encode()),'retained_content_sha256':sha(content.encode()),'normalization':'remove Unicode whitespace and Word cell separator U+0007 only; full retained body must be contiguous, not merely its prefix','first5_path_n':len(ps),'first5_tdoc_ids':sorted({p['tdocNumber'] for p in ps})})
    must(len(source_cases)==len(rids),'complete dependency Resolution coverage')
    # Register-role provenance for every participating TDoc. Read only the matching meeting workbook(s).
    placeholders=','.join('?' for _ in tids)
    mt=[dict(r) for r in con.execute('SELECT t.node_id,t.tdocNumber,m.meetingNumber FROM Tdoc t JOIN rel_PRESENTED_AT e ON e.src_id=t.node_id JOIN Meeting m ON m.node_id=e.dst_id WHERE t.node_id IN ('+placeholders+')',sorted(tids))]
    wbpaths=list((root/'data/corpus/tsg/RAN/formal/meetings/RAN2/source').rglob('*.xlsx'))
    def meetkey(t):return re.sub('[^a-z0-9]','',t.casefold()).replace('tdoclistmeeting','')
    bymeeting=collections.defaultdict(set)
    for m in mt: bymeeting[m['meetingNumber']].add(m['tdocNumber'])
    rows=collections.defaultdict(list); workbooks=[]
    for meeting,wanted in sorted(bymeeting.items()):
        candidates=[p for p in wbpaths if meetkey(p.stem)==meetkey(meeting)]
        must(candidates,'no original workbook '+meeting)
        for p in candidates:
            observed,members=workbook(p,wanted); pp=pin(p,root)
            workbooks.append({'pin':pp,'meeting':meeting,'members':members,'target_ids_n':len(wanted),'matched_rows_n':len(observed)})
            for rr in observed: rows[rr['literal_row']['TDoc'].strip()].append({'source':pp,**rr})
    roles=[]; failures=[]
    for tn in sorted(tids):
        td=dict(con.execute('SELECT * FROM Tdoc WHERE node_id=?',(tn,)).fetchone()); tid=td['tdocNumber']
        companies=[dict(r) for r in con.execute('SELECT c.* FROM rel_SUBMITTED_BY e JOIN Company c ON e.dst_id=c.node_id WHERE e.src_id=?',(tn,))]
        wis=[dict(r) for r in con.execute('SELECT w.* FROM rel_RELATED_TO e JOIN WorkItem w ON e.dst_id=w.node_id WHERE e.src_id=?',(tn,))]
        matches=[]
        for rr in rows[tid]:
            vals=rr['literal_row']; pieces={canon(re.sub(r'\s*\((?:Rapporteur|Moderator|Rapporteurs)\)\s*$','',s,flags=re.I)) for s in vals.get('Source','').split(',')}
            cok=[]
            for co in companies:
                ali=co['aliases'] or co['companyName']; aliases=json.loads(ali) if ali.lstrip().startswith('[') else [ali]
                cok.append(any(canon(a) in pieces for a in [co['companyName']]+aliases))
            wset={x.strip() for x in vals.get('Related WIs','').split(',')}; wok=all(w['workItemCode'] in wset for w in wis)
            matches.append({**rr,'all_recorded_company_roles_supported':all(cok),'all_recorded_WI_roles_supported':wok})
        okay=any(x['all_recorded_company_roles_supported'] and x['all_recorded_WI_roles_supported'] for x in matches)
        if not okay:failures.append({'tdocNumber':tid,'companies':[x['companyName'] for x in companies],'WIs':[x['workItemCode'] for x in wis],'register_rows':matches})
        roles.append({'tdocNumber':tid,'node_id':tn,'recorded_companies':companies,'recorded_WIs':wis,'source_role_supported':okay,'original_TDoc_column_rows':matches})
    missing=json.loads((case/'actual_full_retained_width6_8_missing_earlier_frontier_source_scope.json').read_text()); missingwis=sorted({r['workItemCode'] for ca in missing['cases'] for pp in ca['missing_literal_paths'] for r in pp['WI_company_roles']})
    must(not set(missingwis)&set(first),'width6_8 missing enters originalfirst5')
    con.close(); dbafter=pin(db,root);must(dbbefore==dbafter,'immutable database changed')
    out={'id':'RAN2_P2_CQ3-3','status':'ACTUAL_RECORDED_OPERATIONAL_FRONTIER_AUDIT','database':dbbefore,'immutable_database_unchanged':True,'original_query':json.loads((case/'original.json').read_text())['cypher'],'paths_SQL':q,'full_recorded_scope':{'Resolution_n':len(res),'path_n':len(paths),'WI_n':len(codes),'WI_company_groups_n':len(group_rows)},'authored_7digit_reference_equivalence':{'expected_existing_target_pairs_n':len(expected),'actual_pairs_n':len(actual),'missing':sorted(expected-actual),'extra':sorted(actual-expected),'historical_generator_binding_claimed':False},'first5':first,'first5_dependency':{'Resolution_n':len(rids),'path_n':len(dep),'Tdoc_n':len(tids),'WI_company_groups_n':sum(x['workItemCode'] in first for x in group_rows),'full_content_source_cases':source_cases,'original_registers':workbooks,'all_Tdoc_roles':roles,'role_failure_n':len(failures),'role_failures':failures},'full_group_population':group_rows,'generalized_6_8_digit_nonliteral_paths':nonliteral,'generalized_6_8_digit_missing_earlier_pairs':{'pairs':missing['missing_literal_id_pairs'],'Resolution_n':missing['missing_resolution_n'],'WI_codes':missingwis,'all_matched_source_spans_after_first_Annex':all(m['after_first_Annex'] for ca in missing['cases'] for m in ca['own_source_matches']),'any_original_first5_affected':False,'interpretation':'Diagnostic alternatives, not authored7digit proxy or native gold. All listed WI codes sort after the original fifth WI.'},'limits':['Source fidelity is full retained text for the complete first5 dependency, not every physical paragraph in all reports.','Recorded citation/reference incidence is not causal technological leadership, approval, normative incorporation, or exclusive authorship.','No hardcoded Tdoc/WI/company exclusions or first-header truncation.','Parser INDEX source is prior rule evidence, not established historical generator provenance.','Current package and v4 native/scorers are preserved; this is a new candidate evidence audit, not admission.'],'API_calls':0,'native_calls':0,'new_gold':False,'public_change':False}
    a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'path':a.output.resolve().relative_to(root).as_posix(),'bytes':a.output.stat().st_size,'sha256':sha(a.output.read_bytes()),'first5':first,'source_dependencies':len(source_cases),'Tdoc_roles':len(roles),'role_failures':len(failures)}))

if __name__=='__main__':main()
