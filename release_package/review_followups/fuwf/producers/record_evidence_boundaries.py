#!/usr/bin/env python3
"""Check frozen/example boundaries and pinned comparator/disclosure scope."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import urllib.request
import xml.etree.ElementTree as ET
import zipfile


PREFIX = 'https://w3id.org/spectra/inst/RAN1/'
PUBLIC_REVISION = '2b6f57e9b0cac90252b9fb4c8847bd67315a3222'
COMPARATOR_REVISION = 'e6487ae660852b56e6d9952680f661215a53ec46'
ETSI_URL = 'https://www.etsi.org/deliver/etsi_ts/138200_138299/138213/17.04.00_60/ts_138213v170400p.pdf'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
G = '{http://graphml.graphdrawing.org/xmlns}'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def normalized(text):
    return re.sub(r'\s+', ' ', text).strip()


def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def download(url, path, cap):
    request = urllib.request.Request(url, headers={'User-Agent': 'source-boundary-audit/1'})
    with urllib.request.urlopen(request, timeout=45) as response:
        data = response.read(cap + 1)
        assert len(data) <= cap
        path.write_bytes(data)
        return {'official_url': url, 'http_status': response.status,
                'bytes': len(data), 'sha256': digest(path)}


def frozen_blocks(path, subjects):
    found, lines, current = {}, [], None
    with path.open() as f:
        for line_number, line in enumerate(f, 1):
            if line.startswith('<'):
                if current in subjects:
                    assert current not in found
                    found[current] = {'first_line': first_line,
                                      'text': ''.join(lines)}
                current = line.split('>', 1)[0][1:]
                first_line, lines = line_number, []
            if current in subjects:
                lines.append(line)
    if current in subjects:
        found[current] = {'first_line': first_line, 'text': ''.join(lines)}
    assert set(found) == subjects
    for block in found.values():
        block['block_sha256'] = hashlib.sha256(block['text'].encode()).hexdigest()
    return found


def inspect_comparator(base, ids):
    folder = base / 'comparison-resume-tail'
    old = json.loads((folder / 'artifact_scope.json').read_text())
    downloads = json.loads((folder / 'downloads.json').read_text())
    assert downloads['revision'] == COMPARATOR_REVISION
    pattern = re.compile(r'(?<![A-Za-z0-9])(?:' + '|'.join(sorted(ids)) + r')(?![A-Za-z0-9])')
    pins, keys, counts, fields, found = [], {}, Counter(), Counter(), Counter()
    graph = folder / 'telecom-kg-rel19.graphml'
    chunks = folder / 'telecom-kg-rel19-chunks.jsonl'
    for path in [graph, chunks]:
        original = next(x for x in downloads['artifacts'] if Path(x['path']).name == path.name)
        assert digest(path) == original['sha256']
        assert path.stat().st_size == original['bytes']
        pins.append({k: original[k] for k in ['url', 'bytes', 'sha256']})
    root = None
    for event, item in ET.iterparse(graph, events=('start', 'end')):
        if root is None:
            root = item
        if event != 'end':
            continue
        tag = item.tag.removeprefix(G)
        if tag == 'key':
            keys[item.attrib['id']] = dict(item.attrib)
        elif tag in ('node', 'edge'):
            counts[tag] += 1
            row = {keys[x.attrib['key']]['attr.name']: x.text or '' for x in item.findall(G + 'data')}
            fields.update(row.keys())
            found.update(pattern.findall(' '.join(row.values()) + ' ' + json.dumps(item.attrib)))
            item.clear()
            root.clear()
    assert dict(counts) == old['graph']['counts'] == {'node': 21540, 'edge': 31718}
    chunk_n, empty_n, chunk_fields, chunk_found = 0, 0, Counter(), Counter()
    with chunks.open() as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            chunk_n += 1
            empty_n += not row.get('text', '')
            chunk_fields.update(row.keys())
            chunk_found.update(pattern.findall(json.dumps(row)))
    assert chunk_n == empty_n == old['chunks']['records'] == 896453
    assert digest(graph) == pins[0]['sha256'] and digest(chunks) == pins[1]['sha256']
    return {'status': 'PASS', 'revision': COMPARATOR_REVISION, 'input_pins': pins,
            'scope': 'Complete pinned GraphML data/record attributes and complete chunk JSONL; not the authors entire system or an alternative document-augmented deployment.',
            'graph_records': dict(counts), 'graph_attribute_names': sorted(fields),
            'chunk_records': chunk_n, 'empty_chunk_text_records': empty_n,
            'chunk_attribute_names': sorted(chunk_fields),
            'liaison_slice_TDoc_ids_checked': sorted(ids),
            'graph_literal_slice_TDoc_mentions': dict(found),
            'chunk_literal_slice_TDoc_mentions': dict(chunk_found),
            'claim': 'These downloaded artifacts do not expose the original liaison To-field records used in the audited slice as source-linked native routing records.',
            'limits': 'Literal ID/field absence does not prove absence of general liaison concepts, history or capabilities elsewhere. No practitioner benefit or QA superiority was measured.',
            'expert_reviews': 0, 'model_calls': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    base, out = args.base, args.output
    out.mkdir(exist_ok=False)
    inputs = out / 'original-downloads'
    inputs.mkdir()
    write(out / 'protocol.json', {'status': 'DEFINED_BEFORE_COMPARISON',
          'classification': {'frozen_vs_followup_trace': 'c: new scoped measurement',
                             'comparator_slice_record_scope': 'c: new full artifact scan',
                             'public_vs_local_disclosure': 'b: source attribution correction'},
          'sample_change': False, 'KG_mutation': False,
          'model_calls': 0, 'expert_reviews': 0})
    frozen = Path('release_package/kg/per_wg/RAN1-body.ttl')
    pin = json.loads((base / 'decision_trace_actual_graph.json').read_text())['frozen_sha256']['RAN1']
    assert digest(frozen) == pin
    resolution = PREFIX + 'Resolution/AGR-110b-8.12-007'
    cr = PREFIX + 'Tdoc/tdoc:R1-2210700'
    section = PREFIX + 'Section/38.213-Rel-17-18'
    pack = PREFIX + 'CRPack/anon_387297736244'
    meeting = PREFIX + 'Meeting/tdoc:meeting%2FRAN1_110b-e'
    agenda = PREFIX + 'AgendaItem/tdoc:agenda%2F110b-8.12'
    blocks = frozen_blocks(frozen, {resolution, cr, section, pack, meeting, agenda})
    assert 'spectra:references' in blocks[resolution]['text'] and '<' + cr + '>' in blocks[resolution]['text']
    assert 'spectra:madeAt <' + meeting + '>' in blocks[resolution]['text']
    assert 'spectra:resolutionBelongsTo <' + agenda + '>' in blocks[resolution]['text']
    assert 'spectra:modifiesSection <' + section + '>' in blocks[cr]['text']
    assert 'spectra:tsgCRPack "RP-222864"' in blocks[cr]['text']
    assert 'spectra:crPackId "RP-222864"' in blocks[pack]['text'] and '<' + cr + '>' in blocks[pack]['text']
    assert digest(frozen) == pin
    boundary = {'status': 'PASS', 'example': 'R1-2210700/CR0388', 'frozen_input_sha256': pin,
                'frozen_records': blocks,
                'already_in_frozen_snapshot': ['resolution REFERENCES final CR', 'resolution MADE_AT meeting',
                    'resolution RESOLUTION_BELONGS_TO agenda', 'CR MODIFIES_SECTION Rel17/clause18',
                    'CR belongsToCrPack and tsgCRPack RP-222864'],
                'established_by_additional_native_source_investigation': [
                    'Agreement wording authenticated against the original minutes paragraph',
                    'Native CR cover and full tracked insertion authenticated',
                    'Complete inserted paragraph absent from TS17.3.0 and exactly present in TS17.4.0 clause18',
                    'Native TS17.4.0 change history lists CR0388/RP-222864 and result version',
                    'Native RP member contains same proposed insertion'],
                'source_evidence': 'refinement/normative-trace/evidence-excerpt.json',
                'boundary': 'The complete incorporation chain was assembled by additional source investigation, not returned by an automated frozen-KG query. Existing graph links alone do not prove incorporation.',
                'absence_scope': 'No global absence claim is made about normative version nodes or literal text elsewhere in the KG.',
                'expert_reviews': 0, 'model_calls': 0}
    write(out / 'trace_boundary.json', boundary)
    with (base / 'verified-routing-slice/records.csv').open(newline='') as f:
        ids = {x['tdoc_number'] for x in csv.DictReader(f)}
    assert len(ids) == 47
    write(out / 'comparator_scope.json', inspect_comparator(base, ids))
    public_url = ('https://raw.githubusercontent.com/spectra-ontology/spec-trace/' + PUBLIC_REVISION +
                  '/release_package/cqs/original_core_repair/REVIEW_GUIDE.md')
    public = download(public_url, inputs / 'public-REVIEW_GUIDE.txt', 65536)
    guide = (inputs / 'public-REVIEW_GUIDE.txt').read_text()
    assert not re.search(r'cutoff.?tie|67 retained controls|eight.*defects', guide, re.I)
    write(out / 'public_disclosure.json', {'status': 'PASS', 'revision': PUBLIC_REVISION,
          'public_guide_receipt': public, 'public_guide_content': guide,
          'public_guide_scope': 'Original-question repair review instructions and admitted/pending distinction.',
          'local_followup_defect_entry': 'refinement/other-session-contract-review.json',
          'defect_count': 8, 'local_proposals_admitted': False, 'local_proposals_published': False,
          'correction': 'The eight scorer defects and local correction proposals are disclosed in this new local follow-up supplement, not in the pinned public REVIEW_GUIDE.md.',
          'does_not_establish_no_score_effect': True})
    receipt = download(ETSI_URL, inputs / 'ts-38-213-v17-4-0.pdf', 8 * 1024**2)
    import fitz
    pdf = fitz.open(inputs / 'ts-38-213-v17-4-0.pdf')
    pages = [page.get_text(sort=True) for page in pdf]
    trace = json.loads((base / 'refinement/normative-trace/evidence-excerpt.json').read_text())
    wg = trace['sources']['WG_CR']
    archive = Path(wg['local_path'])
    assert digest(archive) == wg['archive_sha256']
    with zipfile.ZipFile(archive) as z:
        native = z.read(wg['native_member'])
    assert hashlib.sha256(native).hexdigest() == wg['native_docx_sha256']
    import io
    with zipfile.ZipFile(io.BytesIO(native)) as z:
        body = ET.fromstring(z.read('word/document.xml')).find(W + 'body')
    # Only w:t text, excluding XML indentation and unrelated run metadata.
    paragraph = normalized(''.join(t.text or '' for t in body[17].iter(W + 't')))
    assert hashlib.sha256(paragraph.encode()).hexdigest() == trace['evidence'][2]['normalized_complete_paragraph_sha256']
    # A PDF line break after an existing hyphen splits pdsch-HARQ; rejoin only
    # that literal wrapping class, without altering letters or sentence words.
    def pdf_normalized(text):
        return normalized(re.sub(r'-[ \t]*\r?\n[ \t]*(?=[A-Za-z])', '-', text))
    matches = [i for i, text in enumerate(pages) if paragraph in pdf_normalized(text)]
    words = pdf[260].get_text('words')
    markers = [word for word in words if word[4] == '0388']
    assert len(markers) == 1
    marker = markers[0]
    history = [' '.join(word[4] for word in sorted(words, key=lambda w: w[0])
                       if marker[1] <= (word[1] + word[3]) / 2 <= marker[3])]
    assert matches == [248] and len(history) == 1
    assert all(value in history[0] for value in ['2022-12', 'RAN#98-e', 'RP-222864', '0388', '17.4.0'])
    write(out / 'external_document_access.json', {'status': 'PASS', 'ETSI_receipt': receipt,
          'normative_sentence_pdf_page_zero_based': 248, 'normative_sentence_printed_page': 248,
          'normative_sentence_normalized_sha256': hashlib.sha256(paragraph.encode()).hexdigest(),
          'complete_sentence_equal_after_declared_PDF_line_wrap_normalization': True,
          'PDF_normalization': 'Rejoin ASCII hyphen followed by line break before an alphabetic character, then collapse whitespace; no fuzzy or semantic matching.',
          'PDF_decoder': 'PyMuPDF ' + fitz.VersionBind,
          'change_history_pdf_page_zero_based': 260, 'change_history_printed_page': 260,
          'change_history_row': history[0],
          'native_WG_archive_sha256': wg['archive_sha256'],
          'limit': 'Accessible official PDF corroborates the final sentence and version-history row only; it is not independent human verification of all links or raw DOCX byte identity.',
          'expert_reviews': 0, 'model_calls': 0})
    pdf[260].get_pixmap(matrix=fitz.Matrix(1.5, 1.5),
        clip=fitz.Rect(10, marker[1]-5, 600, marker[3]+5)).save(inputs / 'history-row.png')
    sentence_rects = pdf[248].search_for('For a UE that is indicated the second HARQ-ACK reporting mode, the UE does not expect')
    assert sentence_rects
    sentence_top = min(rect.y0 for rect in sentence_rects)
    pdf[248].get_pixmap(matrix=fitz.Matrix(1.5, 1.5),
        clip=fitz.Rect(10, sentence_top-5, 600, sentence_top+30)).save(inputs / 'normative-sentence.png')
    write(out / 'results.json', {'status': 'PASS', 'frozen_records_checked': len(blocks),
          'comparator_liaison_ids_checked': len(ids), 'public_disclosure_scope_corrected': True,
          'ETSI_pdf_final_sentence_and_history_checked': True,
          'producer_sha256': digest(Path(__file__)), 'model_calls': 0, 'expert_reviews': 0})
    print(json.dumps({'status': 'PASS', 'frozen_records': len(blocks), 'slice_ids': len(ids), 'ETSI_pages': [248, 260]}))


if __name__ == '__main__':
    main()
