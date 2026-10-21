"""Offline replay of the source-certified reverse impact contract."""
import sys
if sys.flags.optimize:
    raise SystemExit('Run with assertions enabled; -O/-OO refused')
from pathlib import Path
import ast,collections,gzip,hashlib,json,re
import xml.etree.ElementTree as E
EXPECTED_PAYLOAD={'README.md': {'bytes': 718, 'sha256': 'cdef9c05c6636c33f5d657519da911708bc380db972d5cbab7ae246e81e68252'}, 'authority/author_spans.json': {'bytes': 24366, 'sha256': 'fd1287260885cdc4eb439211e17a04b7d6dce64a4ee3d3826449fc1235c4d4e4'}, 'authority/criteria.json': {'bytes': 3382, 'sha256': 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4'}, 'authority/original.json': {'bytes': 593, 'sha256': '30d037b2517213e163036aab95b62b89d8b277df86700a77f8fc798bd5a3fd4e'}, 'authority/original_parser.py': {'bytes': 16552, 'sha256': 'e02327bf2ffeeb3e870344f714c64a7b607932da97b3d23073fd3410233b41c0'}, 'contract/definition.json': {'bytes': 1852, 'sha256': 'ddfa1977be5c83d741762c1c6d72c2cd34d90a1dd2157d0012f4ab0bb92ecc0c'}, 'contract/joint_admissibility.json': {'bytes': 6040, 'sha256': '563d9a3c8027faacb8a76119a9028e62084385c553b015ebb2d4c48c5b2a7066'}, 'contract/primary.json': {'bytes': 14259, 'sha256': '77b119199118d469298dd3bbbe872f8f8590b22d0af84ab9564db68322167613'}, 'contract/secondary.json': {'bytes': 27222, 'sha256': '1c2d20e643de4f56e5fe4cc4178d235a15590dd4e49e00323897caaab7f10a6a'}, 'data/complete_eligible_sample_pool.json': {'bytes': 2067, 'sha256': 'c1c48df601c966c87f96a12e5371fa75e2d7024159841d214bec94d0134ede42'}, 'data/frozen_paths.json.gz': {'bytes': 30541, 'sha256': '9cedb3114b0938fd9cde787ec74b6186979455ae74016a10b32e884cc1538b6c'}, 'data/scoring_controls.json': {'bytes': 38899, 'sha256': 'def849e912cfa8c102e4908d7558121e6d2d30ebcffd4ac76eadacd14f2b7b7e'}, 'data/source_field_fragments.json.gz': {'bytes': 52235, 'sha256': '0c77c074b072dc12e5e3bb83b65582f1f18816827c4da02159febc98cfef5a42'}, 'native/coordinator.json': {'bytes': 272, 'sha256': 'f5bdfaaa16d6053a26d9e7f81baeafbcb6948d9e951aaa3145f88dc1f1b563b5'}, 'native/execution_RAN1.json': {'bytes': 1920, 'sha256': '86a209d6c960e6d39a66ecc81357f5f48067d8e8af5f0328ad8ac7a31dba1e20'}, 'native/execution_events.jsonl': {'bytes': 584, 'sha256': '13f5b3e26eb38a5ec5ac2ae60f7f84d94e42a6f86fc0ac4f1369e608040b13ab'}, 'native/execution_protocol.json': {'bytes': 1183, 'sha256': '66a7af8cb42220b49693c9e943af6c4e818f545dc46f10a0eecb880bb2b9b251'}, 'native/fresh_CIM_observations.jsonl': {'bytes': 2336, 'sha256': 'e44798aa6596544b33ab7c323be096cb5e3afa43d7bd79d2a775f90e3dc63861'}, 'native/full.json': {'bytes': 1246, 'sha256': 'ede15ea227341bc1e4bdc96d08d62d58ba76680f469c8e2c771fbd9d9e65b8c0'}, 'native/full.jsonl.gz': {'bytes': 420, 'sha256': '52ea9c35a33c632adea73349b8f2f2864c7bfc25e610602b18a8665fbe8e3d74'}, 'native/input.jsonl': {'bytes': 776, 'sha256': '215e5327066fec5f8d371bd77448ceb169fd45f915a70f4aa7937409e7b0b5eb'}, 'native/limited.json': {'bytes': 1251, 'sha256': '94ec04e325eb7edb0ced51d98379488a009c795258781a913052853030fecb40'}, 'native/limited.jsonl.gz': {'bytes': 98, 'sha256': 'b96b4ca37ddf706e87b2cd1e34251a3a00aacfdcbf37a144cca67f1c38f6d534'}, 'native/outer_guard.json': {'bytes': 2761, 'sha256': '8fdb04611124de730a076eac171bca72dca0b4f44372d5ec6616d0cac36bf12d'}, 'native/resource_checks.jsonl': {'bytes': 1088, 'sha256': '9497e2fdfc592d95a2ccada20e92be94bdf2dbcec7d42a635c4d05f492422635'}, 'proof/ROOT_original_field_role_reopen.json.gz': {'bytes': 28507, 'sha256': 'cc4d3aa4bb4f60020a1e04b8d5c99dfe8d1cd2f457e3dd61224123e4f2c6ccd9'}, 'proof/SQL_and_joint_scorer.json': {'bytes': 8617, 'sha256': '9b0d84bb81f9067cccd4a82dbea1645188c80b6a3792f9839b1809517d92a31b'}, 'proof/actual_native_SQL_joint_binding.json': {'bytes': 7518, 'sha256': '91172c5a027c8f88331f833148ce1f8989e81177ed8f4c9a7fa582eeee25b4ed'}, 'proof/native_preparation.json': {'bytes': 6231, 'sha256': 'e9c3e8fc56feae3fda7041776d150bddd6ec09c97e5ba86847cee7f6bbc3a05a'}, 'proof/primary_schema.json': {'bytes': 1595, 'sha256': 'f7cd2deb6d14de1de5e3fbe98b87e54c4fa20a7a8aec68ae9329e2ee2c2f4f54'}, 'scope.json': {'bytes': 1203, 'sha256': '370c4ce3036a88921aadfdf61c939d5a2e1abbff2bc98c128d19749cb450c9d7'}, 'scoring/item_scorer_dispatch.py': {'bytes': 1017, 'sha256': '6cb3a3e7d4a16f944ca21d3d44d2a75b357f15f2d5d0372d8e1b768ae89172d6'}, 'scoring/one_record_sample_scorer.py': {'bytes': 4356, 'sha256': 'a9a40495742a650bcdd33628ec7ea10c94f8247c94982d3f372c771374f08b9f'}, 'scoring/original_scorer.py': {'bytes': 8320, 'sha256': '1af0744df717abafe8115d560ac2db695ebea8a4b7d2ee104736dabf233badeb'}, 'scoring/review_schema.py': {'bytes': 2268, 'sha256': '42d7019ed86d6ad92f7aef785419ca3cecbe207be4515760ecaf758e7cb3ae55'}, 'scoring/score_predictions.py': {'bytes': 2459, 'sha256': '485b7054923f6a1bf87b1be29503168ef17ce402dbcc521e19a0e1ea72ece4c6'}, 'scoring/scorer.py': {'bytes': 7786, 'sha256': 'c6db2d2423e12e29f97746afdf9f22f143c948db89a4fe4dce14847e932ccdbd'}, 'scoring/source_pins.json': {'bytes': 190, 'sha256': 'a86fad1201ca0225a798d2f48a278fe66c58d326907d959772a6ea05f3266f92'}, 'scoring/typed_values.py': {'bytes': 19323, 'sha256': 'd7eee66cce2dabe3ef48c173e84fac47192266bdd3e8ce78214f8361df5161ba'}, 'source/TSG_1909682_document.xml.gz': {'bytes': 14088, 'sha256': '8bfb7834ca608e8b51a87f69d3aaa3367548fadd6a423fc688227732c23deaef'}, 'source/TSG_1909682_styles.xml.gz': {'bytes': 6288, 'sha256': 'efa6f7b736d82e26a61900f2c8bae07a74222b7fc5a377bc097978060b0a06ea'}, 'source/WG_1909682_document.xml.gz': {'bytes': 13951, 'sha256': '59dc9a36ea1462c21a1264ce2691fa6bd66f6be89946cfa9801d6268ce4ed5b9'}, 'source/WG_1909682_styles.xml.gz': {'bytes': 6160, 'sha256': '87b5b5789b0191481f649b46c536f4799f302df32d29bbc3a625b78e1cd584c8'}, 'source/prior_1908953_document.xml.gz': {'bytes': 13978, 'sha256': '0bb1a4cf88c8fc0a0005326a667aeeb7729b134c97610aad72127f44b4bf9382'}, 'source/prior_1908953_styles.xml.gz': {'bytes': 6133, 'sha256': 'de14ade4884b4a0535c8f5f670a86298042e6c02854c0ccc4921d93c6245d00b'}}
META={'artifact_type': 'source_certified_contract_evidence', 'id': 'RAN1_P4_CQ2-3', 'repair_sha256': '032c4939f0b9e2640d29f874fbf53b725533a261545e12400cce6e9f9abeb541', 'criteria_sha256': 'bfefc447de02b451da33e0c85afb2708cf6ca7a201fedf07ec4d5b984d492fa4', 'original_question_preserved': True, 'new_admissions': 0}
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def read_json(root,n):return json.loads((root/n).read_bytes())
def gz_json(root,n):return json.loads(gzip.decompress((root/n).read_bytes()))
def wt(e):return ''.join(x.text or '' for x in e.iter(W+'t'))
def specs(t):return [a+'.'+b for a,b in re.findall(r'\b(\d{2})\.\s*(\d{3})\b',t)]
def main():
    root=Path(__file__).absolute().parent
    for p in [Path(__file__).absolute(),root,*root.parents]:
        if p.is_symlink():raise ValueError('symlink entry/ancestor')
    expected=set(EXPECTED_PAYLOAD)|{'reproduce.py','manifest.json','inventory.json'}
    actual=set()
    for p in root.rglob('*'):
        if p.is_symlink():raise ValueError('symlink payload')
        rel=p.relative_to(root).as_posix()
        if p.is_file():actual.add(rel)
        elif p.is_dir():
            if not any(v.startswith(rel+'/') for v in expected):raise ValueError('unexpected directory')
        else:raise ValueError('nonregular entry')
    assert actual==expected,'closed payload namespace'
    for n,pin in EXPECTED_PAYLOAD.items():
        b=(root/n).read_bytes()
        assert len(b)==pin['bytes'] and sha(b)==pin['sha256'],n
    manifest=read_json(root,'manifest.json')
    assert canon(manifest)==canon(dict(META,files=EXPECTED_PAYLOAD)),'immutable metadata/payload map'
    inv=read_json(root,'inventory.json')
    files=[{'path':n,'bytes':len((root/n).read_bytes()),'sha256':sha((root/n).read_bytes())} for n in sorted(actual-{'inventory.json'})]
    assert inv=={'files':files},'self-excluding exact inventory'
    # Imports occur only after the complete code and scientific payload bootstrap.
    sys.path.insert(0,str(root/'scoring'))
    import item_scorer_dispatch as dispatcher
    import scorer
    import review_schema
    original=read_json(root,'authority/original.json')
    criteria=read_json(root,'authority/criteria.json')
    definition=read_json(root,'contract/definition.json')
    assert set(definition)=={'id','question_en','original_query','reference_query','required_fields','collection','cardinality_policy','repair_class','original_question_preserved'}
    repair=sha(canon(definition).encode())
    assert repair==META['repair_sha256']
    assert definition['id']==META['id'] and definition['question_en']==original['question_en']
    assert definition['original_query']==original['cypher']
    assert definition['original_question_preserved'] is True
    criteria_sha=sha((root/'authority/criteria.json').read_bytes())
    assert criteria_sha==META['criteria_sha256']
    units=[r['name'] if isinstance(r,dict) else r for r in criteria['semantic_units']]
    for n in ('primary','secondary'):
        review=read_json(root,'contract/'+n+'.json')
        review_schema.check_pass(review,original['question_en'],units,criteria_sha=criteria_sha,identity_key='repair_sha256',identity_sha=repair)
    assert read_json(root,'contract/primary.json')['reviewer']!=read_json(root,'contract/secondary.json')['reviewer']
    paths=gz_json(root,'data/frozen_paths.json.gz')
    assert len(paths['whole_affected_paths'])==577 and len(paths['incoming'])==130
    assert len({r['edge_id'] for r in paths['whole_affected_paths']})==577
    incoming=paths['incoming']
    assert len({r['edge_id'] for r in incoming})==130
    assert all(r['specNumber']=='38.214' and r['rel_type']=='AFFECTS_CORE_SPEC' for r in incoming)
    kept=[r for r in incoming if 'other core' not in (r['reasonForChange'] or '').lower()]
    excluded=[r for r in incoming if 'other core' in (r['reasonForChange'] or '').lower()]
    assert kept==paths['kept'] and excluded==paths['excluded']
    pool=[r['tdocNumber'] for r in kept]
    assert len(pool)==len(set(pool))==129 and len(excluded)==1
    assert excluded[0]['tdocNumber']=='R1-1909682'
    source=gz_json(root,'data/source_field_fragments.json.gz')
    verified=[]
    for rec in source['positive_DOCX']:
        assert rec['tdocNumber'] in rec['front_header_ids']
        assert rec['expected_identifier_present'] is True
        fields=[]
        for row in rec['rows']:
            e=E.fromstring(row['row_XML'])
            assert sha(E.tostring(e))==row['row_XML_sha256']
            cells=[wt(c) for c in e.findall(W+'tc')]
            assert 'other core specifications' in ' '.join(cells).lower()
            assert '38.214' in specs(cells[-1])
            assert row['document_XML_sha256']==rec['document_XML_sha256']
            fields.append(row['row_XML_sha256'])
        assert fields
        verified.append(rec['tdocNumber'])
    assert len(verified)==len(set(verified))==128
    binary=source['binary_CP_observation']
    assert binary['tdocNumber']=='R1-1803552'
    b=binary['binary_core_field']
    assert b['CP_range'][1]-b['CP_range'][0]==len(b['literal'])
    assert binary['tdocNumber'] in b['header']
    core=b['literal'].split('Other core specifications',1)[1].split(' Test specifications',1)[0]
    assert '38.214' in specs(core)
    assert set(verified+[binary['tdocNumber']])==set(pool)
    # Re-execute the original extractor over exact saved document XML bytes.
    parser=(root/'authority/original_parser.py').read_text()
    node=next(n for n in ast.parse(parser).body if isinstance(n,ast.FunctionDef) and n.name=='extract_other_specs')
    env={'re':re};exec(compile(ast.Module(body=[node],type_ignores=[]),'pinned_original_extractor','exec'),env)
    class Cell:
        def __init__(self,t):self.text=t
    class Row:
        def __init__(self,c):self.cells=[Cell(x) for x in c]
    class Table:
        def __init__(self,r):self.rows=[Row(x) for x in r]
    decisive=[]
    for name in ['WG_1909682','TSG_1909682','prior_1908953']:
        raw=gzip.decompress((root/('source/'+name+'_document.xml.gz')).read_bytes())
        styles=gzip.decompress((root/('source/'+name+'_styles.xml.gz')).read_bytes())
        assert sha(raw)==source['negative_versions'][name]['document_XML_sha256']
        assert sha(styles)==source['negative_versions'][name]['styles_XML_sha256']
        doc=E.fromstring(raw)
        rows=[(ti,ri,[wt(c) for c in r.findall(W+'tc')]) for ti,t in enumerate(doc.iter(W+'tbl')) for ri,r in enumerate(t.findall(W+'tr'))]
        truefields=[cells for _,_,cells in rows if any('Other core specifications' in c for c in cells)]
        assert len(truefields)==1 and specs(' '.join(truefields[0]))==[]
        if name!='prior_1908953':
            reason=next((ti,cells) for ti,_,cells in rows if cells and cells[0].strip()=='Reason for change:')
            assert 'other coresets' in ' '.join(reason[1]).lower()
            table=Table([c for ti,_,c in rows if ti==reason[0]])
            assert env['extract_other_specs'](table)==(['38.214','38.213'],[],[])
            decisive.append(name)
    assert decisive==['WG_1909682','TSG_1909682']
    captures=[]
    inputs=[json.loads(x) for x in (root/'native/input.jsonl').read_text().splitlines()]
    execution=read_json(root,'native/execution_RAN1.json')
    protocol=read_json(root,'native/execution_protocol.json')
    guard=read_json(root,'native/outer_guard.json')
    assert guard['status']=='PASS' and guard['child_exit']==0 and guard['owned_cleanup']['owned_stopped'] is True
    assert guard['prestart_available_minimum_bytes']==26*1024**3 and guard['continuous_reserve_minimum_bytes']==16*1024**3
    assert guard['Linux_check_seconds']==2 and guard['Windows_check_seconds']==10
    assert guard['scope_sha256']==sha((root/'contract/definition.json').read_bytes())
    assert protocol['container_memory_bytes']==2*1024**3 and protocol['container_cpu_cores']==1
    assert protocol['query_timeout_seconds']==20 and protocol['model_calls']==0
    assert execution['inventory_unchanged'] is True and execution['source_before']==execution['source_after']
    assert execution['input_sha256']==sha((root/'native/input.jsonl').read_bytes())
    assert execution['model_calls']==0
    for i,name in enumerate(['limited','full']):
        c=read_json(root,'native/'+name+'.json')
        raw=gzip.decompress((root/('native/'+name+'.jsonl.gz')).read_bytes())
        assert sha(raw)==c['rows_sha256']
        assert c['query']==inputs[i]['candidate_query'] and c['query_sha256']==sha(c['query'].encode())
        assert c['columns']==['sp.specNumber','crCount','sampleCRs']
        assert c['status']=='OK' and c['rows_retained']==1 and c['full_rows_available'] is True
        assert c['rollback_completed'] is True and c['truncated'] is False
        assert c['execution_query_type']==c['plan_query_type']=='r'
        rows=[json.loads(x) for x in raw.splitlines()]
        assert len(rows)==1 and len(rows[0])==3
        captures.append(dict(zip(c['columns'],rows[0])))
    assert captures[1]['sp.specNumber']=='38.214' and type(captures[1]['crCount'])is int and captures[1]['crCount']==129
    assert collections.Counter(captures[1]['sampleCRs'])==collections.Counter(pool)
    assert captures[0]['crCount']==129
    native=[{'specNumber':r['sp.specNumber'],'crCount':r['crCount'],'sampleCRs':r['sampleCRs']} for r in captures[:1]]
    actual_pool=captures[1]['sampleCRs']
    score=dispatcher.score(definition,native,native,sample_pool=actual_pool,diagnostic=True)
    assert score['exact'] is True and score['f1']==1 and score['gold_records']==1
    controls=read_json(root,'data/scoring_controls.json')
    passed=0
    for t in controls['tests']:
        r=dispatcher.score(definition,native,t['records'],sample_pool=actual_pool,diagnostic=True)
        assert r['exact'] is t['expected_exact'] and r['f1']==float(t['expected_exact'])
        passed+=1
    assert passed==30
    # Exercise the actual cohort entrypoint without model or answer-parser changes.
    import score_predictions
    task=dict(definition,repair_sha256=repair,validation_status='validated')
    gold={'id':definition['id'],'repair_sha256':repair,'records':native,'sample_pool':actual_pool}
    prediction={'id':definition['id'],'repair_sha256':repair,'records':controls['tests'][1]['records']}
    # run() accepts read-only path objects; in-memory path adapters keep package replay write-free.
    class SavedLines:
        def __init__(self,x):self.b=(json.dumps(x,ensure_ascii=False)+'\n').encode()
        def read_text(self):return self.b.decode()
        def read_bytes(self):return self.b
    result=score_predictions.run(SavedLines(task),SavedLines(gold),SavedLines(prediction))
    assert result['outcomes'][0]['exact'] is True and result['outcomes'][0]['gold_records']==1
    scope=read_json(root,'scope.json')
    assert scope['native_capture_queries']==2 and scope['runtime_source_label_inputs']==0
    assert scope['new_admissions']==0 and type(scope['new_admissions'])is int
    result={'status':'PASS','cases':[{'id':definition['id'],'record_count':1,'count':129,'sample_cardinality':10,'complete_eligible_sample_pool':129,'source_DOCX_fields_replayed':128,'binary_saved_CP_field_observation':1,'frozen_role_paths':577,'incoming_recorded_paths':130,'wrong_field_shadowing_removed':1,'joint_controls':30,'scorer_entrypoint_replayed':True,'full_native_three_columns_equal_SQL':True}],'new_admissions':0,'scope':scope}
    print(json.dumps(result))
    return result
if __name__=='__main__':main()

