// SpectraCQ P2_CQ4-1 — CQ4_기술주도권분석
// Question (English): Return the top-5 companies by FL Summary authorship in agenda 7.1 (NR MIMO) — technology-leadership analysis.
// Schema area: classes=['AgendaItem', 'Company', 'Tdoc'], rels=['BELONGS_TO', 'MODERATED_BY']

MATCH (t:Tdoc)-[:BELONGS_TO]->(ai:AgendaItem), (t)-[:MODERATED_BY]->(c:Company)
WHERE ai.agendaNumber STARTS WITH '7.1' AND t.summaryType = 'FL'
RETURN c.companyName, count(t) AS flCount ORDER BY flCount DESC LIMIT 5
