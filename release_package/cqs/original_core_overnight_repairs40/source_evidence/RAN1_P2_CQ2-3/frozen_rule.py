"""Pure local replay of the exact retained-text query and original rank boundary.

Independent source-role adjudications remain evidence, not a marker classifier.
The lexical full pool is used only to reproduce the certified first15 frontier.
"""
import re


def cystr(s):
    return "'" + s.replace('\\', '\\\\').replace("'", "\\'") + "'"


def queries(patterns):
    prefix = ("MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#115'})\n"
              "WHERE (a.content CONTAINS 'CR' AND (a.content CONTAINS 'agreed' OR a.content CONTAINS 'approved'))\n"
              "   OR (a.content =~ " + cystr(patterns['approval']) + "\n"
              "       AND a.content =~ " + cystr(patterns['TP']) + "\n"
              "       AND (a.content =~ " + cystr(patterns['TS']) + "\n"
              "            OR a.content =~ " + cystr(patterns['named_TP_pointer']) + "))\n")
    return dict(limited=prefix + 'RETURN a.resolutionId, a.content\nORDER BY a.sequence, a.resolutionId\nLIMIT 15',
                full=prefix + 'RETURN a.resolutionId, a.content\nORDER BY a.sequence, a.resolutionId',
                rank=prefix + 'RETURN a.resolutionId, a.content, a.sequence AS __source_order_sequence\nORDER BY a.sequence, a.resolutionId')


def eligible(content, patterns):
    original = 'CR' in content and ('agreed' in content or 'approved' in content)
    matches = {k: bool(re.fullmatch(v, content)) for k, v in patterns.items()}
    return original or (matches['approval'] and matches['TP'] and (matches['TS'] or matches['named_TP_pointer']))


def replay(population, patterns):
    full = [{'a.resolutionId': r['resolutionId'], 'a.content': r['content'],
             '__source_order_sequence': r['sequence']}
            for r in population if eligible(r['content'], patterns)]
    full.sort(key=lambda r: (r['__source_order_sequence'], r['a.resolutionId']))
    return full, full[:15]
