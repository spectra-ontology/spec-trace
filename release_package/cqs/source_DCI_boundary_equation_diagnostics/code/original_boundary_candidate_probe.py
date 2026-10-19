"""Query-independent candidate segmentation, not a production own-role parser.

All original broad windows are used, including those narrowed in older
question-specific investigations. No keyword or ID-based selection is used.
"""
from pathlib import Path
from collections import Counter, defaultdict
from xml.etree import ElementTree as ET
import json, gzip, hashlib, re

H = Path(__file__).resolve().parent
SOURCE = H / 'loop114_RAN1_ten_report_generic_source_text_and_DMRS_tie_proposal_NOT_ADMITTED/evidence'
OUT = H / 'loop164_query_independent_boundary_candidate_feasibility_all3176_NOT_ADMITTED'
OUT.mkdir(exist_ok=False)
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'
OLE = '{urn:schemas-microsoft-com:office:office}OLEObject'
TDOC = re.compile(r'^\s*R\d+[A-Z]?-\d{6,8}(?:\b|(?=[A-Z]))')
MARKER = re.compile(r'^\s*(?:Agreement|Conclusion|Working\s+Assumption)\s*:?\s*$', re.I)
APPROVAL = re.compile(r'\b(?:is|are)\s+(?:agreed|approved|endorsed)\b', re.I)
NUMERICAL_CLAUSE = re.compile(r'^\s*\d+(?:\.\d+)+(?:\s|[A-Z])')

def sha(data): return hashlib.sha256(data).hexdigest()
def text(e): return ''.join(x.text or '' for x in e.iter() if x.tag in {W+'t',M+'t'})
def on(e): return e is not None and e.get(W+'val','true').lower() not in {'false','0','off','none'}
def jread(name):
    with gzip.open(SOURCE / name, 'rt') as f: return [json.loads(line) for line in f]
def write(name, obj):
    p = OUT / name
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
    return {'path': name, 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())}

geometry = jread('identity_and_source_geometry.jsonl.gz')
assert len(geometry) == 3176 and len({r['resolutionId'] for r in geometry}) == 3176
by_meeting = defaultdict(list)
for row in geometry: by_meeting[row['meeting']].append(row)

all_rows, candidates, preservation = [], [], []
for meeting, group in by_meeting.items():
    suffix = meeting.replace('RAN1#','').replace('bis','b')
    path = SOURCE / f'RAN1_{suffix}_document.xml.gz'
    xml = gzip.decompress(path.read_bytes())
    body = list(ET.fromstring(xml).find(W+'body'))
    literals = [text(b) for b in body]

    def next_nonblank(index):
        for i in range(index+1,len(body)):
            if literals[i].strip(): return i
        return None

    def prior_nonblank(index, lo):
        for i in range(index-1,lo-1,-1):
            if literals[i].strip(): return i
        return None

    def tabbed_tdoc(index):
        return (body[index].tag == W+'p' and bool(TDOC.match(literals[index]))
                and len(list(body[index].iter(W+'tab'))) >= 2)

    for g in group:
        lo, hi = g['original_broad_raw_body_child_range']
        literal = '\n'.join(literals[lo:hi])
        assert sha(literal.encode()) == g['broad_source_literal_sha256'], g['resolutionId']
        flagged, kept = [], []
        for i in range(lo+1,hi):
            block, value = body[i], literals[i].strip()
            if not value or block.tag != W+'p': continue
            nxt = next_nonblank(i)
            prev = prior_nonblank(i,lo)
            blank_before = i > lo and not literals[i-1].strip()
            style = block.find(W+'pPr/'+W+'pStyle')
            style_name = style.get(W+'val') if style is not None else None
            reasons = []
            if style_name and re.fullmatch(r'Heading\d+',style_name,re.I):
                if NUMERICAL_CLAUSE.match(value):
                    kept.append({'raw_body_child0':i,'reason':'Numerical normative-clause heading retained as possible adopted-TP content.'})
                else:
                    reasons.append('top_level_named_Word_heading_transition')
            if re.fullmatch(r'From\s+AI\s*\d+(?:\.\d+)*',value,re.I) and nxt is not None and tabbed_tdoc(nxt):
                reasons.append('From_AI_then_separate_tabbed_TDoc_group')
            if tabbed_tdoc(i) and blank_before:
                has_own_approval = bool(APPROVAL.search(value)) or (nxt is not None and bool(APPROVAL.search(literals[nxt])))
                explicit_final_intro = prev is not None and bool(re.search(r'\bFinal\s+CRs?\b',literals[prev],re.I))
                if has_own_approval or explicit_final_intro:
                    kept.append({'raw_body_child0':i,'reason':'Own final-CR/approval continuation retained; tabbed TDoc alone is not a new contribution boundary.'})
                else:
                    reasons.append('blank_then_tabbed_TDoc_title_source_group_without_own_approval')
            # A candidate only: a bold/underlined label immediately before a new
            # resolution may be a following topic title OR an own emphasized line.
            # It is never automatically cut.
            runs = [r for r in block.iter(W+'r') if text(r).strip()]
            mark = block.find(W+'pPr/'+W+'rPr')
            emphasized = bool(runs) and all(
                (on(r.find(W+'rPr/'+W+'b')) or (mark is not None and on(mark.find(W+'b'))))
                and (on(r.find(W+'rPr/'+W+'u')) or (mark is not None and on(mark.find(W+'u'))))
                for r in runs)
            if emphasized and blank_before and nxt is not None and MARKER.fullmatch(literals[nxt].strip()):
                reasons.append('emphasized_label_before_next_resolution_AMBIGUOUS')
            if reasons:
                flagged.append({'raw_body_child0':i,'literal':value,'reasons':reasons,
                                'pStyle':style_name,'XML_sha256':sha(ET.tostring(block,encoding='utf-8')),
                                'next_nonblank':None if nxt is None else {'raw_body_child0':nxt,'literal':literals[nxt]},
                                'prior_nonblank':None if prev is None else {'raw_body_child0':prev,'literal':literals[prev]},
                                'candidate_only_no_automatic_cut':True})
        status = Counter()
        for block in body[lo:hi]:
            for tag in ['del','moveFrom','ins','moveTo']:
                status['w:'+tag] += sum(1 for _ in block.iter(W+tag))
            for tag in ['strike','dstrike']:
                status['explicit_on_w:'+tag] += sum(on(e) for e in block.iter(W+tag))
            status['OLE'] += sum(1 for _ in block.iter(OLE))
            status['OMML'] += sum(1 for _ in block.iter(M+'oMath'))
        row = {'resolutionId':g['resolutionId'],'meeting':meeting,
               'original_broad_raw_body_child_range':[lo,hi],
               'original_broad_literal_sha256_actual':sha(literal.encode()),
               'source_document_XML_sha256':sha(xml),
               'boundary_candidates':flagged,'own_continuation_preservation_witnesses':kept,
               'raw_redline_and_math_primitive_counts':dict(status),
               'interpretation':'Candidate inventory, not certified segmentation. An unflagged record is not proven fully own-content or redline/math faithful.'}
        all_rows.append(row)
        if flagged: candidates.append(row)
        if kept: preservation.append(row)

