import argparse
import gc
import json
import re
from collections import Counter, defaultdict


def graph(path):
    with open(path) as stream:
        return json.load(stream)['@graph']


def values(value):
    return value if isinstance(value, list) else ([] if value is None else [value])


def number(value):
    return value.removeprefix('tdoc:')


def load_records():
    state = {}
    state['meetings'] = {r['@id']: r['tdoc:meetingNumber'] for r in graph('records/phase-1/meetings.jsonld')}
    state['releases'] = {r['@id']: r['tdoc:releaseName'] for r in graph('records/phase-1/releases.jsonld')}
    keep = {'@id', 'tdoc:tdocNumber', 'tdoc:type', 'tdoc:status', 'presentedAt',
            'targetRelease', 'revisedTo', 'isRevisionOf', 'tdoc:crNumber',
            'tdoc:crRevision', 'tdoc:tsgCRPack', 'modifies', 'tdoc:clausesAffected'}
    state['docs'] = {r['@id']: {k: v for k, v in r.items() if k in keep}
                     for r in graph('records/phase-1/tdocs.jsonld')}
    gc.collect()
    state['packs'] = {r['@id']: r for r in graph('records/phase-4/crpacks.jsonld')}
    state['doc_packs'] = defaultdict(set)
    for p, r in state['packs'].items():
        for doc in values(r['hasCR']):
            state['doc_packs'][doc].add(p)
    state['sections'] = {r['@id']: set(values(r['modifiedByCR']))
                         for r in graph('records/phase-4/section_extensions.jsonld')}
    state['doc_sections'] = defaultdict(set)
    for section, docs in state['sections'].items():
        for doc in docs:
            state['doc_sections'][doc].add(section)
    state['extensions'] = {r['@id']: {k: v for k, v in r.items()
                                     if k in {'belongsToCRPack', 'modifiesSection'}}
                           for r in graph('records/phase-4/cr_extensions.jsonld')}
    gc.collect()
    state['resolutions'] = {}
    for filename in ['resolutions_document_dispositions.jsonld', 'resolutions_agreements.jsonld',
                     'resolutions_conclusions.jsonld', 'resolutions_working_assumptions.jsonld']:
        for r in graph('records/phase-2/' + filename):
            state['resolutions'][r['@id']] = r.get('madeAt')
        gc.collect()
    state['dispositions'] = defaultdict(list)
    for r in graph('records/phase-2/decision_dispositions.jsonld'):
        a = json.loads(r['assessmentMethod'])
        state['dispositions'][r['dispositionTarget']].append({
            'code': r['dispositionCode'], 'status': r['evidenceStatus'],
            'scope': a.get('scope'), 'resolution': r['dispositionOf'],
            'subject': a.get('subject'), 'rule': a.get('rule'),
            'quote': r['evidenceQuote'],
        })
    gc.collect()
    state['revisions'] = defaultdict(set)
    for doc, r in state['docs'].items():
        for newer in values(r.get('revisedTo')):
            state['revisions'][doc].add(newer)
        for older in values(r.get('isRevisionOf')):
            state['revisions'][older].add(doc)
    return state


def valid_dispositions(state, doc):
    output = set()
    for r in state['dispositions'].get(doc, []):
        if r['status'] == 'source_verified' and r['scope'] == 'whole_target':
            meeting_id = state['resolutions'][r['resolution']]
            output.add((r['code'], state['meetings'][meeting_id]))
    return sorted(output)


def descendants(state, root):
    found = set()
    pending = list(state['revisions'].get(root, []))
    while pending:
        doc = pending.pop()
        if doc == root or doc in found:
            continue
        found.add(doc)
        pending.extend(state['revisions'].get(doc, []))
    return found


