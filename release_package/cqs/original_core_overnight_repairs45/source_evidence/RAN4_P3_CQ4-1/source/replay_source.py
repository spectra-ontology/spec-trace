"""Replay exact cropped report/register source roles with the full frozen frontier."""
import sys
if sys.flags.optimize:
    raise SystemExit('Run with assertions enabled; -O/-OO refused')
from pathlib import Path
import collections,gzip,hashlib,json,re
import xml.etree.ElementTree as E
EXPECTED_PAYLOAD = {'frozen_dependency_projection.json.gz': {'bytes': 62173, 'sha256': '60b115e7085f101be7ee430f8baa9c65bf3b8f541ff110f0674928971d3d9b3b'}, 'original_register_role_fragments.json.gz': {'bytes': 3089, 'sha256': '514b3a6d3852a90410d71ab956b057fef7df38400c79e78671fe10e810802c56'}, 'original_report_fragments.json.gz': {'bytes': 20396, 'sha256': '69c190fd5b4f2601cc7334f8923d74c7f5bf441fe0f2338b11d056030f1f7aa3'}, 'source_manifest.json': {'bytes': 2619, 'sha256': '3b0948c31d2afd2913dc2f86d066a6e791277af6d40b10a479c5f3a405f7f6a4'}}
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
S='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

def digest(b):return hashlib.sha256(b).hexdigest()
def norm(t):return re.sub(r'\s+',' ',t).strip()
def text(e):
    return ''.join((x.text or '')if x.tag==W+'t'else'\t'if x.tag==W+'tab'else'\n'if x.tag in {W+'br',W+'cr'}else''for x in e.iter())
def flags(e):
    out=[]
    for x in e.iter():
        n=x.tag.rsplit('}',1)[-1]
        if n in {'del','delText','moveFrom'}:out.append(n)
        if n in {'strike','dstrike','vanish','webHidden'}and x.get(W+'val','1').lower()not in {'0','false','off','no'}:out.append(n)
    return out

