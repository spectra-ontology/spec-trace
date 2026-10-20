#!/usr/bin/env python3
"""Offline finite witnesses for two sealed bounded frozen-data judgments."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Run without -O/-OO')
import collections
import decimal
import gzip
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import stat
import unicodedata
import xml.etree.ElementTree as ET
from zipfile import ZipFile

PACKAGE_ROOT = Path(__file__).absolute().parent
INVENTORY_SHA256 = 'b1d540ae07642a4950567bfc511308a2a77b222ebb8745cfa35fe8d9a1f8f212'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
R2_ID = 'RAN2_P3_CQ5-3'
R3_ID = 'RAN3_P4_CQ2-3'
QUESTION_SHA = {R2_ID:'17e2bd7058d434f51fcef2f6ae700f31b79ff4a792968de93d82e51f3c02f9de',R3_ID:'7ee81e701ed56f165725186000a3ce6ca09c409a7353a50bdbbd3aa208bb8fcb'}
QUERY_SHA = {R2_ID:'8a353b2881c4fc96bed7c8c4db6cbb26a6acc50ce330f10ffce9e5fdc806ba28',R3_ID:'73a9e415c6f7bfa2817e9e92d768305d7dd517edd05ff4a6328d539edb3bc613'}
EXPECTED_SUBTYPES = {R2_ID:'missing_source_section_role',R3_ID:'missing_incoming_spec_role'}
META = {'inventory.json','manifest.json','reproduce.py'}

def require(condition, message):
    if not condition: raise RuntimeError(message)

def sha(raw): return hashlib.sha256(raw).hexdigest()
def unique(pairs):
    result={}
    for key,value in pairs:
        require(key not in result,'Duplicate JSON key')
        result[key]=value
    return result
def parse(raw):
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def no_links(path):
    p=Path(path).absolute()
    for part in (p,*p.parents):
        require(not part.is_symlink(),'Symlink prohibited')
    return p
def safe(name):
    require(type(name)is str and not Path(name).is_absolute() and '..'not in Path(name).parts,'Unsafe package path')
    path=no_links(PACKAGE_ROOT/name)
    require(stat.S_ISREG(path.stat().st_mode),'Expected regular included file')
    return path
def raw(name): return safe(name).read_bytes()
def data(name):
    b=raw(name)
    return parse(gzip.decompress(b) if name.endswith('.gz') else b)
def norm(value):
    return ''.join(c for c in unicodedata.normalize('NFKC',str(value)).casefold() if c.isalnum())
def nested(value):
    if type(value)is str: yield value
    elif type(value)is dict:
        for x in value.values():yield from nested(x)
    elif type(value)is list:
        for x in value:yield from nested(x)
def text(el):
    if el.tag in {W+'del',W+'moveFrom'}:return ''
    if el.tag in {W+'t',W+'delText'}:return el.text or ''
    if el.tag==W+'tab':return '\t'
    if el.tag in {W+'br',W+'cr'}:return '\n'
    return ''.join(text(child)for child in el)
def positive_flags(el):
    if el is None:return []
    return [x.tag for x in el.iter()if x.tag in {W+'strike',W+'dstrike',W+'vanish',W+'webHidden'} and x.get(W+'val','1').casefold()not in {'0','false','off','no'}]
def typed_record(row):
    return tuple((k,type(v).__name__,v)for k,v in sorted(row.items()))

def integrity():
    no_links(__file__);no_links(PACKAGE_ROOT)
    for path in PACKAGE_ROOT.rglob('*'):
        no_links(path)
        require(path.is_dir()or stat.S_ISREG(path.stat().st_mode),'Nonregular package entry')
    invraw=raw('inventory.json')
    require(sha(invraw)==INVENTORY_SHA256,'Immutable inventory mismatch')
    inv=parse(invraw)
    require(type(inv)is dict and set(inv)=={'files','excluded_metadata'},'Inventory schema')
    require(inv['excluded_metadata']==sorted(META),'Exact metadata exclusions')
    expected=set(inv['files'])|META
    actual={str(p.relative_to(PACKAGE_ROOT))for p in PACKAGE_ROOT.rglob('*')if p.is_file()}
    require(actual==expected,'Closed file inventory mismatch')
    for name,pin in inv['files'].items():
        b=raw(name)
        require(type(pin)is dict and set(pin)=={'sha256','bytes'} and type(pin['bytes'])is int and pin['bytes']>=0,'Pin schema')
        require(len(b)==pin['bytes']and sha(b)==pin['sha256'],'Included bytes mismatch: '+name)
    m=data('manifest.json')
    require(set(m)=={'artifact_type','classification','new_admissions','human_expert_validation_n','cases','inventory_sha256','reproduce_sha256','included_files','limits'},'Manifest keys')
    require(m['artifact_type']=='bounded_structural_source_loss_evidence'and m['classification']=='unsupported_frozen_data','Manifest scope')
    require(type(m['new_admissions'])is int and m['new_admissions']==0,'No admission')
    require(type(m['human_expert_validation_n'])is int and m['human_expert_validation_n']==0,'No human expert claim')
    require(m['inventory_sha256']==INVENTORY_SHA256 and m['reproduce_sha256']==sha(raw('reproduce.py')),'Metadata pins')
    require(type(m['included_files'])is int and m['included_files']==len(actual),'File count')
    require(m['cases']==[{'id':i,'subtype':EXPECTED_SUBTYPES[i]}for i in [R2_ID,R3_ID]],'Exact cases')
    require(m['limits']==[
        'Finite original frozen-release support loss; not intrinsic or permanent impossibility.',
        'No source-enriched experiment is admitted as an original frozen pass.',
        'Fresh package replay reads included source bytes and finite frozen projections only; it does not reload a full graph, rerun native, or repeat historical all-property scans.',
        'The RAN2 seven-role arithmetic is conditional on the retained numerator, not corrected technical gold or full1506 source certification.',
        'RAN3 complete first10 frontier is within19974 captured CR identities, not all historical or physical submissions.',
        'Original human expert validation count is zero; the two reviews are nonblind AI development judgments.'
    ],'Limitations changed')
    require(sha(raw('common/criteria.json'))=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4','Original criteria')
    for folder,ident in [('RAN2',R2_ID),('RAN3',R3_ID)]:
        require(sha(raw(folder+'/original_question.txt'))==QUESTION_SHA[ident],'Original question changed')
        require(sha(raw(folder+'/original_query.cypher'))==QUERY_SHA[ident],'Original query changed')
        original=data(folder+'/original_row.json')
        require(original['id']==ident and original['question_en'].encode()==raw(folder+'/original_question.txt')and original['cypher'].encode()==raw(folder+'/original_query.cypher'),'Original row binding')
        primary=data(folder+'/judgments/primary.json');root=data(folder+'/judgments/ROOT_seven_units.json');final=data(folder+'/judgments/ROOT_final.json')
        require(primary['id']==root['id']==final['id']==ident,'Judgment identity')
        require(root['decision']==final['local_recommendation']=='unsupported_frozen_data','Sealed disposition')
        require(len(root['semantic_units'])==7,'Exact seven units')
        require(root.get('human_expert_validation_n',root.get('expert_validation_n'))==0,'Expert zero')
    return m

def r2_source():
    source=data('RAN2/source/own_seven_source_witnesses.json')
    expected={v['name']:v for v in source}
    require(len(expected)==7,'Seven own source roles')
    style_xml=None
    with ZipFile(safe('RAN2/source/38331-j20.docx'))as archive:
        style_xml=archive.read('word/styles.xml')
        styles=ET.fromstring(style_xml)
        stylemap={s.get(W+'styleId'):s for s in styles.findall(W+'style')}
        stream=archive.open('word/document.xml')
        stack=[];ordinal=0;observed={};all_heading_names=set()
        require(not positive_flags(styles.find(W+'docDefaults')),'Style defaults active formatting')
        def style_chain(sid):
            result=[];seen=set()
            while sid:
                require(sid in stylemap and sid not in seen,'Style chain missing/cyclic')
                seen.add(sid);s=stylemap[sid];result.append(s)
                base=s.find(W+'basedOn');sid=None if base is None else base.get(W+'val')
            return result
        with stream:
            for event,el in ET.iterparse(stream,events=('start','end')):
                if event=='start':stack.append(el);continue
                if len(stack)>1 and stack[-2].tag==W+'body':
                    if el.tag==W+'p':
                        pstyle=el.find(W+'pPr/'+W+'pStyle')
                        sid=None if pstyle is None else pstyle.get(W+'val')
                        style_name=stylemap[sid].find(W+'name').get(W+'val')if sid in stylemap else None
                        value=text(el)
                        if style_name and style_name.casefold().replace(' ','')=='heading4':
                            name=re.sub(r'^[\s–—−-]+','',value).strip();all_heading_names.add(name)
                            if name in expected:
                                require(ordinal==expected[name]['body_child_zero_based']and value==expected[name]['text'],'Own heading locator/text')
                                require(not positive_flags(el)and not list(el.iter(W+'del'))and not list(el.iter(W+'moveFrom')),'Active source heading')
                                ids=[sid]+[s.get(W+'styleId')for s in styles.findall(W+'style')if s.get(W+'default')=='1']
                                ids += [s.get(W+'val')for s in el.iter(W+'rStyle')]
                                for i in ids:
                                    for s in style_chain(i): require(not positive_flags(s),'Inherited hidden/strike property')
                                observed[name]=ordinal
                    ordinal+=1;stack[-2].remove(el);el.clear()
                stack.pop()
    require(set(observed)==set(expected),'All seven reopened')
    return expected,all_heading_names

def r2_case():
    names,heading_names=r2_source()
    projection=data('RAN2/frozen/dependency.json.gz')
    specs={r['node_id']:r for r in projection['Spec']}
    sections=projection['Section'];section_ids={r['sectionId']for r in sections}
    for name in names:
        require(not any(norm(r['sectionNumber'])==norm(name)or r['sectionId']==names[name]['sectionId']for r in sections),'Unexpected retained Section role')
    source_product=data('RAN2/source/reused1506_source_product.json.gz')
    retained_own={r['sectionId']for r in sections if r['sectionId'].startswith('38.331-Rel-19-')}
    product_own={r['sectionId']for r in source_product['sections']}
    require(len(retained_own)==1499 and len(product_own)==1506,'Finite product sizes')
    require(product_own-retained_own=={x['sectionId']for x in names.values()}and not(retained_own-product_own),'1506 conditional delta')
    rrc=projection['RRCParameter_own_parent']
    existing={r['sectionNumber']for r in sections if r['sectionId'].startswith('38.331-Rel-19-')}
    candidates=[r for r in rrc if r['ieName']not in existing]
    require(len(rrc)==2171 and len(candidates)==1839,'Retained candidate pool')
    fine=[r for r in candidates if r['granularity']=='item'and r['release']is None and r['ieKind']in {'BIT','INTEGER','CHOICE','ENUMERATED'}and '-'in r['ieName']and r['parentSectionId']=='38.331-Rel-19-6.3.2']
    positives={r['ieName']for r in fine if r['ieName']in heading_names}
    require(len(fine)==52 and positives==set(names),'Finer retained-field alternative counterexample')
    exact=data('RAN2/frozen/exact_names_and_all_incident_edges.json')
    require(set(exact)==set(names),'Exact retained-name alternatives')
    for name,item in exact.items():
        require(len(item['records'])==1 and item['records'][0]['labels']==['RRCParameter'],'Exact names only survive as RRCParameter')
        require(len(item['incident'])==1 and item['incident'][0]['edge']['rel_type']=='definedInSection'and item['incident'][0]['neighbor']['properties']['sectionId']=='38.331-Rel-19-6.3.2','Parent link is not own Heading4 role')
    crcounts=collections.Counter(e['dst_id']for e in projection['CR_MODIFIES_hub_paths'])
    releases=collections.defaultdict(list)
    for edge in projection['IN_RELEASE_OF']: releases[edge['dst_id']].append(specs[edge['src_id']])
    seccounts=collections.Counter(e['dst_id']for e in projection['Section_BELONGS_TO_SPEC_paths'])
    pool=[]
    for nid,numerator in crcounts.items():
        rs=releases[nid]
        if not rs:continue
        rs=sorted(rs,key=lambda s:int(s['specRelease'].replace('Rel-','')),reverse=True)
        maximum=int(rs[0]['specRelease'].replace('Rel-',''))
        require(sum(int(x['specRelease'].replace('Rel-',''))==maximum for x in rs)==1,'Latest edition tie')
        denominator=seccounts[rs[0]['node_id']]
        if denominator==0:continue
        density=(decimal.Decimal(numerator)/denominator).quantize(decimal.Decimal('.01'),rounding=decimal.ROUND_HALF_UP)
        pool.append({'specNumber':specs[nid]['specNumber'],'crCnt':numerator,'secCnt':denominator,'density':float(density)})
    pool.sort(key=lambda x:x['density'],reverse=True)
    saved=data('RAN2/history/actual_full_original_metric_and_saved_native_typed_agreement.json')
    require(len(crcounts)==72 and len(pool)==14,'Full metric dependency')
    require(collections.Counter(map(typed_record,pool[:5]))==collections.Counter(map(typed_record,saved['selected_native5_full4_columns'])),'Historical native5 typed equality')
    target=next(r for r in pool if r['specNumber']=='38.331')
    require(target=={'specNumber':'38.331','crCnt':10599,'secCnt':1499,'density':7.07},'Necessary selected metric')
    require(sum(r['density']>target['density']for r in pool)==3 and pool[4]['density']==3.31,'Required top5 frontier')
    changed=(decimal.Decimal(10599)/1506).quantize(decimal.Decimal('.01'),rounding=decimal.ROUND_HALF_UP)
    require(changed==decimal.Decimal('7.04'),'Seven-role conditional arithmetic')
    require(saved['semantic_source_gold_certified']is False,'No corrected gold certification')
    return {'id':R2_ID,'classification':'unsupported_frozen_data','subtype':EXPECTED_SUBTYPES[R2_ID],
        'reopened_source_heading_roles':7,'retained_Section_role_matches':0,'retained_RRCParameter_names':7,
        'conditional_source_product':[1499,1506],'required_density_before':'7.07','seven_role_conditional_density':'7.04',
        'full_metric_rows':14,'historical_native_rows_recompared':5,'finer_recovery_candidates':52,'false_roles':45}

def r3_cover(observation):
    archive=safe('RAN3/source/archives/'+Path(observation['archive']).name)
    with ZipFile(archive)as outer:
        info=outer.getinfo(observation['member']);body=outer.read(info)
    require(sha(body)==observation['member_sha256'],'Own cover member bytes')
    with ZipFile(BytesIO(body))as inner:
        xml=inner.read('word/document.xml');style_xml=inner.read('word/styles.xml')
    require(sha(xml)==observation['document_xml_sha256']and sha(style_xml)==observation['styles_xml_sha256'],'Own XML/styles')
    doc=ET.fromstring(xml);styles=ET.fromstring(style_xml);b=doc.find(W+'body')
    stylemap={s.get(W+'styleId'):s for s in styles.findall(W+'style')}
    default=next((sid for sid,s in stylemap.items()if s.get(W+'type')=='paragraph'and s.get(W+'default')in {'1','true'}),None)
    defaults=styles.find(W+'docDefaults/'+W+'rPrDefault/'+W+'rPr')
    parents={c:p for p in doc.iter()for c in p}
    def chain(sid):
        seen=set();res=[]
        while sid:
            require(sid in stylemap and sid not in seen,'Cover style chain')
            seen.add(sid);s=stylemap[sid];res.append(s)
            base=s.find(W+'basedOn');sid=None if base is None else base.get(W+'val')
        return res
    def active(cell):
        for p in cell.iter(W+'p'):
            ps=p.find(W+'pPr/'+W+'pStyle');pchain=chain(ps.get(W+'val')if ps is not None else default)
            for r in p.iter(W+'r'):
                rs=r.find(W+'rPr/'+W+'rStyle');rchain=[]if rs is None else chain(rs.get(W+'val'))
                applied=[defaults]+[s.find(W+'rPr')for s in pchain+rchain]+[r.find(W+'rPr')]
                require(not any(positive_flags(x)for x in applied),'Cover hidden/strike')
                current=r
                while current in parents:
                    current=parents[current];require(current.tag not in {W+'del',W+'moveFrom'},'Cover deleted ancestor')
    first_table=next(i for i,e in enumerate(b)if e.tag==W+'tbl')
    header='\n'.join(text(e)for e in list(b)[:first_table]if e.tag==W+'p')
    require(sorted(set(re.findall(r'R3-\d{6}(?!\d)',header)))==[observation['tdocNumber']],'Own physical cover ID')
    found=[]
    for role in observation['affected_roles']:
        cells=b.findall(W+'tbl')[role['table_index']].findall(W+'tr')[role['row_index']].findall(W+'tc')
        values=['\n'.join(text(p)for p in c.iter(W+'p'))for c in cells];col=role['label_column']
        require(values[col+1]==role['active_value']and values[col-2].strip()==role['active_yes_checkbox']and values[col-1].strip()==role['active_no_checkbox'],'Own role locator/value')
        for j in [col-2,col-1,col+1]:active(cells[j])
        positive=bool(re.search(r'(?<!\d)38\s*\.\s*473(?!\d|[-.]\d)',values[col+1]))
        if positive:require(values[col-2].strip().lower()=='x'and values[col-1].strip().lower()!='x','Role YES')
        found.append({'role':role['role'],'positive':positive})
    return {'id':observation['tdocNumber'],'positive':any(x['positive']for x in found),'role_n':len(found),'body':b}

def r3_case():
    projection=data('RAN3/frozen/dependency.json.gz')
    all_ids=projection['all19974_CR_identities']
    require(len(all_ids)==19974 and len({r['tdocNumber']for r in all_ids})==19974,'Captured CR identity universe')
    pool=projection['all353_target_paths'];require(len(pool)==353,'Full original path pool')
    pool=sorted(pool,key=lambda r:r['tdocNumber'],reverse=True);cutoff=pool[9]['tdocNumber']
    frontier=sorted((r['tdocNumber']for r in all_ids if r['tdocNumber']>=cutoff),reverse=True)
    observations=data('RAN3/source/all38_own_cover_observations.json.gz')['observations']
    require(frontier==sorted((r['tdocNumber']for r in observations),reverse=True)and len(frontier)==38,'Complete possible entrant frontier')
    covers=[r3_cover(x)for x in observations]
    require(sum(x['role_n']for x in covers)==114,'All role fields')
    source10=sorted((r['id']for r in covers if r['positive']),reverse=True)[:10]
    frozen10=[r['tdocNumber']for r in pool[:10]]
    require(source10[-1]=='R3-260686'and frozen10[-1]=='R3-260681'and source10[:9]==frozen10[:9],'Necessary source/frozen first10 difference')
    witness=projection['witness']
    require(len(witness['identity_nodes'])==len(witness['normalized_alias_nodes'])==1,'Retained own identity/alias')
    node=witness['identity_nodes'][0];props=parse(node['properties_json'])
    require(props['tdocNumber']=='R3-260686','Witness ID')
    relations={'AFFECTS_CORE_SPEC','AFFECTS_TEST_SPEC','AFFECTS_OM_SPEC'}
    edges=witness['all_incident_edges']
    require(len(edges)==4 and not any(e['rel_type']in relations for e in edges),'No retained own affected-role edge')
    require(not any('38.473'in s for s in nested(props)),'No own alternative affected-spec field')
    require(sorted(e['rel_type']for e in edges)==['BELONGS_TO_CR_PACK','HAS_CR','MODIFIED_BY_CR','MODIFIES_SECTION'],'Retained other roles')
    require(len(witness['same_long_payload_other_nodes'])==0,'Other payload role alternatives')
    cover=next(x for x in covers if x['id']=='R3-260686')
    form=cover['body'].findall(W+'tbl')[0].findall(W+'tr')[3]
    formtext=' '.join(text(c)for c in form.findall(W+'tc'))
    require('38.423'in formtext and '1668'in formtext and '19.1.0'in formtext,'Own form versus affected-spec role')
    for field,index in [('reasonForChange',11),('summaryOfChange',13),('consequencesIfNotApproved',15)]:
        cells=cover['body'].findall(W+'tbl')[2].findall(W+'tr')[index].findall(W+'tc')
        value='\n'.join(text(p)for p in cells[-1].iter(W+'p'))
        require(' '.join(value.split())==' '.join(props[field].split()),'Positive own payload equality: '+field)
    history=data('RAN3/history/actual_source_and_all_retained_alternatives.json')
    require(history['source_selected10']==source10 and history['frozen_selected10']==frozen10,'Historical source/frozen prefix')
    return {'id':R3_ID,'classification':'unsupported_frozen_data','subtype':EXPECTED_SUBTYPES[R3_ID],
        'raw_own_covers':38,'raw_role_fields':114,'captured_CR_identity_universe':19974,'original_path_pool':353,
        'necessary_identity':'R3-260686','source_first10':source10,'frozen_first10':frozen10,
        'positive_own_metadata_equal_fields':3,'retained_incident_edges':4,
        'historical_all_property_scan_repeated':False}

def main():
    integrity()
    cases=[r2_case(),r3_case()]
    print(json.dumps({'status':'PASS','cases':cases,'new_admissions':0},ensure_ascii=False))
if __name__=='__main__':main()

