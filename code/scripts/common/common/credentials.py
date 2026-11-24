#!/usr/bin/env python3
"""Connection settings for the scripts of this package, read from environment variables.

This file stands at the import path of the project's credential module and
offers the same names. It holds no secret, no host and no password, and it
reads no settings file. Before running a script that opens a database
connection, export NEO4J_PASSWORD, and NEO4J_USER when the account name
differs from the server's default account.

    from common import credentials
    driver = GraphDatabase.driver(uri, auth=credentials.neo4j_auth())
"""

from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

# The folder that holds `scripts/`. It is derived from this file's own position.
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class MissingCredential(RuntimeError):
    """A required setting is absent from the environment. No default stands in for it."""


def env_file_values(env_file: str | Path | None = None) -> dict[str, str]:
    """Settings files are not read in this package, so the mapping is always empty."""
    return {}


def secret(name: str, *, env_file: str | Path | None = None) -> str:
    """Return the value of the environment variable `name`, or raise MissingCredential."""
    value = os.environ.get(name)
    if value:
        return value
    raise MissingCredential(f"{name} is not set. Export it as an environment variable.")


def neo4j_user() -> str:
    """Account name: NEO4J_USER, or the server's default account name when it is unset."""
    return os.environ.get("NEO4J_USER") or "neo4j"


def neo4j_password(*, env_file: str | Path | None = None) -> str:
    return secret("NEO4J_PASSWORD", env_file=env_file)


def neo4j_auth(*, env_file: str | Path | None = None) -> tuple[str, str]:
    """The (account name, password) pair for `GraphDatabase.driver(..., auth=...)`."""
    return (neo4j_user(), neo4j_password(env_file=env_file))


def neo4j_http_authorization() -> str:
    """The value of an HTTP Basic Authorization header, built when a request is made."""
    user, password = neo4j_auth()
    return "Basic " + base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
