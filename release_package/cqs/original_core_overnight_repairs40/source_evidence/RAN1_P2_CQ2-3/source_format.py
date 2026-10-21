import pathlib,json,hashlib,zipfile,xml.etree.ElementTree as E,re
D=pathlib.Path(__file__).absolute().parent
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}';M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
 b=p.read_bytes();return dict(path=str(p.relative_to(D)),bytes=len(b),sha256=sha(b))
def truth(el):return el is not None and el.get(W+'val','true').lower() not in ('0','false','off','no')
def prop(el,name):return False if el is None else truth(el.find(W+name))
def attr(el,name):return None if el is None else el.get(W+name)
def load_doc(path):
 with zipfile.ZipFile(path) as z: xb=z.read('word/document.xml');sb=z.read('word/styles.xml')
 root=E.fromstring(xb);styles=E.fromstring(sb);byid={s.get(W+'styleId'):s for s in styles.findall(W+'style')};parent={c:p for p in root.iter() for c in p}
 # All relevant documents have no inherited strike/dstrike in any style, including conditional table styles or defaults.
 assert not styles.findall('.//'+W+'strike') and not styles.findall('.//'+W+'dstrike')
 def chain(sid):
  result=[];seen=set()
  while sid:
   assert sid not in seen;seen.add(sid);s=byid.get(sid)
   if s is None:return result+[dict(styleId=sid,missing=True)]
   result.append(dict(styleId=sid,type=s.get(W+'type'),basedOn=attr(s.find(W+'basedOn'),'val'),style_xml_sha256=sha(E.tostring(s))))
   sid=attr(s.find(W+'basedOn'),'val')
  return result
 def block(i):
  el=list(root.find(W+'body'))[i];paras=[el] if el.tag==W+'p' else list(el.iter(W+'p'));rows=[]
  for pi,p in enumerate(paras):
   pstyle=attr(p.find(W+'pPr/'+W+'pStyle'),'val');table=p
   while table is not None and table.tag!=W+'tbl':table=parent.get(table)
   tstyle=attr(table.find(W+'tblPr/'+W+'tblStyle'),'val') if table is not None else None
   active=[];removed=[];marked=[];runs=list(p.iter(W+'r'));charstyles=set();visible=[]
   for ri,r in enumerate(runs):
    text=''.join(n.text or '' for n in r.iter() if n.tag in (W+'t',W+'delText'));visible.append(text)
    rp=r.find(W+'rPr');rs=attr(rp.find(W+'rStyle'),'val') if rp is not None else None
    if rs:charstyles.add(rs)
    ancestors=[];a=r
    while a is not None:
     if a.tag in (W+'del',W+'ins',W+'moveFrom',W+'moveTo'):ancestors.append(a.tag.split('}')[-1])
     a=parent.get(a)
    deleted=('del' in ancestors or 'moveFrom' in ancestors or bool(r.findall('.//'+W+'delText')))
    struck=prop(rp,'strike') or prop(rp,'dstrike');hidden=prop(rp,'vanish')
    (removed if deleted or struck else active).append(text)
    if text and (deleted or struck or hidden):marked.append(dict(run_index=ri,text=text,direct_strike=prop(rp,'strike'),direct_dstrike=prop(rp,'dstrike'),deleted=deleted,change_ancestors=ancestors,direct_hidden=hidden,run_style_chain=chain(rs)))
   rows.append(dict(paragraph_index=pi,text=''.join(visible),active_text=''.join(active),removed_or_struck_text=''.join(removed),paragraph_style_chain=chain(pstyle),table_style_chain=chain(tstyle),character_style_chains={s:chain(s) for s in sorted(charstyles)},marked_runs=marked,run_n=len(runs)))
  text=''.join(n.text or '' for n in el.iter() if n.tag in (W+'t',W+'delText',M+'t'))
  return dict(body_child0=i,kind=el.tag.split('}')[-1],xml_bytes=len(E.tostring(el)),xml_sha256=sha(E.tostring(el)),full_XML_text_sha256=sha(text.encode()),paragraphs=rows,OMML_n=len(list(el.iter(M+'oMath'))))
 return dict(path=pin(path),document_xml_bytes=len(xb),document_xml_sha256=sha(xb),styles_xml_bytes=len(sb),styles_xml_sha256=sha(sb),all_style_and_default_strike_elements_n=0,all_style_and_default_double_strike_elements_n=0,all_styles_checked_including_table_conditionals=True),block
