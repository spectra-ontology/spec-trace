#!/usr/bin/env python3
"""Check public audit comparison against changed real diagnostic fields."""
import argparse
import copy
from pathlib import Path
import census_tree_gate as gate
import projected_audit_gate as projected


def find_leaf(expected,actual,wanted,path=()):
    if wanted=='withheld' and isinstance(expected,dict) and expected.get('withheld') is True and isinstance(actual,str):
        return path
    if wanted=='inline' and isinstance(expected,str) and projected.INLINE.search(expected):
        return path
    if isinstance(expected,dict) and isinstance(actual,dict):
        for key in expected:
            result=find_leaf(expected[key],actual[key],wanted,path+(key,))
            if result is not None:return result
    if isinstance(expected,list) and isinstance(actual,list):
        for key,(left,right) in enumerate(zip(expected,actual)):
            result=find_leaf(left,right,wanted,path+(key,))
            if result is not None:return result
    return None


def access(value,path):
    for key in path:value=value[key]
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['code','public-reference','actual','out']:
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    runner=gate.load(args.code/'restore_census_artifact.py','negative_projection_runner')
    expected=projected.fields(runner,'clause',gate.read(args.public_reference))
    actual=projected.fields(runner,'clause',gate.read(args.actual))
    counts={};projected.project_like_reference(expected,actual,counts)
    controls=[]
    for name in ['changed_withheld_diagnostic','changed_inline_filename','changed_withheld_digest','missing_diagnostic_field','changed_visible_count']:
        left,right=copy.deepcopy(expected),copy.deepcopy(actual)
        if name in ['changed_withheld_diagnostic','changed_inline_filename','changed_withheld_digest','missing_diagnostic_field']:
            path=find_leaf(left,right,'inline' if name=='changed_inline_filename' else 'withheld')
            if path is None:raise ValueError('Real projection control leaf not found')
            if name=='changed_withheld_digest':
                access(left,path)['sha256']='0'*64
            elif name=='missing_diagnostic_field':
                del access(right,path[:-1])[path[-1]]
            elif name=='changed_inline_filename':
                old=access(right,path);index=projected.INLINE.search(access(left,path)).start()
                access(right,path[:-1])[path[-1]]=old[:index]+('X' if old[index]!='X' else 'Y')+old[index+1:]
            else:
                access(right,path[:-1])[path[-1]]+='X'
        else:
            right['corpus']['filesRead']+=1
        try:
            projected.project_like_reference(left,right,{})
            rejected=False
        except ValueError:
            rejected=True
        controls.append({'control':name,'rejectedAsExpected':rejected})
    receipt={'schema':gate.SCHEMA,'helperSha256':gate.digest(projected.__file__),'testHelperSha256':gate.digest(__file__),
        'publicReferenceSha256':gate.digest(args.public_reference),'actualAuditSha256':gate.digest(args.actual),
        'baselineProjectionVerified':True,'baselineProjectionCounts':counts,'controls':controls,
        'passed':all(r['rejectedAsExpected'] for r in controls),'sourceTextIncluded':False}
    gate.write(args.out,receipt)
    print({'passed':receipt['passed'],'controls':len(controls),'baselineProjectionCounts':counts})
    if not receipt['passed']:raise SystemExit(1)


if __name__=='__main__':main()
