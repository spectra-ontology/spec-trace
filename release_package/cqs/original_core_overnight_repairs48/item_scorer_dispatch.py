"""Prospective per-item dispatch; shared kernels retain their original bytes."""
import sys
if sys.flags.optimize:
    raise SystemExit('Run with assertions enabled')
import original_scorer
import one_record_sample_scorer
def score(contract, gold_rows, predicted_rows, *, order_groups=None, sample_pool=None, diagnostic=False):
    if contract['collection']['kind'] == one_record_sample_scorer.KIND:
        if order_groups not in (None, []):
            raise ValueError('joint record uses its explicit complete sample pool')
        return one_record_sample_scorer.score(contract, gold_rows, predicted_rows,
                                             sample_pool=sample_pool, diagnostic=diagnostic)
    if sample_pool is not None:
        raise ValueError('sample pool supplied to an unrelated contract')
    return original_scorer.score(contract, gold_rows, predicted_rows,
                                 order_groups=order_groups, diagnostic=diagnostic)
make_order_groups = original_scorer.make_order_groups

