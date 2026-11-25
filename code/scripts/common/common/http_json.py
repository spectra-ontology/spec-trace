"""Standard-library JSON POST transport without encoder or credential setup."""
from __future__ import annotations

import json
import urllib.request


def post_json(url: str, body: dict, timeout: float = 30.0) -> dict:
    """POST JSON and decode the response; serialization, HTTP and JSON errors propagate."""
    request = urllib.request.Request(
        url,
        data=json.dumps(body, allow_nan=False).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode())
