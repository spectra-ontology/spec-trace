"""Classify stored email fetch results for verification and retry decisions."""
from __future__ import annotations

import json
from pathlib import Path

FETCH_FAILURE_STATUSES = ("detail_failed", "body_failed")
FAILED_FILE_STATUSES = FETCH_FAILURE_STATUSES + ("parse_error", "unknown")
_KNOWN_STATUSES = ("ok", "no_body_url") + FETCH_FAILURE_STATUSES


def message_file_status(path: Path) -> str:
    """Return a hashable known status; malformed records remain retryable.

    A fetched message without a body URL is a completed collection observation.
    Missing, unrecognized or non-string status values require a fresh fetch.
    """
    try:
        data = Path(path).read_text(encoding="utf-8")
        record = json.loads(data)
    except (OSError, UnicodeError, ValueError):
        return "parse_error"
    return message_record_status(record)


def message_record_status(record) -> str:
    """이미 읽은 메시지의 수집 상태를 같은 기준으로 판정합니다."""
    if not isinstance(record, dict):
        return "parse_error"
    status = record.get("fetch_status")
    return status if isinstance(status, str) and status in _KNOWN_STATUSES else "unknown"
