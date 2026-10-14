#!/usr/bin/env python3
"""Reopen native originals for the named documentary incorporation example."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def sha(data):return hashlib.sha256(data).hexdigest()


def text(el):return ''.join(t.text or '' for t in el.iter(W+'t'))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--trace',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();excerpt=json.loads((a.trace/'evidence-excerpt.json').read_text())
    bodies={};pins={}
    for key,s in excerpt['sources'].items():
        path=Path(s.get('local_path',a.trace/'RP-222864.official.zip'))
        data=path.read_bytes();assert sha(data)==s['archive_sha256'],key
        with zipfile.ZipFile(path) as z:member=z.read(s['native_member'])
        assert sha(member)==s['native_docx_sha256'],key
        with zipfile.ZipFile(__import__('io').BytesIO(member)) as z:xml=z.read('word/document.xml')
        bodies[key]=ET.fromstring(xml).find(W+'body')
        pins[str(path)]=sha(data)
    report=text(bodies['meeting_report'][2272]);assert 'Final CR is agreed in R1-2210700' in report
    proposal=bodies['WG_CR'][17];assert proposal.tag==W+'p'
    inserted=''.join(text(el) for el in proposal.iter(W+'ins'))
    assert inserted and inserted==text(proposal)
    assert len(list(proposal.iter(W+'del')))==0
    assert sha(' '.join(inserted.split()).encode())==excerpt['evidence'][2]['normalized_complete_paragraph_sha256']
    before=bodies['normative_before'];after=bodies['normative_after']
    matches=lambda b:[i for i,e in enumerate(b) if e.tag==W+'p' and text(e)==inserted]
    assert matches(before)==[] and matches(after)==[4175]
    assert not list(after[4175].iter(W+'ins')) and not list(after[4175].iter(W+'del'))
    assert '18' in text(after[4162]) and 'Multicast' in text(after[4162])
    clause_next=next(i for i,e in enumerate(after) if i>4162 and e.tag==W+'p' and text(e).startswith('Annex'))
    assert 4162<4175<clause_next
    history=after[4240];assert history.tag==W+'tbl'
    cells=[text(c) for c in list(history.findall(W+'tr'))[352].findall(W+'tc')]
    for field in ['2022-12','RAN#98-e','RP-222864','0388','17.4.0']:assert field in cells,field
    rp=bodies['RP_pack'];assert text(rp[17])==inserted
    rp_insert=''.join(text(e) for e in rp[17].iter(W+'ins'));assert rp_insert==inserted
    for path,pin in pins.items():assert sha(Path(path).read_bytes())==pin
    a.output.write_text(json.dumps({'status':'PASS','source_archives_reopened_n':len(pins),
        'native_sha256_checked':True,'complete_inserted_paragraph_exactly_equal':True,
        'before_occurrences':0,'after_occurrences':1,'after_locator':{'body_index':4175,'paragraph_index':4077},
        'normative_change_history_row_fields':cells,'RP_tracked_insertion_equals_WG':True,
        'input_pins_unchanged':True,'producer_sha256':sha(Path(__file__).read_bytes()),
        'expert_reviews':0,'model_calls':0,
        'limits':'Original-source documentary audit of a deliberately investigated named example; not graph execution, expert adjudication, population accuracy, or causal motivation.'},ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
