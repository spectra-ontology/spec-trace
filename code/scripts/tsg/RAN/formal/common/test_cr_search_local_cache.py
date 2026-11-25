"""Small synthetic CR cache construction and first-use contracts; no DB/model/network."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import cr_hybrid_search as cache
import cr_search_adapter as adapter


class LocalCacheTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="spectra-cr-cache-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "chunks.json"
        self.cache_root = self.root / "cache"
        self.chunks = [
            {"chunkId": "c1", "tdocNumber": "SYNTHETIC-1", "chunkType": "header",
             "title": "Synthetic scheduling", "text": "Reason for change: scheduling",
             "specNumber": "00.000", "meeting": "SYNTHETIC#1"},
            {"chunkId": "c2", "tdocNumber": "SYNTHETIC-1", "chunkType": "body",
             "text": "synthetic payload witness", "specNumber": "00.000", "meeting": "SYNTHETIC#1"},
        ]
        self.write_source(self.chunks)

    def write_source(self, chunks):
        self.source.write_text(json.dumps({"chunks": chunks}), encoding="utf-8")
        self.spec = cache.CacheSpec("synthetic_cr", self.source, cache.sha256(self.source), self.cache_root)

    def cli(self, *extra):
        return [sys.executable, "-B", str(Path(cache.__file__).resolve()),
                "--collection", self.spec.collection_name, "--source", str(self.source),
                "--source-sha256", self.spec.source_sha256,
                "--expected-code-sha256", self.spec.code_sha256,
                "--cache-root", str(self.cache_root), "--receipt", str(self.root / "receipt.json"), *extra]

    def test_local_cache_build_open_filter_and_reuse_without_systemd(self):
        with patch.object(cache, "_build_guard", side_effect=AssertionError("unit guard called")):
            receipt = cache.build_cache(self.spec, build_mode="local-small")
            reused = cache.build_cache(self.spec, build_mode="local-small")
        self.assertEqual((receipt["chunks"], receipt["tdocs"], receipt["buildMode"]), (2, 1, "local-small"))
        self.assertTrue(reused["reused"])
        with cache.SearchCache(self.spec) as reader:
            features = reader.lexical_features("witness", {"chunkType": "body", "meeting": "SYNTHETIC#1"})
            self.assertEqual(features["positiveEvidenceDocuments"], 1)
            self.assertEqual(features["entries"][0]["matchedBodyChunkIds"], ["c2"])
            self.assertEqual(reader.lexical_features("witness", {"chunkType": "header"})["positiveEvidenceDocuments"], 0)
        self.assertFalse(list(self.cache_root.rglob("*.attempt_*.sqlite")))

    def test_default_build_still_requires_original_unit_guard(self):
        with patch.object(cache, "_build_guard", side_effect=cache.CacheError("unit required")) as guard:
            with self.assertRaisesRegex(cache.CacheError, "unit required"):
                cache.build_cache(self.spec)
        guard.assert_called_once_with()
        self.assertFalse(self.cache_root.exists())

    def test_unknown_mode_rejected_before_files_are_created(self):
        with self.assertRaisesRegex(ValueError, "Unknown"):
            cache.build_cache(self.spec, build_mode="unbounded")
        self.assertFalse(self.cache_root.exists())

    def test_source_size_bound_checked_before_hashing_or_creation(self):
        with self.source.open("r+b") as stream:
            stream.truncate(cache.LOCAL_SMALL_MAX_SOURCE_BYTES + 1)
        with patch.object(cache, "sha256", side_effect=AssertionError("must fail before hashing")):
            with self.assertRaisesRegex(cache.CacheError, "32 MiB"):
                cache.build_cache(self.spec, build_mode="local-small")
        self.assertFalse(self.cache_root.exists())

    def test_chunk_limit_rejects_entire_generation_and_preserves_failure_receipt(self):
        with patch.object(cache, "LOCAL_SMALL_MAX_CHUNKS", 1):
            with self.assertRaisesRegex(cache.CacheError, "no partial cache"):
                cache.build_cache(self.spec, build_mode="local-small")
        self.assertFalse(self.spec.path.exists())
        failures = list(self.cache_root.rglob("*.failed.json"))
        self.assertEqual(len(failures), 1)
        self.assertEqual(json.loads(failures[0].read_text())["chunksProcessed"], 1)

    def test_exact_chunk_limit_is_accepted(self):
        self.write_source(self.chunks[:1])
        with patch.object(cache, "LOCAL_SMALL_MAX_CHUNKS", 1):
            self.assertEqual(cache.build_cache(self.spec, build_mode="local-small")["chunks"], 1)

    def test_local_reuse_keeps_chunk_bound_for_a_unit_built_generation(self):
        with patch.object(cache, "_build_guard"):
            cache.build_cache(self.spec)
        with patch.object(cache, "LOCAL_SMALL_MAX_CHUNKS", 1):
            with self.assertRaisesRegex(cache.CacheError, "requires bounded-unit"):
                cache.build_cache(self.spec, build_mode="local-small")
        with cache.SearchCache(self.spec) as reader:
            self.assertEqual(reader.generation["chunks"], 2)

    def test_cli_creates_registry_then_actual_adapter_opens_it(self):
        manifest = self.cache_root / "source_manifest.json"
        result = subprocess.run(self.cli("--build-mode", "local-small", "--write-source-manifest", str(manifest)),
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        printed = json.loads(result.stdout)
        self.assertEqual((printed["chunks"], printed["tdocs"]), (2, 1))
        receipt = json.loads((self.root / "receipt.json").read_text())
        self.assertEqual(receipt["sourceManifest"], str(manifest))
        self.assertEqual(receipt["sourceManifestSha256"], cache.sha256(manifest))

        class Client:
            config = SimpleNamespace(collection_name=self.spec.collection_name,
                                     chunks_path=str(self.source), search_cache_root=str(self.cache_root))
        client = Client()
        opened = adapter._cache(client)
        self.assertEqual(opened.lexical_features("witness")["positiveEvidenceDocuments"], 1)
        self.assertIs(adapter._cache(client), opened)
        self.assertFalse(list(self.cache_root.glob("*.tmp")))

    def test_cli_default_requires_unit(self):
        result = subprocess.run(self.cli(), text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 2)
        self.assertIn("--unit is required", result.stderr)
        self.assertFalse(self.cache_root.exists())

    def test_cli_existing_registry_is_preserved_before_build(self):
        manifest = self.root / "existing.json"
        original = b'{"operator":"preserve these bytes"}'
        manifest.write_bytes(original)
        result = subprocess.run(self.cli("--build-mode", "local-small", "--write-source-manifest", str(manifest)),
                                text=True, capture_output=True, timeout=20)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(manifest.read_bytes(), original)
        self.assertFalse(self.cache_root.exists())

    def test_racing_registry_creation_preserves_operator_file_and_cleans_temp(self):
        manifest = self.root / "registry.json"
        original = b'{"operator":"concurrent"}'
        real_link = cache.os.link

        def create_then_link(source, target, **kwargs):
            Path(target).write_bytes(original)
            return real_link(source, target, **kwargs)

        with patch.object(cache.os, "link", side_effect=create_then_link):
            with self.assertRaises(FileExistsError):
                cache._publish_source_manifest(manifest, self.spec)
        self.assertEqual(manifest.read_bytes(), original)
        self.assertFalse(list(self.root.glob("*.tmp")))

    def test_colliding_temporary_name_preserves_foreign_bytes(self):
        manifest = self.root / "registry.json"
        temporary = self.root / "registry.json.fixed.tmp"
        temporary.write_bytes(b"foreign temporary file")
        with patch.object(cache.uuid, "uuid4", return_value=SimpleNamespace(hex="fixed")):
            with self.assertRaises(FileExistsError):
                cache._publish_source_manifest(manifest, self.spec)
        self.assertEqual(temporary.read_bytes(), b"foreign temporary file")
        self.assertFalse(manifest.exists())


if __name__ == "__main__":
    unittest.main()
