"""OOXML URI normalization preserves literal content and follows encoded targets.

Synthetic in-memory packages only; no corpus, database or network access.
"""
import io
from pathlib import Path
import tempfile
import unittest
import zipfile

from common import docx_reader as reader


class DocumentNamespaceTests(unittest.TestCase):
    def test_failed_strict_open_does_not_report_a_successful_conversion(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / 'broken.docx'
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('_rels/.rels', '<Relationships><Relationship '
                    'Type="http://purl.oclc.org/ooxml/officeDocument/relationships/officeDocument" '
                    'Target="missing.xml"/></Relationships>')
            before = reader.STATS.copy(); note = {}; raw = path.read_bytes()
            with self.assertRaises(KeyError):
                reader.open_document(path, note)
            self.assertEqual(reader.STATS, before)
            self.assertEqual(note, {})
            self.assertEqual(path.read_bytes(), raw)

    def test_successful_strict_open_records_conversion_and_preserves_original(self):
        from docx import Document
        data = io.BytesIO(); document = Document()
        document.add_paragraph('Synthetic source text'); document.save(data)
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / 'strict.docx'
            with zipfile.ZipFile(io.BytesIO(data.getvalue())) as source, zipfile.ZipFile(path, 'w') as target:
                for item in source.infolist():
                    raw = source.read(item)
                    if item.filename.endswith(('.xml', '.rels')):
                        raw = raw.replace(b'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
                                          b'http://purl.oclc.org/ooxml/wordprocessingml/main')
                        raw = raw.replace(b'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
                                          b'http://purl.oclc.org/ooxml/officeDocument/relationships')
                    target.writestr(item, raw)
            raw = path.read_bytes(); note = {}
            before = reader.STATS['이름을 맞춰 연 Strict 문서']
            opened = reader.open_document(path, note)
            self.assertEqual(opened.paragraphs[0].text, 'Synthetic source text')
            self.assertEqual(reader.STATS['이름을 맞춰 연 Strict 문서'], before + 1)
            self.assertTrue(note[reader.STRICT_NOTE_KEY])
            self.assertEqual(path.read_bytes(), raw)

    def test_only_actual_strict_uri_attributes_are_normalized(self):
        uri = b'http://purl.oclc.org/ooxml/wordprocessingml/main'
        literal = b'<!-- <w:t xmlns:w="' + uri + b'"/> -->'
        cdata = b'<![CDATA[<w:t xmlns:w="' + uri + b'"/>]]>'
        quoted = b" sample='literal xmlns:w=\"" + uri + b"\"'"
        data = literal + cdata + b'<w:t label="a > b"' + quoted + b' xmlns:w="' + uri + b'">' + uri + b'</w:t>'
        want = literal + cdata + b'<w:t label="a > b"' + quoted + b' xmlns:w="' + \
            b'http://schemas.openxmlformats.org/wordprocessingml/2006/main">' + uri + b'</w:t>'
        self.assertEqual(reader._to_transitional_names(data), want)

    def test_external_targets_and_non_uri_values_preserve_original_bytes(self):
        source = b'<Relationship Type="http://purl.oclc.org/ooxml/officeDocument/relationships/hyperlink" ' \
                 b'Target="http://purl.oclc.org/ooxml/document" label="prefix http://purl.oclc.org/ooxml/text"/>'
        self.assertEqual(reader._to_transitional_names(source), source.replace(
            b'http://purl.oclc.org/ooxml/officeDocument/relationships/hyperlink',
            b'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink'))

    def test_encoded_office_document_target_resolves_the_actual_part(self):
        package = io.BytesIO()
        with zipfile.ZipFile(package, 'w') as archive:
            archive.writestr('_rels/.rels', '<Relationships><Relationship '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
                'Target="/word/main%20body.xml"/></Relationships>')
            archive.writestr('word/main body.xml', '<body/>')
        package.seek(0)
        with zipfile.ZipFile(package) as archive:
            self.assertEqual(reader.main_part(archive), 'word/main body.xml')
            self.assertEqual(reader.read_zip_part(archive, reader.MAIN_PART), b'<body/>')


if __name__ == '__main__':
    unittest.main()
