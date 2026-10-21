#!/usr/bin/env python3
"""Replay the included source/frozen/native/scoring bindings with stdlib only."""
import ast
from collections import defaultdict
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import types
import xml.etree.ElementTree as ET
import zipfile

MANIFEST_SHA256 = 'e82347b27a7142c5458e5483260a84f2d61fdd052e97a30c89dd54fcf2209461'
H = lambda value:hashlib.sha256(value).hexdigest()
N = lambda value:' '.join((value or '').split())
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def require(condition,message):
    if not condition:raise ValueError(message)


def load(root,name):
    path=root/name
    raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)


def display_cfb(text):
    stack=[];out=[];cpmap=[]
    for cp,char in enumerate(text):
        if char=='\x13':stack.append(False)
        elif char=='\x14':require(bool(stack),'unpaired field separator');stack[-1]=True
        elif char=='\x15':require(bool(stack),'unpaired field end');stack.pop()
        elif all(stack):out.append(char);cpmap.append(cp)
    require(not stack,'unclosed field')
    return ''.join(out),cpmap


def literal(element):
    return ''.join((x.text or '') if x.tag in {W+'t',W+'delText'} else '\t' if x.tag==W+'tab' else '\n' if x.tag in {W+'br',W+'cr'} else '' for x in element.iter())


def parsed_original(raw,reader):
    if raw.startswith(b'PK'):
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:root=ET.fromstring(archive.read('word/document.xml'))
        return [literal(p) for p in root.iter(W+'p')],root,None
    text,_,_=reader.parse_doc(raw)
    display,_=display_cfb(text)
    return [m.group().rstrip('\r') for m in re.finditer(r'[^\r]*\r|[^\r]+$',display)],None,text


def pure_module(root,filename,environment=None):
    """Load only original pure recognizer definitions and regex assignments."""
    tree=ast.parse((root/'readers'/filename).read_text())
    selected=[]
    for statement in tree.body:
        if isinstance(statement,ast.FunctionDef) and statement.name!='main':selected.append(statement)
        elif isinstance(statement,ast.Assign) and all(isinstance(t,ast.Name) for t in statement.targets):
            names={t.id for t in statement.targets}
            if names <= {'HEADER','DECISION','POSITIVE','ACTION','CAUSE','QUANTITY','ACRONYM','CHANGE','SAME','REUSE','Q_SPEC','TIMING','RATIO','INTERRUPT','CONDITIONAL_PROCESSING'}:
                selected.append(statement)
    env={'re':re}
    env.update(environment or {})
    exec(compile(ast.Module(body=selected,type_ignores=[]),filename,'exec'),env)
    return types.SimpleNamespace(**env)


