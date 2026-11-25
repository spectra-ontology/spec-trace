"""Qdrant 세대 교체의 조회 종료와 삭제 범위를 서비스 없이 검사한다.

Spec: docs/common/process/internal_embedding_guide.md.
Ontology: 합성 포인트 ID를 사용하며 실제 컬렉션·모델에 접근하지 않는다.
Cycle: 합성 페이지 응답 → 실제 교체 함수 → 삭제·업서트 호출 대조.
배경: 반복된 continuation을 정상 진행으로 받아들이면 교체가 끝나지 않는다.
사용: python3 -B -m unittest discover -s scripts/common/common -p test_qdrant_generation.py.
LLM 호출: 없음.
"""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import qdrant_generation as generation
from common.email_vectors import EmailQdrantManager


def point(identifier):
    return SimpleNamespace(id=identifier, vector=[1.0], payload={"text": "synthetic"})


class GenerationScrollTests(unittest.TestCase):
    def client(self, pages):
        return SimpleNamespace(
            scroll=Mock(side_effect=[*pages, AssertionError("조회 반복을 제때 거절하지 못했습니다")]),
            delete=Mock(), delete_collection=Mock(), upsert=Mock(),
            get_collections=Mock(return_value=SimpleNamespace(
                collections=[SimpleNamespace(name="original"), SimpleNamespace(name="stage")])),
            count=Mock(return_value=SimpleNamespace(count=2)),
        )

    def test_prune_rejects_repeated_cursor_before_deleting_any_point(self):
        for second in ([], [point(3)]):
            with self.subTest(empty=not second):
                client = self.client([([point(2)], 7), (second, 7)])
                with self.assertRaisesRegex(ValueError, "반복"):
                    generation.prune_outside(client, "original", [1])
                self.assertEqual(client.scroll.call_count, 2)
                client.delete.assert_not_called()
                client.delete_collection.assert_not_called()

    def test_prune_follows_advancing_pages_and_preserves_scope(self):
        client = self.client([([point(1), point(2)], 7), ([], 9), ([point(3)], None)])
        scope = object()
        self.assertEqual(generation.prune_outside(
            client, "original", [1], scroll_filter=scope, delete_batch=1), 2)
        self.assertEqual([call.kwargs["offset"] for call in client.scroll.call_args_list], [None, 7, 9])
        self.assertTrue(all(call.kwargs["scroll_filter"] is scope
                            for call in client.scroll.call_args_list))
        self.assertEqual([call.kwargs["points_selector"].points
                          for call in client.delete.call_args_list], [[2], [3]])
        client.delete_collection.assert_not_called()

    def test_prune_refuses_empty_replacement_before_any_client_call(self):
        client = self.client([])
        with self.assertRaises(ValueError):
            generation.prune_outside(client, "original", [])
        client.scroll.assert_not_called()
        client.delete.assert_not_called()

    def test_promote_repeated_cursor_retains_staging_for_recovery(self):
        for second in ([], [point(2)]):
            with self.subTest(empty=not second):
                client = self.client([([point(1)], 7), (second, 7)])
                create = Mock()
                with self.assertRaisesRegex(ValueError, "반복"):
                    generation.promote_staging(client, "stage", "original", create, expected=2)
                self.assertEqual(client.scroll.call_count, 2)
                client.delete_collection.assert_called_once_with("original")
                create.assert_called_once_with("original")
                # 원 컬렉션은 복사 중일 수 있다. 복구용 stage를 지우지 않는지 확인한다.
                self.assertEqual(client.upsert.call_count, 1)
                self.assertEqual(client.upsert.call_args.kwargs["collection_name"], "original")

    def test_promote_completes_only_after_terminal_page_and_count_match(self):
        client = self.client([([point(1)], 7), ([], 9), ([point(2)], None)])
        create = Mock()
        self.assertEqual(generation.promote_staging(
            client, "stage", "original", create, expected=2), 2)
        self.assertEqual([call.args[0] for call in client.delete_collection.call_args_list],
                         ["original", "stage"])
        self.assertEqual([call.kwargs["offset"] for call in client.scroll.call_args_list], [None, 7, 9])
        self.assertEqual(client.upsert.call_count, 2)
        create.assert_called_once_with("original")

    def test_email_pruning_rejects_repeat_before_deletion_and_allows_progress(self):
        for method in ("prune_parents", "prune_absent"):
            for repeated in (True, False):
                with self.subTest(method=method, repeated=repeated):
                    first = SimpleNamespace(id=2, payload={"messageId": "synthetic"})
                    pages = [([first], 7), ([], 7)] if repeated else [
                        ([first], 7), ([], 9), ([], None)]
                    client = self.client(pages)
                    manager = object.__new__(EmailQdrantManager)
                    manager.client, manager.name = client, "synthetic"
                    manager._retry = lambda: (lambda fn, *a, **kw: fn(*a, **kw))
                    args = ("messageId", {"synthetic": {1}}) if method == "prune_parents" else ({1},)
                    if repeated:
                        with self.assertRaisesRegex(ValueError, "반복"):
                            getattr(manager, method)(*args)
                        self.assertEqual(client.scroll.call_count, 2)
                        client.delete.assert_not_called()
                    else:
                        self.assertEqual(getattr(manager, method)(*args), 1)
                        self.assertEqual([c.kwargs["offset"] for c in client.scroll.call_args_list], [None, 7, 9])
                        client.delete.assert_called_once()
                        self.assertEqual(client.delete.call_args.kwargs["points_selector"].points, [2])


if __name__ == "__main__":
    unittest.main()
