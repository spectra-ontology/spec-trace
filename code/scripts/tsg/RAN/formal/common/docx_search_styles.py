#!/usr/bin/env python3
"""docx_search_styles.py — document styles for opt-in Word search presentation.

Spec: WordprocessingML character/paragraph style inheritance and direct vertAlign.
Ontology: preserve source typography without assigning footnote or exponent meaning.
Cycle: resolve document styles → copy the search paragraph → render explicit roles.
배경: ordinary run text may inherit its superscript/subscript from styles.xml.
사용: SearchStyles(document.styles.element).read(paragraph_xml).
LLM 호출: 없음. Source XML and primary quotation readers remain unchanged.
"""
from __future__ import annotations

from copy import deepcopy

from lxml import etree

import docx_text

W = '{' + docx_text.W_NS + '}'
SCRIPT_ROLES = frozenset(('superscript', 'subscript'))


class SearchStyles:
    """Resolve visual script roles for one document, without modifying its XML.

    A direct baseline property overrides inherited script. Vertical position and
    font size do not establish a superscript/subscript role and are not inferred.
    """

    def __init__(self, styles):
        self._styles = {}
        self._resolved = {}
        self._default_paragraph = None
        self._default_character = None
        for style in styles.findall(W + 'style'):
            identity = style.get(W + 'styleId')
            if identity is None:
                raise ValueError('Word style without an identity')
            if identity in self._styles:
                raise ValueError('Duplicate Word style identity: ' + str(identity))
            parent = style.find(W + 'basedOn')
            role = style.find(W + 'rPr/' + W + 'vertAlign')
            self._styles[identity] = (
                parent.get(W + 'val') if parent is not None else None,
                role.get(W + 'val') if role is not None else None,
            )
            if style.get(W + 'default') in ('1', 'true', 'on'):
                if style.get(W + 'type') == 'paragraph':
                    self._default_paragraph = identity
                elif style.get(W + 'type') == 'character':
                    self._default_character = identity
        default = styles.find(W + 'docDefaults/' + W + 'rPrDefault/' + W + 'rPr/' + W + 'vertAlign')
        self._document_default = default.get(W + 'val') if default is not None else None

    def _role(self, identity, seen=()):
        if identity in self._resolved:
            return self._resolved[identity]
        if identity not in self._styles:
            return None
        if identity in seen:
            raise ValueError('Cycle in Word script style inheritance: ' + str(identity))
        parent, direct = self._styles[identity]
        role = direct if direct is not None else self._role(parent, seen + (identity,))
        self._resolved[identity] = role
        return role

    def _inherited_role(self, paragraph, run):
        direct = run.find(W + 'rPr/' + W + 'vertAlign')
        if direct is not None:
            return None
        style = run.find(W + 'rPr/' + W + 'rStyle')
        role = self._role(style.get(W + 'val') if style is not None else self._default_character)
        if role is None:
            style = paragraph.find(W + 'pPr/' + W + 'pStyle')
            role = self._role(style.get(W + 'val') if style is not None else self._default_paragraph)
        return self._document_default if role is None else role

    def read(self, paragraph, *, deleted=docx_text.DROP):
        paragraph = getattr(paragraph, '_p', paragraph)
        roles = []
        for index, run in enumerate(paragraph.iter(W + 'r')):
            owner = run.getparent()
            while owner is not None and owner.tag != W + 'p':
                owner = owner.getparent()
            role = self._inherited_role(owner if owner is not None else paragraph, run)
            if role in SCRIPT_ROLES:
                roles.append((index, role))
        if not roles:
            return docx_text.search_text(paragraph, deleted=deleted)
        copy = deepcopy(paragraph)
        runs = list(copy.iter(W + 'r'))
        for index, role in roles:
            properties = runs[index].find(W + 'rPr')
            if properties is None:
                properties = etree.Element(W + 'rPr')
                runs[index].insert(0, properties)
            alignment = etree.SubElement(properties, W + 'vertAlign')
            alignment.set(W + 'val', role)
        return docx_text.search_text(copy, deleted=deleted)
