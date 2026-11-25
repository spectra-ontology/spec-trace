"""Build metadata filter cases from a bounded payload sample and WG-specific fixtures."""

def select_filter_cases(payloads: list[dict], single_filter_tests: dict, combined_filter_tests: list, historical: bool = False) -> tuple:
    """Build positive cases from observed values and one coherent payload combination."""
    fields = tuple(single_filter_tests)
    observed = {field: [] for field in fields}
    combinations = []
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        values = {}
        for field in fields:
            raw = payload.get(field)
            candidates = raw if field == "source" and isinstance(raw, list) else [raw]
            valid = [v for v in candidates if isinstance(v, str) and v.strip()]
            if not valid:
                continue
            for value in valid:
                if value not in observed[field]:
                    observed[field].append(value)
            values[field] = [valid[0]] if field == "source" else valid[0]
        if len(values) >= 2:
            combinations.append(values)

    unsupported = [field for field in fields if not observed[field]]
    if historical:
        singles, combined = single_filter_tests, combined_filter_tests
        positive_count = sum(not case.get("expect_empty") for cases in singles.values() for case in cases) + len(combined)
    else:
        singles = {field: [] for field in fields}
        for field in fields:
            value_key = "values" if field == "source" else "value"
            if observed[field]:
                value = observed[field][0]
                singles[field].append({value_key: [value] if field == "source" else value,
                                       "description": "Observed selected-collection value"})
            for case in single_filter_tests[field]:
                if not case.get("expect_empty"):
                    continue
                value = case[value_key][0] if field == "source" else case[value_key]
                while value in observed[field]:
                    value += "__SPECTRA_VALIDATION_ABSENT__"
                singles[field].append({value_key: [value] if field == "source" else value,
                                       "description": "Absent-value negative check", "expect_empty": True})
        combined = ([{"id": "CF-OBSERVED", "description": "Fields observed together in one payload",
                      "filters": max(combinations, key=len)}] if combinations else [])
        positive_count = len(fields) - len(unsupported) + len(combined)
    return singles, combined, {"mode": "historical" if historical else "observed",
                               "sample_count": len(payloads), "sample_limit": 100,
                               "unsupported_fields": unsupported, "positive_cases": positive_count}
