#!/usr/bin/env python3
"""pptx_search_text.py — source-preserving editable slide search text.

Spec: RAN5 Phase-6 native presentation source projection.
Ontology: slide locators and document identity stay with the retained source.
Cycle: DrawingML runs / editable a14 Choice / OMML → ordered search blocks.
배경: plain text getters omit editable math and explicit glyph/script roles.
사용: search_blocks(path); identity evidence continues to use native_blocks.
LLM 호출: 없음. Local XML and the maintained symbol / OMML readers only.

Explicit run baseline and Symbol font are supported. Inherited DrawingML
styles, geometry and image recognition are separate contracts. Unsupported
editable compatibility alternatives or nonempty groups fail closed.
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation

from docx_text import math_linear
import symbol_fonts

NS = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
      'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006'}
A, P, M, MC = ('{' + NS[k] + '}' for k in ('a', 'p', 'm', 'mc'))


def paragraph_text(paragraph):
    """Preserve text order and explicit run roles; linearize source OMML."""
    parts = []
    for node in paragraph:
        if node.tag in {A + 'r', A + 'fld'}:
            text = ''.join(t.text or '' for t in node.findall(A + 't'))
            properties = node.find(A + 'rPr')
            if properties is not None:
                font = properties.find(A + 'latin')
                if font is not None and font.get('typeface') == 'Symbol':
                    text = ''.join(symbol_fonts.glyph(symbol_fonts.table('Symbol'), ord(c)) or c
                                   for c in text)
                baseline = int(properties.get('baseline', '0'))
                if baseline and text:
                    role = 'sub' if baseline < 0 else 'sup'
                    text = f'<{role}>{text}</{role}>'
            parts.append(text)
        elif node.tag == A + 'br':
            parts.append('\v')  # Same soft-break character as python-pptx.
        elif node.tag == M + 'oMath':
            parts.append(math_linear(node))
        else:
            # The observed a14:m wrapper contains one direct OMML expression.
            parts.extend(math_linear(math) for math in node.findall(M + 'oMath'))
    return ''.join(parts)


def shape_paragraphs(shape):
    """Read the observed editable shapes once, retaining blank table cells."""
    if shape.tag == P + 'sp':
        body = shape.find(P + 'txBody')
        return [] if body is None else [paragraph_text(p) for p in body.findall(A + 'p')]
    if shape.tag == P + 'graphicFrame':
        tables = shape.findall('./' + A + 'graphic/' + A + 'graphicData/' + A + 'tbl')
        return [' | '.join('\n'.join(paragraph_text(p) for p in cell.findall('./' + A + 'txBody/' + A + 'p'))
                           for cell in row.findall(A + 'tc'))
                for table in tables for row in table.findall(A + 'tr')]
    if shape.tag == P + 'grpSp':
        if any((t.text or '').strip() for t in shape.iter() if t.tag in {A + 't', M + 't'}):
            raise ValueError('Unreviewed nonempty presentation group')
        return []
    if shape.tag == MC + 'AlternateContent':
        choices = shape.findall(MC + 'Choice')
        if (len(choices) != 1 or choices[0].get('Requires') != 'a14'
                or choices[0].nsmap.get('a14') != 'http://schemas.microsoft.com/office/drawing/2010/main'):
            raise ValueError('Unreviewed editable presentation compatibility choice')
        children = list(choices[0])
        if any(child.tag not in {P + 'sp', P + 'graphicFrame', P + 'grpSp'} for child in children):
            raise ValueError('Unsupported editable presentation choice content')
        return [text for child in children for text in shape_paragraphs(child)]
    return []


def search_blocks(path: Path):
    """Use presentation relationship order and the original slide locators."""
    result = {}
    for index, slide in enumerate(Presentation(path).slides, 1):
        tree = slide._element.find('./' + P + 'cSld/' + P + 'spTree')
        if tree is None:
            raise ValueError('Presentation slide lacks a shape tree')
        result[f'presentation slide {index}'] = '\n'.join(
            text for child in tree for text in shape_paragraphs(child))
    return result
