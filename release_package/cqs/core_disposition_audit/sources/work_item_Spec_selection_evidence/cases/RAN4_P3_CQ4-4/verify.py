"""Reproduce a bounded original WI-to-Spec selection-rule diagnostic.

No answer gold, query admission, API evaluation, or new source classifier is made.
"""
import collections
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode=True
if sys.flags.optimize:raise SystemExit('Verification requires enabled checks; -O/-OO refused.')
HERE=Path(os.path.abspath(__file__)).parent
INVENTORY_SHA256='40a172444c824fd1ad74cfde9208dafabf5a92c2ca55d331c261cab274480169'
SECONDARY_REQUIRED=True
S={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def require(b,msg):
    if not b:raise ValueError(msg)
def sha(b):return hashlib.sha256(b).hexdigest()
def unique(pairs):
    d={}
    for k,v in pairs:
        require(k not in d,'duplicate JSON key');d[k]=v
    return d
def parse(b):return json.loads(b,object_pairs_hook=unique,parse_constant=lambda s:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def safe(path):
    p=Path(os.path.abspath(path))
    for x in (p,*p.parents):require(not x.is_symlink(),'symlink forbidden')
    if p.exists():require(stat.S_ISREG(p.lstat().st_mode) or stat.S_ISDIR(p.lstat().st_mode),'nonregular entry forbidden')
    return p
def read(n):return safe(HERE/n).read_bytes()
def load(n):
    b=read(n);return parse(gzip.decompress(b) if n.endswith('.gz') else b)
def audit():
    counts={'packet_read_opens':0,'stdlib_read_opens':0,'host_private_open_attempts':0,'write_open_attempts':0,'network_calls':0,'subprocess_calls':0,'SQL_calls':0}
    stdlib=Path(os.__file__).resolve().parent
    def hook(event,args):
        if event.startswith(('socket.','http.client.','urllib.')):
            counts['network_calls']+=1;raise RuntimeError('Network forbidden')
        if event in {'subprocess.Popen','os.system','os.posix_spawn','os.posix_spawnp','os.fork','os.exec','os.spawn'}:
            counts['subprocess_calls']+=1;raise RuntimeError('Subprocess forbidden')
        if event.startswith('sqlite3.'):
            counts['SQL_calls']+=1;raise RuntimeError('SQL forbidden')
        if event=='open':
            p,mode,flags=args
            if isinstance(p,int):
                counts['host_private_open_attempts']+=1;raise RuntimeError('Descriptor open forbidden')
            if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_APPEND|os.O_TRUNC)):
                counts['write_open_attempts']+=1;raise RuntimeError('Writes forbidden')
            target=Path(os.path.abspath(os.fsdecode(p)))
            if target.is_relative_to(HERE):safe(target);counts['packet_read_opens']+=1
            elif target.is_relative_to(stdlib):counts['stdlib_read_opens']+=1
            else:
                counts['host_private_open_attempts']+=1;raise RuntimeError('Host-private open forbidden')
    sys.addaudithook(hook);return counts

