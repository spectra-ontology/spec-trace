#!/usr/bin/env python3
"""agenda_retention.py — Canonical Phase-1 agendas survive Phase-2 orphan cleanup.

Spec: docs/tsg/build/process/orphan_detection_guide.md.
Ontology: AgendaItem id and (meetingNumber, agendaNumber) source identities.
Cycle: validate canonical source -> reclaim edges -> sweep unsupported backfills.
배경: A source-backed agenda can legitimately have no incident relationship.
사용: Phase-2 loaders call guarded_cleanup within session.execute_write.
LLM 호출: 없음. This module uses the caller's transaction and creates no files.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import stat


def canonical_agenda_path(root: Path, wg: str) -> Path:
    if not isinstance(wg, str) or not re.fullmatch(r"RAN[1-9]\d*", wg):
        raise ValueError("invalid formal RAN working group")
    return Path(root).resolve() / "ontology/output/tsg/RAN/formal/instances/phase-1" / wg / "agenda_items.jsonld"


def _read_snapshot(path: Path) -> tuple[bytes, tuple]:
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError("canonical agenda source must use regular paths")
    before = path.stat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("canonical agenda source must be a regular file")
    data = path.read_bytes()
    after = path.stat()
    def identity(value):
        return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
    if identity(before) != identity(after):
        raise RuntimeError("canonical agenda source changed while being read")
    return data, identity(after)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate canonical agenda JSON key: {key}")
        result[key] = value
    return result


@dataclass(frozen=True)
class AgendaRetention:
    path: Path
    sha256: str
    identity: tuple
    ids: tuple[str, ...]
    keys: tuple[tuple[str, str], ...]

    def assert_current(self) -> None:
        data, identity = _read_snapshot(self.path)
        if identity != self.identity or hashlib.sha256(data).hexdigest() != self.sha256:
            raise RuntimeError("canonical agenda source changed during cleanup")


def load_agenda_retention(root: Path, wg: str) -> AgendaRetention:
    path = canonical_agenda_path(root, wg)
    data, identity = _read_snapshot(path)
    payload = json.loads(data, object_pairs_hook=_unique_object)
    rows = payload.get("@graph") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows:
        raise ValueError("canonical agenda source requires a nonempty @graph array")
    ids, keys = set(), set()
    for row in rows:
        if not isinstance(row, dict) or row.get("@type") != "tdoc:AgendaItem":
            raise ValueError("canonical agenda source contains a malformed AgendaItem")
        for field in ("@id", "tdoc:meetingNumber", "tdoc:agendaNumber"):
            value = row.get(field)
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(f"canonical agenda source requires a nonempty {field} string")
        identity_key = row["@id"]
        composite_key = (row["tdoc:meetingNumber"], row["tdoc:agendaNumber"])
        if identity_key in ids or composite_key in keys:
            raise ValueError("duplicate canonical agenda id or composite identity")
        ids.add(identity_key)
        keys.add(composite_key)
    source = AgendaRetention(path, hashlib.sha256(data).hexdigest(), identity,
                             tuple(sorted(ids)), tuple(sorted(keys)))
    source.assert_current()
    return source


def sweep_unsupported_agendas(tx, root: Path, wg: str, source: AgendaRetention | None = None) -> int:
    source = source if source is not None else load_agenda_retention(root, wg)
    if source.path != canonical_agenda_path(root, wg):
        raise ValueError("canonical agenda retention scope differs from loader")
    source.assert_current()
    result = tx.run("""
        MATCH (a:AgendaItem)
        WHERE a._createdBy = 'phase-2-backfill' AND NOT (a)--()
          AND NOT (coalesce(a.id, '') IN $canonical_ids)
          AND NOT ([coalesce(a.meetingNumber, ''), coalesce(a.agendaNumber, '')] IN $canonical_keys)
        WITH collect(a) AS orphans, count(a) AS swept
        FOREACH (n IN orphans | DELETE n)
        RETURN swept
    """, canonical_ids=list(source.ids), canonical_keys=[list(key) for key in source.keys])
    record = result.single()
    if record is None or type(record.get("swept")) is not int or record["swept"] < 0:
        raise RuntimeError("agenda cleanup returned no valid deletion count")
    source.assert_current()
    return record["swept"]


def guarded_cleanup(tx, root: Path, wg: str, reclaim, sweep, *, source: AgendaRetention | None = None):
    """Validate before the first deletion; exceptions roll back the caller's unit."""
    source = source if source is not None else load_agenda_retention(root, wg)
    if source.path != canonical_agenda_path(root, wg):
        raise ValueError("canonical agenda retention scope differs from loader")
    source.assert_current()
    reclaimed = reclaim(tx)
    source.assert_current()
    swept = sweep(tx, source)
    source.assert_current()
    return reclaimed, swept
