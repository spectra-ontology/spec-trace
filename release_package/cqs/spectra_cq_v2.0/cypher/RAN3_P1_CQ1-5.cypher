// SpectraCQ RAN3_P1_CQ1-5 (RAN3, phase 1) -- CQ1_Tdoc
// Question: List the TDocs agreed at meeting RAN3#130 (approved-outcome review).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}) WHERE t.status = 'agreed' RETURN t.tdocNumber, t.title ORDER BY t.tdocNumber LIMIT 10
