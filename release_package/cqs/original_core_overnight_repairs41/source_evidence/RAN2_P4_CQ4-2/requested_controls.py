"""The same twelve requested-role probes used before native execution."""
import copy


def run(task, rows, scorer, contract_checks):
    groups = scorer.make_order_groups(task, rows, rows)
    generic = contract_checks.checks(task, rows, groups)
    assert all(c['pass'] for c in generic)
    pred = scorer.reference_prediction(task, rows)
    results = []

    def check(name, value, wanted):
        actual = scorer.score(task, rows, value, diagnostic=True, order_groups=groups)
        assert actual['exact'] is wanted, (name, actual)
        results.append(dict(check=name, pass_=True, expected_exact=wanted, result=actual))

    check('unordered_serialization_of_same_five_complete_CR_records', list(reversed(pred)), True)
    check('first_returned_CR_replaced_with_later_existing_CR', pred[1:] + [rows[5]], False)
    check('duplicate_CR_identity_displaces_other_CR', pred[:-1] + [pred[0]], False)
    value = copy.deepcopy(pred); value[0]['reason'] = value[1]['reason']
    check('reason_from_different_CR_not_accepted', value, False)
    value = copy.deepcopy(pred); value[0]['summary'] = value[1]['summary']
    check('summary_from_different_CR_not_accepted', value, False)
    value = copy.deepcopy(pred); value[0]['summary'] = value[0]['summary'][:30]
    check('short_summary_fragment_does_not_supply_full_source_field', value, False)
    value = copy.deepcopy(pred); value[0].pop('summary')
    check('identity_and_reason_without_summary_rejected', value, False)
    value = copy.deepcopy(pred); value[0].pop('reason')
    check('identity_and_summary_without_reason_rejected', value, False)
    value = copy.deepcopy(pred); value[0]['reason'] = None
    check('null_requested_reason_rejected', value, False)
    value = copy.deepcopy(pred); value[0]['summary'] = 7
    check('nonstring_requested_summary_rejected', value, False)
    value = copy.deepcopy(pred); value[0]['tdocNumber'] = 1803854
    check('nonstring_CR_identity_rejected', value, False)
    check('unrequested_approval_payload_is_context_not_mandatory', [dict(r, Agreement_content=None) for r in pred], True)
    assert len(generic) == 15 and len(results) == 12 and len(groups) == 162 and len(pred) == 5
    return dict(generic=generic, requested=results, n=len(generic) + len(results), reference=pred)
