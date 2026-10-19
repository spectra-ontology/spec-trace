"""Build a disjoint classification overlay while preserving the frozen index."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
LABELS={'contract_verified':'답안 계약 검증 통과','clarification_required':'명세 보완 필요',
        'evidence_pending':'근거·검증 미완료'}


DEFAULT_CANDIDATE_FILES=['metric_classification_candidates.json', 'missing_input_classification_candidates.json', 'extent_classification_candidates.json', 'conflicting_entity_description_candidates.json']

def build(candidate_paths=None):
    if candidate_paths is None:candidate_paths=[HERE/name for name in DEFAULT_CANDIDATE_FILES]
    baseline=[json.loads(l) for l in (HERE/'baseline560_metadata.jsonl').open()]
    assert len(baseline)==560 and len({r['id'] for r in baseline})==560
    candidates={}
    for path in candidate_paths:
        for r in json.loads(path.read_text())['cases']:
            assert r['id'] not in candidates, 'Duplicate classification candidate'
            candidates[r['id']]=r
    assert set(candidates)<=set(r['id'] for r in baseline)
    result=[]
    for r in baseline:
        ident=r['id'];candidate=candidates.get(ident)
        if r['immutable_public_status']=='pass':
            assert candidate is None, 'Do not overwrite a current pass with a diagnostic candidate'
            category='contract_verified';evidence='Pinned immutable current-core pass record and its referenced repair bundle.'
        elif candidate:
            category='clarification_required';evidence=candidate.get('evidence',candidate.get('why_original_query_does_not_close_contract'))
            q=candidate.get('question_sha256')
            if q:assert q==r['original_question_sha256']
        else:
            category='evidence_pending';evidence='Remaining immutable nonadmitted item; this overlay does not claim irreducible ambiguity or permanent impossibility.'
        item={**r,'classification':category,'classification_label_ko':LABELS[category],
              'classification_evidence':evidence,'diagnostic_subtype':candidate.get('subtype') if candidate else None,
              'benchmark_admission_changed':False}
        if candidate and candidate.get('subtype')=='conflicting_entity_description':
            assert candidate['classification_is_conditional'] is True and candidate['admission'] is False
            item.update(classification_is_conditional=True,classification_condition=candidate['condition'],
                        recovery_condition=candidate['recovery_condition'],remaining_answer_evidence_pending=candidate['remaining_answer_evidence_pending'])
        result.append(item)
    counts=Counter(r['classification'] for r in result)
    assert sum(counts.values())==560
    return result,{'registered_n':560,'partition_counts':dict(counts),
        'nonadmitted_legacy_n':sum(r['immutable_public_status']!='pass' for r in baseline),
        'classification_is_not_new_admission':True,'expert_validation_n':0}


def main():
    p=argparse.ArgumentParser();p.add_argument('--candidates',type=Path,action='append',required=True)
    p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    rows,summary=build(a.candidates);a.output_dir.mkdir(exist_ok=False)
    (a.output_dir/'classification_overlay560.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
    (a.output_dir/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':main()
