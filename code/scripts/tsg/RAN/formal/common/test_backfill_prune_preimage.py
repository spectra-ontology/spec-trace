"""Pruning refuses graph state absent from the retained recovery preimage."""
import contextlib
import copy
import io
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import prune_stale_backfill as prune


class PrunePreimage(unittest.TestCase):
    def setUp(self):
        self.snapshot = {'props': {'tdocNumber': 'R1-000001 '}, 'labels': ['Tdoc'], 'rels': []}
        self.entry = {'element_id': 'synthetic', 'props': self.snapshot['props'],
                      'labels': self.snapshot['labels'], 'relationships': self.snapshot['rels']}

    def test_same_snapshot_is_accepted_and_changed_or_missing_snapshot_is_rejected(self):
        snapshots = [copy.deepcopy(self.snapshot), None,
                     dict(self.snapshot, props={'tdocNumber': 'R1-000002'}),
                     dict(self.snapshot, labels=['Tdoc', 'Custom']),
                     dict(self.snapshot, rels=[{'type': 'CUSTOM', 'other_labels': ['Custom']}])]
        for index, snapshot in enumerate(snapshots):
            tx = SimpleNamespace(run=lambda *args, **kwargs: SimpleNamespace(single=lambda: snapshot))
            with self.subTest(index=index):
                if index:
                    with self.assertRaises(RuntimeError):
                        prune._assert_prune_preimage(tx, self.entry)
                else:
                    prune._assert_prune_preimage(tx, self.entry)

    def test_actual_prune_refuses_new_incident_relationship_before_move_or_delete(self):
        queries = []
        current = copy.deepcopy(self.snapshot)
        current['rels'] = [{'type': 'CUSTOM', 'other_labels': ['Custom']}]
        def run(query, **kwargs):
            queries.append(query)
            if query != prune.Q_SNAPSHOT:
                self.fail('graph mutation ran before preimage validation')
            return SimpleNamespace(single=lambda: self.snapshot)
        def execute_write(function):
            tx = SimpleNamespace(run=lambda query, **kwargs: SimpleNamespace(single=lambda: current))
            return function(tx)
        session = SimpleNamespace(run=run, execute_write=execute_write)
        stale = dict(element_id='synthetic', verdict='prune', name='R1-000001 ', twin='R1-000001',
                     twin_element_id=None, meetings=[], reason='', edges={})
        with patch.object(prune.backfill_provenance, 'stale_nodes', return_value=[stale]), \
             patch.object(prune, '_record', return_value=prune.PROJECT_ROOT/'synthetic.json'), \
             contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, 'relationship changed'):
                prune._prune_nodes(session, 'RAN1', True)
        self.assertEqual(queries, [prune.Q_SNAPSHOT])

    def test_equivalent_relationship_and_label_order_is_accepted(self):
        first = {'type': 'CUSTOM', 'other_labels': ['B', 'A']}
        second = {'type': 'OTHER', 'other_labels': ['C']}
        entry = dict(self.entry, labels=['Tdoc', 'Custom'], relationships=[first, second])
        snapshot = dict(self.snapshot, labels=['Custom', 'Tdoc'],
                        rels=[second, dict(first, other_labels=['A', 'B'])])
        tx = SimpleNamespace(run=lambda *args, **kwargs: SimpleNamespace(single=lambda: snapshot))
        prune._assert_prune_preimage(tx, entry)


if __name__ == '__main__':
    unittest.main()
