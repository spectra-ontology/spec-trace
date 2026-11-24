import collections
import gc
import json
import re


def load(path):
    with open(path) as f:
        data = json.load(f)
    graph = data.pop('@graph')
    del data
    return graph


def vals(x):
    return x if isinstance(x, list) else [x] if x is not None else []


def lit(x):
    return x.get('@value', '') if isinstance(x, dict) else x


def solve(write=False, verbose=False):
    def report(*args, **kwargs):
        if verbose:
            print(*args, **kwargs)
    with open('questions.jsonl') as f:
        questions = [json.loads(line) for line in f]
    meetings = {r['@id']: r['tdoc:meetingNumber'] for r in load('records/phase-1/meetings.jsonld')}
    packs = {r['tdoc:crPackId']: r for r in load('records/phase-4/crpacks.jsonld')}
    member_packs = collections.defaultdict(set)
    for number, pack in packs.items():
        for doc in vals(pack.get('hasCR')):
            member_packs[doc].add(number)

    sections = load('records/phase-4/section_extensions.jsonld')
    report('SECTION SAMPLE', json.dumps(sections[0], ensure_ascii=False))
    section_by_id = {s['@id']: s for s in sections}
    clause_members = collections.defaultdict(set)
    clauses_by_cr = collections.defaultdict(set)
    for s in sections:
        for cr in vals(s.get('modifiedByCR')):
            clause_members[s['@id']].add(cr)
            clauses_by_cr[cr].add(s['@id'])
    report('SECTION keys', collections.Counter(k for s in sections for k in s).most_common())
    del sections

    cr_extensions = load('records/phase-4/cr_extensions.jsonld')
    report('CR EXT SAMPLE', json.dumps(cr_extensions[0], ensure_ascii=False))
    report('CR EXT keys', collections.Counter(k for s in cr_extensions for k in s).most_common())
    for cr in cr_extensions:
        for s in vals(cr.get('modifiesSection')):
            clause_members[s].add(cr['@id'])
            clauses_by_cr[cr['@id']].add(s)
        for p in vals(cr.get('belongsToCRPack')):
            matches = [n for n,r in packs.items() if r['@id'] == p]
            member_packs[cr['@id']].update(matches)
    del cr_extensions
    gc.collect()

    raw_docs = load('records/phase-1/tdocs.jsonld')
    keep = ['@id', '@type', 'tdoc:tdocNumber', 'targetRelease', 'modifies', 'isRevisionOf', 'revisedTo', 'tdoc:tsgCRPack', 'tdoc:status', 'tdoc:clausesAffected', 'presentedAt']
    docs = {r['@id']: {k:r[k] for k in keep if k in r} for r in raw_docs}
    del raw_docs
    gc.collect()
    revisions = collections.defaultdict(set)
    for r in docs.values():
        for old in vals(r.get('isRevisionOf')):
            revisions[old].add(r['@id'])
        for new in vals(r.get('revisedTo')):
            revisions[r['@id']].add(new)
        for pack in vals(r.get('tdoc:tsgCRPack')):
            if pack in packs:
                member_packs[r['@id']].add(pack)
    candidates = set()
    plans = {}
    for q in questions:
        sentence = q['question']
        doc_match = re.search(r'R4-\d+', sentence)
        pack_match = re.search(r'RP-\d+', sentence)
        if 'Follow its revisions' in sentence:
            root = 'tdoc:' + doc_match[0]
            desc = set()
            todo = list(revisions[root])
            while todo:
                nxt = todo.pop()
                if nxt != root and nxt not in desc:
                    desc.add(nxt)
                    todo.extend(revisions[nxt])
            plans[q['id']] = ('revision', desc, root)
            candidates |= desc | {root}
        elif sentence.startswith('Which Rel-'):
            rel, clause, spec = re.search(r'Which Rel-(\d+).*?clause (\S+) of TS (\S+) ', sentence).groups()
            sid = f'tdoc:section/{spec}-Rel-{rel}-{clause}'
            exact = set(clause_members[sid])
            inclusive = set(exact)
            section_ids = {sid}
            for other_sid in section_by_id:
                if other_sid.startswith(sid + '.'):
                    inclusive |= clause_members[other_sid]
                    section_ids.add(other_sid)
            # Include explicit raw clause metadata as well as section relations.
            for doc, record in docs.items():
                if record.get('targetRelease') != f'tdoc:release/Rel_{rel}' or record.get('modifies') != 'tdoc:spec/' + spec.replace('.', '_'):
                    continue
                raw = record.get('tdoc:clausesAffected', '')
                boundary = r'(?<![A-Za-z0-9.])' + re.escape(clause)
                if re.search(boundary + r'(?![A-Za-z0-9.])', raw):
                    exact.add(doc)
                if re.search(boundary + r'(?:\.[A-Za-z0-9]+)*(?![A-Za-z0-9.])', raw):
                    inclusive.add(doc)
            # Require the explicit target release for the CR itself.
            exact = {d for d in exact if docs.get(d, {}).get('targetRelease') == f'tdoc:release/Rel_{rel}'}
            inclusive = {d for d in inclusive if docs.get(d, {}).get('targetRelease') == f'tdoc:release/Rel_{rel}'}
            plans[q['id']] = ('clause', inclusive, exact, sid)
            candidates |= inclusive
            report('CLAUSE CANDIDATES', q['id'], 'exact', sorted(exact), 'inclusive', sorted(inclusive))
        elif pack_match:
            p = pack_match[0]
            members = {doc for doc, ps in member_packs.items() if p in ps}
            assert members == set(vals(packs.get(p, {}).get('hasCR'))), (p, members ^ set(vals(packs.get(p, {}).get('hasCR'))))
            plans[q['id']] = ('pack_members', members, p)
            candidates |= members
        else:
            doc = 'tdoc:' + doc_match[0]
            if sentence.startswith('In which'):
                kind = 'pack_only'
            elif sentence.startswith('Trace'):
                kind = 'trace'
            else:
                kind = 'decision_pack'
            plans[q['id']] = (kind, {doc}, doc)
            candidates.add(doc)
    # Keep only queried documents and transitive revisions.
    docs = {d:r for d,r in docs.items() if d in candidates}
    assert candidates <= docs.keys(), candidates - docs.keys()
    member_packs = {d: sorted(member_packs[d]) for d in candidates}
    del revisions
    gc.collect()

    # Load this large file by itself; retain only relevant disposition records.
    raw_dispositions = load('records/phase-2/decision_dispositions.jsonld')
    report('DISPOSITION TOTAL', len(raw_dispositions))
    report('DISPOSITION statuses', collections.Counter(r.get('evidenceStatus') for r in raw_dispositions))
    selected = [r for r in raw_dispositions if r.get('dispositionTarget') in candidates]
    del raw_dispositions
    gc.collect()
    disps = collections.defaultdict(list)
    for r in selected:
        method = json.loads(r.get('assessmentMethod', '{}'))
        if r.get('evidenceStatus') == 'source_verified' and method.get('scope') == 'whole_target':
            disps[r['dispositionTarget']].append(r)
    event_ids = {r['dispositionOf'] for rows in disps.values() for r in rows}
    event_by_id = {}
    for path in ['records/phase-2/resolutions_document_dispositions.jsonld', 'records/phase-2/resolutions_agreements.jsonld', 'records/phase-2/resolutions_conclusions.jsonld', 'records/phase-2/resolutions_working_assumptions.jsonld']:
        graph = load(path)
        for r in graph:
            if r['@id'] in event_ids:
                event_by_id[r['@id']] = r
        del graph
        gc.collect()
    assert not (event_ids - event_by_id.keys()), event_ids - event_by_id.keys()
    qualified = collections.defaultdict(set)
    for doc, entries in disps.items():
        for r in entries:
            event = event_by_id[r['dispositionOf']]
            mid = event.get('madeAt')
            assert mid in meetings, (doc, mid)
            meeting = meetings[mid]
            if not meeting.startswith('RAN4#'):
                continue
            qualified[doc].add((r['dispositionCode'], meeting))

    answers = []
    for q in questions:
        plan = plans[q['id']]
        kind, ds = plan[:2]
        rows = set()
        note = ''
        for doc in ds:
            number = docs.get(doc, {}).get('tdoc:tdocNumber', doc.removeprefix('tdoc:'))
            ps = member_packs.get(doc, [])
            qs = qualified.get(doc, [])
            if kind == 'pack_only':
                for p in ps:
                    rows.add((p, packs[p]['tdoc:tsgMeeting']))
            elif kind == 'pack_members':
                for code, meeting in qs:
                    rows.add((number, code, meeting))
            elif kind == 'revision':
                for code, meeting in qs:
                    for p in ps:
                        rows.add((number, code, p))
            elif kind == 'clause':
                for code, meeting in qs:
                    for p in ps:
                        rows.add((number, code, meeting, p))
            elif kind == 'decision_pack':
                for code, meeting in qs:
                    for p in ps:
                        rows.add((code, meeting, p, packs[p]['tdoc:tsgMeeting']))
            elif kind == 'trace':
                for code, meeting in qs:
                    for p in ps:
                        for sid in clauses_by_cr.get(doc, []):
                            s = section_by_id.get(sid)
                            if s:
                                match = re.fullmatch(r'tdoc:section/(.+)-Rel-(\d+)-(.+)', sid)
                                assert match, sid
                                spec, release, clause = match.groups()
                                wanted_spec = re.search(r'each clause of TS (\S+) ', q['question'])[1]
                                if spec != wanted_spec:
                                    continue
                                rows.add((code, meeting, p, packs[p]['tdoc:tsgMeeting'], clause))
        if kind == 'clause' and plan[1] != plan[2]:
            exact_rows = {(docs[d]['tdoc:tdocNumber'], code, meeting, p) for d in plan[2] for code, meeting in qualified.get(d, []) for p in member_packs.get(d, [])}
            alternative = '; '.join(', '.join(row) for row in sorted(exact_rows))
            note = f'Interpreted clause 12 to include its subclauses. The alternative exact-clause-only reading yields {len(exact_rows)} row: {alternative}.'
        if not rows:
            if kind == 'pack_only':
                note = 'No CR-pack membership for the specifically named document was found in the records; other revisions of the same CR were not substituted.'
            else:
                note = 'No row meeting all stated conditions was found in the records.'
        a = {'id':q['id'], 'rows':[list(r) for r in sorted(rows)], 'note':note}
        answers.append(a)
        report('ANSWER', json.dumps(a, ensure_ascii=False))
        if kind != 'clause' or len(ds) < 50:
            for doc in sorted(ds):
                report('JOIN', doc, 'PACKS', member_packs.get(doc,[]), 'QUALIFIED', sorted(qualified.get(doc,[])), 'CLAUSES', sorted(clauses_by_cr.get(doc,[])) if kind == 'trace' else '', 'LIST_STATUS', docs.get(doc,{}).get('tdoc:status'))
        if kind == 'clause' and plan[1] != plan[2]:
            report('EXACT QUALIFIED', [(doc,sorted(qualified.get(doc,[])),member_packs.get(doc,[])) for doc in sorted(plan[2])])
    assert len(answers) == len(questions) == 28
    assert [a['id'] for a in answers] == [q['id'] for q in questions]
    for answer, question in zip(answers, questions):
        assert isinstance(answer['note'], str)
        assert len(answer['rows']) == len({tuple(r) for r in answer['rows']})
        for row in answer['rows']:
            assert len(row) == len(question['fields']), (answer['id'], row)
            assert all(isinstance(value, str) for value in row)
    if write:
        with open('answers.jsonl', 'w') as f:
            for a in answers:
                f.write(json.dumps(a, ensure_ascii=False) + '\n')
    return answers, selected, event_by_id, plans, docs


if __name__ == '__main__':
    solve(write=False)
