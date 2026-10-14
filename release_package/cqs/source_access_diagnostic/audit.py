#!/usr/bin/env python3
"""Offline, question-selected source access audit. Never reads scores or gold.

Saved candidates and supplied context are observations, not fresh retrieval.
The optional FTS probes inspect a bounded source sample, without answering or
rerunning a model. Missing matches never certify global source absence.
"""
import argparse
import collections
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import time
import xml.etree.ElementTree as ET
import zipfile


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def excerpt(text, anchor, radius=700):
    pos = text.lower().find(anchor.lower())
    if pos < 0:
        return None
    return {'offset': pos, 'text': text[max(0, pos-radius):pos+len(anchor)+radius]}


def question_anchor(question):
    for pattern in [r'\bR[1-5]-\d{6,}\b', r'\bAGR-[\w.\-]+',
                    r'\b(?:TS|spec)\s+(\d{2}\.\d{3}(?:-\d+)?)',
                    r'\bWork Item\s+([A-Za-z0-9_\-]+)',
                    r'\bRAN[1-5]#\d+(?:bis)?', r'\bRel-\d+']:
        m = re.search(pattern, question, re.I)
        if m:
            return m.group(1) if m.lastindex else m.group(0)
    return None


def decision_fragments(text, tdoc):
    """Role-specific source evidence; forbid crossing a different TDoc entry."""
    fragments = []
    for match in re.finditer(re.escape(tdoc), text, re.I):
        # A predecessor mentioned in another contribution's "Replaces" field
        # is not the contribution whose following Decision is being recorded.
        if re.search(r'\b(?:Replaces|Revision\s+of)\s*$',text[max(0,match.start()-80):match.start()],re.I):
            continue
        window = text[match.end():match.end()+2000]
        decision = re.search(r'\bDecision\s*:\s*([^.!?\n]{1,180}[.!?]?)', window, re.I)
        if decision is None:
            continue
        between = window[:decision.start()]
        clean = re.sub(r'\(\s*Replaces\s+R[1-5]-\d+\s*\)', '', between, flags=re.I)
        if re.search(r'\bR[1-5]-\d{6,}\b', clean):
            continue
        end = match.end() + decision.end()
        fragments.append({'target_tdoc': tdoc, 'source_offset': match.start(),
                          'explicit_decision_text': decision.group(1).strip(),
                          'evidence': text[match.start():end],
                          'rule': 'Named TDoc followed by explicit Decision, no intervening other TDoc entry; revision predecessor in Replaces is auxiliary.'})
    return fragments


def role_support(text, task):
    anchor = question_anchor(task['question_en'])
    if task['diagnostic_type'] == 'named_document_attribute' and anchor:
        if 'decision status' in task['question_en'].lower():
            return decision_fragments(text, anchor)
        # A Contact role must be explicit; edit-author names are not Contact.
        evidence = []
        for m in re.finditer(r'\bContact(?:\s+person)?\s*[:=]\s*([^\n]{1,160})', text, re.I):
            if anchor.lower() in text[max(0, m.start()-1500):m.end()+1500].lower():
                evidence.append({'target_tdoc': anchor, 'explicit_contact_text': m.group(1),
                                 'evidence': text[max(0,m.start()-150):m.end()],
                                 'rule': 'Explicit Contact field adjacent to named contribution; not document-editor attribution.'})
        return evidence
    return []


