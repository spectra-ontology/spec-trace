#!/usr/bin/env python3
"""reconcile_tdoc_source_classification.py — fenced source-backed CR class reconciliation.

Spec: Phase-1 document classification and selected-source count contract.
Ontology: own-numbered CR documents, source Spec/Release and independent disposition.
Cycle: validate source ledger → full file/live preimages → guarded transaction → readback.
배경: uploaded numbered CR forms can retain spreadsheet reservation classifications.
사용: --wg RAN4 --out retained-receipt.json [--apply].
LLM 호출: none. Local evidence and explicit Neo4j writes only.
"""
from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path
import sys

import reconcile_tdoc_source_supplements as guarded
from tdoc_source_supplements import SupplementError, reference_graphs
from tdoc_source_classification import (apply_source_classifications, source_inputs,
                                       target_selection, validated_classifications)


def build_proposal(root, wg, *, selected_targets=None, selection_fences=None):
    directory = guarded.axis.tree_path('ontology_instances', wg=wg, phase=1, root=root)
    path = directory / 'tdocs.jsonld'
    original = path.read_bytes()
    document = json.loads(original)
    instances = document['@graph']
    references = reference_graphs(directory)
    selected = {m['tdoc:meetingNumber'] for m in references['meetings']}
    rows = validated_classifications(root, wg, selected, selected_targets=selected_targets)
    if not rows:
        raise SupplementError('No selected source-backed classifications')
    if selected_targets is not None and {r['target'] for r in rows} != set(selected_targets):
        raise SupplementError('Selected classifications are outside the current source population')
    changed = apply_source_classifications(root, wg, instances, references, selected,
                                           selected_targets=selected_targets)
    if len({n['@id'] for n in instances}) != len(instances):
        raise SupplementError('Canonical classification identity collision')
    props, labels, add, remove, endpoints = {}, {}, set(), set(), {}
    for row in rows:
        id_ = 'tdoc:' + row['target']
        labels[id_] = ['CR', 'Tdoc']
        for delta in row['deltas']:
            field, before, after = delta['field'], delta['before'], delta['sourceBackedValue']
            if field == '@type':
                continue
            props.setdefault(id_, {})[field.removeprefix('tdoc:') if field.startswith('tdoc:') else '_' + field] = after
            if field in guarded.RELATIONS:
                relation, label = guarded.RELATIONS[field]
                endpoints[after] = label
                add.add((id_, relation, after))
                if before is not None:
                    remove.add((id_, relation, before))
    fences = source_inputs(root, wg, selected, selected_targets=selected_targets)
    fences.update(selection_fences or {})
    for name in ('meetings', 'specs', 'releases'):
        p = directory / (name + '.jsonld')
        fences[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    for name in ('reconcile_tdoc_source_classification.py', 'tdoc_source_classification.py',
                 'reconcile_tdoc_source_supplements.py', 'tdoc_source_supplements.py',
                 'decision_disposition.py', 'docx_text.py'):
        p = Path(__file__).with_name(name)
        fences[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return dict(wg=wg, path=path, original=original,
        encoded=json.dumps(document, ensure_ascii=False, indent=2), fences=fences,
        beforeCount=len(instances), afterCount=len(instances), newCanonicalNodes=[],
        supplementTargets=[], affected=sorted(r['target'] for r in rows),
        sourceDispositions={}, correctionScopes=dict(Counter(r['scope'] for r in rows)),
        changedCanonicalFields=changed, properties=props, labels=labels,
        addEdges=sorted(add), removeEdges=sorted(remove), endpoints=endpoints)


if __name__ == '__main__':
    scope = argparse.ArgumentParser(add_help=False)
    scope.add_argument('--targets-file', type=Path)
    selection, remaining = scope.parse_known_args()
    def selected_proposal(root, wg):
        targets, fences = target_selection(root, wg, selection.targets_file) if selection.targets_file else (None, {})
        return build_proposal(root, wg, selected_targets=targets, selection_fences=fences)
    sys.argv = [sys.argv[0], *remaining]
    guarded.main(proposal_builder=selected_proposal, wg_choices=[f'RAN{i}' for i in range(1, 6)])
