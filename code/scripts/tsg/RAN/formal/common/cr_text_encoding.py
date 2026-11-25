"""Restore two proven UTF8 byte sequences in CR paragraph source copies.

Spec: CR revision text preserves deletion state and visible Unicode characters.
Ontology: Existing CR chunk schema.
Cycle: RAN parser control-character repair.
배경: Source math and quote bytes were stored as Latin1 or Windows-1252 text.
사용: Pass the returned paragraph to the existing native reader.
LLM 호출: 없음.
"""
from __future__ import annotations
import copy

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M='http://schemas.openxmlformats.org/officeDocument/2006/math'
_TEXT={f'{{{W}}}t',f'{{{W}}}delText',f'{{{M}}}t'}
_DELETED={f'{{{W}}}del',f'{{{W}}}moveFrom'}
_BARRIERS={f'{{{W}}}'+n for n in ['tab','ptab','br','cr','sym','fldChar','instrText','drawing','object','pict','txbxContent']}
_MATH=f'{{{M}}}oMath'
# E2 81 A1 reverses exactly to the invisible function-application operator.
_MATH_BYTES='\u00e2\u0081\u00a1'
# CP1252 maps E2 80 9C to â€œ; its undefined 9D byte remains U+009D.
_QUOTE_OPEN='\u00e2\u20ac\u0153'
_QUOTE_CLOSE='\u00e2\u20ac\u009d'


def _runs(p):
    groups=[];current=[];key=None
    def flush():
        nonlocal current,key
        if current:groups.append((key,current))
        current=[];key=None
    def walk(n,deleted=False,math=False):
        nonlocal current,key
        if isinstance(n.tag,str) and n.tag.endswith('Pr'):
            return
        if n.tag in _BARRIERS:
            flush();return
        structural = (isinstance(n.tag,str) and n.tag.startswith('{'+M+'}')
                      and n.tag not in {_MATH, f'{{{M}}}r', f'{{{M}}}t', f'{{{M}}}rPr'})
        field = n.tag == f'{{{W}}}fldSimple'
        if structural or field:flush()
        deleted=deleted or n.tag in _DELETED
        if n.tag==_MATH:
            flush();math=True
        if n.tag in _TEXT:
            k=(deleted,math)
            if key!=k:flush();key=k
            current.append(n)
        else:
            for c in n:walk(c,deleted,math)
        if n.tag==_MATH or structural or field:flush()
    walk(p);flush();return groups


def repaired_paragraph(p):
    """Return p unchanged, or a source copy with reversible math/paired quotes.

    A sequence may span adjacent text runs with identical deletion state. Tabs,
    fields, pictures and equation boundaries stop matching. Correct Unicode and
    isolated control bytes are unchanged. Only the supplied copy is modified.
    """
    nodes=[n for n in p.iter() if n.tag in _TEXT]
    if not any(any(c in (n.text or '') for c in ['\u0081','\u009d']) for n in nodes):return p
    fixed=copy.deepcopy(p);changed=False
    for (deleted,math),group in _runs(fixed):
        text=''.join(n.text or '' for n in group)
        replacements=[]
        if math:
            start=0
            while (at:=text.find(_MATH_BYTES,start))>=0:
                raw=text[at:at+3]
                assert raw.encode('latin1').decode('utf8')=='\u2061'
                replacements.append((at,at+3,'\u2061'));start=at+3
        elif _QUOTE_OPEN in text and _QUOTE_CLOSE in text:
            # Pair in source order; preserve an unmatched spelling verbatim.
            start=0
            while (left:=text.find(_QUOTE_OPEN,start))>=0:
                right=text.find(_QUOTE_CLOSE,left+3)
                if right<0:break
                for at,char in [(left,'\u201c'),(right,'\u201d')]:
                    raw=text[at:at+3]
                    data=bytes(0x9d if c=='\u009d' else c.encode('cp1252')[0] for c in raw)
                    assert data.decode('utf8')==char
                    assert ''.join(bytes([v]).decode('cp1252') if v!=0x9d else '\u009d' for v in char.encode('utf8'))==raw
                    replacements.append((at,at+3,char))
                start=right+3
        if not replacements:continue
        # All edits are mapped to original run offsets. Put each decoded character
        # where its first source byte stood; remove only its other two bytes.
        offset=0;bounds=[]
        for n in group:
            bounds.append((offset,offset+len(n.text or ''),n));offset+=len(n.text or '')
        for begin,end,char in sorted(replacements,reverse=True):
            for lo,hi,n in bounds:
                a=max(begin,lo);z=min(end,hi)
                if a<z:
                    value=n.text or ''
                    n.text=value[:a-lo]+(char if lo<=begin<hi else '')+value[z-lo:]
            changed=True
    return fixed if changed else p
