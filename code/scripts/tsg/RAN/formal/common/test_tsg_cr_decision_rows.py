"""Synthetic CR-sheet rows keep selected disposition and identity together."""
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from openpyxl import Workbook

import tsg_cr_decision as decisions


class SelectedSheetRows(unittest.TestCase):
    def setUp(self):
        decisions._lists.cache_clear()
        self.addCleanup(decisions._lists.cache_clear)

    def read_rows(self, rows):
        return self.read_books([(rows, True)])

    def read_books(self, books):
        with tempfile.TemporaryDirectory(prefix='spectra-tsg-decision-') as folder:
            archive = Path(folder) / 'synthetic.zip'
            lists = {}
            with ZipFile(archive, 'w') as target:
                for index, (rows, identity_header) in enumerate(books):
                    book = Workbook()
                    sheet = book.active
                    sheet.title = 'CRs_RAN_fixture'
                    header = ['Plenary doc', 'WG doc', 'TSG status']
                    if identity_header:
                        header += ['Spec', 'CR', 'Rev', 'REL']
                    sheet.append(header)
                    for status, spec, number, rev in rows:
                        row = ['RP-000001', 'R1-000001', status]
                        if identity_header:
                            row += [spec, number, rev, 'Rel-18']
                        sheet.append(row)
                    stream = io.BytesIO()
                    book.save(stream)
                    book.close()
                    member = f'TDoc_List_Meeting_RAN#99_fixture{index}.xlsx'
                    target.writestr(member, stream.getvalue())
                    lists[str(index)] = (archive, member)
            with patch.object(decisions, '_latest_lists', return_value=lists):
                return decisions._lists()

    def test_best_status_identity_is_independent_of_row_order(self):
        approved = ('approved', '38.000', '0007', '1')
        obsolete = ('reissued', '38.001', '0008', '2')
        for rows in ((approved, obsolete), (obsolete, approved)):
            with self.subTest(rows=rows):
                decisions._lists.cache_clear()
                pairs, _, _, identities = self.read_rows(rows)
                self.assertEqual(pairs[('RP-000001', 'R1-000001')][0], 'approved')
                self.assertEqual(identities[('RP-000001', 'R1-000001')],
                                 ('38.000', '0007', '1', 'Rel-18'))
                self.assertEqual(decisions.sheet_cr_label('CR9999', 'R1-000001', 'RP-000001'), 'CR0007r1')

    def test_equal_status_preserves_the_same_first_row_for_both_fields(self):
        rows = [('approved', '38.000', '0007', '1'), ('approved', '38.001', '0008', '2')]
        pairs, _, _, identities = self.read_rows(rows)
        self.assertEqual(pairs[('RP-000001', 'R1-000001')][0], 'approved')
        self.assertEqual(identities[('RP-000001', 'R1-000001')], ('38.000', '0007', '1', 'Rel-18'))

    def test_a_single_row_retains_the_existing_identity_contract(self):
        pairs, packs, _, identities = self.read_rows([('postponed', '38.000', '0007', '1')])
        self.assertEqual(pairs[('RP-000001', 'R1-000001')], ('postponed', 'RAN#99'))
        self.assertEqual(packs, frozenset({'RP-000001'}))
        self.assertEqual(identities[('RP-000001', 'R1-000001')], ('38.000', '0007', '1', 'Rel-18'))

    def test_selected_sheet_without_identity_clears_prior_sheet_identity(self):
        _, _, _, identities = self.read_books([
            ([('reissued', '38.000', '0007', '1')], True),
            ([('approved', '', '', '')], False),
        ])
        self.assertNotIn(('RP-000001', 'R1-000001'), identities)


if __name__ == '__main__':
    unittest.main()
