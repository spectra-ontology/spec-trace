"""Generic documentary own-record boundary, from the actual source probe."""

import re

TD=re.compile(r'R1-\d{7}(?!\d)')

HEADER=re.compile(r'^R1-\d{7}\t')

FINAL=re.compile(r'(?i)^.*\bfinal\s+CRs?\b.*(?:in|:)\s*:?$')

STATUS=re.compile(r'^\(Rel-\d+,.*\bCR\d+.*\) is (?:agreed|endorsed)\.$')

FOLLOWING=re.compile(r'(?i)^.*\bfollowing\s+Tdocs?\b.*$')

COMEBACK=re.compile(r'(?i)^.*\bcomeback\s+for\s+draft\s+LS\b.*$')

def own_record(text):
    ls=text.splitlines();accepted_headers={};cut=len(ls)
    for i,s in enumerate(ls):
        if not HEADER.match(s):continue
        previous=next((j for j in range(i-1,-1,-1) if ls[j].strip()),None)
        nxt=next((j for j in range(i+1,len(ls)) if ls[j].strip()),None)
        final=(previous is not None and (FINAL.fullmatch(ls[previous]) or (STATUS.fullmatch(ls[previous]) and previous>0 and any(v=='final_CR' for v in accepted_headers.values()))) and nxt is not None and STATUS.fullmatch(ls[nxt]))
        listed=previous is not None and (FOLLOWING.fullmatch(ls[previous]) or accepted_headers.get(previous)=='explicit_following_Tdocs')
        comeback=(previous is not None and COMEBACK.fullmatch(ls[previous]) and nxt is not None and TD.search(ls[i]) and TD.search(ls[i]).group() in ls[nxt] and re.search(r'(?i)\b(?:endorsed|approved|agreed)\b',ls[nxt]))
        if final:accepted_headers[i]='final_CR'
        elif listed:accepted_headers[i]='explicit_following_Tdocs'
        elif comeback:accepted_headers[i]='draft_LS_comeback'
        else:cut=i;break
    return '\n'.join(ls[:cut]),{'cut_line':cut,'line_n':len(ls),'accepted_header_rules':accepted_headers}
