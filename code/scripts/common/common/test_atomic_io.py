#!/usr/bin/env python3
"""공유 파일 writer의 기존 파일 보존·권한·실패 정리 계약을 검사한다."""
import json
import shutil
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
import threading
from contextlib import contextmanager

import atomic_io


class AtomicJsonTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="spectra-json-publication-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / "receipt.json"
        self.path.write_bytes(b'{"previous":true}\n')
        self.path.chmod(0o640)
        self.before = self.path.read_bytes()

    def test_roundtrip_unicode_and_existing_mode(self):
        atomic_io.write_json_atomic(self.path, {"text": "본문\n", "values": [None, 0, True]})
        self.assertEqual(json.loads(self.path.read_text()), {"text": "본문\n", "values": [None, 0, True]})
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o640)
        self.assertEqual(list(self.root.iterdir()), [self.path])

    def test_invalid_values_and_failed_fsync_or_replace_preserve_original(self):
        for value in (object(), float("nan"), float("inf"), -float("inf")):
            with self.subTest(value=type(value).__name__), self.assertRaises((ValueError, TypeError)):
                atomic_io.write_json_atomic(self.path, {"bad": value})
            self.assertEqual(self.path.read_bytes(), self.before)
        for operation in ("fsync", "replace"):
            with self.subTest(operation=operation), patch.object(
                    atomic_io.os, operation, side_effect=OSError("synthetic failure")), self.assertRaises(OSError):
                atomic_io.write_json_atomic(self.path, {"new": True})
            self.assertEqual(self.path.read_bytes(), self.before)
            self.assertEqual(list(self.root.iterdir()), [self.path])

    def test_parent_creation_remains_callers_responsibility_and_new_file_is_private(self):
        target = self.root / "missing/receipt.json"
        with self.assertRaises(FileNotFoundError):
            atomic_io.write_json_atomic(target, {"new": True})
        self.assertFalse(target.parent.exists())
        target = self.root / "new.json"
        atomic_io.write_json_atomic(target, {"new": True})
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)

    def test_existing_and_dangling_symlinks_are_preserved(self):
        for target in (self.path, self.root / "absent.json"):
            link = self.root / "link.json"
            link.symlink_to(target)
            with self.subTest(target=target), self.assertRaisesRegex(ValueError, "심볼릭 링크"):
                atomic_io.write_json_atomic(link, {"new": True})
            self.assertTrue(link.is_symlink())
            self.assertEqual(self.path.read_bytes(), self.before)
            link.unlink()


