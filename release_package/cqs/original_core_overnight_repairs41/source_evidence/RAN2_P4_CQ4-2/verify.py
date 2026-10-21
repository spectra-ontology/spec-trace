#!/usr/bin/env python3
"""Replay the frozen approved-change metadata trace case without host files, network, or a model call.

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
INVENTORY_SHA256 = 'f80e0bda331237853573d8146634ff7cd1f98a070772bd52a8437988a789cbc9'
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


def parse_native(item):
    meta = read_json(item['meta'])
    raw = gzip.decompress(safe(HERE / item['rows']).read_bytes())
    values = [parse_json(line) for line in raw.splitlines()]
    require(all(type(r) is list and len(r)==3 and all(type(v) is str for v in r) for r in values), 'native typed three fields')
    rows = [dict(zip(meta['columns'],r)) for r in values]
    query = safe(HERE / item['query']).read_bytes()
    require(meta['id']=='RAN2_P4_CQ4-2' and meta['wg']=='RAN2' and meta['status']=='OK','actual native case/status')
    require(meta['query'].encode()==query and meta['query_sha256']==sha(query),'byte-exact native query')
    require(meta['columns']==['tdocNumber','reason','summary'],'requested native columns')
    require(meta['rows_retained']==len(rows)==item['rows_n'] and meta['bytes_retained']==len(raw) and meta['rows_sha256']==sha(raw),'complete retained native rows')
    require(meta['full_rows_available'] and not meta['truncated'] and meta['rollback_completed'] and meta['execution_summary_complete'],'native full output/rollback')
    require(meta['plan_query_type']==meta['execution_query_type']=='r' and meta['limits']['timeout_s']==20,'readonly EXPLAIN/execute20s')
    return rows,meta,raw


def main():
    audit=no_host_audit()
    require(sha(safe(HERE/'immutable_inventory.json').read_bytes())==INVENTORY_SHA256,'immutable inventory differs')
    inventory=read_json('immutable_inventory.json');manifest=read_json('manifest.json')
    require(manifest['files']==inventory and manifest['immutable_inventory_sha256']==INVENTORY_SHA256,'inventory declaration')
    actual=set()
    for path in HERE.rglob('*'):
        safe(path);mode=path.lstat().st_mode
        require(stat.S_ISREG(mode) or stat.S_ISDIR(mode),'nonregular payload')
        if stat.S_ISREG(mode):actual.add(path.relative_to(HERE).as_posix())
    require(actual==set(inventory)|{'manifest.json','immutable_inventory.json','verify.py'},'closed inventory mismatch')
    for name,pin in inventory.items():
        relative=Path(name)
        require(type(name)is str and name and '\\'not in name and not relative.is_absolute() and '..'not in relative.parts,'unsafe payload path')
        raw=safe(HERE/relative).read_bytes()
        require(len(raw)==pin['bytes'] and sha(raw)==pin['sha256'],'payload pin mismatch: '+name)
    require(sha(safe(HERE/'verify.py').read_bytes())==manifest['verifier_sha256'],'verifier differs')
    declarations=read_json('packet_declarations.json')
    require(set(manifest)==set(declarations)|{'files','immutable_inventory_sha256','verifier_sha256'},'manifest fields')
    require(all(manifest[k]==v for k,v in declarations.items()),'manifest scientific declarations')
    typed=local_module('typed_values');local_module('scorer');scorer=local_module('original_scorer')
    controls=local_module('contract_checks');review_schema=local_module('review_schema')
    requested=local_module('requested_controls');reader=local_module('binary_reader');style=local_module('binary_styles');source=local_module('source_replay')
    task=read_json('data/repair.json');original=read_json('authority/original.json');criteria=read_json('authority/criteria.json')
    require(task['id']==original['id']==manifest['id']=='RAN2_P4_CQ4-2','case identity')
    require(task['question_en']==original['question_en'] and task['original_query']==task['reference_query']==original['cypher'],'unchanged original EN/query')
    require(sha(task['question_en'].encode())==manifest['question_sha256'],'original EN SHA')
    require(len(task)==9 and sha(typed.json_exact(task).encode())==manifest['canonical_repair_sha256'],'canonical9 identity')
    require(sha((HERE/'authority/criteria.json').read_bytes())==manifest['criteria_sha256']=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4','fixed original7criteria')
    require([r['name']for r in task['required_fields']]==['tdocNumber','reason','summary'] and all(r['type']=='string' and r['nullable']is False for r in task['required_fields']),'three typed substantive answer roles')
    require(task['collection']=={'kind':'top_k_boundary_ties','value':5,'source_order_keys':[{'source_column':'tdocNumber','direction':'asc'}],'tie_policy':'any_subset_at_boundary','within_tie_order':'any','require_rank_order':False},'original ASC5 membership and unrequested serialization')
    primary=read_json('reviews/primary.json');secondary=read_json('reviews/secondary.json')
    for review in [primary,secondary]:
        review_schema.check_pass(review,task['question_en'],criteria['semantic_units'],criteria_sha=manifest['criteria_sha256'],identity_key='repair_sha256',identity_sha=manifest['canonical_repair_sha256'])
        require(review['nonblind']is True and review.get('human_expert_n',0)==0,'nonblind AI/human0 provenance')
    require(primary['reviewer']!=secondary['reviewer'] and secondary['reviewer']=='/root','distinct primary and independent ROOT secondary')
    require(secondary['source_replay']=='actual_ROOT_fresh_eight_archives_ten_fields_replay_v1.json','ROOT independent source receipt link')
    rootproof=read_json('reviews/ROOT_actual_source_replay.json');binding=read_json('reviews/main_D_actual_native_SQL_binding.json')
    require(rootproof['status']=='PASS' and binding['status'].startswith('PASS'),'actual ROOT source and native SQL binding')
    require(binding['SQLite_sha256_before']==binding['SQLite_sha256_after']==manifest['SQLite_sha256'],'fresh immutable SQL before/after')
    require(binding['full162_global_approval_classifier']is False,'finite source certification scope')
    frozen=read_json('data/full_frozen_input.json.gz')
    require(frozen['SQLite_sha256']==manifest['SQLite_sha256'],'frozen input database binding')
    crs=frozen['CR'];ags=frozen['Agreement'];refs=frozen['REFERENCES']
    require(len(crs)==34622 and len(ags)==3413 and len(refs)==2192,'full captured CR/Agreement/ref class input')
    require(len({r['node_id']for r in crs})==34622 and len({r['node_id']for r in ags})==3413,'original distinct node identities')
    bycr={r['node_id']:r for r in crs};byag={r['node_id']:r for r in ags}
    require(all(type(a)is int and type(c)is int and a in byag and c in bycr for a,c in refs),'original reference endpoint types')
    referenced={c for a,c in refs}
    population=sorted((r for r in crs if r['reasonForChange']is not None and r['node_id']in referenced),key=lambda r:r['tdocNumber'])
    full=[{'tdocNumber':r['tdocNumber'],'reason':r['reasonForChange'],'summary':r['summaryOfChange']}for r in population]
    require(len(full)==162 and len({r['tdocNumber']for r in full})==162,'DISTINCT CR node162 and actual unique tdoc keys')
    require(all(type(r[k])is str for r in full for k in ('tdocNumber','reason','summary')),'actual all162 three fields nonnull strings')
    require(sum(bycr[c]['reasonForChange']is not None for a,c in refs)==165,'retained raw path multiplicity165')
    cutoff=full[4]['tdocNumber'];prefix=[r for r in crs if r['tdocNumber']is not None and r['tdocNumber']<=cutoff]
    metadata=[r for r in prefix if r['reasonForChange']is not None];refprefix=[r for r in prefix if r['node_id']in referenced]
    require(len(prefix)==7127 and len(metadata)==104 and len(refprefix)==374,'unfiltered prefix7127, metadata104, referenced374')
    require(sum(r['reasonForChange']is None for r in prefix)==7023,'null metadata retained separately from empty source')
    require(len([r for r in metadata if r['node_id']in referenced])==5 and sum(r['tdocNumber']==cutoff for r in prefix)==1,'closed captured-source ASC5 frontier')
    targets={r['tdocNumber']:r['node_id']for r in metadata};matches=[];content_targets=set();note_targets=set()
    for a in ags:
        for field in ['content','note']:
            value=a[field] or ''
            for tid in sorted(set(re.findall(r'R2-\d{7}',value))&targets.keys()):
                exists=[a['node_id'],targets[tid]]in refs
                matches.append(dict(Agreement=a['resolutionId'],Agreement_node_id=a['node_id'],tdocNumber=tid,CR_node_id=targets[tid],field=field,existing_REFERENCES=exists))
                (content_targets if field=='content'else note_targets).add(tid)
    boundary=read_json('data/authority_reference_boundary.json')
    require(matches==boundary['content_and_note_matches'] and len(matches)==5 and all(r['existing_REFERENCES']for r in matches),'all3413 original body/note reference boundary exact replay')
    require(len(targets.keys()-content_targets-note_targets)==99 and not(note_targets-content_targets),'99 no mention and no hidden note-only earlier metadata target')
    require(all(len([r for r in full if r['tdocNumber']<cutoff])==4 for _ in [0]),'four before unique cutoff')
    for excerpt in boundary['excerpts']:
        lines=(HERE/'authority'/excerpt['file']).read_text().splitlines(keepends=True)
        value=''.join(lines[excerpt['first_line']-1:excerpt['last_line']])
        require(value==excerpt['text'] and sha(value.encode())==excerpt['sha256_utf8'],'original authority excerpt line/byte identity')
    captured={};metas={}
    for item in read_json('native/index.json'):
        rows,meta,raw=parse_native(item);captured[item['kind']]=rows;metas[item['kind']]=meta
        bound=next(r for r in binding['captures']if r['kind']==item['kind'])
        require(bound['metadata']['sha256']==sha((HERE/item['meta']).read_bytes()) and bound['retained_rows']['sha256']==sha(raw),'actual native/freshSQL proof pins')
    require(captured['full']==full and captured['limited']==full[:5],'all162 and selected5 exact three-field native/frozen equality')
    require((HERE/'queries/limited.cypher').read_bytes()==task['reference_query'].encode(),'exact canonical216B native query')
    execution=read_json('native/execution_RAN2.json');protocol=read_json('native/execution_protocol.json');guard=read_json('native/guard_receipt.json')
    require(execution['inventory_unchanged'] and execution['source_before']==execution['source_after'],'native source inventory unchanged')
    require(execution['source_before']['nodes']==156288 and execution['source_before']['relationships']==939037 and execution['source_before']['source']['sha256']==manifest['ttl_sha256'],'original archived graph inventory')
    require(execution['model_calls']==0 and len(execution['items'])==2 and all(i['status']=='OK'for i in execution['items']),'actual2 readonly native,0model')
    require(execution['input_sha256']==sha((HERE/'native/requested_input.jsonl').read_bytes()),'native input exact pin')
    inputs=[parse_json(line)for line in (HERE/'native/requested_input.jsonl').read_bytes().splitlines()if line.strip()]
    require(len(inputs)==2 and {i['query_sha256']for i in inputs}=={m['query_sha256']for m in metas.values()},'actual native exactly2 queries')
    require(all(i['candidate_query']==metas['limited'if i['query_sha256']==sha(task['reference_query'].encode())else'full']['query'] and i['query_sha256']==sha(i['candidate_query'].encode())for i in inputs),'native input query bytes exact')
    require(protocol['container_memory_bytes']==protocol['python_address_space_limit_bytes']==2*1024**3 and protocol['container_cpu_cores']==protocol['concurrent_containers']==1 and protocol['query_timeout_seconds']==20,'unchanged protocol2GiB/1CPU/20s')
    require(guard['status']=='PASS' and guard['child_exit']==0 and guard['quality_rerolls']==0,'actual native guard PASS')
    require(guard['prestart_available_minimum_bytes']==26*1024**3 and guard['continuous_reserve_minimum_bytes']==16*1024**3,'twohost26/16 guards')
    require(all(v>=26*1024**3 for k,v in guard['initial_memory'].items()if k.endswith('available_bytes')),'bothhost admission')
    require(all(s[k]>=16*1024**3 for s in guard['memory_samples']for k in ['Linux_available_bytes','Windows_available_bytes']),'continuous bothhost reserve')
    require(guard['owned_cleanup']['owned_stopped'] and guard['owned_cleanup']['common_lock_held'],'owned cleanup/commonlock')
    actual_controls=requested.run(task,full,scorer,controls)
    saved=read_json('data/actual_requested_controls.json')
    require(actual_controls['generic']==saved['generic_controls'],'actual generic controls equality')
    require([dict(check=r['check'],**{'pass':r['pass_']},expected_exact=r['expected_exact'],result=r['result'])for r in actual_controls['requested']]==saved['requested_role_controls'],'same12 actual role controls')
    source_counts=source.run(HERE,read_json('sources/index.json'),read_json('data/source_fields10.json.gz'),read_json('data/source_active_approval5.json.gz'),read_json('data/source_strike_counterreading.json.gz'),rootproof,full[:5],reader,style)
    require(all(audit[k]==0 for k in ['network_calls','subprocess_calls','SQL_calls','host_private_open_attempts','write_open_attempts']),'default nohost audit')
    print(json.dumps(dict(status='PASS',id=task['id'],native_counts=[162,5],source_reopened=source_counts,
        captured_input_counts=[34622,3413,2192],frontier_counts=[7127,104,374,5],requested_role_controls=actual_controls['n'],
        distinct_nonblind_AI_reviews=2,semantic_units=7,human_n=0,model_calls=0,ROOT_final_seal_included=False,no_host_audit=audit),ensure_ascii=False))


if __name__=='__main__':main()
