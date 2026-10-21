#!/usr/bin/env python3
"""Joint complete-record scoring for a scalar answer with an unordered sample."""
import sys
if sys.flags.optimize != 0:
    raise SystemExit('optimized execution is unsupported')
import original_scorer
import scorer as typed

KIND='one_record_with_unordered_sample'

def sample_contract(limit):
    return {'required_fields':[{'name':'sampleCR','type':'string','nullable':False}],
            'collection':{'kind':'top_k_boundary_ties','value':limit,
                          'tie_policy':'any_subset_at_boundary','within_tie_order':'any',
                          'require_rank_order':False},
            'cardinality_policy':{'mode':'top_k','value':limit,
                                  'tie_policy':'any_subset_at_boundary'},
            'validation_status':'validated'}

def score(contract,gold_rows,predicted_rows,*,sample_pool,diagnostic=False):
    """Count one match only when the complete scalar-and-sample record is valid."""
    if contract['collection']!={'kind':KIND,'value':10,
            'tie_policy':'any_distinct_members_of_complete_pool',
            'within_tie_order':'any','require_rank_order':False}:
        raise ValueError('unsupported joint sample contract')
    if contract['cardinality_policy']!={'mode':'exact','value':1}:
        raise ValueError('joint answer must retain one logical record')
    if type(contract['cardinality_policy']['value']) is not int:
        raise ValueError('outer cardinality must be an integer')
    if not diagnostic and contract.get('validation_status')!='validated':
        raise ValueError('unvalidated task cannot supply benchmark scores')
    fields=contract['required_fields']
    if [f['name'] for f in fields]!=['specNumber','crCount','sampleCRs']:
        raise ValueError('original scalar/list roles changed')
    expected=[{'type':'string'},{'type':'integer'},
              {'type':'array','items':{'type':'string'}}]
    if any(typed.get_kernel().field_schema(f)!=s for f,s in zip(fields,expected)):
        raise ValueError('original scalar/list types changed')
    if fields[2].get('nested_array_semantics')!={'$':'multiset'}:
        raise ValueError('sample multiplicity must be retained before eligibility')
    if type(gold_rows) is not list or len(gold_rows)!=1:
        raise ValueError('one native scalar/sample gold record required')
    typed.project(gold_rows,fields,gold=True)
    if type(sample_pool) is not list or not sample_pool:
        raise ValueError('complete eligible sample population absent')
    pool=[{'sampleCR':v} for v in sample_pool]
    sc=sample_contract(contract['collection']['value'])
    tokens,_=typed.project(pool,sc['required_fields'],gold=True)
    if len(set(tokens))!=len(tokens):
        raise ValueError('fixed native sample pool must have unique identities')
    gold=gold_rows[0]
    if gold['crCount']!=len(sample_pool):
        raise ValueError('current full native collect and count are inconsistent')
    def component(values):
        rows=[{'sampleCR':v} for v in values]
        return original_scorer.score(sc,pool,rows,diagnostic=True,order_groups=[pool])
    if not component(gold['sampleCRs'])['exact']:
        raise ValueError('saved native sample is not an admissible original sample')
    if type(predicted_rows) is not list:
        raise ValueError('records must be a list')
    _,errors=typed.project(predicted_rows,fields)
    cardinality=len(predicted_rows)==1
    scalars=False;sample=None
    if cardinality and not errors:
        row=predicted_rows[0]
        scalars=all(typed.record_token(row,[f])==typed.record_token(gold,[f]) for f in fields[:2])
        sample=component(row['sampleCRs'])
    exact=bool(cardinality and not errors and scalars and sample and sample['exact'])
    value=1.0 if exact else 0.0
    return {'diagnostic_only':diagnostic,'exact':exact,'precision':value,'recall':value,'f1':value,
            'matched_records':int(exact),'gold_records':1,'predicted_records':len(predicted_rows),
            'cardinality_valid':cardinality,'order_valid':True,'type_errors':errors,
            'joint_complete_record':True,'scalar_roles_valid':scalars,
            'sample_component':sample,'eligible_sample_population_records':len(sample_pool),
            'metric_unit':'one complete target/count/sample record; sample components receive no separate answer credit'}