def scan_context(artifact_dir, task):
    result = {'artifact_directory': str(artifact_dir), 'rounds': [],
              'candidate_literal_present': False, 'candidate_requested_role_fragments': [],
              'final_literal_present': False, 'final_requested_role_fragments': [],
              'full_requested_population_sufficient': 'UNESTABLISHED'}
    anchor = question_anchor(task['question_en'])
    for p in sorted(artifact_dir.glob('retrieval_round_*.json')):
        value = read_json(p)
        hits = value.get('hits', [])
        literal = []
        semantic = []
        for hit in hits:
            text = hit.get('snippet', '')
            header = json.dumps(hit.get('metadata', {}), ensure_ascii=False)
            if anchor and anchor.lower() in (header+'\n'+text).lower():
                literal.append({k:hit.get(k) for k in ['rank','collection','point_id','chunk_id','id']})
            for fragment in role_support(text, task):
                semantic.append({'source': {k:hit.get(k) for k in ['collection','point_id','chunk_id','id']}, **fragment})
        result['rounds'].append({'artifact': str(p), 'artifact_sha256': file_sha(p),
                                'status': value.get('status'), 'query': value.get('query'),
                                'matching_documents': value.get('matching_documents'),
                                'saved_candidate_n': len(hits),
                                'candidate_cap_truncated': value.get('context_candidate_truncated'),
                                'literal_witnesses': literal, 'requested_role_fragments': semantic})
        result['candidate_literal_present'] |= bool(literal)
        result['candidate_requested_role_fragments'].extend(semantic)
    p = artifact_dir/'final_context.json'
    if not p.exists():
        result['final_context_status'] = 'NOT_SAVED_OR_NOT_ISSUED'
        return result
    value = read_json(p)
    docs = value.get('documents', [])
    result.update(final_context_artifact=str(p), final_context_sha256=file_sha(p),
                  final_context_status='SAVED', final_document_n=len(docs),
                  final_stats=value.get('stats'), final_documents=[])
    for doc in docs:
        formatted = doc.get('formatted', '')
        if digest_bytes(formatted.encode()) != doc.get('formatted_sha256'):
            raise ValueError('saved formatted context SHA mismatch')
        txt = doc.get('text','')
        literal = bool(anchor and anchor.lower() in formatted.lower())
        fragments = role_support(txt, task)
        record = {k:doc.get(k) for k in ['collection','point_id','chunk_id','doc_row_id',
                                       'formatted_sha256','window_offsets',
                                       'full_text_characters','source_text_truncated','source_header_truncated']}
        record.update(question_anchor_literal_present=literal, requested_role_fragments=fragments,
                      question_anchor_excerpt=excerpt(formatted, anchor) if literal else None)
        result['final_documents'].append(record)
        result['final_literal_present'] |= literal
        result['final_requested_role_fragments'].extend([{'source': {k:doc.get(k) for k in ['collection','point_id','chunk_id']}, **f} for f in fragments])
    if task['diagnostic_type'] == 'named_document_attribute' and result['final_requested_role_fragments']:
        result['named_field_evidence_present'] = True
        result['sufficiency_limit'] = 'Explicit requested source role is supplied; full frozen-source identity/content equivalence must still be checked against located original source. No model correctness is inferred.'
    else:
        result['named_field_evidence_present'] = False
        result['sufficiency_limit'] = 'A finite context or identifier match cannot establish exhaustive list/count/rank/chain coverage. No complete source inventory aligned to the frozen graph was established here.'
    return result


