CALL {
MATCH (m:Meeting)<-[:PRESENTED_AT]-(c:CR)
WHERE c.reasonForChange IS NOT NULL
WITH m, collect({cr:c, fields:[reduce(n = "", token IN split(reduce(w = c.reasonForChange, white IN ["\t", "\n", "\u000b", "\f", "\r", "\u001c", "\u001d", "\u001e", "\u001f", "\u0085", "\u00a0", "\u1680", "\u2000", "\u2001", "\u2002", "\u2003", "\u2004", "\u2005", "\u2006", "\u2007", "\u2008", "\u2009", "\u200a", "\u2028", "\u2029", "\u202f", "\u205f", "\u3000"] | replace(w, white, " ")), " ") | CASE WHEN token = "" THEN n WHEN n = "" THEN token ELSE n + " " + token END), reduce(n = "", token IN split(reduce(w = coalesce(c.summaryOfChange, ""), white IN ["\t", "\n", "\u000b", "\f", "\r", "\u001c", "\u001d", "\u001e", "\u001f", "\u0085", "\u00a0", "\u1680", "\u2000", "\u2001", "\u2002", "\u2003", "\u2004", "\u2005", "\u2006", "\u2007", "\u2008", "\u2009", "\u200a", "\u2028", "\u2029", "\u202f", "\u205f", "\u3000"] | replace(w, white, " ")), " ") | CASE WHEN token = "" THEN n WHEN n = "" THEN token ELSE n + " " + token END)], history:[value IN [part IN tail(split(replace(toLower(reduce(n = "", token IN split(reduce(w = coalesce(c.reasonForChange, ""), white IN ["\t", "\n", "\u000b", "\f", "\r", "\u001c", "\u001d", "\u001e", "\u001f", "\u0085", "\u00a0", "\u1680", "\u2000", "\u2001", "\u2002", "\u2003", "\u2004", "\u2005", "\u2006", "\u2007", "\u2008", "\u2009", "\u200a", "\u2028", "\u2029", "\u202f", "\u205f", "\u3000"] | replace(w, white, " ")), " ") | CASE WHEN token = "" THEN n WHEN n = "" THEN token ELSE n + " " + token END)), " ", ""), "agreementinran4#")) | toInteger(substring(part, 0, coalesce(head([k IN range(0, size(part)-1) WHERE NOT substring(part,k,1) =~ "[0-9]" | k]),size(part))))] WHERE value IS NOT NULL | value]}) AS candidates
MATCH (a:Agreement)-[:MADE_AT]->(m)
WITH a,m,candidates,split(coalesce(a.contentWithEquations, a.content, "") + "\n" + coalesce(a.note, ""), "\n") AS lines
WITH a,m,candidates,lines,reduce(state = {ended:false,abstracted:false,operative:[]}, lineIndex IN range(0,size(lines)-1) | CASE
WHEN state.ended THEN state
WHEN lines[lineIndex] =~ "(?is)^\\s*Decision\\s*:.*" THEN {ended:true,abstracted:state.abstracted,operative:state.operative}
WHEN lines[lineIndex] =~ "(?is)^\\s*Abstract\\s*:.*" THEN {ended:false,abstracted:true,operative:state.operative}
WHEN lines[lineIndex] =~ "(?is)^\\s*Discussion\\s*:.*" THEN {ended:false,abstracted:false,operative:state.operative}
WHEN NOT state.abstracted AND trim(lines[lineIndex]) <> "" THEN {ended:false,abstracted:false,operative:state.operative+[lineIndex]}
ELSE state END) AS selected
UNWIND selected.operative AS i
WITH a,m,candidates,i,reduce(n = "", token IN split(reduce(w = lines[i], white IN ["\t", "\n", "\u000b", "\f", "\r", "\u001c", "\u001d", "\u001e", "\u001f", "\u0085", "\u00a0", "\u1680", "\u2000", "\u2001", "\u2002", "\u2003", "\u2004", "\u2005", "\u2006", "\u2007", "\u2008", "\u2009", "\u200a", "\u2028", "\u2029", "\u202f", "\u205f", "\u3000"] | replace(w, white, " ")), " ") | CASE WHEN token = "" THEN n WHEN n = "" THEN token ELSE n + " " + token END) AS line
WHERE line =~ "(?is).*\\b(?:shall|must|should|will|(?:is|are|be)\\s+(?:not\\s+)?(?:allowed|required|defined|introduced|assumed|used|applied|configured|supported|increased|decreased|changed|set|agreed|approved|endorsed)|no\\s+requirement|additional\\s+delay\\s+can\\s+be\\s+expected|not\\s+required|do\\s+not\\s+define)\\b.*" OR line =~ "(?is)^\\s*Interruptions\\s+on\\s+(.+?)\\s+are\\s+allowed\\b.*?\\bdue\\s+to\\s+(.+?)(?:\\s+in\\s+|[.;]|$).*"
WITH a,m,candidates,i,line,
CASE WHEN line =~ "(?is)^\\s*Interruptions\\s+on\\s+(.+?)\\s+are\\s+allowed\\b.*?\\bdue\\s+to\\s+(.+?)(?:\\s+in\\s+|[.;]|$).*" THEN replace(replace(toLower(head(split(substring(toLower(line), size("interruptions on ")), " are allowed"))), "measurements", "measurement"), " carrier based switching", " carrier switching") ELSE "" END AS target,
CASE WHEN line =~ "(?is)^\\s*Interruptions\\s+on\\s+(.+?)\\s+are\\s+allowed\\b.*?\\bdue\\s+to\\s+(.+?)(?:\\s+in\\s+|[.;]|$).*" THEN replace(replace(toLower(head(split(head(split(head(split(head(tail(split(toLower(line)," due to ")))," in ")),".")),";"))), "measurements", "measurement"), " carrier based switching", " carrier switching") ELSE "" END AS cause
UNWIND candidates AS item
WITH a,m,i,line,target,cause,item,[field IN item.fields | replace(replace(toLower(field), "measurements", "measurement"), " carrier based switching", " carrier switching")] AS semanticFields
WHERE NOT(size(item.history)>0 AND all(oldMeeting IN item.history WHERE oldMeeting <> m.meetingNumberInt))
AND ((line =~ "(?is).*\\b(?:shall|must|should|will|(?:is|are|be)\\s+(?:not\\s+)?(?:allowed|required|defined|introduced|assumed|used|applied|configured|supported|increased|decreased|changed|set|agreed|approved|endorsed)|no\\s+requirement|additional\\s+delay\\s+can\\s+be\\s+expected|not\\s+required|do\\s+not\\s+define)\\b.*" AND any(field IN item.fields WHERE field CONTAINS line))
OR (line =~ "(?is)^\\s*Interruptions\\s+on\\s+(.+?)\\s+are\\s+allowed\\b.*?\\bdue\\s+to\\s+(.+?)(?:\\s+in\\s+|[.;]|$).*" AND target <> "" AND cause <> "" AND any(field IN semanticFields WHERE field CONTAINS target AND field CONTAINS cause AND field =~ "(?is).*\\b(?:impact|impacted|interrupt|interrupted|interruption|delay|delayed)\\b.*")))
RETURN a,item.cr AS c
UNION
MATCH (a:Agreement)-[:RESOLUTION_BELONGS_TO]->(agenda:AgendaItem)<-[:RESOLUTION_BELONGS_TO]-(previous:Agreement)
WHERE previous.sequence = a.sequence - 1
WITH a,previous,split(coalesce(previous.contentWithEquations, previous.content, "") + "\n" + coalesce(previous.note, ""), "\n") AS previousLines,split(coalesce(a.contentWithEquations, a.content, "") + "\n" + coalesce(a.note, ""), "\n") AS lines
WITH a,previous,previousLines,lines,last([j IN range(0,size(previousLines)-1) WHERE previousLines[j] =~ "^\\s*R4-[0-9]{6,7}[\\t ]+\\S.*" | j]) AS ownHeader,
head([j IN range(0,size(lines)-1) WHERE lines[j] =~ "(?is)^\\s*Decision\\s*:.*" | j]) AS ownDecision
WHERE ownHeader IS NOT NULL AND ownDecision IS NOT NULL
AND none(j IN range(ownHeader+1,size(previousLines)-1) WHERE previousLines[j] =~ "(?is)^\\s*Decision\\s*:.*")
AND lines[ownDecision] =~ "(?is)^\\s*Decision\\s*:\\s*(?:(?:the\\s+)?document\\s+(?:was\\s+|is\\s+)?)?(?:agreed|approved|endorsed|accepted)\\b.*"
AND none(j IN range(0,ownDecision) WHERE lines[j] =~ "^\\s*R4-[0-9]{6,7}[\\t ]+\\S.*")
WITH a,head(split(reduce(n = "", token IN split(reduce(w = previousLines[ownHeader], white IN ["\t", "\n", "\u000b", "\f", "\r", "\u001c", "\u001d", "\u001e", "\u001f", "\u0085", "\u00a0", "\u1680", "\u2000", "\u2001", "\u2002", "\u2003", "\u2004", "\u2005", "\u2006", "\u2007", "\u2008", "\u2009", "\u200a", "\u2028", "\u2029", "\u202f", "\u205f", "\u3000"] | replace(w, white, " ")), " ") | CASE WHEN token = "" THEN n WHEN n = "" THEN token ELSE n + " " + token END), " ")) AS ownTdoc
MATCH (a)-[:MADE_AT]->(m:Meeting)<-[:PRESENTED_AT]-(c:CR)
WHERE c.tdocNumber=ownTdoc AND c.reasonForChange IS NOT NULL
RETURN a,c
UNION
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting)
WITH a,m,split(coalesce(a.contentWithEquations, a.content, "") + "\n" + coalesce(a.note, ""), "\n") AS lines
WITH a,m,lines,reduce(state = {ended:false,abstracted:false,operative:[]}, lineIndex IN range(0,size(lines)-1) | CASE
WHEN state.ended THEN state
WHEN lines[lineIndex] =~ "(?is)^\\s*Decision\\s*:.*" THEN {ended:true,abstracted:state.abstracted,operative:state.operative}
WHEN lines[lineIndex] =~ "(?is)^\\s*Abstract\\s*:.*" THEN {ended:false,abstracted:true,operative:state.operative}
WHEN lines[lineIndex] =~ "(?is)^\\s*Discussion\\s*:.*" THEN {ended:false,abstracted:false,operative:state.operative}
WHEN NOT state.abstracted AND trim(lines[lineIndex]) <> "" THEN {ended:false,abstracted:false,operative:state.operative+[lineIndex]}
ELSE state END) AS selected
UNWIND selected.operative AS i
WITH a,m,i,reduce(n = "", token IN split(reduce(w = lines[i], white IN ["\t", "\n", "\u000b", "\f", "\r", "\u001c", "\u001d", "\u001e", "\u001f", "\u0085", "\u00a0", "\u1680", "\u2000", "\u2001", "\u2002", "\u2003", "\u2004", "\u2005", "\u2006", "\u2007", "\u2008", "\u2009", "\u200a", "\u2028", "\u2029", "\u202f", "\u205f", "\u3000"] | replace(w, white, " ")), " ") | CASE WHEN token = "" THEN n WHEN n = "" THEN token ELSE n + " " + token END) AS line
WHERE line =~ "(?is)^\\s*For\\s+(.+?),\\s*([-+]?\\d+(?:\\.\\d+)?)\\s*([A-Za-z%]+)\\s+is\\s+used[.;]?\\s*$"
WITH a,m,i,line,substring(head(split(line, ",")),4) AS topic
UNWIND range(0,size(topic)-1) AS tokenBegin
WITH a,m,i,line,topic,tokenBegin
WHERE substring(topic,tokenBegin,1) =~ "[A-Z]"
AND (tokenBegin=0 OR NOT substring(topic,tokenBegin-1,1) =~ "[\\p{L}\\p{N}_]")
WITH a,m,i,line,topic,tokenBegin,coalesce(head([j IN range(tokenBegin,size(topic)-1) WHERE NOT substring(topic,j,1) =~ "[A-Z0-9-]" | j]),size(topic)) AS tokenEnd
WITH a,m,i,line,topic,tokenBegin,last([j IN range(tokenBegin,tokenEnd-1) WHERE substring(topic,j,1) =~ "[A-Z0-9]" | j]) AS lastWord
WHERE lastWord-tokenBegin>=1
AND (lastWord+1=size(topic) OR NOT substring(topic,lastWord+1,1) =~ "[\\p{L}\\p{N}_]")
WITH a,m,i,line,collect(substring(topic,tokenBegin,lastWord-tokenBegin+1)) AS terms
MATCH (m)<-[:PRESENTED_AT]-(c:CR)
WHERE c.reasonForChange IS NOT NULL
WITH a,c,terms,split(coalesce(c.reasonForChange,""),"\n")+split(coalesce(c.summaryOfChange,""),"\n") AS clauses
WHERE size(terms)>0 AND any(clause IN clauses WHERE clause =~ "(?is).*\\b(?:add(?:ed|ing|ition)?|correct(?:ed|ing|ions?)?|updat(?:e|ed|ing)|modif(?:y|ied|ying|ication)|chang(?:e|ed|ing)|remov(?:e|ed|ing|al))\\b.*"
AND all(term IN terms WHERE clause =~ ("(?is).*\\b"+term+"\\b.*")))
RETURN a,c

