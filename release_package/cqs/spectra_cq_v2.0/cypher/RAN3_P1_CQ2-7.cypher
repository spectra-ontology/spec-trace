// SpectraCQ RAN3_P1_CQ2-7 (RAN3, phase 1) -- CQ2_Tdoc
// Question: List the incoming liaison statements at meeting RAN3#130 (incoming-LS triage).
// Gold: 10 rows, primary column "l.tdocNumber"

MATCH (l:LS)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}) WHERE l.direction = 'in' RETURN l.tdocNumber, l.title ORDER BY l.tdocNumber LIMIT 10
