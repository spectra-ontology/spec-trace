#!/usr/bin/env python3
"""Check a true source-link mutation without changing any evidence file."""
import sys
if sys.flags.optimize: raise SystemExit('Optimization prohibited')
import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET
sys.dont_write_bytecode=True

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=Path,required=True);a=p.parse_args()
    path=a.bundle.absolute()/'verify_source_evidence.py'
    for x in [path,*path.parents]:
        if x.is_symlink():raise ValueError('Symlink path prohibited')
    spec=importlib.util.spec_from_file_location('cq030_portable_meaning_guard',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.bootstrap()
    source=json.loads(gzip.decompress((path.parent/'source/own_paragraphs_and_styles.json.gz').read_bytes()))
    positive=m.verify_source_snippets(source)
    bad=copy.deepcopy(source)
    own=next(s for s in bad['sources'] if (s['specNumber'],s['specRelease'])==('38.214','Rel-15'))
    para=next(q for q in own['paragraphs'] if 'reporting_resourceMapping_parameters_TS38211' in q['roles'])
    node=ET.fromstring(para['xml_utf8']);changes=0
    for e in node.iter():
        if e.text and '38.211' in e.text:
            changes+=e.text.count('38.211');e.text=e.text.replace('38.211','38.215')
    assert changes>0
    para['xml_utf8']=ET.tostring(node,encoding='unicode')
    para['xml_utf8_sha256']=hashlib.sha256(para['xml_utf8'].encode()).hexdigest()
    para['text_w_t_plus_m_t']=m.text(node)
    try:m.verify_source_snippets(bad)
    except AssertionError:rejected=True
    else:rejected=False
    assert rejected
    print(json.dumps({'status':'PASS','positive':positive,'source_link_wrong_target_rejected':True,
        'mutation':'Own reporting resourceMapping TS38.211 becomes TS38.215 in memory; XML/text/hash remain consistent.',
        'immutable_file_hash_rejection_bypassed_for_this_function_test':True,
        'evidence_files_changed':0,'API_calls':0,'native_runs':0}))

if __name__=='__main__':main()
