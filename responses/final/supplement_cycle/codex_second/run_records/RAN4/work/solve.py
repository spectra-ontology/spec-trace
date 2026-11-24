import json
import re
import gc
from collections import defaultdict, Counter


def load_records(path, consume):
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    for record in data['@graph']:
        consume(record)
    del data
    gc.collect()


def many(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


with open('questions.jsonl', encoding='utf-8') as f:
    questions = [json.loads(line) for line in f if line.strip()]
meetings = {}
load_records('records/phase-1/meetings.jsonld', lambda r: meetings.update({r['@id']: r['tdoc:meetingNumber']}))
releases = {}
load_records('records/phase-1/releases.jsonld', lambda r: releases.update({r['@id']: r['tdoc:releaseName']}))
specs = {}
load_records('records/phase-1/specs.jsonld', lambda r: specs.update({r['@id']: r['tdoc:specNumber']}))

packs = {}
pack_members = defaultdict(set)
doc_packs = defaultdict(set)
pack_edge_sources = defaultdict(set)

def add_pack_edge(doc, pack, source):
    pack_members[pack].add(doc)
    doc_packs[doc].add(pack)
    pack_edge_sources[(doc, pack)].add(source)


def pack_record(r):
    packs[r['@id']] = (r['tdoc:crPackId'], r['tdoc:tsgMeeting'])
    for doc in many(r.get('hasCR')):
        add_pack_edge(doc, r['@id'], 'hasCR')

load_records('records/phase-4/crpacks.jsonld', pack_record)
sections = defaultdict(set)
doc_sections = defaultdict(set)
section_pattern = re.compile(r'^tdoc:section/(.+)-Rel-(\d+)-(.+)$')

def add_section_edge(doc, section):
    match = section_pattern.fullmatch(section)
    assert match, section
    spec, release, clause = match.groups()
    key = (spec, 'Rel-' + release, clause)
    sections[key].add(doc)
    doc_sections[doc].add(key)


def section_record(r):
    for doc in many(r.get('modifiedByCR')):
        add_section_edge(doc, r['@id'])

load_records('records/phase-4/section_extensions.jsonld', section_record)

def cr_extension_record(r):
    for pack in many(r.get('belongsToCRPack')):
        add_pack_edge(r['@id'], pack, 'belongsToCRPack')
    for section in many(r.get('modifiesSection')):
        add_section_edge(r['@id'], section)

load_records('records/phase-4/cr_extensions.jsonld', cr_extension_record)

docs = {}
successors = defaultdict(set)
edge_sources = defaultdict(set)

def add_revision_edge(before, after, source):
    successors[before].add(after)
    edge_sources[(before, after)].add(source)


def tdoc_record(r):
    rid = r['@id']
    docs[rid] = {k: r[k] for k in ['tdoc:tdocNumber', 'tdoc:type', 'tdoc:status', 'presentedAt', 'targetRelease', 'modifies', 'tdoc:crNumber', 'tdoc:crRevision', 'tdoc:clausesAffected'] if k in r}
    for after in many(r.get('revisedTo')):
        add_revision_edge(rid, after, 'revisedTo')
    for before in many(r.get('isRevisionOf')):
        add_revision_edge(before, rid, 'isRevisionOf')
    for pack in many(r.get('tdoc:tsgCRPack')):
        add_pack_edge(rid, 'tdoc:crpack/' + pack, 'tdoc:tsgCRPack')

load_records('records/phase-1/tdocs.jsonld', tdoc_record)

def revision_assertion(r):
    if r.get('evidenceStatus') == 'rejected' and r.get('assertionPredicateIRI', '').endswith('#revisedTo'):
        successors[r['assertionSubject']].discard(r['assertionObject'])

load_records('records/phase-1/revision_source_assertions.jsonld', revision_assertion)

def descendants(start):
    seen = {start}
    pending = list(successors[start])
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        pending.extend(successors[current] - seen)
    return seen - {start}


def number(doc):
    return docs.get(doc, {}).get('tdoc:tdocNumber', doc.removeprefix('tdoc:'))


def is_release(doc, release):
    return any(releases.get(r) == release for r in many(docs.get(doc, {}).get('targetRelease')))


def is_spec(doc, spec):
    return any(specs.get(r) == spec for r in many(docs.get(doc, {}).get('modifies')))


def is_cr(doc):
    return docs.get(doc, {}).get('tdoc:type') == 'CR'


def classify(q):
    text = q['question']
    if text.startswith('In which TSG RAN CR pack'):
        return 'pack'
    if text.startswith('RAN4 recorded document'):
        return 'revisions'
    if text.startswith('Trace change request'):
        return 'trace'
    if text.startswith('TSG RAN CR pack'):
        return 'members'
    if text.startswith('Which Rel-'):
        return 'clause'
    if text.startswith('Change request'):
        return 'decision'
    raise ValueError(text)


query_info = {}
needed_docs = set()
for q in questions:
    kind = classify(q)
    info = {'kind': kind}
    if kind in ['pack', 'decision', 'trace', 'revisions']:
        doc = 'tdoc:' + re.search(r'R4-\d+', q['question']).group()
        info['doc'] = doc
        needed_docs.add(doc)
        if kind == 'revisions':
            info['candidates'] = descendants(doc)
            needed_docs.update(info['candidates'])
        if kind == 'trace':
            info['spec'] = re.search(r'to TS ([\d.\-]+)\)', q['question']).group(1)
    elif kind == 'members':
        pack = 'tdoc:crpack/' + re.search(r'RP-\d+', q['question']).group()
        info['pack'] = pack
        info['candidates'] = pack_members[pack]
        needed_docs.update(info['candidates'])
    elif kind == 'clause':
        release, clause, spec = re.search(r'Which (Rel-\d+) change requests that modify clause (\S+) of TS ([\d.\-]+)', q['question']).groups()
        info.update(release=release, clause=clause, spec=spec)
        # Release qualifies the CR. Clause links do not override CR targetRelease.
        all_exact = set().union(*(members for (s, r, c), members in sections.items() if s == spec and c == clause))
        info['candidates'] = {doc for doc in all_exact if is_cr(doc) and is_release(doc, release) and is_spec(doc, spec)}
        info['section_release_candidates'] = sections[(spec, release, clause)]
        info['subclauses'] = set().union(*(members for (s, r, c), members in sections.items() if s == spec and c.startswith(clause + '.')))
        info['subclauses'] = {doc for doc in info['subclauses'] if is_cr(doc) and is_release(doc, release) and is_spec(doc, spec)} - info['candidates']
        needed_docs.update(info['candidates'] | info['section_release_candidates'] | info['subclauses'])
    query_info[q['id']] = info

# Load the largest file alone; retain only the needed decision evidence.
dispositions = defaultdict(list)
all_dispositions = defaultdict(list)
scope_counts = Counter()

def disposition_record(r):
    if r['dispositionTarget'] not in needed_docs:
        return
    assessment = json.loads(r['assessmentMethod'])
    scope_counts[assessment.get('scope')] += 1
    item = {
        'resolution': r['dispositionOf'],
        'code': r['dispositionCode'],
        'evidence': r['evidenceStatus'],
        'scope': assessment.get('scope'),
        'decision_text': assessment.get('documentEntry', {}).get('decisionText', ''),
        'quote': r['evidenceQuote'],
    }
    all_dispositions[r['dispositionTarget']].append(item)
    if r['evidenceStatus'] == 'source_verified' and assessment.get('scope') == 'whole_target':
        dispositions[r['dispositionTarget']].append(item)

load_records('records/phase-2/decision_dispositions.jsonld', disposition_record)
needed_resolutions = {r['resolution'] for items in all_dispositions.values() for r in items}
resolutions = {}

def resolution_record(r):
    if r['@id'] in needed_resolutions:
        resolutions[r['@id']] = {k:r[k] for k in ['madeAt', 'aboutTdoc', 'resolutionScope'] if k in r}

for path in ['records/phase-2/resolutions_document_dispositions.jsonld', 'records/phase-2/resolutions_agreements.jsonld', 'records/phase-2/resolutions_conclusions.jsonld', 'records/phase-2/resolutions_working_assumptions.jsonld']:
    load_records(path, resolution_record)


def decision_pairs(doc):
    result = set()
    for disposition in dispositions[doc]:
        resolution = resolutions.get(disposition['resolution'])
        if resolution is None:
            continue
        meeting = meetings.get(resolution['madeAt'])
        if meeting is not None:
            result.add((disposition['code'], meeting))
    return result


def pack_pairs(doc):
    return {packs[pack] for pack in doc_packs[doc] if pack in packs}


def clause_values(doc, spec):
    return {clause for section_spec, release, clause in doc_sections[doc] if section_spec == spec}


answers = []
for q in questions:
    info = query_info[q['id']]
    kind = info['kind']
    rows = set()
    notes = []
    if kind == 'pack':
        rows = pack_pairs(info['doc'])
        if not rows:
            notes.append('No CR-pack membership is recorded for the named document. Interpreted the R4 number as the exact document; following other versions of the same CR could give a different result.')
    elif kind == 'decision':
        rows = {(code, meeting, pack, tsg) for code, meeting in decision_pairs(info['doc']) for pack, tsg in pack_pairs(info['doc'])}
        if not decision_pairs(info['doc']):
            notes.append('No source-verified whole-document disposition with a recorded RAN4 meeting was found for the named document.')
        if not pack_pairs(info['doc']):
            notes.append('No CR-pack membership is recorded for the named document.')
    elif kind == 'trace':
        rows = {(code, meeting, pack, tsg, clause) for code, meeting in decision_pairs(info['doc']) for pack, tsg in pack_pairs(info['doc']) for clause in clause_values(info['doc'], info['spec'])}
        if not decision_pairs(info['doc']):
            notes.append('No source-verified whole-document disposition with a recorded RAN4 meeting was found for the named document.')
        if not pack_pairs(info['doc']):
            notes.append('No CR-pack membership is recorded for the named document.')
        if not clause_values(info['doc'], info['spec']):
            notes.append('No clause-modification links for the named specification were found for the named document.')
        section_releases = {r for s,r,c in doc_sections[info['doc']] if s == info['spec']}
        if len(section_releases) > 1:
            notes.append('Included all linked clauses of the named specification because the sentence gives no release restriction. The section links span ' + ', '.join(sorted(section_releases)) + '; filtering to the CR target release would omit some clauses.')
    elif kind == 'members':
        rows = {(number(doc), code, meeting) for doc in info['candidates'] if is_cr(doc) for code, meeting in decision_pairs(doc)}
        for doc in sorted(info['candidates']):
            codes = {code for code, meeting in decision_pairs(doc)}
            if len(codes) > 1:
                if doc == 'tdoc:R4-2017391':
                    notes.append('R4-2017391 has source-verified whole-document agreed (CR source entry) and not_treated (reserved other source entry) at RAN4#97-e. Included both; a reading requiring the source entry itself to be CR-typed would retain agreed alone.')
                else:
                    notes.append(number(doc) + ' has multiple source-verified whole-document dispositions (' + ', '.join(sorted(codes)) + '). Retained all recorded dispositions; a final-disposition-only reading would require selecting among decision events.')
        if not rows:
            notes.append('No member CR has a source-verified whole-document disposition with a recorded RAN4 meeting.')
    elif kind == 'revisions':
        rows = {(number(doc), code, pack) for doc in info['candidates'] for code, meeting in decision_pairs(doc) for pack, tsg in pack_pairs(doc)}
        if not rows:
            notes.append('No recorded later revision satisfies both the source-verified whole-document disposition and CR-pack membership conditions.')
    elif kind == 'clause':
        rows = {(number(doc), code, meeting, pack) for doc in info['candidates'] for code, meeting in decision_pairs(doc) for pack, tsg in pack_pairs(doc)}
        qualified_subclauses = {doc for doc in info['subclauses'] if decision_pairs(doc) and pack_pairs(doc)}
        if qualified_subclauses:
            notes.append('Matched the named clause exactly. A broader reading that includes changes recorded only against its subclauses would add CRs.')
        if not rows:
            notes.append('No CR matches the exact clause, target release, source-verified whole-document disposition, and CR-pack membership conditions.')
    answers.append({'id': q['id'], 'rows': [list(row) for row in sorted(rows)], 'note': ' '.join(notes)})

assert len(answers) == 82
assert len({a['id'] for a in answers}) == len(answers)
for q, answer in zip(questions, answers):
    assert answer['id'] == q['id']
    assert all(len(row) == len(q['fields']) and all(isinstance(value, str) for value in row) for row in answer['rows'])
    assert len(answer['rows']) == len({tuple(row) for row in answer['rows']})
with open('answers.jsonl', 'w', encoding='utf-8') as f:
    for answer in answers:
        f.write(json.dumps(answer, ensure_ascii=False) + '\n')

print('COUNTS', dict(Counter(info['kind'] for info in query_info.values())))
print('NEEDED_DOCS',len(needed_docs),'DISPOSITION_SCOPES',dict(scope_counts))
for answer in answers:
    info=query_info[answer['id']]
    print(answer['id'], info['kind'], len(answer['rows']), answer['note'])
    if info['kind']=='revisions':
        print('  descendants',[(number(d),sorted(successors[d]),sorted(pack_pairs(d)),sorted(decision_pairs(d))) for d in sorted(info['candidates'])])
    if info['kind']=='clause':
        print('  candidate_crs', sorted(number(d) for d in info['candidates']))
        different = info['candidates'] ^ info['section_release_candidates']
        if different: print('  release_reading_differences',[(number(d),docs.get(d,{}).get('targetRelease'), sorted(pack_pairs(d)),sorted(decision_pairs(d))) for d in sorted(different)])
        qualified_subclauses = {doc for doc in info['subclauses'] if decision_pairs(doc) and pack_pairs(doc)}
        if qualified_subclauses: print('  qualified_subclause_only', sorted(number(d) for d in qualified_subclauses))
    if info['kind'] in ['pack','decision','trace']:
        doc=info['doc']
        if not answer['rows'] or any(d['scope']!='whole_target' for d in all_dispositions[doc]):
            print('  document_evidence',number(doc),docs.get(doc,{}).get('tdoc:status'),[(d['code'],d['evidence'],d['scope']) for d in all_dispositions[doc]],sorted(pack_pairs(doc)))
        other_edges=[(packs.get(p),sorted(pack_edge_sources[(doc,p)])) for p in doc_packs[doc] if pack_edge_sources[(doc,p)] != {'hasCR','belongsToCRPack','tdoc:tsgCRPack'}]
        if other_edges:print('  pack_edge_sources',other_edges)
print('TOTAL_ROWS',sum(len(a['rows']) for a in answers))