def main():
    root=Path(__file__).absolute().parent
    for p in [root,*root.parents,Path(__file__).absolute()]:assert not p.is_symlink(),'Symlink boundary'
    expected_names=set(EXPECTED_PAYLOAD)|{'replay_source.py','inventory.json'}
    assert set(p.name for p in root.iterdir())==expected_names
    for p in root.iterdir():assert not p.is_symlink()and p.is_file(),'Only regular files accepted'
    for rel,pin in EXPECTED_PAYLOAD.items():
        b=(root/rel).read_bytes();assert len(b)==pin['bytes']and digest(b)==pin['sha256'],rel
    inventory=json.loads((root/'inventory.json').read_text())
    actual=[{'path':p.name,'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())}for p in sorted(root.iterdir())if p.name!='inventory.json']
    assert inventory=={'files':actual}
    load=lambda n:json.loads(gzip.decompress((root/n).read_bytes()))
    manifest=json.loads((root/'source_manifest.json').read_text())
    assert manifest['id']=='RAN4_P3_CQ4-1'and manifest['native_calls']==0 and type(manifest['native_calls'])is int
    f=load('frozen_dependency_projection.json.gz');report=load('original_report_fragments.json.gz');regs=load('original_register_role_fragments.json.gz')
    paths=f['paths'];crs={r['node_id']:r for r in f['CR_properties']}
    assert len(paths)==1766 and len(crs)==1733 and len(f['Resolution_identities'])==216
    assert len({(r['reference_edge'],r['modifies_edge'])for r in paths})==len(paths)
    for p in paths:
        assert p['tdocNumber']==crs[p['cr_node']]['tdocNumber']and p['specNumber']=='38.133'
    eligible=[p for p in paths if(crs[p['cr_node']]['status']or'').strip().lower()in {'agreed','approved','endorsed'}]
    pairs=[(p['resolutionId'],p['tdocNumber'])for p in eligible]
    assert len(pairs)==len(set(pairs))==635
    top=max(p['resolutionId']for p in paths)
    alltop=[p for p in paths if p['resolutionId']==top];positive=[p for p in eligible if p['resolutionId']==top]
    assert len(alltop)==28 and len(positive)==18
    r=report['recorded_resolution'];assert r['resolutionId']==top
    pp=report['paragraphs'];lo,hi=report['retained_content_range'];a,b=report['source_context_range']
    assert [p['paragraph_index']for p in pp]==list(range(a,b))and len(pp)==359
    decoded={}
    for p in pp:
        e=E.fromstring(p['xml']);assert text(e)==p['text']and flags(e)==[]and p['deleted_ancestors']==[]
        decoded[p['paragraph_index']]=p['text']
    assert flags(E.fromstring(report['styles_xml']))==[]
    assert digest(report['styles_xml'].encode())==report['styles_xml_sha256']
    assert norm('\n'.join(decoded[i]for i in range(lo,hi)))==norm(r['content'])
    assert decoded[a].startswith('4.9.7\t')and decoded[hi].startswith('4.9.8\t')
    head=list(re.finditer(r'^(R4-[0-9]{7})\t',r['content'],re.M));current=set()
    for i,h in enumerate(head):
        block=r['content'][h.start():head[i+1].start()if i+1<len(head)else len(r['content'])]
        if re.search(r'^Decision:[ \t]*The document was (agreed|approved|endorsed)\.?[ \t]*$',block,re.I|re.M):current.add(h.group(1))
    current&={p['tdocNumber']for p in alltop}
    assert len(current)==14
    fields=['TDoc','Title','Type','For','TDoc Status','Spec']
    assert regs['retained_columns']==fields
    verified={}
    for reg in regs['registers']:
        strings={v['index']:''.join(t.text or ''for t in E.fromstring(v['xml']).iter(S+'t'))for v in reg['used_shared_strings']}
        used=set()
        def val(c):
            v=c.find(S+'v')
            if c.get('t')=='s':
                idx=int(v.text);used.add(idx);return strings[idx]
            if c.get('t')=='inlineStr':return ''.join(t.text or ''for t in c.iter(S+'t'))
            return v.text if v is not None else ''
        hh=E.fromstring(reg['header_xml_selected_cells'])
        columns={re.sub('[0-9]','',c.get('r')):val(c)for c in hh.findall(S+'c')}
        assert set(columns.values())==set(fields)
        for row in reg['rows']:
            e=E.fromstring(row['xml_selected_cells']);assert int(e.get('r'))==row['row']
            vals={columns[re.sub('[0-9]','',c.get('r'))]:val(c)for c in e.findall(S+'c')}
            assert vals==row['values']and set(vals)==set(fields)
            cr=crs[row['frozen_node_id']];tdoc=vals['TDoc'];assert tdoc not in verified
            assert all(vals[k]==cr[v]for k,v in [('TDoc','tdocNumber'),('Title','title'),('Type','type'),('For','for'),('TDoc Status','status')])
            assert vals['Spec']=='38.133';verified[tdoc]=vals
        assert used==set(strings),'Only actually used shared strings retained'
    assert set(verified)=={p['tdocNumber']for p in alltop}
    positive_ids={p['tdocNumber']for p in positive}
    assert {k for k,v in verified.items()if v['TDoc Status'].strip().lower()in {'agreed','approved','endorsed'}}==positive_ids
    past=positive_ids-current;assert len(past)==4
    for ident in past:
        assert verified[ident]['TDoc Status']=='endorsed'
        assert any(ident in decoded[i]and'endorsed'in decoded[i].lower()for i in range(lo,hi))
    assert len(set(verified)-positive_ids)==10
    result={'status':'PASS','id':manifest['id'],'gate':'cropped_original_source_and_complete_frozen_query_dependency','recorded_paths':len(paths),'filtered_unique_pairs':len(pairs),'all_cutoff_paths':len(alltop),'admissible_highest_ID_ties':len(positive),'same_record_current_document_outcomes':len(current),'earlier_endorsed_document_states':len(past),'excluded_cutoff_document_states':10,'source_report_paragraphs':len(pp),'source_final_registers':len(regs['registers']),'source_register_rows':len(verified),'source_register_fields':fields,'register_private_fields_or_full_sharedStrings_copied':False,'native_executed_by_this_replay':False,'new_admissions':0}
    print(json.dumps(result))
    return result
if __name__=='__main__':main()
