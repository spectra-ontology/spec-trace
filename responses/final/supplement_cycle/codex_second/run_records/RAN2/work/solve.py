import argparse
import collections
import json
import re


def graph(path):
    with open(path) as stream:
        return json.load(stream)['@graph']


def many(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def number(iri):
    return iri.removeprefix('tdoc:')


class Records:
    def __init__(self):
        self.questions = [json.loads(line) for line in open('questions.jsonl')]
        self.meetings = {x['@id']: x for x in graph('records/phase-1/meetings.jsonld')}
        self.releases = {x['@id']: x['tdoc:releaseName'] for x in graph('records/phase-1/releases.jsonld')}
        self.tdocs = {}
        keep = {'@id', '@type', 'tdoc:tdocNumber', 'tdoc:type', 'tdoc:title',
                'tdoc:status', 'targetRelease', 'presentedAt', 'revisedTo',
                'isRevisionOf', 'tdoc:crNumber', 'tdoc:crRevision',
                'tdoc:tsgCRPack', 'modifies', 'tdoc:clausesAffected'}
        data = graph('records/phase-1/tdocs.jsonld')
        for x in data:
            self.tdocs[x['@id']] = {k: v for k, v in x.items() if k in keep}
        del data

        self.packs = {x['tdoc:crPackId']: x for x in graph('records/phase-4/crpacks.jsonld')}
        self.pack_links = collections.defaultdict(lambda: collections.defaultdict(set))
        for p, x in self.packs.items():
            for d in many(x.get('hasCR')):
                self.pack_links[d][p].add('hasCR')
        self.sections = collections.defaultdict(lambda: collections.defaultdict(set))
        for x in graph('records/phase-4/section_extensions.jsonld'):
            for d in many(x.get('modifiedByCR')):
                self.sections[d][x['@id']].add('modifiedByCR')
        data = graph('records/phase-4/cr_extensions.jsonld')
        for x in data:
            d = x['@id']
            for p in many(x.get('belongsToCRPack')):
                self.pack_links[d][p.removeprefix('tdoc:crpack/')].add('belongsToCRPack')
            for s in many(x.get('modifiesSection')):
                self.sections[d][s].add('modifiesSection')
        del data
        for d, x in self.tdocs.items():
            for p in many(x.get('tdoc:tsgCRPack')):
                self.pack_links[d][p].add('tdoc:tsgCRPack')

        self.rejected_edges = set()
        for x in graph('records/phase-1/revision_source_assertions.jsonld'):
            if x.get('evidenceStatus') == 'rejected' and x.get('assertionPredicateIRI', '').endswith('#revisedTo'):
                self.rejected_edges.add((x['assertionSubject'], x['assertionObject']))
        self.revision_edges = collections.defaultdict(lambda: collections.defaultdict(set))
        for d, x in self.tdocs.items():
            for after in many(x.get('revisedTo')):
                if (d, after) not in self.rejected_edges:
                    self.revision_edges[d][after].add('revisedTo')
            for before in many(x.get('isRevisionOf')):
                self.revision_edges[before][d].add('isRevisionOf')

        self.events = {}
        for suffix in ['document_dispositions', 'agreements', 'conclusions', 'working_assumptions']:
            data = graph('records/phase-2/resolutions_' + suffix + '.jsonld')
            for x in data:
                self.events[x['@id']] = {'madeAt': x['madeAt'], 'content': x['content']}
            del data
        self.dispositions = collections.defaultdict(list)
        data = graph('records/phase-2/decision_dispositions.jsonld')
        for x in data:
            a = json.loads(x['assessmentMethod'])
            self.dispositions[x['dispositionTarget']].append({
                'id': x['@id'], 'event': x['dispositionOf'], 'code': x['dispositionCode'],
                'status': x['evidenceStatus'], 'scope': a.get('scope'),
                'rule': a.get('rule'), 'subject': a.get('subject'),
                'identity': a.get('identityStatus'),
                'quote': x['evidenceQuote'],
            })
        del data

    def meeting_name(self, event):
        iri = self.events[event]['madeAt']
        return self.meetings[iri]['tdoc:meetingNumber']

    def valid_dispositions(self, d):
        return [x for x in self.dispositions[d]
                if x['status'] == 'source_verified' and x['scope'] == 'whole_target'
                and self.meetings[self.events[x['event']]['madeAt']]['tdoc:workingGroup'] == 'RAN2']

    def section_parts(self, s):
        match = re.fullmatch(r'tdoc:section/(.+)-(Rel-\d+)-(.+)', s)
        if not match:
            raise ValueError(s)
        return match.groups()

    def descendants(self, d):
        seen = set()
        pending = list(self.revision_edges[d])
        while pending:
            target = pending.pop()
            if target not in seen:
                seen.add(target)
                pending.extend(self.revision_edges[target])
        return seen - {d}

    def describe_doc(self, d):
        print('DOC', number(d), json.dumps(self.tdocs.get(d), ensure_ascii=False))
        print('PACKS', dict(self.pack_links[d]))
        print('SECTIONS', {s: sorted(prov) for s, prov in self.sections[d].items()})
        for x in self.dispositions[d]:
            print('DECISION', {k: v for k, v in x.items() if k not in {'id', 'quote'}},
                  'MEETING', self.meeting_name(x['event']), 'QUOTE', x['quote'][:500])

    def answer(self, q):
        sentence = q['question']
        rows = set()
        notes = []
        if sentence.startswith('In which TSG RAN CR pack'):
            d = 'tdoc:' + re.search(r'R2-\d+', sentence).group()
            for p in self.pack_links[d]:
                if p in self.packs:
                    rows.add((p, self.packs[p]['tdoc:tsgMeeting']))
                else:
                    notes.append('The document names CR pack ' + p + ', but no plenary meeting for that pack is recorded.')
            if not rows and not notes:
                notes.append('No CR-pack membership is recorded for the specified document; the question presupposes a submission that these records do not establish.')
        elif sentence.startswith('TSG RAN CR pack'):
            p = re.search(r'RP-\d+', sentence).group()
            excluded = []
            for d, links in self.pack_links.items():
                if p not in links:
                    continue
                if self.tdocs.get(d, {}).get('tdoc:type') != 'CR':
                    continue
                if not self.valid_dispositions(d):
                    excluded.append(number(d))
                for x in self.valid_dispositions(d):
                    rows.add((number(d), x['code'], self.meeting_name(x['event'])))
            if excluded:
                notes.append('Excluded pack member(s) ' + ', '.join(sorted(excluded)) +
                             ': no source-verified whole-document RAN2 disposition is recorded for them; list status alone was not used.')
        elif sentence.startswith('RAN2 recorded document'):
            root = 'tdoc:' + re.search(r'R2-\d+', sentence).group()
            for d in self.descendants(root):
                for x in self.valid_dispositions(d):
                    for p in self.pack_links[d]:
                        rows.add((number(d), x['code'], p))
            if not rows:
                notes.append('No later version satisfies both the verified whole-document disposition and recorded CR-pack membership conditions.')
        elif sentence.startswith('Which Rel-'):
            rel, clause, spec = re.search(r'Which (Rel-\d+) change requests that modify clause (\S+) of TS ([\d.]+)', sentence).groups()
            section = 'tdoc:section/' + spec + '-' + rel + '-' + clause
            excluded = []
            for d, sections in self.sections.items():
                if section not in sections:
                    continue
                doc = self.tdocs.get(d, {})
                if doc.get('tdoc:type') != 'CR' or rel not in [self.releases[r] for r in many(doc.get('targetRelease'))]:
                    continue
                if 'tdoc:spec/' + spec.replace('.', '_') not in many(doc.get('modifies')):
                    continue
                if self.pack_links[d] and not self.valid_dispositions(d):
                    excluded.append(number(d))
                for x in self.valid_dispositions(d):
                    for p in self.pack_links[d]:
                        rows.add((number(d), x['code'], self.meeting_name(x['event']), p))
            if excluded:
                notes.append('Excluded ' + ', '.join(sorted(excluded)) +
                             ': clause and CR-pack links exist, but no source-verified whole-document RAN2 disposition is recorded.')
            if not clause[0].isdigit():
                notes.append('Interpreted ' + clause + ' as the exact named Section label in the records. An alternative is its enclosing numbered clause; the records do not specify that containment.')
        elif sentence.startswith(('Change request', 'Trace change request')):
            d = 'tdoc:' + re.search(r'R2-\d+', sentence).group()
            trace = sentence.startswith('Trace')
            spec = re.search(r'to TS ([\d.]+)', sentence).group(1)
            for x in self.valid_dispositions(d):
                for p in self.pack_links[d]:
                    if p not in self.packs:
                        continue
                    row = (x['code'], self.meeting_name(x['event']), p, self.packs[p]['tdoc:tsgMeeting'])
                    if trace:
                        for s in self.sections[d]:
                            section_spec, _, clause = self.section_parts(s)
                            if section_spec == spec:
                                rows.add(row + (clause,))
                    else:
                        rows.add(row)
            if not rows:
                why = []
                if not self.valid_dispositions(d):
                    why.append('no source-verified whole-document RAN2 disposition')
                if not self.pack_links[d]:
                    why.append('no recorded CR-pack membership')
                if trace and not self.sections[d]:
                    why.append('no explicit modified-section link')
                notes.append('The specified document has ' + '; '.join(why or ['no complete matching row']) + '.')
        else:
            raise ValueError(sentence)
        return {'id': q['id'], 'rows': [list(row) for row in sorted(rows)], 'note': ' '.join(dict.fromkeys(notes))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['answers', 'inspect', 'audit'])
    parser.add_argument('documents', nargs='*')
    args = parser.parse_args()
    r = Records()
    if args.action == 'inspect':
        for d in args.documents:
            r.describe_doc('tdoc:' + d)
    elif args.action == 'answers':
        with open('answers.jsonl', 'w') as stream:
            for q in r.questions:
                result = r.answer(q)
                stream.write(json.dumps(result, ensure_ascii=False) + '\n')
                print(result['id'], len(result['rows']), result['note'])
    elif args.action == 'audit':
        print('QUESTION TYPES', dict(collections.Counter(q['question'].split()[0] for q in r.questions)))
        print('MEETING NAME DIFFERENCES', [(x['tdoc:meetingNumber'], x['tdoc:canonicalMeetingNumber']) for x in r.meetings.values() if x['tdoc:meetingNumber'] != x['tdoc:canonicalMeetingNumber']])
        for q in r.questions:
            if q['question'].startswith('RAN2 recorded'):
                root = 'tdoc:' + re.search(r'R2-\d+', q['question']).group()
                descendants = r.descendants(root)
                print('REVISION', number(root), 'DESCENDANTS', len(descendants))
                for d in sorted({root} | descendants):
                    print(' ', number(d), '->', {number(a): sorted(prov) for a, prov in r.revision_edges[d].items()},
                          'STATUS', r.tdocs.get(d, {}).get('tdoc:status'),
                          'DECISIONS', [(x['code'], r.meeting_name(x['event'])) for x in r.valid_dispositions(d)],
                          'PACKS', list(r.pack_links[d]))
        print('SOURCE COVERAGE')
        c = collections.Counter(tuple(sorted(prov)) for links in r.pack_links.values() for prov in links.values())
        print('PACK LINKS', dict(c))
        c = collections.Counter(tuple(sorted(prov)) for links in r.sections.values() for prov in links.values())
        print('SECTION LINKS', dict(c))


if __name__ == '__main__':
    main()
