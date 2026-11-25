#!/usr/bin/env python3
"""review_tr_impact_sources.py — assess source observations for five-WG TR claims.

Spec: operations rulebook §3–4; ontology/schema/tdoc-ontology.ttl EvidenceAssertion.
Ontology: adjudicated claims retain their source-bound scope and evidence.
Cycle: retained original CSV + TR/CR source receipts + target clause observations
       → explicit assessed claims and separately supported study relations.
배경: source observation refresh must preserve an adjudicated primary-source chain.
사용: python3 -B review_tr_impact_sources.py --out <report> [--update-assessments --journal <new-journal>]
LLM 호출: 없음. This tool never promotes a causal claim from token overlap.
The reviewed relation policy is intentionally narrower than the original claim.
"""
from __future__ import annotations
import argparse,base64,copy,csv,fcntl,gzip,hashlib,io,json,os,re,sys
from contextlib import ExitStack
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from tr_impact_evidence import source_text,claim_of,assess_impacts,coverage_counts,SPEC_NUMBER_LEFT,SPEC_NUMBER_RIGHT
from tr_source_identity import resolution_for,CONFIG as IDENTITY_CONFIG
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'.git').exists())
sys.path.insert(0,str(ROOT/'scripts/common'))
from common import review_artifacts
from common.atomic_io import write_text_atomic
WGS=('RAN1','RAN2','RAN3','RAN4','RAN5')
# These passages were individually read as proposed changes, rather than enacted changes.
RECOMMENDATIONS={('RAN1','38.889','38.213'),('RAN1','38.824','38.214'),
 ('RAN3','38.743','38.401'),('RAN4','38.815','38.101-2'),('RAN4','38.863','38.101-5'),
 ('RAN4','38.887','38.101-2'),('RAN4','38.891','38.101-2'),('RAN4','38.768','38.101-1')}
# Administrative history and abbreviation precedence alone are not substantive discussions.
METADATA_ONLY={('RAN2','38.835','38.300'),('RAN5','38.903','38.522')}


def normalize(t):return re.sub(r'\s+',' ',t).strip()

def _number_pattern(numbers):
 values=sorted(set(numbers),key=len,reverse=True)
 return (SPEC_NUMBER_LEFT+'(?:'+'|'.join(re.escape(n) for n in values)+')'+SPEC_NUMBER_RIGHT) if values else r'(?!)'

def _declared_tr_number(header):
 match=re.search(r'3GPP\s+TR\s+(\d{2}\.\d{3}(?:-\d+)*)(?![\w-]|\.\d)',header)
 return match.group(1) if match else None

def source_receipt(path,sha,paragraphs,index,start=0,end=None):
 p=paragraphs[index];end=min(len(p),end if end is not None else start+1400)
 return {'path':str(path.relative_to(ROOT)),'sha256':sha,
  'locator':f'word/document.xml final-view paragraph-text line {index+1}, characters {start}:{end}',
  'quote':p[start:end]}


def _sha(raw):
 return hashlib.sha256(raw).hexdigest()


def _source_snapshot(path):
 raw=path.read_bytes()
 return source_text(path,source_bytes=raw).splitlines(),_sha(raw)


def _json_snapshot(path):
 raw=path.read_bytes()
 return json.loads(raw),_sha(raw)


def _assessment_source_fingerprints():
 """Fence every current canonical assessment and its retained primary sources."""
 from reconcile_tr_impact_evidence import source_fingerprints
 identity_path=ROOT/'ontology/config/tr_source_identity_resolutions.json'
 paths={Path(__file__).resolve(),Path(__file__).with_name('tr_impact_evidence.py'),
        Path(__file__).with_name('docx_text.py'),Path(__file__).with_name('tr_source_identity.py'),
        Path(review_artifacts.__file__).resolve()}
 for wg in WGS:
  paths.update(ROOT/p for p in source_fingerprints(wg))
  paths.update((ROOT/f'ontology/input/tsg/RAN/formal/TR/{wg}').glob('*/*.docx'))
 for name in ('tr_cr_candidate_inventory.json','tr_source_assessments.json'):
  path=review_artifacts.current_review_input(ROOT,name)
  if path.is_file():paths.add(path)
 fingerprints={p:_sha(p.read_bytes()) for p in sorted(paths)}
 fingerprints[identity_path]=_sha(identity_path.read_bytes()) if identity_path.exists() else None
 return fingerprints


