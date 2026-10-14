#!/usr/bin/env python3
"""Supplement the SAME 100 fixed CR samples with a native binary Word reader.

Original archive placement is metadata, not the authoritative release field.
The original cover's explicit release binds targets. Complex clauses, duplicate
documents, absent identities and decoder failures remain unresolved.
"""
import argparse
import collections
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.parse
import zipfile


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)


def load_reader(path):
    spec = importlib.util.spec_from_file_location('isolated_source_reader', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def binary_fields(text):
    lines = text.splitlines()
    fields = []
    for i, line in enumerate(lines):
        if not re.search(r'\bClauses?\s+affected\s*:', line, re.I):
            continue
        right = re.split(r'Clauses?\s+affected\s*:', line, flags=re.I)[1]
        values = [x.strip() for x in right.split('|') if x.strip()]
        value = ' '.join(values)
        end = i
        for j in range(i+1, min(i+9, len(lines))):
            cells = [x.strip() for x in lines[j].split('|')]
            if not any(cells):
                end = j
                continue
            if len(cells) >= 3 and not cells[1] and any(cells[2:]):
                continuation = ' '.join(x for x in cells[2:] if x)
                if re.fullmatch(r'[\dA-Za-z.,;\s]+', continuation):
                    value += ' ' + continuation
                    end = j
                    continue
            break
        fields.append({'text': value, 'locator': {'decoder_line_start': i+1, 'decoder_line_end': end+1},
                       'quote': '\n'.join(lines[i:end+1])})
    releases = sorted(set('Rel-' + x for x in re.findall(r'\bRelease\s*:\s*\|?\s*Rel[- ]?(\d+)\b', text, re.I)))
    specs = sorted(set(re.findall(r'^\s*3GPP\s+(?:TS|TR)\s+(\d{2}\.\d{3}(?:-\d+)?)\s+V', text, re.M)))
    return fields, specs, releases


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sampling', type=Path, required=True)
    p.add_argument('--reader', type=Path, required=True)
    p.add_argument('--antiword', type=Path, required=True)
    p.add_argument('--mapping', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    reader = load_reader(a.reader)
    sample = json.loads(a.sampling.read_text())
    cases = [c for c in sample['cases'] if c['relation'] == 'MODIFIES_SECTION']
    selected = [{'wg': c['wg'], 'direction': c['direction'], 'identity': c['sample_identity']} for c in cases]
    write(a.output/'protocol.json', {'selected': selected, 'selected_n': len(cases),
          'sampling_sha256': sha(a.sampling), 'reader_sha256': sha(a.reader), 'producer_sha256': sha(__file__),
          'antiword_sha256': sha(a.antiword), 'decoder': 'antiword 0.37, -t -w 0 -m UTF-8.txt, original DOC bytes via stdin',
          'release_binding': 'Explicit original cover release; archive directory mismatch is retained as provenance metadata.',
          'clause_rule': 'Nonempty simple explicit clause lists only; no ranges or inferred expansions.',
          'comparison_scope': 'Entire original Clauses affected field in the SAME selected 100 records; unique graph/source identities only.',
          'replacement_n': 0, 'expert_review_n': 0, 'model_calls': 0})
    before, results, transcripts = {}, [], []
    for wg in reader.WGS:
        candidates = reader.cr_candidates(wg)
        for case in (c for c in cases if c['wg'] == wg):
            if case['direction'] == 'source_first':
                sources, graphs = [case['source']], case['graph_matches']
            else:
                sources = [s for s in candidates if s['tdoc'] == case['graph']['tdoc']]
                graphs = [case['graph']]
            result = {'wg': wg, 'direction': case['direction'], 'identity': case['sample_identity'],
                      'source_document_n': len(sources), 'graph_identity_n': len(graphs),
                      'status': 'unresolved', 'documents': []}
            for source in sources:
                path = Path(source['source_path'])
                before.setdefault(str(path), sha(path))
                with zipfile.ZipFile(path) as z:
                    data = z.read(source['member'])
                doc = {'archive': str(path), 'archive_sha256': before[str(path)], 'member': source['member'],
                       'member_sha256': hashlib.sha256(data).hexdigest(), 'archive_release': source['release']}
                result['documents'].append(doc)
                try:
                    if data.startswith(b'PK'):
                        rows = reader.paragraphs(data)
                        fields, spec_value, rel_value = reader.cr_fields(rows)
                        specs, releases = ([spec_value] if spec_value else []), ([rel_value] if rel_value else [])
                        doc['decoder'] = 'native_OOXML'
                    else:
                        env = dict(os.environ, ANTIWORDHOME=str(a.mapping.resolve()))
                        proc = subprocess.run([str(a.antiword.resolve()), '-t', '-w', '0', '-m', 'UTF-8.txt', '-'],
                                              input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, env=env)
                        if proc.returncode:
                            raise ValueError('antiword exit ' + str(proc.returncode) + ': ' + proc.stderr.decode(errors='replace')[:250])
                        text = proc.stdout.decode('utf-8', errors='strict')
                        fields, specs, releases = binary_fields(text)
                        key = hashlib.sha256((str(path)+'::'+source['member']).encode()).hexdigest()
                        transcripts.append({'document_key': key, 'archive': str(path), 'member': source['member'],
                                            'decoded_text_sha256': hashlib.sha256(proc.stdout).hexdigest(), 'text': text})
                        doc.update(decoder='antiword', decoded_text_sha256=hashlib.sha256(proc.stdout).hexdigest(),
                                   transcript_key=key, stderr=proc.stderr.decode(errors='replace'))
                    member_spec = re.search(r'(?:^|/)(\d{2})(\d{3})(?:_|-)', source['member'])
                    named_spec = '.'.join(member_spec.groups()) if member_spec else None
                    if not specs and named_spec:
                        specs = [named_spec]
                        doc['spec_binding'] = 'original_archive_member_identifier; body_spec_header_unavailable'
                    else:
                        doc['spec_binding'] = 'original_document_spec_field_or_body_header'
                    doc.update(fields=fields, specs=specs, native_releases=releases, member_spec=named_spec)
                    if (len(fields) != 1 or len(specs) != 1 or len(releases) != 1 or len(graphs) != 1
                            or (named_spec and specs[0] != named_spec)):
                        doc.update(status='unresolved', reason='nonunique_or_conflicting_field_spec_release_graph_identity')
                        continue
                    tokens, simple = reader.clause_tokens(fields[0]['text'])
                    if not tokens or not simple:
                        doc.update(status='unresolved', reason='empty_or_complex_clause_syntax')
                        continue
                    expected = sorted({specs[0]+'-'+releases[0]+'-'+c for c in tokens})
                    actual = sorted({urllib.parse.unquote(x.rsplit('/',1)[-1]) for x in graphs[0]['targets']['MODIFIES_SECTION']})
                    doc['comparison'] = {'source_set': expected, 'graph_set': actual,
                                         'source_only': sorted(set(expected)-set(actual)),
                                         'graph_only': sorted(set(actual)-set(expected)), 'exact_equal': expected == actual}
                    doc['archive_release_agrees'] = releases[0] == source['release']
                    doc['status'] = 'field_set_match' if expected == actual else 'field_set_mismatch'
                except Exception as error:
                    doc.update(status='unresolved', reason=type(error).__name__+': '+str(error))
            if len(sources) == 1:
                result['status'] = result['documents'][0]['status']
            else:
                result['reason'] = 'missing_or_duplicate_source_documents_no_favorable_choice'
            results.append(result)
    drift = [path for path, value in before.items() if sha(path) != value]
    counts = collections.defaultdict(collections.Counter)
    for row in results:
        counts[row['direction']][row['status']] += 1
        counts[row['direction']]['selected_n'] += 1
    write(a.output/'results.json', {'selected_n': len(results), 'counts': {k:dict(v) for k,v in counts.items()},
          'cases': results, 'input_before_sha256': before, 'drift_paths': drift,
          'validity': 'INVALID_INPUT_DRIFT' if drift else 'INPUTS_UNCHANGED', 'model_calls': 0, 'expert_reviews': 0,
          'limits': ['Field-level machine audit, not process-causality validation or a corpus accuracy estimate.',
                     'Antiword text extraction can omit Word objects and revision state; ambiguous fields retained unresolved.',
                     'Archive release differs in some documents; explicit source release is authoritative.',
                     'This supplementary reader does not replace or erase the initial audit results.']})
    with (a.output/'native_transcripts.jsonl').open('x') as f:
        for row in transcripts:
            f.write(json.dumps(row, ensure_ascii=False)+'\n')
    print(json.dumps({'counts': {k:dict(v) for k,v in counts.items()}, 'drift': drift}), flush=True)
    if drift:
        raise ValueError('Input drift')


if __name__ == '__main__':
    main()
