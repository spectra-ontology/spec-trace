#!/usr/bin/env python3
"""Check preprocessing fidelity, source identities, model pins and isolated targets."""
import argparse
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from build_dense_collections import build, checked_snapshot, prepare_document, sha, sqlite_rows, target_name


class BuilderTests(unittest.TestCase):
    def test_preprocessing_preserves_declared_full_and_incremental_paths(self):
        self.assertEqual(prepare_document("ran1_tdoc_chunks", " x \n", "full"), " x \n")
        self.assertEqual(prepare_document("ran1_tdoc_chunks", " x \n", "incremental"), "x")
        self.assertEqual(prepare_document("ran1_cr_chunks", " x \n", "full"), "x")
        self.assertEqual(prepare_document("ran1_resolution_chunks", " x \n", "full"), " x \n")

    def test_operational_names_and_unsupported_sources_are_rejected(self):
        self.assertEqual(target_name("rebuild_check_", "ran1_cr_chunks"), "rebuild_check_ran1_cr_chunks")
        for prefix in ("ran1_", "production_", "rebuild_../", "rebuild_BAD_"):
            with self.assertRaises(ValueError):
                target_name(prefix, "ran1_cr_chunks")
        with self.assertRaises(ValueError):
            target_name("rebuild_check_", "ran1_email_chunks")

    def test_sqlite_rows_preserve_uint64_ids_content_and_metadata(self):
        db = sqlite3.connect(":memory:")
        db.execute("CREATE TABLE docs(collection,point_id,chunk_id,text,meta)")
        db.executemany("INSERT INTO docs VALUES(?,?,?,?,?)", [
            ("ran1_cr_chunks", "18446744073709551614", "a", " \nx ", '{"meeting":"RAN1#1"}'),
            ("ran1_cr_chunks", "1", "b", "   ", '{}'),
            ("ran1_cr_chunks", "2", "c", "y", '{}')])
        rows = list(sqlite_rows(db, "ran1_cr_chunks", 1))
        self.assertEqual(rows, [(18446744073709551614, "a", " \nx ", {"meeting": "RAN1#1"})])
        self.assertEqual(len(list(sqlite_rows(db, "ran1_cr_chunks", 0))), 2)
        db.close()

    def test_changed_model_file_fails_before_loading(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "model.bin"
            path.write_bytes(b"fixed")
            contract = {"model": {"files": {"model.bin": {"sha256": sha(b"fixed"), "bytes": 5}}}}
            self.assertEqual(checked_snapshot(Path(folder), contract)["model.bin"], sha(b"fixed"))
            path.write_bytes(b"other")
            with self.assertRaisesRegex(ValueError, "Pinned model file differs"):
                checked_snapshot(Path(folder), contract)

    def test_reused_output_is_rejected_before_model_or_source_access(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "existing").write_text("evidence")
            with self.assertRaisesRegex(ValueError, "new or empty"):
                build(argparse.Namespace(out=Path(folder)))


if __name__ == "__main__":
    unittest.main()
