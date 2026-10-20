"""Replay source-positive versus retained-nonnull membership witnesses."""
import sys
if sys.flags.optimize:
    raise SystemExit('Optimized verification is refused.')
import encodings.ascii
import encodings.cp437
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import xml.etree.ElementTree as E
import zipfile

HERE = Path(os.path.abspath(__file__)).parent
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
X = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'


def require(condition, reason):
    if not condition: raise RuntimeError(reason)


def no_symlink(path):
    for part in (path, *path.parents):
        require(not part.is_symlink(), 'Symlink boundary rejected')


def sha(data): return hashlib.sha256(data).hexdigest()
def load(path): return json.loads(path.read_bytes())
def unzip_json(path): return json.loads(gzip.decompress(path.read_bytes()))
def text(element): return ''.join(x.text or '' for x in element.iter(W+'t'))


no_symlink(HERE)
for path in HERE.rglob('*'):
    no_symlink(path)
    require(path.is_file() or path.is_dir(), 'Nonregular entry rejected')
inventory_bytes = (HERE/'inventory.json').read_bytes()
require(sha(inventory_bytes) == 'aa4c06bf9d965f49dfe8d4a5668dae1733b55e8e0ce17da85f728cdf7d3bc0f5', 'Inventory changed')
inventory = json.loads(inventory_bytes)
require({str(p.relative_to(HERE)) for p in HERE.rglob('*') if p.is_file()} == set(inventory)|{'inventory.json','verify_evidence.py'}, 'Closed inventory differs')
for name, expected in inventory.items():
    data = (HERE/name).read_bytes()
    require(len(data)==expected['bytes'] and sha(data)==expected['sha256'], 'Payload differs: '+name)


def audit(event, args):
    if event in {'subprocess.Popen','os.system'} or event.startswith('socket.'):
        raise RuntimeError('External execution/network forbidden')
    if event == 'sqlite3.connect':
        require(args[0] in (':memory:',b':memory:'), 'Only the in-memory diagnostic database is allowed')
    if event == 'open' and isinstance(args[0],(str,bytes,os.PathLike)):
        path = Path(os.fsdecode(args[0])); path = path if path.is_absolute() else Path.cwd()/path
        no_symlink(path)
        require(path.resolve().is_relative_to(HERE), 'Artifact outside package')
        require(args[1] is None or not any(c in str(args[1]) for c in 'wax+'), 'Artifact writes forbidden')


sys.addaudithook(audit)


def pin(path, expected):
    data = path.read_bytes()
    require(len(data)==expected['bytes'] and sha(data)==expected['sha256'], 'Historical binding differs: '+path.name)


def parts(folder, stem, expected):
    trees = []
    for kind in ['document','styles']:
        data = gzip.decompress((folder/(stem+'_'+kind+'.xml.gz')).read_bytes())
        require(sha(data)==expected[kind+'_XML_sha256'], 'Original XML identity differs')
        trees.append(E.fromstring(data))
    return trees


def active(elements, styles):
    style_map = {x.get(W+'styleId'):x for x in styles.findall(W+'style')}
    ids = {k for k,x in style_map.items() if x.get(W+'default') in ('true','1','on')}
    for element in elements:
        for tag in ['pStyle','rStyle','tblStyle']:
            ids.update(x.get(W+'val') for x in element.iter(W+tag))
    closure = set()
    def add(k):
        if k in closure: return
        require(k in style_map, 'Source style unresolved')
        closure.add(k)
        parent = style_map[k].find(W+'basedOn')
        if parent is not None: add(parent.get(W+'val'))
    for sid in ids: add(sid)
    trees = elements+[style_map[k] for k in closure]
    defaults = styles.find(W+'docDefaults')
    if defaults is not None: trees.append(defaults)
    on = lambda e:e.get(W+'val','true').lower() not in ('0','false','off','no')
    require(not any(on(e) for root in trees for flag in ['strike','dstrike','vanish','webHidden'] for e in root.iter(W+flag)), 'Inactive source field')
    require(not any(list(root.iter(W+'del')) or list(root.iter(W+'moveFrom')) for root in elements), 'Deleted source field')


