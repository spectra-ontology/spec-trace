import json
import re
from collections import defaultdict


def graph(path):
    with open(path) as handle:
        return json.load(handle)['@graph']


def values(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


with open('questions.jsonl') as handle:
    questions = [json.loads(line) for line in handle]

# Retain compact indexes, discarding each complete graph before the next load.
tdocs = {}
revisions = defaultdict(set)
for item in graph('records/phase-1/tdocs.jsonld'):
    tdocs[item['@id']] = {key: item[key] for key in (
        'tdoc:tdocNumber', 'tdoc:type', 'targetRelease', 'modifies',
        'tdoc:crNumber', 'tdoc:crRevision', 'tdoc:clausesAffected',
        'tdoc:tsgCRPack', 'tdoc:status', 'presentedAt'
    ) if key in item}
    for later in values(item.get('revisedTo')):
        revisions[item['@id']].add(later)
    for earlier in values(item.get('isRevisionOf')):
        revisions[earlier].add(item['@id'])
del item

meetings = {item['@id']: item['tdoc:meetingNumber']
            for item in graph('records/phase-1/meetings.jsonld')}
releases = {item['@id']: item['tdoc:releaseName']
            for item in graph('records/phase-1/releases.jsonld')}

event_meetings = {}
for filename in ('resolutions_document_dispositions.jsonld',
                 'resolutions_agreements.jsonld',
                 'resolutions_conclusions.jsonld',
                 'resolutions_working_assumptions.jsonld'):
    for item in graph('records/phase-2/' + filename):
        event_meetings[item['@id']] = item['madeAt']
del item

dispositions = defaultdict(set)
excluded = defaultdict(list)
for item in graph('records/phase-2/decision_dispositions.jsonld'):
    method = json.loads(item['assessmentMethod'])
    target = item['dispositionTarget']
    if item['evidenceStatus'] == 'source_verified' and method.get('scope') == 'whole_target':
        meeting_id = event_meetings[item['dispositionOf']]
        dispositions[target].add((item['dispositionCode'], meetings[meeting_id]))
    else:
        excluded[target].append((item['dispositionCode'], item['evidenceStatus'], method.get('scope')))
del item, method

packs = {}
document_packs = defaultdict(set)
for item in graph('records/phase-4/crpacks.jsonld'):
    packs[item['@id']] = (item['tdoc:crPackId'], item['tdoc:tsgMeeting'])
    for document in values(item.get('hasCR')):
        document_packs[document].add(item['@id'])
del item

sections = defaultdict(set)
section_pattern = re.compile(r'tdoc:section/(.+)-(Rel-\d+)-(.+)')
for item in graph('records/phase-4/section_extensions.jsonld'):
    match = section_pattern.fullmatch(item['@id'])
    assert match, item['@id']
    for document in values(item['modifiedByCR']):
        sections[document].add(match.groups())
del item

for item in graph('records/phase-4/cr_extensions.jsonld'):
    for pack in values(item.get('belongsToCRPack')):
        assert pack in packs, pack
        document_packs[item['@id']].add(pack)
    for section in values(item.get('modifiesSection')):
        match = section_pattern.fullmatch(section)
        assert match, section
        sections[item['@id']].add(match.groups())
del item

# Check any additional pack and clause evidence on the phase-1 document lists.
raw_pack_differences = []
for document, item in tdocs.items():
    for pack_number in values(item.get('tdoc:tsgCRPack')):
        pack = 'tdoc:crpack/' + pack_number
        if pack not in document_packs[document]:
            raw_pack_differences.append((document, pack_number, pack in packs))


def descendants(document):
    found = set()
    pending = list(revisions[document])
    while pending:
        later = pending.pop()
        if later not in found and later != document:
            found.add(later)
            pending.extend(revisions[later])
    return found


def full_rows(document):
    for disposition, meeting in sorted(dispositions[document]):
        for pack in sorted(document_packs[document]):
            pack_number, tsg_meeting = packs[pack]
            yield disposition, meeting, pack_number, tsg_meeting


def clause_candidates(spec, clause, release, include_subclauses=False):
    for document, linked_sections in sections.items():
        item = tdocs.get(document, {})
        if releases.get(item.get('targetRelease')) != release:
            continue
        if item.get('tdoc:type') != 'CR':
            continue
        if 'tdoc:spec/' + spec.replace('.', '_') not in values(item.get('modifies')):
            continue
        if any(section_spec == spec and (section_clause == clause or (
            include_subclauses and section_clause.startswith(clause + '.')
        )) for section_spec, section_release, section_clause in linked_sections):
            yield document


answers = []
for question in questions:
    sentence = question['question']
    fields = question['fields']
    rows = []
    note = ''
    document_match = re.search(r'R3-\d+', sentence)
    document = 'tdoc:' + document_match.group() if document_match else None
    if sentence.startswith('Trace change request'):
        spec = re.search(r'TS ([\d.]+)', sentence).group(1)
        clauses = {clause for section_spec, release, clause in sections[document]
                   if section_spec == spec}
        rows = [list(base) + [clause] for base in full_rows(document)
                for clause in clauses]
    elif sentence.startswith('TSG RAN CR pack'):
        pack = 'tdoc:crpack/' + re.search(r'RP-\d+', sentence).group()
        for member, memberships in document_packs.items():
            if pack in memberships and tdocs.get(member, {}).get('tdoc:type') == 'CR':
                for disposition, meeting in dispositions[member]:
                    rows.append([tdocs[member]['tdoc:tdocNumber'], disposition, meeting])
    elif sentence.startswith('In which TSG RAN CR pack'):
        rows = [list(packs[pack]) for pack in document_packs[document]]
        if not rows:
            note = ('No CR pack membership is recorded for the exact named document; '
                    'I did not substitute another document with the same CR number or a later revision.')
    elif sentence.startswith('Change request'):
        rows = [list(row) for row in full_rows(document)]
    elif sentence.startswith('RAN3 recorded document'):
        for later in descendants(document):
            for disposition, meeting, pack, tsg_meeting in full_rows(later):
                rows.append([tdocs[later]['tdoc:tdocNumber'], disposition, pack])
    elif sentence.startswith('Which Rel-'):
        release = re.search(r'Rel-\d+', sentence).group()
        clause, spec = re.search(r'clause ([\d.]+) of TS ([\d.]+)', sentence).groups()
        for candidate in clause_candidates(spec, clause, release):
            for disposition, meeting, pack, tsg_meeting in full_rows(candidate):
                rows.append([tdocs[candidate]['tdoc:tdocNumber'], disposition, meeting, pack])
        direct_documents = {row[0] for row in rows}
        broad_documents = {tdocs[candidate]['tdoc:tdocNumber']
                           for candidate in clause_candidates(spec, clause, release, True)
                           if dispositions[candidate] and document_packs[candidate]}
        if broad_documents - direct_documents:
            note = ('Matched the exact recorded clause number and the CR target release. '
                    'Alternatively, modifying this clause could include changes recorded only against its subclauses.')
    else:
        raise AssertionError(sentence)
    rows = sorted(set(tuple(row) for row in rows))
    assert all(len(row) == len(fields) and all(isinstance(v, str) for v in row) for row in rows)
    answers.append({'id': question['id'], 'rows': [list(row) for row in rows], 'note': note})


if __name__ == '__main__':
    with open('answers.jsonl', 'w') as handle:
        for answer in answers:
            handle.write(json.dumps(answer, ensure_ascii=False) + '\n')
    print('Questions:', len(answers), 'Rows:', sum(len(answer['rows']) for answer in answers))
    print('Phase-1 pack links outside phase-4:', len(raw_pack_differences))
    for question, answer in zip(questions, answers):
        print(answer['id'], len(answer['rows']), answer['note'])
