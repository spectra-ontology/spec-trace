#!/usr/bin/env python3
"""Bounded original MS-DOC direct-character-property evidence, stdlib only.

This is not a renderer or a complete style evaluator. Implements documented CFB
streams, MS-DOC Fib/Clx/Pcd/PlcBteChpx/ChpxFkp and typed Prl lengths. The source
claim is restricted to explicit direct sprmCFStrike=1 after piece modifiers.
https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-doc/be58bf9c-d1d3-40cc-91ee-36452d7939b2
"""
import bisect, hashlib, io, json, struct, zipfile
from pathlib import Path
H=lambda b:hashlib.sha256(b).hexdigest()
u16=lambda b,o:struct.unpack_from('<H',b,o)[0]
u32=lambda b,o:struct.unpack_from('<I',b,o)[0]
class CFB:
 def __init__(self,raw):
  assert raw[:8]==bytes.fromhex('d0cf11e0a1b11ae1')
  self.raw=raw;self.size=1<<u16(raw,30);self.mini=1<<u16(raw,32)
  assert self.size in (512,4096) and self.mini==64
  fatids=list(struct.unpack_from('<109I',raw,76));nfat=u32(raw,44)
  current=u32(raw,68)
  for _ in range(u32(raw,72)):
   row=self.sector(current);fatids.extend(struct.unpack_from('<%dI'%(self.size//4-1),row));current=u32(row,self.size-4)
  fatids=[i for i in fatids if i<0xfffffffa];assert len(fatids)==nfat
  self.fat=[i for s in fatids for i in struct.unpack('<%dI'%(self.size//4),self.sector(s))]
  directory=self.chain(u32(raw,48));self.entries=[]
  for i in range(0,len(directory),128):
   x=directory[i:i+128];n=u16(x,64)
   if x[66] and n:
    name=x[:n-2].decode('utf-16-le');size=struct.unpack_from('<Q',x,120)[0]
    self.entries.append({'name':name,'type':x[66],'start':u32(x,116),'size':size,'directory_index':i//128,'left':u32(x,68),'right':u32(x,72),'child':u32(x,76)})
  root=next(x for x in self.entries if x['type']==5)
  by_index={x['directory_index']:x for x in self.entries}
  todo=[root['child']];seen=set();self.root_streams={}
  while todo:
   i=todo.pop()
   if i in (0xffffffff,0xfffffffe):continue
   assert i not in seen and i in by_index,('bad CFB root sibling link',i)
   seen.add(i);e=by_index[i];todo.extend((e['left'],e['right']))
   if e['type']==2:
    assert e['name'] not in self.root_streams,('duplicate root CFB stream',e['name'])
    self.root_streams[e['name']]=e
  # ObjectPool children may contain identical stream names. Only the root
  # storage sibling tree defines this document's WordDocument and table.

  self.minidata=self.chain(root['start'])[:root['size']]
  mini_raw=self.chain(u32(raw,60)) if u32(raw,64) else b''
  self.minifat=list(struct.unpack('<%dI'%(len(mini_raw)//4),mini_raw))
 def sector(self,i):
  p=(i+1)*self.size;assert 0<=p<len(self.raw)
  return self.raw[p:p+self.size]
 def chain(self,start):
  out=[];seen=set();i=start
  while i<0xfffffffa:
   assert i not in seen and i<len(self.fat);seen.add(i);out.append(self.sector(i));i=self.fat[i]
  assert i in (0xfffffffe,0xffffffff);return b''.join(out)
 def stream(self,name):
  e=self.root_streams[name]
  if e['size']>=4096:
   body=self.chain(e['start']);assert len(body)>=e['size'],('truncated logical stream',name,len(body),e['size'])
   return body[:e['size']]
  out=[];i=e['start'];seen=set()
  while i<0xfffffffa:
   assert i not in seen and i<len(self.minifat);seen.add(i)
   out.append(self.minidata[i*self.mini:(i+1)*self.mini]);i=self.minifat[i]
  body=b''.join(out);assert len(body)>=e['size'],('truncated mini stream',name)
  return body[:e['size']]

def prls(raw):
 out=[];i=0
 while i<len(raw):
  assert i+2<=len(raw);start=i;s=u16(raw,i);i+=2;spra=s>>13
  if spra==6:
   # This bounded reader refuses exceptional variable-size opcodes instead of
   # resynchronizing heuristically across potentially unparsed operands.
   assert s not in (0xd608,0xd606),('exceptional variable operand',hex(s))
   assert i<len(raw);n=raw[i];i+=1
  else:n=(1,1,2,4,2,2,0,3)[spra]
  assert i+n<=len(raw),(hex(s),i,n,len(raw))
  operand=raw[i:i+n];i+=n
  out.append({'sprm':hex(s),'operand_hex':operand.hex(),'prl_start':start,'prl_end':i})
 return out

def parse_doc(raw):
 c=CFB(raw);word=c.stream('WordDocument');table_name='1Table' if u16(word,10)&0x200 else '0Table';table=c.stream(table_name)
 assert not (u16(word,10)&0x100),'encrypted source refused'
 offset=32;csw=u16(word,offset);offset+=2+2*csw;cslw=u16(word,offset);offset+=2+4*cslw;npairs=u16(word,offset);offset+=2
 assert npairs>=34
 pairs=[struct.unpack_from('<II',word,offset+8*i) for i in range(npairs)]
 clx_fc,size=pairs[33];clx=table[clx_fc:clx_fc+size];prcs=[];pos=0
 while clx[pos]==1:
  n=u16(clx,pos+1);prcs.append(clx[pos+3:pos+3+n]);pos+=3+n
 assert clx[pos]==2;n=u32(clx,pos+1);plc=clx[pos+5:pos+5+n];assert len(plc)==n and (n-4)%12==0
 count=(n-4)//12;cps=list(struct.unpack_from('<%dI'%(count+1),plc));assert cps[0]==0 and cps==sorted(cps)
 pieces=[];text=[]
 for i in range(count):
  pcd=plc[4*(count+1)+8*i:4*(count+1)+8*(i+1)];x=u32(pcd,2);compressed=bool(x&0x40000000);fc=x&0x3fffffff
  assert not x&0x80000000
  if compressed:assert fc%2==0;fc//=2
  width=1 if compressed else 2;body=word[fc:fc+width*(cps[i+1]-cps[i])]
  decoded=body.decode('cp1252' if compressed else 'utf-16-le');assert len(decoded)==cps[i+1]-cps[i]
  pieces.append({'cp_start':cps[i],'cp_end':cps[i+1],'fc_start':fc,'width':width,'prm':u16(pcd,6),'pcd_hex':pcd.hex()});text.append(decoded)
 bte_fc,bte_size=pairs[12];bte=table[bte_fc:bte_fc+bte_size];assert (bte_size-4)%8==0
 nb=(bte_size-4)//8;bte_fcs=list(struct.unpack_from('<%dI'%(nb+1),bte));pages=list(struct.unpack_from('<%dI'%nb,bte,4*(nb+1)))
 def direct(cp):
  p=pieces[bisect.bisect_right(cps,cp)-1];fc=p['fc_start']+(cp-p['cp_start'])*p['width']
  j=bisect.bisect_right(bte_fcs,fc)-1;assert 0<=j<nb
  pn=pages[j]&0x3fffff;page=word[pn*512:(pn+1)*512];assert len(page)==512
  crun=page[511];assert 1<=crun<=101;fcs=list(struct.unpack_from('<%dI'%(crun+1),page));r=bisect.bisect_right(fcs,fc)-1;assert 0<=r<crun
  loc=page[4*(crun+1)+r]*2
  grp=b'' if loc==0 else page[loc+1:loc+1+page[loc]];ops=prls(grp)
  prm=p['prm'];piece_ops=[]
  if prm&1:
   iprm=prm>>1;assert iprm<len(prcs);piece_ops=[x for x in prls(prcs[iprm]) if (int(x['sprm'],16)>>10)&7==2]
  elif prm:
   # Nonzero compact Prm0 requires the documented isprm lookup. This version
   # refuses it, preserving the unresolved gate instead of assuming no override.
   raise ValueError('nonzero Prm0 needs official isprm mapping:'+hex(prm))
  return {'cp':cp,'fc':fc,'piece':p,'FKP_page':pn,'FKP_run':r,'FKP_run_fc_start':fcs[r],'FKP_run_fc_end':fcs[r+1],'grpprl_hex':grp.hex(),'direct_PRLs':ops,'piece_character_PRLs':piece_ops}
 return ''.join(text),direct,{'streams':[dict(x,sha256=H(c.stream(x['name']))) for x in c.root_streams.values() if x['name'] in ('WordDocument',table_name)],'FIB_pairs_start':offset,'FIB_nFib':u16(word,2),'FIB_pairs':npairs,'CLX_offset':clx_fc,'CLX_size':size,'CLX_Prc_n':len(prcs),'piece_n':len(pieces),'PlcBteChpx_offset':bte_fc,'PlcBteChpx_size':bte_size,'CHPX_pages':nb,'text_cp_length':len(''.join(text))}
