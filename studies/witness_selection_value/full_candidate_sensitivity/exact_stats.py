"""Integer finite-policy PMFs. Importing performs no measurement."""
from fractions import Fraction
from functools import reduce
from math import gcd


def fraction(value):
    value = Fraction(value)
    return {'numerator': value.numerator, 'denominator': value.denominator,
            'rational': str(value), 'decimal_display': float(value)}


def convolve(left, right):
    result = {}
    for a, x in left.items():
        for b, y in right.items():
            result[a + b] = result.get(a + b, 0) + x * y
    return result


def summarize_pmf(coefficients, population, score_denominator):
    coefficients = {int(k): int(v) for k, v in coefficients.items() if v}
    if population <= 0 or not coefficients or sum(coefficients.values()) != population:
        raise ValueError('Invalid exact finite PMF')
    support = sorted(coefficients)
    mean = Fraction(sum(k * v for k, v in coefficients.items()), population * score_denominator)
    quantiles = {}
    for label, target in [('0.05', Fraction(1, 20)), ('0.50', Fraction(1, 2)),
                          ('0.95', Fraction(19, 20))]:
        cumulative = 0
        for index in support:
            cumulative += coefficients[index]
            if cumulative * target.denominator >= population * target.numerator:
                quantiles[label] = fraction(Fraction(index, score_denominator))
                break
    return {'mean': fraction(mean), 'minimum': fraction(Fraction(support[0], score_denominator)),
            'maximum': fraction(Fraction(support[-1], score_denominator)),
            'policy_quantiles_not_confidence_intervals': quantiles,
            'pmf_integer_denominator': population, 'score_index_denominator': score_denominator,
            'pmf_integer_coefficients': {str(k): coefficients[k] for k in support}}


def aggregate(cells, subset, policy, weighting):
    # Denominators are assigned within each cell BEFORE any cross-cell weight.
    chosen = [c for c in cells if c['primary_available'] and c['subsets'][subset]]
    if len(chosen) == 0:
        return None
    counts = [len(c['subsets'][subset]) for c in chosen]
    if weighting == 'control':
        shifts, score_denominator = [1] * len(chosen), sum(counts)
    elif weighting == 'equal_cell':
        lattice = reduce(lambda a, b: a * b // gcd(a, b), counts, 1)
        shifts = [lattice // count for count in counts]
        score_denominator = len(chosen) * lattice
    else:
        raise ValueError(weighting)
    polynomial, population = {0: 1}, 1
    expected = Fraction(0)
    for cell, shift, count in zip(chosen, shifts, counts):
        n = cell['policy_sizes'][policy]
        if n <= 0:
            raise ValueError('Empty eligible cell entered primary aggregate')
        histogram = cell['histograms'][policy][subset]
        if sum(histogram.values()) != n:
            raise ValueError('Cell histogram denominator mismatch')
        polynomial = convolve(polynomial, {j * shift: number for j, number in histogram.items()})
        population *= n
        within_cell_expected_count = Fraction(sum(j * v for j, v in histogram.items()), n)
        expected += within_cell_expected_count * shift / score_denominator
    result = summarize_pmf(polynomial, population, score_denominator)
    if expected != Fraction(result['mean']['numerator'], result['mean']['denominator']):
        raise ValueError('PMF expectation differs from cell-normalized formula')
    result.update(cells=[c['cell_id'] for c in chosen], cell_count=len(chosen),
                  category_empty_available_cells=[c['cell_id'] for c in cells
                                                  if c['primary_available'] and not c['subsets'][subset]],
                  frozen_control_slots=sum(counts), weighting=weighting,
                  independent_cell_draws_hypothetical=True)
    return result


def contrast(eligible, universe):
    get = lambda value: Fraction(value['numerator'], value['denominator'])
    return {'mean_E_minus_U': fraction(get(eligible['mean']) - get(universe['mean'])),
            'minimum_E_minus_maximum_U': fraction(get(eligible['minimum']) - get(universe['maximum'])),
            'maximum_E_minus_minimum_U': fraction(get(eligible['maximum']) - get(universe['minimum'])),
            'interpretation': 'Exact support bounds under the stated finite policies; not an unseen-error bound.'}
