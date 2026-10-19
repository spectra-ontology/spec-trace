#!/usr/bin/env python3
"""Replay bounded original-source extraction without native/model access.

Stable identities and own-role boundaries are explicit retained witnesses.
The verifier checks their literal/XML consistency, not human semantic truth.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

sys.dont_write_bytecode = True
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def records(path):
    return [json.loads(line) for line in gzip.decompress(path.read_bytes()).decode().splitlines()]


def literal(element):
    return ''.join(e.text or '' for e in element.iter() if e.tag in (W+'t', M+'t'))


def positive(text):
    return 'DMRS' in text and 'pattern' in text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--original-docx-directory', type=Path)
    args = parser.parse_args()
    base = args.bundle.resolve()
    manifest = json.loads((base/'manifest.json').read_text())
    for entry in manifest['files']:
        path = (base/entry['path']).resolve()
        assert path.is_relative_to(base) and path.is_file()
        data = path.read_bytes()
        assert len(data)==entry['bytes'] and sha(data)==entry['sha256'], entry['path']
    assert not list(base.rglob('*.pyc'))
    spec = importlib.util.spec_from_file_location('raw_word_formatting', base/manifest['formatting_reader'])
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    reader.FFS = re.compile('Agreement|DMRS|pattern')
    bodies, formatting, expected_corpus = {}, {}, []
    for source in manifest['source_documents']:
        xml = gzip.decompress((base/source['document_XML']).read_bytes())
        styles = gzip.decompress((base/source['styles_XML']).read_bytes())
        assert sha(xml)==source['document_XML_sha256'] and sha(styles)==source['styles_XML_sha256']
        body = list(ET.fromstring(xml).find(W+'body'))
        bodies[source['meeting']] = body
        for i, el in enumerate(body):
            if el.tag in (W+'p',W+'tbl'):
                expected_corpus.append({'source_document_id': source['meeting']+'_original_report', 'raw_body_child0': i, 'kind': el.tag.rsplit('}',1)[-1], 'text': literal(el)})
        container = io.BytesIO()
        with zipfile.ZipFile(container,'w') as z:
            z.writestr('word/document.xml',xml)
            z.writestr('word/styles.xml',styles)
        actual = reader.audit_document(container.getvalue())
        filtered = [(i,el) for i,el in enumerate(body) if el.tag in (W+'p',W+'tbl')]
        assert len(filtered)==len(actual['blocks'])
        raw_by_paragraph = {}
        for (i,el), other in zip(filtered,actual['blocks']):
            assert ET.tostring(el)==ET.tostring(other)
            raw_by_paragraph.update((p,i) for p in other.iter(W+'p'))
        fmt = {}
        for p in actual['paragraphs']:
            if p['occurrences']:
                i = raw_by_paragraph[p['element']]
                fmt.setdefault(i,[]).append({'raw_body_child0':i,'paragraph_literal':p['raw_text'],'occurrences':p['occurrences']})
        formatting[source['meeting']] = fmt
    assert len(bodies)==10
    if args.original_docx_directory:
        original = {sha(p.read_bytes()):p for p in args.original_docx_directory.glob('*.docx')}
        for source in manifest['source_documents']:
            path = original.get(source['original_DOCX_sha256'])
            assert path is not None, source['meeting']
            with zipfile.ZipFile(path) as z:
                assert sha(z.read('word/document.xml'))==source['document_XML_sha256']
                assert sha(z.read('word/styles.xml'))==source['styles_XML_sha256']
    geometry = records(base/manifest['geometry'])
    patch = records(base/manifest['property_patch'])
    by_id = {r['resolutionId']:r['sourceRecordWindowText'] for r in patch}
    assert len(geometry)==len(patch)==len(by_id)==3176
    identities = records(base/'original_parser_registry_witness.jsonl.gz')
    original_agreements = {r['original_parser_record']['decision_id']:r for r in identities if r['subtype']=='Agreement'}
    assert len(original_agreements)==3176 and set(original_agreements)==set(by_id)
    broad_positives, own_positives, corrected = set(), [], []
    by_geometry = {}
    for row in geometry:
        qid = row['resolutionId']
        by_geometry[qid] = row
        start,broad_end = row['original_broad_raw_body_child_range']
        own_start,end = row['source_record_raw_body_child_range']
        body = bodies[row['meeting']]
        assert own_start==start and 0<=start<end<=broad_end<=len(body)
        assert original_agreements[qid]['raw_body_child_range'][0]==start
        assert literal(body[start]).strip().lower().startswith('agreement')
        text = '\n'.join(literal(el) for el in body[start:end])
        broad = '\n'.join(literal(el) for el in body[start:broad_end])
        assert text==by_id[qid] and sha(text.encode())==row['source_record_literal_sha256'], qid
        assert sha(broad.encode())==row['broad_source_literal_sha256'], qid
        if end!=broad_end:
            corrected.append(qid)
            assert row['source_role_boundary_rationale']
        if positive(broad):
            broad_positives.add(qid)
        if positive(text):
            assert positive(broad)
            own_positives.append({'resolutionId':qid,'meetingNumberInt':row['meetingNumberInt']})
    assert len(broad_positives)==12 and len(own_positives)==11 and len(corrected)==16
    observations = json.loads((base/'twelve_broad_positive_own_role_observations.json').read_text())
    assert {r['resolutionId'] for r in observations}==broad_positives
    for row in observations:
        qid = row['resolutionId']
        g = by_geometry[qid]
        assert row['source_record_raw_body_child_range']==g['source_record_raw_body_child_range']
        assert row['full_own_source_literal']==by_id[qid]
        assert row['own_literal_match'] is positive(by_id[qid])
        start,end = row['raw_body_child_range']
        actual = [p for i in range(start,end) for p in formatting[row['meeting']].get(i,[])]
        assert actual==row['marker_and_keyword_formatting'], qid
        assert all(o['active_formatting_status']=='all_active' for p in actual for o in p['occurrences'])
    assert {r['resolutionId'] for r in observations if not r['own_literal_match']}=={'AGR-120-8.1-024'}
    unbound = records(base/'all112_unbound_full_source_windows.jsonl.gz')
    assert len(unbound)==112
    counts = Counter()
    for row in unbound:
        body = bodies[row['meeting']]
        start,end = row['raw_body_child_range']
        text = '\n'.join(literal(el) for el in body[start:end])
        assert text==row['full_source_candidate_window_literal']
        for block in row['blocks']:
            assert ET.tostring(body[block['raw_body_child0']])==ET.tostring(ET.fromstring(block['XML']))
        counts['direct' if row['direct_body_paragraph'] else 'nested']+=1
        if positive(text):
            counts['literal_positive']+=1
            assert row['meeting']=='RAN1#119' and [start,end]==[2457,2458] and not row['direct_body_paragraph']
            observed = row['source_role_observation']
            assert observed['outer_existing_resolutionId']=='AGR-119-9.3.3-011' and observed['invented_new_ID'] is False
            assert text in by_id['AGR-119-9.3.3-011']
            assert literal(body[2455])=='Send an LS to RAN4 with the following contents:'
            assert 'Final LS is in R1-2410889.' in by_id['AGR-119-9.3.3-011']
    assert counts=={'direct':79,'nested':33,'literal_positive':6}
    corpus = records(base/manifest['common_corpus'])
    assert corpus==expected_corpus and len(corpus)==manifest['full_common_body_blocks']
    comparison = json.loads((base/'original_source_to_frozen_scalar_comparison.json').read_text())
    assert len(comparison)==12 and all(not r['source_only_IDs'] and not r['frozen_only_IDs'] for r in comparison)
    assert [(r['meeting'],r['frozen_record_mismatches']) for r in comparison if r['frozen_record_mismatches']]==[('RAN1#118',[{'resolutionId':'AGR-118-9.1.1-001','frozen_exists':True,'unequal_fields':['content']}])]
    selected = json.loads((base/'conditional_boundary_selection_NOT_GOLD.json').read_text())
    required = {r['resolutionId'] for r in own_positives if r['meetingNumberInt']>117}
    boundary = {r['resolutionId'] for r in own_positives if r['meetingNumberInt']==117}
    assert len(required)==8 and len(boundary)==3
    assert required==set(selected['required_above_boundary_IDs']) and boundary==set(selected['boundary_candidate_IDs'])
    assert selected['required_boundary_subset_size']==2 and selected['original_has_ID_tiebreaker'] is False
    question = json.loads((base/'original_question_and_query.json').read_text())
    assert sha(question['cypher'].encode())==manifest['original_query_sha256']
    assert 'ORDER BY m.meetingNumberInt DESC LIMIT 10' in question['cypher']
    print(json.dumps({'status':'PASS','source_documents':10,'generic_property_rows_reextracted_from_XML':len(patch),'whole_generic_common_body_blocks':len(corpus),'original_parser_identity_witnesses':len(original_agreements),'retained_whole_source_scalar_mismatches':1,'broad_literal_possible_positives':12,'source_own_literal_matches':11,'foreign_contribution_excluded':1,'broad_negative_whole_block_containment':3176-12,'own_role_boundary_corrections':len(corrected),'unbound_direct':counts['direct'],'nested_full_table':counts['nested'],'nested_positive_labels_belonging_to_one_existing_outer':counts['literal_positive'],'required_above_boundary':8,'boundary_candidates':3,'required_boundary_subset':2,'original_DOCX_bytes_reopened':10 if args.original_docx_directory else 0,'limits':'This independently reextracts literal text and formatting from included XML, but uses retained original-parser identity and independently reviewable own-boundary witnesses. It does not rerun the original parser, certify every broad-negative ownership boundary, interpret all technical topics, render complete Word/equations, resolve complete-pool alias scoring, execute native/model gates, or admit an original frozen question.'},ensure_ascii=False))


if __name__=='__main__':
    main()
