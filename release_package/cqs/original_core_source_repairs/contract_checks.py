"""Replay actual per-item requested-field scoring controls and corruptions."""
import original_scorer


def checks(task, records, order_groups=None):
    results = []
    predictions = original_scorer.reference_prediction(task, records)

    def require(name, predictions, expected):
        outcome = original_scorer.score(task, records, predictions, diagnostic=True, order_groups=order_groups)
        results.append({'check': name, 'pass': outcome['exact'] is expected})

    require('complete_requested_reference', predictions, True)
    require('extra_invalid_record', predictions + [{}], False)
    if not predictions:
        require('formal_empty_reference', [], True)
        return results
    require('empty_prediction_for_nonempty_gold', [], False)
    for field in task['required_fields']:
        name = field['name']
        require('missing_required_field:' + name, [{k: v for k, v in r.items() if k != name} for r in predictions], False)
        require('wrong_type_or_shape:' + name, [dict(r, **{name: {'__wrong_shape__': True}}) for r in predictions], False)
        values = [r[name] for r in records if r[name] is not None]
        replacement = None
        if field['type'] == 'string':
            replacement = '__ORIGINAL_CORE_WRONG_VALUE__'
            while replacement in values:
                replacement += '_'
        elif field['type'] in {'integer', 'number'}:
            replacement = min(values) - 1 if values else -1
        elif field['type'] == 'boolean':
            replacement = False if True in values else True
        if replacement is not None:
            require('wrong_requested_value:' + name, [dict(r, **{name: replacement}) for r in predictions], False)
    require('unrequested_context_ignored', [dict(r, __unasked_context__=True) for r in predictions], True)
    if task['collection']['kind'] == 'top_k_boundary_ties':
        if len(predictions) > 1:
            require('duplicate_requested_record', predictions[:-1] + predictions[:1], False)
        remaining = len(predictions)
        for group in order_groups:
            take = min(remaining, len(group))
            if 0 < take < len(group):
                offset = len(predictions) - remaining
                alternative = predictions[:offset] + group[-take:]
                require('alternative_boundary_subset', alternative, True)
            remaining -= take
        if len(records) > len(predictions):
            # A row below the boundary is forbidden; a different boundary row
            # is allowed and covered by the positive control above.
            first_rank = next(i for i, g in enumerate(order_groups) if predictions[-1] in g)
            if first_rank + 1 < len(order_groups):
                require('lower_rank_displaces_boundary', predictions[:-1] + order_groups[first_rank + 1][:1], False)
    return results
