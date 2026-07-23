// SpectraCQ RAN2_P1_CQ4-2 (RAN2, phase 1) -- CQ4
// Question: Summarize the outcomes of Samsung's contributions at RAN2#132 (meeting result summary).
// Gold: 10 rows, primary column "t.status"

MATCH (m:Meeting {canonicalMeetingNumber: 'RAN2#132'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}) RETURN t.status, count(t) AS count ORDER BY count DESC
