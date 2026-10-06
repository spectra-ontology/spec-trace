"""Regex features used by the recorded query-composition analyses.

This is a surface parser, not a Cypher grammar or an execution validator. String
literals and function-call maps are excluded from node-pattern matching, and
inverse arrows are normalized to their directed endpoints.
"""
import re

STR_RE = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")
NODE_RE = re.compile(r'\(\s*([A-Za-z_][A-Za-z0-9_]*)?\s*'
                     r'((?::\s*[A-Za-z_][A-Za-z0-9_]*\s*)*)'
                     r'(\{[^{}]*\})?\s*\)')
CONN_RE = re.compile(r'(<-|-)\s*\[([^\[\]]*)\]\s*(->|-)')
REL_TYPE_RE = re.compile(r':\s*([A-Za-z_][A-Za-z0-9_|`\s]*)')
PATTERN_LEAD_KEYWORDS = {'match', 'merge', 'create'}
_LEAD_RE = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)\s*$')


def strip_strings(query):
    return STR_RE.sub("''", query or '')


def _labels_of_decl(decl):
    return re.findall(r':\s*([A-Za-z_][A-Za-z0-9_]*)', decl or '')


def node_matches(stripped):
    def is_call_map(match):
        if match.group(1) or (match.group(2) or '').strip() or not match.group(3):
            return False
        lead = _LEAD_RE.search(stripped[:match.start()])
        return bool(lead) and lead.group(1).lower() not in PATTERN_LEAD_KEYWORDS
    return [m for m in NODE_RE.finditer(stripped) if not is_call_map(m)]


def var_labels(stripped):
    labels = {}
    for match in node_matches(stripped):
        if match.group(1):
            labels.setdefault(match.group(1), set()).update(_labels_of_decl(match.group(2)))
    return labels


def node_labels(query):
    return {label for match in node_matches(strip_strings(query))
            for label in _labels_of_decl(match.group(2))}


def rel_types(query):
    out = set()
    for match in CONN_RE.finditer(strip_strings(query)):
        types = REL_TYPE_RE.search(match.group(2))
        if types:
            out.update(re.sub(r'\*.*$', '', t.strip().strip('`')).strip()
                       for t in types.group(1).split('|') if t.strip())
    return out


def parse_patterns(query):
    stripped = strip_strings(query)
    labels = var_labels(stripped)
    nodes = [(m.start(), m.end(), m.group(1), _labels_of_decl(m.group(2)))
             for m in node_matches(stripped)]
    triples = []
    for left, right in zip(nodes, nodes[1:]):
        _, end, variable_a, declared_a = left
        start, _, variable_b, declared_b = right
        between = stripped[end:start].strip()
        connector = CONN_RE.fullmatch(between)
        if connector:
            lhs, inner, rhs = connector.groups()
            arrow = ('left' if lhs == '<-' and rhs == '-'
                     else 'right' if lhs == '-' and rhs == '->' else 'undir')
            types_match = REL_TYPE_RE.search(inner)
            types = []
            if types_match:
                types = [re.sub(r'\*.*$', '', t.strip().strip('`')).strip()
                         for t in types_match.group(1).split('|')]
                types = [t for t in types if t]
            variable_length = '*' in inner
        elif re.fullmatch(r'-+>|<-+|--+', between):
            arrow = ('left' if between.startswith('<')
                     else 'right' if between.endswith('>') else 'undir')
            types, variable_length = [], False
        else:
            continue
        a = set(declared_a) | labels.get(variable_a, set())
        b = set(declared_b) | labels.get(variable_b, set())
        triples.append((b, types, a, variable_length, arrow) if arrow == 'left'
                       else (a, types, b, variable_length, arrow))
    return triples
