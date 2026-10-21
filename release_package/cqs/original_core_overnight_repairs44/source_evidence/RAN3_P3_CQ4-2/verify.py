#!/usr/bin/env python3
"""Replay the bounded original RAN3 approval-provenance case without host files, network, or a model call.

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
INVENTORY_SHA256 = 'c184b9a406514a74fa4b8081b764652c225cc53e68681ec8fb47a93de2ce114e'
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
      "m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}
W = "{" + NS["w"] + "}"
TEXT_TAGS = {W + "t", "{" + NS["m"] + "}t"}

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


def bag(rows):
    return collections.Counter(tuple((k,type(v).__name__,v)for k,v in sorted(r.items()))for r in rows)


def native(item):
    meta=read_json(item['meta'])
    raw=gzip.decompress(safe(HERE/item['rows']).read_bytes())
    arrays=[parse_json(line)for line in raw.splitlines()]
    require(all(type(r)is list and len(r)==2 and all(type(v)is str for v in r)for r in arrays),'native two nonnull string fields')
    columns=['r.resolutionId','cr.tdocNumber']
    require(meta['id']=='RAN3_P3_CQ4-2' and meta['wg']=='RAN3' and meta['status']=='OK' and meta['columns']==columns,'native case and field roles')
    query=safe(HERE/item['query']).read_bytes()
    require(meta['query'].encode()==query and meta['query_sha256']==sha(query),'exact query UTF8 bytes')
    require(meta['rows_retained']==len(arrays)==item['rows_n'] and meta['bytes_retained']==len(raw) and meta['rows_sha256']==sha(raw),'complete full rows pin')
    require(meta['full_rows_available'] and not meta['truncated'] and meta['rollback_completed'] and meta['execution_summary_complete'],'full read-only capture/rollback')
    require(meta['plan_query_type']==meta['execution_query_type']=='r' and meta['limits']['timeout_s']==20,'read-only EXPLAIN/execute20s')
    rows=[dict(zip(columns,r))for r in arrays]
    require(all(a[columns[0]]>=b[columns[0]]for a,b in zip(rows,rows[1:])),'original ResolutionID DESC selection')
    return rows,meta,raw


def main():
    audit=no_host_audit()
    require(sha(safe(HERE/'immutable_inventory.json').read_bytes())==INVENTORY_SHA256,'immutable inventory differs')
    inventory=read_json('immutable_inventory.json');manifest=read_json('manifest.json')
    require(manifest['files']==inventory and manifest['immutable_inventory_sha256']==INVENTORY_SHA256,'inventory declaration')
    actual=set()
    for p in HERE.rglob('*'):
        safe(p);mode=p.lstat().st_mode
        require(stat.S_ISREG(mode)or stat.S_ISDIR(mode),'nonregular payload')
        if stat.S_ISREG(mode):actual.add(p.relative_to(HERE).as_posix())
    require(actual==set(inventory)|{'manifest.json','immutable_inventory.json','verify.py'},'closed inventory mismatch')
    for name,pin in inventory.items():
        relative=Path(name)
        require(type(name)is str and name and '\\'not in name and not relative.is_absolute()and'..'not in relative.parts,'unsafe payload path')
        raw=safe(HERE/relative).read_bytes()
        require(len(raw)==pin['bytes']and sha(raw)==pin['sha256'],'payload pin mismatch: '+name)
    require(sha(safe(HERE/'verify.py').read_bytes())==manifest['verifier_sha256'],'verifier differs')
    declarations=read_json('packet_declarations.json')
    require(set(manifest)==set(declarations)|{'files','immutable_inventory_sha256','verifier_sha256'},'manifest fields')
    require(all(manifest[k]==v for k,v in declarations.items()),'manifest scientific declarations')
    typed=local_module('typed_values');local_module('scorer');scorer=local_module('original_scorer')
    controls=local_module('contract_checks');review_schema=local_module('review_schema')
    requested=local_module('requested_controls');binaryreader=local_module('binary_reader');binarystyles=local_module('binary_styles');xmlreader=local_module('original_ooxml_reader');source=local_module('source_replay')
    task=read_json('data/repair.json');original=read_json('authority/original.json');criteria=read_json('authority/criteria.json')
    require(task['id']==original['id']==manifest['id']=='RAN3_P3_CQ4-2','case identity')
    require(task['question_en']==original['question_en']and task['original_query']==original['cypher'],'original question/query preserved')
    require(sha(task['question_en'].encode())==manifest['question_sha256'],'original EN bytes')
    require(set(task)=={'id','question_en','original_query','reference_query','required_fields','collection','cardinality_policy','repair_class','original_question_preserved'},'established canonical nine keys')
    require(sha(typed.json_exact(task).encode())==manifest['canonical_repair_sha256'],'canonical repair semantic pin')
    require(sha((HERE/'authority/criteria.json').read_bytes())==manifest['criteria_sha256']=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4','fixed7criteria')
    require(task['required_fields']==[{'name':'resolutionId','type':'string','nullable':False,'source_column_or_expression':'r.resolutionId'}],'original requested Resolution identity role')
    require(task['collection']=={'kind':'set'}and task['cardinality_policy']=={'mode':'exact','value':6},'six requested identities without unrequested serialization')
    require(task['repair_class']=='query_and_scorer'and task['original_question_preserved']is True,'question-preserving query repair')
    authority=read_json('authority/spans.json')
    require(authority['question_en']==task['question_en']and authority['original_query']==task['original_query'],'original authority question/query')
    for context in authority['preserved_contexts']:
        name=Path(context['file']['path']).name
        raw=safe(HERE/'authority'/name).read_bytes()
        require(sha(raw)==context['file']['sha256']and len(raw)==context['file']['bytes'],'preserved authority full bytes')
        lines=raw.decode().splitlines()
        for span in context['spans']:
            text='\n'.join(lines[span['start_line']-1:span['end_line']])
            require(text==span['text']and sha(text.encode())==span['UTF8_sha256'],'original authority exact line/text SHA')
    primary=read_json('reviews/primary.json');secondary=read_json('reviews/secondary.json')
    for review in [primary,secondary]:
        review_schema.check_pass(review,task['question_en'],criteria['semantic_units'],criteria_sha=manifest['criteria_sha256'],identity_key='repair_sha256',identity_sha=manifest['canonical_repair_sha256'])
        require(review.get('human_expert_n',review.get('expert_validation_n',0))==0,'AI/human0 provenance')
    require(primary['reviewer']!=secondary['reviewer'],'distinct primary and secondary reviewers')
    require(manifest['review_provenance']=={'distinct_AI_reviewers':2,'nonblind':True,'human_expert_n':0},'review scope')
    sql=read_json('data/SQL_receipt.json');rows=read_json('data/frozen617.json.gz')
    require(sql['status']=='PASS_READONLY_SQL_FULL125_SELECTED10_TWO_COLUMNS_AND_BOUNDED_SOURCE35'and sql['DB_before']==sql['DB_after'],'actual immutable SQL provenance')
    require(sql['DB_before']['sha256']==manifest['SQLite_sha256'],'frozen SQLite pin')
    require(len(rows)==617 and len({r['resolutionId']for r in rows})==104,'all original617 paths/104 Resolution identities')
    require(all(type(r['resolutionId'])is str and type(r['tdocNumber'])is str and r['specNumber']=='38.423'and type(r['content'])is str for r in rows),'frozen source fields and target MODIFIES domain')
    require(all(a['resolutionId']>=b['resolutionId']for a,b in zip(rows,rows[1:])),'original ordered full domain')
    prefix,suffix=sql['regex_prefix'],sql['regex_suffix']
    def lit(s):return "'"+s.replace('\\','\\\\').replace("'","\\'")+"'"
    reference="MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.423'}) WHERE r.content =~ ("+lit(prefix)+' + cr.tdocNumber + '+lit(suffix)+') RETURN r.resolutionId, cr.tdocNumber ORDER BY r.resolutionId DESC LIMIT 10'
    require(reference==task['reference_query']and(HERE/'queries/limited.cypher').read_bytes()==reference.encode(),'exact generic query reconstruction and canonical bytes')
    eligible=[r for r in rows if re.fullmatch(prefix+r['tdocNumber']+suffix,r['content'])]
    project=lambda rs:[{'r.resolutionId':r['resolutionId'],'cr.tdocNumber':r['tdocNumber']}for r in rs]
    full=project(eligible);selected=full[:10]
    require(len(full)==125 and len({r['r.resolutionId']for r in full})==54,'full125 predicate/query diagnostics')
    require(full==read_json('data/expected_full125.json')and selected==read_json('data/expected_selected10.json'),'full125/selected10 SQL two-field parity')
    require((HERE/'queries/full.cypher').read_bytes()==reference.removesuffix(' LIMIT 10').encode(),'full diagnostic query exact bytes')
    cut=selected[-1]['r.resolutionId'];frontier=[r for r in rows if r['resolutionId']>=cut]
    require(cut=='CON-121bis-23.1-001'and len(frontier)==35 and len({r['resolutionId']for r in frontier})==10,'unfiltered pre-cutoff frontier35/10')
    require(sum(r['resolutionId']>cut for r in eligible)==9 and sum(r['resolutionId']==cut for r in eligible)==1 and eligible[10]['resolutionId']<cut,'closed first10 membership; no unreviewed cutoff tie')
    stored_frontier=read_json('data/frontier35.json')
    require([(r['resolutionId'],r['tdocNumber'])for r in frontier]==[(r['resolutionId'],r['tdocNumber'])for r in stored_frontier],'raw frontier before eligibility')
    require(all(bool(re.fullmatch(prefix+r['tdocNumber']+suffix,r['content']))==s['generic_positive']for r,s in zip(frontier,stored_frontier)),'frozen same-CR event labels exactly recomputed')
    replay=source.run(HERE/'sources',read_json('data/original_source_index.json'),stored_frontier,rows,xmlreader,binaryreader,binarystyles)
    expected_source=read_json('data/source35.json.gz')
    require(replay==expected_source,'original2OOXML+RTF+CFB active35 and267 header source replay')
    require(replay['counts']=={'prefix_paths':35,'retained_bodies':10,'full_header_bindings':267,'positive_paths':10,'negative_own_paths':15,'reference_only_paths':10},'all bounded source roles')
    require(replay['original_format_counts']==manifest['original_format_counts']=={'OOXML':2,'RTF':1,'CFB':1},'original formats, converted DOCX not original authority')
    require(replay['converted_DOCX_used_as_original_authority']is False,'source derivation labels')
    archived=read_json('data/original_archive_source35.json.gz')
    require(archived['rows']==replay['rows']and archived['body_bindings']==replay['body_bindings']and archived['counts']==replay['counts'],'necessary-member extraction equals actual original archive source replay')
    require(manifest['original_archive_bytes_included']is False and manifest['register_payload']=={'header_rows':1,'selected_rows':10,'exact_sharedStrings_fragments':173},'minimal report/register public source payload')
    ids=[{'resolutionId':v}for v in sorted({r['r.resolutionId']for r in selected})]
    require(len(ids)==6 and ids==read_json('data/requested_set6.json'),'actual first10 path→six requested identities')
    actual_controls=requested.run(task,ids,replay['rows'],prefix,suffix,scorer,controls)
    saved=read_json('data/scoring_controls.json')
    require(all(actual_controls[k]==saved[k]for k in ['generic_controls','requested_role_controls','source_event_controls','total_controls_n']),'unchanged7 typed+9 role+8 source-event controls')
    captured={};metas={}
    for item in read_json('native/index.json'):
        native_rows,meta,raw=native(item);captured[item['kind']]=native_rows;metas[item['kind']]=meta
    require(set(captured)=={'full','limited'}and bag(captured['full'])==bag(full)and bag(captured['limited'])==bag(selected),'actual native full125 and canonical limited10 typed two-field equality')
    execution=read_json('native/execution_RAN3.json');protocol=read_json('native/execution_protocol.json');guard=read_json('native/guard_receipt.json')
    require(execution['inventory_unchanged']and execution['source_before']==execution['source_after'],'native frozen inventory unchanged')
    require(execution['source_before']['source']['sha256']==manifest['ttl_sha256']=='d9791c08773a0e38b89869b3882d3098d879a37ddd7109630c346200d6776e95','original archived RAN3 TTL identity')
    require(execution['model_calls']==0 and len(execution['items'])==2 and all(i['status']=='OK'for i in execution['items']),'actual2 read-only native,0model')
    require(execution['input_sha256']==sha((HERE/'native/requested_input.jsonl').read_bytes()),'actual native input pin')
    inputs=[parse_json(line)for line in(HERE/'native/requested_input.jsonl').read_bytes().splitlines()if line.strip()]
    require(len(inputs)==2 and {i['query_sha256']for i in inputs}=={m['query_sha256']for m in metas.values()}and all(i['query_sha256']==sha(i['candidate_query'].encode())for i in inputs),'exact two native input queries')
    require(protocol['container_memory_bytes']==protocol['python_address_space_limit_bytes']==2*1024**3 and protocol['container_cpu_cores']==protocol['concurrent_containers']==1 and protocol['query_timeout_seconds']==20,'original2GiB/1CPU/20s protocol')
    require(guard['status']=='PASS'and guard['child_exit']==0 and guard['quality_rerolls']==0,'actual guarded native PASS')
    require(guard['prestart_available_minimum_bytes']==26*1024**3 and guard['continuous_reserve_minimum_bytes']==16*1024**3,'dualhost26/16GiB guards')
    require(all(v>=26*1024**3 for k,v in guard['initial_memory'].items()if k.endswith('available_bytes')),'bothhost admission')
    require(all(s[k]>=16*1024**3 for s in guard['memory_samples']for k in ['Linux_available_bytes','Windows_available_bytes']),'continuous bothhost reserve')
    require(guard['owned_cleanup']['owned_stopped']and guard['owned_cleanup']['common_lock_held'],'owned cleanup/commonlock')
    binding=read_json('reviews/main_D_native_SQL_binding.json');rootproof=read_json('reviews/ROOT_actual_source_SQL_native.json')
    require(binding['status'].startswith('PASS')and rootproof['status'].startswith('PASS'),'actual main/independent ROOT source SQL native receipts')
    source_index=read_json('data/original_source_index.json');extraction=read_json('data/source_extraction_bridge.json')
    require(extraction['status']=='PASS_ACTUAL_ORIGINAL_ARCHIVES_TO_MINIMAL_SOURCE_PAYLOAD_EXACT_BYTES'and len(extraction['entries'])==5 and all(e['byteexact']for e in extraction['entries']),'actual minimum-source exact-byte provenance')
    require(extraction['participants_payload_included']is False and extraction['whole_register_included']is False,'minimum source payload scope')
    reopened={(r['archive']['sha256'],r['member_sha256'],r['member_bytes'])for r in rootproof['originals_reopened']}
    require(all((i['archive_sha256'],i['member_sha256'],i['member_bytes'])in reopened for i in source_index),'all public original source pins joined to independent ROOT fresh archives')
    require(manifest['source_certification']=={'raw_prefix_paths':35,'Resolution_bodies':10,'original_reports':4,'selected_approved_paths':10,'requested_Resolution_ids':6,'global125_approval_certified':False},'bounded source certification scope')
    require(all(audit[k]==0 for k in ['network_calls','subprocess_calls','SQL_calls','host_private_open_attempts','write_open_attempts']),'default no-host audit')
    print(json.dumps({'status':'PASS','id':task['id'],'original_paths':617,'native_counts':[125,10],'source_frontier_paths':35,'source_body_contexts':10,'source_header_bindings':267,'source_approved_selected_paths':10,'requested_identity_set_n':6,'controls_n':24,'distinct_nonblind_AI_reviewers':2,'human_n':0,'model_calls':0,'ROOT_final_seal_included':False,'no_host_audit':audit},ensure_ascii=False))


if __name__=='__main__':main()


