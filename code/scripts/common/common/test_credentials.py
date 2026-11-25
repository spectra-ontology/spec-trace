#!/usr/bin/env python3
"""Verify the release credential module's environment-only contract.

Synthetic environment values test lookup, missing values, ignored settings files,
and Neo4j authentication/header consistency. Signature and AST checks retain the
prohibition on credential defaults, including synthetic negative examples.

Usage: python3 -B scripts/common/common/test_credentials.py
Exit: 0 = all checks pass / 1 = a check fails. No service or model calls.
"""
from __future__ import annotations

import ast
import base64
import inspect
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from common import credentials  # noqa: E402

FAIL: list[str] = []

_SECRETISH = ("PASSWORD", "SECRET", "TOKEN", "API_KEY")


def default_sites(source: str) -> list[str]:
    """Find secret defaults, literal fallback values, and direct secret assignments."""
    found: list[str] = []

    def secretish(node: ast.AST) -> bool:
        return any(w in ast.dump(node) for w in _SECRETISH)

    for node in ast.walk(ast.parse(source)):
        # ① os.environ.get(KEY, 대신값) · os.getenv(KEY, 대신값)
        if isinstance(node, ast.Call) and len(node.args) >= 2:
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            if name in ("get", "getenv") and secretish(node.args[0]):
                found.append(f"{name}(…, 대신값) @줄 {node.lineno}")
        # ② <비밀 읽기> or "평문"
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            for left, right in zip(node.values, node.values[1:]):
                if secretish(left) and isinstance(right, ast.Constant) and isinstance(right.value, str):
                    found.append(f"… or '평문' @줄 {node.lineno}")
        # ③ PASSWORD = "평문" 꼴의 직접 대입
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and any(w in tgt.id.upper() for w in _SECRETISH):
                    found.append(f"{tgt.id} = '평문' @줄 {node.lineno}")
    return found


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'✅' if ok else '🔴'} {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        FAIL.append(name)


def main() -> int:
    print("── 1. Credential functions accept no fallback value")
    sig = inspect.signature(credentials.secret)
    params = list(sig.parameters)
    check("secret() accepts only name and env_file", params == ["name", "env_file"], str(params))
    check("secret() requires name",
          sig.parameters["name"].default is inspect.Parameter.empty)
    for fn in ("neo4j_password", "neo4j_auth"):
        p = list(inspect.signature(getattr(credentials, fn)).parameters)
        check(f"{fn}() accepts no fallback value", p == ["env_file"], str(p))

    src = Path(credentials.__file__).read_text(encoding="utf-8")
    sites = default_sites(src)
    check("Module code contains no secret default", sites == [], "; ".join(sites) or "0 sites")

    print("── 2. Environment variables supply values; settings files are ignored")
    key = "SPECTRA_SELFTEST_SECRET"
    with tempfile.TemporaryDirectory() as d:
        good = Path(d) / "with-value"
        good.write_text(f"{key}=synthetic-file-value\n", encoding="utf-8")
        malformed = Path(d) / "invalid-utf8"
        malformed.write_bytes(b"SPECTRA_SELFTEST_SECRET=broken-\xff\n")
        missing = Path(d) / "does-not-exist"
        with patch.dict(os.environ, {}, clear=True):
            for label, path in (("default", None), ("populated", good),
                                ("invalid UTF-8", malformed), ("missing", missing)):
                check(f"{label} settings file produces an empty mapping",
                      credentials.env_file_values(path) == {})
                try:
                    credentials.secret(key, env_file=path)
                    check(f"Absent environment value rejects {label} file fallback", False)
                except credentials.MissingCredential as exc:
                    check(f"Absent environment value rejects {label} file fallback",
                          key in str(exc))
            check("Ignoring settings files does not populate the environment", key not in os.environ)
            os.environ[key] = ""
            try:
                credentials.secret(key, env_file=good)
                check("An empty environment value raises MissingCredential", False)
            except credentials.MissingCredential:
                check("An empty environment value raises MissingCredential", True)
            value = "synthetic-environment-value"
            os.environ[key] = value
            check("secret() returns the environment value", credentials.secret(key) == value)
            check("The environment value takes precedence over a populated file",
                  credentials.secret(key, env_file=good) == value and os.environ[key] == value)
            with patch.object(Path, "read_text", side_effect=AssertionError("Settings file read")), \
                    patch.object(Path, "read_bytes", side_effect=AssertionError("Settings file read")):
                check("Credential lookup and mapping avoid settings file reads",
                      credentials.secret(key, env_file=good) == value
                      and credentials.env_file_values(good) == {})

    print("── 3. Neo4j settings and headers use synthetic environment values")
    with patch.dict(os.environ, {}, clear=True):
        check("The default Neo4j account is neo4j", credentials.neo4j_user() == "neo4j")
        for name in ("neo4j_password", "neo4j_auth", "neo4j_http_authorization"):
            try:
                getattr(credentials, name)()
                check(f"{name}() requires an environment password", False)
            except credentials.MissingCredential:
                check(f"{name}() requires an environment password", True)
        os.environ["NEO4J_PASSWORD"] = "synthetic-neo4j-password"
        check("neo4j_password() reads the synthetic environment value",
              credentials.neo4j_password() == "synthetic-neo4j-password")
        check("neo4j_auth() uses the default account with the environment password",
              credentials.neo4j_auth() == ("neo4j", "synthetic-neo4j-password"))
        os.environ["NEO4J_USER"] = "synthetic-user"
        check("NEO4J_USER overrides the default account", credentials.neo4j_user() == "synthetic-user")
        check("neo4j_auth() agrees with the individual environment accessors",
              credentials.neo4j_auth() == (credentials.neo4j_user(), credentials.neo4j_password()))
        expected = "Basic " + base64.b64encode(b"synthetic-user:synthetic-neo4j-password").decode("ascii")
        check("The HTTP Basic header encodes the exact synthetic authentication pair",
              credentials.neo4j_http_authorization() == expected)
        os.environ["NEO4J_USER"] = ""
        check("An empty NEO4J_USER selects the default account", credentials.neo4j_user() == "neo4j")
        os.environ["NEO4J_PASSWORD"] = ""
        try:
            credentials.neo4j_password()
            check("An empty NEO4J_PASSWORD raises MissingCredential", False)
        except credentials.MissingCredential:
            check("An empty NEO4J_PASSWORD raises MissingCredential", True)

    print("── 4. Synthetic negative examples exercise the default detector")
    # ①에서 사용하는 AST 검사에 비밀값 기본값의 합성 예시를 전달한다.
    # 실제 위반은 검출하고, 실행 코드가 아닌 docstring의 예시는 제외해야 한다.
    for label, sample in [
        ("환경변수 읽기 + 대신값", 'PW = os.environ.get("NEO4J_PASSWORD", "평문")'),
        ("getenv + 대신값", 'PW = os.getenv("NEO4J_PASSWORD", "평문")'),
        ("`or \"…\"` 대신값", 'PW = os.environ.get("NEO4J_PASSWORD") or "평문"'),
        ("이름에 직접 대입", 'NEO4J_PASSWORD = "평문"'),
    ]:
        check(f"The default detector catches a synthetic violation ({label})", default_sites(sample) != [])
    check("A docstring example is excluded from executable-code findings",
          default_sites('"""예: os.environ.get(\'NEO4J_PASSWORD\', \'평문\')"""') == [])

    def _with_default(name, default=None):  # 허용하지 않는 기본값 인자가 포함된 합성 함수
        return default
    sig_bad = inspect.signature(_with_default)
    check("The signature check detects an added fallback argument",
          list(sig_bad.parameters) != ["name", "env_file"])

    print(f"\n{'[PASS]' if not FAIL else '[FAIL]'} {len(FAIL)} failures" + (f" · {FAIL}" if FAIL else ""))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
