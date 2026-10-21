"""Bounded original-format source replay: OOXML, RTF and CFB Word97.

The RTF parser accepts this finite document's actual token vocabulary and
rejects new/unknown destination or character-state controls rather than
silently ignoring them. Converted DOCX files are not source authority here.
"""
import bisect, collections, hashlib, io, json, re, zipfile
import xml.etree.ElementTree as ET

W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
H=lambda b:hashlib.sha256(b).hexdigest()
norm=lambda s:re.sub(r'\s+','',s).lower()
HEADER=re.compile(r'(?m)^[ \t]*(R3-[0-9]{6})[ \t]+\S')
DECISION=re.compile(r'(?im)^[ \t]*(?:Decision:[ \t]*)?The[ \t]+document[ \t]+was[ \t]+([^\n]*)')
POSITIVE=re.compile(r'(?i)^(?:agreed(?:[ \t]+in[ \t]+principle)?|endorsed|approved|conditionally[ \t]+agreed)(?=[ \t.,!(;]|$)')
RTF_ALLOWED=set('rtf ansi ansicpg paperh paperw margl margr margt margb psz colortbl fonttbl red green blue fcharset fnil f plain fs tx cf cb tab pard par b sb tqr i ul page u'.split())

def rtf_text(raw):
    source=raw.decode('ascii'); out=[];stack=[];skip=False;counts=collections.Counter();i=0;fallback=0
    while i<len(source):
        c=source[i]
        if c=='{':stack.append(skip);i+=1;continue
        if c=='}':assert stack;skip=stack.pop();i+=1;continue
        if c=='\\':
            start=i;i+=1;assert i<len(source)
            if source[i] in '{}\\':
                if not skip and not fallback:out.append(source[i])
                elif fallback:fallback-=1
                i+=1;continue
            if source[i]=="'":
                ch=bytes.fromhex(source[i+1:i+3]).decode('cp1252');i+=3
                if not skip and not fallback:out.append(ch)
                elif fallback:fallback-=1
                continue
            m=re.match(r'([A-Za-z]+)(-?[0-9]+)?( ?)',source[i:]);assert m,('unsupported RTF symbol',source[start:start+50])
            token,arg=m.group(1),m.group(2);i+=m.end();counts[token]+=1
            assert token in RTF_ALLOWED,('unsupported RTF control',token)
            if token in {'fonttbl','colortbl'}:skip=True
            if token=='ansicpg':assert arg=='1252'
            if not skip:
                if token=='u':
                    n=int(arg);out.append(chr(n if n>=0 else n+65536));fallback=1
                elif token in {'par','page'}:out.append('\n')
                elif token=='tab':out.append('\t')
            continue
        i+=1
        if c in '\r\n':continue
        if fallback:fallback-=1;continue
        if not skip:out.append(c)
    assert not stack and not fallback
    # An explicit finite vocabulary excludes strike, hidden, revision,
    # fields and objects across every group, including destinations.
    return ''.join(out),{'control_tokens':dict(sorted(counts.items())),'unknown_controls':0,'active_text_controls_present':False}

def xml_text(raw,xmlreader):
    # Reuse the independently pinned OOXML reader only for original OOXML.
    with zipfile.ZipFile(io.BytesIO(raw))as z:
        styles=ET.fromstring(z.read('word/styles.xml'))
    assert not any(e.tag in {W+k for k in ('strike','dstrike','vanish','webHidden')}for e in styles.iter())
    item=xmlreader.open_report_bytes(raw)
    # Only character runs contribute visible characters. Paragraph tab-stop
    # definitions (w:pPr/w:tabs/w:tab) are layout, not body tab characters.
    text='\n'.join(''.join(r['text']for r in b['runs'])for b in item['blocks'])
    aligned=[]
    for b in item['blocks']:
        aligned.append(''.join(r['text']if r['active']else'\ufffd'*len(r['text'])for r in b['runs']))
    active='\n'.join(aligned)
    return text,active,item

def xlsx_rows(raw):
    S='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    with zipfile.ZipFile(io.BytesIO(raw))as z:
        assert z.testzip()is None
        shared=[''.join(e.text or ''for e in x.iter(S+'t'))for x in ET.fromstring(z.read('xl/sharedStrings.xml')).findall(S+'si')]
        sheet=z.read('xl/worksheets/sheet1.xml');root=ET.fromstring(sheet);rows=[]
        for row in root.findall(S+'sheetData/'+S+'row'):
            cells={}
            for c in row.findall(S+'c'):
                v=c.find(S+'v');value=''if v is None else v.text
                if c.get('t')=='s':value=shared[int(value)]
                cells[re.sub(r'[0-9]+$','',c.get('r'))]=value
            rows.append({'row':int(row.get('r')),'cells':cells,'row_XML_sha256':H(ET.tostring(row,encoding='utf-8'))})
    assert rows[0]['cells']['A']=='TDoc'and rows[0]['cells']['F']=='Type'and rows[0]['cells']['T']=='Spec'
    return rows,H(sheet)

