"""Explicit partition composition of unchanged canonical typed/top-k scorers.

This supplement validates eligibility. It does not create native gold, infer
question meaning, or change the canonical scientific files.
"""
import copy

def validate(policy, full_population, prediction, scorer, original_scorer):
    if type(prediction) is not list:
        raise ValueError('outer records must be list')
    # Schema must be checked before any nested set normalization.
    _, errors = scorer.project(prediction, policy['outer_required_fields'])
    if errors:
        return {'exact':False,'reason':'typed_prediction_error','type_errors':errors}
    if any(set(row) != {'workItemCode','topCompanies'} for row in prediction):
        return {'exact':False,'reason':'outer_field_shape'}
    if len(prediction) != policy['outer_selection']['value']:
        return {'exact':False,'reason':'outer_cardinality'}
    names=[row['workItemCode'] for row in prediction]
    expected=sorted(full_population)[:policy['outer_selection']['value']]
    if len(names)!=len(set(names)):
        return {'exact':False,'reason':'duplicate_outer_partition'}
    coverage=scorer.score(policy['outer_WI_contract'],[{'workItemCode':n} for n in expected],
                          [{'workItemCode':n} for n in names],diagnostic=True)
    if not coverage['exact']:
        return {'exact':False,'reason':'outer_partition_membership','canonical_outer':coverage}
    outcomes=[]
    for row in prediction:
        code=row['workItemCode']
        inner=copy.deepcopy(policy['per_partition_contract'])
        gold=full_population[code]
        # This is eligibility-population input. A later native bridge must bind
        # the independently captured limited rows and uncapped counts separately.
        order=original_scorer.make_order_groups(inner,gold,gold)
        result=original_scorer.score(inner,gold,row['topCompanies'],diagnostic=True,order_groups=order)
        outcomes.append({'workItemCode':code,'canonical':result})
    return {'exact':all(v['canonical']['exact'] for v in outcomes),
            'reason':'canonical_partition_eligibility','canonical_outer':coverage,'partitions':outcomes,
            'native_gold_created':False,'canonical_scientific_modules_modified':False}
