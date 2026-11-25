#!/usr/bin/env python3
"""role_agenda_evidence.py — Serialize source-qualified report placements and their evidence.

Spec: docs/tsg/RAN/formal/RAN1/phase-2/step1_parsing.md.
Ontology: reportedUnderAgenda with EvidenceAssertion and shared EvidenceFragment.
Cycle: actual accepted report paragraph/heading/TOC receipts -> JSON-LD.
배경: a shared Tdoc can be reported under another agenda without changing its registration.
사용: role_assertion_id(meeting, role), evidence_document(validated_records).
LLM 호출: none. This module performs no file or database writes.
"""
from __future__ import annotations

import hashlib
import json

PREDICATE = 'https://w3id.org/spectra#reportedUnderAgenda'


def role_assertion_id(meeting, role):
    number = meeting.split('#', 1)[1]
    return f'RAN1:role-agenda:{number}:{role["tdoc_number"]}:p{role["paragraph_index"]}'


def evidence_document(records, context):
    assertions, fragments = {}, {}
    for record in records:
        aid = record['assertionId']
        node = {'@id': 'tdoc:assertion/' + aid, '@type': 'EvidenceAssertion',
                'assertionId': aid, 'evidenceStatus': record['evidenceStatus'],
                'assessmentMethod': json.dumps({'method': record['method'],
                    'sourceRole': record['category'], 'meeting': record['meeting'],
                    'paragraphIndex': record['paragraphIndex'],
                    'scope': 'report_placement_separate_from_registered_primary_agenda'}, sort_keys=True),
                'assertionSubject': record['tdoc'],
                'assertionObject': record['agendaId'], 'assertionPredicateIRI': PREDICATE,
                'hasEvidence': []}
        for item in record['evidence']:
            if not item['quote'].strip():
                continue
            locator = f'word/document.xml accepted body paragraph {item["paragraphIndex"]}; {item["role"]}'
            body = {'evidencePath': record['sourcePath'], 'evidenceSha256': record['sourceSha256'],
                    'evidenceLocator': locator, 'evidenceQuote': item['quote']}
            key = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            fid = 'tdoc:evidence/role-agenda-' + key
            fragments[fid] = {'@id': fid, '@type': 'EvidenceFragment', **body}
            if fid not in node['hasEvidence']:
                node['hasEvidence'].append(fid)
        if aid in assertions and assertions[aid] != node:
            raise ValueError(f'Conflicting role-placement assertion identity: {aid}')
        assertions[aid] = node
    return {'@context': context, '@graph': [*assertions.values(), *fragments.values()]}
