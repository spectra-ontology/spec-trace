CALL {
MATCH (candidate:Agreement)
WITH candidate, head(split(candidate.content,'\n')) AS header,
substring(candidate.content,size(head(split(candidate.content,'\n')))+1) AS body
WHERE header =~ '(?i)^(Adopt|Approve|Agree)\\b[^\\n]*?\\bTS\\s*\\d{2}\\.\\d{3}\\s+V\\d+\\.\\d+\\.\\d+\\s*,?\\s*Clause\\s*\\d+(?:\\.\\d+)*\\b.*$'
WITH candidate, header, body, head([i IN range(0,size(header)-2) WHERE substring(header,i,2) =~ '(?i)TS' AND (i=0 OR NOT substring(header,i-1,1) =~ '[A-Za-z0-9_]') AND substring(header,i+2) =~ '(?is)\\s*\\d{2}\\.\\d{3}\\s+V.*']) AS tspos
WITH candidate, header, body, tspos, trim(substring(header,tspos+2)) AS afterTS
WITH candidate, header, body, tspos, afterTS, substring(afterTS,0,6) AS spec
WITH candidate, header, body, tspos, afterTS, spec, trim(substring(afterTS,6)) AS afterSpec
WITH candidate, header, body, tspos, afterTS, spec, afterSpec, head(split(substring(afterSpec,1),'.')) AS major
WITH candidate, header, body, tspos, afterTS, spec, afterSpec, major, head([i IN range(0,size(afterSpec)-6) WHERE substring(afterSpec,i,6) =~ '(?i)Clause' AND (i=0 OR NOT substring(afterSpec,i-1,1) =~ '[A-Za-z0-9_]')]) AS clausePos
WITH candidate, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, trim(substring(afterSpec,clausePos+6)) AS afterClause
WITH candidate, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, last([n IN range(1,size(afterClause)) WHERE substring(afterClause,0,n) =~ '\\d+(?:\\.\\d+)*' AND (n=size(afterClause) OR NOT substring(afterClause,n,1) =~ '[A-Za-z0-9_]')]) AS clauseLen
WITH candidate, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, substring(afterClause,0,clauseLen) AS clause
WITH candidate, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, substring(afterClause,clauseLen) AS suffix
WITH candidate, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, head([i IN range(0,size(suffix)-9) WHERE substring(suffix,i,9) =~ '(?i)regarding' AND (i=0 OR NOT substring(suffix,i-1,1) =~ '[A-Za-z0-9_]') AND substring(suffix,i+9,1) =~ '\\s']) AS regardingPos
WITH candidate, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, regardingPos, CASE WHEN regardingPos IS NULL THEN '' ELSE substring(suffix,regardingPos+9) END AS rawTopic
WITH candidate, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, regardingPos, rawTopic, reduce(s='',i IN CASE WHEN size(rawTopic)>0 THEN range(0,size(rawTopic)-1) ELSE [] END | s+CASE WHEN substring(rawTopic,i,1) =~ '\\s' THEN ' ' ELSE substring(rawTopic,i,1) END) AS topicWS
WITH candidate, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, regardingPos, rawTopic, topicWS, reduce(s='',t IN [t IN split(topicWS,' ') WHERE t<>''] | CASE WHEN s='' THEN t ELSE s+' '+t END) AS joinedTopic
WITH candidate, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, regardingPos, rawTopic, topicWS, joinedTopic, [i IN CASE WHEN size(joinedTopic)>0 THEN range(0,size(joinedTopic)-1) ELSE [] END WHERE NOT substring(joinedTopic,i,1) IN [' ','.']] AS topicBounds
WITH candidate, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, regardingPos, rawTopic, topicWS, joinedTopic, topicBounds, CASE WHEN regardingPos IS NULL OR size(topicBounds)=0 THEN null ELSE toLower(substring(joinedTopic,head(topicBounds),last(topicBounds)-head(topicBounds)+1)) END AS topic
WITH candidate, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, regardingPos, rawTopic, topicWS, joinedTopic, topicBounds, topic, reduce(s='',i IN CASE WHEN size(body)>0 THEN range(0,size(body)-1) ELSE [] END | s+CASE WHEN substring(body,i,1) =~ '[A-Za-z0-9_-]' THEN substring(body,i,1) ELSE ' ' END) AS wordBody
WITH candidate, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, regardingPos, rawTopic, topicWS, joinedTopic, topicBounds, topic, wordBody, [i IN CASE WHEN size(wordBody)>0 THEN range(0,size(wordBody)-1) ELSE [] END WHERE substring(wordBody,i,1)<>' ' AND (i=0 OR substring(wordBody,i-1,1)=' ')] AS wordStarts
WITH candidate, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, regardingPos, rawTopic, topicWS, joinedTopic, topicBounds, topic, wordBody, wordStarts, [i IN wordStarts | {beginOffset:i,text:head(split(substring(wordBody,i),' '))}] AS words
WITH candidate, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, regardingPos, rawTopic, topicWS, joinedTopic, topicBounds, topic, wordBody, wordStarts, words, [w IN words WHERE w.text =~ '[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+'] AS params
WITH candidate, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, regardingPos, rawTopic, topicWS, joinedTopic, topicBounds, topic, wordBody, wordStarts, words, params, [i IN CASE WHEN size(params)>1 THEN range(0,size(params)-2) ELSE [] END WHERE params[i].text<>params[i+1].text AND substring(body,params[i].beginOffset+size(params[i].text),params[i+1].beginOffset-params[i].beginOffset-size(params[i].text)) =~ '[\\s\\[\\]()]*' | {left:params[i].text,right:params[i+1].text,beginOffset:params[i].beginOffset,end:params[i+1].beginOffset+size(params[i+1].text),surface:substring(body,params[i].beginOffset,params[i+1].beginOffset+size(params[i+1].text)-params[i].beginOffset)}] AS pairs
WITH candidate, spec, major, clause, topic, pairs
MATCH (section:Section {sectionId:spec+'-Rel-'+major+'-'+clause})
OPTIONAL MATCH (table:TSTable)-[:TABLE_IN_SECTION]->(section)
WITH candidate,topic,pairs,section,collect(table.tableCaption) AS captions
MATCH (cr:CR)-[:MODIFIES_SECTION]->(section)
WHERE coalesce(cr.reasonForChange,'') =~ '(?is).*\\bparameter\\b.*\\b(?:correct\\s+name|name\\s+(?:is\\s+)?correct|renam\\w*)\\b.*'
WITH DISTINCT candidate,topic,pairs,captions
UNWIND pairs AS pair
WITH candidate,topic,pair,
any(cap IN captions WHERE coalesce(cap,'') =~ '(?s).*(?<![A-Za-z0-9_-])'+pair.left+'(?![A-Za-z0-9_-]).*') AS leftIn,
any(cap IN captions WHERE coalesce(cap,'') =~ '(?s).*(?<![A-Za-z0-9_-])'+pair.right+'(?![A-Za-z0-9_-]).*') AS rightIn
WHERE leftIn<>rightIn
OPTIONAL MATCH (candidate)-[:MADE_AT]->(cm:Meeting)
OPTIONAL MATCH (candidate)-[:RESOLUTION_BELONGS_TO]->(cg:AgendaItem)
WITH candidate,topic,pair,leftIn,collect(DISTINCT CASE WHEN cm IS NOT NULL AND cg IS NOT NULL THEN {meeting:cm,agenda:cg} ELSE null END) AS contexts
ORDER BY candidate.resolutionId,pair.beginOffset
RETURN collect({anchor:candidate,topic:topic,contexts:contexts,surface:pair.surface,left:pair.left,right:pair.right,beginOffset:pair.beginOffset,newName:CASE WHEN leftIn THEN pair.left ELSE pair.right END}) AS localRepairs
}
MATCH (a:Agreement)-[originalMadeAt:MADE_AT]->(m:Meeting)
WHERE a.content CONTAINS 'PUSCH' AND a.content CONTAINS 'repetition'
CALL {
WITH a
OPTIONAL MATCH (a)-[:MADE_AT]->(am:Meeting)
OPTIONAL MATCH (a)-[:RESOLUTION_BELONGS_TO]->(ag:AgendaItem)
RETURN collect(DISTINCT CASE WHEN am IS NOT NULL AND ag IS NOT NULL THEN {meeting:am,agenda:ag} ELSE null END) AS targetContexts
}
CALL {
WITH a
WITH a,head(split(a.content,'\n')) AS header,substring(a.content,size(head(split(a.content,'\n')))+1) AS body
WHERE header =~ '(?i)^(Adopt|Approve|Agree)\\b[^\\n]*?\\bTS\\s*\\d{2}\\.\\d{3}\\s+V\\d+\\.\\d+\\.\\d+\\s*,?\\s*Clause\\s*\\d+(?:\\.\\d+)*\\b.*$'
WITH a, header, body, head([i IN range(0,size(header)-2) WHERE substring(header,i,2) =~ '(?i)TS' AND (i=0 OR NOT substring(header,i-1,1) =~ '[A-Za-z0-9_]') AND substring(header,i+2) =~ '(?is)\\s*\\d{2}\\.\\d{3}\\s+V.*']) AS tspos
WITH a, header, body, tspos, trim(substring(header,tspos+2)) AS afterTS
WITH a, header, body, tspos, afterTS, substring(afterTS,0,6) AS spec
WITH a, header, body, tspos, afterTS, spec, trim(substring(afterTS,6)) AS afterSpec
WITH a, header, body, tspos, afterTS, spec, afterSpec, head(split(substring(afterSpec,1),'.')) AS major
WITH a, header, body, tspos, afterTS, spec, afterSpec, major, head([i IN range(0,size(afterSpec)-6) WHERE substring(afterSpec,i,6) =~ '(?i)Clause' AND (i=0 OR NOT substring(afterSpec,i-1,1) =~ '[A-Za-z0-9_]')]) AS clausePos
WITH a, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, trim(substring(afterSpec,clausePos+6)) AS afterClause
WITH a, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, last([n IN range(1,size(afterClause)) WHERE substring(afterClause,0,n) =~ '\\d+(?:\\.\\d+)*' AND (n=size(afterClause) OR NOT substring(afterClause,n,1) =~ '[A-Za-z0-9_]')]) AS clauseLen
WITH a, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, substring(afterClause,0,clauseLen) AS clause
WITH a, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, substring(afterClause,clauseLen) AS suffix
WITH a, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, head([i IN range(0,size(suffix)-9) WHERE substring(suffix,i,9) =~ '(?i)regarding' AND (i=0 OR NOT substring(suffix,i-1,1) =~ '[A-Za-z0-9_]') AND substring(suffix,i+9,1) =~ '\\s']) AS regardingPos
WITH a, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, regardingPos, CASE WHEN regardingPos IS NULL THEN '' ELSE substring(suffix,regardingPos+9) END AS rawTopic
WITH a, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, regardingPos, rawTopic, reduce(s='',i IN CASE WHEN size(rawTopic)>0 THEN range(0,size(rawTopic)-1) ELSE [] END | s+CASE WHEN substring(rawTopic,i,1) =~ '\\s' THEN ' ' ELSE substring(rawTopic,i,1) END) AS topicWS
WITH a, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, regardingPos, rawTopic, topicWS, reduce(s='',t IN [t IN split(topicWS,' ') WHERE t<>''] | CASE WHEN s='' THEN t ELSE s+' '+t END) AS joinedTopic
WITH a, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, regardingPos, rawTopic, topicWS, joinedTopic, [i IN CASE WHEN size(joinedTopic)>0 THEN range(0,size(joinedTopic)-1) ELSE [] END WHERE NOT substring(joinedTopic,i,1) IN [' ','.']] AS topicBounds
WITH a, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, regardingPos, rawTopic, topicWS, joinedTopic, topicBounds, CASE WHEN regardingPos IS NULL OR size(topicBounds)=0 THEN null ELSE toLower(substring(joinedTopic,head(topicBounds),last(topicBounds)-head(topicBounds)+1)) END AS topic
WITH a, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, regardingPos, rawTopic, topicWS, joinedTopic, topicBounds, topic, reduce(s='',i IN CASE WHEN size(body)>0 THEN range(0,size(body)-1) ELSE [] END | s+CASE WHEN substring(body,i,1) =~ '[A-Za-z0-9_-]' THEN substring(body,i,1) ELSE ' ' END) AS wordBody
WITH a, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, regardingPos, rawTopic, topicWS, joinedTopic, topicBounds, topic, wordBody, [i IN CASE WHEN size(wordBody)>0 THEN range(0,size(wordBody)-1) ELSE [] END WHERE substring(wordBody,i,1)<>' ' AND (i=0 OR substring(wordBody,i-1,1)=' ')] AS wordStarts
WITH a, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, regardingPos, rawTopic, topicWS, joinedTopic, topicBounds, topic, wordBody, wordStarts, [i IN wordStarts | {beginOffset:i,text:head(split(substring(wordBody,i),' '))}] AS words
WITH a, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, regardingPos, rawTopic, topicWS, joinedTopic, topicBounds, topic, wordBody, wordStarts, words, [w IN words WHERE w.text =~ '[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+'] AS params
WITH a, header, body, tspos, afterTS, spec, afterSpec, major, clausePos, afterClause, clauseLen, clause, suffix, regardingPos, rawTopic, topicWS, joinedTopic, topicBounds, topic, wordBody, wordStarts, words, params, [i IN CASE WHEN size(params)>1 THEN range(0,size(params)-2) ELSE [] END WHERE params[i].text<>params[i+1].text AND substring(body,params[i].beginOffset+size(params[i].text),params[i+1].beginOffset-params[i].beginOffset-size(params[i].text)) =~ '[\\s\\[\\]()]*' | {left:params[i].text,right:params[i+1].text,beginOffset:params[i].beginOffset,end:params[i+1].beginOffset+size(params[i+1].text),surface:substring(body,params[i].beginOffset,params[i+1].beginOffset+size(params[i+1].text)-params[i].beginOffset)}] AS pairs
WITH a, spec, major, clause, topic, pairs
RETURN topic,pairs
UNION
WITH a
WITH a,head(split(a.content,'\n')) AS header
WHERE NOT header =~ '(?i)^(Adopt|Approve|Agree)\\b[^\\n]*?\\bTS\\s*\\d{2}\\.\\d{3}\\s+V\\d+\\.\\d+\\.\\d+\\s*,?\\s*Clause\\s*\\d+(?:\\.\\d+)*\\b.*$'
RETURN null AS topic,[] AS pairs
}
WITH a,m,originalMadeAt,localRepairs,targetContexts,topic,pairs,[r IN localRepairs WHERE r.anchor=a] AS directRepairs
WITH a,m,originalMadeAt,directRepairs,pairs,
[r IN localRepairs WHERE r.anchor<>a AND topic IS NOT NULL AND r.topic=topic AND any(c IN r.contexts WHERE c IN targetContexts)] AS siblingRepairs
UNWIND CASE WHEN size(directRepairs)=0 AND size(pairs)>0 THEN pairs ELSE [null] END AS pair
WITH a,m,originalMadeAt,directRepairs,pair,
reduce(names=[],r IN siblingRepairs | CASE WHEN r.newName IN [pair.left,pair.right] AND NOT r.newName IN names THEN names+[r.newName] ELSE names END) AS possibleNames
WITH a,m,originalMadeAt,directRepairs,collect(CASE WHEN pair IS NOT NULL AND size(possibleNames)=1 THEN {surface:pair.surface,newName:head(possibleNames),beginOffset:pair.beginOffset} ELSE null END) AS inferredPairs
WITH a,m,originalMadeAt,CASE WHEN size(directRepairs)>0 THEN directRepairs ELSE inferredPairs END AS replacements,
CASE WHEN a.contentWithEquations IS NOT NULL AND trim(a.contentWithEquations)<>'' THEN a.contentWithEquations ELSE a.content END AS answerBody
WITH a,m,originalMadeAt,reduce(answer=answerBody,r IN replacements | replace(answer,r.surface,r.newName))+
CASE WHEN a.note IS NOT NULL AND trim(a.note)<>'' THEN '\nNote: '+a.note ELSE '' END AS answer
RETURN m.meetingNumber AS `m.meetingNumber`,a.resolutionId AS `a.resolutionId`,answer AS `a.content`
ORDER BY m.meetingNumberInt DESC
LIMIT 10
