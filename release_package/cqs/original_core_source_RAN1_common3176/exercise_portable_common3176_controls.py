#!/usr/bin/env python3
"""Challenge the portable verifier after rehashing every modified file."""
import argparse
import concurrent.futures
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode=True
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def repin(folder):
    p=folder/'manifest.json';m=json.loads(p.read_text())
    for f in m['files']:
        x=folder/f['path'];f['bytes']=x.stat().st_size;f['sha256']=sha(x)
    dump(p,m)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--out',type=Path,required=True);a=p.parse_args();source=a.bundle.resolve();out=a.out.resolve();assert not out.exists() and not out.is_relative_to(source);out.mkdir(parents=True)
    def run(folder,label,expected):
        began=time.time();r=subprocess.run([sys.executable,'-B','-I',str(folder/'verify_common3176_portable_source.py')],cwd='/',capture_output=True,text=True)
        result={'case':label,'expected_exit_zero':expected,'actual_exit':r.returncode,'elapsed_seconds':time.time()-began,'stdout':r.stdout,'stderr':r.stderr,'manifest_sha256':sha(folder/'manifest.json')};dump(out/(label+'.json'),result);assert (r.returncode==0)==expected,label;return result
    with tempfile.TemporaryDirectory(prefix='common3176-portable-') as temporary:
        base=Path(temporary);relocated=base/'relocated/evidence';shutil.copytree(source,relocated);positive=run(relocated,'relocated_positive',True);tasks=[]
        for kind in ['wrong_XML_derived_property','auxiliary_IRI_binding','wrong_RDF_property','wrong_DMRS_boundary']:
            target=base/kind/'evidence';shutil.copytree(source,target)
            if kind=='wrong_XML_derived_property':
                f=target/'raw_extraction/generic_property_patch.jsonl.gz';items=[json.loads(x) for x in gzip.decompress(f.read_bytes()).decode().splitlines()];items[0]['sourceRecordWindowText']+='\nA foreign contribution was inserted.';f.write_bytes(gzip.compress(('\n'.join(json.dumps(x,ensure_ascii=False) for x in items)+'\n').encode(),mtime=0));repin(target/'raw_extraction')
            elif kind=='auxiliary_IRI_binding':
                f=target/'whole_snapshot/all3176_exact_node_IRI_property_bindings.json';items=json.loads(f.read_text());items[0]['source_iri']='https://w3id.org/spectra/inst/_/Resolution/'+items[0]['resolutionId'];dump(f,items)
            elif kind=='wrong_RDF_property':
                f=target/'whole_snapshot/generic_property_additions.ttl';s=f.read_text();assert 'sourceRecordWindowText' in s;f.write_text(s.replace('sourceRecordWindowText','unrelatedText',1))
            else:
                f=target/'source_only_prefix_selection.json';items=json.loads(f.read_text());items['RAN1_P2_CQ5-11']['boundary_candidates'].pop();dump(f,items)
            repin(target);tasks.append((target,kind,False))
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:results=list(executor.map(lambda v:run(*v),tasks))
    receipt={'status':'PASS','tested_manifest_sha256':sha(source/'manifest.json'),'positive_relocated_checkout_independent':positive['actual_exit']==0,'semantic_negatives_with_all_affected_hashes_repinned':[{k:v for k,v in x.items() if k not in ['stdout','stderr']} for x in results],'native_calls':0,'API_calls':0,'expert_validation_n':0};dump(out/'receipt.json',receipt);print(json.dumps(receipt))
if __name__=='__main__':main()
