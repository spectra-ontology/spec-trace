"""Fresh original archive and all same-agenda frozen representations, readonly."""
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import io
import itertools
import json
from pathlib import Path
import sqlite3
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p/'CLAUDE.md').exists())
TASK = ROOT/'logs/pending-tasks/spectracq-core-contract-2026-10-13'
OLD = TASK/'empirical/overnight_reaudit/root_evidence/two_agent_unresolved_loop/RAN1_RAN3_RAN4'
SRC = OLD/'loop114_RAN1_ten_report_generic_source_text_and_DMRS_tie_proposal_NOT_ADMITTED/evidence'
DB = TASK/'empirical/relational/RAN1.sqlite'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
STEMS = ['The above agreement applies to PUCCH with repetitions',
         'The above agreement applies to different priority indexes for PUCCH/PUSCH']


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pin(p):
    b = p.read_bytes()
    return {'path': str(p.resolve()), 'sha256': sha(b), 'bytes': len(b)}


def literal(el):
    return ''.join(t.text or '' for t in el.iter(W+'t'))


def main():
    out = HERE/'actual_original_archive_and_event_closure_v1'
    out.mkdir(exist_ok=False)
    manifest = json.loads((SRC/'manifest.json').read_text())
    originals = []
    for label in ['121', '120b']:
        entry = next(d for d in manifest['source_documents'] if d['meeting']=='RAN1#'+label)
        archive = ROOT/entry['original_archive']['path']
        with zipfile.ZipFile(archive) as z:
            if z.testzip() is not None:
                raise AssertionError('archive CRC')
            docx = z.read(entry['original_archive']['member'])
            member_crc = z.getinfo(entry['original_archive']['member']).CRC
        if sha(docx)!=entry['original_DOCX_sha256'] or sha(archive.read_bytes())!=entry['original_archive']['sha256']:
            raise AssertionError('original source pins')
        loader = ROOT/'ontology/input/tsg/RAN/formal/meetings/RAN1/Final_Report'/f'Final_Report_RAN1-{label}.docx'
        if label=='121' and loader.read_bytes()!=docx:
            raise AssertionError('mandatory current source version identity')
        with zipfile.ZipFile(io.BytesIO(docx)) as z:
            if z.testzip() is not None:
                raise AssertionError('DOCX CRC')
            xml, styles = z.read('word/document.xml'), z.read('word/styles.xml')
            xml_crc, styles_crc = z.getinfo('word/document.xml').CRC, z.getinfo('word/styles.xml').CRC
        if xml!=gzip.decompress((SRC/entry['document_XML']).read_bytes()):
            raise AssertionError('portable XML source identity')
        body = list(ET.fromstring(xml).find(W+'body'))
        hits = []
        for i, el in enumerate(body):
            if any(s in literal(el) for s in STEMS):
                hits.append({'raw_body_child0': i, 'literal': literal(el),
                             'XML': ET.tostring(el, encoding='unicode'),
                             'struck_run_literals': [literal(r) for r in el.iter(W+'r')
                                                    if r.find(W+'rPr/'+W+'strike') is not None]})
        originals.append({'meeting': entry['meeting'], 'archive': pin(archive),
                          'member': entry['original_archive']['member'], 'member_CRC': member_crc,
                          'DOCX_sha256': sha(docx), 'DOCX_bytes': len(docx),
                          'loader_DOCX': pin(loader), 'loader_and_archive_member_equal': loader.read_bytes()==docx,
                          'document_XML': {'sha256': sha(xml), 'bytes': len(xml), 'CRC': xml_crc},
                          'styles_XML': {'sha256': sha(styles), 'bytes': len(styles), 'CRC': styles_crc},
                          'condition_stem_source_hits': hits})
    c = sqlite3.connect(DB.resolve().as_uri()+'?mode=ro&immutable=1', uri=True)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA query_only=ON')
    same = [dict(r) for r in c.execute('''SELECT n.* FROM _node_record n JOIN edge e
        ON e.src_id=n.node_id AND e.rel_type='RESOLUTION_BELONGS_TO' JOIN AgendaItem a ON a.node_id=e.dst_id
        WHERE a.agendaNumber='9.11.3' AND a.meetingNumber='121' ORDER BY n.node_id''')]
    for row in same:
        row['all_incident_edges'] = [dict(e) for e in c.execute('SELECT * FROM edge WHERE src_id=? OR dst_id=?', (row['node_id'],row['node_id']))]
    broad = []
    for row in c.execute('SELECT * FROM _node_record ORDER BY node_id'):
        s = row['properties_json'].lower()
        if 'pucch' not in s or not ('repetition' in s or 'priority index' in s):
            continue
        if not ('appl' in s or ('condition' in s and any(t in s for t in ['remov','wa','assumption']))):
            continue
        props = json.loads(row['properties_json'])
        rid = props.get('resolutionId')
        if rid and (rid.startswith(('AGR-121-', 'CON-121-', 'WA-121-')) or 'working assumption' in s):
            broad.append(dict(row))
    original = json.loads((HERE/'actual_retained_proposal_boundary_v1/all_original_positive_rows.json').read_text())
    before = [x['resolutionId'] for x in original if x['meetingNumberInt']>121]
    tied = [x['resolutionId'] for x in original if x['meetingNumberInt']==121]
    witnesses = {'AGR-121-9.11.3-007', 'AGR-121-9.11.3-008'}
    possibilities = [{'literal_query_only_ID_set_NOT_GOLD': sorted(before+list(combo)),
                       'source_deletion_witnesses_in_set': sorted(set(combo)&witnesses)}
                      for combo in itertools.combinations(tied,10-len(before))]
    if len(possibilities)!=5 or any(not x['source_deletion_witnesses_in_set'] for x in possibilities):
        raise AssertionError('exhaustive original tie obligation')
    current = [dict(c.execute('SELECT * FROM _node_record WHERE node_id=?',(n,)).fetchone()) for n in [12567,12568]]
    for row in current:
        props = json.loads(row['properties_json'])
        if set(props)!={'content','hasFFS','hasTBD','resolutionId','sequence'}:
            raise AssertionError(('new alternate metadata', row['node_id'], set(props)))
    receipt = {'status':'ACTUAL_BOUNDED_SOURCE_AND_RETAINED_EVENT_CLOSURE',
               'id':'RAN1_P2_CQ5-10', 'utc':datetime.now(timezone.utc).isoformat(),
               'original_archives_reopened':len(originals), 'current_loader_same_DOCX_as_physical_original':True,
               'same_121_agenda_9_11_3_retained_nodes':len(same),
               'broad_cross_history_applicability_alternate_candidates':len(broad),
               'all_original_top10_tie_possibilities':len(possibilities),
               'minimum_source_deletion_witnesses_per_original_tie_selection':min(len(x['source_deletion_witnesses_in_set']) for x in possibilities),
               'current_two_node_only_properties':['content','hasFFS','hasTBD','resolutionId','sequence'],
               'current_two_node_incident_roles':['MADE_AT','RESOLUTION_BELONGS_TO'],
               'manually_read_all_same_event_context':True,
               'manually_read_broad_alternates':False,
               'limits':['The broad alternate file must be substantively read before absence is used as a final-review premise.',
                         'Exact-stem and event context scope do not amount to proof that no mathematical paraphrase anywhere could ever be inferred.',
                         'Original literal query candidate sets contain a demonstrated foreign-proposal role error and are not gold/admissible source-verified answers.'],
               'API_native_public_central_actions':0,'human_expert_n':0,'nonblind_AI':True,'original560_pass_increment':0}
    for n,d in [('actual_two_original_report_sources.json',originals),('all_same_event_agenda_retained_nodes_and_edges.json',same),
                ('broad_applicability_alternative_candidates.json',broad),('all_original_literal_cutoff_combinations_NOT_GOLD.json',possibilities),('receipt.json',receipt)]:
        (out/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__':
    main()
