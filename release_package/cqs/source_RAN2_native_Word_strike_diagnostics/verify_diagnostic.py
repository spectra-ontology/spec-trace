#!/usr/bin/env python3
"""Bounded source-format diagnostic; Python standard library, no host fallback."""
import hashlib
import io
import json
import os
import re
from pathlib import Path
import stat
import sys
import types
import zipfile

INVENTORY_SHA256 = 'd87f1c7aeb252f5b9f02fad814d8b6cbd83c04a6ef467c6190c617f94ee175c1'
INVENTORY_BYTES = 2099
IMMUTABLE_FILES = 11
SCOPE = {
 'tdocNumber': 'R2-1803854',
 'related_original_question_id': 'RAN2_P4_CQ4-2',
 'source_counterexamples': 1,
 'source_summary_CP': [1353, 14731],
 'strike_CP': [9069, 9086],
 'strike_characters': 17,
 'nonempty_styles_inspected': 107,
 'whole_question_status': 'evidence_pending',
 'original560_pass_increment': 0,
 'human_expert_n': 0,
 'nonblind_AI': True,
 'new_model_API_calls': 0,
 'native_database_executions': 0,
 'benchmark_text_policy': 'active-only versus marked historical transcript is not selected',
 'claim_limit': 'One pinned original native-format witness and one retained frozen-field projection; not whole-document rendering, whole-graph recount or prevalence.'
}
CLAIMS = {
 'included_original_ZIP_and_member_reparse': True,
 'all_107_style_character_UPX_and_conditional_branches_inspected': True,
 'all_17_witness_direct_PRLs_and_piece_overrides_reparsed': True,
 'bounded_observed_opcode_allowlists': True,
 'frozen_projection_only_not_full_graph_recount': True,
 'official_authority_URL_section_hash_rule_pins_only_HTML_omitted': True,
 'full_Word_renderer_or_general_parser': False,
 'whole_question_answer_or_approval_attribution_certified': False
}

def sha(b):
 return hashlib.sha256(b).hexdigest()

def canonical(v):
 return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)

def same(a,b,where):
 assert canonical(a)==canonical(b), where

def no_links(path):
 # Do not resolve before checking: same-byte external symlinks must not be read.
 p=Path(os.path.abspath(os.fspath(path)))
 for q in [p,*p.parents]:
  st=os.lstat(q)
  assert not stat.S_ISLNK(st.st_mode), ('symlink refused',str(q))
 return p

ENTRY=no_links(__file__)
ROOT=no_links(ENTRY.parent)

def read(rel):
 assert type(rel) is str and rel and not rel.startswith('/')
 p=Path(rel)
 assert '..' not in p.parts and '.' not in p.parts and p.as_posix()==rel
 path=no_links(ROOT/p)
 assert path.is_file()
 return path.read_bytes()

def load(rel):
 def pairs(xs):
  result={}
  for k,v in xs:
   assert k not in result, ('duplicate JSON key',k)
   result[k]=v
  return result
 return json.loads(read(rel),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))

def toggle(operand,style):
 assert type(style) is bool
 assert type(operand) is int and operand in (0,1,0x80,0x81)
 return {0:False,1:True,0x80:style,0x81:not style}[operand]

