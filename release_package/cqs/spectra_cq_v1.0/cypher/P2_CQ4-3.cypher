// SpectraCQ P2_CQ4-3 — CQ4_기술주도권분석
// Question (English): Return the top-10 companies by FL Summary count (technology-leadership ranking).
// Schema area: classes=['Company', 'Tdoc'], rels=['MODERATED_BY']

MATCH (t:Tdoc)-[:MODERATED_BY]->(c:Company)
WHERE t.summaryType = 'FL'
RETURN c.companyName, count(t) AS flCount ORDER BY flCount DESC LIMIT 10
