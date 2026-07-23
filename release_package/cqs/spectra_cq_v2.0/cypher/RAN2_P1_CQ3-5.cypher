// SpectraCQ RAN2_P1_CQ3-5 (RAN2, phase 1) -- CQ3
// Question: List other companies' TDocs under the same agenda item as R2-2509337 (competing-proposal scan).
// Gold: 10 rows, primary column "c.companyName"

MATCH (t0:Tdoc {tdocNumber: 'R2-2509337'})-[:BELONGS_TO]->(a:AgendaItem), (t0)-[:PRESENTED_AT]->(m:Meeting) MATCH (m)<-[:PRESENTED_AT]-(t:Tdoc)-[:BELONGS_TO]->(a), (t)-[:SUBMITTED_BY]->(c:Company) WHERE t.tdocNumber <> 'R2-2509337' RETURN c.companyName, t.tdocNumber, t.title, t.status ORDER BY c.companyName, t.tdocNumber LIMIT 10
