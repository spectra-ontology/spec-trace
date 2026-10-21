MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting)
WHERE a.content CONTAINS 'HARQ' AND a.content CONTAINS 'feedback'
WITH a,m,split(a.content,'\n') AS lines
WITH a,m,lines,head([i IN range(0,size(lines)-1) WHERE trim(lines[i]) =~ 'R1-[0-9]{6,8}\\t[^\\t]+\\t.+' | i]) AS headerAt
WITH a,m,CASE WHEN headerAt IS NULL THEN lines ELSE lines[0..headerAt] END AS ownPrefixLines
WHERE any(line IN ownPrefixLines WHERE line CONTAINS 'HARQ')
  AND any(line IN ownPrefixLines WHERE line CONTAINS 'feedback')
RETURN m.meetingNumber, a.resolutionId, a.content
ORDER BY m.meetingNumberInt DESC LIMIT 10