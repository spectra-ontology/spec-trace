// SpectraCQ P3_CQ040 — 통합분석
// Question (English): Compare CR counts vs Agreement counts per TS (change-vs-consensus ratio).
// Schema area: classes=['Agreement', 'CR', 'Spec'], rels=['MODIFIES', 'REFERENCES']

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.211','38.212','38.213','38.214','38.215'] WITH sp.specNumber AS ts, count(cr) AS crCnt OPTIONAL MATCH (agr:Agreement)-[:REFERENCES]->(cr2:CR)-[:MODIFIES]->(sp2:Spec) WHERE sp2.specNumber = ts RETURN ts, crCnt, count(DISTINCT agr) AS agrCnt ORDER BY crCnt DESC
