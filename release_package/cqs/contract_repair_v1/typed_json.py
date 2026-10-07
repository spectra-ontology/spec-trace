"""Strict JSON shape checks without coercion, used for nested output fields."""
import math


def matches(value, schema):
    kinds = schema.get('type')
    kinds = kinds if isinstance(kinds, list) else [kinds]
    accepted = {
        'string': isinstance(value, str), 'integer': type(value) is int,
        'number': type(value) in (int, float) and math.isfinite(value),
        'boolean': type(value) is bool, 'null': value is None,
        'array': isinstance(value, list), 'object': isinstance(value, dict)}
    if not any(accepted.get(kind, False) for kind in kinds):
        return False
    if isinstance(value, list):
        return (len(value) <= schema.get('maxItems', len(value))
                and all(matches(item, schema['items']) for item in value))
    if isinstance(value, dict):
        properties = schema.get('properties', {})
        return (all(key in value for key in schema.get('required', []))
                and (schema.get('additionalProperties') is not False
                     or all(key in properties for key in value))
                and all(matches(item, properties[key]) for key, item in value.items() if key in properties))
    return True
