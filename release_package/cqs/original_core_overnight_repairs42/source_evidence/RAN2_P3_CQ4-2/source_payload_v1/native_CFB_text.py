"""Exact retained-CFB lexical recipe; formatting scope is separate."""
import hashlib,struct
import binary_reader
reader=vars(binary_reader)
def sha(b):return hashlib.sha256(b).hexdigest()
def retained_CFB_text(raw):
 c=reader['CFB'](raw);u16=reader['u16'];u32=reader['u32']
 word=c.stream('WordDocument');table_name='1Table' if u16(word,10)&0x200 else '0Table';table=c.stream(table_name)
 assert not u16(word,10)&0x100
 off=32;off+=2+2*u16(word,off);off+=2+4*u16(word,off);n=u16(word,off);off+=2
 assert n>=34
 pairs=[struct.unpack_from('<II',word,off+8*i) for i in range(n)]
 fc,size=pairs[33];clx=table[fc:fc+size];assert len(clx)==size;pos=0
 while clx[pos]==1:pos+=3+u16(clx,pos+1)
 assert clx[pos]==2
 n=u32(clx,pos+1);plc=clx[pos+5:pos+5+n];assert len(plc)==n and (n-4)%12==0
 count=(n-4)//12;cps=struct.unpack_from('<%dI'%(count+1),plc);assert cps[0]==0 and list(cps)==sorted(cps)
 text=[];astral=0
 for i in range(count):
  pcd=plc[4*(count+1)+8*i:4*(count+1)+8*(i+1)];x=u32(pcd,2);assert not x&0x80000000
  compressed=bool(x&0x40000000);fc=x&0x3fffffff
  if compressed:assert fc%2==0;fc//=2
  units=cps[i+1]-cps[i];width=1 if compressed else 2;body=word[fc:fc+width*units];assert len(body)==width*units
  decoded=body.decode('cp1252' if compressed else 'utf-16-le')
  assert (len(decoded) if compressed else len(decoded.encode('utf-16-le'))//2)==units
  astral+=sum(ord(c)>65535 for c in decoded);text.append(decoded)
 return ''.join(text),{'piece_n':count,'UTF16_CP_units':cps[-1],'Python_codepoints':sum(map(len,text)),'astral_characters':astral,'text_only_no_formatting_certification':True,'streams':{k:hashlib.sha256(c.stream(k)).hexdigest() for k in ('WordDocument',table_name)}}
