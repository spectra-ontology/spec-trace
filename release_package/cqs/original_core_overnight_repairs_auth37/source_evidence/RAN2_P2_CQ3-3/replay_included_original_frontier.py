"""Offline source/retained-reference replay for the original first-five frontier.

No database, host source fallback, network, subprocess or model is used. XML
members and original register files are included; whole original DOCX archives
and immutable SQL are separately pinned and were checked in the actual audit.
"""
import collections
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

if sys.flags.optimize:
    raise RuntimeError('optimized Python is not supported')
sys.dont_write_bytecode = True
D = Path(__file__).absolute().parent
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
X = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

def require(value, message):
    if not value:
        raise RuntimeError(message)

def regular(path):
    path = Path(path).absolute()
    for item in [path, *path.parents]:
        require(not item.is_symlink(), 'symlink or symlink ancestor')
    require(path.is_file(), 'not a regular file')
    return path

def read(root, entry):
    relative = Path(entry['path'])
    require(not relative.is_absolute() and '..' not in relative.parts, 'nonrelative source input')
    raw = regular(root / relative).read_bytes()
    require(type(entry['bytes']) is int and len(raw) == entry['bytes'], 'source byte count')
    require(hashlib.sha256(raw).hexdigest() == entry['sha256'], 'source input hash')
    return raw

def normalized(text):
    return ''.join(text.split()).replace('\x07', '')

def company_normal(text):
    return re.sub('[^a-z0-9]', '', text.casefold())

def workbook_rows(raw, wanted):
    import io
    import zipfile
    observed = []
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        require(archive.testzip() is None, 'XLSX CRC failure')
        strings = [''.join(node.text or '' for node in entry.iter(X+'t'))
            for entry in ET.fromstring(archive.read('xl/sharedStrings.xml'))] if 'xl/sharedStrings.xml' in archive.namelist() else []
        for member in sorted(name for name in archive.namelist() if re.fullmatch(r'xl/worksheets/sheet[0-9]+\.xml', name)):
            headers = None
            for row in ET.fromstring(archive.read(member)).iter(X+'row'):
                values = {}
                for cell in row:
                    column = re.sub('[0-9]', '', cell.get('r',''))
                    value_node = cell.find(X+'v')
                    value = (value_node.text or '') if value_node is not None else ''
                    if cell.get('t') == 's':
                        value = strings[int(value)] if value else ''
                    elif cell.get('t') == 'inlineStr':
                        value = ''.join(node.text or '' for node in cell.iter(X+'t'))
                    values[column] = value
                if headers is None:
                    if 'TDoc' in values.values():
                        headers = values
                    continue
                named = {headers[col]: value for col,value in values.items() if col in headers}
                if named.get('TDoc','').strip() in wanted:
                    observed.append(named)
    return observed

