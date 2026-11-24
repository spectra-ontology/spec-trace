import json, re, collections, gc, sys

def load(path):
    with open(path) as f:
        return json.load(f)['@graph']

def many(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]

def docname(uri):
    assert uri.startswith('tdoc:R5-'), uri
    return uri[len('tdoc:'):]

def section_parts(uri):
    m = re.fullmatch(r'tdoc:section/(.+)-Rel-(\d+)-(.+)', uri)
    assert m, uri
    return m.groups()

with open('questions.jsonl') as f:
    questions = [json.loads(s) for s in f]
meetings = {r['@id']: r['tdoc:meetingNumber'] for r in load('records/phase-1/meetings.jsonld')}
releases = {r['@id']: r['tdoc:releaseName'] for r in load('records/phase-1/releases.jsonld')}
packs = {}
member_packs = collections.defaultdict(set)
for r in load('records/phase-4/crpacks.jsonld'):
    packs[r['@id']] = (r['tdoc:crPackId'], r['tdoc:tsgMeeting'], tuple(many(r['hasCR'])))
    for d in many(r['hasCR']):
        member_packs[d].add(r['@id'])
sections = {}
for r in load('records/phase-4/section_extensions.jsonld'):
    sections[r['@id']] = set(many(r['modifiedByCR']))
cr_sections = {}
cr_packs = {}
for r in load('records/phase-4/cr_extensions.jsonld'):
    cr_sections[r['@id']] = set(many(r.get('modifiesSection')))
    cr_packs[r['@id']] = set(many(r.get('belongsToCRPack')))
assert dict(member_packs) == cr_packs
section_reverse = collections.defaultdict(set)
for s, ds in sections.items():
    for d in ds:
        section_reverse[d].add(s)
assert dict(section_reverse) == {d: ss for d, ss in cr_sections.items() if ss}

keep_keys = ['tdoc:tdocNumber', 'tdoc:type', 'tdoc:status', 'tdoc:crNumber', 'tdoc:crRevision', 'targetRelease', 'modifies', 'revisedTo', 'isRevisionOf', 'presentedAt', 'tdoc:tsgCRPack', 'tdoc:clausesAffected']
tdocs = {}
forward = collections.defaultdict(set)
link_origin = collections.defaultdict(set)
graph = load('records/phase-1/tdocs.jsonld')
for r in graph:
    tdocs[r['@id']] = {k: r[k] for k in keep_keys if k in r}
    for new in many(r.get('revisedTo')):
        forward[r['@id']].add(new)
        link_origin[(r['@id'],new)].add('revisedTo')
    for old in many(r.get('isRevisionOf')):
        forward[old].add(r['@id'])
        link_origin[(old,r['@id'])].add('isRevisionOf')
del graph
gc.collect()

valid = collections.defaultdict(list)
rejected = collections.defaultdict(list)
all_disposition_codes = set()
graph = load('records/phase-2/decision_dispositions.jsonld')
for r in graph:
    a = json.loads(r['assessmentMethod'])
    all_disposition_codes.add(r['dispositionCode'])
    info = (r['dispositionCode'], r['dispositionOf'], r['evidenceStatus'], a.get('scope'))
    assert r['targetTdocNumber'] == docname(r['dispositionTarget'])
    if r['evidenceStatus'] == 'source_verified' and a.get('scope') == 'whole_target':
        valid[r['dispositionTarget']].append(info)
    else:
        rejected[r['dispositionTarget']].append(info)
del graph
gc.collect()

needed_events = {v[1] for vs in valid.values() for v in vs}
events = {}
for path in ['records/phase-2/resolutions_document_dispositions.jsonld','records/phase-2/resolutions_conclusions.jsonld','records/phase-2/discussions.jsonld']:
    graph = load(path)
    for r in graph:
        if r['@id'] in needed_events:
            events[r['@id']] = {k:r[k] for k in ['madeAt','resolutionScope','aboutTdoc','references'] if k in r}
    del graph
    gc.collect()
assert needed_events <= events.keys(), needed_events-events.keys()

def descendants(start):
    seen = set()
    pending = list(forward.get(start, []))
    while pending:
        d = pending.pop()
        if d in seen:
            continue
        seen.add(d)
        pending.extend(forward.get(d, []))
    assert start not in seen, start
    return seen

def decisions(d):
    return sorted({(code, meetings[events[event]['madeAt']]) for code, event, status, scope in valid.get(d,[])})

def packinfo(d):
    return sorted({packs[p][:2] for p in member_packs.get(d, [])})

def get_q_doc(q):
    return 'tdoc:' + re.search(r'R5-\d+', q['question']).group()

def clause_candidates(spec, clause, inclusive=False):
    result = set()
    matched = []
    for s, ds in sections.items():
        sp, rel, cl = section_parts(s)
        if sp == spec and (cl == clause or (inclusive and cl.startswith(clause+'.'))):
            result.update(ds)
            matched.append(s)
    return result, matched