files = [write('all3176_query_independent_segmentation_candidate_rows.json',all_rows),
         write('all_flagged_candidate_windows_with_exact_boundaries.json',candidates),
         write('all_preserved_own_TP_and_final_CR_continuations.json',preservation)]
rules = {
    'scope':'All3176 original broad stable-record windows from10 retained report XMLs, not only lexical positives or a selected prefix.',
    'question_or_target_ID_filter':False,
    'candidate_boundary_rules':['Named top-level Word heading, excluding numerical normative-clause headings.',
       'From AI + following separate tabbed TDoc/title/source paragraph.',
       'Blank paragraph + tabbed TDoc/title/source paragraph, unless its line/following line records own approval or preceding line explicitly introduces Final CRs.',
       'Bold/underlined standalone label before next resolution, explicitly ambiguous and never an automatic cut.'],
    'never_automatically_remove':['adopted TP tables','record notes','normative clause headings','own approved final CR continuations','struck/deleted spans'],
    'redline_representation':'Retain raw XML/styles and preserve removed/insertion/move/strike status as typed segments. Raw explicit-property counts here are not an effective inherited-style renderer.',
    'math_representation':'Retain OMML XML or CFB/preview provenance with typed decoded/unread status. Current93-object decoder is separate access evidence, not an exact formula oracle.',
    'content_contract_first':'What-was-agreed requires actual recorded decision content. Original3-column query retained; no ID-only substitute or header-only reduction. All31 latest tie candidates remain admissible until a separately reviewed contract says otherwise.',
    'no_graph_or_gold_written':True,
    'scope_limit':'This probe does not admit a generic own-text field. It produces a finite boundary-review frontier; observations are not exclusion masks.'}
files.append(write('prospective_generic_segmentation_and_answer_content_policy.json',rules))
receipt={'status':'ACTUAL_ALL3176_GENERIC_CANDIDATE_FEASIBILITY_NOT_SEGMENTATION_PASS',
         'stable_windows':len(all_rows),'reports':len(by_meeting),
         'windows_with_boundary_candidates':len(candidates),
         'candidate_paragraphs':sum(len(r['boundary_candidates'])for r in all_rows),
         'candidate_rule_occurrences':dict(Counter(reason for r in all_rows for c in r['boundary_candidates']for reason in c['reasons'])),
         'windows_with_explicit_own_continuation_preservation':len(preservation),
         'redline_or_math_windows':sum(any(r['raw_redline_and_math_primitive_counts'].values())for r in all_rows),
         'all_original_broad_window_literal_hashes_replayed':True,
         'question_specific_prior_window_cuts_inherited':False,
         'remaining_whole_question_gates':['Candidate false boundaries on own normative/approved material must be ruled out by independent raw-role reading before any cut.',
             'A generic role-typed redline/math renderer is still needed; counts do not implement faithful answer content.',
             'Full latest31 admissible-content and source field contract requires independent semantic review, then new input/scorer/native/model gates.'],
         'source_geometry_sha256':sha((SOURCE/'identity_and_source_geometry.jsonl.gz').read_bytes()),
         'files':files,'original560_pass_increment':0,'human_experts':0,'new_API_native_graph_public_operations':0}
write('receipt.json',receipt)
print(json.dumps({k:receipt[k]for k in ['status','stable_windows','reports','windows_with_boundary_candidates','candidate_paragraphs','candidate_rule_occurrences','windows_with_explicit_own_continuation_preservation']}))
