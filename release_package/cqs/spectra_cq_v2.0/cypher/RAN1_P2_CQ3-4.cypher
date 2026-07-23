// SpectraCQ RAN1_P2_CQ3-4 (RAN1, phase 2) -- CQ3
// Question: List Qualcomm's 10 most recent agreements.
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Qualcomm'}), (a)-[:MADE_AT]->(m:Meeting) RETURN t.tdocNumber, a.resolutionId, a.content, m.meetingNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber, a.resolutionId LIMIT 10