def corpus_probe(conn, task, timeout=20):
    anchor = question_anchor(task['question_en'])
    if not anchor:
        return {'status':'NO_UNAMBIGUOUS_QUESTION_ANCHOR', 'source_presence':'UNKNOWN',
                'semantic_support':'UNESTABLISHED'}
    # A diagnostic literal probe, not a rerun of the frozen retrieval policy.
    sql = ('SELECT d.id,d.collection,d.point_id,d.chunk_id,d.metadata,d.text '
           'FROM search JOIN docs d ON d.id=search.rowid WHERE search MATCH ? LIMIT 33')
    expression = '"'+anchor.replace('"','""')+'"'
    start = time.monotonic()
    conn.set_progress_handler(lambda: int(time.monotonic()-start > timeout), 10000)
    output = {'anchor_from_original_question':anchor, 'sql':sql, 'parameters':[expression],
              'read_only':True, 'timeout_s':timeout, 'sample_cap':32,
              'semantic_support':'UNESTABLISHED', 'source_presence':'UNKNOWN'}
    try:
        cursor = conn.execute(sql,(expression,))
        rows = cursor.fetchall()
        output.update(status='OK', candidate_probe_truncated=len(rows)>32,
                      source_sample=[], selected_source_ids=[])
        for row in rows[:32]:
            metadata=json.loads(row[4]); text=row[5]
            witness={'row_id':row[0], 'collection':row[1], 'point_id':row[2], 'chunk_id':row[3],
                     'metadata':metadata,'full_text_sha256':digest_bytes(text.encode()),
                     'text_characters':len(text), 'literal_excerpt':excerpt(text,anchor),
                     'requested_role_fragments':role_support(text,task)}
            output['source_sample'].append(witness)
            if metadata.get('tdocNumber'):
                output['selected_source_ids'].append(metadata['tdocNumber'])
        exact_literal_n=sum(bool(r['literal_excerpt']) or anchor.lower() in json.dumps(r['metadata'],ensure_ascii=False).lower() for r in output['source_sample'])
        output['exact_anchor_literal_source_n']=exact_literal_n
        output['source_presence']=('EXACT_ANCHOR_LITERAL_IN_SAMPLED_CORPUS' if exact_literal_n else
                                   'TOKEN_MATCH_CANDIDATES_ONLY' if rows else 'NO_MATCH_IN_THIS_PROBE')
        output['requested_role_evidence_n']=sum(len(r['requested_role_fragments']) for r in output['source_sample'])
        output['semantic_support']='EXPLICIT_NAMED_ROLE_IN_CORPUS' if output['requested_role_evidence_n'] else 'UNESTABLISHED'
    except sqlite3.OperationalError as exc:
        output.update(status='INTERRUPTED' if 'interrupted' in str(exc) else 'ERROR', error=str(exc))
    output['elapsed_s']=round(time.monotonic()-start,6)
    return output


def read_docx(archive_path, task):
    result={'path':str(archive_path),'sha256':file_sha(archive_path),'members':[]}
    with zipfile.ZipFile(archive_path) as z:
        for info in z.infolist():
            if not info.filename.lower().endswith('.docx') or info.file_size>64*1024**2:
                continue
            raw=z.read(info)
            member={'name':info.filename,'sha256':digest_bytes(raw),'bytes':len(raw)}
            with zipfile.ZipFile(io.BytesIO(raw)) as doc:
                info2=doc.getinfo('word/document.xml')
                if info2.file_size>64*1024**2:
                    member['status']='XML_LIMIT';result['members'].append(member);continue
                xml=doc.read(info2)
                tree=ET.fromstring(xml)
                ns='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
                paragraphs=[''.join(t.text or '' for t in para.iter(ns+'t')) for para in tree.iter(ns+'p')]
                text='\n'.join(paragraphs)
                member.update(status='READ',xml_sha256=digest_bytes(xml), normalized_paragraph_text_sha256=digest_bytes(text.encode()),
                              requested_role_fragments=role_support(text,task),
                              question_anchor_excerpt=excerpt(text,question_anchor(task['question_en']) or ''))
            result['members'].append(member)
    return result


