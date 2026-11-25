#!/usr/bin/env python3
"""Slice generated script markers while retaining raw source ownership.

Spec: chunking_standards.md P7-V11; generated <sup>/<sub> search presentation.
Ontology: source text and script roles remain bound to their original interval.
Cycle: generated presentation → one parsed source map → independently balanced slices.
배경: 문자 수 기준 분할이 생성된 첨자 태그 중간을 자르는 경우를 처리한다.
사용: ScriptMarkup(text).slice(raw_start, raw_end); offsets are Python codepoints.
LLM 호출: 없음. No tokenizer, model, filesystem, or database calls.

Only the four exact, case-sensitive generated markers are formatting controls:
<sup>, </sup>, <sub>, </sub>. Every other character is literal, including '<',
'<=', entities, and other tag-like strings. Callers must know that these four
markers were generated; literal source text using the same spelling needs a
different representation. Malformed generated nesting raises ValueError.

A raw half-open interval owns the non-marker characters whose raw positions lie
inside it. A boundary inside a marker owns none of that marker's bytes. Rendering
closes and reopens the original role stack, so each result is balanced without
moving any source character across the requested boundary. A whole-source slice
retains the exact input bytes, including empty or adjacent redundant markers.
With no markers, slice() is exactly the native string slice. Token budgets and overlap policy
belong to the caller and must account for the rendered boundary markers.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
import re


_MARKER = re.compile(r"</?(?:sup|sub)>")


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """A non-marker source interval and its outer-to-inner script role stack."""

    raw_start: int
    raw_end: int
    roles: tuple[str, ...]


class ScriptMarkup:
    """Parse once; render source-owned slices in O(log spans + selected spans)."""

    __slots__ = ("_text", "_source_map", "_ends", "_has_markup")

    def __init__(self, text: str):
        if not isinstance(text, str):
            raise TypeError("ScriptMarkup text must be a string")
        spans: list[SourceSpan] = []
        stack: list[str] = []
        cursor = 0
        has_markup = False
        for marker in _MARKER.finditer(text):
            has_markup = True
            if cursor < marker.start():
                spans.append(SourceSpan(cursor, marker.start(), tuple(stack)))
            token = marker.group()
            closing = token[1] == "/"
            role = token[2:-1] if closing else token[1:-1]
            if closing:
                if not stack or stack[-1] != role:
                    raise ValueError(
                        f"Unmatched generated marker {token!r} at raw offset {marker.start()}"
                    )
                stack.pop()
            else:
                stack.append(role)
            cursor = marker.end()
        if stack:
            raise ValueError(f"Unclosed generated script roles: {tuple(stack)!r}")
        if cursor < len(text):
            spans.append(SourceSpan(cursor, len(text), ()))
        self._text = text
        self._source_map = tuple(spans)
        self._ends = tuple(span.raw_end for span in spans)
        self._has_markup = has_markup

    @property
    def text(self) -> str:
        """The exact supplied text, including generated markers."""
        return self._text

    @property
    def source_map(self) -> tuple[SourceSpan, ...]:
        """Immutable source spans; marker positions are absent, never reassigned."""
        return self._source_map

    @property
    def has_markup(self) -> bool:
        return self._has_markup

    def slice(self, raw_start: int | None = 0, raw_end: int | None = None) -> str:
        """Render text[raw_start:raw_end]'s owned characters with original roles.

        Negative and out-of-range bounds have Python string-slicing semantics.
        Boundaries in marker tokens are allowed. A whole-source interval retains
        the exact input. Other tag-only or reversed intervals produce an empty
        string. Each call reuses the constructor's source map.
        """
        if not self._has_markup:
            return self._text[raw_start:raw_end]
        start, end, _ = slice(raw_start, raw_end).indices(len(self._text))
        if start >= end:
            return ""
        if start == 0 and end == len(self._text):
            return self._text
        rendered: list[str] = []
        active: tuple[str, ...] = ()
        index = bisect_right(self._ends, start)
        while index < len(self._source_map):
            span = self._source_map[index]
            if span.raw_start >= end:
                break
            roles = span.roles
            shared = 0
            while shared < min(len(active), len(roles)) and active[shared] == roles[shared]:
                shared += 1
            rendered.extend(f"</{role}>" for role in reversed(active[shared:]))
            rendered.extend(f"<{role}>" for role in roles[shared:])
            rendered.append(self._text[max(start, span.raw_start):min(end, span.raw_end)])
            active = roles
            index += 1
        rendered.extend(f"</{role}>" for role in reversed(active))
        return "".join(rendered)
