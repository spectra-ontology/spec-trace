#!/usr/bin/env python3
"""Rebind the same fixed source-first CR members to their native cover IDs.

Preserves the initial sample and results. The old \b regex rejects identifiers
preceded by underscores in original member names. Current IDs are determined
from original pre-CHANGE REQUEST headers, independently of graph outcomes.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.parse
import zipfile


def mod(path, name):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def write(path, data):
    with path.open('x') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', type=Path, required=True)
    p.add_argument('--scripts', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(exist_ok=False)
    rd = mod(a.scripts/'source_audit.py', 'fuwf_original_reader')
    native = mod(a.scripts/'native_cr_audit.py', 'fuwf_original_native_reader')
    sample = json.loads((a.base/'source-audit/sampling.json').read_text())
    cases = [c for c in sample['cases'] if c['relation'] == 'MODIFIES_SECTION'
             and c['direction'] == 'source_first']
    anti = a.base/'legacy-reader/extracted/usr/bin/antiword'
    env = dict(os.environ, ANTIWORDHOME=str((anti.parent.parent/'share/antiword').resolve()))
    write(a.output/'protocol.json', {
        'selected_n': len(cases), 'identities': [c['sample_identity'] for c in cases],
        'sampling_sha256': rd.digest(a.base/'source-audit/sampling.json'),
        'producer_sha256': rd.digest(Path(__file__)),
        'reader_sha256': rd.digest(a.scripts/'source_audit.py'),
        'native_reader_sha256': rd.digest(a.scripts/'native_cr_audit.py'),
        'antiword_sha256': rd.digest(anti),
        'reason': 'Original filename regex word boundaries reject underscore-prefixed current TDoc IDs and can select older rev-of IDs.',
        'binding_rule': 'Exactly one distinct TDoc ID on native pre-CHANGE REQUEST header rows, excluding rows explicitly marked was/revision/rev of/endorsed/from/ex-. Must equal first filename TDoc ID. No graph-dependent choice.',
        'comparison_rule': 'Exactly one frozen CR/TDoc subject; exactly one native field/spec/release; complete simple clause lists, no range expansion; all other cases remain unresolved.',
        'same_sample': 'Member/archive identities, ranks and all denominators unchanged; old results retained. Original frame itself was affected, so this is a correction on that fixed sample, not an unbiased corpus estimate.',
        'replacement_n': 0, 'model_calls': 0, 'expert_reviews': 0,
        'registered_before_corrected_graph_scan': True})
    rows, pins = [], {}
    loose = re.compile(r'R[1-5]-\d{6,7}(?!\d)', re.I)
    oldmarker = re.compile(r'\b(?:was|revision|revised|rev\s+of|endorsed|from)\b|ex-', re.I)
    # Bind source identities BEFORE scanning the graph or seeing corrected sets.
    for c in cases:
        s = c['source']; path = Path(s['source_path'])
        pins.setdefault(str(path), rd.digest(path))
        with zipfile.ZipFile(path) as z:
            data = z.read(s['member'])
        row = {'identity': c['sample_identity'], 'wg': c['wg'],
               'selection_rank': c['selection_rank'], 'old_tdoc': s['tdoc'],
               'archive': str(path), 'archive_sha256': pins[str(path)],
               'member': s['member'], 'member_sha256': hashlib.sha256(data).hexdigest(),
               'archive_release': s['release'], 'status': 'unresolved'}
        try:
            if data.startswith(b'PK'):
                units = rd.paragraphs(data)
                fields, spec, release = rd.cr_fields(units)
                specs, releases = ([spec] if spec else []), ([release] if release else [])
                row['decoder'] = 'native_OOXML'
            else:
                proc = subprocess.run([str(anti.resolve()), '-t', '-w', '0', '-m', 'UTF-8.txt', '-'],
                    input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=30)
                if proc.returncode:
                    raise ValueError('antiword exit '+str(proc.returncode))
                text = proc.stdout.decode('utf-8')
                fields, specs, releases = native.binary_fields(text)
                units = [{'text': t, 'locator': {'decoder_line': i+1}}
                         for i, t in enumerate(text.splitlines())]
                row.update(decoder='antiword', decoded_text_sha256=hashlib.sha256(proc.stdout).hexdigest())
            header, marker = [], False
            for u in units:
                if re.search(r'\bCHANGE\s+REQUEST\b', u['text'], re.I):
                    marker = True
                    break
                header.append(u)
            witnesses = [dict(u, ids=[x.upper() for x in loose.findall(u['text'])])
                         for u in header if loose.search(u['text']) and not oldmarker.search(u['text'])]
            ids = sorted({v for u in witnesses for v in u['ids']})
            named = [x.upper() for x in loose.findall(s['member'])]
            row.update(header_witnesses=witnesses, header_ids=ids,
                       filename_ids=named, fields=fields, specs=specs, releases=releases)
            if not marker or len(ids) != 1 or not named or ids[0] != named[0]:
                row['reason'] = 'native_current_header_unbound_or_conflicting_with_filename'
            else:
                row.update(current_tdoc=ids[0], binding_status='native_header_and_first_filename_ID_agree',
                           binding_changed=ids[0] != s['tdoc'])
        except Exception as e:
            row['reason'] = type(e).__name__+': '+str(e)
        rows.append(row)
    write(a.output/'source_bindings_before_graph.json', {'cases': rows, 'input_pins': pins})
    wanted = defaultdict(set)
    for r in rows:
        if r.get('current_tdoc'):
            wanted[r['wg']].add(r['current_tdoc'])
    graph = defaultdict(lambda: defaultdict(list)); turtle = rd.reader(); frozen = {}
    for wg in rd.WGS:
        path = rd.ROOT/f'release_package/kg/per_wg/{wg}-body.ttl'
        h = rd.digest(path)
        if h != rd.FROZEN[wg]:
            raise ValueError('Frozen graph drift: '+wg)
        frozen[wg] = {'path': rd.relpath(path), 'sha256': h}
        print('scan_corrected_native_bindings', wg, flush=True)
        for subject, types, text in turtle.blocks(path):
            if 'spectra:CR' not in types:
                continue
            tid = turtle.literal(text, 'spectra:tdocNumber')
            if tid not in wanted[wg]:
                continue
            rec = rd.graph_record(turtle, subject, types, text)
            rec['additional_literals'] = {p: turtle.literal(text, 'spectra:'+p)
                for p in ['title', 'crRelease', 'release', 'revision', 'crNumber', 'specNumber', 'type']}
            rec['frozen_block'] = text
            graph[wg][tid].append(rec)
    for r in rows:
        if not r.get('current_tdoc'):
            continue
        gs = graph[r['wg']][r['current_tdoc']]; r['graph_matches'] = gs
        if len(gs) != 1:
            r['reason'] = 'missing_or_nonunique_current_CR_graph_identity'
            continue
        if len(r['fields']) != 1 or len(r['specs']) != 1 or len(r['releases']) != 1:
            r['reason'] = 'nonunique_or_missing_native_field_spec_release'
            continue
        clauses, simple = rd.clause_tokens(r['fields'][0]['text'])
        if not clauses or not simple:
            r['reason'] = 'empty_or_complex_clause_list_no_expansion'
            continue
        expected = sorted({r['specs'][0]+'-'+r['releases'][0]+'-'+c for c in clauses})
        actual = sorted({urllib.parse.unquote(t.rsplit('/',1)[-1])
                         for t in gs[0]['targets']['MODIFIES_SECTION']})
        r['comparison'] = {'source_set': expected, 'graph_set': actual,
                           'source_only': sorted(set(expected)-set(actual)),
                           'graph_only': sorted(set(actual)-set(expected)), 'exact_equal': expected == actual}
        r['status'] = 'native_cover_set_match' if expected == actual else 'native_cover_set_difference'
    drift = [p for p,h in pins.items() if rd.digest(p) != h]
    drift += [v['path'] for v in frozen.values() if rd.digest(rd.ROOT/v['path']) != v['sha256']]
    result = {'selected_n': len(rows), 'counts': dict(Counter(r['status'] for r in rows)),
        'binding_changed_n': sum(r.get('binding_changed', False) for r in rows),
        'binding_confirmed_n': sum(bool(r.get('current_tdoc')) for r in rows),
        'cases': rows, 'source_pins': pins, 'frozen': frozen, 'drift_paths': drift,
        'validity': 'INVALID_INPUT_DRIFT' if drift else 'INPUTS_UNCHANGED',
        'model_calls': 0, 'expert_reviews': 0,
        'limits': ['Corrected audit binding is separate from any graph correction; no production data was changed.',
                   'Original source frame ID regex affected eligibility, so corrected fixed samples cannot certify corpus completeness.',
                   'Machine comparison of native cover fields; not final adoption, causal tracing, or expert validation.']}
    write(a.output/'results.json', result)
    print(json.dumps({k:result[k] for k in ['counts','binding_changed_n','binding_confirmed_n','drift_paths']}), flush=True)
    if drift:
        raise ValueError('Input drift')


if __name__ == '__main__':
    main()
