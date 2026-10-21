"""Source-cell and character-property replay using the original binary reader."""
import hashlib
import io
import re
import xml.etree.ElementTree as ET
import zipfile

H = lambda b: hashlib.sha256(b).hexdigest()
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
norm = lambda s: re.sub(r'\s+', ' ', s).strip()


def inline(el):
    out = []
    for e in el.iter():
        if e.tag == W + 't': out.append(e.text or '')
        elif e.tag == W + 'tab': out.append('\t')
        elif e.tag in {W + 'br', W + 'cr'}: out.append('\n')
    return ''.join(out)


def text(el):
    if el.tag == W + 'p': return inline(el)
    if el.tag == W + 'tbl':
        return '\n'.join('\t'.join(text(tc) for tc in tr.findall(W + 'tc')) for tr in el.findall(W + 'tr'))
    ps = el.findall(W + 'p')
    return '\n'.join(inline(p) for p in ps) if ps else inline(el)


def run(here, source_index, field_proof, approval_proof, strike_proof, root_source_proof, selected, reader, style):
    native = {}; xml = {}; originals = {}
    for item in source_index:
        archive = here / item['local_archive']
        rawzip = archive.read_bytes()
        assert H(rawzip) == item['archive_sha256']
        with zipfile.ZipFile(io.BytesIO(rawzip)) as z:
            assert z.testzip() is None
            raw = z.read(item['member'])
        assert H(raw) == item['member_sha256'] and len(raw) == item['member_bytes']
        tid = item['tdocNumber']; originals[tid] = raw
        if raw[:8] == bytes.fromhex('d0cf11e0a1b11ae1'):
            native[tid] = reader.parse_doc(raw)
        else:
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                xml[tid] = ET.fromstring(z.read('word/document.xml'))
    assert len(source_index) == 8 and len(native) == 7 and len(xml) == 1
    selected_by_id = {r['tdocNumber']: r for r in selected}
    for row in field_proof['fields']:
        tid, field = row['tdocNumber'], row['field']
        expected = selected_by_id[tid]['reason' if field == 'reasonForChange' else 'summary']
        if tid in native:
            source_fields = style.source_fields(native[tid][0])
            candidates = [r for r in source_fields if r['field'] == field]
            assert len(candidates) == 1
            value = candidates[0]['transcribed_value']
            assert row['original_Word97_field']['cp_start'] == candidates[0]['cp_start']
            assert row['original_Word97_field']['cp_end'] == candidates[0]['cp_end']
        else:
            cells = []
            for tbl in xml[tid].iter(W + 'tbl'):
                for tr in tbl.findall(W + 'tr'):
                    tcs = tr.findall(W + 'tc')
                    if len(tcs) >= 2 and norm(text(tcs[0])) == row['label']: cells.append(tcs[1])
            assert len(cells) == 1
            value = text(cells[0])
        assert norm(value) == norm(expected) == norm(row['source_literal']) == norm(row['frozen_value'])
    assert len(field_proof['fields']) == 10
    for report in approval_proof['reports']:
        tid = report['report']; raw = originals[tid]
        parsed, direct, meta = native[tid]
        assert meta == report['original_binary_parse'] and H(parsed.encode()) == report['whole_text_sha256']
        styles = style.stylesheet(raw)
        assert styles == report['stylesheet'] and not styles['watched_style_operations']
    for row in approval_proof['rows']:
        parsed, direct, _ = native[row['report']]
        a, b = row['approval_CP_range']; ca, cb = row['own_context_CP_range']
        assert parsed[a:b] == row['approval_text'] and parsed[ca:cb] == row['own_context']
        assert parsed[row['target_CP']:row['target_CP'] + len(row['tdocNumber'])] == row['tdocNumber']
        checked = 0
        styles = style.stylesheet(originals[row['report']]); bystyle = {r['istd']:r for r in styles['styles']}
        for run in row['binary_character_runs']:
            assert run['cp_start'] == ca + checked
            assert run['text'] == parsed[run['cp_start']:run['cp_end']]
            for cp in range(run['cp_start'], run['cp_end']):
                actual = direct(cp); saved = run['raw_direct_evidence']
                assert {k:v for k,v in actual.items() if k not in {'cp','fc'}} == {k:v for k,v in saved.items() if k not in {'cp','fc'}}
                checked += 1
            d = direct(run['cp_start']); ops = style.expand_ops(d['direct_PRLs'] + d['piece_character_PRLs'])
            assert not [op for op in ops if int(op['sprm'],16) in style.WATCH]
            for op in ops:
                if int(op['sprm'],16) in (0x4a30,0x2a32,0x2a33,0xca85):
                    assert int(op['sprm'],16) == 0x4a30
                    assert int.from_bytes(bytes.fromhex(op['operand_hex']), 'little') in bystyle
        assert checked == cb - ca and row['active_outcome_character_gate'] is True
    assert len(approval_proof['rows']) == 5
    # Preserve the genuine direct-strike counterreading in an archival field.
    parsed, direct, _ = native[strike_proof['tdocNumber']]
    styles = style.stylesheet(originals[strike_proof['tdocNumber']])
    assert styles == strike_proof['whole_stylesheet'] and not styles['watched_style_operations']
    witness = strike_proof['strike_witness']; a, b = witness['cp_start'], witness['cp_end']
    assert parsed[a:b] == witness['literal'] == 'to be transmitted' and b-a == 17
    for cp, saved in zip(range(a,b), witness['characters']):
        d = direct(cp)
        assert d == saved['direct_evidence'] and parsed[cp] == saved['character']
        flags = [op for op in d['direct_PRLs'] + d['piece_character_PRLs'] if int(op['sprm'],16)==0x0837]
        assert flags and flags[-1]['operand_hex'] == '81' and saved['effective_native_strike'] is True
    # Independently rebind every ROOT report-target observation, including
    # revisions/intended outcomes, without selecting only favorable windows.
    for hit in root_source_proof['all_selected_report_target_windows']:
        parsed = native[hit['report']][0]; cp = hit['cp']; target = hit['target']
        assert parsed[cp:cp + len(target)] == target
        actual = parsed[max(0, cp-450):min(len(parsed), cp+len(target)+650)]
        assert H(actual.encode()) == hit['source_window_sha256']
    assert len(root_source_proof['all_selected_report_target_windows']) == 18
    return dict(original_archives=8, original_binary_members=7, original_OOXML_members=1,
                requested_source_fields=10, active_approval_roles=5, report_target_windows=18,
                retained_struck_literal_characters=17)
