import hashlib,re
ANCHOR='In NR case, PH range would need to be expanded based on LTE PHR.'
HEADER=re.compile(r'\x13HYPERLINK "[^"\r]*/(R4-\d{6,8})\.zip"\x14\1\x15[^\r]*\r')
def sha(b):return hashlib.sha256(b).hexdigest()
def witness(raw,reader):
 text,direct,meta=reader['parse_doc'](raw)
 matches=list(re.finditer(re.escape('Agreement: '+ANCHOR+'\r'),text))
 assert len(matches)==1,('unique complete own Agreement paragraph required',len(matches))
 a=matches[0];headers=list(HEADER.finditer(text))
 before=[h for h in headers if h.end()<=a.start()]
 after=[h for h in headers if h.start()>=a.end()]
 assert before and len(after)>=3
 owner=before[-1];first,second,third=after[:3]
 assert owner.group(1)=='R4-1804616'
 assert first.group(1)=='R4-1804833' and second.group(1)=='R4-1804834'
 own=text[a.start():first.start()]
 assert own=='Agreement: '+ANCHOR+'\rDecision:\t\tNoted\x0b\x0b\r'
 assert not re.search(r'R4-\d{6,8}',own)
 target=text[second.start():third.start()]
 assert 'CR for PHR requirement for NR' in target
 assert '38.133 v15.1.0' in target and 'Decision:\t\tNoted' in target
 end=text.index('\r7.11\t',second.end())
 local=text[owner.start():end+1]
 return {'native_parse':meta,'text_cp_length':len(text),
  'source_own_document':{'tdocNumber':owner.group(1),'header_CP':[owner.start(),owner.end()],'raw_header':owner.group()},
  'Agreement_paragraph':{'CP':[a.start(),a.end()],'raw_paragraph':a.group(),'content_without_label':ANCHOR},
  'own_Agreement_until_next_Tdoc':{'CP':[a.start(),first.start()],'raw_text':own,'literal_R4_Tdoc_tokens':[]},
  'following_first_document':{'tdocNumber':first.group(1),'header_CP':[first.start(),first.end()],'raw_header':first.group()},
  'following_target_CR_document':{'tdocNumber':second.group(1),'header_CP':[second.start(),second.end()],'raw_header':second.group(),
   'explicit_Decision':'Noted','same_topic_is_not_denied':True},
  'physical_local_window':{'CP':[owner.start(),end+1],'raw_text':local,'raw_text_utf8_sha256':sha(local.encode()),
   'native_table_cell_markers':local.count('\x07'),'paragraph_markers':local.count('\r'),
   'control_characters_preserved':True},
  'formatting_assurance':'Raw CFB text/piece mapping and complete native paragraph/field boundaries only. No style-based active/deleted/rendered interpretation is asserted.'}
