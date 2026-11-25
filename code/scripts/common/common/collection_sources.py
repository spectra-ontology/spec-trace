"""Pinned, bounded source selections shared by incremental collection CLIs."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from urllib.parse import unquote, urlsplit

MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_SELECTION_BYTES = 256 * 1024 * 1024
MAX_SELECTION_FILES = 256


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def validate_pin(value):
    _require(isinstance(value, dict), "source pin must be an object")
    _require(type(value.get("bytes")) is int and 0 < value["bytes"] <= MAX_FILE_BYTES,
             "source pin requires a positive bounded byte size")
    _require(isinstance(value.get("sha256"), str) and
             re.fullmatch(r"[0-9a-f]{64}", value["sha256"]),
             "source pin requires a lowercase SHA256")
    return value


def _relative(value):
    _require(isinstance(value, str) and value and "\\" not in value and
             not {".", "..", ""}.intersection(value.split("/")),
             "selected source path must be a canonical relative path")
    path = PurePosixPath(value)
    _require(not path.is_absolute() and str(path) == value and
             not any(ord(c) < 32 for c in value), "invalid selected source path")
    return path


def load_meeting_sources(path, *, wg, meeting, base_url):
    """Validate the complete selection before any network access or writes."""
    path = Path(path)
    _require(path.is_file() and not path.is_symlink(), "source manifest must be a regular file")
    _require(path.stat().st_size <= 1024 * 1024, "source manifest exceeds 1 MiB")
    data = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(data, dict) and data.get("schema") == 1 and
             data.get("scope") == "selected_files", "unsupported source selection schema")
    _require(isinstance(wg, str) and re.fullmatch(r"RAN[1-5]", wg) and isinstance(meeting, str) and
             re.fullmatch(rf"TSGR{wg[-1]}_+\d+[A-Za-z0-9_-]*", meeting) and data.get("wg") == wg and
             data.get("meeting") == meeting and meeting.startswith(f"TSGR{wg[-1]}_"),
             "source manifest WG/meeting identity differs from the requested target")
    base = urlsplit(base_url)
    _require(base.scheme == "https" and base.netloc == "www.3gpp.org" and
             not base.query and not base.fragment, "selected sources require official verified HTTPS")
    prefix = unquote(base.path).rstrip("/") + "/" + meeting + "/"
    rows = data.get("files")
    _require(isinstance(rows, list) and 1 <= len(rows) <= MAX_SELECTION_FILES,
             "source manifest needs a nonempty bounded files list")
    seen = set()
    for row in rows:
        validate_pin(row)
        relative = str(_relative(row.get("path")))
        _require(relative not in seen, "duplicate selected source path")
        seen.add(relative)
        parsed = urlsplit(row.get("url", ""))
        _require(parsed.scheme == "https" and parsed.netloc == "www.3gpp.org" and
                 not parsed.query and not parsed.fragment and unquote(parsed.path) == prefix + relative,
                 "selected source URL differs from its meeting-relative identity")
    _require(sum(row["bytes"] for row in rows) <= MAX_SELECTION_BYTES,
             "selected source download exceeds the total byte limit")
    return data


def validate_archive_pins(value, *, specs=None):
    """Pin exactly named archive versions while retaining ordinary latest-mode defaults."""
    _require(isinstance(value, dict), "pinned_archives must be an object")
    if not value:
        return {}
    _require(len(value) <= MAX_SELECTION_FILES, "too many pinned archives")
    for number, row in value.items():
        _require(isinstance(number, str) and re.fullmatch(r"\d{2}\.\d{3}(?:-\d+)?", number),
                 "pinned archive key must be a spec number")
        _require(specs is None or number in specs, "pinned archive is outside the selected specs")
        validate_pin(row)
        _require(isinstance(row.get("filename"), str) and re.fullmatch(
            re.escape(number.replace(".", "")) + r"-[a-z0-9]+\.zip", row["filename"], re.I),
            "pinned archive filename differs from its spec identity")
    _require(sum(row["bytes"] for row in value.values()) <= MAX_SELECTION_BYTES,
             "pinned archives exceed the total byte limit")
    return value


def verify_file(path, pin):
    validate_pin(pin)
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size != pin["bytes"]:
        return False
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == pin["sha256"]


def download_verified(session, url, destination, pin, *, timeout=120):
    """Stream at most pinned bytes and publish atomically after size and SHA checks."""
    validate_pin(pin)
    parsed = urlsplit(url)
    _require(parsed.scheme == "https" and parsed.netloc == "www.3gpp.org" and
             not parsed.query and not parsed.fragment, "selected download requires official HTTPS")
    destination = Path(destination)
    _require(not destination.is_symlink(), "selected download destination is a symlink")
    # Inspect ancestors before mkdir/open, including a symlinked existing parent.
    for parent in destination.parents:
        _require(not parent.is_symlink(), "selected download path contains a symlink")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".pinned-", delete=False) as stream:
            temporary = Path(stream.name)
            digest, received = hashlib.sha256(), 0
            with session.get(url, timeout=timeout, stream=True, verify=True, allow_redirects=False) as response:
                response.raise_for_status()
                _require(response.status_code == 200, "selected download requires a complete HTTP 200 response")
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    received += len(chunk)
                    _require(received <= pin["bytes"], "selected source exceeds its pinned byte limit")
                    stream.write(chunk)
                    digest.update(chunk)
            _require(received == pin["bytes"] and digest.hexdigest() == pin["sha256"],
                     "selected source byte/SHA256 verification failed")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return {"bytes": received, "sha256": digest.hexdigest(), "transport": "verified_https"}


def collect_meeting_sources(selection, destination, session, *, dry_run=False):
    """Collect only selected paths; all other meeting files remain outside this run."""
    destination = Path(destination)
    rows = []
    for pin in selection["files"]:
        target = destination.joinpath(*_relative(pin["path"]).parts)
        _require(target.resolve().is_relative_to(destination.resolve()), "selected source escapes destination")
        for parent in target.parents:
            _require(not parent.is_symlink(), "selected source path contains a symlink")
        if dry_run:
            rows.append({"path": pin["path"], "status": "planned"})
        elif verify_file(target, pin):
            rows.append({"path": pin["path"], "status": "verified_existing"})
        else:
            receipt = download_verified(session, pin["url"], target, pin)
            rows.append({"path": pin["path"], "status": "downloaded", **receipt})
    return {"scope": "selected_files", "whole_meeting_downloaded": False,
            "files": rows, "selected_files": len(rows)}
