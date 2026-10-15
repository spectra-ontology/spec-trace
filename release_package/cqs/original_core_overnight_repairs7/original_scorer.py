"""Additive exact-descriptor matrix decoding; all legacy contracts delegate unchanged."""
from original_scorer_base import *
from original_scorer_base import score as base_score
from matrix_records import normalize_matrix_records, MatrixRepresentationError
from pathlib import Path
import hashlib

def score(contract,gold_rows,predicted_rows,*,diagnostic=False,order_groups=None):
    descriptor=contract.get('collection',{}).get('matrix_representation')
    if descriptor is None:
        return base_score(contract,gold_rows,predicted_rows,diagnostic=diagnostic,order_groups=order_groups)
    actual=hashlib.sha256((Path(__file__).parent/'matrix_records.py').read_bytes()).hexdigest()
    if descriptor.get('normalizer_sha256') != actual:
        raise ValueError('declared matrix normalizer differs from pinned code')
    try:
        decoded=normalize_matrix_records(contract,predicted_rows,typed.get_kernel())
    except MatrixRepresentationError as exc:
        decoded=[{'matrix_representation_error':str(exc)}]
    return base_score(contract,gold_rows,decoded,diagnostic=diagnostic,order_groups=order_groups)
