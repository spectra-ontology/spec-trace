"""Package relationships resolve to real parts without touching the filesystem."""
import io
import unittest
import zipfile

from common.docx_reader import MAIN_PART, read_zip_part, resolve_relationship_part


class RelationshipPartsTests(unittest.TestCase):
    def package(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as z:
            z.writestr('_rels/.rels', '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
                <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
                              Target="alternate/body.xml"/></Relationships>''')
            z.writestr('alternate/body.xml', '<actual/>')
            z.writestr('alternate/_rels/body.xml.rels', '<actual-relationships/>')
            z.writestr(MAIN_PART, '<unused/>')
            z.writestr('alternate/charts/one.xml', '<chart/>')
            z.writestr('word/media/a b.png', b'image')
        return zipfile.ZipFile(buffer)

    def test_relative_and_absolute_targets_use_the_relationship_source(self):
        with self.package() as z:
            for target, expected in (
                ('charts/one.xml', 'alternate/charts/one.xml'),
                ('/word/media/a%20b.png', 'word/media/a b.png'),
                ('../word/media/a%20b.png', 'word/media/a b.png'),
            ):
                with self.subTest(target=target):
                    self.assertEqual(resolve_relationship_part(z, target), expected)

    def test_external_missing_and_escaping_targets_have_no_member(self):
        with self.package() as z:
            for target in ('https://example.invalid/chart', '//example.invalid/chart',
                           '../../escape.xml', 'missing.xml', 'charts/one.xml#anchor'):
                with self.subTest(target=target):
                    self.assertIsNone(resolve_relationship_part(z, target))
            self.assertIsNone(resolve_relationship_part(z, 'charts/one.xml', target_mode='External'))

    def test_office_document_relationship_is_authoritative_over_unused_conventional_part(self):
        with self.package() as z:
            self.assertEqual(read_zip_part(z, MAIN_PART), b'<actual/>')
            self.assertEqual(read_zip_part(z, 'word/_rels/document.xml.rels'), b'<actual-relationships/>')


if __name__ == '__main__':
    unittest.main()
