#!/usr/bin/env python3
"""docx_search_fragments.py — search roles for a recovered Word source fragment.

Spec: TS heading recovery; source-bound search presentation of recovered lead text.
Ontology: keep source typography separate from clause identity and interpretation.
Cycle: check the actual quotation → project the actual search roles → fail closed.
배경: 제목 문단에서 분리한 NOTE 문자열도 실제 원문의 첨자 역할을 보존한다.
사용: search_fragment(paragraph_xml, recovered_lead, render=styles.read).
LLM 호출: 없음. No source, producer, artifact, model or database writes.

The caller owns heading acceptance and clause allocation. This helper does not
infer either. Primary quotation and default chunk readers remain unchanged.
Fragments spanning omitted equations must be handled from their source XML;
this helper rejects an unmatched fragment rather than drop the equation.
"""
from __future__ import annotations

import docx_text
from ts_search_presentation import normalize, project, source_info


class SourceFragmentMismatch(ValueError):
    """The recovered string cannot be bound to one actual source presentation."""


def search_fragment(paragraph, fragment: str, *, render=docx_text.search_text) -> str:
    """Keep the fragment's exact characters and add actual source script roles.

    All matching occurrences in the paragraph must have the same presentation.
    ``render`` may be a document-bound ``SearchStyles.read`` function. Generated
    markup is accepted only after its plain text equals the default chunk view.
    Literal marker-like source text is therefore rejected, rather than stripped.
    """
    if not fragment.strip():
        return fragment
    paragraph = getattr(paragraph, '_p', paragraph)
    normalized, mapping = normalize(fragment)
    quotation, _ = normalize(docx_text.final_text(paragraph))
    if normalized not in quotation:
        raise SourceFragmentMismatch('fragment is absent from the actual primary quotation')
    plain, source, roles = source_info(render(paragraph))
    if plain != docx_text.chunk_text(paragraph):
        raise SourceFragmentMismatch('search markup does not preserve the source chunk view')
    result, status = project(fragment, normalized, mapping, source, roles)
    if result is None:
        raise SourceFragmentMismatch('source fragment presentation: ' + status)
    return result['text']
