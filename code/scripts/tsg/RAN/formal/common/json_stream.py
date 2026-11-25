"""큰 JSON 파일의 최상위 배열 하나를 원소 하나씩 읽는다.

Phase-8 CR 청크 파일(`{"metadata": {...}, "chunks": [ {...}, ... ]}`)은 WG 마다 수억 바이트라
`json.load` 로 통째로 올리면 파이썬 객체가 파일의 몇 배로 부풀어, 임베딩 모델과 한 프로세스에
놓인 적재기가 메모리 한도에서 죽는다. 적재기는 묶음 단위로만 쓰므로 파일을 통째로 쥘 까닭이 없다.

`iter_array(path, "chunks")` 는 최상위 객체의 키를 차례로 풀어 가다 그 키의 배열을 만나면 원소를
하나씩 돌려준다. 다른 키의 값은 풀어서 버리고, 배열 뒤의 나머지도 끝까지 풀어 파일이 온전한지
확인한다 — 잘린 파일이나 꼴이 다른 파일은 원소를 덜 돌려준 채 조용히 끝나지 않고 예외를 낸다.
"""
import json
from contextlib import nullcontext
from pathlib import Path
from typing import Iterator, TextIO

_READ = 1 << 20
_WS = " \t\n\r"


class _Reader:
    def __init__(self, f):
        self.f = f
        self.buf = ""
        self.pos = 0
        self.eof = False
        self.dec = json.JSONDecoder()

    def _more(self) -> bool:
        if self.eof:
            return False
        s = self.f.read(_READ)
        if not s:
            self.eof = True
            return False
        self.buf = self.buf[self.pos:] + s
        self.pos = 0
        return True

    def peek(self) -> str:
        """공백을 건너뛴 다음 글자(파일 끝이면 빈 글)."""
        while True:
            while self.pos < len(self.buf) and self.buf[self.pos] in _WS:
                self.pos += 1
            if self.pos < len(self.buf) or not self._more():
                return self.buf[self.pos:self.pos + 1]

    def expect(self, ch: str):
        got = self.peek()
        if got != ch:
            raise ValueError(f"JSON 꼴이 다르다: '{ch}' 자리에 {got!r}")
        self.pos += 1

    def value(self):
        """다음 JSON 값 하나를 푼다. 값이 읽은 자리 끝에 걸쳐 있으면 더 읽고 다시 푼다."""
        self.peek()
        while True:
            try:
                obj, end = self.dec.raw_decode(self.buf, self.pos)
            except json.JSONDecodeError:
                if self._more():
                    continue
                raise
            # 숫자는 읽은 자리 끝에서 끊겨도 풀리므로, 끝에 닿았으면 더 읽어 보고 다시 푼다.
            if end == len(self.buf) and self._more():
                continue
            # 1e / 1. 는 raw_decode가 숫자 1만 먼저 풀 수 있다. 다음 글자가 값의
            # 구분자가 아니면 현재 조각 끝까지 더 읽은 뒤 온전한 JSON 수를 판정한다.
            if isinstance(obj, (int, float)) and not isinstance(obj, bool) and end < len(self.buf) and self.buf[end] not in _WS + ",]}:":
                if self._more():
                    continue
                raise ValueError("JSON 숫자 뒤에 잘못된 글이 있다")
            self.pos = end
            return obj


def iter_array(path: Path | TextIO, key: str) -> Iterator[dict]:
    """Read a path or a caller-owned text stream, including a gzip snapshot."""
    with (nullcontext(path) if hasattr(path, 'read') else open(path, "r", encoding="utf-8")) as f:
        r = _Reader(f)
        r.expect("{")
        found = False
        first = True
        seen_keys = set()
        while r.peek() != "}":
            if not first:
                r.expect(",")
            first = False
            k = r.value()
            if not isinstance(k, str):
                raise ValueError("JSON 객체의 키는 문자열이어야 한다")
            if k in seen_keys:
                raise ValueError(f"JSON 최상위 키가 중복되었다: {k!r}")
            seen_keys.add(k)
            r.expect(":")
            if k != key:
                r.value()
                continue
            found = True
            r.expect("[")
            if r.peek() == "]":
                r.pos += 1
                continue
            while True:
                yield r.value()
                if r.peek() == "]":
                    r.pos += 1
                    break
                r.expect(",")
        r.expect("}")
        if r.peek():
            raise ValueError("JSON 최상위 객체 뒤에 남은 글이 있다")
        if not found:
            raise KeyError(f"최상위 키 '{key}' 가 없다: {path}")
