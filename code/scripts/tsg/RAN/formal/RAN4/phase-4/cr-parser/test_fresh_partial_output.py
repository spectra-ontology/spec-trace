"""The first resumable CR batch prepares its output directory on a new PC."""
import ast
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[7] / 'scripts' / 'common'))
from common.atomic_io import write_text_atomic

SOURCE = Path(__file__).with_name('02_parse_cr_documents.py')


class FreshPartialOutput(unittest.TestCase):
    def test_actual_batch_writer_creates_parent(self):
        node = next(n for n in ast.parse(SOURCE.read_text()).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'save_partial_results')
        @dataclass
        class Row:
            tdoc_number: str
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'new' / 'parsed'
            env = dict(OUTPUT_DIR=output, CRDocumentData=Row, asdict=asdict, json=json,
                       write_text_atomic=write_text_atomic)
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), 'exec'), env)
            result = env['save_partial_results']([Row('R4-1')], 0)
            self.assertEqual(json.loads(result.read_text()), [{'tdoc_number': 'R4-1'}])


if __name__ == '__main__':
    unittest.main()