def locate_sources(root, source_files, task, corpus, methods):
    anchor=question_anchor(task['question_en'])
    ids=set()
    if anchor and re.fullmatch(r'R[1-5]-\d+',anchor):ids.add(anchor)
    # For named fields, inspect source documents that actually contain the role
    # in the corpus sample or model context, rather than irrelevant candidates.
    if task['diagnostic_type']=='named_document_attribute':
        for d in corpus.get('source_sample',[]):
            if d.get('requested_role_fragments') and d['metadata'].get('tdocNumber'):
                ids.add(d['metadata']['tdocNumber'])
        for m in methods.values():
            for d in m.get('final_documents',[]):
                if d.get('requested_role_fragments'):
                    td=re.match(r'R[1-5]-\d+',d.get('chunk_id') or '')
                    if td:ids.add(td.group(0))
    paths=[]
    for f in source_files:
        p=Path(f)
        if p.suffix.lower()!='.zip' or '/source/' not in f:
            continue
        if p.stem in ids:
            paths.append(p)
        elif task['diagnostic_type']=='spec_structure_inventory' and anchor and ('/TS/'+task['wg']+'/source/'+anchor+'/') in f:
            paths.append(p)
    paths=sorted(set(paths))
    result={'selection':'Original question identifiers and actual corpus/context source document identities; no gold/answer values.',
            'source_document_ids':sorted(ids),'archive_paths_found':[str(p) for p in paths],
            'source_archive_n':len(paths),'required_original_evidence':'UNESTABLISHED',
            'archives':[],'scope_limit':'Location is not extraction completeness or equality to frozen KG. Missing locator results do not prove archive absence.'}
    # Only named-field documents are decoded in this availability diagnostic.
    # Exhaustive source reconstruction is a separate parent-owned pipeline.
    for path in paths:
        if task['diagnostic_type']=='named_document_attribute':
            result['archives'].append(read_docx(path,task))
        else:
            result['archives'].append({'path':str(path),'sha256':file_sha(path),
                                      'bytes':path.stat().st_size,'content_decoded':False})
    fragments=[f for a in result['archives'] for m in a.get('members',[]) for f in m.get('requested_role_fragments',[])]
    result['named_role_fragments']=fragments
    if fragments:
        result['required_original_evidence']='EXPLICIT_NAMED_ROLE_LOCATED'
    elif paths:
        result['required_original_evidence']='SOURCE_FILES_LOCATED_SUPPORT_COMPLETENESS_UNESTABLISHED'
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--empirical',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert decision_fragments('R3-258530\nTitle\n(Replaces R3-257013)\nDecision: The document was not treated.','R3-258530')
    assert not decision_fragments('R3-261999\n(Replaces R3-258530)\nDecision: The document was noted.','R3-258530')
    assert not decision_fragments('R3-258530 body\nR3-261999\nDecision: Agreed.','R3-258530')
    if hasattr(os,'sched_getaffinity'):
        os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    protocol_path=args.output/'protocol.json'
    protocol=read_json(protocol_path)
    protocol_sha=file_sha(protocol_path)
    run=args.empirical/'runs/original-core-transport-supplement'
    inventory=read_json(run/'retrieval_corpus_inventory.json')
    shards={s['WG']:s for s in inventory['shards']}
    source_files=subprocess.check_output(['rg','--files',str(args.root/'data/corpus/tsg/RAN/formal'),'-g','*.zip'],text=True).splitlines()
    source_inventory_sha=digest_bytes(('\n'.join(sorted(source_files))+'\n').encode())
    records=[]
    source_guards=[]
    for wg in ['RAN1','RAN2','RAN3','RAN4','RAN5']:
        path=args.root/shards[wg]['path']
        before={'size':path.stat().st_size,'mtime_ns':path.stat().st_mtime_ns}
        if before!={'size':shards[wg]['bytes'],'mtime_ns':shards[wg]['mtime_ns']}:
            raise ValueError('corpus stat differs from frozen inventory')
        conn=sqlite3.connect(path.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
        conn.execute('PRAGMA query_only=ON');conn.execute('PRAGMA cache_size=-32768');conn.execute('PRAGMA threads=1');conn.execute('PRAGMA mmap_size=0')
        for task in protocol['selected']:
            if task['wg']!=wg:continue
            probe=corpus_probe(conn,task)
            methods={m:scan_context(run/'retrieval'/m/task['id'],task) for m in ['C','D']}
            original=locate_sources(args.root,source_files,task,probe,methods)
            role_values={f.get('explicit_decision_text') or f.get('explicit_contact_text') for f in original['named_role_fragments']}
            for m in methods.values():
                context_values={f.get('explicit_decision_text') or f.get('explicit_contact_text') for f in m['final_requested_role_fragments']}
                m['same_explicit_role_value_as_located_original']=bool(role_values and context_values and context_values<=role_values)
                if task['diagnostic_type']=='named_document_attribute' and m['same_explicit_role_value_as_located_original']:
                    m['full_requested_population_sufficient']='SUPPORTED_NAMED_SINGLE_FIELD_BY_MATCHED_ORIGINAL_TEXT'
                    m['sufficiency_limit']='The named source field is explicitly supplied and agrees with located original DOCX. This is source evidence support, not model correctness or graph-wide information equality.'
            record={**task,'question_anchor':question_anchor(task['question_en']),
                    'layer1_original_source':original,'layer2_retained_text_corpus':probe,
                    'layer3_and4_actual_candidates_context_and_sufficiency':methods,
                    'graph_corpus_identity_content_cutoff_equivalence':'UNKNOWN',
                    'model_scores_read':False,'gold_or_reference_read':False,
                    'new_model_calls':0,'new_frozen_retrieval_calls':0}
            records.append(record)
            print(json.dumps({'id':task['id'],'done':len(records),'n':protocol['unique_ID_n']}),flush=True)
        conn.close()
        after={'size':path.stat().st_size,'mtime_ns':path.stat().st_mtime_ns}
        if before!=after:raise ValueError('immutable corpus stat changed')
        source_guards.append({'wg':wg,'recorded_full_SHA_from_preexisting_inventory':shards[wg]['sha256'],
                              'before':before,'after':after,'stat_unchanged':True,
                              'full_corpus_rehash_in_this_diagnostic':False})
    if file_sha(protocol_path)!=protocol_sha:raise ValueError('selection protocol changed')
    report={'kind':'Actual offline question-selected four-layer source access diagnostic',
            'snapshot_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'protocol_sha256':protocol_sha,'tool_sha256':file_sha(__file__),
            'selected_denominator':protocol['unique_ID_n'],'completed_n':len(records),
            'source_path_inventory_sha256':source_inventory_sha,'source_archive_paths_n':len(source_files),
            'source_guards':source_guards,'corpus_inventory_sha256':file_sha(run/'retrieval_corpus_inventory.json'),
            'all_items_accounted':len(records)==protocol['unique_ID_n'],
            'new_paid_calls':0,'new_model_calls':0,'new_native_graph_queries':0,
            'new_diagnostic_read_only_FTS_probes':sum(r['layer2_retained_text_corpus'].get('status')!='NO_UNAMBIGUOUS_QUESTION_ANCHOR' for r in records),
            'score_replay_or_JSON_sensitivity':False,'human_or_expert_reviews':0,
            'source_cutoff_content_equivalence':'UNKNOWN','items':records,
            'limits':['Question-only audit selection fixed after original experiment, before new support audit; not preregistered original performance sampling.',
                      'Bounded literal FTS probes diagnose presence only; sample omission/timeout is not corpus or original-source absence.',
                      'Source identity/content/cutoff equality with the graph and exhaustive text population support remain unestablished.',
                      'Complete original-source answer reconstruction for population/structure/chain tasks is a separate pipeline, not claimed here.',
                      'Corpus files opened immutable/read-only, per-WG stat checked against frozen inventory. Preexisting full hashes are linked, not newly rehashed here.']}
    p=args.output/'report.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    summary={'protocol_sha256':protocol_sha,'report_sha256':file_sha(p),'tool_sha256':report['tool_sha256'],
             'selected_n':len(records),'types':dict(collections.Counter(r['diagnostic_type'] for r in records)),
             'named_source_role_located_n':sum(bool(r['layer1_original_source']['named_role_fragments']) for r in records),
             'corpus_explicit_named_role_n':sum(r['layer2_retained_text_corpus'].get('requested_role_evidence_n',0)>0 for r in records),
             'C_named_full_field_support_n':sum(r['layer3_and4_actual_candidates_context_and_sufficiency']['C'].get('full_requested_population_sufficient')=='SUPPORTED_NAMED_SINGLE_FIELD_BY_MATCHED_ORIGINAL_TEXT' for r in records),
             'D_named_full_field_support_n':sum(r['layer3_and4_actual_candidates_context_and_sufficiency']['D'].get('full_requested_population_sufficient')=='SUPPORTED_NAMED_SINGLE_FIELD_BY_MATCHED_ORIGINAL_TEXT' for r in records),
             'whole_population_support_certified_n':0,'new_model_calls':0,
             'limits':report['limits']}
    (args.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