UNION
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting)
WITH a,m,split(coalesce(a.contentWithEquations, a.content, "") + "\n" + coalesce(a.note, ""),"\n") AS lines
WITH a,m,lines,reduce(state = {ended:false,abstracted:false,operative:[]}, lineIndex IN range(0,size(lines)-1) | CASE
WHEN state.ended THEN state
WHEN lines[lineIndex] =~ "(?is)^\\s*Decision\\s*:.*" THEN {ended:true,abstracted:state.abstracted,operative:state.operative}
WHEN lines[lineIndex] =~ "(?is)^\\s*Abstract\\s*:.*" THEN {ended:false,abstracted:true,operative:state.operative}
WHEN lines[lineIndex] =~ "(?is)^\\s*Discussion\\s*:.*" THEN {ended:false,abstracted:false,operative:state.operative}
WHEN NOT state.abstracted AND trim(lines[lineIndex]) <> "" THEN {ended:false,abstracted:false,operative:state.operative+[lineIndex]}
ELSE state END) AS selected
UNWIND selected.operative AS i
WITH a,m,lines,i,reduce(n = "", token IN split(reduce(w = lines[i], white IN ["\t", "\n", "\u000b", "\f", "\r", "\u001c", "\u001d", "\u001e", "\u001f", "\u0085", "\u00a0", "\u1680", "\u2000", "\u2001", "\u2002", "\u2003", "\u2004", "\u2005", "\u2006", "\u2007", "\u2008", "\u2009", "\u200a", "\u2028", "\u2029", "\u202f", "\u205f", "\u3000"] | replace(w, white, " ")), " ") | CASE WHEN token = "" THEN n WHEN n = "" THEN token ELSE n + " " + token END) AS line
WHERE line =~ "(?is)^\\s*(.+?)\\s+(?:shall|should|must)\\s+have\\s+the\\s+same\\s+(.+?)\\s+in\\s+terms\\s+of\\s+(.+?)\\s+for\\s+both\\s+(.+?)\\s+and\\s+(.+?)[.\\s]*$" OR line =~ "(?is)^\\s*for\\s+(?:the\\s+)?(.+?),\\s*(?:the\\s+)?(.+?)\\s+from\\s+(.+?)\\s+can\\s+be\\s+reused[.\\s]*$" OR line =~ "(?is).*\\brequirement\\s+(?:shall|should|must)\\s+be\\s+\\d+(?:\\.\\d+)?\\s*\\S+\\s+for\\s+(.+?)\\s+in\\s+TS\\s*(\\d{2}\\.\\d{3}(?:-\\d+)?)\\b.*"
WITH a,m,lines,i,line,toLower(line) AS lowerLine
MATCH (m)<-[:PRESENTED_AT]-(c:CR)
WHERE c.reasonForChange IS NOT NULL
AND any(header IN lines WHERE header =~ "^\\s*R4-[0-9]{6,7}[\\t ]+\\S.*" AND head(split(reduce(n = "", token IN split(reduce(w = header, white IN ["\t", "\n", "\u000b", "\f", "\r", "\u001c", "\u001d", "\u001e", "\u001f", "\u0085", "\u00a0", "\u1680", "\u2000", "\u2001", "\u2002", "\u2003", "\u2004", "\u2005", "\u2006", "\u2007", "\u2008", "\u2009", "\u200a", "\u2028", "\u2029", "\u202f", "\u205f", "\u3000"] | replace(w, white, " ")), " ") | CASE WHEN token = "" THEN n WHEN n = "" THEN token ELSE n + " " + token END)," "))=c.tdocNumber)
WITH a,c,line,lowerLine,toLower(replace(replace(coalesce(c.title,"")+" "+coalesce(c.reasonForChange,"")+" "+coalesce(c.summaryOfChange,""), "de-activated", "deactivated"), "(s)", "s")) AS rawFields,
substring(lowerLine,0,coalesce(head([j IN range(0,size(lowerLine)-1) WHERE substring(lowerLine,j,6)=" shall" OR substring(lowerLine,j,7)=" should" OR substring(lowerLine,j,5)=" must" | j]),0)) AS sameEntity,
CASE WHEN replace(head(split(trim(last(split(lowerLine," in ts")))," ")),".",".") ENDS WITH "." THEN substring(replace(head(split(trim(last(split(lowerLine," in ts")))," ")),".","."),0,size(replace(head(split(trim(last(split(lowerLine," in ts")))," ")),".","."))-1) ELSE replace(head(split(trim(last(split(lowerLine," in ts")))," ")),".",".") END AS qSpec,split(last(split(head(split(lowerLine," in ts"))," for "))," ") AS qParts
WITH a,c,line,lowerLine,qSpec,[word IN split(reduce(text = "", j IN range(0,size(rawFields)-1) | text + CASE WHEN substring(rawFields,j,1) =~ "[a-z0-9]" THEN substring(rawFields,j,1) ELSE " " END)," ") WHERE word <> "" | CASE WHEN size(word)>1 AND word ENDS WITH "s" AND NOT word ENDS WITH "ss" THEN substring(word,0,size(word)-1) ELSE word END] AS fieldWords,
toLower(replace(replace(sameEntity + " " + head(split(last(split(lowerLine,"have the same "))," in terms of ")) + " " + head(split(last(split(lowerLine," in terms of "))," for both ")) + " " + head(split(last(split(lowerLine," for both "))," and ")), "de-activated", "deactivated"), "(s)", "s")) AS sameRaw,toLower(replace(replace(replace(head(split(substring(lowerLine,size("for ")),",")),"e-utra","lte") + " " + replace(head(split(last(split(lowerLine,","))," from ")),"e-utra","lte") + " " + head(split(last(split(lowerLine," from "))," can be reused")), "de-activated", "deactivated"), "(s)", "s")) AS reuseRaw,
CASE WHEN size(qParts)>0 THEN qParts[0..size(qParts)-1] ELSE [] END AS qQualifiers
WITH a,c,line,lowerLine,qSpec,fieldWords,[word IN split(reduce(text = "", j IN range(0,size(sameRaw)-1) | text + CASE WHEN substring(sameRaw,j,1) =~ "[a-z0-9]" THEN substring(sameRaw,j,1) ELSE " " END)," ") WHERE word <> "" | CASE WHEN size(word)>1 AND word ENDS WITH "s" AND NOT word ENDS WITH "ss" THEN substring(word,0,size(word)-1) ELSE word END] AS sameWords,[word IN split(reduce(text = "", j IN range(0,size(reuseRaw)-1) | text + CASE WHEN substring(reuseRaw,j,1) =~ "[a-z0-9]" THEN substring(reuseRaw,j,1) ELSE " " END)," ") WHERE word <> "" | CASE WHEN size(word)>1 AND word ENDS WITH "s" AND NOT word ENDS WITH "ss" THEN substring(word,0,size(word)-1) ELSE word END] AS reuseWords,
toLower(replace(replace(reduce(text = "", word IN qQualifiers | text+" "+word), "de-activated", "deactivated"), "(s)", "s")) AS qualifierRaw,qQualifiers
WITH a,c,line,lowerLine,qSpec,fieldWords,sameWords,reuseWords,[word IN split(reduce(text = "", j IN range(0,size(qualifierRaw)-1) | text + CASE WHEN substring(qualifierRaw,j,1) =~ "[a-z0-9]" THEN substring(qualifierRaw,j,1) ELSE " " END)," ") WHERE word <> "" | CASE WHEN size(word)>1 AND word ENDS WITH "s" AND NOT word ENDS WITH "ss" THEN substring(word,0,size(word)-1) ELSE word END] AS qualifierWords,qQualifiers
WHERE (line =~ "(?is)^\\s*(.+?)\\s+(?:shall|should|must)\\s+have\\s+the\\s+same\\s+(.+?)\\s+in\\s+terms\\s+of\\s+(.+?)\\s+for\\s+both\\s+(.+?)\\s+and\\s+(.+?)[.\\s]*$" AND all(word IN sameWords WHERE word IN fieldWords))
OR (line =~ "(?is)^\\s*for\\s+(?:the\\s+)?(.+?),\\s*(?:the\\s+)?(.+?)\\s+from\\s+(.+?)\\s+can\\s+be\\s+reused[.\\s]*$" AND all(word IN reuseWords WHERE word IN ["the","on","in","of","for","to","a","an"] OR word IN fieldWords))
OR (line =~ "(?is).*\\brequirement\\s+(?:shall|should|must)\\s+be\\s+\\d+(?:\\.\\d+)?\\s*\\S+\\s+for\\s+(.+?)\\s+in\\s+TS\\s*(\\d{2}\\.\\d{3}(?:-\\d+)?)\\b.*" AND size(qQualifiers)>0 AND all(word IN qualifierWords WHERE word IN fieldWords)
AND EXISTS { MATCH (c)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber=qSpec })
RETURN a,c
UNION
MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting)
WITH a,m,split(coalesce(a.contentWithEquations, a.content, "") + "\n" + coalesce(a.note, ""),"\n") AS lines
WITH a,m,lines,reduce(state = {ended:false,abstracted:false,operative:[]}, lineIndex IN range(0,size(lines)-1) | CASE
WHEN state.ended THEN state
WHEN lines[lineIndex] =~ "(?is)^\\s*Decision\\s*:.*" THEN {ended:true,abstracted:state.abstracted,operative:state.operative}
WHEN lines[lineIndex] =~ "(?is)^\\s*Abstract\\s*:.*" THEN {ended:false,abstracted:true,operative:state.operative}
WHEN lines[lineIndex] =~ "(?is)^\\s*Discussion\\s*:.*" THEN {ended:false,abstracted:false,operative:state.operative}
WHEN NOT state.abstracted AND trim(lines[lineIndex]) <> "" THEN {ended:false,abstracted:false,operative:state.operative+[lineIndex]}
ELSE state END) AS selected
UNWIND selected.operative AS i
WITH a,m,lines,i,reduce(n = "", token IN split(reduce(w = lines[i], white IN ["\t", "\n", "\u000b", "\f", "\r", "\u001c", "\u001d", "\u001e", "\u001f", "\u0085", "\u00a0", "\u1680", "\u2000", "\u2001", "\u2002", "\u2003", "\u2004", "\u2005", "\u2006", "\u2007", "\u2008", "\u2009", "\u200a", "\u2028", "\u2029", "\u202f", "\u205f", "\u3000"] | replace(w, white, " ")), " ") | CASE WHEN token = "" THEN n WHEN n = "" THEN token ELSE n + " " + token END) AS line
WHERE line =~ "(?is)^\\s*(MRTD|MTTD)\\s*=\\s*[-+]?\\d+(?:\\.\\d+)?\\s*(?:us|\u00b5s|\u03bcs)\\s*$"
OR line =~ "(?is).*[-+]?\\d+(?:\\.\\d+)?\\s*%\\s*of\\s*CP\\b.*"
OR line =~ "(?is)^\\s*PCell\\s+interruption\\s+length\\s+for\\s+(?:inter-band\\s+)?([A-Z][A-Z0-9-]+)\\s*:\\s*\\d+(?:\\.\\d+)?\\s+subframes?\\s+each\\s*$"
OR line =~ "(?is).*\\bIf\\s+UE\\s+provides\\s+the\\s+measurement\\s+report\\b.*?\\bthen\\s+T_?processing\\s+will\\s+be\\b.*?\\bOtherwise\\b.*?\\bT_?processing\\b.*"
WITH a,m,line,coalesce(a.contentWithEquations,a.content,"")+"\n"+coalesce(a.note,"") AS body
MATCH (m)<-[:PRESENTED_AT]-(c:CR)
WHERE c.reasonForChange IS NOT NULL
WITH a,c,line,body,coalesce(c.title,"")+" "+coalesce(c.reasonForChange,"")+" "+coalesce(c.summaryOfChange,"") AS fields
WHERE (line =~ "(?is)^\\s*(MRTD|MTTD)\\s*=\\s*[-+]?\\d+(?:\\.\\d+)?\\s*(?:us|\u00b5s|\u03bcs)\\s*$"
AND fields =~ "(?is).*\\bendorsed\\s+draft\\s*CRs?\\b.*"
AND EXISTS { MATCH (c)-[:MODIFIES_SECTION]->(section:Section) WHERE toLower(section.sectionTitle)="timing" })
OR (line =~ "(?is).*[-+]?\\d+(?:\\.\\d+)?\\s*%\\s*of\\s*CP\\b.*" AND body =~ "(?is).*\\bEVM\\s+window\\s+length\\b.*" AND fields =~ "(?is).*\\bEVM\\s+window\\s+length\\b.*")
OR (line =~ "(?is)^\\s*PCell\\s+interruption\\s+length\\s+for\\s+(?:inter-band\\s+)?([A-Z][A-Z0-9-]+)\\s*:\\s*\\d+(?:\\.\\d+)?\\s+subframes?\\s+each\\s*$"
AND fields =~ ("(?is).*\\b"+head(split(last(split(toLower(head(split(line,":")))," ")),":"))+"\\b.*")
AND fields =~ "(?is).*\\b(?:introduc(?:e|ed|ing|tion)|added\\s+reference)\\b.*")
OR (line =~ "(?is).*\\bIf\\s+UE\\s+provides\\s+the\\s+measurement\\s+report\\b.*?\\bthen\\s+T_?processing\\s+will\\s+be\\b.*?\\bOtherwise\\b.*?\\bT_?processing\\b.*"
AND fields =~ "(?is).*\\bprocessing\\s+time\\b.*" AND fields =~ "(?is).*\\bRF\\s+warm\\s+up\\b.*" AND fields =~ "(?is).*\\baddition\\s+delay\\b.*")
RETURN a,c
}
WITH DISTINCT c ORDER BY c.tdocNumber ASC LIMIT 5 RETURN c.tdocNumber AS tdocNumber,c.reasonForChange AS reason,c.summaryOfChange AS summary