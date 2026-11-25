#!/usr/bin/env python3
"""test_embedding_cardinality.py — 임베딩 누락 시 세대 교체 차단을 검증한다.

Spec: E-2/E-3 및 TR Phase-9 입력·벡터 일대일 계약.
Ontology: 기존 청크 ID·payload·세대 교체 규칙을 유지한다.
Cycle: 실제 적재 함수 → 짧거나 긴 합성 벡터 반환 → 쓰기·승격 여부 검사.
배경: zip의 짧은 순회로 사라진 청크를 성공 처리하지 않는다.
사용: python3 -B scripts/tsg/RAN/formal/common/test_embedding_cardinality.py
LLM 호출·DB·모델·네트워크: 없음. 메모리 임베더와 Qdrant 대역만 사용한다.
"""
import ast
import contextlib
import functools
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())


def email_loader(wg):
    """Import the real WG entry point without running its CLI or opening clients."""
    path = ROOT / f"scripts/tsg/RAN/email/RAN{wg}/phase-2/qdrant/01_load_email_chunks.py"
    spec = importlib.util.spec_from_file_location(f"email_vectors_test_ran{wg}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EmbeddingCardinalityTests(unittest.TestCase):
    def test_staging_cleanup_preserves_original_failure_and_owned_scope(self):
        paths = [ROOT / f"scripts/tsg/RAN/formal/RAN{wg}/phase-{phase}/qdrant/{name}"
                 for wg in range(1, 6)
                 for phase, name in ((6, "02_load_qdrant.py"), (7, "01_load_qdrant.py"),
                                     (8, "01_load_qdrant.py"), (9, "01_load_qdrant.py"))]
        paths.append(ROOT / "scripts/tsg/RAN/formal/TSG_RAN/phase-9/qdrant/01_load_qdrant.py")
        for path in paths:
            node = next(n for n in ast.parse(path.read_text()).body
                        if isinstance(n, ast.FunctionDef) and n.name == "_abandon_staging_on_error")
            for original_type in (RuntimeError, SystemExit, KeyboardInterrupt):
                for cleanup_type in (None, RuntimeError, SystemExit, KeyboardInterrupt):
                    for broken_output in (False, True):
                        with self.subTest(path=str(path), original=original_type.__name__,
                                          cleanup=cleanup_type, broken_output=broken_output):
                            events = []
                            foreign = types.SimpleNamespace(name="foreign", abandon_replace=lambda: events.append("foreign"),
                                                            close=lambda: self.fail("foreign client must stay open"))
                            def abandon():
                                events.append("first")
                                if cleanup_type:
                                    raise cleanup_type("synthetic cleanup failure")
                            first = types.SimpleNamespace(name="first", abandon_replace=abandon, close=lambda: None)
                            second = types.SimpleNamespace(name="second", abandon_replace=lambda: events.append("second"), close=lambda: None)
                            opened = [foreign]
                            def diagnostic(*args, **kwargs):
                                if broken_output:
                                    raise BrokenPipeError("synthetic diagnostic failure")
                            env = {"functools": functools, "sys": sys, "_STAGING_OPEN": opened, "print": diagnostic}
                            exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), env)
                            original = original_type("synthetic load failure")
                            def load():
                                opened.extend((first, second))
                                raise original
                            with self.assertRaises(BaseException) as caught:
                                env["_abandon_staging_on_error"](load)()
                            self.assertIs(caught.exception, original)
                            self.assertEqual(events, ["first", "second"])
                            self.assertEqual(opened, [foreign])
            events, opened = [], []
            env = {"functools": functools, "sys": sys, "_STAGING_OPEN": opened}
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), env)
            def successful_load():
                opened.append(types.SimpleNamespace(abandon_replace=lambda: events.append("abandoned"), close=lambda: None))
                return "completed"
            self.assertEqual(env["_abandon_staging_on_error"](successful_load)(), "completed")
            self.assertEqual((events, opened), ([], []))

    def test_email_replacement_rejects_short_or_long_vectors(self):
        for wg in range(1, 6):
            production = email_loader(wg)
            # Resolution now uses common.resolution_vectors; its public loaders,
            # short/long embedding batches and positive-coverage fence are
            # exercised in scripts/common/ontology/test_resolution_vectors.py.
            for phase, filename in ((2, "01_load_email_chunks.py"),):
                for returned in (1, 3):
                    with self.subTest(wg=wg, phase=phase, returned=returned), tempfile.TemporaryDirectory() as td:
                        events = []
                        class Qdrant:
                            mode = "fixture"
                            client = types.SimpleNamespace(close=lambda: None)
                            def abandon_replace(self):
                                pass
                            def open_target(self, **kwargs):
                                events.append("open")
                            def upsert(self, points):
                                events.append("upsert")
                            def finish_replace(self, ids):
                                events.append("finish")
                        class Embedder:
                            def embed_texts(self, texts):
                                return [[0.1]] * returned
                        inp = Path(td) / "threads.jsonl"
                        inp.write_text(json.dumps({"wg": f"RAN{wg}", "thread_key": "t", "messages": [{"body_original": "a", "body_original_len": 1, "sender_raw": "Synthetic", "msg_id": "m", "index": 0}]}) + "\n")
                        hooks = {"_ROOT": Path(td), "load_dotenv": lambda *a, **kw: None,
                               "JSONL": inp, "COLLECTION": "fixture", "BATCH": 128, "QdrantManager": Qdrant,
                               "EmbeddingClient": Embedder, "thread_anchor_fields": lambda d: ([], [], []),
                               "message_chunks": lambda *a: [("m#0", "a", {"tokenCount": 1}), ("m#1", "b", {"tokenCount": 1})],
                               "message_identity": types.SimpleNamespace(assert_unique=lambda *a: None, message_key=lambda *a: "m", thread_hash=lambda x: x)}
                        models = types.ModuleType("qdrant_client.http.models")
                        models.PointStruct = lambda **kwargs: types.SimpleNamespace(**kwargs)
                        # 실제 진입점과 공통 엔진을 함께 실행하고 외부 입출력만 대체한다.
                        with patch.multiple(production, **hooks), \
                                patch.dict(sys.modules, {"qdrant_client.http.models": models}), \
                                contextlib.redirect_stdout(io.StringIO()):
                            with self.assertRaisesRegex(RuntimeError, "cardinality mismatch"):
                                production.run(estimate=False, recreate=True)
                        self.assertEqual(events, ["open"])

    def test_formal_batch_rejects_missing_vector_before_payload_access(self):
        paths = [ROOT / "scripts/tsg/RAN/formal/TSG_RAN/phase-9/qdrant/01_load_qdrant.py",
                 ROOT / "scripts/tsg/RAN/formal/RAN3/phase-6/qdrant/02_load_qdrant.py",
                 ROOT / "scripts/tsg/RAN/formal/RAN2/phase-6/qdrant/02_load_qdrant.py"]
        for path in paths:
            node = next(n for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == "process_batch")
            env = {"EmbeddingClient": object, "PointStruct": object}
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), env)
            for vectors in ([], [[0.1]], [[0.1]] * 3):
                with self.subTest(vectors=len(vectors)), self.assertRaisesRegex(RuntimeError, "cardinality mismatch"):
                    env["process_batch"](types.SimpleNamespace(embed_texts=lambda texts: vectors), ["a", "b"], [{}, {}])
            with self.assertRaises(ValueError):
                env["process_batch"](None, ["a"], [{}, {}])