def replay(root):
    root = Path(root).absolute()
    manifest = json.loads(regular(root/'source_replay_inputs.json').read_text())
    fixture = json.loads(gzip.decompress(read(root, manifest['retained_projection'])))
    audit = json.loads(read(root, manifest['actual_source_audit']))
    resolution = {row['node_id']: row for row in fixture['Resolution']}
    tdocs = {row['tdocNumber']: row['node_id'] for row in fixture['Tdoc_identities']}
    expected = {(row['node_id'], tdocs[tid]) for row in fixture['Resolution']
        for tid in set(re.findall(r'R2-\d{7}', row['content'] or '')) if tid in tdocs}
    actual = {tuple(row) for row in fixture['all_references']}
    require(expected == actual and len(actual) == 12995, 'all retained original literal references differ')
    groups = collections.defaultdict(set)
    for row in fixture['paths']:
        require((row['rn'],row['tn']) in actual, 'path is not a retained original reference')
        groups[row['workItemCode'],row['companyName']].add(row['rn'])
    first = sorted({code for code,company in groups})[:5]
    dependency = [row for row in fixture['paths'] if row['workItemCode'] in first]
    rn = {row['rn'] for row in dependency}
    tn = {row['tn'] for row in dependency}
    require(len(groups) == 1939 and len(dependency) == 358 and len(rn) == 12 and len(tn) == 294,
            'full recorded/selected dependency changed')
    require(audit['first5'] == first and audit['first5_dependency']['role_failure_n'] == 0
            and audit['first5_dependency']['role_failures'] == [], 'source role failure')
    sources = {}
    for entry in manifest['documents']:
        raw = gzip.decompress(read(root, entry['document_xml']))
        styles = gzip.decompress(read(root, entry['styles_xml']))
        require(len(raw) == entry['raw_document_xml']['bytes'] and hashlib.sha256(raw).hexdigest() == entry['raw_document_xml']['sha256'], 'XML original member pin')
        require(len(styles) == entry['raw_styles_xml']['bytes'] and hashlib.sha256(styles).hexdigest() == entry['raw_styles_xml']['sha256'], 'styles original member pin')
        blocks = list(ET.fromstring(raw).find(W+'body'))
        texts = [''.join((node.text or '') if node.tag == W+'t' else '\t' if node.tag == W+'tab' else '\n'
            for node in block.iter() if node.tag in (W+'t',W+'tab',W+'br',W+'cr')) for block in blocks]
        sources[entry['original_archive']['path']] = (blocks, texts)
    cases = audit['first5_dependency']['full_content_source_cases']
    require({row['resolution_node'] for row in cases} == rn, 'source cases do not cover complete dependency')
    for case in cases:
        blocks,texts = sources[case['source_archive']['path']]
        content = resolution[case['resolution_node']]['content']
        require(hashlib.sha256(content.encode()).hexdigest() == case['retained_content_sha256'], 'retained content identity')
        needle = normalized(content)
        for start,end in case['raw_body_children_fullcontent_matches']:
            require(needle in normalized('\n'.join(texts[start:end])), 'entire retained content does not match original')
            require(end <= case['first_Annex_body_child'], 'source dependency enters Annex')
        annex = []
        for index,block in enumerate(blocks):
            style = block.find(W+'pPr/'+W+'pStyle')
            style_id = style.get(W+'val','') if style is not None else ''
            if re.match(r'^Annex\s+[A-G]\s*:', texts[index].strip(), re.I) and 'toc' not in style_id.lower():
                annex.append(index)
        require(annex and annex[0] == case['first_Annex_body_child'], 'original Annex position changed')
    role_rows = audit['first5_dependency']['all_Tdoc_roles']
    require({row['node_id'] for row in role_rows} == tn, 'Tdoc role coverage differs')
    wanted = {row['tdocNumber'] for row in role_rows}
    observed = collections.defaultdict(list)
    for entry in manifest['workbooks']:
        for row in workbook_rows(read(root, entry['included']), wanted):
            observed[row['TDoc'].strip()].append(row)
    for role in role_rows:
        supported = False
        for row in observed[role['tdocNumber']]:
            names = {company_normal(re.sub(r'\s*\((?:Rapporteur|Moderator|Rapporteurs)\)\s*$','',name,flags=re.I))
                     for name in row.get('Source','').split(',')}
            company_ok = []
            for company in role['recorded_companies']:
                aliases = company['aliases'] or company['companyName']
                aliases = json.loads(aliases) if aliases.lstrip().startswith('[') else [aliases]
                company_ok.append(any(company_normal(name) in names for name in [company['companyName'],*aliases]))
            wi_names = {value.strip() for value in row.get('Related WIs','').split(',')}
            wi_ok = all(wi['workItemCode'] in wi_names for wi in role['recorded_WIs'])
            supported |= all(company_ok) and wi_ok
        require(supported and role['source_role_supported'] is True, 'original Tdoc-column/company/WI role failed')
    return {'status':'PASS_INCLUDED_ORIGINAL_FRONTIER_REPLAY', 'Resolution_loaded':len(resolution),
        'retained_literal_references':len(actual), 'full_path_records':len(fixture['paths']),
        'WI_company_groups':len(groups),'first5':first,'full_source_contents':len(cases),
        'full_dependency_paths':len(dependency),'original_Tdoc_roles':len(role_rows),
        'original_XLSX':len(manifest['workbooks']),'original_XML_documents':len(manifest['documents']),
        'source_role_failures':0,'source_all3773_raw_body_claimed':False,
        'native_gold_replayed':False,'historical_generator_binding_claimed':False,
        'original_query_preserved':True,'API_calls':0,'native_calls':0,'database_calls':0}

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputs',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(replay(args.inputs),ensure_ascii=False))
