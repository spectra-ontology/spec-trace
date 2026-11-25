#!/usr/bin/env python3
"""ts_search_renderer.py — bind TS search rendering to one Word document.

Spec: Phase-7 source typography, complete equation captions and heading recovery.
Ontology: source roles are retained independently of heading and clause identity.
Cycle: document styles → scoped renderer → existing body/table extraction.
배경: primary quotation text remains suitable for heading recognition.
사용: @document_styles on a parser whose second argument is its DOCX path.
LLM 호출: 없음. Reads local styles.xml; source XML and default readers are preserved.
"""
from contextvars import ContextVar
from functools import wraps
from zipfile import ZipFile

from lxml import etree

import docx_text
from docx_search_fragments import search_fragment
from docx_search_styles import SearchStyles

_RENDER = ContextVar('ts_search_document_renderer', default=docx_text.search_text)


def read(paragraph):
    return _RENDER.get()(paragraph)


def fragment(paragraph, value):
    return search_fragment(paragraph, value, render=_RENDER.get())


def document_styles(function):
    """Scope styles with exception-safe reset, including concurrent parser calls."""
    @wraps(function)
    def wrapped(spec_number, docx_path, *args, **kwargs):
        with ZipFile(docx_path) as source:
            reader = SearchStyles(etree.fromstring(source.read('word/styles.xml'))).read
        token = _RENDER.set(reader)
        try:
            return function(spec_number, docx_path, *args, **kwargs)
        finally:
            _RENDER.reset(token)
    return wrapped
