#!/usr/bin/env python3
"""Check a separate expansion; never change the frozen evaluation cohort."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import continue_original as continuation

BASE = Path(__file__).resolve().parent
EXTRA = BASE / 'further_expansion'
RUN = EXTRA / 'native_capture'
PRIMARY = ('unresolved_repairs_RAN1_RAN2.jsonl', 'primary_RAN3_RAN4_RAN5.jsonl',
           'primary_RAN3_additional.jsonl', 'additional_proposals_RAN1_RAN2.jsonl',
           'primary_RAN5_other_specs.jsonl')
SECONDARY = ('secondary_RAN1_RAN2.jsonl', 'secondary_RAN3_RAN4_RAN5.jsonl',
             'secondary_RAN3_additional.jsonl','secondary_additional_RAN1_RAN2.jsonl',
             'secondary_RAN5_other_specs.jsonl')
FROZEN = BASE / 'final_staging/release_package/cqs/original_core_repair'
MAXIMUM_REQUIRED = {'RAN5_P3_CQ2-4', 'RAN3_P3_CQ2-3'}
MAXIMUM_SOURCE_WITNESS = EXTRA / 'max_frequency_source_witness.json'
MAXIMUM_SOURCE_WITNESS_SHA = 'de154879dbc9f2c9f50ae5ad5153e22ec988b764963a9ce603a1cea6c61b94d9'
MAXIMUM_DERIVATION = EXTRA / 'audit_maximum_source.py'
MAXIMUM_DERIVATION_SHA = 'bb15122f9480a822e3a91e654bfb56095bd16c4131a3952fadf4f118ffc86cb7'
SOURCE_PARSER = continuation.native.PUBLIC.parents[0] / 'pipeline/load_released_kg.py'


def derive_complete_maximum(pool, answer_fields):
    """Derive every maximum tie from the independently captured complete pool."""
    names = set(answer_fields)
    if not pool or 'referenceCount' in names:
        raise ValueError('Maximum frequency pool empty or requested identity ambiguous')
    identities = []
    for row in pool:
        if set(row) != names | {'referenceCount'}:
            raise ValueError('Maximum source-pool fields differ from requested identities')
        if (type(row['referenceCount']) is not int or row['referenceCount'] < 0
                or any(type(row[name]) is not str or not row[name] for name in names)):
            raise ValueError('Maximum source-pool identity/count type invalid')
        identities.append(continuation.digest({name:row[name] for name in answer_fields}))
    if len(identities) != len(set(identities)):
        raise ValueError('Maximum source-pool requested identities are duplicated')
    maximum = max(row['referenceCount'] for row in pool)
    records = [{name:row[name] for name in answer_fields}
               for row in pool if row['referenceCount'] == maximum]
    return maximum, records


def maximum_witness(task, records, receipt):
    if task['id'] not in MAXIMUM_REQUIRED:
        return None
    if continuation.sha(MAXIMUM_SOURCE_WITNESS) != MAXIMUM_SOURCE_WITNESS_SHA:
        raise ValueError('Independent complete maximum source-witness bytes changed')
    if continuation.sha(MAXIMUM_DERIVATION) != MAXIMUM_DERIVATION_SHA:
        raise ValueError('Independent maximum derivation code bytes changed')
    document = json.loads(MAXIMUM_SOURCE_WITNESS.read_text())
    if continuation.sha(SOURCE_PARSER) != document['parser_sha256']:
        raise ValueError('Maximum source parser bytes changed')
    matches = [row for row in document['results'] if row['id'] == task['id']]
    if len(matches) != 1:
        raise ValueError('Complete maximum frequency pool missing or duplicated')
    source = matches[0]
    graph = continuation.native.ROOT / source['graph_source_path']
    if (continuation.sha(graph) != source['graph_source_sha256']
            or receipt['provenance']['graph_source_sha256'] != source['graph_source_sha256']):
        raise ValueError('Maximum source pool and actual native receipt graph differ')
    if task['collection']['kind'] != 'set' or task['cardinality_policy']['mode'] != 'all':
        raise ValueError('Maximum source witness requires every maximum tie as a set')
    if (not task['required_fields']
            or any(field['type'] != 'string' or field['nullable'] is not False
                   for field in task['required_fields'])):
        raise ValueError('Maximum witness requested identity fields differ')
    pool_path = None
    if 'pool_path' in source:
        pool_path = continuation.native.ROOT / source['pool_path']
        if continuation.sha(pool_path) != source['pool_sha256']:
            raise ValueError('Complete maximum source-pool rows changed')
        pool = continuation.read(pool_path)
        if (len(pool) != source['pool_count']
                or sum(row['referenceCount'] == 0 for row in pool) != source['zero_count']):
            raise ValueError('Complete maximum source-pool cardinality/zero population differs')
    else:
        pool = source['pool']
    answer_fields = [field['name'] for field in task['required_fields']]
    maximum, expected = derive_complete_maximum(pool, answer_fields)
    if (maximum != source['maximum']
            or sorted(map(continuation.digest, expected)) != sorted(map(continuation.digest, source['maximal_requested_records']))):
        raise ValueError('Maximum witness summary differs from complete pool derivation')
    if sorted(map(continuation.digest, records)) != sorted(map(continuation.digest, expected)):
        raise ValueError('Actual native gold omits or changes an independently derived maximum tie')
    witness = {
        'kind':'full_frozen_source_frequency_pool',
        'scope':'All eligible frequency-pool records independently derived from the exact frozen graph; actual native requested gold equals all argmax ties. This does not assert raw archive truth or human/expert validation.',
        'id':task['id'],'repair_sha256':task['repair_sha256'],
        'original_question_sha256':task['original_question_sha256'],
        'query_sha256':task['reference_query_sha256'],
        'source_witness_path':str(MAXIMUM_SOURCE_WITNESS),
        'source_witness_sha256':MAXIMUM_SOURCE_WITNESS_SHA,
        'derivation_script_path':str(MAXIMUM_DERIVATION),
        'derivation_script_sha256':MAXIMUM_DERIVATION_SHA,
        'parser_path':str(SOURCE_PARSER),'parser_sha256':document['parser_sha256'],
        'graph_source_path':source['graph_source_path'],'graph_source_sha256':source['graph_source_sha256'],
        'source_pool_n':len(pool),'source_zero_n':sum(row['referenceCount'] == 0 for row in pool),
        'maximum_frequency':maximum,'maximum_tie_n':len(expected),
        'expected_maximum_records_sha256':continuation.digest(sorted(expected,key=continuation.digest)),
        'actual_native_projected_records_sha256':continuation.digest(records),
        'native_receipt_sha256':receipt['receipt_sha256'],
        'native_rows_sha256':receipt['rows_sha256'],
        'native_argmax_matches_complete_source_pool':True,
        'expert_validation_n':0,'human_author_review_completed':False}
    if pool_path:
        witness.update(source_pool_path=str(pool_path),source_pool_sha256=source['pool_sha256'])
    return witness


def metadata_errata(task):
    # Raw primary is preserved verbatim. An erratum is metadata only, outside
    # the nine-key meaning definition and both independent semantic judgments.
    if task['id'] != 'RAN1_P3_CQ020':
        return []
    context = task['primary_review'].get('source_context', {})
    path = context.get('actual_cross_spec_loader_path')
    if not path or 'RAN2' not in path:
        return []
    return [{'field':'primary_review.source_context.actual_cross_spec_loader_path',
             'recorded_value':path,'corrected_applicability':'not applicable to this RAN1 submitted-CR lookup',
             'reason':'The RAN2 cross-spec loader path was copied into source metadata. This task uses RAN1 SUBMITTED_BY/MODIFIES source relationships, not that RAN2 loader.',
             'raw_primary_preserved':True,'definition_sha256_unchanged':True}]


def inputs():
    # Later explicitly listed proposals supersede earlier candidates only.
    # All previous definitions and reviews remain in their unchanged files.
    proposals={}
    for n in PRIMARY:
        if (EXTRA/n).exists():
            proposals.update(continuation.unique(continuation.read(EXTRA/n)))
    review_versions={}
    for n in SECONDARY:
        if (EXTRA/n).exists():
            for r in continuation.read(EXTRA/n):
                key=(r['id'],r.get('repair_sha256'))
                if key in review_versions:raise ValueError('Duplicate review for exact definition')
                review_versions[key]=r
    reviews={id:review_versions.get((id,t['repair_sha256'])) for id,t in proposals.items()}
    originals = continuation.unique(continuation.read(
        continuation.native.PUBLIC / 'spectra_cq_v2.0/benchmark.jsonl'))
    prior = continuation.unique(continuation.read(FROZEN/'tasks.jsonl'))
    criteria = json.loads((BASE/'criteria.json').read_text())
    selected = {}
    for id,t in proposals.items():
        o=originals[id]
        definition={k:t[k] for k in continuation.DEFINITION_KEYS}
        if (id in prior or t['question_en']!=o['question_en']
            or t['original_query']!=o['cypher']
            or t['original_question_preserved'] is not True
            or t['repair_sha256']!=continuation.digest(definition)
            or t['criteria_sha256']!=continuation.sha(BASE/'criteria.json')
            or t['reference_query_sha256']!=hashlib.sha256(t['reference_query'].encode()).hexdigest()
            or t['original_query_sha256']!=hashlib.sha256(o['cypher'].encode()).hexdigest()
            or t['original_question_sha256']!=hashlib.sha256(o['question_en'].encode()).hexdigest()
            or t['repair_class']!=('scorer_only' if t['reference_query']==o['cypher'] else 'query_and_scorer')):
            raise ValueError('Original question or pinned definition changed: '+id)
        for review in [t['primary_review'],reviews.get(id)]:
            if not review or review.get('status')!='pass':break
            continuation.review_schema.check_pass(review,t['question_en'],criteria['semantic_units'],
                criteria_sha=t['criteria_sha256'],identity_key='repair_sha256',identity_sha=t['repair_sha256'])
        else:
            continuation.native.normalize_fields(t['required_fields'])
            selected[id]=t
    return proposals,reviews,selected


def capture(wg):
    proposals,reviews,selected=inputs()
    continuation.RUN=RUN
    continuation.candidates=lambda:selected
    continuation.capture(wg)


def admit():
    continuation.native.verify_sources()
    proposals,reviews,selected=inputs()
    continuation.RUN=RUN
    tasks=[];gold=[];checks=[];dispositions=[]
    for id,t in sorted(proposals.items()):
        second=reviews.get(id)
        if id not in selected:
            dispositions.append({'id':id,'status':'pending','reason':second.get('reason','Separate semantic review did not pass') if second else 'Separate semantic review pending'})
            continue
        try:
            rows,receipt=continuation.references(t)
            if rows is None:raise ValueError('Complete exact-query capture unavailable')
            records=continuation.native.answer_projection(rows,t['required_fields'],receipt['columns'])
            witness=maximum_witness(t,records,receipt)
            groups=continuation.original_scorer.make_order_groups(t,rows,records) if t['collection']['kind'] in {'native_ordered_ties','top_k_boundary_ties'} else None
            tests=continuation.checks(t,records,groups)
            if not all(x['pass'] for x in tests):raise ValueError('Actual scorer controls failed')
            tasks.append(dict(t,secondary_review=second,validation_status='validated',
                reference_evidence=receipt,native_rows=len(rows),projected_records_sha256=continuation.digest(records),
                completeness_witness=witness,metadata_errata=metadata_errata(t),
                human_author_review_completed=False,expert_validation_n=0,
                model_calls=0,model_call_scope='Benchmark predictions only; AI reviews separately recorded.'))
            gold.append({'id':id,'repair_sha256':t['repair_sha256'],'records':records,'order_groups':groups})
            checks.append({'id':id,'repair_sha256':t['repair_sha256'],'checks':tests,'pass':True})
            dispositions.append({'id':id,'status':'pass','repair_sha256':t['repair_sha256']})
        except (ValueError,TypeError,KeyError) as e:
            dispositions.append({'id':id,'status':'pending','reason':str(e)})
    RUN.mkdir(exist_ok=True,parents=True)
    for n,values in [('tasks.jsonl',tasks),('reference_gold.jsonl',gold),('scorer_checks.jsonl',checks),('dispositions.jsonl',dispositions)]:
        continuation.write(RUN/n,values)
    report={'candidate_n':len(proposals),'admitted_additional_n':len(tasks),'native_rows':sum(t['native_rows'] for t in tasks),
            'scorer_control_n':sum(len(t['checks']) for t in checks),'dispositions':dict(Counter(t['status'] for t in dispositions)),
            'prior_frozen_cohort_n':350,'union_n':350+len(tasks),'evaluation_frozen_cohort_changed':False,
            'expert_validation_n':0,'human_author_review_completed':False,'benchmark_model_calls':0,
            'published':False,'frozen_prior_manifest_sha256':continuation.sha(FROZEN/'manifest.json')}
    report['complete_maximum_source_pool_gates']={t['id']:t['completeness_witness']['native_argmax_matches_complete_source_pool']
        for t in tasks if t['id'] in MAXIMUM_REQUIRED}
    report['metadata_errata_n']=sum(len(t['metadata_errata']) for t in tasks)
    (RUN/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('action',choices=['capture','admit']);a.add_argument('--wg')
    args=a.parse_args()
    if args.action=='capture':
        if args.wg not in {'RAN1','RAN2','RAN3','RAN4','RAN5'}:a.error('capture requires a supported WG')
        capture(args.wg)
    else:admit()
