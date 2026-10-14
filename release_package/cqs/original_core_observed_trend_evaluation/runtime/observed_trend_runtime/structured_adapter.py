#!/usr/bin/env python3
"""Gold-free Text2Cypher/Text2SQL generation and deferred read execution.

evaluate() generates one query and records it, without touching Neo4j or SQLite.
The root runner invokes execute_generated() only after freezing sources and all
queries. No reference query, gold, repair reason or review record is read here.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sqlite3
import time

ROW_CAP = 100000
BYTE_CAP = 256 * 1024 * 1024
TIMEOUT_SECONDS = 60
MAX_GENERATION_TOKENS = 4096
METHODS = {'A': 'Text2Cypher', 'B': 'Text2SQL',
           'Text2Cypher': 'Text2Cypher', 'Text2SQL': 'Text2SQL'}
FORBIDDEN_INPUT = {'gold', 'gold_rows', 'reference_query', 'original_query', 'repair_notes',
                   'repair_reason', 'primary_review', 'secondary_review', 'semantic_evidence',
                   'native_rows', 'order_groups', 'scorer_checks', 'reference_outputs'}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def reject_private(value):
    if isinstance(value, dict):
        if FORBIDDEN_INPUT.intersection(value):
            raise ValueError('private evaluation evidence in generator input')
        for child in value.values():
            reject_private(child)
    elif isinstance(value, list):
        for child in value:
            reject_private(child)


def output_format(task):
    contract = task.get('output_format', task.get('contract', task))
    fields = contract.get('required_fields')
    if not isinstance(fields, list) or not fields:
        raise ValueError('nonempty requested typed fields required')
    visible_fields = [{key: field[key] for key in
        ('name', 'type', 'nullable', 'json_schema', 'nested_array_semantics') if key in field}
        for field in fields]
    collection = contract.get('collection', {})
    visible_collection = {key: collection[key] for key in
        ('kind', 'value', 'order_keys', 'tie_policy', 'within_tie_order', 'require_rank_order') if key in collection}
    cardinality = contract.get('cardinality_policy', {})
    visible_cardinality = {key: cardinality[key] for key in ('mode', 'value', 'tie_policy') if key in cardinality}
    return {'required_fields': visible_fields, 'collection': visible_collection,
            'cardinality_policy': visible_cardinality,
            **({'identity_format': task['identity_format']} if task.get('identity_format') else {}),
            **({'ordering_format': task['ordering_format']} if task.get('ordering_format') else {}),
            'instruction': 'Return exactly the named requested fields as query aliases. Nested objects/arrays must match the declared JSON types. Do not return hidden rank columns as answer fields. Preserve requested cardinality and order; do not add an unstated output cap.'}


def graph_schema(group):
    return {'labels': group['labels'],
            'properties_by_label': {label: {**{field['name']: field['neo4j_native_types'] for field in fields},
                                             'iri':['STRING NOT NULL']}
                                    for label, fields in group['label_properties'].items()},
            'directed_relationships': [[r['from_label'], r['relationship'], r['to_label']]
                                      for r in group['relationship_triples']],
            'auxiliary_identity_codec':'iri is the exact loader-only stable entity identity, using /inst/_/{cls}/{nid}. It is not the source IRI containing RANx or a new source-authored property. Business identifier fields retain their original values.'}


def messages_for(task, method):
    reject_private(task)
    method = METHODS[method]
    question = task.get('question_en', task.get('question'))
    if not isinstance(question, str) or not question:
        raise ValueError('original question required')
    schema = task.get('graph_schema' if method == 'Text2Cypher' else 'sql_schema')
    if not isinstance(schema, dict) or not schema:
        raise ValueError('value-free method schema required')
    instruction = ('Generate exactly one read-only '+('Neo4j 5 Cypher' if method == 'Text2Cypher' else 'SQLite 3 SQL')
        +' query using only the original question, requested output format and supplied schema. '
        'No tools, files, internet, external facts, answer literals or unsupported assumptions. '
        'Return only JSON {"query": "...", "abstain": false}. If unsupported, return '
        '{"query":"","abstain":true}. Every output alias must equal a required field name. '
        'Do not mutate data, call procedures or external functions, attach databases, or add a '
        'row LIMIT not requested by the question. Use the question\'s exact identities, filters, '
        'counting units and direction. A schema property may be absent on a node. A recorded '
        'documentary relation is not independent evidence of causation or approval. Top-k queries '
        'may select any boundary-tied members while including all higher-ranked members; do not '
        'add a required tie-breaking identity order. Return no explanation. ')
    if method == 'Text2SQL':
        instruction += ('Use label tables joined through shared node_id; directed rel_TYPE tables '
            'have src_id,dst_id,edge_id. A multilabel node appears in each label table with the same '
            'identity. STRICT ANY property columns preserve strings/numbers; booleans are 0/1, '
            'arrays/objects are canonical JSON text, absent properties are NULL. node_property '
            'provides exact native_type/value_json when mixed types or null-presence matter. '
            'Use SQLite JSON functions for nested answer objects/arrays. Private tables whose '
            'names start with _ are inaccessible. Cast booleans to0/1 only when the answer type '
            'is boolean; do not cast identifiers or numeric-looking strings to numbers. ')
    else:
        instruction += 'Do not use APOC, procedure CALL, USE, LOAD CSV or mutation. Anonymous read subqueries are allowed. Lists use list membership, not scalar equality. '
    public = {'question': question, 'output_format': output_format(task), 'schema': schema}
    return [{'role': 'system', 'content': instruction},
            {'role': 'user', 'content': canonical(public)}]


def evaluate(task_public, method, caller, run_dir):
    """Generate once; deferred execution prevents races with native capture."""
    method = METHODS[method]
    task_id = task_public['id']
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', task_id):
        raise ValueError('unsafe task id')
    path = Path(run_dir)/'predictions'/method/(task_id+'.json')
    if path.exists():
        raise ValueError('existing scientific prediction; no regeneration')
    messages = messages_for(task_public, method)
    call = caller.call(task_id+'_'+method, messages, max_tokens=MAX_GENERATION_TOKENS)
    record = {'id':task_id,'repair_sha256':task_public['repair_sha256'],'method':method,
              'wg':task_public.get('wg',task_id.split('_')[0]),'records':[],
              'status':'GENERATION_ERROR','abstain':True,'generated_query':None,
              'query_sha256':None,'execution':None,'call':call,
              'prompt_sha256':hashlib.sha256(canonical(messages).encode()).hexdigest(),
              'private_evidence_read_by_generator':False,'adapter_sha256':sha(__file__)}
    if call.get('ok') and call.get('finish_reason') not in {'length','max_tokens'}:
        try:
            obj=json.loads(call['content'])
            if (not isinstance(obj,dict) or set(obj)!={'query','abstain'}
                    or type(obj['query']) is not str or type(obj['abstain']) is not bool
                    or len(obj['query'].encode())>65536
                    or obj['abstain'] and obj['query'].strip()
                    or not obj['abstain'] and not obj['query'].strip()):
                raise ValueError('invalid generated query envelope')
            record.update(generated_query=obj['query'],abstain=obj['abstain'],
                          status='ABSTAIN' if obj['abstain'] else 'QUERY_READY',
                          query_sha256=hashlib.sha256(obj['query'].encode()).hexdigest())
        except (TypeError,ValueError,KeyError) as exc:
            record.update(status='GENERATION_FORMAT_ERROR',error_class=type(exc).__name__)
    elif call.get('finish_reason') in {'length','max_tokens'}:
        record['status']='GENERATION_TRUNCATED'
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as stream:
        json.dump(record,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    return record


def decode_json_sql(value, schema):
    """Predeclared JSON/boolean representation codec; never numeric coercion."""
    if value is None or not isinstance(schema, dict):
        return value
    types = schema.get('type')
    types = {types} if isinstance(types, str) else set(types or [])
    # Integer0/1 is ambiguous if both numeric and boolean are valid. Preserve
    # it as a number in that case, rather than guessing from a gold value.
    if 'boolean' in types and not types.intersection({'integer', 'number'}):
        if type(value) is int and value in (0, 1):
            return bool(value)
    if isinstance(value, list) and ('array' in types or 'items' in schema):
        return [decode_json_sql(child, schema.get('items', {})) for child in value]
    if isinstance(value, dict) and ('object' in types or 'properties' in schema):
        properties = schema.get('properties', {})
        return {key: decode_json_sql(child, properties.get(key, {})) for key, child in value.items()}
    return value


def decode_sql_record(row, fields):
    """Only representation decoding declared by the requested answer types."""
    out = dict(row)
    for field in fields:
        name=field['name']
        if name not in out:
            continue
        value=out[name]
        if value is None:
            continue
        if field['type']=='json':
            decoded=json.loads(value) if isinstance(value,str) else value
            out[name]=decode_json_sql(decoded,field.get('json_schema',{}))
        elif field['type']=='boolean' and type(value) is int and value in (0,1):
            out[name]=bool(value)
    return out


def _result(status, rows, columns, start, byte_count=0, error=None):
    return {'status':status,'rows':rows,'columns':columns,'row_count_retained':len(rows),
            'complete':status=='OK','truncated':status in {'ROW_CAP','BYTE_CAP'},
            'retained_json_bytes':byte_count,'elapsed_s':round(time.monotonic()-start,6),
            'row_cap':ROW_CAP,'byte_cap':BYTE_CAP,'timeout_s':TIMEOUT_SECONDS,'error_class':error}


def file_identity(path):
    stat=Path(path).stat()
    return {'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns,'device':stat.st_dev,'inode':stat.st_ino}


def run_sql_query(db_path, query, fields, *, expected_db_sha=None, row_cap=ROW_CAP, byte_cap=BYTE_CAP,
                  timeout_s=TIMEOUT_SECONDS,source_guard_batch_verified=False,expected_db_stat=None):
    started=time.monotonic();rows=[];columns=[];size=0;db_path=Path(db_path).resolve(strict=True)
    if source_guard_batch_verified:
        if not expected_db_sha or expected_db_stat!=file_identity(db_path):
            return _result('SOURCE_MISMATCH',rows,columns,started)
    elif expected_db_sha and sha(db_path)!=expected_db_sha:
        return _result('SOURCE_MISMATCH',rows,columns,started)
    if not isinstance(query,str) or not re.match(r'^\s*(SELECT|WITH)\b',query,re.I):
        return _result('REJECTED',rows,columns,started)
    con=sqlite3.connect(db_path.as_uri()+'?mode=ro&immutable=1',uri=True,timeout=timeout_s)
    con.execute('PRAGMA query_only=ON');con.execute('PRAGMA temp_store=FILE');con.execute('PRAGMA cache_size=-32768')
    con.enable_load_extension(False)
    denied={sqlite3.SQLITE_ATTACH,sqlite3.SQLITE_DETACH,sqlite3.SQLITE_PRAGMA,sqlite3.SQLITE_INSERT,
            sqlite3.SQLITE_UPDATE,sqlite3.SQLITE_DELETE,sqlite3.SQLITE_CREATE_TABLE,
            sqlite3.SQLITE_CREATE_TEMP_TABLE,sqlite3.SQLITE_CREATE_INDEX,sqlite3.SQLITE_DROP_TABLE,
            sqlite3.SQLITE_ALTER_TABLE,sqlite3.SQLITE_TRANSACTION,sqlite3.SQLITE_SAVEPOINT}
    def authorize(action,arg1,arg2,database,source):
        if action in denied or action==sqlite3.SQLITE_READ and str(arg1).startswith('_'):
            return sqlite3.SQLITE_DENY
        if action==sqlite3.SQLITE_FUNCTION and str(arg2).lower() in {'load_extension','readfile','writefile'}:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    con.set_authorizer(authorize)
    con.set_progress_handler(lambda:int(time.monotonic()-started>timeout_s),1000)
    try:
        cur=con.execute(query);columns=[c[0] for c in cur.description or []]
        if len(columns)!=len(set(columns)):
            return _result('DUPLICATE_COLUMNS',rows,columns,started)
        status='OK'
        for values in cur:
            record=decode_sql_record(dict(zip(columns,values)),fields)
            added=len(canonical(record).encode())+1
            if len(rows)==row_cap:
                status='ROW_CAP';break
            if size+added>byte_cap:
                status='BYTE_CAP';break
            rows.append(record);size+=added
        result=_result(status,rows,columns,started,size)
        result.update(row_cap=row_cap,byte_cap=byte_cap,timeout_s=timeout_s,
                      source_guard_batch_verified=source_guard_batch_verified,
                      immutable_read_only=True,file_identity_after=file_identity(db_path))
        if source_guard_batch_verified and result['file_identity_after']!=expected_db_stat:
            result.update(status='SOURCE_MISMATCH',complete=False)
        return result
    except (sqlite3.Error,sqlite3.Warning,ValueError,TypeError,MemoryError) as exc:
        status='TIMEOUT' if time.monotonic()-started>timeout_s else 'ERROR'
        return _result(status,rows,columns,started,size,type(exc).__name__)
    finally:
        con.close()


def run_cypher_query(wg,query,executor_directory,*,source_guard_expected,
                     row_cap=ROW_CAP,byte_cap=BYTE_CAP,timeout_s=TIMEOUT_SECONDS,
                     source_guard_batch_verified=False):
    """Root calls after final freeze; no operational ports are configurable."""
    import sys
    executor_directory=Path(executor_directory).resolve(strict=True)
    sys.path.insert(0,str(executor_directory))
    spec=importlib.util.spec_from_file_location('empirical_frozen_executor',executor_directory/'execute_frozen_reference_gold.py')
    executor=importlib.util.module_from_spec(spec);spec.loader.exec_module(executor)
    guard_spec=importlib.util.spec_from_file_location('empirical_frozen_read_guard',executor_directory/'replay_generated_read_queries.py')
    guard=importlib.util.module_from_spec(guard_spec);guard_spec.loader.exec_module(guard)
    if not source_guard_expected or source_guard_expected['wg']!=wg:
        raise ValueError('frozen source guard identity required')
    if source_guard_batch_verified:
        manifest=executor_directory/'_frozen_ttl_v1'/wg.lower()/'import_manifest.json'
        if sha(manifest)!=source_guard_expected['import_manifest_sha256']:
            raise ValueError('frozen import manifest changed within batch')
    elif executor.source_guard(wg)!=source_guard_expected:
        raise ValueError('frozen graph source guard changed before model query')
    from neo4j import GraphDatabase,READ_ACCESS
    started=time.monotonic();rows=[];columns=[];size=0
    rollback_completed=False;summary_complete=False;plan_type=None;execution_type=None
    try:
        clean=guard.screen_query(query)
        guard.owned_container_guard(wg)
        with GraphDatabase.driver('bolt://127.0.0.1:'+str(executor.PORTS[wg]),auth=None,
                                  connection_timeout=5,max_transaction_retry_time=0) as driver:
            with driver.session(database='neo4j',default_access_mode=READ_ACCESS,fetch_size=100) as session:
                tx=session.begin_transaction(timeout=timeout_s)
                try:
                    plan=tx.run('EXPLAIN '+clean).consume();guard.require_read_plan(plan);plan_type=plan.query_type
                    cur=tx.run(clean);columns=list(cur.keys());status='OK'
                    if len(columns)!=len(set(columns)):
                        raise ValueError('duplicate query aliases')
                    for row in cur:
                        record=row.data();added=len(canonical(record).encode())+1
                        if len(rows)==row_cap:
                            status='ROW_CAP';break
                        if size+added>byte_cap:
                            status='BYTE_CAP';break
                        rows.append(record);size+=added
                    if status=='OK':
                        actual=cur.consume();execution_type=actual.query_type
                        if actual.query_type!='r' or actual.counters.contains_updates or actual.counters.contains_system_updates:
                            raise ValueError('generated query execution was not ordinary read')
                        summary_complete=True
                finally:
                    tx.rollback();rollback_completed=True
        result=_result(status,rows,columns,started,size)
        result.update(plan_query_type=plan_type,execution_query_type=execution_type,
                      execution_summary_complete=summary_complete,rollback_completed=rollback_completed,
                      source_guard_batch_verified=source_guard_batch_verified,
                      row_cap=row_cap,byte_cap=byte_cap,timeout_s=timeout_s)
    except Exception as exc:
        result=_result('ERROR',rows,columns,started,size,type(exc).__name__)
    result.update(plan_query_type=plan_type,execution_query_type=execution_type,
                  execution_summary_complete=summary_complete,rollback_completed=rollback_completed,
                  source_guard_batch_verified=source_guard_batch_verified)
    guard.owned_container_guard(wg)
    if not source_guard_batch_verified and executor.source_guard(wg)!=source_guard_expected:
        raise ValueError('frozen graph source guard changed after model query')
    return result


def execute_generated(record, task_public, *, sql_db=None, expected_sql_sha=None,
                      executor_directory=None, source_guard_expected=None,
                      source_guard_batch_verified=False,expected_sql_stat=None):
    if record['id']!=task_public['id'] or record['repair_sha256']!=task_public['repair_sha256']:
        raise ValueError('task/query identity differs from frozen definition')
    if record['status']!='QUERY_READY':
        return record
    result=dict(record)
    query=record['generated_query']
    if hashlib.sha256(query.encode()).hexdigest()!=record['query_sha256']:
        raise ValueError('generated query changed')
    if record['method']=='Text2SQL':
        execution=run_sql_query(sql_db,query,output_format(task_public)['required_fields'],expected_db_sha=expected_sql_sha,
                                source_guard_batch_verified=source_guard_batch_verified,expected_db_stat=expected_sql_stat)
    else:
        execution=run_cypher_query(record['wg'],query,executor_directory,source_guard_expected=source_guard_expected,
                                   source_guard_batch_verified=source_guard_batch_verified)
    result.update(execution=execution,status=execution['status'],
                  records=execution['rows'] if execution['complete'] else [],
                  abstain=not execution['complete'])
    # Full partial output stays in execution for auditing but cannot be scored
    # as a complete answer when an operational cap or error was encountered.
    return result
