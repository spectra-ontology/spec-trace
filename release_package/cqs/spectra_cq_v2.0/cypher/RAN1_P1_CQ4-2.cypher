// SpectraCQ RAN1_P1_CQ4-2 (RAN1, phase 1) -- CQ4
// Question: Summarize the outcome of Ericsson's contributions at meeting RAN1#120 by status (count per status).
// Gold: 7 rows, primary column "t.status"

MATCH (m:Meeting {meetingNumber: 'RAN1#120'})<-[:PRESENTED_AT]-(t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Ericsson'}) RETURN t.status, count(t) AS count ORDER BY count DESC LIMIT 10
