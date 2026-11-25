"""Bind repair receipts to the synthetic JSON bytes actually parsed.

The maintained functions are extracted through AST; source documents, models,
databases and production imports are not accessed.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

COMMON = Path(__file__).resolve().parent


def actual_function(filename, name, env):
    path = COMMON / filename
    node = next(node for node in ast.parse(path.read_text()).body
                if isinstance(node, ast.FunctionDef) and node.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), env)
    return env[name]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class StoppedBeforeSources(Exception):
    pass


class InputReceiptGeneration(unittest.TestCase):
    def test_slide_receipt_hashes_parsed_proposal_even_if_path_changes(self):
        for changed in (False, True):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                proposal = root / 'proposal.json'
                original = b'{"collection":"ran5_tdoc_chunks","generation":"A"}'
                proposal.write_bytes(original)
                captured = {}

                def loads(raw):
                    value = json.loads(raw)
                    if changed:
                        proposal.write_bytes(b'{"collection":"ran5_tdoc_chunks","generation":"B"}')
                    return value

                def receipt(path, report):
                    captured.update(report)
                    raise StoppedBeforeSources

                env = dict(ROOT=root, json=NS(loads=loads), datetime=datetime,
                           timezone=timezone, sha=lambda path: digest(path.read_bytes()),
                           sha_bytes=digest, atomic_json=receipt)
                reconcile = actual_function('reconcile_pptx_search_text.py', 'reconcile', env)
                with self.assertRaises(StoppedBeforeSources):
                    reconcile(proposal, root / 'out')
                self.assertEqual(captured['proposalSHA256'], digest(original))
                fence = actual_function('reconcile_pptx_search_text.py', 'assert_fence', env)
                fences = {proposal.name: captured['proposalSHA256']}
                if changed:
                    with self.assertRaisesRegex(ValueError, 'fence changed'):
                        fence(fences)
                else:
                    fence(fences)

    def test_form_receipt_fence_uses_parsed_metadata_generation(self):
        for changed in (False, True):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                metadata = root / 'metadata.json'
                original = json.dumps(dict(mode='applied_exact_readback', wg='RAN4',
                    sourceFences={}, phase4DocumentsAfterSha256='synthetic')).encode()
                metadata.write_bytes(original)
                script = root / 'scripts/common/reconcile_tdoc_source_extensions.py'
                parser = root / 'scripts/tsg/RAN/formal/RAN4/phase-4/cr-parser/01_parse_cr_documents.py'
                loader = parser.parent.parent / 'neo4j/01_load_cr_ontology.py'
                files = [script, parser, loader, script.with_name('guarded.py'),
                         script.with_name('review_artifacts.py')]
                files += [script.with_name(name) for name in
                          ('tdoc_supplement_vectors.py', 'cr_form.py', 'docx_text.py')]
                for path in files:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text('synthetic')
                captured = {}

                def loads(raw):
                    value = json.loads(raw)
                    if changed:
                        metadata.write_bytes(original + b'\n')
                    return value

                def check_sources(fences):
                    captured.update(fences)
                    raise StoppedBeforeSources

                env = dict(ROOT=root, __file__=str(script), __doc__='synthetic',
                    argparse=argparse, Path=Path, json=NS(loads=loads), hashlib=hashlib,
                    guarded=NS(__file__=str(files[3])),
                    review_artifacts=NS(__file__=str(files[4])),
                    sha=lambda path: digest(path.read_bytes()), check_sources=check_sources)
                main = actual_function('reconcile_tdoc_source_extensions.py', 'main', env)
                argv = ['synthetic', '--wg', 'RAN4', '--metadata-receipt', str(metadata),
                        '--out', str(root / 'out.json')]
                with patch.object(sys, 'argv', argv), self.assertRaises(StoppedBeforeSources):
                    main()
                expected = captured[metadata.relative_to(root).as_posix()]
                self.assertEqual(expected, digest(original))
                self.assertEqual(digest(metadata.read_bytes()) == expected, not changed)

                def resolve(root, relative, expected):
                    if digest((root / relative).read_bytes()) != expected:
                        raise ValueError('synthetic generation mismatch')

                env['review_artifacts'].resolve_recorded_path = resolve
                fence = actual_function('reconcile_tdoc_source_extensions.py', 'check_sources', env)
                fences = {metadata.name: expected}
                if changed:
                    with self.assertRaisesRegex(ValueError, 'fence changed'):
                        fence(fences)
                else:
                    fence(fences)


if __name__ == '__main__':
    unittest.main()
