#!/usr/bin/env python3
"""자격증명 로더의 필수 인자, 정본 파일 읽기와 누락 시 예외를 검증한다.

기본값 인자가 없는지와 소스에 평문 기본값·직접 대입이 있는지를 AST로 검사한다.
합성 입력으로 위반 탐지와 docstring 예시 제외도 확인한다.

Usage: python3 scripts/common/common/test_credentials.py
Exit: 0 = 전부 통과 / 1 = 하나라도 실패. LLM 호출: 없음."""
from __future__ import annotations

import ast
import inspect
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from common import credentials  # noqa: E402

FAIL: list[str] = []

_SECRETISH = ("PASSWORD", "SECRET", "TOKEN", "API_KEY")


def default_sites(source: str) -> list[str]:
    """AST에서 자격증명 이름의 기본값 호출, 문자열 or 대체값과 평문 직접 대입을 찾는다."""
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
    print("── ① 대신값을 받을 자리가 없다 (구조)")
    sig = inspect.signature(credentials.secret)
    params = list(sig.parameters)
    check("secret() 의 인자는 name 과 env_file 뿐", params == ["name", "env_file"], str(params))
    check("secret() 의 name 에 기본값이 없다",
          sig.parameters["name"].default is inspect.Parameter.empty)
    for fn in ("neo4j_password", "neo4j_auth"):
        p = list(inspect.signature(getattr(credentials, fn)).parameters)
        check(f"{fn}() 도 대신값 인자를 받지 않는다", p == ["env_file"], str(p))

    src = Path(credentials.__file__).read_text(encoding="utf-8")
    sites = default_sites(src)
    check("모듈 코드에 대신값을 두는 자리가 없다", sites == [], "; ".join(sites) or "0건")

    print("── ② 정본 파일에 값이 있으면 읽는다 (프로세스 환경 없이)")
    key = "SPECTRA_SELFTEST_SECRET"
    os.environ.pop(key, None)
    token = "selftest-" + os.urandom(4).hex()
    with tempfile.TemporaryDirectory() as d:
        good = Path(d) / "with-value"
        good.write_text(
            "# 주석 줄\n"
            "\n"
            "BARE_LINE_WITHOUT_EQUALS\n"
            f"export {key}={token}\n"
            'QUOTED="a=b"\n',
            encoding="utf-8",
        )
        got = credentials.secret(key, env_file=good)
        check("export 접두 · 주석 · 빈 줄 · `=` 없는 줄을 넘겨 값을 찾는다", got == token)
        vals = credentials.env_file_values(good)
        check("감싼 따옴표를 벗기고 값 안의 `=` 는 지킨다", vals.get("QUOTED") == "a=b", repr(vals.get("QUOTED")))
        check("`=` 없는 줄은 키가 되지 않는다", "BARE_LINE_WITHOUT_EQUALS" not in vals)

        malformed = Path(d) / "invalid-utf8"
        malformed.write_bytes(b"SPECTRA_SELFTEST_SECRET=broken-\xff\n")
        try:
            credentials.env_file_values(malformed)
            check("손상된 UTF-8을 다른 비밀값으로 바꾸지 않는다", False)
        except UnicodeError:
            check("손상된 UTF-8을 다른 비밀값으로 바꾸지 않는다", True)
        malformed.write_text(f"{key}={token}\n", encoding="utf-8")
        check("정본 파일을 고친 뒤 다시 읽을 수 있다",
              credentials.env_file_values(malformed).get(key) == token)

        os.environ[key] = ""
        got = credentials.secret(key, env_file=good)
        check("빈 프로세스 값은 정본 파일에서 읽는다", got == token)
        check("빈 프로세스 값에도 읽은 정본을 전달한다", os.environ.get(key) == token)
        child = subprocess.run(
            [sys.executable, "-c", "import os, sys; sys.stdout.write(os.environ[sys.argv[1]])", key],
            check=True, capture_output=True, text=True,
        )
        check("하위 프로세스도 같은 정본을 받는다", child.stdout == token)
        override = "process-" + os.urandom(4).hex()
        os.environ[key] = override
        got = credentials.secret(key, env_file=good)
        check("이미 지정한 프로세스 값은 정본 파일보다 우선한다",
              got == override and os.environ[key] == override)

        print("── ③ 값이 없으면 멈춘다 (역방향 — 이 방향이 없으면 통과만 하는 시험이다)")
        os.environ.pop(key, None)
        empty = Path(d) / "without-value"
        empty.write_text("# 값 없음\n", encoding="utf-8")
        try:
            credentials.secret(key, env_file=empty)
            check("없으면 MissingCredential 로 멈춘다", False, "예외 없이 값을 돌려줬다")
        except credentials.MissingCredential as exc:
            check("없으면 MissingCredential 로 멈춘다", True, "정본 자리를 말한다"
                  if ".env" in str(exc) else "메시지에 정본 자리가 없다")
        missing = Path(d) / "does-not-exist"
        check("정본 파일이 아예 없으면 빈 사전이다", credentials.env_file_values(missing) == {})
        try:
            credentials.secret(key, env_file=missing)
            check("정본 파일이 없어도 멈춘다", False, "예외 없이 값을 돌려줬다")
        except credentials.MissingCredential:
            check("정본 파일이 없어도 멈춘다", True)
    os.environ.pop(key, None)

    print("── ④ 현재 환경에서 Neo4j 자격증명을 읽는다 (비밀값은 출력하지 않는다)")
    try:
        pw = credentials.neo4j_password()
        check("neo4j_password() 가 빈 문자열이 아니다", bool(pw), f"{len(pw)}자")
        user, pw2 = credentials.neo4j_auth()
        check("neo4j_auth() 가 같은 사용자 이름과 비밀번호를 반환한다",
              user == credentials.neo4j_user() and pw2 == pw)
    except credentials.MissingCredential as exc:
        check("neo4j_password() 가 값을 돌려준다", False, f"정본에 값이 없다: {exc}")

    print("── ⑤ 기본값 탐지기가 합성 결함을 실제로 검출하는지 확인한다")
    # ①에서 사용하는 AST 검사에 비밀값 기본값의 합성 예시를 전달한다.
    # 실제 위반은 검출하고, 실행 코드가 아닌 docstring의 예시는 제외해야 한다.
    for label, sample in [
        ("환경변수 읽기 + 대신값", 'PW = os.environ.get("NEO4J_PASSWORD", "평문")'),
        ("getenv + 대신값", 'PW = os.getenv("NEO4J_PASSWORD", "평문")'),
        ("`or \"…\"` 대신값", 'PW = os.environ.get("NEO4J_PASSWORD") or "평문"'),
        ("이름에 직접 대입", 'NEO4J_PASSWORD = "평문"'),
    ]:
        check(f"기본값 탐지기가 합성 위반({label})을 검출한다", default_sites(sample) != [])
    check("설명글이 결함 꼴을 예시로 적어도 코드로 세지 않는다",
          default_sites('"""예: os.environ.get(\'NEO4J_PASSWORD\', \'평문\')"""') == [])

    def _with_default(name, default=None):  # 허용하지 않는 기본값 인자가 포함된 합성 함수
        return default
    sig_bad = inspect.signature(_with_default)
    check("기본값 인자가 추가되면 ① 의 함수 서명 검사가 불일치를 검출한다",
          list(sig_bad.parameters) != ["name", "env_file"])

    print(f"\n{'[PASS]' if not FAIL else '[FAIL]'} 실패 {len(FAIL)}건" + (f" · {FAIL}" if FAIL else ""))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
