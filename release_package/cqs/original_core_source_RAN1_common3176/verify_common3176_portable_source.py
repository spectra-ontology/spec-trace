#!/usr/bin/env python3
"""Replay included source evidence; optional whole-base verification is explicit."""
import argparse
import contextlib
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode=True

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def records(p):return [json.loads(x) for x in gzip.decompress(p.read_bytes()).decode().splitlines()]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--base-ttl',type=Path);p.add_argument('--base-sql',type=Path);p.add_argument('--rebuild-out',type=Path)
    p.add_argument('--full-public-facts',action='store_true')
    a=p.parse_args();b=a.bundle.resolve();m=json.loads((b/'manifest.json').read_text())
    assert not list(b.rglob('*.pyc')) and not list(b.rglob('__pycache__'))
    for f in m['files']:
        x=(b/f['path']).resolve();assert x.is_relative_to(b) and x.is_file()
        assert x.stat().st_size==f['bytes'] and sha(x)==f['sha256'],f['path']
    raw=b/'raw_extraction'
    child=subprocess.run([sys.executable,'-B','-I',str(raw/'verify_source_evidence.py')],capture_output=True,text=True)
    assert child.returncode==0,child.stdout+child.stderr
    result=json.loads(child.stdout.strip().splitlines()[-1]);assert result['status']=='PASS'
    patch=records(raw/'generic_property_patch.jsonl.gz');geom=records(raw/'identity_and_source_geometry.jsonl.gz')
    texts={x['resolutionId']:x['sourceRecordWindowText'] for x in patch}
    bindings=json.loads((b/'whole_snapshot/all3176_exact_node_IRI_property_bindings.json').read_text())
    assert len(bindings)==len(patch)==len({x['source_iri'] for x in bindings})==len({x['node_id'] for x in bindings})==3176
    assert {x['resolutionId']:x['sourceRecordWindowText'] for x in bindings}==texts
    assert all(x['source_iri']=='https://w3id.org/spectra/inst/RAN1/Resolution/'+x['resolutionId'] and sorted(x['labels'])==['Agreement','Resolution'] for x in bindings)
    spec=importlib.util.spec_from_file_location('pinned_public_loader',b/'recipe/load_released_kg.py');loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
    with contextlib.redirect_stdout(io.StringIO()):nodes,edges,stats=loader.parse_ttl(b/'whole_snapshot/generic_property_additions.ttl')
    assert len(nodes)==3176 and not edges and not stats['prop_conflicts']
    for x in bindings:
        key=('Resolution',x['resolutionId']);assert nodes[key]['props']=={'sourceRecordWindowText':x['sourceRecordWindowText']} and not nodes[key]['labels']
    selection=json.loads((b/'source_only_prefix_selection.json').read_text())
    for qid,w in selection.items():
        pool=[{'resolutionId':x['resolutionId'],'meetingNumberInt':x['meetingNumberInt']} for x in geom if all(t in texts[x['resolutionId']] for t in w['literal_terms'])]
        pool.sort(key=lambda x:(-x['meetingNumberInt'],x['resolutionId']))
        assert pool==w['source_only_full_matching_records'] and len(pool)>=10
        definition=json.loads((b/'semantics'/f'{qid}_common3176_definition.json').read_text())
        assert all("CONTAINS '"+t+"'" in definition['original_query'] for t in w['literal_terms'])
        if qid.endswith('-11'):
            boundary=pool[9]['meetingNumberInt'];above=[x for x in pool if x['meetingNumberInt']>boundary];tied=[x for x in pool if x['meetingNumberInt']==boundary]
            assert above==w['mandatory_above_boundary'] and tied==w['boundary_candidates'] and w['choose_at_boundary']==10-len(above)
            assert len(above)==8 and len(tied)==3 and w['choose_at_boundary']==2 and boundary==117
        else:
            assert pool[:10]==w['selected_prefix']
        for role in ['primary_exact','independent_secondary']:
            f=b/'semantics'/f'{qid}_common3176_{role}_seven_unit_review.json';assert f.is_file();review=json.loads(f.read_text())
            assert review['status'].lower()=='pass' and len(review['semantic_evidence'])==7
    full=False
    if any((a.base_ttl,a.base_sql,a.rebuild_out,a.full_public_facts)):
        assert all((a.base_ttl,a.base_sql,a.rebuild_out)), 'All three base/rebuild paths required.'
        cmd=[sys.executable,'-B','-I',str(b/'rebuild_common3176_snapshot.py'),'--bundle',str(b),'--base-ttl',str(a.base_ttl.resolve()),'--base-sql',str(a.base_sql.resolve()),'--out',str(a.rebuild_out.resolve())]
        if a.full_public_facts:cmd.append('--full-public-facts')
        rebuilt=subprocess.run(cmd,capture_output=True,text=True)
        assert rebuilt.returncode==0,rebuilt.stdout+rebuilt.stderr
        full=json.loads(rebuilt.stdout.strip().splitlines()[-1])
        assert full['status']=='PASS'
    print(json.dumps({'status':'PASS','included_files':len(m['files']),'raw_source_replay':result,'generic_literal_RDF_additions':len(nodes),'source_prefix_questions':len(selection),'full_base_replay':full,'original_frozen_admission_delta':0,'expert_validation_n':0},ensure_ascii=False))

if __name__=='__main__':main()
