"""Replay a finite pack-scope counterexample; no answer policy is selected."""
import sys
if sys.flags.optimize:
    raise SystemExit('Optimized verification is refused.')
import ast
from collections import Counter
import encodings.ascii
import encodings.cp437
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import sqlite3
import xml.etree.ElementTree as E
import zipfile

HERE = Path(os.path.abspath(__file__)).parent


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def no_symlink(path):
    for part in (path, *path.parents):
        require(not part.is_symlink(), 'Symlink boundary rejected')


no_symlink(HERE)
for path in HERE.rglob('*'):
    no_symlink(path)
    require(path.is_file() or path.is_dir(), 'Nonregular entry rejected')
inventory_bytes = (HERE/'inventory.json').read_bytes()
require(hashlib.sha256(inventory_bytes).hexdigest() == '3a358c3a52f870d0cc408a09616e51c8498d1cfc1945df662f4dc73b29eccd5c', 'Inventory changed')
inventory = json.loads(inventory_bytes)
require({str(p.relative_to(HERE)) for p in HERE.rglob('*') if p.is_file()} == set(inventory)|{'inventory.json','verify_evidence.py'}, 'Closed inventory differs')
for name, expected in inventory.items():
    value=(HERE/name).read_bytes()
    require(len(value)==expected['bytes'] and hashlib.sha256(value).hexdigest()==expected['sha256'], 'Payload differs: '+name)


def audit(event, args):
    if event in {'subprocess.Popen','os.system'} or event.startswith('socket.'):
        raise RuntimeError('External execution/network is forbidden')
    if event=='sqlite3.connect':
        require(args[0] in (':memory:',b':memory:'), 'Only the in-memory diagnostic database is allowed')
    if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
        path=Path(os.fsdecode(args[0]));path=path if path.is_absolute() else Path.cwd()/path
        no_symlink(path)
        require(path.resolve().is_relative_to(HERE), 'Artifact read outside included package')
        require(args[1] is None or not any(c in str(args[1]) for c in 'wax+'), 'Artifact writes forbidden')


sys.addaudithook(audit)


def load(name):
    return json.loads((HERE/name).read_bytes())


def pin(name, expected):
    value=(HERE/name).read_bytes()
    require(len(value)==expected['bytes'] and hashlib.sha256(value).hexdigest()==expected['sha256'], 'Historical binding differs: '+name)


row=load('original_row.json')
require(row['id']=='RAN5_P4_CQ3-1', 'Wrong question identity')
require(hashlib.sha256(row['question_en'].encode()).hexdigest()=='d0546d700ddc1ef7670027a1b492d86cf5370819429ad626d6e03c45cdca44b0', 'Original English differs')
require(hashlib.sha256(row['cypher'].encode()).hexdigest()=='66f6207044ad4a7c7538a73da04fbb802745aa8712d5f0bb083dee4769e2ed48', 'Original query differs')
authority=load('authority_excerpts.json')['read_original_authority']
for item in authority:
    name='authority/'+Path(item['source']['path']).name
    pin(name,item['source'])
    lines=(HERE/name).read_text().splitlines()
    require(all(lines[x['line']-1]==x['text'] for x in item['exact_text']), 'Original authority excerpt differs')
design=(HERE/'authority/RAN5_original_Phase4_INDEX_design.md').read_text()
require('특정 CR Pack에 포함된 CR 목록과 변경 요약은?' in design, 'Positive single-pack authority missing')
runner=ast.parse((HERE/'authority/RAN5_original_Phase4_INDEX_runner.py').read_text())
runs=[n for n in ast.walk(runner) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='run']
require(len(runs)==1 and ast.unparse(runs[0])=='session.run(query)' and len(runs[0].args)==1 and not runs[0].keywords, 'Original unbound runner differs')

prior=load('historical_scope_and_source.json')
root=load('ROOT_historical_scope_and_source.json')
pin('original_register.xlsx',prior['source_original_register'])
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(io.BytesIO((HERE/'original_register.xlsx').read_bytes())) as z:
    shared=[''.join(x.itertext()) for x in E.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)]
    for member in {x['sheet_member'] for x in prior['source_three_exact_rows']}:
        raw=z.read(member);require(hashlib.sha256(raw).hexdigest()==root['source_worksheet_sha256'],'Source worksheet differs')
        sheet=E.fromstring(raw)
        for number, expected in root['source_actual_rows'].items():
            element=next(x for x in sheet.findall('.//s:sheetData/s:row',ns) if x.get('r')==number)
            cells={}
            for cell in element.findall('s:c',ns):
                v=cell.find('s:v',ns);value=v.text if v is not None else ''
                if cell.get('t')=='s' and value:value=shared[int(value)]
                if cell.get('t')=='inlineStr':value=''.join(cell.find('s:is',ns).itertext())
                cells[cell.get('r')]=value
            require(cells==expected,'Own source membership/header differs')
