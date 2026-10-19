"""Replay source observations for the proposed original-query fifteen-item extent.

This checks source evidence, not semantic admission, native execution or model scores.
"""
import argparse
import collections
import copy
import datetime
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import sqlite3
import sys
from xml.etree import ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from raw_source import audit_document, iter_blocks, W, FFS, HEAD

HERE = Path(__file__).resolve().parent
MONTHS = {n:i+1 for i,n in enumerate(('January February March April May June July August September October November December').split())}
MONTH = '(?:'+'|'.join(MONTHS)+')'
DAY = r'\d{1,2}(?:st|nd|rd|th|h)?'
DM = re.compile(r'(?P<d1>'+DAY+r')\s*(?P<m1>'+MONTH+r')?\s*[-–]\s*(?P<d2>'+DAY+r')\s*(?P<m2>'+MONTH+r')\s*,?\s*(?P<year>20\d{2})')
MD = re.compile(r'(?P<m1>'+MONTH+r')\s*(?P<d1>'+DAY+r')\s*[-–]\s*(?:(?P<m2>'+MONTH+r')\s*)?(?P<d2>'+DAY+r')\s*,?\s*(?P<year>20\d{2})')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rows(name):
    p = HERE/name
    raw = gzip.decompress(p.read_bytes()) if name.endswith('.gz') else p.read_bytes()
    return [json.loads(line) for line in raw.decode().splitlines() if line.strip()]


def text(e):
    if e.tag in (W+'t','{http://schemas.openxmlformats.org/officeDocument/2006/math}t'):
        return e.text or ''
    if e.tag == W+'tab':
        return '\t'
    if e.tag in (W+'br',W+'cr'):
        return '\n'
    return ''.join(text(c) for c in e)


def period(value):
    hits = [m for rx in (DM,MD) for m in rx.finditer(value)]
    assert len(hits)==1, ('date range',value)
    d = hits[0].groupdict()
    year = int(d['year'])
    start = datetime.date(year,MONTHS[d['m1'] or d['m2']],int(re.match(r'\d+',d['d1'])[0])).isoformat()
    end = datetime.date(year,MONTHS[d['m2'] or d['m1']],int(re.match(r'\d+',d['d2'])[0])).isoformat()
    assert start<=end
    return start,end


def calendar():
    windows = rows('calendar/all192_front8_XML_windows.jsonl.gz')
    raw = {r['source_row']:r for r in rows('calendar/all192_authored_raw_frontmatter_inputs.jsonl.gz')}
    sources = rows('calendar/all192_own_report_source_identity_and_period_ledger.jsonl.gz')
    meetings = rows('calendar/all60_source_reported_Meeting_period_ledger.jsonl.gz')
    assert len(windows)==len(raw)==len(sources)==192 and len(meetings)==60
    bykey = {(s['source_archive']['path'],s['member']):s for s in sources}
    periods = {}
    for win in windows:
        key = (win['original_source_archive_pin']['path'],win['original_member'])
        s = bykey[key]
        r = raw[win['raw_source_row']]
        assert win['original_source_archive_pin']==s['source_archive']
        assert win['original_member_sha256']==s['member_sha256']
        assert win['original_full_document_XML_sha256']==s['document_XML_sha256']
        assert len(win['paragraphs'])==8
        values=[]
        for i,p in enumerate(win['paragraphs']):
            assert p['paragraph_zero_based']==i
            assert sha(p['xml'].encode())==p['sha256']==r['source_cell_coordinates']['paragraph_ElementTree_utf8_XML_sha256'][i]
            values.append(text(ET.fromstring(p['xml'])))
        assert values==[p['literal_authored_text_with_tabs_and_breaks'] for p in r['fields']['paragraphs']]
        ti,di=s['title_all_document_paragraph_index'],s['date_all_document_paragraph_index']
        assert 0<=ti<8 and di==ti+1 and di<8
        assert ''.join(values[ti].split())==''.join(s['title_literal'].split())
        assert ''.join(values[di].split())==''.join(s['period']['literal'].split())
        actual=period(values[di]);assert actual==(s['period']['start'],s['period']['end'])
        periods[key]=actual
    bynode={}
    for m in meetings:
        assert m['all_matched_source_reports']
        for s in m['all_matched_source_reports']:
            key=(s['source_archive']['path'],s['member'])
            assert s==bykey[key]
            assert periods[key]==(m['sourceReportedStartDate'],m['sourceReportedEndDate'])
        bynode[m['frozen_Meeting']['node_id']]=m
    assert len(bynode)==60
    return bynode,sources