def replay_frozen(root,frozen):
    old=pure_module(root,'probe_generic_current_amendment_rule_v3.py')
    quant=pure_module(root,'probe_quantitative_usage_current_amendment_candidate_v2.py',{'g':old})
    grammar=pure_module(root,'probe_earlier_retained_grammar_extensions_v2.py',{'old':old})
    extra=pure_module(root,'probe_generic_current_amendment_rule_v5.py',{'old':old,'gramm':grammar})
    processing=pure_module(root,'probe_generic_current_amendment_rule_v6.py',{'old':old})
    meetings={row['node_id']:row for row in frozen['Meeting']}
    cr_by_id={row['node_id']:row for row in frozen['CR_reason_nonnull']}
    agreements={row['node_id']:row for row in frozen['Agreement']}
    rels=frozen['relationships'];by_meeting=defaultdict(list);agreement_meetings=defaultdict(list)
    for edge in rels['rel_PRESENTED_AT']:
        if edge['src_id'] in cr_by_id:
            value=dict(cr_by_id[edge['src_id']],meeting_id=edge['dst_id'])
            by_meeting[edge['dst_id']].append(value)
    for edge in rels['rel_MADE_AT']:
        if edge['src_id'] in agreements:agreement_meetings[edge['src_id']].append(edge['dst_id'])
    agendas=defaultdict(list);by_agenda=defaultdict(list)
    for edge in rels['rel_RESOLUTION_BELONGS_TO']:
        if edge['src_id'] in agreements:
            agendas[edge['src_id']].append(edge['dst_id']);by_agenda[edge['dst_id']].append(agreements[edge['src_id']])
    specs=defaultdict(set);sections=defaultdict(list)
    for row in frozen['modified_specs']:specs[row['src_id']].add(row['specNumber'])
    for row in frozen['modified_sections']:sections[row['src_id']].append({'sectionTitle':row['sectionTitle']})
    # Pure function bodies above resolve globals in their original namespaces.
    # Cache only technical-line extraction, preserving each returned pair.
    old_lines=old.technical_lines
    cache={row['node_id']:old_lines(row) for row in agreements.values()}
    for function in [old.operative_matches,quant.candidate,grammar.matches,extra.extra,processing.roles]:
        dependency=function.__globals__.get('old',function.__globals__.get('g'))
        if dependency is not None:dependency.technical_lines=lambda a:cache[a['node_id']]
    old.operative_matches.__globals__['technical_lines']=lambda a:cache[a['node_id']]
    matched={};paths=[]
    for a in agreements.values():
        for meeting_id in agreement_meetings[a['node_id']]:
            for cr in by_meeting[meeting_id]:
                roles=(old.operative_matches(a,cr,meetings[meeting_id]['meetingNumberInt'])
                       +quant.candidate(a,cr)+grammar.matches(a,cr,specs[cr['node_id']])
                       +extra.extra(a,cr,sections[cr['node_id']])+processing.roles(a,cr))
                if roles:matched[cr['node_id']]=cr;paths.append((a['resolutionId'],cr['tdocNumber']))
            for agenda_id in agendas[a['node_id']]:
                for previous in by_agenda[agenda_id]:
                    if previous['sequence']!=a['sequence']-1:continue
                    lines=old.retained_body(previous).splitlines()
                    headers=[(i,old.HEADER.match(line))for i,line in enumerate(lines)if old.HEADER.match(line)]
                    if not headers:continue
                    index,header=headers[-1]
                    current=old.retained_body(a).splitlines()
                    decisions=[(i,line)for i,line in enumerate(current)if old.DECISION.match(line)]
                    if any(old.DECISION.match(line)for line in lines[index+1:]) or not decisions:continue
                    di,decision=decisions[0]
                    if not old.POSITIVE.match(decision) or any(old.HEADER.match(line)for line in current[:di]):continue
                    for cr in by_meeting[meeting_id]:
                        if cr['tdocNumber']==header.group(1):matched[cr['node_id']]=cr;paths.append((a['resolutionId'],cr['tdocNumber']))
    full=[{'tdocNumber':cr['tdocNumber'],'reason':cr['reasonForChange'],'summary':cr['summaryOfChange']}
          for cr in sorted(matched.values(),key=lambda row:row['tdocNumber'])]
    return full,paths,cr_by_id,agreements,agreement_meetings