def xlsx_rows_from_extract(extract):
    S='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    wrap=lambda raw:ET.fromstring(b'<x xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'+raw+b'</x>')[0]
    shared={}
    for number,item in extract['sharedStrings_exact_fragments'].items():
        raw=item['raw_XML_UTF8'].encode();assert H(raw)==item['raw_XML_sha256']
        shared[int(number)]=''.join(e.text or ''for e in wrap(raw).iter(S+'t'))
    rows=[];referenced=set()
    for item in extract['header_and_selected_rows']:
        raw=item['raw_XML_UTF8'].encode();assert H(raw)==item['raw_XML_sha256']
        el=wrap(raw);assert int(el.get('r'))==item['row'];cells={}
        for c in el.findall(S+'c'):
            v=c.find(S+'v');value=''if v is None else v.text
            if c.get('t')=='s':referenced.add(int(value));value=shared[int(value)]
            cells[re.sub(r'[0-9]+$','',c.get('r'))]=value
        rows.append({'row':int(el.get('r')),'cells':cells,'row_XML_sha256':H(ET.tostring(el,encoding='utf-8'))})
    assert referenced==set(shared)and len(rows)==11
    assert rows[0]['cells']['A']=='TDoc'and rows[0]['cells']['F']=='Type'and rows[0]['cells']['T']=='Spec'
    return rows,extract['original_sheet_sha256']


