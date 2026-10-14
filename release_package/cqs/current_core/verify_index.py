#!/usr/bin/env python3
"""Verify every current ID, exact question and referenced frozen definition."""
from collections import Counter
import hashlib
import json
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):return [json.loads(line) for line in p.read_text().splitlines() if line]
def main():
    here=Path(__file__).resolve().parent;root=here.parents[2]
    manifest=json.loads((here/'index_manifest.json').read_text())
    for name,digest in manifest['files'].items():
        assert sha(here/name)==digest
    originals={r['id']:r for r in rows(root/'release_package/cqs/original_core_repair/provenance/original_benchmark.jsonl')}
    parent=root/'release_package/cqs/original_core_repair'
    parent_manifest=json.loads((parent/'manifest.json').read_text())
    parent_ledger=rows(parent/'all_core_dispositions.jsonl')
    assert sha(parent/'all_core_dispositions.jsonl')==parent_manifest['files']['all_core_dispositions.jsonl']
    assert manifest['source_snapshot']==parent_manifest['graph_sources']
    tasks=rows(here/'current_tasks.jsonl');ledger=rows(here/'all_core_dispositions.jsonl')
    assert len(ledger)==560 and len(tasks)==manifest['repaired_n']
    assert {r['id'] for r in ledger} <= set(originals)
    assert len({r['id'] for r in ledger})==560 and len({r['id'] for r in tasks})==manifest['repaired_n']
    assert {r['id'] for r in ledger}=={r['id'] for r in parent_ledger}
    frozen={};gold={}
    for scope,digest in manifest['cohort_manifest_pins'].items():
        bundle=root/'release_package/cqs'/scope
        assert sha(bundle/'manifest.json')==digest
        bm=json.loads((bundle/'manifest.json').read_text())
        for name in ['tasks.jsonl','reference_gold.jsonl']:
            assert sha(bundle/name)==bm['files'][name]
        frozen[scope]={r['id']:r for r in rows(bundle/'tasks.jsonl')}
        gold[scope]={r['id']:r for r in rows(bundle/'reference_gold.jsonl')}
    for t in tasks:
        scope=Path(t['bundle']).name;source=frozen[scope][t['id']];g=gold[scope][t['id']]
        assert t['bundle']=='release_package/cqs/'+scope
        assert t['bundle_manifest_sha256']==manifest['cohort_manifest_pins'][scope]
        assert t['question_en']==source['question_en']==originals[t['id']]['question_en']
        assert t['original_question_sha256']==hashlib.sha256(t['question_en'].encode()).hexdigest()
        original_query=originals[t['id']]['cypher']
        assert source['original_query']==original_query
        assert source['original_query_sha256']==hashlib.sha256(original_query.encode()).hexdigest()
        assert source['reference_query_sha256']==hashlib.sha256(source['reference_query'].encode()).hexdigest()
        actual_class='scorer_only' if source['reference_query']==original_query else 'query_and_scorer'
        assert t['repair_class']==source['repair_class']==actual_class
        assert t['repair_sha256']==source['repair_sha256']==g['repair_sha256']
        assert t['required_fields']==source['required_fields'] and t['collection']==source['collection']
        assert t['gold_record_n']==len(g['records'])
        if scope=='original_core_topk_replacements':
            assert t['supersedes_repair_sha256']==source['replaces_public371_repair_sha256']
            assert t['supersedes_repair_sha256']==frozen['original_core_repair'][t['id']]['repair_sha256']
        else:assert 'supersedes_repair_sha256' not in t
    by_id={r['id']:r for r in tasks}
    for r in ledger:
        assert r['id'] in originals
        if r['id'] in by_id:
            assert r['status']=='pass' and r['repair_sha256']==by_id[r['id']]['repair_sha256']
        else:assert r['status']!='pass'
    assert dict(Counter(r['repair_class'] for r in tasks))==manifest['repair_classes']
    assert sum('supersedes_repair_sha256' in r for r in tasks)==manifest['replacement_ids_n']==10
    assert sum(r['status']=='pass' for r in ledger)==manifest['repaired_n']
    assert sum(r['status']=='pending' for r in ledger)==manifest['pending_n']
    print(json.dumps({'status':'PASS','original_n':560,'repaired_n':manifest['repaired_n'],'pending_n':manifest['pending_n'],
                      'replacement_n':10,'new_API_calls':0,'new_database_executions':0}))
if __name__=='__main__':main()
