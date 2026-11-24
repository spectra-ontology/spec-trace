import json
import re
import sys
from collections import defaultdict


def graph(path):
    with open(path) as stream:
        return json.load(stream)['@graph']


def many(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def docnum(identifier):
    return identifier.removeprefix('tdoc:')


with open('questions.jsonl') as stream:
    questions = [json.loads(line) for line in stream]

sentences = ' '.join(q['question'] for q in questions)
named_docs = {'tdoc:' + n for n in re.findall(r'R1-\d+', sentences)}
named_packs = set(re.findall(r'RP-\d+', sentences))
section_queries = {}
for q in questions:
    match = re.search(
        r'Which (Rel-\d+) change requests that modify clause ([\d.]+) of TS ([\d.]+)',
        q['question'],
    )
    if match:
        release, clause, spec = match.groups()
        section_queries[q['id']] = (release, clause, spec)

packs = {r['@id']: r for r in graph('records/phase-4/crpacks.jsonld')}
pack_members = {key: set(many(r['hasCR'])) for key, r in packs.items()}
doc_packs = defaultdict(set)
for pack_id, members in pack_members.items():
    for document in members:
        doc_packs[document].add(pack_id)

section_docs = defaultdict(set)
doc_sections = defaultdict(set)
for record in graph('records/phase-4/section_extensions.jsonld'):
    for document in many(record.get('modifiedByCR')):
        section_docs[record['@id']].add(document)
        doc_sections[document].add(record['@id'])

extension_docs = {}
section_edge_differences = []
for record in graph('records/phase-4/cr_extensions.jsonld'):
    identifier = record['@id']
    extension_docs[identifier] = record
    stated_sections = set(many(record.get('modifiesSection')))
    if stated_sections != doc_sections[identifier]:
        section_edge_differences.append(identifier)
    for section in stated_sections:
        section_docs[section].add(identifier)
        doc_sections[identifier].add(section)
    for pack_id in many(record.get('belongsToCRPack')):
        doc_packs[identifier].add(pack_id)
        pack_members.setdefault(pack_id, set()).add(identifier)

candidates = set(named_docs)
for release, clause, spec in section_queries.values():
    candidates.update(section_docs[f'tdoc:section/{spec}-{release}-{clause}'])
for pack_id, record in packs.items():
    if record['tdoc:crPackId'] in named_packs:
        candidates.update(pack_members[pack_id])

docs = {}
all_tdocs = graph('records/phase-1/tdocs.jsonld')
for record in all_tdocs:
    identifier = record['@id']
    if identifier in candidates or record.get('tdoc:tsgCRPack') in named_packs:
        docs[identifier] = record
        candidates.add(identifier)
        if record.get('tdoc:tsgCRPack'):
            pack_id = 'tdoc:crpack/' + record['tdoc:tsgCRPack']
            doc_packs[identifier].add(pack_id)
            pack_members.setdefault(pack_id, set()).add(identifier)
del all_tdocs

dispositions = defaultdict(list)
for record in graph('records/phase-2/decision_dispositions.jsonld'):
    if record['dispositionTarget'] not in candidates:
        continue
    assessment = json.loads(record['assessmentMethod'])
    dispositions[record['dispositionTarget']].append({
        'event': record['dispositionOf'],
        'code': record['dispositionCode'],
        'status': record['evidenceStatus'],
        'scope': assessment.get('scope'),
        'rule': assessment.get('rule'),
        'quote': record['evidenceQuote'],
        'target': record['targetTdocNumber'],
    })

event_ids = {d['event'] for values in dispositions.values() for d in values}
events = {}
for filename in [
    'resolutions_document_dispositions.jsonld',
    'resolutions_agreements.jsonld',
    'resolutions_conclusions.jsonld',
    'resolutions_working_assumptions.jsonld',
]:
    for record in graph('records/phase-2/' + filename):
        if record['@id'] in event_ids:
            if record['@id'] in events:
                assert events[record['@id']] == record
            events[record['@id']] = record

meetings = {r['@id']: r for r in graph('records/phase-1/meetings.jsonld')}
releases = {r['@id']: r['tdoc:releaseName'] for r in graph('records/phase-1/releases.jsonld')}


def decision_rows(document):
    result = set()
    for d in dispositions.get(document, []):
        if d['status'] != 'source_verified' or d['scope'] != 'whole_target':
            continue
        event = events[d['event']]
        for meeting_id in many(event['madeAt']):
            meeting = meetings[meeting_id]
            assert meeting['tdoc:workingGroup'] == 'RAN1'
            result.add((d['code'], meeting['tdoc:meetingNumber']))
    return sorted(result)


def pack_rows(document):
    return sorted({
        (packs[p]['tdoc:crPackId'], packs[p]['tdoc:tsgMeeting'])
        for p in doc_packs.get(document, set())
        if p in packs
    })


answers = []
for q in questions:
    sentence = q['question']
    rows = set()
    note = ''
    document_match = re.search(r'R1-\d+', sentence)
    if document_match:
        document = 'tdoc:' + document_match.group()
        if q['fields'] == ['cr_pack', 'tsg_meeting']:
            rows.update(pack_rows(document))
        else:
            clauses = [None]
            if 'clause' in q['fields']:
                spec = re.search(r'to TS ([\d.]+)', sentence).group(1)
                clauses = sorted({
                    section.split('-Rel-', 1)[1].split('-', 1)[1]
                    for section in doc_sections.get(document, set())
                    if section.startswith('tdoc:section/' + spec + '-Rel-')
                })
            for code, meeting in decision_rows(document):
                for pack_number, plenary_meeting in pack_rows(document):
                    for clause in clauses:
                        row = (code, meeting, pack_number, plenary_meeting)
                        rows.add(row + (clause,) if clause is not None else row)
        if not rows:
            note = (
                'Cannot determine a CR pack from the supplied records: no membership '
                'is recorded for this exact document number.'
            )
            decisions = decision_rows(document)
            if decisions:
                note += ' Its source-verified whole-document disposition is ' + '; '.join(
                    code + ' at ' + meeting for code, meeting in decisions
                ) + '.'
            if docs[document].get('revisedTo'):
                note += (
                    ' I read the question as asking about the named document. '
                    'An alternative would follow its revision link to '
                    + ', '.join(docnum(r) for r in many(docs[document]['revisedTo']))
                    + ', which is a different document number.'
                )
    elif q['id'] in section_queries:
        release, clause, spec = section_queries[q['id']]
        section = f'tdoc:section/{spec}-{release}-{clause}'
        for document in sorted(section_docs.get(section, set())):
            record = docs.get(document)
            if not record or record.get('tdoc:type') != 'CR':
                continue
            if releases.get(record.get('targetRelease')) != release:
                continue
            if 'tdoc:spec/' + spec.replace('.', '_') not in many(record.get('modifies')):
                continue
            for code, meeting in decision_rows(document):
                for pack_number, plenary_meeting in pack_rows(document):
                    rows.add((record['tdoc:tdocNumber'], code, meeting, pack_number))
    else:
        pack_number = re.search(r'RP-\d+', sentence).group()
        for document in sorted(pack_members.get('tdoc:crpack/' + pack_number, set())):
            for code, meeting in decision_rows(document):
                rows.add((docnum(document), code, meeting))
        multi_disposition = {
            document for document in pack_members.get('tdoc:crpack/' + pack_number, set())
            if len({code for code, meeting in decision_rows(document)}) > 1
        }
        if multi_disposition:
            note = (
                'I include every distinct qualifying disposition. Ten member CRs have '
                'both agreed and endorsed recorded as source_verified with whole_target '
                'scope at RAN1#122b, producing 28 rows for 18 CRs. An alternative reading '
                'would choose one final disposition per CR; the question does not '
                'specify that selection.'
            )
    answers.append({'id': q['id'], 'rows': [list(r) for r in sorted(rows)], 'note': note})

if '--write' in sys.argv:
    with open('answers.jsonl', 'w') as stream:
        for answer in answers:
            stream.write(json.dumps(answer, ensure_ascii=False) + '\n')

if '--audit' in sys.argv:
    print('CANDIDATES', len(candidates), 'MISSING_TDOCS', sorted(candidates - docs.keys()))
    print('SECTION_EDGE_DIFFERENCES', section_edge_differences)
    print('MISSING_EVENTS', sorted(event_ids - events.keys()))
    for q, answer in zip(questions, answers):
        print(json.dumps({'question': q['id'], 'rows': answer['rows'], 'note': answer['note']}))
        if q['id'] in section_queries:
            release, clause, spec = section_queries[q['id']]
            relevant = section_docs.get(f'tdoc:section/{spec}-{release}-{clause}', set())
        elif 'RP-' in q['question']:
            number = re.search(r'RP-\d+', q['question']).group()
            relevant = pack_members.get('tdoc:crpack/' + number, set())
        else:
            relevant = {'tdoc:' + re.search(r'R1-\d+', q['question']).group()}
        for document in sorted(relevant):
            record = docs.get(document, {})
            summary = [
                docnum(document),
                record.get('tdoc:type'),
                releases.get(record.get('targetRelease')),
                record.get('modifies'),
                record.get('tdoc:status'),
                pack_rows(document),
                decision_rows(document),
                [[d['code'], d['status'], d['scope'], d['event']] for d in dispositions.get(document, [])],
            ]
            print(json.dumps(summary))
else:
    for answer in answers:
        print(json.dumps(answer))
