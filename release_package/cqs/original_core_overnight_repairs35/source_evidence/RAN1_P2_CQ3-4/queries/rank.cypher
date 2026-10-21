MATCH (c:Company {companyName:'Qualcomm'})
CALL {
WITH c
MATCH (headerOwner:Agreement)
UNWIND split(coalesce(headerOwner.content,'')+'\n'+coalesce(headerOwner.note,''),'\n') AS line
WITH c,split(line,'\t') AS cells
WHERE size(cells)>=3 AND cells[0] =~ 'R1-[0-9]{7}'
WITH c,cells,[cell IN cells[2..] WHERE trim(cell)<>''] AS sourceCells
WITH c,cells,CASE WHEN sourceCells[0] =~ '(?i)(?:RAN1,\\s*)?Moderator' AND size(sourceCells)>1 AND sourceCells[1] STARTS WITH '(' THEN sourceCells[0]+' '+sourceCells[1] ELSE sourceCells[0] END AS source
WHERE source =~ '(?is).*(?<![A-Za-z0-9_])'+c.companyName+'(?![A-Za-z0-9_]).*'
RETURN collect(DISTINCT cells[0]+'\n'+trim(replace(cells[1],' ',' '))) AS headerKeys
}
CALL {
WITH c,headerKeys
MATCH (t:Tdoc)
WHERE EXISTS { MATCH (t)-[:SUBMITTED_BY]->(c) } OR (size(split(coalesce(t.secretaryRemarks,''),'Original source'))>1 AND head(split(last(split(t.secretaryRemarks,'Original source')),'<')) =~ '(?is).*(?<![A-Za-z0-9_])'+c.companyName+'(?![A-Za-z0-9_]).*') OR t.tdocNumber+'\n'+trim(replace(coalesce(t.title,''),' ',' ')) IN headerKeys
RETURN collect(DISTINCT t.tdocNumber) AS qualifyingTdocNumbers
}
WITH qualifyingTdocNumbers
MATCH (a:Agreement)
WITH qualifyingTdocNumbers,a,(CASE WHEN a.contentWithEquations IS NOT NULL AND a.contentWithEquations<>'' THEN a.contentWithEquations ELSE coalesce(a.content,'') END)+'\n'+coalesce(a.note,'') AS rawText
UNWIND tail(split(rawText,'R1-')) AS rawToken
WITH qualifyingTdocNumbers,a,substring(rawToken,0,7) AS digits,substring(rawToken,7,1) AS following
WHERE digits =~ '[0-9]{7}' AND NOT following =~ '[0-9]' AND 'R1-'+digits IN qualifyingTdocNumbers
WITH a,collect(DISTINCT 'R1-'+digits) AS broadQualifiedTdocNumbers
CALL {
WITH a
WITH [CASE WHEN a.contentWithEquations IS NOT NULL AND a.contentWithEquations<>'' THEN a.contentWithEquations ELSE coalesce(a.content,'') END,coalesce(a.note,'')] AS pieces
UNWIND [0,1] AS pieceIndex
WITH pieceIndex,split(pieces[pieceIndex],'\n') AS lines
WITH pieceIndex,lines,[i IN range(0,size(lines)-1) WHERE lines[i] =~ '(?s)^R1-\\d{7}\\t.*$' | {index:i,line:lines[i],previousIndex:last([j IN range(0,i-1) WHERE trim(lines[j])<>'']),followingIndex:head([j IN range(i+1,size(lines)-1) WHERE trim(lines[j])<>''])}] AS positions
WITH pieceIndex,lines,[h IN positions | {index:h.index,line:h.line,previousIndex:h.previousIndex,previous:lines[h.previousIndex],following:lines[h.followingIndex]}] AS headers
WITH pieceIndex,lines,reduce(state={cut:size(lines),finalSeen:false,listed:[]},h IN headers |
CASE WHEN state.cut<size(lines) THEN state
WHEN coalesce((((h.previous =~ '(?i)^.*\\bfinal\\s+CRs?\\b.*(?:in|:)\\s*:?$') OR (h.previous =~ '^\\(Rel-\\d+,.*\\bCR\\d+.*\\) is (?:agreed|endorsed)\\.$' AND h.previousIndex>0 AND state.finalSeen)) AND h.following =~ '^\\(Rel-\\d+,.*\\bCR\\d+.*\\) is (?:agreed|endorsed)\\.$'),false) OR coalesce((h.previous =~ '(?i)^.*\\bfollowing\\s+Tdocs?\\b.*$' OR h.previousIndex IN state.listed),false) OR coalesce((h.previous =~ '(?i)^.*\\bcomeback\\s+for\\s+draft\\s+LS\\b.*$' AND h.following CONTAINS substring(h.line,0,10) AND h.following =~ '(?is).*\\b(?:endorsed|approved|agreed)\\b.*'),false) OR coalesce(h.previous =~ '(?i)^.*\\b(?:agreement|agreements|decision|decisions|above)\\b.*\\bcaptured\\b.*\\bin\\s*:?$',false) THEN {cut:state.cut,finalSeen:state.finalSeen OR coalesce((((h.previous =~ '(?i)^.*\\bfinal\\s+CRs?\\b.*(?:in|:)\\s*:?$') OR (h.previous =~ '^\\(Rel-\\d+,.*\\bCR\\d+.*\\) is (?:agreed|endorsed)\\.$' AND h.previousIndex>0 AND state.finalSeen)) AND h.following =~ '^\\(Rel-\\d+,.*\\bCR\\d+.*\\) is (?:agreed|endorsed)\\.$'),false),listed:CASE WHEN NOT coalesce((((h.previous =~ '(?i)^.*\\bfinal\\s+CRs?\\b.*(?:in|:)\\s*:?$') OR (h.previous =~ '^\\(Rel-\\d+,.*\\bCR\\d+.*\\) is (?:agreed|endorsed)\\.$' AND h.previousIndex>0 AND state.finalSeen)) AND h.following =~ '^\\(Rel-\\d+,.*\\bCR\\d+.*\\) is (?:agreed|endorsed)\\.$'),false) AND coalesce((h.previous =~ '(?i)^.*\\bfollowing\\s+Tdocs?\\b.*$' OR h.previousIndex IN state.listed),false) THEN state.listed+[h.index] ELSE state.listed END}
ELSE {cut:h.index,finalSeen:state.finalSeen,listed:state.listed} END) AS state
WITH pieceIndex,reduce(result='',j IN CASE WHEN state.cut>0 THEN range(0,state.cut-1) ELSE [] END | result+CASE WHEN j=0 THEN '' ELSE '\n' END+lines[j]) AS ownText
ORDER BY pieceIndex
WITH collect(ownText) AS ownTexts
RETURN ownTexts[0]+CASE WHEN ownTexts[1]<>'' THEN '\n'+ownTexts[1] ELSE '' END AS answer
}

