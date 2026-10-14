#!/usr/bin/env python3
"""Rehash protected files and all original input pins without changing them."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=a.base/'refinement'
    load=lambda name:json.loads((a.base/name).read_text())
    protected=load('refinement/safety_start.json')['protected_files'];pins={}
    for name,key in [('source-audit/results.json','inspected_source_sha256'),
                     ('native-cr-audit/results.json','input_before_sha256'),
                     ('wg-cr-extension/results.json','input_before_sha256'),
                     ('refinement/native-verification-meeting/results.json','native_input_pins')]:
        for path,h in load(name)[key].items():
            path=str(Path(path).resolve())
            if path in pins:assert pins[path]==h,path
            pins[path]=h
    frozen=load('refinement/cr-binding/results.json')['frozen']
    for v in frozen.values():pins[str(Path(v['path']).resolve())]=v['sha256']
    trace=load('refinement/normative-trace/evidence-excerpt.json')
    for key,v in trace['sources'].items():
        path=v.get('local_path',str(r/'normative-trace/RP-222864.official.zip'))
        pins[str(Path(path).resolve())]=v['archive_sha256']
    extension=r/'report-source-extension-corrected/results.json'
    if extension.exists():
        for path,h in json.loads(extension.read_text())['inspected_source_sha256'].items():
            absolute=str(Path(path).resolve())
            if absolute in pins:assert pins[absolute]==h,path
            pins[absolute]=h
    drift=[p for p,h in pins.items() if digest(Path(p))!=h]
    protected_drift=[v['path'] for v in protected if digest(Path(v['path']))!=v['sha256']]
    scripts=Path(__file__).parent;producer_checks=[]
    for name,protocol in [('source_audit.py','wg-cr-extension/protocol.json'),
                          ('native_cr_audit.py','refinement/cr-binding/protocol.json'),
                          ('refine_cr_binding.py','refinement/cr-binding/protocol.json'),
                          ('complete_cr_literal_lists.py','refinement/cr-literal-lists-complete/protocol.json'),
                          ('refine_graph_cover_lists.py','refinement/graph-cr-literal-lists-complete/protocol.json')]:
        field='reader_sha256' if name=='source_audit.py' else 'native_reader_sha256' if name=='native_cr_audit.py' else 'producer_sha256'
        expected=load(protocol)[field];actual=digest(scripts/name)
        producer_checks.append({'script':name,'recorded_sha256':expected,'actual_sha256':actual,'equal':actual==expected})
    result={'utc':datetime.now(timezone.utc).isoformat(),
        'status':'PASS' if not drift and not protected_drift and all(c['equal'] for c in producer_checks) else 'FAIL',
        'protected_files_checked':len(protected),'protected_file_drift':protected_drift,
        'original_source_and_frozen_pins_checked':len(pins),'native_input_drift':drift,
        'producer_checks':producer_checks,'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'scope':'This task writes only its local reviewer documents, scripts, refinement artifacts and scoped handoff/memory. No original source or frozen export is rewritten.',
        'public_mutations_by_this_refinement':0,'OpenReview_posts_by_this_refinement':0,
        'operational_DB_calls_by_this_refinement':0,'new_model_calls_by_this_refinement':0,'expert_reviews':0}
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','protected_files_checked','original_source_and_frozen_pins_checked','protected_file_drift','native_input_drift']}),flush=True)
    if result['status']!='PASS':raise ValueError('Safety/pin verification failed; see retained report.')


if __name__=='__main__':main()
