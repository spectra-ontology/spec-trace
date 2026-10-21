"""Frozen-field technical CR-object approval grammar; source IO is separate."""
import re

TRANSITION_PATTERN = r'^\s*(?:Decision\s*:|R3-[0-9]{6}[\t ]+\S)'
DIRECT_PREFIX = (r'\b(?:agree|approve|endorse|adopt)\s+'
                 r'(?:(?!\b(?:CRs?|and|or|but|to|if|unless|until)\b|R3-[0-9]{6})[^,.;:!?\n])*?\bCRs?\b'
                 r'\s*(?:in\s*)?\(?'
                 r'(?:R3-[0-9]{6}\s*(?:,|and|or)\s*)*')
DIRECT_SUFFIX = r'\b'
POST_PREFIX = r'\b'
POST_SUFFIX = (r'\b(?:\s*(?:,|and)\s*R3-[0-9]{6}\b)*'
               r'(?:\s*\([^.;:!?\n]*\))?\s*'
               r'(?:(?:is|are|was|were)\s+)?(?:agreed|approved|endorsed|adopted)\b')
PREVIOUS_PREFIX = r'\b(?:revision\s+of|replaces?|was|revised\s+from)\s+'
PREVIOUS_MIDDLE = r'\b|\b'
PREVIOUS_SUFFIX = r'\s+(?:rev\s+in|revised\s+to)\b'
NEGATED_PATTERN = (r'\b(?:not|never)\b[^.;]*\b'
                   r'(?:agree|agreed|approve|approved|endorse|endorsed|adopt|adopted)\b'
                   r'|^\s*no\s+CRs?\b')
CONDITIONAL_PATTERN = r'^\s*(?:if|unless|until)\b'
TRANSITION = re.compile(TRANSITION_PATTERN, re.I)
NEGATED = re.compile(NEGATED_PATTERN, re.I)
CONDITIONAL = re.compile(CONDITIONAL_PATTERN, re.I)

def technical_lines(content):
    out = []
    for line in (content or '').split('\n'):
        if TRANSITION.search(line):
            break
        out.append(line)
    return out

def approves(content, tdoc):
    target = re.escape(tdoc)
    direct = re.compile(DIRECT_PREFIX + target + DIRECT_SUFFIX, re.I)
    post = re.compile(POST_PREFIX + target + POST_SUFFIX, re.I)
    previous = re.compile(PREVIOUS_PREFIX + target + PREVIOUS_MIDDLE + target + PREVIOUS_SUFFIX, re.I)
    return any((direct.search(line) or post.search(line))
               and not previous.search(line)
               and not NEGATED.search(line)
               and not CONDITIONAL.search(line)
               for line in technical_lines(content))

def project(x):
    agreements = {row['node_id']: row for row in x['Agreement']}
    crs = {row['node_id']: row for row in x['CR']}
    selected, paths = {}, []
    for u, v in x['REFERENCES']:
        if u not in agreements or v not in crs:
            continue
        a, c = agreements[u], crs[v]
        if c['reasonForChange'] is not None and approves(a['content'], c['tdocNumber']):
            selected[v] = c
            paths.append({'resolutionId': a['resolutionId'], 'tdocNumber': c['tdocNumber'], 'CR_node_id': v})
    return sorted(selected.values(), key=lambda c: c['tdocNumber']), paths
