import collections
import json
import re


def records(path):
    with open(path) as handle:
        return json.load(handle)['@graph']


def many(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def unique(rows):
    return [list(row) for row in sorted(set(map(tuple, rows)))]


with open('questions.jsonl') as handle:
    questions = [json.loads(line) for line in handle if line.strip()]

meetings = {}
for d in records('records/phase-1/meetings.jsonld'):
    meetings[d['@id']] = d['tdoc:meetingNumber']
    canonical_id = 'tdoc:meeting/' + d['tdoc:canonicalMeetingNumber'].replace('#', '_')
    assert canonical_id not in meetings or meetings[canonical_id] == d['tdoc:meetingNumber']
    meetings[canonical_id] = d['tdoc:meetingNumber']
releases = {d['@id']: d['tdoc:releaseName']
            for d in records('records/phase-1/releases.jsonld')}
tdocs = {}
successors = collections.defaultdict(set)
for d in records('records/phase-1/tdocs.jsonld'):
    keep = ['@id', '@type', 'tdoc:tdocNumber', 'tdoc:type', 'tdoc:status',
            'targetRelease', 'presentedAt', 'modifies', 'tdoc:crNumber',
            'tdoc:tsgCRPack', 'revisedTo', 'isRevisionOf', 'tdoc:clausesAffected']
    tdocs[d['@id']] = {k: d[k] for k in keep if k in d}
    for nxt in many(d.get('revisedTo')):
        successors[d['@id']].add(nxt)
    for prev in many(d.get('isRevisionOf')):
        successors[prev].add(d['@id'])

packs = {}
memberships = collections.defaultdict(set)
for p in records('records/phase-4/crpacks.jsonld'):
    packs[p['@id']] = p
    for doc in many(p['hasCR']):
        memberships[doc].add(p['@id'])

sections = collections.defaultdict(set)
section_members = collections.defaultdict(set)
for s in records('records/phase-4/section_extensions.jsonld'):
    match = re.fullmatch(r'tdoc:section/(.+)-(Rel-\d+)-(.+)', s['@id'])
    assert match, s['@id']
    spec, release, clause = match.groups()
    for doc in many(s['modifiedByCR']):
        sections[doc].add((spec, release, clause))
        section_members[(spec, release, clause)].add(doc)

# Check both exported directions without using an external data store.
inverse_memberships = set()
inverse_sections = set()
for d in records('records/phase-4/cr_extensions.jsonld'):
    for pack in many(d['belongsToCRPack']):
        inverse_memberships.add((d['@id'], pack))
    for section in many(d.get('modifiesSection')):
        inverse_sections.add((d['@id'], section))
assert inverse_memberships == {(doc, pack) for doc, ps in memberships.items() for pack in ps}
assert inverse_sections == {(doc, 'tdoc:section/' + spec + '-' + rel + '-' + clause)
                            for doc, ss in sections.items() for spec, rel, clause in ss}
del inverse_memberships, inverse_sections

decisions = {}
for path in ['records/phase-2/resolutions_document_dispositions.jsonld',
             'records/phase-2/resolutions_conclusions.jsonld',
             'records/phase-2/discussions.jsonld']:
    for d in records(path):
        decisions[d['@id']] = {k: d[k] for k in ['@id', 'madeAt', 'content'] if k in d}

dispositions = collections.defaultdict(list)
excluded = collections.defaultdict(list)
for d in records('records/phase-2/decision_dispositions.jsonld'):
    method = json.loads(d['assessmentMethod'])
    if d['evidenceStatus'] == 'source_verified' and method.get('scope') == 'whole_target':
        decision = decisions[d['dispositionOf']]
        meeting_id = decision['madeAt']
        # All decision meetings must resolve to the exact recorded display name.
        meeting = meetings[meeting_id]
        dispositions[d['dispositionTarget']].append((d['dispositionCode'], meeting, d['dispositionOf']))
    else:
        excluded[d['dispositionTarget']].append((d['dispositionCode'], d['evidenceStatus'], method.get('scope')))


def descend(start):
    seen = {start}
    todo = list(successors[start])
    while todo:
        doc = todo.pop()
        if doc in seen:
            continue
        seen.add(doc)
        todo.extend(successors[doc] - seen)
    return seen - {start}


def packrows(doc):
    return [(packs[p]['tdoc:crPackId'], packs[p]['tdoc:tsgMeeting'])
            for p in sorted(memberships[doc])]


def docrows(doc):
    return [(code, meeting, pack, tsg)
            for code, meeting, _ in dispositions[doc]
            for pack, tsg in packrows(doc)]


answers = []
for q in questions:
    question = q['question']
    rows = []
    notes = []
    if question.startswith('In which TSG RAN CR pack'):
        doc = 'tdoc:' + re.search(r'R5-\d+', question).group()
        rows = packrows(doc)
    elif question.startswith('Change request '):
        doc = 'tdoc:' + re.search(r'R5-\d+', question).group()
        rows = docrows(doc)
    elif question.startswith('Trace change request '):
        doc = 'tdoc:' + re.search(r'R5-\d+', question).group()
        spec = re.search(r'to TS (\S+)\)', question).group(1)
        clauses = {clause for s, release, clause in sections[doc] if s == spec}
        rows = [list(row) + [clause] for row in docrows(doc) for clause in clauses]
        release = releases[tdocs[doc]['targetRelease']]
        release_clauses = {clause for s, r, clause in sections[doc] if s == spec and r == release}
        if release_clauses != clauses:
            alt_count = len(unique([list(row) + [clause] for row in docrows(doc) for clause in release_clauses]))
            notes.append('Used all explicit clause links for the named specification, without filtering their release tags. An alternative restricts sections to the CR target release (' + release + ') and yields ' + str(alt_count) + ' rows.')
    elif question.startswith('TSG RAN CR pack '):
        pack = 'tdoc:crpack/' + re.search(r'RP-\d+', question).group()
        for doc in many(packs[pack]['hasCR']):
            for code, meeting, _ in dispositions[doc]:
                rows.append([tdocs[doc]['tdoc:tdocNumber'], code, meeting])
    elif question.startswith('Which Rel-'):
        release, clause, spec = re.search(r'Which (Rel-\d+) change requests that modify clause (\S+) of TS (\S+)', question).groups()
        candidates = {doc for (s, r, c), docs in section_members.items()
                      if s == spec and c == clause for doc in docs
                      if releases.get(tdocs[doc].get('targetRelease')) == release}
        def clause_rows(docs):
            return unique([[tdocs[doc]['tdoc:tdocNumber'], code, meeting, pack]
                           for doc in docs for code, meeting, pack, tsg in docrows(doc)])
        for doc in candidates:
            assert tdocs[doc]['tdoc:type'] == 'CR'
            assert tdocs[doc]['modifies'] == 'tdoc:spec/' + spec.replace('.', '_')
            for code, meeting, pack, tsg in docrows(doc):
                rows.append([tdocs[doc]['tdoc:tdocNumber'], code, meeting, pack])
        # These are interpretations of the sentence, not assumptions about a key.
        section_release_rows = clause_rows(section_members[(spec, release, clause)])
        descendant_candidates = {doc for (s, r, c), docs in section_members.items()
                                 if s == spec and (c == clause or c.startswith(clause + '.'))
                                 for doc in docs if releases.get(tdocs[doc].get('targetRelease')) == release}
        descendant_rows = clause_rows(descendant_candidates)
        notes.append('Interpreted the named clause as an exact recorded clause and ' + release + ' as the CR target release. Alternatives include subclauses or use the linked section record\'s release tag.')
        if descendant_rows != unique(rows):
            notes.append('Including subclauses yields ' + str(len(descendant_rows)) + ' rows.')
        if section_release_rows != unique(rows):
            notes.append('Using section release tags yields ' + str(len(section_release_rows)) + ' rows.')
    elif question.startswith('RAN5 recorded document '):
        doc = 'tdoc:' + re.search(r'R5-\d+', question).group()
        assert any(code == 'revised' for code, _, _ in dispositions[doc])
        for later in descend(doc):
            for code, meeting, pack, tsg in docrows(later):
                rows.append([tdocs[later]['tdoc:tdocNumber'], code, pack])
    else:
        raise ValueError(question)
    rows = unique(rows)
    assert all(len(row) == len(q['fields']) and all(isinstance(v, str) for v in row) for row in rows)
    if question.startswith(('In which TSG RAN CR pack', 'Trace change request ', 'Change request ')):
        cr, spec = re.search(r'CR (\d+) to TS ([\d.-]+)\)', question).groups()
        assert tdocs[doc]['tdoc:crNumber'] == cr, (q['id'], tdocs[doc]['tdoc:crNumber'], cr)
        assert tdocs[doc]['modifies'] == 'tdoc:spec/' + spec.replace('.', '_')
    if not rows:
        if question.startswith('In which TSG RAN CR pack'):
            notes.append('No CR pack membership is recorded for the exact named R5 document.')
        else:
            notes.append('No complete row satisfying all requested record conditions was found.')
    answers.append({'id': q['id'], 'rows': rows, 'note': ' '.join(notes)})

assert len(answers) == 80 and [a['id'] for a in answers] == [q['id'] for q in questions]
assert len(set(a['id'] for a in answers)) == len(answers)
assert all(len(a['rows']) == len(set(map(tuple, a['rows']))) for a in answers)
with open('answers.jsonl', 'w') as handle:
    for answer in answers:
        handle.write(json.dumps(answer, ensure_ascii=False) + '\n')

print('Wrote', len(answers), 'answers;', sum(len(a['rows']) for a in answers), 'rows.')
for q, answer in zip(questions, answers):
    print(answer['id'], len(answer['rows']), answer['note'])

# Compact diagnostic evidence: potential naming, release, and revision issues.
print('DIAGNOSTICS')
for q in questions:
    question = q['question']
    if question.startswith('RAN5 recorded document '):
        doc = 'tdoc:' + re.search(r'R5-\d+', question).group()
        later = sorted(descend(doc))
        print('REVISIONS', doc, [(d, sorted(successors[d]), unique([x[:2] for x in dispositions[d]]), packrows(d)) for d in later])
    elif question.startswith('Which Rel-'):
        release, clause, spec = re.search(r'Which (Rel-\d+) change requests that modify clause (\S+) of TS (\S+)', question).groups()
        matches = [(s, r, c, sorted(docs)) for (s, r, c), docs in section_members.items() if s == spec and c == clause]
        print('CLAUSE', q['id'], [(r, len(docs), [d for d in docs if releases.get(tdocs[d].get('targetRelease')) != r]) for s,r,c,docs in matches])
    elif question.startswith(('Trace change request ', 'Change request ')):
        doc = 'tdoc:' + re.search(r'R5-\d+', question).group()
        if excluded[doc] or len(dispositions[doc]) != 1:
            print('DISPOSITION', doc, dispositions[doc], excluded[doc])
    if question.startswith('In which TSG RAN CR pack'):
        doc = 'tdoc:' + re.search(r'R5-\d+', question).group()
        if not packrows(doc):
            print('NO_PACK', doc, 'list_status', tdocs[doc]['tdoc:status'], 'list_pack', tdocs[doc].get('tdoc:tsgCRPack'), 'revisions', sorted(descend(doc)))
