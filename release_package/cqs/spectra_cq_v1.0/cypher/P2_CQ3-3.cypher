// SpectraCQ P2_CQ3-3 — CQ3_회사기여도
// Question (English): Return the top-10 companies by Resolution contributions in agenda 7.1 (NR MIMO).
// Schema area: classes=['AgendaItem', 'Agreement', 'Company', 'RESOLUTION_BELONGS_TO', 'Tdoc'], rels=['REFERENCES', 'RESOLUTION_BELONGS_TO', 'SUBMITTED_BY']

MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company), (a)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) WHERE ai.agendaNumber STARTS WITH '7.1' RETURN c.companyName, count(DISTINCT a) AS contributionCount ORDER BY contributionCount DESC LIMIT 10
