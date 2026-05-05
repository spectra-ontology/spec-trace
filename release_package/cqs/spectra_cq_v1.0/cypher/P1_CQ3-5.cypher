// SpectraCQ P1_CQ3-5 — CQ3_회사분석
// Question (English): List TDocs from other companies that share the same agenda item with TDoc R1-2501234 (competing-contribution review).
// Schema area: classes=['AgendaItem', 'Company', 'Tdoc'], rels=['BELONGS_TO', 'SUBMITTED_BY']

MATCH (t0:Tdoc {tdocNumber: 'R1-2501234'})-[:BELONGS_TO]->(a:AgendaItem)<-[:BELONGS_TO]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company) WHERE t.tdocNumber <> t0.tdocNumber RETURN t.tdocNumber, t.title, c.companyName, a.agendaNumber ORDER BY t.tdocNumber ASC LIMIT 10