class EmailVectorContractTests(unittest.TestCase):
    def test_public_projection_keeps_payload_and_live_hooks(self):
        keys = ["chunkId", "messageId", "messageIndex", "threadKey", "senderKey",
                "archiveCode", "sentDate", "roundNum", "subject", "chunkIndex",
                "totalChunks", "text", "textSha256", "tokenCount", "specAnchors",
                "meetingAnchors", "bracketIds"]
        for wg in range(1, 6):
            with self.subTest(wg=wg):
                loader = email_loader(wg)
                events = []
                def first_key(mid, index):
                    events.append(("key", index))
                    loader.message_identity.chunk_key = lambda m, i: f"later:{m}#{i}"
                    return f"first:{mid}#{index}"
                def first_sha(text):
                    events.append(("sha", text))
                    loader.text_sha = lambda value: "later:" + value
                    loader.count_tokens = lambda value: 100 + len(value)
                    return "first:" + text
                loader.message_identity.chunk_key = first_key
                loader.text_sha = first_sha
                loader.count_tokens = lambda value: self.fail("token hook looked up too early")
                loader.split_giant_section_v2 = lambda values, **kw: ["alpha", "beta"]
                loader.enforce_hard_max = lambda chunks, **kw: chunks
                anchors = (["38.331"], ["meeting"], ["id"])
                message = {"msg_id": "m", "body_original": "body", "sender_raw": '"Alice" <a@b>',
                           "index": 2, "archive_code": "archive", "date_parsed": "date",
                           "round_num": 3, "subject": "subject"}
                rows = loader.message_chunks("thread", message, anchors)
                mid = loader.message_identity.message_key("thread", "m")
                self.assertEqual([row[0] for row in rows], [f"first:{mid}#0", f"later:{mid}#1"])
                self.assertEqual([row[2]["textSha256"] for row in rows], ["first:alpha", "later:beta"])
                self.assertEqual([row[2]["tokenCount"] for row in rows], [105, 104])
                self.assertEqual(events, [("key", 0), ("sha", "alpha")])
                for index, (cid, text, payload) in enumerate(rows):
                    self.assertEqual(list(payload), keys)
                    self.assertEqual((payload["chunkId"], payload["messageId"], payload["senderKey"]),
                                     (cid, mid, "alice"))
                    self.assertEqual((payload["chunkIndex"], payload["totalChunks"], payload["text"]),
                                     (index, 2, text))
                    for key, value in zip(keys[-3:], anchors):
                        self.assertIs(payload[key], value)
                error = RuntimeError("token fixture")
                def fail_count(value):
                    raise error
                loader.count_tokens = fail_count
                with self.assertRaises(RuntimeError) as got:
                    loader.message_chunks("thread", message, anchors)
                self.assertIs(got.exception, error)
                loader.split_giant_section_v2 = lambda *a, **kw: self.fail("anchors must be checked first")
                with self.assertRaises(ValueError):
                    loader.message_chunks("thread", message, ([], []))

    def test_manager_uses_live_settings_generation_and_retry_identity(self):
        import qdrant_client
        for wg in range(1, 6):
            with self.subTest(wg=wg):
                loader = email_loader(wg)
                events = []
                client = types.SimpleNamespace(
                    get_collections=lambda: types.SimpleNamespace(collections=[]),
                    create_collection=lambda **kw: events.append(("create", kw)),
                    create_payload_index=lambda **kw: events.append(("index", kw)),
                    upsert=lambda **kw: events.append(("upsert", kw)),
                    delete_collection=lambda name: events.append(("abandon", name)))
                with patch.object(qdrant_client, "QdrantClient", return_value=client) as ctor:
                    qm = loader.QdrantManager()
                ctor.assert_called_once_with(host=loader.QDRANT_HOST, port=loader.QDRANT_PORT,
                                             timeout=loader.QDRANT_TIMEOUT)
                retry_calls = []
                def retry(fn, *args, **kwargs):
                    retry_calls.append(fn)
                    return fn(*args, **kwargs)
                loader._with_retry = retry
                loader.COLLECTION = "changed_email_chunks"
                loader.EMBED_DIM = 7
                def prepare(c, name, create, *, call):
                    self.assertIs(call, retry)
                    create(name + "_stage")
                    return name + "_stage"
                def promote(c, source, target, create, *, expected, call):
                    self.assertIs(call, retry)
                    self.assertEqual((source, target, expected),
                                     ("changed_email_chunks_stage", "changed_email_chunks", 2))
                    return expected
                loader.qdrant_generation = types.SimpleNamespace(
                    ABSENT="absent", STAGING="staging", IN_PLACE="in_place",
                    plan_replace=lambda *args: "staging", prepare_staging=prepare,
                    promote_staging=promote,
                    prune_outside=lambda *args, **kw: 4)
                with contextlib.redirect_stdout(io.StringIO()):
                    qm.open_target(recreate=True)
                self.assertEqual(qm.name, "changed_email_chunks_stage")
                self.assertEqual(events[0][1]["vectors_config"].size, 7)
                self.assertEqual(len([event for event in events if event[0] == "index"]), 8)
                qm.upsert(["point"])
                self.assertEqual(events[-1], ("upsert", {"collection_name": qm.name, "points": ["point"]}))
                self.assertEqual(qm.finish_replace({1, 2}), 2)
                self.assertEqual(qm.name, "changed_email_chunks")
                qm.mode = "in_place"
                self.assertEqual(qm.finish_replace({1, 2}), 4)
                qm.abandon_replace()
                self.assertFalse(any(event[0] == "abandon" for event in events))
                qm.mode, qm.name = "staging", "unfinished"
                qm.abandon_replace()
                self.assertEqual(events[-1], ("abandon", "unfinished"))
                self.assertEqual(qm.name, "changed_email_chunks")
                self.assertEqual(len(retry_calls), 2)

    def test_manager_parent_cleanup_keeps_foreign_ids_and_propagates_read_error(self):
        import qdrant_client
        loader = email_loader(2)
        deletes = []
        pages = [( [types.SimpleNamespace(id=1, payload={"threadKey": "t"}),
                    types.SimpleNamespace(id=2, payload={"threadKey": "t"})], "next"),
                 ( [types.SimpleNamespace(id=3, payload={"threadKey": "foreign"})], None)]
        client = types.SimpleNamespace(
            scroll=lambda **kw: pages.pop(0),
            delete=lambda **kw: deletes.extend(kw["points_selector"].points))
        with patch.object(qdrant_client, "QdrantClient", return_value=client):
            qm = loader.QdrantManager()
        self.assertEqual(qm.prune_parents("threadKey", {"t": {1}}), 1)
        self.assertEqual(deletes, [2])
        deletes.clear()
        calls = 0
        error = RuntimeError("later scroll failed")
        def broken_scroll(**kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                return [types.SimpleNamespace(id=2, payload={"threadKey": "t"})], "next"
            raise error
        client.scroll = broken_scroll
        with self.assertRaises(RuntimeError) as got:
            qm.prune_parents("threadKey", {"t": {1}})
        self.assertIs(got.exception, error)
        self.assertEqual(deletes, [])


if __name__ == "__main__":
    unittest.main()
