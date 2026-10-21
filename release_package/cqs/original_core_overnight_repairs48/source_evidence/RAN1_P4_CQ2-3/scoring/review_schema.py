"""Validate the recorded scope and identity of AI semantic judgments.

This checks evidence records, not the truth of their semantic conclusions.
"""


def check_pass(review, original_question, units, *, criteria_sha, identity_key, identity_sha):
    if (review.get('status') != 'pass' or review.get(identity_key) != identity_sha
            or review.get('criteria_sha256') != criteria_sha):
        raise ValueError('semantic judgment is not pinned to the admitted definition/criteria')
    evidence = review.get('semantic_evidence')
    if isinstance(evidence, list):
        names = [row.get('unit') for row in evidence]
        if len(names) != len(set(names)) or set(names) != set(units):
            raise ValueError('semantic evidence does not cover exactly the seven criteria units')
        for row in evidence:
            quote = row.get('original_quote')
            if (row.get('status') != 'pass' or not isinstance(quote, str) or not quote
                    or quote not in original_question or not row.get('finding')
                    or not isinstance(row.get('query_clauses'), list)):
                raise ValueError('semantic unit lacks original-question evidence and a pass finding')
    elif isinstance(evidence, dict):
        if set(evidence) != set(units):
            raise ValueError('semantic evidence does not cover exactly the seven criteria units')
        if not any(row.get('original_derivation') == original_question or row.get('original_quote') == original_question
                   for row in evidence.values()):
            raise ValueError('semantic judgment omits the original question quotation')
        for row in evidence.values():
            if (not (row.get('original_derivation') or row.get('independent_derivation'))
                    or not (row.get('query_evidence') or row.get('query_clause'))
                    or not (row.get('assessment') or row.get('judgment')) or row.get('status', 'pass') != 'pass'
                    or (row.get('original_quote') and row['original_quote'] not in original_question)):
                raise ValueError('semantic unit lacks derivation, query evidence or a pass finding')
    else:
        raise ValueError('semantic evidence must contain separate per-unit judgments')
