// SpectraCQ RAN3_P1_CQ3-5 (RAN3, phase 1) -- CQ3
// Question: List other companies' contributions in the same agenda and meeting as R3-258530 (peer-contribution comparison).
// Gold: 10 rows, primary column "c.companyName"

MATCH (t:Tdoc {tdocNumber: 'R3-258530'})-[:BELONGS_TO]->(a:AgendaItem), (t)-[:PRESENTED_AT]->(m:Meeting) MATCH (other:Tdoc)-[:BELONGS_TO]->(a), (other)-[:PRESENTED_AT]->(m), (other)-[:SUBMITTED_BY]->(c:Company) WHERE other.tdocNumber <> 'R3-258530' RETURN c.companyName, other.tdocNumber, other.title ORDER BY c.companyName LIMIT 10
