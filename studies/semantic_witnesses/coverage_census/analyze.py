#!/usr/bin/env python3
"""Post-review author analysis of every frozen witness candidate, using raw data.

No study implementation imports, SQL generation, new selection or model calls.
The review files one directory above are treated as immutable inputs.
"""
import ast
import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile
import time

P = D = E = CODE = None

def canon(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def load(p):
    return json.loads(p.read_text())

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def save(p,x):
    p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n')

def short(s):return s[0],s[2]

GATES = {
 'pack_multicode':['multiple_codes'],
 'pack_duplicates':['duplicate_count'],
 'pack_multicode_duplicates':['multiple_codes','duplicate_count'],
 'meeting_multicode':['multiple_codes'],
 'meeting_duplicates':['duplicate_count'],
 'meeting_multicode_duplicates':['multiple_codes','duplicate_count'],
 'intersection':['three_nonempty_regions'],
 'intersection_release':['three_nonempty_regions','release_collision'],
 'difference':['three_nonempty_regions'],
 'difference_release':['three_nonempty_regions','release_collision'],
 'conjunction':['three_nonempty_regions'],
 'conjunction_release':['three_nonempty_regions','release_collision'],
 'maximum_variation':['positive_count_variation'],
 'maximum_ties':['positive_count_variation','ties'],
 'maximum_release_count':['positive_count_variation','release_count_result_changes'],
 'maximum_release_winner':['positive_count_variation','release_winner_set_changes'],
 'maximum_ties_release':['positive_count_variation','ties','release_count_result_changes'],
 'absence':['mixed_presence_absence'],
 'composition':['three_nonempty_regions','nonempty_histogram','or_changes_histogram']
}

DEFINITIONS = {
 'multiple_codes':'At least two disposition codes have at least one distinct document in the cohort.',
 'duplicate_count':'At least one code has more raw joined disposition rows than distinct documents; pack membership multiplicity is retained.',
 'three_nonempty_regions:document_pair':'L intersection R, L minus R and R minus L are all nonempty typed-section sets.',
 'three_nonempty_regions:section_pair':'The pack contains at least one document in each of B1 intersection B2, B1 minus B2 and B2 minus B1.',
 'release_collision:document_pair':'Some typed section in L minus R has its (spec,clause) projection in the other document R.',
 'release_collision:section_pair':'Broad document conjunction using only (spec,clause) strictly contains the full-typed conjunction.',
 'positive_count_variation':'At least two distinct strictly positive typed footprint sizes occur among pack members.',
 'ties':'At least two pack members attain the largest typed footprint size.',
 'release_count_result_changes':'The complete (document,maximum count) rowset differs after projecting away release before distinct counting.',
 'release_winner_set_changes':'The maximizing document set differs after projecting away release before distinct counting.',
 'mixed_presence_absence':'At least one pack member has no recorded section link and at least one has a recorded section link.',
 'nonempty_histogram':'The conjunction-selected documents have at least one source_verified whole_target disposition.',
 'or_changes_histogram':'The per-code distinct-document histogram differs between conjunction-selected and disjunction-selected documents.'
}

def raw(c):
    members=defaultdict(set); multiplicity=Counter()
    for doc,p in c.execute('SELECT cr,pack_id FROM cr_in_pack'):
        members[p].add(doc);multiplicity[p,doc]+=1
    ids={r[0]:tuple(r[1:]) for r in c.execute('SELECT id,spec,release,clause FROM section')}
    assert all(all(x is not None for x in s) for s in ids.values())
    links=defaultdict(set);link_rows=Counter()
    for doc,identity in c.execute('SELECT cr,section_id FROM cr_modifies_section'):
        assert identity in ids
        links[doc].add(ids[identity]);link_rows[doc,identity]+=1
    resolutions=dict(c.execute('SELECT id,meeting_id FROM resolution'))
    doc_codes=defaultdict(Counter);meeting_records=defaultdict(list)
    for doc,code,res in c.execute("SELECT target,code,resolution_id FROM disposition WHERE evidence_status='source_verified' AND scope='whole_target'"):
        doc_codes[doc][code]+=1;meeting_records[resolutions[res]].append((doc,code))
    return {'members':members,'multiplicity':multiplicity,'ids':ids,'links':links,'link_rows':link_rows,
            'resolutions':resolutions,'doc_codes':doc_codes,'meeting_records':meeting_records}

def histogram(r,docs,pack=None):
    counts=Counter();nraw=Counter()
    for doc in docs:
        counts.update(r['doc_codes'][doc].keys())
        m=1 if pack is None else r['multiplicity'][pack,doc]
        for code,n in r['doc_codes'][doc].items():nraw[code]+=m*n
    return dict(counts),{code:nraw[code]-n for code,n in counts.items()}

def generated(r,preuniverse):
    """Re-enumerate exactly the frozen universe and recompute all witness flags."""
    M,L=r['members'],r['links']
    for kind,cohorts in [('pack',sorted(M)),('meeting',sorted(r['meeting_records']))]:
        for cohort in cohorts:
            if kind=='pack':counts,excess=histogram(r,M[cohort],cohort)
            else:
                pairs=r['meeting_records'][cohort]
                groups=defaultdict(set);nraw=Counter(code for _,code in pairs)
                for doc,code in pairs:groups[code].add(doc)
                counts={code:len(ds) for code,ds in groups.items()}
                excess={code:nraw[code]-n for code,n in counts.items()}
            props={'code_counts':counts,'raw_duplicate_excess_by_code':excess,'code_groups':len(counts),'raw_duplicate_excess':sum(excess.values())}
            a=[kind,cohort];multi=len(counts)>=2;dup=any(n>0 for n in excess.values())
            yield f'{kind}_multicode',a,props,{'multiple_codes':multi},None
            yield f'{kind}_duplicates',a,props,{'duplicate_count':dup},None
            yield f'{kind}_multicode_duplicates',a,props,{'multiple_codes':multi,'duplicate_count':dup},None
    for pack,docs in sorted(M.items()):
        bysection=defaultdict(set);byshort=defaultdict(set)
        for doc in docs:
            for s in L[doc]:bysection[s].add(doc);byshort[short(s)].add(doc)
        pairset=set()
        for ds in bysection.values():pairset.update(itertools.combinations(sorted(ds),2))
        # Release aliases outside the frozen shared-typed candidate restriction
        # are measured separately; zero inside that universe is not global zero.
        release_groups=defaultdict(lambda:defaultdict(set))
        for s,ds in bysection.items():release_groups[short(s)][s[1]].update(ds)
        all_collision_pairs=set()
        for groups in release_groups.values():
            for ds1,ds2 in itertools.combinations(groups.values(),2):
                all_collision_pairs.update(tuple(sorted((d1,d2))) for d1 in ds1 for d2 in ds2 if d1!=d2)
        preuniverse['document_pairs_before_shared_typed_identity']+=math.comb(len(docs),2)
        preuniverse['document_pairs_with_shared_typed_identity']+=len(pairset)
        preuniverse['document_pairs_release_collision_before_shared_identity_gate']+=len(all_collision_pairs)
        preuniverse['document_pairs_release_collision_after_shared_identity_gate']+=len(pairset&all_collision_pairs)
        for first,second in sorted(pairset):
            left,right=L[first],L[second];common=left&right;lo=left-right;ro=right-left
            basic=bool(common and lo and ro)
            props={'intersection_size':len(common),'first_only_size':len(lo),'second_only_size':len(ro)}
            falseleft=sorted(s for s in lo if short(s) in {short(t) for t in right})
            yield 'intersection',[pack,first,second],props,{'three_nonempty_regions':basic},None
            yield 'intersection_release',[pack,first,second],dict(props,release_blind_extra_sections=falseleft),{'three_nonempty_regions':basic,'release_collision':bool(falseleft)},None
            for a,b in [(first,second),(second,first)]:
                oneonly=L[a]-L[b];twoshort={short(t) for t in L[b]}
                falseone=sorted(s for s in oneonly if short(s) in twoshort)
                props2={'intersection_size':len(common),'first_only_size':len(oneonly),'second_only_size':len(L[b]-L[a])}
                yield 'difference',[pack,a,b],props2,{'three_nonempty_regions':basic},None
                yield 'difference_release',[pack,a,b],dict(props2,release_blind_removed_sections=falseone),{'three_nonempty_regions':basic,'release_collision':bool(falseone)},None
        section_pairs=set()
        for doc in docs:section_pairs.update(itertools.combinations(sorted(L[doc]),2))
        preuniverse['section_pairs_before_document_cooccurrence']+=math.comb(len(bysection),2)
        preuniverse['section_pairs_with_document_cooccurrence']+=len(section_pairs)
        for one,two in sorted(section_pairs):
            a,b=bysection[one],bysection[two];both=a&b;ao=a-b;bo=b-a
            basic=bool(both and ao and bo)
            props={'both_documents':len(both),'first_only_documents':len(ao),'second_only_documents':len(bo),'neither_documents':len(docs-a-b)}
            anchor=[pack,one,two]
            yield 'conjunction',anchor,props,{'three_nonempty_regions':basic},None
            broad=byshort[short(one)]&byshort[short(two)]
            rawcollision=broad!=both
            # The frozen enumerator stores a false flag/empty extra list when
            # the preceding basic gate fails. Retain that exact file contract.
            archiveextra=sorted(broad-both) if basic else []
            yield 'conjunction_release',anchor,dict(props,release_blind_extra_documents=archiveextra),{'three_nonempty_regions':basic,'release_collision':basic and rawcollision},{'release_collision':rawcollision}
            hc,_=histogram(r,both,pack);ho,_=histogram(r,a|b,pack)
            yield 'composition',anchor,dict(props,conjunction_code_counts=hc,or_code_counts=ho),{'three_nonempty_regions':basic,'nonempty_histogram':bool(hc),'or_changes_histogram':hc!=ho},None
        counts={d:len(L[d]) for d in docs};positive=sorted({n for n in counts.values() if n>0});varied=len(positive)>=2
        high=max(counts.values());winners={d:n for d,n in counts.items() if n==high}
        collapsed={d:len({short(s) for s in L[d]}) for d in docs};lowhigh=max(collapsed.values());lowwinners={d:n for d,n in collapsed.items() if n==lowhigh}
        ties=len(winners)>=2;changed=winners!=lowwinners;winnerchanged=set(winners)!=set(lowwinners)
        props={'members':len(docs),'positive_count_values':positive,'typed_counts':counts,'typed_maximum':high,'typed_winners':winners,'release_collapsed_counts':collapsed,'release_collapsed_maximum':lowhigh,'release_collapsed_winners':lowwinners,'winner_set_changed':winnerchanged,'result_set_changed':changed,'ties':len(winners)}
        for st,flags in [
            ('maximum_variation',{'positive_count_variation':varied}),
            ('maximum_ties',{'positive_count_variation':varied,'ties':ties}),
            ('maximum_release_count',{'positive_count_variation':varied,'release_count_result_changes':changed}),
            ('maximum_release_winner',{'positive_count_variation':varied,'release_winner_set_changes':winnerchanged}),
            ('maximum_ties_release',{'positive_count_variation':varied,'ties':ties,'release_count_result_changes':changed})]:
            yield st,[pack],props,flags,None
        absent={d for d in docs if not L[d]}
        yield 'absence',[pack],{'zero_link_members':len(absent),'positive_link_members':len(docs-absent)},{'mixed_presence_absence':bool(absent and docs-absent)},None

def source_audit(c,r,wg):
    graphpath=P/('records/RAN5_graph_export/RAN5/cr_extensions.jsonld' if wg=='RAN5' else f'records/phase-4/{wg}/cr_extensions.jsonld')
    g=load(graphpath)['@graph'];source_links=Counter();source_members=Counter();idcounts=Counter()
    def items(x):return [] if x is None else x if isinstance(x,list) else [x]
    for rec in g:
        doc=rec['@id'];idcounts[doc]+=1
        source_links.update((doc,s) for s in dict.fromkeys(items(rec.get('modifiesSection'))))
        source_members.update((doc,p) for p in dict.fromkeys(items(rec.get('belongsToCRPack'))))
    assert source_links==r['link_rows']
    assert source_members==Counter({(d,p):n for (p,d),n in r['multiplicity'].items()})
    # Full typed identities and target-release metadata stay separate.
    releases=Counter();projection_collisions=[];mixed_release_docs=[]
    for doc,ss in sorted(r['links'].items()):
        group=defaultdict(set)
        for s in ss:group[short(s)].add(s[1])
        bad={canon(k):sorted(v) for k,v in group.items() if len(v)>1}
        if bad:projection_collisions.append({'document':doc,'collisions':bad})
        if len({s[1] for s in ss})>1:mixed_release_docs.append(doc)
        releases.update(s[1] for s in ss)
    aliases=defaultdict(set)
    for ss in r['links'].values():
        for s in ss:aliases[short(s)].add(s[1])
    aliases={canon(k):sorted(v) for k,v in aliases.items() if len(v)>1}
    pack_aliases=[]
    for p,docs in sorted(r['members'].items()):
        a=defaultdict(set)
        for d in docs:
            for s in r['links'][d]:a[short(s)].add(s[1])
        n=sum(len(v)>1 for v in a.values())
        if n:pack_aliases.append({'pack':p,'projected_identities_with_multiple_releases':n})
    schema={}
    for name in ['section','cr_modifies_section','document','cr_in_pack','disposition','resolution']:
        schema[name]={'create_sql':c.execute('SELECT sql FROM sqlite_master WHERE name=?',(name,)).fetchone()[0],
                      'foreign_keys':c.execute('PRAGMA foreign_key_list('+name+')').fetchall(),
                      'indexes':c.execute('PRAGMA index_list('+name+')').fetchall()}
    mismatch=c.execute('SELECT COUNT(*) FROM cr_modifies_section x JOIN section s ON s.id=x.section_id JOIN document d ON d.id=x.cr WHERE s.release IS NOT d.target_release').fetchone()[0]
    return {'raw_record_path':str(graphpath.relative_to(P)),'raw_record_sha256':sha(graphpath),'raw_records':len(g),'unique_document_records':len(idcounts),'repeated_document_record_ids':sum(n>1 for n in idcounts.values()),
            'raw_modifiesSection_links':sum(source_links.values()),'raw_forward_memberships':sum(source_members.values()),'raw_links_equal_sqlite':True,'raw_memberships_equal_sqlite':True,
            'linked_documents':len([d for d,s in r['links'].items() if s]),'linked_documents_with_multiple_release_values':len(mixed_release_docs),
            'documents_with_projection_cardinality_collision':len(projection_collisions),'projection_collision_examples':projection_collisions[:5],
            'global_projected_identities_spanning_multiple_releases':len(aliases),'global_projected_identity_examples':sorted(aliases.items())[:5],
            'packs_with_cross_document_release_aliases':len(pack_aliases),'pack_release_alias_examples':pack_aliases[:5],
            'linked_sections_mismatching_document_target_release':mismatch,'schema':schema,
            'schema_classification':'SQLite schema permits multiple release identities for the same (document,spec,clause); no such functional dependency or join filter is enforced.',
            'snapshot_classification':'Every document projection is injective in this frozen snapshot.' if not projection_collisions else 'Projection collisions exist.'}

def source_code_receipts():
    files=[P/'code/scripts/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/export_chain_records_sqlite.py',
           P/'studies/semantic_witnesses/build_semantic_witnesses.py',CODE/'common/phase-4/cr_section_index.py']
    files += [CODE/f'RAN{n}/phase-4/cr-parser/03_generate_cr_jsonld.py' for n in range(1,5)]
    files += [CODE/'RAN5/phase-4/neo4j/01_load_cr_ontology.py']
    result=[]
    for p in files:
        text=p.read_text();tree=ast.parse(text);wanted={'parse_clauses_to_sections','load_modifies_section','resolve','generate_cr_extensions','export','enumerate_pools'}
        functions=[{'name':n.name,'line_start':n.lineno,'line_end':n.end_lineno,'sha256':hashlib.sha256(ast.get_source_segment(text,n).encode()).hexdigest()} for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name in wanted]
        result.append({'path':str(p.relative_to(P)),'sha256':sha(p),'functions':functions})
    return result

def classify(cell):
    if cell['available']:return 'witness_present_in_frozen_snapshot'
    st=cell['stratum'];m=cell['marginal_raw_predicate_pass_counts']
    if st.startswith('maximum_') and 'release' in st:return 'per_document_release_projection_injective_in_frozen_materialization'
    if st=='pack_duplicates' or (st=='pack_multicode_duplicates' and m['duplicate_count']==0):return 'no_raw_duplicate_excess_in_observed_pack_cohorts'
    if st=='pack_multicode_duplicates':return 'multicode_and_duplicate_cohorts_disjoint_in_snapshot'
    if st.endswith('_release'):
        return 'no_release_collision_in_enumerated_candidate_universe' if m['release_collision']==0 else 'release_collisions_fail_joint_three_region_requirement'
    return 'no_candidate_satisfies_all_frozen_gates'

def main():
    global P,D,E,CODE
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release',required=True,type=Path,help='Release root with sqlite, records, code and studies.')
    parser.add_argument('--out',required=True,type=Path,help='Output directory; temporary materialization also stays here.')
    parser.add_argument('--materialized-db-dir',type=Path,help='Optional existing RAN2..5.sqlite directory. Omit for cold gzip materialization.')
    parser.add_argument('--preserve-review-dir',type=Path,help='Optional review directory whose direct files must remain unchanged.')
    args=parser.parse_args()
    P=args.release.resolve();E=args.out.resolve();E.mkdir(parents=True,exist_ok=True)
    D=P/'studies/witness_selection_value';CODE=P/'code/scripts/tsg/RAN/formal'
    start=time.monotonic();script_hash=sha(Path(__file__));assert sqlite3.sqlite_version=='3.37.2'
    immutable={p.name:sha(p) for p in args.preserve_review_dir.iterdir() if p.is_file()} if args.preserve_review_dir else {}
    selection=load(D/'measurement/selection.json');definitions=load(P/'studies/semantic_witnesses/protocol.json')['strata']
    assert sha(D/'protocol.json')==selection['protocol_sha256']
    hashes={str(p):sha(p) for p in [D/'measurement/selection.json',D/'protocol.json',P/'studies/semantic_witnesses/protocol.json']}
    cellmap={(x['wg'],x['stratum']):x for x in selection['cells']};report=[];wgstats={};sources={};mismatches=[];materialization=[]
    for pin in selection['inputs']:
        wg=pin['wg'];plain=P/f'sqlite/{wg}.sqlite';source=plain if plain.exists() else plain.with_suffix('.sqlite.gz')
        temporary=None
        if source.suffix!='.gz':db=source
        elif args.materialized_db_dir:db=args.materialized_db_dir/(wg+'.sqlite')
        else:
            temporary=Path(tempfile.mkdtemp(prefix='.witness-db-',dir=E));db=temporary/(wg+'.sqlite')
            with gzip.open(source,'rb') as src,db.open('wb') as dest:shutil.copyfileobj(src,dest)
        assert sha(source)==pin['source_sha256'];assert sha(db)==pin['database_sha256']
        hashes[str(source)] = sha(source)
        c=sqlite3.connect('file:'+str(db.resolve())+'?mode=ro&immutable=1',uri=True);c.execute('PRAGMA query_only=ON')
        r=raw(c);sources[wg]=source_audit(c,r,wg);c.close()
        assert sha(db)==pin['database_sha256']
        materialization.append({'wg':wg,'source':str(source.relative_to(P)),'database_sha256':pin['database_sha256'],'hash_matches_before_and_after_read':True,'cold_decompressed':temporary is not None})
        if temporary:shutil.rmtree(temporary)
        rawpath=P/sources[wg]['raw_record_path'];hashes[str(rawpath)]=sources[wg]['raw_record_sha256']
        preuniverse=Counter();stats={st:{'universe':0,'prefix':[0]*len(gs),'marginal':Counter(),'raw_marginal':Counter(),'first_fail':Counter(),'patterns':Counter(),'example':None,'closest':None,'closest_n':-1,'raw_collision_example':None} for st,gs in GATES.items()}
        archive=D/f'measurement/candidate_universe_{wg}.jsonl.gz';ah=hashlib.sha256();n=0
        with gzip.open(archive,'rb') as f:
            for st,a,properties,flags,raw_override in generated(r,preuniverse):
                line=f.readline();assert line,'archive unexpectedly ended';ah.update(line);old=json.loads(line)
                actual={'stratum':st,'candidate':a,'original_predicate_results':flags,'properties':properties}
                if canon(actual)!=canon(old):
                    mismatches.append({'wg':wg,'index':n,'actual':actual,'old':old})
                    raise AssertionError(('raw recomputation mismatch',wg,n,st,a))
                s=stats[st];s['universe']+=1;rawflags=dict(flags);rawflags.update(raw_override or {})
                for name,v in flags.items():s['marginal'][name]+=bool(v)
                for name,v in rawflags.items():s['raw_marginal'][name]+=bool(v)
                alive=True;first=False
                for j,g in enumerate(GATES[st]):
                    alive=alive and flags[g]
                    s['prefix'][j]+=alive
                    if not alive and not first:s['first_fail'][g]+=1;first=True
                pattern=tuple(flags[g] for g in GATES[st]);s['patterns'][str(pattern)]+=1
                if alive and s['example'] is None:s['example']={'anchor':a,'properties':properties}
                if sum(pattern)>s['closest_n']:s['closest_n']=sum(pattern);s['closest']={'anchor':a,'flags':flags,'properties':properties}
                if rawflags.get('release_collision') and s['raw_collision_example'] is None:
                    ex={'anchor':a,'frozen_flags':flags,'raw_flags':rawflags,'frozen_properties':properties}
                    if st=='conjunction_release':
                        p,one,two=a;one,two=tuple(one),tuple(two)
                        typed={d for d in r['members'][p] if one in r['links'][d] and two in r['links'][d]}
                        broad={d for d in r['members'][p] if {short(one),short(two)}.issubset({short(t) for t in r['links'][d]})}
                        ex['raw_release_blind_extra_documents']=sorted(broad-typed)
                    s['raw_collision_example']=ex
                n+=1
            assert not f.readline(),'archive contains extra candidates'
        pin2=next(x for x in selection['inputs'] if x['wg']==wg)
        assert sha(archive)==pin2['candidate_file_sha256'];assert ah.hexdigest()==pin2['candidate_uncompressed_sha256']
        hashes[str(archive)]=sha(archive)
        for st,s in stats.items():
            old=cellmap[wg,st];assert s['universe']==old['pre_predicate_candidates'];assert s['prefix'][-1]==old['original_witness_eligible']
            if st.startswith('intersection') or st.startswith('difference'):
                factor=2 if st.startswith('difference') else 1
                pre=[{'gate':'same_pack_distinct_document_pair','remaining':preuniverse['document_pairs_before_shared_typed_identity']*factor},{'gate':'shared_full_typed_section','remaining':preuniverse['document_pairs_with_shared_typed_identity']*factor}]
            elif st.startswith('conjunction') or st=='composition':
                pre=[{'gate':'distinct_typed_section_pair_present_somewhere_in_pack','remaining':preuniverse['section_pairs_before_document_cooccurrence']},{'gate':'cooccur_on_at_least_one_pack_member','remaining':preuniverse['section_pairs_with_document_cooccurrence']}]
            elif st.startswith('meeting_'):
                pre=[{'gate':'distinct_meeting_id_in_resolution_table','remaining':len(set(r['resolutions'].values()))},{'gate':'has_source_verified_whole_target_disposition','remaining':len(r['meeting_records'])}]
            else:pre=[{'gate':'observed_nonempty_forward_pack_membership_cohort','remaining':len(r['members'])}]
            assert pre[-1]['remaining']==s['universe']
            cell={'wg':wg,'stratum':st,'family':next(x['family'] for x in definitions if x['id']==st),'candidate_universe':s['universe'],'universe_gates':pre,
                  'witness_gates':[{'gate':g,'remaining':s['prefix'][i],'marginal_frozen_flag_pass':s['marginal'][g],'marginal_raw_predicate_pass':s['raw_marginal'][g],'first_failed_here':s['first_fail'][g]} for i,g in enumerate(GATES[st])],
                  'eligible':s['prefix'][-1],'available':s['prefix'][-1]>0,'marginal_raw_predicate_pass_counts':dict(s['raw_marginal']),'joint_flag_patterns':dict(s['patterns']),
                  'necessary_and_sufficient_condition':'Within the frozen enumerated universe, there exists a candidate satisfying every ordered witness gate.',
                  'scope':'Exact finite frozen-snapshot characterization; not impossibility over arbitrary databases or source records.',
                  'first_eligible_example':s['example'],'closest_candidate_example':None if s['example'] else s['closest'],
                  'first_raw_release_collision_example':s['raw_collision_example']}
            cell['classification']=classify(cell);report.append(cell)
        wgstats[wg]={'candidate_rows':n,'preuniverse_counts':dict(preuniverse),'all_rows_properties_and_flags_equal_frozen_archive':True}
        print(canon({'wg':wg,'rows':n,'available':sum(x['wg']==wg and x['available'] for x in report)}),flush=True)
    assert len(report)==95 and sum(x['available'] for x in report)==66
    assert sum(x['candidate_universe'] for x in report)==2269290
    assert all(sha(Path(p))==h for p,h in hashes.items())
    if args.preserve_review_dir:assert all(sha(args.preserve_review_dir/name)==h for name,h in immutable.items())
    code=source_code_receipts()
    save(E/'cell_analysis.json',{'role':'post-review author analysis; no re-rating','definitions':DEFINITIONS,'gate_order':GATES,'cells':report,'working_groups':wgstats,'sources':sources,'source_code':code,
        'conjunction_release_note':'The frozen enumerator stores release_collision=false and no extras when three_nonempty_regions fails. Marginal raw predicate counts additionally compute release collision without that shortcut; prefix/final counts are identical.',
        'maximum_release_conclusion':{'schema':'Not an implication of SQLite schema or the typed identity definition. Different releases have different valid section IDs and the link table has no dependency forcing a single release for a projected identity.',
           'current_records':'Projection (spec,release,clause)->(spec,clause) is injective within every linked document in these five frozen materializations. Consequently every per-document distinct footprint count, maximum count and winner rowset is unchanged; all 15 release-sensitive maximum cells have zero eligible candidates.',
           'construction_mechanism':'The pinned SectionIndex resolver returns one selected section for each (spec,section number,target release) argument. The inspected per-CR builders pass fixed spec/release arguments and deduplicate full section IDs; all released cr_extensions records have unique document IDs as checked. This gives a construction-level explanation under those conditions, not an ontology axiom or a universal claim about future/multi-record materializations.',
           'cross_document_distinction':'Within-document projection injectivity is compatible with cross-document release aliases. Membership and conjunction may therefore remain release-sensitive while footprint counting does not.'}})
    fields=['wg','stratum','family','candidate_universe','eligible','available','classification','universe_gates','witness_gates','marginal_raw_predicate_pass_counts']
    with (E/'cells.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for row in report:w.writerow({k:canon(row[k]) if isinstance(row[k],(list,dict)) else row[k] for k in fields})
    with (E/'gate_counts.csv').open('w',newline='') as f:
        fields2=['wg','stratum','gate_type','gate_index','gate','remaining','marginal_frozen_flag_pass','marginal_raw_predicate_pass','first_failed_here']
        w=csv.DictWriter(f,fieldnames=fields2);w.writeheader()
        for row in report:
            for kind,key in [('universe','universe_gates'),('witness','witness_gates')]:
                for i,g in enumerate(row[key]):w.writerow(dict(wg=row['wg'],stratum=row['stratum'],gate_type=kind,gate_index=i,**g))
    assert sha(Path(__file__))==script_hash
    save(E/'receipt.json',{'role':'post-review author analysis; first review preserved','python':sys.version,'sqlite':sqlite3.sqlite_version,'read_only':True,'study_imports':[],
         'model_calls':0,'sql_generation_or_modification':False,'reselected_anchors':False,'all_raw_properties_and_predicates_recomputed':True,'all_frozen_candidate_rows_matched':sum(x['candidate_rows'] for x in wgstats.values()),
         'cells':95,'available':66,'unavailable':29,'classification_counts':dict(Counter(x['classification'] for x in report)),
         'source_raw_links_equal_sqlite_all_wgs':True,'source_raw_memberships_equal_sqlite_all_wgs':True,
         'input_sha256':{str(Path(p).relative_to(P)):h for p,h in hashes.items()},
         'raw_record_sha256':{x['raw_record_path']:x['raw_record_sha256'] for x in sources.values()},
         'code_sha256':{x['path']:x['sha256'] for x in code},'review_files_before_sha256':immutable,'review_files_unchanged':True,
         'materialization':materialization,'release_argument':str(P),'output_argument':str(E),
         'script_sha256':script_hash,'elapsed_seconds':time.monotonic()-start,
         'main_paper_or_public_package_changed':False,'review_recommendation_changed':False})
    print(canon({'cells':95,'available':66,'unavailable':29,'classifications':dict(Counter(x['classification'] for x in report)),'seconds':time.monotonic()-start}),flush=True)

if __name__=='__main__':main()
