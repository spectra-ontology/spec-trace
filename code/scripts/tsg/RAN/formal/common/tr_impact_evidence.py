#!/usr/bin/env python3
"""tr_impact_evidence.py — TR 영향 주장의 원본 자료 검증 상태를 확인한다.

Spec: docs/common/process/spectra_operations_rulebook.md §3.1, §4.1.
Ontology: NewTS/NewSection/ExtendSection은 검증된 반영 인과 주장이다.
Cycle: 원래 매핑과 원본 자료·인용 검증 기록 → 생성기/적재기 사전 검사 → TRImpact.
배경: 주제 대응과 절 번호 존재만으로 반영 인과를 확정하지 않는다.
사용: 생성·적재 전에 require_verified_impacts(root, wg, rows)를 호출한다.
LLM 호출: 없음. 로컬 원본 자료의 해시·인용·주장 일치만 검사한다.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'common'))
from common.review_artifacts import resolve_recorded_path
from common.atomic_io import write_text_atomic

CAUSAL_TYPES = frozenset(('NewTS', 'NewSection', 'ExtendSection'))
VERIFIED_IMPACT_SCOPES = frozenset(('new_specification', 'new_section', 'existing_section_change',
    'published_definition_reuse', 'published_analysis_reuse', 'explicit_no_change'))
NAMESPACE = 'https://w3id.org/spectra#'
# 규격 번호 토큰 경계: 앞쪽은 단어·점·하이픈이 붙지 않은 자리이거나 원문에서 띄어 쓰지 않은
# 'TS'·'TR' 접두어(예: 'TS38.101-1') 바로 뒤이고, 뒤쪽은 하위 번호(-N·.N)나 단어가 이어지지 않는 자리다.
SPEC_NUMBER_LEFT = r'(?:(?<![\w.-])|(?<=\bT[SR]))'
SPEC_NUMBER_RIGHT = r'(?![\w-]|\.\d)'
_SOURCE_TEXT_CACHE = {}


class ImpactEvidenceError(ValueError):
    """출처 검증 대기 주장을 검증된 인과관계로 등록하려 할 때 발생하는 오류다."""


def _value(row, name):
    value = row.get(name, row.get('tdoc:' + name, ''))
    if isinstance(value, dict):
        value = value.get('@id', '')
    return '' if value is None else str(value)


def claim_of(row):
    tr = _value(row, 'trNumber') or _value(row, 'impactOfTR')
    spec = _value(row, 'impactsSpec') or _value(row, 'candidateImpactsSpec')
    section = _value(row, 'affectedSection') or _value(row, 'impactsSection') or _value(row, 'candidateImpactsSection')
    # A section reference must not be mistaken for a raw clause number.
    if ':' in section or '/' in section:
        sid = section.rsplit('/', 1)[-1].split(':')[-1]
        section = sid.split('-Rel-')[-1].split('-', 1)[-1] if '-Rel-' in sid else sid
    return {'trNumber': tr.rsplit('/', 1)[-1].split(':')[-1].replace('_', '.'),
            'impactType': _value(row, 'impactType'),
            'impactsSpec': spec.rsplit('/', 1)[-1].split(':')[-1].replace('_', '.'),
            'impactsSection': section}


def source_text(path, *, source_bytes=None):
    data = path.read_bytes() if source_bytes is None else source_bytes
    if path.suffix.lower() == '.docx':
        import docx_text
        with zipfile.ZipFile(io.BytesIO(data)) as package:
            raw = docx_text.zip_part(package, 'word/document.xml')
            try:
                document = ET.fromstring(raw)
            except ET.ParseError:
                # Use the shared deterministic tag-balancing repair and demand
                # a strict parse afterwards; never discard unparseable content.
                repaired, changes = docx_text.repair_tag_balance(raw)
                if not changes:
                    raise
                document = ET.fromstring(repaired)
        return '\n'.join(docx_text.final_text(p) for p in document.iter(
            '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'))
    return data.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')


def _bound_source(root, evidence):
    """Read the recorded or relocated source and verify its recorded SHA-256."""
    try:
        if not isinstance(evidence, dict):
            raise ValueError('TRImpact source binding must be an object')
        if 'bytes' in evidence and (type(evidence['bytes']) is not int or evidence['bytes'] < 0):
            raise ValueError('nonnegative integer byte count required')
        return resolve_recorded_path(root, evidence.get('path'), evidence.get('sha256'),
                                     expected_bytes=evidence.get('bytes'))
    except (ValueError, OSError) as exc:
        raise ImpactEvidenceError(f'TRImpact source binding: {exc}') from exc


def _receipt(root, evidence):
    path = _bound_source(root, evidence)
    source_bytes = path.read_bytes()
    current_sha = hashlib.sha256(source_bytes).hexdigest()
    if current_sha != evidence['sha256']:
        raise ImpactEvidenceError(f'TRImpact 원본 자료의 SHA 불일치: {evidence["path"]}')
    if any(not isinstance(evidence.get(field), str) or not evidence[field].strip()
           for field in ('quote', 'locator')):
        raise ImpactEvidenceError('TRImpact 증거의 원문 인용·위치가 필요합니다')
    normalize = lambda text: re.sub(r'\s+', ' ', text).strip()
    key = (str(path.resolve()), current_sha)
    if key not in _SOURCE_TEXT_CACHE:
        _SOURCE_TEXT_CACHE[key] = normalize(source_text(path, source_bytes=source_bytes))
    if normalize(evidence['quote']) not in _SOURCE_TEXT_CACHE[key]:
        raise ImpactEvidenceError(f'TRImpact 인용이 현재 원문에 없음: {evidence["path"]}')


def coverage_counts(entries):
    """manifest의 assessmentCoverage가 담는 세 집계를 claims 목록에서 계산한다."""
    return {'allInputClaims': len(entries),
            'retainedOriginalClaims': sum(bool(e.get('originalRow')) for e in entries),
            'sourceDiscoveredClaims': sum(e.get('inputOrigin') == 'source_discovery' for e in entries)}


def _require_manifest_identity(wg, manifest):
    """manifest의 WG·schema 신원과, 기록되어 있으면 assessmentCoverage 집계를 claims와 대조한다."""
    if manifest.get('wg') != wg or manifest.get('schema') != 1:
        raise ImpactEvidenceError(f'{wg}: TRImpact 증거 manifest 신원 불일치')
    if 'assessmentCoverage' in manifest:
        expected = coverage_counts(manifest.get('claims', []))
        recorded = {name: manifest['assessmentCoverage'].get(name) for name in expected}
        if recorded != expected:
            raise ImpactEvidenceError(f'{wg}: assessmentCoverage 집계 {recorded}가 claims 집계 {expected}와 다릅니다')


def require_verified_impacts(root, wg, rows, *, _manifest=None):
    """인과 주장마다 현재 원본 자료와 일치하는 검증 기록을 요구한다.

    NewTS·NewSection·ExtendSection의 근거, 검증 상태, 설명과 원본 자료의 해시를 검사한다.
    검증 대기 주장이 있으면 ImpactEvidenceError를 발생시켜 적재를 중단한다.
    이 함수는 기존 주장과 후보 기록을 수정하지 않는다. NoChange·TopicalCandidate는
    이 인과 검사의 대상에서 제외한다.
    """
    root = Path(root)
    rows = [row for row in rows if _value(row, 'impactType') in CAUSAL_TYPES]
    claims = [claim_of(row) for row in rows]
    if not claims:
        return
    path = root / f'ontology/input/tsg/RAN/formal/TR/{wg}/tr_impact_evidence.json'
    if not path.is_file():
        raise ImpactEvidenceError(f'{wg}: 반영 인과 검증 기록 파일 없음: {path.relative_to(root)}')
    manifest = json.loads(path.read_bytes()) if _manifest is None else _manifest
    _require_manifest_identity(wg, manifest)
    entries = manifest.get('claims', [])
    pending = []
    for claim, row in zip(claims, rows):
        matches = [entry for entry in entries if entry.get('claim') == claim]
        if len(matches) != 1:
            pending.append(f'{claim}: 이 주장과 정확히 일치하는 검증 기록 1개가 필요함')
            continue
        entry = matches[0]
        if entry.get('inputOrigin') == 'source_discovery':
            discovery = entry.get('discoveryEvidence', {})
            if entry.get('originalRow') or claim_of(entry.get('discoveredInputRow', {})) != claim:
                raise ImpactEvidenceError(f'{claim}: source-discovery provenance mismatch')
            try:
                _bound_source(root, discovery)
            except ImpactEvidenceError as exc:
                raise ImpactEvidenceError(f'{claim}: source-discovery provenance mismatch: {exc}') from exc
        if entry.get('status') != 'verified':
            pending.append(f'{claim}: 출처 검증 대기')
            continue
        if (not entry.get('verifiedImpactDescription')
                or _value(row, 'impactDescription') != entry['verifiedImpactDescription']):
            raise ImpactEvidenceError(f'{claim}: 검증된 범위의 설명과 현재 주장이 다릅니다')
        evidence = entry.get('incorporationEvidence')
        if not isinstance(evidence, dict) or evidence.get('kind') != 'incorporation':
            raise ImpactEvidenceError(f'{claim}: 반영 인과를 입증하는 원본 자료가 필요합니다')
        if not entry.get('reviewExplanation'):
            raise ImpactEvidenceError(f'{claim}: 원문으로 해당 주장을 뒷받침하는 판정 근거가 필요합니다')
        _verified_scope(root, entry, claim)
        _receipt(root, evidence)
        if entry['verifiedImpactDescription'].startswith('Agreed CR '):
            approval = entry.get('approvalEvidence', {})
            if (approval.get('kind') != 'target_specific_document_agreement'
                    or approval.get('targetTdocNumber') != evidence.get('changeDocument')
                    or approval.get('dispositionCode') != 'agreed'
                    or not approval.get('assessmentMethod')):
                raise ImpactEvidenceError(f'{claim}: Agreed CR requires target-specific source disposition evidence')
            _receipt(root, approval)
    if pending:
        raise ImpactEvidenceError(f'{wg}: {len(pending)}/{len(claims)} 인과 주장 출처 검증 대기; '
                                  f'원래 주장·후보 보존: {path.relative_to(root)}; '
                                  + '; '.join(pending[:3]))


EVIDENCE_FIELDS = ('evidenceStatus', 'verifiedImpactScope', 'evidencePath', 'evidenceSha256',
                   'evidenceLocator', 'evidenceQuote', 'assessmentMethod')


def _verified_scope(root, entry, claim):
    scope = entry.get('verifiedImpactScope')
    assessment = entry.get('scopeAssessment', {})
    if (scope not in VERIFIED_IMPACT_SCOPES or assessment.get('scope') != scope
            or not assessment.get('explanation') or not assessment.get('evidence')
            or ((claim['impactType'] == 'NoChange') != (scope == 'explicit_no_change'))):
        raise ImpactEvidenceError(f'{claim}: verified impact requires an explicit source-bound operation scope')
    for evidence in assessment['evidence']:
        _receipt(root, evidence)
    return scope


def fragment_of(evidence):
    receipt={k:evidence[k] for k in ('path','sha256','locator','quote')}
    token=hashlib.sha256(json.dumps(receipt,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return {'@id':NAMESPACE+'evidence/'+token,'@type':'EvidenceFragment',
        **{'evidence'+key[0].upper()+key[1:]:value for key,value in receipt.items()}}


def assess_impacts(root, wg, rows):
    """Annotate every assertion; pending records remain usable as candidates.

    A verified record applies only to its exact reviewed claim and description.
    All other records retain their original content with explicit pending status.
    This operation never interprets absent evidence as NoChange.
    """
    root = Path(root)
    manifest_path = root / f'ontology/input/tsg/RAN/formal/TR/{wg}/tr_impact_evidence.json'
    manifest_bytes = manifest_path.read_bytes() if manifest_path.is_file() else None
    manifest = json.loads(manifest_bytes) if manifest_bytes is not None else {}
    if manifest:
        _require_manifest_identity(wg, manifest)
    entries = manifest.get('claims', [])
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest() if manifest else ''
    for row in rows:
        if not _value(row, 'impactType'):
            continue
        claim = claim_of(row)
        matches = [(i, e) for i, e in enumerate(entries) if e.get('claim') == claim]
        if len(matches) > 1:
            raise ImpactEvidenceError(f'{wg}: duplicate claim receipts: {claim}')
        index, entry = matches[0] if matches else (None, {})
        status = 'source_verified' if entry.get('status') == 'verified' else 'rejected' if entry.get('status') == 'rejected' else 'pending'
        if status == 'source_verified':
            if claim['impactType'] not in CAUSAL_TYPES | {'NoChange'}:
                raise ImpactEvidenceError(f'{wg}: unrecognized verified impactType: {claim["impactType"]}')
            require_verified_impacts(root, wg, [row], _manifest=manifest)
            evidence = entry.get('incorporationEvidence')
            if not isinstance(evidence, dict):
                raise ImpactEvidenceError(f'{claim}: source_verified requires a source verification record')
            if claim['impactType'] == 'NoChange':
                if (evidence.get('kind') != 'explicit_no_change'
                        or not entry.get('boundedScope')
                        or not entry.get('reviewExplanation')
                        or _value(row, 'impactDescription') != entry.get('verifiedImpactDescription')):
                    raise ImpactEvidenceError(f'{claim}: verified NoChange requires explicit negative evidence, boundedScope and its exact reviewed description')
            _receipt(root, evidence)
            scope = _verified_scope(root, entry, claim)
            attrs = {'evidenceStatus': status, 'verifiedImpactScope': scope, 'evidencePath': evidence['path'],
                     'evidenceSha256': evidence['sha256'], 'evidenceLocator': evidence['locator'],
                     'evidenceQuote': evidence['quote'], 'assessmentMethod': entry['reviewExplanation']}
        else:
            attrs = {'evidenceStatus': status, 'evidencePath': str(manifest_path.relative_to(root)) if manifest else '',
                     'evidenceSha256': manifest_sha, 'evidenceLocator': f'claims[{index}]' if index is not None else 'unassessed input claim',
                     'evidenceQuote': '', 'assessmentMethod': entry.get('reason', 'Candidate assertion; primary-source incorporation or explicit no-change evidence requires review.')}
        receipts=list(entry.get('sourceEvidence', []))
        if status=='source_verified':
            receipts.insert(0,entry['incorporationEvidence'])
            if entry.get('approvalEvidence'):
                receipts.append(entry['approvalEvidence'])
        fragments={}
        for receipt in receipts:
            _receipt(root,receipt)
            fragment=fragment_of(receipt);fragments[fragment['@id']]=fragment
        prefix = 'tdoc:' if any(k.startswith('tdoc:') for k in row) else ''
        row.pop('hasEvidence',None);row.pop('tdoc:hasEvidence',None)
        if fragments:row[prefix+'hasEvidence']=list(fragments.values())
        for field, value in attrs.items():
            row.pop(field, None); row.pop('tdoc:' + field, None)
            row[prefix + field] = value
        if status != 'source_verified':
            row.pop('verifiedImpactScope', None)
            row.pop('tdoc:verifiedImpactScope', None)
    return rows


def evidence_instance(root, wg, instance):
    """Represent candidate targets explicitly in generated RDF, preserving identity."""
    # A clause locator is metadata until it identifies a particular released
    # Section. JSON-LD @type:@id must never expand a bare "F"/"7.3.2" into an IRI.
    for field in ('impactsSection', 'candidateImpactsSection'):
        for prefix in ('', 'tdoc:'):
            key = prefix + field
            value = _value(instance, field) if key in instance else ''
            if value and '-Rel-' not in value:
                affected = prefix + 'affectedSection'
                if _value(instance, 'affectedSection') not in ('', value):
                    raise ImpactEvidenceError('Raw TR clause locators disagree')
                instance[affected] = value
                instance.pop(key)
    assess_impacts(root, wg, [instance])
    verified = (_value(instance, 'evidenceStatus') == 'source_verified'
                and _value(instance, 'impactType') in CAUSAL_TYPES)
    for name in ('impactsSpec', 'impactsSection'):
        for prefix in ('', 'tdoc:'):
            old, candidate = prefix + name, prefix + 'candidate' + name[0].upper() + name[1:]
            if verified and candidate in instance:
                instance[old] = instance.pop(candidate)
            elif not verified and old in instance:
                instance[candidate] = instance.pop(old)
    return instance


def impact_records(rows):
    return [r for r in rows if _value(r, 'impactType')]


def load_assessed_impact_nodes(session, root, wg, rows):
    """Write assertion metadata and remove stale causal roles in one transaction.

    Ordinary bootstrap does not require every candidate to have been adjudicated.
    This function materializes the same reviewed/pending distinction as JSON-LD.
    """
    impacts = impact_records(rows)
    assess_impacts(root, wg, impacts)
    params = []
    for row in impacts:
        props = {name: _value(row, name) for name in ('trImpactId', 'impactType', 'impactDescription', 'affectedSection', *EVIDENCE_FIELDS)}
        props['verifiedImpactScope'] = _value(row, 'verifiedImpactScope') or None
        props['affectedSection'] = claim_of(row)['impactsSection']
        if not props['trImpactId']:
            raise ImpactEvidenceError('TRImpact assertion identity is required')
        params.append(props)
    def write(tx):
        result = tx.run('''UNWIND $rows AS row
            MERGE (imp:TRImpact {trImpactId: row.trImpactId})
            SET imp += row
            WITH imp
            OPTIONAL MATCH (imp)-[r]-(target)
            WHERE (imp.evidenceStatus <> 'source_verified'
                   OR NOT imp.impactType IN ['NewTS','NewSection','ExtendSection'])
              AND type(r) IN ['IMPACTS_SPEC','SPEC_IMPACTED_BY','IMPACTS_SECTION','SECTION_IMPACTED_BY',
                              'impactsSpec','specImpactedBy','impactsSection','sectionImpactedBy']
            DELETE r
            RETURN count(DISTINCT imp) AS count''', rows=params)
        count=result.single()['count'] if params else 0
        for row in impacts:
            fragments=row.get('hasEvidence',row.get('tdoc:hasEvidence',[]))
            tx.run('''MATCH (imp:TRImpact {trImpactId:$iid}) OPTIONAL MATCH (imp)-[r:HAS_EVIDENCE]->()
                DELETE r''',iid=_value(row,'trImpactId')).consume()
            for fragment in fragments:
                props={k:v for k,v in fragment.items() if not k.startswith('@')}
                tx.run('''MATCH (imp:TRImpact {trImpactId:$iid})
                    MERGE (e:EvidenceFragment {id:$id}) SET e += $props
                    MERGE (imp)-[:HAS_EVIDENCE]->(e)''',iid=_value(row,'trImpactId'),id=fragment['@id'],props=props).consume()
        return count
    return session.execute_write(write) if hasattr(session, 'execute_write') else write(session)


def study_assertion_instances(root,wg):
    """Qualified noncausal source findings, independently assessed from impacts."""
    root=Path(root);path=root/f'ontology/input/tsg/RAN/formal/TR/{wg}/tr_impact_evidence.json'
    manifest=json.loads(path.read_text());result={}
    for entry in manifest['claims']:
        claim=entry['claim']
        for assertion in entry.get('supportedStudyAssertions',[]):
            target=assertion.get('targetSpecNumber',claim['impactsSpec'])
            if not re.fullmatch(r'\d{2}\.\d{3}(?:-\d+)*',target):
                raise ImpactEvidenceError(f'Noncausal source assertion requires an exact specification number: {target}')
            predicate=assertion['predicate']
            if predicate not in ('discussesSpec','recommendsChangeToSpec'):
                raise ImpactEvidenceError(f'Unsupported noncausal source predicate: {predicate}')
            evidence=assertion['evidence'];_receipt(root,evidence)
            # A target number in the actual reviewed quote is mandatory even for a study relation.
            if not re.search(SPEC_NUMBER_LEFT + re.escape(target) + SPEC_NUMBER_RIGHT, evidence['quote']):
                raise ImpactEvidenceError(f'Noncausal source quote lacks exact target number: {claim}')
            token=hashlib.sha256(json.dumps([wg,claim['trNumber'],target,predicate,evidence],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            iid='tr-source-'+token
            result[iid]={'@id':NAMESPACE+'assertion/'+iid,'@type':'EvidenceAssertion',
                'assertionId':iid,'evidenceStatus':'source_verified','assessmentMethod':assertion['description'],
                'assertionSubject':{'@id':NAMESPACE+'tr/'+claim['trNumber']},
                'assertionObject':{'@id':NAMESPACE+'spec/'+target.replace('.','_')},
                'assertionPredicateIRI':NAMESPACE+predicate,'hasEvidence':[fragment_of(evidence)]}
    return list(result.values())


def write_study_assertions_document(root,wg, *, output_path=None):
    """Emit the same supplement whose source path, SHA-256 and quote are verified, optionally into caller staging."""
    root=Path(root)
    import sys
    sys.path.insert(0,str(root/'scripts/common'))
    from ontology.jsonld_context import canonical_document
    path=(Path(output_path) if output_path is not None else
          root/f'ontology/output/tsg/RAN/formal/instances/phase-5/{wg}/tr_source_assertions.jsonld')
    path.parent.mkdir(parents=True,exist_ok=True)
    graph=study_assertion_instances(root,wg)
    # Include the asserted, noncausal triples as well as the source verification records for each assertion.
    for assertion in list(graph):
        predicate=assertion['assertionPredicateIRI'].removeprefix(NAMESPACE)
        graph.append({'@id':assertion['assertionSubject']['@id'],'@type':'TechnicalReport',
                      predicate:assertion['assertionObject']})
    write_text_atomic(path, json.dumps(canonical_document({'@graph':graph},wg=wg),ensure_ascii=False,indent=2)+'\n')
    return path


def load_study_assertions(session,root,wg):
    assertions=study_assertion_instances(root,wg)
    for assertion in assertions:
        tr=assertion['assertionSubject']['@id'].rsplit('/',1)[-1]
        spec=assertion['assertionObject']['@id'].rsplit('/',1)[-1].replace('_','.')
        predicate=assertion['assertionPredicateIRI'].removeprefix(NAMESPACE)
        rel={'discussesSpec':'DISCUSSES_SPEC','recommendsChangeToSpec':'RECOMMENDS_CHANGE_TO_SPEC'}[predicate]
        found=session.run('''MATCH (tr:TechnicalReport {trNumber:$tr}), (s:Spec {specNumber:$spec})
            WHERE s.specRelease IS NULL
            WITH collect(DISTINCT tr) AS reports, collect(DISTINCT s) AS specs
            WHERE size(reports)=1 AND size(specs)=1
            WITH head(reports) AS tr, head(specs) AS s
            MERGE (a:EvidenceAssertion {assertionId:$iid})
            SET a.evidenceStatus='source_verified',a.assessmentMethod=$method,a.assertionPredicateIRI=$predicate
            MERGE (a)-[:ASSERTION_SUBJECT]->(tr) MERGE (a)-[:ASSERTION_OBJECT]->(s)
            MERGE (tr)-[r:'''+rel+''']->(s) SET r.evidenceStatus='source_verified',r.assertionId=$iid
            RETURN count(a) AS count''',tr=tr,spec=spec,iid=assertion['assertionId'],
            method=assertion['assessmentMethod'],predicate=assertion['assertionPredicateIRI']).single()['count']
        if found!=1:raise ImpactEvidenceError(f'Noncausal assertion target identity missing/ambiguous: {tr}, {spec}')
        for fragment in assertion['hasEvidence']:
            props={k:v for k,v in fragment.items() if not k.startswith('@')}
            session.run('''MATCH (a:EvidenceAssertion {assertionId:$iid})
                MERGE (e:EvidenceFragment {id:$id}) SET e += $props
                MERGE (a)-[:HAS_EVIDENCE]->(e)''',iid=assertion['assertionId'],id=fragment['@id'],props=props).consume()
    return len(assertions)


def _target_value(row, name):
    return _value(row, name) or _value(row, 'candidate' + name[0].upper() + name[1:])


def link_assessed_impact_targets(session, root, wg, rows, target='spec'):
    """Only verified assertions receive causal target edges; all others receive candidates."""
    impacts = impact_records(rows); assess_impacts(root, wg, impacts)
    count = 0
    for row in impacts:
        verified = (_value(row, 'evidenceStatus') == 'source_verified'
                    and _value(row, 'impactType') in CAUSAL_TYPES)
        iid = _value(row, 'trImpactId')
        if target == 'spec':
            value = _target_value(row, 'impactsSpec')
            if not value:
                continue
            number = value.rsplit('/', 1)[-1].split(':')[-1].replace('_', '.')
            rel = 'IMPACTS_SPEC' if verified else 'CANDIDATE_IMPACTS_SPEC'
            # Candidate and verified targets both use the Spec with this number and no specRelease.
            query = '''OPTIONAL MATCH (h:Spec {specNumber:$number}) WHERE h.specRelease IS NULL
                WITH collect(h) AS hubs
                CALL {
                  WITH hubs WITH hubs WHERE size(hubs)=0
                  MERGE (s:Spec {id:$specId}) SET s.specNumber=$number RETURN s
                  UNION
                  WITH hubs WITH hubs WHERE size(hubs)=1 UNWIND hubs AS s RETURN s
                }
                WITH s MATCH (imp:TRImpact {trImpactId:$iid})
                MERGE (imp)-[r:''' + rel + ''']->(s)
                SET r.evidenceStatus=$status
                ''' + ('MERGE (s)-[:SPEC_IMPACTED_BY]->(imp)' if verified else '') + '''
                RETURN count(DISTINCT imp) AS count'''
            written=session.run(query,number=number,specId=f'tdoc:spec/{number.replace(".","_")}',iid=iid,status='source_verified' if verified else _value(row,'evidenceStatus')).single()['count']
            if written!=1:
                raise ImpactEvidenceError(f'{wg}: target Spec without specRelease or assertion identity is not unique: {number}, {iid}')
            count += written
        else:
            value = _target_value(row, 'impactsSection')
            if not value:
                continue
            sid = value.rsplit('/', 1)[-1].split(':')[-1]
            # Never invent a Section from a raw clause number or choose an arbitrary release.
            if '-Rel-' not in sid:
                continue
            rel = 'IMPACTS_SECTION' if verified else 'CANDIDATE_IMPACTS_SECTION'
            query = '''MATCH (imp:TRImpact {trImpactId:$iid}), (s:Section {sectionId:$sid})
                MERGE (imp)-[r:''' + rel + ''']->(s) SET r.evidenceStatus=$status
                ''' + ('MERGE (s)-[:SECTION_IMPACTED_BY]->(imp)' if verified else '') + '''
                RETURN count(DISTINCT imp) AS count'''
            count += session.run(query,iid=iid,sid=sid,status='source_verified' if verified else _value(row,'evidenceStatus')).single()['count']
    return count
