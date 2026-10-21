#!/usr/bin/env python3
"""Replay the frozen Agreement CR-approval trace case without host files, network, or a model call.

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
INVENTORY_SHA256 = '2f66cb5b8f7460242000ba25324afecf88b439b098fb174575e03cc7d31672aa'
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


def source_replay(proof, matrix, population):
    fmt=local_module('source_format')
    # The source helper is the exact fresh XML/style projection used by the primary.
    report, block=fmt.load_doc(HERE/'original_report115.docx')
    require(report==proof['report'],'report bytes/XML/styles and inherited strike')
    for row in proof['own16']:
        g=row['original_geometry']
        actual=[block(i) for i in range(g['marker_raw_body_child0'],g['exclusive_raw_body_end0'])]
        require(actual==row['source_blocks'],'actual own16 source/XML/style replay')
    for row in proof['external6']:
        meta,getblock=fmt.load_doc(HERE/row['source']['path']['path'])
        require(meta==row['source'],'external CR proposal source/XML/style bytes')
        require([getblock(b['body_child0']) for b in row['source_blocks']]==row['source_blocks'],'actual external6 roles/XML/style replay')
    with zipfile.ZipFile(HERE/'original_report115.docx') as z:
        blocks=list(ET.fromstring(z.read('word/document.xml')).find(W+'body'))
    byid={r['resolutionId']:r for r in population}
    for row in matrix['rows']:
        require(byid[row['resolutionId']]['content']==row['original_content'],'source/frozen original full content')
        require(sha(row['original_content'].encode())==row['original_content_sha256'],'own content digest')
        for b in row['source_blocks']:
            el=blocks[b['raw_body_child0']]
            actual=dict(raw_body_child0=b['raw_body_child0'],kind=el.tag.split('}')[-1],
                        style=el.find(W+'pPr/'+W+'pStyle').get(W+'val') if el.find(W+'pPr/'+W+'pStyle') is not None else None,
                        text=''.join(n.text or '' for n in el.iter(W+'t')),
                        OMML_n=len(list(el.iter('{'+NS['m']+'}oMath'))),
                        strike_runs_n=sum(r.find(W+'rPr/'+W+'strike') is not None for r in el.iter(W+'r')),
                        deleted_text=[n.text for n in el.iter(W+'delText')])
            require(actual==b,'all55 original block text/geometry/removed-text replay')
    require(proof['selected_n']==15 and proof['excluded_strong_counterwitness']=='AGR-115-8.11.2-001','source scope')
    return dict(own16=16,external6=6,all55=55)


def parse_native(item):
    meta=read_json(item['meta']);raw=gzip.decompress(safe(HERE/item['rows']).read_bytes())
    positional=[parse_json(line) for line in raw.splitlines() if line.strip()]
    cols=item['columns'];require(all(type(r)is list and len(r)==len(cols) for r in positional),'native shape')
    rows=[dict(zip(cols,r)) for r in positional];query=safe(HERE/item['query']).read_bytes()
    require(meta['status']=='OK' and meta['id']=='RAN1_P2_CQ2-3' and meta['wg']=='RAN1','native identity/status')
    require(meta['query'].encode()==query and meta['query_sha256']==sha(query),'exact native query bytes')
    require(meta['columns']==cols and meta['rows_retained']==len(rows)==item['rows_n'],'native columns/count')
    require(meta['rows_sha256']==sha(raw) and meta['bytes_retained']==len(raw),'native full retained bytes')
    require(meta['full_rows_available'] and not meta['truncated'] and meta['execution_summary_complete'] and meta['rollback_completed'],'native full rows/rollback')
    require(meta['plan_query_type']==meta['execution_query_type']=='r','native readonly EXPLAIN/execute')
    for r in rows:
        require(type(r['a.resolutionId']) is str and type(r['a.content']) is str,'native context fields typed')
        if '__source_order_sequence'in r:require(type(r['__source_order_sequence'])is int,'native sequence integer')
    return rows,meta


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
    controls=local_module('contract_checks');review_schema=local_module('review_schema');rule=local_module('frozen_rule')
    task=read_json('data/repair.json');original=read_json('authority/original_selected_row.json');criteria=read_json('authority/criteria.json')
    require(task['id']==original['id']==manifest['id']=='RAN1_P2_CQ2-3','case identity')
    require(task['question_en']==original['question_en'] and task['original_query']==original['cypher'],'original EN/query')
    require(sha(task['question_en'].encode())==manifest['question_sha256'],'original EN SHA')
    require(len(task)==9 and sha(typed.json_exact(task).encode())==manifest['canonical_repair_sha256'],'canonical9 identity')
    require(sha((HERE/'authority/criteria.json').read_bytes())==manifest['criteria_sha256']=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4','fixed7criteria')
    require(len(task['required_fields'])==1 and task['required_fields'][0]['name']=='a.resolutionId' and task['required_fields'][0]['type']=='string' and task['required_fields'][0]['nullable']is False,'requested typed Agreement identity')
    require(task['collection']=={'kind':'top_k_boundary_ties','value':15,'source_order_keys':[{'source_column':'__source_order_sequence','direction':'asc'},{'source_column':'a.resolutionId','direction':'asc'}],'tie_policy':'any_subset_at_boundary','within_tie_order':'any','require_rank_order':False},'original membership order/bound15 and unrequested serialization')
    primary=read_json('reviews/primary.json');secondary=read_json('reviews/secondary.json')
    for review in [primary,secondary]:
        review_schema.check_pass(review,task['question_en'],criteria['semantic_units'],criteria_sha=manifest['criteria_sha256'],identity_key='repair_sha256',identity_sha=manifest['canonical_repair_sha256'])
        require(review['nonblind']is True,'nonblind AI provenance')
        require(review.get('human_n',review.get('human_expert_n',0))==0,'human0')
    require(primary['reviewer']!=secondary['reviewer'] and secondary['reviewer']=='/root','distinct primary/ROOT secondary')
    rootproof=read_json('reviews/ROOT_actual_source_native_SQL_proof.json')
    require(rootproof['status'].startswith('PASS'),'ROOT actual proof status')
    require(secondary['independent_actual_proof']['sha256']==sha((HERE/'reviews/ROOT_actual_source_native_SQL_proof.json').read_bytes()),'secondary/actual independent ROOT proof pin')
    require(primary['repair_file_sha256']==secondary['repair_file_sha256']==sha((HERE/'data/repair.json').read_bytes()),'both reviews/canonical file pin')
    require(rootproof['repair']['sha256']==sha((HERE/'data/repair.json').read_bytes()) and rootproof['definition']['sha256']==sha((HERE/'data/frozen_definition.json').read_bytes()),'ROOT proof/canonical scientific definition pins')
    require(rootproof['immutable_SQL_before_after']['sha256']==manifest['SQLite_sha256'],'ROOT independent immutable SQL pin')
    require(rootproof['source_role_matrix']['sha256']==sha(gzip.decompress((HERE/'data/all55_source_matrix.json.gz').read_bytes())),'ROOT independent original55 judgment pin')
    require(rootproof['source_XML_style_evidence']['sha256']==sha(gzip.decompress((HERE/'data/selected15_plus_TP1_source_style_proof.json.gz').read_bytes())),'ROOT independent selected source/style pin')
    require(rootproof['native_guard']['sha256']==sha((HERE/'native/guard_receipt.json').read_bytes()),'ROOT actual native guard pin')
    require(rootproof['full_population']==357 and rootproof['full_lexical_selection_rows']==156 and rootproof['actual_reopened_source_documents']==7 and rootproof['actual_own_source_fragments']==16 and rootproof['actual_external_CR_object_fragments']==6,'ROOT independently reopened full dependency/source scope')
    require(rootproof['XML_active_and_removed_text_independently_recomputed']is True and rootproof['strong_TP1_counterwitness_preserved']is True,'ROOT independent active/removed text and strong opposition')
    require(rootproof['human_expert_n']==0 and rootproof['new_paid_calls']==0,'ROOT independent provenance')
    patterns=read_json('data/regex_parameters.json');queries=rule.queries(patterns)
    for name,q in queries.items():require(safe(HERE/('queries/'+name+'.cypher')).read_bytes()==q.encode(),'exact rule/Cypher:'+name)
    require(task['reference_query'].encode()==safe(HERE/'queries/limited.cypher').read_bytes(),'canonical exact limited query')
    population=read_json('data/population357.json.gz');require(len(population)==357,'full original357')
    require(len({r['resolutionId']for r in population})==357,'distinct original357 Agreement identities')
    require(all(type(r['resolutionId'])is str and type(r['sequence'])is int and type(r['content'])is str for r in population),'population types')
    ordered=sorted(population,key=lambda r:(r['sequence'],r['resolutionId']))
    require(population==ordered and len({(r['sequence'],r['resolutionId'])for r in population})==357,'original ordered357/unique pairs')
    full,limited=rule.replay(population,patterns)
    require(len(full)==156 and len(limited)==15,'retained lexical156/selected15')
    require(full==read_json('data/fresh_SQL_full156_with_source_order.json.gz') and limited==read_json('data/fresh_SQL_selected15_context.json.gz'),'actual immutable SQL/pure rule full typed equality')
    matrix=read_json('data/all55_source_matrix.json.gz');rows=matrix['rows']
    require(len(rows)==55 and [r['resolutionId']for r in rows]==[r['resolutionId']for r in population[:55]],'original unfiltered first55')
    for i,r in enumerate(rows,1):
        require(r['raw357_rank1']==i and r['sequence']==1,'raw55 source order')
        require(type(r['independent_source_eligibility'])is bool,'source judgment missing')
        require(r['independent_source_eligibility']==rule.eligible(r['original_content'],patterns)==r['generic_retained_query_includes'],'source/judgment/query comparison')
    require(sum(r['independent_source_eligibility']for r in rows)==17,'source17positive/38other')
    prefix=rows[:44];sourceids=[r['resolutionId']for r in prefix if r['independent_source_eligibility']]
    require(len(sourceids)==15 and sourceids==[r['a.resolutionId']for r in limited],'all44 source-closed first15')
    require(rows[15]['independent_source_eligibility']is False and rows[43]['independent_source_eligibility']is True,'strong excludedTP1/actual CR-form entrant44')
    cutoff=(limited[-1]['__source_order_sequence'],limited[-1]['a.resolutionId'])
    require(sum((r['sequence'],r['resolutionId'])<=cutoff for r in population)==44 and sum((r['sequence'],r['resolutionId'])==cutoff for r in population)==1,'unfiltered prefix44/unique cutoff')
    require(matrix['broadpool156_is_selection_diagnostic_not_globally_certified_CR_classifier']is True,'bounded lexical diagnostic scope')
    source_counts=source_replay(read_json('data/selected15_plus_TP1_source_style_proof.json.gz'),matrix,population)
    captured={};metas={}
    for item in read_json('native/index.json'):captured[item['kind']],metas[item['kind']]=parse_native(item)
    require(captured['rank']==full,'actual native rank156/pure rule/freshSQL typed equality')
    context=lambda rs:[{'a.resolutionId':r['a.resolutionId'],'a.content':r['a.content']}for r in rs]
    require(captured['full']==context(full) and captured['limited']==context(limited),'native full156 and limited15 context equality')
    require(metas['limited']['query']==task['reference_query'],'actual native canonical bytes exact')
    for name in ['rank','full','limited']:
        bound=rootproof['complete_typed_native_comparisons'][name]
        require(bound['query']['sha256']==sha((HERE/('queries/'+name+'.cypher')).read_bytes()),'ROOT exact query pin:'+name)
        require(bound['metadata']['sha256']==sha((HERE/('native/'+name+'.json')).read_bytes()),'ROOT actual native metadata pin:'+name)
        require(bound['full_rows']['sha256']==sha(gzip.decompress((HERE/('native/'+name+'.jsonl.gz')).read_bytes())),'ROOT actual native row-byte pin:'+name)
        require(bound['rows']==len(captured[name]),'ROOT actual native full count:'+name)
    execution=read_json('native/execution_RAN1.json');protocol=read_json('native/execution_protocol.json');guard=read_json('native/guard_receipt.json')
    require(execution['inventory_unchanged'] and execution['source_before']==execution['source_after'],'native frozen inventory unchanged')
    require(execution['model_calls']==0 and len(execution['items'])==3 and all(i['status']=='OK'for i in execution['items']),'actual3readonly/native0model')
    require(execution['input_sha256']==sha((HERE/'native/requested_input.jsonl').read_bytes()),'actual capture exact requested input pin')
    inputs=[parse_json(line)for line in (HERE/'native/requested_input.jsonl').read_bytes().splitlines()if line.strip()]
    require(len(inputs)==3 and {i['query_sha256']for i in inputs}=={sha(q.encode())for q in queries.values()},'original exact3 native input queries')
    require(all(i['query_sha256']==sha(i['candidate_query'].encode()) and i['candidate_query']in queries.values()for i in inputs),'native inputs exact UTF8 source query')
    require({i['query_sha256']for i in execution['items']}=={i['query_sha256']for i in inputs},'native actual execution items bind all3 original inputs')
    require(execution['source_before']['source']['sha256']==manifest['ttl_sha256'],'TTL inventory pin')
    require(protocol['container_memory_bytes']==protocol['python_address_space_limit_bytes']==2*1024**3 and protocol['container_cpu_cores']==protocol['concurrent_containers']==1 and protocol['query_timeout_seconds']==20,'unchanged execution protocol')
    require(guard['status']=='PASS'and guard['child_exit']==0 and guard['quality_rerolls']==0,'actual native guard')
    require(guard['prestart_available_minimum_bytes']==26*1024**3 and guard['continuous_reserve_minimum_bytes']==16*1024**3,'twohost memory26/16')
    require(all(v>=26*1024**3 for k,v in guard['initial_memory'].items()if k.endswith('available_bytes')),'actual twohost admission')
    require(all(s[k]>=16*1024**3 for s in guard['memory_samples']for k in ['Linux_available_bytes','Windows_available_bytes']),'actual continuous reserve')
    require(guard['owned_cleanup']['owned_stopped'] and guard['owned_cleanup']['common_lock_held'],'owned cleanup/commonlock')
    projected=[{'a.resolutionId':r['a.resolutionId']}for r in full];groups=scorer.make_order_groups(task,captured['rank'],projected)
    checked=controls.checks(task,projected,groups);require(all(c['pass']for c in checked),'requested-field negative controls')
    prediction=scorer.reference_prediction(task,projected)
    more=[(list(reversed(prediction)),True),(prediction[:-1]+[{'a.resolutionId':'AGR-115-8.11.2-001'}],False),(prediction[:-1],False),(prediction[:-1]+[projected[15]],False),([dict(r,**{'a.content':None})for r in prediction],True)]
    for p,want in more:require(scorer.score(task,projected,p,diagnostic=True,order_groups=groups)['exact']is want,'identity/boundary/source-role control')
    require(all(audit[k]==0 for k in ['network_calls','subprocess_calls','SQL_calls','host_private_open_attempts','write_open_attempts']),'nohost audit')
    print(json.dumps(dict(status='PASS',id=task['id'],scope='Original Agreement CR-proposal approval trace: source-certified first15 from full original prefix44, additional55-role review; later lexical156 diagnostic only',native_counts=[156,156,15],source_reopened=source_counts,requested_role_controls=len(checked)+len(more),distinct_nonblind_AI_reviews=2,semantic_units=7,human_n=0,model_calls=0,ROOT_final_seal_included=False,no_host_audit=audit),ensure_ascii=False))


if __name__=='__main__':main()
