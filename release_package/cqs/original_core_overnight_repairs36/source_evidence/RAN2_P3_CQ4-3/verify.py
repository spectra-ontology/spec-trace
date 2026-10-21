#!/usr/bin/env python3
"""Replay the frozen Resolution affected-clause trace case without host files, network, or a model call.

This verifies a captured case and its diagnostic controls. It does not decide
question meaning or turn a local check into an independent review/native run.
"""
from __future__ import annotations

import argparse
import collections
import copy
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
if sys.flags.optimize:
    raise SystemExit('Verification requires enabled checks; -O/-OO refused.')
HERE = Path(os.path.abspath(__file__)).parent
INVENTORY_SHA256 = '2aa975403b23656e9fadb31746326317200adce5bb74f918c4663dd71a41ffdc'
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
      "m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}
W = "{" + NS["w"] + "}"
TEXT_TAGS = {W + "t", "{" + NS["m"] + "}t"}
FIELDS = ["r.resolutionId", "cr.tdocNumber", "cr.clausesAffected", "sp.specNumber"]
RANKS = []


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_pairs(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, "duplicate JSON object key")
        out[key] = value
    return out


def parse_json(raw):
    return json.loads(raw, object_pairs_hook=unique_pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def read_json(name):
    path = safe(HERE / name)
    raw = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
    return parse_json(raw)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe(path):
    path = Path(os.path.abspath(path))
    for ancestor in (path, *path.parents):
        require(not ancestor.is_symlink(), 'symlink forbidden: ' + str(ancestor))
    if path.exists():
        mode = path.lstat().st_mode
        require(stat.S_ISREG(mode) or stat.S_ISDIR(mode), 'nonregular entry forbidden: ' + str(path))
    return path


def local_module(name):
    # Explicit members support -I -S and prevent ambient/PYTHONPATH fallbacks.
    path = safe(HERE / (name + '.py'))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def no_host_audit():
    counts = {'network_calls': 0, 'subprocess_calls': 0, 'SQL_calls': 0,
              'host_private_open_attempts': 0, 'write_open_attempts': 0,
              'packet_read_opens': 0, 'stdlib_read_opens': 0}
    stdlib = Path(os.__file__).resolve().parent
    def hook(event, args):
        if event.startswith(('socket.', 'http.client.', 'urllib.')):
            counts['network_calls'] += 1
            raise RuntimeError('No-host replay forbids network: ' + event)
        if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.posix_spawnp', 'os.fork', 'os.exec', 'os.spawn'}:
            counts['subprocess_calls'] += 1
            raise RuntimeError('No-host replay forbids subprocess: ' + event)
        if event.startswith('sqlite3.'):
            counts['SQL_calls'] += 1
            raise RuntimeError('No-host replay forbids SQL: ' + event)
        if event == 'open':
            path, mode, flags = args
            if isinstance(path, int):
                counts['host_private_open_attempts'] += 1
                raise RuntimeError('No-host replay forbids descriptor file opens')
            if (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC)):
                counts['write_open_attempts'] += 1
                raise RuntimeError('No-host replay forbids file writes')
            target = Path(os.path.abspath(os.fsdecode(path)))
            if target.is_relative_to(HERE):
                safe(target)
                counts['packet_read_opens'] += 1
            elif target.is_relative_to(stdlib):
                counts['stdlib_read_opens'] += 1
            else:
                counts['host_private_open_attempts'] += 1
                raise RuntimeError('No-host replay forbids host-private open: ' + str(target))
    sys.addaudithook(hook)
    return counts


def token(row, fields=FIELDS):
    require(type(row) is dict and set(row) == set(fields), "unexpected native/requested columns")
    require(all(type(row[k]) is str for k in FIELDS), "requested fields must all be strings")
    for name in RANKS:
        if name in fields:
            require(type(row[name]) is int, "source numeric rank must be an integer")
    return tuple((k, type(row[k]).__name__, row[k]) for k in fields)


