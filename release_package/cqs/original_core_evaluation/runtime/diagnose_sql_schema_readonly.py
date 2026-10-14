#!/usr/bin/env python3
"""Diagnose saved SQL compile errors; never execute answer queries or regenerate.

Only SQLite metadata and EXPLAIN compilation are read. No EXPLAIN opcodes are
executed, no benchmark rows are fetched, and no generated query is repaired.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3

BASE = Path(__file__).resolve().parent
RUN = BASE/'runs/original-core-main'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    result={'kind':'Read-only diagnostic of saved Text2SQL generation and schema metadata',
        'completed_utc':datetime.now(timezone.utc).isoformat(),
        'protocol_sha256':sha(RUN/'protocol.json'),
        'adapter_sha256':sha(BASE/'structured_adapter.py'),
        'paid_calls':0,'answer_query_executions':0,'query_repairs':0,
        'source_changed':False,'workgroups':{},'items':[]}
    generation=Counter();statuses=Counter();compile_status=Counter();errors=Counter();naming=Counter()
    for wg in ('RAN1','RAN2','RAN3','RAN4','RAN5'):
        db=BASE/'relational'/(wg+'.sqlite')
        before=sha(db)
        schema_path=RUN/'schemas'/(wg+'_sql.json')
        schema=json.loads(schema_path.read_text())
        connection=sqlite3.connect(db.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
        tables={row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        declared=set(schema['relationship_tables'])
        missing_labels=sorted(set(schema['label_tables'])-tables)
        missing_prefixed=sorted('rel_'+name for name in declared if 'rel_'+name not in tables)
        bare_names_present=sorted(declared & tables)
        def authorize(action,arg1,arg2,database,source):
            if action in {sqlite3.SQLITE_ATTACH,sqlite3.SQLITE_DETACH,sqlite3.SQLITE_PRAGMA,
                          sqlite3.SQLITE_INSERT,sqlite3.SQLITE_UPDATE,sqlite3.SQLITE_DELETE,
                          sqlite3.SQLITE_CREATE_TABLE,sqlite3.SQLITE_CREATE_TEMP_TABLE,
                          sqlite3.SQLITE_CREATE_INDEX,sqlite3.SQLITE_DROP_TABLE,
                          sqlite3.SQLITE_ALTER_TABLE,sqlite3.SQLITE_TRANSACTION,sqlite3.SQLITE_SAVEPOINT}:
                return sqlite3.SQLITE_DENY
            if action==sqlite3.SQLITE_READ and str(arg1).startswith('_'):
                return sqlite3.SQLITE_DENY
            if action==sqlite3.SQLITE_FUNCTION and str(arg2).lower() in {'load_extension','readfile','writefile'}:
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK
        connection.set_authorizer(authorize)
        for file in sorted((RUN/'arm_outputs/text2sql').glob(wg+'_*.json')):
            output=json.loads(file.read_text());id=output['id'];generation[output['status']]+=1
            executed_path=RUN/'executed/text2sql'/(id+'.json')
            execution=json.loads(executed_path.read_text()) if executed_path.exists() else {}
            statuses[execution.get('status','not_retained')]+=1
            if output['status']!='QUERY_READY':continue
            query=output['generated_query']
            item={'id':id,'generation_sha256':sha(file),
                'execution_sha256':sha(executed_path) if executed_path.exists() else None,
                'generated_query_sha256':hashlib.sha256(query.encode()).hexdigest(),
                'saved_execution_status':execution.get('status')}
            try:
                # EXPLAIN is compiled only: fetch no opcode or answer rows.
                connection.execute('EXPLAIN '+query)
                item['compile']='OK';compile_status['OK']+=1
            except sqlite3.Error as error:
                text=str(error);item.update(compile='ERROR',error_class=type(error).__name__,compile_error=text)
                compile_status['ERROR']+=1
                match=re.match(r'no such table: (.+)',text)
                if match:
                    table=match.group(1)
                    category='missing_relation_prefix' if table in declared and 'rel_'+table in tables else 'other_missing_table'
                    item['missing_table']=table
                elif text.startswith('no such column:'):
                    category='missing_column'
                elif 'syntax error' in text or 'incomplete input' in text:
                    category='syntax'
                elif 'not authorized' in text or 'prohibited' in text:
                    category='read_guard_rejection'
                else:category='other_compile_error'
                item['error_category']=category;errors[category]+=1
            relations=[]
            for name in declared:
                # Count quoted/unquoted direct relation table references in FROM/JOIN.
                pattern=r'\b(?:FROM|JOIN)\s+["`\[]?'+re.escape(name)+r'["`\]]?(?=\s|$|\))'
                if re.search(pattern,query,re.I):relations.append(name)
            item['unprefixed_declared_relation_references']=sorted(relations)
            if relations:naming['items_with_unprefixed_declared_relationship_table']+=1
            result['items'].append(item)
        connection.close()
        after=sha(db)
        if before!=after:raise ValueError('readonly source bytes changed: '+wg)
        result['workgroups'][wg]={'schema_sha256':sha(schema_path),'sqlite_sha256':before,
            'source_unchanged':True,'declared_label_tables_absent':missing_labels,
            'declared_prefixed_relation_tables_absent':missing_prefixed,
            'unprefixed_relationship_names_present_as_actual_tables':bare_names_present,
            'relationship_types_n':len(declared)}
    result.update(generation_statuses=dict(generation),saved_execution_statuses=dict(statuses),
        compile_only_statuses=dict(compile_status),compile_error_categories=dict(errors),
        naming_diagnostic=dict(naming),
        interpretation={'actual_table_names':'Directed relationship tables are physically rel_TYPE.',
            'system_instruction':'The frozen SQL system prompt explicitly states directed rel_TYPE tables.',
            'schema_card':'relationship_tables keys are unprefixed relationship-type names, not explicit physical table names.',
            'scope':'Missing-prefix failures are preserved model outputs. The schema presentation could be clearer; this audit does not prove that clarifying it would improve performance or establish a runtime executor bug.',
            'quality_retries_or_score_relabeling':'None. No generation, answer execution, performance rescoring or table aliases are added.'})
    target=BASE/'sql_generation_schema_diagnostic.json'
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ('generation_statuses','saved_execution_statuses','compile_only_statuses','compile_error_categories','naming_diagnostic')}))


if __name__=='__main__':main()
