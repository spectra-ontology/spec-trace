MATCH (sp:Spec)
WHERE sp.specNumber IN ['38.201','38.202','38.211','38.212','38.213','38.214','38.215','38.291']
WITH DISTINCT sp.specNumber AS ts
OPTIONAL MATCH (cr:CR)-[:MODIFIES]->(crTarget:Spec)
WHERE crTarget.specNumber = ts
WITH ts, count(DISTINCT cr) AS crCnt
OPTIONAL MATCH (agr:Agreement)-[:REFERENCES]->(cr2:CR)-[:MODIFIES]->(agrTarget:Spec)
WHERE agrTarget.specNumber = ts
RETURN ts, crCnt, count(DISTINCT agr) AS agrCnt
ORDER BY crCnt DESC, ts ASC