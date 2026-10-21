"""Actual original XML/style review support; no native or API calls."""
import hashlib,io,json,re,zipfile
from pathlib import Path
from xml.etree import ElementTree as E
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
def sha(b):return hashlib.sha256(b).hexdigest()
def tx(e):return ''.join(n.text or'' for n in e.iter() if n.tag in(W+'t',W+'delText',M+'t'))
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def props(rp):
 if rp is None:return {}
 return {e.tag.split('}')[-1]:{k.split('}')[-1]:v for k,v in e.attrib.items()}for e in rp}
def active(v):return v is not None and v.get('val','true').lower()not in('0','false','off','none')
def run_style(p,r,styles,defaults):
 layers=[('docDefaults',defaults)]
 ps=p.find(W+'pPr/'+W+'pStyle');rs=r.find(W+'rPr/'+W+'rStyle')
 def chain(sid):
  if not sid:return[]
  seen=set();ans=[]
  while sid and sid not in seen:
   seen.add(sid);s=styles.get(sid)
   if s is None:break
   ans.append((sid,props(s.find(W+'rPr'))));ba=s.find(W+'basedOn');sid=ba.get(W+'val')if ba is not None else None
  return list(reversed(ans))
 pid=ps.get(W+'val')if ps is not None else next((sid for sid,s in styles.items()if s.get(W+'type')=='paragraph'and s.get(W+'default')=='1'),None)
 layers+=chain(pid)
 if rs is not None:layers+=chain(rs.get(W+'val'))
 layers+=[('direct',props(r.find(W+'rPr')))]
 effective={}
 for _,pr in layers:effective.update(pr)
 return layers,effective