criteria = load(HERE/'criteria.json')
results = []
for wg, qid, tid, qhash, chash in [
    ('RAN2','RAN2_P4_CQ4-5','R2-2509478','28472a2f2a7880ce172ffe900905c9dedb82d49fc1b12f89c0d87c9a5697b5f8','3729caf7ad2494a142eba20fdbcb82457823165a91759c85c71e68f700b6dd4d'),
    ('RAN4','RAN4_P4_CQ4-5','R4-1916202','a546f9a18c4636bde0fb1bf14376701620ce1cb0567fd914be90b2bfaa98a513','4bd3f2e20f49f49c8a41be53fe72744bb4e76d47a1445e0200138ffe41836023')]:
    folder = HERE/wg
    original = load(folder/'original_row.json'); binding = load(folder/'source_binding.json')
    require(original['id']==qid and sha(original['question_en'].encode())==qhash and sha(original['cypher'].encode())==chash, 'Original question/query differs')
    require('IS NOT NULL' in original['cypher'] and 'DESC' in original['cypher'] and 'LIMIT 10' in original['cypher'], 'Concrete counterauthority differs')
    root = load(folder/'ROOT_final_scope_classification.json'); primary = load(folder/'primary_seven_units.json')
    seal = load(folder/'ROOT_final_seal.json')
    pin(folder/'ROOT_final_scope_classification.json', seal['final_packet'])
    pin(folder/'primary_seven_units.json', binding['primary_seven_unit_review'])
    history_bytes = gzip.decompress((folder/'ROOT_historical_source_and_frozen.json.gz').read_bytes())
    require(sha(history_bytes)==root['ROOT_actual_source_replay']['sha256'] and len(history_bytes)==root['ROOT_actual_source_replay']['bytes'], 'ROOT historical replay differs')
    history = json.loads(history_bytes)
    require(root['id']==qid and root['recommendation']=='clarification_required' and root['public_admission'] is False and root['human_expert_validation_n']==0, 'ROOT judgment/attribution differs')
    require(seal['final_local_decision']=='clarification_required' and seal['public_admission'] is False and seal['human_expert_validation_n']==0, 'Completed ROOT seal differs')
    require([r['unit'] for r in root['exact_seven_unit_findings']]==criteria['semantic_units'], 'ROOT seven-unit coverage differs')
    units = primary['semantic_evidence'] if wg=='RAN2' else primary['seven_unit_disposition']
    names = [r['unit'] for r in units] if wg=='RAN2' else [r['role'] for r in units]
    require(names==criteria['semantic_units'] and primary['expert_validation_n']==0, 'Primary seven-unit coverage/attribution differs')
    if wg=='RAN4': require([r['unit'] for r in units]==list(range(1,8)), 'Numbered primary units differ')
    require(primary.get('recommendation',primary.get('local_recommendation'))=='clarification_required', 'Primary judgment differs')
    if wg=='RAN2': pin(folder/'primary_seven_units.json',root['primary_evidence']['seven_unit_judgment'])
    else: pin(folder/'primary_seven_units.json',root['primary_final_packet'])
    doc, styles = parts(folder,'own_CR',binding['source_parts'])
    matches = []
    for ti, table in enumerate(doc.iter(W+'tbl')):
        for ri, row in enumerate(table.findall(W+'tr')):
            cells = row.findall(W+'tc')
            if cells and re.sub('[^a-z]','',text(cells[0]).lower())=='summaryofchange':
                matches.append((ti,ri,row,'\n'.join(text(c) for c in cells[1:]).strip()))
    require(len(matches)==1 and matches[0][3]==binding['summary'] and bool(binding['summary']), 'Own active Summary role/value differs')
    active([matches[0][2]],styles)
    records = [json.loads(line) for line in gzip.decompress((folder/'full_frozen_source_identity_projection.jsonl.gz').read_bytes()).splitlines()]
    own = [r for r in records if json.loads(r['properties_json']).get('tdocNumber')==tid]
    require(len(own)==1 and json.loads(own[0]['properties_json']).get('summaryOfChange') is None, 'Own retained nonnull-policy exclusion differs')
    design = (folder/'original_Phase4_design.md').read_text()
    require('4-5' in design and 'summaryOfChange' in design and '승인' in design, 'Own original design authority missing')
    if wg=='RAN2':
        report_pin = binding['original_sources']['meeting_report']
        report, report_styles = parts(folder,'meeting_report',{'document_XML_sha256':report_pin['XML_sha256'],'styles_XML_sha256':report_pin['styles_sha256']})
        body = list(report.find(W+'body'))
        require(text(body[8418])=='Annex E:List of agreed CRs' and tid in text(body[4821]) and text(body[4822])=='=> Agreed', 'Own documentary approval differs')
        active([body[4821],body[4822]],report_styles)
        agreed = [[text(c) for c in row.findall(W+'tc')] for row in body[8419].findall(W+'tr')]
        ids = [r[0] for r in agreed if r and re.fullmatch(r'R2-\d{7}',r[0])]
        require(len(ids)==len(set(ids))==240 and max(ids)==tid, 'Source-positive necessary cutoff differs')
        values = [{'tdocNumber':json.loads(r['properties_json'])['tdocNumber'],'summary':json.loads(r['properties_json']).get('summaryOfChange')} for r in records]
        require(len(values)==240 and {v['tdocNumber'] for v in values}==set(ids), 'Complete finite source identity projection differs')
        require(sorted(values,key=lambda r:r['tdocNumber'],reverse=True)==history['fresh_approved240'], 'Historical generic projection binding differs')
        c = sqlite3.connect(':memory:');c.execute('CREATE TABLE metadata(tdoc TEXT,summary TEXT)')
        c.executemany('INSERT INTO metadata VALUES(?,?)',[(v['tdocNumber'],v['summary']) for v in values])
        sql = c.execute('SELECT tdoc,summary FROM metadata WHERE summary IS NOT NULL ORDER BY tdoc DESC LIMIT 10').fetchall()
        python = [(v['tdocNumber'],v['summary']) for v in sorted(values,key=lambda r:r['tdocNumber'],reverse=True) if v['summary'] is not None][:10]
        require(sql==python and tid not in {r[0] for r in sql}, 'Conditional retained-field selection differs')
        require(sum(v['summary'] is not None for v in values)==210, 'Conditional known-field population differs')
        c.close(); rank = 1
    else:
        reg = binding['original_sources']['meeting_register']
        workbook = (folder/'original_register.xlsx').read_bytes()
        require(sha(workbook)==reg['member_sha256'], 'Original workbook member differs')
        with zipfile.ZipFile(io.BytesIO(workbook)) as z:
            strings = [''.join(t.text or '' for t in e.iter(X+'t')) for e in E.fromstring(z.read('xl/sharedStrings.xml')).findall(X+'si')]
            sheet = z.read('xl/worksheets/sheet1.xml')
        require(sha(sheet)==reg['sheet_XML_sha256'], 'Original register sheet differs')
        rows = {}; headers = None
        for row in E.fromstring(sheet).iter(X+'row'):
            vals = {}
            for cell in row.findall(X+'c'):
                col = re.match('[A-Z]+',cell.get('r')).group();v=cell.find(X+'v')
                vals[col] = strings[int(v.text)] if cell.get('t')=='s' and v is not None else ''.join(t.text or '' for t in cell.iter(X+'t')) if cell.get('t')=='inlineStr' else v.text if v is not None else ''
            if headers is None: headers=vals;continue
            props = {k:vals.get(col,'') for col,k in headers.items() if k}
            if props.get('TDoc'): rows[props['TDoc']]={'row':int(row.get('r')),'properties':props,'row_XML_ET_sha256':sha(E.tostring(row))}
        require(len(rows)==3112 and rows[tid]==reg['witness_row'], 'Own documentary register role differs')
        require(rows[tid]['properties']['Type']=='CR' and rows[tid]['properties']['TDoc Status']=='agreed', 'Own documentary agreement differs')
        above = [{'tdocNumber':k,'type':r['properties']['Type'],'status':r['properties']['TDoc Status']} for k,r in sorted(rows.items(),reverse=True) if k>tid and r['properties']['Type'] in ['CR','draftCR','pCR'] and r['properties']['TDoc Status'] in ['agreed','approved','endorsed']]
        require(above==reg['all_accepted_CR_family_possible_entrants_above_witness'] and len(above)==7, 'Conservative necessary selection bound differs')
        require(own==history['retained_alternatives']['own_full_record'] and len(records)==1, 'Own frozen metadata binding differs')
        rank = len(above)+1
    require(rank<=10, 'Witness outside original concrete extent')
    results.append({'id':qid,'witness':tid,'source_positive_necessary_rank_upper_bound':rank,'retained_nonnull_excludes_same_witness':True,'classification':'clarification_required'})
print(json.dumps({'status':'PASS','cases':results,'two_separate_nonblind_AI_reviews_per_case':True,'expert_validation_n':0,'new_admissions':0,'new_model_calls':0,'fresh_private_database_reads':0,'fresh_native_executions':0,'scope':'Original XML and finite emitted generic projections; not a full source-positive answer, physical-source completeness, TSG approval or incorporation claim.'}))
