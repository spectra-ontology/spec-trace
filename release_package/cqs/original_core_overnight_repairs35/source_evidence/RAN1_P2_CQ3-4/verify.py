#!/usr/bin/env python3
"""Replay the frozen Qualcomm Agreement case without host files, network, or a model call.

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
INVENTORY_SHA256 = 'aa9b41f949915030a1c295c186e1e86f4c821faf257fe35c89bf514f5b7bc8b2'
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
      "m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}
W = "{" + NS["w"] + "}"
TEXT_TAGS = {W + "t", "{" + NS["m"] + "}t"}
FIELDS = ["t.tdocNumber", "a.resolutionId", "a.content", "m.meetingNumber"]
RANKS = ["__source_order_meetingNumberInt", "__source_order_bis"]


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
    require(receipt['status'] == 'OK' and receipt['id'] == 'RAN1_P2_CQ3-4' and receipt['wg'] == 'RAN1', 'native status or identity')
    require(receipt['query_sha256'] == digest == sha(receipt['query'].encode()), 'native query pin')
    require(receipt['columns'] == fields, 'native column definition')
    require(receipt['plan_query_type'] == receipt['execution_query_type'] == 'r', 'native read-only classification')
    require(receipt['rollback_completed'] and receipt['execution_summary_complete'] and receipt['full_rows_available'] and not receipt['truncated'], 'native capture/rollback incomplete')
    require(sha(raw) == receipt['rows_sha256'] and len(raw) == receipt['bytes_retained'], 'native retained byte pin')
    require(len(rows) == receipt['rows_retained'] == item['row_count'], 'native retained cardinality')
    return rows, receipt


def raw_register(path, source):
    S = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    with zipfile.ZipFile(path) as z:
        shared = z.read('xl/sharedStrings.xml')
        sheet = z.read('xl/worksheets/sheet1.xml')
    require(sha(shared) == source['sharedStrings_XML_sha256'] and sha(sheet) == source['sheet_XML_sha256'], 'raw register XML pin')
    strings = [''.join(n.itertext()) for n in ET.fromstring(shared)]
    header, output = None, []
    for row in ET.fromstring(sheet).find(S+'sheetData'):
        cells = {}
        for cell in row:
            value = cell.find(S+'v')
            cells[re.sub(r'\d','',cell.attrib['r'])] = strings[int(value.text)] if cell.get('t') == 's' and value is not None else value.text if value is not None else ''.join(cell.itertext())
        if header is None:
            header = cells
            require([header[k] for k in ['A','B','C']] == ['TDoc','Title','Source'], 'register Source schema')
        else:
            output.append({'number':cells.get('A'),'title':cells.get('B'),'Source':cells.get('C'),'row':int(row.attrib['r']),'raw_XML':ET.tostring(row,encoding='unicode')})
    return output


def main():
    if len(sys.argv) != 1:
        raise SystemExit('This closed replay takes no external files or flags.')
    safe(HERE / 'verify.py')
    audit = no_host_audit()
    inventory_raw = safe(HERE / 'immutable_inventory.json').read_bytes()
    require(sha(inventory_raw) == INVENTORY_SHA256, 'fixed payload inventory changed')
    inventory = parse_json(inventory_raw)['files']
    manifest = read_json('manifest.json')
    require(manifest['id'] == 'RAN1_P2_CQ3-4', 'wrong case')
    require(manifest['files'] == inventory and manifest['immutable_inventory_sha256'] == INVENTORY_SHA256, 'manifest inventory declaration differs')
    actual = set()
    for path in HERE.rglob('*'):
        safe(path)
        mode = path.lstat().st_mode
        require(stat.S_ISREG(mode) or stat.S_ISDIR(mode), 'nonregular entry forbidden')
        if stat.S_ISREG(mode):
            actual.add(path.relative_to(HERE).as_posix())
    require(actual == set(inventory) | {'manifest.json','immutable_inventory.json','verify.py'}, 'missing or extra payload file')
    for name, pin in inventory.items():
        relative = Path(name)
        require(type(name) is str and name and '\\' not in name and not relative.is_absolute() and '..' not in relative.parts, 'unsafe payload path')
        raw = safe(HERE / relative).read_bytes()
        require(len(raw) == pin['bytes'] and sha(raw) == pin['sha256'], 'pin mismatch: '+name)
    require(sha((HERE / 'verify.py').read_bytes()) == manifest['verifier_sha256'], 'verifier differs')
    declarations = read_json('packet_declarations.json')
    require(set(manifest) == set(declarations) | {'files','immutable_inventory_sha256','verifier_sha256'}, 'unexpected manifest declaration')
    require(all(manifest.get(k) == v for k,v in declarations.items()), 'scientific declaration differs')
    local_module('typed_values')
    local_module('scorer')
    original_scorer = local_module('original_scorer')
    contract_checks = local_module('contract_checks')
    rule = local_module('frozen_rule')
    styles = local_module('source_xml_styles')
    original = read_json('authority/original_selected_row.json')
    repair = read_json('data/repair.json')
    contract = read_json('data/scoring_contract.json')
    require(sha(original['question_en'].encode()) == manifest['question_sha256'], 'original question bytes')
    require(original['question_en'] == repair['question_en'] == contract['question_en'], 'question changed')
    require(original['cypher'] == repair['original_query'], 'original query changed')
    require(sha((HERE / 'authority/criteria.json').read_bytes()) == manifest['criteria_sha256'], 'fixed criteria changed')
    require(sha((HERE / 'queries/limited.cypher').read_bytes()) == manifest['candidate_query_sha256'] == contract['reference_query_sha256'], 'candidate query changed')
    require(repair['reference_query'] == (HERE/'queries/limited.cypher').read_text(), 'canonical candidate mismatch')
    require(repair['required_fields'] == contract['required_fields'] and repair['collection'] == contract['collection'] and repair['cardinality_policy'] == contract['cardinality_policy'], 'canonical scoring definition')
    require([f['name'] for f in contract['required_fields']] == ['a.resolutionId'] and contract['collection']['require_rank_order'] is False, 'List minimum output is identity set')
    inputs_raw = gzip.decompress((HERE/'data/frozen_inputs.json.gz').read_bytes())
    require(sha(inputs_raw) == manifest['raw_frozen_inputs_sha256'], 'original frozen scalar/relation input bytes')
    inputs = parse_json(inputs_raw)
    agreements, tdocs, company = inputs['Agreement'], inputs['Tdoc'], inputs['Company']
    meetings = {m['node_id']:m for m in inputs['Meeting']}
    require(len(agreements) == 21058 and len(tdocs) == 123677, 'full frozen input coverage')
    require(len({a['node_id'] for a in agreements}) == len(agreements) and len({t['tdocNumber'] for t in tdocs}) == len(tdocs), 'duplicate frozen identity')
    inferred = rule.project(agreements,tdocs,meetings,company)
    ranked = inferred['all_distinct_Agreement_rows']
    require(len(ranked) == len({r['a.resolutionId'] for r in ranked}) == 534, 'full distinct Agreement population')
    require(inferred['qualified_Tdoc_n'] == 9079 and inferred['header_Company_Tdoc_title_keys'] == 984, 'generic Company inference population')
    saved_ranked = read_json('data/full534_ranked_SQL.json.gz')
    require(ranked == saved_ranked, 'full534 fresh SQL generic projection differs')
    qualified = set(inferred['Company_proofs'])
    require(qualified == {r['tdocNumber'] for r in read_json('data/qualified_Tdocs9079_SQL.json.gz')}, 'Company9079 fresh SQL set differs')
    qualified_missing_edges = sum(len(set(w['own_qualifying_Tdocs']) - set(next(a['REFERENCES_Tdocs'] for a in agreements if a['resolutionId'] == w['id']))) for w in inferred['witnesses'])
    require(qualified_missing_edges == 59, 'qualified own references missing existing edges were discarded')
    plain = [{k:r[k] for k in FIELDS} for r in ranked]
    by_id = {a['resolutionId']:a for a in agreements}
    source_capture = read_json('data/source_capture.json')
    require(source_capture['DB_before'] == source_capture['DB_after'], 'source SQL immutable pin')
    docs = {}
    for source in source_capture['source_pins']:
        raw = (HERE/'source'/(source['meeting'].replace('#','_')+'_source.docx')).read_bytes()
        require(sha(raw) == source['DOCX_sha256'], 'original DOCX pin')
        with zipfile.ZipFile(HERE/'source'/(source['meeting'].replace('#','_')+'_source.docx')) as z:
            xb,sb = z.read('word/document.xml'),z.read('word/styles.xml')
        require(sha(xb) == source['XML_sha256'] and sha(sb) == source['styles_sha256'], 'original XML/styles pins')
        root,sty = ET.fromstring(xb),ET.fromstring(sb)
        docs[source['meeting']] = (root,list(root.find(W+'body')),{s.get(W+'styleId'):s for s in sty.findall(W+'style')},styles.props(sty.find(W+'docDefaults/'+W+'rPrDefault/'+W+'rPr')))
    census = read_lines('data/source869.jsonl.gz')
    require(len(census) == len({a['resolutionId'] for a in census}) == 869, 'original source census coverage')
    block_count,source_positive,source_known = 0,[],set()
    for a in census:
        body = docs[a['meeting']][1]
        for captured in a['source_blocks']:
            element = body[captured['raw_body_child']]
            require(sha(ET.tostring(element)) == captured['XML_sha256'] and block_text(element) == captured['text'], 'actual original source block differs')
            block_count += 1
        own = rule.own_record('\n'.join(b['text'] for b in a['source_blocks']))[0]
        frozen = by_id[a['resolutionId']]
        require(all(frozen.get(k) == v for k,v in a['frozen'].items()), 'census frozen source properties')
        retained = rule.own_record(frozen.get('contentWithEquations') or frozen.get('content'))[0]
        note = rule.own_record(frozen.get('note'))[0]
        refs = set(rule.TD.findall(own))
        source_known.update(refs)
        squal = sorted(refs & qualified)
        fqual = sorted(set(rule.TD.findall(retained+'\n'+note)) & qualified)
        require(squal == fqual, 'source/frozen own qualified reference differs')
        if squal:
            source_positive.append({'id':a['resolutionId'],'meeting':a['meeting'],'refs':squal})
    require(block_count == 7173 and len(source_positive) == 12, 'source binding counts')
    frontier = {r['id'] for r in source_positive if r['meeting'] in ['RAN1#123','RAN1#122b']}
    require(frontier == {r['a.resolutionId'] for r in plain[:10]}, 'full source latest10 frontier')
    registers = read_json('data/register_capture.json')
    raw_registers = {}
    alias_rows = 0
    aliases = parse_json(company['aliases'])
    for source in registers['source_pins']:
        path = HERE/'source'/Path(source['path']).name
        require(sha(path.read_bytes()) == source['sha256'], 'original register pin')
        rows = raw_register(path,source)
        raw_registers[source['sha256']] = {r['row']:r for r in rows}
        for row in rows:
            canonical = rule.company_in_source(row['Source'],company)
            any_alias = any(re.search(r'(?<!\w)'+re.escape(alias)+r'(?!\w)',row['Source'] or '',re.I) for alias in aliases)
            require(canonical == bool(any_alias), 'recorded Company alias changes latest Source qualifier')
            alias_rows += 1
    require(alias_rows == 4578, 'raw alias/Source row coverage')
    matched = read_json('data/current_register_own192.json.gz')
    tdoc_map = {t['tdocNumber']:t for t in tdocs}
    require(len(matched) == 192, 'own raw register coverage')
    matched_numbers = set()
    for row in matched:
        actual = raw_registers[row['file_sha256']][row['source_row']]
        require(actual['raw_XML'] == row['row_XML'] and actual['number'] == row['tdocNumber'] and actual['title'] == row['title'] and actual['Source'] == row['Source'], 'retained raw Source row differs')
        require(rule.normalize_title(actual['title']) == rule.normalize_title(tdoc_map[row['tdocNumber']]['title']), 'normalized exact own Tdoc title binding')
        require(rule.company_in_source(actual['Source'],company) == (row['tdocNumber'] in qualified), 'raw register/current retained Company qualifier')
        matched_numbers.add(row['tdocNumber'])
    for a in census:
        if a['meeting'] in ['RAN1#123','RAN1#122b']:
            own = rule.own_record('\n'.join(b['text'] for b in a['source_blocks']))[0]
            require((set(rule.TD.findall(own)) & set(tdoc_map)) <= matched_numbers, 'newest own Tdoc raw source not covered')
    chronology = read_json('data/chronology.json')
    for item in chronology:
        body = docs[item['meeting']][1]
        for line in item['first110_body_children_nonempty']:
            literal = ''.join((n.text or '') if n.tag in TEXT_TAGS else '\t' if n.tag == W+'tab' else '' for n in body[line['raw_body_child']].iter())
            require(literal == line['text'], 'original chronological authority text changed')
    operative = read_json('data/operative10_runs_styles.json.gz')
    role_review = read_json('data/operative32_primary.json')
    role_map = {a['id']:a for a in role_review['items']}
    first = {r['a.resolutionId']:r for r in plain[:10]}
    require({a['id'] for a in operative} == set(first), 'operative newest10 coverage')
    role_count,flagged = 0,[]
    for a in operative:
        root,body,sty,defaults = docs[a['meeting']]
        parents = {child:parent for parent in root.iter() for child in parent}
        active = []
        require(a['candidate_four_fields'] == first[a['id']], 'source operative candidate/native context differs')
        for block in a['actual_own_blocks']:
            element = body[block['raw_body_child']]
            require(sha(ET.tostring(element)) == block['xml_sha256'], 'operative own original XML')
            for paragraph in element.iter(W+'p'):
                for run in paragraph.iter(W+'r'):
                    _,effective = styles.run_style(paragraph,run,sty,defaults)
                    ancestors,current = [],run
                    while current in parents:
                        current = parents[current]
                        ancestors.append(current.tag.split('}')[-1])
                    strike = styles.active(effective.get('strike')) or styles.active(effective.get('dstrike'))
                    hidden = styles.active(effective.get('vanish')) or styles.active(effective.get('webHidden'))
                    deleted = 'del' in ancestors or 'moveFrom' in ancestors
                    if strike or hidden or deleted:
                        flagged.append({'id':a['id'],'child':block['raw_body_child'],'text':styles.tx(run),'strike':strike,'hidden':hidden,'tracked_deleted':deleted})
                    else:
                        active.append(styles.tx(run))
        for role in role_map[a['id']]['required_operative_roles']:
            fragment = norm(role['operative_role_literal'])
            require(fragment in norm(''.join(active)) and fragment in norm(first[a['id']]['a.content']), 'operative active-source/native condition missing')
            role_count += 1
    require(role_count == 32, 'operative role cardinality')
    require(flagged == [{'id':'AGR-123-6-001','child':337,'text':'for ','strike':True,'hidden':False,'tracked_deleted':False}], 'source deleted/hidden/struck witness changed')
    for item in role_review['table_style_checks']:
        sty = docs[first[item['id']]['m.meetingNumber']][2]
        for layer in item['table_style_chain']:
            actual = sty[layer['styleId']]
            require(ET.tostring(actual,encoding='unicode') == layer['raw_XML'], 'table style inheritance differs')
            require(not any(n.tag in (W+'strike',W+'dstrike',W+'vanish',W+'webHidden') for n in actual.iter()), 'table inherited hidden/strike condition')
    ids = [{'a.resolutionId':r['a.resolutionId']} for r in ranked]
    require(ids == read_lines('data/reference_gold.jsonl') and ranked == read_lines('data/reference_order_rows.jsonl'), 'canonical reference changed')
    groups = original_scorer.make_order_groups(contract,ranked,ids)
    controls = contract_checks.checks(contract,ids,groups)
    pred = original_scorer.reference_prediction(contract,ids)
    cases = [('reverse_serialization_same_top10_set_allowed',list(reversed(pred)),True),('lower_rank_identity_cannot_replace_top10_member',pred[:-1]+ids[10:11],False),('only9_requested_entities_rejected',pred[:-1],False),('11_requested_entities_rejected',pred+ids[10:11],False),('all_three_context_fields_not_required_or_scored',[dict(r,**{'a.content':'unasked context','m.meetingNumber':'unasked context','t.tdocNumber':'unasked context'}) for r in pred],True)]
    for name,guess,expected in cases:
        controls.append({'check':name,'pass':original_scorer.score(contract,ids,guess,diagnostic=True,order_groups=groups)['exact'] is expected})
    saved_controls = read_json('data/identity_set_controls.json')['controls']
    require([(c['check'],c['pass']) for c in controls] == [(c['check'],c['pass']) for c in saved_controls] and all(c['pass'] for c in controls), 'requested-field controls failed')
    # Source association/ownership ablations are diagnostics, never query inputs.
    dependency = []
    def check(name,actual,expected):
        dependency.append({'check':name,'pass':actual == expected})
    check('foreign_following_catalogue_not_own',rule.own_record('Agreement decision.\nR1-1000001\tCatalogue with Qualcomm title\tOther Co')[0],'Agreement decision.')
    captured = 'The agreement above is captured in:\nR1-1000001\tCR\tQualcomm\n(Rel-19, 38.213, X, Y, CR0001, Cat F) is agreed.'
    check('explicit_captured_header_retained',rule.own_record(captured)[0],captured)
    listed = 'Endorse following Tdocs:\nR1-1000001\tCR\tQualcomm\nR1-1000002\tCR\tOther'
    check('explicit_following_header_chain_retained',rule.own_record(listed)[0],listed)
    check('embedded_company_name_rejected',rule.company_in_source('NonQualcommVendor',company),False)
    check('canonical_alias_source_allowed',rule.company_in_source('Qualcomm Incorporated; Samsung',company),True)
    def headers(value):
        return rule.frozen_header_company_sources([{'resolutionId':'CONTROL_ONLY','content':value,'note':None}],company)
    check('company_in_title_not_Source_rejected',len(headers('R1-1000001\tQualcomm title\tOther Company')),0)
    check('exact_Tdoc_title_header_binding_available',('R1-1000001','Real title') in headers('R1-1000001\tReal title\tQualcomm Incorporated'),True)
    check('wrong_title_does_not_bind',('R1-1000001','Wrong title') in headers('R1-1000001\tReal title\tQualcomm Incorporated'),False)
    row8191 = next(r for r in matched if r['tdocNumber'] == 'R1-2508191')
    check('raw_current_Source_positive_8191',rule.company_in_source(row8191['Source'],company),True)
    check('8063_retained_header_changes_same_Agreement_representative',plain[4]['t.tdocNumber'],'R1-2508063')
    check('company_in_later_metadata_cell_rejected',len(headers('R1-1000001\tReal title\tOther Co\tQualcomm metadata')),0)
    check('explicit_split_Moderator_Source_continuation_retained',('R1-1000001','Real title') in headers('R1-1000001\tReal title\tModerator\t(Qualcomm Inc.)'),True)
    require(len(dependency) == 12 and all(c['pass'] for c in dependency), 'source dependency controls')
    native_index = read_json('native_capture_index.json')
    require(set(native_index['queries']) == {'full','rank','limited'}, 'all native query roles required')
    actual_native = {}
    execution = read_json(native_index['execution_receipt'])
    require(execution['inventory_unchanged'] and execution['source_before'] == execution['source_after'], 'native inventory changed')
    require(execution['source_before']['nodes'] == 165418 and execution['source_before']['relationships'] == 848228 and execution['model_calls'] == 0, 'native source inventory/model calls')
    protocol = read_json('native/execution_protocol.json')
    require(protocol['container_memory_bytes'] == protocol['python_address_space_limit_bytes'] == 2*1024**3 and protocol['container_cpu_cores'] == protocol['concurrent_containers'] == 1 and protocol['query_timeout_seconds'] == 20 and protocol['model_calls'] == 0, 'original native resource/timeout protocol')
    guard = read_json(native_index['guard_receipt'])
    require(guard['status'] == 'PASS' and guard['child_exit'] == 0 and guard['quality_rerolls'] == 0, 'native operational guard')
    require(guard['prestart_available_minimum_bytes'] == 26*1024**3 and guard['continuous_reserve_minimum_bytes'] == 16*1024**3, 'native guard thresholds')
    require(guard['owned_cleanup']['owned_stopped'] and guard['owned_cleanup']['common_lock_held'], 'native owned cleanup')
    require(min(guard['initial_memory']['Linux_available_bytes'],guard['initial_memory']['Windows_available_bytes']) >= 26*1024**3, 'native admission reserve')
    require(all(min(s['Linux_available_bytes'],s['Windows_available_bytes']) >= 16*1024**3 for s in guard['memory_samples']), 'native continuous reserves')
    for kind,item in native_index['queries'].items():
        rows,receipt = parse_native(item)
        expected = ranked if kind == 'rank' else plain if kind == 'full' else plain[:10]
        require(rows == expected, 'actual native full typed ordered values differ: '+kind)
        require(any(x['status'] == 'OK' and x['query_sha256'] == receipt['query_sha256'] and x['rows'] == len(rows) for x in execution['items']), 'native execution ledger incomplete')
        actual_native[kind] = {'rows':len(rows),'elapsed_s':receipt['elapsed_s'],'query_sha256':receipt['query_sha256']}
    binding = read_json(native_index['primary_binding'])
    require(binding['full534_exact_typed_ordered_equal'] and binding['Company_qualified9079_exact_equal'] and binding['SQLite_before'] == binding['SQLite_after'] == source_capture['DB_before'], 'primary native SQL/source binding absent')
    require(binding['actual_native10_ids'] == [r['a.resolutionId'] for r in plain[:10]], 'observed native10 replaced')
    primary = read_json('data/canonical_primary_review.json')
    require(primary['reviewer'] == 'main_D' and primary['reviewer_kind'] == 'nonblind_AI_primary' and primary['human_expert_n'] == 0 and len(primary['seven_unit_review']) == 7, 'primary seven-unit record')
    require(primary['criteria_sha256'] == manifest['criteria_sha256'] and primary['candidate_query_sha256'] == manifest['candidate_query_sha256'], 'primary criteria/definition differ')
    result = {'id':manifest['id'],'status':'PASS_PORTABLE_SOURCE_NATIVE_CAPTURE_AND_CONTROLS_PENDING_ROOT_SEMANTIC_SEAL','packet_pins_checked':len(inventory),'frozen_Agreement_inputs':len(agreements),'frozen_Tdoc_inputs':len(tdocs),'full534_native_and_fresh_SQL_typed_equal':True,'qualified_Tdocs':len(qualified),'original_source_records':len(census),'raw_source_blocks_checked':block_count,'raw_register_alias_Source_rows_checked':alias_rows,'own_raw_register_rows_checked':len(matched),'source_positive_Agreements':len(source_positive),'latest10_operative_role_bindings':role_count,'requested_output':'top10 Agreement identity set; native4 context preserved','requested_field_controls':len(controls),'source_dependency_controls':len(dependency),'actual_native':actual_native,'default_no_host_audit':audit,'native_calls_performed_here':0,'API_calls':0,'human_expert_n':0,'ROOT_final_semantic_seal_claimed':False}
    print(json.dumps(result,ensure_ascii=False))


if __name__ == '__main__':
    main()
