"""Phase arguments remain one path component in shared tree and import paths."""
from pathlib import Path
import unittest

from common import axis


class PhasePathTests(unittest.TestCase):
    def test_phase_paths_refuse_parent_and_absolute_paths(self):
        for phase in ('/tmp/outside', '../outside', '..', '.', '', ' ',
                      'phase-3/../../outside', 'phase-3\\outside', 'bad\x00name', -1, True, 1.5):
            with self.subTest(phase=repr(phase)):
                with self.assertRaises(axis.TreeGrammarError):
                    axis.tree_path('docs', wg='RAN1', phase=phase, root=Path('/repo'))
                with self.assertRaises(axis.TreeGrammarError):
                    axis.import_url('RAN1', phase, 'rows.json')

    def test_numeric_and_extension_phase_names_use_the_same_segment(self):
        for phase, segment in ((0, 'phase-0'), (11, 'phase-11'), ('phase-extension', 'phase-extension')):
            with self.subTest(phase=phase):
                path = axis.tree_path('docs', wg='RAN1', phase=phase, root=Path('/repo'))
                self.assertEqual(path, Path('/repo/docs/tsg/RAN/formal/RAN1') / segment)
                self.assertEqual(axis.import_url('RAN1', phase, 'rows.json'),
                                 f'file:///output/instances/{segment}/RAN1/rows.json')
                self.assertEqual(axis.tree_parse('docs', path, root=Path('/repo'))['phase'], segment)


if __name__ == '__main__':
    unittest.main()