def validate_latest(audit,spans,occurrences):
    assert len(spans)==286 and len({r['resolutionId'] for r in spans})==286
    blocks,paragraphs=audit['blocks'],audit['paragraphs']
    owner={}
    byparagraph={p['all_paragraph_index']:p for p in paragraphs}
    for r in spans:
        lo,hi=r['body_blocks']
        assert 0<=lo<hi<len(blocks)
        for bi in range(lo,hi):
            assert bi not in owner,('overlapping Agreement spans',bi)
            owner[bi]=r
        assert [ET.tostring(b,encoding='unicode') for b in blocks[lo:hi]]==r['raw_body_block_xml']
        assert ET.tostring(blocks[hi],encoding='unicode')==r['next_boundary_block']['xml']
        assert HEAD.match(paragraphs[next(p['all_paragraph_index'] for p in paragraphs if p['body_block_index']==lo)]['final_literal'])
        actual=[]
        for p in paragraphs:
            if lo<=p['body_block_index']<hi:
                actual.extend(p['occurrences'])
        assert bool(actual)==r['has_raw_own_span_marker']
        assert any(x['active_formatting_status']=='all_active' for x in actual)==r['has_active_formatting_marker']
        assert len(actual)==r['FFS_occurrence_count']
        expected_p={p['all_paragraph_index']:p for p in r['paragraphs']}
        for pi,p in expected_p.items():
            ap=byparagraph[pi]
            assert ET.tostring(ap['element'],encoding='unicode')==p['paragraph_xml']
            assert ap['raw_text']==p['raw_text']
            assert [(x['start'],x['end'],x['active_formatting_status']) for x in ap['occurrences']]==[(x['start'],x['end'],x['active_formatting_status']) for x in p['FFS_occurrences']]
    for x in occurrences:
        ap=byparagraph[x['all_paragraph_index']]
        assert owner[ap['body_block_index']]['resolutionId']==x['resolutionId']
        assert any((y['start'],y['end'],y['active_formatting_status'])==(x['start'],x['end'],x['active_formatting_status']) for y in ap['occurrences'])
    assert len(occurrences)==103
    assert sum(r['has_raw_own_span_marker'] for r in spans)==43
    assert sum(r['has_active_formatting_marker'] for r in spans)==39
    candidates=[]
    for p in paragraphs:
        if not HEAD.match(p['final_literal']):continue
        bi=p['body_block_index'];r=owner.get(bi)
        own=r and bi==r['body_blocks'][0] and blocks[bi] is p['element']
        prior=bool(re.search(r'(?:made\s+in\s+)?RAN1\s*#\s*(?:121|122bis)\b',p['final_literal'],re.I))
        role='retained_own_heading' if own else 'explicit_prior_meeting_body_heading' if blocks[bi] is p['element'] and prior else 'nested_within_retained_own_span' if r else 'unclassified_candidate'
        candidates.append((bi,p['all_paragraph_index'],role,r['resolutionId'] if r else None))
    assert len(candidates)==293
    assert collections.Counter(c[2] for c in candidates)=={'retained_own_heading':286,'explicit_prior_meeting_body_heading':2,'nested_within_retained_own_span':5}
    unowned=[p for p in paragraphs if p['occurrences'] and p['body_block_index'] not in owner]
    assert [p['body_block_index'] for p in unowned]==[2101,2109,3711,3712]
    assert blocks[2098].tag==W+'p' and text(blocks[2098]).strip()=='Conclusion:'
    assert text(blocks[2107]).strip()=='Working assumption:'
    assert text(blocks[3696]).strip()=='Working Assumption'
    return candidates,unowned


