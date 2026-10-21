"""Prospective explicit nested-top-k dispatch; outer complete-WI record metrics.

Eligibility uses unchanged canonical inner top-k scoring. A fully eligible
nested answer is one complete matching WI record. Company partial matches do
not contribute outer precision/recall. This module is not a native capture or
an amendment to any of the nine canonical scientific modules.
"""
import copy


def score(definition, policy, full_population, prediction, scorer, original_scorer,
          verify_release, bound_adapter, *, diagnostic=False, validated_task=None):
    identity = bound_adapter.check_binding(definition, policy, verify_release)
    if not diagnostic:
        if (type(validated_task) is not dict or validated_task.get('validation_status') != 'validated'
                or validated_task.get('id') != definition['id']
                or validated_task.get('repair_sha256') != identity):
            raise ValueError('production task envelope is absent, unvalidated or belongs to another repair')
        task_definition = {key: validated_task[key] for key in verify_release.DEFINITION_KEYS}
        if verify_release.digest(task_definition) != identity:
            raise ValueError('validated task definition differs from the fixed nine-key definition')
    if type(prediction) is not list:
        raise ValueError('records must be a list')
    expected = sorted(full_population)[:policy['outer_selection']['value']]
    # A representation-independent comparison label, never an answer field or
    # substitute native gold. All eligible nested subsets of one WI share it.
    outer_contract = {
        'required_fields': [
            {'name': 'workItemCode', 'type': 'string', 'nullable': False},
            {'name': '_complete_record_identity', 'type': 'string', 'nullable': False}],
        'collection': {'kind': 'set'},
        'cardinality_policy': copy.deepcopy(definition['cardinality_policy']),
        'validation_status': 'validated'}
    gold_comparison = [{'workItemCode': code, '_complete_record_identity': 'ELIGIBLE_COMPLETE_RECORD'}
                       for code in expected]
    observed = []
    judgments = []
    original_type_errors = []
    codes = []
    kernel = scorer.get_kernel()
    for index, row in enumerate(prediction):
        # Validate the original full answer schema before the set equivalence.
        _, errors = scorer.project([row], definition['required_fields'])
        original_type_errors.extend(dict(x, row=index) for x in errors)
        code = row.get('workItemCode') if type(row) is dict else None
        eligible = False
        reason = 'invalid_schema_or_unknown_WI'
        inner_result = None
        if (not errors and type(row) is dict and set(row) == {'workItemCode', 'topCompanies'}
                and code in expected):
            inner = copy.deepcopy(policy['per_partition_contract'])
            if not diagnostic:
                inner['validation_status'] = 'validated'
            population = full_population[code]
            groups = original_scorer.make_order_groups(inner, population, population)
            inner_result = original_scorer.score(inner, population, row['topCompanies'],
                diagnostic=diagnostic, order_groups=groups)
            eligible = inner_result['exact'] is True
            reason = 'eligible_complete_WI_record' if eligible else 'entire_WI_record_mismatch'
        if type(code) is str:
            codes.append(code)
        try:
            invalid_identity = 'INVALID_OR_INELIGIBLE:' + kernel.json_exact(row)
        except (ValueError, TypeError):
            invalid_identity = 'INVALID_OR_INELIGIBLE:' + repr(row)
        observed.append({'workItemCode': code, '_complete_record_identity':
            'ELIGIBLE_COMPLETE_RECORD' if eligible else invalid_identity})
        judgments.append({'row': index, 'workItemCode': code, 'eligible_complete_record': eligible,
                          'reason': reason, 'inner_canonical': inner_result})
    result = scorer.score(outer_contract, gold_comparison, observed, diagnostic=diagnostic)
    # Original outer set semantics define metric denominators. The explicit
    # answer contract additionally rejects repeated WI rows/raw extra rows.
    no_duplicate_WI = len(codes) == len(set(codes))
    raw_cardinality_valid = len(prediction) == len(expected)
    strict_shapes = all(type(row) is dict and set(row) == {'workItemCode', 'topCompanies'} for row in prediction)
    exact = (result['exact'] and not original_type_errors and no_duplicate_WI
             and raw_cardinality_valid and strict_shapes)
    result.update(exact=exact, repair_sha256=identity, diagnostic_only=diagnostic,
        type_errors=original_type_errors, cardinality_valid=raw_cardinality_valid and result['cardinality_valid'],
        duplicate_WI_valid=no_duplicate_WI, full_field_shapes_valid=strict_shapes,
        scoring_unit='outer complete WI record; inner company partial credit is zero',
        nested_eligibility_judgments=judgments, scientific_modules_modified=False,
        semantic_equivalence='per-WI canonical top-k acceptance defines complete-record equality',
        full_population_is_native_gold=False,
        set_duplicate_note='Equivalent duplicate complete records collapse in set F1, but exact rejects repeated WI/raw cardinality.')
    return result