def main():
 assert sys.flags.optimize==0, 'Python -O disables diagnostic assertions and is refused'
 ib=read('immutable_inventory.json')
 assert len(ib)==INVENTORY_BYTES and sha(ib)==INVENTORY_SHA256
 inv=load('immutable_inventory.json')
 assert set(inv)=={'schema_version','scope','files'} and type(inv['schema_version']) is int and inv['schema_version']==1
 assert type(inv['files']) is list and len(inv['files'])==IMMUTABLE_FILES
 expected_paths=set()
 for item in inv['files']:
  assert set(item)=={'path','bytes','sha256'}
  assert type(item['bytes']) is int and item['bytes']>=0
  assert type(item['sha256']) is str and len(item['sha256'])==64
  assert item['path'] not in expected_paths
  expected_paths.add(item['path'])
  data=read(item['path'])
  assert len(data)==item['bytes'] and sha(data)==item['sha256'], ('immutable file changed',item['path'])
 actual=set()
 for p in ROOT.rglob('*'):
  no_links(p)
  if p.is_file(): actual.add(p.relative_to(ROOT).as_posix())
 assert actual==expected_paths|{'manifest.json','immutable_inventory.json','verify_diagnostic.py'}, ('undeclared/missing files',sorted(actual^expected_paths))
 own=ENTRY.read_bytes()
 expected_manifest={
  'schema_version':1,
  'id':'RAN2-1803854-native-strike-17CP',
  'status':'LOCAL_PORTABLE_DIAGNOSTIC_PROPOSAL',
  'artifact_type':'bounded_original_source_format_counterexample',
  'scope_and_provenance':SCOPE,
  'verification_claims':CLAIMS,
  'immutable_inventory':{'path':'immutable_inventory.json','bytes':INVENTORY_BYTES,'sha256':INVENTORY_SHA256,'files':IMMUTABLE_FILES},
  'verifier':{'path':'verify_diagnostic.py','bytes':len(own),'sha256':sha(own)}
 }
 same(load('manifest.json'),expected_manifest,'Exact typed manifest declarations, self pin and inventory pin')
 modules={}
 for name,rel in [('native_reader','code/native_reader.py'),('formatting_reader','code/formatting_reader.py')]:
  module=types.ModuleType(name);module.__file__=str(ROOT/rel);sys.modules[name]=module
  exec(compile(read(rel),module.__file__,'exec'),module.__dict__)
  modules[name]=module
 native=modules['native_reader'];fmt=modules['formatting_reader']
 witness=load('evidence/observed_witness.json')
 source=witness['source_archive'];archive=read(source['path'])
 assert len(archive)==source['bytes'] and sha(archive)==source['sha256']=='6e694487977fcaf6df47e9177e4383d8193d3de7520ce6d290a2b50be0a1c80a'
 with zipfile.ZipFile(io.BytesIO(archive)) as z:
  matches=[i for i in z.infolist() if i.filename==witness['member']]
  assert len(matches)==1
  info=matches[0];raw=z.read(info)
 assert info.file_size==len(raw)==witness['member_bytes']==2525696
 assert format(info.CRC,'08x')==witness['member_CRC32']=='c1220902'
 assert sha(raw)==witness['member_sha256']=='bea46f4fcba84871a1175e1f4a071e732e09e2f6890c0dfa14c8b43b86fc39ee'
 text,direct,parse=native.parse_doc(raw)
 cover=text[:text.index('Reason for change:')]
 assert re.findall(r'(?<![A-Za-z0-9])R2-\d{6,8}(?!\d)',cover)==['R2-1803854']
 assert text[31:41]=='R2-1803854'
 same(parse,witness['binary_parse'],'all recorded native parse metadata')
 styles=fmt.stylesheet(raw)
 same(styles,witness['whole_stylesheet'],'all native styles and inheritance/conditional branches')
 assert styles['nonempty_styles']==107 and styles['watched_style_operations']==[]
 summary=next(x for x in fmt.source_fields(text) if x['field']=='summaryOfChange')
 same(summary,witness['summary_source_cell'],'full source summary cell and exact CP boundary')
 assert (summary['cp_start'],summary['cp_end'])==(1353,14731)
 sw=witness['strike_witness'];assert (sw['cp_start'],sw['cp_end'])==(9069,9086)
 assert sw['literal']==text[9069:9086]=='to be transmitted'
 assert sw['native_neighborhood'] in text
 observed_direct=set();derived=[]
 for cp in range(9069,9086):
  ev=direct(cp)
  assert ev['piece']['prm']==0 and ev['piece_character_PRLs']==[]
  ops=ev['direct_PRLs'];codes={x['sprm'] for x in ops};observed_direct.update(codes)
  assert not codes.intersection({'0x4a30','0x2a32','0x2a33','0xca85'})
  strike=[x for x in ops if int(x['sprm'],16)==0x0837]
  assert len(strike)==1 and strike[0]['operand_hex']=='81'
  derived.append({'character':text[cp],'style_strike':False,'effective_native_strike':toggle(0x81,False),'direct_evidence':ev})
 same(derived,sw['characters'],'all 17 native CP direct properties and effective strike states')
 scope=load('evidence/bounded_opcode_scope.json')
 same(sorted(observed_direct),scope['observed_witness_direct_opcodes'],'closed direct observed opcode set')
 stylecodes=sorted({x['sprm'] for s in styles['styles'] for x in s['character_UPX_PRLs']})
 same(stylecodes,scope['observed_style_opcodes'],'closed all-style observed opcode set')
 assert not ({int(s,16) for s in stylecodes}|{int(s,16) for s in observed_direct}) & {0xc615,0xd608,0xd606}
 assert scope['archive_sha256']==source['sha256'] and scope['member_sha256']==sha(raw)
 assert scope['native_character_PRL_piece_overrides_in_witness']==[]
 frozen=load('evidence/retained_frozen_summary_projection.json')
 assert frozen['tdocNumber']=='R2-1803854'
 assert 'to be transmittedbuilt' in frozen['summaryOfChange']
 assert witness['frozen_neighborhood'] in frozen['summaryOfChange']
 question=load('evidence/related_original_question.json')
 assert 'RAN2_P4_CQ4-2' in canonical(question)
 # Replay the documented operand truth table, including Boolean versus integer types.
 controls=[]
 for style in (False,True):
  for operand in (0,1,0x80,0x81):
   expected=(False if operand==0 else True if operand==1 else style if operand==0x80 else not style)
   assert toggle(operand,style) is expected
   controls.append({'style':style,'operand':hex(operand),'result':expected})
 rejected=0
 for operand,style in [(2,False),(False,False),(0,0),(0x81,1)]:
  try: toggle(operand,style)
  except AssertionError: rejected+=1
  else: raise AssertionError(('unsupported toggle input accepted',operand,style))
 assert rejected==4
 for op in (0xd608,0xd606):
  try:native.prls(op.to_bytes(2,'little')+b'\x00')
  except AssertionError:pass
  else:raise AssertionError('exceptional variable PRL accepted')
 authority=load('provenance/primary_authority_URL_section_hash_and_rule_pins.json')
 assert len(authority['items'])==14
 assert len({x['id'] for x in authority['items']})==14
 for item in authority['items']:
  assert item['official_url'].startswith('https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-doc/')
  assert type(item['original_HTML_bytes']) is int and item['original_HTML_bytes']>0
  assert type(item['original_HTML_sha256']) is str and len(item['original_HTML_sha256'])==64
  assert item['HTML_included'] is False and type(item['used_rule_paraphrase']) is str
 result={'status':'PASS','id':'RAN2-1803854-native-strike-17CP','source_counterexamples':1,'native_struck_characters':17,'nonempty_styles_inspected':107,'valid_toggle_controls':8,'invalid_toggle_controls_rejected':4,'exceptional_PRL_controls_rejected':2,'whole_question_status':'evidence_pending','original560_pass_increment':0,'human_expert_n':0,'new_model_API_calls':0,'native_database_executions':0,'immutable_files':IMMUTABLE_FILES,'network_or_host_fallback':False,'limits':'Pinned original source witness and saved frozen summary projection only; active-only answer policy and whole-question closure are not determined.'}
 print(json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=='__main__':
 main()
