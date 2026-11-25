"""TR metadata correction requires exact point coverage and preserved payloads."""
import copy
from types import SimpleNamespace
import unittest

from reconcile_tr_source_identity import verify_points


class IdentityReadback(unittest.TestCase):
    def setUp(self):
        self.before = [SimpleNamespace(id=i, vector=[0.5, 0.5],
            payload={'trNumber': '38.000', 'text': 'synthetic', 'custom': {'keep': i}})
            for i in (1, 2)]
        self.projection = {'trTitle': 'Synthetic report', 'sourceDocumentSha256': 'a' * 64}
        self.after = copy.deepcopy(self.before)
        for point in self.after:
            point.payload.update(self.projection)

    def test_exact_projection_accepts_reordered_points(self):
        verify_points(self.before, list(reversed(self.after)), self.projection)

    def test_missing_duplicate_or_foreign_point_is_rejected(self):
        foreign = copy.deepcopy(self.after[0]); foreign.id = 3
        for after in (self.after[:1], self.after + [self.after[0]], [self.after[0], foreign]):
            with self.subTest(ids=[p.id for p in after]), self.assertRaisesRegex(ValueError, 'coverage'):
                verify_points(self.before, after, self.projection)

    def test_unknown_payload_field_or_vector_change_is_rejected(self):
        for field in ('custom', 'text', 'vector', 'trTitle'):
            after = copy.deepcopy(self.after)
            if field == 'vector':
                after[0].vector = [0.1, 0.9]
            else:
                after[0].payload[field] = 'changed'
            with self.subTest(field=field), self.assertRaises(ValueError):
                verify_points(self.before, after, self.projection)


if __name__ == '__main__':
    unittest.main()
