"""Offline, byte-pinned bounded diagnostics; no native/API/host-source fallback."""
import argparse,gzip,hashlib,importlib.util,json,re,sys,zipfile
from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree as ET

INVENTORY_SHA256 = 'ebcff3ff9f328f9c0074db5865303e293f005e122269c3ae98222305abc6b835'
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'

def sha(b): return hashlib.sha256(b).hexdigest()
def regular_nosymlink(path):
    path=Path(path).absolute()
    for p in [path,*path.parents]:
        assert not p.is_symlink(),f'Symlink not allowed: {p.name}'
    assert path.is_file(),f'Missing regular file: {path.name}'
    return path

def main():
    if sys.flags.optimize != 0:
        raise RuntimeError('Optimized Python disables diagnostic assertions and is refused')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-docx-123')
    parser.add_argument('--source-docx-117')
    args=parser.parse_args()
    here=regular_nosymlink(Path(__file__)).parent
    def read(name):
        p=here/name
        assert '..' not in Path(name).parts and not Path(name).is_absolute()
        return regular_nosymlink(p).read_bytes()
    inv_raw=read('immutable_inventory.json')
    assert sha(inv_raw)==INVENTORY_SHA256,'Immutable inventory mismatch'
    inv=json.loads(inv_raw);assert inv['schema']=='bounded-diagnostic-payload-v1'
    names=set()
    for pin in inv['files']:
        name=pin['path'];assert name not in names;names.add(name)
        raw=read(name);assert len(raw)==pin['bytes'] and sha(raw)==pin['sha256'],f'Payload mismatch: {name}'
    allowed=names|{'manifest.json','immutable_inventory.json','verify_diagnostics.py'}
    actual=set()
    for p in here.rglob('*'):
        assert not p.is_symlink(),'Symlinks forbidden'
        if p.is_file():actual.add(p.relative_to(here).as_posix())
    assert actual==allowed,'Closed package file inventory mismatch'
    manifest=json.loads(read('manifest.json'))
    assert manifest=={'schema':'bounded-diagnostic-manifest-v1','status':'BOUNDED_SOURCE_DIAGNOSTIC_PROPOSAL_NOT_ADMISSION','id':'RAN1_P2_CQ5-4','original560_pass_increment':0,'human_expert_n':0,'immutable_inventory_sha256':INVENTORY_SHA256,'payload_files':len(names),'verifier_sha256':sha(read('verify_diagnostics.py'))},'Scientific declaration or verifier self-hash mismatch'
    provenance=json.loads(read('provenance.json'))
    assert provenance['original560_pass_increment']==0 and provenance['human_expert_n']==0
    expected=json.loads(read('expected_results.json'))
    assert expected['original560_pass_increment']==0 and expected['human_expert_n']==0
    # All local modules were already checked against the fixed closed inventory.
    def load(name,filename):
        p=here/'code'/filename;spec=importlib.util.spec_from_file_location(name,p)
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
        return module
    helper=load('docx_text','docx_text_helpers_extracted.py')
    helper_provenance=json.loads(read('code/helper_extraction_provenance.json'))
    assert sha(read('code/docx_text_helpers_extracted.py'))==helper_provenance['included_helper_sha256']
    for n in ['symbol_fonts','glyph_width','metafile_text','ole_cfb','mtef','mtef_linear','preview_math']:
        load(n,n+'.py')
    original=sys.modules['mtef_linear'];patch=load('prospective_renderer','prospective_mtef_linear_empty_script.py')
    cfb=sys.modules['ole_cfb'];mtef=sys.modules['mtef'];preview=sys.modules['preview_math']
    objects=json.loads(gzip.decompress(read('source/93_objects_expected_differential_measurements.json.gz')))
    member_inventory=json.loads(read('source/member_inventory.json'))
    assert len(objects)==93 and len(member_inventory)==157
    from io import BytesIO
    members={}
    with zipfile.ZipFile(BytesIO(read('source/bounded93_original_members.zip'))) as z:
        assert len(z.namelist())==len(set(z.namelist()))==157
        assert set(z.namelist())=={p['path']for p in member_inventory}
        for pin in member_inventory:
            raw=z.read(pin['path']);assert len(raw)==pin['bytes'] and sha(raw)==pin['sha256'];members[pin['path']]=raw
    before_exact=after_exact=before_ws=after_ws=changed=empty_objects=0
    changed_ids=[]
    for obj in objects:
        raw=members[obj['member']];assert sha(raw)==obj['member_sha256']
        stream=cfb.streams(raw)['Equation Native'];assert sha(stream)==obj['EquationNative_sha256']
        eqn=mtef.Eqn(stream);assert eqn.tail==obj['MTEF_tail']==0 and eqn.version==obj['MTEF_version']
        before,bu=original.linear(eqn);after,au=patch.linear(eqn)
        assert before==obj['before_native_text'] and after==obj['after_prospective_text']
        assert bu==obj['before_unknown']==au==obj['after_unknown']==[]
        # Empty-template object classification is derived from the parsed AST.
        def walk(ns):
            for n in ns or []:
                yield n
                if n[0] in {'line','pile'}:yield from walk(n[1])
                elif n[0] in {'tmpl','matrix'}:yield from walk(n[3])
        renderer=original.Render(eqn)
        empty=False
        for n in walk(eqn.body):
            if n[0]=='tmpl':
                scr=renderer.script(n)
                if scr is not None and not scr[0] and not scr[1]:empty=True
        empty_objects+=empty
        if before!=after:changed+=1;changed_ids.append(obj['ObjectID'])
        b_exact=a_exact=b_ws=a_ws=False
        for old in obj['previews']:
            rawp=members[old['member']];assert sha(rawp)==old['sha256'];notes=[];ptext=preview.read(rawp,notes)
            assert ptext==old['text'] and notes==old['notes']
            b_exact|=before==ptext;a_exact|=after==ptext
            b_ws|=re.sub(r'\s','',before)==re.sub(r'\s','',ptext)
            a_ws|=re.sub(r'\s','',after)==re.sub(r'\s','',ptext)
        before_exact+=b_exact;after_exact+=a_exact;before_ws+=b_ws;after_ws+=a_ws
    assert changed_ids==['_1831739946']
    assert (changed,93-changed,empty_objects,before_exact,after_exact,before_ws,after_ws)==(1,92,1,90,90,92,93)
    controls=json.loads(read('source/five_AST_controls.json'))
    assert len(controls)==5
    for c in controls:
        e=SimpleNamespace(version=3,body=c['AST'])
        b,bu=original.linear(e);a,au=patch.linear(e)
        assert b==c['expected_before'] and a==c['expected_after'] and bu==au==[]
    # Counterexample to using a candidate predicate as an automatic cut.
    contexts=json.loads(gzip.decompress(read('source/six_boundary_contexts_full_XML.json.gz')))
    assert len(contexts)==6
    lookup={r['candidate_inventory_row']['resolutionId']:r for r in contexts}
    parsed={}
    literal=lambda e:''.join(n.text or ''for n in e.iter()if n.tag in {W+'t',M+'t'})
    for rid,row in lookup.items():
        blocks={}
        for b in row['full_original_broad_window_blocks']:
            raw=b['raw_XML'].encode();assert sha(raw)==b['XML_sha256'];xml=ET.fromstring(raw);assert literal(xml)==b['literal'];blocks[b['raw_body_child0']]=(xml,b['literal'])
        parsed[rid]=blocks
    own=parsed['AGR-117-8.1-005'];i=873
    assert not own[i-1][1].strip()
    xml,value=own[i]
    assert re.match(r'^\s*R\d+[A-Z]?-\d{6,8}(?:\b|(?=[A-Z]))',value)
    assert len(list(xml.iter(W+'tab')))>=2
    nxt=next(k for k in sorted(own)if k>i and own[k][1].strip())
    prev=next(k for k in sorted(own,reverse=True)if k<i and own[k][1].strip())
    approval=re.compile(r'\b(?:is|are)\s+(?:agreed|approved|endorsed)\b',re.I)
    assert not approval.search(value) and not approval.search(own[nxt][1])
    assert not re.search(r'\bFinal\s+CRs?\b',own[prev][1],re.I)
    assert own[874][1]=='Final CR in:' and 'is agreed.'in own[878][1]
    assert 'Correction on PT-RS Coherence Conditions for 8 Tx'in own[873][1] and 'Correction on PT-RS Coherence Conditions for 8 Tx'in own[877][1]
    # Five detection checks are source-observation consistency checks, not a
    # claim that every flagged paragraph is foreign or safe to remove.
    for rid,k in [('AGR-123-7-002',384),('AGR-123-8.5-004',924),('AGR-123-8.5-010',979),('AGR-123-8.7.1-002',1153),('AGR-123-9.2-015',1608)]:
        row=lookup[rid]['candidate_inventory_row'];assert any(c['raw_body_child0']==k for c in row['boundary_candidates'])
    # Optional source equality replay never guesses a local fallback path.
    optional=[]
    for meeting,arg in [('RAN1#123',args.source_docx_123),('RAN1#117',args.source_docx_117)]:
        if arg is None:continue
        pin=next(p for p in provenance['source_registry']if p['meeting']==meeting)
        path=regular_nosymlink(Path(arg));raw=path.read_bytes();assert sha(raw)==pin['member_sha256'],'Optional DOCX hash mismatch'
        with zipfile.ZipFile(BytesIO(raw)) as z:
            full=z.read('word/document.xml');assert sha(full)==pin['XML_sha256'];body=list(ET.fromstring(full).find(W+'body'))
            for row in contexts:
                if row['candidate_inventory_row']['meeting']!=meeting:continue
                for b in row['full_original_broad_window_blocks']:
                    assert sha(ET.tostring(body[b['raw_body_child0']],encoding='utf-8'))==b['XML_sha256']
            if meeting=='RAN1#123':
                for name,data in members.items():assert z.read(name)==data
        optional.append(meeting)
    result={'status':'PASS_BOUNDED_DIAGNOSTIC_NOT_ADMISSION','objects_reparsed_from_included_original_CFB':93,'unique_original_CFB_WMF_members':157,'actual_changed_objects':1,'unchanged_objects':92,'preview_whitespace_ignored_agreement_before_after':[92,93],'preview_exact_string_agreement_before_after':[90,90],'AST_controls_passed':5,'own_FinalCR_false_cut_reproduced':True,'optional_full_source_DOCX_equality':optional,'full3176_scan_recomputed':False,'formula_semantic_fidelity_certified':False,'DCI_admitted':False,'original560_pass_increment':0,'human_expert_n':0}
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=='__main__':main()
