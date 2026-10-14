"""Replay actual per-item requested-field scoring controls and corruptions."""
import original_scorer


def checks(task, records, order_groups=None):
    results = []

    def require(name, predictions, expected):
        outcome = original_scorer.score(task, records, predictions, diagnostic=True, order_groups=order_groups)
        results.append({'check': name, 'pass': outcome['exact'] is expected})

    require('complete_requested_reference', records, True)
    require('extra_invalid_record', records + [{}], False)
    if not records:
        require('formal_empty_reference', [], True)
        return results
    require('empty_prediction_for_nonempty_gold', [], False)
    for field in task['required_fields']:
        name = field['name']
        require('missing_required_field:' + name, [{k: v for k, v in r.items() if k != name} for r in records], False)
        require('wrong_type_or_shape:' + name, [dict(r, **{name: {'__wrong_shape__': True}}) for r in records], False)
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
            require('wrong_requested_value:' + name, [dict(r, **{name: replacement}) for r in records], False)
    require('unrequested_context_ignored', [dict(r, __unasked_context__=True) for r in records], True)
    return results