def run(folder,index,frontier,all617,xmlreader,binaryreader,binarystyles):
    reports={};register=None
    for item in index:
        if 'local_extract'in item:
            raw=(folder/item['local_extract']).read_bytes()
            assert H(raw)==item['extract_sha256']and len(raw)==item['extract_bytes']
            extract=json.loads(raw);assert extract['source_XLSX_sha256']==item['archive_sha256']and extract['source_XLSX_bytes']==item['archive_bytes']
            register=xlsx_rows_from_extract(extract);continue
        if 'local_member'in item:raw=(folder/item['local_member']).read_bytes()
        else:
            archive=(folder/item['local_archive']).read_bytes();assert H(archive)==item['archive_sha256']
            if item['member']=='[SELF]':raw=archive
            else:
                with zipfile.ZipFile(io.BytesIO(archive))as z:
                    assert z.testzip()is None;raw=z.read(item['member'])
        assert H(raw)==item['member_sha256']and len(raw)==item['member_bytes']
        if item['kind']=='register':
            register=xlsx_rows(raw);continue
        if item['format']=='RTF':
            text,meta=rtf_text(raw);active=text;direct=None
        elif item['format']=='CFB':
            native,direct,meta=binaryreader.parse_doc(raw)
            # Preserve one-character offsets in the Word CP stream.
            text=native.replace('\r','\n').replace('\x0b','\n').replace('\x07','\t');active=text
            styles=binarystyles.stylesheet(raw);assert not styles['watched_style_operations'];meta=meta|{'stylesheet':styles}
        else:
            assert item['format']=='OOXML';text,active,meta=xml_text(raw,xmlreader);direct=None
        reports[item['meeting']]={'item':item,'raw':raw,'text':text,'active':active,'meta':meta,'direct':direct,
          'headers':[(m.group(1),m.start(),m.end())for m in HEADER.finditer(text)]}
    assert len(reports)==4 and register is not None
    registerrows,sheetsha=register;roles=[]
    for row in frontier:
        rep=reports[row['resolutionId'].split('-')[1]];text=rep['text'];td=row['tdocNumber'];events=[]
        for hi,(tid,start,_)in enumerate(rep['headers']):
            if tid!=td:continue
            end=rep['headers'][hi+1][1]if hi+1<len(rep['headers'])else len(text)
            matches=list(DECISION.finditer(text,start,end));assert len(matches)==1,(td,'own decision count',len(matches))
            m=matches[0];a,b=m.span();assert rep['active'][a:b]==text[a:b],(td,'inactive original outcome',repr(text[a:b]),repr(rep['active'][a:b]))
            header_end=text.find('\n',start)
            assert rep['active'][start:header_end]==text[start:header_end],(td,'inactive original header')
            if rep['direct']is not None:
                for cp in range(start,b):
                    d=rep['direct'](cp);ops=binarystyles.expand_ops(d['direct_PRLs']+d['piece_character_PRLs'])
                    assert not [op for op in ops if int(op['sprm'],16)in binarystyles.WATCH],(td,'inactive binary character',cp)
            outcome=m.group(1).strip();events.append({'header_CP':start,'end_before_next_header_CP':end,
              'header_text':text[start:text.find('\n',start)],'decision_CP':[a,b],'decision_text':text[a:b],
              'outcome':outcome,'positive':bool(POSITIVE.match(outcome)),'active_header_and_outcome':True})
        positive=any(e['positive']for e in events);assert positive==row['generic_positive'],(td,'original-format mismatch')
        reg=[]
        if positive:
            reg=[r for r in registerrows if r['cells'].get('A')==td];assert len(reg)==1
            assert reg[0]['cells']['F']in {'CR','draftCR','pCR'}and reg[0]['cells']['T']=='38.423'
        mentions=[m.start()for m in re.finditer(re.escape(td),text)];assert mentions
        roles.append({'resolutionId':row['resolutionId'],'tdocNumber':td,'source_role_positive':positive,
          'own_original_events':events,'mentions_CP':mentions,'original_register_rows':reg,
          'classification':'same_CR_endorsed'if positive else'same_CR_nonapproval'if events else'reference_only_without_own_current_meeting_approval'})
    bindings=[];frozen={r['resolutionId']:r for r in all617}
    for rid in dict.fromkeys(r['resolutionId']for r in frontier):
        rep=reports[rid.split('-')[1]];content=frozen[rid]['content'];wanted=[m.group(1)for m in HEADER.finditer(content)]
        first=norm(content.splitlines()[0]);assert first
        # Retain every same-sentence anchor compatible with the complete
        # following header sequence. Repeated prose does not license a
        # fabricated unique paragraph position.
        candidates=[];offset=0
        for line in rep['text'].splitlines(keepends=True):
            if first in norm(line):
                hs=[h for h in rep['headers']if h[1]>=offset]
                if [h[0]for h in hs[:len(wanted)]]==wanted:candidates.append((offset,line.rstrip('\n'),hs[:len(wanted)]))
            offset+=len(line)
        assert candidates,(rid,'original anchor+all-header boundary',len(candidates))
        cp,line,hs=candidates[0]
        assert all(candidate[2]==hs for candidate in candidates),(rid,'different full-header correspondence')
        for pos,literal,_ in candidates:
            assert norm(rep['active'][pos:pos+len(literal)])==norm(literal)
            if rep['direct']is not None:
                for char in range(pos,pos+len(literal)):
                    d=rep['direct'](char);ops=binarystyles.expand_ops(d['direct_PRLs']+d['piece_character_PRLs'])
                    assert not [op for op in ops if int(op['sprm'],16)in binarystyles.WATCH]
        bindings.append({'resolutionId':rid,'content_UTF8_sha256':H(content.encode()),
         'compatible_active_anchor_candidates':[{'CP':p,'text':t}for p,t,_ in candidates],
         'headers':[{'tdocNumber':td,'CP':a,'source_text':rep['text'][a:rep['text'].find('\n',a)]}for td,a,_ in hs]})
    assert sum(len(b['headers'])for b in bindings)==267
    byrid={b['resolutionId']:b for b in bindings}
    for role in roles:
        for ev in role['own_original_events']:
            assert any(h['tdocNumber']==role['tdocNumber']and h['CP']==ev['header_CP']for h in byrid[role['resolutionId']]['headers'])
    out={'status':'PASS_ORIGINAL_ARCHIVE_FORMATS_BOUNDED35_ACTIVE_ROLES_AND267_RETAINED_HEADERS',
      'original_format_counts':{'OOXML':2,'RTF':1,'CFB':1},'register_sheet_XML_sha256':sheetsha,
      'reports':[{'meeting':k,'source':v['item'],'text_UTF8_sha256':H(v['text'].encode()),'text_characters':len(v['text']),
       'parser_evidence':v['meta']if k!='111'and k!='118'else{k2:v2 for k2,v2 in v['meta'].items()if k2!='blocks'}}for k,v in reports.items()],
      'rows':roles,'body_bindings':bindings,'counts':{'prefix_paths':35,'retained_bodies':10,'full_header_bindings':267,
       'positive_paths':sum(r['source_role_positive']for r in roles),'negative_own_paths':sum(r['classification']=='same_CR_nonapproval'for r in roles),
       'reference_only_paths':sum(r['classification']=='reference_only_without_own_current_meeting_approval'for r in roles)},
      'global125_source_approval_certified':False,'converted_DOCX_used_as_original_authority':False}
    assert out['counts']=={'prefix_paths':35,'retained_bodies':10,'full_header_bindings':267,'positive_paths':10,'negative_own_paths':15,'reference_only_paths':10}
    return out