def solve(state, question):
    sentence = question['question']
    rows = set()
    note = ''
    if sentence.startswith('In which TSG RAN CR pack'):
        doc = 'tdoc:' + re.search(r'R2-\d+', sentence).group()
        for pack_id in state['doc_packs'].get(doc, []):
            pack = state['packs'][pack_id]
            rows.add((pack['tdoc:crPackId'], pack['tdoc:tsgMeeting']))
        if not rows:
            note = f'No CR-pack membership is recorded for the exact document {number(doc)}.'
            status = state['docs'].get(doc, {}).get('tdoc:status')
            if status:
                note += f' Its document list status is "{status}".'
    elif sentence.startswith('TSG RAN CR pack'):
        pack_id = 'tdoc:crpack/' + re.search(r'RP-\d+', sentence).group()
        for doc in values(state['packs'][pack_id]['hasCR']):
            for code, meeting in valid_dispositions(state, doc):
                rows.add((number(doc), code, meeting))
    elif sentence.startswith('RAN2 recorded document'):
        root = 'tdoc:' + re.search(r'R2-\d+', sentence).group()
        for doc in descendants(state, root):
            for code, _ in valid_dispositions(state, doc):
                for pack_id in state['doc_packs'].get(doc, []):
                    rows.add((number(doc), code, state['packs'][pack_id]['tdoc:crPackId']))
        note = ('Interpreted "every later version" as every reachable revision satisfying the stated filters, '
                'including intermediate versions. An alternative is to include only terminal versions.')
    elif sentence.startswith('Which Rel-'):
        release = re.search(r'Rel-\d+', sentence).group()
        clause, spec = re.search(r'modify clause (.*?) of TS ([\d.]+)', sentence).groups()
        section_prefix = 'tdoc:section/' + spec + '-' + release + '-'
        section = section_prefix + clause
        for doc in state['sections'].get(section, []):
            r = state['docs'].get(doc, {})
            if release not in [state['releases'].get(v) for v in values(r.get('targetRelease'))]:
                continue
            if 'tdoc:spec/' + spec.replace('.', '_') not in values(r.get('modifies')):
                continue
            if r.get('tdoc:type') != 'CR':
                continue
            for code, meeting in valid_dispositions(state, doc):
                for pack_id in state['doc_packs'].get(doc, []):
                    rows.add((number(doc), code, meeting, state['packs'][pack_id]['tdoc:crPackId']))
        note = (f'Interpreted "modify clause {clause}" as an explicit link to that exact clause. '
                'A broader reading could include changes linked only to its subclauses.')
    else:
        doc = 'tdoc:' + re.search(r'R2-\d+', sentence).group()
        for code, meeting in valid_dispositions(state, doc):
            for pack_id in state['doc_packs'].get(doc, []):
                pack = state['packs'][pack_id]
                base = (code, meeting, pack['tdoc:crPackId'], pack['tdoc:tsgMeeting'])
                if sentence.startswith('Trace change request'):
                    spec = re.search(r'to TS ([\d.]+)', sentence).group(1)
                    for section in state['doc_sections'].get(doc, []):
                        match = re.fullmatch(r'tdoc:section/([\d.]+)-Rel-\d+-(.*)', section)
                        if match and match.group(1) == spec:
                            rows.add(base + (match.group(2),))
                else:
                    rows.add(base)
    return {'id': question['id'], 'rows': [list(row) for row in sorted(rows)], 'note': note}


def diagnostics(state, questions, answers):
    pack_diff = []
    section_diff = []
    for doc, extension in state['extensions'].items():
        extension_packs = set(values(extension.get('belongsToCRPack')))
        canonical_packs = state['doc_packs'].get(doc, set())
        if extension_packs != canonical_packs:
            pack_diff.append((doc, sorted(extension_packs), sorted(canonical_packs)))
        extension_sections = set(values(extension.get('modifiesSection')))
        canonical_sections = state['doc_sections'].get(doc, set())
        if extension_sections != canonical_sections:
            section_diff.append((doc, sorted(extension_sections), sorted(canonical_sections)))
    print('COUNTS', json.dumps({k: len(state[k]) for k in ['docs', 'packs', 'sections', 'resolutions', 'dispositions']}))
    print('PACK_LINK_DIFFERENCES', len(pack_diff), json.dumps(pack_diff[:3]))
    print('SECTION_LINK_DIFFERENCES', len(section_diff), json.dumps(section_diff[:3]))
    for q, a in zip(questions, answers):
        print('ANSWER', a['id'], len(a['rows']), json.dumps(a['rows'], ensure_ascii=False))
        if q['question'].startswith('RAN2 recorded document'):
            root = 'tdoc:' + re.search(r'R2-\d+', q['question']).group()
            print('REVISION_DESCENDANTS', number(root), json.dumps([
                {'document': number(d), 'next': sorted(number(n) for n in state['revisions'].get(d, [])),
                 'list_status': state['docs'].get(d, {}).get('tdoc:status'),
                 'dispositions': valid_dispositions(state, d),
                 'packs': sorted(state['packs'][p]['tdoc:crPackId'] for p in state['doc_packs'].get(d, []))}
                for d in sorted(descendants(state, root))], ensure_ascii=False))
        if q['question'].startswith('Which Rel-'):
            release = re.search(r'Rel-\d+', q['question']).group()
            clause, spec = re.search(r'modify clause (.*?) of TS ([\d.]+)', q['question']).groups()
            key = 'tdoc:section/' + spec + '-' + release + '-' + clause
            print('CLAUSE_CANDIDATES', key, json.dumps([
                {'document': number(d), 'release': state['docs'].get(d, {}).get('targetRelease'),
                 'dispositions': valid_dispositions(state, d),
                 'packs': sorted(state['packs'][p]['tdoc:crPackId'] for p in state['doc_packs'].get(d, []))}
                for d in sorted(state['sections'].get(key, []))], ensure_ascii=False))
            subclauses = {s: ds for s, ds in state['sections'].items() if s.startswith(key + '.')}
            print('SUBCLAUSE_ALTERNATIVE', json.dumps({s: sorted(number(d) for d in ds) for s, ds in subclauses.items()}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--brief', action='store_true')
    args = parser.parse_args()
    with open('questions.jsonl') as stream:
        questions = [json.loads(line) for line in stream]
    state = load_records()
    answers = [solve(state, q) for q in questions]
    for q, a in zip(questions, answers):
        assert len(a['rows']) == len({tuple(row) for row in a['rows']})
        assert all(len(row) == len(q['fields']) and all(isinstance(v, str) for v in row) for row in a['rows'])
    assert len({a['id'] for a in answers}) == len(questions) == 28
    if args.write:
        with open('answers.jsonl', 'w') as stream:
            for a in answers:
                stream.write(json.dumps(a, ensure_ascii=False) + '\n')
    if args.brief:
        for a in answers:
            print(a['id'], len(a['rows']), a['note'])
    else:
        diagnostics(state, questions, answers)


if __name__ == '__main__':
    main()
