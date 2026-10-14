"""Diagnose saved recovered SQL artifacts without opening/executing SQLite."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path):
    return {'path':str(Path(path).relative_to(ROOT)), 'sha256':sha(path)}


def load(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


TOKEN=re.compile(r"--[^\n]*|/\*.*?\*/|'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\"|`(?:[^`]|``)*`|\[[^\]]*\]|[A-Za-z_][A-Za-z0-9_]*|[(),.]",re.S)


def tables(query):
    """Explicit FROM/JOIN names only; no strings/comments or known CTE aliases."""
    tokens=[m.group() for m in TOKEN.finditer(query)
            if not m.group().startswith(('--','/*'))]
    unquote=lambda t:t[1:-1].replace(t[0]*2,t[0]) if t[:1] in {'"',"'",'`','['} else t
    ctes=set()
    if tokens and tokens[0].upper()=='WITH':
        depth=0
        for i,t in enumerate(tokens[:-2]):
            if t=='(':depth+=1
            if t==')':depth-=1
            if depth==0 and tokens[i+1].upper()=='AS' and tokens[i+2]=='(':
                ctes.add(unquote(t).casefold())
    found=[]
    for i,t in enumerate(tokens[:-1]):
        if t.upper() not in {'FROM','JOIN'}:continue
        n=tokens[i+1]
        if n in {'(',')',',','.'}:continue
        if i+3<len(tokens) and tokens[i+2]=='.':n=tokens[i+3]
        name=unquote(n)
        if name.casefold() not in ctes:
            found.append({'name':name,'quoted':n[:1] in {'"',"'",'`','['}})
    return found


old_path=BASE/'sql_generation_schema_diagnostic.json'
old=load(old_path)
old_items={row['id']:row for row in old['items']}
phases=[]
all_items=[]
schemas={}
for label,dirname,n in [('recovered350','original-core-transport-supplement',350),
                       ('recovered21','additional-originals-transport-supplement',21)]:
    run=BASE/'runs'/dirname
    protocol=load(run/'protocol.json')
    generation=load(run/'generation_complete.json')
    completion=load(run/'execution_complete.json')
    statuses=rows(run/'text2sql/statuses.jsonl')
    assert len(statuses)==n and len({r['id'] for r in statuses})==n
    assert set(r['id'] for r in statuses)==set(protocol['cohort_ids'])
    assert generation['completed_method_items']==4*n
    assert completion['completed_method_items']==2*n
    assert generation['original_artifacts_unchanged'] is True
    assert completion['original_execution_artifacts_unchanged'] is True
    phase_items=[]
    for wg in [f'RAN{x}' for x in range(1,6)]:
        schema_path=run/'schemas'/f'{wg}_sql.json'
        schema=load(schema_path)
        manifest_path=BASE/'relational'/f'{wg}.manifest.json'
        manifest=load(manifest_path)
        assert sha(schema_path)==old['workgroups'][wg]['schema_sha256']
        assert manifest['db_sha256']==old['workgroups'][wg]['sqlite_sha256']
        assert schema==manifest['schema']
        schemas[wg]={'schema':schema,'schema_file':pin(schema_path),
                     'sqlite_manifest':pin(manifest_path),'sqlite_sha256':manifest['db_sha256'],
                     'physical_table_inventory_evidence':'Previously saved SQLite metadata diagnostic with the same database and schema pins; no new SQLite connection or metadata query.',
                     'relationship_types_n':len(schema['relationship_tables'])}
    for status in statuses:
        execution_path=run/status['artifact']
        executed=load(execution_path)
        generation_path=run/'arm_outputs/text2sql'/f"{status['id']}.json"
        generated=load(generation_path)
        query=executed.get('generated_query')
        assert executed['id']==status['id'] and executed['status']==status['status']
        assert executed['repair_sha256']==status['repair_sha256']==generated['repair_sha256']
        if isinstance(query,str):assert hashlib.sha256(query.encode()).hexdigest()==executed['query_sha256']
        schema=schemas[executed['wg']]['schema']
        declared={name.casefold():name for name in schema['relationship_tables']}
        names=tables(query or '')
        mismatch=sorted({declared[t['name'].casefold()] for t in names if t['name'].casefold() in declared})
        ex=executed.get('execution') or {}
        actual_messages={key:ex[key] for key in ['error','error_message','message','exception'] if key in ex}
        saved=old_items.get(status['id'])
        matched=bool(saved and query and saved.get('generated_query_sha256')==executed['query_sha256'])
        prior_compile={key:saved[key] for key in ['compile','error_class','compile_error','error_category','missing_table'] if key in saved} if matched else None
        cat=executed['status']
        if cat=='ERROR':
            if prior_compile and prior_compile.get('compile')=='ERROR':cat='saved_same_query_compile_'+prior_compile['error_category']
            elif ex.get('error_class') in {'ValueError','TypeError','JSONDecodeError'}:cat='type_or_decode_exception_class_message_unretained'
            else:cat='execution_error_specific_cause_unretained'
        elif cat in {'TIMEOUT','ROW_CAP','BYTE_CAP','REJECTED','SOURCE_MISMATCH','DUPLICATE_COLUMNS'}:
            cat='executor_'+cat.lower()
        item={'id':status['id'],'phase':label,'wg':executed['wg'],'repair_sha256':status['repair_sha256'],
              'generation_status':generated['status'],'saved_execution_status':executed['status'],
              'generated_SQL':query,'generated_query_sha256':executed.get('query_sha256'),
              'actual_execution_error_class':ex.get('error_class'),
              'actual_execution_error_messages':actual_messages,
              'actual_execution_specific_error_message_retained':bool(actual_messages),
              'diagnostic_category':cat,
              'saved_same_query_compile_diagnostic':prior_compile,
              'compile_diagnostic_scope':'A prior recorded compile-only observation for this exact query and schema; not a new query execution or retained execution-error message.' if prior_compile else None,
              'static_schema_evidence':{'explicit_FROM_JOIN_names':names,
                   'unprefixed_declared_relationship_table_references':mismatch,
                   'physical_expected_names':['rel_'+name for name in mismatch],
                   'unquoted_REFERENCES_table_token':any(t['name'].upper()=='REFERENCES' and not t['quoted'] for t in names),
                   'scope':'Lexical mismatch evidence only; not an inferred first exception or proof that prefix repair makes the answer correct. Known CTE aliases and string/comment text are excluded; this is not a complete SQL parser.'},
              'evidence':[pin(generation_path),pin(execution_path),schemas[executed['wg']]['schema_file'],schemas[executed['wg']]['sqlite_manifest']]}
        phase_items.append(item)
    phases.append({'phase':label,'cohort_n':n,'run':str(run.relative_to(ROOT)),
                   'pins':[pin(run/name) for name in ['protocol.json','generation_complete.json','execution_complete.json','text2sql/statuses.jsonl','analysis.json']],
                   'generation_status_counts':dict(Counter(i['generation_status'] for i in phase_items)),
                   'execution_status_counts':dict(Counter(i['saved_execution_status'] for i in phase_items)),
                   'diagnostic_category_counts':dict(Counter(i['diagnostic_category'] for i in phase_items)),
                   'execution_ERROR_with_unprefixed_declared_relation_token_n':sum(i['saved_execution_status']=='ERROR' and bool(i['static_schema_evidence']['unprefixed_declared_relationship_table_references']) for i in phase_items),
                   'execution_ERROR_specific_message_unretained_n':sum(i['saved_execution_status']=='ERROR' and not i['actual_execution_specific_error_message_retained'] for i in phase_items),
                   'items':phase_items})
    all_items+=phase_items
assert len(all_items)==371 and len({i['id'] for i in all_items})==371
result={'kind':'Read-only saved recovered371 SQL diagnostic; two disjoint phases, no compilation/execution',
        'completed_utc':datetime.now(timezone.utc).isoformat(),'status':'COMPLETE_SAVED_ARTIFACT_DIAGNOSTIC',
        'model_calls':0,'SQLite_connections':0,'SQL_query_executions':0,'new_EXPLAIN_compilations':0,
        'query_repairs':0,'performance_rescoring':0,
        'pins':[pin(old_path),pin(BASE/'structured_adapter.py'),pin(Path(__file__))],
        'cohort_n':371,'union_execution_status_counts':dict(Counter(i['saved_execution_status'] for i in all_items)),
        'union_diagnostic_category_counts':dict(Counter(i['diagnostic_category'] for i in all_items)),
        'union_static_unprefixed_declared_relationship_references_n':sum(bool(i['static_schema_evidence']['unprefixed_declared_relationship_table_references']) for i in all_items),
        'workgroups':{k:{x:v for x,v in s.items() if x!='schema'} for k,s in schemas.items()},'phases':phases,
        'interpretation':{'frozen_schema_limitation':'System instructions say rel_TYPE, while schema relationship_tables keys display TYPE. This is a disclosed schema-presentation issue, not evidence of causal SQL inferiority or an executor correctness defect.',
             'error_retention_limitation':'The frozen SQL executor saves exception class only. Specific current execution messages cannot be recovered without new execution, which this diagnostic does not perform. Previously recorded exact-query compile strings are retained with explicit scope; unmatched OperationalErrors remain specific-cause unclassified.',
             'no_claim_every_failure_is_prefix':'Non-OK statuses include abstentions/generation errors. Static naming mismatches are separate from recorded compile categories, and category counts retain unknown causes.',
             'source_and_score_scope':'No aliases, query edits, new answers or changed scores.350/21 are separate frozen cohorts; recovery reuses preserved successes and replays only authorized identical infrastructure-failed payloads.'}}
target=BASE/'sql_generation_schema_diagnostic_recovered.json'
target.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps({'path':str(target.relative_to(ROOT)),'sha256':sha(target),
    'cohort_n':371,'statuses':result['union_execution_status_counts'],'categories':result['union_diagnostic_category_counts'],
    'static_relation_mismatch_items':result['union_static_unprefixed_declared_relationship_references_n']}))
