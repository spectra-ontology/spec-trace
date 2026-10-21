"""Replay the pure-Cypher operators on frozen records without graph access."""
from __future__ import annotations

import ast
import re


def patterns_from_query(query):
    literals = [ast.literal_eval(m.group()) for m in re.finditer(r"'(?:\\.|[^'\\])*'", query)]
    return {
        'proposal': next(s for s in literals if s.startswith('(?i)Proposal')),
        'header': next(s for s in literals if s.startswith('R2-[0-9]')),
        'previous': next(s for s in literals if s.startswith('(?i).*\\bCR')),
        'following': next(s for s in literals if s.startswith('(?i)(can')),
        'case': next(s for s in literals if s == 'case-[0-9]+'),
    }


def classify(row, query):
    pats = patterns_from_query(query)
    lines = (row['content'] or '').split('\n')
    header = lambda s: re.fullmatch(pats['header'], s.strip()) is not None
    proposal = lambda s: re.fullmatch(pats['proposal'], s.strip()) is not None
    boundaries = []
    headers = []
    for i, line in enumerate(lines):
        if header(line):
            headers.append(i)
        previous = next((p for p in reversed(lines[:i]) if p.strip()), '')
        following = next((p for p in lines[i + 1:] if p.strip()), '')
        embedded = (re.fullmatch(pats['previous'], previous) is not None and
                    re.fullmatch(pats['following'], following) is not None)
        if (i > 0 and proposal(line)) or (header(line) and not embedded):
            boundaries.append(i)
    own = lines[:boundaries[0] if boundaries else len(lines)]
    first = headers[0] if headers else None
    first_cells = lines[first].strip().split('\t') if first is not None else []
    joined = ' '.join([''] + own).lower()
    for char in '(),.:':
        joined = joined.replace(char, ' ')
    cases = [word for word in joined.split(' ') if re.fullmatch(pats['case'], word)]
    scopes = [i for i, line in enumerate(lines) if line.lower().startswith('scope:') and
              any('taking the conclusion for ' + token + ' into account' in line.lower() for token in cases)]
    direct = any(re.fullmatch(r'(?s).*(?<![A-Za-z0-9])' + row['tdocNumber'] + r'(?![0-9]).*', line)
                 is not None for line in own)
    family = (first is not None and not any(proposal(lines[i]) for i in range(1, first))
              and len(first_cells) >= 4 and first_cells[3].lower() in {'cr', 'draftcr', 'pcr'}
              and row['title'] == first_cells[1])
    scoped_family = False
    for scope in scopes:
        first_cr = next((j for j in range(scope + 1, len(lines)) if header(lines[j])
                         and len(lines[j].strip().split('\t')) >= 4
                         and lines[j].strip().split('\t')[3].lower() in {'cr', 'draftcr', 'pcr'}), None)
        if first_cr is not None and row['title'] == lines[first_cr].strip().split('\t')[1]:
            scoped_family = True
    return {'strict_direct_or_embedded': direct, 'same_first_CR_title_family': bool(family),
            'explicit_conclusion_scope_title_family': scoped_family,
            'provisional_eligible': direct or family or scoped_family}


def path_key(row):
    return tuple(row[k] for k in ('resolutionId', 'tdocNumber', 'specNumber'))


def project(row):
    return {field: row[key] for field, key in (
        ('r.resolutionId', 'resolutionId'), ('cr.tdocNumber', 'tdocNumber'),
        ('cr.clausesAffected', 'clausesAffected'), ('sp.specNumber', 'specNumber'))}


def replay(rows, query):
    candidates = [row for row in rows if classify(row, query)['provisional_eligible']]
    candidates.sort(key=path_key)
    selected = candidates[:10]
    cutoff = path_key(selected[-1])
    # This is the ORIGINAL universe, not the candidates list.
    frontier = [row for row in rows if path_key(row) <= cutoff]
    return {'full_projected_rows': [project(r) for r in candidates],
            'selected_projected_rows': [project(r) for r in selected],
            'original_frontier_path_rows': frontier,
            'selected_cutoff3key': list(cutoff)}
