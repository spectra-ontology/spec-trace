// SpectraCQ RAN3_P1_CQ4-1 (RAN3, phase 1) -- CQ4
// Question: List Samsung's past-meeting contributions to Work Item NR_newRAT-Core (historical contribution review).
// Gold: 10 rows, primary column "m.canonicalMeetingNumber"

MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}), (t)-[:RELATED_TO]->(w:WorkItem {workItemCode: 'NR_newRAT-Core'}), (t)-[:PRESENTED_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, t.tdocNumber, t.title, t.status ORDER BY m.meetingNumberInt DESC LIMIT 10
