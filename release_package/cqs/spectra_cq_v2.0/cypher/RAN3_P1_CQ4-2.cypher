// SpectraCQ RAN3_P1_CQ4-2 (RAN3, phase 1) -- CQ4
// Question: Summarize the outcomes of Samsung's contributions at meeting RAN3#130 (result rollup by status).
// Gold: 7 rows, primary column "t.status"

MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}), (t)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}) RETURN t.status, count(t) AS cnt ORDER BY cnt DESC
