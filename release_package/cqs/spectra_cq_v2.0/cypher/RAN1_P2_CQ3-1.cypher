// SpectraCQ RAN1_P2_CQ3-1 (RAN1, phase 2) -- CQ3
// Question: List Huawei's TDocs that led to an agreement (tracing a company's contributions to the standard).
// Gold: 15 rows, primary column "t.tdocNumber"

MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (a)-[:MADE_AT]->(m:Meeting) RETURN t.tdocNumber, t.title, a.resolutionId, m.meetingNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber, a.resolutionId LIMIT 15
