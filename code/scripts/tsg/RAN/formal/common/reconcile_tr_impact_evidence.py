#!/usr/bin/env python3
"""Reconcile source-assessed TR claims and qualified study findings.

Spec: operations rulebook §3–4; ontology/schema/tdoc-ontology.ttl EvidenceAssertion.
Cycle: 185 retained claims → verified source receipts → full durable preimage →
       guarded WG transaction → candidate/causal graph and independent study findings.
Usage: python3 -B reconcile_tr_impact_evidence.py --out <journal> [--apply]
LLM calls: none. Default is read-only; --apply performs explicitly requested reconciliation.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import sys
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'.git').exists())
sys.path.insert(0,str(ROOT/'scripts/common'))
from common import axis,credentials
from common.atomic_io import write_text_atomic
from neo4j import GraphDatabase,READ_ACCESS
from tr_impact_evidence import (CAUSAL_TYPES,claim_of,assess_impacts,load_assessed_impact_nodes,
 link_assessed_impact_targets,load_study_assertions,study_assertion_instances,ImpactEvidenceError,_bound_source)

TARGET_RELATIONS=['IMPACTS_SPEC','SPEC_IMPACTED_BY','IMPACTS_SECTION','SECTION_IMPACTED_BY',
 'impactsSpec','specImpactedBy','impactsSection','sectionImpactedBy',
 'CANDIDATE_IMPACTS_SPEC','CANDIDATE_IMPACTS_SECTION','candidateImpactsSpec','candidateImpactsSection']


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()


def source_fingerprints(wg):
 """Bind the plan and transaction to its manifest, CSV and retained source files."""
 directory=ROOT/f'ontology/input/tsg/RAN/formal/TR/{wg}'
 paths={directory/'tr_impact_evidence.json',directory/'tr_impact_mapping.csv',
        ROOT/'scripts/tsg/RAN/formal/common/reconcile_tr_impact_evidence.py',
        ROOT/'scripts/tsg/RAN/formal/common/tr_impact_evidence.py',
        ROOT/'scripts/tsg/RAN/formal/common/tr_source_identity.py',
        ROOT/'scripts/common/common/review_artifacts.py'}
 manifest=json.loads((directory/'tr_impact_evidence.json').read_text())
 if 'originalCsv' in manifest:
  original=manifest['originalCsv']
  if (not isinstance(original,dict) or not isinstance(original.get('contentUtf8'),str)
      or hashlib.sha256(original['contentUtf8'].encode('utf-8')).hexdigest()!=original.get('sha256')):
   raise ValueError('Historical original CSV content SHA mismatch')
 def visit(value):
  if isinstance(value,dict):
   if 'path' in value and 'sha256' in value:
    paths.add(_bound_source(ROOT,value))
   for child in value.values():visit(child)
  elif isinstance(value,list):
   for child in value:visit(child)
 visit(manifest['claims'])
 return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def check_source_fingerprints(expected,wg):
 try:
  current=source_fingerprints(wg)
 except (ValueError,OSError) as exc:
  raise ValueError('TR source inputs changed after planning; transaction refused') from exc
 if current!=expected:
  raise ValueError('TR source inputs changed after planning; transaction refused')


def snapshot(session):
 rows=session.run('''MATCH (imp:TRImpact) OPTIONAL MATCH (imp)-[r]-(n)
 WITH imp,r,n ORDER BY elementId(r)
 RETURN elementId(imp) AS elementId,labels(imp) AS labels,properties(imp) AS properties,
 collect(CASE WHEN r IS NULL THEN null ELSE {elementId:elementId(r),type:type(r),
 properties:properties(r),outgoing:startNode(r)=imp,otherElementId:elementId(n),
 otherLabels:labels(n),otherProperties:properties(n)} END) AS relationships
 ORDER BY elementId(imp)''').data()
 for row in rows:
  row['labels'].sort()
  for rel in row['relationships']:rel['otherLabels'].sort()
 return rows


def observed_claim(node):
 props=node['properties'];rels=node['relationships']
 trs={r['otherProperties']['trNumber'] for r in rels if r['type'] in ('HAS_TR_IMPACT','IMPACT_OF_TR') and r['otherProperties'].get('trNumber')}
 specs={r['otherProperties']['specNumber'] for r in rels if r['type'] in TARGET_RELATIONS and r['otherProperties'].get('specNumber')}
 if len(trs)!=1 or len(specs)>1:raise ValueError(f'Legacy assertion identity ambiguous: {props}')
 return claim_of(dict(props,trNumber=next(iter(trs)),impactsSpec=next(iter(specs)) if specs else ''))


def retained_claim_keys(entry):
 """Historical rows may resolve a prior ID; source discoveries have no invented original."""
 claims=[entry['claim']]
 if entry.get('originalRow'):
  claims.append(claim_of(entry['originalRow']))
 elif entry.get('inputOrigin')!='source_discovery' or not entry.get('discoveryEvidence'):
  raise ValueError('New TR assertion requires its explicit source-discovery provenance')
 return [json.dumps(c,sort_keys=True) for c in claims]


def build_plan(wg,before):
 directory=ROOT/f'ontology/input/tsg/RAN/formal/TR/{wg}'
 manifest=json.loads((directory/'tr_impact_evidence.json').read_text())
 rows=list(csv.DictReader((directory/'tr_impact_mapping.csv').open()))
 old={}
 for node in before:
  key=json.dumps(observed_claim(node),sort_keys=True)
  if key in old:raise ValueError('Duplicate legacy TR claim identity')
  old[key]=node
 changes=[];covered=set()
 for index,row in enumerate(rows):
  claim=claim_of(row);entry=next(e for e in manifest['claims'] if e['claim']==claim)
  keys=retained_claim_keys(entry)
  matches={old[k]['elementId']:old[k] for k in keys if k in old}
  if len(matches)>1:raise ValueError(f'Current and legacy claim resolve to different nodes: {claim}')
  previous=next(iter(matches.values()),None)
  if previous:covered.add(previous['elementId'])
  tr,spec,section=claim['trNumber'],claim['impactsSpec'],claim['impactsSection']
  iid=f'{tr}-{spec or "NoChange"}'
  if section:iid+='-S'+section
  if not spec and wg=='RAN5':iid+='-'+str(index)
  row['trImpactId']=iid;row['affectedSection']=section
  changes.append({'beforeElementId':previous['elementId'] if previous else None,
   'beforeTrImpactId':previous['properties']['trImpactId'] if previous else None,'row':row})
 if covered!={n['elementId'] for n in before}:raise ValueError(f'{wg}: unmapped legacy nodes require review')
 assess_impacts(ROOT,wg,[c['row'] for c in changes])
 return changes


def apply_plan(session,before,changes,wg,source_inputs=None):
 source_inputs=source_inputs if source_inputs is not None else source_fingerprints(wg)
 check_source_fingerprints(source_inputs,wg)
 rows=[c['row'] for c in changes]
 # Validate all independent source findings before opening the mutation transaction.
 source_findings=study_assertion_instances(ROOT,wg)
 with session.begin_transaction(timeout=180) as tx:
  if digest(snapshot(tx))!=digest(before):raise ValueError('Live TR preimage changed; refusing stale plan')
  for change in changes:
   if change['beforeElementId'] and change['beforeTrImpactId']!=change['row']['trImpactId']:
    n=tx.run('''MATCH (i:TRImpact) WHERE elementId(i)=$id AND i.trImpactId=$old
      SET i.legacyTrImpactId=$old,i.trImpactId=$new RETURN count(i) AS count''',
      id=change['beforeElementId'],old=change['beforeTrImpactId'],new=change['row']['trImpactId']).single()['count']
    if n!=1:raise ValueError('TR assertion rekey preimage mismatch')
  ids=[r['trImpactId'] for r in rows]
  # Retarget only from explicitly retained current rows; original edges remain in the journal.
  tx.run('''MATCH (i:TRImpact)-[r]-() WHERE i.trImpactId IN $ids AND type(r) IN $types DELETE r''',ids=ids,types=TARGET_RELATIONS).consume()
  count=load_assessed_impact_nodes(tx,ROOT,wg,rows)
  if count!=len(rows):raise ValueError('Assertion write count mismatch')
  for row in rows:
   linked=tx.run('''MATCH (i:TRImpact {trImpactId:$iid}), (tr:TechnicalReport {trNumber:$tr})
       MERGE (tr)-[:HAS_TR_IMPACT]->(i) MERGE (i)-[:IMPACT_OF_TR]->(tr)
       RETURN count(i) AS count''',iid=row['trImpactId'],tr=row['trNumber']).single()['count']
   if linked!=1:raise ValueError('Assertion owner missing or ambiguous')
  link_assessed_impact_targets(tx,ROOT,wg,rows,'spec')
  # A raw clause number has no release identity and is retained as affectedSection metadata.
  # Only an explicit release-key reference can create a section-target relation.
  link_assessed_impact_targets(tx,ROOT,wg,rows,'section')
  findings=load_study_assertions(tx,ROOT,wg)
  after=snapshot(tx)
  if len(after)!=len(rows) or {n['properties']['trImpactId'] for n in after}!=set(ids):
   raise ValueError('TR assertion population mismatch')
  if not {n['elementId'] for n in before}.issubset({n['elementId'] for n in after}):
   raise ValueError('Legacy assertion node identity lost')
  leakage=tx.run('''MATCH (i:TRImpact)-[r]-() WHERE type(r) IN $types
      AND (i.evidenceStatus <> 'source_verified' OR NOT i.impactType IN $causal)
      RETURN count(r) AS count''',types=TARGET_RELATIONS[:8],causal=list(CAUSAL_TYPES)).single()['count']
  if leakage:raise ValueError('Pending/noncausal assertion leaked into canonical target relations')
  if findings!=len(source_findings):raise ValueError('Source finding population mismatch')
  check_source_fingerprints(source_inputs,wg)
  tx.commit()
 return after,findings


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
 p.add_argument('--wg',action='append',choices=['RAN1','RAN2','RAN3','RAN4','RAN5'],help='Explicit WG subset; default all five')
 p.add_argument('--apply',action='store_true');args=p.parse_args()
 if args.out.exists():raise SystemExit('Use a new journal path; existing before images are immutable.')
 args.out.parent.mkdir(parents=True,exist_ok=True)
 report={'schema':2,'observedAtUtc':datetime.now(timezone.utc).isoformat(),
  'mode':'apply' if args.apply else 'read_only','workingGroups':[]}
 for wg in (args.wg or ('RAN1','RAN2','RAN3','RAN4','RAN5')):
  with GraphDatabase.driver(axis.bolt_uri(wg),auth=credentials.neo4j_auth()) as driver,driver.session() as session:
   source_inputs=source_fingerprints(wg)
   before=snapshot(session);changes=build_plan(wg,before)
   check_source_fingerprints(source_inputs,wg)
   # Full before images for every existing ancillary node and edge touched by this producer.
   ancillary=session.run('''MATCH (n) WHERE (n:EvidenceAssertion AND n.assertionId STARTS WITH 'tr-source-')
      OR (n:EvidenceFragment AND (n.evidencePath CONTAINS '/TR/'
          OR EXISTS { MATCH (:TRImpact)-[:HAS_EVIDENCE]->(n) }
          OR EXISTS { MATCH (a:EvidenceAssertion)-[:HAS_EVIDENCE]->(n)
                      WHERE a.assertionId STARTS WITH 'tr-source-' }))
      OPTIONAL MATCH (n)-[r]-(m)
      RETURN elementId(n) AS elementId, labels(n) AS labels,properties(n) AS properties,
      collect(CASE WHEN r IS NULL THEN null ELSE {id:elementId(r),type:type(r),
      properties:properties(r),outgoing:startNode(r)=n,otherId:elementId(m),
      otherLabels:labels(m),otherProperties:properties(m)} END) AS relationships''').data()
   group={'wg':wg,'before':before,'beforeSha256':digest(before),'ancillaryBefore':ancillary,
      'manifestSha256':hashlib.sha256((ROOT/f'ontology/input/tsg/RAN/formal/TR/{wg}/tr_impact_evidence.json').read_bytes()).hexdigest(),
      'sourceFingerprints':source_inputs,'changes':changes,'committed':False}
   report['workingGroups'].append(group)
   write_text_atomic(args.out,json.dumps(report,ensure_ascii=False,indent=2,default=str)+'\n')
   if args.apply:
    after,findings=apply_plan(session,before,changes,wg,source_inputs)
    group.update(after=after,afterSha256=digest(after),sourceFindingCount=findings,committed=True)
   write_text_atomic(args.out,json.dumps(report,ensure_ascii=False,indent=2,default=str)+'\n')
   print(wg,'originalNodes',len(before),'assessedAssertions',len(changes),'verified',sum(c['row']['evidenceStatus']=='source_verified' for c in changes),'committed',group['committed'],flush=True)
 print(args.out)
if __name__=='__main__':main()
