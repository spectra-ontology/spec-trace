#!/usr/bin/env python3
"""email_vectors.py — Shared email payload projection and Qdrant generation management.

Spec: docs/tsg/RAN/email/RAN2/phase-2/design-spec/email_vdb_specs.md (§5–8)
Ontology: EmailMessage.id / Delegate.delegateId remain payload foreign keys.
Cycle: E-2 message chunk projection, upsert, parent-tail cleanup and replacement.
배경: Five WG entry points share one payload and collection-management contract.
사용: WG E-2 loaders import this module; each keeps its own source and encoder.
LLM 호출: None here. Encoding and chunk splitting remain in the WG entry point.
"""
from __future__ import annotations

from dataclasses import dataclass
from common.qdrant_generation import check_scroll_progress


@dataclass(frozen=True)
class QdrantSettings:
    """The WG collection and client settings, read through a live getter."""

    collection: str
    dimension: int
    host: str
    port: int
    timeout: int


def build_message_chunks(tk, message, anchors, *, message_id, sender_key, chunks,
                         chunk_key, text_sha, count_tokens):
    """Project already split message bodies into the E-2 payload contract."""
    spec_anchors, meeting_anchors, bracket_ids = anchors
    total = len(chunks)
    out = []
    for i, ck in enumerate(chunks):
        chunk_id = chunk_key(message_id, i)                         # Spec §5.1
        out.append((chunk_id, ck, {                                 # Spec §5.2
            "chunkId": chunk_id,
            "messageId": message_id,
            "messageIndex": message.get("index"),
            "threadKey": tk,
            "senderKey": sender_key,
            "archiveCode": message.get("archive_code"),
            "sentDate": message.get("date_parsed"),
            "roundNum": message.get("round_num"),
            "subject": message.get("subject"),
            "chunkIndex": i,
            "totalChunks": total,
            "text": ck,
            "textSha256": text_sha(ck),
            "tokenCount": count_tokens(ck),
            "specAnchors": spec_anchors,
            "meetingAnchors": meeting_anchors,
            "bracketIds": bracket_ids,
        }))
    return out


