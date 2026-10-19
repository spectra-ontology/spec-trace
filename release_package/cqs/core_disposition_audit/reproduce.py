"""Recount bundled conditional graph witnesses with SQLite and Python sets."""
import argparse
from bisect import bisect_left, bisect_right
from collections import defaultdict
from fractions import Fraction
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import sqlite3

HERE = Path(__file__).resolve().parent
RANK_SQL = '''SELECT wg,companyName,count(DISTINCT Tdoc_node_id) AS distinctTdocs,
count(DISTINCT Resolution_node_id) AS distinctResolutions
FROM rank_path GROUP BY wg,companyName ORDER BY wg,companyName'''
TREND_SQL = '''SELECT wg,meeting_node AS node_id,canonicalMeetingNumber,meetingNumberInt,
count(DISTINCT resolution_node) AS all_resolution_count,
count(DISTINCT CASE WHEN Tdoc_node IS NOT NULL THEN resolution_node END) AS linked_resolution_count,
count(DISTINCT CASE WHEN exact_named_company_submitter=1 THEN resolution_node END) AS company_resolution_count
FROM trend_path GROUP BY wg,meeting_node,canonicalMeetingNumber,meetingNumberInt
ORDER BY wg,meetingNumberInt,canonicalMeetingNumber,meeting_node'''
AREA_SQL = '''SELECT s.*,
(SELECT count(DISTINCT dst_id) FROM section_edge e WHERE e.src_id=s.node_id
 AND e.type='typed_CONTAINS_TABLE') AS direct_distinct_tables,
(SELECT count(DISTINCT dst_id) FROM section_edge e WHERE e.src_id=s.node_id
 AND e.type='typed_HAS_SUB_SECTION') AS direct_distinct_child_sections
FROM section_spec s ORDER BY node_id,spec_node_id'''


def rows(name):
    with gzip.open(HERE/'witnesses'/name, 'rt') as f:
        return [json.loads(l) for l in f]


def insert(c, table, data):
    keys = list(data[0])
    c.execute('CREATE TABLE '+table+' ('+','.join('"'+k+'"' for k in keys)+')')
    c.executemany('INSERT INTO '+table+' VALUES ('+','.join('?' for _ in keys)+')',
                  [[r[k] for k in keys] for r in data])


def keymap(data, keys):
    return {tuple(r[k] for k in keys):r for r in data}


def direction(x):
    return (x>0)-(x<0)


def cutoff(domain, m, first):
    def score(r):
        t,s=r['direct_distinct_tables'],r['direct_distinct_child_sections']
        return m*t+s if first=='tables' else t+m*s
    scores=sorted(score(r) for r in domain)
    inside,outside=set(),set()
    for r in domain:
        v=score(r); above=len(scores)-bisect_right(scores,v)
        tied=bisect_right(scores,v)-bisect_left(scores,v)
        k=(r['node_id'],r['spec_node_id'])
        if above+tied<=10:inside.add(k)
        if above>=10:outside.add(k)
    return inside,outside


