// SpectraCQ RAN2_P1_CQ3-1 (RAN2, phase 1) -- CQ3
// Question: List Ericsson's contributions to Work Item NR_newRAT-Core (competitor positioning).
// Gold: 10 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Ericsson'}), (t)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}), (t)-[:PRESENTED_AT]->(m:Meeting) RETURN t.tdocNumber, t.title, t.status, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC, t.tdocNumber ASC LIMIT 10