def combined(element):
    return "".join(e.text or "" for e in element.iter() if e.tag in TEXT_TAGS)


def norm(value):
    return re.sub(r"\s+", "", value).casefold()


def read_lines(name):
    path = safe(HERE / name)
    raw = path.read_bytes()
    if name.endswith('.gz'):
        raw = gzip.decompress(raw)
    return [parse_json(line) for line in raw.splitlines() if line.strip()]


def block_text(element):
    return ''.join((n.text or '') if n.tag in TEXT_TAGS else '\t' if n.tag == W+'tab' else '\n' if n.tag in (W+'br', W+'cr') else '' for n in element.iter())


def parse_native(item):
    receipt = read_json(item['receipt'])
    raw = gzip.decompress((HERE / item['rows']).read_bytes())
    fields = item['columns']
    records = [parse_json(line) for line in raw.splitlines() if line.strip()]
    require(all(type(row) is list and len(row) == len(fields) for row in records), 'native positional row shape')
    rows = [dict(zip(fields, row)) for row in records]
    for row in rows:
        token(row, fields)
    digest = sha((HERE / item['query']).read_bytes())
    require(receipt['status'] == 'OK' and receipt['id'] == 'RAN2_P3_CQ4-3' and receipt['wg'] == 'RAN2', 'native status or identity')
    require(receipt['query_sha256'] == digest == sha(receipt['query'].encode()), 'native query pin')
    require(receipt['columns'] == fields, 'native column definition')
    require(receipt['plan_query_type'] == receipt['execution_query_type'] == 'r', 'native read-only classification')
    require(receipt['rollback_completed'] and receipt['execution_summary_complete'] and receipt['full_rows_available'] and not receipt['truncated'], 'native capture/rollback incomplete')
    require(sha(raw) == receipt['rows_sha256'] and len(raw) == receipt['bytes_retained'], 'native retained byte pin')
    require(len(rows) == receipt['rows_retained'] == item['row_count'], 'native retained cardinality')
    return rows, receipt


def source_text(element, include_deleted=False):
    tags = TEXT_TAGS | ({W+'delText'} if include_deleted else set())
    return ''.join((n.text or '') if n.tag in tags else '\t' if n.tag == W+'tab' else '\n' if n.tag in (W+'br',W+'cr') else '' for n in element.iter())


