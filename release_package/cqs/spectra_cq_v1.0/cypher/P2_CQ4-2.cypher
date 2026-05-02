// SpectraCQ P2_CQ4-2 — CQ4_기술주도권분석
// Question (English): List the agenda items in which Huawei authored an FL Summary.
// Schema area: classes=['AgendaItem', 'Company', 'Tdoc'], rels=['BELONGS_TO', 'MODERATED_BY']

MATCH (t:Tdoc)-[:BELONGS_TO]->(ai:AgendaItem), (t)-[:MODERATED_BY]->(c:Company {companyName: 'Huawei'})
WHERE t.summaryType = 'FL'
RETURN DISTINCT ai.agendaNumber, count(t) AS flCount ORDER BY flCount DESC LIMIT 15
