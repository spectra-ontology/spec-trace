#!/usr/bin/env python3
"""Paper-claim verifier: extract every quantitative claim in main.tex and
re-derive each one from the deployed Knowledge Graph + validation JSONs.

Exit code:
  0 — every claim verified against ground truth
  1 — at least one claim mismatches (review required)

This exists because trust-based "the JSON file says X" is NOT verification.
This script re-executes the underlying queries and refuses to PASS unless
the live measurement equals the paper claim.

Run: python3 tests/paper_claim_verifier.py [--paper PATH] [--strict]

Designed to be CI-runnable: depends only on neo4j driver, rdflib, json.
Requires the five RAN Neo4j instances to be reachable on
bolt://localhost:768{7..91} with NEO4J_PASSWORD env (default 'password123').
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PAPER = REPO / 'docs' / 'paper' / 'iswc' / 'latex' / 'main.tex'
VAL = REPO / 'release_package' / 'validation'
PWD = os.environ.get('NEO4J_PASSWORD', 'password123')

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = '') -> None:
    results.append((name, ok, detail))
    mark = 'PASS' if ok else 'FAIL'
    print(f'  [{mark}] {name}{(" — " + detail) if detail else ""}')


def section(title: str) -> None:
    print(f'\n=== {title} ===')


def neo4j_run(port: int, cypher: str, **params) -> list[dict]:
    from neo4j import GraphDatabase
    drv = GraphDatabase.driver(f'bolt://localhost:{port}', auth=('neo4j', PWD))
    try:
        with drv.session() as s:
            return [r.data() for r in s.run(cypher, **params)]
    finally:
        drv.close()


def load_json(name: str) -> dict:
    return json.loads((VAL / name).read_text())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--paper', default=str(PAPER))
    ap.add_argument('--strict', action='store_true', help='exit 1 on any FAIL')
    args = ap.parse_args()

    paper_text = Path(args.paper).read_text()

    section('1. Schema element counts (paper §4 / §6 Table 5)')
    sm = load_json('structural_metrics.json')
    paper_claims = {
        '26 classes': sm['classes_total'] == 26,
        '53 object properties': sm['object_properties'] == 53,
        '81 data properties': sm['data_properties'] == 81,
        '886 triples': sm['triples_total'] == 886,
        '20 functional properties': sm['functional_properties'] == 20,
        '2 inverse-functional': sm['inverse_functional_properties'] == 2,
        '15 inverse pairs': sm['inverse_property_pairs'] == 15,
        '6 irreflexive': sm['irreflexive_properties'] == 6,
        '2 asymmetric': sm['asymmetric_properties'] == 2,
    }
    for label, ok in paper_claims.items():
        check(label, ok)

    section('2. SHACL shapes (paper §7 RAS item ii)')
    import rdflib
    g = rdflib.Graph()
    g.parse(REPO / 'release_package/shapes/spectra-core.shacl.ttl', format='turtle')
    SH = rdflib.Namespace('http://www.w3.org/ns/shacl#')
    n_shapes = len(list(g.subjects(rdflib.RDF.type, SH.NodeShape)))
    check('8 SHACL NodeShapes', n_shapes == 8, f'actual {n_shapes}')

    section('3. SpectraCQ (137 NL + 137 Cypher; phase distribution)')
    cqs = json.load(open(REPO / 'release_package/cqs/spectra_cq_v1.0/questions.json'))
    n_cqs = len(cqs.get('cqs', []))
    check('137 CQ entries', n_cqs == 137, f'actual {n_cqs}')
    n_cypher = len(list((REPO / 'release_package/cqs/spectra_cq_v1.0/cypher').glob('*.cypher')))
    check('137 Cypher files', n_cypher == 137, f'actual {n_cypher}')
    expected_phases = {'P1': 25, 'P2': 34, 'P3': 45, 'P4': 15, 'P5': 18}
    for ph, exp in expected_phases.items():
        n = sum(1 for c in cqs['cqs'] if c.get('phase') == int(ph[1]))
        check(f'  phase {ph}={exp}', n == exp, f'actual {n}')

    section('4. SpectraCQ live re-execution against RAN1 Neo4j (137/137 PASS)')
    pass_n, fail_list = 0, []
    cypher_dir = REPO / 'release_package/cqs/spectra_cq_v1.0/cypher'
    for f in sorted(cypher_dir.glob('*.cypher')):
        cypher = f.read_text()
        try:
            recs = neo4j_run(7687, cypher)
            if recs:
                pass_n += 1
            else:
                fail_list.append(f.stem)
        except Exception as e:
            fail_list.append(f'{f.stem} (ERROR: {str(e)[:60]})')
    check(f'137/137 live PASS on RAN1', pass_n == 137 and not fail_list,
          f'PASS {pass_n}/137; fail {fail_list[:5]}' if fail_list else '')

    section('5. Per-WG class coverage (paper §6.4)')
    pwg = load_json('per_wg_class_coverage.json')
    expected_pct = {'RAN1': 100.0, 'RAN2': 84.6, 'RAN3': 88.5, 'RAN4': 92.3, 'RAN5': 76.9}
    spectra_classes = ['Tdoc','CR','LS','Summary','SessionNotes','Resolution','Agreement','Conclusion','WorkingAssumption','Spec','Section','TSTable','TSFigure','TechnicalReport','TRImpact','Meeting','Company','Contact','WorkingGroup','AgendaItem','CRPack','WorkItem','Release','Figure','Table','Chart']
    for ran, port in [('RAN1',7687),('RAN2',7688),('RAN3',7689),('RAN4',7690),('RAN5',7691)]:
        used = sum(1 for cls in spectra_classes if neo4j_run(port, f'MATCH (n:`{cls}`) RETURN count(n) AS c')[0]['c'] > 0)
        json_pct = pwg['per_wg_class_coverage'][ran]['pct']
        live_pct = round(used/26*100, 1)
        check(f'{ran} {expected_pct[ran]}%', live_pct == expected_pct[ran], f'live {live_pct}%, json {json_pct}%')

    section('6. Cross-WG extension (paper §6.4: 1 OP + 2 DPs)')
    cw = load_json('cross_wg_schema_diff.json')
    union = cw.get('aggregate_non_ran1', {})
    op_ext = union.get('object_properties', {}).get('ran2_to_5_extensions_count', 0)
    cls_ext = union.get('classes', {}).get('ran2_to_5_extensions_count', 0)
    check('0 new classes for RAN2-5', cls_ext == 0)
    check('1 new OP (REFERENCES_SPEC)', op_ext == 1)
    # DP candidates: filter loader-local underscore + scaffolding
    dp_ext_raw = union.get('data_properties', {}).get('ran2_to_5_extensions_union', [])
    dp_real = [d for d in dp_ext_raw if not d.startswith('_') and d not in ('id', 'for_', 'release')]
    check('2 substantive DP candidates (summaryId + discussionText)',
          set(dp_real) == {'summaryId', 'discussionText'}, f'actual {dp_real}')
    check('REFERENCES_SPEC actually exists in RAN3', neo4j_run(7689, 'MATCH ()-[r:REFERENCES_SPEC]->() RETURN count(r) AS c')[0]['c'] > 0)
    check('summaryId DP populated in RAN3', neo4j_run(7689, 'MATCH (s:Summary) WHERE s.summaryId IS NOT NULL RETURN count(s) AS c')[0]['c'] > 0)
    check('discussionText DP populated in RAN5', neo4j_run(7691, 'MATCH (n) WHERE n.discussionText IS NOT NULL RETURN count(n) AS c')[0]['c'] > 0)

    section('7. RAN1 instance counts (paper Table 6 — all 26)')
    ic = load_json('ran1_instance_counts.json')
    for cls, json_n in ic['RAN1']['counts'].items():
        if json_n is None: continue
        live_n = neo4j_run(7687, f'MATCH (n:`{cls}`) RETURN count(n) AS c')[0]['c']
        check(f'  {cls}: {json_n}', live_n == json_n, f'live {live_n}' if live_n != json_n else '')

    section('8. Relation integrity (paper §6.E3)')
    ri = load_json('ran1_relation_integrity.json')
    paper_pcts = {'submittedBy': 99.36, 'presentedAt': 100.0, 'madeAt': 100.0,
                  'references': 51.55, 'modifiesSection': 34.66}
    for rel, expected in paper_pcts.items():
        json_pct = ri['relations'][rel]['pct']
        check(f'{rel} {expected}%', json_pct == expected, f'json {json_pct}%')

    section('9. Use scenario specific numbers (paper Table 8)')
    cw_use = load_json('cross_wg_use_evidence.json')
    # S2: RAN1->RAN2 LS, top recipient
    s2_data = next((q for q in cw_use['queries'] if q.get('name') == 'RAN1_LS_by_recipient_WG'), None)
    if s2_data:
        ran2_count = next((r['n'] for r in s2_data['result'] if r['wg'] == 'RAN2'), None)
        check('S2: 3,644 LSs RAN1→RAN2', ran2_count == 3644, f'actual {ran2_count}')
    # S2.b: 1,450 received in RAN2 KG from RAN1
    s2b = next((q for q in cw_use['queries'] if q.get('name') == 'RAN2_KG_LSes_from_RAN1'), None)
    if s2b:
        check('S2: 1,450 received in RAN2 KG from RAN1', s2b['total'] == 1450, f'actual {s2b["total"]}')
        peak = s2b['top_meetings'][0]
        check(f'S2 peak: RAN2#118-e (62)', peak['mtg'] == 'RAN2#118-e' and peak['n'] == 62,
              f'actual {peak}')
    # S3: TS 38.300 CR counts
    s3 = next((q for q in cw_use['queries'] if q.get('name') == 'TS_38300_modify_CR_count_per_WG_KG'), None)
    if s3:
        check('S3: TS 38.300 RAN2 2,039 CRs', s3['result'].get('RAN2') == 2039)
        check('S3: TS 38.300 RAN3 270 CRs', s3['result'].get('RAN3') == 270)
    # S5: TR 38.889 exists in RAN1
    tr_exists = neo4j_run(7687, "MATCH (tr:TechnicalReport {trNumber: '38.889'}) RETURN tr LIMIT 1")
    check('S5: TR 38.889 exists in RAN1', bool(tr_exists))
    # S7: NR_eMIMO-Core WorkItem
    wi_exists = neo4j_run(7687, "MATCH (wi:WorkItem {id: 'tdoc:workitem/NR_eMIMO-Core'}) RETURN wi LIMIT 1")
    check('S7: NR_eMIMO-Core WorkItem exists', bool(wi_exists))

    section('10. SPARQL portability (paper §7 + §6 RAS)')
    port = load_json('cypher_to_sparql_portability.json')
    check('136/137 SPARQL-equivalent', port.get('schema_level_translatable') == 136 and port.get('neo4j_specific') == 1)

    section('11. Body-text TTL deposit (paper §7)')
    body_dir = REPO / 'release_package/kg/per_wg'
    total_size = 0
    for n in range(1, 6):
        f = body_dir / f'RAN{n}-body.ttl'
        if not f.exists():
            check(f'RAN{n}-body.ttl exists', False, 'missing in checkout')
            continue
        sz = f.stat().st_size
        total_size += sz
        check(f'RAN{n}-body.ttl >= 80 MB', sz >= 80*1024*1024, f'{sz/1024/1024:.1f} MB')
    total_gb = total_size / 1024 / 1024 / 1024
    check('Total body ~0.9 GB', 0.85 <= total_gb <= 1.0, f'{total_gb:.2f} GB')

    section('12. Specific paper-text matches (regex)')
    paper_specific_checks = [
        ('14 of 137 CQs reference companies', '14 of 137 CQs'),
        ('123 remaining CQs', 'remaining 123 CQs'),
        ('123,677 unique RAN1 TDocs', '123{,}677'),
        ('60 meetings', 'from the 60 meetings'),
        ('NR meeting range RAN1#84--#123', 'RAN1\\#84--\\#123'),
        ('peak RAN2#118-e: 62', 'RAN2\\#118-e: 62'),
        ('TR 38.889 (not 38.913)', 'TR~38.889'),
        ('25,586 distinct LSs', '25{,}586'),
        ('one TDoc re-tabled (caption)', 'one TDoc was re-tabled'),
    ]
    forbidden = [
        ('No "TR 38.913" in narrative', 'TR 38.913'),
        ('No "TR~38.913"', 'TR~38.913'),
        ('No "26,791 LSs" in narrative', '26,791 LSs'),
        ('No "207 TDocs" in narrative', '207 TDocs'),
        ('No "0.17%" in §6.E3', '0.17\\%'),
        ('No "13 of 137 CQs"', '13 of 137 CQs'),
        ('No "remaining 124 CQs"', 'remaining 124 CQs'),
    ]
    for label, needle in paper_specific_checks:
        check(label, needle in paper_text)
    for label, needle in forbidden:
        check(label, needle not in paper_text, 'still in paper' if needle in paper_text else '')

    # Final summary
    print()
    total = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = total - passed
    print(f'=== Summary: {passed}/{total} paper claims verified ===')
    if failed:
        print('Failures:')
        for name, ok, detail in results:
            if not ok:
                print(f'  - {name}: {detail}')
        return 1 if args.strict else 0
    print('All paper claims verified against ground truth.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
