// SpectraCQ RAN1_P2_CQ2-2 (RAN1, phase 2) -- CQ2_Tdoc-Resolution
// Question: Which agreement did TDoc R1-2001110 lead to? (tracing a contribution into the standard)
// Gold: 2 rows, primary column "t.tdocNumber"

MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc {tdocNumber: 'R1-2001110'}), (a)-[:MADE_AT]->(m:Meeting) RETURN t.tdocNumber, a.resolutionId, a.content, m.meetingNumber