def raw_workbook(name):
    S='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    with zipfile.ZipFile(safe(HERE/name)) as z:
        strings=[''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml'))] if 'xl/sharedStrings.xml' in z.namelist() else []
        root=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
    output={}
    for row in root.find(S+'sheetData'):
        cells={}
        for cell in row.findall(S+'c'):
            value=cell.find(S+'v')
            raw=value.text if value is not None else ''.join(cell.itertext())
            cells[re.sub(r'\d','',cell.attrib['r'])]=strings[int(raw)] if cell.get('t')=='s' else raw
        output[int(row.attrib['r'])]=cells
    return output


def column_name(number):
    output=''
    while number:
        number,rem=divmod(number-1,26)
        output=chr(65+rem)+output
    return output


def source_replay(proof, rows):
    report_trees={}; workbooks={}; fragment_count=0; cover_count=0
    for meeting,pin in proof['fresh_original_report_pins'].items():
        name='sources/report_'+meeting+'.docx'
        require(sha((HERE/name).read_bytes())==pin['original']['member_sha256'],'original report DOCX member pin')
        with zipfile.ZipFile(HERE/name) as z:
            xml=z.read('word/document.xml'); styles=z.read('word/styles.xml')
        require(sha(xml)==pin['document_xml_sha256'] and sha(styles)==pin['styles_xml_sha256'],'original report XML/styles')
        blocks=list(ET.fromstring(xml).find(W+'body'))
        require(len(blocks)==pin['all_raw_body_children_n'],'report body length')
        report_trees[meeting]=blocks
        name='sources/register_'+meeting+'.xlsx'
        require(sha((HERE/name).read_bytes())==pin['workbook_member_sha256'],'original workbook member pin')
        workbooks[meeting]=raw_workbook(name)
    grouped={r['resolutionId']:r for r in rows}
    for review in proof['source_resolution_reviews']:
        blocks=report_trees[review['source_meeting']]
        first=blocks[review['own_start_body_child0']]
        require(source_text(first,True).strip() in [line.strip() for line in grouped[review['resolutionId']]['content'].splitlines()],'Resolution own first-line binding')
        for fragment in review['original_source_fragments']:
            block=blocks[fragment['body_child0']]
            raw=ET.tostring(block,encoding='unicode')
            require(raw==fragment['xml'] and sha(raw.encode())==fragment['xml_sha256'],'source report fragment XML')
            require(source_text(block,True)==fragment['text'],'source report fragment text')
            fragment_count+=1
    for tid,pin in proof['fresh_original_CR_documents49'].items():
        name='sources/'+tid+'.docx'
        require(sha((HERE/name).read_bytes())==pin['member_sha256'],'original CR DOCX member pin')
        with zipfile.ZipFile(HERE/name) as z:
            xml=z.read('word/document.xml'); styles=z.read('word/styles.xml')
        require(sha(xml)==pin['document_xml_sha256'] and sha(styles)==pin['styles_xml_sha256'],'CR XML/styles')
        root=ET.fromstring(xml); tables=list(root.iter(W+'tbl'))
        paragraphs=list(root.iter(W+'p'))
        require(len(paragraphs)==pin['paragraphs_n'],'CR complete paragraph count')
        for cover in pin['formal_cover_rows']:
            row=tables[cover['table0']].findall(W+'tr')[cover['row0']]
            require(sha(ET.tostring(row))==cover['xml_sha256'],'CR cover XML')
            require([source_text(c).strip() for c in row.findall(W+'tc')]==cover['cells'],'CR cover fields')
            cover_count+=1
        for operative in pin.get('explicit_Case3_reason_and_operative_XML',[]):
            paragraph=paragraphs[operative['all_w_p_ordinal0']]
            require(ET.tostring(paragraph,encoding='unicode')==operative['xml'],'recovered own Case source operative XML')
            require(source_text(paragraph,True)==operative['text'],'recovered own Case source operative text')
    for row in proof['original54_path_judgments']:
        cell=row['original_named_metadata_cells']; book=workbooks[cell['meeting']]
        for field,value in cell['fields'].items():
            column=column_name(cell['columns1'][field])
            require(book[1].get(column,'').strip()==field,'original workbook named column')
            require(str(book[cell['excel_row1']].get(column,''))==str(value),'original workbook raw field value')
        require(cell['fields']['Clauses Affected']==row['clausesAffected'] and str(cell['fields']['Spec'])==row['specNumber'],'raw clauses/spec binding')
        norm=lambda s:re.sub(r'\s+','',s).rstrip(',.;')
        require(norm(row['original_CR_cover_clauses'])==norm(row['clausesAffected']),'CR cover clauses/frozen declaration')
    null=proof['original_NULL_own_positive_control2228']['original_metadata_cells']
    require(null['fields']['Clauses Affected'] in ('',None),'source-positive recorded-blank counterauthority')
    require(workbooks[null['meeting']][null['excel_row1']].get(column_name(null['columns1']['Clauses Affected']),'')=='','actual workbook blank counterauthority')
    return {'report_DOCX':len(report_trees),'CR_DOCX':len(proof['fresh_original_CR_documents49']),'report_XML_fragments':fragment_count,'CR_cover_rows':cover_count,'original_named_workbook_path_records':54}


def main():
    if len(sys.argv)!=1:
        raise SystemExit('This closed replay takes no external files or flags.')
    safe(HERE/'verify.py'); audit=no_host_audit()
    inventory_raw=safe(HERE/'immutable_inventory.json').read_bytes()
    require(sha(inventory_raw)==INVENTORY_SHA256,'fixed payload inventory changed')
    inventory=parse_json(inventory_raw)['files']; manifest=read_json('manifest.json')
    require(manifest['id']=='RAN2_P3_CQ4-3','wrong case')
    require(manifest['files']==inventory and manifest['immutable_inventory_sha256']==INVENTORY_SHA256,'manifest inventory declaration differs')
    actual=set()
    for path in HERE.rglob('*'):
        safe(path); mode=path.lstat().st_mode
        require(stat.S_ISREG(mode) or stat.S_ISDIR(mode),'nonregular entry forbidden')
        if stat.S_ISREG(mode):actual.add(path.relative_to(HERE).as_posix())
    require(actual==set(inventory)|{'manifest.json','immutable_inventory.json','verify.py'},'missing or extra payload file')
    for name,pin in inventory.items():
        relative=Path(name)
        require(type(name)is str and name and '\\'not in name and not relative.is_absolute() and '..'not in relative.parts,'unsafe payload path')
        raw=safe(HERE/relative).read_bytes()
        require(len(raw)==pin['bytes'] and sha(raw)==pin['sha256'],'pin mismatch: '+name)
    require(sha((HERE/'verify.py').read_bytes())==manifest['verifier_sha256'],'verifier differs')
    declarations=read_json('packet_declarations.json')
    require(set(manifest)==set(declarations)|{'files','immutable_inventory_sha256','verifier_sha256'},'unexpected manifest declaration')
    require(all(manifest.get(k)==v for k,v in declarations.items()),'scientific declaration differs')
    typed=local_module('typed_values'); local_module('scorer')
    original_scorer=local_module('original_scorer'); checks=local_module('contract_checks')
    review_schema=local_module('review_schema'); rule=local_module('frozen_rule')
    original=read_json('authority/original_selected_row.json'); repair=read_json('data/repair.json')
    require(original['question_en']==repair['question_en'] and original['cypher']==repair['original_query'],'original EN/query bytes')
    require(sha(repair['question_en'].encode())==manifest['question_sha256'],'original EN SHA')
    require(sha(typed.json_exact(repair).encode())==manifest['canonical_repair_sha256'],'canonical9 identity')
    require(len(repair)==9 and [f['name'] for f in repair['required_fields']]==FIELDS,'canonical9 requested4')
    require(all(f['type']=='string' and f['nullable'] is False for f in repair['required_fields']),'requested4 typed schema')
    require(repair['collection']=={'kind':'multiset'} and repair['cardinality_policy']=={'mode':'top_k','value':10},'original pathbag cap10')
    require(sha((HERE/'authority/criteria.json').read_bytes())==manifest['criteria_sha256'],'fixed criteria')
    criteria=read_json('authority/criteria.json')
    primary=read_json('reviews/primary.json')
    units=criteria['semantic_units']
    require(len(units)==7,'exact seven original meaning units')
    review_schema.check_pass(primary,repair['question_en'],units,criteria_sha=manifest['criteria_sha256'],identity_key='repair_sha256',identity_sha=manifest['canonical_repair_sha256'])
    secondary=read_json('reviews/secondary.json')
    review_schema.check_pass(secondary,repair['question_en'],units,criteria_sha=manifest['criteria_sha256'],identity_key='repair_sha256',identity_sha=manifest['canonical_repair_sha256'])
    require(primary['reviewer']!=secondary['reviewer'] and secondary['reviewer']=='/root','two distinct AI reviewers')
    require(primary['nonblind'] is True and secondary['nonblind'] is True and primary['human_n']==secondary['human_n']==0,'review provenance/nonblind AI human0')
    require(secondary['primary_review']['sha256']==sha((HERE/'reviews/primary.json').read_bytes()),'secondary/actual primary pin')
    require(secondary['source_and_native_SQL_bridge']['sha256']==sha((HERE/'reviews/ROOT_actual_source_native_SQL_bridge.json').read_bytes()),'secondary/actual original-source bridge pin')
    require(secondary['source_ownership_proof']['sha256']==sha(gzip.decompress((HERE/'data/source54_52_closure.json.gz').read_bytes())),'secondary/original independent source judgment pin')
    require(secondary['repair_file_sha256']==sha((HERE/'data/repair.json').read_bytes()) and secondary['ROOT_final_seal'] is False,'canonical file pin/review separate from final seal')
    bridge=read_json('reviews/ROOT_actual_source_native_SQL_bridge.json')
    require(bridge['status']=='PASS_ROOT_FRESH_ORIGINAL_BYTE_REOPEN_AND_NATIVE_SQL_TRACE_BAGS' and bridge['database']['sha256']==manifest['sqlite_sha256'],'independent ROOT fresh source/SQL proof')
    require(bridge['original_raw_paths']==185 and bridge['original_predicate_free_prefix_n']==52 and bridge['manual_source_positive_n']==10 and bridge['manual_source_excluded_n']==42,'independent ROOT original prefix coverage')
    require(bridge['actual_native_capture']['sha256']==sha((HERE/'native/execution_RAN2.json').read_bytes()) and bridge['actual_guard']['sha256']==sha((HERE/'native/guard_receipt.json').read_bytes()),'independent ROOT exact native/guard pins')
    query=(HERE/'queries/limited10.cypher').read_text()
    require(repair['reference_query']+'\n'==query,'preserved old final-LF Cypher/canonical bridge')
    require((HERE/'queries/canonical_limited10.cypher').read_text()==repair['reference_query'],'exact canonical query/native bytes')
    frontier=read_json('data/fresh_sql_frontier.json.gz'); rows=frontier['all185_rows']
    require(len(rows)==185 and frontier['sqlite_sha256_before']==frontier['sqlite_sha256_after']==manifest['sqlite_sha256'],'original full185 immutable SQL')
    replay=rule.replay(rows,query)
    require(len(replay['full_projected_rows'])==49 and len(replay['selected_projected_rows'])==10 and len(replay['original_frontier_path_rows'])==52,'frozen49/10/original52')
    emulation=read_json('data/operator_emulation.json')
    require(replay['full_projected_rows']==emulation['full49_projected_rows'] and replay['selected_projected_rows']==emulation['selected10_projected_rows'],'full185 rule emulation')
    for row in rows:
        derived=rule.classify(row,query)
        require(all(derived[k]==row[k] for k in derived),'all185 predicate component equivalence')
    proof=read_json('data/source54_52_closure.json.gz')
    pathid=lambda r:tuple(r[k] for k in ('rnode','refedge','crnode','modedge','spnode'))
    keyed={pathid(r):r for r in rows}
    require(len(keyed)==185,'raw node/edge paths retained')
    matrix=proof['original54_path_judgments'];require(len(matrix)==54,'preserved original54')
    for row in matrix:
        source=keyed[pathid(row)]
        require(all(row[k]==source[k] for k in ('resolutionId','tdocNumber','title','clausesAffected','specNumber','specRelease')),'own source/raw path binding')
        require(row['retained_predicate_result_COMPARISON_ONLY']==rule.classify(source,query)['provisional_eligible'],'predicate/source judgments separate comparison')
    cutoff=tuple(replay['selected_cutoff3key'])
    front=[r for r in rows if rule.path_key(r)<=cutoff]
    require(collections.Counter(pathid(r) for r in front)==collections.Counter(pathid(r) for r in replay['original_frontier_path_rows']),'original185 precut universe before candidate filter')
    frontids={pathid(r) for r in front}; matrixfront=[r for r in matrix if pathid(r) in frontids]
    require(len(matrixfront)==52 and {pathid(r) for r in matrixfront}==frontids,'all52 own-source closure')
    counts=collections.Counter(r['manual_source_ownership'] for r in matrixfront)
    require(counts=={'own_positive':10,'foreign_to_this_own_decision':42},'own10/excluded42 unknown0')
    require(all((r['manual_source_ownership']=='own_positive')==r['retained_predicate_result_COMPARISON_ONLY'] for r in matrixfront),'no excluded own path before cut')
    require(sum(rule.path_key(r)==cutoff for r in rows)==1,'original boundary singleton')
    require(proof['global_candidate_classifier_certified'] is False and frontier['global_own_classifier_claim'] is False,'no unsupported global claim')
    require(sum(r['manual_source_ownership']=='own_not_certified_possible_positive' for r in matrix)==1,'aftercut possible-positive retained')
    source_counts=source_replay(proof,rows)
    native=read_json('native/index.json'); observed={}; receipts={}
    for item in native:
        observed[item['kind']],receipts[item['kind']]=parse_native(item)
    bag=lambda records:collections.Counter(token(row) for row in records)
    require(bag(observed['original185'])==bag([rule.project(r) for r in rows]),'actual full185 native/SQL4role rawbag')
    require(bag(observed['candidate49'])==bag(replay['full_projected_rows']),'actual full49 native/SQL4role rawbag')
    require(observed['limited10']==replay['selected_projected_rows'],'actual limited10 original three-key membership')
    require(observed['canonical_limited10']==observed['limited10'],'exact-canonical native10/preserved old native10 observed equality')
    require(receipts['canonical_limited10']['query']==repair['reference_query'],'actual captured query equals canonical exact bytes')
    gold=read_json('data/actual_native_gold10.json');require(gold==observed['canonical_limited10'],'gold actual exact-canonical observed native10')
    execution=read_json('native/execution_RAN2.json');protocol=read_json('native/execution_protocol.json');guard=read_json('native/guard_receipt.json')
    require(execution['inventory_unchanged'] and execution['source_before']==execution['source_after'],'frozen graph unchanged')
    require(execution['source_before']['nodes']==156288 and execution['source_before']['relationships']==939037 and execution['model_calls']==0,'original RAN2 graph/model0')
    require(execution['source_before']['source']['sha256']==manifest['ttl_sha256'],'archived TTL pin')
    require(protocol['container_memory_bytes']==protocol['python_address_space_limit_bytes']==2*1024**3 and protocol['container_cpu_cores']==protocol['concurrent_containers']==1 and protocol['query_timeout_seconds']==20,'unchanged execution resource protocol')
    require(protocol['model_calls']==0 and guard['status']=='PASS' and guard['child_exit']==0 and guard['quality_rerolls']==0,'actual native guard success')
    require(guard['prestart_available_minimum_bytes']==26*1024**3 and guard['continuous_reserve_minimum_bytes']==16*1024**3,'two-host reserve thresholds')
    require(all(v>=26*1024**3 for k,v in guard['initial_memory'].items() if k.endswith('available_bytes')),'two-host admission samples')
    require(all(s[k]>=16*1024**3 for s in guard['memory_samples'] for k in ('Linux_available_bytes','Windows_available_bytes')),'continuous two-host samples')
    require(guard['owned_cleanup']['owned_stopped'] and guard['owned_cleanup']['common_lock_held'],'owned cleanup/common lock')
    require(len(execution['items'])==3 and all(i['status']=='OK' for i in execution['items']),'all native executions succeeded')
    exact_execution=read_json('native/canonical_execution_RAN2.json');exact_protocol=read_json('native/canonical_execution_protocol.json');exact_guard=read_json('native/canonical_guard_receipt.json')
    require(exact_execution['inventory_unchanged'] and exact_execution['source_before']==exact_execution['source_after']==execution['source_before'],'exact canonical capture original graph unchanged')
    require(len(exact_execution['items'])==1 and exact_execution['items'][0]['status']=='OK' and exact_execution['items'][0]['rows']==10 and exact_execution['items'][0]['query_sha256']==sha(repair['reference_query'].encode()),'one exact canonical execution/query SHA')
    require(exact_protocol==protocol,'unchanged canonical query capture execution protocol')
    require(exact_guard['status']=='PASS' and exact_guard['child_exit']==0 and exact_guard['quality_rerolls']==0,'actual canonical query guard success')
    require(exact_guard['prestart_available_minimum_bytes']==26*1024**3 and exact_guard['continuous_reserve_minimum_bytes']==16*1024**3,'exact canonical two-host thresholds')
    require(all(v>=26*1024**3 for k,v in exact_guard['initial_memory'].items() if k.endswith('available_bytes')),'exact canonical two-host admission samples')
    require(all(sample[k]>=16*1024**3 for sample in exact_guard['memory_samples'] for k in ('Linux_available_bytes','Windows_available_bytes')),'exact canonical continuous samples')
    require(exact_guard['owned_cleanup']['owned_stopped'] and exact_guard['owned_cleanup']['common_lock_held'],'exact canonical owned cleanup/common lock')
    exact_input=read_lines('native/canonical_requested_input.jsonl')
    require(len(exact_input)==1 and exact_input[0]['candidate_query']==repair['reference_query'] and exact_execution['input_sha256']==sha((HERE/'native/canonical_requested_input.jsonl').read_bytes()),'exact canonical input execution pin')
    exact_bridge=read_json('reviews/ROOT_actual_source_native_SQL_canonical_bridge_v3.json')
    require(exact_bridge['canonical_query_bytes_exact'] is True and exact_bridge['prior_limited_rows_preserved_and_identical'] is True,'independent ROOT canonical byte bridge')
    for key,name in [('actual_native_capture','native/execution_RAN2.json'),('actual_guard','native/guard_receipt.json'),('actual_exact_canonical_capture','native/canonical_execution_RAN2.json'),('actual_exact_canonical_guard','native/canonical_guard_receipt.json'),('actual_exact_canonical_meta','native/canonical_limited10.json')]:
        require(exact_bridge[key]['sha256']==sha((HERE/name).read_bytes()),'independent ROOT exact bridge pin: '+key)
    require(exact_bridge['actual_exact_canonical_rows']['sha256']==sha(gzip.decompress((HERE/'native/canonical_limited10.jsonl.gz').read_bytes())),'independent ROOT exact row bytes')
    controls=checks.checks(repair,gold)
    require(len(controls)==16 and all(c['pass'] for c in controls),'official requested4 controls')
    preds=[list(reversed(gold)),gold[:-1]+[gold[0]],gold[:-1]+[replay['full_projected_rows'][10]],copy.deepcopy(gold),copy.deepcopy(gold)]
    preds[3][0]['cr.tdocNumber']=gold[1]['cr.tdocNumber'];preds[4][0]['cr.clausesAffected']=None
    for prediction,want in zip(preds,[True,False,False,False,False]):
        require(original_scorer.score(repair,gold,prediction,diagnostic=True,order_groups=None)['exact'] is want,'additional multiset/path-binding control')
    print(json.dumps({'status':'PASS','id':manifest['id'],'scope':'frozen native/source replay; independent semantic ROOT review and seal remain separate','canonical_repair_sha256':manifest['canonical_repair_sha256'],'native_counts':[len(observed[k]) for k in ('original185','candidate49','limited10','canonical_limited10')],'exact_canonical_native_query_sha256':sha(repair['reference_query'].encode()),'actual_guards_preserved_and_verified':2,'source_closure':{'original54':54,'original_raw_prefix52':52,'own_positive':10,'foreign':42,'unknown_in_prefix':0},'source_reopened':source_counts,'requested_role_controls':21,'exact_semantic_units':7,'distinct_nonblind_AI_reviews':2,'ROOT_final_seal_included':False,'model_calls':0,'human_n':0,'no_host_audit':audit},ensure_ascii=False))


if __name__=='__main__':
    main()
