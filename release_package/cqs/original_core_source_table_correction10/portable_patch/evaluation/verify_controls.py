"""Replay native-derived source-variant scoring controls without network access."""
import json
from pathlib import Path
import original_scorer
from contract_checks import checks

def main():
    here=Path(__file__).resolve().parent
    task=json.loads((here/'tasks.jsonl').read_text())
    reference=json.loads((here/'reference_gold.jsonl').read_text())
    rows=reference['records']
    assert reference['repair_sha256']==task['repair_sha256']
    observed=[json.loads(s) for s in (here.parent/'evidence/actual_query_result80_observations.jsonl').read_text().splitlines()]
    assert rows==[{'tableId':r['tableId']} for r in observed]
    assert len(rows)==80 and len(set(r['tableId'] for r in rows))==80
    scope=json.loads((here.parent/'source/source_units80.json').read_text())
    new=set(r['properties']['tableId'] for r in json.loads((here.parent/'patch/new_node_edge_mapping10.json').read_text())['new_tables'])
    old=[r for r in rows if r['tableId'] not in new]
    assert len(new)==10 and len(old)==70
    base=checks(task,rows);assert all(r['pass'] for r in base)
    controls=[]
    def check(name,predicted,expected):
        result=original_scorer.score(task,rows,predicted,diagnostic=True)
        record={'name':name,'expected_exact':expected,'actual':result,'pass':result['exact'] is expected}
        assert record['pass'];controls.append(record)
    check('actual_native80_any_order',list(reversed(rows)),True)
    check('native_all_projected_fields_are_compatible_auxiliary',observed,True)
    check('set_duplicate_witness',rows+rows[:1],True)
    check('auxiliary_caption_or_number_ignored',[{**r,'tableCaption':'aux','tableNumber':'aux'} for r in rows],True)
    check('old_frozen70_is_incomplete_for_separate_source_variant',old,False)
    check('latest_edition_only',[r for r in rows if '-Rel-19-' in r['tableId']],False)
    missing=sorted(new)[0];without=[r for r in rows if r['tableId']!=missing]
    check('one_new_actual_table_missing',without,False)
    check('duplicate_displaces_new_table',without+old[:1],False)
    check('unasked_limit25',rows[:25],False)
    check('null_identity',[{'tableId':None}]+rows[1:],False)
    check('wrong_type_identity',[{'tableId':1}]+rows[1:],False)
    check('caption_is_not_table_identity',[{'tableId':r['tableCaption']} for r in observed],False)
    check('ordinal_is_not_edition_aware_table_identity',[{'tableId':r['tableNumber']} for r in observed],False)
    collapsed={}
    for r in observed:collapsed.setdefault(r['tableNumber'],{'tableId':r['tableId']})
    check('collapse_edition_identity',list(collapsed.values()),False)
    unrelated=json.loads((here/'actual_unrelated_TableId_control.json').read_text())['tableId']
    check('actual_unrelated_table_added',rows+[{'tableId':unrelated}],False)
    void={r['tableId'] for r in scope if r['actual_Word_table'] is None}
    check('physical_only62_changes_TSTable_record_unit',[r for r in rows if r['tableId'] not in void],False)
    print(json.dumps({'actual_native_derived_required_records':len(rows),'base_controls':base,'scope_controls':controls,'controls_n':len(base)+len(controls),'all_pass':True,'model_performance_claimed':False},ensure_ascii=False,sort_keys=True))

if __name__=='__main__':main()
