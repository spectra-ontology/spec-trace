"""Validate a complete document generation before publishing chunks or vectors."""
from __future__ import annotations

from collections.abc import Callable


def require_chunk_projection(chunks, *, owner_key: str, owner: str,
                             point_id: Callable, text_keys=("text",)) -> list[dict]:
    """Require nonempty text, matching ownership, and distinct chunk/point IDs.

    A malformed member rejects the entire document generation. Filtering it out
    would allow a later replacement to remove its previously stored counterpart.
    """
    if not isinstance(chunks, list) or not chunks:
        raise ValueError(f"{owner}: nonempty chunk list required")
    seen_chunks, seen_points = set(), set()
    for index, chunk in enumerate(chunks):
        where = f"{owner}: chunk[{index}]"
        if not isinstance(chunk, dict):
            raise ValueError(f"{where}: object required")
        body = next((chunk.get(key) for key in text_keys if chunk.get(key)), None)
        if not isinstance(body, str) or not body.strip():
            raise ValueError(f"{where}: nonblank text required")
        if chunk.get(owner_key) != owner:
            raise ValueError(f"{where}: {owner_key} does not match selected document")
        chunk_id = chunk.get("chunkId")
        if not isinstance(chunk_id, str) or not chunk_id.strip():
            raise ValueError(f"{where}: nonblank chunkId required")
        if chunk_id in seen_chunks:
            raise ValueError(f"{where}: duplicate chunkId {chunk_id!r}")
        projected_id = point_id(chunk_id)
        if projected_id in seen_points:
            raise ValueError(f"{where}: point ID collision for {chunk_id!r}")
        seen_chunks.add(chunk_id)
        seen_points.add(projected_id)
    return chunks
