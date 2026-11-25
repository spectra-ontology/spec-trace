#!/usr/bin/env python3
"""ts_caption_coherence.py — complete captions in edition-equivalent TS twins.

Spec: identical source-body identities in primary and P12 collections.
Ontology: every claimed edition binds each actual caption to its source section.
Cycle: same old body → independently bound source captions → coherent new body.
배경: shared source chunks require the same complete caption presentation.
사용: complete_twins(records, bodies, source_candidates) returns reviewed deltas.
LLM 호출: 없음. Pure transformation; original records and bodies remain unchanged.
"""
from copy import deepcopy
import hashlib


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def key(record):
    return record['collection'], str(record['pointId'])


def complete_twins(records, bodies, candidates):
    records = deepcopy(records)
    bodies = dict(bodies)
    candidates = {c['candidate']: c for c in candidates}
    grouped = {}
    for record in records:
        grouped.setdefault((record['collection'].split('_')[0], record['chunkId']), []).append(record)
    completed = []
    for twins in grouped.values():
        if len({r['newBodySHA256'] for r in twins}) <= 1:
            continue
        if len({r['oldBodySHA256'] for r in twins}) != 1:
            raise ValueError('Same canonical identity has different historical bodies')
        donors = [r for r in twins if r.get('captionEdits')]
        if len(donors) != 1:
            raise ValueError('Conflicting bodies require one exact source-caption donor')
        donor = donors[0]
        donor_editions = {tuple(s['edition']) for s in donor['sources']}
        for recipient in twins:
            if recipient is donor:
                continue
            editions = {tuple(s['edition']) for s in recipient['sources']}
            if not editions or not editions.issubset(donor_editions):
                raise ValueError('Caption donor does not cover each recipient source edition')
            prior = bodies[key(recipient)]
            lines = prior.splitlines(keepends=True)
            proofs = []
            for edit in donor['captionEdits']:
                index = edit['lineIndex']
                old, new = edit['oldCaption'], edit['replacementCaption']
                line = lines[index]
                ending = line[len(line.rstrip('\r\n')):]
                if sha(old + ending) != edit['oldLineSHA256'] or sha(new + ending) != edit['newLineSHA256']:
                    raise ValueError('Caption edit literal SHA mismatch')
                evidence = [candidates[i] for i in edit['sourceCandidateIds']]
                for wg, spec, release in editions:
                    actual = [s for s in evidence if (s['wg'], s['spec'], s['release']) == (wg, spec, release)
                              and s['oldCaption'] == old and s['replacementCaption'] == new
                              and any(spec + '-' + o['sectionNumber'] == donor['sources'][0]['sectionId']
                                      for o in s['observedSourceSections'])]
                    if not actual:
                        raise ValueError(f'Caption lacks an exact source-section/edition binding: {recipient["chunkId"]} {(wg, spec, release)} {old}')
                    proofs.extend({'source': s['source'], 'sha256': s['sourceSHA256'],
                                   'locator': s['sourceLocator'], 'edition': [wg, spec, release]} for s in actual)
                if line.rstrip('\r\n') == old:
                    lines[index] = new + ending
                elif line.rstrip('\r\n') != new:
                    raise ValueError('Recipient caption differs from the exact source-bound line')
            current = ''.join(lines)
            if current != bodies[key(donor)]:
                raise ValueError('Twin bodies differ outside the adjudicated caption edits')
            recipient['newBodySHA256'] = sha(current)
            recipient['captionEdits'] = deepcopy(donor['captionEdits'])
            bodies[key(recipient)] = current
            completed.append({'collection': recipient['collection'], 'pointId': recipient['pointId'],
                              'chunkId': recipient['chunkId'], 'oldProposedBodySHA256': sha(prior),
                              'newBodySHA256': sha(current), 'donorCollection': donor['collection'],
                              'sourceBindings': proofs})
    return records, bodies, completed