class ExclusivePublicationTests(unittest.TestCase):
    def test_new_text_and_json_publish_complete_private_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            text, record = root/'answer.txt', root/'record.json'
            atomic_io.write_text_atomic(text, '본문\n', overwrite=False)
            atomic_io.write_json_atomic(record, {'answer': '본문'}, mode=0o640, overwrite=False)
            self.assertEqual(text.read_text(), '본문\n')
            self.assertEqual(text.stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(record.read_text()), {'answer': '본문'})
            self.assertEqual(record.stat().st_mode & 0o777, 0o640)
            self.assertEqual(set(root.iterdir()), {text, record})

    def test_failed_write_fsync_link_and_interruption_leave_retryable_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root/'new.txt'
            # Encoding fails during the actual temporary stream write.
            with self.assertRaises(UnicodeEncodeError):
                atomic_io.write_text_atomic(path, 'partial\ud800', overwrite=False)
            self.assertEqual(list(root.iterdir()), [])
            named_temporary = atomic_io.tempfile.NamedTemporaryFile
            @contextmanager
            def failed_stream(**kwargs):
                with named_temporary(**kwargs) as stream:
                    write = stream.write
                    def partial_write(text):
                        write(text[:3])
                        stream.flush()
                        raise OSError('partial temporary write')
                    with patch.object(stream, 'write', side_effect=partial_write):
                        yield stream
            with patch.object(atomic_io.tempfile, 'NamedTemporaryFile', failed_stream), self.assertRaises(OSError):
                atomic_io.write_text_atomic(path, 'complete', overwrite=False)
            self.assertEqual(list(root.iterdir()), [])
            for operation, error in [('fsync', OSError('sync failed')),
                                     ('link', OSError('link failed')),
                                     ('fsync', KeyboardInterrupt('interrupted'))]:
                with self.subTest(operation=operation, error=type(error).__name__), \
                        patch.object(atomic_io.os, operation, side_effect=error), \
                        self.assertRaises(type(error)):
                    atomic_io.write_text_atomic(path, 'complete', overwrite=False)
                self.assertEqual(list(root.iterdir()), [])
            atomic_io.write_text_atomic(path, 'complete', overwrite=False)
            self.assertEqual(path.read_text(), 'complete')

    def test_existing_files_symlinks_and_same_target_remain_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root/'existing'
            path.write_bytes(b'original')
            path.chmod(0o640)
            inode = path.stat().st_ino
            for target in (path, root/'link', root/'dangling'):
                if target.name == 'link':
                    target.symlink_to(path)
                elif target.name == 'dangling':
                    target.symlink_to(root/'absent')
                for content in ('replacement', 'original'):
                    with self.subTest(target=target, content=content), self.assertRaises(FileExistsError):
                        atomic_io.write_text_atomic(target, content, overwrite=False)
                if target != path:
                    self.assertTrue(target.is_symlink())
            self.assertEqual(path.read_bytes(), b'original')
            self.assertEqual(path.stat().st_ino, inode)
            self.assertEqual(path.stat().st_mode & 0o777, 0o640)
            self.assertEqual({p.name for p in root.iterdir()}, {'existing', 'link', 'dangling'})

    def test_racing_writers_publish_one_complete_result_without_clobber(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root/'result.txt'
            barrier = threading.Barrier(2)
            link = atomic_io.os.link
            def racing_link(source, destination):
                barrier.wait(timeout=5)
                return link(source, destination)
            def publish(text):
                try:
                    atomic_io.write_text_atomic(path, text, overwrite=False)
                    return 'published', text
                except FileExistsError:
                    return 'exists', text
            with patch.object(atomic_io.os, 'link', side_effect=racing_link), ThreadPoolExecutor(2) as pool:
                results = list(pool.map(publish, ['first complete result', 'second complete result']))
            self.assertEqual(sorted(status for status, _ in results), ['exists', 'published'])
            winner = next(text for status, text in results if status == 'published')
            self.assertEqual(path.read_text(), winner)
            self.assertEqual(list(root.iterdir()), [path])


class AtomicCopyTests(unittest.TestCase):
    def test_copy_metadata_and_interrupted_copy_preserve_previous_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, destination = root / "source.docx", root / "destination.docx"
            source.write_bytes(b"complete new document")
            source.chmod(0o640)
            destination.write_bytes(b"previous document")
            def interrupted(src, tmp):
                Path(tmp).write_bytes(b"partial")
                raise KeyboardInterrupt("synthetic interrupted copy")
            with patch.object(atomic_io.shutil, "copy2", interrupted), self.assertRaises(KeyboardInterrupt):
                atomic_io.copy_file_atomic(source, destination)
            self.assertEqual(destination.read_bytes(), b"previous document")
            self.assertEqual(set(root.iterdir()), {source, destination})
            atomic_io.copy_file_atomic(source, destination)
            self.assertEqual(destination.read_bytes(), source.read_bytes())
            self.assertEqual(destination.stat().st_mode & 0o777, 0o640)
            self.assertEqual(destination.stat().st_mtime_ns, source.stat().st_mtime_ns)
            self.assertEqual(set(root.iterdir()), {source, destination})

    def test_symlinks_and_same_file_preserve_original(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source"; source.write_bytes(b"original")
            with self.assertRaises(shutil.SameFileError):
                atomic_io.copy_file_atomic(source, source)
            hardlink = root / "hardlink"; hardlink.hardlink_to(source)
            with self.assertRaises(shutil.SameFileError):
                atomic_io.copy_file_atomic(source, hardlink)
            link = root / "symlink"; link.symlink_to(source)
            with self.assertRaisesRegex(ValueError, "심볼릭 링크"):
                atomic_io.copy_file_atomic(source, link)
            self.assertTrue(link.is_symlink())
            self.assertEqual(source.read_bytes(), b"original")


class WriterLockTests(unittest.TestCase):
    def test_competitor_refuses_and_lock_inode_survives_release(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            lock = root / "logs/common/verification/writer-locks/shared.lock"
            with atomic_io.repository_writer_lock(root, "shared"):
                inode = lock.stat().st_ino
                with self.assertRaises(BlockingIOError):
                    with atomic_io.repository_writer_lock(root, "shared"):
                        self.fail("competing lock entered")
            with atomic_io.repository_writer_lock(root, "shared"):
                self.assertEqual(lock.stat().st_ino, inode)

    def test_symlink_parent_and_leaf_preserve_target_without_creating_files(self):
        for parent in (True, False):
            with self.subTest(parent=parent), tempfile.TemporaryDirectory() as folder:
                root = Path(folder) / "repo"
                root.mkdir()
                target = Path(folder) / "retained"
                target.mkdir()
                sentinel = target / "sentinel"
                sentinel.write_bytes(b"retained")
                if parent:
                    (root / "logs").symlink_to(target, target_is_directory=True)
                else:
                    lock = root / "logs/common/verification/writer-locks/shared.lock"
                    lock.parent.mkdir(parents=True)
                    lock.symlink_to(sentinel)
                with self.assertRaises(ValueError):
                    with atomic_io.repository_writer_lock(root, "shared"):
                        self.fail("symlink lock entered")
                self.assertEqual(sentinel.read_bytes(), b"retained")
                self.assertEqual(list(target.iterdir()), [sentinel])



if __name__ == "__main__":
    unittest.main(verbosity=2)