def frozen_projection(source_root=None):
    if source_root is None:
        return rows('frozen/all21058_Agreement_MADE_AT_and_Agenda_operands.jsonl.gz')
    path=source_root/'logs/pending-tasks/spectracq-core-contract-2026-10-13/empirical/relational/RAN1.sqlite'
    with path.open('rb') as stream:
        h=hashlib.file_digest(stream,'sha256').hexdigest() if hasattr(hashlib,'file_digest') else sha(stream.read())
    manifest=json.loads((HERE/'manifest.json').read_text());assert h==manifest['original_frozen_SQL']['sha256']
    c=sqlite3.connect(path.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
    c.execute('PRAGMA query_only=ON');c.row_factory=sqlite3.Row
    result=[]
    for row in c.execute('SELECT node_id,resolutionId,hasFFS,sequence FROM Agreement ORDER BY node_id'):
        r=dict(row)
        r['meetings']=[dict(x) for x in c.execute('SELECT m.node_id,m.meetingNumber,m.meetingNumberInt FROM rel_MADE_AT e JOIN Meeting m ON m.node_id=e.dst_id WHERE e.src_id=? ORDER BY m.node_id',(r['node_id'],))]
        r['agendas']=[dict(x) for x in c.execute('SELECT ag.node_id,ag.agendaNumber FROM rel_RESOLUTION_BELONGS_TO e JOIN AgendaItem ag ON ag.node_id=e.dst_id WHERE e.src_id=? ORDER BY ag.node_id',(r['node_id'],))]
        result.append(r)
    c.close();return result


def negative_controls(audit,spans,occurrences):
    result=[]
    cases=['drop_own_span','duplicate_own_span','flip_source_marker_flag','flip_active_formatting_flag','corrupt_source_XML','corrupt_next_boundary_XML','change_FFS_formatting_status','change_occurrence_owner']
    for case in cases:
        ss,oo=copy.deepcopy(spans),copy.deepcopy(occurrences)
        pos=next(i for i,s in enumerate(ss) if s['has_raw_own_span_marker'])
        if case=='drop_own_span':ss.pop()
        elif case=='duplicate_own_span':ss[-1]=copy.deepcopy(ss[0])
        elif case=='flip_source_marker_flag':ss[pos]['has_raw_own_span_marker']=False
        elif case=='flip_active_formatting_flag':ss[pos]['has_active_formatting_marker']=not ss[pos]['has_active_formatting_marker']
        elif case=='corrupt_source_XML':ss[0]['raw_body_block_xml'][0]+=' '
        elif case=='corrupt_next_boundary_XML':ss[0]['next_boundary_block']['xml']+=' '
        elif case=='change_FFS_formatting_status':oo[0]['active_formatting_status']='all_active' if oo[0]['active_formatting_status']!='all_active' else 'all_removed_or_struck'
        elif case=='change_occurrence_owner':oo[0]['resolutionId']='AGR-wrong-owner'
        try:validate_latest(audit,ss,oo)
        except AssertionError:result.append({'case':case,'rejected':True})
        else:raise AssertionError(('negative accepted',case))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path)
    parser.add_argument('--full-original-calendars',action='store_true')
    args=parser.parse_args()
    manifest=json.loads((HERE/'manifest.json').read_text())
    for pin in manifest['files']:
        p=HERE/pin['path'];assert p.is_file() and p.stat().st_size==pin['bytes'] and sha(p.read_bytes())==pin['sha256'],pin['path']
    assert not list(HERE.rglob('*.pyc')) and not list(HERE.rglob('__pycache__'))
    docx=(HERE/'source/latest_report.docx').read_bytes();audit=audit_document(docx)
    assert sha(docx)==manifest['latest_report']['member_sha256']
    assert sha(audit['xml'])==manifest['latest_report']['document_xml_sha256']
    spans=rows('source/all286_retained_Agreement_full_raw_own_spans.jsonl.gz')
    occurrences=rows('source/all_retained_Agreement_FFS_formatting_occurrences.jsonl')
    candidates,unowned=validate_latest(audit,spans,occurrences)
    expected_candidates=rows('source/all293_literal_Agreement_heading_candidates.jsonl.gz')
    assert candidates==[(r['body_block_index'],r['all_paragraph_index'],r['classification'],r['existing_span_owner']) for r in expected_candidates]
    mapping=json.loads((HERE/'source/body_coordinate_mapping.json').read_text())
    rawbody=ET.fromstring(audit['xml']).find(W+'body');rawindex={e:i for i,e in enumerate(rawbody)}
    assert mapping['all_blocks']==[{'p_or_table_block_ordinal':i,'raw_body_child_ordinal':rawindex.get(e),'tag':e.tag.split('}')[-1]} for i,e in enumerate(iter_blocks(rawbody))]
    bymeeting,sources=calendar()
    projection=frozen_projection();assert len(projection)==21058
    if args.source_root:
        assert frozen_projection(args.source_root)==projection
        source_archive=args.source_root/manifest['latest_report']['archive_path']
        assert sha(source_archive.read_bytes())==manifest['latest_report']['archive_sha256']
        with zipfile.ZipFile(source_archive) as z:assert z.read(manifest['latest_report']['member'])==docx
    if args.full_original_calendars:
        assert args.source_root,'--full-original-calendars requires --source-root'
        for s in sources:
            archive=args.source_root/s['source_archive']['path']
            assert sha(archive.read_bytes())==s['source_archive']['sha256']
            with zipfile.ZipFile(archive) as z:member=z.read(s['member'])
            assert sha(member)==s['member_sha256']
            with zipfile.ZipFile(io.BytesIO(member)) as z:assert sha(z.read('word/document.xml'))==s['document_XML_sha256']
    assert len({r['node_id'] for r in projection})==21058
    assert len({r['resolutionId'] for r in projection})==21058
    assert sum(len(r['meetings']) for r in projection)==21288
    assert sum(bool(r['hasFFS']) for r in projection)==4635
    joined=[]
    for r in projection:
        assert r['meetings']
        dates=set()
        for m in r['meetings']:
            sm=bymeeting[m['node_id']]
            assert sm['frozen_Meeting']['meetingNumber']==m['meetingNumber']
            dates.add((sm['sourceReportedStartDate'],sm['sourceReportedEndDate']))
            if r['hasFFS']:joined.append((r['resolutionId'],m['meetingNumberInt'],sm['sourceReportedEndDate']))
        assert len(dates)==1
    numeric=[r[0] for r in sorted(joined,key=lambda r:(-r[1],r[0]))[:15]]
    authentic=[r[0] for r in sorted(joined,key=lambda r:r[0])]
    # Stable sorting separately expresses DESC authentic period, ASC identity.
    authentic=[r[0] for r in sorted(sorted(joined,key=lambda r:r[0]),key=lambda r:r[2],reverse=True)[:15]]
    assert numeric==authentic and len(set(numeric))==15
    latest=max(m['sourceReportedEndDate'] for m in bymeeting.values())
    latest_nodes=[nid for nid,m in bymeeting.items() if m['sourceReportedEndDate']==latest]
    latest_frozen={r['resolutionId'] for r in projection if any(m['node_id'] in latest_nodes for m in r['meetings'])}
    assert latest_frozen=={r['resolutionId'] for r in spans}
    retained=sorted(r['resolutionId'] for r in spans if r['has_raw_own_span_marker'])[:15]
    active=sorted(r['resolutionId'] for r in spans if r['has_active_formatting_marker'])[:15]
    assert retained==active==numeric
    selected=rows('source_selected_records.jsonl')
    assert selected==[{'resolutionId':rid} for rid in retained]
    controls=negative_controls(audit,spans,occurrences)
    print(json.dumps({'status':'PASS','source_selected_records':15,'all_retained_Agreement_spans':286,
      'raw_marker_positive':43,'raw_marker_negative':243,'active_marker_positive':39,'heading_candidates':293,
      'unowned_FFS_paragraphs':len(unowned),'all192_calendar_windows':192,'all60_frozen_Meeting_calendars':60,
      'frozen_Agreement_projection':21058,'frozen_MADE_AT_join_rows':21288,
      'original15_numeric_and_authentic_and_active_prefix_equal':True,'negative_controls':controls,
      'full_frozen_SQL_replayed':bool(args.source_root),'full192_original_archives_reopened':bool(args.full_original_calendars),
      'source_semantic_admission':False,'native_or_model_calls':0,
      'limits':['Default replay uses included typed frozen projection and raw source witnesses; optional full SQL replay is separate.',
      'Formal own-span identity mapping is pinned to the prior actual current-parser source-access output, not a newly validated general-purpose Agreement parser.',
      'Calendar witnesses establish the fixed fifteen-item prefix, not general equality of numeric and calendar ordering.',
      'Literal/formatting-active FFS is not a claim of unresolved status today. Scope/required-role/order policy awaits independent semantic review.']},ensure_ascii=False,sort_keys=True))


if __name__=='__main__':
    main()