UNWIND tail(split(answer,'R1-')) AS token
WITH broadQualifiedTdocNumbers,a,answer,substring(token,0,7) AS digits,substring(token,7,1) AS following
WHERE digits =~ '[0-9]{7}' AND NOT following =~ '[0-9]' AND 'R1-'+digits IN broadQualifiedTdocNumbers
WITH a,answer,min('R1-'+digits) AS representativeTdoc
MATCH (a)-[:MADE_AT]->(m:Meeting)
WITH a,answer,representativeTdoc,m,CASE WHEN toLower(coalesce(m.canonicalMeetingNumber,m.meetingNumber)) ENDS WITH 'b' OR toLower(coalesce(m.canonicalMeetingNumber,m.meetingNumber)) ENDS WITH 'bis' THEN 1 ELSE 0 END AS bisRank
ORDER BY m.meetingNumberInt DESC,bisRank DESC,m.meetingNumber
WITH a,answer,representativeTdoc,head(collect(DISTINCT {meeting:m,bisRank:bisRank})) AS latest
WITH a,answer,representativeTdoc,latest.meeting AS m,latest.bisRank AS bisRank
RETURN representativeTdoc AS `t.tdocNumber`,a.resolutionId AS `a.resolutionId`,answer AS `a.content`,m.meetingNumber AS `m.meetingNumber`,m.meetingNumberInt AS `__source_order_meetingNumberInt`,bisRank AS `__source_order_bis`
ORDER BY m.meetingNumberInt DESC,bisRank DESC,representativeTdoc,a.resolutionId
