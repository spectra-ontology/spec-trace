// SpectraCQ RAN1_P1_CQ3-5 (RAN1, phase 1) -- CQ3
// Question: List other companies' TDocs under the same agenda item as TDoc R1-2501234 (checking competing contributions).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (t0:Tdoc {tdocNumber: 'R1-2501234'})-[:BELONGS_TO]->(a:AgendaItem)<-[:BELONGS_TO]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company) WHERE t.tdocNumber <> t0.tdocNumber RETURN t.tdocNumber, t.title, c.companyName, a.agendaNumber ORDER BY t.tdocNumber ASC LIMIT 10
