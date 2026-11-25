"""Check length-based progress and all WG hooks without models or databases.

Spec: docs/common/process/internal_embedding_guide.md.
Cycle: synthetic selected input → production timing hooks → observed counters.
LLM calls: 0. Network access: 0. Model and database calls are synthetic.
"""
from __future__ import annotations

import ast
from contextlib import redirect_stdout
import hashlib
import io
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from embedding_progress import EmbeddingProgress

ROOT = next(path for path in Path(__file__).resolve().parents if (path / ".git").exists())


class Clock:
    value = 0.0

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


def tracker(texts, *, existing=()):
    clock = Clock()
    chunks = [{"id": index, "text": text} for index, text in enumerate(texts)]
    progress = EmbeddingProgress(chunks, existing_ids=set(existing), point_id=lambda row: row["id"],
                                 text_of=lambda row: row["text"], clock=clock)
    return progress, clock


class EmbeddingProgressTests(unittest.TestCase):
    def test_uneven_lengths_use_observed_characters_and_exclude_initialization_and_upload(self):
        progress, clock = tracker(["a" * 10, "b" * 90])
        def initialize():
            clock.advance(7)
        def encode():
            clock.advance(1)
            return [[1.0]]
        progress.embed(["a" * 10], encode, initialize=initialize)
        def upload():
            clock.advance(100)
        progress.upload([object()], upload)
        report = progress.snapshot()
        self.assertEqual(report["eta_embedding_seconds"], 9)
        self.assertEqual(report["remaining_characters"], 90)
        self.assertEqual(report["initialization_seconds"], 7)
        self.assertEqual(report["embedding_seconds"], 1)
        self.assertEqual(report["upload_seconds"], 100)
        self.assertEqual(report["eta_basis"], "character_length_proportional")

    def test_resumed_and_empty_chunks_are_excluded_from_pending_input(self):
        progress, _ = tracker(["large resumed text", "  ", "ready"], existing=(0,))
        report = progress.snapshot()
        self.assertEqual((report["total_chunks"], report["resumed_chunks"], report["empty_chunks"]), (3, 1, 1))
        self.assertEqual((report["pending_chunks"], report["pending_characters"]), (1, 5))
        self.assertIsNone(report["eta_embedding_seconds"])
        self.assertEqual(report["eta_basis"], "embedding_observation_pending")

    def test_no_pending_input_has_no_remaining_embedding_work(self):
        progress, _ = tracker(["resumed", ""], existing=(0,))
        self.assertEqual(progress.snapshot()["eta_embedding_seconds"], 0)
        self.assertIsNone(progress.snapshot()["initialization_seconds"])

    def test_missing_vectors_are_failed_and_eta_requires_review(self):
        progress, clock = tracker(["first", "second", "pending"])
        def encode():
            clock.advance(2)
            return [[1.0], None]
        progress.embed(["first", "second"], encode, initialize=lambda: None)
        report = progress.snapshot()
        self.assertEqual((report["attempted_chunks"], report["embedded_chunks"], report["failed_chunks"]), (2, 1, 1))
        self.assertEqual(report["uploaded_chunks"], 0)
        self.assertIsNone(report["eta_embedding_seconds"])
        self.assertEqual(report["eta_basis"], "failure_requires_review")

    def test_embedding_exception_keeps_failure_and_original_exception(self):
        progress, clock = tracker(["body"])
        error = RuntimeError("synthetic embedding failure")
        def encode():
            clock.advance(3)
            raise error
        with self.assertRaises(RuntimeError) as raised:
            progress.embed(["body"], encode, initialize=lambda: None)
        self.assertIs(raised.exception, error)
        self.assertEqual(progress.snapshot()["failed_chunks"], 1)
        self.assertEqual(progress.snapshot()["embedded_chunks"], 0)
        self.assertEqual(progress.snapshot()["embedding_seconds"], 3)
        self.assertIsNone(progress.snapshot()["eta_embedding_seconds"])

    def test_upload_exception_counts_no_uploaded_success(self):
        progress, clock = tracker(["body"])
        def upload():
            clock.advance(4)
            raise RuntimeError("synthetic upload failure")
        with self.assertRaises(RuntimeError):
            progress.upload([object()], upload)
        report = progress.snapshot()
        self.assertEqual(report["uploaded_chunks"], 0)
        self.assertTrue(report["upload_failed"])
        self.assertEqual(report["upload_seconds"], 4)
        self.assertIsNone(report["eta_embedding_seconds"])

    def test_model_initialization_failure_is_reported_before_any_embedding(self):
        progress, clock = tracker(["body"])
        encode = Mock()
        def initialize():
            clock.advance(5)
            raise RuntimeError("synthetic model initialization failure")
        with self.assertRaises(RuntimeError):
            progress.embed(["body"], encode, initialize=initialize)
        encode.assert_not_called()
        report = progress.snapshot()
        self.assertTrue(report["initialization_failed"])
        self.assertEqual(report["initialization_seconds"], 5)
        self.assertEqual(report["attempted_chunks"], 0)
        self.assertIsNone(report["eta_embedding_seconds"])

    def test_initialization_runs_once_and_final_partial_batch_is_accounted(self):
        progress, clock = tracker(["a", "bb"])
        initialize = Mock(side_effect=lambda: clock.advance(8))
        for text in ("a", "bb"):
            def encode():
                clock.advance(len(text))
                return [[1.0]]
            progress.embed([text], encode, initialize=initialize)
            progress.upload([object()], lambda: None)
        initialize.assert_called_once_with()
        report = progress.snapshot()
        self.assertEqual(report["input_characters"], 3)
        self.assertEqual(report["uploaded_chunks"], 2)
        self.assertEqual(report["eta_embedding_seconds"], 0)

    def test_first_rest_keeps_initialization_time_and_eta_uses_embedding_only(self):
        progress, clock = tracker(["a" * 10, "b" * 90])
        rests = []
        def initialize():
            clock.advance(7)
        def encode():
            clock.advance(1)
            return [[1.0]]
        def rested(call):
            started = clock()
            result = call()
            rests.append((clock() - started) * 0.5)
            clock.advance(rests[-1])
            return result
        progress.embed(["a" * 10], encode, initialize=initialize, around=rested, rest_ratio=0.5)
        report = progress.snapshot()
        self.assertEqual(rests, [4])
        self.assertEqual(report["initialization_seconds"], 7)
        self.assertEqual(report["embedding_seconds"], 1)
        self.assertEqual(report["rest_seconds"], 4)
        self.assertEqual(report["eta_embedding_seconds"], 13.5)

    def test_interrupted_rest_preserves_successful_embedding_and_marks_cycle_failure(self):
        progress, clock = tracker(["body"])
        error = KeyboardInterrupt()
        def encode():
            clock.advance(1)
            return [[1.0]]
        def interrupted(call):
            call()
            clock.advance(0.2)
            raise error
        with self.assertRaises(KeyboardInterrupt) as raised:
            progress.embed(["body"], encode, initialize=lambda: None, around=interrupted)
        self.assertIs(raised.exception, error)
        report = progress.snapshot()
        self.assertEqual(report["embedded_chunks"], 1)
        self.assertEqual(report["uploaded_chunks"], 0)
        self.assertTrue(report["embedding_cycle_failed"])
        self.assertIsNone(report["eta_embedding_seconds"])

    def test_all_wg_production_hooks_preserve_input_and_resume_identity(self):
        for wg in range(1, 6):
            with self.subTest(wg=wg):
                clock, trackers, encoded = Clock(), [], []
                chunks = []
                for index, text in enumerate(("resumed", "  ", "a" * 10, "b" * 90)):
                    chunk = dict(chunkId=f"fixture-{index}", text=text, specNumber="fixture-spec",
                                 chunkIndex=index, level=1, sectionId=f"section-{index}", sectionNumber=str(index),
                                 sectionTitle="fixture", totalChunks=4, isAnnex=False, hasTables=False, hasFigures=False)
                    if wg == 5 and index == 3:
                        chunk["content"] = chunk.pop("text")
                    chunks.append(chunk)
                class Progress(EmbeddingProgress):
                    def __init__(self, *args, **kwargs):
                        super().__init__(*args, clock=clock, **kwargs)
                        trackers.append(self)
                def encode(encoder, texts, **kwargs):
                    encoded.extend(texts)
                    clock.advance(sum(map(len, texts)) / 10)
                    return [[1.0] for _ in texts]
                class Manager:
                    def __init__(self, config):
                        self.points = []
                    def get_collection_info(self):
                        return {"points_count": 1 + len(self.points)}
                    def existing_point_ids(self, ids):
                        return {ids[0]}
                    def create_collection(self, **kwargs):
                        pass
                    def upsert_points(self, points):
                        clock.advance(100)
                        self.points.extend(points)
                namespace = dict(hashlib=hashlib, time=SimpleNamespace(time=clock), EmbeddingProgress=Progress,
                                 load_all_chunks=lambda *args, **kwargs: chunks, local_encoder_for=lambda name: None,
                                 load_local_encoder=lambda encoder: clock.advance(7), embed_local=encode,
                                 rested=lambda fn, *args, **kwargs: fn(*args, **kwargs), REST=0.0, QdrantManager=Manager,
                                 PointStruct=lambda **kwargs: SimpleNamespace(**kwargs), count_tokens=len)
                path = ROOT / f"scripts/tsg/RAN/formal/RAN{wg}/phase-7/qdrant/01_load_qdrant.py"
                selected = []
                for node in ast.parse(path.read_text()).body:
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in (
                        "EmbeddingClient", "generate_point_id", "_accept_chunks", "process_batch", "load_to_qdrant"):
                        node.decorator_list = []
                        selected.append(node)
                module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
                                          *selected], type_ignores=[])
                exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)
                config = SimpleNamespace(collection_name=f"ran{wg}_ts_sections", parsed_base=Path("fixture"),
                                         embedding_model="fixture-model", embedding_dim=1, batch_size=1, encode_batch_size=1,
                                         encoder=SimpleNamespace(provider="local"))
                with redirect_stdout(io.StringIO()):
                    result = namespace["load_to_qdrant"](config, resume=True)
                self.assertEqual(result, 0)
                self.assertEqual(encoded, ["a" * 10, "b" * 90])
                report = trackers[0].snapshot()
                self.assertEqual((report["resumed_chunks"], report["empty_chunks"], report["uploaded_chunks"]), (1, 1, 2))
                self.assertEqual(report["initialization_seconds"], 7)
                self.assertEqual(report["embedding_seconds"], 10)
                self.assertEqual(report["upload_seconds"], 200)
                self.assertEqual(report["remaining_characters"], 0)


if __name__ == "__main__":
    unittest.main()
