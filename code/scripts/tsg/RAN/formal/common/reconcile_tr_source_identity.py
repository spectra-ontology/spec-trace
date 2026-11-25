#!/usr/bin/env python3
"""Reconcile source-resolved TR titles and vector-source identity provenance.

Spec: operations rulebook §3–4; tr_source_identity_resolutions.json.
Cycle: official identity resolution → full immutable preimage → guarded writes.
Usage: python3 -B reconcile_tr_source_identity.py --out <journal> [--apply]
No source bytes, IDs, embeddings or TR-number keys change. No model/API calls.
"""
import argparse,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'.git').exists())
sys.path.insert(0,str(ROOT/'scripts/common'))
from common import axis,credentials
from common.service_endpoints import QDRANT_URL
from common.exception_notes import add_exception_note
from neo4j import GraphDatabase
from qdrant_client import QdrantClient,models
from tr_source_identity import resolution_for,CONFIG
from document_decision_storage import durable_json


def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,default=str).encode()).hexdigest()


def snapshot(session,number):
 return session.run('''MATCH (t:TechnicalReport {trNumber:$number}) OPTIONAL MATCH(t)-[r]-(n)
 WITH t,r,n ORDER BY elementId(r)
 RETURN elementId(t) AS elementId,labels(t) AS labels,properties(t) AS properties,
 collect(CASE WHEN r IS NULL THEN null ELSE {id:elementId(r),type:type(r),properties:properties(r),
 outgoing:startNode(r)=t,otherId:elementId(n),otherLabels:labels(n),otherProperties:properties(n)} END) AS relationships''',number=number).data()


def verify_points(before,after,projection):
 expected={point.id:point for point in before}
 actual={point.id:point for point in after}
 if len(expected)!=len(before) or len(actual)!=len(after) or set(expected)!=set(actual):
  raise ValueError('TR source identity point coverage changed')
 for pid,point in actual.items():
  old=expected[pid]
  if point.vector!=old.vector:
   raise ValueError('Embedding changed during identity metadata correction')
  if point.payload!={**old.payload,**projection}:
   raise ValueError('TR source identity exact payload postcondition failed')


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
 if a.out.exists():raise SystemExit('Use a new journal path; existing before images are immutable.')
 report={'schema':1,'observedAtUtc':datetime.now(timezone.utc).isoformat(),'mode':'apply' if a.apply else 'read_only','resolutions':[]}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 def save():durable_json(a.out,json.loads(json.dumps(report,ensure_ascii=False,default=str)))
 q=QdrantClient(url=QDRANT_URL,timeout=120)
 try:
  config_path=ROOT/CONFIG;config_bytes=config_path.read_bytes()
  config_sha=hashlib.sha256(config_bytes).hexdigest()
  report['sourceIdentityConfigSha256']=config_sha
  def check_generation():
   if config_path.read_bytes()!=config_bytes:
    raise ValueError('TR source identity configuration changed after planning')
  for config in json.loads(config_bytes)['resolutions']:
   r=resolution_for(ROOT,config['wg'],config['trNumber'],ROOT/config['sourcePath']);wg=r['wg'];number=r['trNumber'];collection=wg.lower()+'_tr_sections'
   check_generation()
   points=[];offset=None;seen_offsets=set();flt=models.Filter(must=[models.FieldCondition(key='trNumber',match=models.MatchValue(value=number))])
   while True:
    batch,offset=q.scroll(collection,scroll_filter=flt,limit=100,offset=offset,with_payload=True,with_vectors=True)
    points.extend(batch)
    if offset is None:break
    if offset in seen_offsets:raise ValueError('Qdrant source identity scroll cursor repeated or cycled')
    seen_offsets.add(offset)
   with GraphDatabase.driver(axis.bolt_uri(wg),auth=credentials.neo4j_auth()) as driver,driver.session() as session:
    before=snapshot(session,number)
    if len(before)!=1:raise ValueError('TR identity must resolve to exactly one existing node')
    check_generation()
    record={'wg':wg,'trNumber':number,'resolution':r,'before':before,'qdrantCollection':collection,'qdrantBefore':[p.model_dump(mode='json') for p in points],'neo4jCommitted':False,'qdrantCompleted':False};report['resolutions'].append(record);save()
    if a.apply:
     with session.begin_transaction() as tx:
      if digest(snapshot(tx,number))!=digest(before):raise ValueError('TR changed after durable preimage')
      check_generation()
      tx.run('''MATCH (t:TechnicalReport {trNumber:$number}) SET t.trTitle=$title,
        t.sourceIdentityAssessmentPath=$path,t.sourceIdentityAssessmentSha256=$sha,
        t.sourceIdentityAssessmentMethod=$method''',number=number,title=r['canonicalTitle'],path=CONFIG,sha=config_sha,method=r['assessmentMethod']).consume()
      check_generation()
      tx.commit()
     record['neo4jCommitted']=True;save()
     projection={'trTitle':r['canonicalTitle'],'sourceIdentityAssessmentPath':CONFIG,
        'sourceIdentityAssessmentSha256':config_sha,
        'sourceDocumentSha256':r['sourceSha256']}
     for point in points:
      current=q.retrieve(collection,ids=[point.id],with_payload=True,with_vectors=False)
      if len(current)!=1 or current[0].payload!=point.payload:raise ValueError('Qdrant source payload changed after durable preimage')
      check_generation()
      q.set_payload(collection,payload=projection,points=[point.id],wait=True)
     record['qdrantCompleted']=True;record['after']=snapshot(session,number)
     after=q.retrieve(collection,ids=[p.id for p in points],with_payload=True,with_vectors=True)
     verify_points(points,after,projection)
     check_generation()
     record['qdrantAfterSha256']=digest([p.model_dump(mode='json') for p in after]);save()
    print(wg,number,'TR node',len(before),'source points',len(points),'applied',a.apply,flush=True)
  check_generation();save()
 finally:
  primary_error=sys.exc_info()[1]
  try:q.close()
  except BaseException as close_error:
   if primary_error is None:raise
   add_exception_note(primary_error,f'Qdrant client close also failed: {type(close_error).__name__}: {close_error}')
if __name__=='__main__':main()