def inventory():
    invbytes=read('immutable_inventory.json');require(sha(invbytes)==INVENTORY_SHA256,'inventory pin')
    inv=parse(invbytes);files=set();dirs=set()
    for p in HERE.rglob('*'):
        safe(p)
        if p.is_file():files.add(p.relative_to(HERE).as_posix())
        elif p.is_dir():dirs.add(p.relative_to(HERE).as_posix())
        else:raise ValueError('nonregular inventory entry')
    require(files==set(inv['files'])|{'immutable_inventory.json','manifest.json','verify.py'},'closed file inventory')
    expected_dirs={p.as_posix() for n in files for p in Path(n).parents if p.as_posix()!='.'}
    require(dirs==expected_dirs,'closed directory inventory')
    for n,pin in inv['files'].items():
        b=read(n);require(len(b)==pin['bytes'] and sha(b)==pin['sha256'],'scientific payload pin '+n)
    mb=read('manifest.json');m=parse(mb)
    require(mb==(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode(),'canonical manifest bytes')
    require(set(m)=={'inventory_sha256','files','verify_sha256','fixed_metadata'},'manifest schema')
    require(m['inventory_sha256']==INVENTORY_SHA256 and m['files']==inv['files'],'manifest inventory exact')
    require(m['verify_sha256']==sha(read('verify.py')),'verifier self pin')
    require(m['fixed_metadata']=={'id':'RAN4_P3_CQ4-4','recommendation':'clarification_required','new_admissions':0,'API_calls':0,'native_calls':0,'secondary_required':SECONDARY_REQUIRED,'complete79_body_boundary_certification':False,'current_INDEX_is_frozen_generator':False},'metadata exact')
    return len(files)

def xlsx(data):
    out=[]
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        ss=[''.join(x.itertext()) for x in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',S)] if 'xl/sharedStrings.xml' in z.namelist() else []
        for member in z.namelist():
            if not re.fullmatch(r'xl/worksheets/sheet\d+\.xml',member):continue
            hdr=None
            for row in ET.fromstring(z.read(member)).findall('.//s:row',S):
                vals={}
                for c in row.findall('s:c',S):
                    v=c.find('s:v',S);v=v.text if v is not None else ''
                    if c.get('t')=='s':v=ss[int(v)]
                    elif c.get('t')=='inlineStr':v=''.join(c.find('s:is',S).itertext())
                    vals[re.sub(r'\d','',c.get('r'))]=v
                if hdr is None and 'TDoc' in vals.values():hdr=vals;continue
                if hdr is None:continue
                out.append({'sheet':member,'row1':int(row.get('r')),'fields':{hdr.get(k,k):v for k,v in vals.items()},'row_xml_sha256_ET_UTF8':sha(ET.tostring(row,encoding='utf-8'))})
    return out

def main():
    safe(HERE);counts=audit();nfiles=inventory()
    criteria=load('contract/criteria.json');require(sha(read('contract/criteria.json'))=='bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4','fixed seven criteria')
    original=load('contract/original.json');a=load('contract/minimum_contract_and_counterauthority.json');primary=load('contract/primary_review.json')
    require(original['id']=='RAN4_P3_CQ4-4','question identity')
    require(sha(original['question_en'].encode())=='6b3b0679cf3334e8aa0bef7733258fcc2e05ea97248338688d73d0a5b1b132f2','unchanged English')
    require(sha(original['cypher'].encode())=='a81576558564f0a7d979077cf3c46769fbb95bcc80e4003b0df4a406e1b62424','unchanged query')
    require(primary['question_en']==original['question_en'] and primary['question_sha256']==sha(original['question_en'].encode()) and primary['original_query_sha256']==sha(original['cypher'].encode()),'primary original pins')
    require(primary['recommendation']=='clarification_required' and primary['ROOT_seal'] is False and primary['new_admissions']==0,'no primary admission')
    require([x['unit'] for x in primary['semantic_units']]==criteria['semantic_units'],'primary exact7')
    require(all(x['original_quote'] in original['question_en'] and x['judgment'] and x['query_clauses'] for x in primary['semantic_units']),'primary evidence seven')
    if SECONDARY_REQUIRED:
        sec=load('contract/secondary_review.json')
        require(sec['id']==original['id'] and sec['recommendation']=='clarification_required','secondary independent judgment')
        require(sec['question_sha256']==sha(original['question_en'].encode()) and sec['original_query_sha256']==sha(original['cypher'].encode()),'secondary original pins')
        require(sec['criteria']['sha256']==sha(read('contract/criteria.json')),'secondary criteria')
        require([x['unit'] for x in sec['semantic_units']]==criteria['semantic_units'],'secondary exact7')
        require(all(x['original_quote'] in original['question_en'] and x['judgment'] and x['query_clauses'] for x in sec['semantic_units']),'secondary original seven-unit evidence')
        require(sec['reviewer']!=primary['reviewer'] and sec['nonblind_AI'] is True and sec['human_expert_n']==0 and sec['independent_AI_reviewers_including_primary_n']==2,'distinct nonblind AI reviews, human0')
        require(sec['primary_review']['sha256']==sha(read('contract/primary_review.json')),'secondary binds exact primary')
    p3=read('authority/phase3_original_preserved.md');p2=read('authority/phase2_original_preserved.md');p1=read('authority/phase1_original_preserved.md')
    require(sha(p3)=='87c7d2293d03e7b872fbf588cc87b30413030e146ba7a1f63d4fdf9d494442a1','preserved P3')
    require(sha(p2)=='2aa9abf53a42c7dc1203f4109b8ba0162920bc2980ffadcadfcf1251daa129b1','preserved P2')
    for ex in a['preserved_source_contexts']:
        source={sha(p3):p3,sha(p2):p2,sha(p1):p1}[ex['source']['sha256']].decode().splitlines()
        lines=source[ex['start_line1']-1:ex['end_line1']]
        require(lines==[x['literal'] for x in ex['lines']],'exact original context lines')
        require(sha('\n'.join(lines).encode())==ex['exact_excerpt_utf8_sha256'],'original excerpt digest')
    ls=p3.decode().splitlines()
    require('Meeting 번호 DESC | Resolution ID ASC' in ls[219] and 'Count DESC | TS 번호 ASC' in ls[220] and '목록 조회 | 10' in ls[226],'original different CQ4/CQ5 defaults and limit')
    require('ORDER BY rCount DESC, sp.specNumber LIMIT 10' in original['cypher'],'authored count query counterauthority')
    obs=load('source/current_INDEX_observation.json');require(obs['historical_binding']['current_INDEX_is_proven_frozen_RDF_generator'] is False and obs['historical_binding']['RAN2_boundary_authority_transferred'] is False,'currentINDEX separated from historical authority')
    require(sha(read('source/current_INDEX_RAN4_decision_extractor.py.txt'))==obs['current_INDEX_bytes']['sha256'],'separate currentINDEX bytes')
    projection=load('frozen/projection.json.gz');paths=projection['raw_paths'];rs={x['node_id']:x for x in projection['resolutions']};cr={x['node_id']:x for x in projection['CRs']}
    require(len(paths)==818 and len(rs)==79 and len(cr)==809,'finite frozen dependency sizes')
    require(len({(x['related_edge'],x['reference_edge'],x['modifies_edge']) for x in paths})==818,'raw edge path multiplicity')
    require(all(type(x['specNumber']) is str and x['specNumber'] and type(x['resolution_node']) is int for x in paths),'typed identity/node roles')
    require(all(x['workItemCode']=='NR_newRAT-Perf' and x['tdocNumber']==cr[x['cr_node']]['tdocNumber'] for x in paths),'literal WI and typed CR links')
    for x in paths:require(x['tdocNumber'] in set(re.findall(r'R4-\d{7}(?!\d)',rs[x['resolution_node']]['content'])),'frozen content reference literal')
    grouped=collections.defaultdict(set)
    for x in paths:grouped[x['specNumber']].add(x['resolution_node'])
    rank=sorted([{'specNumber':s,'rCount':len(v)} for s,v in grouped.items()],key=lambda x:(-x['rCount'],x['specNumber']))
    diag=load('frozen/authority_alternatives.json');domains=diag['domain_alternatives'];require(rank==domains['authored_count_retained_domain']['all_groups'],'all14 grouped counts replay')
    explicit=projection['explicit28'];require(len(explicit)==len(set(explicit))==28,'original explicit28 domain')
    require('38.101-1~5' in ls[80] and '**28 spec**' in ls[80] and '38.1xx' in ls[240],'original scope counterauthority')
    for k,rr in [('same_authored_count_explicit28',[x for x in rank if x['specNumber'] in explicit]),('same_authored_count_literal_38_1xx',[x for x in rank if x['specNumber'].startswith('38.1') and x['specNumber']!='38.173'])]:
        require(rr==domains[k]['all_groups'] and rr[:10]==domains[k]['limited10'],'finite scope diagnostic')
    require([len(domains[k]['all_groups']) for k in ['authored_count_retained_domain','same_authored_count_explicit28','same_authored_count_literal_38_1xx']]==[14,8,8],'actual diagnostic domain sizes')
    for k,v in domains.items():require(v['limited_identity_set']==sorted(x['specNumber'] for x in v['limited10']),'logical identity projection')
    # Reopen ALL11 original ZIP-contained named registers; source binding is not a body-boundary claim.
    books={}
    for source in load('source/register_archives.json'):
        raw=read(source['portable_file']);require(sha(raw)==source['archive']['sha256'] and len(raw)==source['archive']['bytes'],'original report ZIP')
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            data=z.read(source['register_member']);require(sha(data)==source['register_sha256'],'original embedded register')
        books[source['meeting']]=xlsx(data)
    bindings=load('source/809_named_register_bindings.json');require(len(bindings)==809 and len(books)==11 and {x['cr_node'] for x in bindings}==set(cr),'all809/11 source sizes and complete CR domain')
    for b in bindings:
        actual=[x for x in books[b['meeting']] if x['fields'].get('TDoc')==b['tdocNumber']]
        require(actual==b['source_rows'] and actual,'original named rows exact')
        specs={x['specNumber'] for x in paths if x['cr_node']==b['cr_node']}
        require({x['fields'].get('Spec') for x in actual}==specs==set(b['graph_specs']),'all809 source Spec equals frozen graph')
        require(all('NR_newRAT-Perf' in [x.strip() for x in row['fields'].get('Related WIs','').split(',')] for row in actual),'all809 exact WI token')
        require(all(row['fields'].get('Type')==cr[b['cr_node']]['type'] and row['fields'].get('Type') in {'CR','draftCR','pCR'} for row in actual),'all809 original class exact')
    # The witness-order examples are intentionally NOT two answer golds or a lifted Spec order.
    made=projection['resolution_made_at'];key=lambda x:(-made[str(x['resolution_node'])][0]['meetingNumberInt'],x['resolutionId'])
    ordered=sorted(paths,key=key);tie=[x for x in ordered if key(x)==key(ordered[0])];td=diag['original_CQ4_default_first_witness_tie']
    require(len(tie)==td['paths_n']==37,'source default actual first witness tie')
    require(td['Spec_set']==sorted({x['specNumber'] for x in tie}),'witness tie projection')
    lookup={(x['related_edge'],x['reference_edge'],x['modifies_edge']):x for x in tie}
    for ex in td['legal_tied_examples']:
        require(len(ex['witness_rows'])==10 and ex['source_authorized_tie_break'] is False,'diagnostic witness example scope')
        for row in ex['witness_rows']:require((row['related_edge'],row['reference_edge'],row['modifies_edge']) in lookup and key(row)==key(tie[0]),'legal original default witness tie')
        require(ex['projected_Spec_identity_set']==sorted({x['specNumber'] for x in ex['witness_rows']}),'diagnostic projection')
    require(td['legal_tied_examples'][0]['projected_Spec_identity_set']!=td['legal_tied_examples'][1]['projected_Spec_identity_set'],'witness keys alone not unique grouped membership')
    require(all(counts[k]==0 for k in ['host_private_open_attempts','write_open_attempts','network_calls','subprocess_calls','SQL_calls']),'no-host replay')
    print(json.dumps({'status':'PASS','id':original['id'],'recommendation':'clarification_required','reviewers_in_packet':2 if SECONDARY_REQUIRED else 1,'ROOT_seal':False,'files':nfiles,'raw_paths':818,'Resolution_nodes':79,'CRs':809,'recorded_Spec_groups':14,'newTS_scope_groups':8,'reopened_original_registers':11,'all809_source_metadata':True,'all818_frozen_content_reference_literals':True,'complete79_body_boundary_certification':False,'new_admissions':0,'API_calls':0,'native_calls':0,'no_host_audit':counts},ensure_ascii=False))
if __name__=='__main__':main()
