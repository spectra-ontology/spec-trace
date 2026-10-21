"""Prospective unchanged-question repair over retained graph scalar values only."""
import re

TD=re.compile(r'R1-\d{7}(?!\d)')
HEADER=re.compile(r'^R1-\d{7}\t')
FINAL=re.compile(r'(?i)^.*\bfinal\s+CRs?\b.*(?:in|:)\s*:?$')
STATUS=re.compile(r'^\(Rel-\d+,.*\bCR\d+.*\) is (?:agreed|endorsed)\.$')
FOLLOWING=re.compile(r'(?i)^.*\bfollowing\s+Tdocs?\b.*$')
COMEBACK=re.compile(r'(?i)^.*\bcomeback\s+for\s+draft\s+LS\b.*$')
CAPTURED=re.compile(r'(?i)^.*\b(?:agreement|agreements|decision|decisions|above)\b.*\bcaptured\b.*\bin\s*:?$')


def own_record(value):
    ls=(value or'').split('\n');accepted={};cut=len(ls)
    for i,s in enumerate(ls):
        if not HEADER.match(s):continue
        previous=next((j for j in range(i-1,-1,-1)if ls[j].strip()),None)
        nxt=next((j for j in range(i+1,len(ls))if ls[j].strip()),None)
        final=previous is not None and(FINAL.fullmatch(ls[previous])or(STATUS.fullmatch(ls[previous])and previous>0 and any(v=='final_CR'for v in accepted.values())))and nxt is not None and STATUS.fullmatch(ls[nxt])
        listed=previous is not None and(FOLLOWING.fullmatch(ls[previous])or accepted.get(previous)=='explicit_following_Tdocs')
        comeback=previous is not None and COMEBACK.fullmatch(ls[previous])and nxt is not None and TD.search(s).group()in ls[nxt]and re.search(r'(?i)\b(?:endorsed|approved|agreed)\b',ls[nxt])
        captured=previous is not None and CAPTURED.fullmatch(ls[previous])
        if final:accepted[i]='final_CR'
        elif listed:accepted[i]='explicit_following_Tdocs'
        elif comeback:accepted[i]='draft_LS_comeback'
        elif captured:accepted[i]='explicit_captured_agreement'
        else:cut=i;break
    return '\n'.join(ls[:cut]),{'cut_line':cut,'line_n':len(ls),'accepted_header_rules':accepted}


def normalize_title(value):return(value or'').replace('\u00a0',' ').strip()
def company_in_source(source,company):
    return bool(re.search(r'(?<!\w)'+re.escape(company['companyName'])+r'(?!\w)',source or'',re.I))
def original_source(remark):
    pieces=(remark or'').split('Original source')
    return pieces[-1].split('<',1)[0]if len(pieces)>1 else''
def header_source(cells):
    source_cells=[cell for cell in cells[2:]if cell.strip()]
    if not source_cells:return ''
    first=source_cells[0]
    if re.fullmatch(r'(?i)(?:RAN1,\s*)?Moderator',first)and len(source_cells)>1 and source_cells[1].startswith('('):
        return first+' '+source_cells[1]
    return first

def frozen_header_company_sources(agreements,company):
    headers={}
    for a in agreements:
        for line in((a.get('content')or'')+'\n'+(a.get('note')or'')).split('\n'):
            cells=line.split('\t')
            if len(cells)<3 or not TD.fullmatch(cells[0]):continue
            source=header_source(cells)
            if not company_in_source(source,company):continue
            key=(cells[0],normalize_title(cells[1]))
            headers.setdefault(key,[]).append({'owner':a['resolutionId'],'line':line,'source':source})
    return headers
def meeting_key(meeting):
    label=(meeting.get('canonicalMeetingNumber')or meeting['meetingNumber']).lower()
    return(meeting['meetingNumberInt'],int(label.endswith('b')or label.endswith('bis')))


def project(agreements,tdocs,meetings,company):
    headers=frozen_header_company_sources(agreements,company)
    qualified={};proof={}
    for t in tdocs:
        reasons=[]
        if company['companyName']in t['SUBMITTED_BY_companies']:reasons.append('existing_SUBMITTED_BY')
        if company_in_source(original_source(t.get('secretaryRemarks')),company):reasons.append('retained_secretary_explicit_original_source')
        if(t['tdocNumber'],normalize_title(t['title']))in headers:reasons.append('retained_exact_Tdoc_title_Source_header')
        if reasons:qualified[t['tdocNumber']]=t;proof[t['tdocNumber']]=reasons
    rows=[];witnesses=[]
    for a in agreements:
        main=a.get('contentWithEquations')or a.get('content')or''
        own,rule=own_record(main);note,note_rule=own_record(a.get('note'))
        answer=own+('\n'+note if note else'')
        refs=sorted(set(TD.findall(answer))&set(qualified))
        if not refs:continue
        made=[meetings[n]for n in a['MADE_AT_node_ids']]
        if not made:continue
        latest=max(made,key=meeting_key)
        # Distinct Agreement entity; earliest original qualifying Tdoc key.
        t=refs[0];key=meeting_key(latest)
        row={'t.tdocNumber':t,'a.resolutionId':a['resolutionId'],'a.content':answer,'m.meetingNumber':latest['meetingNumber'],'__source_order_meetingNumberInt':key[0],'__source_order_bis':key[1]}
        rows.append(row);witnesses.append({'id':a['resolutionId'],'own_qualifying_Tdocs':refs,'Tdoc_company_proofs':{n:proof[n]for n in refs},'body_rule':rule,'note_rule':note_rule,'selected_Meeting_node_id':latest['node_id'],'meeting_key':list(key)})
    rows.sort(key=lambda r:(-r['__source_order_meetingNumberInt'],-r['__source_order_bis'],r['t.tdocNumber'],r['a.resolutionId']))
    return{'all_distinct_Agreement_rows':rows,'first10':rows[:10],'witnesses':witnesses,'qualified_Tdoc_n':len(qualified),'header_Company_Tdoc_title_keys':len(headers),'Company_proofs':proof}
