// SpectraCQ RAN3_P1_CQ2-6 (RAN3, phase 1) -- CQ2_Tdoc
// Question: List the TDocs postponed at meeting RAN3#121bis (deferred-item tracking).
// Gold: 3 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 121}) WHERE t.status = 'postponed' RETURN t.tdocNumber, t.title LIMIT 10