def _check_fingerprints(expected):
 for path,sha in expected.items():
  if sha is None:
   if path.exists():raise ValueError(f'Assessment source changed; refusing stale update: {path}')
   continue
  if not path.is_file() or _sha(path.read_bytes())!=sha:
   raise ValueError(f'Assessment source changed; refusing stale update: {path}')


def _persist_json(path,value):
 write_text_atomic(path,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
 descriptor=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(descriptor)
 finally:os.close(descriptor)


def _apply_assessment_updates(replacements,source_fingerprints,journal_path,inventory_check=None):
 """Prepare the whole batch; retain full bytes and roll back owned writes on error.

 Directory locks serialize this tool's writers. Byte fences detect other source
 writers. A crash can leave a recorded partial batch; the durable full preimages
 support recovery. Files with external concurrent changes are preserved.
 """
 journal_path=Path(journal_path)
 if journal_path in source_fingerprints or journal_path in replacements:
  raise ValueError('The journal must be separate from assessment inputs')
 if journal_path.exists():raise ValueError('Use a new assessment journal path')
 for before,after in replacements.values():
  before.decode('utf-8');after.decode('utf-8')
 def encoded(raw):return base64.b64encode(gzip.compress(raw,mtime=0)).decode('ascii')
 entries=[{'path':str(path),'beforeSha256':_sha(before),'afterSha256':_sha(after),
           'beforeGzipBase64':encoded(before),'afterGzipBase64':encoded(after),
           'written':False} for path,(before,after) in replacements.items()]
 report={'schema':1,'state':'prepared','files':entries,
         'sourceFingerprints':{str(p):sha for p,sha in source_fingerprints.items()},
         'atomicity':'Guarded multi-file replacement with durable recovery bytes and exception rollback.'}
 journal_path.parent.mkdir(parents=True,exist_ok=True)
 with ExitStack() as stack:
  for directory in sorted({p.parent for p in replacements}):
   descriptor=os.open(directory,os.O_RDONLY|os.O_DIRECTORY)
   stack.callback(os.close,descriptor)
   fcntl.flock(descriptor,fcntl.LOCK_EX)
  _check_fingerprints(source_fingerprints)
  if inventory_check is not None:inventory_check()
  for path,(before,_) in replacements.items():
   if path.read_bytes()!=before:raise ValueError(f'Assessment preimage changed: {path}')
  # Exclusive reservation protects another run's recovery journal.
  with journal_path.open('x'):pass
  _persist_json(journal_path,report)
  expected=dict(source_fingerprints);attempted=[]
  try:
   for entry,(path,(before,after)) in zip(entries,replacements.items()):
    _check_fingerprints(expected)
    if inventory_check is not None:inventory_check()
    attempted.append((entry,path,before,after))
    write_text_atomic(path,after.decode('utf-8'))
    if path.read_bytes()!=after:raise ValueError(f'Assessment postimage mismatch: {path}')
    expected[path]=_sha(after);entry['written']=True
    _persist_json(journal_path,report)
   _check_fingerprints(expected)
   if inventory_check is not None:inventory_check()
   report['state']='committed'
   _persist_json(journal_path,report)
  except BaseException as exc:
   conflicts=[];rollback_errors=[]
   for entry,path,before,after in reversed(attempted):
    try:
     current=path.read_bytes() if path.is_file() else None
     if current==after:
      write_text_atomic(path,before.decode('utf-8'));entry['restored']=True
     elif current!=before:
      conflicts.append(str(path))
    except Exception as rollback_error:
     rollback_errors.append({'path':str(path),'error':str(rollback_error)})
   report.update(state='recovery_required' if rollback_errors else
                       'external_changes_preserved' if conflicts else 'rolled_back',
                 error=f'{type(exc).__name__}: {exc}',externalConflicts=conflicts,
                 rollbackErrors=rollback_errors)
   _persist_json(journal_path,report)
   raise
 return report


def run(update=False,journal_path=None):
 if update and journal_path is None:
  raise ValueError('Assessment updates require a new durable journal path')
 if update and Path(journal_path).exists():
  raise ValueError('Use a new assessment journal path')
 source_inputs=_assessment_source_fingerprints()
 def source_inventory():
  return tuple(sorted(str(p) for wg in WGS for p in
      (ROOT/f'ontology/input/tsg/RAN/formal/TR/{wg}').glob('*/*.docx')))
 original_inventory=source_inventory()
 def check_inventory():
  if source_inventory()!=original_inventory:
   raise ValueError('Assessment source inventory changed during update')
 initial_files={p:p.read_bytes() for p in source_inputs
                if p.name in {'tr_impact_evidence.json','tr_impact_mapping.csv'}}
 _check_fingerprints(source_inputs)
 replacements={}
 cache={}
 assertions=[];all_sources={};cr_candidates=review_artifacts.current_review_input(ROOT,'tr_cr_candidate_inventory.json')
 raw_candidates=json.loads(cr_candidates.read_text())['workingGroups'] if cr_candidates.is_file() else {}
 target_path=review_artifacts.current_review_input(ROOT,'tr_source_assessments.json')
 targets=json.loads(target_path.read_text())['assertions'] if target_path.is_file() else []
 for wg in WGS:
  directory=ROOT/f'ontology/input/tsg/RAN/formal/TR/{wg}'
  manifest_path=directory/'tr_impact_evidence.json';manifest=json.loads(initial_files[manifest_path])
  original=list(csv.DictReader(io.StringIO(manifest['originalCsv']['contentUtf8'])))
  csv_path=directory/'tr_impact_mapping.csv'
  current=list(csv.DictReader(io.StringIO(initial_files[csv_path].decode('utf-8'))))
  updated=[]
  for row_index,row in enumerate(current):
   claim=claim_of(row);tr=claim['trNumber'];target=claim['impactsSpec'];key=(wg,tr,target)
   previous=next((e for e in manifest['claims'] if e['claim']==claim),None)
   if previous:
    entry=copy.deepcopy(previous)
   elif row_index<len(original):
    entry={'claim':claim,'status':'pending','originalCsvLine':row_index+2,'originalRow':original[row_index]}
   else:
    raise ValueError(f'{wg}: a newly discovered claim needs an explicit provenance entry before assessment: {claim}')
   preserve_adjudication=entry['status'] in {'verified','rejected'}
   adjudicated={name:copy.deepcopy(entry[name]) for name in
                ('sourceReview','sourceEvidence','supportedStudyAssertions')
                if name in entry} if preserve_adjudication else {}
   if entry['status']=='verified':
    # Fresh lexical observations cannot replace a source-bound adjudication.
    # Require its current primary receipts before reusing that adjudication.
    assess_impacts(ROOT,wg,[dict(row)])
   evidence=[];mentions=[];identities=[];inventory=[];scope_evidence=[]
   paths=sorted((directory/tr).glob('*.docx'))
   for path in paths:
    relative=str(path.relative_to(ROOT))
    if relative not in cache:
     cache[relative]=_source_snapshot(path)
    paragraphs,sha=cache[relative];all_sources[relative]=sha
    inventory.append({'path':relative,'sha256':sha,'paragraphCount':len(paragraphs)})
    header='\n'.join(paragraphs[:18]);declared=_declared_tr_number(header)
    resolution=resolution_for(ROOT,wg,tr,path)
    identities.append({'path':relative,'declaredTrNumber':declared,
      'matchesClaim':True if resolution else declared==tr if declared else None,
      **({'resolution':'official_archive_and_registry_resolved_template_error',
          'canonicalTrNumber':resolution['trNumber'],'registryUrl':resolution['registryUrl'],
          'sourceIdentityAssessmentPath':IDENTITY_CONFIG,
          'sourceIdentityAssessmentSha256':_sha((ROOT/IDENTITY_CONFIG).read_bytes()),
          'officialArchiveEvidenceSha256':resolution['officialArchiveEvidenceSha256']} if resolution else {})})
    scope_indices=[i for i,p in enumerate(paragraphs) if re.match(r'^\s*1\s+Scope\s*$',p,re.I)]
    if scope_indices:
     i=scope_indices[-1]+1
     while i<len(paragraphs) and not paragraphs[i].strip():i+=1
     if i<len(paragraphs):scope_evidence.append(source_receipt(path,sha,paragraphs,i))
    if not target:continue
    pattern=re.compile(_number_pattern([target]))
    for i,p in enumerate(paragraphs):
     m=pattern.search(p)
     if not m:continue
     bibliographic=bool(re.match(r'^\s*(?:\[[^]]+\]\s*)?(?:3GPP[,\s]+)?(?:TS|TR)\s*\d',p,re.I))
     receipt=source_receipt(path,sha,paragraphs,i,max(0,m.start()-500),max(0,m.start()-500)+1500)
     mentions.append({'bibliographic':bibliographic,'receipt':receipt})
   # These fields describe observed source content; they do not assert incorporation.
   good_identity=all(i['matchesClaim'] is not False for i in identities)
   body=[m['receipt'] for m in mentions if not m['bibliographic']]
   ref=[m['receipt'] for m in mentions if m['bibliographic']]
   evidence=(body[:2] or ref[:1])+scope_evidence[:1]
   if not evidence and inventory:
    path=ROOT/inventory[0]['path'];paragraphs,sha=cache[inventory[0]['path']]
    i=next((i for i,p in enumerate(paragraphs) if len(p.strip())>30),0)
    evidence=[source_receipt(path,sha,paragraphs,i)]
   if not evidence:raise ValueError(f'No actual source receipt for {wg}: {claim}')
   if entry['status']=='verified':
    verdict='supported_narrow_incorporation';explanation=entry['reviewExplanation']
   elif entry['status']=='rejected':
    verdict='contradicted_no_change_claim';explanation=entry['rejectionExplanation']
   elif not good_identity:
    verdict='not_established_source_identity_conflict'
    explanation=f"Claim for TR {tr} has a source whose cover identifies a different TR ({identities}). Establish the correct source identity before evaluating NoChange or target incorporation."
   elif row['impactType']=='NoChange':
    verdict='not_established_negative_claim'
    explanation=f"Reviewed TR {tr} scope and available conclusions describe a study/reference purpose. This does not establish the original universal NoChange assertion: no bounded target-specification set, source/target release comparison, or explicit approved no-change disposition is supplied. Retain NoChange as an assessed pending claim."
   elif body:
    verdict='not_established_incorporation'
    explanation=f"TR {tr} explicitly discusses TS {target} in its body ({len(body)} source paragraph occurrences across {len(paths)} editions). The quoted scope/discussion or proposed normative work supports a study relation; it does not establish the original {row['impactType']} claim, its clause location, or an approved source-to-target change. A matching enacted change receipt and target edition remain required."
   elif ref:
    verdict='not_established_citation_only'
    explanation=f"TR {tr} lists TS {target} as a reference ({len(ref)} bibliographic occurrences), with no exact target-number occurrence in the reviewed source body. A bibliography entry supports citation only; the original {row['impactType']} claim requires an enacted change receipt and target edition."
   else:
    verdict='not_established_target_link'
    explanation=f"Reviewed {len(paths)} local TR {tr} source editions, scope, conclusions and exact TS {target} mentions. The source establishes the study purpose, but supplies no exact TS-number passage for this candidate. The original {row['impactType']} claim needs a target-specific source link and enacted change receipt."
   section=next((e.get('sourceReview',{}).get('targetSectionObservations',e.get('targetSectionObservations')) for e in targets if e['wg']==wg and e['claim']==claim),None)
   if section is not None:
    explanation+=(' Target-clause observations are preserved separately; clause existence does not establish causal incorporation.' if section else ' The specified target clause is also absent from the current parsed TS edition population; no Section is fabricated.')
   entry['sourceReview']={'verdict':verdict,'reviewScope':'TR source identity, actual scope, conclusions and all exact target-number paragraph occurrences; retained CR candidate reasons were cross-checked separately; parsed target-clause observations when specified.',
    'reviewExplanation':explanation,'sources':inventory,'sourceIdentities':identities,
    'bodyTargetMentionCount':len(body),'bibliographicTargetMentionCount':len(ref),
    'targetSectionObservations':section,'reviewer':'Codex source assessment; no domain-expert certification claimed'}
   candidate_pattern=re.compile(_number_pattern([tr]))
   entry['sourceReview']['crCandidateMatches']=[
      {'id':c['id'],'targetSpecNumber':c['spec'],'reason':c.get('reason',''),'summary':c.get('summary',''),
       'meaning':'Discovery candidate; review the primary CR and its target-specific disposition before an enacted-change claim.'}
      for c in raw_candidates.get(wg,[]) if target and c.get('spec')==target
      and candidate_pattern.search(c.get('reason','')+' '+c.get('summary',''))]
   evidence+=entry.get('targetEvidence',[])+entry.get('additionalSourceEvidence',[])+entry.get('rejectionEvidence',[])
   entry['sourceEvidence']=evidence
   if entry['status']!='verified':
    entry['reason']=explanation
    if entry['status']=='rejected':
     row['impactDescription']=entry['rejectedImpactDescription']
    elif not good_identity:
     row['impactDescription']=f"Assessed {row['impactType']} candidate for TR {tr}; the retained document cover identifies another TR. Source identity and the original claim remain explicitly pending."
    else:
     scope=normalize(scope_evidence[0]['quote'])[:550] if scope_evidence else 'Scope is retained in the attached source receipts.'
     row['impactDescription']=(f"Assessed {row['impactType']} candidate for TR {tr}"+
       (f" concerning TS {target}" if target else '')+
       f". Source scope: {scope} "+
       ('A bounded explicit no-change determination remains pending.' if row['impactType']=='NoChange'
        else 'The historical incorporation claim remains pending; separately supported study relations retain their own receipts.'))
   supported=[]
   if good_identity and body and key not in METADATA_ONLY:
    # A conservative body passage is sufficient for this expressly noncausal relation.
    selected=body[0]
    if key in RECOMMENDATIONS:
     recommendation=next((e for e in body if re.search(r'\b(?:should|need|expected|recommended|concluded to support|standard impacts|specification impacts|to be added)\b',e['quote'],re.I)),None)
     if recommendation:selected=recommendation
    supported.append({'predicate':'discussesSpec','description':f'TR {tr} discusses TS {target} in its source body.','evidence':selected})
    if key in RECOMMENDATIONS and recommendation:
     supported.append({'predicate':'recommendsChangeToSpec','description':f'TR {tr} identifies proposed normative work concerning TS {target}; this is a recommendation, not proof of enacted incorporation.','evidence':selected})
   supported+=entry.get('additionalSourceAssertions',[])
   entry['supportedStudyAssertions']=supported
   observations={name:copy.deepcopy(entry[name]) for name in
                 ('sourceReview','sourceEvidence','supportedStudyAssertions')}
   if preserve_adjudication:
    for name in ('sourceReview','sourceEvidence','supportedStudyAssertions'):
     if name in adjudicated:entry[name]=adjudicated[name]
     else:entry.pop(name,None)
   updated.append(entry)
   assertions.append({'wg':wg,'csvLine':row_index+2,'claim':claim,'status':entry['status'],'currentDescription':row['impactDescription'],
    'sourceReview':entry['sourceReview'],'sourceEvidence':entry['sourceEvidence'],
    **({'supportedStudyAssertions':entry['supportedStudyAssertions']} if 'supportedStudyAssertions' in entry else {}),
    **({'currentSourceObservations':observations} if preserve_adjudication else {})})
  if update:
   manifest['claims']=updated;manifest['assessmentCoverage']={**coverage_counts(updated),'includesExplicitNegativeClaims':True,
      'meaning':'All original assertions have a source assessment; pending identifies a specified missing entailment, not an unreviewed row.'}
   manifest['assertionPolicy']='Preserve all source-assessed original claims, including explicit NoChange. Only a verified narrow incorporation receipt authorizes causal target edges. Independently supported study relations retain separate evidence assertions.'
   replacements[manifest_path]=(initial_files[manifest_path],
      (json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
   output=io.StringIO(newline='')
   writer=csv.DictWriter(output,fieldnames=current[0].keys(),lineterminator='\n')
   writer.writeheader();writer.writerows(current)
   replacements[csv_path]=(initial_files[csv_path],output.getvalue().encode('utf-8'))
 _check_fingerprints(source_inputs)
 if _assessment_source_fingerprints()!=source_inputs:
  raise ValueError('Assessment source inventory changed during review')
 check_inventory()
 update_receipt=_apply_assessment_updates(replacements,source_inputs,journal_path,check_inventory) if update else None
 return {'schema':1,'assertionCount':len(assertions),'sourceDocxCount':len(all_sources),
    'sourceInputsStableAtAssessmentCompletion':True,'assessmentUpdate':update_receipt,
    'sourceInventory':[{'path':p,'sha256':s} for p,s in all_sources.items()],
    'crCandidateCounts':{wg:len(rows) for wg,rows in raw_candidates.items()},
    'reviewBoundary':'Full source files were parsed and hashed; semantic review used source identities, actual scope/conclusion passages, target-number occurrences and existing exact CR incorporation receipts. This is not a claim that every paragraph of every TR or every historical TS change was individually adjudicated.',
    'assertions':assertions}


def _discover_cr_source(task):
 """Read an actual accepted DOCX; matches remain discovery candidates."""
 relative, pattern = task
 path=ROOT/relative
 try:
  paragraphs,sha=_source_snapshot(path)
  regex=re.compile(pattern)
  hits=[]
  for index,paragraph in enumerate(paragraphs):
   for match in regex.finditer(paragraph):
    start=max(0,match.start()-500);end=min(len(paragraph),match.end()+900)
    hits.append({'trNumber':match.group(), 'locator':f'word/document.xml final-view paragraph-text line {index+1}, characters {start}:{end}',
      'quote':paragraph[start:end], 'previousParagraph':paragraphs[index-1] if index else '',
      'nextParagraph':paragraphs[index+1] if index+1<len(paragraphs) else ''})
  return {'path':relative,'sha256':sha,
    'paragraphCount':len(paragraphs),'mentions':hits}
 except Exception as error:
  return {'path':relative,'error':type(error).__name__+': '+str(error)}


def discover_cq_evidence(workers=4):
 """Inspect the retained local change/report corpus for the original CQ scopes.

 No token match entails enactment, and an empty retained-corpus search does not
 prove NoChange. Exact source spans are produced for subsequent adjudication.
 """
 meaning_path=ROOT/'logs/common/verification/decision-dispositions/tr_cq_meaning_reconciliation.json'
 assessments_path=review_artifacts.current_review_input(ROOT,'tr_source_assessments.json')
 meaning,meaning_sha=_json_snapshot(meaning_path)
 assessment,assessment_sha=_json_snapshot(assessments_path)
 questions=[q for q in meaning['manualReviewOfAll20ObservedShortfalls']
            if q['meaning']=='verified_causal_incorporation_or_bounded_NoChange']
 assessments=assessment['assertions']
 result={'purpose':'Additional source discovery for unchanged causal/NoChange questions; candidates never auto-promote an assertion.',
  'boundary':'Parsed-CR selected source files, current checked document-decision entry population, and retained TR scope/conclusion text. NoChange is not established by corpus absence.',
  'inputs':{str(meaning_path.relative_to(ROOT)):meaning_sha,str(assessments_path.relative_to(ROOT)):assessment_sha},
  'questions':questions,'workingGroups':{}}
 for wg in ('RAN3','RAN4','RAN5'):
  selected={}
  for q in questions:
   if q['wg']!=wg:continue
   selection=q['sourceAssessmentReceipt']['selection']
   for assertion in assessments:
    claim=assertion['claim']
    if assertion['wg']!=wg:continue
    if any(selection[key] and value not in selection[key] for key,value in (
       ('trNumbers',claim['trNumber']),('targetSpecNumbers',claim['impactsSpec']),('claimTypes',claim['impactType']))):continue
    selected[(claim['trNumber'],claim['impactsSpec'])]=assertion
  tr_numbers=sorted({tr for tr,target in selected})
  pattern=_number_pattern(tr_numbers)
  regex=re.compile(pattern)
  specs={target for tr,target in selected if target}
  wildcard=any(not target for tr,target in selected)
  parsed_path=ROOT/f'ontology/output/tsg/RAN/formal/parsed_cr/{wg}/cr_documents.json'
  parsed_data,parsed_sha=_json_snapshot(parsed_path)
  parsed=parsed_data['documents']
  documents=[cr for cr in parsed if wildcard or cr.get('spec_number') in specs]
  by_path={}
  for cr in documents:
   by_path.setdefault(cr['source_path'],[]).append({key:cr.get(key) for key in (
    'tdoc_number','spec_number','cr_number','rev','reason_for_change','summary_of_change','clauses_affected')})
  inventory=[]; candidates=[]; errors=[]
  with ProcessPoolExecutor(max_workers=workers) as pool:
   for index,source in enumerate(pool.map(_discover_cr_source,((path,pattern) for path in sorted(by_path)),chunksize=8),1):
    if 'error' in source:errors.append(source)
    else:
     inventory.append({key:source[key] for key in ('path','sha256','paragraphCount')})
     if source['mentions']:
      source['parsedCRRows']=by_path[source['path']];candidates.append(source)
    if index%1000==0:print(f'{wg} actual CR sources {index}/{len(by_path)}; mentions {len(candidates)}; parse errors {len(errors)}',flush=True)
  report_path=ROOT/f'ontology/output/tsg/RAN/formal/instances/phase-2/{wg}/resolutions_document_dispositions.jsonld'
  report_data,report_sha=_json_snapshot(report_path)
  report_nodes=report_data['@graph']; report_matches=[]
  for node in report_nodes:
   if regex.search(node['content']):report_matches.append({key:node.get(key) for key in ('resolutionId','content','madeAt','aboutTdoc','@type')})
  tr_inventory=[]
  for tr in tr_numbers:
   for path in sorted((ROOT/f'ontology/input/tsg/RAN/formal/TR/{wg}/{tr}').glob('*.docx')):
    paragraphs,sha=_source_snapshot(path);passages=[]
    for index,paragraph in enumerate(paragraphs):
     if re.match(r'^\s*(?:\d+(?:\.\d+)*\s+)?(?:Scope|Conclusions?|Summary and conclusions?)\s*$',paragraph,re.I):
      passages.append({'headingLine':index+1,'quote':'\n'.join(paragraphs[index:index+24])})
    tr_inventory.append({'trNumber':tr,'path':str(path.relative_to(ROOT)),'sha256':sha,
      'paragraphCount':len(paragraphs),'scopeConclusionPassages':passages})
  result['workingGroups'][wg]={'selectedOriginalClaims':[{'claim':a['claim'],'csvLine':a['csvLine'],'status':a['status']} for a in selected.values()],
   'parsedCRInput':{'path':str(parsed_path.relative_to(ROOT)),'sha256':parsed_sha,
                   'allParsedRows':len(parsed),'selectedParsedRows':len(documents)},
   'crSourceInventory':inventory,'crSourceErrors':errors,'crSourceCandidates':candidates,
   'documentDecisionSource':{'path':str(report_path.relative_to(ROOT)),'sha256':report_sha,
     'allEntries':len(report_nodes),'matchingEntries':report_matches},'trSourceInventory':tr_inventory}
  print(f'{wg} discovery complete: {len(inventory)} actual CR files; {len(candidates)} candidates; {len(report_matches)} report entries; {len(tr_inventory)} TR sources',flush=True)
 return result


def discover_target_spec_evidence(workers=4):
 """Read retained target editions for exact TR references and nearby meaning."""
 meaning_path=ROOT/'logs/common/verification/decision-dispositions/tr_cq_meaning_reconciliation.json'
 assessments_path=review_artifacts.current_review_input(ROOT,'tr_source_assessments.json')
 meaning,meaning_sha=_json_snapshot(meaning_path)
 assessment,assessment_sha=_json_snapshot(assessments_path)
 questions=[q for q in meaning['manualReviewOfAll20ObservedShortfalls']
            if q['meaning']=='verified_causal_incorporation_or_bounded_NoChange']
 assertions=assessment['assertions']
 result={'purpose':'Exact retained target-TS source search for the unchanged causal CQ scopes; references remain discovery candidates until their meaning is adjudicated.',
  'boundary':'Actual local DOCX target editions only. A reference is not itself causal incorporation, and corpus absence is not NoChange.',
  'inputs':{str(meaning_path.relative_to(ROOT)):meaning_sha,str(assessments_path.relative_to(ROOT)):assessment_sha},'workingGroups':{}}
 for wg in ('RAN3','RAN4','RAN5'):
  pairs=set()
  for q in questions:
   if q['wg']!=wg:continue
   selection=q['sourceAssessmentReceipt']['selection']
   for assertion in assertions:
    c=assertion['claim']
    if assertion['wg']!=wg:continue
    if any(selection[key] and value not in selection[key] for key,value in (
      ('trNumbers',c['trNumber']),('targetSpecNumbers',c['impactsSpec']),('claimTypes',c['impactType']))):continue
    if c['impactsSpec']:pairs.add((c['trNumber'],c['impactsSpec']))
  tasks=[]
  for spec in sorted({spec for tr,spec in pairs}):
   trs=sorted({tr for tr,target in pairs if target==spec},key=len,reverse=True)
   pattern=_number_pattern(trs)
   tasks.extend((str(p.relative_to(ROOT)),pattern) for p in sorted((ROOT/f'ontology/input/tsg/RAN/formal/TS/{wg}/{spec}').glob('*.docx')))
  sources=[]
  with ProcessPoolExecutor(max_workers=workers) as pool:
   for index,source in enumerate(pool.map(_discover_cr_source,tasks,chunksize=1),1):
    sources.append(source)
    print(f'{wg} actual target TS sources {index}/{len(tasks)}',flush=True)
  result['workingGroups'][wg]={'selectedPairs':[{'trNumber':tr,'specNumber':spec} for tr,spec in sorted(pairs)],'sources':sources}
 return result


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
 p.add_argument('--update-assessments',action='store_true')
 p.add_argument('--journal',type=Path,help='New durable recovery journal, required for --update-assessments')
 p.add_argument('--discover-cq-evidence',action='store_true',help='Read actual local sources for the unchanged causal CQ selectors; produce candidates only.')
 p.add_argument('--discover-target-spec-evidence',action='store_true',help='Read actual retained target TS editions for the causal CQ selectors; produce source spans only.')
 p.add_argument('--workers',type=int,default=4);a=p.parse_args()
 discovery=a.discover_cq_evidence or a.discover_target_spec_evidence
 if a.discover_cq_evidence and a.discover_target_spec_evidence:p.error('Choose one discovery corpus per output receipt.')
 if discovery and a.update_assessments:p.error('Discovery preserves all assertion statuses; use a separate reviewed update.')
 if a.update_assessments and (a.journal is None or a.journal.resolve()==a.out.resolve()):
  p.error('--update-assessments requires a new --journal separate from --out')
 if a.workers<1:p.error('--workers must be positive')
 result=(discover_cq_evidence(a.workers) if a.discover_cq_evidence else
         discover_target_spec_evidence(a.workers) if a.discover_target_spec_evidence else run(a.update_assessments,a.journal))
 a.out.parent.mkdir(parents=True,exist_ok=True);write_text_atomic(a.out,json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 if discovery:return
 from collections import Counter
 print('TR assessments',result['assertionCount'],'sourceDOCX',result['sourceDocxCount'],Counter(e['sourceReview']['verdict'] for e in result['assertions']))
 print('supported noncausal assertions',sum(len(e.get('supportedStudyAssertions',[])) for e in result['assertions']))
if __name__=='__main__':main()