def verify(root):
    manifest_path=root/'payload_manifest.json'
    require(H(manifest_path.read_bytes())==MANIFEST_SHA256,'payload manifest identity')
    manifest=load(root,'payload_manifest.json')
    require(manifest['schema']==1 and manifest['id']=='RAN4_P4_CQ4-2','package schema/id')
    for row in manifest['files']:
        path=(root/row['path']).resolve()
        require(path.is_relative_to(root.resolve()),'unsafe member path')
        raw=path.read_bytes()
        require(len(raw)==row['bytes'] and H(raw)==row['sha256'],'payload byte identity '+row['path'])
    original=load(root,'contract/original.json');definition=load(root,'contract/definition.json')
    require(original['id']==definition['id']==manifest['id'],'original identity')
    require(definition['question_en']==original['question_en'] and definition['original_query']==original['cypher'],'original question/query')
    require([f['name']for f in definition['required_fields']]==['tdocNumber','reason','summary'],'requested field roles')
    require(definition['collection']=={'kind':'top_k_boundary_ties','value':5,'source_order_keys':[{'source_column':'tdocNumber','direction':'asc'}],'tie_policy':'any_subset_at_boundary','within_tie_order':'any','require_rank_order':False},'original collection')
    limited_query=(root/'native/limited_reference.cypher').read_text()
    require(definition['reference_query']==limited_query,'definition/native query binding')
    require(json.dumps(definition,ensure_ascii=False,separators=(',',':'),sort_keys=True).encode()==(root/'contract/canonical_repair.json').read_bytes(),'canonical definition')
    criteria=load(root,'contract/criteria.json')
    require(H((root/'contract/criteria.json').read_bytes())=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4','fixed original seven criteria')
    secondary=load(root,'contract/secondary.json')
    require(len(secondary['semantic_units'])==7 and all(unit['ROOT_verdict']=='PASS' for unit in secondary['semantic_units']),'independent ROOT exact-seven source review')
    require(secondary['definition']['sha256']==H((root/'contract/definition.json').read_bytes()) and secondary['criteria']['sha256']==H((root/'contract/criteria.json').read_bytes()),'independent ROOT review contract binding')
    require(secondary['question_en_sha256']==H(original['question_en'].encode()),'independent review original question binding')
    primary=load(root,'contract/primary.json')
    require(len(primary['semantic_units'])==7 and all(unit['primary_verdict']=='PASS' for unit in primary['semantic_units']),'primary exact-seven review')
    expected_scoring={'scorer.py':'c6db2d2423e12e29f97746afdf9f22f143c948db89a4fe4dce14847e932ccdbd','original_scorer.py':'1af0744df717abafe8115d560ac2db695ebea8a4b7d2ee104736dabf233badeb','typed_values.py':'d7eee66cce2dabe3ef48c173e84fac47192266bdd3e8ce78214f8361df5161ba','source_pins.json':'a86fad1201ca0225a798d2f48a278fe66c58d326907d959772a6ea05f3266f92'}
    for name,digest in expected_scoring.items():require(H((root/'scoring'/name).read_bytes())==digest,'unchanged released scorer bytes '+name)
    frozen=load(root,'frozen/retained_projection.json.gz')
    require(len(frozen['Agreement'])==1905 and len(frozen['CR_reason_nonnull'])==12300,'whole retained input population')
    spec=importlib.util.spec_from_file_location('portable_D52_binary_reader',root/'readers/binary_reader_root_scoped_v2.py')
    reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    cr_by_tdoc={row['tdocNumber']:row for row in frozen['CR_reason_nonnull']}
    originals=load(root,'source/original34_manifest.json')
    cutoff=max(row['tdocNumber']for row in originals)
    prefix={td for td in cr_by_tdoc if td<=cutoff}
    require(prefix=={row['tdocNumber']for row in originals} and len(prefix)==34,'complete earliest source frontier')
    parsed={};cover_fields=0
    for source in originals:
        td=source['tdocNumber'];raw=gzip.decompress((root/source['local_member_gz']).read_bytes())
        require(H(raw)==source['member_sha256'] and len(raw)==source['member_bytes'],'original CR bytes '+td)
        paragraphs,xml,raw_text=parsed_original(raw,reader);parsed[td]=paragraphs
        require(len(paragraphs)==source['paragraph_count'],'original paragraph count '+td)
        require(H(json.dumps(paragraphs,ensure_ascii=False,separators=(',',':')).encode())==source['whole_original_display_paragraphs_sha256'],'whole original paragraph text '+td)
        require(len(source['source_cover_fields'])==2,'two requested source fields '+td)
        for field in source['source_cover_fields']:
            value=field.get('transcribed_value',field.get('raw_value'))
            require(field['frozen_value']==cr_by_tdoc[td][field['field']],'source/frozen field binding '+td)
            require(N(value)==N(field['frozen_value']),'source/frozen whitespace projection '+td)
            if xml is not None:
                rowxml=ET.fromstring(field['row_XML'])
                matching=[row for row in xml.iter(W+'tr')if ET.tostring(row,encoding='unicode')==ET.tostring(rowxml,encoding='unicode')]
                require(len(matching)==1,'exact original cover row '+td)
                cells=matching[0].findall(W+'tc')
                actual='\n'.join(literal(p)for p in cells[1].findall(W+'p')).strip()
                require(N(actual)==N(value),'original cover cell value '+td)
            else:
                require(raw_text[field['cp_start']:field['cp_end']]==field['raw_value'],'original cover CP slice '+td)
            cover_fields+=1
    source_caps=load(root,'source/evidence/negative26_focused_current_object_and_all110_act_text_NOT_gold_v2.json.gz')
    negatives=source_caps['26negative_focused_capsules']
    for row in negatives:
        for paragraph in row['exact_original_paragraph_locators']:
            require(parsed[row['tdocNumber']][paragraph.get('paragraph0',paragraph.get('index'))]==paragraph.get('text',paragraph.get('literal')),'negative current object source locator')
    role_matrix=load(root,'source/evidence/main_D_proposed_prefix34_current_role_matrix_NOT_gold_v2.json.gz')
    matrix=role_matrix['matrix']
    require({row['tdocNumber']for row in matrix}==prefix,'all source roles covered')
    positive={row['tdocNumber']for row in matrix if row['proposed_main_D_role'].startswith('POSITIVE')}
    negative={row['tdocNumber']for row in negatives}
    require(len(positive)==8 and len(negative)==26 and positive.isdisjoint(negative) and positive|negative==prefix,'8P26N source closure')

    act_caps=load(root,'source/evidence/all110_same_event_original_technical_act_capsules_NOT_gold_v1.json.gz')
    reports={}
    for meeting,pin in act_caps['report_source_pins'].items():
        raw=gzip.decompress((root/('source/reports/'+meeting+'.doc.gz')).read_bytes())
        require(H(raw)==pin['member_sha256'],'original report bytes '+meeting)
        reports[meeting]=reader.parse_doc(raw)[0]
    agreement_by_rid={row['resolutionId']:row for row in frozen['Agreement']}
    cp_slices=0
    for act in act_caps['acts']:
        a=agreement_by_rid[act['resolutionId']]
        require(H((a['contentWithEquations']or a['content']or'').encode())==act['retained_content_sha256'],'original/frozen Agreement role')
        require(a['note']==act['retained_note'],'own Agreement note')
        require(act['anchor_count']==len(act['original_source_windows']) and act['anchor_count']>0,'source own-act anchors')
        text=reports[act['original_report_meeting']]
        for window in act['original_source_windows']:
            for key in ['preceding_paragraphs','raw_own_act_through_first_decision_or_header']:
                for paragraph in window[key]:
                    require(H(text[paragraph['cp_start']:paragraph['cp_end']].encode())==paragraph['raw_CP_sha256'],'raw own-act CP slice')
                    cp_slices+=1
    require(len(act_caps['acts'])==110 and cp_slices==18940,'complete original event-act source binding')
    bridge=load(root,'source/evidence/actual_87_current_1subframe_reference_incorporation_NOT_gold_v1.json.gz')
    bridge_raw=gzip.decompress((root/'source/bridge_members/R4-1808471.doc.gz').read_bytes())
    require(H(bridge_raw)==bridge['new_interruption_CR_original_sha256'],'specific current normative bridge source')
    require(bridge['new_interruption_CR_frozen']['reasonForChange'] is None,'source-only null reason preserved')

    replay,paths,_,agreements,agreement_meetings=replay_frozen(root,frozen)
    native={}
    for kind in ['limited','full']:
        query=(root/('native/'+kind+'_reference.cypher')).read_bytes();digest=H(query)
        base='native/actual/reference_outputs/RAN4_P4_CQ4-2/'+digest
        meta=load(root,base+'.json');raw=(root/(base+'.jsonl')).read_bytes()
        require(meta['status']=='OK' and meta['full_rows_available'] and not meta['truncated'] and meta['rollback_completed'],'actual native read completed')
        require(meta['query_sha256']==digest and meta['query']==query.decode() and meta['rows_sha256']==H(raw),'native execution query/row binding')
        require(meta['columns']==['tdocNumber','reason','summary'],'native three columns')
        native[kind]=[dict(zip(meta['columns'],json.loads(line)))for line in raw.splitlines()]
        require(len(native[kind])==meta['rows_retained'],'native all rows retained')
    require(replay==native['full'],'whole frozen rule replay equals actual native full')
    require(native['limited']==native['full'][:5] and len(native['limited'])==5,'original native top5')
    require([row['tdocNumber']for row in native['limited']]==sorted(positive)[:5],'source and native selected membership')
    require({row['tdocNumber']for row in native['full']if row['tdocNumber']<=cutoff}==positive,'all prefix native/source roles agree')
    for row in native['full']:
        cr=cr_by_tdoc[row['tdocNumber']]
        require(row=={'tdocNumber':cr['tdocNumber'],'reason':cr['reasonForChange'],'summary':cr['summaryOfChange']},'native all named field source binding')
    sys.path.insert(0,str(root/'scoring'))
    spec=importlib.util.spec_from_file_location('portable_D52_original_scorer',root/'scoring/original_scorer.py')
    scorer=importlib.util.module_from_spec(spec);spec.loader.exec_module(scorer)
    require(load(root,'scoring/contract.json')==definition,'unchanged scorer/definition contract')
    groups=scorer.make_order_groups(definition,native['full'],native['full'])
    scored=scorer.score(definition,native['full'],native['limited'],diagnostic=True,order_groups=groups)
    require(scored['exact'] and scored['f1']==1.0,'native requested-record scoring binding')
    root_source=load(root,'source/evidence/actual_ROOT_prefix34_all110_original_and_SQL_replay_v1_NOT_gold.json.gz')
    require(root_source['all110_original_report_CP_slices_replayed']==cp_slices,'independent ROOT source replay binding')
    return {'status':'PASS_PORTABLE_SOURCE_FROZEN_NATIVE_AND_UNCHANGED_SCORER_BINDING',
            'Agreement':len(agreements),'eligible_CR':len(cr_by_tdoc),'source_frontier':len(prefix),
            'source_cover_fields':cover_fields,'source_original_acts':110,'source_original_CP_slices':cp_slices,
            'prefix_source_positive':len(positive),'prefix_source_negative':len(negative),
            'native_full':len(native['full']),'native_selected':len(native['limited']),
            'selected_ids':[row['tdocNumber']for row in native['limited']],
            'scorer_diagnostic_exact':scored['exact'],'model_API_calls':0,'native_calls':0,
            'scope':'Included original-source bindings and retained-rule/native equality; independent semantic reviews and external publication admission remain separately recorded.'}


if __name__=='__main__':
    root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent
    print(json.dumps(verify(root),ensure_ascii=False))
