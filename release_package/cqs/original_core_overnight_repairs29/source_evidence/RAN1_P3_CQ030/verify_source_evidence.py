#!/usr/bin/env python3
"""Offline source snippets, saved native output and typed-reference replay.

No network, Neo4j, subprocess, model or private-path fallback is used. Optional
--source-root reopens only the15 explicitly pinned original DOCX files.
"""
import sys
if sys.flags.optimize:
    raise SystemExit('Run without -O/-OO; checks must remain enabled.')
import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
EXPECTED_INVENTORY_SHA = '3bdcccb51b2b35902aeff897969c5938b09153274c5b29234c29cfa8428f6160'
EXPECTED_MANIFEST = {'id': 'RAN1_P3_CQ030', 'artifact_type': 'prospective_original_question_source_and_reference_evidence', 'repair_sha256': '2ccf3cee24fd22978933c92b140fdbc30ec18536cdb04dd01284391b4d468667', 'criteria_sha256': 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'original_question_preserved': True, 'question_sha256': '8a1a11568bbde942a0c81fb2f3e728d16d486b6361433eb013d2d662501c6ecf', 'query_sha256': 'b443e46dd6c9577cb063094540a92fea56368f2711c8dd3e15280241dc75147d', 'source_members': 20, 'required_fields': 2, 'native_columns': 4, 'expert_validation_n': 0, 'new_model_calls': 0, 'new_native_runs': 0, 'original560_increment': 0, 'admitted': False, 'status': 'LOCAL_SOURCE_AND_REFERENCE_GATES_PASS_PENDING_ROOT_SEAL', 'readme_sha256': '8d9b56a0e9cbc461e4b7bb80b7b441b71a3569f1de354ee13a42718209b86f6f'}
META = {'manifest.json', 'immutable_payload_inventory.json', 'README.md', 'verify_source_evidence.py'}
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M='http://schemas.openxmlformats.org/officeDocument/2006/math'
NS={'w':W,'m':M}
ID='RAN1_P3_CQ030'

def no_links(path):
    p=Path(path).absolute()
    for x in [p,*p.parents]:
        if x.is_symlink(): raise ValueError('Symlink path prohibited: '+str(x))
    return p

ROOT=no_links(Path(__file__).absolute().parent)
no_links(Path(__file__).absolute())
def sha(data): return hashlib.sha256(data).hexdigest()
def canonical(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def same(a,b): return canonical(a)==canonical(b)
def read(name): return json.loads((ROOT/name).read_bytes())

def bootstrap():
    for p in ROOT.rglob('*'):
        no_links(p)
        if not (p.is_file() or p.is_dir()): raise ValueError('Nonregular entry')
    b=(ROOT/'immutable_payload_inventory.json').read_bytes()
    if sha(b)!=EXPECTED_INVENTORY_SHA: raise ValueError('Immutable inventory changed')
    inv=json.loads(b)
    actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()}
    if actual != set(inv)|META: raise ValueError('Closed file inventory mismatch')
    expected_dirs={str(Path(n).parent) for n in actual}
    expected_dirs |= {str(a) for n in actual for a in Path(n).parents}
    for p in ROOT.rglob('*'):
        if p.is_dir() and p.relative_to(ROOT).as_posix() not in expected_dirs:
            raise ValueError('Unexpected directory')
    for name,pin in inv.items():
        raw=(ROOT/name).read_bytes()
        if len(raw)!=pin['bytes'] or sha(raw)!=pin['sha256']: raise ValueError('Payload changed: '+name)
    manifest=read('manifest.json')
    actual_meta={k:v for k,v in manifest.items() if k!='files'}
    if not same(actual_meta,EXPECTED_MANIFEST): raise ValueError('Metadata claims changed')
    if sha((ROOT/'README.md').read_bytes())!=manifest['readme_sha256']: raise ValueError('README changed')
    expected={**inv, 'immutable_payload_inventory.json':{'bytes':len(b),'sha256':sha(b)},
        'README.md':{'bytes':(ROOT/'README.md').stat().st_size,'sha256':sha((ROOT/'README.md').read_bytes())},
        'verify_source_evidence.py':{'bytes':Path(__file__).stat().st_size,'sha256':sha(Path(__file__).read_bytes())}}
    if not same(manifest['files'],expected): raise ValueError('Outer map changed')
    return manifest

