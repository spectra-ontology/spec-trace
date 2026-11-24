import collections
import json
import re


def graph(path):
    with open(path) as handle:
        return json.load(handle)['@graph']


def many(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


with open('questions.jsonl') as handle:
    questions = [json.loads(line) for line in handle if line.strip()]

packs = {d['@id']: d for d in graph('records/phase-4/crpacks.jsonld')}
doc_packs = collections.defaultdict(set)
for pid, pack in packs.items():
    for doc in many(pack['hasCR']):
        doc_packs[doc].add(pid)

sections = {d['@id']: d for d in graph('records/phase-4/section_extensions.jsonld')}
extensions = {d['@id']: d for d in graph('records/phase-4/cr_extensions.jsonld')}
doc_sections = collections.defaultdict(set)
section_docs = collections.defaultdict(set)
for sid, section in sections.items():
    for doc in many(section['modifiedByCR']):
        doc_sections[doc].add(sid)
        section_docs[sid].add(doc)

needed = set()
for question in questions:
    needed.update('tdoc:' + number for number in re.findall(r'R1-\d+', question['question']))
    for number in re.findall(r'RP-\d+', question['question']):
        needed.update(many(packs['tdoc:crpack/' + number]['hasCR']))
    match = re.search(r'Which (Rel-\d+) change requests that modify clause (\S+) of TS ([\d.]+)', question['question'])
    if match:
        release, clause, spec = match.groups()
        prefix = 'tdoc:section/' + spec + '-' + release + '-'
        needed.update(section_docs.get(prefix + clause, set()))
        for sid, docs in section_docs.items():
            if sid.startswith(prefix + clause + '.'):
                needed.update(docs)

tdocs = {}
for doc in graph('records/phase-1/tdocs.jsonld'):
    if doc['@id'] in needed:
        tdocs[doc['@id']] = doc
del doc

meetings = {d['@id']: d for d in graph('records/phase-1/meetings.jsonld')}
events = {}
for filename in ['resolutions_document_dispositions', 'resolutions_agreements', 'resolutions_conclusions', 'resolutions_working_assumptions']:
    for event in graph('records/phase-2/' + filename + '.jsonld'):
        events[event['@id']] = {'madeAt': event['madeAt'], 'content': event['content']}
del event

dispositions = collections.defaultdict(list)
excluded = collections.defaultdict(list)
for disposition in graph('records/phase-2/decision_dispositions.jsonld'):
    doc_id = disposition['dispositionTarget']
    if doc_id not in needed:
        continue
    method = json.loads(disposition['assessmentMethod'])
    reduced = {
        'event': disposition['dispositionOf'],
        'code': disposition['dispositionCode'],
        'status': disposition['evidenceStatus'],
        'scope': method.get('scope'),
        'rule': method.get('rule'),
        'quote': disposition['evidenceQuote'],
    }
    if reduced['status'] == 'source_verified' and reduced['scope'] == 'whole_target':
        dispositions[doc_id].append(reduced)
    else:
        excluded[doc_id].append(reduced)
del disposition, method


def decision_rows(doc_id):
    rows = set()
    for disposition in dispositions.get(doc_id, []):
        meeting_id = events[disposition['event']]['madeAt']
        meeting = meetings[meeting_id]
        if meeting['tdoc:workingGroup'] == 'RAN1':
            rows.add((disposition['code'], meeting['tdoc:meetingNumber']))
    return rows


def pack_rows(doc_id):
    return {(packs[pid]['tdoc:crPackId'], packs[pid]['tdoc:tsgMeeting']) for pid in doc_packs.get(doc_id, set())}


def clauses_for(doc_id, spec):
    output = set()
    for sid in doc_sections.get(doc_id, set()):
        match = re.fullmatch(r'tdoc:section/([\d.]+)-(Rel-\d+)-(.+)', sid)
        if match and match[1] == spec:
            output.add(match[3])
    return output


def conflict_note(doc_ids):
    details = []
    for doc_id in sorted(doc_ids):
        ds = decision_rows(doc_id)
        if len(ds) > 1:
            details.append(doc_id.removeprefix('tdoc:') + ': ' + ', '.join(code + ' at ' + meeting for code, meeting in sorted(ds)))
    if not details:
        return ''
    return ('I read the request as asking for every qualifying recorded disposition. '
            + '; '.join(details)
            + '. The singular wording could instead mean only the final agreed/annex outcome; the question does not specify that restriction.')


answers = []
for question in questions:
    sentence = question['question']
    fields = question['fields']
    rows = set()
    note = ''
    candidate_docs = set()
    if sentence.startswith('In which TSG RAN CR pack'):
        doc_id = 'tdoc:' + re.search(r'R1-\d+', sentence)[0]
        candidate_docs.add(doc_id)
        rows.update(pack_rows(doc_id))
    elif sentence.startswith('Change request') or sentence.startswith('Trace change request'):
        doc_id = 'tdoc:' + re.search(r'R1-\d+', sentence)[0]
        candidate_docs.add(doc_id)
        clause_values = [None]
        if 'clause' in fields:
            spec = re.search(r'to TS ([\d.]+)', sentence)[1]
            clause_values = sorted(clauses_for(doc_id, spec))
        for code, wg_meeting in decision_rows(doc_id):
            for pack, tsg_meeting in pack_rows(doc_id):
                for clause in clause_values:
                    row = (code, wg_meeting, pack, tsg_meeting)
                    rows.add(row + (clause,) if clause is not None else row)
        note = conflict_note(candidate_docs)
    elif sentence.startswith('TSG RAN CR pack'):
        pack_id = 'tdoc:crpack/' + re.search(r'RP-\d+', sentence)[0]
        candidate_docs.update(many(packs[pack_id]['hasCR']))
        for doc_id in candidate_docs:
            for code, wg_meeting in decision_rows(doc_id):
                rows.add((doc_id.removeprefix('tdoc:'), code, wg_meeting))
        note = conflict_note(candidate_docs)
    elif sentence.startswith('Which Rel-'):
        match = re.search(r'Which (Rel-\d+) change requests that modify clause (\S+) of TS ([\d.]+)', sentence)
        release, clause, spec = match.groups()
        sid = 'tdoc:section/' + spec + '-' + release + '-' + clause
        candidate_docs.update(section_docs.get(sid, set()))
        for doc_id in candidate_docs:
            doc = tdocs.get(doc_id)
            if not doc or 'tdoc:CR' not in many(doc['@type']):
                continue
            if 'tdoc:release/' + release.replace('-', '_') not in many(doc.get('targetRelease')):
                continue
            if 'tdoc:spec/' + spec.replace('.', '_') not in many(doc.get('modifies')):
                continue
            for code, wg_meeting in decision_rows(doc_id):
                for pack, tsg_meeting in pack_rows(doc_id):
                    rows.add((doc_id.removeprefix('tdoc:'), code, wg_meeting, pack))
        note = conflict_note(candidate_docs)
    else:
        raise ValueError(sentence)
    if not rows and not note:
        note = 'No row met all stated conditions in the supplied records.'
    answers.append({'id': question['id'], 'rows': [list(row) for row in sorted(rows)], 'note': note})
    print(question['id'], 'rows=' + str(len(rows)), 'candidates=' + str(len(candidate_docs)), ('NOTE: ' + note) if note else '')

assert len(answers) == len(questions) == 60
assert [a['id'] for a in answers] == [q['id'] for q in questions]
assert len({a['id'] for a in answers}) == len(answers)
for question, answer in zip(questions, answers):
    assert isinstance(answer['note'], str)
    assert len({tuple(row) for row in answer['rows']}) == len(answer['rows'])
    assert all(len(row) == len(question['fields']) and all(isinstance(value, str) for value in row)
               for row in answer['rows'])

with open('answers.jsonl', 'w') as handle:
    for answer in answers:
        handle.write(json.dumps(answer, ensure_ascii=False) + '\n')

print('TOTAL', len(answers), sum(len(a['rows']) for a in answers), 'format checks passed')
