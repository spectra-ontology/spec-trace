"""Production-dispatch tests using explicit prospective validation envelopes.
No registration, admission or model call is performed by this test harness.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
if sys.flags.optimize:
    raise RuntimeError('optimized Python is not supported')
sys.dont_write_bytecode = True
D = Path(__file__).absolute().parent
P = D.parent
sys.path[:0] = [str(D), str(P), str(P / 'canonical')]
import score_predictions_partitioned_dispatch as dispatch
import scorer
import original_scorer
import verify_release

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
def require(condition, message):
    if not condition:
        raise ValueError(message)

out = D / 'actual_production_reader_controls_v1'
require(not out.exists(), 'Preserve previous production controls')
out.mkdir()
fixture = out / 'fixture'; fixture.mkdir()
definition = json.loads((P/'definition.json').read_text())
identity = verify_release.digest(definition)
task = dict(definition, repair_sha256=identity, validation_status='validated')
dump(fixture/'prospective_validated_task_fixture.json', task)
file_paths = {
 'task': fixture/'prospective_validated_task_fixture.json',
 'definition': P/'definition.json',
 'policy': P/'nested_eligibility_policy.json',
 'limited_native_records': P/'actual_native_SQL_bridge_v1/actual_limited_native_projected_records.jsonl',
 'full_native_partition_population': P/'actual_native_SQL_bridge_v1/actual_native_full_partition_population.json',
 'metric_code': D/'partitioned_complete_record_score.py',
 'dispatch_code': D/'score_predictions_partitioned_dispatch.py',
 'metric_specification': D/'prospective_metric_dispatch_specification.json'}
declaration = {'id':definition['id'], 'repair_sha256':identity,
 'dispatch':'explicit_partitioned_top_k_complete_outer_WI_record',
 'limited_native_is_eligibility_population':False,
 'fixture_status':'prospective validation-envelope control fixture; not a registry or admission',
 'files':{key:{'path':str(path.relative_to(P)), 'bytes':path.stat().st_size,'sha256':sha(path)}
          for key,path in file_paths.items()}}
declaration_path = fixture/'dispatch_declaration.json'; dump(declaration_path,declaration)
outputs=[]
flags=[]
original_inner=original_scorer.score
original_outer=scorer.score
def inner(*args, **kwargs):
    flags.append({'module':'original_scorer','diagnostic':kwargs.get('diagnostic',False),
                  'validated':args[0].get('validation_status')})
    require(kwargs.get('diagnostic',False) is False, 'Diagnostic inner call in production')
    return original_inner(*args,**kwargs)
def outer(*args, **kwargs):
    flags.append({'module':'scorer','diagnostic':kwargs.get('diagnostic',False),
                  'validated':args[0].get('validation_status')})
    require(kwargs.get('diagnostic',False) is False, 'Diagnostic outer call in production')
    return original_outer(*args,**kwargs)
original_scorer.score=inner; scorer.score=outer
prior=json.loads((D/'actual_original_five_tie_diagnostic_controls.json').read_text())
for index,test in enumerate(prior['controls']):
    prediction={'id':definition['id'],'repair_sha256':identity,'records':test['input']}
    prediction_path=fixture/'prediction.jsonl'
    prediction_path.write_text(scorer.get_kernel().json_exact(prediction)+'\n')
    result=dispatch.read_run(P,declaration_path,prediction_path)
    ok=result['diagnostic_only'] is False and result['exact'] is test['expected']['exact']
    for key in ['matched_records','precision','recall','f1']:
        if key in test['expected'] and test['expected'][key] is not None:
            ok=ok and math.isclose(result[key],test['expected'][key],rel_tol=0,abs_tol=1e-12)
    require(ok, test['name'])
    outputs.append({'name':test['name'],'expected':test['expected'],'actual':result,'PASS':ok})
base=json.loads((P/'actual_native_SQL_bridge_v1/actual_limited_native_projected_records.jsonl').read_text().splitlines()[0])
native=[json.loads(x) for x in file_paths['limited_native_records'].read_text().splitlines()]
prediction={'id':definition['id'],'repair_sha256':identity,'records':native}
dump(fixture/'actual_native_prediction_envelope.json',prediction)
prediction_path.write_text(scorer.get_kernel().json_exact(prediction)+'\n')
actual_native=dispatch.read_run(P,declaration_path,prediction_path)
require(actual_native['exact'] is True and actual_native['diagnostic_only'] is False,'actual native production')
rejections=[]
def rejected(name, thunk):
    try:
        thunk()
    except (ValueError,KeyError,TypeError) as exc:
        rejections.append({'name':name,'rejected':True,'error':type(exc).__name__+': '+str(exc)})
    else:
        raise ValueError('Accepted adverse production input: '+name)
policy=json.loads(file_paths['policy'].read_text())
population=json.loads(file_paths['full_native_partition_population'].read_text())
def values(t=task,d=definition,decl=declaration,pred=prediction,pop=population,lim=native):
    return dispatch.run(t,d,policy,lim,pop,pred,decl)
for status in [None,'development_probe','two_pass',False,1]:
    t=copy.deepcopy(task); t['validation_status']=status
    rejected('unvalidated_task_'+repr(status),lambda t=t:values(t=t))
for key,value in [('id','wrong'),('repair_sha256','0'*64),('question_en','wrong'),
                  ('reference_query','RETURN 1'),('required_fields',[])]:
    t=copy.deepcopy(task); t[key]=value
    rejected('task_binding_'+key,lambda t=t:values(t=t))
for key,value in [('id','wrong'),('repair_sha256','0'*64),('dispatch','generic_set'),
                  ('limited_native_is_eligibility_population',True)]:
    decl=copy.deepcopy(declaration);decl[key]=value
    rejected('declaration_'+key,lambda decl=decl:values(decl=decl))
t=copy.deepcopy(definition);t['validation_status']='validated'
rejected('validated_field_added_to_nine_key_definition',lambda:values(d=t))
for key,value in [('id','wrong'),('repair_sha256','0'*64)]:
    pred=copy.deepcopy(prediction);pred[key]=value
    rejected('prediction_'+key,lambda pred=pred:values(pred=pred))
pred=copy.deepcopy(prediction);pred['admitted']=True
rejected('surplus_prediction_metadata',lambda:values(pred=pred))
lim=copy.deepcopy(native);lim[0]['topCompanies'][0]['count']+=100
rejected('actual_native_bridge_wrong_count',lambda:values(lim=lim))
for role in ['task','definition','policy','limited_native_records','full_native_partition_population',
             'metric_code','dispatch_code','metric_specification']:
    decl=copy.deepcopy(declaration);decl['files'][role]['sha256']='0'*64
    bad=fixture/('bad_'+role+'.json');dump(bad,decl)
    rejected('reader_bad_byte_pin_'+role,lambda bad=bad:dispatch.read_run(P,bad,prediction_path))
for value in [True,float(file_paths['task'].stat().st_size)]:
    decl=copy.deepcopy(declaration);decl['files']['task']['bytes']=value
    bad=fixture/('bad_bytes_'+repr(value)+'.json');dump(bad,decl)
    rejected('reader_bytes_strict_type_'+repr(value),lambda bad=bad:dispatch.read_run(P,bad,prediction_path))
# Restore the actual-native valid prediction after negative fixtures.
prediction_path.write_text(scorer.get_kernel().json_exact(prediction)+'\n')
canonical={x.name:sha(x) for x in (P/'canonical').iterdir() if x.is_file()}
expected_pins=json.loads((P/'scientific_module_pins.json').read_text())['copied']
require(all(canonical[name]==entry['sha256'] for name,entry in expected_pins.items()),'canonical scientific bytes drift')
receipt={'status':'PASS','id':definition['id'],'repair_sha256':identity,
 'production_reader_controls_n':len(outputs),'production_rejections_n':len(rejections),
 'all_5_lawful_subsets_accepted':True,'original_complete_outer_WI_record_metric_preserved':True,
 'actual_native5_production_replay':actual_native,
 'actual_native5_not_full_1939_group_eligibility':True,
 'production_internal_calls':{'count':len(flags),'diagnostic_true_calls':sum(x['diagnostic'] is True for x in flags),
       'all_subcontracts_validated':all(x['validated']=='validated' for x in flags)},
 'controls':outputs,'rejections':rejections,'canonical9_unchanged':True,
 'validation_envelope_is_prospective_control_fixture_not_admission':True,
 'API_calls':0,'native_calls':0,'database_calls':0,'public_mutations':0,
 'inputs':{str(path.relative_to(P)):{'bytes':path.stat().st_size,'sha256':sha(path)}
    for path in [*file_paths.values(),D/'replay_production_reader_controls.py',declaration_path]},
 'remaining_gate':'Actual admitted task envelope must be issued by ROOT after final acceptance; this exercises the same non-diagnostic production branch with a clearly labelled validation-envelope fixture.'}
result=out/'actual_production_dispatch_and_reader_controls.json';dump(result,receipt)
print(json.dumps({'status':'PASS','production_controls':len(outputs),'rejections':len(rejections),
 'diagnostic_true_calls':0,'receipt_sha256':sha(result)}))