def mod(name,path):
    s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def text(node): return ''.join(e.text or '' for e in node.iter() if e.tag in {'{'+W+'}t','{'+M+'}t'})
def tree(node):
    return [node.tag,sorted(node.attrib.items()),node.text or '',[[tree(c),c.tail or ''] for c in node]]

def verify_source_snippets(data,source_root=None):
    sources=data['sources']
    assert len(sources)==15
    lookup={(s['specNumber'],s['specRelease']):s for s in sources}
    assert len(lookup)==15
    assert set(lookup)=={(sp,'Rel-'+str(r)) for sp in ['38.211','38.212','38.214'] for r in range(15,20)}
    n=0
    for s in sources:
        ps=s['paragraphs']; roles={}
        assert len({p['paragraph_all_w_p0'] for p in ps})==len(ps)
        stylemap={}
        for xml in s['inspected_styles_xml']:
            el=ET.fromstring(xml);stylemap[el.get('{'+W+'}styleId')]=el
        assert set(stylemap)==set(s['style_ids_inspected'])
        for el in list(stylemap.values())+([ET.fromstring(s['docDefaults_xml'])] if s['docDefaults_xml'] else []):
            assert not any(e.tag in {'{'+W+'}strike','{'+W+'}dstrike','{'+W+'}vanish'} for e in el.iter())
            base=el.find('w:basedOn',NS)
            if base is not None: assert base.get('{'+W+'}val') in stylemap
        for p in ps:
            raw=p['xml_utf8'].encode();assert sha(raw)==p['xml_utf8_sha256']
            el=ET.fromstring(raw);assert text(el)==p['text_w_t_plus_m_t']
            assert not any(e.tag in {'{'+W+'}strike','{'+W+'}dstrike','{'+W+'}vanish','{'+W+'}del','{'+W+'}moveFrom'} for e in el.iter())
            for e in el.iter():
                if e.tag in {'{'+W+'}pStyle','{'+W+'}rStyle'}: assert e.get('{'+W+'}val') in stylemap
            for role in p['roles']: roles.setdefault(role,[]).append(p)
            n+=1
        assert {k:[p['paragraph_all_w_p0'] for p in v] for k,v in roles.items()}==s['selected_role_indices']
        def role(name):
            rows=roles[name];assert len(rows)==1;return rows[0]['text_w_t_plus_m_t']
        if s['specNumber']=='38.211':
            assert role('own_mapping_clause')=='7.4.1.5.3Mapping to physical resources'
            assert 'Tables 7.4.1.5.3-1' in role('physical_mapping_parameters_use_table1')
            assert 'CSI-ResourceConfig' in role('mapping_resource_setting_and_density')
            assert re.match(r'^Table\s+7\.4\.1\.5\.3-1\s*:',role('returned_table_caption_7.4.1.5.3-1'))
            if s['specRelease']=='Rel-19':
                assert '48, 64, 128' in role('48_64_128_aggregation_table6') and 'Table 7.4.1.5.3-6' in role('48_64_128_aggregation_table6')
                assert re.match(r'^Table\s+7\.4\.1\.5\.3-6\s*:',role('returned_table_caption_7.4.1.5.3-6'))
        elif s['specNumber']=='38.212':
            assert role('own_CSI_only_clause')=='6.3.1.1.2CSI only'
            for name in roles:
                if name.startswith(('returned_table_caption_','boundary_table_caption_')):
                    t=role(name);assert 'Mapping order of CSI fields' in t and 'CSI report' in t
        else:
            heading=role('actual_CSI_reporting_heading');assert heading=='5.2UE procedure for reporting channel state information (CSI)'
            r=role('reporting_resourceMapping_parameters_TS38211')
            assert 'resourceMapping defines the number of ports, CDM-type, and OFDM symbol and subcarrier occupancy' in r and '7.4.1.5' in r and '38.211' in r
            r=role('reporting_nrofPorts_TS38211');assert 'nrofPorts in resourceMapping defines the number of CSI-RS ports' in r and '38.211' in r
            r=role('reported_CSI_derived_from_NZP_CSI_RS_TS38211');assert 'computing CSI value reported' in r and 'NZP CSI-RS' in r and '38.211' in r
            if s['specRelease']=='Rel-19':
                r=role('codebook_48_64_128_CSI_RS_channel_measurement');assert 'For 48, 64 and 128 antenna ports' in r and 'aggregating K CSI-RS resources for channel measurement' in r
                r=role('codebook_port_index_TS38211_mapping_clause');assert '7.4.1.5.3' in r and '38.211' in r and 'port index' in r
        if source_root is not None:
            path=no_links(source_root/s['file']['path']);raw=path.read_bytes()
            assert len(raw)==s['file']['bytes'] and sha(raw)==s['file']['sha256']
            with zipfile.ZipFile(path) as z:
                doc=z.read('word/document.xml');sty=z.read('word/styles.xml')
                assert sha(doc)==s['document_xml_sha256'] and format(z.getinfo('word/document.xml').CRC,'08x')==s['document_xml_CRC32']
                assert sha(sty)==s['styles_xml_sha256']
            original_ps=ET.fromstring(doc).findall('.//w:p',NS)
            for p in ps: assert tree(original_ps[p['paragraph_all_w_p0']])==tree(ET.fromstring(p['xml_utf8']))
            original_styles={x.get('{'+W+'}styleId'):x for x in ET.fromstring(sty).findall('w:style',NS)}
            for sid,el in stylemap.items(): assert tree(original_styles[sid])==tree(el)
    assert n==72
    return {'sources':15,'own_paragraphs':n,'optional_original_DOCX_reopened':15 if source_root else 0}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-root',type=Path);args=parser.parse_args()
    manifest=bootstrap()
    definition=read('contract/definition.json');criteria=read('contract/criteria.json')
    repair=sha(canonical(definition).encode())
    assert len(definition)==9 and repair==manifest['repair_sha256'] and definition['id']==ID
    assert definition['original_question_preserved'] is True and definition['original_query']==definition['reference_query']
    assert definition['repair_class']=='scorer_only' and definition['collection']=={'kind':'multiset'}
    assert definition['cardinality_policy']=={'mode':'exact','value':20}
    assert [f['name'] for f in definition['required_fields']]==['specNumber','tableNumber']
    assert [f['source_column_or_expression'] for f in definition['required_fields']]==['sp.specNumber','tbl.tableNumber']
    schema=mod('cq030_review',ROOT/'runtime/review_schema.py')
    for name in ['primary','secondary']:
        review=read('contract/'+name+'.json')
        schema.check_pass(review,definition['question_en'],criteria['semantic_units'],
            criteria_sha=sha((ROOT/'contract/criteria.json').read_bytes()),identity_key='repair_sha256',identity_sha=repair)
    assert (ROOT/'contract/primary.json').read_bytes()!=(ROOT/'contract/secondary.json').read_bytes()
    native=read('native/receipt.json');execution=native['execution']
    assert native['id']==ID and native['original_question']==definition['question_en']
    assert native['reference_query_utf8_sha256']==execution['query_utf8_sha256']==sha(definition['reference_query'].encode())
    assert execution['status']=='OK' and execution['full_json_rows_available'] is True and execution['truncated'] is False
    assert execution['rollback_completed'] is True and execution['execution_summary_complete'] is True
    assert execution['execution_query_type']==execution['plan_query_type']=='r'
    assert execution['query_modified'] is False and execution['record_data_coercion_used'] is False
    raw=(ROOT/'native/rows.jsonl').read_bytes();assert sha(raw)==execution['rows_file_sha256']
    rows=[json.loads(l) for l in raw.splitlines() if l.strip()]
    assert len(rows)==execution['row_count_retained']==20
    cols=['sp.specNumber','tbl.tableNumber','tbl.tableCaption','sec.sectionNumber'];assert execution['columns']==cols
    assert all(type(r) is list and len(r)==4 and all(type(v) is str for v in r) for r in rows)
    run=read('native/run_report.json');frozen=read('native/frozen_manifest.json')
    assert run['frozen_manifest_sha256']==sha((ROOT/'native/frozen_manifest.json').read_bytes())
    assert run['source_inventory_unchanged'] is True and run['new_model_calls']==0 and type(run['new_model_calls']) is int
    item=[x for x in run['items'] if x['id']==ID];assert len(item)==1 and item[0]['status']=='OK' and item[0]['receipt_sha256']==sha((ROOT/'native/receipt.json').read_bytes())
    before=[x for x in run['source_guards_before'] if x['wg']=='RAN1'];after=[x for x in run['source_guards_after'] if x['wg']=='RAN1'];assert before==after and len(before)==1
    sourcepin=[x for x in frozen['graph_import_pins'] if x['wg']=='RAN1'];assert len(sourcepin)==1
    assert before[0]['source']['sha256']==sourcepin[0]['source_sha256']=='9540683df5407bb3f8978ad4d05ddc7f7880f10c94f21273f588d737f145e231'
    assert before[0]['nodes']==165418 and before[0]['relationships']==848228
    assert before[0]['import_manifest_sha256']==sourcepin[0]['sha256']
    pool=read('reference/full_pool_332.json')['rows'];assert len(pool)==332
    assert rows==[r[:4] for r in pool[:20]]
    assert all('csi' in r[2].lower() for r in pool)
    assert all(tuple(a[:2])<=tuple(b[:2]) for a,b in zip(pool,pool[1:]))
    strict=[r for r in pool if tuple(r[:2])<tuple(pool[19][:2])];boundary=[r for r in pool if tuple(r[:2])==tuple(pool[19][:2])]
    assert len(strict)==18 and len(boundary)==5
    gold=read('reference/requested_records.json');assert gold==[{'specNumber':r[0],'tableNumber':r[1]} for r in rows]
    for subset in itertools.combinations(boundary,2):
        assert Counter(canonical(r[:4]) for r in strict+list(subset))==Counter(canonical(r) for r in rows)
    scorer=mod('cq030_scorer',ROOT/'runtime/scorer.py')
    controls=read('reference/typed_controls.json')
    assert controls['repair_sha256']==repair and controls['n']==21
    # Reconstruct each saved control from its documented operation; outcomes are
    # recomputed rather than trusted from saved PASS flags.
    import copy
    preds={'exact':gold,'reverse_unrequested_order':list(reversed(gold)),
        'missing_row':gold[:-1],'extra_row':gold+[gold[0]],
        'deduplicated_unique_table_pairs':[dict(specNumber=a,tableNumber=b) for a,b in sorted({(r['specNumber'],r['tableNumber']) for r in gold})],
        'optional_caption_not_required':[dict(r,tableCaption='ignored optional annotation') for r in gold]}
    for f in ['specNumber','tableNumber']:
        for label,value in [('wrong_string','WRONG'),('wrong_integer_type',1),('null',None),('bool',True),('array',['wrong']),('object',{'wrong':1})]:
            p=copy.deepcopy(gold);p[0][f]=value;preds[f+'_'+label]=p
        p=copy.deepcopy(gold);del p[0][f];preds[f+'_missing_required']=p
    p=copy.deepcopy(gold);p[-1]=copy.deepcopy(gold[0]);preds['same_count_wrong_multiplicity']=p
    assert set(preds)=={x['name'] for x in controls['controls']}
    for c in controls['controls']:
        result=scorer.score(definition,gold,preds[c['name']],diagnostic=True)
        assert result==c['actual'] and result['exact'] is c['expected_exact']
    data=json.loads(gzip.decompress((ROOT/'source/own_paragraphs_and_styles.json.gz').read_bytes()))
    source_result=verify_source_snippets(data,no_links(args.source_root) if args.source_root else None)
    print(json.dumps({'status':'PASS','id':ID,'repair_sha256':repair,'native_rows':20,'native_columns':4,
        'required_fields':2,'frozen_pool':332,'boundary_combinations':10,'typed_controls':21,
        'source':source_result,'API_calls':0,'native_runs':0,'public_admissions':0}))

if __name__=='__main__': main()
