"""Replay matrix mutations with the declared scorer, without source/API/native access."""
from copy import deepcopy
import hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import original_scorer
def actual_controls(task,records):
    rows=sorted({r["companyName"] for r in records})
    dims=sorted({r["specNumber"] for r in records})
    sparse=[{"matrix":{"rowField":"companyName","columnField":"specNumber","valueField":"crCount","rowValues":rows,"columnValues":dims,"default":0,"cells":[r for r in records if r["crCount"]>0]}}]
    controls=[]
    def control(name,values,expected):
        score=original_scorer.score(task,records,values,diagnostic=True)
        assert score['exact'] is expected,(name,score)
        controls.append({'name':name,'expected_exact':expected,'actual':score,'prediction_records_sha256':hashlib.sha256(json.dumps(values,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()})
    control('complete_dense',records,True);control('complete_explicit_axes_sparse',sparse,True)
    control('dense_reverse_order',records[::-1],True)
    control('positive_records_without_axes',[r for r in records if r['crCount']],False)
    control('dense_missing_coordinate',records[1:],False)
    control('same_dense_coordinate_repeated',records+[records[0]],True)
    wrong=deepcopy(records);wrong[0]['crCount']+=1;control('wrong_CR_count',wrong,False)
    wrong=deepcopy(records);wrong[0]['crCount']=str(wrong[0]['crCount']);control('wrong_count_string',wrong,False)
    wrong=deepcopy(records);wrong[0]['crCount']=bool(wrong[0]['crCount']);control('wrong_count_boolean',wrong,False)
    wrong=deepcopy(records);wrong[0].pop('specNumber');control('missing_requested_spec_role',wrong,False)
    wrong=deepcopy(records);wrong[0]['companyName'],wrong[0]['specNumber']=wrong[0]['specNumber'],wrong[0]['companyName'];control('swapped_requested_roles',wrong,False)
    def mutate(name,fn,expected=False):
        values=deepcopy(sparse);fn(values[0]['matrix']);control(name,values,expected)
    mutate('sparse_missing_company_axis',lambda m:(m.update(rowValues=rows[1:]),m.update(cells=[r for r in m['cells'] if r['companyName']!=rows[0]])))
    mutate('sparse_missing_spec_axis',lambda m:(m.update(columnValues=dims[1:]),m.update(cells=[r for r in m['cells'] if r['specNumber']!=dims[0]])))
    mutate('sparse_extra_unknown_company_axis',lambda m:m['rowValues'].append('SYNTHETIC_UNKNOWN_COMPANY_CONTROL'))
    mutate('sparse_extra_excluded_series_spec',lambda m:m['columnValues'].append('38.591-1'))
    mutate('sparse_missing_nonzero_cell',lambda m:m.update(cells=m['cells'][1:]))
    mutate('sparse_wrong_declared_default',lambda m:m.update(default=False))
    mutate('sparse_wrong_role_descriptor',lambda m:m.update(valueField='rank'))
    mutate('sparse_missing_axis_definition',lambda m:m.pop('columnValues'))
    mutate('sparse_conflicting_coordinate',lambda m:m['cells'].append(dict(m['cells'][0],crCount=m['cells'][0]['crCount']+1)))
    mutate('sparse_repeat_coordinate',lambda m:m['cells'].append(deepcopy(m['cells'][0])),True)
    mutate('sparse_repeat_company_axis',lambda m:m['rowValues'].append(rows[0]),True)
    mutate('sparse_axis_order_independent',lambda m:(m['rowValues'].reverse(),m['columnValues'].reverse()),True)
    return controls
