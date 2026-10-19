"""Read raw Word FFS marker runs without importing the repository parser."""
import io
import re
import zipfile
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
FFS = re.compile(r'\bFFS\b', re.I)
HEAD = re.compile(r'^\s*Agreement(?:\s|:|$)', re.I)


def iter_blocks(element):
    for child in element:
        if child.tag in (W+'p', W+'tbl'):
            yield child
        elif child.tag in (W+'sdt', W+'sdtContent', W+'customXml'):
            yield from iter_blocks(child)


def final_literal(element):
    if element.tag in (W+'del', W+'moveFrom', W+'drawing', W+'pict', W+'object'):
        return ''
    if element.tag == W+'t':
        return element.text or ''
    if element.tag == W+'tab':
        return '\t'
    if element.tag in (W+'br', W+'cr'):
        return '\n'
    return ''.join(final_literal(c) for c in element)


def boolean(element):
    return None if element is None else element.get(W+'val', 'true').lower() not in ('false', '0', 'off')


def properties(rpr):
    return {k: boolean(rpr.find(W+k)) if rpr is not None else None for k in ('strike', 'dstrike', 'vanish', 'webHidden')}


def audit_document(docx_bytes):
    with zipfile.ZipFile(io.BytesIO(docx_bytes)) as z:
        xml = z.read('word/document.xml')
        styles_xml = z.read('word/styles.xml')
    root, styles = ET.fromstring(xml), ET.fromstring(styles_xml)
    body = root.find(W+'body')
    blocks = list(iter_blocks(body))
    paragraphs = list(body.iter(W+'p'))
    parent = {c:p for p in root.iter() for c in p}
    block_index = {e:i for i,b in enumerate(blocks) for e in b.iter()}
    stylemap = {s.get(W+'styleId'):s for s in styles.findall(W+'style')}
    default_p = next((s.get(W+'styleId') for s in stylemap.values() if s.get(W+'type')=='paragraph' and s.get(W+'default')=='1'), None)
    defaults = properties(styles.find(W+'docDefaults/'+W+'rPrDefault/'+W+'rPr'))

    def chain(sid):
        result, seen = [], set()
        while sid:
            assert sid not in seen and sid in stylemap, ('unresolved style',sid)
            seen.add(sid)
            s = stylemap[sid]
            result.append(s)
            b = s.find(W+'basedOn')
            sid = b.get(W+'val') if b is not None else None
        return list(reversed(result))

    def formatting(p, run, ancestors, tag):
        ppr, rpr = p.find(W+'pPr'), run.find(W+'rPr') if run is not None else None
        ps = ppr.find(W+'pStyle') if ppr is not None else None
        rs = rpr.find(W+'rStyle') if rpr is not None else None
        effective = {k:bool(v) for k,v in defaults.items()}
        for sid in [ps.get(W+'val') if ps is not None else default_p, rs.get(W+'val') if rs is not None else None]:
            for s in chain(sid):
                for k,v in properties(s.find(W+'rPr')).items():
                    if v:
                        effective[k] = not effective[k]
        direct = properties(rpr)
        for k,v in direct.items():
            if v is not None:
                effective[k] = v
        tags = [a.tag for a in ancestors]
        return {'deleted':W+'del' in tags or tag==W+'delText', 'moveFrom':W+'moveFrom' in tags,
                'effective_properties':effective, 'direct_run_properties':direct,
                'paragraph_mark_properties':properties(ppr.find(W+'rPr')) if ppr is not None else properties(None)}

    result = []
    for pi,p in enumerate(paragraphs):
        text_parts, char_state = [], []
        for t in p.iter():
            if t.tag not in (W+'t',W+'delText',W+'tab',W+'br',W+'cr'):
                continue
            ancestors, cur = [], t
            while cur in parent:
                cur = parent[cur]
                ancestors.append(cur)
                if cur.tag == W+'p':
                    break
            if not ancestors or ancestors[-1] is not p:
                continue
            run = next((a for a in ancestors if a.tag==W+'r'), None)
            f = formatting(p,run,ancestors,t.tag)
            value = '\t' if t.tag==W+'tab' else '\n' if t.tag in (W+'br',W+'cr') else t.text or ''
            text_parts.append(value)
            char_state.extend([f]*len(value))
        text = ''.join(text_parts)
        occurrences = []
        for m in FFS.finditer(text):
            states = char_state[m.start():m.end()]
            removed = [s['deleted'] or s['moveFrom'] or s['effective_properties']['strike'] or s['effective_properties']['dstrike'] for s in states]
            status = 'all_active' if not any(removed) else 'all_removed_or_struck' if all(removed) else 'mixed_active_and_removed'
            occurrences.append({'start':m.start(),'end':m.end(),'literal':m.group(),'active_formatting_status':status})
        result.append({'all_paragraph_index':pi,'body_block_index':block_index[p], 'raw_text':text,
                       'final_literal':final_literal(p),'occurrences':occurrences, 'element':p})
    return {'xml':xml,'styles_xml':styles_xml,'blocks':blocks,'paragraphs':result}
