"""Inspect exact original source covers and preserve the study-release selector."""
import gzip,hashlib,json,re
from pathlib import Path
import xml.etree.ElementTree as E
D=Path(__file__).resolve().parent;F=D/'actual_original_sources_and_complete_frozen_v1'
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}';N={'w':W[1:-1]}
def active(x):
 if x.tag in {W+'del',W+'moveFrom'}:return ''
 return (x.text or '') if x.tag==W+'t' else ''.join(active(y) for y in x)
out=[]
for m in json.loads((F/'source_originals_metadata_and_locators.json').read_bytes()):
 b=gzip.decompress((F/m['source_dir']/'document.xml.gz').read_bytes());body=E.fromstring(b).find('w:body',N)
 blocks=[{'body_child':i,'text':active(x),'table_rows':[[active(tc) for tc in tr.findall('w:tc',N)] for tr in x.findall('w:tr',N)]} for i,x in enumerate(body) if i<9]
 if m['key'].startswith('TR'):
  cover=[x for x in blocks if re.search(r'TR\s*38[.]\d+\s+V18[.]|Release\s*18',x['text'])]
  assert cover,m['key']
 else:cover=blocks
 out.append({'key':m['key'],'document_xml_sha256':hashlib.sha256(b).hexdigest(),'actual_original_cover_blocks':cover})
p=D/'actual_ROOT_original_release_covers_and_CR_source_role_v2.json';assert not p.exists();p.write_text(json.dumps({'status':'PASS_SOURCE_COVERS_PARSED_FROM_ORIGINAL_XML','sources':out,'role_note':'All six original TR covers targetRelease18. The later actual normative CR2504980 targetsRelease19; original question selects study release and has no effect-release restriction. Cover lines in first capture included direct paragraphs only; this versioned table-aware supplement provides actual cover proof without changing that prior capture.'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':'PASS','source_n':len(out),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))