def reproduce():
    expected=json.loads((HERE/'expected.json').read_text())
    c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row
    rank=rows('rank_paths.jsonl.gz');trend=rows('trend_paths.jsonl.gz')
    sections=rows('section_spec_operand_inventory.jsonl.gz');edges=rows('typed_section_edges.jsonl.gz')
    for name,data in [('rank_path',rank),('trend_path',trend),('section_spec',sections),('section_edge',edges)]:
        insert(c,name,data)
    rank_counts=[dict(r) for r in c.execute(RANK_SQL)]
    trend_counts=[dict(r) for r in c.execute(TREND_SQL)]
    area_counts=[dict(r) for r in c.execute(AREA_SQL)]
    c.close()
    # These sets consume raw witness rows, independently of aggregate SQL.
    rs=defaultdict(lambda:[set(),set()])
    for r in rank:
        s=rs[r['wg'],r['companyName']];s[0].add(r['Tdoc_node_id']);s[1].add(r['Resolution_node_id'])
    for r in rank_counts:
        assert [r['distinctTdocs'],r['distinctResolutions']]==list(map(len,rs[r['wg'],r['companyName']]))
    ts=defaultdict(lambda:[set(),set(),set()])
    for r in trend:
        s=ts[r['wg'],r['meeting_node']];s[0].add(r['resolution_node'])
        if r['Tdoc_node'] is not None:s[1].add(r['resolution_node'])
        if r['exact_named_company_submitter']:s[2].add(r['resolution_node'])
    for r in trend_counts:
        assert [r['all_resolution_count'],r['linked_resolution_count'],r['company_resolution_count']]==list(map(len,ts[r['wg'],r['node_id']]))
    es=defaultdict(set)
    for r in edges:es[r['type'],r['src_id']].add(r['dst_id'])
    for r in area_counts:
        assert r['direct_distinct_tables']==len(es['typed_CONTAINS_TABLE',r['node_id']])
        assert r['direct_distinct_child_sections']==len(es['typed_HAS_SUB_SECTION',r['node_id']])
    result={'checks':'All SQLite aggregates equal independent Python set recounts and pinned expected rows.',
            'witness_rows':{'ranks':len(rank),'trends':len(trend),'section_spec_operands':len(sections),'typed_section_edges':len(edges)},
            'rank_counterexamples':{},'trend_counterexamples':{},'area_counterexamples':{}}
    for wg in ['RAN3','RAN4']:
        actual=[{k:v for k,v in r.items() if k!='wg'} for r in rank_counts if r['wg']==wg]
        assert keymap(actual,['companyName'])==keymap(expected['ranks'][wg],['companyName'])
        inversions=[{'a':a,'b':b} for a,b in itertools.combinations(actual,2)
                    if (a['distinctTdocs']-b['distinctTdocs'])*(a['distinctResolutions']-b['distinctResolutions'])<0]
        named=['Nokia','ZTE'] if wg=='RAN3' else ['Qualcomm','LG Electronics','Samsung']
        # The actual released LG company literal is preserved, without alias expansion.
        selected=[r for r in actual if r['companyName'] in named or (wg=='RAN4' and r['companyName'].startswith('LG'))]
        extents={}
        for metric in ['distinctTdocs','distinctResolutions']:
            boundary=sorted((r[metric] for r in actual),reverse=True)[9]
            extents[metric]={'tenth_value':boundary,
                'strictly_above_cutoff':sorted(r['companyName'] for r in actual if r[metric]>boundary),
                'tied_at_cutoff':sorted(r['companyName'] for r in actual if r[metric]==boundary)}
        result['rank_counterexamples'][wg]={'full_company_population':len(actual),'strict_pairwise_reversals':len(inversions),
            'selected_literal_company_counts':selected,'conditional_top10_cutoffs_no_tie_winner_selected':extents}
        meetings=[{k:v for k,v in r.items() if k!='wg'} for r in trend_counts if r['wg']==wg]
        assert keymap(meetings,['node_id'])==keymap(expected['trends'][wg],['node_id'])
        labels=['RAN3#93bis','RAN3#94'] if wg=='RAN3' else ['RAN4#87','RAN4#88']
        pair=[next(r for r in meetings if r['canonicalMeetingNumber']==label) for label in labels]
        a,b=pair
        n0,n1=a['company_resolution_count'],b['company_resolution_count']
        result['trend_counterexamples'][wg]={'same_Resolution_unit':True,'pair':pair,
            'count_direction':direction(n1-n0),
            'share_among_all_Resolutions_direction':direction(Fraction(n1,b['all_resolution_count'])-Fraction(n0,a['all_resolution_count'])),
            'share_among_Tdoc_linked_Resolutions_direction':direction(Fraction(n1,b['linked_resolution_count'])-Fraction(n0,a['linked_resolution_count']))}
    assert keymap(area_counts,['node_id','spec_node_id'])==keymap(expected['area_operand_counts'],['node_id','spec_node_id'])
    m=1+max(max(r['direct_distinct_tables'],r['direct_distinct_child_sections']) for r in area_counts)
    assert m==expected['area_weight_M']
    for name,domain in [('all_original_Section_to_Spec_operand_rows',area_counts),
                       ('both_direct_counts_positive_sensitivity_only',[r for r in area_counts if r['direct_distinct_tables']>0 and r['direct_distinct_child_sections']>0])]:
        ti,to=cutoff(domain,m,'tables');si,so=cutoff(domain,m,'children')
        counts={'table_in_child_out':len(ti&so),'child_in_table_out':len(si&to)}
        assert counts==expected['area_forced_membership_difference_counts'][name]
        result['area_counterexamples'][name]={'population_rows':len(domain),'M':m,
            'positive_weights':{'table_priority':[m,1],'child_priority':[1,m]},'tie_robust_membership_difference_counts':counts,
            'example_rows':[r for r in domain if (r['specNumber'],r['specRelease'],r['sectionNumber']) in
                           [('38.213','Rel-18','16.3'),('38.211','Rel-16','6.3.2')]]}
    return result


def main():
    a=argparse.ArgumentParser();a.add_argument('--output',type=Path);args=a.parse_args()
    result=reproduce()
    text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        with args.output.open('x') as f:f.write(text)
    else:print(text,end='')


if __name__=='__main__':main()
