"""Read the leading document identity in an explicitly described liaison field.

Spec: Phase-1 TDoc_List replyTo/originalLS reference identity.
Ontology: a descriptive LS title qualifies its leading document, not a new IRI.
Cycle: source reference cell -> canonical Tdoc endpoint -> reference validation.
Only observed leading-ID/optional-alias/LS-title syntax is resolved. Other external
document names and document numbers mentioned inside prose retain their identity.
"""
from __future__ import annotations

import re
from urllib.parse import unquote

_DESCRIBED_LS = re.compile(
    r'(?P<primary>R[1-5]-\d{6,8})\s+'
    r'(?:\(R[1-5]-\d{6,8}\)\s+)?'
    r'(?P<title>LS\s+(?:on|to|from)\s+\S.*)', re.I | re.S)
_OTHER_TDOC = re.compile(r'(?<![A-Za-z0-9])[A-Za-z][A-Za-z0-9]{1,3}-\s*\d+[A-Za-z]?(?![A-Za-z0-9])')


def described_liaison_target(value: str) -> str | None:
    """Resolve a cell's leading primary ID; never promote IDs within its title."""
    text = unquote(value).strip()
    for namespace in ('https://w3id.org/spectra#', 'tdoc:'):
        if text.startswith(namespace):
            text = text[len(namespace):]
            break
    match = _DESCRIBED_LS.fullmatch(text)
    if match is None or _OTHER_TDOC.search(match['title']):
        return None
    return match['primary'].upper()
