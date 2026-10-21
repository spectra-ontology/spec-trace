"""Mandatory, prospective binding for partitioned top-k validation.

Uses the public projection function and unchanged canonical scoring kernels.
The old generic set verifier does not dispatch this supplement automatically.
"""
import json
from nested_partition_eligibility import validate

def exact(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)

def check_binding(definition, policy, verify_release):
    if set(definition) != set(verify_release.DEFINITION_KEYS):
        raise ValueError('canonical definition key set differs')
    expected={'partition_field':'workItemCode','members_field':'topCompanies',
              'outer_selection':policy['outer_selection'],
              'member_contract':policy['per_partition_contract'],'supplement_required':True}
    if exact(definition['collection']) != exact({'kind':'set','partitioned_top_k':expected}):
        raise ValueError('definition is not explicitly bound to the required partition supplement')
    if exact(policy['definition_collection_must_include_explicit_supplement']) != exact(expected):
        raise ValueError('policy binding differs')
    if exact(definition['required_fields']) != exact(policy['outer_required_fields']):
        raise ValueError('projected field schema differs')
    if exact(definition['cardinality_policy']) != exact(policy['outer_WI_contract']['cardinality_policy']):
        raise ValueError('outer cardinality differs')
    if definition['original_question_preserved'] is not True:
        raise ValueError('original question preservation flag differs')
    return verify_release.digest(definition)

def score_prediction(definition, policy, full_population, prediction, scorer, original_scorer, verify_release):
    identity=check_binding(definition,policy,verify_release)
    # Projection is the actual public entry path. It retains nested types and
    # values; eligibility then uses the separately supplied full partitions.
    projected=verify_release.project(prediction,definition['required_fields'],['workItemCode','topCompanies'])
    result=validate(policy,full_population,projected,scorer,original_scorer)
    # Public projection ignores surplus top-level columns. Model-envelope
    # validation must still reject surplus named answer fields.
    if any(type(row) is not dict or set(row)!={'workItemCode','topCompanies'} for row in prediction):
        result={'exact':False,'reason':'surplus_or_missing_prediction_fields'}
    result['repair_sha256']=identity
    result['supplement_explicit']=True
    return result
