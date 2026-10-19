"""Separate-cohort adapter for an explicitly declared exact share contract.

No frozen runner is edited. install() operates on a fresh in-memory adapter
instance and is needed before prompts, answer parsing and execution assembly.
The same public representation enters A/B/C/D. The same canonicalization enters
native A, SQL B, raw retrieval C/D and requested-field scoring. No gold is read
by any candidate parser or generator. Root owns any future API/native runtime.
"""
from contextvars import ContextVar
from functools import wraps
from rational_share_records import (encoding,normalize_records,normalize_sql_records,
    parse_retrieval_answer,public_representation)

_TASK=ContextVar('exact_share_task',default=None)


def public_task(task,legacy_public_task):
    """Keep only the value-free representation descriptor through runner freeze.

    Legacy cohort public_task functions filter collection keys. A fresh runner
    must use this hook before serializing public_tasks, not just install the
    prompt/parser hooks afterwards. No local codec path, source, gold or hash is
    provided to a method.
    """
    result=legacy_public_task(task)
    spec=encoding(task)
    if spec is None:
        return result
    result=dict(result,collection=dict(result['collection']))
    result['collection']['rational_share_representation']={
        'kind':'exact_rational_share','unit':'one','field':spec['field']}
    result['required_fields']=[dict(f,value_representation={
        'kind':'exact_rational_share','unit':'one'}) if f['name']==spec['field']
        else f for f in result['required_fields']]
    return result


def add_public_format(result,task):
    value=public_representation(task)
    if value is None:
        return result
    return dict(result,value_representations=[value])


def candidate_records(task,method,records):
    return normalize_sql_records(task,records) if method in {'B','Text2SQL'} else normalize_records(task,records)


def score(task,gold,predicted,original_score,**kwargs):
    if encoding(task) is None:
        return original_score(task,gold,predicted,**kwargs)
    return original_score(task,normalize_records(task,gold,gold=True),
        normalize_records(task,predicted),**kwargs)


def install(structured,retrieval):
    """Install on fresh module instances; return immutable original callbacks.

    An isolated runner using its own execution path must additionally invoke
    candidate_records() on each successful native/SQL result before persistence.
    This is a declared integration obligation, not a claim that an old frozen
    runner already uses these hooks.
    """
    if getattr(structured,'_exact_share_installed',False):
        raise ValueError('share hooks already installed on this adapter instance')
    old_output=structured.output_format; old_public=retrieval.public_contract
    old_parse=retrieval.parse_answer; old_evaluate=retrieval.evaluate
    old_decode=structured.decode_sql_record; old_execute=structured.execute_generated
    @wraps(old_output)
    def output(task):
        result=add_public_format(old_output(task),task)
        if encoding(task):
            field=encoding(task)['field']
            for value in result['required_fields']:
                if value['name']==field:
                    value['value_representation']={'kind':'exact_rational_share','unit':'one'}
        return result
    @wraps(old_public)
    def public(task):
        return add_public_format(old_public(task),task)
    @wraps(old_parse)
    def parse(content):
        task=_TASK.get()
        return old_parse(content) if task is None else parse_retrieval_answer(task,content,old_parse)
    @wraps(old_evaluate)
    def evaluate(task,*args,**kwargs):
        token=_TASK.set(task)
        try:
            return old_evaluate(task,*args,**kwargs)
        finally:
            _TASK.reset(token)
    @wraps(old_decode)
    def decode(row,fields):
        share=[f for f in fields if f.get('value_representation',{}).get('kind')=='exact_rational_share']
        if not share:
            return old_decode(row,fields)
        if len(share)!=1:
            raise ValueError('one explicit share field expected')
        name=share[0]['name']
        result=old_decode(row,[f for f in fields if f['name']!=name])
        task={'collection':{'rational_share_representation':{'kind':'exact_rational_share','unit':'one','field':name}}}
        return normalize_sql_records(task,[result])[0]
    @wraps(old_execute)
    def execute(record,task,*args,**kwargs):
        result=old_execute(record,task,*args,**kwargs)
        if not encoding(task):
            return result
        result=dict(result)
        if result.get('execution'):
            execution=dict(result['execution'])
            execution['rows']=candidate_records(task,record['method'],execution['rows'])
            result['execution']=execution
        result['records']=candidate_records(task,record['method'],result.get('records',[]))
        return result
    structured.output_format=output; structured.decode_sql_record=decode
    structured.execute_generated=execute; structured._exact_share_installed=True
    retrieval.public_contract=public; retrieval.parse_answer=parse; retrieval.evaluate=evaluate
    return {'structured_output_format':old_output,'retrieval_public_contract':old_public,
        'retrieval_parse_answer':old_parse,'retrieval_evaluate':old_evaluate,
        'structured_decode_sql_record':old_decode,'structured_execute_generated':old_execute}