def compute():
    answers = []
    diagnostics = []
    for q in questions:
        text = q['question']
        rows = []
        note = ''
        diag = {'id': q['id']}
        if text.startswith('Which Rel-'):
            rel, clause, spec = re.search(r'Which (Rel-\d+) change requests that modify clause (\S+) of TS (\S+)', text).groups()
            candidates, nodes = clause_candidates(spec, clause)
            inclusive, incl_nodes = clause_candidates(spec, clause, True)
            eligible = {d for d in candidates if tdocs.get(d,{}).get('tdoc:type') == 'CR' and releases.get(tdocs.get(d,{}).get('targetRelease')) == rel}
            def rows_for(ds):
                return sorted({(docname(d),code,meeting,pack) for d in ds
                    if tdocs.get(d,{}).get('tdoc:type') == 'CR' and releases.get(tdocs.get(d,{}).get('targetRelease')) == rel
                    for code,meeting in decisions(d) for pack,tsg in packinfo(d)})
            rows = rows_for(eligible)
            incl_rows = rows_for(inclusive)
            section_rel_rows = sorted({(docname(d),code,meeting,pack) for s in nodes if section_parts(s)[1] == rel.removeprefix('Rel-') for d in sections[s] for code,meeting in decisions(d) for pack,tsg in packinfo(d)})
            diag.update(kind='clause',nodes=nodes, candidates=[(docname(d),tdocs.get(d,{}).get('targetRelease'),decisions(d),packinfo(d)) for d in sorted(candidates)], descendant_nodes=len(incl_nodes),descendant_row_count=len(incl_rows),descendant_rows_added=sorted(set(incl_rows)-set(rows)),section_release_rows=section_rel_rows)
            if set(incl_rows) != set(rows):
                added = len(set(incl_rows)-set(rows))
                note = 'Interpreted \"modify clause '+clause+'\" as an explicit link to that exact clause. Including subclauses is another reasonable reading and would add '+str(added)+(' row.' if added == 1 else ' rows.')
            else:
                note = 'Used explicit links to the exact numbered clause. Reading the clause as including its subclauses gives the same rows in these records.'
            if set(section_rel_rows) != set(rows):
                rel_note = 'Interpreted '+rel+' as the CR targetRelease, rather than the release embedded in the linked section identifier; those filters give different rows.'
                note = (note+' '+rel_note).strip()
        elif text.startswith('TSG RAN CR pack'):
            pack = 'tdoc:crpack/' + re.search(r'RP-\d+',text).group()
            rows = sorted({(docname(d),code,meeting) for d in packs[pack][2] for code,meeting in decisions(d)})
            diag.update(kind='pack_members',pack=pack,members=len(packs[pack][2]),excluded=[(docname(d),rejected.get(d,[])) for d in packs[pack][2] if not decisions(d)])
        elif 'Follow its revisions' in text:
            start = get_q_doc(q)
            later = descendants(start)
            rows = sorted({(docname(d),code,pack) for d in later for code,meeting in decisions(d) for pack,tsg in packinfo(d)})
            diag.update(kind='revisions',start=docname(start),later=[(docname(d),tdocs.get(d),decisions(d),packinfo(d)) for d in sorted(later)],edges=[(docname(old),docname(new),sorted(link_origin[(old,new)])) for old in {start}|later for new in forward.get(old,[])])
            nonleaf_rows = [r for r in rows if forward.get('tdoc:'+r[0])]
            if not nonleaf_rows:
                note = 'Followed all forward revision links transitively, excluding the starting document. A reading limited to terminal revisions gives the same rows here.'
            else:
                note = 'Interpreted "every later version" as all documents reachable through revision links, including intermediate versions. A terminal-version-only reading would exclude '+', '.join(sorted({r[0] for r in nonleaf_rows}))+'.'
        elif text.startswith('In which TSG'):
            d = get_q_doc(q)
            rows = packinfo(d)
            later = descendants(d)
            diag.update(kind='pack_lookup',doc=docname(d),metadata=tdocs.get(d),later=[(docname(x),tdocs.get(x),packinfo(x)) for x in sorted(later)])
            if not rows:
                statuses = decisions(d)
                withdrawn = [m for c,m in statuses if c == 'withdrawn']
                note = 'No CR pack membership is recorded for the named document.'
                if withdrawn:
                    note += ' It has a source-verified whole-document withdrawn disposition at '+', '.join(withdrawn)+'. The question presupposes a submission that the records do not establish.'
        else:
            d = get_q_doc(q)
            base = {(code,meeting,pack,tsg) for code,meeting in decisions(d) for pack,tsg in packinfo(d)}
            if text.startswith('Trace change request'):
                spec = re.search(r'to TS (\d+\.\d+-\d+)',text).group(1)
                clauses = {section_parts(s)[2] for s in cr_sections.get(d,[]) if section_parts(s)[0] == spec}
                rows = sorted({row+(clause,) for row in base for clause in clauses})
                diag.update(kind='trace',doc=docname(d),sections=sorted(cr_sections.get(d,[])),metadata=tdocs.get(d))
                target_rel = releases.get(tdocs.get(d,{}).get('targetRelease'))
                linked_rels = sorted({'Rel-'+section_parts(s)[1] for s in cr_sections.get(d,[]) if section_parts(s)[0] == spec})
                if linked_rels and target_rel and any(rel != target_rel for rel in linked_rels):
                    note = 'The CR targets '+target_rel+', while its linked section identifiers carry '+', '.join(linked_rels)+'. Used the clause numbers from the explicit modification links; the question specifies no release.'
            else:
                rows = sorted(base)
                diag.update(kind='decision_pack',doc=docname(d))
            if not rows:
                note = 'No complete row satisfies the required joins in the supplied records.'
                diag.update(valid=valid.get(d,[]),rejected=rejected.get(d,[]),packs=packinfo(d))
        answers.append({'id':q['id'],'rows':[list(row) for row in rows],'note':note})
        diagnostics.append(diag)
    return answers, diagnostics

if __name__ == '__main__':
    answers, diagnostics = compute()
    if '--write' in sys.argv:
        with open('answers.jsonl','w') as f:
            for a in answers:
                f.write(json.dumps(a,ensure_ascii=False)+'\n')
    for a,d in zip(answers,diagnostics):
        print(json.dumps({'answer':a,'diagnostic':d},ensure_ascii=False))