class EmailQdrantManager:
    """Manage the E-2 collection using settings and helpers from its WG loader."""

    def __init__(self, *, settings, retry, generation):
        # Getters retain each WG facade's live bindings throughout a long run.
        self._settings = settings
        self._retry = retry
        self._generation = generation
        from qdrant_client import QdrantClient
        self.client = QdrantClient(host=settings().host, port=settings().port,
                                   timeout=settings().timeout)
        self.name = settings().collection
        self.mode = None
        self._promotion_attempted = False

    def open_target(self, recreate: bool = False):
        """입력 조회·검사·임베딩 준비를 마친 뒤 적재 대상 컬렉션을 정한다.

        --recreate 여도 여기서 기존 컬렉션을 지우지 않는다. 벡터 설정(차원 · 거리)이 같으면
        같은 컬렉션에 업서트하고 부모별로 이번 입력에 없는 포인트를 삭제한다.
        finish_replace는 전체 입력에서 빠진 포인트를 삭제하며, 실패 전에 반영한 변경은 유지된다.
        설정이 다르면 별도 staging 컬렉션에 적재하고 finish_replace가 기존 이름으로 복사한다.
        복사를 시작하기 전까지 기존 컬렉션을 유지한다
        (scripts/common/common/qdrant_generation.py).
        """
        from qdrant_client.http.models import Distance
        self._promotion_attempted = False
        names = [c.name for c in self.client.get_collections().collections]
        if not recreate:
            if self._settings().collection in names:
                print(f"  기존 컬렉션 사용: {self._settings().collection}")
            else:
                self._create(self._settings().collection)
            return
        self.mode = self._generation().plan_replace(
            self.client, self._settings().collection,
            self._settings().dimension, Distance.COSINE)
        if self.mode == self._generation().ABSENT:
            self._create(self._settings().collection)
        elif self.mode == self._generation().STAGING:
            self.name = self._generation().prepare_staging(
                self.client, self._settings().collection, self._create, call=self._retry())
            print(f"  벡터 설정이 달라 staging 컬렉션에 적재: {self.name}")
        else:
            print(f"  기존 컬렉션에 업서트 후 이번 입력에 없는 포인트 삭제: {self._settings().collection}")

    def finish_replace(self, keep_ids: set) -> int:
        """전체 입력의 적재를 마친 뒤 --recreate의 삭제·복사 단계를 수행한다.

        in_place면 이번 실행에 포함되지 않은 포인트를 삭제하고, staging이면 검증한
        별도 컬렉션을 기존 이름으로 복사한다. 삭제하거나 복사한 포인트 수를 반환한다.
        """
        if self.mode == self._generation().IN_PLACE:
            return self._generation().prune_outside(
                self.client, self._settings().collection, keep_ids, call=self._retry())
        if self.mode == self._generation().STAGING:
            # 원 컬렉션을 교체하기 시작한 뒤에는 완성 staging을 복구용으로 보존한다.
            self._promotion_attempted = True
            moved = self._generation().promote_staging(
                self.client, self.name, self._settings().collection, self._create,
                expected=len(keep_ids), call=self._retry())
            self.name = self._settings().collection
            self._promotion_attempted = False
            return moved
        return 0

    def abandon_replace(self) -> None:
        """승격 전 미완성 staging만 삭제하고, 승격을 시도한 데이터는 복구용으로 보존한다."""
        if self.mode == self._generation().STAGING and self.name != self._settings().collection:
            if self._promotion_attempted:
                print(f"  [WARN] 교체 실패: 복구용 컬렉션 {self.name}을 보존합니다. "
                      f"원 컬렉션 {self._settings().collection}의 적재 상태를 확인하세요.")
                return
            self._retry()(self.client.delete_collection, self.name)
            self.name = self._settings().collection

    def _create(self, name: str):
        from qdrant_client.http import models
        from qdrant_client.http.models import Distance, VectorParams
        print(f"  컬렉션 생성: {name} (dim={self._settings().dimension}, Cosine)")     # Spec §0/§8
        self.client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=self._settings().dimension, distance=Distance.COSINE),
        )
        # payload 인덱스: FK/필터 필드 (Spec §5.2)
        for field in ("messageId", "threadKey", "senderKey", "archiveCode",
                      "specAnchors", "meetingAnchors", "bracketIds"):
            self.client.create_payload_index(
                collection_name=name, field_name=field,
                field_schema=models.PayloadSchemaType.KEYWORD)
        self.client.create_payload_index(
            collection_name=name, field_name="roundNum",
            field_schema=models.PayloadSchemaType.INTEGER)

    def upsert(self, points):
        if points:
            self._retry()(self.client.upsert, collection_name=self.name, points=points)

    def existing_payloads(self, ids: list[int], batch: int = 1000) -> dict[int, dict]:
        """주어진 point id 중 이미 컬렉션에 있는 것의 payload 를 돌려준다.

        재개를 위치가 아니라 신원으로 판정하기 위한 것이다 — point id 는 chunkId 의
        결정적 함수라(md5) 스레드 열거 순서와 무관하게 같은 청크가 같은 id 를 얻는다.
        id 가 있다는 것만으로는 건너뛰지 않는다. 같은 id 에 다른 본문이 실려 있으면
        (입력이 바뀐 경우) 그 점의 벡터는 지금 본문의 벡터가 아니기 때문이다.
        """
        found: dict[int, dict] = {}
        for i in range(0, len(ids), batch):
            got = self._retry()(
                self.client.retrieve, collection_name=self.name, ids=ids[i:i + batch],
                with_payload=True, with_vectors=False,
            )
            found.update((int(p.id), p.payload or {}) for p in got)
        return found

    def vectors(self, ids: list[int], batch: int = 256) -> dict[int, list]:
        """point id → 저장된 벡터(본문이 같아 payload 만 바꿀 때 벡터를 그대로 다시 싣는다)."""
        found: dict[int, list] = {}
        for i in range(0, len(ids), batch):
            got = self._retry()(
                self.client.retrieve, collection_name=self.name, ids=ids[i:i + batch],
                with_payload=False, with_vectors=True,
            )
            found.update((int(p.id), p.vector) for p in got)
        return found

    def count(self) -> int:
        return self.client.get_collection(self.name).points_count

    def prune_parents(self, field: str, new_ids_by_parent: dict) -> int:
        """같은 부모의 포인트 가운데 이번 입력이 만들지 않은 id 를 지운다.

        부모 신원은 payload `field` 값의 정확 일치로만 고른다(keyword 인덱스 MatchAny).
        그래서 다른 부모의 포인트는 필터에 걸리지 않는다. 지우는 것은 그 부모의
        현재 id 집합 밖에 있는 것뿐이라 같은 입력을 다시 돌리면 0건이다.
        부모는 그 부모의 청크를 모두 만든 뒤에만 넘어오므로 집합이 덜 찬 채로
        지우는 일이 없다.
        """
        from qdrant_client.http import models
        if not new_ids_by_parent:
            return 0
        stale: list[int] = []
        parents = list(new_ids_by_parent)
        for i in range(0, len(parents), 256):
            flt = models.Filter(must=[models.FieldCondition(
                key=field, match=models.MatchAny(any=parents[i:i + 256]))])
            offset = None
            seen_offsets = set()
            while True:
                got, offset = self._retry()(
                    self.client.scroll, collection_name=self.name, scroll_filter=flt,
                    limit=1000, offset=offset, with_payload=[field], with_vectors=False)
                check_scroll_progress(offset, seen_offsets)
                for p in got:
                    keep = new_ids_by_parent.get((p.payload or {}).get(field))
                    if keep is not None and int(p.id) not in keep:
                        stale.append(int(p.id))
                if offset is None:
                    break
        self._delete_ids(stale)
        return len(stale)

    def prune_absent(self, keep_ids: set) -> int:
        """컬렉션 전체를 훑어 이번 실행이 만들지 않은 id 를 지운다(전량 동기화).

        입력에서 통째로 빠진 부모는 부모 단위 정리로는 보이지 않는다 — 이번 실행이
        그 부모를 한 번도 만나지 않기 때문이다. 이 적재기는 매 실행 원본 자료 전량을
        읽고 이 컬렉션에 포인트를 쓰는 자리가 이 적재기 하나뿐이므로, 전량을 끝까지
        읽은 실행의 id 집합이 곧 컬렉션이 가져야 할 집합이다.
        """
        stale: list[int] = []
        offset = None
        seen_offsets = set()
        while True:
            got, offset = self._retry()(
                self.client.scroll, collection_name=self.name, limit=10000,
                offset=offset, with_payload=False, with_vectors=False)
            check_scroll_progress(offset, seen_offsets)
            stale.extend(int(p.id) for p in got if int(p.id) not in keep_ids)
            if offset is None:
                break
        self._delete_ids(stale)
        return len(stale)

    def _delete_ids(self, ids: list) -> None:
        from qdrant_client.http import models
        for i in range(0, len(ids), 1000):
            self._retry()(self.client.delete, collection_name=self.name,
                        points_selector=models.PointIdsList(points=ids[i:i + 1000]))