require(root['source_actual_rows']['1']['A1']=='TDoc' and root['source_actual_rows']['1']['Z1']=='TSG CR Pack','Source header role differs')

records=[json.loads(line) for line in gzip.decompress((HERE/'full_frozen_pack_projection.jsonl.gz').read_bytes()).splitlines()]
require(len(records)==23262 and len({r[0] for r in records})==23262 and len({r[1] for r in records})==1220,'Finite complete projection count differs')
c=sqlite3.connect(':memory:');c.execute('CREATE TABLE matches(edge_id INTEGER,pack_node INTEGER,cr_node INTEGER,crPackId TEXT,tdocNumber TEXT,summary TEXT)')
c.executemany('INSERT INTO matches VALUES(?,?,?,?,?,?)',records)
def public(rows):
    return [{'crPackId':r[3],'tdocNumber':r[4],'summaryOfChange':r[5]} for r in rows]
global_sql=public(c.execute('SELECT * FROM matches ORDER BY tdocNumber LIMIT 10').fetchall())
require(global_sql==public(sorted(records,key=lambda r:r[4])[:10])==root['exact_frozen_global10'],'Global query projection differs')
require(len({r['crPackId'] for r in global_sql})==6 and any(r['summaryOfChange'] is None for r in global_sql),'Six-pack/null counterexample differs')
groups={}
for pack in ['RP-181570','RP-181571']:
    selected=public(c.execute('SELECT * FROM matches WHERE crPackId=? ORDER BY tdocNumber LIMIT 10',(pack,)).fetchall())
    require(selected==public(sorted((r for r in records if r[3]==pack),key=lambda r:r[4])[:10])==root['counterpolicy_same_sort_and_limit'][pack],'Single-pack counterpolicy differs')
    require(len(selected)==10 and {r['crPackId'] for r in selected}=={pack},'Coherent single-pack scope differs')
    require(len([r for r in records if r[3]==pack])==prior['bound_single_pack_counterexamples'][pack]['total_frozen_members'],'Conditional full frozen group count differs')
    groups[pack]=selected
require(not ({r['tdocNumber'] for r in groups['RP-181570']}&{r['tdocNumber'] for r in groups['RP-181571']}),'Two choices no longer disjoint')
for tid,pack,number in [('R5-184054','RP-181570','56'),('R5-184087','RP-181570','89'),('R5-184226','RP-181571','228')]:
    require(root['source_actual_rows'][number]['A'+number]==tid and root['source_actual_rows'][number]['Z'+number]==pack,'Own documentary membership identity differs')
    require(any(r['tdocNumber']==tid for r in groups[pack]),'Source member not in diagnostic group')
criteria=load('criteria.json');primary=load('primary_seven_units.json');secondary=load('ROOT_final_scope_classification.json')
require([x['unit'] for x in primary['semantic_units']]==criteria['semantic_units'],'Primary seven-unit coverage differs')
require(primary['local_recommendation']=='clarification_required' and primary['admitted'] is False and primary['expert_validation_n']==0,'Primary classification/attribution differs')
require([x['unit'] for x in secondary['exact_seven_unit_findings']]==criteria['semantic_units'],'ROOT seven-unit coverage differs')
require(secondary['recommendation']=='clarification_required' and secondary['public_admission'] is False and secondary['human_expert_validation_n']==0,'ROOT classification/attribution differs')
pin('primary_seven_units.json',secondary['primary_evidence']['primary_review'])
pin('ROOT_historical_scope_and_source.json',secondary['ROOT_fresh_replay'])
seal=load('ROOT_final_seal.json');pin('ROOT_final_scope_classification.json',seal['final_packet'])
require(seal['final_local_decision']=='clarification_required' and seal['public_admission'] is False,'Completed classification seal differs')
c.close()
print(json.dumps({'status':'PASS','id':row['id'],'classification':'clarification_required','finite_projection_records':23262,'frozen_packs':1220,'global_first10_distinct_packs':6,'single_pack_comparison_n':2,'disjoint_single_pack_sets':True,'own_source_membership_rows':3,'two_separate_nonblind_AI_reviews':True,'expert_validation_n':0,'new_admissions':0,'new_model_calls':0,'fresh_private_database_reads':0,'fresh_native_executions':0,'scope_limit':'Portable finite emitted projection and three own register rows; no full physical pack membership, own summary certification, approval, or normative incorporation claim.'}))
