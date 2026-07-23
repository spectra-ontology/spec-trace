// SpectraCQ RAN3_P1_CQ3-2 (RAN3, phase 1) -- CQ3
// Question: Break down contributions by company under agenda item 8.1 at meeting RAN3#130 (competitive landscape).
// Gold: 7 rows, primary column "c.companyName"

MATCH (t:Tdoc)-[:BELONGS_TO]->(a:AgendaItem {agendaNumber: '8.1'}), (t)-[:PRESENTED_AT]->(m:Meeting {meetingNumberInt: 130}), (t)-[:SUBMITTED_BY]->(c:Company) RETURN c.companyName, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
